import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ros2_trashbot_behavior.remote_bridge_protocol import parse_bool


API_VERSION = "slice2.operator.v1"

OPERATOR_PROMPTS = {
    "waiting_for_trash": {
        "phone_copy": "Waiting for trash. Place trash on the robot, then start delivery.",
        "speaker_prompt": "Please place trash on the robot.",
    },
    "loaded_and_ready": {
        "phone_copy": "Trash is loaded. Ready to deliver.",
        "speaker_prompt": "Trash loaded. Preparing to depart.",
    },
    "delivering": {
        "phone_copy": "Delivering to the selected trash station.",
        "speaker_prompt": "Delivering trash now.",
    },
    "arrived_at_station": {
        "phone_copy": "Arrived. Remove or dispose of the load, then confirm dropoff.",
        "speaker_prompt": "Arrived at the trash station. Please remove the trash.",
    },
    "returning": {
        "phone_copy": "Dropoff confirmed. Returning or waiting for the next task.",
        "speaker_prompt": "Dropoff confirmed. Returning now.",
    },
    "completed": {
        "phone_copy": "Task completed.",
        "speaker_prompt": "Task completed.",
    },
    "canceling": {
        "phone_copy": "Cancel request sent. Waiting for the robot to stop.",
        "speaker_prompt": "Cancel request sent.",
    },
    "canceled": {
        "phone_copy": "Task canceled. The robot is stopped or returning to standby.",
        "speaker_prompt": "Task canceled.",
    },
    "failed": {
        "phone_copy": "Task failed. Check diagnostics or request help.",
        "speaker_prompt": "Task failed. Please check the phone.",
    },
    "needs_human_help": {
        "phone_copy": "Human help is required. Follow the shown instruction.",
        "speaker_prompt": "Human help is required.",
    },
    "diagnostics_ready": {
        "phone_copy": "Diagnostics are ready. Share this support package if help is needed.",
        "speaker_prompt": "Diagnostics are ready.",
    },
}


def operator_prompt_for_state(state):
    return dict(OPERATOR_PROMPTS.get(str(state or ""), OPERATOR_PROMPTS["needs_human_help"]))

HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trashbot Operator</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #172026;
      --muted: #60707c;
      --line: #d7dee3;
      --accent: #126b5f;
      --accent-ink: #ffffff;
      --danger: #b42318;
      --warn: #9a5b00;
      --ok: #1d7f4f;
    }
    * { box-sizing: border-box; }
    body {
      background: var(--bg);
      color: var(--ink);
      font-family: system-ui, -apple-system, Segoe UI, sans-serif;
      margin: 0;
    }
    main {
      display: grid;
      gap: 14px;
      margin: 0 auto;
      max-width: 860px;
      padding: 14px;
    }
    header {
      align-items: center;
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }
    h1 { font-size: 22px; margin: 0; }
    h2 { font-size: 15px; margin: 0 0 10px; }
    button, input {
      border-radius: 8px;
      font: inherit;
      min-height: 44px;
      padding: 10px 12px;
    }
    button {
      background: #eef3f4;
      border: 1px solid var(--line);
      color: var(--ink);
      cursor: pointer;
      font-weight: 650;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: var(--accent-ink);
    }
    button.danger { color: var(--danger); }
    button:disabled {
      color: #7b878f;
      cursor: not-allowed;
      opacity: 0.55;
    }
    label { color: var(--muted); display: grid; gap: 6px; font-size: 13px; }
    input { border: 1px solid var(--line); width: 100%; }
    canvas {
      background: #fbfcfc;
      border: 1px solid var(--line);
      border-radius: 8px;
      display: block;
      height: 260px;
      max-width: 100%;
      width: 100%;
    }
    pre {
      background: #111820;
      border-radius: 8px;
      color: #edf2f7;
      font-size: 12px;
      margin: 0;
      max-height: 280px;
      overflow: auto;
      padding: 12px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .status {
      align-items: start;
      display: grid;
      gap: 10px;
      grid-template-columns: minmax(0, 1fr) auto;
    }
    .stateBadge {
      background: #edf7f5;
      border: 1px solid #c7e3dd;
      border-radius: 999px;
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      padding: 6px 10px;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .stateBadge.problem {
      background: #fff4ef;
      border-color: #f3c8bb;
      color: var(--danger);
    }
    .message { color: var(--muted); margin: 4px 0 0; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .row button { flex: 1 1 150px; }
    .steps {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }
    .step {
      border-bottom: 3px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      min-height: 44px;
      padding: 4px 0 8px;
    }
    .step.active {
      border-color: var(--accent);
      color: var(--ink);
      font-weight: 750;
    }
    .step.done { border-color: var(--ok); color: var(--ink); }
    .telemetry, .diagnosticGrid {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-top: 12px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
    }
    .metric span {
      color: var(--muted);
      display: block;
      font-size: 12px;
      margin-bottom: 3px;
    }
    .metric strong { overflow-wrap: anywhere; }
    .supportList {
      color: var(--muted);
      font-size: 13px;
      margin: 8px 0 0;
      padding-left: 18px;
    }
    [hidden] { display: none; }
    @media (max-width: 560px) {
      main { padding: 10px; }
      header { align-items: start; flex-direction: column; }
      .status { grid-template-columns: 1fr; }
      .steps { grid-template-columns: 1fr; }
      .telemetry, .diagnosticGrid { grid-template-columns: 1fr; }
      canvas { height: 220px; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Trashbot Operator</h1>
        <p class="message">Phone control for trash delivery</p>
      </div>
      <span id="connectionState" class="stateBadge">loading</span>
    </header>
    <section class="panel status">
      <div>
        <span id="stateBadge" class="stateBadge">waiting</span>
        <h2 id="stateTitle">Waiting for trash</h2>
        <p id="stateMessage" class="message">Place trash on the robot, then start delivery.</p>
        <p class="message">Speaker: <strong id="speakerPrompt">Please place trash on the robot.</strong></p>
      </div>
      <label>Trash station
        <input id="target" value="trash_station" autocomplete="off">
      </label>
    </section>
    <section class="panel">
      <div class="steps" id="journeySteps">
        <div class="step" data-step="waiting">1. Load trash</div>
        <div class="step" data-step="delivering">2. Deliver</div>
        <div class="step" data-step="dropoff">3. Dropoff</div>
        <div class="step" data-step="returning">4. Return</div>
        <div class="step" data-step="completed">5. Complete</div>
      </div>
      <div class="row">
        <button id="collectButton" class="primary" onclick="collect()">Start Delivery</button>
        <button id="dropoffButton" onclick="confirmDropoff()">Confirm Dropoff</button>
        <button id="cancelButton" class="danger" onclick="cancelTask()">Cancel</button>
        <button id="diagnosticsButton" onclick="diagnostics()">Diagnostics</button>
      </div>
    </section>
    <section class="panel">
      <h2>Robot Location</h2>
      <div id="locationPanel" class="telemetry" hidden>
        <div class="metric"><span>Frame</span><strong id="locationFrame">unknown</strong></div>
        <div class="metric"><span>Updated</span><strong id="poseAge">no pose</strong></div>
        <div class="metric"><span>X</span><strong id="locationX">-</strong></div>
        <div class="metric"><span>Y</span><strong id="locationY">-</strong></div>
        <div class="metric"><span>Yaw</span><strong id="locationYaw">-</strong></div>
        <div class="metric"><span>Path</span><strong id="pathCount">0 points</strong></div>
      </div>
      <canvas id="robotMap" width="640" height="260"></canvas>
    </section>
    <section id="diagnosticsPanel" class="panel" hidden>
      <h2>Support Diagnostics</h2>
      <div class="diagnosticGrid">
        <div class="metric"><span>Software</span><strong id="diagSoftware">-</strong></div>
        <div class="metric"><span>Map</span><strong id="diagMap">-</strong></div>
        <div class="metric"><span>Route</span><strong id="diagRoute">-</strong></div>
        <div class="metric"><span>Failure</span><strong id="diagFailure">-</strong></div>
        <div class="metric"><span>Task record</span><strong id="diagTask">-</strong></div>
        <div class="metric"><span>Status file</span><strong id="diagStatusFile">-</strong></div>
        <div class="metric"><span>Vision samples</span><strong id="diagVisionSamples">-</strong></div>
        <div class="metric"><span>Latest vision sample</span><strong id="diagLatestVisionSample">-</strong></div>
      </div>
      <ul id="diagRefs" class="supportList"></ul>
    </section>
    <section class="panel">
      <h2>Raw Status</h2>
      <pre id="status">loading...</pre>
    </section>
  </main>
<script>
const STATE_COPY = {
  waiting_for_trash: ['Waiting for trash', 'Place trash on the robot, then start delivery.', 'waiting'],
  loaded_and_ready: ['Trash loaded', 'Ready to deliver to the selected trash station.', 'waiting'],
  delivering: ['Delivering', 'The robot is moving to the trash station.', 'delivering'],
  navigating: ['Delivering', 'The robot is moving to the trash station.', 'delivering'],
  arrived_at_station: ['Arrived', 'Remove or dispose of the load, then confirm dropoff.', 'dropoff'],
  dropoff: ['Confirm dropoff', 'Remove or dispose of the load, then confirm dropoff.', 'dropoff'],
  returning: ['Returning', 'Dropoff is confirmed. The robot is returning or waiting.', 'returning'],
  completed: ['Task completed', 'The robot is ready for the next delivery.', 'completed'],
  canceling: ['Canceling', 'Cancel request sent. Waiting for the robot to stop.', 'returning'],
  canceled: ['Canceled', 'The robot is stopped or returning to standby.', 'completed'],
  failed: ['Needs help', 'Task failed. Open diagnostics or request help.', 'dropoff'],
  needs_human_help: ['Needs help', 'Human help is required. Follow the shown instruction.', 'dropoff'],
  network_error: ['Connection issue', 'The phone cannot reach the robot control page.', 'waiting']
};
const STEP_ORDER = ['waiting', 'delivering', 'dropoff', 'returning', 'completed'];
function fmt(value) {
  return Number.isFinite(value) ? value.toFixed(2) : '-';
}
function text(value, fallback) {
  const normalized = String(value || '').trim();
  return normalized || fallback;
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
function updateJourney(payload) {
  const state = String(payload.state || 'waiting_for_trash');
  const copy = STATE_COPY[state] || [state.replaceAll('_', ' '), payload.message || '', 'waiting'];
  const step = copy[2];
  const activeIndex = STEP_ORDER.indexOf(step);
  const stateBadge = document.getElementById('stateBadge');
  stateBadge.textContent = state;
  stateBadge.classList.toggle('problem', state === 'failed' || state === 'needs_human_help' || state === 'network_error');
  document.getElementById('stateTitle').textContent = copy[0];
  document.getElementById('stateMessage').textContent = text(payload.phone_copy, text(payload.message, copy[1]));
  document.getElementById('speakerPrompt').textContent = text(payload.speaker_prompt, 'No speaker prompt.');
  document.getElementById('connectionState').textContent = state === 'network_error' ? 'offline' : 'online';
  document.querySelectorAll('#journeySteps .step').forEach((node) => {
    const index = STEP_ORDER.indexOf(node.dataset.step);
    node.classList.toggle('active', index === activeIndex);
    node.classList.toggle('done', activeIndex >= 0 && index < activeIndex);
  });
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
  updateJourney(payload);
  showTelemetry(payload);
  const collectButton = document.getElementById('collectButton');
  const dropoffButton = document.getElementById('dropoffButton');
  const cancelButton = document.getElementById('cancelButton');
  collectButton.disabled = !Boolean(payload.can_collect);
  dropoffButton.disabled = !Boolean(payload.can_confirm_dropoff);
  cancelButton.disabled = !Boolean(payload.can_cancel);
}
function showDiagnostics(payload) {
  const panel = document.getElementById('diagnosticsPanel');
  panel.hidden = false;
  const failure = payload.failure || {};
  const latest = payload.latest_status || {};
  const visionSamples = payload.vision_samples || {};
  const refs = Array.isArray(payload.log_refs) ? payload.log_refs : [];
  const taskRecord = failure.task_record_path || (payload.last_task || {}).task_record_path || latest.task_record_path || '';
  document.getElementById('diagSoftware').textContent = text(payload.software_version, 'not reported');
  document.getElementById('diagMap').textContent = text(payload.map_version, 'not reported');
  document.getElementById('diagRoute').textContent = text(payload.route_version, 'not reported');
  document.getElementById('diagFailure').textContent = text(failure.error_code || failure.message, 'none reported');
  document.getElementById('diagTask').textContent = text(taskRecord, 'not reported');
  document.getElementById('diagStatusFile').textContent = text(payload.operator_status_file, 'not reported');
  document.getElementById('diagVisionSamples').textContent = visionSamples.read_error
    ? visionSamples.read_error
    : `${Number(visionSamples.sample_count || 0)} samples`;
  document.getElementById('diagLatestVisionSample').textContent = text(
    visionSamples.latest_sample_ref,
    visionSamples.sample_count ? 'sample reference missing' : 'no samples'
  );
  const refList = document.getElementById('diagRefs');
  refList.innerHTML = '';
  [...refs, payload.vision_sample_manifest_ref].filter(Boolean).forEach((ref) => {
    const item = document.createElement('li');
    item.textContent = ref;
    refList.appendChild(item);
  });
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
async function diagnostics() {
  const payload = await api('/api/diagnostics');
  if (payload) showDiagnostics(payload);
}
setInterval(refresh, 1000);
refresh();
</script>
</body>
</html>"""


def status_payload(state, message="", **extra):
    prompt = operator_prompt_for_state(state)
    payload = {
        "api_version": API_VERSION,
        "state": state,
        "message": message,
        "phone_copy": prompt["phone_copy"],
        "speaker_prompt": prompt["speaker_prompt"],
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
