from app.retrieve import Retriever


def test_public_caller_receives_no_internal_chunk_even_if_it_ranks_first(kb, cfg):
    r = Retriever(kb, cfg)
    q = "What settlement discount can staff offer on arrears?"
    staff = r.search(q, "staff")
    assert staff.hits[0].chunk.acl == "staff"  # the internal chunk is the best match
    for mode in ("bm25", "dense", "hybrid", "hybrid_rerank"):
        assert all(h.chunk.acl == "public" for h in r.search(q, "public", mode).hits)


def test_top_k_is_five_and_ids_are_unique(kb, cfg):
    hits = Retriever(kb, cfg).search("refund within 30 days", "public").hits
    assert len(hits) == 5 and len({h.chunk.id for h in hits}) == 5


def test_embeddings_reuse_disk_cache_on_rerun(cfg):
    from app.corpus import load_corpus
    from app.embed import Embedder
    ch = load_corpus(cfg["chunk_size"])
    Embedder(cfg["embed_model"]).embed_chunks([c.id for c in ch], [c.text for c in ch])
    again = Embedder(cfg["embed_model"])
    again.embed_chunks([c.id for c in ch], [c.text for c in ch])
    assert again.computed == 0
