import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from eventforge.events.schemas.constants import EMBEDDING_DIMENSION


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""


class JobStatus(StrEnum):
    """Lifecycle states for a research job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStageName(StrEnum):
    """Named stages in the pipeline, in execution order."""
    INGESTION = "ingestion"
    EMBEDDING = "embedding"
    KNOWLEDGE_MINING = "knowledge_mining"
    RESEARCH = "research"
    SYNTHESIS = "synthesis"


class StageStatus(StrEnum):
    """Per-stage execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """Authenticated user keyed by external auth subject (mock user locally)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_subject_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    jobs: Mapped[list["Job"]] = relationship(back_populates="user")


class Job(Base):
    """A research query and its overall pipeline state."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[str] = mapped_column(
        String(32), nullable=False, default="standard")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=JobStatus.PENDING.value)
    max_sources: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="jobs")
    stages: Mapped[list["JobStage"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    sources: Mapped[list["Source"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    document_chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    knowledge_entities: Mapped[list["KnowledgeEntity"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    research_notes: Mapped[list["ResearchNote"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    synthesis_report: Mapped["SynthesisReport | None"] = relationship(
        back_populates="job", cascade="all, delete-orphan", uselist=False
    )
    llm_usage_records: Mapped[list["LLMUsage"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class LLMUsage(Base):
    """Token usage and cost for one LLM call within a job."""

    __tablename__ = "llm_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["Job"] = relationship(back_populates="llm_usage_records")


class JobStage(Base):
    """Execution record for one pipeline stage on a job."""

    __tablename__ = "job_stages"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "stage",
            name="uq_job_stages_job_id_stage"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(
        "jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StageStatus.PENDING.value
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    job: Mapped["Job"] = relationship(back_populates="stages")


class Source(Base):
    """Web source discovered during ingestion."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey(
        "jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["Job"] = relationship(back_populates="sources")
    document_chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """Chunked source text with a pgvector embedding."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "chunk_index",
            name="uq_document_chunks_source_id_chunk_index",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIMENSION), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["Job"] = relationship(back_populates="document_chunks")
    source: Mapped["Source"] = relationship(back_populates="document_chunks")
    knowledge_entities: Mapped[list["KnowledgeEntity"]] = relationship(
        back_populates="chunk"
    )


class KnowledgeEntity(Base):
    """Entity extracted from a document chunk during knowledge mining."""

    __tablename__ = "knowledge_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["Job"] = relationship(back_populates="knowledge_entities")
    chunk: Mapped["DocumentChunk | None"] = relationship(back_populates="knowledge_entities")


class ResearchNote(Base):
    """Output of one parallel research sub-task."""

    __tablename__ = "research_notes"
    __table_args__ = (
        UniqueConstraint("job_id", "task_index", name="uq_research_notes_job_id_task_index"),
        UniqueConstraint("task_id", name="uq_research_notes_task_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    task_index: Mapped[int] = mapped_column(Integer, nullable=False)
    sub_query: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["Job"] = relationship(back_populates="research_notes")


class SynthesisReport(Base):
    """Final synthesized report for a completed job."""

    __tablename__ = "synthesis_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["Job"] = relationship(back_populates="synthesis_report")


class ProcessedEvent(Base):
    """Idempotency record — composite PK (event_id, worker_name)."""

    __tablename__ = "processed_events"

    # Composite PK lets each consumer claim the same event_id independently
    # (e.g. the API publisher and the ingestion worker both reference one
    # query.submitted event_id without colliding).
    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
