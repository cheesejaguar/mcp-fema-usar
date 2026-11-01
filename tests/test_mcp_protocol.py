"""In-memory MCP protocol tests for FEMA USAR server.

These tests verify MCP tool discovery and invocation using FastMCP's
in-memory testing capabilities.
"""

import json
import threading

import pytest

from fema_usar_mcp.tool_registry import ToolRegistry

# Tools whose default invocation currently fails inside the product code.
# The medical helper stubs (fema_usar_mcp/tools/medical.py) were written with a
# single ``data`` parameter but are called with 0-4 positional arguments, and
# several callers index the stub return values with keys the stubs never set.
BROKEN_MEDICAL_TOOLS = {
    "medical_supply_inventory": (
        "generate_inventory_alerts() takes 1 positional arg but is called with 2; "
        "out_of_stock_items is an int but the caller calls len() on it"
    ),
    "triage_coordinator": (
        "generate_priority_queue() takes 1 positional arg but is called with 2; "
        "assess_triage_resource_needs() result lacks the 'personnel' key"
    ),
    "health_surveillance": (
        "assess_environmental_health_risks() takes 1 positional arg but is called "
        "with 2; its result lacks the 'risk_levels' key"
    ),
    "evacuation_coordinator": (
        "assess_transport_feasibility() takes 1 positional arg but is called with 4; "
        "generate_patient_preparation_requirements() returns a list, not a dict"
    ),
}

# Tools that need arguments, or that intentionally return Markdown, not JSON.
NON_DEFAULT_TOOLS = {
    "get_async_task_info",
    "submit_async_operation",
    "usar_execute_tool",
    "usar_get_tool_schema",
}
MARKDOWN_TOOLS = {
    "calculate_task_force_readiness",
    "get_usar_system_status",
    "list_functional_groups",
}


def _all_registered_tool_names():
    from fema_usar_mcp.tool_registry import initialize_registry

    return sorted(tool["name"] for tool in initialize_registry().list_tools("all"))


class TestToolDiscovery:
    """Test MCP tool discovery and listing."""

    @pytest.mark.unit
    async def test_eager_server_has_minimum_tools(self, mcp_server):
        """Verify eager server has at least 35 tools registered."""
        tools = await mcp_server.get_tools()
        assert len(tools) >= 35, f"Expected at least 35 tools, found {len(tools)}"

    @pytest.mark.unit
    async def test_latent_server_has_meta_tools_only(self, latent_mcp_server):
        """Verify latent server exposes only meta-tools."""
        tools = await latent_mcp_server.get_tools()
        assert set(tools) == {
            "usar_browse_categories",
            "usar_list_tools",
            "usar_get_tool_schema",
            "usar_execute_tool",
            "usar_health_check",
            "usar_metrics",
        }

    @pytest.mark.unit
    async def test_command_tools_registered(self, mcp_server):
        """Verify Command Group tools are registered."""
        tools = await mcp_server.get_tools()
        tool_names = list(tools.keys())

        command_tools = [
            "task_force_leader_dashboard",
            "safety_officer_monitor",
            "personnel_accountability",
            "mission_assignment_tracker",
            "external_coordination",
        ]

        for tool_name in command_tools:
            assert tool_name in tool_names, f"Missing command tool: {tool_name}"

    @pytest.mark.unit
    async def test_search_tools_registered(self, mcp_server):
        """Verify Search Group tools are registered."""
        tools = await mcp_server.get_tools()
        tool_names = list(tools.keys())

        search_tools = [
            "victim_location_tracker",
            "search_pattern_planner",
            "technical_search_equipment",
            "canine_team_deployment",
            "void_space_assessment",
        ]

        for tool_name in search_tools:
            assert tool_name in tool_names, f"Missing search tool: {tool_name}"

    @pytest.mark.unit
    async def test_rescue_tools_registered(self, mcp_server):
        """Verify Rescue Group tools are registered."""
        tools = await mcp_server.get_tools()
        tool_names = list(tools.keys())

        rescue_tools = [
            "rescue_squad_operations",
            "victim_extraction_planner",
            "structural_stabilization",
            "heavy_equipment_operations",
            "debris_removal_coordinator",
        ]

        for tool_name in rescue_tools:
            assert tool_name in tool_names, f"Missing rescue tool: {tool_name}"

    @pytest.mark.unit
    async def test_medical_tools_registered(self, mcp_server):
        """Verify Medical Group tools are registered."""
        tools = await mcp_server.get_tools()
        tool_names = list(tools.keys())

        medical_tools = [
            "patient_care_tracker",
            "medical_supply_inventory",
            "triage_coordinator",
            "health_surveillance",
            "evacuation_coordinator",
        ]

        for tool_name in medical_tools:
            assert tool_name in tool_names, f"Missing medical tool: {tool_name}"


