import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7RouteReplayPreviewFrame,
  O7RouteReplayPreviewResponse,
  O7RouteReplayPreviewTransition,
} from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7RouteReplayPreviewOptions {
  fixtureJson?: string;
}

const SUPPORTED_SCHEMA = "trashbot.o7.route_replay_fixture.v1" as const;
const SAMPLE_FRAME_LIMIT = 3;
const SAMPLE_REF_LIMIT = 8;
const SAMPLE_TRANSITION_LIMIT = 6;

const FORBIDDEN_COPY = [
  "Authorization",
  "access_key",
  "secret",
  "token",
  "password",
  "postgres://",
  "postgresql://",
  "mysql://",
  "redis://",
  "amqp://",
  "mongodb://",
  "/cmd_vel",
  "/dev/tty",
  "/dev/ttyUSB",
  "/dev/ttyACM",
  "serial",
  "UART",
  "baudrate",
  "WAVE ROVER",
  "Traceback",
];

const SUCCESS_CLAIM_PATTERNS = [
  /\bdelivery\s+(success|succeeded|completed|complete)\b/i,
  /\bdropoff\s+(success|succeeded|completed|complete)\b/i,
  /\broute\s+replay\s+(success|succeeded|completed|complete)\b/i,
  /"delivery_success"\s*:\s*true/i,
  /"playback_available"\s*:\s*true/i,
];

const CONTROL_CLAIM_PATTERNS = [
  /"primary_actions_enabled"\s*:\s*true/i,
  /"safe_to_control"\s*:\s*true/i,
  /"robot_control_executed"\s*:\s*true/i,
  /"command_dispatch_enabled"\s*:\s*true/i,
];

const SENSITIVE_PATTERNS: Array<[RegExp, string]> = [
  [/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]"],
  [/\bAuthorization\s*:\s*[^,\s]+/gi, "Authorization: [REDACTED]"],
  [/\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+/gi, "$1=[REDACTED]"],
  [/\b(postgres|postgresql|mysql|redis|amqp|mongodb):\/\/[^,\s]+/gi, "[REDACTED_URL]"],
  [/\/cmd_vel\b/g, "[REDACTED_ROS_TOPIC]"],
  [/\/dev\/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*/gi, "/dev/[REDACTED_DEVICE]"],
  [/\b[A-Za-z]:\\[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/\/(Users|home|tmp|private|var|mnt|run|workspace|ws)\/[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+/gi, "$1=[REDACTED_RATE]"],
  [/WAVE\s+ROVER/gi, "[REDACTED_PLATFORM]"],
  [/Traceback \(most recent call last\):[\s\S]*/gi, "[REDACTED_TRACEBACK]"],
];

// 该 adapter 只读用户显式指定的本地 JSON fixture，并输出可消费的安全摘要。
// 它不连接 O6 云归档、不读取 ROS graph、不打开串口、不发任何机器人或 Nav2 命令。
// 输出采用白名单字段，避免把 fixture 里的绝对路径、凭证、串口或控制 topic 原样复制。
// 成功/控制声明一律 blocked，是为了阻止测试 fixture 被误读成真实 O7 历史回放能力。
// frame/keyframe/transition 都限量采样，完整轨迹不得通过该预览 API 泄露或伪装成播放器。
// `safe_to_play=false` 表示前端最多展示摘要，不能提供播放、下发、恢复或机器人动作入口。

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown): string {
  // 空值统一转为空字符串，避免 null/undefined 被展示成真实业务 token。
  return value === null || value === undefined ? "" : String(value);
}

function safeText(value: unknown): string {
  // 所有展示文本都先脱敏，防止 fixture 内嵌路径、凭证或硬件细节。
  return SENSITIVE_PATTERNS.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), asText(value));
}

function safeRef(value: unknown): string {
  // evidence/keyframe 引用只保留 basename；绝对路径和目录结构不会进入响应。
  const raw = asText(value).trim();
  if (!raw) {
    return "";
  }
  if (path.isAbsolute(raw) || raw.includes("/") || raw.includes("\\")) {
    return `file:${path.basename(raw)}`;
  }
  return safeText(raw);
}

function safeNumber(value: unknown): number | null {
  // 只接受有限数字，字符串数字不自动提升，避免复制不可信 payload。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function encoded(value: unknown): string {
  // 安全扫描覆盖完整 fixture；无法序列化时退回空对象文本。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function hasForbiddenCopy(value: unknown): boolean {
  // 命中凭证、串口、ROS 控制 topic 或 traceback 时，整个 fixture 不再摘要。
  const payload = encoded(value);
  return FORBIDDEN_COPY.some((token) => payload.includes(token));
}

