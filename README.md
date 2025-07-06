# mcp-fema-usar

A server providing FEMA Urban Search and Rescue (USAR) workers with access to common ICS/NIMS resources. The server exposes endpoints for listing and retrieving Incident Command System (ICS) forms.

## Requirements
* Python 3.12+
* `fastapi`
* `uvicorn`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running

Start the server with:

```bash
python server.py
```

The API will be available at `http://localhost:8000`. Endpoints include:

- `/ics_forms` – list available ICS forms.
- `/ics_forms/{id}` – get details about a specific form.
- `/ics_forms/{id}/content` – get the actual form file.
- `/datasets` – list supported open datasets.
- `/datasets/{id}` – get details about a specific dataset.

## Example configuration

Tools like Cursor or ChatLM can connect to this server with a small JSON configuration. Copy `example_config.json` and adjust the `mcp_server` value if the server is hosted elsewhere.
