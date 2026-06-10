<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  getO7ConsumerTaskDetail,
  getRobotControlSummary,
  postRobotControlBaseManual,
  postRobotControlBaseStop,
  postRobotControlMapProofRefresh,
  postRobotControlRadarScanProofRefresh,
  postRobotControlCameraOffer,
  postRobotControlCameraPeerClose,
} from "../client/workstationApi";
import type {
  O7ConsumerTaskDetailResponse,
  RobotControlBaseCommandProxyResponse,
  RobotControlPreviewStatus,
  RobotControlProofRefreshProxyResponse,
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
const mapRefreshResult = ref<RobotControlProofRefreshProxyResponse | null>(null);
const manualCommandResult = ref<RobotControlBaseCommandProxyResponse | null>(null);
const manualCommandPending = ref(false);
const jogSpeedMps = ref(0.08);
const jogDurationMs = ref(500);
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
const mapRefreshPending = ref(false);
const previewVideo = ref<HTMLVideoElement | null>(null);
const previewStream = ref<MediaStream | null>(null);
const previewPeerConnection = ref<RTCPeerConnection | null>(null);
const previewStartPending = ref(false);
const previewStopPending = ref(false);
const sessionEpoch = ref(0);

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

function recordContains(record: Record<string, string> | undefined, needle: string): boolean {
  // 首屏只看人话摘要，具体 key 需要在详情里复核，所以这里用宽松字符串匹配。
  if (!record) {
    return false;
  }
  return Object.entries(record).some(([key, value]) => key.includes(needle) || value.includes(needle));
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
  if (connection.status === "readable" && connection.failed_count === 0 && connection.blocked_count === 0) {
    return { state: "已连接", hint: "已读到小车状态摘要。" };
  }
  if (connection.status === "blocked" || connection.failed_count > 0 || connection.blocked_count > 0 || connection.dangerous_true_fields.length > 0) {
    return { state: "有异常", hint: "可读到部分信息，但有字段被阻断或失败。" };
  }
  return { state: "未连接", hint: "还没有连上可读状态。" };
}

function summarizeCameraState(): { state: "未打开" | "连接中" | "已打开" | "失败"; hint: string } {
  // 摄像头首屏只暴露会话进度，不泄露 peer / ICE / SDP 细节。
  switch (previewStatus.value) {
    case "starting_local_peer":
    case "connecting_offer_posted":
      return { state: "连接中", hint: "正在打开实时画面。" };
    case "streaming":
      return { state: "已打开", hint: "画面已打开，控制仍然锁定。" };
    case "start_failed":
    case "peer_cleanup_failed":
      return { state: "失败", hint: failureReason.value || "打开画面失败。" };
    default:
      return { state: "未打开", hint: "还没有打开实时画面。" };
  }
}

function summarizeProofState(pending: boolean, result: RobotControlProofRefreshProxyResponse | null): { state: "未刷新" | "刷新中" | "已刷新" | "失败"; hint: string } {
  // 雷达和地图首屏共用同一套人话状态，细节保留给详情区。
  if (pending) {
    return { state: "刷新中", hint: "正在刷新证据。" };
  }
  if (!result) {
    return { state: "未刷新", hint: "还没有刷新过。" };
  }
  if (result.proxy_status === "refresh_failed" || result.status === "blocked" || result.last_result_status === "fetch_failed") {
    return { state: "失败", hint: result.failure_reason || "刷新失败。" };
  }
  return { state: "已刷新", hint: "已经拿到最新证据。" };
}

function summarizeRadarEvidence(): string {
  // 只给出 scan / tf 的人话判断，不把 raw packet 等字段铺到首屏。
  if (!radarRefreshResult.value) {
    return "scan 未见；tf 未见。";
  }
  const record = radarRefreshResult.value.latest_readback_key_values;
  const scanVisible = recordContains(record, "scan");
  const tfVisible = recordContains(record, "tf");
  return `scan ${scanVisible ? "可见" : "未见"}；tf ${tfVisible ? "可见" : "未见"}。`;
}

function summarizeMapEvidence(): string {
  // 地图首屏只说 map / evidence 的可见性，不展开 proof schema。
  if (!mapRefreshResult.value) {
    return "map 未见；evidence 未见。";
  }
  const record = mapRefreshResult.value.latest_readback_key_values;
  const mapVisible = recordContains(record, "map");
  const evidenceVisible = recordContains(record, "evidence");
  return `map ${mapVisible ? "可见" : "未见"}；evidence ${evidenceVisible ? "可见" : "未见"}。`;
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
const radarSummary = computed(() => summarizeProofState(radarRefreshPending.value, radarRefreshResult.value));
const mapSummary = computed(() => summarizeProofState(mapRefreshPending.value, mapRefreshResult.value));
const manualBoundary = computed(() => robotSummary.value?.safe_command_boundary ?? null);
const manualSpeedLimit = computed(() => manualBoundary.value?.speed_limit_mps ?? 0.12);
const manualDurationLimit = computed(() => manualBoundary.value?.duration_limit_ms ?? 800);
const checklistMissing = computed(() => hilChecklist.value.filter((item) => !item.checked).map((item) => item.label));
const hilChecklistConfirmed = computed(() => checklistMissing.value.length === 0);
const canSendStop = computed(() => !manualCommandPending.value && !loading.value && robotApiBaseUrl.value.trim().length > 0);
const manualBlockedReason = computed(() => {
  if (!robotApiBaseUrl.value.trim()) {
    return "先输入小车地址并连接。";
  }
  if (!hilChecklistConfirmed.value) {
    return `还缺现场确认：${checklistMissing.value.join("；")}。`;
  }
  return "允许发送一次低速短时点动；安全锁定不会解除。";
});
const manualMotionSummary = computed(() => {
  // 首屏只呈现普通用户能理解的状态，不把代理合同细节直接抛到第一屏。
  if (manualCommandPending.value) {
    return { state: "发送中", hint: "正在发送本次点动或停止请求。" };
  }
  if (!manualCommandResult.value) {
    return hilChecklistConfirmed.value
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
  return JSON.stringify(record).slice(0, 260);
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

function makeRefreshFallback(
  kind: "radar_scan_proof_refresh" | "map_proof_refresh",
  baseUrl: string,
  reason: string,
): RobotControlProofRefreshProxyResponse {
  // 网络错误或解析错误时也要保留卡片字段，避免 UI 空白后误读为成功。
  const now = Date.now();
  const endpoint = kind === "radar_scan_proof_refresh" ? "/api/radar/scan-proof/refresh" : "/api/map/proof/refresh";
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

function stampNow(): string {
  // 时间戳使用浏览器本地 ISO 字符串，足够支撑 operator 复核最近一次 Start/Stop。
  return new Date().toISOString();
}

function clearPreviewElement(): void {
  // 离开页面或停止时必须清空 srcObject，避免 UI 继续显示上一轮残留帧。
  if (previewVideo.value) {
    previewVideo.value.srcObject = null;
  }
}

function replacePreviewStream(track: MediaStreamTrack | null): void {
  // 页面只消费远端 video track；不申请音频，也不把其他 track 混入 video 元素。
  previewStream.value?.getTracks().forEach((streamTrack) => streamTrack.stop());
  if (!track) {
    previewStream.value = null;
    clearPreviewElement();
    return;
  }
  const nextStream = new MediaStream([track]);
  previewStream.value = nextStream;
  if (previewVideo.value) {
    previewVideo.value.srcObject = nextStream;
  }
}

function bindVideoTrack(track: MediaStreamTrack, epoch: number): void {
  // track 生命周期要绑定到当前 session，避免旧 peer 的 ended 事件覆盖新会话状态。
  if (sessionEpoch.value !== epoch) {
    return;
  }
  videoTrackState.value = track.readyState;
  replacePreviewStream(track);
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
  replacePreviewStream(null);
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
  kind: "radar_scan_proof_refresh" | "map_proof_refresh",
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

async function refreshMapProof(): Promise<void> {
  // Map refresh 只刷新 no-motion map proof snapshot，不开启建图、导航或路径执行。
  await runRefreshAction(
    "map_proof_refresh",
    () => postRobotControlMapProofRefresh(robotApiBaseUrl.value),
    mapRefreshResult,
    mapRefreshPending,
  );
}

async function sendManualMotion(direction: "forward" | "back" | "left" | "right"): Promise<void> {
  // 非 stop 点动必须通过 checklist gate；即使远端成功，也继续维持 fail-closed UI。
  if (!hilChecklistConfirmed.value || !robotApiBaseUrl.value.trim() || manualCommandPending.value) {
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
      request_contract: {
        max_speed_mps: manualSpeedLimit.value,
        max_duration_ms: manualDurationLimit.value,
        allowed_directions: manualBoundary.value?.allowed_directions ?? ["forward", "back", "left", "right", "stop"],
      },
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
      request_contract: {
        max_speed_mps: manualSpeedLimit.value,
        max_duration_ms: manualDurationLimit.value,
        allowed_directions: manualBoundary.value?.allowed_directions ?? ["forward", "back", "left", "right", "stop"],
      },
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
      bindVideoTrack(track, epoch);
    };

    const localOffer = await peer.createOffer();
    await peer.setLocalDescription(localOffer);
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
    videoElement.srcObject = previewStream.value;
  }
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
    <div class="section-head compact-head">
      <div>
        <p class="eyebrow">小车控制</p>
        <h2>Rober 小车</h2>
        <p class="muted">面向普通用户的简易风格，真实控制仍保持锁定。</p>
      </div>
      <span class="pill danger">安全锁定</span>
    </div>

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

    <div class="robot-console-grid">
      <article class="snapshot-panel">
        <h3>小车连接</h3>
        <div class="simple-status-row">
          <span class="status-chip" :data-state="robotConnectionSummary.state">{{ robotConnectionSummary.state }}</span>
          <span class="muted">{{ robotConnectionSummary.hint }}</span>
        </div>
        <p class="panel-note">先输入地址，再点连接/刷新；真正控制始终关闭。</p>
      </article>

      <article class="snapshot-panel">
        <h3>实时画面</h3>
        <div class="panel-action-row">
          <button type="button" :disabled="!canStartPreview" @click="startPreview">打开画面</button>
          <button type="button" :disabled="!canStopPreview" @click="stopPreview">关闭画面</button>
          <span class="status-chip" :data-state="cameraSummary.state">{{ cameraSummary.state }}</span>
        </div>
        <video ref="previewVideo" autoplay muted playsinline />
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
        <p class="panel-note">{{ radarSummary.hint }} {{ summarizeRadarEvidence() }}</p>
      </article>

      <article class="snapshot-panel">
        <h3>地图</h3>
        <div class="panel-action-row">
          <button type="button" :disabled="loading || mapRefreshPending || !robotApiBaseUrl.trim()" @click="refreshMapProof">
            刷新地图
          </button>
          <span class="status-chip" :data-state="mapSummary.state">{{ mapSummary.state }}</span>
        </div>
        <p class="panel-note">{{ mapSummary.hint }} {{ summarizeMapEvidence() }}</p>
      </article>

      <article class="snapshot-panel">
        <h3>移动/导航</h3>
        <div class="panel-action-row wrap-actions">
          <span class="status-chip" :data-state="manualMotionSummary.state">{{ manualMotionSummary.state }}</span>
          <span class="status-chip" data-state="locked">自动导航（未开放）</span>
        </div>
        <p class="panel-note">{{ manualBoundary?.manual_motion_entry_label ?? "受控点动（需现场确认）" }}</p>
        <div class="motion-pad">
          <button type="button" :disabled="manualCommandPending || !hilChecklistConfirmed || !robotApiBaseUrl.trim()" @click="sendManualMotion('forward')">前进</button>
          <div class="motion-middle-row">
            <button type="button" :disabled="manualCommandPending || !hilChecklistConfirmed || !robotApiBaseUrl.trim()" @click="sendManualMotion('left')">左转</button>
            <button type="button" class="danger-button" :disabled="!canSendStop" @click="sendStop">停止</button>
            <button type="button" :disabled="manualCommandPending || !hilChecklistConfirmed || !robotApiBaseUrl.trim()" @click="sendManualMotion('right')">右转</button>
          </div>
          <button type="button" :disabled="manualCommandPending || !hilChecklistConfirmed || !robotApiBaseUrl.trim()" @click="sendManualMotion('back')">后退</button>
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
        <p class="panel-note">非 stop 方向必须勾完整 checklist；stop 可单独发送。</p>
      </article>
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
          <dl class="kv compact-kv">
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
          </dl>
        </section>

        <section class="advanced-block">
          <h3>雷达详情</h3>
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
          </dl>
        </section>

        <section class="advanced-block">
          <h3>地图详情</h3>
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
          </dl>
        </section>

        <section class="advanced-block">
          <h3>任务与证据</h3>
          <dl class="kv compact-kv">
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
          <h3>控制边界 / readback</h3>
          <p class="muted">{{ robotSummary?.safe_command_boundary.locked_reason ?? "locked by V1 boundary" }}</p>
          <dl class="kv compact-kv">
            <dt>manual motion entry</dt>
            <dd>{{ robotSummary?.safe_command_boundary.manual_motion_entry_status ?? "not_loaded" }}</dd>
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
