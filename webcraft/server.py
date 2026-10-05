"""Tiny development server for previewing a built site."""

from __future__ import annotations

import functools
import os
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Union


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_request(self, code="-", size="-") -> None:
        # Only report failed requests to keep the console readable.
        if isinstance(code, int) and code >= 400:
            super().log_request(code, size)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve(directory: Union[str, os.PathLike] = "dist", port: int = 8000, *, open_browser: bool = True) -> None:
    """Serve ``directory`` on ``http://localhost:<port>`` until interrupted."""
    handler = functools.partial(_QuietHandler, directory=os.fspath(directory))
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        url = f"http://localhost:{httpd.server_address[1]}/"
        print(f"WebCraft  ▸  {url}   (durdurmak için / to stop: Ctrl+C)")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
