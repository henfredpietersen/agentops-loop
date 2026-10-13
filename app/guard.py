"""Guard: scans retrieved spans (and the ticket) for injection or role escalation before generation."""
import re

INJECTION = [
    r"ignore (all )?(previous|prior|above) instructions", r"disregard (the|all|your)", r"system prompt",
    r"you are now", r"admin mode", r"forget your rules", r"new instruction", r"note to ai",
    r"<!--", r"\bassistant:", r"\bsystem:", r"override", r"bypass", r"reveal (your|the)",
]
ESCALATION = [
    r"treat (this|the) (caller|user) as staff", r"set role\s*=?\s*staff", r"role\s*=\s*staff",
    r"include internal documents", r"return internal chunks", r"grant access to the admin",
    r"i authori[sz]e you",
]
_RX = re.compile("|".join(f"(?:{p})" for p in INJECTION + ESCALATION), re.I)


def scan(texts: list[str]) -> bool:
    """True if any text carries an injection or escalation pattern."""
    return any(_RX.search(t) for t in texts)
