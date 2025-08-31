"""Test configuration for FEMA USAR MCP Server."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from fema_usar_mcp.core import (
    EquipmentItem,
    OperationalStatus,
    PersonnelPosition,
    USARTaskForceConfig,
)


@pytest.fixture
def test_client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_task_force_config():
    """Sample USAR task force configuration for testing."""
    return USARTaskForceConfig(
        task_force_id="TEST-TF1",
        task_force_name="Test Task Force 1",
        home_location="Test City, Test State",
        operational_status=OperationalStatus.READY,
        personnel_count=70,
        equipment_ready_count=16400,
        certifications_current=True,
        training_compliance=95.0,
    )


@pytest.fixture
def sample_personnel_position():
    """Sample personnel position for testing."""
    return PersonnelPosition(
        position_id="TFL-001",
        position_name="Task Force Leader",
        functional_group="COMMAND",
        required_qualifications=["NIMS_ICS_300", "USAR_Task_Force_Leader"],
        is_critical=True,
        minimum_experience_years=5,
    )


@pytest.fixture
def sample_equipment_item():
    """Sample equipment item for testing."""
    return EquipmentItem(
        equipment_id="EQ-001",
        equipment_name="Delsar Seismic Listening Device",
        category="search",
        serial_number="DSL-2024-001",
        status="operational",
        deployment_ready=True,
        last_inspection=datetime(2024, 8, 1, 12, 0, 0),
        next_maintenance=datetime(2024, 12, 1, 12, 0, 0),
    )


@pytest.fixture
def mock_advanced_library(monkeypatch):
    """Mock advanced library dependencies for testing."""
    import sys
    from unittest.mock import MagicMock

    # Mock numpy if not available
    if "numpy" not in sys.modules:
        sys.modules["numpy"] = MagicMock()

    # Mock pandas if not available
    if "pandas" not in sys.modules:
        sys.modules["pandas"] = MagicMock()

    return True
