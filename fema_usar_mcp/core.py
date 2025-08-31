"""Core business logic and domain models for FEMA USAR operations."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# USAR-specific constants
TOTAL_PERSONNEL_POSITIONS = 70
TOTAL_EQUIPMENT_ITEMS = 16400
DEPLOYMENT_TIME_TARGET_HOURS = 6
SELF_SUFFICIENCY_HOURS = 96
TOTAL_TASK_FORCES = 28

# Functional Groups
FUNCTIONAL_GROUPS = {
    "COMMAND": ["Task Force Leader", "Safety Officer"],
    "SEARCH": ["Search Team Manager", "Technical Search Specialist", "Canine Handler"],
    "RESCUE": [
        "Rescue Team Manager",
        "Rescue Squad Leader",
        "Rescue Specialist",
        "Heavy Equipment Operator",
    ],
    "MEDICAL": ["Medical Team Manager", "Task Force Physician", "Medical Specialist"],
    "PLANNING": [
        "Planning Section Chief",
        "SITL",
        "RESL",
        "Documentation Unit Leader",
        "Demobilization Unit Leader",
    ],
    "LOGISTICS": [
        "Logistics Section Chief",
        "Supply Unit Leader",
        "Facilities Unit Leader",
        "Ground Support Unit Leader",
    ],
    "TECHNICAL": [
        "Structures Specialist",
        "Hazmat Specialist",
        "Heavy Equipment/Rigging Specialist",
        "Communications Specialist",
    ],
}

# Check for optional dependencies
ADVANCED_INTEGRATION_AVAILABLE = True
try:
    import numpy  # noqa: F401
    import pandas  # noqa: F401
except ImportError:
    ADVANCED_INTEGRATION_AVAILABLE = False
    logger.warning(
        "Advanced integration libraries not available - some features will be limited"
    )


class OperationalStatus(str, Enum):
    """Task force operational status."""

    READY = "ready"
    DEPLOYED = "deployed"
    DEMOBILIZING = "demobilizing"
    MAINTENANCE = "maintenance"
    TRAINING = "training"
    UNAVAILABLE = "unavailable"


class AlertLevel(str, Enum):
    """Safety and operational alert levels."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    CRITICAL = "critical"


class MissionType(str, Enum):
    """Types of USAR missions."""

    SEARCH_AND_RESCUE = "search_and_rescue"
    TECHNICAL_RESCUE = "technical_rescue"
    HAZMAT_RESPONSE = "hazmat_response"
    STRUCTURAL_COLLAPSE = "structural_collapse"
    DISASTER_RESPONSE = "disaster_response"
    TRAINING_EXERCISE = "training_exercise"


class PersonnelPosition(BaseModel):
    """Personnel position within USAR task force."""

    position_id: str = Field(..., description="Unique position identifier")
    position_name: str = Field(..., description="Official position title")
    functional_group: str = Field(
        ..., description="Functional group (Command, Search, etc.)"
    )
    required_qualifications: list[str] = Field(default_factory=list)
    current_assignee: str | None = None
    backup_assignee: str | None = None
    is_critical: bool = Field(False, description="Position critical for operations")
    minimum_experience_years: int = Field(
        0, description="Minimum years of experience required"
    )


class EquipmentItem(BaseModel):
    """Individual equipment item tracking."""

    equipment_id: str = Field(..., description="Unique equipment identifier")
    equipment_name: str = Field(..., description="Equipment name/description")
    category: str = Field(..., description="Equipment category")
    serial_number: str | None = None
    assigned_to: str | None = None
    location: str | None = None
    status: Literal["operational", "maintenance", "repair", "unavailable"] = (
        "operational"
    )
    last_inspection: datetime | None = None
    next_maintenance: datetime | None = None
    deployment_ready: bool = True


class USARTaskForceConfig(BaseModel):
    """Configuration for a USAR task force."""

    task_force_id: str = Field(..., description="Task force identifier (e.g., CA-TF1)")
    task_force_name: str = Field(..., description="Official task force name")
    home_location: str = Field(..., description="Home base location")
    operational_status: OperationalStatus = OperationalStatus.READY
    personnel_count: int = Field(70, description="Current personnel count")
    equipment_ready_count: int = Field(
        16400, description="Equipment items ready for deployment"
    )
    last_deployment: datetime | None = None
    certifications_current: bool = True
    training_compliance: float = Field(
        100.0, ge=0, le=100, description="Training compliance percentage"
    )


class SafetyAlert(BaseModel):
    """Safety alert or incident."""

    alert_id: str = Field(..., description="Unique alert identifier")
    alert_level: AlertLevel
    alert_type: str = Field(..., description="Type of safety alert")
    location: str | None = None
    description: str = Field(..., description="Alert description")
    personnel_affected: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
    resolution_notes: str | None = None


