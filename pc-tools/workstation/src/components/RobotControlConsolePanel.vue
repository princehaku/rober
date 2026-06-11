<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  getO7ConsumerTaskDetail,
  getRobotControlSummary,
  getRobotControlMapList,
  postRobotControlBaseManual,
  postRobotControlBaseStop,
  postRobotControlMapStart,
  postRobotControlMapSave,
  postRobotControlLocalizeReset,
  postRobotControlNav2GoalPreflight,
  postRobotControlMapProofRefresh,
  postRobotControlNav2ProofRefresh,
  postRobotControlOperatorReport,
  postRobotControlRadarStart,
  postRobotControlRadarScanProofRefresh,
  postRobotControlRadarStop,
  postRobotControlCameraOffer,
  postRobotControlCameraPeerClose,
  postRobotControlCameraFirstFrameProbe,
} from "../client/workstationApi";
import type {
  O7ConsumerTaskDetailResponse,
  RobotControlBaseCommandProxyResponse,
  RobotControlCameraFirstFrameProbeProxyResponse,
  RobotControlMapLifecycleResponse,
  RobotControlNavGoalPreflightResponse,
  RobotControlOperatorReportProxyResponse,
  RobotControlOperatorReportRequest,
  RobotControlPreviewStatus,
  RobotControlProofRefreshProxyResponse,
  RobotControlRadarLifecycleResponse,
  RobotControlSummaryResponse,
} from "../shared/contracts";

// 本组件仍然是 fail-closed 控制台；新增的 WebRTC 只负责观察视频，不负责任何运动控制。
const robotApiBaseUrl = ref("");
const o6ConsumerBaseUrl = ref("http://127.0.0.1:8088");
const taskId = ref("");
const fieldEvidenceManifestJson = ref("");
const loading = ref(false);
const error = ref("");
const robotSummary = ref<RobotControlSummaryResponse | null>(null);
const taskDetail = ref<O7ConsumerTaskDetailResponse | null>(null);
const radarRefreshResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const radarLifecycleResult = ref<RobotControlRadarLifecycleResponse | null>(null);
const mapRefreshResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const nav2RefreshResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const navGoalPreflightResult = ref<RobotControlNavGoalPreflightResponse | null>(null);
const localizationResetResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const mapLifecycleResult = ref<RobotControlMapLifecycleResponse | null>(null);
const manualCommandResult = ref<RobotControlBaseCommandProxyResponse | null>(null);
const manualCommandPending = ref(false);
const mapLifecyclePending = ref(false);
const mapLifecycleMapName = ref("");
const mapLifecycleArtifactPath = ref("");
const operatorReportPending = ref(false);
const operatorReportResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const operatorReportEvidenceRef = ref("");
const operatorReportSiteState = ref("field_operator_claim_ready_for_review");
const operatorReportExternalVideoRef = ref("");
const operatorReportCameraArtifactsRef = ref("");
const operatorReportWheelFeedbackRef = ref("");
const operatorReportScanDeltaRef = ref("");
const operatorReportRouteMapRef = ref("");
const operatorReportNotes = ref("");
const operatorReportFlags = ref({
  operator_present: false,
  physical_clearance_confirmed: false,
  emergency_stop_ready: false,
  observed_motion: false,
  observed_stop: false,
  external_video_recorded: false,
  visible_content_proven: false,
  wheel_feedback_lr_nonzero_proven: false,
  physical_motion_lidar_delta_proven: false,
  real_route_map_proven: false,
  delivery_success: false,
});
const jogSpeedMps = ref(0.08);
const jogDurationMs = ref(500);
const navGoalX = ref(0.8);
const navGoalY = ref(0);
const navGoalYaw = ref(0);
const confirmNavigationPreflight = ref(false);
const hilChecklist = ref([
  { id: "operator_ready", checked: false, label: "现场有人扶控并准备急停" },
  { id: "clearance_confirmed", checked: false, label: "已确认小车周围无人和障碍" },
  { id: "low_speed_only", checked: false, label: "本轮仅做低速短时点动" },
  { id: "not_autonomy_mode", checked: false, label: "本轮不是自动导航任务" },
]);

// WebRTC 状态单独维护，是为了把“上位机 readback”与“本地页面会话状态”区分开。
const previewStatus = ref<RobotControlPreviewStatus>("idle_not_started");
const failureReason = ref("");
const previewPeerId = ref("");
const previewPeerBaseUrl = ref("");
const iceConnectionState = ref("new");
const videoTrackState = ref("not_received");
const lastOfferAt = ref("");
const lastStopAt = ref("");
const cleanupStatus = ref("not_started");
const radarRefreshPending = ref(false);
const radarLifecyclePending = ref(false);
const mapRefreshPending = ref(false);
const nav2RefreshPending = ref(false);
const navGoalPreflightPending = ref(false);
const localizationResetPending = ref(false);
const previewVideo = ref<HTMLVideoElement | null>(null);
const previewStream = ref<MediaStream | null>(null);
const previewPeerConnection = ref<RTCPeerConnection | null>(null);
const previewStartPending = ref(false);
const previewStopPending = ref(false);
const sessionEpoch = ref(0);
const videoElementHasSrcObject = ref(false);
const videoElementReadyState = ref(0);
const videoElementWidth = ref(0);
const videoElementHeight = ref(0);
const videoElementPresentedFrames = ref<number | null>(null);
const videoElementFrameStatus = ref("not_observed");
type CameraFrameSampleStatus = "not_sampled" | "sampling" | "visible_content_observed" | "near_black" | "sample_failed";
const previewFrameSampleStatus = ref<CameraFrameSampleStatus>("not_sampled");
const previewFrameSampleMeanLuma = ref<number | null>(null);
const previewFrameSampleMaxLuma = ref<number | null>(null);
const previewFrameSampleNonBlackRatio = ref<number | null>(null);
const previewFrameSampledAt = ref("");
const previewFrameSampleFailure = ref("");
const previewFrameSampleAttempts = ref(0);
const previewFrameSampleCanvasSize = ref("not_sampled");
const cameraFirstFrameProbePending = ref(false);
const cameraFirstFrameProbeResult = ref<RobotControlCameraFirstFrameProbeProxyResponse | null>(null);
const evidenceSweepPending = ref(false);
const evidenceSweepStartedAt = ref("");
const evidenceSweepCompletedAt = ref("");
const evidenceSweepLines = ref<string[]>([]);
let previewFrameSampleTimers: number[] = [];

const selectedTaskSummary = computed(() => {
  // task_id 是回放和 evidence 的主键；没有 task_id 时保持 blocked 空状态。
  if (!taskId.value.trim()) {
    return "task_id not selected; route replay/mock fallback summary blocked";
  }
  if (!taskDetail.value) {
    return "task detail not loaded; use Refresh control console";
  }
  return `${taskDetail.value.requested_task_id} / ${taskDetail.value.detail_status}`;
});

const routeReplaySource = computed(() => {
  // 本地 manifest 只能补 field_evidence，不覆盖 O6 trajectory/events 主路径。
  if (!taskDetail.value) {
    return "blocked_not_loaded";
  }
  const fieldSource = taskDetail.value.field_evidence.source_contract;
  return fieldSource === "not_loaded" ? "o6_consumer_detail_missing_or_blocked" : `${fieldSource} + O6 consumer detail`;
});

const previewBusy = computed(() => loading.value || previewStartPending.value || previewStopPending.value);
const canStartPreview = computed(() => !previewBusy.value && robotApiBaseUrl.value.trim().length > 0);
const canStopPreview = computed(
  () => !previewBusy.value && (previewPeerConnection.value !== null || previewPeerId.value.length > 0),
);

function summarizeRobotConnection(): { state: "未连接" | "已连接" | "有异常"; hint: string } {
  // 连接状态只给普通用户看三档，细节放在折叠区。
  if (!robotApiBaseUrl.value.trim()) {
    return { state: "未连接", hint: "先输入地址，再点连接/刷新。" };
  }
  const connection = robotSummary.value?.robot_api_connection;
  if (!connection) {
    return { state: "未连接", hint: "先输入地址，再点连接/刷新。" };
  }
  if (connection.status === "readable" && connection.failed_count === 0 && connection.blocked_count === 0) {
    return { state: "已连接", hint: "已读到小车状态摘要。" };
  }
  if (connection.status === "blocked" || connection.failed_count > 0 || connection.blocked_count > 0 || connection.dangerous_true_fields.length > 0) {
    return { state: "有异常", hint: "可读到部分信息，但有字段被阻断或失败。" };
  }
  return { state: "未连接", hint: "还没有连上可读状态。" };
}

function summarizeCameraState(): { state: "未打开" | "连接中" | "已打开" | "画面可见" | "画面偏暗" | "失败"; hint: string } {
  // 摄像头首屏只暴露普通用户能理解的结论，不泄露 peer / ICE / SDP / canvas 细节。
  switch (previewStatus.value) {
    case "starting_local_peer":
    case "connecting_offer_posted":
      return { state: "连接中", hint: "正在打开实时画面。" };
    case "streaming":
      if (previewFrameSampleStatus.value === "visible_content_observed") {
        return { state: "画面可见", hint: "画面可见。" };
      }
      if (previewFrameSampleStatus.value === "near_black") {
        return { state: "画面偏暗", hint: "画面太暗，先检查镜头/光线。" };
      }
      if (previewFrameSampleStatus.value === "sampling") {
        return { state: "已打开", hint: "画面已打开，正在确认内容。" };
      }
      if (previewFrameSampleStatus.value === "sample_failed") {
        return { state: "已打开", hint: "画面已打开，暂时无法判断明暗。" };
      }
      return { state: "已打开", hint: "画面已打开。" };
    case "start_failed":
    case "peer_cleanup_failed":
      return { state: "失败", hint: failureReason.value || "打开画面失败。" };
    default:
      return { state: "未打开", hint: "还没有打开实时画面。" };
  }
}

function summarizeProofState(pending: boolean, result: RobotControlProofRefreshProxyResponse | null): { state: "未刷新" | "刷新中" | "已刷新" | "失败"; hint: string } {
  // 雷达和地图首屏共用同一套普通状态，避免把工程 proof 字段放回默认界面。
  if (pending) {
    return { state: "刷新中", hint: "正在刷新。" };
  }
  if (!result) {
    return { state: "未刷新", hint: "还没有刷新。" };
  }
  if (result.proxy_status === "refresh_failed" || result.status === "blocked" || result.last_result_status === "fetch_failed") {
    return { state: "失败", hint: result.failure_reason || "刷新失败。" };
  }
  return { state: "已刷新", hint: "已刷新。" };
}

function radarFieldIsTrue(value: string | undefined): boolean {
  // summary 已经把布尔值压成字符串；这里统一识别，避免普通首屏掺入字段名判断。
  return value === "true";
}

function summarizeRadarState(): { state: "雷达未运行" | "刷新中" | "雷达已运行" | "刷新失败"; hint: string } {
  // 雷达首屏优先消费 summary 的最终 lifecycle/continuity 结论；只有最近一次 refresh 明确失败时才覆盖。
  if (radarRefreshPending.value) {
    return { state: "刷新中", hint: "正在刷新雷达状态。" };
  }
  if (
    radarRefreshResult.value &&
    (radarRefreshResult.value.proxy_status === "refresh_failed" ||
      radarRefreshResult.value.status === "blocked" ||
      radarRefreshResult.value.last_result_status === "fetch_failed")
  ) {
    return { state: "刷新失败", hint: radarRefreshResult.value.failure_reason || "暂时没有拿到新的雷达状态。" };
  }
  const lidar = robotSummary.value?.readback_summary.lidar;
  if (!lidar) {
    return { state: "雷达未运行", hint: "先连接小车，再读取雷达状态。" };
  }
  const lifecycleRunning = radarFieldIsTrue(lidar.lifecycle_running);
  const windowObserved = radarFieldIsTrue(lidar.continuous_window_observed);
  const latestFresh = radarFieldIsTrue(lidar.latest_scan_proof_fresh);
  if (lifecycleRunning && windowObserved && latestFresh) {
    return { state: "雷达已运行", hint: "当前窗口已看到新的雷达状态。" };
  }
  if (lifecycleRunning) {
    return { state: "雷达未运行", hint: "雷达正在准备，先点刷新再看结果。" };
  }
  return { state: "雷达未运行", hint: "还没有看到雷达正在运行。" };
}

function summarizeNav2Planning(): { state: "未检查" | "检查中" | "路径可生成" | "检查失败"; hint: string } {
  // 路径规划属于诊断信息，只能在高级区展示，避免普通用户首屏被工程语义污染。
  if (nav2RefreshPending.value) {
    return { state: "检查中", hint: "正在检查路径是否可生成。" };
  }
  const result = nav2RefreshResult.value;
  if (!result) {
    return { state: "未检查", hint: "还没有检查路径。" };
  }
  const record = result.latest_readback_key_values;
  const pathGenerated = record.path_generated === "true" || record.path_generation_succeeded === "true";
  if (pathGenerated && result.proxy_status === "refresh_failed") {
    return { state: "路径可生成", hint: "检查已返回；不会发车。" };
  }
  if (result.proxy_status !== "refresh_forwarded" || result.status === "blocked") {
    return { state: "检查失败", hint: result.failure_reason || "检查失败。" };
  }
  return pathGenerated
    ? { state: "路径可生成", hint: "检查已返回；不会发车。" }
    : { state: "未检查", hint: "还没有可用路径。" };
}

