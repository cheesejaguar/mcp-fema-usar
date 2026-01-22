"""Tool metadata definitions for FEMA USAR MCP latent loading.

This module defines lightweight metadata for all 38+ USAR tools without
importing their implementations. This enables a ~96% reduction in initial
token consumption.
"""

from .tool_registry import FunctionalGroup, ToolMetadata


def get_command_tools() -> list[ToolMetadata]:
    """Get metadata for Command Group tools."""
    return [
        ToolMetadata(
            name="task_force_leader_dashboard",
            category=FunctionalGroup.COMMAND,
            description="AI-enhanced situational awareness dashboard for Task Force Leader",
            module_path="fema_usar_mcp.tools.command",
            function_name="task_force_leader_dashboard",
            key_parameters=[
                "task_force_id",
                "include_personnel",
                "include_equipment",
                "include_missions",
            ],
            cache_ttl=120,
            tags=["dashboard", "leadership", "overview"],
        ),
        ToolMetadata(
            name="safety_officer_monitor",
            category=FunctionalGroup.COMMAND,
            description="Real-time hazard monitoring and personnel safety tracking",
            module_path="fema_usar_mcp.tools.command",
            function_name="safety_officer_monitor",
            key_parameters=["monitoring_mode", "location_filter"],
            cache_ttl=60,
            tags=["safety", "monitoring", "hazards"],
        ),
        ToolMetadata(
            name="personnel_accountability",
            category=FunctionalGroup.COMMAND,
            description="Real-time personnel location and accountability tracking",
            module_path="fema_usar_mcp.tools.command",
            function_name="personnel_accountability",
            key_parameters=["accountability_type", "functional_group"],
            cache_ttl=60,
            tags=["personnel", "tracking", "accountability"],
        ),
        ToolMetadata(
            name="mission_assignment_tracker",
            category=FunctionalGroup.COMMAND,
            description="Track mission assignments and operational progress",
            module_path="fema_usar_mcp.tools.command",
            function_name="mission_assignment_tracker",
            key_parameters=["mission_status", "priority_filter"],
            cache_ttl=60,
            tags=["missions", "assignments", "tracking"],
        ),
        ToolMetadata(
            name="external_coordination",
            category=FunctionalGroup.COMMAND,
            description="Coordinate with external agencies and incident command",
            module_path="fema_usar_mcp.tools.command",
            function_name="external_coordination",
            key_parameters=["coordination_type", "communication_status"],
            cache_ttl=300,
            tags=["coordination", "agencies", "communication"],
        ),
    ]


def get_search_tools() -> list[ToolMetadata]:
    """Get metadata for Search Group tools."""
    return [
        ToolMetadata(
            name="victim_location_tracker",
            category=FunctionalGroup.SEARCH,
            description="Advanced victim location tracking with AI-powered analysis",
            module_path="fema_usar_mcp.tools.search",
            function_name="victim_location_tracker",
            key_parameters=[
                "search_area_id",
                "victim_status",
                "include_gps",
                "ai_analysis",
            ],
            cache_ttl=60,
            tags=["victims", "tracking", "ai", "location"],
        ),
        ToolMetadata(
            name="search_pattern_planner",
            category=FunctionalGroup.SEARCH,
            description="Plan and monitor search patterns for systematic coverage",
            module_path="fema_usar_mcp.tools.search",
            function_name="search_pattern_planner",
            key_parameters=["building_type", "search_method", "team_assignments"],
            cache_ttl=300,
            tags=["search", "patterns", "planning"],
        ),
        ToolMetadata(
            name="technical_search_equipment",
            category=FunctionalGroup.SEARCH,
            description="Manage technical search equipment operations and data",
            module_path="fema_usar_mcp.tools.search",
            function_name="technical_search_equipment",
            key_parameters=["equipment_type", "operation_mode"],
            cache_ttl=60,
            tags=["equipment", "technical", "sensors"],
        ),
        ToolMetadata(
            name="canine_team_deployment",
            category=FunctionalGroup.SEARCH,
            description="Manage canine search team deployment and effectiveness",
            module_path="fema_usar_mcp.tools.search",
            function_name="canine_team_deployment",
            key_parameters=[
                "search_type",
                "deployment_status",
                "environmental_conditions",
            ],
            cache_ttl=120,
            tags=["canine", "k9", "deployment"],
        ),
        ToolMetadata(
            name="void_space_assessment",
            category=FunctionalGroup.SEARCH,
            description="Assess void spaces for victim survivability and accessibility",
            module_path="fema_usar_mcp.tools.search",
            function_name="void_space_assessment",
            key_parameters=["assessment_type", "priority_level"],
            cache_ttl=300,
            tags=["voids", "survivability", "assessment"],
        ),
    ]


