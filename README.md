# FEMA Urban Search and Rescue (USAR) MCP Server

A comprehensive Model Context Protocol (MCP) server providing specialized digital tools for all 28 FEMA USAR Task Forces during emergency response operations. This server implements domain-specific tools for each of the 70 personnel positions within a Type 1 USAR task force, enhancing operational effectiveness, safety, and coordination during disaster response missions.

## 🚀 Features

### **35+ Specialized Tools** organized by functional groups:
- **Command Tools**: Task Force Leader dashboard, Safety Officer monitoring, Personnel accountability
- **Search Tools**: Victim tracking, Technical search equipment, Canine team deployment
- **Rescue Tools**: Squad operations, Victim extraction planning, Heavy equipment operations
- **Medical Tools**: Patient care tracking, Medical supply inventory, Triage coordination
- **Planning Tools**: Situational awareness (SITL), Resource tracking (RESL), Documentation automation
- **Logistics Tools**: Supply chain management, Facilities coordination, Ground support tracking
- **Technical Specialist Tools**: Structural assessment, Hazmat monitoring, Communications management

### **Federal Integration**
- FEMA IRIS (Incident Resource Inventory System) integration
- NIMS/ICS protocol compliance and automation
- Federal asset tracking system interfaces
- Multi-band radio and satellite communication support

### **Field-Optimized Design**
- 72-96 hour self-sufficiency support with offline capabilities
- Real-time equipment accountability (16,400+ items)
- Personnel tracking for all 70 task force positions
- Rugged hardware compatibility and mobile optimization

## 📋 Requirements

### System Requirements
- Python 3.11 or higher
- FastMCP 2.11.3 or higher
- 4GB+ RAM recommended for full deployment
- Network connectivity (with offline fallback capabilities)

### Optional Dependencies
- Advanced analytics: `numpy`, `scipy`, `pandas`, `scikit-learn`
- Visualization: `matplotlib`, `plotly`, `folium`, `dash`
- Integration: `boto3`, `redis`, `celery`, `pika`

## 🛠️ Installation

### Basic Installation
```bash
# Clone the repository
git clone https://github.com/fema/fema-usar-mcp.git
cd fema-usar-mcp

# Install base dependencies
pip install -e .

# Or install with all features
pip install -e .[dev,advanced,visualization,integration]
```

### Development Installation
```bash
# Install with development tools
pip install -e .[dev]

# Set up pre-commit hooks (optional)
pre-commit install
```

## 🚀 Running the Server

### MCP Server (Primary Interface)
```bash
# Start the FastMCP server
fema-usar-mcp

# Or run directly
python -m fema_usar_mcp.fastmcp_server
```

### HTTP API Server (Optional)
```bash
# Start the HTTP API server
fema-usar-http

# Or run directly
python -m app.main
```

The HTTP API will be available at `http://localhost:8000` with the following endpoints:

## 📡 API Endpoints

### Health and Status
- `GET /health` – System health check
- `GET /status` – Comprehensive system status
- `GET /capabilities` – Available tools and integrations

### USAR Operations
- `POST /usar/status` – Get task force operational status
- `POST /usar/deploy` – Initiate task force deployment

### ICS Forms and Resources
- `GET /ics_forms` – List available ICS forms
- `GET /ics_forms/{id}` – Get specific ICS form details
- `GET /ics_forms/{id}/content` – Download ICS form file
- `GET /datasets` – List available open datasets
- `GET /documents` – List available reference documents

## 🔧 MCP Tools

### Command Group Tools
```python
# Task Force Leader Dashboard
task_force_leader_dashboard(task_force_id="CA-TF1", include_personnel=True)

# Safety Officer Monitoring
safety_officer_monitor(monitoring_mode="real_time")

# Personnel Accountability
personnel_accountability(accountability_type="full")
```

### Search Group Tools
```python
# Victim Location Tracking
victim_location_tracker(search_area_id="AREA-A1", victim_status="confirmed")

# Technical Search Equipment
technical_search_equipment(equipment_type="delsar", operation_mode="active")

# Canine Team Deployment
canine_team_deployment(search_type="live_find", deployment_status=True)
```

### Example Tool Usage
```python
from fema_usar_mcp.tools.command import task_force_leader_dashboard

# Get comprehensive dashboard for CA-TF1
result = task_force_leader_dashboard(
    task_force_id="CA-TF1",
    include_personnel=True,
    include_equipment=True,
    include_missions=True
)
print(result)  # Returns JSON with complete situational awareness
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run with coverage
pytest --cov=fema_usar_mcp

# Run specific test categories
pytest -m integration
pytest -m slow
```

### Test Categories
- `unit`: Fast unit tests
- `integration`: Integration tests with external systems
- `slow`: Performance and load tests
- `requires_network`: Tests requiring network access

## 📁 Project Structure

