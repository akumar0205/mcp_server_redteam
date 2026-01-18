from __future__ import annotations

from datetime import datetime
from typing import Iterable

import httpx

from mcp_redteam.config import EndpointsFile, TargetConfig, auth_headers
from mcp_redteam.judges.deterministic import (
    check_poisoned_description,
    check_schema_risks,
    check_transcript_for_injection,
    check_transport_risks,
)
from mcp_redteam.mcp.http_client import MCPHttpClient
from mcp_redteam.runner.trace import (
    EndpointScanResult,
    Finding,
    RunReport,
    Severity,
    TestCaseResult,
    ToolCallTrace,
)
from mcp_redteam.suite.models import Suite


def _score_findings(findings: Iterable[Finding]) -> tuple[float, dict[str, int]]:
    weights = {
        Severity.critical: 20,
        Severity.high: 10,
        Severity.medium: 5,
        Severity.low: 2,
    }
    score = 100.0
    counts: dict[str, int] = {level.value: 0 for level in Severity}
    for finding in findings:
        counts[finding.severity.value] += 1
        score -= weights[finding.severity]
    return max(score, 0.0), counts


async def scan_endpoints(endpoints: EndpointsFile) -> list[EndpointScanResult]:
    results: list[EndpointScanResult] = []
    for endpoint in endpoints.endpoints:
        client = MCPHttpClient(str(endpoint.base_url), endpoint.auth)
        tools = await client.get_tools()
        findings: list[Finding] = []
        for tool in tools.tools:
            findings.extend(check_poisoned_description(tool, endpoint.name))
            findings.extend(check_schema_risks(tool, endpoint.name))
        findings.extend(check_transport_risks(str(endpoint.base_url), endpoint.auth, endpoint.name))
        results.append(
            EndpointScanResult(
                name=endpoint.name,
                base_url=str(endpoint.base_url),
                auth_type=endpoint.auth.type.value,
                tools=[tool.name for tool in tools.tools],
                findings=findings,
            )
        )
    return results


def build_scan_report(endpoints: EndpointsFile, endpoint_results: list[EndpointScanResult]) -> RunReport:
    run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    findings = [finding for result in endpoint_results for finding in result.findings]
    score, counts = _score_findings(findings)
    return RunReport(
        run_id=run_id,
        timestamp=datetime.utcnow(),
        mode="scan-mcp",
        suite_name=None,
        targets=[],
        endpoints=[str(endpoint.base_url) for endpoint in endpoints.endpoints],
        test_results=[],
        endpoint_results=endpoint_results,
        findings=findings,
        score=score,
        severity_counts=counts,
    )


async def run_suite(
    suite: Suite,
    endpoints: EndpointsFile,
    target: TargetConfig | None = None,
) -> RunReport:
    run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    mode = "run" if target else "scan"
    endpoint_results = await scan_endpoints(endpoints)
    endpoint_findings = [finding for result in endpoint_results for finding in result.findings]

    test_results: list[TestCaseResult] = []
    if target:
        tool_urls = [str(endpoint.base_url) for endpoint in endpoints.endpoints]
        headers = auth_headers(target.auth)
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            for test in suite.tests:
                response = await client.post(
                    f"{str(target.base_url).rstrip('/')}/chat",
                    json={
                        "system_policy": test.policy,
                        "user_prompt": test.prompt,
                        "tool_server_urls": tool_urls,
                    },
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
                tool_calls = [
                    ToolCallTrace(**tool_call) for tool_call in payload.get("tool_calls", [])
                ]
                findings = []
                for call in tool_calls:
                    findings.extend(check_transcript_for_injection(call.output, test.id))
                test_results.append(
                    TestCaseResult(
                        test_id=test.id,
                        name=test.name,
                        prompt=test.prompt,
                        policy=test.policy,
                        tool_servers=tool_urls,
                        assistant_response=payload.get("assistant_response"),
                        tool_calls=tool_calls,
                        findings=findings,
                        judges=["deterministic"],
                    )
                )
    else:
        for test in suite.tests:
            test_results.append(
                TestCaseResult(
                    test_id=test.id,
                    name=test.name,
                    prompt=test.prompt,
                    policy=test.policy,
                    tool_servers=[str(endpoint.base_url) for endpoint in endpoints.endpoints],
                    findings=endpoint_findings,
                    judges=["server-only"],
                )
            )

    if target:
        all_findings = endpoint_findings + [
            finding for result in test_results for finding in result.findings
        ]
    else:
        all_findings = endpoint_findings
    score, counts = _score_findings(all_findings)
    return RunReport(
        run_id=run_id,
        timestamp=datetime.utcnow(),
        mode=mode,
        suite_name=suite.name,
        targets=[str(target.base_url)] if target else [],
        endpoints=[str(endpoint.base_url) for endpoint in endpoints.endpoints],
        test_results=test_results,
        endpoint_results=endpoint_results,
        findings=all_findings,
        score=score,
        severity_counts=counts,
    )


async def run_demo(
    suite: Suite,
    agent_url: str,
    tool_urls: list[str],
) -> RunReport:
    run_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    test_results: list[TestCaseResult] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        for test in suite.tests:
            response = await client.post(
                f"{agent_url.rstrip('/')}/chat",
                json={
                    "system_policy": test.policy,
                    "user_prompt": test.prompt,
                    "tool_server_urls": tool_urls,
                },
            )
            response.raise_for_status()
            payload = response.json()
            tool_calls = [ToolCallTrace(**tool_call) for tool_call in payload.get("tool_calls", [])]
            findings = []
            for call in tool_calls:
                findings.extend(check_transcript_for_injection(call.output, test.id))
            test_results.append(
                TestCaseResult(
                    test_id=test.id,
                    name=test.name,
                    prompt=test.prompt,
                    policy=test.policy,
                    tool_servers=tool_urls,
                    assistant_response=payload.get("assistant_response"),
                    tool_calls=tool_calls,
                    findings=findings,
                    judges=["deterministic"],
                )
            )
    all_findings = [finding for result in test_results for finding in result.findings]
    score, counts = _score_findings(all_findings)
    return RunReport(
        run_id=run_id,
        timestamp=datetime.utcnow(),
        mode="demo",
        suite_name=suite.name,
        targets=[agent_url],
        endpoints=tool_urls,
        test_results=test_results,
        findings=all_findings,
        score=score,
        severity_counts=counts,
    )
