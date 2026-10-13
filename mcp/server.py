"""MCP server (stdio) exposing search and refuse over the same retriever and guard.

Run: python mcp/server.py   (no __init__.py here on purpose, so this folder never shadows the mcp package)
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from mcp.server import MCPServer  # noqa: E402

from app.config import load_config  # noqa: E402
from app.corpus import load_corpus  # noqa: E402
from app.guard import scan  # noqa: E402
from app.reasons import Reason  # noqa: E402
from app.redact import redact  # noqa: E402
from app.retrieve import KnowledgeBase, Retriever  # noqa: E402

server = MCPServer("agentops-loop")
_cfg = load_config()
_retriever = Retriever(KnowledgeBase(_cfg, load_corpus(_cfg["chunk_size"])), _cfg)


@server.tool()
def search(query: str, role: str = "public") -> dict:
    """Search the governed knowledge base. Returns up to 5 spans the role may see, redacted."""
    if role not in ("public", "staff"):
        return {"refused": True, "reason": Reason.tool_denied.value}
    res = _retriever.search(redact(query), role)
    spans = [{"chunk_id": h.chunk.id, "source": h.chunk.source, "score": round(h.score, 4), "text": redact(h.chunk.text)} for h in res.hits]
    if scan([s["text"] for s in spans]):
        return {"refused": True, "reason": Reason.injection_detected.value}
    return {"refused": False, "evidence": round(res.evidence, 4), "spans": spans}


@server.tool()
def refuse(reason: str) -> dict:
    """Refuse with one of the API reason codes."""
    if reason not in {r.value for r in Reason}:
        return {"refused": True, "reason": Reason.tool_denied.value}
    return {"refused": True, "reason": reason}


if __name__ == "__main__":
    server.run("stdio")
