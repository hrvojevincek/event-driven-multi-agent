"""add knowledge_entities table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-22 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_entities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("chunk_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_entities_chunk_id"), "knowledge_entities", ["chunk_id"], unique=False
    )
    op.create_index(
        op.f("ix_knowledge_entities_job_id"), "knowledge_entities", ["job_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_entities_job_id"), table_name="knowledge_entities")
    op.drop_index(op.f("ix_knowledge_entities_chunk_id"), table_name="knowledge_entities")
    op.drop_table("knowledge_entities")
