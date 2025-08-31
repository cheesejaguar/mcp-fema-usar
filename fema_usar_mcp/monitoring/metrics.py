"""Monitoring and metrics collection for Federal USAR MCP.

Provides comprehensive monitoring, alerting, and observability
for USAR operations and system health.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import psutil
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    start_http_server,
)

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Alert:
    """Alert model."""

    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    source: str
    timestamp: datetime
    labels: dict[str, str]
    resolved: bool = False
    resolved_at: datetime | None = None
    acknowledgment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class HealthCheck:
    """Health check model."""

    name: str
    status: str  # healthy, degraded, unhealthy
    last_check: datetime
    response_time_ms: float
    details: dict[str, Any]
    check_function: Callable | None = None


class USARMetrics:
    """FEMA USAR specific metrics collector."""

    def __init__(self, registry: CollectorRegistry = None):
        """Initialize USAR metrics.

        Args:
            registry: Prometheus registry
        """
        self.registry = registry or CollectorRegistry()
        self._init_metrics()

    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # System metrics
        self.system_cpu_usage = Gauge(
            "usar_system_cpu_usage_percent",
            "System CPU usage percentage",
            registry=self.registry,
        )

        self.system_memory_usage = Gauge(
            "usar_system_memory_usage_bytes",
            "System memory usage in bytes",
            registry=self.registry,
        )

        self.system_disk_usage = Gauge(
            "usar_system_disk_usage_percent",
            "System disk usage percentage",
            ["mount_point"],
            registry=self.registry,
        )

        # Application metrics
        self.api_requests_total = Counter(
            "usar_api_requests_total",
            "Total API requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.api_request_duration = Histogram(
            "usar_api_request_duration_seconds",
            "API request duration",
            ["method", "endpoint"],
            registry=self.registry,
        )

        self.active_sessions = Gauge(
            "usar_active_sessions",
            "Number of active user sessions",
            registry=self.registry,
        )

        self.database_connections = Gauge(
            "usar_database_connections",
            "Database connection pool usage",
            ["pool_name"],
            registry=self.registry,
        )

        # USAR operational metrics
        self.active_deployments = Gauge(
            "usar_active_deployments",
            "Number of active deployments",
            ["task_force_id"],
            registry=self.registry,
        )

        self.personnel_deployed = Gauge(
            "usar_personnel_deployed",
            "Number of personnel deployed",
            ["task_force_id", "functional_group"],
            registry=self.registry,
        )

        self.equipment_operational = Gauge(
            "usar_equipment_operational",
            "Number of operational equipment items",
            ["task_force_id", "category"],
            registry=self.registry,
        )

        self.operations_active = Gauge(
            "usar_operations_active",
            "Number of active operations",
            ["deployment_id", "operation_type"],
            registry=self.registry,
        )

        self.search_operations_total = Counter(
            "usar_search_operations_total",
            "Total search operations conducted",
            ["task_force_id", "search_type", "result"],
            registry=self.registry,
        )

        self.rescue_operations_total = Counter(
            "usar_rescue_operations_total",
            "Total rescue operations conducted",
            ["task_force_id", "rescue_type", "result"],
            registry=self.registry,
        )

        self.medical_patients_treated = Counter(
            "usar_medical_patients_treated_total",
            "Total patients treated",
            ["task_force_id", "triage_category"],
            registry=self.registry,
        )

        self.safety_incidents_total = Counter(
            "usar_safety_incidents_total",
            "Total safety incidents",
            ["task_force_id", "incident_type", "severity"],
            registry=self.registry,
        )

        # Performance metrics
        self.cache_hit_rate = Gauge(
            "usar_cache_hit_rate",
            "Cache hit rate percentage",
            ["cache_name"],
            registry=self.registry,
        )

        self.async_tasks_pending = Gauge(
            "usar_async_tasks_pending",
            "Number of pending async tasks",
            registry=self.registry,
        )

        self.backup_last_success = Gauge(
            "usar_backup_last_success_timestamp",
            "Timestamp of last successful backup",
            ["backup_type"],
            registry=self.registry,
        )

        # Integration metrics
        self.external_api_requests = Counter(
            "usar_external_api_requests_total",
            "External API requests",
            ["service", "endpoint", "status"],
            registry=self.registry,
        )

        self.external_api_response_time = Histogram(
            "usar_external_api_response_time_seconds",
            "External API response time",
            ["service"],
            registry=self.registry,
        )


class AlertManager:
    """Alert management system."""

    def __init__(self):
        """Initialize alert manager."""
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.alert_rules: list[Callable] = []
        self.notification_channels: list[Callable] = []

    def add_alert_rule(self, rule_function: Callable):
        """Add alert rule.

        Args:
            rule_function: Function that returns Alert or None
        """
        self.alert_rules.append(rule_function)

    def add_notification_channel(self, channel_function: Callable):
        """Add notification channel.

        Args:
            channel_function: Function to send notifications
        """
        self.notification_channels.append(channel_function)

    def fire_alert(self, alert: Alert):
        """Fire new alert.

        Args:
            alert: Alert to fire
        """
        if alert.alert_id in self.active_alerts:
            # Update existing alert
            existing = self.active_alerts[alert.alert_id]
            existing.timestamp = alert.timestamp
            existing.message = alert.message
            existing.labels = alert.labels
        else:
            # New alert
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)

            # Send notifications
            for channel in self.notification_channels:
                try:
                    channel(alert)
                except Exception as e:
                    logger.error(f"Notification failed: {str(e)}")

        logger.warning(f"Alert fired: {alert.name} - {alert.message}")

    def resolve_alert(self, alert_id: str, resolved_by: str = "system"):
        """Resolve alert.

        Args:
            alert_id: Alert identifier
            resolved_by: Who resolved the alert
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(UTC)
            alert.acknowledgment = f"Resolved by {resolved_by}"

            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert.name}")

    def check_alert_rules(self, metrics_data: dict[str, Any]):
        """Check all alert rules against metrics.

        Args:
            metrics_data: Current metrics data
        """
        for rule in self.alert_rules:
            try:
                alert = rule(metrics_data)
                if alert:
                    self.fire_alert(alert)
            except Exception as e:
                logger.error(f"Alert rule check failed: {str(e)}")

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """Get active alerts.

        Args:
            severity: Filter by severity

        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)


class HealthMonitor:
    """System health monitoring."""

    def __init__(self):
        """Initialize health monitor."""
        self.health_checks: dict[str, HealthCheck] = {}
        self.health_status = "healthy"

    def add_health_check(self, check: HealthCheck):
        """Add health check.

        Args:
            check: Health check to add
        """
        self.health_checks[check.name] = check

    async def run_health_checks(self) -> dict[str, Any]:
        """Run all health checks.

        Returns:
            Health check results
        """
        results = {}
        overall_status = "healthy"

        for name, check in self.health_checks.items():
            try:
                start_time = time.time()

                if check.check_function:
                    status, details = await check.check_function()
                else:
                    status, details = "healthy", {}

                response_time = (time.time() - start_time) * 1000

                check.status = status
                check.last_check = datetime.now(UTC)
                check.response_time_ms = response_time
                check.details = details

                results[name] = {
                    "status": status,
                    "response_time_ms": response_time,
                    "last_check": check.last_check.isoformat(),
                    "details": details,
                }

                # Update overall status
                if status == "unhealthy":
                    overall_status = "unhealthy"
                elif status == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"

            except Exception as e:
                check.status = "unhealthy"
                check.last_check = datetime.now(UTC)
                check.details = {"error": str(e)}

                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": check.last_check.isoformat(),
                }

                overall_status = "unhealthy"

        self.health_status = overall_status

        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": datetime.now(UTC).isoformat(),
        }


class MetricsCollector:
    """System metrics collector."""

    def __init__(self, metrics: USARMetrics):
        """Initialize metrics collector.

        Args:
            metrics: USAR metrics instance
        """
        self.metrics = metrics
        self.collection_interval = 15  # seconds
        self._running = False

    async def start_collection(self):
        """Start metrics collection."""
        self._running = True
        logger.info("Starting metrics collection")

        while self._running:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                await asyncio.sleep(self.collection_interval)

    def stop_collection(self):
        """Stop metrics collection."""
        self._running = False
        logger.info("Stopped metrics collection")

    async def _collect_system_metrics(self):
        """Collect system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.system_cpu_usage.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics.system_memory_usage.set(memory.used)

        # Disk usage
        disk_partitions = psutil.disk_partitions()
        for partition in disk_partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                usage_percent = (usage.used / usage.total) * 100
                self.metrics.system_disk_usage.labels(
                    mount_point=partition.mountpoint
                ).set(usage_percent)
            except PermissionError:
                continue

    async def _collect_application_metrics(self):
        """Collect application-specific metrics."""
        # These would be populated by the actual application
        # For now, we'll set some example values

        # Database connections (example)
        self.metrics.database_connections.labels(pool_name="primary").set(5)

        # Cache hit rates (example)
        self.metrics.cache_hit_rate.labels(cache_name="operational_data").set(85.5)

        # Active sessions (example)
        self.metrics.active_sessions.set(12)