function hasSuccessClaim(value: unknown): boolean {
  // 真实完成或 playback 可用声明不能由本地 fixture 自证，必须 fail closed。
  const payload = encoded(value);
  return SUCCESS_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function hasControlClaim(value: unknown): boolean {
  // 任意控制开关为 true 都说明 fixture 不安全，不能进入可消费预览。
  const payload = encoded(value);
  return CONTROL_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function sampleFrame(value: unknown, index: number): O7RouteReplayPreviewFrame {
  // frame 摘要只保留轨迹预览需要的数值和引用，不透传原始对象。
  const frame = isObject(value) ? value : {};
  const pose = isObject(frame.pose) ? frame.pose : frame;
  const velocity = isObject(frame.velocity) ? frame.velocity : frame;
  return {
    frame_index: safeNumber(frame.frame_index ?? frame.index) ?? index,
    timestamp_ms: safeNumber(frame.timestamp_ms ?? frame.t_ms),
    pose: {
      x_m: safeNumber(pose.x_m ?? pose.x),
      y_m: safeNumber(pose.y_m ?? pose.y),
      yaw_rad: safeNumber(pose.yaw_rad ?? pose.yaw),
    },
    velocity: {
      linear_mps: safeNumber(velocity.linear_mps ?? velocity.vx_mps),
      angular_radps: safeNumber(velocity.angular_radps ?? velocity.wz_radps),
    },
    state: safeText(frame.state || "not_provided"),
    evidence_ref: safeRef(frame.evidence_ref ?? frame.keyframe_ref),
  };
}

function sampleTransition(value: unknown): O7RouteReplayPreviewTransition {
  // 状态转移只保留 from/to/timestamp/evidence_ref，防止复制完整事件 payload。
  const transition = isObject(value) ? value : {};
  return {
    from: safeText(transition.from || transition.from_state || "not_provided"),
    to: safeText(transition.to || transition.to_state || transition.state || "not_provided"),
    timestamp_ms: safeNumber(transition.timestamp_ms ?? transition.t_ms),
    evidence_ref: safeRef(transition.evidence_ref),
  };
}

function safeStringList(value: unknown, limit: number): string[] {
  // 引用列表限量输出，并过滤空值，避免把整包 archive 搬进 API。
  if (!Array.isArray(value)) {
    return [];
  }
  return value.slice(0, limit).map((item) => safeRef(item)).filter(Boolean);
}

function stateTransitionGaps(payload: JsonObject, transitions: unknown[]): string[] {
  // gaps 是字段缺失摘要，不代表真实云端归档查询结果。
  const gaps: string[] = ["not_o6_cloud_archive", "not_real_route_playback", "robot_control_disabled"];
  if (!Array.isArray(payload.trajectory_frames) || payload.trajectory_frames.length === 0) {
    gaps.push("trajectory_frames_empty_or_missing");
  }
  if (!Array.isArray(payload.keyframe_refs) || payload.keyframe_refs.length === 0) {
    gaps.push("keyframe_refs_empty_or_missing");
  }
  if (transitions.length === 0) {
    gaps.push("state_transitions_empty_or_missing");
  }
  if (!asText(payload.evidence_ref).trim()) {
    gaps.push("task_evidence_ref_missing");
  }
  return gaps;
}

function blockedResponse(
  status: O7RouteReplayPreviewResponse["input_status"]["status"],
  failureReason: string,
  fixturePath = "",
): O7RouteReplayPreviewResponse {
  // 所有失败使用同一响应 schema，调用方无需按 HTTP 500 猜测边界。
  return {
    schema: "trashbot.o7.route_replay_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "blocked_not_proven",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status,
      failure_reason: failureReason,
    },
    source_fixture_schema: "not_loaded",
    real_cloud_archive_connected: false,
    robot_control_executed: false,
    task: {
      task_id: "not_loaded",
      robot_id: "not_loaded",
      route_id: "not_loaded",
      evidence_ref: "not_loaded",
    },
    route_metadata: {
      map_frame: "not_loaded",
      frame_schema: "fixture_trajectory_frame_summary_v1",
      source: "local_json_fixture",
    },
    trajectory: {
      frame_count: 0,
      sample_frames: [],
      status: "blocked_not_proven",
    },
    playback_cursor_initial_state: {
      frame_index: null,
      timestamp_ms: null,
      playing: false,
      speed: 0,
      safe_to_play: false,
      status: "blocked_not_proven",
    },
    keyframes: {
      count: 0,
      sample_refs: [],
      status: "blocked_not_proven",
    },
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      task_evidence_ref: "not_loaded",
      keyframe_refs: [],
    },
    state_transitions: {
      count: 0,
      sample: [],
      gaps: [failureReason, "fixture_preview_blocked", "not_o6_cloud_archive", "robot_control_disabled"],
      status: "blocked_not_proven",
    },
    blocked_reasons: [failureReason],
    not_proven: [
      "real_o6_cloud_archive",
      "real_route_replay_playback",
      "real_robot_control",
      "delivery_success",
    ],
  };
}

