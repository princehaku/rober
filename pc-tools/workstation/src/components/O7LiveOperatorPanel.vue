<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  getO7DirectUpperStatus,
  getO7LocalWebrtcCamera,
  postO7DirectUpperManual,
  postO7DirectUpperOperatorCommand,
  postO7DirectUpperStop,
} from "../client/workstationApi";
import type {
  O7DirectUpperApiCommandResponse,
  O7DirectUpperApiStatusResponse,
  O7LiveOperatorDirection,
  O7LiveOperatorPanelResponse,
  O7LocalWebrtcCameraResponse,
} from "../shared/contracts";

const props = defineProps<{
  liveOperatorPanel: O7LiveOperatorPanelResponse | null;
}>();

const speed = ref(0.2);
const lockMessage = ref("控制锁定：底盘串口/反馈/ACK 未确认");
const cameraSmoke = ref<O7LocalWebrtcCameraResponse | null>(null);
const directUpperStatus = ref<O7DirectUpperApiStatusResponse | null>(null);
const cameraLoading = ref(true);
const directUpperLoading = ref(true);
const cameraError = ref("");
const directUpperError = ref("");
const cameraVideo = ref<HTMLVideoElement | null>(null);
const cameraPreviewStatus = ref<"idle" | "connecting" | "playing" | "failed">("idle");
const cameraPreviewMessage = ref("摄像头状态读取中");
const cameraPeerId = ref<string | null>(null);
const manualCommandInFlight = ref<O7LiveOperatorDirection | null>(null);
const operatorCommandInFlight = ref<string | null>(null);
const operatorEvidenceRef = ref("operator_field_report_pending");
const operatorReportNote = ref("not_proven: waiting for field evidence");
const mapId = ref("latest");
const operatorConfirmed = ref(false);
const fixtureMode = ref(false);
let cameraPeerConnection: RTCPeerConnection | null = null;

interface CameraOfferAnswerPayload {
  type: "answer" | "pranswer" | "rollback";
  sdp?: string;
  peer_id?: string;
  error?: string;
}

interface BaseBoundaryDisplay {
  observed_write_device: string;
  baudrate: number;
  required_feedback_id: string;
  t1001_feedback_status: string;
  manual_control_status: string;
}

const directionLabels: Record<O7LiveOperatorDirection, string> = {
  forward: "前进",
  back: "后退",
  left: "左转",
  right: "右转",
  stop: "Stop",
};

const STRAIGHT_PULSE_DURATION_MS = 250;
const TURN_PULSE_DURATION_MS = 350;
const TURN_PULSE_SPEED_MPS = 0.08;
const KEYBOARD_DIRECTIONS: Record<string, O7LiveOperatorDirection> = {
  w: "forward",
  s: "back",
  a: "left",
  d: "right",
  " ": "stop",
  spacebar: "stop",
  x: "stop",
};

const statusLights = computed(() => [
  {
    label: "在线",
    tone: props.liveOperatorPanel?.ssh.reachable ? "green" : "gray",
    text: props.liveOperatorPanel?.ssh.reachable
      ? `8787 API ${props.liveOperatorPanel.ssh.workstation_api_8787_status}`
      : "未连接",
  },
  {
    label: "安全锁",
    tone: props.liveOperatorPanel?.safe_to_control ? "green" : "yellow",
    text: props.liveOperatorPanel?.safe_to_control ? "已解锁" : "控制锁定",
  },
  {
    label: "摄像头",
    tone: cameraSmoke.value?.status === "ready" ? "green" : "yellow",
    text: cameraSmoke.value?.status === "ready" ? "8088 ready" : "等待服务",
  },
  {
    label: "雷达",
    tone: props.liveOperatorPanel?.realtime_radar.ready ? "green" : "yellow",
    text: props.liveOperatorPanel?.realtime_radar.ready ? "/scan ready" : "等待 /scan",
  },
  {
    label: "底盘",
    tone: props.liveOperatorPanel?.control.robot_ack_connected ? "green" : "red",
    text: props.liveOperatorPanel?.control.robot_ack_connected ? "ACK 已连接" : "未确认",
  },
]);

const directUpperModeText = computed(() => {
  // Direct mode 的状态来自 PC 本机 API；未配置时明确提示 env，而不是假装 cloud relay 可用。
  if (directUpperLoading.value) {
    return "正在检查 direct upper mode";
  }
  if (directUpperError.value) {
    return `本机 API 暂不可读：${directUpperError.value}`;
  }
  const status = directUpperStatus.value;
  if (!status || status.status === "not_configured") {
    return "未配置 ROBER_UPPER_API_BASE_URL";
  }
  return `${status.status} · ${status.upper_status_summary.base_port} · ${status.upper_status_summary.lidar_port}`;
});

