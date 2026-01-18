from __future__ import annotations

import re
from typing import Any

from mcp_redteam.config import AuthConfig, AuthType, is_localhost
from mcp_redteam.mcp.protocol import ToolDefinition
from mcp_redteam.runner.trace import Finding, Severity

INJECTION_PHRASES = [
    "ignore previous",
    "always include",
    "exfiltrate",
    "send to",
    "print secrets",
    "override system",
]

DATA_MOVEMENT_TOOLS = {"send_email", "http_request", "export", "upload", "export_data"}

RISK_FIELDS = {
    "url": "URL",
    "uri": "URL",
    "href": "URL",
    "path": "file path",
    "filepath": "file path",
    "cmd": "command",
    "shell": "command",
    "command": "command",
    "email": "email",
    "to": "email",
    "recipient": "email",
    "domain": "domain",
}


def _stringify_schema(schema: dict[str, Any]) -> str:
    return " ".join(map(str, schema.values())).lower()


def check_poisoned_description(tool: ToolDefinition, source: str) -> list[Finding]:
    findings: list[Finding] = []
    description_lower = tool.description.lower()
    for phrase in INJECTION_PHRASES:
        if phrase in description_lower:
            severity = Severity.high if tool.name in DATA_MOVEMENT_TOOLS else Severity.medium
            findings.append(
                Finding(
                    id=f"poison-{tool.name}",
                    severity=severity,
                    category="Tool Description Poisoning",
                    title=f"Injection-like phrase in {tool.name}",
                    source=source,
                    evidence=f"Found phrase '{phrase}' in description: {tool.description}",
                    recommendation="Remove instruction-like text or constrain tool usage.",
                )
            )
            break
    return findings


def check_schema_risks(tool: ToolDefinition, source: str) -> list[Finding]:
    findings: list[Finding] = []
    schema = tool.input_schema or {}
    properties = schema.get("properties", {})
    for field_name, details in properties.items():
        normalized = field_name.lower()
        for risky_key, label in RISK_FIELDS.items():
            if risky_key == normalized:
                has_constraints = any(
                    key in details for key in ["pattern", "enum", "maxLength", "minLength"]
                )
                severity = Severity.high if not has_constraints else Severity.medium
                findings.append(
                    Finding(
                        id=f"schema-{tool.name}-{field_name}",
                        severity=severity,
                        category="Dangerous Argument Surface",
                        title=f"{tool.name} accepts {label} input",
                        source=source,
                        evidence=f"Field '{field_name}' lacks constraints: {details}",
                        recommendation="Add allowlists or validation constraints.",
                    )
                )
    if not properties and _stringify_schema(schema):
        findings.append(
            Finding(
                id=f"schema-{tool.name}-unknown",
                severity=Severity.low,
                category="Dangerous Argument Surface",
                title=f"{tool.name} schema is underspecified",
                source=source,
                evidence=f"Input schema: {schema}",
                recommendation="Provide explicit schema properties and constraints.",
            )
        )
    return findings


def check_transport_risks(base_url: str, auth: AuthConfig, source: str) -> list[Finding]:
    findings: list[Finding] = []
    if base_url.startswith("http://") and not is_localhost(base_url):
        findings.append(
            Finding(
                id=f"transport-{source}",
                severity=Severity.medium,
                category="Missing Auth/Transport Risk",
                title="Insecure transport",
                source=source,
                evidence=f"Endpoint uses HTTP without TLS: {base_url}",
                recommendation="Use HTTPS for remote MCP endpoints.",
            )
        )
    if auth.type == AuthType.none and not is_localhost(base_url):
        findings.append(
            Finding(
                id=f"auth-{source}",
                severity=Severity.medium,
                category="Missing Auth/Transport Risk",
                title="Missing authentication",
                source=source,
                evidence="Endpoint configured with no authentication.",
                recommendation="Require authentication for remote MCP endpoints.",
            )
        )
    return findings


def check_transcript_for_injection(output: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    if not output:
        return findings
    lowered = output.lower()
    for phrase in INJECTION_PHRASES:
        if phrase in lowered:
            findings.append(
                Finding(
                    id=f"output-{source}",
                    severity=Severity.medium,
                    category="Tool Output Injection",
                    title="Tool output contains injection-like text",
                    source=source,
                    evidence=f"Output contained '{phrase}': {output}",
                    recommendation="Sanitize tool outputs before using in agent prompts.",
                )
            )
            break
    return findings
