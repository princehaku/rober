import { PROOF_FLAGS } from "../shared/contracts";
import type {
  RobotApiEndpointReadback,
  RobotApiProofSummary,
  RobotApiReadEndpointId,
  RobotControlOperatorHilMaterialSummary,
  RobotControlMapLifecycleAction,
  RobotControlMapLifecycleEndpoint,
  RobotControlMapLifecycleRequest,
  RobotControlMapLifecycleResponse,
  RobotControlProofRefreshProxyResponse,
  RobotControlProofRefreshKind,
  RobotControlRadarLifecycleAction,
  RobotControlRadarLifecycleEndpoint,
  RobotControlRadarLifecycleResponse,
  RobotControlSummaryResponse,
} from "../shared/contracts";

type JsonRecord = Record<string, unknown>;
type InternalRobotApiEndpointReadback = RobotApiEndpointReadback & {
  payload: JsonRecord | null;
};

const ROBOT_CONTROL_SCHEMA = "trashbot.pc_tools_workstation.robot_control_summary.v1" as const;
const DEFAULT_REQUEST_TIMEOUT_MS = 1500;
const SLOW_READBACK_TIMEOUT_MS = 4000;
export const ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS = 0.12;
export const ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS = 800;
export const ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS = ["forward", "back", "left", "right", "stop"] as const;
export const ROBOT_CONTROL_HIL_CHECKLIST = [
  { id: "operator_ready", label: "现场有人扶控并准备急停" },
  { id: "clearance_confirmed", label: "已确认小车周围无人和障碍" },
  { id: "low_speed_only", label: "本轮仅做低速短时点动" },
  { id: "not_autonomy_mode", label: "本轮不是自动导航任务" },
] as const;

type RobotReadEndpointConfig = {
  id: RobotApiReadEndpointId;
  endpoint: string;
  timeout_ms: number;
};

const READ_ENDPOINTS: RobotReadEndpointConfig[] = [
  // 真实上位机 /api/status 会顺带聚合 camera/radar/base 子摘要，读取窗口要比 proof latest 更宽。
  { id: "status", endpoint: "/api/status", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "map_proof_latest", endpoint: "/api/map/proof/latest", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "localize_proof_latest", endpoint: "/api/localize/proof/latest", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "nav2_status", endpoint: "/api/nav2/status", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "nav2_proof_latest", endpoint: "/api/nav2/proof/latest", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "operator_report_latest", endpoint: "/api/operator/report", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  // camera 端点在真实板端会探测设备与健康摘要，允许更长只读窗口，避免误判成离线。
  { id: "camera_health", endpoint: "/api/camera/health", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "camera_devices", endpoint: "/api/camera/devices", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "radar_status", endpoint: "/api/radar/status", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "radar_scan_proof_latest", endpoint: "/api/radar/scan-proof/latest", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "radar_raw_packet_proof_latest", endpoint: "/api/radar/raw-packet-proof/latest", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  // base 读取仍保持短超时；它被安全边界 blocked 的原因来自危险字段，不应靠放宽超时掩盖。
  { id: "base_status", endpoint: "/api/base/status", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "base_feedback_samples_latest", endpoint: "/api/base/feedback-samples/latest", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
];

export type RobotProofRefreshConfig = {
  kind: RobotControlProofRefreshKind;
  endpoint: "/api/radar/scan-proof/refresh" | "/api/map/proof/refresh" | "/api/nav2/proof/refresh" | "/api/localize/reset";
  request_body: Record<string, unknown>;
  timeout_cap_ms: number;
  safety_margin_ms: number;
  key_fields: string[];
};

const RADAR_SCAN_PROOF_REFRESH_CONFIG: RobotProofRefreshConfig = {
  kind: "radar_scan_proof_refresh",
  endpoint: "/api/radar/scan-proof/refresh",
  request_body: {
    timeout_s: 10,
    runtime_warmup_s: 6,
    start_runtime: true,
  },
  timeout_cap_ms: 60_000,
  safety_margin_ms: 10_000,
  key_fields: [
    "status",
    "latest_proof_status",
    "latest_result_status",
    "evidence_ref",
    "scan_once_observed",
    "scan_hz_observed",
    "raw_packet_once_observed",
    "tf_observed",
    "blocked_reasons",
  ],
};

const MAP_PROOF_REFRESH_CONFIG: RobotProofRefreshConfig = {
  kind: "map_proof_refresh",
  endpoint: "/api/map/proof/refresh",
  request_body: {
    timeout_s: 45,
  },
  timeout_cap_ms: 120_000,
  safety_margin_ms: 20_000,
  key_fields: [
    "status",
    "latest_proof_status",
    "latest_result_status",
    "evidence_ref",
    "map_once_observed",
    "map_file_observed",
    "map_metadata_observed",
    "blocked_reasons",
  ],
};

const NAV2_NO_MOTION_PROOF_REFRESH_CONFIG: RobotProofRefreshConfig = {
  kind: "nav2_no_motion_proof_refresh",
  endpoint: "/api/nav2/proof/refresh",
  request_body: {
    timeout_s: 8,
    managed_runtime_opt_in: false,
    managed_timeout_s: 8,
    managed_map_yaml: "",
    initialpose_opt_in: false,
    path_generation_opt_in: true,
    path_generation_timeout_s: 8,
    path_goal_frame_id: "map",
    path_goal_x: 0.8,
    path_goal_y: 0,
    path_goal_yaw: 0,
  },
  timeout_cap_ms: 60_000,
  safety_margin_ms: 30_000,
  key_fields: [
    "status",
    "latest_proof_status",
    "latest_result_status",
    "evidence_ref",
    "managed_runtime_started",
    "initialpose_published",
    "path_generation_requested",
    "path_generated",
    "path_generation_succeeded",
    "path_point_count",
    "planner_server_active",
    "blocked_reasons",
  ],
};

const LOCALIZATION_RESET_CONFIG: RobotProofRefreshConfig = {
  kind: "localization_reset",
  endpoint: "/api/localize/reset",
  request_body: {
    timeout_s: 8,
    managed_runtime_opt_in: true,
    managed_timeout_s: 12,
    initialpose_opt_in: true,
    initialpose_x: 0,
    initialpose_y: 0,
    initialpose_yaw: 0,
    initialpose_frame_id: "map",
    path_generation_opt_in: false,
  },
  timeout_cap_ms: 60_000,
  safety_margin_ms: 30_000,
  key_fields: [
    "status",
    "latest_proof_status",
    "latest_result_status",
    "evidence_ref",
    "initialpose_published",
    "amcl_pose_observed",
    "localization_tf_observed",
    "managed_runtime_started",
    "managed_runtime_cleanup_ok",
    "localization_reset_observed",
    "root_causes",
    "blocked_reasons",
  ],
};

const NAV2_NO_MOTION_PROOF_LATEST_ENDPOINT = "/api/nav2/proof/latest" as const;

type RobotMapLifecycleConfig = {
  action: RobotControlMapLifecycleAction;
  endpoint: RobotControlMapLifecycleEndpoint;
  method: "GET" | "POST";
};

const MAP_LIFECYCLE_CONFIGS: Record<RobotControlMapLifecycleAction, RobotMapLifecycleConfig> = {
  list: { action: "list", endpoint: "/api/map/list", method: "GET" },
  start: { action: "start", endpoint: "/api/map/start", method: "POST" },
  save: { action: "save", endpoint: "/api/map/save", method: "POST" },
  reset: { action: "reset", endpoint: "/api/map/reset", method: "POST" },
};

type RobotRadarLifecycleConfig = {
  action: RobotControlRadarLifecycleAction;
  endpoint: RobotControlRadarLifecycleEndpoint;
};

const RADAR_LIFECYCLE_CONFIGS: Record<RobotControlRadarLifecycleAction, RobotRadarLifecycleConfig> = {
  start: { action: "start", endpoint: "/api/radar/start" },
  stop: { action: "stop", endpoint: "/api/radar/stop" },
};

const REFRESH_NON_MOTION_EVIDENCE_ACTION_FIELDS = new Set(["sends_commands", "starts_ros2"]);

const HARD_DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "command_dispatch_enabled",
  "manual_control_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "robot_control_executed",
  "sends_motion_commands",
  "sends_base_motion_commands",
  "publishes_cmd_vel",
  "calls_base_manual",
  "starts_nav2",
  "opens_serial",
  "opens_base_uart",
  "uses_base_uart",
  "hil_pass",
]);

const DANGEROUS_TRUE_FIELDS = new Set([...HARD_DANGEROUS_TRUE_FIELDS, ...REFRESH_NON_MOTION_EVIDENCE_ACTION_FIELDS]);
const NO_TRUE_FIELD_EXEMPTIONS = new Set<string>();
const OPERATOR_REPORT_CLAIM_TRUE_FIELD_EXEMPTIONS = new Set([
  "structured_hil_claims.delivery_success",
  "latest_result.structured_hil_claims.delivery_success",
  "latest_result.operator_report.structured_hil_claims.delivery_success",
]);

const STATUS_KEYS = [
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "path_generated",
  "path_generation_requested",
  "path_generation_succeeded",
  "path_point_count",
  "managed_runtime_started",
  "scan_once_observed",
  "map_once_observed",
  "amcl_pose_observed",
  "localization_tf_observed",
  "planner_server_active",
  "latest_path_generated",
  "latest_proof_status",
  "feedback_ack_status",
  "latest_t1001_observed_count",
  "latest_scan_once_observed",
] as const;

function asRecord(value: unknown): JsonRecord | null {
  // 代理只接受 JSON object；数组、字符串等 payload 不进入 UI 摘要。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonRecord) : null;
}

function asString(value: unknown, fallback = "not_loaded"): string {
  // 展示字段统一截断，避免远端错误页或长路径污染控制台布局。
  return typeof value === "string" && value.trim() ? value.trim().slice(0, 180) : fallback;
}

function isPrivateIpv4(hostname: string): boolean {
  // Robot API 只允许回环或 RFC1918 局域网 IPv4，避免 PC 代理变成公网 SSRF 工具。
  const parts = hostname.split(".").map((part) => Number(part));
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part) || part < 0 || part > 255)) {
    return false;
  }
  const a = parts[0] ?? -1;
  const b = parts[1] ?? -1;
  return a === 10 || a === 127 || (a === 192 && b === 168) || (a === 172 && b >= 16 && b <= 31);
}

