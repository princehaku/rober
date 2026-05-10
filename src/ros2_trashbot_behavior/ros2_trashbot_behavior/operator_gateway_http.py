import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ros2_trashbot_behavior.remote_bridge_protocol import parse_bool


API_VERSION = "slice2.operator.v1"
ELEVATOR_ASSIST_SPEAKER_PROMPT = "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,"

ELEVATOR_ASSIST_PHASES = {
    "approaching_elevator",
    "waiting_elevator_open",
    "entering_elevator",
    "requesting_floor_help",
    "waiting_target_floor",
    "exiting_elevator",
    "resume_delivery",
}

ELEVATOR_ASSIST_HELP_STATES = {
    "door_timeout",
    "door_closed_or_unknown",
    "target_floor_unconfirmed",
    "target_floor_evidence_unreliable",
    "unsafe_to_enter",
    "unsafe_to_exit",
    "manual_takeover_required",
}

ELEVATOR_ASSIST_COPY = {
    "approaching_elevator": {
        "phone_copy": "正在前往电梯厅。",
        "speaker_prompt": "前往电梯厅。",
    },
    "waiting_elevator_open": {
        "phone_copy": "已到电梯厅，等待电梯开门。",
        "speaker_prompt": "等待电梯开门。",
    },
    "entering_elevator": {
        "phone_copy": "正在进入电梯，请保持通道安全。",
        "speaker_prompt": "正在进入电梯。",
    },
    "requesting_floor_help": {
        "phone_copy": "已进入电梯，正在请求帮忙按楼层。",
        "speaker_prompt": ELEVATOR_ASSIST_SPEAKER_PROMPT,
    },
    "waiting_target_floor": {
        "phone_copy": "正在等待目标楼层，请保持通道安全。",
        "speaker_prompt": "正在等待目标楼层。",
    },
    "exiting_elevator": {
        "phone_copy": "已到目标楼层，准备驶出。",
        "speaker_prompt": "到达目标楼层，准备驶出。",
    },
    "resume_delivery": {
        "phone_copy": "已驶出电梯，继续送往垃圾站。",
        "speaker_prompt": "已驶出电梯，继续送垃圾。",
    },
    "door_timeout": {
        "phone_copy": "电梯未开门，需要人工协助。",
        "speaker_prompt": "需要人工协助。",
    },
    "door_closed_or_unknown": {
        "phone_copy": "电梯门未确认打开，需要人工协助。",
        "speaker_prompt": "需要人工协助。",
    },
    "target_floor_unconfirmed": {
        "phone_copy": "未确认目标楼层，请人工确认。",
        "speaker_prompt": "未确认目标楼层，需要人工协助。",
    },
    "target_floor_evidence_unreliable": {
        "phone_copy": "目标楼层证据不可靠，请人工确认。",
        "speaker_prompt": "未确认目标楼层，需要人工协助。",
    },
    "unsafe_to_exit": {
        "phone_copy": "目标楼层出口不安全，需要人工接管。",
        "speaker_prompt": "需要人工协助。",
    },
    "manual_takeover_required": {
        "phone_copy": "需要人工接管电梯段任务。",
        "speaker_prompt": "需要人工协助。",
    },
}

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


def _elevator_copy_key(elevator_assist):
    if not isinstance(elevator_assist, dict):
        return ""
    for key in ("state", "phase", "reason"):
        value = str(elevator_assist.get(key) or "").strip()
        if value in ELEVATOR_ASSIST_COPY:
            return value
    return ""


def default_elevator_assist():
    return {
        "enabled": False,
        "mode": "",
        "state": "disabled",
        "phase": "",
        "requires_human_help": False,
        "reason": "",
        "target_floor": "",
        "phone_copy": "",
        "speaker_prompt": "",
        "evidence": {},
        "events": [],
    }


