"""Database models and persistence layer for FEMA USAR MCP.

Provides SQLAlchemy models, database operations, and data management
for USAR operations with high availability and disaster recovery.
"""

import logging
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()
metadata = MetaData()


class TaskForceModel(Base):
    """Task force database model."""

    __tablename__ = "task_forces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_force_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    home_location = Column(String(255), nullable=False)
    operational_status = Column(String(50), nullable=False, default="ready")
    personnel_count = Column(Integer, nullable=False, default=0)
    equipment_ready_count = Column(Integer, nullable=False, default=0)
    training_compliance = Column(Float, nullable=False, default=100.0)
    last_deployment = Column(DateTime(timezone=True))
    last_training = Column(DateTime(timezone=True))
    certifications = Column(ARRAY(String), default=[])
    contact_info = Column(JSONB)
    configuration = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    deployments = relationship("DeploymentModel", back_populates="task_force")
    personnel = relationship("PersonnelModel", back_populates="task_force")
    equipment = relationship("EquipmentModel", back_populates="task_force")

    __table_args__ = (
        Index("ix_task_forces_status", "operational_status"),
        Index("ix_task_forces_location", "home_location"),
        CheckConstraint("personnel_count >= 0"),
        CheckConstraint("equipment_ready_count >= 0"),
        CheckConstraint("training_compliance >= 0 AND training_compliance <= 100"),
    )


class DeploymentModel(Base):
    """Deployment database model."""

    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(String(50), unique=True, nullable=False, index=True)
    task_force_id = Column(
        String(20), ForeignKey("task_forces.task_force_id"), nullable=False
    )
    incident_id = Column(String(50), nullable=False, index=True)
    deployment_status = Column(String(50), nullable=False, default="pending")
    priority = Column(String(20), nullable=False, default="medium")
    deployment_location = Column(JSONB)
    deployment_time = Column(DateTime(timezone=True), nullable=False)
    estimated_duration = Column(Integer)  # hours
    actual_duration = Column(Integer)  # hours
    personnel_deployed = Column(Integer, default=0)
    equipment_deployed = Column(JSONB)
    mission_objectives = Column(ARRAY(String))
    operational_periods = Column(JSONB)
    weather_conditions = Column(JSONB)
    safety_incidents = Column(JSONB)
    resources_used = Column(JSONB)
    lessons_learned = Column(Text)
    after_action_report = Column(Text)
    deployment_costs = Column(Float)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    task_force = relationship("TaskForceModel", back_populates="deployments")
    operations = relationship("OperationModel", back_populates="deployment")
    reports = relationship("ReportModel", back_populates="deployment")

    __table_args__ = (
        Index("ix_deployments_incident", "incident_id"),
        Index("ix_deployments_status", "deployment_status"),
        Index("ix_deployments_time", "deployment_time"),
        CheckConstraint("personnel_deployed >= 0"),
        CheckConstraint("estimated_duration > 0"),
        CheckConstraint("deployment_costs >= 0"),
    )


class PersonnelModel(Base):
    """Personnel database model."""

    __tablename__ = "personnel"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(String(50), unique=True, nullable=False, index=True)
    task_force_id = Column(
        String(20), ForeignKey("task_forces.task_force_id"), nullable=False
    )
    full_name = Column(String(255), nullable=False)
    position_title = Column(String(100), nullable=False)
    functional_group = Column(String(50), nullable=False)
    usar_role = Column(String(50), nullable=False)
    security_clearance = Column(String(30), nullable=False, default="official_use_only")
    badge_number = Column(String(50))
    agency = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    emergency_contact = Column(JSONB)
    certifications = Column(ARRAY(String))
    qualifications = Column(ARRAY(String))
    training_records = Column(JSONB)
    medical_status = Column(String(30), default="cleared")
    deployment_status = Column(String(30), default="available")
    current_location = Column(JSONB)
    contact_info = Column(JSONB)
    performance_metrics = Column(JSONB)
    last_deployment = Column(DateTime(timezone=True))
    last_training = Column(DateTime(timezone=True))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    task_force = relationship("TaskForceModel", back_populates="personnel")

    __table_args__ = (
        Index("ix_personnel_role", "usar_role"),
        Index("ix_personnel_group", "functional_group"),
        Index("ix_personnel_status", "deployment_status"),
        Index("ix_personnel_clearance", "security_clearance"),
        UniqueConstraint("badge_number", "agency", name="uq_personnel_badge_agency"),
    )


