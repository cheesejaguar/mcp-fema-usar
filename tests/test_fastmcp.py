"""Tests for FastMCP server functionality."""

import json

import pytest
from fastmcp import Client

from fema_usar_mcp.core import get_system_status
from fema_usar_mcp.fastmcp_server import mcp
from fema_usar_mcp.tools.command import (
    personnel_accountability,
    safety_officer_monitor,
    task_force_leader_dashboard,
)


class TestFastMCPServerInitialization:
    """Tests for FastMCP server initialization."""

    @pytest.mark.unit
    def test_server_instance_created(self):
        """Test that FastMCP server instance is created correctly."""
        assert mcp is not None
        assert mcp.name == "fema-usar-mcp"

    @pytest.mark.unit
    async def test_tools_registered(self):
        """Test that the command tools are registered with the MCP server."""
        tools = await mcp.get_tools()
        for func in (
            task_force_leader_dashboard,
            safety_officer_monitor,
            personnel_accountability,
        ):
            assert func.__name__ in tools
            assert tools[func.__name__].fn is func

    @pytest.mark.unit
    async def test_system_status_tool_exists(self):
        """System status tool is registered and callable over the MCP protocol."""
        async with Client(mcp) as client:
            tool_names = {tool.name for tool in await client.list_tools()}
            assert "get_usar_system_status" in tool_names

            result = await client.call_tool("get_usar_system_status")
            text = result.content[0].text
            assert "Federal USAR MCP System Status" in text
            assert "Federal USAR MCP Server" in text


class TestCommandTools:
    """Tests for Command Group tools."""

    @pytest.mark.unit
    def test_task_force_leader_dashboard_basic(self):
        """Test basic task force leader dashboard functionality."""
        result = task_force_leader_dashboard("TEST-TF1")

        assert "Task Force Leader Dashboard" in result
        assert "TEST-TF1" in result

        # Parse JSON to verify structure
        result_data = json.loads(result)
        assert "dashboard" in result_data
        assert "status" in result_data
        assert result_data["status"] == "success"

    @pytest.mark.unit
    def test_safety_officer_monitor_real_time(self):
        """Test safety officer monitoring in real-time mode."""
        result = safety_officer_monitor("real_time")

        assert "Safety Officer Monitor" in result

        # Parse JSON to verify structure
        result_data = json.loads(result)
        assert "monitor" in result_data
        assert result_data["data"]["monitoring_mode"] == "real_time"

    @pytest.mark.unit
    def test_personnel_accountability_full(self):
        """Test personnel accountability with full information."""
        result = personnel_accountability("full")

        assert "Personnel Accountability" in result

        # Parse JSON to verify structure
        result_data = json.loads(result)
        assert "accountability" in result_data
        assert result_data["data"]["accountability_type"] == "full"
        assert result_data["data"]["total_personnel"] == 70


class TestSystemStatusTool:
    """Tests for system status functionality."""

    @pytest.mark.unit
    def test_get_system_status(self):
        """Test system status retrieval."""
        status = get_system_status()

        assert status["system"] == "Federal USAR MCP Server"
        assert status["version"] == "0.1.0"
        assert status["status"] == "operational"
        assert "capabilities" in status

    @pytest.mark.unit
    def test_capabilities_structure(self):
        """Test that capabilities have expected structure."""
        status = get_system_status()
        capabilities = status["capabilities"]

        assert "functional_groups" in capabilities
        assert "total_positions" in capabilities
        assert "total_equipment" in capabilities
        assert capabilities["total_positions"] == 70
        assert capabilities["total_equipment"] == 16400


class TestCoreBusinessLogic:
    """Tests for core business logic functions."""

    @pytest.mark.unit
    def test_deployment_readiness_calculation(self, sample_task_force_config):
        """Test deployment readiness calculation."""
        from fema_usar_mcp.core import calculate_deployment_readiness

        readiness = calculate_deployment_readiness(sample_task_force_config)

        assert readiness["deployment_capable"] is True
        assert readiness["personnel_readiness_percent"] == 100.0
        assert readiness["equipment_readiness_percent"] == 100.0
        assert readiness["training_readiness_percent"] == 95.0
        assert readiness["overall_readiness_percent"] == 98.3

    @pytest.mark.unit
    def test_safety_alert_processing(self):
        """Test safety alert processing functionality."""
        from fema_usar_mcp.core import AlertLevel, SafetyAlert, process_safety_alert

        alert = SafetyAlert(
            alert_id="TEST-ALERT-001",
            alert_level=AlertLevel.RED,
            alert_type="structural_hazard",
            description="Test structural hazard alert",
            personnel_affected=["PERS-001", "PERS-002"],
        )

        result = process_safety_alert(alert)

        assert result["alert_id"] == "TEST-ALERT-001"
        assert result["immediate_response_required"] is True
        assert result["personnel_count_affected"] == 2
        assert result["notification_level"] == "urgent"
        assert "Evacuate affected area immediately" in result["recommendations"]


class TestToolIntegration:
    """Tests for tool integration and error handling."""

    @pytest.mark.unit
    def test_tool_error_handling(self):
        """Test that tools handle errors gracefully."""
        # Test with invalid parameters that might cause errors
        result = task_force_leader_dashboard(
            task_force_id="",  # Empty string
            include_personnel=True,
            include_equipment=True,
        )

        # Should still return valid JSON even with empty task_force_id
        result_data = json.loads(result)
        assert result_data["status"] == "success"
        assert result_data["data"]["task_force_id"] == ""
        assert "personnel_status" in result_data["data"]
        assert "equipment_status" in result_data["data"]

    @pytest.mark.integration
    def test_multiple_tools_coordination(self):
        """Test that multiple tools can work together."""
        # Get personnel accountability
        personnel_result = personnel_accountability("status")
        personnel_data = json.loads(personnel_result)

        # Get safety monitoring
        safety_result = safety_officer_monitor("summary")
        safety_data = json.loads(safety_result)

        # Both should succeed
        assert personnel_data["status"] == "success"
        assert safety_data["status"] == "success"

        # Data should be consistent
        assert personnel_data["data"]["total_personnel"] == 70
        assert safety_data["data"]["personnel_tracked"] == 70


class TestPerformanceAndScalability:
    """Tests for performance and scalability."""

    @pytest.mark.unit
    @pytest.mark.slow
    def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        # Test with maximum personnel and equipment
        result = task_force_leader_dashboard(
            "LARGE-TF1",
            include_personnel=True,
            include_equipment=True,
            include_missions=True,
        )

        # Should complete in reasonable time and return valid data
        result_data = json.loads(result)
        assert result_data["status"] == "success"
        data = result_data["data"]
        assert data["summary"]["total_personnel"] == 70
        assert data["summary"]["equipment_total"] == 16400
        assert isinstance(data["mission_assignments"], list)
        assert "personnel_status" in data
        assert "equipment_status" in data

    @pytest.mark.unit
    def test_concurrent_tool_calls(self):
        """Test concurrent tool calls don't interfere."""
        import concurrent.futures

        def call_dashboard(tf_id):
            return task_force_leader_dashboard(tf_id)

        # Execute multiple calls concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(call_dashboard, f"TF-{i}") for i in range(1, 4)]

            results = [future.result() for future in futures]

        # All calls should succeed and each result belongs to its own request
        for i, result in enumerate(results, start=1):
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["data"]["task_force_id"] == f"TF-{i}"
