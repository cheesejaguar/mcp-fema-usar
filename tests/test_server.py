import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure repository root is in Python path when running via `pytest`
sys.path.append(str(Path(__file__).resolve().parents[1]))

import server

client = TestClient(server.app)


def test_list_forms():
    response = client.get('/ics_forms')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(server.ICS_FORMS)
    # check that first item matches
    assert data[0]['id'] == server.ICS_FORMS[0].id


def test_get_form():
    form = server.ICS_FORMS[0]
    response = client.get(f'/ics_forms/{form.id}')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == form.id
    assert data['name'] == form.name


def test_get_form_not_found():
    response = client.get('/ics_forms/unknown')
    assert response.status_code == 404


def test_get_form_content():
    form = server.ICS_FORMS[0]
    # Create a dummy file for testing
    form_path = Path(__file__).parent.parent / "resources" / "forms"
    form_path.mkdir(exist_ok=True)
    (form_path / form.filename).touch()

    response = client.get(f'/ics_forms/{form.id}/content')
    assert response.status_code == 200
    # Check if the file is returned
    assert response.headers['content-disposition'] == f'attachment; filename={form.filename}'


def test_get_form_content_not_found():
    response = client.get('/ics_forms/unknown/content')
    assert response.status_code == 404


def test_list_datasets():
    response = client.get('/datasets')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(server.OPEN_DATASETS)
    assert data[0]['id'] == server.OPEN_DATASETS[0].id


def test_get_dataset():
    dataset = server.OPEN_DATASETS[0]
    response = client.get(f'/datasets/{dataset.id}')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == dataset.id
    assert data['name'] == dataset.name


def test_get_dataset_not_found():
    response = client.get('/datasets/unknown')
    assert response.status_code == 404


def test_list_documents():
    response = client.get('/documents')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(server.DOCUMENTS)
    if len(data) > 0:
        assert data[0]['id'] == server.DOCUMENTS[0].id


def test_get_document():
    if not server.DOCUMENTS:
        return
    doc = server.DOCUMENTS[0]
    response = client.get(f'/documents/{doc.id}')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == doc.id
    assert data['name'] == doc.name


def test_get_document_not_found():
    response = client.get('/documents/unknown')
    assert response.status_code == 404


def test_get_document_content():
    if not server.DOCUMENTS:
        return
    doc = server.DOCUMENTS[0]
    # Create a dummy file for testing
    doc_path = Path(__file__).parent.parent / "resources" / "documents"
    doc_path.mkdir(exist_ok=True)
    (doc_path / doc.filename).touch()

    response = client.get(f'/documents/{doc.id}/content')
    assert response.status_code == 200
    # Check if the file is returned
    assert response.headers['content-disposition'] == f'attachment; filename={doc.filename}'


def test_get_document_content_not_found():
    response = client.get('/documents/unknown/content')
    assert response.status_code == 404
