"""Runtime-owned loader for an actual multimodal checkpoint.

This module deliberately has no heuristic or lightweight-model substitution.
When a configured GeoChat-compatible checkpoint cannot be loaded, callers receive
an explicit ``ModelUnavailableError`` and must label any classical analysis as
classical remote-sensing verification.
"""

from __future__ import annotations

import hashlib
import os
import platform
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image


class ModelUnavailableError(RuntimeError):
    """Raised when no verified multimodal checkpoint is available to run."""


@dataclass(frozen=True)
class RuntimeConfig:
    model_id: str
    checkpoint: str
    device: str
    dtype: str
    load_in_4bit: bool
    load_in_8bit: bool
    max_new_tokens: int
    temperature: float
    adapter: str


class ModelManager:
    """Lazy singleton loader with explicit runtime state and inference locking."""

    _instance: Optional["ModelManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self.config = RuntimeConfig(
            model_id=os.getenv("SATQUERY_VLM_MODEL_ID", "MBZUAI/geochat-7B"),
            checkpoint=os.getenv("SATQUERY_VLM_CHECKPOINT", ""),
            device=os.getenv("SATQUERY_VLM_DEVICE", "auto"),
            dtype=os.getenv("SATQUERY_VLM_DTYPE", "auto"),
            load_in_4bit=os.getenv("SATQUERY_VLM_LOAD_IN_4BIT", "false").lower() == "true",
            load_in_8bit=os.getenv("SATQUERY_VLM_LOAD_IN_8BIT", "false").lower() == "true",
            max_new_tokens=int(os.getenv("SATQUERY_VLM_MAX_NEW_TOKENS", "256")),
            temperature=float(os.getenv("SATQUERY_VLM_TEMPERATURE", "0.2")),
            adapter=os.getenv("SATQUERY_VLM_ADAPTER", ""),
        )
        self._model: Any = None
        self._processor: Any = None
        self._load_error: Optional[str] = None
        self._load_time_ms: Optional[float] = None
        self._adapter_state: Dict[str, Any] = self._inspect_adapter()
        self._inference_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "ModelManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _resolve_device(self) -> str:
        try:
            import torch
            if self.config.device != "auto":
                return self.config.device
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def _inspect_adapter(self) -> Dict[str, Any]:
        path = Path(self.config.adapter) if self.config.adapter else None
        config_path = path / "adapter_config.json" if path else None
        weights = None
        if path:
            for name in ("adapter_model.safetensors", "adapter_model.bin"):
                candidate = path / name
                if candidate.exists():
                    weights = candidate
                    break
        return {
            "configured": bool(path),
            "path": str(path) if path else None,
            "config_exists": bool(config_path and config_path.exists()),
            "weights_exists": bool(weights),
            "weights_path": str(weights) if weights else None,
            "loaded": False,
            "compatible": False,
            "sha256": self._sha256(weights) if weights else None,
        }

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _checkpoint_path(self) -> Optional[Path]:
        if not self.config.checkpoint:
            return None
        path = Path(self.config.checkpoint).expanduser()
        return path if path.exists() else None

    def _checkpoint_ready(self) -> bool:
        path = self._checkpoint_path()
        return bool(path and (path / "config.json").exists())

    def load(self) -> None:
        if self._model is not None:
            return
        if self._load_error is not None:
            raise ModelUnavailableError(self._load_error)
        if not self._checkpoint_ready():
            self._load_error = (
                "No local GeoChat-compatible checkpoint is configured. Set "
                "SATQUERY_VLM_CHECKPOINT to a verified local checkpoint before using VQA."
            )
            raise ModelUnavailableError(self._load_error)

        started = time.perf_counter()
        try:
            import torch
            from transformers import AutoModelForVision2Seq, AutoProcessor

            device = self._resolve_device()
            kwargs: Dict[str, Any] = {"trust_remote_code": True, "low_cpu_mem_usage": True}
            if device == "cuda":
                kwargs["device_map"] = "auto"
                if self.config.load_in_4bit:
                    kwargs["load_in_4bit"] = True
                elif self.config.load_in_8bit:
                    kwargs["load_in_8bit"] = True
                elif self.config.dtype == "bfloat16":
                    kwargs["torch_dtype"] = torch.bfloat16
                else:
                    kwargs["torch_dtype"] = torch.float16

            checkpoint = str(self._checkpoint_path())
            self._processor = AutoProcessor.from_pretrained(checkpoint, trust_remote_code=True)
            self._model = AutoModelForVision2Seq.from_pretrained(checkpoint, **kwargs)
            if device == "cpu":
                self._model.to("cpu")
            self._model.eval()

            if self._adapter_state["configured"]:
                if not (self._adapter_state["config_exists"] and self._adapter_state["weights_exists"]):
                    raise ModelUnavailableError("Configured adapter is missing config or weights.")
                from peft import PeftModel
                self._model = PeftModel.from_pretrained(self._model, self.config.adapter)
                self._adapter_state.update({"loaded": True, "compatible": True})
        except Exception as exc:
            self._model = None
            self._processor = None
            self._load_error = f"GeoChat-compatible checkpoint failed to load: {exc}"
            raise ModelUnavailableError(self._load_error) from exc
        finally:
            self._load_time_ms = round((time.perf_counter() - started) * 1000, 2)

    def generate(self, image: Image.Image, query: str) -> Dict[str, Any]:
        self.load()
        started = time.perf_counter()
        try:
            import torch
            with self._inference_lock, torch.inference_mode():
                inputs = self._processor(images=image, text=query, return_tensors="pt")
                device = self._resolve_device()
                inputs = {name: value.to(device) if hasattr(value, "to") else value for name, value in inputs.items()}
                generated = self._model.generate(
                    **inputs,
                    max_new_tokens=self.config.max_new_tokens,
                    do_sample=self.config.temperature > 0,
                    temperature=self.config.temperature if self.config.temperature > 0 else None,
                )
                answer = self._processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
        except Exception as exc:
            raise ModelUnavailableError(f"Model generation failed: {exc}") from exc
        if not answer:
            raise ModelUnavailableError("Model generation returned an empty answer.")
        return {
            "model_generated_answer": answer,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "model_input_shape": list(np.asarray(image).shape),
        }

    def unload(self) -> None:
        self._model = None
        self._processor = None
        self._load_error = None

    def integrity(self) -> Dict[str, Any]:
        checkpoint = self._checkpoint_path()
        device = self._resolve_device()
        status = "PASS" if self._model is not None else ("FAIL" if self._checkpoint_ready() and self._load_error else "NOT_AVAILABLE")
        return {
            "status": status,
            "model_id": self.config.model_id,
            "checkpoint_path": str(checkpoint) if checkpoint else None,
            "checkpoint_exists": bool(checkpoint),
            "checkpoint_loaded": self._model is not None,
            "device": device,
            "dtype": self.config.dtype,
            "quantization": "4bit" if self.config.load_in_4bit else ("8bit" if self.config.load_in_8bit else "none"),
            "inference_supported": self._model is not None,
            "load_time_ms": self._load_time_ms,
            "last_error": self._load_error,
            "adapter": self._adapter_state,
            "hardware": {"platform": platform.platform(), "cpu_count": os.cpu_count()},
        }
