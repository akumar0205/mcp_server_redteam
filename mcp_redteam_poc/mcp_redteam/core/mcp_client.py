from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any

from .transport_base import Transport, TransportResponse


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class Resource:
    uri: str
    description: str


@dataclass
class Prompt:
    name: str
    description: str


@dataclass
class MCPResponse:
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    latency_ms: float
    request_id: int


class MCPClient:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._ids = itertools.count(1)
        self.protocol_version = "2024-11-05"

    def send_request(self, method: str, params: dict[str, Any] | None, timeout: float) -> MCPResponse:
        request_id = next(self._ids)
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        response: TransportResponse = self._transport.send(message, timeout=timeout)
        payload = response.payload
        return MCPResponse(
            result=payload.get("result"),
            error=payload.get("error"),
            latency_ms=response.latency_ms,
            request_id=request_id,
        )

    def initialize(self, timeout: float) -> MCPResponse:
        return self.send_request(
            "initialize",
            {"protocolVersion": self.protocol_version, "capabilities": {}},
            timeout=timeout,
        )

    def list_tools(self, timeout: float) -> tuple[MCPResponse, list[Tool]]:
        response = self.send_request("listTools", {}, timeout=timeout)
        tools: list[Tool] = []
        if response.result:
            for item in response.result.get("tools", []):
                tools.append(
                    Tool(
                        name=item.get("name", ""),
                        description=item.get("description", ""),
                        input_schema=item.get("inputSchema", {}),
                    )
                )
        return response, tools

    def list_resources(self, timeout: float) -> tuple[MCPResponse, list[Resource]]:
        response = self.send_request("listResources", {}, timeout=timeout)
        resources: list[Resource] = []
        if response.result:
            for item in response.result.get("resources", []):
                resources.append(
                    Resource(
                        uri=item.get("uri", ""),
                        description=item.get("description", ""),
                    )
                )
        return response, resources

    def list_prompts(self, timeout: float) -> tuple[MCPResponse, list[Prompt]]:
        response = self.send_request("listPrompts", {}, timeout=timeout)
        prompts: list[Prompt] = []
        if response.result:
            for item in response.result.get("prompts", []):
                prompts.append(
                    Prompt(
                        name=item.get("name", ""),
                        description=item.get("description", ""),
                    )
                )
        return response, prompts

    def call_tool(self, name: str, args: dict[str, Any], timeout: float) -> MCPResponse:
        return self.send_request("callTool", {"name": name, "arguments": args}, timeout=timeout)

    def close(self) -> None:
        self._transport.close()
