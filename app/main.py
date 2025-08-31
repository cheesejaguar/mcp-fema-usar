"""FastAPI HTTP interface for FEMA USAR MCP server."""

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from fema_usar_mcp.core import (
    get_system_status,
    get_usar_capabilities,
)


class ICSForm(BaseModel):
    id: str
    name: str
    description: str
    filename: str


class OpenDataset(BaseModel):
    id: str
    name: str
    description: str
    url: str


class Document(BaseModel):
    id: str
    name: str
    description: str
    filename: str


class USARStatusRequest(BaseModel):
    task_force_id: str
    request_type: str = "full_status"
    include_personnel: bool = True
    include_equipment: bool = True


class USARStatusResponse(BaseModel):
    task_force_id: str
    operational_status: str
    personnel_count: int
    equipment_ready: int
    mission_assignments: list[dict[str, Any]]
    last_updated: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    print("🚀 FEMA USAR MCP HTTP API starting up...")
    yield
    print("📴 FEMA USAR MCP HTTP API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="FEMA USAR MCP API",
    description="HTTP API for FEMA Urban Search and Rescue operations",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load existing data files
DATA_PATH = Path(__file__).parent.parent / "resources" / "ics_forms.json"
with DATA_PATH.open() as f:
    ICS_FORMS = [ICSForm(**item) for item in json.load(f)]

DATASET_PATH = Path(__file__).parent.parent / "resources" / "open_datasets.json"
with DATASET_PATH.open() as f:
    OPEN_DATASETS = [OpenDataset(**item) for item in json.load(f)]

DOCUMENTS_PATH = Path(__file__).parent.parent / "resources" / "documents.json"
if DOCUMENTS_PATH.exists():
    with DOCUMENTS_PATH.open() as f:
        DOCUMENTS = [Document(**item) for item in json.load(f)]
else:
    DOCUMENTS = []


# Health and Status Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return get_system_status()


@app.get("/status", response_model=dict[str, Any])
async def get_usar_status():
    """Get comprehensive USAR system status."""
    return {
        "system": "FEMA USAR MCP Server",
        "version": "0.1.0",
        "status": "operational",
        "capabilities": get_usar_capabilities(),
        "task_forces_supported": 28,
        "tools_available": 35,
    }


@app.get("/capabilities")
async def get_capabilities():
    """Get system capabilities and available tools."""
    return {
        "functional_groups": [
            "Command",
            "Search",
            "Rescue",
            "Medical",
            "Planning",
            "Logistics",
            "Technical Specialists",
        ],
        "tools": get_usar_capabilities()["tools"],
        "integrations": [
            "FEMA IRIS",
            "NIMS ICT",
            "Federal Asset Tracking",
            "Multi-band Radio Systems",
            "Satellite Communications",
        ],
        "personnel_positions": 70,
        "equipment_items": 16400,
    }


# USAR-specific endpoints
@app.post("/usar/status", response_model=USARStatusResponse)
async def get_task_force_status(request: USARStatusRequest):
    """Get task force operational status."""
    # This would integrate with actual task force data
    return USARStatusResponse(
        task_force_id=request.task_force_id,
        operational_status="Ready",
        personnel_count=70,
        equipment_ready=16400,
        mission_assignments=[],
        last_updated="2024-08-31T12:00:00Z",
    )


@app.post("/usar/deploy")
async def initiate_deployment(
    task_force_id: str,
    deployment_location: str,
    mission_type: str = "search_and_rescue",
):
    """Initiate task force deployment."""
    return {
        "deployment_id": f"DEPLOY-{task_force_id}-001",
        "task_force_id": task_force_id,
        "location": deployment_location,
        "mission_type": mission_type,
        "estimated_departure": "6 hours",
        "status": "deployment_initiated",
    }


# Existing ICS Forms endpoints
@app.get("/ics_forms", response_model=list[ICSForm])
def list_forms() -> list[ICSForm]:
    """List available ICS forms."""
    return ICS_FORMS


@app.get("/ics_forms/{form_id}", response_model=ICSForm)
def get_form(form_id: str) -> ICSForm:
    """Retrieve a specific ICS form by id."""
    for form in ICS_FORMS:
        if form.id.lower() == form_id.lower():
            return form
    raise HTTPException(status_code=404, detail="ICS form not found")


@app.get("/ics_forms/{form_id}/content")
def get_form_content(form_id: str) -> FileResponse:
    """Retrieve the actual ICS form file."""
    for form in ICS_FORMS:
        if form.id.lower() == form_id.lower():
            file_path = (
                Path(__file__).parent.parent / "resources" / "forms" / form.filename
            )
            if file_path.exists():
                return FileResponse(
                    file_path,
                    headers={
                        "Content-Disposition": f"attachment; filename={form.filename}"
                    },
                )
            else:
                raise HTTPException(status_code=404, detail="Form file not found")
    raise HTTPException(status_code=404, detail="ICS form not found")


# Existing datasets endpoints
@app.get("/datasets", response_model=list[OpenDataset])
def list_datasets() -> list[OpenDataset]:
    """List available open datasets."""
    return OPEN_DATASETS


@app.get("/datasets/{dataset_id}", response_model=OpenDataset)
def get_dataset(dataset_id: str) -> OpenDataset:
    """Retrieve details for a specific dataset."""
    for dataset in OPEN_DATASETS:
        if dataset.id.lower() == dataset_id.lower():
            return dataset
    raise HTTPException(status_code=404, detail="Dataset not found")


# Existing documents endpoints
@app.get("/documents", response_model=list[Document])
def list_documents() -> list[Document]:
    """List available documents."""
    return DOCUMENTS


@app.get("/documents/{document_id}", response_model=Document)
def get_document(document_id: str) -> Document:
    """Retrieve a specific document by id."""
    for doc in DOCUMENTS:
        if doc.id.lower() == document_id.lower():
            return doc
    raise HTTPException(status_code=404, detail="Document not found")


@app.get("/documents/{document_id}/content")
def get_document_content(document_id: str) -> FileResponse:
    """Retrieve the actual document file."""
    for doc in DOCUMENTS:
        if doc.id.lower() == document_id.lower():
            file_path = (
                Path(__file__).parent.parent / "resources" / "documents" / doc.filename
            )
            if file_path.exists():
                return FileResponse(
                    file_path,
                    headers={
                        "Content-Disposition": f"attachment; filename={doc.filename}"
                    },
                )
            else:
                raise HTTPException(status_code=404, detail="Document file not found")
    raise HTTPException(status_code=404, detail="Document not found")


def run():
    """Run the HTTP server."""
    import uvicorn

    host = os.getenv("UVICORN_HOST", "0.0.0.0")
    port = int(os.getenv("UVICORN_PORT", "8000"))

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=os.getenv("UVICORN_RELOAD", "false").lower() == "true",
        log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    run()
