"""FEMA Incident Resource Inventory System (IRIS) integration module.

Provides real-time integration with FEMA IRIS for resource tracking,
deployment coordination, and federal asset management.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IRISResourceStatus(Enum):
    """FEMA IRIS resource status codes."""
    AVAILABLE = "available"
    DEPLOYED = "deployed" 
    IN_TRANSIT = "in_transit"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class IRISResourceType(Enum):
    """FEMA IRIS resource types."""
    PERSONNEL = "personnel"
    EQUIPMENT = "equipment"
    FACILITY = "facility"
    VEHICLE = "vehicle"
    AIRCRAFT = "aircraft"
    VESSEL = "vessel"


@dataclass
class IRISCredentials:
    """FEMA IRIS API credentials and configuration."""
    api_key: str
    secret_key: str
    base_url: str = "https://iris.fema.gov/api/v2"
    timeout: int = 30
    max_retries: int = 3


class IRISResource(BaseModel):
    """FEMA IRIS resource model."""
    resource_id: str = Field(..., description="Unique IRIS resource identifier")
    resource_type: IRISResourceType = Field(..., description="Type of resource")
    name: str = Field(..., description="Resource name/description")
    status: IRISResourceStatus = Field(..., description="Current resource status")
    location: Dict[str, Any] = Field(..., description="Current resource location")
    capabilities: List[str] = Field(default_factory=list, description="Resource capabilities")
    availability_date: Optional[datetime] = Field(None, description="Available deployment date")
    owner_agency: str = Field(..., description="Owning agency")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Contact information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class IRISDeploymentOrder(BaseModel):
    """FEMA IRIS deployment order model."""
    order_id: str = Field(..., description="Deployment order ID")
    incident_id: str = Field(..., description="Associated incident ID")
    requesting_agency: str = Field(..., description="Agency requesting resources")
    resources_requested: List[Dict[str, Any]] = Field(..., description="Requested resources")
    priority: str = Field(..., description="Deployment priority")
    deployment_location: Dict[str, Any] = Field(..., description="Deployment location")
    requested_arrival: datetime = Field(..., description="Requested arrival time")
    special_instructions: Optional[str] = Field(None, description="Special deployment instructions")


class FEMAIRISClient:
    """FEMA IRIS API client for resource management integration."""
    
    def __init__(self, credentials: IRISCredentials):
        """Initialize FEMA IRIS client.
        
        Args:
            credentials: IRIS API credentials and configuration
        """
        self.credentials = credentials
        self.session: Optional[httpx.AsyncClient] = None
        self._auth_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        
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
        """Authenticate with FEMA IRIS API."""
        try:
            auth_data = {
                "api_key": self.credentials.api_key,
                "secret_key": self.credentials.secret_key,
                "grant_type": "client_credentials"
            }
            
            response = await self.session.post("/auth/token", json=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self._auth_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires = datetime.now(timezone.utc).timestamp() + expires_in
            
            # Update session headers with auth token
            self.session.headers.update({
                "Authorization": f"Bearer {self._auth_token}"
            })
            
            logger.info("Successfully authenticated with FEMA IRIS")
            
        except Exception as e:
            logger.error(f"FEMA IRIS authentication failed: {str(e)}")
            raise
            
    async def _ensure_authenticated(self):
        """Ensure valid authentication token."""
        if not self._auth_token or not self._token_expires:
            await self._authenticate()
            return
            
        # Check if token is about to expire (5 minute buffer)
        if datetime.now(timezone.utc).timestamp() + 300 > self._token_expires:
            await self._authenticate()
            
    async def get_available_resources(
        self,
        resource_type: Optional[IRISResourceType] = None,
        location_radius_miles: Optional[int] = None,
        center_lat: Optional[float] = None,
        center_lon: Optional[float] = None,
        capabilities: Optional[List[str]] = None
    ) -> List[IRISResource]:
        """Get available FEMA resources from IRIS.
        
        Args:
            resource_type: Filter by resource type
            location_radius_miles: Search radius in miles
            center_lat: Center latitude for radius search
            center_lon: Center longitude for radius search  
            capabilities: Required capabilities filter
            
        Returns:
            List of available IRIS resources
        """
        await self._ensure_authenticated()
        
        params = {"status": "available"}
        if resource_type:
            params["type"] = resource_type.value
        if location_radius_miles and center_lat and center_lon:
            params.update({
                "radius": location_radius_miles,
                "lat": center_lat,
                "lon": center_lon
            })
        if capabilities:
            params["capabilities"] = ",".join(capabilities)
            
        try:
            response = await self.session.get("/resources", params=params)
            response.raise_for_status()
            
            resources_data = response.json()
            resources = [IRISResource(**resource) for resource in resources_data.get("resources", [])]
            
            logger.info(f"Retrieved {len(resources)} available resources from FEMA IRIS")
            return resources
            
        except Exception as e:
            logger.error(f"Failed to retrieve FEMA IRIS resources: {str(e)}")
            raise
            
    async def request_resource_deployment(
        self,
        incident_id: str,
        resource_ids: List[str],
        deployment_location: Dict[str, Any],
        requested_arrival: datetime,
        priority: str = "medium",
        special_instructions: Optional[str] = None
    ) -> IRISDeploymentOrder:
        """Request deployment of FEMA resources.
        
        Args:
            incident_id: FEMA incident identifier
            resource_ids: List of IRIS resource IDs to deploy
            deployment_location: Deployment location details
            requested_arrival: Requested arrival datetime
            priority: Deployment priority (low, medium, high, critical)
            special_instructions: Additional deployment instructions
            
        Returns:
            IRIS deployment order
        """
        await self._ensure_authenticated()
        
        deployment_data = {
            "incident_id": incident_id,
            "resource_ids": resource_ids,
            "deployment_location": deployment_location,
            "requested_arrival": requested_arrival.isoformat(),
            "priority": priority,
            "requesting_agency": "FEMA-USAR-MCP"
        }
        
        if special_instructions:
            deployment_data["special_instructions"] = special_instructions
            
        try:
            response = await self.session.post("/deployments", json=deployment_data)
            response.raise_for_status()
            
            order_data = response.json()
            deployment_order = IRISDeploymentOrder(**order_data)
            
            logger.info(f"Created FEMA IRIS deployment order: {deployment_order.order_id}")
            return deployment_order
            
        except Exception as e:
            logger.error(f"Failed to create FEMA IRIS deployment order: {str(e)}")
            raise
            
    async def update_resource_status(
        self,
        resource_id: str,
        status: IRISResourceStatus,
        location: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update FEMA IRIS resource status.
        
        Args:
            resource_id: IRIS resource identifier
            status: New resource status
            location: Updated location information
            notes: Status update notes
            
        Returns:
            True if update successful
        """
        await self._ensure_authenticated()
        
        update_data = {
            "status": status.value,
            "updated_by": "FEMA-USAR-MCP",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if location:
            update_data["location"] = location
        if notes:
            update_data["notes"] = notes
            
        try:
            response = await self.session.put(f"/resources/{resource_id}/status", json=update_data)
            response.raise_for_status()
            
            logger.info(f"Updated FEMA IRIS resource {resource_id} status to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update FEMA IRIS resource status: {str(e)}")
            return False
            
    async def get_deployment_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of FEMA resource deployment.
        
        Args:
            order_id: IRIS deployment order ID
            
        Returns:
            Deployment status information
        """
        await self._ensure_authenticated()
        
        try:
            response = await self.session.get(f"/deployments/{order_id}")
            response.raise_for_status()
            
            deployment_status = response.json()
            logger.info(f"Retrieved FEMA IRIS deployment status for order {order_id}")
            return deployment_status
            
        except Exception as e:
            logger.error(f"Failed to get FEMA IRIS deployment status: {str(e)}")
            raise
            
    async def submit_situation_report(
        self,
        incident_id: str,
        report_data: Dict[str, Any]
    ) -> bool:
        """Submit situation report to FEMA IRIS.
        
        Args:
            incident_id: FEMA incident identifier
            report_data: Situation report data
            
        Returns:
            True if submission successful
        """
        await self._ensure_authenticated()
        
        report_payload = {
            "incident_id": incident_id,
            "report_type": "situation_report",
            "submitted_by": "FEMA-USAR-MCP",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "data": report_data
        }
        
        try:
            response = await self.session.post("/reports", json=report_payload)
            response.raise_for_status()
            
            logger.info(f"Submitted situation report to FEMA IRIS for incident {incident_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit FEMA IRIS situation report: {str(e)}")
            return False


class IRISIntegrationManager:
    """Manager for FEMA IRIS integration operations."""
    
    def __init__(self, credentials: IRISCredentials):
        """Initialize IRIS integration manager.
        
        Args:
            credentials: FEMA IRIS API credentials
        """
        self.credentials = credentials
        self._client: Optional[FEMAIRISClient] = None
        
    async def initialize(self):
        """Initialize IRIS integration."""
        try:
            self._client = FEMAIRISClient(self.credentials)
            await self._client.__aenter__()
            logger.info("FEMA IRIS integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FEMA IRIS integration: {str(e)}")
            raise
            
    async def shutdown(self):
        """Shutdown IRIS integration."""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
            logger.info("FEMA IRIS integration shutdown complete")
            
    @property
    def client(self) -> FEMAIRISClient:
        """Get IRIS client instance."""
        if not self._client:
            raise RuntimeError("IRIS integration not initialized")
        return self._client
        
    async def sync_task_force_resources(
        self,
        task_force_id: str,
        resources: List[Dict[str, Any]]
    ) -> bool:
        """Synchronize task force resources with FEMA IRIS.
        
        Args:
            task_force_id: Task force identifier
            resources: List of task force resources
            
        Returns:
            True if synchronization successful
        """
        try:
            # Convert local resources to IRIS format and update
            for resource in resources:
                iris_resource = self._convert_to_iris_resource(task_force_id, resource)
                await self.client.update_resource_status(
                    iris_resource["resource_id"],
                    IRISResourceStatus(iris_resource["status"]),
                    iris_resource.get("location"),
                    f"Updated by {task_force_id} MCP system"
                )
            
            logger.info(f"Synchronized {len(resources)} resources for {task_force_id} with FEMA IRIS")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync task force resources with FEMA IRIS: {str(e)}")
            return False
            
    def _convert_to_iris_resource(self, task_force_id: str, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Convert local resource to IRIS resource format.
        
        Args:
            task_force_id: Task force identifier
            resource: Local resource data
            
        Returns:
            IRIS-formatted resource data
        """
        return {
            "resource_id": f"{task_force_id}-{resource.get('id', 'unknown')}",
            "resource_type": resource.get("type", "equipment"),
            "name": resource.get("name", "Unknown Resource"),
            "status": resource.get("status", "available"),
            "location": {
                "latitude": resource.get("latitude"),
                "longitude": resource.get("longitude"),
                "address": resource.get("location", "Unknown Location")
            },
            "capabilities": resource.get("capabilities", []),
            "owner_agency": task_force_id
        }


# Factory function for creating IRIS integration
def create_iris_integration(
    api_key: str,
    secret_key: str,
    base_url: str = "https://iris.fema.gov/api/v2"
) -> IRISIntegrationManager:
    """Create FEMA IRIS integration manager.
    
    Args:
        api_key: FEMA IRIS API key
        secret_key: FEMA IRIS secret key
        base_url: IRIS API base URL
        
    Returns:
        Configured IRIS integration manager
    """
    credentials = IRISCredentials(
        api_key=api_key,
        secret_key=secret_key,
        base_url=base_url
    )
    return IRISIntegrationManager(credentials)