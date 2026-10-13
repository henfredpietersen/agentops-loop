"""Governed knowledge base + hybrid retriever.

Order: ACL filter -> BM25 and dense over allowed chunks -> weighted fusion -> rerank top
`rerank_depth` -> top_k. Nothing outside the final top_k is ever handed to generation.
"""
from dataclasses import dataclass, field

import numpy as np
from rank_bm25 import BM25Okapi

from app.chunking import Chunk, chunk_text
from app.embed import Embedder
from app.rerank import make_reranker
from app.store import make_store
from app.text import idf_table, tokens

ROLE_ACL = {"public": {"public"}, "staff": {"public", "staff"}}
MODES = ("bm25", "dense", "hybrid", "hybrid_rerank")


@dataclass
class Hit:
    chunk: Chunk
    score: float


@dataclass
class Retrieval:
    hits: list[Hit]
    evidence: float            # reranker score of top-1 allowed chunk
    forbidden_evidence: float  # best reranker score among chunks the role may NOT see (never returned)
    candidate_ids: list[str] = field(default_factory=list)


class KnowledgeBase:
    def __init__(self, cfg: dict, chunks: list[Chunk] | None = None, store=None):
        self.cfg = cfg
        self.chunks: dict[str, Chunk] = {}
        self.embedder = Embedder(cfg["embed_model"])
        self.store = store or make_store()
        self._bm25: dict[str, tuple[BM25Okapi, list[str]]] = {}
        self.reranker = None
        if chunks:
            self.add(chunks)

    def add(self, chunks: list[Chunk]) -> list[str]:
        new = [c for c in chunks]
        for c in new:
            self.chunks[c.id] = c
        vecs = self.embedder.embed_chunks([c.id for c in new], [c.text for c in new])
        self.store.upsert([c.id for c in new], [c.acl for c in new], vecs)
        self._bm25.clear()
        self.idf = idf_table([tokens(c.text) for c in self.chunks.values()])
        self.reranker = make_reranker(self.cfg["rerank_model"], self.idf)
        return [c.id for c in new]

    def ingest(self, source: str, doc_id: str, text: str, classification: str, acl: str) -> list[str]:
        meta = dict(doc_id=doc_id, source=source, classification=classification, acl=acl)
        return self.add(chunk_text(text, meta, self.cfg["chunk_size"]))

    def _bm25_for(self, acls: frozenset) -> tuple[BM25Okapi, list[str]]:
        key = ",".join(sorted(acls))
        if key not in self._bm25:
            ids = [cid for cid, c in self.chunks.items() if c.acl in acls]
            self._bm25[key] = (BM25Okapi([tokens(self.chunks[i].text) for i in ids]), ids)
        return self._bm25[key]


def _minmax(d: dict[str, float]) -> dict[str, float]:
    if not d:
        return {}
    lo, hi = min(d.values()), max(d.values())
    return {k: (v - lo) / (hi - lo) if hi > lo else 1.0 for k, v in d.items()}


class Retriever:
    def __init__(self, kb: KnowledgeBase, cfg: dict):
        self.kb, self.cfg = kb, cfg

    def _rank(self, query: str, acls: set[str], mode: str, depth: int) -> dict[str, float]:
        bm, ids = self.kb._bm25_for(frozenset(acls))
        bm_scores = dict(zip(ids, bm.get_scores(tokens(query)))) if ids else {}
        if mode == "bm25":
            return bm_scores
        dense = dict(self.kb.store.search(self.kb.embedder.embed_query(query), acls, limit=max(depth, 50)))
        if mode == "dense":
            return dense
        a = self.cfg["hybrid_alpha"]
        b, d = _minmax(bm_scores), _minmax(dense)
        return {k: a * d.get(k, 0.0) + (1 - a) * b.get(k, 0.0) for k in set(b) | set(d)}

    def search(self, query: str, role: str, mode: str = "hybrid_rerank") -> Retrieval:
        assert mode in MODES
        acls = ROLE_ACL[role]
        k, depth = self.cfg["top_k"], self.cfg["rerank_depth"]
        fused = self._rank(query, acls, mode, depth)
        cand = sorted(fused, key=lambda x: -fused[x])[:depth]
        rr = dict(zip(cand, self.kb.reranker.score(query, [self.kb.chunks[c].text for c in cand])))
        order = sorted(cand, key=lambda x: -rr[x]) if mode == "hybrid_rerank" else cand
        top = order[:k]
        hits = [Hit(self.kb.chunks[c], rr[c] if mode == "hybrid_rerank" else fused[c]) for c in top]
        assert all(h.chunk.acl in acls for h in hits)
        evidence = max((rr[c] for c in top), default=0.0)
        forbidden = 0.0
        hidden = {"staff"} - acls
        if hidden:  # acl-miss probe: score only, ids and text never leave this function
            f_rank = self._rank(query, hidden, "bm25", depth)
            f_cand = sorted(f_rank, key=lambda x: -f_rank[x])[:5]
            if f_cand:
                forbidden = max(self.kb.reranker.score(query, [self.kb.chunks[c].text for c in f_cand]))
        return Retrieval(hits=hits, evidence=evidence, forbidden_evidence=forbidden, candidate_ids=cand)
