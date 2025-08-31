"""Operations models for FEMA USAR missions and activities."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


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
    incident_number: Optional[str] = Field(None, description="Incident number")
    location: str = Field(..., description="Mission location")
    gps_coordinates: Optional[Dict[str, float]] = Field(None, description="GPS coordinates")
    
    # Priority and timing
    priority: MissionPriority = MissionPriority.MEDIUM
    status: MissionStatus = MissionStatus.ASSIGNED
    assigned_date: datetime = Field(default_factory=datetime.now)
    required_start_time: Optional[datetime] = Field(None, description="Required start time")
    estimated_duration_hours: Optional[float] = Field(None, description="Estimated duration")
    actual_start_time: Optional[datetime] = Field(None, description="Actual start time")
    actual_completion_time: Optional[datetime] = Field(None, description="Actual completion time")
    
    # Resources
    assigned_personnel: List[str] = Field(default_factory=list, description="Assigned personnel IDs")
    assigned_equipment: List[str] = Field(default_factory=list, description="Assigned equipment IDs")
    required_resources: Dict[str, Any] = Field(default_factory=dict, description="Required resources")
    
    # Mission details
    mission_description: str = Field(..., description="Detailed mission description")
    operational_objectives: List[str] = Field(default_factory=list, description="Mission objectives")
    safety_considerations: List[str] = Field(default_factory=list, description="Safety considerations")
    special_instructions: Optional[str] = Field(None, description="Special instructions")
    
    # Progress tracking
    progress_percent: float = Field(0.0, ge=0, le=100, description="Mission progress percentage")
    milestones_completed: List[str] = Field(default_factory=list, description="Completed milestones")
    current_activities: List[str] = Field(default_factory=list, description="Current activities")
    
    # Communication
    reporting_frequency_minutes: int = Field(30, description="Reporting frequency in minutes")
    next_report_due: Optional[datetime] = Field(None, description="Next report due time")
    communication_plan: Optional[str] = Field(None, description="Communication plan")
    
    # Results and outcomes
    mission_results: Optional[Dict[str, Any]] = Field(None, description="Mission results")
    lessons_learned: Optional[str] = Field(None, description="Lessons learned")
    after_action_items: List[str] = Field(default_factory=list, description="After action items")


class OperationalTimeline(BaseModel):
    """Operational timeline tracking model."""
    timeline_id: str = Field(..., description="Timeline identifier")
    operation_name: str = Field(..., description="Operation name")
    start_time: datetime = Field(..., description="Operation start time")
    end_time: Optional[datetime] = Field(None, description="Operation end time")
    
    # Timeline events
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Timeline events")
    milestones: List[Dict[str, Any]] = Field(default_factory=list, description="Key milestones")
    critical_events: List[Dict[str, Any]] = Field(default_factory=list, description="Critical events")
    
    # Status
    current_phase: str = Field(..., description="Current operational phase")
    overall_status: str = Field("active", description="Overall operation status")
    completion_percent: float = Field(0.0, ge=0, le=100, description="Overall completion percentage")


class SafetyIncident(BaseModel):
    """Safety incident model."""
    incident_id: str = Field(..., description="Incident identifier")
    incident_type: SafetyIncidentType = Field(..., description="Type of incident")
    severity: str = Field(..., description="Incident severity (minor, moderate, major, critical)")
    
    # Incident details
    incident_date: datetime = Field(..., description="Date and time of incident")
    location: str = Field(..., description="Incident location")
    description: str = Field(..., description="Detailed incident description")
    
    # Personnel involved
    personnel_involved: List[str] = Field(default_factory=list, description="Personnel involved")
    injuries: Optional[Dict[str, Any]] = Field(None, description="Injury details if applicable")
    medical_treatment_required: bool = Field(False, description="Whether medical treatment was required")
    
    # Equipment involved
    equipment_involved: List[str] = Field(default_factory=list, description="Equipment involved")
    equipment_damage: Optional[str] = Field(None, description="Equipment damage description")
    
    # Response and investigation
    immediate_actions_taken: List[str] = Field(default_factory=list, description="Immediate actions taken")
    investigation_required: bool = Field(False, description="Whether investigation is required")
    investigation_status: Optional[str] = Field(None, description="Investigation status")
    
    # Prevention and lessons learned
    contributing_factors: List[str] = Field(default_factory=list, description="Contributing factors")
    corrective_actions: List[str] = Field(default_factory=list, description="Corrective actions")
    lessons_learned: Optional[str] = Field(None, description="Lessons learned")
    
    # Reporting
    reported_by: str = Field(..., description="Person reporting the incident")
    reported_to: List[str] = Field(default_factory=list, description="Agencies/people notified")
    follow_up_required: bool = Field(False, description="Whether follow-up is required")


class ResourceUtilization(BaseModel):
    """Resource utilization tracking model."""
    utilization_id: str = Field(..., description="Utilization record identifier")
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="Type of resource (personnel, equipment, etc.)")
    
    # Utilization period
    utilization_start: datetime = Field(..., description="Utilization start time")
    utilization_end: Optional[datetime] = Field(None, description="Utilization end time")
    total_hours: Optional[float] = Field(None, description="Total hours utilized")
    
    # Assignment details
    assigned_to_mission: Optional[str] = Field(None, description="Mission assignment")
    assigned_to_activity: Optional[str] = Field(None, description="Specific activity")
    utilization_purpose: str = Field(..., description="Purpose of utilization")
    
    # Performance metrics
    effectiveness_rating: Optional[str] = Field(None, description="Effectiveness rating")
    efficiency_rating: Optional[str] = Field(None, description="Efficiency rating")
    performance_notes: Optional[str] = Field(None, description="Performance notes")
    
    # Costs
    hourly_cost: Optional[float] = Field(None, description="Hourly cost")
    total_cost: Optional[float] = Field(None, description="Total utilization cost")
    cost_center: Optional[str] = Field(None, description="Cost center")
    
    # Additional tracking
    location: Optional[str] = Field(None, description="Utilization location")
    supervisor: Optional[str] = Field(None, description="Supervising person")
    notes: Optional[str] = Field(None, description="Additional notes")