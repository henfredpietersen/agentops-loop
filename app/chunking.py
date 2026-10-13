"""Heading-aware chunking. Tables are atomic. Chunk id = hash of normalized text."""
import hashlib
import re
from dataclasses import dataclass, asdict


@dataclass
class Chunk:
    id: str
    doc_id: str
    source: str
    classification: str
    acl: str
    heading: str
    text: str

    def dict(self) -> dict:
        return asdict(self)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def chunk_id(text: str) -> str:
    return hashlib.sha256(normalize(text).encode()).hexdigest()[:16]


def _blocks(lines: list[str]) -> list[str]:
    """Group lines into blocks split on blank lines; a table is always one block."""
    blocks, cur, in_table = [], [], False
    for line in lines:
        is_table = line.lstrip().startswith("|")
        if is_table != in_table and cur:
            blocks.append("\n".join(cur)); cur = []
        in_table = is_table
        if not line.strip() and not in_table:
            if cur:
                blocks.append("\n".join(cur)); cur = []
            continue
        cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    return [b for b in blocks if b.strip()]


def _sections(body: str) -> list[tuple[str, list[str]]]:
    sections, heading, cur = [], "", []
    for line in body.splitlines():
        if re.match(r"^#{1,6}\s", line):
            if any(l.strip() for l in cur):
                sections.append((heading, cur))
            heading, cur = line.lstrip("#").strip(), [line]
        else:
            cur.append(line)
    if any(l.strip() for l in cur):
        sections.append((heading, cur))
    return sections


def _words(s: str) -> int:
    return len(s.split())


def chunk_text(body: str, meta: dict, chunk_size: int = 512) -> list[Chunk]:
    out: list[Chunk] = []
    for heading, lines in _sections(body):
        blocks = _blocks(lines)
        packed, cur = [], []
        for b in blocks:
            if cur and _words("\n\n".join(cur + [b])) > chunk_size:
                packed.append(cur); cur = []
            cur.append(b)  # a table block is never split, even if it alone exceeds chunk_size
        if cur:
            packed.append(cur)
        for group in packed:
            text = "\n\n".join(group)
            if len(group) == 1 and re.match(r"^#{1,6}\s", text) and "\n" not in text:
                continue  # bare heading with no body
            out.append(Chunk(id=chunk_id(text), doc_id=meta["doc_id"], source=meta["source"],
                             classification=meta["classification"], acl=meta["acl"],
                             heading=heading, text=text))
    return out


def parse_doc(raw: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise ValueError("missing front matter")
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)
    return meta, m.group(2)
