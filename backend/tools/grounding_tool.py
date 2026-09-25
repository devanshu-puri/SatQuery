"""
Tool 2: Text-Guided Region Grounding & Captioning Tool.
Locates target spatial features/land-covers specified in natural language queries
and outputs bounding boxes with EPSG:4326 GeoJSON vector polygons.
"""

import time
from typing import Dict, Any, Optional, List
import numpy as np
from models.geochat_wrapper import GeoChatVLM
from geospatial.grounding_utils import pixel_box_to_geojson_polygon, build_geojson_feature_collection
from geospatial.raster_parser import generate_preview_base64

class RegionGroundingTool:
    name = "RegionGroundingTool"
    description = "Grounds natural language objects in remote sensing imagery to GeoJSON bounding polygons."

    def __init__(self):
        self.vlm = GeoChatVLM(model_id="geochat_7b")

    def run(
        self,
        rgb_array: np.ndarray,
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        start_t = time.perf_counter()
        ground_res = self.vlm.ground_regions(rgb_array, query, metadata)
        caption_res = self.vlm.generate_caption(rgb_array, metadata)

        # Convert normalized bounding boxes to real-world GeoJSON features
        features = []
        if metadata and "dimensions" in metadata and "affine_transform" in metadata:
            width = metadata["dimensions"]["width"]
            height = metadata["dimensions"]["height"]
            affine = metadata["affine_transform"]
            crs_str = metadata.get("crs", "EPSG:4326")
        else:
            height, width = rgb_array.shape[:2]
            affine = [0.0001, 0.0, 77.59, 0.0, -0.0001, 12.97]
            crs_str = "EPSG:4326"

        for idx, box in enumerate(ground_res["bounding_boxes_norm"]):
            lbl = ground_res["labels"][idx] if idx < len(ground_res["labels"]) else ground_res["target_label"]
            feat = pixel_box_to_geojson_polygon(
                box_norm=box,
                width=width,
                height=height,
                affine_transform=affine,
                crs_str=crs_str,
                label=lbl,
                confidence=ground_res["confidence"]
            )
            features.append(feat)

        geojson_fc = build_geojson_feature_collection(features)
        preview_url = generate_preview_base64(rgb_array[:, :, :3])
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

        return {
            "tool_name": self.name,
            "query": query,
            "target_label": ground_res["target_label"],
            "detected_count": ground_res["detected_count"],
            "caption": caption_res["caption"],
            "confidence_score": ground_res["confidence"],
            "visual_evidence": geojson_fc,
            "preview_url": preview_url,
            "bounding_boxes_norm": ground_res["bounding_boxes_norm"],
            "prompt_sent_to_model": ground_res.get("prompt_sent_to_model"),
            "confidence_penalties": ground_res.get("confidence_penalties", []),
            "internal_latency_ms": elapsed_ms
        }