export function normalizeRobotApiBaseUrl(baseUrl: string): { ok: true; normalized: URL } | { ok: false; reason: string } {
  // 不提供默认地址，是为了避免页面初次加载时误探 workstation 自己或真实机器人。
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    return { ok: false, reason: "baseUrl_not_provided" };
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return { ok: false, reason: "baseUrl_invalid_url" };
  }
  if (parsed.protocol !== "http:") {
    return { ok: false, reason: "baseUrl_protocol_not_allowed" };
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    return { ok: false, reason: "baseUrl_must_not_include_credentials_query_or_hash" };
  }
  if (
    parsed.hostname !== "localhost" &&
    parsed.hostname !== "::1" &&
    parsed.hostname !== "[::1]" &&
    !isPrivateIpv4(parsed.hostname)
  ) {
    return { ok: false, reason: "baseUrl_must_be_loopback_or_private_lan" };
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  return { ok: true, normalized: parsed };
}

export function endpointUrl(base: URL, endpoint: string): string {
  // 允许 base URL 带只读网关前缀，但 endpoint 仍由白名单提供，operator 不能拼危险路径。
  const next = new URL(base.toString());
  const prefix = next.pathname === "/" ? "" : next.pathname.replace(/\/+$/, "");
  next.pathname = `${prefix}${endpoint}`;
  next.search = "";
  next.hash = "";
  return next.toString();
}

export function scanDangerousTrueFields(
  value: unknown,
  path = "",
  fields: ReadonlySet<string> = DANGEROUS_TRUE_FIELDS,
  exemptTruePaths: ReadonlySet<string> = NO_TRUE_FIELD_EXEMPTIONS,
): string[] {
  // 任意层出现危险 true 字段都进入 blocked reason；PC 端仍固定不放开控制按钮。
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanDangerousTrueFields(item, `${path}[${index}]`, fields, exemptTruePaths));
  }
  return Object.entries(value as JsonRecord).flatMap(([key, nested]) => {
    const currentPath = path ? `${path}.${key}` : key;
    // 默认不豁免任何危险字段；只有调用方确认是 operator report claim 时才传精确路径白名单。
    const current = fields.has(key) && nested === true && !exemptTruePaths.has(currentPath) ? [currentPath] : [];
    return current.concat(scanDangerousTrueFields(nested, currentPath, fields, exemptTruePaths));
  });
}

