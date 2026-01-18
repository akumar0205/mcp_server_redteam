from __future__ import annotations

from typing import Any

import httpx

from mcp_redteam.config import AuthConfig, auth_headers
from mcp_redteam.mcp.protocol import ToolCatalog, ToolResult


class MCPHttpClient:
    def __init__(self, base_url: str, auth: AuthConfig, timeout_s: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = httpx.Timeout(timeout_s)

    async def get_tools(self) -> ToolCatalog:
        headers = auth_headers(self.auth)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/tools", headers=headers)
            response.raise_for_status()
            return ToolCatalog.model_validate(response.json())

    async def call_tool(self, tool: str, args: dict[str, Any]) -> ToolResult:
        headers = auth_headers(self.auth)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/call",
                json={"tool": tool, "args": args},
                headers=headers,
            )
            response.raise_for_status()
            return ToolResult.model_validate(response.json())
