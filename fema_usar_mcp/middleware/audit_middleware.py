"""Audit middleware for FEMA USAR MCP tool invocations.

This module provides comprehensive audit logging for tool calls,
including sensitive data sanitization and compliance reporting.
"""

import hashlib
import json
import logging
import os
import re
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any

from .auth_middleware import get_current_user

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""

    audit_id: str
    timestamp: str
    tool_name: str
    user_id: str | None
    username: str | None
    parameters: dict[str, Any]
    parameters_sanitized: bool
    result_status: str
    execution_time_ms: float
    error_message: str | None = None
    task_force_id: str | None = None
    ip_address: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditLog:
    """Thread-safe audit log with configurable retention."""

    def __init__(self, max_entries: int = 10000, retention_hours: int = 72):
        """Initialize the audit log.

        Args:
            max_entries: Maximum number of entries to retain in memory
            retention_hours: Hours to retain entries (for file-based logging)
        """
        self._entries: deque[AuditEntry] = deque(maxlen=max_entries)
        self._lock = threading.RLock()
        self._retention_hours = retention_hours
        self._file_logging_enabled = os.environ.get(
            "USAR_AUDIT_FILE_LOGGING", ""
        ).lower() in ("true", "1", "yes")
        self._log_file = os.environ.get("USAR_AUDIT_LOG_FILE", "/tmp/usar_audit.jsonl")

    def add_entry(self, entry: AuditEntry) -> None:
        """Add an audit entry.

        Args:
            entry: The audit entry to add
        """
        with self._lock:
            self._entries.append(entry)

            # Log to file if enabled
            if self._file_logging_enabled:
                self._write_to_file(entry)

            # Also log to standard logger
            logger.info(
                f"AUDIT: {entry.tool_name} by {entry.username or 'anonymous'} "
                f"- {entry.result_status} ({entry.execution_time_ms:.2f}ms)"
            )

    def get_entries(
        self,
        limit: int = 100,
        tool_name: str | None = None,
        user_id: str | None = None,
        since: str | None = None,
    ) -> list[AuditEntry]:
        """Get audit entries with optional filtering.

        Args:
            limit: Maximum number of entries to return
            tool_name: Filter by tool name
            user_id: Filter by user ID
            since: ISO timestamp to filter entries after

        Returns:
            List of matching audit entries
        """
        with self._lock:
            entries = list(self._entries)

        # Apply filters
        if tool_name:
            entries = [e for e in entries if e.tool_name == tool_name]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        if since:
            entries = [e for e in entries if e.timestamp >= since]

        # Return most recent first, limited
        return list(reversed(entries))[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """Get audit statistics.

        Returns:
            Dictionary with audit statistics
        """
        with self._lock:
            entries = list(self._entries)

        if not entries:
            return {
                "total_entries": 0,
                "tools_invoked": {},
                "users_active": {},
                "avg_execution_time_ms": 0,
                "error_rate": 0,
            }

        # Calculate statistics
        tools_invoked: dict[str, int] = {}
        users_active: dict[str, int] = {}
        total_time = 0.0
        errors = 0

        for entry in entries:
            tools_invoked[entry.tool_name] = tools_invoked.get(entry.tool_name, 0) + 1
            user = entry.username or "anonymous"
            users_active[user] = users_active.get(user, 0) + 1
            total_time += entry.execution_time_ms
            if entry.result_status == "error":
                errors += 1

        return {
            "total_entries": len(entries),
            "tools_invoked": tools_invoked,
            "users_active": users_active,
            "avg_execution_time_ms": total_time / len(entries),
            "error_rate": errors / len(entries) if entries else 0,
            "oldest_entry": entries[0].timestamp if entries else None,
            "newest_entry": entries[-1].timestamp if entries else None,
        }

    def clear(self) -> int:
        """Clear all audit entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count

    def _write_to_file(self, entry: AuditEntry) -> None:
        """Write an entry to the audit log file.

        Args:
            entry: The entry to write
        """
        try:
            with open(self._log_file, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        except OSError as e:
            logger.error(f"Failed to write audit log: {e}")


# Global audit log instance
_audit_log: AuditLog | None = None
_audit_lock = threading.Lock()


def get_audit_log() -> AuditLog:
    """Get or create the global audit log.

    Returns:
        The global AuditLog instance
    """
    global _audit_log
    with _audit_lock:
        if _audit_log is None:
            _audit_log = AuditLog()
        return _audit_log


# Sensitive data patterns for sanitization
SENSITIVE_PATTERNS = [
    # Social Security Numbers
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN-REDACTED]"),
    # Credit card numbers
    (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[CC-REDACTED]"),
    # Phone numbers
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE-REDACTED]"),
    # Email addresses
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL-REDACTED]"),
    # Patient IDs (common patterns)
    (r"\bPAT-\d{3,}\b", lambda m: f"PAT-{_hash_id(m.group())}"),
    # API keys / tokens
    (
        r"\b(api[_-]?key|token|bearer|auth)[=:\s]+[A-Za-z0-9-_.]{20,}\b",
        "[TOKEN-REDACTED]",
    ),
    # Passwords
    (r"\b(password|passwd|pwd)[=:\s]+\S+\b", "[PASSWORD-REDACTED]"),
]


def _hash_id(value: str) -> str:
    """Hash an ID for privacy while maintaining uniqueness.

    Args:
        value: The value to hash

    Returns:
        First 8 characters of MD5 hash
    """
    return hashlib.md5(value.encode()).hexdigest()[:8]


def sanitize_value(value: Any) -> tuple[Any, bool]:
    """Sanitize a single value for audit logging.

    Args:
        value: The value to sanitize

    Returns:
        Tuple of (sanitized_value, was_sanitized)
    """
    if value is None:
        return None, False

    if isinstance(value, dict):
        sanitized = {}
        any_sanitized = False
        for k, v in value.items():
            sanitized[k], was_sanitized = sanitize_value(v)
            any_sanitized = any_sanitized or was_sanitized
        return sanitized, any_sanitized

    if isinstance(value, list):
        sanitized = []
        any_sanitized = False
        for item in value:
            san_item, was_sanitized = sanitize_value(item)
            sanitized.append(san_item)
            any_sanitized = any_sanitized or was_sanitized
        return sanitized, any_sanitized

    if isinstance(value, str):
        original = value
        for pattern, replacement in SENSITIVE_PATTERNS:
            if callable(replacement):
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
            else:
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        return value, value != original

    return value, False


def sanitize_parameters(params: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Sanitize parameters dictionary for audit logging.

    Args:
        params: Parameters to sanitize

    Returns:
        Tuple of (sanitized_params, was_sanitized)
    """
    return sanitize_value(params)


def audit_tool_call(
    tool_name: str,
    parameters: dict[str, Any],
    result: str,
    execution_time_ms: float,
    error: Exception | None = None,
) -> AuditEntry:
    """Create and log an audit entry for a tool call.

    Args:
        tool_name: Name of the tool that was called
        parameters: Parameters passed to the tool
        result: Result returned by the tool
        execution_time_ms: Execution time in milliseconds
        error: Optional exception if tool failed

    Returns:
        The created audit entry
    """
    # Get current user context
    user = get_current_user()

    # Sanitize parameters
    sanitized_params, was_sanitized = sanitize_parameters(parameters)

    # Determine result status
    if error:
        result_status = "error"
        error_message = str(error)
    else:
        try:
            result_data = json.loads(result)
            result_status = result_data.get("status", "success")
            error_message = result_data.get("error")
        except (json.JSONDecodeError, AttributeError):
            result_status = "success"
            error_message = None

    # Create audit entry
    entry = AuditEntry(
        audit_id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        tool_name=tool_name,
        user_id=user.user_id if user else None,
        username=user.username if user else None,
        parameters=sanitized_params,
        parameters_sanitized=was_sanitized,
        result_status=result_status,
        execution_time_ms=execution_time_ms,
        error_message=error_message,
        task_force_id=user.task_force_id if user else None,
        metadata={
            "result_length": len(result),
            "parameter_count": len(parameters),
        },
    )

    # Add to audit log
    get_audit_log().add_entry(entry)

    return entry


def audited_tool(func: Callable) -> Callable:
    """Decorator that adds audit logging to a tool function.

    This decorator automatically logs all tool invocations with
    timing, parameters (sanitized), and results.

    Returns:
        Decorated function with audit logging
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        tool_name = func.__name__
        error = None
        result = ""

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error = e
            result = json.dumps({"error": str(e)})
            raise
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
            audit_tool_call(
                tool_name=tool_name,
                parameters=kwargs,
                result=result,
                execution_time_ms=execution_time_ms,
                error=error,
            )

    return wrapper


def audit_enabled() -> bool:
    """Check if audit logging is enabled.

    Returns:
        True (audit logging is always enabled)
    """
    # Audit logging is always enabled - this function is for API consistency
    return True


def export_audit_log(
    format: str = "json",
    limit: int | None = None,
    since: str | None = None,
) -> str:
    """Export audit log entries.

    Args:
        format: Export format ('json' or 'csv')
        limit: Maximum entries to export
        since: ISO timestamp to filter entries after

    Returns:
        Exported audit log as string
    """
    audit_log = get_audit_log()
    entries = audit_log.get_entries(limit=limit or 10000, since=since)

    if format == "json":
        return json.dumps([asdict(e) for e in entries], indent=2)

    elif format == "csv":
        if not entries:
            return (
                "audit_id,timestamp,tool_name,username,result_status,execution_time_ms"
            )

        headers = [
            "audit_id",
            "timestamp",
            "tool_name",
            "username",
            "result_status",
            "execution_time_ms",
        ]
        lines = [",".join(headers)]

        for entry in entries:
            row = [
                entry.audit_id,
                entry.timestamp,
                entry.tool_name,
                entry.username or "anonymous",
                entry.result_status,
                str(entry.execution_time_ms),
            ]
            lines.append(",".join(row))

        return "\n".join(lines)

    else:
        raise ValueError(f"Unsupported format: {format}")
