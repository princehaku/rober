<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getO7LocalWebrtcCamera } from "../client/workstationApi";
import type { O7LocalWebrtcCameraResponse } from "../shared/contracts";

const cameraSmoke = ref<O7LocalWebrtcCameraResponse | null>(null);
const cameraError = ref("");
const cameraLoading = ref(true);

const dependencyCopy = computed(() => {
  // 依赖摘要来自后端 health.imports，前端只负责压缩展示，不补造 ready 状态。
  const summary = cameraSmoke.value?.dependency_summary ?? [];
  return summary.length ? summary.join(" · ") : "not_loaded";
});

const browserSmokeCopy = computed(() => {
  // 浏览器 smoke 来自显式脚本产物；UI 只能展示证据摘要，不能触发 /offer。
  const smoke = cameraSmoke.value?.browser_smoke;
  if (!smoke) {
    return "not_loaded";
  }
  return [
    `executed_at=${smoke.executed_at}`,
    `first_frame=${smoke.first_frame_received}`,
    `size=${smoke.video_width ?? "null"}x${smoke.video_height ?? "null"}`,
    `first_frame_ms=${smoke.first_frame_ms ?? "null"}`,
  ].join(" · ");
});

const browserStatsCopy = computed(() => {
  // stats 是 smoke 脚本采集的只读浏览器证据，UI 只压缩展示定位线索。
  const smoke = cameraSmoke.value?.browser_smoke;
  const inbound = smoke?.inbound_video_stats?.[0];
  const pair = smoke?.selected_candidate_pair;
  return [
    `ontrack=${smoke?.ontrack_count ?? 0}`,
    `packets=${inbound?.packetsReceived ?? "null"}`,
    `frames_decoded=${inbound?.framesDecoded ?? "null"}`,
    `pair=${pair?.state ?? "null"}`,
  ].join(" · ");
});

const browserStabilityCopy = computed(() => {
  // stability 仍来自 operator 显式 smoke JSON，前端只展示证据，不自动播放摄像头。
  const stability = cameraSmoke.value?.browser_smoke.stability_summary;
  if (!stability) {
    return "not_loaded";
  }
  return [
    `status=${stability.status}`,
    `window_ms=${stability.observation_window_ms}`,
    `samples=${stability.sample_count}`,
    `fps=${stability.estimated_fps ?? "null"}`,
    `packet_rate=${stability.estimated_packet_rate ?? "null"}`,
  ].join(" · ");
});

const browserResourceCopy = computed(() => {
  // CPU/温度来自远端 /health 可选字段，缺失时显示 not_available 而不是判失败。
  const stability = cameraSmoke.value?.browser_smoke.stability_summary;
  return [
    `system_metrics=${stability?.remote_system_metrics === "not_available" ? "not_available" : "available"}`,
    `stability_metrics=${stability?.remote_stability_metrics === "not_available" ? "not_available" : "available"}`,
    `cleanup=${stability?.remote_active_peer_cleaned ?? "not_available"}`,
  ].join(" · ");
});

async function refreshCameraSmoke(): Promise<void> {
  // 刷新只读状态，不启动 /offer、不打开摄像头、不创建 WebRTC peer。
  cameraLoading.value = true;
  cameraError.value = "";
  try {
    cameraSmoke.value = await getO7LocalWebrtcCamera();
  } catch (error) {
    // API 自身不可用时也必须保留 fail-closed 文案，不能回落成浏览器直连 LAN smoke。
    cameraError.value = error instanceof Error ? error.message : "local_webrtc_camera_api_unavailable";
  } finally {
    cameraLoading.value = false;
  }
}

onMounted(() => {
  // O7 首页加载时自动取一次状态，让真实摄像头 smoke 的缺口直接可见。
  void refreshCameraSmoke();
});
</script>

