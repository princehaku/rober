<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  getO7ConsumerTaskDetail,
  getRobotControlSummary,
  postRobotControlCameraOffer,
  postRobotControlCameraPeerClose,
} from "../client/workstationApi";
import type { O7ConsumerTaskDetailResponse, RobotControlPreviewStatus, RobotControlSummaryResponse } from "../shared/contracts";

// 本组件仍然是 fail-closed 控制台；新增的 WebRTC 只负责观察视频，不负责任何运动控制。
const robotApiBaseUrl = ref("");
const o6ConsumerBaseUrl = ref("http://127.0.0.1:8088");
const taskId = ref("");
const fieldEvidenceManifestJson = ref("");
const loading = ref(false);
const error = ref("");
const robotSummary = ref<RobotControlSummaryResponse | null>(null);
const taskDetail = ref<O7ConsumerTaskDetailResponse | null>(null);

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
const previewVideo = ref<HTMLVideoElement | null>(null);
const previewStream = ref<MediaStream | null>(null);
const previewPeerConnection = ref<RTCPeerConnection | null>(null);
const previewStartPending = ref(false);
const previewStopPending = ref(false);
const sessionEpoch = ref(0);

const proofRows = computed(() => {
  // O3 proof 字段固定列出，缺字段也要显示 unknown，不能把缺失当作通过。
  const proof = robotSummary.value?.o3_proof_summary;
  return [
    ["managed_runtime_started", proof?.managed_runtime_started],
    ["scan_once_observed", proof?.scan_once_observed],
    ["map_once_observed", proof?.map_once_observed],
    ["amcl_pose_observed", proof?.amcl_pose_observed],
    ["localization_tf_observed", proof?.localization_tf_observed],
    ["planner_server_active", proof?.planner_server_active],
    ["path_generation_requested", proof?.path_generation_requested],
    ["path_generation_succeeded", proof?.path_generation_succeeded],
    ["path_generated", proof?.path_generated],
    ["path_point_count", proof?.path_point_count],
  ];
});

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

