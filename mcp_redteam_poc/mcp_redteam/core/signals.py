from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SignalEvidence:
    signal: str
    detail: str
    transcript_id: int


ERROR_PATTERNS = [
    re.compile(r"Traceback", re.IGNORECASE),
    re.compile(r"Exception", re.IGNORECASE),
    re.compile(r"File \".+\"", re.IGNORECASE),
]


def detect_error_leak(response_payload: dict[str, Any], transcript_id: int) -> list[SignalEvidence]:
    evidence: list[SignalEvidence] = []
    text = str(response_payload)
    for pattern in ERROR_PATTERNS:
        if pattern.search(text):
            evidence.append(
                SignalEvidence(
                    signal="ErrorLeakSignal",
                    detail="Potential stack trace or exception leakage",
                    transcript_id=transcript_id,
                )
            )
            break
    return evidence


def detect_canary(response_payload: dict[str, Any], transcript_id: int) -> list[SignalEvidence]:
    if "CANARY_SECRET" in str(response_payload):
        return [
            SignalEvidence(
                signal="CanarySignal",
                detail="Canary value detected in response",
                transcript_id=transcript_id,
            )
        ]
    return []


def detect_ssrf(response_payload: dict[str, Any], transcript_id: int) -> list[SignalEvidence]:
    if "FAKE_METADATA_TOKEN" in str(response_payload):
        return [
            SignalEvidence(
                signal="SSRFSignal",
                detail="Fake metadata token detected",
                transcript_id=transcript_id,
            )
        ]
    return []


def detect_timing(latency_ms: float, threshold_ms: float, transcript_id: int) -> list[SignalEvidence]:
    if latency_ms >= threshold_ms:
        return [
            SignalEvidence(
                signal="TimingSignal",
                detail=f"Latency {latency_ms:.1f}ms exceeds threshold {threshold_ms:.1f}ms",
                transcript_id=transcript_id,
            )
        ]
    return []
