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
