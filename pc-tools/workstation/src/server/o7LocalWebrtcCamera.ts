import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7BrowserPlaybackSmokeSummary,
  O7BrowserPlaybackStabilitySummary,
  O7LocalWebrtcCameraResponse,
  O7LongStabilityAcceptanceSummary,
} from "../shared/contracts";
import fs from "node:fs/promises";
import path from "node:path";
import { displayRoot, WORKSTATION_RUNTIME_ROOT } from "./paths";

const ENDPOINT = "/api/o7/local-webrtc-camera" as const;
const DEFAULT_CAMERA_BASE_URL = "http://192.168.1.11:8088";
const REMOTE_SELF_TEST_SCHEMA = "trashbot.local_webrtc_camera_offer_self_test.v1" as const;
const BROWSER_SMOKE_SCHEMA = "trashbot.o7.local_webrtc_browser_playback_smoke.v1" as const;
const DEFAULT_BROWSER_SMOKE_RESULT = path.join(WORKSTATION_RUNTIME_ROOT, "o7-browser-playback-smoke.json");
const REQUEST_TIMEOUT_MS = 1500;
const LONG_STABILITY_REQUIRED_WINDOW_MS = 180000;

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

function defaultBrowserSmoke(reason: string, baseUrl: string): O7BrowserPlaybackSmokeSummary {
  // PC API 不运行浏览器 smoke；没有显式脚本证据时只能展示 not_run，不能推断首帧成功。
  return {
    schema: BROWSER_SMOKE_SCHEMA,
    status: "not_run",
    base_url: baseUrl,
    page_url: baseUrl,
    executed_at: "not_run",
    browser_engine: "not_run",
    browser_available: false,
    playwright_available: false,
    start_clicked: false,
    first_frame_received: false,
    video_width: null,
    video_height: null,
    first_frame_ms: null,
    connection_state: null,
    ice_connection_state: null,
    ice_gathering_state: null,
    signaling_state: null,
    failure_category: "not_run",
    remote_health_status: null,
    remote_active_peer_connections: null,
    offer_http_status: null,
    offer_error_reason: null,
    offer_error_detail: null,
    observation_window_ms: null,
    final_ready_state: null,
    stable_video_width: null,
    stable_video_height: null,
    ontrack_count: 0,
    receiver_track_states: [],
    transceiver_directions: [],
    inbound_video_stats: [],
    selected_candidate_pair: null,
    peer_state_timeline: [],
    post_smoke_remote_health: null,
    stability_summary: defaultStabilitySummary(),
    long_stability_acceptance: defaultLongStabilityAcceptance(reason),
    console_error_count: 0,
    page_error_count: 0,
    server_peer_id: null,
    server_peer_close_status: "not_attempted",
    console_errors: [],
    page_errors: [],
    blocked_reason: reason,
    report_path: displayRoot(DEFAULT_BROWSER_SMOKE_RESULT),
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    offer_executed_by_browser: false,
    workstation_api_offer_executed: false,
  };
}

function defaultStabilitySummary(): O7BrowserPlaybackStabilitySummary {
  // stability 只接受显式 browser smoke 产物；没有产物时必须保持 not_observed。
  return {
    status: "not_observed",
    observation_window_ms: 0,
    sample_interval_ms: null,
    sample_count: 0,
    first_packets_received: null,
    last_packets_received: null,
    first_frames_decoded: null,
    last_frames_decoded: null,
    first_frames_received: null,
    last_frames_received: null,
    estimated_fps: null,
    estimated_packet_rate: null,
    video_size_stable: "not_available",
    stable_video_width: null,
    stable_video_height: null,
    connection_remained_connected: "not_available",
    ice_remained_connected: "not_available",
    console_errors_added: 0,
    page_errors_added: 0,
    remote_health_samples: 0,
    remote_health_statuses: [],
    remote_active_peer_connections_first: null,
    remote_active_peer_connections_last: null,
    remote_system_metrics: "not_available",
    remote_stability_metrics: "not_available",
    post_close_active_peer_connections: null,
    remote_active_peer_cleaned: "not_available",
  };
}

function defaultLongStabilityAcceptance(blockedReason: string): O7LongStabilityAcceptanceSummary {
  // 长稳态验收必须由显式 artifact 支撑；默认只表达缺口，避免把 30s smoke 外推成 3-5min 通过。
  return {
    status: "not_observed",
    required_window_ms: LONG_STABILITY_REQUIRED_WINDOW_MS,
    observed_window_ms: 0,
    blocked_reasons: [blockedReason],
    safe_to_control: false,
  };
}

function stringArray(value: unknown): string[] {
  // 外部 JSON 只接受字符串数组，避免 UI 展示复杂对象或泄露异常 payload。
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string").slice(0, 20) : [];
}

