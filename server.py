from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
from pydantic import BaseModel
import json
from pathlib import Path


class ICSForm(BaseModel):
    id: str
    name: str
    description: str


app = FastAPI(title="FEMA USAR MCP Server")

DATA_PATH = Path(__file__).parent / "resources" / "ics_forms.json"
with DATA_PATH.open() as f:
    ICS_FORMS = [ICSForm(**item) for item in json.load(f)]


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


server = FastMCP.from_fastapi(app, name="fema-usar")

if __name__ == "__main__":
    import uvicorn

    # FastMCPOpenAPI implements the ASGI interface directly
    uvicorn.run(server, host="0.0.0.0", port=8000)
