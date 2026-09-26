import asyncio

import numpy as np

from agent.multilingual import interpret_query
from agent.router import AgentController


def test_interpreter_detects_indic_language_target_and_intent():
    parsed = interpret_query("इस क्षेत्र में जल निकाय कहाँ दिखाएं?")
    assert parsed["language"] == "hi"
    assert parsed["target_concept"] == "water"
    assert parsed["intent"] == "region_grounding"


def test_interpreter_routes_telugu_change_request():
    parsed = interpret_query("ఈ రెండు తేదీల మధ్య మార్పు ఏమిటి?")
    assert parsed["language"] == "te"
    assert parsed["intent"] == "bitemporal_change"


def test_agent_records_language_and_uses_real_input():
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    result = asyncio.run(AgentController().route_and_execute_stream(
        "ಈ ಚಿತ್ರದಲ್ಲಿ ನೀರು ಇದೆಯೇ?",
        image_primary=image,
        metadata_primary={"modality": "Optical", "dimensions": {"width": 32, "height": 32}},
    ))
    assert result["language"] == "kn"
    assert result["execution_trace"]["target_concept"] == "water"
    assert "human_summary" in result
