from fastapi import FastAPI
from pydantic import BaseModel

from . import agent

app = FastAPI(
    title="damn-vulnerable-agent",
    description=(
        "Agente LLM deliberadamente inseguro para practicar defensa de "
        "agentes de IA. NO expongas esto fuera de 127.0.0.1."
    ),
)


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str | None
    tool_calls: list[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = agent.run_turn(req.session_id, req.message)
    return ChatResponse(session_id=req.session_id, reply=result["reply"], tool_calls=result["tool_calls"])