async function loadFixture(filePath: string): Promise<{ payload: JsonObject | null; status: string; reason: string }> {
  // 只读取 query 指定的单个 JSON 文件；目录、坏 JSON 和非对象都不会抛出到 Express。
  if (!filePath.trim()) {
    return { payload: null, status: "not_provided", reason: "fixture_json_not_provided" };
  }
  try {
    const content = await fs.readFile(path.resolve(filePath), "utf8");
    const parsed = JSON.parse(content) as unknown;
    if (!isObject(parsed)) {
      return { payload: null, status: "not_object", reason: "fixture_json_not_object" };
    }
    return { payload: parsed, status: "loaded", reason: "" };
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      return { payload: null, status: "missing", reason: "fixture_json_missing" };
    }
    if (error instanceof SyntaxError) {
      return { payload: null, status: "bad_json", reason: "fixture_json_bad_json" };
    }
    return { payload: null, status: "read_error", reason: "fixture_json_read_error" };
  }
}

export async function buildO7RouteReplayPreview(
  options: O7RouteReplayPreviewOptions = {},
): Promise<O7RouteReplayPreviewResponse> {
  // adapter 入口保持单一 query path，便于测试覆盖所有 fail-closed 分支。
  const fixturePath = asText(options.fixtureJson).trim();
  const loaded = await loadFixture(fixturePath);
  if (!loaded.payload) {
    return blockedResponse(loaded.status as O7RouteReplayPreviewResponse["input_status"]["status"], loaded.reason, fixturePath);
  }
  if (loaded.payload.schema !== SUPPORTED_SCHEMA) {
    return blockedResponse("unsupported_schema", "unsupported_fixture_schema", fixturePath);
  }
  if (hasForbiddenCopy(loaded.payload)) {
    return blockedResponse("unsafe_copy", "fixture_contains_unsafe_copy", fixturePath);
  }
  if (hasSuccessClaim(loaded.payload)) {
    return blockedResponse("success_claim", "fixture_contains_success_claim", fixturePath);
  }
  if (hasControlClaim(loaded.payload)) {
    return blockedResponse("control_claim", "fixture_contains_control_claim", fixturePath);
  }

  const trajectoryFrames = Array.isArray(loaded.payload.trajectory_frames) ? loaded.payload.trajectory_frames : [];
  const stateTransitions = Array.isArray(loaded.payload.state_transitions) ? loaded.payload.state_transitions : [];
  const sampleFrames = trajectoryFrames.slice(0, SAMPLE_FRAME_LIMIT).map((frame, index) => sampleFrame(frame, index));
  const sampleTransitions = stateTransitions.slice(0, SAMPLE_TRANSITION_LIMIT).map((transition) => sampleTransition(transition));
  const keyframeRefs = safeStringList(loaded.payload.keyframe_refs, SAMPLE_REF_LIMIT);
  const evidenceRef = safeRef(loaded.payload.evidence_ref);
  const firstTimestamp = sampleFrames[0]?.timestamp_ms ?? null;

  return {
    schema: "trashbot.o7.route_replay_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "fixture_preview_ready",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status: "loaded",
      failure_reason: "",
    },
    source_fixture_schema: SUPPORTED_SCHEMA,
    real_cloud_archive_connected: false,
    robot_control_executed: false,
    task: {
      task_id: safeText(loaded.payload.task_id || "not_provided"),
      robot_id: safeText(loaded.payload.robot_id || "not_provided"),
      route_id: safeText(loaded.payload.route_id || "not_provided"),
      evidence_ref: evidenceRef,
    },
    route_metadata: {
      map_frame: safeText(loaded.payload.map_frame || "map"),
      frame_schema: "fixture_trajectory_frame_summary_v1",
      source: "local_json_fixture",
    },
    trajectory: {
      frame_count: trajectoryFrames.length,
      sample_frames: sampleFrames,
      status: "fixture_summary_only",
    },
    playback_cursor_initial_state: {
      frame_index: trajectoryFrames.length > 0 ? 0 : null,
      timestamp_ms: firstTimestamp,
      playing: false,
      speed: 0,
      safe_to_play: false,
      status: "preview_cursor_only",
    },
    keyframes: {
      count: Array.isArray(loaded.payload.keyframe_refs) ? loaded.payload.keyframe_refs.length : 0,
      sample_refs: keyframeRefs,
      status: "fixture_refs_only",
    },
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      task_evidence_ref: evidenceRef,
      keyframe_refs: keyframeRefs,
    },
    state_transitions: {
      count: stateTransitions.length,
      sample: sampleTransitions,
      gaps: stateTransitionGaps(loaded.payload, stateTransitions),
      status: "fixture_summary_only",
    },
    blocked_reasons: ["not_o6_cloud_archive", "robot_control_disabled", "delivery_success_not_proven"],
    not_proven: [
      "real_o6_cloud_archive",
      "real_history_task_archive",
      "real_route_replay_playback",
      "real_keyframe_archive",
      "real_state_transition_archive",
      "real_robot_control",
      "delivery_success",
    ],
  };
}
