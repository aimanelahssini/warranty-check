#!/usr/bin/env python3
"""Local warranty checker: serves the page and calls brand APIs the browser can't reach (CORS)."""
import json
import os
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "api"))
from _core import BRANDS, lookup  # noqa: E402

STATIC = os.path.join(HERE, "public")
PORT = int(os.environ.get("WARRANTY_PORT", "8765"))
TYPES = {".html": "text/html; charset=utf-8", ".svg": "image/svg+xml", ".css": "text/css", ".js": "text/javascript",
         ".png": "image/png", ".xml": "application/xml", ".txt": "text/plain; charset=utf-8", ".json": "application/json"}


def this_computer(ask_root):
    def dmi(name):
        try:
            with open(f"/sys/class/dmi/id/{name}") as f:
                return f.read().strip()
        except OSError:
            return ""
    serial = dmi("product_serial")
    if not serial and ask_root:
        try:
            serial = subprocess.run(["pkexec", "cat", "/sys/class/dmi/id/product_serial"],
                                    capture_output=True, text=True, timeout=120).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            serial = ""
    return {"vendor": dmi("sys_vendor"), "model": dmi("product_version") or dmi("product_name"), "serial": serial}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, ctype="application/json"):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(url.query)
        brand = url.path.removeprefix("/api/")
        if brand in BRANDS:
            return self.send(200, lookup(brand, (qs.get("serial") or [""])[0]))
        if url.path == "/api/this":
            return self.send(200, this_computer("root" in qs))
        path = os.path.realpath(os.path.join(STATIC, url.path.lstrip("/")))
        if not (path + os.sep).startswith(STATIC + os.sep):
            return self.send(404, b"not found", "text/plain")
        if os.path.isdir(path):
            if not url.path.endswith("/"):
                self.send_response(301)
                self.send_header("Location", url.path + "/" + (f"?{url.query}" if url.query else ""))
                self.end_headers()
                return
            path = os.path.join(path, "index.html")
        if not os.path.isfile(path):
            return self.send(404, b"not found", "text/plain")
        with open(path, "rb") as f:
            self.send(200, f.read(), TYPES.get(os.path.splitext(path)[1], "application/octet-stream"))


if __name__ == "__main__":
    print(f"Warranty check on http://127.0.0.1:{PORT}", file=sys.stderr)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
