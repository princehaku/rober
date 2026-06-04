import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7DirectUpperApiCommand,
  O7DirectUpperApiCommandResponse,
  O7DirectUpperApiDirection,
  O7DirectUpperApiRequestResult,
  O7DirectUpperApiSafetyFlags,
  O7DirectUpperApiStatusResponse,
} from "../shared/contracts";

const REQUEST_TIMEOUT_MS = 1200;
const MANUAL_REQUEST_TIMEOUT_MS = 5500;
const MAX_PC_MANUAL_SPEED_MPS = 0.08;
const MAX_PC_MANUAL_DURATION_MS = 350;
const FIELD_DEFAULT_UPPER_API_BASE_URL = "http://192.168.1.11:8787";
const ALLOWED_DIRECTIONS = ["forward", "back", "left", "right", "stop"] as const;
const DEFAULT_SCAN_PROOF_BLOCKERS = ["radar_scan_proof_latest_not_loaded"] as const;
const LOADED_SCAN_PROOF_NOT_OBSERVED_BLOCKERS = ["radar_scan_proof_blocked_or_not_observed"] as const;
type UpperApiBaseUrlSource = "env" | "field_default" | "not_configured";

interface DirectUpperOptions {
  env?: NodeJS.ProcessEnv;
  body?: unknown;
}

interface RemoteJsonResult {
  request: O7DirectUpperApiRequestResult;
  json: Record<string, unknown> | null;
}

interface ResolvedUpperBaseUrl {
  url: string;
  source: UpperApiBaseUrlSource;
}

function safetyFlags(): O7DirectUpperApiSafetyFlags {
  // Direct mode 只说明 PC 本机绕过 cloud relay 访问 8787；不把 HTTP 转发等同于机器人闭环控制。
  return {
    cloud_relay_bypassed: true,
    pc_local_only: true,
    direct_upper_computer_mode: true,
    production_4g_cloud_route_changed: false,
    safe_to_control: false,
    sends_cmd_vel: false,
    sends_wave_rover_json_directly: false,
    robot_control_executed: false,
    robot_ack_connected: false,
    t1001_observed: false,
  };
}

function normalizeBaseUrl(value: string): string {
  // 统一去掉尾部斜杠，避免 path 拼接时出现双斜杠导致测试和现场 curl 证据不一致。
  return value.trim().replace(/\/+$/, "");
}

function configuredUpperBaseUrl(env: NodeJS.ProcessEnv = process.env): ResolvedUpperBaseUrl {
  const configured = normalizeBaseUrl(env.ROBER_UPPER_API_BASE_URL ?? "");
  if (configured) {
    // env 仍然最高优先级，现场如果变更 IP 可以显式覆盖默认值。
    return { url: configured, source: "env" };
  }

  // CEO 本轮指定 PC 现场默认上位机 8787；只给 status 和非底盘 operator 代理使用。
  return { url: "", source: "not_configured" };
}

function resolveFieldUpperBaseUrl(env: NodeJS.ProcessEnv = process.env): ResolvedUpperBaseUrl {
  const configured = configuredUpperBaseUrl(env);
  if (configured.url) {
    return configured;
  }

  // field default 让 direct-upper 雷达/status 链路不再因缺 env 被卡死。
  return { url: FIELD_DEFAULT_UPPER_API_BASE_URL, source: "field_default" };
}