```
fema-usar-mcp/
├── pyproject.toml              # Project configuration and dependencies
├── README.md                   # This file
├── LICENSE                     # MIT license
│
├── fema_usar_mcp/             # Main package
│   ├── __init__.py            # Package initialization
│   ├── fastmcp_server.py      # FastMCP server implementation
│   ├── core.py                # Core business logic and models
│   │
│   ├── tools/                 # MCP tools organized by function
│   │   ├── command.py         # Command group tools
│   │   ├── search.py          # Search team tools
│   │   ├── rescue.py          # Rescue team tools
│   │   ├── medical.py         # Medical team tools
│   │   ├── planning.py        # Planning section tools
│   │   ├── logistics.py       # Logistics section tools
│   │   └── technical.py       # Technical specialist tools
│   │
│   ├── models/                # Pydantic data models
│   │   ├── personnel.py       # Personnel and position models
│   │   ├── equipment.py       # Equipment and inventory models
│   │   └── operations.py      # Mission and operation models
│   │
│   └── integrations/          # External system integrations
│       ├── fema_systems.py    # FEMA IRIS, NIMS ICT integration
│       ├── equipment.py       # Equipment tracking systems
│       └── communications.py  # Communication system interfaces
│
├── app/                       # Optional HTTP API
│   ├── __init__.py
│   └── main.py               # FastAPI application
│
├── tests/                     # Comprehensive test suite
│   ├── conftest.py           # Test configuration
│   ├── test_fastmcp.py       # FastMCP server tests
│   └── test_http_api.py      # HTTP API tests
│
├── resources/                 # Static resources
│   ├── ics_forms.json        # ICS form catalog
│   ├── documents.json        # Document catalog
│   ├── forms/                # ICS form files
│   └── documents/            # Reference documents
│
└── docs/                     # Additional documentation
    ├── ARCHITECTURE.md       # System architecture
    ├── DEPLOYMENT.md         # Deployment guide
    └── API.md               # API reference
```

## 🔒 Security and Compliance

### Federal Security Standards
- **FISMA Compliance**: Follows Federal Information Security Management Act requirements
- **FedRAMP Ready**: Designed for FedRAMP authorization process
- **NIST Cybersecurity Framework**: Implements NIST security controls
- **PIV Card Integration**: Supports Personal Identity Verification card authentication

### Data Protection
- **Encryption**: AES-256 encryption for data at rest and in transit
- **Access Control**: Role-based access control aligned with ICS positions
- **Audit Logging**: Comprehensive audit trail for all system activities
- **Privacy Compliance**: Adheres to Privacy Act requirements for PII protection

## 🌐 Integration

### MCP Client Configuration
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

### Environment Configuration
```bash
# Production settings
export UVICORN_HOST=0.0.0.0
export UVICORN_PORT=8080
export UVICORN_WORKERS=4
export CORS_ORIGINS=https://yourdomain.com

# Development settings
export UVICORN_RELOAD=true
export UVICORN_LOG_LEVEL=debug
```

## 📊 Performance Metrics

### Target Performance
- **Deployment Time**: <5.1 hours (15% improvement over 6-hour target)
- **Equipment Accountability**: 99.5% accuracy
- **Information Processing**: 40% reduction in processing time
- **Documentation Automation**: 80% of ICS forms automated
- **System Uptime**: 99.9% availability during operations

### Operational Capacity
- **Personnel Positions**: 70 tracked positions per task force
- **Equipment Items**: 16,400+ items managed per task force
- **Task Forces**: 28 FEMA task forces supported nationwide
- **Self-Sufficiency**: 72-96 hour offline operation capability

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes following the coding standards
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Coding Standards
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Write comprehensive docstrings
- Maintain test coverage above 90%
- Use semantic versioning for releases

## 📝 Documentation

### Additional Resources
- [Product Requirements Document (PRD)](PRD.md) - Comprehensive requirements
- [Development Standard](STANDARD.md) - Implementation guidelines
- [Architecture Documentation](docs/ARCHITECTURE.md) - System design
- [API Reference](docs/API.md) - Complete API documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

### Training Materials
- FEMA USAR personnel training modules
- System administrator guides
- Integration documentation for external systems
- Troubleshooting and maintenance procedures

## 🆘 Support

### Getting Help
- **Issues**: Report bugs at [GitHub Issues](https://github.com/fema/fema-usar-mcp/issues)
- **Documentation**: See [docs/](docs/) directory
- **Training**: Contact FEMA USAR Program Office
- **Emergency Support**: 24/7 support during active deployments

### System Status
- **Service Status**: [status.fema-usar-mcp.gov](https://status.fema-usar-mcp.gov)
- **Maintenance Windows**: Announced via FEMA channels
- **Version Updates**: Automatic during maintenance windows

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏛️ Acknowledgments

- **FEMA Urban Search and Rescue Program Office** - Program oversight and requirements
- **28 FEMA USAR Task Forces** - Operational requirements and testing
- **National Institute of Standards and Technology (NIST)** - Cybersecurity framework
- **Department of Homeland Security (DHS)** - Security and compliance guidance

---

**For official FEMA USAR information, visit:** [https://www.fema.gov/emergency-managers/practitioners/urban-search-rescue](https://www.fema.gov/emergency-managers/practitioners/urban-search-rescue)

**Emergency Response:** This system is designed to support life-saving operations. For actual emergencies, contact local emergency services immediately.