const directUpperPaths = computed(() => {
  // 路径由后端 contract 返回，方便 curl/浏览器工具复制并避免前端散落 endpoint 字符串。
  const paths = directUpperStatus.value?.local_api_paths;
  return paths
    ? [
        paths.status,
        paths.stop,
        paths.feedback_request,
        paths.manual,
        paths.radar_start,
        paths.radar_stop,
        paths.map_start,
        paths.map_reset,
        paths.map_save,
        paths.map_load,
        paths.map_list,
        paths.localize_reset,
        paths.operator_report,
      ]
    : [
        "/api/o7/direct-upper/status",
        "/api/o7/direct-upper/base/stop",
        "/api/o7/direct-upper/base/feedback-request",
        "/api/o7/direct-upper/base/manual",
        "/api/o7/direct-upper/radar/start",
        "/api/o7/direct-upper/radar/stop",
        "/api/o7/direct-upper/map/start",
        "/api/o7/direct-upper/map/reset",
        "/api/o7/direct-upper/map/save",
        "/api/o7/direct-upper/map/load",
        "/api/o7/direct-upper/map/list",
        "/api/o7/direct-upper/localize/reset",
        "/api/o7/direct-upper/operator-report",
      ];
});

const operatorControls = computed(() => [
  { id: "radar_start", label: "Radar start", kind: "radar_start" as const, payload: {} },
  { id: "radar_stop", label: "Radar stop", kind: "radar_stop" as const, payload: {} },
  { id: "map_start", label: "Map start", kind: "map_start" as const, payload: {} },
  { id: "map_reset", label: "Map reset", kind: "map_reset" as const, payload: {} },
  { id: "map_save", label: "Map save", kind: "map_save" as const, payload: { map_id: mapId.value } },
  { id: "map_load", label: "Map load", kind: "map_load" as const, payload: { map_id: mapId.value } },
  { id: "map_list", label: "Map list", kind: "map_list" as const, payload: {} },
  { id: "localize_reset", label: "Localize reset", kind: "localize_reset" as const, payload: {} },
]);

const directUpperEvidenceSummary = computed(() => {
  // evidence_ref 由 operator 显式填写；缺省值仍是 pending，不能被 UI 包装成现场材料。
  const status = directUpperStatus.value?.upper_status_summary;
  const map = status?.map_artifact_ref ?? "not_loaded";
  const localize = status?.localization_status ?? "not_loaded";
  const report = status?.operator_report_evidence_ref ?? "missing_operator_report";
  return `map=${map} · localize=${localize} · report=${report}`;
});

const operatorEvidenceRefValue = computed(() => {
  // 空 evidence_ref 会让现场链路无法复盘，因此统一压成 missing token 进入所有命令 envelope。
  const trimmed = operatorEvidenceRef.value.trim();
  return trimmed || "missing_operator_evidence_ref";
});

const operatorModeSummary = computed(() => {
  // fixture mode 是显式软件护栏模式，真实上位机未执行时也必须在 UI 文案里暴露。
  return fixtureMode.value
    ? "fixture mode · no upper fetch · software_guard"
    : "real upper mode · radar/report use field_default if env is absent; base/map/localize still require env";
});

const directUpperAdapterSummary = computed(() => {
  // adapter 指纹用于现场识别旧 Vite middleware；缺字段时优先提示重启 dev server。
  const adapter = directUpperStatus.value?.adapter;
  if (!adapter) {
    return "adapter=missing · stale_dev_server_missing_adapter · restart npm run dev";
  }
  return `adapter=${adapter.version} · source=${adapter.source} · field_default=${adapter.field_default_enabled ? adapter.field_default_url : "disabled"}`;
});

const directUpperStaleWarning = computed(() => {
  // 旧 5173 进程可能固定住旧 Express app；这个提示只来自 API 指纹，不靠 operator 猜测。
  const status = directUpperStatus.value;
  if (!status) {
    return "";
  }
  if (!status.adapter) {
    return "stale_dev_server_missing_adapter：当前 5173 API 不是本轮 direct-upper adapter，请重启 npm run dev。";
  }
  if (status.status === "not_configured" || status.upper_api_base_url_source === "not_configured") {
    return "direct_upper_not_using_field_default：若 Radar start 仍报 base_url_not_configured，请重启占用 5173 的旧 Vite 进程。";
  }
  return "";
});

const cameraStatusText = computed(() => {
  // 摄像头 ready 只来自 PC 后端对 8088 /health 和 /devices 的只读摘要。
  if (cameraSmoke.value?.status === "ready") {
    return "上位机 8088 ready";
  }
  if (cameraLoading.value) {
    return "正在检查摄像头";
  }
  return props.liveOperatorPanel?.camera.health_status === "not_listening_observed"
    ? "上位机 8088 未监听"
    : "等待摄像头服务";
});

const cameraUrl = computed(() => {
  // 打开页面和创建 offer 都必须是用户显式动作，避免首屏并发页面抢占 camera peer。
  return cameraSmoke.value?.camera_page_url || props.liveOperatorPanel?.camera.lan_page_url || "#";
});

const cameraSource = computed(() => {
  // 用户界面固定显示历史可用源；local camera API 的 0 不能覆盖合同中的 /dev/video1。
  return props.liveOperatorPanel?.camera.video_source ?? "/dev/video1";
});

const cameraPreviewTone = computed(() => {
  // 预览状态只描述媒体链路，不代表底盘、ROS2、Nav2 或 robot ACK 可控。
  if (cameraPreviewStatus.value === "playing") {
    return "画面已连接";
  }
  if (cameraPreviewStatus.value === "connecting") {
    return "正在连接";
  }
  if (cameraPreviewStatus.value === "failed") {
    return "预览失败";
  }
  return cameraSmoke.value?.status === "ready" ? "准备连接" : "等待摄像头";
});