function notLoadedHilMaterialSummary(status: RobotControlOperatorHilMaterialSummary["status"]): RobotControlOperatorHilMaterialSummary {
  // 摘要只用于高级诊断；默认值保持材料缺失，不外推 HIL、delivery 或 safe control。
  return {
    status,
    source_endpoint_id: "operator_report_latest",
    source_path: "operator_report_latest.structured_hil_claims",
    report_status: "not_loaded",
    evidence_ref: "not_loaded",
    external_video: "not_loaded",
    camera_visible: "not_loaded",
    wheel_feedback: "not_loaded",
    lidar_delta: "not_loaded",
    route_map: "not_loaded",
    delivery_claim: "not_loaded",
    site_state: "not_loaded",
  };
}

function boolText(value: unknown): string {
  // claim 布尔值必须原样标成 true/false，不能提升成 proof/pass 文案。
  return typeof value === "boolean" ? String(value) : "not_loaded";
}

function claimWithRef(claim: unknown, ref: unknown): string {
  // 每个现场材料都带引用，便于 operator 追溯原始视频、日志或地图产物。
  const refText = asString(ref, "not_loaded");
  return `${boolText(claim)}; ref=${refText}`;
}

function buildOperatorHilMaterialSummary(
  readbacks: InternalRobotApiEndpointReadback[],
): RobotControlOperatorHilMaterialSummary {
  // 只消费 /api/operator/report 的 structured_hil_claims，不从其它 readback 猜 HIL 状态。
  const operatorReadback = readbacks.find((item) => item.id === "operator_report_latest");
  const payload = operatorReadback?.payload ?? null;
  if (!payload) {
    return notLoadedHilMaterialSummary("not_loaded");
  }
  const claims = asRecord(payload.structured_hil_claims) ?? asRecord(findFirstKey(payload, ["structured_hil_claims"]));
  const reportStatus = asString(findFirstKey(payload, ["operator_report_status"]) ?? findFirstKey(payload, ["status"]), "not_loaded");
  if (!claims) {
    return {
      ...notLoadedHilMaterialSummary("missing"),
      report_status: reportStatus,
      evidence_ref: asString(findFirstKey(payload, ["evidence_ref", "latest_evidence_ref"]), "not_loaded"),
    };
  }
  return {
    status: "loaded",
    source_endpoint_id: "operator_report_latest",
    source_path: "operator_report_latest.structured_hil_claims",
    report_status: reportStatus,
    evidence_ref: asString(findFirstKey(payload, ["evidence_ref", "latest_evidence_ref"]), "not_loaded"),
    external_video: claimWithRef(claims.external_video_recorded, claims.external_video_ref),
    camera_visible: claimWithRef(claims.visible_content_proven, claims.camera_artifacts_ref),
    wheel_feedback: claimWithRef(claims.wheel_feedback_lr_nonzero_proven, claims.wheel_feedback_ref),
    lidar_delta: claimWithRef(claims.physical_motion_lidar_delta_proven, claims.scan_delta_ref),
    route_map: claimWithRef(claims.real_route_map_proven, claims.route_map_ref),
    delivery_claim: boolText(claims.delivery_success),
    site_state: asString(claims.site_state, "not_loaded"),
  };
}

function findFirstKey(value: unknown, keys: string[], depth = 0): unknown {
  // Robot API proof 字段可能位于 latest_result/proof/status 多层结构；递归只读查找但限制深度。
  if (!value || typeof value !== "object" || depth > 6) {
    return undefined;
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findFirstKey(item, keys, depth + 1);
      if (found !== undefined) {
        return found;
      }
    }
    return undefined;
  }
  const record = value as JsonRecord;
  for (const key of keys) {
    if (record[key] !== undefined) {
      return record[key];
    }
  }
  for (const nested of Object.values(record)) {
    const found = findFirstKey(nested, keys, depth + 1);
    if (found !== undefined) {
      return found;
    }
  }
  return undefined;
}

function stringList(value: unknown, limit = 8): string[] {
  // root_causes/not_proven 只做短摘要；对象原因压缩成 JSON 片段用于排障。
  if (!Array.isArray(value)) {
    return [];
  }
  return value.slice(0, limit).map((item) => {
    if (typeof item === "string") {
      return item.slice(0, 180);
    }
    if (item && typeof item === "object") {
      return JSON.stringify(item).slice(0, 180);
    }
    return String(item).slice(0, 180);
  });
}

function compactKeyValues(payload: JsonRecord | null, keys: readonly string[] = STATUS_KEYS): Record<string, string> {
  // 关键字段白名单足够支撑控制台判断，不透传完整上位机 payload。
  const entries = keys.flatMap((key) => {
    const found = findFirstKey(payload, [key]);
    return found === undefined ? [] : [[key, String(found).slice(0, 120)] as const];
  });
  return Object.fromEntries(entries);
}

function compactTrueFields(fields: string[]): string[] {
  // 响应只保留短字段名，避免把完整对象路径直接塞进卡片和日志摘要。
  return fields.map((field) => field.slice(0, 180));
}

function numericSeconds(value: unknown): number | null {
  // 只接受有限正数秒；其他值视为未配置，避免把异常 body 变成无限等待。
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    return null;
  }
  return value;
}

export function computeRobotProofRefreshTimeoutMs(config: Pick<RobotProofRefreshConfig, "request_body" | "timeout_cap_ms" | "safety_margin_ms">): number {
  // 代理 timeout 由 body 预估时长加安全余量推导，并且封顶，避免卡死 workstation。
  const timeoutS = numericSeconds(config.request_body.timeout_s) ?? 0;
  const warmupS = numericSeconds(config.request_body.runtime_warmup_s) ?? 0;
  const managedS = config.request_body.managed_runtime_opt_in === true ? numericSeconds(config.request_body.managed_timeout_s) ?? 0 : 0;
  const pathGenerationS = numericSeconds(config.request_body.path_generation_timeout_s) ?? 0;
  const calculatedMs = Math.round((timeoutS + warmupS + managedS + pathGenerationS) * 1000 + Math.max(0, Math.trunc(config.safety_margin_ms)));
  return Math.min(config.timeout_cap_ms, calculatedMs);
}

function safeMapName(value: unknown): string | null {
  // map_name 会进入上位机 argv；PC 侧先限短基名，板端还会再校验一次。
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== "string") {
    return "";
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  if (trimmed.length > 64 || !/^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/.test(trimmed)) {
    return "";
  }
  return trimmed;
}

function safeLifecycleArtifactPath(value: unknown): string | null {
  // artifact_path 只作为兼容请求字段；上位机会忽略它，PC 仍拒绝绝对路径和穿越。
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== "string") {
    return "";
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  if (trimmed.length > 120 || trimmed.startsWith("/") || trimmed.includes("..") || !/^[A-Za-z0-9._/-]+$/.test(trimmed)) {
    return "";
  }
  return trimmed;
}

