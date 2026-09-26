"""Verify a configured real VLM without downloading model weights at startup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from geospatial.model_preprocessor import prepare_model_image
from models.model_manager import ModelManager, ModelUnavailableError


def main() -> int:
    manager = ModelManager.instance()
    print("RUNTIME:", manager.integrity())
    sample = ROOT / "backend" / "data" / "samples" / "cartosat_optical_bengaluru.tif"
    if not sample.exists():
        print("REAL INFERENCE: FAIL - sample raster is missing")
        return 1
    try:
        import rasterio
        with rasterio.open(sample) as dataset:
            raw = dataset.read()
        image, evidence = prepare_model_image(raw[:3].transpose(1, 2, 0))
        result = manager.generate(image, "Is there a water body in this image?")
    except ModelUnavailableError as exc:
        print(f"REAL MODEL LOAD: FAIL - {exc}")
        print("REAL INFERENCE: FAIL - no verified checkpoint was executed")
        return 2
    print("REAL MODEL LOAD: PASS")
    print("REAL INFERENCE: PASS")
    print("INPUT SHA256:", evidence["input_sha256"])
    print("ANSWER:", result["model_generated_answer"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
