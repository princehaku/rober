import { PROOF_FLAGS } from "../shared/contracts";
import type {
  RobotApiEndpointReadback,
  RobotApiProofSummary,
  RobotApiReadEndpointId,
  RobotControlSummaryResponse,
} from "../shared/contracts";

type JsonRecord = Record<string, unknown>;

const ROBOT_CONTROL_SCHEMA = "trashbot.pc_tools_workstation.robot_control_summary.v1" as const;
const REQUEST_TIMEOUT_MS = 1500;

const READ_ENDPOINTS: Array<{ id: RobotApiReadEndpointId; endpoint: string }> = [
  { id: "status", endpoint: "/api/status" },
  { id: "map_proof_latest", endpoint: "/api/map/proof/latest" },
  { id: "localize_proof_latest", endpoint: "/api/localize/proof/latest" },
  { id: "nav2_status", endpoint: "/api/nav2/status" },
  { id: "nav2_proof_latest", endpoint: "/api/nav2/proof/latest" },
  { id: "operator_report_latest", endpoint: "/api/operator/report" },
  { id: "camera_health", endpoint: "/api/camera/health" },
  { id: "camera_devices", endpoint: "/api/camera/devices" },
  { id: "radar_status", endpoint: "/api/radar/status" },
  { id: "radar_scan_proof_latest", endpoint: "/api/radar/scan-proof/latest" },
  { id: "radar_raw_packet_proof_latest", endpoint: "/api/radar/raw-packet-proof/latest" },
  { id: "base_status", endpoint: "/api/base/status" },
  { id: "base_feedback_samples_latest", endpoint: "/api/base/feedback-samples/latest" },
];

const DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "command_dispatch_enabled",
  "manual_control_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "robot_control_executed",
  "sends_commands",
  "sends_motion_commands",
  "sends_base_motion_commands",
  "publishes_cmd_vel",
  "calls_base_manual",
  "starts_ros2",
  "starts_nav2",
  "opens_serial",
  "opens_base_uart",
  "uses_base_uart",
  "hil_pass",
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

function normalizeRobotApiBaseUrl(baseUrl: string): { ok: true; normalized: URL } | { ok: false; reason: string } {
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

function endpointUrl(base: URL, endpoint: string): string {
  // 允许 base URL 带只读网关前缀，但 endpoint 仍由白名单提供，operator 不能拼危险路径。
  const next = new URL(base.toString());
  const prefix = next.pathname === "/" ? "" : next.pathname.replace(/\/+$/, "");
  next.pathname = `${prefix}${endpoint}`;
  next.search = "";
  next.hash = "";
  return next.toString();
}

function scanDangerousTrueFields(value: unknown, path = ""): string[] {
  // 任意层出现危险 true 字段都进入 blocked reason；PC 端仍固定不放开控制按钮。
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanDangerousTrueFields(item, `${path}[${index}]`));
  }
  return Object.entries(value as JsonRecord).flatMap(([key, nested]) => {
    const currentPath = path ? `${path}.${key}` : key;
    const current = DANGEROUS_TRUE_FIELDS.has(key) && nested === true ? [currentPath] : [];
    return current.concat(scanDangerousTrueFields(nested, currentPath));
  });
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

function compactKeyValues(payload: JsonRecord | null): Record<string, string> {
  // 关键字段白名单足够支撑控制台判断，不透传完整上位机 payload。
  const entries = STATUS_KEYS.flatMap((key) => {
    const found = findFirstKey(payload, [key]);
    return found === undefined ? [] : [[key, String(found).slice(0, 120)] as const];
  });
  return Object.fromEntries(entries);
}

async function readEndpoint(base: URL, id: RobotApiReadEndpointId, endpoint: string): Promise<RobotApiEndpointReadback> {
  // 每条读请求都有短超时；失败只影响该 endpoint，不阻断整个控制台 blocked 摘要。
  const url = endpointUrl(base, endpoint);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (error) {
    return {
      id,
      endpoint,
      http_status: null,
      request_status: "fetch_failed",
      schema: "not_loaded",
      status: "fetch_failed",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: [error instanceof Error ? error.message.slice(0, 180) : "fetch_failed"],
      dangerous_true_fields: [],
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
    };
  }

  const dangerous = scanDangerousTrueFields(payload);
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
  };
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
      allowed_methods: ["GET"],
      allowed_endpoint_class: "status_latest_readback_only",
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
      camera: { status: "not_loaded", devices_status: "not_loaded", preview_status: "locked_no_webrtc_session" },
      lidar: { status: "not_loaded", latest_scan_proof_status: "not_loaded", latest_raw_packet_proof_status: "not_loaded" },
      base: { status: "not_loaded", latest_feedback_status: "not_loaded", feedback_ack_status: "not_loaded" },
    },
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
    cmd_vel_topic: "/cmd_vel",
    nav2_goal: "Nav2 NavigateToPose locked",
    map_start: "map start locked",
    radar_start: "radar start locked",
    keyboard_control: "keyboard control locked",
    map_click_goal: "map click goal locked",
    locked_reason: "requires safety lock, HIL gate, robot ACK, timeout/cancel/stop/recovery evidence before enablement",
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
    READ_ENDPOINTS.map((item) => readEndpoint(normalized.normalized, item.id, item.endpoint)),
  );
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
      allowed_methods: ["GET"],
      allowed_endpoint_class: "status_latest_readback_only",
      unsafe_urls_rejected: true,
    },
    observed_at_ms: observedAt,
    read_endpoints: readbacks,
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
        preview_status: "locked_no_webrtc_session",
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
    safe_command_boundary: lockedBoundary(),
    blocked_reasons: blockedReasons.length ? blockedReasons : ["dangerous actions locked by V1 boundary"],
    not_proven: ["O7", "path_generated", "delivery_success", "safe_to_control_true", "real_robot_ack"],
    ...PROOF_FLAGS,
  };
}
