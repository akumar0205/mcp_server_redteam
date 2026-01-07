from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.mcp_client import Tool


@dataclass
class TestCase:
    tool_name: str
    args: dict[str, Any]
    probe_name: str
    expected_signals: list[str]


def extract_param_names(tool: Tool) -> list[str]:
    props = tool.input_schema.get("properties", {})
    if isinstance(props, dict):
        return [str(name) for name in props.keys()]
    return []
