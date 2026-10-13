"""Actors and tool allowlists. A tool outside an actor's allowlist raises ToolDenied."""
from app.models import Citation, SpecialistAnswer

ALLOWLIST = {"supervisor": {"route", "refuse"}, "specialist": {"search"}}

SUPERVISOR_SYSTEM = ("You triage student-service tickets for an online college. Call route with one of "
                     "refund, access, billing, or call refuse if the ticket is not a student-service request.")
SPECIALIST_SYSTEM = {
    "refund": "You answer refund and cancellation questions.",
    "access": "You answer LMS access, assessment, enrolment and student record questions.",
    "billing": "You answer fee, invoice and payment questions.",
}
CITATION_RULE = ('Answer only from the spans. Cite the chunk_id of every span you use. Return JSON: '
                 '{"answer": str, "citations": [chunk_id]}.')


class ToolDenied(Exception):
    pass


class Agent:
    def __init__(self, name: str, tools: dict):
        self.name, self.tools = name, tools

    def call_tool(self, tool: str, **args):
        if tool not in ALLOWLIST[self.name]:
            raise ToolDenied(f"{self.name} may not call {tool}")
        return self.tools[tool](**args)


def build_prompt(route: str, ticket: str, spans: list[dict], refusal_instruction: str) -> list[dict]:
    """System line, ticket, five spans, citation rule. No history."""
    system = f"{SPECIALIST_SYSTEM[route]} {refusal_instruction}"
    body = "\n\n".join(f"[{s['chunk_id']}] {s['text']}" for s in spans)
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"{ticket}\n\nSPANS:\n{body}\n\n{CITATION_RULE}"}]


def specialist_answer(ticket_id: str, route: str, answer: str, cited: list[str], allowed: dict[str, str]) -> SpecialistAnswer:
    """Keep only citations that were retrieved and allowed for this caller."""
    cites = [Citation(chunk_id=c, source=allowed[c]) for c in dict.fromkeys(cited) if c in allowed]
    return SpecialistAnswer(ticket_id=ticket_id, route=route, answer=answer, citations=cites, refused=False)
