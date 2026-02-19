# System Architecture

## Overview

The Federal USAR MCP Server is a domain-specific Model Context Protocol (MCP) server providing 38+ specialized tools for all 28 Federal USAR Task Forces. The system is built on FastMCP and follows a modular, domain-driven architecture.

## System Context

```
External Systems          Federal USAR MCP Server          Clients
+--------------+         +------------------------+       +-------------+
| FEMA IRIS    |<------->| FastMCP Server (MCP)   |<----->| LLM Clients |
| NIMS ICT     |         | FastAPI Server (HTTP)  |       | Claude, etc |
| Asset Tracking|         | Tool Registry          |       +-------------+
| Radio Systems|         | Core Business Logic    |       +-------------+
+--------------+         +------------------------+       | HTTP Clients|
                                                          | Web Apps    |
                                                          +-------------+
```

## Core Components

### 1. FastMCP Server (`fema_usar_mcp/fastmcp_server.py`)

The primary interface. Registers all 38+ operational tools plus system/meta-tools with the MCP framework. Supports eager loading where all tools are available immediately (~122,800 tokens).

Entry point: `fema-usar-mcp`

### 2. Latent FastMCP Server (`fema_usar_mcp/fastmcp_server_latent.py`)

Lightweight alternative that only exposes 6 meta-tools at startup (~5,200 tokens, 96% reduction). Functional tools are loaded on-demand via `usar_execute_tool`.

Meta-tools exposed:
- `usar_browse_categories` - Discover tool categories
- `usar_list_tools` - List tools in a category
- `usar_get_tool_schema` - Get full schema for a tool
- `usar_execute_tool` - Execute any tool by name
- `usar_health_check` - System health status
- `usar_metrics` - Performance metrics

Entry point: `fema-usar-mcp-latent`

### 3. Tool Registry (`fema_usar_mcp/tool_registry.py`)

Stores lightweight metadata for all tools without importing implementations. Supports:
- Dynamic import and schema extraction on demand
- Schema caching with configurable TTL
- Thread-safe operations
- Tool execution by name with parameter passing

### 4. Core Business Logic (`fema_usar_mcp/core.py`)

Domain models and constants:
- `USARTaskForceConfig` - Task force configuration model
- `OperationalStatus` - Status enum (ready, deployed, etc.)
- `PersonnelPosition` - Position tracking model
- `EquipmentItem` - Equipment tracking model
- Deployment readiness calculations
- System status and capabilities

### 5. HTTP API Server (`app/main.py`)

Optional FastAPI-based REST interface providing:
- Health/status endpoints
- ICS form catalog and file serving
- USAR status and deployment endpoints
- Open dataset catalog
- Document management

Entry point: `fema-usar-http`

## Tool Architecture

Tools are organized by USAR functional groups in `fema_usar_mcp/tools/`:

| Module | Tools | Description |
|--------|-------|-------------|
| `command.py` | 5 | Task Force Leader, Safety Officer, Personnel, Missions, Coordination |
| `search.py` | 5 | Victim Tracking, Search Patterns, Tech Search, Canine, Void Space |
| `rescue.py` | 5 | Squad Ops, Victim Extraction, Heavy Equipment, Stabilization, Debris |
| `medical.py` | 5 | Patient Care, Medical Supply, Triage, Health Surveillance, Evacuation |
| `planning.py` | 5 | SITL Dashboard, RESL Tracker, Documentation, Demobilization, Timeline |
| `logistics.py` | 5 | Supply Chain, Facilities, Ground Support, Fuel, Maintenance |
| `technical.py` | 5 | Structural Assessment, Hazmat, Communications, Rigging, Environmental |
| `decision_support.py` | 3 | Tactical Decision, Strategic Planning, Operational Intelligence |

**Total**: 38 functional tools + system/meta-tools

### Tool Function Pattern

All tools follow a consistent signature:
```python
def tool_name(
    required_param: str,
    optional_param: str = "default",
    task_force_id: str = "DEFAULT-TF"
) -> str:
    """Tool description for MCP."""
    return json.dumps(result, indent=2)
```

### Middleware Stack (Command Tools)

Command group tools apply security and performance decorators:
```python
@performance_optimized_tool(cache_ttl=120, enable_monitoring=True)
@audited_tool
@secured_tool
def task_force_leader_dashboard(...) -> str:
```

## Supporting Components

### Models (`fema_usar_mcp/models/`)
- `personnel.py` - Personnel positions, qualifications, accountability
- `equipment.py` - Equipment inventory, maintenance, status
- `operations.py` - Missions, deployments, operational status

### Integrations (`fema_usar_mcp/integrations/`)
- `fema_iris.py` - Federal IRIS system (placeholder)
- `nims_ict.py` - NIMS ICT protocol compliance (placeholder)
- `fema_systems.py` - General FEMA systems
- `equipment.py` - Equipment tracking systems
- `communications.py` - Multi-band radio and satellite

### Security (`fema_usar_mcp/security/` and `fema_usar_mcp/middleware/`)
- RBAC permission checking via `auth_middleware.py`
- Audit logging via `audit_middleware.py`
- PIV card authentication via `security/auth.py`
- FISMA compliance via `compliance/audit.py`

### Performance (`fema_usar_mcp/performance.py` and `async_performance.py`)
- LRU caching with configurable TTL
- Async task processing for long-running operations
- Performance metrics and monitoring
- Rate limiting

## Data Flow

```
Client Request
    |
    v
FastMCP Server / HTTP API
    |
    v
Middleware (Auth -> Audit -> Performance)
    |
    v
Tool Function (in tools/*.py)
    |
    v
Core Business Logic (core.py)
    |
    v
Integration Layer (integrations/*.py)
    |
    v
JSON Response -> Client
```

## Deployment Architecture

### Docker
```
Dockerfile -> python:3.12-slim
  Port: 8000 (HTTP API)
  CMD: python -m app.main
```

### Fly.io
```
fly.toml -> iad region
  HTTP: port 80/443
  Internal: port 8000
  Health checks: 15s intervals
```

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `UVICORN_HOST` | `0.0.0.0` | HTTP server bind address |
| `UVICORN_PORT` | `8000` | HTTP server port |
| `CORS_ORIGINS` | `localhost` | Allowed CORS origins |
| `USAR_SECURITY_ENABLED` | `false` | Enable RBAC security |
| `USAR_AUDIT_FILE_LOGGING` | `false` | Enable file-based audit logging |
| `USAR_MCP_LATENT_LOADING` | `false` | Use latent loading mode |