class EquipmentModel(Base):
    """Equipment database model."""

    __tablename__ = "equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(String(50), unique=True, nullable=False, index=True)
    task_force_id = Column(
        String(20), ForeignKey("task_forces.task_force_id"), nullable=False
    )
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50))
    serial_number = Column(String(100))
    manufacturer = Column(String(100))
    model = Column(String(100))
    acquisition_date = Column(DateTime(timezone=True))
    acquisition_cost = Column(Float)
    current_status = Column(String(30), nullable=False, default="operational")
    condition = Column(String(30), nullable=False, default="good")
    location = Column(String(255))
    current_coordinates = Column(JSONB)
    assigned_to = Column(String(255))
    maintenance_schedule = Column(JSONB)
    maintenance_history = Column(JSONB)
    last_inspection = Column(DateTime(timezone=True))
    next_inspection = Column(DateTime(timezone=True))
    certifications_required = Column(ARRAY(String))
    specifications = Column(JSONB)
    usage_metrics = Column(JSONB)
    replacement_date = Column(DateTime(timezone=True))
    disposal_date = Column(DateTime(timezone=True))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    task_force = relationship("TaskForceModel", back_populates="equipment")

    __table_args__ = (
        Index("ix_equipment_category", "category"),
        Index("ix_equipment_status", "current_status"),
        Index("ix_equipment_condition", "condition"),
        Index("ix_equipment_location", "location"),
        Index("ix_equipment_inspection", "next_inspection"),
        CheckConstraint("acquisition_cost >= 0"),
    )


