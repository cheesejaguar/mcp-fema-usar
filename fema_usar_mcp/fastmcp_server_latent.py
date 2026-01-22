"""FastMCP server with latent tool loading for FEMA USAR.

This server implementation uses registry-based lazy loading to reduce
initial token consumption from ~122,800 to ~5,200 (96% reduction).

Instead of loading all 38+ tools at startup, this server exposes only
4 meta-tools that allow discovery and execution of any USAR tool on demand.

Usage:
    # Start with latent loading
    fema-usar-mcp-latent

    # Or set environment variable with regular server
    USAR_MCP_LATENT_LOADING=true fema-usar-mcp
"""

import json
import logging
import os
import sys
from datetime import datetime

from fastmcp import FastMCP

from .performance import get_performance_stats
from .tool_registry import get_registry, initialize_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance with latent loading
mcp = FastMCP("fema-usar-mcp-latent")


@mcp.tool()
def usar_browse_categories() -> str:
    """Browse available USAR tool categories with descriptions.

    Use this tool to discover what types of USAR tools are available.
    This is the starting point for exploring the 38+ USAR tools organized
    across 8 functional groups.

    Returns:
        JSON string with category list, tool counts, and descriptions
    """
    try:
        registry = initialize_registry()
        categories = registry.get_categories()

        return json.dumps(
            {
                "tool": "USAR Category Browser",
                "status": "success",
                "server_mode": "latent_loading",
                "total_tools": sum(cat["count"] for cat in categories.values()),
                "categories": categories,
                "usage_hint": "Use usar_list_tools(category) to see tools in a specific category",
            },
            indent=2,
        )
    except Exception as e:
        logger.error(f"Category browse error: {str(e)}", exc_info=True)
        return json.dumps(
            {"tool": "USAR Category Browser", "status": "error", "error": str(e)},
            indent=2,
        )


@mcp.tool()
def usar_list_tools(category: str = "all", include_parameters: bool = False) -> str:
    """List USAR tools in a category with optional parameter preview.

    Args:
        category: Category to filter by. Options:
            - command: Task Force leadership and safety tools
            - search: Victim location and search pattern tools
            - rescue: Squad operations and extraction tools
            - medical: Patient care and triage tools
            - planning: Situational awareness and documentation tools
            - logistics: Supply chain and facilities tools
            - technical: Structural assessment and hazmat tools
            - decision_support: AI-powered decision support tools
            - system: Performance and status tools
            - all: Show all tools (default)
        include_parameters: Include key parameters in the output

    Returns:
        JSON string with tool list and descriptions
    """
    try:
        registry = initialize_registry()
        tools = registry.list_tools(
            category=category, include_parameters=include_parameters
        )

        return json.dumps(
            {
                "tool": "USAR Tool Lister",
                "status": "success",
                "category_filter": category,
                "tool_count": len(tools),
                "tools": tools,
                "usage_hint": "Use usar_get_tool_schema(tool_name) to get full schema, or usar_execute_tool(tool_name, parameters) to execute",
            },
            indent=2,
        )
    except Exception as e:
        logger.error(f"Tool list error: {str(e)}", exc_info=True)
        return json.dumps(
            {"tool": "USAR Tool Lister", "status": "error", "error": str(e)}, indent=2
        )


@mcp.tool()
def usar_get_tool_schema(tool_name: str) -> str:
    """Load and return the full schema for a specific USAR tool.

    This dynamically imports the tool and extracts its full parameter schema
    including types, defaults, and descriptions.

    Args:
        tool_name: Name of the tool to get schema for

    Returns:
        JSON string with full tool schema including all parameters
    """
    try:
        registry = initialize_registry()
        schema = registry.load_tool_schema(tool_name)

        if schema is None:
            available_tools = [m.name for m in registry.get_all_metadata().values()]
            return json.dumps(
                {
                    "tool": "USAR Schema Loader",
                    "status": "error",
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": available_tools,
                },
                indent=2,
            )

        return json.dumps(
            {
                "tool": "USAR Schema Loader",
                "status": "success",
                "schema": schema,
                "usage_hint": f"Use usar_execute_tool('{tool_name}', '{{...}}') to execute with parameters",
            },
            indent=2,
        )
    except Exception as e:
        logger.error(f"Schema load error: {str(e)}", exc_info=True)
        return json.dumps(
            {"tool": "USAR Schema Loader", "status": "error", "error": str(e)}, indent=2
        )


@mcp.tool()
def usar_execute_tool(tool_name: str, parameters: str = "{}") -> str:
    """Execute any USAR tool by name with JSON parameters.

    This is a meta-tool that can execute any of the 38+ registered USAR tools
    without needing to load them as separate MCP tools. This enables latent
    loading where tools are only imported when actually used.

    Args:
        tool_name: Name of the tool to execute
        parameters: JSON string of parameters to pass to the tool

    Returns:
        Tool execution result as JSON string

    Examples:
        usar_execute_tool("task_force_leader_dashboard", '{"task_force_id": "CA-TF1"}')
        usar_execute_tool("victim_location_tracker", '{"search_area_id": "AREA-A1", "victim_status": "confirmed"}')
    """
    try:
        registry = initialize_registry()

        # Parse parameters
        try:
            params = json.loads(parameters) if parameters != "{}" else {}
        except json.JSONDecodeError as e:
            return json.dumps(
                {
                    "tool": "USAR Tool Executor",
                    "status": "error",
                    "error": f"Invalid JSON parameters: {str(e)}",
                    "parameters_received": parameters,
                    "hint": 'Parameters must be valid JSON, e.g., \'{"key": "value"}\'',
                },
                indent=2,
            )

        # Execute the tool
        result = registry.execute_tool(tool_name, params)
        return result

    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}", exc_info=True)
        return json.dumps(
            {"tool": "USAR Tool Executor", "status": "error", "error": str(e)}, indent=2
        )


