from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .heuristics import rank_tools
from .mcp_client import MCPClient, Tool
from .report import Finding, Report, ReportSummary
from .signals import (
    SignalEvidence,
    detect_canary,
    detect_error_leak,
    detect_ssrf,
    detect_timing,
)
from .transcript import TranscriptWriter
from .transport_http import HttpTransport
from .transport_stdio import StdioTransport
from ..probes import (
    AuthProbe,
    PathTraversalProbe,
    SSRFProbe,
    CmdInjectionProbe,
    DoSProbe,
    SchemaConfusionProbe,
    PromptInjectionProbe,
)


SEVERITY_MAP = {
    "PathTraversalProbe": "High",
    "SSRFProbe": "High",
    "CmdInjectionProbe": "High",
    "DoSProbe": "Medium",
    "SchemaConfusionProbe": "Low",
    "AuthProbe": "Medium",
    "PromptInjectionProbe": "Low",
}


@dataclass
class ScanContext:
    target: str
    timeout: float
    latency_threshold_ms: float
    metadata: dict[str, Any]


def _make_client(transport: str, cmd: str | None, url: str | None) -> MCPClient:
    if transport == "stdio":
        if not cmd:
            raise ValueError("--cmd is required for stdio transport")
        return MCPClient(StdioTransport(cmd))
    if transport == "http":
        if not url:
            raise ValueError("--url is required for http transport")
        return MCPClient(HttpTransport(url))
    raise ValueError(f"Unsupported transport {transport}")


def _record_transcript(transcript: TranscriptWriter, direction: str, method: str, request_id: int, payload: dict[str, Any], latency_ms: float | None, error: str | None) -> None:
    transcript.record(
        direction=direction,
        method=method,
        request_id=request_id,
        payload=payload,
        latency_ms=latency_ms,
        error=error,
    )


def run_scan(
    transport: str,
    cmd: str | None,
    url: str | None,
    out_dir: Path,
    budget: int,
    timeout: float,
    include_llm: bool,
) -> None:
    transcript_path = out_dir / "transcript.jsonl"
    transcript = TranscriptWriter(transcript_path)
    target = cmd if transport == "stdio" else (url or "")
    context = ScanContext(
        target=target,
        timeout=timeout,
        latency_threshold_ms=timeout * 800,
        metadata={
            "fake_metadata_url": "http://127.0.0.1:9100/metadata",
            "lab_supports_auth_toggle": True,
        },
    )

    client = _make_client(transport, cmd, url)
    findings: list[Finding] = []
    tests_run = 0
    tools: list[Tool] = []
    resources = []
    prompts = []

    try:
        init_params = {"protocolVersion": client.protocol_version, "capabilities": {}}
        init_response = client.initialize(timeout=timeout)
        _record_transcript(transcript, "request", "initialize", init_response.request_id, init_params, None, None)
        _record_transcript(
            transcript,
            "response",
            "initialize",
            init_response.request_id,
            {"result": init_response.result, "error": init_response.error},
            init_response.latency_ms,
            json.dumps(init_response.error) if init_response.error else None,
        )

        tools_resp, tools = client.list_tools(timeout=timeout)
        _record_transcript(transcript, "request", "listTools", tools_resp.request_id, {}, None, None)
        _record_transcript(
            transcript,
            "response",
            "listTools",
            tools_resp.request_id,
            {"result": tools_resp.result, "error": tools_resp.error},
            tools_resp.latency_ms,
            json.dumps(tools_resp.error) if tools_resp.error else None,
        )

        resources_resp, resources = client.list_resources(timeout=timeout)
        _record_transcript(transcript, "request", "listResources", resources_resp.request_id, {}, None, None)
        _record_transcript(
            transcript,
            "response",
            "listResources",
            resources_resp.request_id,
            {"result": resources_resp.result, "error": resources_resp.error},
            resources_resp.latency_ms,
            json.dumps(resources_resp.error) if resources_resp.error else None,
        )

        prompts_resp, prompts = client.list_prompts(timeout=timeout)
        _record_transcript(transcript, "request", "listPrompts", prompts_resp.request_id, {}, None, None)
        _record_transcript(
            transcript,
            "response",
            "listPrompts",
            prompts_resp.request_id,
            {"result": prompts_resp.result, "error": prompts_resp.error},
            prompts_resp.latency_ms,
            json.dumps(prompts_resp.error) if prompts_resp.error else None,
        )

        prompt_probe = PromptInjectionProbe()
        prompt_findings = prompt_probe.scan(tools, resources, prompts)
        for finding in prompt_findings:
            findings.append(
                Finding(
                    severity=SEVERITY_MAP["PromptInjectionProbe"],
                    confidence="Low",
                    tool_name=finding.location,
                    probe_name=prompt_probe.name,
                    description="Potential prompt injection pattern detected",
                    repro_args={},
                    evidence=[
                        SignalEvidence(
                            signal="PromptInjectionSignal",
                            detail=f"Matched content: {finding.content}",
                            transcript_id=0,
                        )
                    ],
                    remediation="Review prompt/tool descriptions to remove instruction-hijacking content.",
                )
            )

        tool_risks = rank_tools(tools)
        probes = [
            AuthProbe(),
            PathTraversalProbe(),
            SSRFProbe(),
            CmdInjectionProbe(),
            DoSProbe(),
            SchemaConfusionProbe(),
        ]

        for tool_risk in tool_risks:
            tool = tool_risk.tool
            for probe in probes:
                for test_case in probe.generate(tool, context.metadata):
                    if tests_run >= budget:
                        break
                    tests_run += 1
                    response = client.call_tool(test_case.tool_name, test_case.args, timeout=timeout)
                    _record_transcript(
                        transcript,
                        "request",
                        "callTool",
                        response.request_id,
                        {\"name\": test_case.tool_name, \"arguments\": test_case.args},
                        None,
                        None,
                    )
                    response_payload: dict[str, Any] = {"result": response.result, "error": response.error}
                    _record_transcript(
                        transcript,
                        "response",
                        "callTool",
                        response.request_id,
                        response_payload,
                        response.latency_ms,
                        json.dumps(response.error) if response.error else None,
                    )
                    evidence: list[SignalEvidence] = []
                    evidence.extend(detect_error_leak(response_payload, response.request_id))
                    evidence.extend(detect_canary(response_payload, response.request_id))
                    evidence.extend(detect_ssrf(response_payload, response.request_id))
                    if response.latency_ms is not None:
                        evidence.extend(
                            detect_timing(response.latency_ms, context.latency_threshold_ms, response.request_id)
                        )
                    if evidence:
                        findings.append(
                            Finding(
                                severity=SEVERITY_MAP.get(test_case.probe_name, "Low"),
                                confidence="High" if evidence else "Low",
                                tool_name=test_case.tool_name,
                                probe_name=test_case.probe_name,
                                description=f"Probe {test_case.probe_name} triggered signals",
                                repro_args=test_case.args,
                                evidence=evidence,
                                remediation="Harden input validation and restrict dangerous operations.",
                            )
                        )
                if tests_run >= budget:
                    break
            if tests_run >= budget:
                break
    finally:
        client.close()
        transcript.close()

    report = Report(
        summary=ReportSummary(
            target=target,
            tool_count=len(tools),
            tests_run=tests_run,
            include_llm=include_llm,
        ),
        findings=findings,
    )
    report.write(out_dir / "report.json", out_dir / "report.md")
