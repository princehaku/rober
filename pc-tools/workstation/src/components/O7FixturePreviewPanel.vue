<script setup lang="ts">
import { ref } from "vue";
import { loadO7FixturePreview } from "../client/workstationApi";
import type { O7FixturePreviewInputs, O7FixturePreviewKind, O7FixturePreviewResponses } from "../client/workstationApi";

type O7FixturePreviewResult = O7FixturePreviewResponses[O7FixturePreviewKind];

interface PreviewConfig {
  id: O7FixturePreviewKind;
  title: string;
  expectedSchema: string;
}

const previewConfigs: PreviewConfig[] = [
  // 五个入口均为 PC-only fixture preview，不映射成机器人动作。
  { id: "realtimeElevator", title: "Realtime/Elevator", expectedSchema: "trashbot.o7.realtime_elevator_preview.v1" },
  { id: "routeReplay", title: "Route Replay", expectedSchema: "trashbot.o7.route_replay_preview.v1" },
  { id: "labeling", title: "Labeling", expectedSchema: "trashbot.o7.labeling_preview.v1" },
  { id: "voice", title: "Voice", expectedSchema: "trashbot.o7.voice_preview.v1" },
  { id: "safeCommand", title: "Safe Command", expectedSchema: "trashbot.o7.safe_command_preview.v1" },
];

// 默认不加载任何本地路径，避免页面打开时读取 operator 工作站文件。
const inputs = ref<O7FixturePreviewInputs>({
  realtimeElevator: "",
  routeReplay: "",
  labeling: "",
  voice: "",
  safeCommand: "",
});

// 每个 preview 独立保存响应和错误，单个坏 fixture 不影响其他只读摘要。
const results = ref<Partial<O7FixturePreviewResponses>>({});
const errors = ref<Partial<Record<O7FixturePreviewKind, string>>>({});
const loading = ref<Partial<Record<O7FixturePreviewKind, boolean>>>({});

function asRecord(result: O7FixturePreviewResult | undefined): Record<string, unknown> {
  // Vue template 需要统一读取 union 字段；这里只做只读投影，不改响应内容。
  return result ? (result as unknown as Record<string, unknown>) : {};
}

function asStringArray(value: unknown): string[] {
  // 后端契约规定 blocked_reasons/not_proven 是数组；防御式处理避免坏响应撑爆 UI。
  return Array.isArray(value) ? value.map(String) : [];
}

function jsonSummary(value: unknown): string {
  // 摘要只展示后端已经脱敏的安全字段，不读取或展开原始 fixture。
  return JSON.stringify(value ?? "not_loaded", null, 2);
}

function inputStatus(result: O7FixturePreviewResult | undefined): string {
  const status = asRecord(result).input_status as { status?: string } | undefined;
  // 未点击 load 前保持 not_loaded，空路径加载后由后端返回 not_provided。
  return status?.status ?? "not_loaded";
}

function failureReason(result: O7FixturePreviewResult | undefined): string {
  const status = asRecord(result).input_status as { failure_reason?: string } | undefined;
  return status?.failure_reason ?? "fixture_json_not_provided";
}

function blockedReasons(result: O7FixturePreviewResult | undefined): string[] {
  return asStringArray(asRecord(result).blocked_reasons);
}

function notProven(result: O7FixturePreviewResult | undefined): string[] {
  return asStringArray(asRecord(result).not_proven);
}

