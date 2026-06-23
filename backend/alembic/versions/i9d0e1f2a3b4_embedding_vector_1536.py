"""expand document_chunks embedding to 1536 dimensions

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-06-23 20:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector

EMBEDDING_DIMENSION = 1536
MOCK_EMBEDDING_DIMENSION = 8

revision: str = "i9d0e1f2a3b4"
down_revision: str | Sequence[str] | None = "h8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DELETE FROM document_chunks")
    op.alter_column(
        "document_chunks",
        "embedding",
        existing_type=Vector(MOCK_EMBEDDING_DIMENSION),
        type_=Vector(EMBEDDING_DIMENSION),
        existing_nullable=False,
        nullable=False,
    )


def downgrade() -> None:
    op.execute("DELETE FROM document_chunks")
    op.alter_column(
        "document_chunks",
        "embedding",
        existing_type=Vector(EMBEDDING_DIMENSION),
        type_=Vector(MOCK_EMBEDDING_DIMENSION),
        existing_nullable=False,
        nullable=False,
    )
