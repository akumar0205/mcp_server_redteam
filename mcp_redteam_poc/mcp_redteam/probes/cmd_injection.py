from __future__ import annotations

from typing import Any

from .base import TestCase, extract_param_names
from ..core.mcp_client import Tool


class CmdInjectionProbe:
    name = "CmdInjectionProbe"

    def generate(self, tool: Tool, metadata: dict[str, Any]) -> list[TestCase]:
        param_names = extract_param_names(tool)
        cmd_params = [p for p in param_names if "cmd" in p.lower() or "command" in p.lower()]
        if not cmd_params:
            return []
        args = {cmd_params[0]: "echo safe && cat /etc/passwd"}
        return [
            TestCase(
                tool_name=tool.name,
                args=args,
                probe_name=self.name,
                expected_signals=["ErrorLeakSignal"],
            )
        ]
