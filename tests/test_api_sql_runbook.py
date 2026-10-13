import re
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

import app.api as api
from app.models import TicketResponse
from app.pipeline import Service
from app.reasons import Reason

ROOT = Path(__file__).resolve().parent.parent


def client(cfg, kb, mock_llm):
    api._svc = Service(cfg, kb=kb, llm=mock_llm())
    return TestClient(api.app)


def test_webhook_returns_202_and_structured_body(cfg, kb, mock_llm):
    c = client(cfg, kb, mock_llm)
    r = c.post("/hooks/ticket", json={"ticket": "What settlement discount can staff offer on arrears?", "role": "public"})
    assert r.status_code == 202
    body = TicketResponse(**r.json())
    assert body.refused and body.reason == Reason.acl_blocked and body.slack_text


def test_ingest_webhook_returns_202_and_chunk_ids(cfg, kb, mock_llm):
    c = client(cfg, kb, mock_llm)
    body = {"source": "lms", "doc_id": "new", "text": "# Library\n\nThe e-library is open 24 hours.", "classification": "public", "acl": "public"}
    r = c.post("/ingest", json=body)
    assert r.status_code == 202 and len(r.json()["chunk_ids"]) == 1
    assert c.post("/ingest", json=body).json()["chunk_ids"] == r.json()["chunk_ids"]


def test_openapi_matches_pydantic_models(cfg, kb, mock_llm):
    spec = client(cfg, kb, mock_llm).get("/openapi.json").json()
    props = spec["components"]["schemas"]["TicketResponse"]["properties"]
    assert set(props) == set(TicketResponse.model_fields)
    assert spec["components"]["schemas"]["Reason"]["enum"] == [r.value for r in Reason]


def test_leaked_chunk_sql_returns_zero(tmp_path, cfg):
    from eval.harness import run_train
    db = tmp_path / "eval.db"
    run_train(cfg, "test", db=db)
    q = (ROOT / "sql" / "check.sql").read_text().split(";")
    leak_sql = next(s for s in q if "leaked_chunks" in s)
    assert sqlite3.connect(db).execute(leak_sql).fetchone()[0] == 0


def test_runbook_codes_match_api_reason_codes():
    documented = set(re.findall(r"^### `(\w+)`", (ROOT / "RUNBOOK.md").read_text(), re.M))
    assert documented == {r.value for r in Reason}
