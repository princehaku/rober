import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trashbot Route Debug</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #64748b;
      --line: #d9e1ea;
      --ok: #18794e;
      --ok-bg: #e7f6ee;
      --warn: #9a5b00;
      --warn-bg: #fff4d8;
      --error: #b42318;
      --error-bg: #fde8e7;
      --muted-bg: #eef2f6;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
    }
    main {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 40px;
    }
    header {
      display: flex;
      flex-wrap: wrap;
      gap: 12px 18px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 18px;
    }
    h1 {
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
      letter-spacing: 0;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 14px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .badge.ok { color: var(--ok); background: var(--ok-bg); }
    .badge.warning { color: var(--warn); background: var(--warn-bg); }
    .badge.error { color: var(--error); background: var(--error-bg); }
    .badge.muted { color: var(--muted); background: var(--muted-bg); }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      min-width: 0;
    }
    section.full { grid-column: 1 / -1; }
    h2 {
      margin: 0 0 12px;
      font-size: 15px;
      line-height: 1.25;
      letter-spacing: 0;
    }
    dl {
      display: grid;
      grid-template-columns: minmax(120px, 0.35fr) minmax(0, 1fr);
      gap: 8px 12px;
      margin: 0;
      align-items: start;
    }
    dt {
      color: var(--muted);
      font-size: 13px;
    }
    dd {
      margin: 0;
      min-width: 0;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }
    .summary {
      margin: 0;
      color: var(--muted);
      overflow-wrap: anywhere;
    }
    progress {
      width: 100%;
      height: 16px;
      margin: 4px 0 10px;
    }
    ul {
      margin: 0;
      padding-left: 18px;
    }
    li {
      margin: 3px 0;
      overflow-wrap: anywhere;
    }
    pre {
      margin: 0;
      max-height: 420px;
      overflow: auto;
      padding: 12px;
      border-radius: 6px;
      background: #101820;
      color: #e6edf3;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    @media (max-width: 720px) {
      main {
        width: min(100% - 20px, 1120px);
        padding-top: 16px;
      }
      .grid { grid-template-columns: 1fr; }
      dl { grid-template-columns: 1fr; gap: 3px 0; }
      h1 { font-size: 21px; }
    }
  </style>
</head>
<body>
<main>
  <header>
    <h1>Trashbot Fixed Route Debug</h1>
    <span id="routeStateBadge" class="badge muted">Loading</span>
  </header>
  <div class="grid">
    <section class="full">
      <h2>Route Summary</h2>
      <p id="routeSummary" class="summary">loading...</p>
      <dl>
        <dt>Updated</dt><dd id="routeUpdatedAt">not provided</dd>
        <dt>Route file</dt><dd id="routeFile">not provided</dd>
        <dt>Keyframe dir</dt><dd id="keyframeDir">not provided</dd>
        <dt>Contract</dt><dd id="routeContract">not provided</dd>
      </dl>
    </section>
    <section>
      <h2>Checkpoint</h2>
      <div id="routeProgress">not provided</div>
    </section>
    <section>
      <h2>Current Target</h2>
      <dl id="routeTarget"></dl>
    </section>
    <section>
      <h2>Visual Gate</h2>
      <dl id="visualGateStatus"></dl>
    </section>
    <section>
      <h2>Keyframe Preflight</h2>
      <div id="keyframePreflight">not provided</div>
    </section>
    <section>
      <h2>Failure Reason</h2>
      <dl>
        <dt>Failure</dt><dd id="routeFailureReason">not provided</dd>
        <dt>Last error</dt><dd id="routeLastError">not provided</dd>
        <dt>Last transition</dt><dd id="routeLastTransition">not provided</dd>
        <dt>Last nav result</dt><dd id="routeLastNavResult">not provided</dd>
      </dl>
    </section>
    <section>
      <h2>Recent Task</h2>
      <dl id="recentTask"></dl>
    </section>
    <section class="full">
      <h2>Raw Status</h2>
      <pre id="rawStatus">loading...</pre>
    </section>
  </div>
</main>
<script>
const missing = 'not provided';

function valueOrMissing(value) {
  if (value === undefined || value === null || value === '') {
    return missing;
  }
  return String(value);
}

function setText(id, value) {
  document.getElementById(id).innerText = valueOrMissing(value);
}

function dlRow(label, value) {
  return '<dt>' + escapeHtml(label) + '</dt><dd>' + escapeHtml(valueOrMissing(value)) + '</dd>';
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function formatUpdatedAt(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return new Date(value * 1000).toLocaleString();
  }
  return valueOrMissing(value);
}

function routeStateView(status) {
  const state = status && status.state;
  if (state === 'completed') {
    return { label: 'Completed', tone: 'ok' };
  }
  if (state === 'ready') {
    return { label: 'Active', tone: 'ok' };
  }
  if (state === 'running') {
    return { label: 'Active', tone: 'warning' };
  }
  if (state === 'waiting_visual_gate') {
    return { label: 'Waiting visual gate', tone: 'warning' };
  }
  if (state === 'error' || state === 'invalid_status_file') {
    return { label: 'Error', tone: 'error' };
  }
  if (state === 'missing_status_file') {
    return { label: 'Missing status', tone: 'muted' };
  }
  return { label: 'Unknown', tone: 'muted' };
}

