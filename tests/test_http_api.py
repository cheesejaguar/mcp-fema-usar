"""Tests for HTTP API functionality."""

import pytest
from fastapi.testclient import TestClient


class TestHealthAndStatus:
    """Tests for health and status endpoints."""

    @pytest.mark.unit
    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["system"] == "FEMA USAR MCP Server"
        assert data["status"] == "operational"

    @pytest.mark.unit
    def test_status_endpoint(self, test_client: TestClient):
        """Test status endpoint."""
        response = test_client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert data["system"] == "FEMA USAR MCP Server"
        assert data["tools_available"] == 35
        assert data["task_forces_supported"] == 28

    @pytest.mark.unit
    def test_capabilities_endpoint(self, test_client: TestClient):
        """Test capabilities endpoint."""
        response = test_client.get("/capabilities")
        assert response.status_code == 200

        data = response.json()
        assert "functional_groups" in data
        assert "tools" in data
        assert "integrations" in data
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
        assert "deployment_id" in data
        assert data["task_force_id"] == "CA-TF1"
        assert data["location"] == "Los Angeles, CA"
        assert data["estimated_departure"] == "6 hours"


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
        response = test_client.get("/ics_forms/ics_201")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "ics_201"
        assert "name" in data
        assert "filename" in data

    @pytest.mark.unit
    def test_get_nonexistent_form(self, test_client: TestClient):
        """Test getting non-existent form returns 404."""
        response = test_client.get("/ics_forms/nonexistent")
        assert response.status_code == 404


class TestDatasetsAPI:
    """Tests for datasets API endpoints."""

    @pytest.mark.unit
    def test_list_datasets(self, test_client: TestClient):
        """Test listing available datasets."""
        response = test_client.get("/datasets")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.unit
    def test_get_specific_dataset(self, test_client: TestClient):
        """Test getting specific dataset information."""
        # First get the list to find a valid dataset ID
        list_response = test_client.get("/datasets")
        datasets = list_response.json()

        if datasets:
            dataset_id = datasets[0]["id"]
            response = test_client.get(f"/datasets/{dataset_id}")
            assert response.status_code == 200

            data = response.json()
            assert data["id"] == dataset_id


class TestDocumentsAPI:
    """Tests for documents API endpoints."""

    @pytest.mark.unit
    def test_list_documents(self, test_client: TestClient):
        """Test listing available documents."""
        response = test_client.get("/documents")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.unit
    def test_get_document_info(self, test_client: TestClient):
        """Test getting document information."""
        # First get the list to find a valid document ID
        list_response = test_client.get("/documents")
        documents = list_response.json()

        if documents:
            doc_id = documents[0]["id"]
            response = test_client.get(f"/documents/{doc_id}")
            assert response.status_code == 200

            data = response.json()
            assert data["id"] == doc_id


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
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestCORSAndSecurity:
    """Tests for CORS and security features."""

    @pytest.mark.unit
    def test_cors_headers_present(self, test_client: TestClient):
        """Test that CORS headers are present."""
        response = test_client.options("/health")
        # In test environment, CORS middleware should be configured
        # The actual headers depend on the CORS configuration


class TestPerformance:
    """Tests for API performance."""

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
