"""Tool registry for latent loading of FEMA USAR MCP tools.

This module provides a lightweight registry system that stores tool metadata
without importing the actual tool implementations. Tools are loaded on-demand
when their schema is requested or when they are executed.
"""

import importlib
import inspect
import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FunctionalGroup(Enum):
    """USAR functional groups for tool categorization."""

    COMMAND = "command"
    SEARCH = "search"
    RESCUE = "rescue"
    MEDICAL = "medical"
    PLANNING = "planning"
    LOGISTICS = "logistics"
    TECHNICAL = "technical"
    DECISION_SUPPORT = "decision_support"
    SYSTEM = "system"


@dataclass
class ToolMetadata:
    """Lightweight metadata for a USAR tool without importing implementation."""

    name: str
    category: FunctionalGroup
    description: str  # Short summary (<100 chars)
    module_path: str  # e.g., "fema_usar_mcp.tools.command"
    function_name: str
    key_parameters: list[str] = field(default_factory=list)
    cache_ttl: int = 300  # Default 5 minutes
    requires_auth: bool = False
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "module_path": self.module_path,
            "function_name": self.function_name,
            "key_parameters": self.key_parameters,
            "cache_ttl": self.cache_ttl,
            "requires_auth": self.requires_auth,
            "tags": self.tags,
        }


@dataclass
class CachedSchema:
    """Cached tool schema with TTL."""

    schema: dict[str, Any]
    timestamp: float
    ttl: float = 1800.0  # 30 minutes default


