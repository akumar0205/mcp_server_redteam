from __future__ import annotations

import re
from typing import Any

import httpx
from fastapi import FastAPI

from mcp_redteam.mcp.protocol import ChatRequest, ChatResponse, ToolCatalog, ToolTrace

app = FastAPI(title="Demo MCP Agent Server")

KEYWORDS = {
    "weather": "get_weather",
    "status": "get_status",
    "email": "send_email",
    "export": "export_data",
    "summarize": "summarize_log",
}


async def fetch_tools(client: httpx.AsyncClient, base_url: str) -> ToolCatalog:
    response = await client.get(f"{base_url.rstrip('/')}/tools")
    response.raise_for_status()
    return ToolCatalog.model_validate(response.json())


async def call_tool(client: httpx.AsyncClient, base_url: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(
        f"{base_url.rstrip('/')}/call",
        json={"tool": tool, "args": args},
    )
    response.raise_for_status()
    payload = response.json()
    return payload


def decide_tool(prompt: str, tools: list[str]) -> list[tuple[str, dict[str, Any]]]:
    prompt_lower = prompt.lower()
    decided: list[tuple[str, dict[str, Any]]] = []
    for keyword, tool_name in KEYWORDS.items():
        if keyword in prompt_lower and tool_name in tools:
            args: dict[str, Any] = {}
            if tool_name == "get_weather":
                match = re.search(r"in ([A-Za-z ]+)", prompt)
                args["city"] = match.group(1).strip() if match else "Seattle"
            elif tool_name == "send_email":
                args = {"to": "security@example.com", "subject": "Report", "body": prompt}
            elif tool_name == "export_data":
                args = {"destination": "https://example.com/export"}
            elif tool_name == "summarize_log":
                args = {"lines": 50}
            decided.append((tool_name, args))
    return decided


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    tool_calls: list[ToolTrace] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        tool_map: dict[str, str] = {}
        for url in request.tool_server_urls:
            catalog = await fetch_tools(client, url)
            for tool in catalog.tools:
                tool_map.setdefault(tool.name, url)
        plan = decide_tool(request.user_prompt, list(tool_map.keys()))
        for tool_name, args in plan:
            url = tool_map.get(tool_name)
            if not url:
                continue
            result = await call_tool(client, url, tool_name, args)
            tool_calls.append(
                ToolTrace(
                    tool=tool_name,
                    args=args,
                    output=result.get("output", ""),
                    structured=result.get("structured"),
                )
            )

    summary_lines = ["Assistant response:"]
    summary_lines.append(request.user_prompt)
    if tool_calls:
        summary_lines.append("\nTool outputs:")
        for trace in tool_calls:
            summary_lines.append(f"- {trace.tool}: {trace.output}")
    else:
        summary_lines.append("\nNo tool calls were made.")
    return ChatResponse(assistant_response="\n".join(summary_lines), tool_calls=tool_calls)
