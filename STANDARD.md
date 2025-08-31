# FastMCP Server Development Standard

**Version:** 1.0  
**Last Updated:** August 2024  
**Framework:** FastMCP 2.11.3+  

---

## 📋 **Overview**

This document provides a comprehensive technical standard for building specialized Model Context Protocol (MCP) servers using the FastMCP framework. The patterns described here can be applied to any domain - from physics and finance to biology and engineering.

## 🏗️ **Architecture Pattern**

### **Core Principles**

1. **Domain-Driven Design**: Organize tools by logical specialty areas
2. **Modular Architecture**: Separate concerns into focused modules
3. **Dual Interface Support**: Provide both HTTP REST API and MCP interfaces
4. **Type Safety First**: Use Python type hints for automatic schema generation
5. **Graceful Degradation**: Handle optional dependencies elegantly
6. **Performance Optimization**: Design for speed and scalability

### **Directory Structure**

```
your-specialty-mcp/
├── pyproject.toml              # Project configuration
├── README.md                   # Comprehensive documentation
├── index.html                  # Professional landing page
├── RELEASE_NOTES_v*.md         # Version release notes
├── LICENSE                     # MIT license recommended
│
├── your_specialty_mcp/         # Main package
│   ├── __init__.py            # Package initialization
│   ├── fastmcp_server.py      # FastMCP server implementation
│   ├── core.py                # Shared business logic
│   │
│   ├── tools/                 # Modular tool organization
│   │   ├── __init__.py
│   │   ├── core.py           # Essential domain tools
│   │   ├── analysis.py       # Analysis and computation tools
│   │   ├── modeling.py       # Mathematical modeling tools
│   │   ├── optimization.py   # Optimization algorithms
│   │   ├── visualization.py  # Data visualization tools
│   │   └── integration.py    # External system integration
│   │
│   └── integrations/          # Third-party integrations
│       ├── __init__.py
│       ├── domain_lib1.py    # Integration with domain library 1
│       └── domain_lib2.py    # Integration with domain library 2
│
├── tests/                     # Comprehensive test suite
│   ├── conftest.py           # Test configuration
│   ├── test_fastmcp.py       # FastMCP server tests
│   ├── test_core.py          # Core functionality tests
│   ├── test_tools_*.py       # Tool module tests
│   └── test_integrations_*.py # Integration tests
│
├── app/                       # Optional HTTP API
│   ├── __init__.py
│   └── main.py               # FastAPI application
│
└── docs/                      # Additional documentation
    ├── API.md
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT.md
    └── CONTRIBUTING.md
```

## 🛠️ **Implementation Guide**

### **Step 1: Project Setup**

#### **pyproject.toml Configuration**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "your-specialty-mcp"
version = "0.1.0"
description = "MCP server for [your specialty] operations"
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
license = { text = "MIT" }
readme = "README.md"
requires-python = ">=3.11"
keywords = ["mcp", "your-specialty", "ai-tools"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering",
]

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "fastmcp>=2.11.3",
    "pydantic>=2.0.0",
    # Add your domain-specific core dependencies here
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "httpx>=0.25.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.6.0",
]
# Add optional dependency groups for your domain
advanced = [
    "numpy>=1.24.0",
    "scipy>=1.11.0",
    "pandas>=2.0.0",
]
visualization = [
    "matplotlib>=3.7.0",
    "plotly>=5.15.0",
]

[project.scripts]
your-specialty-mcp = "your_specialty_mcp.fastmcp_server:run"
your-specialty-http = "app.main:run"
```

### **Step 2: Core Business Logic**

#### **core.py - Domain Models and Logic**

```python
from __future__ import annotations

from typing import Literal, Any, Dict, List
from pydantic import BaseModel, Field
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Domain-specific constants
DOMAIN_CONSTANT_1 = "value1"
DOMAIN_CONSTANT_2 = 42

# Check for optional dependencies
ADVANCED_LIBRARY_AVAILABLE = True
try:
    import advanced_domain_library
except ImportError:
    ADVANCED_LIBRARY_AVAILABLE = False