class TestToolRegistry:
    """Test the tool registry for latent loading."""

    @pytest.mark.unit
    def test_registry_initialization(self, tool_registry):
        """Test registry initializes with all tool metadata."""
        stats = tool_registry.get_stats()
        assert stats["total_tools_registered"] >= 38

    @pytest.mark.unit
    def test_registry_categories(self, tool_registry):
        """Test registry provides correct categories."""
        categories = tool_registry.get_categories()

        expected_categories = [
            "command",
            "search",
            "rescue",
            "medical",
            "planning",
            "logistics",
            "technical",
            "decision_support",
            "system",
        ]

        for cat in expected_categories:
            assert cat in categories, f"Missing category: {cat}"

    @pytest.mark.unit
    def test_registry_list_tools(self, tool_registry):
        """Test listing tools by category."""
        # List all tools
        all_tools = tool_registry.list_tools(category="all")
        assert len(all_tools) >= 38

        # List command tools
        command_tools = tool_registry.list_tools(category="command")
        assert len(command_tools) == 5

        # List with parameters
        tools_with_params = tool_registry.list_tools(
            category="command", include_parameters=True
        )
        assert "key_parameters" in tools_with_params[0]

    @pytest.mark.unit
    def test_registry_get_metadata(self, tool_registry):
        """Test getting individual tool metadata."""
        metadata = tool_registry.get_metadata("task_force_leader_dashboard")

        assert metadata is not None
        assert metadata.name == "task_force_leader_dashboard"
        assert metadata.category.value == "command"
        assert len(metadata.description) > 0

    @pytest.mark.unit
    def test_registry_load_tool_function(self, tool_registry):
        """Test dynamic tool function loading."""
        func = tool_registry.load_tool_function("task_force_leader_dashboard")

        assert func is not None
        assert callable(func)

        from fema_usar_mcp.tools.command import task_force_leader_dashboard

        assert func is task_force_leader_dashboard

        # Execute the loaded function
        data = json.loads(func(task_force_id="TEST-TF1"))
        assert data["status"] == "success"
        assert data["data"]["task_force_id"] == "TEST-TF1"

    @pytest.mark.unit
    def test_registry_load_tool_schema(self, tool_registry):
        """Test schema extraction from loaded tools."""
        schema = tool_registry.load_tool_schema("task_force_leader_dashboard")

        assert schema is not None
        assert "name" in schema
        assert "description" in schema
        assert "inputSchema" in schema
        assert schema["name"] == "task_force_leader_dashboard"

    @pytest.mark.unit
    def test_registry_execute_tool(self, tool_registry):
        """Test executing tools through the registry."""
        result = tool_registry.execute_tool(
            "task_force_leader_dashboard", {"task_force_id": "TEST-TF1"}
        )

        data = json.loads(result)
        assert data["status"] == "success"
        assert data["data"]["task_force_id"] == "TEST-TF1"

    @pytest.mark.unit
    def test_registry_execute_tool_invalid_params(self, tool_registry):
        """Unknown parameters produce a structured error, not an exception."""
        result = tool_registry.execute_tool(
            "task_force_leader_dashboard", {"no_such_param": 1}
        )
        data = json.loads(result)
        assert data["error"] == (
            "Invalid parameters for tool 'task_force_leader_dashboard'"
        )
        assert "no_such_param" in data["details"]

    @pytest.mark.unit
    def test_registry_execute_nonexistent_tool(self, tool_registry):
        """Test executing a nonexistent tool returns error."""
        result = tool_registry.execute_tool("nonexistent_tool")

        data = json.loads(result)
        assert data["error"] == "Tool 'nonexistent_tool' not found"
        assert "task_force_leader_dashboard" in data["available_tools"]

    @pytest.mark.unit
    def test_registry_caching(self, tool_registry):
        """Test schema caching works correctly."""
        # First load
        tool_registry.load_tool_schema("task_force_leader_dashboard")
        stats1 = tool_registry.get_stats()

        # Second load (should hit cache)
        tool_registry.load_tool_schema("task_force_leader_dashboard")
        stats2 = tool_registry.get_stats()

        assert stats2["cache_hits"] > stats1["cache_hits"]


