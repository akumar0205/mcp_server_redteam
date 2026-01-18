from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from mcp_redteam.mcp.protocol import ToolDefinition, ToolResult

ToolHandler = Callable[[dict[str, Any]], Awaitable[ToolResult]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolDefinition, ToolHandler]] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        self._tools[definition.name] = (definition, handler)

    def list_tools(self) -> list[ToolDefinition]:
        return [definition for definition, _handler in self._tools.values()]

    async def call(self, tool: str, args: dict[str, Any]) -> ToolResult:
        if tool not in self._tools:
            raise KeyError(f"Unknown tool: {tool}")
        definition, handler = self._tools[tool]
        return await handler(args)
