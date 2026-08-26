"""create favorite_bullets table

Revision ID: 004
Revises: 003
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "favorite_bullets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "application_id",
            sa.Integer(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bullet_text", sa.Text(), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("relevance", sa.String(20), server_default="medium"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("application_id", "bullet_text"),
    )


def downgrade() -> None:
    op.drop_table("favorite_bullets")
