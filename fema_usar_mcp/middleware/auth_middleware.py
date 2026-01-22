"""Authentication and authorization middleware for FEMA USAR MCP tools.

This module provides RBAC (Role-Based Access Control) for MCP tool execution.
Security is disabled by default and can be enabled via environment variable.

Usage:
    USAR_SECURITY_ENABLED=true fema-usar-mcp
"""

import json
import logging
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Permission levels for USAR operations."""

    # Command permissions
    COMMAND_READ = "command:read"
    COMMAND_WRITE = "command:write"
    COMMAND_ALL = "command:*"

    # Safety permissions
    SAFETY_READ = "safety:read"
    SAFETY_WRITE = "safety:write"
    SAFETY_ALL = "safety:*"

    # Search permissions
    SEARCH_READ = "search:read"
    SEARCH_WRITE = "search:write"
    SEARCH_ALL = "search:*"

    # Rescue permissions
    RESCUE_READ = "rescue:read"
    RESCUE_WRITE = "rescue:write"
    RESCUE_ALL = "rescue:*"

    # Medical permissions
    MEDICAL_READ = "medical:read"
    MEDICAL_WRITE = "medical:write"
    MEDICAL_ALL = "medical:*"

    # Planning permissions
    PLANNING_READ = "planning:read"
    PLANNING_WRITE = "planning:write"
    PLANNING_ALL = "planning:*"

    # Logistics permissions
    LOGISTICS_READ = "logistics:read"
    LOGISTICS_WRITE = "logistics:write"
    LOGISTICS_ALL = "logistics:*"

    # Technical permissions
    TECHNICAL_READ = "technical:read"
    TECHNICAL_WRITE = "technical:write"
    TECHNICAL_ALL = "technical:*"

    # System permissions
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_ALL = "system:*"

    # Global permissions
    ALL = "*"


# Mapping of tool names to required permissions
TOOL_PERMISSIONS: dict[str, str] = {
    # Command tools
    "task_force_leader_dashboard": "command:*",
    "safety_officer_monitor": "safety:*",
    "personnel_accountability": "command:read",
    "mission_assignment_tracker": "command:read",
    "external_coordination": "command:*",
    # Search tools
    "victim_location_tracker": "search:read",
    "search_pattern_planner": "search:write",
    "technical_search_equipment": "search:read",
    "canine_team_deployment": "search:write",
    "void_space_assessment": "search:read",
    # Rescue tools
    "rescue_squad_operations": "rescue:write",
    "victim_extraction_planner": "rescue:write",
    "structural_stabilization": "rescue:write",
    "heavy_equipment_operations": "rescue:write",
    "debris_removal_coordinator": "rescue:write",
    # Medical tools
    "patient_care_tracker": "medical:write",
    "medical_supply_inventory": "medical:read",
    "triage_coordinator": "medical:write",
    "health_surveillance": "medical:read",
    "evacuation_coordinator": "medical:write",
    # Planning tools
    "situation_unit_dashboard": "planning:read",
    "resource_unit_tracker": "planning:read",
    "documentation_automation": "planning:write",
    "demobilization_planner": "planning:write",
    "operational_timeline": "planning:read",
    # Logistics tools
    "supply_chain_manager": "logistics:write",
    "facilities_coordinator": "logistics:write",
    "ground_support_tracker": "logistics:read",
    "fuel_management": "logistics:write",
    "maintenance_scheduler": "logistics:write",
    # Technical tools
    "structural_assessment": "technical:read",
    "hazmat_monitoring": "technical:read",
    "communications_manager": "technical:write",
    "rigging_calculator": "technical:read",
    "environmental_monitor": "technical:read",
    # Decision support tools
    "tactical_decision_support": "command:read",
    "strategic_planning_advisor": "planning:read",
    "operational_intelligence_system": "command:*",
    # System tools
    "get_system_performance": "system:read",
    "clear_system_cache": "system:admin",
    "submit_async_operation": "system:write",
    "get_async_task_info": "system:read",
    "get_usar_system_status": "system:read",
    "calculate_task_force_readiness": "system:read",
    "list_functional_groups": "system:read",
    # Meta-tools
    "usar_browse_categories": "system:read",
    "usar_list_tools": "system:read",
    "usar_get_tool_schema": "system:read",
    "usar_execute_tool": "*",  # Requires underlying tool's permission
    "usar_health_check": "system:read",
    "usar_metrics": "system:read",
}


@dataclass
class User:
    """Represents an authenticated user."""

    user_id: str
    username: str
    roles: list[str]
    permissions: set[str]
    task_force_id: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class AuthContext:
    """Authentication context for a request."""

    user: User | None
    is_authenticated: bool
    auth_method: str | None
    session_id: str | None


# Thread-local storage for current user context
_auth_context = threading.local()


def security_enabled() -> bool:
    """Check if security is enabled via environment variable.

    Returns:
        True if USAR_SECURITY_ENABLED is set to a truthy value
    """
    return os.environ.get("USAR_SECURITY_ENABLED", "").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def get_current_user() -> User | None:
    """Get the current authenticated user.

    Returns:
        User object if authenticated, None otherwise
    """
    ctx = getattr(_auth_context, "context", None)
    if ctx and ctx.is_authenticated:
        return ctx.user
    return None


def set_current_user(
    user: User, auth_method: str = "api_key", session_id: str | None = None
) -> None:
    """Set the current authenticated user.

    Args:
        user: The authenticated user
        auth_method: Method used for authentication
        session_id: Optional session identifier
    """
    _auth_context.context = AuthContext(
        user=user,
        is_authenticated=True,
        auth_method=auth_method,
        session_id=session_id,
    )


def clear_current_user() -> None:
    """Clear the current authentication context."""
    _auth_context.context = AuthContext(
        user=None, is_authenticated=False, auth_method=None, session_id=None
    )


def check_permission(required: str, user: User | None = None) -> bool:
    """Check if user has the required permission.

    Args:
        required: Required permission string
        user: User to check (defaults to current user)

    Returns:
        True if user has permission, False otherwise
    """
    if not security_enabled():
        return True  # Security disabled, allow all

    if user is None:
        user = get_current_user()

    if user is None:
        return False  # No user, deny

    # Check for wildcard permission
    if Permission.ALL.value in user.permissions:
        return True

    # Check for exact permission match
    if required in user.permissions:
        return True

    # Check for category wildcard (e.g., "command:*" grants "command:read")
    if ":" in required:
        category = required.split(":")[0]
        if f"{category}:*" in user.permissions:
            return True

    return False


def require_permission(permission: str):
    """Decorator requiring specific RBAC permission.

    Args:
        permission: Required permission string

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not security_enabled():
                return func(*args, **kwargs)

            user = get_current_user()
            if not check_permission(permission, user):
                logger.warning(
                    f"Permission denied: {permission} for user {user.username if user else 'anonymous'}"
                )
                return json.dumps(
                    {
                        "error": "Permission denied",
                        "required_permission": permission,
                        "user": user.username if user else "anonymous",
                        "hint": "Contact your administrator to request access",
                    },
                    indent=2,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_permission_for_tool(tool_name: str) -> str | None:
    """Get the required permission for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Required permission string or None if not found
    """
    return TOOL_PERMISSIONS.get(tool_name)


def create_user(
    user_id: str,
    username: str,
    roles: list[str],
    task_force_id: str | None = None,
) -> User:
    """Create a user with permissions derived from roles.

    Args:
        user_id: Unique user identifier
        username: Display name
        roles: List of role names
        task_force_id: Optional task force association

    Returns:
        User object with derived permissions
    """
    # Role to permission mapping
    role_permissions = {
        "task_force_leader": {
            Permission.COMMAND_ALL.value,
            Permission.SAFETY_ALL.value,
            Permission.PLANNING_READ.value,
            Permission.SYSTEM_READ.value,
        },
        "safety_officer": {
            Permission.SAFETY_ALL.value,
            Permission.COMMAND_READ.value,
            Permission.TECHNICAL_READ.value,
        },
        "search_manager": {
            Permission.SEARCH_ALL.value,
            Permission.COMMAND_READ.value,
            Permission.TECHNICAL_READ.value,
        },
        "rescue_manager": {
            Permission.RESCUE_ALL.value,
            Permission.COMMAND_READ.value,
            Permission.TECHNICAL_ALL.value,
        },
        "medical_manager": {
            Permission.MEDICAL_ALL.value,
            Permission.COMMAND_READ.value,
        },
        "planning_chief": {
            Permission.PLANNING_ALL.value,
            Permission.COMMAND_READ.value,
            Permission.LOGISTICS_READ.value,
        },
        "logistics_chief": {
            Permission.LOGISTICS_ALL.value,
            Permission.COMMAND_READ.value,
        },
        "admin": {Permission.ALL.value},
        "operator": {
            Permission.COMMAND_READ.value,
            Permission.SEARCH_READ.value,
            Permission.RESCUE_READ.value,
            Permission.MEDICAL_READ.value,
            Permission.PLANNING_READ.value,
            Permission.LOGISTICS_READ.value,
            Permission.TECHNICAL_READ.value,
            Permission.SYSTEM_READ.value,
        },
    }

    # Collect all permissions from roles
    permissions: set[str] = set()
    for role in roles:
        role_perms = role_permissions.get(role, set())
        permissions.update(role_perms)

    return User(
        user_id=user_id,
        username=username,
        roles=roles,
        permissions=permissions,
        task_force_id=task_force_id,
    )


def secured_tool(func: Callable) -> Callable:
    """Decorator that applies permission checking based on TOOL_PERMISSIONS.

    This decorator automatically looks up the required permission for the
    decorated function based on its name.

    Returns:
        Decorated function with permission checking
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not security_enabled():
            return func(*args, **kwargs)

        tool_name = func.__name__
        permission = get_permission_for_tool(tool_name)

        if permission and not check_permission(permission):
            user = get_current_user()
            logger.warning(
                f"Permission denied: {permission} for tool {tool_name}, user {user.username if user else 'anonymous'}"
            )
            return json.dumps(
                {
                    "error": "Permission denied",
                    "tool": tool_name,
                    "required_permission": permission,
                    "user": user.username if user else "anonymous",
                },
                indent=2,
            )

        return func(*args, **kwargs)

    return wrapper
