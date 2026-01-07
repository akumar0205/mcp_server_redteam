from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class TransportResponse:
    payload: dict[str, Any]
    latency_ms: float


class Transport(Protocol):
    def send(self, message: dict[str, Any], timeout: float) -> TransportResponse:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError
