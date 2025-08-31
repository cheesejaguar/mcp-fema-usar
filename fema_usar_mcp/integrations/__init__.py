"""FEMA USAR MCP Integrations Package.

This package contains integrations with external systems:
- FEMA systems (IRIS, NIMS ICT)
- Equipment tracking systems
- Communication systems
"""

from .communications import (
    encrypted_messaging,
    radio_interface,
    satellite_comm,
)
from .equipment import (
    equipment_scanner,
    inventory_sync,
    maintenance_tracker,
)
from .fema_systems import (
    federal_asset_tracker,
    iris_connector,
    nims_ict_integration,
)

__all__ = [
    # FEMA systems
    "iris_connector",
    "nims_ict_integration",
    "federal_asset_tracker",
    # Equipment systems
    "equipment_scanner",
    "inventory_sync",
    "maintenance_tracker",
    # Communication systems
    "radio_interface",
    "satellite_comm",
    "encrypted_messaging",
]
