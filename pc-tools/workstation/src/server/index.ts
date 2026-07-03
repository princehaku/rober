import express from "express";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  buildEvidenceToolsResponse,
  buildHardwareMaterialsResponse,
  buildHealth,
  buildO7CloudArchiveTasks,
  buildO7CloudArchiveTasksProbe,
  buildO7LiveEndpointsManifest,
  buildO7ConsumerTaskDetail,
  buildO7ConsumerTaskList,
  buildO7CloudOperatorConsoleProbe,
  buildO7OperatorConsoleAcceptanceResponse,
  buildO7OperatorConsoleResponse,
  buildO7PreviewsAcceptanceResponse,
  buildO7LabelingPreview,
  buildO7FieldEvidenceConsumerIngest,
  buildO7RealtimeElevatorProbe,
  buildO7RealtimeElevatorPreview,
  buildO7RouteReplayPreview,
  buildO7RtcSignalingContractProbe,
  buildO7SafeCommandPreview,
  buildO7VoicePreview,
  buildProofBoundary,
  buildLocalizationResetProxy,
  buildRadarLifecycleProxy,
  buildRadarScanProofRefreshProxy,
  buildMapLifecycleProxy,
  buildMapPreviewProxy,
  buildMapProofRefreshProxy,
  buildNavGoalPreflightProxy,
  buildNav2LifecycleProxy,
  buildNav2NoMotionProofRefreshProxy,
  buildOperatorReportProxy,
  buildRobotControlSummary,
  buildRouteDebugSummary,
  buildTrainingLabelingResponse,
} from "./catalog";
import { DEFAULT_ROBOT_API_BASE_URL } from "../shared/robotDefaults";
import {
  endpointUrl,
  normalizeRobotApiBaseUrl,
  ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS,
  ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS,
  ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
  ROBOT_CONTROL_KEYBOARD_MANUAL_COMMAND_MODE,
  ROBOT_CONTROL_CAMERA_HEALTH_TIMEOUT_MS,
  ROBOT_CONTROL_SUMMARY_HTTP_READBACK_TIMEOUT_MS,
  NAV2_GOAL_EXECUTION_BLOCKING_REQUIREMENTS,
  NAV2_GOAL_EXECUTION_OPERATOR_PRECHECK_REQUIREMENTS,
  NAV2_GOAL_EXECUTION_PROXY_GUARD_REQUIREMENTS,
  NAV2_GOAL_MINIMAL_PRECHECK_PLAIN,
  notRequiredConfirmedManualOperatorReportPreflight,
  notRequiredOperatorReportPreflight,
  scanDangerousTrueFields,
} from "./robotControlSummary";
import { WORKSTATION_NODE_PORT, WORKSTATION_PUBLIC_HOST } from "../shared/workstationDefaults";
import { PROOF_FLAGS } from "../shared/contracts";
import type { Response } from "express";
import type { RobotControlKeyboardLocalEvidence } from "./robotControlSummary";
import type {
  RobotControlBaseCommandProxyResponse,
  RobotControlBaseCommandRequest,
  RobotControlBaseFeedbackSamplesProxyResponse,
  RobotControlCameraAnswerSummary,
  RobotControlCameraCloseProxyResponse,
  RobotControlCameraFirstFrameProbeProxyResponse,
  RobotControlCameraMjpegStatusResponse,
  RobotControlCameraOfferProxyResponse,
  RobotControlEvidenceCaptureEndpointId,
  RobotControlEvidenceCapturePhase,
  RobotControlEvidenceCaptureStatus,
  RobotControlEvidenceEndpointCapture,
  RobotControlEvidenceReadbackSummary,
  RobotControlFreeRoamAutonomyAction,
  RobotControlFreeRoamAutonomyEndpoint,
  RobotControlFreeRoamAutonomyLatestResponse,
  RobotControlFreeRoamAutonomyResponse,
  RobotControlLiveSummaryResponse,
  RobotControlOperatorReportPreflight,
  RobotControlMapLifecycleAction,
  RobotControlNav2LifecycleAction,
  RobotControlRadarLifecycleAction,
  RobotControlRadarStatusResponse,
  RobotControlReadOnlyStatusRemoteEndpoint,
  RobotControlReadOnlyStatusResponse,
  RobotControlReadOnlyStatusWorkstationEndpoint,
  RobotControlNavGoalExecutionResponse,
  RobotControlNavGoalExecutionLatestResponse,
  RobotControlDeliveryCompleteRequest,
  RobotControlDeliveryCompleteResponse,
  RobotControlDeliveryLatestResponse,
  RobotControlDeliveryGapCheckResponse,
  RobotControlSummaryResponse,
} from "../shared/contracts";
import type {
  RobotControlCameraFirstFrameProbeOverlay,
  RobotControlCameraMjpegRelayOverlay,
} from "./robotControlSummary";

const CAMERA_FIRST_FRAME_FAILURE_REASONS = new Set([
  "capture_read_returned_false",
  "capture_read_call_timeout",
  "first_frame_timeout",
  "first_frame_total_timeout",
]);
const FREE_ROAM_MAPPING_REQUIRED_GATE_IDS = [
  "camera_first_frame",
  "lidar_fresh",
  "mapping_active",
  "fresh_map_preview",
] as const;
const FREE_ROAM_MAPPING_START_REQUIRED_GATE_IDS = [
  "camera_first_frame",
  "lidar_fresh",
] as const;
const CAMERA_FIRST_FRAME_PROBE_TIMEOUT_MS = 12_000;
const CAMERA_FIRST_FRAME_BACKEND_SMOKE_TIMEOUT_MS = 45_000;
const CAMERA_USB_RECOVERY_TIMEOUT_MS = 60_000;
const PORT = Number(process.env.PORT ?? WORKSTATION_NODE_PORT);
const HOST = process.env.HOST ?? WORKSTATION_PUBLIC_HOST;
// summary 里 MJPEG overlay 只是首屏辅助诊断，不能比真正 summary 读回更慢。
const ROBOT_CONTROL_SUMMARY_CAMERA_OVERLAY_TIMEOUT_MS = 600;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_ROOT = path.resolve(__dirname, "../../dist");

export function workstationListenAddress(): string {
  // 启动日志统一走同一个地址格式，避免 public 脚本排障时出现口径漂移。
  return `http://${HOST}:${PORT}`;
}

export function listenFailureHint(error: NodeJS.ErrnoException, host = HOST, port = PORT): string {
  // 7001 是 PC 工作站自己的公开入口；端口被占时必须给出下一手，而不是只吐 Node 栈。
  if (error.code !== "EADDRINUSE") {
    return `pc-tools workstation API failed to listen on ${host}:${port}: ${error.message}`;
  }
  return [
    `pc-tools workstation API failed to listen on ${host}:${port}: address already in use.`,
    `检查占用进程: lsof -nP -iTCP:${port} -sTCP:LISTEN || netstat -anv | rg '[.:]${port} .*LISTEN'`,
    "停掉占用进程后重试，或临时改用 PORT=<free-port> npm run api。",
  ].join("\n");
}

function queryString(value: unknown): string {
  // Express query 可能是数组或对象；只接受单个字符串，其他形态 fail closed 为空。
  // 为空会让 catalog 返回 not_proven/blocked，而不是把异常 query 当路径读取。
  return typeof value === "string" ? value : "";
}

function queryBoolean(value: unknown): boolean | undefined {
  // 布尔 query 只接受显式 true/false；其他拼写不参与证据覆盖，避免 URL 噪声改变验收状态。
  const text = queryString(value).trim().toLowerCase();
  if (["true", "1", "yes", "y"].includes(text)) {
    return true;
  }
  if (["false", "0", "no", "n"].includes(text)) {
    return false;
  }
  return undefined;
}

function queryNonNegativeInteger(value: unknown): number | undefined {
  // pulse 计数必须是非负整数；非法数字直接丢弃，由 summary builder 使用保守默认。
  const text = queryString(value).trim();
  if (!/^\d+$/.test(text)) {
    return undefined;
  }
  const parsed = Number(text);
  return Number.isSafeInteger(parsed) ? parsed : undefined;
}

function robotControlKeyboardEvidenceQuery(query: Record<string, unknown>): RobotControlKeyboardLocalEvidence | undefined {
  // 这份 evidence 只描述 PC 当前页面的键盘 hold 窗口，不代表上位机持久事实或 HIL 完成。
  const evidence: RobotControlKeyboardLocalEvidence = {
    keyboard_enabled: queryBoolean(query.keyboard_enabled),
    keyboard_armed: queryBoolean(query.keyboard_armed),
    keyboard_current_direction: queryString(query.keyboard_current_direction).trim() || undefined,
    keyboard_current_hold_pulse_count: queryNonNegativeInteger(query.keyboard_current_hold_pulse_count),
    keyboard_best_continuous_pulse_count: queryNonNegativeInteger(query.keyboard_best_continuous_pulse_count),
    keyboard_verified_min_forwarded_pulses: queryNonNegativeInteger(query.keyboard_verified_min_forwarded_pulses),
    keyboard_continuous_pulse_verified: queryBoolean(query.keyboard_continuous_pulse_verified),
    keyboard_stop_settled_after_pulse: queryBoolean(query.keyboard_stop_settled_after_pulse),
    keyboard_motion_verified: queryBoolean(query.keyboard_motion_verified),
  };
  const hasEvidence = Object.values(evidence).some((value) => value !== undefined);
  return hasEvidence ? evidence : undefined;
}

export function robotControlSummaryQueryBaseUrl(value: unknown): string {
  // summary 是普通首屏的只读入口；没有 query 时默认连固定小车，避免现场手填地址。
  return robotControlReadOnlyQueryBaseUrl(value);
}

export function robotControlReadOnlyQueryBaseUrl(value: unknown): string {
  // 所有 Robot Control 固定代理都可以默认连固定小车；真正的安全边界由固定 endpoint 和确认项承担。
  const requested = queryString(value).trim();
  return requested || DEFAULT_ROBOT_API_BASE_URL;
}

export function robotControlFixedProxyQueryBaseUrl(value: unknown): string {
  // 没有 query 时保留默认小车地址；但显式 baseUrl= 空值必须 fail-closed，避免探路 POST 误触发真实上位机。
  if (typeof value === "string" && value.trim().length === 0) {
    return "";
  }
  return robotControlReadOnlyQueryBaseUrl(value);
}

type CameraMjpegRelayClient = {
  id: number;
  response: Response;
  headersStarted: boolean;
};

type CameraMjpegRelay = {
  key: string;
  normalizedBaseUrl: URL;
  clients: Set<CameraMjpegRelayClient>;
  controller: AbortController | null;
  contentType: string;
  upstreamActive: boolean;
  latestFrameChunk: Buffer | null;
  latestFrameUpdatedAtMs: number | null;
};

type CameraMjpegRelayLastFailure = {
  failure_reason: string;
  remote_http_status: number | null;
  failed_at_ms: number | null;
  last_error_payload?: Record<string, unknown> | null;
  last_first_frame_format_attempts_summary?: string;
  mjpeg_open_source_fallback_attempted?: boolean;
  open_source_fallback_failure_reason?: string;
  primary_source_failure_reason?: string;
  source_diagnosis_status?: string;
  source_diagnosis_plain_hint?: string;
  source_diagnosis_next_action?: string;
  source_diagnosis_not_exclusive?: string;
  source_readiness?: string;
  source_failure_reason?: string;
  selected_path?: string;
  selected_name?: string;
  selected_is_uvc_or_usb?: string;
  source_usage_status?: string;
  source_usage_owner_count?: string;
  source_usage_scope?: "free" | "camera_service_self" | "external_holder" | "unknown";
  source_usage_not_exclusive?: string;
  uvc_usb_topology_status?: string;
  uvc_usb_topology_plain_hint?: string;
  uvc_usb_topology_next_action?: string;
  uvc_usb_topology_video_usb_speed?: string;
  uvc_usb_topology_kernel_usb_address?: string;
  uvc_usb_topology_video_interface_count?: string;
};

function cameraSourceUsageScope(
  status: string | undefined,
  ownerCount: string | undefined,
): "free" | "camera_service_self" | "external_holder" | "unknown" {
  // 相机服务自己持有设备是共享预览的单上游模型，不是浏览器或其它进程独占。
  const normalizedStatus = shortText(status, "");
  const normalizedOwnerCount = shortText(ownerCount, "");
  if (normalizedStatus === "not_in_use" || normalizedOwnerCount === "0") {
    return "free";
  }
  if (normalizedStatus === "in_use_by_camera_service" || normalizedStatus === "camera_service_self") {
    return "camera_service_self";
  }
  if (normalizedStatus && normalizedStatus !== "not_loaded") {
    return "external_holder";
  }
  return "unknown";
}

function cameraSourceUsageNotExclusive(scope: "free" | "camera_service_self" | "external_holder" | "unknown"): string {
  // 输出字符串而不是布尔，是为了和既有 compactValueText 风格保持兼容。
  return scope === "free" || scope === "camera_service_self" ? "true" : "false";
}

function cameraMjpegFormatAttemptsSummary(payload: Record<string, unknown> | null | undefined): string {
  // health/status 里只放短摘要；raw 尝试矩阵仍留在上车端，避免普通页面被大 JSON 淹没。
  const attempts = Array.isArray(payload?.first_frame_format_attempts)
    ? payload.first_frame_format_attempts
    : Array.isArray(payload?.last_first_frame_format_attempts)
      ? payload.last_first_frame_format_attempts
      : [];
  const parts = attempts
    .map((item) => asRecord(item))
    .filter((item): item is Record<string, unknown> => item !== null)
    .map((attempt) => {
      const fourcc = shortText(attempt.label ?? attempt.fourcc, "unknown");
      const openSource = shortText(attempt.open_source, "");
      const openBackend = shortText(attempt.open_backend, "");
      const openMethod = openSource || openBackend
        ? `(${[openSource, openBackend].filter((item) => item && item !== "default").join("/") || "default"})`
        : "";
      const label = `${fourcc}${openMethod}`;
      const status = shortText(attempt.status, "unknown");
      if (status === "frame_read") return `${label} 已出帧`;
      if (status === "open_failed") return `${label} 打不开`;
      if (status === "first_frame_unreadable") return `${label} 无首帧`;
      return `${label} ${status}`;
    })
    .filter(Boolean)
    .slice(0, 6);
  return parts.length > 0 ? parts.join("；") : "none";
}

let nextCameraMjpegRelayClientId = 1;
const cameraMjpegRelays = new Map<string, CameraMjpegRelay>();
const cameraMjpegRelayLastFailures = new Map<string, CameraMjpegRelayLastFailure>();
const cameraFirstFrameProbeOverlays = new Map<string, RobotControlCameraFirstFrameProbeOverlay>();

function cameraMjpegUpstreamTimeoutMs(): number {
  // PC 等待窗口要略长于上位机 8787 的 8s relay 窗口，才能拿到真实 503/无帧 JSON，而不是抢先报 timeout。
  const parsed = Number(process.env.ROBER_CAMERA_MJPEG_UPSTREAM_TIMEOUT_MS ?? "12000");
  return Number.isFinite(parsed) && parsed >= 100 ? Math.min(parsed, 60000) : 12000;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // camera proxy 只接受/返回 JSON object；数组或字符串一律 fail-closed。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function shortText(value: unknown, fallback: string): string {
  // 响应只保留短摘要，避免把远端 traceback、路径或超长文本直接暴露给 UI。
  return typeof value === "string" && value.trim() ? value.trim().slice(0, 240) : fallback;
}

function cameraSourceDisplayName(value: unknown, fallback = "UVC 设备"): string {
  // 真实上位机偶发把 selected_name 序列化成 not_loaded；普通诊断不能把占位词当设备名展示。
  const text = shortText(value, "");
  return text && !["not_loaded", "none", "unknown", "null"].includes(text) ? text : fallback;
}

function cameraDiagnosisPlainHint(value: unknown, selectedName: string): string {
  // health/relay 的中文 hint 是给用户看的；这里仅清理占位设备名，不改写“不是独占/无首帧”的结论。
  const hint = shortText(value, "");
  if (!hint) {
    return "";
  }
  const deviceName = cameraSourceDisplayName(selectedName, "UVC 设备");
  return hint.replace(/：(not_loaded|none|unknown|null|摄像头|USB 摄像头)\s*当前没人占用/g, `：${cameraOwnerFreeText(deviceName)}`);
}

function cameraOwnerFreeText(selectedName: string): string {
  // 英文设备型号后接中文时保留一个空格；中文泛称直接连接，避免“摄像头 当前”这种断裂文案。
  return /[A-Za-z0-9]$/.test(selectedName) ? `${selectedName} 当前没人占用` : `${selectedName}当前没人占用`;
}

function normalizeAnswerSdp(value: string): string {
  // 浏览器对 SDP 行结束更严格；这里不改写语义，只统一成 CRLF 并补最后一个 CRLF。
  const crlfNormalized = value.replace(/\r?\n/g, "\r\n");
  return crlfNormalized.endsWith("\r\n") ? crlfNormalized : `${crlfNormalized}\r\n`;
}

function safeAnswer(value: unknown): RobotControlCameraAnswerSummary | null {
  // 前端必须拿到 answer.sdp/type 才能 setRemoteDescription；除此之外不透传更多媒体字段。
  const payload = asRecord(value);
  if (!payload) {
    return null;
  }
  const sdp = typeof payload.sdp === "string" ? payload.sdp : "";
  const type = payload.type === "answer" || payload.type === "pranswer" ? payload.type : null;
  if (!sdp.trim() || !type) {
    return null;
  }
  return { type, sdp: normalizeAnswerSdp(sdp) };
}

function safeAnswerFromPayload(payload: Record<string, unknown> | null): RobotControlCameraAnswerSummary | null {
  // 真实上位机当前返回顶层 answer SDP；本机 proxy 同时兼容嵌套 answer 和顶层 answer。
  return safeAnswer(payload?.answer) ?? safeAnswer(payload);
}

function peerIdText(value: unknown): string {
  // peer_id 只保留短字母数字摘要，避免路径注入或日志污染。
  return typeof value === "string" && /^[A-Za-z0-9_-]{1,120}$/.test(value) ? value : "";
}

function shortValue(value: unknown, fallback = "not_loaded"): string {
  // probe 摘要只展示短标量，避免 UI/契约承载整份远端 JSON。
  if (value === undefined || value === null) {
    return fallback;
  }
  if (typeof value === "string") {
    return value.trim() ? value.trim().slice(0, 180) : fallback;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value).slice(0, 180);
}

