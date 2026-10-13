"""One ticket end to end: supervisor -> search -> guard -> evidence gate -> specialist -> trace."""
import hashlib
import json
import os
import time
import uuid

import numpy as np

from app.agents import SUPERVISOR_SYSTEM, Agent, ToolDenied, build_prompt, specialist_answer
from app.config import config_hash
from app.corpus import load_corpus
from app.guard import scan
from app.llm import est_tokens, get_llm
from app.models import Trace, TraceSpan, TicketResponse
from app.reasons import Reason, record
from app.redact import redact
from app.retrieve import KnowledgeBase, Retriever

REFUSAL_TEXT = {
    Reason.weak_evidence: "I can't answer that from the approved knowledge base. A support agent will follow up.",
    Reason.acl_blocked: "That information is not available to you. A support agent will follow up.",
    Reason.injection_detected: "This request was blocked by a safety check and passed to a support agent.",
    Reason.tool_denied: "This request was blocked by a policy check and passed to a support agent.",
    Reason.budget_exceeded: "This request is too long to process automatically. A support agent will follow up.",
    Reason.bad_route: "This doesn't look like a student-service request, so I can't help with it here.",
}


def slack_text(r: dict) -> str:
    head = f"*Ticket {r['ticket_id']}* | route: {r['route']}"
    if r["refused"]:
        return f"{head} | refused ({r['reason']})\n{r['answer']}"
    cites = ", ".join(f"{c['chunk_id']} ({c['source']})" for c in r["citations"])
    return f"{head}\n{r['answer']}\nSources: {cites}"


