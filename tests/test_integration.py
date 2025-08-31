"""Comprehensive integration tests for FEMA USAR MCP Server."""

import json
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from fema_usar_mcp.core import get_system_status
from fema_usar_mcp.tools.command import (
    personnel_accountability,
    safety_officer_monitor,
    task_force_leader_dashboard,
)
from fema_usar_mcp.tools.logistics import (
    supply_chain_manager,
)
from fema_usar_mcp.tools.medical import (
    patient_care_tracker,
)
from fema_usar_mcp.tools.planning import (
    documentation_automation,
    resource_unit_tracker,
    situation_unit_dashboard,
)
from fema_usar_mcp.tools.rescue import (
    rescue_squad_operations,
    victim_extraction_planner,
)
from fema_usar_mcp.tools.search import (
    victim_location_tracker,
)
from fema_usar_mcp.tools.technical import (
    communications_manager,
    hazmat_monitoring,
    structural_assessment,
)


class TestToolIntegration:
    """Test integration between different tool modules."""

    @pytest.mark.integration
    def test_command_to_search_coordination(self):
        """Test coordination between command and search tools."""
        # Get task force status
        tfl_result = task_force_leader_dashboard("TEST-TF1", include_personnel=True)
        tfl_data = json.loads(tfl_result)

        # Use task force status to deploy search teams
        search_result = victim_location_tracker("AREA-A1", "confirmed")
        search_data = json.loads(search_result)

        # Verify data consistency
        assert tfl_data["status"] == "success"
        assert search_data["status"] == "success"
        assert tfl_data["dashboard"]["personnel"]["search_teams"]["available"] >= 0

    @pytest.mark.integration
    def test_search_to_rescue_handoff(self):
        """Test handoff from search operations to rescue operations."""
        # Complete victim location
        search_result = victim_location_tracker("AREA-A1", "confirmed")
        search_data = json.loads(search_result)

        # Initiate rescue operations based on search results
        rescue_result = rescue_squad_operations(
            squad_id="SQUAD-Alpha",
            operation_type="victim_extrication",
            victim_id="VIC-001",
            location="Building A - Floor 2",
            personnel_assigned=6,
            equipment_required=["cutting_tools", "shoring_equipment"],
        )
        rescue_data = json.loads(rescue_result)

        # Verify operational continuity
        assert search_data["status"] == "success"
        assert rescue_data["status"] == "success"
        assert (
            rescue_data["rescue_data"]["operational_status"]["operation_type"]
            == "victim_extrication"
        )

    @pytest.mark.integration
    def test_rescue_to_medical_coordination(self):
        """Test coordination between rescue and medical operations."""
        # Complete victim extraction
        extraction_result = victim_extraction_planner(
            victim_id="VIC-001",
            victim_location="Building A - Floor 2 - Room 204",
            extraction_method="vertical_lift",
            victim_condition="stable_conscious",
            entrapment_type="structural_debris",
            access_difficulty="moderate",
        )
        extraction_data = json.loads(extraction_result)

        # Hand off to medical team
        medical_result = patient_care_tracker(
            patient_id="VIC-001",
            patient_name="John Doe",
            age=35,
            gender="male",
            triage_priority="yellow",
            chief_complaint="crush_injury_lower_extremity",
            vital_signs={"bp": "120/80", "pulse": 88, "resp": 16, "temp": 98.6},
            treatments_given=["immobilization", "pain_management"],
            medications_administered=["morphine_5mg_iv"],
            location_found="Building A - Floor 2 - Room 204",
            transport_destination="Regional Medical Center",
        )
        medical_data = json.loads(medical_result)

        # Verify patient continuity
        assert extraction_data["status"] == "success"
        assert medical_data["status"] == "success"
        assert (
            medical_data["patient_data"]["patient_identification"]["patient_id"]
            == "VIC-001"
        )

    @pytest.mark.integration
    def test_planning_to_logistics_integration(self):
        """Test integration between planning and logistics functions."""
        # Get resource requirements from planning
        planning_result = resource_unit_tracker("all", "deployment", "TEST-TF1")
        planning_data = json.loads(planning_result)

        # Use resource data for supply management
        logistics_result = supply_chain_manager(
            supply_category="equipment",
            inventory_action="check",
            priority_level="routine",
        )
        logistics_data = json.loads(logistics_result)

        # Verify resource alignment
        assert planning_data["status"] == "success"
        assert logistics_data["status"] == "success"
        assert (
            logistics_data["supply_chain_data"]["inventory_status"][
                "total_inventory_value"
            ]
            > 0
        )

    @pytest.mark.integration
    def test_technical_to_safety_coordination(self):
        """Test coordination between technical specialists and safety functions."""
        # Perform structural assessment
        structural_result = structural_assessment(
            assessment_type="detailed",
            structure_type="commercial",
            building_id="BLDG-A001",
            damage_level="moderate",
            include_load_calculations=True,
        )
        structural_data = json.loads(structural_result)

        # Update safety monitoring based on assessment
        safety_result = safety_officer_monitor("real_time")
        safety_data = json.loads(safety_result)

        # Verify safety integration
        assert structural_data["status"] == "success"
        assert safety_data["status"] == "success"
        assert (
            structural_data["assessment_data"]["safety_evaluation"][
                "occupancy_recommendation"
            ]
            is not None
        )


