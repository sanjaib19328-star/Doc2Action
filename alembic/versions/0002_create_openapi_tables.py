"""create_openapi_tables

Revision ID: 0002_create_openapi_tables
Revises: 0001_create_users_table
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # api_specifications table
    op.create_table(
        "api_specifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="1.0.0"),
        sa.Column("spec_version", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("servers", sa.JSON(), nullable=False),
        sa.Column("raw_spec", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_specifications_id"), "api_specifications", ["id"], unique=False)
    op.create_index(op.f("ix_api_specifications_owner_id"), "api_specifications", ["owner_id"], unique=False)

    # api_operations table
    op.create_table(
        "api_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_id", sa.String(length=255), nullable=True),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("request_body", sa.JSON(), nullable=True),
        sa.Column("responses", sa.JSON(), nullable=False),
        sa.Column("security", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["specification_id"], ["api_specifications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_operations_id"), "api_operations", ["id"], unique=False)
    op.create_index(op.f("ix_api_operations_specification_id"), "api_operations", ["specification_id"], unique=False)
    op.create_index(op.f("ix_api_operations_operation_id"), "api_operations", ["operation_id"], unique=False)

    # api_security_schemes table
    op.create_table(
        "api_security_schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheme_name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("scheme_in", sa.String(length=50), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("scheme", sa.String(length=50), nullable=True),
        sa.Column("bearer_format", sa.String(length=100), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["specification_id"], ["api_specifications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_security_schemes_id"), "api_security_schemes", ["id"], unique=False)
    op.create_index(op.f("ix_api_security_schemes_specification_id"), "api_security_schemes", ["specification_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_security_schemes_specification_id"), table_name="api_security_schemes")
    op.drop_index(op.f("ix_api_security_schemes_id"), table_name="api_security_schemes")
    op.drop_table("api_security_schemes")

    op.drop_index(op.f("ix_api_operations_operation_id"), table_name="api_operations")
    op.drop_index(op.f("ix_api_operations_specification_id"), table_name="api_operations")
    op.drop_index(op.f("ix_api_operations_id"), table_name="api_operations")
    op.drop_table("api_operations")

    op.drop_index(op.f("ix_api_specifications_owner_id"), table_name="api_specifications")
    op.drop_index(op.f("ix_api_specifications_id"), table_name="api_specifications")
    op.drop_table("api_specifications")
