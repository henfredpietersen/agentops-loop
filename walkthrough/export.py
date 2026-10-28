"""Export what the interactive walkthrough shows, by running this repo's own code.

    AGENTOPS_STANDIN=1 python walkthrough/export.py

Every answer, refusal and score on the page comes from here or from the logged
runs in runs/. Nothing is re-calculated in the browser. Timing and trace ids are
left out on purpose so the export is identical on every run (CI checks that).
"""

import ast
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("AGENTOPS_STANDIN", "1")
for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
    os.environ.pop(key, None)  # the published page always shows the labelled stand-in

from app.config import load_config  # noqa: E402
from app.pipeline import Service  # noqa: E402
from eval.harness import base_kb, run_attacks, run_rows  # noqa: E402
from eval.score import metrics  # noqa: E402


def jsonl(name):
    return [json.loads(line) for line in (ROOT / "data" / name).read_text().splitlines() if line.strip()]


def ask(svc, ticket, role):
    resp, _ = svc.handle(ticket, role)
    d = resp.model_dump(mode="json")
    return {"ticket": ticket, "role": role, "route": d["route"], "refused": d["refused"],
            "reason": d["reason"], "answer": d["answer"],
            "citations": [{"chunk_id": c["chunk_id"], "source": c["source"]} for c in d["citations"]]}


def test_names(path):
    tree = ast.parse(path.read_text())
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]


def build() -> dict:
    cfg = load_config()
    svc = Service(cfg, kb=base_kb(cfg))
    train = {t["id"]: t for t in jsonl("train.jsonl")}

    # Every training ticket, scored one at a time with the frozen eval/score.py.
    rows, _ = run_rows(cfg, list(train.values()))
    train_S = metrics(rows)["S"]
    logged = json.loads((ROOT / "runs" / "1" / "decision.json").read_text())["train_S_before"]
    assert train_S == logged, f"train S {train_S} does not match the logged {logged}"
    tickets = []
    for r in rows:
        m = metrics([r])
        tickets.append({
            "id": r["ticket_id"], "ticket": train[r["ticket_id"]]["ticket"], "role": r["caller_role"],
            "answerable": r["answerable"], "gold_route": r["gold_route"], "route": r["route"],
            "refused": r["refused"], "reason": r["reason"], "answer": r["answer"], "gold_span": r["gold_span"],
            "checks": {
                "route": m["route_accuracy"] == 1.0,
                "refusal": m["refusal_accuracy"] == 1.0,
                "found_source": m["recall"] == 1.0 if r["answerable"] else None,
                "answer_supported": m["span_support"] == 1.0 if r["answerable"] else None,
                "no_leak": m["acl_compliance"] == 1.0,
            },
            "S": m["S"],
        })
    staff_q = train["t26"]["ticket"]
    acl = {"public": ask(svc, staff_q, "public"), "staff": ask(svc, staff_q, "staff")}
    out_of_scope = [ask(svc, train[i]["ticket"], "public") for i in ("u05", "u01")]

    attacks = {a["id"]: a for a in jsonl("attacks.jsonl")}
    guard = {}
    for label, on in (("on", True), ("off", False)):
        r = run_attacks(cfg, guard_on=on)
        guard[label] = {"attack_refusal": r["attack_refusal"], "detail": r["detail"]}
    attack_rows = []
    for d_on, d_off in zip(guard["on"]["detail"], guard["off"]["detail"], strict=True):
        a = attacks[d_on["id"]]
        poison = [ln for ln in a["poison_doc"]["text"].splitlines() if ln.strip() and not ln.startswith("#")]
        attack_rows.append({"id": a["id"], "ticket": a["ticket"], "planted": poison[0] if poison else "",
                            "guard_on": d_on, "guard_off": d_off})

    runs = [json.loads((ROOT / "runs" / str(i) / "decision.json").read_text()) for i in range(1, 7)]
    keep = ("run", "changes", "train_S_before", "train_S_after", "holdout_mean_S", "accepted_mean_S",
            "attack_refusal", "decision", "reason")
    accepted = json.loads((ROOT / "runs" / "accepted.json").read_text())
    ablation = json.loads((ROOT / "runs" / "ablation.json").read_text())

    return {
        "backend": accepted["backend"],
        "config": {"refusal_threshold": cfg.get("refusal_threshold")},
        "splits": {"train": len(train), "holdout": len(jsonl("holdout.jsonl")), "attacks": len(attacks)},
        "train_S": train_S,
        "tickets": tickets,
        "acl": acl,
        "out_of_scope": out_of_scope,
        "attacks": {"refusal_on": guard["on"]["attack_refusal"], "refusal_off": guard["off"]["attack_refusal"],
                    "rows": attack_rows},
        "runs": [{k: r.get(k) for k in keep} for r in runs],
        "accepted": {k: accepted[k] for k in ("config_hash", "samples", "mean_S", "spread", "attack_refusal",
                                               "leaked_responses", "metrics_mean")},
        "ablation": [{k: r[k] for k in ("row", "mean_S", "recall", "span_support", "attack_refusal")}
                     for r in ablation],
        "seal": json.loads((ROOT / "data" / "SEALED.json").read_text()),
        "seal_tests": test_names(ROOT / "tests" / "test_splits_sealed.py")
        + test_names(ROOT / "tests" / "test_eval_loop.py"),
        "policy_assistant": json.loads((ROOT / "walkthrough" / "policy_assistant_eval.json").read_text()),
    }


if __name__ == "__main__":
    out = ROOT / "walkthrough" / "data.json"
    out.write_text(json.dumps(build(), indent=1, sort_keys=True) + "\n")
    print(f"Wrote {out.relative_to(ROOT)}")
