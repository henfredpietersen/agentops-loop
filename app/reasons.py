"""Reason codes. RUNBOOK.md must document exactly these; tests must raise each one."""
import json
import os
from enum import Enum


class Reason(str, Enum):
    weak_evidence = "weak_evidence"
    acl_blocked = "acl_blocked"
    injection_detected = "injection_detected"
    tool_denied = "tool_denied"
    budget_exceeded = "budget_exceeded"
    bad_route = "bad_route"


_SEEN: set[str] = set()


def record(reason: "Reason") -> None:
    _SEEN.add(reason.value)
    path = os.environ.get("AGENTOPS_REASONS_LOG")
    if path:
        with open(path, "a") as f:
            f.write(json.dumps(reason.value) + "\n")


def seen() -> set[str]:
    return set(_SEEN)
