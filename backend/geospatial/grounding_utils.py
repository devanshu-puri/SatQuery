"""
Grounding and Vector Utility.
Transforms normalized bounding boxes [ymin, xmin, ymax, xmax] (0-1000 or 0.0-1.0)
from Vision-Language Models into GeoJSON Polygons and Features with EPSG:4326 reprojection.
"""

from typing import List, Dict, Any, Tuple
import pyproj
from rasterio.transform import Affine

def normalize_box(box: List[float]) -> Tuple[float, float, float, float]:
    """Ensures bbox coordinates are in [0.0, 1.0] normalized range."""
    ymin, xmin, ymax, xmax = box
    if any(v > 1.0 for v in [ymin, xmin, ymax, xmax]):
        # Scaled from 0-1000 (common in PaliGemma/GeoChat)
        return ymin / 1000.0, xmin / 1000.0, ymax / 1000.0, xmax / 1000.0
    return ymin, xmin, ymax, xmax

def pixel_box_to_geojson_polygon(
    box_norm: List[float],
    width: int,
    height: int,
    affine_transform: List[float],
    crs_str: str,
    label: str = "Target",
    confidence: float = 0.90
) -> Dict[str, Any]:
    """
    Converts a normalized bounding box into a GeoJSON Feature Polygon in EPSG:4326.
    """
    ymin_norm, xmin_norm, ymax_norm, xmax_norm = normalize_box(box_norm)

    # Convert to pixel space
    px_min = xmin_norm * width
    px_max = xmax_norm * width
    py_min = ymin_norm * height
    py_max = ymax_norm * height

    # Affine transform: [a, b, c, d, e, f]
    # x_geo = a * px + b * py + c
    # y_geo = d * px + e * py + f
    aff = Affine(*affine_transform[:6])

    # 4 corners in native raster CRS
    top_left = aff * (px_min, py_min)
    top_right = aff * (px_max, py_min)
    bottom_right = aff * (px_max, py_max)
    bottom_left = aff * (px_min, py_max)

    # Set up reprojection to EPSG:4326 (WGS84 Lon/Lat)
    if crs_str and "4326" not in crs_str:
        try:
            transformer = pyproj.Transformer.from_crs(crs_str, "EPSG:4326", always_xy=True)
            def reproject(pt):
                lon, lat = transformer.transform(pt[0], pt[1])
                return [round(lon, 6), round(lat, 6)]
        except Exception:
            def reproject(pt):
                return [round(pt[0], 6), round(pt[1], 6)]
    else:
        def reproject(pt):
            return [round(pt[0], 6), round(pt[1], 6)]

    p1 = reproject(top_left)
    p2 = reproject(top_right)
    p3 = reproject(bottom_right)
    p4 = reproject(bottom_left)

    coordinates = [[p1, p2, p3, p4, p1]]

    return {
        "type": "Feature",
        "properties": {
            "label": label,
            "confidence": round(confidence, 3),
            "bbox_norm": [round(ymin_norm, 4), round(xmin_norm, 4), round(ymax_norm, 4), round(xmax_norm, 4)]
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": coordinates
        }
    }

def build_geojson_feature_collection(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Wraps feature list in a GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": features
    }