# Pre-built alert rules
def create_system_alert_rules(alert_manager: AlertManager):
    """Create system-level alert rules.

    Args:
        alert_manager: Alert manager instance
    """

    def high_cpu_usage(metrics: dict[str, Any]) -> Alert | None:
        """Alert for high CPU usage."""
        cpu_usage = metrics.get("system_cpu_usage", 0)
        if cpu_usage > 90:
            return Alert(
                alert_id="high_cpu_usage",
                name="High CPU Usage",
                severity=AlertSeverity.CRITICAL,
                message=f"CPU usage is {cpu_usage:.1f}% (threshold: 90%)",
                source="system",
                timestamp=datetime.now(UTC),
                labels={"component": "system", "metric": "cpu"},
            )
        elif cpu_usage > 80:
            return Alert(
                alert_id="elevated_cpu_usage",
                name="Elevated CPU Usage",
                severity=AlertSeverity.WARNING,
                message=f"CPU usage is {cpu_usage:.1f}% (threshold: 80%)",
                source="system",
                timestamp=datetime.now(UTC),
                labels={"component": "system", "metric": "cpu"},
            )
        return None

    def high_memory_usage(metrics: dict[str, Any]) -> Alert | None:
        """Alert for high memory usage."""
        memory_usage = metrics.get("system_memory_usage", 0)
        memory_total = metrics.get("system_memory_total", 1)
        usage_percent = (memory_usage / memory_total) * 100

        if usage_percent > 95:
            return Alert(
                alert_id="high_memory_usage",
                name="High Memory Usage",
                severity=AlertSeverity.CRITICAL,
                message=f"Memory usage is {usage_percent:.1f}% (threshold: 95%)",
                source="system",
                timestamp=datetime.now(UTC),
                labels={"component": "system", "metric": "memory"},
            )
        elif usage_percent > 85:
            return Alert(
                alert_id="elevated_memory_usage",
                name="Elevated Memory Usage",
                severity=AlertSeverity.WARNING,
                message=f"Memory usage is {usage_percent:.1f}% (threshold: 85%)",
                source="system",
                timestamp=datetime.now(UTC),
                labels={"component": "system", "metric": "memory"},
            )
        return None

    def disk_space_low(metrics: dict[str, Any]) -> Alert | None:
        """Alert for low disk space."""
        disk_usage = metrics.get("system_disk_usage", {})
        for mount_point, usage_percent in disk_usage.items():
            if usage_percent > 95:
                return Alert(
                    alert_id=f"disk_full_{mount_point.replace('/', '_')}",
                    name="Disk Space Critical",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Disk usage on {mount_point} is {usage_percent:.1f}% (threshold: 95%)",
                    source="system",
                    timestamp=datetime.now(UTC),
                    labels={
                        "component": "system",
                        "metric": "disk",
                        "mount_point": mount_point,
                    },
                )
            elif usage_percent > 85:
                return Alert(
                    alert_id=f"disk_low_{mount_point.replace('/', '_')}",
                    name="Disk Space Warning",
                    severity=AlertSeverity.WARNING,
                    message=f"Disk usage on {mount_point} is {usage_percent:.1f}% (threshold: 85%)",
                    source="system",
                    timestamp=datetime.now(UTC),
                    labels={
                        "component": "system",
                        "metric": "disk",
                        "mount_point": mount_point,
                    },
                )
        return None

    # Add rules to alert manager
    alert_manager.add_alert_rule(high_cpu_usage)
    alert_manager.add_alert_rule(high_memory_usage)
    alert_manager.add_alert_rule(disk_space_low)


