import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Cada test usa su propia base SQLite temporal, nunca /data/memory.db."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "memory.db")
        from app import config

        monkeypatch.setattr(config, "DB_PATH", db_path)
        yield db_path


class FakeLLM:
    """Sustituye app.llm.chat con una secuencia de respuestas predefinidas,
    para que los tests sean deterministas y no dependan de Ollama."""

    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.calls = []

    def __call__(self, messages, registry):
        self.calls.append({"messages": messages, "registry": registry})
        return self._responses.pop(0)


@pytest.fixture
def fake_llm(monkeypatch):
    def _install(responses: list[dict]) -> FakeLLM:
        fake = FakeLLM(responses)
        from app import llm

        monkeypatch.setattr(llm, "chat", fake)
        return fake

    return _install