const controlDetails = computed(() => {
  const reasons = props.liveOperatorPanel?.control.blocked_reasons ?? [];
  if (!reasons.length) {
    return "等待底盘串口身份、T=1001 反馈和机器人 ACK 确认。";
  }
  return `工程详情：${reasons.join(" / ")}`;
});

const baseBoundaryText = computed(() => {
  const boundary = (props.liveOperatorPanel?.control as { base_boundary?: BaseBoundaryDisplay } | undefined)
    ?.base_boundary;
  if (!boundary) {
    return "底盘边界：manual control fail-closed，未配置真实控制入口。";
  }
  return [
    `${boundary.observed_write_device} @ ${boundary.baudrate}`,
    `${boundary.required_feedback_id} ${boundary.t1001_feedback_status}`,
    `manual control ${boundary.manual_control_status}`,
  ].join(" · ");
});

const realtimeRadar = computed(() => {
  // 雷达状态只读后端派生字段，前端不把 raw packet 或串口材料重新计算为 ready。
  return props.liveOperatorPanel?.realtime_radar ?? null;
});

const realtimeMap = computed(() => {
  // 地图状态依赖后端 map/SLAM artifact 摘要；没有 /scan 时始终等待雷达。
  return props.liveOperatorPanel?.realtime_map ?? null;
});

const radarStatusSummary = computed(() => {
  const radar = realtimeRadar.value;
  if (!radar) {
    return "blocked · scan proof latest 未加载";
  }
  const age = radar.age_seconds === null ? "age n/a" : `${radar.age_seconds}s`;
  return `${radar.status} · once=${radar.scan_once_observed ? "yes" : "no"} · hz=${radar.scan_hz_observed ? "yes" : "no"} · ${radar.artifact_status}/${radar.freshness_status}/${age}`;
});

const mapStatusSummary = computed(() => {
  const map = realtimeMap.value;
  if (!map) {
    return "waiting_for_radar · map contract 未加载";
  }
  if (map.status === "waiting_for_radar") {
    return "waiting_for_radar · 先等待真实 /scan once+hz";
  }
  if (map.status === "waiting_for_mapping") {
    return `waiting_for_mapping · map=${map.map_artifact_status} · slam=${map.slam_artifact_status}`;
  }
  return `ready · map=${map.map_artifact_status} · slam=${map.slam_artifact_status}`;
});

const mapTopBlockers = computed(() => {
  // 地图 blocker 与雷达 blocker 分开显示，避免重新出现“雷达/建图”合并口径。
  const blockers = realtimeMap.value?.blocked_reasons ?? ["realtime_radar_not_ready"];
  return blockers.slice(0, 3);
});

const scanProofLatest = computed(() => {
  // scan proof 来自 8787 统一 status 的 artifact readback；PC 不执行 collector 或串口读取。
  return props.liveOperatorPanel?.lidar_radar.scan_proof_latest ?? null;
});

const scanProofSummary = computed(() => {
  const proof = scanProofLatest.value;
  if (!proof) {
    return "scan proof latest 未加载";
  }
  const age = proof.age_seconds === null ? "age n/a" : `${proof.age_seconds}s`;
  return `${proof.artifact_status} · ${proof.freshness_status} · ${age} · ${proof.latest_proof_status}`;
});

const scanProofTopBlockers = computed(() => {
  // 只显示前 3 个 blocker，避免现场长 blocker 列表挤压操作区。
  const blockers = realtimeRadar.value?.blocked_reasons ?? scanProofLatest.value?.blocked_reasons ?? ["radar_scan_proof_latest_not_loaded"];
  return blockers.slice(0, 3);
});

const rawPacketProofLatest = computed(() => {
  // raw packet proof 同样来自 8787 status 摘要；前端不能自己推断或触发 LiDAR 串口采集。
  return props.liveOperatorPanel?.lidar_radar.raw_packet_proof_latest ?? null;
});

const rawPacketProofSummary = computed(() => {
  const proof = rawPacketProofLatest.value;
  if (!proof) {
    return "raw packet proof latest 未加载";
  }
  const age = proof.age_seconds === null ? "age n/a" : `${proof.age_seconds}s`;
  return `${proof.artifact_status} · ${proof.freshness_status} · ${age} · ${proof.latest_proof_status}`;
});

const rawPacketProofStats = computed(() => {
  const proof = rawPacketProofLatest.value;
  if (!proof) {
    return ["bytes n/a", "sync n/a", "packets n/a", "points n/a"];
  }
  // 这些数字只代表 latest artifact 摘要，不代表 ROS2 /scan 已连续可用。
  return [
    `bytes ${proof.latest_bytes_read ?? "n/a"}`,
    `sync ${proof.latest_sync_header_count ?? "n/a"}`,
    `packets ${proof.latest_packets_parse_ok ?? "n/a"}`,
    `points ${proof.latest_points_total ?? "n/a"}`,
  ];
});