function coreFalseFields(kind: O7FixturePreviewKind, result: O7FixturePreviewResult | undefined): string[] {
  const record = asRecord(result);
  // 这些字段是 operator 最容易误读成“已接通/可操作”的核心开关，必须显式展示 false。
  const common = [
    `safe_to_control=${String(record.safe_to_control ?? false)}`,
    `delivery_success=${String(record.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(record.primary_actions_enabled ?? false)}`,
    `pc_only=${String(record.pc_only ?? true)}`,
  ];
  if (kind === "realtimeElevator") {
    const route = record.route_membership_summary as { on_route?: false; in_elevator_zone?: false } | undefined;
    return [
      ...common,
      `real_realtime_api_connected=${String(record.real_realtime_api_connected ?? false)}`,
      `real_ros2_tf_connected=${String(record.real_ros2_tf_connected ?? false)}`,
      `latency_lt_2s_proven=${String(record.latency_lt_2s_proven ?? false)}`,
      `route_membership_summary.on_route=${String(route?.on_route ?? false)}`,
      `route_membership_summary.in_elevator_zone=${String(route?.in_elevator_zone ?? false)}`,
      `robot_control_executed=${String(record.robot_control_executed ?? false)}`,
    ];
  }
  if (kind === "routeReplay") {
    const cursor = record.playback_cursor_initial_state as { playing?: false; safe_to_play?: false } | undefined;
    return [
      ...common,
      `real_cloud_archive_connected=${String(record.real_cloud_archive_connected ?? false)}`,
      `playback_cursor_initial_state.playing=${String(cursor?.playing ?? false)}`,
      `playback_cursor_initial_state.safe_to_play=${String(cursor?.safe_to_play ?? false)}`,
      `robot_control_executed=${String(record.robot_control_executed ?? false)}`,
    ];
  }
  if (kind === "labeling") {
    return [
      ...common,
      `real_annotation_api_connected=${String(record.real_annotation_api_connected ?? false)}`,
      `submit_enabled=${String(record.submit_enabled ?? false)}`,
      `rollback_enabled=${String(record.rollback_enabled ?? false)}`,
      `dataset_export_available=${String(record.dataset_export_available ?? false)}`,
      `robot_control_executed=${String(record.robot_control_executed ?? false)}`,
    ];
  }
  if (kind === "voice") {
    return [
      ...common,
      `real_voice_api_connected=${String(record.real_voice_api_connected ?? false)}`,
      `real_asr_tts_runtime_connected=${String(record.real_asr_tts_runtime_connected ?? false)}`,
      `asr_stream_connected=${String(record.asr_stream_connected ?? false)}`,
      `tts_send_enabled=${String(record.tts_send_enabled ?? false)}`,
      `speaker_dispatch_enabled=${String(record.speaker_dispatch_enabled ?? false)}`,
      `robot_control_executed=${String(record.robot_control_executed ?? false)}`,
    ];
  }
  return [
    ...common,
    `command_dispatch_enabled=${String(record.command_dispatch_enabled ?? false)}`,
    `manual_control_enabled=${String(record.manual_control_enabled ?? false)}`,
    `navigate_goal_enabled=${String(record.navigate_goal_enabled ?? false)}`,
    `keyboard_control_enabled=${String(record.keyboard_control_enabled ?? false)}`,
    `real_command_api_connected=${String(record.real_command_api_connected ?? false)}`,
    `real_robot_ack_connected=${String(record.real_robot_ack_connected ?? false)}`,
    `robot_control_executed=${String(record.robot_control_executed ?? false)}`,
  ];
}

function summaryFields(kind: O7FixturePreviewKind, result: O7FixturePreviewResult | undefined): Array<[string, unknown]> {
  const record = asRecord(result);
  // 摘要挑选 contract 中已脱敏的低噪声字段，避免展示原始 JSON payload。
  if (kind === "realtimeElevator") {
    return [
      ["session", record.session],
      ["map_summary", record.map_summary],
      ["robot_pose_summary", record.robot_pose_summary],
      ["pose_freshness_summary", record.pose_freshness_summary],
      ["elevator_state_chain_summary", record.elevator_state_chain_summary],
    ];
  }
  if (kind === "routeReplay") {
    return [
      ["task", record.task],
      ["route_metadata", record.route_metadata],
      ["trajectory", record.trajectory],
      ["playback_cursor_initial_state", record.playback_cursor_initial_state],
      ["state_transitions", record.state_transitions],
    ];
  }
  if (kind === "labeling") {
    return [
      ["queue", record.queue],
      ["review_items", record.review_items],
      ["label_schema", record.label_schema],
      ["draft_labels", record.draft_labels],
      ["dataset_export", record.dataset_export],
    ];
  }
  if (kind === "voice") {
    return [
      ["voice_session", record.voice_session],
      ["asr_events", record.asr_events],
      ["tts_draft_summary", record.tts_draft_summary],
      ["speaker_dispatch_summary", record.speaker_dispatch_summary],
      ["media_preflight_dependency", record.media_preflight_dependency],
    ];
  }
  return [
    ["command_session", record.command_session],
    ["manual_turn_envelope_summary", record.manual_turn_envelope_summary],
    ["navigate_goal_envelope_summary", record.navigate_goal_envelope_summary],
    ["robot_ack_summary", record.robot_ack_summary],
    ["evidence_gaps", record.evidence_gaps],
  ];
}