class ToolRegistry:
    """Registry for managing tool metadata and lazy loading.

    The registry stores lightweight metadata about all available tools
    without importing them. Tools are loaded on-demand when:
    - Their full schema is requested
    - They are executed

    This reduces initial token consumption from ~122,800 to ~5,200.
    """

    def __init__(self, schema_cache_ttl: float = 1800.0):
        """Initialize the tool registry.

        Args:
            schema_cache_ttl: TTL for cached schemas in seconds (default 30 min)
        """
        self._metadata: dict[str, ToolMetadata] = {}
        self._loaded_functions: dict[str, Callable] = {}
        self._schema_cache: dict[str, CachedSchema] = {}
        self._schema_cache_ttl = schema_cache_ttl
        self._lock = threading.RLock()
        self._load_count = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def register_metadata(self, metadata: ToolMetadata) -> None:
        """Register lightweight metadata for a tool.

        Args:
            metadata: Tool metadata without importing implementation
        """
        with self._lock:
            self._metadata[metadata.name] = metadata
            logger.debug(f"Registered tool metadata: {metadata.name}")

    def register_all_metadata(self, metadata_list: list[ToolMetadata]) -> None:
        """Register multiple tool metadata entries at once.

        Args:
            metadata_list: List of tool metadata entries
        """
        with self._lock:
            for metadata in metadata_list:
                self._metadata[metadata.name] = metadata
            logger.info(f"Registered {len(metadata_list)} tool metadata entries")

    def get_all_metadata(self) -> dict[str, ToolMetadata]:
        """Get all registered tool metadata."""
        with self._lock:
            return self._metadata.copy()

    def get_metadata(self, tool_name: str) -> ToolMetadata | None:
        """Get metadata for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            ToolMetadata or None if not found
        """
        with self._lock:
            return self._metadata.get(tool_name)

    def get_categories(self) -> dict[str, dict[str, Any]]:
        """Get category summary with tool counts.

        Returns:
            Dictionary of categories with counts and descriptions
        """
        with self._lock:
            categories: dict[str, dict[str, Any]] = {}
            for metadata in self._metadata.values():
                category = metadata.category.value
                if category not in categories:
                    categories[category] = {
                        "count": 0,
                        "tools": [],
                        "description": self._get_category_description(
                            metadata.category
                        ),
                    }
                categories[category]["count"] += 1
                categories[category]["tools"].append(
                    {"name": metadata.name, "description": metadata.description}
                )
            return categories

    def get_tools_by_category(
        self, category: str | FunctionalGroup
    ) -> list[ToolMetadata]:
        """Get all tools in a specific category.

        Args:
            category: Category name or FunctionalGroup enum

        Returns:
            List of tool metadata in the category
        """
        if isinstance(category, str):
            try:
                category = FunctionalGroup(category)
            except ValueError:
                return []

        with self._lock:
            return [
                metadata
                for metadata in self._metadata.values()
                if metadata.category == category
            ]

    def list_tools(
        self, category: str = "all", include_parameters: bool = False
    ) -> list[dict[str, Any]]:
        """List tools with optional parameter preview.

        Args:
            category: Filter by category (default "all")
            include_parameters: Include key parameters in output

        Returns:
            List of tool summaries
        """
        with self._lock:
            tools = []
            for metadata in self._metadata.values():
                if category != "all" and metadata.category.value != category:
                    continue

                tool_info = {
                    "name": metadata.name,
                    "category": metadata.category.value,
                    "description": metadata.description,
                }

                if include_parameters:
                    tool_info["key_parameters"] = metadata.key_parameters

                tools.append(tool_info)

            return sorted(tools, key=lambda x: (x["category"], x["name"]))

    def load_tool_function(self, tool_name: str) -> Callable | None:
        """Dynamically import and return a tool function.

        Args:
            tool_name: Name of the tool to load

        Returns:
            The tool function or None if not found
        """
        with self._lock:
            # Return cached function if available
            if tool_name in self._loaded_functions:
                return self._loaded_functions[tool_name]

            # Get metadata
            metadata = self._metadata.get(tool_name)
            if not metadata:
                logger.warning(f"Tool not found in registry: {tool_name}")
                return None

            try:
                # Dynamic import
                module = importlib.import_module(metadata.module_path)
                func = getattr(module, metadata.function_name)

                # Handle FastMCP FunctionTool wrapper
                # FunctionTool objects have the actual function in .fn attribute
                if hasattr(func, "fn") and callable(func.fn):
                    func = func.fn

                # Cache the loaded function
                self._loaded_functions[tool_name] = func
                self._load_count += 1
                logger.info(f"Loaded tool function: {tool_name}")

                return func

            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to load tool {tool_name}: {e}")
                return None

    def load_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """Load full schema for a specific tool on demand.

        Args:
            tool_name: Name of the tool

        Returns:
            Full JSON schema for the tool or None if not found
        """
        with self._lock:
            # Check schema cache
            if tool_name in self._schema_cache:
                cached = self._schema_cache[tool_name]
                if time.time() - cached.timestamp < cached.ttl:
                    self._cache_hits += 1
                    return cached.schema
                else:
                    del self._schema_cache[tool_name]

            self._cache_misses += 1

            # Load function to extract schema
            func = self.load_tool_function(tool_name)
            if not func:
                return None

            # Extract schema from function signature and docstring
            schema = self._extract_schema(func, tool_name)

            # Cache the schema
            self._schema_cache[tool_name] = CachedSchema(
                schema=schema, timestamp=time.time(), ttl=self._schema_cache_ttl
            )

            return schema

    def execute_tool(
        self, tool_name: str, parameters: dict[str, Any] | None = None
    ) -> str:
        """Execute a tool by name with the given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Dictionary of parameters to pass to the tool

        Returns:
            Tool execution result as JSON string
        """
        if parameters is None:
            parameters = {}

        func = self.load_tool_function(tool_name)
        if not func:
            return json.dumps(
                {
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": list(self._metadata.keys()),
                },
                indent=2,
            )

        try:
            result = func(**parameters)
            return result
        except TypeError as e:
            return json.dumps(
                {
                    "error": f"Invalid parameters for tool '{tool_name}'",
                    "details": str(e),
                    "expected_parameters": self.get_metadata(tool_name).key_parameters
                    if self.get_metadata(tool_name)
                    else [],
                },
                indent=2,
            )
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return json.dumps(
                {"error": f"Tool execution failed: {str(e)}", "tool": tool_name},
                indent=2,
            )

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        with self._lock:
            return {
                "total_tools_registered": len(self._metadata),
                "tools_loaded": len(self._loaded_functions),
                "schemas_cached": len(self._schema_cache),
                "load_count": self._load_count,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": (
                    self._cache_hits / (self._cache_hits + self._cache_misses)
                    if (self._cache_hits + self._cache_misses) > 0
                    else 0
                ),
                "categories": {
                    cat.value: len(self.get_tools_by_category(cat))
                    for cat in FunctionalGroup
                },
            }

    def clear_cache(self) -> int:
        """Clear the schema cache.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._schema_cache)
            self._schema_cache.clear()
            return count

    def _extract_schema(self, func: Callable, tool_name: str) -> dict[str, Any]:
        """Extract JSON schema from function signature and docstring.

        Args:
            func: The function to extract schema from
            tool_name: Name of the tool

        Returns:
            JSON schema dictionary
        """
        sig = inspect.signature(func)
        docstring = func.__doc__ or ""

        # Parse docstring for parameter descriptions
        param_docs = self._parse_docstring_params(docstring)

        # Build parameters schema
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_schema: dict[str, Any] = {"type": "string"}  # Default type

            # Infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                param_schema = self._annotation_to_schema(param.annotation)

            # Add description from docstring
            if param_name in param_docs:
                param_schema["description"] = param_docs[param_name]

            # Add default value if present
            if param.default != inspect.Parameter.empty:
                param_schema["default"] = param.default
            else:
                required.append(param_name)

            properties[param_name] = param_schema

        # Extract first line of docstring as description
        description = docstring.split("\n")[0].strip() if docstring else ""

        return {
            "name": tool_name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def _parse_docstring_params(self, docstring: str) -> dict[str, str]:
        """Parse parameter descriptions from docstring.

        Args:
            docstring: Function docstring

        Returns:
            Dictionary mapping parameter names to descriptions
        """
        params = {}
        in_args = False
        current_param = None
        current_desc = []

        for line in docstring.split("\n"):
            line = line.strip()

            if line.startswith("Args:"):
                in_args = True
                continue
            elif line.startswith("Returns:") or line.startswith("Raises:"):
                if current_param:
                    params[current_param] = " ".join(current_desc).strip()
                break
            elif in_args:
                if ":" in line and not line.startswith(" "):
                    # Save previous param
                    if current_param:
                        params[current_param] = " ".join(current_desc).strip()

                    # Parse new param
                    parts = line.split(":", 1)
                    current_param = parts[0].strip()
                    current_desc = [parts[1].strip()] if len(parts) > 1 else []
                elif current_param and line:
                    current_desc.append(line)

        # Save last param
        if current_param:
            params[current_param] = " ".join(current_desc).strip()

        return params

    def _annotation_to_schema(self, annotation: Any) -> dict[str, Any]:
        """Convert Python type annotation to JSON schema.

        Args:
            annotation: Python type annotation

        Returns:
            JSON schema fragment
        """
        # Handle string annotations
        if isinstance(annotation, str):
            return {"type": "string"}

        # Handle basic types
        type_mapping = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }

        if annotation in type_mapping:
            return type_mapping[annotation]

        # Handle Optional types
        origin = getattr(annotation, "__origin__", None)
        if origin is type(None):
            return {"type": "null"}

        # Handle Union types (including Optional)
        if hasattr(annotation, "__args__"):
            args = annotation.__args__
            if type(None) in args:
                # Optional type - get the non-None type
                non_none_args = [a for a in args if a is not type(None)]
                if non_none_args:
                    return self._annotation_to_schema(non_none_args[0])

        # Handle Literal types
        if origin is type(None):
            return {"type": "null"}

        # Handle list with type args
        if origin is list:
            return {"type": "array"}

        # Handle dict with type args
        if origin is dict:
            return {"type": "object"}

        # Default to string
        return {"type": "string"}

    def _get_category_description(self, category: FunctionalGroup) -> str:
        """Get human-readable description for a category.

        Args:
            category: The functional group

        Returns:
            Description string
        """
        descriptions = {
            FunctionalGroup.COMMAND: "Task Force leadership, safety monitoring, and personnel accountability tools",
            FunctionalGroup.SEARCH: "Victim location tracking, search patterns, and technical search equipment",
            FunctionalGroup.RESCUE: "Squad operations, victim extraction, structural stabilization, and heavy equipment",
            FunctionalGroup.MEDICAL: "Patient care, medical supplies, triage coordination, and health surveillance",
            FunctionalGroup.PLANNING: "Situational awareness, resource tracking, and documentation automation",
            FunctionalGroup.LOGISTICS: "Supply chain, facilities, ground support, and maintenance scheduling",
            FunctionalGroup.TECHNICAL: "Structural assessment, hazmat monitoring, communications, and rigging",
            FunctionalGroup.DECISION_SUPPORT: "AI-powered tactical, strategic, and operational intelligence",
            FunctionalGroup.SYSTEM: "Performance monitoring, cache management, and system status",
        }
        return descriptions.get(category, "USAR operational tools")


# Global registry instance
_registry: ToolRegistry | None = None
_registry_lock = threading.Lock()


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry.

    Returns:
        The global ToolRegistry instance
    """
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = ToolRegistry()
        return _registry


def initialize_registry() -> ToolRegistry:
    """Initialize the registry with all tool metadata.

    Returns:
        The initialized ToolRegistry
    """
    from .tool_metadata import get_all_tool_metadata

    registry = get_registry()
    metadata_list = get_all_tool_metadata()
    registry.register_all_metadata(metadata_list)
    return registry