def create_usar_alert_rules(alert_manager: AlertManager):
    """Create USAR-specific alert rules.

    Args:
        alert_manager: Alert manager instance
    """

    def deployment_health_check(metrics: dict[str, Any]) -> Alert | None:
        """Alert for deployment health issues."""
        active_deployments = metrics.get("active_deployments", 0)
        if active_deployments > 10:
            return Alert(
                alert_id="high_deployment_load",
                name="High Deployment Load",
                severity=AlertSeverity.WARNING,
                message=f"Managing {active_deployments} active deployments",
                source="usar_operations",
                timestamp=datetime.now(UTC),
                labels={"component": "operations", "metric": "deployments"},
            )
        return None

    def safety_incident_spike(metrics: dict[str, Any]) -> Alert | None:
        """Alert for safety incident spikes."""
        recent_incidents = metrics.get("safety_incidents_last_hour", 0)
        if recent_incidents >= 3:
            return Alert(
                alert_id="safety_incident_spike",
                name="Safety Incident Spike",
                severity=AlertSeverity.CRITICAL,
                message=f"{recent_incidents} safety incidents in the last hour",
                source="usar_safety",
                timestamp=datetime.now(UTC),
                labels={"component": "safety", "metric": "incidents"},
            )
        return None

    def equipment_failure_rate(metrics: dict[str, Any]) -> Alert | None:
        """Alert for high equipment failure rate."""
        failure_rate = metrics.get("equipment_failure_rate_percent", 0)
        if failure_rate > 10:
            return Alert(
                alert_id="high_equipment_failure_rate",
                name="High Equipment Failure Rate",
                severity=AlertSeverity.ERROR,
                message=f"Equipment failure rate is {failure_rate:.1f}%",
                source="usar_equipment",
                timestamp=datetime.now(UTC),
                labels={"component": "equipment", "metric": "failure_rate"},
            )
        return None

    # Add USAR-specific rules
    alert_manager.add_alert_rule(deployment_health_check)
    alert_manager.add_alert_rule(safety_incident_spike)
    alert_manager.add_alert_rule(equipment_failure_rate)


