from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ..core.mcp_client import Tool, Resource, Prompt


INJECTION_PATTERNS = [
    re.compile(r"ignore (all|previous) instructions", re.IGNORECASE),
    re.compile(r"system prompt", re.IGNORECASE),
    re.compile(r"you are an? ai", re.IGNORECASE),
]


@dataclass
class PromptInjectionFinding:
    location: str
    content: str


class PromptInjectionProbe:
    name = "PromptInjectionProbe"

    def scan(self, tools: list[Tool], resources: list[Resource], prompts: list[Prompt]) -> list[PromptInjectionFinding]:
        findings: list[PromptInjectionFinding] = []
        for tool in tools:
            findings.extend(self._scan_text(f"tool:{tool.name}", tool.description))
        for resource in resources:
            findings.extend(self._scan_text(f"resource:{resource.uri}", resource.description))
        for prompt in prompts:
            findings.extend(self._scan_text(f"prompt:{prompt.name}", prompt.description))
        return findings

    def _scan_text(self, location: str, text: str) -> list[PromptInjectionFinding]:
        findings: list[PromptInjectionFinding] = []
        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                findings.append(PromptInjectionFinding(location=location, content=text))
                break
        return findings
