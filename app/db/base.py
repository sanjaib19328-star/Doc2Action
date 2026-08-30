import uuid
from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import DateTime, func, String, Boolean, ForeignKey, JSON, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    Provides common columns like created_at and updated_at.
    """

    id: Any
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(Base):
    """
    User account model for authentication and identity.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    specifications: Mapped[List["APISpecification"]] = relationship(
        "APISpecification", back_populates="owner", cascade="all, delete-orphan"
    )
    connections: Mapped[List["APIConnection"]] = relationship(
        "APIConnection", back_populates="owner", cascade="all, delete-orphan"
    )
    execution_logs: Mapped[List["APIExecutionLog"]] = relationship(
        "APIExecutionLog", back_populates="user", cascade="all, delete-orphan"
    )
    action_proposals: Mapped[List["APIActionProposal"]] = relationship(
        "APIActionProposal", back_populates="user", cascade="all, delete-orphan"
    )
    applications: Mapped[List["Application"]] = relationship(
        "Application", back_populates="owner", cascade="all, delete-orphan"
    )


class Application(Base):
    """
    Application entity acting as the top-level organizational boundary for user resources.
    """

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="applications")
    specifications: Mapped[List["APISpecification"]] = relationship(
        "APISpecification", back_populates="application"
    )
    connections: Mapped[List["APIConnection"]] = relationship(
        "APIConnection", back_populates="application"
    )
    execution_logs: Mapped[List["APIExecutionLog"]] = relationship(
        "APIExecutionLog", back_populates="application"
    )
    action_proposals: Mapped[List["APIActionProposal"]] = relationship(
        "APIActionProposal", back_populates="application"
    )


class APISpecification(Base):
    """
    Stores metadata and raw specification of ingested OpenAPI/Swagger documents.
    """

    __tablename__ = "api_specifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    spec_version: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    servers: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)
    raw_spec: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    owner: Mapped["User"] = relationship("User", back_populates="specifications")
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="specifications")
    operations: Mapped[List["APIOperation"]] = relationship(
        "APIOperation", back_populates="specification", cascade="all, delete-orphan"
    )
    security_schemes: Mapped[List["APISecurityScheme"]] = relationship(
        "APISecurityScheme", back_populates="specification", cascade="all, delete-orphan"
    )
    connections: Mapped[List["APIConnection"]] = relationship(
        "APIConnection", back_populates="specification", cascade="all, delete-orphan"
    )


class APIOperation(Base):
    """
    Normalized HTTP operation extracted from an OpenAPI specification.
    """

    __tablename__ = "api_operations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    specification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)
    request_body: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    responses: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, defaultdict=dict) if False else mapped_column(JSON, nullable=False, default=dict)
    security: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)

    specification: Mapped["APISpecification"] = relationship("APISpecification", back_populates="operations")


class APISecurityScheme(Base):
    """
    Normalized security scheme extracted from an OpenAPI specification.
    """

    __tablename__ = "api_security_schemes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    specification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    scheme_in: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    scheme: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bearer_format: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    specification: Mapped["APISpecification"] = relationship("APISpecification", back_populates="security_schemes")


class APIConnection(Base):
    """
    Persistent API connection representing an active API specification connected to a user's account.
    """

    __tablename__ = "api_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    specification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_specifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auth_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    owner: Mapped["User"] = relationship("User", back_populates="connections")
    specification: Mapped["APISpecification"] = relationship("APISpecification", back_populates="connections")
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="connections")
    endpoints: Mapped[List["APIEndpoint"]] = relationship(
        "APIEndpoint", back_populates="connection", cascade="all, delete-orphan"
    )
    execution_logs: Mapped[List["APIExecutionLog"]] = relationship(
        "APIExecutionLog", back_populates="connection", cascade="all, delete-orphan"
    )
    action_proposals: Mapped[List["APIActionProposal"]] = relationship(
        "APIActionProposal", back_populates="connection", cascade="all, delete-orphan"
    )


class APIEndpoint(Base):
    """
    Persistent API catalog endpoint entity extracted from an API connection.
    """

    __tablename__ = "api_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)
    request_body_schema: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    response_schema: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    security_requirements: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)

    connection: Mapped["APIConnection"] = relationship("APIConnection", back_populates="endpoints")
    execution_logs: Mapped[List["APIExecutionLog"]] = relationship(
        "APIExecutionLog", back_populates="endpoint", cascade="all, delete-orphan"
    )
    action_proposals: Mapped[List["APIActionProposal"]] = relationship(
        "APIActionProposal", back_populates="endpoint", cascade="all, delete-orphan"
    )


class APIExecutionLog(Base):
    """
    Audit and record log for executed API requests.
    Stores masked request/response metadata, latency, status code, and execution status.
    """

    __tablename__ = "api_execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    request_headers: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    request_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    request_body: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # success, error, timeout, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="execution_logs")
    connection: Mapped["APIConnection"] = relationship("APIConnection", back_populates="execution_logs")
    endpoint: Mapped["APIEndpoint"] = relationship("APIEndpoint", back_populates="execution_logs")
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="execution_logs")


class APIActionProposal(Base):
    """
    Human-in-the-Loop Action Proposal entity.
    Stores proposed API actions prior to user confirmation and execution.
    """

    __tablename__ = "api_action_proposals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    intent_summary: Mapped[str] = mapped_column(Text, nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    path_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    query_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    headers: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    body: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, confirmed, rejected, executed, expired
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    execution_result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="action_proposals")
    connection: Mapped["APIConnection"] = relationship("APIConnection", back_populates="action_proposals")
    endpoint: Mapped["APIEndpoint"] = relationship("APIEndpoint", back_populates="action_proposals")
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="action_proposals")
