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
  buildMapProofRefreshProxy,
  buildNavGoalPreflightProxy,
  buildNav2NoMotionProofRefreshProxy,
  buildOperatorReportProxy,
  buildRobotControlSummary,
  buildRouteDebugSummary,
  buildTrainingLabelingResponse,
} from "./catalog";
import {
  endpointUrl,
  normalizeRobotApiBaseUrl,
  ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS,
  ROBOT_CONTROL_HIL_CHECKLIST,
  ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS,
  ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
  fetchFirstJogOperatorReportPreflight,
  fetchManualMotionOperatorReportPreflight,
  notRequiredOperatorReportPreflight,
  scanDangerousTrueFields,
} from "./robotControlSummary";
import type {
  RobotControlBaseCommandProxyResponse,
  RobotControlBaseCommandRequest,
  RobotControlBaseFeedbackSamplesProxyResponse,
  RobotControlCameraAnswerSummary,
  RobotControlCameraCloseProxyResponse,
  RobotControlCameraFirstFrameProbeProxyResponse,
  RobotControlCameraOfferProxyResponse,
  RobotControlEvidenceCaptureEndpointId,
  RobotControlEvidenceCapturePhase,
  RobotControlEvidenceCaptureStatus,
  RobotControlEvidenceEndpointCapture,
  RobotControlEvidenceReadbackSummary,
  RobotControlOperatorReportPreflight,
  RobotControlMapLifecycleAction,
  RobotControlRadarLifecycleAction,
} from "../shared/contracts";

const PORT = Number(process.env.PORT ?? 8787);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_ROOT = path.resolve(__dirname, "../../dist");

