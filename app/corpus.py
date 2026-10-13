"""Load the governed corpus from data/corpus/*.md."""
from pathlib import Path

from app.chunking import Chunk, chunk_text, parse_doc
from app.config import ROOT

CORPUS_DIR = ROOT / "data" / "corpus"


def load_corpus(chunk_size: int = 512, corpus_dir: Path = CORPUS_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    for p in sorted(corpus_dir.glob("*.md")):
        meta, body = parse_doc(p.read_text())
        chunks.extend(chunk_text(body, meta, chunk_size))
    return chunks
