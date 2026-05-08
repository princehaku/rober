import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse


API_VERSION = "slice2.operator.v1"


def status_payload(state, message="", **extra):
    payload = {
        "api_version": API_VERSION,
        "state": state,
        "message": message,
        "updated_at": time.time(),
    }
    payload.update(extra)
    return payload


def parse_json_body(handler):
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8") or "{}")


def make_handler(gateway):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, status, payload):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/status":
                self._send_json(200, gateway.snapshot())
                return
            self._send_json(404, status_payload("not_found", f"unknown path: {path}"))

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            try:
                body = parse_json_body(self)
            except json.JSONDecodeError as exc:
                self._send_json(400, status_payload("bad_request", str(exc)))
                return
            if not isinstance(body, dict):
                self._send_json(400, status_payload("bad_request", "JSON body must be an object"))
                return
            if path == "/api/collect":
                target = body.get("target") or next(iter(query.get("target", [])), "")
                try:
                    trash_type = int(body.get("trash_type", 0) or 0)
                except (TypeError, ValueError) as exc:
                    self._send_json(400, status_payload("bad_request", f"invalid trash_type: {exc}"))
                    return
                status, payload = gateway.start_collection(target, trash_type)
                self._send_json(status, payload)
                return
            if path == "/api/dropoff/confirm":
                accepted = bool(body.get("accepted", True))
                status, payload = gateway.confirm_dropoff(accepted)
                self._send_json(status, payload)
                return
            if path == "/api/cancel":
                status, payload = gateway.cancel_collection()
                self._send_json(status, payload)
                return
            self._send_json(404, status_payload("not_found", f"unknown path: {path}"))

        def log_message(self, _format, *_args):
            return

    return Handler
