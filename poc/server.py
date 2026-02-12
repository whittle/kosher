"""Background HTTP server for serving the test page."""

import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class _QuietHandler(SimpleHTTPRequestHandler):
    """HTTP handler that suppresses request logging."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


def start_server(port: int = 8765) -> str:
    """Start a background HTTP server serving the poc/ directory.

    Returns the base URL (e.g. "http://127.0.0.1:8765").
    """
    directory = str(Path(__file__).parent)
    handler = partial(_QuietHandler, directory=directory)
    server = HTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"http://127.0.0.1:{port}"
