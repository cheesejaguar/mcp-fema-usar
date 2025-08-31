"""Equipment models for FEMA USAR operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


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
    maintenance_type: str = Field(..., description="Type of maintenance (preventive, corrective, etc.)")
    maintenance_date: datetime = Field(..., description="Date maintenance was performed")
    performed_by: str = Field(..., description="Person/organization performing maintenance")
    description: str = Field(..., description="Description of maintenance performed")
    parts_used: Optional[List[str]] = Field(default_factory=list, description="Parts used in maintenance")
    cost: Optional[float] = Field(None, description="Cost of maintenance")
    next_maintenance_due: Optional[datetime] = Field(None, description="Next scheduled maintenance")
    notes: Optional[str] = Field(None, description="Additional notes")


class EquipmentModel(BaseModel):
    """Complete equipment model for USAR operations."""
    equipment_id: str = Field(..., description="Unique equipment identifier")
    equipment_name: str = Field(..., description="Equipment name/description")
    category: EquipmentCategory = Field(..., description="Equipment category")
    subcategory: Optional[str] = Field(None, description="Equipment subcategory")
    
    # Basic information
    manufacturer: Optional[str] = Field(None, description="Equipment manufacturer")
    model: Optional[str] = Field(None, description="Equipment model")
    serial_number: Optional[str] = Field(None, description="Serial number")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    purchase_cost: Optional[float] = Field(None, description="Purchase cost")
    
    # Status and condition
    status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    deployment_status: DeploymentStatus = DeploymentStatus.AVAILABLE
    condition: str = Field("excellent", description="Physical condition")
    deployment_ready: bool = Field(True, description="Ready for deployment")
    
    # Location and assignment
    current_location: Optional[str] = Field(None, description="Current location")
    assigned_to: Optional[str] = Field(None, description="Person/team assigned to")
    home_cache: str = Field(..., description="Home cache/storage location")
    
    # Maintenance
    maintenance_records: List[MaintenanceRecord] = Field(default_factory=list)
    last_inspection: Optional[datetime] = Field(None, description="Last inspection date")
    next_maintenance: Optional[datetime] = Field(None, description="Next scheduled maintenance")
    maintenance_interval_days: Optional[int] = Field(None, description="Maintenance interval in days")
    
    # Specifications
    weight_pounds: Optional[float] = Field(None, description="Weight in pounds")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Dimensions (length, width, height)")
    power_requirements: Optional[str] = Field(None, description="Power requirements")
    operating_temperature_range: Optional[str] = Field(None, description="Operating temperature range")
    
    # Deployment tracking
    total_deployments: int = Field(0, description="Total number of deployments")
    total_hours_used: Optional[float] = Field(None, description="Total operational hours")
    last_deployment_date: Optional[datetime] = Field(None, description="Last deployment date")
    
    # Safety and compliance
    safety_certified: bool = Field(True, description="Safety certification current")
    safety_certification_date: Optional[datetime] = Field(None, description="Safety certification date")
    safety_certification_expiry: Optional[datetime] = Field(None, description="Safety certification expiry")
    
    # Additional metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: List[str] = Field(default_factory=list, description="Equipment tags/keywords")