from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Finding(BaseModel):
    id: str
    severity: Severity
    category: str
    title: str
    source: str
    evidence: str
    recommendation: str


class ToolCallTrace(BaseModel):
    tool: str
    args: dict[str, Any]
    output: str
    structured: Optional[dict[str, Any]] = None


class TestCaseResult(BaseModel):
    test_id: str
    name: str
    prompt: str
    policy: str
    tool_servers: list[str]
    assistant_response: Optional[str] = None
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    judges: list[str] = Field(default_factory=list)


class EndpointScanResult(BaseModel):
    name: str
    base_url: str
    auth_type: str
    tools: list[str]
    findings: list[Finding] = Field(default_factory=list)


class RunReport(BaseModel):
    run_id: str
    timestamp: datetime
    mode: str
    suite_name: Optional[str] = None
    targets: list[str] = Field(default_factory=list)
    endpoints: list[str] = Field(default_factory=list)
    test_results: list[TestCaseResult] = Field(default_factory=list)
    endpoint_results: list[EndpointScanResult] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    score: float = 0.0
    severity_counts: dict[str, int] = Field(default_factory=dict)