watch(
  () => props.liveOperatorPanel?.control.speed.default_value,
  (defaultSpeed) => {
    // 速度默认值来自后端合同；未加载时保守回到 0.2m/s 视觉占位。
    speed.value = typeof defaultSpeed === "number" ? defaultSpeed : 0.2;
  },
  { immediate: true },
);

async function refreshCameraSmoke(): Promise<void> {
  // 首屏只读健康摘要，不自动创建 WebRTC peer，避免已有 active peer 时触发 409 噪声。
  cameraLoading.value = true;
  cameraError.value = "";
  try {
    cameraSmoke.value = await getO7LocalWebrtcCamera();
    if (cameraPreviewStatus.value === "idle") {
      cameraPreviewMessage.value =
        cameraSmoke.value.status === "ready"
          ? "摄像头已就绪，点击重新连接预览"
          : "摄像头服务未 ready，保留打开摄像头页面入口";
    }
  } catch (error) {
    // 摄像头失败只影响预览，不影响底盘 fail-closed 锁定策略。
    cameraError.value = error instanceof Error ? error.message : "camera_status_unavailable";
    cameraPreviewStatus.value = "failed";
    cameraPreviewMessage.value = "摄像头状态暂不可读";
  } finally {
    cameraLoading.value = false;
  }
}

async function refreshDirectUpperStatus(): Promise<void> {
  // 该入口只读 PC 本机 direct status；不会触发 stop/manual，也不会绕过后端 guardrail。
  directUpperLoading.value = true;
  directUpperError.value = "";
  try {
    directUpperStatus.value = await getO7DirectUpperStatus();
  } catch (error) {
    directUpperError.value = error instanceof Error ? error.message : "direct_upper_status_unavailable";
  } finally {
    directUpperLoading.value = false;
  }
}

async function waitForIceGatheringComplete(peerConnection: RTCPeerConnection): Promise<void> {
  // aiortc 服务端需要完整 SDP candidate；等待 ICE complete 可以提高首帧成功率。
  if (peerConnection.iceGatheringState === "complete") {
    return;
  }
  await new Promise<void>((resolve) => {
    const timeout = window.setTimeout(() => {
      peerConnection.removeEventListener("icegatheringstatechange", onChange);
      resolve();
    }, 2500);
    function onChange(): void {
      if (peerConnection.iceGatheringState === "complete") {
        window.clearTimeout(timeout);
        peerConnection.removeEventListener("icegatheringstatechange", onChange);
        resolve();
      }
    }
    peerConnection.addEventListener("icegatheringstatechange", onChange);
  });
}

async function closeRemoteCameraPeer(reason: string): Promise<void> {
  const peerId = cameraPeerId.value;
  if (!peerId) {
    return;
  }
  cameraPeerId.value = null;
  try {
    // close peer 只清理 8088 摄像头媒体 session，不发送机器人控制或 ROS2 指令。
    await fetch(`/api/o7/local-webrtc-camera/peers/${peerId}/close`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    });
  } catch {
    // 页面卸载或网络抖动时不能阻塞本地资源释放。
  }
}

async function stopCameraPreview(reason = "manual_stop"): Promise<void> {
  // 停止预览只关闭 WebRTC media peer 和本地 track，不触碰底盘安全锁。
  await closeRemoteCameraPeer(reason);
  if (cameraPeerConnection) {
    cameraPeerConnection.getReceivers().forEach((receiver) => receiver.track?.stop());
    cameraPeerConnection.getSenders().forEach((sender) => sender.track?.stop());
    cameraPeerConnection.close();
    cameraPeerConnection = null;
  }
  if (cameraVideo.value) {
    cameraVideo.value.srcObject = null;
  }
  cameraPreviewStatus.value = "idle";
  cameraPreviewMessage.value = "摄像头已就绪，可重新连接预览";
}

async function startCameraPreview(): Promise<void> {
  if (cameraPreviewStatus.value === "connecting" || cameraPreviewStatus.value === "playing") {
    return;
  }
  if (cameraSmoke.value?.status !== "ready") {
    cameraPreviewStatus.value = "failed";
    cameraPreviewMessage.value = "摄像头服务未 ready";
    return;
  }
  await stopCameraPreview("restart_before_new_offer");
  cameraPreviewStatus.value = "connecting";
  cameraPreviewMessage.value = "正在连接上位机摄像头";
  try {
    const peerConnection = new RTCPeerConnection({ iceServers: [] });
    cameraPeerConnection = peerConnection;
    peerConnection.addTransceiver("video", { direction: "recvonly" });
    peerConnection.ontrack = (event) => {
      // aiortc 可能返回 streamless track；此处补 MediaStream 保证 video 能播放。
      const stream = event.streams[0] ?? new MediaStream([event.track]);
      if (cameraVideo.value) {
        cameraVideo.value.srcObject = stream;
        void cameraVideo.value.play();
      }
      cameraPreviewStatus.value = "playing";
      cameraPreviewMessage.value = "摄像头画面已连接";
    };
    peerConnection.onconnectionstatechange = () => {
      if (["failed", "disconnected", "closed"].includes(peerConnection.connectionState)) {
        cameraPreviewStatus.value = cameraPreviewStatus.value === "playing" ? "idle" : "failed";
        cameraPreviewMessage.value = `连接状态：${peerConnection.connectionState}`;
      }
    };

    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    await waitForIceGatheringComplete(peerConnection);
    const response = await fetch("/api/o7/local-webrtc-camera/offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(peerConnection.localDescription),
    });
    const payload = (await response.json().catch(() => ({ error: `offer_${response.status}` }))) as CameraOfferAnswerPayload;
    if (!response.ok) {
      const reason = payload.error || `offer_${response.status}`;
      const readableReason =
        response.status === 409
          ? "摄像头已有预览连接，关闭其他页面或稍后再点重新连接预览"
          : reason;
      throw new Error(readableReason);
    }
    cameraPeerId.value = payload.peer_id ?? null;
    await peerConnection.setRemoteDescription(payload);
  } catch (error) {
    await stopCameraPreview("preview_start_failed");
    cameraPreviewStatus.value = "failed";
    cameraPreviewMessage.value = error instanceof Error ? error.message : "camera_preview_failed";
  }
}

