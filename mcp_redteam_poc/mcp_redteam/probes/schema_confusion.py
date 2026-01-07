from __future__ import annotations

from typing import Any

from .base import TestCase
from ..core.mcp_client import Tool


class SchemaConfusionProbe:
    name = "SchemaConfusionProbe"

    def generate(self, tool: Tool, metadata: dict[str, Any]) -> list[TestCase]:
        return [
            TestCase(
                tool_name=tool.name,
                args={"unexpected": [1, 2, 3]},
                probe_name=self.name,
                expected_signals=["ErrorLeakSignal"],
            )
        ]
