"""Federal USAR MCP Tools Package.

This package contains specialized tools organized by functional groups:
- Command tools (Task Force Leader, Safety Officer)
- Search tools (Technical Search, Canine Teams)
- Rescue tools (Squad Operations, Heavy Equipment)
- Medical tools (Patient Care, Health Surveillance)
- Planning tools (SITL, RESL, Documentation)
- Logistics tools (Supply, Facilities, Ground Support)
- Technical Specialist tools (Structural, Hazmat, Communications)
- Decision Support tools (Tactical, Strategic, Intelligence)
"""

from .command import (
    external_coordination,
    mission_assignment_tracker,
    personnel_accountability,
    safety_officer_monitor,
    task_force_leader_dashboard,
)
from .decision_support import (
    operational_intelligence_system,
    strategic_planning_advisor,
    tactical_decision_support,
)
from .logistics import (
    facilities_coordinator,
    fuel_management,
    ground_support_tracker,
    maintenance_scheduler,
    supply_chain_manager,
)
from .medical import (
    evacuation_coordinator,
    health_surveillance,
    medical_supply_inventory,
    patient_care_tracker,
    triage_coordinator,
)
from .planning import (
    demobilization_planner,
    documentation_automation,
    operational_timeline,
    resource_unit_tracker,
    situation_unit_dashboard,
)
from .rescue import (
    debris_removal_coordinator,
    heavy_equipment_operations,
    rescue_squad_operations,
    structural_stabilization,
    victim_extraction_planner,
)
from .search import (
    canine_team_deployment,
    search_pattern_planner,
    technical_search_equipment,
    victim_location_tracker,
    void_space_assessment,
)
from .technical import (
    communications_manager,
    environmental_monitor,
    hazmat_monitoring,
    rigging_calculator,
    structural_assessment,
)

__all__ = [
    # Command tools
    "task_force_leader_dashboard",
    "safety_officer_monitor",
    "personnel_accountability",
    "mission_assignment_tracker",
    "external_coordination",
    # Search tools
    "victim_location_tracker",
    "search_pattern_planner",
    "technical_search_equipment",
    "canine_team_deployment",
    "void_space_assessment",
    # Rescue tools
    "rescue_squad_operations",
    "victim_extraction_planner",
    "structural_stabilization",
    "heavy_equipment_operations",
    "debris_removal_coordinator",
    # Medical tools
    "patient_care_tracker",
    "medical_supply_inventory",
    "triage_coordinator",
    "health_surveillance",
    "evacuation_coordinator",
    # Planning tools
    "situation_unit_dashboard",
    "resource_unit_tracker",
    "documentation_automation",
    "demobilization_planner",
    "operational_timeline",
    # Logistics tools
    "supply_chain_manager",
    "facilities_coordinator",
    "ground_support_tracker",
    "fuel_management",
    "maintenance_scheduler",
    # Technical tools
    "structural_assessment",
    "hazmat_monitoring",
    "communications_manager",
    "rigging_calculator",
    "environmental_monitor",
    # Decision Support tools
    "tactical_decision_support",
    "strategic_planning_advisor",
    "operational_intelligence_system",
]
