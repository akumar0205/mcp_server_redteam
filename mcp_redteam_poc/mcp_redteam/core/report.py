from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .signals import SignalEvidence


@dataclass
class Finding:
    severity: str
    confidence: str
    tool_name: str
    probe_name: str
    description: str
    repro_args: dict[str, Any]
    evidence: list[SignalEvidence]
    remediation: str


@dataclass
class ReportSummary:
    target: str
    tool_count: int
    tests_run: int
    include_llm: bool


@dataclass
class Report:
    summary: ReportSummary
    findings: list[Finding]

    def to_json(self) -> dict[str, Any]:
        return {
            "summary": asdict(self.summary),
            "findings": [
                {
                    **{k: v for k, v in asdict(finding).items() if k != "evidence"},
                    "evidence": [asdict(ev) for ev in finding.evidence],
                }
                for finding in self.findings
            ],
        }

    def write(self, json_path: Path, md_path: Path) -> None:
        json_path.write_text(json.dumps(self.to_json(), indent=2), encoding="utf-8")
        md_path.write_text(self._to_markdown(), encoding="utf-8")

    def _to_markdown(self) -> str:
        lines = [
            "# MCP Red Team Report",
            "",
            "## Summary",
            f"- Target: {self.summary.target}",
            f"- Tools discovered: {self.summary.tool_count}",
            f"- Tests executed: {self.summary.tests_run}",
            f"- LLM probes enabled: {self.summary.include_llm}",
            "",
            "## Findings",
        ]
        if not self.findings:
            lines.append("No findings detected.")
            return "\n".join(lines)
        for finding in self.findings:
            lines.extend(
                [
                    f"### {finding.severity}: {finding.probe_name} on {finding.tool_name}",
                    f"- Confidence: {finding.confidence}",
                    f"- Description: {finding.description}",
                    f"- Repro args: `{json.dumps(finding.repro_args)}`",
                    f"- Remediation: {finding.remediation}",
                    "- Evidence:",
                ]
            )
            for ev in finding.evidence:
                lines.append(f"  - {ev.signal}: {ev.detail} (transcript id {ev.transcript_id})")
            lines.append("")
        return "\n".join(lines)