def get_rescue_tools() -> list[ToolMetadata]:
    """Get metadata for Rescue Group tools."""
    return [
        ToolMetadata(
            name="rescue_squad_operations",
            category=FunctionalGroup.RESCUE,
            description="Manage rescue squad deployment and tactical operations",
            module_path="fema_usar_mcp.tools.rescue",
            function_name="rescue_squad_operations",
            key_parameters=[
                "squad_id",
                "operation_type",
                "victim_id",
                "location",
                "personnel_assigned",
            ],
            cache_ttl=60,
            tags=["squads", "operations", "tactical"],
        ),
        ToolMetadata(
            name="victim_extraction_planner",
            category=FunctionalGroup.RESCUE,
            description="Plan comprehensive victim extraction operations",
            module_path="fema_usar_mcp.tools.rescue",
            function_name="victim_extraction_planner",
            key_parameters=[
                "victim_id",
                "victim_location",
                "extraction_method",
                "victim_condition",
                "entrapment_type",
                "access_difficulty",
            ],
            cache_ttl=300,
            tags=["extraction", "planning", "victims"],
        ),
        ToolMetadata(
            name="structural_stabilization",
            category=FunctionalGroup.RESCUE,
            description="Track and manage structural stabilization and shoring",
            module_path="fema_usar_mcp.tools.rescue",
            function_name="structural_stabilization",
            key_parameters=[
                "structure_location",
                "stabilization_type",
                "urgency",
                "structural_damage",
            ],
            cache_ttl=300,
            tags=["structural", "shoring", "stabilization"],
        ),
        ToolMetadata(
            name="heavy_equipment_operations",
            category=FunctionalGroup.RESCUE,
            description="Manage heavy equipment deployment and safety protocols",
            module_path="fema_usar_mcp.tools.rescue",
            function_name="heavy_equipment_operations",
            key_parameters=[
                "equipment_type",
                "operation_mode",
                "location",
                "operator_qualified",
            ],
            cache_ttl=120,
            tags=["heavy equipment", "operations", "safety"],
        ),
        ToolMetadata(
            name="debris_removal_coordinator",
            category=FunctionalGroup.RESCUE,
            description="Coordinate debris removal operations with progress tracking",
            module_path="fema_usar_mcp.tools.rescue",
            function_name="debris_removal_coordinator",
            key_parameters=["area_id", "removal_priority", "debris_type"],
            cache_ttl=120,
            tags=["debris", "removal", "coordination"],
        ),
    ]


def get_medical_tools() -> list[ToolMetadata]:
    """Get metadata for Medical Group tools."""
    return [
        ToolMetadata(
            name="patient_care_tracker",
            category=FunctionalGroup.MEDICAL,
            description="Track patient care and generate ICS-213 documentation",
            module_path="fema_usar_mcp.tools.medical",
            function_name="patient_care_tracker",
            key_parameters=[
                "patient_id",
                "triage_priority",
                "chief_complaint",
                "vital_signs",
            ],
            cache_ttl=60,
            tags=["patients", "care", "documentation"],
        ),
        ToolMetadata(
            name="medical_supply_inventory",
            category=FunctionalGroup.MEDICAL,
            description="Manage medical supply inventory with consumption tracking",
            module_path="fema_usar_mcp.tools.medical",
            function_name="medical_supply_inventory",
            key_parameters=[
                "inventory_action",
                "supply_category",
                "location",
                "low_stock_threshold",
            ],
            cache_ttl=600,
            tags=["inventory", "supplies", "medical"],
        ),
        ToolMetadata(
            name="triage_coordinator",
            category=FunctionalGroup.MEDICAL,
            description="Coordinate triage operations with patient flow management",
            module_path="fema_usar_mcp.tools.medical",
            function_name="triage_coordinator",
            key_parameters=[
                "triage_location",
                "operation_mode",
                "patient_flow_rate",
                "transport_availability",
            ],
            cache_ttl=60,
            tags=["triage", "coordination", "patient flow"],
        ),
        ToolMetadata(
            name="health_surveillance",
            category=FunctionalGroup.MEDICAL,
            description="Monitor personnel health and environmental hazards",
            module_path="fema_usar_mcp.tools.medical",
            function_name="health_surveillance",
            key_parameters=[
                "monitoring_scope",
                "surveillance_type",
                "alert_threshold",
                "environmental_hazards",
            ],
            cache_ttl=300,
            tags=["health", "surveillance", "monitoring"],
        ),
        ToolMetadata(
            name="evacuation_coordinator",
            category=FunctionalGroup.MEDICAL,
            description="Coordinate medical evacuation and transport logistics",
            module_path="fema_usar_mcp.tools.medical",
            function_name="evacuation_coordinator",
            key_parameters=[
                "evacuation_type",
                "transport_mode",
                "destination_type",
                "patient_acuity",
            ],
            cache_ttl=60,
            tags=["evacuation", "transport", "medical"],
        ),
    ]


