from __future__ import annotations

from pathlib import Path

from mcp_redteam.runner.trace import RunReport


def write_report_json(report: RunReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "report.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path
