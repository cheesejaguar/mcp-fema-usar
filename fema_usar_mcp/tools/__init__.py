"""FEMA USAR MCP Tools Package.

This package contains specialized tools organized by functional groups:
- Command tools (Task Force Leader, Safety Officer)
- Search tools (Technical Search, Canine Teams)
- Rescue tools (Squad Operations, Heavy Equipment)
- Medical tools (Patient Care, Health Surveillance)
- Planning tools (SITL, RESL, Documentation)
- Logistics tools (Supply, Facilities, Ground Support)
- Technical Specialist tools (Structural, Hazmat, Communications)
"""

from .command import (
    task_force_leader_dashboard,
    safety_officer_monitor,
    personnel_accountability,
)
from .search import (
    victim_location_tracker,
    search_pattern_planner,
    technical_search_equipment,
)
from .rescue import (
    rescue_squad_operations,
    victim_extraction_planner,
    structural_stabilization,
)
from .medical import (
    patient_care_tracker,
    medical_supply_inventory,
    triage_coordinator,
)
from .planning import (
    situation_unit_dashboard,
    resource_unit_tracker,
    documentation_automation,
)
from .logistics import (
    supply_chain_manager,
    facilities_coordinator,
    ground_support_tracker,
)
from .technical import (
    structural_assessment,
    hazmat_monitoring,
    communications_manager,
)

__all__ = [
    # Command tools
    "task_force_leader_dashboard",
    "safety_officer_monitor", 
    "personnel_accountability",
    # Search tools
    "victim_location_tracker",
    "search_pattern_planner",
    "technical_search_equipment",
    # Rescue tools
    "rescue_squad_operations",
    "victim_extraction_planner",
    "structural_stabilization",
    # Medical tools
    "patient_care_tracker",
    "medical_supply_inventory",
    "triage_coordinator",
    # Planning tools
    "situation_unit_dashboard",
    "resource_unit_tracker",
    "documentation_automation",
    # Logistics tools
    "supply_chain_manager",
    "facilities_coordinator",
    "ground_support_tracker",
    # Technical tools
    "structural_assessment",
    "hazmat_monitoring",
    "communications_manager",
]