function commandResultMessage(action: string, result: O7DirectUpperApiCommandResponse): string {
  // 返回文案同时呈现“已转发”和“仍未闭环”，避免 operator 把 HTTP 200 误解成 HIL/ACK 通过。
  const request = result.upper_request;
  const http = request.http_status === null ? "HTTP n/a" : `HTTP ${request.http_status}`;
  const ack = result.robot_ack_connected ? "ACK observed" : "ACK not observed";
  const t1001 = result.t1001_observed ? "T=1001 observed" : "T=1001 not observed";
  const blockers = result.blocked_reasons.length ? result.blocked_reasons.join(" / ") : "none";
  const evidence = result.command_payload_summary.evidence_ref ?? operatorEvidenceRefValue.value;
  const adapter = result.adapter?.version ?? "missing_adapter_stale_dev_server";
  const source = result.upper_api_base_url_source ?? "missing_source";
  if (result.upper_api_base_url_source === "fixture" && result.accepted_by_workstation) {
    return `${action} fixture 已记录（仍锁定）：${request.path}；source=${source}；adapter=${adapter}；evidence_ref=${evidence}；${ack} / ${t1001}；锁定原因 ${blockers}；safe_to_control=false`;
  }
  if (result.accepted_by_workstation && request.ok) {
    return `${action} 已发送（仍锁定）：${request.path} ${http}；source=${source}；adapter=${adapter}；evidence_ref=${evidence}；${ack} / ${t1001}；锁定原因 ${blockers}；safe_to_control=false`;
  }
  const reason = result.failure_reason || request.failure_reason || "manual_request_failed";
  return `${action} 失败：${reason}；${request.path} ${request.executed ? http : "not_executed"}；direct status ${
    directUpperStatus.value?.status ?? "unknown"
  }；source=${source}；adapter=${adapter}；evidence_ref=${evidence}；锁定原因 ${blockers}；safe_to_control=false`;
}

function isEditableControlTarget(target: EventTarget | null): boolean {
  // 键盘遥控只服务空白页面焦点；输入框、滑条和可编辑区域必须保留原生键盘行为。
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  return Boolean(target.closest('input, textarea, select, [contenteditable="true"], [role="textbox"]'));
}

function manualPulseForDirection(direction: O7LiveOperatorDirection): { speedMps: number; durationMs: number } {
  // 左右转现场感知偏弱，因此 UI 层主动请求更长 turn pulse；真实上限仍由 PC 后端和 8787 guardrail clamp。
  if (direction === "left" || direction === "right") {
    return { speedMps: TURN_PULSE_SPEED_MPS, durationMs: TURN_PULSE_DURATION_MS };
  }
  if (direction === "stop") {
    return { speedMps: 0, durationMs: STRAIGHT_PULSE_DURATION_MS };
  }
  return { speedMps: speed.value, durationMs: STRAIGHT_PULSE_DURATION_MS };
}

function ensureOperatorConfirmed(action: string): boolean {
  // 所有会触发 real/fixture 控制面的按钮和键盘快捷键都必须经过同一个人工确认门。
  if (!operatorConfirmed.value) {
    lockMessage.value = `${action} 未发送：请先勾选 operator confirmation；evidence_ref=${operatorEvidenceRefValue.value}；safe_to_control=false`;
    return false;
  }
  return true;
}

async function sendManualControl(direction: O7LiveOperatorDirection): Promise<void> {
  // 方向按钮只调用 PC 同源 direct-upper manual 代理；浏览器不直连 8787、不发 /cmd_vel、不构造 WAVE ROVER JSON。
  const action = directionLabels[direction];
  if (!ensureOperatorConfirmed(action)) {
    return;
  }
  if (manualCommandInFlight.value) {
    lockMessage.value = `${action} 未发送：上一条 ${directionLabels[manualCommandInFlight.value]} 仍在等待；safe_to_control=false`;
    return;
  }
  manualCommandInFlight.value = direction;
  const pulse = manualPulseForDirection(direction);
  lockMessage.value = `${action} 发送中：通过 PC 同源 /api/o7/direct-upper/base/manual；safe_to_control=false`;
  try {
    const result = await postO7DirectUpperManual(
      direction,
      pulse.speedMps,
      pulse.durationMs,
      operatorEvidenceRefValue.value,
      fixtureMode.value,
    );
    lockMessage.value = commandResultMessage(action, result);
    await refreshDirectUpperStatus();
  } catch (error) {
    const reason = error instanceof Error ? error.message : "manual_request_failed";
    lockMessage.value = `${action} 失败：${reason}；只调用 PC 同源 direct-upper manual；safe_to_control=false`;
  } finally {
    manualCommandInFlight.value = null;
  }
}

