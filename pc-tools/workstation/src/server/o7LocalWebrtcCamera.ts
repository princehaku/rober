import { PROOF_FLAGS } from "../shared/contracts";
import type { O7LocalWebrtcCameraResponse } from "../shared/contracts";

const ENDPOINT = "/api/o7/local-webrtc-camera" as const;
const DEFAULT_CAMERA_BASE_URL = "http://192.168.1.11:8088";
const REMOTE_SELF_TEST_SCHEMA = "trashbot.local_webrtc_camera_offer_self_test.v1" as const;
const REQUEST_TIMEOUT_MS = 1500;

const SAFETY_FIELDS = [
  "safe_to_control",
  "robot_control_executed",
  "sends_commands",
  "cloud_relay",
] as const;

interface LocalCameraOptions {
  env?: NodeJS.ProcessEnv;
}

interface JsonResult {
  ok: boolean;
  status: number | null;
  json: Record<string, unknown> | null;
  reason: string;
}

function responseBase(reason: string, baseUrl = DEFAULT_CAMERA_BASE_URL): O7LocalWebrtcCameraResponse {
  // 基础响应先固定所有危险能力为 false，后续 ready/degraded 也只能追加只读诊断字段。
  return {
    schema: "trashbot.pc_tools_workstation.o7_local_webrtc_camera.v1",
    endpoint: ENDPOINT,
    remote_self_test_schema: REMOTE_SELF_TEST_SCHEMA,
    status: "fail_closed",
    base_url: baseUrl,
    base_url_source: "dev_default_unconfigured",
    camera_page_url: baseUrl,
    host: "not_configured",
    health_http_status: null,
    devices_http_status: null,
    remote_schemas: {
      health: "not_loaded",
      devices: "not_loaded",
    },
    health_status: "not_loaded",
    video_source: "not_loaded",
    device_count: 0,
    dependency_statuses: {},
    dependency_summary: [],
    blocked_reasons: [reason],
    not_proven: [
      "real_browser_video_playback_not_proven",
      "webrtc_offer_answer_not_executed_by_workstation",
      "first_frame_received_not_proven",
      "robot_control_not_connected",
    ],
    fail_closed_reason: reason,
    health_get_executed: false,
    devices_get_executed: false,
    offer_executed: false,
    webrtc_session_created: false,
    sends_commands: false,
    cloud_relay: false,
    robot_control_executed: false,
    fixed_false_fields: {
      safe_to_control: false,
      robot_control_executed: false,
      sends_commands: false,
      cloud_relay: false,
      offer_executed: false,
      webrtc_session_created: false,
    },
    ...PROOF_FLAGS,
  };
}

function normalizeBaseUrl(baseUrl: string): { ok: true; normalized: string } | { ok: false; reason: string } {
  // LAN camera smoke 是 HTTP 诊断页；禁止凭证、query 和 hash，避免配置值变成隐式代理入口。
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    return { ok: false, reason: "base_url_not_configured" };
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return { ok: false, reason: "base_url_invalid_url" };
  }
  if (parsed.protocol !== "http:") {
    return { ok: false, reason: "base_url_protocol_not_allowed" };
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    return { ok: false, reason: "base_url_must_not_include_credentials_query_or_hash" };
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  return { ok: true, normalized: parsed.toString().replace(/\/$/, "") };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // 远端 smoke 必须返回 JSON object；数组和字符串都不能当作健康合同消费。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

async function fetchJson(url: string): Promise<JsonResult> {
  // 这里只做 GET 诊断，短超时失败直接转为机器可读 reason，不阻塞 PC 工作站首屏。
  try {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    const text = await response.text();
    let parsed: unknown = null;
    try {
      parsed = text ? JSON.parse(text) : null;
    } catch {
      return { ok: false, status: response.status, json: null, reason: "remote_json_parse_failed" };
    }
    return {
      ok: response.ok,
      status: response.status,
      json: asRecord(parsed),
      reason: response.ok ? "none" : `remote_http_${response.status}`,
    };
  } catch {
    return { ok: false, status: null, json: null, reason: "remote_fetch_failed" };
  }
}

function dependencyStatuses(health: Record<string, unknown> | null): Record<string, "ok" | "missing" | "unknown"> {
  // Orange Pi smoke 的 imports 字段是依赖真相；坏类型时不能由 PC 前端补造依赖状态。
  const imports = asRecord(health?.imports);
  if (!imports) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(imports).map(([name, loaded]) => [name, loaded === true ? "ok" : loaded === false ? "missing" : "unknown"]),
  );
}

