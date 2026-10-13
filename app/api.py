"""FastAPI surface. Response models are the Pydantic contracts, so OpenAPI matches them."""
from fastapi import FastAPI

from app.config import config_hash, load_config
from app.models import Health, IngestIn, IngestOut, TicketIn, TicketResponse
from app.pipeline import Service

app = FastAPI(title="agentops-loop", version="0.1.0")
_svc: Service | None = None


def svc() -> Service:
    global _svc
    if _svc is None:
        _svc = Service(load_config())
    return _svc


@app.get("/health", response_model=Health)
def health():
    s = svc()
    return Health(status="ok", chunks=len(s.kb.chunks), config_hash=config_hash(s.cfg), llm=s.llm.name)


@app.post("/ingest", response_model=IngestOut, status_code=202)
def ingest(body: IngestIn):
    s = svc()
    ids = s.kb.ingest(body.source, body.doc_id, body.text, body.classification, body.acl)
    s.invalidate()
    return IngestOut(doc_id=body.doc_id, chunk_ids=ids)


@app.post("/tickets", response_model=TicketResponse)
def tickets(body: TicketIn):
    return svc().handle(body.ticket, body.role, body.ticket_id)[0]


@app.post("/hooks/ticket", response_model=TicketResponse, status_code=202)
def hook_ticket(body: TicketIn):
    return svc().handle(body.ticket, body.role, body.ticket_id)[0]


@app.post("/eval")
def run_eval():
    from eval.holdout import run_holdout
    return run_holdout(load_config())


@app.post("/loop")
def run_loop():
    from loop.loop import run_attempt
    return run_attempt()
