from __future__ import annotations

from typing import Any

from .base import TestCase, extract_param_names
from ..core.mcp_client import Tool


class SSRFProbe:
    name = "SSRFProbe"

    def generate(self, tool: Tool, metadata: dict[str, Any]) -> list[TestCase]:
        param_names = extract_param_names(tool)
        url_params = [p for p in param_names if "url" in p.lower() or "fetch" in p.lower()]
        if not url_params:
            return []
        url = metadata.get("fake_metadata_url", "http://127.0.0.1:9100/metadata")
        args = {url_params[0]: url}
        return [
            TestCase(
                tool_name=tool.name,
                args=args,
                probe_name=self.name,
                expected_signals=["SSRFSignal"],
            )
        ]
