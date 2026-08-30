"""create_execution_logs_table

Revision ID: 0004_create_execution_logs_table
Revises: 0003_create_catalog_tables
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_execution_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("http_method", sa.String(length=10), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("request_headers", sa.JSON(), nullable=False),
        sa.Column("request_params", sa.JSON(), nullable=False),
        sa.Column("request_body", sa.JSON(), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["api_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["endpoint_id"], ["api_endpoints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_execution_logs_id"), "api_execution_logs", ["id"], unique=False)
    op.create_index(op.f("ix_api_execution_logs_user_id"), "api_execution_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_api_execution_logs_connection_id"), "api_execution_logs", ["connection_id"], unique=False)
    op.create_index(op.f("ix_api_execution_logs_endpoint_id"), "api_execution_logs", ["endpoint_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_execution_logs_endpoint_id"), table_name="api_execution_logs")
    op.drop_index(op.f("ix_api_execution_logs_connection_id"), table_name="api_execution_logs")
    op.drop_index(op.f("ix_api_execution_logs_user_id"), table_name="api_execution_logs")
    op.drop_index(op.f("ix_api_execution_logs_id"), table_name="api_execution_logs")
    op.drop_table("api_execution_logs")
