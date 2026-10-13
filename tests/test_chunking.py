from app.chunking import chunk_text, chunk_id
from app.corpus import load_corpus

META = dict(doc_id="d", source="lms", classification="public", acl="public")


def test_table_stays_one_chunk_even_when_over_chunk_size():
    rows = "\n".join(f"| row {i} | value {i} | note {i} |" for i in range(80))
    body = "# Fees\n\nIntro line.\n\n| a | b | c |\n|---|---|---|\n" + rows
    chunks = chunk_text(body, META, chunk_size=50)
    table_chunks = [c for c in chunks if "| row 0 |" in c.text]
    assert len(table_chunks) == 1
    assert "| row 79 |" in table_chunks[0].text


def test_unchanged_text_keeps_chunk_id_across_reingest():
    a = load_corpus(512)
    b = load_corpus(512)
    assert [c.id for c in a] == [c.id for c in b]
    assert chunk_id("Hello   World\n") == chunk_id("hello world")


def test_changed_text_changes_id():
    assert chunk_id("refund within 30 days") != chunk_id("refund within 14 days")


def test_corpus_has_internal_and_public_and_24_docs():
    chunks = load_corpus()
    assert len({c.doc_id for c in chunks}) == 24
    assert {c.acl for c in chunks} == {"public", "staff"}
    assert all((c.classification == "internal") == (c.acl == "staff") for c in chunks)
