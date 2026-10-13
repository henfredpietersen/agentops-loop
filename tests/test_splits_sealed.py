import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"


def _rows(name):
    return [json.loads(l) for l in (D / f"{name}.jsonl").read_text().splitlines() if l.strip()]


def test_holdout_and_attacks_match_seal():
    seal = json.loads((D / "SEALED.json").read_text())
    for name in ("holdout", "attacks"):
        assert hashlib.sha256((D / f"{name}.jsonl").read_bytes()).hexdigest() == seal[name]


def test_split_sizes():
    tr = _rows("train")
    assert len(tr) >= 40 and sum(r["answerable"] for r in tr[:40]) == 28
    assert len(_rows("attacks")) == 10


def test_no_ticket_overlap_between_train_and_holdout():
    assert not {r["ticket"] for r in _rows("train")} & {r["ticket"] for r in _rows("holdout")}
