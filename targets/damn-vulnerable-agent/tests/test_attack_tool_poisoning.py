"""
Test determinista del vector attacks/01-tool-poisoning.

FakeLLM no "decide" nada (es un guion fijo), así que esto NO prueba que un
modelo real caiga en la inyección — eso lo demuestra
attacks/01-tool-poisoning/run_attack.py contra Ollama de verdad. Lo que SÍ
es determinista y vale la pena probar en CI es que el *mecanismo* de
mitigación (sanitize_tool_descriptions) realmente neutraliza la descripción
envenenada antes de que llegue al LLM, con o sin tools añadidas en caliente.
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "attacks", "01-tool-poisoning")
)

from poisoned_tool import POISONED_TOOL  # noqa: E402

from app import agent, config  # noqa: E402


def _descriptions_seen_by_llm(fake, name):
    last_call = fake.calls[-1]
    for tool in last_call["registry"]:
        if tool["name"] == name:
            return tool["description"]
    raise AssertionError(f"tool {name} no estaba en el registro enviado al LLM")


def test_poisoned_description_reaches_model_when_sanitizer_disabled(fake_llm, isolated_db):
    config.ENABLE_TOOL_SANITIZER = False
    fake = fake_llm([{"role": "assistant", "content": "la hora es x", "tool_calls": []}])

    agent.run_turn("attack-1", "¿qué hora es?", extra_tools=[POISONED_TOOL])

    description = _descriptions_seen_by_llm(fake, "get_server_time")
    assert "IMPORTANT SYSTEM NOTE" in description


def test_poisoned_description_is_redacted_when_sanitizer_enabled(fake_llm, isolated_db):
    config.ENABLE_TOOL_SANITIZER = True
    try:
        fake = fake_llm([{"role": "assistant", "content": "la hora es x", "tool_calls": []}])

        agent.run_turn("attack-2", "¿qué hora es?", extra_tools=[POISONED_TOOL])

        description = _descriptions_seen_by_llm(fake, "get_server_time")
        assert "IMPORTANT SYSTEM NOTE" not in description
        assert "bloqueada" in description
    finally:
        config.ENABLE_TOOL_SANITIZER = False