function sanitizeMapLifecycleBody(body: unknown): { ok: true; body: RobotControlMapLifecycleRequest } | { ok: false; reason: string } {
  // 固定代理只接受 map_name/artifact_path 两个短字段；未知字段直接拒绝，不做“忽略后转发”。
  if (body === undefined || body === null) {
    return { ok: true, body: {} };
  }
  const payload = asRecord(body);
  if (!payload) {
    return { ok: false, reason: "request_body_must_be_json_object" };
  }
  const unknownKeys = Object.keys(payload).filter((key) => key !== "map_name" && key !== "artifact_path");
  if (unknownKeys.length > 0) {
    return { ok: false, reason: `request_body_unknown_fields:${unknownKeys.slice(0, 4).join("|")}` };
  }
  const mapName = safeMapName(payload.map_name);
  if (mapName === "") {
    return { ok: false, reason: "map_name_invalid_or_too_long" };
  }
  const artifactPath = safeLifecycleArtifactPath(payload.artifact_path);
  if (artifactPath === "") {
    return { ok: false, reason: "artifact_path_invalid_or_too_long" };
  }
  return {
    ok: true,
    body: {
      ...(mapName ? { map_name: mapName } : {}),
      ...(artifactPath ? { artifact_path: artifactPath } : {}),
    },
  };
}

function mapNamesFromPayload(payload: JsonRecord | null): string[] {
  // 地图列表只暴露短文件名摘要，避免把完整上位机路径或大量列表铺进首页。
  const maps = findFirstKey(payload, ["maps"]);
  if (!Array.isArray(maps)) {
    return [];
  }
  return maps.slice(0, 12).flatMap((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      return [];
    }
    const record = item as JsonRecord;
    return typeof record.name === "string" && record.name.trim() ? [record.name.trim().slice(0, 120)] : [];
  });
}

function mapCountFromPayload(payload: JsonRecord | null): number | null {
  // map_count 优先使用上位机字段；缺字段时用 maps 数组长度兜底，仍不证明地图质量。
  const count = findFirstKey(payload, ["map_count"]);
  if (typeof count === "number" && Number.isFinite(count)) {
    return count;
  }
  const maps = findFirstKey(payload, ["maps"]);
  return Array.isArray(maps) ? maps.length : null;
}

function commandResultSummary(payload: JsonRecord | null): RobotControlMapLifecycleResponse["command_result"] {
  // command_result.executed 只作为诊断字段；PC 响应顶层 robot_control_executed 仍固定 false。
  const commandResult = asRecord(findFirstKey(payload, ["command_result"]));
  return {
    mode: asString(commandResult?.mode, "not_loaded"),
    executed: commandResult?.executed === true,
    ok: typeof commandResult?.ok === "boolean" ? commandResult.ok : null,
  };
}

function blockedRadarLifecycleResponse(
  sourceBaseUrl: string,
  config: RobotRadarLifecycleConfig,
  reason: string,
): RobotControlRadarLifecycleResponse {
  // URL、fetch 或危险字段失败时仍返回完整合同，前端不需要为错误态伪造安全字段。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: "lifecycle_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: config.endpoint,
    remote_method: "POST",
    remote_http_status: null,
    status: "blocked",
    command_result: { mode: "not_loaded", executed: false, ok: null },
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function remoteBlockedReasons(payload: JsonRecord | null): string[] {
  // 上位机 guard 的 blocked_reasons 是诊断信息，不自动等同 PC 代理拦截。
  return stringList(findFirstKey(payload, ["blocked_reasons"]), 8);
}

function remoteFailureReasons(payload: JsonRecord | null, prefix: string): string[] {
  // 远端明确 failure 才影响代理状态；command_result.executed 只是诊断字段，不再单独判失败。
  const reasons: string[] = [];
  const failure = asString(findFirstKey(payload, ["failure_reason"]), "");
  if (failure) {
    reasons.push(`${prefix}_remote_failure:${failure}`);
  }
  const error = findFirstKey(payload, ["error"]);
  if (typeof error === "string" && error.trim()) {
    reasons.push(`${prefix}_remote_error:${error.trim().slice(0, 120)}`);
  } else if (error && typeof error === "object") {
    reasons.push(`${prefix}_remote_error`);
  }
  return reasons;
}

export async function buildRadarLifecycleProxy(
  baseUrl: string,
  action: RobotControlRadarLifecycleAction,
): Promise<RobotControlRadarLifecycleResponse> {
  // Radar lifecycle 只代理 start/stop 两个固定传感器 endpoint；浏览器 body 被忽略。
  const config = RADAR_LIFECYCLE_CONFIGS[action];
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedRadarLifecycleResponse(baseUrl, config, normalized.reason);
  }

  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, config.endpoint), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
      signal: AbortSignal.timeout(5000),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? "fetch_timeout_5000ms"
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return {
      ...blockedRadarLifecycleResponse(baseUrl, config, reason),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    };
  }

  let bodyJson: unknown;
  try {
    bodyJson = await response.json();
  } catch {
    return {
      ...blockedRadarLifecycleResponse(baseUrl, config, "response_json_parse_failed"),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_parse_failed", `radar_lifecycle_http_status_${response.status}`],
    };
  }

  const payload = asRecord(bodyJson);
  if (!payload) {
    return {
      ...blockedRadarLifecycleResponse(baseUrl, config, "response_json_not_object"),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_not_object", `radar_lifecycle_http_status_${response.status}`],
    };
  }

  const hardDangerous = scanDangerousTrueFields(payload, "", HARD_DANGEROUS_TRUE_FIELDS);
  const commandResult = commandResultSummary(payload);
  const blockedReasons = [
    ...(response.ok ? [] : [`radar_lifecycle_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
    ...remoteBlockedReasons(payload),
  ];
  const forwarded = response.ok && hardDangerous.length === 0;
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: forwarded ? "lifecycle_forwarded" : "lifecycle_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_method: "POST",
    remote_http_status: response.status,
    status: forwarded ? "loaded_fail_closed_summary" : "blocked",
    command_result: commandResult,
    failure_reason:
      hardDangerous.length > 0
        ? `hard_dangerous_true_field:${hardDangerous[0]}`
        : asString(findFirstKey(payload, ["failure_reason", "error"]), response.ok ? "" : `radar_lifecycle_http_status_${response.status}`),
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    robot_control_executed: false,
  };
}

function blockedMapLifecycleResponse(
  sourceBaseUrl: string,
  config: RobotMapLifecycleConfig,
  reason: string,
  body: RobotControlMapLifecycleRequest = {},
): RobotControlMapLifecycleResponse {
  // URL、body 或 fetch 被拒时仍返回完整 fail-closed 合同，前端不用另造错误态。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: "lifecycle_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: config.endpoint,
    remote_method: config.method,
    remote_http_status: null,
    status: "blocked",
    map_count: null,
    map_names: [],
    command_result: { mode: "not_loaded", executed: false, ok: null },
    request_body: body,
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

export async function buildMapLifecycleProxy(
  baseUrl: string,
  action: RobotControlMapLifecycleAction,
  body: unknown = {},
): Promise<RobotControlMapLifecycleResponse> {
  // 这里是建图 lifecycle 的唯一固定代理：action 决定白名单 endpoint，浏览器不能传动态路径。
  const config = MAP_LIFECYCLE_CONFIGS[action];
  const sanitized = config.method === "GET" ? { ok: true as const, body: {} } : sanitizeMapLifecycleBody(body);
  if (!sanitized.ok) {
    return blockedMapLifecycleResponse(baseUrl, config, sanitized.reason);
  }
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedMapLifecycleResponse(baseUrl, config, normalized.reason, sanitized.body);
  }

  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, config.endpoint), {
      method: config.method,
      headers: config.method === "POST" ? { "Content-Type": "application/json" } : undefined,
      body: config.method === "POST" ? JSON.stringify(sanitized.body) : undefined,
      signal: AbortSignal.timeout(config.action === "start" || config.action === "save" ? 120_000 : 5_000),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? `fetch_timeout_${config.action === "start" || config.action === "save" ? 120_000 : 5_000}ms`
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return {
      ...blockedMapLifecycleResponse(baseUrl, config, reason, sanitized.body),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    };
  }

  let bodyJson: unknown;
  try {
    bodyJson = await response.json();
  } catch {
    return {
      ...blockedMapLifecycleResponse(baseUrl, config, "response_json_parse_failed", sanitized.body),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_parse_failed", `map_lifecycle_http_status_${response.status}`],
    };
  }

  const payload = asRecord(bodyJson);
  if (!payload) {
    return {
      ...blockedMapLifecycleResponse(baseUrl, config, "response_json_not_object", sanitized.body),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_not_object", `map_lifecycle_http_status_${response.status}`],
    };
  }

  const hardDangerous = scanDangerousTrueFields(payload, "", HARD_DANGEROUS_TRUE_FIELDS);
  const commandResult = commandResultSummary(payload);
  const blockedReasons = [
    ...(response.ok ? [] : [`map_lifecycle_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
    ...remoteFailureReasons(payload, "map_lifecycle"),
  ];
  const forwarded = response.ok && blockedReasons.length === 0;
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: forwarded ? "lifecycle_forwarded" : "lifecycle_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_method: config.method,
    remote_http_status: response.status,
    status: forwarded ? "loaded_fail_closed_summary" : "blocked",
    map_count: mapCountFromPayload(payload),
    map_names: mapNamesFromPayload(payload),
    command_result: commandResult,
    request_body: sanitized.body,
    failure_reason:
      blockedReasons.length > 0
        ? blockedReasons[0] ?? "map_lifecycle_blocked"
        : asString(findFirstKey(payload, ["failure_reason", "error"]), ""),
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    robot_control_executed: false,
  };
}

