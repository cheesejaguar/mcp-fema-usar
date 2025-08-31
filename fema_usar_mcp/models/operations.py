"""Operations models for FEMA USAR missions and activities."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MissionStatus(str, Enum):
    """Mission assignment status."""

    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class MissionPriority(str, Enum):
    """Mission priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SafetyIncidentType(str, Enum):
    """Types of safety incidents."""

    INJURY = "injury"
    NEAR_MISS = "near_miss"
    EQUIPMENT_FAILURE = "equipment_failure"
    STRUCTURAL_HAZARD = "structural_hazard"
    ENVIRONMENTAL_HAZARD = "environmental_hazard"
    OPERATIONAL_HAZARD = "operational_hazard"


class MissionAssignment(BaseModel):
    """USAR mission assignment model."""

    mission_id: str = Field(..., description="Unique mission identifier")
    mission_name: str = Field(..., description="Mission name/title")
    mission_type: str = Field(..., description="Type of mission")

    # Assignment details
    requesting_agency: str = Field(..., description="Agency requesting assistance")
    incident_number: str | None = Field(None, description="Incident number")
    location: str = Field(..., description="Mission location")
    gps_coordinates: dict[str, float] | None = Field(
        None, description="GPS coordinates"
    )

    # Priority and timing
    priority: MissionPriority = MissionPriority.MEDIUM
    status: MissionStatus = MissionStatus.ASSIGNED
    assigned_date: datetime = Field(default_factory=datetime.now)
    required_start_time: datetime | None = Field(
        None, description="Required start time"
    )
    estimated_duration_hours: float | None = Field(
        None, description="Estimated duration"
    )
    actual_start_time: datetime | None = Field(None, description="Actual start time")
    actual_completion_time: datetime | None = Field(
        None, description="Actual completion time"
    )

    # Resources
    assigned_personnel: list[str] = Field(
        default_factory=list, description="Assigned personnel IDs"
    )
    assigned_equipment: list[str] = Field(
        default_factory=list, description="Assigned equipment IDs"
    )
    required_resources: dict[str, Any] = Field(
        default_factory=dict, description="Required resources"
    )

    # Mission details
    mission_description: str = Field(..., description="Detailed mission description")
    operational_objectives: list[str] = Field(
        default_factory=list, description="Mission objectives"
    )
    safety_considerations: list[str] = Field(
        default_factory=list, description="Safety considerations"
    )
    special_instructions: str | None = Field(
        None, description="Special instructions"
    )

    # Progress tracking
    progress_percent: float = Field(
        0.0, ge=0, le=100, description="Mission progress percentage"
    )
    milestones_completed: list[str] = Field(
        default_factory=list, description="Completed milestones"
    )
    current_activities: list[str] = Field(
        default_factory=list, description="Current activities"
    )

    # Communication
    reporting_frequency_minutes: int = Field(
        30, description="Reporting frequency in minutes"
    )
    next_report_due: datetime | None = Field(
        None, description="Next report due time"
    )
    communication_plan: str | None = Field(None, description="Communication plan")

    # Results and outcomes
    mission_results: dict[str, Any] | None = Field(
        None, description="Mission results"
    )
    lessons_learned: str | None = Field(None, description="Lessons learned")
    after_action_items: list[str] = Field(
        default_factory=list, description="After action items"
    )


class OperationalTimeline(BaseModel):
    """Operational timeline tracking model."""

    timeline_id: str = Field(..., description="Timeline identifier")
    operation_name: str = Field(..., description="Operation name")
    start_time: datetime = Field(..., description="Operation start time")
    end_time: datetime | None = Field(None, description="Operation end time")

    # Timeline events
    events: list[dict[str, Any]] = Field(
        default_factory=list, description="Timeline events"
    )
    milestones: list[dict[str, Any]] = Field(
        default_factory=list, description="Key milestones"
    )
    critical_events: list[dict[str, Any]] = Field(
        default_factory=list, description="Critical events"
    )

    # Status
    current_phase: str = Field(..., description="Current operational phase")
    overall_status: str = Field("active", description="Overall operation status")
    completion_percent: float = Field(
        0.0, ge=0, le=100, description="Overall completion percentage"
    )


class SafetyIncident(BaseModel):
    """Safety incident model."""

    incident_id: str = Field(..., description="Incident identifier")
    incident_type: SafetyIncidentType = Field(..., description="Type of incident")
    severity: str = Field(
        ..., description="Incident severity (minor, moderate, major, critical)"
    )

    # Incident details
    incident_date: datetime = Field(..., description="Date and time of incident")
    location: str = Field(..., description="Incident location")
    description: str = Field(..., description="Detailed incident description")

    # Personnel involved
    personnel_involved: list[str] = Field(
        default_factory=list, description="Personnel involved"
    )
    injuries: dict[str, Any] | None = Field(
        None, description="Injury details if applicable"
    )
    medical_treatment_required: bool = Field(
        False, description="Whether medical treatment was required"
    )

    # Equipment involved
    equipment_involved: list[str] = Field(
        default_factory=list, description="Equipment involved"
    )
    equipment_damage: str | None = Field(
        None, description="Equipment damage description"
    )

    # Response and investigation
    immediate_actions_taken: list[str] = Field(
        default_factory=list, description="Immediate actions taken"
    )
    investigation_required: bool = Field(
        False, description="Whether investigation is required"
    )
    investigation_status: str | None = Field(
        None, description="Investigation status"
    )

    # Prevention and lessons learned
    contributing_factors: list[str] = Field(
        default_factory=list, description="Contributing factors"
    )
    corrective_actions: list[str] = Field(
        default_factory=list, description="Corrective actions"
    )
    lessons_learned: str | None = Field(None, description="Lessons learned")

    # Reporting
    reported_by: str = Field(..., description="Person reporting the incident")
    reported_to: list[str] = Field(
        default_factory=list, description="Agencies/people notified"
    )
    follow_up_required: bool = Field(False, description="Whether follow-up is required")


class ResourceUtilization(BaseModel):
    """Resource utilization tracking model."""

    utilization_id: str = Field(..., description="Utilization record identifier")
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(
        ..., description="Type of resource (personnel, equipment, etc.)"
    )

    # Utilization period
    utilization_start: datetime = Field(..., description="Utilization start time")
    utilization_end: datetime | None = Field(
        None, description="Utilization end time"
    )
    total_hours: float | None = Field(None, description="Total hours utilized")

    # Assignment details
    assigned_to_mission: str | None = Field(None, description="Mission assignment")
    assigned_to_activity: str | None = Field(None, description="Specific activity")
    utilization_purpose: str = Field(..., description="Purpose of utilization")

    # Performance metrics
    effectiveness_rating: str | None = Field(
        None, description="Effectiveness rating"
    )
    efficiency_rating: str | None = Field(None, description="Efficiency rating")
    performance_notes: str | None = Field(None, description="Performance notes")

    # Costs
    hourly_cost: float | None = Field(None, description="Hourly cost")
    total_cost: float | None = Field(None, description="Total utilization cost")
    cost_center: str | None = Field(None, description="Cost center")

    # Additional tracking
    location: str | None = Field(None, description="Utilization location")
    supervisor: str | None = Field(None, description="Supervising person")
    notes: str | None = Field(None, description="Additional notes")
