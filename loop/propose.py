"""Proposer: one call per attempt, reads train failures only, may only pick from the menu.

With an LLM key the call goes to the model as one JSON request. Without one, a stand-in
heuristic maps failure counts to a menu move and skips moves already tried.
"""
import json
import os
from collections import Counter

from app.config import MENU

PROTECTED_PREFIXES = ("eval/", "tests/", "data/train.jsonl", "data/holdout.jsonl", "data/attacks.jsonl",
                      "data/SEALED.json", "RUNBOOK.md", "app/", "loop/")


class PatchRejected(Exception):
    pass


def validate_patch(patch: dict) -> dict:
    """A patch is {"changes": {menu_key: value}, "paths": ["config/config.json"]}. Anything else is rejected."""
    paths = patch.get("paths", ["config/config.json"])
    for p in paths:
        if p != "config/config.json" or any(p.startswith(x) for x in PROTECTED_PREFIXES):
            raise PatchRejected(f"patch touches protected path {p}")
    changes = patch.get("changes", {})
    if not changes or len(changes) > 1:
        raise PatchRejected("exactly one menu change per attempt")
    for k, v in changes.items():
        if k not in MENU:
            raise PatchRejected(f"{k} is not on the menu")
        allowed = MENU[k]
        if allowed is str:
            if not isinstance(v, str) or "\n" in v or len(v) > 200:
                raise PatchRejected("refusal_instruction must be one line")
        elif v not in allowed:
            raise PatchRejected(f"{k}={v} not in {allowed}")
    return changes


def _standin(cfg: dict, fails: list[dict], tried: set[str]) -> dict:
    why = Counter(w for f in fails for w in f["why"])
    thr = cfg["refusal_threshold"]
    moves = []
    direction = -1 if why["wrong_refusal"] >= why["should_refuse"] else 1
    for step in (1, 2, 3):  # nearest threshold moves first, in the direction the failures point
        moves.append(("refusal_threshold", round(thr + direction * 0.05 * step, 2)))
        moves.append(("refusal_threshold", round(thr - direction * 0.05 * step, 2)))
    if why["span_unsupported"]:
        moves += [("hybrid_alpha", a) for a in MENU["hybrid_alpha"] if a != cfg["hybrid_alpha"]]
        moves += [("rerank_depth", d) for d in MENU["rerank_depth"] if d != cfg["rerank_depth"]]
    moves += [("chunk_size", c) for c in MENU["chunk_size"] if c != cfg["chunk_size"]]
    for k, v in moves:
        key = json.dumps({k: v})
        if key not in tried and (k != "refusal_threshold" or v in MENU[k]):
            return {"changes": {k: v}, "paths": ["config/config.json"], "rationale": f"failures={dict(why)}"}
    return {"changes": {}, "paths": ["config/config.json"], "rationale": "menu exhausted"}


def propose(cfg: dict, fails: list[dict], tried: set[str], llm=None) -> dict:
    if llm is not None and hasattr(llm, "_chat"):
        menu = {k: (v if v is not str else "one line of text") for k, v in MENU.items()}
        msg = ("You tune a RAG service. Current config: " + json.dumps({k: cfg[k] for k in MENU}) +
               "\nTrain failures: " + json.dumps(fails[:40]) + "\nAlready tried: " + json.dumps(sorted(tried)) +
               "\nMenu: " + json.dumps(menu) +
               '\nReturn JSON {"changes": {one_key: value}, "paths": ["config/config.json"], "rationale": str}.')
        d = llm._chat([{"role": "user", "content": msg}], response_format={"type": "json_object"})
        return json.loads(d["choices"][0]["message"]["content"])
    return _standin(cfg, fails, tried)
