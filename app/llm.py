"""LLM client. OpenAI-compatible chat/completions over httpx; provider picked by env.

LLM_PROVIDER = anthropic | openai | gemini, plus the matching *_API_KEY and optional LLM_MODEL.
With no key, a stand-in is used: a keyword router for the supervisor and a seeded extractive
generator for the specialist. The stand-in is labelled in every report; tests mock generation.
"""
import json
import os
import random
import re

import httpx

from app.text import tokens

PROVIDERS = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
    "anthropic": ("https://api.anthropic.com/v1", "ANTHROPIC_API_KEY", "claude-haiku-4-5"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY", "gemini-2.0-flash"),
}

ROUTE_TOOLS = [
    {"type": "function", "function": {"name": "route", "description": "Send the ticket to one specialist.",
     "parameters": {"type": "object", "properties": {"route": {"type": "string", "enum": ["refund", "access", "billing"]}}, "required": ["route"]}}},
    {"type": "function", "function": {"name": "refuse", "description": "Refuse: the ticket is not a student-service request.",
     "parameters": {"type": "object", "properties": {"reason": {"type": "string", "enum": ["bad_route"]}}, "required": ["reason"]}}},
]


def est_tokens(text: str) -> int:
    return max(1, round(len(text.split()) * 1.3))


class OpenAICompatLLM:
    def __init__(self, provider: str):
        base, key_env, default_model = PROVIDERS[provider]
        self.base, self.key = base, os.environ[key_env]
        self.model = os.environ.get("LLM_MODEL", default_model)
        self.name = f"{provider}:{self.model}"

    def _chat(self, messages, **kw) -> dict:
        r = httpx.post(f"{self.base}/chat/completions", timeout=60,
                       headers={"Authorization": f"Bearer {self.key}"},
                       json={"model": self.model, "messages": messages, "temperature": 0.2, **kw})
        r.raise_for_status()
        return r.json()

    def supervise(self, system: str, ticket: str) -> tuple[str, dict, dict]:
        d = self._chat([{"role": "system", "content": system}, {"role": "user", "content": ticket}],
                       tools=ROUTE_TOOLS, tool_choice="required")
        call = d["choices"][0]["message"]["tool_calls"][0]["function"]
        u = d.get("usage", {})
        return call["name"], json.loads(call["arguments"] or "{}"), {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0)}

    def answer(self, prompt: list[dict], spans: list[dict], seed: int) -> tuple[str, list[str], dict]:
        d = self._chat(prompt, response_format={"type": "json_object"}, seed=seed)
        u = d.get("usage", {})
        body = json.loads(d["choices"][0]["message"]["content"])
        return body.get("answer", ""), list(body.get("citations", [])), {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0)}


KEYWORDS = {
    "refund": ["refund", "cancel", "chargeback", "money back", "cooling"],
    "billing": ["fee", "invoice", "pay", "payment", "debit", "statement", "deposit", "sponsor", "arrears",
                "collections", "settlement", "vat", "eft", "bitcoin", "cost", "price", "american express"],
    "access": ["login", "log in", "password", "locked", "exam", "assessment", "access", "enrol", "certificate",
               "transcript", "academic record", "defer", "extension", "extend", "surname", "name", "re-sit",
               "remark", "mark", "verify", "verification", "authenticator", "proctor", "browser", "safari", "venue"],
}


class StandInLLM:
    name = "standin-extractive"

    def supervise(self, system: str, ticket: str):
        t = ticket.lower()
        score = {r: sum(t.count(k) for k in kws) for r, kws in KEYWORDS.items()}
        best = max(score, key=lambda r: (score[r], r == "refund", r == "billing"))
        usage = {"in": est_tokens(system + ticket), "out": 8}
        if score[best] == 0:
            return "refuse", {"reason": "bad_route"}, usage
        return "route", {"route": best}, usage

    def answer(self, prompt: list[dict], spans: list[dict], seed: int):
        rng = random.Random(seed)
        ticket = prompt[1]["content"].split("\n", 1)[0]
        pick = 0 if (len(spans) == 1 or rng.random() < 0.85) else 1
        span = spans[pick]
        q = set(tokens(ticket))
        lines = [l for l in span["text"].splitlines() if l.strip() and not l.lstrip().startswith("#") and not set(l.strip()) <= set("|-")]
        units = [u.strip(" |") for l in lines for u in re.split(r"(?<=[.!?])\s+", l) if u.strip(" |")] or [span["text"]]
        best = max(units, key=lambda u: (len(q & set(tokens(u))), -abs(len(u) - 90)))
        text = " ".join(prompt[0]["content"].split()) + "\n" + "\n".join(p["content"] for p in prompt[1:])
        return best, [span["chunk_id"]], {"in": est_tokens(text), "out": est_tokens(best)}


def get_llm():
    provider = os.environ.get("LLM_PROVIDER", "").lower()
    if provider in PROVIDERS and os.environ.get(PROVIDERS[provider][1]):
        return OpenAICompatLLM(provider)
    return StandInLLM()
