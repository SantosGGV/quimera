import json
import sqlite3
import time
from contextlib import contextmanager

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    tool_name TEXT,
    tool_arguments TEXT,
    tool_call_id TEXT,
    created_at REAL NOT NULL
);
"""


@contextmanager
def _connect():
    conn = sqlite3.connect(config.DB_PATH)
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def append_message(
    session_id: str,
    role: str,
    content: str | None = None,
    tool_name: str | None = None,
    tool_arguments: dict | None = None,
    tool_call_id: str | None = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages "
            "(session_id, role, content, tool_name, tool_arguments, tool_call_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                role,
                content,
                tool_name,
                json.dumps(tool_arguments) if tool_arguments is not None else None,
                tool_call_id,
                time.time(),
            ),
        )


def load_history(session_id: str) -> list[dict]:
    """Devuelve la historia en el formato de mensajes que espera el LLM."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content, tool_name, tool_arguments, tool_call_id "
            "FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()

    messages = []
    for role, content, tool_name, tool_arguments, tool_call_id in rows:
        msg = {"role": role, "content": content}
        if tool_name:
            msg["tool_name"] = tool_name
        if tool_arguments:
            msg["tool_arguments"] = json.loads(tool_arguments)
        if tool_call_id:
            msg["tool_call_id"] = tool_call_id
        messages.append(msg)
    return messages
