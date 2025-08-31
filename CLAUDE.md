# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start the FastMCP server (primary interface)
python -m fema_usar_mcp.fastmcp_server
# or
fema-usar-mcp

# Start the HTTP API server (optional)
python -m app.main
# or
fema-usar-http
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fema_usar_mcp

# Run specific test categories
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
pytest -m slow          # Performance tests
```

### Code Quality
```bash
# Lint with ruff
ruff check .

# Format with ruff
ruff format .

# Type checking
mypy fema_usar_mcp/
```

### Package Management
```bash
# Install base package
pip install -e .

# Install with dev dependencies
pip install -e .[dev]

# Install all optional dependencies
pip install -e .[dev,advanced,visualization,integration]
```

## Architecture Overview

### Core System Design
This is a **FEMA Urban Search and Rescue (USAR) Model Context Protocol (MCP) server** providing AI-powered tools for emergency responders. The system supports all 28 FEMA USAR Task Forces with 70+ specialized digital tools organized by functional groups.

### Key Architectural Components

**FastMCP Server (`fema_usar_mcp/fastmcp_server.py`)**
- Primary MCP interface with 35+ registered tools
- Handles tool registration for all functional groups
- Provides performance monitoring and async task management
- Entry point: `fema-usar-mcp` command

**HTTP API Server (`app/main.py`)**
- Optional FastAPI-based REST interface
- Provides endpoints for health, status, ICS forms, and deployment operations
- CORS-enabled for web client integration
- Entry point: `fema-usar-http` command

**Core Domain Logic (`fema_usar_mcp/core.py`)**
- Business logic for USAR operations
- Task force configuration and readiness calculations
- System status and capabilities management
- Constants: 70 personnel positions, 16,400+ equipment items, 6-hour deployment target

### Functional Group Tool Architecture

Tools are organized by USAR operational structure in `fema_usar_mcp/tools/`:

- **Command Tools** (`command.py`): Task Force Leader dashboard, Safety Officer monitoring
- **Search Tools** (`search.py`): Victim tracking, Technical search equipment, Canine deployment
- **Rescue Tools** (`rescue.py`): Squad operations, Heavy equipment, Structural stabilization  
- **Medical Tools** (`medical.py`): Patient care, Medical supply inventory, Triage coordination
- **Planning Tools** (`planning.py`): Situational awareness, Resource tracking, Documentation
- **Logistics Tools** (`logistics.py`): Supply chain, Facilities, Ground support
- **Technical Tools** (`technical.py`): Structural assessment, Hazmat monitoring, Communications

Each tool module contains 5-8 specialized functions that return JSON-formatted operational data.

### Integration Architecture

**Federal Systems Integration** (placeholder implementations in `fema_usar_mcp/integrations/`):
- FEMA IRIS (Incident Resource Inventory System)
- NIMS ICT (National Incident Management System)
- Federal asset tracking systems
- Multi-band radio and satellite communications

**Performance Architecture** (`fema_usar_mcp/performance.py`):
- Async task processing for long-running operations
- LRU caching system for frequently accessed data
- Performance metrics and monitoring

**Security & Compliance** (`fema_usar_mcp/security/` and `fema_usar_mcp/compliance/`):
- Authentication and authorization systems
- FISMA compliance auditing
- Privacy and data protection controls

### Static Resources

**Resource Files** (`resources/`):
- `ics_forms.json`: ICS form catalog and metadata
- `forms/`: Physical ICS form files (PDF)
- `documents/`: Reference documentation
- `open_datasets.json`: Available datasets catalog

## Development Patterns

### Tool Function Pattern
All USAR tools follow this signature pattern:
```python
def tool_name(
    required_param: str,
    optional_param: str = "default",
    task_force_id: str = "DEFAULT-TF"
) -> str:
    """Tool description for MCP."""
    # Implementation returns JSON string
    return json.dumps(result, indent=2)
```

### Error Handling Pattern
Tools use consistent error handling:
```python
try:
    # Tool logic
    return json.dumps({"tool": "Tool Name", "status": "success", ...})
except Exception as e:
    return json.dumps({"tool": "Tool Name", "status": "error", "error": str(e)})
```

### Configuration Management
- Environment variables: `UVICORN_HOST`, `UVICORN_PORT`, `CORS_ORIGINS`
- Task force configurations use `USARTaskForceConfig` model
- System constants defined in `core.py`

## Testing Structure

Tests are categorized with pytest markers:
- `@pytest.mark.unit`: Fast unit tests
- `@pytest.mark.integration`: Integration tests with external systems  
- `@pytest.mark.slow`: Performance and load tests
- `@pytest.mark.requires_network`: Tests requiring network access

## GitHub Actions CI/CD

Two primary workflows:
- **CI/CD Pipeline** (`.github/workflows/ci.yml`): Tests, linting, security scans
- **Deploy** (`.github/workflows/deploy.yml`): Docker image builds and deployment

Both use `uv` for fast Python dependency management and ruff for linting/formatting.

## Key Dependencies

- **FastMCP**: MCP server framework (≥2.11.3)
- **FastAPI**: HTTP API framework
- **Pydantic**: Data validation and models
- **SQLAlchemy**: Database ORM for future data persistence
- **Ruff**: Code linting and formatting (replaces black)
- **pytest**: Testing framework

## Domain-Specific Context

This system is designed for **emergency response training and exercises only**. It simulates real USAR operations but should never be used in actual disaster scenarios. The system models:

- Type 1 USAR Task Force structure (70 personnel, 16,400+ equipment items)
- 72-96 hour self-sufficiency operations
- Federal emergency response protocols (NIMS/ICS)
- Equipment accountability and personnel tracking
- Multi-agency coordination and communication