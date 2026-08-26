"""create tailoring_versions table

Revision ID: 003
Revises: 002
Create Date: 2026-08-26
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tailoring_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "application_id",
            sa.Integer(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("tailoring_result", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    conn = op.get_bind()
    apps_with_results = conn.execute(
        sa.text("SELECT id, tailoring_result FROM applications WHERE tailoring_result IS NOT NULL")
    )
    for app in apps_with_results:
        result = app.tailoring_result
        if isinstance(result, dict):
            result = json.dumps(result)
        conn.execute(
            sa.text(
                "INSERT INTO tailoring_versions "
                "(application_id, version_number, tailoring_result) "
                "VALUES (:app_id, 1, CAST(:result AS json))"
            ),
            {"app_id": app.id, "result": result},
        )


def downgrade() -> None:
    op.drop_table("tailoring_versions")