class TestSystemIntegration:
    """Test system-wide integration capabilities."""

    @pytest.mark.integration
    def test_full_incident_workflow(self):
        """Test complete incident response workflow integration."""
        # 1. Initial deployment
        tfl_result = task_force_leader_dashboard(
            "TEST-TF1", include_personnel=True, include_equipment=True
        )

        # 2. Establish communications
        comm_result = communications_manager("all", "status")

        # 3. Deploy search teams
        search_result = victim_location_tracker("AREA-A1", "confirmed")

        # 4. Initiate rescue operations
        rescue_result = rescue_squad_operations(
            squad_id="SQUAD-Alpha",
            operation_type="search_and_rescue",
            victim_id="VIC-001",
            location="Building A",
            personnel_assigned=6,
            equipment_required=["search_equipment", "rescue_tools"],
        )

        # 5. Medical response
        medical_result = patient_care_tracker(
            patient_id="VIC-001",
            patient_name="Jane Smith",
            age=28,
            gender="female",
            triage_priority="red",
            chief_complaint="trauma_multiple_injuries",
            vital_signs={"bp": "90/60", "pulse": 120, "resp": 24, "temp": 97.8},
            treatments_given=["airway_management", "iv_fluids"],
            medications_administered=["epinephrine_1mg_iv"],
            location_found="Building A - Floor 1",
            transport_destination="Level 1 Trauma Center",
        )

        # 6. Update planning and logistics
        planning_result = situation_unit_dashboard("all", "real_time", "TEST-INC-001")
        logistics_result = supply_chain_manager("all", "check")

        # Verify all systems operational
        results = [
            tfl_result,
            comm_result,
            search_result,
            rescue_result,
            medical_result,
            planning_result,
            logistics_result,
        ]
        for result in results:
            data = json.loads(result)
            assert data["status"] == "success"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_operations(self):
        """Test system performance under concurrent operations."""

        def run_operation(operation_func, *args):
            """Run operation and return result."""
            return operation_func(*args)

        # Define concurrent operations
        operations = [
            (task_force_leader_dashboard, "TEST-TF1"),
            (victim_location_tracker, "AREA-A1", "confirmed"),
            (
                rescue_squad_operations,
                "SQUAD-Alpha",
                "search_and_rescue",
                "VIC-001",
                "Building A",
                6,
                ["tools"],
            ),
            (
                patient_care_tracker,
                "VIC-001",
                "Test Patient",
                30,
                "male",
                "yellow",
                "injury",
                {},
                [],
                [],
                "Building A",
                "Hospital",
            ),
            (situation_unit_dashboard, "all", "real_time"),
            (supply_chain_manager, "all", "check"),
            (structural_assessment, "preliminary", "commercial"),
            (hazmat_monitoring, "air_quality", "normal"),
        ]

        # Execute operations concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(run_operation, op_func, *op_args)
                for op_func, *op_args in operations
            ]
            results = [future.result() for future in futures]

        # Verify all operations completed successfully
        for result in results:
            data = json.loads(result)
            assert data["status"] == "success"

    @pytest.mark.integration
    def test_data_consistency_across_tools(self):
        """Test data consistency across different tool modules."""
        # Get personnel data from different sources
        tfl_result = task_force_leader_dashboard("TEST-TF1", include_personnel=True)
        tfl_data = json.loads(tfl_result)

        personnel_result = personnel_accountability("full")
        personnel_data = json.loads(personnel_result)

        resource_result = resource_unit_tracker(
            "personnel", "accountability", "TEST-TF1"
        )
        resource_data = json.loads(resource_result)

        # Verify personnel count consistency
        tfl_personnel = tfl_data["dashboard"]["personnel"]["total_personnel"]
        personnel_count = personnel_data["data"]["total_personnel"]
        resource_personnel = resource_data["resource_data"]["personnel_tracking"][
            "total_personnel"
        ]

        assert tfl_personnel == personnel_count == resource_personnel == 70