function recordArray(value: unknown): Array<Record<string, unknown>> {
  // stats 诊断只接受 object 数组并截断，避免把浏览器原始大对象完整塞进 API 响应。
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => Boolean(asRecord(item))).slice(0, 20) : [];
}

function metricRecordOrUnavailable(value: unknown): Record<string, unknown> | "not_available" {
  // 远端 health 的指标字段是可选增量合同；只允许 object 或 not_available 两种展示形态。
  const record = asRecord(value);
  return record ? Object.fromEntries(Object.entries(record).slice(0, 24)) : "not_available";
}

function activePeerCountFromHealth(value: Record<string, unknown> | null): number | null {
  // 兼容远端 health 的 snake_case 与 camelCase，判定 post-close cleanup 时只接受数字。
  const activePeerConnections = value?.active_peer_connections ?? value?.activePeerConnections;
  return typeof activePeerConnections === "number" ? activePeerConnections : null;
}

function longStabilityAcceptanceFromSmoke(
  record: Record<string, unknown>,
  stability: O7BrowserPlaybackStabilitySummary,
): O7LongStabilityAcceptanceSummary {
  // 该函数只做 artifact 消费层验收，不发 /offer、不补采样、不创建任何 WebRTC session。
  const observedWindowMs = stability.observation_window_ms;
  const postCloseHealth = asRecord(record.post_smoke_remote_health);
  const postCloseActivePeers = stability.post_close_active_peer_connections ?? activePeerCountFromHealth(postCloseHealth);
  const postClosePeerCountCleaned = postCloseActivePeers === 0;
  const remoteActivePeerCleaned = stability.remote_active_peer_cleaned === "cleaned";
  const blockedReasons = [
    ...(["ok"].includes(String(record.status)) ? [] : [`browser_smoke_status_${String(record.status ?? "unknown")}`]),
    ...(record.first_frame_received === true ? [] : ["first_frame_not_received"]),
    ...(stability.status === "observed" ? [] : ["stability_summary_not_observed"]),
    ...(stability.sample_count > 0 ? [] : ["stability_sample_count_zero"]),
    ...(observedWindowMs >= LONG_STABILITY_REQUIRED_WINDOW_MS ? [] : ["observation_window_below_180000ms"]),
    ...(stability.connection_remained_connected === "connected" ? [] : ["connection_not_continuously_connected"]),
    ...(stability.ice_remained_connected === "connected" ? [] : ["ice_not_continuously_connected"]),
    ...(stability.video_size_stable === "stable" ? [] : ["video_size_not_stable"]),
    ...(stability.console_errors_added === 0 ? [] : ["console_errors_added"]),
    ...(stability.page_errors_added === 0 ? [] : ["page_errors_added"]),
    ...(postClosePeerCountCleaned ? [] : ["post_close_active_peer_connections_not_zero"]),
    ...(remoteActivePeerCleaned ? [] : ["remote_active_peer_not_cleaned"]),
  ];

  if (record.status === "not_run" || stability.status === "not_observed") {
    return {
      status: "not_observed",
      required_window_ms: LONG_STABILITY_REQUIRED_WINDOW_MS,
      observed_window_ms: observedWindowMs,
      blocked_reasons: blockedReasons.length ? blockedReasons : ["long_stability_artifact_not_observed"],
      safe_to_control: false,
    };
  }

  const onlyWindowTooShort = blockedReasons.length === 1 && blockedReasons[0] === "observation_window_below_180000ms";
  return {
    status: blockedReasons.length === 0 ? "accepted" : onlyWindowTooShort ? "needs_long_run" : "failed",
    required_window_ms: LONG_STABILITY_REQUIRED_WINDOW_MS,
    observed_window_ms: observedWindowMs,
    blocked_reasons: blockedReasons,
    safe_to_control: false,
  };
}

