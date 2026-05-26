import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type { O7SafeCommandPreviewResponse } from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7SafeCommandPreviewOptions {
  fixtureJson?: string;
}

const SUPPORTED_SCHEMA = "trashbot.o7.safe_command_fixture.v1" as const;
const SAMPLE_REF_LIMIT = 8;

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
  /\bcommand\s+(success|succeeded|completed|complete)\b/i,
  /\bnavigate\s+(success|succeeded|completed|complete)\b/i,
  /"delivery_success"\s*:\s*true/i,
  /"proof_status"\s*:\s*"(pass|passed|proven|verified)"/i,
];

const CONTROL_CLAIM_PATTERNS = [
  /"primary_actions_enabled"\s*:\s*true/i,
  /"safe_to_control"\s*:\s*true/i,
];

const DISPATCH_ENABLED_PATTERNS = [
  /"command_dispatch_enabled"\s*:\s*true/i,
  /\bcommand\s+dispatch\s+(enabled|available|ready)\b/i,
];

const MANUAL_ENABLED_PATTERNS = [
  /"manual_control_enabled"\s*:\s*true/i,
  /\bmanual\s+(control|turn)\s+(enabled|available|ready)\b/i,
];

const NAVIGATE_ENABLED_PATTERNS = [
  /"navigate_goal_enabled"\s*:\s*true/i,
  /\bnavigate\s+goal\s+(enabled|available|ready)\b/i,
];

const KEYBOARD_ENABLED_PATTERNS = [
  /"keyboard_control_enabled"\s*:\s*true/i,
  /\bkeyboard\s+control\s+(enabled|available|ready)\b/i,
];

const REAL_COMMAND_API_PATTERNS = [
  /"real_command_api_connected"\s*:\s*true/i,
  /"command_api_connected"\s*:\s*true/i,
  /\breal\s+command\s+api\s+(connected|ready)\b/i,
];

const REAL_ROBOT_ACK_PATTERNS = [
  /"real_robot_ack_connected"\s*:\s*true/i,
  /"robot_ack_connected"\s*:\s*true/i,
  /\breal\s+robot\s+ack\s+(connected|ready)\b/i,
];

const ROBOT_CONTROL_EXECUTED_PATTERNS = [
  /"robot_control_executed"\s*:\s*true/i,
  /\brobot\s+control\s+(executed|sent|dispatched)\b/i,
];

const ACK_SUCCESS_PATTERNS = [
  /"ack_status"\s*:\s*"(success|succeeded|acked|ok|pass|passed|delivered)"/i,
  /"robot_ack"\s*:\s*true/i,
  /\b(robot\s+)?ack\s+(success|succeeded|acked|ok|pass|passed|delivered)\b/i,
];

const HARDWARE_VERIFIED_PATTERNS = [
  /"hardware_verified"\s*:\s*true/i,
  /"hil_verified"\s*:\s*true/i,
  /"hil_pass"\s*:\s*true/i,
  /\b(hil|hardware)\s+(verified|pass|passed|success|succeeded)\b/i,
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

// 这个 adapter 只读取用户显式传入的本地 safe-command JSON fixture，并输出白名单摘要。
// 它不连接云端 command API、不读取 ROS2/Nav2、不打开串口、不发送方向键或目标点命令。
// 即使 fixture 给出 envelope、limit 或 ACK 字段，响应仍固定 sends_to_robot=false 和 enabled=false。
// 任何成功、真实连接、ACK pass、HIL/硬件验证或控制执行声明都会 fail closed。
// evidence/audit 引用只保留 basename，避免本地路径、凭证、topic 或硬件细节泄露到 PC UI。

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown): string {
  // 空值统一为空字符串，避免 null/undefined 被渲染成真实 command id。
  return value === null || value === undefined ? "" : String(value);
}

function safeText(value: unknown): string {
  // 手控方向、goal source 和缺口说明都可能来自 fixture，必须先脱敏再返回。
  return SENSITIVE_PATTERNS.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), asText(value));
}

