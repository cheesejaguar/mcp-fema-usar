"""Federal USAR MCP Models Package.

This package contains Pydantic models for FEMA USAR domain entities:
- Personnel models (70 positions, qualifications, tracking)
- Equipment models (16,400 items, maintenance, deployment)
- Operations models (missions, timelines, safety)
"""

from .equipment import (
    DeploymentStatus,
    EquipmentCategory,
    EquipmentModel,
    MaintenanceRecord,
)
from .operations import (
    MissionAssignment,
    OperationalTimeline,
    ResourceUtilization,
    SafetyIncident,
)
from .personnel import (
    PersonnelLocation,
    PersonnelModel,
    PersonnelQualification,
    PositionAssignment,
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