class TestMetaTools:
    """Test meta-tool functionality for latent loading."""

    @pytest.mark.unit
    def test_usar_browse_categories(self, tool_registry):
        """Test the category browsing meta-tool."""
        categories = tool_registry.get_categories()

        assert len(categories) >= 8
        for cat_info in categories.values():
            assert "count" in cat_info
            assert "tools" in cat_info
            assert "description" in cat_info
            assert cat_info["count"] > 0

    @pytest.mark.unit
    def test_usar_list_tools_all(self, tool_registry):
        """Test listing all tools."""
        tools = tool_registry.list_tools(category="all")

        assert len(tools) >= 38
        for tool in tools:
            assert "name" in tool
            assert "category" in tool
            assert "description" in tool

    @pytest.mark.unit
    def test_usar_list_tools_by_category(self, tool_registry):
        """Test listing tools filtered by category."""
        categories = [
            "command",
            "search",
            "rescue",
            "medical",
            "planning",
            "logistics",
            "technical",
        ]

        for category in categories:
            tools = tool_registry.list_tools(category=category)
            assert len(tools) >= 3, f"Category {category} should have at least 3 tools"

            for tool in tools:
                assert tool["category"] == category

    @pytest.mark.unit
    def test_usar_execute_tool_with_params(self, tool_registry):
        """Test executing a tool with parameters."""
        result = tool_registry.execute_tool(
            "safety_officer_monitor", {"monitoring_mode": "real_time"}
        )

        data = json.loads(result)
        assert data["status"] == "success"
        assert data["data"]["monitoring_mode"] == "real_time"

    @pytest.mark.unit
    def test_usar_execute_medical_tool(self, tool_registry):
        """Test executing a medical tool."""
        result = tool_registry.execute_tool(
            "patient_care_tracker",
            {"patient_id": "PAT-TEST", "triage_priority": "immediate"},
        )

        data = json.loads(result)
        assert data["status"] == "success"
        patient = data["data"]["patient_identification"]
        assert patient["patient_id"] == "PAT-TEST"
        assert patient["triage_tag"] == "immediate"
        assert patient["care_level"] == "critical"


