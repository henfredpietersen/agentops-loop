import asyncio
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("agentops_mcp_server", ROOT / "mcp" / "server.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_mcp_exposes_search_and_refuse_with_acl():
    mod = _load()
    names = {t.name for t in asyncio.run(mod.server.list_tools())}
    assert names == {"search", "refuse"}
    out = mod.search("What settlement discount can staff offer on arrears?", "public")
    staff_ids = {c.id for c in mod._retriever.kb.chunks.values() if c.acl == "staff"}
    assert not {s["chunk_id"] for s in out["spans"]} & staff_ids
    assert mod.refuse("weak_evidence") == {"refused": True, "reason": "weak_evidence"}
