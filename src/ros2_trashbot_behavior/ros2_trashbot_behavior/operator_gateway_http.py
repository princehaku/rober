import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ros2_trashbot_behavior.remote_bridge_protocol import parse_bool


API_VERSION = "slice2.operator.v1"

HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trashbot Operator</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; max-width: 720px; }
    button, input { font: inherit; padding: 10px; margin: 4px 0; }
    button { min-width: 140px; }
    label { display: block; margin-top: 12px; }
    canvas { border: 1px solid #999; display: block; height: 260px; max-width: 100%; width: 100%; }
    pre { background: #111; color: #eee; padding: 14px; overflow: auto; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
    .telemetry { display: grid; gap: 8px; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 12px 0; }
    .telemetry div { border: 1px solid #ddd; padding: 10px; }
    [hidden] { display: none; }
  </style>
</head>
<body>
  <h1>Trashbot Operator</h1>
  <label>Delivery target <input id="target" value="trash_station"></label>
  <div class="row">
    <button id="collectButton" onclick="collect()">Start Delivery</button>
    <button id="dropoffButton" onclick="confirmDropoff()">Confirm Dropoff</button>
    <button id="cancelButton" onclick="cancelTask()">Cancel</button>
    <button id="diagnosticsButton" onclick="diagnostics()">Diagnostics</button>
  </div>
  <div id="locationPanel" class="telemetry" hidden>
    <div>Frame <strong id="locationFrame">unknown</strong></div>
    <div>Updated <strong id="poseAge">no pose</strong></div>
    <div>X <strong id="locationX">-</strong></div>
    <div>Y <strong id="locationY">-</strong></div>
    <div>Yaw <strong id="locationYaw">-</strong></div>
    <div>Path <strong id="pathCount">0 points</strong></div>
  </div>
  <canvas id="robotMap" width="640" height="260"></canvas>
  <pre id="status">loading...</pre>
<script>
function fmt(value) {
  return Number.isFinite(value) ? value.toFixed(2) : '-';
}
function drawMap(payload) {
  const canvas = document.getElementById('robotMap');
  const ctx = canvas.getContext('2d');
  const path = Array.isArray(payload.robot_path) ? payload.robot_path : [];
  const location = payload.robot_location || payload.location;
  const pose = payload.robot_pose || location || null;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#ddd';
  ctx.lineWidth = 1;
  for (let x = 0; x < canvas.width; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
  if (!pose && path.length === 0) {
    ctx.fillStyle = '#666';
    ctx.fillText('waiting for /amcl_pose', 16, 24);
    return;
  }
  const points = path.length ? path : [pose];
  const xs = points.map(p => Number(p.x)).filter(Number.isFinite);
  const ys = points.map(p => Number(p.y)).filter(Number.isFinite);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const span = Math.max(maxX - minX, maxY - minY, 1);
  const pad = 24;
  const project = p => ({
    x: pad + ((Number(p.x) - minX) / span) * (canvas.width - pad * 2),
    y: canvas.height - pad - ((Number(p.y) - minY) / span) * (canvas.height - pad * 2)
  });
  ctx.strokeStyle = '#2364aa';
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach((p, index) => {
    const q = project(p);
    if (index === 0) ctx.moveTo(q.x, q.y);
    else ctx.lineTo(q.x, q.y);
  });
  ctx.stroke();
  if (pose) {
    const q = project(pose);
    ctx.fillStyle = '#d7263d';
    ctx.beginPath(); ctx.arc(q.x, q.y, 7, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#d7263d';
    ctx.beginPath();
    ctx.moveTo(q.x, q.y);
    ctx.lineTo(q.x + Math.cos(Number(pose.yaw || 0)) * 22, q.y - Math.sin(Number(pose.yaw || 0)) * 22);
    ctx.stroke();
  }
}
function showTelemetry(payload) {
  const location = payload.robot_location || payload.location;
  const pose = payload.robot_pose || location || null;
  const locationPanel = document.getElementById('locationPanel');
  locationPanel.hidden = !location;
  if (payload.robot_pose) {
    locationPanel.hidden = false;
  }
  document.getElementById('locationFrame').textContent = pose ? pose.frame_id : 'unknown';
  document.getElementById('locationX').textContent = pose ? fmt(Number(pose.x)) : '-';
  document.getElementById('locationY').textContent = pose ? fmt(Number(pose.y)) : '-';
  document.getElementById('locationYaw').textContent = pose ? fmt(Number(pose.yaw)) : '-';
  document.getElementById('pathCount').textContent = `${Array.isArray(payload.robot_path) ? payload.robot_path.length : 0} points`;
  document.getElementById('poseAge').textContent = pose ? new Date(Number(pose.updated_at || 0) * 1000).toLocaleTimeString() : 'no pose';
  drawMap(payload);
}
function showStatus(payload) {
  document.getElementById('status').textContent = JSON.stringify(payload, null, 2);
  showTelemetry(payload);
  const collectButton = document.getElementById('collectButton');
  const dropoffButton = document.getElementById('dropoffButton');
  const cancelButton = document.getElementById('cancelButton');
  collectButton.disabled = !Boolean(payload.can_collect);
  dropoffButton.disabled = !Boolean(payload.can_confirm_dropoff);
  cancelButton.disabled = !Boolean(payload.can_cancel);
}
async function api(path, options) {
  try {
    const response = await fetch(path, options || {});
    const payload = await response.json();
    showStatus(payload);
    return payload;
  } catch (error) {
    showStatus({
      state: 'network_error',
      message: String(error),
      can_collect: false,
      can_confirm_dropoff: false,
      can_cancel: false
    });
    return null;
  }
}
async function refresh() { await api('/api/status'); }
async function collect() {
  await api('/api/collect', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target: document.getElementById('target').value})
  });
}
async function confirmDropoff() { await api('/api/dropoff/confirm', {method: 'POST'}); }
async function cancelTask() { await api('/api/cancel', {method: 'POST'}); }
async function diagnostics() { await api('/api/diagnostics'); }
setInterval(refresh, 1000);
refresh();
</script>
</body>
</html>"""


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
    try:
        length = int(handler.headers.get("Content-Length") or 0)
    except ValueError as exc:
        raise ValueError(f"invalid Content-Length: {exc}") from exc
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
            if path == "/" or path == "/index.html":
                body = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/api/status":
                self._send_json(200, gateway.snapshot())
                return
            if path == "/api/diagnostics":
                self._send_json(200, gateway.diagnostics())
                return
            self._send_json(404, status_payload("not_found", f"unknown path: {path}"))

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            try:
                body = parse_json_body(self)
            except (ValueError, json.JSONDecodeError) as exc:
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
                try:
                    accepted = parse_bool(body.get("accepted"), default=True)
                except ValueError as exc:
                    self._send_json(400, status_payload("bad_request", str(exc)))
                    return
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