class MissionAssignment(BaseModel):
    """USAR mission assignment."""

    mission_id: str = Field(..., description="Unique mission identifier")
    mission_type: MissionType
    location: str = Field(..., description="Mission location")
    requesting_agency: str = Field(..., description="Agency requesting assistance")
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    estimated_duration_hours: int | None = None
    resources_required: dict[str, Any] = Field(default_factory=dict)
    assigned_personnel: list[str] = Field(default_factory=list)
    status: Literal["assigned", "en_route", "on_scene", "completed", "cancelled"] = (
        "assigned"
    )
    start_time: datetime | None = None
    completion_time: datetime | None = None


class USARError(Exception):
    """USAR-specific error handling."""

    pass


def get_functional_group_positions() -> dict[str, list[str]]:
    """Get all functional groups and their positions."""
    return FUNCTIONAL_GROUPS.copy()


def calculate_deployment_readiness(
    task_force_config: USARTaskForceConfig,
) -> dict[str, Any]:
    """Calculate task force deployment readiness."""
    start_time = time.time()

    try:
        # Calculate readiness metrics
        personnel_readiness = (
            task_force_config.personnel_count / TOTAL_PERSONNEL_POSITIONS
        ) * 100
        equipment_readiness = (
            task_force_config.equipment_ready_count / TOTAL_EQUIPMENT_ITEMS
        ) * 100
        training_readiness = task_force_config.training_compliance

        # Overall readiness calculation
        overall_readiness = (
            personnel_readiness + equipment_readiness + training_readiness
        ) / 3

        # Determine deployment capability
        deployment_capable = (
            overall_readiness >= 85.0
            and task_force_config.operational_status == OperationalStatus.READY
            and task_force_config.certifications_current
        )

        processing_time = (time.time() - start_time) * 1000

        return {
            "overall_readiness_percent": round(overall_readiness, 1),
            "personnel_readiness_percent": round(personnel_readiness, 1),
            "equipment_readiness_percent": round(equipment_readiness, 1),
            "training_readiness_percent": round(training_readiness, 1),
            "deployment_capable": deployment_capable,
            "estimated_deployment_time_hours": (
                DEPLOYMENT_TIME_TARGET_HOURS if deployment_capable else None
            ),
            "self_sufficiency_hours": SELF_SUFFICIENCY_HOURS,
            "processing_time_ms": processing_time,
            "last_calculated": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Deployment readiness calculation error: {str(e)}", exc_info=True)
        raise USARError(f"Readiness calculation failed: {str(e)}") from e


def process_safety_alert(alert: SafetyAlert) -> dict[str, Any]:
    """Process and validate safety alert."""
    start_time = time.time()

    try:
        # Determine response requirements based on alert level
        response_requirements = {
            AlertLevel.GREEN: {
                "immediate_response": False,
                "notification_level": "info",
            },
            AlertLevel.YELLOW: {
                "immediate_response": False,
                "notification_level": "warning",
            },
            AlertLevel.RED: {
                "immediate_response": True,
                "notification_level": "urgent",
            },
            AlertLevel.CRITICAL: {
                "immediate_response": True,
                "notification_level": "emergency",
            },
        }

        requirements = response_requirements.get(alert.alert_level)
        processing_time = (time.time() - start_time) * 1000

        return {
            "alert_id": alert.alert_id,
            "processing_status": "processed",
            "immediate_response_required": requirements["immediate_response"],
            "notification_level": requirements["notification_level"],
            "personnel_count_affected": len(alert.personnel_affected),
            "estimated_impact": (
                "high"
                if alert.alert_level in [AlertLevel.RED, AlertLevel.CRITICAL]
                else "low"
            ),
            "processing_time_ms": processing_time,
            "recommendations": generate_safety_recommendations(alert),
        }

    except Exception as e:
        logger.error(f"Safety alert processing error: {str(e)}", exc_info=True)
        raise USARError(f"Alert processing failed: {str(e)}") from e


def generate_safety_recommendations(alert: SafetyAlert) -> list[str]:
    """Generate safety recommendations based on alert type."""
    recommendations = []

    alert_type_lower = alert.alert_type.lower()

    if "structural" in alert_type_lower:
        recommendations.extend(
            [
                "Evacuate affected area immediately",
                "Contact Structures Specialist for assessment",
                "Establish safety perimeter",
                "Implement fall protection protocols",
            ]
        )
    elif "hazmat" in alert_type_lower or "chemical" in alert_type_lower:
        recommendations.extend(
            [
                "Initiate decontamination procedures",
                "Deploy Hazmat Specialist team",
                "Establish contamination control zones",
                "Monitor air quality continuously",
            ]
        )
    elif "medical" in alert_type_lower:
        recommendations.extend(
            [
                "Deploy Medical Specialist immediately",
                "Prepare evacuation if necessary",
                "Document injury/illness details",
                "Notify Task Force Leader",
            ]
        )
    else:
        recommendations.extend(
            [
                "Assess situation for escalation",
                "Notify appropriate specialists",
                "Document incident details",
                "Monitor for changes",
            ]
        )

    return recommendations


def get_usar_capabilities() -> dict[str, Any]:
    """Get comprehensive USAR system capabilities."""
    return {
        "functional_groups": list(FUNCTIONAL_GROUPS.keys()),
        "total_positions": TOTAL_PERSONNEL_POSITIONS,
        "total_equipment": TOTAL_EQUIPMENT_ITEMS,
        "deployment_time_target": DEPLOYMENT_TIME_TARGET_HOURS,
        "self_sufficiency_hours": SELF_SUFFICIENCY_HOURS,
        "supported_task_forces": TOTAL_TASK_FORCES,
        "tools": {
            "command_tools": 5,
            "search_tools": 5,
            "rescue_tools": 5,
            "medical_tools": 5,
            "planning_tools": 5,
            "logistics_tools": 5,
            "technical_tools": 5,
        },
        "integrations": {
            "fema_iris": True,
            "nims_ict": True,
            "federal_asset_tracking": True,
            "multi_band_radio": True,
            "satellite_comm": True,
        },
        "advanced_features_available": ADVANCED_INTEGRATION_AVAILABLE,
    }


def get_system_status() -> dict[str, Any]:
    """Return comprehensive system status."""
    return {
        "system": "FEMA USAR MCP Server",
        "version": "0.1.0",
        "status": "operational",
        "capabilities": get_usar_capabilities(),
        "advanced_integration_available": ADVANCED_INTEGRATION_AVAILABLE,
        "functional_groups_supported": len(FUNCTIONAL_GROUPS),
        "uptime": "operational",
        "last_updated": datetime.now().isoformat(),
    }


def validate_personnel_assignment(
    position: PersonnelPosition, assignee_qualifications: list[str]
) -> bool:
    """Validate that personnel meet position requirements."""
    if not position.required_qualifications:
        return True

    return all(
        qual in assignee_qualifications for qual in position.required_qualifications
    )


def calculate_mission_resource_requirements(
    mission: MissionAssignment,
) -> dict[str, Any]:
    """Calculate resource requirements for a mission."""
    base_requirements = {
        MissionType.SEARCH_AND_RESCUE: {
            "personnel": 35,
            "equipment_categories": ["search", "rescue", "medical", "communications"],
            "estimated_duration_hours": 72,
        },
        MissionType.TECHNICAL_RESCUE: {
            "personnel": 45,
            "equipment_categories": ["rescue", "rigging", "cutting", "medical"],
            "estimated_duration_hours": 48,
        },
        MissionType.HAZMAT_RESPONSE: {
            "personnel": 25,
            "equipment_categories": ["hazmat", "decon", "monitoring", "medical"],
            "estimated_duration_hours": 36,
        },
        MissionType.STRUCTURAL_COLLAPSE: {
            "personnel": 60,
            "equipment_categories": ["search", "rescue", "shoring", "heavy_equipment"],
            "estimated_duration_hours": 96,
        },
    }

    requirements = base_requirements.get(
        mission.mission_type, base_requirements[MissionType.SEARCH_AND_RESCUE]
    )

    # Adjust for priority
    priority_multipliers = {"low": 0.7, "medium": 1.0, "high": 1.3, "critical": 1.5}
    multiplier = priority_multipliers.get(mission.priority, 1.0)

    return {
        "recommended_personnel": int(requirements["personnel"] * multiplier),
        "required_equipment_categories": requirements["equipment_categories"],
        "estimated_duration_hours": int(
            requirements["estimated_duration_hours"] * multiplier
        ),
        "resource_intensity": mission.priority,
        "specialized_requirements": get_specialized_requirements(mission.mission_type),
    }


def get_specialized_requirements(mission_type: MissionType) -> list[str]:
    """Get specialized requirements for mission types."""
    requirements = {
        MissionType.SEARCH_AND_RESCUE: [
            "Technical Search Specialist",
            "Canine Teams (2 minimum)",
            "Medical Team Manager",
            "Communications Specialist",
        ],
        MissionType.TECHNICAL_RESCUE: [
            "Heavy Equipment/Rigging Specialist",
            "Rescue Team Manager",
            "Medical Specialist",
            "Safety Officer",
        ],
        MissionType.HAZMAT_RESPONSE: [
            "Hazmat Specialist (2 required)",
            "Medical Team Manager",
            "Decontamination Equipment",
            "Environmental Monitoring",
        ],
        MissionType.STRUCTURAL_COLLAPSE: [
            "Structures Specialist (required)",
            "Heavy Equipment Operator",
            "Rescue Team Manager",
            "Technical Search Specialist",
        ],
    }

    return requirements.get(mission_type, [])
