<script setup lang="ts">
import { ref } from "vue";
import { getO7CloudArchiveTasks, loadO7FixturePreview } from "../client/workstationApi";
import type { O7FixturePreviewInputs, O7FixturePreviewKind, O7FixturePreviewResponses } from "../client/workstationApi";
import type { O7CloudArchiveTasksResponse } from "../shared/contracts";

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
const archiveJson = ref("");
const archiveResult = ref<O7CloudArchiveTasksResponse | null>(null);
const archiveError = ref("");
const archiveLoading = ref(false);

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

function archiveFalseFields(result: O7CloudArchiveTasksResponse | null): string[] {
  const fields = result?.fixed_false_fields;
  // archive 入口聚合 KR3-KR6 的危险开关，必须在 UI 中集中展示为 false。
  return [
    `real_cloud_archive_connected=${String(fields?.real_cloud_archive_connected ?? false)}`,
    `real_realtime_api_connected=${String(fields?.real_realtime_api_connected ?? false)}`,
    `real_annotation_api_connected=${String(fields?.real_annotation_api_connected ?? false)}`,
    `real_voice_api_connected=${String(fields?.real_voice_api_connected ?? false)}`,
    `real_command_api_connected=${String(fields?.real_command_api_connected ?? false)}`,
    `real_asr_tts_runtime_connected=${String(fields?.real_asr_tts_runtime_connected ?? false)}`,
    `asr_stream_connected=${String(fields?.asr_stream_connected ?? false)}`,
    `tts_send_enabled=${String(fields?.tts_send_enabled ?? false)}`,
    `speaker_dispatch_enabled=${String(fields?.speaker_dispatch_enabled ?? false)}`,
    `safe_to_control=${String(fields?.safe_to_control ?? false)}`,
    `delivery_success=${String(fields?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(fields?.primary_actions_enabled ?? false)}`,
    `pc_only=${String(fields?.pc_only ?? true)}`,
    `robot_control_executed=${String(fields?.robot_control_executed ?? false)}`,
  ];
}

function labelingFalseFields(result: O7CloudArchiveTasksResponse | null): string[] {
  const inspector = result?.labeling_queue_inspector;
  // 标注队列来自 archive fixture，但提交、回滚、导出和真实标注 API 必须继续由后端固定为 false。
  return [
    `submit_enabled=${String(inspector?.submit_enabled ?? false)}`,
    `rollback_enabled=${String(inspector?.rollback_enabled ?? false)}`,
    `dataset_export_available=${String(inspector?.dataset_export_available ?? false)}`,
    `real_annotation_api_connected=${String(inspector?.real_annotation_api_connected ?? false)}`,
    `draft_labels.autosave_available=${String(inspector?.draft_labels.autosave_available ?? false)}`,
    `dataset_export.available=${String(inspector?.dataset_export.available ?? false)}`,
  ];
}

