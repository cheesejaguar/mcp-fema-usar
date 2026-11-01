import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure repository root is in Python path when running via `pytest`
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import main as app_main
from app.main import DOCUMENTS, ICS_FORMS, OPEN_DATASETS, ICSForm, app

pytestmark = pytest.mark.unit

client = TestClient(app)

RESOURCES_DIR = Path(__file__).resolve().parents[1] / "resources"


def test_list_forms():
    response = client.get("/ics_forms")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(ICS_FORMS)
    # check that first item matches
    assert data[0]["id"] == ICS_FORMS[0].id


def test_get_form():
    form = ICS_FORMS[0]
    response = client.get(f"/ics_forms/{form.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == form.id
    assert data["name"] == form.name


def test_get_form_not_found():
    response = client.get("/ics_forms/unknown")
    assert response.status_code == 404


def test_get_form_content():
    form = ICS_FORMS[0]
    form_file = RESOURCES_DIR / "forms" / form.filename

    response = client.get(f"/ics_forms/{form.id}/content")
    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == f"attachment; filename={form.filename}"
    )
    assert response.content == form_file.read_bytes()


def test_get_form_content_not_found():
    response = client.get("/ics_forms/unknown/content")
    assert response.status_code == 404


def test_get_form_content_missing_file(monkeypatch):
    """A catalogued form whose file is absent on disk returns a 404."""
    missing = ICSForm(
        id="missing-form",
        name="Missing",
        description="Catalogued but not on disk",
        filename="does_not_exist.pdf",
    )
    monkeypatch.setattr(app_main, "ICS_FORMS", [*ICS_FORMS, missing])

    response = client.get("/ics_forms/missing-form/content")
    assert response.status_code == 404
    assert response.json()["detail"] == "Form file not found"


def test_list_datasets():
    response = client.get("/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(OPEN_DATASETS)
    assert data[0]["id"] == OPEN_DATASETS[0].id


def test_get_dataset():
    dataset = OPEN_DATASETS[0]
    response = client.get(f"/datasets/{dataset.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dataset.id
    assert data["name"] == dataset.name


def test_get_dataset_not_found():
    response = client.get("/datasets/unknown")
    assert response.status_code == 404


def test_documents_catalog_loaded():
    """resources/documents.json ships with the repo, so DOCUMENTS is non-empty."""
    assert len(DOCUMENTS) > 0


def test_list_documents():
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(DOCUMENTS)
    assert data[0]["id"] == DOCUMENTS[0].id


def test_get_document():
    doc = DOCUMENTS[0]
    response = client.get(f"/documents/{doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc.id
    assert data["name"] == doc.name


def test_get_document_not_found():
    response = client.get("/documents/unknown")
    assert response.status_code == 404


def test_get_document_content():
    doc = DOCUMENTS[0]
    doc_file = RESOURCES_DIR / "documents" / doc.filename

    response = client.get(f"/documents/{doc.id}/content")
    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == f"attachment; filename={doc.filename}"
    )
    assert response.content == doc_file.read_bytes()


def test_get_document_content_not_found():
    response = client.get("/documents/unknown/content")
    assert response.status_code == 404
