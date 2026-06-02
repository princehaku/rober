<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { O7LiveOperatorDirection, O7LiveOperatorPanelResponse } from "../shared/contracts";

const props = defineProps<{
  liveOperatorPanel: O7LiveOperatorPanelResponse | null;
}>();

const speed = ref(0.2);
const blockedMessage = ref("control_blocked_waiting_for_operator_action");

const directionLabels: Record<O7LiveOperatorDirection, string> = {
  forward: "Forward",
  back: "Back",
  left: "Left",
  right: "Right",
  stop: "Stop",
};

const blockedReasons = computed(() => props.liveOperatorPanel?.control.blocked_reasons ?? []);

watch(
  () => props.liveOperatorPanel?.control.speed.default_value,
  (defaultSpeed) => {
    // 速度默认值来自后端契约；接口未加载时保持本地安全默认，不创建真实控制状态。
    speed.value = typeof defaultSpeed === "number" ? defaultSpeed : 0.2;
  },
  { immediate: true },
);

function showBlocked(direction: O7LiveOperatorDirection): void {
  // 按钮只是 operator 反馈入口，不 fetch 控制 API，也不构造 cmd_vel 或底盘 JSON。
  blockedMessage.value = `${directionLabels[direction]} blocked: ${blockedReasons.value.join(", ") || "control_contract_not_loaded"}`;
}
</script>

<template>
  <section class="workspace live-operator-panel" aria-label="PC Live Operator">
    <div class="section-head">
      <div>
        <p class="eyebrow">O7 same-LAN operator surface · fail closed</p>
        <h2>PC Live Operator</h2>
      </div>
      <span class="pill danger">safe_to_control={{ liveOperatorPanel?.safe_to_control ?? false }}</span>
    </div>

    <div class="live-operator-grid">
      <article class="live-tile radar-tile">
        <div class="section-head compact-head">
          <div>
            <p class="eyebrow">LiDAR / Radar Signal</p>
            <h3>Signal Contract</h3>
          </div>
          <span class="pill danger">{{ liveOperatorPanel?.lidar_radar.scan_status ?? "not_loaded" }}</span>
        </div>
        <dl class="kv compact-kv">
          <dt>/dev/lidar</dt>
          <dd>{{ liveOperatorPanel?.lidar_radar.dev_lidar ?? "not_loaded" }}</dd>
          <dt>STC by-id</dt>
          <dd>{{ liveOperatorPanel?.lidar_radar.stc_by_id ?? "not_loaded" }}</dd>
          <dt>point cloud</dt>
          <dd>pointcloud_fabricated={{ liveOperatorPanel?.lidar_radar.pointcloud_fabricated ?? false }}</dd>
        </dl>
        <ul class="dense">
          <li v-for="fact in liveOperatorPanel?.lidar_radar.source_facts ?? []" :key="fact">{{ fact }}</li>
        </ul>
      </article>

      <article class="live-tile camera-tile">
        <div class="section-head compact-head">
          <div>
            <p class="eyebrow">Camera image entry</p>
            <h3>Camera Health</h3>
          </div>
          <span class="pill">{{ liveOperatorPanel?.camera.health_status ?? "not_loaded" }}</span>
        </div>
        <div class="camera-preview">
          <span>LAN camera page</span>
          <a :href="liveOperatorPanel?.camera.lan_page_url ?? '#'" target="_blank" rel="noreferrer">
            {{ liveOperatorPanel?.camera.base_url ?? "not_loaded" }}
          </a>
        </div>
        <dl class="kv compact-kv">
          <dt>video source</dt>
          <dd>{{ liveOperatorPanel?.camera.video_source ?? "not_loaded" }}</dd>
          <dt>auto offer</dt>
          <dd>offer_auto_post_enabled={{ liveOperatorPanel?.camera.offer_auto_post_enabled ?? false }}</dd>
          <dt>ssh</dt>
          <dd>
            {{ liveOperatorPanel?.ssh.host ?? "not_loaded" }}:{{ liveOperatorPanel?.ssh.port ?? "not_loaded" }}
            · reachable={{ liveOperatorPanel?.ssh.reachable ?? false }}
            · 8787={{ liveOperatorPanel?.ssh.workstation_api_8787_status ?? "not_loaded" }}
          </dd>
        </dl>
      </article>

      <article class="live-tile control-tile">
        <div class="section-head compact-head">
          <div>
            <p class="eyebrow">Manual control preview</p>
            <h3>Direction Controls</h3>
          </div>
          <span class="pill danger">dispatch={{ liveOperatorPanel?.control.command_dispatch_enabled ?? false }}</span>
        </div>
        <div class="speed-row">
          <label>
            <span>Speed</span>
            <input
              v-model.number="speed"
              type="range"
              :min="liveOperatorPanel?.control.speed.min ?? 0"
              :max="liveOperatorPanel?.control.speed.max ?? 0.5"
              :step="liveOperatorPanel?.control.speed.step ?? 0.05"
              aria-label="Live operator speed"
            >
          </label>
          <output>{{ speed.toFixed(2) }} {{ liveOperatorPanel?.control.speed.unit ?? "m/s" }}</output>
        </div>
        <div class="direction-pad" aria-label="Live operator direction controls">
          <button
            v-for="direction in liveOperatorPanel?.control.visible_directions ?? ['forward', 'back', 'left', 'right', 'stop']"
            :key="direction"
            class="secondary"
            type="button"
            @click="showBlocked(direction)"
          >
            {{ directionLabels[direction] }}
          </button>
        </div>
        <p class="blocked-copy" role="status">{{ blockedMessage }}</p>
        <dl class="kv compact-kv">
          <dt>sends commands</dt>
          <dd>sends_commands={{ liveOperatorPanel?.control.sends_commands ?? false }}</dd>
          <dt>robot ACK</dt>
          <dd>robot_ack_connected={{ liveOperatorPanel?.control.robot_ack_connected ?? false }}</dd>
        </dl>
      </article>
    </div>
  </section>
</template>