@mcp.tool()
def usar_health_check() -> str:
    """System health and readiness check for latent loading mode.

    Returns comprehensive health status including:
    - Tool registry status
    - Cache statistics
    - Performance metrics
    - System readiness

    Returns:
        JSON string with health check results
    """
    try:
        # Get registry stats
        registry = get_registry()
        registry_stats = registry.get_stats()

        # Get performance stats
        perf_stats = get_performance_stats()

        health_data = {
            "tool": "USAR Health Check",
            "status": "healthy",
            "server_mode": "latent_loading",
            "timestamp": datetime.now().isoformat(),
            "registry": {
                "total_tools": registry_stats["total_tools_registered"],
                "tools_loaded": registry_stats["tools_loaded"],
                "schemas_cached": registry_stats["schemas_cached"],
                "cache_hit_rate": f"{registry_stats['cache_hit_rate']:.1%}",
            },
            "performance": {
                "cache_size": perf_stats["cache"]["cache_size"],
                "cache_hit_rate": f"{perf_stats['cache']['hit_rate']:.1%}",
                "active_tasks": perf_stats["active_tasks"],
                "memory_usage_mb": f"{perf_stats['cache']['memory_usage_mb']:.2f}",
            },
            "token_savings": {
                "eager_loading_tokens": "~122,800",
                "latent_loading_tokens": "~5,200",
                "reduction_percent": "96%",
            },
            "system_ready": True,
            "functional_groups_available": list(registry_stats["categories"].keys()),
        }

        return json.dumps(health_data, indent=2)

    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        return json.dumps(
            {
                "tool": "USAR Health Check",
                "status": "unhealthy",
                "error": str(e),
                "system_ready": False,
            },
            indent=2,
        )


@mcp.tool()
def usar_metrics() -> str:
    """Get detailed performance metrics and cache statistics.

    Returns:
        JSON string with comprehensive metrics including:
        - Tool registry statistics
        - Cache performance
        - Memory usage
        - Tool usage patterns
    """
    try:
        # Get all stats
        registry = get_registry()
        registry_stats = registry.get_stats()
        perf_stats = get_performance_stats()

        metrics_data = {
            "tool": "USAR Metrics",
            "status": "success",
            "server_mode": "latent_loading",
            "timestamp": datetime.now().isoformat(),
            "tool_registry": {
                "total_registered": registry_stats["total_tools_registered"],
                "dynamically_loaded": registry_stats["tools_loaded"],
                "schemas_cached": registry_stats["schemas_cached"],
                "load_operations": registry_stats["load_count"],
                "cache_hits": registry_stats["cache_hits"],
                "cache_misses": registry_stats["cache_misses"],
                "cache_hit_rate": registry_stats["cache_hit_rate"],
                "tools_by_category": registry_stats["categories"],
            },
            "performance_cache": {
                "size": perf_stats["cache"]["cache_size"],
                "max_size": perf_stats["cache"]["max_size"],
                "hits": perf_stats["cache"]["hits"],
                "misses": perf_stats["cache"]["misses"],
                "evictions": perf_stats["cache"]["evictions"],
                "hit_rate": perf_stats["cache"]["hit_rate"],
                "memory_mb": perf_stats["cache"]["memory_usage_mb"],
            },
            "async_tasks": {
                "active": perf_stats["active_tasks"],
            },
            "counters": perf_stats.get("counters", {}),
        }

        return json.dumps(metrics_data, indent=2)

    except Exception as e:
        logger.error(f"Metrics error: {str(e)}", exc_info=True)
        return json.dumps(
            {"tool": "USAR Metrics", "status": "error", "error": str(e)}, indent=2
        )


def run():
    """Run the latent loading MCP server."""
    try:
        # Initialize the registry with metadata (but don't load tools)
        registry = initialize_registry()
        stats = registry.get_stats()

        logger.info("Starting Federal USAR MCP server (latent loading mode)...")
        logger.info(
            f"Tool registry initialized with {stats['total_tools_registered']} tools"
        )
        logger.info(f"Server exposing {len(mcp._tools)} meta-tools")
        logger.info("Token reduction: ~122,800 -> ~5,200 (96% reduction)")
        logger.info(
            "Functional groups: Command, Search, Rescue, Medical, Planning, Logistics, Technical, Decision Support"
        )
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


def should_use_latent_loading() -> bool:
    """Check if latent loading should be enabled.

    Returns:
        True if latent loading is enabled via environment variable
    """
    return os.environ.get("USAR_MCP_LATENT_LOADING", "").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


if __name__ == "__main__":
    run()
