"""create_applications_table_and_columns

Revision ID: 0006_create_applications_table
Revises: 0005
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_create_applications_table"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create applications table
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_applications_id"), "applications", ["id"], unique=False)
    op.create_index(op.f("ix_applications_owner_id"), "applications", ["owner_id"], unique=False)

    # 2. Add application_id column to api_specifications
    op.add_column("api_specifications", sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_api_specifications_application_id", "api_specifications", "applications", ["application_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_api_specifications_application_id"), "api_specifications", ["application_id"], unique=False)

    # 3. Add application_id column to api_connections
    op.add_column("api_connections", sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_api_connections_application_id", "api_connections", "applications", ["application_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_api_connections_application_id"), "api_connections", ["application_id"], unique=False)

    # 4. Add application_id column to api_execution_logs
    op.add_column("api_execution_logs", sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_api_execution_logs_application_id", "api_execution_logs", "applications", ["application_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_api_execution_logs_application_id"), "api_execution_logs", ["application_id"], unique=False)

    # 5. Add application_id column to api_action_proposals
    op.add_column("api_action_proposals", sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_api_action_proposals_application_id", "api_action_proposals", "applications", ["application_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_api_action_proposals_application_id"), "api_action_proposals", ["application_id"], unique=False)


def downgrade() -> None:
    op.drop_constraint("fk_api_action_proposals_application_id", "api_action_proposals", type_="foreignkey")
    op.drop_index(op.f("ix_api_action_proposals_application_id"), table_name="api_action_proposals")
    op.drop_column("api_action_proposals", "application_id")

    op.drop_constraint("fk_api_execution_logs_application_id", "api_execution_logs", type_="foreignkey")
    op.drop_index(op.f("ix_api_execution_logs_application_id"), table_name="api_execution_logs")
    op.drop_column("api_execution_logs", "application_id")

    op.drop_constraint("fk_api_connections_application_id", "api_connections", type_="foreignkey")
    op.drop_index(op.f("ix_api_connections_application_id"), table_name="api_connections")
    op.drop_column("api_connections", "application_id")

    op.drop_constraint("fk_api_specifications_application_id", "api_specifications", type_="foreignkey")
    op.drop_index(op.f("ix_api_specifications_application_id"), table_name="api_specifications")
    op.drop_column("api_specifications", "application_id")

    op.drop_index(op.f("ix_applications_owner_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_id"), table_name="applications")
    op.drop_table("applications")
