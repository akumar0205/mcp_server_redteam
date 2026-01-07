from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*([^\s]+)"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-_=]+"),
]


@dataclass
class TranscriptEntry:
    timestamp: str
    direction: str
    method: str
    request_id: int
    payload: dict[str, Any]
    latency_ms: float | None
    error: str | None


class TranscriptWriter:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._handle = path.open("w", encoding="utf-8")

    def close(self) -> None:
        self._handle.close()

    def _redact_value(self, value: Any) -> Any:
        if isinstance(value, str):
            redacted = value
            for pattern in SECRET_PATTERNS:
                redacted = pattern.sub("<REDACTED>", redacted)
            return redacted
        if isinstance(value, dict):
            return {k: self._redact_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._redact_value(v) for v in value]
        return value

    def record(self, direction: str, method: str, request_id: int, payload: dict[str, Any], latency_ms: float | None, error: str | None) -> None:
        entry = TranscriptEntry(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            direction=direction,
            method=method,
            request_id=request_id,
            payload=self._redact_value(payload),
            latency_ms=latency_ms,
            error=error,
        )
        self._handle.write(json.dumps(entry.__dict__) + "\n")
        self._handle.flush()
