import argparse
import datetime as dt
import pathlib
import sys
from typing import Sequence

from .core.runner import run_scan
from .lab.vuln_server import run_http_server
from .lab.fake_metadata import run_fake_metadata


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MCP Red Team PoC scanner (authorized testing only)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lab_parser = subparsers.add_parser("lab", help="Start local vulnerable MCP lab servers")
    lab_parser.add_argument("--mcp-host", default="127.0.0.1", help="MCP server host")
    lab_parser.add_argument("--mcp-port", type=int, default=9000, help="MCP server port")
    lab_parser.add_argument("--metadata-host", default="127.0.0.1", help="Fake metadata host")
    lab_parser.add_argument("--metadata-port", type=int, default=9100, help="Fake metadata port")

    scan_parser = subparsers.add_parser("scan", help="Run MCP Red Team scan")
    scan_parser.add_argument("--transport", choices=["stdio", "http"], required=True)
    scan_parser.add_argument("--cmd", help="Command to spawn for stdio transport")
    scan_parser.add_argument("--url", help="HTTP endpoint for MCP JSON-RPC")
    scan_parser.add_argument("--out", help="Output directory (default runs/<timestamp>)")
    scan_parser.add_argument("--budget", type=int, default=50, help="Max tool calls")
    scan_parser.add_argument("--timeout", type=float, default=10.0, help="Timeout seconds")
    scan_parser.add_argument("--include-llm", action="store_true", help="Include LLM-based probes (stub)")

    return parser.parse_args(argv)


def _default_out_dir() -> pathlib.Path:
    timestamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return pathlib.Path("runs") / timestamp


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])

    if args.command == "lab":
        run_fake_metadata(args.metadata_host, args.metadata_port)
        run_http_server(args.mcp_host, args.mcp_port, args.metadata_host, args.metadata_port)
        return

    if args.command == "scan":
        out_dir = pathlib.Path(args.out) if args.out else _default_out_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        run_scan(
            transport=args.transport,
            cmd=args.cmd,
            url=args.url,
            out_dir=out_dir,
            budget=args.budget,
            timeout=args.timeout,
            include_llm=args.include_llm,
        )
        return

    raise SystemExit("Unknown command")
