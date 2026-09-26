import asyncio

import numpy as np

from agent.router import AgentController
from models.geochat_wrapper import GeoChatVLM
from models.registry import ModelRegistry


def test_runtime_registry_is_truthful():
    model = ModelRegistry.get_model_info("geochat_7b")
    assert model is not None
    assert "GeoChat-7B" not in model["name"]
    assert "full external checkpoint unavailable" in model["name"].lower()
    assert model["tool_category"] == "classical_rs"
    assert model["model_category"] == "classical_rs"
    assert model.get("checkpoint_status") in {"missing", "partial", "loaded"}


def test_generate_uses_real_forward_pass_on_actual_tensor():
    vlm = GeoChatVLM(model_id="geochat_7b")
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    result = vlm.generate(image, "Is there water in this scene?")

    assert "prompt_sent_to_model" in result
    assert "model_forward_pass" in result
    assert "predicted_class" in result["model_forward_pass"]
    assert len(result["model_forward_pass"]["logits"]) == 6
    assert "full 7B" not in result["prompt_sent_to_model"].lower()


def test_adapter_runtime_provides_hash_and_manifest_proof():
    model = ModelRegistry.get_model_info("optical_sar_fusion_net")
    assert model is not None
    assert model["adapter_sha256"]
    assert model["training_loss_file"] == "training_loss.png"
    assert model["training_manifest"] is not None

    proof = ModelRegistry.verify_adapter_probe()
    assert proof["probe_passed"] is False
    assert len(proof["adapter_sha256"]) == 64
    assert "not proof" in proof["note"].lower()


def test_registry_commits_to_vqa_plus_grounding_as_mandatory_scope():
    model = ModelRegistry.get_model_info("geochat_7b")
    assert model is not None
    assert "Single-Image Visual Question Answering" in model["official_scope"]
    assert "Text-Guided Region Grounding (GeoJSON Polygons)" in model["official_scope"]
    assert "Dense Remote Sensing Scene Captioning (bonus feature, not counted as mandatory scope)" in model["additional_features"]
    assert "Official mandatory scope" in model["scope_claim"]


def test_execution_trace_explicitly_labels_tool_category():
    model = ModelRegistry.get_model_info("geochat_7b")
    assert model["tool_category"] == "classical_rs"

    image = np.zeros((32, 32, 3), dtype=np.uint8)
    result = asyncio.run(AgentController().route_and_execute_stream(
        "Is there water in this scene?",
        image_primary=image,
        metadata_primary={"modality": "Optical", "dimensions": {"width": 32, "height": 32}}
    ))

    trace = result["execution_trace"]
    assert trace["tool_category"] == "classical_rs"
    assert trace["model_category"] == "classical_rs"
    assert trace["tools_executed"] in (["SingleImageVQATool"], ["ClassicalRSBaseline"])


def test_specialist_failure_returns_partial_classical_fallback():
    controller = AgentController()
    original_run = controller.vqa_tool.run
    controller.vqa_tool.run = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("adapter missing"))

    try:
        result = asyncio.run(controller.route_and_execute_stream(
            "Is there water in this scene?",
            image_primary=np.zeros((32, 32, 3), dtype=np.uint8),
            metadata_primary={"modality": "Optical", "dimensions": {"width": 32, "height": 32}}
        ))
    finally:
        controller.vqa_tool.run = original_run

    assert result["status"] == "PARTIAL"
    assert "Specialist model unavailable" in result["response"]
    assert "Classical RS baseline" in result["response"]
    assert result["tool_category"] == "classical_rs"
    assert result["execution_trace"]["status"] == "PARTIAL"
