"""
Agentic Controller & Tool Dispatcher for SatQuery AI.
Analyzes query semantics AND input file metadata (band count, modalities, temporal pairs),
dispatches to specialized RS tools from the Model Registry, and generates the auditable execution trace.
Supports async execution and live streaming event callbacks.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
import numpy as np
from models.registry import ModelRegistry
from tools import (
    SingleImageVQATool,
    RegionGroundingTool,
    BiTemporalChangeDetectionTool,
    OpticalSARFusionTool
)

class AgentController:
    """Agentic orchestrator dynamically matching query and geospatial inputs to specialist tools."""

    def __init__(self):
        self.vqa_tool = SingleImageVQATool()
        self.grounding_tool = RegionGroundingTool()
        self.change_tool = BiTemporalChangeDetectionTool()
        self.fusion_tool = OpticalSARFusionTool()

    async def route_and_execute_stream(
        self,
        query: str,
        image_primary: np.ndarray,
        image_secondary: Optional[np.ndarray] = None,
        metadata_primary: Optional[Dict[str, Any]] = None,
        metadata_secondary: Optional[Dict[str, Any]] = None,
        mode_override: Optional[str] = None,
        stream_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes routing and tool execution while broadcasting live step-by-step telemetry events.
        """
        start_time = time.time()
        q_lower = query.lower()

        async def emit(step: str, detail: str):
            if stream_callback:
                if asyncio.iscoroutinefunction(stream_callback):
                    await stream_callback({"step": step, "detail": detail, "timestamp": time.time()})
                else:
                    stream_callback({"step": step, "detail": detail, "timestamp": time.time()})

        # Step 1: Query & Modality Analysis
        await emit("Classifying Query Intent", f"Parsing natural language semantics: '{query[:60]}...'")
        await asyncio.sleep(0.05)

        has_secondary = image_secondary is not None
        modality_primary = metadata_primary.get("modality", "Optical") if metadata_primary else "Optical"
        modality_secondary = metadata_secondary.get("modality", "Optical") if metadata_secondary else "Optical"

        is_sar_opt_pair = has_secondary and (
            ("sar" in modality_primary.lower() and "optical" in modality_secondary.lower()) or
            ("optical" in modality_primary.lower() and "sar" in modality_secondary.lower())
        )
        is_temporal_pair = has_secondary and not is_sar_opt_pair

        # Step 2: Compatibility Validation & Task Resolution
        await emit("Validating Input Compatibility", f"Primary: {modality_primary} | Secondary Pair: {'Available' if has_secondary else 'None'}")
        await asyncio.sleep(0.05)

        if mode_override:
            task_type = mode_override
            rationale = f"Explicitly requested task mode override: '{mode_override}'."
        elif is_sar_opt_pair or any(w in q_lower for w in ["fusion", "sar", "radar", "cross-modal", "all-weather"]):
            task_type = "optical_sar_fusion"
            rationale = "Cross-modal Optical + SAR radar inputs and/or query requesting multi-sensor fusion."
        elif is_temporal_pair or any(w in q_lower for w in ["change", "difference", "compare", "evolution", "before and after", "temporal"]):
            task_type = "bitemporal_change"
            rationale = "Bi-temporal multi-date satellite scenes detected and/or change-detection query semantics."
        elif any(w in q_lower for w in ["where", "locate", "ground", "find", "detect", "bounding", "segment", "outline", "box"]):
            task_type = "region_grounding"
            rationale = "Text-guided spatial feature localization requiring vector bounding polygons."
        else:
            task_type = "single_image_vqa"
            rationale = "Single-scene Visual Question Answering on optical/multispectral reflectance."

        # Step 3: Model & Adapter Selection
        if task_type == "optical_sar_fusion":
            model_meta = ModelRegistry.get_model_info("optical_sar_fusion_net")
            model_name = model_meta["name"]
            adapter_id = model_meta["adapter_id"]
            tool_name = "OpticalSARFusionTool"

            await emit(f"Loading {adapter_id}", f"Binding {model_name} cross-attention weights...")
            await asyncio.sleep(0.08)

            sar_input = image_secondary if image_secondary is not None else (np.mean(image_primary, axis=-1) * 0.8)
            await emit("Executing Cross-Modal Fusion", "Jointly computing optical reflectance & SAR backscatter...")
            
            res = self.fusion_tool.run(
                rgb_optical=image_primary,
                sar_array=sar_input,
                query=query,
                metadata_opt=metadata_primary,
                metadata_sar=metadata_secondary
            )
            response_text = res["explanation"]
            confidence = res["confidence_score"]
            visual_evidence = res.get("visual_evidence")
            preview_url = res.get("fused_preview_url")
            extra_stats = {
                "sar_water_coverage_pct": res.get("sar_water_coverage_pct"),
                "sar_urban_coverage_pct": res.get("sar_urban_coverage_pct")
            }

        elif task_type == "bitemporal_change":
            model_meta = ModelRegistry.get_model_info("cdvqa_siamese_vlm")
            model_name = model_meta["name"]
            adapter_id = model_meta["adapter_id"]
            tool_name = "BiTemporalChangeDetectionTool"

            await emit(f"Loading {adapter_id}", f"Binding {model_name} Siamese weights...")
            await asyncio.sleep(0.08)

            t2_input = image_secondary if image_secondary is not None else np.fliplr(image_primary)
            await emit("Executing Bi-Temporal Change Detection", "Calculating radiometric difference vectors (T1 vs T2)...")

            res = self.change_tool.run(
                rgb_t1=image_primary,
                rgb_t2=t2_input,
                query=query,
                metadata_t1=metadata_primary,
                metadata_t2=metadata_secondary
            )
            response_text = res["explanation"]
            confidence = res["confidence_score"]
            visual_evidence = res.get("visual_evidence")
            preview_url = res.get("difference_map_url")
            extra_stats = {
                "change_percentage": res.get("change_percentage"),
                "detected_clusters_count": res.get("detected_clusters_count")
            }

        elif task_type == "region_grounding":
            model_meta = ModelRegistry.get_model_info("geochat_7b")
            model_name = model_meta["name"]
            adapter_id = model_meta["adapter_id"]
            tool_name = "RegionGroundingTool"

            await emit(f"Loading {adapter_id}", f"Binding {model_name} region grounding projector...")
            await asyncio.sleep(0.08)

            await emit("Executing Region Grounding", f"Extracting spatial feature clusters for '{query}'...")
            res = self.grounding_tool.run(
                rgb_array=image_primary,
                query=query,
                metadata=metadata_primary
            )
            response_text = f"Region Grounding: Identified {res['detected_count']} instance(s) matching '{res['target_label']}'. {res['caption']}"
            confidence = res["confidence_score"]
            visual_evidence = res.get("visual_evidence")
            preview_url = None
            extra_stats = {
                "detected_count": res.get("detected_count"),
                "target_label": res.get("target_label")
            }

        else: # single_image_vqa
            model_meta = ModelRegistry.get_model_info("geochat_7b")
            model_name = model_meta["name"]
            adapter_id = model_meta["adapter_id"]
            tool_name = "SingleImageVQATool"

            await emit(f"Loading {adapter_id}", f"Binding {model_name} RS-VQA weights...")
            await asyncio.sleep(0.08)

            await emit("Executing RS-VQA Inference", "Performing multi-spectral feature question answering...")
            res = self.vqa_tool.run(
                rgb_array=image_primary,
                query=query,
                metadata=metadata_primary
            )
            response_text = res["answer"]
            confidence = res["confidence_score"]
            visual_evidence = None
            preview_url = None
            extra_stats = {
                "category": res.get("category"),
                "spectral_diagnostics": res.get("spectral_diagnostics")
            }

        # Step 4: Confidence & Trace Assembly
        await emit("Synthesizing Auditable Execution Trace", f"Confidence estimated at {int(confidence * 100)}% | Task: {task_type}")
        latency_ms = round((time.time() - start_time) * 1000, 2)

        execution_trace = {
            "task_selected": task_type,
            "router_decision": rationale,
            "model_invoked": model_name,
            "adapter_used": adapter_id,
            "tools_executed": [tool_name],
            "input_metadata": {
                "primary_crs": metadata_primary.get("crs", "EPSG:4326") if metadata_primary else "EPSG:4326",
                "primary_dimensions": metadata_primary.get("dimensions", {"width": image_primary.shape[1], "height": image_primary.shape[0]}) if metadata_primary else {"width": image_primary.shape[1], "height": image_primary.shape[0]},
                "primary_modality": modality_primary,
                "has_secondary_pair": has_secondary,
                "secondary_modality": modality_secondary if has_secondary else "None"
            },
            "confidence_score": round(confidence, 3),
            "latency_ms": latency_ms
        }

        return {
            "query": query,
            "task_type": task_type,
            "response": response_text,
            "confidence_score": round(confidence, 3),
            "visual_evidence": visual_evidence,
            "preview_url": preview_url,
            "extra_stats": extra_stats,
            "execution_trace": execution_trace
        }

    def route_and_execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper."""
        return asyncio.run(self.route_and_execute_stream(*args, **kwargs))
