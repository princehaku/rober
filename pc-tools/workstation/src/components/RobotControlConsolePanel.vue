<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  getO7ConsumerTaskDetail,
  getRobotControlSummary,
  getRobotControlMapList,
  getRobotControlDeliveryLatest,
  postRobotControlBaseFeedbackSamples,
  postRobotControlBaseFirstJog,
  postRobotControlBaseManual,
  postRobotControlBaseStop,
  postRobotControlDeliveryComplete,
  postRobotControlDeliveryGapCheck,
  postRobotControlMapStart,
  postRobotControlMapSave,
  postRobotControlLocalizeReset,
  getRobotControlNav2GoalExecutionLatest,
  postRobotControlNav2GoalExecute,
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
  RobotControlBaseCommandRequest,
  RobotControlBaseCommandProxyResponse,
  RobotControlBaseFeedbackSamplesProxyResponse,
  RobotControlCameraFirstFrameProbeProxyResponse,
  RobotControlDeliveryCompleteResponse,
  RobotControlDeliveryLatestResponse,
  RobotControlDeliveryGapCheckResponse,
  RobotControlMapLifecycleResponse,
  RobotControlNavGoalExecutionLatestResponse,
  RobotControlNavGoalExecutionResponse,
  RobotControlNavGoalPreflightResponse,
  RobotControlOperatorReportProxyResponse,
  RobotControlOperatorReportRequest,
  RobotControlPreviewStatus,
  RobotControlProofRefreshProxyResponse,
  RobotControlRadarLifecycleResponse,
  RobotControlSummaryResponse,
} from "../shared/contracts";

// 本组件仍然是 fail-closed 控制台；默认地址固定到当前上位机，减少普通用户每次手输。
const DEFAULT_ROBOT_API_BASE_URL = "http://192.168.1.11:8787";
type ManualDirection = "forward" | "back" | "left" | "right";
const KEYBOARD_JOG_INTERVAL_MS = 260;
const KEYBOARD_JOG_DURATION_MS = 240;
const WHEEL_ZERO_NEXT_ACTION_SUMMARY = "下一步：检查电机使能、供电、模式和现场空间后重试读取轮速。";
const robotApiBaseUrl = ref(DEFAULT_ROBOT_API_BASE_URL);
const robotApiBaseUrlUsesDefault = computed(() => robotApiBaseUrl.value.trim() === DEFAULT_ROBOT_API_BASE_URL);
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
const navGoalExecutionResult = ref<RobotControlNavGoalExecutionResponse | null>(null);
const navGoalExecutionLatestResult = ref<RobotControlNavGoalExecutionLatestResponse | null>(null);
const deliveryLatestResult = ref<RobotControlDeliveryLatestResponse | null>(null);
const deliveryGapCheckResult = ref<RobotControlDeliveryGapCheckResponse | null>(null);
const deliveryCompletionResult = ref<RobotControlDeliveryCompleteResponse | null>(null);
const localizationResetResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const mapLifecycleResult = ref<RobotControlMapLifecycleResponse | null>(null);
const manualCommandResult = ref<RobotControlBaseCommandProxyResponse | null>(null);
const manualCommandPending = ref(false);
const mapLifecyclePending = ref(false);
const mapLifecycleMapName = ref("");
const mapLifecycleArtifactPath = ref("");
const operatorReportPending = ref(false);
const operatorReportResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainMotionPrecheckPending = ref(false);
const plainMotionPrecheckResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainVisualMaterialPending = ref(false);
const plainVisualMaterialResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainFirstJogMaterialRestorePending = ref(false);
const plainFirstJogMaterialRestoreResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainFirstJogResult = ref<RobotControlBaseCommandProxyResponse | null>(null);
const plainWheelEvidenceSavePending = ref(false);
const plainWheelEvidenceSaveResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainExternalVideoRef = ref("");
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
const confirmNavigationExecution = ref(false);
const plainTripSafetyConfirmed = ref(false);
const confirmDeliveryCompletion = ref(false);
const deliveryEvidenceRef = ref("");
const deliveryOperatorEvidenceRef = ref("");
const deliveryOperatorVideoRef = ref("");
const deliveryOperatorRouteMapRef = ref("");
const deliveryOperatorConfirmations = ref({
  operator_present: false,
  physical_clearance_confirmed: false,
  emergency_stop_ready: false,
  observed_motion: false,
  observed_stop: false,
  route_video_refs_verified: false,
  delivery_success: false,
});
const navGoalExecutionTimeoutS = ref(8);
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
const navGoalExecutionPending = ref(false);
const navGoalExecutionLatestPending = ref(false);
const deliveryLatestPending = ref(false);
const deliveryGapCheckPending = ref(false);
const deliveryCompletionPending = ref(false);
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
const baseFeedbackSamplesPending = ref(false);
const baseFeedbackSamplesResult = ref<RobotControlBaseFeedbackSamplesProxyResponse | null>(null);
const evidenceSweepPending = ref(false);
const evidenceSweepStartedAt = ref("");
const evidenceSweepCompletedAt = ref("");
const evidenceSweepLines = ref<string[]>([]);
const keyboardControlPanel = ref<HTMLElement | null>(null);
const plainTripRunPanel = ref<HTMLElement | null>(null);
const plainWheelRecordPanel = ref<HTMLElement | null>(null);
const plainDeliveryStatusPanel = ref<HTMLElement | null>(null);
const plainDeliveryFinalPanel = ref<HTMLElement | null>(null);
const keyboardControlArmed = ref(false);
const keyboardHeldDirection = ref<ManualDirection | null>(null);
const keyboardControlStatus = ref("idle_not_started");
const keyboardLastDirection = ref("not_loaded");
const keyboardLastStopReason = ref("not_loaded");
let previewFrameSampleTimers: number[] = [];
let keyboardJogTimer: number | null = null;
let keyboardJogInFlight = false;

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

function resetRobotApiBaseUrlToDefault(): void {
  // 恢复地址只改本地输入值；真正读取或控制仍必须由用户再显式点击。
  if (robotApiBaseUrlUsesDefault.value) {
    return;
  }
  robotApiBaseUrl.value = DEFAULT_ROBOT_API_BASE_URL;
}

function robotConnectionBlockedReasonText(): string {
  // 普通首屏只用 blocked reason 判断“没回应/失败”大类，完整 endpoint 留在高级诊断。
  const connection = robotSummary.value?.robot_api_connection;
  return connection?.blocked_reasons.join(" ") ?? "";
}

function summarizeRobotConnection(): { state: "未连接" | "已连接" | "有异常"; hint: string } {
  // 连接状态只给普通用户看三档，细节放在折叠区。
  if (!robotApiBaseUrl.value.trim()) {
    return { state: "未连接", hint: "先输入地址，再点连接/刷新。" };
  }
  const connection = robotSummary.value?.robot_api_connection;
  if (!connection) {
    return { state: "未连接", hint: "先输入地址，再点连接/刷新。" };
  }
  if (connection.dangerous_true_fields.length > 0) {
    return { state: "有异常", hint: "读到危险字段，控制保持锁定。" };
  }
  if (connection.loaded_count > 0) {
    if (connection.failed_count > 0 || connection.blocked_count > 0 || connection.status === "degraded" || connection.status === "blocked") {
      return { state: "已连接", hint: "已读到小车状态；部分项目未通过，可展开高级诊断。" };
    }
    return { state: "已连接", hint: "已读到小车状态摘要。" };
  }
  if (connection.status === "blocked" || connection.failed_count > 0 || connection.blocked_count > 0) {
    const reasonText = robotConnectionBlockedReasonText();
    if (reasonText.includes("fetch_timeout")) {
      return { state: "有异常", hint: "上位机没回应；检查小车电源、网络和上位机服务后再点连接/刷新。" };
    }
    return { state: "有异常", hint: "连接失败；检查小车地址、网络和上位机服务后再试。" };
  }
  return { state: "未连接", hint: "还没有连上可读状态。" };
}

function cameraSourcePlainFailureHint(): string {
  // summary 已经完成工程归因；普通首屏只翻译成可处理的现场动作。
  const camera = robotSummary.value?.readback_summary.camera;
  if (!camera) {
    return "";
  }
  const sourceFailed =
    camera.status === "source_first_frame_failed"
    || camera.source_readiness === "first_frame_failed"
    || camera.source_failure_reason === "first_frame_timeout"
    || camera.last_offer_failure_reason === "first_frame_timeout";
  return sourceFailed ? "相机没有出画面，检查摄像头/视频线。" : "";
}