async function readEndpoint(base: URL, config: RobotReadEndpointConfig): Promise<InternalRobotApiEndpointReadback> {
  // 每条读请求都按白名单 endpoint 带独立超时；慢端点允许更宽窗口，但范围仍局限在只读 GET。
  const { id, endpoint, timeout_ms } = config;
  const url = endpointUrl(base, endpoint);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      signal: AbortSignal.timeout(timeout_ms),
    });
  } catch (error) {
    const timeoutReason =
      error instanceof Error && error.name === "TimeoutError"
        ? `fetch_timeout_${timeout_ms}ms`
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return {
      id,
      endpoint,
      http_status: null,
      request_status: "fetch_failed",
      schema: "not_loaded",
      status: "fetch_failed",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: [timeoutReason],
      dangerous_true_fields: [],
      payload: null,
    };
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return {
      id,
      endpoint,
      http_status: response.status,
      request_status: "bad_json",
      schema: "not_loaded",
      status: "bad_json",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: ["response_json_parse_failed"],
      dangerous_true_fields: [],
      payload: null,
    };
  }

  const payload = asRecord(body);
  if (!payload) {
    return {
      id,
      endpoint,
      http_status: response.status,
      request_status: "not_object",
      schema: "not_object",
      status: "not_object",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: ["response_json_not_object"],
      dangerous_true_fields: [],
      payload: null,
    };
  }

  const dangerous = scanDangerousTrueFields(
    payload,
    "",
    DANGEROUS_TRUE_FIELDS,
    id === "operator_report_latest" ? OPERATOR_REPORT_CLAIM_TRUE_FIELD_EXEMPTIONS : NO_TRUE_FIELD_EXEMPTIONS,
  );
  const status = asString(findFirstKey(payload, ["status", "latest_proof_status", "state"]), response.ok ? "loaded" : "blocked");
  return {
    id,
    endpoint,
    http_status: response.status,
    request_status: response.ok && dangerous.length === 0 ? "loaded" : "blocked",
    schema: asString(payload.schema, "schema_missing"),
    status,
    evidence_ref: asString(findFirstKey(payload, ["evidence_ref", "latest_evidence_ref"]), "not_loaded"),
    key_values: compactKeyValues(payload),
    blocked_reasons: [
      ...(response.ok ? [] : [`http_status_${response.status}`]),
      ...dangerous.map((field) => `dangerous_true_field:${field}`),
    ],
    dangerous_true_fields: dangerous,
    payload,
  };
}

function blockedRefreshResponse(
  sourceBaseUrl: string,
  reason: string,
  config: RobotProofRefreshConfig,
): RobotControlProofRefreshProxyResponse {
  // 固定 POST 刷新端点在 URL 不合法时也必须返回同一套 fail-closed 字段，避免 UI 分叉。
  const observedAt = Date.now();
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
    ...PROOF_FLAGS,
    refresh_kind: config.kind,
    proxy_status: "refresh_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: config.endpoint,
    remote_http_status: null,
    status: "blocked",
    last_result_status: "blocked_not_proven",
    last_result_schema: "not_loaded",
    last_result_evidence_ref: "not_loaded",
    last_refreshed_at_ms: observedAt,
    latest_readback_key_values: {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    non_motion_evidence_actions_observed: [],
    robot_control_executed: false,
  };
}

