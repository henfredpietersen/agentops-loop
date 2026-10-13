import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["AGENTOPS_STANDIN"] = "1"
os.environ.setdefault("AGENTOPS_CACHE", tempfile.mkdtemp(prefix="agentops-cache-"))
os.environ.pop("LLM_PROVIDER", None)
LOG = ROOT / ".pytest_reasons.jsonl"
os.environ["AGENTOPS_REASONS_LOG"] = str(LOG)

import pytest  # noqa: E402

from app.config import load_config  # noqa: E402


def pytest_sessionstart(session):
    LOG.write_text("")


class MockLLM:
    """Generation is mocked in tests. Supervisor routing reuses the keyword stand-in."""
    name = "mock"

    def __init__(self, cite=None, answer=None, tool=None):
        from app.llm import StandInLLM
        self._sup = StandInLLM()
        self.calls = 0
        self.cite, self.answer_text, self.tool = cite, answer, tool

    def supervise(self, system, ticket):
        if self.tool:
            return self.tool, {}, {"in": 1, "out": 1}
        return self._sup.supervise(system, ticket)

    def answer(self, prompt, spans, seed):
        self.calls += 1
        cited = self.cite(spans) if self.cite else [spans[0]["chunk_id"]]
        return self.answer_text or spans[0]["text"], cited, {"in": 100, "out": 20}


@pytest.fixture
def cfg():
    c = load_config()
    c["prices_per_mtok"]["mock"] = c["prices_per_mtok"][c["llm_model"]]
    return c


@pytest.fixture(scope="session")
def kb():
    from app.corpus import load_corpus
    from app.retrieve import KnowledgeBase
    from app.store import InMemoryStore
    c = load_config()
    return KnowledgeBase(c, load_corpus(c["chunk_size"]), store=InMemoryStore())


@pytest.fixture
def mock_llm():
    return MockLLM
