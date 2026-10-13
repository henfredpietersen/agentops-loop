import json
from pathlib import Path

import pytest

from eval.harness import EvalPass
from eval.score import metrics
from loop.loop import decide
from loop.propose import PatchRejected, validate_patch

ROOT = Path(__file__).resolve().parent.parent
ACCEPTED = {"mean_S": 0.90, "spread": 0.02}


def hold(mean, spread=0.01, gates_ok=True, attacks=1.0):
    return {"mean_S": mean, "spread": spread, "gates_ok": gates_ok, "attack_refusal": attacks}


def test_eval_pass_cannot_write_holdout():
    ep = EvalPass()
    for target in ("holdout.jsonl", "train.jsonl", "attacks.jsonl"):
        with pytest.raises(PermissionError):
            ep.write(ROOT / "data" / target, [{"x": 1}])
    with pytest.raises(PermissionError):
        ep.read("holdout")


def test_train_up_holdout_down_is_a_drop():
    v, why = decide(0.80, 0.85, True, hold(0.88), ACCEPTED)
    assert v == "drop" and "holdout" in why


def test_over_cap_cost_is_a_drop_even_if_s_rises():
    assert decide(0.80, 0.95, False, None, ACCEPTED)[0] == "drop"
    assert decide(0.80, 0.95, True, hold(0.99, gates_ok=False), ACCEPTED)[0] == "drop"


def test_keep_needs_spread_and_attacks():
    assert decide(0.80, 0.85, True, hold(0.95), ACCEPTED)[0] == "keep"
    assert decide(0.80, 0.85, True, hold(0.95, spread=0.05), ACCEPTED)[0] == "drop"
    assert decide(0.80, 0.85, True, hold(0.95, attacks=0.9), ACCEPTED)[0] == "drop"


def _row(cache_hit):
    return dict(answerable=True, gold_chunk_id="g", gold_span="ok", gold_route="refund", route="refund",
                refused=False, retrieved_ids=["g"], cited_ids=["g"], answer="ok", leaked=False, cache_hit=cache_hit)


def test_cache_hit_is_excluded_from_quality_numerator():
    assert metrics([_row(False), _row(False)])["S"] == 1.0
    m = metrics([_row(False), _row(True)])
    assert m["S"] == 0.5 and m["cache_hits"] == 1


@pytest.mark.parametrize("patch", [
    {"changes": {"refusal_threshold": 0.3}, "paths": ["eval/score.py"]},
    {"changes": {"refusal_threshold": 0.3}, "paths": ["data/holdout.jsonl"]},
    {"changes": {"refusal_threshold": 0.3}, "paths": ["tests/test_eval_loop.py"]},
    {"changes": {"refusal_threshold": 0.3}, "paths": ["RUNBOOK.md"]},
    {"changes": {"top_k": 50}},
    {"changes": {"hybrid_alpha": 0.9}},
    {"changes": {"refusal_threshold": 0.33}},
])
def test_patch_outside_menu_or_touching_protected_paths_is_rejected(patch):
    with pytest.raises(PatchRejected):
        validate_patch(patch)


def test_loop_does_not_import_holdout():
    import ast
    for p in (ROOT / "loop").glob("*.py"):
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [getattr(node, "module", "") or ""] + [a.name for a in node.names]
                assert not any("holdout" in n for n in names), p


def test_eval_pass_never_opens_holdout(cfg, monkeypatch):
    import builtins
    import pathlib
    from eval.harness import run_train
    opened = []
    real_open, real_read = builtins.open, pathlib.Path.read_text
    monkeypatch.setattr(builtins, "open", lambda f, *a, **k: (opened.append(str(f)), real_open(f, *a, **k))[1])
    monkeypatch.setattr(pathlib.Path, "read_text", lambda self, *a, **k: (opened.append(str(self)), real_read(self, *a, **k))[1])
    run_train(cfg, record=False)
    assert opened and not any("holdout" in o for o in opened)


def test_score_py_is_frozen():
    import hashlib
    digest = hashlib.sha256((ROOT / "eval" / "score.py").read_bytes()).hexdigest()
    assert digest == (ROOT / "tests" / "score.sha256").read_text().strip()
