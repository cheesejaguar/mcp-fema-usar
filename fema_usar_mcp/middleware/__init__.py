"""Middleware components for FEMA USAR MCP Server.

This package provides authentication, authorization, and audit
middleware for tool execution.
"""

from .audit_middleware import audit_tool_call, audited_tool, get_audit_log
from .auth_middleware import (
    TOOL_PERMISSIONS,
    Permission,
    check_permission,
    get_current_user,
    require_permission,
    secured_tool,
    security_enabled,
)

__all__ = [
    # Auth
    "Permission",
    "TOOL_PERMISSIONS",
    "require_permission",
    "check_permission",
    "get_current_user",
    "security_enabled",
    "secured_tool",
    # Audit
    "audited_tool",
    "audit_tool_call",
    "get_audit_log",
]