function failedRefreshResponse(
  sourceBaseUrl: string,
  normalizedBaseUrl: URL,
  reason: string,
  config: RobotProofRefreshConfig,
  observedAt: number,
  extras: Partial<RobotControlProofRefreshProxyResponse> = {},
): RobotControlProofRefreshProxyResponse {
  // POST 失败和 Nav2 latest 兜底共用一套响应骨架，避免在错误态漏掉 fail-closed 字段。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
    ...PROOF_FLAGS,
    refresh_kind: config.kind,
    proxy_status: "refresh_failed",
    source_base_url: sourceBaseUrl,
    normalized_base_url: normalizedBaseUrl.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_http_status: null,
    status: "blocked",
    last_result_status: "fetch_failed",
    last_result_schema: "not_loaded",
    last_result_evidence_ref: "not_loaded",
    last_refreshed_at_ms: observedAt,
    latest_readback_key_values: {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    non_motion_evidence_actions_observed: [],
    robot_control_executed: false,
    ...extras,
  };
}

async function nav2LatestReadbackAfterPostFailure(
  baseUrl: string,
  normalizedBaseUrl: URL,
  config: RobotProofRefreshConfig,
  observedAt: number,
  postFailureReason: string,
): Promise<RobotControlProofRefreshProxyResponse> {
  // 只给 Nav2 no-motion refresh 提供固定 latest GET 兜底；不能扩展成任意 GET/POST 代理。
  if (config.kind !== "nav2_no_motion_proof_refresh") {
    return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt);
  }

  let latestResponse: Response;
  try {
    latestResponse = await fetch(endpointUrl(normalizedBaseUrl, NAV2_NO_MOTION_PROOF_LATEST_ENDPOINT), {
      method: "GET",
      signal: AbortSignal.timeout(DEFAULT_REQUEST_TIMEOUT_MS),
    });
  } catch (error) {
    const latestFailure =
      error instanceof Error && error.name === "TimeoutError"
        ? `latest_fetch_timeout_${DEFAULT_REQUEST_TIMEOUT_MS}ms`
        : error instanceof Error
          ? `latest_fetch_failed:${error.message.slice(0, 160)}`
          : "latest_fetch_failed";
    return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
      blocked_reasons: [postFailureReason, latestFailure],
    });
  }

  const latestBody = await latestResponse.json().catch(() => null);
  const latestPayload = asRecord(latestBody);
  if (!latestResponse.ok || !latestPayload) {
    return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
      blocked_reasons: [
        postFailureReason,
        latestPayload ? `latest_http_status_${latestResponse.status}` : "latest_response_json_not_object",
      ],
    });
  }

  const hardDangerous = scanDangerousTrueFields(latestPayload, "", HARD_DANGEROUS_TRUE_FIELDS);
  if (hardDangerous.length > 0) {
    return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
      failure_reason: `hard_dangerous_true_field:${hardDangerous[0]}`,
      blocked_reasons: [
        postFailureReason,
        ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
      ],
      hard_dangerous_true_fields: hardDangerous,
    });
  }

  return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
    last_result_status: asString(
      findFirstKey(latestPayload, ["status", "latest_proof_status", "latest_result_status", "refresh_status", "result_status"]),
      "loaded",
    ),
    last_result_schema: asString(latestPayload.schema, "schema_missing"),
    last_result_evidence_ref: asString(findFirstKey(latestPayload, ["evidence_ref", "latest_evidence_ref", "result_evidence_ref"]), "not_loaded"),
    latest_readback_key_values: compactKeyValues(latestPayload, config.key_fields),
    blocked_reasons: [postFailureReason, "post_timeout_latest_readback_loaded"],
  });
}

