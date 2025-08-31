"""FEMA USAR MCP Models Package.

This package contains Pydantic models for FEMA USAR domain entities:
- Personnel models (70 positions, qualifications, tracking)
- Equipment models (16,400 items, maintenance, deployment)
- Operations models (missions, timelines, safety)
"""

from .personnel import (
    PersonnelModel,
    PersonnelQualification,
    PersonnelLocation,
    PositionAssignment,
)
from .equipment import (
    EquipmentModel,
    EquipmentCategory,
    MaintenanceRecord,
    DeploymentStatus,
)
from .operations import (
    MissionAssignment,
    OperationalTimeline,
    SafetyIncident,
    ResourceUtilization,
)

__all__ = [
    # Personnel models
    "PersonnelModel",
    "PersonnelQualification",
    "PersonnelLocation", 
    "PositionAssignment",
    # Equipment models
    "EquipmentModel",
    "EquipmentCategory",
    "MaintenanceRecord",
    "DeploymentStatus",
    # Operations models
    "MissionAssignment",
    "OperationalTimeline",
    "SafetyIncident",
    "ResourceUtilization",
]