function summarizeMapLifecycle(): { state: "未读取" | "处理中" | "已读取" | "失败"; hint: string } {
  // lifecycle 摘要只说列表/保存结果，不把 start/reset 或工程 proof 细节放回首页。
  if (mapLifecyclePending.value) {
    return { state: "处理中", hint: "正在读取或保存地图。" };
  }
  const result = mapLifecycleResult.value;
  if (!result) {
    return { state: "未读取", hint: "还没有读取地图列表。" };
  }
  if (result.proxy_status !== "lifecycle_forwarded" || result.status === "blocked") {
    return { state: "失败", hint: result.failure_reason || "地图 lifecycle 请求被阻断。" };
  }
  if (result.action === "list") {
    return { state: "已读取", hint: `地图列表 ${result.map_count ?? 0} 个候选。` };
  }
  return { state: "已读取", hint: "地图高级操作已返回；详情在高级诊断。" };
}

function syncJogInputsToBoundary(): void {
  // 输入框默认跟随后端安全边界收口，避免页面初值或手输值越界。
  const speedLimit = robotSummary.value?.safe_command_boundary.speed_limit_mps ?? 0.12;
  const durationLimit = robotSummary.value?.safe_command_boundary.duration_limit_ms ?? 800;
  jogSpeedMps.value = Math.min(jogSpeedMps.value, speedLimit);
  jogDurationMs.value = Math.min(jogDurationMs.value, durationLimit);
}

const robotConnectionSummary = computed(() => summarizeRobotConnection());
const cameraSummary = computed(() => summarizeCameraState());
const cameraFirstFrameProbeSummary = computed(() => {
  // 首帧探针是高级诊断结果：只说明底层 camera readback，不升级为实时图传成功。
  if (cameraFirstFrameProbePending.value) {
    return "probe pending";
  }
  const result = cameraFirstFrameProbeResult.value;
  if (!result) {
    return "probe not requested";
  }
  const values = result.probe_key_values;
  return `${result.proxy_status}; status=${result.status}; open=${values.open_ok}; read=${values.read_ok}; reason=${result.failure_reason || values.failure_reason}`;
});
const evidenceSweepSummary = computed(() => {
  // 一键巡检聚合固定代理结果；blocked 仍按 blocked 展示，不伪装成全量通过。
  if (evidenceSweepPending.value) {
    return "evidence sweep pending";
  }
  if (!evidenceSweepLines.value.length) {
    return "evidence sweep not requested";
  }
  return evidenceSweepLines.value.join(" | ");
});
const radarSummary = computed(() => summarizeRadarState());
const radarLifecycleSummary = computed(() => {
  // 雷达 lifecycle 是高级诊断动作；摘要只说明代理和 guard 结果，不证明 runtime 已启动。
  if (radarLifecyclePending.value) {
    return "radar lifecycle pending";
  }
  const result = radarLifecycleResult.value;
  if (!result) {
    return "radar lifecycle not requested";
  }
  return `${result.action}:${result.proxy_status}; mode=${result.command_result.mode}; executed=${result.command_result.executed}; failure=${result.failure_reason || "none"}`;
});
const mapSummary = computed(() => summarizeProofState(mapRefreshPending.value, mapRefreshResult.value));
const nav2PlanningSummary = computed(() => summarizeNav2Planning());
const mapLifecycleSummary = computed(() => summarizeMapLifecycle());
const manualBoundary = computed(() => robotSummary.value?.safe_command_boundary ?? null);
const manualSpeedLimit = computed(() => manualBoundary.value?.speed_limit_mps ?? 0.12);
const manualDurationLimit = computed(() => manualBoundary.value?.duration_limit_ms ?? 800);
const checklistMissing = computed(() => hilChecklist.value.filter((item) => !item.checked).map((item) => item.label));
const hilChecklistConfirmed = computed(() => checklistMissing.value.length === 0);
const canSendStop = computed(() => !manualCommandPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0);
const canRunEvidenceSweep = computed(() => !evidenceSweepPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0);
function claimWithRefReady(value: string | undefined): boolean {
  // 现场材料的四类引用型 claim 必须同时满足 true 且带 ref，缺任一条件都按未满足处理。
  return typeof value === "string" && value.startsWith("true; ref=") && !value.endsWith("not_loaded");
}

const operatorMaterialMissingFields = computed(() => {
  // 这里直接输出后端约定字段名，方便现场人员对照材料清单补证据。
  const summary = robotSummary.value?.operator_hil_material_summary;
  const checks = [
    { id: "operator_present", ready: summary?.operator_present === "true" },
    { id: "physical_clearance_confirmed", ready: summary?.physical_clearance === "true" },
    { id: "emergency_stop_ready", ready: summary?.emergency_stop === "true" },
    { id: "external_video_recorded", ready: claimWithRefReady(summary?.external_video) },
    { id: "visible_content_proven", ready: claimWithRefReady(summary?.camera_visible) },
    { id: "wheel_feedback_lr_nonzero_proven", ready: claimWithRefReady(summary?.wheel_feedback) },
    { id: "physical_motion_lidar_delta_proven", ready: claimWithRefReady(summary?.lidar_delta) },
  ];
  return checks.filter((item) => !item.ready).map((item) => item.id);
});

const operatorMaterialReady = computed(() => {
  // 未加载 summary 时会自然落入缺项列表，因此这里不再额外放宽。
  return robotSummary.value?.operator_hil_material_summary?.status === "loaded" && operatorMaterialMissingFields.value.length === 0;
});

const canSendManualMotion = computed(() => {
  // 非 stop 方向必须同时满足地址、checklist、现场材料和“当前无 pending”。
  return !manualCommandPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0 && hilChecklistConfirmed.value && operatorMaterialReady.value;
});

const operatorMaterialGateSummary = computed(() => {
  // 首页只给“现场材料”普通结论；具体字段名和引用全部留在高级诊断。
  return operatorMaterialReady.value
    ? { state: "已满足", hint: "现场材料已满足；仍只允许一次低速短时点动。" }
    : { state: "未满足", hint: "需要补齐现场材料后，才允许低速点动。" };
});
const manualBlockedReason = computed(() => {
  if (!robotApiBaseUrl.value.trim()) {
    return "先输入小车地址并连接。";
  }
  if (manualCommandPending.value || loading.value) {
    return "当前仍有请求处理中；本机不会并发发送点动。";
  }
  if (!hilChecklistConfirmed.value) {
    return `还缺现场确认：${checklistMissing.value.join("；")}。`;
  }
  if (!operatorMaterialReady.value) {
    return `材料未满足，本机不会发送点动。缺项：${operatorMaterialMissingFields.value.join("、")}。`;
  }
  return "允许发送一次低速短时点动；安全锁定不会解除。";
});
const manualMotionSummary = computed(() => {
  // 高级点动区需要解释门禁原因；首屏不会直接展示这段工程化文字。
  if (manualCommandPending.value) {
    return { state: "发送中", hint: "正在发送本次点动或停止请求。" };
  }
  if (!manualCommandResult.value) {
    return canSendManualMotion.value
      ? { state: "可点动", hint: "现场确认已完成，可发送一次低速短时点动。" }
      : { state: "未确认", hint: manualBlockedReason.value };
  }
  if (manualCommandResult.value.proxy_status === "command_forwarded") {
    return manualCommandResult.value.command_kind === "stop"
      ? { state: "已发送", hint: "已发送停止请求。" }
      : { state: "已发送", hint: `已发送 ${manualCommandResult.value.applied_direction} 点动；速度和时长已按本机上限收口。` };
  }
  return { state: "失败", hint: manualCommandResult.value.failure_reason || "请求被拒绝或上位机不可达。" };
});

const plainMotionSummary = computed(() => {
  // 首屏只呈现“能不能停”和最近停止结果，不暴露点动、路径、材料或接口细节。
  if (manualCommandPending.value) {
    return { state: "处理中", hint: "正在处理请求。" };
  }
  if (!manualCommandResult.value) {
    return { state: "待命", hint: "需要时可直接停止。" };
  }
  if (manualCommandResult.value.command_kind === "stop" && manualCommandResult.value.proxy_status === "command_forwarded") {
    return { state: "已停止", hint: "停止请求已发送。" };
  }
  if (manualCommandResult.value.command_kind === "stop") {
    return { state: "停止失败", hint: manualCommandResult.value.failure_reason || "停止请求失败。" };
  }
  return { state: "待命", hint: "需要时可直接停止。" };
});

const plainEvidenceSweepSummary = computed(() => {
  // 普通首屏只给“检查小车”结果，不暴露 proof/Nav2/HIL 等工程语义。
  if (evidenceSweepPending.value) {
    return { state: "检查中", hint: "正在依次检查画面、雷达、地图、定位和停止。" };
  }
  if (!evidenceSweepLines.value.length) {
    return { state: "待检查", hint: "点击检查小车，自动读取关键状态。" };
  }
  const hasCameraIssue = evidenceSweepLines.value.some((line) => line.includes("camera_probe:first_frame_timeout"));
  const hasError = evidenceSweepLines.value.some((line) => line.startsWith("error:"));
  if (hasError) {
    return { state: "检查失败", hint: "检查没有完整跑完，详情在高级诊断。" };
  }
  if (hasCameraIssue) {
    return { state: "需要处理", hint: "基础检查已返回；实时画面仍需处理。" };
  }
  return { state: "已检查", hint: "关键状态已读取，详情可展开高级诊断。" };
});
function listText(items: string[] | undefined, fallback = "none"): string {
  // blocked/not_proven 只展示少量摘要，完整定位应回到后端日志或 artifact。
  return items && items.length ? items.slice(0, 6).join("; ") : fallback;
}

function sampleText(items: Record<string, unknown>[] | undefined): string {
  // 只读样本压缩成短 JSON，页面不承担完整数据浏览器职责。
  if (!items || items.length === 0) {
    return "none";
  }
  return items
    .slice(0, 2)
    .map((item) => JSON.stringify(item).slice(0, 160))
    .join(" | ");
}

function recordText(record: Record<string, string> | undefined): string {
  // key-value 摘要只展示短 JSON，避免把刷新结果拆成太多视觉噪声。
  if (!record || Object.keys(record).length === 0) {
    return "none";
  }
  return JSON.stringify(record).slice(0, 520);
}

function evidenceEndpointText(items: RobotControlBaseCommandProxyResponse["evidence_capture_endpoints"] | undefined): string {
  // 运动证据 endpoint 列表只展示固定 GET 摘要，证明它不是任意代理或 raw dump。
  if (!items || items.length === 0) {
    return "none";
  }
  return items
    .map((item) => `${item.phase}:${item.endpoint}:${item.method}:${item.request_status}:${item.http_status ?? "n/a"}`)
    .join(" | ");
}

function evidenceReadbackText(readback: RobotControlBaseCommandProxyResponse["before_readback"] | undefined): string {
  // before/after 只显示每个 endpoint 的短 key_values，足够排障且不会污染首页。
  if (!readback || Object.keys(readback).length === 0) {
    return "none";
  }
  return JSON.stringify(readback).slice(0, 520);
}

function timestampText(epochMs: number | null | undefined): string {
  // 刷新时间统一显示成 ISO 字符串，便于和上位机日志对齐。
  return typeof epochMs === "number" && Number.isFinite(epochMs) ? new Date(epochMs).toISOString() : "never";
}

function requestBodyForDirection(direction: "forward" | "back" | "left" | "right") {
  // 提交前再次按当前边界 clamp，避免浏览器层被手工改值后越过安全上限。
  return {
    direction,
    speed: Math.min(Math.max(jogSpeedMps.value, 0), manualSpeedLimit.value),
    duration_ms: Math.min(Math.max(jogDurationMs.value, 0), manualDurationLimit.value),
    confirm_hil_checklist: hilChecklistConfirmed.value,
  } as const;
}

function commandEvidenceFallback(commandKind: "manual" | "stop", reason: string) {
  // 浏览器层异常也必须补齐证据字段，避免错误态合同缺字段。
  return {
    evidence_capture_status: "blocked" as const,
    evidence_capture_endpoints: [],
    evidence_capture_blocked_reasons: [reason],
    before_readback: {},
    after_readback: {},
    motion_evidence_summary: `${commandKind} command before/after fixed GET evidence snapshot blocked or unavailable; this is not HIL pass.`,
  };
}

function commandOperatorReportPreflightFallback(commandKind: "manual" | "stop", reason: string) {
  // 前端本地异常不会绕过后端 preflight；这里只补齐响应形状用于错误展示。
  const required = manualBoundary.value?.operator_report_preflight_required_fields ?? [];
  return {
    status: commandKind === "stop" ? "not_required_for_stop" as const : "blocked" as const,
    source_endpoint: "/api/operator/report" as const,
    request_status: commandKind === "stop" ? "not_required" as const : "blocked" as const,
    http_status: null,
    report_status: commandKind === "stop" ? "not_required_for_stop" : "not_checked",
    evidence_ref: commandKind === "stop" ? "not_required_for_stop" : "not_checked",
    required_fields: required,
    missing_fields: commandKind === "stop" ? [] : required,
    material_summary: robotSummary.value?.operator_hil_material_summary ?? {
      status: "not_loaded" as const,
      source_endpoint_id: "operator_report_latest" as const,
      source_path: "operator_report_latest.structured_hil_claims" as const,
      report_status: "not_loaded",
      evidence_ref: "not_loaded",
      operator_present: "not_loaded",
      physical_clearance: "not_loaded",
      emergency_stop: "not_loaded",
      external_video: "not_loaded",
      camera_visible: "not_loaded",
      wheel_feedback: "not_loaded",
      lidar_delta: "not_loaded",
      route_map: "not_loaded",
      delivery_claim: "not_loaded",
      site_state: "not_loaded",
    },
    failure_reason: commandKind === "stop" ? "" : reason,
    hard_dangerous_true_fields: [],
  };
}

