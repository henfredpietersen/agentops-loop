"""Snapshot policy-assistant's retrieval evaluation for the walkthrough page.

    python walkthrough/export_policy_assistant.py /path/to/policy-assistant

Runs that repo's own retriever and eval set, and records which section it ranked
first for every question. The snapshot is committed here with the source commit,
because CI for this repo does not check out policy-assistant.
"""

import json
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "policy_assistant_eval.json"


def main(repo: str) -> int:
    repo_path = Path(repo).resolve()
    sys.path.insert(0, str(repo_path / "src"))
    import pandas as pd
    from policy_assistant.documents import load_chunks
    from policy_assistant.evaluation import evaluate_retriever
    from policy_assistant.retriever import TfidfRetriever

    chunks = load_chunks(repo_path / "data" / "docs")
    retriever = TfidfRetriever().fit(chunks)
    df = pd.read_csv(repo_path / "data" / "retrieval_eval.csv")
    metrics = evaluate_retriever(retriever, df)
    questions = []
    for q, expected in zip(df["question"], df["expected_id"], strict=True):
        results = retriever.search(q, top_k=3)
        ids = [r.chunk.id for r in results]
        questions.append({
            "question": q, "expected": expected,
            "rank": ids.index(expected) + 1 if expected in ids else None,
            "results": [{"id": r.chunk.id, "title": r.chunk.title, "score": round(r.score, 3)} for r in results],
        })
    commit = subprocess.run(["git", "-C", str(repo_path), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    snap = {"repo": "henfredpietersen/policy-assistant", "commit": commit, "n": metrics.n,
            "hit_at_1": round(metrics.hit_at_1, 4), "hit_at_3": round(metrics.hit_at_3, 4),
            "mrr": round(metrics.mrr, 4), "questions": questions}
    OUT.write_text(json.dumps(snap, indent=1, sort_keys=True) + "\n")
    print(f"Wrote {OUT.name}: Hit@1 {metrics.hit_at_1:.2f}, Hit@3 {metrics.hit_at_3:.2f}, MRR {metrics.mrr:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
