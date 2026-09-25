"""
Sample Dataset Loader for Offline Zero-Setup Demo Mode.
Loads pre-cached benchmark samples from BigEarthNet, VRSBench, CDVQA, and Cartosat/RISAT.
"""

import os
from typing import List, Dict, Any
from geospatial import parse_geotiff

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")

DEMO_SAMPLES = [
    {
        "id": "sample_optical_vqa",
        "title": "ISRO Cartosat-2S Optical Scene (VRSBench / RSVQA)",
        "task_recommended": "single_image_vqa",
        "query_recommended": "What is the agricultural crop condition and land use in this scene?",
        "file_primary": "cartosat_optical_bengaluru.tif",
        "file_secondary": None,
        "description": "High-resolution optical scene over Bengaluru Urban with active vegetation and built-up structures.",
        "modality": "Optical RGB (Cartosat-2S)",
        "provenance": "ISRO Bhuvan / VRSBench Benchmark Subset"
    },
    {
        "id": "sample_grounding",
        "title": "Transportation & Forest Grounding (VRSBench)",
        "task_recommended": "region_grounding",
        "query_recommended": "Locate all dense vegetation areas and built structures",
        "file_primary": "cartosat_optical_bengaluru.tif",
        "file_secondary": None,
        "description": "Text-guided region localization predicting EPSG:4326 GeoJSON vector bounding polygons.",
        "modality": "Optical RGB",
        "provenance": "VRSBench (arXiv:2311.13788)"
    },
    {
        "id": "sample_bitemporal_change",
        "title": "Bi-Temporal Urban & Vegetation Change (CDVQA / LEVIR-CD)",
        "task_recommended": "bitemporal_change",
        "query_recommended": "Compare before and after satellite images to detect significant land-cover change",
        "file_primary": "bitemporal_t1_2023.tif",
        "file_secondary": "bitemporal_t2_2024.tif",
        "description": "Co-registered pair (2023 vs 2024) revealing structural expansion and vegetation clearance.",
        "modality": "Bi-Temporal Optical Pair (T1, T2)",
        "provenance": "CDVQA / LEVIR-CD Benchmark"
    },
    {
        "id": "sample_optical_sar_fusion",
        "title": "Optical + EOS-04 (RISAT-1A Heritage) C-Band SAR Fusion (18m NRB)",
        "task_recommended": "optical_sar_fusion",
        "query_recommended": "Perform optical and EOS-04 RISAT-1A SAR radar cross-modal fusion for all-weather water and urban mapping",
        "file_primary": "cartosat_optical_bengaluru.tif",
        "file_secondary": "eos04_sar_mrs_bengaluru.tif",
        "description": "Co-registered ISRO Cartosat-2S Optical + ISRO EOS-04 (RISAT-1A Payload) C-band SAR Medium Resolution ScanSAR (MRS, 18m NRB dual-pol VV/VH).",
        "modality": "Cross-Modal (Cartosat-2S + EOS-04/RISAT-1A SAR)",
        "provenance": "ISRO Bhuvan / Bhoonidhi Open Data Archive (EOS-04 Level-2B NRB MRS)"
    },
    {
        "id": "sample_sentinel1_fusion",
        "title": "Optical + Sentinel-1 C-Band SAR Fusion (10m IW GRD)",
        "task_recommended": "optical_sar_fusion",
        "query_recommended": "Combine Sentinel-2 optical with Sentinel-1 SAR dual-pol backscatter to validate structural footprints",
        "file_primary": "cartosat_optical_bengaluru.tif",
        "file_secondary": "sentinel1_sar_vv_vh.tif",
        "description": "Co-registered Optical + Sentinel-1 C-band SAR (VV/VH dual-pol, 10m GSD). Multi-sensor architecture validated across both EOS-04 and Sentinel-1 SAR standards.",
        "modality": "Cross-Modal (Optical + Sentinel-1 SAR)",
        "provenance": "BigEarthNet-MM / ESA Copernicus Open Access Hub"
    }
]

def get_demo_samples_list() -> List[Dict[str, Any]]:
    """Returns catalog of demo samples with parsed metadata and previews."""
    results = []
    for s in DEMO_SAMPLES:
        p_path = os.path.join(SAMPLES_DIR, s["file_primary"])
        s_path = os.path.join(SAMPLES_DIR, s["file_secondary"]) if s["file_secondary"] else None

        p_meta = parse_geotiff(p_path) if os.path.exists(p_path) else None
        s_meta = parse_geotiff(s_path) if s_path and os.path.exists(s_path) else None

        entry = {
            **s,
            "primary_metadata": p_meta,
            "secondary_metadata": s_meta,
            "preview_url": p_meta.get("preview_url") if p_meta else None
        }
        if s["id"] == "sample_bitemporal_change":
            entry["t1_acquisition_date"] = "2023-02-15"
            entry["t2_acquisition_date"] = "2024-02-18"
            entry["t1_preview_url"] = p_meta.get("preview_url") if p_meta else None
            entry["t2_preview_url"] = s_meta.get("preview_url") if s_meta else None
        results.append(entry)
    return results