async function sendStopControl(): Promise<void> {
  // Stop 走独立 /api/base/stop 代理；它是安全护栏，不复用 manual stop 的短 pulse 语义。
  if (!ensureOperatorConfirmed("Stop")) {
    return;
  }
  if (operatorCommandInFlight.value || manualCommandInFlight.value) {
    lockMessage.value = "Stop 未发送：仍有上一条控制请求在等待；safe_to_control=false";
    return;
  }
  operatorCommandInFlight.value = "stop";
  lockMessage.value = "Stop 发送中：通过 PC 同源 /api/o7/direct-upper/base/stop；safe_to_control=false";
  try {
    const result = await postO7DirectUpperStop(operatorEvidenceRefValue.value, fixtureMode.value);
    lockMessage.value = commandResultMessage("Stop", result);
    await refreshDirectUpperStatus();
  } catch (error) {
    const reason = error instanceof Error ? error.message : "stop_request_failed";
    lockMessage.value = `Stop 失败：${reason}；只调用 PC 同源 direct-upper stop；safe_to_control=false`;
  } finally {
    operatorCommandInFlight.value = null;
  }
}

async function sendOperatorControl(control: (typeof operatorControls.value)[number]): Promise<void> {
  // 雷达/建图/定位按钮只调用 PC 同源代理；浏览器不直连 8787，也不发布 ROS2 service/action。
  if (!ensureOperatorConfirmed(control.label)) {
    return;
  }
  if (operatorCommandInFlight.value || manualCommandInFlight.value) {
    lockMessage.value = `${control.label} 未发送：上一条请求仍在等待；safe_to_control=false`;
    return;
  }
  operatorCommandInFlight.value = control.id;
  lockMessage.value = `${control.label} 发送中：evidence_ref=${operatorEvidenceRefValue.value}；safe_to_control=false`;
  try {
    const result = await postO7DirectUpperOperatorCommand(control.kind, {
      ...control.payload,
      evidence_ref: operatorEvidenceRefValue.value,
      fixture_mode: fixtureMode.value,
    });
    lockMessage.value = commandResultMessage(control.label, result);
    await refreshDirectUpperStatus();
  } catch (error) {
    const reason = error instanceof Error ? error.message : `${control.id}_request_failed`;
    lockMessage.value = `${control.label} 失败：${reason}；只调用 PC 同源 direct-upper 代理；safe_to_control=false`;
  } finally {
    operatorCommandInFlight.value = null;
  }
}

async function sendOperatorReport(): Promise<void> {
  // operator report 必须携带 evidence_ref，作为人工现场材料引用；它不是机器人 ACK。
  if (!ensureOperatorConfirmed("Operator report")) {
    return;
  }
  if (operatorCommandInFlight.value || manualCommandInFlight.value) {
    lockMessage.value = "Operator report 未发送：上一条请求仍在等待；safe_to_control=false";
    return;
  }
  operatorCommandInFlight.value = "operator_report";
  lockMessage.value = `Operator report 发送中：evidence_ref=${operatorEvidenceRefValue.value}；safe_to_control=false`;
  try {
    const result = await postO7DirectUpperOperatorCommand("operator_report", {
      evidence_ref: operatorEvidenceRefValue.value,
      note: operatorReportNote.value,
      fixture_mode: fixtureMode.value,
    });
    lockMessage.value = commandResultMessage("Operator report", result);
    await refreshDirectUpperStatus();
  } catch (error) {
    const reason = error instanceof Error ? error.message : "operator_report_failed";
    lockMessage.value = `Operator report 失败：${reason}；没有报告不得把现场链路写成完成；safe_to_control=false`;
  } finally {
    operatorCommandInFlight.value = null;
  }
}

function handleManualKeydown(event: KeyboardEvent): void {
  // repeat keydown 会把短 pulse 变成长按连续命令；现场遥控先保持一次按键一次请求。
  if (event.repeat || isEditableControlTarget(event.target)) {
    return;
  }
  const direction = KEYBOARD_DIRECTIONS[event.key.toLowerCase()] ?? (event.code === "Space" ? "stop" : null);
  if (!direction) {
    return;
  }
  event.preventDefault();
  void sendManualControl(direction);
}

onMounted(() => {
  // 首屏只读 camera/direct 状态；offer 与 manual 都必须由用户按钮触发。
  window.addEventListener("keydown", handleManualKeydown);
  void refreshCameraSmoke();
  void refreshDirectUpperStatus();
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleManualKeydown);
  void stopCameraPreview("component_unmount");
});
</script>

