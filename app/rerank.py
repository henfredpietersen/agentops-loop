"""Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2 when it loads, else a labelled stand-in.

Scores are in [0, 1] so the refusal threshold means the same thing for both backends.
"""
import math
import os

from app.text import tokens


class StandInReranker:
    name = "standin-idf-coverage"

    def __init__(self, idf: dict[str, float]):
        self.idf = idf

    def score(self, query: str, texts: list[str]) -> list[float]:
        q = list(dict.fromkeys(tokens(query)))
        total = sum(self.idf.get(t, 1.0) for t in q) or 1.0
        out = []
        for t in texts:
            ct = tokens(t)
            cs = set(ct)
            cov = sum(self.idf.get(w, 1.0) for w in q if w in cs) / total
            bigrams = set(zip(ct, ct[1:]))
            qb = list(zip(q, q[1:]))
            bonus = (sum(1 for b in qb if b in bigrams) / len(qb)) if qb else 0.0
            out.append(min(1.0, 0.85 * cov + 0.15 * bonus))
        return out


class CrossEncoderReranker:
    def __init__(self, model: str):
        from sentence_transformers import CrossEncoder
        self.m = CrossEncoder(model)
        self.name = model

    def score(self, query: str, texts: list[str]) -> list[float]:
        logits = self.m.predict([(query, t) for t in texts])
        return [1 / (1 + math.exp(-float(x))) for x in logits]


def make_reranker(model: str, idf: dict[str, float]):
    if os.environ.get("AGENTOPS_STANDIN") == "1":
        return StandInReranker(idf)
    try:
        return CrossEncoderReranker(model)
    except Exception:
        if os.environ.get("AGENTOPS_REQUIRE_MODELS") == "1":
            raise
        return StandInReranker(idf)