# Pydantic models for your domain
class DomainRequest(BaseModel):
    """Request model for domain operations."""
    input_parameter: str = Field(..., description="Primary input parameter")
    optional_parameter: float | None = Field(None, description="Optional parameter")
    processing_options: Dict[str, Any] = Field(default_factory=dict)

class DomainResponse(BaseModel):
    """Response model for domain operations."""
    result: Any
    metadata: Dict[str, Any]
    processing_time_ms: float
    
class DomainError(Exception):
    """Domain-specific error handling."""
    pass

# Core business logic functions
def process_domain_request(request: DomainRequest) -> DomainResponse:
    """Main business logic for domain operations."""
    start_time = time.time()
    
    try:
        # Your domain logic here
        result = perform_domain_calculation(
            request.input_parameter,
            request.optional_parameter,
            **request.processing_options
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return DomainResponse(
            result=result,
            metadata={"status": "success"},
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Domain processing error: {str(e)}", exc_info=True)
        raise DomainError(f"Processing failed: {str(e)}")

def perform_domain_calculation(param1: str, param2: float = None, **options) -> Any:
    """Domain-specific calculation logic."""
    # Implement your core domain calculations
    pass

def get_system_status() -> Dict[str, Any]:
    """Return system status and capabilities."""
    return {
        "system": "Your Specialty MCP Server",
        "version": "0.1.0",
        "status": "operational",
        "capabilities": {
            "core_operations": True,
            "advanced_features": ADVANCED_LIBRARY_AVAILABLE,
        },
        "advanced_library_available": ADVANCED_LIBRARY_AVAILABLE,
    }
```

### **Step 3: FastMCP Server Implementation**

#### **fastmcp_server.py - Main Server**

```python
"""FastMCP server implementation for [Your Specialty] tools."""

import logging
import sys

from fastmcp import FastMCP

# Import all tool modules
from .tools.core import (
    primary_operation,
    secondary_operation,
    get_domain_status,
)
from .tools.analysis import (
    analyze_data,
    generate_report,
)
from .tools.modeling import (
    create_model,
    validate_model,
)
from .tools.optimization import (
    optimize_parameters,
    sensitivity_analysis,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("your-specialty-mcp")

# Register core tools
mcp.tool(primary_operation)
mcp.tool(secondary_operation)
mcp.tool(get_domain_status)

# Register analysis tools
mcp.tool(analyze_data)
mcp.tool(generate_report)

# Register modeling tools
mcp.tool(create_model)
mcp.tool(validate_model)

# Register optimization tools
mcp.tool(optimize_parameters)
mcp.tool(sensitivity_analysis)

def run():
    """Run the MCP server."""
    try:
        logger.info("Starting Your Specialty MCP server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run()
```

### **Step 4: Tool Module Pattern**

#### **tools/core.py - Core Domain Tools**

```python
"""Core tools for [your specialty] operations."""

import json
import logging
from typing import Literal

from ..core import (
    ADVANCED_LIBRARY_AVAILABLE,
    DomainError,
    DomainRequest,
    process_domain_request,
    get_system_status as _get_system_status,
)

logger = logging.getLogger(__name__)

def primary_operation(
    input_data: str,
    processing_mode: Literal["fast", "accurate", "comprehensive"] = "accurate",
    options: dict | None = None
) -> str:
    """Perform the primary domain operation.
    
    Args:
        input_data: Primary input for the operation
        processing_mode: Processing mode selection
        options: Optional processing parameters
        
    Returns:
        JSON string with operation results
    """
    try:
        request = DomainRequest(
            input_parameter=input_data,
            processing_options=options or {}
        )
        
        result = process_domain_request(request)
        
        return json.dumps({
            "operation": "primary",
            "mode": processing_mode,
            "result": result.result,
            "metadata": result.metadata,
            "processing_time_ms": result.processing_time_ms
        }, indent=2)
        
    except DomainError as e:
        return f"Domain operation error: {str(e)}"
    except Exception as e:
        logger.error(f"Primary operation error: {str(e)}", exc_info=True)
        return f"Unexpected error: {str(e)}"

def secondary_operation(
    input_data: dict,
    validation_level: Literal["basic", "thorough"] = "basic"
) -> str:
    """Perform secondary domain operation with validation.
    
    Args:
        input_data: Input data dictionary
        validation_level: Level of validation to perform
        
    Returns:
        JSON string with operation results
    """
    try:
        # Your secondary operation logic here
        result = perform_secondary_calculation(input_data, validation_level)
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Secondary operation error: {str(e)}", exc_info=True)
        return f"Secondary operation error: {str(e)}"

def get_domain_status() -> str:
    """Get system status and capabilities.
    
    Returns:
        JSON string with system status information
    """
    status = _get_system_status()
    return json.dumps(status, indent=2)

def perform_secondary_calculation(data: dict, level: str) -> dict:
    """Implement your secondary calculation logic."""
    # Add your domain-specific logic
    return {"status": "completed", "validation_level": level}
```

#### **tools/analysis.py - Analysis Tools**

```python
"""Analysis tools for [your specialty]."""

import json
import logging
from typing import List

logger = logging.getLogger(__name__)

def analyze_data(
    dataset: List[dict],
    analysis_type: str = "comprehensive",
    parameters: dict | None = None
) -> str:
    """Perform data analysis on the provided dataset.
    
    Args:
        dataset: List of data records to analyze
        analysis_type: Type of analysis to perform
        parameters: Optional analysis parameters
        
    Returns:
        JSON string with analysis results
    """
    try:
        # Your analysis logic here
        results = perform_data_analysis(dataset, analysis_type, parameters or {})
        
        return json.dumps({
            "analysis_type": analysis_type,
            "data_points": len(dataset),
            "results": results,
            "summary_statistics": calculate_summary_stats(results)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Data analysis error: {str(e)}", exc_info=True)
        return f"Analysis error: {str(e)}"

def generate_report(
    analysis_results: dict,
    report_format: str = "summary",
    include_charts: bool = True
) -> str:
    """Generate a formatted report from analysis results.
    
    Args:
        analysis_results: Results from previous analysis
        report_format: Format of the report (summary, detailed, executive)
        include_charts: Whether to include chart descriptions
        
    Returns:
        Formatted report string
    """
    try:
        # Your report generation logic here
        report = create_formatted_report(analysis_results, report_format, include_charts)
        
        return report
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}", exc_info=True)
        return f"Report generation error: {str(e)}"

def perform_data_analysis(dataset: List[dict], analysis_type: str, params: dict) -> dict:
    """Implement your data analysis logic."""
    # Add your domain-specific analysis
    return {"analyzed": True, "type": analysis_type}

def calculate_summary_stats(results: dict) -> dict:
    """Calculate summary statistics."""
    # Add your statistical calculations
    return {"mean": 0, "std": 0, "count": 0}

def create_formatted_report(results: dict, format_type: str, include_charts: bool) -> str:
    """Create formatted report."""
    # Add your report formatting logic
    return f"Report ({format_type}): Analysis completed successfully."
```

### **Step 5: Integration Patterns**

#### **integrations/domain_library.py - Third-party Integration**

```python
"""Integration with domain-specific libraries."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Check library availability
LIBRARY_AVAILABLE = True
try:
    import domain_specific_library
except ImportError:
    LIBRARY_AVAILABLE = False
    logger.warning("Domain library not available - some features will be limited")

class LibraryIntegrationError(Exception):
    """Raised when library integration fails."""
    pass

def perform_advanced_calculation(
    input_data: Dict[str, Any],
    method: str = "default",
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Perform calculation using external library.
    
    Args:
        input_data: Input parameters for calculation
        method: Calculation method to use
        options: Optional calculation parameters
        
    Returns:
        Dictionary with calculation results
        
    Raises:
        LibraryIntegrationError: If library is not available or calculation fails
    """
    if not LIBRARY_AVAILABLE:
        raise LibraryIntegrationError(
            "Domain library not available. Install with: pip install domain-library"
        )
    
    try:
        # Use the external library
        calculator = domain_specific_library.Calculator(method=method)
        result = calculator.compute(input_data, **(options or {}))
        
        return {
            "result": result,
            "method_used": method,
            "library_version": domain_specific_library.__version__,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Library calculation error: {str(e)}", exc_info=True)
        raise LibraryIntegrationError(f"Calculation failed: {str(e)}")

def get_library_status() -> Dict[str, Any]:
    """Get status of external library integration."""
    status = {
        "available": LIBRARY_AVAILABLE,
        "library_name": "domain-specific-library"
    }
    
    if LIBRARY_AVAILABLE:
        try:
            status.update({
                "version": domain_specific_library.__version__,
                "features": domain_specific_library.get_available_features(),
                "status": "operational"
            })
        except Exception as e:
            status["status"] = f"error: {str(e)}"
    else:
        status["status"] = "not_installed"
        status["install_command"] = "pip install domain-specific-library"
    
    return status
```

### **Step 6: Testing Pattern**

#### **test_fastmcp.py - FastMCP Server Tests**

```python
"""Tests for FastMCP server functionality."""

from unittest.mock import patch
import pytest

from your_specialty_mcp.fastmcp_server import mcp
from your_specialty_mcp.tools.core import (
    primary_operation,
    secondary_operation,
    get_domain_status,
)

class TestFastMCPServerInitialization:
    """Tests for FastMCP server initialization."""

    @pytest.mark.unit
    def test_server_instance_created(self):
        """Test that FastMCP server instance is created correctly."""
        assert mcp is not None
        assert mcp.name == "your-specialty-mcp"

    @pytest.mark.unit
    def test_tools_registered(self):
        """Test that all required tools are registered."""
        # The tools are registered as functions, so we can verify they exist
        assert callable(primary_operation)
        assert callable(secondary_operation)
        assert callable(get_domain_status)

class TestPrimaryOperationTool:
    """Tests for the primary_operation tool."""

    @pytest.mark.unit
    def test_primary_operation_basic(self):
        """Test basic primary operation functionality."""
        result = primary_operation("test_input", "fast")
        
        assert "primary" in result
        assert "test_input" in result or "processing" in result

    @pytest.mark.unit
    @patch("your_specialty_mcp.tools.core.process_domain_request")
    def test_primary_operation_with_mock(self, mock_process):
        """Test primary operation with mocked dependencies."""
        # Mock the core processing function
        mock_process.return_value.result = {"calculated": True}
        mock_process.return_value.metadata = {"status": "success"}
        mock_process.return_value.processing_time_ms = 100.0
        
        result = primary_operation("test_input")
        
        assert "calculated" in result
        mock_process.assert_called_once()

class TestDomainStatusTool:
    """Tests for the get_domain_status tool."""

    @pytest.mark.unit
    def test_get_domain_status(self):
        """Test domain status retrieval."""
        result = get_domain_status()
        
        assert "Your Specialty MCP Server" in result
        assert "operational" in result
        assert "capabilities" in result
```

### **Step 7: HTTP API Integration (Optional)**

#### **app/main.py - FastAPI Integration**

```python
"""FastAPI HTTP interface for [Your Specialty] MCP server."""

import os
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from your_specialty_mcp.core import (
    DomainRequest,
    DomainResponse,
    process_domain_request,
    get_system_status,
)

# Request/Response models for HTTP API
class HTTPDomainRequest(BaseModel):
    input_parameter: str
    optional_parameter: float | None = None
    processing_options: Dict[str, Any] = {}

class HTTPDomainResponse(BaseModel):
    result: Any
    metadata: Dict[str, Any]
    processing_time_ms: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("🚀 Your Specialty MCP HTTP API starting up...")
    yield
    # Shutdown
    print("📴 Your Specialty MCP HTTP API shutting down...")

# Create FastAPI application
app = FastAPI(
    title="Your Specialty MCP API",
    description="HTTP API for [Your Specialty] operations",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return get_system_status()

@app.post("/process", response_model=HTTPDomainResponse)
async def process_domain_operation(request: HTTPDomainRequest):
    """Process domain operation via HTTP."""
    try:
        domain_request = DomainRequest(
            input_parameter=request.input_parameter,
            optional_parameter=request.optional_parameter,
            processing_options=request.processing_options
        )
        
        result = process_domain_request(domain_request)
        
        return HTTPDomainResponse(
            result=result.result,
            metadata=result.metadata,
            processing_time_ms=result.processing_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/capabilities")
async def get_capabilities():
    """Get system capabilities."""
    return {
        "tools": [
            "primary_operation",
            "secondary_operation", 
            "analyze_data",
            "generate_report",
            "create_model",
            "optimize_parameters",
        ],
        "status": get_system_status()
    }

def run():
    """Run the HTTP server."""
    import uvicorn
    
    host = os.getenv("UVICORN_HOST", "0.0.0.0")
    port = int(os.getenv("UVICORN_PORT", "8080"))
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=os.getenv("UVICORN_RELOAD", "false").lower() == "true",
        log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
    )

if __name__ == "__main__":
    run()
```

### **Step 8: Landing Page Template**

#### **index.html - Professional Landing Page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Your Specialty] MCP - Comprehensive [Domain] Operations API</title>
    <meta name="description" content="Open-source [your specialty] platform with [key features]. Features X+ tools and FastMCP integration.">
    <meta name="keywords" content="[your-specialty], MCP, FastAPI, [domain-keywords]">
    <meta name="author" content="[Your Specialty] MCP Project">
    
    <style>
        /* Use the same CSS framework as aerospace-mcp */
        :root {
            --primary-color: #1e40af;    /* Adjust for your domain */
            --secondary-color: #7c3aed;
            --accent-color: #f59e0b;
            /* ... rest of CSS variables */
        }
        /* Include all the CSS from aerospace-mcp/index.html */
    </style>
</head>
<body>
    <!-- Adapt the HTML structure for your domain -->
    <header class="header">
        <div class="hero-content">
            <h1>🎯 [Your Specialty] MCP</h1>
            <p>Comprehensive [domain description] with FastMCP integration and X+ specialized tools.</p>
            
            <!-- Update stats for your domain -->
            <div class="stats">
                <div class="stat">
                    <span class="stat-number">X+</span>
                    <div class="stat-label">[Domain] Tools</div>
                </div>
                <!-- Add more relevant stats -->
            </div>
        </div>
    </header>
    
    <!-- Update feature cards for your domain -->
    <section id="features" class="section">
        <h2>🌟 Comprehensive [Domain] Capabilities</h2>
        <div class="features-grid">
            <!-- Create feature cards specific to your domain -->
        </div>
    </section>
    
    <!-- Include the same JavaScript for interactivity -->
    <script>
        /* Include all JavaScript from aerospace-mcp/index.html */
    </script>
</body>
</html>
```

## 🧪 **Testing Standards**

### **Test Organization**

```python
# test_conftest.py
import pytest
from your_specialty_mcp.fastmcp_server import mcp

@pytest.fixture
def sample_domain_data():
    """Provide sample data for testing."""
    return {
        "input_parameter": "test_value",
        "optional_parameter": 42.0,
        "processing_options": {"mode": "test"}
    }

@pytest.fixture
def mock_advanced_library(monkeypatch):
    """Mock advanced library for testing."""
    # Mock external dependencies
    pass
```

### **Test Categories**

1. **Unit Tests** (`@pytest.mark.unit`) - Individual function testing
2. **Integration Tests** (`@pytest.mark.integration`) - Cross-module testing
3. **FastMCP Tests** - Server and tool registration testing
4. **HTTP API Tests** - FastAPI endpoint testing
5. **Performance Tests** - Load and response time testing

## 📦 **Deployment Patterns**

### **Docker Configuration**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for your domain
RUN apt-get update && apt-get install -y \
    build-essential \
    # Add domain-specific system packages
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml .
RUN pip install -e .

# Copy application code
COPY . .

# Expose ports
EXPOSE 8080

# Command to run
CMD ["your-specialty-mcp"]
```

### **GitHub Actions CI/CD**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
        test-type: [unit, integration]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e .[dev]
    
    - name: Run tests
      run: |
        pytest -m ${{ matrix.test-type }} --cov=your_specialty_mcp
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 🔧 **Configuration Standards**

### **Environment Variables**

```bash
# Development
UVICORN_HOST=localhost
UVICORN_PORT=8080
UVICORN_RELOAD=true
UVICORN_LOG_LEVEL=debug

# Production
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8080
UVICORN_WORKERS=4
CORS_ORIGINS=https://yourdomain.com

# Domain-specific settings
DOMAIN_LIBRARY_PATH=/opt/domain-lib
DOMAIN_CONFIG_FILE=/etc/domain/config.yaml
DOMAIN_CACHE_SIZE=1000
```

### **Logging Configuration**

```python
# logging_config.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('your_specialty_mcp.log')
        ]
    )
    
    # Domain-specific logger
    domain_logger = logging.getLogger('your_specialty_mcp.domain')
    domain_logger.setLevel(logging.DEBUG)
```

## 📚 **Documentation Standards**

### **Required Documentation Files**

1. **README.md** - Comprehensive project overview
2. **API.md** - Complete API reference
3. **ARCHITECTURE.md** - System design documentation
4. **DEPLOYMENT.md** - Deployment and operations guide
5. **CONTRIBUTING.md** - Development and contribution guidelines
6. **CHANGELOG.md** - Version history and changes
7. **RELEASE_NOTES_vX.X.X.md** - Release-specific documentation

### **Code Documentation Standards**

```python
def domain_operation(
    input_data: str,
    processing_mode: Literal["fast", "accurate"] = "accurate",
    options: dict | None = None
) -> str:
    """Perform domain-specific operation with specified parameters.
    
    This function processes input data according to domain-specific algorithms
    and returns formatted results. The processing mode affects speed vs accuracy
    trade-offs in the calculations.
    
    Args:
        input_data: Primary input parameter for the operation. Should be
            formatted according to domain specifications.
        processing_mode: Processing mode selection:
            - "fast": Quick processing with reduced accuracy
            - "accurate": Full processing with maximum accuracy
        options: Optional processing parameters as key-value pairs.
            Common options include:
            - "precision": int (default=6) - decimal precision
            - "validation": bool (default=True) - input validation
            
    Returns:
        JSON string containing:
        - result: Main calculation results
        - metadata: Processing information and statistics
        - processing_time_ms: Execution time in milliseconds
        
    Raises:
        DomainError: If domain-specific processing fails
        ValueError: If input parameters are invalid
        
    Examples:
        >>> result = domain_operation("sample_input", "fast")
        >>> print(result)
        {"result": {...}, "metadata": {...}, "processing_time_ms": 45.2}
        
        >>> result = domain_operation(
        ...     "complex_input", 
        ...     "accurate", 
        ...     {"precision": 8, "validation": True}
        ... )
    
    Note:
        This function requires [domain library] for advanced calculations.
        Install with: pip install domain-library
    """
```

## 🚀 **Performance Optimization**

### **Caching Strategy**

```python
from functools import lru_cache
from typing import Any, Dict
import time

# In-memory caching for expensive operations
@lru_cache(maxsize=1000)
def cached_domain_calculation(input_hash: str, mode: str) -> Any:
    """Cached version of expensive domain calculations."""
    return expensive_domain_operation(input_hash, mode)

# Time-based cache invalidation
class TimedCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Any:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())
```

### **Async Processing**

```python
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor

async def batch_process_requests(requests: List[DomainRequest]) -> List[DomainResponse]:
    """Process multiple requests concurrently."""
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [
            loop.run_in_executor(executor, process_domain_request, request)
            for request in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
    return [r for r in results if not isinstance(r, Exception)]
```

## 🔒 **Security Considerations**

### **Input Validation**

```python
from pydantic import BaseModel, validator, Field
from typing import List, Any

class SecureDomainRequest(BaseModel):
    """Request model with security validations."""
    
    input_data: str = Field(..., min_length=1, max_length=10000)
    numeric_param: float = Field(ge=0, le=1000000)
    options: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('input_data')
    def validate_input_data(cls, v):
        # Add domain-specific input validation
        if any(char in v for char in ['<', '>', '&', '"', "'"]):
            raise ValueError("Input contains potentially unsafe characters")
        return v
    
    @validator('options')
    def validate_options(cls, v):
        # Limit options to prevent injection attacks
        allowed_keys = {'precision', 'mode', 'timeout', 'format'}
        if not set(v.keys()).issubset(allowed_keys):
            raise ValueError(f"Only these option keys are allowed: {allowed_keys}")
        return v
```

### **Rate Limiting**

```python
from fastapi import HTTPException, Request
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] 
            if req_time > minute_ago
        ]
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        self.requests[client_id].append(now)
        return True

# Usage in FastAPI
rate_limiter = RateLimiter(requests_per_minute=100)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    response = await call_next(request)
    return response
```

## 📈 **Monitoring and Observability**

### **Metrics Collection**

```python
import time
from functools import wraps
from typing import Dict, Any
import logging

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_by_tool': defaultdict(int),
            'processing_times': [],
            'errors_total': 0,
            'errors_by_type': defaultdict(int),
        }
    
    def record_request(self, tool_name: str, processing_time: float):
        self.metrics['requests_total'] += 1
        self.metrics['requests_by_tool'][tool_name] += 1
        self.metrics['processing_times'].append(processing_time)
    
    def record_error(self, error_type: str):
        self.metrics['errors_total'] += 1
        self.metrics['errors_by_type'][error_type] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        avg_processing_time = (
            sum(self.metrics['processing_times']) / len(self.metrics['processing_times'])
            if self.metrics['processing_times'] else 0
        )
        
        return {
            **self.metrics,
            'avg_processing_time_ms': avg_processing_time,
            'error_rate': self.metrics['errors_total'] / max(self.metrics['requests_total'], 1)
        }

# Global metrics collector
metrics = MetricsCollector()

def track_metrics(tool_name: str):
    """Decorator to track tool metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                processing_time = (time.time() - start_time) * 1000
                metrics.record_request(tool_name, processing_time)
                return result
            except Exception as e:
                metrics.record_error(type(e).__name__)
                raise
        return wrapper
    return decorator
```

## 🔄 **Version Management**

### **Semantic Versioning**

Follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes to APIs or tool interfaces
- **MINOR**: New features, new tools, backward-compatible changes
- **PATCH**: Bug fixes, documentation updates, performance improvements

### **Migration Guides**

```python
# migrations/v0_1_0_to_v0_2_0.py
"""Migration guide from v0.1.0 to v0.2.0."""

def migrate_tool_parameters():
    """
    Tool parameter changes in v0.2.0:
    
    OLD (v0.1.0):
        primary_operation(input_data, mode, opts)
    
    NEW (v0.2.0):
        primary_operation(input_data, processing_mode, options)
    
    The 'mode' parameter has been renamed to 'processing_mode'
    and 'opts' has been renamed to 'options' for consistency.
    """
    pass

def migrate_response_format():
    """
    Response format changes in v0.2.0:
    
    OLD: Returns plain text
    NEW: Returns JSON with metadata
    
    Update your client code to parse JSON responses.
    """
    pass
```

## 🎯 **Best Practices Summary**

### **Development**
1. **Follow the modular architecture** with domain-specific tool groupings
2. **Use type hints everywhere** for automatic schema generation
3. **Implement comprehensive error handling** with domain-specific exceptions
4. **Write extensive tests** covering unit, integration, and performance scenarios
5. **Document everything** with clear docstrings and examples

### **Deployment**
1. **Use environment variables** for configuration
2. **Implement proper logging** with structured formats
3. **Add health checks** and monitoring endpoints
4. **Use containers** for consistent deployment
5. **Plan for scaling** with stateless design

### **Maintenance**
1. **Follow semantic versioning** for releases
2. **Maintain comprehensive changelogs** 
3. **Provide migration guides** for breaking changes
4. **Monitor performance metrics** and user feedback
5. **Keep dependencies updated** with security patches

---

This standard provides a comprehensive framework for building high-quality, production-ready MCP servers using FastMCP. Adapt the patterns to your specific domain while maintaining the core architectural principles.

**Happy building! 🚀**