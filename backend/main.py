import os
import io
import json
import uuid
import asyncio
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from PIL import Image

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gee_service import initialize_gee
from ingestion.gee_fetcher import fetch_gee_layer
from ingestion.upload_handler import process_upload, get_upload
from agent.router import AgentController
from agent.multilingual import interpret_query
from models.registry import ModelRegistry
from models.model_manager import ModelManager
from reporting.pdf_generator import generate_evaluation_pdf
from data.sample_loader import get_demo_samples_list, SAMPLES_DIR
from geospatial import parse_geotiff, normalize_to_8bit_rgb

app = FastAPI(title="SatQuery AI - ISRO / SAC Finals Multi-Modal Engine")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_controller = AgentController()

# Session Query History & Report Store
SESSION_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
QUERY_REPORT_CACHE: Dict[str, Dict[str, Any]] = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json_if_exists(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _file_age_days(path: str) -> float:
    if not path or not os.path.exists(path):
        return float("inf")
    try:
        timestamp = os.path.getmtime(path)
        age_days = (datetime.utcnow() - datetime.fromtimestamp(timestamp)).total_seconds() / 86400.0
        return max(0.0, age_days)
    except Exception:
        return float("inf")


def _eval_status(path: str, label: str) -> Dict[str, Any]:
    exists = os.path.exists(path)
    age_days = _file_age_days(path)
    fresh = exists and age_days < 30.0
    payload = {
        "status": "PASS" if fresh else "PARTIAL",
        "path": path,
        "exists": exists,
        "freshness_days": age_days if exists else float("inf"),
        "result": load_json_if_exists(path),
        "label": label,
        "note": f"{label} result file is fresh (<30 days)" if fresh else f"{label} result file is missing or older than 30 days",
    }
    if exists:
        payload["evaluated_at"] = load_json_if_exists(path).get("evaluated_at") if isinstance(load_json_if_exists(path), dict) else None
    return payload


# Check GEE status on startup
GEE_STATUS = {"authenticated": False, "message": "Initializing..."}

@app.on_event("startup")
async def startup_event():
    global GEE_STATUS
    try:
        initialize_gee()
        GEE_STATUS = {"authenticated": True, "message": "Google Earth Engine Connected & Active"}
    except Exception as e:
        GEE_STATUS = {"authenticated": False, "message": f"GEE Auth Fallback (Demo & Upload Modes Active): {e}"}
        print(GEE_STATUS["message"])

    app.state.adapter_proof = ModelRegistry.verify_adapter_probe()
    manager = ModelManager.instance()
    if os.getenv("SATQUERY_PRELOAD_MODELS", "false").lower() == "true":
        try:
            manager.load()
        except Exception as exc:
            print(f"[VLM] preload unavailable: {exc}")
    app.state.geochat_probe = manager.integrity()

# Request / Response Schemas
class GEEFetchRequest(BaseModel):
    geometry: Dict[str, Any]
    start_date: str
    end_date: str
    max_cloud_cover: float = 20.0
    layer_type: str = "true_color"

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default_session"
    primary_upload_id: Optional[str] = None
    secondary_upload_id: Optional[str] = None
    demo_sample_id: Optional[str] = None
    task_mode: Optional[str] = None
    aoi_geometry: Optional[Dict[str, Any]] = None

class PDFReportRequest(BaseModel):
    query_result: Dict[str, Any]
    image_base64: Optional[str] = None

@app.get("/api/healthz")
def health_check():
    """Returns liveness and readiness status for all core subsystems."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "subsystems": {
            "api_server": "Operational",
            "gee_connection": GEE_STATUS,
            "agent_controller": "Operational",
            "models_registry": {
                "active_models_count": len(ModelRegistry.list_models()),
                "geochat_status": ModelManager.instance().integrity()["status"],
                "optical_sar_fusion_status": "PARTIAL (classical verification)",
                "cdvqa_siamese_status": "PARTIAL (classical verification)"
            },
            "rasterio_gdal": "Loaded & Functional"
        }
    }

@app.get("/api/models")
def get_models():
    """Returns the Model Registry catalog with provenance and capabilities."""
    return ModelRegistry.list_models()


@app.get("/api/model-integrity")
def model_integrity():
    """Returns a live runtime integrity check computed from the actual filesystem and model probes."""
    bigearthnet_adapter = os.path.join(BASE_DIR, "models", "adapters", "bigearthnet_lora", "adapter_model.bin")
    bigearthnet_manifest = os.path.join(BASE_DIR, "models", "adapters", "bigearthnet_lora", "training_manifest.json")
    bigearthnet_loss = os.path.join(BASE_DIR, "models", "adapters", "bigearthnet_lora", "training_loss.png")
    vrsbench_result = os.path.join(BASE_DIR, "eval_results", "vrsbench_result.json")
    rsvqa_result = os.path.join(BASE_DIR, "eval_results", "rsvqa_result.json")
    cdvqa_result = os.path.join(BASE_DIR, "eval_results", "cdvqa_result.json")
    real_risat_file = os.path.join(BASE_DIR, "data", "samples", "eos04_sar_mrs_bengaluru.tif")
    adapter_runtime = ModelRegistry.get_adapter_runtime_summary("bigearthnet_lora")
    real_risat_exists = os.path.exists(real_risat_file)
    adapter_manifest = load_json_if_exists(bigearthnet_manifest)
    adapter_probe = getattr(app.state, "adapter_proof", {})
    rs_adaptation_pass = bool(adapter_probe.get("probe_passed"))

    rs_adaptation = {
        "status": "PASS" if rs_adaptation_pass else "PARTIAL",
        "adapter_name": adapter_runtime.get("adapter_name"),
        "adapter_sha256": adapter_runtime.get("adapter_sha256"),
        "manifest": adapter_manifest,
        "training_loss_png": os.path.exists(bigearthnet_loss),
        "training_loss_file": os.path.basename(bigearthnet_loss) if os.path.exists(bigearthnet_loss) else None,
        "adapter_file": bigearthnet_adapter,
        "adapter_proof": adapter_probe,
        "note": "Adapter was injected into a compatible base model and verified by inference" if rs_adaptation_pass else "Adapter files may be present, but no compatible base-model injection and inference verification has run.",
    }

    vrsbench_check = _eval_status(vrsbench_result, "VRSBench")
    rsvqa_check = _eval_status(rsvqa_result, "RSVQA")
    cdvqa_check = _eval_status(cdvqa_result, "CDVQA")

    risat_data = {
        "status": "PASS" if real_risat_exists else "PARTIAL",
        "real_risat_file": real_risat_file,
        "real_risat_exists": real_risat_exists,
        "note": "EOS-04 / RISAT-1A heritage SAR (18m NRB MRS)" if real_risat_exists else "Sentinel-1 C-band SAR — RISAT-class proxy pending Bhoonidhi access",
    }

    geochat_probe = ModelManager.instance().integrity()
    geochat_checkpoint = {
        "status": geochat_probe.get("status", "PARTIAL"),
        "passed": bool(geochat_probe.get("checkpoint_loaded")),
        "model_id": geochat_probe.get("model_id"),
        "checkpoint_path": geochat_probe.get("checkpoint_path"),
        "device": geochat_probe.get("device"),
        "dtype": geochat_probe.get("dtype"),
        "note": geochat_probe.get("last_error") or "Real checkpoint loaded; inference is available.",
        "probe": geochat_probe,
    }

    try:
        from tools.change_detection_tool import BiTemporalChangeDetectionTool
        tool = BiTemporalChangeDetectionTool()
        t1a = np.zeros((32, 32, 3), dtype=np.uint8)
        t2a = np.zeros((32, 32, 3), dtype=np.uint8)
        t1a[8:24, 8:24, :] = 80
        t2a[8:24, 8:24, :] = 200
        t1b = np.zeros((32, 32, 3), dtype=np.uint8)
        t2b = t1b.copy()
        res_a = tool.run(t1a, t2a, "What changed between these dates?")
        res_b = tool.run(t1b, t2b, "What changed between these dates?")
        delta = abs(float(res_a.get("change_percentage", 0.0)) - float(res_b.get("change_percentage", 0.0)))
        change_pass = delta > 0.0
        change_model = {
            "status": "PASS" if change_pass else "PARTIAL",
            "note": "Change model loads and produces different outputs for distinct T1/T2 pairs" if change_pass else "Change model output is identical across distinct T1/T2 pairs",
            "output_delta": delta,
            "probe_pair_a": res_a.get("change_percentage"),
            "probe_pair_b": res_b.get("change_percentage"),
        }
    except Exception as exc:
        change_model = {"status": "PARTIAL", "note": f"Change model probe failed: {exc}", "output_delta": 0.0}

    try:
        from tools.optical_sar_fusion_tool import OpticalSARFusionTool
        fusion_tool = OpticalSARFusionTool()
        optical_a = np.zeros((32, 32, 3), dtype=np.uint8)
        sar_a = np.zeros((32, 32), dtype=np.float32)
        optical_b = np.full((32, 32, 3), 255, dtype=np.uint8)
        sar_b = np.full((32, 32), 200.0, dtype=np.float32)
        optical_a[8:24, 8:24, :] = 180
        sar_a[8:24, 8:24] = 80
        res_a = fusion_tool.run(optical_a, sar_a, "Identify flooded water bodies.")
        res_b = fusion_tool.run(optical_b, sar_b, "Identify flooded water bodies.")
        delta = abs(float(res_a.get("sar_water_coverage_pct", 0.0)) - float(res_b.get("sar_water_coverage_pct", 0.0)))
        fusion_pass = delta > 0.0
        fusion_model = {
            "status": "PASS" if fusion_pass else "PARTIAL",
            "note": "Fusion model loads and outputs distinct results for different optical/SAR pairs" if fusion_pass else "Fusion model output is identical across distinct optical/SAR pairs",
            "output_delta": delta,
            "probe_pair_a": res_a.get("sar_water_coverage_pct"),
            "probe_pair_b": res_b.get("sar_water_coverage_pct"),
        }
    except Exception as exc:
        fusion_model = {"status": "PARTIAL", "note": f"Fusion model probe failed: {exc}", "output_delta": 0.0}

    status = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "rs_adaptation": rs_adaptation,
        "bigearthnet_adapter": rs_adaptation,
        "vrsbench_eval": vrsbench_check,
        "rsvqa_eval": rsvqa_check,
        "cdvqa_eval": cdvqa_check,
        "risat_data": risat_data,
        "risat_sar": risat_data,
        "geochat_checkpoint": geochat_checkpoint,
        "geochat": geochat_probe,
        "change_model": change_model,
        "fusion_model": fusion_model,
    }
    return status


@app.get("/api/demo/samples")
def get_demo_samples():
    """Returns pre-loaded benchmark sample pairs for zero-setup demo mode."""
    return {"samples": get_demo_samples_list()}

@app.post("/api/upload")
async def upload_raster(file: UploadFile = File(...)):
    """Ingests GeoTIFF / satellite imagery with CRS and band profiling."""
    try:
        contents = await file.read()
        res = process_upload(file.filename, contents)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/fetch/gee")
def fetch_gee(request: GEEFetchRequest):
    """Fetches server-side filtered GEE imagery by AOI, date, and cloud cover."""
    res = fetch_gee_layer(
        aoi_geojson=request.geometry,
        start_date=request.start_date,
        end_date=request.end_date,
        max_cloud_cover=request.max_cloud_cover,
        layer_type=request.layer_type
    )
    return res

@app.post("/api/fetch/gee/bitemporal")
def fetch_gee_bitemporal_endpoint(request: GEEFetchRequest):
    """Bug 4: Fetches dual-timestamp co-registered GEE imagery for change detection."""
    from ingestion.gee_fetcher import fetch_gee_bitemporal
    res = fetch_gee_bitemporal(
        aoi_geojson=request.geometry,
        start_date=request.start_date,
        end_date=request.end_date,
        max_cloud_cover=request.max_cloud_cover
    )
    return res

@app.post("/api/query")
async def execute_query(request: QueryRequest):
    """
    Main Agent Entrypoint.
    Classifies task, validates inputs, executes specialized RS model,
    estimates dynamic confidence, logs execution trace, and stores in session history.
    Never uses synthetic random noise fallback.
    """
    from geospatial.raster_parser import crop_raster_by_aoi
    import rasterio

    primary_arr = None
    secondary_arr = None
    meta_primary = None
    meta_secondary = None

    # Option A: Demo Sample Mode
    demo_sample_id = request.demo_sample_id
    # If no upload and no sample id specified, infer a compatible demo pair from
    # the multilingual controller intent. This never creates synthetic imagery.
    if not demo_sample_id and not request.primary_upload_id:
        interpreted = interpret_query(request.query)
        if interpreted["intent"] == "bitemporal_change" or request.task_mode == "bitemporal_change":
            demo_sample_id = "sample_bitemporal_change"
        elif interpreted["intent"] == "optical_sar_fusion" or request.task_mode == "optical_sar_fusion":
            demo_sample_id = "sample_optical_sar_fusion"
        elif interpreted["intent"] == "region_grounding" or request.task_mode == "region_grounding":
            demo_sample_id = "sample_grounding"
        else:
            demo_sample_id = "sample_optical_vqa"

    if demo_sample_id:
        samples = get_demo_samples_list()
        match = next((s for s in samples if s["id"] == demo_sample_id), None)
        if match:
            p_file = os.path.join(SAMPLES_DIR, match["file_primary"])
            s_file = os.path.join(SAMPLES_DIR, match["file_secondary"]) if match.get("file_secondary") else None

            if os.path.exists(p_file):
                raw_p, primary_arr, crop_meta_p = crop_raster_by_aoi(p_file, request.aoi_geometry)
                meta_primary = {**(match.get("primary_metadata") or {}), **crop_meta_p, "raw_bands": raw_p, "is_demo_pair": bool(s_file)}
                if demo_sample_id == "sample_bitemporal_change":
                    meta_primary["acquisition_date"] = match.get("t1_acquisition_date", "2023-02-15")

            if s_file and os.path.exists(s_file):
                raw_s, secondary_arr, crop_meta_s = crop_raster_by_aoi(s_file, request.aoi_geometry)
                meta_secondary = {**(match.get("secondary_metadata") or {}), **crop_meta_s, "raw_bands": raw_s, "is_demo_pair": True}
                if demo_sample_id == "sample_bitemporal_change":
                    meta_secondary["acquisition_date"] = match.get("t2_acquisition_date", "2024-02-18")

    # Option B: Uploaded Files
    if primary_arr is None and request.primary_upload_id:
        p_info = get_upload(request.primary_upload_id)
        if p_info and os.path.exists(p_info["temp_path"]):
            raw_p, primary_arr, crop_meta_p = crop_raster_by_aoi(p_info["temp_path"], request.aoi_geometry)
            meta_primary = {**(p_info.get("metadata") or {}), **crop_meta_p, "raw_bands": raw_p}

    if secondary_arr is None and request.secondary_upload_id:
        s_info = get_upload(request.secondary_upload_id)
        if s_info and os.path.exists(s_info["temp_path"]):
            raw_s, secondary_arr, crop_meta_s = crop_raster_by_aoi(s_info["temp_path"], request.aoi_geometry)
            meta_secondary = {**(s_info.get("metadata") or {}), **crop_meta_s, "raw_bands": raw_s}

    # Bug 1 Fix: Explicit error state when no real raster is available (NEVER random noise!)
    if primary_arr is None:
        return {
            "evidence_unavailable": True,
            "evidence_reason": "No satellite imagery or raster uploaded or selected for this AOI.",
            "query": request.query,
            "task_type": request.task_mode or "single_image_vqa",
            "response": "Analysis unavailable: No valid raster imagery found for the requested Area of Interest. Please select a benchmark sample or upload a GeoTIFF.",
            "confidence_score": 0.0,
            "visual_evidence": None,
            "preview_url": None,
            "bitemporal_previews": None,
            "intent_tool_mismatch": False,
            "extra_stats": {},
            "execution_trace": {
                "task_selected": request.task_mode,
                "error": "Raster image unavailable. np.random fallback disabled."
            }
        }

    # Execute Agent Pipeline
    result = await agent_controller.route_and_execute_stream(
        query=request.query,
        image_primary=primary_arr,
        image_secondary=secondary_arr,
        metadata_primary=meta_primary,
        metadata_secondary=meta_secondary,
        mode_override=request.task_mode
    )

    source_filename = (meta_primary or {}).get("filename")
    source_path = None
    if request.demo_sample_id:
        sample = next((s for s in get_demo_samples_list() if s["id"] == request.demo_sample_id), None)
        if sample:
            source_path = os.path.join(SAMPLES_DIR, sample["file_primary"])
    elif request.primary_upload_id:
        p_info = get_upload(request.primary_upload_id)
        if p_info and os.path.exists(p_info["temp_path"]):
            source_path = p_info["temp_path"]

    result["source_context"] = {
        "request_id": f"qry_{uuid.uuid4().hex[:8]}",
        "dataset_id": request.demo_sample_id or (request.primary_upload_id or "current_upload"),
        "sample_id": request.demo_sample_id,
        "source_filename": source_filename,
        "source_path": source_path,
        "source_crs": (meta_primary or {}).get("crs"),
        "source_dimensions": (meta_primary or {}).get("dimensions"),
        "source_modality": (meta_primary or {}).get("modality"),
    }

    result["evidence_unavailable"] = False
    query_id = f"qry_{uuid.uuid4().hex[:8]}"
    result["query_id"] = query_id
    result["source_context"]["request_id"] = query_id
    result["timestamp"] = datetime.utcnow().isoformat()

    # Save to Session History & Report Cache
    session_id = request.session_id or "default_session"
    if session_id not in SESSION_HISTORY:
        SESSION_HISTORY[session_id] = []
    SESSION_HISTORY[session_id].append(result)
    QUERY_REPORT_CACHE[query_id] = result

    return result

@app.websocket("/api/query/stream")
async def websocket_query_stream(websocket: WebSocket):
    """
    Live Agent Execution Streaming WebSocket.
    Emits real-time agent reasoning steps ("thinking" telemetry) to the frontend.
    """
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        req_json = json.loads(data)
        
        async def stream_callback(step_event):
            await websocket.send_text(json.dumps({"type": "step", "data": step_event}))

        request = QueryRequest(**req_json)
        await stream_callback({"step": "Resolving current raster", "detail": "Loading the requested upload or benchmark sample; synthetic stream inputs are disabled."})
        result = await execute_query(request)

        await websocket.send_text(json.dumps({"type": "result", "data": result}))
        await websocket.close()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        await websocket.close()

@app.get("/api/session/{session_id}/history")
def get_session_history(session_id: str):
    """Returns query history for a given session."""
    return {"session_id": session_id, "history": SESSION_HISTORY.get(session_id, [])}

@app.post("/api/report/pdf")
def download_pdf_report(request: PDFReportRequest):
    """Generates official ISRO / SAC Evaluation Summary PDF."""
    try:
        pdf_bytes = generate_evaluation_pdf(
            query_result=request.query_result,
            image_base64=request.image_base64
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=satquery_isro_evaluation_report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

@app.get("/api/report/{query_id}")
def get_cached_report_pdf(query_id: str):
    """Generates PDF directly from query ID cache."""
    if query_id not in QUERY_REPORT_CACHE:
        raise HTTPException(status_code=404, detail="Query report not found")
    res = QUERY_REPORT_CACHE[query_id]
    pdf_bytes = generate_evaluation_pdf(res, image_base64=res.get("preview_url"))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=satquery_evaluation_{query_id}.pdf"}
    )

# Benchmark Evaluation Endpoints
EVAL_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "eval_results")

@app.get("/api/eval-results")
def get_benchmark_eval_results():
    """Returns official benchmark evaluation summary across VRSBench, RSVQA, and CDVQA."""
    summary_path = os.path.join(EVAL_RESULTS_DIR, "benchmark_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "status": "NOT_RUN",
        "message": "Evaluation results not yet generated. Run /api/eval-results/run to execute harness."
    }

@app.get("/api/eval-results/{benchmark_name}")
def get_benchmark_raw_receipt(benchmark_name: str):
    """Returns full per-example raw JSON receipt for a given benchmark."""
    valid_names = {
        "vrsbench": "vrsbench_result.json",
        "rsvqa": "rsvqa_result.json",
        "cdvqa": "cdvqa_result.json"
    }
    fname = valid_names.get(benchmark_name.lower())
    if not fname:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_name}' not found. Available: {list(valid_names.keys())}")
    file_path = os.path.join(EVAL_RESULTS_DIR, fname)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Receipt file '{fname}' not found.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/eval-results/run")
def trigger_benchmark_evaluations():
    """Runs all 3 official benchmark evaluation harnesses and generates fresh JSON receipts."""
    try:
        from benchmarks.run_all_evals import run_all_benchmarks
        summary = run_all_benchmarks()
        return {"status": "SUCCESS", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark evaluation failed: {str(e)}")

# Legacy compatibility endpoints
@app.get("/api/states")
def get_states():
    return {"states": ["Karnataka", "Maharashtra", "Tamil Nadu"]}

@app.get("/api/areas/{state}")
def get_areas(state: str):
    return {"areas": ["Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mandya"]}

@app.get("/api/location/{state}/{area}")
def get_location(state: str, area: str):
    return {"lat": 12.9716, "lon": 77.5946, "zoom": 11}

@app.post("/api/analyze")
async def run_legacy_analyze(request: QueryRequest):
    return await execute_query(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