function queryString(value: unknown): string {
  // Express query 可能是数组或对象；只接受单个字符串，其他形态 fail closed 为空。
  // 为空会让 catalog 返回 not_proven/blocked，而不是把异常 query 当路径读取。
  return typeof value === "string" ? value : "";
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // camera proxy 只接受/返回 JSON object；数组或字符串一律 fail-closed。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function shortText(value: unknown, fallback: string): string {
  // 响应只保留短摘要，避免把远端 traceback、路径或超长文本直接暴露给 UI。
  return typeof value === "string" && value.trim() ? value.trim().slice(0, 240) : fallback;
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

function cameraProbeKeyValues(payload: Record<string, unknown> | null): RobotControlCameraFirstFrameProbeProxyResponse["probe_key_values"] {
  // 上位机把真实脚本输出放在 probe_payload；没有时按顶层兼容，便于旧 artifact 测试。
  const probePayload = asRecord(payload?.probe_payload) ?? payload;
  const metrics = asRecord(probePayload?.frame_metrics);
  const backendSmoke = asRecord(probePayload?.backend_smoke);
  const backendAttempts = Array.isArray(backendSmoke?.attempts) ? backendSmoke.attempts : [];
  return {
    schema: shortValue(probePayload?.schema),
    device: shortValue(probePayload?.device),
    requested_fourcc: shortValue(probePayload?.requested_fourcc, "default"),
    open_ok: shortValue(probePayload?.open_ok),
    read_ok: shortValue(probePayload?.read_ok),
    first_frame_timeout: shortValue(probePayload?.first_frame_timeout),
    failure_reason: shortValue(probePayload?.failure_reason, "none"),
    visible_content_proven: shortValue(probePayload?.visible_content_proven),
    elapsed_ms: shortValue(probePayload?.elapsed_ms ?? payload?.elapsed_ms),
    mean_luma: shortValue(metrics?.mean_luma, "not_available"),
    non_black_ratio: shortValue(metrics?.non_black_ratio, "not_available"),
    backend_smoke_status: shortValue(backendSmoke?.status, "not_requested"),
    backend_frame_observed: shortValue(backendSmoke?.frame_observed, "false"),
    backend_attempts: shortValue(backendAttempts.length),
  };
}

function baseFeedbackSampleKeyValues(payload: Record<string, unknown> | null): RobotControlBaseFeedbackSamplesProxyResponse["sample_key_values"] {
  // 反馈采集只展示样本摘要；原始串口帧留在上位机 artifact，避免 PC 页面误读为 HIL pass。
  const feedbackAck = asRecord(payload?.feedback_ack);
  return {
    schema: shortText(payload?.schema, "not_loaded"),
    requested_sample_count: shortValue(payload?.requested_sample_count),
    completed_sample_count: shortValue(payload?.completed_sample_count),
    t1001_observed_count: shortValue(payload?.t1001_observed_count),
    all_samples_observed_t1001: shortValue(payload?.all_samples_observed_t1001),
    partial_samples_observed_t1001: shortValue(payload?.partial_samples_observed_t1001),
    feedback_ack_t1001_observed: shortValue(feedbackAck?.t1001_observed),
    observed_feedback_types: shortValue(payload?.observed_feedback_types),
    sends_motion_commands: shortValue(payload?.sends_motion_commands),
    robot_control_executed: shortValue(payload?.robot_control_executed),
  };
}

function baseFeedbackSamplesFailure(sourceBaseUrl: string, reason: string): RobotControlBaseFeedbackSamplesProxyResponse {
  // 本机拒绝时不能触发任何串口请求；响应仍保持完整 fail-closed 形状。
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
    remote_endpoint: "/api/base/feedback-samples",
    remote_http_status: null,
    status: "blocked",
    sample_key_values: baseFeedbackSampleKeyValues(null),
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
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
  // 方向只接受固定白名单，避免前端把 manual proxy 变成任意运动字符串通道。
  return typeof value === "string" && ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS.includes(value as never)
    ? (value as RobotControlBaseCommandRequest["direction"])
    : null;
}

function mapLifecycleStatusCode(proxyStatus: "lifecycle_forwarded" | "lifecycle_rejected" | "lifecycle_failed"): number {
  // lifecycle 代理保留 HTTP 语义：本机拒绝是 400，上位机/危险字段失败是 502，固定代理成功是 200。
  if (proxyStatus === "lifecycle_forwarded") {
    return 200;
  }
  return proxyStatus === "lifecycle_rejected" ? 400 : 502;
}

function missingHilChecklist(confirmHilChecklist: boolean): string[] {
  // 本轮 checklist 只做完整确认 gate，不在 Node 端逐项收集现场真假，防止 UI 漂移。
  return confirmHilChecklist ? [] : ROBOT_CONTROL_HIL_CHECKLIST.map((item) => item.id);
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

const BASE_COMMAND_EVIDENCE_KEYS = [
  "schema",
  "status",
  "proof_status",
  "feedback_ack_status",
  "latest_t1001_observed_count",
  "latest_proof_status",
  "latest_result_status",
  "evidence_ref",
  "scan_once_observed",
  "scan_hz_observed",
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
): string[] {
  // gap 是下一步补证据清单，不是放行依据；stop 永远不是运动证明。
  if (commandKind === "stop") {
    return ["stop_command_not_motion_proof"];
  }
  const gaps = [
    preflightReason ? "motion_command_not_forwarded" : "",
    status === "captured" ? "" : "before_after_evidence_snapshot_incomplete",
    evidenceKeyTrue(afterReadback, "base_status", ["wheel_feedback_lr_nonzero_proven", "wheel_feedback_nonzero_observed"])
      || evidenceKeyTrue(afterReadback, "base_feedback_samples_latest", ["wheel_feedback_lr_nonzero_proven", "wheel_feedback_nonzero_observed"])
      ? ""
      : "wheel_feedback_lr_nonzero_not_proven",
    evidenceKeyTrue(afterReadback, "radar_status", ["physical_motion_lidar_delta_proven", "lidar_motion_delta_proven", "scan_delta_observed"])
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
    motion_evidence_gaps: buildMotionEvidenceGaps(commandKind, status, afterReadback, preflightReason),
  };
}

function blockedEvidenceCapture(commandKind: "manual" | "stop", reason: string): BaseCommandEvidenceCapture {
  // baseUrl 无法规范化时不能尝试任何远端 GET；响应仍显式写明采集被阻断。
  return buildEvidenceCapture(commandKind, [], reason);
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
      signal: AbortSignal.timeout(1500),
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
  // before/after 两个阶段并行读取固定 GET 列表；阶段之间仍保持顺序，便于和主请求对齐。
  return Promise.all(BASE_COMMAND_EVIDENCE_ENDPOINTS.map((endpoint) => fetchEvidenceEndpoint(baseUrl, phase, endpoint)));
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
    non_stop_requires_confirm_hil_checklist: true,
    hil_checklist_gate_status: isStop
      ? "stop_allowed_without_checklist"
      : confirmHilChecklist
        ? "manual_allowed"
        : "manual_blocked_missing_checklist",
    checklist_missing: isStop ? [] : missingHilChecklist(confirmHilChecklist),
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

async function fetchFixedRobotPostSummary(
  baseUrl: string,
  endpoint: "/api/base/manual" | "/api/base/stop",
  body: Record<string, unknown>,
): Promise<{ remote_http_status: number | null; payload: Record<string, unknown> | null; error: string }> {
  // 这里专门服务固定 base manual/stop 代理，不接受动态 endpoint，避免扩展成万能 POST 转发器。
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
      signal: AbortSignal.timeout(5000),
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

function cameraProbeFailure(sourceBaseUrl: string, reason: string): RobotControlCameraFirstFrameProbeProxyResponse {
  // 本机拒绝或 fetch 失败也返回完整合同，避免高级诊断分叉成异常栈展示。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "probe_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: "/api/camera/first-frame/probe",
    remote_http_status: null,
    status: "blocked",
    probe_key_values: cameraProbeKeyValues(null),
    failure_reason: reason,
    blocked_reasons: [reason],
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
    return {
      remote_http_status: null,
      payload: null,
      error: error instanceof Error ? shortText(error.message, "upper_api_unreachable") : "upper_api_unreachable",
    };
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
    // Robot Control V1 只读代理上位机 GET status/latest/readback，拒绝浏览器直连和危险 URL。
    res.json(await buildRobotControlSummary(queryString(req.query.baseUrl)));
  });

  workstationApp.post("/api/robot-control/base/first-jog", async (req, res) => {
    // 首次试动只解除“轮速/LiDAR delta 必须先存在”的循环；仍要求现场与可视材料。
    const sourceBaseUrl = queryString(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const payload = asRecord(req.body);
    const direction = allowedDirection(payload?.direction);
    const speed = finiteNumber(payload?.speed);
    const durationMs = finiteNumber(payload?.duration_ms);
    const confirmHilChecklist = payload?.confirm_hil_checklist === true;
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
    if (!confirmHilChecklist) {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "confirm_hil_checklist_required", direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    const operatorReportPreflight = await fetchFirstJogOperatorReportPreflight(normalized.normalized);
    if (operatorReportPreflight.status !== "passed") {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(
        sourceBaseUrl,
        "manual",
        "/api/base/manual",
        "first_jog_preflight_required",
        direction,
        speed,
        durationMs,
        confirmHilChecklist,
        evidenceCapture,
        operatorReportPreflight,
      ));
      return;
    }
    const clampedSpeed = clamp(speed, 0, ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS);
    const clampedDurationMs = clamp(durationMs, 0, ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS);
    const remote = await fetchFixedRobotPostSummary(sourceBaseUrl, "/api/base/manual", {
      direction,
      speed: clampedSpeed,
      duration_ms: clampedDurationMs,
      confirm_hil_checklist: true,
    });
    const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
    const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
    if (remote.error) {
      res.status(502).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", remote.error, direction, speed, durationMs, confirmHilChecklist, evidenceCapture, operatorReportPreflight));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload, "", BASE_COMMAND_FAIL_CLOSED_FIELDS);
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
      non_stop_requires_confirm_hil_checklist: true,
      hil_checklist_gate_status: "manual_allowed",
      checklist_missing: [],
      operator_report_preflight: operatorReportPreflight,
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
    // 点动代理只允许固定 manual endpoint；非 stop 动作必须明确通过 HIL checklist gate。
    const sourceBaseUrl = queryString(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const payload = asRecord(req.body);
    const direction = allowedDirection(payload?.direction);
    const speed = finiteNumber(payload?.speed);
    const durationMs = finiteNumber(payload?.duration_ms);
    const confirmHilChecklist = payload?.confirm_hil_checklist === true;
    if (!normalized.ok) {
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", normalized.reason, "stop", speed, durationMs, confirmHilChecklist));
      return;
    }
    const beforeEvidence = await captureEvidencePhase(normalized.normalized, "before");
    if (!direction) {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "direction_invalid", "stop", speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    if (direction === "stop") {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "direction_stop_use_stop_endpoint", direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    if (speed === null || durationMs === null) {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "manual_request_invalid_numbers", direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    if (!confirmHilChecklist) {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", "confirm_hil_checklist_required", direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    const operatorReportPreflight = await fetchManualMotionOperatorReportPreflight(normalized.normalized);
    if (operatorReportPreflight.status !== "passed") {
      const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
      const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
      res.status(400).json(baseCommandFailure(
        sourceBaseUrl,
        "manual",
        "/api/base/manual",
        "operator_report_preflight_required",
        direction,
        speed,
        durationMs,
        confirmHilChecklist,
        evidenceCapture,
        operatorReportPreflight,
      ));
      return;
    }

    const clampedSpeed = clamp(speed, 0, ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS);
    const clampedDurationMs = clamp(durationMs, 0, ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS);
    const remote = await fetchFixedRobotPostSummary(sourceBaseUrl, "/api/base/manual", {
      direction,
      speed: clampedSpeed,
      duration_ms: clampedDurationMs,
      confirm_hil_checklist: true,
    });
    const afterEvidence = await captureEvidencePhase(normalized.normalized, "after");
    const evidenceCapture = buildEvidenceCapture("manual", [...beforeEvidence, ...afterEvidence]);
    if (remote.error) {
      res.status(502).json(baseCommandFailure(sourceBaseUrl, "manual", "/api/base/manual", remote.error, direction, speed, durationMs, confirmHilChecklist, evidenceCapture));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload, "", BASE_COMMAND_FAIL_CLOSED_FIELDS);
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
      non_stop_requires_confirm_hil_checklist: true,
      hil_checklist_gate_status: "manual_allowed",
      checklist_missing: [],
      operator_report_preflight: operatorReportPreflight,
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
    const sourceBaseUrl = queryString(req.query.baseUrl);
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
      non_stop_requires_confirm_hil_checklist: true,
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
    const sourceBaseUrl = queryString(req.query.baseUrl);
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
    const dangerous = scanDangerousTrueFields(remote.payload, "", BASE_FEEDBACK_SAMPLE_FAIL_CLOSED_FIELDS);
    const responseBody: RobotControlBaseFeedbackSamplesProxyResponse = {
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
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/base/feedback-samples",
      remote_http_status: remote.remote_http_status,
      status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "loaded" : "blocked"),
      sample_key_values: baseFeedbackSampleKeyValues(remote.payload),
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
    res.status(responseBody.proxy_status === "samples_forwarded" ? 200 : 502).json(responseBody);
  });

  workstationApp.post("/api/robot-control/operator/report", async (req, res) => {
    // 现场材料提交只转发固定 /api/operator/report；不开放底盘、Nav2、cmd_vel、map/radar start。
    const response = await buildOperatorReportProxy(queryString(req.query.baseUrl), req.body);
    res.status(response.proxy_status === "report_forwarded" ? 200 : response.proxy_status === "report_rejected" ? 400 : 502).json(response);
  });

  workstationApp.post("/api/robot-control/radar/scan-proof/refresh", async (req, res) => {
    // Radar refresh 只允许固定 POST body，不接受浏览器把它改造成通用控制代理。
    const response = await buildRadarScanProofRefreshProxy(queryString(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  ([
    ["start", "/api/robot-control/radar/start"],
    ["stop", "/api/robot-control/radar/stop"],
  ] as Array<[RobotControlRadarLifecycleAction, string]>).forEach(([action, route]) => {
    workstationApp.post(route, async (req, res) => {
      // Radar lifecycle 只转发固定 start/stop；body 被忽略，避免退化成任意 Robot API POST。
      const response = await buildRadarLifecycleProxy(queryString(req.query.baseUrl), action);
      res.status(mapLifecycleStatusCode(response.proxy_status)).json(response);
    });
  });

  workstationApp.post("/api/robot-control/map/proof/refresh", async (req, res) => {
    // Map refresh 只允许固定 POST body，不接受浏览器把它改造成建图/导航控制代理。
    const response = await buildMapProofRefreshProxy(queryString(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  workstationApp.post("/api/robot-control/nav2/proof/refresh", async (req, res) => {
    // Nav2 refresh 只允许固定 no-motion planner proof body，不开放 start/stop、goal 或底盘动作。
    const response = await buildNav2NoMotionProofRefreshProxy(queryString(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  workstationApp.post("/api/robot-control/nav2/goal/preflight", async (req, res) => {
    // 目标预检只读 fixed GET 材料；即使通过也不调用 NavigateToPose、/api/nav2/start、/cmd_vel 或 base manual。
    const response = await buildNavGoalPreflightProxy(queryString(req.query.baseUrl), req.body);
    res.status(response.proxy_status === "preflight_passed" ? 200 : 400).json(response);
  });

  workstationApp.post("/api/robot-control/localize/reset", async (req, res) => {
    // 定位 reset 只转发固定 /api/localize/reset body；浏览器不能传 initialpose 或任意 endpoint。
    const response = await buildLocalizationResetProxy(queryString(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  workstationApp.get("/api/robot-control/map/list", async (req, res) => {
    // Map list 是固定 GET 代理；它只读取地图 artifact 候选，不开放任意 Robot API endpoint。
    const response = await buildMapLifecycleProxy(queryString(req.query.baseUrl), "list");
    res.status(mapLifecycleStatusCode(response.proxy_status)).json(response);
  });

  ([
    ["start", "/api/robot-control/map/start"],
    ["save", "/api/robot-control/map/save"],
    ["reset", "/api/robot-control/map/reset"],
  ] as Array<[RobotControlMapLifecycleAction, string]>).forEach(([action, route]) => {
    workstationApp.post(route, async (req, res) => {
      // lifecycle POST 只能转发到 action 对应的固定上位机 endpoint，body 由 helper 做短字段白名单。
      const response = await buildMapLifecycleProxy(queryString(req.query.baseUrl), action, req.body);
      res.status(mapLifecycleStatusCode(response.proxy_status)).json(response);
    });
  });

  workstationApp.post("/api/robot-control/camera/offer", async (req, res) => {
    // camera offer 只允许本机 Node 代理固定上位机 endpoint，不开放任意 Robot API POST。
    const sourceBaseUrl = queryString(req.query.baseUrl);
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
    const sourceBaseUrl = queryString(req.query.baseUrl);
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

  workstationApp.post("/api/robot-control/camera/first-frame/probe", async (req, res) => {
    // 首帧探针只转发到固定上位机 endpoint；body 为空，不能让浏览器指定任意设备或命令。
    const sourceBaseUrl = queryString(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(cameraProbeFailure(sourceBaseUrl, normalized.reason));
      return;
    }
    const remote = await fetchCameraProxySummary(
      sourceBaseUrl,
      "/api/camera/first-frame/probe",
      { include_backend_smoke: true },
      60000,
    );
    if (remote.error) {
      res.status(502).json({ ...cameraProbeFailure(sourceBaseUrl, remote.error), proxy_status: "probe_failed" });
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
      hard_dangerous_true_fields: dangerous,
      robot_control_executed: false,
    };
    res.status(responseBody.proxy_status === "probe_forwarded" ? 200 : 502).json(responseBody);
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

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  app.listen(PORT, "127.0.0.1", () => {
    console.log(`pc-tools workstation API listening on http://127.0.0.1:${PORT}`);
  });
}
