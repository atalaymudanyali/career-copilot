"""unique version number per application

Revision ID: 005
Revises: 004
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # Concurrent tailoring could have created duplicate numbers before this constraint
    # existed. Keep the oldest row of each duplicate and move the others to new numbers
    # after the application's current max, so the constraint can be added.
    duplicates = conn.execute(
        sa.text(
            "SELECT id, application_id FROM ("
            "  SELECT id, application_id, ROW_NUMBER() OVER ("
            "    PARTITION BY application_id, version_number ORDER BY id"
            "  ) AS rn FROM tailoring_versions"
            ") ranked WHERE rn > 1 ORDER BY id"
        )
    ).fetchall()
    for row in duplicates:
        conn.execute(
            sa.text(
                "UPDATE tailoring_versions SET version_number = ("
                "  SELECT MAX(version_number) + 1 FROM tailoring_versions"
                "  WHERE application_id = :app_id"
                ") WHERE id = :id"
            ),
            {"app_id": row.application_id, "id": row.id},
        )

    # The unique index also serves "versions of application X" lookups, which had no index.
    op.create_unique_constraint(
        "uq_tailoring_versions_application_version",
        "tailoring_versions",
        ["application_id", "version_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_tailoring_versions_application_version", "tailoring_versions", type_="unique"
    )
