"""Human command: copy one reviewed candidate into train.jsonl with human-supplied gold labels.

python scripts/promote_candidate.py --index 0 --ticket "..." --route refund --gold-chunk-id abc --gold-span "..."
Nothing in this repo copies anything into holdout.jsonl.
"""
import argparse
import json
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
ap = argparse.ArgumentParser()
ap.add_argument("--index", type=int, required=True)
ap.add_argument("--ticket", required=True)
ap.add_argument("--route", required=True, choices=["refund", "access", "billing", "none"])
ap.add_argument("--gold-chunk-id")
ap.add_argument("--gold-span")
ap.add_argument("--unanswerable", action="store_true")
a = ap.parse_args()
cand = [json.loads(l) for l in (D / "candidates.jsonl").read_text().splitlines() if l.strip()][a.index]
n = sum(1 for _ in (D / "train.jsonl").open())
row = {"id": f"c{n + 1:02d}", "ticket": a.ticket, "caller_role": cand["caller_role"], "route": a.route,
       "answerable": not a.unanswerable, "gold_chunk_id": a.gold_chunk_id, "gold_span": a.gold_span}
with (D / "train.jsonl").open("a") as f:
    f.write(json.dumps(row) + "\n")
print("appended", row)
