from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from eventforge.events.schemas import QueryDepth


class SubmitQueryRequest(BaseModel):
    """HTTP body for POST /api/v1/queries."""

    topic: str = Field(min_length=1)
    depth: QueryDepth = QueryDepth.STANDARD
    max_sources: int | None = Field(default=None, ge=1, le=100)


class SubmitQueryResponse(BaseModel):
    """HTTP response after a query is accepted into the pipeline."""

    job_id: UUID
    correlation_id: str


class JobStageResponse(BaseModel):
    """One pipeline stage and its execution status."""

    stage: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    error_detail: str | None


class SynthesisReportResponse(BaseModel):
    """Final report produced by the synthesis stage."""

    id: UUID
    content: str
    created_at: datetime


class LLMUsageCallResponse(BaseModel):
    """One logged LLM call for a job."""

    id: UUID
    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    created_at: datetime


class LLMUsageSummaryResponse(BaseModel):
    """Aggregated LLM cost and per-call breakdown for a job."""

    total_cost_usd: float
    calls: list[LLMUsageCallResponse]


class QuerySummaryResponse(BaseModel):
    """Lightweight job summary for list endpoints."""

    job_id: UUID
    correlation_id: str
    topic: str
    depth: str
    status: str
    max_sources: int | None
    created_at: datetime
    updated_at: datetime


class QueryDetailResponse(BaseModel):
    """Full job detail including stages and optional synthesis report."""

    job_id: UUID
    correlation_id: str
    topic: str
    depth: str
    status: str
    max_sources: int | None
    created_at: datetime
    updated_at: datetime
    stages: list[JobStageResponse]
    synthesis_report: SynthesisReportResponse | None = None
    llm_usage: LLMUsageSummaryResponse
