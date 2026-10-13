"""Vector store. Qdrant when QDRANT_URL is set (docker compose), in-memory otherwise.

The ACL filter is applied inside the store query, so a forbidden chunk is never a candidate.
"""
import os

import numpy as np


class InMemoryStore:
    name = "memory"

    def __init__(self):
        self.ids: list[str] = []
        self.acl: list[str] = []
        self.vecs = np.zeros((0, 384), dtype=np.float32)

    def upsert(self, ids, acls, vecs):
        for cid, acl, v in zip(ids, acls, vecs):
            if cid in self.ids:
                i = self.ids.index(cid); self.vecs[i] = v; self.acl[i] = acl
            else:
                self.ids.append(cid); self.acl.append(acl)
                self.vecs = np.vstack([self.vecs, v[None, :]])

    def search(self, vec, allowed_acl: set[str], limit: int) -> list[tuple[str, float]]:
        if not self.ids:
            return []
        sims = self.vecs @ vec
        order = np.argsort(-sims)
        out = [(self.ids[i], float(sims[i])) for i in order if self.acl[i] in allowed_acl]
        return out[:limit]


class QdrantStore:
    name = "qdrant"

    def __init__(self, url: str, collection: str = "chunks"):
        from qdrant_client import QdrantClient, models
        self.m = models
        self.c = QdrantClient(url=url)
        self.col = collection
        if not self.c.collection_exists(collection):
            self.c.create_collection(collection, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))

    def upsert(self, ids, acls, vecs):
        pts = [self.m.PointStruct(id=int(cid, 16) % (2**63), vector=v.tolist(), payload={"chunk_id": cid, "acl": acl})
               for cid, acl, v in zip(ids, acls, vecs)]
        self.c.upsert(self.col, pts)

    def search(self, vec, allowed_acl, limit):
        flt = self.m.Filter(must=[self.m.FieldCondition(key="acl", match=self.m.MatchAny(any=sorted(allowed_acl)))])
        res = self.c.query_points(self.col, query=vec.tolist(), query_filter=flt, limit=limit).points
        return [(p.payload["chunk_id"], float(p.score)) for p in res]


def make_store():
    url = os.environ.get("QDRANT_URL")
    return QdrantStore(url) if url else InMemoryStore()
