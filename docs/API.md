# API Reference

## MCP Tools

The Federal USAR MCP Server exposes 38+ tools via the Model Context Protocol. Tools are organized by functional group.

### Server Modes

**Eager Loading** (`fema-usar-mcp`): All tools loaded at startup.

**Latent Loading** (`fema-usar-mcp-latent`): Only meta-tools loaded; functional tools available via `usar_execute_tool`.

---

## Command Group (5 tools)

### `task_force_leader_dashboard`
Comprehensive dashboard for Task Force Leader situational awareness.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task_force_id` | `str` | `"CA-TF1"` | Task force identifier |
| `include_personnel` | `bool` | `True` | Include personnel status |
| `include_equipment` | `bool` | `True` | Include equipment status |
| `include_missions` | `bool` | `True` | Include mission assignments |

### `safety_officer_monitor`
Real-time safety monitoring and hazard tracking.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `monitoring_mode` | `str` | `"real_time"` | Monitoring mode |
| `task_force_id` | `str` | `"DEFAULT-TF"` | Task force identifier |

### `personnel_accountability`
Personnel accountability and location tracking.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `accountability_type` | `str` | `"full"` | Type of accountability check |
| `task_force_id` | `str` | `"DEFAULT-TF"` | Task force identifier |

### `mission_assignment_tracker`
Track and manage mission assignments.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task_force_id` | `str` | `"DEFAULT-TF"` | Task force identifier |

### `external_coordination`
Coordinate with external agencies and incident command.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task_force_id` | `str` | `"DEFAULT-TF"` | Task force identifier |

---

## Search Group (5 tools)

### `victim_location_tracker`
Track and document victim locations and status.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_area_id` | `str` | required | Search area identifier |
| `victim_status` | `str` | `"confirmed"` | Victim confirmation status |

### `search_pattern_planner`
Plan and monitor search patterns across operational areas.

### `technical_search_equipment`
Manage technical search equipment (Delsar, thermal imaging, etc.).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `equipment_type` | `str` | `"delsar"` | Equipment type |
| `operation_mode` | `str` | `"active"` | Operation mode |

### `canine_team_deployment`
Manage canine search team deployment and tracking.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_type` | `str` | `"live_find"` | Search type |
| `deployment_status` | `bool` | `True` | Current deployment status |

### `void_space_assessment`
Assess void spaces for victim probability analysis.

---

## Rescue Group (5 tools)

### `rescue_squad_operations`
Coordinate rescue squad tactical operations.

### `victim_extraction_planner`
Plan victim extraction procedures and resources.

### `structural_stabilization`
Track structural stabilization operations.

### `heavy_equipment_operations`
Manage heavy equipment deployment and operations.

### `debris_removal_coordinator`
Coordinate debris removal operations and progress.

---

## Medical Group (5 tools)

### `patient_care_tracker`
Track patient care and treatment documentation.

### `medical_supply_inventory`
Manage medical supply inventory and distribution.

### `triage_coordinator`
Coordinate triage operations and priority management.

### `health_surveillance`
Monitor personnel health and fitness status.

### `evacuation_coordinator`
Coordinate medical evacuation and transport logistics.

---

## Planning Group (5 tools)

### `situation_unit_dashboard`
SITL situational awareness and intelligence management.

### `resource_unit_tracker`
RESL resource inventory and tracking.

### `documentation_automation`
Automate ICS form completion and operational documentation.

### `demobilization_planner`
Plan and track demobilization procedures.

### `operational_timeline`
Track operational milestones and timeline.

---

## Logistics Group (5 tools)

### `supply_chain_manager`
Manage supply chain, inventory, and procurement.

### `facilities_coordinator`
Coordinate base camp facilities and setup.

### `ground_support_tracker`
Track vehicle fleet and ground transportation.

### `fuel_management`
Monitor fuel consumption and resupply.

### `maintenance_scheduler`
Schedule and track equipment maintenance.

---

## Technical Group (5 tools)

### `structural_assessment`
Perform structural assessment and safety evaluation.

### `hazmat_monitoring`
Monitor hazardous materials and environmental hazards.

### `communications_manager`
Manage communication systems and frequencies.

### `rigging_calculator`
Calculate rigging loads and safety factors.

### `environmental_monitor`
Monitor environmental conditions at the operations site.

---

## Decision Support Group (3 tools)

### `tactical_decision_support`
AI-driven tactical decision analysis for field operations.

### `strategic_planning_advisor`
Strategic planning recommendations and scenario analysis.

### `operational_intelligence_system`
Aggregate and analyze operational intelligence.

---

## System Tools

### `get_usar_system_status`
Get comprehensive system status and capabilities.

### `calculate_task_force_readiness`
Calculate deployment readiness for a task force.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task_force_id` | `str` | `"CA-TF1"` | Task force identifier |
| `personnel_count` | `int` | `70` | Current personnel count |
| `equipment_ready` | `int` | `16400` | Ready equipment items |
| `training_compliance` | `float` | `100.0` | Training compliance % |

### `list_functional_groups`
List all functional groups and key positions.

### `get_system_performance`
Get system performance statistics and metrics.

### `clear_system_cache`
Clear system cache entries.

### `submit_async_operation`
Submit an operation for async processing.

### `get_async_task_info`
Check async task status and results.

---

## Meta-Tools (Latent Loading)

### `usar_browse_categories`
Browse available tool categories with descriptions and counts.

### `usar_list_tools`
List tools in a category with optional parameter preview.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | `str` | `"all"` | Category filter |
| `include_parameters` | `bool` | `False` | Include parameter details |

### `usar_get_tool_schema`
Load and return the full schema for a specific tool.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool_name` | `str` | required | Tool to get schema for |

### `usar_execute_tool`
Execute any registered tool by name with JSON parameters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool_name` | `str` | required | Tool to execute |
| `parameters` | `str` | `"{}"` | JSON parameters |

### `usar_health_check`
System health and readiness check.

### `usar_metrics`
Detailed performance metrics and cache statistics.

---

## HTTP API Endpoints

Base URL: `http://localhost:8000`

### Health and Status

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | System health check |
| `GET` | `/status` | Comprehensive system status |
| `GET` | `/capabilities` | Available tools and integrations |

### USAR Operations

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/usar/status` | Get task force operational status |
| `POST` | `/usar/deploy` | Initiate task force deployment |

### ICS Forms

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ics_forms` | List available ICS forms |
| `GET` | `/ics_forms/{id}` | Get specific ICS form details |
| `GET` | `/ics_forms/{id}/content` | Download ICS form file |

### Datasets and Documents

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/datasets` | List available open datasets |
| `GET` | `/datasets/{id}` | Get specific dataset details |
| `GET` | `/documents` | List available documents |
| `GET` | `/documents/{id}` | Get specific document |
| `GET` | `/documents/{id}/content` | Download document file |

### Interactive API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
