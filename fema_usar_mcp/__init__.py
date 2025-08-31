"""FEMA Urban Search and Rescue MCP Server.

This package provides comprehensive digital tools supporting all 28 FEMA USAR
Task Forces during emergency response operations. It implements domain-specific
tools for each of the 70 personnel positions within a Type 1 USAR task force.
"""

__version__ = "0.1.0"
__author__ = "FEMA USAR MCP Team"
__email__ = "usar-mcp@example.com"

from .core import (
    EquipmentItem,
    OperationalStatus,
    PersonnelPosition,
    USARTaskForceConfig,
    get_system_status,
)

__all__ = [
    "USARTaskForceConfig",
    "PersonnelPosition",
    "EquipmentItem",
    "OperationalStatus",
    "get_system_status",
]