function requestResult(
  path: O7DirectUpperApiRequestResult["path"],
  method: O7DirectUpperApiRequestResult["method"],
  executed: boolean,
  ok: boolean,
  httpStatus: number | null,
  failureReason: string,
): O7DirectUpperApiRequestResult {
  // 统一 request 摘要方便 UI/test 判断是否真的触发过 8787，而不用解析远端原始 payload。
  return {
    path,
    method,
    executed,
    ok,
    http_status: httpStatus,
    failure_reason: failureReason,
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // 远端 JSON 只允许 object 进入摘要层；数组/字符串都视为坏 schema 并 fail closed。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function stringField(record: Record<string, unknown> | null | undefined, key: string, fallback: string): string {
  const value = record?.[key];
  return typeof value === "string" ? value : fallback;
}

function boolField(record: Record<string, unknown> | null | undefined, key: string, fallback: boolean): boolean {
  const value = record?.[key];
  return typeof value === "boolean" ? value : fallback;
}

function numberField(record: Record<string, unknown> | null | undefined, key: string): number | null {
  const value = record?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function nestedRecord(record: Record<string, unknown> | null | undefined, key: string): Record<string, unknown> | null {
  return asRecord(record?.[key]);
}

function stringArrayField(record: Record<string, unknown> | null | undefined, key: string, fallback: readonly string[]): string[] {
  const value = record?.[key];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [...fallback];
}

function scanProofBlockers(scanProofLatest: Record<string, unknown> | null): string[] {
  const blockers = [
    ...stringArrayField(scanProofLatest, "blockers", []),
    ...stringArrayField(scanProofLatest, "blocked_reasons", []),
    ...stringArrayField(nestedRecord(scanProofLatest, "artifact"), "blockers", []),
  ];
  if (blockers.length) {
    return [...new Set(blockers)];
  }

  const artifact = nestedRecord(scanProofLatest, "artifact");
  const artifactStatus = stringField(artifact, "status", stringField(scanProofLatest, "artifact_status", "not_loaded"));
  const latestProofStatus = stringField(scanProofLatest, "latest_proof_status", "not_loaded");
  if (artifactStatus === "loaded" && latestProofStatus === "blocked_or_not_observed") {
    // artifact 已加载但远端摘要没有 blocker 明细时，不能误报成 proof 未加载。
    return [...LOADED_SCAN_PROOF_NOT_OBSERVED_BLOCKERS];
  }

  // Direct status 是给 curl/PC 工具看的机器可读摘要，只有 artifact 缺失/未加载时才显示未加载。
  return [...DEFAULT_SCAN_PROOF_BLOCKERS];
}

async function fetchUpperJson(
  baseUrl: string,
  path: O7DirectUpperApiRequestResult["path"],
  method: O7DirectUpperApiRequestResult["method"],
  body?: unknown,
  timeoutMs = REQUEST_TIMEOUT_MS,
): Promise<RemoteJsonResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${baseUrl}${path}`, {
      method,
      signal: controller.signal,
      headers: method === "POST" ? { "Content-Type": "application/json" } : undefined,
      body: method === "POST" ? JSON.stringify(body ?? {}) : undefined,
    });
    const json = asRecord(await response.json().catch(() => null));
    const failureReason = response.ok ? (json ? "" : "bad_json") : `upper_http_${response.status}`;
    return {
      request: requestResult(path, method, true, response.ok && Boolean(json), response.status, failureReason),
      json,
    };
  } catch (error) {
    const reason = error instanceof Error && error.name === "AbortError" ? "timeout" : error instanceof Error ? error.message : "fetch_failed";
    return {
      request: requestResult(path, method, true, false, null, reason),
      json: null,
    };
  } finally {
    clearTimeout(timeout);
  }
}

function blockedStatus(baseUrl: ResolvedUpperBaseUrl, reason: string): O7DirectUpperApiStatusResponse {
  // 未配置或 8787 不可读时，仍返回完整本机 API 形状，方便浏览器和 curl 工具直接消费。
  return {
    schema: "trashbot.pc_tools_workstation.o7_direct_upper_status.v1",
    endpoint: "/api/o7/direct-upper/status",
    ...PROOF_FLAGS,
    mode: "direct_upper_computer_lan_only",
    status: baseUrl.url ? "fail_closed" : "not_configured",
    upper_api_base_url: baseUrl.url,
    upper_api_base_url_source: baseUrl.source,
    request_timeout_ms: REQUEST_TIMEOUT_MS,
    health_request: requestResult("/health", "GET", false, false, null, baseUrl.url ? "not_executed" : "base_url_not_configured"),
    status_request: requestResult("/api/status", "GET", false, false, null, baseUrl.url ? "not_executed" : "base_url_not_configured"),
    health_summary: { status: "not_loaded", schema: "not_loaded" },
    upper_status_summary: {
      camera_status: "not_loaded",
      radar_scan_status: "not_loaded",
      radar_scan_proof_artifact_status: "not_loaded",
      radar_scan_proof_freshness_status: "unknown",
      radar_scan_proof_age_seconds: null,
      radar_scan_proof_latest_status: "not_loaded",
      radar_scan_proof_blockers: ["radar_scan_proof_latest_not_loaded"],
      radar_raw_packet_proof_artifact_status: "not_loaded",
      radar_raw_packet_proof_freshness_status: "unknown",
      radar_raw_packet_proof_age_seconds: null,
      radar_raw_packet_proof_latest_status: "not_loaded",
      radar_raw_packet_proof_bytes_read: null,
      radar_raw_packet_proof_sync_header_count: null,
      radar_raw_packet_proof_packets_parse_ok: null,
      radar_raw_packet_proof_points_total: null,
      radar_raw_packet_proof_safe_to_control: false,
      map_lifecycle_status: "not_loaded",
      map_artifact_ref: "not_loaded",
      localization_status: "not_loaded",
      operator_report_evidence_ref: "missing_operator_report",
      lidar_port: "not_loaded",
      base_port: "not_loaded",
      base_baudrate: null,
      base_write_control_available: false,
      robot_ack_connected: false,
      t1001_observed: false,
    },
    safety_flags: safetyFlags(),
    local_api_paths: {
      status: "/api/o7/direct-upper/status",
      stop: "/api/o7/direct-upper/base/stop",
      manual: "/api/o7/direct-upper/base/manual",
      feedback_request: "/api/o7/direct-upper/base/feedback-request",
      radar_start: "/api/o7/direct-upper/radar/start",
      radar_stop: "/api/o7/direct-upper/radar/stop",
      map_start: "/api/o7/direct-upper/map/start",
      map_reset: "/api/o7/direct-upper/map/reset",
      map_save: "/api/o7/direct-upper/map/save",
      map_load: "/api/o7/direct-upper/map/load",
      map_list: "/api/o7/direct-upper/map/list",
      localize_reset: "/api/o7/direct-upper/localize/reset",
      operator_report: "/api/o7/direct-upper/operator-report",
    },
    blocked_reasons: [reason],
    failure_reason: reason,
    not_proven: ["upper_8787_health", "upper_8787_status", "robot_ack", "t1001_feedback", "hil_pass"],
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
  };
}

export async function buildO7DirectUpperStatus(options: DirectUpperOptions = {}): Promise<O7DirectUpperApiStatusResponse> {
  const baseUrl = resolveFieldUpperBaseUrl(options.env);
  if (!baseUrl.url) {
    return blockedStatus(baseUrl, "base_url_not_configured");
  }

  const [healthResult, statusResult] = await Promise.all([
    fetchUpperJson(baseUrl.url, "/health", "GET"),
    fetchUpperJson(baseUrl.url, "/api/status", "GET"),
  ]);
  const camera = nestedRecord(statusResult.json, "camera");
  const radar = nestedRecord(statusResult.json, "radar");
  const base = nestedRecord(statusResult.json, "base");
  const map = nestedRecord(statusResult.json, "map");
  const localization = nestedRecord(statusResult.json, "localization");
  const operator = nestedRecord(statusResult.json, "operator");
  const scanProofLatest = nestedRecord(radar, "scan_proof_latest");
  const scanProofArtifact = nestedRecord(scanProofLatest, "artifact");
  const scanProofFreshness = nestedRecord(scanProofLatest, "freshness");
  const rawPacketProofLatest = nestedRecord(radar, "raw_packet_proof_latest");
  const rawPacketProofArtifact = nestedRecord(rawPacketProofLatest, "artifact");
  const rawPacketProofFreshness = nestedRecord(rawPacketProofLatest, "freshness");
  const blockedReasons = [
    ...(healthResult.request.ok ? [] : [`health_${healthResult.request.failure_reason || "failed"}`]),
    ...(statusResult.request.ok ? [] : [`status_${statusResult.request.failure_reason || "failed"}`]),
    ...(boolField(base, "write_control_available", false) ? [] : ["base_write_control_unavailable"]),
    "robot_ack_not_connected",
    "t1001_feedback_not_observed",
  ];

  return {
    schema: "trashbot.pc_tools_workstation.o7_direct_upper_status.v1",
    endpoint: "/api/o7/direct-upper/status",
    ...PROOF_FLAGS,
    mode: "direct_upper_computer_lan_only",
    status: healthResult.request.ok && statusResult.request.ok ? "ready" : healthResult.request.ok || statusResult.request.ok ? "degraded" : "fail_closed",
    upper_api_base_url: baseUrl.url,
    upper_api_base_url_source: baseUrl.source,
    request_timeout_ms: REQUEST_TIMEOUT_MS,
    health_request: healthResult.request,
    status_request: statusResult.request,
    health_summary: {
      status: stringField(healthResult.json, "status", healthResult.request.ok ? "loaded" : "not_loaded"),
      schema: stringField(healthResult.json, "schema", "not_reported"),
    },
    upper_status_summary: {
      camera_status: stringField(camera, "status", "not_loaded"),
      radar_scan_status: stringField(radar, "scan_status", "not_loaded"),
      radar_scan_proof_artifact_status: stringField(scanProofArtifact, "status", stringField(scanProofLatest, "artifact_status", "not_loaded")),
      radar_scan_proof_freshness_status: stringField(scanProofFreshness, "status", stringField(scanProofLatest, "freshness_status", "unknown")),
      radar_scan_proof_age_seconds: numberField(scanProofFreshness, "age_seconds") ?? numberField(scanProofLatest, "age_seconds"),
      radar_scan_proof_latest_status: stringField(scanProofLatest, "latest_proof_status", "not_loaded"),
      radar_scan_proof_blockers: scanProofBlockers(scanProofLatest),
      radar_raw_packet_proof_artifact_status: stringField(rawPacketProofArtifact, "status", stringField(rawPacketProofLatest, "artifact_status", "not_loaded")),
      radar_raw_packet_proof_freshness_status: stringField(rawPacketProofFreshness, "status", stringField(rawPacketProofLatest, "freshness_status", "unknown")),
      radar_raw_packet_proof_age_seconds: numberField(rawPacketProofFreshness, "age_seconds") ?? numberField(rawPacketProofLatest, "age_seconds"),
      radar_raw_packet_proof_latest_status: stringField(rawPacketProofLatest, "latest_proof_status", "not_loaded"),
      radar_raw_packet_proof_bytes_read: numberField(rawPacketProofLatest, "latest_bytes_read"),
      radar_raw_packet_proof_sync_header_count: numberField(rawPacketProofLatest, "latest_sync_header_count"),
      radar_raw_packet_proof_packets_parse_ok: numberField(rawPacketProofLatest, "latest_packets_parse_ok"),
      radar_raw_packet_proof_points_total: numberField(rawPacketProofLatest, "latest_points_total"),
      radar_raw_packet_proof_safe_to_control: false,
      map_lifecycle_status: stringField(map, "lifecycle_status", stringField(map, "status", "not_loaded")),
      map_artifact_ref: stringField(map, "artifact_ref", stringField(map, "map_ref", "not_loaded")),
      localization_status: stringField(localization, "status", "not_loaded"),
      operator_report_evidence_ref: stringField(operator, "latest_evidence_ref", "missing_operator_report"),
      lidar_port: stringField(radar, "observed_lidar_port", "not_loaded"),
      base_port: stringField(base, "port", "not_loaded"),
      base_baudrate: numberField(base, "baudrate"),
      base_write_control_available: boolField(base, "write_control_available", false),
      robot_ack_connected: false,
      t1001_observed: false,
    },
    safety_flags: safetyFlags(),
    local_api_paths: {
      status: "/api/o7/direct-upper/status",
      stop: "/api/o7/direct-upper/base/stop",
      manual: "/api/o7/direct-upper/base/manual",
      feedback_request: "/api/o7/direct-upper/base/feedback-request",
      radar_start: "/api/o7/direct-upper/radar/start",
      radar_stop: "/api/o7/direct-upper/radar/stop",
      map_start: "/api/o7/direct-upper/map/start",
      map_reset: "/api/o7/direct-upper/map/reset",
      map_save: "/api/o7/direct-upper/map/save",
      map_load: "/api/o7/direct-upper/map/load",
      map_list: "/api/o7/direct-upper/map/list",
      localize_reset: "/api/o7/direct-upper/localize/reset",
      operator_report: "/api/o7/direct-upper/operator-report",
    },
    blocked_reasons: blockedReasons,
    failure_reason: blockedReasons.filter((reason) => !["robot_ack_not_connected", "t1001_feedback_not_observed"].includes(reason)).join("/") || "none",
    not_proven: ["robot_ack", "t1001_feedback", "hil_pass", "ros_odom_imu_battery", "delivery_success"],
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
  };
}

function commandResponse(
  schema: O7DirectUpperApiCommandResponse["schema"],
  endpoint: O7DirectUpperApiCommandResponse["endpoint"],
  command: O7DirectUpperApiCommand,
  baseUrl: ResolvedUpperBaseUrl,
  acceptedByWorkstation: boolean,
  upperRequest: O7DirectUpperApiRequestResult,
  failureReason: string,
  payloadSummary: O7DirectUpperApiCommandResponse["command_payload_summary"],
): O7DirectUpperApiCommandResponse {
  const hardBlockedReasons = ["robot_ack_not_connected", "t1001_feedback_not_observed", "field_evidence_not_proven"];
  const blockedReasons = [...(failureReason === "none" ? [] : [failureReason]), ...hardBlockedReasons];
  // sends_commands 表示没有发送 ROS/cmd_vel 或直写 WAVE ROVER JSON；8787 POST 只记录在 upper_request。
  return {
    schema,
    endpoint,
    ...PROOF_FLAGS,
    mode: "direct_upper_computer_lan_only",
    command,
    accepted_by_workstation: acceptedByWorkstation,
    upper_request: upperRequest,
    upper_api_base_url: baseUrl.url,
    upper_api_base_url_source: baseUrl.source,
    cloud_relay_bypassed: true,
    pc_local_only: true,
    fail_closed: !acceptedByWorkstation || !upperRequest.ok,
    failure_reason: failureReason,
    command_payload_summary: payloadSummary,
    robot_ack_connected: false,
    t1001_observed: false,
    safety_flags: safetyFlags(),
    blocked_reasons: blockedReasons,
    not_proven: ["robot_ack", "t1001_feedback", "hil_pass", "actual_motion_or_stop_observed"],
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
  };
}

function stringFromBody(body: Record<string, unknown> | null, key: string, fallback: string): string {
  const value = body?.[key];
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

async function proxyOperatorCommand(
  options: DirectUpperOptions,
  localEndpoint: O7DirectUpperApiCommandResponse["endpoint"],
  remotePath: O7DirectUpperApiRequestResult["path"],
  schema: O7DirectUpperApiCommandResponse["schema"],
  command: O7DirectUpperApiCommand,
  method: O7DirectUpperApiRequestResult["method"] = "POST",
): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  const body = asRecord(options.body);
  const mapId = stringFromBody(body, "map_id", "not_provided");
  const evidenceRef = stringFromBody(body, "evidence_ref", "missing_operator_evidence_ref");
  const reportNote = stringFromBody(body, "note", "");
  const payloadSummary: O7DirectUpperApiCommandResponse["command_payload_summary"] = {
    direction: "not_applicable",
    speed_mps: 0,
    duration_ms: 0,
    clamped_by_pc: false,
    depends_on_upper_8787_guardrail: true,
    map_id: command === "map_load" || command === "map_save" ? mapId : undefined,
    evidence_ref: evidenceRef,
    report_note: command === "operator_report" ? reportNote.slice(0, 120) : undefined,
  };
  const baseUrl = resolveFieldUpperBaseUrl(options.env);
  if (!baseUrl.url) {
    return {
      status: 400,
      payload: commandResponse(
        schema,
        localEndpoint,
        command,
        baseUrl,
        false,
        requestResult(remotePath, method, false, false, null, "base_url_not_configured"),
        "base_url_not_configured",
        payloadSummary,
      ),
    };
  }

  const remoteBody = command === "map_list" ? undefined : { ...body, evidence_ref: evidenceRef };
  const remote = await fetchUpperJson(baseUrl.url, remotePath, method, remoteBody);
  return {
    status: remote.request.ok ? 200 : 502,
    payload: commandResponse(
      schema,
      localEndpoint,
      command,
      baseUrl,
      remote.request.ok,
      remote.request,
      remote.request.ok ? "none" : remote.request.failure_reason || `${command}_failed`,
      payloadSummary,
    ),
  };
}

export async function proxyO7DirectUpperStop(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  const baseUrl = configuredUpperBaseUrl(options.env);
  const summary = {
    direction: "not_applicable" as const,
    speed_mps: 0,
    duration_ms: 0,
    clamped_by_pc: false,
    depends_on_upper_8787_guardrail: true as const,
  };
  if (!baseUrl.url) {
    return {
      status: 400,
      payload: commandResponse(
        "trashbot.pc_tools_workstation.o7_direct_upper_stop.v1",
        "/api/o7/direct-upper/base/stop",
        "stop",
        baseUrl,
        false,
        requestResult("/api/base/stop", "POST", false, false, null, "base_url_not_configured"),
        "base_url_not_configured",
        summary,
      ),
    };
  }
  const remote = await fetchUpperJson(baseUrl.url, "/api/base/stop", "POST", {});
  return {
    status: remote.request.ok ? 200 : 502,
    payload: commandResponse(
      "trashbot.pc_tools_workstation.o7_direct_upper_stop.v1",
      "/api/o7/direct-upper/base/stop",
      "stop",
      baseUrl,
      remote.request.ok,
      remote.request,
      remote.request.ok ? "none" : remote.request.failure_reason || "upper_stop_failed",
      summary,
    ),
  };
}

export async function proxyO7DirectUpperFeedbackRequest(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  const baseUrl = configuredUpperBaseUrl(options.env);
  const summary: O7DirectUpperApiCommandResponse["command_payload_summary"] = {
    direction: "not_applicable",
    speed_mps: 0,
    duration_ms: 0,
    clamped_by_pc: false,
    depends_on_upper_8787_guardrail: true,
    feedback_request_id: "T=130",
    required_feedback_id: "T=1001",
  };
  if (!baseUrl.url) {
    return {
      status: 400,
      payload: commandResponse(
        "trashbot.pc_tools_workstation.o7_direct_upper_feedback_request.v1",
        "/api/o7/direct-upper/base/feedback-request",
        "feedback_request",
        baseUrl,
        false,
        requestResult("/api/base/feedback-request", "POST", false, false, null, "base_url_not_configured"),
        "base_url_not_configured",
        summary,
      ),
    };
  }
  const remote = await fetchUpperJson(baseUrl.url, "/api/base/feedback-request", "POST", {});
  return {
    status: remote.request.ok ? 200 : 502,
    payload: commandResponse(
      "trashbot.pc_tools_workstation.o7_direct_upper_feedback_request.v1",
      "/api/o7/direct-upper/base/feedback-request",
      "feedback_request",
      baseUrl,
      remote.request.ok,
      remote.request,
      remote.request.ok ? "none" : remote.request.failure_reason || "upper_feedback_request_failed",
      summary,
    ),
  };
}

function manualDirection(value: unknown): O7DirectUpperApiDirection | null {
  return typeof value === "string" && ALLOWED_DIRECTIONS.includes(value as O7DirectUpperApiDirection) ? (value as O7DirectUpperApiDirection) : null;
}

function finiteNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

export async function proxyO7DirectUpperManual(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  const body = asRecord(options.body);
  const direction = manualDirection(body?.direction);
  const requestedSpeed = Math.abs(finiteNumber(body?.speed, 0.04));
  const requestedDuration = Math.round(finiteNumber(body?.duration_ms, 250));
  const speed = Math.min(requestedSpeed, MAX_PC_MANUAL_SPEED_MPS);
  const durationMs = Math.min(Math.max(requestedDuration, 1), MAX_PC_MANUAL_DURATION_MS);
  const clamped = speed !== requestedSpeed || durationMs !== requestedDuration;
  const payloadSummary: O7DirectUpperApiCommandResponse["command_payload_summary"] = {
    direction: direction ?? "not_applicable",
    speed_mps: direction ? speed : 0,
    duration_ms: direction ? durationMs : 0,
    clamped_by_pc: clamped,
    depends_on_upper_8787_guardrail: true as const,
  };

  if (!direction) {
    return {
      status: 400,
      payload: commandResponse(
        "trashbot.pc_tools_workstation.o7_direct_upper_manual.v1",
        "/api/o7/direct-upper/base/manual",
        "manual",
        configuredUpperBaseUrl(options.env),
        false,
        requestResult("/api/base/manual", "POST", false, false, null, "invalid_direction"),
        "invalid_direction",
        payloadSummary,
      ),
    };
  }

  const baseUrl = configuredUpperBaseUrl(options.env);
  if (!baseUrl.url) {
    return {
      status: 400,
      payload: commandResponse(
        "trashbot.pc_tools_workstation.o7_direct_upper_manual.v1",
        "/api/o7/direct-upper/base/manual",
        "manual",
        baseUrl,
        false,
        requestResult("/api/base/manual", "POST", false, false, null, "base_url_not_configured"),
        "base_url_not_configured",
        payloadSummary,
      ),
    };
  }

  const remote = await fetchUpperJson(
    baseUrl.url,
    "/api/base/manual",
    "POST",
    {
      direction,
      speed,
      duration_ms: durationMs,
    },
    MANUAL_REQUEST_TIMEOUT_MS,
  );
  return {
    status: remote.request.ok ? 200 : 502,
    payload: commandResponse(
      "trashbot.pc_tools_workstation.o7_direct_upper_manual.v1",
      "/api/o7/direct-upper/base/manual",
      "manual",
      baseUrl,
      remote.request.ok,
      remote.request,
      remote.request.ok ? "none" : remote.request.failure_reason || "upper_manual_failed",
      payloadSummary,
    ),
  };
}

export async function proxyO7DirectUpperRadarStart(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // 雷达 start 只交给 8787 upper API；PC 不碰 LiDAR 串口，也不把 POST 成功当作 /scan 证明。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/radar/start",
    "/api/radar/start",
    "trashbot.pc_tools_workstation.o7_direct_upper_radar_start.v1",
    "radar_start",
  );
}

export async function proxyO7DirectUpperRadarStop(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // 雷达 stop 只关闭 upper API 管理的雷达链路，不触碰底盘 manual/stop 以外的控制面。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/radar/stop",
    "/api/radar/stop",
    "trashbot.pc_tools_workstation.o7_direct_upper_radar_stop.v1",
    "radar_stop",
  );
}

export async function proxyO7DirectUpperMapStart(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // map start 只请求 upper API 进入建图生命周期；浏览器不连接 ROS graph 或 slam_toolbox。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/map/start",
    "/api/map/start",
    "trashbot.pc_tools_workstation.o7_direct_upper_map_start.v1",
    "map_start",
  );
}

export async function proxyO7DirectUpperMapReset(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // reset 可能影响当前 SLAM 会话，必须经 8787 guardrail 和 operator evidence ref 记录。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/map/reset",
    "/api/map/reset",
    "trashbot.pc_tools_workstation.o7_direct_upper_map_reset.v1",
    "map_reset",
  );
}

export async function proxyO7DirectUpperMapSave(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // save 只保存 upper API 认可的 map artifact；PC 不写 ROS map 文件或伪造 artifact。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/map/save",
    "/api/map/save",
    "trashbot.pc_tools_workstation.o7_direct_upper_map_save.v1",
    "map_save",
  );
}

export async function proxyO7DirectUpperMapLoad(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // load 必须通过 upper API 决定可加载 map；PC 只传 map_id/evidence_ref，不直接读写 ROS2 map_server。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/map/load",
    "/api/map/load",
    "trashbot.pc_tools_workstation.o7_direct_upper_map_load.v1",
    "map_load",
  );
}

export async function proxyO7DirectUpperMapList(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // list 是只读 upper API 查询；响应仍按 command envelope 返回，便于 UI 展示 failure/not_proven。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/map/list",
    "/api/map/list",
    "trashbot.pc_tools_workstation.o7_direct_upper_map_list.v1",
    "map_list",
    "GET",
  );
}

export async function proxyO7DirectUpperLocalizeReset(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // localize reset 只请求 upper API 触发定位恢复，不从浏览器发布 /initialpose。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/localize/reset",
    "/api/localize/reset",
    "trashbot.pc_tools_workstation.o7_direct_upper_localize_reset.v1",
    "localize_reset",
  );
}

export async function proxyO7DirectUpperOperatorReport(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  // operator report 用 evidence_ref 串起现场报告；没有报告不能把控制链路写成已验收。
  return proxyOperatorCommand(
    options,
    "/api/o7/direct-upper/operator-report",
    "/api/operator/report",
    "trashbot.pc_tools_workstation.o7_direct_upper_operator_report.v1",
    "operator_report",
  );
}
