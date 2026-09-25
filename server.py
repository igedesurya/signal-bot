"""Server kecil: sajikan dashboard + proxy Yahoo (biar lolos CORS browser). Stdlib only."""
import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (signal-bot/0.1)"}


def yahoo_url(symbol, interval, period1=None, period2=None, rng=None):
    q = {"interval": interval}
    if period1 is not None and period2 is not None:
        q["period1"] = str(int(period1))
        q["period2"] = str(int(period2))
    elif rng:
        q["range"] = rng
    else:
        q["range"] = "3mo"
    return "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol, safe=".-") + "?" + urllib.parse.urlencode(q)


class H(BaseHTTPRequestHandler):
    server_version = "signalbot/0.2"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        raw = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/health":
            return self._send(200, json.dumps({"ok": True}))
        if u.path == "/api/yahoo":
            qs = urllib.parse.parse_qs(u.query)
            sym = (qs.get("symbol") or [""])[0]
            interval = (qs.get("interval") or ["1d"])[0]
            p1 = (qs.get("period1") or [None])[0]
            p2 = (qs.get("period2") or [None])[0]
            rng = (qs.get("range") or [None])[0]
            if not sym:
                return self._send(400, json.dumps({"error": "symbol required"}))
            try:
                url = yahoo_url(sym, interval, p1, p2, rng)
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=25) as r:
                    data = r.read()
                return self._send(200, data)
            except Exception as e:
                return self._send(502, json.dumps({"error": f"yahoo fetch failed: {e}"}))
        # static
        path = "/index.html" if u.path == "/" else u.path
        f = ROOT / path.lstrip("/")
        if not str(f.resolve()).startswith(str(ROOT.resolve())):
            return self._send(404, "not found", "text/plain")
        if not f.exists() or f.is_dir():
            f = ROOT / "dashboard.html"
        ctype = "text/html"
        if f.suffix == ".js":
            ctype = "text/javascript"
        elif f.suffix == ".json":
            ctype = "application/json"
        return self._send(200, f.read_bytes(), ctype)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "8087"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), H)
    print(f"signal-bot on :{port}")
    srv.serve_forever()
