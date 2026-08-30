"""create_catalog_tables

Revision ID: 0003_create_catalog_tables
Revises: 0002_create_openapi_tables
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # api_connections table
    op.create_table(
        "api_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("auth_config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["specification_id"], ["api_specifications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_connections_id"), "api_connections", ["id"], unique=False)
    op.create_index(op.f("ix_api_connections_owner_id"), "api_connections", ["owner_id"], unique=False)
    op.create_index(op.f("ix_api_connections_specification_id"), "api_connections", ["specification_id"], unique=False)

    # api_endpoints table
    op.create_table(
        "api_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_id", sa.String(length=255), nullable=True),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("request_body_schema", sa.JSON(), nullable=True),
        sa.Column("response_schema", sa.JSON(), nullable=False),
        sa.Column("security_requirements", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["api_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_endpoints_id"), "api_endpoints", ["id"], unique=False)
    op.create_index(op.f("ix_api_endpoints_connection_id"), "api_endpoints", ["connection_id"], unique=False)
    op.create_index(op.f("ix_api_endpoints_operation_id"), "api_endpoints", ["operation_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_endpoints_operation_id"), table_name="api_endpoints")
    op.drop_index(op.f("ix_api_endpoints_connection_id"), table_name="api_endpoints")
    op.drop_index(op.f("ix_api_endpoints_id"), table_name="api_endpoints")
    op.drop_table("api_endpoints")

    op.drop_index(op.f("ix_api_connections_specification_id"), table_name="api_connections")
    op.drop_index(op.f("ix_api_connections_owner_id"), table_name="api_connections")
    op.drop_index(op.f("ix_api_connections_id"), table_name="api_connections")
    op.drop_table("api_connections")
