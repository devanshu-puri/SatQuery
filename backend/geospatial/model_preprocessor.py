"""Creates an auditable RGB evidence artifact from the exact raster/AOI array."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional, Tuple

import numpy as np
from PIL import Image


def prepare_model_image(rgb_array: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> Tuple[Image.Image, Dict[str, Any]]:
    """Normalize a current cropped raster array without inventing display bands."""
    array = np.asarray(rgb_array)
    if array.ndim == 2:
        array = np.repeat(array[:, :, None], 3, axis=2)
    if array.ndim != 3:
        raise ValueError(f"Expected HWC raster array, got shape {array.shape}")
    if array.shape[2] == 1:
        array = np.repeat(array, 3, axis=2)
    rgb = array[:, :, :3]
    if rgb.dtype != np.uint8:
        lower, upper = np.nanpercentile(rgb, (2, 98))
        scale = max(float(upper - lower), 1e-6)
        rgb = np.clip((rgb.astype(np.float32) - lower) * 255.0 / scale, 0, 255).astype(np.uint8)
    contiguous = np.ascontiguousarray(rgb)
    image_hash = hashlib.sha256(contiguous.tobytes()).hexdigest()
    image = Image.fromarray(contiguous, mode="RGB")
    dimensions = {"width": int(contiguous.shape[1]), "height": int(contiguous.shape[0]), "bands": int(array.shape[2])}
    evidence = {
        "input_sha256": image_hash,
        "preprocessed_image_sha256": image_hash,
        "raster_dimensions": dimensions,
        "crs": (metadata or {}).get("crs"),
        "aoi": (metadata or {}).get("aoi_geometry"),
        "preprocessing_steps": ["current AOI crop", "first three display bands", "robust 2nd-98th percentile normalization"],
    }
    return image, evidence
