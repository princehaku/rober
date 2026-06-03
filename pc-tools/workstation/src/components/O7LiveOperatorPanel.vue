<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { getO7DirectUpperStatus, getO7LocalWebrtcCamera } from "../client/workstationApi";
import type {
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
    tone: props.liveOperatorPanel?.lidar_radar.scan_status === "not_proven" ? "gray" : "green",
    text: "未接入",
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
    ? [paths.status, paths.stop, paths.feedback_request, paths.manual]
    : [
        "/api/o7/direct-upper/status",
        "/api/o7/direct-upper/base/stop",
        "/api/o7/direct-upper/base/feedback-request",
        "/api/o7/direct-upper/base/manual",
      ];
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
  // 打开页面仍是用户显式动作；自动 offer 只走同源 PC API 的摄像头媒体预览路径。
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
  const blockers = scanProofLatest.value?.blocked_reasons ?? ["radar_scan_proof_latest_not_loaded"];
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
  // 首屏先读只读健康摘要；只有 ready 后才创建摄像头媒体 offer，不进入控制路径。
  cameraLoading.value = true;
  cameraError.value = "";
  try {
    cameraSmoke.value = await getO7LocalWebrtcCamera();
    if (cameraSmoke.value.status === "ready" && cameraPreviewStatus.value === "idle") {
      await startCameraPreview();
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
    const payload = (await response.json()) as CameraOfferAnswerPayload;
    if (!response.ok) {
      throw new Error(payload.error || `offer_${response.status}`);
    }
    cameraPeerId.value = payload.peer_id ?? null;
    await peerConnection.setRemoteDescription(payload);
  } catch (error) {
    await stopCameraPreview("preview_start_failed");
    cameraPreviewStatus.value = "failed";
    cameraPreviewMessage.value = error instanceof Error ? error.message : "camera_preview_failed";
  }
}

function showLocked(direction: O7LiveOperatorDirection): void {
  // 方向按钮只更新本地提示，不 fetch 控制 API、不发送 /cmd_vel、不构造 WAVE ROVER JSON。
  const action = directionLabels[direction];
  lockMessage.value = `${action} 已拦截：控制锁定，底盘串口/反馈/ACK 未确认`;
}

onMounted(() => {
  // 首屏可自动创建摄像头媒体预览；底盘控制仍保持 fail-closed。
  void refreshCameraSmoke();
  void refreshDirectUpperStatus();
});

onBeforeUnmount(() => {
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

    <article class="console-card map-card" aria-label="地图">
      <div class="card-heading">
        <span class="card-icon">⌁</span>
        <div>
          <p class="console-kicker">地图</p>
          <h2>雷达未接入 / 等待建图</h2>
        </div>
      </div>
      <div class="simple-map" aria-label="未接入雷达的地图占位">
        <span class="route-path" />
        <span class="route-node home" />
        <span class="route-node robot" />
        <span class="route-node dock" />
      </div>
      <p class="muted-copy">当前没有真实 LiDAR `/scan` 证据；这里仅显示路线占位和机器人位置占位。</p>
      <div class="scan-proof-box" aria-label="LiDAR scan proof 状态">
        <div class="status-light-row">
          <span
            class="status-dot"
            :class="scanProofLatest?.latest_scan_once_observed ? 'status-dot-green' : 'status-dot-yellow'"
          />
          <span>Scan proof</span>
          <strong>{{ scanProofSummary }}</strong>
        </div>
        <div class="endpoint-list compact-endpoints" aria-label="LiDAR scan proof blockers">
          <code v-for="blocker in scanProofTopBlockers" :key="blocker">{{ blocker }}</code>
        </div>
        <p class="base-boundary">
          只读 artifact 回放；PC 不启动 collector、不发送 A5 60、不执行底盘控制。
        </p>
      </div>
      <div class="scan-proof-box" aria-label="LiDAR raw packet proof 状态">
        <div class="status-light-row">
          <span
            class="status-dot"
            :class="rawPacketProofLatest?.latest_raw_bytes_observed ? 'status-dot-green' : 'status-dot-yellow'"
          />
          <span>Raw packet proof</span>
          <strong>{{ rawPacketProofSummary }}</strong>
        </div>
        <div class="endpoint-list compact-endpoints" aria-label="LiDAR raw packet proof statistics">
          <code v-for="stat in rawPacketProofStats" :key="stat">{{ stat }}</code>
        </div>
        <p class="base-boundary">
          {{ rawPacketProofLatest?.endpoint || "/api/radar/raw-packet-proof/latest" }} · 只读材料；safe_to_control=false。
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
        <button type="button" class="pad-button forward" @click="showLocked('forward')">前进</button>
        <button type="button" class="pad-button left" @click="showLocked('left')">左转</button>
        <button type="button" class="pad-button stop" @click="showLocked('stop')">Stop</button>
        <button type="button" class="pad-button right" @click="showLocked('right')">右转</button>
        <button type="button" class="pad-button back" @click="showLocked('back')">后退</button>
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