def get_planning_tools() -> list[ToolMetadata]:
    """Get metadata for Planning Section tools."""
    return [
        ToolMetadata(
            name="situation_unit_dashboard",
            category=FunctionalGroup.PLANNING,
            description="Situational awareness dashboard with incident status",
            module_path="fema_usar_mcp.tools.planning",
            function_name="situation_unit_dashboard",
            key_parameters=["incident_id", "display_mode", "include_weather"],
            cache_ttl=60,
            tags=["situation", "dashboard", "awareness"],
        ),
        ToolMetadata(
            name="resource_unit_tracker",
            category=FunctionalGroup.PLANNING,
            description="Track and manage resource allocation and availability",
            module_path="fema_usar_mcp.tools.planning",
            function_name="resource_unit_tracker",
            key_parameters=["resource_type", "tracking_mode", "availability_filter"],
            cache_ttl=120,
            tags=["resources", "tracking", "allocation"],
        ),
        ToolMetadata(
            name="documentation_automation",
            category=FunctionalGroup.PLANNING,
            description="Automate ICS documentation and form generation",
            module_path="fema_usar_mcp.tools.planning",
            function_name="documentation_automation",
            key_parameters=["document_type", "incident_id", "auto_populate"],
            cache_ttl=600,
            tags=["documentation", "ics", "forms"],
        ),
        ToolMetadata(
            name="demobilization_planner",
            category=FunctionalGroup.PLANNING,
            description="Plan and track demobilization operations",
            module_path="fema_usar_mcp.tools.planning",
            function_name="demobilization_planner",
            key_parameters=["task_force_id", "demob_phase", "release_priority"],
            cache_ttl=600,
            tags=["demobilization", "planning", "release"],
        ),
        ToolMetadata(
            name="operational_timeline",
            category=FunctionalGroup.PLANNING,
            description="Track operational milestones and timeline management",
            module_path="fema_usar_mcp.tools.planning",
            function_name="operational_timeline",
            key_parameters=["timeline_scope", "milestone_filter", "include_completed"],
            cache_ttl=300,
            tags=["timeline", "milestones", "operations"],
        ),
    ]


def get_logistics_tools() -> list[ToolMetadata]:
    """Get metadata for Logistics Section tools."""
    return [
        ToolMetadata(
            name="supply_chain_manager",
            category=FunctionalGroup.LOGISTICS,
            description="Manage supply chain operations and inventory",
            module_path="fema_usar_mcp.tools.logistics",
            function_name="supply_chain_manager",
            key_parameters=["supply_category", "operation_mode", "forecast_days"],
            cache_ttl=600,
            tags=["supply chain", "inventory", "logistics"],
        ),
        ToolMetadata(
            name="facilities_coordinator",
            category=FunctionalGroup.LOGISTICS,
            description="Coordinate base of operations and facility management",
            module_path="fema_usar_mcp.tools.logistics",
            function_name="facilities_coordinator",
            key_parameters=["facility_type", "coordination_mode", "capacity_check"],
            cache_ttl=300,
            tags=["facilities", "base", "coordination"],
        ),
        ToolMetadata(
            name="ground_support_tracker",
            category=FunctionalGroup.LOGISTICS,
            description="Track ground support operations and transportation",
            module_path="fema_usar_mcp.tools.logistics",
            function_name="ground_support_tracker",
            key_parameters=["support_type", "vehicle_status", "fuel_tracking"],
            cache_ttl=120,
            tags=["ground support", "vehicles", "transport"],
        ),
        ToolMetadata(
            name="fuel_management",
            category=FunctionalGroup.LOGISTICS,
            description="Manage fuel inventory and consumption tracking",
            module_path="fema_usar_mcp.tools.logistics",
            function_name="fuel_management",
            key_parameters=["fuel_type", "inventory_action", "consumption_period"],
            cache_ttl=300,
            tags=["fuel", "inventory", "consumption"],
        ),
        ToolMetadata(
            name="maintenance_scheduler",
            category=FunctionalGroup.LOGISTICS,
            description="Schedule and track equipment maintenance",
            module_path="fema_usar_mcp.tools.logistics",
            function_name="maintenance_scheduler",
            key_parameters=["equipment_category", "schedule_type", "urgency_filter"],
            cache_ttl=600,
            tags=["maintenance", "equipment", "scheduling"],
        ),
    ]


