"""Equipment models for FEMA USAR operations."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EquipmentStatus(str, Enum):
    """Equipment operational status."""

    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    OUT_OF_SERVICE = "out_of_service"
    UNAVAILABLE = "unavailable"


class EquipmentCategory(str, Enum):
    """Equipment categories for USAR operations."""

    SEARCH = "search"
    RESCUE = "rescue"
    MEDICAL = "medical"
    COMMUNICATIONS = "communications"
    LOGISTICS = "logistics"
    TOOLS = "tools"
    SAFETY = "safety"
    STRUCTURAL = "structural"
    HAZMAT = "hazmat"


class DeploymentStatus(str, Enum):
    """Equipment deployment status."""

    AVAILABLE = "available"
    DEPLOYED = "deployed"
    CHECKED_OUT = "checked_out"
    IN_TRANSIT = "in_transit"
    RETURNED = "returned"


class MaintenanceRecord(BaseModel):
    """Equipment maintenance record."""

    maintenance_id: str = Field(..., description="Maintenance record identifier")
    equipment_id: str = Field(..., description="Equipment identifier")
    maintenance_type: str = Field(
        ..., description="Type of maintenance (preventive, corrective, etc.)"
    )
    maintenance_date: datetime = Field(
        ..., description="Date maintenance was performed"
    )
    performed_by: str = Field(
        ..., description="Person/organization performing maintenance"
    )
    description: str = Field(..., description="Description of maintenance performed")
    parts_used: list[str] | None = Field(
        default_factory=list, description="Parts used in maintenance"
    )
    cost: float | None = Field(None, description="Cost of maintenance")
    next_maintenance_due: datetime | None = Field(
        None, description="Next scheduled maintenance"
    )
    notes: str | None = Field(None, description="Additional notes")


class EquipmentModel(BaseModel):
    """Complete equipment model for USAR operations."""

    equipment_id: str = Field(..., description="Unique equipment identifier")
    equipment_name: str = Field(..., description="Equipment name/description")
    category: EquipmentCategory = Field(..., description="Equipment category")
    subcategory: str | None = Field(None, description="Equipment subcategory")

    # Basic information
    manufacturer: str | None = Field(None, description="Equipment manufacturer")
    model: str | None = Field(None, description="Equipment model")
    serial_number: str | None = Field(None, description="Serial number")
    purchase_date: datetime | None = Field(None, description="Purchase date")
    purchase_cost: float | None = Field(None, description="Purchase cost")

    # Status and condition
    status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    deployment_status: DeploymentStatus = DeploymentStatus.AVAILABLE
    condition: str = Field("excellent", description="Physical condition")
    deployment_ready: bool = Field(True, description="Ready for deployment")

    # Location and assignment
    current_location: str | None = Field(None, description="Current location")
    assigned_to: str | None = Field(None, description="Person/team assigned to")
    home_cache: str = Field(..., description="Home cache/storage location")

    # Maintenance
    maintenance_records: list[MaintenanceRecord] = Field(default_factory=list)
    last_inspection: datetime | None = Field(None, description="Last inspection date")
    next_maintenance: datetime | None = Field(
        None, description="Next scheduled maintenance"
    )
    maintenance_interval_days: int | None = Field(
        None, description="Maintenance interval in days"
    )

    # Specifications
    weight_pounds: float | None = Field(None, description="Weight in pounds")
    dimensions: dict[str, float] | None = Field(
        None, description="Dimensions (length, width, height)"
    )
    power_requirements: str | None = Field(None, description="Power requirements")
    operating_temperature_range: str | None = Field(
        None, description="Operating temperature range"
    )

    # Deployment tracking
    total_deployments: int = Field(0, description="Total number of deployments")
    total_hours_used: float | None = Field(None, description="Total operational hours")
    last_deployment_date: datetime | None = Field(
        None, description="Last deployment date"
    )

    # Safety and compliance
    safety_certified: bool = Field(True, description="Safety certification current")
    safety_certification_date: datetime | None = Field(
        None, description="Safety certification date"
    )
    safety_certification_expiry: datetime | None = Field(
        None, description="Safety certification expiry"
    )

    # Additional metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    notes: str | None = Field(None, description="Additional notes")
    tags: list[str] = Field(default_factory=list, description="Equipment tags/keywords")
