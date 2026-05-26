import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7RealtimeElevatorPreviewResponse,
  O7RealtimeElevatorPreviewStateSample,
} from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7RealtimeElevatorPreviewOptions {
  fixtureJson?: string;
}

const SUPPORTED_SCHEMA = "trashbot.o7.realtime_elevator_fixture.v1" as const;
const SAMPLE_STATE_LIMIT = 5;
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
  /\brealtime\s+(success|succeeded|connected|ready|live)\b/i,
  /\boperator\s+console\s+(success|succeeded|ready|live)\b/i,
  /"delivery_success"\s*:\s*true/i,
  /"proof_status"\s*:\s*"(pass|passed|proven|verified)"/i,
];

const CONTROL_CLAIM_PATTERNS = [
  /"primary_actions_enabled"\s*:\s*true/i,
  /"safe_to_control"\s*:\s*true/i,
  /"command_dispatch_enabled"\s*:\s*true/i,
];

const REAL_REALTIME_API_PATTERNS = [
  /"real_realtime_api_connected"\s*:\s*true/i,
  /"realtime_api_connected"\s*:\s*true/i,
  /\breal\s+realtime\s+api\s+(connected|ready|live)\b/i,
];

const ROS2_TF_CONNECTED_PATTERNS = [
  /"real_ros2_tf_connected"\s*:\s*true/i,
  /"ros2_tf_connected"\s*:\s*true/i,
  /"tf_connected"\s*:\s*true/i,
  /\bros2\s+\/?tf\s+(connected|ready|live)\b/i,
];

const LATENCY_LT_2S_PATTERNS = [
  /"latency_lt_2s_proven"\s*:\s*true/i,
  /"latency_under_2s_proven"\s*:\s*true/i,
  /\blatency\s*(<|lt|under)\s*2\s*s(ec|econds)?\s*(proven|pass|passed|verified)?\b/i,
];

const ROUTE_MEMBERSHIP_TRUE_PATTERNS = [
  /"on_route"\s*:\s*true/i,
  /"route_membership"\s*:\s*true/i,
  /\broute\s+membership\s+(true|proven|pass|passed|verified)\b/i,
];

const ELEVATOR_ZONE_TRUE_PATTERNS = [
  /"in_elevator_zone"\s*:\s*true/i,
  /\belevator\s+zone\s+(true|entered|proven|pass|passed|verified)\b/i,
];

const REAL_ELEVATOR_STATE_PATTERNS = [
  /"real_elevator_state_chain_connected"\s*:\s*true/i,
  /"elevator_state_chain_connected"\s*:\s*true/i,
  /\breal\s+elevator\s+state\s+(chain\s+)?(connected|ready|live)\b/i,
  /\belevator\s+state\s+chain\s+(connected|ready|live)\b/i,
];

const ELEVATOR_ARRIVAL_PATTERNS = [
  /"elevator_arrival_proven"\s*:\s*true/i,
  /"arrival_status"\s*:\s*"(arrived|pass|passed|success|succeeded|verified)"/i,
  /\belevator\s+(arrived|arrival\s+proven|pass|passed|success|succeeded)\b/i,
];

const FLOOR_RECOGNITION_PATTERNS = [
  /"floor_recognition_proven"\s*:\s*true/i,
  /"floor_recognized"\s*:\s*true/i,
  /\bfloor\s+(recognition|recognized)\s+(proven|pass|passed|verified|success|succeeded)\b/i,
];

const HUMAN_TAKEOVER_PATTERNS = [
  /"human_takeover_proven"\s*:\s*true/i,
  /"human_takeover"\s*:\s*\{[^}]*"status"\s*:\s*"(proven|pass|passed|verified|success|succeeded)"/i,
  /\bhuman\s+takeover\s+(proven|pass|passed|verified|success|succeeded)\b/i,
];

