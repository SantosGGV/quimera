# attacks/

Cada subcarpeta documenta un vector de ataque reproducible contra
`damn-vulnerable-agent`: cómo reproducirlo, por qué funciona, a qué
categoría del OWASP Top 10 para LLMs / OWASP Top 10 para Agentic AI mapea,
y cuál es su mitigación (y sus límites).

## Índice

| # | Vector | OWASP LLM Top 10 | OWASP Agentic AI Top 10 | Estado |
|---|---|---|---|---|
| [01](01-tool-poisoning/) | Tool poisoning (inyección vía descripción de herramienta) | LLM01: Prompt Injection | Tool Misuse / Agent Goal Manipulation | Implementado |
| 02 | Memoria contaminada (session/memory poisoning vía SQLite) | LLM01 / LLM04: Data Poisoning | Memory Poisoning | Roadmap — la tabla `messages` ya no tiene ninguna sanitización, a propósito |
| 03 | Excessive agency sin confirmación (encadenar read_file → run_command) | LLM06: Excessive Agency | Excessive Agency / Privilege Compromise | Roadmap — las 3 tools de `app/tools.py` ya están listas para esto |

## Convención de cada vector

```
NN-nombre-del-vector/
├── README.md       # qué es, cómo reproducirlo, por qué funciona, mitigación, mapeo OWASP
├── *.py            # payload / tool envenenada / script de ataque
```

El código de ataque siempre se ejecuta contra el agente real (mismo
`app/agent.py`, mismo modelo que usa `docker-compose.yml`), nunca contra un
mock — el objetivo es ver el comportamiento real, no simularlo.
