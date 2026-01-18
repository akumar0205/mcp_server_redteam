from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)


class ToolCatalog(BaseModel):
    tools: list[ToolDefinition]


class ToolCall(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    output: str
    structured: Optional[dict[str, Any]] = None


class ChatRequest(BaseModel):
    system_policy: str
    user_prompt: str
    tool_server_urls: list[str] = Field(default_factory=list)


class ToolTrace(BaseModel):
    tool: str
    args: dict[str, Any]
    output: str
    structured: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    assistant_response: str
    tool_calls: list[ToolTrace] = Field(default_factory=list)