<template>
  <article class="o7-side-board local-camera-card">
    <div class="section-head compact-head">
      <!-- 该卡只消费 LAN camera smoke 状态，不提供 start/stop/control 按钮。 -->
      <div>
        <p class="eyebrow">O7 Local Camera Smoke</p>
        <h3>LAN 摄像头 smoke 状态</h3>
      </div>
      <span class="pill danger">{{ cameraSmoke?.status ?? (cameraLoading ? "loading" : "fail_closed") }}</span>
    </div>

    <div v-if="cameraError" class="notice" role="alert">
      local camera API unavailable: {{ cameraError }} · safe_to_control=false
    </div>

    <dl class="kv compact-kv">
      <dt>schema</dt>
      <dd>{{ cameraSmoke?.remote_self_test_schema ?? "trashbot.local_webrtc_camera_offer_self_test.v1" }}</dd>
      <dt>host</dt>
      <dd>{{ cameraSmoke?.host ?? "not_loaded" }}</dd>
      <dt>base URL</dt>
      <dd>{{ cameraSmoke?.base_url ?? "not_loaded" }} · {{ cameraSmoke?.base_url_source ?? "not_loaded" }}</dd>
      <dt>video source</dt>
      <dd>{{ cameraSmoke?.video_source ?? "not_loaded" }}</dd>
      <dt>devices</dt>
      <dd>{{ cameraSmoke?.device_count ?? 0 }} · /devices={{ cameraSmoke?.devices_http_status ?? "null" }}</dd>
      <dt>dependencies</dt>
      <dd>{{ dependencyCopy }}</dd>
      <dt>safe boundary</dt>
      <dd>
        safe_to_control={{ cameraSmoke?.fixed_false_fields.safe_to_control ?? false }}
        · sends_commands={{ cameraSmoke?.fixed_false_fields.sends_commands ?? false }}
        · cloud_relay={{ cameraSmoke?.fixed_false_fields.cloud_relay ?? false }}
      </dd>
      <dt>offer</dt>
      <dd>
        offer_executed={{ cameraSmoke?.offer_executed ?? false }}
        · webrtc_session_created={{ cameraSmoke?.webrtc_session_created ?? false }}
      </dd>
      <dt>browser smoke</dt>
      <dd>
        {{ cameraSmoke?.browser_smoke.status ?? "not_loaded" }}
        · {{ browserSmokeCopy }}
      </dd>
      <dt>browser ICE</dt>
      <dd>
        connection={{ cameraSmoke?.browser_smoke.connection_state ?? "null" }}
        · ice={{ cameraSmoke?.browser_smoke.ice_connection_state ?? "null" }}
        · signaling={{ cameraSmoke?.browser_smoke.signaling_state ?? "null" }}
      </dd>
      <dt>browser failure</dt>
      <dd>
        category={{ cameraSmoke?.browser_smoke.failure_category ?? "not_loaded" }}
        · offer={{ cameraSmoke?.browser_smoke.offer_http_status ?? "null" }}
        · remote_peers={{ cameraSmoke?.browser_smoke.remote_active_peer_connections ?? "null" }}
      </dd>
      <dt>browser cleanup</dt>
      <dd>
        peer={{ cameraSmoke?.browser_smoke.server_peer_id ?? "null" }}
        · close={{ cameraSmoke?.browser_smoke.server_peer_close_status ?? "not_loaded" }}
        · ready={{ cameraSmoke?.browser_smoke.final_ready_state ?? "null" }}
      </dd>
      <dt>browser stats</dt>
      <dd>{{ browserStatsCopy }}</dd>
      <dt>stability</dt>
      <dd>{{ browserStabilityCopy }}</dd>
      <dt>resource metrics</dt>
      <dd>{{ browserResourceCopy }}</dd>
      <dt>stability health</dt>
      <dd>
        size={{ cameraSmoke?.browser_smoke.stability_summary.video_size_stable ?? "not_available" }}
        · connection={{ cameraSmoke?.browser_smoke.stability_summary.connection_remained_connected ?? "not_available" }}
        · ice={{ cameraSmoke?.browser_smoke.stability_summary.ice_remained_connected ?? "not_available" }}
      </dd>
      <dt>browser errors</dt>
      <dd>
        console={{ cameraSmoke?.browser_smoke.console_error_count ?? 0 }}
        · page={{ cameraSmoke?.browser_smoke.page_error_count ?? 0 }}
        · stability_console_delta={{ cameraSmoke?.browser_smoke.stability_summary.console_errors_added ?? 0 }}
        · stability_page_delta={{ cameraSmoke?.browser_smoke.stability_summary.page_errors_added ?? 0 }}
        · reason={{ cameraSmoke?.browser_smoke.blocked_reason ?? "not_loaded" }}
      </dd>
      <dt>browser report</dt>
      <dd>{{ cameraSmoke?.browser_smoke.report_path ?? "not_loaded" }}</dd>
      <dt>LAN page</dt>
      <dd>
        <a :href="cameraSmoke?.camera_page_url ?? 'http://192.168.1.11:8088/'" target="_blank" rel="noreferrer">
          {{ cameraSmoke?.camera_page_url ?? "http://192.168.1.11:8088/" }}
        </a>
      </dd>
    </dl>

    <h3>Blocked by</h3>
    <ul class="dense">
      <!-- blocked reasons 是机器可读 reason，便于现场复制到 sprint 证据。 -->
      <li v-for="reason in cameraSmoke?.blocked_reasons ?? ['local_camera_smoke_not_loaded']" :key="reason">
        {{ reason }}
      </li>
    </ul>
  </article>
</template>
