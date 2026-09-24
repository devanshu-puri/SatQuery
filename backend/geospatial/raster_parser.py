"""
Geospatial Raster Parser & Ingestion Engine for SatQuery AI.
Handles GeoTIFF/TIFF validation, CRS & affine transform extraction,
multispectral/SAR band profiling, and web-ready visualization generation.
"""

import os
import io
import base64
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
import pyproj
from PIL import Image

def get_crs_string(crs) -> str:
    """Returns clean EPSG code or CRS representation."""
    if not crs:
        return "EPSG:4326 (Assumed)"
    try:
        epsg = crs.to_epsg()
        if epsg:
            return f"EPSG:{epsg}"
        return crs.to_string()
    except Exception:
        return str(crs)

def infer_modality_and_bands(band_count: int, dtype: str, descriptions: Tuple[str, ...]) -> Dict[str, Any]:
    """Infers sensor modality and band layout based on band count and metadata."""
    if band_count == 1:
        return {
            "modality": "Single-Band Raster",
            "type": "SAR / Grayscale / Mask / DEM",
            "band_names": ["Band 1 (Intensity/Backscatter)"]
        }
    elif band_count == 2:
        return {
            "modality": "Dual-Pol SAR",
            "type": "Sentinel-1 / RISAT SAR (VV/VH)",
            "band_names": ["VV (Co-pol)", "VH (Cross-pol)"]
        }
    elif band_count == 3:
        return {
            "modality": "Optical (True Color RGB)",
            "type": "Cartosat / Sentinel-2 / Landsat (RGB)",
            "band_names": ["Red (B4/R)", "Green (B3/G)", "Blue (B2/B)"]
        }
    elif band_count == 4:
        return {
            "modality": "Optical (VNIR)",
            "type": "Optical RGB + NIR",
            "band_names": ["Red", "Green", "Blue", "Near-Infrared (NIR)"]
        }
    elif band_count in (12, 13):
        return {
            "modality": "Multispectral (Full)",
            "type": "Sentinel-2 MSI Harmonized L2A",
            "band_names": [
                "B1 (Coastal)", "B2 (Blue)", "B3 (Green)", "B4 (Red)",
                "B5 (VRE1)", "B6 (VRE2)", "B7 (VRE3)", "B8 (NIR)",
                "B8A (Narrow NIR)", "B9 (Water Vapor)", "B11 (SWIR1)", "B12 (SWIR2)"
            ]
        }
    else:
        return {
            "modality": "Multispectral",
            "type": f"{band_count}-Band Custom Satellite Raster",
            "band_names": [f"Band {i+1}" for i in range(band_count)]
        }

def normalize_to_8bit_rgb(raster_data: np.ndarray) -> np.ndarray:
    """
    Normalizes multi-band raster arrays into 8-bit (0-255) RGB array for VLM processing and UI display.
    Handles 1-band (SAR/grayscale), 2-band (SAR dual-pol), 3-band (RGB), 4+ bands (extracts RGB/NIR).
    """
    bands, height, width = raster_data.shape
    
    if bands == 1:
        # Grayscale / Single SAR band
        b1 = raster_data[0].astype(np.float32)
        valid = np.isfinite(b1) & (b1 > 0)
        p2, p98 = (np.percentile(b1[valid], (2, 98)) if np.any(valid) else (0, 1))
        norm = np.clip((b1 - p2) / (p98 - p2 + 1e-6) * 255.0, 0, 255).astype(np.uint8)
        rgb = np.stack([norm, norm, norm], axis=-1)
        return rgb

    elif bands == 2:
        # Dual-Pol SAR (VV, VH) -> False color (VV, VH, VV/VH ratio)
        vv = raster_data[0].astype(np.float32)
        vh = raster_data[1].astype(np.float32)
        ratio = np.where(vh > 0, vv / (vh + 1e-6), 0)

        def stretch(arr):
            v = np.isfinite(arr) & (arr > 0)
            p2, p98 = (np.percentile(arr[v], (2, 98)) if np.any(v) else (0, 1))
            return np.clip((arr - p2) / (p98 - p2 + 1e-6) * 255.0, 0, 255).astype(np.uint8)

        rgb = np.stack([stretch(vv), stretch(vh), stretch(ratio)], axis=-1)
        return rgb

    elif bands in (3, 4):
        # RGB or RGB + NIR
        r, g, b = raster_data[0].astype(np.float32), raster_data[1].astype(np.float32), raster_data[2].astype(np.float32)
        def stretch(arr):
            v = np.isfinite(arr) & (arr > 0)
            p2, p98 = (np.percentile(arr[v], (2, 98)) if np.any(v) else (0, 255))
            return np.clip((arr - p2) / (p98 - p2 + 1e-6) * 255.0, 0, 255).astype(np.uint8)
        rgb = np.stack([stretch(r), stretch(g), stretch(b)], axis=-1)
        return rgb

    else:
        # Full Sentinel-2 (B4=Red is index 3, B3=Green is index 2, B2=Blue is index 1)
        r = raster_data[min(3, bands - 1)].astype(np.float32)
        g = raster_data[min(2, bands - 1)].astype(np.float32)
        b = raster_data[min(1, bands - 1)].astype(np.float32)
        def stretch(arr):
            v = np.isfinite(arr) & (arr > 0)
            p2, p98 = (np.percentile(arr[v], (2, 98)) if np.any(v) else (0, 3000))
            return np.clip((arr - p2) / (p98 - p2 + 1e-6) * 255.0, 0, 255).astype(np.uint8)
        rgb = np.stack([stretch(r), stretch(g), stretch(b)], axis=-1)
        return rgb