function shortStringList(value: unknown): string[] {
  // 远端可能用数组或逗号字符串表达缺口；PC 统一成短 token 数组，避免 UI 自己解析。
  if (Array.isArray(value)) {
    return value.map((item) => shortValue(item, "")).map((item) => item.trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    return value.split(",").map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function normalizeFreeRoamMappingMissingId(value: string): string {
  // 上车端直接说“未观测”，PC summary 使用 gate id；这里合并同义词，保证三处读回口径一致。
  const normalized: Record<string, string> = {
    camera_first_frame_not_observed: "camera_first_frame",
    camera_health_unreachable: "camera_first_frame",
    radar_scan_proof_not_fresh: "lidar_fresh",
    fresh_radar_scan_missing: "lidar_fresh",
  };
  return normalized[value] ?? value;
}

function booleanTrueValue(value: unknown): boolean {
  // 上位机 artifact 可能把布尔值序列化成字符串；PC gate 需要统一两种形状。
  return value === true || (typeof value === "string" && value.trim().toLowerCase() === "true");
}

function booleanFalseValue(value: unknown): boolean {
  // HIL false 是强否定证据，优先级高于 action success 或旧字段推导。
  return value === false || (typeof value === "string" && value.trim().toLowerCase() === "false");
}

function nav2GoalExecutionAllowedTrueField(field: string): boolean {
  // Nav2 固定执行 endpoint 允许返回“确实发车且 UART 有反馈”的证据，但仍不允许交付/主控开关变 true。
  return field === "sends_commands"
    || field.endsWith(".sends_commands")
    || field === "robot_control_executed"
    || field.endsWith(".robot_control_executed")
    || field === "sends_motion_commands"
    || field.endsWith(".sends_motion_commands")
    || field === "sends_base_motion_commands"
    || field.endsWith(".sends_base_motion_commands")
    || field === "uses_base_uart"
    || field.endsWith(".uses_base_uart")
    || field === "hil_pass"
    || field.endsWith(".hil_pass");
}

function firstLoadedValue(...values: unknown[]): unknown {
  // 外层 latest 响应常带 fail-closed 摘要，真实 action 证据优先取 latest_result。
  return values.find((value) => value !== undefined && value !== null);
}

function navGoalExecutionProvenValue(payload: Record<string, unknown> | null, latestResult: Record<string, unknown> | null): boolean {
  // 完整 Nav2 路线必须看到同窗口 wheel raw L/R 非零；IMU 姿态变化只能作为运动迹象展示。
  const baseFeedbackSummary = asRecord(latestResult?.base_feedback_summary) ?? asRecord(payload?.base_feedback_summary);
  const wheelFeedback = booleanTrueValue(baseFeedbackSummary?.wheel_feedback_lr_nonzero_proven);
  const sendsBaseMotionCommands = firstLoadedValue(latestResult?.sends_base_motion_commands, payload?.sends_base_motion_commands);
  const usesBaseUart = firstLoadedValue(latestResult?.uses_base_uart, payload?.uses_base_uart);
  if (
    (booleanTrueValue(latestResult?.nav2_goal_execution_proven) || booleanTrueValue(payload?.nav2_goal_execution_proven))
    && wheelFeedback
  ) {
    return true;
  }
  const status = shortValue(firstLoadedValue(latestResult?.status, payload?.status), "").toLowerCase();
  const resultStatus = shortValue(firstLoadedValue(latestResult?.result_status, payload?.result_status), "").toLowerCase();
  return status === "goal_succeeded"
    && booleanTrueValue(firstLoadedValue(latestResult?.goal_accepted, payload?.goal_accepted))
    && booleanTrueValue(firstLoadedValue(latestResult?.result_received, payload?.result_received))
    && resultStatus === "succeeded"
    && booleanTrueValue(firstLoadedValue(latestResult?.robot_control_executed, payload?.robot_control_executed))
    && !booleanFalseValue(sendsBaseMotionCommands)
    && !booleanFalseValue(usesBaseUart)
    && wheelFeedback;
}

function cameraProbeKeyValues(payload: Record<string, unknown> | null): RobotControlCameraFirstFrameProbeProxyResponse["probe_key_values"] {
  // 上位机把真实脚本输出放在 probe_payload；没有时按顶层兼容，便于旧 artifact 测试。
  const probePayload = asRecord(payload?.probe_payload) ?? payload;
  const metrics = asRecord(probePayload?.frame_metrics);
  const backendSmoke = asRecord(probePayload?.backend_smoke);
  const backendAttempts = Array.isArray(backendSmoke?.attempts) ? backendSmoke.attempts : [];
  const fallbackAttempts = Array.isArray(payload?.fallback_attempts) ? payload.fallback_attempts : [];
  const fallbackAttemptSummary = fallbackAttempts
    .map((item) => asRecord(item))
    .filter((item): item is Record<string, unknown> => item !== null)
    .slice(0, 12)
    .map((item) => {
      const fourcc = shortValue(item.fourcc, "default");
      const width = shortValue(item.width, "w");
      const height = shortValue(item.height, "h");
      const status = shortValue(item.status, "unknown");
      const reason = shortValue(item.failure_reason, "none");
      return `${fourcc}@${width}x${height}:${status}/${reason}`;
    })
    .join("; ");
  return {
    schema: shortValue(probePayload?.schema),
    device: shortValue(probePayload?.device),
    requested_fourcc: shortValue(probePayload?.requested_fourcc, "default"),
    open_ok: shortValue(probePayload?.open_ok),
    read_ok: shortValue(probePayload?.read_ok),
    first_frame_timeout: shortValue(probePayload?.first_frame_timeout),
    failure_reason: shortValue(probePayload?.failure_reason, "none"),
    visible_content_proven: shortValue(probePayload?.visible_content_proven),
    visible_content_candidate: shortValue(metrics?.visible_content_candidate),
    sample_path: shortValue(probePayload?.sample_path),
    sample_write_ok: shortValue(probePayload?.sample_write_ok),
    elapsed_ms: shortValue(probePayload?.elapsed_ms ?? payload?.elapsed_ms),
    mean_luma: shortValue(metrics?.mean_luma, "not_available"),
    max_luma: shortValue(metrics?.max_luma, "not_available"),
    dynamic_range_luma: shortValue(metrics?.dynamic_range_luma, "not_available"),
    non_black_ratio: shortValue(metrics?.non_black_ratio, "not_available"),
    backend_smoke_status: shortValue(backendSmoke?.status, "not_requested"),
    backend_frame_observed: shortValue(backendSmoke?.frame_observed, "false"),
    backend_attempts: shortValue(backendAttempts.length),
    streamon_io_error_observed: shortValue(backendSmoke?.streamon_io_error_observed, "false"),
    streamon_io_error_count: shortValue(backendSmoke?.streamon_io_error_count, "0"),
    latest_streamon_io_error: shortValue(backendSmoke?.latest_streamon_io_error, "none"),
    fallback_attempt_count: shortValue(fallbackAttempts.length),
    fallback_attempts_summary: fallbackAttemptSummary || "none",
    low_bandwidth_fallback_attempted: shortValue(payload?.low_bandwidth_fallback_attempted, "false"),
    low_bandwidth_fallback_min_size: shortValue(payload?.low_bandwidth_fallback_min_size, "none"),
  };
}

function cameraProbeDiagnosticAliases(
  probeValues: RobotControlCameraFirstFrameProbeProxyResponse["probe_key_values"],
  sourceFailure: CameraMjpegRelayLastFailure | null,
  dangerousTrueFields: string[] = [],
): Pick<
  RobotControlCameraFirstFrameProbeProxyResponse,
  | "camera_first_frame_ready"
  | "frame_observed"
  | "first_frame_observed"
  | "source_diagnosis_status"
  | "source_diagnosis_not_exclusive"
  | "source_diagnosis_plain_hint"
  | "source_diagnosis_next_action_plain"
  | "camera_usb_speed"
  | "camera_usb_full_speed_detected"
  | "camera_hardware_action_required"
  | "camera_hardware_action_label"
  | "camera_blocks_mapping_start"
  | "camera_blocks_free_move"
  | "camera_reprobe_after_hardware_action_required"
  | "camera_reprobe_sequence"
  | "fixed_camera_probe_endpoint"
  | "fixed_camera_mjpeg_status_endpoint"
  | "fixed_summary_endpoint"
  | "camera_recovery_sends_motion"
  | "camera_recovery_starts_map_runtime"
  | "sends_motion_when_clicked"
  | "starts_map_runtime"
  | "dangerous_true_fields"
> {
  // probe 失败体也要像 status/summary 一样给出同源诊断，避免现场把 502 误解成页面独占或控制动作。
  const frameObserved = probeValues.read_ok === "true"
    || probeValues.backend_frame_observed === "true"
    || probeValues.visible_content_proven === "true";
  const firstFrameReady = probeValues.visible_content_proven === "true";
  const cameraUsbSpeed = sourceFailure?.uvc_usb_topology_video_usb_speed ?? "not_loaded";
  const cameraUsbFullSpeedDetected = cameraUsbSpeed === "12M"
    || sourceFailure?.source_diagnosis_status === "uvc_full_speed_usb_not_exclusive"
    || sourceFailure?.uvc_usb_topology_status === "uvc_video_on_full_speed_usb";
  const cameraTransportHardwareActionRequired = sourceFailure?.source_diagnosis_status === "uvc_transport_error_not_exclusive";
  const cameraNoFrameHardwareActionRequired = sourceFailure?.source_diagnosis_status === "uvc_no_frame_not_exclusive"
    && sourceFailure?.source_diagnosis_not_exclusive === "true";
  const sourceDiagnosisNextActionPlain = cameraMjpegActionPlainText(sourceFailure?.source_diagnosis_next_action ?? "not_loaded")
    || (cameraUsbFullSpeedDetected
      ? "摄像头当前挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub 后复测首帧。"
      : "打开共享预览或点只读检查复测首帧。");
  const cameraHardwareActionRequired = (
    cameraUsbFullSpeedDetected
    || cameraTransportHardwareActionRequired
    || cameraNoFrameHardwareActionRequired
  ) && !firstFrameReady;
  const cameraHardwareActionLabel = cameraHardwareActionRequired
    ? cameraUsbFullSpeedDetected
      ? "换高速USB后复测"
      : cameraTransportHardwareActionRequired
        ? "检查USB/供电后复测"
        : "检查摄像头输入/供电后复测"
    : "复测相机首帧";
  const cameraReprobeSequence = [
    "/api/robot-control/camera/first-frame/probe",
    "/api/robot-control/camera/mjpeg/status",
    "/api/robot-control/summary",
  ];
  return {
    camera_first_frame_ready: firstFrameReady,
    frame_observed: frameObserved,
    first_frame_observed: frameObserved,
    source_diagnosis_status: sourceFailure?.source_diagnosis_status ?? "not_loaded",
    source_diagnosis_not_exclusive: sourceFailure?.source_diagnosis_not_exclusive ?? "not_loaded",
    source_diagnosis_plain_hint: sourceFailure?.source_diagnosis_plain_hint ?? "not_loaded",
    source_diagnosis_next_action_plain: sourceDiagnosisNextActionPlain,
    camera_usb_speed: cameraUsbSpeed,
    camera_usb_full_speed_detected: cameraUsbFullSpeedDetected,
    camera_hardware_action_required: cameraHardwareActionRequired,
    camera_hardware_action_label: cameraHardwareActionLabel,
    camera_blocks_mapping_start: !firstFrameReady,
    camera_blocks_free_move: false,
    camera_reprobe_after_hardware_action_required: cameraHardwareActionRequired,
    camera_reprobe_sequence: cameraReprobeSequence,
    fixed_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe",
    fixed_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status",
    fixed_summary_endpoint: "/api/robot-control/summary",
    camera_recovery_sends_motion: false,
    camera_recovery_starts_map_runtime: false,
    sends_motion_when_clicked: false,
    starts_map_runtime: false,
    dangerous_true_fields: dangerousTrueFields,
  };
}

function baseFeedbackSampleKeyValues(payload: Record<string, unknown> | null): RobotControlBaseFeedbackSamplesProxyResponse["sample_key_values"] {
  // 反馈采集只展示样本摘要；原始串口帧留在上位机 artifact，避免 PC 页面误读为 HIL pass。
  const latestResult = asRecord(payload?.latest_result);
  const sampleRoot = latestResult ?? payload;
  const feedbackAck = asRecord(sampleRoot?.feedback_ack) ?? asRecord(payload?.feedback_ack);
  const wheelSummary = asRecord(sampleRoot?.wheel_feedback_summary) ?? asRecord(payload?.wheel_feedback_summary);
  const latestPair = asRecord(wheelSummary?.latest_pair);
  return {
    schema: shortText(sampleRoot?.schema ?? payload?.schema, "not_loaded"),
    requested_sample_count: shortValue(sampleRoot?.requested_sample_count),
    completed_sample_count: shortValue(sampleRoot?.completed_sample_count),
    t1001_observed_count: shortValue(sampleRoot?.t1001_observed_count),
    all_samples_observed_t1001: shortValue(sampleRoot?.all_samples_observed_t1001),
    partial_samples_observed_t1001: shortValue(sampleRoot?.partial_samples_observed_t1001),
    wheel_feedback_lr_nonzero_proven: shortValue(sampleRoot?.wheel_feedback_lr_nonzero_proven ?? payload?.wheel_feedback_lr_nonzero_proven),
    wheel_feedback_nonzero_observed: shortValue(sampleRoot?.wheel_feedback_nonzero_observed ?? payload?.wheel_feedback_nonzero_observed),
    wheel_feedback_nonzero_frame_count: shortValue(wheelSummary?.nonzero_frame_count),
    wheel_feedback_latest_left_speed: shortValue(latestPair?.left_speed, "not_observed"),
    wheel_feedback_latest_right_speed: shortValue(latestPair?.right_speed, "not_observed"),
    wheel_feedback_source: shortValue(wheelSummary?.source, "not_observed"),
    imu_attitude_delta_observed: shortValue(sampleRoot?.imu_attitude_delta_observed ?? payload?.imu_attitude_delta_observed, "not_loaded"),
    motion_signal_observed: shortValue(sampleRoot?.motion_signal_observed ?? payload?.motion_signal_observed, "not_loaded"),
    motion_signal_source: shortValue(sampleRoot?.motion_signal_source ?? payload?.motion_signal_source, "not_observed"),
    feedback_ack_t1001_observed: shortValue(feedbackAck?.t1001_observed),
    observed_feedback_types: shortValue(sampleRoot?.observed_feedback_types),
    sends_motion_commands: shortValue(sampleRoot?.sends_motion_commands ?? payload?.sends_motion_commands),
    robot_control_executed: shortValue(sampleRoot?.robot_control_executed ?? payload?.robot_control_executed),
  };
}

function baseFeedbackSampleAliases(
  sampleKeyValues: RobotControlBaseFeedbackSamplesProxyResponse["sample_key_values"],
): Pick<
  RobotControlBaseFeedbackSamplesProxyResponse,
  | "wheel_raw_left"
  | "wheel_raw_right"
  | "latest_raw_left"
  | "latest_raw_right"
  | "base_feedback_lr_nonzero_proven"
  | "wheel_feedback_lr_nonzero_proven"
  | "wheel_feedback_source"
  | "wheel_feedback_plain_hint"
  | "wheel_feedback_next_action"
  | "imu_attitude_delta_observed"
  | "motion_signal_observed"
  | "motion_signal_source"
  | "motion_signal_plain_hint"
  | "motion_signal_next_action"
> {
  // 顶层 wheel/motion alias 与 sample_key_values 同源，方便现场一眼确认 L/R 和 IMU 动作信号。
  const left = sampleKeyValues.wheel_feedback_latest_left_speed || "not_observed";
  const right = sampleKeyValues.wheel_feedback_latest_right_speed || "not_observed";
  const proven = sampleKeyValues.wheel_feedback_lr_nonzero_proven || "not_loaded";
  const frameCount = sampleKeyValues.t1001_observed_count || "0";
  const nonzeroFrames = sampleKeyValues.wheel_feedback_nonzero_frame_count || "0";
  const source = sampleKeyValues.wheel_feedback_source || "not_observed";
  const imuObserved = sampleKeyValues.imu_attitude_delta_observed || "not_loaded";
  const motionObserved = sampleKeyValues.motion_signal_observed || "not_loaded";
  const motionSource = sampleKeyValues.motion_signal_source || "not_observed";
  const motionAliases = {
    imu_attitude_delta_observed: imuObserved,
    motion_signal_observed: motionObserved,
    motion_signal_source: motionSource,
    motion_signal_plain_hint: motionObserved === "true"
      ? `只读反馈采样读到运动信号：${motionSource}；这可作为 WASD/低速试动动作迹象，但不替代 wheel raw L/R 非零证据。`
      : "只读反馈采样未读到 IMU/轮速动作信号；按住 WASD 或方向键后再复验。",
    motion_signal_next_action: motionObserved === "true"
      ? "继续用同窗口 wheel raw L/R 或 Nav2/delivery 材料收口完整验收。"
      : "直接低速试动或按住键盘方向键，再复验动作信号和 wheel raw L/R。",
  };
  const pairText = `wheel raw L/R=${left}/${right}`;
  if (proven === "true") {
    return {
      wheel_raw_left: left,
      wheel_raw_right: right,
      latest_raw_left: left,
      latest_raw_right: right,
      base_feedback_lr_nonzero_proven: proven,
      wheel_feedback_lr_nonzero_proven: proven,
      wheel_feedback_source: source,
      wheel_feedback_plain_hint: `只读反馈采样读到 ${pairText}，非零帧 ${nonzeroFrames}/${frameCount}；这不是运动命令，也不能单独替代试动或 Nav2 执行窗口材料。`,
      wheel_feedback_next_action: "继续用对应的试动、键盘或 Nav2 执行窗口材料收口 wheel raw L/R 非零。",
      ...motionAliases,
    };
  }
  if (left !== "not_observed" || right !== "not_observed" || frameCount !== "0") {
    return {
      wheel_raw_left: left,
      wheel_raw_right: right,
      latest_raw_left: left,
      latest_raw_right: right,
      base_feedback_lr_nonzero_proven: proven,
      wheel_feedback_lr_nonzero_proven: proven,
      wheel_feedback_source: source,
      wheel_feedback_plain_hint: `只读反馈采样读到 ${pairText}，非零未证明，T1001 帧 ${frameCount}；这不是运动命令。`,
      wheel_feedback_next_action: "直接低速试动或按住键盘方向键，再复验 wheel raw L/R 非零。",
      ...motionAliases,
    };
  }
  return {
    wheel_raw_left: left,
    wheel_raw_right: right,
    latest_raw_left: left,
    latest_raw_right: right,
    base_feedback_lr_nonzero_proven: proven,
    wheel_feedback_lr_nonzero_proven: proven,
    wheel_feedback_source: source,
    wheel_feedback_plain_hint: "只读反馈采样没有读到可用 wheel raw L/R；这不是运动命令。",
    wheel_feedback_next_action: "先确认上位机底盘反馈链路，再直接做低速试动。",
    ...motionAliases,
  };
}

function baseManualMotionKeyValues(payload: Record<string, unknown> | null): Record<string, string> {
  // 上位机 manual 响应里的 during-motion 反馈是最贴近真实点动窗口的 wheel material。
  const wheelSummary = asRecord(payload?.manual_wheel_feedback_summary);
  // IMU 只证明车身姿态在动，不能替代 WAVE ROVER T1001 的 wheel raw L/R 非零证据。
  const imuSummary = asRecord(payload?.manual_imu_attitude_delta_summary);
  const latestPair = asRecord(wheelSummary?.latest_nonzero_pair) ?? asRecord(wheelSummary?.latest_pair);
  const transaction = asRecord(payload?.serial_motion_transaction);
  const duringFeedback = asRecord(payload?.feedback_during_motion) ?? asRecord(transaction?.feedback_during_motion);
  const afterStopFeedback = asRecord(payload?.feedback_evidence) ?? asRecord(transaction?.feedback_after_stop);
  const manualFeedbackLatest = asRecord(payload?.manual_feedback_samples_latest);
  const commandResult = asRecord(payload?.command_result);
  const stopResult = asRecord(payload?.stop_result);
  const duringFrames = Array.isArray(duringFeedback?.t1001_feedback_frames) ? duringFeedback.t1001_feedback_frames : [];
  const afterStopFrames = Array.isArray(afterStopFeedback?.t1001_feedback_frames) ? afterStopFeedback.t1001_feedback_frames : [];
  const latestArtifactFrames = Array.isArray(manualFeedbackLatest?.t1001_feedback_frames) ? manualFeedbackLatest.t1001_feedback_frames : [];
  const latestDuringFrame = asRecord(duringFrames[duringFrames.length - 1]) ?? asRecord(latestArtifactFrames[latestArtifactFrames.length - 1]);
  return {
    base_command_mode: shortValue(payload?.base_command_mode, "not_loaded"),
    feedback_mode: shortValue(payload?.feedback_mode, "not_loaded"),
    command_result_ok: shortValue(commandResult?.ok, "false"),
    stop_result_ok: shortValue(stopResult?.ok, "false"),
    wheel_feedback_lr_nonzero_proven: shortValue(payload?.wheel_feedback_lr_nonzero_proven, "false"),
    wheel_feedback_nonzero_observed: shortValue(payload?.wheel_feedback_nonzero_observed, "false"),
    wheel_feedback_nonzero_frame_count: shortValue(wheelSummary?.nonzero_frame_count, "0"),
    wheel_feedback_latest_left_speed: shortValue(latestPair?.left_speed, "not_loaded"),
    wheel_feedback_latest_right_speed: shortValue(latestPair?.right_speed, "not_loaded"),
    wheel_feedback_latest_raw_left: shortValue(latestDuringFrame?.L, "not_loaded"),
    wheel_feedback_latest_raw_right: shortValue(latestDuringFrame?.R, "not_loaded"),
    imu_attitude_delta_observed: shortValue(payload?.imu_attitude_delta_observed ?? imuSummary?.imu_attitude_delta_observed, "false"),
    manual_imu_attitude_delta_observed: shortValue(imuSummary?.imu_attitude_delta_observed ?? payload?.imu_attitude_delta_observed, "false"),
    imu_roll_delta: shortValue(imuSummary?.max_abs_roll_delta, "not_loaded"),
    imu_pitch_delta: shortValue(imuSummary?.max_abs_pitch_delta, "not_loaded"),
    manual_imu_roll_delta: shortValue(imuSummary?.max_abs_roll_delta, "not_loaded"),
    manual_imu_pitch_delta: shortValue(imuSummary?.max_abs_pitch_delta, "not_loaded"),
    motion_signal_observed: shortValue(payload?.motion_signal_observed, "false"),
    motion_signal_source: shortValue(payload?.motion_signal_source, "not_loaded"),
    feedback_during_motion_t1001_frame_count: String(duringFrames.length),
    feedback_after_stop_t1001_frame_count: String(afterStopFrames.length),
    feedback_during_motion_status: shortValue(duringFeedback?.t1001_feedback_status, "not_loaded"),
    feedback_during_motion_source: shortValue(duringFeedback?.feedback_source, "not_loaded"),
    feedback_during_motion_attempted: shortValue(payload?.feedback_during_motion_attempted, "false"),
    feedback_after_stop_attempted: shortValue(payload?.feedback_after_stop_attempted, "false"),
    manual_command_executed: shortValue(payload?.manual_command_executed, "false"),
    auto_stop_executed: shortValue(payload?.auto_stop_executed, "false"),
  };
}

function baseManualMotionTopLevelAliases(keyValues: Record<string, string>): Record<string, string> {
  // WASD/点动回包要让现场脚本一眼看到“这次按键窗口”的命令和反馈事实；嵌套对象仍保留完整材料。
  const aliasKeys = [
    "base_command_mode",
    "feedback_mode",
    "command_result_ok",
    "stop_result_ok",
    "wheel_feedback_lr_nonzero_proven",
    "wheel_feedback_nonzero_observed",
    "wheel_feedback_latest_raw_left",
    "wheel_feedback_latest_raw_right",
    "imu_attitude_delta_observed",
    "manual_imu_attitude_delta_observed",
    "imu_roll_delta",
    "imu_pitch_delta",
    "motion_signal_observed",
    "motion_signal_source",
    "feedback_during_motion_t1001_frame_count",
    "feedback_after_stop_t1001_frame_count",
    "manual_command_executed",
    "auto_stop_executed",
  ];
  const aliases: Record<string, string> = {};
  for (const key of aliasKeys) {
    aliases[key] = keyValues[key] ?? "not_loaded";
  }
  return aliases;
}

function navGoalExecutionKeyValues(payload: Record<string, unknown> | null): Record<string, string> {
  // 上位机执行响应里 latest_result 是真正的 action artifact；PC 只展示短摘要。
  const latestResult = asRecord(payload?.latest_result);
  const goalRequest = asRecord(latestResult?.goal_request) ?? asRecord(payload?.goal_request);
  const routePreview = asRecord(goalRequest?.route_preview) ?? asRecord(latestResult?.route_preview) ?? asRecord(payload?.route_preview);
  const cancelResponse = asRecord(latestResult?.cancel_response);
  const baseFeedbackSummary = asRecord(latestResult?.base_feedback_summary) ?? asRecord(payload?.base_feedback_summary);
  const baseCommandSummary = asRecord(latestResult?.base_command_summary) ?? asRecord(payload?.base_command_summary);
  const managedRuntime = asRecord(latestResult?.managed_runtime) ?? asRecord(payload?.managed_runtime);
  const managedRuntimeCleanup = asRecord(managedRuntime?.cleanup);
  const managedRuntimeLifecycleReady = asRecord(managedRuntime?.lifecycle_ready);
  const latestNonzeroPair = asRecord(baseFeedbackSummary?.latest_nonzero_pair);
  const latestPair = asRecord(baseFeedbackSummary?.latest_pair);
  const latestNonzeroCommand = asRecord(baseCommandSummary?.latest_nonzero_command);
  const baseCommandMode = shortValue(latestResult?.base_command_mode ?? payload?.base_command_mode, "not_loaded");
  const baseCommandNonzeroCount = shortValue(baseCommandSummary?.nonzero_command_count, "0");
  const baseCommandLatestNonzeroMode = shortValue(
    baseCommandSummary?.latest_nonzero_command_mode ?? latestNonzeroCommand?.command_mode,
    "not_loaded",
  );
  const latestFeedbackLeft = shortValue(latestNonzeroPair?.left_speed ?? latestPair?.left_speed, "not_observed");
  const latestFeedbackRight = shortValue(latestNonzeroPair?.right_speed ?? latestPair?.right_speed, "not_observed");
  const latestFeedbackRawLeft = shortValue(
    latestNonzeroPair?.raw_left ?? latestNonzeroPair?.left_raw ?? latestNonzeroPair?.L ?? latestNonzeroPair?.left_speed
      ?? latestPair?.raw_left ?? latestPair?.left_raw ?? latestPair?.L ?? latestPair?.left_speed,
    "not_observed",
  );
  const latestFeedbackRawRight = shortValue(
    latestNonzeroPair?.raw_right ?? latestNonzeroPair?.right_raw ?? latestNonzeroPair?.R ?? latestNonzeroPair?.right_speed
      ?? latestPair?.raw_right ?? latestPair?.right_raw ?? latestPair?.R ?? latestPair?.right_speed,
    "not_observed",
  );
  const executionStatus = shortValue(latestResult?.status ?? payload?.status);
  const executionResultStatus = shortValue(payload?.result_status ?? latestResult?.result_status);
  const executionSucceeded = executionStatus === "goal_succeeded" || executionResultStatus === "succeeded";
  const executionProven = navGoalExecutionProvenValue(payload, latestResult);
  const wheelProof = shortValue(baseFeedbackSummary?.wheel_feedback_lr_nonzero_proven, "false");
  const executionProofGap = executionSucceeded && !executionProven
    ? wheelProof === "true" ? "execution_proof_not_proven" : "wheel_lr_nonzero_not_proven"
    : "none";
  const baseCommandModeCounts = (() => {
    // 真实上车 latest 可能只给 latest_nonzero_command.command_mode；PC 仍要把非零命令模式读成可见证据。
    const explicitCounts = baseCommandSummary?.command_mode_counts;
    if (explicitCounts !== undefined && explicitCounts !== null) {
      return shortValue(explicitCounts, "{}");
    }
    const count = Number(baseCommandNonzeroCount);
    const mode = baseCommandLatestNonzeroMode !== "not_loaded" ? baseCommandLatestNonzeroMode : baseCommandMode;
    if (["ros", "pwm", "speed"].includes(mode) && Number.isFinite(count) && count > 0) {
      return JSON.stringify({ [mode]: count });
    }
    return "{}";
  })();
  return {
    status: executionStatus,
    evidence_ref: shortValue(payload?.evidence_ref ?? latestResult?.evidence_ref),
    generated_at_ms: shortValue(latestResult?.generated_at_ms ?? payload?.generated_at_ms),
    response_generated_at_ms: shortValue(payload?.generated_at_ms),
    completed_at_ms: shortValue(latestResult?.completed_at_ms ?? payload?.completed_at_ms),
    nav2_goal_execution_proven: String(executionProven),
    execution_proof_gap: executionProofGap,
    hil_pass: shortValue(latestResult?.hil_pass ?? payload?.hil_pass),
    goal_accepted: shortValue(payload?.goal_accepted ?? latestResult?.goal_accepted),
    result_received: shortValue(payload?.result_received ?? latestResult?.result_received),
    result_status: executionResultStatus,
    goal_frame_id: shortValue(goalRequest?.frame_id ?? goalRequest?.goal_frame_id, "map"),
    goal_x: shortValue(goalRequest?.x ?? goalRequest?.goal_x),
    goal_y: shortValue(goalRequest?.y ?? goalRequest?.goal_y),
    goal_yaw: shortValue(goalRequest?.yaw ?? goalRequest?.goal_yaw),
    route_preview_point_count: shortValue(routePreview?.point_count ?? goalRequest?.route_preview_point_count, "0"),
    route_preview_source_point_count: shortValue(routePreview?.source_point_count ?? goalRequest?.route_preview_source_point_count, "0"),
    route_preview_frame_id: shortValue(routePreview?.frame_id ?? goalRequest?.route_preview_frame_id, "not_loaded"),
    route_start_x: shortValue(routePreview?.start_x ?? goalRequest?.route_start_x, "not_loaded"),
    route_start_y: shortValue(routePreview?.start_y ?? goalRequest?.route_start_y, "not_loaded"),
    route_goal_x: shortValue(routePreview?.goal_x ?? goalRequest?.route_goal_x, "not_loaded"),
    route_goal_y: shortValue(routePreview?.goal_y ?? goalRequest?.route_goal_y, "not_loaded"),
    result_timeout_s: shortValue(goalRequest?.result_timeout_s),
    cancel_requested: shortValue(payload?.cancel_requested ?? latestResult?.cancel_requested),
    cancel_accepted: shortValue(cancelResponse?.accepted, "false"),
    feedback_sample_count: shortValue(payload?.feedback_sample_count ?? latestResult?.feedback_sample_count, "0"),
    base_command_mode: baseCommandMode,
    base_feedback_sample_count: shortValue(baseFeedbackSummary?.sample_count, "0"),
    base_feedback_nonzero_sample_count: shortValue(baseFeedbackSummary?.nonzero_sample_count, "0"),
    base_feedback_lr_nonzero_proven: shortValue(baseFeedbackSummary?.wheel_feedback_lr_nonzero_proven, "false"),
    base_feedback_imu_attitude_delta_observed: shortValue(baseFeedbackSummary?.imu_attitude_delta_observed, "false"),
    base_feedback_imu_roll_delta: shortValue(asRecord(baseFeedbackSummary?.imu_attitude_delta_summary)?.max_abs_roll_delta, "0"),
    base_feedback_imu_pitch_delta: shortValue(asRecord(baseFeedbackSummary?.imu_attitude_delta_summary)?.max_abs_pitch_delta, "0"),
    base_feedback_latest_left_speed: latestFeedbackLeft,
    base_feedback_latest_right_speed: latestFeedbackRight,
    base_feedback_latest_raw_left: latestFeedbackRawLeft,
    base_feedback_latest_raw_right: latestFeedbackRawRight,
    base_command_sample_count: shortValue(baseCommandSummary?.sample_count, "0"),
    base_command_nonzero_count: baseCommandNonzeroCount,
    base_command_nonzero_observed: shortValue(baseCommandSummary?.nonzero_command_observed, "false"),
    base_command_latest_nonzero_mode: baseCommandLatestNonzeroMode,
    base_command_mode_counts: baseCommandModeCounts,
    readback_publishes_cmd_vel: shortValue(payload?.readback_publishes_cmd_vel ?? latestResult?.publishes_cmd_vel, "not_loaded"),
    managed_runtime_requested: shortValue(managedRuntime?.requested, "not_loaded"),
    managed_runtime_started: shortValue(managedRuntime?.started, "not_loaded"),
    managed_runtime_lifecycle_ready_ok: shortValue(managedRuntimeLifecycleReady?.ok, "not_loaded"),
    managed_runtime_cleanup_ok: shortValue(managedRuntimeCleanup?.ok, "not_loaded"),
    robot_control_executed: shortValue(latestResult?.robot_control_executed ?? payload?.robot_control_executed, "false"),
    sends_base_motion_commands: shortValue(latestResult?.sends_base_motion_commands ?? payload?.sends_base_motion_commands, "not_loaded"),
    uses_base_uart: shortValue(latestResult?.uses_base_uart ?? payload?.uses_base_uart, "not_loaded"),
    delivery_success: shortValue(payload?.delivery_success ?? latestResult?.delivery_success, "false"),
  };
}

function navGoalLatestNextMode(keyValues: Record<string, string>): string {
  // action 成功但 wheel L/R 未非零时，下一轮切换控制面做 A/B 复验，避免一直重复同一条无效链路。
  if (
    (keyValues.status === "goal_succeeded" || keyValues.result_status === "succeeded")
    && keyValues.base_feedback_lr_nonzero_proven === "false"
    && keyValues.base_command_mode === "pwm"
  ) {
    return "ros";
  }
  if (
    (keyValues.status === "goal_succeeded" || keyValues.result_status === "succeeded")
    && keyValues.base_feedback_lr_nonzero_proven === "false"
    && keyValues.base_command_mode === "ros"
  ) {
    return "speed";
  }
  return keyValues.base_command_mode && keyValues.base_command_mode !== "not_loaded"
    ? keyValues.base_command_mode
    : "ros";
}

function navGoalExecutionModePlainFields(keyValues: Record<string, string>): Pick<
  RobotControlNavGoalExecutionLatestResponse,
  "goal_execution_next_mode_plain" | "goal_execution_mode_rerun_plain"
> {
  // 外部脚本常只读 latest；这里把“下次用什么控制链”和“为什么要换”做成稳定白话字段。
  const lastMode = keyValues.base_command_mode && keyValues.base_command_mode !== "not_loaded"
    ? keyValues.base_command_mode
    : "not_loaded";
  const nextMode = navGoalLatestNextMode(keyValues);
  const wheelZero = (keyValues.status === "goal_succeeded" || keyValues.result_status === "succeeded")
    && keyValues.base_feedback_lr_nonzero_proven === "false";
  if (!nextMode || nextMode === "not_loaded") {
    return {
      goal_execution_next_mode_plain: "下次执行模式未读到；默认由执行接口按固定策略选择。",
      goal_execution_mode_rerun_plain: "还没有可用的路线执行模式复验结论。",
    };
  }
  if (wheelZero && lastMode !== "not_loaded" && lastMode !== nextMode) {
    return {
      goal_execution_next_mode_plain: `下次将用 ${nextMode.toUpperCase()} 模式重跑图上路线。`,
      goal_execution_mode_rerun_plain: `上次 ${lastMode.toUpperCase()} 模式路线返回成功但轮速 L/R 仍未非零，本次切到 ${nextMode.toUpperCase()} 模式复验控制链。`,
    };
  }
  if (wheelZero) {
    return {
      goal_execution_next_mode_plain: `下次继续用 ${nextMode.toUpperCase()} 模式重跑图上路线。`,
      goal_execution_mode_rerun_plain: "上次路线返回成功但轮速 L/R 仍未非零，本次重点复验同窗口轮速反馈。",
    };
  }
  return {
    goal_execution_next_mode_plain: `下次执行会使用 ${nextMode.toUpperCase()} 模式。`,
    goal_execution_mode_rerun_plain: "当前没有控制模式切换复验要求。",
  };
}

async function resolveNavGoalExecutionDefaultBaseCommandMode(base: URL): Promise<"ros" | "speed" | "pwm"> {
  // 外部脚本可能不传 base_command_mode；发车前只读 latest，沿用 summary 同一套“下次模式”策略。
  try {
    const latest = await fetch(endpointUrl(base, "/api/nav2/goal/execution/latest"), {
      method: "GET",
      signal: AbortSignal.timeout(3000),
    });
    if (!latest.ok) {
      return "ros";
    }
    const payload = asRecord(await latest.json().catch(() => null));
    const nextMode = navGoalLatestNextMode(navGoalExecutionKeyValues(payload));
    return ["ros", "speed", "pwm"].includes(nextMode) ? nextMode as "ros" | "speed" | "pwm" : "ros";
  } catch {
    return "ros";
  }
}

function navGoalLatestPlainFields(
  keyValues: Record<string, string>,
): Pick<
  RobotControlNavGoalExecutionLatestResponse,
  | "route_execution_readiness_plain"
  | "route_execution_precheck_plain"
  | "goal_execution_wheel_raw_lr_status_plain"
  | "goal_execution_wheel_raw_lr_next_action_plain"
  | "base_command_mode"
  | "goal_execution_base_command_mode"
  | "next_execution_base_command_mode"
  | "goal_execution_base_command_nonzero_observed"
  | "goal_execution_base_command_nonzero_count"
  | "goal_execution_base_command_mode_counts"
  | "goal_execution_base_feedback_lr_nonzero_proven"
  | "goal_execution_base_feedback_imu_attitude_delta_observed"
  | "goal_execution_readback_publishes_cmd_vel"
  | "goal_execution_managed_runtime_requested"
  | "goal_execution_managed_runtime_started"
  | "goal_execution_managed_runtime_lifecycle_ready_ok"
  | "goal_execution_managed_runtime_cleanup_ok"
  | "execution_status_plain"
  | "next_action_plain"
  | "goal_execution_base_feedback_latest_raw_left"
  | "goal_execution_base_feedback_latest_raw_right"
> {
  // latest 是只读 artifact；这些字段只解释最近路线证据和下一步，不会重放 Nav2。
  const goalSucceeded = keyValues.status === "goal_succeeded" || keyValues.result_status === "succeeded";
  const wheelProven = keyValues.base_feedback_lr_nonzero_proven === "true";
  const wheelExplicitFalse = keyValues.base_feedback_lr_nonzero_proven === "false";
  const executionProven = keyValues.nav2_goal_execution_proven === "true";
  const left = keyValues.base_feedback_latest_raw_left || keyValues.base_feedback_latest_left_speed || "not_loaded";
  const right = keyValues.base_feedback_latest_raw_right || keyValues.base_feedback_latest_right_speed || "not_loaded";
  const nextMode = navGoalLatestNextMode(keyValues).toUpperCase();
  const commandCount = Number(keyValues.base_command_nonzero_count ?? "0");
  const commandText = keyValues.base_command_nonzero_observed === "true" || (Number.isFinite(commandCount) && commandCount > 0)
    ? `已看到 ${Number.isFinite(commandCount) ? commandCount : 0} 次非零底盘命令`
    : "未看到非零底盘命令";
  const imuText = keyValues.base_feedback_imu_attitude_delta_observed === "true" ? "，IMU 姿态有变化" : "";
  const motionMaterial = keyValues.base_feedback_imu_attitude_delta_observed === "true"
    ? "已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或控制服务。"
    : keyValues.base_command_nonzero_observed === "true" || (Number.isFinite(commandCount) && commandCount > 0)
      ? "已看到非零底盘命令，下一步重点复验执行窗口轮速 L/R。"
      : "还没有读到足够的底盘运动材料。";
  const baseFeedbackAliases = {
    base_command_mode: keyValues.base_command_mode || "not_loaded",
    goal_execution_base_command_mode: keyValues.base_command_mode || "not_loaded",
    next_execution_base_command_mode: navGoalLatestNextMode(keyValues),
    goal_execution_base_command_nonzero_observed: keyValues.base_command_nonzero_observed || "not_loaded",
    goal_execution_base_command_nonzero_count: keyValues.base_command_nonzero_count || "0",
    goal_execution_base_command_mode_counts: keyValues.base_command_mode_counts || "{}",
    goal_execution_base_feedback_lr_nonzero_proven: keyValues.base_feedback_lr_nonzero_proven || "not_loaded",
    goal_execution_base_feedback_imu_attitude_delta_observed: keyValues.base_feedback_imu_attitude_delta_observed || "not_loaded",
    goal_execution_readback_publishes_cmd_vel: keyValues.readback_publishes_cmd_vel || "not_loaded",
    goal_execution_managed_runtime_requested: keyValues.managed_runtime_requested || "not_loaded",
    goal_execution_managed_runtime_started: keyValues.managed_runtime_started || "not_loaded",
    goal_execution_managed_runtime_lifecycle_ready_ok: keyValues.managed_runtime_lifecycle_ready_ok || "not_loaded",
    goal_execution_managed_runtime_cleanup_ok: keyValues.managed_runtime_cleanup_ok || "not_loaded",
    goal_execution_base_feedback_latest_raw_left: left,
    goal_execution_base_feedback_latest_raw_right: right,
  };
  const modePlain = navGoalExecutionModePlainFields(keyValues);
  if (executionProven || wheelProven) {
    return {
      execution_status_plain: "本轮路线执行和执行窗口轮速 L/R 已证明。",
      next_action_plain: "继续送达确认；送达确认不会发车。",
      route_execution_readiness_plain: "完整路线执行已证明；同窗口轮速 L/R 已非零。",
      route_execution_precheck_plain: "下一步是送达确认；送达确认不会发车。",
      goal_execution_wheel_raw_lr_status_plain: `执行窗口轮速 L/R 已非零：L=${left}，R=${right}。`,
      goal_execution_wheel_raw_lr_next_action_plain: "继续送达确认；送达确认不会发车。",
      ...modePlain,
      ...baseFeedbackAliases,
    };
  }
  if (goalSucceeded && wheelExplicitFalse) {
    return {
      execution_status_plain: `上次路线结果成功，但执行窗口轮速 L/R=${left}/${right} 未非零；${motionMaterial}`,
      next_action_plain: `直接用 ${nextMode} 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。`,
      route_execution_readiness_plain: `图上路线可重跑复验；上次路线结果成功，但同窗口轮速 L/R=${left}/${right} 未非零。`,
      route_execution_precheck_plain: `现场默认安全；相机、雷达和现场报告不作为额外发车前置；执行会用 ${nextMode} 模式跑图上路线。`,
      goal_execution_wheel_raw_lr_status_plain: `上次路线结果成功，但执行窗口轮速 L/R=${left}/${right} 未非零；${commandText}${imuText}。`,
      goal_execution_wheel_raw_lr_next_action_plain: `直接用 ${nextMode} 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。`,
      ...modePlain,
      ...baseFeedbackAliases,
    };
  }
  return {
    execution_status_plain: "图上路线还未准备完成。",
    next_action_plain: "先准备图上路线并刷新地图画面，然后直接执行。",
    route_execution_readiness_plain: "图上路线还不可执行；当前缺口：图上路线还未准备完成。",
    route_execution_precheck_plain: "路线准备完成后可直接执行；现场默认安全，不要求额外勾选。",
    goal_execution_wheel_raw_lr_status_plain: "本轮完整路线执行的轮速 L/R 还未证明。",
    goal_execution_wheel_raw_lr_next_action_plain: "先准备图上路线并执行，再在同窗口确认轮速 L/R 非零。",
    ...modePlain,
    ...baseFeedbackAliases,
  };
}

function deliveryCompleteKeyValues(payload: Record<string, unknown> | null): Record<string, string> {
  // delivery completion 是 Nav2 latest + operator report latest 的合成 gate，UI 只展示短摘要。
  const result = asRecord(payload?.latest_result) ?? payload;
  const nav2 = asRecord(result?.nav2_goal_execution);
  const operatorReport = asRecord(result?.operator_report);
  return {
    status: shortValue(result?.status ?? payload?.status),
    delivery_success: shortValue(result?.delivery_success ?? payload?.delivery_success, "false"),
    nav2_status: shortValue(nav2?.status),
    nav2_result_status: shortValue(nav2?.result_status),
    nav2_feedback_sample_count: shortValue(nav2?.feedback_sample_count, "0"),
    nav2_generated_at_ms: shortValue(nav2?.generated_at_ms),
    generated_at_ms: shortValue(result?.generated_at_ms ?? payload?.generated_at_ms),
    response_generated_at_ms: shortValue(payload?.generated_at_ms),
    operator_report_status: shortValue(operatorReport?.operator_report_status),
    operator_evidence_ref: shortValue(operatorReport?.evidence_ref),
    missing_required_material: shortValue(result?.missing_required_material),
  };
}

function deliveryMissingRequiredMaterial(...values: unknown[]): string[] {
  // 真实上位机有时返回数组，有时被 key/value 摘要压成 JSON 字符串；PC 顶层统一还原成短 token。
  const items = new Set<string>();
  const add = (value: unknown): void => {
    if (Array.isArray(value)) {
      value.forEach(add);
      return;
    }
    if (typeof value !== "string") {
      const text = shortValue(value, "");
      if (text) {
        add(text);
      }
      return;
    }
    const text = value.trim();
    if (!text || ["[]", "none", "not_loaded", "null", "undefined"].includes(text)) {
      return;
    }
    if (text.startsWith("[") || text.startsWith("{")) {
      try {
        const parsed = JSON.parse(text) as unknown;
        const parsedRecord = asRecord(parsed);
        if (Array.isArray(parsed)) {
          parsed.forEach(add);
          return;
        }
        if (parsedRecord?.missing_required_material !== undefined) {
          add(parsedRecord.missing_required_material);
          return;
        }
      } catch {
        // 解析失败时保留原短文本，避免丢失现场缺口线索。
      }
    }
    shortText(text, "").split(",").map((item) => item.trim()).filter(Boolean).forEach((item) => items.add(item));
  };
  values.forEach(add);
  return [...items];
}

function deliveryLatestMissingPlain(deliverySuccess: boolean, missing: string[]): string {
  // 送达 latest 是只读材料面板；白话只指向补材料，不暗示已经提交送达确认。
  if (deliverySuccess) {
    return "送达闭环已确认。";
  }
  if (missing.length > 0) {
    return `送达还差 ${missing.length} 项：${missing.join("、")}。`;
  }
  return "送达未确认；latest 未列出具体缺口，先复验 operator report 与 Nav2 执行材料。";
}

function deliveryMaterialRefs(payload: Record<string, unknown> | null): RobotControlDeliveryLatestResponse["delivery_material_refs"] {
  // latest 只把 operator report 里的短 ref 带给前端预填，不暴露完整远端 JSON 或任何 success/control 字段。
  const result = asRecord(payload?.latest_result) ?? payload;
  const operatorReport = asRecord(result?.operator_report);
  const claims = asRecord(operatorReport?.structured_hil_claims);
  return {
    operator_evidence_ref: shortValue(operatorReport?.evidence_ref, ""),
    external_video_ref: shortValue(claims?.external_video_ref, ""),
    camera_artifacts_ref: shortValue(claims?.camera_artifacts_ref, ""),
    route_map_ref: shortValue(claims?.route_map_ref, ""),
    site_state: shortValue(claims?.site_state, ""),
  };
}

function baseFeedbackSamplesFailure(
  sourceBaseUrl: string,
  reason: string,
  remoteEndpoint: RobotControlBaseFeedbackSamplesProxyResponse["remote_endpoint"] = "/api/base/feedback-samples",
): RobotControlBaseFeedbackSamplesProxyResponse {
  // 本机拒绝时不能触发任何串口请求；响应仍保持完整 fail-closed 形状。
  const sampleKeyValues = baseFeedbackSampleKeyValues(null);
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_base_feedback_samples_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "samples_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: remoteEndpoint,
    remote_http_status: null,
    status: "blocked",
    sample_key_values: sampleKeyValues,
    ...baseFeedbackSampleAliases(sampleKeyValues),
    readback_only: true,
    base_feedback_samples_readback_only: true,
    sends_motion_when_clicked: false,
    starts_camera_exclusive_capture: false,
    starts_radar_lifecycle: false,
    starts_nav2: false,
    starts_manual: false,
    starts_keyboard: false,
    starts_free_roam: false,
    starts_map_runtime: false,
    submits_delivery: false,
    stops_motion: false,
    next_action_plain: "轮速样本只读未完成；先确认上位机地址，再读取轮速样本。",
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    sends_motion_commands: false,
    robot_control_executed: false,
  };
}

function buildBaseFeedbackSamplesResponse(
  sourceBaseUrl: string,
  normalizedBaseUrl: URL,
  remoteEndpoint: RobotControlBaseFeedbackSamplesProxyResponse["remote_endpoint"],
  remote: { remote_http_status: number | null; payload: Record<string, unknown> | null; error: string },
): RobotControlBaseFeedbackSamplesProxyResponse {
  // POST 采样与 GET latest 共用同一套危险字段扫描，避免两个入口对“只读轮速”的解释分叉。
  const dangerous = scanDangerousTrueFields(remote.payload, "", BASE_FEEDBACK_SAMPLE_FAIL_CLOSED_FIELDS);
  const sampleKeyValues = baseFeedbackSampleKeyValues(remote.payload);
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_base_feedback_samples_proxy.v1",
    proxy_status:
      remote.remote_http_status === 200 && dangerous.length === 0 ? "samples_forwarded" : "samples_failed",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    source_base_url: sourceBaseUrl,
    normalized_base_url: normalizedBaseUrl.toString().replace(/\/$/, ""),
    remote_endpoint: remoteEndpoint,
    remote_http_status: remote.remote_http_status,
    status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "loaded" : "blocked"),
    sample_key_values: sampleKeyValues,
    ...baseFeedbackSampleAliases(sampleKeyValues),
    readback_only: true,
    base_feedback_samples_readback_only: true,
    sends_motion_when_clicked: false,
    starts_camera_exclusive_capture: false,
    starts_radar_lifecycle: false,
    starts_nav2: false,
    starts_manual: false,
    starts_keyboard: false,
    starts_free_roam: false,
    starts_map_runtime: false,
    submits_delivery: false,
    stops_motion: false,
    next_action_plain: sampleKeyValues.wheel_feedback_lr_nonzero_proven === "true"
      ? "轮速样本只读完成；同窗口 wheel L/R 非零证据已存在。"
      : sampleKeyValues.motion_signal_observed === "true"
        ? "轮速样本只读完成；已观察到 IMU 动作信号，但 wheel L/R 非零仍未证明。"
        : "轮速样本只读完成；直接执行 Nav2、键盘或自由移动后，再读取同窗口动作信号和 wheel L/R 非零证据。",
    failure_reason:
      dangerous.length > 0
        ? `dangerous_true_field:${dangerous[0]}`
        : remote.remote_http_status === 200
          ? ""
          : `feedback_samples_http_status_${remote.remote_http_status}`,
    blocked_reasons: [
      ...(remote.remote_http_status === 200 ? [] : [`feedback_samples_http_status_${remote.remote_http_status}`]),
      ...dangerous.map((field) => `dangerous_true_field:${field}`),
    ],
    hard_dangerous_true_fields: dangerous,
    sends_motion_commands: false,
    robot_control_executed: false,
  };
}

