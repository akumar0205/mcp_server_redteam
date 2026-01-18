from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mcp_redteam.runner.trace import RunReport


def render_report(report: RunReport, output_dir: Path) -> Path:
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html.j2")
    output_dir.mkdir(parents=True, exist_ok=True)
    html = template.render(report=report)
    output_path = output_dir / "report.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path
