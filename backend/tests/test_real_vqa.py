import pytest

from models.model_manager import ModelManager, ModelUnavailableError


def test_vqa_runtime_never_substitutes_a_diagnostic_encoder():
    runtime = ModelManager.instance().integrity()
    assert runtime["model_id"] == "MBZUAI/geochat-7B"
    assert "tiny" not in str(runtime).lower()


def test_unconfigured_real_model_reports_unavailability_honestly():
    manager = ModelManager.instance()
    if manager.integrity()["checkpoint_exists"]:
        pytest.skip("A checkpoint is configured; use the live inference test suite.")
    with pytest.raises(ModelUnavailableError):
        manager.load()
