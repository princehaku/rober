import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Trashbot Route Debug</title></head>
<body>
<h2>Trashbot Fixed Route Debug</h2>
<pre id="status">loading...</pre>
<script>
async function refresh() {
  try {
    const r = await fetch('/api/status');
    const j = await r.json();
    document.getElementById('status').innerText = JSON.stringify(j, null, 2);
  } catch (e) {
    document.getElementById('status').innerText = 'load failed: ' + e;
  }
}
setInterval(refresh, 1000);
refresh();
</script>
</body></html>"""


def make_handler(status_file: str):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload):
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/' or path == '/index.html':
                body = HTML.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == '/api/status':
                if not os.path.exists(status_file):
                    self._send_json({'state': 'missing_status_file', 'status_file': status_file})
                    return
                try:
                    with open(status_file, 'r', encoding='utf-8') as f:
                        self._send_json(json.load(f))
                except (OSError, json.JSONDecodeError) as exc:
                    self._send_json({
                        'state': 'invalid_status_file',
                        'status_file': status_file,
                        'error': str(exc),
                    })
                return
            self.send_response(404)
            self.end_headers()

    return Handler


def main():
    status_file = os.environ.get('TRASHBOT_STATUS_FILE', '/tmp/trashbot_fixed_route_status.json')
    host = os.environ.get('TRASHBOT_WEB_HOST', '0.0.0.0')
    port = int(os.environ.get('TRASHBOT_WEB_PORT', '8765'))
    server = HTTPServer((host, port), make_handler(status_file))
    print(f'Route debug web on http://{host}:{port} status={status_file}')
    server.serve_forever()


if __name__ == '__main__':
    main()

