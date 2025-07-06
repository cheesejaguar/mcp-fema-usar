from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from pathlib import Path
from fastapi.responses import FileResponse


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


app = FastAPI(title="FEMA USAR MCP Server")

DATA_PATH = Path(__file__).parent / "resources" / "ics_forms.json"
with DATA_PATH.open() as f:
    ICS_FORMS = [ICSForm(**item) for item in json.load(f)]

DATASET_PATH = Path(__file__).parent / "resources" / "open_datasets.json"
with DATASET_PATH.open() as f:
    OPEN_DATASETS = [OpenDataset(**item) for item in json.load(f)]

DOCUMENTS_PATH = Path(__file__).parent / "resources" / "documents.json"
if DOCUMENTS_PATH.exists():
    with DOCUMENTS_PATH.open() as f:
        DOCUMENTS = [Document(**item) for item in json.load(f)]
else:
    DOCUMENTS = []


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
            file_path = Path(__file__).parent / "resources" / "forms" / form.filename
            if file_path.exists():
                return FileResponse(file_path, headers={"Content-Disposition": f"attachment; filename={form.filename}"})
            else:
                raise HTTPException(status_code=404, detail="Form file not found")
    raise HTTPException(status_code=404, detail="ICS form not found")


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
            file_path = Path(__file__).parent / "resources" / "documents" / doc.filename
            if file_path.exists():
                return FileResponse(file_path, headers={"Content-Disposition": f"attachment; filename={doc.filename}"})
            else:
                raise HTTPException(status_code=404, detail="Document file not found")
    raise HTTPException(status_code=404, detail="Document not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