def get_technical_tools() -> list[ToolMetadata]:
    """Get metadata for Technical Specialist tools."""
    return [
        ToolMetadata(
            name="structural_assessment",
            category=FunctionalGroup.TECHNICAL,
            description="Comprehensive structural damage assessment",
            module_path="fema_usar_mcp.tools.technical",
            function_name="structural_assessment",
            key_parameters=[
                "building_id",
                "assessment_type",
                "damage_level",
                "include_recommendations",
            ],
            cache_ttl=300,
            tags=["structural", "assessment", "damage"],
        ),
        ToolMetadata(
            name="hazmat_monitoring",
            category=FunctionalGroup.TECHNICAL,
            description="Monitor hazardous materials and environmental conditions",
            module_path="fema_usar_mcp.tools.technical",
            function_name="hazmat_monitoring",
            key_parameters=["monitoring_type", "location", "alert_threshold"],
            cache_ttl=60,
            tags=["hazmat", "monitoring", "environmental"],
        ),
        ToolMetadata(
            name="communications_manager",
            category=FunctionalGroup.TECHNICAL,
            description="Manage communications systems and interoperability",
            module_path="fema_usar_mcp.tools.technical",
            function_name="communications_manager",
            key_parameters=["system_type", "operation_mode", "frequency_allocation"],
            cache_ttl=120,
            tags=["communications", "radio", "interoperability"],
        ),
        ToolMetadata(
            name="rigging_calculator",
            category=FunctionalGroup.TECHNICAL,
            description="Calculate rigging configurations and load limits",
            module_path="fema_usar_mcp.tools.technical",
            function_name="rigging_calculator",
            key_parameters=[
                "rigging_type",
                "load_weight",
                "sling_angle",
                "safety_factor",
            ],
            cache_ttl=600,
            tags=["rigging", "calculations", "loads"],
        ),
        ToolMetadata(
            name="environmental_monitor",
            category=FunctionalGroup.TECHNICAL,
            description="Monitor environmental conditions affecting operations",
            module_path="fema_usar_mcp.tools.technical",
            function_name="environmental_monitor",
            key_parameters=["monitoring_scope", "include_forecast", "alert_settings"],
            cache_ttl=60,
            tags=["environmental", "weather", "conditions"],
        ),
    ]


def get_decision_support_tools() -> list[ToolMetadata]:
    """Get metadata for Decision Support tools."""
    return [
        ToolMetadata(
            name="tactical_decision_support",
            category=FunctionalGroup.DECISION_SUPPORT,
            description="AI-powered tactical decision support for operations",
            module_path="fema_usar_mcp.tools.decision_support",
            function_name="tactical_decision_support",
            key_parameters=["decision_context", "options", "risk_tolerance"],
            cache_ttl=120,
            tags=["ai", "tactical", "decisions"],
        ),
        ToolMetadata(
            name="strategic_planning_advisor",
            category=FunctionalGroup.DECISION_SUPPORT,
            description="Strategic planning recommendations and scenario analysis",
            module_path="fema_usar_mcp.tools.decision_support",
            function_name="strategic_planning_advisor",
            key_parameters=[
                "planning_horizon",
                "scenario_type",
                "resource_constraints",
            ],
            cache_ttl=300,
            tags=["ai", "strategic", "planning"],
        ),
        ToolMetadata(
            name="operational_intelligence_system",
            category=FunctionalGroup.DECISION_SUPPORT,
            description="Integrated operational intelligence and analytics",
            module_path="fema_usar_mcp.tools.decision_support",
            function_name="operational_intelligence_system",
            key_parameters=["intelligence_type", "analysis_depth", "time_range"],
            cache_ttl=60,
            tags=["ai", "intelligence", "analytics"],
        ),
    ]


