"""add sources table

Revision ID: a1b2c3d4e5f6
Revises: 5f4297155502
Create Date: 2026-06-21 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "5f4297155502"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sources_job_id"), "sources", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sources_job_id"), table_name="sources")
    op.drop_table("sources")
