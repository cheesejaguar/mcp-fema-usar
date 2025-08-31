"""Rescue Group tools for FEMA USAR operations."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Literal

from ..constants import RESCUE_OPERATION_PARAMETERS

logger = logging.getLogger(__name__)


def rescue_squad_operations(
    squad_id: str = "SQUAD-1",
    operation_type: Literal[
        "extraction", "debris_removal", "stabilization", "reconnaissance"
    ] = "extraction",
    victim_id: str | None = None,
    location: str = "Building A, Sector 1",
    personnel_assigned: int = 5,
    equipment_required: list[str] = None,
) -> str:
    """Manage rescue squad deployment and tactical operations.

    Args:
        squad_id: Squad identifier (SQUAD-1 through SQUAD-4)
        operation_type: Type of rescue operation
        victim_id: Victim identifier if applicable
        location: Operation location
        personnel_assigned: Number of personnel assigned
        equipment_required: List of required equipment

    Returns:
        JSON string with detailed squad operation status and recommendations
    """
    try:
        if equipment_required is None:
            equipment_required = []

        # Define standard equipment requirements by operation type
        standard_equipment = {
            "extraction": [
                "hydraulic_tools",
                "cribbing",
                "rope_systems",
                "medical_kit",
                "communications",
            ],
            "debris_removal": [
                "chainsaws",
                "cutting_torch",
                "pneumatic_tools",
                "lifting_bags",
                "safety_gear",
            ],
            "stabilization": [
                "shoring_materials",
                "hydraulic_jacks",
                "welding_equipment",
                "measuring_tools",
            ],
            "reconnaissance": [
                "cameras",
                "measuring_devices",
                "safety_equipment",
                "communications",
                "lighting",
            ],
        }

        # Calculate operation requirements
        base_time_estimates = {
            "extraction": 4.0,  # hours
            "debris_removal": 6.0,
            "stabilization": 8.0,
            "reconnaissance": 2.0,
        }

        # Assess squad readiness
        min_personnel_requirements = {
            "extraction": 4,
            "debris_removal": 5,
            "stabilization": 6,
            "reconnaissance": 3,
        }

        estimated_duration = base_time_estimates.get(operation_type, 4.0)
        min_personnel = min_personnel_requirements.get(operation_type, 4)
        required_equipment = standard_equipment.get(operation_type, [])

        # Add user-specified equipment
        if equipment_required:
            required_equipment.extend(equipment_required)
            required_equipment = list(set(required_equipment))  # Remove duplicates

        # Generate operation data
        operation_data = {
            "squad_id": squad_id,
            "operation_type": operation_type,
            "victim_id": victim_id,
            "location": location,
            "timestamp": datetime.now().isoformat(),
            # Personnel and readiness
            "personnel_assigned": personnel_assigned,
            "personnel_required": min_personnel,
            "personnel_adequate": personnel_assigned >= min_personnel,
            # Equipment requirements
            "required_equipment": required_equipment,
            "equipment_count": len(required_equipment),
            # Operation planning
            "estimated_duration_hours": estimated_duration,
            "complexity_level": determine_operation_complexity(
                operation_type, personnel_assigned, victim_id
            ),
            "safety_level": assess_operation_safety_level(operation_type, location),
            # Current status
            "operation_status": "planning",
            "ready_to_deploy": personnel_assigned >= min_personnel,
            "estimated_start_time": (
                datetime.now() + timedelta(minutes=30)
            ).isoformat(),
            "estimated_completion": (
                datetime.now() + timedelta(hours=estimated_duration)
            ).isoformat(),
        }

        # Generate tactical recommendations
        recommendations = []

        if not operation_data["personnel_adequate"]:
            recommendations.append(
                f"Increase personnel to minimum {min_personnel} for {operation_type} operations"
            )

        if operation_type == "extraction" and victim_id:
            recommendations.append(
                f"Coordinate with Medical Team for victim {victim_id} treatment preparation"
            )
            recommendations.append(
                "Prepare extraction pathway and stabilize route before victim movement"
            )

        if operation_data["safety_level"] == "HIGH_RISK":
            recommendations.append(
                "Implement enhanced safety protocols and continuous monitoring"
            )
            recommendations.append("Consider Safety Officer presence during operation")

        # Add equipment-specific recommendations
        if "hydraulic_tools" in required_equipment:
            recommendations.append(
                "Verify hydraulic system pressure and backup power availability"
            )
        if "cutting_torch" in required_equipment:
            recommendations.append(
                "Ensure proper ventilation and fire suppression measures"
            )

        # Squad coordination recommendations
        recommendations.append(
            "Coordinate with Search Team for victim location confirmation"
        )
        recommendations.append(
            "Maintain radio contact every 15 minutes during operation"
        )

        return json.dumps(
            {
                "operation": "Rescue Squad Operations Manager",
                "status": "success",
                "data": operation_data,
                "tactical_recommendations": recommendations,
                "next_actions": [
                    "Conduct final equipment check",
                    "Brief all squad members on operation plan",
                    "Establish communication protocols",
                    "Verify safety equipment functionality",
                ],
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Rescue squad operations error: {str(e)}", exc_info=True)
        return f"Squad operations error: {str(e)}"


def victim_extraction_planner(
    victim_id: str = "VIC-001",
    victim_location: str = "Building A, 2nd Floor, Room 205",
    extraction_method: Literal[
        "manual", "mechanical", "technical", "complex"
    ] = "manual",
    victim_condition: Literal[
        "conscious", "unconscious", "critical", "deceased"
    ] = "conscious",
    entrapment_type: Literal[
        "debris", "structural", "confined_space", "vehicle"
    ] = "debris",
    access_difficulty: Literal[
        "clear", "limited", "complex", "extremely_difficult"
    ] = "limited",
) -> str:
    """Plan comprehensive victim extraction operations with detailed resource allocation.

    Args:
        victim_id: Unique victim identifier
        victim_location: Detailed victim location
        extraction_method: Primary extraction method
        victim_condition: Current victim condition
        entrapment_type: Type of entrapment situation
        access_difficulty: Difficulty of access to victim

    Returns:
        JSON string with detailed extraction plan and resource requirements
    """
    try:
        # Calculate extraction complexity and requirements
        complexity_factors = RESCUE_OPERATION_PARAMETERS

        condition_modifiers = {
            "conscious": {"urgency": "standard", "medical_support": 1},
            "unconscious": {"urgency": "elevated", "medical_support": 2},
            "critical": {"urgency": "immediate", "medical_support": 3},
            "deceased": {"urgency": "recovery", "medical_support": 1},
        }

        access_modifiers = {
            "clear": 1.0,
            "limited": 1.5,
            "complex": 2.0,
            "extremely_difficult": 3.0,
        }

        base_factors = complexity_factors[extraction_method]
        condition_info = condition_modifiers[victim_condition]
        access_multiplier = access_modifiers[access_difficulty]

        # Calculate resource requirements
        estimated_time = base_factors["time"] * access_multiplier
        required_personnel = int(base_factors["personnel"] * access_multiplier)
        equipment_complexity = int(base_factors["equipment"] * access_multiplier)

        # Define extraction phases
        extraction_phases = [
            {
                "phase": "Assessment and Planning",
                "duration_minutes": 30,
                "activities": [
                    "Victim assessment",
                    "Route planning",
                    "Equipment setup",
                ],
                "personnel_required": 3,
                "critical": True,
            },
            {
                "phase": "Access Creation",
                "duration_minutes": int(estimated_time * 30),
                "activities": [
                    "Debris removal",
                    "Structural stabilization",
                    "Access pathway",
                ],
                "personnel_required": required_personnel - 2,
                "critical": True,
            },
            {
                "phase": "Victim Preparation",
                "duration_minutes": 20,
                "activities": [
                    "Medical assessment",
                    "Stabilization",
                    "Extraction preparation",
                ],
                "personnel_required": 2,
                "critical": True,
            },
            {
                "phase": "Extraction",
                "duration_minutes": int(estimated_time * 20),
                "activities": [
                    "Victim movement",
                    "Medical monitoring",
                    "Safety oversight",
                ],
                "personnel_required": required_personnel,
                "critical": True,
            },
            {
                "phase": "Medical Handoff",
                "duration_minutes": 10,
                "activities": ["Medical transfer", "Documentation", "Area securing"],
                "personnel_required": 3,
                "critical": True,
            },
        ]

        # Equipment requirements by extraction method
        equipment_lists = {
            "manual": [
                "Basic rescue tools",
                "Rope systems",
                "Cribbing materials",
                "Medical kit",
                "Communications",
                "Lighting",
                "Safety equipment",
            ],
            "mechanical": [
                "Hydraulic rescue tools",
                "Pneumatic tools",
                "Lifting systems",
                "Cutting equipment",
                "Rope systems",
                "Medical kit",
                "Monitoring equipment",
                "Safety gear",
            ],
            "technical": [
                "Advanced hydraulic systems",
                "Specialized cutting tools",
                "Rigging equipment",
                "Confined space gear",
                "Advanced medical kit",
                "Monitoring systems",
                "Technical rescue gear",
                "Communication systems",
            ],
            "complex": [
                "Heavy hydraulic systems",
                "Specialized extraction equipment",
                "Engineering tools",
                "Advanced rigging",
                "Complete medical setup",
                "Monitoring systems",
                "Technical rescue equipment",
                "Heavy lifting gear",
                "Specialized safety equipment",
            ],
        }

        required_equipment = equipment_lists.get(
            extraction_method, equipment_lists["manual"]
        )

        # Calculate total operation time
        total_operation_time = sum(
            phase["duration_minutes"] for phase in extraction_phases
        )

        # Generate extraction plan
        extraction_plan = {
            "victim_information": {
                "victim_id": victim_id,
                "location": victim_location,
                "condition": victim_condition,
                "entrapment_type": entrapment_type,
                "medical_priority": condition_info["urgency"],
            },
            "extraction_parameters": {
                "method": extraction_method,
                "access_difficulty": access_difficulty,
                "complexity_score": equipment_complexity,
                "estimated_total_time_minutes": total_operation_time,
                "estimated_total_time_hours": round(total_operation_time / 60, 1),
            },
            "resource_requirements": {
                "personnel_required": required_personnel,
                "medical_support_level": condition_info["medical_support"],
                "equipment_list": required_equipment,
                "specialized_tools": len(
                    [
                        eq
                        for eq in required_equipment
                        if "advanced" in eq.lower() or "specialized" in eq.lower()
                    ]
                ),
            },
            "extraction_phases": extraction_phases,
            "safety_considerations": generate_extraction_safety_considerations(
                entrapment_type, victim_condition, access_difficulty
            ),
            "coordination_requirements": {
                "medical_team": condition_info["medical_support"] >= 2,
                "technical_specialists": extraction_method in ["technical", "complex"],
                "heavy_equipment": entrapment_type in ["structural", "vehicle"],
                "incident_command": condition_info["urgency"] == "immediate",
            },
        }

        # Generate recommendations
        recommendations = []

        if condition_info["urgency"] == "immediate":
            recommendations.append(
                "IMMEDIATE ACTION REQUIRED - Critical victim condition"
            )
            recommendations.append(
                "Deploy advanced medical support simultaneously with extraction"
            )

        if access_difficulty in ["complex", "extremely_difficult"]:
            recommendations.append("Consider alternative extraction routes")
            recommendations.append(
                "Request structural specialist evaluation if not already present"
            )

        if extraction_method in ["technical", "complex"]:
            recommendations.append(
                "Deploy Technical Rescue Specialist with extraction team"
            )
            recommendations.append("Establish secondary extraction plan as backup")

        if entrapment_type == "confined_space":
            recommendations.append("Implement confined space rescue protocols")
            recommendations.append("Ensure continuous atmospheric monitoring")

        recommendations.extend(
            [
                f"Estimated operation time: {round(total_operation_time / 60, 1)} hours",
                f"Deploy {required_personnel} personnel minimum",
                "Maintain continuous communication with Incident Command",
                "Prepare medical evacuation route in advance",
            ]
        )

        return json.dumps(
            {
                "planner": "Victim Extraction Planner",
                "status": "success",
                "data": extraction_plan,
                "recommendations": recommendations,
                "critical_success_factors": [
                    "Adequate personnel deployment",
                    "Proper equipment functionality",
                    "Clear communication protocols",
                    "Medical team coordination",
                    "Continuous safety monitoring",
                ],
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Victim extraction planner error: {str(e)}", exc_info=True)
        return f"Extraction planning error: {str(e)}"


def structural_stabilization(
    structure_location: str = "Building A, Northwest Corner",
    stabilization_type: Literal[
        "shoring", "cribbing", "lifting", "temporary_repair"
    ] = "shoring",
    urgency: Literal["immediate", "planned", "preventive", "emergency"] = "immediate",
    structural_damage: Literal["minor", "moderate", "major", "critical"] = "moderate",
    personnel_at_risk: int = 0,
    load_requirements: float | None = None,
) -> str:
    """Track and manage structural stabilization and shoring operations.

    Args:
        structure_location: Detailed location of structural work
        stabilization_type: Type of stabilization required
        urgency: Urgency level for stabilization work
        structural_damage: Level of structural damage observed
        personnel_at_risk: Number of personnel potentially at risk
        load_requirements: Load requirements in pounds if applicable

    Returns:
        JSON string with stabilization plan and safety protocols
    """
    try:
        # Define stabilization parameters
        stabilization_specs = {
            "shoring": {
                "materials": ["Shoring posts", "Cross braces", "Wedges", "Nails/bolts"],
                "time_hours": 4,
                "personnel": 4,
                "complexity": "medium",
                "load_capacity": 5000,  # lbs
            },
            "cribbing": {
                "materials": ["Cribbing blocks", "Step blocks", "Wedges", "Box cribs"],
                "time_hours": 2,
                "personnel": 3,
                "complexity": "low",
                "load_capacity": 10000,  # lbs
            },
            "lifting": {
                "materials": [
                    "Hydraulic jacks",
                    "Lifting bags",
                    "Steel plates",
                    "Support posts",
                ],
                "time_hours": 3,
                "personnel": 5,
                "complexity": "high",
                "load_capacity": 20000,  # lbs
            },
            "temporary_repair": {
                "materials": [
                    "Steel plates",
                    "Welding equipment",
                    "Bolts",
                    "Structural adhesives",
                ],
                "time_hours": 6,
                "personnel": 4,
                "complexity": "high",
                "load_capacity": 8000,  # lbs
            },
        }

        # Urgency multipliers
        urgency_factors = {
            "immediate": {
                "time_multiplier": 0.7,
                "personnel_multiplier": 1.5,
                "priority": 1,
            },
            "planned": {
                "time_multiplier": 1.0,
                "personnel_multiplier": 1.0,
                "priority": 3,
            },
            "preventive": {
                "time_multiplier": 1.2,
                "personnel_multiplier": 1.0,
                "priority": 4,
            },
            "emergency": {
                "time_multiplier": 0.5,
                "personnel_multiplier": 2.0,
                "priority": 0,
            },
        }

        # Damage level impacts
        damage_impacts = {
            "minor": {"safety_factor": 1.2, "monitoring": "periodic"},
            "moderate": {"safety_factor": 1.5, "monitoring": "frequent"},
            "major": {"safety_factor": 2.0, "monitoring": "continuous"},
            "critical": {"safety_factor": 3.0, "monitoring": "constant"},
        }

        specs = stabilization_specs[stabilization_type]
        urgency_info = urgency_factors[urgency]
        damage_info = damage_impacts[structural_damage]

        # Calculate requirements
        estimated_time = specs["time_hours"] * urgency_info["time_multiplier"]
        required_personnel = int(
            specs["personnel"] * urgency_info["personnel_multiplier"]
        )
        load_capacity = specs["load_capacity"]

        if load_requirements:
            # Check if stabilization method can handle required load
            adequate_capacity = load_capacity >= load_requirements
            if not adequate_capacity:
                recommended_method = determine_adequate_stabilization_method(
                    load_requirements, stabilization_specs
                )
            else:
                recommended_method = stabilization_type
        else:
            adequate_capacity = True
            recommended_method = stabilization_type

        # Generate stabilization plan
        stabilization_data = {
            "location": structure_location,
            "stabilization_details": {
                "type": stabilization_type,
                "recommended_method": recommended_method,
                "damage_level": structural_damage,
                "urgency": urgency,
                "priority_level": urgency_info["priority"],
            },
            "resource_requirements": {
                "personnel_required": required_personnel,
                "estimated_time_hours": round(estimated_time, 1),
                "materials_needed": specs["materials"],
                "load_capacity_lbs": load_capacity,
                "load_adequate": adequate_capacity,
            },
            "safety_protocols": {
                "personnel_at_risk": personnel_at_risk,
                "safety_factor": damage_info["safety_factor"],
                "monitoring_frequency": damage_info["monitoring"],
                "evacuation_plan": personnel_at_risk > 0,
                "continuous_assessment": structural_damage in ["major", "critical"],
            },
            "timeline": generate_stabilization_timeline(
                estimated_time, specs["materials"], required_personnel
            ),
            "quality_control": {
                "inspection_points": determine_inspection_points(stabilization_type),
                "load_testing": stabilization_type == "lifting",
                "documentation_required": True,
                "engineer_approval": structural_damage in ["major", "critical"],
            },
        }

        # Generate safety alerts if needed
        safety_alerts = []
        if personnel_at_risk > 0:
            safety_alerts.append(
                {
                    "alert_type": "personnel_risk",
                    "message": f"{personnel_at_risk} personnel potentially at risk",
                    "action_required": "Establish safety perimeter and evacuation procedures",
                }
            )

        if structural_damage == "critical":
            safety_alerts.append(
                {
                    "alert_type": "structural_failure_risk",
                    "message": "Critical structural damage detected",
                    "action_required": "Emergency stabilization required - deploy all available resources",
                }
            )

        if not adequate_capacity and load_requirements:
            safety_alerts.append(
                {
                    "alert_type": "inadequate_capacity",
                    "message": f"Current method insufficient for {load_requirements} lbs load",
                    "action_required": f"Switch to {recommended_method} or deploy additional support",
                }
            )

        # Recommendations
        recommendations = []

        if urgency == "emergency":
            recommendations.append(
                "EMERGENCY STABILIZATION - Deploy immediately with all available personnel"
            )
            recommendations.append("Evacuate all non-essential personnel from area")

        if structural_damage in ["major", "critical"]:
            recommendations.append("Request Structures Specialist evaluation")
            recommendations.append("Implement continuous structural monitoring")

        if personnel_at_risk > 5:
            recommendations.append(
                "Establish incident command post for stabilization operation"
            )
            recommendations.append(
                "Coordinate with Safety Officer for personnel protection"
            )

        recommendations.extend(
            [
                f"Deploy {required_personnel} personnel for {stabilization_type} operation",
                f"Estimated completion in {round(estimated_time, 1)} hours",
                "Maintain communication with all affected teams",
                "Document all stabilization work for engineering review",
            ]
        )

        return json.dumps(
            {
                "stabilization": "Structural Stabilization Manager",
                "status": "success",
                "data": stabilization_data,
                "safety_alerts": safety_alerts,
                "recommendations": recommendations,
                "next_steps": [
                    "Conduct detailed structural assessment",
                    "Gather required materials and personnel",
                    "Establish safety perimeter",
                    "Begin stabilization work",
                    "Monitor progress and structural integrity",
                ],
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Structural stabilization error: {str(e)}", exc_info=True)
        return f"Structural stabilization error: {str(e)}"


def heavy_equipment_operations(
    equipment_type: Literal[
        "excavator", "crane", "loader", "concrete_breaker", "compactor"
    ] = "excavator",
    operation_mode: Literal[
        "debris_removal", "lifting", "site_prep", "demolition", "material_handling"
    ] = "debris_removal",
    location: str = "Site A, Grid Reference 15",
    operator_qualified: bool = True,
    equipment_condition: Literal[
        "excellent", "good", "fair", "needs_maintenance"
    ] = "good",
    work_area_secured: bool = False,
) -> str:
    """Manage heavy equipment deployment, operations, and safety protocols.

    Args:
        equipment_type: Type of heavy equipment
        operation_mode: Primary operation mode
        location: Equipment operation location
        operator_qualified: Whether operator is qualified for this equipment
        equipment_condition: Current equipment condition
        work_area_secured: Whether work area is properly secured

    Returns:
        JSON string with equipment operation plan and safety protocols
    """
    try:
        # Equipment specifications and capabilities
        equipment_specs = {
            "excavator": {
                "primary_uses": ["debris_removal", "digging", "material_handling"],
                "reach_feet": 25,
                "lift_capacity_lbs": 8000,
                "fuel_consumption_gph": 6.5,
                "operator_certification": "Heavy Equipment Operator",
                "setup_time_minutes": 15,
                "safety_radius_feet": 30,
            },
            "crane": {
                "primary_uses": ["lifting", "material_placement", "debris_removal"],
                "reach_feet": 80,
                "lift_capacity_lbs": 25000,
                "fuel_consumption_gph": 8.0,
                "operator_certification": "Crane Operator",
                "setup_time_minutes": 45,
                "safety_radius_feet": 100,
            },
            "loader": {
                "primary_uses": ["material_handling", "debris_removal", "site_prep"],
                "reach_feet": 12,
                "lift_capacity_lbs": 3000,
                "fuel_consumption_gph": 4.5,
                "operator_certification": "Heavy Equipment Operator",
                "setup_time_minutes": 10,
                "safety_radius_feet": 25,
            },
            "concrete_breaker": {
                "primary_uses": ["demolition", "concrete_removal", "debris_breaking"],
                "reach_feet": 15,
                "lift_capacity_lbs": 5000,
                "fuel_consumption_gph": 7.0,
                "operator_certification": "Specialized Equipment Operator",
                "setup_time_minutes": 20,
                "safety_radius_feet": 40,
            },
            "compactor": {
                "primary_uses": [
                    "site_prep",
                    "material_compaction",
                    "surface_preparation",
                ],
                "reach_feet": 8,
                "lift_capacity_lbs": 2000,
                "fuel_consumption_gph": 3.5,
                "operator_certification": "Heavy Equipment Operator",
                "setup_time_minutes": 5,
                "safety_radius_feet": 20,
            },
        }

        specs = equipment_specs[equipment_type]

        # Operation mode requirements
        operation_requirements = {
            "debris_removal": {
                "duration_hours": 8,
                "support_personnel": 2,
                "special_equipment": ["Safety barriers", "Spotters", "Communication"],
                "risk_level": "medium",
            },
            "lifting": {
                "duration_hours": 4,
                "support_personnel": 4,
                "special_equipment": [
                    "Rigging equipment",
                    "Load calculations",
                    "Spotters",
                    "Safety gear",
                ],
                "risk_level": "high",
            },
            "site_prep": {
                "duration_hours": 6,
                "support_personnel": 1,
                "special_equipment": ["Survey equipment", "Safety barriers"],
                "risk_level": "low",
            },
            "demolition": {
                "duration_hours": 10,
                "support_personnel": 3,
                "special_equipment": [
                    "Protective barriers",
                    "Dust control",
                    "Safety monitoring",
                ],
                "risk_level": "high",
            },
            "material_handling": {
                "duration_hours": 6,
                "support_personnel": 2,
                "special_equipment": ["Material containers", "Safety barriers"],
                "risk_level": "medium",
            },
        }

        operation_info = operation_requirements.get(
            operation_mode, operation_requirements["debris_removal"]
        )

        # Calculate fuel requirements
        estimated_fuel_needed = (
            specs["fuel_consumption_gph"] * operation_info["duration_hours"]
        )

        # Generate equipment operation plan
        operation_data = {
            "equipment_information": {
                "type": equipment_type,
                "operation_mode": operation_mode,
                "location": location,
                "operator_qualified": operator_qualified,
                "equipment_condition": equipment_condition,
                "work_area_secured": work_area_secured,
            },
            "operational_specifications": {
                "reach_feet": specs["reach_feet"],
                "lift_capacity_lbs": specs["lift_capacity_lbs"],
                "required_certification": specs["operator_certification"],
                "setup_time_minutes": specs["setup_time_minutes"],
                "safety_radius_feet": specs["safety_radius_feet"],
            },
            "operation_plan": {
                "estimated_duration_hours": operation_info["duration_hours"],
                "support_personnel_required": operation_info["support_personnel"],
                "risk_level": operation_info["risk_level"],
                "special_equipment_needed": operation_info["special_equipment"],
            },
            "resource_requirements": {
                "fuel_needed_gallons": round(estimated_fuel_needed, 1),
                "operator_certification_verified": operator_qualified,
                "equipment_inspection_current": equipment_condition
                in ["excellent", "good"],
                "safety_perimeter_established": work_area_secured,
            },
            "safety_protocols": generate_heavy_equipment_safety_protocols(
                equipment_type, operation_mode, specs["safety_radius_feet"]
            ),
            "pre_operation_checklist": [
                "Verify operator qualifications and certification",
                "Conduct equipment inspection and functionality test",
                "Establish safety perimeter and warning systems",
                "Brief all personnel on operation plan and safety protocols",
                "Test communication systems",
                "Verify fuel levels and hydraulic fluid",
                "Check all safety equipment functionality",
                "Confirm work area is clear of personnel and hazards",
            ],
        }

        # Safety alerts and warnings
        safety_alerts = []

        if not operator_qualified:
            safety_alerts.append(
                {
                    "alert_type": "operator_qualification",
                    "severity": "high",
                    "message": "Operator not qualified for this equipment type",
                    "action": "Replace with qualified operator before operation",
                }
            )

        if equipment_condition in ["fair", "needs_maintenance"]:
            safety_alerts.append(
                {
                    "alert_type": "equipment_condition",
                    "severity": "medium",
                    "message": f"Equipment condition is {equipment_condition}",
                    "action": "Conduct thorough inspection and maintenance before operation",
                }
            )

        if not work_area_secured:
            safety_alerts.append(
                {
                    "alert_type": "work_area_security",
                    "severity": "high",
                    "message": "Work area not properly secured",
                    "action": f"Establish {specs['safety_radius_feet']}-foot safety perimeter",
                }
            )

        if operation_info["risk_level"] == "high":
            safety_alerts.append(
                {
                    "alert_type": "high_risk_operation",
                    "severity": "high",
                    "message": f"{operation_mode} is a high-risk operation",
                    "action": "Implement enhanced safety protocols and continuous monitoring",
                }
            )

        # Operational recommendations
        recommendations = []

        if operation_mode == "lifting":
            recommendations.append(
                "Deploy Heavy Equipment/Rigging Specialist for load calculations"
            )
            recommendations.append(
                "Conduct lift plan review and approval before operation"
            )

        if equipment_type == "crane":
            recommendations.append(
                "Establish ground guides and maintain clear communication"
            )
            recommendations.append(
                "Monitor wind conditions - suspend operations if winds exceed 20 mph"
            )

        if operation_info["duration_hours"] > 8:
            recommendations.append("Plan operator rotation to prevent fatigue")
            recommendations.append(
                "Schedule equipment breaks every 2 hours for inspection"
            )

        recommendations.extend(
            [
                f"Maintain {specs['safety_radius_feet']}-foot safety perimeter at all times",
                f"Ensure {estimated_fuel_needed:.1f} gallons fuel available",
                "Coordinate with other operations to prevent conflicts",
                "Monitor equipment performance continuously",
            ]
        )

        return json.dumps(
            {
                "equipment": "Heavy Equipment Operations Manager",
                "status": "success",
                "data": operation_data,
                "safety_alerts": safety_alerts,
                "recommendations": recommendations,
                "operational_readiness": {
                    "ready_to_operate": all(
                        [
                            operator_qualified,
                            equipment_condition in ["excellent", "good"],
                            work_area_secured,
                        ]
                    ),
                    "blocking_issues": [
                        alert["message"]
                        for alert in safety_alerts
                        if alert["severity"] == "high"
                    ],
                },
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Heavy equipment operations error: {str(e)}", exc_info=True)
        return f"Heavy equipment operations error: {str(e)}"


def debris_removal_coordinator(
    area_id: str = "AREA-A",
    removal_priority: Literal[
        "immediate", "planned", "cleanup", "hazardous"
    ] = "immediate",
    debris_type: Literal[
        "structural", "mixed", "hazardous", "organic", "metal"
    ] = "mixed",
    volume_estimate_cubic_yards: float | None = None,
    access_route_clear: bool = False,
    disposal_site_identified: bool = False,
) -> str:
    """Coordinate comprehensive debris removal operations with progress tracking and resource optimization.

    Args:
        area_id: Area identifier for debris removal
        removal_priority: Priority level for removal operations
        debris_type: Primary type of debris to be removed
        volume_estimate_cubic_yards: Estimated volume in cubic yards
        access_route_clear: Whether access routes are clear
        disposal_site_identified: Whether disposal site has been identified

    Returns:
        JSON string with debris removal coordination plan and progress tracking
    """
    try:
        # Debris type specifications
        debris_specifications = {
            "structural": {
                "handling": "heavy_equipment",
                "sorting_required": True,
                "disposal_method": "construction_landfill",
                "safety_concerns": ["sharp_edges", "unstable_pieces", "dust"],
                "equipment_needed": ["excavator", "loader", "dump_trucks"],
                "processing_rate_cy_hour": 15,
            },
            "mixed": {
                "handling": "manual_and_mechanical",
                "sorting_required": True,
                "disposal_method": "multiple_sites",
                "safety_concerns": [
                    "unknown_materials",
                    "sharp_objects",
                    "contamination",
                ],
                "equipment_needed": ["excavator", "loader", "sorting_equipment"],
                "processing_rate_cy_hour": 8,
            },
            "hazardous": {
                "handling": "specialized",
                "sorting_required": True,
                "disposal_method": "hazmat_facility",
                "safety_concerns": [
                    "chemical_exposure",
                    "contamination",
                    "special_handling",
                ],
                "equipment_needed": [
                    "specialized_containers",
                    "hazmat_suits",
                    "monitoring_equipment",
                ],
                "processing_rate_cy_hour": 3,
            },
            "organic": {
                "handling": "standard",
                "sorting_required": False,
                "disposal_method": "composting_facility",
                "safety_concerns": ["decomposition", "disease", "insects"],
                "equipment_needed": ["loader", "chipper", "trucks"],
                "processing_rate_cy_hour": 20,
            },
            "metal": {
                "handling": "mechanical",
                "sorting_required": True,
                "disposal_method": "recycling_facility",
                "safety_concerns": [
                    "sharp_edges",
                    "heavy_pieces",
                    "structural_failure",
                ],
                "equipment_needed": ["crane", "cutting_torch", "magnets"],
                "processing_rate_cy_hour": 12,
            },
        }

        # Priority level impacts
        priority_impacts = {
            "immediate": {
                "resources_multiplier": 1.5,
                "timeline_hours": 12,
                "personnel_priority": "high",
                "coordination_level": "continuous",
            },
            "planned": {
                "resources_multiplier": 1.0,
                "timeline_hours": 48,
                "personnel_priority": "standard",
                "coordination_level": "regular",
            },
            "cleanup": {
                "resources_multiplier": 0.8,
                "timeline_hours": 96,
                "personnel_priority": "low",
                "coordination_level": "minimal",
            },
            "hazardous": {
                "resources_multiplier": 2.0,
                "timeline_hours": 8,
                "personnel_priority": "critical",
                "coordination_level": "constant",
            },
        }

        debris_spec = debris_specifications[debris_type]
        priority_spec = priority_impacts[removal_priority]

        # Calculate operation requirements
        if volume_estimate_cubic_yards:
            estimated_time_hours = (
                volume_estimate_cubic_yards / debris_spec["processing_rate_cy_hour"]
            ) * priority_spec["resources_multiplier"]
            trucks_needed = max(
                2, int(volume_estimate_cubic_yards / 20)
            )  # 20 cy per truck load
        else:
            estimated_time_hours = 24.0  # Default estimate
            trucks_needed = 4
            volume_estimate_cubic_yards = 100.0  # Default estimate

        # Personnel requirements
        base_personnel = {
            "equipment_operators": 3,
            "ground_personnel": 4,
            "safety_monitor": 1,
            "coordinator": 1,
        }

        if debris_type == "hazardous":
            base_personnel["hazmat_specialists"] = 2
        if debris_spec["sorting_required"]:
            base_personnel["sorting_personnel"] = 2

        total_personnel = sum(base_personnel.values())

        # Generate debris removal plan
        removal_data = {
            "area_identification": {
                "area_id": area_id,
                "debris_type": debris_type,
                "priority": removal_priority,
                "volume_estimate_cy": volume_estimate_cubic_yards,
                "access_route_status": "clear" if access_route_clear else "blocked",
                "disposal_site_status": (
                    "identified" if disposal_site_identified else "pending"
                ),
            },
            "operation_specifications": {
                "handling_method": debris_spec["handling"],
                "sorting_required": debris_spec["sorting_required"],
                "disposal_method": debris_spec["disposal_method"],
                "processing_rate_cy_hour": debris_spec["processing_rate_cy_hour"],
                "estimated_duration_hours": round(estimated_time_hours, 1),
            },
            "resource_allocation": {
                "personnel_breakdown": base_personnel,
                "total_personnel": total_personnel,
                "equipment_required": debris_spec["equipment_needed"],
                "trucks_needed": trucks_needed,
                "specialized_equipment": debris_type == "hazardous",
            },
            "safety_protocols": {
                "primary_concerns": debris_spec["safety_concerns"],
                "ppe_required": determine_ppe_requirements(debris_type),
                "monitoring_requirements": determine_monitoring_requirements(
                    debris_type
                ),
                "emergency_procedures": generate_debris_emergency_procedures(
                    debris_type
                ),
            },
            "coordination_requirements": {
                "access_route_coordination": not access_route_clear,
                "disposal_site_coordination": not disposal_site_identified,
                "traffic_control": True,
                "other_operations_coordination": True,
                "environmental_compliance": debris_type in ["hazardous", "mixed"],
            },
            "progress_tracking": {
                "measurement_method": "cubic_yards_removed",
                "reporting_frequency": priority_spec["coordination_level"],
                "milestone_markers": [25, 50, 75, 90, 100],  # Percentage completion
                "quality_control_points": generate_quality_control_points(debris_type),
            },
        }

        # Generate operation phases
        operation_phases = [
            {
                "phase": "Site Preparation",
                "duration_hours": 2,
                "activities": [
                    "Access route clearing",
                    "Equipment positioning",
                    "Safety setup",
                ],
                "dependencies": ["access_route_clear"],
                "completion_criteria": "Safe work area established",
            },
            {
                "phase": "Debris Processing",
                "duration_hours": estimated_time_hours * 0.8,
                "activities": [
                    "Debris removal",
                    "Sorting operations",
                    "Loading operations",
                ],
                "dependencies": ["equipment_operational"],
                "completion_criteria": f"{volume_estimate_cubic_yards * 0.8:.0f} cy processed",
            },
            {
                "phase": "Final Cleanup",
                "duration_hours": estimated_time_hours * 0.15,
                "activities": [
                    "Area sweeping",
                    "Final inspection",
                    "Equipment cleanup",
                ],
                "dependencies": ["main_removal_complete"],
                "completion_criteria": "Area meets completion standards",
            },
            {
                "phase": "Documentation",
                "duration_hours": 1,
                "activities": [
                    "Final documentation",
                    "Environmental compliance",
                    "Handoff procedures",
                ],
                "dependencies": ["cleanup_complete"],
                "completion_criteria": "All documentation complete",
            },
        ]

        # Generate blocking issues and recommendations
        blocking_issues = []
        if not access_route_clear:
            blocking_issues.append(
                "Access routes must be cleared before debris removal can begin"
            )
        if not disposal_site_identified:
            blocking_issues.append("Disposal site must be identified and permitted")
        if debris_type == "hazardous" and "hazmat_specialists" not in base_personnel:
            blocking_issues.append(
                "Hazmat specialists required for hazardous debris removal"
            )

        recommendations = []

        if removal_priority == "immediate":
            recommendations.append(
                "Deploy maximum available resources for immediate debris removal"
            )
            recommendations.append("Establish 24-hour operations if necessary")

        if debris_type == "hazardous":
            recommendations.append(
                "Coordinate with Environmental Specialist for hazmat protocols"
            )
            recommendations.append("Implement continuous air quality monitoring")

        if not access_route_clear:
            recommendations.append(
                "Priority: Clear access routes for equipment movement"
            )

        if volume_estimate_cubic_yards > 500:
            recommendations.append(
                "Consider establishing temporary debris staging area"
            )
            recommendations.append(
                "Coordinate with multiple disposal sites to manage volume"
            )

        recommendations.extend(
            [
                f"Deploy {total_personnel} personnel for debris removal operation",
                f"Secure {trucks_needed} dump trucks for debris transport",
                "Establish regular progress reporting schedule",
                "Maintain continuous safety monitoring throughout operation",
            ]
        )

        return json.dumps(
            {
                "coordinator": "Debris Removal Coordinator",
                "status": "success",
                "data": removal_data,
                "operation_phases": operation_phases,
                "blocking_issues": blocking_issues,
                "recommendations": recommendations,
                "operational_readiness": {
                    "ready_to_start": len(blocking_issues) == 0,
                    "estimated_start_delay_hours": 4 if blocking_issues else 0,
                    "completion_timeline": f"{round(estimated_time_hours + len(blocking_issues) * 2, 1)} hours",
                },
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Debris removal coordinator error: {str(e)}", exc_info=True)
        return f"Debris removal coordination error: {str(e)}"


# Helper functions for rescue operations


def determine_operation_complexity(
    operation_type: str, personnel: int, victim_id: str | None
) -> str:
    """Determine operation complexity based on parameters."""
    complexity_score = 0

    if operation_type in ["extraction", "stabilization"]:
        complexity_score += 2
    elif operation_type == "debris_removal":
        complexity_score += 1

    if personnel < 4:
        complexity_score += 1
    elif personnel > 8:
        complexity_score -= 1

    if victim_id:
        complexity_score += 1

    if complexity_score <= 1:
        return "low"
    elif complexity_score <= 3:
        return "medium"
    else:
        return "high"


def assess_operation_safety_level(operation_type: str, location: str) -> str:
    """Assess safety level for rescue operation."""
    risk_factors = []

    if "building" in location.lower():
        risk_factors.append("structural")
    if operation_type in ["extraction", "stabilization"]:
        risk_factors.append("complex_operation")
    if "floor" in location.lower() and any(
        num in location for num in ["2", "3", "4", "5"]
    ):
        risk_factors.append("elevated_work")

    if len(risk_factors) >= 3:
        return "HIGH_RISK"
    elif len(risk_factors) >= 2:
        return "MEDIUM_RISK"
    else:
        return "STANDARD_RISK"


def generate_extraction_safety_considerations(
    entrapment_type: str, victim_condition: str, access_difficulty: str
) -> list[str]:
    """Generate safety considerations for victim extraction."""
    considerations = [
        "Maintain continuous communication with victim if conscious",
        "Monitor structural stability throughout extraction",
        "Ensure medical personnel ready for immediate treatment",
    ]

    if entrapment_type == "structural":
        considerations.extend(
            [
                "Request Structures Specialist assessment",
                "Implement additional shoring before extraction",
                "Monitor for secondary collapse risk",
            ]
        )

    if victim_condition in ["unconscious", "critical"]:
        considerations.extend(
            [
                "Prepare advanced life support equipment",
                "Plan for rapid medical evacuation",
                "Consider helicopter evacuation if ground transport delayed",
            ]
        )

    if access_difficulty in ["complex", "extremely_difficult"]:
        considerations.extend(
            [
                "Establish backup extraction route",
                "Deploy additional safety personnel",
                "Consider alternative extraction methods",
            ]
        )

    return considerations


def generate_stabilization_timeline(
    estimated_time: float, materials: list[str], personnel: int
) -> list[dict[str, Any]]:
    """Generate timeline for stabilization operations."""
    phases = [
        {
            "phase": "Material Preparation",
            "start_hour": 0,
            "duration_hours": 0.5,
            "personnel": 2,
            "activities": ["Gather materials", "Prepare tools", "Safety briefing"],
        },
        {
            "phase": "Site Setup",
            "start_hour": 0.5,
            "duration_hours": 0.5,
            "personnel": personnel,
            "activities": [
                "Position equipment",
                "Establish safety perimeter",
                "Initial assessment",
            ],
        },
        {
            "phase": "Stabilization Work",
            "start_hour": 1.0,
            "duration_hours": estimated_time - 2,
            "personnel": personnel,
            "activities": [
                "Install stabilization",
                "Monitor progress",
                "Quality checks",
            ],
        },
        {
            "phase": "Final Inspection",
            "start_hour": estimated_time - 1,
            "duration_hours": 0.5,
            "personnel": 3,
            "activities": ["Final inspection", "Load testing", "Documentation"],
        },
        {
            "phase": "Area Clearing",
            "start_hour": estimated_time - 0.5,
            "duration_hours": 0.5,
            "personnel": 2,
            "activities": ["Clean up area", "Secure materials", "Final safety check"],
        },
    ]

    return phases


def determine_inspection_points(stabilization_type: str) -> list[str]:
    """Determine inspection points for stabilization work."""
    base_points = [
        "Material condition and suitability",
        "Installation alignment and positioning",
        "Connection integrity and security",
        "Load distribution verification",
        "Final stability assessment",
    ]

    type_specific = {
        "shoring": ["Post positioning", "Bracing alignment", "Wedge tightness"],
        "cribbing": ["Block alignment", "Contact surfaces", "Load path verification"],
        "lifting": ["Jack positioning", "Load calculations", "Lifting sequence"],
        "temporary_repair": ["Weld quality", "Bolt torque", "Material compatibility"],
    }

    return base_points + type_specific.get(stabilization_type, [])


def determine_adequate_stabilization_method(
    load_requirements: float, methods: dict[str, dict]
) -> str:
    """Determine adequate stabilization method for load requirements."""
    for method, specs in methods.items():
        if specs["load_capacity"] >= load_requirements:
            return method
    return "lifting"  # Default to highest capacity method


def generate_heavy_equipment_safety_protocols(
    equipment_type: str, operation_mode: str, safety_radius: int
) -> dict[str, Any]:
    """Generate safety protocols for heavy equipment operations."""
    base_protocols = {
        "safety_perimeter": f"{safety_radius} feet minimum",
        "spotters_required": operation_mode in ["lifting", "demolition"],
        "communication": "Continuous radio contact required",
        "emergency_stop": "All personnel trained on emergency stop procedures",
    }

    equipment_specific = {
        "crane": {
            "wind_limits": "Suspend operations if winds exceed 20 mph",
            "load_charts": "Verify all lifts against manufacturer load charts",
            "ground_conditions": "Ensure stable, level ground for crane setup",
        },
        "excavator": {
            "underground_utilities": "Verify utility locations before digging",
            "stability": "Monitor ground conditions and equipment stability",
            "swing_radius": "Maintain clear swing radius at all times",
        },
    }

    base_protocols.update(equipment_specific.get(equipment_type, {}))
    return base_protocols


def determine_ppe_requirements(debris_type: str) -> list[str]:
    """Determine PPE requirements based on debris type."""
    base_ppe = [
        "Hard hat",
        "Safety glasses",
        "Steel-toed boots",
        "High-visibility vest",
    ]

    type_specific = {
        "hazardous": [
            "Chemical-resistant suit",
            "Self-contained breathing apparatus",
            "Chemical-resistant gloves",
        ],
        "structural": ["Cut-resistant gloves", "Dust mask", "Knee protection"],
        "mixed": ["General work gloves", "Dust mask", "Cut-resistant sleeves"],
        "organic": ["Dust mask", "Waterproof gloves", "Tyvek suit"],
        "metal": ["Cut-resistant gloves", "Welding gloves", "Face shield"],
    }

    return base_ppe + type_specific.get(debris_type, [])


def determine_monitoring_requirements(debris_type: str) -> list[str]:
    """Determine monitoring requirements for debris operations."""
    base_monitoring = [
        "Personnel accountability",
        "Equipment status",
        "Weather conditions",
    ]

    type_specific = {
        "hazardous": [
            "Air quality monitoring",
            "Chemical exposure monitoring",
            "Contamination levels",
        ],
        "structural": ["Dust levels", "Noise levels", "Structural stability"],
        "mixed": ["Air quality", "Unknown substance detection"],
        "organic": ["Biological hazard monitoring", "Decomposition gases"],
        "metal": ["Sharp object hazards", "Heavy lift monitoring"],
    }

    return base_monitoring + type_specific.get(debris_type, [])


def generate_debris_emergency_procedures(debris_type: str) -> list[str]:
    """Generate emergency procedures for debris operations."""
    base_procedures = [
        "Immediate stop work signal and procedures",
        "Personnel evacuation routes and rally points",
        "Emergency communication procedures",
        "Medical emergency response",
    ]

    type_specific = {
        "hazardous": [
            "Chemical spill response procedures",
            "Decontamination procedures",
            "Emergency medical treatment for chemical exposure",
        ],
        "structural": [
            "Secondary collapse response",
            "Equipment emergency shutdown",
            "Structural failure evacuation",
        ],
    }

    return base_procedures + type_specific.get(debris_type, [])


def generate_quality_control_points(debris_type: str) -> list[str]:
    """Generate quality control points for debris operations."""
    base_qc = [
        "Volume measurement accuracy",
        "Proper segregation and sorting",
        "Transportation load verification",
        "Disposal site compliance",
    ]

    type_specific = {
        "hazardous": [
            "Hazmat classification verification",
            "Chain of custody documentation",
        ],
        "mixed": ["Contamination screening", "Recycling material separation"],
        "structural": ["Recyclable material identification", "Asbestos screening"],
        "metal": ["Ferrous/non-ferrous separation", "Scrap value documentation"],
    }

    return base_qc + type_specific.get(debris_type, [])
