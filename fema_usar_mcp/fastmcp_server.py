"""FastMCP server implementation for FEMA USAR tools."""

import logging
import sys

from fastmcp import FastMCP

# Import core functionality
from .core import (
    OperationalStatus,
    USARTaskForceConfig,
    calculate_deployment_readiness,
    get_system_status,
)
from .performance import (
    clear_cache,
    get_async_task_result,
    get_async_task_status,
    get_performance_stats,
    submit_async_task,
)

# Import all tool modules - will be implemented in phases
from .tools.command import (
    external_coordination,
    mission_assignment_tracker,
    personnel_accountability,
    safety_officer_monitor,
    task_force_leader_dashboard,
)
from .tools.decision_support import (
    operational_intelligence_system,
    strategic_planning_advisor,
    tactical_decision_support,
)
from .tools.logistics import (
    facilities_coordinator,
    fuel_management,
    ground_support_tracker,
    maintenance_scheduler,
    supply_chain_manager,
)
from .tools.medical import (
    evacuation_coordinator,
    health_surveillance,
    medical_supply_inventory,
    patient_care_tracker,
    triage_coordinator,
)
from .tools.planning import (
    demobilization_planner,
    documentation_automation,
    operational_timeline,
    resource_unit_tracker,
    situation_unit_dashboard,
)
from .tools.rescue import (
    debris_removal_coordinator,
    heavy_equipment_operations,
    rescue_squad_operations,
    structural_stabilization,
    victim_extraction_planner,
)
from .tools.search import (
    canine_team_deployment,
    search_pattern_planner,
    technical_search_equipment,
    victim_location_tracker,
    void_space_assessment,
)
from .tools.technical import (
    communications_manager,
    environmental_monitor,
    hazmat_monitoring,
    rigging_calculator,
    structural_assessment,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("fema-usar-mcp")

# Register Command Group tools
mcp.tool(task_force_leader_dashboard)
mcp.tool(safety_officer_monitor)
mcp.tool(personnel_accountability)
mcp.tool(mission_assignment_tracker)
mcp.tool(external_coordination)

# Register Search Group tools
mcp.tool(victim_location_tracker)
mcp.tool(search_pattern_planner)
mcp.tool(technical_search_equipment)
mcp.tool(canine_team_deployment)
mcp.tool(void_space_assessment)

# Register Rescue Group tools
mcp.tool(rescue_squad_operations)
mcp.tool(victim_extraction_planner)
mcp.tool(structural_stabilization)
mcp.tool(heavy_equipment_operations)
mcp.tool(debris_removal_coordinator)

# Register Medical Group tools
mcp.tool(patient_care_tracker)
mcp.tool(medical_supply_inventory)
mcp.tool(triage_coordinator)
mcp.tool(health_surveillance)
mcp.tool(evacuation_coordinator)

# Register Planning Section tools
mcp.tool(situation_unit_dashboard)
mcp.tool(resource_unit_tracker)
mcp.tool(documentation_automation)
mcp.tool(demobilization_planner)
mcp.tool(operational_timeline)

# Register Logistics Section tools
mcp.tool(supply_chain_manager)
mcp.tool(facilities_coordinator)
mcp.tool(ground_support_tracker)
mcp.tool(fuel_management)
mcp.tool(maintenance_scheduler)

# Register Technical Specialist tools
mcp.tool(structural_assessment)
mcp.tool(hazmat_monitoring)
mcp.tool(communications_manager)
mcp.tool(rigging_calculator)
mcp.tool(environmental_monitor)

# Register Decision Support tools
mcp.tool(tactical_decision_support)
mcp.tool(strategic_planning_advisor)
mcp.tool(operational_intelligence_system)


# Performance monitoring tools
@mcp.tool()
def get_system_performance() -> str:
    """Get comprehensive system performance statistics and metrics.

    Returns:
        JSON string with performance metrics, cache statistics, and system health
    """
    try:
        stats = get_performance_stats()
        import json

        return json.dumps(
            {
                "tool": "System Performance Monitor",
                "status": "success",
                "performance_data": stats,
                "recommendations": [
                    f"Cache hit rate: {stats['cache']['hit_rate']:.1%}",
                    f"Active async tasks: {stats['active_tasks']}",
                    f"Memory usage: {stats['cache']['memory_usage_mb']:.2f} MB",
                ],
            },
            indent=2,
        )
    except Exception as e:
        import json

        return json.dumps(
            {"tool": "System Performance Monitor", "status": "error", "error": str(e)},
            indent=2,
        )


@mcp.tool()
def clear_system_cache(pattern: str = "") -> str:
    """Clear system cache entries matching optional pattern.

    Args:
        pattern: Optional pattern to match cache keys (empty = clear all)

    Returns:
        JSON string with cache clearing results
    """
    try:
        cleared_count = clear_cache(pattern if pattern else None)
        import json

        return json.dumps(
            {
                "tool": "Cache Manager",
                "status": "success",
                "cleared_entries": cleared_count,
                "pattern": pattern or "all",
                "message": f"Cleared {cleared_count} cache entries",
            },
            indent=2,
        )
    except Exception as e:
        import json

        return json.dumps(
            {"tool": "Cache Manager", "status": "error", "error": str(e)}, indent=2
        )


@mcp.tool()
def submit_async_operation(operation: str, parameters: str = "{}") -> str:
    """Submit operation for asynchronous processing.

    Args:
        operation: Name of operation to execute
        parameters: JSON string of operation parameters

    Returns:
        JSON string with async task submission details
    """
    try:
        import json
        import uuid

        task_id = f"async_{operation}_{uuid.uuid4().hex[:8]}"
        params = json.loads(parameters) if parameters != "{}" else {}

        # Placeholder for async operation execution
        def dummy_operation():
            import time

            time.sleep(1)  # Simulate work
            return {"operation": operation, "parameters": params, "result": "completed"}

        submit_async_task(task_id, dummy_operation)

        return json.dumps(
            {
                "tool": "Async Task Manager",
                "status": "submitted",
                "task_id": task_id,
                "operation": operation,
                "message": f"Task {task_id} submitted for async processing",
            },
            indent=2,
        )
    except Exception as e:
        import json

        return json.dumps(
            {"tool": "Async Task Manager", "status": "error", "error": str(e)}, indent=2
        )


@mcp.tool()
def get_async_task_info(task_id: str) -> str:
    """Get status and result of asynchronous task.

    Args:
        task_id: ID of the async task

    Returns:
        JSON string with task status and result if available
    """
    try:
        import json

        status = get_async_task_status(task_id)
        if status is None:
            return json.dumps(
                {
                    "tool": "Async Task Manager",
                    "status": "not_found",
                    "task_id": task_id,
                    "message": "Task not found",
                },
                indent=2,
            )

        result_data = {
            "tool": "Async Task Manager",
            "task_id": task_id,
            "status": status,
        }

        if status == "completed":
            try:
                result = get_async_task_result(task_id, timeout=0.1)
                result_data["result"] = result
            except Exception:
                result_data["result"] = "Result unavailable"

        return json.dumps(result_data, indent=2)
    except Exception as e:
        import json

        return json.dumps(
            {"tool": "Async Task Manager", "status": "error", "error": str(e)}, indent=2
        )


@mcp.tool()
def get_usar_system_status() -> str:
    """Get comprehensive FEMA USAR system status and capabilities.

    Returns:
        JSON string with complete system status, capabilities, and operational metrics
    """
    try:
        status = get_system_status()
        return f"""
# FEMA USAR MCP System Status

## System Information
- **System**: {status["system"]}
- **Version**: {status["version"]}
- **Status**: {status["status"]}
- **Last Updated**: {status["last_updated"]}

## Capabilities
- **Functional Groups**: {status["capabilities"]["functional_groups_supported"]} supported
- **Personnel Positions**: {status["capabilities"]["total_positions"]} tracked
- **Equipment Items**: {status["capabilities"]["total_equipment"]} managed
- **Task Forces Supported**: {status["capabilities"]["supported_task_forces"]}

## Tool Availability
- **Command Tools**: {status["capabilities"]["tools"]["command_tools"]} available
- **Search Tools**: {status["capabilities"]["tools"]["search_tools"]} available
- **Rescue Tools**: {status["capabilities"]["tools"]["rescue_tools"]} available
- **Medical Tools**: {status["capabilities"]["tools"]["medical_tools"]} available
- **Planning Tools**: {status["capabilities"]["tools"]["planning_tools"]} available
- **Logistics Tools**: {status["capabilities"]["tools"]["logistics_tools"]} available
- **Technical Tools**: {status["capabilities"]["tools"]["technical_tools"]} available

## Integration Status
- **FEMA IRIS**: {"✅ Connected" if status["capabilities"]["integrations"]["fema_iris"] else "❌ Disconnected"}
- **NIMS ICT**: {"✅ Connected" if status["capabilities"]["integrations"]["nims_ict"] else "❌ Disconnected"}
- **Federal Asset Tracking**: {"✅ Connected" if status["capabilities"]["integrations"]["federal_asset_tracking"] else "❌ Disconnected"}
- **Multi-band Radio**: {"✅ Available" if status["capabilities"]["integrations"]["multi_band_radio"] else "❌ Unavailable"}
- **Satellite Communications**: {"✅ Available" if status["capabilities"]["integrations"]["satellite_comm"] else "❌ Unavailable"}

## Operational Metrics
- **Deployment Time Target**: {status["capabilities"]["deployment_time_target"]} hours
- **Self-Sufficiency Duration**: {status["capabilities"]["self_sufficiency_hours"]} hours
- **Advanced Features**: {"✅ Available" if status["advanced_integration_available"] else "❌ Limited"}
"""
    except Exception as e:
        logger.error(f"System status retrieval error: {str(e)}", exc_info=True)
        return f"Error retrieving system status: {str(e)}"


@mcp.tool()
def calculate_task_force_readiness(
    task_force_id: str = "CA-TF1",
    personnel_count: int = 70,
    equipment_ready: int = 16400,
    training_compliance: float = 100.0,
) -> str:
    """Calculate deployment readiness for a USAR task force.

    Args:
        task_force_id: Task force identifier (e.g., CA-TF1, TX-TF1)
        personnel_count: Current personnel count (max 70)
        equipment_ready: Equipment items ready for deployment (max 16,400)
        training_compliance: Training compliance percentage (0-100)

    Returns:
        JSON string with detailed readiness assessment
    """
    try:
        # Create task force configuration
        config = USARTaskForceConfig(
            task_force_id=task_force_id,
            task_force_name=f"{task_force_id} USAR Task Force",
            home_location="Home Base",
            operational_status=OperationalStatus.READY,
            personnel_count=min(personnel_count, 70),
            equipment_ready_count=min(equipment_ready, 16400),
            training_compliance=max(0.0, min(training_compliance, 100.0)),
        )

        readiness = calculate_deployment_readiness(config)

        return f"""
# Task Force Deployment Readiness: {task_force_id}

## Overall Assessment
- **Overall Readiness**: {readiness["overall_readiness_percent"]}%
- **Deployment Capable**: {"✅ YES" if readiness["deployment_capable"] else "❌ NO"}
- **Estimated Deployment Time**: {readiness["estimated_deployment_time_hours"] or "N/A"} hours

## Readiness Breakdown
- **Personnel Readiness**: {readiness["personnel_readiness_percent"]}% ({personnel_count}/70 positions)
- **Equipment Readiness**: {readiness["equipment_readiness_percent"]}% ({equipment_ready}/16,400 items)
- **Training Compliance**: {readiness["training_readiness_percent"]}%

## Operational Capability
- **Self-Sufficiency Duration**: {readiness["self_sufficiency_hours"]} hours
- **Last Calculated**: {readiness["last_calculated"]}
- **Processing Time**: {readiness["processing_time_ms"]:.1f}ms

## Recommendations
{"- Task force ready for immediate deployment" if readiness["deployment_capable"] else "- Address deficiencies before deployment"}
{"- Maintain current readiness levels" if readiness["overall_readiness_percent"] >= 90 else "- Improve readiness to meet deployment standards"}
"""
    except Exception as e:
        logger.error(f"Readiness calculation error: {str(e)}", exc_info=True)
        return f"Error calculating task force readiness: {str(e)}"


@mcp.tool()
def list_functional_groups() -> str:
    """List all USAR functional groups and their key positions.

    Returns:
        Formatted list of functional groups and positions
    """
    try:
        from .core import get_functional_group_positions

        groups = get_functional_group_positions()

        result = "# FEMA USAR Functional Groups and Positions\n\n"

        for group, positions in groups.items():
            result += f"## {group.title()} Group\n"
            for position in positions:
                result += f"- {position}\n"
            result += "\n"

        result += f"**Total Positions**: {sum(len(positions) for positions in groups.values())} key positions\n"
        result += "**Total Personnel**: 70 personnel in a Type 1 Task Force\n"

        return result

    except Exception as e:
        logger.error(f"Functional groups listing error: {str(e)}", exc_info=True)
        return f"Error listing functional groups: {str(e)}"


def run():
    """Run the MCP server."""
    try:
        logger.info("Starting FEMA USAR MCP server...")
        logger.info(f"Server initialized with {len(mcp._tools)} tools registered")
        logger.info(
            "Functional groups supported: Command, Search, Rescue, Medical, Planning, Logistics, Technical"
        )
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
