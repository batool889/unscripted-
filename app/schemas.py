from typing import Literal
from pydantic import BaseModel, Field

Status = Literal["answered", "partially_answered", "needs_clarification", "insufficient_evidence", "out_of_scope", "conflicting_sources"]

class Source(BaseModel):
    source_id: str
    document_id: str
    document_name: str
    source_url: str = ""
    page_start: int | None = None
    page_end: int | None = None
    printed_page: str | None = None
    article_number: str | None = None
    record_id: str | None = None
    excerpt: str
    verification_status: str = ""
    version: str = ""

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, max_length=100)
    style: Literal["formal", "levantine"] = "formal"
    language: Literal["ar", "en"] = "ar"

class ChatResponse(BaseModel):
    answer: str
    status: Status
    sources: list[Source] = []
    conversation_id: str
    clarification_question: str | None = None
    limitations: list[str] = []
    usage: dict = {}

class Claim(BaseModel):
    text: str
    source_ids: list[str]

class Draft(BaseModel):
    status: Status
    claims: list[Claim] = []
    message: str = ""
    clarification_question: str | None = None
    limitations: list[str] = []

class Verification(BaseModel):
    supported: bool
    unsupported_claim_indexes: list[int] = []

class PlanRequest(BaseModel):
    completed: list[str] = Field(default_factory=list, max_length=200)
    proposed: list[str] = Field(default_factory=list, max_length=30)
