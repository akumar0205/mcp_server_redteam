from __future__ import annotations

from typing import Any

from .base import TestCase, extract_param_names
from ..core.mcp_client import Tool


class DoSProbe:
    name = "DoSProbe"

    def generate(self, tool: Tool, metadata: dict[str, Any]) -> list[TestCase]:
        param_names = extract_param_names(tool)
        if not param_names:
            return []
        large_payload = "A" * 10000
        args = {param_names[0]: {"nested": [large_payload] * 20}}
        return [
            TestCase(
                tool_name=tool.name,
                args=args,
                probe_name=self.name,
                expected_signals=["TimingSignal"],
            )
        ]