function visualGateView(status) {
  const gate = status && status.visual_gate_status;
  const checkpoint = status && status.visual_gate_checkpoint;
  const detail = status && status.visual_gate_detail;
  const labels = {
    disabled: 'Disabled by parameter',
    passed: 'Passed',
    waiting_camera_frame: 'Waiting camera frame',
    keyframe_preflight_failed: 'Keyframe preflight failed',
    insufficient_matches: 'Insufficient matches',
    no_live_descriptors: 'No live descriptors',
    missing_keyframe: 'Missing keyframe',
    not_checked: 'Not checked'
  };
  return {
    label: labels[gate] || valueOrMissing(gate),
    checkpoint: checkpoint === undefined || checkpoint === null ? missing : checkpoint,
    detail: detail || status.failure_reason || status.last_error || missing,
    enabled: status.enable_visual_gate === undefined ? missing : status.enable_visual_gate
  };
}

function renderKeyframeList(items) {
  if (!Array.isArray(items) || items.length === 0) {
    return '<span>none</span>';
  }
  return '<ul>' + items.map((item) => {
    if (item && typeof item === 'object') {
      const index = item.index === undefined ? '?' : item.index;
      const reason = item.reason ? ': ' + item.reason : '';
      return '<li>' + escapeHtml(index + reason) + '</li>';
    }
    return '<li>' + escapeHtml(item) + '</li>';
  }).join('') + '</ul>';
}

function renderKeyframePreflight(preflight) {
  if (!preflight || typeof preflight !== 'object') {
    document.getElementById('keyframePreflight').innerText = missing;
    return;
  }
  const loaded = Array.isArray(preflight.loaded_keyframes) ? preflight.loaded_keyframes.length : 0;
  const html = [
    '<dl>',
    dlRow('Enabled', preflight.enabled),
    dlRow('Route visual ready', preflight.route_visual_ready),
    dlRow('Total checkpoints', preflight.total_checkpoints),
    dlRow('Loaded keyframes', loaded),
    '<dt>Missing</dt><dd>' + renderKeyframeList(preflight.missing_keyframes) + '</dd>',
    '<dt>Invalid</dt><dd>' + renderKeyframeList(preflight.invalid_keyframes) + '</dd>',
    '</dl>'
  ].join('');
  document.getElementById('keyframePreflight').innerHTML = html;
}

function renderProgress(status) {
  const current = Number(status.current_index);
  const total = Number(status.total);
  if (!Number.isFinite(current) || !Number.isFinite(total) || total <= 0) {
    document.getElementById('routeProgress').innerText = missing;
    return;
  }
  const capped = Math.min(Math.max(current, 0), total);
  document.getElementById('routeProgress').innerHTML =
    '<progress max="' + escapeHtml(total) + '" value="' + escapeHtml(capped) + '"></progress>' +
    '<div>' + escapeHtml(capped + ' / ' + total + ' checkpoints') + '</div>';
}

function recentTaskView(status) {
  const lastTask = status.last_task || {};
  const task = status.task || {};
  const record = status.task_record_path || lastTask.task_record_path;
  const fallbackId = task.id || lastTask.task_id || lastTask.id;
  return {
    reference: record || fallbackId || missing,
    source: record ? 'task_record_path' : (fallbackId ? 'task id' : missing),
    lastTaskState: lastTask.state || lastTask.status || missing,
    navResults: status.nav_results ? JSON.stringify(status.nav_results) : missing
  };
}

function renderStatus(status) {
  const view = routeStateView(status);
  const badge = document.getElementById('routeStateBadge');
  badge.className = 'badge ' + view.tone;
  badge.innerText = view.label;

  setText('routeSummary',
    valueOrMissing(status.state) + ' route in ' + valueOrMissing(status.mode) +
    ' mode at checkpoint ' + valueOrMissing(status.current_index) +
    ' of ' + valueOrMissing(status.total));
  setText('routeUpdatedAt', formatUpdatedAt(status.updated_at));
  setText('routeFile', status.route_file);
  setText('keyframeDir', status.keyframe_dir);
  setText('routeContract', status.route_contract_version);
  renderProgress(status);

  const target = status.current_target || {};
  document.getElementById('routeTarget').innerHTML = [
    dlRow('Index', target.index),
    dlRow('X', target.x),
    dlRow('Y', target.y),
    dlRow('Z', target.z),
    dlRow('Quaternion', [target.qx, target.qy, target.qz, target.qw].map(valueOrMissing).join(', '))
  ].join('');

  const gate = visualGateView(status);
  document.getElementById('visualGateStatus').innerHTML = [
    dlRow('Status', gate.label),
    dlRow('Enabled', gate.enabled),
    dlRow('Checkpoint', gate.checkpoint),
    dlRow('Detail', gate.detail)
  ].join('');
  renderKeyframePreflight(status.keyframe_preflight);

  setText('routeFailureReason', status.failure_reason);
  setText('routeLastError', status.last_error);
  setText('routeLastTransition', status.last_transition);
  setText('routeLastNavResult', status.last_nav_result);

  const recentTask = recentTaskView(status);
  document.getElementById('recentTask').innerHTML = [
    dlRow('Reference', recentTask.reference),
    dlRow('Source', recentTask.source),
    dlRow('Last task state', recentTask.lastTaskState),
    dlRow('Nav results', recentTask.navResults)
  ].join('');
  document.getElementById('rawStatus').innerText = JSON.stringify(status, null, 2);
}

async function refresh() {
  try {
    const response = await fetch('/api/status');
    const status = await response.json();
    renderStatus(status);
  } catch (error) {
    const status = {
      state: 'invalid_status_file',
      failure_reason: 'load failed: ' + error
    };
    renderStatus(status);
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

