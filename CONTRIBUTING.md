# Contributing to FEMA USAR MCP

Thank you for your interest in contributing to the Federal Urban Search and Rescue (USAR) MCP server! This project provides critical tools for emergency response operations, and we welcome contributions that enhance operational effectiveness and safety.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of FEMA USAR operations (helpful but not required)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/mcp-fema-usar.git
   cd mcp-fema-usar
   ```

2. **Set up development environment**
   ```bash
   # Install with development dependencies
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Verify installation**
   ```bash
   # Run tests
   pytest
   
   # Check code quality
   ruff check .
   ruff format --check .
   mypy .
   ```

## 🛠️ Development Workflow

### Code Style and Standards

We maintain strict code quality standards for reliability in emergency response scenarios:

- **Python**: 3.11+ with type hints required
- **Formatting**: Ruff with 88 character line limit
- **Linting**: Ruff with comprehensive rule set
- **Type checking**: MyPy with strict settings
- **Testing**: pytest with >90% coverage requirement

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write code following our standards**
   - Add type hints to all functions
   - Include comprehensive docstrings
   - Follow existing patterns and conventions
   - Ensure security best practices

3. **Add tests**
   ```bash
   # Unit tests
   pytest tests/unit/
   
   # Integration tests
   pytest tests/integration/
   
   # Field simulation tests (for operational tools)
   pytest -m simulation
   ```

4. **Run quality checks**
   ```bash
   # Format code
   ruff format .
   
   # Check linting
   ruff check .
   
   # Type check
   mypy .
   
   # Run all tests
   pytest
   ```

### Commit Guidelines

Follow conventional commits for clear change tracking:

```
feat: add new search grid optimization tool
fix: resolve triage capacity calculation error  
docs: update API documentation for medical tools
style: apply ruff formatting to rescue module
test: add integration tests for logistics tools
refactor: simplify personnel accountability logic
```

## 🧪 Testing

### Test Categories

- **Unit tests**: Individual function testing
- **Integration tests**: Tool interaction testing  
- **Simulation tests**: Field operation scenario testing
- **Performance tests**: Load and response time testing

### Running Tests

```bash
# All tests
pytest

# Specific categories
pytest -m unit
pytest -m integration
pytest -m simulation

# With coverage
pytest --cov=fema_usar_mcp --cov-report=html
```

### Test Requirements

- All new tools must have unit tests
- Integration tests for tool interactions
- Simulation tests for operational scenarios
- Maintain >90% test coverage

## 📝 Documentation

### Code Documentation

- **Docstrings**: Required for all public functions
- **Type hints**: Required for all parameters and returns
- **Examples**: Include usage examples in docstrings
- **Error handling**: Document expected exceptions

### Tool Documentation

When adding new tools, include:

```python
def new_operational_tool(
    parameter: str,
    optional_param: bool = False,
) -> str:
    """Brief description of the tool's purpose.
    
    Detailed explanation of what the tool does, when it's used,
    and how it fits into USAR operations.
    
    Args:
        parameter: Description of required parameter
        optional_param: Description of optional parameter
        
    Returns:
        JSON string with operational data and recommendations
        
    Raises:
        ValueError: When parameter validation fails
        
    Example:
        >>> result = new_operational_tool("search_area_alpha")
        >>> data = json.loads(result)
        >>> print(data["status"])
        success
    """
```

## 🔧 Tool Development Guidelines

### Tool Categories

Tools are organized by USAR functional groups:

- **Command**: Leadership and coordination tools
- **Search**: Victim location and assessment tools  
- **Rescue**: Extraction and recovery tools
- **Medical**: Patient care and triage tools
- **Planning**: Situational awareness and resource planning
- **Logistics**: Supply and equipment management
- **Technical**: Specialized assessment tools

### Security Considerations

This project supports critical emergency response operations:

- **No sensitive data in code**: Never commit credentials or keys
- **Input validation**: Validate all parameters thoroughly
- **Error handling**: Fail safely with informative messages
- **Audit logging**: Log operational decisions and actions

### Performance Requirements

- **Response time**: <200ms for critical operational tools
- **Offline capability**: Tools must work without network connectivity
- **Memory efficiency**: Optimize for resource-constrained field environments
- **Battery awareness**: Consider power consumption in mobile deployments

## 🎯 Contributing Areas

### High Priority

- **Field simulation accuracy**: Improve operational scenario modeling
- **Integration testing**: Expand tool interaction coverage
- **Performance optimization**: Reduce response times
- **Offline capabilities**: Enhance disconnected operation support

### Tool Enhancement Opportunities

- **Search optimization**: Advanced grid search algorithms
- **Resource prediction**: ML-based resource requirement forecasting
- **Communication integration**: Multi-band radio and satellite support
- **GIS integration**: Enhanced mapping and geospatial tools

### Documentation Needs

- **Operational guides**: Tool usage in field scenarios
- **Integration examples**: MCP client implementation examples
- **Performance tuning**: Optimization guidelines
- **Deployment guides**: Production deployment documentation

## 📋 Pull Request Process

1. **Ensure all checks pass**
   - GitHub Actions CI must be green
   - All tests passing
   - Code coverage maintained
   - No linting or type errors

2. **Provide clear description**
   - What changes were made
   - Why the changes were necessary
   - How the changes were tested
   - Any operational impact

3. **Request appropriate reviews**
   - Code changes: 2 reviewer minimum
   - Operational tools: Subject matter expert review
   - Security changes: Security review required

4. **Address feedback promptly**
   - Respond to review comments
   - Make requested changes
   - Re-request review when ready

## 🚨 Security and Safety

### Security Guidelines

- **Vulnerability reporting**: Use GitHub Security Advisories
- **Dependency management**: Keep dependencies updated
- **Code scanning**: Automated security scans required
- **Access control**: Principle of least privilege

### Operational Safety

Remember that this code supports life-safety operations:

- **Thorough testing**: Test extensively before merging
- **Graceful degradation**: Handle failures safely
- **Clear error messages**: Help operators understand issues
- **Rollback capability**: Ensure changes can be reverted quickly

## 📞 Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Documentation**: Check existing docs first
- **Code Examples**: Review existing tool implementations

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors are recognized in:
- Repository contributors page
- Release notes for significant contributions  
- Annual contributor appreciation

Thank you for helping improve emergency response capabilities through technology!