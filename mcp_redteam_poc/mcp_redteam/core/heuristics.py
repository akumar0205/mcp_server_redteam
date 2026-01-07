from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .mcp_client import Tool


RISK_KEYWORDS = {
    "exec": 5,
    "run": 5,
    "shell": 5,
    "cmd": 5,
    "eval": 5,
    "read": 3,
    "write": 3,
    "file": 3,
    "fetch": 4,
    "http": 4,
    "url": 4,
    "sql": 4,
    "query": 3,
    "template": 2,
    "regex": 2,
}

PARAM_KEYWORDS = {
    "path": 3,
    "cmd": 4,
    "command": 4,
    "url": 4,
    "query": 3,
    "headers": 2,
    "template": 2,
    "regex": 2,
    "filename": 3,
    "file": 3,
}


@dataclass
class ToolRisk:
    tool: Tool
    score: int


def _extract_param_names(schema: dict[str, Any]) -> list[str]:
    props = schema.get("properties", {})
    if isinstance(props, dict):
        return [str(name) for name in props.keys()]
    return []


def score_tool(tool: Tool) -> ToolRisk:
    score = 0
    lower_name = tool.name.lower()
    lower_desc = tool.description.lower()
    for keyword, weight in RISK_KEYWORDS.items():
        if keyword in lower_name or keyword in lower_desc:
            score += weight
    for param in _extract_param_names(tool.input_schema):
        lower_param = param.lower()
        for keyword, weight in PARAM_KEYWORDS.items():
            if keyword in lower_param:
                score += weight
    return ToolRisk(tool=tool, score=score)


def rank_tools(tools: list[Tool]) -> list[ToolRisk]:
    risks = [score_tool(tool) for tool in tools]
    return sorted(risks, key=lambda item: item.score, reverse=True)