function summarizeCameraState(): { state: "未打开" | "连接中" | "已打开" | "画面可见" | "画面偏暗" | "失败"; hint: string } {
  // 摄像头首屏只暴露普通用户能理解的结论，不泄露 peer / ICE / SDP / canvas 细节。
  const sourceFailureHint = cameraSourcePlainFailureHint();
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
      if (sourceFailureHint) {
        return { state: "失败", hint: sourceFailureHint };
      }
      return { state: "失败", hint: failureReason.value || "打开画面失败。" };
    default:
      if (sourceFailureHint) {
        return { state: "失败", hint: sourceFailureHint };
      }
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
  // lifecycle 摘要只说普通建图动作结果，不把 endpoint、proof 或命令细节放回首页。
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
    if (result.map_usable_for_navigation) {
      return { state: "已读取", hint: `已有可用地图，${result.map_count ?? 0} 个候选。` };
    }
    if (result.map_needs_rebuild) {
      return { state: "失败", hint: "当前地图不可导航，需要重新建图。" };
    }
    return { state: "已读取", hint: `地图列表 ${result.map_count ?? 0} 个候选。` };
  }
  if (result.action === "start") {
    return { state: "已读取", hint: "重新建图已返回；再查看地图质量。" };
  }
  return { state: "已读取", hint: "保存地图已返回；再查看地图质量。" };
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
  return `${result.proxy_status}; status=${result.status}; open=${values.open_ok}; read=${values.read_ok}; backend=${values.backend_smoke_status}; reason=${result.failure_reason || values.failure_reason}`;
});
const baseFeedbackSamplesSummary = computed(() => {
  // 底盘反馈样本只说明 T=130/T=1001 只读链路，不能解释成手动运动已经可用。
  if (baseFeedbackSamplesPending.value) {
    return "feedback samples pending";
  }
  const result = baseFeedbackSamplesResult.value;
  if (!result) {
    return "feedback samples not requested";
  }
  const values = result.sample_key_values;
  return `${result.proxy_status}; status=${result.status}; t1001=${values.t1001_observed_count}/${values.completed_sample_count}; L/R=${values.wheel_feedback_latest_left_speed}/${values.wheel_feedback_latest_right_speed}; nonzero=${values.wheel_feedback_lr_nonzero_proven}; motion=${values.sends_motion_commands}; reason=${result.failure_reason || "none"}`;
});
const wheelRawLrProgressSummary = computed(() => {
  // 轮速非零只能由运动窗口 during-motion T1001 证明；静态采样和草稿材料只能给下一步提示。
  if (manualCommandPending.value) {
    return "motion window capture pending";
  }
  const motionValues = manualCommandResult.value?.remote_motion_key_values;
  if (motionValues) {
    if (motionValues.wheel_feedback_lr_nonzero_proven === "true") {
      return `motion window nonzero proven; frames=${motionValues.feedback_during_motion_t1001_frame_count ?? "not_loaded"}; L/R=${motionValues.wheel_feedback_latest_raw_left ?? "not_loaded"}/${motionValues.wheel_feedback_latest_raw_right ?? "not_loaded"}`;
    }
    if (manualCommandResult.value?.operator_report_preflight.status === "blocked") {
      const missing = manualCommandResult.value.operator_report_preflight.missing_fields.join(",");
      return `motion gate blocked by operator report; missing=${missing || "unknown"}; report=${manualCommandResult.value.operator_report_preflight.report_status}`;
    }
    return `motion attempted but nonzero not proven; frames=${motionValues.feedback_during_motion_t1001_frame_count ?? "0"}; L/R=${motionValues.wheel_feedback_latest_raw_left ?? "not_loaded"}/${motionValues.wheel_feedback_latest_raw_right ?? "not_loaded"}; next=check motor enable, power, mode, floor clearance`;
  }
  const sampleValues = baseFeedbackSamplesResult.value?.sample_key_values;
  if (sampleValues) {
    if (sampleValues.wheel_feedback_lr_nonzero_proven === "true") {
      return `feedback sample reported nonzero; L/R=${sampleValues.wheel_feedback_latest_left_speed}/${sampleValues.wheel_feedback_latest_right_speed}; still prefer motion window proof`;
    }
    if (sampleValues.sends_motion_commands === "false") {
      return `static T1001 feedback only; L/R=${sampleValues.wheel_feedback_latest_left_speed}/${sampleValues.wheel_feedback_latest_right_speed}; t1001=${sampleValues.t1001_observed_count}; next=restore first-jog materials then run wheel nonzero trial`;
    }
  }
  const firstJog = robotSummary.value?.first_jog_readiness_summary;
  if (firstJog && firstJog.status !== "ready_for_first_jog") {
    return `first-jog not ready; status=${firstJog.status}; missing=${firstJog.missing_fields.join(",") || "none"}; next=${firstJog.next_action}`;
  }
  if (firstJog?.status === "ready_for_first_jog") {
    return "first-jog ready; next=run wheel nonzero trial while operator watches stop";
  }
  return "not checked; run base feedback sample or first-jog readiness first";
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
const keyboardJogIntervalMs = computed(() => manualBoundary.value?.keyboard_jog_interval_ms ?? KEYBOARD_JOG_INTERVAL_MS);
const keyboardJogDurationMs = computed(() => manualBoundary.value?.keyboard_jog_duration_ms ?? KEYBOARD_JOG_DURATION_MS);
const checklistMissing = computed(() => hilChecklist.value.filter((item) => !item.checked).map((item) => item.label));
const hilChecklistConfirmed = computed(() => checklistMissing.value.length === 0);
const canSendStop = computed(() => !manualCommandPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0);
const canRunEvidenceSweep = computed(() => !evidenceSweepPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0);
const keyboardContractReady = computed(() => {
  // 键盘手控必须由后端 summary 明确声明 bounded pulse 合同，不能只靠前端默认值放开。
  return robotSummary.value?.safe_command_boundary.keyboard_control_mode === "bounded_repeating_manual_pulse"
    && robotSummary.value.safe_command_boundary.keyboard_reuses_manual_gate === true;
});
const canUseKeyboardControl = computed(() => keyboardContractReady.value && canSendManualMotion.value);
const canArmKeyboardControl = computed(() => canUseKeyboardControl.value);

const keyboardDirectionPlainLabel = computed(() => {
  // 普通首屏只显示方向中文，避免把底层 direction enum 暴露给现场用户。
  switch (keyboardHeldDirection.value) {
    case "forward":
      return "前进";
    case "back":
      return "后退";
    case "left":
      return "左转";
    case "right":
      return "右转";
    default:
      return "未按键";
  }
});
function claimWithRefReady(value: string | undefined): boolean {
  // 现场材料的四类引用型 claim 必须同时满足 true 且带 ref，缺任一条件都按未满足处理。
  return typeof value === "string" && value.startsWith("true; ref=") && !value.endsWith("not_loaded");
}

function isZeroWheelPair(left: string | undefined, right: string | undefined): boolean {
  // 上位机可能返回 "0"、"0.0" 或数值转字符串；这里只判断有限零值，不把缺失值当成零。
  if (!left || !right || left === "not_loaded" || right === "not_loaded") {
    return false;
  }
  const leftNumber = Number(left);
  const rightNumber = Number(right);
  return Number.isFinite(leftNumber) && Number.isFinite(rightNumber) && leftNumber === 0 && rightNumber === 0;
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

const deliveryOperatorConfirmationReady = computed(() => {
  // 送达成功必须由现场逐项确认；预填 ref 或草稿 report 不能替代 observed motion/stop。
  const confirmations = deliveryOperatorConfirmations.value;
  return confirmations.operator_present
    && confirmations.physical_clearance_confirmed
    && confirmations.emergency_stop_ready
    && confirmations.observed_motion
    && confirmations.observed_stop
    && confirmations.route_video_refs_verified
    && confirmations.delivery_success;
});

const plainDeliveryConfirmMissingLabels = computed(() => {
  // 最终确认区要先提示材料缺口，再提示现场勾选项，避免现场在按钮之间来回猜。
  const confirmations = deliveryOperatorConfirmations.value;
  const materialReady = Boolean(deliveryOperatorVideoRef.value.trim() && deliveryOperatorRouteMapRef.value.trim());
  return [
    { label: "送达材料", ready: materialReady },
    { label: "人在旁边可接管", ready: confirmations.operator_present },
    { label: "周围安全", ready: confirmations.physical_clearance_confirmed },
    { label: "停止手段就绪", ready: confirmations.emergency_stop_ready },
    { label: "已观察到到达/移动", ready: confirmations.observed_motion },
    { label: "已观察到停止", ready: confirmations.observed_stop },
    { label: "视频和行程材料已核对", ready: confirmations.route_video_refs_verified },
    { label: "确认已投放/送达", ready: confirmations.delivery_success },
  ].filter((item) => !item.ready).map((item) => item.label);
});

const plainDeliveryConfirmMissingSummary = computed(() => {
  const missingLabels = plainDeliveryConfirmMissingLabels.value;
  if (missingLabels.length === 0) {
    return "全部确认项已勾选，可以提交。";
  }
  return `还差 ${missingLabels.length} 项：${missingLabels.join("、")}。`;
});

function deliveryDraftMaterialPresent(): boolean {
  // 草稿可能来自本页刚保存，也可能来自上位机 latest；两者都只代表材料草稿，不代表送达成功。
  return operatorReportResult.value?.structured_hil_claims?.site_state === "delivery_material_draft_not_operator_confirmed"
    || deliveryLatestResult.value?.delivery_material_refs?.site_state === "delivery_material_draft_not_operator_confirmed";
}

function plainDeliveryConfirmBlockedLabel(missingLabels: string[]): string {
  // 已有草稿后，按钮直接指向下一组人工确认，避免现场只看到抽象数量。
  if (missingLabels.includes("送达材料")) {
    return "确认送达（先准备材料）";
  }
  if (missingLabels.some((label) => ["人在旁边可接管", "周围安全", "停止手段就绪"].includes(label))) {
    return "确认送达（先勾选安全）";
  }
  if (missingLabels.some((label) => ["已观察到到达/移动", "已观察到停止"].includes(label))) {
    return "确认送达（先确认到达）";
  }
  if (missingLabels.includes("视频和行程材料已核对")) {
    return "确认送达（先核对材料）";
  }
  if (missingLabels.includes("确认已投放/送达")) {
    return "确认送达（先确认投放）";
  }
  return `确认送达（先确认 ${missingLabels.length} 项）`;
}

const plainDeliveryConfirmButtonLabel = computed(() => {
  // 按钮禁用时显示缺项数量；可提交时明确“不发车”，避免送达收口被误解成运动命令。
  const missingLabels = plainDeliveryConfirmMissingLabels.value;
  const missingCount = missingLabels.length;
  if (missingCount > 0 && deliveryDraftMaterialPresent()) {
    return plainDeliveryConfirmBlockedLabel(missingLabels);
  }
  return missingCount > 0 ? `确认送达（还差 ${missingCount} 项）` : "确认送达（不发车）";
});

const plainDeliverySafetyButtonLabel = computed(() => {
  // 下一步直接写在对应按钮上；点击仍只勾选本地确认项，不提交送达。
  const confirmations = deliveryOperatorConfirmations.value;
  return confirmations.operator_present && confirmations.physical_clearance_confirmed && confirmations.emergency_stop_ready
    ? "安全三项已勾选"
    : "下一步：勾选安全三项";
});

const plainDeliveryArrivedStoppedButtonLabel = computed(() => {
  const confirmations = deliveryOperatorConfirmations.value;
  return confirmations.observed_motion && confirmations.observed_stop ? "已确认到达停稳" : "下一步：确认到达停稳";
});

const plainDeliveryRefsVerifiedButtonLabel = computed(() => (
  deliveryOperatorConfirmations.value.route_video_refs_verified ? "材料已核对" : "下一步：核对材料"
));

const plainDeliverySuccessButtonLabel = computed(() => (
  deliveryOperatorConfirmations.value.delivery_success ? "已确认投放/送达" : "下一步：确认投放/送达"
));

const deliveryGateBlockedReasons = computed(() => {
  // 送达缺口可能来自 latest、check 或 complete；合并后给现场人员一个稳定清单。
  return Array.from(new Set([
    ...(deliveryCompletionResult.value?.blocked_reasons ?? []),
    ...(deliveryGapCheckResult.value?.blocked_reasons ?? []),
    ...(deliveryLatestResult.value?.blocked_reasons ?? []),
  ]));
});

function deliveryGateMissing(token: string): boolean {
  // 后端缺口字段有时是精确字段，有时是 required material 名称；这里仅做保守包含判断。
  return deliveryGateBlockedReasons.value.some((reason) => reason.includes(token));
}

const plainDeliveryGateMissingSummary = computed(() => {
  // 把上位机 delivery gate 缺口翻成普通话；字段名留在高级诊断，避免普通首屏变成接口面板。
  if (deliveryCompletionResult.value?.delivery_success === true || deliveryLatestResult.value?.delivery_success === true) {
    return "";
  }
  const reasonText = deliveryGateBlockedReasons.value.join(" ");
  const labels = [
    { label: "完成行程", ready: !reasonText.includes("nav2_goal_succeeded") },
    { label: "现场确认报告", ready: !reasonText.includes("operator_report_ready_for_review") },
    { label: "已观察到到达/移动", ready: !reasonText.includes("operator_observed_motion") },
    { label: "已观察到停止", ready: !reasonText.includes("operator_observed_stop") },
    { label: "确认已投放/送达", ready: !reasonText.includes("structured_hil_claims.delivery_success") },
    { label: "视频和行程材料", ready: !reasonText.includes("external_video_or_visible_camera_ref") && !reasonText.includes("route_map") },
    { label: "最后点击确认送达", ready: !reasonText.includes("confirm_delivery_completion") },
  ].filter((item) => !item.ready).map((item) => item.label);
  if (labels.length === 0) {
    return "";
  }
  return `上位机还差：${labels.join("、")}。`;
});

const plainDeliveryGapCheckButtonLabel = computed(() => {
  // 复查固定 confirm=false，只重新算缺口；按钮文案直接说明不会确认送达。
  if (deliveryGapCheckPending.value) {
    return "复查中";
  }
  const missingCount = deliveryGateBlockedReasons.value.length;
  return missingCount > 0 ? `复查送达条件（还差 ${missingCount} 项，不确认）` : "复查送达条件（不确认）";
});

const plainDeliveryNextActionSummary = computed(() => {
  // 送达 gate 缺项很多时，普通首屏只给一个下一步，避免现场人员在多按钮之间来回猜。
  if (deliveryCompletionResult.value?.delivery_success === true || deliveryLatestResult.value?.delivery_success === true) {
    return "";
  }
  if (!deliveryOperatorVideoRef.value.trim() || !deliveryOperatorRouteMapRef.value.trim()) {
    return "下一步：准备送达材料。";
  }
  const confirmations = deliveryOperatorConfirmations.value;
  if (!confirmations.operator_present || !confirmations.physical_clearance_confirmed || !confirmations.emergency_stop_ready) {
    return "下一步：勾选安全三项。";
  }
  if (!confirmations.observed_motion || !confirmations.observed_stop) {
    return "下一步：确认已到达并停稳。";
  }
  if (!confirmations.route_video_refs_verified) {
    return "下一步：核对视频和行程材料。";
  }
  if (!confirmations.delivery_success) {
    return "下一步：确认已投放/送达。";
  }
  return "下一步：点击确认送达。";
});

const deliveryNav2GoalReady = computed(() => {
  // Nav2 success 可来自刚执行结果、latest 读回或 delivery gate 的压缩 key values。
  const latestStatus = deliveryLatestResult.value?.delivery_key_values.nav2_status
    ?? deliveryGapCheckResult.value?.delivery_key_values.nav2_status
    ?? deliveryCompletionResult.value?.delivery_key_values.nav2_status;
  return latestStatus === "goal_succeeded"
    || navGoalExecutionResult.value?.goal_execution_key_values.status === "goal_succeeded"
    || navGoalExecutionLatestResult.value?.goal_execution_key_values.status === "goal_succeeded";
});

const plainDeliverySummary = computed(() => {
  // 普通首屏只做收口状态提示；按钮只读 latest 或复算缺口，不提交送达确认。
  const deliveryConfirmed = deliveryCompletionResult.value?.delivery_success === true || deliveryLatestResult.value?.delivery_success === true;
  if (deliveryCompletionPending.value || deliveryLatestPending.value || deliveryGapCheckPending.value) {
    return { state: "检查中", hint: "正在读取最近行程和送达状态；不会发车。" };
  }
  if (deliveryConfirmed) {
    return { state: "已送达", hint: "送达 gate 已确认成功。" };
  }
  if (deliveryNav2GoalReady.value) {
    const gapCount = deliveryGateBlockedReasons.value.length;
    return {
      state: "待确认",
      hint: gapCount > 0 ? `行程已完成，还需补齐 ${gapCount} 项送达确认。` : "行程已完成，还需要现场确认送达。",
    };
  }
  if (deliveryLatestResult.value || deliveryGapCheckResult.value || deliveryCompletionResult.value || navGoalExecutionLatestResult.value) {
    return { state: "待行程结果", hint: "还没读到最近一次完整行程结果。" };
  }
  return { state: "未读取", hint: "点击刷新送达状态，只读取结果，不执行行程或确认送达。" };
});

const plainDeliveryLatestButtonLabel = computed(() => {
  // latest 只读最近送达 gate 结果；按钮文案直接说明不会提交确认。
  return deliveryLatestPending.value ? "刷新中" : "刷新送达状态（只读）";
});

const plainDeliveryMaterialSummary = computed(() => {
  // 送达材料草稿只说明“有没有准备好”；不显示 ref、字段名或 delivery claim。
  if (operatorReportPending.value) {
    return { state: "保存中", hint: "正在保存送达材料草稿；不会确认送达。" };
  }
  if (navGoalExecutionLatestPending.value || cameraFirstFrameProbePending.value || deliveryLatestPending.value) {
    return { state: "准备中", hint: "正在读取最近行程和画面材料。" };
  }
  if (deliveryDraftMaterialPresent()) {
    return { state: "已保存", hint: "送达材料草稿已保存；请完成下方最终确认。" };
  }
  if (deliveryOperatorVideoRef.value.trim() && deliveryOperatorRouteMapRef.value.trim()) {
    return { state: "已预填", hint: "视频和行程材料已预填，可先保存草稿。" };
  }
  if (deliveryOperatorRouteMapRef.value.trim()) {
    return { state: "待画面", hint: "行程材料已在，点准备送达材料补画面。" };
  }
  if (deliveryNav2GoalReady.value) {
    return { state: "可准备", hint: "已读到最近行程结果，可以准备送达材料。" };
  }
  return { state: "待行程", hint: "需要先读到最近行程结果，再准备送达材料。" };
});

const plainDeliveryDraftSaveButtonLabel = computed(() => (
  operatorReportPending.value ? "保存中" : "保存送达草稿（不确认）"
));

const plainDeliveryConfirmReady = computed(() => {
  // 普通确认入口复用高级 gate：材料和逐项勾选都满足后才允许提交。
  return !loading.value
    && !operatorReportPending.value
    && !deliveryCompletionPending.value
    && robotApiBaseUrl.value.trim().length > 0
    && deliveryOperatorConfirmationReady.value
    && deliveryOperatorVideoRef.value.trim().length > 0
    && deliveryOperatorRouteMapRef.value.trim().length > 0;
});

const plainDeliveryConfirmSummary = computed(() => {
  // 首屏只解释下一步，不把 operator report、route_map_ref 或 delivery gate 术语暴露给普通用户。
  if (operatorReportPending.value || deliveryCompletionPending.value) {
    return { state: "确认中", hint: "正在提交最终确认。" };
  }
  if (deliveryCompletionResult.value?.delivery_success === true || deliveryLatestResult.value?.delivery_success === true) {
    return { state: "已完成", hint: "送达已确认完成。" };
  }
  if (!deliveryOperatorVideoRef.value.trim() || !deliveryOperatorRouteMapRef.value.trim()) {
    return { state: "待材料", hint: "先准备送达材料，再做最终确认。" };
  }
  if (deliveryDraftMaterialPresent()) {
    return { state: "待确认", hint: "送达材料已保存；现场逐项确认后再提交。" };
  }
  if (!deliveryOperatorConfirmationReady.value) {
    return { state: "待勾选", hint: "逐项确认后才能提交送达结果。" };
  }
  return { state: "可提交", hint: "已满足最终确认条件；提交后只做送达收口，不发车。" };
});

const deliveryClosureChecklist = computed(() => {
  // 这个摘要只是 UI 收口提示，不自动勾选、不提交、不把 delivery_success 提升为 true。
  const confirmations = deliveryOperatorConfirmations.value;
  return [
    {
      id: "nav2_goal_succeeded",
      label: "Nav2 路线执行成功",
      ready: deliveryNav2GoalReady.value && !deliveryGateMissing("nav2_goal_succeeded"),
      hint: deliveryNav2GoalReady.value ? "已有 goal_succeeded 读回" : "先读取或执行最近 Nav2 目标",
    },
    {
      id: "operator_report_ready",
      label: "现场报告 ready_for_review",
      ready: !deliveryGateMissing("operator_report_ready_for_review") && deliveryOperatorConfirmationReady.value,
      hint: deliveryOperatorConfirmationReady.value ? "最终 checklist 已勾全，提交后由上位机确认" : "需要完成下方送达最终确认",
    },
    {
      id: "observed_motion",
      label: "现场观察到运动/到达",
      ready: confirmations.observed_motion && !deliveryGateMissing("operator_observed_motion"),
      hint: confirmations.observed_motion ? "已勾选" : "需要现场勾选",
    },
    {
      id: "observed_stop",
      label: "现场观察到停止",
      ready: confirmations.observed_stop && !deliveryGateMissing("operator_observed_stop"),
      hint: confirmations.observed_stop ? "已勾选" : "需要现场勾选",
    },
    {
      id: "delivery_claim",
      label: "确认已投放/送达",
      ready: confirmations.delivery_success && !deliveryGateMissing("structured_hil_claims.delivery_success"),
      hint: confirmations.delivery_success ? "已勾选" : "需要现场勾选",
    },
    {
      id: "refs_ready",
      label: "视频与 route/map ref",
      ready: Boolean(deliveryOperatorVideoRef.value.trim() && deliveryOperatorRouteMapRef.value.trim() && confirmations.route_video_refs_verified),
      hint: deliveryOperatorVideoRef.value.trim() && deliveryOperatorRouteMapRef.value.trim() ? "ref 已填写，仍需勾选可复核" : "先预填或手动填写 ref",
    },
  ];
});

const goalClosureChecklist = computed(() => {
  // 总目标进度只聚合已读证据，不触发任何控制动作或成功外推。
  const summary = robotSummary.value?.operator_hil_material_summary;
  const wheelReady = claimWithRefReady(summary?.wheel_feedback)
    || plainFirstJogResult.value?.remote_motion_key_values?.wheel_feedback_lr_nonzero_proven === "true"
    || baseFeedbackSamplesResult.value?.sample_key_values.wheel_feedback_lr_nonzero_proven === "true";
  const nav2Ready = deliveryNav2GoalReady.value;
  const deliveryReady = deliveryCompletionResult.value?.delivery_success === true || deliveryLatestResult.value?.delivery_success === true;
  const keyboardReady = canUseKeyboardControl.value;
  return [
    {
      id: "wheel_raw_lr",
      label: "wheel raw L/R 非零",
      ready: wheelReady,
      hint: wheelReady ? "已有非零 L/R 材料" : "仍需 first-jog/manual 期间同帧 T1001 L/R 非零",
    },
    {
      id: "nav2_goal_execution",
      label: "完整 Nav2 路线执行",
      ready: nav2Ready,
      hint: nav2Ready ? "已有 goal_succeeded 读回" : "读取最近 Nav2 结果或执行受限目标后确认",
    },
    {
      id: "delivery_success",
      label: "delivery success",
      ready: deliveryReady,
      hint: deliveryReady ? "delivery gate 已确认成功" : "仍需现场最终确认并通过 delivery gate",
    },
    {
      id: "keyboard_manual",
      label: "PC 键盘连续手控",
      ready: keyboardReady,
      hint: keyboardReady
        ? "键盘入口已就绪，材料 gate 已满足"
        : keyboardContractReady.value ? `键盘入口已在，仍需补齐：${plainKeyboardMissingSummary.value.replace(/^还差：/, "").replace(/。$/, "")}` : "键盘合同未从 summary 读到",
    },
  ];
});

const plainWheelGoalProgressHint = computed(() => {
  // 轮速进度要显示当前 L/R 和帧数，帮助现场判断是“没读到”还是“读到了但仍为 0/0”。
  const sample = baseFeedbackSamplesResult.value?.sample_key_values;
  const base = robotSummary.value?.readback_summary.base;
  const left = sample?.wheel_feedback_latest_left_speed ?? base?.wheel_feedback_latest_left_speed ?? "not_loaded";
  const right = sample?.wheel_feedback_latest_right_speed ?? base?.wheel_feedback_latest_right_speed ?? "not_loaded";
  const frameCount = sample?.t1001_observed_count ?? base?.latest_t1001_observed_count ?? "not_loaded";
  const voltageText = base?.feedback_voltage_v && base.feedback_voltage_v !== "not_loaded" ? `，反馈电压约 ${base.feedback_voltage_v}V` : "";
  if (left !== "not_loaded" && right !== "not_loaded") {
    const frameText = frameCount !== "not_loaded" ? `，已读到 ${frameCount} 帧` : "";
    const nextStep = firstJogMaterialRestoreReady.value
      ? "先点恢复试动确认，再试动读非零。"
      : isZeroWheelPair(left, right) && voltageText ? WHEEL_ZERO_NEXT_ACTION_SUMMARY : "仍需试动读到非零。";
    return `当前轮速 L/R=${left}/${right}${frameText}${voltageText}，${nextStep}`;
  }
  if (firstJogMaterialRestoreReady.value) {
    return "先点恢复试动确认，再试动读取轮速。";
  }
  return "等待运动窗口读到非零 L/R。";
});

const plainDeliveryGoalProgressHint = computed(() => {
  // 送达进度优先显示上位机 gate 缺项；它只是提示，不自动勾选或提交最终确认。
  const missingSummary = plainDeliveryGateMissingSummary.value;
  if (missingSummary) {
    const nextAction = plainDeliveryNextActionSummary.value;
    return `${missingSummary.replace(/^上位机还差：/, "还差：")}${nextAction ? ` ${nextAction}` : ""}`;
  }
  return plainDeliveryNextActionSummary.value || "还缺最终送达确认。";
});

const plainTripEvidenceSummary = computed(() => {
  // 行程成功只展示普通证据摘要；完整 evidence_ref 和 action 细节留在高级诊断。
  const values = navGoalExecutionResult.value?.goal_execution_key_values
    ?? navGoalExecutionLatestResult.value?.goal_execution_key_values
    ?? deliveryLatestResult.value?.delivery_key_values
    ?? deliveryGapCheckResult.value?.delivery_key_values
    ?? deliveryCompletionResult.value?.delivery_key_values;
  const status = values?.nav2_status ?? values?.status;
  if (status !== "goal_succeeded") {
    return "";
  }
  const feedbackCount = values?.feedback_sample_count ?? values?.nav2_feedback_sample_count;
  const feedbackText = feedbackCount && feedbackCount !== "0" && feedbackCount !== "not_loaded" ? `，反馈 ${feedbackCount} 次` : "";
  return `最近行程成功${feedbackText}；送达仍需现场确认。`;
});

const plainGoalProgressItems = computed(() => {
  // 普通首屏只展示用户能决策的四件事；工程字段继续留在高级诊断。
  const wheelReady = goalClosureChecklist.value.find((item) => item.id === "wheel_raw_lr")?.ready === true;
  const navReady = goalClosureChecklist.value.find((item) => item.id === "nav2_goal_execution")?.ready === true;
  const deliveryReady = goalClosureChecklist.value.find((item) => item.id === "delivery_success")?.ready === true;
  return [
    {
      id: "wheel",
      label: "轮速记录",
      actionLabel: "去轮速",
      state: wheelReady ? "已完成" : "待完成",
      hint: wheelReady ? "已读到非零 L/R。" : plainWheelGoalProgressHint.value,
    },
    {
      id: "trip",
      label: "行程执行",
      actionLabel: "去行程",
      state: navReady ? "已完成" : "待完成",
      hint: navReady ? plainTripEvidenceSummary.value || "最近行程已读到成功结果。" : "还没读到最近行程成功结果。",
    },
    {
      id: "delivery",
      label: "送达确认",
      actionLabel: "去送达",
      state: deliveryReady ? "已完成" : "待完成",
      hint: deliveryReady ? "送达已确认。" : plainDeliveryGoalProgressHint.value,
    },
    {
      id: "keyboard",
      label: "键盘手控",
      actionLabel: "去键盘",
      state: canUseKeyboardControl.value ? "可使用" : "未满足",
      hint: canUseKeyboardControl.value ? "可启用键盘面板。" : `先补齐键盘手控条件。${plainKeyboardMissingSummary.value} ${plainKeyboardNextActionSummary.value}`,
    },
  ];
});

const plainGoalProgressNextAction = computed(() => {
  // 现场不应该在四个目标之间猜顺序；总提示只指向第一项未完成的普通任务。
  const nextItem = plainGoalProgressItems.value.find((item) => item.state !== "已完成" && item.state !== "可使用");
  return nextItem ? `下一步：先处理${nextItem.label}。${nextItem.hint}` : "下一步：四项都已完成，保持待命。";
});

const plainTripActionPending = computed(() => navGoalPreflightPending.value || navGoalExecutionPending.value || navGoalExecutionLatestPending.value);

const plainTripSummary = computed(() => {
  // 普通首屏只说“行程”，不把 Nav2、goal 或 proof 术语放到默认界面。
  if (navGoalExecutionPending.value) {
    return { state: "执行中", hint: "正在执行行程；人在旁边准备停止。" };
  }
  if (navGoalPreflightPending.value) {
    return { state: "检查中", hint: "正在检查行程条件；不会发车。" };
  }
  if (navGoalExecutionLatestPending.value) {
    return { state: "读取中", hint: "正在读取最近行程结果。" };
  }
  if (deliveryNav2GoalReady.value) {
    return { state: "已完成", hint: plainTripEvidenceSummary.value || "已读到最近行程完成，可以准备送达材料。" };
  }
  if (navGoalExecutionResult.value?.proxy_status === "execution_failed" || navGoalExecutionResult.value?.proxy_status === "execution_rejected") {
    return { state: "执行失败", hint: navGoalExecutionResult.value.failure_reason || "行程执行未通过。" };
  }
  if (navGoalPreflightResult.value?.proxy_status === "preflight_passed") {
    return { state: "可执行", hint: "检查通过，确认人在旁边后可执行一次行程。" };
  }
  if (navGoalPreflightResult.value && navGoalPreflightResult.value.proxy_status !== "preflight_passed") {
    return { state: "检查失败", hint: "行程条件还没满足，请看高级诊断。" };
  }
  if (!plainTripSafetyConfirmed.value) {
    return { state: "待确认", hint: "先勾选行程前确认，再检查或执行。" };
  }
  return { state: "可检查", hint: "可先检查行程条件，也可执行一次默认行程。" };
});

const canRunPlainTripPreflight = computed(() => {
  // 预检不发车，但也要求现场先确认，避免普通入口被误当成随手按钮。
  return !deliveryNav2GoalReady.value && !loading.value && !plainTripActionPending.value && robotApiBaseUrl.value.trim().length > 0 && plainTripSafetyConfirmed.value;
});

const canRunPlainTripExecution = computed(() => {
  // 真正执行仍由后端 confirm_navigation_execution gate 再次校验。
  return !deliveryNav2GoalReady.value && !loading.value && !plainTripActionPending.value && robotApiBaseUrl.value.trim().length > 0 && plainTripSafetyConfirmed.value;
});

const plainTripPreflightButtonLabel = computed(() => (deliveryNav2GoalReady.value ? "行程已完成" : "检查行程"));
const plainTripExecutionButtonLabel = computed(() => (deliveryNav2GoalReady.value ? "行程已完成" : "执行行程"));
const plainTripLatestButtonLabel = computed(() => (deliveryNav2GoalReady.value ? "重新读取行程" : "读取行程结果"));

const plainGoalProgressPending = computed(() => (
  loading.value
  || navGoalExecutionLatestPending.value
  || deliveryLatestPending.value
  || baseFeedbackSamplesPending.value
));
const plainGoalProgressRefreshButtonLabel = computed(() => (
  plainGoalProgressPending.value ? "刷新中" : "刷新进度（只读）"
));

const firstJogVisualMaterialReady = computed(() => {
  // first-jog readiness 由 PC summary 后端统一判定，避免普通首屏和 API 合同漂移。
  return robotSummary.value?.first_jog_readiness_summary?.visual_material_ready === true;
});

const firstJogMaterialRestoreReady = computed(() => {
  // delivery draft 会覆盖 latest operator report；已有视觉材料时允许 operator 重新确认基础安全三项。
  const firstJog = robotSummary.value?.first_jog_readiness_summary;
  return firstJog?.status === "blocked_missing_basic_safety" && firstJog.visual_material_ready === true;
});

const firstJogMaterialRestoreSummary = computed(() => {
  // 上位机当前只有 latest operator report；送达草稿覆盖后，要把可恢复原因说清楚。
  const summary = robotSummary.value?.operator_hil_material_summary;
  const firstJog = robotSummary.value?.first_jog_readiness_summary;
  if (!summary || !firstJog) {
    return "operator report not loaded";
  }
  if (firstJogMaterialRestoreReady.value) {
    return `latest-only operator report is ${summary.site_state}; visual material kept; missing=${firstJog.missing_fields.join(",")}; action=restore first-jog confirmation`;
  }
  if (firstJog.status === "ready_for_first_jog") {
    return "first-jog material ready; next=run observed trial";
  }
  return `first-jog ${firstJog.status}; missing=${firstJog.missing_fields.join(",") || "none"}; next=${firstJog.next_action}`;
});

const plainVisualMaterialSubmitted = computed(() => {
  // 本页刚提交的视觉材料可作为立即试动的本地反馈；最终仍由后端 first-jog preflight 复核。
  return plainVisualMaterialResult.value?.proxy_status === "report_forwarded" && plainVisualMaterialResult.value.status !== "blocked";
});

const plainFirstJogMaterialRestored = computed(() => {
  // 恢复确认成功后允许进入 first-jog；后端仍会再次读取 latest operator report。
  return plainFirstJogMaterialRestoreResult.value?.proxy_status === "report_forwarded" && plainFirstJogMaterialRestoreResult.value.status !== "blocked";
});

const canSendPlainFirstJog = computed(() => {
  // 普通试动必须先有 first-jog 材料；送达草稿覆盖状态下必须先点“恢复试动确认”。
  if (!robotApiBaseUrl.value.trim() || loading.value || manualCommandPending.value) {
    return false;
  }
  if (plainFirstJogMaterialRestored.value || plainVisualMaterialSubmitted.value) {
    return true;
  }
  if (firstJogMaterialRestoreReady.value) {
    return false;
  }
  return robotSummary.value?.first_jog_readiness_summary?.status === "ready_for_first_jog";
});

const plainFirstJogBlockedHint = computed(() => {
  // 首屏禁用原因必须是普通话术；工程细节留给高级诊断。
  if (canSendPlainFirstJog.value) {
    return "";
  }
  if (!robotApiBaseUrl.value.trim()) {
    return "试动按钮已锁定：先连接小车。";
  }
  if (loading.value || manualCommandPending.value) {
    return "试动按钮已锁定：正在处理上一条请求。";
  }
  if (firstJogMaterialRestoreReady.value) {
    return "试动按钮已锁定：请先点恢复试动确认（不会发车）。";
  }
  if (!firstJogVisualMaterialReady.value && !plainVisualMaterialSubmitted.value) {
    return "试动按钮已锁定：请先记录现场画面。";
  }
  return "试动按钮已锁定：移动前确认还未满足。";
});

const plainFirstJogEvidenceSummary = computed(() => {
  // 普通首屏只压缩试动后的轮速结果；完整 raw key 仍留在高级诊断。
  const result = plainFirstJogResult.value;
  if (!result) {
    return "";
  }
  if (result.proxy_status !== "command_forwarded") {
    return "轮速证据未采集：小车没有进入试动。";
  }
  const values = result.remote_motion_key_values;
  if (!values) {
    return "轮速证据未返回：请查看高级诊断。";
  }
  const left = values.wheel_feedback_latest_raw_left ?? "not_loaded";
  const right = values.wheel_feedback_latest_raw_right ?? "not_loaded";
  const frames = values.feedback_during_motion_t1001_frame_count ?? "0";
  if (values.wheel_feedback_lr_nonzero_proven === "true") {
    return `轮速证据已拿到：L/R=${left}/${right}，运动帧=${frames}。`;
  }
  if (frames !== "0" && left !== "not_loaded" && right !== "not_loaded") {
    return `已试动，但轮速还是 ${left}/${right}：检查电机使能、供电、模式和现场空间后重试。运动帧=${frames}。`;
  }
  return `已试动，但轮速非零还没拿到：L/R=${left}/${right}，运动帧=${frames}。`;
});

const plainWheelRecordSummary = computed(() => {
  // 轮速记录是本轮目标的独立步骤；首屏需要常驻提示，不等试动完成后才出现按钮。
  if (plainWheelEvidenceSavePending.value) {
    return { state: "保存中", hint: "正在保存轮速记录。" };
  }
  if (plainWheelEvidenceSaveResult.value?.proxy_status === "report_forwarded" && plainWheelEvidenceSaveResult.value.status !== "blocked") {
    return {
      state: "已保存",
      hint: plainFirstJogLidarDeltaReady.value ? "轮速和雷达记录已保存；键盘手控材料可复用。" : "轮速记录已保存；键盘手控材料可复用。",
    };
  }
  if (plainFirstJogWheelEvidenceReady.value) {
    return {
      state: "可保存",
      hint: plainFirstJogLidarDeltaReady.value ? "已拿到非零 L/R 和雷达移动记录，先保存。" : "已拿到非零 L/R，先保存轮速记录。",
    };
  }
  if (plainFirstJogResult.value?.proxy_status === "command_forwarded") {
    const values = plainFirstJogResult.value.remote_motion_key_values;
    const left = values?.wheel_feedback_latest_raw_left ?? "not_loaded";
    const right = values?.wheel_feedback_latest_raw_right ?? "not_loaded";
    if (left !== "not_loaded" && right !== "not_loaded") {
      return { state: "待重试", hint: `已试动但 L/R=${left}/${right}，检查电机使能、供电、模式和现场空间后重试。` };
    }
    return { state: "待重试", hint: "已试动，但还没拿到非零 L/R。" };
  }
  if (firstJogMaterialRestoreReady.value) {
    return { state: "待确认", hint: "先点“恢复试动确认”（不会发车），再试动读取轮速。" };
  }
  if (canSendPlainFirstJog.value) {
    return { state: "待试动", hint: "点“试动一下”后读取轮速。" };
  }
  if (firstJogVisualMaterialReady.value || plainVisualMaterialSubmitted.value) {
    return { state: "待确认", hint: "现场画面已在，先完成试动前确认。" };
  }
  return { state: "待准备", hint: "先记录现场画面，再试动读取轮速。" };
});

const plainWheelTrialButtonLabel = computed(() => {
  // 轮速面板里的按钮复用 first-jog；已有一次失败试动后，文案改为重试，减少现场误解。
  if (!robotApiBaseUrl.value.trim()) {
    return "连接后试动读轮速";
  }
  if (loading.value || manualCommandPending.value) {
    return "等待上一条请求";
  }
  if (firstJogMaterialRestoreReady.value && !plainFirstJogMaterialRestored.value) {
    return "先恢复确认再试动";
  }
  if (!firstJogVisualMaterialReady.value && !plainVisualMaterialSubmitted.value) {
    return "先记录画面再试动";
  }
  if (plainFirstJogResult.value?.proxy_status === "command_forwarded" && !plainFirstJogWheelEvidenceReady.value) {
    return "重试低速试动读非零 L/R";
  }
  if (plainFirstJogMaterialRestored.value) {
    return "开始低速试动读非零 L/R";
  }
  const sample = baseFeedbackSamplesResult.value?.sample_key_values;
  const base = robotSummary.value?.readback_summary.base;
  if ((sample && isZeroWheelPair(sample.wheel_feedback_latest_left_speed, sample.wheel_feedback_latest_right_speed))
    || (base && isZeroWheelPair(base.wheel_feedback_latest_left_speed, base.wheel_feedback_latest_right_speed))) {
    return "低速试动读非零 L/R";
  }
  return "低速试动读轮速";
});

const plainWheelEvidenceSaveButtonLabel = computed(() => {
  // 保存按钮只有拿到同帧非零 L/R 才能点；禁用文案直接说明还在等什么。
  if (plainWheelEvidenceSavePending.value || operatorReportPending.value) {
    return "保存中";
  }
  return plainFirstJogWheelEvidenceReady.value ? "保存轮速记录" : "保存轮速记录（等非零 L/R）";
});

const plainWheelReadbackButtonLabel = computed(() => (
  baseFeedbackSamplesPending.value ? "刷新中" : "刷新当前轮速（只读）"
));

const plainWheelEvidenceSaveSummary = computed(() => {
  // 保存状态只用普通话术；完整 operator report 响应留在高级诊断。
  if (plainWheelEvidenceSavePending.value) {
    return "正在保存轮速证据。";
  }
  if (!plainWheelEvidenceSaveResult.value) {
    return "";
  }
  if (plainWheelEvidenceSaveResult.value.proxy_status === "report_forwarded" && plainWheelEvidenceSaveResult.value.status !== "blocked") {
    return plainFirstJogLidarDeltaReady.value
      ? "轮速和雷达移动证据已保存；后续手控材料可复用。"
      : "轮速证据已保存；后续手控材料可复用。";
  }
  return "轮速证据保存失败；请查看高级诊断。";
});

const plainWheelNextActionSummary = computed(() => {
  // 当反馈链路已在线但 L/R 仍为 0/0 时，把现场排障动作直接放在轮速模块里。
  const firstJogValues = plainFirstJogResult.value?.remote_motion_key_values;
  if (plainFirstJogResult.value?.proxy_status === "command_forwarded"
    && isZeroWheelPair(firstJogValues?.wheel_feedback_latest_raw_left, firstJogValues?.wheel_feedback_latest_raw_right)) {
    return WHEEL_ZERO_NEXT_ACTION_SUMMARY;
  }
  const sample = baseFeedbackSamplesResult.value?.sample_key_values;
  if (sample?.t1001_observed_count && sample.t1001_observed_count !== "not_loaded"
    && isZeroWheelPair(sample.wheel_feedback_latest_left_speed, sample.wheel_feedback_latest_right_speed)) {
    return WHEEL_ZERO_NEXT_ACTION_SUMMARY;
  }
  const base = robotSummary.value?.readback_summary.base;
  if (base?.latest_t1001_observed_count && base.latest_t1001_observed_count !== "not_loaded"
    && isZeroWheelPair(base.wheel_feedback_latest_left_speed, base.wheel_feedback_latest_right_speed)) {
    return WHEEL_ZERO_NEXT_ACTION_SUMMARY;
  }
  return "";
});

const plainWheelReadbackSummary = computed(() => {
  // 只读底盘反馈可以解释“当前为什么还不是非零证据”，但不能替代试动窗口材料。
  const base = robotSummary.value?.readback_summary.base;
  const voltage = base?.feedback_voltage_v && base.feedback_voltage_v !== "not_loaded" ? `；反馈电压约 ${base.feedback_voltage_v}V` : "";
  const staleSamples = base?.latest_feedback_status === "stale" ? "；历史轮速样本已过期，以当前读回为准" : "";
  const zeroReadbackNextStep = "这还不是非零证据；若试动后仍为 0/0，检查电机使能、供电、模式和现场空间。";
  const sample = baseFeedbackSamplesResult.value?.sample_key_values;
  if (sample?.t1001_observed_count && sample.t1001_observed_count !== "not_loaded") {
    const left = sample.wheel_feedback_latest_left_speed;
    const right = sample.wheel_feedback_latest_right_speed;
    if (sample.wheel_feedback_lr_nonzero_proven === "true" || sample.wheel_feedback_nonzero_observed === "true") {
      return `只读轮速已出现非零：L/R=${left}/${right}；仍以试动窗口保存为准。`;
    }
    return `已读到底盘反馈，但当前轮速是 L/R=${left}/${right}${voltage}；${zeroReadbackNextStep}`;
  }
  if (!base || base.latest_t1001_observed_count === "not_loaded") {
    return "";
  }
  const left = base.wheel_feedback_latest_left_speed;
  const right = base.wheel_feedback_latest_right_speed;
  if (!left || !right || left === "not_loaded" || right === "not_loaded") {
    return "";
  }
  if (base.wheel_feedback_lr_nonzero_proven === "true" || base.wheel_feedback_nonzero_observed === "true") {
    return `只读轮速已出现非零：L/R=${left}/${right}；仍以试动窗口保存为准。`;
  }
  if (Number(base.latest_t1001_observed_count) > 0) {
    return `已读到底盘反馈，但当前轮速是 L/R=${left}/${right}${voltage}${staleSamples}；${zeroReadbackNextStep}`;
  }
  return "";
});

const plainLidarMotionRecordSummary = computed(() => {
  // LiDAR delta 是试动后的运动证据；普通首屏只说明下一步，不展示后端字段名。
  if (plainFirstJogLidarDeltaReady.value) {
    return plainWheelEvidenceSaveResult.value?.proxy_status === "report_forwarded" && plainWheelEvidenceSaveResult.value.status !== "blocked"
      ? "雷达移动记录已随轮速记录保存；后续键盘手控可复用。"
      : "雷达移动记录已拿到：保存轮速记录时会一起保存。";
  }
  if (!operatorMaterialMissingFields.value.includes("physical_motion_lidar_delta_proven")) {
    return "";
  }
  const gaps = plainFirstJogResult.value?.motion_evidence_gaps ?? [];
  if (gaps.includes("physical_motion_lidar_delta_not_proven")) {
    return "雷达移动记录还没拿到：已试动但雷达前后变化未通过，确认雷达已运行、现场空间足够后重试。";
  }
  if (robotSummary.value?.readback_summary.lidar.lifecycle_running === "true") {
    return "雷达移动记录还没拿到：试动时需要雷达看到前后变化，之后键盘手控才会解锁。";
  }
  return "雷达移动记录还没拿到：先确认雷达已运行，再试动读取移动变化。";
});

const plainFirstJogWheelEvidenceReady = computed(() => {
  // 只有后端 first-jog 响应明确证明 L/R 非零时，才允许保存 wheel feedback claim。
  return plainFirstJogResult.value?.proxy_status === "command_forwarded"
    && plainFirstJogResult.value.remote_motion_key_values?.wheel_feedback_lr_nonzero_proven === "true";
});

const plainFirstJogLidarDeltaReady = computed(() => {
  // LiDAR 位移可以来自 first-jog 后的固定 readback；没有缺口才允许写入材料。
  const result = plainFirstJogResult.value;
  return result?.proxy_status === "command_forwarded"
    && (result.evidence_capture_status === "captured" || result.evidence_capture_status === "partial")
    && !result.motion_evidence_gaps.includes("physical_motion_lidar_delta_not_proven");
});

const canSendManualMotion = computed(() => {
  // 非 stop 方向必须同时满足地址、checklist、现场材料和“当前无 pending”。
  return !manualCommandPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0 && hilChecklistConfirmed.value && operatorMaterialReady.value;
});

const keyboardControlSummary = computed(() => {
  // 高级诊断保留完整 gate 状态，便于现场排障；普通首屏会用另一套不泄露字段名的话术。
  if (keyboardHeldDirection.value) {
    return { state: "手控中", hint: `${keyboardLastDirection.value} 按住点动中；松开按键、窗口失焦或页面隐藏会发送停止。` };
  }
  if (keyboardControlArmed.value && canUseKeyboardControl.value) {
    return { state: "已启用", hint: "键盘面板已聚焦：按住 W/A/S/D 或方向键连续点动，松开即停。" };
  }
  if (canUseKeyboardControl.value) {
    return { state: "可手控", hint: "点击“启用键盘”后，按住 W/A/S/D 或方向键连续点动，松开即停。" };
  }
  if (!keyboardContractReady.value) {
    return { state: "未满足", hint: "键盘合同未从 summary 读到；本机不会启用连续手控。" };
  }
  if (keyboardControlStatus.value.startsWith("blocked")) {
    return { state: "未满足", hint: keyboardControlStatus.value };
  }
  return { state: "未满足", hint: manualBlockedReason.value };
});

const plainKeyboardMissingLabels = computed(() => {
  // 普通首屏只给普通步骤名，不暴露 operator report、HIL 或后端字段名。
  if (canUseKeyboardControl.value) {
    return [];
  }
  if (!robotApiBaseUrl.value.trim()) {
    return ["小车连接"];
  }
  if (manualCommandPending.value || loading.value) {
    return [];
  }
  const missing = new Set<string>();
  if (!keyboardContractReady.value) {
    missing.add("键盘入口");
  }
  if (!hilChecklistConfirmed.value) {
    missing.add("移动前检查");
  }
  const materialMissing = operatorMaterialMissingFields.value;
  if (materialMissing.some((field) => ["operator_present", "physical_clearance_confirmed", "emergency_stop_ready"].includes(field))) {
    missing.add("移动前检查");
  }
  if (materialMissing.some((field) => ["external_video_recorded", "visible_content_proven"].includes(field))) {
    missing.add("现场画面");
  }
  if (materialMissing.includes("wheel_feedback_lr_nonzero_proven")) {
    missing.add("轮速记录");
  }
  if (materialMissing.includes("physical_motion_lidar_delta_proven")) {
    missing.add("雷达移动记录");
  }
  if (missing.size === 0 && !operatorMaterialReady.value) {
    missing.add("现场材料读取");
  }
  return Array.from(missing);
});

const plainKeyboardMissingSummary = computed(() => {
  // pending 态不是缺项，不把按钮文案变成“还差 0 项”。
  if (canUseKeyboardControl.value) {
    return "";
  }
  if (manualCommandPending.value || loading.value) {
    return "正在处理上一条请求，请稍等。";
  }
  const missingLabels = plainKeyboardMissingLabels.value;
  return `还差：${missingLabels.join("、")}。`;
});

const plainKeyboardWheelProofIsNext = computed(() => {
  const missingLabels = plainKeyboardMissingLabels.value;
  const higherPriorityMissing = ["小车连接", "键盘入口", "移动前检查", "现场画面"]
    .some((label) => missingLabels.includes(label));
  // 只有连接、安全和画面这些前置步骤都过了，轮速才是键盘 gate 的第一下一步。
  return !higherPriorityMissing && missingLabels.includes("轮速记录");
});

const plainKeyboardArmButtonLabel = computed(() => {
  // 启用只让键盘面板获得焦点；真正手控必须后续按住方向键。
  const missingLabels = plainKeyboardMissingLabels.value;
  const missingCount = missingLabels.length;
  // 轮速是当前真实收口的高频卡点；只有前置条件都过了，按钮才直接提示先补轮速。
  if (plainKeyboardWheelProofIsNext.value) {
    return "启用键盘（先补轮速）";
  }
  return missingCount > 0 ? `启用键盘（还差 ${missingCount} 项）` : "启用键盘（按键才动）";
});

const plainKeyboardRecheckButtonLabel = computed(() => {
  // 复查按钮同样显示缺项数量；点击仍只刷新只读进度，不会发送手控。
  const missingCount = plainKeyboardMissingLabels.value.length;
  if (plainKeyboardWheelProofIsNext.value) {
    return "复查手控条件（先补轮速，不发车）";
  }
  return missingCount > 0 ? `复查手控条件（还差 ${missingCount} 项，不发车）` : "复查手控条件";
});

const plainKeyboardNextActionSummary = computed(() => {
  // 键盘 gate 缺项可能较多；现场只需要知道当前先做哪个普通动作。
  if (canUseKeyboardControl.value) {
    return "";
  }
  if (!robotApiBaseUrl.value.trim()) {
    return "下一步：连接小车。";
  }
  if (!keyboardContractReady.value) {
    return "下一步：复查手控条件。";
  }
  if (!hilChecklistConfirmed.value) {
    return "下一步：完成移动前检查。";
  }
  const materialMissing = operatorMaterialMissingFields.value;
  if (materialMissing.some((field) => ["operator_present", "physical_clearance_confirmed", "emergency_stop_ready"].includes(field))) {
    return "下一步：完成移动前检查。";
  }
  if (materialMissing.some((field) => ["external_video_recorded", "visible_content_proven"].includes(field))) {
    return "下一步：记录现场画面。";
  }
  if (materialMissing.includes("wheel_feedback_lr_nonzero_proven")) {
    return "下一步：读取并保存轮速记录。";
  }
  if (materialMissing.includes("physical_motion_lidar_delta_proven")) {
    return "下一步：试动读取雷达移动记录。";
  }
  return "下一步：复查手控条件。";
});

const plainKeyboardControlSummary = computed(() => {
  // 普通首屏只说“能不能用”和“怎么停”，不展示 operator report 字段名或 HIL 术语。
  if (keyboardHeldDirection.value) {
    return { state: "手控中", hint: "按住点动中；松开按键、窗口失焦或页面隐藏会自动停止。" };
  }
  if (keyboardControlArmed.value && canUseKeyboardControl.value) {
    return { state: "已启用", hint: "按住 W/A/S/D 或方向键连续手控，松开即停。" };
  }
  if (canUseKeyboardControl.value) {
    return { state: "可手控", hint: "点击启用键盘，让这个小面板获得焦点后再按方向键。" };
  }
  if (keyboardControlArmed.value || keyboardControlStatus.value.startsWith("blocked")) {
    return { state: "未满足", hint: `移动条件还没满足，暂不发送键盘手控。${plainKeyboardMissingSummary.value} ${plainKeyboardNextActionSummary.value}` };
  }
  return { state: "未满足", hint: `先补齐键盘手控条件，再启用键盘。${plainKeyboardMissingSummary.value} ${plainKeyboardNextActionSummary.value}` };
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
  // 首屏只呈现定位/停靠状态和普通检查提示，不暴露点动、路径、材料或接口细节。
  if (localizationResetPending.value) {
    return { state: "定位中", hint: "正在重新定位；不会发车。" };
  }
  if (plainMotionPrecheckPending.value) {
    return { state: "检查中", hint: "正在记录移动前检查；不会发车。" };
  }
  if (plainVisualMaterialPending.value) {
    return { state: "记录中", hint: "正在记录现场画面；不会发车。" };
  }
  if (plainFirstJogMaterialRestorePending.value) {
    return { state: "确认中", hint: "正在恢复试动前确认；不会发车。" };
  }
  if (localizationResetResult.value) {
    if (localizationResetResult.value.proxy_status === "refresh_forwarded" && localizationResetResult.value.status !== "blocked") {
      return { state: "已定位", hint: "定位已返回；需要时可直接停止。" };
    }
    return { state: "定位失败", hint: localizationResetResult.value.failure_reason || "定位请求失败。" };
  }
  if (plainFirstJogResult.value) {
    if (plainFirstJogResult.value.proxy_status === "command_forwarded") {
      return { state: "已试动", hint: "试动请求已发送；观察小车，需要时点停止。" };
    }
    if (plainFirstJogResult.value.failure_reason === "first_jog_preflight_required") {
      return { state: "未试动", hint: "还需要先记录现场画面，小车没有移动。" };
    }
    return { state: "试动失败", hint: "请求被拒绝，小车没有移动。" };
  }
  if (plainFirstJogMaterialRestoreResult.value) {
    if (plainFirstJogMaterialRestoreResult.value.proxy_status === "report_forwarded" && plainFirstJogMaterialRestoreResult.value.status !== "blocked") {
      return { state: "待试动", hint: "试动前确认已恢复；可以试动一下。" };
    }
    return { state: "确认失败", hint: plainFirstJogMaterialRestoreResult.value.failure_reason || "试动前确认恢复失败。" };
  }
  if (plainVisualMaterialResult.value) {
    if (plainVisualMaterialResult.value.proxy_status === "report_forwarded" && plainVisualMaterialResult.value.status !== "blocked") {
      return { state: "已记录", hint: "现场画面已记录；可以试动一下。" };
    }
    return { state: "记录失败", hint: "现场画面记录失败，小车没有移动。" };
  }
  if (plainMotionPrecheckResult.value) {
    if (plainMotionPrecheckResult.value.proxy_status === "report_forwarded" && plainMotionPrecheckResult.value.status !== "blocked") {
      return { state: "已记录", hint: "移动前检查已记录；还需要现场画面。" };
    }
    return { state: "检查失败", hint: plainMotionPrecheckResult.value.failure_reason || "移动前检查提交失败。" };
  }
  if (manualCommandPending.value) {
    return { state: "处理中", hint: "正在处理请求。" };
  }
  if (!manualCommandResult.value) {
    if (firstJogMaterialRestoreReady.value) {
      return { state: "待确认", hint: "已有现场画面；请恢复试动确认后再试动，恢复确认不会发车。" };
    }
    if (firstJogVisualMaterialReady.value) {
      return { state: "待试动", hint: "现场画面已记录；可以试动一下。" };
    }
    return { state: "待记录", hint: "先记录现场画面，再试动一下；需要时可直接停止。" };
  }
  if (manualCommandResult.value.command_kind === "stop" && manualCommandResult.value.proxy_status === "command_forwarded") {
    return { state: "已停止", hint: "停止请求已发送。" };
  }
  if (manualCommandResult.value.command_kind === "stop") {
    return { state: "停止失败", hint: manualCommandResult.value.failure_reason || "停止请求失败。" };
  }
  return operatorMaterialReady.value
    ? { state: "待命", hint: "已完成移动前检查；需要时可直接停止。" }
    : { state: "待记录", hint: "先记录现场画面，再试动一下；需要时可直接停止。" };
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

function requestBodyForDirection(direction: ManualDirection) {
  // 提交前再次按当前边界 clamp，避免浏览器层被手工改值后越过安全上限。
  return {
    direction,
    speed: Math.min(Math.max(jogSpeedMps.value, 0), manualSpeedLimit.value),
    duration_ms: Math.min(Math.max(jogDurationMs.value, 0), manualDurationLimit.value),
    confirm_hil_checklist: hilChecklistConfirmed.value,
  } as const;
}

function requestBodyForKeyboardDirection(direction: ManualDirection) {
  // 键盘连续手控采用短脉冲重复发送，降低“按键卡住”时单条命令持续过久的风险。
  return {
    direction,
    speed: Math.min(Math.max(jogSpeedMps.value, 0), manualSpeedLimit.value),
    duration_ms: Math.min(Math.max(keyboardJogDurationMs.value, 0), manualDurationLimit.value),
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
    motion_evidence_gaps: commandKind === "stop"
      ? ["stop_command_not_motion_proof"]
      : ["motion_command_not_forwarded", "wheel_feedback_lr_nonzero_not_proven", "physical_motion_lidar_delta_not_proven"],
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

function makeNavGoalExecutionFallback(reason: string): RobotControlNavGoalExecutionResponse {
  // 执行异常也只能展示为失败；不能把浏览器状态写成 delivery success。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "execution_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    workstation_endpoint: "/api/robot-control/nav2/goal/execute",
    remote_endpoint: "/api/nav2/goal/execute",
    remote_http_status: null,
    status: "blocked",
    goal_request: {
      goal_frame_id: "map",
      goal_x: navGoalX.value,
      goal_y: navGoalY.value,
      goal_yaw: navGoalYaw.value,
      result_timeout_s: navGoalExecutionTimeoutS.value,
      confirm_navigation_execution: confirmNavigationExecution.value,
    },
    goal_execution_key_values: {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function makeNavGoalExecutionLatestFallback(reason: string): RobotControlNavGoalExecutionLatestResponse {
  // latest 读取失败只代表“无法预填材料”，不能被解释成导航重新执行失败。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1",
    proxy_status: "latest_failed",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest",
    remote_endpoint: "/api/nav2/goal/execution/latest",
    remote_http_status: null,
    status: "blocked",
    goal_execution_key_values: {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function makeDeliveryCompletionFallback(reason: string): RobotControlDeliveryCompleteResponse {
  // 交付确认异常必须 fail closed；只有后端 gate 能把 delivery_success 置 true。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_delivery_complete_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "completion_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    workstation_endpoint: "/api/robot-control/delivery/complete",
    remote_endpoint: "/api/delivery/complete",
    remote_http_status: null,
    status: "blocked",
    request_body: {
      confirm_delivery_completion: confirmDeliveryCompletion.value,
      delivery_evidence_ref: deliveryEvidenceRef.value,
    },
    delivery_key_values: {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function makeDeliveryLatestFallback(reason: string): RobotControlDeliveryLatestResponse {
  // 送达 latest 读取失败只表示缺口未知；不能默认认为送达 gate 已满足。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1",
    proxy_status: "latest_failed",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    workstation_endpoint: "/api/robot-control/delivery/latest",
    remote_endpoint: "/api/delivery/latest",
    remote_http_status: null,
    status: "blocked",
    delivery_key_values: {},
    delivery_material_refs: {
      operator_evidence_ref: "",
      external_video_ref: "",
      camera_artifacts_ref: "",
      route_map_ref: "",
      site_state: "",
    },
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function makeDeliveryGapCheckFallback(reason: string): RobotControlDeliveryGapCheckResponse {
  // 缺口复算固定 confirm=false；异常也不能升级成送达完成。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_delivery_gap_check_proxy.v1",
    proxy_status: "check_failed",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    workstation_endpoint: "/api/robot-control/delivery/check",
    remote_endpoint: "/api/delivery/complete",
    remote_http_status: null,
    status: "blocked",
    request_body: {
      confirm_delivery_completion: false,
      delivery_evidence_ref: "delivery-gap-check-not-confirmed",
    },
    delivery_key_values: {},
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
    map_quality_summary: {
      status: "not_loaded",
      message: "地图质量还没有读取。",
      checked_yaml_count: 0,
      usable_map_count: 0,
      no_free_cell_map_count: 0,
      analysis_failed_count: 0,
    },
    map_usable_for_navigation: false,
    map_needs_rebuild: false,
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

function makeOperatorReportFallback(reason: string, requestBody: RobotControlOperatorReportRequest = operatorReportRequestBody()): RobotControlOperatorReportProxyResponse {
  // 前端异常时也补齐同一响应合同，避免最近提交状态缺失安全字段。
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

function plainMotionPrecheckRequestBody(): RobotControlOperatorReportRequest {
  // 普通检查只确认人在场、周围安全和急停可用；已有进度材料只保留，不补造。
  const inheritedProgressClaims = inheritedProgressClaimsFromSummary();
  return {
    operator_present: true,
    evidence_ref: `plain-motion-precheck-${Date.now()}`,
    physical_clearance_confirmed: true,
    emergency_stop_ready: true,
    observed_motion: false,
    observed_stop: true,
    reported_at: new Date().toISOString(),
    operator_notes: "plain PC motion precheck only; does not prove video, wheel feedback, lidar delta, or motion.",
    structured_hil_claims: {
      external_video_recorded: false,
      visible_content_proven: false,
      ...inheritedProgressClaims,
      delivery_success: false,
      site_state: "plain_motion_precheck_ready_for_review",
    },
  };
}

function plainVisualMaterialRequestBody(): RobotControlOperatorReportRequest {
  // 普通记录画面只提交人工外部视频索引；已有进度材料只保留，不补造。
  const videoRef = plainExternalVideoRef.value.trim();
  const inheritedProgressClaims = inheritedProgressClaimsFromSummary();
  return {
    operator_present: true,
    evidence_ref: `plain-first-jog-video-${Date.now()}`,
    physical_clearance_confirmed: true,
    emergency_stop_ready: true,
    observed_motion: false,
    observed_stop: true,
    reported_at: new Date().toISOString(),
    operator_notes: "plain PC first-jog visual material; does not prove wheel feedback, lidar delta, route map, or delivery success.",
    structured_hil_claims: {
      external_video_recorded: true,
      external_video_ref: videoRef,
      visible_content_proven: false,
      ...inheritedProgressClaims,
      delivery_success: false,
      site_state: "plain_first_jog_visual_ready_for_review",
    },
  };
}

function claimRefFromSummary(value: string | undefined): string {
  // summary 的格式来自后端 "true; ref=..." 合同；只复用明确为 true 的可追溯 ref。
  const prefix = "true; ref=";
  if (!value?.startsWith(prefix)) {
    return "";
  }
  const refValue = value.slice(prefix.length).trim();
  return refValue && refValue !== "not_loaded" ? refValue : "";
}

function inheritedProgressClaimsFromSummary(): Pick<
  NonNullable<RobotControlOperatorReportRequest["structured_hil_claims"]>,
  | "wheel_feedback_lr_nonzero_proven"
  | "wheel_feedback_ref"
  | "physical_motion_lidar_delta_proven"
  | "scan_delta_ref"
  | "real_route_map_proven"
  | "route_map_ref"
> {
  // latest-only operator report 不能把已有 wheel/LiDAR/route 材料冲掉；只有明确 true; ref=... 才继承。
  const summary = robotSummary.value?.operator_hil_material_summary;
  const wheelRef = claimRefFromSummary(summary?.wheel_feedback);
  const scanDeltaRef = claimRefFromSummary(summary?.lidar_delta);
  const routeMapRef = claimRefFromSummary(summary?.route_map);
  return {
    wheel_feedback_lr_nonzero_proven: Boolean(wheelRef),
    ...(wheelRef ? { wheel_feedback_ref: wheelRef } : {}),
    physical_motion_lidar_delta_proven: Boolean(scanDeltaRef),
    ...(scanDeltaRef ? { scan_delta_ref: scanDeltaRef } : {}),
    real_route_map_proven: Boolean(routeMapRef),
    ...(routeMapRef ? { route_map_ref: routeMapRef } : {}),
  };
}

function inheritedBasicSafetyFromSummary(): Pick<RobotControlOperatorReportRequest, "operator_present" | "physical_clearance_confirmed" | "emergency_stop_ready"> {
  // 送达草稿只保留已有 basic safety 确认；没有当前 true 读回时仍保持 false，避免伪造现场人在场。
  const summary = robotSummary.value?.operator_hil_material_summary;
  return {
    operator_present: summary?.operator_present === "true",
    physical_clearance_confirmed: summary?.physical_clearance === "true",
    emergency_stop_ready: summary?.emergency_stop === "true",
  };
}

function plainFirstJogMaterialRestoreRequestBody(): RobotControlOperatorReportRequest {
  // 恢复试动材料只重写 first-jog 前置项；已有进度材料只保留，不补造。
  const summary = robotSummary.value?.operator_hil_material_summary;
  const externalVideoRef = claimRefFromSummary(summary?.external_video);
  const cameraArtifactRef = claimRefFromSummary(summary?.camera_visible);
  const inheritedProgressClaims = inheritedProgressClaimsFromSummary();
  return {
    operator_present: true,
    evidence_ref: `plain-first-jog-restore-${Date.now()}`,
    physical_clearance_confirmed: true,
    emergency_stop_ready: true,
    observed_motion: false,
    observed_stop: true,
    reported_at: new Date().toISOString(),
    operator_notes: "plain PC first-jog material restore after delivery draft; does not prove wheel feedback, lidar delta, route map, or delivery success.",
    structured_hil_claims: {
      external_video_recorded: Boolean(externalVideoRef),
      ...(externalVideoRef ? { external_video_ref: externalVideoRef } : {}),
      visible_content_proven: Boolean(cameraArtifactRef),
      ...(cameraArtifactRef ? { camera_artifacts_ref: cameraArtifactRef } : {}),
      ...inheritedProgressClaims,
      delivery_success: false,
      site_state: "plain_first_jog_material_restored_for_trial",
    },
  };
}

function plainWheelEvidenceReportRequestBody(): RobotControlOperatorReportRequest {
  // 轮速材料只能来自 first-jog 返回的 during-motion T1001 非零证明；同轮 LiDAR 位移已证明时一并保存。
  const values = plainFirstJogResult.value?.remote_motion_key_values ?? {};
  const left = values.wheel_feedback_latest_raw_left ?? "not_loaded";
  const right = values.wheel_feedback_latest_raw_right ?? "not_loaded";
  const frames = values.feedback_during_motion_t1001_frame_count ?? "0";
  const summary = robotSummary.value?.operator_hil_material_summary;
  const externalVideoRef = claimRefFromSummary(summary?.external_video);
  const cameraArtifactRef = claimRefFromSummary(summary?.camera_visible);
  const inheritedProgressClaims = inheritedProgressClaimsFromSummary();
  const wheelRef = `pc-first-jog-wheel-lr-${Date.now()}`;
  const lidarDeltaRef = firstJogLidarDeltaRef();
  return {
    operator_present: true,
    evidence_ref: wheelRef,
    physical_clearance_confirmed: true,
    emergency_stop_ready: true,
    observed_motion: true,
    observed_stop: true,
    reported_at: new Date().toISOString(),
    operator_notes: `PC first-jog wheel evidence save; L/R=${left}/${right}; during_motion_t1001_frames=${frames}; lidar_delta_saved=${Boolean(lidarDeltaRef)}; does not prove route map or delivery success.`,
    structured_hil_claims: {
      external_video_recorded: Boolean(externalVideoRef),
      ...(externalVideoRef ? { external_video_ref: externalVideoRef } : {}),
      visible_content_proven: Boolean(cameraArtifactRef),
      ...(cameraArtifactRef ? { camera_artifacts_ref: cameraArtifactRef } : {}),
      ...inheritedProgressClaims,
      wheel_feedback_lr_nonzero_proven: true,
      wheel_feedback_ref: wheelRef,
      ...(lidarDeltaRef ? { physical_motion_lidar_delta_proven: true, scan_delta_ref: lidarDeltaRef } : {}),
      delivery_success: false,
      site_state: "plain_first_jog_wheel_lr_nonzero_observed",
    },
  };
}

function firstJogLidarDeltaRef(): string {
  // 优先复用上位机返回的 scan delta ref；没有显式 ref 时生成 PC 侧可追踪短 ref。
  if (!plainFirstJogLidarDeltaReady.value) {
    return "";
  }
  const result = plainFirstJogResult.value;
  const remoteValues = result?.remote_motion_key_values ?? {};
  const directRef = remoteValues.scan_delta_ref
    ?? remoteValues.lidar_motion_delta_ref
    ?? result?.after_readback.radar_status?.key_values.scan_delta_ref
    ?? result?.after_readback.radar_scan_proof_latest?.key_values.scan_delta_ref
    ?? result?.after_readback.radar_status?.key_values.evidence_ref
    ?? result?.after_readback.radar_scan_proof_latest?.key_values.evidence_ref;
  if (directRef && directRef !== "not_loaded") {
    return directRef;
  }
  return `pc-first-jog-lidar-delta-${Date.now()}`;
}

function plainFirstJogRequestBody(): RobotControlBaseCommandRequest {
  // 普通首屏只发固定 forward 低速短时 first-jog；方向、速度和时长不开放给普通用户。
  return {
    direction: "forward",
    speed: 0.08,
    duration_ms: 500,
    confirm_hil_checklist: true,
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
      backend_smoke_status: "not_requested",
      backend_frame_observed: "false",
      backend_attempts: "0",
    },
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function makeBaseFeedbackSamplesFallback(reason: string): RobotControlBaseFeedbackSamplesProxyResponse {
  // PC fetch 异常时也保持“未采集/不可控”，避免高级诊断误导 operator。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_base_feedback_samples_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "samples_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    remote_endpoint: "/api/base/feedback-samples",
    remote_http_status: null,
    status: "blocked",
    sample_key_values: {
      schema: "not_loaded",
      requested_sample_count: "not_loaded",
      completed_sample_count: "not_loaded",
      t1001_observed_count: "not_loaded",
      all_samples_observed_t1001: "not_loaded",
      partial_samples_observed_t1001: "not_loaded",
      feedback_ack_t1001_observed: "not_loaded",
      wheel_feedback_lr_nonzero_proven: "not_loaded",
      wheel_feedback_nonzero_observed: "not_loaded",
      wheel_feedback_nonzero_frame_count: "not_loaded",
      wheel_feedback_latest_left_speed: "not_observed",
      wheel_feedback_latest_right_speed: "not_observed",
      wheel_feedback_source: "not_observed",
      observed_feedback_types: "not_loaded",
      sends_motion_commands: "false",
      robot_control_executed: "false",
    },
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    sends_motion_commands: false,
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
  // 重新定位只走固定 /api/localize/reset；发布一次初始位姿，不请求路径、不发 /cmd_vel。
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

async function runNavGoalExecution(): Promise<void> {
  // 真正执行 NavigateToPose 必须显式确认；结果只作为执行证据，不自动标记交付成功。
  if (!robotApiBaseUrl.value.trim() || navGoalExecutionPending.value) {
    return;
  }
  navGoalExecutionPending.value = true;
  try {
    navGoalExecutionResult.value = await postRobotControlNav2GoalExecute(robotApiBaseUrl.value, {
      goal_frame_id: "map",
      goal_x: navGoalX.value,
      goal_y: navGoalY.value,
      goal_yaw: navGoalYaw.value,
      result_timeout_s: navGoalExecutionTimeoutS.value,
      confirm_navigation_execution: confirmNavigationExecution.value,
    });
  } catch (err) {
    navGoalExecutionResult.value = makeNavGoalExecutionFallback(err instanceof Error ? err.message : "nav_goal_execution_request_failed");
  } finally {
    navGoalExecutionPending.value = false;
    await refreshConsole();
  }
}

async function runPlainTripPreflight(): Promise<void> {
  // 普通入口固定使用当前目标参数，只是把高级预检入口翻译成普通操作。
  if (!canRunPlainTripPreflight.value) {
    return;
  }
  confirmNavigationPreflight.value = true;
  await runNavGoalPreflight();
}

async function runPlainTripExecution(): Promise<void> {
  // 普通入口只设置显式确认位，真正执行仍走固定 PC 代理和上位机 gate。
  if (!canRunPlainTripExecution.value) {
    return;
  }
  confirmNavigationExecution.value = true;
  await runNavGoalExecution();
  fillDeliveryRouteRefFromLatestNav2();
}

async function loadNavGoalExecutionLatest(): Promise<void> {
  // 读取最近执行结果只走固定 GET 代理；用于页面刷新后补回 route/map evidence ref。
  if (!robotApiBaseUrl.value.trim() || navGoalExecutionLatestPending.value) {
    return;
  }
  navGoalExecutionLatestPending.value = true;
  try {
    navGoalExecutionLatestResult.value = await getRobotControlNav2GoalExecutionLatest(robotApiBaseUrl.value);
  } catch (err) {
    navGoalExecutionLatestResult.value = makeNavGoalExecutionLatestFallback(err instanceof Error ? err.message : "nav_goal_execution_latest_request_failed");
  } finally {
    navGoalExecutionLatestPending.value = false;
  }
}

async function loadDeliveryLatest(): Promise<void> {
  // delivery latest 只读最近 gate 结论；用于明确现场还缺哪些送达材料。
  if (!robotApiBaseUrl.value.trim() || deliveryLatestPending.value) {
    return;
  }
  deliveryLatestPending.value = true;
  try {
    deliveryLatestResult.value = await getRobotControlDeliveryLatest(robotApiBaseUrl.value);
    fillDeliveryRefsFromLatestReadback();
  } catch (err) {
    deliveryLatestResult.value = makeDeliveryLatestFallback(err instanceof Error ? err.message : "delivery_latest_request_failed");
  } finally {
    deliveryLatestPending.value = false;
  }
}

function fillDeliveryRefsFromLatestReadback(): void {
  // 页面刷新后复用 delivery latest 中的草稿材料 ref；只预填输入，不提交报告、不确认送达。
  const refs = deliveryLatestResult.value?.delivery_material_refs;
  if (!refs) {
    return;
  }
  const videoRef = refs.camera_artifacts_ref || refs.external_video_ref;
  if (!deliveryOperatorVideoRef.value.trim() && videoRef && videoRef !== "not_loaded") {
    deliveryOperatorVideoRef.value = videoRef;
  }
  if (!deliveryOperatorRouteMapRef.value.trim() && refs.route_map_ref && refs.route_map_ref !== "not_loaded") {
    deliveryOperatorRouteMapRef.value = refs.route_map_ref;
    if (!deliveryEvidenceRef.value.trim()) {
      deliveryEvidenceRef.value = `delivery-confirmation-${refs.route_map_ref}`;
    }
  }
  if (!deliveryOperatorEvidenceRef.value.trim() && refs.operator_evidence_ref && refs.operator_evidence_ref !== "not_loaded") {
    deliveryOperatorEvidenceRef.value = refs.operator_evidence_ref;
  }
}

async function preloadGoalClosureReadbacks(): Promise<void> {
  // 目标收口进度只预载固定 GET 读回；不执行 Nav2 goal、不提交 delivery、不触发底盘运动。
  if (!robotApiBaseUrl.value.trim()) {
    return;
  }
  await Promise.all([
    loadNavGoalExecutionLatest(),
    loadDeliveryLatest(),
  ]);
}

async function refreshPlainGoalProgress(): Promise<void> {
  // 普通首屏刷新进度只读 summary、底盘反馈、最近行程和送达状态，不执行行程、不保存材料、不确认送达。
  if (!robotApiBaseUrl.value.trim() || plainGoalProgressPending.value) {
    return;
  }
  await refreshConsole();
  await Promise.all([
    runBaseFeedbackSamples({ refreshAfter: false }),
    preloadGoalClosureReadbacks(),
  ]);
}

function focusPlainGoalProgressTarget(targetId: string): void {
  // 进度区的“去处理”只做本页定位，不能顺手触发行程、送达、手控或任何材料提交。
  const targetMap: Record<string, HTMLElement | null> = {
    wheel: plainWheelRecordPanel.value,
    trip: plainTripRunPanel.value,
    delivery: plainDeliveryStatusPanel.value,
    keyboard: keyboardControlPanel.value,
  };
  const target = targetMap[targetId];
  if (!target) {
    return;
  }
  target.scrollIntoView?.({ block: "center", behavior: "smooth" });
  target.focus({ preventScroll: true });
}

function markDeliveryBasicSafetyConfirmed(): void {
  // 只减少现场重复勾选；到达、停稳和送达成功仍必须由 operator 分开确认。
  deliveryOperatorConfirmations.value.operator_present = true;
  deliveryOperatorConfirmations.value.physical_clearance_confirmed = true;
  deliveryOperatorConfirmations.value.emergency_stop_ready = true;
}

function markDeliveryArrivedAndStopped(): void {
  // operator 需要亲眼确认这两项；按钮只合并本地勾选，不提交 report 或 delivery gate。
  deliveryOperatorConfirmations.value.observed_motion = true;
  deliveryOperatorConfirmations.value.observed_stop = true;
}

function markDeliveryRefsVerified(): void {
  // 材料核对只代表 operator 已看过视频和行程引用；不代表送达成功。
  deliveryOperatorConfirmations.value.route_video_refs_verified = true;
}

function markDeliverySuccessConfirmed(): void {
  // 最后一项必须由 operator 显式点击；这里只勾本地确认，不触发提交。
  deliveryOperatorConfirmations.value.delivery_success = true;
}

async function checkDeliveryGap(): Promise<void> {
  // 复算缺口固定 confirm=false；它刷新 gate artifact，但不能确认送达。
  if (!robotApiBaseUrl.value.trim() || deliveryGapCheckPending.value) {
    return;
  }
  deliveryGapCheckPending.value = true;
  try {
    deliveryGapCheckResult.value = await postRobotControlDeliveryGapCheck(robotApiBaseUrl.value);
  } catch (err) {
    deliveryGapCheckResult.value = makeDeliveryGapCheckFallback(err instanceof Error ? err.message : "delivery_gap_check_request_failed");
  } finally {
    deliveryGapCheckPending.value = false;
    await loadDeliveryLatest();
    await refreshConsole();
  }
}

async function completeDelivery(): Promise<void> {
  // delivery gate 只合成最近 Nav2 执行和 operator report；按钮本身不发送运动命令。
  if (!robotApiBaseUrl.value.trim() || deliveryCompletionPending.value) {
    return;
  }
  deliveryCompletionPending.value = true;
  try {
    deliveryCompletionResult.value = await postRobotControlDeliveryComplete(robotApiBaseUrl.value, {
      confirm_delivery_completion: confirmDeliveryCompletion.value,
      delivery_evidence_ref: deliveryEvidenceRef.value.trim(),
      operator_notes: "PC advanced delivery completion gate; requires latest Nav2 goal and operator report material.",
    });
  } catch (err) {
    deliveryCompletionResult.value = makeDeliveryCompletionFallback(err instanceof Error ? err.message : "delivery_completion_request_failed");
  } finally {
    deliveryCompletionPending.value = false;
    await loadDeliveryLatest();
    await refreshConsole();
  }
}

function fillDeliveryRouteRefFromLatestNav2(): void {
  // 最近 Nav2 execution evidence_ref 可作为 route_map_ref 候选；现场仍需自己确认送达和视频材料。
  const nav2Ref = navGoalExecutionResult.value?.goal_execution_key_values.evidence_ref
    ?? navGoalExecutionLatestResult.value?.goal_execution_key_values.evidence_ref;
  if (nav2Ref && nav2Ref !== "not_loaded") {
    deliveryOperatorRouteMapRef.value = nav2Ref;
    deliveryEvidenceRef.value = `delivery-confirmation-${nav2Ref}`;
    if (!deliveryOperatorEvidenceRef.value.trim()) {
      deliveryOperatorEvidenceRef.value = `operator-${nav2Ref}`;
    }
  }
}

function latestCameraProbeSampleRef(): string {
  // 样张 ref 只能来自固定 camera first-frame probe，不能用任意本地路径或手写危险字段代替。
  const samplePath = cameraFirstFrameProbeResult.value?.probe_key_values.sample_path ?? "";
  if (samplePath && samplePath !== "not_loaded" && samplePath !== "not_available") {
    return samplePath;
  }
  return "";
}

async function fillDeliveryVideoRefFromCameraProbe(): Promise<void> {
  // 送达视频 ref 预填只采集可追溯样张路径；仍要求现场显式确认送达。
  if (!robotApiBaseUrl.value.trim() || cameraFirstFrameProbePending.value) {
    return;
  }
  let sampleRef = latestCameraProbeSampleRef();
  if (!sampleRef) {
    await runCameraFirstFrameProbe();
    sampleRef = latestCameraProbeSampleRef();
  }
  if (sampleRef) {
    deliveryOperatorVideoRef.value = sampleRef;
  }
}

async function prefillDeliveryMaterialRefs(): Promise<void> {
  // 一键预填只收集 ref，不提交 operator report；最终送达仍由现场人员显式确认。
  if (!robotApiBaseUrl.value.trim()) {
    return;
  }
  const existingNav2Ref = navGoalExecutionResult.value?.goal_execution_key_values.evidence_ref
    ?? navGoalExecutionLatestResult.value?.goal_execution_key_values.evidence_ref;
  if (!deliveryOperatorRouteMapRef.value.trim() && (!existingNav2Ref || existingNav2Ref === "not_loaded")) {
    await loadNavGoalExecutionLatest();
  }
  if (!deliveryOperatorRouteMapRef.value.trim()) {
    fillDeliveryRouteRefFromLatestNav2();
  }
  if (!deliveryOperatorVideoRef.value.trim()) {
    await fillDeliveryVideoRefFromCameraProbe();
  }
  await loadDeliveryLatest();
}

async function submitDeliveryDraftMaterial(): Promise<void> {
  // 草稿只保存 ref 材料；成功后自动复算 confirm=false 缺口，减少现场下一步点击。
  if (
    !robotApiBaseUrl.value.trim()
    || operatorReportPending.value
    || !deliveryOperatorVideoRef.value.trim()
    || !deliveryOperatorRouteMapRef.value.trim()
  ) {
    return;
  }
  operatorReportPending.value = true;
  const evidenceRef = deliveryOperatorEvidenceRef.value.trim() || `delivery-draft-${Date.now()}`;
  const inheritedProgressClaims = inheritedProgressClaimsFromSummary();
  const inheritedBasicSafety = inheritedBasicSafetyFromSummary();
  const reportBody: RobotControlOperatorReportRequest = {
    operator_present: inheritedBasicSafety.operator_present,
    evidence_ref: evidenceRef,
    physical_clearance_confirmed: inheritedBasicSafety.physical_clearance_confirmed,
    emergency_stop_ready: inheritedBasicSafety.emergency_stop_ready,
    observed_motion: false,
    observed_stop: false,
    reported_at: new Date().toISOString(),
    operator_notes: "PC delivery draft only; visual and route/map refs are captured, but operator has not confirmed delivery.",
    structured_hil_claims: {
      external_video_recorded: true,
      external_video_ref: deliveryOperatorVideoRef.value.trim(),
      visible_content_proven: true,
      camera_artifacts_ref: deliveryOperatorVideoRef.value.trim(),
      ...inheritedProgressClaims,
      real_route_map_proven: true,
      route_map_ref: deliveryOperatorRouteMapRef.value.trim(),
      delivery_success: false,
      site_state: "delivery_material_draft_not_operator_confirmed",
    },
  };
  let draftSaved = false;
  try {
    operatorReportResult.value = await postRobotControlOperatorReport(robotApiBaseUrl.value, reportBody);
    draftSaved = operatorReportResult.value.proxy_status === "report_forwarded" && operatorReportResult.value.status !== "blocked";
  } catch (err) {
    operatorReportResult.value = makeOperatorReportFallback(err instanceof Error ? err.message : "delivery_draft_report_request_failed", reportBody);
  } finally {
    operatorReportPending.value = false;
  }
  if (draftSaved) {
    await checkDeliveryGap();
    await nextTick();
    plainDeliveryFinalPanel.value?.focus();
  } else {
    await loadDeliveryLatest();
    await refreshConsole();
  }
}

async function submitDeliveryOperatorReportAndComplete(): Promise<void> {
  // 这个快捷入口只帮现场人员把“送达确认材料”写进 operator report，再交给 delivery gate 合成结论。
  if (
    !robotApiBaseUrl.value.trim()
    || operatorReportPending.value
    || deliveryCompletionPending.value
    || !deliveryOperatorConfirmationReady.value
    || !deliveryOperatorVideoRef.value.trim()
    || !deliveryOperatorRouteMapRef.value.trim()
  ) {
    return;
  }
  operatorReportPending.value = true;
  deliveryCompletionPending.value = true;
  const evidenceRef = deliveryOperatorEvidenceRef.value.trim() || `delivery-operator-${Date.now()}`;
  const confirmations = deliveryOperatorConfirmations.value;
  const inheritedProgressClaims = inheritedProgressClaimsFromSummary();
  const reportBody: RobotControlOperatorReportRequest = {
    operator_present: confirmations.operator_present,
    evidence_ref: evidenceRef,
    physical_clearance_confirmed: confirmations.physical_clearance_confirmed,
    emergency_stop_ready: confirmations.emergency_stop_ready,
    observed_motion: confirmations.observed_motion,
    observed_stop: confirmations.observed_stop,
    reported_at: new Date().toISOString(),
    operator_notes: "PC delivery closure shortcut; operator explicitly confirmed delivery, route/map evidence, and visual material.",
    structured_hil_claims: {
      external_video_recorded: true,
      external_video_ref: deliveryOperatorVideoRef.value.trim(),
      visible_content_proven: true,
      camera_artifacts_ref: deliveryOperatorVideoRef.value.trim(),
      ...inheritedProgressClaims,
      real_route_map_proven: confirmations.route_video_refs_verified,
      route_map_ref: deliveryOperatorRouteMapRef.value.trim(),
      delivery_success: confirmations.delivery_success,
      site_state: "operator_confirmed_delivery_complete",
    },
  };
  try {
    operatorReportResult.value = await postRobotControlOperatorReport(robotApiBaseUrl.value, reportBody);
    if (operatorReportResult.value.proxy_status === "report_forwarded" && operatorReportResult.value.status !== "blocked") {
      deliveryCompletionResult.value = await postRobotControlDeliveryComplete(robotApiBaseUrl.value, {
        confirm_delivery_completion: true,
        delivery_evidence_ref: deliveryEvidenceRef.value.trim() || evidenceRef,
        operator_notes: "PC delivery closure shortcut after operator report material submit.",
      });
    }
  } catch (err) {
    operatorReportResult.value = makeOperatorReportFallback(err instanceof Error ? err.message : "delivery_operator_report_request_failed", reportBody);
    deliveryCompletionResult.value = makeDeliveryCompletionFallback(err instanceof Error ? err.message : "delivery_operator_report_request_failed");
  } finally {
    operatorReportPending.value = false;
    deliveryCompletionPending.value = false;
    await loadDeliveryLatest();
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
  // 普通按钮只走固定 /api/map/start，不接受浏览器传运动、串口或 ROS 参数。
  await runMapLifecycleAction("start", () => postRobotControlMapStart(robotApiBaseUrl.value, mapLifecycleRequestBody()));
}

async function saveMap(): Promise<void> {
  // 保存只调用固定 /api/map/save；普通入口不暴露 map_name/artifact_path 输入。
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

async function submitPlainMotionPrecheck(): Promise<void> {
  // 普通首屏只提交基础现场确认，不伪造视频、轮速或 LiDAR motion delta 材料。
  if (!robotApiBaseUrl.value.trim() || plainMotionPrecheckPending.value || operatorReportPending.value) {
    return;
  }
  const requestBody = plainMotionPrecheckRequestBody();
  plainMotionPrecheckPending.value = true;
  localizationResetResult.value = null;
  try {
    plainMotionPrecheckResult.value = await postRobotControlOperatorReport(robotApiBaseUrl.value, requestBody);
  } catch (err) {
    plainMotionPrecheckResult.value = makeOperatorReportFallback(err instanceof Error ? err.message : "plain_motion_precheck_failed", requestBody);
  } finally {
    operatorReportResult.value = plainMotionPrecheckResult.value;
    plainMotionPrecheckPending.value = false;
    await refreshConsole();
  }
}

async function submitPlainVisualMaterial(): Promise<void> {
  // 记录画面只更新 operator report；没有填写视频索引时不提交，避免制造空 ref。
  if (!robotApiBaseUrl.value.trim() || plainVisualMaterialPending.value || operatorReportPending.value || !plainExternalVideoRef.value.trim()) {
    return;
  }
  const requestBody = plainVisualMaterialRequestBody();
  plainVisualMaterialPending.value = true;
  localizationResetResult.value = null;
  plainFirstJogResult.value = null;
  try {
    plainVisualMaterialResult.value = await postRobotControlOperatorReport(robotApiBaseUrl.value, requestBody);
  } catch (err) {
    plainVisualMaterialResult.value = makeOperatorReportFallback(err instanceof Error ? err.message : "plain_visual_material_failed", requestBody);
  } finally {
    operatorReportResult.value = plainVisualMaterialResult.value;
    plainVisualMaterialPending.value = false;
    await refreshConsole();
  }
}

async function restorePlainFirstJogMaterial(): Promise<void> {
  // 送达草稿会覆盖 latest report；恢复按钮只补 first-jog 前置材料，不发送任何运动命令。
  if (!robotApiBaseUrl.value.trim() || plainFirstJogMaterialRestorePending.value || operatorReportPending.value || !firstJogMaterialRestoreReady.value) {
    return;
  }
  const requestBody = plainFirstJogMaterialRestoreRequestBody();
  plainFirstJogMaterialRestorePending.value = true;
  plainFirstJogResult.value = null;
  try {
    plainFirstJogMaterialRestoreResult.value = await postRobotControlOperatorReport(robotApiBaseUrl.value, requestBody);
  } catch (err) {
    plainFirstJogMaterialRestoreResult.value = makeOperatorReportFallback(err instanceof Error ? err.message : "plain_first_jog_material_restore_failed", requestBody);
  } finally {
    operatorReportResult.value = plainFirstJogMaterialRestoreResult.value;
    plainFirstJogMaterialRestorePending.value = false;
    await refreshConsole();
  }
}

async function sendPlainFirstJog(): Promise<void> {
  // 试动按钮只调用 first-jog 固定代理；后端 preflight 不通过时不会调用远端 manual。
  if (!canSendPlainFirstJog.value) {
    return;
  }
  manualCommandPending.value = true;
  localizationResetResult.value = null;
  try {
    plainFirstJogResult.value = await postRobotControlBaseFirstJog(robotApiBaseUrl.value, plainFirstJogRequestBody());
  } catch (err) {
    plainFirstJogResult.value = {
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
      requested_direction: "forward",
      applied_direction: "forward",
      requested_speed_mps: 0.08,
      clamped_speed_mps: 0.08,
      requested_duration_ms: 500,
      clamped_duration_ms: 500,
      confirm_hil_checklist: true,
      non_stop_requires_confirm_hil_checklist: true,
      hil_checklist_gate_status: "manual_allowed",
      checklist_missing: [],
      operator_report_preflight: commandOperatorReportPreflightFallback("manual", err instanceof Error ? err.message : "first_jog_request_failed"),
      request_contract: {
        max_speed_mps: manualSpeedLimit.value,
        max_duration_ms: manualDurationLimit.value,
        allowed_directions: manualBoundary.value?.allowed_directions ?? ["forward", "back", "left", "right", "stop"],
      },
      ...commandEvidenceFallback("manual", err instanceof Error ? err.message : "first_jog_request_failed"),
      failure_reason: err instanceof Error ? err.message : "first_jog_request_failed",
      blocked_reasons: [err instanceof Error ? err.message : "first_jog_request_failed"],
      hard_dangerous_true_fields: [],
    };
  } finally {
    manualCommandResult.value = plainFirstJogResult.value;
    manualCommandPending.value = false;
    await runBaseFeedbackSamples({ refreshAfter: false });
    await refreshConsole();
  }
}

async function savePlainWheelEvidence(): Promise<void> {
  // 保存轮速材料只写 operator report；不补 LiDAR/route/delivery，也不再次发送运动命令。
  if (!robotApiBaseUrl.value.trim() || plainWheelEvidenceSavePending.value || operatorReportPending.value || !plainFirstJogWheelEvidenceReady.value) {
    return;
  }
  const requestBody = plainWheelEvidenceReportRequestBody();
  plainWheelEvidenceSavePending.value = true;
  try {
    plainWheelEvidenceSaveResult.value = await postRobotControlOperatorReport(robotApiBaseUrl.value, requestBody);
  } catch (err) {
    plainWheelEvidenceSaveResult.value = makeOperatorReportFallback(err instanceof Error ? err.message : "plain_wheel_evidence_save_failed", requestBody);
  } finally {
    operatorReportResult.value = plainWheelEvidenceSaveResult.value;
    plainWheelEvidenceSavePending.value = false;
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

async function runBaseFeedbackSamples(options: { refreshAfter?: boolean } = {}): Promise<void> {
  // 反馈样本采集只走固定 T=130 只读代理，不发送方向、速度或 stop/manual 命令。
  if (!robotApiBaseUrl.value.trim() || baseFeedbackSamplesPending.value) {
    return;
  }
  baseFeedbackSamplesPending.value = true;
  try {
    baseFeedbackSamplesResult.value = await postRobotControlBaseFeedbackSamples(robotApiBaseUrl.value);
  } catch (err) {
    baseFeedbackSamplesResult.value = makeBaseFeedbackSamplesFallback(
      err instanceof Error ? err.message : "base_feedback_samples_request_failed",
    );
  } finally {
    baseFeedbackSamplesPending.value = false;
    if (options.refreshAfter ?? true) {
      await refreshConsole();
    }
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

    await runBaseFeedbackSamples();
    appendEvidenceSweepLine("base_feedback", baseFeedbackSamplesResult.value?.status ?? "not_loaded");

    await sendStop();
    appendEvidenceSweepLine("stop", manualCommandResult.value?.status ?? "not_loaded");
  } catch (err) {
    appendEvidenceSweepLine("error", err instanceof Error ? err.message : "evidence_sweep_failed");
  } finally {
    evidenceSweepCompletedAt.value = stampNow();
    evidenceSweepPending.value = false;
  }
}

async function sendManualMotion(direction: ManualDirection): Promise<void> {
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

async function sendKeyboardManualPulse(direction: ManualDirection): Promise<void> {
  // 连续键盘脉冲复用同一个后端 manual 代理；不新增浏览器直连或 /cmd_vel 通道。
  if (!canSendManualMotion.value || keyboardJogInFlight || keyboardHeldDirection.value !== direction) {
    return;
  }
  keyboardJogInFlight = true;
  keyboardControlStatus.value = "sending_keyboard_pulse";
  try {
    manualCommandPending.value = true;
    manualCommandResult.value = await postRobotControlBaseManual(robotApiBaseUrl.value, requestBodyForKeyboardDirection(direction));
    if (keyboardHeldDirection.value === direction) {
      keyboardControlStatus.value = "holding_keyboard_jog";
    }
  } catch (err) {
    keyboardControlStatus.value = `blocked_keyboard_pulse_failed:${err instanceof Error ? err.message : "keyboard_manual_request_failed"}`;
  } finally {
    manualCommandPending.value = false;
    keyboardJogInFlight = false;
    await refreshConsole();
  }
}

function keyboardDirectionFromKey(key: string): ManualDirection | null {
  // 支持 WASD 和方向键，避免普通键盘没有小键盘时无法现场操作。
  const normalizedKey = key.toLowerCase();
  if (normalizedKey === "w" || key === "ArrowUp") {
    return "forward";
  }
  if (normalizedKey === "s" || key === "ArrowDown") {
    return "back";
  }
  if (normalizedKey === "a" || key === "ArrowLeft") {
    return "left";
  }
  if (normalizedKey === "d" || key === "ArrowRight") {
    return "right";
  }
  return null;
}

function eventTargetIsEditable(target: EventTarget | null): boolean {
  // 输入框内按 WASD 必须继续输入文本，不能被全局手控快捷键抢走。
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  const tagName = target.tagName.toLowerCase();
  return target.isContentEditable || tagName === "input" || tagName === "textarea" || tagName === "select";
}

function eventTargetIsKeyboardControlScope(target: EventTarget | null): boolean {
  // 连续手控必须发生在明确聚焦的键盘面板里，避免普通页面快捷键误触底盘。
  const panel = keyboardControlPanel.value;
  return Boolean(panel && target instanceof Node && panel.contains(target));
}

function activateKeyboardControl(): void {
  // 现场 operator 需要先显式进入键盘面板；页面其他区域按键不触发手控。
  keyboardControlArmed.value = true;
  keyboardControlStatus.value = canSendManualMotion.value ? "armed_waiting_for_key" : `blocked_keyboard_manual_gate:${manualBlockedReason.value}`;
  keyboardControlPanel.value?.focus();
}

function disarmKeyboardControl(reason: string): void {
  // 面板失焦或页面失焦时退出 armed 状态；如果正在运动，先通过统一 stop 路径收口。
  keyboardControlArmed.value = false;
  if (keyboardHeldDirection.value) {
    stopKeyboardControl(reason);
    return;
  }
  clearKeyboardJogTimer();
  keyboardLastStopReason.value = reason;
  keyboardControlStatus.value = `disarmed:${reason}`;
}

function clearKeyboardJogTimer(): void {
  // 全局 timer 必须集中清理，防止组件卸载或地址切换后仍重复发点动。
  if (keyboardJogTimer !== null) {
    window.clearInterval(keyboardJogTimer);
    keyboardJogTimer = null;
  }
}

function stopKeyboardControl(reason: string): void {
  // 只有真实进入过按住态才发送 stop；普通误按 blocked 时不制造额外请求。
  const shouldSendStop = keyboardHeldDirection.value !== null || keyboardJogTimer !== null;
  clearKeyboardJogTimer();
  keyboardHeldDirection.value = null;
  keyboardLastStopReason.value = reason;
  keyboardControlStatus.value = `released:${reason}`;
  if (shouldSendStop && canSendStop.value) {
    void sendStop().then(() => {
      keyboardControlStatus.value = `stop_sent:${reason}`;
    });
  }
}

function startKeyboardControl(direction: ManualDirection): void {
  // 切换方向时先收掉旧循环，并让下一次短脉冲按新方向进入后端 preflight。
  if (!keyboardControlArmed.value) {
    keyboardControlStatus.value = "blocked_keyboard_not_armed";
    return;
  }
  if (!canSendManualMotion.value) {
    keyboardControlStatus.value = `blocked_keyboard_manual_gate:${manualBlockedReason.value}`;
    return;
  }
  clearKeyboardJogTimer();
  keyboardHeldDirection.value = direction;
  keyboardLastDirection.value = direction;
  keyboardControlStatus.value = "holding_keyboard_jog";
  void sendKeyboardManualPulse(direction);
  keyboardJogTimer = window.setInterval(() => {
    void sendKeyboardManualPulse(direction);
  }, keyboardJogIntervalMs.value);
}

function handleGlobalKeyDown(event: KeyboardEvent): void {
  // 长按产生的 repeat 事件由 timer 接管，避免浏览器 repeat 频率影响底盘命令节奏。
  const direction = keyboardDirectionFromKey(event.key);
  if (!direction || eventTargetIsEditable(event.target) || !keyboardControlArmed.value || !eventTargetIsKeyboardControlScope(event.target)) {
    return;
  }
  event.preventDefault();
  if (keyboardHeldDirection.value === direction) {
    return;
  }
  if (keyboardHeldDirection.value) {
    stopKeyboardControl("direction_changed");
  }
  startKeyboardControl(direction);
}

function handleGlobalKeyUp(event: KeyboardEvent): void {
  // 松开当前方向键即停；松开非当前方向键不影响正在按住的方向。
  const direction = keyboardDirectionFromKey(event.key);
  if (!direction || !keyboardControlArmed.value || !eventTargetIsKeyboardControlScope(event.target) || keyboardHeldDirection.value !== direction) {
    return;
  }
  event.preventDefault();
  stopKeyboardControl("key_released");
}

function handleKeyboardControlFocusOut(event: FocusEvent): void {
  // 焦点离开键盘面板就退出手控窗口，防止 operator 去填表时旧按键状态继续有效。
  const nextTarget = event.relatedTarget;
  if (nextTarget instanceof Node && keyboardControlPanel.value?.contains(nextTarget)) {
    return;
  }
  disarmKeyboardControl("focus_lost");
}

function handlePageVisibilityChange(): void {
  // 页面隐藏时 operator 不再能观察现场，必须立即退出连续手控。
  if (document.hidden && (keyboardControlArmed.value || keyboardHeldDirection.value)) {
    disarmKeyboardControl("page_hidden");
  }
}

function handleWindowBlur(): void {
  // 窗口失焦时按键释放事件可能丢失，所以主动发送 stop 收口。
  if (keyboardControlArmed.value || keyboardHeldDirection.value) {
    disarmKeyboardControl("window_blur");
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
  if (keyboardHeldDirection.value) {
    stopKeyboardControl("base_url_changed");
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
  // 初次加载直接读取固定上位机地址的摘要；控制动作仍需要显式点击或按键。
  window.addEventListener("keydown", handleGlobalKeyDown);
  window.addEventListener("keyup", handleGlobalKeyUp);
  window.addEventListener("blur", handleWindowBlur);
  document.addEventListener("visibilitychange", handlePageVisibilityChange);
  void refreshConsole().then(() => preloadGoalClosureReadbacks());
});

onBeforeUnmount(() => {
  // 卸载时先退出键盘循环，再释放视频资源；远端 cleanup 尽量执行但不能阻塞组件销毁。
  clearKeyboardJogTimer();
  window.removeEventListener("keydown", handleGlobalKeyDown);
  window.removeEventListener("keyup", handleGlobalKeyUp);
  window.removeEventListener("blur", handleWindowBlur);
  document.removeEventListener("visibilitychange", handlePageVisibilityChange);
  void cleanupPreview("stopped_by_user", "component_unmounted");
});
</script>

<template>
  <section class="workspace robot-console">
    <div class="simple-user-console" data-testid="pc-simple-user-first-screen">
      <form class="robot-quick-connect" @submit.prevent="refreshConsole">
        <label>
          <span>小车地址</span>
          <input v-model="robotApiBaseUrl" name="robotApiBaseUrl" placeholder="http://192.168.1.11:8787">
        </label>
        <button class="secondary compact-stop" type="button" :disabled="loading || robotApiBaseUrlUsesDefault" data-testid="robot-api-default" @click="resetRobotApiBaseUrlToDefault">默认地址</button>
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
            <button type="button" :disabled="loading || mapLifecyclePending || !robotApiBaseUrl.trim()" @click="startMapRuntime">
              重新建图
            </button>
            <button type="button" :disabled="loading || mapLifecyclePending || !robotApiBaseUrl.trim()" @click="saveMap">
              保存地图
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
            <button type="button" :disabled="loading || localizationResetPending || !robotApiBaseUrl.trim()" @click="resetLocalizationProof">
              重新定位
            </button>
            <button type="button" :disabled="loading || plainMotionPrecheckPending || operatorReportPending || !robotApiBaseUrl.trim()" @click="submitPlainMotionPrecheck">
              移动前检查
            </button>
            <label class="plain-video-ref">
              <span>现场画面记录</span>
              <input v-model="plainExternalVideoRef" name="plainExternalVideoRef" placeholder="手机视频编号">
            </label>
            <button type="button" :disabled="loading || plainVisualMaterialPending || operatorReportPending || !robotApiBaseUrl.trim() || !plainExternalVideoRef.trim()" @click="submitPlainVisualMaterial">
              记录画面
            </button>
            <button type="button" :disabled="!canSendPlainFirstJog" @click="sendPlainFirstJog">
              试动一下
            </button>
            <button type="button" class="danger-button compact-stop" :disabled="!canSendStop" @click="sendStop">停止</button>
          </div>
          <div
            ref="keyboardControlPanel"
            class="keyboard-control-box plain-keyboard-control"
            tabindex="0"
            data-testid="keyboard-control-panel"
            @keydown="handleGlobalKeyDown"
            @keyup="handleGlobalKeyUp"
            @focusout="handleKeyboardControlFocusOut"
          >
            <div class="simple-status-row">
              <span class="status-chip" :data-state="plainKeyboardControlSummary.state">{{ plainKeyboardControlSummary.state }}</span>
              <span class="plain-keyboard-direction" data-testid="keyboard-current-direction">当前方向：{{ keyboardDirectionPlainLabel }}</span>
              <button class="secondary compact-stop" type="button" :disabled="plainGoalProgressPending || !robotApiBaseUrl.trim()" data-testid="keyboard-control-recheck" @click="refreshPlainGoalProgress">{{ plainKeyboardRecheckButtonLabel }}</button>
              <button class="secondary compact-stop" type="button" :disabled="!canArmKeyboardControl" data-testid="keyboard-control-arm" @click="activateKeyboardControl">{{ plainKeyboardArmButtonLabel }}</button>
              <button class="danger-button compact-stop" type="button" :disabled="!canSendStop" data-testid="keyboard-control-stop" @click="stopKeyboardControl('button_stop')">键盘停止（随时可点）</button>
            </div>
            <p class="panel-note">{{ plainKeyboardControlSummary.hint }}</p>
            <p v-if="plainKeyboardNextActionSummary" class="panel-note" data-testid="plain-keyboard-next-action">
              {{ plainKeyboardNextActionSummary }}
            </p>
            <p class="panel-note">W/A/S/D 或方向键：前进、左转、后退、右转。</p>
          </div>
          <p class="panel-note">{{ plainMotionSummary.hint }}</p>
          <div class="plain-goal-progress" data-testid="plain-goal-progress">
            <div class="simple-status-row">
              <strong>本轮进度</strong>
              <button type="button" class="secondary compact-stop" :disabled="plainGoalProgressPending" data-testid="plain-goal-progress-refresh" @click="refreshPlainGoalProgress">
                {{ plainGoalProgressRefreshButtonLabel }}
              </button>
            </div>
            <p class="panel-note" data-testid="plain-goal-progress-next-action">{{ plainGoalProgressNextAction }}</p>
            <div v-for="item in plainGoalProgressItems" :key="item.id" class="plain-progress-row">
              <span class="plain-progress-label">{{ item.label }}</span>
              <span class="status-chip" :data-state="item.state">{{ item.state }}</span>
              <span class="muted">{{ item.hint }}</span>
              <button type="button" class="secondary compact-stop" :data-testid="`plain-goal-progress-go-${item.id}`" @click="focusPlainGoalProgressTarget(item.id)">
                {{ item.actionLabel }}
              </button>
            </div>
          </div>
          <div ref="plainTripRunPanel" class="plain-trip-run" tabindex="-1" data-testid="plain-trip-run">
            <div class="simple-status-row">
              <strong>行程操作</strong>
              <span class="status-chip" :data-state="plainTripSummary.state">{{ plainTripSummary.state }}</span>
            </div>
            <label class="plain-trip-confirm">
              <input v-model="plainTripSafetyConfirmed" name="plainTripSafetyConfirmed" type="checkbox">
              <span>人在旁边、周围安全、停止手段就绪</span>
            </label>
            <div class="simple-status-row">
              <button type="button" class="secondary compact-stop" :disabled="!canRunPlainTripPreflight" data-testid="plain-trip-preflight" @click="runPlainTripPreflight">
                {{ plainTripPreflightButtonLabel }}
              </button>
              <button type="button" class="danger-button compact-stop" :disabled="!canRunPlainTripExecution" data-testid="plain-trip-execute" @click="runPlainTripExecution">
                {{ plainTripExecutionButtonLabel }}
              </button>
              <button type="button" class="secondary compact-stop" :disabled="loading || navGoalExecutionLatestPending || !robotApiBaseUrl.trim()" data-testid="plain-trip-latest" @click="loadNavGoalExecutionLatest">
                {{ plainTripLatestButtonLabel }}
              </button>
            </div>
            <p class="panel-note">{{ plainTripSummary.hint }}</p>
            <p v-if="plainTripEvidenceSummary" class="panel-note" data-testid="plain-trip-evidence-summary">
              {{ plainTripEvidenceSummary }}
            </p>
          </div>
          <p v-if="plainFirstJogBlockedHint" class="panel-note">{{ plainFirstJogBlockedHint }}</p>
          <p v-if="plainFirstJogEvidenceSummary" class="panel-note">{{ plainFirstJogEvidenceSummary }}</p>
          <div ref="plainWheelRecordPanel" class="plain-wheel-record" tabindex="-1" data-testid="plain-wheel-record">
            <div class="simple-status-row">
              <strong>轮速记录</strong>
              <span class="status-chip" :data-state="plainWheelRecordSummary.state">{{ plainWheelRecordSummary.state }}</span>
              <button type="button" class="secondary compact-stop" :disabled="loading || plainFirstJogMaterialRestorePending || operatorReportPending || !robotApiBaseUrl.trim() || !firstJogMaterialRestoreReady" @click="restorePlainFirstJogMaterial">
                恢复试动确认
              </button>
              <button type="button" class="secondary compact-stop" :disabled="!canSendPlainFirstJog" data-testid="plain-wheel-trial" @click="sendPlainFirstJog">
                {{ plainWheelTrialButtonLabel }}
              </button>
              <button type="button" class="secondary compact-stop" :disabled="loading || baseFeedbackSamplesPending || !robotApiBaseUrl.trim()" data-testid="plain-wheel-readback-refresh" @click="runBaseFeedbackSamples">
                {{ plainWheelReadbackButtonLabel }}
              </button>
              <button type="button" class="secondary compact-stop" :disabled="loading || plainWheelEvidenceSavePending || operatorReportPending || !robotApiBaseUrl.trim() || !plainFirstJogWheelEvidenceReady" data-testid="plain-wheel-save" @click="savePlainWheelEvidence">
                {{ plainWheelEvidenceSaveButtonLabel }}
              </button>
            </div>
            <p class="panel-note">{{ plainWheelRecordSummary.hint }}</p>
            <p v-if="plainWheelReadbackSummary" class="panel-note" data-testid="plain-wheel-readback-summary">
              {{ plainWheelReadbackSummary }}
            </p>
            <p v-if="plainWheelNextActionSummary" class="panel-note" data-testid="plain-wheel-next-action">
              {{ plainWheelNextActionSummary }}
            </p>
            <p v-if="plainLidarMotionRecordSummary" class="panel-note" data-testid="plain-lidar-motion-record-summary">
              {{ plainLidarMotionRecordSummary }}
            </p>
            <p v-if="plainWheelEvidenceSaveSummary" class="panel-note">{{ plainWheelEvidenceSaveSummary }}</p>
          </div>
          <div ref="plainDeliveryStatusPanel" class="plain-delivery-status" tabindex="-1" data-testid="plain-delivery-status">
            <div class="simple-status-row">
              <strong>任务收口</strong>
              <span class="status-chip" :data-state="plainDeliverySummary.state">{{ plainDeliverySummary.state }}</span>
              <button type="button" class="secondary compact-stop" :disabled="loading || deliveryLatestPending || !robotApiBaseUrl.trim()" data-testid="plain-delivery-latest" @click="loadDeliveryLatest">
                {{ plainDeliveryLatestButtonLabel }}
              </button>
              <button type="button" class="secondary compact-stop" :disabled="loading || deliveryGapCheckPending || !robotApiBaseUrl.trim()" data-testid="plain-delivery-gap-check" @click="checkDeliveryGap">
                {{ plainDeliveryGapCheckButtonLabel }}
              </button>
            </div>
            <p class="panel-note">{{ plainDeliverySummary.hint }}</p>
            <p v-if="plainDeliveryGateMissingSummary" class="panel-note" data-testid="plain-delivery-gate-missing">
              {{ plainDeliveryGateMissingSummary }}
            </p>
            <p v-if="plainDeliveryNextActionSummary" class="panel-note" data-testid="plain-delivery-next-action">
              {{ plainDeliveryNextActionSummary }}
            </p>
            <div class="simple-status-row plain-delivery-material-row">
              <span class="status-chip" :data-state="plainDeliveryMaterialSummary.state">{{ plainDeliveryMaterialSummary.state }}</span>
              <button
                type="button"
                class="secondary compact-stop"
                :disabled="loading || navGoalExecutionLatestPending || cameraFirstFrameProbePending || deliveryLatestPending || !robotApiBaseUrl.trim()"
                @click="prefillDeliveryMaterialRefs"
              >
                准备送达材料
              </button>
              <button
                type="button"
                class="secondary compact-stop"
                :disabled="loading || operatorReportPending || !robotApiBaseUrl.trim() || !deliveryOperatorVideoRef.trim() || !deliveryOperatorRouteMapRef.trim()"
                data-testid="plain-delivery-draft-save"
                @click="submitDeliveryDraftMaterial"
              >
                {{ plainDeliveryDraftSaveButtonLabel }}
              </button>
            </div>
            <p class="panel-note">{{ plainDeliveryMaterialSummary.hint }}</p>
            <div ref="plainDeliveryFinalPanel" class="plain-delivery-final" tabindex="-1" data-testid="plain-delivery-final-confirm">
              <div class="simple-status-row">
                <strong>最终确认</strong>
                <span class="status-chip" :data-state="plainDeliveryConfirmSummary.state">{{ plainDeliveryConfirmSummary.state }}</span>
                <button type="button" class="secondary compact-stop" data-testid="plain-delivery-mark-safety" @click="markDeliveryBasicSafetyConfirmed">
                  {{ plainDeliverySafetyButtonLabel }}
                </button>
                <button type="button" class="secondary compact-stop" data-testid="plain-delivery-mark-arrived-stopped" @click="markDeliveryArrivedAndStopped">
                  {{ plainDeliveryArrivedStoppedButtonLabel }}
                </button>
                <button type="button" class="secondary compact-stop" data-testid="plain-delivery-mark-refs-verified" @click="markDeliveryRefsVerified">
                  {{ plainDeliveryRefsVerifiedButtonLabel }}
                </button>
                <button type="button" class="secondary compact-stop" data-testid="plain-delivery-mark-success" @click="markDeliverySuccessConfirmed">
                  {{ plainDeliverySuccessButtonLabel }}
                </button>
              </div>
              <p class="panel-note">{{ plainDeliveryConfirmSummary.hint }}</p>
              <p v-if="plainDeliveryConfirmMissingSummary" class="panel-note" data-testid="plain-delivery-confirm-missing">
                {{ plainDeliveryConfirmMissingSummary }}
              </p>
              <div class="plain-confirm-grid">
                <label>
                  <input v-model="deliveryOperatorConfirmations.operator_present" name="deliveryOperatorConfirmOperatorPresent" type="checkbox">
                  <span>人在旁边可接管</span>
                </label>
                <label>
                  <input v-model="deliveryOperatorConfirmations.physical_clearance_confirmed" name="deliveryOperatorConfirmClearance" type="checkbox">
                  <span>周围安全</span>
                </label>
                <label>
                  <input v-model="deliveryOperatorConfirmations.emergency_stop_ready" name="deliveryOperatorConfirmEstop" type="checkbox">
                  <span>停止手段就绪</span>
                </label>
                <label>
                  <input v-model="deliveryOperatorConfirmations.observed_motion" name="deliveryOperatorConfirmObservedMotion" type="checkbox">
                  <span>已观察到到达/移动</span>
                </label>
                <label>
                  <input v-model="deliveryOperatorConfirmations.observed_stop" name="deliveryOperatorConfirmObservedStop" type="checkbox">
                  <span>已观察到停止</span>
                </label>
                <label>
                  <input v-model="deliveryOperatorConfirmations.route_video_refs_verified" name="deliveryOperatorConfirmRefsVerified" type="checkbox">
                  <span>视频和行程材料已核对</span>
                </label>
                <label>
                  <input v-model="deliveryOperatorConfirmations.delivery_success" name="deliveryOperatorConfirmDeliverySuccess" type="checkbox">
                  <span>确认已投放/送达</span>
                </label>
              </div>
              <button
                type="button"
                class="danger-button compact-stop"
                :disabled="!plainDeliveryConfirmReady"
                data-testid="plain-delivery-confirm-submit"
                @click="submitDeliveryOperatorReportAndComplete"
              >
                {{ plainDeliveryConfirmButtonLabel }}
              </button>
            </div>
          </div>
        </article>
      </div>
    </div>

    <details class="advanced-details">
      <summary>高级诊断</summary>
      <div class="advanced-grid">
        <section class="advanced-block">
          <h3>目标收口进度</h3>
          <p class="panel-note">只汇总当前已读证据；不会自动发车、提交送达或提升 success。</p>
          <ul class="compact-list" data-testid="goal-closure-checklist">
            <li v-for="item in goalClosureChecklist" :key="item.id" :data-ready="item.ready">
              <span>{{ item.ready ? "已满足" : "未满足" }}：{{ item.label }}</span>
              <small>{{ item.hint }}</small>
            </li>
          </ul>
        </section>
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
            <dt>probe_backends</dt>
            <dd>
              status={{ cameraFirstFrameProbeResult?.probe_key_values.backend_smoke_status ?? "not_requested" }},
              frame={{ cameraFirstFrameProbeResult?.probe_key_values.backend_frame_observed ?? "false" }},
              attempts={{ cameraFirstFrameProbeResult?.probe_key_values.backend_attempts ?? "0" }}
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
            <dt>camera_source_readiness</dt>
            <dd>{{ robotSummary?.readback_summary.camera.source_readiness ?? "not_loaded" }}</dd>
            <dt>camera_source_failure_reason</dt>
            <dd>{{ robotSummary?.readback_summary.camera.source_failure_reason ?? "none" }}</dd>
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
            <dt>map quality</dt>
            <dd>
              status={{ mapLifecycleResult?.map_quality_summary.status ?? "not_loaded" }},
              usable={{ mapLifecycleResult?.map_quality_summary.usable_map_count ?? 0 }},
              no_free={{ mapLifecycleResult?.map_quality_summary.no_free_cell_map_count ?? 0 }}
            </dd>
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
          <form class="robot-control-form" @submit.prevent="runNavGoalExecution">
            <label>
              <span>执行等待（s）</span>
              <input v-model.number="navGoalExecutionTimeoutS" name="navGoalExecutionTimeoutS" type="number" min="2" max="20" step="1">
            </label>
            <label class="checkbox-inline">
              <input v-model="confirmNavigationExecution" name="confirmNavigationExecution" type="checkbox">
              <span>确认执行一次受限导航目标</span>
            </label>
            <button class="danger-button" type="submit" :disabled="loading || navGoalExecutionPending || !robotApiBaseUrl.trim() || !confirmNavigationExecution">
              执行导航目标（高级）
            </button>
          </form>
          <div class="robot-control-form">
            <button class="secondary" type="button" :disabled="loading || navGoalExecutionLatestPending || !robotApiBaseUrl.trim()" @click="loadNavGoalExecutionLatest">
              读取最近 Nav2 结果（高级）
            </button>
            <button class="secondary" type="button" :disabled="loading || deliveryLatestPending || !robotApiBaseUrl.trim()" @click="loadDeliveryLatest">
              读取送达缺口（高级）
            </button>
            <button class="secondary" type="button" :disabled="loading || deliveryGapCheckPending || !robotApiBaseUrl.trim()" @click="checkDeliveryGap">
              复算送达缺口（高级）
            </button>
          </div>
          <form class="robot-control-form" @submit.prevent="completeDelivery">
            <label>
              <span>送达证据 ref</span>
              <input v-model="deliveryEvidenceRef" name="deliveryEvidenceRef" placeholder="delivery-confirmation-...">
            </label>
            <label class="checkbox-inline">
              <input v-model="confirmDeliveryCompletion" name="confirmDeliveryCompletion" type="checkbox">
              <span>确认最近 Nav2 成功且现场报告已确认送达</span>
            </label>
            <button class="danger-button" type="submit" :disabled="loading || deliveryCompletionPending || !robotApiBaseUrl.trim() || !confirmDeliveryCompletion">
              确认送达（高级）
            </button>
          </form>
          <form class="robot-control-form" @submit.prevent="submitDeliveryOperatorReportAndComplete">
            <button
              class="secondary"
              type="button"
              :disabled="loading || navGoalExecutionLatestPending || cameraFirstFrameProbePending || deliveryLatestPending || !robotApiBaseUrl.trim()"
              @click="prefillDeliveryMaterialRefs"
            >
              预填送达材料（高级）
            </button>
            <label>
              <span>operator evidence ref</span>
              <input v-model="deliveryOperatorEvidenceRef" name="deliveryOperatorEvidenceRef" maxlength="512" placeholder="delivery-operator-...">
            </label>
            <label>
              <span>送达视频 ref</span>
              <input v-model="deliveryOperatorVideoRef" name="deliveryOperatorVideoRef" maxlength="512" placeholder="phone-video-or-camera-artifact-ref">
            </label>
            <button class="secondary" type="button" :disabled="loading || cameraFirstFrameProbePending || !robotApiBaseUrl.trim()" @click="fillDeliveryVideoRefFromCameraProbe">
              使用最近画面 ref
            </button>
            <label>
              <span>route/map ref</span>
              <input v-model="deliveryOperatorRouteMapRef" name="deliveryOperatorRouteMapRef" maxlength="512" placeholder="o11-nav2-goal-execution-...">
            </label>
            <button class="secondary" type="button" :disabled="!(navGoalExecutionResult?.goal_execution_key_values.evidence_ref || navGoalExecutionLatestResult?.goal_execution_key_values.evidence_ref)" @click="fillDeliveryRouteRefFromLatestNav2">
              使用最近 Nav2 ref
            </button>
            <button class="secondary" type="button" :disabled="loading || operatorReportPending || !robotApiBaseUrl.trim() || !deliveryOperatorVideoRef.trim() || !deliveryOperatorRouteMapRef.trim()" @click="submitDeliveryDraftMaterial">
              提交送达草稿（高级）
            </button>
            <div class="delivery-closure-check" data-testid="delivery-closure-check">
              <p class="checklist-title">送达收口检查</p>
              <p v-if="deliveryGateBlockedReasons.length" class="panel-note">
                当前 gate 缺项：{{ deliveryGateBlockedReasons.join("、") }}
              </p>
              <ul class="compact-list">
                <li v-for="item in deliveryClosureChecklist" :key="item.id" :data-ready="item.ready">
                  <span>{{ item.ready ? "已满足" : "未满足" }}：{{ item.label }}</span>
                  <small>{{ item.hint }}</small>
                </li>
              </ul>
            </div>
            <div class="checklist-box compact-checklist">
              <p class="checklist-title">送达最终确认</p>
              <label class="checklist-item">
                <input v-model="deliveryOperatorConfirmations.operator_present" name="deliveryOperatorConfirmOperatorPresent" type="checkbox">
                <span>现场有人确认并可接管</span>
              </label>
              <label class="checklist-item">
                <input v-model="deliveryOperatorConfirmations.physical_clearance_confirmed" name="deliveryOperatorConfirmClearance" type="checkbox">
                <span>周围安全已确认</span>
              </label>
              <label class="checklist-item">
                <input v-model="deliveryOperatorConfirmations.emergency_stop_ready" name="deliveryOperatorConfirmEstop" type="checkbox">
                <span>急停/停止手段就绪</span>
              </label>
              <label class="checklist-item">
                <input v-model="deliveryOperatorConfirmations.observed_motion" name="deliveryOperatorConfirmObservedMotion" type="checkbox">
                <span>已观察到小车到达/运动过程</span>
              </label>
              <label class="checklist-item">
                <input v-model="deliveryOperatorConfirmations.observed_stop" name="deliveryOperatorConfirmObservedStop" type="checkbox">
                <span>已观察到小车停止</span>
              </label>
              <label class="checklist-item">
                <input v-model="deliveryOperatorConfirmations.route_video_refs_verified" name="deliveryOperatorConfirmRefsVerified" type="checkbox">
                <span>视频与 route/map ref 可复核</span>
              </label>
              <label class="checklist-item">
                <input v-model="deliveryOperatorConfirmations.delivery_success" name="deliveryOperatorConfirmDeliverySuccess" type="checkbox">
                <span>确认已投放/送达</span>
              </label>
            </div>
            <button class="danger-button" type="submit" :disabled="loading || operatorReportPending || deliveryCompletionPending || !robotApiBaseUrl.trim() || !deliveryOperatorConfirmationReady || !deliveryOperatorVideoRef.trim() || !deliveryOperatorRouteMapRef.trim()">
              提交送达材料并确认（高级）
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
            <dt>goal execution pending</dt>
            <dd>{{ navGoalExecutionPending ? "pending" : "idle" }}</dd>
            <dt>goal execution status</dt>
            <dd>{{ navGoalExecutionResult?.proxy_status ?? "not_loaded" }} / {{ navGoalExecutionResult?.goal_execution_key_values.status ?? "not_loaded" }}</dd>
            <dt>goal execution keys</dt>
            <dd>{{ recordText(navGoalExecutionResult?.goal_execution_key_values) }}</dd>
            <dt>goal execution failure</dt>
            <dd>{{ navGoalExecutionResult?.failure_reason || "none" }}</dd>
            <dt>goal execution blocked reasons</dt>
            <dd>{{ listText(navGoalExecutionResult?.blocked_reasons, "none") }}</dd>
            <dt>goal latest pending</dt>
            <dd>{{ navGoalExecutionLatestPending ? "pending" : "idle" }}</dd>
            <dt>goal latest status</dt>
            <dd>{{ navGoalExecutionLatestResult?.proxy_status ?? "not_loaded" }} / {{ navGoalExecutionLatestResult?.goal_execution_key_values.status ?? "not_loaded" }}</dd>
            <dt>goal latest keys</dt>
            <dd>{{ recordText(navGoalExecutionLatestResult?.goal_execution_key_values) }}</dd>
            <dt>goal latest failure</dt>
            <dd>{{ navGoalExecutionLatestResult?.failure_reason || "none" }}</dd>
            <dt>delivery latest pending</dt>
            <dd>{{ deliveryLatestPending ? "pending" : "idle" }}</dd>
            <dt>delivery latest status</dt>
            <dd>{{ deliveryLatestResult?.proxy_status ?? "not_loaded" }} / {{ deliveryLatestResult?.delivery_key_values.status ?? "not_loaded" }}</dd>
            <dt>delivery latest keys</dt>
            <dd>{{ recordText(deliveryLatestResult?.delivery_key_values) }}</dd>
            <dt>delivery latest missing</dt>
            <dd>{{ listText(deliveryLatestResult?.blocked_reasons, "none") }}</dd>
            <dt>delivery check pending</dt>
            <dd>{{ deliveryGapCheckPending ? "pending" : "idle" }}</dd>
            <dt>delivery check status</dt>
            <dd>{{ deliveryGapCheckResult?.proxy_status ?? "not_checked" }} / {{ deliveryGapCheckResult?.delivery_key_values.status ?? "not_loaded" }}</dd>
            <dt>delivery check keys</dt>
            <dd>{{ recordText(deliveryGapCheckResult?.delivery_key_values) }}</dd>
            <dt>delivery check missing</dt>
            <dd>{{ listText(deliveryGapCheckResult?.blocked_reasons, "none") }}</dd>
            <dt>delivery gate pending</dt>
            <dd>{{ deliveryCompletionPending ? "pending" : "idle" }}</dd>
            <dt>delivery gate status</dt>
            <dd>{{ deliveryCompletionResult?.proxy_status ?? "not_submitted" }} / {{ deliveryCompletionResult?.status ?? "not_loaded" }}</dd>
            <dt>delivery success</dt>
            <dd>{{ deliveryCompletionResult?.delivery_success ?? false }}</dd>
            <dt>delivery keys</dt>
            <dd>{{ recordText(deliveryCompletionResult?.delivery_key_values) }}</dd>
            <dt>delivery failure</dt>
            <dd>{{ deliveryCompletionResult?.failure_reason || "none" }}</dd>
            <dt>delivery blocked reasons</dt>
            <dd>{{ listText(deliveryCompletionResult?.blocked_reasons, "none") }}</dd>
            <dt>delivery dangerous fields</dt>
            <dd>{{ listText(deliveryCompletionResult?.hard_dangerous_true_fields, "none") }}</dd>
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
          <button class="secondary" type="button" :disabled="manualCommandPending || loading || !robotApiBaseUrl.trim()" @click="sendPlainFirstJog">
            轮速非零试采（高级）
          </button>
          <p class="panel-note">键盘连续手控入口已放在普通首屏；此处只保留完整状态、pulse 和 stop trigger 诊断。</p>
          <button class="secondary" type="button" :disabled="baseFeedbackSamplesPending || !robotApiBaseUrl.trim()" @click="runBaseFeedbackSamples">
            {{ baseFeedbackSamplesPending ? "采集中..." : "采集底盘反馈（高级）" }}
          </button>
          <dl class="kv compact-kv">
            <dt>base feedback samples</dt>
            <dd>{{ baseFeedbackSamplesSummary }}</dd>
            <dt>base feedback key values</dt>
            <dd>
              t1001={{ baseFeedbackSamplesResult?.sample_key_values.t1001_observed_count ?? "not_loaded" }},
              completed={{ baseFeedbackSamplesResult?.sample_key_values.completed_sample_count ?? "not_loaded" }},
              ack={{ baseFeedbackSamplesResult?.sample_key_values.feedback_ack_t1001_observed ?? "not_loaded" }}
            </dd>
            <dt>base feedback raw L/R</dt>
            <dd>
              latest_L={{ baseFeedbackSamplesResult?.sample_key_values.wheel_feedback_latest_left_speed ?? "not_loaded" }},
              latest_R={{ baseFeedbackSamplesResult?.sample_key_values.wheel_feedback_latest_right_speed ?? "not_loaded" }},
              nonzero_frames={{ baseFeedbackSamplesResult?.sample_key_values.wheel_feedback_nonzero_frame_count ?? "0" }},
              proven={{ baseFeedbackSamplesResult?.sample_key_values.wheel_feedback_lr_nonzero_proven ?? "false" }},
              source={{ baseFeedbackSamplesResult?.sample_key_values.wheel_feedback_source ?? "not_loaded" }}
            </dd>
            <dt>wheel raw L/R progress</dt>
            <dd>{{ wheelRawLrProgressSummary }}</dd>
            <dt>base feedback safety</dt>
            <dd>
              motion={{ baseFeedbackSamplesResult?.sample_key_values.sends_motion_commands ?? "false" }},
              executed={{ baseFeedbackSamplesResult?.sample_key_values.robot_control_executed ?? "false" }},
              dangerous={{ listText(baseFeedbackSamplesResult?.hard_dangerous_true_fields, "none") }}
            </dd>
            <dt>manual motion entry</dt>
            <dd>{{ robotSummary?.safe_command_boundary.manual_motion_entry_status ?? "not_loaded" }}</dd>
            <dt>material gate</dt>
            <dd>{{ operatorMaterialGateSummary.state }} / {{ operatorMaterialGateSummary.hint }}</dd>
            <dt>first-jog material restore</dt>
            <dd>{{ firstJogMaterialRestoreSummary }}</dd>
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
            <dt>keyboard continuous control</dt>
            <dd>
              status={{ keyboardControlStatus }},
              armed={{ keyboardControlArmed }},
              held={{ keyboardHeldDirection ?? "none" }},
              mode={{ robotSummary?.safe_command_boundary.keyboard_control_mode ?? "bounded_repeating_manual_pulse" }},
              last_direction={{ keyboardLastDirection }},
              pulse_ms={{ keyboardJogDurationMs }},
              interval_ms={{ keyboardJogIntervalMs }},
              stop_reason={{ keyboardLastStopReason }}
            </dd>
            <dt>keyboard summary</dt>
            <dd>{{ keyboardControlSummary.state }} / {{ keyboardControlSummary.hint }}</dd>
            <dt>keyboard stop triggers</dt>
            <dd>{{ listText(robotSummary?.safe_command_boundary.keyboard_stop_triggers, "key_released/window_blur/page_hidden") }}</dd>
            <dt>keyboard proxy</dt>
            <dd>
              manual={{ robotSummary?.safe_command_boundary.keyboard_manual_proxy_endpoint ?? "/api/robot-control/base/manual" }},
              stop={{ robotSummary?.safe_command_boundary.keyboard_stop_proxy_endpoint ?? "/api/robot-control/base/stop" }},
              reuses_gate={{ robotSummary?.safe_command_boundary.keyboard_reuses_manual_gate ?? true }}
            </dd>
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
              readback={{ robotSummary?.readback_summary.base.latest_feedback_status ?? "not_loaded" }},
              t1001={{ robotSummary?.readback_summary.base.latest_t1001_observed_count ?? "not_loaded" }},
              link={{ robotSummary?.readback_summary.base.feedback_link_status ?? "not_observed" }}
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
            <dt>motion evidence gaps</dt>
            <dd>{{ listText(manualCommandResult?.motion_evidence_gaps, "none") }}</dd>
            <dt>motion wheel feedback</dt>
            <dd>{{ recordText(manualCommandResult?.remote_motion_key_values) }}</dd>
            <dt>wheel raw L/R</dt>
            <dd>
              during_frames={{ manualCommandResult?.remote_motion_key_values?.feedback_during_motion_t1001_frame_count ?? "not_loaded" }},
              latest_L={{ manualCommandResult?.remote_motion_key_values?.wheel_feedback_latest_raw_left ?? "not_loaded" }},
              latest_R={{ manualCommandResult?.remote_motion_key_values?.wheel_feedback_latest_raw_right ?? "not_loaded" }},
              nonzero_frames={{ manualCommandResult?.remote_motion_key_values?.wheel_feedback_nonzero_frame_count ?? "0" }},
              proven={{ manualCommandResult?.remote_motion_key_values?.wheel_feedback_lr_nonzero_proven ?? "false" }}
            </dd>
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