# Health check functions
async def database_health_check() -> tuple[str, dict[str, Any]]:
    """Database health check."""
    try:
        # In a real implementation, this would check database connectivity
        # For now, return a simulated result
        return "healthy", {
            "connection_pool_size": 10,
            "active_connections": 3,
            "query_response_time_ms": 15.2,
        }
    except Exception as e:
        return "unhealthy", {"error": str(e)}


async def redis_health_check() -> tuple[str, dict[str, Any]]:
    """Redis health check."""
    try:
        # Simulate Redis health check
        return "healthy", {
            "memory_usage_mb": 45.2,
            "connected_clients": 8,
            "keyspace_hits": 1250,
            "keyspace_misses": 89,
        }
    except Exception as e:
        return "unhealthy", {"error": str(e)}


async def external_api_health_check() -> tuple[str, dict[str, Any]]:
    """External API health check."""
    try:
        # Check FEMA IRIS and NIMS ICT connectivity
        return "healthy", {
            "fema_iris_status": "connected",
            "nims_ict_status": "connected",
            "last_sync_time": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        return "degraded", {"error": str(e)}


class MonitoringManager:
    """Main monitoring management class."""

    def __init__(self, port: int = 9090):
        """Initialize monitoring manager.

        Args:
            port: Prometheus metrics port
        """
        self.port = port
        self.registry = CollectorRegistry()
        self.metrics = USARMetrics(self.registry)
        self.alert_manager = AlertManager()
        self.health_monitor = HealthMonitor()
        self.metrics_collector = MetricsCollector(self.metrics)

        # Initialize health checks
        self._setup_health_checks()

        # Initialize alert rules
        create_system_alert_rules(self.alert_manager)
        create_usar_alert_rules(self.alert_manager)

    def _setup_health_checks(self):
        """Setup health checks."""
        db_check = HealthCheck(
            name="database",
            status="unknown",
            last_check=datetime.now(UTC),
            response_time_ms=0.0,
            details={},
            check_function=database_health_check,
        )

        redis_check = HealthCheck(
            name="redis",
            status="unknown",
            last_check=datetime.now(UTC),
            response_time_ms=0.0,
            details={},
            check_function=redis_health_check,
        )

        api_check = HealthCheck(
            name="external_apis",
            status="unknown",
            last_check=datetime.now(UTC),
            response_time_ms=0.0,
            details={},
            check_function=external_api_health_check,
        )

        self.health_monitor.add_health_check(db_check)
        self.health_monitor.add_health_check(redis_check)
        self.health_monitor.add_health_check(api_check)

    async def start(self):
        """Start monitoring services."""
        logger.info("Starting FEMA USAR monitoring system")

        # Start Prometheus metrics server
        start_http_server(self.port, registry=self.registry)
        logger.info(f"Prometheus metrics server started on port {self.port}")

        # Start metrics collection
        asyncio.create_task(self.metrics_collector.start_collection())

        # Start health check loop
        asyncio.create_task(self._health_check_loop())

        # Start alert check loop
        asyncio.create_task(self._alert_check_loop())

    async def _health_check_loop(self):
        """Health check monitoring loop."""
        while True:
            try:
                await self.health_monitor.run_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(30)

    async def _alert_check_loop(self):
        """Alert checking loop."""
        while True:
            try:
                # Collect current metrics data
                metrics_data = await self._collect_current_metrics()

                # Check alert rules
                self.alert_manager.check_alert_rules(metrics_data)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Alert check error: {str(e)}")
                await asyncio.sleep(60)

    async def _collect_current_metrics(self) -> dict[str, Any]:
        """Collect current metrics data for alert checking."""
        # In a real implementation, this would collect actual metrics
        return {
            "system_cpu_usage": psutil.cpu_percent(),
            "system_memory_usage": psutil.virtual_memory().used,
            "system_memory_total": psutil.virtual_memory().total,
            "active_deployments": 3,
            "safety_incidents_last_hour": 0,
            "equipment_failure_rate_percent": 2.1,
        }

    def get_metrics(self) -> str:
        """Get Prometheus metrics.

        Returns:
            Prometheus metrics in text format
        """
        return generate_latest(self.registry).decode("utf-8")

    async def get_health_status(self) -> dict[str, Any]:
        """Get system health status.

        Returns:
            Health status information
        """
        return await self.health_monitor.run_health_checks()

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """Get active alerts.

        Returns:
            List of active alerts
        """
        alerts = self.alert_manager.get_active_alerts()
        return [alert.to_dict() for alert in alerts]
