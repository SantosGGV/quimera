"""
Capa delgada sobre dos backends de chat con tool-calling: Ollama (nativo) y
OpenAI/compatible. Normaliza mensajes y tool_calls a un formato interno
común para que app/agent.py no tenga que conocer el formato de cada API.

Formato interno de mensajes:
  {"role": "system"|"user", "content": str}
  {"role": "assistant", "content": str|None, "tool_calls": [{"id","name","arguments"}]}
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}

to_tools_schema() convierte el REGISTRY de app/tools.py (ya pasado o no por
el sanitizer de app/security.py) al formato "tools" tipo OpenAI function
calling que ambos backends entienden.
"""

import json
import uuid

import httpx

from . import config


def to_tools_schema(registry: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }
        for tool in registry
    ]


def chat(messages: list[dict], registry: list[dict]) -> dict:
    tools = to_tools_schema(registry)
    if config.LLM_BACKEND == "openai":
        return _openai_chat(messages, tools)
    return _ollama_chat(messages, tools)


def _ollama_chat(messages: list[dict], tools: list[dict]) -> dict:
    wire_messages = []
    for m in messages:
        if m["role"] == "assistant" and m.get("tool_calls"):
            wire_messages.append(
                {
                    "role": "assistant",
                    "content": m.get("content") or "",
                    "tool_calls": [
                        {"function": {"name": tc["name"], "arguments": tc["arguments"]}}
                        for tc in m["tool_calls"]
                    ],
                }
            )
        elif m["role"] == "tool":
            wire_messages.append({"role": "tool", "content": m["content"]})
        else:
            wire_messages.append({"role": m["role"], "content": m.get("content") or ""})

    resp = httpx.post(
        f"{config.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": wire_messages,
            "tools": tools,
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    message = resp.json()["message"]

    tool_calls = []
    for tc in message.get("tool_calls") or []:
        fn = tc["function"]
        arguments = fn["arguments"]
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        tool_calls.append({"id": str(uuid.uuid4()), "name": fn["name"], "arguments": arguments})

    return {
        "role": "assistant",
        "content": message.get("content") or None,
        "tool_calls": tool_calls,
    }


def _openai_chat(messages: list[dict], tools: list[dict]) -> dict:
    wire_messages = []
    for m in messages:
        if m["role"] == "assistant" and m.get("tool_calls"):
            wire_messages.append(
                {
                    "role": "assistant",
                    "content": m.get("content"),
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["arguments"]),
                            },
                        }
                        for tc in m["tool_calls"]
                    ],
                }
            )
        elif m["role"] == "tool":
            wire_messages.append(
                {"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]}
            )
        else:
            wire_messages.append({"role": m["role"], "content": m.get("content") or ""})

    resp = httpx.post(
        f"{config.OPENAI_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
        json={
            "model": config.OPENAI_MODEL,
            "messages": wire_messages,
            "tools": tools,
        },
        timeout=120,
    )
    resp.raise_for_status()
    message = resp.json()["choices"][0]["message"]

    tool_calls = []
    for tc in message.get("tool_calls") or []:
        tool_calls.append(
            {
                "id": tc["id"],
                "name": tc["function"]["name"],
                "arguments": json.loads(tc["function"]["arguments"]),
            }
        )

    return {
        "role": "assistant",
        "content": message.get("content"),
        "tool_calls": tool_calls,
    }