class Service:
    def __init__(self, cfg: dict, kb: KnowledgeBase | None = None, llm=None, guard_on: bool = True,
                 mode: str = "hybrid_rerank", trace_path: str | None = None):
        self.cfg, self.chash = cfg, config_hash(cfg)
        self.kb = kb or KnowledgeBase(cfg, load_corpus(cfg["chunk_size"]))
        self.retriever = Retriever(self.kb, cfg)
        self.llm = llm or get_llm()
        self.guard_on, self.mode = guard_on, mode
        self.trace_path = trace_path or os.environ.get("AGENTOPS_TRACE_PATH")
        self.retrieval_cache: dict = {}
        self.answer_cache: list = []
        self.cache_hits = 0
        price = cfg["prices_per_mtok"].get(getattr(self.llm, "name", ""), cfg["prices_per_mtok"][cfg["llm_model"]])
        self.price_in, self.price_out = price["in"] / 1e6, price["out"] / 1e6
        self.supervisor = Agent("supervisor", {"route": lambda route: route, "refuse": lambda reason: reason})
        self.specialist = Agent("specialist", {"search": self._search})

    def invalidate(self):
        self.retrieval_cache.clear(); self.answer_cache.clear()

    def _search(self, query: str, role: str):
        key = (query, role, self.chash, self.mode)
        if key not in self.retrieval_cache:
            self.retrieval_cache[key] = self.retriever.search(query, role, self.mode)
        return self.retrieval_cache[key]

    def _dollars(self, u: dict) -> float:
        return u["in"] * self.price_in + u["out"] * self.price_out

    def handle(self, ticket: str, role: str = "public", ticket_id: str | None = None, seed: int = 0):
        tid = ticket_id or "tk-" + hashlib.sha256(ticket.encode()).hexdigest()[:8]
        red = redact(ticket)
        tr = Trace(trace_id=uuid.uuid4().hex[:12], ticket_id=tid, caller_role=role, ticket_redacted=red, config_hash=self.chash)
        out = dict(ticket_id=tid, route="none", answer="", citations=[], refused=False, reason=None)

        def finish():
            out["slack_text"] = slack_text(out)
            resp = TicketResponse(**out, trace_id=tr.trace_id, cache_hit=tr.cache_hit,
                                  dollars=round(tr.dollars, 8), latency_ms=round(tr.latency_ms, 2))
            if self.trace_path:
                with open(self.trace_path, "a") as f:
                    f.write(tr.model_dump_json() + "\n")
            return resp, tr

        def refuse(reason: Reason):
            record(reason)
            out.update(refused=True, reason=reason.value, answer=REFUSAL_TEXT[reason], citations=[])
            return finish()

        # answer cache: same role and config hash, cosine >= threshold
        t0 = time.perf_counter()
        qv = self.kb.embedder.embed_query(red)
        for c_role, c_hash, vec, cached in self.answer_cache:
            if c_role == role and c_hash == self.chash and float(np.dot(qv, vec)) >= self.cfg["answer_cache_cosine"]:
                self.cache_hits += 1
                tr.cache_hit = True
                tr.spans.append(TraceSpan(actor="cache", note="answer_cache_hit", latency_ms=(time.perf_counter() - t0) * 1000))
                out.update({k: cached[k] for k in ("route", "answer", "citations", "refused", "reason")})
                return finish()

        # 1. supervisor: route or refuse
        t0 = time.perf_counter()
        name, args, usage = self.llm.supervise(SUPERVISOR_SYSTEM, red)
        tr.spans.append(TraceSpan(actor="supervisor", tool=name, args_keys=sorted(args), tokens_in=usage["in"],
                                  tokens_out=usage["out"], dollars=self._dollars(usage), latency_ms=(time.perf_counter() - t0) * 1000))
        try:
            decision = self.supervisor.call_tool(name, **args)
        except ToolDenied:
            return refuse(Reason.tool_denied)
        if name == "refuse":
            return refuse(Reason.bad_route)
        out["route"] = decision

        # 2. specialist search (acl filter happens inside the retriever)
        t0 = time.perf_counter()
        try:
            ret = self.specialist.call_tool("search", query=red, role=role)
        except ToolDenied:
            return refuse(Reason.tool_denied)
        tr.spans.append(TraceSpan(actor="retriever", tool="search", args_keys=["query", "role"],
                                  chunk_ids=[h.chunk.id for h in ret.hits], latency_ms=(time.perf_counter() - t0) * 1000))
        spans = [{"chunk_id": h.chunk.id, "source": h.chunk.source, "text": redact(h.chunk.text)} for h in ret.hits]

        # 3. guard on spans before generation
        t0 = time.perf_counter()
        flagged = self.guard_on and scan([s["text"] for s in spans] + [red])
        tr.spans.append(TraceSpan(actor="guard", note="flagged" if flagged else ("off" if not self.guard_on else "clean"),
                                  latency_ms=(time.perf_counter() - t0) * 1000))
        if flagged:
            return refuse(Reason.injection_detected)

        # 4. evidence gate
        thr = self.cfg["refusal_threshold"]
        if ret.evidence < thr:
            return refuse(Reason.acl_blocked if ret.forbidden_evidence >= thr else Reason.weak_evidence)

        # 5. budget gate
        prompt = build_prompt(decision, red, spans, self.cfg["refusal_instruction"])
        if est_tokens(" ".join(m["content"] for m in prompt)) > self.cfg["budget"]["max_prompt_tokens"]:
            return refuse(Reason.budget_exceeded)

        # 6. specialist generation -> structured answer with validated citations
        t0 = time.perf_counter()
        answer, cited, usage = self.llm.answer(prompt, spans, seed)
        tr.spans.append(TraceSpan(actor="specialist", tool="generate", args_keys=["spans", "ticket"], chunk_ids=list(cited),
                                  tokens_in=usage["in"], tokens_out=usage["out"], dollars=self._dollars(usage),
                                  latency_ms=(time.perf_counter() - t0) * 1000))
        sa = specialist_answer(tid, decision, redact(answer), cited, {s["chunk_id"]: s["source"] for s in spans})
        if not sa.citations:
            return refuse(Reason.weak_evidence)
        out.update(answer=sa.answer, citations=[c.model_dump() for c in sa.citations])
        self.answer_cache.append((role, self.chash, qv, dict(out)))
        return finish()