async function loadPreview(kind: O7FixturePreviewKind): Promise<void> {
  // Load preview 只触发 GET preview API；即使路径为空，也由后端返回 fail-closed not_provided。
  loading.value[kind] = true;
  errors.value[kind] = "";
  try {
    results.value[kind] = await loadO7FixturePreview(kind, inputs.value[kind]);
  } catch (err) {
    errors.value[kind] = err instanceof Error ? err.message : "preview_api_unavailable_not_proven";
  } finally {
    loading.value[kind] = false;
  }
}
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <div>
        <h2>O7 Fixture Previews</h2>
        <p class="eyebrow">PC-only local JSON preview. No robot command, playback, submit, export, cancel or recovery action.</p>
      </div>
      <span class="pill danger">source=software_proof · proof_status=not_proven</span>
    </div>

    <div class="notice" role="note">
      These previews do not prove real realtime API, ROS2 /tf, cloud archive, annotation API, voice API, safe
      command API, robot ACK, HIL/hardware safety or delivery success.
    </div>

    <div class="route-inputs">
      <label v-for="config in previewConfigs" :key="config.id">
        <span>{{ config.title }} fixture JSON</span>
        <input
          v-model="inputs[config.id]"
          :aria-label="`${config.title} fixture JSON path`"
          placeholder="local fixture path, optional"
        >
        <button class="secondary" type="button" @click="loadPreview(config.id)">
          {{ loading[config.id] ? "Loading preview" : `Load ${config.title} preview` }}
        </button>
      </label>
    </div>

    <div class="snapshot-grid">
      <article v-for="config in previewConfigs" :key="config.id" class="snapshot-panel">
        <div class="section-head compact-head">
          <h3>{{ config.title }}</h3>
          <span class="pill danger">{{ results[config.id]?.preview_status ?? "not_loaded" }}</span>
        </div>

        <div v-if="errors[config.id]" class="notice" role="alert">
          {{ config.title }} preview API unavailable: {{ errors[config.id] }}. primary_actions_enabled=false.
        </div>

        <dl class="kv compact-kv">
          <dt>schema</dt>
          <dd>{{ results[config.id]?.schema ?? config.expectedSchema }}</dd>
          <dt>preview_status</dt>
          <dd>{{ results[config.id]?.preview_status ?? "not_loaded" }}</dd>
          <dt>input status</dt>
          <dd>{{ inputStatus(results[config.id]) }}</dd>
          <dt>failure reason</dt>
          <dd>{{ failureReason(results[config.id]) }}</dd>
          <dt>source fixture schema</dt>
          <dd>{{ results[config.id]?.source_fixture_schema ?? "not_loaded" }}</dd>
        </dl>

        <div class="two-col snapshot-grid">
          <div>
            <h3>Core false fields</h3>
            <ul class="dense">
              <!-- 核心 false 字段直接来自响应或响应缺省，防止 operator 把预览误读成真实能力。 -->
              <li v-for="field in coreFalseFields(config.id, results[config.id])" :key="field">{{ field }}</li>
            </ul>
          </div>
          <div>
            <h3>Blocked reasons</h3>
            <ul class="dense">
              <li v-for="reason in blockedReasons(results[config.id])" :key="reason">{{ reason }}</li>
              <li v-if="blockedReasons(results[config.id]).length === 0">fixture_json_not_provided</li>
            </ul>
          </div>
        </div>

        <h3>Summary fields</h3>
        <table>
          <thead>
            <tr>
              <th>field</th>
              <th>safe summary</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="[name, value] in summaryFields(config.id, results[config.id])" :key="name">
              <td>{{ name }}</td>
              <td>
                <code>{{ jsonSummary(value) }}</code>
              </td>
            </tr>
          </tbody>
        </table>

        <h3>Not proven</h3>
        <ul class="dense">
          <li v-for="item in notProven(results[config.id])" :key="item">{{ item }}</li>
          <li v-if="notProven(results[config.id]).length === 0">
            fixture_preview_not_loaded_and_real_runtime_not_proven
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>
