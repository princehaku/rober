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