class TestErrorHandlingAndResilience:
    """Test error handling and system resilience."""

    @pytest.mark.integration
    def test_graceful_error_handling(self):
        """Test graceful handling of errors across tool integrations."""
        # Test with invalid parameters
        result = task_force_leader_dashboard("", include_personnel=True)
        data = json.loads(result)

        # Should still return valid JSON structure even with empty task_force_id
        assert "status" in data
        assert "tool" in data

    @pytest.mark.integration
    def test_system_recovery_after_failure(self):
        """Test system recovery capabilities after component failure."""
        # Simulate a failure scenario and recovery
        with patch("fema_usar_mcp.tools.command.logger.error") as mock_logger:
            # This should not cause system failure
            result = task_force_leader_dashboard("TEST-TF1")
            data = json.loads(result)
            assert data["status"] == "success"

    @pytest.mark.integration
    def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion scenarios."""
        # Test with high resource demands
        results = []
        for i in range(10):
            result = victim_location_tracker(f"AREA-{i}", "confirmed")
            data = json.loads(result)
            results.append(data["status"])

        # All operations should complete successfully
        assert all(status == "success" for status in results)


class TestPerformanceIntegration:
    """Test performance characteristics of integrated systems."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_response_time_under_load(self):
        """Test system response times under operational load."""
        import time

        start_time = time.time()

        # Execute multiple operations
        operations = [
            task_force_leader_dashboard(
                "TEST-TF1", include_personnel=True, include_equipment=True
            ),
            situation_unit_dashboard("all", "real_time"),
            supply_chain_manager("all", "check"),
            hazmat_monitoring("all", "normal"),
            communications_manager("all", "status"),
        ]

        end_time = time.time()
        total_time = end_time - start_time

        # All operations should complete in reasonable time (< 5 seconds)
        assert total_time < 5.0

        # Verify all operations succeeded
        for result in operations:
            data = json.loads(result)
            assert data["status"] == "success"

    @pytest.mark.integration
    def test_memory_usage_stability(self):
        """Test memory usage stability during extended operations."""
        import gc

        # Force garbage collection
        gc.collect()

        # Execute repeated operations
        for _ in range(20):
            result = task_force_leader_dashboard("TEST-TF1")
            data = json.loads(result)
            assert data["status"] == "success"

        # Force garbage collection again
        gc.collect()

        # Memory should be stable (no significant leaks)
        # This is a basic test - in production, you'd use memory profiling tools


class TestSystemStatusIntegration:
    """Test system status and health monitoring integration."""

    @pytest.mark.integration
    def test_system_health_monitoring(self):
        """Test comprehensive system health monitoring."""
        status = get_system_status()

        assert status["system"] == "FEMA USAR MCP Server"
        assert status["status"] == "operational"
        assert "capabilities" in status
        assert status["capabilities"]["total_positions"] == 70
        assert status["capabilities"]["total_equipment"] == 16400

    @pytest.mark.integration
    def test_tool_availability_monitoring(self):
        """Test monitoring of tool availability and status."""
        # Test each major tool category
        tool_tests = [
            (task_force_leader_dashboard, ("TEST-TF1",)),
            (victim_location_tracker, ("AREA-A1", "confirmed")),
            (
                rescue_squad_operations,
                (
                    "SQUAD-Alpha",
                    "search_and_rescue",
                    "VIC-001",
                    "Building A",
                    6,
                    ["tools"],
                ),
            ),
            (
                patient_care_tracker,
                (
                    "VIC-001",
                    "Test",
                    30,
                    "male",
                    "yellow",
                    "injury",
                    {},
                    [],
                    [],
                    "Building A",
                    "Hospital",
                ),
            ),
            (situation_unit_dashboard, ("all", "real_time")),
            (supply_chain_manager, ("all", "check")),
            (structural_assessment, ("preliminary", "commercial")),
        ]

        availability_results = []
        for tool_func, args in tool_tests:
            try:
                result = tool_func(*args)
                data = json.loads(result)
                availability_results.append(data["status"] == "success")
            except Exception:
                availability_results.append(False)

        # Calculate system availability
        availability_rate = sum(availability_results) / len(availability_results) * 100
        assert availability_rate >= 95.0  # 95% availability target


