from __future__ import annotations

from fastapi import FastAPI, HTTPException

from mcp_redteam.mcp.protocol import ToolCall, ToolCatalog, ToolDefinition, ToolResult
from mcp_redteam.mcp.registry import ToolRegistry

app = FastAPI(title="Benign MCP Tool Server")
registry = ToolRegistry()


async def get_weather(args: dict[str, str]) -> ToolResult:
    city = args.get("city", "unknown")
    return ToolResult(output=f"Weather in {city}: Sunny, 72F", structured={"city": city})


async def get_status(args: dict[str, str]) -> ToolResult:
    return ToolResult(output="All systems nominal", structured={"status": "ok"})


registry.register(
    ToolDefinition(
        name="get_weather",
        description="Fetch the current weather for a city.",
        input_schema={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    ),
    get_weather,
)

registry.register(
    ToolDefinition(
        name="get_status",
        description="Return a service health status summary.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    ),
    get_status,
)


@app.get("/tools", response_model=ToolCatalog)
async def list_tools() -> ToolCatalog:
    return ToolCatalog(tools=registry.list_tools())


@app.post("/call", response_model=ToolResult)
async def call_tool(payload: ToolCall) -> ToolResult:
    try:
        return await registry.call(payload.tool, payload.args)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
