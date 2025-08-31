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
    personnel_accountability,
    safety_officer_monitor,
    task_force_leader_dashboard,
)
from .logistics import (
    facilities_coordinator,
    ground_support_tracker,
    supply_chain_manager,
)
from .medical import (
    medical_supply_inventory,
    patient_care_tracker,
    triage_coordinator,
)
from .planning import (
    documentation_automation,
    resource_unit_tracker,
    situation_unit_dashboard,
)
from .rescue import (
    rescue_squad_operations,
    structural_stabilization,
    victim_extraction_planner,
)
from .search import (
    search_pattern_planner,
    technical_search_equipment,
    victim_location_tracker,
)
from .technical import (
    communications_manager,
    hazmat_monitoring,
    structural_assessment,
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