<template>
  <section class="user-console-grid" aria-label="Rober 用户控制台">
    <article class="console-card preview-card" aria-label="预览">
      <div class="card-heading">
        <span class="card-icon">●</span>
        <div>
          <p class="console-kicker">预览</p>
          <h2>摄像头入口</h2>
        </div>
      </div>
      <div class="camera-window" :class="`camera-window-${cameraPreviewStatus}`">
        <video ref="cameraVideo" class="camera-video" autoplay playsinline muted aria-label="上位机摄像头实时预览" />
        <div v-if="cameraPreviewStatus !== 'playing'" class="camera-placeholder">
          <span class="camera-dot" />
          <strong>{{ cameraStatusText }}</strong>
          <small>{{ cameraSource }} · {{ cameraPreviewTone }}</small>
        </div>
      </div>
      <div class="camera-actions">
        <button type="button" class="primary-link" @click="startCameraPreview">重新连接预览</button>
        <a class="primary-link secondary-link" :href="cameraUrl" target="_blank" rel="noreferrer">打开摄像头页面</a>
      </div>
      <p class="camera-message" role="status">{{ cameraPreviewMessage }}</p>
      <p v-if="cameraError" class="subtle-warning">摄像头状态暂不可读：{{ cameraError }}</p>
    </article>

    <article class="console-card radar-card" aria-label="实时雷达 /scan">
      <div class="card-heading">
        <span class="card-icon">⌁</span>
        <div>
          <p class="console-kicker">雷达</p>
          <h2>实时雷达 (/scan)</h2>
        </div>
      </div>
      <div class="scan-proof-box" aria-label="实时雷达 /scan 状态">
        <div class="status-light-row">
          <span
            class="status-dot"
            :class="realtimeRadar?.ready ? 'status-dot-green' : 'status-dot-yellow'"
          />
          <span>/scan readiness</span>
          <strong>{{ radarStatusSummary }}</strong>
        </div>
        <div class="endpoint-list compact-endpoints" aria-label="实时雷达 blockers">
          <code v-for="blocker in scanProofTopBlockers" :key="blocker">{{ blocker }}</code>
        </div>
        <p class="base-boundary">
          只认 `/scan` once+hz；raw packet proof 不参与雷达 ready 判定。
        </p>
      </div>
      <details class="lock-details diagnostics-details">
        <summary>诊断详情/工程材料</summary>
        <p>{{ scanProofSummary }}</p>
        <div class="endpoint-list compact-endpoints" aria-label="LiDAR raw packet proof statistics">
          <code v-for="stat in rawPacketProofStats" :key="stat">{{ stat }}</code>
        </div>
        <p class="base-boundary">
          Raw packet proof: {{ rawPacketProofSummary }} · {{ rawPacketProofLatest?.endpoint || "/api/radar/raw-packet-proof/latest" }} · safe_to_control=false。
        </p>
      </details>
    </article>

    <article class="console-card map-card" aria-label="实时图 SLAM map">
      <div class="card-heading">
        <span class="card-icon">□</span>
        <div>
          <p class="console-kicker">地图</p>
          <h2>实时图 (SLAM/map)</h2>
        </div>
      </div>
      <div class="simple-map" aria-label="SLAM/map 等待状态占位">
        <span class="route-path" />
        <span class="route-node home" />
        <span class="route-node robot" />
        <span class="route-node dock" />
      </div>
      <p class="muted-copy">{{ mapStatusSummary }}</p>
      <div class="scan-proof-box" aria-label="SLAM map 状态">
        <div class="status-light-row">
          <span
            class="status-dot"
            :class="realtimeMap?.ready ? 'status-dot-green' : 'status-dot-yellow'"
          />
          <span>SLAM/map</span>
          <strong>{{ realtimeMap?.status || "waiting_for_radar" }}</strong>
        </div>
        <div class="endpoint-list compact-endpoints" aria-label="SLAM map blockers">
          <code v-for="blocker in mapTopBlockers" :key="blocker">{{ blocker }}</code>
        </div>
        <p class="base-boundary">
          pointcloud_fabricated=false · 没有 map/SLAM artifact 时保持 waiting_for_mapping。
        </p>
      </div>
    </article>

    <article class="console-card control-card" aria-label="操控">
      <div class="card-heading">
        <span class="card-icon">◆</span>
        <div>
          <p class="console-kicker">操控</p>
          <h2>遥控器</h2>
        </div>
      </div>
      <div class="remote-pad" aria-label="方向控制">
        <button type="button" class="pad-button forward" :disabled="Boolean(manualCommandInFlight)" @click="sendManualControl('forward')">前进</button>
        <button type="button" class="pad-button left" :disabled="Boolean(manualCommandInFlight)" @click="sendManualControl('left')">左转</button>
        <button type="button" class="pad-button stop" :disabled="Boolean(manualCommandInFlight || operatorCommandInFlight)" @click="sendStopControl">Stop</button>
        <button type="button" class="pad-button right" :disabled="Boolean(manualCommandInFlight)" @click="sendManualControl('right')">右转</button>
        <button type="button" class="pad-button back" :disabled="Boolean(manualCommandInFlight)" @click="sendManualControl('back')">后退</button>
      </div>
      <label class="speed-control">
        <span>速度 {{ speed.toFixed(2) }} {{ liveOperatorPanel?.control.speed.unit ?? "m/s" }}</span>
        <input
          v-model.number="speed"
          type="range"
          :min="liveOperatorPanel?.control.speed.min ?? 0"
          :max="liveOperatorPanel?.control.speed.max ?? 0.5"
          :step="liveOperatorPanel?.control.speed.step ?? 0.05"
          aria-label="速度"
        >
      </label>
      <p class="lock-message" role="status">{{ lockMessage }}</p>
      <p class="base-boundary">{{ baseBoundaryText }}</p>
      <details class="lock-details">
        <summary>详情</summary>
        <p>{{ controlDetails }}</p>
      </details>
    </article>

    <article class="console-card operator-workflow-card" aria-label="Upper API operator workflow">
      <div class="card-heading">
        <span class="card-icon">⇄</span>
        <div>
          <p class="console-kicker">Upper API</p>
          <h2>雷达 / 建图 / 定位</h2>
        </div>
      </div>
      <div class="operator-fields">
        <label>
          <span>evidence_ref</span>
          <input v-model="operatorEvidenceRef" type="text" aria-label="operator evidence ref">
        </label>
        <label>
          <span>map_id</span>
          <input v-model="mapId" type="text" aria-label="map id">
        </label>
      </div>
      <div class="operator-guard-row" aria-label="operator mode and confirmation">
        <label class="operator-toggle">
          <input v-model="fixtureMode" type="checkbox" aria-label="fixture mode">
          <span>fixture mode</span>
        </label>
        <label class="operator-toggle confirmation-toggle">
          <input v-model="operatorConfirmed" type="checkbox" aria-label="operator confirmation">
          <span>operator confirmation</span>
        </label>
      </div>
      <div class="operator-control-grid" aria-label="8787 upper API controls">
        <button
          v-for="control in operatorControls"
          :key="control.id"
          type="button"
          class="primary-link operator-button"
          :disabled="Boolean(operatorCommandInFlight || manualCommandInFlight)"
          @click="sendOperatorControl(control)"
        >
          {{ control.label }}
        </button>
      </div>
      <label class="operator-report-field">
        <span>operator report note</span>
        <textarea v-model="operatorReportNote" rows="2" aria-label="operator report note" />
      </label>
      <button
        type="button"
        class="primary-link operator-button"
        :disabled="Boolean(operatorCommandInFlight || manualCommandInFlight)"
        @click="sendOperatorReport"
      >
        Report evidence ref
      </button>
      <p class="base-boundary">
        {{ operatorModeSummary }} · {{ directUpperEvidenceSummary }} · blocked/not_proven 由 8787 与 PC 代理返回，UI 不直连 ROS graph。
      </p>
    </article>

    <article class="console-card status-card" aria-label="状态">
      <div class="card-heading">
        <span class="card-icon">◌</span>
        <div>
          <p class="console-kicker">状态</p>
          <h2>设备状态</h2>
        </div>
      </div>
      <div class="status-light-list">
        <div v-for="item in statusLights" :key="item.label" class="status-light-row">
          <span class="status-dot" :class="`status-dot-${item.tone}`" />
          <span>{{ item.label }}</span>
          <strong>{{ item.text }}</strong>
        </div>
      </div>
    </article>

    <article class="console-card direct-upper-card" aria-label="Direct upper mode">
      <div class="card-heading">
        <span class="card-icon">↔</span>
        <div>
          <p class="console-kicker">Direct</p>
          <h2>PC 本机 8787 接口</h2>
        </div>
      </div>
      <p class="muted-copy">{{ directUpperModeText }}</p>
      <p class="adapter-fingerprint">{{ directUpperAdapterSummary }}</p>
      <p v-if="directUpperStaleWarning" class="subtle-warning">{{ directUpperStaleWarning }}</p>
      <div class="status-light-list">
        <div class="status-light-row">
          <span class="status-dot" :class="directUpperStatus?.status === 'ready' ? 'status-dot-green' : 'status-dot-yellow'" />
          <span>Cloud relay</span>
          <strong>{{ directUpperStatus?.safety_flags.cloud_relay_bypassed ? "已绕过" : "未确认" }}</strong>
        </div>
        <div class="status-light-row">
          <span class="status-dot status-dot-red" />
          <span>ACK / T=1001</span>
          <strong>{{ directUpperStatus?.upper_status_summary.t1001_observed ? "observed" : "not observed" }}</strong>
        </div>
        <div class="status-light-row">
          <span class="status-dot status-dot-yellow" />
          <span>Scan proof</span>
          <strong>{{ directUpperStatus?.upper_status_summary.radar_scan_proof_latest_status || "not_loaded" }}</strong>
        </div>
        <div class="status-light-row">
          <span class="status-dot status-dot-yellow" />
          <span>Raw packet</span>
          <strong>{{ directUpperStatus?.upper_status_summary.radar_raw_packet_proof_latest_status || "not_loaded" }}</strong>
        </div>
      </div>
      <div class="endpoint-list" aria-label="本机 direct upper API 路径">
        <code v-for="path in directUpperPaths" :key="path">{{ path }}</code>
      </div>
      <p class="base-boundary">
        {{ directUpperStatus?.upper_api_base_url || "env ROBER_UPPER_API_BASE_URL required" }}
      </p>
    </article>
  </section>
</template>
