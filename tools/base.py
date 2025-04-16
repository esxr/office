from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from logging_config import get_logger


class BaseTool(ABC):
    """Base class for all tools that can be used by agents."""

    name: str
    description: str

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = get_logger(f"tool.{name}")
        self.logger.debug(f"Initialized {name} tool")

    @abstractmethod
    async def _run(self, **kwargs) -> Any:
        """Run the tool with the given kwargs."""
        pass

    async def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool and return a formatted response."""
        self.logger.info(f"Running tool {self.name} with params: {kwargs}")
        try:
            result = await self._run(**kwargs)
            self.logger.debug(f"Tool {self.name} completed successfully")
            return {"tool_name": self.name, "result": result}
        except Exception as e:
            self.logger.error(f"Error executing tool {self.name}: {str(e)}")
            # Don't catch errors, just log them and re-raise
            raise

    def get_schema(self) -> Dict[str, Any]:
        """Return the schema for this tool."""
        self.logger.debug(f"Getting schema for tool {self.name}")
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema(),
        }

    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Return the parameters schema for this tool."""
        pass