async function buildProofRefreshProxy(
  baseUrl: string,
  config: RobotProofRefreshConfig,
): Promise<RobotControlProofRefreshProxyResponse> {
  // refresh 端点只允许固定 POST 路径和固定 body，不能由前端拼接任意控制参数。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedRefreshResponse(baseUrl, normalized.reason, config);
  }

  const timeout_ms = computeRobotProofRefreshTimeoutMs(config);
  const observedAt = Date.now();
  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, config.endpoint), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config.request_body),
      signal: AbortSignal.timeout(timeout_ms),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? `fetch_timeout_${timeout_ms}ms`
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return nav2LatestReadbackAfterPostFailure(baseUrl, normalized.normalized, config, observedAt, reason);
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return {
      schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
      ...PROOF_FLAGS,
      refresh_kind: config.kind,
      proxy_status: "refresh_failed",
      source_base_url: baseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: config.endpoint,
      remote_http_status: response.status,
      status: "blocked",
      last_result_status: "bad_json",
      last_result_schema: "not_loaded",
      last_result_evidence_ref: "not_loaded",
      last_refreshed_at_ms: observedAt,
      latest_readback_key_values: {},
      failure_reason: "response_json_parse_failed",
      blocked_reasons: ["response_json_parse_failed", `refresh_http_status_${response.status}`],
      hard_dangerous_true_fields: [],
      non_motion_evidence_actions_observed: [],
      robot_control_executed: false,
    };
  }

  const payload = asRecord(body);
  if (!payload) {
    return {
      schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
      ...PROOF_FLAGS,
      refresh_kind: config.kind,
      proxy_status: "refresh_failed",
      source_base_url: baseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: config.endpoint,
      remote_http_status: response.status,
      status: "blocked",
      last_result_status: "not_object",
      last_result_schema: "not_object",
      last_result_evidence_ref: "not_loaded",
      last_refreshed_at_ms: observedAt,
      latest_readback_key_values: {},
      failure_reason: "response_json_not_object",
      blocked_reasons: ["response_json_not_object", `refresh_http_status_${response.status}`],
      hard_dangerous_true_fields: [],
      non_motion_evidence_actions_observed: [],
      robot_control_executed: false,
    };
  }

  const hardDangerous = scanDangerousTrueFields(payload, "", HARD_DANGEROUS_TRUE_FIELDS);
  const nonMotionEvidenceActionsObserved = compactTrueFields(
    scanDangerousTrueFields(payload, "", REFRESH_NON_MOTION_EVIDENCE_ACTION_FIELDS),
  );
  const lastResultStatus = asString(
    findFirstKey(payload, ["status", "latest_proof_status", "latest_result_status", "refresh_status", "result_status"]),
    response.ok ? "loaded" : "blocked",
  );
  const lastResultSchema = asString(payload.schema, "schema_missing");
  const lastResultEvidenceRef = asString(findFirstKey(payload, ["evidence_ref", "latest_evidence_ref", "result_evidence_ref"]), "not_loaded");
  const blockedReasons = [
    ...(response.ok ? [] : [`refresh_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
  ];
  const refreshSuccessful = response.ok && hardDangerous.length === 0;

  return {
    schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
    ...PROOF_FLAGS,
    refresh_kind: config.kind,
    proxy_status: refreshSuccessful ? "refresh_forwarded" : "refresh_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_http_status: response.status,
    status: refreshSuccessful ? "loaded_fail_closed_summary" : "blocked",
    last_result_status: lastResultStatus,
    last_result_schema: lastResultSchema,
    last_result_evidence_ref: lastResultEvidenceRef,
    last_refreshed_at_ms: observedAt,
    latest_readback_key_values: compactKeyValues(payload, config.key_fields),
    failure_reason:
      hardDangerous.length > 0
        ? `hard_dangerous_true_field:${hardDangerous[0]}`
        : response.ok
          ? ""
          : `refresh_http_status_${response.status}`,
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    non_motion_evidence_actions_observed: nonMotionEvidenceActionsObserved,
    robot_control_executed: false,
  };
}

export async function buildRadarScanProofRefreshProxy(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // Radar refresh 只允许固定 no-motion scan proof body，不开放任意参数或动作扩展。
  return buildProofRefreshProxy(baseUrl, RADAR_SCAN_PROOF_REFRESH_CONFIG);
}

export async function buildMapProofRefreshProxy(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // Map refresh 只允许固定 no-motion map proof body，不开放导航、建图或控制参数。
  return buildProofRefreshProxy(baseUrl, MAP_PROOF_REFRESH_CONFIG);
}

export async function buildNav2NoMotionProofRefreshProxy(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // Nav2 refresh 只请求 no-motion planner path proof，不启动 Nav2、不发 goal，也不触碰底盘控制链路。
  return buildProofRefreshProxy(baseUrl, NAV2_NO_MOTION_PROOF_REFRESH_CONFIG);
}

export async function buildLocalizationResetProxy(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // 定位 reset 只请求固定 no-motion /initialpose + AMCL proof body，不开放任意 endpoint 或路径生成。
  return buildProofRefreshProxy(baseUrl, LOCALIZATION_RESET_CONFIG);
}

function pickReadback(readbacks: RobotApiEndpointReadback[], id: RobotApiReadEndpointId): RobotApiEndpointReadback | null {
  // 分区摘要按 endpoint id 查找，缺失时明确 unknown，不由 UI 猜测。
  return readbacks.find((item) => item.id === id) ?? null;
}

function proofBoolean(readbacks: RobotApiEndpointReadback[], keys: string[]): boolean | null {
  // readback 摘要中的 bool 已经压成字符串；这里只接受明确 true/false，不做宽松猜测。
  for (const readback of readbacks) {
    for (const key of keys) {
      const value = readback.key_values[key];
      if (value === "true") {
        return true;
      }
      if (value === "false") {
        return false;
      }
    }
  }
  return null;
}

function proofNumber(readbacks: RobotApiEndpointReadback[], keys: string[]): number | null {
  // path_point_count 等字段只在有限数字时展示，缺失时保持 null/not_proven。
  for (const readback of readbacks) {
    for (const key of keys) {
      const value = readback.key_values[key];
      if (value !== undefined && Number.isFinite(Number(value))) {
        return Number(value);
      }
    }
  }
  return null;
}

function buildProofSummary(readbacks: RobotApiEndpointReadback[]): RobotApiProofSummary {
  // O3 proof 只聚合已读回来的 status/latest 字段；没有字段时保持 null/not_proven。
  const payload = readbacks;
  const rootCauses = stringList(findFirstKey(payload, ["root_causes"]));
  const notProven = stringList(findFirstKey(payload, ["not_proven"]), 12);
  return {
    managed_runtime_started: proofBoolean(readbacks, ["managed_runtime_started"]),
    scan_once_observed: proofBoolean(readbacks, ["scan_once_observed", "latest_scan_once_observed"]),
    map_once_observed: proofBoolean(readbacks, ["map_once_observed", "latest_map_once_observed"]),
    amcl_pose_observed: proofBoolean(readbacks, ["amcl_pose_observed", "latest_amcl_pose_observed"]),
    localization_tf_observed: proofBoolean(readbacks, ["localization_tf_observed", "tf_fresh", "latest_tf_fresh"]),
    planner_server_active: proofBoolean(readbacks, ["planner_server_active", "planner_active", "latest_planner_active"]),
    path_generation_requested: proofBoolean(readbacks, ["path_generation_requested", "latest_path_generation_requested"]),
    path_generation_succeeded: proofBoolean(readbacks, ["path_generation_succeeded", "latest_path_generation_succeeded"]),
    path_generated: proofBoolean(readbacks, ["path_generated", "latest_path_generated"]),
    path_point_count: proofNumber(readbacks, ["path_point_count", "latest_path_point_count"]),
    root_causes: rootCauses.length ? rootCauses : ["root_causes_not_loaded"],
    not_proven: notProven.length ? notProven : ["Robot API proof fields not loaded", "delivery_success"],
  };
}

function failClosed(reason: string, sourceBaseUrl: string): RobotControlSummaryResponse {
  // URL 被拒或未配置时也返回完整合同，前端可以稳定展示七区块和恢复路径。
  const observedAt = Date.now();
  return {
    schema: ROBOT_CONTROL_SCHEMA,
    console_status: "blocked",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    proxy_policy: {
      vue_direct_robot_api_access: false,
      node_proxy_only: true,
      allowed_methods: ["GET", "POST"],
      allowed_endpoint_class: "status_latest_readback_plus_fixed_manual_stop",
      unsafe_urls_rejected: true,
    },
    observed_at_ms: observedAt,
    read_endpoints: [],
    o3_proof_summary: {
      managed_runtime_started: null,
      scan_once_observed: null,
      map_once_observed: null,
      amcl_pose_observed: null,
      localization_tf_observed: null,
      planner_server_active: null,
      path_generation_requested: null,
      path_generation_succeeded: null,
      path_generated: null,
      path_point_count: null,
      root_causes: [reason],
      not_proven: ["robot_api_not_loaded", "path_generated", "delivery_success"],
    },
    robot_api_connection: {
      status: sourceBaseUrl.trim() ? "blocked" : "not_configured",
      loaded_count: 0,
      blocked_count: 0,
      failed_count: 0,
      schema_mismatch_count: 0,
      dangerous_true_fields: [],
      blocked_reasons: [reason],
      last_refresh_ms: observedAt,
    },
    readback_summary: {
      camera: { status: "not_loaded", devices_status: "not_loaded", preview_status: "idle_not_started" },
      lidar: { status: "not_loaded", latest_scan_proof_status: "not_loaded", latest_raw_packet_proof_status: "not_loaded" },
      base: { status: "not_loaded", latest_feedback_status: "not_loaded", feedback_ack_status: "not_loaded" },
    },
    operator_hil_material_summary: notLoadedHilMaterialSummary("not_loaded"),
    safe_command_boundary: lockedBoundary(),
    blocked_reasons: [reason],
    not_proven: ["robot_api_readback", "O7", "path_generated", "delivery_success"],
    ...PROOF_FLAGS,
  };
}

function lockedBoundary(): RobotControlSummaryResponse["safe_command_boundary"] {
  // 控制边界集中在后端返回，避免前端以后误加 enabled 状态。
  return {
    manual_endpoint: "/api/base/manual",
    stop_endpoint: "/api/base/stop",
    cmd_vel_topic: "/cmd_vel",
    nav2_goal: "Nav2 NavigateToPose locked",
    map_start: "map start locked",
    radar_start: "radar start locked",
    keyboard_control: "keyboard control locked",
    map_click_goal: "map click goal locked",
    locked_reason: "requires safety lock, HIL gate, robot ACK, timeout/cancel/stop/recovery evidence before enablement",
    manual_motion_entry_status: "controlled_jog_requires_hil_checklist",
    manual_motion_entry_label: "受控点动（需现场确认）",
    allowed_directions: [...ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS],
    non_stop_requires_confirm_hil_checklist: true,
    speed_limit_mps: ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
    duration_limit_ms: ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS,
    hil_checklist: [...ROBOT_CONTROL_HIL_CHECKLIST],
    command_dispatch_enabled: false,
    manual_control_enabled: false,
    navigate_goal_enabled: false,
    keyboard_control_enabled: false,
    robot_control_executed: false,
  };
}

export async function buildRobotControlSummary(baseUrl: string): Promise<RobotControlSummaryResponse> {
  // 这是 PC Robot Control Console V1 的唯一 Robot API 入口；浏览器永远不直连上位机。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosed(normalized.reason, baseUrl);
  }

  const observedAt = Date.now();
  const readbacks = await Promise.all(
    READ_ENDPOINTS.map((item) => readEndpoint(normalized.normalized, item)),
  );
  const readEndpoints: RobotApiEndpointReadback[] = readbacks.map((item) => ({
    // summary 对外只暴露压缩 readback；完整 payload 只在本函数内用于现场材料摘要。
    id: item.id,
    endpoint: item.endpoint,
    http_status: item.http_status,
    request_status: item.request_status,
    schema: item.schema,
    status: item.status,
    evidence_ref: item.evidence_ref,
    key_values: item.key_values,
    blocked_reasons: item.blocked_reasons,
    dangerous_true_fields: item.dangerous_true_fields,
  }));
  const dangerous = readbacks.flatMap((item) => item.dangerous_true_fields.map((field) => `${item.id}.${field}`));
  const loadedCount = readbacks.filter((item) => item.request_status === "loaded").length;
  const failedCount = readbacks.filter((item) => item.request_status === "fetch_failed" || item.request_status === "bad_json" || item.request_status === "not_object").length;
  const blockedCount = readbacks.filter((item) => item.request_status === "blocked").length;
  const schemaMismatchCount = readbacks.filter(
    (item) => item.schema !== "schema_missing" && !item.schema.startsWith("trashbot.upper_robot_api.v1"),
  ).length;
  const blockedReasons = [
    ...readbacks.flatMap((item) => item.blocked_reasons.map((reason) => `${item.id}:${reason}`)),
    ...dangerous.map((field) => `dangerous_true_field:${field}`),
  ];

  return {
    schema: ROBOT_CONTROL_SCHEMA,
    console_status: blockedReasons.length ? "blocked" : "loaded_fail_closed_summary",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    proxy_policy: {
      vue_direct_robot_api_access: false,
      node_proxy_only: true,
      allowed_methods: ["GET", "POST"],
      allowed_endpoint_class: "status_latest_readback_plus_fixed_manual_stop",
      unsafe_urls_rejected: true,
    },
    observed_at_ms: observedAt,
    read_endpoints: readEndpoints,
    o3_proof_summary: buildProofSummary(readbacks),
    robot_api_connection: {
      status: dangerous.length || blockedCount > 0 ? "blocked" : failedCount > 0 ? "degraded" : "readable",
      loaded_count: loadedCount,
      blocked_count: blockedCount,
      failed_count: failedCount,
      schema_mismatch_count: schemaMismatchCount,
      dangerous_true_fields: dangerous,
      blocked_reasons: blockedReasons,
      last_refresh_ms: observedAt,
    },
    readback_summary: {
      camera: {
        status: pickReadback(readbacks, "camera_health")?.status ?? "not_loaded",
        devices_status: pickReadback(readbacks, "camera_devices")?.status ?? "not_loaded",
        preview_status: "idle_not_started",
      },
      lidar: {
        status: pickReadback(readbacks, "radar_status")?.status ?? "not_loaded",
        latest_scan_proof_status: pickReadback(readbacks, "radar_scan_proof_latest")?.status ?? "not_loaded",
        latest_raw_packet_proof_status: pickReadback(readbacks, "radar_raw_packet_proof_latest")?.status ?? "not_loaded",
      },
      base: {
        status: pickReadback(readbacks, "base_status")?.status ?? "not_loaded",
        latest_feedback_status: pickReadback(readbacks, "base_feedback_samples_latest")?.status ?? "not_loaded",
        feedback_ack_status: pickReadback(readbacks, "base_status")?.key_values.feedback_ack_status ?? "not_loaded",
      },
    },
    operator_hil_material_summary: buildOperatorHilMaterialSummary(readbacks),
    safe_command_boundary: lockedBoundary(),
    blocked_reasons: blockedReasons.length ? blockedReasons : ["dangerous actions locked by V1 boundary"],
    not_proven: ["O7", "path_generated", "delivery_success", "safe_to_control_true", "real_robot_ack"],
    ...PROOF_FLAGS,
  };
}
