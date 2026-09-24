"""
Upload Ingestion & Validation Pipeline for GeoTIFFs, Multi-Spectral Rasters, and Dual Pairs.
"""

import os
import tempfile
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image
from geospatial import parse_geotiff, normalize_to_8bit_rgb, generate_preview_base64

UPLOAD_STORAGE: Dict[str, Dict[str, Any]] = {}

def process_upload(filename: str, contents: bytes) -> Dict[str, Any]:
    """
    Validates uploaded file format, parses spatial and spectral metadata,
    and caches the raster in memory storage.
    """
    suffix = os.path.splitext(filename)[1].lower()
    if suffix not in [".tif", ".tiff", ".geotiff", ".png", ".jpg", ".jpeg"]:
        raise ValueError(f"Unsupported file format '{suffix}'. Please upload GeoTIFF (.tif) or satellite imagery (.png/.jpg).")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    upload_id = f"upl_{int(datetime.utcnow().timestamp())}_{os.path.basename(tmp_path)}"

    if suffix in [".tif", ".tiff", ".geotiff"]:
        metadata = parse_geotiff(tmp_path)
    else:
        img = Image.open(tmp_path).convert("RGB")
        arr = np.array(img)
        preview_b64 = generate_preview_base64(arr)
        metadata = {
            "filename": filename,
            "file_size_bytes": len(contents),
            "crs": "EPSG:4326 (Assumed)",
            "dimensions": {"width": img.width, "height": img.height},
            "resolution_approx": {"x": 10.0, "y": 10.0},
            "modality": "Optical (Standard RGB)",
            "satellite_type": "Standard Satellite Scene",
            "preview_url": preview_b64,
            "affine_transform": [1.0, 0.0, 0.0, 0.0, -1.0, 0.0],
            "wgs84_bounds": {"min_lat": 12.0, "min_lon": 77.0, "max_lat": 13.0, "max_lon": 78.0},
            "center": {"lat": 12.5, "lon": 77.5},
            "band_count": 3
        }

    UPLOAD_STORAGE[upload_id] = {
        "metadata": metadata,
        "temp_path": tmp_path
    }

    return {
        "upload_id": upload_id,
        "metadata": metadata
    }

def get_upload(upload_id: str) -> Optional[Dict[str, Any]]:
    return UPLOAD_STORAGE.get(upload_id)
