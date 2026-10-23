from app import agent


def test_run_turn_executes_tool_call_and_returns_final_reply(fake_llm, isolated_db):
    fake_llm(
        [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call-1", "name": "run_command", "arguments": {"command": "echo hi"}}
                ],
            },
            {"role": "assistant", "content": "la salida fue 'hi'", "tool_calls": []},
        ]
    )

    result = agent.run_turn("s1", "ejecuta echo hi")

    assert result["reply"] == "la salida fue 'hi'"
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["name"] == "run_command"
    assert "hi" in result["tool_calls"][0]["result"]


def test_run_turn_without_tool_calls_returns_direct_reply(fake_llm, isolated_db):
    fake_llm([{"role": "assistant", "content": "hola!", "tool_calls": []}])

    result = agent.run_turn("s2", "hola")

    assert result["reply"] == "hola!"
    assert result["tool_calls"] == []


def test_run_turn_persists_history_across_calls(fake_llm, isolated_db):
    fake_llm([{"role": "assistant", "content": "ok", "tool_calls": []}])
    agent.run_turn("s3", "primer mensaje")

    from app import memory

    history = memory.load_history("s3")
    roles = [m["role"] for m in history]
    assert roles == ["system", "user", "assistant"]
