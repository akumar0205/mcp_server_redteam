# MCP Red Team PoC Scanner

> **Authorized testing only.** This proof-of-concept scanner is intended **only** for local, controlled environments. Do not point it at real systems or public services.

## Features

- MCP JSON-RPC client over stdio or HTTP transports
- Tool/resource/prompt enumeration
- Deterministic probe suite (path traversal, SSRF, command injection, DoS, schema confusion, auth)
- Full JSONL transcript recording with basic secret redaction
- Markdown + JSON reporting
- Local vulnerable lab server and fake metadata server

## Setup

```bash
cd mcp_redteam_poc
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run the Lab Servers

```bash
python -m mcp_redteam lab
```

This starts:
- MCP lab server: `http://127.0.0.1:9000/mcp`
- Fake metadata server: `http://127.0.0.1:9100/metadata`

## Run a Scan (HTTP)

```bash
python -m mcp_redteam scan \
  --transport http \
  --url http://127.0.0.1:9000/mcp
```

## Run a Scan (Stdio)

```bash
python -m mcp_redteam scan \
  --transport stdio \
  --cmd "python -m mcp_redteam.lab.vuln_server --mode stdio"
```

## Output

- `runs/<timestamp>/transcript.jsonl`
- `runs/<timestamp>/report.json`
- `runs/<timestamp>/report.md`

## Smoke Test

```bash
python -m mcp_redteam lab
# In another terminal:
python -m mcp_redteam scan --transport http --url http://127.0.0.1:9000/mcp
```

## Notes

- The scanner uses only localhost targets for SSRF probes.
- `--include-llm` is a stub flag for future extensions and does not call external APIs.
