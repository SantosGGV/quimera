"""
Bucle de tool-calling minimalista. Sin framework, sin confirmación humana,
sin límites de privilegio en las tools (ver app/tools.py): el modelo decide
qué llamar y el agente lo ejecuta. El único límite es MAX_TOOL_ITERATIONS,
una salvaguarda anti-bucle-infinito, no una medida de seguridad.
"""

from . import config, llm, memory, security, tools


def _build_registry(extra_tools: list[dict] | None) -> list[dict]:
    """Registro base + tools dinámicas (ej. de un marketplace de MCP), y
    SOLO ENTONCES se sanitiza, para que la mitigación cubra toda la
    superficie de descripciones que se manda al modelo, no solo las tools
    que vienen de fábrica."""
    registry = tools.get_registry()
    if extra_tools:
        registry = registry + extra_tools
    if config.ENABLE_TOOL_SANITIZER:
        registry = security.sanitize_tool_descriptions(registry)
    return registry


def run_turn(session_id: str, user_message: str, extra_tools: list[dict] | None = None) -> dict:
    registry = _build_registry(extra_tools)

    history = memory.load_history(session_id)
    if not history:
        memory.append_message(session_id, "system", config.SYSTEM_PROMPT)
        history.append({"role": "system", "content": config.SYSTEM_PROMPT})

    memory.append_message(session_id, "user", user_message)
    history.append({"role": "user", "content": user_message})

    trace = []
    for _ in range(config.MAX_TOOL_ITERATIONS):
        response = llm.chat(history, registry)

        if not response["tool_calls"]:
            memory.append_message(session_id, "assistant", response["content"])
            return {"reply": response["content"], "tool_calls": trace}

        memory.append_message(
            session_id,
            "assistant",
            response["content"],
            tool_name=None,
        )
        history.append(response)

        for call in response["tool_calls"]:
            result = tools.dispatch(call["name"], call["arguments"], registry)
            trace.append({"name": call["name"], "arguments": call["arguments"], "result": result})
            memory.append_message(
                session_id,
                "tool",
                content=result,
                tool_name=call["name"],
                tool_arguments=call["arguments"],
                tool_call_id=call["id"],
            )
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": call["name"],
                    "content": result,
                }
            )

    return {
        "reply": "(límite de iteraciones de herramientas alcanzado sin respuesta final)",
        "tool_calls": trace,
    }
