#!/usr/bin/env python3
"""Local warranty checker: serves the page and calls brand APIs the browser can't reach (CORS)."""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
PORT = int(os.environ.get("WARRANTY_PORT", "8765"))
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
TYPES = {".html": "text/html; charset=utf-8", ".svg": "image/svg+xml", ".css": "text/css", ".js": "text/javascript"}


def fetch(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def lenovo(serial):
    d = fetch("https://pcsupport.lenovo.com/us/en/api/v4/upsell/redport/getIbaseInfo",
              {"serialNumber": serial, "country": "us", "language": "en"})
    if d.get("code") != 0 or not d.get("data"):
        return {"ok": False, "error": "Lenovo doesn't know this serial. Check it on the sticker under the laptop."}
    data, m = d["data"], d["data"]["machineInfo"]
    items = []
    for kind in ("baseWarranties", "upgradeWarranties", "contractWarranties"):
        for w in data.get(kind) or []:
            items.append({"name": w.get("name"), "type": w.get("deliveryTypeName") or w.get("type"),
                          "start": w.get("startDate"), "end": w.get("endDate")})
    items.sort(key=lambda w: w["end"] or "", reverse=True)
    status = data.get("warrantyStatus") or ""
    return {
        "ok": True, "full": True,
        "model": m.get("productName"), "product": m.get("product"), "serial": m.get("serial"),
        "inWarranty": status.lower() == "in warranty", "status": status,
        "end": (data.get("currentWarranty") or {}).get("endDate"),
        "facts": {"Built": m.get("buildDate"), "Shipped": m.get("shipDate"), "Ship country": m.get("shipToCountry"),
                  "Purchase date": m.get("popDate"), "Lenovo support until": m.get("eosDate")},
        "items": items,
        "link": f"https://pcsupport.lenovo.com/products/{urllib.parse.quote(serial)}/warranty",
    }


def hp(serial):
    q = urllib.parse.urlencode({"q": serial, "context": "pdp", "authState": "anonymous",
                                "template": "SupportSearchResults"})
    d = fetch(f"https://support.hp.com/wcc-services/searchresult/us-en?{q}")
    v = ((d.get("data") or {}).get("verifyResponse") or {}).get("data")
    if not v or not v.get("productName"):
        return {"ok": False, "error": "HP doesn't know this serial. Check it on the sticker or with Fn+Esc."}
    return {
        "ok": True, "full": False,
        "model": v["productName"], "product": v.get("productNumber"), "serial": v.get("serialNumber"),
        "facts": {"Product number": v.get("productNumber"), "Description": v.get("description")},
        "note": "HP protects warranty dates behind a captcha. Your model is confirmed, open HP's page to see the dates.",
        "link": "https://support.hp.com/us-en" + v["targetUrl"] if v.get("targetUrl") else "https://support.hp.com/us-en/check-warranty",
    }


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
        serial = (qs.get("serial") or [""])[0].strip().upper()
        try:
            if url.path in ("/api/lenovo", "/api/hp"):
                if not serial.isalnum():
                    return self.send(200, {"ok": False, "error": "That doesn't look like a serial number."})
                return self.send(200, (lenovo if url.path == "/api/lenovo" else hp)(serial))
            if url.path == "/api/this":
                return self.send(200, this_computer("root" in qs))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            return self.send(200, {"ok": False, "error": f"Couldn't reach the brand's server ({e})."})
        name = "index.html" if url.path == "/" else url.path.lstrip("/")
        path = os.path.realpath(os.path.join(STATIC, name))
        if not path.startswith(STATIC + os.sep) or not os.path.isfile(path):
            return self.send(404, b"not found", "text/plain")
        with open(path, "rb") as f:
            self.send(200, f.read(), TYPES.get(os.path.splitext(path)[1], "application/octet-stream"))


if __name__ == "__main__":
    print(f"Warranty check on http://127.0.0.1:{PORT}", file=sys.stderr)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
