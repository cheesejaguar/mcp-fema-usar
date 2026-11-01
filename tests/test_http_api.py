"""Tests for HTTP API functionality."""

import pytest
from fastapi.testclient import TestClient

from fema_usar_mcp.core import get_system_status, get_usar_capabilities


class TestHealthAndStatus:
    """Tests for health and status endpoints."""

    @pytest.mark.unit
    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["system"] == "Federal USAR MCP Server"
        assert data["status"] == "operational"
        assert data["capabilities"] == get_system_status()["capabilities"]

    @pytest.mark.unit
    def test_status_endpoint(self, test_client: TestClient):
        """Test status endpoint."""
        response = test_client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert data["system"] == "Federal USAR MCP Server"
        assert data["tools_available"] == 35
        assert data["task_forces_supported"] == 28

    @pytest.mark.unit
    def test_capabilities_endpoint(self, test_client: TestClient):
        """Test capabilities endpoint."""
        response = test_client.get("/capabilities")
        assert response.status_code == 200

        data = response.json()
        assert len(data["functional_groups"]) == 7
        assert "Command" in data["functional_groups"]
        assert data["tools"] == get_usar_capabilities()["tools"]
        assert "FEMA IRIS" in data["integrations"]
        assert data["personnel_positions"] == 70
        assert data["equipment_items"] == 16400


class TestUSAREndpoints:
    """Tests for USAR-specific endpoints."""

    @pytest.mark.unit
    def test_task_force_status(self, test_client: TestClient):
        """Test task force status endpoint."""
        request_data = {
            "task_force_id": "CA-TF1",
            "include_personnel": True,
            "include_equipment": True,
        }

        response = test_client.post("/usar/status", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["task_force_id"] == "CA-TF1"
        assert data["operational_status"] == "Ready"
        assert data["personnel_count"] == 70
        assert data["equipment_ready"] == 16400

    @pytest.mark.unit
    def test_deployment_initiation(self, test_client: TestClient):
        """Test deployment initiation endpoint."""
        response = test_client.post(
            "/usar/deploy",
            params={
                "task_force_id": "CA-TF1",
                "deployment_location": "Los Angeles, CA",
                "mission_type": "search_and_rescue",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["deployment_id"] == "DEPLOY-CA-TF1-001"
        assert data["task_force_id"] == "CA-TF1"
        assert data["location"] == "Los Angeles, CA"
        assert data["mission_type"] == "search_and_rescue"
        assert data["status"] == "deployment_initiated"
        assert data["estimated_departure"] == "6 hours"

    @pytest.mark.unit
    def test_deployment_requires_location(self, test_client: TestClient):
        """Deployment without a location is rejected by validation."""
        response = test_client.post("/usar/deploy", params={"task_force_id": "CA-TF1"})
        assert response.status_code == 422


class TestICSFormsAPI:
    """Tests for ICS Forms API endpoints."""

    @pytest.mark.unit
    def test_list_ics_forms(self, test_client: TestClient):
        """Test listing ICS forms."""
        response = test_client.get("/ics_forms")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check form structure
        form = data[0]
        assert "id" in form
        assert "name" in form
        assert "description" in form
        assert "filename" in form

    @pytest.mark.unit
    def test_get_specific_ics_form(self, test_client: TestClient):
        """Test getting specific ICS form."""
        response = test_client.get("/ics_forms/201")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "201"
        assert data["name"] == "Incident Briefing"
        assert data["filename"] == "ics_201.pdf"


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.unit
    def test_invalid_task_force_status_request(self, test_client: TestClient):
        """Test invalid task force status request."""
        # Missing required field
        invalid_request = {"include_personnel": True}

        response = test_client.post("/usar/status", json=invalid_request)
        assert response.status_code == 422  # Validation error

    @pytest.mark.unit
    def test_malformed_json_request(self, test_client: TestClient):
        """Test handling of malformed JSON requests."""
        response = test_client.post(
            "/usar/status",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestCORSAndSecurity:
    """Tests for CORS and security features."""

    @pytest.mark.unit
    def test_cors_headers_present(self, test_client: TestClient):
        """Preflight from an allowed origin gets CORS headers back."""
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers["access-control-allow-origin"] == "http://localhost:3000"
        )
        assert response.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.unit
    def test_cors_rejects_unknown_origin(self, test_client: TestClient):
        """Preflight from an origin outside CORS_ORIGINS is refused."""
        response = test_client.options(
            "/health",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers


class TestPerformance:
    """Tests for API performance."""

    @pytest.mark.unit
    @pytest.mark.slow
    def test_concurrent_requests(self, test_client: TestClient):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def make_request():
            return test_client.get("/health")

        # Execute multiple requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
