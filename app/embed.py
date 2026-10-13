"""Dense embeddings with an on-disk cache keyed by chunk hash.

Backend: sentence-transformers all-MiniLM-L6-v2 when it can load. If the model cannot
load (no package or no network) and AGENTOPS_REQUIRE_MODELS is not set, a hashed
bag-of-words stand-in is used and reported as backend="standin-hash". Reports always
name the backend so numbers are never passed off as MiniLM numbers.
"""
import hashlib
import os
from pathlib import Path

import numpy as np

from app.config import ROOT
from app.text import tokens

CACHE_DIR = Path(os.environ.get("AGENTOPS_CACHE", ROOT / ".cache"))
DIM = 384


class HashEmbedder:
    name = "standin-hash"

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), DIM), dtype=np.float32)
        for i, t in enumerate(texts):
            toks = tokens(t)
            feats = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
            for f in feats:
                h = int(hashlib.md5(f.encode()).hexdigest(), 16)
                out[i, h % DIM] += 1.0 if (h >> 64) & 1 else -1.0
            n = np.linalg.norm(out[i])
            if n:
                out[i] /= n
        return out


class STEmbedder:
    def __init__(self, model: str):
        from sentence_transformers import SentenceTransformer
        self.m = SentenceTransformer(model)
        self.name = model

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self.m.encode(texts, normalize_embeddings=True), dtype=np.float32)


def make_backend(model: str):
    if os.environ.get("AGENTOPS_STANDIN") == "1":
        return HashEmbedder()
    try:
        return STEmbedder(model)
    except Exception:
        if os.environ.get("AGENTOPS_REQUIRE_MODELS") == "1":
            raise
        return HashEmbedder()


class Embedder:
    def __init__(self, model: str):
        self.backend = make_backend(model)
        self.dir = CACHE_DIR / "emb" / self.backend.name.replace("/", "_")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.computed = 0  # number of chunk texts actually embedded (cache misses)

    @property
    def name(self) -> str:
        return self.backend.name

    def embed_chunks(self, ids: list[str], texts: list[str]) -> np.ndarray:
        vecs, missing = [None] * len(ids), []
        for i, cid in enumerate(ids):
            p = self.dir / f"{cid}.npy"
            if p.exists():
                vecs[i] = np.load(p)
            else:
                missing.append(i)
        if missing:
            new = self.backend.encode([texts[i] for i in missing])
            self.computed += len(missing)
            for j, i in enumerate(missing):
                np.save(self.dir / f"{ids[i]}.npy", new[j])
                vecs[i] = new[j]
        return np.vstack(vecs) if vecs else np.zeros((0, DIM), dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self.backend.encode([text])[0]
