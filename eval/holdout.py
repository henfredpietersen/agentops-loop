"""The only module that opens data/holdout.jsonl. Returns aggregates only, never rows or tickets.

Run as: python -m eval.holdout [--config path] [--samples 3] [--mode hybrid_rerank] [--guard off]
"""
import json
import statistics
from pathlib import Path

from app.config import ROOT, config_hash, load_config
from eval import runstore
from eval.harness import run_attacks, run_rows
from eval.score import WEIGHTS, gates, metrics

_HOLDOUT = ROOT / "data" / "holdout.jsonl"


def _rows() -> list[dict]:
    return [json.loads(l) for l in _HOLDOUT.read_text().splitlines() if l.strip()]


def run_holdout(cfg: dict, samples: int = 3, mode: str = "hybrid_rerank", guard_on: bool = True,
                label: str = "holdout", record: bool = True, db=runstore.DB, llm=None) -> dict:
    rows = _rows()
    ss, all_resp, per = [], [], []
    backend = ""
    for k in range(samples):
        res, svc = run_rows(cfg, rows, seed=k + 1, mode=mode, guard_on=guard_on, llm=llm)
        m, g = metrics(res), gates(res, cfg)
        backend = f"{svc.kb.embedder.name}|{svc.kb.reranker.name}|{svc.llm.name}"
        if record:
            runstore.record(label, "holdout", k, config_hash(cfg), mode, guard_on, m, g, backend, res, db=db)
        ss.append(m["S"]); all_resp += res; per.append(m)
    g = gates(all_resp, cfg)
    att = run_attacks(cfg, mode=mode, guard_on=guard_on, llm=llm)
    return {
        "label": label, "config_hash": config_hash(cfg), "mode": mode, "guard_on": guard_on, "backend": backend,
        "samples": ss, "mean_S": round(statistics.mean(ss), 4), "spread": round(max(ss) - min(ss), 4),
        "metrics_mean": {k: round(statistics.mean(p[k] for p in per), 4) for k in list(WEIGHTS) + ["cache_hits"]},
        "median_dollars": g["median_dollars"], "p95_latency_ms": g["p95_latency_ms"], "gates_ok": g["ok"],
        "attack_refusal": att["attack_refusal"],
        "leaked_responses": sum(r["leaked"] for r in all_resp),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--mode", default="hybrid_rerank")
    ap.add_argument("--guard", default="on")
    ap.add_argument("--label", default="holdout")
    a = ap.parse_args()
    cfg = load_config(Path(a.config) if a.config else None)
    print(json.dumps(run_holdout(cfg, a.samples, a.mode, a.guard == "on", a.label)))
