"""Personnel models for FEMA USAR operations."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PersonnelStatus(str, Enum):
    """Personnel operational status."""

    OPERATIONAL = "operational"
    REST_REHABILITATION = "rest_rehabilitation"
    MEDICAL_EVALUATION = "medical_evaluation"
    TRANSPORTATION = "transportation"
    UNAVAILABLE = "unavailable"


class PersonnelQualification(BaseModel):
    """Personnel qualification model."""

    qualification_id: str = Field(..., description="Qualification identifier")
    qualification_name: str = Field(..., description="Official qualification name")
    certification_date: datetime = Field(
        ..., description="Date qualification was earned"
    )
    expiration_date: datetime | None = Field(
        None, description="Qualification expiration date"
    )
    certifying_agency: str = Field(
        ..., description="Agency that provided certification"
    )
    is_current: bool = Field(True, description="Whether qualification is current")


class PersonnelLocation(BaseModel):
    """Personnel location tracking model."""

    person_id: str = Field(..., description="Personnel identifier")
    location_name: str = Field(..., description="Human-readable location")
    gps_coordinates: dict[str, float] | None = Field(
        None, description="GPS coordinates"
    )
    location_type: str = Field(
        ..., description="Type of location (command_post, operations_area, etc.)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Location timestamp"
    )
    accuracy_meters: float | None = Field(None, description="GPS accuracy in meters")


class PositionAssignment(BaseModel):
    """Personnel position assignment model."""

    assignment_id: str = Field(..., description="Assignment identifier")
    person_id: str = Field(..., description="Personnel identifier")
    position_name: str = Field(..., description="ICS position name")
    functional_group: str = Field(
        ..., description="Functional group (Command, Search, etc.)"
    )
    assignment_start: datetime = Field(..., description="Assignment start time")
    assignment_end: datetime | None = Field(None, description="Assignment end time")
    is_primary: bool = Field(True, description="Whether this is primary assignment")
    supervisor_id: str | None = Field(None, description="Supervisor personnel ID")


class PersonnelModel(BaseModel):
    """Complete personnel model."""

    person_id: str = Field(..., description="Unique personnel identifier")
    name: str = Field(..., description="Personnel name")
    task_force: str = Field(..., description="Task force assignment")
    home_agency: str = Field(..., description="Home agency/department")

    # Status and location
    current_status: PersonnelStatus = PersonnelStatus.OPERATIONAL
    current_location: PersonnelLocation | None = None
    current_assignment: PositionAssignment | None = None

    # Qualifications
    qualifications: list[PersonnelQualification] = Field(default_factory=list)
    primary_specialty: str = Field(..., description="Primary operational specialty")

    # Contact information
    radio_call_sign: str | None = Field(None, description="Radio call sign")
    cell_phone: str | None = Field(None, description="Cell phone number")
    emergency_contact: dict[str, str] | None = Field(
        None, description="Emergency contact info"
    )

    # Health and fitness
    medical_cleared: bool = Field(True, description="Medically cleared for operations")
    fitness_level: str = Field("excellent", description="Physical fitness level")
    last_medical_eval: datetime | None = Field(
        None, description="Last medical evaluation"
    )

    # Deployment tracking
    deployment_ready: bool = Field(True, description="Ready for deployment")
    last_deployment: datetime | None = Field(None, description="Last deployment date")
    total_deployments: int = Field(0, description="Total number of deployments")

    # Additional metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    notes: str | None = Field(None, description="Additional notes")
