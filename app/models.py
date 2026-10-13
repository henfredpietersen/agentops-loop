"""Pydantic contracts. The OpenAPI schema is generated from these."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.reasons import Reason

Role = Literal["public", "staff"]
Route = Literal["refund", "access", "billing", "none"]


class Citation(BaseModel):
    chunk_id: str
    source: str


class SpecialistAnswer(BaseModel):
    ticket_id: str
    route: Route
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    refused: bool
    reason: Optional[Reason] = None


class TicketIn(BaseModel):
    ticket: str
    role: Role = "public"
    ticket_id: Optional[str] = None


class TraceSpan(BaseModel):
    actor: str
    tool: Optional[str] = None
    args_keys: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    dollars: float = 0.0
    note: Optional[str] = None


class Trace(BaseModel):
    trace_id: str
    ticket_id: str
    caller_role: Role
    ticket_redacted: str
    config_hash: str
    cache_hit: bool = False
    spans: list[TraceSpan] = Field(default_factory=list)

    @property
    def dollars(self) -> float:
        return sum(s.dollars for s in self.spans)

    @property
    def latency_ms(self) -> float:
        return sum(s.latency_ms for s in self.spans)


class TicketResponse(SpecialistAnswer):
    slack_text: str
    trace_id: str
    cache_hit: bool = False
    dollars: float = 0.0
    latency_ms: float = 0.0


class IngestIn(BaseModel):
    source: str
    doc_id: str
    text: str
    classification: Literal["public", "internal"]
    acl: Literal["public", "staff"]


class IngestOut(BaseModel):
    doc_id: str
    chunk_ids: list[str]


class Health(BaseModel):
    status: Literal["ok"]
    chunks: int
    config_hash: str
    llm: str