def normalize_elevator_assist(value=None, *, state="", message=""):
    """Return a stable, phone-safe elevator_assist object.

    The behavior layer owns the robot contract; this helper only keeps older
    status payloads compatible while letting new task records pass through the
    same machine-readable shape.
    """
    raw = dict(value) if isinstance(value, dict) else {}
    state_text = str(state or "").strip()
    inferred_phase = state_text if state_text in ELEVATOR_ASSIST_PHASES else ""
    inferred_state = state_text if state_text in ELEVATOR_ASSIST_HELP_STATES else ""

    normalized = default_elevator_assist()
    normalized.update(raw)
    phase = str(raw.get("phase") or inferred_phase or "").strip()
    assist_state = str(raw.get("state") or inferred_state or phase or "").strip()
    reason = str(raw.get("reason") or message or "").strip()
    enabled = bool(raw.get("enabled", False) or phase or assist_state in ELEVATOR_ASSIST_HELP_STATES)
    requires_human_help = bool(
        raw.get("requires_human_help", False)
        or assist_state in ELEVATOR_ASSIST_HELP_STATES
        or phase in ELEVATOR_ASSIST_HELP_STATES
    )

    normalized.update(
        {
            "enabled": enabled,
            "mode": str(raw.get("mode") or ("dry_run" if enabled else "")).strip(),
            "state": assist_state or ("active" if enabled else "disabled"),
            "phase": phase,
            "requires_human_help": requires_human_help,
            "reason": reason,
            "target_floor": str(raw.get("target_floor") or "").strip(),
            "evidence": raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {},
            "events": raw.get("events") if isinstance(raw.get("events"), list) else [],
        }
    )

    copy_key = _elevator_copy_key(normalized)
    copy = dict(ELEVATOR_ASSIST_COPY.get(copy_key, {}))
    if not copy and enabled:
        copy = {
            "phone_copy": "电梯协助流程进行中，请在手机端关注下一步提示。",
            "speaker_prompt": "电梯协助流程进行中。",
        }
    normalized["phone_copy"] = str(raw.get("phone_copy") or copy.get("phone_copy", "")).strip()
    normalized["speaker_prompt"] = str(raw.get("speaker_prompt") or copy.get("speaker_prompt", "")).strip()
    return normalized