def generate_preview_base64(rgb_array: np.ndarray, max_dim: int = 512) -> str:
    """Encodes an RGB array into a base64 PNG data URL."""
    img = Image.fromarray(rgb_array)
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"

def parse_geotiff(file_path: str) -> Dict[str, Any]:
    """
    Parses and validates a GeoTIFF raster file with full spatial and spectral profiling.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with rasterio.open(file_path) as src:
        crs_str = get_crs_string(src.crs)
        bounds = src.bounds
        transform = list(src.transform)
        width, height = src.width, src.height
        band_count = src.count
        dtype = str(src.dtypes[0])
        descriptions = src.descriptions or ()

        # Reproject bounds to EPSG:4326 (WGS84 Lat/Lon) for Web GIS/Leaflet mapping
        if src.crs and src.crs != "EPSG:4326":
            try:
                min_lon, min_lat, max_lon, max_lat = transform_bounds(src.crs, "EPSG:4326", *bounds)
            except Exception:
                min_lon, min_lat, max_lon, max_lat = bounds.left, bounds.bottom, bounds.right, bounds.top
        else:
            min_lon, min_lat, max_lon, max_lat = bounds.left, bounds.bottom, bounds.right, bounds.top

        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0

        # Read array data for thumbnail and band profiling
        # Read at moderate resolution for performance if large
        decimate_factor = max(1, max(width, height) // 1024)
        out_shape = (band_count, height // decimate_factor, width // decimate_factor)
        
        raster_data = src.read(
            out_shape=out_shape,
            resampling=rasterio.enums.Resampling.bilinear
        )

        modality_info = infer_modality_and_bands(band_count, dtype, descriptions)
        rgb_preview = normalize_to_8bit_rgb(raster_data)
        preview_base64 = generate_preview_base64(rgb_preview)

        # Approximate spatial resolution in meters
        res_x, res_y = abs(src.transform.a), abs(src.transform.e)

        return {
            "filename": os.path.basename(file_path),
            "file_size_bytes": os.path.getsize(file_path),
            "crs": crs_str,
            "dimensions": {"width": width, "height": height},
            "resolution_approx": {"x": round(res_x, 4), "y": round(res_y, 4)},
            "native_bounds": {
                "left": bounds.left,
                "bottom": bounds.bottom,
                "right": bounds.right,
                "top": bounds.top
            },
            "wgs84_bounds": {
                "min_lat": round(min_lat, 6),
                "min_lon": round(min_lon, 6),
                "max_lat": round(max_lat, 6),
                "max_lon": round(max_lon, 6)
            },
            "center": {"lat": round(center_lat, 6), "lon": round(center_lon, 6)},
            "affine_transform": transform,
            "band_count": band_count,
            "data_type": dtype,
            "modality": modality_info["modality"],
            "satellite_type": modality_info["type"],
            "band_names": modality_info["band_names"],
            "preview_url": preview_base64,
            "nodata_value": src.nodata
        }