const ROBOT_CONTROL_EXECUTED_PATTERNS = [
  /"robot_control_executed"\s*:\s*true/i,
  /\brobot\s+control\s+(executed|sent|dispatched)\b/i,
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

// 这个 adapter 只读取用户显式传入的本地 realtime/elevator JSON fixture。
// 它不连接云端实时 API、不读取 ROS2 graph 或 /tf、不连接 Nav2/硬件/电梯设备，也不发命令。
// fixture 中的 on_route、in_elevator_zone、楼层识别和人工接管字段只能作为“请求文本”展示。
// 任何真实连接、低延迟、路线成员、电梯到达、楼层识别或控制执行声明都会 fail closed。
// 所有路径和引用都按 basename 输出，防止本机目录、凭证、串口或控制 topic 泄露给 PC UI。

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown): string {
  // 空值统一为空字符串，避免 null/undefined 被渲染成真实业务状态。
  return value === null || value === undefined ? "" : String(value);
}

function safeText(value: unknown): string {
  // 所有展示文本先脱敏，fixture 不能把凭证、路径或硬件细节透传到响应。
  return SENSITIVE_PATTERNS.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), asText(value));
}

function safeRef(value: unknown): string {
  // evidence/audit 引用只保留文件名；PC preview 不暴露本地目录结构。
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
  // 只接受有限 number，字符串数字不升级，避免 fixture 用文本伪造可验证数值。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function safeBooleanText(value: unknown): string {
  // true 不会变成证明；它只作为 blocked/requested 文本展示，真实输出仍固定 false。
  if (typeof value === "boolean") {
    return value ? "requested_true_not_proven" : "requested_false_not_proven";
  }
  const text = safeText(value).trim();
  return text || "not_provided";
}

function encoded(value: unknown): string {
  // 危险声明扫描覆盖完整 payload；不可序列化时按空对象处理。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function hasPattern(value: unknown, patterns: RegExp[]): boolean {
  // 深层字段也必须被拦截，所以统一扫描 JSON 文本。
  const payload = encoded(value);
  return patterns.some((pattern) => pattern.test(payload));
}

function hasForbiddenCopy(value: unknown): boolean {
  // 命中凭证、串口、ROS 控制 topic 或 traceback 时，不返回任何业务摘要。
  const payload = encoded(value);
  return FORBIDDEN_COPY.some((token) => payload.includes(token));
}

function safeStringList(value: unknown, limit: number): string[] {
  // audit refs 限量输出，避免 preview API 变成原始审计日志导出通道。
  if (!Array.isArray(value)) {
    return [];
  }
  return value.slice(0, limit).map((item) => safeRef(item)).filter(Boolean);
}

function nestedObject(root: JsonObject, key: string): JsonObject {
  // 输入字段可缺省；缺省时按空对象生成 blocked/not_proven 摘要。
  const value = root[key];
  return isObject(value) ? value : {};
}

function sampleState(value: unknown): O7RealtimeElevatorPreviewStateSample {
  // 状态链 sample 只保留 state/status/timestamp/evidence_ref，不透传完整事件 payload。
  const event = isObject(value) ? value : {};
  return {
    state: safeText(event.state ?? event.current_state ?? "not_provided"),
    status: safeText(event.status ?? "fixture_summary_only"),
    timestamp_ms: safeNumber(event.timestamp_ms ?? event.t_ms),
    evidence_ref: safeRef(event.evidence_ref),
  };
}

function stateEvidenceRefs(events: unknown[]): string[] {
  // 状态链引用只用于定位 fixture 槽位，不证明真实电梯事件归档存在。
  return events
    .slice(0, SAMPLE_REF_LIMIT)
    .map((event) => (isObject(event) ? safeRef(event.evidence_ref) : ""))
    .filter(Boolean);
}

