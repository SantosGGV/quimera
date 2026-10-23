# damn-vulnerable-agent

Un agente LLM **deliberadamente inseguro**, al estilo DVWA/WebGoat pero para
agentes de IA. Es un blanco de laboratorio para practicar cómo **defender**
sistemas agénticos: cada debilidad que trae de fábrica está documentada en
[`attacks/`](attacks/) junto con su mitigación.

> ⚠️ **Esto es un blanco vulnerable a propósito.** Tiene herramientas que
> leen cualquier archivo, ejecutan cualquier comando de shell y corren SQL
> arbitrario, sin pedir confirmación. Solo debe correr en una VM aislada,
> sin red externa, con todo atado a `127.0.0.1`. Nunca lo expongas.

## Qué es

Un bucle de tool-calling escrito a mano (sin LangChain ni frameworks de
agentes) sobre FastAPI, con memoria en SQLite y Ollama como LLM local por
defecto. La idea es que la vulnerabilidad sea visible leyendo ~30 líneas de
`app/agent.py`, no escondida detrás de abstracciones.

- `POST /chat` — conversación con el agente (bucle de tool-calling incluido).
- Backend de LLM intercambiable: Ollama (local, por defecto) u
  OpenAI/compatible (`LLM_BACKEND=openai`).
- 3 herramientas sobre-privilegiadas: `read_file`, `run_command`,
  `query_sql` (ver `app/tools.py` — sin ninguna guarda, a propósito).
- Memoria de conversación en SQLite sin sanitizar (para estudiar
  contaminación de memoria más adelante).

## Cómo levantarlo

```bash
cd ~/lab-ia/damn-vulnerable-agent
cp .env.example .env   # opcional, los defaults ya usan Ollama local
ollama pull llama3.2:3b   # en el HOST, contra el Ollama nativo (solo la primera vez)
docker compose up -d --build
```

> Este proyecto reutiliza el Ollama nativo de la VM (el que instala
> `~/lab-ia/provision.sh`, en `127.0.0.1:11434`) en vez de levantar uno
> propio en Docker: así no se duplica el servicio ni los modelos
> descargados. El contenedor `app` lo alcanza vía `host.docker.internal`
> (ver `docker-compose.yml`).

Verificar:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat \
  -H 'content-type: application/json' \
  -d '{"session_id":"demo","message":"hola, ¿qué puedes hacer?"}'
```

Todo queda atado a `127.0.0.1` (ver `docker-compose.yml`): ni la app ni
Ollama son alcanzables desde fuera de la VM.

## Tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Los tests usan un LLM falso y determinista (`tests/conftest.py`): no
dependen de que Ollama esté corriendo ni de la respuesta real del modelo.

## Ataques documentados

Ver [`attacks/`](attacks/). El primero, [`01-tool-poisoning`](attacks/01-tool-poisoning/),
muestra cómo una herramienta con una `description` envenenada puede desviar
al agente hacia acciones que el usuario nunca pidió, mapeado a OWASP LLM01
(Prompt Injection) y al Top 10 de Agentic AI (Tool Misuse), con su
mitigación de ejemplo y los límites de esa mitigación.

## Estructura

```
app/            # código del agente (FastAPI, bucle de tool-calling, tools, memoria)
workspace/      # ficheros señuelo para las demos de exfiltración
data/           # memory.db (sqlite, gitignored)
attacks/        # vectores de ataque documentados + reproducción
tests/          # pytest determinista con LLM falso
```
