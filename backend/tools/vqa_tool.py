"""
Tool 1: Single-Image RS-VQA Tool.
Answers complex remote-sensing domain questions on single optical/multispectral scenes.
Returns grounded answers, visual evidence crops, and auditable telemetry.
"""

import time
from typing import Dict, Any, Optional
import numpy as np
from models.geochat_wrapper import GeoChatVLM
from geospatial.raster_parser import generate_preview_base64

class SingleImageVQATool:
    name = "SingleImageVQATool"
    description = "Executes Visual Question Answering on single optical/multispectral satellite scenes."
    tool_category = "ai_specialist_model"

    def __init__(self):
        self.vlm = GeoChatVLM(model_id="geochat_7b")

    def run(
        self,
        rgb_array: np.ndarray,
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        start_t = time.perf_counter()
        result = self.vlm.answer_vqa(rgb_array, query, metadata)
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

        # Generate real visual evidence preview of the actual crop
        preview_url = generate_preview_base64(rgb_array[:, :, :3])

        return {
            "tool_name": self.name,
            "query": query,
            "answer": result["answer"],
            "category": result["category"],
            "confidence_score": result["confidence"],
            "spectral_diagnostics": result["spectral_diagnostics"],
            "prompt_sent_to_model": result.get("prompt_sent_to_model"),
            "low_relevance_warning": result.get("low_relevance_warning", False),
            "confidence_penalties": result.get("confidence_penalties", []),
            "preview_url": preview_url,
            "internal_latency_ms": elapsed_ms
        }
