"""create_action_proposals_table

Revision ID: 0005_create_action_proposals_table
Revises: 0004_create_execution_logs_table
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_create_action_proposals_table"
down_revision: Union[str, None] = "0004_create_execution_logs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_action_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intent_summary", sa.Text(), nullable=False),
        sa.Column("http_method", sa.String(length=10), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("path_params", sa.JSON(), nullable=False),
        sa.Column("query_params", sa.JSON(), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=False),
        sa.Column("body", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("execution_result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["api_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["endpoint_id"], ["api_endpoints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_action_proposals_id"), "api_action_proposals", ["id"], unique=False)
    op.create_index(op.f("ix_api_action_proposals_user_id"), "api_action_proposals", ["user_id"], unique=False)
    op.create_index(op.f("ix_api_action_proposals_connection_id"), "api_action_proposals", ["connection_id"], unique=False)
    op.create_index(op.f("ix_api_action_proposals_endpoint_id"), "api_action_proposals", ["endpoint_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_action_proposals_endpoint_id"), table_name="api_action_proposals")
    op.drop_index(op.f("ix_api_action_proposals_connection_id"), table_name="api_action_proposals")
    op.drop_index(op.f("ix_api_action_proposals_user_id"), table_name="api_action_proposals")
    op.drop_index(op.f("ix_api_action_proposals_id"), table_name="api_action_proposals")
    op.drop_table("api_action_proposals")