class TestToolInvocation:
    """Test direct tool invocation."""

    @pytest.mark.unit
    def test_task_force_leader_dashboard(self):
        """Test Task Force Leader dashboard tool."""
        from fema_usar_mcp.tools.command import task_force_leader_dashboard

        result = task_force_leader_dashboard(task_force_id="TEST-TF1")
        data = json.loads(result)

        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["task_force_id"] == "TEST-TF1"

    @pytest.mark.unit
    def test_safety_officer_monitor(self):
        """Test Safety Officer monitor tool."""
        from fema_usar_mcp.tools.command import safety_officer_monitor

        result = safety_officer_monitor(monitoring_mode="real_time")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["monitoring_mode"] == "real_time"

    @pytest.mark.unit
    def test_victim_location_tracker(self):
        """Test victim location tracker tool."""
        from fema_usar_mcp.tools.search import victim_location_tracker

        result = victim_location_tracker(search_area_id="TEST-AREA")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["search_area_id"] == "TEST-AREA"

    @pytest.mark.unit
    def test_rescue_squad_operations(self):
        """Test rescue squad operations tool."""
        from fema_usar_mcp.tools.rescue import rescue_squad_operations

        result = rescue_squad_operations(
            squad_id="SQUAD-TEST", operation_type="extraction"
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert "data" in data

    @pytest.mark.unit
    def test_patient_care_tracker(self):
        """Test patient care tracker tool."""
        from fema_usar_mcp.tools.medical import patient_care_tracker

        result = patient_care_tracker(patient_id="PAT-TEST")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["patient_identification"]["patient_id"] == "PAT-TEST"


class TestSystemTools:
    """Test system monitoring tools via tool registry."""

    @pytest.mark.unit
    def test_get_system_performance(self, tool_registry):
        """Test system performance tool via registry."""
        result = tool_registry.execute_tool("get_system_performance")
        data = json.loads(result)

        assert data["status"] == "success"
        assert "cache" in data["performance_data"]
        assert "metrics" in data["performance_data"]

    @pytest.mark.unit
    def test_clear_system_cache(self, tool_registry):
        """Test cache clearing tool via registry."""
        result = tool_registry.execute_tool("clear_system_cache")
        data = json.loads(result)

        assert data["status"] == "success"
        assert isinstance(data["cleared_entries"], int)
        assert data["pattern"] == "all"

    @pytest.mark.unit
    def test_get_usar_system_status(self, tool_registry):
        """Test USAR system status tool via registry."""
        result = tool_registry.execute_tool("get_usar_system_status")

        assert "Federal USAR MCP System Status" in result
        assert "Capabilities" in result

    @pytest.mark.unit
    def test_calculate_task_force_readiness(self, tool_registry):
        """Test task force readiness calculation via registry."""
        result = tool_registry.execute_tool(
            "calculate_task_force_readiness",
            {
                "task_force_id": "TEST-TF1",
                "personnel_count": 70,
                "equipment_ready": 16400,
                "training_compliance": 100.0,
            },
        )

        assert "Task Force Deployment Readiness" in result
        assert "TEST-TF1" in result


class TestLatentLoadingPerformance:
    """Test latent loading performance characteristics."""

    @pytest.mark.unit
    def test_registry_starts_empty(self):
        """Test that registry starts with no loaded functions."""
        registry = ToolRegistry()
        stats = registry.get_stats()

        assert stats["tools_loaded"] == 0
        assert stats["schemas_cached"] == 0

    @pytest.mark.unit
    def test_tools_load_on_demand(self, tool_registry):
        """Test that tools are loaded only when needed."""
        from fema_usar_mcp.tool_metadata import get_all_tool_metadata

        registry = ToolRegistry()
        registry.register_all_metadata(get_all_tool_metadata())
        assert registry.get_stats()["tools_loaded"] == 0

        registry.load_tool_function("task_force_leader_dashboard")
        assert registry.get_stats()["tools_loaded"] == 1

        # Loading the same tool again is served from the cache
        registry.load_tool_function("task_force_leader_dashboard")
        assert registry.get_stats()["tools_loaded"] == 1

        registry.load_tool_function("safety_officer_monitor")
        assert registry.get_stats()["tools_loaded"] == 2

    @pytest.mark.unit
    def test_schema_caching_improves_performance(self, tool_registry):
        """Test that schema caching reduces load operations."""
        # Clear any existing cache
        tool_registry.clear_cache()

        # First access - cache miss
        tool_registry.load_tool_schema("task_force_leader_dashboard")
        stats_after_first = tool_registry.get_stats()

        # Second access - should be cache hit
        tool_registry.load_tool_schema("task_force_leader_dashboard")
        stats_after_second = tool_registry.get_stats()

        assert stats_after_second["cache_hits"] > stats_after_first["cache_hits"]


class TestEveryRegisteredTool:
    """Every tool in the registry runs with its defaults and returns success."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "tool_name",
        [
            pytest.param(
                name,
                marks=pytest.mark.xfail(reason=BROKEN_MEDICAL_TOOLS[name], strict=True),
            )
            if name in BROKEN_MEDICAL_TOOLS
            else name
            for name in _all_registered_tool_names()
            if name not in NON_DEFAULT_TOOLS
        ],
    )
    def test_tool_runs_with_defaults(self, tool_registry, tool_name):
        result = tool_registry.execute_tool(tool_name)
        if tool_name in MARKDOWN_TOOLS:
            assert result.lstrip().startswith("# ")
            return
        data = json.loads(result)
        assert data["status"] in ("success", "healthy"), data


class TestPerformanceMonitorLocking:
    """Regression test for PerformanceMonitor.get_all_stats deadlocking."""

    @pytest.mark.unit
    def test_get_all_stats_with_recorded_metrics_does_not_deadlock(self):
        from fema_usar_mcp.performance import PerformanceMonitor

        monitor = PerformanceMonitor()
        monitor.record_metric("tool_latency", 1.0)
        monitor.record_metric("tool_latency", 3.0)

        result = {}
        worker = threading.Thread(
            target=lambda: result.update(monitor.get_all_stats()), daemon=True
        )
        worker.start()
        worker.join(timeout=5)

        assert not worker.is_alive(), "get_all_stats() deadlocked"
        assert result["metrics"]["tool_latency"]["count"] == 2
        assert result["metrics"]["tool_latency"]["avg"] == 2.0
