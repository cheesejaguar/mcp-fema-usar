# mcp-fema-usar

A FastMCP server providing FEMA Urban Search and Rescue (USAR) workers with access to common ICS/NIMS resources. The server exposes endpoints for listing and retrieving Incident Command System (ICS) forms.

## What is an MCP server?

MCP stands for **Model Context Protocol**. An MCP server is a simple web
service that follows this standard so different software tools can ask it
for data in a consistent way. Think of it as a hub that keeps all the forms
and reference material in one place so other apps—including AI-based tools—can
pull what they need without hunting around.

### Why use one?

For FEMA rescue workers, using an MCP server means you have a reliable source for
ICS forms and other important documents. Instead of digging through folders
or emailing files back and forth, you can point your apps to the server and
get the latest versions instantly. This helps your team stay coordinated and
saves time during busy operations.

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
- `/datasets` – list supported open datasets.
- `/datasets/{id}` – get details about a specific dataset.

The server is built with `FastMCP` and wraps a small FastAPI application.