class OperationModel(Base):
    """Operation database model."""

    __tablename__ = "operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id = Column(String(50), unique=True, nullable=False, index=True)
    deployment_id = Column(
        String(50), ForeignKey("deployments.deployment_id"), nullable=False
    )
    operation_type = Column(String(50), nullable=False)  # search, rescue, medical, etc.
    operation_status = Column(String(30), nullable=False, default="active")
    priority = Column(String(20), nullable=False, default="medium")
    location = Column(JSONB)
    objectives = Column(ARRAY(String))
    assigned_personnel = Column(ARRAY(String))
    assigned_equipment = Column(ARRAY(String))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    progress_percentage = Column(Float, default=0.0)
    resources_consumed = Column(JSONB)
    safety_notes = Column(Text)
    environmental_conditions = Column(JSONB)
    results = Column(JSONB)
    lessons_learned = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    deployment = relationship("DeploymentModel", back_populates="operations")

    __table_args__ = (
        Index("ix_operations_type", "operation_type"),
        Index("ix_operations_status", "operation_status"),
        Index("ix_operations_start_time", "start_time"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100"),
        CheckConstraint("duration_minutes >= 0"),
    )


class ReportModel(Base):
    """Report database model."""

    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(String(50), unique=True, nullable=False, index=True)
    deployment_id = Column(
        String(50), ForeignKey("deployments.deployment_id"), nullable=False
    )
    report_type = Column(String(50), nullable=False)  # sitrep, ics, after_action
    form_type = Column(String(20))  # ICS-201, ICS-204, etc.
    report_title = Column(String(255), nullable=False)
    operational_period = Column(Integer)
    reporting_time = Column(DateTime(timezone=True), nullable=False)
    submitted_by = Column(String(255), nullable=False)
    reviewed_by = Column(String(255))
    approved_by = Column(String(255))
    report_data = Column(JSONB, nullable=False)
    attachments = Column(ARRAY(String))
    distribution_list = Column(ARRAY(String))
    classification = Column(String(30), default="official_use_only")
    status = Column(String(30), default="draft")
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    deployment = relationship("DeploymentModel", back_populates="reports")

    __table_args__ = (
        Index("ix_reports_type", "report_type"),
        Index("ix_reports_form_type", "form_type"),
        Index("ix_reports_status", "status"),
        Index("ix_reports_time", "reporting_time"),
        Index("ix_reports_classification", "classification"),
    )


class AuditLogModel(Base):
    """Audit log database model."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_id = Column(String(50), unique=True, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    user_id = Column(String(50))
    resource_type = Column(String(50))
    resource_id = Column(String(50))
    action = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_method = Column(String(10))
    request_url = Column(String(500))
    response_status = Column(Integer)
    event_data = Column(JSONB)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    session_id = Column(String(100))
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_logs_event_type", "event_type"),
        Index("ix_audit_logs_user", "user_id"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_success", "success"),
        Index("ix_audit_logs_ip", "ip_address"),
    )


class DatabaseManager:
    """Database connection and session management."""

    def __init__(self, database_url: str, echo: bool = False):
        """Initialize database manager.

        Args:
            database_url: Database connection URL
            echo: Enable SQL logging
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=echo,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_all_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Created all database tables")

    def get_session(self) -> Session:
        """Get database session.

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()

    def run_migrations(self, alembic_cfg_path: str):
        """Run database migrations.

        Args:
            alembic_cfg_path: Path to alembic configuration file
        """
        alembic_cfg = Config(alembic_cfg_path)
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed")


class TaskForceRepository:
    """Repository for task force operations."""

    def __init__(self, session: Session):
        """Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    def create_task_force(self, task_force_data: dict[str, Any]) -> TaskForceModel:
        """Create new task force record.

        Args:
            task_force_data: Task force data

        Returns:
            Created task force model
        """
        task_force = TaskForceModel(**task_force_data)
        self.session.add(task_force)
        self.session.commit()
        self.session.refresh(task_force)

        logger.info(f"Created task force: {task_force.task_force_id}")
        return task_force

    def get_task_force(self, task_force_id: str) -> TaskForceModel | None:
        """Get task force by ID.

        Args:
            task_force_id: Task force identifier

        Returns:
            Task force model or None
        """
        return (
            self.session.query(TaskForceModel)
            .filter(TaskForceModel.task_force_id == task_force_id)
            .first()
        )

    def update_task_force(self, task_force_id: str, updates: dict[str, Any]) -> bool:
        """Update task force record.

        Args:
            task_force_id: Task force identifier
            updates: Fields to update

        Returns:
            True if update successful
        """
        result = (
            self.session.query(TaskForceModel)
            .filter(TaskForceModel.task_force_id == task_force_id)
            .update(updates)
        )

        if result > 0:
            self.session.commit()
            logger.info(f"Updated task force: {task_force_id}")
            return True
        return False

    def list_active_task_forces(self) -> list[TaskForceModel]:
        """List all active task forces.

        Returns:
            List of active task forces
        """
        return (
            self.session.query(TaskForceModel)
            .filter(TaskForceModel.operational_status.in_(["ready", "deployed"]))
            .all()
        )


class DeploymentRepository:
    """Repository for deployment operations."""

    def __init__(self, session: Session):
        """Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    def create_deployment(self, deployment_data: dict[str, Any]) -> DeploymentModel:
        """Create new deployment record.

        Args:
            deployment_data: Deployment data

        Returns:
            Created deployment model
        """
        deployment = DeploymentModel(**deployment_data)
        self.session.add(deployment)
        self.session.commit()
        self.session.refresh(deployment)

        logger.info(f"Created deployment: {deployment.deployment_id}")
        return deployment

    def get_active_deployments(
        self, task_force_id: str | None = None
    ) -> list[DeploymentModel]:
        """Get active deployments.

        Args:
            task_force_id: Filter by task force (optional)

        Returns:
            List of active deployments
        """
        query = self.session.query(DeploymentModel).filter(
            DeploymentModel.deployment_status.in_(["active", "pending"])
        )

        if task_force_id:
            query = query.filter(DeploymentModel.task_force_id == task_force_id)

        return query.all()

    def complete_deployment(
        self, deployment_id: str, completion_data: dict[str, Any]
    ) -> bool:
        """Mark deployment as completed.

        Args:
            deployment_id: Deployment identifier
            completion_data: Completion data

        Returns:
            True if update successful
        """
        updates = {
            "deployment_status": "completed",
            "completed_at": datetime.now(UTC),
            **completion_data,
        }

        result = (
            self.session.query(DeploymentModel)
            .filter(DeploymentModel.deployment_id == deployment_id)
            .update(updates)
        )

        if result > 0:
            self.session.commit()
            logger.info(f"Completed deployment: {deployment_id}")
            return True
        return False


class AuditRepository:
    """Repository for audit log operations."""

    def __init__(self, session: Session):
        """Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    def create_audit_log(self, audit_data: dict[str, Any]) -> AuditLogModel:
        """Create new audit log entry.

        Args:
            audit_data: Audit log data

        Returns:
            Created audit log model
        """
        audit_log = AuditLogModel(
            log_id=f"audit_{secrets.token_urlsafe(8)}", **audit_data
        )
        self.session.add(audit_log)
        self.session.commit()

        return audit_log

    def get_audit_logs(
        self,
        user_id: str | None = None,
        event_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLogModel]:
        """Get audit logs with filters.

        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum results

        Returns:
            List of audit log entries
        """
        query = self.session.query(AuditLogModel)

        if user_id:
            query = query.filter(AuditLogModel.user_id == user_id)
        if event_type:
            query = query.filter(AuditLogModel.event_type == event_type)
        if start_time:
            query = query.filter(AuditLogModel.timestamp >= start_time)
        if end_time:
            query = query.filter(AuditLogModel.timestamp <= end_time)

        return query.order_by(AuditLogModel.timestamp.desc()).limit(limit).all()


# Event listeners for automatic audit logging
@event.listens_for(TaskForceModel, "after_insert")
def log_task_force_creation(mapper, connection, target):
    """Log task force creation."""
    # In a real implementation, this would create an audit log entry
    logger.info(f"Task force created: {target.task_force_id}")


@event.listens_for(DeploymentModel, "after_insert")
def log_deployment_creation(mapper, connection, target):
    """Log deployment creation."""
    logger.info(f"Deployment created: {target.deployment_id}")


@event.listens_for(DeploymentModel, "after_update")
def log_deployment_update(mapper, connection, target):
    """Log deployment updates."""
    logger.info(f"Deployment updated: {target.deployment_id}")
