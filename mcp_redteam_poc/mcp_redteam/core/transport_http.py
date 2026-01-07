from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

from .transport_base import TransportResponse, Transport


class HttpTransport(Transport):
    def __init__(self, url: str) -> None:
        self._url = url

    def send(self, message: dict[str, Any], timeout: float) -> TransportResponse:
        data = json.dumps(message).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
        latency_ms = (time.time() - start) * 1000
        payload = json.loads(raw)
        return TransportResponse(payload=payload, latency_ms=latency_ms)

    def close(self) -> None:
        return
