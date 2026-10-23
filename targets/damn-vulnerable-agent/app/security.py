"""
Mitigación ilustrativa para attacks/01-tool-poisoning.

Un filtro estático de patrones no es una defensa robusta (un atacante
suficientemente creativo lo rodea reformulando la frase). Lo real para
producción es: registro de tools firmado/con allowlist, principio de mínimo
privilegio en cada tool, y confirmación humana para llamadas sensibles. Este
filtro solo sirve para que la demo de attacks/01-tool-poisoning tenga un
"antes" y un "después" tangibles.
"""

import re

# Frases que delatan una instrucción imperativa dirigida al modelo, en vez
# de una descripción neutra de lo que hace la herramienta.
_SUSPICIOUS_PATTERNS = [
    r"antes de responder",
    r"antes de (?:llamar|usar|ejecutar)",
    r"siempre (?:llama|ejecuta|usa)",
    r"debes (?:llamar|ejecutar|usar)",
    r"sin (?:decirle|mencionarlo|avisar)",
    r"nota (?:del sistema|importante)",
    r"ignora (?:las )?instrucciones",
    r"system note",
    r"important:",
]

_REDACTED = "[descripción bloqueada por sanitize_tool_descriptions: patrón sospechoso detectado]"


def sanitize_tool_descriptions(registry: list[dict]) -> list[dict]:
    """Devuelve una copia del registro con descripciones sospechosas neutralizadas."""
    sanitized = []
    for tool in registry:
        description = tool.get("description", "")
        if any(re.search(p, description, re.IGNORECASE) for p in _SUSPICIOUS_PATTERNS):
            tool = {**tool, "description": _REDACTED}
        sanitized.append(tool)
    return sanitized