function voiceFalseFields(result: O7CloudArchiveTasksResponse | null): string[] {
  const inspector = result?.voice_asr_tts_inspector;
  // KR5 语音检查只展示 archive 摘要，ASR stream、TTS 和喇叭链路都必须继续关闭。
  return [
    `asr_stream_connected=${String(inspector?.asr_stream_connected ?? false)}`,
    `tts_send_enabled=${String(inspector?.tts_send_enabled ?? false)}`,
    `speaker_dispatch_enabled=${String(inspector?.speaker_dispatch_enabled ?? false)}`,
    `real_voice_api_connected=${String(inspector?.real_voice_api_connected ?? false)}`,
    `real_asr_tts_runtime_connected=${String(inspector?.real_asr_tts_runtime_connected ?? false)}`,
    `speaker_dispatch.sends_to_robot=${String(inspector?.speaker_dispatch.sends_to_robot ?? false)}`,
  ];
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

function archiveBlockedReasons(): string[] {
  return archiveResult.value?.blocked_reasons ?? ["archive_json_not_provided"];
}

function archiveNotProven(): string[] {
  return archiveResult.value?.not_proven ?? ["archive_not_loaded_and_real_cloud_archive_not_proven"];
}

function inspectorCursorFields(result: O7CloudArchiveTasksResponse | null): string[] {
  const cursor = result?.route_replay_inspector.cursor_initial_state;
  // cursor 来自后端固定 false 初始态，UI 只展示，不提供逐帧驱动入口。
  return [
    `playing=${String(cursor?.playing ?? false)}`,
    `safe_to_play=${String(cursor?.safe_to_play ?? false)}`,
    `speed=${String(cursor?.speed ?? 0)}`,
    `frame_index=${String(cursor?.frame_index ?? "null")}`,
  ];
}

async function loadArchiveTasks(): Promise<void> {
  // 只有 operator 点击按钮才读取本地 archive 路径；页面加载不会自动触碰文件系统。
  archiveLoading.value = true;
  archiveError.value = "";
  try {
    archiveResult.value = await getO7CloudArchiveTasks(archiveJson.value);
  } catch (err) {
    archiveError.value = err instanceof Error ? err.message : "cloud_archive_task_api_unavailable_not_proven";
  } finally {
    archiveLoading.value = false;
  }
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
        <p class="eyebrow">PC-only local JSON preview. Read-only evidence shaping; robot dispatch stays disabled.</p>
      </div>
      <span class="pill danger">source=software_proof · proof_status=not_proven</span>
    </div>

    <div class="notice" role="note">
      These previews do not prove real realtime API, ROS2 /tf, cloud archive, annotation API, voice API, safe
      command API, robot ACK, HIL/hardware safety or delivery success.
    </div>

    <article class="snapshot-panel">
      <div class="section-head compact-head">
        <div>
          <h3>Cloud Archive Tasks</h3>
          <p class="eyebrow">Read-only local archive fixture for KR3/KR4/KR5/KR6 data source shaping.</p>
        </div>
        <span class="pill danger">{{ archiveResult?.archive_status ?? "not_loaded" }}</span>
      </div>

      <label class="single-input">
        <span>Archive fixture JSON</span>
        <input
          v-model="archiveJson"
          aria-label="Cloud archive fixture JSON path"
          placeholder="local archive fixture path, optional"
        >
      </label>
      <button class="secondary" type="button" @click="loadArchiveTasks">
        {{ archiveLoading ? "Loading archive tasks" : "Load archive tasks" }}
      </button>

      <div v-if="archiveError" class="notice" role="alert">
        Cloud archive task API unavailable: {{ archiveError }}. primary_actions_enabled=false.
      </div>

      <dl class="kv compact-kv">
        <dt>schema</dt>
        <dd>{{ archiveResult?.schema ?? "trashbot.o7.cloud_archive_tasks.v1" }}</dd>
        <dt>archive_status</dt>
        <dd>{{ archiveResult?.archive_status ?? "not_loaded" }}</dd>
        <dt>input status</dt>
        <dd>{{ archiveResult?.input_status.status ?? "not_loaded" }}</dd>
        <dt>failure reason</dt>
        <dd>{{ archiveResult?.input_status.failure_reason ?? "archive_json_not_provided" }}</dd>
        <dt>source fixture schema</dt>
        <dd>{{ archiveResult?.source_fixture_schema ?? "not_loaded" }}</dd>
      </dl>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Task list</h3>
          <dl class="kv compact-kv">
            <dt>total_tasks</dt>
            <dd>{{ archiveResult?.task_list.total_tasks ?? 0 }}</dd>
            <dt>selected_task</dt>
            <dd><code>{{ jsonSummary(archiveResult?.selected_task) }}</code></dd>
            <dt>latest_task</dt>
            <dd><code>{{ jsonSummary(archiveResult?.latest_task) }}</code></dd>
          </dl>
        </div>
        <div>
          <h3>Core false fields</h3>
          <ul class="dense">
            <!-- archive fixed false 字段直接来自后端，避免 UI 自行拼接真实能力状态。 -->
            <li v-for="field in archiveFalseFields(archiveResult)" :key="field">{{ field }}</li>
          </ul>
        </div>
      </div>

      <h3>Safe summaries</h3>
      <table>
        <thead>
          <tr>
            <th>field</th>
            <th>safe summary</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>trajectory</td>
            <td><code>{{ jsonSummary(archiveResult?.safe_summaries.trajectory) }}</code></td>
          </tr>
          <tr>
            <td>events</td>
            <td><code>{{ jsonSummary(archiveResult?.safe_summaries.events) }}</code></td>
          </tr>
          <tr>
            <td>labels</td>
            <td><code>{{ jsonSummary(archiveResult?.safe_summaries.labels) }}</code></td>
          </tr>
          <tr>
            <td>voice</td>
            <td><code>{{ jsonSummary(archiveResult?.safe_summaries.voice) }}</code></td>
          </tr>
          <tr>
            <td>commands</td>
            <td><code>{{ jsonSummary(archiveResult?.safe_summaries.commands) }}</code></td>
          </tr>
        </tbody>
      </table>

      <h3>Route replay inspector</h3>
      <dl class="kv compact-kv">
        <dt>status</dt>
        <dd>{{ archiveResult?.route_replay_inspector.status ?? "blocked_not_proven" }}</dd>
        <dt>selected_task_id</dt>
        <dd>{{ archiveResult?.route_replay_inspector.selected_task_id ?? "null" }}</dd>
        <dt>map_frame</dt>
        <dd>{{ archiveResult?.route_replay_inspector.map_frame ?? "" }}</dd>
        <dt>frame_count</dt>
        <dd>{{ archiveResult?.route_replay_inspector.frame_count ?? 0 }}</dd>
      </dl>

      <h3>Sample frames</h3>
      <table>
        <thead>
          <tr>
            <th>frame_index</th>
            <th>timestamp_ms</th>
            <th>x_m</th>
            <th>y_m</th>
            <th>yaw_rad</th>
            <th>speed_mps</th>
            <th>state</th>
            <th>evidence_ref</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!archiveResult?.route_replay_inspector.sample_frames.length">
            <td colspan="8">blocked_not_proven</td>
          </tr>
          <tr v-for="frame in archiveResult?.route_replay_inspector.sample_frames ?? []" :key="frame.frame_index">
            <td>{{ frame.frame_index }}</td>
            <td>{{ frame.timestamp_ms ?? "null" }}</td>
            <td>{{ frame.x_m ?? "null" }}</td>
            <td>{{ frame.y_m ?? "null" }}</td>
            <td>{{ frame.yaw_rad ?? "null" }}</td>
            <td>{{ frame.speed_mps ?? "null" }}</td>
            <td>{{ frame.state }}</td>
            <td>{{ frame.evidence_ref }}</td>
          </tr>
        </tbody>
      </table>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Event timeline</h3>
          <table>
            <thead>
              <tr>
                <th>event_type</th>
                <th>state</th>
                <th>timestamp_ms</th>
                <th>evidence_ref</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!archiveResult?.route_replay_inspector.event_timeline.length">
                <td colspan="4">blocked_not_proven</td>
              </tr>
              <tr
                v-for="event in archiveResult?.route_replay_inspector.event_timeline ?? []"
                :key="`${event.event_type}:${event.state}:${event.timestamp_ms}`"
              >
                <td>{{ event.event_type }}</td>
                <td>{{ event.state }}</td>
                <td>{{ event.timestamp_ms ?? "null" }}</td>
                <td>{{ event.evidence_ref }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div>
          <h3>Keyframe refs</h3>
          <ul class="dense">
            <li v-for="refValue in archiveResult?.route_replay_inspector.keyframe_refs ?? []" :key="refValue">
              {{ refValue }}
            </li>
            <li v-if="!archiveResult?.route_replay_inspector.keyframe_refs.length">blocked_not_proven</li>
          </ul>
          <h3>Cursor initial state</h3>
          <ul class="dense">
            <!-- cursor 字段必须保持后端给出的初始 false 状态，不能在前端生成可操作状态。 -->
            <li v-for="field in inspectorCursorFields(archiveResult)" :key="field">{{ field }}</li>
          </ul>
        </div>
      </div>

      <h3>Labeling queue inspector</h3>
      <dl class="kv compact-kv">
        <dt>status</dt>
        <dd>{{ archiveResult?.labeling_queue_inspector.status ?? "blocked_not_proven" }}</dd>
        <dt>selected_task_id</dt>
        <dd>{{ archiveResult?.labeling_queue_inspector.selected_task_id ?? "null" }}</dd>
        <dt>review_item_count</dt>
        <dd>{{ archiveResult?.labeling_queue_inspector.review_item_count ?? 0 }}</dd>
      </dl>

      <h3>Sample review items</h3>
      <table>
        <thead>
          <tr>
            <th>item_id</th>
            <th>task_id</th>
            <th>frame_id</th>
            <th>media_ref</th>
            <th>evidence_ref</th>
            <th>current_labels</th>
            <th>label_sample</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!archiveResult?.labeling_queue_inspector.sample_review_items.length">
            <td colspan="7">blocked_not_proven</td>
          </tr>
          <tr
            v-for="item in archiveResult?.labeling_queue_inspector.sample_review_items ?? []"
            :key="item.item_id"
          >
            <td>{{ item.item_id }}</td>
            <td>{{ item.task_id }}</td>
            <td>{{ item.frame_id }}</td>
            <td>{{ item.media_ref }}</td>
            <td>{{ item.evidence_ref }}</td>
            <td>{{ item.current_labels.count }}</td>
            <td><code>{{ jsonSummary(item.current_labels.sample) }}</code></td>
          </tr>
        </tbody>
      </table>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Label schema</h3>
          <dl class="kv compact-kv">
            <dt>schema_ref</dt>
            <dd>{{ archiveResult?.labeling_queue_inspector.label_schema.schema_ref ?? "" }}</dd>
            <dt>version</dt>
            <dd>{{ archiveResult?.labeling_queue_inspector.label_schema.version ?? "" }}</dd>
            <dt>required_fields</dt>
            <dd><code>{{ jsonSummary(archiveResult?.labeling_queue_inspector.label_schema.required_fields ?? []) }}</code></dd>
            <dt>allowed_fields</dt>
            <dd><code>{{ jsonSummary(archiveResult?.labeling_queue_inspector.label_schema.allowed_fields ?? []) }}</code></dd>
          </dl>
          <h3>Allowed label types</h3>
          <ul class="dense">
            <li v-for="labelType in archiveResult?.labeling_queue_inspector.allowed_label_types ?? []" :key="labelType">
              {{ labelType }}
            </li>
            <li v-if="!archiveResult?.labeling_queue_inspector.allowed_label_types.length">blocked_not_proven</li>
          </ul>
        </div>
        <div>
          <h3>Draft labels</h3>
          <dl class="kv compact-kv">
            <dt>count</dt>
            <dd>{{ archiveResult?.labeling_queue_inspector.draft_labels.count ?? 0 }}</dd>
            <dt>sample</dt>
            <dd><code>{{ jsonSummary(archiveResult?.labeling_queue_inspector.draft_labels.sample ?? []) }}</code></dd>
          </dl>
          <h3>Dataset gaps</h3>
          <dl class="kv compact-kv">
            <dt>status</dt>
            <dd>{{ archiveResult?.labeling_queue_inspector.dataset_export.status ?? "blocked_not_available" }}</dd>
            <dt>export_ref</dt>
            <dd>{{ archiveResult?.labeling_queue_inspector.dataset_export.export_ref ?? "" }}</dd>
            <dt>supported_formats</dt>
            <dd><code>{{ jsonSummary(archiveResult?.labeling_queue_inspector.dataset_export.supported_formats ?? []) }}</code></dd>
            <dt>gaps</dt>
            <dd><code>{{ jsonSummary(archiveResult?.labeling_queue_inspector.dataset_export.gaps ?? []) }}</code></dd>
          </dl>
          <h3>Labeling false fields</h3>
          <ul class="dense">
            <!-- 标注危险字段集中展示 false，避免只读检查视图被理解成可写标注界面。 -->
            <li v-for="field in labelingFalseFields(archiveResult)" :key="field">{{ field }}</li>
          </ul>
        </div>
      </div>

      <h3>Voice ASR/TTS inspector</h3>
      <dl class="kv compact-kv">
        <dt>status</dt>
        <dd>{{ archiveResult?.voice_asr_tts_inspector.status ?? "blocked_not_proven" }}</dd>
        <dt>selected_task_id</dt>
        <dd>{{ archiveResult?.voice_asr_tts_inspector.selected_task_id ?? "null" }}</dd>
        <dt>asr_event_count</dt>
        <dd>{{ archiveResult?.voice_asr_tts_inspector.asr_event_count ?? 0 }}</dd>
        <dt>voice_session</dt>
        <dd><code>{{ jsonSummary(archiveResult?.voice_asr_tts_inspector.voice_session) }}</code></dd>
      </dl>

      <h3>ASR event sample</h3>
      <table>
        <thead>
          <tr>
            <th>event_type</th>
            <th>timestamp_ms</th>
            <th>transcript</th>
            <th>confidence</th>
            <th>evidence_ref</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!archiveResult?.voice_asr_tts_inspector.sample_asr_events.length">
            <td colspan="5">blocked_not_proven</td>
          </tr>
          <tr
            v-for="event in archiveResult?.voice_asr_tts_inspector.sample_asr_events ?? []"
            :key="`${event.event_type}:${event.timestamp_ms}:${event.evidence_ref}`"
          >
            <td>{{ event.event_type }}</td>
            <td>{{ event.timestamp_ms ?? "null" }}</td>
            <td>{{ event.transcript }}</td>
            <td>{{ event.confidence ?? "null" }}</td>
            <td>{{ event.evidence_ref }}</td>
          </tr>
        </tbody>
      </table>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Latest transcript slots</h3>
          <dl class="kv compact-kv">
            <dt>latest_partial</dt>
            <dd><code>{{ jsonSummary(archiveResult?.voice_asr_tts_inspector.latest_partial) }}</code></dd>
            <dt>latest_final</dt>
            <dd><code>{{ jsonSummary(archiveResult?.voice_asr_tts_inspector.latest_final) }}</code></dd>
          </dl>
          <h3>TTS draft summary</h3>
          <dl class="kv compact-kv">
            <dt>text</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.text ?? "" }}</dd>
            <dt>text_length</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.text_length ?? 0 }}</dd>
            <dt>voice_profile</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.voice_profile ?? "not_loaded" }}</dd>
            <dt>language</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.language ?? "not_loaded" }}</dd>
            <dt>confirmation_required</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.confirmation_required ?? true }}</dd>
          </dl>
        </div>
        <div>
          <h3>speaker_dispatch summary</h3>
          <dl class="kv compact-kv">
            <dt>ack_status</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.speaker_dispatch.ack_status ?? "blocked_not_proven" }}</dd>
            <dt>speaker_ack_ref</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.speaker_dispatch.speaker_ack_ref ?? "missing_speaker_dispatch_ack" }}</dd>
            <dt>failure_event_ref</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.speaker_dispatch.failure_event_ref ?? "missing_speaker_failure_event" }}</dd>
            <dt>failure_refs</dt>
            <dd><code>{{ jsonSummary(archiveResult?.voice_asr_tts_inspector.speaker_dispatch.failure_refs ?? []) }}</code></dd>
          </dl>
          <h3>media_preflight dependency</h3>
          <dl class="kv compact-kv">
            <dt>required</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.media_preflight_dependency.required ?? true }}</dd>
            <dt>source_schema</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.media_preflight_dependency.source_schema ?? "trashbot.o7_board_media_preflight.v1" }}</dd>
            <dt>status</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.media_preflight_dependency.status ?? "blocked" }}</dd>
            <dt>dependency_ref</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.media_preflight_dependency.dependency_ref ?? "board_media_preflight_summary" }}</dd>
            <dt>gaps</dt>
            <dd><code>{{ jsonSummary(archiveResult?.voice_asr_tts_inspector.media_preflight_dependency.gaps ?? []) }}</code></dd>
          </dl>
          <h3>Voice false fields</h3>
          <ul class="dense">
            <!-- 这些字段是 KR5 的真实链路关闸证据，UI 不能把 fixture 摘要升级成可发声能力。 -->
            <li v-for="field in voiceFalseFields(archiveResult)" :key="field">{{ field }}</li>
          </ul>
        </div>
      </div>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in archiveBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
        </div>
        <div>
          <h3>Not proven</h3>
          <ul class="dense">
            <li v-for="item in archiveNotProven()" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </article>

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
