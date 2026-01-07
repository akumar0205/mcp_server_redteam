from __future__ import annotations

from typing import Any

from .base import TestCase
from ..core.mcp_client import Tool


class AuthProbe:
    name = "AuthProbe"

    def generate(self, tool: Tool, metadata: dict[str, Any]) -> list[TestCase]:
        if not metadata.get("lab_supports_auth_toggle"):
            return []
        if tool.name != "read_file":
            return []
        return [
            TestCase(
                tool_name=tool.name,
                args={"path": "protected/secret.txt"},
                probe_name=self.name,
                expected_signals=["ErrorLeakSignal"],
            )
        ]
