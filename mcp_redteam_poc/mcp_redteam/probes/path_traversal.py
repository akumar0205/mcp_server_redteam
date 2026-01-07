from __future__ import annotations

from typing import Any

from .base import TestCase, extract_param_names
from ..core.mcp_client import Tool


class PathTraversalProbe:
    name = "PathTraversalProbe"

    def generate(self, tool: Tool, metadata: dict[str, Any]) -> list[TestCase]:
        param_names = extract_param_names(tool)
        path_params = [p for p in param_names if "path" in p.lower() or "file" in p.lower()]
        if not path_params:
            return []
        args = {path_params[0]: "../secrets/canary.txt"}
        return [
            TestCase(
                tool_name=tool.name,
                args=args,
                probe_name=self.name,
                expected_signals=["CanarySignal"],
            )
        ]
