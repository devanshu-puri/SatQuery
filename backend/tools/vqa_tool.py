"""
Tool 1: Single-Image RS-VQA Tool.
Answers complex remote-sensing domain questions on single optical/multispectral scenes.
"""

from typing import Dict, Any, Optional
import numpy as np
from models.geochat_wrapper import GeoChatVLM

class SingleImageVQATool:
    name = "SingleImageVQATool"
    description = "Executes Visual Question Answering on single optical/multispectral satellite scenes."

    def __init__(self):
        self.vlm = GeoChatVLM(model_id="geochat_7b")

    def run(
        self,
        rgb_array: np.ndarray,
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        result = self.vlm.answer_vqa(rgb_array, query, metadata)
        return {
            "tool_name": self.name,
            "query": query,
            "answer": result["answer"],
            "category": result["category"],
            "confidence_score": result["confidence"],
            "spectral_diagnostics": result["spectral_diagnostics"]
        }
