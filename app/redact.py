"""Strip email, phone and student-id patterns before anything is logged or sent to a model."""
import re

PATTERNS = [
    ("[EMAIL]", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("[STUDENT_ID]", re.compile(r"\bKOA-\d{6}\b", re.I)),
    ("[PHONE]", re.compile(r"(?:\+27|\b0)(?:[\s-]?\d){9}\b")),
]


def redact(text: str) -> str:
    for token, rx in PATTERNS:
        text = rx.sub(token, text)
    return text