function stabilityFromRecord(value: unknown): O7BrowserPlaybackStabilitySummary {
  // PC API 对显式 smoke JSON 做白名单摘要，避免把任意脚本输出当成 UI 合同。
  const record = asRecord(value);
  if (!record) {
    return defaultStabilitySummary();
  }
  const status = record.status === "observed" ? "observed" : "not_observed";
  const videoSizeStable = ["stable", "changed", "not_available"].includes(String(record.video_size_stable))
    ? (String(record.video_size_stable) as O7BrowserPlaybackStabilitySummary["video_size_stable"])
    : "not_available";
  const connectionRemainedConnected = ["connected", "changed", "not_available"].includes(String(record.connection_remained_connected))
    ? (String(record.connection_remained_connected) as O7BrowserPlaybackStabilitySummary["connection_remained_connected"])
    : "not_available";
  const iceRemainedConnected = ["connected", "changed", "not_available"].includes(String(record.ice_remained_connected))
    ? (String(record.ice_remained_connected) as O7BrowserPlaybackStabilitySummary["ice_remained_connected"])
    : "not_available";
  const remoteActivePeerCleaned = ["cleaned", "not_cleaned", "not_available"].includes(String(record.remote_active_peer_cleaned))
    ? (String(record.remote_active_peer_cleaned) as O7BrowserPlaybackStabilitySummary["remote_active_peer_cleaned"])
    : "not_available";
  return {
    status,
    observation_window_ms: typeof record.observation_window_ms === "number" ? record.observation_window_ms : 0,
    sample_interval_ms: typeof record.sample_interval_ms === "number" ? record.sample_interval_ms : null,
    sample_count: typeof record.sample_count === "number" ? record.sample_count : 0,
    first_packets_received: typeof record.first_packets_received === "number" ? record.first_packets_received : null,
    last_packets_received: typeof record.last_packets_received === "number" ? record.last_packets_received : null,
    first_frames_decoded: typeof record.first_frames_decoded === "number" ? record.first_frames_decoded : null,
    last_frames_decoded: typeof record.last_frames_decoded === "number" ? record.last_frames_decoded : null,
    first_frames_received: typeof record.first_frames_received === "number" ? record.first_frames_received : null,
    last_frames_received: typeof record.last_frames_received === "number" ? record.last_frames_received : null,
    estimated_fps: typeof record.estimated_fps === "number" ? record.estimated_fps : null,
    estimated_packet_rate: typeof record.estimated_packet_rate === "number" ? record.estimated_packet_rate : null,
    video_size_stable: videoSizeStable,
    stable_video_width: typeof record.stable_video_width === "number" ? record.stable_video_width : null,
    stable_video_height: typeof record.stable_video_height === "number" ? record.stable_video_height : null,
    connection_remained_connected: connectionRemainedConnected,
    ice_remained_connected: iceRemainedConnected,
    console_errors_added: typeof record.console_errors_added === "number" ? record.console_errors_added : 0,
    page_errors_added: typeof record.page_errors_added === "number" ? record.page_errors_added : 0,
    remote_health_samples: typeof record.remote_health_samples === "number" ? record.remote_health_samples : 0,
    remote_health_statuses: stringArray(record.remote_health_statuses),
    remote_active_peer_connections_first:
      typeof record.remote_active_peer_connections_first === "number" ? record.remote_active_peer_connections_first : null,
    remote_active_peer_connections_last:
      typeof record.remote_active_peer_connections_last === "number" ? record.remote_active_peer_connections_last : null,
    remote_system_metrics: metricRecordOrUnavailable(record.remote_system_metrics),
    remote_stability_metrics: metricRecordOrUnavailable(record.remote_stability_metrics),
    post_close_active_peer_connections: typeof record.post_close_active_peer_connections === "number" ? record.post_close_active_peer_connections : null,
    remote_active_peer_cleaned: remoteActivePeerCleaned,
  };
}