def operator_prompt_for_state(state, elevator_assist=None):
    elevator_assist = elevator_assist if isinstance(elevator_assist, dict) else {}
    if elevator_assist.get("enabled") and elevator_assist.get("phone_copy"):
        return {
            "phone_copy": elevator_assist.get("phone_copy", ""),
            "speaker_prompt": elevator_assist.get("speaker_prompt", ""),
        }
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
    button, input, select, textarea {
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
    input, select, textarea { border: 1px solid var(--line); width: 100%; }
    textarea { min-height: 86px; resize: vertical; }
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
    .integrityCard {
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-top: 12px;
      padding: 12px;
    }
    .integrityHeader {
      align-items: center;
      display: flex;
      gap: 10px;
      justify-content: space-between;
    }
    .integrityBadge {
      border: 1px solid var(--line);
      border-radius: 999px;
      font-size: 12px;
      font-weight: 750;
      padding: 5px 9px;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .integrityBadge.ok {
      background: #edf7f0;
      border-color: #b7dfc4;
      color: var(--ok);
    }
    .integrityBadge.warning {
      background: #fff7e6;
      border-color: #f0cf8a;
      color: var(--warn);
    }
    .integrityBadge.error {
      background: #fff1ed;
      border-color: #efb7aa;
      color: var(--danger);
    }
    .integrityBadge.muted {
      background: #eef3f4;
      border-color: var(--line);
      color: var(--muted);
    }
    .integrityCard .supportList li {
      overflow-wrap: anywhere;
    }
    .supportList {
      color: var(--muted);
      font-size: 13px;
      margin: 8px 0 0;
      padding-left: 18px;
    }
    .reviewGrid {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-top: 10px;
    }
    .reviewMeta {
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-top: 10px;
      padding: 10px;
    }
    .reviewMeta code {
      color: var(--ink);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    [hidden] { display: none; }
    @media (max-width: 560px) {
      main { padding: 10px; }
      header { align-items: start; flex-direction: column; }
      .status { grid-template-columns: 1fr; }
      .steps { grid-template-columns: 1fr; }
      .telemetry, .diagnosticGrid { grid-template-columns: 1fr; }
      .reviewGrid { grid-template-columns: 1fr; }
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
        <div class="metric"><span>Review queue</span><strong id="diagReviewQueue">-</strong></div>
        <div class="metric"><span>Next review sample</span><strong id="diagNextReviewSample">-</strong></div>
        <div class="metric"><span>Route proof state</span><strong id="diagRouteProofState">-</strong></div>
        <div class="metric"><span>Route proof summary</span><strong id="diagRouteProofSummary">-</strong></div>
        <div class="metric"><span>Route proof reason</span><strong id="diagRouteProofReason">-</strong></div>
        <div class="metric"><span>Route proof source</span><strong id="diagRouteProofSource">-</strong></div>
        <div class="metric"><span>Elevator assist</span><strong id="diagElevatorAssistState">-</strong></div>
        <div class="metric"><span>Elevator prompt</span><strong id="diagElevatorAssistPrompt">-</strong></div>
        <div class="metric"><span>Elevator evidence</span><strong id="diagElevatorAssistEvidence">-</strong></div>
        <div class="metric"><span>Elevator next step</span><strong id="diagElevatorAssistNextStep">-</strong></div>
      </div>
      <div id="diagVisionIntegrity" class="integrityCard">
        <div class="integrityHeader">
          <h2>Vision evidence chain</h2>
          <span id="diagVisionIntegrityBadge" class="integrityBadge muted">unknown</span>
        </div>
        <p id="diagVisionIntegritySummary" class="message">Diagnostics have not been loaded yet.</p>
        <ul id="diagVisionIntegrityReasons" class="supportList"></ul>
        <p class="message">Context coverage: <strong id="diagVisionContextCoverage">not reported</strong></p>
        <p class="message">File counts: <strong id="diagVisionFileCounts">not reported</strong></p>
        <p class="message">Next step: <strong id="diagVisionIntegrityAdvice">Refresh diagnostics after the robot publishes a support package.</strong></p>
      </div>
      <div id="diagHardwareProof" class="integrityCard">
        <div class="integrityHeader">
          <h2>Hardware proof</h2>
          <span id="diagHardwareProofBadge" class="integrityBadge muted">unknown</span>
        </div>
        <p id="diagHardwareProofSummary" class="message">Diagnostics have not been loaded yet.</p>
        <p class="message">Next step: <strong id="diagHardwareProofNextStep">Run software proof, then hardware-in-loop validation.</strong></p>
        <ul id="diagHardwareProofReasons" class="supportList"></ul>
      </div>
      <ul id="diagRefs" class="supportList"></ul>
    </section>
    <section class="panel">
      <h2>Vision Review Queue</h2>
      <p class="message">Select a sample and submit a manual review decision.</p>
      <div class="reviewGrid">
        <label>Sample
          <select id="reviewSampleSelect"></select>
        </label>
        <label>Decision
          <select id="reviewDecisionSelect">
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
            <option value="needs_retry">needs_retry</option>
          </select>
        </label>
      </div>
      <div class="reviewGrid">
        <label>Option (optional)
          <input id="reviewOptionInput" autocomplete="off" placeholder="e.g. route_keyframe_review">
        </label>
        <label>Operator (optional)
          <input id="reviewOperatorInput" autocomplete="off" placeholder="operator_id">
        </label>
      </div>
      <label>Comment (optional)
        <textarea id="reviewCommentInput" placeholder="why this sample was approved or rejected"></textarea>
      </label>
      <div class="row">
        <button id="reviewRefreshButton" onclick="loadReviewQueue()">Refresh Queue</button>
        <button id="reviewJumpPendingButton" onclick="jumpToNextPending()">Jump To Next Pending</button>
        <button id="reviewSubmitButton" class="primary" onclick="submitReviewDecision()">Submit Review Decision</button>
      </div>
      <div class="reviewMeta">
        <p class="message">Queue status: <strong id="reviewQueueStatus">not loaded</strong></p>
        <p class="message">Progress: <strong id="reviewProgressSummary">not loaded</strong></p>
        <p class="message">Decision distribution: <strong id="reviewDecisionDistribution">not loaded</strong></p>
        <p class="message">Next pending sample: <strong id="reviewNextPending">not loaded</strong></p>
        <p class="message">Selected summary: <code id="reviewSelectedSummary">none</code></p>
        <p class="message">Result: <strong id="reviewResultMessage">not submitted</strong></p>
      </div>
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
  approaching_elevator: ['Elevator assist', '正在前往电梯厅。', 'delivering'],
  waiting_elevator_open: ['Elevator assist', '已到电梯厅，等待电梯开门。', 'delivering'],
  entering_elevator: ['Elevator assist', '正在进入电梯，请保持通道安全。', 'delivering'],
  requesting_floor_help: ['Elevator assist', '已进入电梯，正在请求帮忙按楼层。', 'delivering'],
  waiting_target_floor: ['Elevator assist', '正在等待目标楼层，请保持通道安全。', 'delivering'],
  exiting_elevator: ['Elevator assist', '已到目标楼层，准备驶出。', 'delivering'],
  resume_delivery: ['Delivering', '已驶出电梯，继续送往垃圾站。', 'delivering'],
  network_error: ['Connection issue', 'The phone cannot reach the robot control page.', 'waiting']
};
const STEP_ORDER = ['waiting', 'delivering', 'dropoff', 'returning', 'completed'];
const ELEVATOR_ASSIST_SPEAKER_PROMPT = '你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,';
let reviewQueueSnapshot = null;
function fmt(value) {
  return Number.isFinite(value) ? value.toFixed(2) : '-';
}
function text(value, fallback) {
  const normalized = String(value || '').trim();
  return normalized || fallback;
}
function arrayText(value) {
  return Array.isArray(value) ? value.map(item => String(item || '').trim()).filter(Boolean) : [];
}
function countSummary(value) {
  if (!value || typeof value !== 'object') return 'not reported';
  return Object.keys(value).map((key) => {
    const counts = value[key] && typeof value[key] === 'object' ? value[key] : {};
    const parts = Object.keys(counts).map(countKey => `${countKey} ${counts[countKey]}`);
    return parts.length ? `${key}: ${parts.join(', ')}` : key;
  }).join('; ') || 'not reported';
}
function visionIntegrityView(visionSamples) {
  const summary = visionSamples.integrity_summary || {};
  const status = text(summary.status, 'unknown');
  const config = {
    ok: {
      label: 'Healthy',
      tone: 'ok',
      summary: 'Vision evidence chain is complete and ready for support review.',
      advice: 'Continue the task flow. Keep collecting samples during real runs.'
    },
    warning: {
      label: 'Needs review',
      tone: 'warning',
      summary: 'Vision evidence chain is usable, but some evidence should be reviewed first.',
      advice: 'Review the listed sample evidence before using it for route or anomaly decisions.'
    },
    error: {
      label: 'Broken',
      tone: 'error',
      summary: 'Vision evidence chain is not trustworthy until the reported issue is repaired.',
      advice: 'Recreate or repair the missing sample files, then rerun diagnostics.'
    },
    not_configured: {
      label: 'Not configured',
      tone: 'muted',
      summary: 'Vision sample evidence is not configured on this robot yet.',
      advice: 'Configure vision_sample_manifest_ref or run a learning route that writes a manifest.'
    },
    checker_unavailable: {
      label: 'Checker unavailable',
      tone: 'muted',
      summary: 'This software environment cannot run the vision sample checker.',
      advice: 'Install or source the vision package before relying on this support signal.'
    },
    checker_failed: {
      label: 'Checker failed',
      tone: 'error',
      summary: 'The vision sample checker failed, so the sample chain cannot be judged from the phone.',
      advice: 'Share the diagnostics package with support and inspect the checker error.'
    },
    unknown: {
      label: 'Unknown',
      tone: 'muted',
      summary: 'There is not enough diagnostics data to judge the vision evidence chain.',
      advice: 'Refresh diagnostics after the robot publishes a support package.'
    }
  };
  const view = config[status] || config.unknown;
  const missingRefs = Array.isArray(visionSamples.missing_file_refs) ? visionSamples.missing_file_refs : [];
  const reasons = [];
  missingRefs.forEach((item) => {
    if (!item || typeof item !== 'object') return;
    const field = text(item.field, 'file_ref');
    const detail = text(item.resolved_path, text(item.value, 'unresolved path'));
    reasons.push(`Missing ${field}: ${detail}`);
  });
  reasons.push(...arrayText(visionSamples.integrity_errors));
  reasons.push(...arrayText(visionSamples.integrity_warnings));
  if (text(visionSamples.read_error, '')) reasons.push(text(visionSamples.read_error, ''));
  return {
    status,
    label: view.label,
    tone: view.tone,
    summary: view.summary,
    reasons: reasons.slice(0, 3).length ? reasons.slice(0, 3) : ['No blocking evidence-chain issue reported.'],
    advice: view.advice,
    contextCoverage: countSummary(visionSamples.context_field_coverage),
    fileCounts: countSummary(visionSamples.file_counts)
  };
}
function renderVisionIntegrity(visionSamples) {
  const view = visionIntegrityView(visionSamples || {});
  const badge = document.getElementById('diagVisionIntegrityBadge');
  badge.textContent = view.label;
  badge.className = `integrityBadge ${view.tone}`;
  document.getElementById('diagVisionIntegritySummary').textContent = view.summary;
  document.getElementById('diagVisionIntegrityAdvice').textContent = view.advice;
  document.getElementById('diagVisionContextCoverage').textContent = view.contextCoverage;
  document.getElementById('diagVisionFileCounts').textContent = view.fileCounts;
  const reasonList = document.getElementById('diagVisionIntegrityReasons');
  reasonList.innerHTML = '';
  view.reasons.forEach((reason) => {
    const item = document.createElement('li');
    item.textContent = reason;
    reasonList.appendChild(item);
  });
}
function hardwareProofView(hardwareProof) {
  const status = text(hardwareProof.status, 'read_error');
  const config = {
    software_proof: {
      label: 'Software proof',
      tone: 'warning',
      summary: 'Software proof is ready only; it does not validate real hardware or HIL.',
      nextStep: 'Run WAVE ROVER hardware-in-loop validation before treating the robot as hardware-ready.'
    },
    needs_hil: {
      label: 'Needs HIL',
      tone: 'warning',
      summary: 'Software proof exists, hardware-in-loop still required before treating the robot as validated.',
      nextStep: 'Run the WAVE ROVER HIL recipe and capture UART, motion, IMU, and battery evidence.'
    },
    invalid_config: {
      label: 'Invalid config',
      tone: 'error',
      summary: 'The hardware proof artifact reports an invalid bridge configuration.',
      nextStep: 'Fix the bridge configuration, rerun software proof, then run HIL.'
    },
    read_error: {
      label: 'Read error',
      tone: 'error',
      summary: 'The hardware proof artifact cannot be read or trusted.',
      nextStep: 'Recreate the artifact and keep hardware status conservative until HIL passes.'
    }
  };
  const view = config[status] || config.read_error;
  const reasons = [];
  const readError = text(hardwareProof.read_error, '');
  if (readError) reasons.push(readError);
  const riskFlags = Array.isArray(hardwareProof.risk_flags) ? hardwareProof.risk_flags : [];
  riskFlags.slice(0, 3).forEach((flag) => {
    if (flag && typeof flag === 'object') {
      reasons.push(`${text(flag.id, 'risk')}: ${text(flag.detail, text(flag.severity, 'review required'))}`);
    } else {
      reasons.push(String(flag));
    }
  });
  if (text(hardwareProof.artifact_ref, '')) reasons.push(`Artifact: ${hardwareProof.artifact_ref}`);
  return {
    status,
    label: view.label,
    tone: view.tone,
    summary: text(hardwareProof.summary, view.summary),
    nextStep: text(hardwareProof.next_step, view.nextStep),
    reasons: reasons.length ? reasons.slice(0, 4) : ['No blocking hardware proof detail reported.']
  };
}
function renderHardwareProof(hardwareProof) {
  const view = hardwareProofView(hardwareProof || {});
  const badge = document.getElementById('diagHardwareProofBadge');
  badge.textContent = view.label;
  badge.className = `integrityBadge ${view.tone}`;
  document.getElementById('diagHardwareProofSummary').textContent = view.summary;
  document.getElementById('diagHardwareProofNextStep').textContent = view.nextStep;
  const reasonList = document.getElementById('diagHardwareProofReasons');
  reasonList.innerHTML = '';
  view.reasons.forEach((reason) => {
    const item = document.createElement('li');
    item.textContent = reason;
    reasonList.appendChild(item);
  });
}
function decisionSummaryText(item) {
  const status = text(item.review_status, 'pending');
  const reason = text(item.reason, 'unknown_reason');
  const last = item.last_decision && typeof item.last_decision === 'object' ? item.last_decision : null;
  if (!last) return `${status} | ${reason}`;
  return `${status} | ${reason} | ${text(last.decision, 'unknown')} @ ${text(last.timestamp, 'unknown time')}`;
}
function percent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '0.0%';
  return `${(numeric * 100).toFixed(1)}%`;
}
function progressSummaryText(progressSummary) {
  if (!progressSummary || typeof progressSummary !== 'object') return 'not reported';
  const total = Number(progressSummary.total || 0);
  const decided = Number(progressSummary.decided || 0);
  const pending = Number(progressSummary.pending || 0);
  const coverageRate = percent(progressSummary.coverage_rate || 0);
  return `${decided}/${total} decided | ${pending} pending | coverage ${coverageRate}`;
}
function decisionDistributionText(distribution) {
  if (!distribution || typeof distribution !== 'object') return 'not reported';
  const entries = ['approved', 'rejected', 'needs_retry'].map((decision) => {
    const item = distribution[decision] && typeof distribution[decision] === 'object'
      ? distribution[decision]
      : {count: 0, ratio: 0};
    return `${decision} ${Number(item.count || 0)} (${percent(item.ratio || 0)})`;
  });
  return entries.join(' | ');
}
function nextPendingText(nextPendingSample) {
  if (!nextPendingSample || typeof nextPendingSample !== 'object') {
    return 'none';
  }
  return `${text(nextPendingSample.sample_id, 'unknown')} | ${text(nextPendingSample.reason, 'review')}`;
}
function routeProofSummaryText(routeProofSummary) {
  if (!routeProofSummary || typeof routeProofSummary !== 'object') return 'not reported';
  const coverageRate = Number(routeProofSummary.coverage_rate);
  const covered = Number(routeProofSummary.covered_checkpoints);
  const total = Number(routeProofSummary.total_checkpoints);
  const gateStatus = text(routeProofSummary.gate_status, 'unknown');
  const missing = Array.isArray(routeProofSummary.missing_checkpoints)
    ? routeProofSummary.missing_checkpoints.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  const coverageText = Number.isFinite(coverageRate) ? percent(coverageRate) : 'n/a';
  const countText = Number.isFinite(covered) && Number.isFinite(total) ? `${covered}/${total}` : 'n/a';
  const missingText = missing.length ? missing.join(', ') : 'none';
  return `coverage ${coverageText} | checkpoints ${countText} | gate ${gateStatus} | missing ${missingText}`;
}
function elevatorEvidenceText(elevatorAssist) {
  const evidence = elevatorAssist && typeof elevatorAssist.evidence === 'object' ? elevatorAssist.evidence : {};
  const keys = Object.keys(evidence);
  if (!keys.length) return 'not reported';
  return keys.map((key) => `${key}: ${JSON.stringify(evidence[key])}`).join(' | ');
}
function applyReviewProgress(queuePayload) {
  const progressSummary = queuePayload && typeof queuePayload === 'object'
    ? queuePayload.progress_summary
    : null;
  const decisionDistribution = queuePayload && typeof queuePayload === 'object'
    ? queuePayload.decision_distribution
    : null;
  const nextPendingSample = queuePayload && typeof queuePayload === 'object'
    ? queuePayload.next_pending_sample
    : null;
  reviewQueueSnapshot = queuePayload && typeof queuePayload === 'object' ? queuePayload : null;
  document.getElementById('reviewProgressSummary').textContent = progressSummaryText(progressSummary);
  document.getElementById('reviewDecisionDistribution').textContent = decisionDistributionText(decisionDistribution);
  document.getElementById('reviewNextPending').textContent = nextPendingText(nextPendingSample);
  document.getElementById('reviewJumpPendingButton').disabled = !(
    nextPendingSample &&
    typeof nextPendingSample === 'object' &&
    text(nextPendingSample.sample_id, '')
  );
}
function updateSelectedReviewSummary() {
  const select = document.getElementById('reviewSampleSelect');
  const currentOption = select.options[select.selectedIndex];
  document.getElementById('reviewSelectedSummary').textContent = currentOption
    ? text(currentOption.dataset.summary, 'none')
    : 'none';
}
function renderReviewQueue(queuePayload) {
  applyReviewProgress(queuePayload);
  const queue = Array.isArray(queuePayload.review_queue) ? queuePayload.review_queue : [];
  const select = document.getElementById('reviewSampleSelect');
  select.innerHTML = '';
  if (!queue.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No sample pending review';
    option.dataset.summary = 'queue empty';
    select.appendChild(option);
    select.disabled = true;
    document.getElementById('reviewSubmitButton').disabled = true;
    document.getElementById('reviewQueueStatus').textContent = `0 sample | ${text(queuePayload.manifest_read_error, 'queue empty')}`;
    updateSelectedReviewSummary();
    return;
  }
  queue.forEach((item) => {
    const option = document.createElement('option');
    option.value = text(item.sample_id, '');
    option.textContent = `${text(item.sample_id, 'unknown')} (${text(item.review_status, 'pending')})`;
    option.dataset.summary = decisionSummaryText(item);
    select.appendChild(option);
  });
  select.disabled = false;
  document.getElementById('reviewSubmitButton').disabled = false;
  document.getElementById('reviewQueueStatus').textContent = `${Number(queuePayload.review_queue_count || queue.length)} sample(s)`;
  updateSelectedReviewSummary();
}
function jumpToNextPending() {
  const nextPendingSample = reviewQueueSnapshot && typeof reviewQueueSnapshot === 'object'
    ? reviewQueueSnapshot.next_pending_sample
    : null;
  const sampleId = text((nextPendingSample || {}).sample_id, '');
  if (!sampleId) {
    document.getElementById('reviewResultMessage').textContent = 'No pending sample available.';
    return;
  }
  const select = document.getElementById('reviewSampleSelect');
  const option = Array.from(select.options).find((item) => item.value === sampleId);
  if (!option) {
    document.getElementById('reviewResultMessage').textContent = `Pending sample ${sampleId} is outside the current queue window.`;
    return;
  }
  select.value = sampleId;
  updateSelectedReviewSummary();
  document.getElementById('reviewResultMessage').textContent = `Focused pending sample ${sampleId}.`;
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
  const routeProofSummary = payload.route_proof_summary || {};
  const routeProofStatus = payload.route_proof_status || {};
  const hardwareProof = payload.hardware_proof || {};
  const elevatorAssist = payload.elevator_assist || {};
  const elevatorAssistStatus = payload.elevator_assist_status || {};
  const refs = Array.isArray(payload.log_refs) ? payload.log_refs : [];
  const taskRecord = failure.task_record_path || (payload.last_task || {}).task_record_path || latest.task_record_path || '';
  renderVisionIntegrity(visionSamples);
  renderHardwareProof(hardwareProof);
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
  const reviewQueue = Array.isArray(visionSamples.review_queue) ? visionSamples.review_queue : [];
  const progressSummary = visionSamples.progress_summary && typeof visionSamples.progress_summary === 'object'
    ? visionSamples.progress_summary
    : {};
  const nextReview = visionSamples.next_pending_sample && typeof visionSamples.next_pending_sample === 'object'
    ? visionSamples.next_pending_sample
    : null;
  document.getElementById('diagReviewQueue').textContent = `${Number(progressSummary.pending || 0)} pending / ${Number(progressSummary.total || 0)} total`;
  document.getElementById('diagNextReviewSample').textContent = nextReview
    ? `${text(nextReview.reason, 'review')} ${text(nextReview.sample_ref, text(nextReview.sample_id, 'unknown'))}`
    : 'no pending sample';
  document.getElementById('diagRouteProofState').textContent = text(routeProofStatus.state, 'unknown');
  document.getElementById('diagRouteProofSummary').textContent = routeProofSummaryText(routeProofSummary);
  document.getElementById('diagRouteProofReason').textContent = text(
    routeProofStatus.blocking_reason || routeProofStatus.reason,
    'not reported'
  );
  document.getElementById('diagRouteProofSource').textContent = text(routeProofStatus.source, 'not reported');
  document.getElementById('diagElevatorAssistState').textContent = text(
    `${text(elevatorAssistStatus.state, 'unknown')} / ${text(elevatorAssist.phase || elevatorAssist.state, 'none')}`,
    'unknown'
  );
  document.getElementById('diagElevatorAssistPrompt').textContent = text(
    elevatorAssist.speaker_prompt || elevatorAssist.phone_copy,
    'not reported'
  );
  document.getElementById('diagElevatorAssistEvidence').textContent = elevatorEvidenceText(elevatorAssist);
  document.getElementById('diagElevatorAssistNextStep').textContent = text(
    elevatorAssistStatus.next_step || elevatorAssistStatus.reason,
    'not reported'
  );
  renderReviewQueue({
    review_queue_count: visionSamples.review_queue_count,
    review_queue: reviewQueue,
    progress_summary: visionSamples.progress_summary,
    decision_distribution: visionSamples.decision_distribution,
    next_pending_sample: visionSamples.next_pending_sample,
    manifest_read_error: visionSamples.read_error,
  });
  const refList = document.getElementById('diagRefs');
  refList.innerHTML = '';
  [...refs, payload.vision_sample_manifest_ref, hardwareProof.artifact_ref].filter(Boolean).forEach((ref) => {
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
async function loadReviewQueue() {
  try {
    const response = await fetch('/api/vision/review-queue');
    const payload = await response.json();
    renderReviewQueue(payload);
    if (!payload.ok && payload.error) {
      document.getElementById('reviewResultMessage').textContent = `${text(payload.error.code, 'error')}: ${text(payload.error.message, 'request failed')}`;
    }
  } catch (error) {
    document.getElementById('reviewQueueStatus').textContent = `queue load failed: ${String(error)}`;
  }
}
async function submitReviewDecision() {
  const sampleSelect = document.getElementById('reviewSampleSelect');
  const sampleId = text(sampleSelect.value, '');
  if (!sampleId) {
    document.getElementById('reviewResultMessage').textContent = 'sample_id is required';
    return;
  }
  const body = {
    sample_id: sampleId,
    decision: text(document.getElementById('reviewDecisionSelect').value, 'approved'),
    option: text(document.getElementById('reviewOptionInput').value, ''),
    operator: text(document.getElementById('reviewOperatorInput').value, ''),
    comment: text(document.getElementById('reviewCommentInput').value, '')
  };
  try {
    const response = await fetch('/api/vision/review-decisions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const payload = await response.json();
    if (response.ok && payload.ok) {
      document.getElementById('reviewResultMessage').textContent = `stored ${payload.decision} for ${payload.sample_id} at ${text(payload.stored_at, 'unknown time')}`;
      await loadReviewQueue();
      return;
    }
    const error = payload.error || {};
    document.getElementById('reviewResultMessage').textContent = `${text(error.code, 'error')}: ${text(error.message, 'request failed')}`;
  } catch (error) {
    document.getElementById('reviewResultMessage').textContent = `submit failed: ${String(error)}`;
  }
}
async function diagnostics() {
  const payload = await api('/api/diagnostics');
  if (payload) showDiagnostics(payload);
}
document.getElementById('reviewSampleSelect').addEventListener('change', updateSelectedReviewSummary);
setInterval(refresh, 1000);
refresh();
loadReviewQueue();
</script>
</body>
</html>"""


def status_payload(state, message="", **extra):
    elevator_assist = normalize_elevator_assist(
        extra.pop("elevator_assist", None),
        state=state,
        message=message,
    )
    prompt = operator_prompt_for_state(state, elevator_assist=elevator_assist)
    payload = {
        "api_version": API_VERSION,
        "state": state,
        "message": message,
        "phone_copy": prompt["phone_copy"],
        "speaker_prompt": prompt["speaker_prompt"],
        "elevator_assist": elevator_assist,
        "updated_at": time.time(),
    }
    payload.update(extra)
    if elevator_assist.get("enabled"):
        payload["phone_copy"] = elevator_assist.get("phone_copy") or payload["phone_copy"]
        payload["speaker_prompt"] = elevator_assist.get("speaker_prompt") or payload["speaker_prompt"]
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
            if path == "/api/vision/review-queue":
                self._send_json(200, gateway.vision_review_queue())
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
            if path == "/api/vision/review-decisions":
                status, payload = gateway.submit_review_decision(body)
                self._send_json(status, payload)
                return
            self._send_json(404, status_payload("not_found", f"unknown path: {path}"))

        def log_message(self, _format, *_args):
            return

    return Handler