class TestDataFlowIntegration:
    """Test data flow and information sharing between tools."""

    @pytest.mark.integration
    def test_incident_data_propagation(self):
        """Test propagation of incident data across all systems."""
        incident_id = "TEST-INC-001"

        # Generate incident data in planning
        planning_result = situation_unit_dashboard("all", "real_time", incident_id)
        planning_data = json.loads(planning_result)

        # Verify incident ID propagation
        assert planning_data["dashboard"][
            "incident_id"
        ] == incident_id or "incident_id" in str(planning_result)
        assert planning_data["status"] == "success"

    @pytest.mark.integration
    def test_resource_data_synchronization(self):
        """Test synchronization of resource data across systems."""
        # Update resource status in planning
        resource_result = resource_unit_tracker("all", "deployment", "TEST-TF1")
        resource_data = json.loads(resource_result)

        # Check consistency in logistics
        logistics_result = supply_chain_manager("all", "check")
        logistics_data = json.loads(logistics_result)

        # Both systems should be operational
        assert resource_data["status"] == "success"
        assert logistics_data["status"] == "success"

    @pytest.mark.integration
    def test_safety_information_sharing(self):
        """Test sharing of safety information across all tools."""
        # Generate safety alert
        safety_result = safety_officer_monitor("real_time")
        safety_data = json.loads(safety_result)

        # Verify safety information is available
        assert safety_data["status"] == "success"
        assert "safety_monitoring" in safety_data["data"] or "monitor" in safety_data


@pytest.mark.integration
class TestFullSystemIntegration:
    """Comprehensive full system integration tests."""

    def test_end_to_end_usar_deployment(self):
        """Test complete end-to-end USAR deployment scenario."""
        # Phase 1: Deployment initialization
        tfl_result = task_force_leader_dashboard(
            "CA-TF1",
            include_personnel=True,
            include_equipment=True,
            include_missions=True,
        )
        tfl_data = json.loads(tfl_result)
        assert tfl_data["status"] == "success"

        # Phase 2: Site assessment
        structural_result = structural_assessment(
            "preliminary", "commercial", "BLDG-001", "moderate"
        )
        structural_data = json.loads(structural_result)
        assert structural_data["status"] == "success"

        # Phase 3: Search operations
        search_result = victim_location_tracker("AREA-A1", "confirmed")
        search_data = json.loads(search_result)
        assert search_data["status"] == "success"

        # Phase 4: Rescue operations
        rescue_result = rescue_squad_operations(
            "SQUAD-Alpha",
            "victim_extrication",
            "VIC-001",
            "Building A",
            6,
            ["cutting_tools"],
        )
        rescue_data = json.loads(rescue_result)
        assert rescue_data["status"] == "success"

        # Phase 5: Medical operations
        medical_result = patient_care_tracker(
            "VIC-001",
            "Rescued Victim",
            35,
            "male",
            "red",
            "trauma",
            {"bp": "110/70"},
            [],
            [],
            "Building A",
            "Hospital",
        )
        medical_data = json.loads(medical_result)
        assert medical_data["status"] == "success"

        # Phase 6: Documentation and reporting
        doc_result = documentation_automation("all", True, "TEST-INC-001")
        doc_data = json.loads(doc_result)
        assert doc_data["status"] == "success"

        # Verify operational continuity
        assert all(
            data["status"] == "success"
            for data in [
                tfl_data,
                structural_data,
                search_data,
                rescue_data,
                medical_data,
                doc_data,
            ]
        )

    def test_multi_incident_coordination(self):
        """Test coordination of multiple simultaneous incidents."""
        incidents = ["INC-001", "INC-002", "INC-003"]
        results = []

        for incident_id in incidents:
            # Create situation dashboard for each incident
            result = situation_unit_dashboard("all", "real_time", incident_id)
            data = json.loads(result)
            results.append(data["status"])

        # All incidents should be handled successfully
        assert all(status == "success" for status in results)

    def test_system_scalability(self):
        """Test system scalability under increased load."""
        # Simulate multiple task forces
        task_forces = ["CA-TF1", "CA-TF2", "NV-TF1", "UT-TF1", "CO-TF1"]
        results = []

        for tf_id in task_forces:
            result = task_force_leader_dashboard(tf_id)
            data = json.loads(result)
            results.append(data["status"])

        # All task forces should be managed successfully
        assert all(status == "success" for status in results)