function finiteNumber(value: unknown): number | null {
  // 点动请求必须落到确定数值；NaN/Infinity/字符串都按无效处理。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function clamp(value: number, min: number, max: number): number {
  // 代理和 UI 双重限幅，确保浏览器绕过 disabled 也拿不到更大速度/时长。
  return Math.min(max, Math.max(min, value));
}

function allowedDirection(value: unknown): RobotControlBaseCommandRequest["direction"] | null {
  // 方向只接受固定白名单；常见脚本别名先归一，最终仍只向上位机转发标准方向。
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim().toLowerCase();
  const alias = normalized === "backward" || normalized === "reverse" ? "back" : normalized;
  return ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS.includes(alias as never)
    ? (alias as RobotControlBaseCommandRequest["direction"])
    : null;
}

function mapLifecycleStatusCode(proxyStatus: "lifecycle_forwarded" | "lifecycle_rejected" | "lifecycle_failed"): number {
  // lifecycle 代理保留 HTTP 语义：本机拒绝是 400，上位机/危险字段失败是 502，固定代理成功是 200。
  if (proxyStatus === "lifecycle_forwarded") {
    return 200;
  }
  return proxyStatus === "lifecycle_rejected" ? 400 : 502;
}

const BASE_COMMAND_FAIL_CLOSED_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "manual_control_enabled",
  "command_dispatch_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
]);

const BASE_FEEDBACK_SAMPLE_FAIL_CLOSED_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "manual_control_enabled",
  "command_dispatch_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "robot_control_executed",
  "sends_motion_commands",
  "sends_base_motion_commands",
  "publishes_cmd_vel",
  "calls_base_manual",
]);

const BASE_COMMAND_EVIDENCE_ENDPOINTS: Array<{
  id: RobotControlEvidenceCaptureEndpointId;
  endpoint: RobotControlEvidenceEndpointCapture["endpoint"];
}> = [
  { id: "base_status", endpoint: "/api/base/status" },
  { id: "base_feedback_samples_latest", endpoint: "/api/base/feedback-samples/latest" },
  { id: "radar_status", endpoint: "/api/radar/status" },
  { id: "radar_scan_proof_latest", endpoint: "/api/radar/scan-proof/latest" },
];
const BASE_COMMAND_EVIDENCE_ENDPOINT_TIMEOUT_MS = 5000;

const BASE_COMMAND_EVIDENCE_KEYS = [
  "schema",
  "status",
  "proof_status",
  "feedback_ack_status",
  "latest_t1001_observed_count",
  "base_command_mode",
  "nav2_base_command_mode",
  "nav2_goal_execute_default_base_command_mode",
  "wheel_feedback_lr_nonzero_proven",
  "wheel_feedback_nonzero_observed",
  "motion_signal_observed",
  "motion_signal_source",
  "physical_motion_lidar_delta_proven",
  "lidar_motion_delta_proven",
  "scan_delta_observed",
  "scan_delta_ref",
  "latest_proof_status",
  "latest_result_status",
  "evidence_ref",
  "latest_evidence_ref",
  "scan_status",
  "continuous_scan_status",
  "continuity_window_status",
  "continuous_window_observed",
  "lifecycle_running",
  "lifecycle_state",
  "lifecycle_status",
  "controller_server_active",
  "planner_server_active",
  "path_generated",
  "path_point_count",
  "latest_controller_active",
  "latest_planner_active",
  "latest_path_generated",
  "latest_path_point_count",
  "latest_scan_proof_fresh",
  "latest_raw_packet_proof_status",
  "scan_once_observed",
  "scan_hz_observed",
  "scan_point_count",
  "scan_preview_point_count",
  "scan_preview_source_point_count",
  "latest_scan_age_ms",
  "scan_age_ms",
  "raw_packet_once_observed",
  "tf_observed",
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "robot_control_executed",
  "blocked_reasons",
  "not_proven",
];

type BaseCommandEvidenceCapture = {
  evidence_capture_status: RobotControlEvidenceCaptureStatus;
  evidence_capture_endpoints: RobotControlEvidenceEndpointCapture[];
  evidence_capture_blocked_reasons: string[];
  before_readback: RobotControlEvidenceReadbackSummary;
  after_readback: RobotControlEvidenceReadbackSummary;
  motion_evidence_summary: string;
  motion_evidence_gaps: string[];
};

function compactKeyValues(payload: Record<string, unknown> | null): Record<string, string> {
  // 证据响应只保留排障短摘要，不把上位机 raw JSON 原样铺进 PC 合同或 UI。
  if (!payload) {
    return {};
  }
  const entries = BASE_COMMAND_EVIDENCE_KEYS.flatMap((key) => {
    const value = payload[key];
    if (value === undefined) {
      return [];
    }
    const serialized = typeof value === "string" ? value : JSON.stringify(value);
    return [[key, serialized.slice(0, 180)] as const];
  });
  return Object.fromEntries(entries);
}

function statusStringValue(payload: Record<string, unknown> | null, key: string, fallback = "not_loaded"): string {
  // 上车状态字段可能在顶层、proof_latest 或反馈摘要里；统一转成短字符串给 PC 直连状态代理。
  const feedbackSamples = asRecord(payload?.feedback_samples_latest);
  const feedbackReadback = asRecord(payload?.feedback_readback);
  const proofLatest = asRecord(payload?.proof_latest);
  const values = [
    payload?.[key],
    proofLatest?.[key],
    feedbackSamples?.[key],
    feedbackReadback?.[key],
  ];
  const value = firstLoadedValue(...values);
  if (value === undefined || value === null) {
    return fallback;
  }
  return (typeof value === "string" ? value : JSON.stringify(value)).slice(0, 180);
}

function readOnlyStatusKeyValues(payload: Record<string, unknown> | null): Record<string, string> {
  // compactKeyValues 只抓固定顶层；这里补齐 live 排障需要的嵌套状态别名。
  const base = compactKeyValues(payload);
  const keys = [
    "base_command_mode",
    "nav2_base_command_mode",
    "nav2_goal_execute_default_base_command_mode",
    "wheel_feedback_lr_nonzero_proven",
    "wheel_feedback_nonzero_observed",
    "motion_signal_observed",
    "motion_signal_source",
    "latest_t1001_observed_count",
    "lifecycle_running",
    "lifecycle_state",
    "controller_server_active",
    "planner_server_active",
    "path_generated",
    "path_point_count",
    "latest_controller_active",
    "latest_planner_active",
    "latest_path_generated",
    "latest_path_point_count",
    "status",
  ];
  for (const key of keys) {
    const value = statusStringValue(payload, key, "");
    if (value) {
      base[key] = value;
    }
  }
  return base;
}

function readOnlyStatusPlainFields(
  workstationEndpoint: RobotControlReadOnlyStatusWorkstationEndpoint,
  keyValues: Record<string, string>,
): Pick<
  RobotControlReadOnlyStatusResponse,
  | "plain_hint"
  | "next_action_plain"
  | "base_command_mode"
  | "nav2_base_command_mode"
  | "nav2_goal_execute_default_base_command_mode"
  | "lifecycle_running"
  | "lifecycle_state"
  | "controller_server_active"
  | "planner_server_active"
  | "path_generated"
  | "path_point_count"
  | "wheel_feedback_lr_nonzero_proven"
  | "wheel_feedback_nonzero_observed"
  | "motion_signal_observed"
  | "motion_signal_source"
  | "latest_t1001_observed_count"
> {
  // 这里只生成白话读回，不决定是否发车；真正动作仍走带安全确认的固定 POST。
  const baseCommandMode = keyValues.base_command_mode || "not_loaded";
  const nav2BaseCommandMode = keyValues.nav2_base_command_mode || "not_loaded";
  const nav2DefaultBaseMode = keyValues.nav2_goal_execute_default_base_command_mode || "not_loaded";
  const lifecycleRunning = keyValues.lifecycle_running || "not_loaded";
  const lifecycleState = keyValues.lifecycle_state || "not_loaded";
  const controllerActive = keyValues.controller_server_active || keyValues.latest_controller_active || "not_loaded";
  const plannerActive = keyValues.planner_server_active || keyValues.latest_planner_active || "not_loaded";
  const pathGenerated = keyValues.path_generated || keyValues.latest_path_generated || "not_loaded";
  const pathPointCount = keyValues.path_point_count || keyValues.latest_path_point_count || "not_loaded";
  const wheelLrNonzero = keyValues.wheel_feedback_lr_nonzero_proven || "not_loaded";
  const wheelAnyNonzero = keyValues.wheel_feedback_nonzero_observed || "not_loaded";
  const motionObserved = keyValues.motion_signal_observed || "not_loaded";
  const motionSource = keyValues.motion_signal_source || "not_loaded";
  const t1001Count = keyValues.latest_t1001_observed_count || "not_loaded";
  if (workstationEndpoint === "/api/robot-control/base/status") {
    const wheelReady = wheelLrNonzero === "true" || wheelAnyNonzero === "true";
    const motionReady = motionObserved === "true";
    return {
      plain_hint: wheelReady
        ? "底盘状态已读到，wheel raw L/R 已出现非零。"
        : motionReady
          ? "底盘状态已读到，wheel raw L/R 仍未非零；已看到其它运动迹象。"
          : "底盘状态已读到，wheel raw L/R 当前未非零。",
      next_action_plain: wheelReady
        ? "继续用同一个状态窗口复核 Nav2 路线或键盘手控闭环。"
        : "需要证明轮速时，直接执行短动作或路线，并读取同窗口 wheel raw L/R。",
      base_command_mode: baseCommandMode,
      nav2_base_command_mode: nav2BaseCommandMode,
      nav2_goal_execute_default_base_command_mode: nav2DefaultBaseMode,
      lifecycle_running: lifecycleRunning,
      lifecycle_state: lifecycleState,
      controller_server_active: controllerActive,
      planner_server_active: plannerActive,
      path_generated: pathGenerated,
      path_point_count: pathPointCount,
      wheel_feedback_lr_nonzero_proven: wheelLrNonzero,
      wheel_feedback_nonzero_observed: wheelAnyNonzero,
      motion_signal_observed: motionObserved,
      motion_signal_source: motionSource,
      latest_t1001_observed_count: t1001Count,
    };
  }
  const navStatus = keyValues.status || "not_loaded";
  const servicesReady = controllerActive === "true" && plannerActive === "true";
  const pathReady = pathGenerated === "true" && pathPointCount !== "0" && pathPointCount !== "not_loaded";
  const lifecycleInactive = lifecycleRunning === "false" || ["stopped", "inactive", "unconfigured"].includes(lifecycleState);
  const nextAction = servicesReady && pathReady
    ? "Nav2 路线和服务已读到；可直接执行图上路线。"
    : pathReady && (controllerActive === "false" || lifecycleInactive)
      ? "图上路线已生成；当前控制服务或 lifecycle 未 active。执行接口会托管启动自动驾驶 runtime，并在同窗口复验轮速 L/R。"
      : controllerActive === "false"
        ? "控制服务未 active；先恢复 Nav2 runtime，再确认路线点。"
      : "先启动或刷新 Nav2 runtime，再确认路线点和 controller 状态。";
  return {
    plain_hint: `Nav2 状态已读到：${navStatus}；路线点 ${pathPointCount}；控制服务=${controllerActive}。`,
    next_action_plain: nextAction,
    base_command_mode: baseCommandMode,
    nav2_base_command_mode: nav2BaseCommandMode,
    nav2_goal_execute_default_base_command_mode: nav2DefaultBaseMode,
    lifecycle_running: lifecycleRunning,
    lifecycle_state: lifecycleState,
    controller_server_active: controllerActive,
    planner_server_active: plannerActive,
    path_generated: pathGenerated,
    path_point_count: pathPointCount,
    wheel_feedback_lr_nonzero_proven: wheelLrNonzero,
    wheel_feedback_nonzero_observed: wheelAnyNonzero,
    motion_signal_observed: motionObserved,
    motion_signal_source: motionSource,
    latest_t1001_observed_count: t1001Count,
  };
}

function readOnlyStatusDangerousFields(
  workstationEndpoint: RobotControlReadOnlyStatusWorkstationEndpoint,
  payload: Record<string, unknown> | null,
): string[] {
  // 直连 status 是只读窗口；base/status 允许上车回报 readback sends_commands，但仍禁止 motion/control 顶层放行。
  const allowedReadback = new Set([
    "sends_commands",
    "readback_sends_commands",
  ]);
  return scanDangerousTrueFields(payload).filter((field) => {
    if (workstationEndpoint !== "/api/robot-control/base/status") {
      return true;
    }
    const last = field.split(".").pop() ?? field;
    return !allowedReadback.has(last);
  });
}

