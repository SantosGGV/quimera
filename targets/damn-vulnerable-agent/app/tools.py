"""
Herramientas DELIBERADAMENTE sobre-privilegiadas.

No hay validación de rutas, no hay allowlist de comandos, no hay
parametrización SQL, y no se pide confirmación humana antes de ejecutar
nada. Esto es "excessive agency" (OWASP LLM Top 10 / Agentic AI Top 10) a
propósito: el objetivo del laboratorio es poder observar qué pasa cuando un
agente tiene estas herramientas y algo (un usuario malicioso, una
herramienta envenenada, un documento hostil) consigue dirigir su
comportamiento.

NUNCA uses este código fuera de un contenedor de laboratorio aislado.
"""

import sqlite3
import subprocess

from . import config


def read_file(path: str) -> str:
    """Lee el contenido de cualquier archivo accesible al proceso."""
    with open(path, "r", errors="replace") as f:
        return f.read()


def run_command(command: str) -> str:
    """Ejecuta cualquier comando de shell y devuelve stdout+stderr."""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return f"$ {command}\n[exit {result.returncode}]\n{result.stdout}{result.stderr}"


def query_sql(query: str) -> str:
    """Ejecuta SQL arbitrario (sin parametrizar) contra la base de memoria."""
    conn = sqlite3.connect(config.DB_PATH)
    try:
        cursor = conn.execute(query)
        if cursor.description:
            columns = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
            return str({"columns": columns, "rows": rows})
        conn.commit()
        return f"OK, {cursor.rowcount} filas afectadas"
    finally:
        conn.close()


# Registro de herramientas: nombre, descripción (esto es lo que se manda al
# modelo y lo que ataca "tool poisoning"), schema de parámetros, e
# implementación.
REGISTRY = [
    {
        "name": "read_file",
        "description": "Lee el contenido de un archivo de texto dado su path.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Ruta del archivo a leer"}},
            "required": ["path"],
        },
        "fn": read_file,
    },
    {
        "name": "run_command",
        "description": "Ejecuta un comando de shell en el sistema y devuelve su salida.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Comando de shell a ejecutar"}},
            "required": ["command"],
        },
        "fn": run_command,
    },
    {
        "name": "query_sql",
        "description": "Ejecuta una consulta SQL contra la base de datos de memoria del agente.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Consulta SQL a ejecutar"}},
            "required": ["query"],
        },
        "fn": query_sql,
    },
]


def get_registry() -> list[dict]:
    """Copia de la REGISTRY base. Los scripts de attacks/ le añaden tools envenenadas."""
    return list(REGISTRY)


def dispatch(name: str, arguments: dict, registry: list[dict]) -> str:
    for tool in registry:
        if tool["name"] == name:
            try:
                return tool["fn"](**arguments)
            except Exception as exc:  # el agente vulnerable no oculta errores
                return f"ERROR ejecutando {name}: {exc}"
    return f"ERROR: herramienta '{name}' no encontrada"
