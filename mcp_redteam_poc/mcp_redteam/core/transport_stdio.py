from __future__ import annotations

import json
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any

from .transport_base import TransportResponse, Transport


@dataclass
class _ResponseLine:
    raw: str
    received_at: float


class StdioTransport(Transport):
    def __init__(self, cmd: str) -> None:
        self._process = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        if not self._process.stdin or not self._process.stdout:
            raise RuntimeError("Failed to start stdio process")
        self._stdin = self._process.stdin
        self._stdout = self._process.stdout
        self._queue: queue.Queue[_ResponseLine] = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        while True:
            line = self._stdout.readline()
            if not line:
                break
            self._queue.put(_ResponseLine(raw=line.strip(), received_at=time.time()))

    def send(self, message: dict[str, Any], timeout: float) -> TransportResponse:
        if self._process.poll() is not None:
            raise RuntimeError("Stdio process has exited")
        start = time.time()
        payload = json.dumps(message)
        self._stdin.write(payload + "\n")
        self._stdin.flush()
        try:
            response_line = self._queue.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError("Timed out waiting for stdio response") from exc
        latency_ms = (response_line.received_at - start) * 1000
        response_payload = json.loads(response_line.raw)
        return TransportResponse(payload=response_payload, latency_ms=latency_ms)

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
