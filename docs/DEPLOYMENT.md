# Deployment Guide

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager
- Docker (for containerized deployment)
- Fly.io CLI (for cloud deployment)

## Local Development

### Install Dependencies

```bash
# Basic installation
pip install -e .

# With development tools
pip install -e .[dev]

# All optional dependencies
pip install -e .[dev,advanced,visualization,integration]
```

### Run the MCP Server

```bash
# Eager loading (all tools available immediately)
fema-usar-mcp

# Latent loading (recommended for LLM clients)
fema-usar-mcp-latent

# Or via environment variable
USAR_MCP_LATENT_LOADING=true fema-usar-mcp
```

### Run the HTTP API Server

```bash
# Start HTTP API on port 8000
fema-usar-http

# Custom host/port
UVICORN_HOST=localhost UVICORN_PORT=8080 fema-usar-http

# Development mode with auto-reload
UVICORN_RELOAD=true fema-usar-http
```

## MCP Client Configuration

### Claude Desktop / Claude Code

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "fema-usar": {
      "command": "fema-usar-mcp",
      "args": []
    }
  }
}
```

For latent loading mode:

```json
{
  "mcpServers": {
    "fema-usar": {
      "command": "fema-usar-mcp-latent",
      "args": []
    }
  }
}
```

## Docker Deployment

### Build the Image

```bash
docker build -t fema-usar-mcp .
```

### Run the Container

```bash
# HTTP API server
docker run -p 8000:8000 fema-usar-mcp

# With environment variables
docker run -p 8000:8000 \
  -e UVICORN_HOST=0.0.0.0 \
  -e UVICORN_PORT=8000 \
  -e CORS_ORIGINS=https://yourdomain.com \
  fema-usar-mcp
```

### Docker Configuration

The `Dockerfile` uses:
- Base image: `python:3.12-slim`
- Exposed port: `8000`
- Default command: `python -m app.main` (HTTP API)

## Fly.io Deployment

### Initial Setup

```bash
# Install Fly.io CLI
curl -L https://fly.io/install.sh | sh

# Authenticate
fly auth login

# Launch the app
fly launch
```

### Deploy

```bash
fly deploy
```

### Configuration

The `fly.toml` configures:
- Region: `iad` (US East)
- Internal port: `8000`
- External ports: `80` (HTTP), `443` (HTTPS/TLS)
- Health checks: every 15 seconds

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UVICORN_HOST` | `0.0.0.0` | HTTP server bind address |
| `UVICORN_PORT` | `8000` | HTTP server port |
| `UVICORN_RELOAD` | `false` | Enable auto-reload (dev only) |
| `UVICORN_LOG_LEVEL` | `info` | Log level |
| `CORS_ORIGINS` | `localhost:3000,localhost:8080` | Allowed CORS origins |
| `USAR_SECURITY_ENABLED` | `false` | Enable RBAC security |
| `USAR_AUDIT_FILE_LOGGING` | `false` | Enable file-based audit logging |
| `USAR_AUDIT_LOG_FILE` | `/var/log/usar_audit.jsonl` | Audit log file path |
| `USAR_MCP_LATENT_LOADING` | `false` | Use latent loading mode |

## Security Configuration

### Enable RBAC

```bash
USAR_SECURITY_ENABLED=true fema-usar-mcp
```

When enabled, tool access is restricted based on the user's ICS role. Roles map to functional group permissions.

### Enable Audit Logging

```bash
USAR_AUDIT_FILE_LOGGING=true \
USAR_AUDIT_LOG_FILE=/var/log/usar_audit.jsonl \
fema-usar-mcp
```

Audit logs capture all tool invocations with timestamps, parameters (sanitized for sensitive data), and results.

## CI/CD Pipeline

The project includes GitHub Actions workflows:

- **ci.yml**: Runs on push/PR to main. Includes linting (ruff), testing (pytest), and security scanning (bandit).
- **deploy.yml**: Deploys to Fly.io on merge to main.
- **release.yml**: Creates releases on git tags, publishes to PyPI.
- **dependency-updates.yml**: Weekly dependency update checks.

## Monitoring

### Health Check

```bash
# HTTP API health
curl http://localhost:8000/health

# MCP health (via tool)
# Use usar_health_check tool through MCP client
```

### Performance Metrics

Available via the `usar_metrics` MCP tool or `get_system_performance` tool, providing:
- Tool registry statistics
- Cache hit rates and memory usage
- Active async task count
- Per-tool invocation counts

## Troubleshooting

### Common Issues

**Import errors on startup**: Ensure all dependencies are installed. Run `pip install -e .[dev]` for full setup.

**Resource files not found**: The HTTP API expects `resources/ics_forms.json` and `resources/open_datasets.json`. Missing files are handled gracefully with empty collections.

**High token usage in LLM clients**: Switch to latent loading mode (`fema-usar-mcp-latent`) for 96% token reduction.

**Performance issues**: Check cache statistics via `get_system_performance` tool. Clear stale caches with `clear_system_cache`.
