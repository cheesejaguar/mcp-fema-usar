"""Compliance reporting and audit trail system for FEMA USAR MCP.

Provides comprehensive audit logging, compliance reporting, and regulatory
adherence for federal USAR operations.
"""

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types for FEMA compliance."""

    # Authentication events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_LOGIN_FAILED = "user_login_failed"
    USER_PASSWORD_CHANGE = "user_password_change"
    USER_PRIVILEGE_CHANGE = "user_privilege_change"

    # Data access events
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"

    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    SYSTEM_ERROR = "system_error"
    SYSTEM_BACKUP = "system_backup"

    # USAR operational events
    DEPLOYMENT_CREATE = "deployment_create"
    DEPLOYMENT_MODIFY = "deployment_modify"
    DEPLOYMENT_COMPLETE = "deployment_complete"
    MISSION_ASSIGN = "mission_assign"
    PERSONNEL_DEPLOY = "personnel_deploy"
    EQUIPMENT_ASSIGN = "equipment_assign"
    SAFETY_INCIDENT = "safety_incident"

    # Compliance events
    COMPLIANCE_REPORT_GENERATE = "compliance_report_generate"
    AUDIT_LOG_ACCESS = "audit_log_access"
    PRIVACY_DATA_ACCESS = "privacy_data_access"
    RETENTION_POLICY_APPLY = "retention_policy_apply"


class ComplianceFramework(Enum):
    """Compliance frameworks and regulations."""

    FEMA_DIRECTIVE = "fema_directive"
    NIMS_STANDARD = "nims_standard"
    ICS_STANDARD = "ics_standard"
    FISMA = "fisma"
    PRIVACY_ACT = "privacy_act"
    FOIA = "foia"
    STAFFORD_ACT = "stafford_act"
    ROBERT_T_STAFFORD_ACT = "robert_t_stafford_act"


class AuditSeverity(Enum):
    """Audit event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Comprehensive audit event model."""

    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: str | None
    session_id: str | None
    ip_address: str | None
    user_agent: str | None
    resource_type: str | None
    resource_id: str | None
    action: str
    description: str
    severity: AuditSeverity
    compliance_frameworks: list[ComplianceFramework]
    data_classification: str
    retention_period_days: int
    event_data: dict[str, Any]
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    success: bool
    error_message: str | None
    geolocation: dict[str, str] | None
    device_info: dict[str, str] | None
    hash_signature: str | None

    def calculate_hash(self, secret_key: str) -> str:
        """Calculate hash signature for tamper detection."""
        hash_data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "success": self.success,
        }

        hash_string = json.dumps(hash_data, sort_keys=True) + secret_key
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "description": self.description,
            "severity": self.severity.value,
            "compliance_frameworks": [f.value for f in self.compliance_frameworks],
            "data_classification": self.data_classification,
            "retention_period_days": self.retention_period_days,
            "event_data": self.event_data,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "success": self.success,
            "error_message": self.error_message,
            "geolocation": self.geolocation,
            "device_info": self.device_info,
            "hash_signature": self.hash_signature,
        }


class ComplianceReport:
    """Compliance report model."""

    def __init__(
        self,
        report_id: str,
        report_type: str,
        framework: ComplianceFramework,
        period_start: datetime,
        period_end: datetime,
        generated_by: str,
    ):
        self.report_id = report_id
        self.report_type = report_type
        self.framework = framework
        self.period_start = period_start
        self.period_end = period_end
        self.generated_by = generated_by
        self.generated_at = datetime.now(UTC)
        self.findings: list[dict[str, Any]] = []
        self.metrics: dict[str, Any] = {}
        self.recommendations: list[str] = []
        self.compliance_score: float | None = None

    def add_finding(self, finding: dict[str, Any]):
        """Add compliance finding to report."""
        self.findings.append(
            {
                **finding,
                "finding_id": str(uuid.uuid4()),
                "identified_at": datetime.now(UTC).isoformat(),
            }
        )

    def calculate_compliance_score(self) -> float:
        """Calculate overall compliance score."""
        if not self.findings:
            return 100.0

        total_findings = len(self.findings)
        critical_findings = sum(
            1 for f in self.findings if f.get("severity") == "critical"
        )
        high_findings = sum(1 for f in self.findings if f.get("severity") == "high")

        # Score calculation based on findings severity
        score = 100.0
        score -= critical_findings * 10  # -10 points per critical
        score -= high_findings * 5  # -5 points per high
        score -= (
            total_findings - critical_findings - high_findings
        ) * 2  # -2 points per other

        self.compliance_score = max(0.0, score)
        return self.compliance_score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "framework": self.framework.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "generated_by": self.generated_by,
            "generated_at": self.generated_at.isoformat(),
            "findings": self.findings,
            "metrics": self.metrics,
            "recommendations": self.recommendations,
            "compliance_score": self.compliance_score,
        }


class AuditLogger:
    """Secure audit logging system."""

    def __init__(
        self,
        database_url: str,
        encryption_key: bytes | None = None,
        s3_bucket: str | None = None,
    ):
        """Initialize audit logger.

        Args:
            database_url: Database connection URL
            encryption_key: Encryption key for sensitive data
            s3_bucket: S3 bucket for secure storage
        """
        self.database_url = database_url
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.s3_bucket = s3_bucket
        self.fernet = Fernet(self.encryption_key)
        self.secret_key = os.getenv("AUDIT_SECRET_KEY", "default_secret")

        # Database setup
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # S3 client
        self.s3_client = boto3.client("s3") if s3_bucket else None

        # Cache for performance
        self._event_cache: list[AuditEvent] = []
        self._cache_size_limit = 100

    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key if none provided."""
        return Fernet.generate_key()

    async def log_event(self, event: AuditEvent):
        """Log audit event securely.

        Args:
            event: Audit event to log
        """
        try:
            # Calculate hash signature
            event.hash_signature = event.calculate_hash(self.secret_key)

            # Encrypt sensitive data
            if event.event_data and self._contains_sensitive_data(event.event_data):
                event.event_data = self._encrypt_data(event.event_data)

            # Store in database
            await self._store_event_db(event)

            # Store in S3 for long-term retention
            if self.s3_client:
                await self._store_event_s3(event)

            # Cache for quick access
            self._event_cache.append(event)
            if len(self._event_cache) > self._cache_size_limit:
                self._event_cache.pop(0)

            logger.debug(f"Audit event logged: {event.event_id}")

        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            # Critical: audit logging failure should be escalated
            raise

    async def _store_event_db(self, event: AuditEvent):
        """Store event in database."""
        session = self.SessionLocal()
        try:
            # Insert audit event
            insert_sql = text(
                """
                INSERT INTO audit_events (
                    event_id, event_type, timestamp, user_id, session_id,
                    ip_address, user_agent, resource_type, resource_id, action,
                    description, severity, compliance_frameworks, data_classification,
                    retention_period_days, event_data, before_state, after_state,
                    success, error_message, geolocation, device_info, hash_signature
                ) VALUES (
                    :event_id, :event_type, :timestamp, :user_id, :session_id,
                    :ip_address, :user_agent, :resource_type, :resource_id, :action,
                    :description, :severity, :compliance_frameworks, :data_classification,
                    :retention_period_days, :event_data, :before_state, :after_state,
                    :success, :error_message, :geolocation, :device_info, :hash_signature
                )
            """
            )

            session.execute(
                insert_sql,
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp,
                    "user_id": event.user_id,
                    "session_id": event.session_id,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id,
                    "action": event.action,
                    "description": event.description,
                    "severity": event.severity.value,
                    "compliance_frameworks": json.dumps(
                        [f.value for f in event.compliance_frameworks]
                    ),
                    "data_classification": event.data_classification,
                    "retention_period_days": event.retention_period_days,
                    "event_data": (
                        json.dumps(event.event_data) if event.event_data else None
                    ),
                    "before_state": (
                        json.dumps(event.before_state) if event.before_state else None
                    ),
                    "after_state": (
                        json.dumps(event.after_state) if event.after_state else None
                    ),
                    "success": event.success,
                    "error_message": event.error_message,
                    "geolocation": (
                        json.dumps(event.geolocation) if event.geolocation else None
                    ),
                    "device_info": (
                        json.dumps(event.device_info) if event.device_info else None
                    ),
                    "hash_signature": event.hash_signature,
                },
            )

            session.commit()

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def _store_event_s3(self, event: AuditEvent):
        """Store event in S3 for long-term retention."""
        if not self.s3_client:
            return

        try:
            # Create S3 key with partitioning by date
            date_partition = event.timestamp.strftime("%Y/%m/%d")
            s3_key = f"audit-logs/{date_partition}/{event.event_id}.json"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json.dumps(event.to_dict(), indent=2),
                ServerSideEncryption="AES256",
                Metadata={
                    "event-type": event.event_type.value,
                    "severity": event.severity.value,
                    "timestamp": event.timestamp.isoformat(),
                },
            )

        except ClientError as e:
            logger.warning(f"Failed to store audit event in S3: {str(e)}")

    def _contains_sensitive_data(self, data: dict[str, Any]) -> bool:
        """Check if data contains sensitive information."""
        sensitive_keys = {
            "password",
            "ssn",
            "social_security",
            "credit_card",
            "bank_account",
            "pii",
            "personal_info",
            "medical_info",
            "secret",
            "key",
            "token",
        }

        def check_keys(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if key.lower() in sensitive_keys:
                        return True
                    if isinstance(value, dict | list):
                        if check_keys(value, full_key):
                            return True
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict | list):
                        if check_keys(item, f"{prefix}[{i}]"):
                            return True
            return False

        return check_keys(data)

    def _encrypt_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Encrypt sensitive data fields."""
        encrypted_data = data.copy()

        def encrypt_sensitive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in {
                        "password",
                        "ssn",
                        "social_security",
                        "secret",
                        "token",
                    }:
                        if isinstance(value, str):
                            obj[key] = self.fernet.encrypt(value.encode()).decode()
                    elif isinstance(value, dict | list):
                        encrypt_sensitive(value)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict | list):
                        encrypt_sensitive(item)

        encrypt_sensitive(encrypted_data)
        return encrypted_data

    async def query_events(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        event_types: list[AuditEventType] | None = None,
        user_id: str | None = None,
        resource_type: str | None = None,
        severity: AuditSeverity | None = None,
        limit: int = 1000,
    ) -> list[AuditEvent]:
        """Query audit events with filters.

        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            event_types: Filter by event types
            user_id: Filter by user ID
            resource_type: Filter by resource type
            severity: Filter by severity
            limit: Maximum results

        Returns:
            List of matching audit events
        """
        session = self.SessionLocal()
        try:
            # Build query
            sql = "SELECT * FROM audit_events WHERE 1=1"
            params = {}

            if start_time:
                sql += " AND timestamp >= :start_time"
                params["start_time"] = start_time

            if end_time:
                sql += " AND timestamp <= :end_time"
                params["end_time"] = end_time

            if event_types:
                sql += " AND event_type IN :event_types"
                params["event_types"] = tuple(et.value for et in event_types)

            if user_id:
                sql += " AND user_id = :user_id"
                params["user_id"] = user_id

            if resource_type:
                sql += " AND resource_type = :resource_type"
                params["resource_type"] = resource_type

            if severity:
                sql += " AND severity = :severity"
                params["severity"] = severity.value

            sql += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit

            result = session.execute(text(sql), params)
            rows = result.fetchall()

            # Convert to AuditEvent objects
            events = []
            for row in rows:
                event = AuditEvent(
                    event_id=row.event_id,
                    event_type=AuditEventType(row.event_type),
                    timestamp=row.timestamp,
                    user_id=row.user_id,
                    session_id=row.session_id,
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    action=row.action,
                    description=row.description,
                    severity=AuditSeverity(row.severity),
                    compliance_frameworks=[
                        ComplianceFramework(f)
                        for f in json.loads(row.compliance_frameworks or "[]")
                    ],
                    data_classification=row.data_classification,
                    retention_period_days=row.retention_period_days,
                    event_data=json.loads(row.event_data) if row.event_data else {},
                    before_state=(
                        json.loads(row.before_state) if row.before_state else None
                    ),
                    after_state=(
                        json.loads(row.after_state) if row.after_state else None
                    ),
                    success=row.success,
                    error_message=row.error_message,
                    geolocation=(
                        json.loads(row.geolocation) if row.geolocation else None
                    ),
                    device_info=(
                        json.loads(row.device_info) if row.device_info else None
                    ),
                    hash_signature=row.hash_signature,
                )
                events.append(event)

            return events

        finally:
            session.close()


class ComplianceReporter:
    """Compliance reporting system."""

    def __init__(self, audit_logger: AuditLogger):
        """Initialize compliance reporter.

        Args:
            audit_logger: Audit logger instance
        """
        self.audit_logger = audit_logger

    async def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        period_start: datetime,
        period_end: datetime,
        generated_by: str,
    ) -> ComplianceReport:
        """Generate comprehensive compliance report.

        Args:
            framework: Compliance framework
            period_start: Report period start
            period_end: Report period end
            generated_by: Report generator ID

        Returns:
            Compliance report
        """
        report_id = f"compliance_{framework.value}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        report = ComplianceReport(
            report_id=report_id,
            report_type=f"{framework.value}_compliance",
            framework=framework,
            period_start=period_start,
            period_end=period_end,
            generated_by=generated_by,
        )

        # Query relevant audit events
        events = await self.audit_logger.query_events(
            start_time=period_start, end_time=period_end, limit=10000
        )

        # Generate framework-specific findings
        if framework == ComplianceFramework.FEMA_DIRECTIVE:
            await self._analyze_fema_compliance(report, events)
        elif framework == ComplianceFramework.FISMA:
            await self._analyze_fisma_compliance(report, events)
        elif framework == ComplianceFramework.PRIVACY_ACT:
            await self._analyze_privacy_compliance(report, events)

        # Calculate compliance metrics
        report.metrics = self._calculate_compliance_metrics(events)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report.findings)

        # Calculate compliance score
        report.calculate_compliance_score()

        # Log report generation
        await self.audit_logger.log_event(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.COMPLIANCE_REPORT_GENERATE,
                timestamp=datetime.now(UTC),
                user_id=generated_by,
                session_id=None,
                ip_address=None,
                user_agent=None,
                resource_type="compliance_report",
                resource_id=report_id,
                action="generate",
                description=f"Generated {framework.value} compliance report",
                severity=AuditSeverity.INFO,
                compliance_frameworks=[framework],
                data_classification="official_use_only",
                retention_period_days=2555,  # 7 years
                event_data={
                    "report_type": report.report_type,
                    "period_days": (period_end - period_start).days,
                },
                before_state=None,
                after_state=None,
                success=True,
                error_message=None,
                geolocation=None,
                device_info=None,
                hash_signature=None,
            )
        )

        return report

    async def _analyze_fema_compliance(
        self, report: ComplianceReport, events: list[AuditEvent]
    ):
        """Analyze FEMA directive compliance."""
        # Check for required audit events
        required_events = {
            AuditEventType.USER_LOGIN,
            AuditEventType.DATA_ACCESS,
            AuditEventType.DEPLOYMENT_CREATE,
        }

        found_events = {event.event_type for event in events}
        missing_events = required_events - found_events

        for missing_event in missing_events:
            report.add_finding(
                {
                    "type": "missing_audit_events",
                    "severity": "medium",
                    "description": f"No {missing_event.value} events found in period",
                    "requirement": "FEMA Directive requires comprehensive audit logging",
                }
            )

        # Check for security incidents
        security_events = [
            e for e in events if e.event_type == AuditEventType.USER_LOGIN_FAILED
        ]
        if len(security_events) > 10:
            report.add_finding(
                {
                    "type": "excessive_failed_logins",
                    "severity": "high",
                    "description": f"{len(security_events)} failed login attempts detected",
                    "requirement": "FEMA security policy requires monitoring of authentication failures",
                }
            )

    async def _analyze_fisma_compliance(
        self, report: ComplianceReport, events: list[AuditEvent]
    ):
        """Analyze FISMA compliance."""
        # Check for configuration changes without approval
        config_changes = [
            e for e in events if e.event_type == AuditEventType.SYSTEM_CONFIG_CHANGE
        ]

        for change_event in config_changes:
            if not change_event.event_data.get("approval_id"):
                report.add_finding(
                    {
                        "type": "unauthorized_config_change",
                        "severity": "critical",
                        "description": "System configuration change without documented approval",
                        "event_id": change_event.event_id,
                        "requirement": "FISMA requires approval for all system changes",
                    }
                )

        # Check for data access controls
        data_access_events = [
            e for e in events if e.event_type == AuditEventType.DATA_ACCESS
        ]
        sensitive_access = [
            e
            for e in data_access_events
            if e.data_classification in ["secret", "top_secret"]
        ]

        for access_event in sensitive_access:
            if not access_event.event_data.get("justification"):
                report.add_finding(
                    {
                        "type": "undocumented_sensitive_access",
                        "severity": "high",
                        "description": "Access to sensitive data without documented justification",
                        "event_id": access_event.event_id,
                        "requirement": "FISMA requires justification for sensitive data access",
                    }
                )

    async def _analyze_privacy_compliance(
        self, report: ComplianceReport, events: list[AuditEvent]
    ):
        """Analyze Privacy Act compliance."""
        # Check for PII access
        pii_events = [
            e for e in events if e.event_type == AuditEventType.PRIVACY_DATA_ACCESS
        ]

        for pii_event in pii_events:
            if not pii_event.event_data.get("legal_basis"):
                report.add_finding(
                    {
                        "type": "unauthorized_pii_access",
                        "severity": "critical",
                        "description": "Access to PII without documented legal basis",
                        "event_id": pii_event.event_id,
                        "requirement": "Privacy Act requires legal basis for PII access",
                    }
                )

    def _calculate_compliance_metrics(self, events: list[AuditEvent]) -> dict[str, Any]:
        """Calculate compliance metrics."""
        total_events = len(events)
        if total_events == 0:
            return {}

        # Event type distribution
        event_types = {}
        for event in events:
            event_types[event.event_type.value] = (
                event_types.get(event.event_type.value, 0) + 1
            )

        # Severity distribution
        severity_dist = {}
        for event in events:
            severity_dist[event.severity.value] = (
                severity_dist.get(event.severity.value, 0) + 1
            )

        # Success rate
        successful_events = sum(1 for e in events if e.success)
        success_rate = (
            (successful_events / total_events) * 100 if total_events > 0 else 0
        )

        return {
            "total_events": total_events,
            "event_type_distribution": event_types,
            "severity_distribution": severity_dist,
            "success_rate_percent": success_rate,
            "unique_users": len({e.user_id for e in events if e.user_id}),
            "time_span_days": len({e.timestamp.date() for e in events}),
        }

    def _generate_recommendations(self, findings: list[dict[str, Any]]) -> list[str]:
        """Generate compliance recommendations."""
        recommendations = []

        # Group findings by type
        finding_types = {}
        for finding in findings:
            finding_type = finding.get("type", "unknown")
            finding_types[finding_type] = finding_types.get(finding_type, 0) + 1

        # Generate recommendations based on findings
        if "missing_audit_events" in finding_types:
            recommendations.append(
                "Implement comprehensive audit logging for all system events"
            )

        if "unauthorized_config_change" in finding_types:
            recommendations.append(
                "Establish formal change management process with approval workflows"
            )

        if "excessive_failed_logins" in finding_types:
            recommendations.append(
                "Implement account lockout policies and monitoring for brute force attacks"
            )

        if "unauthorized_pii_access" in finding_types:
            recommendations.append(
                "Implement access controls and justification requirements for PII data"
            )

        if not recommendations:
            recommendations.append(
                "Continue current compliance practices and regular monitoring"
            )

        return recommendations


class ComplianceManager:
    """Main compliance management system."""

    def __init__(
        self,
        database_url: str,
        encryption_key: bytes | None = None,
        s3_bucket: str | None = None,
    ):
        """Initialize compliance manager.

        Args:
            database_url: Database connection URL
            encryption_key: Encryption key for sensitive data
            s3_bucket: S3 bucket for secure storage
        """
        self.audit_logger = AuditLogger(database_url, encryption_key, s3_bucket)
        self.reporter = ComplianceReporter(self.audit_logger)
        self.retention_policies: dict[AuditEventType, int] = {}

        # Setup default retention policies
        self._setup_default_retention_policies()

    def _setup_default_retention_policies(self):
        """Setup default retention policies for different event types."""
        # FEMA/Federal requirements
        self.retention_policies.update(
            {
                # Authentication events - 3 years
                AuditEventType.USER_LOGIN: 1095,
                AuditEventType.USER_LOGOUT: 1095,
                AuditEventType.USER_LOGIN_FAILED: 1095,
                # System events - 7 years
                AuditEventType.SYSTEM_CONFIG_CHANGE: 2555,
                AuditEventType.SYSTEM_ERROR: 2555,
                # USAR operational events - 10 years
                AuditEventType.DEPLOYMENT_CREATE: 3650,
                AuditEventType.SAFETY_INCIDENT: 3650,
                # Privacy/PII events - 7 years
                AuditEventType.PRIVACY_DATA_ACCESS: 2555,
                # Compliance events - 7 years
                AuditEventType.COMPLIANCE_REPORT_GENERATE: 2555,
            }
        )

    async def log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str = "",
        description: str = "",
        severity: AuditSeverity = AuditSeverity.INFO,
        compliance_frameworks: list[ComplianceFramework] | None = None,
        event_data: dict[str, Any] | None = None,
        **kwargs,
    ) -> str:
        """Log audit event with compliance tracking.

        Args:
            event_type: Type of audit event
            user_id: User identifier
            resource_type: Resource type
            resource_id: Resource identifier
            action: Action performed
            description: Event description
            severity: Event severity
            compliance_frameworks: Applicable compliance frameworks
            event_data: Additional event data
            **kwargs: Additional event attributes

        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())

        # Determine retention period
        retention_days = self.retention_policies.get(event_type, 365)  # Default 1 year

        # Default compliance frameworks
        if not compliance_frameworks:
            compliance_frameworks = [
                ComplianceFramework.FEMA_DIRECTIVE,
                ComplianceFramework.NIMS_STANDARD,
            ]

        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now(UTC),
            user_id=user_id,
            session_id=kwargs.get("session_id"),
            ip_address=kwargs.get("ip_address"),
            user_agent=kwargs.get("user_agent"),
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=description,
            severity=severity,
            compliance_frameworks=compliance_frameworks,
            data_classification=kwargs.get("data_classification", "official_use_only"),
            retention_period_days=retention_days,
            event_data=event_data or {},
            before_state=kwargs.get("before_state"),
            after_state=kwargs.get("after_state"),
            success=kwargs.get("success", True),
            error_message=kwargs.get("error_message"),
            geolocation=kwargs.get("geolocation"),
            device_info=kwargs.get("device_info"),
            hash_signature=None,  # Will be calculated by audit logger
        )

        # Log the event
        await self.audit_logger.log_event(event)

        return event_id

    async def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        period_days: int = 30,
        generated_by: str = "system",
    ) -> ComplianceReport:
        """Generate compliance report.

        Args:
            framework: Compliance framework
            period_days: Report period in days
            generated_by: Report generator

        Returns:
            Compliance report
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=period_days)

        return await self.reporter.generate_compliance_report(
            framework=framework,
            period_start=start_time,
            period_end=end_time,
            generated_by=generated_by,
        )

    async def apply_retention_policy(self):
        """Apply retention policy to delete expired audit records."""
        cutoff_date = datetime.now(UTC) - timedelta(
            days=max(self.retention_policies.values())
        )

        # Query events to delete
        session = self.audit_logger.SessionLocal()
        try:
            # This would implement actual deletion based on retention policies
            # For now, we'll just mark them as archived
            sql = text(
                """
                UPDATE audit_events
                SET archived = TRUE
                WHERE timestamp < :cutoff_date
                AND archived IS NOT TRUE
            """
            )

            result = session.execute(sql, {"cutoff_date": cutoff_date})
            archived_count = result.rowcount
            session.commit()

            # Log retention policy application
            await self.log_audit_event(
                event_type=AuditEventType.RETENTION_POLICY_APPLY,
                action="archive_expired_events",
                description=f"Archived {archived_count} expired audit events",
                severity=AuditSeverity.INFO,
                event_data={
                    "archived_count": archived_count,
                    "cutoff_date": cutoff_date.isoformat(),
                },
            )

            logger.info(f"Retention policy applied: archived {archived_count} events")

        except Exception as e:
            session.rollback()
            logger.error(f"Retention policy application failed: {str(e)}")
            raise
        finally:
            session.close()


# Factory function for creating compliance manager
def create_compliance_manager(
    database_url: str,
    encryption_key: str | None = None,
    s3_bucket: str | None = None,
) -> ComplianceManager:
    """Create compliance manager instance.

    Args:
        database_url: Database connection URL
        encryption_key: Encryption key (base64 encoded)
        s3_bucket: S3 bucket for audit storage

    Returns:
        Configured compliance manager
    """
    # Convert encryption key from string if provided
    enc_key = None
    if encryption_key:
        import base64

        enc_key = base64.b64decode(encryption_key.encode())

    return ComplianceManager(database_url, enc_key, s3_bucket)