function defaultBlockedReasons(payload: JsonObject, stateEvents: unknown[]): string[] {
  // blocked reasons 描述本地 fixture 到真实 O7-KR1/KR2 的缺口，不代表查询过机器人。
  const reasons = [
    "real_realtime_api_not_connected",
    "ros2_tf_forwarding_not_proven",
    "latency_lt_2s_not_proven",
    "route_membership_forced_false",
    "real_elevator_state_chain_not_connected",
    "floor_recognition_not_proven",
    "human_takeover_not_proven",
    "robot_control_disabled",
    "delivery_success_not_proven",
  ];
  if (!asText(payload.map_ref).trim()) {
    reasons.push("map_ref_missing_or_not_connected");
  }
  if (!isObject(payload.robot_pose)) {
    reasons.push("robot_pose_missing_or_not_connected");
  }
  if (stateEvents.length === 0) {
    reasons.push("elevator_state_chain_empty_or_missing");
  }
  return Array.from(new Set(reasons));
}

function blockedResponse(
  status: O7RealtimeElevatorPreviewResponse["input_status"]["status"],
  failureReason: string,
  fixturePath = "",
): O7RealtimeElevatorPreviewResponse {
  // 所有失败都返回同一 schema 和固定 false 开关，调用方不能从异常推断真实连接能力。
  return {
    schema: "trashbot.o7.realtime_elevator_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "blocked_not_proven",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status,
      failure_reason: failureReason,
    },
    source_fixture_schema: "not_loaded",
    real_realtime_api_connected: false,
    real_ros2_tf_connected: false,
    real_elevator_state_chain_connected: false,
    latency_lt_2s_proven: false,
    robot_control_executed: false,
    session: {
      session_id: "not_loaded",
      source: "local_json_fixture",
      evidence_ref: "not_loaded",
      audit_refs: [],
      status: "blocked_not_proven",
    },
    map_summary: {
      map_ref: "not_loaded",
      map_frame: "map",
      source: "local_json_fixture",
      status: "blocked_not_proven",
    },
    robot_pose_summary: {
      x_m: null,
      y_m: null,
      yaw_rad: null,
      pose_source: "not_loaded",
      status: "blocked_not_proven",
    },
    pose_freshness_summary: {
      timestamp_ms: null,
      age_ms: null,
      latency_lt_2s_proven: false,
      status: "blocked_not_proven",
    },
    route_membership_summary: {
      route_id: "not_loaded",
      requested_status: "not_loaded",
      requested_on_route: "blocked_not_proven",
      requested_in_elevator_zone: "blocked_not_proven",
      on_route: false,
      in_elevator_zone: false,
      status: "blocked_not_proven",
    },
    elevator_state_chain_summary: {
      current_state: "not_loaded",
      sample_limit: SAMPLE_STATE_LIMIT,
      count: 0,
      sample: [],
      status: "blocked_not_proven",
    },
    current_floor_evidence_summary: {
      floor_label: "not_loaded",
      confidence: null,
      evidence_ref: "missing_current_floor_evidence",
      status: "blocked_not_proven",
    },
    target_floor_summary: {
      floor_label: "not_loaded",
      confirmation_status: "not_proven",
      evidence_ref: "missing_target_floor_confirmation",
      status: "blocked_not_proven",
    },
    human_takeover_summary: {
      required: true,
      reason: "real_human_takeover_not_proven",
      operator_action: "manual_review_required",
      evidence_ref: "missing_human_takeover_trace",
      status: "blocked_not_proven",
    },
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      session_evidence_ref: "not_loaded",
      audit_refs: [],
      elevator_state_refs: [],
      floor_evidence_ref: "missing_current_floor_evidence",
      target_floor_evidence_ref: "missing_target_floor_confirmation",
      human_takeover_evidence_ref: "missing_human_takeover_trace",
    },
    blocked_reasons: [failureReason],
    not_proven: [
      "real_realtime_api_connected",
      "real_ros2_tf_forwarding",
      "real_map_artifact",
      "real_robot_pose",
      "robot_position_latency_lt_2s",
      "real_route_membership",
      "real_elevator_zone_membership",
      "real_elevator_state_chain",
      "real_floor_recognition",
      "real_target_floor_confirmation",
      "real_human_takeover",
      "real_robot_control",
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

export async function buildO7RealtimeElevatorPreview(
  options: O7RealtimeElevatorPreviewOptions = {},
): Promise<O7RealtimeElevatorPreviewResponse> {
  // 主入口按固定顺序关闸：先验证 schema，再拦截任何真实实时、/tf、电梯或控制声明。
  const fixturePath = asText(options.fixtureJson).trim();
  const loaded = await loadFixture(fixturePath);
  if (!loaded.payload) {
    return blockedResponse(loaded.status as O7RealtimeElevatorPreviewResponse["input_status"]["status"], loaded.reason, fixturePath);
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
  if (hasPattern(loaded.payload, REAL_REALTIME_API_PATTERNS)) {
    return blockedResponse("real_realtime_api_claim", "fixture_contains_real_realtime_api_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ROS2_TF_CONNECTED_PATTERNS)) {
    return blockedResponse("ros2_tf_connected_claim", "fixture_contains_ros2_tf_connected_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, LATENCY_LT_2S_PATTERNS)) {
    return blockedResponse("latency_lt_2s_claim", "fixture_contains_latency_lt_2s_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ROUTE_MEMBERSHIP_TRUE_PATTERNS)) {
    return blockedResponse("route_membership_true_claim", "fixture_contains_route_membership_true_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ELEVATOR_ZONE_TRUE_PATTERNS)) {
    return blockedResponse("in_elevator_zone_true_claim", "fixture_contains_elevator_zone_true_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, REAL_ELEVATOR_STATE_PATTERNS)) {
    return blockedResponse("real_elevator_state_claim", "fixture_contains_real_elevator_state_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ELEVATOR_ARRIVAL_PATTERNS)) {
    return blockedResponse("elevator_arrival_claim", "fixture_contains_elevator_arrival_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, FLOOR_RECOGNITION_PATTERNS)) {
    return blockedResponse("floor_recognition_proven_claim", "fixture_contains_floor_recognition_proven_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, HUMAN_TAKEOVER_PATTERNS)) {
    return blockedResponse("human_takeover_proven_claim", "fixture_contains_human_takeover_proven_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ROBOT_CONTROL_EXECUTED_PATTERNS)) {
    return blockedResponse("robot_control_executed_claim", "fixture_contains_robot_control_executed_claim", fixturePath);
  }

  const pose = nestedObject(loaded.payload, "robot_pose");
  const freshness = nestedObject(loaded.payload, "pose_freshness");
  const routeMembership = nestedObject(loaded.payload, "route_membership");
  const currentFloor = nestedObject(loaded.payload, "current_floor_evidence");
  const targetFloor = nestedObject(loaded.payload, "target_floor");
  const humanTakeover = nestedObject(loaded.payload, "human_takeover");
  const stateEvents = Array.isArray(loaded.payload.elevator_state_chain) ? loaded.payload.elevator_state_chain : [];
  const sampleStates = stateEvents.slice(0, SAMPLE_STATE_LIMIT).map((event) => sampleState(event));
  const auditRefs = safeStringList(loaded.payload.audit_refs, SAMPLE_REF_LIMIT);
  const evidenceRef = safeRef(loaded.payload.evidence_ref);
  const floorEvidenceRef = safeRef(currentFloor.evidence_ref) || "missing_current_floor_evidence";
  const targetFloorEvidenceRef = safeRef(targetFloor.evidence_ref) || "missing_target_floor_confirmation";
  const humanTakeoverEvidenceRef = safeRef(humanTakeover.evidence_ref) || "missing_human_takeover_trace";

  return {
    schema: "trashbot.o7.realtime_elevator_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "fixture_preview_ready",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status: "loaded",
      failure_reason: "",
    },
    source_fixture_schema: SUPPORTED_SCHEMA,
    real_realtime_api_connected: false,
    real_ros2_tf_connected: false,
    real_elevator_state_chain_connected: false,
    latency_lt_2s_proven: false,
    robot_control_executed: false,
    session: {
      session_id: safeText(loaded.payload.session_id || "not_provided"),
      source: "local_json_fixture",
      evidence_ref: evidenceRef,
      audit_refs: auditRefs,
      status: "fixture_summary_only",
    },
    map_summary: {
      map_ref: safeRef(loaded.payload.map_ref) || safeText(loaded.payload.map_ref || "not_provided"),
      map_frame: safeText(loaded.payload.map_frame || "map") || "map",
      source: "local_json_fixture",
      status: "fixture_summary_only",
    },
    robot_pose_summary: {
      x_m: safeNumber(pose.x_m ?? pose.x),
      y_m: safeNumber(pose.y_m ?? pose.y),
      yaw_rad: safeNumber(pose.yaw_rad ?? pose.yaw),
      pose_source: safeText(pose.pose_source ?? pose.source ?? "local_json_fixture_not_tf") || "local_json_fixture_not_tf",
      status: "fixture_summary_only",
    },
    pose_freshness_summary: {
      timestamp_ms: safeNumber(freshness.timestamp_ms ?? freshness.last_update_ms),
      age_ms: safeNumber(freshness.age_ms),
      latency_lt_2s_proven: false,
      status: "fixture_summary_only",
    },
    route_membership_summary: {
      route_id: safeText(routeMembership.route_id ?? "not_provided"),
      requested_status: safeText(routeMembership.status ?? "fixture_summary_only") || "fixture_summary_only",
      requested_on_route: safeBooleanText(routeMembership.on_route),
      requested_in_elevator_zone: safeBooleanText(routeMembership.in_elevator_zone),
      on_route: false,
      in_elevator_zone: false,
      status: "blocked_not_proven",
    },
    elevator_state_chain_summary: {
      current_state: safeText(loaded.payload.current_state ?? sampleStates[0]?.state ?? "not_provided"),
      sample_limit: SAMPLE_STATE_LIMIT,
      count: stateEvents.length,
      sample: sampleStates,
      status: "fixture_summary_only",
    },
    current_floor_evidence_summary: {
      floor_label: safeText(currentFloor.floor_label ?? currentFloor.floor ?? "not_provided"),
      confidence: safeNumber(currentFloor.confidence),
      evidence_ref: floorEvidenceRef,
      status: "fixture_summary_only",
    },
    target_floor_summary: {
      floor_label: safeText(targetFloor.floor_label ?? targetFloor.floor ?? loaded.payload.target_floor ?? "not_provided"),
      confirmation_status: safeText(targetFloor.confirmation_status ?? "not_proven") || "not_proven",
      evidence_ref: targetFloorEvidenceRef,
      status: "fixture_summary_only",
    },
    human_takeover_summary: {
      required: true,
      reason: safeText(humanTakeover.reason ?? "real_human_takeover_not_proven") || "real_human_takeover_not_proven",
      operator_action: safeText(humanTakeover.operator_action ?? "manual_review_required") || "manual_review_required",
      evidence_ref: humanTakeoverEvidenceRef,
      status: "blocked_not_proven",
    },
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      session_evidence_ref: evidenceRef,
      audit_refs: auditRefs,
      elevator_state_refs: stateEvidenceRefs(stateEvents),
      floor_evidence_ref: floorEvidenceRef,
      target_floor_evidence_ref: targetFloorEvidenceRef,
      human_takeover_evidence_ref: humanTakeoverEvidenceRef,
    },
    blocked_reasons: defaultBlockedReasons(loaded.payload, stateEvents),
    not_proven: [
      "real_realtime_api_connected",
      "real_ros2_tf_forwarding",
      "real_map_artifact",
      "real_robot_pose",
      "robot_position_latency_lt_2s",
      "real_route_membership",
      "real_elevator_zone_membership",
      "real_elevator_state_chain",
      "real_current_floor_recognition",
      "real_target_floor_confirmation",
      "real_human_takeover",
      "real_robot_control",
      "delivery_success",
    ],
  };
}