function makeRefreshFallback(
  kind: "radar_scan_proof_refresh" | "map_proof_refresh" | "nav2_no_motion_proof_refresh" | "localization_reset",
  baseUrl: string,
  reason: string,
): RobotControlProofRefreshProxyResponse {
  // 网络错误或解析错误时也要保留卡片字段，避免 UI 空白后误读为成功。
  const now = Date.now();
  const endpoint =
    kind === "radar_scan_proof_refresh"
      ? "/api/radar/scan-proof/refresh"
      : kind === "map_proof_refresh"
        ? "/api/map/proof/refresh"
        : kind === "nav2_no_motion_proof_refresh"
          ? "/api/nav2/proof/refresh"
          : "/api/localize/reset";
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    refresh_kind: kind,
    proxy_status: "refresh_failed",
    source_base_url: baseUrl,
    normalized_base_url: baseUrl.trim() || "not_loaded",
    remote_endpoint: endpoint,
    remote_http_status: null,
    status: "blocked",
    last_result_status: "fetch_failed",
    last_result_schema: "not_loaded",
    last_result_evidence_ref: "not_loaded",
    last_refreshed_at_ms: now,
    latest_readback_key_values: {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    non_motion_evidence_actions_observed: [],
    robot_control_executed: false,
  };
}

