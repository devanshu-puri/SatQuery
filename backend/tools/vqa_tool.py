"""
Tool 1: Single-Image RS-VQA Tool.
Answers complex remote-sensing domain questions on single optical/multispectral scenes.
Returns grounded answers, visual evidence crops, and auditable telemetry.
"""

import time
from typing import Dict, Any, Optional
import numpy as np
from models.model_manager import ModelManager
from geospatial.model_preprocessor import prepare_model_image
from geospatial.raster_parser import generate_preview_base64

class SingleImageVQATool:
    name = "SingleImageVQATool"
    description = "Executes Visual Question Answering on single optical/multispectral satellite scenes."
    tool_category = "ai_specialist_model"

    def __init__(self):
        self.model_manager = ModelManager.instance()

    def run(
        self,
        rgb_array: np.ndarray,
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        start_t = time.perf_counter()
        image, evidence = prepare_model_image(rgb_array, metadata)
        result = self.model_manager.generate(image, query)
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

        # Generate real visual evidence preview of the actual crop
        preview_url = generate_preview_base64(rgb_array[:, :, :3])

        return {
            "tool_name": self.name,
            "query": query,
            "answer": result["model_generated_answer"],
            "model_generated_answer": result["model_generated_answer"],
            "answer_source": "model_generated",
            "category": "Real multimodal model inference",
            "confidence_score": None,
            "spectral_diagnostics": {},
            "prompt_sent_to_model": query,
            "low_relevance_warning": False,
            "confidence_penalties": [],
            "evidence": evidence,
            "model_input_shape": result["model_input_shape"],
            "preview_url": preview_url,
            "internal_latency_ms": elapsed_ms
        }
