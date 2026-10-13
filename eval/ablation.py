"""Holdout ablations: BM25, dense, hybrid, hybrid+rerank, hybrid+rerank with the guard off."""
import json

from app.config import ROOT, load_config
from eval.holdout import run_holdout

ROWS = [("bm25", "bm25", True), ("dense", "dense", True), ("hybrid", "hybrid", True),
        ("hybrid+rerank", "hybrid_rerank", True), ("hybrid+rerank, guard off", "hybrid_rerank", False)]


def main() -> list[dict]:
    cfg = load_config()
    out = []
    for name, mode, guard in ROWS:
        r = run_holdout(cfg, mode=mode, guard_on=guard, label=f"ablation-{mode}-guard-{'on' if guard else 'off'}")
        out.append({"row": name, "mean_S": r["mean_S"], "spread": r["spread"], "recall": r["metrics_mean"]["recall"],
                    "span_support": r["metrics_mean"]["span_support"], "attack_refusal": r["attack_refusal"],
                    "median_dollars": r["median_dollars"], "p95_latency_ms": r["p95_latency_ms"], "backend": r["backend"]})
    (ROOT / "runs" / "ablation.json").write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    for r in main():
        print(r)
