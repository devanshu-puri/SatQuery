"""
Full End-to-End Automated Validation Suite for SatQuery AI
Covers Groups A, B, C, D, E, F, Semantic Routing, Georeferencing, Error Handling,
and Auditable Execution Tracing.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import urllib.request
import base64
import numpy as np
from io import BytesIO
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"

def post_json(endpoint, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(endpoint):
    with urllib.request.urlopen(f"{BASE_URL}{endpoint}") as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_e2e_suite():
    print("=" * 80)
    print("SATQUERY AI: FULL COMPREHENSIVE E2E VERIFICATION SUITE")
    print("=" * 80)

    test_results = []

    # -------------------------------------------------------------
    # GROUP A: SINGLE IMAGE VQA
    # -------------------------------------------------------------
    print("\n[GROUP A: SINGLE IMAGE VQA]")
    # A1
    r_a1 = post_json("/api/query", {
        "query": "Is there a water body in this image?",
        "demo_sample_id": "sample_optical_vqa",
        "task_mode": "single_image_vqa"
    })
    ok_a1 = (
        r_a1["task_type"] == "single_image_vqa" and
        isinstance(r_a1["response"], str) and
        len(r_a1["response"]) > 20 and
        r_a1.get("confidence_score") is not None and
        r_a1.get("preview_url") is not None
    )
    test_results.append(("A1 - Single Image VQA (Water Presence)", "Single Optical", "Is there a water body in this image?", "single_image_vqa", "GeoChat-7B", "Text + Evidence Preview", "PASS" if ok_a1 else "FAIL"))
    print(f"  A1 (Water Check): Status={'PASS' if ok_a1 else 'FAIL'} | Conf={r_a1.get('confidence_score')}")
    print(f"  Response: {r_a1['response'][:100]}...")

    # A2
    r_a2 = post_json("/api/query", {
        "query": "What type of land cover is dominant in this image?",
        "demo_sample_id": "sample_optical_vqa",
        "task_mode": "single_image_vqa"
    })
    ok_a2 = (
        r_a2["task_type"] == "single_image_vqa" and
        "dominant" in r_a2["response"].lower() and
        r_a2.get("extra_stats", {}).get("spectral_diagnostics") is not None
    )
    test_results.append(("A2 - Single Image VQA (Dominant Land Cover)", "Single Optical", "What type of land cover is dominant in this image?", "single_image_vqa", "GeoChat-7B", "Text + Diagnostics", "PASS" if ok_a2 else "FAIL"))
    print(f"  A2 (Dominant Land Cover): Status={'PASS' if ok_a2 else 'FAIL'} | Category={r_a2.get('extra_stats', {}).get('category')}")
    print(f"  Response: {r_a2['response'][:100]}...")

    # -------------------------------------------------------------
    # GROUP B: SINGLE IMAGE CAPTIONING
    # -------------------------------------------------------------
    print("\n[GROUP B: SINGLE IMAGE CAPTIONING]")
    r_b = post_json("/api/query", {
        "query": "Describe the land-cover and major objects visible in this image.",
        "demo_sample_id": "sample_optical_vqa",
        "task_mode": "single_image_vqa"
    })
    ans_b = r_b["response"].lower()
    ok_b = (
        r_b["task_type"] == "single_image_vqa" and
        any(w in ans_b for w in ["vegetation", "cropland", "crop"]) and
        any(w in ans_b for w in ["built-up", "infrastructure", "structure"])
    )
    test_results.append(("B - Single Image Captioning", "Single Optical", "Describe the land-cover and major objects visible in this image.", "single_image_vqa", "GeoChat-7B", "Descriptive Scene Text", "PASS" if ok_b else "FAIL"))
    print(f"  B (Captioning): Status={'PASS' if ok_b else 'FAIL'}")
    print(f"  Response: {r_b['response'][:100]}...")

    # -------------------------------------------------------------
    # GROUP C: SINGLE IMAGE GROUNDING
    # -------------------------------------------------------------
    print("\n[GROUP C: SINGLE IMAGE GROUNDING]")
    r_c = post_json("/api/query", {
        "query": "Highlight the water body referred to in the query.",
        "demo_sample_id": "sample_grounding",
        "task_mode": "region_grounding"
    })
    evidence_c = r_c.get("visual_evidence")
    has_geojson = (
        evidence_c is not None and
        evidence_c.get("type") == "FeatureCollection" and
        len(evidence_c.get("features", [])) > 0
    )
    ok_c = (
        r_c["task_type"] == "region_grounding" and
        has_geojson and
        r_c.get("preview_url") is not None
    )
    feature_count = len(evidence_c.get("features", [])) if evidence_c else 0
    test_results.append(("C - Single Image Region Grounding", "Single Optical", "Highlight the water body referred to in the query.", "region_grounding", "GeoChat-7B", f"GeoJSON Vector ({feature_count} polygons)", "PASS" if ok_c else "FAIL"))
    print(f"  C (Grounding): Status={'PASS' if ok_c else 'FAIL'} | Polygons Generated={feature_count}")
    if has_geojson:
        first_feat = evidence_c["features"][0]
        print(f"  Vector CRS: EPSG:4326 | Coordinates sample: {first_feat['geometry']['coordinates'][0][:2]}")

    # -------------------------------------------------------------
    # GROUP D: BI-TEMPORAL CHANGE ANALYSIS
    # -------------------------------------------------------------
    print("\n[GROUP D: BI-TEMPORAL CHANGE ANALYSIS]")
    r_d = post_json("/api/query", {
        "query": "What changed between these two dates, and where did the change occur?",
        "demo_sample_id": "sample_bitemporal_change",
        "task_mode": "bitemporal_change"
    })
    ok_d = (
        r_d["task_type"] == "bitemporal_change" and
        r_d.get("extra_stats", {}).get("change_percentage") is not None and
        r_d.get("bitemporal_previews") is not None and
        r_d.get("preview_url") is not None and
        r_d.get("visual_evidence") is not None
    )
    chg_pct = r_d.get("extra_stats", {}).get("change_percentage")
    test_results.append(("D - Bi-Temporal Change Analysis", "Dual Co-registered T1/T2", "What changed between these two dates, and where did the change occur?", "bitemporal_change", "CDVQA Siamese-VLM", f"Change map + {chg_pct}% change", "PASS" if ok_d else "FAIL"))
    print(f"  D (Change Analysis): Status={'PASS' if ok_d else 'FAIL'} | Surface Change: {chg_pct}% | Clusters: {r_d.get('extra_stats', {}).get('detected_clusters_count')}")
    print(f"  Response: {r_d['response'][:100]}...")

    # -------------------------------------------------------------
    # GROUP E: CHANGE DIRECTION (INCREASED/DECREASED/UNCHANGED)
    # -------------------------------------------------------------
    print("\n[GROUP E: CHANGE DIRECTION]")
    r_e = post_json("/api/query", {
        "query": "Has the built-up area increased, decreased, or remained unchanged?",
        "demo_sample_id": "sample_bitemporal_change",
        "task_mode": "bitemporal_change"
    })
    resp_e = r_e["response"]
    built_dir = r_e.get("extra_stats", {}).get("built_direction")
    ok_e = (
        r_e["task_type"] == "bitemporal_change" and
        built_dir in ["INCREASED", "DECREASED", "UNCHANGED"] and
        built_dir in resp_e
    )
    test_results.append(("E - Change Direction Assessment", "Dual Co-registered T1/T2", "Has the built-up area increased, decreased, or remained unchanged?", "bitemporal_change", "CDVQA Siamese-VLM", f"Direction: {built_dir}", "PASS" if ok_e else "FAIL"))
    print(f"  E (Change Direction): Status={'PASS' if ok_e else 'FAIL'} | Direction Identified: {built_dir}")
    print(f"  T1 Built-Up: {r_e.get('extra_stats', {}).get('t1_built_pct')}% -> T2 Built-Up: {r_e.get('extra_stats', {}).get('t2_built_pct')}%")

    # -------------------------------------------------------------
    # GROUP F: OPTICAL + SAR CROSS-MODAL FUSION
    # -------------------------------------------------------------
    print("\n[GROUP F: OPTICAL + SAR CROSS-MODAL ANALYSIS]")
    r_f = post_json("/api/query", {
        "query": "Use the optical and SAR images together to identify built-up and water-covered regions.",
        "demo_sample_id": "sample_optical_sar_fusion",
        "task_mode": "optical_sar_fusion"
    })
    sar_water = r_f.get("extra_stats", {}).get("sar_water_coverage_pct")
    sar_urban = r_f.get("extra_stats", {}).get("sar_urban_coverage_pct")
    ok_f = (
        r_f["task_type"] == "optical_sar_fusion" and
        sar_water is not None and
        sar_urban is not None and
        r_f.get("preview_url") is not None
    )
    test_results.append(("F - Optical + SAR Cross-Modal Fusion", "Optical + C-Band SAR Pair", "Use the optical and SAR images together to identify built-up and water-covered regions.", "optical_sar_fusion", "OpticalSARFusionNet", f"Fused Map (Water: {sar_water}%, Urban: {sar_urban}%)", "PASS" if ok_f else "FAIL"))
    print(f"  F (Cross-Modal Fusion): Status={'PASS' if ok_f else 'FAIL'} | SAR Water: {sar_water}% | SAR Urban: {sar_urban}%")
    print(f"  Response: {r_f['response'][:100]}...")

    # -------------------------------------------------------------
    # GROUP G: SEMANTIC INTENT ROUTING (NO MODE OVERRIDE)
    # -------------------------------------------------------------
    print("\n[GROUP G: SEMANTIC INTENT ROUTING - AUTO-CLASSIFICATION]")
    semantic_queries = [
        ("Is there a water body?", "single_image_vqa"),
        ("Describe this image.", "single_image_vqa"),
        ("Where is the water body?", "region_grounding"),
        ("What changed between these two dates?", "bitemporal_change"),
        ("Did urban development increase?", "bitemporal_change"),
        ("Are there more constructed areas now?", "bitemporal_change"),
        ("Show me the lake.", "region_grounding"),
        ("Mark the water.", "region_grounding"),
        ("Use the optical and SAR images together to identify built-up areas.", "optical_sar_fusion")
    ]

    for q, expected_intent in semantic_queries:
        res = post_json("/api/query", {"query": q})
        actual_intent = res.get("task_type")
        match = (actual_intent == expected_intent)
        status = "PASS" if match else "FAIL"
        test_results.append((f"Semantic Routing: '{q[:25]}...'", "Auto Inferred", q, expected_intent, res.get("execution_trace", {}).get("model_invoked"), actual_intent, status))
        print(f"  Query: \"{q}\" -> Classified: {actual_intent} (Expected: {expected_intent}) | [{status}]")

    # -------------------------------------------------------------
    # GROUP H: GEOREFERENCED DATA HANDLING
    # -------------------------------------------------------------
    print("\n[GROUP H: GEOREFERENCED DATA HANDLING]")
    res_geo = post_json("/api/query", {
        "query": "Give coordinates and bounding extent",
        "demo_sample_id": "sample_optical_vqa",
        "task_mode": "single_image_vqa"
    })
    trace_geo = res_geo.get("execution_trace", {}).get("input_metadata", {})
    crs = trace_geo.get("primary_crs")
    dims = trace_geo.get("primary_dimensions")
    ok_geo = (crs == "EPSG:4326" and dims.get("width") in [256, 512] and dims.get("height") in [256, 512])
    test_results.append(("H - Georeferenced Coordinates & Transform", "GeoTIFF EPSG:4326", "Give coordinates and bounding extent", "single_image_vqa", "GeoChat-7B", f"CRS: {crs}, Dims: {dims['width']}x{dims['height']}", "PASS" if ok_geo else "FAIL"))
    print(f"  Georeferencing: Status={'PASS' if ok_geo else 'FAIL'} | CRS: {crs} | Dims: {dims}")

    # -------------------------------------------------------------
    # GROUP I: ERROR HANDLING & INPUT VALIDATION
    # -------------------------------------------------------------
    print("\n[GROUP I: ERROR HANDLING & VALIDATION]")
    # 1. Missing secondary image when user manually forces bitemporal change on single image
    # Note: we test by sending a primary upload id without secondary upload id
    sample_path = os.path.join(os.path.dirname(__file__), "data", "samples", "cartosat_optical_bengaluru.tif")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    # Upload single file
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test_single.tif"\r\n'
        f"Content-Type: image/tiff\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req_up = urllib.request.Request(
        f"{BASE_URL}/api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req_up) as resp_up:
        up_data = json.loads(resp_up.read().decode("utf-8"))
    upload_id = up_data["upload_id"]

    # Now attempt bitemporal change with only 1 uploaded image
    r_err_change = post_json("/api/query", {
        "query": "What changed over time?",
        "primary_upload_id": upload_id,
        "task_mode": "bitemporal_change"
    })
    ok_err_change = ("missing secondary" in r_err_change.get("response", "").lower() or r_err_change.get("execution_trace", {}).get("status") == "VALIDATION_FAILED")
    test_results.append(("I1 - Error Handling: Missing Secondary Temporal Scene", "Single Upload", "What changed over time?", "bitemporal_change", "AgentController Guardrail", "Clear Rejection / Validation Warning", "PASS" if ok_err_change else "FAIL"))
    print(f"  Error Handling (Missing T2): Status={'PASS' if ok_err_change else 'FAIL'}")
    print(f"  Response: {r_err_change['response'][:90]}...")

    # 2. Missing SAR pair when user forces optical_sar_fusion on single image
    r_err_sar = post_json("/api/query", {
        "query": "Use optical and SAR together",
        "primary_upload_id": upload_id,
        "task_mode": "optical_sar_fusion"
    })
    ok_err_sar = ("missing sar" in r_err_sar.get("response", "").lower() or r_err_sar.get("execution_trace", {}).get("status") == "VALIDATION_FAILED")
    test_results.append(("I2 - Error Handling: Missing SAR Sensor Modality", "Single Upload", "Use optical and SAR together", "optical_sar_fusion", "AgentController Guardrail", "Clear Rejection / Validation Warning", "PASS" if ok_err_sar else "FAIL"))
    print(f"  Error Handling (Missing SAR): Status={'PASS' if ok_err_sar else 'FAIL'}")
    print(f"  Response: {r_err_sar['response'][:90]}...")

    # -------------------------------------------------------------
    # SUMMARY TEST MATRIX TABLE
    # -------------------------------------------------------------
    print("\n" + "=" * 105)
    print(f"{'Test':<40} | {'Input':<15} | {'Expected Task':<18} | {'Status':<8}")
    print("-" * 105)
    total_pass = 0
    for name, inp, q, task, model, out, status in test_results:
        print(f"{name:<40} | {inp:<15} | {task:<18} | {status:<8}")
        if status == "PASS":
            total_pass += 1
    print("=" * 105)
    print(f"TOTAL: {total_pass}/{len(test_results)} Tests Passed ({total_pass/len(test_results)*100:.1f}%)")

if __name__ == "__main__":
    run_e2e_suite()