function safeRef(value: unknown): string {
  // 本地路径只保留文件名；PC preview 不把用户目录结构暴露给前端。
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
  // 只接受 fixture 中的有限 number，不把字符串数字自动升级成可执行 limit。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function encoded(value: unknown): string {
  // fail-closed 扫描覆盖完整 payload；序列化失败时按空对象处理。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function hasPattern(value: unknown, patterns: RegExp[]): boolean {
  // 危险声明可能藏在深层对象里，因此统一扫描 JSON 文本。
  const payload = encoded(value);
  return patterns.some((pattern) => pattern.test(payload));
}

function hasForbiddenCopy(value: unknown): boolean {
  // 命中凭证、串口、ROS 控制 topic 或 traceback 时，不返回任何业务摘要。
  const payload = encoded(value);
  return FORBIDDEN_COPY.some((token) => payload.includes(token));
}

function safeStringList(value: unknown, limit: number, refMode = false): string[] {
  // 缺口和审计引用限量输出，防止 preview API 变成原始审计日志导出通道。
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .slice(0, limit)
    .map((item) => (refMode ? safeRef(item) : safeText(item)))
    .filter(Boolean);
}

function defaultEvidenceGaps(value: unknown): string[] {
  // gaps 只描述本地 fixture 到真实控制链路的缺口，不代表查询过云端或机器人。
  const fixtureGaps = safeStringList(value, SAMPLE_REF_LIMIT * 2);
  return Array.from(
    new Set([
      ...fixtureGaps,
      "real_command_api_not_connected",
      "manual_turn_dispatch_not_proven",
      "navigate_goal_dispatch_not_proven",
      "robot_ack_timeout_trace_missing",
      "cancel_ack_trace_missing",
      "stop_ack_trace_missing",
      "recovery_event_trace_missing",
      "hil_or_hardware_safety_not_proven",
    ]),
  );
}

function blockedResponse(
  status: O7SafeCommandPreviewResponse["input_status"]["status"],
  failureReason: string,
  fixturePath = "",
): O7SafeCommandPreviewResponse {
  // 所有失败都返回同一 schema 和固定 false 开关，调用方不能从异常推断控制能力。
  return {
    schema: "trashbot.o7.safe_command_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "blocked_not_proven",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status,
      failure_reason: failureReason,
    },
    source_fixture_schema: "not_loaded",
    command_dispatch_enabled: false,
    manual_control_enabled: false,
    navigate_goal_enabled: false,
    keyboard_control_enabled: false,
    real_command_api_connected: false,
    real_robot_ack_connected: false,
    robot_control_executed: false,
    command_session: {
      command_session_id: "not_loaded",
      source: "local_json_fixture",
      evidence_ref: "not_loaded",
      audit_refs: [],
      status: "blocked_not_proven",
    },
    manual_turn_envelope_summary: {
      sends_to_robot: false,
      requested_direction: "not_loaded",
      velocity_limited: true,
      steering_limited: true,
      evidence_ref: "missing_manual_turn_command_envelope_trace",
      status: "blocked_not_proven",
    },
    navigate_goal_envelope_summary: {
      sends_to_robot: false,
      goal_source: "not_loaded",
      map_frame: "map",
      x_m: null,
      y_m: null,
      yaw_rad: null,
      evidence_ref: "missing_navigate_goal_command_envelope_trace",
      status: "blocked_not_proven",
    },
    velocity_limits: {
      max_linear_mps: null,
      max_angular_radps: null,
      source: "not_loaded",
      hardware_verified: false,
      status: "blocked_not_proven",
    },
    steering_limits: {
      max_steering_angle_rad: null,
      max_turn_rate_radps: null,
      source: "not_loaded",
      hardware_verified: false,
      status: "blocked_not_proven",
    },
    map_goal_slot: {
      map_frame: "map",
      x_m: null,
      y_m: null,
      yaw_rad: null,
      status: "blocked_not_proven",
      evidence_ref: "missing_map_goal_selection_trace",
    },
    idempotency_key_requirement: {
      required: true,
      key_ref: "missing_idempotency_key_requirement",
      header: "Idempotency-Key",
      status: "blocked_not_proven",
    },
    confirmation_policy: {
      manual_turn_requires_confirmation: true,
      navigate_goal_requires_confirmation: true,
      keyboard_control_requires_hold: true,
      status: "blocked_not_proven",
    },
    robot_ack_summary: {
      ack_status: "blocked_not_proven",
      last_command_id: "not_loaded",
      ack_ref: "missing_robot_command_ack",
      timeout_ms: null,
      cancel_ack_ref: "missing_robot_cancel_ack",
      stop_ack_ref: "missing_robot_stop_ack",
      recovery_ref: "missing_robot_recovery_event",
      status: "blocked_not_proven",
    },
    evidence_gaps: defaultEvidenceGaps([failureReason, "fixture_preview_blocked"]),
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      session_evidence_ref: "not_loaded",
      ack_ref: "missing_robot_command_ack",
      cancel_ack_ref: "missing_robot_cancel_ack",
      stop_ack_ref: "missing_robot_stop_ack",
      recovery_ref: "missing_robot_recovery_event",
      audit_refs: [],
    },
    blocked_reasons: [failureReason],
    not_proven: [
      "real_command_api_connected",
      "real_manual_turn_dispatch",
      "real_navigate_goal_dispatch",
      "real_keyboard_control",
      "real_robot_command_ack",
      "real_command_timeout",
      "real_cancel_ack",
      "real_stop_ack",
      "real_recovery_event",
      "real_hil_or_hardware_safety",
      "delivery_success",
    ],
  };
}

