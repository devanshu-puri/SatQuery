"""
Tool 2: Text-Guided Region Grounding & Captioning Tool.
Locates target spatial features/land-covers specified in natural language queries
and outputs bounding boxes with EPSG:4326 GeoJSON vector polygons.
"""

from typing import Dict, Any, Optional, List
import numpy as np
from models.geochat_wrapper import GeoChatVLM
from geospatial.grounding_utils import pixel_box_to_geojson_polygon, build_geojson_feature_collection

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
        ground_res = self.vlm.ground_regions(rgb_array, query, metadata)
        caption_res = self.vlm.generate_caption(rgb_array, metadata)

        # Convert normalized bounding boxes to real-world GeoJSON features
        features = []
        if metadata:
            width = metadata["dimensions"]["width"]
            height = metadata["dimensions"]["height"]
            affine = metadata["affine_transform"]
            crs_str = metadata["crs"]
        else:
            height, width, _ = rgb_array.shape
            affine = [1.0, 0.0, 0.0, 0.0, -1.0, 0.0]
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

        return {
            "tool_name": self.name,
            "query": query,
            "target_label": ground_res["target_label"],
            "detected_count": ground_res["detected_count"],
            "caption": caption_res["caption"],
            "confidence_score": ground_res["confidence"],
            "visual_evidence": geojson_fc,
            "bounding_boxes_norm": ground_res["bounding_boxes_norm"]
        }