async function buildReadOnlyStatusResponse(
  sourceBaseUrl: string,
  workstationEndpoint: RobotControlReadOnlyStatusWorkstationEndpoint,
  remoteEndpoint: RobotControlReadOnlyStatusRemoteEndpoint,
): Promise<{ httpStatus: number; body: RobotControlReadOnlyStatusResponse }> {
  // 统一两个直连 status 代理，避免 base/nav2 出现不同的 fail-closed 细节。
  const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
  const fallbackBase: RobotControlReadOnlyStatusResponse = {
    schema: "trashbot.pc_tools_workstation.robot_control_read_only_status_proxy.v1",
    proxy_status: "status_rejected",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    robot_control_executed: false,
    source_base_url: sourceBaseUrl,
    normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
    workstation_endpoint: workstationEndpoint,
    remote_endpoint: remoteEndpoint,
    remote_method: "GET",
    remote_http_status: null,
    status: "blocked",
    status_key_values: {},
    ...readOnlyStatusPlainFields(workstationEndpoint, {}),
    failure_reason: normalized.ok ? "" : normalized.reason,
    blocked_reasons: normalized.ok ? [] : [normalized.reason],
    hard_dangerous_true_fields: [],
    sends_commands: false,
    sends_motion_commands: false,
  };
  if (!normalized.ok) {
    return { httpStatus: 400, body: fallbackBase };
  }
  try {
    const remote = await fetch(endpointUrl(normalized.normalized, remoteEndpoint), {
      method: "GET",
      signal: AbortSignal.timeout(10000),
    });
    const remotePayload = asRecord(await remote.json().catch(() => null));
    const dangerous = readOnlyStatusDangerousFields(workstationEndpoint, remotePayload);
    const statusKeyValues = readOnlyStatusKeyValues(remotePayload);
    const responseBody: RobotControlReadOnlyStatusResponse = {
      ...fallbackBase,
      proxy_status: remote.ok && remotePayload && dangerous.length === 0 ? "status_loaded" : "status_failed",
      remote_http_status: remote.status,
      status: remote.ok ? "loaded_fail_closed_summary" : "blocked",
      status_key_values: statusKeyValues,
      ...readOnlyStatusPlainFields(workstationEndpoint, statusKeyValues),
      failure_reason: dangerous.length > 0 ? `dangerous_true_field:${dangerous[0]}` : remote.ok ? "" : `status_http_status_${remote.status}`,
      blocked_reasons: [
        ...(remote.ok ? [] : [`status_http_status_${remote.status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
      ],
      hard_dangerous_true_fields: dangerous,
      sends_commands: false,
      sends_motion_commands: false,
      robot_control_executed: false,
    };
    return { httpStatus: responseBody.proxy_status === "status_loaded" ? 200 : 502, body: responseBody };
  } catch (error) {
    const reason = error instanceof Error ? shortText(error.message, "status_failed") : "status_failed";
    return {
      httpStatus: 502,
      body: { ...fallbackBase, proxy_status: "status_failed", failure_reason: reason, blocked_reasons: [reason] },
    };
  }
}

function radarStatusPlainFields(
  keyValues: Record<string, string>,
): Pick<
  RobotControlRadarStatusResponse,
  | "continuous_scan_status"
  | "lifecycle_running"
  | "lifecycle_state"
  | "latest_scan_proof_fresh"
  | "scan_point_count"
  | "latest_scan_age_ms"
  | "plain_hint"
  | "next_action_plain"
  | "radar_status_plain"
  | "radar_next_action_plain"
  | "radar_scan_required_observations"
  | "radar_scan_observation_status"
  | "radar_scan_observation_missing_reasons"
  | "radar_scan_ready_for_map_overlay"
  | "radar_overlay_ready_for_map"
  | "radar_map_overlay_readiness_status"
  | "radar_map_overlay_next_action_plain"
  | "radar_status_map_preview_endpoint"
  | "radar_status_map_preview_remote_endpoint"
  | "radar_status_map_preview_remote_http_status"
  | "radar_status_map_preview_status"
  | "radar_status_map_preview_radar_overlay_status"
  | "radar_status_map_preview_radar_overlay_current_point_count"
  | "radar_status_map_preview_radar_overlay_source_point_count"
  | "radar_status_map_preview_radar_overlay_wysiwyg_complete"
  | "radar_status_map_preview_radar_overlay_primary_blocked_reason"
  | "radar_status_map_preview_radar_overlay_current_vs_source_plain"
  | "radar_status_map_preview_failure_reason"
  | "radar_overlay_status"
  | "radar_overlay_point_count"
  | "radar_overlay_current_point_count"
  | "radar_overlay_source_point_count"
  | "radar_overlay_wysiwyg_complete"
  | "radar_overlay_primary_blocked_reason"
  | "radar_overlay_current_vs_source_plain"
  | "radar_overlay_wysiwyg_status_plain"
  | "radar_overlay_wysiwyg_next_action_plain"
> {
  // radar/status 只证明雷达本体；地图雷达点所见即所得必须以 map preview 同轮贴图为准。
  const observationLabel = (reason: string): string => ({
    scan_once: "没有读到一帧雷达",
    scan_hz: "雷达频率未确认",
    raw_packet_once: "雷达原始包未确认",
  }[reason] || reason.replace(/_/g, " "));
  const observationLabelPlain = (reasons: string[]): string => reasons.map(observationLabel).join("、") || "雷达新扫描未确认";
  const continuous = keyValues.continuous_scan_status || "not_loaded";
  const running = keyValues.lifecycle_running || "not_loaded";
  const lifecycleState = keyValues.lifecycle_state || "not_loaded";
  const fresh = keyValues.latest_scan_proof_fresh || "not_loaded";
  const scanPointCount = keyValues.scan_point_count || keyValues.scan_preview_point_count || "not_loaded";
  const scanAgeMs = keyValues.latest_scan_age_ms || keyValues.scan_age_ms || "not_loaded";
  const radarReady = running === "true" && fresh === "true";
  const radarStopped = running === "false" || lifecycleState === "stopped" || continuous === "lifecycle_not_running";
  const requiredObservations = [
    ["scan_once_observed", "scan_once"],
    ["scan_hz_observed", "scan_hz"],
    ["raw_packet_once_observed", "raw_packet_once"],
  ] as const;
  const missingObservations = radarReady
    ? []
    : requiredObservations
      .filter(([key]) => keyValues[key] !== "true")
      .map(([, label]) => label);
  const missingObservationText = missingObservations.length > 0 ? missingObservations.join(",") : "none";
  const observationStatus = radarReady
    ? "all_required_observations_observed"
    : missingObservations.length > 0
      ? "missing_required_observations"
      : "latest_scan_not_fresh";
  const overlayReadinessStatus = radarStopped
    ? "blocked_radar_lifecycle_not_running"
    : radarReady
      ? "scan_ready_refresh_map_preview"
      : missingObservations.length > 0
        ? "blocked_missing_scan_observations"
        : "blocked_latest_scan_not_fresh";
  const overlayReadyForMap = radarReady ? "map_preview_required" : "false";
  const overlayNextActionPlain = overlayReadinessStatus === "scan_ready_refresh_map_preview"
    ? "雷达扫描材料已就绪；刷新地图画面，确认地图上实际显示的雷达点数。"
    : overlayReadinessStatus === "blocked_missing_scan_observations"
      ? `先补齐雷达扫描材料：${observationLabelPlain(missingObservations)}；有新扫描后再刷新地图画面。`
      : radarStopped
        ? "先启动雷达并等待新扫描，再刷新地图画面确认雷达点。"
        : "先刷新雷达扫描读数，确认拿到新扫描后再刷新地图画面。";
  const radarStatusPlain = radarReady
    ? "雷达已运行，最新扫描是新的；地图雷达点仍以同轮地图预览为准。"
    : radarStopped
      ? "雷达未运行或扫描已停；旧雷达来源点不能当作当前地图雷达点。"
      : "雷达状态未完全就绪；需要确认雷达正在运行且有新扫描。";
  const radarNextActionPlain = radarReady
    ? "刷新地图画面，确认地图上实际显示的雷达点数。"
    : radarStopped
      ? "先启动雷达并等待新扫描，再刷新地图画面确认雷达点。"
      : "先刷新雷达扫描读数，再读取雷达状态；就绪后刷新地图画面确认雷达点。";
  return {
    continuous_scan_status: continuous,
    lifecycle_running: running,
    lifecycle_state: lifecycleState,
    latest_scan_proof_fresh: fresh,
    scan_point_count: scanPointCount,
    latest_scan_age_ms: scanAgeMs,
    plain_hint: `${radarStatusPlain.replace(/[。；\s]+$/g, "")}。下一步：${radarNextActionPlain.replace(/[。；\s]+$/g, "")}。`,
    next_action_plain: radarNextActionPlain,
    radar_status_plain: radarStatusPlain,
    radar_next_action_plain: radarNextActionPlain,
    radar_scan_required_observations: requiredObservations.map(([, label]) => label).join(","),
    radar_scan_observation_status: observationStatus,
    radar_scan_observation_missing_reasons: missingObservationText,
    radar_scan_ready_for_map_overlay: radarReady && missingObservations.length === 0 ? "true" : "false",
    radar_overlay_ready_for_map: overlayReadyForMap,
    radar_map_overlay_readiness_status: overlayReadinessStatus,
    radar_map_overlay_next_action_plain: overlayNextActionPlain,
    ...radarStatusMapPreviewFields(null, null, ""),
    radar_overlay_point_count: "not_loaded",
    radar_overlay_current_point_count: "not_loaded",
    radar_overlay_source_point_count: scanPointCount,
    radar_overlay_wysiwyg_complete: "false",
    radar_overlay_primary_blocked_reason: overlayReadinessStatus,
    radar_overlay_current_vs_source_plain: `地图雷达点：当前 not_loaded，来源 ${scanPointCount}；下一步：${overlayNextActionPlain}`,
    radar_overlay_wysiwyg_status_plain: `雷达 status 不直接绘制地图雷达点；${radarStatusPlain}`,
    radar_overlay_wysiwyg_next_action_plain: overlayNextActionPlain,
  };
}

function radarStatusMapPreviewFields(
  payload: Record<string, unknown> | null,
  remoteHttpStatus: number | null,
  failureReason: string,
): Pick<
  RobotControlRadarStatusResponse,
  | "radar_status_map_preview_endpoint"
  | "radar_status_map_preview_remote_endpoint"
  | "radar_status_map_preview_remote_http_status"
  | "radar_status_map_preview_status"
  | "radar_status_map_preview_radar_overlay_status"
  | "radar_status_map_preview_radar_overlay_current_point_count"
  | "radar_status_map_preview_radar_overlay_source_point_count"
  | "radar_status_map_preview_radar_overlay_wysiwyg_complete"
  | "radar_status_map_preview_radar_overlay_primary_blocked_reason"
  | "radar_status_map_preview_radar_overlay_current_vs_source_plain"
  | "radar_status_map_preview_failure_reason"
  | "radar_overlay_status"
  | "radar_overlay_point_count"
  | "radar_overlay_current_point_count"
  | "radar_overlay_source_point_count"
  | "radar_overlay_wysiwyg_complete"
  | "radar_overlay_primary_blocked_reason"
  | "radar_overlay_current_vs_source_plain"
> {
  // radar/status 本体不绘制地图点；这里额外读固定 map preview，只把同轮贴图结果合并为只读 alias。
  const payloadRoot = asRecord(payload?.payload) ?? payload;
  const overlayStatus = statusStringValue(payloadRoot, "radar_overlay_status");
  const currentPointCount = statusStringValue(payloadRoot, "radar_overlay_current_point_count",
    statusStringValue(payloadRoot, "radar_overlay_point_count", statusStringValue(payloadRoot, "radar_overlay_count")));
  const sourcePointCount = statusStringValue(payloadRoot, "radar_overlay_source_point_count",
    statusStringValue(payloadRoot, "radar_overlay_source_count"));
  const primaryBlockedReason = statusStringValue(payloadRoot, "radar_overlay_primary_blocked_reason", "")
    || (overlayStatus === "loaded" && currentPointCount !== "0" && currentPointCount !== "not_loaded" ? "none" : "map_preview_not_loaded");
  const currentVsSourcePlain = statusStringValue(payloadRoot, "radar_overlay_current_vs_source_plain", "")
    || `地图雷达点：当前 ${currentPointCount}，来源 ${sourcePointCount}；状态=${overlayStatus}。`;
  const complete = statusStringValue(payloadRoot, "radar_overlay_wysiwyg_complete", "")
    || (overlayStatus === "loaded" && currentPointCount !== "0" && currentPointCount !== "not_loaded" ? "true" : "false");
  return {
    radar_status_map_preview_endpoint: "/api/robot-control/map/preview",
    radar_status_map_preview_remote_endpoint: "/api/map/preview",
    radar_status_map_preview_remote_http_status: remoteHttpStatus,
    radar_status_map_preview_status: payloadRoot ? shortText(payloadRoot.status, remoteHttpStatus && remoteHttpStatus >= 400 ? "blocked" : "loaded") : "not_loaded",
    radar_status_map_preview_radar_overlay_status: overlayStatus,
    radar_status_map_preview_radar_overlay_current_point_count: currentPointCount,
    radar_status_map_preview_radar_overlay_source_point_count: sourcePointCount,
    radar_status_map_preview_radar_overlay_wysiwyg_complete: complete,
    radar_status_map_preview_radar_overlay_primary_blocked_reason: primaryBlockedReason,
    radar_status_map_preview_radar_overlay_current_vs_source_plain: currentVsSourcePlain,
    radar_status_map_preview_failure_reason: failureReason,
    radar_overlay_status: overlayStatus,
    radar_overlay_point_count: currentPointCount,
    radar_overlay_current_point_count: currentPointCount,
    radar_overlay_source_point_count: sourcePointCount,
    radar_overlay_wysiwyg_complete: complete,
    radar_overlay_primary_blocked_reason: primaryBlockedReason,
    radar_overlay_current_vs_source_plain: currentVsSourcePlain,
  };
}

const RADAR_STATUS_READBACK_FLAGS = {
  // radar/status 只读取雷达与贴图诊断，不启动 lifecycle，也不触发任何底盘/导航动作。
  readback_only: true,
  radar_status_readback_only: true,
  sends_motion_when_clicked: false,
  starts_radar_lifecycle: false,
  starts_nav2: false,
  starts_manual: false,
  starts_keyboard: false,
  starts_free_roam: false,
  starts_map_runtime: false,
  submits_delivery: false,
  stops_motion: false,
} satisfies Pick<
  RobotControlRadarStatusResponse,
  | "readback_only"
  | "radar_status_readback_only"
  | "sends_motion_when_clicked"
  | "starts_radar_lifecycle"
  | "starts_nav2"
  | "starts_manual"
  | "starts_keyboard"
  | "starts_free_roam"
  | "starts_map_runtime"
  | "submits_delivery"
  | "stops_motion"
>;

function evidenceReadbackSummary(
  endpoints: RobotControlEvidenceEndpointCapture[],
  phase: RobotControlEvidenceCapturePhase,
): RobotControlEvidenceReadbackSummary {
  // before/after 摘要按固定 endpoint id 索引，前端和 reviewer 可以稳定比较同一类读数。
  return Object.fromEntries(
    endpoints.filter((endpoint) => endpoint.phase === phase).map((endpoint) => [endpoint.id, endpoint]),
  ) as RobotControlEvidenceReadbackSummary;
}

function evidenceStatus(endpoints: RobotControlEvidenceEndpointCapture[], preflightReason = ""): RobotControlEvidenceCaptureStatus {
  // captured 只代表固定 GET 快照完整，不代表 HIL pass、运动安全或送达成功。
  if (preflightReason) {
    return "blocked";
  }
  const loadedCount = endpoints.filter((endpoint) => endpoint.request_status === "loaded").length;
  if (loadedCount === endpoints.length && endpoints.length > 0) {
    return "captured";
  }
  return loadedCount > 0 ? "partial" : "blocked";
}

function buildMotionEvidenceSummary(
  commandKind: "manual" | "stop",
  status: RobotControlEvidenceCaptureStatus,
): string {
  // 这句话会进入响应合同和首页摘要，必须明确“证据快照不是 HIL 通过”。
  const commandLabel = commandKind === "stop" ? "stop command" : "manual command";
  if (status === "captured") {
    return `${commandLabel} before/after fixed GET evidence snapshot captured; this is not HIL pass.`;
  }
  if (status === "partial") {
    return `${commandLabel} before/after fixed GET evidence snapshot partially captured; this is not HIL pass.`;
  }
  return `${commandLabel} before/after fixed GET evidence snapshot blocked or unavailable; this is not HIL pass.`;
}

function evidenceKeyTrue(readback: RobotControlEvidenceReadbackSummary, endpointId: RobotControlEvidenceCaptureEndpointId, keys: string[]): boolean {
  // 上位机后续若补出结构化运动 proof，PC 才能把对应 gap 清掉；只读 T=1001 不算轮速非零。
  const keyValues = readback[endpointId]?.key_values ?? {};
  return keys.some((key) => keyValues[key] === "true");
}

function buildMotionEvidenceGaps(
  commandKind: "manual" | "stop",
  status: RobotControlEvidenceCaptureStatus,
  afterReadback: RobotControlEvidenceReadbackSummary,
  preflightReason = "",
  remoteMotionKeyValues: Record<string, string> = {},
): string[] {
  // gap 是下一步补证据清单，不是放行依据；stop 永远不是运动证明。
  if (commandKind === "stop") {
    return ["stop_command_not_motion_proof"];
  }
  const remoteWheelFeedbackObserved =
    remoteMotionKeyValues.wheel_feedback_lr_nonzero_proven === "true"
    || remoteMotionKeyValues.wheel_feedback_nonzero_observed === "true";
  const remoteLidarDeltaObserved =
    remoteMotionKeyValues.physical_motion_lidar_delta_proven === "true"
    || remoteMotionKeyValues.lidar_motion_delta_proven === "true"
    || remoteMotionKeyValues.scan_delta_observed === "true";
  const remoteBodyMotionObserved =
    // 上位机同窗口 IMU 姿态变化只能清掉“有无运动迹象”gap，wheel raw L/R 仍独立验收。
    remoteMotionKeyValues.motion_signal_observed === "true"
    || remoteMotionKeyValues.imu_attitude_delta_observed === "true"
    || remoteMotionKeyValues.manual_imu_attitude_delta_observed === "true";
  const gaps = [
    preflightReason ? "motion_command_not_forwarded" : "",
    status === "captured" ? "" : "before_after_evidence_snapshot_incomplete",
    remoteWheelFeedbackObserved
      || evidenceKeyTrue(afterReadback, "base_status", ["wheel_feedback_lr_nonzero_proven", "wheel_feedback_nonzero_observed"])
      || evidenceKeyTrue(afterReadback, "base_feedback_samples_latest", ["wheel_feedback_lr_nonzero_proven", "wheel_feedback_nonzero_observed"])
      ? ""
      : "wheel_feedback_lr_nonzero_not_proven",
    remoteLidarDeltaObserved
      || remoteBodyMotionObserved
      || evidenceKeyTrue(afterReadback, "radar_status", ["physical_motion_lidar_delta_proven", "lidar_motion_delta_proven", "scan_delta_observed"])
      || evidenceKeyTrue(afterReadback, "radar_scan_proof_latest", ["physical_motion_lidar_delta_proven", "lidar_motion_delta_proven", "scan_delta_observed"])
      ? ""
      : "physical_motion_lidar_delta_not_proven",
  ];
  return gaps.filter(Boolean);
}

function buildEvidenceCapture(
  commandKind: "manual" | "stop",
  endpoints: RobotControlEvidenceEndpointCapture[],
  preflightReason = "",
  remoteMotionKeyValues: Record<string, string> = {},
): BaseCommandEvidenceCapture {
  // evidence_capture_* 字段集中生成，保证成功、失败、本地拒绝三条路径合同一致。
  const status = evidenceStatus(endpoints, preflightReason);
  const beforeReadback = evidenceReadbackSummary(endpoints, "before");
  const afterReadback = evidenceReadbackSummary(endpoints, "after");
  const endpointFailures = endpoints
    .filter((endpoint) => endpoint.request_status !== "loaded")
    .map((endpoint) => `${endpoint.phase}_${endpoint.id}:${endpoint.failure_reason}`);
  return {
    evidence_capture_status: status,
    evidence_capture_endpoints: endpoints,
    evidence_capture_blocked_reasons: [...(preflightReason ? [preflightReason] : []), ...endpointFailures],
    before_readback: beforeReadback,
    after_readback: afterReadback,
    motion_evidence_summary: buildMotionEvidenceSummary(commandKind, status),
    motion_evidence_gaps: buildMotionEvidenceGaps(commandKind, status, afterReadback, preflightReason, remoteMotionKeyValues),
  };
}

function blockedEvidenceCapture(commandKind: "manual" | "stop", reason: string): BaseCommandEvidenceCapture {
  // baseUrl 无法规范化时不能尝试任何远端 GET；响应仍显式写明采集被阻断。
  return buildEvidenceCapture(commandKind, [], reason);
}

function realtimeManualEvidenceCapture(remoteMotionKeyValues: Record<string, string> = {}): BaseCommandEvidenceCapture {
  // WASD/屏幕方向键需要低延迟；完整轮速和雷达复验在松手后走固定只读 readback。
  return {
    evidence_capture_status: "partial",
    evidence_capture_endpoints: [],
    evidence_capture_blocked_reasons: ["realtime_manual_skips_before_after_get_snapshot"],
    before_readback: {},
    after_readback: {},
    motion_evidence_summary: "manual command realtime path skipped before/after fixed GET evidence snapshot; release readback must verify wheel/summary.",
    motion_evidence_gaps: buildMotionEvidenceGaps("manual", "partial", {}, "", remoteMotionKeyValues),
  };
}

async function fetchEvidenceEndpoint(
  baseUrl: URL,
  phase: RobotControlEvidenceCapturePhase,
  config: (typeof BASE_COMMAND_EVIDENCE_ENDPOINTS)[number],
): Promise<RobotControlEvidenceEndpointCapture> {
  // 运动证据采集只允许固定 GET endpoint；不接受用户提供 method、path 或 body。
  try {
    const response = await fetch(endpointUrl(baseUrl, config.endpoint), {
      method: "GET",
      signal: AbortSignal.timeout(BASE_COMMAND_EVIDENCE_ENDPOINT_TIMEOUT_MS),
    });
    const payload = asRecord(await response.json().catch(() => null));
    return {
      phase,
      id: config.id,
      endpoint: config.endpoint,
      method: "GET",
      request_status: response.ok && payload ? "loaded" : "failed",
      http_status: response.status,
      status: shortText(payload?.status, response.ok ? "loaded" : "blocked"),
      schema: shortText(payload?.schema, "not_loaded"),
      key_values: compactKeyValues(payload),
      failure_reason: response.ok && payload ? "" : `http_status_${response.status}`,
    };
  } catch (error) {
    return {
      phase,
      id: config.id,
      endpoint: config.endpoint,
      method: "GET",
      request_status: "failed",
      http_status: null,
      status: "blocked",
      schema: "not_loaded",
      key_values: {},
      failure_reason: error instanceof Error ? shortText(error.message, "fetch_failed") : "fetch_failed",
    };
  }
}

async function captureEvidencePhase(
  baseUrl: URL,
  phase: RobotControlEvidenceCapturePhase,
): Promise<RobotControlEvidenceEndpointCapture[]> {
  // 上位机部分 GET 会同步读串口/雷达；串行采集避免并发请求把 aiohttp 事件循环挤到超时。
  const captures: RobotControlEvidenceEndpointCapture[] = [];
  for (const endpoint of BASE_COMMAND_EVIDENCE_ENDPOINTS) {
    captures.push(await fetchEvidenceEndpoint(baseUrl, phase, endpoint));
  }
  return captures;
}

function baseCommandFailure(
  sourceBaseUrl: string,
  commandKind: "manual" | "stop",
  remoteEndpoint: "/api/base/manual" | "/api/base/stop",
  reason: string,
  requestedDirection: RobotControlBaseCommandRequest["direction"],
  requestedSpeedMps: number | null,
  requestedDurationMs: number | null,
  confirmHilChecklist: boolean,
  evidenceCapture: BaseCommandEvidenceCapture = blockedEvidenceCapture(commandKind, reason),
  operatorReportPreflight: RobotControlOperatorReportPreflight = notRequiredOperatorReportPreflight(),
): RobotControlBaseCommandProxyResponse {
  // 即使失败也返回完整 fail-closed 合同，避免前端在错误态分叉出另一套解释逻辑。
  const isStop = requestedDirection === "stop" || commandKind === "stop";
  const failureEvidenceCapture = isStop || evidenceCapture.motion_evidence_gaps.includes("motion_command_not_forwarded")
    ? evidenceCapture
    : {
        ...evidenceCapture,
        motion_evidence_gaps: ["motion_command_not_forwarded", ...evidenceCapture.motion_evidence_gaps],
      };
  const resolvedOperatorReportPreflight = isStop || operatorReportPreflight.status !== "not_required_for_stop"
    ? operatorReportPreflight
    : {
        ...operatorReportPreflight,
        status: "blocked" as const,
        request_status: "blocked" as const,
        report_status: "not_checked",
        evidence_ref: "not_checked",
        missing_fields: operatorReportPreflight.required_fields,
        failure_reason: reason,
      };
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
    command_kind: commandKind,
    proxy_status: "command_rejected",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    robot_control_executed: false,
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: remoteEndpoint,
    remote_http_status: null,
    status: "blocked",
    requested_direction: requestedDirection,
    applied_direction: isStop ? "stop" : requestedDirection,
    requested_speed_mps: requestedSpeedMps,
    clamped_speed_mps: isStop ? 0 : clamp(requestedSpeedMps ?? 0, 0, ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS),
    requested_duration_ms: requestedDurationMs,
    clamped_duration_ms: isStop ? 0 : clamp(requestedDurationMs ?? 0, 0, ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS),
    confirm_hil_checklist: confirmHilChecklist,
    ...baseCommandMinimalPrecheckFields(confirmHilChecklist),
    non_stop_requires_confirm_hil_checklist: false,
    hil_checklist_gate_status: isStop ? "stop_allowed_without_checklist" : "manual_allowed",
    checklist_missing: [],
    operator_report_preflight: resolvedOperatorReportPreflight,
    request_contract: {
      max_speed_mps: ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
      max_duration_ms: ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS,
      allowed_directions: [...ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS],
    },
    ...failureEvidenceCapture,
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
  };
}

function baseCommandMinimalPrecheckFields(confirmHilChecklist: boolean) {
  // 现场本轮按 CEO 口径默认安全，旧字段名只作为上位机兼容字段保留，不再要求用户手动勾选。
  return {
    minimal_precheck_safety_only: true as const,
    safety_confirmation_field: "confirm_hil_checklist" as const,
    safety_confirmation_received: confirmHilChecklist,
    operator_report_preflight_required: false as const,
    camera_or_radar_required_for_motion: false as const,
    minimal_precheck_plain: confirmHilChecklist
      ? "最小预检已通过：现场默认安全，不要求用户额外勾选；相机、雷达和 operator report 不作为本次低速运动前置。"
      : "停止或失败读回不需要安全确认；相机、雷达和 operator report 不作为低速运动前置。",
  };
}

function finiteManualSpeedFromPayload(payload: Record<string, unknown> | null): number | null {
  // PC 前端使用 speed，现场脚本更常写 speed_mps；两个名字都收敛到同一条低速手控合同。
  return finiteNumber(payload?.speed ?? payload?.speed_mps ?? payload?.linear_x_mps ?? payload?.linear_mps);
}

function manualCommandModeFromPayload(payload: Record<string, unknown> | null): "ros" | "speed" | "pwm" {
  // 页面默认仍是 ROS bridge；显式传 mode 时给现场快速 A/B，不让 PC 代理把 speed/pwm 掉包成 ros。
  const value = String(payload?.command_mode ?? payload?.manual_command_mode ?? "").trim().toLowerCase();
  return value === "speed" || value === "pwm" || value === "ros"
    ? value
    : ROBOT_CONTROL_KEYBOARD_MANUAL_COMMAND_MODE;
}

async function fetchFixedRobotPostSummary(
  baseUrl: string,
  endpoint: "/api/base/manual" | "/api/base/stop" | RobotControlFreeRoamAutonomyEndpoint,
  body: Record<string, unknown>,
): Promise<{ remote_http_status: number | null; payload: Record<string, unknown> | null; error: string }> {
  // 这里专门服务固定 base manual/stop 代理，不接受动态 endpoint，避免扩展成万能 POST 转发器。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return { remote_http_status: null, payload: null, error: normalized.reason };
  }
  // 上位机 ROS2 CLI /cmd_vel 短 pulse 本身很短，但进程启动和 DDS 匹配现场实测可到约 15s；PC 只放宽等待响应，不放宽运动时长。
  const timeoutMs = endpoint.startsWith("/api/free-roam/autonomy/") ? 60000 : 25000;
  try {
    const response = await fetch(endpointUrl(normalized.normalized, endpoint), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    });
    const json = await response.json().catch(() => null);
    return {
      remote_http_status: response.status,
      payload: asRecord(json),
      error: "",
    };
  } catch (error) {
    if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
      return {
        remote_http_status: null,
        payload: null,
        error: `fetch_timeout_${timeoutMs}ms`,
      };
    }
    return {
      remote_http_status: null,
      payload: null,
      error: error instanceof Error ? shortText(error.message, "upper_api_unreachable") : "upper_api_unreachable",
    };
  }
}

function freeRoamAutonomyProxyFailure(
  sourceBaseUrl: string,
  action: RobotControlFreeRoamAutonomyAction,
  remoteEndpoint: RobotControlFreeRoamAutonomyEndpoint,
  reason: string,
  requestBody: Record<string, boolean> = {},
): RobotControlFreeRoamAutonomyResponse {
  // 自动扫图代理失败也要保持完整合同，避免前端把异常当成已经启动。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_free_roam_autonomy_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    action,
    proxy_status: "autonomy_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: remoteEndpoint,
    remote_method: "POST",
    remote_http_status: null,
    status: "blocked",
    request_body: requestBody,
    command_result: { mode: "not_sent", executed: false, ok: false },
    latest_decision_state: "not_loaded",
    latest_cmd_vel_publish_enabled: false,
    start_runtime_wait: {
      waited: false,
      ok: false,
      reason: "not_sent",
    },
    sets_state_machine_parameters: false,
    direct_cmd_vel_publish: false,
    motion_unlock_requested: false,
    does_not_set_motion_unlock: true,
    free_move_start_ready: false,
    free_move_blocked_reasons: [reason],
    mapping_readiness_ready: false,
    mapping_blocked_reasons: ["not_checked"],
    sensor_readiness: {
      ready: false,
      missing: ["not_checked"],
    },
    blocked_parameters_not_touched: ["enable_cmd_vel_publish", "motion_hil_unlocked", "cmd_vel_topic"],
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function freeRoamAutonomyProxyResponse(
  sourceBaseUrl: string,
  action: RobotControlFreeRoamAutonomyAction,
  remoteEndpoint: RobotControlFreeRoamAutonomyEndpoint,
  requestBody: Record<string, boolean>,
  remote: { remote_http_status: number | null; payload: Record<string, unknown> | null; error: string },
): RobotControlFreeRoamAutonomyResponse {
  // 只摘取上位机短字段；完整 runtime 仍通过 latest/readback 展示。
  if (remote.error || !remote.payload) {
    return {
      ...freeRoamAutonomyProxyFailure(sourceBaseUrl, action, remoteEndpoint, remote.error || "upper_api_bad_response", requestBody),
      proxy_status: "autonomy_failed",
      remote_http_status: remote.remote_http_status,
    };
  }
  const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
  const commandResult = asRecord(remote.payload.command_result);
  const commandResultItems = Array.isArray(commandResult?.results) ? commandResult.results : [];
  const firstCommandResult = asRecord(commandResultItems[0]);
  const commandParameters = Array.isArray(firstCommandResult?.parameters)
    ? firstCommandResult.parameters.map((item) => shortValue(item, "unknown")).filter((item) => item !== "unknown")
    : Array.isArray(commandResult?.touched_parameters)
      ? commandResult.touched_parameters.map((item) => shortValue(item, "unknown")).filter((item) => item !== "unknown")
      : [];
  const sensorReadiness = asRecord(remote.payload.sensor_readiness);
  const mappingReadiness = asRecord(sensorReadiness?.mapping_readiness);
  const startRuntimeWait = asRecord(remote.payload.start_runtime_wait);
  const motionUnlockRequested = remote.payload.motion_unlock_requested === true;
  const freeMoveStartReady = remote.payload.free_move_start_ready === true
    || sensorReadiness?.free_move_ready === true
    || sensorReadiness?.ready === true;
  const freeMoveBlockedReasons = Array.isArray(remote.payload.free_move_blocked_reasons)
    ? remote.payload.free_move_blocked_reasons.map((item) => shortValue(item, "unknown"))
    : Array.isArray(sensorReadiness?.missing) && !freeMoveStartReady
      ? sensorReadiness.missing.map((item) => shortValue(item, "unknown"))
      : [];
  const mappingBlockedReasons = Array.isArray(remote.payload.mapping_blocked_reasons)
    ? remote.payload.mapping_blocked_reasons.map((item) => shortValue(item, "unknown"))
    : Array.isArray(mappingReadiness?.missing)
      ? mappingReadiness.missing.map((item) => shortValue(item, "unknown"))
      : [];
  const forwarded = remote.remote_http_status !== null && remote.remote_http_status >= 200 && remote.remote_http_status < 300 && remote.payload.status === "requested";
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_free_roam_autonomy_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    action,
    proxy_status: forwarded ? "autonomy_forwarded" : "autonomy_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
    remote_endpoint: remoteEndpoint,
    remote_method: "POST",
    remote_http_status: remote.remote_http_status,
    status: forwarded ? "requested" : "blocked",
    request_body: requestBody,
    command_result: {
      mode: shortValue(commandResult?.mode, "not_loaded"),
      executed: commandResult?.executed === true,
      ok: typeof commandResult?.ok === "boolean" ? commandResult.ok : null,
      write_strategy: shortValue(firstCommandResult?.write_strategy, "unknown"),
      parameters: commandParameters,
      parameter_count: commandParameters.length,
      stdout_preview: shortValue(firstCommandResult?.stdout_preview, ""),
    },
    latest_decision_state: shortValue(remote.payload.latest_decision_state, "not_loaded"),
    latest_cmd_vel_publish_enabled: remote.payload.latest_cmd_vel_publish_enabled === true,
    start_runtime_wait: {
      waited: startRuntimeWait?.waited === true,
      ok: startRuntimeWait?.ok === true,
      attempts: typeof startRuntimeWait?.attempts === "number" ? startRuntimeWait.attempts : undefined,
      http_status: typeof startRuntimeWait?.http_status === "number" ? startRuntimeWait.http_status : null,
      decision_state: shortValue(startRuntimeWait?.decision_state, ""),
      cmd_vel_publish_enabled: startRuntimeWait?.cmd_vel_publish_enabled === true,
      failure_reason: shortValue(startRuntimeWait?.failure_reason, ""),
      reason: shortValue(startRuntimeWait?.reason, ""),
    },
    sets_state_machine_parameters: remote.payload.sets_state_machine_parameters === true,
    mapping_active_requested: remote.payload.mapping_active_requested === true,
    mapping_active_applied: remote.payload.mapping_active_applied === true,
    direct_cmd_vel_publish: false,
    motion_unlock_requested: motionUnlockRequested,
    does_not_set_motion_unlock: remote.payload.does_not_set_motion_unlock === false ? false : true,
    free_move_start_ready: freeMoveStartReady,
    free_move_blocked_reasons: freeMoveBlockedReasons,
    mapping_readiness_ready: remote.payload.mapping_readiness_ready === true || mappingReadiness?.ready === true,
    mapping_blocked_reasons: mappingBlockedReasons,
    sensor_readiness: {
      ready: sensorReadiness?.ready === true,
      missing: Array.isArray(sensorReadiness?.missing)
        ? sensorReadiness.missing.map((item) => shortValue(item, "unknown"))
        : [],
      free_move_ready: sensorReadiness?.free_move_ready === true,
      free_move_without_camera_allowed: sensorReadiness?.free_move_without_camera_allowed === true,
      motion_without_radar_allowed: sensorReadiness?.motion_without_radar_allowed === true,
      degraded_without_radar: sensorReadiness?.degraded_without_radar === true,
      mapping_readiness: {
        ready: mappingReadiness?.ready === true,
        missing: Array.isArray(mappingReadiness?.missing)
          ? mappingReadiness.missing.map((item) => shortValue(item, "unknown"))
          : [],
        requires_camera_first_frame: mappingReadiness?.requires_camera_first_frame === true,
        requires_fresh_radar_scan: mappingReadiness?.requires_fresh_radar_scan === true,
        free_move_allowed_when_mapping_not_ready: mappingReadiness?.free_move_allowed_when_mapping_not_ready === true,
      },
      camera: asRecord(sensorReadiness?.camera) ?? {},
      radar: asRecord(sensorReadiness?.radar) ?? {},
    },
    blocked_parameters_not_touched: Array.isArray(remote.payload.blocked_parameters_not_touched)
      ? remote.payload.blocked_parameters_not_touched.map((item) => shortValue(item, "unknown"))
      : [],
    failure_reason: shortValue(remote.payload.failure_reason, forwarded ? "none" : "free_roam_autonomy_rejected"),
    blocked_reasons: Array.isArray(remote.payload.blocked_reasons)
      ? remote.payload.blocked_reasons.map((item) => shortValue(item, "unknown"))
      : forwarded ? [] : ["free_roam_autonomy_rejected"],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function freeRoamAutonomyLatestKeyValues(payload: Record<string, unknown> | null): Record<string, string> {
  // latest 只读 runtime 摘要；不把完整 decision/gates 原样透出，避免普通接口变成 raw artifact dump。
  const latest = asRecord(payload?.latest_result) ?? payload;
  const decision = asRecord(latest?.decision);
  const mapMetrics = asRecord(latest?.map_metrics) ?? asRecord(payload?.map_metrics);
  const snapshot = asRecord(latest?.snapshot) ?? asRecord(payload?.snapshot);
  const mapFreeCells = shortValue(
    mapMetrics?.free_cells ?? snapshot?.map_free_cells ?? snapshot?.free_cells,
    "not_loaded",
  );
  const mapUnknownRatio = shortValue(
    mapMetrics?.unknown_ratio ?? snapshot?.map_unknown_ratio ?? snapshot?.unknown_ratio,
    "not_loaded",
  );
  const gates = Array.isArray(decision?.gates) ? decision.gates : [];
  const gateStateById = new Map(gates
    .map((gate) => asRecord(gate))
    .filter((gate): gate is Record<string, unknown> => gate !== null)
    .map((gate) => [shortValue(gate.id), shortValue(gate.state)]));
  const externalStopRequested = snapshot?.external_stop_requested === true || gateStateById.has("external_stop_request");
  // 自由移动只看 runtime 启停门禁；建图验收必须把四个材料缺口补齐，避免 latest 和 summary 口径打架。
  const remoteMappingStartMissing = shortStringList(latest?.free_roam_mapping_start_missing_reasons ?? payload?.free_roam_mapping_start_missing_reasons)
    .map(normalizeFreeRoamMappingMissingId);
  const remoteMappingStartReady = booleanTrueValue(latest?.free_roam_mapping_start_ready ?? payload?.free_roam_mapping_start_ready);
  const mappingMissing = FREE_ROAM_MAPPING_REQUIRED_GATE_IDS.filter((id) => gateStateById.get(id) !== "ready");
  const mappingStartMissing = remoteMappingStartMissing.length > 0
    ? Array.from(new Set(remoteMappingStartMissing))
    : FREE_ROAM_MAPPING_START_REQUIRED_GATE_IDS.filter((id) => gateStateById.get(id) !== "ready");
  const mappingStartReady = remoteMappingStartReady || mappingStartMissing.length === 0;
  return {
    status: shortValue(payload?.status),
    runtime_status: shortValue(latest?.status, "loaded"),
    decision_state: shortValue(decision?.state ?? latest?.decision_state),
    decision_reason: shortValue(decision?.reason ?? latest?.decision_reason),
    stop_required: shortValue(decision?.stop_required ?? latest?.stop_required),
    external_stop_requested: externalStopRequested ? "true" : "false",
    operator_confirmed: gateStateById.get("operator_confirmed") === "ready" ? "true" : gateStateById.has("operator_confirmed") ? "false" : "not_loaded",
    artifact_only: shortValue(latest?.artifact_only),
    cmd_vel_publish_enabled: shortValue(latest?.cmd_vel_publish_enabled),
    free_roam_motion_start_ready: shortValue(latest?.free_roam_motion_start_ready ?? payload?.free_roam_motion_start_ready, "false"),
    free_move_start_ready: shortValue(latest?.free_move_start_ready ?? payload?.free_move_start_ready, "false"),
    motion_start_ready: shortValue(latest?.motion_start_ready ?? payload?.motion_start_ready, "false"),
    motion_without_radar_allowed: shortValue(latest?.motion_without_radar_allowed ?? payload?.motion_without_radar_allowed, "false"),
    free_move_without_camera_allowed: shortValue(latest?.free_move_without_camera_allowed ?? payload?.free_move_without_camera_allowed, "false"),
    gate_count: String(gates.length),
    runtime_gate_count: String(gates.length),
    mapping_gate_count: String(FREE_ROAM_MAPPING_REQUIRED_GATE_IDS.length),
    mapping_required_ids: FREE_ROAM_MAPPING_REQUIRED_GATE_IDS.join(","),
    mapping_missing: mappingMissing.length > 0 ? mappingMissing.join(",") : "none",
    mapping_ready: mappingMissing.length === 0 ? "true" : "false",
    mapping_start_required_ids: FREE_ROAM_MAPPING_START_REQUIRED_GATE_IDS.join(","),
    mapping_start_missing: mappingStartMissing.length > 0 ? mappingStartMissing.join(",") : "none",
    mapping_start_ready: mappingStartReady ? "true" : "false",
    free_roam_mapping_start_ready: mappingStartReady ? "true" : "false",
    free_roam_mapping_start_missing_reasons: mappingStartMissing.length > 0 ? mappingStartMissing.join(",") : "none",
    free_roam_mapping_start_plain: shortValue(latest?.free_roam_mapping_start_plain ?? payload?.free_roam_mapping_start_plain, ""),
    free_roam_mapping_start_next_action: shortValue(latest?.free_roam_mapping_start_next_action ?? payload?.free_roam_mapping_start_next_action, ""),
    map_free_cells: mapFreeCells,
    map_unknown_ratio: mapUnknownRatio,
  };
}

function freeRoamLatestMissingPlainLabels(missingReasons: string[]): string[] {
  // latest endpoint 不依赖 summary，也要把建图缺口翻译成普通用户能理解的短词。
  const labels: Record<string, string> = {
    camera_first_frame: "画面首帧",
    lidar_fresh: "雷达新鲜",
    mapping_active: "地图记录",
    fresh_map_preview: "地图画面",
  };
  return missingReasons.map((reason) => labels[reason] ?? reason).filter(Boolean);
}

function freeRoamLatestMotionReadinessPlain(startReady: boolean, motionReady: boolean, externalStopRequested: boolean): string {
  // 低速自由移动和建图验收分层；相机/雷达缺口不能再被解释成车不能先动。
  if (!startReady) {
    return "自由移动未就绪；先连接上车状态机并确认停止兜底。";
  }
  if (motionReady) {
    return "自由移动正在运行；相机和雷达不作为继续移动的前置。";
  }
  if (externalStopRequested) {
    return "可先自由移动；停止请求会在开始时自动解除，不作为启动阻塞。";
  }
  return "可先自由移动；现场默认安全，只保留停止兜底。";
}

function freeRoamLatestMappingReadinessPlain(startReady: boolean, mappingReady: boolean, mappingMissingReasons: string[]): string {
  if (mappingReady) {
    return "建图验收已就绪；雷达和摄像头材料满足，可以继续低速建图。";
  }
  const missingText = freeRoamLatestMissingPlainLabels(mappingMissingReasons).join("、");
  if (!startReady) {
    return missingText
      ? `建图验收未就绪；还差：${missingText}；先连接上车状态机。`
      : "建图验收未就绪；还在等待上车状态机。";
  }
  return missingText
    ? `建图验收未就绪；还差：${missingText}；不影响先低速自由移动。`
    : "建图验收材料还在读取；不影响先低速自由移动。";
}

function freeRoamLatestMotionNextAction(startReady: boolean, motionReady: boolean, externalStopRequested: boolean): string {
  if (motionReady) {
    return "继续低速监看；需要停下时点停止。";
  }
  if (startReady) {
    return externalStopRequested
      ? "可直接先自由移动；开始时会先清除停止请求。"
      : "可直接先自由移动。";
  }
  return "先连接上车自由移动状态机，并确认停止兜底可用。";
}

function freeRoamLatestStartStatusPlain(startReady: boolean, motionReady: boolean, externalStopRequested: boolean): string {
  if (motionReady) {
    return "自由移动已启动；继续保持现场可接管，必要时点击停止。";
  }
  if (!startReady) {
    return "自由移动暂不可启动；先连接上车自由移动状态机并确认停止兜底。";
  }
  return externalStopRequested
    ? "自由移动可启动；点击开始会先清除停止请求，不作为启动阻塞。"
    : "自由移动可启动；现场默认安全，只保留停止兜底。";
}

function freeRoamLatestMotionRuntimeStatusPlain(startReady: boolean, motionReady: boolean): string {
  if (motionReady) {
    return "自由移动正在运行并发布低速运动；继续监看现场，必要时点击停止。";
  }
  if (startReady) {
    return "当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。";
  }
  return "当前未在自由移动运行态；上车自由移动状态机还未就绪。";
}

function freeRoamLatestMappingAcceptanceStatusPlain(startReady: boolean, mappingReady: boolean, mappingMissingReasons: string[]): string {
  if (mappingReady) {
    return "建图验收已就绪；画面、雷达、地图记录和地图画面已满足验收口径。";
  }
  const missingText = freeRoamLatestMissingPlainLabels(mappingMissingReasons).join("、");
  if (!startReady) {
    return missingText
      ? `建图验收未就绪；还差：${missingText}；同时自由移动状态机未就绪。`
      : "建图验收未就绪；还在等待自由移动状态机和建图材料。";
  }
  return missingText
    ? `建图验收未就绪；还差：${missingText}；这不阻止先低速自由移动。`
    : "建图验收未就绪；继续读取建图材料，这不阻止先低速自由移动。";
}

function freeRoamLatestMappingNextAction(startReady: boolean, mappingReady: boolean, mappingMissingReasons: string[]): string {
  if (mappingReady) {
    return "建图验收已就绪；继续低速监看地图、雷达和画面。";
  }
  const missingText = freeRoamLatestMissingPlainLabels(mappingMissingReasons).join("、");
  if (!startReady) {
    return missingText
      ? `先连接上车自由移动状态机；建图验收还差：${missingText}。`
      : "先连接上车自由移动状态机，并继续读取建图验收材料。";
  }
  return missingText
    ? `建图验收还差：${missingText}；不影响先低速自由移动。`
    : "继续读取建图验收材料；不影响先低速自由移动。";
}

function joinChinesePlainParts(...parts: string[]): string {
  // 中文白话字段直接顺接完整句，避免多余空格出现在普通首屏或现场脚本输出里。
  return parts.map((part) => part.trim()).filter(Boolean).join("");
}

function freeRoamLatestReadinessFromKeyValues(
  latestKeyValues: Record<string, string>,
  loaded: boolean,
): Pick<
  RobotControlFreeRoamAutonomyLatestResponse,
  | "runtime_status"
  | "decision_state"
  | "decision_reason"
  | "stop_request_pending"
  | "free_roam_stop_request_pending"
  | "start_will_clear_stop_request"
  | "start_clears_stop_request_not_blocking"
  | "motion_start_blocked_by_stop_request"
  | "stop_request_status_plain"
  | "safety_confirmed"
  | "plain_hint"
  | "next_action_plain"
  | "free_move_ready"
  | "free_move_start_ready"
  | "free_roam_motion_start_ready"
  | "motion_start_ready"
  | "free_roam_motion_ready"
  | "motion_ready"
  | "motion_without_radar_allowed"
  | "free_move_without_camera_allowed"
  | "free_roam_mapping_start_ready"
  | "mapping_start_ready"
  | "free_roam_mapping_start_missing_reasons"
  | "mapping_start_missing_reasons"
  | "free_roam_mapping_start_plain"
  | "free_roam_mapping_start_next_action"
  | "free_roam_mapping_ready"
  | "free_roam_mapping_missing_reasons"
  | "mapping_ready"
  | "mapping_missing_reasons"
  | "missing_capabilities"
  | "mapping_readiness_ready"
  | "mapping_blocked_reasons"
  | "motion_readiness_plain"
  | "free_move_start_status_plain"
  | "motion_runtime_status_plain"
  | "mapping_acceptance_status_plain"
  | "mapping_readiness_plain"
  | "motion_next_action_plain"
  | "mapping_next_action_plain"
> {
  const runtimeStatus = latestKeyValues.runtime_status ?? "not_loaded";
  const decisionState = latestKeyValues.decision_state ?? "not_loaded";
  const decisionReason = latestKeyValues.decision_reason ?? "not_loaded";
  const startReady = loaded && (latestKeyValues.free_roam_motion_start_ready === "true" || runtimeStatus === "loaded");
  const motionReady = startReady && latestKeyValues.cmd_vel_publish_enabled === "true";
  const mappingMissing = (latestKeyValues.mapping_missing ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item && item !== "none" && item !== "not_loaded");
  const mappingStartMissing = (latestKeyValues.mapping_start_missing ?? latestKeyValues.free_roam_mapping_start_missing_reasons ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item && item !== "none" && item !== "not_loaded");
  const mappingReady = startReady && (latestKeyValues.mapping_ready === "true" || mappingMissing.length === 0);
  const mappingStartReady = startReady && (latestKeyValues.mapping_start_ready === "true" || latestKeyValues.free_roam_mapping_start_ready === "true" || mappingStartMissing.length === 0);
  const externalStopRequested = latestKeyValues.external_stop_requested === "true"
    || (decisionState === "stopping" && /现场请求停止|external_stop/i.test(decisionReason));
  const safetyConfirmed = latestKeyValues.operator_confirmed === "true";
  const startStatusPlain = freeRoamLatestStartStatusPlain(startReady, motionReady, externalStopRequested);
  const mappingAcceptancePlain = freeRoamLatestMappingAcceptanceStatusPlain(startReady, mappingReady, mappingMissing);
  const motionNextActionPlain = freeRoamLatestMotionNextAction(startReady, motionReady, externalStopRequested);
  const mappingNextActionPlain = freeRoamLatestMappingNextAction(startReady, mappingReady, mappingMissing);
  const startWillClearStopRequest = startReady && externalStopRequested;
  const stopRequestStatusPlain = externalStopRequested
    ? startWillClearStopRequest
      ? "停止请求会在开始自由移动时自动解除，不作为启动阻塞。"
      : "当前有停止请求；先恢复自由移动启动条件，再清除停止请求。"
    : "当前没有停止请求。";
  return {
    runtime_status: runtimeStatus,
    decision_state: decisionState,
    decision_reason: decisionReason,
    stop_request_pending: externalStopRequested,
    free_roam_stop_request_pending: externalStopRequested,
    start_will_clear_stop_request: startWillClearStopRequest,
    start_clears_stop_request_not_blocking: startWillClearStopRequest,
    motion_start_blocked_by_stop_request: false,
    stop_request_status_plain: stopRequestStatusPlain,
    safety_confirmed: safetyConfirmed,
    // 顶层白话给现场脚本直接消费；细分字段仍保留给页面分区展示。
    plain_hint: joinChinesePlainParts(startStatusPlain, mappingAcceptancePlain),
    next_action_plain: joinChinesePlainParts(motionNextActionPlain, mappingNextActionPlain),
    free_move_ready: startReady,
    free_move_start_ready: startReady,
    free_roam_motion_start_ready: startReady,
    motion_start_ready: startReady,
    free_roam_motion_ready: motionReady,
    motion_ready: motionReady,
    motion_without_radar_allowed: latestKeyValues.motion_without_radar_allowed === "true" || startReady,
    free_move_without_camera_allowed: latestKeyValues.free_move_without_camera_allowed === "true" || startReady,
    free_roam_mapping_start_ready: mappingStartReady,
    mapping_start_ready: mappingStartReady,
    free_roam_mapping_start_missing_reasons: mappingStartMissing,
    mapping_start_missing_reasons: mappingStartMissing,
    free_roam_mapping_start_plain: latestKeyValues.free_roam_mapping_start_plain || freeRoamLatestMappingAcceptanceStatusPlain(startReady, mappingStartReady, mappingStartMissing),
    free_roam_mapping_start_next_action: latestKeyValues.free_roam_mapping_start_next_action || freeRoamLatestMappingNextAction(startReady, mappingStartReady, mappingStartMissing),
    free_roam_mapping_ready: mappingReady,
    free_roam_mapping_missing_reasons: mappingMissing,
    mapping_ready: mappingReady,
    mapping_missing_reasons: mappingMissing,
    missing_capabilities: mappingMissing,
    mapping_readiness_ready: mappingReady,
    mapping_blocked_reasons: mappingMissing,
    motion_readiness_plain: freeRoamLatestMotionReadinessPlain(startReady, motionReady, externalStopRequested),
    free_move_start_status_plain: startStatusPlain,
    motion_runtime_status_plain: freeRoamLatestMotionRuntimeStatusPlain(startReady, motionReady),
    mapping_acceptance_status_plain: mappingAcceptancePlain,
    mapping_readiness_plain: freeRoamLatestMappingReadinessPlain(startReady, mappingReady, mappingMissing),
    motion_next_action_plain: motionNextActionPlain,
    mapping_next_action_plain: mappingNextActionPlain,
  };
}

function unsafeProxyFailure(
  sourceBaseUrl: string,
  reason: string,
  remoteEndpoint: RobotControlCameraOfferProxyResponse["remote_endpoint"],
): RobotControlCameraOfferProxyResponse;
function unsafeProxyFailure(
  sourceBaseUrl: string,
  reason: string,
  remoteEndpoint: RobotControlCameraCloseProxyResponse["remote_endpoint"],
  peerId: string,
): RobotControlCameraCloseProxyResponse;
function unsafeProxyFailure(
  sourceBaseUrl: string,
  reason: string,
  remoteEndpoint: string,
  peerId = "",
): RobotControlCameraOfferProxyResponse | RobotControlCameraCloseProxyResponse {
  // URL/请求体验证失败时也返回固定 false 合同，避免前端为了错误态另写一套逻辑。
  const common = {
    source: "software_proof" as const,
    proof_status: "not_proven" as const,
    safe_to_control: false as const,
    delivery_success: false as const,
    primary_actions_enabled: false as const,
    pc_only: true as const,
    robot_control_executed: false as const,
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_http_status: null,
    blocked_reasons: [reason],
  };
  if (remoteEndpoint === "/api/camera/offer") {
    return {
      schema: "trashbot.pc_tools_workstation.robot_control_camera_offer_proxy.v1",
      proxy_status: "offer_rejected",
      remote_endpoint: "/api/camera/offer",
      status: "blocked",
      peer_id: "",
      answer: null,
      error: reason,
      failure_reason: reason,
      ...common,
    };
  }
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_close_proxy.v1",
    proxy_status: "close_rejected",
    remote_endpoint: "/api/camera/peers/{peer_id}/close",
    peer_id: peerId,
    status: "blocked",
    error: reason,
    failure_reason: reason,
    ...common,
  };
}

const CAMERA_FIRST_FRAME_PROBE_NO_MOTION_FLAGS = {
  // 首帧 probe 是固定诊断 POST：只读相机首帧证据，不抢占控制链路，也不启动运动或建图。
  readback_only: true,
  camera_probe_readback_only: true,
  sends_motion_when_clicked: false,
  starts_camera_exclusive_capture: false,
  starts_radar_lifecycle: false,
  starts_nav2: false,
  starts_manual: false,
  starts_keyboard: false,
  starts_free_roam: false,
  starts_map_runtime: false,
  submits_delivery: false,
  stops_motion: false,
} satisfies Pick<
  RobotControlCameraFirstFrameProbeProxyResponse,
  | "readback_only"
  | "camera_probe_readback_only"
  | "sends_motion_when_clicked"
  | "starts_camera_exclusive_capture"
  | "starts_radar_lifecycle"
  | "starts_nav2"
  | "starts_manual"
  | "starts_keyboard"
  | "starts_free_roam"
  | "starts_map_runtime"
  | "submits_delivery"
  | "stops_motion"
>;

const CAMERA_USB_RECOVERY_NO_MOTION_FLAGS = {
  // USB recovery 会短暂重启相机链路并做 STREAMON smoke；它仍绝不能触发任何底盘或 Nav2 行为。
  sends_motion_when_clicked: false,
  starts_radar_lifecycle: false,
  starts_nav2: false,
  starts_manual: false,
  starts_keyboard: false,
  starts_free_roam: false,
  starts_map_runtime: false,
  submits_delivery: false,
  stops_motion: false,
  publishes_cmd_vel: false,
  opens_base_uart: false,
  sends_motion_commands: false,
};

function safeCameraUsbRecoveryBody(value: unknown): Record<string, unknown> {
  // PC 只允许选择 videoN 和少量 skip 开关，避免浏览器 body 影响上车 root 命令。
  const body = asRecord(value);
  const rawDevice = typeof body?.device === "string" ? body.device : "/dev/video1";
  const device = /^\/dev\/video[0-9]{1,2}$/.test(rawDevice) ? rawDevice : "/dev/video1";
  return {
    device,
    skip_service: body?.skip_service === true,
    skip_reauthorize: body?.skip_reauthorize === true,
    skip_audio_unbind: body?.skip_audio_unbind === true,
  };
}

function cameraUsbRecoveryFailure(sourceBaseUrl: string, reason: string): Record<string, unknown> {
  // 本机拒绝时也返回完整 no-motion 边界，现场脚本不用猜这个 endpoint 是否会发车。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_usb_recovery_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    ...CAMERA_USB_RECOVERY_NO_MOTION_FLAGS,
    proxy_status: "recovery_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    workstation_endpoint: "/api/robot-control/camera/usb-recovery",
    remote_endpoint: "/api/camera/usb-recovery",
    remote_http_status: null,
    status: "blocked",
    frame_observed: false,
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function cameraProbeFailure(sourceBaseUrl: string, reason: string): RobotControlCameraFirstFrameProbeProxyResponse {
  // 本机拒绝或 fetch 失败也返回完整合同，避免高级诊断分叉成异常栈展示。
  const probeValues = cameraProbeKeyValues(null);
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    ...CAMERA_FIRST_FRAME_PROBE_NO_MOTION_FLAGS,
    proxy_status: "probe_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: "/api/camera/first-frame/probe",
    remote_http_status: null,
    status: "blocked",
    probe_key_values: probeValues,
    failure_reason: reason,
    blocked_reasons: [reason],
    ...cameraProbeDiagnosticAliases(probeValues, null),
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

async function fetchCameraProxySummary(
  baseUrl: string,
  endpoint: string,
  body: Record<string, unknown>,
  timeoutMs = 5000,
): Promise<{ remote_http_status: number | null; payload: Record<string, unknown> | null; error: string }> {
  // camera proxy 只向白名单 endpoint 发 POST JSON，不允许动态路径或浏览器跨域直连。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return { remote_http_status: null, payload: null, error: normalized.reason };
  }
  try {
    const response = await fetch(endpointUrl(normalized.normalized, endpoint), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    });
    const json = await response.json().catch(() => null);
    return {
      remote_http_status: response.status,
      payload: asRecord(json),
      error: "",
    };
  } catch (error) {
    if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
      return {
        remote_http_status: null,
        payload: null,
        error: `fetch_timeout_${timeoutMs}ms`,
      };
    }
    return {
      remote_http_status: null,
      payload: null,
      error: error instanceof Error ? shortText(error.message, "upper_api_unreachable") : "upper_api_unreachable",
    };
  }
}

function cameraMjpegRelayKey(normalizedBaseUrl: URL): string {
  // 共享 key 只取规范化后的 Robot API 根地址；query 不参与，避免同一相机被重复打开。
  return normalizedBaseUrl.toString().replace(/\/$/, "");
}

function cameraMjpegMultiViewerPlain(relayKey: string, clientCount: number): string {
  // 多页面共享能力来自 PC Node relay key：同一小车地址只维护一条上游 MJPEG，后进页面复用缓存和同流。
  const keyText = relayKey && relayKey !== "not_loaded" ? "同一小车地址" : "小车地址未生成";
  return `多人实时预览共用单条上游流；谁打开页面都接入同一个共享 relay（${keyText}），当前 ${clientCount} 个页面观看，不会因为新页面进入而独占摄像头。`;
}

function cameraProbeOverlayFromResponse(
  response: RobotControlCameraFirstFrameProbeProxyResponse,
): RobotControlCameraFirstFrameProbeOverlay {
  // summary 保留首帧和 backend smoke 短结论，普通首屏才能解释“不是浏览器独占，而是源头无帧”。
  return {
    checked_at_ms: Date.now(),
    proxy_status: response.proxy_status,
    status: response.status,
    failure_reason: response.failure_reason || response.probe_key_values.failure_reason || "none",
    open_ok: response.probe_key_values.open_ok,
    read_ok: response.probe_key_values.read_ok,
    visible_content_proven: response.probe_key_values.visible_content_proven,
    backend_smoke_status: response.probe_key_values.backend_smoke_status,
    backend_frame_observed: response.probe_key_values.backend_frame_observed,
    backend_attempts: response.probe_key_values.backend_attempts,
    streamon_io_error_observed: response.probe_key_values.streamon_io_error_observed,
    streamon_io_error_count: response.probe_key_values.streamon_io_error_count,
    latest_streamon_io_error: response.probe_key_values.latest_streamon_io_error,
    fallback_attempts_summary: response.probe_key_values.fallback_attempts_summary,
    low_bandwidth_fallback_attempted: response.probe_key_values.low_bandwidth_fallback_attempted,
    low_bandwidth_fallback_min_size: response.probe_key_values.low_bandwidth_fallback_min_size,
  };
}

function getCameraMjpegRelay(normalizedBaseUrl: URL): CameraMjpegRelay {
  const key = cameraMjpegRelayKey(normalizedBaseUrl);
  const existing = cameraMjpegRelays.get(key);
  if (existing) {
    return existing;
  }
  const relay: CameraMjpegRelay = {
    key,
    normalizedBaseUrl,
    clients: new Set(),
    controller: null,
    contentType: "",
    upstreamActive: false,
    latestFrameChunk: null,
    latestFrameUpdatedAtMs: null,
  };
  cameraMjpegRelays.set(key, relay);
  return relay;
}

function cameraMjpegStatusResponse(
  sourceBaseUrl: string,
  normalizedBaseUrl: URL | null,
  relay: CameraMjpegRelay | null,
  failureReason = "",
  sourceFailure: CameraMjpegRelayLastFailure | null = null,
): RobotControlCameraMjpegStatusResponse {
  // 这个端点只读本机 relay 状态，帮助现场判断多个 PC 页面是否共享同一个上游视频流。
  const relayKey = normalizedBaseUrl ? cameraMjpegRelayKey(normalizedBaseUrl) : "not_loaded";
  const relayFailure = normalizedBaseUrl ? cameraMjpegRelayLastFailures.get(relayKey) ?? null : null;
  const lastFailure = relayFailure ?? sourceFailure;
  // relay failure 说明共享 MJPEG 最近为什么失败；health 里的 source diagnosis 说明相机源为什么无帧，两者不能互相覆盖。
  const diagnosisSource = sourceFailure ?? relayFailure;
  const previewStatus = cameraMjpegPreviewStatus(relay, failureReason, lastFailure, diagnosisSource);
  const previewGuidance = cameraMjpegPreviewGuidance(previewStatus, diagnosisSource);
  const previewVisibility = cameraMjpegPreviewVisibility(previewStatus, previewGuidance);
  const clientCount = relay?.clients.size ?? 0;
  const upstreamActive = relay?.upstreamActive ?? false;
  const contentTypeLoaded = Boolean(relay?.contentType);
  const cachedFrameLoaded = Boolean(relay?.latestFrameChunk);
  const cachedFrameAgeMs = relay?.latestFrameUpdatedAtMs ? Math.max(0, Date.now() - relay.latestFrameUpdatedAtMs) : null;
  const lastFailureReason = lastFailure?.failure_reason ?? "";
  const lastRemoteHttpStatus = lastFailure?.remote_http_status ?? null;
  const lastFailureAtMs = lastFailure?.failed_at_ms ?? null;
  const sourceDiagnosisNextActionPlain = cameraMjpegActionPlainText(diagnosisSource?.source_diagnosis_next_action ?? "not_loaded")
    || previewGuidance.next_action_plain;
  const sourceReadiness = diagnosisSource?.source_readiness
    ?? (previewStatus === "source_first_frame_failed" ? "first_frame_failed" : "not_loaded");
  const sourceFailureReason = diagnosisSource?.source_failure_reason
    ?? (previewStatus === "source_first_frame_failed" ? lastFailureReason || "first_frame_failed" : "not_loaded");
  const lastErrorPayload = asRecord(lastFailure?.last_error_payload);
  const mjpegOpenSourceFallbackAttempted = Boolean(
    diagnosisSource?.mjpeg_open_source_fallback_attempted
      ?? lastErrorPayload?.mjpeg_open_source_fallback_attempted
      ?? false,
  );
  const openSourceFallbackFailureReason = shortText(
    diagnosisSource?.open_source_fallback_failure_reason
      ?? lastErrorPayload?.open_source_fallback_failure_reason,
    "not_loaded",
  );
  const primarySourceFailureReason = shortText(
    diagnosisSource?.primary_source_failure_reason
      ?? lastErrorPayload?.primary_source_failure_reason
      ?? sourceFailureReason,
    "not_loaded",
  );
  const sourceUsageScope = cameraSourceUsageScope(diagnosisSource?.source_usage_status, diagnosisSource?.source_usage_owner_count);
  const sourceUsageNotExclusive = cameraSourceUsageNotExclusive(sourceUsageScope);
  const cameraUsbSpeed = diagnosisSource?.uvc_usb_topology_video_usb_speed ?? "not_loaded";
  const cameraUsbFullSpeedDetected = cameraUsbSpeed === "12M"
    || diagnosisSource?.source_diagnosis_status === "uvc_full_speed_usb_not_exclusive"
    || diagnosisSource?.uvc_usb_topology_status === "uvc_video_on_full_speed_usb";
  const cameraCurrentVisible = previewVisibility.visible_status === "visible_cached_frame";
  const cameraTransportHardwareActionRequired = diagnosisSource?.source_diagnosis_status === "uvc_transport_error_not_exclusive";
  const cameraNoFrameHardwareActionRequired = diagnosisSource?.source_diagnosis_status === "uvc_no_frame_not_exclusive"
    && sourceUsageNotExclusive === "true";
  const cameraHardwareActionRequired = (
    cameraUsbFullSpeedDetected
    || cameraTransportHardwareActionRequired
    || cameraNoFrameHardwareActionRequired
  ) && !cameraCurrentVisible;
  const cameraHardwareActionLabel = cameraHardwareActionRequired
    ? cameraUsbFullSpeedDetected
      ? "换高速USB后复测"
      : cameraTransportHardwareActionRequired
        ? "检查USB/供电后复测"
        : "检查摄像头输入/供电后复测"
    : "复测相机首帧";
  const firstFrameProbeStatus = cameraCurrentVisible
    ? "frame_read"
    : sourceReadiness === "first_frame_failed" || previewStatus === "source_first_frame_failed"
      ? "source_first_frame_failed"
      : "not_loaded";
  const firstFrameFailureReason = firstFrameProbeStatus === "frame_read"
    ? "none"
    : sourceFailureReason !== "not_loaded"
      ? sourceFailureReason
      : primarySourceFailureReason !== "not_loaded"
        ? primarySourceFailureReason
        : lastFailureReason || "not_loaded";
  const sharedPreviewGapPlain = cameraCurrentVisible
    ? `共享预览已读到画面帧；当前 ${clientCount} 个页面共用同一条上游流，不会因为新页面进入而独占摄像头。`
    : `${previewVisibility.visible_plain.replace(/[。；\s]+$/g, "")}；共享入口可加入，但当前相机源还没有可显示帧。`;
  const cameraRecoverySequence = [
    "/api/robot-control/camera/first-frame/probe",
    "/api/robot-control/camera/mjpeg/status",
    "/api/robot-control/summary",
  ];
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_mjpeg_status.v1",
    proxy_status: failureReason ? "status_rejected" : "status_loaded",
    source_base_url: sourceBaseUrl,
    normalized_base_url: normalizedBaseUrl ? normalizedBaseUrl.toString().replace(/\/$/, "") : "not_loaded",
    workstation_endpoint: "/api/robot-control/camera/mjpeg/status",
    remote_endpoint: "/api/camera/mjpeg",
    relay_key: relayKey,
    client_count: clientCount,
    shared_preview_client_count: clientCount,
    viewer_count: clientCount,
    upstream_active: upstreamActive,
    shared_preview_upstream_active: upstreamActive,
    upstream_connected: upstreamActive,
    content_type_loaded: contentTypeLoaded,
    shared_preview_content_type_loaded: contentTypeLoaded,
    content_type: relay?.contentType ?? "",
    cached_frame_loaded: cachedFrameLoaded,
    shared_preview_cached_frame_loaded: cachedFrameLoaded,
    has_recent_frame: cachedFrameLoaded,
    cached_frame_age_ms: cachedFrameAgeMs,
    shared_preview_cached_frame_age_ms: cachedFrameAgeMs,
    shared_capture: true,
    shared_preview_shared_capture: true,
    exclusive_camera_claim: false,
    shared_preview_exclusive_camera_claim: false,
    shared_preview_contract: "single_shared_capture_for_multiple_clients",
    shared_preview_multi_viewer_status: "single_upstream_multi_viewer",
    shared_preview_multi_viewer_plain: cameraMjpegMultiViewerPlain(relayKey, clientCount),
    shared_preview_everyone_can_join: true,
    shared_preview_current_frame_visible: cameraCurrentVisible,
    shared_preview_gap_plain: sharedPreviewGapPlain,
    shared_preview_readback_only: true,
    shared_preview_starts_camera_exclusive_capture: false,
    shared_preview_sends_motion: false,
    shared_preview_starts_nav2: false,
    shared_preview_starts_manual: false,
    shared_preview_starts_keyboard: false,
    shared_preview_starts_free_roam: false,
    shared_preview_starts_map_runtime: false,
    shared_preview_submits_delivery: false,
    shared_preview_stops_motion: false,
    last_failure_reason: lastFailureReason,
    shared_preview_last_failure_reason: lastFailureReason,
    last_remote_http_status: lastRemoteHttpStatus,
    shared_preview_last_remote_http_status: lastRemoteHttpStatus,
    last_failure_at_ms: lastFailureAtMs,
    shared_preview_last_failure_at_ms: lastFailureAtMs,
    source_diagnosis_status: diagnosisSource?.source_diagnosis_status ?? "not_loaded",
    source_diagnosis_plain_hint: diagnosisSource?.source_diagnosis_plain_hint ?? "not_loaded",
    source_diagnosis_next_action: diagnosisSource?.source_diagnosis_next_action ?? "not_loaded",
    source_diagnosis_next_action_plain: sourceDiagnosisNextActionPlain,
    source_diagnosis_not_exclusive: diagnosisSource?.source_diagnosis_not_exclusive ?? "not_loaded",
    source_readiness: sourceReadiness,
    source_failure_reason: sourceFailureReason,
    last_first_frame_format_attempts_summary: diagnosisSource?.last_first_frame_format_attempts_summary ?? "none",
    mjpeg_open_source_fallback_attempted: mjpegOpenSourceFallbackAttempted,
    open_source_fallback_failure_reason: openSourceFallbackFailureReason,
    primary_source_failure_reason: primarySourceFailureReason,
    selected_path: diagnosisSource?.selected_path ?? "not_loaded",
    selected_name: diagnosisSource?.selected_name ?? "not_loaded",
    selected_device: diagnosisSource?.selected_path ?? "not_loaded",
    selected_device_label: diagnosisSource?.selected_name ?? "not_loaded",
    selected_is_uvc_or_usb: diagnosisSource?.selected_is_uvc_or_usb ?? "not_loaded",
    source_usage_status: diagnosisSource?.source_usage_status ?? "not_loaded",
    source_usage_owner_count: diagnosisSource?.source_usage_owner_count ?? "not_loaded",
    source_usage_scope: sourceUsageScope,
    source_usage_not_exclusive: sourceUsageNotExclusive,
    uvc_usb_topology_status: diagnosisSource?.uvc_usb_topology_status ?? "not_loaded",
    uvc_usb_topology_plain_hint: diagnosisSource?.uvc_usb_topology_plain_hint ?? "not_loaded",
    uvc_usb_topology_next_action: diagnosisSource?.uvc_usb_topology_next_action ?? "not_loaded",
    uvc_usb_topology_video_usb_speed: cameraUsbSpeed,
    uvc_usb_topology_kernel_usb_address: diagnosisSource?.uvc_usb_topology_kernel_usb_address ?? "not_loaded",
    uvc_usb_topology_video_interface_count: diagnosisSource?.uvc_usb_topology_video_interface_count ?? "not_loaded",
    camera_usb_speed: cameraUsbSpeed,
    camera_usb_full_speed_detected: cameraUsbFullSpeedDetected,
    camera_hardware_action_required: cameraHardwareActionRequired,
    camera_hardware_action_label: cameraHardwareActionLabel,
    usb_speed: cameraUsbSpeed,
    usb_full_speed_detected: cameraUsbFullSpeedDetected,
    hardware_action_required: cameraHardwareActionRequired,
    hardware_action_label: cameraHardwareActionLabel,
    first_frame_probe_status: firstFrameProbeStatus,
    first_frame_probe_failure_reason: firstFrameFailureReason,
    first_frame_failure_reason: firstFrameFailureReason,
    camera_first_frame_probe_status: firstFrameProbeStatus,
    camera_first_frame_failure_reason: firstFrameFailureReason,
    camera_blocks_mapping_start: !cameraCurrentVisible,
    camera_blocks_free_move: false,
    camera_reprobe_after_hardware_action_required: cameraHardwareActionRequired,
    camera_reprobe_sequence: cameraRecoverySequence,
    fixed_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe",
    fixed_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status",
    fixed_summary_endpoint: "/api/robot-control/summary",
    camera_recovery_sends_motion: false,
    camera_recovery_starts_map_runtime: false,
    // MJPEG status 只读本机共享预览和上车 health，不创建独占采集，也不触发任何运动链路。
    readback_only: true,
    camera_status_readback_only: true,
    camera_mjpeg_status_readback_only: true,
    sends_motion_when_clicked: false,
    starts_camera_exclusive_capture: false,
    starts_radar_lifecycle: false,
    starts_nav2: false,
    starts_manual: false,
    starts_keyboard: false,
    starts_free_roam: false,
    starts_map_runtime: false,
    submits_delivery: false,
    stops_motion: false,
    // status/plain_hint 是 preview_* 的顶层别名，方便现场脚本直接读共享画面是否可见。
    status: previewStatus,
    plain_hint: previewGuidance.plain_hint,
    next_action_plain: previewGuidance.next_action_plain,
    preview_status: previewStatus,
    preview_plain_hint: previewGuidance.plain_hint,
    preview_next_action: previewGuidance.next_action,
    preview_next_action_plain: previewGuidance.next_action_plain,
    preview_visible_status: previewVisibility.visible_status,
    preview_visible_plain: previewVisibility.visible_plain,
    camera_wysiwyg_status_plain: previewVisibility.wysiwyg_status_plain,
    camera_wysiwyg_next_action_plain: previewVisibility.wysiwyg_next_action_plain,
    failure_reason: failureReason,
    blocked_reasons: failureReason ? [failureReason] : [],
    // 相机共享预览状态是纯读回端点，显式给脚本一个空数组，避免 jq 读到 null 后误判为合同缺失。
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
    ...PROOF_FLAGS,
  };
}

function cameraMjpegPreviewVisibility(
  previewStatus: RobotControlCameraMjpegStatusResponse["preview_status"],
  previewGuidance: { plain_hint: string; next_action_plain: string },
): {
  visible_status: string;
  visible_plain: string;
  wysiwyg_status_plain: string;
  wysiwyg_next_action_plain: string;
} {
  // 共享 relay 的连接状态不等于画面已经可见；status 端点也要直接返回所见即所得结论。
  if (previewStatus === "streaming") {
    return {
      visible_status: "visible_cached_frame",
      visible_plain: "当前有共享实时画面缓存帧；新页面复用同一条上游流。",
      wysiwyg_status_plain: "画面已可见：共享实时画面已有缓存帧，多个页面复用同一条上游流。",
      wysiwyg_next_action_plain: "继续监看共享实时画面。",
    };
  }
  if (previewStatus === "source_first_frame_failed") {
    return {
      visible_status: "not_visible_source_first_frame_failed",
      visible_plain: `当前没有实时画面；${previewGuidance.plain_hint}`,
      wysiwyg_status_plain: `画面未可见：${previewGuidance.plain_hint}`,
      wysiwyg_next_action_plain: previewGuidance.next_action_plain,
    };
  }
  if (previewStatus === "waiting_for_first_frame") {
    return {
      visible_status: "not_visible_waiting_for_first_frame",
      visible_plain: `当前没有实时画面；${previewGuidance.plain_hint}`,
      wysiwyg_status_plain: `画面未可见：${previewGuidance.plain_hint}`,
      wysiwyg_next_action_plain: previewGuidance.next_action_plain,
    };
  }
  if (previewStatus === "blocked") {
    return {
      visible_status: "not_visible_blocked",
      visible_plain: `当前没有实时画面；${previewGuidance.plain_hint}`,
      wysiwyg_status_plain: `画面未可见：${previewGuidance.plain_hint}`,
      wysiwyg_next_action_plain: previewGuidance.next_action_plain,
    };
  }
  return {
    visible_status: "not_visible_idle",
    visible_plain: `当前没有实时画面；${previewGuidance.plain_hint}`,
    wysiwyg_status_plain: `画面未可见：${previewGuidance.plain_hint}`,
    wysiwyg_next_action_plain: previewGuidance.next_action_plain,
  };
}

function cameraMjpegPreviewStatus(
  relay: CameraMjpegRelay | null,
  failureReason: string,
  lastFailure: CameraMjpegRelayLastFailure | null,
  diagnosisSource: CameraMjpegRelayLastFailure | null,
): RobotControlCameraMjpegStatusResponse["preview_status"] {
  // 这个状态只解释 PC 共享预览现状；不能把“入口可打开”误写成“画面已经可见”。
  if (failureReason) {
    return "blocked";
  }
  if (relay?.latestFrameChunk) {
    return "streaming";
  }
  const sourceFirstFrameFailed = lastFailure?.failure_reason === "camera_source_first_frame_failed"
    || diagnosisSource?.source_readiness === "first_frame_failed"
    || CAMERA_FIRST_FRAME_FAILURE_REASONS.has(diagnosisSource?.source_failure_reason ?? "")
    || diagnosisSource?.source_diagnosis_status === "uvc_no_frame_not_exclusive"
    || diagnosisSource?.source_diagnosis_status === "uvc_transport_error_not_exclusive"
    || diagnosisSource?.source_diagnosis_status === "uvc_full_speed_usb_not_exclusive";
  if (sourceFirstFrameFailed) {
    return "source_first_frame_failed";
  }
  if ((relay?.clients.size ?? 0) > 0 || relay?.upstreamActive) {
    return "waiting_for_first_frame";
  }
  return "idle_not_started";
}

function cameraMjpegPreviewGuidance(
  previewStatus: RobotControlCameraMjpegStatusResponse["preview_status"],
  diagnosisSource: CameraMjpegRelayLastFailure | null,
): { plain_hint: string; next_action: string; next_action_plain: string } {
  // 普通用户只需要看到“现在有没有实时画面”和下一步；完整诊断字段仍保留给高级区。
  if (previewStatus === "streaming") {
    return {
      plain_hint: "共享实时画面已有缓存帧，多个页面复用同一条上游流。",
      next_action: "continue_monitoring_shared_preview",
      next_action_plain: "继续监看共享实时画面。",
    };
  }
  if (previewStatus === "source_first_frame_failed") {
    const nextAction = diagnosisSource?.source_diagnosis_next_action ?? "check_usb_camera_input_power_or_known_good_uvc";
    return {
      plain_hint: diagnosisSource?.source_diagnosis_plain_hint ?? "不是页面独占：UVC 设备没有输出视频帧。",
      next_action: nextAction,
      next_action_plain: cameraMjpegActionPlainText(nextAction),
    };
  }
  if (previewStatus === "waiting_for_first_frame") {
    return {
      plain_hint: "共享实时画面正在等待首帧；返回前不能把黑框当作画面可见。",
      next_action: "wait_or_run_first_frame_probe",
      next_action_plain: "等待首帧，必要时点只读检查复测画面。",
    };
  }
  if (previewStatus === "blocked") {
    return {
      plain_hint: "共享实时画面状态读取被本机拒绝或失败。",
      next_action: "check_robot_api_base_url_and_retry",
      next_action_plain: "确认小车地址可访问后重试共享预览状态。",
    };
  }
  return {
    plain_hint: "页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。",
    next_action: "auto_join_shared_mjpeg_preview",
    next_action_plain: "打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。",
  };
}

function cameraMjpegActionPlainText(action: string): string {
  // MJPEG status 是很多页面共享的入口；除了 token，也给现场人员能直接执行的下一步。
  const value = action.trim();
  if (!value || value === "not_loaded" || value === "none") {
    return "";
  }
  const normalized = value.replace(/\s+/g, "_").toLowerCase();
  if (normalized === "check_usb_camera_input_power_or_known_good_uvc") {
    return "检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。";
  }
  if (normalized === "check_usb_cable_port_power_or_known_good_uvc") {
    return "检查 USB 线、接口和摄像头供电，必要时换 known-good UVC 复测；共享预览不是页面独占。";
  }
  if (normalized === "move_camera_to_high_speed_usb_port_or_powered_hub") {
    return "摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。";
  }
  if (normalized === "continue_monitoring_shared_preview") {
    return "继续监看共享实时画面。";
  }
  if (normalized === "open_shared_preview") {
    return "打开共享实时预览；页面会复用同一条上游流。";
  }
  if (normalized === "auto_join_shared_mjpeg_preview") {
    return "打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。";
  }
  if (normalized === "open_shared_preview_when_needed" || normalized === "open_shared_preview_or_run_first_frame_probe") {
    return "需要看画面时打开共享预览，或点只读检查复测首帧。";
  }
  if (normalized === "wait_or_run_first_frame_probe") {
    return "等待首帧，必要时点只读检查复测画面。";
  }
  if (normalized === "check_robot_api_base_url_and_retry") {
    return "确认小车地址可访问后重试共享预览状态。";
  }
  return `${value.replace(/_/g, " ")}。`;
}

async function cameraSourceFirstFrameFailureForStatus(
  normalizedBaseUrl: URL,
  timeoutMs = ROBOT_CONTROL_CAMERA_HEALTH_TIMEOUT_MS,
): Promise<CameraMjpegRelayLastFailure | null> {
  // status 端点不创建 MJPEG client；只读 health，并与 summary 共享 camera 读取预算，避免慢 health 丢掉“不是独占”的现场诊断。
  try {
    const response = await fetch(endpointUrl(normalizedBaseUrl, "/api/camera/health"), {
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!response.ok) {
      return null;
    }
    const payload = asRecord(await response.json().catch(() => null));
    const status = shortText(payload?.status, "");
    const readiness = shortText(payload?.source_readiness, "");
    const reason = shortText(payload?.source_failure_reason, "");
    const lastOffer = asRecord(asRecord(payload?.media_diagnostics)?.last_offer_error);
    const lastOfferReason = shortText(lastOffer?.failure_reason, "");
    const sourceDiagnosis = asRecord(payload?.source_diagnosis)
      ?? asRecord(asRecord(payload?.media_diagnostics)?.source_diagnosis);
    const sourceUsage = asRecord(payload?.source_usage)
      ?? asRecord(asRecord(payload?.media_diagnostics)?.source_usage);
    const uvcUsbTopology = asRecord(payload?.uvc_usb_topology)
      ?? asRecord(asRecord(payload?.media_diagnostics)?.uvc_usb_topology)
      ?? asRecord(sourceDiagnosis?.uvc_usb_topology);
    const currentSelection = asRecord(payload?.current_selection);
    const selectedName = cameraSourceDisplayName(
      payload?.selected_name
        ?? asRecord(payload?.source_summary)?.selected_name
        ?? currentSelection?.selected_name
        ?? sourceDiagnosis?.selected_name,
      "USB 摄像头",
    );
    const selectedPath = shortText(
      payload?.selected_path
        ?? currentSelection?.selected_path
        ?? sourceDiagnosis?.selected_path
        ?? sourceUsage?.device
        ?? payload?.video_source,
      "not_loaded",
    );
    const selectedIsUvcOrUsb = String(
      currentSelection?.selected_is_uvc_or_usb
        ?? sourceDiagnosis?.selected_is_uvc_or_usb
        ?? "not_loaded",
    );
    const diagnosisStatus = shortText(sourceDiagnosis?.status, "");
    const diagnosisPlainHint = cameraDiagnosisPlainHint(sourceDiagnosis?.plain_hint, selectedName);
    const diagnosisNextAction = shortText(sourceDiagnosis?.next_action, "");
    const rawDiagnosisNotExclusive = sourceDiagnosis?.not_exclusive === undefined
      ? "not_loaded"
      : String(sourceDiagnosis.not_exclusive);
    const lastError = asRecord(payload?.last_first_frame_error) ?? lastOffer;
    const mjpegOpenSourceFallbackAttempted = Boolean(
      payload?.mjpeg_open_source_fallback_attempted
        ?? lastError?.mjpeg_open_source_fallback_attempted
        ?? false,
    );
    const openSourceFallbackFailureReason = shortText(
      payload?.open_source_fallback_failure_reason
        ?? lastError?.open_source_fallback_failure_reason,
      "not_loaded",
    );
    const primarySourceFailureReason = shortText(
      payload?.primary_source_failure_reason
        ?? lastError?.primary_source_failure_reason
        ?? reason
        ?? lastOfferReason,
      "not_loaded",
    );
    const firstFrameFailed = status === "source_first_frame_failed"
      || readiness === "first_frame_failed"
      || CAMERA_FIRST_FRAME_FAILURE_REASONS.has(reason)
      || CAMERA_FIRST_FRAME_FAILURE_REASONS.has(lastOfferReason);
    const sourceUsageStatus = shortText(sourceUsage?.status, "");
    const sourceUsageOwnerCount = sourceUsage?.owner_count === undefined ? "not_loaded" : String(sourceUsage.owner_count);
    const sourceUsageScope = cameraSourceUsageScope(sourceUsageStatus, sourceUsageOwnerCount);
    const sourceUsageNotExclusive = cameraSourceUsageNotExclusive(sourceUsageScope);
    const canExplainNoFrameAsNotExclusive = firstFrameFailed && sourceUsageNotExclusive === "true" && rawDiagnosisNotExclusive !== "true";
    const resolvedDiagnosisStatus = canExplainNoFrameAsNotExclusive && diagnosisStatus !== "uvc_no_frame_not_exclusive"
      ? "uvc_no_frame_not_exclusive"
      : diagnosisStatus;
    const resolvedDiagnosisPlainHint = canExplainNoFrameAsNotExclusive && (!diagnosisPlainHint || !diagnosisPlainHint.includes("不是页面独占"))
      ? sourceUsageScope === "camera_service_self"
        ? `不是页面独占：相机服务正在用单上游共享预览读取 ${selectedName}，但 UVC 设备没有输出视频帧。`
        : `不是页面独占：${cameraOwnerFreeText(selectedName)}，但 UVC 设备没有输出视频帧。`
      : diagnosisPlainHint;
    const resolvedDiagnosisNextAction = canExplainNoFrameAsNotExclusive
      ? "check_usb_camera_input_power_or_known_good_uvc"
      : diagnosisNextAction;
    const resolvedDiagnosisNotExclusive = canExplainNoFrameAsNotExclusive ? "true" : rawDiagnosisNotExclusive;
    const usbTopologyFields = {
      uvc_usb_topology_status: shortText(uvcUsbTopology?.status ?? sourceDiagnosis?.uvc_usb_topology_status, "not_loaded"),
      uvc_usb_topology_plain_hint: shortText(uvcUsbTopology?.plain_hint ?? sourceDiagnosis?.uvc_usb_topology_plain_hint, "not_loaded"),
      uvc_usb_topology_next_action: shortText(uvcUsbTopology?.next_action ?? sourceDiagnosis?.uvc_usb_topology_next_action, "not_loaded"),
      uvc_usb_topology_video_usb_speed: shortText(uvcUsbTopology?.video_usb_speed ?? sourceDiagnosis?.uvc_usb_topology_video_usb_speed, "not_loaded"),
      uvc_usb_topology_kernel_usb_address: shortText(uvcUsbTopology?.kernel_usb_address ?? sourceDiagnosis?.uvc_usb_topology_kernel_usb_address, "not_loaded"),
      uvc_usb_topology_video_interface_count: shortText(uvcUsbTopology?.video_interface_count ?? sourceDiagnosis?.uvc_usb_topology_video_interface_count, "not_loaded"),
    };
    const sourceSelectedNotProbed = status === "source_not_probed" || readiness === "source_selected_not_probed";
    const hasUsefulSourceDiagnosis = Boolean(
      diagnosisStatus && diagnosisStatus !== "not_loaded" && diagnosisStatus !== "none",
    );
    if (!firstFrameFailed) {
      if (!hasUsefulSourceDiagnosis && !sourceSelectedNotProbed) {
        return null;
      }
      return {
        failure_reason: "",
        remote_http_status: response.status,
        failed_at_ms: null,
        source_diagnosis_status: resolvedDiagnosisStatus || readiness || status || "not_loaded",
        source_diagnosis_plain_hint: resolvedDiagnosisPlainHint || "相机源已选中但还没读过首帧；打开共享预览或运行首帧检查。",
        source_diagnosis_next_action: resolvedDiagnosisNextAction || "open_shared_preview_or_run_first_frame_probe",
        source_diagnosis_not_exclusive: resolvedDiagnosisNotExclusive,
        source_readiness: readiness || (sourceSelectedNotProbed ? "source_selected_not_probed" : "not_loaded"),
        source_failure_reason: reason || "none",
        selected_path: selectedPath,
        selected_name: selectedName,
        selected_is_uvc_or_usb: selectedIsUvcOrUsb,
        source_usage_status: sourceUsageStatus || "not_loaded",
        source_usage_owner_count: sourceUsageOwnerCount,
        source_usage_scope: sourceUsageScope,
        source_usage_not_exclusive: sourceUsageNotExclusive,
        ...usbTopologyFields,
        last_first_frame_format_attempts_summary: cameraMjpegFormatAttemptsSummary(payload),
        mjpeg_open_source_fallback_attempted: mjpegOpenSourceFallbackAttempted,
        open_source_fallback_failure_reason: openSourceFallbackFailureReason,
        primary_source_failure_reason: primarySourceFailureReason,
      };
    }
    return {
      failure_reason: "camera_source_first_frame_failed",
      remote_http_status: response.status,
      failed_at_ms: Date.now(),
      source_diagnosis_status: resolvedDiagnosisStatus || "not_loaded",
      source_diagnosis_plain_hint: resolvedDiagnosisPlainHint || "not_loaded",
      source_diagnosis_next_action: resolvedDiagnosisNextAction || "not_loaded",
      source_diagnosis_not_exclusive: resolvedDiagnosisNotExclusive,
      source_readiness: "first_frame_failed",
      source_failure_reason: reason || lastOfferReason || "first_frame_failed",
      selected_path: selectedPath,
      selected_name: selectedName,
      selected_is_uvc_or_usb: selectedIsUvcOrUsb,
      source_usage_status: sourceUsageStatus || "not_loaded",
      source_usage_owner_count: sourceUsageOwnerCount,
      source_usage_scope: sourceUsageScope,
      source_usage_not_exclusive: sourceUsageNotExclusive,
      ...usbTopologyFields,
      last_first_frame_format_attempts_summary: cameraMjpegFormatAttemptsSummary(payload),
      mjpeg_open_source_fallback_attempted: mjpegOpenSourceFallbackAttempted,
      open_source_fallback_failure_reason: openSourceFallbackFailureReason,
      primary_source_failure_reason: primarySourceFailureReason,
    };
  } catch {
    return null;
  }
}

async function buildRobotControlSummaryForHttp(
  sourceBaseUrl: string,
  options: { keyboardEvidence?: RobotControlKeyboardLocalEvidence } = {},
): Promise<RobotControlSummaryResponse> {
  // summary 与 live-summary 共用同一份只读 overlay，避免两个现场入口对相机/共享预览状态说法不一致。
  const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
  const relayKey = normalized.ok ? cameraMjpegRelayKey(normalized.normalized) : "";
  const firstFrameOverlay = normalized.ok
    ? cameraFirstFrameProbeOverlays.get(relayKey) ?? null
    : null;
  const relay = normalized.ok ? cameraMjpegRelays.get(relayKey) ?? null : null;
  const lastFailure = normalized.ok ? cameraMjpegRelayLastFailures.get(relayKey) ?? null : null;
  const sourceFailure = normalized.ok
    ? await cameraSourceFirstFrameFailureForStatus(normalized.normalized, ROBOT_CONTROL_SUMMARY_CAMERA_OVERLAY_TIMEOUT_MS)
    : null;
  const lastFailureForOverlay = lastFailure ?? sourceFailure;
  const mjpegRelayOverlay: RobotControlCameraMjpegRelayOverlay | null = relay
    ? {
      relay_key: relayKey,
      client_count: relay.clients.size,
      upstream_active: relay.upstreamActive,
      content_type_loaded: Boolean(relay.contentType),
      cached_frame_loaded: Boolean(relay.latestFrameChunk),
      cached_frame_age_ms: relay.latestFrameUpdatedAtMs ? Math.max(0, Date.now() - relay.latestFrameUpdatedAtMs) : null,
      shared_capture: true,
      exclusive_camera_claim: false,
      last_failure_reason: lastFailureForOverlay?.failure_reason ?? "",
      last_remote_http_status: lastFailureForOverlay?.remote_http_status ?? null,
      last_failure_at_ms: lastFailureForOverlay?.failed_at_ms ?? null,
      source_diagnosis_status: lastFailureForOverlay?.source_diagnosis_status,
      source_diagnosis_plain_hint: lastFailureForOverlay?.source_diagnosis_plain_hint,
      source_diagnosis_next_action: lastFailureForOverlay?.source_diagnosis_next_action,
      source_diagnosis_not_exclusive: lastFailureForOverlay?.source_diagnosis_not_exclusive,
      source_readiness: lastFailureForOverlay?.source_readiness,
      source_failure_reason: lastFailureForOverlay?.source_failure_reason,
      selected_path: lastFailureForOverlay?.selected_path,
      selected_name: lastFailureForOverlay?.selected_name,
      selected_is_uvc_or_usb: lastFailureForOverlay?.selected_is_uvc_or_usb,
      source_usage_status: lastFailureForOverlay?.source_usage_status,
      source_usage_owner_count: lastFailureForOverlay?.source_usage_owner_count,
      last_error_payload: lastFailureForOverlay?.last_error_payload ?? null,
    }
    : lastFailureForOverlay
      ? {
        relay_key: relayKey,
        client_count: 0,
        upstream_active: false,
        content_type_loaded: false,
        cached_frame_loaded: false,
        cached_frame_age_ms: null,
        shared_capture: true,
        exclusive_camera_claim: false,
        last_failure_reason: lastFailureForOverlay.failure_reason,
        last_remote_http_status: lastFailureForOverlay.remote_http_status,
        last_failure_at_ms: lastFailureForOverlay.failed_at_ms,
        source_diagnosis_status: lastFailureForOverlay.source_diagnosis_status,
        source_diagnosis_plain_hint: lastFailureForOverlay.source_diagnosis_plain_hint,
        source_diagnosis_next_action: lastFailureForOverlay.source_diagnosis_next_action,
        source_diagnosis_not_exclusive: lastFailureForOverlay.source_diagnosis_not_exclusive,
        source_readiness: lastFailureForOverlay.source_readiness,
        source_failure_reason: lastFailureForOverlay.source_failure_reason,
        selected_path: lastFailureForOverlay.selected_path,
        selected_name: lastFailureForOverlay.selected_name,
        selected_is_uvc_or_usb: lastFailureForOverlay.selected_is_uvc_or_usb,
        source_usage_status: lastFailureForOverlay.source_usage_status,
        source_usage_owner_count: lastFailureForOverlay.source_usage_owner_count,
        last_error_payload: lastFailureForOverlay.last_error_payload ?? null,
      }
      : null;
  // HTTP 首屏固定快预算；慢 wheel L/R 证据由内部 builder/独立刷新读取，不能拖慢普通用户首屏。
  return buildRobotControlSummary(sourceBaseUrl, firstFrameOverlay, mjpegRelayOverlay, {
    readbackTimeoutMs: ROBOT_CONTROL_SUMMARY_HTTP_READBACK_TIMEOUT_MS,
    keyboardEvidence: options.keyboardEvidence,
  });
}

function buildRobotControlLiveSummaryResponse(summary: RobotControlSummaryResponse): RobotControlLiveSummaryResponse {
  // 扁平 live-summary 是给现场 curl/jq 用的只读视图；权威数据仍来自同一次 summary 聚合。
  return {
    ...(summary.live_closure_summary as NonNullable<RobotControlSummaryResponse["live_closure_summary"]>),
    schema: "trashbot.pc_tools_workstation.robot_control_live_summary.v1",
    console_status: summary.console_status,
    source_base_url: summary.source_base_url,
    normalized_base_url: summary.normalized_base_url,
    observed_at_ms: summary.observed_at_ms,
    workstation_endpoint: "/api/robot-control/live-summary",
    summary_endpoint: "/api/robot-control/summary",
    // 现场脚本常只读 live-summary；现场验收包也透到这里，避免再钻 summary.field_acceptance_packet。
    field_acceptance_packet: summary.field_acceptance_packet,
    field_acceptance_status: summary.field_acceptance_status,
    field_acceptance_next_step_id: summary.field_acceptance_next_step_id,
    field_acceptance_next_step_label: summary.field_acceptance_next_step_label,
    field_acceptance_next_step_start_endpoint: summary.field_acceptance_next_step_start_endpoint,
    field_acceptance_next_step_sends_motion: summary.field_acceptance_next_step_sends_motion,
    field_acceptance_next_step_requires_safety_confirm: summary.field_acceptance_next_step_requires_safety_confirm,
    field_acceptance_ready_step_ids: summary.field_acceptance_ready_step_ids,
    field_acceptance_blocked_step_ids: summary.field_acceptance_blocked_step_ids,
    field_acceptance_motion_step_ids: summary.field_acceptance_motion_step_ids,
    field_acceptance_no_motion_step_ids: summary.field_acceptance_no_motion_step_ids,
    field_acceptance_acceptance_endpoints: summary.field_acceptance_acceptance_endpoints,
    field_acceptance_safety_confirm_required: summary.field_acceptance_safety_confirm_required,
    field_acceptance_minimal_precheck_safety_only: summary.field_acceptance_minimal_precheck_safety_only,
    field_acceptance_summary_plain: summary.field_acceptance_summary_plain,
    field_acceptance_wysiwyg_ready: summary.field_acceptance_wysiwyg_ready,
    field_acceptance_wysiwyg_missing_surface_ids: summary.field_acceptance_wysiwyg_missing_surface_ids,
    field_acceptance_wysiwyg_primary_refresh_endpoint: summary.field_acceptance_wysiwyg_primary_refresh_endpoint,
    field_acceptance_wysiwyg_primary_refresh_label: summary.field_acceptance_wysiwyg_primary_refresh_label,
    field_acceptance_wysiwyg_next_action_plain: summary.field_acceptance_wysiwyg_next_action_plain,
    field_acceptance_wysiwyg_camera_next_action_plain: summary.field_acceptance_wysiwyg_camera_next_action_plain,
    field_acceptance_wysiwyg_radar_map_next_action_plain: summary.field_acceptance_wysiwyg_radar_map_next_action_plain,
    field_acceptance_wysiwyg_refresh_sequence: summary.field_acceptance_wysiwyg_refresh_sequence,
    field_acceptance_wysiwyg_refresh_sequence_labels: summary.field_acceptance_wysiwyg_refresh_sequence_labels,
    field_acceptance_wysiwyg_refresh_mode: summary.field_acceptance_wysiwyg_refresh_mode,
    field_acceptance_wysiwyg_refresh_sends_motion: summary.field_acceptance_wysiwyg_refresh_sends_motion,
    field_acceptance_wysiwyg_refresh_starts_nav2: summary.field_acceptance_wysiwyg_refresh_starts_nav2,
    field_acceptance_wysiwyg_refresh_starts_manual: summary.field_acceptance_wysiwyg_refresh_starts_manual,
    field_acceptance_wysiwyg_refresh_starts_keyboard: summary.field_acceptance_wysiwyg_refresh_starts_keyboard,
    field_acceptance_wysiwyg_refresh_starts_free_roam: summary.field_acceptance_wysiwyg_refresh_starts_free_roam,
    field_acceptance_wysiwyg_refresh_starts_radar_lifecycle: summary.field_acceptance_wysiwyg_refresh_starts_radar_lifecycle,
    field_acceptance_wysiwyg_refresh_starts_map_runtime: summary.field_acceptance_wysiwyg_refresh_starts_map_runtime,
    field_acceptance_wysiwyg_refresh_submits_delivery: summary.field_acceptance_wysiwyg_refresh_submits_delivery,
    field_acceptance_wysiwyg_refresh_stops_motion: summary.field_acceptance_wysiwyg_refresh_stops_motion,
    field_acceptance_steps: summary.field_acceptance_steps,
    nav2_route_acceptance_packet: summary.nav2_route_acceptance_packet,
    map_preview_status: summary.readback_summary.map.status,
    path_preview_point_count: summary.readback_summary.map.path_preview_point_count,
    route_target_visible: summary.readback_summary.map.route_target_visible,
    route_target_source: summary.readback_summary.map.route_target_source,
    route_target_state: summary.readback_summary.map.route_target_state,
    readback_only: true,
    sends_motion_when_clicked: false,
    starts_nav2: false,
    starts_manual: false,
    starts_keyboard: false,
    starts_free_roam: false,
    starts_map_runtime: false,
    submits_delivery: false,
    stops_motion: false,
    publishes_cmd_vel: false,
    robot_control_executed: false,
  };
}

function startCameraMjpegClient(client: CameraMjpegRelayClient, contentType: string): void {
  // 浏览器端只能看到只读 multipart 流；这里不透传上位机控制字段。
  if (client.headersStarted || client.response.headersSent) {
    client.headersStarted = true;
    return;
  }
  client.response.status(200);
  client.response.setHeader("Content-Type", contentType);
  client.response.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
  client.response.setHeader("X-Robber-Proxy", "camera-mjpeg-shared-readonly");
  client.response.setHeader("X-Robber-Camera-Shared-Capture", "single_shared_capture_for_multiple_clients");
  client.response.setHeader("X-Robber-Camera-Exclusive-Claim", "false");
  client.response.flushHeaders?.();
  client.headersStarted = true;
}

function writeCachedCameraMjpegFrame(relay: CameraMjpegRelay, client: CameraMjpegRelayClient): void {
  // 后进页面先收到最近一帧，再继续跟随实时流；这不会新开相机 reader，也不改变上车端占用。
  if (!relay.latestFrameChunk || client.response.destroyed) {
    return;
  }
  try {
    startCameraMjpegClient(client, relay.contentType);
    client.response.write(relay.latestFrameChunk);
  } catch {
    removeCameraMjpegClient(relay, client);
  }
}

function removeCameraMjpegClient(relay: CameraMjpegRelay, client: CameraMjpegRelayClient): void {
  relay.clients.delete(client);
  if (relay.clients.size === 0) {
    // 没有人观看时释放唯一上游连接，避免长期占用摄像头 reader。
    relay.controller?.abort();
    relay.controller = null;
    relay.upstreamActive = false;
    cameraMjpegRelays.delete(relay.key);
  }
}

function endCameraMjpegRelayClients(
  relay: CameraMjpegRelay,
  status: number,
  error: string,
  remoteStatus: number | null,
  lastErrorPayload: Record<string, unknown> | null = null,
): void {
  // 上游失败时只收口所有预览响应；不能影响 summary、键盘或 Nav2 代理。
  cameraMjpegRelayLastFailures.set(relay.key, {
    failure_reason: error,
    remote_http_status: remoteStatus,
    failed_at_ms: Date.now(),
    last_error_payload: lastErrorPayload,
  });
  const clients = Array.from(relay.clients);
  relay.clients.clear();
  cameraMjpegRelays.delete(relay.key);
  for (const client of clients) {
    if (client.response.destroyed) {
      continue;
    }
    if (client.headersStarted || client.response.headersSent) {
      client.response.end();
    } else {
      client.response.status(status).json({
        error,
        remote_http_status: remoteStatus,
        safe_to_control: false,
        robot_control_executed: false,
      });
    }
  }
}

async function cameraMjpegRemoteFailure(remote: globalThis.Response): Promise<{ reason: string; payload: Record<string, unknown> | null }> {
  // 上位机 relay 会把 8088 的真实失败放进 JSON；保留这个短原因，避免 PC 首屏误报成泛化 timeout。
  try {
    const payload = asRecord(await remote.clone().json().catch(() => null));
    const relay = asRecord(payload?.relay);
    const relayPayload = asRecord(relay?.last_error_payload);
    const lastErrorPayload = relayPayload ?? payload;
    const relayReason = normalizeCameraMjpegRemoteFailureReason(shortText(relay?.last_failure_reason, ""));
    if (relayReason) {
      return { reason: relayReason, payload: lastErrorPayload };
    }
    const failureReason = normalizeCameraMjpegRemoteFailureReason(shortText(payload?.failure_reason, ""));
    if (failureReason) {
      return { reason: failureReason, payload: lastErrorPayload };
    }
    const error = normalizeCameraMjpegRemoteFailureReason(shortText(payload?.error, ""));
    if (error) {
      return { reason: error, payload: lastErrorPayload };
    }
  } catch {
    // 非 JSON 错误页只保留通用短原因，防止 HTML/代理错误污染普通首屏。
  }
  return { reason: "camera_mjpeg_proxy_failed", payload: null };
}

function normalizeCameraMjpegRemoteFailureReason(reason: string): string {
  // aiohttp 的 socket read timeout 本质是上游 MJPEG 没等到帧；普通 UI 复用既有中文解释。
  const lower = reason.toLowerCase();
  if (lower.includes("timeout on reading data from socket") || lower.includes("shared_mjpeg_relay_timeout")) {
    return "camera_mjpeg_upstream_timeout";
  }
  return reason;
}

async function ensureCameraMjpegRelayStarted(relay: CameraMjpegRelay): Promise<void> {
  if (relay.upstreamActive) {
    return;
  }
  relay.upstreamActive = true;
  relay.controller = new AbortController();
  let connectTimedOut = false;
  const connectTimeout = setTimeout(() => {
    connectTimedOut = true;
    relay.controller?.abort();
  }, cameraMjpegUpstreamTimeoutMs());
  try {
    const remote = await fetch(endpointUrl(relay.normalizedBaseUrl, "/api/camera/mjpeg"), {
      method: "GET",
      signal: relay.controller.signal,
    });
    clearTimeout(connectTimeout);
    const contentType = remote.headers.get("content-type") ?? "";
    if (!remote.ok || !contentType.includes("multipart/x-mixed-replace") || !remote.body) {
      const remoteFailure = await cameraMjpegRemoteFailure(remote);
      endCameraMjpegRelayClients(relay, 502, remoteFailure.reason, remote.status, remoteFailure.payload);
      return;
    }
    relay.contentType = contentType;
    cameraMjpegRelayLastFailures.delete(relay.key);
    for (const client of relay.clients) {
      startCameraMjpegClient(client, contentType);
    }
    const reader = remote.body.getReader();
    while (relay.clients.size > 0) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      const frameChunk = Buffer.from(value);
      relay.latestFrameChunk = frameChunk;
      relay.latestFrameUpdatedAtMs = Date.now();
      for (const client of Array.from(relay.clients)) {
        try {
          startCameraMjpegClient(client, contentType);
          client.response.write(frameChunk);
        } catch {
          removeCameraMjpegClient(relay, client);
        }
      }
    }
    reader.releaseLock();
    endCameraMjpegRelayClients(relay, 502, "camera_mjpeg_upstream_closed", null);
  } catch (error) {
    clearTimeout(connectTimeout);
    if (!connectTimedOut && relay.clients.size === 0) {
      return;
    }
    const reason = connectTimedOut
      ? "camera_mjpeg_upstream_timeout"
      : error instanceof Error ? shortText(error.message, "camera_mjpeg_proxy_failed") : "camera_mjpeg_proxy_failed";
    endCameraMjpegRelayClients(relay, 502, reason, null);
  } finally {
    clearTimeout(connectTimeout);
    relay.controller = null;
    relay.upstreamActive = false;
  }
}

async function fetchBaseFeedbackSamplesProxy(
  baseUrl: string,
): Promise<{ remote_http_status: number | null; payload: Record<string, unknown> | null; error: string }> {
  // 这个 POST 只发送 vendor T=130 反馈采样参数，不接受浏览器传入 body 或运动方向。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return { remote_http_status: null, payload: null, error: normalized.reason };
  }
  try {
    const response = await fetch(endpointUrl(normalized.normalized, "/api/base/feedback-samples"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sample_count: 3,
        sample_interval_s: 0.15,
        read_timeout_s: 0.25,
        read_window_s: 0.35,
      }),
      signal: AbortSignal.timeout(6000),
    });
    const json = await response.json().catch(() => null);
    return {
      remote_http_status: response.status,
      payload: asRecord(json),
      error: "",
    };
  } catch (error) {
    return {
      remote_http_status: null,
      payload: null,
      error: error instanceof Error ? shortText(error.message, "upper_api_unreachable") : "upper_api_unreachable",
    };
  }
}

async function fetchBaseFeedbackSamplesLatestProxy(
  baseUrl: string,
): Promise<{ remote_http_status: number | null; payload: Record<string, unknown> | null; error: string }> {
  // GET 入口只读取上位机已经缓存的 latest 轮速材料，给脚本/首屏 readback 使用，不触发 T=130 采样窗口。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return { remote_http_status: null, payload: null, error: normalized.reason };
  }
  try {
    const response = await fetch(endpointUrl(normalized.normalized, "/api/base/feedback-samples/latest"), {
      method: "GET",
      signal: AbortSignal.timeout(6000),
    });
    const json = await response.json().catch(() => null);
    return {
      remote_http_status: response.status,
      payload: asRecord(json),
      error: "",
    };
  } catch (error) {
    return {
      remote_http_status: null,
      payload: null,
      error: error instanceof Error ? shortText(error.message, "upper_api_unreachable") : "upper_api_unreachable",
    };
  }
}

export function createWorkstationApp(): express.Express {
  const workstationApp = express();

  // Express 只承载本地 PC API 和构建后的静态 UI。
  // 这里不挂载任何 ROS2、串口、控制或云端生产客户端。
  workstationApp.use(express.json());

  workstationApp.get("/api/health", (_req, res) => {
    // health 也保留 fail-closed 字段，避免监控把服务在线误读为机器人在线。
    res.json(buildHealth());
  });

  workstationApp.get("/api/tools/evidence", async (_req, res) => {
    // API 只读索引 JSON fixture，不执行任何外部脚本或现场链路。
    res.json(await buildEvidenceToolsResponse());
  });

  workstationApp.get("/api/tools/hardware-materials", async (_req, res) => {
    // Hardware materials 只读扫描 WAVE ROVER fixture 文件名，不打开串口或执行 HIL。
    res.json(await buildHardwareMaterialsResponse());
  });

  workstationApp.get("/api/hardware/wave-rover/material-coverage", async (_req, res) => {
    // 新路径按本轮 tech-plan 命名；响应与旧 tools 路径一致，便于 UI 和 reviewer 复核。
    res.json(await buildHardwareMaterialsResponse());
  });

  workstationApp.get("/api/tools/training-labeling", async (_req, res) => {
    // 训练/标注第一阶段是占位入口，必须显式声明未接真实流水线。
    res.json(await buildTrainingLabelingResponse());
  });

  workstationApp.get("/api/route/debug-summary", async (req, res) => {
    // route 摘要可读取用户指定的本地 JSON，但仍不执行 Python、ROS2 或控制动作。
    res.json(
      await buildRouteDebugSummary({
        statusJson: queryString(req.query.statusJson),
        taskRecord: queryString(req.query.taskRecord),
        taskRecordDir: queryString(req.query.taskRecordDir),
        elevatorRouteReconciliation: queryString(req.query.elevatorRouteReconciliation),
      }),
    );
  });

  workstationApp.get("/api/o7/operator-console", (_req, res) => {
    // O7 console 只返回 cloud contract draft，不连接机器人、不发送控制命令。
    res.json(buildO7OperatorConsoleResponse());
  });

  workstationApp.get("/api/o7/operator-console/acceptance", (_req, res) => {
    // Acceptance guard 只复核 O7 console 响应，不读取硬件、不发命令、不连接云端生产。
    res.json(buildO7OperatorConsoleAcceptanceResponse());
  });

  workstationApp.get("/api/o7/previews/acceptance", (_req, res) => {
    // Previews guard 汇总本地/HTTP 预览证据边界，不读取 fixture、不探测云端、不触发控制。
    res.json(buildO7PreviewsAcceptanceResponse());
  });

  workstationApp.get("/api/o7/live-endpoints/manifest", (_req, res) => {
    // Live endpoints manifest 只读取 env 配置并脱敏，不执行 ping/connect/send 或硬件读取。
    res.json(buildO7LiveEndpointsManifest());
  });

  workstationApp.get("/api/o7/cloud-operator-console-probe", async (req, res) => {
    // Cloud probe 只允许后端探测本机回环 HTTP contract，不能变成外网或生产云代理。
    res.json(await buildO7CloudOperatorConsoleProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/consumer-read/tasks", async (req, res) => {
    // O7 列表主入口只读代理本机回环 O6 consumer read，不直连公网或机器人。
    res.json(await buildO7ConsumerTaskList(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/consumer-read/tasks/:taskId", async (req, res) => {
    // 本地 field evidence manifest 只作为远端缺字段时的只读补齐来源，不改变远端轨迹/事件等摘要。
    res.json(
      await buildO7ConsumerTaskDetail(
        queryString(req.query.baseUrl),
        req.params.taskId ?? "",
        queryString(req.query.fieldEvidenceManifestJson),
      ),
    );
  });

  workstationApp.get("/api/o7/cloud-archive/tasks-probe", async (req, res) => {
    // Archive tasks probe 只拉取本机回环 cloud relay contract，不读取远程 URL、不发送任何控制动作。
    res.json(await buildO7CloudArchiveTasksProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/realtime-elevator-probe", async (req, res) => {
    // Realtime/elevator probe 只拉取本机回环 snapshot contract，不读取 ROS2 /tf、地图或电梯设备。
    res.json(await buildO7RealtimeElevatorProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/rtc-signaling-contract-probe", async (req, res) => {
    // RTC signaling contract probe 只拉取本机回环协议清单，不创建 WebRTC session、视频或 ROS2 /tf 连接。
    res.json(await buildO7RtcSignalingContractProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/realtime-elevator-preview", async (req, res) => {
    // Realtime/elevator preview 只读取本地 fixture 摘要，不连接云端实时流、ROS2 /tf 或电梯设备。
    res.json(await buildO7RealtimeElevatorPreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/route-replay-preview", async (req, res) => {
    // Route replay preview 只读取 query 指定的本地 JSON fixture，并固定关闭云归档和控制声明。
    res.json(await buildO7RouteReplayPreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/labeling-preview", async (req, res) => {
    // Labeling preview 只读取本地 fixture 摘要，提交、回滚、导出和机器人控制全部关闭。
    res.json(await buildO7LabelingPreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/field-evidence-consumer-ingest", async (req, res) => {
    // Field evidence consumer ingest 把 manifest 入口和 route replay / labeling 两条只读链拼成一份摘要。
    res.json(
      await buildO7FieldEvidenceConsumerIngest({
        manifestJson: queryString(req.query.manifestJson),
        routeReplayFixtureJson: queryString(req.query.routeReplayFixtureJson),
        labelingFixtureJson: queryString(req.query.labelingFixtureJson),
      }),
    );
  });

  workstationApp.get("/api/o7/voice-preview", async (req, res) => {
    // Voice preview 只读取本地 ASR/TTS fixture 摘要，不连接语音 API、不发送 TTS、不播放音频。
    res.json(await buildO7VoicePreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/safe-command-preview", async (req, res) => {
    // Safe command preview 只读取本地命令 envelope fixture，不连接云端、ROS2、Nav2 或硬件。
    res.json(await buildO7SafeCommandPreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/cloud-archive/tasks", async (req, res) => {
    // Cloud archive tasks 只读取用户指定的本地 archive fixture，不连接 O6 云端或真实 API。
    res.json(await buildO7CloudArchiveTasks({ archiveJson: queryString(req.query.archiveJson) }));
  });

  workstationApp.get("/api/robot-control/summary", async (req, res) => {
    // Robot Control V1 只读代理默认连固定上位机；危险 URL 仍由 summary builder fail-closed。
    const sourceBaseUrl = robotControlSummaryQueryBaseUrl(req.query.baseUrl);
    res.json(await buildRobotControlSummaryForHttp(sourceBaseUrl, {
      keyboardEvidence: robotControlKeyboardEvidenceQuery(req.query as Record<string, unknown>),
    }));
  });

  workstationApp.get("/api/robot-control/live-summary", async (req, res) => {
    // 给现场脚本一个扁平只读入口，避免每次都记 live_closure_summary 嵌套路径。
    const sourceBaseUrl = robotControlSummaryQueryBaseUrl(req.query.baseUrl);
    const summary = await buildRobotControlSummaryForHttp(sourceBaseUrl, {
      keyboardEvidence: robotControlKeyboardEvidenceQuery(req.query as Record<string, unknown>),
    });
    res.json(buildRobotControlLiveSummaryResponse(summary));
  });

  workstationApp.post("/api/robot-control/base/first-jog", async (req, res) => {
    // 首次试动与普通手控使用同一个最小门禁：现场默认安全，页面打开即可点动，画面/雷达只影响后续验收。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const payload = asRecord(req.body);
    const direction = allowedDirection(payload?.direction);
    const speed = finiteManualSpeedFromPayload(payload);
    const durationMs = finiteNumber(payload?.duration_ms);
    const confirmHilChecklist = true;
    if (!normalized.ok) {
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", normalized.reason, "stop", speed, durationMs, confirmHilChecklist));
      return;
    }
    const beforeEvidence = await captureEvidencePhase(normalized.normalized, "before");
    if (!direction || direction === "stop") {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(
        sourceBaseUrl,
        "manual",
        "/api/base/manual",
        direction === "stop" ? "first_jog_stop_use_stop_endpoint" : "direction_invalid",
        direction ?? "stop",
        speed,
        durationMs,
        confirmHilChecklist,
        evidenceCapture,
      ));
      return;
    }
    if (speed === null || durationMs === null) {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "manual_request_invalid_numbers", direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    const operatorReportPreflight = notRequiredConfirmedManualOperatorReportPreflight();
    const clampedSpeed = clamp(speed, 0, ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS);
    const clampedDurationMs = clamp(durationMs, 0, ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS);
    const manualCommandMode = manualCommandModeFromPayload(payload);
    const remote = await fetchFixedRobotPostSummary(sourceBaseUrl, "/api/base/manual", {
      direction,
      speed: clampedSpeed,
      duration_ms: clampedDurationMs,
      command_mode: manualCommandMode,
      feedback_mode: "bridge_debug",
      confirm_hil_checklist: true,
    });
    const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
    const remoteMotionKeyValues = baseManualMotionKeyValues(remote.payload);
    const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence], "", remoteMotionKeyValues);
    if (remote.error) {
      res.status(502).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", remote.error, direction, speed, durationMs, confirmHilChecklist, evidenceCapture, operatorReportPreflight));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload, "", BASE_COMMAND_FAIL_CLOSED_FIELDS);
    const responseEvidenceCapture = remote.remote_http_status === 200
      ? evidenceCapture
      : {
          ...evidenceCapture,
          motion_evidence_gaps: [
            "motion_command_not_forwarded",
            ...evidenceCapture.motion_evidence_gaps.filter((gap) => gap !== "motion_command_not_forwarded"),
          ],
        };
    const responseBody: RobotControlBaseCommandProxyResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
      command_kind: "manual",
      proxy_status:
        remote.remote_http_status === 200 && dangerous.length === 0 ? "command_forwarded" : "command_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/base/manual",
      remote_http_status: remote.remote_http_status,
      status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "loaded" : "blocked"),
      requested_direction: direction,
      applied_direction: direction,
      requested_speed_mps: speed,
      clamped_speed_mps: clampedSpeed,
      requested_duration_ms: durationMs,
      clamped_duration_ms: clampedDurationMs,
      confirm_hil_checklist: true,
      ...baseCommandMinimalPrecheckFields(true),
      non_stop_requires_confirm_hil_checklist: false,
      hil_checklist_gate_status: "manual_allowed",
      checklist_missing: [],
      operator_report_preflight: operatorReportPreflight,
      request_contract: {
        max_speed_mps: ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
        max_duration_ms: ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS,
        allowed_directions: [...ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS],
      },
      remote_motion_key_values: remoteMotionKeyValues,
      ...baseManualMotionTopLevelAliases(remoteMotionKeyValues),
      ...responseEvidenceCapture,
      failure_reason:
        dangerous.length > 0
          ? `dangerous_true_field:${dangerous[0]}`
          : remote.remote_http_status === 200
            ? ""
            : `manual_http_status_${remote.remote_http_status}`,
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`manual_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
      ],
      hard_dangerous_true_fields: dangerous,
    };
    res.status(responseBody.proxy_status === "command_forwarded" ? 200 : 502).json(responseBody);
  });

  workstationApp.post("/api/robot-control/base/manual", async (req, res) => {
    // 点动代理只允许固定 manual endpoint；WASD 要低延迟，松手后再补只读证据快照。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const payload = asRecord(req.body);
    const direction = allowedDirection(payload?.direction);
    const speed = finiteManualSpeedFromPayload(payload);
    const durationMs = finiteNumber(payload?.duration_ms);
    const confirmHilChecklist = true;
    if (!normalized.ok) {
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", normalized.reason, "stop", speed, durationMs, confirmHilChecklist));
      return;
    }
    if (!direction) {
      const evidenceCapture = realtimeManualEvidenceCapture();
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "direction_invalid", "stop", speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    if (direction === "stop") {
      const evidenceCapture = realtimeManualEvidenceCapture();
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "direction_stop_use_stop_endpoint", direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    if (speed === null || durationMs === null) {
      const evidenceCapture = realtimeManualEvidenceCapture();
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "manual_request_invalid_numbers", direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    const operatorReportPreflight = notRequiredConfirmedManualOperatorReportPreflight();

    const clampedSpeed = clamp(speed, 0, ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS);
    const clampedDurationMs = clamp(durationMs, 0, ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS);
    const manualCommandMode = manualCommandModeFromPayload(payload);
    const remote = await fetchFixedRobotPostSummary(sourceBaseUrl, "/api/base/manual", {
      direction,
      speed: clampedSpeed,
      duration_ms: clampedDurationMs,
      command_mode: manualCommandMode,
      feedback_mode: "realtime",
      confirm_hil_checklist: true,
    });
    const remoteMotionKeyValues = baseManualMotionKeyValues(remote.payload);
    const evidenceCapture = realtimeManualEvidenceCapture(remoteMotionKeyValues);
    if (remote.error) {
      res.status(502).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", remote.error, direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload, "", BASE_COMMAND_FAIL_CLOSED_FIELDS);
    const responseEvidenceCapture = remote.remote_http_status === 200
      ? evidenceCapture
      : {
          ...evidenceCapture,
          motion_evidence_gaps: [
            "motion_command_not_forwarded",
            ...evidenceCapture.motion_evidence_gaps.filter((gap) => gap !== "motion_command_not_forwarded"),
          ],
        };
    const responseBody: RobotControlBaseCommandProxyResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
      command_kind: "manual",
      proxy_status:
        remote.remote_http_status === 200 && dangerous.length === 0 ? "command_forwarded" : "command_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/base/manual",
      remote_http_status: remote.remote_http_status,
      status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "loaded" : "blocked"),
      requested_direction: direction,
      applied_direction: direction,
      requested_speed_mps: speed,
      clamped_speed_mps: clampedSpeed,
      requested_duration_ms: durationMs,
      clamped_duration_ms: clampedDurationMs,
      confirm_hil_checklist: true,
      ...baseCommandMinimalPrecheckFields(true),
      non_stop_requires_confirm_hil_checklist: false,
      hil_checklist_gate_status: "manual_allowed",
      checklist_missing: [],
      operator_report_preflight: operatorReportPreflight,
      request_contract: {
        max_speed_mps: ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
        max_duration_ms: ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS,
        allowed_directions: [...ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS],
      },
      remote_motion_key_values: remoteMotionKeyValues,
      ...baseManualMotionTopLevelAliases(remoteMotionKeyValues),
      ...responseEvidenceCapture,
      failure_reason:
        dangerous.length > 0
          ? `dangerous_true_field:${dangerous[0]}`
          : remote.remote_http_status === 200
            ? ""
            : `manual_http_status_${remote.remote_http_status}`,
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`manual_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
      ],
      hard_dangerous_true_fields: dangerous,
    };
    res.status(responseBody.proxy_status === "command_forwarded" ? 200 : 502).json(responseBody);
  });

  workstationApp.post("/api/robot-control/base/stop", async (req, res) => {
    // stop 是唯一允许在未勾 checklist 时执行的动作；它仍然只走固定 stop endpoint。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "stop", "/api/base/stop", normalized.reason, "stop", 0, 0, false));
      return;
    }
    const beforeEvidence = await captureEvidencePhase(normalized.normalized, "before");
    const remote = await fetchFixedRobotPostSummary(sourceBaseUrl, "/api/base/stop", {});
    const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
    const evidenceCapture = buildEvidenceCapture("stop", [...beforeEvidence, ...afterEvidence]);
    if (remote.error) {
      res.status(502).json(baseCommandFailure(sourceBaseUrl, "stop", "/api/base/stop", remote.error, "stop", 0, 0, false, evidenceCapture));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload, "", BASE_COMMAND_FAIL_CLOSED_FIELDS);
    const responseBody: RobotControlBaseCommandProxyResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
      command_kind: "stop",
      proxy_status:
        remote.remote_http_status === 200 && dangerous.length === 0 ? "command_forwarded" : "command_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/base/stop",
      remote_http_status: remote.remote_http_status,
      status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "stopped" : "blocked"),
      requested_direction: "stop",
      applied_direction: "stop",
      requested_speed_mps: 0,
      clamped_speed_mps: 0,
      requested_duration_ms: 0,
      clamped_duration_ms: 0,
      confirm_hil_checklist: false,
      ...baseCommandMinimalPrecheckFields(false),
      non_stop_requires_confirm_hil_checklist: false,
      hil_checklist_gate_status: "stop_allowed_without_checklist",
      checklist_missing: [],
      operator_report_preflight: notRequiredOperatorReportPreflight(),
      request_contract: {
        max_speed_mps: ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
        max_duration_ms: ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS,
        allowed_directions: [...ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS],
      },
      ...evidenceCapture,
      failure_reason:
        dangerous.length > 0
          ? `dangerous_true_field:${dangerous[0]}`
          : remote.remote_http_status === 200
            ? ""
            : `stop_http_status_${remote.remote_http_status}`,
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`stop_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
      ],
      hard_dangerous_true_fields: dangerous,
    };
    res.status(responseBody.proxy_status === "command_forwarded" ? 200 : 502).json(responseBody);
  });

  workstationApp.post("/api/robot-control/base/feedback-samples", async (req, res) => {
    // 反馈样本只触发固定 T=130 只读采集，不接受浏览器 body，也不调用 manual/stop/cmd_vel。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(baseFeedbackSamplesFailure(sourceBaseUrl, normalized.reason));
      return;
    }
    const remote = await fetchBaseFeedbackSamplesProxy(sourceBaseUrl);
    if (remote.error) {
      res.status(502).json({
        ...baseFeedbackSamplesFailure(sourceBaseUrl, remote.error),
        proxy_status: "samples_failed",
      } satisfies RobotControlBaseFeedbackSamplesProxyResponse);
      return;
    }
    const responseBody = buildBaseFeedbackSamplesResponse(sourceBaseUrl, normalized.normalized, "/api/base/feedback-samples", remote);
    res.status(responseBody.proxy_status === "samples_forwarded" ? 200 : 502).json(responseBody);
  });

  workstationApp.get("/api/robot-control/base/feedback-samples", async (req, res) => {
    // 只读脚本入口必须返回 JSON latest；不能让 GET 掉进 SPA fallback，也不能补发采样或运动 POST。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(baseFeedbackSamplesFailure(sourceBaseUrl, normalized.reason, "/api/base/feedback-samples/latest"));
      return;
    }
    const remote = await fetchBaseFeedbackSamplesLatestProxy(sourceBaseUrl);
    if (remote.error) {
      res.status(502).json({
        ...baseFeedbackSamplesFailure(sourceBaseUrl, remote.error, "/api/base/feedback-samples/latest"),
        proxy_status: "samples_failed",
      } satisfies RobotControlBaseFeedbackSamplesProxyResponse);
      return;
    }
    const responseBody = buildBaseFeedbackSamplesResponse(sourceBaseUrl, normalized.normalized, "/api/base/feedback-samples/latest", remote);
    res.status(responseBody.proxy_status === "samples_forwarded" ? 200 : 502).json(responseBody);
  });

  workstationApp.post("/api/robot-control/operator/report", async (req, res) => {
    // 现场材料提交只转发固定 /api/operator/report；不开放底盘、Nav2、cmd_vel、map/radar start。
    const response = await buildOperatorReportProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl), req.body);
    res.status(response.proxy_status === "report_forwarded" ? 200 : response.proxy_status === "report_rejected" ? 400 : 502).json(response);
  });

  workstationApp.post("/api/robot-control/radar/scan-proof/refresh", async (req, res) => {
    // Radar refresh 只允许固定 POST body，不接受浏览器把它改造成通用控制代理。
    const response = await buildRadarScanProofRefreshProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  workstationApp.get("/api/robot-control/base/status", async (req, res) => {
    // Base status 是固定只读 GET；用于证明 command mode 与 wheel raw L/R 读回，不发送 manual/stop/cmd_vel。
    const response = await buildReadOnlyStatusResponse(
      robotControlReadOnlyQueryBaseUrl(req.query.baseUrl),
      "/api/robot-control/base/status",
      "/api/base/status",
    );
    res.status(response.httpStatus).json(response.body);
  });

  workstationApp.get("/api/robot-control/nav2/status", async (req, res) => {
    // Nav2 status 是固定只读 GET；用于解释路线/服务 blocker，不启动 lifecycle、不执行 goal。
    const response = await buildReadOnlyStatusResponse(
      robotControlReadOnlyQueryBaseUrl(req.query.baseUrl),
      "/api/robot-control/nav2/status",
      "/api/nav2/status",
    );
    res.status(response.httpStatus).json(response.body);
  });

  workstationApp.get("/api/robot-control/radar/status", async (req, res) => {
    // Radar status 是固定只读 GET；给地图和现场 smoke 一个稳定 JSON 入口，不能退化成任意 Robot API 代理。
    const sourceBaseUrl = robotControlReadOnlyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const fallbackBase: RobotControlRadarStatusResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_radar_status_proxy.v1",
      proxy_status: "status_rejected",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
      workstation_endpoint: "/api/robot-control/radar/status",
      remote_endpoint: "/api/radar/status",
      remote_method: "GET",
      remote_http_status: null,
      status: "blocked",
      ...RADAR_STATUS_READBACK_FLAGS,
      radar_key_values: {},
      ...radarStatusPlainFields({}),
      failure_reason: normalized.ok ? "" : normalized.reason,
      blocked_reasons: normalized.ok ? [] : [normalized.reason],
      hard_dangerous_true_fields: [],
    };
    if (!normalized.ok) {
      res.status(400).json(fallbackBase);
      return;
    }
    try {
      const remote = await fetch(endpointUrl(normalized.normalized, "/api/radar/status"), {
        method: "GET",
        signal: AbortSignal.timeout(8000),
      });
      const remotePayload = asRecord(await remote.json().catch(() => null));
      const dangerous = scanDangerousTrueFields(remotePayload);
      const radarKeyValues = compactKeyValues(remotePayload);
      let mapPreviewPayload: Record<string, unknown> | null = null;
      let mapPreviewHttpStatus: number | null = null;
      let mapPreviewFailureReason = "";
      try {
        const mapPreviewProxy = await buildMapPreviewProxy(sourceBaseUrl);
        mapPreviewHttpStatus = mapPreviewProxy.remote_http_status;
        mapPreviewPayload = mapPreviewProxy as unknown as Record<string, unknown>;
        if (mapPreviewProxy.proxy_status !== "preview_forwarded") {
          mapPreviewFailureReason = mapPreviewProxy.failure_reason || "map_preview_not_loaded";
        }
      } catch (mapPreviewError) {
        mapPreviewFailureReason = mapPreviewError instanceof Error
          ? shortText(mapPreviewError.message, "map_preview_failed")
          : "map_preview_failed";
      }
      const responseBody: RobotControlRadarStatusResponse = {
        ...fallbackBase,
        proxy_status: remote.ok && remotePayload && dangerous.length === 0 ? "status_loaded" : "status_failed",
        remote_http_status: remote.status,
        status: remote.ok ? "loaded_fail_closed_summary" : "blocked",
        radar_key_values: radarKeyValues,
        ...radarStatusPlainFields(radarKeyValues),
        ...radarStatusMapPreviewFields(mapPreviewPayload, mapPreviewHttpStatus, mapPreviewFailureReason),
        failure_reason: dangerous.length > 0 ? `dangerous_true_field:${dangerous[0]}` : remote.ok ? "" : `radar_status_http_status_${remote.status}`,
        blocked_reasons: [
          ...(remote.ok ? [] : [`radar_status_http_status_${remote.status}`]),
          ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ],
        hard_dangerous_true_fields: dangerous,
      };
      res.status(responseBody.proxy_status === "status_loaded" ? 200 : 502).json(responseBody);
    } catch (error) {
      const reason = error instanceof Error ? shortText(error.message, "radar_status_failed") : "radar_status_failed";
      res.status(502).json({ ...fallbackBase, proxy_status: "status_failed", failure_reason: reason, blocked_reasons: [reason] });
    }
  });

  ([
    ["start", "/api/robot-control/radar/start"],
    ["stop", "/api/robot-control/radar/stop"],
  ] as Array<[RobotControlRadarLifecycleAction, string]>).forEach(([action, route]) => {
    workstationApp.post(route, async (req, res) => {
      // Radar lifecycle 只转发固定 start/stop；body 被忽略，避免退化成任意 Robot API POST。
      const response = await buildRadarLifecycleProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl), action);
      res.status(mapLifecycleStatusCode(response.proxy_status)).json(response);
    });
  });

  workstationApp.post("/api/robot-control/map/proof/refresh", async (req, res) => {
    // Map refresh 只允许固定 POST body，不接受浏览器把它改造成建图/导航控制代理。
    const response = await buildMapProofRefreshProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  workstationApp.post("/api/robot-control/nav2/proof/refresh", async (req, res) => {
    // Nav2 refresh 只允许固定 no-motion planner proof body，不开放 start/stop、goal 或底盘动作。
    const response = await buildNav2NoMotionProofRefreshProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  ([
    ["start", "/api/robot-control/nav2/start"],
    ["stop", "/api/robot-control/nav2/stop"],
  ] as Array<[RobotControlNav2LifecycleAction, string]>).forEach(([action, route]) => {
    workstationApp.post(route, async (req, res) => {
      // Nav2 lifecycle 只恢复/停止服务栈；body 被忽略，不能透传目标点或速度控制。
      const response = await buildNav2LifecycleProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl), action);
      res.status(mapLifecycleStatusCode(response.proxy_status)).json(response);
    });
  });

  workstationApp.post("/api/robot-control/nav2/goal/preflight", async (req, res) => {
    // 目标预检只做最小确认和 fixed GET 摘要；即使通过也不调用 NavigateToPose、/api/nav2/start、/cmd_vel 或 base manual。
    const response = await buildNavGoalPreflightProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl), req.body);
    res.status(response.proxy_status === "preflight_passed" ? 200 : 400).json(response);
  });

  workstationApp.post("/api/robot-control/nav2/goal/execute", async (req, res) => {
    // 目标执行只转发固定 NavigateToPose proof endpoint；不开放任意上位机 POST。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const payload = asRecord(req.body);
    // 现场普通页打开即用；PC 固定代理自动写入上车兼容确认字段，不再要求用户额外勾选。
    const confirmNavigationExecution = true;
    const goalX = clamp(Number(payload?.goal_x ?? 0.8), -3, 3);
    const goalY = clamp(Number(payload?.goal_y ?? 0), -3, 3);
    const goalYaw = clamp(Number(payload?.goal_yaw ?? 0), -Math.PI, Math.PI);
    const routePreviewPointCount = Math.round(clamp(Number(payload?.route_preview_point_count ?? 0), 0, 10000));
    const routePreviewSourcePointCount = Math.round(clamp(Number(payload?.route_preview_source_point_count ?? routePreviewPointCount), 0, 100000));
    const routePreviewFrameId = shortText(String(payload?.route_preview_frame_id ?? "map"), "map").slice(0, 64);
    const nullableRouteNumber = (value: unknown): number | null => {
      // 路线元数据只做证据绑定；非法坐标丢弃为 null，不能影响真正目标点 clamp。
      const numeric = Number(value);
      return Number.isFinite(numeric) ? clamp(numeric, -1000, 1000) : null;
    };
    const routeStartX = nullableRouteNumber(payload?.route_start_x);
    const routeStartY = nullableRouteNumber(payload?.route_start_y);
    const routeGoalX = nullableRouteNumber(payload?.route_goal_x);
    const routeGoalY = nullableRouteNumber(payload?.route_goal_y);
    const routePreview = {
      point_count: routePreviewPointCount,
      source_point_count: routePreviewSourcePointCount,
      frame_id: routePreviewFrameId,
      start_x: routeStartX,
      start_y: routeStartY,
      goal_x: routeGoalX,
      goal_y: routeGoalY,
    };
    const resultTimeoutS = clamp(Number(payload?.result_timeout_s ?? 8), 2, 20);
    const serverTimeoutS = clamp(Number(payload?.server_timeout_s ?? 12), 1, 20);
    // O11 execute helper 默认支持托管 runtime；PC 侧显式写入，避免普通用户先手动启动 Nav2 lifecycle。
    const managedRuntimeOptIn = payload?.managed_runtime_opt_in !== false;
    const managedStartupS = clamp(Number(payload?.managed_startup_s ?? 2), 0, 5);
    const managedReadyTimeoutS = clamp(Number(payload?.managed_ready_timeout_s ?? 90), 10, 90);
    const requestedBaseCommandMode = String(payload?.base_command_mode ?? payload?.nav2_base_command_mode ?? "").trim().toLowerCase();
    const requestedBaseCommandModeValid = ["ros", "speed", "pwm"].includes(requestedBaseCommandMode);
    // Nav2 普通执行默认走 ROS /cmd_vel 到 bridge，避免旧 PWM 诊断模式继续混入真实路线复验。
    let baseCommandMode: "ros" | "speed" | "pwm" = requestedBaseCommandModeValid
      ? requestedBaseCommandMode as "ros" | "speed" | "pwm"
      : "ros";
    const fallbackBase: RobotControlNavGoalExecutionResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_proxy.v1",
      proxy_status: "execution_rejected",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      minimal_precheck_safety_only: true,
      minimal_precheck_plain: NAV2_GOAL_MINIMAL_PRECHECK_PLAIN,
      execution_blocking_requirements: [...NAV2_GOAL_EXECUTION_BLOCKING_REQUIREMENTS],
      operator_precheck_requirements: [...NAV2_GOAL_EXECUTION_OPERATOR_PRECHECK_REQUIREMENTS],
      proxy_guard_requirements: [...NAV2_GOAL_EXECUTION_PROXY_GUARD_REQUIREMENTS],
      camera_preflight_required: false,
      radar_preflight_required: false,
      operator_report_preflight_required: false,
      route_readback_preflight_required: false,
      localization_readback_preflight_required: false,
      nav2_status_readback_preflight_required: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
      workstation_endpoint: "/api/robot-control/nav2/goal/execute",
      remote_endpoint: "/api/nav2/goal/execute",
      remote_http_status: null,
      status: "blocked",
      goal_request: {
        goal_frame_id: "map",
        goal_x: goalX,
        goal_y: goalY,
        goal_yaw: goalYaw,
        result_timeout_s: resultTimeoutS,
        server_timeout_s: serverTimeoutS,
        managed_runtime_opt_in: managedRuntimeOptIn,
        managed_startup_s: managedStartupS,
        managed_ready_timeout_s: managedReadyTimeoutS,
        confirm_navigation_execution: confirmNavigationExecution,
        base_command_mode: baseCommandMode,
        route_preview_point_count: routePreviewPointCount,
        route_preview_source_point_count: routePreviewSourcePointCount,
        route_preview_frame_id: routePreviewFrameId,
        route_start_x: routeStartX,
        route_start_y: routeStartY,
        route_goal_x: routeGoalX,
        route_goal_y: routeGoalY,
      },
      goal_execution_key_values: {},
      failure_reason: normalized.ok ? "" : normalized.reason,
      blocked_reasons: normalized.ok ? [] : [normalized.reason],
      hard_dangerous_true_fields: [],
    };
    if (!normalized.ok) {
      res.status(400).json(fallbackBase);
      return;
    }
    // 真正发车前复用 PC 本机最小确认门禁，防止用户绕过前端按钮直接打执行接口。
    const preflight = await buildNavGoalPreflightProxy(sourceBaseUrl, {
      goal_x: goalX,
      goal_y: goalY,
      goal_yaw: goalYaw,
      confirm_navigation_preflight: true,
    });
    if (preflight.proxy_status !== "preflight_passed") {
      const blockedReasons = preflight.blocked_reasons.length > 0 ? preflight.blocked_reasons : ["nav_goal_preflight_failed"];
      res.status(400).json({
        ...fallbackBase,
        goal_execution_key_values: {
          preflight_status: preflight.preflight_status,
          missing_requirements: blockedReasons.join(","),
        },
        failure_reason: blockedReasons[0],
        blocked_reasons: blockedReasons,
        hard_dangerous_true_fields: preflight.hard_dangerous_true_fields,
      });
      return;
    }
    if (!requestedBaseCommandModeValid) {
      baseCommandMode = await resolveNavGoalExecutionDefaultBaseCommandMode(normalized.normalized);
      fallbackBase.goal_request.base_command_mode = baseCommandMode;
    }
    try {
      const remote = await fetch(endpointUrl(normalized.normalized, "/api/nav2/goal/execute"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal_frame_id: "map",
          goal_x: goalX,
          goal_y: goalY,
          goal_yaw: goalYaw,
          server_timeout_s: serverTimeoutS,
          result_timeout_s: resultTimeoutS,
          managed_runtime_opt_in: managedRuntimeOptIn,
          managed_startup_s: managedStartupS,
          managed_ready_timeout_s: managedReadyTimeoutS,
          confirm_navigation_execution: true,
          base_command_mode: baseCommandMode,
          route_preview: routePreview,
          route_preview_point_count: routePreviewPointCount,
          route_preview_source_point_count: routePreviewSourcePointCount,
          route_preview_frame_id: routePreviewFrameId,
          route_start_x: routeStartX,
          route_start_y: routeStartY,
          route_goal_x: routeGoalX,
          route_goal_y: routeGoalY,
        }),
        // O11 会等待 Nav2 lifecycle active 后才发 goal；PC 等待窗口必须大于上位机 helper 的结构化超时。
        signal: AbortSignal.timeout(Math.round((resultTimeoutS + 90) * 1000)),
      });
      const remotePayload = asRecord(await remote.json().catch(() => null));
      const dangerous = scanDangerousTrueFields(remotePayload).filter(
        (field) => !nav2GoalExecutionAllowedTrueField(field),
      );
      const responseBody: RobotControlNavGoalExecutionResponse = {
        ...fallbackBase,
        proxy_status: remote.ok && dangerous.length === 0 ? "execution_forwarded" : "execution_failed",
        remote_http_status: remote.status,
        status: remote.ok ? "loaded_fail_closed_summary" : "blocked",
        goal_execution_key_values: navGoalExecutionKeyValues(remotePayload),
        failure_reason: dangerous.length > 0 ? `dangerous_true_field:${dangerous[0]}` : remote.ok ? "" : `execute_http_status_${remote.status}`,
        blocked_reasons: [
          ...(remote.ok ? [] : [`execute_http_status_${remote.status}`]),
          ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ],
        hard_dangerous_true_fields: dangerous,
        robot_control_executed: remotePayload?.robot_control_executed === true,
      };
      res.status(responseBody.proxy_status === "execution_forwarded" ? 200 : 502).json(responseBody);
    } catch (error) {
      const reason = error instanceof Error ? shortText(error.message, "nav2_goal_execute_failed") : "nav2_goal_execute_failed";
      res.status(502).json({ ...fallbackBase, proxy_status: "execution_failed", failure_reason: reason, blocked_reasons: [reason] });
    }
  });

  workstationApp.get("/api/robot-control/nav2/goal/execution/latest", async (req, res) => {
    // latest 只读最近 NavigateToPose artifact，用于送达材料预填；不发送新的 Nav2 goal。
    const sourceBaseUrl = robotControlReadOnlyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const fallbackBase: RobotControlNavGoalExecutionLatestResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
      proxy_status: "latest_rejected",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
      workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
      remote_endpoint: "/api/nav2/goal/execution/latest",
      remote_http_status: null,
      status: "blocked",
      goal_execution_key_values: {},
      latest_key_values: {},
      goal_execution_status: "not_loaded",
      result_status: "not_loaded",
      nav2_goal_execution_proven: "not_loaded",
      execution_proof_gap: "not_loaded",
      goal_execution_hil_pass: "not_loaded",
      goal_execution_robot_control_executed: "not_loaded",
      goal_execution_feedback_sample_count: "not_loaded",
      goal_execution_base_feedback_sample_count: "not_loaded",
      goal_execution_base_feedback_nonzero_sample_count: "not_loaded",
      goal_execution_goal_succeeded: "not_loaded",
      goal_execution_wheel_rerun_needed: "not_loaded",
      goal_execution_minimal_precheck_safety_only: true,
      goal_execution_safety_confirm_required: false,
      goal_execution_camera_preflight_required: false,
      goal_execution_radar_preflight_required: false,
      goal_execution_operator_report_preflight_required: false,
      goal_execution_route_wysiwyg_preflight_required: false,
      readback_only: true,
      nav2_goal_execution_latest_readback_only: true,
      sends_motion_when_clicked: false,
      starts_camera_exclusive_capture: false,
      starts_radar_lifecycle: false,
      starts_nav2: false,
      starts_manual: false,
      starts_keyboard: false,
      starts_free_roam: false,
      starts_map_runtime: false,
      submits_delivery: false,
      stops_motion: false,
      fixed_goal_execution_endpoint: "/api/robot-control/nav2/goal/execute",
      fixed_goal_execution_latest_endpoint: "/api/robot-control/nav2/goal/execution/latest",
      plain_hint: "图上路线还未准备完成。",
      execution_status_plain: "图上路线还未准备完成。",
      next_action_plain: "先准备图上路线并刷新地图画面，然后直接执行。",
      route_execution_readiness_plain: "图上路线还不可执行；当前缺口：图上路线还未准备完成。",
      route_execution_precheck_plain: "路线准备完成后可直接执行；现场默认安全，不要求额外勾选。",
      goal_execution_wheel_raw_lr_status_plain: "本轮完整路线执行的轮速 L/R 还未证明。",
      goal_execution_wheel_raw_lr_next_action_plain: "先准备图上路线并执行，再在同窗口确认轮速 L/R 非零。",
      goal_execution_next_mode_plain: "下次执行模式未读到；默认由执行接口按固定策略选择。",
      goal_execution_mode_rerun_plain: "还没有可用的路线执行模式复验结论。",
      base_command_mode: "not_loaded",
      goal_execution_base_command_mode: "not_loaded",
      next_execution_base_command_mode: "ros",
      goal_execution_base_command_nonzero_observed: "not_loaded",
      goal_execution_base_command_nonzero_count: "0",
      goal_execution_base_command_mode_counts: "{}",
      goal_execution_base_feedback_lr_nonzero_proven: "not_loaded",
      goal_execution_base_feedback_imu_attitude_delta_observed: "not_loaded",
      goal_execution_readback_publishes_cmd_vel: "not_loaded",
      goal_execution_managed_runtime_requested: "not_loaded",
      goal_execution_managed_runtime_started: "not_loaded",
      goal_execution_managed_runtime_lifecycle_ready_ok: "not_loaded",
      goal_execution_managed_runtime_cleanup_ok: "not_loaded",
      goal_execution_base_feedback_latest_raw_left: "not_loaded",
      goal_execution_base_feedback_latest_raw_right: "not_loaded",
      failure_reason: normalized.ok ? "" : normalized.reason,
      blocked_reasons: normalized.ok ? [] : [normalized.reason],
      hard_dangerous_true_fields: [],
    };
    if (!normalized.ok) {
      res.status(400).json(fallbackBase);
      return;
    }
    try {
      const remote = await fetch(endpointUrl(normalized.normalized, "/api/nav2/goal/execution/latest"), {
        method: "GET",
        signal: AbortSignal.timeout(10000),
      });
      const remotePayload = asRecord(await remote.json().catch(() => null));
      const dangerous = scanDangerousTrueFields(remotePayload).filter(
        (field) => !nav2GoalExecutionAllowedTrueField(field),
      );
      const goalExecutionKeyValues = navGoalExecutionKeyValues(remotePayload);
      const latestPlainFields = navGoalLatestPlainFields(goalExecutionKeyValues);
      const latestKeyValues = {
        ...goalExecutionKeyValues,
        route_execution_readiness_plain: latestPlainFields.route_execution_readiness_plain,
        route_execution_precheck_plain: latestPlainFields.route_execution_precheck_plain,
        goal_execution_wheel_raw_lr_status_plain: latestPlainFields.goal_execution_wheel_raw_lr_status_plain,
        goal_execution_wheel_raw_lr_next_action_plain: latestPlainFields.goal_execution_wheel_raw_lr_next_action_plain,
        execution_status_plain: latestPlainFields.execution_status_plain,
        next_action_plain: latestPlainFields.next_action_plain,
        goal_execution_base_command_mode: latestPlainFields.goal_execution_base_command_mode,
        next_execution_base_command_mode: latestPlainFields.next_execution_base_command_mode,
        goal_execution_base_command_nonzero_observed: latestPlainFields.goal_execution_base_command_nonzero_observed,
        goal_execution_base_command_nonzero_count: latestPlainFields.goal_execution_base_command_nonzero_count,
        goal_execution_base_command_mode_counts: latestPlainFields.goal_execution_base_command_mode_counts,
        goal_execution_base_feedback_lr_nonzero_proven: latestPlainFields.goal_execution_base_feedback_lr_nonzero_proven,
        goal_execution_base_feedback_imu_attitude_delta_observed: latestPlainFields.goal_execution_base_feedback_imu_attitude_delta_observed,
        goal_execution_base_feedback_latest_raw_left: latestPlainFields.goal_execution_base_feedback_latest_raw_left,
        goal_execution_base_feedback_latest_raw_right: latestPlainFields.goal_execution_base_feedback_latest_raw_right,
      };
      const goalExecutionGoalSucceeded = goalExecutionKeyValues.status === "goal_succeeded"
        || goalExecutionKeyValues.result_status === "succeeded";
      const goalExecutionWheelRerunNeeded = goalExecutionGoalSucceeded
        && goalExecutionKeyValues.nav2_goal_execution_proven !== "true";
      const responseBody: RobotControlNavGoalExecutionLatestResponse = {
        ...fallbackBase,
        proxy_status: remote.ok && dangerous.length === 0 ? "latest_loaded" : "latest_failed",
        remote_http_status: remote.status,
        status: remote.ok ? "loaded_fail_closed_summary" : "blocked",
        goal_execution_key_values: goalExecutionKeyValues,
        latest_key_values: latestKeyValues,
        goal_execution_status: goalExecutionKeyValues.status ?? "not_loaded",
        result_status: goalExecutionKeyValues.result_status ?? "not_loaded",
        nav2_goal_execution_proven: goalExecutionKeyValues.nav2_goal_execution_proven ?? "not_loaded",
        execution_proof_gap: goalExecutionKeyValues.execution_proof_gap ?? "not_loaded",
        goal_execution_hil_pass: goalExecutionKeyValues.hil_pass ?? "not_loaded",
        goal_execution_robot_control_executed: goalExecutionKeyValues.robot_control_executed ?? "not_loaded",
        goal_execution_feedback_sample_count: goalExecutionKeyValues.feedback_sample_count ?? "not_loaded",
        goal_execution_base_feedback_sample_count: goalExecutionKeyValues.base_feedback_sample_count ?? "not_loaded",
        goal_execution_base_feedback_nonzero_sample_count: goalExecutionKeyValues.base_feedback_nonzero_sample_count ?? "not_loaded",
        goal_execution_goal_succeeded: String(goalExecutionGoalSucceeded),
        goal_execution_wheel_rerun_needed: String(goalExecutionWheelRerunNeeded),
        goal_execution_minimal_precheck_safety_only: true,
        goal_execution_safety_confirm_required: false,
        goal_execution_camera_preflight_required: false,
        goal_execution_radar_preflight_required: false,
        goal_execution_operator_report_preflight_required: false,
        goal_execution_route_wysiwyg_preflight_required: false,
        fixed_goal_execution_endpoint: "/api/robot-control/nav2/goal/execute",
        fixed_goal_execution_latest_endpoint: "/api/robot-control/nav2/goal/execution/latest",
        ...latestPlainFields,
        plain_hint: latestPlainFields.execution_status_plain,
        failure_reason: dangerous.length > 0 ? `dangerous_true_field:${dangerous[0]}` : remote.ok ? "" : `latest_http_status_${remote.status}`,
        blocked_reasons: [
          ...(remote.ok ? [] : [`latest_http_status_${remote.status}`]),
          ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ],
        hard_dangerous_true_fields: dangerous,
        // latest 是只读回放，不会发起 NavigateToPose；历史执行事实只留在 goal_execution_key_values。
        robot_control_executed: false,
      };
      res.status(responseBody.proxy_status === "latest_loaded" ? 200 : 502).json(responseBody);
    } catch (error) {
      const reason = error instanceof Error ? shortText(error.message, "nav2_goal_execution_latest_failed") : "nav2_goal_execution_latest_failed";
      res.status(502).json({ ...fallbackBase, proxy_status: "latest_failed", failure_reason: reason, blocked_reasons: [reason] });
    }
  });

  workstationApp.get("/api/robot-control/delivery/latest", async (req, res) => {
    // delivery latest 只读交付 gate 最近结论，帮助现场补材料；不会提交 operator report 或确认送达。
    const sourceBaseUrl = robotControlReadOnlyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const fallbackBase: RobotControlDeliveryLatestResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
      proxy_status: "latest_rejected",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
      workstation_endpoint: "/api/robot-control/delivery/latest",
      remote_endpoint: "/api/delivery/latest",
      remote_http_status: null,
      status: "blocked",
      delivery_claim_ready: false,
      delivery_material_ready: false,
      delivery_key_values: {},
      delivery_material_refs: deliveryMaterialRefs(null),
      missing_required_material: [],
      delivery_missing_required_material: [],
      delivery_missing_required_material_count: 0,
      delivery_missing_required_material_plain: deliveryLatestMissingPlain(false, []),
      delivery_operator_evidence_ref: "",
      delivery_nav2_status: "not_loaded",
      delivery_nav2_result_status: "not_loaded",
      delivery_nav2_feedback_sample_count: "0",
      delivery_latest_readback_only: true,
      delivery_complete_sends_motion: false,
      failure_reason: normalized.ok ? "" : normalized.reason,
      blocked_reasons: normalized.ok ? [] : [normalized.reason],
      hard_dangerous_true_fields: [],
    };
    if (!normalized.ok) {
      res.status(400).json(fallbackBase);
      return;
    }
    try {
      const remote = await fetch(endpointUrl(normalized.normalized, "/api/delivery/latest"), {
        method: "GET",
        signal: AbortSignal.timeout(10000),
      });
      const remotePayload = asRecord(await remote.json().catch(() => null));
      const latestResult = asRecord(remotePayload?.latest_result) ?? remotePayload;
      const deliveryKeyValues = deliveryCompleteKeyValues(remotePayload);
      const missingMaterial = deliveryMissingRequiredMaterial(
        latestResult?.missing_required_material,
        remotePayload?.missing_required_material,
        deliveryKeyValues.missing_required_material,
      );
      const dangerous = scanDangerousTrueFields(remotePayload).filter(
        (field) =>
          field !== "delivery_success" &&
          !field.endsWith(".delivery_success"),
      );
      const remoteDeliverySuccess = remotePayload?.delivery_success === true || latestResult?.delivery_success === true;
      const responseBody: RobotControlDeliveryLatestResponse = {
        ...fallbackBase,
        proxy_status: remote.ok && dangerous.length === 0 ? "latest_loaded" : "latest_failed",
        proof_status: remoteDeliverySuccess ? "proven" : "not_proven",
        remote_http_status: remote.status,
        status: remoteDeliverySuccess ? "delivery_success_confirmed" : remote.ok ? "loaded_fail_closed_summary" : "blocked",
        delivery_success: remoteDeliverySuccess,
        delivery_claim_ready: remoteDeliverySuccess,
        delivery_material_ready: missingMaterial.length === 0,
        delivery_key_values: deliveryKeyValues,
        delivery_material_refs: deliveryMaterialRefs(remotePayload),
        missing_required_material: missingMaterial,
        delivery_missing_required_material: missingMaterial,
        delivery_missing_required_material_count: missingMaterial.length,
        delivery_missing_required_material_plain: deliveryLatestMissingPlain(remoteDeliverySuccess, missingMaterial),
        delivery_operator_evidence_ref: deliveryKeyValues.operator_evidence_ref || "",
        delivery_nav2_status: deliveryKeyValues.nav2_status || "not_loaded",
        delivery_nav2_result_status: deliveryKeyValues.nav2_result_status || "not_loaded",
        delivery_nav2_feedback_sample_count: deliveryKeyValues.nav2_feedback_sample_count || "0",
        delivery_latest_readback_only: true,
        delivery_complete_sends_motion: false,
        failure_reason: dangerous.length > 0 ? `dangerous_true_field:${dangerous[0]}` : remote.ok ? "" : `delivery_latest_http_status_${remote.status}`,
        blocked_reasons: [
          ...(remote.ok ? [] : [`delivery_latest_http_status_${remote.status}`]),
          ...missingMaterial,
          ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ],
        hard_dangerous_true_fields: dangerous,
      };
      res.status(responseBody.proxy_status === "latest_loaded" ? 200 : 502).json(responseBody);
    } catch (error) {
      const reason = error instanceof Error ? shortText(error.message, "delivery_latest_failed") : "delivery_latest_failed";
      res.status(502).json({ ...fallbackBase, proxy_status: "latest_failed", failure_reason: reason, blocked_reasons: [reason] });
    }
  });

  workstationApp.post("/api/robot-control/delivery/check", async (req, res) => {
    // 缺口复算固定 confirm=false；只让上位机用当前 Nav2/operator report 重新生成 blocked 缺项。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const requestBody: RobotControlDeliveryCompleteRequest = {
      confirm_delivery_completion: false,
      delivery_evidence_ref: "delivery-gap-check-not-confirmed",
      operator_notes: "PC delivery gap check only; confirm_delivery_completion=false so this cannot produce delivery success.",
    };
    const fallbackBase: RobotControlDeliveryGapCheckResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_delivery_gap_check_proxy.v1",
      proxy_status: "check_rejected",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
      workstation_endpoint: "/api/robot-control/delivery/check",
      remote_endpoint: "/api/delivery/complete",
      remote_http_status: null,
      status: "blocked",
      request_body: requestBody,
      delivery_key_values: {},
      missing_required_material: [],
      failure_reason: normalized.ok ? "" : normalized.reason,
      blocked_reasons: normalized.ok ? [] : [normalized.reason],
      hard_dangerous_true_fields: [],
    };
    if (!normalized.ok) {
      res.status(400).json(fallbackBase);
      return;
    }
    try {
      const remote = await fetch(endpointUrl(normalized.normalized, "/api/delivery/complete"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
        signal: AbortSignal.timeout(15000),
      });
      const remotePayload = asRecord(await remote.json().catch(() => null));
      const missingMaterial = Array.isArray(remotePayload?.missing_required_material)
        ? remotePayload.missing_required_material.map((item) => shortText(item, "")).filter(Boolean)
        : [];
      const dangerous = scanDangerousTrueFields(remotePayload);
      const responseBody: RobotControlDeliveryGapCheckResponse = {
        ...fallbackBase,
        proxy_status: remote.ok && dangerous.length === 0 ? "check_loaded" : "check_failed",
        remote_http_status: remote.status,
        status: remote.ok ? "loaded_fail_closed_summary" : "blocked",
        delivery_key_values: deliveryCompleteKeyValues(remotePayload),
        missing_required_material: missingMaterial,
        failure_reason: dangerous.length > 0 ? `dangerous_true_field:${dangerous[0]}` : remote.ok ? "" : `delivery_check_http_status_${remote.status}`,
        blocked_reasons: [
          ...(remote.ok ? [] : [`delivery_check_http_status_${remote.status}`]),
          ...missingMaterial,
          ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ],
        hard_dangerous_true_fields: dangerous,
      };
      res.status(responseBody.proxy_status === "check_loaded" ? 200 : 502).json(responseBody);
    } catch (error) {
      const reason = error instanceof Error ? shortText(error.message, "delivery_check_failed") : "delivery_check_failed";
      res.status(502).json({ ...fallbackBase, proxy_status: "check_failed", failure_reason: reason, blocked_reasons: [reason] });
    }
  });

  workstationApp.post("/api/robot-control/delivery/complete", async (req, res) => {
    // 交付完成只调用固定 gate；不会发送 Nav2 goal、manual、stop 或底盘运动请求。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const payload = asRecord(req.body);
    const confirmDeliveryCompletion = payload?.confirm_delivery_completion === true;
    const requestBody = {
      confirm_delivery_completion: confirmDeliveryCompletion,
      delivery_evidence_ref: shortText(payload?.delivery_evidence_ref, ""),
      operator_notes: shortText(payload?.operator_notes, ""),
    };
    const fallbackBase: RobotControlDeliveryCompleteResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_delivery_complete_proxy.v1",
      proxy_status: "completion_rejected",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
      workstation_endpoint: "/api/robot-control/delivery/complete",
      remote_endpoint: "/api/delivery/complete",
      remote_http_status: null,
      status: "blocked",
      request_body: requestBody,
      delivery_key_values: {},
      missing_required_material: [],
      failure_reason: normalized.ok ? "" : normalized.reason,
      blocked_reasons: normalized.ok ? [] : [normalized.reason],
      hard_dangerous_true_fields: [],
    };
    if (!normalized.ok) {
      res.status(400).json(fallbackBase);
      return;
    }
    if (!confirmDeliveryCompletion) {
      res.status(400).json({
        ...fallbackBase,
        failure_reason: "confirm_delivery_completion_required",
        blocked_reasons: ["confirm_delivery_completion_required"],
      });
      return;
    }
    try {
      const remote = await fetch(endpointUrl(normalized.normalized, "/api/delivery/complete"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
        signal: AbortSignal.timeout(15000),
      });
      const remotePayload = asRecord(await remote.json().catch(() => null));
      const missingMaterial = Array.isArray(remotePayload?.missing_required_material)
        ? remotePayload.missing_required_material.map((item) => shortText(item, "")).filter(Boolean)
        : [];
      const dangerous = scanDangerousTrueFields(remotePayload).filter(
        (field) =>
          field !== "delivery_success" &&
          !field.endsWith(".delivery_success"),
      );
      const remoteDeliverySuccess = remotePayload?.delivery_success === true;
      const responseBody: RobotControlDeliveryCompleteResponse = {
        ...fallbackBase,
        proxy_status: remote.ok && dangerous.length === 0 ? "completion_forwarded" : "completion_failed",
        proof_status: remoteDeliverySuccess ? "proven" : "not_proven",
        remote_http_status: remote.status,
        status: remoteDeliverySuccess ? "delivery_success_confirmed" : remote.ok ? "loaded_fail_closed_summary" : "blocked",
        delivery_success: remoteDeliverySuccess,
        delivery_key_values: deliveryCompleteKeyValues(remotePayload),
        missing_required_material: missingMaterial,
        failure_reason: dangerous.length > 0 ? `dangerous_true_field:${dangerous[0]}` : remote.ok ? "" : `delivery_complete_http_status_${remote.status}`,
        blocked_reasons: [
          ...(remote.ok ? [] : [`delivery_complete_http_status_${remote.status}`]),
          ...missingMaterial,
          ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ],
        hard_dangerous_true_fields: dangerous,
      };
      res.status(responseBody.proxy_status === "completion_forwarded" ? 200 : 502).json(responseBody);
    } catch (error) {
      const reason = error instanceof Error ? shortText(error.message, "delivery_complete_failed") : "delivery_complete_failed";
      res.status(502).json({ ...fallbackBase, proxy_status: "completion_failed", failure_reason: reason, blocked_reasons: [reason] });
    }
  });

  workstationApp.post("/api/robot-control/localize/reset", async (req, res) => {
    // 定位 reset 只转发固定 /api/localize/reset body；浏览器不能传 initialpose 或任意 endpoint。
    const response = await buildLocalizationResetProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  workstationApp.get("/api/robot-control/map/list", async (req, res) => {
    // Map list 是固定 GET 代理；它只读取地图 artifact 候选，不开放任意 Robot API endpoint。
    const response = await buildMapLifecycleProxy(robotControlReadOnlyQueryBaseUrl(req.query.baseUrl), "list");
    res.status(mapLifecycleStatusCode(response.proxy_status)).json(response);
  });

  workstationApp.get("/api/robot-control/map/preview", async (req, res) => {
    // Map preview 只读取固定上位机 /api/map/preview；不会启动建图、Nav2、底盘或串口。
    const response = await buildMapPreviewProxy(robotControlReadOnlyQueryBaseUrl(req.query.baseUrl));
    res.status(response.proxy_status === "preview_forwarded" ? 200 : response.proxy_status === "preview_rejected" ? 400 : 502).json(response);
  });

  ([
    ["start", "/api/robot-control/map/start"],
    ["save", "/api/robot-control/map/save"],
    ["reset", "/api/robot-control/map/reset"],
  ] as Array<[RobotControlMapLifecycleAction, string]>).forEach(([action, route]) => {
    workstationApp.post(route, async (req, res) => {
      // lifecycle POST 只能转发到 action 对应的固定上位机 endpoint，body 由 helper 做短字段白名单。
      const response = await buildMapLifecycleProxy(robotControlFixedProxyQueryBaseUrl(req.query.baseUrl), action, req.body);
      res.status(mapLifecycleStatusCode(response.proxy_status)).json(response);
    });
  });

  workstationApp.get("/api/robot-control/free-roam/autonomy/latest", async (req, res) => {
    // 自动扫图 latest 是只读 runtime artifact 代理；不启动/停止状态机，也不发布任何速度。
    const sourceBaseUrl = robotControlReadOnlyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const fallbackBase: RobotControlFreeRoamAutonomyLatestResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_free_roam_autonomy_latest_proxy.v1",
      proxy_status: "latest_rejected",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.ok ? normalized.normalized.toString().replace(/\/$/, "") : "not_loaded",
      workstation_endpoint: "/api/robot-control/free-roam/autonomy/latest",
      remote_endpoint: "/api/free-roam/autonomy/latest",
      remote_method: "GET",
      remote_http_status: null,
      status: "blocked",
      readback_only: true,
      free_roam_latest_readback_only: true,
      sends_motion_when_clicked: false,
      starts_camera_exclusive_capture: false,
      starts_radar_lifecycle: false,
      starts_nav2: false,
      starts_manual: false,
      starts_keyboard: false,
      starts_free_roam: false,
      starts_map_runtime: false,
      submits_delivery: false,
      stops_motion: false,
      plain_hint: "自由移动暂不可启动；先连接上车自由移动状态机并确认停止兜底。建图验收未就绪；还在等待自由移动状态机和建图材料。",
      next_action_plain: "先连接上车自由移动状态机，并确认停止兜底可用。先连接上车自由移动状态机，并继续读取建图验收材料。",
      runtime_status: "not_loaded",
      decision_state: "not_loaded",
      decision_reason: normalized.ok ? "not_loaded" : normalized.reason,
      stop_request_pending: false,
      free_roam_stop_request_pending: false,
      start_will_clear_stop_request: false,
      start_clears_stop_request_not_blocking: false,
      motion_start_blocked_by_stop_request: false,
      stop_request_status_plain: "停止请求状态未读到；先恢复上车连接。",
      safety_confirmed: false,
      free_move_ready: false,
      free_move_start_ready: false,
      free_roam_motion_start_ready: false,
      motion_start_ready: false,
      free_roam_motion_ready: false,
      motion_ready: false,
      motion_without_radar_allowed: false,
      free_move_without_camera_allowed: false,
      free_roam_mapping_start_ready: false,
      mapping_start_ready: false,
      free_roam_mapping_start_missing_reasons: ["not_checked"],
      mapping_start_missing_reasons: ["not_checked"],
      free_roam_mapping_start_plain: "建图启动未就绪；还在等待上车自由移动状态机。",
      free_roam_mapping_start_next_action: "先连接上车自由移动状态机，并继续读取相机和雷达。",
      free_roam_mapping_ready: false,
      free_roam_mapping_missing_reasons: ["not_checked"],
      mapping_ready: false,
      mapping_missing_reasons: ["not_checked"],
      missing_capabilities: ["not_checked"],
      mapping_readiness_ready: false,
      mapping_blocked_reasons: ["not_checked"],
      motion_readiness_plain: "自由移动未就绪；先连接上车状态机并确认停止兜底。",
      free_move_start_status_plain: "自由移动暂不可启动；先连接上车自由移动状态机并确认停止兜底。",
      motion_runtime_status_plain: "当前未在自由移动运行态；上车自由移动状态机还未就绪。",
      mapping_acceptance_status_plain: "建图验收未就绪；还在等待自由移动状态机和建图材料。",
      mapping_readiness_plain: "建图验收未就绪；还在等待上车状态机。",
      motion_next_action_plain: "先连接上车自由移动状态机，并确认停止兜底可用。",
      mapping_next_action_plain: "先连接上车自由移动状态机，并继续读取建图验收材料。",
      latest_key_values: {},
      failure_reason: normalized.ok ? "" : normalized.reason,
      blocked_reasons: normalized.ok ? [] : [normalized.reason],
      hard_dangerous_true_fields: [],
    };
    if (!normalized.ok) {
      res.status(400).json(fallbackBase);
      return;
    }
    try {
      const remote = await fetch(endpointUrl(normalized.normalized, "/api/free-roam/autonomy/latest"), {
        method: "GET",
        signal: AbortSignal.timeout(10000),
      });
      const remotePayload = asRecord(await remote.json().catch(() => null));
      const dangerous = scanDangerousTrueFields(remotePayload).filter(
        (field) => field !== "cmd_vel_publish_enabled" && !field.endsWith(".cmd_vel_publish_enabled"),
      );
      const latestKeyValues = freeRoamAutonomyLatestKeyValues(remotePayload);
      const latestLoaded = remote.ok && dangerous.length === 0;
      const latestReadiness = freeRoamLatestReadinessFromKeyValues(latestKeyValues, latestLoaded);
      const responseBody: RobotControlFreeRoamAutonomyLatestResponse = {
        ...fallbackBase,
        proxy_status: latestLoaded ? "latest_loaded" : "latest_failed",
        remote_http_status: remote.status,
        status: remote.ok ? "loaded_fail_closed_summary" : "blocked",
        ...latestReadiness,
        sends_commands: false,
        sends_motion_commands: false,
        latest_key_values: latestKeyValues,
        failure_reason: dangerous.length > 0 ? `dangerous_true_field:${dangerous[0]}` : remote.ok ? "" : `free_roam_autonomy_latest_http_status_${remote.status}`,
        blocked_reasons: [
          ...(remote.ok ? [] : [`free_roam_autonomy_latest_http_status_${remote.status}`]),
          ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ],
        hard_dangerous_true_fields: dangerous,
      };
      res.status(responseBody.proxy_status === "latest_loaded" ? 200 : 502).json(responseBody);
    } catch (error) {
      const reason = error instanceof Error ? shortText(error.message, "free_roam_autonomy_latest_failed") : "free_roam_autonomy_latest_failed";
      res.status(502).json({ ...fallbackBase, proxy_status: "latest_failed", failure_reason: reason, blocked_reasons: [reason] });
    }
  });

  workstationApp.post("/api/robot-control/free-roam/autonomy/start", async (req, res) => {
    // 自由移动 start 只能转固定上位机 endpoint；建图确认只是可选事实，不再阻止低速移动。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const requestBody = {
      confirm_operator_safety: req.body?.confirm_operator_safety === true,
      confirm_mapping_active: req.body?.confirm_mapping_active === true,
    };
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      const response = freeRoamAutonomyProxyFailure(
        sourceBaseUrl,
        "start",
        "/api/free-roam/autonomy/start",
        normalized.reason,
        requestBody,
      );
      res.status(400).json(response);
      return;
    }
    if (!requestBody.confirm_operator_safety) {
      const response = freeRoamAutonomyProxyFailure(
        sourceBaseUrl,
        "start",
        "/api/free-roam/autonomy/start",
        "missing_free_roam_operator_confirmation",
        requestBody,
      );
      res.status(400).json(response);
      return;
    }
    const remote = await fetchFixedRobotPostSummary(sourceBaseUrl, "/api/free-roam/autonomy/start", requestBody);
    const response = freeRoamAutonomyProxyResponse(sourceBaseUrl, "start", "/api/free-roam/autonomy/start", requestBody, remote);
    res.status(response.proxy_status === "autonomy_forwarded" ? 200 : response.proxy_status === "autonomy_rejected" ? 400 : 502).json(response);
  });

  workstationApp.post("/api/robot-control/free-roam/autonomy/stop", async (req, res) => {
    // stop 不需要确认，但仍只请求上车端状态机 stop，不发布浏览器侧速度。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      const response = freeRoamAutonomyProxyFailure(sourceBaseUrl, "stop", "/api/free-roam/autonomy/stop", normalized.reason, {});
      res.status(400).json(response);
      return;
    }
    const remote = await fetchFixedRobotPostSummary(sourceBaseUrl, "/api/free-roam/autonomy/stop", {});
    const response = freeRoamAutonomyProxyResponse(sourceBaseUrl, "stop", "/api/free-roam/autonomy/stop", {}, remote);
    res.status(response.proxy_status === "autonomy_forwarded" ? 200 : 502).json(response);
  });

  workstationApp.post("/api/robot-control/camera/offer", async (req, res) => {
    // camera offer 只允许本机 Node 代理固定上位机 endpoint，不开放任意 Robot API POST。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(unsafeProxyFailure(sourceBaseUrl, normalized.reason, "/api/camera/offer"));
      return;
    }
    const payload = asRecord(req.body);
    const sdp = typeof payload?.sdp === "string" ? payload.sdp.trim() : "";
    const type = payload?.type === "offer" ? "offer" : "";
    if (!payload || !sdp || type !== "offer") {
      res.status(400).json(unsafeProxyFailure(sourceBaseUrl, "invalid_offer_request", "/api/camera/offer"));
      return;
    }
    const remote = await fetchCameraProxySummary(sourceBaseUrl, "/api/camera/offer", { type, sdp });
    if (remote.error) {
      res.status(502).json(unsafeProxyFailure(sourceBaseUrl, remote.error, "/api/camera/offer"));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload);
    const answer = safeAnswerFromPayload(remote.payload);
    const responseBody: RobotControlCameraOfferProxyResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_camera_offer_proxy.v1",
      proxy_status:
        remote.remote_http_status === 200 && dangerous.length === 0 && answer ? "offer_forwarded" : "offer_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/camera/offer",
      remote_http_status: remote.remote_http_status,
      status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "loaded" : "blocked"),
      peer_id: peerIdText(remote.payload?.peer_id),
      answer,
      error: shortText(remote.payload?.error, ""),
      failure_reason:
        dangerous.length > 0
          ? `dangerous_true_field:${dangerous[0]}`
          : !answer
            ? "remote_answer_missing"
            : remote.remote_http_status === 200
              ? ""
              : `offer_http_status_${remote.remote_http_status}`,
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`offer_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ...(answer ? [] : ["remote_answer_missing"]),
      ],
    };
    res.status(responseBody.proxy_status === "offer_forwarded" ? 200 : 502).json(responseBody);
  });

  workstationApp.post("/api/robot-control/camera/peers/:peerId/close", async (req, res) => {
    // peer cleanup 只允许关闭已知 peer_id；不接受任意路径、query 拼接或控制类 POST。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const peerId = peerIdText(req.params.peerId ?? "");
    if (!normalized.ok) {
      res
        .status(400)
        .json(unsafeProxyFailure(sourceBaseUrl, normalized.reason, "/api/camera/peers/{peer_id}/close", peerId));
      return;
    }
    if (!peerId) {
      res
        .status(400)
        .json(unsafeProxyFailure(sourceBaseUrl, "peer_id_invalid", "/api/camera/peers/{peer_id}/close", peerId));
      return;
    }
    const remote = await fetchCameraProxySummary(sourceBaseUrl, `/api/camera/peers/${peerId}/close`, {});
    if (remote.error) {
      res
        .status(502)
        .json(unsafeProxyFailure(sourceBaseUrl, remote.error, "/api/camera/peers/{peer_id}/close", peerId));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload);
    const responseBody: RobotControlCameraCloseProxyResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_camera_close_proxy.v1",
      proxy_status:
        remote.remote_http_status === 200 && dangerous.length === 0 ? "peer_closed" : "close_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/camera/peers/{peer_id}/close",
      remote_http_status: remote.remote_http_status,
      peer_id: peerId,
      status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "closed" : "blocked"),
      error: shortText(remote.payload?.error, ""),
      failure_reason:
        dangerous.length > 0
          ? `dangerous_true_field:${dangerous[0]}`
          : remote.remote_http_status === 200
            ? ""
            : `close_http_status_${remote.remote_http_status}`,
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`close_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
      ],
    };
    res.status(responseBody.proxy_status === "peer_closed" ? 200 : 502).json(responseBody);
  });

  workstationApp.get("/api/robot-control/camera/mjpeg/status", async (req, res) => {
    // 只读共享预览状态；不会创建 MJPEG client，也不会触发上位机 camera reader。
    const sourceBaseUrl = robotControlReadOnlyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(cameraMjpegStatusResponse(sourceBaseUrl, null, null, normalized.reason));
      return;
    }
    const relayKey = cameraMjpegRelayKey(normalized.normalized);
    const sourceFailure = await cameraSourceFirstFrameFailureForStatus(normalized.normalized);
    res.json(cameraMjpegStatusResponse(sourceBaseUrl, normalized.normalized, cameraMjpegRelays.get(relayKey) ?? null, "", sourceFailure));
  });

  workstationApp.get("/api/robot-control/camera/mjpeg", async (req, res) => {
    // MJPEG fallback 只代理固定 camera stream；PC Node 只开一条上游流，再广播给多个浏览器。
    const sourceBaseUrl = robotControlReadOnlyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json({ error: normalized.reason, safe_to_control: false, robot_control_executed: false });
      return;
    }
    const relay = getCameraMjpegRelay(normalized.normalized);
    const client: CameraMjpegRelayClient = {
      id: nextCameraMjpegRelayClientId,
      response: res,
      headersStarted: false,
    };
    nextCameraMjpegRelayClientId += 1;
    relay.clients.add(client);
    res.on("close", () => removeCameraMjpegClient(relay, client));
    if (relay.contentType) {
      startCameraMjpegClient(client, relay.contentType);
      writeCachedCameraMjpegFrame(relay, client);
    }
    void ensureCameraMjpegRelayStarted(relay);
  });

  workstationApp.post("/api/robot-control/camera/first-frame/probe", async (req, res) => {
    // 首帧探针只转发固定白名单 body；不能让浏览器指定任意设备或命令。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(cameraProbeFailure(sourceBaseUrl, normalized.reason));
      return;
    }
    const includeBackendSmoke = req.query.backendSmoke === "1" || req.query.backendSmoke === "true";
    const sourceFailurePromise = cameraSourceFirstFrameFailureForStatus(normalized.normalized);
    // 默认保持快速首帧探针；只有用户主动请求深度诊断时才启动 ffmpeg/v4l2-ctl 后端矩阵。
    const remote = await fetchCameraProxySummary(
      sourceBaseUrl,
      "/api/camera/first-frame/probe",
      {
        include_backend_smoke: includeBackendSmoke,
        auto_format_fallback: true,
        timeout_s: 3,
        read_call_timeout_s: 4,
      },
      includeBackendSmoke ? CAMERA_FIRST_FRAME_BACKEND_SMOKE_TIMEOUT_MS : CAMERA_FIRST_FRAME_PROBE_TIMEOUT_MS,
    );
    const sourceFailure = await sourceFailurePromise;
    if (remote.error) {
      const probeValues = cameraProbeKeyValues(null);
      const failureBody = {
        ...cameraProbeFailure(sourceBaseUrl, remote.error),
        proxy_status: "probe_failed" as const,
        normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
        probe_key_values: probeValues,
        ...cameraProbeDiagnosticAliases(probeValues, sourceFailure),
      };
      cameraFirstFrameProbeOverlays.set(cameraMjpegRelayKey(normalized.normalized), cameraProbeOverlayFromResponse(failureBody));
      // 首帧失败是现场诊断材料，不是 PC 代理传输失败；保持 HTTP 200，避免 curl -fsS 隐藏换线/换口提示。
      res.status(200).json(failureBody);
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload);
    const probeValues = cameraProbeKeyValues(remote.payload);
    const status = shortText(remote.payload?.status, remote.remote_http_status === 200 ? "loaded" : "blocked");
    const failureReason =
      dangerous.length > 0
        ? `dangerous_true_field:${dangerous[0]}`
        : probeValues.failure_reason !== "none"
          ? probeValues.failure_reason
          : remote.remote_http_status === 200
            ? ""
            : `probe_http_status_${remote.remote_http_status}`;
    const responseBody: RobotControlCameraFirstFrameProbeProxyResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      ...CAMERA_FIRST_FRAME_PROBE_NO_MOTION_FLAGS,
      proxy_status:
        remote.remote_http_status === 200 && dangerous.length === 0 ? "probe_forwarded" : "probe_failed",
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/camera/first-frame/probe",
      remote_http_status: remote.remote_http_status,
      status,
      probe_key_values: probeValues,
      failure_reason: failureReason,
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`probe_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ...(failureReason && dangerous.length === 0 ? [failureReason] : []),
      ],
      ...cameraProbeDiagnosticAliases(probeValues, sourceFailure, dangerous),
      hard_dangerous_true_fields: dangerous,
      robot_control_executed: false,
    };
    cameraFirstFrameProbeOverlays.set(cameraMjpegRelayKey(normalized.normalized), cameraProbeOverlayFromResponse(responseBody));
    // 上车返回 503/timeout 时仍把完整 fail-closed JSON 交给普通脚本读取，真实失败状态保留在 body 字段。
    res.status(200).json(responseBody);
  });

  workstationApp.post("/api/robot-control/camera/usb-recovery", async (req, res) => {
    // USB recovery 是相机链路恢复动作：允许重启相机服务和 reauthorize USB，但固定不发车。
    const sourceBaseUrl = robotControlFixedProxyQueryBaseUrl(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(cameraUsbRecoveryFailure(sourceBaseUrl, normalized.reason));
      return;
    }
    const requestBody = safeCameraUsbRecoveryBody(req.body);
    const remote = await fetchCameraProxySummary(
      sourceBaseUrl,
      "/api/camera/usb-recovery",
      requestBody,
      CAMERA_USB_RECOVERY_TIMEOUT_MS,
    );
    if (remote.error) {
      res.status(200).json({
        ...cameraUsbRecoveryFailure(sourceBaseUrl, remote.error),
        proxy_status: "recovery_failed",
        normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
        request_body: requestBody,
      });
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload);
    const frameObserved = remote.payload?.frame_observed === true;
    const status = shortText(remote.payload?.status, remote.remote_http_status === 200 ? "loaded" : "blocked");
    const failureReason = dangerous.length > 0
      ? `dangerous_true_field:${dangerous[0]}`
      : frameObserved
        ? ""
        : shortText(remote.payload?.stream_failure_class ?? remote.payload?.next_action ?? `recovery_http_status_${remote.remote_http_status}`, "recovery_failed");
    res.status(200).json({
      schema: "trashbot.pc_tools_workstation.robot_control_camera_usb_recovery_proxy.v1",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      ...CAMERA_USB_RECOVERY_NO_MOTION_FLAGS,
      proxy_status: remote.remote_http_status === 200 && dangerous.length === 0 ? "recovery_forwarded" : "recovery_failed",
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      workstation_endpoint: "/api/robot-control/camera/usb-recovery",
      remote_endpoint: "/api/camera/usb-recovery",
      remote_http_status: remote.remote_http_status,
      request_body: requestBody,
      status,
      frame_observed: frameObserved,
      usb_video_speed: shortText(remote.payload?.usb_video_speed, "not_loaded"),
      stream_failure_class: shortText(remote.payload?.stream_failure_class, "not_loaded"),
      next_action: shortText(remote.payload?.next_action, "not_loaded"),
      next_action_plain: shortText(remote.payload?.next_action_plain, "not_loaded"),
      usb_high_speed_observed: remote.payload?.usb_high_speed_observed === true,
      opens_camera_for_recovery: true,
      recovery_payload: remote.payload ?? {},
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`recovery_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ...(failureReason ? [failureReason] : []),
      ],
      failure_reason: failureReason,
      hard_dangerous_true_fields: dangerous,
      robot_control_executed: false,
    });
  });

  workstationApp.get("/api/proof-boundary", (_req, res) => {
    // proof boundary 是 UI 的安全锚点，所有控制与交付成功声明都固定关闭。
    res.json(buildProofBoundary());
  });

  workstationApp.use(express.static(DIST_ROOT));

  workstationApp.use((_req, res) => {
    // 构建后可由同一 Node 进程托管静态 UI；缺 dist 时仍返回明确失败。
    res.sendFile(path.join(DIST_ROOT, "index.html"), (error) => {
      if (error) {
        res.status(404).json({
          ...buildProofBoundary(),
          status: "dist_not_built_not_proven",
        });
      }
    });
  });

  return workstationApp;
}

export const app = createWorkstationApp();
let cliServer: ReturnType<typeof app.listen> | null = null;

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  // 直接让 Express 绑定最终端口；额外 probe 在 tsx 启动链路下会制造已监听却报占用的误导日志。
  let cliServerListening = false;
  cliServer = app.listen(PORT, HOST, () => {
    cliServerListening = true;
    console.log(`pc-tools workstation API listening on ${workstationListenAddress()}`);
  });
  cliServer.on("error", (error: NodeJS.ErrnoException) => {
    if (cliServerListening && error.code === "EADDRINUSE") {
      // tsx/macOS 偶发在 listening 后再抛 duplicate EADDRINUSE；端口已可用时直接静默，避免现场误判启动失败。
      return;
    }
    console.error(listenFailureHint(error));
    process.exitCode = 1;
  });
}
