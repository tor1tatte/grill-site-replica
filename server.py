#!/usr/bin/env python3
"""Local preview server: serves site/ and accepts leads at POST /api/lead.

  python3 server.py [port]          # default 8000, bound to 127.0.0.1

Leads are appended to leads.jsonl (outside site/, never served).
Checks: JSON only, 4 KB body cap, honeypot, phone/consent validation,
5 requests per minute per IP. For production put this behind a real host,
or point <meta name="lead-endpoint"> at your own CRM / Telegram-bot webhook.
"""
import http.server
import json
import pathlib
import re
import sys
import time
import functools

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "site"
LEADS = ROOT / "leads.jsonl"
hits = {}


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % a))

    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        if self.path != "/api/lead":
            return self._json(404, {"ok": False})
        ip = self.client_address[0]
        now = time.time()
        recent = [t for t in hits.get(ip, []) if now - t < 60]
        if len(recent) >= 5:
            return self._json(429, {"ok": False, "error": "rate"})
        hits[ip] = recent + [now]
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n <= 0 or n > 4096:
                return self._json(413, {"ok": False})
            d = json.loads(self.rfile.read(n))
            if not isinstance(d, dict):
                raise ValueError
        except Exception:
            return self._json(400, {"ok": False})
        if d.get("website"):  # honeypot: pretend success, store nothing
            return self._json(200, {"ok": True})
        digits = re.sub(r"\D", "", str(d.get("phone", "")))
        if len(digits) != 11 or d.get("consent") is not True:
            return self._json(422, {"ok": False})
        rec = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "name": str(d.get("name", ""))[:80],
            "phone": "+" + digits,
            "email": str(d.get("email", ""))[:120],
            "source": str(d.get("source", ""))[:40],
            "product": str(d.get("product", ""))[:120],
            "page": str(d.get("page", ""))[:120],
            "consent": True,
        }
        with open(LEADS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._json(200, {"ok": True})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(H, directory=str(SITE))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as s:
        print(f"http://127.0.0.1:{port}/  (leads -> {LEADS})")
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            pass