function makeNavGoalPreflightFallback(reason: string): RobotControlNavGoalPreflightResponse {
  // 浏览器异常不会绕过后端门禁；这里补齐形状，只用于展示“本机未执行导航”。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_preflight.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "preflight_rejected",
    preflight_status: "preflight_rejected",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    workstation_endpoint: "/api/robot-control/nav2/goal/preflight",
    remote_methods_used: ["GET"],
    remote_read_endpoints: [],
    forbidden_remote_endpoints_not_called: ["/api/nav2/start", "NavigateToPose", "/cmd_vel", "/api/base/manual"],
    goal_request: {
      goal_frame_id: "map",
      goal_x: navGoalX.value,
      goal_y: navGoalY.value,
      goal_yaw: navGoalYaw.value,
      confirm_navigation_preflight: confirmNavigationPreflight.value,
    },
    goal_limits: {
      frame_id: "map",
      x_min_m: -3,
      x_max_m: 3,
      y_min_m: -3,
      y_max_m: 3,
      yaw_min_rad: -3.1416,
      yaw_max_rad: 3.1416,
    },
    operator_report_preflight: commandOperatorReportPreflightFallback("manual", reason),
    localization_summary: {
      request_status: "blocked",
      status: "not_loaded",
      localization_reset_observed: false,
      nav2_no_motion_localization_runtime_observed: false,
      map_to_base_link: false,
    },
    nav2_path_summary: {
      request_status: "blocked",
      status: "not_loaded",
      path_generated: false,
      path_generation_succeeded: false,
      path_point_count: 0,
    },
    nav2_status_summary: {
      request_status: "blocked",
      status: "not_loaded",
    },
    missing_requirements: [reason],
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function makeRadarLifecycleFallback(action: "start" | "stop", reason: string): RobotControlRadarLifecycleResponse {
  // 浏览器 fetch 异常时也保持与后端一致的安全字段，避免高级诊断误判。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    action,
    proxy_status: "lifecycle_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    remote_endpoint: action === "start" ? "/api/radar/start" : "/api/radar/stop",
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

function mapLifecycleRequestBody() {
  // 可选输入只从高级诊断进入；空值不发送，保持 save 的默认软件 guard 行为。
  return {
    ...(mapLifecycleMapName.value.trim() ? { map_name: mapLifecycleMapName.value.trim() } : {}),
    ...(mapLifecycleArtifactPath.value.trim() ? { artifact_path: mapLifecycleArtifactPath.value.trim() } : {}),
  };
}

function makeMapLifecycleFallback(action: "list" | "start" | "save", reason: string): RobotControlMapLifecycleResponse {
  // fetch 级失败仍补完整字段，避免地图卡片在错误时消失或误读成成功。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    action,
    proxy_status: "lifecycle_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    remote_endpoint: action === "list" ? "/api/map/list" : action === "start" ? "/api/map/start" : "/api/map/save",
    remote_method: action === "list" ? "GET" : "POST",
    remote_http_status: null,
    status: "blocked",
    map_count: null,
    map_names: [],
    command_result: { mode: "not_loaded", executed: false, ok: null },
    request_body: action === "start" || action === "save" ? mapLifecycleRequestBody() : {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function operatorReportRequestBody(): RobotControlOperatorReportRequest {
  // 现场材料提交只组装白名单字段；空 ref 不发送，减少上位机保存无意义空字符串。
  const claims = {
    external_video_recorded: operatorReportFlags.value.external_video_recorded,
    ...(operatorReportExternalVideoRef.value.trim() ? { external_video_ref: operatorReportExternalVideoRef.value.trim() } : {}),
    visible_content_proven: operatorReportFlags.value.visible_content_proven,
    ...(operatorReportCameraArtifactsRef.value.trim() ? { camera_artifacts_ref: operatorReportCameraArtifactsRef.value.trim() } : {}),
    wheel_feedback_lr_nonzero_proven: operatorReportFlags.value.wheel_feedback_lr_nonzero_proven,
    ...(operatorReportWheelFeedbackRef.value.trim() ? { wheel_feedback_ref: operatorReportWheelFeedbackRef.value.trim() } : {}),
    physical_motion_lidar_delta_proven: operatorReportFlags.value.physical_motion_lidar_delta_proven,
    ...(operatorReportScanDeltaRef.value.trim() ? { scan_delta_ref: operatorReportScanDeltaRef.value.trim() } : {}),
    real_route_map_proven: operatorReportFlags.value.real_route_map_proven,
    ...(operatorReportRouteMapRef.value.trim() ? { route_map_ref: operatorReportRouteMapRef.value.trim() } : {}),
    delivery_success: operatorReportFlags.value.delivery_success,
    ...(operatorReportSiteState.value.trim() ? { site_state: operatorReportSiteState.value.trim() } : {}),
  };
  return {
    operator_present: operatorReportFlags.value.operator_present,
    ...(operatorReportEvidenceRef.value.trim() ? { evidence_ref: operatorReportEvidenceRef.value.trim() } : {}),
    physical_clearance_confirmed: operatorReportFlags.value.physical_clearance_confirmed,
    emergency_stop_ready: operatorReportFlags.value.emergency_stop_ready,
    observed_motion: operatorReportFlags.value.observed_motion,
    observed_stop: operatorReportFlags.value.observed_stop,
    reported_at: new Date().toISOString(),
    ...(operatorReportNotes.value.trim() ? { operator_notes: operatorReportNotes.value.trim() } : {}),
    structured_hil_claims: claims,
  };
}

function makeOperatorReportFallback(reason: string): RobotControlOperatorReportProxyResponse {
  // 前端异常时也补齐同一响应合同，避免最近提交状态缺失安全字段。
  const requestBody = operatorReportRequestBody();
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "report_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    remote_endpoint: "/api/operator/report",
    remote_method: "POST",
    remote_http_status: null,
    status: "blocked",
    request_body: requestBody,
    structured_hil_claims: requestBody.structured_hil_claims ?? {},
    rejected_fields: [],
    ignored_fields: [],
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function makeCameraFirstFrameProbeFallback(reason: string): RobotControlCameraFirstFrameProbeProxyResponse {
  // 浏览器 fetch 异常时仍显示完整 fail-closed 响应，不把异常当作相机状态成功。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "probe_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    remote_endpoint: "/api/camera/first-frame/probe",
    remote_http_status: null,
    status: "blocked",
    probe_key_values: {
      schema: "not_loaded",
      device: "not_loaded",
      requested_fourcc: "not_loaded",
      open_ok: "not_loaded",
      read_ok: "not_loaded",
      first_frame_timeout: "not_loaded",
      failure_reason: reason,
      visible_content_proven: "false",
      elapsed_ms: "not_loaded",
      mean_luma: "not_available",
      non_black_ratio: "not_available",
    },
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function stampNow(): string {
  // 时间戳使用浏览器本地 ISO 字符串，足够支撑 operator 复核最近一次 Start/Stop。
  return new Date().toISOString();
}

function waitForIceGatheringComplete(peer: RTCPeerConnection, epoch: number, timeoutMs = 3500): Promise<void> {
  // 上位机当前不支持 trickle ICE；必须把 host candidates 收进 offer SDP 后再发给固定代理。
  if (sessionEpoch.value !== epoch || peer.iceGatheringState === "complete") {
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    const previousHandler = peer.onicegatheringstatechange;
    const timeout = window.setTimeout(() => finish(), timeoutMs);
    const finish = () => {
      window.clearTimeout(timeout);
      peer.onicegatheringstatechange = previousHandler;
      resolve();
    };
    peer.onicegatheringstatechange = function handleIceGatheringStateChange(event: Event) {
      previousHandler?.call(peer, event);
      if (sessionEpoch.value !== epoch || peer.iceGatheringState === "complete") {
        finish();
      }
    };
  });
}

function clearPreviewElement(): void {
  // 离开页面或停止时必须清空 srcObject，避免 UI 继续显示上一轮残留帧。
  if (previewVideo.value) {
    previewVideo.value.srcObject = null;
  }
  syncPreviewVideoElementDiagnostics();
}

function clearPreviewFrameSamplingTimers(): void {
  // 采样只允许低频短时重试；会话结束或重启时必须清掉旧 timer，避免旧结果污染新会话。
  previewFrameSampleTimers.forEach((timer) => window.clearTimeout(timer));
  previewFrameSampleTimers = [];
}

function resetPreviewFrameSampling(): void {
  // 新会话或停止后必须清空上一轮亮度结论，避免普通首屏继续展示过期“可见/偏暗”。
  clearPreviewFrameSamplingTimers();
  previewFrameSampleStatus.value = "not_sampled";
  previewFrameSampleMeanLuma.value = null;
  previewFrameSampleMaxLuma.value = null;
  previewFrameSampleNonBlackRatio.value = null;
  previewFrameSampledAt.value = "";
  previewFrameSampleFailure.value = "";
  previewFrameSampleAttempts.value = 0;
  previewFrameSampleCanvasSize.value = "not_sampled";
}

function syncPreviewVideoElementDiagnostics(): void {
  // 这些字段只放在高级诊断和 smoke artifact，用真实 video 元素状态补足 track/live 的间接证据。
  const videoElement = previewVideo.value;
  videoElementHasSrcObject.value = Boolean(videoElement?.srcObject);
  videoElementReadyState.value = videoElement?.readyState ?? 0;
  videoElementWidth.value = videoElement?.videoWidth ?? 0;
  videoElementHeight.value = videoElement?.videoHeight ?? 0;
  const quality = videoElement?.getVideoPlaybackQuality?.();
  videoElementPresentedFrames.value = typeof quality?.totalVideoFrames === "number" ? quality.totalVideoFrames : null;
  if (!videoElementHasSrcObject.value) {
    videoElementFrameStatus.value = "not_bound";
  } else if (videoElementWidth.value > 0 && videoElementHeight.value > 0 && videoElementReadyState.value >= 2) {
    videoElementFrameStatus.value = "visible_frame_ready";
  } else if (videoElementReadyState.value > 0) {
    videoElementFrameStatus.value = "metadata_or_loading";
  }
}

function requestPreviewFrameProbe(videoElement: HTMLVideoElement, epoch: number): void {
  // requestVideoFrameCallback 能证明浏览器渲染管线真的收到帧；不支持时退回 readyState/尺寸采样。
  if (typeof videoElement.requestVideoFrameCallback !== "function") {
    syncPreviewVideoElementDiagnostics();
    return;
  }
  videoElement.requestVideoFrameCallback((_now, metadata) => {
    if (sessionEpoch.value !== epoch) {
      return;
    }
    videoElementWidth.value = metadata.width || videoElement.videoWidth || 0;
    videoElementHeight.value = metadata.height || videoElement.videoHeight || 0;
    videoElementReadyState.value = videoElement.readyState;
    videoElementHasSrcObject.value = Boolean(videoElement.srcObject);
    videoElementPresentedFrames.value = typeof metadata.presentedFrames === "number" ? metadata.presentedFrames : videoElementPresentedFrames.value;
    videoElementFrameStatus.value = "frame_callback_observed";
  });
}

function roundFrameMetric(value: number): number {
  // 采样指标只用于人眼可见性诊断，保留三位小数足够复核且不会引入伪精度。
  return Math.round(value * 1000) / 1000;
}

function classifyPreviewFrameQuality(meanLuma: number, maxLuma: number, nonBlackRatio: number): CameraFrameSampleStatus {
  // 阈值故意保守：只有亮度均值、亮点上界和非黑比例同时过线，才允许首屏显示“画面可见”。
  if (meanLuma >= 18 && maxLuma >= 96 && nonBlackRatio >= 0.05) {
    return "visible_content_observed";
  }
  return "near_black";
}

function samplePreviewFrame(epoch: number): void {
  // 采样只在本地浏览器内存完成；它只判断画面内容是否近黑，不承担任何控制放行职责。
  if (sessionEpoch.value !== epoch || previewStatus.value !== "streaming") {
    return;
  }
  previewFrameSampleAttempts.value += 1;
  const videoElement = previewVideo.value;
  if (!videoElement || !videoElement.srcObject) {
    previewFrameSampleStatus.value = "sample_failed";
    previewFrameSampleFailure.value = "video_src_object_missing";
    return;
  }
  if (videoElement.videoWidth <= 0 || videoElement.videoHeight <= 0 || videoElement.readyState < 2) {
    if (previewFrameSampleAttempts.value >= 3) {
      previewFrameSampleStatus.value = "sample_failed";
    }
    previewFrameSampleFailure.value = "video_frame_not_ready";
    return;
  }
  previewFrameSampleStatus.value = "sampling";
  const sampleWidth = Math.max(16, Math.min(64, Math.floor(videoElement.videoWidth / 10) || 32));
  const sampleHeight = Math.max(16, Math.min(48, Math.floor(videoElement.videoHeight / 10) || 24));
  previewFrameSampleCanvasSize.value = `${sampleWidth}x${sampleHeight}`;
  try {
    const canvas = document.createElement("canvas");
    canvas.width = sampleWidth;
    canvas.height = sampleHeight;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) {
      previewFrameSampleStatus.value = "sample_failed";
      previewFrameSampleFailure.value = "canvas_2d_context_unavailable";
      return;
    }
    context.drawImage(videoElement, 0, 0, sampleWidth, sampleHeight);
    const imageData = context.getImageData(0, 0, sampleWidth, sampleHeight);
    const pixels = imageData.data;
    const totalPixels = pixels.length / 4;
    let lumaSum = 0;
    let lumaMax = 0;
    let nonBlackCount = 0;
    for (let index = 0; index < pixels.length; index += 4) {
      const luma = Math.round((pixels[index]! * 77 + pixels[index + 1]! * 150 + pixels[index + 2]! * 29) / 256);
      lumaSum += luma;
      if (luma > lumaMax) {
        lumaMax = luma;
      }
      if (luma >= 16) {
        nonBlackCount += 1;
      }
    }
    const meanLuma = totalPixels > 0 ? lumaSum / totalPixels : 0;
    const nonBlackRatio = totalPixels > 0 ? nonBlackCount / totalPixels : 0;
    previewFrameSampleMeanLuma.value = roundFrameMetric(meanLuma);
    previewFrameSampleMaxLuma.value = lumaMax;
    previewFrameSampleNonBlackRatio.value = roundFrameMetric(nonBlackRatio);
    previewFrameSampledAt.value = stampNow();
    previewFrameSampleFailure.value = "";
    previewFrameSampleStatus.value = classifyPreviewFrameQuality(meanLuma, lumaMax, nonBlackRatio);
  } catch (err) {
    previewFrameSampleStatus.value = "sample_failed";
    previewFrameSampleFailure.value = err instanceof Error ? err.message : "frame_sampling_failed";
  }
}

function schedulePreviewFrameSampling(epoch: number): void {
  // 单次 loadeddata/playing 可能还拿不到稳定像素，因此每会话允许最多三次低频补采样。
  if (sessionEpoch.value !== epoch || previewStatus.value !== "streaming") {
    return;
  }
  clearPreviewFrameSamplingTimers();
  previewFrameSampleStatus.value = "sampling";
  previewFrameSampleFailure.value = "";
  const delaysMs = [0, 300, 1000];
  previewFrameSampleTimers = delaysMs.map((delayMs) =>
    window.setTimeout(() => {
      if (sessionEpoch.value !== epoch || previewStatus.value !== "streaming") {
        return;
      }
      samplePreviewFrame(epoch);
    }, delayMs),
  );
}

function handlePreviewVideoReady(): void {
  // video 元素发出 loadeddata/playing 时，才说明浏览器已有机会读到真实像素内容。
  syncPreviewVideoElementDiagnostics();
  if (previewStatus.value === "streaming") {
    schedulePreviewFrameSampling(sessionEpoch.value);
  }
}

function bindPreviewStreamToElement(stream: MediaStream, epoch: number): void {
  // 绑定后主动 play，避免部分浏览器只完成 WebRTC track 但 video 元素仍停在 HAVE_NOTHING。
  const videoElement = previewVideo.value;
  if (!videoElement) {
    return;
  }
  videoElement.srcObject = stream;
  syncPreviewVideoElementDiagnostics();
  requestPreviewFrameProbe(videoElement, epoch);
  try {
    const playResult = videoElement.play();
    if (playResult) {
      void playResult
        .then(() => {
          syncPreviewVideoElementDiagnostics();
          requestPreviewFrameProbe(videoElement, epoch);
          schedulePreviewFrameSampling(epoch);
        })
        .catch(() => {
          syncPreviewVideoElementDiagnostics();
        });
    }
  } catch {
    syncPreviewVideoElementDiagnostics();
  }
}

function replacePreviewStream(track: MediaStreamTrack | null, remoteStream: MediaStream | null, epoch: number): void {
  // 页面只消费远端 video track；不申请音频，也不把其他 track 混入 video 元素。
  if (previewStream.value && previewStream.value !== remoteStream) {
    previewStream.value.getTracks().forEach((streamTrack) => streamTrack.stop());
  }
  if (!track) {
    previewStream.value = null;
    clearPreviewElement();
    return;
  }
  const nextStream = remoteStream ?? new MediaStream([track]);
  previewStream.value = nextStream;
  bindPreviewStreamToElement(nextStream, epoch);
}

function bindVideoTrack(track: MediaStreamTrack, remoteStream: MediaStream | null, epoch: number): void {
  // track 生命周期要绑定到当前 session，避免旧 peer 的 ended 事件覆盖新会话状态。
  if (sessionEpoch.value !== epoch) {
    return;
  }
  resetPreviewFrameSampling();
  previewFrameSampleStatus.value = "sampling";
  videoTrackState.value = track.readyState;
  replacePreviewStream(track, remoteStream, epoch);
  previewStatus.value = "streaming";
  failureReason.value = "";
  track.onended = () => {
    if (sessionEpoch.value !== epoch) {
      return;
    }
    videoTrackState.value = track.readyState;
  };
}

function closeLocalPeer(reason: RobotControlPreviewStatus): void {
  // 本地 peer 先关，保证重复 Start、切换 baseUrl、卸载时不会持有旧的 ICE/track 资源。
  previewPeerConnection.value?.getReceivers().forEach((receiver) => receiver.track?.stop());
  previewPeerConnection.value?.close();
  previewPeerConnection.value = null;
  replacePreviewStream(null, null, sessionEpoch.value);
  resetPreviewFrameSampling();
  iceConnectionState.value = "closed";
  videoTrackState.value = "stopped";
  previewStatus.value = reason;
}

async function cleanupPreview(reason: RobotControlPreviewStatus, cleanupReason: string): Promise<void> {
  // cleanup 是 Start/Stop/baseUrl 变化/组件卸载的统一入口，避免 peer 泄漏成僵尸会话。
  const peerId = previewPeerId.value;
  const peerBaseUrl = previewPeerBaseUrl.value;
  closeLocalPeer(reason);
  cleanupStatus.value = cleanupReason;
  if (!peerId || !peerBaseUrl.trim()) {
    previewPeerId.value = "";
    previewPeerBaseUrl.value = "";
    lastStopAt.value = stampNow();
    return;
  }
  try {
    const response = await postRobotControlCameraPeerClose(peerBaseUrl, peerId);
    previewPeerId.value = "";
    previewPeerBaseUrl.value = "";
    lastStopAt.value = stampNow();
    cleanupStatus.value = `${response.proxy_status}:${response.status}`;
    if (response.proxy_status !== "peer_closed") {
      previewStatus.value = "peer_cleanup_failed";
      failureReason.value = response.failure_reason || response.error || "peer_cleanup_failed";
    }
  } catch (err) {
    previewStatus.value = "peer_cleanup_failed";
    failureReason.value = err instanceof Error ? err.message : "peer_cleanup_failed";
    cleanupStatus.value = "peer_cleanup_failed";
    lastStopAt.value = stampNow();
  }
}

async function refreshConsole(): Promise<void> {
  // 刷新永远先读 Node proxy；只有 task_id 存在才读 O6 detail。
  loading.value = true;
  error.value = "";
  try {
    const [summary, detail] = await Promise.all([
      getRobotControlSummary(robotApiBaseUrl.value),
      taskId.value.trim()
        ? getO7ConsumerTaskDetail(o6ConsumerBaseUrl.value, taskId.value, fieldEvidenceManifestJson.value)
        : Promise.resolve(null),
    ]);
    robotSummary.value = summary;
    taskDetail.value = detail;
  } catch (err) {
    // 前端异常仍保持所有主动作关闭，具体 Robot API 失败应优先看 summary.blocked_reasons。
    error.value = err instanceof Error ? err.message : "robot_control_console_refresh_failed";
  } finally {
    loading.value = false;
  }
}

async function runRefreshAction(
  kind: "radar_scan_proof_refresh" | "map_proof_refresh" | "nav2_no_motion_proof_refresh",
  action: () => Promise<RobotControlProofRefreshProxyResponse>,
  target: typeof radarRefreshResult,
  pending: typeof radarRefreshPending,
): Promise<void> {
  // 刷新动作先落本地卡片状态，再顺手回刷 Robot Control summary，避免卡片和顶部摘要不同步。
  pending.value = true;
  try {
    target.value = await action();
  } catch (err) {
    const reason = err instanceof Error ? err.message : `${kind}_request_failed`;
    target.value = makeRefreshFallback(kind, robotApiBaseUrl.value, reason);
  } finally {
    pending.value = false;
    await refreshConsole();
  }
}

async function refreshRadarProof(): Promise<void> {
  // Radar refresh 只刷新 no-motion scan proof snapshot，不开启任何底盘动作。
  await runRefreshAction(
    "radar_scan_proof_refresh",
    () => postRobotControlRadarScanProofRefresh(robotApiBaseUrl.value),
    radarRefreshResult,
    radarRefreshPending,
  );
}

async function runRadarLifecycleAction(
  action: "start" | "stop",
  request: () => Promise<RobotControlRadarLifecycleResponse>,
): Promise<void> {
  // lifecycle 只在高级诊断内触发；结果回写最近一次摘要并刷新只读状态。
  if (!robotApiBaseUrl.value.trim() || radarLifecyclePending.value) {
    return;
  }
  radarLifecyclePending.value = true;
  try {
    radarLifecycleResult.value = await request();
  } catch (err) {
    radarLifecycleResult.value = makeRadarLifecycleFallback(action, err instanceof Error ? err.message : `${action}_request_failed`);
  } finally {
    radarLifecyclePending.value = false;
    await refreshConsole();
  }
}

async function startRadarLifecycle(): Promise<void> {
  // 启动雷达只走固定传感器 endpoint；不会调用底盘、Nav2 或 /cmd_vel。
  await runRadarLifecycleAction("start", () => postRobotControlRadarStart(robotApiBaseUrl.value));
}

async function stopRadarLifecycle(): Promise<void> {
  // 停止雷达用于真实上位机 dry-run guard smoke；不会触发任何底盘运动。
  await runRadarLifecycleAction("stop", () => postRobotControlRadarStop(robotApiBaseUrl.value));
}

async function refreshMapProof(): Promise<void> {
  // Map refresh 只刷新 no-motion map proof snapshot，不开启建图、导航或路径执行。
  await runRefreshAction(
    "map_proof_refresh",
    () => postRobotControlMapProofRefresh(robotApiBaseUrl.value),
    mapRefreshResult,
    mapRefreshPending,
  );
}

async function refreshNav2Proof(): Promise<void> {
  // Nav2 refresh 只做 no-motion planner proof，不调用 Nav2 start/stop、NavigateToPose 或底盘接口。
  await runRefreshAction(
    "nav2_no_motion_proof_refresh",
    () => postRobotControlNav2ProofRefresh(robotApiBaseUrl.value),
    nav2RefreshResult,
    nav2RefreshPending,
  );
}

async function resetLocalizationProof(): Promise<void> {
  // 定位重置只在高级诊断触发；它发布一次 /initialpose，不请求路径、不发 /cmd_vel。
  await runRefreshAction(
    "localization_reset",
    () => postRobotControlLocalizeReset(robotApiBaseUrl.value),
    localizationResetResult,
    localizationResetPending,
  );
}

async function runNavGoalPreflight(): Promise<void> {
  // 预检按钮只请求 workstation 本机门禁；门禁通过也只是“可准备”，不会触发目标执行。
  if (!robotApiBaseUrl.value.trim() || navGoalPreflightPending.value) {
    return;
  }
  navGoalPreflightPending.value = true;
  try {
    navGoalPreflightResult.value = await postRobotControlNav2GoalPreflight(robotApiBaseUrl.value, {
      goal_frame_id: "map",
      goal_x: navGoalX.value,
      goal_y: navGoalY.value,
      goal_yaw: navGoalYaw.value,
      confirm_navigation_preflight: confirmNavigationPreflight.value,
    });
  } catch (err) {
    navGoalPreflightResult.value = makeNavGoalPreflightFallback(err instanceof Error ? err.message : "nav_goal_preflight_request_failed");
  } finally {
    navGoalPreflightPending.value = false;
    await refreshConsole();
  }
}

async function runMapLifecycleAction(
  action: "list" | "start" | "save",
  request: () => Promise<RobotControlMapLifecycleResponse>,
): Promise<void> {
  // 地图 lifecycle 动作结束后回刷 summary，让首页连接状态和高级 readback 保持一致。
  if (!robotApiBaseUrl.value.trim() || mapLifecyclePending.value) {
    return;
  }
  mapLifecyclePending.value = true;
  try {
    mapLifecycleResult.value = await request();
  } catch (err) {
    mapLifecycleResult.value = makeMapLifecycleFallback(action, err instanceof Error ? err.message : `${action}_request_failed`);
  } finally {
    mapLifecyclePending.value = false;
    await refreshConsole();
  }
}

async function loadMapList(): Promise<void> {
  // 列表读取是 GET-only 固定代理，不触发建图、不启动底盘、不发送 /cmd_vel。
  await runMapLifecycleAction("list", () => getRobotControlMapList(robotApiBaseUrl.value));
}

async function startMapRuntime(): Promise<void> {
  // 开始建图只在高级诊断内开放，走固定 /api/map/start no-motion runtime helper。
  await runMapLifecycleAction("start", () => postRobotControlMapStart(robotApiBaseUrl.value, mapLifecycleRequestBody()));
}

async function saveMap(): Promise<void> {
  // 保存只调用固定 /api/map/save；上位机会忽略 artifact_path 并在固定目录产出地图。
  await runMapLifecycleAction("save", () => postRobotControlMapSave(robotApiBaseUrl.value, mapLifecycleRequestBody()));
}

async function submitOperatorReport(): Promise<void> {
  // 现场材料提交只允许高级诊断显式点击；成功后回刷 /api/operator/report readback 摘要。
  if (!robotApiBaseUrl.value.trim() || operatorReportPending.value) {
    return;
  }
  operatorReportPending.value = true;
  try {
    operatorReportResult.value = await postRobotControlOperatorReport(robotApiBaseUrl.value, operatorReportRequestBody());
  } catch (err) {
    operatorReportResult.value = makeOperatorReportFallback(err instanceof Error ? err.message : "operator_report_request_failed");
  } finally {
    operatorReportPending.value = false;
    await refreshConsole();
  }
}

async function runCameraFirstFrameProbe(): Promise<void> {
  // 这个按钮只触发上位机固定首帧探针，不创建 WebRTC peer，也不发送任何运动命令。
  if (!robotApiBaseUrl.value.trim() || cameraFirstFrameProbePending.value) {
    return;
  }
  cameraFirstFrameProbePending.value = true;
  try {
    cameraFirstFrameProbeResult.value = await postRobotControlCameraFirstFrameProbe(robotApiBaseUrl.value);
  } catch (err) {
    cameraFirstFrameProbeResult.value = makeCameraFirstFrameProbeFallback(
      err instanceof Error ? err.message : "camera_first_frame_probe_request_failed",
    );
  } finally {
    cameraFirstFrameProbePending.value = false;
    await refreshConsole();
  }
}

function appendEvidenceSweepLine(label: string, value: string): void {
  // 巡检行只保留短状态，完整 payload 留在各自高级卡片和 sprint artifact。
  evidenceSweepLines.value = [...evidenceSweepLines.value, `${label}:${value}`];
}

async function runEvidenceSweep(): Promise<void> {
  // 一键巡检只走 summary/camera/radar/map/Nav2/stop 固定代理；不会发非 stop 运动。
  if (!canRunEvidenceSweep.value) {
    return;
  }
  evidenceSweepPending.value = true;
  evidenceSweepStartedAt.value = stampNow();
  evidenceSweepCompletedAt.value = "";
  evidenceSweepLines.value = [];
  try {
    await refreshConsole();
    appendEvidenceSweepLine("summary", robotSummary.value?.robot_api_connection.status ?? "not_loaded");

    await runCameraFirstFrameProbe();
    appendEvidenceSweepLine("camera_probe", cameraFirstFrameProbeResult.value?.status ?? "not_loaded");

    await refreshRadarProof();
    appendEvidenceSweepLine("radar", radarRefreshResult.value?.last_result_status ?? "not_loaded");

    await refreshMapProof();
    appendEvidenceSweepLine("map", mapRefreshResult.value?.last_result_status ?? "not_loaded");

    await refreshNav2Proof();
    appendEvidenceSweepLine("nav2", nav2RefreshResult.value?.last_result_status ?? "not_loaded");

    await sendStop();
    appendEvidenceSweepLine("stop", manualCommandResult.value?.status ?? "not_loaded");
  } catch (err) {
    appendEvidenceSweepLine("error", err instanceof Error ? err.message : "evidence_sweep_failed");
  } finally {
    evidenceSweepCompletedAt.value = stampNow();
    evidenceSweepPending.value = false;
  }
}

async function sendManualMotion(direction: "forward" | "back" | "left" | "right"): Promise<void> {
  // 非 stop 点动必须通过 checklist gate；即使远端成功，也继续维持 fail-closed UI。
  if (!canSendManualMotion.value) {
    return;
  }
  manualCommandPending.value = true;
  try {
    manualCommandResult.value = await postRobotControlBaseManual(robotApiBaseUrl.value, requestBodyForDirection(direction));
  } catch (err) {
    manualCommandResult.value = {
      schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
      command_kind: "manual",
      proxy_status: "command_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: robotApiBaseUrl.value,
      normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
      remote_endpoint: "/api/base/manual",
      remote_http_status: null,
      status: "blocked",
      requested_direction: direction,
      applied_direction: direction,
      requested_speed_mps: jogSpeedMps.value,
      clamped_speed_mps: Math.min(Math.max(jogSpeedMps.value, 0), manualSpeedLimit.value),
      requested_duration_ms: jogDurationMs.value,
      clamped_duration_ms: Math.min(Math.max(jogDurationMs.value, 0), manualDurationLimit.value),
      confirm_hil_checklist: hilChecklistConfirmed.value,
      non_stop_requires_confirm_hil_checklist: true,
      hil_checklist_gate_status: hilChecklistConfirmed.value ? "manual_allowed" : "manual_blocked_missing_checklist",
      checklist_missing: checklistMissing.value,
      operator_report_preflight: commandOperatorReportPreflightFallback("manual", err instanceof Error ? err.message : "manual_request_failed"),
      request_contract: {
        max_speed_mps: manualSpeedLimit.value,
        max_duration_ms: manualDurationLimit.value,
        allowed_directions: manualBoundary.value?.allowed_directions ?? ["forward", "back", "left", "right", "stop"],
      },
      ...commandEvidenceFallback("manual", err instanceof Error ? err.message : "manual_request_failed"),
      failure_reason: err instanceof Error ? err.message : "manual_request_failed",
      blocked_reasons: [err instanceof Error ? err.message : "manual_request_failed"],
    };
  } finally {
    manualCommandPending.value = false;
    await refreshConsole();
  }
}

async function sendStop(): Promise<void> {
  // stop 始终保留，是为了在 checklist 未完成时也有 fail-safe 退路。
  if (!robotApiBaseUrl.value.trim() || manualCommandPending.value) {
    return;
  }
  manualCommandPending.value = true;
  try {
    manualCommandResult.value = await postRobotControlBaseStop(robotApiBaseUrl.value);
  } catch (err) {
    manualCommandResult.value = {
      schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
      command_kind: "stop",
      proxy_status: "command_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: robotApiBaseUrl.value,
      normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
      remote_endpoint: "/api/base/stop",
      remote_http_status: null,
      status: "blocked",
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
      operator_report_preflight: commandOperatorReportPreflightFallback("stop", ""),
      request_contract: {
        max_speed_mps: manualSpeedLimit.value,
        max_duration_ms: manualDurationLimit.value,
        allowed_directions: manualBoundary.value?.allowed_directions ?? ["forward", "back", "left", "right", "stop"],
      },
      ...commandEvidenceFallback("stop", err instanceof Error ? err.message : "stop_request_failed"),
      failure_reason: err instanceof Error ? err.message : "stop_request_failed",
      blocked_reasons: [err instanceof Error ? err.message : "stop_request_failed"],
    };
  } finally {
    manualCommandPending.value = false;
    await refreshConsole();
  }
}

async function startPreview(): Promise<void> {
  // Start Preview 只在显式用户点击后创建会话，页面初始不自动占用 camera peer。
  if (!robotApiBaseUrl.value.trim() || previewStartPending.value) {
    return;
  }
  previewStartPending.value = true;
  failureReason.value = "";
  cleanupStatus.value = "starting_new_session";
  const epoch = sessionEpoch.value + 1;
  sessionEpoch.value = epoch;
  await cleanupPreview("stopped_by_user", "cleanup_before_restart");
  try {
    if (typeof globalThis.RTCPeerConnection !== "function") {
      throw new Error("webrtc_not_supported");
    }
    const peer = new RTCPeerConnection();
    previewPeerConnection.value = peer;
    previewStatus.value = "starting_local_peer";
    iceConnectionState.value = peer.iceConnectionState;
    videoTrackState.value = "waiting_remote_track";

    // recvonly transceiver 保证页面只收视频，不会在本机申请麦克风或发送媒体。
    peer.addTransceiver("video", { direction: "recvonly" });
    peer.oniceconnectionstatechange = () => {
      if (sessionEpoch.value !== epoch) {
        return;
      }
      iceConnectionState.value = peer.iceConnectionState;
    };
    peer.ontrack = (event) => {
      if (sessionEpoch.value !== epoch) {
        return;
      }
      const track = event.track;
      if (track.kind !== "video") {
        return;
      }
      const remoteStream = event.streams[0] ?? null;
      bindVideoTrack(track, remoteStream, epoch);
    };

    const localOffer = await peer.createOffer();
    await peer.setLocalDescription(localOffer);
    cleanupStatus.value = "waiting_ice_candidates";
    await waitForIceGatheringComplete(peer, epoch);
    const localDescription = peer.localDescription;
    if (!localDescription?.sdp || localDescription.type !== "offer") {
      throw new Error("invalid_local_offer");
    }

    previewStatus.value = "connecting_offer_posted";
    lastOfferAt.value = stampNow();
    const offerResponse = await postRobotControlCameraOffer(robotApiBaseUrl.value, {
      type: "offer",
      sdp: localDescription.sdp,
    });
    previewPeerId.value = offerResponse.peer_id;
    previewPeerBaseUrl.value = robotApiBaseUrl.value.trim();
    if (offerResponse.proxy_status !== "offer_forwarded" || !offerResponse.answer) {
      throw new Error(offerResponse.failure_reason || offerResponse.error || "offer_request_failed");
    }

    // setRemoteDescription 成功只是信令已闭环；真正 streaming 仍以 video track 到达为准。
    await peer.setRemoteDescription(offerResponse.answer);
  } catch (err) {
    const nextFailureReason = err instanceof Error ? err.message : "offer_request_failed";
    await cleanupPreview("stopped_by_user", "start_failed_cleanup");
    previewStatus.value = "start_failed";
    failureReason.value = nextFailureReason;
  } finally {
    previewStartPending.value = false;
  }
}

async function stopPreview(): Promise<void> {
  // Stop Preview 必须显式回收本地 peer 和远端 peer_id，防止 8088 active peers 残留。
  if (!canStopPreview.value) {
    return;
  }
  previewStopPending.value = true;
  failureReason.value = "";
  await cleanupPreview("stopped_by_user", "stopped_by_user");
  previewStopPending.value = false;
}

watch(previewVideo, (videoElement) => {
  // video 元素可能在 tab 切换后重建；这里把现有 stream 重新绑定，避免黑屏。
  if (videoElement && previewStream.value) {
    bindPreviewStreamToElement(previewStream.value, sessionEpoch.value);
    return;
  }
  syncPreviewVideoElementDiagnostics();
});

watch(robotApiBaseUrl, async (nextValue, previousValue) => {
  // baseUrl 切换必须先清旧 peer，避免把旧板端会话遗留在新的 operator 目标上。
  if (nextValue.trim() === previousValue.trim()) {
    return;
  }
  if (previewPeerConnection.value || previewPeerId.value) {
    await cleanupPreview("stopped_by_user", "base_url_changed_cleanup");
  }
});

watch(manualBoundary, () => {
  // 后端边界一旦变化，前端输入立即重新 clamp，避免显示值与实际允许值分叉。
  syncJogInputsToBoundary();
}, { immediate: true });

onMounted(() => {
  // 初次加载只拿到 baseUrl_not_provided 的 blocked 摘要，不会探测真实机器人。
  void refreshConsole();
});

onBeforeUnmount(() => {
  // 卸载时只做本地资源释放；远端 cleanup 尽量执行，但不能阻塞组件销毁。
  void cleanupPreview("stopped_by_user", "component_unmounted");
});
</script>

<template>
  <section class="workspace robot-console">
    <div class="simple-user-console" data-testid="pc-simple-user-first-screen">
      <form class="robot-quick-connect" @submit.prevent="refreshConsole">
        <label>
          <span>小车地址</span>
          <input v-model="robotApiBaseUrl" name="robotApiBaseUrl" placeholder="http://192.168.x.x:8787">
        </label>
        <button class="secondary" type="submit" :disabled="loading">连接/刷新</button>
        <span class="status-chip" :data-state="robotConnectionSummary.state">{{ robotConnectionSummary.state }}</span>
      </form>

      <div v-if="error" class="notice" role="alert">
        {{ error }}；安全锁定保持不变。
      </div>

      <div class="robot-console-grid" data-smoke-scope="simple-robot-control-first-screen">
        <article class="snapshot-panel">
          <h3>小车连接</h3>
          <div class="simple-status-row">
            <span class="status-chip" :data-state="robotConnectionSummary.state">{{ robotConnectionSummary.state }}</span>
            <span class="muted">{{ robotConnectionSummary.hint }}</span>
          </div>
          <div class="panel-action-row wrap-actions">
            <button type="button" :disabled="!canRunEvidenceSweep" @click="runEvidenceSweep">检查小车</button>
            <span class="status-chip" :data-state="plainEvidenceSweepSummary.state">{{ plainEvidenceSweepSummary.state }}</span>
          </div>
          <p class="panel-note">{{ plainEvidenceSweepSummary.hint }}</p>
        </article>

        <article class="snapshot-panel">
          <h3>实时画面</h3>
          <div class="panel-action-row">
            <button type="button" :disabled="!canStartPreview" @click="startPreview">打开画面</button>
            <button type="button" :disabled="!canStopPreview" @click="stopPreview">关闭画面</button>
            <span class="status-chip" :data-state="cameraSummary.state">{{ cameraSummary.state }}</span>
          </div>
          <video
            ref="previewVideo"
            data-testid="robot-camera-preview-video"
            autoplay
            muted
            playsinline
            @loadedmetadata="syncPreviewVideoElementDiagnostics"
            @loadeddata="handlePreviewVideoReady"
            @playing="handlePreviewVideoReady"
            @resize="syncPreviewVideoElementDiagnostics"
          />
          <p class="panel-note">{{ cameraSummary.hint }}</p>
        </article>

        <article class="snapshot-panel">
          <h3>雷达</h3>
          <div class="panel-action-row">
            <button type="button" :disabled="loading || radarRefreshPending || !robotApiBaseUrl.trim()" @click="refreshRadarProof">
              刷新雷达
            </button>
            <span class="status-chip" :data-state="radarSummary.state">{{ radarSummary.state }}</span>
          </div>
          <p class="panel-note">{{ radarSummary.hint }}</p>
        </article>

        <article class="snapshot-panel">
          <h3>地图</h3>
          <div class="panel-action-row wrap-actions">
            <button type="button" :disabled="loading || mapRefreshPending || !robotApiBaseUrl.trim()" @click="refreshMapProof">
              刷新地图
            </button>
            <button type="button" :disabled="loading || mapLifecyclePending || !robotApiBaseUrl.trim()" @click="loadMapList">
              地图列表
            </button>
            <span class="status-chip" :data-state="mapSummary.state">{{ mapSummary.state }}</span>
            <span class="status-chip" :data-state="mapLifecycleSummary.state">{{ mapLifecycleSummary.state }}</span>
          </div>
          <p class="panel-note">{{ mapSummary.hint }}</p>
          <p class="panel-note">{{ mapLifecycleSummary.hint }}</p>
        </article>

        <article class="snapshot-panel">
          <h3>移动/导航</h3>
          <div class="panel-action-row wrap-actions">
            <span class="status-chip" :data-state="plainMotionSummary.state">{{ plainMotionSummary.state }}</span>
            <button type="button" class="danger-button compact-stop" :disabled="!canSendStop" @click="sendStop">停止</button>
          </div>
          <p class="panel-note">{{ plainMotionSummary.hint }}</p>
        </article>
      </div>
    </div>

    <details class="advanced-details">
      <summary>高级诊断</summary>
      <div class="advanced-grid">
        <section class="advanced-block">
          <h3>连接详情</h3>
          <form class="robot-control-form" @submit.prevent="refreshConsole">
            <label>
              <span>task_id</span>
              <input v-model="taskId" name="task_id" placeholder="task_id">
            </label>
            <label>
              <span>O6 consumer base URL</span>
              <input v-model="o6ConsumerBaseUrl" name="o6ConsumerBaseUrl" placeholder="http://127.0.0.1:8088">
            </label>
            <label>
              <span>Mock/field manifest JSON</span>
              <input v-model="fieldEvidenceManifestJson" name="fieldEvidenceManifestJson" placeholder="optional local JSON">
            </label>
            <button class="secondary" type="submit" :disabled="loading">刷新状态</button>
          </form>
          <dl class="kv compact-kv">
            <dt>selected</dt>
            <dd>{{ selectedTaskSummary }}</dd>
            <dt>source</dt>
            <dd>{{ routeReplaySource }}</dd>
            <dt>task status</dt>
            <dd>{{ taskDetail?.task_summary?.task_status_summary ?? "blocked_not_loaded" }}</dd>
            <dt>safe_to_control</dt>
            <dd>safe_to_control=false</dd>
            <dt>delivery_success</dt>
            <dd>delivery_success=false</dd>
            <dt>primary_actions_enabled</dt>
            <dd>primary_actions_enabled=false</dd>
            <dt>proxy</dt>
            <dd>Node server only; Vue direct access=false</dd>
            <dt>normalized base URL</dt>
            <dd>{{ robotSummary?.normalized_base_url ?? "not_loaded" }}</dd>
            <dt>Robot API status</dt>
            <dd>{{ robotSummary?.robot_api_connection.status ?? "not_loaded" }}</dd>
            <dt>read count</dt>
            <dd>
              loaded={{ robotSummary?.robot_api_connection.loaded_count ?? 0 }},
              failed={{ robotSummary?.robot_api_connection.failed_count ?? 0 }},
              blocked={{ robotSummary?.robot_api_connection.blocked_count ?? 0 }}
            </dd>
            <dt>blocked reason</dt>
            <dd>{{ listText(robotSummary?.robot_api_connection.blocked_reasons, "none") }}</dd>
          </dl>
        </section>

        <section class="advanced-block">
          <h3>实时画面详情</h3>
          <div class="robot-control-form">
            <button
              class="secondary"
              type="button"
              :disabled="loading || cameraFirstFrameProbePending || !robotApiBaseUrl.trim()"
              @click="runCameraFirstFrameProbe"
            >
              首帧探针（高级）
            </button>
          </div>
          <dl class="kv compact-kv">
            <dt>first_frame_probe</dt>
            <dd>{{ cameraFirstFrameProbeSummary }}</dd>
            <dt>probe_remote</dt>
            <dd>
              {{ cameraFirstFrameProbeResult?.remote_endpoint ?? "/api/camera/first-frame/probe" }}
              -> {{ cameraFirstFrameProbeResult?.remote_http_status ?? "n/a" }}
            </dd>
            <dt>probe_device</dt>
            <dd>{{ cameraFirstFrameProbeResult?.probe_key_values.device ?? "not_loaded" }}</dd>
            <dt>probe_fourcc</dt>
            <dd>{{ cameraFirstFrameProbeResult?.probe_key_values.requested_fourcc ?? "not_loaded" }}</dd>
            <dt>probe_open_read</dt>
            <dd>
              open={{ cameraFirstFrameProbeResult?.probe_key_values.open_ok ?? "not_loaded" }},
              read={{ cameraFirstFrameProbeResult?.probe_key_values.read_ok ?? "not_loaded" }}
            </dd>
            <dt>probe_timeout</dt>
            <dd>{{ cameraFirstFrameProbeResult?.probe_key_values.first_frame_timeout ?? "not_loaded" }}</dd>
            <dt>probe_failure</dt>
            <dd>{{ cameraFirstFrameProbeResult?.failure_reason || cameraFirstFrameProbeResult?.probe_key_values.failure_reason || "none" }}</dd>
            <dt>probe_visible</dt>
            <dd>{{ cameraFirstFrameProbeResult?.probe_key_values.visible_content_proven ?? "false" }}</dd>
            <dt>probe_luma</dt>
            <dd>
              mean={{ cameraFirstFrameProbeResult?.probe_key_values.mean_luma ?? "not_available" }},
              non_black={{ cameraFirstFrameProbeResult?.probe_key_values.non_black_ratio ?? "not_available" }}
            </dd>
            <dt>probe_dangerous_fields</dt>
            <dd>{{ listText(cameraFirstFrameProbeResult?.hard_dangerous_true_fields, "none") }}</dd>
            <dt>preview_status</dt>
            <dd>{{ previewStatus }}</dd>
            <dt>failure_reason</dt>
            <dd>{{ failureReason || "none" }}</dd>
            <dt>peer_id</dt>
            <dd>{{ previewPeerId || "not_assigned" }}</dd>
            <dt>peer base URL</dt>
            <dd>{{ previewPeerBaseUrl || "not_assigned" }}</dd>
            <dt>ice_connection_state</dt>
            <dd>{{ iceConnectionState }}</dd>
            <dt>video_track_state</dt>
            <dd>{{ videoTrackState }}</dd>
            <dt>video_element_src_object</dt>
            <dd>{{ videoElementHasSrcObject ? "true" : "false" }}</dd>
            <dt>video_element_ready_state</dt>
            <dd>{{ videoElementReadyState }}</dd>
            <dt>video_element_size</dt>
            <dd>{{ videoElementWidth }}x{{ videoElementHeight }}</dd>
            <dt>video_element_presented_frames</dt>
            <dd>{{ videoElementPresentedFrames ?? "not_available" }}</dd>
            <dt>video_element_frame_status</dt>
            <dd>{{ videoElementFrameStatus }}</dd>
            <dt>sample_status</dt>
            <dd>{{ previewFrameSampleStatus }}</dd>
            <dt>mean_luma</dt>
            <dd>{{ previewFrameSampleMeanLuma ?? "not_sampled" }}</dd>
            <dt>max_luma</dt>
            <dd>{{ previewFrameSampleMaxLuma ?? "not_sampled" }}</dd>
            <dt>non_black_ratio_ge16</dt>
            <dd>{{ previewFrameSampleNonBlackRatio ?? "not_sampled" }}</dd>
            <dt>sample_attempts</dt>
            <dd>{{ previewFrameSampleAttempts }}</dd>
            <dt>sample_canvas_size</dt>
            <dd>{{ previewFrameSampleCanvasSize }}</dd>
            <dt>sampled_at</dt>
            <dd>{{ previewFrameSampledAt || "never" }}</dd>
            <dt>sample_failure</dt>
            <dd>{{ previewFrameSampleFailure || "none" }}</dd>
            <dt>last_offer_at</dt>
            <dd>{{ lastOfferAt || "never" }}</dd>
            <dt>last_stop_at</dt>
            <dd>{{ lastStopAt || "never" }}</dd>
            <dt>cleanup_status</dt>
            <dd>{{ cleanupStatus }}</dd>
            <dt>camera_health</dt>
            <dd>{{ robotSummary?.readback_summary.camera.status ?? "not_loaded" }}</dd>
            <dt>camera_devices</dt>
            <dd>{{ robotSummary?.readback_summary.camera.devices_status ?? "not_loaded" }}</dd>
            <dt>camera_video_source</dt>
            <dd>{{ robotSummary?.readback_summary.camera.video_source ?? "not_loaded" }}</dd>
            <dt>camera_selected_path</dt>
            <dd>{{ robotSummary?.readback_summary.camera.selected_path ?? "not_loaded" }}</dd>
            <dt>camera_source_mode</dt>
            <dd>{{ robotSummary?.readback_summary.camera.video_source_mode ?? "not_loaded" }}</dd>
            <dt>camera_active_peer_count</dt>
            <dd>{{ robotSummary?.readback_summary.camera.active_peer_count ?? "not_loaded" }}</dd>
            <dt>camera_last_offer_error</dt>
            <dd>{{ robotSummary?.readback_summary.camera.last_offer_error ?? "none" }}</dd>
            <dt>camera_last_offer_failure</dt>
            <dd>{{ robotSummary?.readback_summary.camera.last_offer_failure_reason ?? "none" }}</dd>
          </dl>
        </section>

        <section class="advanced-block">
          <h3>雷达详情</h3>
          <div class="robot-control-form">
            <button class="secondary" type="button" :disabled="loading || radarLifecyclePending || !robotApiBaseUrl.trim()" @click="startRadarLifecycle">
              启动雷达（高级）
            </button>
            <button class="secondary" type="button" :disabled="loading || radarLifecyclePending || !robotApiBaseUrl.trim()" @click="stopRadarLifecycle">
              停止雷达（高级）
            </button>
          </div>
          <dl class="kv compact-kv">
            <dt>pending</dt>
            <dd>{{ radarRefreshPending ? "pending" : "idle" }}</dd>
            <dt>last result status</dt>
            <dd>{{ radarRefreshResult?.last_result_status ?? "not_loaded" }}</dd>
            <dt>failure reason</dt>
            <dd>{{ radarRefreshResult?.failure_reason || "none" }}</dd>
            <dt>latest readback key values</dt>
            <dd>{{ recordText(radarRefreshResult?.latest_readback_key_values) }}</dd>
            <dt>non-motion evidence actions</dt>
            <dd>{{ listText(radarRefreshResult?.non_motion_evidence_actions_observed, "none") }}</dd>
            <dt>hard dangerous true fields</dt>
            <dd>{{ listText(radarRefreshResult?.hard_dangerous_true_fields, "none") }}</dd>
            <dt>last refreshed time</dt>
            <dd>{{ timestampText(radarRefreshResult?.last_refreshed_at_ms) }}</dd>
            <dt>blocked reasons</dt>
            <dd>{{ listText(radarRefreshResult?.blocked_reasons, "none") }}</dd>
            <dt>lifecycle pending</dt>
            <dd>{{ radarLifecyclePending ? "pending" : "idle" }}</dd>
            <dt>lifecycle summary</dt>
            <dd>{{ radarLifecycleSummary }}</dd>
            <dt>lifecycle remote</dt>
            <dd>
              {{ radarLifecycleResult?.remote_method ?? "POST" }}
              {{ radarLifecycleResult?.remote_endpoint ?? "not_loaded" }}
              -> {{ radarLifecycleResult?.remote_http_status ?? "n/a" }}
            </dd>
            <dt>lifecycle status</dt>
            <dd>{{ radarLifecycleResult?.proxy_status ?? "not_loaded" }} / {{ radarLifecycleResult?.status ?? "not_loaded" }}</dd>
            <dt>lifecycle command_result</dt>
            <dd>
              mode={{ radarLifecycleResult?.command_result.mode ?? "not_loaded" }},
              executed={{ radarLifecycleResult?.command_result.executed ?? false }},
              ok={{ radarLifecycleResult?.command_result.ok ?? "n/a" }}
            </dd>
            <dt>lifecycle failure</dt>
            <dd>{{ radarLifecycleResult?.failure_reason || "none" }}</dd>
            <dt>lifecycle blocked reasons</dt>
            <dd>{{ listText(radarLifecycleResult?.blocked_reasons, "none") }}</dd>
            <dt>lifecycle dangerous fields</dt>
            <dd>{{ listText(radarLifecycleResult?.hard_dangerous_true_fields, "none") }}</dd>
          </dl>
        </section>

        <section class="advanced-block">
          <h3>地图详情</h3>
          <div class="robot-control-form">
            <label>
              <span>map_name（可选）</span>
              <input v-model="mapLifecycleMapName" name="mapLifecycleMapName" maxlength="80" placeholder="floor_1">
            </label>
            <label>
              <span>artifact_path（可选）</span>
              <input v-model="mapLifecycleArtifactPath" name="mapLifecycleArtifactPath" maxlength="240" placeholder="maps/floor_1.yaml">
            </label>
            <button class="secondary" type="button" :disabled="loading || mapLifecyclePending || !robotApiBaseUrl.trim()" @click="loadMapList">
              地图列表
            </button>
            <button class="secondary" type="button" :disabled="loading || mapLifecyclePending || !robotApiBaseUrl.trim()" @click="saveMap">
              保存地图
            </button>
            <button class="secondary" type="button" :disabled="loading || mapLifecyclePending || !robotApiBaseUrl.trim()" @click="startMapRuntime">
              开始建图（高级）
            </button>
            <button class="secondary" type="button" disabled title="受控/高级：本轮不开放 reset">
              Reset（受控/高级，禁用）
            </button>
          </div>
          <dl class="kv compact-kv">
            <dt>pending</dt>
            <dd>{{ mapRefreshPending ? "pending" : "idle" }}</dd>
            <dt>last result status</dt>
            <dd>{{ mapRefreshResult?.last_result_status ?? "not_loaded" }}</dd>
            <dt>failure reason</dt>
            <dd>{{ mapRefreshResult?.failure_reason || "none" }}</dd>
            <dt>latest readback key values</dt>
            <dd>{{ recordText(mapRefreshResult?.latest_readback_key_values) }}</dd>
            <dt>non-motion evidence actions</dt>
            <dd>{{ listText(mapRefreshResult?.non_motion_evidence_actions_observed, "none") }}</dd>
            <dt>hard dangerous true fields</dt>
            <dd>{{ listText(mapRefreshResult?.hard_dangerous_true_fields, "none") }}</dd>
            <dt>last refreshed time</dt>
            <dd>{{ timestampText(mapRefreshResult?.last_refreshed_at_ms) }}</dd>
            <dt>blocked reasons</dt>
            <dd>{{ listText(mapRefreshResult?.blocked_reasons, "none") }}</dd>
            <dt>lifecycle action</dt>
            <dd>{{ mapLifecycleResult?.action ?? "not_loaded" }}</dd>
            <dt>lifecycle HTTP</dt>
            <dd>
              {{ mapLifecycleResult?.remote_method ?? "n/a" }}
              {{ mapLifecycleResult?.remote_endpoint ?? "not_loaded" }}
              -> {{ mapLifecycleResult?.remote_http_status ?? "n/a" }}
            </dd>
            <dt>lifecycle status</dt>
            <dd>{{ mapLifecycleResult?.proxy_status ?? "not_loaded" }} / {{ mapLifecycleResult?.status ?? "not_loaded" }}</dd>
            <dt>map_count</dt>
            <dd>{{ mapLifecycleResult?.map_count ?? "n/a" }}</dd>
            <dt>map names</dt>
            <dd>{{ listText(mapLifecycleResult?.map_names, "none") }}</dd>
            <dt>command_result</dt>
            <dd>
              mode={{ mapLifecycleResult?.command_result.mode ?? "not_loaded" }},
              executed={{ mapLifecycleResult?.command_result.executed ?? false }},
              ok={{ mapLifecycleResult?.command_result.ok ?? "n/a" }}
            </dd>
            <dt>request body</dt>
            <dd>{{ JSON.stringify(mapLifecycleResult?.request_body ?? {}) }}</dd>
            <dt>lifecycle failure</dt>
            <dd>{{ mapLifecycleResult?.failure_reason || "none" }}</dd>
            <dt>lifecycle blocked reasons</dt>
            <dd>{{ listText(mapLifecycleResult?.blocked_reasons, "none") }}</dd>
            <dt>lifecycle dangerous fields</dt>
            <dd>{{ listText(mapLifecycleResult?.hard_dangerous_true_fields, "none") }}</dd>
          </dl>
        </section>

        <section class="advanced-block">
          <h3>Nav2 规划详情</h3>
          <div class="robot-control-form">
            <button class="secondary" type="button" :disabled="loading || nav2RefreshPending || !robotApiBaseUrl.trim()" @click="refreshNav2Proof">
              检查路径（高级）
            </button>
            <button class="secondary" type="button" :disabled="loading || localizationResetPending || !robotApiBaseUrl.trim()" @click="resetLocalizationProof">
              定位重置（高级）
            </button>
          </div>
          <p class="panel-note">{{ nav2PlanningSummary.state }}：{{ nav2PlanningSummary.hint }}</p>
          <form class="robot-control-form" @submit.prevent="runNavGoalPreflight">
            <label>
              <span>目标 x（m）</span>
              <input v-model.number="navGoalX" name="navGoalX" type="number" min="-3" max="3" step="0.1">
            </label>
            <label>
              <span>目标 y（m）</span>
              <input v-model.number="navGoalY" name="navGoalY" type="number" min="-3" max="3" step="0.1">
            </label>
            <label>
              <span>目标 yaw（rad）</span>
              <input v-model.number="navGoalYaw" name="navGoalYaw" type="number" min="-3.1416" max="3.1416" step="0.1">
            </label>
            <label class="checkbox-inline">
              <input v-model="confirmNavigationPreflight" name="confirmNavigationPreflight" type="checkbox">
              <span>确认仅做导航目标预检</span>
            </label>
            <button class="secondary" type="submit" :disabled="loading || navGoalPreflightPending || !robotApiBaseUrl.trim()">
              导航目标预检（高级）
            </button>
          </form>
          <dl class="kv compact-kv">
            <dt>goal preflight pending</dt>
            <dd>{{ navGoalPreflightPending ? "pending" : "idle" }}</dd>
            <dt>goal preflight status</dt>
            <dd>
              {{ navGoalPreflightResult?.proxy_status ?? "not_loaded" }} /
              {{ navGoalPreflightResult?.preflight_status ?? "not_loaded" }}
            </dd>
            <dt>goal request</dt>
            <dd>{{ JSON.stringify(navGoalPreflightResult?.goal_request ?? { goal_frame_id: "map", goal_x: navGoalX, goal_y: navGoalY, goal_yaw: navGoalYaw, confirm_navigation_preflight: confirmNavigationPreflight }) }}</dd>
            <dt>goal missing requirements</dt>
            <dd>{{ listText(navGoalPreflightResult?.missing_requirements, "none") }}</dd>
            <dt>goal localization summary</dt>
            <dd>{{ JSON.stringify(navGoalPreflightResult?.localization_summary ?? {}) }}</dd>
            <dt>goal path summary</dt>
            <dd>{{ JSON.stringify(navGoalPreflightResult?.nav2_path_summary ?? {}) }}</dd>
            <dt>goal operator material gate</dt>
            <dd>
              {{ navGoalPreflightResult?.operator_report_preflight.status ?? "not_loaded" }} /
              {{ navGoalPreflightResult?.operator_report_preflight.failure_reason || "none" }}
            </dd>
            <dt>goal readback endpoints</dt>
            <dd>
              {{
                navGoalPreflightResult?.remote_read_endpoints
                  .map((endpoint) => `${endpoint.endpoint}:${endpoint.request_status}:${endpoint.http_status ?? "n/a"}`)
                  .join(" | ") ?? "none"
              }}
            </dd>
            <dt>goal forbidden endpoints</dt>
            <dd>{{ listText(navGoalPreflightResult?.forbidden_remote_endpoints_not_called, "none") }}</dd>
            <dt>goal robot_control_executed</dt>
            <dd>robot_control_executed={{ navGoalPreflightResult?.robot_control_executed ?? false }}</dd>
            <dt>localize reset pending</dt>
            <dd>{{ localizationResetPending ? "pending" : "idle" }}</dd>
            <dt>localize reset endpoint</dt>
            <dd>{{ localizationResetResult?.remote_endpoint ?? "/api/localize/reset" }}</dd>
            <dt>localize reset status</dt>
            <dd>{{ localizationResetResult?.last_result_status ?? "not_loaded" }}</dd>
            <dt>localize reset keys</dt>
            <dd>{{ recordText(localizationResetResult?.latest_readback_key_values) }}</dd>
            <dt>localize reset failure</dt>
            <dd>{{ localizationResetResult?.failure_reason || "none" }}</dd>
            <dt>localize reset blocked reasons</dt>
            <dd>{{ listText(localizationResetResult?.blocked_reasons, "none") }}</dd>
            <dt>localize reset dangerous fields</dt>
            <dd>{{ listText(localizationResetResult?.hard_dangerous_true_fields, "none") }}</dd>
            <dt>pending</dt>
            <dd>{{ nav2RefreshPending ? "pending" : "idle" }}</dd>
            <dt>remote endpoint</dt>
            <dd>{{ nav2RefreshResult?.remote_endpoint ?? "/api/nav2/proof/refresh" }}</dd>
            <dt>last result status</dt>
            <dd>{{ nav2RefreshResult?.last_result_status ?? "not_loaded" }}</dd>
            <dt>failure reason</dt>
            <dd>{{ nav2RefreshResult?.failure_reason || "none" }}</dd>
            <dt>latest readback key values</dt>
            <dd>{{ recordText(nav2RefreshResult?.latest_readback_key_values) }}</dd>
            <dt>hard dangerous true fields</dt>
            <dd>{{ listText(nav2RefreshResult?.hard_dangerous_true_fields, "none") }}</dd>
            <dt>last refreshed time</dt>
            <dd>{{ timestampText(nav2RefreshResult?.last_refreshed_at_ms) }}</dd>
            <dt>blocked reasons</dt>
            <dd>{{ listText(nav2RefreshResult?.blocked_reasons, "none") }}</dd>
            <dt>control boundary</dt>
            <dd>no Nav2 start/stop; no NavigateToPose; no /cmd_vel; no /api/base/manual</dd>
          </dl>
        </section>

        <section class="advanced-block">
          <h3>任务与证据</h3>
          <div class="robot-control-form">
            <button class="secondary" type="button" :disabled="!canRunEvidenceSweep" @click="runEvidenceSweep">
              一键证据巡检（高级）
            </button>
          </div>
          <dl class="kv compact-kv">
            <dt>evidence_sweep</dt>
            <dd>{{ evidenceSweepSummary }}</dd>
            <dt>sweep_started_at</dt>
            <dd>{{ evidenceSweepStartedAt || "never" }}</dd>
            <dt>sweep_completed_at</dt>
            <dd>{{ evidenceSweepCompletedAt || "never" }}</dd>
            <dt>O3 proof summary</dt>
            <dd>
              {{ robotSummary?.o3_proof_summary.proof_status ?? "not_loaded" }};
              {{ robotSummary?.o3_proof_summary.delivery_success ?? false }};
              {{ robotSummary?.o3_proof_summary.primary_actions_enabled ?? false }}
            </dd>
            <dt>root_causes</dt>
            <dd>{{ listText(robotSummary?.o3_proof_summary.root_causes) }}</dd>
            <dt>not_proven</dt>
            <dd>{{ listText(robotSummary?.o3_proof_summary.not_proven) }}</dd>
            <dt>route replay</dt>
            <dd>{{ taskDetail?.trajectory.status ?? "blocked_not_loaded" }} / frames={{ taskDetail?.trajectory.frame_count ?? 0 }}</dd>
            <dt>events</dt>
            <dd>{{ taskDetail?.events.status ?? "blocked_not_loaded" }} / count={{ taskDetail?.events.count ?? 0 }}</dd>
            <dt>tunnel</dt>
            <dd>{{ taskDetail?.tunnel_status.latest_known_status ?? "blocked_not_loaded" }}</dd>
            <dt>field evidence</dt>
            <dd>{{ taskDetail?.field_evidence.artifact_status ?? "blocked_not_loaded" }}</dd>
            <dt>manifest gate</dt>
            <dd>{{ taskDetail?.field_evidence.manifest_gate.status ?? "blocked_not_loaded" }}</dd>
            <dt>evidence</dt>
            <dd>{{ taskDetail?.evidence.status ?? "blocked_not_loaded" }} / count={{ taskDetail?.evidence.count ?? 0 }}</dd>
            <dt>labeling</dt>
            <dd>{{ taskDetail?.labeling.status ?? "blocked_not_loaded" }} / labels={{ taskDetail?.labeling.label_count ?? 0 }}</dd>
            <dt>keyframe/sample</dt>
            <dd>{{ sampleText(taskDetail?.evidence.sample_evidence) }}</dd>
          </dl>
        </section>

        <section class="advanced-block">
          <h3>现场 HIL 材料</h3>
          <form class="robot-control-form" @submit.prevent="submitOperatorReport">
            <label>
              <span>evidence_ref</span>
              <input v-model="operatorReportEvidenceRef" name="operatorReportEvidenceRef" maxlength="512" placeholder="field-hil-20260611-0620-op">
            </label>
            <label>
              <span>site_state</span>
              <input v-model="operatorReportSiteState" name="operatorReportSiteState" maxlength="160" placeholder="field_operator_claim_ready_for_review">
            </label>
            <label>
              <span>外部视频 ref</span>
              <input v-model="operatorReportExternalVideoRef" name="operatorReportExternalVideoRef" maxlength="512" placeholder="phone-video.mp4">
            </label>
            <label>
              <span>相机 artifact ref</span>
              <input v-model="operatorReportCameraArtifactsRef" name="operatorReportCameraArtifactsRef" maxlength="512" placeholder="runtime/camera/latest_metrics.json">
            </label>
            <label>
              <span>feedback ref</span>
              <input v-model="operatorReportWheelFeedbackRef" name="operatorReportWheelFeedbackRef" maxlength="512" placeholder="runtime/wave_rover_feedback_debug.jsonl">
            </label>
            <label>
              <span>scan delta ref</span>
              <input v-model="operatorReportScanDeltaRef" name="operatorReportScanDeltaRef" maxlength="512" placeholder="runtime/scan_delta/latest_metrics.json">
            </label>
            <label>
              <span>route/map ref</span>
              <input v-model="operatorReportRouteMapRef" name="operatorReportRouteMapRef" maxlength="512" placeholder="runtime/routes/field-route.csv">
            </label>
            <label>
              <span>operator_notes</span>
              <input v-model="operatorReportNotes" name="operatorReportNotes" maxlength="2000" placeholder="no-motion material submit from PC">
            </label>
            <div class="checklist-box compact-checklist">
              <p class="checklist-title">现场材料 claim</p>
              <label>
                <input v-model="operatorReportFlags.operator_present" type="checkbox">
                <span>operator present</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.physical_clearance_confirmed" type="checkbox">
                <span>clearance</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.emergency_stop_ready" type="checkbox">
                <span>emergency stop ready</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.observed_motion" type="checkbox">
                <span>observed motion</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.observed_stop" type="checkbox">
                <span>observed stop</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.external_video_recorded" type="checkbox">
                <span>external video recorded</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.visible_content_proven" type="checkbox">
                <span>camera visible</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.wheel_feedback_lr_nonzero_proven" type="checkbox">
                <span>wheel feedback nonzero</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.physical_motion_lidar_delta_proven" type="checkbox">
                <span>LiDAR delta</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.real_route_map_proven" type="checkbox">
                <span>route/map</span>
              </label>
              <label>
                <input v-model="operatorReportFlags.delivery_success" type="checkbox">
                <span>delivery claim</span>
              </label>
            </div>
            <button class="secondary" type="submit" :disabled="loading || operatorReportPending || !robotApiBaseUrl.trim()">
              提交现场材料（高级）
            </button>
          </form>
          <dl class="kv compact-kv">
            <dt>latest submit</dt>
            <dd>
              {{ operatorReportPending ? "pending" : operatorReportResult?.proxy_status ?? "not_submitted" }} /
              {{ operatorReportResult?.status ?? "not_loaded" }}
            </dd>
            <dt>submit remote</dt>
            <dd>
              {{ operatorReportResult?.remote_method ?? "POST" }}
              {{ operatorReportResult?.remote_endpoint ?? "/api/operator/report" }}
              -> {{ operatorReportResult?.remote_http_status ?? "n/a" }}
            </dd>
            <dt>submit failure</dt>
            <dd>{{ operatorReportResult?.failure_reason || "none" }}</dd>
            <dt>submit rejected fields</dt>
            <dd>{{ listText(operatorReportResult?.rejected_fields, "none") }}</dd>
            <dt>submit dangerous fields</dt>
            <dd>{{ listText(operatorReportResult?.hard_dangerous_true_fields, "none") }}</dd>
            <dt>submit request claims</dt>
            <dd>{{ JSON.stringify(operatorReportResult?.structured_hil_claims ?? {}) }}</dd>
            <dt>status</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.status ?? "not_loaded" }}</dd>
            <dt>report status</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.report_status ?? "not_loaded" }}</dd>
            <dt>evidence_ref</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.evidence_ref ?? "not_loaded" }}</dd>
            <dt>operator_present</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.operator_present ?? "not_loaded" }}</dd>
            <dt>physical_clearance</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.physical_clearance ?? "not_loaded" }}</dd>
            <dt>emergency_stop</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.emergency_stop ?? "not_loaded" }}</dd>
            <dt>外部视频</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.external_video ?? "not_loaded" }}</dd>
            <dt>相机可见</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.camera_visible ?? "not_loaded" }}</dd>
            <dt>轮速反馈</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.wheel_feedback ?? "not_loaded" }}</dd>
            <dt>LiDAR delta</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.lidar_delta ?? "not_loaded" }}</dd>
            <dt>route/map</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.route_map ?? "not_loaded" }}</dd>
            <dt>delivery claim</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.delivery_claim ?? "not_loaded" }}</dd>
            <dt>site_state</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.site_state ?? "not_loaded" }}</dd>
            <dt>source</dt>
            <dd>{{ robotSummary?.operator_hil_material_summary.source_path ?? "operator_report_latest.structured_hil_claims" }}</dd>
          </dl>
        </section>

        <section class="advanced-block">
          <h3>现场点动设置 / 控制边界</h3>
          <p class="muted">{{ robotSummary?.safe_command_boundary.locked_reason ?? "locked by V1 boundary" }}</p>
          <div class="motion-pad">
            <button type="button" :disabled="!canSendManualMotion" @click="sendManualMotion('forward')">前进</button>
            <div class="motion-middle-row">
              <button type="button" :disabled="!canSendManualMotion" @click="sendManualMotion('left')">左转</button>
              <button type="button" class="danger-button" :disabled="!canSendStop" @click="sendStop">停止</button>
              <button type="button" :disabled="!canSendManualMotion" @click="sendManualMotion('right')">右转</button>
            </div>
            <button type="button" :disabled="!canSendManualMotion" @click="sendManualMotion('back')">后退</button>
          </div>
          <div class="motion-limits">
            <label>
              <span>速度上限（m/s）</span>
              <input v-model.number="jogSpeedMps" type="number" min="0" :max="manualSpeedLimit" step="0.01">
            </label>
            <label>
              <span>时长上限（ms）</span>
              <input v-model.number="jogDurationMs" type="number" min="0" :max="manualDurationLimit" step="50">
            </label>
          </div>
          <div class="checklist-box">
            <p class="checklist-title">现场确认</p>
            <label v-for="item in hilChecklist" :key="item.id" class="checklist-item">
              <input v-model="item.checked" type="checkbox">
              <span>{{ item.label }}</span>
            </label>
          </div>
          <p class="panel-note">{{ manualMotionSummary.hint }}</p>
          <p v-if="operatorMaterialMissingFields.length" class="panel-note">
            材料未满足，本机不会发送点动。缺项：{{ operatorMaterialMissingFields.join("、") }}
          </p>
          <p class="panel-note">非 stop 方向必须同时满足地址、checklist、现场材料且当前没有 pending；stop 可在材料缺失时单独发送。</p>
          <dl class="kv compact-kv">
            <dt>manual motion entry</dt>
            <dd>{{ robotSummary?.safe_command_boundary.manual_motion_entry_status ?? "not_loaded" }}</dd>
            <dt>material gate</dt>
            <dd>{{ operatorMaterialGateSummary.state }} / {{ operatorMaterialGateSummary.hint }}</dd>
            <dt>material missing fields</dt>
            <dd>{{ operatorMaterialMissingFields.length ? operatorMaterialMissingFields.join(", ") : "none" }}</dd>
            <dt>operator report preflight</dt>
            <dd>
              {{ manualCommandResult?.operator_report_preflight.status ?? "not_loaded" }} /
              {{ manualCommandResult?.operator_report_preflight.failure_reason || "none" }}
            </dd>
            <dt>operator report preflight missing</dt>
            <dd>{{ listText(manualCommandResult?.operator_report_preflight.missing_fields, "none") }}</dd>
            <dt>operator report preflight summary</dt>
            <dd>
              endpoint={{ manualCommandResult?.operator_report_preflight.source_endpoint ?? "/api/operator/report" }},
              http={{ manualCommandResult?.operator_report_preflight.http_status ?? "n/a" }},
              report={{ manualCommandResult?.operator_report_preflight.report_status ?? "not_loaded" }},
              evidence={{ manualCommandResult?.operator_report_preflight.evidence_ref ?? "not_loaded" }}
            </dd>
            <dt>manual stop endpoint</dt>
            <dd>{{ robotSummary?.safe_command_boundary.stop_endpoint ?? "/api/base/stop" }}</dd>
            <dt>manual limits</dt>
            <dd>
              speed&lt;={{ robotSummary?.safe_command_boundary.speed_limit_mps ?? 0.12 }} m/s;
              duration&lt;={{ robotSummary?.safe_command_boundary.duration_limit_ms ?? 800 }} ms
            </dd>
            <dt>command_dispatch_enabled</dt>
            <dd>command_dispatch_enabled=false</dd>
            <dt>manual_control_enabled</dt>
            <dd>manual_control_enabled=false</dd>
            <dt>navigate_goal_enabled</dt>
            <dd>navigate_goal_enabled=false</dd>
            <dt>keyboard_control_enabled</dt>
            <dd>keyboard_control_enabled=false</dd>
            <dt>robot_control_executed</dt>
            <dd>robot_control_executed=false</dd>
            <dt>Camera / LiDAR / Base</dt>
            <dd>
              /api/camera/health={{ robotSummary?.readback_summary.camera.status ?? "not_loaded" }},
              /api/camera/devices={{ robotSummary?.readback_summary.camera.devices_status ?? "not_loaded" }},
              /api/radar/status={{ robotSummary?.readback_summary.lidar.status ?? "not_loaded" }},
              scan={{ robotSummary?.readback_summary.lidar.latest_scan_proof_status ?? "not_loaded" }},
              raw={{ robotSummary?.readback_summary.lidar.latest_raw_packet_proof_status ?? "not_loaded" }},
              continuous={{ robotSummary?.readback_summary.lidar.continuous_scan_status ?? "not_loaded" }},
              lifecycle={{ robotSummary?.readback_summary.lidar.lifecycle_running ?? "not_loaded" }}/{{ robotSummary?.readback_summary.lidar.lifecycle_state ?? "not_loaded" }},
              window={{ robotSummary?.readback_summary.lidar.continuous_window_observed ?? "not_loaded" }}/{{ robotSummary?.readback_summary.lidar.continuity_window_status ?? "not_loaded" }},
              /api/base/status={{ robotSummary?.readback_summary.base.status ?? "not_loaded" }},
              readback={{ robotSummary?.readback_summary.base.latest_feedback_status ?? "not_loaded" }}
            </dd>
            <dt>unsafe starts</dt>
            <dd>radar start=false; map start=false; base manual=false</dd>
            <dt>latest base proxy</dt>
            <dd>
              {{ manualCommandResult?.command_kind ?? "not_loaded" }} /
              {{ manualCommandResult?.proxy_status ?? "not_loaded" }} /
              {{ manualCommandResult?.failure_reason || "none" }}
            </dd>
            <dt>latest base clamp</dt>
            <dd>
              dir={{ manualCommandResult?.applied_direction ?? "not_loaded" }},
              speed={{ manualCommandResult?.clamped_speed_mps ?? "n/a" }},
              duration={{ manualCommandResult?.clamped_duration_ms ?? "n/a" }}
            </dd>
            <dt>evidence capture</dt>
            <dd>
              {{ manualCommandResult?.evidence_capture_status ?? "not_loaded" }} /
              {{ manualCommandResult?.motion_evidence_summary ?? "none" }}
            </dd>
            <dt>evidence endpoints</dt>
            <dd>{{ evidenceEndpointText(manualCommandResult?.evidence_capture_endpoints) }}</dd>
            <dt>evidence blocked reasons</dt>
            <dd>{{ listText(manualCommandResult?.evidence_capture_blocked_reasons, "none") }}</dd>
            <dt>before readback</dt>
            <dd>{{ evidenceReadbackText(manualCommandResult?.before_readback) }}</dd>
            <dt>after readback</dt>
            <dd>{{ evidenceReadbackText(manualCommandResult?.after_readback) }}</dd>
          </dl>
          <table class="preflight-table">
            <thead>
              <tr>
                <th>endpoint</th>
                <th>HTTP</th>
                <th>状态</th>
                <th>schema</th>
                <th>key readback</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="endpoint in robotSummary?.read_endpoints ?? []" :key="endpoint.id">
                <td>{{ endpoint.endpoint }}</td>
                <td>{{ endpoint.http_status ?? "n/a" }}</td>
                <td>{{ endpoint.request_status }} / {{ endpoint.status }}</td>
                <td>{{ endpoint.schema }}</td>
                <td>{{ JSON.stringify(endpoint.key_values).slice(0, 220) }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </details>
  </section>
</template>