function browserSmokeFromRecord(record: Record<string, unknown>, fallbackBaseUrl: string, reportPath: string): O7BrowserPlaybackSmokeSummary {
  // browser smoke 是脚本产物；PC API 只做白名单字段摘要，并重新固定控制相关字段为 false。
  const firstFrame = record.first_frame_received === true;
  const status = ["ok", "degraded", "failed", "fail_closed"].includes(String(record.status))
    ? (String(record.status) as O7BrowserPlaybackSmokeSummary["status"])
    : "fail_closed";
  const stabilitySummary = stabilityFromRecord(record.stability_summary);
  return {
    schema: String(record.schema ?? BROWSER_SMOKE_SCHEMA),
    status,
    base_url: String(record.base_url ?? fallbackBaseUrl),
    page_url: String(record.page_url ?? record.base_url ?? fallbackBaseUrl),
    executed_at: String(record.executed_at ?? "unknown"),
    browser_engine: String(record.browser_engine ?? "unknown"),
    browser_available: record.browser_available === true,
    playwright_available: record.playwright_available === true,
    start_clicked: record.start_clicked === true,
    first_frame_received: firstFrame,
    video_width: typeof record.video_width === "number" ? record.video_width : null,
    video_height: typeof record.video_height === "number" ? record.video_height : null,
    first_frame_ms: typeof record.first_frame_ms === "number" ? record.first_frame_ms : null,
    connection_state: typeof record.connection_state === "string" ? record.connection_state : null,
    ice_connection_state: typeof record.ice_connection_state === "string" ? record.ice_connection_state : null,
    ice_gathering_state: typeof record.ice_gathering_state === "string" ? record.ice_gathering_state : null,
    signaling_state: typeof record.signaling_state === "string" ? record.signaling_state : null,
    failure_category: String(record.failure_category ?? (firstFrame ? "none" : "unknown")),
    remote_health_status: typeof record.remote_health_status === "string" ? record.remote_health_status : null,
    remote_active_peer_connections: typeof record.remote_active_peer_connections === "number" ? record.remote_active_peer_connections : null,
    offer_http_status: typeof record.offer_http_status === "number" ? record.offer_http_status : null,
    offer_error_reason: typeof record.offer_error_reason === "string" ? record.offer_error_reason : null,
    offer_error_detail: typeof record.offer_error_detail === "string" ? record.offer_error_detail : null,
    observation_window_ms: typeof record.observation_window_ms === "number" ? record.observation_window_ms : null,
    final_ready_state: typeof record.final_ready_state === "number" ? record.final_ready_state : null,
    stable_video_width: typeof record.stable_video_width === "number" ? record.stable_video_width : null,
    stable_video_height: typeof record.stable_video_height === "number" ? record.stable_video_height : null,
    ontrack_count: typeof record.ontrack_count === "number" ? record.ontrack_count : 0,
    receiver_track_states: recordArray(record.receiver_track_states),
    transceiver_directions: recordArray(record.transceiver_directions),
    inbound_video_stats: recordArray(record.inbound_video_stats),
    selected_candidate_pair: asRecord(record.selected_candidate_pair),
    peer_state_timeline: recordArray(record.peer_state_timeline),
    post_smoke_remote_health: asRecord(record.post_smoke_remote_health),
    stability_summary: stabilitySummary,
    long_stability_acceptance: longStabilityAcceptanceFromSmoke(record, stabilitySummary),
    console_error_count: typeof record.console_error_count === "number" ? record.console_error_count : stringArray(record.console_errors).length,
    page_error_count: typeof record.page_error_count === "number" ? record.page_error_count : stringArray(record.page_errors).length,
    server_peer_id: typeof record.server_peer_id === "string" ? record.server_peer_id : null,
    server_peer_close_status: typeof record.server_peer_close_status === "string" ? record.server_peer_close_status : "not_attempted",
    console_errors: stringArray(record.console_errors),
    page_errors: stringArray(record.page_errors),
    blocked_reason: String(record.blocked_reason ?? (firstFrame ? "none" : "first_frame_not_proven")),
    report_path: displayRoot(reportPath),
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    offer_executed_by_browser: record.offer_executed_by_browser === true,
    workstation_api_offer_executed: false,
  };
}

async function readBrowserSmoke(env: NodeJS.ProcessEnv, baseUrl: string): Promise<O7BrowserPlaybackSmokeSummary> {
  const configuredPath = env.ROBER_O7_BROWSER_SMOKE_RESULT_JSON?.trim();
  const resultPath = configuredPath ? path.resolve(configuredPath) : DEFAULT_BROWSER_SMOKE_RESULT;
  try {
    const parsed = JSON.parse(await fs.readFile(resultPath, "utf8")) as unknown;
    const record = asRecord(parsed);
    if (!record || record.schema !== BROWSER_SMOKE_SCHEMA) {
      return { ...defaultBrowserSmoke("browser_smoke_result_schema_invalid", baseUrl), status: "fail_closed", report_path: displayRoot(resultPath) };
    }
    return browserSmokeFromRecord(record, baseUrl, resultPath);
  } catch {
    return { ...defaultBrowserSmoke("browser_smoke_result_not_found_run_explicit_script", baseUrl), report_path: displayRoot(resultPath) };
  }
}

function responseBase(
  reason: string,
  baseUrl = DEFAULT_CAMERA_BASE_URL,
  browserSmoke = defaultBrowserSmoke("browser_smoke_result_not_loaded", baseUrl),
): O7LocalWebrtcCameraResponse {
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
    browser_smoke: browserSmoke,
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
    const browserSmoke = await readBrowserSmoke(env, DEFAULT_CAMERA_BASE_URL);
    // 未配置时展示开发默认地址但不主动探测，避免把固定 LAN IP 不可达变成页面启动失败。
    return {
      ...responseBase("base_url_not_configured", DEFAULT_CAMERA_BASE_URL, browserSmoke),
      status: "not_configured",
      fail_closed_reason: "base_url_not_configured",
      blocked_reasons: ["set_ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL_to_lan_smoke_base_url"],
    };
  }

  const normalized = normalizeBaseUrl(configuredBaseUrl);
  if (!normalized.ok) {
    const browserSmoke = await readBrowserSmoke(env, "blocked_unsafe_url");
    return {
      ...responseBase(normalized.reason, "blocked_unsafe_url", browserSmoke),
      base_url_source: "env",
    };
  }

  const browserSmoke = await readBrowserSmoke(env, normalized.normalized);
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
      ...responseBase(blockedReasons[0] ?? "remote_fetch_failed", normalized.normalized, browserSmoke),
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
    ...responseBase("none_remote_health_devices_loaded", normalized.normalized, browserSmoke),
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
