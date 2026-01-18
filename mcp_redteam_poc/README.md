# MCP Red Team Harness

> **Authorized testing only.** This harness is intended for controlled environments and security testing.

## Requirements

- Python 3.11+
- `uv` for dependency management

## Setup (uv)

```bash
cd mcp_redteam_poc
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Demo Mode (Built-in Agent + Tool Server)

```bash
mcp-redteam demo \
  --suite suites/baseline \
  --out artifacts/demo \
  --tool-server benign
```

## Run Mode (Real Agent + MCP Endpoints)

```bash
mcp-redteam run \
  --suite suites/injections \
  --target configs/target_http.json \
  --mcp-endpoints configs/mcp_endpoints.json \
  --out artifacts/run
```

## Scan MCP Endpoints (Server-only Validation)

```bash
mcp-redteam scan-mcp \
  --mcp-endpoints configs/mcp_endpoints.json \
  --out artifacts/scan
```

## Output

Each run writes the following into the output directory:

- `report.html` (static HTML report)
- `report.json` (structured JSON)
- `report.junit.xml` (custom JUnit XML)

## Notes

- Demo mode launches a local demo agent server plus a local MCP tool server on ephemeral ports.
- Server-only scan mode performs tool poisoning heuristics, schema risk checks, and transport/auth checks.
