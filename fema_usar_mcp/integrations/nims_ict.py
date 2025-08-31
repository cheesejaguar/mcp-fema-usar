"""NIMS Incident Command Table (ICT) integration module.

Provides integration with NIMS ICT system for incident command structure,
resource ordering, and operational coordination.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NIMSCommandLevel(Enum):
    """NIMS command structure levels."""
    INCIDENT_COMMANDER = "incident_commander"
    DEPUTY_IC = "deputy_ic"
    COMMAND_STAFF = "command_staff"
    SECTION_CHIEF = "section_chief"
    BRANCH_DIRECTOR = "branch_director"
    DIVISION_SUPERVISOR = "division_supervisor"
    GROUP_SUPERVISOR = "group_supervisor"
    UNIT_LEADER = "unit_leader"
    TASK_FORCE_LEADER = "task_force_leader"
    STRIKE_TEAM_LEADER = "strike_team_leader"


class NIMSResourceKind(Enum):
    """NIMS resource kind classifications."""
    PERSONNEL = "personnel"
    TEAMS = "teams"
    EQUIPMENT = "equipment"
    SUPPLIES = "supplies"
    FACILITIES = "facilities"
    AIRCRAFT = "aircraft"
    WATERCRAFT = "watercraft"


class NIMSResourceStatus(Enum):
    """NIMS resource status codes."""
    ASSIGNED = "assigned"
    AVAILABLE = "available" 
    OUT_OF_SERVICE = "out_of_service"
    COMMITTED = "committed"
    STAGING = "staging"
    TRANSPORTING = "transporting"


@dataclass
class NIMSICTCredentials:
    """NIMS ICT system credentials."""
    username: str
    password: str
    organization_id: str
    base_url: str = "https://ict.nims.gov/api/v3"
    timeout: int = 30


class NIMSICSPosition(BaseModel):
    """NIMS ICS organizational position."""
    position_id: str = Field(..., description="Unique position identifier")
    position_title: str = Field(..., description="ICS position title")
    command_level: NIMSCommandLevel = Field(..., description="Command structure level")
    reports_to: Optional[str] = Field(None, description="Supervisor position ID")
    assigned_person: Optional[str] = Field(None, description="Assigned person name")
    qualifications: List[str] = Field(default_factory=list, description="Required qualifications")
    responsibilities: List[str] = Field(default_factory=list, description="Position responsibilities")
    status: str = Field("vacant", description="Position status")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Contact information")


class NIMSResourceOrder(BaseModel):
    """NIMS resource order model."""
    order_id: str = Field(..., description="Resource order identifier")
    incident_id: str = Field(..., description="Associated incident ID")
    requesting_agency: str = Field(..., description="Requesting agency")
    resource_kind: NIMSResourceKind = Field(..., description="Kind of resource")
    resource_type: str = Field(..., description="Specific resource type")
    quantity: int = Field(..., description="Quantity requested")
    priority: str = Field(..., description="Order priority")
    requested_arrival: datetime = Field(..., description="Requested arrival time")
    delivery_location: Dict[str, Any] = Field(..., description="Delivery location")
    special_requirements: Optional[str] = Field(None, description="Special requirements")
    order_status: str = Field("pending", description="Order status")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")


class NIMSOperationalPeriod(BaseModel):
    """NIMS operational period model."""
    period_id: str = Field(..., description="Operational period identifier")
    incident_id: str = Field(..., description="Associated incident ID")
    period_number: int = Field(..., description="Sequential period number")
    start_time: datetime = Field(..., description="Period start time")
    end_time: datetime = Field(..., description="Period end time")
    objectives: List[str] = Field(default_factory=list, description="Period objectives")
    strategies: List[str] = Field(default_factory=list, description="Strategies employed")
    resource_assignments: List[Dict[str, Any]] = Field(default_factory=list, description="Resource assignments")
    weather_forecast: Optional[Dict[str, Any]] = Field(None, description="Weather forecast")
    safety_concerns: List[str] = Field(default_factory=list, description="Safety concerns")


class NIMSICTClient:
    """NIMS ICT system API client."""
    
    def __init__(self, credentials: NIMSICTCredentials):
        """Initialize NIMS ICT client.
        
        Args:
            credentials: NIMS ICT credentials
        """
        self.credentials = credentials
        self.session: Optional[httpx.AsyncClient] = None
        self._auth_token: Optional[str] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
        
    async def _initialize_session(self):
        """Initialize HTTP session and authenticate."""
        self.session = httpx.AsyncClient(
            base_url=self.credentials.base_url,
            timeout=httpx.Timeout(self.credentials.timeout),
            headers={"User-Agent": "FEMA-USAR-MCP/1.0"}
        )
        await self._authenticate()
        
    async def _close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.aclose()
            self.session = None
            
    async def _authenticate(self):
        """Authenticate with NIMS ICT system."""
        try:
            auth_data = {
                "username": self.credentials.username,
                "password": self.credentials.password,
                "organization_id": self.credentials.organization_id
            }
            
            response = await self.session.post("/auth/login", json=auth_data)
            response.raise_for_status()
            
            auth_response = response.json()
            self._auth_token = auth_response["access_token"]
            
            # Update session headers
            self.session.headers.update({
                "Authorization": f"Bearer {self._auth_token}"
            })
            
            logger.info("Successfully authenticated with NIMS ICT")
            
        except Exception as e:
            logger.error(f"NIMS ICT authentication failed: {str(e)}")
            raise
            
    async def get_incident_organization(self, incident_id: str) -> List[NIMSICSPosition]:
        """Get ICS organizational chart for incident.
        
        Args:
            incident_id: NIMS incident identifier
            
        Returns:
            List of ICS positions
        """
        try:
            response = await self.session.get(f"/incidents/{incident_id}/organization")
            response.raise_for_status()
            
            org_data = response.json()
            positions = [NIMSICSPosition(**pos) for pos in org_data.get("positions", [])]
            
            logger.info(f"Retrieved {len(positions)} ICS positions for incident {incident_id}")
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get NIMS incident organization: {str(e)}")
            raise
            
    async def update_position_assignment(
        self,
        incident_id: str,
        position_id: str,
        assigned_person: str,
        contact_info: Dict[str, str]
    ) -> bool:
        """Update ICS position assignment.
        
        Args:
            incident_id: NIMS incident identifier
            position_id: ICS position identifier
            assigned_person: Name of assigned person
            contact_info: Contact information
            
        Returns:
            True if update successful
        """
        try:
            assignment_data = {
                "assigned_person": assigned_person,
                "contact_info": contact_info,
                "assigned_at": datetime.now(timezone.utc).isoformat(),
                "assigned_by": "FEMA-USAR-MCP"
            }
            
            response = await self.session.put(
                f"/incidents/{incident_id}/positions/{position_id}/assignment",
                json=assignment_data
            )
            response.raise_for_status()
            
            logger.info(f"Updated ICS position {position_id} assignment to {assigned_person}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update NIMS position assignment: {str(e)}")
            return False
            
    async def submit_resource_order(
        self,
        incident_id: str,
        resource_kind: NIMSResourceKind,
        resource_type: str,
        quantity: int,
        delivery_location: Dict[str, Any],
        requested_arrival: datetime,
        priority: str = "routine",
        special_requirements: Optional[str] = None
    ) -> NIMSResourceOrder:
        """Submit resource order to NIMS ICT.
        
        Args:
            incident_id: NIMS incident identifier
            resource_kind: Kind of resource
            resource_type: Specific resource type
            quantity: Quantity requested
            delivery_location: Delivery location details
            requested_arrival: Requested arrival time
            priority: Order priority
            special_requirements: Special requirements
            
        Returns:
            Created resource order
        """
        try:
            order_data = {
                "incident_id": incident_id,
                "resource_kind": resource_kind.value,
                "resource_type": resource_type,
                "quantity": quantity,
                "delivery_location": delivery_location,
                "requested_arrival": requested_arrival.isoformat(),
                "priority": priority,
                "requesting_agency": "FEMA-USAR-MCP",
                "order_date": datetime.now(timezone.utc).isoformat()
            }
            
            if special_requirements:
                order_data["special_requirements"] = special_requirements
                
            response = await self.session.post(f"/incidents/{incident_id}/resource-orders", json=order_data)
            response.raise_for_status()
            
            order_response = response.json()
            resource_order = NIMSResourceOrder(**order_response)
            
            logger.info(f"Submitted NIMS resource order: {resource_order.order_id}")
            return resource_order
            
        except Exception as e:
            logger.error(f"Failed to submit NIMS resource order: {str(e)}")
            raise
            
    async def update_resource_status(
        self,
        incident_id: str,
        resource_id: str,
        status: NIMSResourceStatus,
        location: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update resource status in NIMS ICT.
        
        Args:
            incident_id: NIMS incident identifier
            resource_id: Resource identifier
            status: New resource status
            location: Current location
            notes: Status update notes
            
        Returns:
            True if update successful
        """
        try:
            status_data = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": "FEMA-USAR-MCP"
            }
            
            if location:
                status_data["location"] = location
            if notes:
                status_data["notes"] = notes
                
            response = await self.session.put(
                f"/incidents/{incident_id}/resources/{resource_id}/status",
                json=status_data
            )
            response.raise_for_status()
            
            logger.info(f"Updated NIMS resource {resource_id} status to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update NIMS resource status: {str(e)}")
            return False
            
    async def create_operational_period(
        self,
        incident_id: str,
        period_number: int,
        start_time: datetime,
        end_time: datetime,
        objectives: List[str],
        strategies: List[str]
    ) -> NIMSOperationalPeriod:
        """Create operational period in NIMS ICT.
        
        Args:
            incident_id: NIMS incident identifier
            period_number: Sequential period number
            start_time: Period start time
            end_time: Period end time
            objectives: Period objectives
            strategies: Strategies to employ
            
        Returns:
            Created operational period
        """
        try:
            period_data = {
                "incident_id": incident_id,
                "period_number": period_number,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "objectives": objectives,
                "strategies": strategies,
                "created_by": "FEMA-USAR-MCP",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = await self.session.post(f"/incidents/{incident_id}/operational-periods", json=period_data)
            response.raise_for_status()
            
            period_response = response.json()
            operational_period = NIMSOperationalPeriod(**period_response)
            
            logger.info(f"Created NIMS operational period: {operational_period.period_id}")
            return operational_period
            
        except Exception as e:
            logger.error(f"Failed to create NIMS operational period: {str(e)}")
            raise
            
    async def submit_situation_report(
        self,
        incident_id: str,
        report_type: str,
        report_data: Dict[str, Any]
    ) -> bool:
        """Submit situation report to NIMS ICT.
        
        Args:
            incident_id: NIMS incident identifier
            report_type: Type of situation report
            report_data: Report content data
            
        Returns:
            True if submission successful
        """
        try:
            report_payload = {
                "incident_id": incident_id,
                "report_type": report_type,
                "report_data": report_data,
                "submitted_by": "FEMA-USAR-MCP",
                "submitted_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = await self.session.post(f"/incidents/{incident_id}/reports", json=report_payload)
            response.raise_for_status()
            
            logger.info(f"Submitted NIMS situation report for incident {incident_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit NIMS situation report: {str(e)}")
            return False


class NIMSICTIntegrationManager:
    """Manager for NIMS ICT integration operations."""
    
    def __init__(self, credentials: NIMSICTCredentials):
        """Initialize NIMS ICT integration manager.
        
        Args:
            credentials: NIMS ICT credentials
        """
        self.credentials = credentials
        self._client: Optional[NIMSICTClient] = None
        
    async def initialize(self):
        """Initialize NIMS ICT integration."""
        try:
            self._client = NIMSICTClient(self.credentials)
            await self._client.__aenter__()
            logger.info("NIMS ICT integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NIMS ICT integration: {str(e)}")
            raise
            
    async def shutdown(self):
        """Shutdown NIMS ICT integration."""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
            logger.info("NIMS ICT integration shutdown complete")
            
    @property
    def client(self) -> NIMSICTClient:
        """Get NIMS ICT client instance."""
        if not self._client:
            raise RuntimeError("NIMS ICT integration not initialized")
        return self._client
        
    async def sync_incident_organization(
        self,
        incident_id: str,
        task_force_personnel: List[Dict[str, Any]]
    ) -> bool:
        """Synchronize task force personnel with NIMS ICS organization.
        
        Args:
            incident_id: NIMS incident identifier
            task_force_personnel: Task force personnel assignments
            
        Returns:
            True if synchronization successful
        """
        try:
            # Get current ICS organization
            ics_positions = await self.client.get_incident_organization(incident_id)
            
            # Map task force personnel to ICS positions
            for person in task_force_personnel:
                ics_position = self._map_to_ics_position(person, ics_positions)
                if ics_position:
                    await self.client.update_position_assignment(
                        incident_id,
                        ics_position.position_id,
                        person["name"],
                        person.get("contact_info", {})
                    )
            
            logger.info(f"Synchronized {len(task_force_personnel)} personnel with NIMS ICS")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync incident organization with NIMS ICT: {str(e)}")
            return False
            
    def _map_to_ics_position(
        self,
        person: Dict[str, Any],
        ics_positions: List[NIMSICSPosition]
    ) -> Optional[NIMSICSPosition]:
        """Map task force person to appropriate ICS position.
        
        Args:
            person: Task force personnel data
            ics_positions: Available ICS positions
            
        Returns:
            Matching ICS position or None
        """
        position_title = person.get("position", "").lower()
        
        # Position mapping logic
        position_mappings = {
            "task force leader": "task_force_leader",
            "safety officer": "safety_officer", 
            "search team manager": "group_supervisor",
            "rescue team manager": "group_supervisor",
            "medical team manager": "group_supervisor"
        }
        
        mapped_title = position_mappings.get(position_title)
        if not mapped_title:
            return None
            
        # Find matching vacant ICS position
        for ics_pos in ics_positions:
            if (ics_pos.position_title.lower().replace(" ", "_") == mapped_title and
                ics_pos.status == "vacant"):
                return ics_pos
                
        return None


# Factory function for creating NIMS ICT integration
def create_nims_ict_integration(
    username: str,
    password: str,
    organization_id: str,
    base_url: str = "https://ict.nims.gov/api/v3"
) -> NIMSICTIntegrationManager:
    """Create NIMS ICT integration manager.
    
    Args:
        username: NIMS ICT username
        password: NIMS ICT password  
        organization_id: Organization identifier
        base_url: NIMS ICT API base URL
        
    Returns:
        Configured NIMS ICT integration manager
    """
    credentials = NIMSICTCredentials(
        username=username,
        password=password,
        organization_id=organization_id,
        base_url=base_url
    )
    return NIMSICTIntegrationManager(credentials)