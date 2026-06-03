import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7DirectUpperApiCommandResponse,
  O7DirectUpperApiDirection,
  O7DirectUpperApiRequestResult,
  O7DirectUpperApiSafetyFlags,
  O7DirectUpperApiStatusResponse,
} from "../shared/contracts";

const REQUEST_TIMEOUT_MS = 1200;
const MAX_PC_MANUAL_SPEED_MPS = 0.08;
const MAX_PC_MANUAL_DURATION_MS = 350;
const ALLOWED_DIRECTIONS = ["forward", "back", "left", "right", "stop"] as const;

interface DirectUpperOptions {
  env?: NodeJS.ProcessEnv;
  body?: unknown;
}

interface RemoteJsonResult {
  request: O7DirectUpperApiRequestResult;
  json: Record<string, unknown> | null;
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

function configuredUpperBaseUrl(env: NodeJS.ProcessEnv = process.env): string {
  // 直连模式必须显式配置 8787 base URL；这里不使用历史 dev default，避免误向现场机器人发 POST。
  return (env.ROBER_UPPER_API_BASE_URL ?? "").trim().replace(/\/+$/, "");
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

async function fetchUpperJson(
  baseUrl: string,
  path: O7DirectUpperApiRequestResult["path"],
  method: O7DirectUpperApiRequestResult["method"],
  body?: unknown,
): Promise<RemoteJsonResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
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

function blockedStatus(baseUrl: string, reason: string): O7DirectUpperApiStatusResponse {
  // 未配置或 8787 不可读时，仍返回完整本机 API 形状，方便浏览器和 curl 工具直接消费。
  return {
    schema: "trashbot.pc_tools_workstation.o7_direct_upper_status.v1",
    endpoint: "/api/o7/direct-upper/status",
    ...PROOF_FLAGS,
    mode: "direct_upper_computer_lan_only",
    status: baseUrl ? "fail_closed" : "not_configured",
    upper_api_base_url: baseUrl,
    upper_api_base_url_source: baseUrl ? "env" : "not_configured",
    request_timeout_ms: REQUEST_TIMEOUT_MS,
    health_request: requestResult("/health", "GET", false, false, null, baseUrl ? "not_executed" : "base_url_not_configured"),
    status_request: requestResult("/api/status", "GET", false, false, null, baseUrl ? "not_executed" : "base_url_not_configured"),
    health_summary: { status: "not_loaded", schema: "not_loaded" },
    upper_status_summary: {
      camera_status: "not_loaded",
      radar_scan_status: "not_loaded",
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
  const baseUrl = configuredUpperBaseUrl(options.env);
  if (!baseUrl) {
    return blockedStatus("", "base_url_not_configured");
  }

  const [healthResult, statusResult] = await Promise.all([
    fetchUpperJson(baseUrl, "/health", "GET"),
    fetchUpperJson(baseUrl, "/api/status", "GET"),
  ]);
  const camera = nestedRecord(statusResult.json, "camera");
  const radar = nestedRecord(statusResult.json, "radar");
  const base = nestedRecord(statusResult.json, "base");
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
    upper_api_base_url: baseUrl,
    upper_api_base_url_source: "env",
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
  command: O7DirectUpperApiCommandResponse["command"],
  baseUrl: string,
  acceptedByWorkstation: boolean,
  upperRequest: O7DirectUpperApiRequestResult,
  failureReason: string,
  payloadSummary: O7DirectUpperApiCommandResponse["command_payload_summary"],
): O7DirectUpperApiCommandResponse {
  const hardBlockedReasons = ["robot_ack_not_connected", "t1001_feedback_not_observed"];
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
    upper_api_base_url: baseUrl,
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

export async function proxyO7DirectUpperStop(options: DirectUpperOptions = {}): Promise<{ status: number; payload: O7DirectUpperApiCommandResponse }> {
  const baseUrl = configuredUpperBaseUrl(options.env);
  const summary = {
    direction: "not_applicable" as const,
    speed_mps: 0,
    duration_ms: 0,
    clamped_by_pc: false,
    depends_on_upper_8787_guardrail: true as const,
  };
  if (!baseUrl) {
    return {
      status: 400,
      payload: commandResponse(
        "trashbot.pc_tools_workstation.o7_direct_upper_stop.v1",
        "/api/o7/direct-upper/base/stop",
        "stop",
        "",
        false,
        requestResult("/api/base/stop", "POST", false, false, null, "base_url_not_configured"),
        "base_url_not_configured",
        summary,
      ),
    };
  }
  const remote = await fetchUpperJson(baseUrl, "/api/base/stop", "POST", {});
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
  if (!baseUrl) {
    return {
      status: 400,
      payload: commandResponse(
        "trashbot.pc_tools_workstation.o7_direct_upper_feedback_request.v1",
        "/api/o7/direct-upper/base/feedback-request",
        "feedback_request",
        "",
        false,
        requestResult("/api/base/feedback-request", "POST", false, false, null, "base_url_not_configured"),
        "base_url_not_configured",
        summary,
      ),
    };
  }
  const remote = await fetchUpperJson(baseUrl, "/api/base/feedback-request", "POST", {});
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
  if (!baseUrl) {
    return {
      status: 400,
      payload: commandResponse(
        "trashbot.pc_tools_workstation.o7_direct_upper_manual.v1",
        "/api/o7/direct-upper/base/manual",
        "manual",
        "",
        false,
        requestResult("/api/base/manual", "POST", false, false, null, "base_url_not_configured"),
        "base_url_not_configured",
        payloadSummary,
      ),
    };
  }

  const remote = await fetchUpperJson(baseUrl, "/api/base/manual", "POST", {
    direction,
    speed,
    duration_ms: durationMs,
  });
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
