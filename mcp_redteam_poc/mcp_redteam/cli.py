from __future__ import annotations

import asyncio
import multiprocessing
import socket
import time
from pathlib import Path
from typing import Optional

import typer

from mcp_redteam.config import EndpointsFile, TargetConfig, load_json_config
from mcp_redteam.report.html import render_report
from mcp_redteam.report.junit import write_junit
from mcp_redteam.runner.harness import build_scan_report, run_demo, run_suite, scan_endpoints
from mcp_redteam.storage import write_report_json
from mcp_redteam.suite.loader import load_suite

app = typer.Typer(add_completion=False)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _run_uvicorn(app_path: str, port: int) -> None:
    import uvicorn

    uvicorn.run(app_path, host="127.0.0.1", port=port, log_level="error")


def _start_server(app_path: str) -> tuple[str, multiprocessing.Process]:
    port = _find_free_port()
    process = multiprocessing.Process(target=_run_uvicorn, args=(app_path, port), daemon=True)
    process.start()
    time.sleep(0.5)
    return f"http://127.0.0.1:{port}", process


def _write_outputs(report, out_dir: Path) -> None:
    write_report_json(report, out_dir)
    render_report(report, out_dir)
    write_junit(report, out_dir)


@app.command()
def run(
    suite: Path = typer.Option(..., "--suite", exists=True, help="Path to suite.yaml or suite dir"),
    target: Optional[Path] = typer.Option(None, "--target", help="Path to target JSON"),
    mcp_endpoints: Path = typer.Option(..., "--mcp-endpoints", help="Path to MCP endpoints JSON"),
    out: Path = typer.Option(..., "--out", help="Output directory"),
    llm_judge: bool = typer.Option(False, "--llm-judge", help="Enable LLM judge"),
) -> None:
    suite_data = load_suite(suite)
    endpoints = load_json_config(mcp_endpoints, EndpointsFile)
    target_config = load_json_config(target, TargetConfig) if target else None
    report = asyncio.run(run_suite(suite_data, endpoints, target_config))
    _write_outputs(report, out)


@app.command("scan-mcp")
def scan_mcp(
    mcp_endpoints: Path = typer.Option(..., "--mcp-endpoints", help="Path to MCP endpoints JSON"),
    out: Path = typer.Option(..., "--out", help="Output directory"),
) -> None:
    endpoints = load_json_config(mcp_endpoints, EndpointsFile)
    endpoint_results = asyncio.run(scan_endpoints(endpoints))
    report = build_scan_report(endpoints, endpoint_results)
    _write_outputs(report, out)


@app.command()
def demo(
    suite: Path = typer.Option(..., "--suite", exists=True, help="Path to suite.yaml or suite dir"),
    out: Path = typer.Option(..., "--out", help="Output directory"),
    tool_server: list[str] = typer.Option(
        ["benign"],
        "--tool-server",
        help="Tool server type (benign|poisoned-tools|injection-output)",
    ),
) -> None:
    suite_data = load_suite(suite)
    tool_map = {
        "benign": "mcp_redteam.mcp.servers.benign:app",
        "poisoned-tools": "mcp_redteam.mcp.servers.poisoned_tools:app",
        "injection-output": "mcp_redteam.mcp.servers.injection_output:app",
    }
    tool_urls: list[str] = []
    processes: list[multiprocessing.Process] = []
    agent_url, agent_proc = _start_server("mcp_redteam.mcp.servers.demo_agent_server:app")
    processes.append(agent_proc)
    try:
        for server in tool_server:
            if server not in tool_map:
                raise typer.BadParameter(f"Unknown tool server: {server}")
            url, proc = _start_server(tool_map[server])
            tool_urls.append(url)
            processes.append(proc)
        report = asyncio.run(run_demo(suite_data, agent_url, tool_urls))
        _write_outputs(report, out)
    finally:
        for proc in processes:
            proc.terminate()
            proc.join(timeout=2)


if __name__ == "__main__":
    app()
