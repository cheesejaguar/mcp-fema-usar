# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the FEMA USAR MCP Server.

## Workflows Overview

### 🔄 `ci.yml` - Main CI Pipeline
**Triggers:** Push to main/develop, Pull Requests  
**Purpose:** Comprehensive testing and quality checks

**Jobs:**
- **Pre-check**: Fast validation of dependencies and configuration
- **Lint**: Code quality checks with ruff, black, and mypy
- **Test**: Unit and integration tests across Python 3.11 and 3.12
- **Security**: Security vulnerability scanning with bandit and safety
- **Performance**: Load and benchmark tests (main branch only)
- **Build**: Package building and validation

**Performance Optimizations:**
- ⚡ Parallel job execution
- 📦 Comprehensive caching (uv, pip, pre-commit)
- 🎯 Fail-fast on critical issues
- 🔀 Concurrency control to prevent resource conflicts

### 🚀 `deploy.yml` - Deployment Pipeline
**Triggers:** Push to main, Releases, Manual dispatch  
**Purpose:** Automated deployment to staging and production

**Features:**
- Waits for CI pipeline completion before deploying
- Multi-environment support (staging/production)
- Health checks and deployment verification
- Docker image building for releases
- Fly.io deployment integration

### 📦 `release.yml` - Release Management
**Triggers:** Git tags (v*), Manual dispatch  
**Purpose:** Automated package publishing and release creation

**Features:**
- Automatic version extraction from git tags
- PyPI package publishing
- GitHub release creation with artifacts
- Pre-release detection and handling

### 🔧 `dependency-updates.yml` - Dependency Management
**Triggers:** Weekly schedule (Mondays), Manual dispatch  
**Purpose:** Automated dependency updates and security patches

**Features:**
- Weekly dependency updates via automated PRs
- Security vulnerability detection and patching
- Automated testing of updated dependencies
- Separate security update workflow for urgent patches

## Configuration Files

### `.pre-commit-config.yaml`
Pre-commit hooks for local development:
- Code formatting (black, ruff)
- Type checking (mypy)
- Security scanning (bandit)
- Unit tests (pytest)
- YAML/JSON validation

## Usage

### Setting Up CI/CD

1. **Required Secrets:**
   ```bash
   # For PyPI publishing (optional)
   PYPI_TOKEN=<your-pypi-token>
   
   # For Docker publishing (optional)
   DOCKER_USERNAME=<docker-username>
   DOCKER_PASSWORD=<docker-password>
   
   # For Fly.io deployment
   FLY_API_TOKEN=<fly-api-token>
   ```

2. **Enable Pre-commit (recommended):**
   ```bash
   uv add --group dev pre-commit
   uv run pre-commit install
   ```

### Manual Workflow Triggers

- **Deploy to Staging:** Go to Actions → Deploy → Run workflow
- **Create Release:** Create and push a git tag: `git tag v1.0.0 && git push origin v1.0.0`
- **Update Dependencies:** Go to Actions → Dependency Updates → Run workflow

### Monitoring

- **CI Status:** Check the status badge in README.md
- **Test Coverage:** Coverage reports uploaded to Codecov
- **Security Alerts:** Automatically created PRs for security issues
- **Performance:** Benchmark results stored as artifacts

## Performance Metrics

The CI pipeline is optimized for speed:
- **Cold start:** ~3-5 minutes (with cache misses)
- **Warm start:** ~1-2 minutes (with cache hits)
- **Full pipeline:** ~8-12 minutes (including all matrix jobs)

## Troubleshooting

### Common Issues

1. **Cache Issues:** If builds are slow, check if caching is working properly
2. **Test Failures:** Check the specific job logs for detailed error information
3. **Deployment Failures:** Verify health check endpoints are responding
4. **Dependency Issues:** Check for conflicts in the dependency update PRs

### Emergency Procedures

- **Skip CI:** Add `[skip ci]` to commit message (not recommended for main branch)
- **Force Deploy:** Use manual workflow dispatch with override options
- **Rollback:** Revert the problematic commit and redeploy

## Development Workflow

1. **Feature Development:**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   uv run pre-commit run --all-files  # Local validation
   git push origin feature/new-feature  # Triggers CI
   ```

2. **Pull Request:**
   - CI runs automatically on PR creation
   - All checks must pass before merge
   - Coverage reports help identify test gaps

3. **Release Process:**
   ```bash
   git checkout main
   git pull origin main
   git tag v1.0.0
   git push origin v1.0.0  # Triggers release workflow
   ```

This CI/CD setup ensures high code quality, automated testing, and reliable deployments while maintaining fast feedback loops for developers.