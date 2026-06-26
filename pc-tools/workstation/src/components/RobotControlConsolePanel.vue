<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  getO7ConsumerTaskDetail,
  getRobotControlSummary,
  getRobotControlMapPreview,
  getRobotControlMapList,
  getRobotControlRadarStatus,
  getRobotControlDeliveryLatest,
  getRobotControlFreeRoamAutonomyLatest,
  postRobotControlBaseFeedbackSamples,
  postRobotControlBaseFirstJog,
  postRobotControlBaseManual,
  postRobotControlBaseStop,
  postRobotControlDeliveryComplete,
  postRobotControlDeliveryGapCheck,
  postRobotControlFreeRoamAutonomyStart,
  postRobotControlFreeRoamAutonomyStop,
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
import { DEFAULT_ROBOT_API_BASE_URL } from "../shared/robotDefaults";
import type {
  O7ConsumerTaskDetailResponse,
  RobotControlBaseCommandRequest,
  RobotControlBaseCommandProxyResponse,
  RobotControlBaseFeedbackSamplesProxyResponse,
  RobotControlCameraFirstFrameProbeProxyResponse,
  RobotControlDeliveryCompleteResponse,
  RobotControlDeliveryLatestResponse,
  RobotControlDeliveryGapCheckResponse,
  RobotControlFreeRoamAutonomyLatestResponse,
  RobotControlFreeRoamAutonomyResponse,
  RobotControlMapLifecycleResponse,
  RobotControlMapPreviewResponse,
  RobotControlNavGoalExecutionLatestResponse,
  RobotControlNavGoalExecutionResponse,
  RobotControlNavGoalPreflightResponse,
  RobotControlOperatorReportProxyResponse,
  RobotControlOperatorReportRequest,
  RobotControlPreviewStatus,
  RobotControlProofRefreshProxyResponse,
  RobotControlRadarLifecycleResponse,
  RobotControlRadarStatusResponse,
  RobotApiFrameTransform,
  RobotApiScanPreviewPoint,
  RobotControlSummaryResponse,
} from "../shared/contracts";

type ManualDirection = "forward" | "back" | "left" | "right";
type MapNavGoal = {
  goal_frame_id: "map";
  goal_x: number;
  goal_y: number;
  goal_yaw: number;
};
const KEYBOARD_JOG_INTERVAL_MS = 260;
const KEYBOARD_JOG_DURATION_MS = 240;
const KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES = 2;
const WHEEL_ZERO_NEXT_ACTION_SUMMARY = "下一步：检查电机使能、供电、模式和现场空间后重试读取轮速。";
const EVIDENCE_STALE_AFTER_MS = 15 * 60 * 1000;
const robotApiBaseUrl = ref(DEFAULT_ROBOT_API_BASE_URL);
const robotApiBaseUrlUsesDefault = computed(() => robotApiBaseUrl.value.trim() === DEFAULT_ROBOT_API_BASE_URL);
const robotApiBaseUrlPlainLabel = computed(() => {
  // 首屏只展示 host:port，既让现场确认默认小车，又避免把高级 URL 输入框放回普通视图。
  return robotApiBaseUrl.value.trim().replace(/^https?:\/\//, "") || "未设置地址";
});
const o6ConsumerBaseUrl = ref("http://127.0.0.1:8088");
const taskId = ref("");
const fieldEvidenceManifestJson = ref("");
const loading = ref(false);
const error = ref("");
const robotSummary = ref<RobotControlSummaryResponse | null>(null);
const taskDetail = ref<O7ConsumerTaskDetailResponse | null>(null);
const radarRefreshResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const radarLifecycleResult = ref<RobotControlRadarLifecycleResponse | null>(null);
const radarStatusResult = ref<RobotControlRadarStatusResponse | null>(null);
const radarLifecyclePendingAction = ref<"start" | "stop" | null>(null);
const mapRefreshResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const nav2RefreshResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const navGoalPreflightResult = ref<RobotControlNavGoalPreflightResponse | null>(null);
const navGoalExecutionResult = ref<RobotControlNavGoalExecutionResponse | null>(null);
const navGoalExecutionLatestResult = ref<RobotControlNavGoalExecutionLatestResponse | null>(null);
const navGoalExecutionPendingGoal = ref<MapNavGoal | null>(null);
const navGoalExecutionAttemptGoal = ref<MapNavGoal | null>(null);
const plainTripStopRequestedDuringExecution = ref(false);
const plainTripStopSettledDuringExecution = ref(false);
const plainTripStopResultDuringExecution = ref<RobotControlBaseCommandProxyResponse | null>(null);
const plainTripPostExecutionMapPreviewRefreshFailed = ref(false);
const deliveryLatestResult = ref<RobotControlDeliveryLatestResponse | null>(null);
const deliveryGapCheckResult = ref<RobotControlDeliveryGapCheckResponse | null>(null);
const deliveryCompletionResult = ref<RobotControlDeliveryCompleteResponse | null>(null);
const localizationResetResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const mapLifecycleResult = ref<RobotControlMapLifecycleResponse | null>(null);
const mapLifecyclePendingAction = ref<"list" | "start" | "save" | null>(null);
const mapPreviewResult = ref<RobotControlMapPreviewResponse | null>(null);
const freeRoamAutonomyResult = ref<RobotControlFreeRoamAutonomyResponse | null>(null);
const freeRoamAutonomyPendingAction = ref<"start" | "stop" | null>(null);
const freeRoamAutonomyStopQueuedAfterStart = ref(false);
const manualCommandResult = ref<RobotControlBaseCommandProxyResponse | null>(null);
const manualCommandPending = ref(false);
const mapLifecyclePending = ref(false);
const mapPreviewPending = ref(false);
const freeRoamAutonomyPending = ref(false);
const freeRoamAutonomyLatestPending = ref(false);
const freeRoamAutonomyLatestResult = ref<RobotControlFreeRoamAutonomyLatestResponse | null>(null);
const mapLifecycleMapName = ref("");
const mapLifecycleArtifactPath = ref("");
const plainFreeRoamMappingConfirmed = ref(false);
const plainFreeRoamMapPreviewFreshForSession = ref(false);
const plainFreeRoamMapPreviewRefreshFailedForSession = ref(false);
const plainFreeRoamLiveMapPreviewRefreshedForHold = ref(false);
const plainFreeRoamSavedMapPreviewFreshForSession = ref(false);
const plainFreeRoamSavedMapPreviewRefreshFailed = ref(false);
const operatorReportPending = ref(false);
const operatorReportResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainVisualMaterialPending = ref(false);
const plainVisualMaterialResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainFirstJogMaterialRestorePending = ref(false);
const plainFirstJogMaterialRestoreResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainFirstJogResult = ref<RobotControlBaseCommandProxyResponse | null>(null);
const plainWheelEvidenceSavePending = ref(false);
const plainWheelEvidenceSaveResult = ref<RobotControlOperatorReportProxyResponse | null>(null);
const plainWheelZeroBlockerChecked = ref(false);
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
const rawFailureReason = ref("");
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
const mapWysiwygRefreshPending = computed(() => mapPreviewPending.value || mapRefreshPending.value);
function mapWysiwygRefreshPendingText(): string {
  return mapPreviewPending.value ? "地图画面刷新中" : "地图状态刷新中";
}
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
const plainRadarRefreshButton = ref<HTMLButtonElement | null>(null);
const plainRadarStartButton = ref<HTMLButtonElement | null>(null);
const keyboardControlPanel = ref<HTMLElement | null>(null);
const keyboardControlRecheckButton = ref<HTMLButtonElement | null>(null);
const keyboardControlArmButton = ref<HTMLButtonElement | null>(null);
const plainTripRunPanel = ref<HTMLElement | null>(null);
const plainTripSafetyCheckbox = ref<HTMLInputElement | null>(null);
const plainTripPrepareButton = ref<HTMLButtonElement | null>(null);
const plainTripExecuteButton = ref<HTMLButtonElement | null>(null);
const plainTripLatestButton = ref<HTMLButtonElement | null>(null);
const plainWheelRecordPanel = ref<HTMLElement | null>(null);
const plainMotionRestoreButton = ref<HTMLButtonElement | null>(null);
const plainFirstJogRestoreButton = ref<HTMLButtonElement | null>(null);
const plainWheelTrialButton = ref<HTMLButtonElement | null>(null);
const plainWheelReadbackButton = ref<HTMLButtonElement | null>(null);
const plainWheelZeroCheckButton = ref<HTMLButtonElement | null>(null);
const plainWheelSaveButton = ref<HTMLButtonElement | null>(null);
const plainDeliveryStatusPanel = ref<HTMLElement | null>(null);
const plainDeliveryPrefillButton = ref<HTMLButtonElement | null>(null);
const plainDeliveryDraftSaveButton = ref<HTMLButtonElement | null>(null);
const plainDeliveryFinalPanel = ref<HTMLElement | null>(null);
const plainDeliveryAllConfirmedButton = ref<HTMLButtonElement | null>(null);
const plainDeliveryConfirmSubmitButton = ref<HTMLButtonElement | null>(null);
const plainFreeRoamConfirmCheckbox = ref<HTMLInputElement | null>(null);
const plainFreeRoamStartButton = ref<HTMLButtonElement | null>(null);
const plainFreeRoamKeyboardButton = ref<HTMLButtonElement | null>(null);
const plainFreeRoamMapRefreshButton = ref<HTMLButtonElement | null>(null);
const plainFreeRoamStopButton = ref<HTMLButtonElement | null>(null);
const plainFreeRoamSaveButton = ref<HTMLButtonElement | null>(null);
const plainFreeRoamAutoStopButton = ref<HTMLButtonElement | null>(null);
const keyboardControlArmed = ref(false);
const keyboardHeldDirection = ref<ManualDirection | null>(null);
const keyboardControlStatus = ref("idle_not_started");
const keyboardLastDirection = ref("not_loaded");
const keyboardVerifiedPulseCount = ref(0);
const keyboardHoldPulseCount = ref(0);
const keyboardLastWheelFeedbackValues = ref<Record<string, string> | null>(null);
const keyboardLastStopReason = ref("not_loaded");
let previewFrameSampleTimers: number[] = [];
let keyboardJogTimer: number | null = null;
let keyboardJogInFlight = false;
let keyboardStopAfterPulseReason: string | null = null;
const keyboardControlOwnerId = `keyboard-owner-${Date.now()}-${Math.random().toString(16).slice(2)}`;
const KEYBOARD_CONTROL_OWNER_KEY = "__roberPcKeyboardControlOwner" as const;

type KeyboardControlWindow = Window & typeof globalThis & {
  __roberPcKeyboardControlOwner?: string;
};

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
const canRunPlainCameraProbe = computed(() => (
  !loading.value
  && !previewBusy.value
  && !cameraFirstFrameProbePending.value
  && robotApiBaseUrl.value.trim().length > 0
));

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
  const probeFailureHint = cameraProbePlainFailureHint();
  const sourceFailed =
    camera?.status === "source_first_frame_failed"
    || camera?.source_readiness === "first_frame_failed"
    || camera?.source_failure_reason === "first_frame_timeout"
    || camera?.last_offer_failure_reason === "first_frame_timeout";
  if (sourceFailed || probeFailureHint) {
    return probeFailureHint || "相机没有出画面，检查摄像头/视频线。";
  }
  const rawLastOfferReason = camera?.last_offer_failure_reason || camera?.last_offer_error || "";
  const lastOfferReason = ["", "none", "not_loaded"].includes(rawLastOfferReason) ? "" : rawLastOfferReason;
  if (lastOfferReason) {
    return cameraOfferPlainFailureHint(lastOfferReason);
  }
  return "";
}

function cameraProbePlainFailureHint(): string {
  // 用户主动做过首帧探针后，普通首屏也要消费结果；不能只把失败藏在高级诊断。
  const result = cameraFirstFrameProbeResult.value;
  if (!result) {
    return "";
  }
  const values = result.probe_key_values;
  const failed =
    result.proxy_status === "probe_failed"
    || result.proxy_status === "probe_rejected"
    || values.first_frame_timeout === "true"
    || values.open_ok === "false"
    || values.read_ok === "false";
  if (!failed) {
    return "";
  }
  return "相机没有出画面，检查摄像头/视频线。";
}

function plainVisualMaterialSaveFailureReason(): string {
  // 记录画面失败要保留上位机短原因，但不把 operator report 字段名塞回首屏。
  const result = plainVisualMaterialResult.value;
  if (!result || (result.proxy_status === "report_forwarded" && result.status !== "blocked")) {
    return "";
  }
  return result.failure_reason || result.blocked_reasons[0] || "保存失败";
}

function plainVisualMaterialSaveFailureHint(): string {
  // 只有固定 camera probe 读到样张后保存失败，才贴回实时画面卡；手填 ref 失败仍留在移动/导航卡。
  const reason = plainVisualMaterialSaveFailureReason();
  if (!reason || !latestCameraProbeSampleRef()) {
    return "";
  }
  return `画面已读到，但记录保存失败：${reason}；请重试记录当前画面。`;
}

function cameraOfferPlainFailureHint(reason: string): string {
  // offer 失败原因来自上位机/信令层；首屏要翻成现场可执行动作，原始字段留在高级诊断。
  if (!reason) {
    return "";
  }
  if (reason.includes("remote_answer_missing") || reason.includes("answer_missing")) {
    return "上位机没有返回视频应答；检查相机服务后重试。";
  }
  if (reason.includes("webrtc_not_supported")) {
    return "当前浏览器不支持实时画面；换 Chrome 后重试。";
  }
  if (reason.includes("invalid_local_offer")) {
    return "本机没有生成有效视频请求；刷新页面后重试。";
  }
  if (reason.includes("fetch_timeout")) {
    return "打开画面超时；检查小车网络和相机服务后重试。";
  }
  if (reason.includes("offer_rejected")) {
    return "上位机拒绝打开画面；检查相机服务状态后重试。";
  }
  if (reason.includes("opencv_capture_not_opened") || reason.includes("capture_not_opened") || reason.includes("camera_open_failed")) {
    return "相机没有打开；检查摄像头/视频线或占用后重试。";
  }
  return `打开画面失败：${reason}`;
}

function browserVideoFrameDrawn(): boolean {
  // 只有浏览器 video 元素真的进入可绘制状态，才允许把 WebRTC track 说成“画面已打开”。
  return videoElementFrameStatus.value === "frame_callback_observed" || videoElementFrameStatus.value === "visible_frame_ready";
}

function summarizeCameraState(): { state: "未打开" | "连接中" | "关闭中" | "检查中" | "等待画面" | "已打开" | "画面可见" | "画面偏暗" | "失败"; hint: string } {
  // 摄像头首屏只暴露普通用户能理解的结论，不泄露 peer / ICE / SDP / canvas 细节。
  const sourceFailureHint = cameraSourcePlainFailureHint();
  const camera = robotSummary.value?.readback_summary.camera;
  const cameraOnline = camera?.status === "ready" || camera?.devices_status === "loaded";
  const visualSaveFailureHint = plainVisualMaterialSaveFailureHint();
  if (cameraFirstFrameProbePending.value && !browserVideoFrameDrawn()) {
    return { state: "检查中", hint: "正在检查当前画面，等待上位机返回样张。" };
  }
  if (visualSaveFailureHint) {
    return { state: "失败", hint: visualSaveFailureHint };
  }
  if (previewStopPending.value) {
    return { state: "关闭中", hint: "正在关闭实时画面，等待上位机释放视频会话。" };
  }
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
      if (sourceFailureHint && !browserVideoFrameDrawn()) {
        return { state: "失败", hint: sourceFailureHint };
      }
      if (!browserVideoFrameDrawn()) {
        return { state: "等待画面", hint: "视频已接入，等待浏览器绘出第一帧。" };
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
      return { state: "失败", hint: cameraOfferPlainFailureHint(rawFailureReason.value || failureReason.value) || "打开画面失败。" };
    default:
      if (sourceFailureHint) {
        return { state: "失败", hint: sourceFailureHint };
      }
      if (cameraOnline) {
        return { state: "未打开", hint: "相机在线，点打开画面。" };
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

function radarStartSucceeded(result: RobotControlRadarLifecycleResponse | null): boolean {
  // 只有上位机明确返回 ok=true 才把启动视为可继续刷新；dry-run/未配置不能冒充成功。
  return result?.action === "start"
    && result.proxy_status === "lifecycle_forwarded"
    && result.status !== "blocked"
    && result.command_result.ok === true;
}

function radarStartCommandConfigured(): boolean {
  // 老版本 summary 没有该字段时保持兼容；只有明确 false 才阻止现场点击 dry-run 启动。
  return effectiveLidarReadback.value?.radar_start_configured !== "false";
}

type LidarReadback = RobotControlSummaryResponse["readback_summary"]["lidar"];

function radarStatusValue(key: string): string | undefined {
  // 独立 radar/status 是刷新地图时的最新只读材料；只有成功 JSON 才覆盖 summary 的旧读数。
  if (radarStatusResult.value?.proxy_status !== "status_loaded") {
    return undefined;
  }
  return radarStatusResult.value.radar_key_values[key];
}

const effectiveLidarReadback = computed<LidarReadback | null>(() => {
  // 地图雷达 marker 必须使用最新可用口径：radar/status 优先，summary 作为兼容兜底。
  const summary = robotSummary.value?.readback_summary.lidar;
  if (!summary && radarStatusResult.value?.proxy_status !== "status_loaded") {
    return null;
  }
  return {
    status: radarStatusValue("status") ?? summary?.status ?? "not_loaded",
    latest_scan_proof_status: radarStatusValue("latest_scan_proof_status") ?? summary?.latest_scan_proof_status ?? "not_loaded",
    latest_raw_packet_proof_status: radarStatusValue("latest_raw_packet_proof_status") ?? summary?.latest_raw_packet_proof_status ?? "not_loaded",
    continuous_scan_status: radarStatusValue("continuous_scan_status") ?? summary?.continuous_scan_status ?? "not_loaded",
    lifecycle_running: radarStatusValue("lifecycle_running") ?? summary?.lifecycle_running ?? "false",
    lifecycle_state: radarStatusValue("lifecycle_state") ?? summary?.lifecycle_state ?? "not_loaded",
    continuous_window_observed: radarStatusValue("continuous_window_observed") ?? summary?.continuous_window_observed ?? "false",
    continuity_window_status: radarStatusValue("continuity_window_status") ?? summary?.continuity_window_status ?? "not_loaded",
    latest_scan_proof_fresh: radarStatusValue("latest_scan_proof_fresh") ?? summary?.latest_scan_proof_fresh ?? "false",
    radar_start_configured: summary?.radar_start_configured ?? "true",
  };
});

type PlainRadarState = "雷达未运行" | "雷达启动中" | "雷达待刷新" | "刷新中" | "雷达已运行" | "刷新失败" | "雷达启动失败";

function radarStartFailed(result: RobotControlRadarLifecycleResponse | null): boolean {
  // start 失败要贴回地图，避免按钮区说失败、地图却仍只显示泛化“未运行”。
  return Boolean(result && result.action === "start" && !radarStartSucceeded(result));
}

function radarStartFailureLabel(result: RobotControlRadarLifecycleResponse | null): string {
  // 普通首屏沿用上位机短 failure_reason；完整 guard 细节仍留在高级诊断。
  if (!radarStartFailed(result)) {
    return "";
  }
  return result?.failure_reason ? `雷达启动失败：${result.failure_reason}` : "雷达启动失败";
}

function radarRefreshFailed(result: RobotControlProofRefreshProxyResponse | null): boolean {
  // refresh 失败也要贴到地图，避免雷达卡说失败、地图 marker 只剩泛化“刷新失败”。
  return Boolean(result && (
    result.proxy_status === "refresh_failed" ||
    result.status === "blocked" ||
    result.last_result_status === "fetch_failed"
  ));
}

function radarRefreshFailureLabel(result: RobotControlProofRefreshProxyResponse | null): string {
  // 普通首屏只显示短原因；endpoint、blocked reasons 仍留在高级诊断区。
  if (!radarRefreshFailed(result)) {
    return "";
  }
  return result?.failure_reason ? `雷达刷新失败：${result.failure_reason}` : "雷达刷新失败";
}

function plainRadarPointHint(live: boolean): string {
  // 雷达卡片要和地图口径一致：普通用户需要知道点数，以及这些点现在能不能贴到地图。
  const proof = robotSummary.value?.o3_proof_summary;
  const points = proof?.scan_preview_points ?? [];
  const fallbackCount = finitePlainNumber(proof?.scan_preview_point_count) ?? 0;
  const count = points.length > 0 ? points.length : fallbackCount;
  if (count <= 0) {
    return "";
  }
  if (proof?.robot_pose?.frame_id === "map") {
    return live ? `已读取雷达点 ${count} 个，已贴到地图。` : `已有雷达点 ${count} 个，刷新后确认实时性。`;
  }
  return live
    ? `已读取雷达点 ${count} 个，当前先显示局部轮廓。`
    : `已有雷达点 ${count} 个，当前先显示局部轮廓，刷新后确认实时性。`;
}

function plainRadarRefreshReason(lidar: RobotControlSummaryResponse["readback_summary"]["lidar"]): string {
  // lifecycle 已运行但 proof 未 fresh 时，要把 stale / incomplete 区分开，避免现场误判为雷达没启动。
  const statusText = `${lidar.continuous_scan_status ?? ""} ${lidar.continuity_window_status ?? ""}`.toLowerCase();
  if (statusText.includes("stale")) {
    return "最新记录已过期";
  }
  if (statusText.includes("incomplete")) {
    return "最新记录不完整";
  }
  if (!radarFieldIsTrue(lidar.continuous_window_observed)) {
    return "连续窗口还没读到";
  }
  return "最新记录未确认";
}

function latestRadarObstacleDistanceLabel(): string {
  // 上位机有时只给自动扫图 gate 的最近障碍距离，没有 scan 点数组；此时只能显示局部距离，不能伪造地图坐标。
  const gates = robotSummary.value?.safe_command_boundary.free_roam_autonomy_gates ?? [];
  const obstacleGate = gates.find((gate) => gate.id === "obstacle_clear");
  const match = obstacleGate?.evidence.match(/(?:最近障碍|障碍|距离)\s*([0-9]+(?:\.[0-9]+)?)\s*m/i);
  const distance = finitePlainNumber(match?.[1]);
  return distance === null ? "" : `最近障碍 ${distance.toFixed(2)}m`;
}

function summarizeRadarState(): { state: PlainRadarState; hint: string } {
  // 雷达首屏优先消费 summary 的最终 lifecycle/continuity 结论；只有最近一次 refresh 明确失败时才覆盖。
  if (radarLifecyclePendingAction.value === "start") {
    return { state: "雷达启动中", hint: "正在启动雷达，等待上位机返回。" };
  }
  if (radarLifecyclePendingAction.value === "stop") {
    return { state: "刷新中", hint: "正在停止雷达，等待上位机返回。" };
  }
  if (radarRefreshPending.value) {
    if (radarStartSucceeded(radarLifecycleResult.value)) {
      return { state: "刷新中", hint: "雷达启动已返回，正在刷新新雷达点。" };
    }
    return { state: "刷新中", hint: "正在刷新雷达状态。" };
  }
  if (radarRefreshFailed(radarRefreshResult.value)) {
    return { state: "刷新失败", hint: radarRefreshResult.value.failure_reason || "暂时没有拿到新的雷达状态。" };
  }
  const lidar = effectiveLidarReadback.value;
  if (!lidar) {
    return { state: "雷达未运行", hint: "先连接小车，再读取雷达状态。" };
  }
  const lifecycleRunning = radarFieldIsTrue(lidar.lifecycle_running);
  const windowObserved = radarFieldIsTrue(lidar.continuous_window_observed);
  const latestFresh = radarFieldIsTrue(lidar.latest_scan_proof_fresh);
  if (lifecycleRunning && windowObserved && latestFresh) {
    const pointHint = plainRadarPointHint(true);
    return { state: "雷达已运行", hint: pointHint ? `当前窗口已看到新的雷达状态；${pointHint}` : "当前窗口已看到新的雷达状态。" };
  }
  if (lifecycleRunning) {
    const pointHint = plainRadarPointHint(false);
    const reason = plainRadarRefreshReason(lidar);
    return { state: "雷达待刷新", hint: pointHint ? `雷达正在运行，但${reason}；先刷新雷达确认。${pointHint}` : `雷达正在运行，但${reason}；先刷新雷达确认。` };
  }
  if (!radarStartCommandConfigured()) {
    return { state: "雷达未运行", hint: "上位机雷达启动命令未配置，先配置后再启动雷达。" };
  }
  if (radarStartSucceeded(radarLifecycleResult.value)) {
    return { state: "雷达待刷新", hint: "雷达启动已返回，请点刷新雷达确认状态。" };
  }
  if (radarLifecycleResult.value?.action === "start" && radarLifecycleResult.value) {
    return { state: "雷达启动失败", hint: radarLifecycleResult.value.failure_reason ? `雷达启动没有成功：${radarLifecycleResult.value.failure_reason}。` : "雷达启动没有成功，请检查上位机配置。" };
  }
  const pointHint = plainRadarPointHint(false);
  return { state: "雷达未运行", hint: pointHint ? `还没有看到雷达正在运行。${pointHint}` : "还没有看到雷达正在运行。" };
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
    if (mapLifecyclePendingAction.value === "start") {
      return { state: "处理中", hint: "正在启动地图记录，返回前先不要移动。" };
    }
    if (mapLifecyclePendingAction.value === "save") {
      return { state: "处理中", hint: "正在保存当前地图，保存完成前不要继续移动。" };
    }
    return { state: "处理中", hint: "正在读取地图列表。" };
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
const cameraFrameTooDark = computed(() => cameraSummary.value.state === "画面偏暗");
const plainCameraReadyForFreeRoamAutonomy = computed(() => {
  // 自动扫图发车只要求上位机相机采集源 ready，不强制浏览器已经打开 WebRTC 画面。
  if (robotSummary.value?.safe_command_boundary.free_roam_autonomy === "ready") {
    return true;
  }
  const camera = robotSummary.value?.readback_summary.camera;
  const sourceFailure =
    camera?.source_readiness === "first_frame_failed"
    || camera?.source_failure_reason === "first_frame_timeout"
    || camera?.last_offer_failure_reason === "first_frame_timeout";
  return Boolean(camera?.status === "ready" && camera?.video_source && !sourceFailure);
});
function plainCameraVideoFrameTruth(): string {
  // 普通首屏只说浏览器是否真的绘制出帧，不暴露 readyState/srcObject 等工程字段。
  const hasSize = videoElementWidth.value > 0 && videoElementHeight.value > 0;
  const sizeText = hasSize ? ` ${videoElementWidth.value}x${videoElementHeight.value}` : "";
  switch (videoElementFrameStatus.value) {
    case "frame_callback_observed":
      return `浏览器已收到视频帧${sizeText}。`;
    case "visible_frame_ready":
      return `浏览器已绘制视频帧${sizeText}。`;
    case "metadata_or_loading":
      return "视频轨道已接入，浏览器正在等待可绘制帧。";
    case "not_bound":
      return cameraSummary.value.state === "未打开" ? "" : "视频元素还没绑定实时流。";
    default:
      return "";
  }
}

const plainCameraFrameEvidenceState = computed(() => {
  // data-state 表达业务结论；这里单独表达浏览器帧证据，避免“已连接”和“已出图”被混在一起。
  switch (videoElementFrameStatus.value) {
    case "frame_callback_observed":
    case "visible_frame_ready":
      return "已绘制帧";
    case "metadata_or_loading":
      return "等待绘帧";
    default:
      if (["连接中", "等待画面", "已打开"].includes(cameraSummary.value.state)) {
        return "等待绘帧";
      }
      if (videoElementFrameStatus.value === "not_bound") {
        return "未绑定";
      }
      return "未观测";
  }
});

const plainCameraWysiwygStatus = computed(() => {
  // 普通首屏要把“按钮状态”和“真实看到的画面”分开说清，避免把已连接误解成已出图。
  const frameTruth = plainCameraVideoFrameTruth();
  switch (cameraSummary.value.state) {
    case "画面可见":
      return `画面状态：当前显示真实视频帧。${frameTruth}`;
    case "画面偏暗":
      return `画面状态：当前画面偏暗，先检查镜头或光线。${frameTruth}`;
    case "已打开":
      return `画面状态：画面已打开，正在确认是否有可见内容。${frameTruth}`;
    case "等待画面":
      return `画面状态：视频已接入，等待浏览器绘出第一帧。${frameTruth}`;
    case "连接中":
      return `画面状态：正在连接真实画面。${frameTruth}`;
    case "关闭中":
      return "画面状态：正在关闭实时画面，等待上位机释放视频会话。";
    case "检查中":
      return "画面状态：正在检查当前画面，等待上位机返回样张。";
    case "失败":
      return `画面状态：${cameraSummary.value.hint}`;
    default:
      if (cameraSummary.value.hint === "相机在线，点打开画面。") {
        return "画面状态：相机在线但画面未打开，点打开画面。";
      }
      return "画面状态：还没打开，本页没有显示实时画面。";
  }
});
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
const plainCameraProbeButtonLabel = computed(() => (
  cameraFirstFrameProbePending.value ? "检查中" : "检查画面（只读）"
));
const plainCameraProbeSummary = computed(() => {
  // 首屏只说明样张是否读到；样张成功不等于实时视频窗口已经打开。
  if (cameraFirstFrameProbePending.value) {
    return "只读检查：正在等待上位机返回样张。";
  }
  const result = cameraFirstFrameProbeResult.value;
  if (!result) {
    return "";
  }
  const failureHint = cameraProbePlainFailureHint();
  if (failureHint) {
    return `只读检查：${failureHint}`;
  }
  const values = result.probe_key_values;
  const sampleWritten = values.sample_write_ok === "true" && Boolean(latestCameraProbeSampleRef());
  const visible = values.visible_content_proven === "true" || values.visible_content_candidate === "true";
  if (result.proxy_status === "probe_forwarded" && values.open_ok === "true" && values.read_ok === "true" && visible) {
    return sampleWritten
      ? "只读检查：上位机样张已读到，实时窗口仍未打开。"
      : "只读检查：上位机读到首帧，但样张没有落盘，实时窗口仍未打开。";
  }
  if (result.proxy_status === "probe_forwarded" && values.open_ok === "true" && values.read_ok === "true") {
    return "只读检查：上位机读到首帧，但内容还不确定；请检查镜头和光线。";
  }
  return `只读检查：${result.failure_reason || values.failure_reason || "没有确认可见画面。"}`;
});
const canSubmitPlainVisualFromCamera = computed(() => (
  !loading.value
  && !previewBusy.value
  && !cameraFirstFrameProbePending.value
  && !plainVisualMaterialPending.value
  && !operatorReportPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const plainRecordCurrentCameraLabel = computed(() => (
  previewBusy.value
    ? "等待画面稳定"
    : cameraFirstFrameProbePending.value
      ? "正在检查画面"
      : plainVisualMaterialSaveFailureHint()
        ? "重试记录当前画面"
        // 只有浏览器真的绘制过当前视频帧，按钮才说“用当前画面”；否则先说明会重新检查相机样张。
        : browserVideoFrameDrawn() ? "用当前画面记录" : "检查并记录画面"
));
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
const plainRadarRequiresRefresh = computed(() => ["雷达待刷新", "刷新失败"].includes(radarSummary.value.state));
const plainRadarStartUnavailable = computed(() => {
  // 配置缺失时普通首屏仍展示卡点，但不让按钮发送一个注定 dry-run 的 start 请求。
  return radarSummary.value.state === "雷达未运行" && !radarStartCommandConfigured();
});
const canStartRadarLifecycle = computed(() => (
  !loading.value
  && !radarLifecyclePending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canResetLocalization = computed(() => (
  !loading.value
  && !localizationResetPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canRefreshNav2Proof = computed(() => (
  !loading.value
  && !nav2RefreshPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canRefreshMapProof = computed(() => (
  !loading.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canRefreshMapPreview = computed(() => (
  !loading.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canRefreshRadarProof = computed(() => (
  !loading.value
  && !radarRefreshPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const plainRadarStartButtonLabel = computed(() => {
  if (plainRadarStartUnavailable.value) {
    return "雷达未配置";
  }
  if (radarLifecyclePendingAction.value === "start") {
    return "雷达启动中";
  }
  if (mapWysiwygRefreshPending.value) {
    return "等待地图刷新";
  }
  return "启动雷达";
});
const plainLocalizationResetButtonLabel = computed(() => (
  mapWysiwygRefreshPending.value ? "等待地图刷新" : "重新定位"
));
const nav2ProofRefreshButtonLabel = computed(() => (
  mapWysiwygRefreshPending.value ? "等待地图刷新" : "检查路径（高级）"
));
const mapProofRefreshButtonLabel = computed(() => (
  mapWysiwygRefreshPending.value ? "等待地图刷新" : "刷新地图"
));
const mapPreviewRefreshButtonLabel = computed(() => (
  mapWysiwygRefreshPending.value ? "等待地图刷新" : "刷新地图画面"
));
const radarProofRefreshButtonLabel = computed(() => (
  mapWysiwygRefreshPending.value ? "等待地图刷新" : "刷新雷达"
));
const canLoadNavGoalExecutionLatest = computed(() => (
  !loading.value
  && !navGoalExecutionLatestPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canLoadDeliveryLatest = computed(() => (
  !loading.value
  && !deliveryLatestPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canCheckDeliveryGap = computed(() => (
  !loading.value
  && !deliveryGapCheckPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canRunBaseFeedbackSamples = computed(() => (
  !baseFeedbackSamplesPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canFillDeliveryVideoRefFromCameraProbe = computed(() => (
  !loading.value
  && !previewBusy.value
  && !cameraFirstFrameProbePending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canPrefillDeliveryMaterialRefs = computed(() => (
  canFillDeliveryVideoRefFromCameraProbe.value
  && !plainDeliveryMapWysiwygPending.value
  && !navGoalExecutionLatestPending.value
  && !deliveryLatestPending.value
  && !cameraFrameTooDark.value
));
const canStopFreeRoamAutonomy = computed(() => (
  robotApiBaseUrl.value.trim().length > 0
  && freeRoamAutonomyPendingAction.value !== "stop"
));
const plainFreeRoamAutoStopButtonLabel = computed(() => {
  if (freeRoamAutonomyPendingAction.value === "stop") {
    return "停止中";
  }
  if (freeRoamAutonomyStopQueuedAfterStart.value) {
    return "停止已排队";
  }
  return "停止自动扫图（随时可点）";
});
const plainFreeRoamLatestButtonLabel = computed(() => (
  freeRoamAutonomyLatestPending.value ? "刷新中" : "刷新自动扫图状态（只读）"
));
const plainFreeRoamLatestSummary = computed(() => {
  const latest = freeRoamAutonomyLatestResult.value;
  if (!latest) {
    return "";
  }
  if (latest.proxy_status !== "latest_loaded") {
    return `自动扫图状态读取失败：${latest.failure_reason || latest.proxy_status}。`;
  }
  const kv = latest.latest_key_values;
  const state = kv.decision_state || "not_loaded";
  const reason = kv.decision_reason && kv.decision_reason !== "not_loaded" ? `：${kv.decision_reason}` : "";
  const mode = kv.artifact_only === "true"
    ? "当前只是记录模式，不会自己跑"
    : kv.cmd_vel_publish_enabled === "true"
      ? "运动发布已解锁，等待真车 HIL"
      : "运动发布未解锁";
  const stop = kv.stop_required === "true" ? "，要求停止兜底" : "";
  return `最新读取：${state}${reason}${stop}；${mode}。`;
});
const showPlainRadarStart = computed(() => {
  // 雷达是 Nav2 和 LiDAR delta 的前置条件；启动传感器不触发底盘运动，可以放在普通首屏。
  return radarLifecyclePendingAction.value === "start"
    || radarSummary.value.state === "雷达未运行"
    || radarSummary.value.state === "雷达启动失败";
});

function plainRadarTripBlockedHint(rerun: boolean): string {
  // lifecycle 已运行但 proof 不完整时，下一步是刷新记录，不是重复启动雷达。
  if (plainRadarStartUnavailable.value) {
    return rerun ? "雷达启动命令未配置，先在上位机配置后再重新执行本轮行程。" : "雷达启动命令未配置，先在上位机配置后再检查或执行行程。";
  }
  if (plainRadarRequiresRefresh.value) {
    return rerun ? "雷达在运行，先刷新雷达，再重新执行本轮行程。" : "雷达在运行，先刷新雷达，再检查或执行行程。";
  }
  return rerun ? "雷达未运行，先启动雷达，再重新执行本轮行程。" : "雷达未运行，先启动雷达，再检查或执行行程。";
}

function plainRadarTripBlockedNextAction(rerun: boolean): string {
  if (plainRadarStartUnavailable.value) {
    return "下一步：先配置雷达启动命令。";
  }
  if (plainRadarRequiresRefresh.value) {
    return rerun ? "下一步：先刷新雷达，再重新执行本轮行程。" : "下一步：先刷新雷达，再检查或执行行程。";
  }
  return rerun ? "下一步：先启动雷达，再重新执行本轮行程。" : "下一步：先启动雷达，再检查或执行行程。";
}

function plainRadarDeliveryNextAction(rerun: boolean): string {
  if (plainRadarStartUnavailable.value) {
    return "下一步：先配置雷达启动命令。";
  }
  if (plainRadarRequiresRefresh.value) {
    return rerun ? "下一步：先刷新雷达，再重新执行本轮行程。" : "下一步：先刷新雷达，再完成本轮行程。";
  }
  return rerun ? "下一步：先启动雷达，再重新执行本轮行程。" : "下一步：先启动雷达，再完成本轮行程。";
}

function plainRadarDeliveryBlockedHint(rerun: boolean): string {
  if (plainRadarStartUnavailable.value) {
    return "送达确认前先配置雷达启动命令并完成本轮完整行程";
  }
  if (plainRadarRequiresRefresh.value) {
    return rerun ? "送达确认前先刷新雷达并重新执行本轮完整行程" : "送达确认前先刷新雷达并完成本轮完整行程";
  }
  return rerun ? "送达确认前先启动雷达并重新执行本轮完整行程" : "送达确认前先启动雷达并完成本轮完整行程";
}

function plainRadarTripClosureHint(rerun: boolean): string {
  if (plainRadarStartUnavailable.value) {
    return rerun ? "雷达启动命令未配置，先在上位机配置后再重新执行完整行程" : "雷达启动命令未配置，先在上位机配置后再执行完整行程";
  }
  if (plainRadarRequiresRefresh.value) {
    return rerun ? "雷达在运行，先刷新雷达，再重新执行完整行程" : "雷达在运行，先刷新雷达，再检查或执行完整行程";
  }
  return rerun ? "雷达未运行，先启动雷达，再重新执行完整行程" : "雷达未运行，先启动雷达，再检查或执行完整行程";
}
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
type PlainMapVisualState = "地图未读取" | "地图处理中" | "地图待刷新" | "地图可见" | "地图不可用";
function finitePlainNumber(value: string | number | null | undefined): number | null {
  // 地图 overlay 只能使用明确数字；not_loaded/空值不能被当作 0 坐标。
  if (value === null || value === undefined || value === "" || value === "not_loaded") {
    return null;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function clampPercent(value: number): number {
  // marker 保留在地图框内，避免目标点落在边缘时文字被裁掉。
  return Math.min(98, Math.max(2, value));
}

function mapFrameStyle(width: number, height: number): Record<string, string> {
  return width > 0 && height > 0 ? { "--map-aspect": `${width} / ${height}` } : {};
}

function plainCellCount(preview: RobotControlMapPreviewResponse | null, key: string): number {
  // cell_counts 是地图质量的直接来源；缺字段按 0 处理，避免把未知地图说成已扫完。
  const value = preview?.cell_counts?.[key];
  return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : 0;
}

function percentText(value: number): string {
  return `${Math.max(0, Math.min(100, value)).toFixed(1)}%`;
}

function mapCoordinatePercent(goalX: number, goalY: number, preview: RobotControlMapPreviewResponse): { left: number; top: number } | null {
  // ROS map origin 是地图左下角；浏览器图像坐标从左上角开始，因此 y 轴需要反转。
  const originX = finitePlainNumber(preview.origin?.[0]);
  const originY = finitePlainNumber(preview.origin?.[1]);
  const resolution = finitePlainNumber(preview.resolution);
  if (originX === null || originY === null || resolution === null || resolution <= 0 || preview.width <= 0 || preview.height <= 0) {
    return null;
  }
  const mapXCell = (goalX - originX) / resolution;
  const mapYCell = (goalY - originY) / resolution;
  const left = clampPercent((mapXCell / preview.width) * 100);
  const top = clampPercent((1 - mapYCell / preview.height) * 100);
  return { left, top };
}

function mapCoordinateStyle(goalX: number, goalY: number, preview: RobotControlMapPreviewResponse): Record<string, string> | null {
  const percent = mapCoordinatePercent(goalX, goalY, preview);
  if (!percent) {
    return null;
  }
  const { left, top } = percent;
  return { left: `${left.toFixed(2)}%`, top: `${top.toFixed(2)}%` };
}

function latestRobotPoseOverlay() {
  const preview = mapPreviewResult.value;
  const pose = robotSummary.value?.o3_proof_summary.robot_pose;
  if (!preview || preview.proxy_status !== "preview_forwarded" || !pose || pose.frame_id !== "map") {
    return null;
  }
  const style = mapCoordinateStyle(pose.x, pose.y, preview);
  if (!style) {
    return null;
  }
  return {
    pose,
    style,
    aria: `机器人位置，地图坐标 x=${pose.x.toFixed(2)}, y=${pose.y.toFixed(2)}`,
  };
}

function scanPointInBaseFrame(point: RobotApiScanPreviewPoint, transform: RobotApiFrameTransform | null): { x: number; y: number; transformApplied: boolean } | null {
  // scan 点若来自 laser_frame，只有显式外参存在时才做 base_link 转换；否则按旧相对坐标展示但不声称外参已应用。
  const localX = finitePlainNumber(point.x_m);
  const localY = finitePlainNumber(point.y_m);
  if (localX === null || localY === null) {
    return null;
  }
  const pointFrame = point.frame_id || "";
  if (!["laser", "laser_frame"].includes(pointFrame) || !transform) {
    return { x: localX, y: localY, transformApplied: false };
  }
  const yaw = finitePlainNumber(transform.yaw) ?? 0;
  return {
    x: transform.x + localX * Math.cos(yaw) - localY * Math.sin(yaw),
    y: transform.y + localX * Math.sin(yaw) + localY * Math.cos(yaw),
    transformApplied: true,
  };
}

function radarScanPointToMapPercent(point: RobotApiScanPreviewPoint, pose: { x: number; y: number; yaw: number | null }, preview: RobotControlMapPreviewResponse, transform: RobotApiFrameTransform | null): { left: number; top: number; transformApplied: boolean } | null {
  // scan 点先按可用外参转 base_link，再用 map-frame robot pose 转成地图坐标。
  const basePoint = scanPointInBaseFrame(point, transform);
  if (!basePoint) {
    return null;
  }
  const yaw = finitePlainNumber(pose.yaw) ?? 0;
  const mapX = pose.x + basePoint.x * Math.cos(yaw) - basePoint.y * Math.sin(yaw);
  const mapY = pose.y + basePoint.x * Math.sin(yaw) + basePoint.y * Math.cos(yaw);
  const percent = mapCoordinatePercent(mapX, mapY, preview);
  return percent ? { ...percent, transformApplied: basePoint.transformApplied } : null;
}

function radarStateUsesPendingPoints(radarState: string): boolean {
  // 雷达 lifecycle 正在或已启动但 proof 未 fresh 时，地图点只能当待刷新材料，不能叫实时点。
  return radarState === "雷达待刷新" || radarState === "刷新中" || radarState === "雷达启动中";
}

function latestRadarScanOverlay(robotPose: ReturnType<typeof latestRobotPoseOverlay>, radarState = "") {
  // 没有 map-frame 位姿时不把雷达点强行落到地图坐标，只返回待定位提示。
  const points = robotSummary.value?.o3_proof_summary.scan_preview_points ?? [];
  const transform = robotSummary.value?.o3_proof_summary.frame_transforms.base_link_to_laser_frame ?? null;
  const preview = mapPreviewResult.value;
  if (!robotPose || !preview || preview.proxy_status !== "preview_forwarded" || points.length === 0) {
    return {
      dots: [],
      label: points.length > 0 ? `雷达点已读取 ${points.length} 个，等待地图位置` : "雷达点位未读取",
    };
  }
  const dots = points
    .map((point, index) => {
      const percent = radarScanPointToMapPercent(point, robotPose.pose, preview, transform);
      if (!percent) {
        return null;
      }
      return {
        key: `${point.source_index ?? index}-${percent.left.toFixed(2)}-${percent.top.toFixed(2)}`,
        left: percent.left,
        top: percent.top,
      };
    })
    .filter((point): point is { key: string; left: number; top: number } => point !== null);
  const transformedCount = points.filter((point) => ["laser", "laser_frame"].includes(point.frame_id || "")).length;
  const transformLabel = transform && transformedCount > 0 ? "，已套用雷达外参" : "";
  const prefix = radarStateUsesPendingPoints(radarState)
    ? "待刷新雷达点"
    : radarState === "雷达已运行" || !radarState ? "雷达点" : "最近雷达点";
  return {
    dots,
    label: dots.length > 0 ? `${prefix} ${dots.length} 个${transformLabel}` : "雷达点位未读取",
  };
}

function latestRadarLocalScanOverlay(robotPose: ReturnType<typeof latestRobotPoseOverlay>, radarState = "") {
  // 缺 map-frame 位姿时只能画雷达局部轮廓，不能冒充地图坐标。
  const points = robotSummary.value?.o3_proof_summary.scan_preview_points ?? [];
  const transform = robotSummary.value?.o3_proof_summary.frame_transforms.base_link_to_laser_frame ?? null;
  if (robotPose || points.length === 0) {
    return { dots: [], label: points.length > 0 ? `雷达点已读取 ${points.length} 个，等待地图位置` : "雷达点位未读取", state: "" };
  }
  const localPoints = points
    .map((point) => scanPointInBaseFrame(point, transform))
    .filter((point): point is { x: number; y: number; transformApplied: boolean } => point !== null);
  if (localPoints.length === 0) {
    return { dots: [], label: "雷达点位未读取", state: "" };
  }
  const radius = Math.max(0.4, ...localPoints.map((point) => Math.hypot(point.x, point.y)));
  const dots = localPoints.map((point, index) => ({
    key: `${index}-${point.x.toFixed(2)}-${point.y.toFixed(2)}`,
    left: clampPercent(50 + (point.x / radius) * 44),
    top: clampPercent(50 - (point.y / radius) * 44),
  }));
  const transformedCount = localPoints.filter((point) => point.transformApplied).length;
  const transformLabel = transform && transformedCount > 0 ? "，已套用雷达外参" : "";
  const freshRadar = radarState === "雷达已运行" || !radarState;
  const pendingRadar = radarStateUsesPendingPoints(radarState);
  const state = freshRadar ? "实时局部点" : pendingRadar ? "待刷新局部点" : "最近局部点";
  const statusLabel = freshRadar ? "" : `，${radarState}`;
  const prefix = freshRadar ? "雷达局部点" : pendingRadar ? "待刷新雷达局部点" : "最近雷达局部点";
  return {
    dots,
    label: `${prefix} ${dots.length} 个${transformLabel}${statusLabel}，等待地图位置`,
    state,
  };
}

function latestNavGoalOverlay() {
  const preview = mapPreviewResult.value;
  if (!preview || preview.proxy_status !== "preview_forwarded") {
    return null;
  }
  if (navGoalExecutionPending.value && navGoalExecutionPendingGoal.value) {
    // pending 标记来自用户刚点击的图上路线终点；只做 UI 读图提示，不替代后端执行结果。
    const pendingGoal = navGoalExecutionPendingGoal.value;
    const style = mapCoordinateStyle(pendingGoal.goal_x, pendingGoal.goal_y, preview);
    if (!style) {
      return null;
    }
    const stopState = plainTripStopOverlayState();
    return {
      label: stopState.label,
      state: stopState.state,
      style,
      aria: `${stopState.ariaPrefix}，目标地图坐标 x=${pendingGoal.goal_x.toFixed(2)}, y=${pendingGoal.goal_y.toFixed(2)}`,
    };
  }
  if (navGoalExecutionLatestPending.value) {
    // latest 读取未返回前不能继续把旧到达结果画成当前结论，先明确标成只读刷新中。
    const values = navGoalExecutionResult.value?.goal_execution_key_values ?? navGoalExecutionLatestResult.value?.goal_execution_key_values;
    const attemptedGoal = navGoalExecutionResult.value ? navGoalExecutionAttemptGoal.value : null;
    const routeGoal = latestNavPathOverlay()?.executionGoal;
    const goalX = finitePlainNumber(values?.goal_x) ?? attemptedGoal?.goal_x ?? routeGoal?.x ?? null;
    const goalY = finitePlainNumber(values?.goal_y) ?? attemptedGoal?.goal_y ?? routeGoal?.y ?? null;
    const goalFrameId = values?.goal_frame_id || attemptedGoal?.goal_frame_id || routeGoal?.frame_id;
    if (goalX === null || goalY === null || (goalFrameId && goalFrameId !== "map")) {
      return null;
    }
    const style = mapCoordinateStyle(goalX, goalY, preview);
    if (!style) {
      return null;
    }
    return {
      label: "读取中",
      state: "读取中",
      style,
      aria: `正在读取最近行程结果，旧结果暂不作为当前结论，地图坐标 x=${goalX.toFixed(2)}, y=${goalY.toFixed(2)}`,
    };
  }
  const values = navGoalExecutionResult.value?.goal_execution_key_values ?? navGoalExecutionLatestResult.value?.goal_execution_key_values;
  if (!values) {
    return null;
  }
  const attemptedGoal = navGoalExecutionResult.value ? navGoalExecutionAttemptGoal.value : null;
  const goalX = finitePlainNumber(values.goal_x) ?? attemptedGoal?.goal_x ?? null;
  const goalY = finitePlainNumber(values.goal_y) ?? attemptedGoal?.goal_y ?? null;
  const goalFrameId = values.goal_frame_id || attemptedGoal?.goal_frame_id;
  if (goalX === null || goalY === null || (goalFrameId && goalFrameId !== "map")) {
    return null;
  }
  const style = mapCoordinateStyle(goalX, goalY, preview);
  if (!style) {
    return null;
  }
  const complete = nav2ExecutionComplete(values);
  const succeeded = nav2GoalSucceeded(values);
  const stale = evidenceIsStale(values);
  const deliveryFailureText = deliveryCompletionFailureText(deliveryCompletionResult.value);
  // 终点 marker 直接表达执行证据，避免把“本轮目标”误读成已经完整到达。
  const controlUnproven = succeeded && !stale && nav2FeedbackSampleCount(values) > 0 && !nav2ExecutionControlProven(values);
  const state = complete && !stale && deliveryCompletionPending.value
    ? "送达确认中"
    : complete && !stale && deliveryFailureText
    ? "送达确认失败"
    : complete && !stale && deliverySuccessReady.value
    ? "已送达"
    : complete && !stale ? "已到达" : succeeded && stale ? "旧到达" : controlUnproven ? "到达未证明" : succeeded ? "到达缺反馈" : "行程未通过";
  const deliveryText = state === "送达确认中"
    ? "，正在提交送达确认"
    : state === "送达确认失败" ? `，送达确认失败：${deliveryFailureText}`
    : state === "已送达" ? "，delivery gate 已确认" : state === "已到达" ? "，下一步准备送达材料" : "";
  const failureText = state === "行程未通过"
    ? plainTripFailureReasonText(navGoalExecutionResult.value ?? navGoalExecutionLatestResult.value, values)
    : "";
  const label = failureText ? `${state}：${failureText}` : state;
  const failureAria = failureText ? `，失败原因${failureText}` : "";
  return {
    label,
    state,
    style,
    aria: `${state}${failureAria}${deliveryText}，地图坐标 x=${goalX.toFixed(2)}, y=${goalY.toFixed(2)}`,
  };
}

function latestNavPathOverlay() {
  const preview = mapPreviewResult.value;
  const proof = robotSummary.value?.o3_proof_summary;
  const points = proof?.path_preview_points ?? [];
  if (!preview || preview.proxy_status !== "preview_forwarded" || points.length < 2) {
    return null;
  }
  const mapPoints = points.filter((point) => !point.frame_id || point.frame_id === "map");
  const projectedPoints = mapPoints
    .map((point) => ({ source: point, percent: mapCoordinatePercent(point.x, point.y, preview) }))
    .filter((point): point is { source: typeof mapPoints[number]; percent: { left: number; top: number } } => point.percent !== null);
  const svgPoints = projectedPoints
    .map((point) => point.percent)
    .map((point) => `${point.left.toFixed(2)},${point.top.toFixed(2)}`);
  if (svgPoints.length < 2) {
    return null;
  }
  const firstPoint = projectedPoints[0];
  const lastPoint = projectedPoints[projectedPoints.length - 1];
  const sourceCount = Number(proof?.path_preview_source_point_count ?? proof?.path_point_count ?? svgPoints.length);
  const totalCount = Number.isFinite(sourceCount) && sourceCount > 0 ? sourceCount : svgPoints.length;
  const currentRoute = proof?.path_generated === true || proof?.path_generation_succeeded === true;
  const routeExecuting = currentRoute && navGoalExecutionPending.value && Boolean(navGoalExecutionPendingGoal.value);
  const routeStopState = routeExecuting ? plainTripStopOverlayState() : null;
  const routePrefix = currentRoute ? "路线" : "最近路线";
  const routeState = routeStopState?.state ?? (currentRoute ? "当前路线" : "最近路线");
  const endpointSummary = `起点 x=${firstPoint.source.x.toFixed(2)}, y=${firstPoint.source.y.toFixed(2)}，终点 x=${lastPoint.source.x.toFixed(2)}, y=${lastPoint.source.y.toFixed(2)}`;
  const routeLabel = routeExecuting
    ? `${routeStopState?.actionText ?? "正在执行图上路线"} ${svgPoints.length}/${totalCount} 个点`
    : currentRoute ? `已读取 ${svgPoints.length} 个路线点` : `已读取最近路线 ${svgPoints.length} 个点`;
  const routeCaption = routeExecuting
    ? routeState === "执行中"
      ? `图上路线执行中 ${svgPoints.length}/${totalCount} 个点`
      : `${routeStopState?.actionText ?? "正在执行图上路线"} ${svgPoints.length}/${totalCount} 个点`
    : currentRoute
      ? `路线已显示 ${svgPoints.length}/${totalCount} 个点`
      : `最近路线已显示 ${svgPoints.length}/${totalCount} 个点，待重新规划`;
  return {
    points: svgPoints.join(" "),
    endpoints: [
      {
        id: "start",
        label: "起点",
        state: `${routePrefix}起点`,
        style: { left: `${firstPoint.percent.left.toFixed(2)}%`, top: `${firstPoint.percent.top.toFixed(2)}%` },
        aria: `${routePrefix}起点，地图坐标 x=${firstPoint.source.x.toFixed(2)}, y=${firstPoint.source.y.toFixed(2)}`,
      },
      {
        id: "end",
        label: "终点",
        state: `${routePrefix}终点`,
        style: { left: `${lastPoint.percent.left.toFixed(2)}%`, top: `${lastPoint.percent.top.toFixed(2)}%` },
        aria: `${routePrefix}终点，地图坐标 x=${lastPoint.source.x.toFixed(2)}, y=${lastPoint.source.y.toFixed(2)}`,
      },
    ],
    displayedCount: svgPoints.length,
    totalCount,
    coordinateLabel: `${routePrefix} ${svgPoints.length}/${totalCount} 个点`,
    endpointSummary,
    executionGoal: {
      // 普通用户入口必须执行“图上看到的终点”，避免被高级表单里的默认 X/Y 悄悄带偏。
      frame_id: "map",
      x: lastPoint.source.x,
      y: lastPoint.source.y,
    },
    state: routeState,
    label: routeLabel,
    caption: routeCaption,
  };
}

function freeRoamAutonomyRuntimeActive(): boolean {
  // 自动扫图 start 已转发或上车端 runtime 正在动作时，草图只能作为监看覆盖参考，不能再说“不会自动移动”。
  const resultActive = freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded"
    && freeRoamAutonomyResult.value.action === "start";
  const runtime = robotSummary.value?.safe_command_boundary.free_roam_autonomy_runtime;
  const runtimeMotionUnlocked = robotSummary.value?.safe_command_boundary.free_roam_autonomy === "ready"
    && runtime?.cmd_vel_publish_enabled === true
    && runtime.artifact_only === false;
  const runtimeActive = runtime?.status === "loaded"
    && runtimeMotionUnlocked
    && ["running", "avoiding", "turning_for_coverage", "stopping"].includes(runtime.state);
  return resultActive || runtimeActive;
}

function latestFreeRoamSweepPlanOverlay(robotPose: ReturnType<typeof latestRobotPoseOverlay>) {
  // 这里只画“扫地图草图”，不生成真实导航目标；缺占用栅格明细时不能把草图说成避障路径。
  const preview = mapPreviewResult.value;
  if (!preview || preview.proxy_status !== "preview_forwarded" || !preview.image_data_url || !preview.has_free_cells) {
    return null;
  }
  const left = 14;
  const right = 86;
  const top = 16;
  const bottom = 84;
  const laneCount = Math.max(4, Math.min(7, Math.round((preview.height || 100) / 18)));
  const laneStep = laneCount > 1 ? (bottom - top) / (laneCount - 1) : 0;
  const robotStart = robotPose ? mapCoordinatePercent(robotPose.pose.x, robotPose.pose.y, preview) : null;
  const points: string[] = [];
  if (robotStart) {
    points.push(`${robotStart.left.toFixed(2)},${robotStart.top.toFixed(2)}`);
  }
  for (let index = 0; index < laneCount; index += 1) {
    const y = top + laneStep * index;
    const startX = index % 2 === 0 ? left : right;
    const endX = index % 2 === 0 ? right : left;
    points.push(`${startX.toFixed(2)},${y.toFixed(2)}`);
    points.push(`${endX.toFixed(2)},${y.toFixed(2)}`);
  }
  const activeAutonomy = freeRoamAutonomyRuntimeActive();
  const activeAutonomyText = activeAutonomy
    ? "自动扫图运行中，草图用于监看覆盖，不是固定路线。"
    : "只读计划，不会自动移动。";
  return {
    points: points.join(" "),
    laneCount,
    state: activeAutonomy ? "自动扫图运行中" : "只读计划",
    showStart: Boolean(robotStart),
    startStyle: robotStart ? { left: `${robotStart.left.toFixed(2)}%`, top: `${robotStart.top.toFixed(2)}%` } : {},
    label: robotStart
      ? `扫地图草图，从当前位置接入 ${laneCount} 段覆盖线；${activeAutonomyText}`
      : `扫地图草图 ${laneCount} 段，等待定位后从当前位置接入；${activeAutonomyText}`,
  };
}

function plainRouteMapCaption(routePath: ReturnType<typeof latestNavPathOverlay>): string {
  // 路线 caption 只解释当前地图上是否能看到路线；不作为执行行程的放行条件。
  if (routePath) {
    return routePath.caption;
  }
  const proof = robotSummary.value?.o3_proof_summary;
  if (!proof?.path_generated && !proof?.path_generation_succeeded) {
    return "";
  }
  const pointCount = Number(proof.path_point_count ?? 0);
  if (Number.isFinite(pointCount) && pointCount > 0) {
    return "路线已准备，刷新地图画面查看";
  }
  return "";
}

function plainMapCoordinateTruthLabel(
  poseObserved: boolean,
  radarScanOverlay: ReturnType<typeof latestRadarScanOverlay>,
  radarLocalScanOverlay: ReturnType<typeof latestRadarLocalScanOverlay>,
  routePath: ReturnType<typeof latestNavPathOverlay>,
  radarState: string,
  localizationFailureLabel = "",
  obstacleDistanceLabel = "",
): string {
  // 所见即所得的核心是把“贴在地图坐标”和“只显示局部轮廓”说清楚，避免误把局部雷达当地图定位。
  if (poseObserved) {
    const scanPrefix = radarStateUsesPendingPoints(radarState)
      ? "待刷新雷达点"
      : radarState === "雷达已运行" ? "雷达点" : "最近雷达点";
    const scanText = radarScanOverlay.dots.length > 0 ? `${scanPrefix} ${radarScanOverlay.dots.length} 个已贴到地图` : "雷达点未贴图";
    const routeText = routePath ? `${routePath.coordinateLabel}已贴到地图` : "路线未显示";
    return `坐标口径：机器人位置已读到，${scanText}，${routeText}。`;
  }
  const poseText = localizationFailureLabel ? `机器人定位失败：${localizationFailureLabel}` : "机器人位置未读到";
  if (radarLocalScanOverlay.dots.length > 0) {
    const routeText = routePath ? `${routePath.coordinateLabel}仍按地图坐标显示` : "目标线未显示";
    const liveRadar = radarState === "雷达已运行" || radarState === "雷达待刷新" || radarState === "雷达启动中" || radarState === "刷新中";
    const scanText = liveRadar
      ? `雷达只显示车身局部轮廓 ${radarLocalScanOverlay.dots.length} 个点`
      : `最近雷达记录只显示车身局部轮廓 ${radarLocalScanOverlay.dots.length} 个点，当前${radarState}`;
    return `坐标口径：${poseText}，${scanText}，不贴到地图；${routeText}。`;
  }
  if (obstacleDistanceLabel && (radarState === "雷达已运行" || radarState === "雷达待刷新" || radarState === "雷达启动中" || radarState === "刷新中")) {
    const routeText = routePath ? `${routePath.coordinateLabel}仍按地图坐标显示` : "目标线未显示";
    return `坐标口径：${poseText}，雷达只显示${obstacleDistanceLabel}，不贴到地图；${routeText}。`;
  }
  if (routePath) {
    return `坐标口径：${poseText}，${routePath.coordinateLabel}按地图坐标显示，雷达不贴图。`;
  }
  return `坐标口径：${poseText}，地图上的雷达和小车位置仍待定位。`;
}

function plainRadarFreshnessLabel(
  radarState: string,
  poseObserved: boolean,
  radarScanOverlay: ReturnType<typeof latestRadarScanOverlay>,
  radarLocalScanOverlay: ReturnType<typeof latestRadarLocalScanOverlay>,
  obstacleDistanceLabel = "",
): string {
  // 雷达点可能来自最近一次 artifact；首屏必须说清它是不是当前运行中的实时点。
  const mapPointCount = radarScanOverlay.dots.length;
  const localPointCount = radarLocalScanOverlay.dots.length;
  if (radarState === "雷达已运行") {
    if (poseObserved && mapPointCount > 0) {
      return `雷达点口径：实时雷达 ${mapPointCount} 个已贴到地图。`;
    }
    if (localPointCount > 0) {
      return `雷达点口径：实时雷达 ${localPointCount} 个只显示局部轮廓，等定位后再贴地图。`;
    }
    if (obstacleDistanceLabel) {
      return `雷达点口径：实时雷达未返回点数组，只显示${obstacleDistanceLabel}，等点位或定位后再贴地图。`;
    }
    return "雷达点口径：雷达已运行，但当前还没读到点位。";
  }
  if (radarState === "雷达启动中") {
    return "雷达点口径：雷达启动命令发送中，返回并刷新后才显示新点位。";
  }
  if (radarState === "雷达启动失败") {
    return "雷达点口径：雷达启动失败，未显示新点位。";
  }
  if (radarState === "雷达刷新失败") {
    return "雷达点口径：雷达刷新失败，未显示新点位。";
  }
  if (radarState === "雷达待刷新" || radarState === "刷新中") {
    if (radarState === "刷新中" && radarStartSucceeded(radarLifecycleResult.value)) {
      return "雷达点口径：雷达启动已返回，正在刷新新点位。";
    }
    if (poseObserved && mapPointCount > 0) {
      return `雷达点口径：正在确认实时性，当前地图上显示待刷新雷达点 ${mapPointCount} 个。`;
    }
    if (obstacleDistanceLabel) {
      return `雷达点口径：正在确认实时性，当前只显示${obstacleDistanceLabel}，刷新后再确认点位。`;
    }
    return localPointCount > 0
      ? `雷达点口径：正在确认实时性，当前先显示局部轮廓 ${localPointCount} 个点。`
      : "雷达点口径：正在确认实时性，刷新后才显示新点位。";
  }
  if (localPointCount > 0) {
    return `雷达点口径：这是最近记录 ${localPointCount} 个点，不是实时雷达。`;
  }
  return "雷达点口径：未读到可显示的实时雷达点。";
}

function plainMapImageFreshnessLabel(previewLoaded: boolean): string {
  // 地图画面和建图动作不是实时视频流；首屏必须明确当前看到的是刷新结果还是上次结果。
  if (mapPreviewPending.value && mapSavedThisSession.value) {
    return "地图画面：地图已保存，正在自动刷新最新画面。";
  }
  if (mapPreviewPending.value) {
    return "地图画面：正在刷新当前地图。";
  }
  const failureText = mapPreviewFailureText(mapPreviewResult.value);
  if (failureText) {
    return `地图画面：刷新失败：${failureText}。`;
  }
  if (keyboardHeldDirection.value && mapRuntimeStarted.value) {
    return plainFreeRoamLiveMapPreviewRefreshedForHold.value
      ? "地图画面：本次按住后已刷新一次；继续移动后还要再刷新确认最新覆盖。"
      : "地图画面：正在扫图，当前显示仍是上次刷新结果。";
  }
  if (mapRuntimeStarted.value) {
    return plainFreeRoamMapPreviewFreshForSession.value
      ? "地图画面：本轮扫图已刷新过；继续移动后要再刷新再保存。"
      : "地图画面：地图记录中，先刷新扫图画面再保存。";
  }
  if (mapSavedThisSession.value) {
    return plainFreeRoamSavedMapPreviewFreshForSession.value
      ? "地图画面：地图已保存，已自动刷新最新画面，可检查效果。"
      : "地图画面：地图已保存，刷新地图画面后检查效果。";
  }
  return previewLoaded ? "地图画面：显示最近读取的真实地图。" : "地图画面：还没读到真实地图图像。";
}

function freeRoamRuntimeMapMarker(robotPose: ReturnType<typeof latestRobotPoseOverlay>) {
  // 自动扫图 runtime 标记只表达上车端状态机判断；缺地图位姿时固定角落展示，不能冒充真实坐标。
  const runtime = robotSummary.value?.safe_command_boundary.free_roam_autonomy_runtime;
  if (!runtime || runtime.status !== "loaded") {
    return null;
  }
  const stateLabels: Record<string, string> = {
    locked: "门禁锁定",
    ready: "等待启动",
    running: "低速直行",
    avoiding: "避障换向",
    turning_for_coverage: "找新覆盖",
    stopping: "停止中",
    completed: "已完成",
  };
  const label = stateLabels[runtime.state] ?? runtime.state;
  const stopSuffix = runtime.stop_required ? "，要求停止" : "";
  return {
    label: `自动扫图：${label}`,
    state: runtime.state,
    style: robotPose
      ? robotPose.style
      : { left: "12px", top: "12px" },
    aria: robotPose
      ? `自动扫图状态 ${label}${stopSuffix}，贴近机器人当前位置`
      : `自动扫图状态 ${label}${stopSuffix}，机器人地图位置未读到，标记不代表坐标`,
  };
}

function freeRoamManualDirectionMapMarker(robotPose: ReturnType<typeof latestRobotPoseOverlay>) {
  // 手控扫图方向来自本机按住状态；只在地图记录中显示，避免待机时误导 operator。
  const direction = keyboardHeldDirection.value;
  if (!direction || !mapRuntimeStarted.value) {
    return null;
  }
  const label = keyboardDirectionPlainLabel.value;
  const wheelSuffix = keyboardWheelFeedbackMapSuffix();
  const wheelAria = keyboardWheelFeedbackPlainText().replace(/^；/, "，");
  const progressText = keyboardForwardedPulseProgressText.value;
  return {
    label: `扫图方向：${label}${wheelSuffix}`,
    state: direction,
    wheelState: keyboardWheelFeedbackState(),
    style: robotPose
      ? robotPose.style
      : { left: "12px", top: "48px" },
    aria: robotPose
      ? `正在${label}扫图，${progressText}${wheelAria}，标记贴近机器人当前位置`
      : `正在${label}扫图，${progressText}${wheelAria}，机器人地图位置未读到，标记不代表坐标`,
  };
}

function manualDirectionOrNull(direction: string | null): ManualDirection | null {
  // 历史方向来自字符串 ref；画地图轨迹前先收窄类型，避免未知状态被画成假轨迹。
  return direction === "forward" || direction === "back" || direction === "left" || direction === "right" ? direction : null;
}

function freeRoamManualTrailOverlay(robotPose: ReturnType<typeof latestRobotPoseOverlay>) {
  // 短轨迹只是把“刚才按住的方向”贴回地图，不是里程计轨迹，也不参与任何控制 gate。
  const preview = mapPreviewResult.value;
  if (!mapRuntimeStarted.value || !preview || preview.proxy_status !== "preview_forwarded" || !preview.image_data_url) {
    return null;
  }
  const liveDirection = keyboardHeldDirection.value;
  const stoppedDirection = keyboardControlStatus.value.startsWith("released")
    || keyboardControlStatus.value.startsWith("stop_sent")
    || keyboardControlStatus.value.startsWith("blocked_keyboard_stop_failed")
    ? manualDirectionOrNull(keyboardLastDirection.value)
    : null;
  const direction = liveDirection ?? stoppedDirection;
  if (!direction) {
    return null;
  }
  const base = robotPose ? mapCoordinatePercent(robotPose.pose.x, robotPose.pose.y, preview) : { left: 18, top: 74 };
  if (!base) {
    return null;
  }
  const yaw = robotPose ? finitePlainNumber(robotPose.pose.yaw) : null;
  const fallbackVectors: Record<ManualDirection, { dx: number; dy: number }> = {
    forward: { dx: 0, dy: -1 },
    back: { dx: 0, dy: 1 },
    left: { dx: -1, dy: 0 },
    right: { dx: 1, dy: 0 },
  };
  const yawOffset: Record<ManualDirection, number> = {
    forward: 0,
    back: Math.PI,
    left: Math.PI / 2,
    right: -Math.PI / 2,
  };
  const vector = yaw === null
    ? fallbackVectors[direction]
    : {
      dx: Math.cos(yaw + yawOffset[direction]),
      dy: -Math.sin(yaw + yawOffset[direction]),
    };
  const length = liveDirection ? (keyboardManualPulseObserved.value ? 20 : 13) : 11;
  const start = {
    left: clampPercent(base.left - vector.dx * length),
    top: clampPercent(base.top - vector.dy * length),
  };
  const end = {
    left: clampPercent(base.left),
    top: clampPercent(base.top),
  };
  const state = liveDirection
    ? "扫图中"
    : keyboardControlStatus.value.startsWith("released")
      ? "停止中"
      : keyboardControlStatus.value.startsWith("blocked_keyboard_stop_failed")
        ? "停止失败"
        : "已停止";
  const directionLabel = manualDirectionPlainLabel(direction);
  const progressText = liveDirection ? keyboardForwardedPulseProgressText.value : plainFreeRoamMapPreviewFreshForSession.value ? "地图画面已刷新" : "等待刷新地图画面";
  const wheelText = keyboardWheelFeedbackPlainText().replace(/^；/, "，");
  const locatedSuffix = robotPose ? "贴近机器人当前位置" : "机器人地图位置未读到，轨迹不代表坐标";
  return {
    points: `${start.left.toFixed(2)},${start.top.toFixed(2)} ${end.left.toFixed(2)},${end.top.toFixed(2)}`,
    state,
    aria: `扫图短轨迹：${directionLabel}，${state}，${progressText}${wheelText}，${locatedSuffix}；短轨迹按按住方向推导，不代表里程计轨迹`,
  };
}

function freeRoamAutonomyFailureText(result: RobotControlFreeRoamAutonomyResponse | null): string {
  // 自动扫图失败原因要在普通首屏可读；完整 blocked reasons 仍留在高级诊断。
  if (!result || result.proxy_status !== "autonomy_failed") {
    return "";
  }
  const raw = result.failure_reason || result.blocked_reasons?.[0] || result.command_result.mode || "request_failed";
  const reason = raw.toLowerCase();
  if (reason.includes("safety") || reason.includes("confirm_operator")) {
    return "安全确认未通过";
  }
  if (reason.includes("mapping") || reason.includes("map_runtime") || reason.includes("map lifecycle")) {
    return "地图记录未启动";
  }
  if (reason.includes("not_ready") || reason.includes("gate") || reason.includes("locked")) {
    return "自动扫图条件未满足";
  }
  if (reason.includes("timeout")) {
    return "等待上车端超时";
  }
  if (reason.includes("fetch") || reason.includes("network")) {
    return "上位机没有回应";
  }
  return "请求失败";
}

function mapLifecycleFailed(result: RobotControlMapLifecycleResponse | null): boolean {
  // 地图记录/保存失败必须继续贴在扫图地图上，不能回落成“尚未开始”的空状态。
  return Boolean(result && (result.proxy_status !== "lifecycle_forwarded" || result.status === "blocked"));
}

function mapLifecycleFailureText(result: RobotControlMapLifecycleResponse | null): string {
  // 普通首屏只给可执行短原因；endpoint、blocked reasons 全量细节留在高级诊断。
  if (!mapLifecycleFailed(result)) {
    return "";
  }
  const raw = result?.failure_reason || result?.blocked_reasons?.[0] || result?.command_result.mode || "request_failed";
  const reason = raw.toLowerCase();
  if (reason.includes("timeout")) {
    return "上位机等待超时";
  }
  if (reason.includes("fetch") || reason.includes("network")) {
    return "上位机没有回应";
  }
  if (reason.includes("command_not_configured") || reason.includes("not_configured")) {
    return "上位机命令未配置";
  }
  if (reason.includes("map") && (reason.includes("unusable") || reason.includes("no_free") || reason.includes("quality"))) {
    return "地图不可用";
  }
  if (reason.includes("blocked") || reason.includes("rejected")) {
    return "请求被阻止";
  }
  return "请求失败";
}

function mapPreviewFailureText(result: RobotControlMapPreviewResponse | null): string {
  // 地图画面失败要复用上位机短原因；技术 endpoint 细节仍放在高级诊断。
  if (!result || result.proxy_status === "preview_forwarded") {
    return "";
  }
  return result.failure_reason || result.blocked_reasons[0] || "地图画面读取失败";
}

function localizationResetFailed(result: RobotControlProofRefreshProxyResponse | null): boolean {
  // 重新定位失败要回写到地图缺位 marker；成功回包不覆盖真实 pose 观测。
  return Boolean(result && (result.proxy_status !== "refresh_forwarded" || result.status === "blocked"));
}

function localizationResetFailureLabel(result: RobotControlProofRefreshProxyResponse | null): string {
  // 普通首屏保留上位机给出的短 failure_reason，避免 operator 只看到“位置未读到”。
  if (!localizationResetFailed(result)) {
    return "";
  }
  return result?.failure_reason || result?.blocked_reasons?.[0] || "定位请求失败";
}

function freeRoamActionMapMarker(robotPose: ReturnType<typeof latestRobotPoseOverlay>) {
  // 扫图流程 marker 把“记录中/已停/可保存/保存中”贴回地图，避免状态只散落在按钮文案里。
  const style = robotPose
    ? robotPose.style
    : { left: "12px", top: "84px" };
  const locatedSuffix = robotPose ? "，贴近机器人当前位置" : "，机器人地图位置未读到，标记不代表坐标";
  const autonomyResult = freeRoamAutonomyResult.value;
  if (mapLifecyclePendingAction.value === "start") {
    return { label: "扫图记录启动中", state: "starting", style, aria: `扫图记录启动中${locatedSuffix}` };
  }
  if (mapLifecyclePendingAction.value === "save") {
    return { label: "地图保存中", state: "saving", style, aria: `当前扫图地图正在保存${locatedSuffix}` };
  }
  if (mapLifecycleFailed(mapLifecycleResult.value) && mapLifecycleResult.value?.action !== "list") {
    const actionText = mapLifecycleResult.value?.action === "save" ? "保存" : "记录启动";
    const failureText = mapLifecycleFailureText(mapLifecycleResult.value);
    const label = failureText ? `地图${actionText}失败：${failureText}` : `地图${actionText}失败`;
    return { label, state: "map_failed", style, aria: `${label}${locatedSuffix}` };
  }
  if (freeRoamAutonomyStopQueuedAfterStart.value) {
    return { label: "自动扫图停止已排队", state: "auto_stop_queued", style, aria: `上车端自动扫图启动返回后会立刻请求停止${locatedSuffix}` };
  }
  if (freeRoamAutonomyPendingAction.value === "start") {
    return { label: "自动扫图启动中", state: "auto_starting", style, aria: `上车端自动扫图状态机正在启动${locatedSuffix}` };
  }
  if (freeRoamAutonomyPendingAction.value === "stop") {
    return { label: "自动扫图停止中", state: "auto_stopping", style, aria: `上车端自动扫图状态机正在停止${locatedSuffix}` };
  }
  if (autonomyResult?.proxy_status === "autonomy_failed") {
    const actionText = autonomyResult.action === "start" ? "启动" : "停止";
    const failureText = freeRoamAutonomyFailureText(autonomyResult);
    const label = failureText ? `自动扫图${actionText}失败：${failureText}` : `自动扫图${actionText}失败`;
    return {
      label,
      state: "auto_failed",
      style,
      aria: `${label}${locatedSuffix}`,
    };
  }
  if (autonomyResult?.proxy_status === "autonomy_forwarded" && autonomyResult.action === "start") {
    const radarFailureText = radarRefreshFailureLabel(radarRefreshResult.value);
    if (radarFailureText) {
      return { label: `自动扫图已启动，${radarFailureText}`, state: "auto_radar_failed", style, aria: `自动扫图状态机已启动，但${radarFailureText}${locatedSuffix}` };
    }
    if (plainFreeRoamMapPreviewRefreshFailedForSession.value) {
      const failureText = mapPreviewFailureText(mapPreviewResult.value);
      const label = failureText ? `自动扫图已启动，地图刷新失败：${failureText}` : "自动扫图已启动，地图刷新失败";
      return { label, state: "auto_map_failed", style, aria: `自动扫图状态机已启动，但地图画面刷新失败${failureText ? `：${failureText}` : ""}${locatedSuffix}` };
    }
    if (mapPreviewPending.value && mapRuntimeStarted.value) {
      return { label: "自动扫图已启动，刷新中", state: "auto_refreshing", style, aria: `自动扫图状态机已启动，地图画面正在刷新${locatedSuffix}` };
    }
    return { label: "自动扫图低速运行中", state: "auto_running", style, aria: `自动扫图状态机已启动，低速运行中，PC 正在监看地图和雷达${locatedSuffix}` };
  }
  if (autonomyResult?.proxy_status === "autonomy_forwarded" && autonomyResult.action === "stop") {
    return plainFreeRoamMapPreviewFreshForSession.value
      ? { label: "自动扫图已停止，可保存", state: "auto_stopped_fresh", style, aria: `自动扫图停止请求已发送，地图画面已刷新，可以保存${locatedSuffix}` }
      : { label: "自动扫图已停止，待刷新画面", state: "auto_stopped_needs_refresh", style, aria: `自动扫图停止请求已发送，需要刷新停止后的地图画面${locatedSuffix}` };
  }
  if (mapPreviewPending.value && mapSavedThisSession.value) {
    return { label: "保存后刷新中", state: "saved_refreshing", style, aria: `扫图地图已保存，正在自动刷新最新画面${locatedSuffix}` };
  }
  if (mapSavedThisSession.value && plainFreeRoamSavedMapPreviewRefreshFailed.value) {
    const failureText = mapPreviewFailureText(mapPreviewResult.value);
    const label = failureText ? `保存后画面刷新失败：${failureText}` : "保存后画面刷新失败";
    return { label, state: "saved_refresh_failed", style, aria: `扫图地图已保存，但最新地图画面刷新失败${failureText ? `：${failureText}` : ""}${locatedSuffix}` };
  }
  if (mapPreviewPending.value && mapRuntimeStarted.value) {
    return { label: "扫图画面刷新中", state: "refreshing", style, aria: `扫图地图画面正在刷新${locatedSuffix}` };
  }
  if (keyboardHeldDirection.value && mapRuntimeStarted.value) {
    const wheelAria = keyboardWheelFeedbackPlainText().replace(/^；/, "，");
    return { label: "扫图移动中", state: "driving", style, aria: `正在${keyboardDirectionPlainLabel.value}扫图，${keyboardForwardedPulseProgressText.value}${wheelAria}${locatedSuffix}` };
  }
  if (mapRuntimeStarted.value && keyboardControlStatus.value.startsWith("released")) {
    const stopLabelSuffix = keyboardLastStopMapSuffix();
    const stopAriaSuffix = keyboardLastStopMapAria();
    return { label: `停止发送中${stopLabelSuffix}`, state: "stopping", style, aria: `已松开方向键${stopAriaSuffix}，正在发送停止${locatedSuffix}` };
  }
  if (mapRuntimeStarted.value && keyboardStopFailedAfterPulse.value) {
    const stopLabelSuffix = keyboardLastStopMapSuffix();
    const stopAriaSuffix = keyboardLastStopMapAria();
    return { label: `停止失败${stopLabelSuffix}`, state: "stop_failed", style, aria: `扫图停止请求失败${stopAriaSuffix}，未证明小车已停止，请点红色停止并现场接管${locatedSuffix}` };
  }
  if (mapRuntimeStarted.value && keyboardControlStatus.value.startsWith("stop_sent")) {
    const stopLabelSuffix = keyboardLastStopMapSuffix();
    const stopAriaSuffix = keyboardLastStopMapAria();
    return plainFreeRoamMapPreviewFreshForSession.value
      ? { label: `已停可保存${stopLabelSuffix}`, state: "stopped_fresh", style, aria: `扫图已停止${stopAriaSuffix}，地图画面已刷新，可以保存${locatedSuffix}` }
      : { label: `已停待刷新${stopLabelSuffix}`, state: "stopped_needs_refresh", style, aria: `扫图已停止${stopAriaSuffix}，需要刷新地图画面${locatedSuffix}` };
  }
  if (mapRuntimeStarted.value) {
    const failureText = mapPreviewFailureText(mapPreviewResult.value);
    if (failureText) {
      return { label: `扫图画面刷新失败：${failureText}`, state: "runtime_refresh_failed", style, aria: `扫图地图画面刷新失败：${failureText}，需要重试刷新扫图画面${locatedSuffix}` };
    }
  }
  if (mapRuntimeStarted.value && keyboardControlArmed.value && canUseKeyboardControl.value) {
    return { label: "键盘已启用（按住才动）", state: "armed", style, aria: `键盘扫图已启用，按住方向键才会移动${locatedSuffix}` };
  }
  if (mapRuntimeStarted.value) {
    return { label: "地图记录中", state: "recording", style, aria: `地图记录已启动，等待扫图移动${locatedSuffix}` };
  }
  if (mapSavedThisSession.value) {
    const label = plainFreeRoamSavedMapPreviewFreshForSession.value ? "地图已保存，画面已刷新" : "地图已保存";
    const freshnessText = plainFreeRoamSavedMapPreviewFreshForSession.value ? "，地图画面已自动刷新，可以检查效果" : "";
    return { label, state: "saved", style, aria: `扫图地图已保存${freshnessText}${locatedSuffix}` };
  }
  return null;
}

const plainMapVisualSummary = computed(() => {
  // 首屏现场视图只使用真实 readback；缺地图或缺定位时显式标缺口，不能画一个假坐标。
  const proof = robotSummary.value?.o3_proof_summary;
  const mapReadback = mapRefreshResult.value?.latest_readback_key_values ?? {};
  const previewLoaded = mapPreviewResult.value?.proxy_status === "preview_forwarded" && Boolean(mapPreviewResult.value.image_data_url);
  const routeGoal = latestNavGoalOverlay();
  const routePath = latestNavPathOverlay();
  const robotPose = latestRobotPoseOverlay();
  const freeRoamSweepPlan = latestFreeRoamSweepPlanOverlay(robotPose);
  const freeRoamRuntimeMarker = freeRoamRuntimeMapMarker(robotPose);
  const freeRoamDirectionMarker = freeRoamManualDirectionMapMarker(robotPose);
  const freeRoamTrail = freeRoamManualTrailOverlay(robotPose);
  const freeRoamActionMarker = freeRoamActionMapMarker(robotPose);
  const mapObserved = proof?.map_once_observed === true
    || mapReadback.map_once_observed === "true"
    || mapReadback.latest_map_once_observed === "true";
  const lifecycle = mapLifecycleResult.value;
  const lifecycleUsable = Boolean(lifecycle?.map_usable_for_navigation || (lifecycle?.map_quality_summary.usable_map_count ?? 0) > 0);
  const lifecycleFailed = mapLifecycleSummary.value.state === "失败";
  const state: PlainMapVisualState = mapRefreshPending.value || mapLifecyclePending.value || mapPreviewPending.value
    ? "地图处理中"
    : lifecycleFailed
      ? "地图不可用"
      : previewLoaded || mapObserved || lifecycleUsable
        ? "地图可见"
        : mapRefreshResult.value || lifecycle
          ? "地图待刷新"
          : "地图未读取";
  const poseObserved = Boolean(robotPose);
  const radarState = radarSummary.value.state;
  const lidar = effectiveLidarReadback.value;
  const radarStartAwaitingRefresh = radarStartSucceeded(radarLifecycleResult.value) && !radarFieldIsTrue(lidar?.lifecycle_running);
  const radarStartFailureText = radarStartFailureLabel(radarLifecycleResult.value);
  const radarRefreshFailureText = radarRefreshFailureLabel(radarRefreshResult.value);
  const displayedRadarState = radarStartFailureText ? "雷达启动失败" : radarRefreshFailureText ? "雷达刷新失败" : radarState;
  const radarNeedsMapPose = radarState === "雷达已运行" || radarState === "雷达待刷新" || radarState === "雷达启动中" || radarState === "刷新中";
  const radarOverlayMode = poseObserved
    ? radarState === "雷达已运行"
      ? "known-pose-running"
      : radarState === "雷达待刷新" || radarState === "雷达启动中" || radarState === "刷新中"
        ? "known-pose-pending"
        : "known-pose-stopped"
    : radarNeedsMapPose
      ? "pose-missing"
      : "stopped";
  const radarScanOverlay = latestRadarScanOverlay(robotPose, radarState);
  const radarLocalScanOverlay = latestRadarLocalScanOverlay(robotPose, radarState);
  const radarLocalPointCount = radarLocalScanOverlay.dots.length;
  const radarObstacleDistanceLabel = latestRadarObstacleDistanceLabel();
  const showRadarObstacleDistance = !poseObserved && radarNeedsMapPose && radarLocalPointCount === 0 && Boolean(radarObstacleDistanceLabel);
  const hasRecentLocalScan = !poseObserved && !radarNeedsMapPose && radarLocalScanOverlay.dots.length > 0;
  const radarOverlayLabel = poseObserved
    ? radarStartFailureText
      ? radarStartFailureText
      : radarRefreshFailureText
      ? radarRefreshFailureText
      : radarStartAwaitingRefresh
      ? "雷达已启动，待刷新"
      : radarState === "雷达已运行"
      ? "雷达"
      : radarState
    : radarStartFailureText
      ? radarStartFailureText
      : radarRefreshFailureText
      ? radarRefreshFailureText
      : radarStartAwaitingRefresh
      ? "雷达已启动，位置未读到"
      : radarNeedsMapPose
      ? radarLocalPointCount > 0 ? `${radarState}，局部点 ${radarLocalPointCount} 个` : showRadarObstacleDistance ? `${radarState}，${radarObstacleDistanceLabel}` : `${radarState}，位置未读到`
      : hasRecentLocalScan ? `${radarState}，显示最近点` : radarState;
  const showRadarSweep = radarState === "雷达已运行" || radarState === "雷达待刷新" || radarState === "雷达启动中" || radarState === "刷新中";
  const radarSweepAria = poseObserved
    ? radarStartAwaitingRefresh
      ? "雷达已启动扫描范围，跟随机器人位置，等待刷新确认"
      : `${radarState}扫描范围，跟随机器人位置`
    : radarStartAwaitingRefresh
      ? "雷达已启动扫描范围占位，等待刷新确认和机器人地图位置"
      : `${radarState}扫描范围占位，等待机器人地图位置`;
  const radarOverlayAria = poseObserved
    ? radarStartFailureText
      ? `${radarStartFailureText}，已叠在机器人位置`
      : radarRefreshFailureText
      ? `${radarRefreshFailureText}，已叠在机器人位置`
      : radarStartAwaitingRefresh
      ? "雷达已启动，已叠在机器人位置，等待刷新确认"
      : `${radarState}，已叠在机器人位置`
    : radarStartFailureText
      ? `${radarStartFailureText}，地图位置未读到`
      : radarRefreshFailureText
      ? `${radarRefreshFailureText}，地图位置未读到`
      : radarStartAwaitingRefresh
      ? "雷达已启动，地图位置未读到，等待刷新确认"
      : showRadarObstacleDistance
        ? `${radarState}，地图位置未读到，${radarObstacleDistanceLabel}，按雷达局部距离显示，未贴到地图`
      : radarNeedsMapPose && radarLocalPointCount > 0
        ? `${radarState}，地图位置未读到，局部轮廓 ${radarLocalPointCount} 个点等待定位`
        : `${radarState}，地图位置未读到`;
  const mapRef = claimRefFromSummary(robotSummary.value?.operator_hil_material_summary.route_map)
    || lifecycle?.map_names?.[0]
    || mapRefreshResult.value?.last_result_evidence_ref
    || "";
  const localizationFailureLabel = localizationResetFailureLabel(localizationResetResult.value);
  const poseLabel = poseObserved ? "位置已读到" : localizationFailureLabel ? `定位失败：${localizationFailureLabel}` : "位置未读到";
  const poseMissingState = localizationFailureLabel ? "定位失败" : "位置未读到";
  const poseMissingAria = localizationFailureLabel
    ? `定位失败：${localizationFailureLabel}，地图上的小车位置未读到`
    : "机器人位置未读到";
  return {
    state,
    poseLabel,
    poseMissingState,
    poseMissingAria,
    radarLabel: displayedRadarState,
    radarOverlayLabel,
    radarOverlayMode,
    radarOverlayAria,
    radarOverlayStyle: poseObserved ? (robotPose?.style ?? {}) : {},
    showRadarSweep,
    radarSweepAria,
    radarScanDots: radarScanOverlay.dots,
    radarScanLabel: radarLocalScanOverlay.dots.length > 0 ? radarLocalScanOverlay.label : showRadarObstacleDistance ? `${radarObstacleDistanceLabel}，等待地图位置` : radarScanOverlay.label,
    radarFreshnessLabel: plainRadarFreshnessLabel(displayedRadarState, poseObserved, radarScanOverlay, radarLocalScanOverlay, showRadarObstacleDistance ? radarObstacleDistanceLabel : ""),
    coordinateTruthLabel: plainMapCoordinateTruthLabel(poseObserved, radarScanOverlay, radarLocalScanOverlay, routePath, displayedRadarState, localizationFailureLabel, showRadarObstacleDistance ? radarObstacleDistanceLabel : ""),
    tripExecutionLabel: plainMapTripExecutionLabel(),
    showRadarScanPoints: showRadarSweep && radarScanOverlay.dots.length > 0,
    radarScanAria: `雷达点位，${radarScanOverlay.label}`,
    radarLocalScanDots: radarLocalScanOverlay.dots,
    showRadarLocalScan: radarLocalScanOverlay.dots.length > 0,
    radarLocalScanState: radarLocalScanOverlay.state,
    radarLocalScanAria: `雷达局部点位，${radarLocalScanOverlay.label}`,
    mapImageFreshnessLabel: plainMapImageFreshnessLabel(previewLoaded),
    mapRefLabel: previewLoaded ? `真实地图 ${mapPreviewResult.value?.width}x${mapPreviewResult.value?.height}` : mapRef ? "地图记录已读取" : "地图记录未读到",
    routePathLabel: plainRouteMapCaption(routePath),
    imageDataUrl: mapPreviewResult.value?.image_data_url || "",
    imageAlt: previewLoaded ? `真实地图 ${mapPreviewResult.value?.map_name || ""}`.trim() : "",
    frameStyle: mapFrameStyle(mapPreviewResult.value?.width ?? 0, mapPreviewResult.value?.height ?? 0),
    showRobotPose: poseObserved,
    robotPoseStyle: robotPose?.style ?? {},
    robotPoseAria: robotPose?.aria ?? "机器人位置未读到",
    showRadarPulse: poseObserved && radarState === "雷达已运行",
    showRouteGoal: Boolean(routeGoal),
    routeGoalLabel: routeGoal?.label ?? "",
    routeGoalState: routeGoal?.state ?? "",
    routeGoalStyle: routeGoal?.style ?? {},
    routeGoalAria: routeGoal?.aria ?? "",
    showRoutePath: Boolean(routePath),
    routePathPoints: routePath?.points ?? "",
    routePathState: routePath?.state ?? "",
    routePathAria: routePath?.label ?? "",
    routeEndpointMarkers: routePath?.endpoints.filter((point) => point.id === "start" || !routeGoal) ?? [],
    showFreeRoamSweepPlan: Boolean(freeRoamSweepPlan),
    freeRoamSweepPlanPoints: freeRoamSweepPlan?.points ?? "",
    freeRoamSweepPlanState: freeRoamSweepPlan?.state ?? "",
    freeRoamSweepPlanAria: freeRoamSweepPlan?.label ?? "",
    freeRoamSweepPlanLabel: freeRoamSweepPlan?.label ?? "",
    showFreeRoamSweepStart: freeRoamSweepPlan?.showStart ?? false,
    freeRoamSweepStartStyle: freeRoamSweepPlan?.startStyle ?? {},
    showFreeRoamRuntimeMarker: Boolean(freeRoamRuntimeMarker),
    freeRoamRuntimeMarkerLabel: freeRoamRuntimeMarker?.label ?? "",
    freeRoamRuntimeMarkerState: freeRoamRuntimeMarker?.state ?? "",
    freeRoamRuntimeMarkerStyle: freeRoamRuntimeMarker?.style ?? {},
    freeRoamRuntimeMarkerAria: freeRoamRuntimeMarker?.aria ?? "",
    showFreeRoamDirectionMarker: Boolean(freeRoamDirectionMarker),
    freeRoamDirectionMarkerLabel: freeRoamDirectionMarker?.label ?? "",
    freeRoamDirectionMarkerState: freeRoamDirectionMarker?.state ?? "",
    freeRoamDirectionMarkerWheelState: freeRoamDirectionMarker?.wheelState ?? "",
    freeRoamDirectionMarkerStyle: freeRoamDirectionMarker?.style ?? {},
    freeRoamDirectionMarkerAria: freeRoamDirectionMarker?.aria ?? "",
    showFreeRoamTrail: Boolean(freeRoamTrail),
    freeRoamTrailPoints: freeRoamTrail?.points ?? "",
    freeRoamTrailState: freeRoamTrail?.state ?? "",
    freeRoamTrailAria: freeRoamTrail?.aria ?? "",
    showFreeRoamActionMarker: Boolean(freeRoamActionMarker),
    freeRoamActionMarkerLabel: freeRoamActionMarker?.label ?? "",
    freeRoamActionMarkerState: freeRoamActionMarker?.state ?? "",
    freeRoamActionMarkerStyle: freeRoamActionMarker?.style ?? {},
    freeRoamActionMarkerAria: freeRoamActionMarker?.aria ?? "",
  };
});
const manualBoundary = computed(() => robotSummary.value?.safe_command_boundary ?? null);
const manualSpeedLimit = computed(() => manualBoundary.value?.speed_limit_mps ?? 0.12);
const manualDurationLimit = computed(() => manualBoundary.value?.duration_limit_ms ?? 800);
const keyboardJogIntervalMs = computed(() => manualBoundary.value?.keyboard_jog_interval_ms ?? KEYBOARD_JOG_INTERVAL_MS);
const keyboardJogDurationMs = computed(() => manualBoundary.value?.keyboard_jog_duration_ms ?? KEYBOARD_JOG_DURATION_MS);
const plainManualSafetyConfirmed = computed(() => plainTripSafetyConfirmed.value || plainFreeRoamMappingConfirmed.value);
const plainUnifiedSafetyConfirmed = computed({
  // 普通首屏只有一个真实安全确认语义；两个可见复选框同步显示，避免现场重复确认。
  get: () => plainManualSafetyConfirmed.value,
  set: (confirmed: boolean) => {
    plainTripSafetyConfirmed.value = confirmed;
    plainFreeRoamMappingConfirmed.value = confirmed;
  },
});
const canSendStop = computed(() => !manualCommandPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0);
const canRequestKeyboardStop = computed(() => (
  canSendStop.value
  || (
    manualCommandPending.value
    && keyboardHeldDirection.value !== null
    && robotApiBaseUrl.value.trim().length > 0
  )
));
const canRunEvidenceSweep = computed(() => !evidenceSweepPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0);
const keyboardContractReady = computed(() => {
  // 键盘手控必须由后端 summary 明确声明 bounded pulse 合同，不能只靠前端默认值放开。
  return robotSummary.value?.safe_command_boundary.keyboard_control_mode === "bounded_repeating_manual_pulse"
    && robotSummary.value.safe_command_boundary.keyboard_reuses_manual_gate === true;
});
const canUseKeyboardControl = computed(() => keyboardContractReady.value && canSendManualMotion.value);
const canArmKeyboardControl = computed(() => canUseKeyboardControl.value);
const keyboardManualPulseObserved = computed(() => keyboardVerifiedPulseCount.value >= KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES);
const keyboardStopSettledAfterPulse = computed(() => keyboardManualPulseObserved.value && !keyboardHeldDirection.value && keyboardControlStatus.value.startsWith("stop_sent"));
const keyboardStopFailedAfterPulse = computed(() => (
  // stop 失败时不能等“连续 2 次”才告警；任何一次扫图移动后的 stop 失败都必须 fail-closed。
  !keyboardHeldDirection.value
  && keyboardControlStatus.value.startsWith("blocked_keyboard_stop_failed")
));
const mapRuntimeStarted = computed(() => (
  mapLifecycleResult.value?.action === "start"
  && mapLifecycleResult.value.proxy_status === "lifecycle_forwarded"
  && mapLifecycleResult.value.command_result.executed === true
));
const keyboardMapWysiwygBlocked = computed(() => (
  // 地图画面或 proof 刷新中不能开始新的扫图移动；已经按住移动时仍允许松开并发送 stop。
  mapRuntimeStarted.value && mapWysiwygRefreshPending.value && !keyboardHeldDirection.value
));
const canPressKeyboardDirection = computed(() => (
  keyboardControlArmed.value
  && canUseKeyboardControl.value
  && !keyboardMapWysiwygBlocked.value
  && !keyboardStopFailedAfterPulse.value
));
const mapSavedThisSession = computed(() => (
  mapLifecycleResult.value?.action === "save"
  && mapLifecycleResult.value.proxy_status === "lifecycle_forwarded"
));
const canStartPlainFreeRoamMapping = computed(() => (
  plainManualSafetyConfirmed.value
  && !loading.value
  && !mapLifecyclePending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canStartMapLifecycle = computed(() => (
  !loading.value
  && !mapLifecyclePending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const freeRoamAutonomySaveBlocked = computed(() => (
  // 自动扫图状态机未明确停止前不能保存地图，避免把运行中或停止失败的覆盖过程误收口。
  freeRoamAutonomyPendingAction.value !== null
  || (
    freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded"
    && freeRoamAutonomyResult.value.action === "start"
  )
  || (
    freeRoamAutonomyResult.value?.proxy_status === "autonomy_failed"
    && freeRoamAutonomyResult.value.action === "stop"
  )
));
const freeRoamMapWysiwygPending = computed(() => (
  // 自动扫图 start 必须等地图画面/状态刷新结束，不能拿旧图当本轮所见即所得证据。
  mapWysiwygRefreshPending.value
));
const canSaveMapLifecycle = computed(() => (
  !loading.value
  && !mapLifecyclePending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canSavePlainFreeRoamMapping = computed(() => (
  plainManualSafetyConfirmed.value
  && mapRuntimeStarted.value
  && plainFreeRoamMapPreviewFreshForSession.value
  && !keyboardStopFailedAfterPulse.value
  && !freeRoamAutonomySaveBlocked.value
  && !freeRoamMapWysiwygPending.value
  && !loading.value
  && !mapLifecyclePending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const canStartFreeRoamAutonomy = computed(() => (
  (
    robotSummary.value?.safe_command_boundary.free_roam_autonomy_start_ready === true
    || robotSummary.value?.safe_command_boundary.free_roam_autonomy === "ready"
  )
  && plainManualSafetyConfirmed.value
  && mapRuntimeStarted.value
  && plainFreeRoamMapPreviewFreshForSession.value
  && !freeRoamMapWysiwygPending.value
  && plainCameraReadyForFreeRoamAutonomy.value
  && radarSummary.value.state === "雷达已运行"
  && canSendStop.value
  && !freeRoamAutonomyPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const freeRoamAutonomyStartedThisSession = computed(() => (
  // 自动扫图代理结果只代表状态机请求已转发；下一步提示必须从人工键盘流程切回监看/停止流程。
  freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded"
  && freeRoamAutonomyResult.value.action === "start"
));
const freeRoamAutonomyStoppedThisSession = computed(() => (
  // stop 请求已转发后，现场下一步应回到刷新/保存地图，而不是继续引导键盘扫图。
  freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded"
  && freeRoamAutonomyResult.value.action === "stop"
));
const canArmPlainFreeRoamKeyboard = computed(() => (
  // 扫图键盘入口必须等地图记录真的启动；普通键盘手控仍保持最小安全确认入口。
  plainManualSafetyConfirmed.value
  && mapRuntimeStarted.value
  && canArmKeyboardControl.value
));
const plainFreeRoamMappingSummary = computed(() => {
  // 扫地式建图向导只编排已有安全入口；自由跑动仍必须由键盘低速脉冲和停止按钮兜底。
  if (!robotApiBaseUrl.value.trim()) {
    return { state: "未连接", hint: "先连接默认小车，再开始扫地式建图。" };
  }
  if (!plainManualSafetyConfirmed.value) {
    return { state: "待确认", hint: "勾选现场安全确认后，才允许启动建图向导。" };
  }
  if (mapLifecyclePending.value) {
    if (mapLifecyclePendingAction.value === "start") {
      return { state: "启动中", hint: "正在启动地图记录；启动返回前不要移动小车。" };
    }
    if (mapLifecyclePendingAction.value === "save") {
      return { state: "保存中", hint: "正在保存当前扫图地图；保存完成前不要继续移动。" };
    }
    return { state: "读取中", hint: "正在读取地图列表。" };
  }
  if (mapPreviewPending.value && mapSavedThisSession.value) {
    return { state: "刷新中", hint: "地图已保存，正在自动刷新最新画面。" };
  }
  if (mapWysiwygRefreshPending.value) {
    return { state: "刷新中", hint: `${mapWysiwygRefreshPendingText()}；刷新完成后再开始或保存扫图。` };
  }
  if (mapPreviewPending.value) {
    return { state: "刷新中", hint: "正在刷新扫图画面；刷新完成后再保存。" };
  }
  if (mapLifecycleFailed(mapLifecycleResult.value) && mapLifecycleResult.value?.action !== "list") {
    const actionText = mapLifecycleResult.value?.action === "save" ? "保存地图" : "启动地图记录";
    const failureText = mapLifecycleFailureText(mapLifecycleResult.value);
    const reasonSuffix = failureText ? `：${failureText}` : "";
    return { state: "失败", hint: `${actionText}失败${reasonSuffix}；检查上位机地图服务后重试。` };
  }
  if (mapSavedThisSession.value) {
    if (plainFreeRoamSavedMapPreviewRefreshFailed.value) {
      const failureText = mapPreviewFailureText(mapPreviewResult.value);
      const reasonSuffix = failureText ? `：${failureText}` : "";
      return { state: "失败", hint: `地图已保存，但最新画面刷新失败${reasonSuffix}；重试刷新扫图画面后再检查效果。` };
    }
    return plainFreeRoamSavedMapPreviewFreshForSession.value
      ? { state: "已保存", hint: "地图已保存，地图画面已自动刷新；现在可以检查 free cell 和路线可用性。" }
      : { state: "已保存", hint: "地图已保存；刷新地图画面后可检查 free cell 和路线可用性。" };
  }
  if (mapRuntimeStarted.value) {
    if (keyboardStopFailedAfterPulse.value) {
      return { state: "失败", hint: "扫图停止请求失败；先点红色停止并现场接管，不能保存当前地图。" };
    }
    const failureText = mapPreviewFailureText(mapPreviewResult.value);
    if (failureText) {
      return { state: "待刷新", hint: `地图记录已启动，但扫图画面刷新失败：${failureText}；重试刷新扫图画面后再继续保存。` };
    }
    return canUseKeyboardControl.value
      ? { state: "扫图中", hint: "建图已启动。按住方向键/WASD 低速扫一圈，松开即停，随时点停止。" }
      : { state: "待手控", hint: `建图已启动，但键盘移动条件还没满足。${plainKeyboardNextActionSummary.value}` };
  }
  return { state: "可开始", hint: "先启动地图记录，再按住方向键让小车低速走一圈，最后保存地图。" };
});
const plainFreeRoamMappingStartLabel = computed(() => (
  mapLifecyclePending.value && mapLifecyclePendingAction.value === "start"
    ? "启动中"
    : mapWysiwygRefreshPending.value
      ? "等待地图刷新"
      : mapRuntimeStarted.value ? "重新启动记录" : "开始扫地式建图"
));
const plainFreeRoamMappingSaveLabel = computed(() => (
  mapLifecyclePending.value && mapLifecyclePendingAction.value === "save"
    ? "保存中"
    : keyboardStopFailedAfterPulse.value
      ? "先停止小车"
    : freeRoamAutonomySaveBlocked.value
      ? "先停止自动扫图"
    : freeRoamMapWysiwygPending.value && mapRuntimeStarted.value
      ? "等待地图刷新"
    : mapRuntimeStarted.value && !plainFreeRoamMapPreviewFreshForSession.value
      ? "先刷新画面"
      : "保存当前地图"
));
const canRefreshPlainFreeRoamMapPreview = computed(() => (
  (mapRuntimeStarted.value || mapSavedThisSession.value)
  && canRefreshMapPreview.value
));
const plainFreeRoamMapPreviewLabel = computed(() => {
  // 扫图卡片内的画面刷新只读地图预览，必须等记录启动后才作为流程按钮出现。
  if (mapWysiwygRefreshPending.value) {
    return "等待地图刷新";
  }
  return mapRuntimeStarted.value || mapSavedThisSession.value ? "刷新扫图画面" : "先开始记录";
});
const plainFreeRoamKeyboardLabel = computed(() => {
  // 按扫地式建图顺序提示下一步，避免 operator 在未记录地图时先移动。
  if (!plainManualSafetyConfirmed.value) {
    return "先勾安全确认";
  }
  if (!mapRuntimeStarted.value) {
    return "先开始记录";
  }
  if (keyboardControlArmed.value && canUseKeyboardControl.value) {
    return "键盘已启用（按住才动）";
  }
  return canArmKeyboardControl.value ? "启用键盘扫图" : "键盘条件未满足";
});
const plainFreeRoamNextActionLabel = computed(() => {
  // “下一步”只做流程导航，不能替现场确认、启动建图、发送手控或保存地图。
  if (!plainManualSafetyConfirmed.value) {
    return "下一步：勾安全确认";
  }
  if (mapLifecyclePending.value) {
    return "下一步：等待地图动作完成";
  }
  if (mapPreviewPending.value && mapSavedThisSession.value) {
    return "下一步：等待画面刷新";
  }
  if (mapSavedThisSession.value && plainFreeRoamSavedMapPreviewRefreshFailed.value) {
    return "下一步：重新刷新扫图画面";
  }
  if (!mapRuntimeStarted.value && !mapSavedThisSession.value) {
    if (mapWysiwygRefreshPending.value) {
      return "下一步：等待地图刷新";
    }
    return canStartPlainFreeRoamMapping.value ? "下一步：开始记录" : "下一步：等待连接";
  }
  if (freeRoamAutonomyStopQueuedAfterStart.value) {
    return "下一步：等待启动返回后自动停止";
  }
  if (freeRoamAutonomyPendingAction.value === "start") {
    return "下一步：等待自动扫图启动";
  }
  if (freeRoamAutonomyPendingAction.value === "stop") {
    return "下一步：等待自动扫图停止";
  }
  if (freeRoamAutonomyResult.value?.proxy_status === "autonomy_failed") {
    return freeRoamAutonomyResult.value.action === "stop"
      ? "下一步：点红色停止"
      : "下一步：人工扫图或重试自动扫图";
  }
  if (freeRoamAutonomyStartedThisSession.value) {
    return "下一步：监看或停止自动扫图";
  }
  if (freeRoamAutonomyStoppedThisSession.value) {
    return plainFreeRoamMapPreviewFreshForSession.value ? "下一步：保存地图" : "下一步：刷新扫图画面";
  }
  if (mapRuntimeStarted.value && mapPreviewFailureText(mapPreviewResult.value) && !keyboardHeldDirection.value) {
    return "下一步：重新刷新扫图画面";
  }
  if (mapRuntimeStarted.value && keyboardStopFailedAfterPulse.value) {
    return "下一步：点红色停止";
  }
  if (mapRuntimeStarted.value && !keyboardControlArmed.value) {
    return canArmPlainFreeRoamKeyboard.value ? "下一步：启用键盘" : "下一步：补齐键盘条件";
  }
  if (keyboardMapWysiwygBlocked.value) {
    return "下一步：等待地图刷新";
  }
  if (keyboardHeldDirection.value) {
    return "下一步：松开或停止";
  }
  if (mapRuntimeStarted.value && keyboardControlStatus.value.startsWith("released")) {
    return "下一步：等待停止完成";
  }
  if (mapRuntimeStarted.value && !mapSavedThisSession.value) {
    if (keyboardStopSettledAfterPulse.value) {
      return plainFreeRoamMapPreviewFreshForSession.value ? "下一步：保存地图" : "下一步：刷新扫图画面";
    }
    return "下一步：按住方向键扫图";
  }
  return "下一步：检查地图画面";
});
const plainFreeRoamManualGuideButtonLabel = computed(() => {
  // 自动扫图未开放时，这个按钮就是人工扫图向导；文案必须显示下一次点击的真实动作。
  const nextAction = plainFreeRoamNextActionLabel.value.replace(/^下一步：/, "");
  if (nextAction === "勾安全确认") {
    return "先勾安全确认";
  }
  if (nextAction === "开始记录") {
    return "开始记录并继续";
  }
  if (nextAction === "启用键盘") {
    return "启用键盘扫图";
  }
  if (nextAction === "刷新扫图画面") {
    return "刷新扫图画面";
  }
  if (nextAction === "保存地图") {
    return "保存当前地图";
  }
  if (nextAction === "松开或停止") {
    return "松开或停止";
  }
  return `按步骤：${nextAction}`;
});
const plainFreeRoamAutonomyGuideButtonLabel = computed(() => {
  // 自动扫图已由上车端开放但仍差现场证据时，按钮只做补证引导，不能伪装成真正 start。
  if (!plainManualSafetyConfirmed.value) {
    return "先勾安全确认";
  }
  if (!mapRuntimeStarted.value) {
    return "开始记录并继续";
  }
  if (!plainFreeRoamMapPreviewFreshForSession.value) {
    return "刷新扫图画面";
  }
  if (!plainCameraReadyForFreeRoamAutonomy.value) {
    return cameraSummary.value.state === "失败" ? "检查摄像头后开始" : "打开画面后开始";
  }
  if (radarSummary.value.state !== "雷达已运行") {
    return plainRadarRequiresRefresh.value ? "刷新雷达后开始" : "启动雷达后开始";
  }
  if (!canSendStop.value) {
    return "补停止兜底";
  }
  return "检查自动扫图条件";
});
const plainFreeRoamDriveStatus = computed(() => {
  // 扫图状态只解释当前本地流程，不自动启用键盘、不发送 manual，也不把自动扫图说成已开放。
  if (!plainManualSafetyConfirmed.value) {
    return "扫图状态：先勾安全确认，小车不会移动。";
  }
  if (mapLifecyclePendingAction.value === "start") {
    return "扫图状态：正在启动地图记录，等记录启动后再移动。";
  }
  if (mapLifecyclePendingAction.value === "save") {
    return "扫图状态：正在保存当前地图，保存完成前不要继续移动。";
  }
  if (mapLifecycleFailed(mapLifecycleResult.value) && mapLifecycleResult.value?.action !== "list") {
    const actionText = mapLifecycleResult.value?.action === "save" ? "地图保存" : "地图记录启动";
    const failureText = mapLifecycleFailureText(mapLifecycleResult.value);
    const reasonSuffix = failureText ? `：${failureText}` : "";
    return `扫图状态：${actionText}失败${reasonSuffix}，小车不会移动；检查上位机地图服务后重试。`;
  }
  if (!mapRuntimeStarted.value && !mapSavedThisSession.value) {
    return "扫图状态：还没开始记录，键盘扫图锁定。";
  }
  if (mapPreviewPending.value && mapSavedThisSession.value) {
    return "扫图状态：地图已保存，正在自动刷新最新画面。";
  }
  if (freeRoamAutonomyStopQueuedAfterStart.value) {
    return "扫图状态：停止自动扫图已排队，启动请求返回后会立刻请求上车端停止。";
  }
  if (freeRoamAutonomyPendingAction.value === "start") {
    return "扫图状态：正在启动上车端自动扫图状态机，PC 保持地图、雷达和停止兜底。";
  }
  if (freeRoamAutonomyPendingAction.value === "stop") {
    return "扫图状态：正在请求上车端自动扫图停止，红色停止仍可随时兜底。";
  }
  if (freeRoamAutonomyResult.value?.proxy_status === "autonomy_failed") {
    const failureText = freeRoamAutonomyFailureText(freeRoamAutonomyResult.value);
    const reasonSuffix = failureText ? `：${failureText}` : "";
    return freeRoamAutonomyResult.value.action === "start"
      ? `扫图状态：自动扫图启动失败${reasonSuffix}，未证明上车状态机已启动；继续人工按住扫图或重试。`
      : `扫图状态：自动扫图停止失败${reasonSuffix}，未证明上车状态机已停止；必要时点击红色停止。`;
  }
  if (freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded" && freeRoamAutonomyResult.value.action === "start") {
    const radarFailureText = radarRefreshFailureLabel(radarRefreshResult.value);
    if (radarFailureText) {
      return `扫图状态：自动扫图状态机已启动，但${radarFailureText}；继续现场接管，必要时停止自动扫图。`;
    }
    if (plainFreeRoamMapPreviewRefreshFailedForSession.value) {
      const failureText = mapPreviewFailureText(mapPreviewResult.value);
      const reasonSuffix = failureText ? `：${failureText}` : "";
      return `扫图状态：自动扫图状态机已启动，但地图画面刷新失败${reasonSuffix}；当前地图不是自动扫图启动后的新画面。`;
    }
    return "扫图状态：自动扫图状态机已启动，低速运行中，地图和雷达监看中；需要收口时点击停止自动扫图或红色停止。";
  }
  if (freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded" && freeRoamAutonomyResult.value.action === "stop") {
    return "扫图状态：自动扫图停止请求已发送，继续看地图和雷达确认现场收口。";
  }
  if (mapSavedThisSession.value) {
    if (plainFreeRoamSavedMapPreviewRefreshFailed.value) {
      const failureText = mapPreviewFailureText(mapPreviewResult.value);
      const reasonSuffix = failureText ? `：${failureText}` : "";
      return `扫图状态：地图已保存，但最新画面刷新失败${reasonSuffix}；当前画面不是保存后的新图。`;
    }
    return plainFreeRoamSavedMapPreviewFreshForSession.value
      ? "扫图状态：地图已保存，地图画面已自动刷新，可以检查效果。"
      : "扫图状态：地图已保存，刷新地图画面检查效果。";
  }
  if (mapRuntimeStarted.value) {
    const failureText = mapPreviewFailureText(mapPreviewResult.value);
    if (failureText) {
      return `扫图状态：地图记录中，但扫图画面刷新失败：${failureText}；重试刷新扫图画面后再继续保存。`;
    }
  }
  if (keyboardMapWysiwygBlocked.value) {
    return `扫图状态：${mapWysiwygRefreshPendingText()}，等刷新完成后再继续按住移动。`;
  }
  if (keyboardHeldDirection.value) {
    const wheelText = keyboardWheelFeedbackPlainText();
    if (mapWysiwygRefreshPending.value && mapRuntimeStarted.value) {
      return `扫图状态：正在${keyboardDirectionPlainLabel.value}扫图，${mapWysiwygRefreshPendingText()}；${keyboardForwardedPulseProgressText.value}${wheelText}。`;
    }
    if (plainFreeRoamLiveMapPreviewRefreshedForHold.value) {
      return `扫图状态：正在${keyboardDirectionPlainLabel.value}扫图，地图画面已跟随刷新；${keyboardForwardedPulseProgressText.value}${wheelText}。`;
    }
    return `扫图状态：正在${keyboardDirectionPlainLabel.value}扫图，松开即停；${keyboardForwardedPulseProgressText.value}${wheelText}。`;
  }
  if (keyboardControlStatus.value.startsWith("released")) {
    return "扫图状态：已松开，正在发送停止；完成前不要继续移动。";
  }
  if (keyboardStopFailedAfterPulse.value) {
    return "扫图状态：停止请求失败，未证明小车已停止；请点红色停止并现场接管。";
  }
  if (keyboardControlStatus.value.startsWith("stop_sent")) {
    const failureText = mapPreviewFailureText(mapPreviewResult.value);
    if (failureText) {
      return `扫图状态：已停止，但扫图画面刷新失败：${failureText}；重试刷新扫图画面后再保存地图。`;
    }
    if (mapPreviewPending.value && mapRuntimeStarted.value) {
      return "扫图状态：已停止，正在刷新扫图画面。";
    }
    return plainFreeRoamMapPreviewFreshForSession.value
      ? "扫图状态：已停止，地图画面已刷新，可以保存当前地图。"
      : "扫图状态：已停止，先刷新扫图画面，再保存地图。";
  }
  if (keyboardControlArmed.value && canUseKeyboardControl.value) {
    return "扫图状态：键盘已启用，按住方向键/WASD 低速扫图；松开即停。";
  }
  if (mapRuntimeStarted.value) {
    return canArmPlainFreeRoamKeyboard.value
      ? "扫图状态：地图记录中，先启用键盘扫图；启用本身不会移动。"
      : "扫图状态：地图记录中，键盘条件未满足，不能扫图移动。";
  }
  return "扫图状态：等待地图记录状态。";
});
const plainFreeRoamSweepPlanSummary = computed(() => {
  // 这是给 operator 的地图读图辅助，不是自动驾驶承诺；真实移动仍由键盘或后端安全状态机放行。
  const preview = mapPreviewResult.value;
  if (!preview || preview.proxy_status !== "preview_forwarded" || !preview.image_data_url) {
    return "扫地图草图：先刷新地图画面；本页不会自动移动。";
  }
  if (!preview.has_free_cells || plainCellCount(preview, "free") <= 0) {
    return "扫地图草图：地图还没读到可通行区域，先继续建图或刷新。";
  }
  const plan = latestFreeRoamSweepPlanOverlay(latestRobotPoseOverlay());
  if (!plan) {
    return "扫地图草图：等待地图画面和可通行区域。";
  }
  if (freeRoamAutonomyRuntimeActive()) {
    return plan.showStart
      ? "扫地图草图：自动扫图运行中，蛇形草图用于监看覆盖，不是固定路线。"
      : "扫地图草图：自动扫图运行中，等待定位后接入当前位置；草图只作覆盖监看参考。";
  }
  return plan.showStart
    ? "扫地图草图：已从当前位置画出蛇形覆盖草图；不会自动移动。"
    : "扫地图草图：已在地图上画出蛇形覆盖草图；等待定位后接入当前位置，不会自动移动。";
});
const plainFreeRoamCoverageSummary = computed(() => {
  // 像扫地机一样给出“已经扫到多少”的直观反馈；只读地图预览，不触发建图或移动。
  const preview = mapPreviewResult.value;
  const previewLoaded = preview?.proxy_status === "preview_forwarded";
  if (!previewLoaded) {
    if (mapSavedThisSession.value && plainFreeRoamSavedMapPreviewRefreshFailed.value) {
      const failureText = mapPreviewFailureText(mapPreviewResult.value);
      const reasonSuffix = failureText ? `：${failureText}` : "";
      return {
        state: "失败",
        primary: `地图画面刷新失败${reasonSuffix}`,
        secondary: "当前没有保存后的新地图画面可检查。",
        guidance: "地图已保存，但需要重新刷新扫图画面后再检查覆盖效果。",
        barStyle: { "--coverage-known": "0%" },
        quality: "preview_failed",
      };
    }
    if (mapRuntimeStarted.value) {
      const failureText = mapPreviewFailureText(mapPreviewResult.value);
      if (failureText) {
        return {
          state: "失败",
          primary: `扫图画面刷新失败：${failureText}`,
          secondary: "当前没有地图记录中的新画面可检查。",
          guidance: "地图记录仍在运行，重试刷新扫图画面后再继续移动或保存。",
          barStyle: { "--coverage-known": "0%" },
          quality: "preview_failed",
        };
      }
    }
    const guidance = mapRuntimeStarted.value || mapSavedThisSession.value
      ? mapPreviewPending.value && mapSavedThisSession.value
        ? "地图已保存，正在自动刷新最新画面；刷新后检查覆盖效果。"
        : "地图记录已启动，点刷新扫图画面查看最新覆盖。"
      : "当前还没读到地图画面，先开始记录或刷新地图画面。";
    return {
      state: mapPreviewPending.value && mapSavedThisSession.value ? "刷新中" : "待刷新",
      primary: mapPreviewPending.value && mapSavedThisSession.value ? "地图覆盖正在刷新" : "地图覆盖还没读取",
      secondary: "刷新地图画面后显示可通行区域和未知区域。",
      guidance,
      barStyle: { "--coverage-known": "0%" },
      quality: "not_loaded",
    };
  }
  const free = plainCellCount(preview, "free");
  const occupied = plainCellCount(preview, "occupied");
  const unknown = plainCellCount(preview, "unknown");
  const other = plainCellCount(preview, "other");
  const countedTotal = free + occupied + unknown + other;
  const imageTotal = Math.max(0, Math.trunc((preview?.width ?? 0) * (preview?.height ?? 0)));
  const total = countedTotal > 0 ? countedTotal : imageTotal;
  const known = free + occupied + other;
  const knownPercent = total > 0 ? (known / total) * 100 : 0;
  const unknownPercent = total > 0 ? (unknown / total) * 100 : 100;
  const state = free > 0 ? (unknownPercent > 80 ? "待继续" : "已扫出") : "待继续";
  return {
    state,
    primary: free > 0 ? `已扫出 ${free} 个可通行格` : "还没扫出可通行区域",
    secondary: `未知区域 ${percentText(unknownPercent)}，已知区域 ${percentText(knownPercent)}。`,
    guidance: mapRuntimeStarted.value
      ? plainFreeRoamLiveMapPreviewRefreshedForHold.value && keyboardHeldDirection.value
        ? "扫图中地图画面已自动刷新；松开后会再刷新一次用于保存。"
        : "地图记录中；覆盖条是上次刷新结果，点刷新扫图画面才是当前画面。"
      : mapSavedThisSession.value
        ? mapPreviewPending.value
          ? "地图已保存，正在自动刷新最新画面；刷新后检查覆盖效果。"
          : plainFreeRoamSavedMapPreviewFreshForSession.value
          ? "地图已保存，地图画面已自动刷新；现在检查覆盖效果。"
          : "地图已保存，刷新后检查覆盖效果。"
        : "当前显示最近地图画面，开始记录后可边扫边刷新。",
    barStyle: { "--coverage-known": percentText(knownPercent) },
    quality: preview.navigation_quality || (preview.has_free_cells ? "has_free_cells" : "not_loaded"),
  };
});
const plainFreeRoamAutonomyReadiness = computed(() => {
  // 自动扫图需要上车端闭环保护；PC 端这里只展示 readiness，不生成任何运动命令。
  const boundary = robotSummary.value?.safe_command_boundary;
  const policy = boundary?.free_roam_autonomy_policy;
  const preview = mapPreviewResult.value;
  const previewLoaded = preview?.proxy_status === "preview_forwarded";
  const autonomyRunningUnlocked = boundary?.free_roam_autonomy === "ready";
  const autonomyStartReady = boundary?.free_roam_autonomy_start_ready === true || autonomyRunningUnlocked;
  const autonomyLocked = !autonomyStartReady;
  const autonomyReady = autonomyStartReady;
  const hasRuntimeGateRows = Boolean(boundary?.free_roam_autonomy_gates?.length);
  const manualFallbackHint = "自动扫图未开放；当前用人工按住扫图：开始记录 -> 启用键盘 -> 按住方向键/WASD -> 停止 -> 保存地图。";
  const blockers: string[] = [];
  if (!robotApiBaseUrl.value.trim()) {
    blockers.push("默认小车未连接");
  }
  if (!plainManualSafetyConfirmed.value) {
    blockers.push("现场安全确认未勾选");
  }
  if (!mapRuntimeStarted.value) {
    blockers.push("地图记录未启动");
  }
  if (freeRoamMapWysiwygPending.value) {
    blockers.push(mapPreviewPending.value ? "地图画面正在刷新" : "地图状态正在刷新");
  }
  if (!previewLoaded) {
    blockers.push("地图画面未刷新");
  } else if (plainCellCount(preview, "free") <= 0) {
    blockers.push("地图还没有可通行区域");
  }
  if (radarSummary.value.state !== "雷达已运行") {
    blockers.push(radarSummary.value.state);
  }
  if (!autonomyStartReady && !canUseKeyboardControl.value) {
    blockers.push("键盘低速手控条件未满足");
  }
  if (!canSendStop.value) {
    blockers.push("停止兜底暂不可用");
  }
  if (!autonomyStartReady) {
    blockers.push(hasRuntimeGateRows ? "自动扫图真车验证未完成" : "上车端避障和自动停止未验证");
  }
  const policyGates = policy?.required_gates ?? [
    "onboard_watchdog",
    "lidar_obstacle_gate",
    "operator_stop_fallback",
  ];
  const gateLabel = (gate: string): string => {
    // 后端合同保留英文 token 便于测试和集成，普通首屏只显示现场可理解的中文。
    const labels: Record<string, string> = {
      onboard_watchdog: "上车端自动停止",
      lidar_obstacle_gate: "雷达避障",
      fresh_map_preview: "地图刷新",
      operator_stop_fallback: "停止兜底",
      free_roam_hil_artifact: "自动扫图真车验证",
    };
    return labels[gate] ?? gate;
  };
  const gateStateLabel = (state: string): string => {
    if (state === "ready") {
      return "已满足";
    }
    if (state === "blocked") {
      return "未满足";
    }
    return "待验证";
  };
  const gateHintText = (value: string | undefined): string => {
    // 多行 gate 在测试和读屏时会拼成连续文本；补句号避免“停止”“雷达”等跨行误连。
    const text = value?.trim() || "等待上车端报告";
    return /[。！？.!?]$/.test(text) ? text : `${text}。`;
  };
  const runtime = boundary?.free_roam_autonomy_runtime;
  const runtimeReason = runtime?.reason && runtime.reason !== "not_loaded" ? `：${runtime.reason}` : "";
  const runtimeModeText = (() => {
    // runtime state 来自上车端 artifact；这里只做翻译，不把任何状态外推成 PC 自动发车。
    if (!runtime || runtime.status !== "loaded") {
      return "自动扫图状态：未读取上车端 runtime，当前只能人工按住扫图。";
    }
    const motionBoundary = runtime.artifact_only
      ? "当前只是记录模式，不会自己跑；真车自动扫图还要完成安全确认、地图记录、雷达和停止兜底。"
      : runtime.cmd_vel_publish_enabled
      ? "运动发布已解锁，PC 仍等待真车 HIL 记录。"
      : autonomyStartReady
      ? "启动条件已满足；点击开始后由上车端复检相机和雷达，再打开运动双锁。"
      : "运动发布未解锁，不会自己跑。";
    const stateLabels: Record<string, string> = {
      locked: "门禁锁定",
      ready: "等待启动",
      running: "低速直行判断",
      avoiding: "避障换向",
      turning_for_coverage: "原地找新覆盖",
      stopping: "停止中",
      completed: "已完成并要求停止",
    };
    const stateText = stateLabels[runtime.state] ?? runtime.state;
    const stopText = runtime.stop_required ? "，要求停止兜底" : "";
    return `自动扫图状态：${stateText}${runtimeReason}${stopText}；${motionBoundary}`;
  })();
  const nextActionText = (() => {
    // 自动扫图按钮有时只是流程向导；单独写出下一手动作，避免把“未开放”误读成会自己跑。
    if (!robotApiBaseUrl.value.trim()) {
      return "自动扫图下一步：连接默认小车。";
    }
    if (!plainManualSafetyConfirmed.value) {
      return "自动扫图下一步：勾选现场安全确认。";
    }
    if (!mapRuntimeStarted.value) {
      return "自动扫图下一步：开始地图记录。";
    }
    if (freeRoamMapWysiwygPending.value || !plainFreeRoamMapPreviewFreshForSession.value) {
      return "自动扫图下一步：刷新扫图画面。";
    }
    if (radarSummary.value.state !== "雷达已运行") {
      return plainRadarRequiresRefresh.value ? "自动扫图下一步：刷新雷达。" : "自动扫图下一步：启动雷达。";
    }
    if (!canSendStop.value) {
      return "自动扫图下一步：补齐停止兜底。";
    }
    return autonomyReady && blockers.length === 0
      ? "自动扫图下一步：点击开始自动扫图（低速）。"
      : "自动扫图下一步：先用人工按住扫图完成本轮地图。";
  })();
  const contractGateRows = boundary?.free_roam_autonomy_gates?.length
    ? boundary.free_roam_autonomy_gates.map((gate) => ({
      id: gate.id,
      label: gate.label || gateLabel(gate.id),
      state: gateStateLabel(gate.state),
      hint: gateHintText(gate.next_action || gate.evidence),
    }))
    : policyGates.map((gate) => ({
      id: gate,
      label: gateLabel(gate),
      state: "待验证",
      hint: gateHintText(undefined),
    }));
  const speedLimit = policy?.max_speed_mps ?? manualSpeedLimit.value;
  const runtimeLimit = policy?.max_runtime_s ?? 60;
  return {
    state: autonomyReady && blockers.length === 0 ? "已就绪" : autonomyReady ? "待处理" : "未满足",
    buttonLabel: freeRoamAutonomyPending.value && freeRoamAutonomyPendingAction.value === "start"
      ? "启动中"
      : autonomyReady && freeRoamMapWysiwygPending.value ? "等待地图刷新"
      : autonomyReady && blockers.length ? plainFreeRoamAutonomyGuideButtonLabel.value
      : autonomyLocked ? plainFreeRoamManualGuideButtonLabel.value : "开始自动扫图（低速）",
    // ready 后才走固定上车状态机 start；未 ready 时按钮仍只做流程定位。
    disabled: autonomyReady ? (freeRoamAutonomyPending.value || freeRoamMapWysiwygPending.value) : false,
    hint: autonomyLocked
      ? manualFallbackHint
      : freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded" && freeRoamAutonomyResult.value.action === "start"
      ? freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded" && freeRoamAutonomyResult.value.action === "start"
        ? radarRefreshFailureLabel(radarRefreshResult.value)
          ? `自动扫图状态机已启动；${radarRefreshFailureLabel(radarRefreshResult.value)}，PC 继续保留停止兜底。`
          : plainFreeRoamMapPreviewRefreshFailedForSession.value
            ? `自动扫图状态机已启动；地图画面刷新失败${mapPreviewFailureText(mapPreviewResult.value) ? `：${mapPreviewFailureText(mapPreviewResult.value)}` : ""}，PC 继续保留停止兜底。`
          : "自动扫图状态机已启动；PC 继续监看地图、雷达和停止兜底。"
        : "自动扫图状态机已启动；PC 继续监看地图、雷达和停止兜底。"
      : blockers.length
        ? `还差：${blockers.slice(0, 3).join("、")}。`
      : autonomyRunningUnlocked
        ? "上车端自动扫图已就绪并已解锁；PC 继续监看地图、雷达和停止兜底。"
        : "上车端自动扫图已就绪；点击后只启动上车状态机，PC 继续负责地图/雷达所见即所得监看和停止兜底。",
    nextActionText,
    blockers: blockers.slice(0, 4),
    gateRows: contractGateRows,
    runtimeText: runtimeModeText,
    policyText: hasRuntimeGateRows
      ? `上限 ${speedLimit.toFixed(2)} m/s，最长 ${runtimeLimit}s，正在读取上车端自动扫图门禁。`
      : `上限 ${speedLimit.toFixed(2)} m/s，最长 ${runtimeLimit}s，必须先通过 ${policyGates.slice(0, 3).map(gateLabel).join("、")}。`,
  };
});
const plainFreeRoamMappingSteps = computed(() => {
  // 步骤条只表达本地向导状态；真正动作仍由每个固定按钮和后端 gate 执行。
  const safetyReady = plainManualSafetyConfirmed.value;
  const mappingStarted = mapRuntimeStarted.value || mapSavedThisSession.value;
  const keyboardReady = canUseKeyboardControl.value;
  const keyboardMoving = keyboardHeldDirection.value !== null;
  const stopObserved = keyboardStopSettledAfterPulse.value || keyboardControlStatus.value.startsWith("stop_sent");
  const saved = mapSavedThisSession.value;
  const autoStarted = freeRoamAutonomyStartedThisSession.value;
  const autoStopped = freeRoamAutonomyStoppedThisSession.value;
  const autoStartFailed = freeRoamAutonomyResult.value?.proxy_status === "autonomy_failed" && freeRoamAutonomyResult.value.action === "start";
  const autoStopFailed = freeRoamAutonomyResult.value?.proxy_status === "autonomy_failed" && freeRoamAutonomyResult.value.action === "stop";
  const autoFailureText = freeRoamAutonomyFailureText(freeRoamAutonomyResult.value);
  const autoFailureSuffix = autoFailureText ? `：${autoFailureText}` : "";
  return [
    {
      id: "confirm",
      label: "安全确认",
      state: safetyReady ? "已完成" : "待确认",
      hint: safetyReady ? "现场已确认可以低速扫图" : "先勾选现场安全确认",
    },
    {
      id: "start",
      label: "启动记录",
      state: mappingStarted ? "已完成" : safetyReady ? "可执行" : "待确认",
      hint: mappingStarted ? "地图记录已启动" : safetyReady ? "点击开始扫地式建图" : "需要先做安全确认",
    },
    {
      id: "drive",
      label: "低速扫图",
      state: saved || autoStopped ? "已完成" : autoStartFailed ? "失败" : autoStarted ? "自动扫图中" : keyboardMoving ? "手控中" : keyboardReady && mappingStarted ? "可手控" : mappingStarted ? "待手控" : "待完成",
      hint: saved
        ? "扫图已收口，检查地图效果"
        : autoStopped
          ? "自动扫图已停止，检查停止后的地图画面"
        : autoStartFailed
          ? `自动扫图启动失败${autoFailureSuffix}，继续人工按住扫图或重试`
        : autoStarted
          ? "自动扫图运行中，PC 监看地图和雷达"
        : keyboardMoving
          ? `正在${keyboardDirectionPlainLabel.value}，松开即停`
          : keyboardReady && mappingStarted
            ? "启用键盘后按住方向键/WASD 扫一圈"
            : mappingStarted ? plainKeyboardNextActionSummary.value : "先启动地图记录",
    },
    {
      id: "stop",
      label: "停止收口",
      state: saved || stopObserved || autoStopped ? "已完成" : autoStopFailed ? "失败" : autoStarted ? "可停止" : mappingStarted ? "可执行" : "待完成",
      hint: saved ? "扫图已停止并保存" : stopObserved ? "停止已发送" : autoStopped ? "自动扫图已停止，刷新画面后保存" : autoStopFailed ? `自动扫图停止失败${autoFailureSuffix}，先点红色停止并现场接管` : autoStarted ? "点击停止自动扫图或红色停止" : mappingStarted ? "松开按键或点击停止" : "先启动地图记录",
    },
    {
      id: "save",
      label: "保存地图",
      state: saved ? "已保存" : canSavePlainFreeRoamMapping.value ? "可保存" : "待完成",
      hint: saved
        ? mapPreviewPending.value
          ? "已保存，正在刷新地图画面"
          : plainFreeRoamSavedMapPreviewFreshForSession.value
          ? "已保存，地图画面已自动刷新，可以检查效果"
          : "已保存，刷新地图画面检查效果"
        : canSavePlainFreeRoamMapping.value
          ? "扫图结束后保存刚刷新过的地图"
          : freeRoamAutonomySaveBlocked.value ? "先停止自动扫图，再保存地图"
          : mapRuntimeStarted.value ? "先刷新扫图画面，再保存地图" : "启动地图记录后才能保存",
    },
  ];
});
const keyboardForwardedPulseProgressText = computed(() => {
  // 验证必须来自同一次按住会话；历史最佳只用于提示，不把分散单脉冲累加成连续手控。
  if (keyboardManualPulseObserved.value) {
    return `已连续 ${KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES}/${KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES} 次`;
  }
  if (keyboardHeldDirection.value) {
    return `本次按住 ${keyboardHoldPulseCount.value}/${KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES} 次`;
  }
  return `最佳连续 ${keyboardVerifiedPulseCount.value}/${KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES} 次`;
});

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

function manualDirectionPlainLabel(direction: string): string {
  // 上次方向来自内部 enum；普通首屏统一翻译成现场能听懂的中文。
  switch (direction) {
    case "forward":
      return "前进";
    case "back":
      return "后退";
    case "left":
      return "左转";
    case "right":
      return "右转";
    default:
      return "未记录";
  }
}

function keyboardStopReasonPlainLabel(reason: string): string {
  // 停止原因只解释 operator 关心的入口，避免把底层事件名直接暴露到普通界面。
  if (reason.includes("key_released")) {
    return "松开键盘";
  }
  if (reason.includes("screen_button_released") || reason.includes("free_roam_screen_button_released")) {
    return "松开屏幕方向键";
  }
  if (reason.includes("screen_button_left") || reason.includes("free_roam_screen_button_left")) {
    return "手指移出方向键";
  }
  if (reason.includes("screen_button_cancelled") || reason.includes("free_roam_screen_button_cancelled")) {
    return "方向键触控取消";
  }
  if (reason.includes("window_blur") || reason.includes("focus")) {
    return "窗口或面板失焦";
  }
  if (reason.includes("page_hidden")) {
    return "页面隐藏";
  }
  if (reason.includes("button_stop") || reason.includes("mapping_stop")) {
    return "点击停止";
  }
  if (reason.includes("direction_changed")) {
    return "切换方向";
  }
  return "停止已触发";
}

const plainKeyboardLastStopSummary = computed(() => {
  // 连续手控松开后要留下一句“刚才停的是哪个方向”，否则现场很难复核按住-松开闭环。
  if (keyboardHeldDirection.value) {
    return `正在按住：${keyboardDirectionPlainLabel.value}`;
  }
  if (keyboardLastDirection.value === "not_loaded") {
    return "上次方向：未记录。";
  }
  const directionText = manualDirectionPlainLabel(keyboardLastDirection.value);
  if (!keyboardLastStopReason.value || keyboardLastStopReason.value === "not_loaded") {
    return `上次方向：${directionText}；等待停止收口。`;
  }
  return `上次方向：${directionText}；停止原因：${keyboardStopReasonPlainLabel(keyboardLastStopReason.value)}。`;
});

function keyboardWheelFeedbackPlainText(): string {
  const values = keyboardLastWheelFeedbackValues.value;
  if (!values) {
    return "";
  }
  const left = values.wheel_feedback_latest_raw_left ?? values.wheel_feedback_latest_left_speed ?? "not_loaded";
  const right = values.wheel_feedback_latest_raw_right ?? values.wheel_feedback_latest_right_speed ?? "not_loaded";
  if (left === "not_loaded" && right === "not_loaded") {
    return "";
  }
  const nonzero = values.wheel_feedback_lr_nonzero_proven === "true" || values.wheel_feedback_nonzero_observed === "true";
  return nonzero
    ? `；轮速 L/R=${left}/${right}，非零已读到`
    : `；轮速 L/R=${left}/${right}，等待非零`;
}

function keyboardWheelFeedbackState(): "未读取" | "等待非零" | "非零已读到" {
  // 地图上的扫图方向 marker 需要结构化轮速证据，避免只靠短文案判断 wheel raw L/R 是否已非零。
  const values = keyboardLastWheelFeedbackValues.value;
  if (!values) {
    return "未读取";
  }
  const left = values.wheel_feedback_latest_raw_left ?? values.wheel_feedback_latest_left_speed ?? "not_loaded";
  const right = values.wheel_feedback_latest_raw_right ?? values.wheel_feedback_latest_right_speed ?? "not_loaded";
  if (left === "not_loaded" && right === "not_loaded") {
    return "未读取";
  }
  return values.wheel_feedback_lr_nonzero_proven === "true" || values.wheel_feedback_nonzero_observed === "true" ? "非零已读到" : "等待非零";
}

function keyboardWheelFeedbackMapSuffix(): string {
  // 地图 marker 空间有限，只显示轮速结论；完整 L/R 数值继续放在状态行和 aria 说明里。
  const values = keyboardLastWheelFeedbackValues.value;
  if (!values) {
    return "";
  }
  const left = values.wheel_feedback_latest_raw_left ?? values.wheel_feedback_latest_left_speed ?? "not_loaded";
  const right = values.wheel_feedback_latest_raw_right ?? values.wheel_feedback_latest_right_speed ?? "not_loaded";
  if (left === "not_loaded" && right === "not_loaded") {
    return "";
  }
  const nonzero = values.wheel_feedback_lr_nonzero_proven === "true" || values.wheel_feedback_nonzero_observed === "true";
  return nonzero ? "，轮速非零" : "，轮速待非零";
}

function keyboardLastStopMapSuffix(): string {
  // 松开后地图 marker 继续保留上次方向，方便现场把“已停”与刚才的按住动作对上。
  if (keyboardLastDirection.value === "not_loaded") {
    return "";
  }
  return `：${manualDirectionPlainLabel(keyboardLastDirection.value)}${keyboardWheelFeedbackMapSuffix()}`;
}

function keyboardLastStopMapAria(): string {
  // aria 里保留停止原因和 L/R，地图可见信息与键盘状态行保持一致。
  if (keyboardLastDirection.value === "not_loaded") {
    return "";
  }
  const direction = `，上次方向${manualDirectionPlainLabel(keyboardLastDirection.value)}`;
  const reason = keyboardLastStopReason.value && keyboardLastStopReason.value !== "not_loaded"
    ? `，停止原因${keyboardStopReasonPlainLabel(keyboardLastStopReason.value)}`
    : "";
  const wheel = keyboardWheelFeedbackPlainText().replace(/^；/, "，");
  return `${direction}${reason}${wheel}`;
}

const plainKeyboardWheelFeedbackSummary = computed(() => {
  // 最近键盘脉冲的轮速读数要在松开后继续可见，方便现场复核连续手控是否真的带出底盘反馈。
  const values = keyboardLastWheelFeedbackValues.value;
  if (!values) {
    return "";
  }
  const left = values.wheel_feedback_latest_raw_left ?? values.wheel_feedback_latest_left_speed ?? "not_loaded";
  const right = values.wheel_feedback_latest_raw_right ?? values.wheel_feedback_latest_right_speed ?? "not_loaded";
  if (left === "not_loaded" && right === "not_loaded") {
    return "";
  }
  const frameCount = values.wheel_feedback_nonzero_frame_count ?? values.feedback_during_motion_t1001_frame_count ?? "0";
  const nonzero = values.wheel_feedback_lr_nonzero_proven === "true" || values.wheel_feedback_nonzero_observed === "true";
  return nonzero
    ? `键盘轮速：L/R=${left}/${right}，非零已读到 ${frameCount} 帧。`
    : `键盘轮速：L/R=${left}/${right}，还没读到非零。`;
});

const plainKeyboardLiveStatus = computed(() => {
  // 这行只解释本地键盘循环状态，不作为任何控制 gate 或成功证据。
  if (keyboardHeldDirection.value) {
    const wheelText = keyboardWheelFeedbackPlainText();
    if (keyboardManualPulseObserved.value) {
      return `正在${keyboardDirectionPlainLabel.value}，${keyboardForwardedPulseProgressText.value}${wheelText}；松开后完成停止收口。`;
    }
    return `正在${keyboardDirectionPlainLabel.value}，松开即停；${keyboardForwardedPulseProgressText.value}${wheelText}。`;
  }
  if (keyboardControlStatus.value.startsWith("blocked_keyboard_pulse_failed")) {
    return "键盘手控请求未成功，未记为已验证。";
  }
  if (keyboardControlStatus.value.startsWith("blocked_keyboard_stop_failed")) {
    return "键盘停止请求未成功，未记为已验证。";
  }
  if (keyboardControlArmed.value && keyboardControlStatus.value.startsWith("released")) {
    return "已松开，正在发送停止。";
  }
  if (keyboardStopSettledAfterPulse.value) {
    return `键盘手控已验证，${keyboardForwardedPulseProgressText.value}，停止已发送；需要继续移动可按住方向键。`;
  }
  if (keyboardControlArmed.value && keyboardControlStatus.value.startsWith("stop_sent")) {
    return "已停止，按住方向键可继续点动。";
  }
  if (keyboardVerifiedPulseCount.value > 0 && !keyboardManualPulseObserved.value) {
    return `${keyboardForwardedPulseProgressText.value}，需同一次按住达到 ${KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES} 次。`;
  }
  if (keyboardControlArmed.value && canUseKeyboardControl.value) {
    return "等待按键，按住才会动。";
  }
  if (canUseKeyboardControl.value) {
    return "未启用，先点启用键盘。";
  }
  return plainKeyboardMissingSummary.value || "键盘手控暂未满足。";
});

const plainKeyboardControlGuide = computed(() => {
  // 普通首屏需要说明所有自动停止触发，避免现场误以为只有松开按键才会停。
  const intervalSeconds = (keyboardJogIntervalMs.value / 1000).toFixed(2).replace(/0$/, "");
  return `W/A/S/D 或方向键：前进、左转、后退、右转。按住会持续低速移动，约每 ${intervalSeconds} 秒续一次；松开、窗口失焦或切页面都会停。`;
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

function formatPlainVoltage(value: string | undefined): string {
  // 普通首屏只需要供电读数的大致判断；原始长小数仍留在高级诊断和接口里。
  if (!value || value === "not_loaded") {
    return "";
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return "";
  }
  return (Math.round(parsed * 100) / 100).toFixed(2).replace(/\.?0+$/, "");
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

const plainDeliveryMapWysiwygPending = computed(() => mapPreviewPending.value || mapRefreshPending.value);

const plainDeliveryConfirmMissingLabels = computed(() => {
  // 最终确认区要先提示材料缺口，再提示现场勾选项，避免现场在按钮之间来回猜。
  const confirmations = deliveryOperatorConfirmations.value;
  const materialReady = Boolean(deliveryOperatorVideoRef.value.trim() && deliveryOperatorRouteMapRef.value.trim());
  return [
    { label: "本轮行程", ready: deliveryNav2GoalReady.value },
    { label: "地图画面刷新完成", ready: !plainDeliveryMapWysiwygPending.value },
    { label: "本轮行程材料", ready: !deliveryNav2GoalReady.value || deliveryRouteMapMatchesFreshNav2.value },
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

function usableMaterialRef(value: string | undefined): string {
  // delivery latest 和 operator summary 都可能用 not_loaded 占位；恢复材料时只能采用真实 ref。
  const trimmed = value?.trim() ?? "";
  return trimmed && trimmed !== "not_loaded" ? trimmed : "";
}

function deliveryLatestDraftVisualRefs(): { externalVideoRef: string; cameraArtifactRef: string; routeMapRef: string } {
  // delivery latest 是当前真实上位机里最容易保留画面草稿的位置；这里只读 ref，不当成送达确认。
  const refs = deliveryLatestResult.value?.delivery_material_refs;
  return {
    externalVideoRef: usableMaterialRef(refs?.external_video_ref) || usableMaterialRef(refs?.camera_artifacts_ref),
    cameraArtifactRef: usableMaterialRef(refs?.camera_artifacts_ref) || usableMaterialRef(refs?.external_video_ref),
    routeMapRef: usableMaterialRef(refs?.route_map_ref),
  };
}

const deliveryDraftVisualMaterialReady = computed(() => {
  // 恢复 first-jog 至少要有可追溯的画面 ref；否则仍要求现场重新记录画面。
  const refs = deliveryLatestDraftVisualRefs();
  return deliveryDraftMaterialPresent() && Boolean(refs.externalVideoRef && refs.cameraArtifactRef);
});

function plainDeliveryConfirmBlockedLabel(missingLabels: string[]): string {
  // 已有草稿后，按钮直接指向下一组人工确认，避免现场只看到抽象数量。
  if (missingLabels.includes("本轮行程")) {
    if (plainTripRadarBlocked.value) {
      if (plainRadarStartUnavailable.value) {
        return "确认送达（先配置雷达）";
      }
      if (plainRadarRequiresRefresh.value) {
        return "确认送达（先刷新雷达）";
      }
      if (plainTripNeedsFreshRunAfterRadar.value) {
        return "确认送达（先雷达再行程）";
      }
      return "确认送达（先启动雷达）";
    }
    return "确认送达（先重新行程）";
  }
  if (missingLabels.includes("地图画面刷新完成")) {
    return "确认送达（等待地图刷新）";
  }
  if (missingLabels.includes("本轮行程材料")) {
    return "确认送达（先更新行程材料）";
  }
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
  // 按钮禁用时也直接显示下一步动作；可提交时明确“不发车”，避免送达收口被误解成运动命令。
  if (operatorReportPending.value || deliveryCompletionPending.value) {
    return "确认中";
  }
  if (deliverySuccessReady.value) {
    return "送达已完成";
  }
  const missingLabels = plainDeliveryConfirmMissingLabels.value;
  const missingCount = missingLabels.length;
  if (missingCount > 0) {
    return plainDeliveryConfirmBlockedLabel(missingLabels);
  }
  return "确认送达（不发车）";
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

const plainDeliveryAllConfirmedButtonLabel = computed(() => (
  deliveryOperatorConfirmationReady.value ? "全部确认已勾选" : "全部已确认"
));

const deliveryGateBlockedReasons = computed(() => {
  // 送达缺口可能来自 latest、check 或 complete；合并后给现场人员一个稳定清单。
  return Array.from(new Set([
    ...(deliveryCompletionResult.value?.blocked_reasons ?? []),
    ...(deliveryCompletionResult.value?.missing_required_material ?? []),
    ...(deliveryGapCheckResult.value?.blocked_reasons ?? []),
    ...(deliveryGapCheckResult.value?.missing_required_material ?? []),
    ...(deliveryLatestResult.value?.blocked_reasons ?? []),
    ...(deliveryLatestResult.value?.missing_required_material ?? []),
  ]));
});

function deliveryGateMissing(token: string): boolean {
  // 后端缺口字段有时是精确字段，有时是 required material 名称；这里仅做保守包含判断。
  return deliveryGateBlockedReasons.value.some((reason) => reason.includes(token));
}

const plainDeliveryGateMissingSummary = computed(() => {
  // 把上位机 delivery gate 缺口翻成普通话；字段名留在高级诊断，避免普通首屏变成接口面板。
  if (deliverySuccessReady.value) {
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
  if (plainDeliveryMapWysiwygPending.value) {
    return "等待地图刷新";
  }
  const missingCount = deliveryGateBlockedReasons.value.length;
  return missingCount > 0 ? `复查送达条件（还差 ${missingCount} 项，不确认）` : "复查送达条件（不确认）";
});

const plainDeliveryNextActionSummary = computed(() => {
  // 送达 gate 缺项很多时，普通首屏只给一个下一步，避免现场人员在多按钮之间来回猜。
  if (deliverySuccessReady.value) {
    return "下一步：送达已完成，可继续键盘手控或结束本轮。";
  }
  if (!deliveryNav2GoalReady.value) {
    // 旧行程或未证实行程会阻塞送达，但已保存的材料草稿仍可复用，避免现场误以为要从零准备。
    const draftReusePrefix = deliveryDraftMaterialPresent() ? "送达材料草稿已保存，可复用；" : "";
    if (plainTripRadarBlocked.value) {
      return `${draftReusePrefix}${plainRadarDeliveryNextAction(plainTripNeedsFreshRunAfterRadar.value)}`;
    }
    if (plainTripHasFreshUnprovenControlEvidence.value) {
      return `${draftReusePrefix}下一步：重新执行完整行程。`;
    }
    if (plainTripHasFreshIncompleteEvidence.value) {
      return `${draftReusePrefix}下一步：重新读取或执行完整行程。`;
    }
    if (plainTripLatestNotProvenEvidence.value) {
      return `${draftReusePrefix}下一步：检查或重新执行完整行程。`;
    }
    return plainTripHasSucceededEvidence.value ? `${draftReusePrefix}下一步：重新执行本轮行程。` : `${draftReusePrefix}下一步：先完成行程。`;
  }
  if (plainDeliveryMapWysiwygPending.value) {
    return `下一步：等待${plainTripMapWysiwygWaitText()}。`;
  }
  if (!deliveryRouteMapMatchesFreshNav2.value) {
    return "下一步：更新行程材料。";
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

function nav2GoalSucceeded(values: Record<string, string> | undefined): boolean {
  return (values?.nav2_status ?? values?.status) === "goal_succeeded";
}

function nav2EvidenceStatus(values: Record<string, string> | undefined): string {
  return values?.nav2_status ?? values?.status ?? "";
}

function directNav2ExecutionFallbackValues(): Record<string, string> | undefined {
  // 直接执行失败可能只返回 proxy 失败和原因；首屏需要保留本次图上终点，但不能伪造成成功证据。
  const result = navGoalExecutionResult.value;
  if (!result || Object.keys(result.goal_execution_key_values ?? {}).length > 0) {
    return undefined;
  }
  if (result.proxy_status !== "execution_failed" && result.proxy_status !== "execution_rejected") {
    return undefined;
  }
  const attemptedGoal = navGoalExecutionAttemptGoal.value ?? result.goal_request;
  const fallbackValues: Record<string, string> = {
    status: "goal_failed",
    result_status: result.failure_reason || result.proxy_status,
    failure_reason: result.failure_reason || result.proxy_status,
    delivery_success: "false",
  };
  if (attemptedGoal?.goal_frame_id === "map") {
    fallbackValues.goal_frame_id = "map";
    fallbackValues.goal_x = String(attemptedGoal.goal_x);
    fallbackValues.goal_y = String(attemptedGoal.goal_y);
  }
  return fallbackValues;
}

function nav2FeedbackSampleCount(values: Record<string, string> | undefined): number {
  // 完整行程不仅要 success，还要读到执行过程反馈样本；缺字段按 0 处理，避免把空摘要当成完整路线。
  const parsed = Number(values?.feedback_sample_count ?? values?.nav2_feedback_sample_count ?? "0");
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

function explicitFalseKeyValue(value: string | undefined): boolean {
  // 上位机 live latest 会把未证明真车执行写成字符串 false；这类明确信号不能被 success 文案盖过去。
  return value?.trim().toLowerCase() === "false";
}

function nav2ExecutionControlProven(values: Record<string, string> | undefined): boolean {
  // goal_succeeded 只说明 action 返回成功；完整路线还必须没有“执行/真车控制未证明”的显式 false。
  return !explicitFalseKeyValue(values?.nav2_goal_execution_proven)
    && !explicitFalseKeyValue(values?.robot_control_executed);
}

function plainTripFailureReasonText(result: { failure_reason?: string } | null | undefined, values: Record<string, string> | undefined): string {
  // 地图 marker 空间有限；把常见后端英文原因翻译成普通用户能判断的短原因。
  const raw = [
    result?.failure_reason,
    values?.failure_reason,
    values?.result_status,
    nav2EvidenceStatus(values),
  ].find((item) => item && item !== "not_loaded" && item !== "goal_succeeded") ?? "";
  const reason = raw.toLowerCase();
  if (!reason) {
    return "";
  }
  if (reason.includes("planner")) {
    return "规划失败";
  }
  if (reason.includes("timeout")) {
    return "等待超时";
  }
  if (reason.includes("locked") || reason.includes("not_ready") || reason.includes("not ready") || reason.includes("unavailable")) {
    return "行程未开放";
  }
  if (reason.includes("obstacle") || reason.includes("collision")) {
    return "被障碍挡住";
  }
  if (reason.includes("controller") || reason.includes("control")) {
    return "控制失败";
  }
  if (reason.includes("rejected") || reason.includes("preflight") || reason.includes("blocked")) {
    return "条件未通过";
  }
  if (reason.includes("abort") || reason.includes("cancel")) {
    return "已中止";
  }
  return "执行失败";
}

function directNav2ExecutionValues(): Record<string, string> | undefined {
  // 地图和行程卡只展示直接执行/最近执行结果；delivery 摘要只用于收口，不反推地图执行进度。
  return directNav2ExecutionFallbackValues()
    ?? navGoalExecutionResult.value?.goal_execution_key_values
    ?? navGoalExecutionLatestResult.value?.goal_execution_key_values;
}

function nav2ExecutionComplete(values: Record<string, string> | undefined): boolean {
  return nav2GoalSucceeded(values) && nav2FeedbackSampleCount(values) > 0 && nav2ExecutionControlProven(values);
}

function nav2EvidenceValues(): Array<Record<string, string> | undefined> {
  // 直接 Nav2 执行/最近结果是本轮行程的权威来源；一旦已读到，就不能再用 delivery latest 的旧摘要补完成。
  const directValue = directNav2ExecutionValues();
  if (directValue) {
    return [directValue];
  }
  return [
    deliveryLatestResult.value?.delivery_key_values,
    deliveryGapCheckResult.value?.delivery_key_values,
    deliveryCompletionResult.value?.delivery_key_values,
  ];
}

function evidenceAgeMs(values: Record<string, string> | undefined): number | null {
  const actionGeneratedAt = parsePositiveMillis(values?.generated_at_ms ?? values?.nav2_generated_at_ms);
  if (actionGeneratedAt === null) {
    return null;
  }
  const referenceAt = parsePositiveMillis(values?.response_generated_at_ms) ?? Date.now();
  return Math.max(0, referenceAt - actionGeneratedAt);
}

function evidenceIsStale(values: Record<string, string> | undefined): boolean {
  const ageMs = evidenceAgeMs(values);
  return ageMs !== null && ageMs >= EVIDENCE_STALE_AFTER_MS;
}

function deliveryResultSucceeded(result: RobotControlDeliveryCompleteResponse | RobotControlDeliveryLatestResponse | null): boolean {
  return result?.delivery_success === true;
}

function deliveryResultRouteMapRef(result: RobotControlDeliveryCompleteResponse | RobotControlDeliveryLatestResponse | null): string {
  // latest 会带 operator report 的 route/map ref；complete 响应通常只带 key values，因此要兼容两种形状。
  if (!result) {
    return "";
  }
  const latestRefs = "delivery_material_refs" in result ? result.delivery_material_refs : null;
  return latestRefs?.route_map_ref?.trim()
    || result.delivery_key_values.route_map_ref?.trim()
    || result.delivery_key_values.nav2_evidence_ref?.trim()
    || result.delivery_key_values.evidence_ref?.trim()
    || "";
}

function deliveryResultMatchesFreshNav2(result: RobotControlDeliveryCompleteResponse | RobotControlDeliveryLatestResponse | null): boolean {
  // delivery_success 只能证明同一轮行程收口；latest 带旧 route/map ref 时不能点亮本轮完成。
  const freshRef = freshNav2RouteMapRef.value;
  if (!freshRef) {
    return true;
  }
  const resultRouteRef = deliveryResultRouteMapRef(result);
  if (resultRouteRef) {
    return resultRouteRef === freshRef;
  }
  return result === deliveryCompletionResult.value && deliveryRouteMapMatchesFreshNav2.value;
}

function deliveryResultReadyForCurrentRun(result: RobotControlDeliveryCompleteResponse | RobotControlDeliveryLatestResponse | null): boolean {
  // delivery success 也必须是当前证据；latest 还必须和本轮 Nav2 行程材料对齐。
  return deliveryResultSucceeded(result)
    && !evidenceIsStale(result?.delivery_key_values)
    && deliveryResultMatchesFreshNav2(result);
}

function deliveryCompletionFailedForCurrentRun(result: RobotControlDeliveryCompleteResponse | null): boolean {
  // 只有本页刚提交的 delivery complete 失败才贴回地图；latest 读取失败不能污染当前到达 marker。
  if (!result || result.delivery_success === true || evidenceIsStale(result.delivery_key_values)) {
    return false;
  }
  return result.proxy_status !== "completion_forwarded" || result.status === "blocked";
}

function deliveryCompletionFailureText(result: RobotControlDeliveryCompleteResponse | null): string {
  // 普通首屏给短原因；完整 blocked/missing 字段仍在送达区和高级诊断里。
  if (!deliveryCompletionFailedForCurrentRun(result)) {
    return "";
  }
  return result?.failure_reason || result?.missing_required_material?.[0] || result?.blocked_reasons?.[0] || result?.status || result?.proxy_status || "delivery_completion_failed";
}

const plainTripHasSucceededEvidence = computed(() => nav2EvidenceValues().some((values) => nav2GoalSucceeded(values)));
const plainTripHasFreshUnprovenControlEvidence = computed(() => nav2EvidenceValues().some((values) => (
  nav2GoalSucceeded(values) && nav2FeedbackSampleCount(values) > 0 && !nav2ExecutionControlProven(values) && !evidenceIsStale(values)
)));
const plainTripHasFreshIncompleteEvidence = computed(() => nav2EvidenceValues().some((values) => (
  nav2GoalSucceeded(values) && nav2FeedbackSampleCount(values) === 0 && !evidenceIsStale(values)
)));
const plainTripLatestNotProvenEvidence = computed(() => {
  // 直接执行或 latest 已经读到失败时，要告诉普通用户“未通过”，不能继续显示成“没读到”。
  const values = directNav2ExecutionValues();
  const status = nav2EvidenceStatus(values);
  const directFailed = navGoalExecutionResult.value?.proxy_status === "execution_failed"
    || navGoalExecutionResult.value?.proxy_status === "execution_rejected";
  return (directFailed || navGoalExecutionLatestResult.value?.proxy_status === "latest_loaded")
    && Boolean(status)
    && status !== "not_loaded"
    && status !== "goal_succeeded";
});
function plainTripFailureSummaryText(): string {
  // 行程失败原因要和地图 marker 同口径，避免地图说“规划失败”、行程卡只说“未通过”。
  const reason = plainTripFailureReasonText(navGoalExecutionResult.value ?? navGoalExecutionLatestResult.value, directNav2ExecutionValues());
  return reason
    ? `最近行程未通过（${reason}），需要检查或重新执行完整行程。`
    : "最近行程未通过，需要检查或重新执行完整行程。";
}
function plainTripFailureShortText(): string {
  const reason = plainTripFailureReasonText(navGoalExecutionResult.value ?? navGoalExecutionLatestResult.value, directNav2ExecutionValues());
  return reason ? `最近行程未通过（${reason}）` : "最近行程未通过";
}
const plainTripNeedsFreshRunAfterRadar = computed(() => {
  // 雷达未运行时如果已经读到旧/失败/不完整行程，现场需要先恢复传感器，再重新跑本轮路线。
  return plainTripHasFreshIncompleteEvidence.value
    || plainTripHasFreshUnprovenControlEvidence.value
    || plainTripHasSucceededEvidence.value
    || plainTripLatestNotProvenEvidence.value;
});
const deliverySuccessReady = computed(() => (
  deliveryResultReadyForCurrentRun(deliveryCompletionResult.value) || deliveryResultReadyForCurrentRun(deliveryLatestResult.value)
));
const deliverySuccessEvidenceIsStale = computed(() => (
  [deliveryCompletionResult.value, deliveryLatestResult.value].some((result) => deliveryResultSucceeded(result) && evidenceIsStale(result?.delivery_key_values))
));
const deliverySuccessEvidenceRouteMismatch = computed(() => (
  [deliveryCompletionResult.value, deliveryLatestResult.value].some((result) => (
    deliveryResultSucceeded(result)
    && !evidenceIsStale(result?.delivery_key_values)
    && !deliveryResultMatchesFreshNav2(result)
  ))
));

const deliveryNav2GoalReady = computed(() => {
  // 本轮完成只接受未过期且带反馈样本的 goal_succeeded；旧/空摘要只能作为提示材料。
  return nav2EvidenceValues().some((values) => nav2ExecutionComplete(values) && !evidenceIsStale(values));
});

const freshNav2RouteMapRef = computed(() => {
  // 送达材料必须引用当前新鲜 Nav2 execution，避免旧草稿 route/map ref 被误当成本轮证据。
  const values = nav2EvidenceValues().find((item) => nav2ExecutionComplete(item) && !evidenceIsStale(item));
  const evidenceRef = values?.evidence_ref ?? "";
  return evidenceRef && evidenceRef !== "not_loaded" ? evidenceRef : "";
});

const deliveryRouteMapMatchesFreshNav2 = computed(() => {
  // 部分后端只返回状态不返回 evidence_ref；没有可比 ref 时只保留“本轮行程”新鲜度 gate。
  const freshRef = freshNav2RouteMapRef.value;
  return !freshRef || deliveryOperatorRouteMapRef.value.trim() === freshRef;
});

const plainDeliverySummary = computed(() => {
  // 普通首屏只做收口状态提示；按钮只读 latest 或复算缺口，不提交送达确认。
  const deliveryConfirmed = deliverySuccessReady.value;
  if (deliveryCompletionPending.value) {
    return { state: "确认中", hint: "正在提交送达确认；不会发车，结果返回前先保持现场接管。" };
  }
  if (deliveryLatestPending.value || deliveryGapCheckPending.value) {
    return { state: "检查中", hint: "正在读取最近行程和送达状态；不会发车。" };
  }
  if (deliveryConfirmed) {
    return { state: "已送达", hint: "送达 gate 已确认成功。" };
  }
  if (deliverySuccessEvidenceIsStale.value) {
    return { state: "需复验", hint: "读到旧送达成功记录；本轮仍需重新确认送达。" };
  }
  if (deliverySuccessEvidenceRouteMismatch.value) {
    return { state: "需复验", hint: "读到送达成功记录，但行程材料不是本轮记录；本轮仍需重新确认送达。" };
  }
  if (deliveryNav2GoalReady.value) {
    const gapCount = deliveryGateBlockedReasons.value.length;
    return {
      state: "待确认",
      hint: gapCount > 0 ? `行程已完成，还需补齐 ${gapCount} 项送达确认。` : "行程已完成，还需要现场确认送达。",
    };
  }
  if (deliveryLatestResult.value || deliveryGapCheckResult.value || deliveryCompletionResult.value || navGoalExecutionLatestResult.value) {
    if (plainTripHasFreshUnprovenControlEvidence.value) {
      return { state: "待行程结果", hint: "最近行程有成功结果和反馈，但真车执行未证明，需要重新执行完整行程。" };
    }
    if (plainTripHasFreshIncompleteEvidence.value) {
      return { state: "待行程结果", hint: "最近行程缺少反馈样本，需要重新读取或执行完整行程。" };
    }
    if (plainTripLatestNotProvenEvidence.value) {
      return { state: "待行程结果", hint: plainTripFailureSummaryText() };
    }
    return plainTripHasSucceededEvidence.value
      ? { state: "需复验", hint: "读到旧行程成功记录；本轮送达前需要重新执行行程。" }
      : { state: "待行程结果", hint: "还没读到最近一次完整行程结果。" };
  }
  return { state: "未读取", hint: "点击刷新送达状态，只读取结果，不执行行程或确认送达。" };
});

const plainDeliveryLatestButtonLabel = computed(() => {
  // latest 只读最近送达 gate 结果；按钮文案直接说明不会提交确认。
  if (plainDeliveryMapWysiwygPending.value) {
    return "等待地图刷新";
  }
  return deliveryLatestPending.value ? "刷新中" : "刷新送达状态（只读）";
});

const plainDeliveryPrefillButtonLabel = computed(() => {
  // 按钮文案跟随当前缺哪类材料；点击仍只做 latest/probe 预填，不提交送达。
  if (navGoalExecutionLatestPending.value || cameraFirstFrameProbePending.value || deliveryLatestPending.value) {
    return "准备中";
  }
  if (plainDeliveryMapWysiwygPending.value) {
    return "等待地图刷新";
  }
  if (previewBusy.value) {
    return "等待画面稳定";
  }
  if (cameraFrameTooDark.value) {
    return "先检查画面光线";
  }
  const hasVideoRef = deliveryOperatorVideoRef.value.trim().length > 0;
  const hasRouteRef = deliveryOperatorRouteMapRef.value.trim().length > 0;
  const visualPrefix = browserVideoFrameDrawn() ? "" : "检查画面并";
  if (hasRouteRef && !hasVideoRef) {
    return `${visualPrefix}补送达画面`;
  }
  if (hasVideoRef && hasRouteRef) {
    return "重新准备材料";
  }
  return `${visualPrefix}准备送达材料`;
});

const plainDeliveryMaterialSummary = computed(() => {
  // 送达材料草稿只说明“有没有准备好”；不显示 ref、字段名或 delivery claim。
  if (operatorReportPending.value) {
    return { state: "保存中", hint: "正在保存送达材料草稿；不会确认送达。" };
  }
  if (navGoalExecutionLatestPending.value || cameraFirstFrameProbePending.value || deliveryLatestPending.value) {
    return { state: "准备中", hint: "正在读取最近行程和画面材料。" };
  }
  if (plainDeliveryMapWysiwygPending.value) {
    return { state: "刷新中", hint: `${plainTripMapWysiwygPendingText()}；刷新完成后再准备或保存送达材料。` };
  }
  if (previewBusy.value) {
    return { state: "等待画面", hint: "实时画面正在打开或关闭；画面稳定后再准备送达材料。" };
  }
  if (cameraFrameTooDark.value) {
    return { state: "待画面", hint: "当前画面偏暗，先检查镜头或光线后再准备送达材料。" };
  }
  if (deliveryDraftMaterialPresent()) {
    const ageText = formatEvidenceAge(
      deliveryLatestResult.value?.delivery_key_values,
      "这份草稿较旧，如本轮已重新到达，请重新准备材料或重新确认",
    );
    const mismatchText = deliveryRouteMapMatchesFreshNav2.value ? "" : "行程材料不是本轮记录，请点准备送达材料更新。";
    return { state: "已保存", hint: `送达材料草稿已保存${ageText}；${mismatchText}请完成下方最终确认。` };
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
  if (plainTripHasSucceededEvidence.value) {
    return { state: "需复验", hint: "行程成功记录较旧，先重新执行本轮行程。" };
  }
  return { state: "待行程", hint: "需要先读到最近行程结果，再准备送达材料。" };
});

const plainDeliveryDraftSaveButtonLabel = computed(() => (
  operatorReportPending.value ? "保存中" : "保存送达草稿（不确认）"
));

const plainDeliveryConfirmReady = computed(() => {
  // 普通确认入口复用高级 gate：本轮行程、材料和逐项勾选都满足后才允许提交。
  return !loading.value
    && !operatorReportPending.value
    && !deliveryCompletionPending.value
    && !deliverySuccessReady.value
    && !plainDeliveryMapWysiwygPending.value
    && robotApiBaseUrl.value.trim().length > 0
    && deliveryNav2GoalReady.value
    && deliveryRouteMapMatchesFreshNav2.value
    && deliveryOperatorConfirmationReady.value
    && deliveryOperatorVideoRef.value.trim().length > 0
    && deliveryOperatorRouteMapRef.value.trim().length > 0;
});

const plainDeliveryConfirmSummary = computed(() => {
  // 首屏只解释下一步，不把 operator report、route_map_ref 或 delivery gate 术语暴露给普通用户。
  if (operatorReportPending.value || deliveryCompletionPending.value) {
    return { state: "确认中", hint: "正在提交最终确认。" };
  }
  if (deliverySuccessReady.value) {
    return { state: "已完成", hint: "送达已确认完成。" };
  }
  if (deliverySuccessEvidenceIsStale.value) {
    return { state: "待确认", hint: "旧送达成功记录不能用于本轮，仍需重新确认送达。" };
  }
  if (deliverySuccessEvidenceRouteMismatch.value) {
    return { state: "待材料", hint: "送达成功记录的行程材料不是本轮记录，先重新准备材料并确认送达。" };
  }
  if (plainDeliveryMapWysiwygPending.value) {
    return { state: "刷新中", hint: `${plainTripMapWysiwygPendingText()}；刷新完成后再提交送达确认。` };
  }
  if (!deliveryNav2GoalReady.value) {
    if (plainTripRadarBlocked.value) {
      return { state: "待行程", hint: plainRadarTripBlockedHint(plainTripNeedsFreshRunAfterRadar.value) };
    }
    if (plainTripHasFreshUnprovenControlEvidence.value) {
      return { state: "待行程", hint: "最近行程未证明真车执行，先重新执行完整行程。" };
    }
    if (plainTripHasFreshIncompleteEvidence.value) {
      return { state: "待行程", hint: "最近行程缺少反馈样本，先重新读取或执行完整行程。" };
    }
    if (plainTripLatestNotProvenEvidence.value) {
      return { state: "待行程", hint: plainTripFailureSummaryText() };
    }
    return plainTripHasSucceededEvidence.value
      ? { state: "待行程", hint: "旧行程记录不能用于本轮送达，先重新执行本轮行程。" }
      : { state: "待行程", hint: "先完成本轮行程，再做最终确认。" };
  }
  if (!deliveryRouteMapMatchesFreshNav2.value) {
    return { state: "待材料", hint: "行程材料不是本轮记录，先点准备送达材料更新。" };
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

const plainDeliverySubmitResultSummary = computed(() => {
  // 红色确认按钮的后端 gate 结果必须回到普通首屏；这里只读结果，不自动重试。
  const result = deliveryCompletionResult.value;
  if (!result) {
    return "";
  }
  if (result.delivery_success === true) {
    return "送达提交已通过：上位机已确认送达完成。";
  }
  const missingSummary = plainDeliveryGateMissingSummary.value;
  if (missingSummary) {
    return `送达提交未通过：${missingSummary.replace(/^上位机还差：/, "还差：")}`;
  }
  return `送达提交未通过：${result.failure_reason || result.status || result.proxy_status}。`;
});

const deliveryClosureChecklist = computed(() => {
  // 这个摘要只是 UI 收口提示，不自动勾选、不提交、不把 delivery_success 提升为 true。
  const confirmations = deliveryOperatorConfirmations.value;
  return [
    {
      id: "nav2_goal_succeeded",
      label: "Nav2 路线执行成功",
      ready: deliveryNav2GoalReady.value && !deliveryGateMissing("nav2_goal_succeeded"),
      hint: deliveryNav2GoalReady.value
        ? "已有本轮 goal_succeeded 和反馈样本"
        : plainTripHasFreshUnprovenControlEvidence.value ? "已有 goal_succeeded 和反馈，但真车执行未证明" : plainTripHasFreshIncompleteEvidence.value ? "已有 goal_succeeded，但缺反馈样本" : plainTripHasSucceededEvidence.value ? "已有旧 goal_succeeded，需本轮复验" : plainTripLatestNotProvenEvidence.value ? plainTripFailureSummaryText().replace("需要", "需").replace(/。$/, "") : "先读取或执行最近 Nav2 目标",
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

const currentWheelReadback = computed(() => {
  // 当前只读 T1001 只能解释现场状态；真正 wheel proof 仍优先看运动窗口或已保存材料。
  const sample = baseFeedbackSamplesResult.value?.sample_key_values;
  const base = robotSummary.value?.readback_summary.base;
  return {
    left: sample?.wheel_feedback_latest_left_speed ?? base?.wheel_feedback_latest_left_speed ?? "not_loaded",
    right: sample?.wheel_feedback_latest_right_speed ?? base?.wheel_feedback_latest_right_speed ?? "not_loaded",
  };
});
const currentWheelReadbackLoaded = computed(() => {
  const { left, right } = currentWheelReadback.value;
  return left !== "not_loaded" && right !== "not_loaded";
});

const wheelClosureEvidence = computed(() => {
  // 轮速收口必须写清证据来源，避免把历史材料、静态 T1001 读回和本轮 during-motion proof 混成一句“已完成”。
  if (plainWheelEvidenceSaveFailed.value) {
    return {
      ready: false,
      hint: "本轮已读到非零 L/R，但保存失败，需重试保存轮速记录",
    };
  }
  const motionValues = plainFirstJogResult.value?.remote_motion_key_values;
  if (motionValues?.wheel_feedback_lr_nonzero_proven === "true") {
    return {
      ready: true,
      hint: `本轮试动已读到非零 L/R=${motionValues.wheel_feedback_latest_raw_left ?? "not_loaded"}/${motionValues.wheel_feedback_latest_raw_right ?? "not_loaded"}`,
    };
  }
  const keyboardMotionValues = keyboardLastWheelFeedbackValues.value;
  if (keyboardMotionValues?.wheel_feedback_lr_nonzero_proven === "true" || keyboardMotionValues?.wheel_feedback_nonzero_observed === "true") {
    // 键盘连续手控同样走固定 manual 代理；其运动窗口读到的 T1001 非零 L/R 可以作为本轮 wheel raw 证据。
    return {
      ready: true,
      hint: `本轮键盘手控已读到非零 L/R=${keyboardMotionValues.wheel_feedback_latest_raw_left ?? keyboardMotionValues.wheel_feedback_latest_left_speed ?? "not_loaded"}/${keyboardMotionValues.wheel_feedback_latest_raw_right ?? keyboardMotionValues.wheel_feedback_latest_right_speed ?? "not_loaded"}`,
    };
  }
  const sampleValues = baseFeedbackSamplesResult.value?.sample_key_values;
  if (sampleValues?.wheel_feedback_lr_nonzero_proven === "true") {
    return {
      ready: false,
      hint: `只读采样读到非零 L/R=${sampleValues.wheel_feedback_latest_left_speed}/${sampleValues.wheel_feedback_latest_right_speed}；仍需低速试动窗口保存`,
    };
  }
  if (claimWithRefReady(robotSummary.value?.operator_hil_material_summary?.wheel_feedback)) {
    const { left, right } = currentWheelReadback.value;
    const currentReadbackIsZero = isZeroWheelPair(left, right);
    return {
      ready: !currentReadbackIsZero,
      hint: currentReadbackIsZero
        ? `已有历史非零材料；当前只读 L/R=${left}/${right}，本轮复验需低速重试`
        : "已有历史非零 L/R 材料",
    };
  }
  const { left, right } = currentWheelReadback.value;
  const frameCount = sampleValues?.t1001_observed_count ?? robotSummary.value?.readback_summary.base.latest_t1001_observed_count ?? "not_loaded";
  if (currentWheelReadbackLoaded.value) {
    const frameText = frameCount !== "not_loaded" ? `，已读到 ${frameCount} 帧` : "";
    return {
      ready: false,
      hint: `当前只读 L/R=${left}/${right}${frameText}；仍需低速试动窗口保存非零 L/R`,
    };
  }
  return {
    ready: false,
    hint: "仍需 first-jog/manual 期间同帧 T1001 L/R 非零",
  };
});

const goalClosureChecklist = computed(() => {
  // 总目标进度只聚合已读证据，不触发任何控制动作或成功外推。
  const wheelEvidence = wheelClosureEvidence.value;
  const nav2Ready = deliveryNav2GoalReady.value;
  const deliveryReady = deliverySuccessReady.value;
  const keyboardReady = canUseKeyboardControl.value && keyboardStopSettledAfterPulse.value;
  return [
    {
      id: "wheel_raw_lr",
      label: "wheel raw L/R 非零",
      ready: wheelEvidence.ready,
      hint: wheelEvidence.hint,
    },
    {
      id: "nav2_goal_execution",
      label: "完整 Nav2 路线执行",
      ready: nav2Ready,
      hint: nav2Ready
        ? "已有本轮 goal_succeeded 和反馈样本"
        : plainTripRadarBlocked.value ? plainRadarTripClosureHint(plainTripNeedsFreshRunAfterRadar.value)
        : plainTripHasFreshUnprovenControlEvidence.value ? "已有 goal_succeeded 和反馈，但真车执行未证明，需重新执行完整行程" : plainTripHasFreshIncompleteEvidence.value ? "已有 goal_succeeded，但缺反馈样本，需重新读取或执行完整行程" : plainTripHasSucceededEvidence.value ? "已有旧 goal_succeeded，需本轮复验" : plainTripLatestNotProvenEvidence.value ? plainTripFailureSummaryText().replace("需要", "需").replace(/。$/, "") : "读取最近 Nav2 结果或执行受限目标后确认",
    },
    {
      id: "delivery_success",
      label: "delivery success",
      ready: deliveryReady,
      hint: deliveryReady
        ? "delivery gate 已确认成功"
        : deliverySuccessEvidenceIsStale.value ? "已有旧 delivery success，需本轮重新确认"
          : deliverySuccessEvidenceRouteMismatch.value ? "已有 delivery success，但行程材料不是本轮记录"
            : !deliveryNav2GoalReady.value ? (plainTripRadarBlocked.value ? plainRadarDeliveryBlockedHint(plainTripNeedsFreshRunAfterRadar.value) : "送达确认前先完成本轮完整行程")
            : "仍需现场最终确认并通过 delivery gate",
    },
    {
      id: "keyboard_manual",
      label: "PC 键盘连续手控",
      ready: keyboardReady,
      hint: keyboardReady
        ? `已连续转发键盘方向输入，${keyboardForwardedPulseProgressText.value}，且停止已发送`
        : canUseKeyboardControl.value
          ? keyboardManualPulseObserved.value ? `已连续转发键盘方向输入，${keyboardForwardedPulseProgressText.value}，仍需松开按键完成停止收口` : !wheelClosureEvidence.value.ready ? `键盘入口已就绪，仍需按住方向键读取非零 L/R 并连续验证，${keyboardForwardedPulseProgressText.value}` : `键盘入口已就绪，仍需按住方向键连续验证，${keyboardForwardedPulseProgressText.value}`
          : keyboardContractReady.value ? `键盘入口已在，仍需补齐：${plainKeyboardMissingSummary.value.replace(/^还差：/, "").replace(/。$/, "")}` : "键盘合同未从 summary 读到",
    },
  ];
});

const plainWheelGoalProgressHint = computed(() => {
  if (plainWheelEvidenceSaveFailed.value) {
    return "轮速保存失败：请重试保存，未保存前不要进入行程。";
  }
  // 轮速进度要显示当前 L/R 和帧数，帮助现场判断是“没读到”还是“读到了但仍为 0/0”。
  const sample = baseFeedbackSamplesResult.value?.sample_key_values;
  const base = robotSummary.value?.readback_summary.base;
  const left = sample?.wheel_feedback_latest_left_speed ?? base?.wheel_feedback_latest_left_speed ?? "not_loaded";
  const right = sample?.wheel_feedback_latest_right_speed ?? base?.wheel_feedback_latest_right_speed ?? "not_loaded";
  const frameCount = sample?.t1001_observed_count ?? base?.latest_t1001_observed_count ?? "not_loaded";
  const voltage = formatPlainVoltage(base?.feedback_voltage_v);
  const voltageText = voltage ? `，反馈电压约 ${voltage}V` : "";
  if (left !== "not_loaded" && right !== "not_loaded") {
    const frameText = frameCount !== "not_loaded" ? `，已读到 ${frameCount} 帧` : "";
    let nextStep = "仍需试动读到非零。";
    if (firstJogMaterialRestoreReady.value) {
      nextStep = "先点恢复试动确认，再试动读非零。";
    } else if (plainWheelZeroBlockerActive.value) {
      nextStep = WHEEL_ZERO_NEXT_ACTION_SUMMARY;
    } else if (isZeroWheelPair(left, right) && canSendPlainFirstJog.value) {
      nextStep = "下一步：低速试动读取非零 L/R。";
    }
    return `当前轮速 L/R=${left}/${right}${frameText}${voltageText}，${nextStep}`;
  }
  if (firstJogMaterialRestoreReady.value) {
    return "先点恢复试动确认，再试动读取轮速。";
  }
  if (canRunBaseFeedbackSamples.value) {
    return "还没读到当前 L/R；先刷新当前轮速（只读），再低速试动读取非零。";
  }
  return "等待运动窗口读到非零 L/R。";
});

const plainWheelGoalNextAction = computed(() => {
  // 每个目标行都给一条短下一步，避免第一卡点挡住其它目标的操作线索。
  if (wheelClosureEvidence.value.ready) {
    return "已完成。";
  }
  if (plainWheelEvidenceSaveFailed.value) {
    return "下一步：重试保存轮速记录。";
  }
  if (plainWheelZeroBlockerActive.value && !plainWheelZeroBlockerChecked.value) {
    return "下一步：检查轮速卡点。";
  }
  if (plainWheelZeroBlockerChecked.value) {
    return "下一步：重试读非零 L/R。";
  }
  if (firstJogMaterialRestoreBlocksMotion.value) {
    return "下一步：恢复试动确认。";
  }
  if (!currentWheelReadbackLoaded.value && canRunBaseFeedbackSamples.value) {
    return "下一步：刷新当前轮速（只读）。";
  }
  if (canSendPlainFirstJog.value) {
    return "下一步：试动读取轮速。";
  }
  if (!firstJogVisualMaterialReady.value && !plainVisualMaterialSubmitted.value) {
    return "下一步：记录现场画面。";
  }
  return "下一步：勾选安全确认。";
});

const plainTripGoalNextAction = computed(() => {
  const navReady = goalClosureChecklist.value.find((item) => item.id === "nav2_goal_execution")?.ready === true;
  if (navReady) {
    return "已完成。";
  }
  if (plainTripRadarBlocked.value) {
    return plainRadarTripBlockedNextAction(plainTripNeedsFreshRunAfterRadar.value);
  }
  if (plainTripHasFreshIncompleteEvidence.value) {
    return "下一步：重新读取或执行完整行程。";
  }
  if (plainTripHasSucceededEvidence.value) {
    return "下一步：重新执行本轮行程。";
  }
  if (plainTripLatestNotProvenEvidence.value) {
    return "下一步：检查或重新执行行程。";
  }
  if (plainTripPreparedBySummary.value && plainManualSafetyConfirmed.value) {
    if (plainTripMapWysiwygPending.value) {
      return `下一步：等待${plainTripMapWysiwygWaitText()}。`;
    }
    return plainTripCurrentRouteVisible.value ? "下一步：执行行程。" : "下一步：刷新地图画面。";
  }
  return plainManualSafetyConfirmed.value ? "下一步：检查或执行行程。" : "下一步：勾选行程前确认。";
});

const plainDeliveryGoalProgressHint = computed(() => {
  // 送达进度优先显示上位机 gate 缺项；它只是提示，不自动勾选或提交最终确认。
  if (deliverySuccessEvidenceIsStale.value) {
    return "旧送达成功记录不能用于本轮，仍需重新确认送达。";
  }
  const missingSummary = plainDeliveryGateMissingSummary.value;
  if (missingSummary) {
    const nextAction = plainDeliveryNextActionSummary.value;
    return `${missingSummary.replace(/^上位机还差：/, "还差：")}${nextAction ? ` ${nextAction}` : ""}`;
  }
  return plainDeliveryNextActionSummary.value || "还缺最终送达确认。";
});

const plainDeliveryGoalNextAction = computed(() => (
  goalClosureChecklist.value.find((item) => item.id === "delivery_success")?.ready === true
    ? "已完成。"
    : plainDeliveryNextActionSummary.value || "下一步：完成最终送达确认。"
));

const plainKeyboardGoalNextAction = computed(() => {
  if (canUseKeyboardControl.value) {
    if (keyboardStopSettledAfterPulse.value) {
      return "已验证。";
    }
    if (keyboardManualPulseObserved.value) {
      return "下一步：松开按键完成停止收口。";
    }
    if (!wheelClosureEvidence.value.ready) {
      return plainKeyboardNextActionSummary.value;
    }
    return "下一步：启用键盘并按住方向键验证。";
  }
  return plainKeyboardNextActionSummary.value || "下一步：复查手控条件。";
});

function parsePositiveMillis(value: string | undefined): number | null {
  // 上位机时间只用于提示证据新旧，解析失败时保持旧文案，不推断 freshness。
  if (!value || value === "not_loaded") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function formatEvidenceAge(values: Record<string, string> | undefined, staleMessage = "这条记录较旧，如需本轮复验，请重新执行行程"): string {
  // latest 可能是昨天的 artifact；普通用户需要看到年龄，避免把旧材料误当成本轮证据。
  const actionGeneratedAt = parsePositiveMillis(values?.generated_at_ms ?? values?.nav2_generated_at_ms);
  if (actionGeneratedAt === null) {
    return "";
  }
  const referenceAt = parsePositiveMillis(values?.response_generated_at_ms) ?? Date.now();
  const ageMs = Math.max(0, referenceAt - actionGeneratedAt);
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;
  const ageText = ageMs < minuteMs
    ? "刚刚"
    : ageMs < hourMs
      ? `约 ${Math.max(1, Math.round(ageMs / minuteMs))} 分钟前`
      : ageMs < dayMs
        ? `约 ${Math.max(1, Math.round(ageMs / hourMs))} 小时前`
        : `约 ${Math.max(1, Math.round(ageMs / dayMs))} 天前`;
  const staleText = ageMs >= EVIDENCE_STALE_AFTER_MS ? `；${staleMessage}` : "";
  return `，${ageText}${staleText}`;
}

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
  const hasFeedbackSamples = nav2FeedbackSampleCount(values) > 0;
  const feedbackText = hasFeedbackSamples ? `，反馈 ${feedbackCount} 次` : "，未读到反馈样本";
  const nextText = hasFeedbackSamples
    ? nav2ExecutionControlProven(values) ? "送达仍需现场确认。" : "真车执行未证明，需重新执行完整行程。"
    : "需重新读取或执行完整行程。";
  return `最近行程成功${feedbackText}${formatEvidenceAge(values)}；${nextText}`;
});

function plainTripPendingRouteText(): string {
  // 执行中状态必须把“正在去哪”说清楚；目标来自刚点击的图上路线终点，不从高级表单再推断。
  const goal = navGoalExecutionPendingGoal.value;
  if (!goal) {
    return "";
  }
  const routePath = latestNavPathOverlay();
  const routeText = routePath && !routePath.caption.startsWith("最近") ? `；${routePath.coordinateLabel}` : "";
  return `目标 x=${goal.goal_x.toFixed(2)}, y=${goal.goal_y.toFixed(2)}${routeText}`;
}

function plainTripStopOverlayState(): { label: string; state: string; ariaPrefix: string; actionText: string } {
  // 行程 stop 是 base stop 兜底，不代表 Nav2 action 已取消；地图和状态只表达 stop 请求链路。
  if (!plainTripStopRequestedDuringExecution.value) {
    return { label: "行程中", state: "执行中", ariaPrefix: "正在执行图上路线", actionText: "正在执行图上路线" };
  }
  if (manualCommandPending.value) {
    return { label: "行程停止中", state: "停止中", ariaPrefix: "正在发送行程停止请求", actionText: "正在发送行程停止请求" };
  }
  const stopResult = plainTripStopResultDuringExecution.value
    ?? (manualCommandResult.value?.command_kind === "stop" ? manualCommandResult.value : null);
  const stopFailed = stopResult && baseStopResultFailed(stopResult);
  if (stopResult && !stopFailed) {
    return { label: "停止已发送", state: "停止已发送", ariaPrefix: "行程停止请求已发送", actionText: "行程停止请求已发送" };
  }
  if (stopResult) {
    return { label: "停止失败", state: "停止失败", ariaPrefix: "行程停止请求失败", actionText: "行程停止请求失败，人在旁边接管" };
  }
  if (plainTripStopSettledDuringExecution.value) {
    return { label: "停止已发送", state: "停止已发送", ariaPrefix: "行程停止请求已发送", actionText: "行程停止请求已发送" };
  }
  return { label: "停止已请求", state: "停止已请求", ariaPrefix: "行程停止已请求", actionText: "行程停止已请求" };
}

function baseStopResultFailed(result: RobotControlBaseCommandProxyResponse): boolean {
  // stop proxy 失败必须压过“已请求/已发送”兜底，避免地图把失败回包显示成成功停止。
  return result.proxy_status === "command_failed" || result.proxy_status === "command_rejected" || result.status === "blocked";
}

function recordPlainTripStopResult(result: RobotControlBaseCommandProxyResponse | null): void {
  // 行程执行中的 stop 结果要独立留给地图 overlay；通用 manual 结果可能被其他链路消费。
  if (!navGoalExecutionPending.value || !plainTripStopRequestedDuringExecution.value || !result) {
    return;
  }
  plainTripStopResultDuringExecution.value = result;
  plainTripStopSettledDuringExecution.value = !baseStopResultFailed(result);
}

function plainMapTripExecutionLabel(): string {
  // 地图 caption 要短，只表达当前执行结果；详细下一步放在行程卡。
  if (navGoalExecutionPending.value) {
    const targetText = plainTripPendingRouteText();
    const stopState = plainTripStopOverlayState();
    return targetText ? `行程执行：${stopState.actionText}（${targetText}）` : `行程执行：${stopState.actionText}`;
  }
  if (navGoalExecutionLatestPending.value) {
    return "行程执行：正在读取最近行程结果";
  }
  const values = directNav2ExecutionValues();
  const status = nav2EvidenceStatus(values);
  if (!status || status === "not_loaded") {
    return "";
  }
  if (nav2ExecutionComplete(values) && !evidenceIsStale(values)) {
    const postExecutionMapFailure = plainTripPostExecutionMapPreviewFailureText();
    if (postExecutionMapFailure) {
      return `行程执行：已到达，反馈 ${nav2FeedbackSampleCount(values)} 次，地图刷新失败（${postExecutionMapFailure}）`;
    }
    if (deliveryCompletionPending.value) {
      return `行程执行：已到达，反馈 ${nav2FeedbackSampleCount(values)} 次，送达确认中`;
    }
    const deliveryFailureText = deliveryCompletionFailureText(deliveryCompletionResult.value);
    if (deliveryFailureText) {
      return `行程执行：已到达，反馈 ${nav2FeedbackSampleCount(values)} 次，送达确认失败（${deliveryFailureText}）`;
    }
    if (deliverySuccessReady.value) {
      return `行程执行：已送达，反馈 ${nav2FeedbackSampleCount(values)} 次，delivery gate 已确认`;
    }
    return `行程执行：已到达，反馈 ${nav2FeedbackSampleCount(values)} 次，准备送达材料`;
  }
  if (nav2GoalSucceeded(values) && evidenceIsStale(values)) {
    return "行程执行：旧到达记录";
  }
  if (nav2GoalSucceeded(values) && nav2FeedbackSampleCount(values) > 0 && !nav2ExecutionControlProven(values)) {
    return "行程执行：已到达，执行未证明";
  }
  if (nav2GoalSucceeded(values)) {
    return "行程执行：已到达，缺反馈";
  }
  const failureText = plainTripFailureReasonText(navGoalExecutionResult.value ?? navGoalExecutionLatestResult.value, values);
  return failureText ? `行程执行：未通过（${failureText}）` : "行程执行：未通过";
}

const plainTripExecutionProgress = computed(() => {
  // 这行只解释已有执行证据，不会触发读取、执行、送达确认或任何底盘命令。
  if (navGoalExecutionPending.value) {
    const targetText = plainTripPendingRouteText();
    const stopState = plainTripStopOverlayState();
    const suffix = stopState.state === "执行中" ? "人在旁边准备停止。" : "人在旁边接管，等待行程结果返回。";
    return targetText ? `行程进度：${stopState.actionText}，${targetText}；${suffix}` : `行程进度：${stopState.actionText}，${suffix}`;
  }
  if (navGoalExecutionLatestPending.value) {
    return "行程进度：正在读取最近行程结果，返回前不把旧结果当作当前结论。";
  }
  const values = directNav2ExecutionValues();
  const status = nav2EvidenceStatus(values);
  if (!status || status === "not_loaded") {
    return "";
  }
  const ageText = formatEvidenceAge(values, "这条行程较旧，如需本轮验收，请重新执行图上路线");
  if (nav2ExecutionComplete(values) && !evidenceIsStale(values)) {
    const postExecutionMapFailure = plainTripPostExecutionMapPreviewFailureText();
    if (postExecutionMapFailure) {
      return `行程进度：已到达，读到 ${nav2FeedbackSampleCount(values)} 次执行反馈${ageText}；执行后地图画面刷新失败：${postExecutionMapFailure}，先刷新地图画面再准备送达材料。`;
    }
    return `行程进度：已到达，读到 ${nav2FeedbackSampleCount(values)} 次执行反馈${ageText}；下一步准备送达材料。`;
  }
  if (nav2GoalSucceeded(values) && evidenceIsStale(values)) {
    const feedbackText = nav2FeedbackSampleCount(values) > 0 ? `，读到 ${nav2FeedbackSampleCount(values)} 次执行反馈` : "，未读到反馈样本";
    return `行程进度：读到旧的到达记录${feedbackText}${ageText}。`;
  }
  if (nav2GoalSucceeded(values) && nav2FeedbackSampleCount(values) > 0 && !nav2ExecutionControlProven(values)) {
    return `行程进度：已到达并读到 ${nav2FeedbackSampleCount(values)} 次反馈，但真车执行未证明${ageText}；重新执行完整行程。`;
  }
  if (nav2GoalSucceeded(values)) {
    return `行程进度：已到达，但没有执行反馈样本${ageText}；重新读取或执行完整行程。`;
  }
  return `行程进度：${plainTripFailureSummaryText().replace("需要", "先")}`;
});

const plainGoalProgressItems = computed(() => {
  // 普通首屏只展示用户能决策的四件事；工程字段继续留在高级诊断。
  const wheelEvidence = wheelClosureEvidence.value;
  const wheelReady = wheelEvidence.ready;
  const navReady = goalClosureChecklist.value.find((item) => item.id === "nav2_goal_execution")?.ready === true;
  const deliveryReady = goalClosureChecklist.value.find((item) => item.id === "delivery_success")?.ready === true;
  return [
    {
      id: "wheel",
      label: "轮速记录",
      actionLabel: firstJogMaterialRestoreBlocksMotion.value ? "去恢复" : "去轮速",
      state: wheelReady ? "已完成" : "待完成",
      hint: wheelReady ? `${wheelEvidence.hint}。` : plainWheelGoalProgressHint.value,
      nextAction: plainWheelGoalNextAction.value,
    },
    {
      id: "trip",
      label: "行程执行",
      actionLabel: plainTripRadarBlocked.value ? "去雷达" : "去行程",
      state: navReady ? "已完成" : "待完成",
      hint: navReady
        ? plainTripEvidenceSummary.value || "最近行程已读到成功结果。"
        : plainTripRadarBlocked.value ? plainRadarTripBlockedHint(plainTripNeedsFreshRunAfterRadar.value) : plainTripHasFreshUnprovenControlEvidence.value ? "最近行程未证明真车执行，需要重新执行完整行程。" : plainTripHasFreshIncompleteEvidence.value ? "最近行程缺少反馈样本，需要重新读取或执行完整行程。" : plainTripHasSucceededEvidence.value ? "最近行程记录较旧，需要重新执行本轮行程。" : plainTripLatestNotProvenEvidence.value ? plainTripFailureSummaryText() : plainTripPreparedBySummary.value ? (plainManualSafetyConfirmed.value ? (plainTripCurrentRouteVisible.value ? `路线已准备 ${plainTripPreparedPointCount.value} 个点，可执行行程。` : `路线已准备 ${plainTripPreparedPointCount.value} 个点，先刷新地图画面确认图上路线。`) : `路线已准备 ${plainTripPreparedPointCount.value} 个点，先勾选行程前确认。`) : "还没读到最近行程成功结果。",
      nextAction: plainTripGoalNextAction.value,
    },
    {
      id: "delivery",
      label: "送达确认",
      actionLabel: "去送达",
      state: deliveryReady ? "已完成" : "待完成",
      hint: deliveryReady ? "送达已确认。" : plainDeliveryGoalProgressHint.value,
      nextAction: plainDeliveryGoalNextAction.value,
    },
    {
      id: "keyboard",
      label: "键盘手控",
      actionLabel: "去键盘",
      state: canUseKeyboardControl.value ? (keyboardStopSettledAfterPulse.value ? "已验证" : "待验证") : "未满足",
      hint: canUseKeyboardControl.value
        ? keyboardStopSettledAfterPulse.value ? `已连续转发键盘方向输入，${keyboardForwardedPulseProgressText.value}，停止已发送；现场可继续按住方向键手控。` : keyboardManualPulseObserved.value ? `已连续转发键盘方向输入，${keyboardForwardedPulseProgressText.value}；松开按键完成停止收口。` : !wheelClosureEvidence.value.ready ? `键盘已解锁；点击启用键盘后按住方向键读取非零 L/R 并连续验证，${keyboardForwardedPulseProgressText.value}。` : `键盘已解锁；点击启用键盘后按住方向键连续验证，${keyboardForwardedPulseProgressText.value}。`
        : `先补齐键盘手控条件。${plainKeyboardMissingSummary.value} ${plainKeyboardNextActionSummary.value}`,
      nextAction: plainKeyboardGoalNextAction.value,
    },
  ];
});

const plainGoalProgressNextAction = computed(() => {
  // 现场不应该在四个目标之间猜顺序；总提示只指向第一项未完成的普通任务。
  const nextItem = plainGoalProgressItems.value.find((item) => item.state !== "已完成" && item.state !== "已验证");
  return nextItem ? `下一步：先处理${nextItem.label}。${nextItem.hint}` : "下一步：四项都已完成，保持待命。";
});

const plainGoalProgressPrimaryTarget = computed(() => {
  // 主按钮只指向当前第一项缺口；没有缺口时禁用，不能触发任何自动动作。
  return plainGoalProgressItems.value.find((item) => item.state !== "已完成" && item.state !== "已验证")?.id ?? "";
});

const plainGoalProgressPrimaryActionLabel = computed(() => {
  // 文案直接写出要跳到哪个卡点，减少现场点按钮前的二次判断。
  const target = plainGoalProgressItems.value.find((item) => item.id === plainGoalProgressPrimaryTarget.value);
  if (target?.id === "wheel" && firstJogMaterialRestoreBlocksMotion.value) {
    return "去恢复确认";
  }
  if (target?.id === "wheel" && canSendPlainWheelTrial.value) {
    return "去低速试动";
  }
  if (target?.id === "trip" && plainTripRadarBlocked.value) {
    if (plainRadarStartUnavailable.value) {
      return "去配置雷达";
    }
    if (plainRadarRequiresRefresh.value) {
      return "去刷新雷达";
    }
    return "去启动雷达";
  }
  return target ? `去${target.label.replace("执行", "").replace("确认", "")}卡点` : "全部完成";
});

const plainGoalProgressPanelState = computed(() => {
  // 外层状态只汇总现有四个收口目标；不把历史材料或单项成功误写成整轮完成。
  if (deliveryCompletionPending.value) {
    return "确认中";
  }
  if (navGoalExecutionPending.value) {
    return "执行中";
  }
  if (plainGoalProgressPending.value || mapWysiwygRefreshPending.value) {
    return "刷新中";
  }
  return plainGoalProgressPrimaryTarget.value ? "待处理" : "已完成";
});

const plainGoalProgressStateSummary = computed(() => {
  // 四个目标的当前结论压成一行，方便现场先看全局状态再按下一步执行。
  const fragments = plainGoalProgressItems.value.map((item) => `${item.label}${item.state}`);
  return `当前状态：${fragments.join("；")}。`;
});

const plainGoalProgressEvidenceSummary = computed(() => {
  // 这行只压缩已读证据，不刷新接口，也不把只读材料外推成真实完成。
  const wheelReady = goalClosureChecklist.value.find((item) => item.id === "wheel_raw_lr")?.ready === true;
  const { left, right } = currentWheelReadback.value;
  const wheelText = wheelReady
    ? isZeroWheelPair(left, right) ? `轮速有历史材料，当前 L/R=${left}/${right}` : "轮速已完成"
    : left !== "not_loaded" && right !== "not_loaded" ? `轮速 L/R=${left}/${right}` : "轮速未读到";
  const tripText = deliveryNav2GoalReady.value || plainTripHasSucceededEvidence.value
    ? plainTripEvidenceSummary.value.replace("；送达仍需现场确认。", "") || "行程已完成"
    : plainTripLatestNotProvenEvidence.value ? plainTripFailureShortText() : plainTripPreparedBySummary.value ? `路线已准备 ${plainTripPreparedPointCount.value} 点` : "行程未完成";
  const deliveryText = deliverySuccessReady.value
    ? "送达已完成"
    : deliverySuccessEvidenceIsStale.value ? "送达有旧成功记录"
      : deliverySuccessEvidenceRouteMismatch.value ? "送达成功材料非本轮"
        : "送达未完成";
  const keyboardText = canUseKeyboardControl.value ? (keyboardStopSettledAfterPulse.value ? "键盘已验证" : "键盘待验证") : "键盘未满足";
  return `当前读数：${wheelText}；${tripText}；${deliveryText}；${keyboardText}。`;
});

const plainGoalProgressBlockerSummary = computed(() => {
  // 验收卡点只选当前第一处真实缺口，避免现场在多条提示里来回找重点。
  const wheelReady = goalClosureChecklist.value.find((item) => item.id === "wheel_raw_lr")?.ready === true;
  const sample = baseFeedbackSamplesResult.value?.sample_key_values;
  const base = robotSummary.value?.readback_summary.base;
  const left = sample?.wheel_feedback_latest_left_speed ?? base?.wheel_feedback_latest_left_speed ?? "not_loaded";
  const right = sample?.wheel_feedback_latest_right_speed ?? base?.wheel_feedback_latest_right_speed ?? "not_loaded";
  if (!wheelReady) {
    if (plainWheelEvidenceSaveFailed.value) {
      return "验收卡点：轮速已读到，但保存失败；先重试保存轮速记录。";
    }
    if (firstJogMaterialRestoreReady.value && !plainFirstJogMaterialRestored.value) {
      return "验收卡点：送达草稿覆盖了试动确认，先恢复试动确认，再低速试动读非零 L/R。";
    }
    if (plainWheelZeroBlockerActive.value && isZeroWheelPair(left, right)) {
      return `验收卡点：轮速 L/R=${left}/${right}，检查电机使能、供电、模式和现场空间后重试。`;
    }
    return "验收卡点：还需要试动期间同帧 L/R 都非零。";
  }
  if (!deliveryNav2GoalReady.value) {
    if (plainTripRadarBlocked.value) {
      return `验收卡点：${plainRadarTripClosureHint(plainTripNeedsFreshRunAfterRadar.value).replace("完整行程", "本轮行程")}。`;
    }
    if (plainTripHasFreshUnprovenControlEvidence.value) {
      return "验收卡点：行程有成功结果和反馈，但真车执行未证明，需要重新执行完整行程。";
    }
    if (plainTripHasFreshIncompleteEvidence.value) {
      return "验收卡点：行程成功但缺少反馈样本，需要重新读取或执行完整行程。";
    }
    return plainTripHasSucceededEvidence.value
      ? "验收卡点：行程成功记录较旧，需要重新执行本轮行程。"
      : plainTripLatestNotProvenEvidence.value ? `验收卡点：${plainTripFailureSummaryText()}`
      : plainTripPreparedBySummary.value ? (plainTripMapWysiwygPending.value ? `验收卡点：路线已准备 ${plainTripPreparedPointCount.value} 个点，${plainTripMapWysiwygPendingText()}，刷新完成后再执行。` : plainTripCurrentRouteVisible.value ? `验收卡点：路线已准备 ${plainTripPreparedPointCount.value} 个点，还需要点击执行行程并读到成功结果。` : `验收卡点：路线已准备 ${plainTripPreparedPointCount.value} 个点，还需要刷新地图画面确认图上路线。`)
        : "验收卡点：还没读到行程成功结果。";
  }
  if (!deliverySuccessReady.value) {
    if (deliverySuccessEvidenceIsStale.value) {
      return "验收卡点：送达成功记录较旧，需要本轮重新确认送达。";
    }
    if (deliverySuccessEvidenceRouteMismatch.value) {
      return "验收卡点：送达成功记录的行程材料不是本轮记录，需要重新准备材料并确认送达。";
    }
    return plainDeliveryNextActionSummary.value ? `验收卡点：送达未完成，${plainDeliveryNextActionSummary.value}` : "验收卡点：送达未完成，需要现场最终确认。";
  }
  if (canUseKeyboardControl.value && !keyboardStopSettledAfterPulse.value) {
    if (keyboardManualPulseObserved.value) {
      return `验收卡点：键盘已连续转发 ${KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES}/${KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES} 次，松开按键完成停止收口。`;
    }
    return `验收卡点：键盘已解锁，点击启用键盘后按住方向键连续验证，${keyboardForwardedPulseProgressText.value}。`;
  }
  if (!canUseKeyboardControl.value) {
    return `验收卡点：键盘手控未满足，${plainKeyboardNextActionSummary.value}`;
  }
  return "验收卡点：四项都已满足，保持待命。";
});

const plainTripActionPending = computed(() => navGoalPreflightPending.value || navGoalExecutionPending.value || navGoalExecutionLatestPending.value || nav2RefreshPending.value);
const plainTripMapWysiwygPending = computed(() => mapPreviewPending.value || mapRefreshPending.value);
const manualMotionActiveForTrip = computed(() => (
  // 行程执行和手控/键盘不能同时作为新动作启动；stop 仍走独立兜底入口。
  manualCommandPending.value || Boolean(keyboardHeldDirection.value)
));
function plainTripMapWysiwygPendingText(): string {
  // 地图 proof 和地图画面任一刷新中，都不能把旧路线当成当前可执行图上路线。
  return mapPreviewPending.value ? "地图画面刷新中" : "地图状态刷新中";
}
function plainTripMapWysiwygWaitText(): string {
  return mapPreviewPending.value ? "地图画面刷新" : "地图状态刷新";
}
function plainTripPostExecutionMapPreviewFailureText(): string {
  // 行程执行后的自动地图刷新失败只影响“画面是否最新”，不能覆盖 Nav2 已返回的执行结果。
  if (!plainTripPostExecutionMapPreviewRefreshFailed.value) {
    return "";
  }
  return mapPreviewFailureText(mapPreviewResult.value) || "地图画面读取失败";
}
function plainTripPreparedRouteMapPreviewFailureText(routeVisible: boolean): string {
  // 路线已准备但图上路线不可见时，地图画面失败必须贴回行程卡片，避免用户反复点错入口。
  if (routeVisible) {
    return "";
  }
  return mapPreviewFailureText(mapPreviewResult.value);
}
const plainTripRadarBlocked = computed(() => {
  // 雷达状态只作为普通提示；执行按钮按“安全确认 + 后端定位/路线预检”收敛，不在前端重复硬挡。
  return false;
});

const plainTripPreparedByRefresh = computed(() => {
  // 普通首屏“准备行程”复用 no-motion Nav2 proof refresh，只看路径点是否已由上位机生成。
  const values = nav2RefreshResult.value?.latest_readback_key_values;
  if (!values) {
    return false;
  }
  const pointCount = Number(values.path_point_count ?? "0");
  return (values.path_generated === "true" || values.path_generation_succeeded === "true") && Number.isFinite(pointCount) && pointCount > 0;
});
const plainTripPreparedPointCount = computed(() => {
  // summary 可能已经带着最近 no-motion 路线；普通用户不应被迫再点一次“准备行程”才知道路线已可检查。
  const refreshValues = nav2RefreshResult.value?.latest_readback_key_values;
  const refreshCount = Number(refreshValues?.path_point_count ?? "0");
  if (plainTripPreparedByRefresh.value && Number.isFinite(refreshCount) && refreshCount > 0) {
    return refreshCount;
  }
  const proof = robotSummary.value?.o3_proof_summary;
  const summaryCount = Number(proof?.path_preview_point_count ?? proof?.path_point_count ?? 0);
  const summaryPrepared = (proof?.path_generated === true || proof?.path_generation_succeeded === true)
    && Number.isFinite(summaryCount)
    && summaryCount > 0;
  return summaryPrepared ? summaryCount : 0;
});
const plainTripPreparedBySummary = computed(() => plainTripPreparedPointCount.value > 0);

function plainTripPreparationFailureHint(): string {
  // 底层 root cause 可能是英文诊断字段；普通首屏只翻译成下一步，不泄露 planner_server_not_active 等术语。
  const values = nav2RefreshResult.value?.latest_readback_key_values;
  const rootCauseText = String(values?.root_causes ?? values?.status ?? values?.latest_proof_status ?? "");
  if (rootCauseText.includes("planner_server_not_active")) {
    return "行程服务还没准备好，先点重新定位，或稍后再准备一次。";
  }
  if (rootCauseText.includes("map") || rootCauseText.includes("no_free")) {
    return "地图还不能用于行程，先刷新地图或重新建图。";
  }
  if (rootCauseText.includes("localization") || rootCauseText.includes("tf")) {
    return "位置还没对上地图，先点重新定位后再准备。";
  }
  return "行程准备还没完成，确认地图和定位后再试一次。";
}

const plainTripSummary = computed(() => {
  // 普通首屏只说“行程”，不把 Nav2、goal 或 proof 术语放到默认界面。
  if (navGoalExecutionPending.value) {
    const targetText = plainTripPendingRouteText();
    const stopState = plainTripStopOverlayState();
    const suffix = stopState.state === "执行中" ? "人在旁边准备停止。" : "人在旁边接管，等待行程结果返回。";
    return { state: stopState.state, hint: targetText ? `${stopState.actionText}，${targetText}；${suffix}` : `${stopState.actionText}；${suffix}` };
  }
  if (nav2RefreshPending.value) {
    return { state: "准备中", hint: "正在准备行程；不会发车。" };
  }
  if (navGoalPreflightPending.value) {
    return { state: "复查中", hint: "正在可选复查行程条件；不会发车。" };
  }
  if (navGoalExecutionLatestPending.value) {
    return { state: "读取中", hint: "正在读取最近行程结果。" };
  }
  const postExecutionMapFailure = plainTripPostExecutionMapPreviewFailureText();
  if (postExecutionMapFailure) {
    return { state: "待刷新", hint: `本轮行程已返回，但执行后地图画面刷新失败：${postExecutionMapFailure}；先刷新地图画面，再准备送达材料。` };
  }
  if (deliveryNav2GoalReady.value) {
    return { state: "已完成", hint: plainTripEvidenceSummary.value || "已读到最近行程完成，可以准备送达材料。" };
  }
  if (plainTripHasFreshUnprovenControlEvidence.value) {
    return { state: "需复验", hint: plainTripEvidenceSummary.value || "最近行程未证明真车执行，需要重新执行完整行程。" };
  }
  if (plainTripHasFreshIncompleteEvidence.value) {
    return { state: "需复验", hint: plainTripEvidenceSummary.value || "最近行程缺少反馈样本，需要重新读取或执行完整行程。" };
  }
  if (plainTripHasSucceededEvidence.value) {
    return { state: "需复验", hint: plainTripEvidenceSummary.value || "最近行程记录较旧，需要重新执行本轮行程。" };
  }
  if (plainTripLatestNotProvenEvidence.value) {
    return { state: "需检查", hint: plainTripFailureSummaryText() };
  }
  if (navGoalExecutionResult.value?.proxy_status === "execution_failed" || navGoalExecutionResult.value?.proxy_status === "execution_rejected") {
    return { state: "执行失败", hint: navGoalExecutionResult.value.failure_reason || "行程执行未通过。" };
  }
  if (plainTripPreparedByRefresh.value) {
    const routeVisible = latestNavPathOverlay() !== null;
    const mapFailure = plainTripPreparedRouteMapPreviewFailureText(routeVisible);
    if (plainTripMapWysiwygPending.value) {
      return { state: "刷新中", hint: `路线 ${plainTripPreparedPointCount.value} 个点已准备；${plainTripMapWysiwygPendingText()}，刷新完成后再执行图上路线。` };
    }
    if (mapFailure) {
      return { state: "待刷新", hint: `路线 ${plainTripPreparedPointCount.value} 个点已准备，但地图画面刷新失败：${mapFailure}；重试刷新图上路线。` };
    }
    return plainManualSafetyConfirmed.value
      ? { state: "已准备", hint: routeVisible ? `行程准备已刷新，地图上已显示路线 ${plainTripPreparedPointCount.value} 个点；可执行图上路线，后端仍会复查定位和路线。` : `行程准备已刷新，路线 ${plainTripPreparedPointCount.value} 个点已准备；先刷新地图画面确认图上路线。` }
      : { state: "已准备", hint: routeVisible ? `行程准备已刷新，地图上已显示路线 ${plainTripPreparedPointCount.value} 个点；勾选安全确认后可执行图上路线。` : `行程准备已刷新，路线 ${plainTripPreparedPointCount.value} 个点已准备；勾选安全确认后先刷新地图画面确认图上路线。` };
  }
  if (nav2RefreshResult.value && !plainTripPreparedByRefresh.value) {
    return { state: "待准备", hint: plainTripPreparationFailureHint() };
  }
  if (plainTripPreparedBySummary.value) {
    const routeVisible = latestNavPathOverlay() !== null;
    const mapFailure = plainTripPreparedRouteMapPreviewFailureText(routeVisible);
    if (plainTripMapWysiwygPending.value) {
      return { state: "刷新中", hint: `路线 ${plainTripPreparedPointCount.value} 个点已准备；${plainTripMapWysiwygPendingText()}，刷新完成后再执行图上路线。` };
    }
    if (mapFailure) {
      return { state: "待刷新", hint: `路线 ${plainTripPreparedPointCount.value} 个点已准备，但地图画面刷新失败：${mapFailure}；重试刷新图上路线。` };
    }
    return plainManualSafetyConfirmed.value
      ? { state: "已准备", hint: routeVisible ? `地图上已显示路线 ${plainTripPreparedPointCount.value} 个点；可直接执行图上路线，后端仍会复查定位和路线。` : `路线 ${plainTripPreparedPointCount.value} 个点已准备；先刷新地图画面确认图上路线。` }
      : { state: "已准备", hint: routeVisible ? `地图上已显示路线 ${plainTripPreparedPointCount.value} 个点；勾选安全确认后可执行图上路线。` : `路线 ${plainTripPreparedPointCount.value} 个点已准备；勾选安全确认后先刷新地图画面确认图上路线。` };
  }
  if (navGoalPreflightResult.value?.proxy_status === "preflight_passed") {
    return { state: "可执行", hint: "可选复查通过；确认人在旁边后可执行一次图上路线。" };
  }
  if (navGoalPreflightResult.value && navGoalPreflightResult.value.proxy_status !== "preflight_passed") {
    return { state: "复查失败", hint: "可选复查未通过；行程条件还没满足，请看高级诊断。" };
  }
  if (!plainManualSafetyConfirmed.value) {
    return { state: "待确认", hint: "先勾选行程前确认，再准备或执行行程。" };
  }
  return { state: "可执行", hint: "已完成最小确认；执行前后端会复查定位和路线。" };
});

const plainTripRouteWysiwygSummary = computed(() => {
  // 行程执行必须和当前地图画面绑定：看得到路线才说“执行图上路线”，看不到就提示先刷新地图。
  const routePath = latestNavPathOverlay();
  if (routePath) {
    const routeIdentity = `${routePath.coordinateLabel}，${routePath.endpointSummary}`;
    if (plainTripMapWysiwygPending.value) {
      return `${plainTripMapWysiwygPendingText()}；刷新完成后再执行这条图上路线（${routeIdentity}）。`;
    }
    return routePath.caption.startsWith("最近")
      ? `地图上显示的是最近路线（${routeIdentity}）；先准备行程，再执行新的图上路线。`
      : `执行前确认地图上的起点、终点和路线；按钮会执行这条图上路线（${routeIdentity}）。`;
  }
  if (plainTripPreparedBySummary.value) {
    const mapFailure = mapPreviewFailureText(mapPreviewResult.value);
    if (mapFailure) {
      return `路线已准备 ${plainTripPreparedPointCount.value} 个点；地图画面刷新失败：${mapFailure}，重试刷新图上路线。`;
    }
    return `路线已准备 ${plainTripPreparedPointCount.value} 个点；先刷新地图画面确认图上路线。`;
  }
  return "";
});
const plainTripRunStatus = computed(() => {
  // 行程状态只解释当前 UI gate；真正执行仍必须显式点击按钮并由后端复查定位和路线。
  if (navGoalExecutionPending.value) {
    const targetText = plainTripPendingRouteText();
    const stopState = plainTripStopOverlayState();
    const suffix = stopState.state === "执行中" ? "人在旁边准备停止。" : "人在旁边接管，等待行程结果返回。";
    return targetText ? `行程状态：${stopState.actionText}，${targetText}；${suffix}` : `行程状态：${stopState.actionText}，${suffix}`;
  }
  if (nav2RefreshPending.value) {
    return "行程状态：正在准备路线，不会发车。";
  }
  if (navGoalPreflightPending.value) {
    return "行程状态：正在可选复查行程条件，不会发车。";
  }
  if (deliveryNav2GoalReady.value) {
    const postExecutionMapFailure = plainTripPostExecutionMapPreviewFailureText();
    if (postExecutionMapFailure) {
      return `行程状态：本轮行程已完成，但执行后地图画面刷新失败：${postExecutionMapFailure}；先刷新地图画面。`;
    }
    return "行程状态：本轮行程已完成，可以准备送达材料。";
  }
  if (!plainManualSafetyConfirmed.value) {
    return "行程状态：先勾安全确认，小车不会出发。";
  }
  if (plainTripHasFreshIncompleteEvidence.value) {
    return "行程状态：最近行程缺少反馈样本，重新读取或重新执行后再送达。";
  }
  if (plainTripHasFreshUnprovenControlEvidence.value) {
    return "行程状态：最近行程未证明真车执行，重新执行完整行程后再送达。";
  }
  if (plainTripLatestNotProvenEvidence.value) {
    return `行程状态：${plainTripFailureSummaryText().replace("需要", "先")}`;
  }
  if (navGoalExecutionResult.value?.proxy_status === "execution_failed" || navGoalExecutionResult.value?.proxy_status === "execution_rejected") {
    return `行程状态：${plainTripFailureSummaryText().replace("需要", "先")}`;
  }
  if (plainTripHasSucceededEvidence.value) {
    return "行程状态：读到旧行程成功记录；如需本轮验收，请重新执行图上路线。";
  }
  if (plainTripMapWysiwygPending.value && plainTripPreparedBySummary.value) {
    return `行程状态：路线已准备 ${plainTripPreparedPointCount.value} 个点，${plainTripMapWysiwygPendingText()}；刷新完成后再执行图上路线。`;
  }
  if (plainTripPreparedBySummary.value && !plainTripCurrentRouteVisible.value) {
    const mapFailure = mapPreviewFailureText(mapPreviewResult.value);
    if (mapFailure) {
      return `行程状态：路线已准备 ${plainTripPreparedPointCount.value} 个点，但地图画面刷新失败：${mapFailure}；重试刷新图上路线。`;
    }
    return `行程状态：路线已准备 ${plainTripPreparedPointCount.value} 个点，但地图上还没显示；先刷新地图画面。`;
  }
  if (plainTripCurrentRouteVisible.value) {
    return "行程状态：图上路线已可执行；点击执行前确认起点、终点和路径。";
  }
  if (navGoalPreflightResult.value?.proxy_status === "preflight_passed") {
    return "行程状态：可选复查通过；准备好后执行一次图上路线。";
  }
  if (nav2RefreshResult.value && !plainTripPreparedByRefresh.value) {
    return `行程状态：${plainTripPreparationFailureHint()}`;
  }
  return "行程状态：已勾安全确认；可以准备图上路线。";
});
const plainTripMinimalPrecheckSummary = computed(() => {
  // 普通首屏只保留一个现场安全确认；路线和定位复查放在后端执行 gate，避免前端堆叠预检步骤。
  if (!robotApiBaseUrl.value.trim()) {
    return "行程前确认：先连接默认小车。";
  }
  if (!plainManualSafetyConfirmed.value) {
    return "行程前确认：只需勾选现场安全确认；不会要求额外预检。";
  }
  if (plainTripMapWysiwygPending.value) {
    return `行程前确认：安全确认已完成；等待${plainTripMapWysiwygPendingText()}后再执行。`;
  }
  if (plainTripCurrentRouteVisible.value) {
    return "行程前确认：安全确认已完成；可以执行图上路线，后端会复查定位和路线。";
  }
  if (plainTripPreparedBySummary.value) {
    return "行程前确认：安全确认已完成；先刷新地图画面确认图上路线。";
  }
  return "行程前确认：安全确认已完成；先准备图上路线。";
});
const plainTripCurrentRouteVisible = computed(() => {
  // 只有当前路线真正画到地图上，普通首屏才允许执行“图上路线”；最近路线不能作为执行依据。
  const routePath = latestNavPathOverlay();
  return Boolean(routePath && !routePath.caption.startsWith("最近"));
});
const plainTripRecentRouteVisible = computed(() => {
  // 旧路线可以照实显示在地图上，但按钮必须明确要求重新准备，不能暗示可直接执行。
  const routePath = latestNavPathOverlay();
  return Boolean(routePath && routePath.caption.startsWith("最近"));
});

function plainTripVisibleRouteGoal() {
  const routePath = latestNavPathOverlay();
  if (!routePath || routePath.caption.startsWith("最近")) {
    return null;
  }
  return {
    goal_frame_id: routePath.executionGoal.frame_id,
    goal_x: routePath.executionGoal.x,
    goal_y: routePath.executionGoal.y,
    // 路线预览只有平面终点；朝向仍沿用当前显式设置，避免新增隐藏推断。
    goal_yaw: navGoalYaw.value,
  };
}

const canRefreshPlainTripPreparation = computed(() => {
  // 准备行程只刷新 no-motion planner proof；仍要求 operator 先完成同一个现场安全确认。
  return !deliveryNav2GoalReady.value && canRefreshNav2Proof.value && plainManualSafetyConfirmed.value;
});

const canRunPlainTripExecution = computed(() => {
  // 行程按钮承担普通首屏向导：无图上路线时只准备并刷新地图，已有图上路线时才执行。
  return !deliveryNav2GoalReady.value
    && !loading.value
    && !plainTripActionPending.value
    && !manualMotionActiveForTrip.value
    && robotApiBaseUrl.value.trim().length > 0
    && plainManualSafetyConfirmed.value
    && !plainTripMapWysiwygPending.value;
});

const plainTripPreparationButtonLabel = computed(() => {
  // 普通用户只看到“准备行程”；底层 no-motion Nav2 proof refresh 留在高级诊断。
  if (deliveryNav2GoalReady.value) {
    return "行程已完成";
  }
  if (!robotApiBaseUrl.value.trim()) {
    return "连接后准备行程";
  }
  if (nav2RefreshPending.value) {
    return "准备中（不发车）";
  }
  if (mapWysiwygRefreshPending.value) {
    return "等待地图刷新";
  }
  return plainManualSafetyConfirmed.value ? "准备行程（不发车）" : "先勾选确认";
});

const plainTripExecutionButtonLabel = computed(() => {
  // 真正执行仍由后端 confirm_navigation_execution gate 再次校验。
  if (deliveryNav2GoalReady.value) {
    return "行程已完成";
  }
  if (!robotApiBaseUrl.value.trim()) {
    return "连接后执行行程";
  }
  if (nav2RefreshPending.value) {
    return "准备路线中（不发车）";
  }
  if (navGoalExecutionLatestPending.value) {
    return "读取行程结果中";
  }
  if (loading.value || navGoalPreflightPending.value || navGoalExecutionPending.value) {
    return "执行中";
  }
  if (manualMotionActiveForTrip.value) {
    return "等待手控停止";
  }
  if (!plainManualSafetyConfirmed.value) {
    return "先勾选确认";
  }
  if (plainTripMapWysiwygPending.value && plainTripPreparedBySummary.value) {
    return "等待地图刷新";
  }
  if (plainTripRecentRouteVisible.value) {
    return "重新准备路线（不发车）";
  }
  if (!plainTripCurrentRouteVisible.value) {
    return plainTripPreparedBySummary.value ? "刷新图上路线" : "准备图上路线";
  }
  if (plainTripHasFreshUnprovenControlEvidence.value || plainTripHasFreshIncompleteEvidence.value || plainTripLatestNotProvenEvidence.value) {
    return "重新执行图上路线";
  }
  return plainTripPreparedBySummary.value ? "执行图上路线" : "执行行程";
});
const plainTripLatestButtonLabel = computed(() => {
  if (mapWysiwygRefreshPending.value) {
    return "等待地图刷新";
  }
  return deliveryNav2GoalReady.value ? "重新读取行程（只读）" : "读取行程结果（只读）";
});
const plainTripStopButtonLabel = computed(() => (
  // 行程执行时把 stop 放在行程区就近呈现；底层仍复用统一 base stop 兜底，不新增 Nav2 cancel 接口。
  manualCommandPending.value ? "停止中" : "行程停止（随时可点）"
));

const plainGoalProgressPending = computed(() => (
  loading.value
  || navGoalExecutionLatestPending.value
  || deliveryLatestPending.value
  || baseFeedbackSamplesPending.value
));
const canRefreshPlainGoalProgress = computed(() => (
  !plainGoalProgressPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));
const plainGoalProgressRefreshButtonLabel = computed(() => (
  plainGoalProgressPending.value
    ? "刷新中"
    : mapWysiwygRefreshPending.value
      ? "等待地图刷新"
      : "刷新进度（只读）"
));

const firstJogVisualMaterialReady = computed(() => {
  // first-jog readiness 由 PC summary 后端统一判定，避免普通首屏和 API 合同漂移。
  return robotSummary.value?.first_jog_readiness_summary?.visual_material_ready === true;
});

const firstJogMaterialRestoreReady = computed(() => {
  // delivery draft 会覆盖 latest operator report；已有视觉材料时允许 operator 重新确认基础安全三项。
  const firstJog = robotSummary.value?.first_jog_readiness_summary;
  if (firstJog?.status === "blocked_missing_basic_safety" && firstJog.visual_material_ready === true) {
    return true;
  }
  return firstJog?.status !== "ready_for_first_jog" && deliveryDraftVisualMaterialReady.value;
});

const firstJogMaterialRestoreSummary = computed(() => {
  // 上位机当前只有 latest operator report；送达草稿覆盖后，要把可恢复原因说清楚。
  const summary = robotSummary.value?.operator_hil_material_summary;
  const firstJog = robotSummary.value?.first_jog_readiness_summary;
  if (!summary || !firstJog) {
    return "operator report not loaded";
  }
  if (firstJogMaterialRestoreReady.value) {
    if (firstJog.status === "blocked_missing_basic_safety" && firstJog.visual_material_ready === true) {
      return `latest-only operator report is ${summary.site_state}; visual material kept; missing=${firstJog.missing_fields.join(",")}; action=restore first-jog confirmation`;
    }
    const refs = deliveryLatestDraftVisualRefs();
    return `delivery latest draft visual material kept; external=${refs.externalVideoRef || "not_loaded"}; camera=${refs.cameraArtifactRef || "not_loaded"}; first_jog=${firstJog.status}; action=restore first-jog confirmation`;
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

const firstJogMaterialRestoreBlocksMotion = computed(() => (
  firstJogMaterialRestoreReady.value && !plainFirstJogMaterialRestored.value
));

const canRestorePlainFirstJogMaterial = computed(() => (
  !loading.value
  && !previewBusy.value
  && !mapWysiwygRefreshPending.value
  && !plainFirstJogMaterialRestorePending.value
  && !operatorReportPending.value
  && robotApiBaseUrl.value.trim().length > 0
  && firstJogMaterialRestoreReady.value
));

const plainFirstJogMaterialRestoreButtonLabel = computed(() => {
  // 恢复会重写 latest operator report，必须等画面和地图读回稳定，避免把过期材料写成新结论。
  if (plainFirstJogMaterialRestorePending.value || operatorReportPending.value) {
    return "恢复中";
  }
  if (previewBusy.value) {
    return "等待画面稳定";
  }
  if (mapWysiwygRefreshPending.value) {
    return "等待地图刷新";
  }
  return "恢复试动确认";
});

const canSendPlainFirstJog = computed(() => {
  // 普通试动必须先有 first-jog 材料；送达草稿覆盖状态下必须先点“恢复试动确认”。
  if (!robotApiBaseUrl.value.trim() || loading.value || manualCommandPending.value) {
    return false;
  }
  if (plainFirstJogMaterialRestored.value || plainVisualMaterialSubmitted.value) {
    return true;
  }
  if (firstJogMaterialRestoreBlocksMotion.value) {
    return false;
  }
  return robotSummary.value?.first_jog_readiness_summary?.status === "ready_for_first_jog";
});

const canSendPlainWheelTrial = computed(() => {
  // wheel raw L/R 的重试只要求现场先确认轮速卡点；雷达缺口留给行程/键盘移动记录处理。
  return canSendPlainFirstJog.value && (!plainWheelZeroBlockerActive.value || plainWheelZeroBlockerChecked.value);
});

const plainWheelTrialDisabled = computed(() => !canSendPlainWheelTrial.value);

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
  if (firstJogMaterialRestoreBlocksMotion.value) {
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
  if (plainWheelEvidenceSaveFailed.value) {
    return { state: "保存失败", hint: "轮速已读到，但保存没有成功；请重试保存，不要直接进入行程。" };
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
      if (isZeroWheelPair(left, right) && plainWheelZeroBlockerChecked.value) {
        return { state: "待重试", hint: "轮速卡点已检查；请低速重试读取非零 L/R。" };
      }
      return { state: "待重试", hint: `已试动但 L/R=${left}/${right}，检查电机使能、供电、模式和现场空间后重试。` };
    }
    return { state: "待重试", hint: "已试动，但还没拿到非零 L/R。" };
  }
  if (firstJogMaterialRestoreBlocksMotion.value) {
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
  if (firstJogMaterialRestoreBlocksMotion.value) {
    return "先恢复确认再试动";
  }
  if (!firstJogVisualMaterialReady.value && !plainVisualMaterialSubmitted.value && !plainFirstJogMaterialRestored.value) {
    return "先记录画面再试动";
  }
  if (plainWheelZeroBlockerActive.value && plainWheelZeroBlockerChecked.value) {
    return "检查后重试读非零 L/R";
  }
  if (plainWheelZeroBlockerActive.value) {
    return "先查卡点再重试读非零 L/R";
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
  if (mapWysiwygRefreshPending.value) {
    return "等待地图刷新";
  }
  if (plainWheelEvidenceSaveFailed.value && plainFirstJogWheelEvidenceReady.value) {
    return "重试保存轮速记录";
  }
  if (plainFirstJogWheelEvidenceReady.value) {
    return "保存轮速记录";
  }
  if (firstJogMaterialRestoreBlocksMotion.value) {
    return "保存轮速记录（先恢复确认）";
  }
  if (!firstJogVisualMaterialReady.value && !plainVisualMaterialSubmitted.value && !plainFirstJogMaterialRestored.value) {
    return "保存轮速记录（先记录画面）";
  }
  if (!plainFirstJogResult.value) {
    return "保存轮速记录（先试动）";
  }
  return "保存轮速记录（等非零 L/R）";
});

const canSavePlainWheelEvidence = computed(() => (
  !loading.value
  && !mapWysiwygRefreshPending.value
  && !plainWheelEvidenceSavePending.value
  && !operatorReportPending.value
  && robotApiBaseUrl.value.trim().length > 0
  && plainFirstJogWheelEvidenceReady.value
));

const plainWheelEvidenceSaveFailed = computed(() => (
  Boolean(plainWheelEvidenceSaveResult.value)
  && !(plainWheelEvidenceSaveResult.value?.proxy_status === "report_forwarded" && plainWheelEvidenceSaveResult.value.status !== "blocked")
));

const plainWheelReadbackButtonLabel = computed(() => (
  baseFeedbackSamplesPending.value
    ? "刷新中"
    : mapWysiwygRefreshPending.value
      ? "等待地图刷新"
      : "刷新当前轮速（只读）"
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
  // 静止状态下 L/R=0/0 是正常现象；只有运动窗口已发出仍为 0/0，才进入排障卡点。
  const firstJogValues = plainFirstJogResult.value?.remote_motion_key_values;
  if (plainFirstJogResult.value?.proxy_status === "command_forwarded"
    && isZeroWheelPair(firstJogValues?.wheel_feedback_latest_raw_left, firstJogValues?.wheel_feedback_latest_raw_right)) {
    return WHEEL_ZERO_NEXT_ACTION_SUMMARY;
  }
  return "";
});

const plainWheelZeroBlockerActive = computed(() => plainWheelNextActionSummary.value !== "");

const plainWheelZeroBlockerSummary = computed(() => {
  // 这个确认只服务现场排障流程，不写 operator report，也不证明 wheel raw L/R 非零。
  if (!plainWheelZeroBlockerActive.value) {
    return "";
  }
  if (plainWheelZeroBlockerChecked.value) {
    return "轮速卡点已检查：电机使能、供电、模式和现场空间已确认；下一步低速重试读非零 L/R。";
  }
  return "轮速卡点：请确认电机使能、供电、模式和现场空间后再重试。";
});

const plainWheelZeroBlockerButtonLabel = computed(() => (
  plainWheelZeroBlockerChecked.value ? "轮速卡点已检查" : "已检查轮速卡点"
));

const plainWheelReadbackSummary = computed(() => {
  // 只读底盘反馈可以解释“当前为什么还不是非零证据”，但不能替代试动窗口材料。
  const base = robotSummary.value?.readback_summary.base;
  const plainVoltage = formatPlainVoltage(base?.feedback_voltage_v);
  const voltage = plainVoltage ? `；反馈电压约 ${plainVoltage}V` : "";
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
  if (effectiveLidarReadback.value?.lifecycle_running === "true") {
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
  // 普通手控预检收敛为一个用户可见安全确认；后端仍负责固定方向、限速、限时和 stop 兜底。
  return !manualCommandPending.value
    && !navGoalExecutionPending.value
    && !loading.value
    && robotApiBaseUrl.value.trim().length > 0
    && plainManualSafetyConfirmed.value;
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
  if (!plainManualSafetyConfirmed.value) {
    missing.add("安全确认");
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
  if (navGoalExecutionPending.value) {
    return "行程正在执行，暂不启动键盘手控。";
  }
  const missingLabels = plainKeyboardMissingLabels.value;
  return `还差：${missingLabels.join("、")}。`;
});

const plainKeyboardMotionProofNextStep = computed(() => {
  const missingLabels = plainKeyboardMissingLabels.value;
  const higherPriorityMissing = ["小车连接", "键盘入口", "安全确认"]
    .some((label) => missingLabels.includes(label));
  // 只有连接、安全和画面这些前置步骤都过了，运动证据才是键盘 gate 的第一下一步。
  if (higherPriorityMissing) {
    return "";
  }
  if (missingLabels.includes("轮速记录")) {
    return "wheel";
  }
  if (missingLabels.includes("雷达移动记录")) {
    return "lidar";
  }
  return "";
});

function plainKeyboardBlockedActionLabel(missingLabels: string[]): string {
  // 按普通流程顺序提示下一步，避免按钮只显示抽象缺项数量。
  if (missingLabels.includes("小车连接")) {
    return "先连接";
  }
  if (missingLabels.includes("键盘入口")) {
    return "先复查入口";
  }
  if (missingLabels.includes("安全确认")) {
    return "先勾安全确认";
  }
  return "";
}

const plainKeyboardArmButtonLabel = computed(() => {
  // 启用只让键盘面板获得焦点；真正手控必须后续按住方向键。
  if (navGoalExecutionPending.value) {
    return "启用键盘（行程中）";
  }
  const missingLabels = plainKeyboardMissingLabels.value;
  const missingCount = missingLabels.length;
  const actionLabel = plainKeyboardBlockedActionLabel(missingLabels);
  if (actionLabel) {
    return `启用键盘（${actionLabel}）`;
  }
  return missingCount > 0 ? `启用键盘（还差 ${missingCount} 项）` : "启用键盘（按键才动）";
});

const plainKeyboardRecheckButtonLabel = computed(() => {
  // 复查按钮同样显示缺项数量；点击仍只刷新只读进度，不会发送手控。
  if (mapWysiwygRefreshPending.value) {
    return "等待地图刷新";
  }
  if (navGoalExecutionPending.value) {
    return "复查手控条件（行程中，不发车）";
  }
  const missingLabels = plainKeyboardMissingLabels.value;
  const missingCount = missingLabels.length;
  const actionLabel = plainKeyboardBlockedActionLabel(missingLabels);
  if (actionLabel) {
    return `复查手控条件（${actionLabel}，不发车）`;
  }
  return missingCount > 0 ? `复查手控条件（还差 ${missingCount} 项，不发车）` : "复查手控条件";
});
const canRefreshPlainKeyboardGate = computed(() => (
  !plainGoalProgressPending.value
  && !mapWysiwygRefreshPending.value
  && robotApiBaseUrl.value.trim().length > 0
));

const plainKeyboardNextActionSummary = computed(() => {
  // 键盘 gate 缺项可能较多；现场只需要知道当前先做哪个普通动作。
  if (canUseKeyboardControl.value) {
    if (!wheelClosureEvidence.value.ready) {
      const { left, right } = currentWheelReadback.value;
      const readbackText = currentWheelReadbackLoaded.value ? `当前 L/R=${left}/${right}；` : "";
      return `下一步：启用键盘并按住方向键，${readbackText}读取非零 L/R 并连续验证。`;
    }
    return "";
  }
  if (!robotApiBaseUrl.value.trim()) {
    return "下一步：连接小车。";
  }
  if (!keyboardContractReady.value) {
    return "下一步：复查手控条件。";
  }
  if (navGoalExecutionPending.value) {
    return "下一步：等待行程执行返回，必要时按停止接管。";
  }
  if (!plainManualSafetyConfirmed.value) {
    return "下一步：勾选安全确认。";
  }
  return "下一步：点启用键盘，按住方向键才会动。";
});
const plainKeyboardSafetySummary = computed(() => {
  // 把“勾安全确认即可启用键盘”的普通路径直接写出来；这里不自动启用，也不发送方向脉冲。
  if (!robotApiBaseUrl.value.trim()) {
    return "键盘手控：先连接默认小车。";
  }
  if (!keyboardContractReady.value) {
    return "键盘手控：入口还没读到，先复查手控条件。";
  }
  if (navGoalExecutionPending.value) {
    return "键盘手控：行程正在执行，暂不启用新的手控。";
  }
  if (!plainManualSafetyConfirmed.value) {
    return "键盘手控：勾选安全确认后即可启用；按住方向键才会动。";
  }
  return canUseKeyboardControl.value
    ? "键盘手控：安全确认已完成；现在可启用键盘，按住方向键才会动。"
    : "键盘手控：安全确认已完成，等待手控入口复查。";
});

const plainKeyboardControlSummary = computed(() => {
  // 普通首屏只说“能不能用”和“怎么停”，不展示 operator report 字段名或 HIL 术语。
  if (keyboardHeldDirection.value) {
    return { state: "手控中", hint: "按住点动中；松开按键、窗口失焦或页面隐藏会自动停止。" };
  }
  if (keyboardControlStatus.value.startsWith("blocked_keyboard_pulse_failed")) {
    return { state: "待验证", hint: "上次按键没有成功发送；检查后再按住方向键。" };
  }
  if (keyboardControlStatus.value.startsWith("blocked_keyboard_stop_failed")) {
    return { state: "停止失败", hint: "上次停止没有成功发送；请先现场确认小车已停，再重新启用键盘。" };
  }
  if (keyboardStopSettledAfterPulse.value) {
    return { state: "已验证", hint: "键盘连续手控已完成 2 次连续脉冲验证，且停止已发送；需要继续移动可按住方向键，松开即停。" };
  }
  if (keyboardManualPulseObserved.value) {
    return { state: "待停止", hint: "已完成 2 次连续脉冲验证；松开按键后完成停止收口。" };
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
  if (navGoalExecutionPending.value) {
    return "行程正在执行；暂不发送新的手控动作，必要时按停止接管。";
  }
  if (!plainManualSafetyConfirmed.value) {
    return "先勾选安全确认：人在旁边、周围安全、停止手段就绪。";
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
  // 首屏只呈现定位/停靠状态和最小安全确认，不再要求普通用户额外点“移动前检查”。
  if (localizationResetPending.value) {
    return { state: "定位中", hint: "正在重新定位；不会发车。" };
  }
  if (cameraFirstFrameProbePending.value) {
    return { state: "记录中", hint: "正在读取当前画面；不会发车。" };
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
    ? { state: "待命", hint: "安全确认已勾；需要时可直接停止。" }
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
    confirm_hil_checklist: plainManualSafetyConfirmed.value,
  } as const;
}

function requestBodyForKeyboardDirection(direction: ManualDirection) {
  // 键盘连续手控采用短脉冲重复发送，降低“按键卡住”时单条命令持续过久的风险。
  return {
    direction,
    speed: Math.min(Math.max(jogSpeedMps.value, 0), manualSpeedLimit.value),
    duration_ms: Math.min(Math.max(keyboardJogDurationMs.value, 0), manualDurationLimit.value),
    confirm_hil_checklist: plainManualSafetyConfirmed.value,
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
    missing_required_material: [],
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
    missing_required_material: [],
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
    missing_required_material: [],
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

function makeMapPreviewFallback(reason: string): RobotControlMapPreviewResponse {
  // 地图画面刷新失败也要留在普通首屏；不能清空成“还没读到”而丢掉本轮失败原因。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_map_preview_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "preview_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    remote_endpoint: "/api/map/preview",
    remote_http_status: null,
    status: "blocked",
    map_name: "",
    map_yaml_name: "",
    map_image_name: "",
    width: 0,
    height: 0,
    resolution: null,
    origin: [],
    cell_counts: {},
    has_free_cells: false,
    navigation_quality: "not_loaded",
    image_mime_type: "not_loaded",
    image_data_url: "",
    source_image_format: "not_loaded",
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function makeRadarStatusFallback(reason: string): RobotControlRadarStatusResponse {
  // 地图刷新顺带读雷达状态；雷达状态失败只能影响 marker 口径，不能吞掉地图画面。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_radar_status_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    proxy_status: "status_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    workstation_endpoint: "/api/robot-control/radar/status",
    remote_endpoint: "/api/radar/status",
    remote_method: "GET",
    remote_http_status: null,
    status: "blocked",
    radar_key_values: {},
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

function plainVisualMaterialRequestBody(options: { videoRef?: string; cameraArtifactRef?: string; visibleContentProven?: boolean } = {}): RobotControlOperatorReportRequest {
  // 普通记录画面只提交可追溯 ref；当前画面样张来自固定 camera probe，不能手写任意工程字段。
  const videoRef = (options.videoRef ?? plainExternalVideoRef.value).trim();
  const cameraArtifactRef = options.cameraArtifactRef?.trim() ?? "";
  const visibleContentProven = options.visibleContentProven === true;
  const inheritedProgressClaims = inheritedProgressClaimsFromSummary();
  return {
    operator_present: true,
    evidence_ref: `${visibleContentProven ? "plain-first-jog-camera" : "plain-first-jog-video"}-${Date.now()}`,
    physical_clearance_confirmed: true,
    emergency_stop_ready: true,
    observed_motion: false,
    observed_stop: true,
    reported_at: new Date().toISOString(),
    operator_notes: "plain PC first-jog visual material; does not prove wheel feedback, lidar delta, route map, or delivery success.",
    structured_hil_claims: {
      external_video_recorded: true,
      external_video_ref: videoRef,
      visible_content_proven: visibleContentProven,
      ...(cameraArtifactRef ? { camera_artifacts_ref: cameraArtifactRef } : {}),
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
  const deliveryRefs = deliveryLatestDraftVisualRefs();
  const wheelRef = claimRefFromSummary(summary?.wheel_feedback);
  const scanDeltaRef = claimRefFromSummary(summary?.lidar_delta);
  const routeMapRef = claimRefFromSummary(summary?.route_map) || deliveryRefs.routeMapRef;
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
  const deliveryRefs = deliveryLatestDraftVisualRefs();
  const externalVideoRef = claimRefFromSummary(summary?.external_video) || deliveryRefs.externalVideoRef;
  const cameraArtifactRef = claimRefFromSummary(summary?.camera_visible) || deliveryRefs.cameraArtifactRef;
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
  rawFailureReason.value = "";
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
      rawFailureReason.value = failureReason.value;
    }
  } catch (err) {
    previewStatus.value = "peer_cleanup_failed";
    failureReason.value = err instanceof Error ? err.message : "peer_cleanup_failed";
    rawFailureReason.value = failureReason.value;
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

async function refreshMapPreview(options: { countForFreeRoamSession?: boolean; freeRoamLiveRefresh?: boolean; savedMapRefresh?: boolean; tripExecutionRefresh?: boolean; radarStatusRefresh?: boolean } = {}): Promise<void> {
  // 地图画面只读真实 YAML/PGM 预览；失败时保留状态视图，不阻断 summary 刷新。
  if (!robotApiBaseUrl.value.trim() || mapWysiwygRefreshPending.value) {
    return;
  }
  const refreshStartedDuringFreeRoamRuntime = options.countForFreeRoamSession === true && mapRuntimeStarted.value;
  const liveRefreshDuringFreeRoam = options.freeRoamLiveRefresh === true && mapRuntimeStarted.value;
  const refreshAfterSavedMap = (options.savedMapRefresh === true || mapSavedThisSession.value) && mapSavedThisSession.value;
  const refreshAfterTripExecution = options.tripExecutionRefresh === true && navGoalExecutionResult.value?.proxy_status === "execution_forwarded";
  if (refreshStartedDuringFreeRoamRuntime) {
    plainFreeRoamMapPreviewRefreshFailedForSession.value = false;
  }
  if (refreshAfterSavedMap) {
    plainFreeRoamSavedMapPreviewRefreshFailed.value = false;
  }
  if (refreshAfterTripExecution) {
    plainTripPostExecutionMapPreviewRefreshFailed.value = false;
  }
  mapPreviewPending.value = true;
  try {
    const shouldRefreshRadarStatus = options.radarStatusRefresh === true;
    const [mapPreview, radarStatus] = await Promise.all([
      getRobotControlMapPreview(robotApiBaseUrl.value).catch((err: unknown) =>
        makeMapPreviewFallback(err instanceof Error ? err.message : "map_preview_request_failed"),
      ),
      shouldRefreshRadarStatus
        ? getRobotControlRadarStatus(robotApiBaseUrl.value).catch((err: unknown) =>
          makeRadarStatusFallback(err instanceof Error ? err.message : "radar_status_request_failed"),
        )
        : Promise.resolve(null),
    ]);
    mapPreviewResult.value = mapPreview;
    if (radarStatus) {
      radarStatusResult.value = radarStatus;
    }
    if (mapPreviewResult.value?.proxy_status === "preview_forwarded") {
      plainTripPostExecutionMapPreviewRefreshFailed.value = false;
    } else if (refreshAfterTripExecution) {
      plainTripPostExecutionMapPreviewRefreshFailed.value = true;
    }
    if (refreshStartedDuringFreeRoamRuntime && mapRuntimeStarted.value && mapPreviewResult.value?.proxy_status === "preview_forwarded") {
      plainFreeRoamMapPreviewFreshForSession.value = true;
      plainFreeRoamMapPreviewRefreshFailedForSession.value = false;
    } else if (refreshStartedDuringFreeRoamRuntime && mapRuntimeStarted.value) {
      plainFreeRoamMapPreviewRefreshFailedForSession.value = true;
    }
    if (liveRefreshDuringFreeRoam && mapRuntimeStarted.value && mapPreviewResult.value?.proxy_status === "preview_forwarded") {
      plainFreeRoamLiveMapPreviewRefreshedForHold.value = true;
    }
    if (refreshAfterSavedMap && mapSavedThisSession.value && mapPreviewResult.value?.proxy_status === "preview_forwarded") {
      plainFreeRoamSavedMapPreviewFreshForSession.value = true;
      plainFreeRoamSavedMapPreviewRefreshFailed.value = false;
    } else if (refreshAfterSavedMap && mapSavedThisSession.value) {
      plainFreeRoamSavedMapPreviewRefreshFailed.value = true;
    }
  } catch (err) {
    mapPreviewResult.value = makeMapPreviewFallback(err instanceof Error ? err.message : "map_preview_request_failed");
    radarStatusResult.value = makeRadarStatusFallback(err instanceof Error ? err.message : "radar_status_request_failed");
    if (refreshAfterTripExecution) {
      plainTripPostExecutionMapPreviewRefreshFailed.value = true;
    }
    if (refreshStartedDuringFreeRoamRuntime && mapRuntimeStarted.value) {
      plainFreeRoamMapPreviewRefreshFailedForSession.value = true;
    }
    if (refreshAfterSavedMap && mapSavedThisSession.value) {
      plainFreeRoamSavedMapPreviewRefreshFailed.value = true;
    }
  } finally {
    mapPreviewPending.value = false;
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

async function refreshRadarProof(options: { focusAfterReady?: boolean } = {}): Promise<void> {
  // Radar refresh 只刷新 no-motion scan proof snapshot，不开启任何底盘动作。
  if (mapWysiwygRefreshPending.value) {
    return;
  }
  await runRefreshAction(
    "radar_scan_proof_refresh",
    () => postRobotControlRadarScanProofRefresh(robotApiBaseUrl.value),
    radarRefreshResult,
    radarRefreshPending,
  );
  try {
    // proof refresh 后立即读固定 radar/status，让地图 marker 和 readiness 使用同一轮最新状态。
    radarStatusResult.value = await getRobotControlRadarStatus(robotApiBaseUrl.value);
  } catch (err) {
    radarStatusResult.value = makeRadarStatusFallback(err instanceof Error ? err.message : "radar_status_request_failed");
  }
  if (options.focusAfterReady !== false) {
    await focusPlainGoalProgressAfterRadarReady();
  }
}

async function focusPlainGoalProgressAfterRadarReady(): Promise<void> {
  // 雷达只是前置条件；刷新确认运行后回到当前第一缺口，不固定落到轮速。
  await nextTick();
  if (radarSummary.value.state !== "雷达已运行") {
    return;
  }
  const targetId = plainGoalProgressPrimaryTarget.value;
  if (!targetId) {
    return;
  }
  focusPlainGoalProgressTarget(targetId);
}

async function runRadarLifecycleAction(
  action: "start" | "stop",
  request: () => Promise<RobotControlRadarLifecycleResponse>,
): Promise<void> {
  // lifecycle 只在高级诊断内触发；结果回写最近一次摘要并刷新只读状态。
  if (!robotApiBaseUrl.value.trim() || radarLifecyclePending.value) {
    return;
  }
  if (action === "start" && mapWysiwygRefreshPending.value) {
    return;
  }
  radarLifecyclePending.value = true;
  radarLifecyclePendingAction.value = action;
  try {
    radarLifecycleResult.value = await request();
  } catch (err) {
    radarLifecycleResult.value = makeRadarLifecycleFallback(action, err instanceof Error ? err.message : `${action}_request_failed`);
  } finally {
    radarLifecyclePending.value = false;
    radarLifecyclePendingAction.value = null;
    await refreshConsole();
  }
}

async function startRadarLifecycle(): Promise<void> {
  // 启动雷达只走固定传感器 endpoint；不会调用底盘、Nav2 或 /cmd_vel。
  await runRadarLifecycleAction("start", () => postRobotControlRadarStart(robotApiBaseUrl.value));
}

async function startPlainRadarLifecycle(): Promise<void> {
  // 普通首屏启动成功后自动做一次只读刷新；失败时留在启动按钮，避免现场误以为已进入运行阶段。
  await startRadarLifecycle();
  if (radarStartSucceeded(radarLifecycleResult.value)) {
    await refreshRadarProof();
    await nextTick();
    if (radarSummary.value.state !== "雷达已运行") {
      plainRadarRefreshButton.value?.focus({ preventScroll: true });
    }
    return;
  }
  await nextTick();
  (plainRadarStartButton.value ?? plainRadarRefreshButton.value)?.focus({ preventScroll: true });
}

async function stopRadarLifecycle(): Promise<void> {
  // 停止雷达用于真实上位机 dry-run guard smoke；不会触发任何底盘运动。
  await runRadarLifecycleAction("stop", () => postRobotControlRadarStop(robotApiBaseUrl.value));
}

async function refreshMapProof(): Promise<void> {
  // Map refresh 只刷新 no-motion map proof snapshot，不开启建图、导航或路径执行。
  if (mapWysiwygRefreshPending.value) {
    return;
  }
  await runRefreshAction(
    "map_proof_refresh",
    () => postRobotControlMapProofRefresh(robotApiBaseUrl.value),
    mapRefreshResult,
    mapRefreshPending,
  );
  await refreshMapPreview();
}

async function refreshNav2Proof(): Promise<void> {
  // Nav2 refresh 只做 no-motion planner proof；随后刷新地图画面，让路线点和真实底图一起显示。
  if (mapWysiwygRefreshPending.value) {
    return;
  }
  await runRefreshAction(
    "nav2_no_motion_proof_refresh",
    () => postRobotControlNav2ProofRefresh(robotApiBaseUrl.value),
    nav2RefreshResult,
    nav2RefreshPending,
  );
  await refreshMapPreview();
}

async function resetLocalizationProof(): Promise<void> {
  // 重新定位只走固定 /api/localize/reset；发布一次初始位姿，不请求路径、不发 /cmd_vel。
  if (mapWysiwygRefreshPending.value) {
    return;
  }
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

async function runNavGoalExecution(goalOverride?: MapNavGoal): Promise<void> {
  // 真正执行 NavigateToPose 必须显式确认；结果只作为执行证据，不自动标记交付成功。
  if (!robotApiBaseUrl.value.trim() || navGoalExecutionPending.value) {
    return;
  }
  const goalRequest = goalOverride ?? {
    goal_frame_id: "map" as const,
    goal_x: navGoalX.value,
    goal_y: navGoalY.value,
    goal_yaw: navGoalYaw.value,
  };
  navGoalExecutionAttemptGoal.value = goalRequest;
  navGoalExecutionPendingGoal.value = goalRequest;
  plainTripStopRequestedDuringExecution.value = false;
  plainTripStopSettledDuringExecution.value = false;
  plainTripStopResultDuringExecution.value = null;
  navGoalExecutionPending.value = true;
  try {
    navGoalExecutionResult.value = await postRobotControlNav2GoalExecute(robotApiBaseUrl.value, {
      goal_frame_id: goalRequest.goal_frame_id,
      goal_x: goalRequest.goal_x,
      goal_y: goalRequest.goal_y,
      goal_yaw: goalRequest.goal_yaw,
      result_timeout_s: navGoalExecutionTimeoutS.value,
      confirm_navigation_execution: confirmNavigationExecution.value,
    });
  } catch (err) {
    navGoalExecutionResult.value = makeNavGoalExecutionFallback(err instanceof Error ? err.message : "nav_goal_execution_request_failed");
  } finally {
    navGoalExecutionPending.value = false;
    navGoalExecutionPendingGoal.value = null;
    plainTripStopRequestedDuringExecution.value = false;
    plainTripStopSettledDuringExecution.value = false;
    plainTripStopResultDuringExecution.value = null;
    await refreshConsole();
  }
}

async function runPlainTripExecution(): Promise<void> {
  // 普通入口先保证路线所见即所得；没有当前图上路线时，只做 no-motion 准备和地图刷新。
  if (!canRunPlainTripExecution.value) {
    return;
  }
  plainTripPostExecutionMapPreviewRefreshFailed.value = false;
  let routeGoal = plainTripVisibleRouteGoal();
  if (!routeGoal) {
    await refreshNav2Proof();
    await nextTick();
    (enabledButton(plainTripExecuteButton.value) ?? enabledButton(plainTripPrepareButton.value))?.focus({ preventScroll: true });
    return;
  }
  confirmNavigationExecution.value = true;
  await runNavGoalExecution(routeGoal);
  await refreshMapPreview({ tripExecutionRefresh: true });
  if (navGoalExecutionResult.value?.proxy_status === "execution_forwarded") {
    await loadNavGoalExecutionLatest();
  }
  fillDeliveryRouteRefFromLatestNav2();
  if (deliveryNav2GoalReady.value) {
    await loadDeliveryLatest();
    await focusPlainDeliveryStatusPanel();
  }
}

async function stopPlainTripExecution(): Promise<void> {
  // 行程区 stop 只做就近兜底显示；实际请求仍复用统一 base stop，不声明 Nav2 action 已取消。
  if (navGoalExecutionPending.value) {
    plainTripStopRequestedDuringExecution.value = true;
    plainTripStopSettledDuringExecution.value = false;
    plainTripStopResultDuringExecution.value = null;
  }
  const stopResult = await sendStop();
  if (navGoalExecutionPending.value && plainTripStopRequestedDuringExecution.value && !manualCommandPending.value) {
    // null 只说明本次没有拿到新 stop 回包，不能覆盖 sendStop 内已经记录的成功/失败结果。
    if (stopResult) {
      plainTripStopResultDuringExecution.value = stopResult;
      plainTripStopSettledDuringExecution.value = !baseStopResultFailed(stopResult);
    }
  }
}

async function loadNavGoalExecutionLatest(options: { allowDuringMapRefresh?: boolean } = {}): Promise<void> {
  // 读取最近执行结果只走固定 GET 代理；用于页面刷新后补回 route/map evidence ref。
  if (!robotApiBaseUrl.value.trim() || navGoalExecutionLatestPending.value || (!options.allowDuringMapRefresh && mapWysiwygRefreshPending.value)) {
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

async function loadDeliveryLatest(options: { allowDuringMapRefresh?: boolean } = {}): Promise<void> {
  // delivery latest 只读最近 gate 结论；用于明确现场还缺哪些送达材料。
  if (!robotApiBaseUrl.value.trim() || deliveryLatestPending.value || (!options.allowDuringMapRefresh && mapWysiwygRefreshPending.value)) {
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
    loadNavGoalExecutionLatest({ allowDuringMapRefresh: true }),
    loadDeliveryLatest({ allowDuringMapRefresh: true }),
  ]);
}

async function refreshPlainGoalProgress(): Promise<void> {
  // 普通首屏刷新进度只读 summary、底盘反馈、最近行程和送达状态，不执行行程、不保存材料、不确认送达。
  if (!robotApiBaseUrl.value.trim() || plainGoalProgressPending.value || mapWysiwygRefreshPending.value) {
    return;
  }
  await refreshConsole();
  await Promise.all([
    runBaseFeedbackSamples({ refreshAfter: false }),
    preloadGoalClosureReadbacks(),
  ]);
}

async function refreshPlainKeyboardGate(): Promise<void> {
  // 键盘复查仍只读刷新；刷新后把焦点带到下一步按钮，不自动启用键盘或发送手控。
  if (!canRefreshPlainKeyboardGate.value) {
    return;
  }
  await refreshPlainGoalProgress();
  await nextTick();
  focusPlainKeyboardNextTarget();
}

function focusPlainGoalProgressTarget(targetId: string): void {
  // 进度区的“去处理”只做本页定位，不能顺手触发行程、送达、手控或任何材料提交。
  const targetMap: Record<string, HTMLElement | null> = {
    wheel: plainWheelGoalTarget(),
    trip: plainTripGoalTarget(),
    delivery: plainDeliveryGoalTarget(),
    keyboard: plainKeyboardNextTarget(),
  };
  const target = targetMap[targetId];
  if (!target) {
    return;
  }
  target.scrollIntoView?.({ block: "center", behavior: "smooth" });
  target.focus({ preventScroll: true });
}

function plainWheelGoalTarget(): HTMLElement | null {
  // 轮速目标的跳转要落到现场“下一手动作”，否则用户还得在面板里二次找卡点。
  if (firstJogMaterialRestoreBlocksMotion.value) {
    return enabledButton(plainMotionRestoreButton.value)
      ?? enabledButton(plainFirstJogRestoreButton.value)
      ?? plainWheelRecordPanel.value;
  }
  if (plainWheelZeroBlockerActive.value && !plainWheelZeroBlockerChecked.value) {
    return enabledButton(plainWheelZeroCheckButton.value) ?? plainWheelRecordPanel.value;
  }
  if (plainWheelZeroBlockerChecked.value) {
    return enabledButton(plainWheelTrialButton.value) ?? plainWheelRecordPanel.value;
  }
  if (!currentWheelReadbackLoaded.value && canRunBaseFeedbackSamples.value) {
    return enabledButton(plainWheelReadbackButton.value) ?? plainWheelRecordPanel.value;
  }
  if (canSendPlainFirstJog.value) {
    return enabledButton(plainWheelTrialButton.value) ?? plainWheelRecordPanel.value;
  }
  return plainWheelRecordPanel.value;
}

function plainTripGoalTarget(): HTMLElement | null {
  // 行程目标也落到真实下一手控件；只移动焦点，不自动勾选、不执行 Nav2。
  if (deliveryNav2GoalReady.value) {
    return enabledButton(plainTripLatestButton.value) ?? plainTripRunPanel.value;
  }
  if (plainTripRadarBlocked.value) {
    return plainRadarNextTarget() ?? plainTripRunPanel.value;
  }
  if (!plainManualSafetyConfirmed.value) {
    return plainTripSafetyCheckbox.value ?? plainTripRunPanel.value;
  }
  return enabledButton(plainTripExecuteButton.value)
    ?? enabledButton(plainTripPrepareButton.value)
    ?? enabledButton(plainTripLatestButton.value)
    ?? plainTripRunPanel.value;
}

function plainDeliveryGoalTarget(): HTMLElement | null {
  // 送达目标同样落到现场下一手动作；这里只移动焦点，最终提交仍必须 operator 再点一次。
  const missingLabels = plainDeliveryConfirmMissingLabels.value;
  if (missingLabels.includes("本轮行程")) {
    if (plainTripRadarBlocked.value) {
      return plainRadarNextTarget() ?? plainDeliveryStatusPanel.value;
    }
    return plainTripRunPanel.value ?? plainDeliveryStatusPanel.value;
  }
  if (missingLabels.includes("本轮行程材料") || missingLabels.includes("送达材料")) {
    return enabledButton(plainDeliveryPrefillButton.value)
      ?? enabledButton(plainDeliveryDraftSaveButton.value)
      ?? plainDeliveryStatusPanel.value;
  }
  if (deliveryOperatorConfirmationReady.value) {
    return enabledButton(plainDeliveryConfirmSubmitButton.value) ?? plainDeliveryFinalPanel.value;
  }
  return enabledButton(plainDeliveryAllConfirmedButton.value) ?? plainDeliveryFinalPanel.value;
}

async function focusPlainDeliveryStatusPanel(): Promise<void> {
  // 行程成功后只把现场带到送达材料区；不能自动准备材料、提交报告或确认送达。
  await nextTick();
  const target = plainDeliveryStatusPanel.value;
  if (!target) {
    return;
  }
  target.scrollIntoView?.({ block: "center", behavior: "smooth" });
  target.focus({ preventScroll: true });
}

async function focusPlainDeliveryDraftSaveButton(): Promise<void> {
  // 送达材料准备好后只聚焦草稿保存按钮；是否保存仍必须由现场人员显式点击。
  await nextTick();
  const target = plainDeliveryDraftSaveButton.value;
  if (!target || target.disabled) {
    return;
  }
  target.scrollIntoView?.({ block: "center", behavior: "smooth" });
  target.focus({ preventScroll: true });
}

async function focusPlainDeliveryConfirmSubmitButton(): Promise<void> {
  // 最终确认勾齐后只聚焦红色提交按钮；提交 delivery gate 仍必须另点一次。
  await nextTick();
  const target = plainDeliveryConfirmSubmitButton.value;
  if (!target || target.disabled || !plainDeliveryConfirmReady.value) {
    return;
  }
  target.scrollIntoView?.({ block: "center", behavior: "smooth" });
  target.focus({ preventScroll: true });
}

async function focusKeyboardPanelAfterDeliverySuccess(): Promise<void> {
  // 送达 gate 通过后只把现场带到键盘区；若已满足 gate，则聚焦启用按钮但不自动启用。
  await nextTick();
  focusPlainKeyboardNextTarget({ scroll: true });
}

function focusPlainKeyboardNextTarget(options: { scroll?: boolean } = {}): void {
  // 键盘 gate 未满足时直接带到真实补证动作；仍只改变焦点，不触发任何接口。
  const target = plainKeyboardNextTarget();
  if (!target) {
    return;
  }
  if (options.scroll) {
    target.scrollIntoView?.({ block: "center", behavior: "smooth" });
  }
  target.focus({ preventScroll: true });
}

function enabledButton(button: HTMLButtonElement | null): HTMLButtonElement | null {
  return button && !button.disabled ? button : null;
}

function plainRadarNextTarget(): HTMLElement | null {
  // LiDAR delta 依赖雷达先运行；若普通首屏已暴露启动/刷新入口，优先带现场处理传感器。
  if (showPlainRadarStart.value) {
    return enabledButton(plainRadarStartButton.value)
      ?? enabledButton(plainRadarRefreshButton.value)
      ?? plainRadarRefreshButton.value;
  }
  return enabledButton(plainRadarRefreshButton.value) ?? plainRadarRefreshButton.value;
}

function plainKeyboardNextTarget(): HTMLElement | null {
  if (canArmKeyboardControl.value) {
    return enabledButton(keyboardControlArmButton.value) ?? keyboardControlPanel.value;
  }
  if (firstJogMaterialRestoreBlocksMotion.value) {
    return enabledButton(plainFirstJogRestoreButton.value) ?? plainWheelRecordPanel.value;
  }
  if (plainKeyboardMotionProofNextStep.value === "wheel") {
    return enabledButton(plainWheelSaveButton.value)
      ?? enabledButton(plainWheelZeroCheckButton.value)
      ?? enabledButton(plainWheelTrialButton.value)
      ?? plainWheelRecordPanel.value;
  }
  if (plainKeyboardMotionProofNextStep.value === "lidar") {
    return plainRadarNextTarget()
      ?? enabledButton(plainWheelTrialButton.value)
      ?? enabledButton(plainWheelSaveButton.value)
      ?? plainWheelRecordPanel.value;
  }
  return enabledButton(keyboardControlRecheckButton.value) ?? keyboardControlPanel.value;
}

function plainFreeRoamNextTarget(): HTMLElement | null {
  // 扫图向导只把焦点带到下一手动作；不会自动勾选、启动地图、发送手控或保存。
  if (!plainManualSafetyConfirmed.value) {
    return plainFreeRoamConfirmCheckbox.value;
  }
  if (!mapRuntimeStarted.value && !mapSavedThisSession.value) {
    return enabledButton(plainFreeRoamStartButton.value) ?? plainFreeRoamStartButton.value;
  }
  if (freeRoamAutonomyPendingAction.value) {
    return plainFreeRoamAutoStopButton.value
      ?? enabledButton(plainFreeRoamMapRefreshButton.value)
      ?? plainFreeRoamStartButton.value;
  }
  if (freeRoamAutonomyStartedThisSession.value) {
    return enabledButton(plainFreeRoamAutoStopButton.value)
      ?? enabledButton(plainFreeRoamMapRefreshButton.value)
      ?? plainFreeRoamStartButton.value;
  }
  if (freeRoamAutonomyStoppedThisSession.value) {
    return plainFreeRoamMapPreviewFreshForSession.value
      ? enabledButton(plainFreeRoamSaveButton.value) ?? plainFreeRoamSaveButton.value
      : enabledButton(plainFreeRoamMapRefreshButton.value) ?? plainFreeRoamMapRefreshButton.value;
  }
  if (mapSavedThisSession.value && plainFreeRoamSavedMapPreviewRefreshFailed.value) {
    return enabledButton(plainFreeRoamMapRefreshButton.value) ?? plainFreeRoamMapRefreshButton.value;
  }
  if (mapRuntimeStarted.value && !keyboardControlArmed.value) {
    return enabledButton(plainFreeRoamKeyboardButton.value) ?? plainKeyboardNextTarget();
  }
  if (keyboardHeldDirection.value) {
    return enabledButton(plainFreeRoamStopButton.value) ?? keyboardControlPanel.value;
  }
  if (mapRuntimeStarted.value && !mapSavedThisSession.value) {
    if (keyboardStopSettledAfterPulse.value) {
      return plainFreeRoamMapPreviewFreshForSession.value
        ? enabledButton(plainFreeRoamSaveButton.value) ?? plainFreeRoamSaveButton.value
        : enabledButton(plainFreeRoamMapRefreshButton.value) ?? plainFreeRoamMapRefreshButton.value;
    }
    return keyboardControlPanel.value;
  }
  return enabledButton(plainFreeRoamSaveButton.value)
    ?? enabledButton(plainFreeRoamStartButton.value)
    ?? plainFreeRoamConfirmCheckbox.value;
}

function plainFreeRoamAutonomyNextTarget(): HTMLElement | null {
  // 自动扫图补证优先处理真车门禁证据；缺雷达新鲜证明时不能继续引导 operator 去手控。
  if (!plainManualSafetyConfirmed.value) {
    return plainFreeRoamConfirmCheckbox.value;
  }
  if (!mapRuntimeStarted.value && !mapSavedThisSession.value) {
    return enabledButton(plainFreeRoamStartButton.value) ?? plainFreeRoamStartButton.value;
  }
  if (freeRoamMapWysiwygPending.value || !plainFreeRoamMapPreviewFreshForSession.value) {
    return enabledButton(plainFreeRoamMapRefreshButton.value) ?? plainFreeRoamMapRefreshButton.value;
  }
  if (radarSummary.value.state !== "雷达已运行") {
    return plainRadarNextTarget() ?? plainFreeRoamStartButton.value;
  }
  if (!canSendStop.value) {
    return enabledButton(keyboardControlRecheckButton.value) ?? keyboardControlPanel.value;
  }
  return plainFreeRoamNextTarget();
}

async function focusPlainFreeRoamNextTarget(): Promise<void> {
  // 这里刻意只做 scroll/focus，所有真实动作仍由用户按对应按钮触发。
  await nextTick();
  const target = plainFreeRoamNextTarget();
  if (!target) {
    return;
  }
  target.scrollIntoView?.({ block: "center", behavior: "smooth" });
  target.focus({ preventScroll: true });
}

async function focusPlainFreeRoamAutonomyNextTarget(): Promise<void> {
  // 自动扫图按钮在未满足时也只移动焦点，避免一次点击混入运动、Nav2 或送达动作。
  await nextTick();
  const target = plainFreeRoamAutonomyNextTarget();
  if (!target) {
    return;
  }
  target.scrollIntoView?.({ block: "center", behavior: "smooth" });
  target.focus({ preventScroll: true });
}

async function advancePlainFreeRoamManualGuide(): Promise<void> {
  // 自动扫图未 ready 时，这个按钮只推进人工扫图的非运动步骤；真正移动仍必须按住方向键。
  if (!plainManualSafetyConfirmed.value) {
    await focusPlainFreeRoamNextTarget();
    return;
  }
  if (!mapRuntimeStarted.value && !mapSavedThisSession.value && canStartPlainFreeRoamMapping.value) {
    await startMapRuntime();
    await focusPlainFreeRoamNextTarget();
    return;
  }
  if (mapRuntimeStarted.value && !keyboardControlArmed.value && canArmPlainFreeRoamKeyboard.value) {
    activateKeyboardControl();
    await focusPlainFreeRoamNextTarget();
    return;
  }
  await focusPlainFreeRoamNextTarget();
}

async function advancePlainFreeRoamAutonomyGuide(): Promise<void> {
  // 上车端自动扫图 start-ready 后，先补非运动证据；最终发车仍只走固定 start 代理。
  if (!plainManualSafetyConfirmed.value) {
    await focusPlainFreeRoamAutonomyNextTarget();
    return;
  }
  if (!mapRuntimeStarted.value && !mapSavedThisSession.value && canStartPlainFreeRoamMapping.value) {
    await startMapRuntime();
    await refreshMapPreview({ countForFreeRoamSession: true });
    if (canStartFreeRoamAutonomy.value) {
      await startFreeRoamAutonomy();
      return;
    }
    await focusPlainFreeRoamAutonomyNextTarget();
    return;
  }
  if (mapRuntimeStarted.value && !plainFreeRoamMapPreviewFreshForSession.value && canRefreshPlainFreeRoamMapPreview.value) {
    await refreshMapPreview({ countForFreeRoamSession: true });
    if (canStartFreeRoamAutonomy.value) {
      await startFreeRoamAutonomy();
      return;
    }
  }
  await focusPlainFreeRoamAutonomyNextTarget();
}

function markDeliveryBasicSafetyConfirmed(): void {
  // 只减少现场重复勾选；到达、停稳和送达成功仍必须由 operator 分开确认。
  deliveryOperatorConfirmations.value.operator_present = true;
  deliveryOperatorConfirmations.value.physical_clearance_confirmed = true;
  deliveryOperatorConfirmations.value.emergency_stop_ready = true;
}

async function markPlainWheelZeroBlockerChecked(): Promise<void> {
  // 本地勾选只改变现场操作提示，不调用任何机器人接口。
  plainWheelZeroBlockerChecked.value = true;
  await nextTick();
  const target = enabledButton(plainWheelTrialButton.value) ?? plainWheelRecordPanel.value;
  target.focus({ preventScroll: true });
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

async function markDeliverySuccessConfirmed(): Promise<void> {
  // 最后一项必须由 operator 显式点击；这里只勾本地确认，不触发提交。
  deliveryOperatorConfirmations.value.delivery_success = true;
  await focusPlainDeliveryConfirmSubmitButton();
}

async function markAllDeliveryConfirmations(): Promise<void> {
  // 这个按钮只把现场已确认事项合并勾选；最终提交仍必须单独点击“确认送达”。
  markDeliveryBasicSafetyConfirmed();
  markDeliveryArrivedAndStopped();
  markDeliveryRefsVerified();
  deliveryOperatorConfirmations.value.delivery_success = true;
  await focusPlainDeliveryConfirmSubmitButton();
}

async function checkDeliveryGap(): Promise<void> {
  // 复算缺口固定 confirm=false；它刷新 gate artifact，但不能确认送达。
  if (!canCheckDeliveryGap.value) {
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
  if (!canFillDeliveryVideoRefFromCameraProbe.value) {
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
  if (!canPrefillDeliveryMaterialRefs.value) {
    return;
  }
  const routeRefNeedsRefresh = !deliveryOperatorRouteMapRef.value.trim()
    || (deliveryNav2GoalReady.value && !deliveryRouteMapMatchesFreshNav2.value);
  if (routeRefNeedsRefresh && !freshNav2RouteMapRef.value) {
    await loadNavGoalExecutionLatest();
  }
  if (routeRefNeedsRefresh) {
    fillDeliveryRouteRefFromLatestNav2();
  }
  if (!deliveryOperatorVideoRef.value.trim()) {
    await fillDeliveryVideoRefFromCameraProbe();
  }
  await loadDeliveryLatest();
  if (deliveryOperatorVideoRef.value.trim() && deliveryOperatorRouteMapRef.value.trim() && !deliveryDraftMaterialPresent()) {
    await focusPlainDeliveryDraftSaveButton();
  }
}

async function submitDeliveryDraftMaterial(): Promise<void> {
  // 草稿只保存 ref 材料；成功后自动复算 confirm=false 缺口，减少现场下一步点击。
  if (
    !robotApiBaseUrl.value.trim()
    || operatorReportPending.value
    || plainDeliveryMapWysiwygPending.value
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
    || plainDeliveryMapWysiwygPending.value
    || !deliveryNav2GoalReady.value
    || !deliveryRouteMapMatchesFreshNav2.value
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
    if (deliveryCompletionResult.value?.delivery_success === true) {
      await focusKeyboardPanelAfterDeliverySuccess();
    }
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
  mapLifecyclePendingAction.value = action;
  try {
    mapLifecycleResult.value = await request();
  } catch (err) {
    mapLifecycleResult.value = makeMapLifecycleFallback(action, err instanceof Error ? err.message : `${action}_request_failed`);
  } finally {
    mapLifecyclePending.value = false;
    mapLifecyclePendingAction.value = null;
    await refreshConsole();
  }
  await refreshMapPreview({ savedMapRefresh: action === "save" });
}

async function loadMapList(): Promise<void> {
  // 列表读取是 GET-only 固定代理，不触发建图、不启动底盘、不发送 /cmd_vel。
  await runMapLifecycleAction("list", () => getRobotControlMapList(robotApiBaseUrl.value));
}

async function startMapRuntime(): Promise<void> {
  // 普通按钮只走固定 /api/map/start，不接受浏览器传运动、串口或 ROS 参数。
  if (mapWysiwygRefreshPending.value) {
    return;
  }
  plainFreeRoamMapPreviewFreshForSession.value = false;
  plainFreeRoamMapPreviewRefreshFailedForSession.value = false;
  plainFreeRoamLiveMapPreviewRefreshedForHold.value = false;
  plainFreeRoamSavedMapPreviewFreshForSession.value = false;
  plainFreeRoamSavedMapPreviewRefreshFailed.value = false;
  await runMapLifecycleAction("start", () => postRobotControlMapStart(robotApiBaseUrl.value, mapLifecycleRequestBody()));
  if (mapRuntimeStarted.value && canArmPlainFreeRoamKeyboard.value) {
    // 启动建图后只打开键盘窗口，不发送方向脉冲；真正移动仍要 operator 按住方向键。
    activateKeyboardControl();
  }
}

async function saveMap(options: { refreshRouteAfterSave?: boolean } = {}): Promise<void> {
  // 保存只调用固定 /api/map/save；普通入口不暴露 map_name/artifact_path 输入。
  if (mapWysiwygRefreshPending.value) {
    return;
  }
  await runMapLifecycleAction("save", () => postRobotControlMapSave(robotApiBaseUrl.value, mapLifecycleRequestBody()));
  if (options.refreshRouteAfterSave === true && mapSavedThisSession.value && plainFreeRoamSavedMapPreviewFreshForSession.value && canRefreshNav2Proof.value) {
    await refreshNav2Proof();
  }
}

function makeFreeRoamAutonomyFallback(action: "start" | "stop", reason: string): RobotControlFreeRoamAutonomyResponse {
  // 自动扫图代理失败时必须保持“未启动/未停止已证明”的可读状态。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_free_roam_autonomy_proxy.v1",
    source: "software_proof",
    proof_status: "not_proven",
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    action,
    proxy_status: "autonomy_failed",
    source_base_url: robotApiBaseUrl.value,
    normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
    remote_endpoint: action === "start" ? "/api/free-roam/autonomy/start" : "/api/free-roam/autonomy/stop",
    remote_method: "POST",
    remote_http_status: null,
    status: "blocked",
    request_body: action === "start" ? { confirm_operator_safety: true, confirm_mapping_active: true } : {},
    command_result: { mode: "not_sent", executed: false, ok: false },
    latest_decision_state: "not_loaded",
    sets_state_machine_parameters: false,
    direct_cmd_vel_publish: false,
    does_not_set_motion_unlock: true,
    blocked_parameters_not_touched: ["enable_cmd_vel_publish", "motion_hil_unlocked", "cmd_vel_topic"],
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

async function refreshFreeRoamAutonomyLatest(): Promise<void> {
  // 只读刷新自动扫图 runtime；不启动/停止状态机，也不发送底盘命令。
  if (!robotApiBaseUrl.value.trim() || freeRoamAutonomyLatestPending.value) {
    return;
  }
  freeRoamAutonomyLatestPending.value = true;
  try {
    freeRoamAutonomyLatestResult.value = await getRobotControlFreeRoamAutonomyLatest(robotApiBaseUrl.value);
  } catch (err) {
    const reason = err instanceof Error ? err.message : "free_roam_autonomy_latest_failed";
    freeRoamAutonomyLatestResult.value = {
      schema: "trashbot.pc_tools_workstation.robot_control_free_roam_autonomy_latest_proxy.v1",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: robotApiBaseUrl.value,
      normalized_base_url: robotApiBaseUrl.value.trim() || "not_loaded",
      workstation_endpoint: "/api/robot-control/free-roam/autonomy/latest",
      remote_endpoint: "/api/free-roam/autonomy/latest",
      remote_method: "GET",
      remote_http_status: null,
      proxy_status: "latest_failed",
      status: "blocked",
      latest_key_values: {},
      failure_reason: reason,
      blocked_reasons: [reason],
      hard_dangerous_true_fields: [],
    };
  } finally {
    freeRoamAutonomyLatestPending.value = false;
  }
  await refreshConsole();
}

async function startFreeRoamAutonomy(): Promise<void> {
  // 真正自动扫图 start 只走固定上车状态机代理；未 ready 时推进人工扫图的非运动向导。
  if (!canStartFreeRoamAutonomy.value) {
    if (
      robotSummary.value?.safe_command_boundary.free_roam_autonomy_start_ready === true
      || robotSummary.value?.safe_command_boundary.free_roam_autonomy === "ready"
    ) {
      await advancePlainFreeRoamAutonomyGuide();
      return;
    }
    await advancePlainFreeRoamManualGuide();
    return;
  }
  let stopQueuedAfterStart = false;
  freeRoamAutonomyPending.value = true;
  freeRoamAutonomyPendingAction.value = "start";
  try {
    freeRoamAutonomyResult.value = await postRobotControlFreeRoamAutonomyStart(robotApiBaseUrl.value, {
      confirm_operator_safety: true,
      confirm_mapping_active: true,
    });
  } catch (err) {
    freeRoamAutonomyResult.value = makeFreeRoamAutonomyFallback("start", err instanceof Error ? err.message : "free_roam_autonomy_start_failed");
  } finally {
    freeRoamAutonomyPending.value = false;
    freeRoamAutonomyPendingAction.value = null;
    if (freeRoamAutonomyStopQueuedAfterStart.value) {
      freeRoamAutonomyStopQueuedAfterStart.value = false;
      stopQueuedAfterStart = true;
    }
  }
  if (stopQueuedAfterStart) {
    await stopFreeRoamAutonomy();
    return;
  }
  await refreshConsole();
  if (freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded" && freeRoamAutonomyResult.value.action === "start") {
    await refreshRadarProof({ focusAfterReady: false });
  }
  await refreshMapPreview({ countForFreeRoamSession: true });
}

async function stopFreeRoamAutonomy(): Promise<void> {
  // 自动 stop 请求只改变上车状态机 stop 参数；底盘 stop 按钮仍保留为独立兜底。
  if (!robotApiBaseUrl.value.trim() || freeRoamAutonomyPendingAction.value === "stop") {
    return;
  }
  if (freeRoamAutonomyPendingAction.value === "start") {
    freeRoamAutonomyStopQueuedAfterStart.value = true;
    return;
  }
  freeRoamAutonomyPending.value = true;
  freeRoamAutonomyPendingAction.value = "stop";
  try {
    freeRoamAutonomyResult.value = await postRobotControlFreeRoamAutonomyStop(robotApiBaseUrl.value);
  } catch (err) {
    freeRoamAutonomyResult.value = makeFreeRoamAutonomyFallback("stop", err instanceof Error ? err.message : "free_roam_autonomy_stop_failed");
  } finally {
    freeRoamAutonomyPending.value = false;
    freeRoamAutonomyPendingAction.value = null;
    if (freeRoamAutonomyResult.value?.proxy_status === "autonomy_forwarded" && freeRoamAutonomyResult.value.action === "stop") {
      // 自动扫图期间地图可能已经变化；stop 后必须重新读画面，不能沿用启动前的 fresh 标记去保存。
      plainFreeRoamMapPreviewFreshForSession.value = false;
      plainFreeRoamLiveMapPreviewRefreshedForHold.value = false;
    }
    await refreshConsole();
  }
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

async function submitPlainVisualMaterial(options: { videoRef?: string; cameraArtifactRef?: string; visibleContentProven?: boolean } = {}): Promise<void> {
  // 记录画面只更新 operator report；没有填写视频索引时不提交，避免制造空 ref。
  const videoRef = (options.videoRef ?? plainExternalVideoRef.value).trim();
  if (!robotApiBaseUrl.value.trim() || plainVisualMaterialPending.value || operatorReportPending.value || !videoRef) {
    return;
  }
  const requestBody = plainVisualMaterialRequestBody({ ...options, videoRef });
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

async function submitPlainVisualMaterialFromCameraProbe(): Promise<void> {
  // 当前画面记录只走固定 camera probe，再提交 operator report；不会打开运动、Nav2 或 delivery gate。
  if (!robotApiBaseUrl.value.trim() || previewBusy.value || cameraFirstFrameProbePending.value || plainVisualMaterialPending.value || operatorReportPending.value) {
    return;
  }
  // 每次点击都重新读取一帧，避免把旧 probe 样张误当成 operator 眼前的当前画面。
  await runCameraFirstFrameProbe();
  const sampleRef = latestCameraProbeSampleRef();
  if (!sampleRef) {
    return;
  }
  plainExternalVideoRef.value = sampleRef;
  await submitPlainVisualMaterial({ videoRef: sampleRef, cameraArtifactRef: sampleRef, visibleContentProven: true });
}

async function restorePlainFirstJogMaterial(): Promise<void> {
  // 送达草稿会覆盖 latest report；恢复按钮只补 first-jog 前置材料，不发送任何运动命令。
  if (!canRestorePlainFirstJogMaterial.value) {
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
    if (plainFirstJogMaterialRestored.value) {
      await nextTick();
      focusAfterPlainFirstJogMaterialRestore();
    }
  }
}

function focusAfterPlainFirstJogMaterialRestore(): void {
  // 恢复确认只服务 wheel raw L/R 流程；成功后回到轮速下一手动作，不被雷达卡点抢焦点。
  const target = plainWheelGoalTarget();
  target?.scrollIntoView?.({ block: "center", behavior: "smooth" });
  target?.focus({ preventScroll: true });
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
    await runBaseFeedbackSamples({ refreshAfter: false, allowDuringMapRefresh: true });
    await refreshConsole();
    if (plainFirstJogWheelEvidenceReady.value) {
      await nextTick();
      plainWheelSaveButton.value?.scrollIntoView?.({ block: "center", behavior: "smooth" });
      plainWheelSaveButton.value?.focus({ preventScroll: true });
    }
  }
}

async function savePlainWheelEvidence(): Promise<void> {
  // 保存轮速材料只写 operator report；不补 LiDAR/route/delivery，也不再次发送运动命令。
  if (!canSavePlainWheelEvidence.value) {
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
    if (plainWheelEvidenceSaveResult.value?.proxy_status === "report_forwarded" && plainWheelEvidenceSaveResult.value.status !== "blocked") {
      await nextTick();
      plainTripRunPanel.value?.scrollIntoView?.({ block: "center", behavior: "smooth" });
      plainTripRunPanel.value?.focus({ preventScroll: true });
    }
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

async function runBaseFeedbackSamples(options: { refreshAfter?: boolean; allowDuringMapRefresh?: boolean } = {}): Promise<void> {
  // 反馈样本采集只走固定 T=130 只读代理，不发送方向、速度或 stop/manual 命令。
  if (!robotApiBaseUrl.value.trim()
    || baseFeedbackSamplesPending.value
    || (!options.allowDuringMapRefresh && mapWysiwygRefreshPending.value)) {
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
    await focusPlainWheelZeroCheckAfterReadback();
  }
}

async function focusPlainWheelZeroCheckAfterReadback(): Promise<void> {
  // 只读刷新读到 L/R=0/0 后带到本地排查确认；不发送运动、不写 operator report。
  await nextTick();
  if (!plainWheelZeroBlockerActive.value || plainWheelZeroBlockerChecked.value) {
    return;
  }
  const target = plainWheelZeroCheckButton.value;
  if (!target) {
    return;
  }
  target.focus({ preventScroll: true });
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
      confirm_hil_checklist: plainManualSafetyConfirmed.value,
      non_stop_requires_confirm_hil_checklist: true,
      hil_checklist_gate_status: plainManualSafetyConfirmed.value ? "manual_allowed" : "manual_blocked_missing_checklist",
      checklist_missing: plainManualSafetyConfirmed.value ? [] : ["安全确认"],
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
    const result = await postRobotControlBaseManual(robotApiBaseUrl.value, requestBodyForKeyboardDirection(direction));
    manualCommandResult.value = result;
    if (result.remote_motion_key_values) {
      keyboardLastWheelFeedbackValues.value = result.remote_motion_key_values;
    }
    const pulseForwarded = result.proxy_status === "command_forwarded"
      && typeof result.remote_http_status === "number"
      && result.remote_http_status >= 200
      && result.remote_http_status < 300;
    if (pulseForwarded) {
      keyboardHoldPulseCount.value += 1;
      keyboardVerifiedPulseCount.value = Math.max(keyboardVerifiedPulseCount.value, keyboardHoldPulseCount.value);
      if (
        mapRuntimeStarted.value
        && !plainFreeRoamLiveMapPreviewRefreshedForHold.value
        && keyboardHoldPulseCount.value >= KEYBOARD_VERIFIED_MIN_FORWARDED_PULSES
      ) {
        void refreshMapPreview({ freeRoamLiveRefresh: true });
      }
    }
    if (keyboardHeldDirection.value === direction && pulseForwarded) {
      keyboardControlStatus.value = "holding_keyboard_jog";
    } else if (keyboardHeldDirection.value === direction) {
      clearKeyboardJogTimer();
      keyboardHeldDirection.value = null;
      keyboardHoldPulseCount.value = 0;
      keyboardControlStatus.value = `blocked_keyboard_pulse_failed:${result.failure_reason || result.proxy_status}`;
    }
  } catch (err) {
    clearKeyboardJogTimer();
    if (keyboardHeldDirection.value === direction) {
      keyboardHeldDirection.value = null;
    }
    keyboardHoldPulseCount.value = 0;
    keyboardControlStatus.value = `blocked_keyboard_pulse_failed:${err instanceof Error ? err.message : "keyboard_manual_request_failed"}`;
  } finally {
    manualCommandPending.value = false;
    keyboardJogInFlight = false;
    if (keyboardStopAfterPulseReason && !keyboardHeldDirection.value) {
      const reason = keyboardStopAfterPulseReason;
      keyboardStopAfterPulseReason = null;
      await sendKeyboardReleaseStop(reason);
    }
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
  // 启用后就是全页面键盘窗口；真正的安全边界由 armed、editable 拦截和后端 manual gate 负责。
  void target;
  return true;
}

function keyboardControlWindow(): KeyboardControlWindow {
  // 全局键盘事件可能被测试或热更新留下多个组件实例监听；owner 令牌保证只有当前启用的实例响应。
  return window as KeyboardControlWindow;
}

function setKeyboardControlOwner(): void {
  // 点击启用键盘才拿到全局按键所有权；新挂载实例会先清空旧 owner。
  keyboardControlWindow()[KEYBOARD_CONTROL_OWNER_KEY] = keyboardControlOwnerId;
}

function clearKeyboardControlOwner(): void {
  // 只清理自己的 owner，避免误关掉另一个刚启用的控制台实例。
  if (keyboardControlWindow()[KEYBOARD_CONTROL_OWNER_KEY] === keyboardControlOwnerId) {
    keyboardControlWindow()[KEYBOARD_CONTROL_OWNER_KEY] = "";
  }
}

function resetKeyboardControlOwnerOnMount(): void {
  // 新控制台挂载时默认没有任何实例持有全局按键，必须重新点“启用键盘”。
  keyboardControlWindow()[KEYBOARD_CONTROL_OWNER_KEY] = "";
}

function ownsKeyboardControl(): boolean {
  // armed 只是本实例状态；owner 才能证明当前全局按键应由这个实例处理。
  return keyboardControlWindow()[KEYBOARD_CONTROL_OWNER_KEY] === keyboardControlOwnerId;
}

function activateKeyboardControl(): void {
  // 现场 operator 需要先显式启用键盘；启用后全局按键才进入同一个 manual gate。
  setKeyboardControlOwner();
  keyboardControlArmed.value = true;
  keyboardControlStatus.value = canSendManualMotion.value ? "armed_waiting_for_key" : `blocked_keyboard_manual_gate:${manualBlockedReason.value}`;
  keyboardControlPanel.value?.focus();
}

function disarmKeyboardControl(reason: string): void {
  // 面板失焦或页面失焦时退出 armed 状态；如果正在运动，先通过统一 stop 路径收口。
  clearKeyboardControlOwner();
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
  keyboardHoldPulseCount.value = 0;
  keyboardLastStopReason.value = reason;
  keyboardControlStatus.value = `released:${reason}`;
  if (shouldSendStop && canSendStop.value) {
    void sendKeyboardReleaseStop(reason);
  } else if (shouldSendStop && manualCommandPending.value) {
    keyboardStopAfterPulseReason = reason;
  } else if (shouldSendStop) {
    keyboardControlStatus.value = "blocked_keyboard_stop_failed:stop_unavailable";
  }
}

async function sendKeyboardReleaseStop(reason: string): Promise<void> {
  // 键盘验收必须等 release stop 真正转发成功；失败或不可发都不能算已验证。
  if (!canSendStop.value) {
    keyboardControlStatus.value = "blocked_keyboard_stop_failed:stop_unavailable";
    return;
  }
  await sendStop();
  const result = manualCommandResult.value;
  const stopForwarded = result?.command_kind === "stop"
    && result.proxy_status === "command_forwarded"
    && typeof result.remote_http_status === "number"
    && result.remote_http_status >= 200
    && result.remote_http_status < 300;
  keyboardControlStatus.value = stopForwarded ? `stop_sent:${reason}` : `blocked_keyboard_stop_failed:${result?.failure_reason || result?.proxy_status || "stop_not_forwarded"}`;
  if (!stopForwarded) {
    clearKeyboardControlOwner();
    keyboardControlArmed.value = false;
    keyboardVerifiedPulseCount.value = 0;
    keyboardHoldPulseCount.value = 0;
  }
  if (stopForwarded && mapRuntimeStarted.value && robotApiBaseUrl.value.trim()) {
    void refreshMapPreview({ countForFreeRoamSession: true });
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
  if (keyboardStopFailedAfterPulse.value) {
    keyboardControlStatus.value = "blocked_keyboard_stop_failed:recheck_before_next_move";
    return;
  }
  if (keyboardMapWysiwygBlocked.value) {
    keyboardControlStatus.value = "blocked_map_preview_pending";
    return;
  }
  clearKeyboardJogTimer();
  keyboardHeldDirection.value = direction;
  keyboardHoldPulseCount.value = 0;
  keyboardLastWheelFeedbackValues.value = null;
  plainFreeRoamLiveMapPreviewRefreshedForHold.value = false;
  keyboardLastDirection.value = direction;
  keyboardControlStatus.value = "holding_keyboard_jog";
  void sendKeyboardManualPulse(direction);
  keyboardJogTimer = window.setInterval(() => {
    void sendKeyboardManualPulse(direction);
  }, keyboardJogIntervalMs.value);
}

function handleKeyboardDirectionPointerDown(direction: ManualDirection, event: PointerEvent): void {
  // 屏幕方向键只是一种更稳的按住入口，仍复用键盘 armed 状态和 manual gate。
  event.preventDefault();
  keyboardControlPanel.value?.focus();
  if (keyboardHeldDirection.value && keyboardHeldDirection.value !== direction) {
    stopKeyboardControl("screen_direction_changed");
  }
  if (keyboardHeldDirection.value === direction) {
    return;
  }
  startKeyboardControl(direction);
}

function handleKeyboardDirectionPointerEnd(direction: ManualDirection, reason: string): void {
  // 松开、移出或取消都走统一 stop 路径，防止屏幕按钮残留连续点动。
  if (keyboardHeldDirection.value === direction) {
    stopKeyboardControl(reason);
  }
}

function handleGlobalKeyDown(event: KeyboardEvent): void {
  // 长按产生的 repeat 事件由 timer 接管，避免浏览器 repeat 频率影响底盘命令节奏。
  const direction = keyboardDirectionFromKey(event.key);
  if (!direction || eventTargetIsEditable(event.target) || !keyboardControlArmed.value || !ownsKeyboardControl() || !eventTargetIsKeyboardControlScope(event.target)) {
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
  if (!direction || !keyboardControlArmed.value || !ownsKeyboardControl() || !eventTargetIsKeyboardControlScope(event.target) || keyboardHeldDirection.value !== direction) {
    return;
  }
  event.preventDefault();
  stopKeyboardControl("key_released");
}

function handleKeyboardControlFocusOut(event: FocusEvent): void {
  // 启用后允许 operator 看地图或点击空白处继续按键；只有进入可编辑控件才退出手控窗口。
  const nextTarget = event.relatedTarget;
  if (!(nextTarget instanceof HTMLElement) || !eventTargetIsEditable(nextTarget)) {
    return;
  }
  disarmKeyboardControl("editable_focus");
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

async function sendStop(): Promise<RobotControlBaseCommandProxyResponse | null> {
  // stop 始终保留，是为了在 checklist 未完成时也有 fail-safe 退路。
  if (!robotApiBaseUrl.value.trim() || manualCommandPending.value) {
    return null;
  }
  manualCommandPending.value = true;
  let stopResult: RobotControlBaseCommandProxyResponse | null = null;
  try {
    stopResult = await postRobotControlBaseStop(robotApiBaseUrl.value);
    manualCommandResult.value = stopResult;
    recordPlainTripStopResult(stopResult);
  } catch (err) {
    stopResult = {
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
    manualCommandResult.value = stopResult;
    recordPlainTripStopResult(stopResult);
  } finally {
    manualCommandPending.value = false;
    await refreshConsole();
  }
  return stopResult;
}

async function startPreview(): Promise<void> {
  // Start Preview 只在显式用户点击后创建会话，页面初始不自动占用 camera peer。
  if (!robotApiBaseUrl.value.trim() || previewStartPending.value) {
    return;
  }
  previewStartPending.value = true;
  failureReason.value = "";
  rawFailureReason.value = "";
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
    rawFailureReason.value = nextFailureReason;
    failureReason.value = cameraOfferPlainFailureHint(nextFailureReason) || nextFailureReason;
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
  rawFailureReason.value = "";
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
  mapPreviewResult.value = null;
  plainTripPostExecutionMapPreviewRefreshFailed.value = false;
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
  resetKeyboardControlOwnerOnMount();
  window.addEventListener("keydown", handleGlobalKeyDown);
  window.addEventListener("keyup", handleGlobalKeyUp);
  window.addEventListener("blur", handleWindowBlur);
  document.addEventListener("visibilitychange", handlePageVisibilityChange);
  void refreshConsole().then(() => {
    void refreshMapPreview();
    void preloadGoalClosureReadbacks();
  });
});

onBeforeUnmount(() => {
  // 卸载时先退出键盘循环，再释放视频资源；远端 cleanup 尽量执行但不能阻塞组件销毁。
  clearKeyboardControlOwner();
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
      <div class="robot-quick-connect">
        <div class="plain-default-robot">
          <span class="plain-default-robot-title">默认小车</span>
          <span class="plain-default-robot-address" data-testid="robot-api-default-address">{{ robotApiBaseUrlPlainLabel }}</span>
          <span class="muted" data-testid="robot-api-default-summary">{{ robotApiBaseUrlUsesDefault ? "已使用默认地址" : "已改为高级地址" }}</span>
        </div>
        <button class="secondary compact-stop" type="button" :disabled="loading || robotApiBaseUrlUsesDefault" data-testid="robot-api-default" @click="resetRobotApiBaseUrlToDefault">恢复默认</button>
        <button class="secondary" type="button" :disabled="loading" data-testid="robot-api-refresh" @click="refreshConsole">连接/刷新</button>
        <span class="status-chip" :data-state="robotConnectionSummary.state">{{ robotConnectionSummary.state }}</span>
      </div>

      <div v-if="error" class="notice" role="alert">
        {{ error }}；安全锁定保持不变。
      </div>

      <div class="robot-console-grid" data-smoke-scope="simple-robot-control-first-screen">
        <article class="snapshot-panel plain-connection-panel" data-testid="plain-connection-panel" :data-state="robotConnectionSummary.state">
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

        <article class="snapshot-panel plain-camera-panel" data-testid="plain-camera-panel" :data-state="cameraSummary.state" :data-frame-state="plainCameraFrameEvidenceState">
          <h3>实时画面</h3>
          <div class="panel-action-row">
            <button type="button" :disabled="!canStartPreview" @click="startPreview">打开画面</button>
            <button type="button" class="secondary compact-stop" :disabled="!canRunPlainCameraProbe" data-testid="plain-camera-probe" @click="runCameraFirstFrameProbe">
              {{ plainCameraProbeButtonLabel }}
            </button>
            <button type="button" :disabled="!canStopPreview" @click="stopPreview">关闭画面</button>
            <span class="status-chip" :data-state="cameraSummary.state">{{ cameraSummary.state }}</span>
          </div>
          <div class="camera-preview-frame" data-testid="robot-camera-preview-frame" :data-state="cameraSummary.state" :data-frame-state="plainCameraFrameEvidenceState">
            <video
              ref="previewVideo"
              data-testid="robot-camera-preview-video"
              :data-frame-state="plainCameraFrameEvidenceState"
              autoplay
              muted
              playsinline
              @loadedmetadata="syncPreviewVideoElementDiagnostics"
              @loadeddata="handlePreviewVideoReady"
              @playing="handlePreviewVideoReady"
              @resize="syncPreviewVideoElementDiagnostics"
            />
            <div v-if="cameraSummary.state !== '画面可见'" class="camera-preview-overlay" data-testid="robot-camera-preview-overlay" :data-state="cameraSummary.state">
              <strong>{{ cameraSummary.state }}</strong>
              <span>{{ cameraSummary.hint }}</span>
            </div>
          </div>
          <p class="panel-note">{{ cameraSummary.hint }}</p>
          <p class="panel-note" data-testid="robot-camera-wysiwyg-status">{{ plainCameraWysiwygStatus }}</p>
          <p v-if="plainCameraProbeSummary" class="panel-note" data-testid="plain-camera-probe-summary">{{ plainCameraProbeSummary }}</p>
        </article>

        <article class="snapshot-panel plain-radar-panel" data-testid="plain-radar-panel" :data-state="radarSummary.state">
          <h3>雷达</h3>
          <div class="panel-action-row">
            <button ref="plainRadarRefreshButton" type="button" :disabled="!canRefreshRadarProof" data-testid="plain-radar-refresh" @click="refreshRadarProof">
              {{ radarProofRefreshButtonLabel }}
            </button>
            <button v-if="showPlainRadarStart" ref="plainRadarStartButton" type="button" class="secondary compact-stop" :disabled="!canStartRadarLifecycle || plainRadarStartUnavailable" data-testid="plain-radar-start" @click="startPlainRadarLifecycle">
              {{ plainRadarStartButtonLabel }}
            </button>
            <span class="status-chip" :data-state="radarSummary.state">{{ radarSummary.state }}</span>
          </div>
          <p class="panel-note">{{ radarSummary.hint }}</p>
        </article>

        <article class="snapshot-panel plain-map-panel" data-testid="plain-map-panel" :data-state="plainMapVisualSummary.state">
          <h3>地图</h3>
          <div class="plain-map-viewport" data-testid="plain-map-wysiwyg-view" :data-state="plainMapVisualSummary.state">
            <div class="plain-map-layer" :class="{ 'has-real-map': plainMapVisualSummary.imageDataUrl }">
              <div class="plain-map-overlay-frame" :style="plainMapVisualSummary.frameStyle">
                <img v-if="plainMapVisualSummary.imageDataUrl" class="plain-map-image" data-testid="plain-map-preview-image" :src="plainMapVisualSummary.imageDataUrl" :alt="plainMapVisualSummary.imageAlt">
                <template v-else>
                  <span class="plain-map-grid-line horizontal" />
                  <span class="plain-map-grid-line vertical" />
                  <span class="plain-map-wall top" />
                  <span class="plain-map-wall bottom" />
                  <span class="plain-map-wall left" />
                  <span class="plain-map-wall right" />
                </template>
                <svg v-if="plainMapVisualSummary.showRoutePath" class="plain-map-route-path" viewBox="0 0 100 100" preserveAspectRatio="none" data-testid="plain-map-route-path" :data-state="plainMapVisualSummary.routePathState" :aria-label="plainMapVisualSummary.routePathAria">
                  <polyline :points="plainMapVisualSummary.routePathPoints" />
                </svg>
                <svg v-if="plainMapVisualSummary.showFreeRoamSweepPlan" class="plain-map-free-roam-sweep-plan" viewBox="0 0 100 100" preserveAspectRatio="none" data-testid="plain-map-free-roam-sweep-plan" :data-state="plainMapVisualSummary.freeRoamSweepPlanState" :aria-label="plainMapVisualSummary.freeRoamSweepPlanAria">
                  <polyline :points="plainMapVisualSummary.freeRoamSweepPlanPoints" />
                </svg>
                <svg v-if="plainMapVisualSummary.showFreeRoamTrail" class="plain-map-free-roam-trail" viewBox="0 0 100 100" preserveAspectRatio="none" data-testid="plain-map-free-roam-trail" :data-state="plainMapVisualSummary.freeRoamTrailState" :aria-label="plainMapVisualSummary.freeRoamTrailAria">
                  <polyline :points="plainMapVisualSummary.freeRoamTrailPoints" />
                </svg>
                <span
                  v-for="marker in plainMapVisualSummary.routeEndpointMarkers"
                  :key="marker.id"
                  class="plain-map-route-endpoint-marker"
                  :data-testid="`plain-map-route-${marker.id}-marker`"
                  :data-state="marker.state"
                  :style="marker.style"
                  :aria-label="marker.aria"
                >{{ marker.label }}</span>
                <span v-if="plainMapVisualSummary.showRouteGoal" class="plain-map-route-goal-marker" data-testid="plain-map-route-goal-marker" :data-state="plainMapVisualSummary.routeGoalState" :style="plainMapVisualSummary.routeGoalStyle" :aria-label="plainMapVisualSummary.routeGoalAria">{{ plainMapVisualSummary.routeGoalLabel }}</span>
                <span v-if="plainMapVisualSummary.showFreeRoamSweepStart" class="plain-map-free-roam-start-marker" data-testid="plain-map-free-roam-start-marker" :style="plainMapVisualSummary.freeRoamSweepStartStyle" aria-label="扫图草图从机器人当前位置接入">扫图起点</span>
                <span v-if="plainMapVisualSummary.showFreeRoamRuntimeMarker" class="plain-map-free-roam-runtime-marker" data-testid="plain-map-free-roam-runtime-marker" :data-state="plainMapVisualSummary.freeRoamRuntimeMarkerState" :style="plainMapVisualSummary.freeRoamRuntimeMarkerStyle" :aria-label="plainMapVisualSummary.freeRoamRuntimeMarkerAria">{{ plainMapVisualSummary.freeRoamRuntimeMarkerLabel }}</span>
                <span v-if="plainMapVisualSummary.showFreeRoamActionMarker" class="plain-map-free-roam-action-marker" data-testid="plain-map-free-roam-action-marker" :data-state="plainMapVisualSummary.freeRoamActionMarkerState" :style="plainMapVisualSummary.freeRoamActionMarkerStyle" :aria-label="plainMapVisualSummary.freeRoamActionMarkerAria">{{ plainMapVisualSummary.freeRoamActionMarkerLabel }}</span>
                <span v-if="plainMapVisualSummary.showFreeRoamDirectionMarker" class="plain-map-free-roam-direction-marker" data-testid="plain-map-free-roam-direction-marker" :data-state="plainMapVisualSummary.freeRoamDirectionMarkerState" :data-wheel-state="plainMapVisualSummary.freeRoamDirectionMarkerWheelState" :style="plainMapVisualSummary.freeRoamDirectionMarkerStyle" :aria-label="plainMapVisualSummary.freeRoamDirectionMarkerAria">{{ plainMapVisualSummary.freeRoamDirectionMarkerLabel }}</span>
                <span v-if="plainMapVisualSummary.showRadarSweep" class="plain-map-radar-sweep" :class="`mode-${plainMapVisualSummary.radarOverlayMode}`" data-testid="plain-map-radar-sweep" :data-state="plainMapVisualSummary.radarLabel" :style="plainMapVisualSummary.radarOverlayStyle" :aria-label="plainMapVisualSummary.radarSweepAria" />
                <svg v-if="plainMapVisualSummary.showRadarScanPoints" class="plain-map-radar-scan-points" viewBox="0 0 100 100" preserveAspectRatio="none" data-testid="plain-map-radar-scan-points" :aria-label="plainMapVisualSummary.radarScanAria">
                  <circle v-for="point in plainMapVisualSummary.radarScanDots" :key="point.key" :cx="point.left" :cy="point.top" r="1.15" />
                </svg>
                <svg v-if="plainMapVisualSummary.showRadarLocalScan" class="plain-map-radar-local-scan" viewBox="0 0 100 100" preserveAspectRatio="none" data-testid="plain-map-radar-local-scan" :data-state="plainMapVisualSummary.radarLocalScanState" :aria-label="plainMapVisualSummary.radarLocalScanAria">
                  <line x1="50" y1="44" x2="50" y2="56" />
                  <line x1="44" y1="50" x2="56" y2="50" />
                  <circle v-for="point in plainMapVisualSummary.radarLocalScanDots" :key="point.key" :cx="point.left" :cy="point.top" r="1.6" />
                </svg>
                <span v-if="plainMapVisualSummary.showRadarPulse" class="plain-map-radar-pulse" data-testid="plain-map-radar-pulse" :style="plainMapVisualSummary.radarOverlayStyle" aria-hidden="true" />
                <span v-if="plainMapVisualSummary.showRobotPose" class="plain-map-robot-marker" data-testid="plain-map-robot-marker" :style="plainMapVisualSummary.robotPoseStyle" :aria-label="plainMapVisualSummary.robotPoseAria" />
                <span v-else class="plain-map-unknown-pose" data-testid="plain-map-pose-missing" :data-state="plainMapVisualSummary.poseMissingState" :aria-label="plainMapVisualSummary.poseMissingAria">{{ plainMapVisualSummary.poseLabel }}</span>
                <span class="plain-map-radar-marker" :class="`mode-${plainMapVisualSummary.radarOverlayMode}`" data-testid="plain-map-radar-marker" :data-state="plainMapVisualSummary.radarLabel" :style="plainMapVisualSummary.radarOverlayStyle" :aria-label="plainMapVisualSummary.radarOverlayAria">{{ plainMapVisualSummary.radarOverlayLabel }}</span>
              </div>
            </div>
            <div class="plain-map-caption">
              <span class="status-chip" :data-state="plainMapVisualSummary.state">{{ plainMapVisualSummary.state }}</span>
              <span class="muted">{{ plainMapVisualSummary.mapRefLabel }}</span>
              <span v-if="plainMapVisualSummary.routePathLabel" class="muted" data-testid="plain-map-route-label">{{ plainMapVisualSummary.routePathLabel }}</span>
              <span v-if="plainMapVisualSummary.freeRoamSweepPlanLabel" class="muted" data-testid="plain-map-free-roam-sweep-label">{{ plainMapVisualSummary.freeRoamSweepPlanLabel }}</span>
              <span class="muted" data-testid="plain-map-radar-scan-label">{{ plainMapVisualSummary.radarScanLabel }}</span>
              <span class="muted" data-testid="plain-map-radar-freshness-label">{{ plainMapVisualSummary.radarFreshnessLabel }}</span>
              <span class="muted" data-testid="plain-map-image-freshness-label">{{ plainMapVisualSummary.mapImageFreshnessLabel }}</span>
              <span class="muted" data-testid="plain-map-coordinate-truth-label">{{ plainMapVisualSummary.coordinateTruthLabel }}</span>
              <span v-if="plainMapVisualSummary.tripExecutionLabel" class="muted" data-testid="plain-map-trip-execution-label">{{ plainMapVisualSummary.tripExecutionLabel }}</span>
            </div>
          </div>
          <div class="panel-action-row wrap-actions">
            <button type="button" :disabled="!canRefreshMapProof" data-testid="plain-map-proof-refresh" @click="refreshMapProof">
              {{ mapProofRefreshButtonLabel }}
            </button>
            <button type="button" :disabled="!canRefreshMapPreview" data-testid="plain-map-preview-refresh" @click="refreshMapPreview({ radarStatusRefresh: true })">
              {{ mapPreviewRefreshButtonLabel }}
            </button>
            <button type="button" :disabled="loading || mapLifecyclePending || !robotApiBaseUrl.trim()" @click="loadMapList">
              地图列表
            </button>
            <button type="button" :disabled="!canStartMapLifecycle" @click="startMapRuntime">
              重新建图
            </button>
            <button type="button" :disabled="!canSaveMapLifecycle" @click="saveMap">
              保存地图
            </button>
            <span class="status-chip" :data-state="mapSummary.state">{{ mapSummary.state }}</span>
            <span class="status-chip" :data-state="mapLifecycleSummary.state">{{ mapLifecycleSummary.state }}</span>
          </div>
          <p class="panel-note">{{ mapSummary.hint }}</p>
          <p class="panel-note">{{ mapLifecycleSummary.hint }}</p>
        </article>

        <article class="snapshot-panel plain-free-roam-map" :data-state="plainFreeRoamMappingSummary.state" data-testid="plain-free-roam-mapping">
          <h3>扫地式建图</h3>
          <div class="simple-status-row">
            <span class="status-chip" :data-state="plainFreeRoamMappingSummary.state">{{ plainFreeRoamMappingSummary.state }}</span>
            <span class="muted">先建图，再低速扫一圈，最后保存。</span>
          </div>
          <label class="plain-trip-confirm">
            <input ref="plainFreeRoamConfirmCheckbox" v-model="plainUnifiedSafetyConfirmed" name="plainFreeRoamMappingConfirmed" type="checkbox" data-testid="plain-free-roam-confirm">
            <span>人在旁边、周围安全、可以随时按停止</span>
          </label>
          <div class="panel-action-row wrap-actions">
            <button ref="plainFreeRoamStartButton" type="button" :disabled="!canStartPlainFreeRoamMapping" data-testid="plain-free-roam-start" @click="startMapRuntime">
              {{ plainFreeRoamMappingStartLabel }}
            </button>
            <button ref="plainFreeRoamKeyboardButton" type="button" class="secondary compact-stop" :disabled="!canArmPlainFreeRoamKeyboard" data-testid="plain-free-roam-keyboard" @click="activateKeyboardControl">
              {{ plainFreeRoamKeyboardLabel }}
            </button>
            <button type="button" class="secondary compact-stop" data-testid="plain-free-roam-next-action" @click="focusPlainFreeRoamNextTarget">
              {{ plainFreeRoamNextActionLabel }}
            </button>
            <button ref="plainFreeRoamMapRefreshButton" type="button" class="secondary compact-stop" :disabled="!canRefreshPlainFreeRoamMapPreview" data-testid="plain-free-roam-map-refresh" @click="refreshMapPreview({ countForFreeRoamSession: true, radarStatusRefresh: true })">
              {{ plainFreeRoamMapPreviewLabel }}
            </button>
            <button ref="plainFreeRoamStopButton" type="button" class="danger-button compact-stop" :disabled="!canRequestKeyboardStop" data-testid="plain-free-roam-stop" @click="stopKeyboardControl('free_roam_mapping_stop')">
              停止
            </button>
            <button ref="plainFreeRoamSaveButton" type="button" class="secondary compact-stop" :disabled="!canSavePlainFreeRoamMapping" data-testid="plain-free-roam-save" @click="saveMap({ refreshRouteAfterSave: true })">
              {{ plainFreeRoamMappingSaveLabel }}
            </button>
          </div>
          <p class="panel-note" data-testid="plain-free-roam-hint">{{ plainFreeRoamMappingSummary.hint }}</p>
          <p class="panel-note" data-testid="plain-free-roam-drive-status">{{ plainFreeRoamDriveStatus }}</p>
          <p class="panel-note" data-testid="plain-free-roam-sweep-plan-summary">{{ plainFreeRoamSweepPlanSummary }}</p>
          <p class="panel-note">按住方向键或 W/A/S/D 移动，松开即停；保存后刷新地图画面检查效果。</p>
          <div class="keyboard-direction-pad" data-testid="plain-free-roam-direction-pad">
            <button
              type="button"
              :disabled="!canPressKeyboardDirection"
              data-testid="plain-free-roam-screen-forward"
              @pointerdown="handleKeyboardDirectionPointerDown('forward', $event)"
              @pointerup="handleKeyboardDirectionPointerEnd('forward', 'free_roam_screen_button_released')"
              @pointerleave="handleKeyboardDirectionPointerEnd('forward', 'free_roam_screen_button_left')"
              @pointercancel="handleKeyboardDirectionPointerEnd('forward', 'free_roam_screen_button_cancelled')"
            >
              前进
            </button>
            <div class="motion-middle-row">
              <button
                type="button"
                :disabled="!canPressKeyboardDirection"
                data-testid="plain-free-roam-screen-left"
                @pointerdown="handleKeyboardDirectionPointerDown('left', $event)"
                @pointerup="handleKeyboardDirectionPointerEnd('left', 'free_roam_screen_button_released')"
                @pointerleave="handleKeyboardDirectionPointerEnd('left', 'free_roam_screen_button_left')"
                @pointercancel="handleKeyboardDirectionPointerEnd('left', 'free_roam_screen_button_cancelled')"
              >
                左转
              </button>
              <button class="danger-button" type="button" :disabled="!canRequestKeyboardStop" data-testid="plain-free-roam-screen-stop" @click="stopKeyboardControl('free_roam_screen_button_stop')">
                停止
              </button>
              <button
                type="button"
                :disabled="!canPressKeyboardDirection"
                data-testid="plain-free-roam-screen-right"
                @pointerdown="handleKeyboardDirectionPointerDown('right', $event)"
                @pointerup="handleKeyboardDirectionPointerEnd('right', 'free_roam_screen_button_released')"
                @pointerleave="handleKeyboardDirectionPointerEnd('right', 'free_roam_screen_button_left')"
                @pointercancel="handleKeyboardDirectionPointerEnd('right', 'free_roam_screen_button_cancelled')"
              >
                右转
              </button>
            </div>
            <button
              type="button"
              :disabled="!canPressKeyboardDirection"
              data-testid="plain-free-roam-screen-back"
              @pointerdown="handleKeyboardDirectionPointerDown('back', $event)"
              @pointerup="handleKeyboardDirectionPointerEnd('back', 'free_roam_screen_button_released')"
              @pointerleave="handleKeyboardDirectionPointerEnd('back', 'free_roam_screen_button_left')"
              @pointercancel="handleKeyboardDirectionPointerEnd('back', 'free_roam_screen_button_cancelled')"
            >
              后退
            </button>
          </div>
          <div class="plain-free-roam-coverage" :data-state="plainFreeRoamCoverageSummary.state" data-testid="plain-free-roam-coverage">
            <div class="simple-status-row">
              <strong>扫图覆盖</strong>
              <span class="status-chip" :data-state="plainFreeRoamCoverageSummary.state">{{ plainFreeRoamCoverageSummary.state }}</span>
            </div>
            <div class="plain-free-roam-coverage-bar" :style="plainFreeRoamCoverageSummary.barStyle" aria-hidden="true">
              <span />
            </div>
            <p class="panel-note">{{ plainFreeRoamCoverageSummary.primary }}</p>
            <p class="panel-note">{{ plainFreeRoamCoverageSummary.secondary }}</p>
            <p class="panel-note" data-testid="plain-free-roam-coverage-guidance">{{ plainFreeRoamCoverageSummary.guidance }}</p>
          </div>
          <div class="plain-free-roam-readiness" :data-state="plainFreeRoamAutonomyReadiness.state" data-testid="plain-free-roam-autonomy-readiness">
            <div class="simple-status-row">
              <strong>自动扫图准备</strong>
              <span class="status-chip" :data-state="plainFreeRoamAutonomyReadiness.state">{{ plainFreeRoamAutonomyReadiness.state }}</span>
            </div>
            <div class="panel-action-row wrap-actions">
              <button type="button" class="secondary compact-stop" :disabled="plainFreeRoamAutonomyReadiness.disabled" data-testid="plain-free-roam-auto-start" @click="startFreeRoamAutonomy">
                {{ plainFreeRoamAutonomyReadiness.buttonLabel }}
              </button>
              <button type="button" class="secondary compact-stop" :disabled="freeRoamAutonomyLatestPending || !robotApiBaseUrl.trim()" data-testid="plain-free-roam-autonomy-latest" @click="refreshFreeRoamAutonomyLatest">
                {{ plainFreeRoamLatestButtonLabel }}
              </button>
              <button ref="plainFreeRoamAutoStopButton" type="button" class="danger-button compact-stop" :disabled="!canStopFreeRoamAutonomy" data-testid="plain-free-roam-auto-stop" @click="stopFreeRoamAutonomy">
                {{ plainFreeRoamAutoStopButtonLabel }}
              </button>
              <span class="muted">{{ plainFreeRoamAutonomyReadiness.policyText }}</span>
            </div>
            <p class="panel-note">{{ plainFreeRoamAutonomyReadiness.hint }}</p>
            <p class="panel-note" data-testid="plain-free-roam-autonomy-next-action">{{ plainFreeRoamAutonomyReadiness.nextActionText }}</p>
            <p class="panel-note" data-testid="plain-free-roam-autonomy-runtime">{{ plainFreeRoamAutonomyReadiness.runtimeText }}</p>
            <p v-if="plainFreeRoamLatestSummary" class="panel-note" data-testid="plain-free-roam-autonomy-latest-summary">{{ plainFreeRoamLatestSummary }}</p>
            <div v-if="plainFreeRoamAutonomyReadiness.blockers.length" class="plain-readiness-blockers">
              <span v-for="blocker in plainFreeRoamAutonomyReadiness.blockers" :key="blocker" class="muted">{{ blocker }}。</span>
            </div>
            <div class="plain-goal-progress" data-testid="plain-free-roam-autonomy-gates">
              <div v-for="gate in plainFreeRoamAutonomyReadiness.gateRows" :key="gate.id" class="plain-progress-row">
                <span class="plain-progress-label">{{ gate.label }}</span>
                <span class="status-chip" :data-state="gate.state">{{ gate.state }}</span>
                <span class="muted">{{ gate.hint }}</span>
              </div>
            </div>
          </div>
          <div class="plain-goal-progress" data-testid="plain-free-roam-steps">
            <div v-for="step in plainFreeRoamMappingSteps" :key="step.id" class="plain-progress-row">
              <span class="plain-progress-label">{{ step.label }}</span>
              <span class="status-chip" :data-state="step.state">{{ step.state }}</span>
              <span class="muted">{{ step.hint }}</span>
            </div>
          </div>
        </article>

        <article class="snapshot-panel plain-motion-panel" data-testid="plain-motion-panel" :data-state="plainMotionSummary.state">
          <h3>移动/导航</h3>
          <label class="plain-trip-confirm">
            <input v-model="plainUnifiedSafetyConfirmed" type="checkbox" data-testid="plain-motion-safety-confirm">
            <span>人在旁边、周围安全、停止手段就绪</span>
          </label>
          <div class="panel-action-row wrap-actions">
            <span class="status-chip" :data-state="plainMotionSummary.state">{{ plainMotionSummary.state }}</span>
            <button type="button" :disabled="!canResetLocalization" @click="resetLocalizationProof">
              {{ plainLocalizationResetButtonLabel }}
            </button>
            <label class="plain-video-ref">
              <span>现场画面记录</span>
              <input v-model="plainExternalVideoRef" name="plainExternalVideoRef" placeholder="手机视频编号">
            </label>
            <button type="button" :disabled="loading || plainVisualMaterialPending || operatorReportPending || !robotApiBaseUrl.trim() || !plainExternalVideoRef.trim()" @click="submitPlainVisualMaterial">
              记录画面
            </button>
            <button type="button" class="secondary compact-stop" :disabled="!canSubmitPlainVisualFromCamera" data-testid="plain-record-current-camera" @click="submitPlainVisualMaterialFromCameraProbe">
              {{ plainRecordCurrentCameraLabel }}
            </button>
            <button
              v-if="firstJogMaterialRestoreBlocksMotion"
              ref="plainMotionRestoreButton"
              type="button"
              class="secondary compact-stop"
              :disabled="!canRestorePlainFirstJogMaterial"
              data-testid="plain-motion-restore"
              @click="restorePlainFirstJogMaterial"
            >
              {{ plainFirstJogMaterialRestoreButtonLabel }}
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
            :data-state="plainKeyboardControlSummary.state"
            data-testid="keyboard-control-panel"
            @keydown="handleGlobalKeyDown"
            @keyup="handleGlobalKeyUp"
            @focusout="handleKeyboardControlFocusOut"
          >
            <div class="simple-status-row">
              <span class="status-chip" :data-state="plainKeyboardControlSummary.state">{{ plainKeyboardControlSummary.state }}</span>
              <span class="plain-keyboard-direction" data-testid="keyboard-current-direction">当前方向：{{ keyboardDirectionPlainLabel }}</span>
              <button ref="keyboardControlRecheckButton" class="secondary compact-stop" type="button" :disabled="!canRefreshPlainKeyboardGate" data-testid="keyboard-control-recheck" @click="refreshPlainKeyboardGate">{{ plainKeyboardRecheckButtonLabel }}</button>
              <button ref="keyboardControlArmButton" class="secondary compact-stop" type="button" :disabled="!canArmKeyboardControl" data-testid="keyboard-control-arm" @click="activateKeyboardControl">{{ plainKeyboardArmButtonLabel }}</button>
              <button class="danger-button compact-stop" type="button" :disabled="!canRequestKeyboardStop" data-testid="keyboard-control-stop" @click="stopKeyboardControl('button_stop')">键盘停止（随时可点）</button>
            </div>
            <p class="panel-note">{{ plainKeyboardControlSummary.hint }}</p>
            <p class="panel-note" data-testid="plain-keyboard-safety-summary">{{ plainKeyboardSafetySummary }}</p>
            <p class="panel-note" data-testid="keyboard-live-status">{{ plainKeyboardLiveStatus }}</p>
            <p v-if="plainKeyboardWheelFeedbackSummary" class="panel-note" data-testid="keyboard-wheel-feedback-summary">{{ plainKeyboardWheelFeedbackSummary }}</p>
            <p class="panel-note" data-testid="keyboard-last-stop-summary">{{ plainKeyboardLastStopSummary }}</p>
            <div class="keyboard-direction-pad" data-testid="keyboard-direction-pad">
              <button
                type="button"
                :disabled="!canPressKeyboardDirection"
                data-testid="keyboard-screen-forward"
                @pointerdown="handleKeyboardDirectionPointerDown('forward', $event)"
                @pointerup="handleKeyboardDirectionPointerEnd('forward', 'screen_button_released')"
                @pointerleave="handleKeyboardDirectionPointerEnd('forward', 'screen_button_left')"
                @pointercancel="handleKeyboardDirectionPointerEnd('forward', 'screen_button_cancelled')"
              >
                前进
              </button>
              <div class="motion-middle-row">
                <button
                  type="button"
                  :disabled="!canPressKeyboardDirection"
                  data-testid="keyboard-screen-left"
                  @pointerdown="handleKeyboardDirectionPointerDown('left', $event)"
                  @pointerup="handleKeyboardDirectionPointerEnd('left', 'screen_button_released')"
                  @pointerleave="handleKeyboardDirectionPointerEnd('left', 'screen_button_left')"
                  @pointercancel="handleKeyboardDirectionPointerEnd('left', 'screen_button_cancelled')"
                >
                  左转
                </button>
                <button class="danger-button" type="button" :disabled="!canRequestKeyboardStop" data-testid="keyboard-screen-stop" @click="stopKeyboardControl('screen_button_stop')">
                  停止
                </button>
                <button
                  type="button"
                  :disabled="!canPressKeyboardDirection"
                  data-testid="keyboard-screen-right"
                  @pointerdown="handleKeyboardDirectionPointerDown('right', $event)"
                  @pointerup="handleKeyboardDirectionPointerEnd('right', 'screen_button_released')"
                  @pointerleave="handleKeyboardDirectionPointerEnd('right', 'screen_button_left')"
                  @pointercancel="handleKeyboardDirectionPointerEnd('right', 'screen_button_cancelled')"
                >
                  右转
                </button>
              </div>
              <button
                type="button"
                :disabled="!canPressKeyboardDirection"
                data-testid="keyboard-screen-back"
                @pointerdown="handleKeyboardDirectionPointerDown('back', $event)"
                @pointerup="handleKeyboardDirectionPointerEnd('back', 'screen_button_released')"
                @pointerleave="handleKeyboardDirectionPointerEnd('back', 'screen_button_left')"
                @pointercancel="handleKeyboardDirectionPointerEnd('back', 'screen_button_cancelled')"
              >
                后退
              </button>
            </div>
            <p v-if="plainKeyboardNextActionSummary" class="panel-note" data-testid="plain-keyboard-next-action">
              {{ plainKeyboardNextActionSummary }}
            </p>
            <p class="panel-note" data-testid="keyboard-control-guide">{{ plainKeyboardControlGuide }}</p>
          </div>
          <p class="panel-note">{{ plainMotionSummary.hint }}</p>
          <div class="plain-goal-progress" :data-state="plainGoalProgressPanelState" data-testid="plain-goal-progress">
            <div class="simple-status-row">
              <strong>本轮进度</strong>
              <span class="status-chip" :data-state="plainGoalProgressPanelState" data-testid="plain-goal-progress-panel-state">{{ plainGoalProgressPanelState }}</span>
              <button type="button" class="secondary compact-stop" :disabled="!plainGoalProgressPrimaryTarget" data-testid="plain-goal-progress-primary-action" @click="focusPlainGoalProgressTarget(plainGoalProgressPrimaryTarget)">
                {{ plainGoalProgressPrimaryActionLabel }}
              </button>
              <button type="button" class="secondary compact-stop" :disabled="!canRefreshPlainGoalProgress" data-testid="plain-goal-progress-refresh" @click="refreshPlainGoalProgress">
                {{ plainGoalProgressRefreshButtonLabel }}
              </button>
            </div>
            <p class="panel-note" data-testid="plain-goal-progress-next-action">{{ plainGoalProgressNextAction }}</p>
            <p class="panel-note" data-testid="plain-goal-progress-state-summary">{{ plainGoalProgressStateSummary }}</p>
            <p class="panel-note" data-testid="plain-goal-progress-evidence-summary">{{ plainGoalProgressEvidenceSummary }}</p>
            <p class="panel-note" data-testid="plain-goal-progress-blocker-summary">{{ plainGoalProgressBlockerSummary }}</p>
            <div v-for="item in plainGoalProgressItems" :key="item.id" class="plain-progress-row">
              <span class="plain-progress-label">{{ item.label }}</span>
              <span class="status-chip" :data-state="item.state">{{ item.state }}</span>
              <span class="muted">{{ item.hint }}</span>
              <small class="muted" :data-testid="`plain-goal-progress-next-${item.id}`">{{ item.nextAction }}</small>
              <button type="button" class="secondary compact-stop" :data-testid="`plain-goal-progress-go-${item.id}`" @click="focusPlainGoalProgressTarget(item.id)">
                {{ item.actionLabel }}
              </button>
            </div>
          </div>
          <div ref="plainTripRunPanel" class="plain-trip-run" tabindex="-1" :data-state="plainTripSummary.state" data-testid="plain-trip-run">
            <div class="simple-status-row">
              <strong>行程操作</strong>
              <span class="status-chip" :data-state="plainTripSummary.state">{{ plainTripSummary.state }}</span>
            </div>
            <label class="plain-trip-confirm">
              <input ref="plainTripSafetyCheckbox" v-model="plainUnifiedSafetyConfirmed" name="plainTripSafetyConfirmed" type="checkbox">
              <span>人在旁边、周围安全、停止手段就绪</span>
            </label>
            <div class="simple-status-row">
              <button ref="plainTripPrepareButton" type="button" class="secondary compact-stop" :disabled="!canRefreshPlainTripPreparation" data-testid="plain-trip-prepare" @click="refreshNav2Proof">
                {{ plainTripPreparationButtonLabel }}
              </button>
              <button ref="plainTripExecuteButton" type="button" class="danger-button compact-stop" :disabled="!canRunPlainTripExecution" data-testid="plain-trip-execute" @click="runPlainTripExecution">
                {{ plainTripExecutionButtonLabel }}
              </button>
              <button ref="plainTripLatestButton" type="button" class="secondary compact-stop" :disabled="!canLoadNavGoalExecutionLatest" data-testid="plain-trip-latest" @click="loadNavGoalExecutionLatest">
                {{ plainTripLatestButtonLabel }}
              </button>
              <button v-if="navGoalExecutionPending" type="button" class="danger-button compact-stop" :disabled="!canSendStop" data-testid="plain-trip-stop" @click="stopPlainTripExecution">
                {{ plainTripStopButtonLabel }}
              </button>
            </div>
            <p class="panel-note">{{ plainTripSummary.hint }}</p>
            <p class="panel-note" data-testid="plain-trip-run-status">{{ plainTripRunStatus }}</p>
            <p class="panel-note" data-testid="plain-trip-minimal-precheck">{{ plainTripMinimalPrecheckSummary }}</p>
            <p v-if="plainTripExecutionProgress" class="panel-note" data-testid="plain-trip-execution-progress">{{ plainTripExecutionProgress }}</p>
            <p v-if="plainTripRouteWysiwygSummary" class="panel-note" data-testid="plain-trip-route-wysiwyg">
              {{ plainTripRouteWysiwygSummary }}
            </p>
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
              <button ref="plainFirstJogRestoreButton" type="button" class="secondary compact-stop" :disabled="!canRestorePlainFirstJogMaterial" data-testid="plain-first-jog-restore" @click="restorePlainFirstJogMaterial">
                {{ plainFirstJogMaterialRestoreButtonLabel }}
              </button>
              <button ref="plainWheelTrialButton" type="button" class="secondary compact-stop" :disabled="plainWheelTrialDisabled" data-testid="plain-wheel-trial" @click="sendPlainFirstJog">
                {{ plainWheelTrialButtonLabel }}
              </button>
              <button ref="plainWheelReadbackButton" type="button" class="secondary compact-stop" :disabled="loading || !canRunBaseFeedbackSamples" data-testid="plain-wheel-readback-refresh" @click="runBaseFeedbackSamples">
                {{ plainWheelReadbackButtonLabel }}
              </button>
              <button v-if="plainWheelZeroBlockerActive" ref="plainWheelZeroCheckButton" type="button" class="secondary compact-stop" data-testid="plain-wheel-zero-check" @click="markPlainWheelZeroBlockerChecked">
                {{ plainWheelZeroBlockerButtonLabel }}
              </button>
              <button ref="plainWheelSaveButton" type="button" class="secondary compact-stop" :disabled="!canSavePlainWheelEvidence" data-testid="plain-wheel-save" @click="savePlainWheelEvidence">
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
            <p v-if="plainWheelZeroBlockerSummary" class="panel-note" data-testid="plain-wheel-zero-check-summary">
              {{ plainWheelZeroBlockerSummary }}
            </p>
            <p v-if="plainLidarMotionRecordSummary" class="panel-note" data-testid="plain-lidar-motion-record-summary">
              {{ plainLidarMotionRecordSummary }}
            </p>
            <p v-if="plainWheelEvidenceSaveSummary" class="panel-note">{{ plainWheelEvidenceSaveSummary }}</p>
          </div>
          <div ref="plainDeliveryStatusPanel" class="plain-delivery-status" tabindex="-1" data-testid="plain-delivery-status" :data-state="plainDeliverySummary.state">
            <div class="simple-status-row">
              <strong>任务收口</strong>
              <span class="status-chip" :data-state="plainDeliverySummary.state">{{ plainDeliverySummary.state }}</span>
              <button type="button" class="secondary compact-stop" :disabled="!canLoadDeliveryLatest" data-testid="plain-delivery-latest" @click="loadDeliveryLatest">
                {{ plainDeliveryLatestButtonLabel }}
              </button>
              <button type="button" class="secondary compact-stop" :disabled="!canCheckDeliveryGap" data-testid="plain-delivery-gap-check" @click="checkDeliveryGap">
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
                ref="plainDeliveryPrefillButton"
                type="button"
                class="secondary compact-stop"
                :disabled="!canPrefillDeliveryMaterialRefs"
                data-testid="plain-delivery-prefill-material"
                @click="prefillDeliveryMaterialRefs"
              >
                {{ plainDeliveryPrefillButtonLabel }}
              </button>
              <button
                ref="plainDeliveryDraftSaveButton"
                type="button"
                class="secondary compact-stop"
                :disabled="loading || plainDeliveryMapWysiwygPending || operatorReportPending || !robotApiBaseUrl.trim() || !deliveryOperatorVideoRef.trim() || !deliveryOperatorRouteMapRef.trim()"
                data-testid="plain-delivery-draft-save"
                @click="submitDeliveryDraftMaterial"
              >
                {{ plainDeliveryDraftSaveButtonLabel }}
              </button>
            </div>
            <p class="panel-note">{{ plainDeliveryMaterialSummary.hint }}</p>
            <div ref="plainDeliveryFinalPanel" class="plain-delivery-final" tabindex="-1" data-testid="plain-delivery-final-confirm" :data-state="plainDeliveryConfirmSummary.state">
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
                <button ref="plainDeliveryAllConfirmedButton" type="button" class="secondary compact-stop" data-testid="plain-delivery-mark-all-confirmed" @click="markAllDeliveryConfirmations">
                  {{ plainDeliveryAllConfirmedButtonLabel }}
                </button>
              </div>
              <p class="panel-note">{{ plainDeliveryConfirmSummary.hint }}</p>
              <p v-if="plainDeliveryConfirmMissingSummary" class="panel-note" data-testid="plain-delivery-confirm-missing">
                {{ plainDeliveryConfirmMissingSummary }}
              </p>
              <p v-if="plainDeliverySubmitResultSummary" class="panel-note" data-testid="plain-delivery-submit-result">
                {{ plainDeliverySubmitResultSummary }}
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
                ref="plainDeliveryConfirmSubmitButton"
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
              <span>Robot API base URL</span>
              <input v-model="robotApiBaseUrl" name="robotApiBaseUrl" placeholder="http://192.168.1.11:8787">
            </label>
            <div class="panel-action-row">
              <button class="secondary compact-stop" type="button" :disabled="loading || robotApiBaseUrlUsesDefault" data-testid="robot-api-default-advanced" @click="resetRobotApiBaseUrlToDefault">恢复默认地址</button>
              <span class="muted">普通首屏固定使用默认小车；改地址仅用于高级联调。</span>
            </div>
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
            <dt>raw_failure_reason</dt>
            <dd>{{ rawFailureReason || "none" }}</dd>
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
            <button class="secondary" type="button" :disabled="!canStartRadarLifecycle" @click="startRadarLifecycle">
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
            <button class="secondary" type="button" :disabled="!canSaveMapLifecycle" @click="saveMap">
              保存地图
            </button>
            <button class="secondary" type="button" :disabled="!canStartMapLifecycle" @click="startMapRuntime">
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
            <button class="secondary" type="button" :disabled="!canRefreshNav2Proof" data-testid="advanced-nav2-proof-refresh" @click="refreshNav2Proof">
              {{ nav2ProofRefreshButtonLabel }}
            </button>
            <button class="secondary" type="button" :disabled="!canResetLocalization" @click="resetLocalizationProof">
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
            <button class="secondary" type="button" :disabled="!canLoadNavGoalExecutionLatest" @click="loadNavGoalExecutionLatest">
              读取最近 Nav2 结果（高级）
            </button>
            <button class="secondary" type="button" :disabled="!canLoadDeliveryLatest" @click="loadDeliveryLatest">
              读取送达缺口（高级）
            </button>
            <button class="secondary" type="button" :disabled="!canCheckDeliveryGap" @click="checkDeliveryGap">
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
              data-testid="advanced-delivery-prefill-material"
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
            <button class="secondary" type="button" :disabled="!canFillDeliveryVideoRefFromCameraProbe" @click="fillDeliveryVideoRefFromCameraProbe">
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
            <button class="danger-button" type="submit" :disabled="loading || operatorReportPending || deliveryCompletionPending || !robotApiBaseUrl.trim() || !deliveryNav2GoalReady || !deliveryRouteMapMatchesFreshNav2 || !deliveryOperatorConfirmationReady || !deliveryOperatorVideoRef.trim() || !deliveryOperatorRouteMapRef.trim()">
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
            <dt>goal minimal safety gate</dt>
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
          <button class="secondary" type="button" :disabled="!canRunBaseFeedbackSamples" @click="runBaseFeedbackSamples">
            {{ baseFeedbackSamplesPending ? "采集中..." : mapWysiwygRefreshPending ? "等待地图刷新" : "采集底盘反馈（高级）" }}
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
              {{ manualCommandResult?.operator_report_preflight?.status ?? "not_loaded" }} /
              {{ manualCommandResult?.operator_report_preflight?.failure_reason || "none" }}
            </dd>
            <dt>operator report preflight missing</dt>
            <dd>{{ listText(manualCommandResult?.operator_report_preflight?.missing_fields, "none") }}</dd>
            <dt>operator report preflight summary</dt>
            <dd>
              endpoint={{ manualCommandResult?.operator_report_preflight?.source_endpoint ?? "/api/operator/report" }},
              http={{ manualCommandResult?.operator_report_preflight?.http_status ?? "n/a" }},
              report={{ manualCommandResult?.operator_report_preflight?.report_status ?? "not_loaded" }},
              evidence={{ manualCommandResult?.operator_report_preflight?.evidence_ref ?? "not_loaded" }}
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
              /api/radar/status={{ effectiveLidarReadback?.status ?? "not_loaded" }},
              scan={{ effectiveLidarReadback?.latest_scan_proof_status ?? "not_loaded" }},
              raw={{ effectiveLidarReadback?.latest_raw_packet_proof_status ?? "not_loaded" }},
              continuous={{ effectiveLidarReadback?.continuous_scan_status ?? "not_loaded" }},
              lifecycle={{ effectiveLidarReadback?.lifecycle_running ?? "not_loaded" }}/{{ effectiveLidarReadback?.lifecycle_state ?? "not_loaded" }},
              window={{ effectiveLidarReadback?.continuous_window_observed ?? "not_loaded" }}/{{ effectiveLidarReadback?.continuity_window_status ?? "not_loaded" }},
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
