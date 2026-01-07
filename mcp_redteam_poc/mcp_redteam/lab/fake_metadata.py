from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


class FakeMetadataHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - HTTP verb
        if self.path != "/metadata":
            self.send_response(404)
            self.end_headers()
            return
        payload = b"FAKE_METADATA_TOKEN=local-metadata"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - base method
        return


def run_fake_metadata(host: str, port: int) -> None:
    server = HTTPServer((host, port), FakeMetadataHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Fake metadata server listening on http://{host}:{port}/metadata")