function display(value: unknown): string {
  // 展示层统一把 null/undefined 压成 unknown，避免模板里散落 fallback 逻辑。
  if (value === null || value === undefined) {
    return "unknown";
  }
  return String(value);
}

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
    <div class="section-head">
      <div>
        <p class="eyebrow">O7 Robot Control Console V1</p>
        <h2>Robot Control</h2>
      </div>
      <span class="pill danger">primary_actions_enabled=false</span>
    </div>

    <form class="robot-control-form" @submit.prevent="refreshConsole">
      <label>
        <span>task_id selector</span>
        <input v-model="taskId" name="task_id" placeholder="task_id">
      </label>
      <label>
        <span>Robot API base URL</span>
        <input v-model="robotApiBaseUrl" name="robotApiBaseUrl" placeholder="http://192.168.x.x:8787">
      </label>
      <label>
        <span>O6 consumer base URL</span>
        <input v-model="o6ConsumerBaseUrl" name="o6ConsumerBaseUrl" placeholder="http://127.0.0.1:8088">
      </label>
      <label>
        <span>Mock/field manifest JSON</span>
        <input v-model="fieldEvidenceManifestJson" name="fieldEvidenceManifestJson" placeholder="optional local JSON">
      </label>
      <button class="secondary" type="submit" :disabled="loading">Refresh control console</button>
    </form>

    <div v-if="error" class="notice" role="alert">
      {{ error }}; safe_to_control=false; delivery_success=false; primary_actions_enabled=false.
    </div>

    <div class="robot-console-grid">
      <article class="snapshot-panel">
        <h3>task_id selector</h3>
        <dl class="kv compact-kv">
          <dt>selected</dt>
          <dd>{{ selectedTaskSummary }}</dd>
          <dt>source</dt>
          <dd>{{ routeReplaySource }}</dd>
          <dt>task status</dt>
          <dd>{{ taskDetail?.task_summary?.task_status_summary ?? "blocked_not_loaded" }}</dd>
          <dt>safe_to_control</dt>
          <dd>false</dd>
          <dt>delivery_success</dt>
          <dd>false</dd>
        </dl>
      </article>

      <article class="snapshot-panel">
        <h3>Robot API connection</h3>
        <dl class="kv compact-kv">
          <dt>proxy</dt>
          <dd>Node server only; Vue direct access=false</dd>
          <dt>base URL</dt>
          <dd>{{ robotSummary?.normalized_base_url ?? "not_loaded" }}</dd>
          <dt>状态</dt>
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
      </article>

      <article class="snapshot-panel">
        <h3>Camera Preview</h3>
        <div class="locked-actions" aria-label="camera preview actions">
          <button type="button" :disabled="!canStartPreview" @click="startPreview">Start Preview</button>
          <button type="button" :disabled="!canStopPreview" @click="stopPreview">Stop Preview</button>
        </div>
        <video ref="previewVideo" autoplay muted playsinline />
        <dl class="kv compact-kv">
          <dt>preview_status</dt>
          <dd>{{ previewStatus }}</dd>
          <dt>failure_reason</dt>
          <dd>{{ failureReason || "none" }}</dd>
          <dt>peer_id</dt>
          <dd>{{ previewPeerId || "not_assigned" }}</dd>
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
        </dl>
        <p class="muted">
          camera_health={{ robotSummary?.readback_summary.camera.status ?? "not_loaded" }};
          devices={{ robotSummary?.readback_summary.camera.devices_status ?? "not_loaded" }};
          safe_to_control=false; delivery_success=false; primary_actions_enabled=false.
        </p>
      </article>

      <article class="snapshot-panel">
        <h3>O3 proof summary</h3>
        <table>
          <tbody>
            <tr v-for="[key, value] in proofRows" :key="key">
              <th>{{ key }}</th>
              <td>{{ display(value) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="muted">root_causes: {{ listText(robotSummary?.o3_proof_summary.root_causes) }}</p>
        <p class="muted">not_proven: {{ listText(robotSummary?.o3_proof_summary.not_proven) }}</p>
      </article>

      <article class="snapshot-panel">
        <h3>route replay / Mock fallback</h3>
        <dl class="kv compact-kv">
          <dt>source</dt>
          <dd>{{ routeReplaySource }}</dd>
          <dt>trajectory</dt>
          <dd>{{ taskDetail?.trajectory.status ?? "blocked_not_loaded" }} / frames={{ taskDetail?.trajectory.frame_count ?? 0 }}</dd>
          <dt>events</dt>
          <dd>{{ taskDetail?.events.status ?? "blocked_not_loaded" }} / count={{ taskDetail?.events.count ?? 0 }}</dd>
          <dt>tunnel</dt>
          <dd>{{ taskDetail?.tunnel_status.latest_known_status ?? "blocked_not_loaded" }}</dd>
          <dt>Mock</dt>
          <dd>{{ fieldEvidenceManifestJson ? "local_mock_or_field_manifest_visible" : "Mock fallback not selected" }}</dd>
        </dl>
      </article>

      <article class="snapshot-panel">
        <h3>evidence / keyframe / labeling readiness</h3>
        <dl class="kv compact-kv">
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
      </article>

      <article class="snapshot-panel">
        <h3>manual / nav safe command boundary</h3>
        <p class="muted">{{ robotSummary?.safe_command_boundary.locked_reason ?? "locked by V1 boundary" }}</p>
        <div class="locked-actions" aria-label="locked robot actions">
          <button disabled type="button">/api/base/manual locked</button>
          <button disabled type="button">cmd_vel locked</button>
          <button disabled type="button">Nav2 goal locked</button>
          <button disabled type="button">map start locked</button>
          <button disabled type="button">radar start locked</button>
          <button disabled type="button">keyboard control locked</button>
          <button disabled type="button">map click goal locked</button>
        </div>
        <p class="muted">
          command_dispatch_enabled=false; manual_control_enabled=false; navigate_goal_enabled=false;
          keyboard_control_enabled=false; robot_control_executed=false.
        </p>
      </article>

      <article class="snapshot-panel">
        <h3>Camera / LiDAR / Base readback</h3>
        <dl class="kv compact-kv">
          <dt>Camera</dt>
          <dd>
            /api/camera/health={{ robotSummary?.readback_summary.camera.status ?? "not_loaded" }},
            /api/camera/devices={{ robotSummary?.readback_summary.camera.devices_status ?? "not_loaded" }}
          </dd>
          <dt>LiDAR</dt>
          <dd>
            /api/radar/status={{ robotSummary?.readback_summary.lidar.status ?? "not_loaded" }},
            scan={{ robotSummary?.readback_summary.lidar.latest_scan_proof_status ?? "not_loaded" }},
            raw={{ robotSummary?.readback_summary.lidar.latest_raw_packet_proof_status ?? "not_loaded" }}
          </dd>
          <dt>Base</dt>
          <dd>
            /api/base/status={{ robotSummary?.readback_summary.base.status ?? "not_loaded" }},
            readback={{ robotSummary?.readback_summary.base.latest_feedback_status ?? "not_loaded" }}
          </dd>
          <dt>unsafe starts</dt>
          <dd>radar start=false; map start=false; base manual=false</dd>
        </dl>
      </article>
    </div>

    <section class="preflight-panel">
      <h3>Robot API readback endpoints</h3>
      <table>
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
  </section>
</template>