def get_system_tools() -> list[ToolMetadata]:
    """Get metadata for System tools.

    Note: These are typically always loaded and not part of latent loading.
    """
    return [
        ToolMetadata(
            name="get_system_performance",
            category=FunctionalGroup.SYSTEM,
            description="Get system performance statistics and metrics",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="get_system_performance",
            key_parameters=[],
            cache_ttl=60,
            tags=["system", "performance", "metrics"],
        ),
        ToolMetadata(
            name="clear_system_cache",
            category=FunctionalGroup.SYSTEM,
            description="Clear system cache entries",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="clear_system_cache",
            key_parameters=["pattern"],
            cache_ttl=0,
            tags=["system", "cache", "management"],
        ),
        ToolMetadata(
            name="submit_async_operation",
            category=FunctionalGroup.SYSTEM,
            description="Submit operation for async processing",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="submit_async_operation",
            key_parameters=["operation", "parameters"],
            cache_ttl=0,
            tags=["system", "async", "operations"],
        ),
        ToolMetadata(
            name="get_async_task_info",
            category=FunctionalGroup.SYSTEM,
            description="Get status of async task",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="get_async_task_info",
            key_parameters=["task_id"],
            cache_ttl=0,
            tags=["system", "async", "status"],
        ),
        ToolMetadata(
            name="get_usar_system_status",
            category=FunctionalGroup.SYSTEM,
            description="Get FEMA USAR system status and capabilities",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="get_usar_system_status",
            key_parameters=[],
            cache_ttl=300,
            tags=["system", "status", "capabilities"],
        ),
        ToolMetadata(
            name="calculate_task_force_readiness",
            category=FunctionalGroup.SYSTEM,
            description="Calculate deployment readiness for a task force",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="calculate_task_force_readiness",
            key_parameters=[
                "task_force_id",
                "personnel_count",
                "equipment_ready",
                "training_compliance",
            ],
            cache_ttl=300,
            tags=["system", "readiness", "task force"],
        ),
        ToolMetadata(
            name="list_functional_groups",
            category=FunctionalGroup.SYSTEM,
            description="List all USAR functional groups and positions",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="list_functional_groups",
            key_parameters=[],
            cache_ttl=3600,
            tags=["system", "groups", "positions"],
        ),
        # Meta-tools for latent loading and tool discovery
        ToolMetadata(
            name="usar_browse_categories",
            category=FunctionalGroup.SYSTEM,
            description="Browse available USAR tool categories and their tool counts",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="usar_browse_categories",
            key_parameters=[],
            cache_ttl=3600,
            tags=["meta", "discovery", "categories"],
        ),
        ToolMetadata(
            name="usar_list_tools",
            category=FunctionalGroup.SYSTEM,
            description="List tools in a category with optional parameter details",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="usar_list_tools",
            key_parameters=["category", "include_parameters"],
            cache_ttl=3600,
            tags=["meta", "discovery", "tools"],
        ),
        ToolMetadata(
            name="usar_get_tool_schema",
            category=FunctionalGroup.SYSTEM,
            description="Load full JSON schema for a specific tool",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="usar_get_tool_schema",
            key_parameters=["tool_name"],
            cache_ttl=3600,
            tags=["meta", "schema", "discovery"],
        ),
        ToolMetadata(
            name="usar_execute_tool",
            category=FunctionalGroup.SYSTEM,
            description="Execute any USAR tool by name with JSON parameters",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="usar_execute_tool",
            key_parameters=["tool_name", "parameters"],
            cache_ttl=0,
            tags=["meta", "execution", "dynamic"],
        ),
        ToolMetadata(
            name="usar_health_check",
            category=FunctionalGroup.SYSTEM,
            description="System health and readiness check",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="usar_health_check",
            key_parameters=[],
            cache_ttl=60,
            tags=["meta", "health", "status"],
        ),
        ToolMetadata(
            name="usar_metrics",
            category=FunctionalGroup.SYSTEM,
            description="Performance metrics and cache statistics",
            module_path="fema_usar_mcp.fastmcp_server",
            function_name="usar_metrics",
            key_parameters=[],
            cache_ttl=60,
            tags=["meta", "metrics", "performance"],
        ),
    ]


def get_all_tool_metadata() -> list[ToolMetadata]:
    """Get metadata for all USAR tools.

    Returns:
        List of all tool metadata entries (38+ tools)
    """
    all_metadata = []
    all_metadata.extend(get_command_tools())
    all_metadata.extend(get_search_tools())
    all_metadata.extend(get_rescue_tools())
    all_metadata.extend(get_medical_tools())
    all_metadata.extend(get_planning_tools())
    all_metadata.extend(get_logistics_tools())
    all_metadata.extend(get_technical_tools())
    all_metadata.extend(get_decision_support_tools())
    all_metadata.extend(get_system_tools())
    return all_metadata


def get_tool_count_by_category() -> dict[str, int]:
    """Get count of tools by category.

    Returns:
        Dictionary mapping category names to tool counts
    """
    all_tools = get_all_tool_metadata()
    counts: dict[str, int] = {}
    for tool in all_tools:
        category = tool.category.value
        counts[category] = counts.get(category, 0) + 1
    return counts
