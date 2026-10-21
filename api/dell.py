"""Vercel function: GET /api/dell?serial=..."""
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from _core import lookup  # noqa: E402

BRAND = os.path.splitext(os.path.basename(__file__))[0]


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        body = json.dumps(lookup(BRAND, (qs.get("serial") or [""])[0], (qs.get("lang") or ["en"])[0])).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