async function loadFixture(filePath: string): Promise<{ payload: JsonObject | null; status: string; reason: string }> {
  // 只读 query 指定的单个 JSON 文件；目录、坏 JSON 和非对象都转换成 blocked 响应。
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

export async function buildO7SafeCommandPreview(
  options: O7SafeCommandPreviewOptions = {},
): Promise<O7SafeCommandPreviewResponse> {
  // 主入口按固定顺序关闸：先验证 schema，再拦截任何真实控制、ACK 或 HIL 声明。
  const fixturePath = asText(options.fixtureJson).trim();
  const loaded = await loadFixture(fixturePath);
  if (!loaded.payload) {
    return blockedResponse(loaded.status as O7SafeCommandPreviewResponse["input_status"]["status"], loaded.reason, fixturePath);
  }
  if (loaded.payload.schema !== SUPPORTED_SCHEMA) {
    return blockedResponse("unsupported_schema", "unsupported_fixture_schema", fixturePath);
  }
  if (hasForbiddenCopy(loaded.payload)) {
    return blockedResponse("unsafe_copy", "fixture_contains_unsafe_copy", fixturePath);
  }
  if (hasPattern(loaded.payload, SUCCESS_CLAIM_PATTERNS)) {
    return blockedResponse("success_claim", "fixture_contains_success_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, CONTROL_CLAIM_PATTERNS)) {
    return blockedResponse("control_claim", "fixture_contains_control_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, DISPATCH_ENABLED_PATTERNS)) {
    return blockedResponse("dispatch_enabled_claim", "fixture_contains_dispatch_enabled_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, MANUAL_ENABLED_PATTERNS)) {
    return blockedResponse("manual_enabled_claim", "fixture_contains_manual_control_enabled_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, NAVIGATE_ENABLED_PATTERNS)) {
    return blockedResponse("navigate_enabled_claim", "fixture_contains_navigate_goal_enabled_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, KEYBOARD_ENABLED_PATTERNS)) {
    return blockedResponse("keyboard_enabled_claim", "fixture_contains_keyboard_control_enabled_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, REAL_COMMAND_API_PATTERNS)) {
    return blockedResponse("real_command_api_claim", "fixture_contains_real_command_api_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, REAL_ROBOT_ACK_PATTERNS)) {
    return blockedResponse("real_robot_ack_claim", "fixture_contains_real_robot_ack_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ROBOT_CONTROL_EXECUTED_PATTERNS)) {
    return blockedResponse("robot_control_executed_claim", "fixture_contains_robot_control_executed_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ACK_SUCCESS_PATTERNS)) {
    return blockedResponse("ack_success_claim", "fixture_contains_ack_success_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, HARDWARE_VERIFIED_PATTERNS)) {
    return blockedResponse("hardware_verified_claim", "fixture_contains_hardware_or_hil_verified_claim", fixturePath);
  }

  const manualTurn = isObject(loaded.payload.manual_turn_envelope) ? loaded.payload.manual_turn_envelope : {};
  const navigateGoal = isObject(loaded.payload.navigate_goal_envelope) ? loaded.payload.navigate_goal_envelope : {};
  const velocityLimits = isObject(loaded.payload.velocity_limits) ? loaded.payload.velocity_limits : {};
  const steeringLimits = isObject(loaded.payload.steering_limits) ? loaded.payload.steering_limits : {};
  const mapGoalSlot = isObject(loaded.payload.map_goal_slot) ? loaded.payload.map_goal_slot : {};
  const idempotency = isObject(loaded.payload.idempotency_key_requirement) ? loaded.payload.idempotency_key_requirement : {};
  const confirmation = isObject(loaded.payload.confirmation_policy) ? loaded.payload.confirmation_policy : {};
  const robotAck = isObject(loaded.payload.robot_ack_status) ? loaded.payload.robot_ack_status : {};
  const evidenceRef = safeRef(loaded.payload.evidence_ref);
  const auditRefs = safeStringList(loaded.payload.audit_refs, SAMPLE_REF_LIMIT, true);
  const mapFrame = safeText(mapGoalSlot.map_frame ?? navigateGoal.map_frame ?? "map") || "map";
  const ackRef = safeRef(robotAck.ack_ref) || "missing_robot_command_ack";
  const cancelAckRef = safeRef(robotAck.cancel_ack_ref) || "missing_robot_cancel_ack";
  const stopAckRef = safeRef(robotAck.stop_ack_ref) || "missing_robot_stop_ack";
  const recoveryRef = safeRef(robotAck.recovery_ref) || "missing_robot_recovery_event";

  return {
    schema: "trashbot.o7.safe_command_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "fixture_preview_ready",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status: "loaded",
      failure_reason: "",
    },
    source_fixture_schema: SUPPORTED_SCHEMA,
    command_dispatch_enabled: false,
    manual_control_enabled: false,
    navigate_goal_enabled: false,
    keyboard_control_enabled: false,
    real_command_api_connected: false,
    real_robot_ack_connected: false,
    robot_control_executed: false,
    command_session: {
      command_session_id: safeText(loaded.payload.command_session_id || "not_provided"),
      source: "local_json_fixture",
      evidence_ref: evidenceRef,
      audit_refs: auditRefs,
      status: "fixture_summary_only",
    },
    manual_turn_envelope_summary: {
      sends_to_robot: false,
      requested_direction: safeText(manualTurn.requested_direction ?? manualTurn.direction ?? "not_provided"),
      velocity_limited: true,
      steering_limited: true,
      evidence_ref: safeRef(manualTurn.evidence_ref) || "missing_manual_turn_command_envelope_trace",
      status: "fixture_summary_only",
    },
    navigate_goal_envelope_summary: {
      sends_to_robot: false,
      goal_source: safeText(navigateGoal.goal_source ?? "fixture_map_goal_slot") || "fixture_map_goal_slot",
      map_frame: safeText(navigateGoal.map_frame ?? mapFrame) || "map",
      x_m: safeNumber(navigateGoal.x_m ?? navigateGoal.x),
      y_m: safeNumber(navigateGoal.y_m ?? navigateGoal.y),
      yaw_rad: safeNumber(navigateGoal.yaw_rad ?? navigateGoal.yaw),
      evidence_ref: safeRef(navigateGoal.evidence_ref) || "missing_navigate_goal_command_envelope_trace",
      status: "fixture_summary_only",
    },
    velocity_limits: {
      max_linear_mps: safeNumber(velocityLimits.max_linear_mps),
      max_angular_radps: safeNumber(velocityLimits.max_angular_radps),
      source: safeText(velocityLimits.source ?? "local_json_fixture_not_hil") || "local_json_fixture_not_hil",
      hardware_verified: false,
      status: "fixture_limit_summary_only",
    },
    steering_limits: {
      max_steering_angle_rad: safeNumber(steeringLimits.max_steering_angle_rad),
      max_turn_rate_radps: safeNumber(steeringLimits.max_turn_rate_radps),
      source: safeText(steeringLimits.source ?? "local_json_fixture_not_hil") || "local_json_fixture_not_hil",
      hardware_verified: false,
      status: "fixture_limit_summary_only",
    },
    map_goal_slot: {
      map_frame: mapFrame,
      x_m: safeNumber(mapGoalSlot.x_m ?? mapGoalSlot.x),
      y_m: safeNumber(mapGoalSlot.y_m ?? mapGoalSlot.y),
      yaw_rad: safeNumber(mapGoalSlot.yaw_rad ?? mapGoalSlot.yaw),
      status: "fixture_slot_summary_only",
      evidence_ref: safeRef(mapGoalSlot.evidence_ref) || "missing_map_goal_selection_trace",
    },
    idempotency_key_requirement: {
      required: true,
      key_ref: safeRef(idempotency.key_ref ?? idempotency.evidence_ref) || "missing_idempotency_key_requirement",
      header: "Idempotency-Key",
      status: "fixture_requirement_summary_only",
    },
    confirmation_policy: {
      manual_turn_requires_confirmation: true,
      navigate_goal_requires_confirmation: true,
      keyboard_control_requires_hold: true,
      status: safeText(confirmation.status ?? "fixture_policy_summary_only") === "blocked_not_proven"
        ? "blocked_not_proven"
        : "fixture_policy_summary_only",
    },
    robot_ack_summary: {
      ack_status: "blocked_not_proven",
      last_command_id: safeText(robotAck.last_command_id ?? "not_provided"),
      ack_ref: ackRef,
      timeout_ms: safeNumber(robotAck.timeout_ms),
      cancel_ack_ref: cancelAckRef,
      stop_ack_ref: stopAckRef,
      recovery_ref: recoveryRef,
      status: "blocked_not_proven",
    },
    evidence_gaps: defaultEvidenceGaps(loaded.payload.evidence_gaps),
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      session_evidence_ref: evidenceRef,
      ack_ref: ackRef,
      cancel_ack_ref: cancelAckRef,
      stop_ack_ref: stopAckRef,
      recovery_ref: recoveryRef,
      audit_refs: auditRefs,
    },
    blocked_reasons: [
      "real_command_api_not_connected",
      "command_dispatch_disabled",
      "manual_control_disabled",
      "navigate_goal_disabled",
      "keyboard_control_disabled",
      "robot_ack_not_proven",
      "hil_or_hardware_safety_not_proven",
      "delivery_success_not_proven",
    ],
    not_proven: [
      "real_command_api_connected",
      "real_manual_turn_dispatch",
      "real_navigate_goal_dispatch",
      "real_keyboard_control",
      "real_robot_command_ack",
      "real_robot_command_timeout",
      "real_cancel_ack",
      "real_stop_ack",
      "real_recovery_event",
      "real_velocity_limit_hil",
      "real_steering_limit_hil",
      "delivery_success",
    ],
  };
}