function summarizeDependencies(statuses: Record<string, "ok" | "missing" | "unknown">): string[] {
  // 摘要用于 UI 扫读，仍保留每个依赖的机器可读状态。
  return Object.entries(statuses).map(([name, status]) => `${name}=${status}`);
}

function scanDangerousTrueFields(...records: Array<Record<string, unknown> | null>): string[] {
  // 远端 smoke 若打开任何控制相关字段，PC 侧必须整体 fail closed。
  return records.flatMap((record, index) => {
    if (!record) {
      return [];
    }
    return SAFETY_FIELDS.flatMap((field) => (record[field] === true ? [`response_${index}.${field}`] : []));
  });
}

export async function buildO7LocalWebrtcCamera(options: LocalCameraOptions = {}): Promise<O7LocalWebrtcCameraResponse> {
  const env = options.env ?? process.env;
  const configuredBaseUrl = env.ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL ?? "";
  if (!configuredBaseUrl.trim()) {
    // 未配置时展示开发默认地址但不主动探测，避免把固定 LAN IP 不可达变成页面启动失败。
    return {
      ...responseBase("base_url_not_configured", DEFAULT_CAMERA_BASE_URL),
      status: "not_configured",
      fail_closed_reason: "base_url_not_configured",
      blocked_reasons: ["set_ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL_to_lan_smoke_base_url"],
    };
  }

  const normalized = normalizeBaseUrl(configuredBaseUrl);
  if (!normalized.ok) {
    return {
      ...responseBase(normalized.reason, "blocked_unsafe_url"),
      base_url_source: "env",
    };
  }

  const [health, devices] = await Promise.all([
    fetchJson(`${normalized.normalized}/health`),
    fetchJson(`${normalized.normalized}/devices`),
  ]);
  const healthJson = health.json;
  const devicesJson = devices.json;
  const dangerous = scanDangerousTrueFields(healthJson, devicesJson);
  const statuses = dependencyStatuses(healthJson);
  const deviceList = Array.isArray(devicesJson?.devices) ? devicesJson.devices : [];
  const healthStatus = String(healthJson?.status ?? "not_loaded");
  const blockedReasons = [
    ...(health.ok && healthJson ? [] : [`health_${health.reason}`]),
    ...(devices.ok && devicesJson ? [] : [`devices_${devices.reason}`]),
    ...dangerous.map((field) => `dangerous_true:${field}`),
  ];

  if (blockedReasons.length > 0) {
    return {
      ...responseBase(blockedReasons[0] ?? "remote_fetch_failed", normalized.normalized),
      base_url_source: "env",
      host: String(healthJson?.host ?? new URL(normalized.normalized).host),
      health_http_status: health.status,
      devices_http_status: devices.status,
      remote_schemas: {
        health: String(healthJson?.schema ?? "not_loaded"),
        devices: String(devicesJson?.schema ?? "not_loaded"),
      },
      health_status: healthStatus,
      video_source: String(healthJson?.video_source ?? "not_loaded"),
      device_count: deviceList.length,
      dependency_statuses: statuses,
      dependency_summary: summarizeDependencies(statuses),
      blocked_reasons: blockedReasons,
      health_get_executed: true,
      devices_get_executed: true,
    };
  }

  return {
    ...responseBase("none_remote_health_devices_loaded", normalized.normalized),
    status: healthStatus === "ready" ? "ready" : "degraded",
    base_url_source: "env",
    host: String(healthJson?.host ?? new URL(normalized.normalized).host),
    health_http_status: health.status,
    devices_http_status: devices.status,
    remote_schemas: {
      health: String(healthJson?.schema ?? "not_loaded"),
      devices: String(devicesJson?.schema ?? "not_loaded"),
    },
    health_status: healthStatus,
    video_source: String(healthJson?.video_source ?? "not_loaded"),
    device_count: deviceList.length,
    dependency_statuses: statuses,
    dependency_summary: summarizeDependencies(statuses),
    blocked_reasons: healthStatus === "ready" ? [] : ["remote_health_degraded"],
    fail_closed_reason: healthStatus === "ready" ? "none_health_devices_loaded_offer_not_executed" : "remote_health_degraded",
    health_get_executed: true,
    devices_get_executed: true,
  };
}
