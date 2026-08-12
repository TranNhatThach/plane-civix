import inspect
import logging
from typing import Dict, Any, Callable, List, Optional

logger = logging.getLogger(__name__)


class AgentTool:
    """
    Metadata wrapper for an AI Agent Tool function.
    """
    def __init__(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters_schema: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.func = func
        self.description = description
        self.parameters_schema = parameters_schema or {}

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert tool metadata to OpenAI Function Tool Schema format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }


class ToolRegistry:
    """
    Central Registry for all Plane AI Agent tools.
    Provides registration, lookup, execution, and automatic OpenAI schema generation.
    """
    _registry: Dict[str, AgentTool] = {}

    @classmethod
    def register(
        cls,
        name: str,
        description: str,
        parameters_schema: Optional[Dict[str, Any]] = None
    ):
        """Decorator to register a tool function into the registry."""
        def decorator(func: Callable):
            tool = AgentTool(
                name=name,
                func=func,
                description=description,
                parameters_schema=parameters_schema
            )
            cls._registry[name] = tool
            return func
        return decorator

    @classmethod
    def get_tool(cls, name: str) -> Optional[AgentTool]:
        """Retrieve registered tool by name."""
        return cls._registry.get(name)

    @classmethod
    def get_tools_map(cls) -> Dict[str, Callable]:
        """Get dictionary mapping tool names to python callable functions."""
        return {name: tool.func for name, tool in cls._registry.items()}

    @classmethod
    def get_openai_schemas(cls) -> List[Dict[str, Any]]:
        """Generate OpenAI tools schema array for all registered tools."""
        return [tool.to_openai_schema() for tool in cls._registry.values()]


# Shortcut decorator alias
agent_tool = ToolRegistry.register
