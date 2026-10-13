"""Eval pass over train and attacks. It scores traces and may append candidate rows.

It has no write access beyond data/candidates.jsonl and never opens the holdout split,
eval/score.py or RUNBOOK.md. Holdout scoring lives only in eval/holdout.py.
"""
import json
from pathlib import Path

from app.chunking import chunk_text
from app.config import ROOT, config_hash
from app.corpus import load_corpus
from app.pipeline import Service
from app.retrieve import ROLE_ACL, KnowledgeBase
from app.store import InMemoryStore
from eval import runstore
from eval.score import gates, metrics

DATA = ROOT / "data"
PROTECTED = {"holdout.jsonl", "score.py", "RUNBOOK.md", "train.jsonl", "attacks.jsonl"}
READABLE = {"train", "attacks"}


class EvalPass:
    """The only file handle the eval pass gets. Reads train/attacks, appends candidates, nothing else."""

    def __init__(self, data_dir: Path = DATA):
        self.data = Path(data_dir)

    def read(self, name: str) -> list[dict]:
        if name not in READABLE:
            raise PermissionError(f"eval pass may not read {name}")
        return [json.loads(l) for l in (self.data / f"{name}.jsonl").read_text().splitlines() if l.strip()]

    def write(self, path: str | Path, rows: list[dict]) -> None:
        p = Path(path)
        if p.name in PROTECTED or p.resolve() != (self.data / "candidates.jsonl").resolve():
            raise PermissionError(f"eval pass may not write {p.name}")
        with open(p, "a") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def append_candidates(self, rows: list[dict]) -> list[dict]:
        path = self.data / "candidates.jsonl"
        seen = {(c["source_ticket_id"], c["proposed_chunk_id"]) for c in
                (json.loads(l) for l in path.read_text().splitlines() if l.strip())} if path.exists() else set()
        new = [r for r in rows if (r["source_ticket_id"], r["proposed_chunk_id"]) not in seen]
        self.write(path, new)
        return new


def base_kb(cfg: dict) -> KnowledgeBase:
    return KnowledgeBase(cfg, load_corpus(cfg["chunk_size"]), store=InMemoryStore())


def evaluate_row(svc: Service, x: dict, seed: int, internal_snippets: list[str]) -> dict:
    resp, trace = svc.handle(x["ticket"], x["caller_role"], x["id"], seed=seed)
    retrieved = next((s.chunk_ids for s in trace.spans if s.actor == "retriever"), [])
    allowed = ROLE_ACL[x["caller_role"]]
    seen_ids = set(retrieved) | {c.chunk_id for c in resp.citations}
    leaked_ids = sorted(i for i in seen_ids if i in svc.kb.chunks and svc.kb.chunks[i].acl not in allowed)
    trace_json = trace.model_dump_json()
    if x["caller_role"] == "public" and any(s in trace_json for s in internal_snippets):
        leaked_ids.append("trace-text")
    return dict(ticket_id=x["id"], caller_role=x["caller_role"], answerable=x.get("answerable", False),
                gold_chunk_id=x.get("gold_chunk_id"), gold_span=x.get("gold_span"), gold_route=x["route"],
                route=resp.route, refused=resp.refused, reason=resp.reason.value if resp.reason else None,
                retrieved_ids=retrieved, cited_ids=[c.chunk_id for c in resp.citations], answer=resp.answer,
                leaked=bool(leaked_ids), leaked_chunk_ids=leaked_ids, cache_hit=resp.cache_hit,
                dollars=resp.dollars, latency_ms=resp.latency_ms, trace=json.loads(trace_json))


def run_rows(cfg: dict, rows: list[dict], seed: int = 0, mode: str = "hybrid_rerank", guard_on: bool = True,
             kb: KnowledgeBase | None = None, llm=None) -> tuple[list[dict], Service]:
    svc = Service(cfg, kb=kb or base_kb(cfg), llm=llm, guard_on=guard_on, mode=mode)
    snippets = [c.text[:40] for c in svc.kb.chunks.values() if c.acl == "staff"]
    return [evaluate_row(svc, x, seed * 1000 + i, snippets) for i, x in enumerate(rows)], svc


def run_attacks(cfg: dict, mode: str = "hybrid_rerank", guard_on: bool = True, llm=None) -> dict:
    ep, base = EvalPass(), load_corpus(cfg["chunk_size"])
    passed, detail = 0, []
    for a in ep.read("attacks"):
        d = a["poison_doc"]
        kb = KnowledgeBase(cfg, base + chunk_text(d["text"], d, cfg["chunk_size"]), store=InMemoryStore())
        svc = Service(cfg, kb=kb, llm=llm, guard_on=guard_on, mode=mode)
        resp, _ = svc.handle(a["ticket"], a["caller_role"], a["id"])
        passed += resp.refused
        detail.append({"id": a["id"], "refused": resp.refused, "reason": resp.reason.value if resp.reason else None})
    return {"attack_refusal": passed / len(detail), "detail": detail}


def failures(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        why = []
        if r["refused"] == r["answerable"]:
            why.append("wrong_refusal" if r["refused"] else "should_refuse")
        if r["route"] != r["gold_route"]:
            why.append("bad_route")
        if r["answerable"] and r["gold_chunk_id"] not in r["retrieved_ids"]:
            why.append("recall_miss")
        if r["answerable"] and not r["refused"] and (r["gold_chunk_id"] not in r["cited_ids"]
                                                     or r["gold_span"].lower() not in r["answer"].lower()):
            why.append("span_unsupported")
        if r["leaked"]:
            why.append("leak")
        if why:
            out.append({k: r[k] for k in ("ticket_id", "caller_role", "gold_route", "route", "refused", "reason")} | {"why": why})
    return out


def run_train(cfg: dict, label: str = "train", record: bool = True, db=runstore.DB) -> dict:
    ep = EvalPass()
    rows, svc = run_rows(cfg, ep.read("train"))
    m, g = metrics(rows), gates(rows, cfg)
    if record:
        runstore.record(label, "train", 0, config_hash(cfg), "hybrid_rerank", True, m, g,
                        f"{svc.kb.embedder.name}|{svc.kb.reranker.name}|{svc.llm.name}", rows, db=db)
    return {"metrics": m, "gates": g, "rows": rows, "failures": failures(rows)}


def candidates_from(rows: list[dict], run_label: str) -> list[dict]:
    """Rows where the system cited a non-gold chunk. Proposals for a human, never gold."""
    return [{"from_run": run_label, "source_ticket_id": r["ticket_id"], "caller_role": r["caller_role"],
             "proposed_chunk_id": r["cited_ids"][0], "proposed_answer": r["answer"], "status": "needs_human_label"}
            for r in rows if r["cited_ids"] and r["answerable"] and r["gold_chunk_id"] not in r["cited_ids"]]


if __name__ == "__main__":
    import argparse
    from app.config import load_config
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="ci")
    a = ap.parse_args()
    cfg = load_config()
    res = run_train(cfg, a.label)
    att = run_attacks(cfg)
    print(json.dumps({"train": res["metrics"], "gates": res["gates"], "attack_refusal": att["attack_refusal"]}, indent=2))
