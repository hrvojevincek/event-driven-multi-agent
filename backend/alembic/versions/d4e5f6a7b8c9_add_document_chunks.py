"""add document_chunks table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-22 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

MOCK_EMBEDDING_DIMENSION = 8

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(MOCK_EMBEDDING_DIMENSION), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "chunk_index",
            name="uq_document_chunks_source_id_chunk_index",
        ),
    )
    op.create_index(op.f("ix_document_chunks_job_id"), "document_chunks", ["job_id"], unique=False)
    op.create_index(
        op.f("ix_document_chunks_source_id"), "document_chunks", ["source_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunks_source_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_job_id"), table_name="document_chunks")
    op.drop_table("document_chunks")
