# mcp-fema-usar

A FastMCP server providing FEMA Urban Search and Rescue (USAR) workers with access to common ICS/NIMS resources. The server exposes endpoints for listing and retrieving Incident Command System (ICS) forms.

## Requirements
* Python 3.12+
* `fastmcp`
* `fastapi`

Install dependencies:

```bash
pip install fastmcp fastapi
```

## Running

Start the server with:

```bash
python server.py
```

The API will be available at `http://localhost:8000`. Endpoints include:

- `/ics_forms` – list available ICS forms.
- `/ics_forms/{id}` – get details about a specific form.

The server is built with `FastMCP` and wraps a small FastAPI application.
