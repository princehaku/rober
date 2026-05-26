<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  getO7CloudArchiveTasks,
  getO7CloudArchiveTasksProbe,
  getO7CloudOperatorConsoleProbe,
  getO7PreviewsAcceptance,
  getO7RealtimeElevatorProbe,
  loadO7FixturePreview,
} from "../client/workstationApi";
import type { O7FixturePreviewInputs, O7FixturePreviewKind, O7FixturePreviewResponses } from "../client/workstationApi";
import type {
  O7CloudArchiveTasksProbeResponse,
  O7CloudArchiveTasksResponse,
  O7LabelingQueueInspectorReviewItem,
  O7PreviewsAcceptanceResponse,
  O7SafeCommandInspectorCommandSample,
  O7VoiceAsrTtsInspectorAsrEvent,
  O7CloudOperatorConsoleProbeResponse,
  O7RealtimeElevatorProbeResponse,
} from "../shared/contracts";

type O7FixturePreviewResult = O7FixturePreviewResponses[O7FixturePreviewKind];

interface PreviewConfig {
  id: O7FixturePreviewKind;
  title: string;
  expectedSchema: string;
}

interface RouteReplayTrajectoryPoint {
  frame_index: number;
  cursor_index: number;
  x_m: number;
  y_m: number;
}

interface RouteReplayMinimapPoint extends RouteReplayTrajectoryPoint {
  svg_x: number;
  svg_y: number;
}

interface LocalAnnotationDraft {
  labelType: string;
  confidence: string;
  note: string;
}

interface LocalTtsDraft {
  text: string;
  voiceProfile: string;
  language: string;
}

interface LocalSafeCommandDraft {
  commandMode: "manual_turn" | "navigate_goal";
  manualDirection: string;
  targetX: string;
  targetY: string;
  targetYaw: string;
  idempotencyDraftRef: string;
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
const cloudArchiveProbeBaseUrl = ref("http://127.0.0.1:8088");
const cloudArchiveProbeResult = ref<O7CloudArchiveTasksProbeResponse | null>(null);
const cloudArchiveProbeError = ref("");
const cloudArchiveProbeLoading = ref(false);
const realtimeElevatorProbeBaseUrl = ref("http://127.0.0.1:8088");
const realtimeElevatorProbeResult = ref<O7RealtimeElevatorProbeResponse | null>(null);
const realtimeElevatorProbeError = ref("");
const realtimeElevatorProbeLoading = ref(false);
const cloudProbeBaseUrl = ref("http://127.0.0.1:8088");
const cloudProbeResult = ref<O7CloudOperatorConsoleProbeResponse | null>(null);
const cloudProbeError = ref("");
const cloudProbeLoading = ref(false);
const previewsAcceptanceResult = ref<O7PreviewsAcceptanceResponse | null>(null);
const previewsAcceptanceError = ref("");
const previewsAcceptanceLoading = ref(false);
const routeReplayCursor = ref(0);
const labelingReviewCursor = ref(0);
const localAnnotationDrafts = ref<Record<string, LocalAnnotationDraft>>({});
const localTtsDraft = ref<LocalTtsDraft | null>(null);
const voiceAsrEventCursor = ref(0);
const safeCommandCursor = ref(0);
const localSafeCommandDraft = ref<LocalSafeCommandDraft | null>(null);

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
    `real_robot_ack_connected=${String(fields?.real_robot_ack_connected ?? false)}`,
    `real_asr_tts_runtime_connected=${String(fields?.real_asr_tts_runtime_connected ?? false)}`,
    `command_dispatch_enabled=${String(fields?.command_dispatch_enabled ?? false)}`,
    `manual_control_enabled=${String(fields?.manual_control_enabled ?? false)}`,
    `navigate_goal_enabled=${String(fields?.navigate_goal_enabled ?? false)}`,
    `keyboard_control_enabled=${String(fields?.keyboard_control_enabled ?? false)}`,
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

function safeCommandFalseFields(result: O7CloudArchiveTasksResponse | null): string[] {
  const inspector = result?.safe_command_inspector;
  // KR6 inspector 只读展示 command envelope，所有发送、手控、键盘、ACK 和真实 API 字段必须保持 false。
  return [
    `command_dispatch_enabled=${String(inspector?.command_dispatch_enabled ?? false)}`,
    `manual_control_enabled=${String(inspector?.manual_control_enabled ?? false)}`,
    `navigate_goal_enabled=${String(inspector?.navigate_goal_enabled ?? false)}`,
    `keyboard_control_enabled=${String(inspector?.keyboard_control_enabled ?? false)}`,
    `real_command_api_connected=${String(inspector?.real_command_api_connected ?? false)}`,
    `real_robot_ack_connected=${String(inspector?.real_robot_ack_connected ?? false)}`,
    `robot_control_executed=${String(inspector?.robot_control_executed ?? false)}`,
    `safe_to_control=${String(inspector?.safe_to_control ?? false)}`,
    `primary_actions_enabled=${String(inspector?.primary_actions_enabled ?? false)}`,
    `delivery_success=${String(inspector?.delivery_success ?? false)}`,
    `manual_turn_envelope.sends_to_robot=${String(inspector?.manual_turn_envelope.sends_to_robot ?? false)}`,
    `navigate_goal_envelope.sends_to_robot=${String(inspector?.navigate_goal_envelope.sends_to_robot ?? false)}`,
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

function cloudProbeBlockedReasons(): string[] {
  return cloudProbeResult.value?.blocked_reasons ?? ["cloud_operator_console_probe_not_loaded"];
}

function cloudProbeNotProven(): string[] {
  return cloudProbeResult.value?.not_proven ?? ["cloud_operator_console_probe_not_proven"];
}

function cloudArchiveProbeBlockedReasons(): string[] {
  return cloudArchiveProbeResult.value?.blocked_reasons ?? ["cloud_archive_tasks_probe_not_loaded"];
}

function cloudArchiveProbeNotProven(): string[] {
  return cloudArchiveProbeResult.value?.not_proven ?? ["cloud_archive_tasks_probe_not_proven"];
}

function realtimeElevatorProbeBlockedReasons(): string[] {
  return realtimeElevatorProbeResult.value?.blocked_reasons ?? ["realtime_elevator_probe_not_loaded"];
}

function realtimeElevatorProbeNotProven(): string[] {
  return realtimeElevatorProbeResult.value?.not_proven ?? ["realtime_elevator_probe_not_proven"];
}

function previewsAcceptanceBlocked(): string[] {
  return previewsAcceptanceResult.value?.blocked ?? ["o7_previews_acceptance_guard_not_loaded"];
}

function previewsAcceptanceNotProven(): string[] {
  return previewsAcceptanceResult.value?.not_proven ?? ["real_rtc_video_control_ack_hil_not_proven"];
}

function previewsAcceptanceFalseFields(): string[] {
  const fields = previewsAcceptanceResult.value?.fixed_false_fields;
  // Guard 字段必须来自后端摘要；未加载时也按 false 展示，避免空白被误读为可用。
  return [
    `reads_hardware=${String(fields?.reads_hardware ?? false)}`,
    `sends_commands=${String(fields?.sends_commands ?? false)}`,
    `connects_cloud_production=${String(fields?.connects_cloud_production ?? false)}`,
    `safe_to_control=${String(fields?.safe_to_control ?? false)}`,
    `delivery_success=${String(fields?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(fields?.primary_actions_enabled ?? false)}`,
    `playback_available=${String(fields?.playback_available ?? false)}`,
    `submit_enabled=${String(fields?.submit_enabled ?? false)}`,
    `tts_send_enabled=${String(fields?.tts_send_enabled ?? false)}`,
    `command_dispatch_enabled=${String(fields?.command_dispatch_enabled ?? false)}`,
    `manual_control_enabled=${String(fields?.manual_control_enabled ?? false)}`,
    `navigate_goal_enabled=${String(fields?.navigate_goal_enabled ?? false)}`,
    `keyboard_control_enabled=${String(fields?.keyboard_control_enabled ?? false)}`,
    `robot_control_executed=${String(fields?.robot_control_executed ?? false)}`,
    `real_realtime_api_connected=${String(fields?.real_realtime_api_connected ?? false)}`,
    `real_cloud_archive_connected=${String(fields?.real_cloud_archive_connected ?? false)}`,
    `real_annotation_api_connected=${String(fields?.real_annotation_api_connected ?? false)}`,
    `real_voice_api_connected=${String(fields?.real_voice_api_connected ?? false)}`,
    `real_command_api_connected=${String(fields?.real_command_api_connected ?? false)}`,
    `real_robot_ack_connected=${String(fields?.real_robot_ack_connected ?? false)}`,
  ];
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

const routeReplayFrames = computed(() => archiveResult.value?.route_replay_inspector.sample_frames ?? []);
const labelingReviewItems = computed(() => archiveResult.value?.labeling_queue_inspector.sample_review_items ?? []);
const voiceAsrEvents = computed(() => archiveResult.value?.voice_asr_tts_inspector.sample_asr_events ?? []);
const safeCommandSamples = computed(() => archiveResult.value?.safe_command_inspector.sample_commands ?? []);

function isFiniteNumber(value: unknown): value is number {
  // 轨迹小地图只接受真实 finite number；null、NaN 和字符串都不能进入 SVG 归一化。
  return typeof value === "number" && Number.isFinite(value);
}

const routeReplayTrajectoryPoints = computed<RouteReplayTrajectoryPoint[]>(() =>
  routeReplayFrames.value
    .map((frame, cursorIndex) => ({ frame, cursorIndex }))
    .filter(({ frame }) => isFiniteNumber(frame.x_m) && isFiniteNumber(frame.y_m))
    .map(({ frame, cursorIndex }) => ({
      frame_index: frame.frame_index,
      cursor_index: cursorIndex,
      x_m: Number(frame.x_m),
      y_m: Number(frame.y_m),
    })),
);

function normalizeRouteReplayPoint(
  point: RouteReplayTrajectoryPoint,
  bounds: { minX: number; maxX: number; minY: number; maxY: number },
): RouteReplayMinimapPoint {
  const width = bounds.maxX - bounds.minX;
  const height = bounds.maxY - bounds.minY;
  // 单点、水平线和垂直线用中心线兜底，避免除以 0 后产生 NaN 或误导性 marker。
  const svgX = width === 0 ? 50 : 10 + ((point.x_m - bounds.minX) / width) * 80;
  const svgY = height === 0 ? 50 : 90 - ((point.y_m - bounds.minY) / height) * 80;
  return { ...point, svg_x: svgX, svg_y: svgY };
}

const routeReplayMinimapPoints = computed<RouteReplayMinimapPoint[]>(() => {
  const points = routeReplayTrajectoryPoints.value;
  if (!points.length) {
    return [];
  }
  const xs = points.map((point) => point.x_m);
  const ys = points.map((point) => point.y_m);
  const bounds = {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
  };
  // 所有 SVG 坐标都限制在固定 viewBox 内，保证响应式布局不因数据极端值抖动。
  return points.map((point) => normalizeRouteReplayPoint(point, bounds));
});

const routeReplayMinimapPolyline = computed(() =>
  routeReplayMinimapPoints.value.map((point) => `${point.svg_x.toFixed(2)},${point.svg_y.toFixed(2)}`).join(" "),
);

const currentRouteReplayMinimapMarker = computed<RouteReplayMinimapPoint | null>(() => {
  const frame = routeReplayFrames.value[routeReplayCursor.value] ?? null;
  // 当前帧没有有效坐标时不画 marker，避免把未知位置显示成轨迹上的确定点。
  if (!frame || !isFiniteNumber(frame.x_m) || !isFiniteNumber(frame.y_m)) {
    return null;
  }
  return routeReplayMinimapPoints.value.find((point) => point.cursor_index === routeReplayCursor.value) ?? null;
});

const routeReplayMinimapStatus = computed(() => {
  // 少于两个有效点不能构成轨迹检查能力，只能作为未证明状态展示。
  if (routeReplayTrajectoryPoints.value.length < 2) {
    return "blocked_not_proven";
  }
  return "readonly_fixture_trajectory_ready";
});

const routeReplayCurrentMarkerStatus = computed(() => {
  // marker 与现有 routeReplayCursor 绑定；当前 sample 坐标无效时必须显式 unknown。
  if (!currentRouteReplayMinimapMarker.value) {
    return "blocked_unknown_current_frame_coordinate";
  }
  return `frame_index=${currentRouteReplayMinimapMarker.value.frame_index}`;
});

const routeReplayBlockedReason = computed(() => {
  const archive = archiveResult.value as (O7CloudArchiveTasksResponse & { playback_available?: boolean }) | null;
  // 逐帧浏览只绑定本地 sample_frames；未加载、无 selected task、显式 playback=false 都必须关闸。
  if (!archive) {
    return "archive_not_loaded";
  }
  if (!archive.route_replay_inspector.selected_task_id) {
    return "selected_task_missing";
  }
  if (!routeReplayFrames.value.length) {
    return "sample_frames_missing";
  }
  if (archive.playback_available === false) {
    return "playback_available_false";
  }
  if (archive.route_replay_inspector.status !== "fixture_inspector_ready") {
    return "route_replay_inspector_blocked_not_proven";
  }
  return "";
});

const routeReplayNavigationEnabled = computed(() => routeReplayBlockedReason.value === "");

const labelingReviewBlockedReason = computed(() => {
  const inspector = archiveResult.value?.labeling_queue_inspector;
  // 标注 review panel 只绑定本地 archive fixture；任何缺口都回到 blocked_not_proven。
  if (!archiveResult.value) {
    return "archive_not_loaded";
  }
  if (!inspector?.selected_task_id) {
    return "selected_task_missing";
  }
  if (!labelingReviewItems.value.length) {
    return "sample_review_items_missing";
  }
  if (inspector.status !== "fixture_labeling_ready") {
    return "labeling_queue_inspector_blocked_not_proven";
  }
  return "";
});

const labelingReviewNavigationEnabled = computed(() => labelingReviewBlockedReason.value === "");

const voiceMonitorBlockedReason = computed(() => {
  const inspector = archiveResult.value?.voice_asr_tts_inspector;
  const draft = inspector?.tts_draft;
  // 语音 monitor 只读本地 fixture；缺 archive、缺 selected task、缺样本或 inspector blocked 都必须 fail-closed。
  if (!archiveResult.value) {
    return "archive_not_loaded";
  }
  if (!inspector?.selected_task_id) {
    return "selected_task_missing";
  }
  if (!voiceAsrEvents.value.length && !draft?.text && !draft?.text_length) {
    return "voice_fixture_sample_and_tts_draft_missing";
  }
  if (inspector.status !== "fixture_voice_ready") {
    return "voice_asr_tts_inspector_blocked_not_proven";
  }
  return "";
});

const voiceAsrNavigationEnabled = computed(() => voiceMonitorBlockedReason.value === "" && voiceAsrEvents.value.length > 0);
const voiceMonitorPanelStatus = computed(() => (voiceMonitorBlockedReason.value ? "blocked_not_proven" : "local_fixture_voice_monitor_ready"));
const localTtsDraftInputsEnabled = computed(() => voiceMonitorBlockedReason.value === "");

function defaultLocalTtsDraft(): LocalTtsDraft {
  const inspector = archiveResult.value?.voice_asr_tts_inspector;
  // 默认值只来自当前 archive fixture 摘要；缺少 ready 上下文时保持空值并由校验 fail-closed。
  if (!localTtsDraftInputsEnabled.value || !inspector) {
    return { text: "", voiceProfile: "", language: "" };
  }
  return {
    text: inspector.tts_draft.text,
    voiceProfile: inspector.tts_draft.voice_profile,
    language: inspector.tts_draft.language,
  };
}

const currentLocalTtsDraft = computed<LocalTtsDraft>(() => localTtsDraft.value ?? defaultLocalTtsDraft());

const localTtsSourceTranscriptSummary = computed(() => {
  const inspector = archiveResult.value?.voice_asr_tts_inspector;
  // 摘要优先 final，再退到 partial/current sample；它只是本地上下文提示，不生成可发送 payload。
  if (!localTtsDraftInputsEnabled.value || !inspector) {
    return "blocked_not_proven";
  }
  const finalText = inspector.latest_final.text.trim();
  if (finalText) {
    return `latest_final_chars=${finalText.length}; text=${finalText.slice(0, 80)}`;
  }
  const partialText = inspector.latest_partial.text.trim();
  if (partialText) {
    return `latest_partial_chars=${partialText.length}; text=${partialText.slice(0, 80)}`;
  }
  const currentTranscript = currentVoiceAsrEvent.value?.transcript.trim() ?? "";
  if (currentTranscript) {
    return `current_asr_event_chars=${currentTranscript.length}; text=${currentTranscript.slice(0, 80)}`;
  }
  return "blocked_not_proven";
});

const localTtsDraftTextLength = computed(() => currentLocalTtsDraft.value.text.trim().length);

const localTtsDraftValidationStatus = computed(() => {
  if (!localTtsDraftInputsEnabled.value) {
    return "blocked_not_proven";
  }
  if (!currentLocalTtsDraft.value.text.trim()) {
    return "blocked_tts_text_empty";
  }
  if (localTtsDraftTextLength.value > 120) {
    return "blocked_tts_text_too_long";
  }
  if (!currentLocalTtsDraft.value.voiceProfile.trim()) {
    return "blocked_voice_profile_empty";
  }
  if (!currentLocalTtsDraft.value.language.trim()) {
    return "blocked_language_empty";
  }
  return "local_tts_draft_valid";
});

const localTtsDraftStatus = computed(() => {
  if (!localTtsDraftInputsEnabled.value) {
    return "blocked_not_proven";
  }
  return localTtsDraftValidationStatus.value === "local_tts_draft_valid"
    ? "local_tts_draft_ready"
    : "local_tts_draft_blocked";
});

const safeCommandReviewBlockedReason = computed(() => {
  const inspector = archiveResult.value?.safe_command_inspector;
  // KR6 review panel 只审阅本地 fixture 摘要；缺 archive、task、样本或 inspector blocked 都不能进入可浏览状态。
  if (!archiveResult.value) {
    return "archive_not_loaded";
  }
  if (!inspector?.selected_task_id) {
    return "selected_task_missing";
  }
  if (
    !safeCommandSamples.value.length &&
    inspector.manual_turn_envelope.status !== "fixture_summary_only" &&
    inspector.navigate_goal_envelope.status !== "fixture_summary_only"
  ) {
    return "command_samples_and_envelopes_missing";
  }
  if (inspector.status !== "fixture_command_ready") {
    return "safe_command_inspector_blocked_not_proven";
  }
  return "";
});

const safeCommandNavigationEnabled = computed(
  () => safeCommandReviewBlockedReason.value === "" && safeCommandSamples.value.length > 0,
);
const safeCommandReviewPanelStatus = computed(() =>
  safeCommandReviewBlockedReason.value ? "blocked_not_proven" : "local_fixture_safe_command_review_ready",
);

const safeCommandDraftEditorBlockedReason = computed(() => {
  const inspector = archiveResult.value?.safe_command_inspector;
  // 草稿编辑器比 review cursor 更严格：两类 envelope 都要存在，避免 operator 在缺上下文时形成伪 payload。
  if (safeCommandReviewBlockedReason.value) {
    return safeCommandReviewBlockedReason.value;
  }
  if (
    !inspector ||
    inspector.manual_turn_envelope.status !== "fixture_summary_only" ||
    inspector.navigate_goal_envelope.status !== "fixture_summary_only"
  ) {
    return "safe_command_manual_or_navigate_context_missing";
  }
  return "";
});

const safeCommandDraftInputsEnabled = computed(() => safeCommandDraftEditorBlockedReason.value === "");

function defaultLocalSafeCommandDraft(): LocalSafeCommandDraft {
  const inspector = archiveResult.value?.safe_command_inspector;
  const commandMode =
    currentSafeCommandSample.value?.command_type === "navigate_goal" ? "navigate_goal" : "manual_turn";
  // 默认值只来自当前 safe_command_inspector 摘要；缺上下文时保持空值并由校验 fail-closed。
  if (!safeCommandDraftInputsEnabled.value || !inspector) {
    return {
      commandMode,
      manualDirection: "",
      targetX: "",
      targetY: "",
      targetYaw: "",
      idempotencyDraftRef: "",
    };
  }
  const targetX = inspector.navigate_goal_envelope.x_m ?? inspector.map_goal_slot.x_m;
  const targetY = inspector.navigate_goal_envelope.y_m ?? inspector.map_goal_slot.y_m;
  const targetYaw = inspector.navigate_goal_envelope.yaw_rad ?? inspector.map_goal_slot.yaw_rad;
  return {
    commandMode,
    manualDirection: inspector.manual_turn_envelope.requested_direction,
    targetX: targetX === null ? "" : String(targetX),
    targetY: targetY === null ? "" : String(targetY),
    targetYaw: targetYaw === null ? "" : String(targetYaw),
    idempotencyDraftRef:
      currentSafeCommandSample.value?.idempotency_key_ref || inspector.idempotency_key_requirement.key_ref,
  };
}

const currentLocalSafeCommandDraft = computed<LocalSafeCommandDraft>(
  () => localSafeCommandDraft.value ?? defaultLocalSafeCommandDraft(),
);

const safeCommandAllowedManualDirections = computed(() => {
  const requestedDirection = archiveResult.value?.safe_command_inspector.manual_turn_envelope.requested_direction ?? "";
  // 固定安全集合外加当前 fixture 请求方向；这样能审阅历史 fixture，又不会接受任意输入。
  return Array.from(new Set(["left", "right", "forward", "backward", "stop", requestedDirection].filter(Boolean)));
});

function finiteDraftNumber(value: string): number | null {
  const parsed = Number(value);
  // 输入框值以字符串保存，便于把空值、非数字和 NaN 分别挡在本地校验层。
  return Number.isFinite(parsed) ? parsed : null;
}

const localSafeCommandTargetSummary = computed(() => {
  const x = finiteDraftNumber(currentLocalSafeCommandDraft.value.targetX);
  const y = finiteDraftNumber(currentLocalSafeCommandDraft.value.targetY);
  const yaw = finiteDraftNumber(currentLocalSafeCommandDraft.value.targetYaw);
  // target summary 只描述当前浏览器草稿，不构造可发送的 navigate payload。
  if (x === null || y === null || yaw === null) {
    return "target_summary=blocked_invalid_navigate_goal";
  }
  return `x=${x}; y=${y}; yaw=${yaw}; map_frame=${archiveResult.value?.safe_command_inspector.navigate_goal_envelope.map_frame ?? "map"}`;
});

const localSafeCommandDraftValidationStatus = computed(() => {
  if (!safeCommandDraftInputsEnabled.value) {
    return "blocked_not_proven";
  }
  if (!currentLocalSafeCommandDraft.value.idempotencyDraftRef.trim()) {
    return "blocked_idempotency_key_missing";
  }
  if (currentLocalSafeCommandDraft.value.commandMode === "manual_turn") {
    const direction = currentLocalSafeCommandDraft.value.manualDirection.trim();
    if (!direction || !safeCommandAllowedManualDirections.value.includes(direction)) {
      return "blocked_manual_direction_not_allowed";
    }
    return "local_safe_command_draft_valid";
  }
  if (
    finiteDraftNumber(currentLocalSafeCommandDraft.value.targetX) === null ||
    finiteDraftNumber(currentLocalSafeCommandDraft.value.targetY) === null ||
    finiteDraftNumber(currentLocalSafeCommandDraft.value.targetYaw) === null
  ) {
    return "blocked_invalid_navigate_goal";
  }
  return "local_safe_command_draft_valid";
});

const localSafeCommandDraftStatus = computed(() => {
  if (!safeCommandDraftInputsEnabled.value) {
    return "blocked_not_proven";
  }
  return localSafeCommandDraftValidationStatus.value === "local_safe_command_draft_valid"
    ? "local_safe_command_draft_ready"
    : "local_safe_command_draft_blocked";
});

const currentRouteReplayFrame = computed(() => {
  // cursor 是数组下标，不发送给后端；frame_index 保持使用 archive fixture 的原始字段。
  if (!routeReplayNavigationEnabled.value) {
    return null;
  }
  return routeReplayFrames.value[routeReplayCursor.value] ?? routeReplayFrames.value[0] ?? null;
});

function routeReplayCursorDisplay(): string {
  const frame = currentRouteReplayFrame.value;
  // blocked 时也显示总 sample 数，方便 operator 区分未加载和已加载但不可浏览。
  if (!frame) {
    return `blocked_not_proven / ${routeReplayFrames.value.length}`;
  }
  return `${routeReplayCursor.value + 1} / ${routeReplayFrames.value.length}`;
}

const currentLabelingReviewItem = computed<O7LabelingQueueInspectorReviewItem | null>(() => {
  // cursor 只用于本地聚焦 sample item，不能被解释为 selected task 或真实云端队列状态。
  if (!labelingReviewNavigationEnabled.value) {
    return null;
  }
  return labelingReviewItems.value[labelingReviewCursor.value] ?? labelingReviewItems.value[0] ?? null;
});

const localDraftAllowedLabelTypes = computed(() => archiveResult.value?.labeling_queue_inspector.allowed_label_types ?? []);

const localDraftItemKey = computed(() => {
  const item = currentLabelingReviewItem.value;
  // 草稿按 item_id 隔离，避免 operator 切换 cursor 后看到上一条 review item 的内存草稿。
  return item ? `${item.task_id}:${item.item_id}` : "";
});

function emptyLocalAnnotationDraft(): LocalAnnotationDraft {
  // confidence 用字符串保存，确保 "abc"、空值和 NaN 都能被校验状态准确暴露。
  return { labelType: "", confidence: "0.5", note: "" };
}

function defaultLocalAnnotationDraft(): LocalAnnotationDraft {
  // 默认 label type 取当前 fixture 允许列表第一项；列表为空时保持空值并 fail-closed。
  return { ...emptyLocalAnnotationDraft(), labelType: localDraftAllowedLabelTypes.value[0] ?? "" };
}

const currentLocalAnnotationDraft = computed<LocalAnnotationDraft>(() => {
  const key = localDraftItemKey.value;
  if (!key) {
    return emptyLocalAnnotationDraft();
  }
  return localAnnotationDrafts.value[key] ?? defaultLocalAnnotationDraft();
});

const localDraftEditorBlockedReason = computed(() => {
  // editor 只在 labeling review panel 已证明有本地 sample item 且 allowed label types 非空时开放输入。
  if (labelingReviewBlockedReason.value) {
    return labelingReviewBlockedReason.value;
  }
  if (!localDraftAllowedLabelTypes.value.length) {
    return "allowed_label_types_missing";
  }
  return "";
});

const localDraftInputsEnabled = computed(() => localDraftEditorBlockedReason.value === "");

const localDraftValidationStatus = computed(() => {
  if (!localDraftInputsEnabled.value) {
    return "blocked_not_proven";
  }
  if (!localDraftAllowedLabelTypes.value.includes(currentLocalAnnotationDraft.value.labelType)) {
    return "blocked_label_type_not_allowed";
  }
  const confidence = Number(currentLocalAnnotationDraft.value.confidence);
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
    return "blocked_invalid_confidence";
  }
  return "local_memory_draft_valid";
});

const localDraftStatus = computed(() => {
  if (!localDraftInputsEnabled.value) {
    return "blocked_not_proven";
  }
  return localDraftValidationStatus.value === "local_memory_draft_valid"
    ? "local_memory_draft_ready"
    : "local_memory_draft_blocked";
});

const localDraftNoteSummary = computed(() => {
  const note = currentLocalAnnotationDraft.value.note.trim();
  // 只展示长度和短摘要，不把本地 operator 输入解释为可提交 annotation payload。
  if (!note) {
    return "note_chars=0; metadata_summary=empty_local_memory_only";
  }
  return `note_chars=${note.length}; metadata_summary=${note.slice(0, 80)}`;
});

function writeCurrentLocalAnnotationDraft(patch: Partial<LocalAnnotationDraft>): void {
  const key = localDraftItemKey.value;
  if (!key) {
    return;
  }
  // 每次写入只更新当前 item 的内存槽位，不调用 API、不写后端、不触发 autosave。
  localAnnotationDrafts.value = {
    ...localAnnotationDrafts.value,
    [key]: {
      ...currentLocalAnnotationDraft.value,
      ...patch,
    },
  };
}

function setLocalDraftLabelType(event: Event): void {
  writeCurrentLocalAnnotationDraft({ labelType: (event.target as HTMLSelectElement).value });
}

function setLocalDraftConfidence(event: Event): void {
  writeCurrentLocalAnnotationDraft({ confidence: (event.target as HTMLInputElement).value });
}

function setLocalDraftNote(event: Event): void {
  writeCurrentLocalAnnotationDraft({ note: (event.target as HTMLTextAreaElement).value });
}

function resetLocalAnnotationDraft(): void {
  const key = localDraftItemKey.value;
  if (!key) {
    return;
  }
  // Reset draft 只重置当前 item 的浏览器内存，不影响其他 item，也不创建云端副作用。
  localAnnotationDrafts.value = {
    ...localAnnotationDrafts.value,
    [key]: defaultLocalAnnotationDraft(),
  };
}

function labelingReviewCursorDisplay(): string {
  const item = currentLabelingReviewItem.value;
  // blocked 时保留 sample 数，方便 operator 区分“未加载”和“已加载但不可浏览”。
  if (!item) {
    return `blocked_not_proven / ${labelingReviewItems.value.length}`;
  }
  return `${labelingReviewCursor.value + 1} / ${labelingReviewItems.value.length}`;
}

const currentVoiceAsrEvent = computed<O7VoiceAsrTtsInspectorAsrEvent | null>(() => {
  // cursor 只用于 operator 聚焦 ASR 样本，不能解释为真实 stream offset 或云端订阅状态。
  if (!voiceAsrNavigationEnabled.value) {
    return null;
  }
  return voiceAsrEvents.value[voiceAsrEventCursor.value] ?? voiceAsrEvents.value[0] ?? null;
});

const currentSafeCommandSample = computed<O7SafeCommandInspectorCommandSample | null>(() => {
  // command cursor 只用于本地审阅 sample，不会映射成 dispatch、手控、寻路或 ACK 查询。
  if (!safeCommandNavigationEnabled.value) {
    return null;
  }
  return safeCommandSamples.value[safeCommandCursor.value] ?? safeCommandSamples.value[0] ?? null;
});

function voiceAsrCursorDisplay(): string {
  const event = currentVoiceAsrEvent.value;
  // blocked 时保留 sample 数，方便 operator 判断是未加载还是 fixture 缺 ASR 样本。
  if (!event) {
    return `blocked_not_proven / ${voiceAsrEvents.value.length}`;
  }
  return `${voiceAsrEventCursor.value + 1} / ${voiceAsrEvents.value.length}`;
}

function safeCommandCursorDisplay(): string {
  const command = currentSafeCommandSample.value;
  // blocked 时保留 command sample 数，方便区分未加载、fixture 缺样本和 inspector blocked。
  if (!command) {
    return `blocked_not_proven / ${safeCommandSamples.value.length}`;
  }
  return `${safeCommandCursor.value + 1} / ${safeCommandSamples.value.length}`;
}

function clampRouteReplayCursor(index: number): void {
  const maxIndex = Math.max(routeReplayFrames.value.length - 1, 0);
  // 所有 navigation 都只改浏览器内存里的数组下标，避免误变成真实回放命令。
  routeReplayCursor.value = Math.min(Math.max(index, 0), maxIndex);
}

function clampLabelingReviewCursor(index: number): void {
  const maxIndex = Math.max(labelingReviewItems.value.length - 1, 0);
  // 标注浏览 cursor 不能落库、不能 autosave，只允许在当前浏览器会话内换焦点。
  labelingReviewCursor.value = Math.min(Math.max(index, 0), maxIndex);
}

function clampVoiceAsrEventCursor(index: number): void {
  const maxIndex = Math.max(voiceAsrEvents.value.length - 1, 0);
  // ASR navigation 是本地数组浏览，不连接 ASR stream，也不会触发 TTS 或喇叭派发。
  voiceAsrEventCursor.value = Math.min(Math.max(index, 0), maxIndex);
}

function clampSafeCommandCursor(index: number): void {
  const maxIndex = Math.max(safeCommandSamples.value.length - 1, 0);
  // command navigation 只改变浏览器内存下标，不写后端、不发送命令、不绑定键盘。
  safeCommandCursor.value = Math.min(Math.max(index, 0), maxIndex);
}

function resetRouteReplayCursor(): void {
  clampRouteReplayCursor(0);
}

function resetLabelingReviewCursor(): void {
  clampLabelingReviewCursor(0);
}

function resetVoiceAsrEventCursor(): void {
  clampVoiceAsrEventCursor(0);
}

function resetLocalTtsDraft(): void {
  // reset 只丢弃浏览器内存覆盖值，重新显示当前 fixture 的只读默认草稿。
  localTtsDraft.value = null;
}

function resetLocalSafeCommandDraft(): void {
  // reset 只丢弃浏览器内存覆盖值，重新显示当前 archive 的 fixture 默认草稿。
  localSafeCommandDraft.value = null;
}

function resetSafeCommandCursor(): void {
  clampSafeCommandCursor(0);
}

function writeLocalTtsDraft(patch: Partial<LocalTtsDraft>): void {
  if (!localTtsDraftInputsEnabled.value) {
    return;
  }
  // 编辑仅更新当前浏览器内存，不调用 API、不播放、不派发喇叭。
  localTtsDraft.value = {
    ...currentLocalTtsDraft.value,
    ...patch,
  };
}

function setLocalTtsDraftText(event: Event): void {
  writeLocalTtsDraft({ text: (event.target as HTMLTextAreaElement).value });
}

function setLocalTtsVoiceProfile(event: Event): void {
  writeLocalTtsDraft({ voiceProfile: (event.target as HTMLInputElement).value });
}

function setLocalTtsLanguage(event: Event): void {
  writeLocalTtsDraft({ language: (event.target as HTMLInputElement).value });
}

function writeLocalSafeCommandDraft(patch: Partial<LocalSafeCommandDraft>): void {
  if (!safeCommandDraftInputsEnabled.value) {
    return;
  }
  // 编辑仅更新浏览器内存，不调用 API、不写云端、不派发手控或寻路命令。
  localSafeCommandDraft.value = {
    ...currentLocalSafeCommandDraft.value,
    ...patch,
  };
}

function setLocalSafeCommandMode(event: Event): void {
  writeLocalSafeCommandDraft({ commandMode: (event.target as HTMLSelectElement).value as LocalSafeCommandDraft["commandMode"] });
}

function setLocalSafeCommandDirection(event: Event): void {
  writeLocalSafeCommandDraft({ manualDirection: (event.target as HTMLInputElement).value });
}

function setLocalSafeCommandTargetX(event: Event): void {
  writeLocalSafeCommandDraft({ targetX: (event.target as HTMLInputElement).value });
}

function setLocalSafeCommandTargetY(event: Event): void {
  writeLocalSafeCommandDraft({ targetY: (event.target as HTMLInputElement).value });
}

function setLocalSafeCommandTargetYaw(event: Event): void {
  writeLocalSafeCommandDraft({ targetYaw: (event.target as HTMLInputElement).value });
}

function setLocalSafeCommandIdempotencyDraftRef(event: Event): void {
  writeLocalSafeCommandDraft({ idempotencyDraftRef: (event.target as HTMLInputElement).value });
}

function previousRouteReplayFrame(): void {
  if (routeReplayNavigationEnabled.value) {
    clampRouteReplayCursor(routeReplayCursor.value - 1);
  }
}

function previousLabelingReviewItem(): void {
  if (labelingReviewNavigationEnabled.value) {
    clampLabelingReviewCursor(labelingReviewCursor.value - 1);
  }
}

function previousVoiceAsrEvent(): void {
  if (voiceAsrNavigationEnabled.value) {
    clampVoiceAsrEventCursor(voiceAsrEventCursor.value - 1);
  }
}

function previousSafeCommand(): void {
  if (safeCommandNavigationEnabled.value) {
    clampSafeCommandCursor(safeCommandCursor.value - 1);
  }
}

function nextRouteReplayFrame(): void {
  if (routeReplayNavigationEnabled.value) {
    clampRouteReplayCursor(routeReplayCursor.value + 1);
  }
}

function nextLabelingReviewItem(): void {
  if (labelingReviewNavigationEnabled.value) {
    clampLabelingReviewCursor(labelingReviewCursor.value + 1);
  }
}

function nextVoiceAsrEvent(): void {
  if (voiceAsrNavigationEnabled.value) {
    clampVoiceAsrEventCursor(voiceAsrEventCursor.value + 1);
  }
}

function nextSafeCommand(): void {
  if (safeCommandNavigationEnabled.value) {
    clampSafeCommandCursor(safeCommandCursor.value + 1);
  }
}

function setRouteReplayCursorFromInput(event: Event): void {
  const target = event.target as HTMLInputElement;
  if (routeReplayNavigationEnabled.value) {
    clampRouteReplayCursor(Number(target.value));
  }
}

async function loadArchiveTasks(): Promise<void> {
  // 只有 operator 点击按钮才读取本地 archive 路径；页面加载不会自动触碰文件系统。
  archiveLoading.value = true;
  archiveError.value = "";
  try {
    archiveResult.value = await getO7CloudArchiveTasks(archiveJson.value);
    resetRouteReplayCursor();
    resetLabelingReviewCursor();
    localAnnotationDrafts.value = {};
    resetVoiceAsrEventCursor();
    resetLocalTtsDraft();
    resetSafeCommandCursor();
    resetLocalSafeCommandDraft();
  } catch (err) {
    archiveError.value = err instanceof Error ? err.message : "cloud_archive_task_api_unavailable_not_proven";
  } finally {
    archiveLoading.value = false;
  }
}

watch(localDraftItemKey, () => {
  // item cursor 改变时不复用上一条 item 的草稿；新 item 通过独立 key 读取自己的内存槽位。
  if (localDraftItemKey.value && !localAnnotationDrafts.value[localDraftItemKey.value]) {
    writeCurrentLocalAnnotationDraft(defaultLocalAnnotationDraft());
  }
});

watch(archiveJson, () => {
  // operator 切换 archive path 时立即清理本地覆盖值，避免旧任务草稿留在新路径上下文里。
  resetLocalTtsDraft();
  resetLocalSafeCommandDraft();
});

async function loadCloudOperatorConsoleProbe(): Promise<void> {
  // 这里只触发 PC 后端 GET probe；浏览器不直接访问 relay，也不创建任何机器人动作。
  cloudProbeLoading.value = true;
  cloudProbeError.value = "";
  try {
    cloudProbeResult.value = await getO7CloudOperatorConsoleProbe(cloudProbeBaseUrl.value);
  } catch (err) {
    cloudProbeError.value = err instanceof Error ? err.message : "cloud_operator_console_probe_api_unavailable_not_proven";
  } finally {
    cloudProbeLoading.value = false;
  }
}

async function loadCloudArchiveTasksProbe(): Promise<void> {
  // 这里只触发 PC 后端回环 probe；浏览器不直连 relay，也不读取本地 archive fixture。
  cloudArchiveProbeLoading.value = true;
  cloudArchiveProbeError.value = "";
  try {
    cloudArchiveProbeResult.value = await getO7CloudArchiveTasksProbe(cloudArchiveProbeBaseUrl.value);
  } catch (err) {
    cloudArchiveProbeError.value = err instanceof Error ? err.message : "cloud_archive_tasks_probe_api_unavailable_not_proven";
  } finally {
    cloudArchiveProbeLoading.value = false;
  }
}

async function loadRealtimeElevatorProbe(): Promise<void> {
  // 这里只触发 PC 后端回环 snapshot probe；浏览器不访问 relay，也不读取 ROS2 /tf 或地图文件。
  realtimeElevatorProbeLoading.value = true;
  realtimeElevatorProbeError.value = "";
  try {
    realtimeElevatorProbeResult.value = await getO7RealtimeElevatorProbe(realtimeElevatorProbeBaseUrl.value);
  } catch (err) {
    realtimeElevatorProbeError.value = err instanceof Error ? err.message : "realtime_elevator_probe_api_unavailable_not_proven";
  } finally {
    realtimeElevatorProbeLoading.value = false;
  }
}

async function loadPreviewsAcceptance(): Promise<void> {
  // 该按钮只加载本地 guard 摘要，不会间接执行 probe、读取 fixture、连接云端或发命令。
  previewsAcceptanceLoading.value = true;
  previewsAcceptanceError.value = "";
  try {
    previewsAcceptanceResult.value = await getO7PreviewsAcceptance();
  } catch (err) {
    previewsAcceptanceError.value = err instanceof Error ? err.message : "o7_previews_acceptance_guard_unavailable";
  } finally {
    previewsAcceptanceLoading.value = false;
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
          <h3>O7 previews acceptance guard</h3>
          <p class="eyebrow">Read-only readiness summary for local/HTTP O7 Preview software proof boundaries.</p>
        </div>
        <span class="pill danger">{{ previewsAcceptanceResult?.acceptance_verdict ?? "not_loaded" }}</span>
      </div>

      <button class="secondary" type="button" @click="loadPreviewsAcceptance">
        {{ previewsAcceptanceLoading ? "Loading previews guard" : "Load previews acceptance guard" }}
      </button>

      <div v-if="previewsAcceptanceError" class="notice" role="alert">
        O7 previews acceptance guard unavailable: {{ previewsAcceptanceError }}. safe_to_control=false.
      </div>

      <dl class="kv compact-kv">
        <dt>schema</dt>
        <dd>{{ previewsAcceptanceResult?.schema ?? "trashbot.o7.previews_acceptance.v1" }}</dd>
        <dt>guard endpoint</dt>
        <dd>{{ previewsAcceptanceResult?.guard_endpoint ?? "/api/o7/previews/acceptance" }}</dd>
        <dt>evidence boundary</dt>
        <dd>{{ previewsAcceptanceResult?.evidence_boundary ?? "software_proof_o7_previews_acceptance_guard" }}</dd>
        <dt>not real capability proof</dt>
        <dd>{{ previewsAcceptanceResult?.not_real_capability_proof ?? true }}</dd>
      </dl>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Covered surfaces</h3>
          <ul class="dense">
            <!-- surface id 由后端 guard 返回，UI 只展示覆盖面，不推断 O7 完成度。 -->
            <li v-for="surface in previewsAcceptanceResult?.surfaces ?? []" :key="surface.id">
              {{ surface.id }} · {{ surface.evidence_boundary }} · {{ surface.acceptance_status }}
            </li>
            <li v-if="!previewsAcceptanceResult?.surfaces.length">not_loaded</li>
          </ul>
          <h3>Safety invariants</h3>
          <ul class="dense">
            <!-- 固定 false 字段集中展示，提醒 operator 这些面板仍不能控制机器人。 -->
            <li v-for="field in previewsAcceptanceFalseFields()" :key="field">{{ field }}</li>
          </ul>
        </div>
        <div>
          <h3>Blocked</h3>
          <ul class="dense">
            <li v-for="reason in previewsAcceptanceBlocked()" :key="reason">{{ reason }}</li>
          </ul>
          <h3>Not proven</h3>
          <ul class="dense">
            <li v-for="item in previewsAcceptanceNotProven()" :key="item">{{ item }}</li>
          </ul>
          <h3>Software proof only</h3>
          <ul class="dense">
            <li v-for="item in previewsAcceptanceResult?.software_proof_only ?? []" :key="item">{{ item }}</li>
            <li v-if="!previewsAcceptanceResult?.software_proof_only.length">not_loaded</li>
          </ul>
        </div>
      </div>
    </article>

    <article class="snapshot-panel">
      <div class="section-head compact-head">
        <div>
          <h3>Cloud operator console probe</h3>
          <p class="eyebrow">Read-only local loopback HTTP contract proof for /api/o7/operator-console.</p>
        </div>
        <span class="pill danger">{{ cloudProbeResult?.probe_status ?? "not_loaded" }}</span>
      </div>

      <label class="single-input">
        <span>Cloud relay base URL</span>
        <input
          v-model="cloudProbeBaseUrl"
          aria-label="Cloud operator console probe base URL"
          placeholder="http://127.0.0.1:8088"
        >
      </label>
      <button class="secondary" type="button" @click="loadCloudOperatorConsoleProbe">
        {{ cloudProbeLoading ? "Loading probe" : "Probe cloud operator console" }}
      </button>

      <div v-if="cloudProbeError" class="notice" role="alert">
        Cloud operator console probe API unavailable: {{ cloudProbeError }}. primary_actions_enabled=false.
      </div>

      <dl class="kv compact-kv">
        <dt>schema</dt>
        <dd>{{ cloudProbeResult?.schema ?? "trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1" }}</dd>
        <dt>source base URL</dt>
        <dd>{{ cloudProbeResult?.source_base_url ?? "not_loaded" }}</dd>
        <dt>remote schema</dt>
        <dd>{{ cloudProbeResult?.remote_schema ?? "not_loaded" }}</dd>
        <dt>cloud API status</dt>
        <dd>{{ cloudProbeResult?.cloud_api_status ?? "not_loaded" }}</dd>
        <dt>operator mode</dt>
        <dd>{{ cloudProbeResult?.operator_mode ?? "observe_only" }}</dd>
        <dt>fail closed reason</dt>
        <dd>{{ cloudProbeResult?.fail_closed_reason ?? "probe_not_loaded" }}</dd>
        <dt>local loopback only</dt>
        <dd>{{ cloudProbeResult?.local_loopback_only ?? true }}</dd>
      </dl>

      <div class="two-col snapshot-grid">
        <div>
          <h3>KR ids</h3>
          <ul class="dense">
            <!-- KR ids 只来自远端 fail-closed contract，不代表真实 O7 能力可用。 -->
            <li v-for="krId in cloudProbeResult?.kr_ids ?? []" :key="krId">{{ krId }}</li>
            <li v-if="!cloudProbeResult?.kr_ids.length">not_loaded</li>
          </ul>
          <h3>Key false fields</h3>
          <ul class="dense">
            <!-- false 字段由 PC 后端扫描远端响应生成，危险字段 true 会整体 fail closed。 -->
            <li v-for="field in cloudProbeResult?.key_false_fields ?? []" :key="field">{{ field }}</li>
            <li v-if="!cloudProbeResult?.key_false_fields.length">not_loaded</li>
          </ul>
        </div>
        <div>
          <h3>Blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in cloudProbeBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h3>Not proven</h3>
          <ul class="dense">
            <li v-for="item in cloudProbeNotProven()" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </article>

    <article class="snapshot-panel">
      <div class="section-head compact-head">
        <div>
          <h3>Cloud archive tasks probe</h3>
          <p class="eyebrow">Read-only local loopback HTTP contract proof for /api/o7/cloud-archive/tasks.</p>
        </div>
        <span class="pill danger">{{ cloudArchiveProbeResult?.probe_status ?? "not_loaded" }}</span>
      </div>

      <label class="single-input">
        <span>Cloud relay base URL</span>
        <input
          v-model="cloudArchiveProbeBaseUrl"
          aria-label="Cloud archive tasks probe base URL"
          placeholder="http://127.0.0.1:8088"
        >
      </label>
      <button class="secondary" type="button" @click="loadCloudArchiveTasksProbe">
        {{ cloudArchiveProbeLoading ? "Loading archive probe" : "Probe cloud archive tasks" }}
      </button>

      <div v-if="cloudArchiveProbeError" class="notice" role="alert">
        Cloud archive tasks probe API unavailable: {{ cloudArchiveProbeError }}. primary_actions_enabled=false.
      </div>

      <dl class="kv compact-kv">
        <dt>schema</dt>
        <dd>{{ cloudArchiveProbeResult?.schema ?? "trashbot.pc_tools_workstation.o7_cloud_archive_tasks_probe.v1" }}</dd>
        <dt>source base URL</dt>
        <dd>{{ cloudArchiveProbeResult?.source_base_url ?? "not_loaded" }}</dd>
        <dt>remote schema</dt>
        <dd>{{ cloudArchiveProbeResult?.remote_schema ?? "not_loaded" }}</dd>
        <dt>archive status</dt>
        <dd>{{ cloudArchiveProbeResult?.archive_status ?? "not_loaded" }}</dd>
        <dt>task count</dt>
        <dd>{{ cloudArchiveProbeResult?.task_count ?? 0 }}</dd>
        <dt>selected/latest</dt>
        <dd>{{ cloudArchiveProbeResult?.selected_task_id ?? "null" }} / {{ cloudArchiveProbeResult?.latest_task_id ?? "null" }}</dd>
        <dt>fail closed reason</dt>
        <dd>{{ cloudArchiveProbeResult?.fail_closed_reason ?? "probe_not_loaded" }}</dd>
        <dt>local loopback only</dt>
        <dd>{{ cloudArchiveProbeResult?.local_loopback_only ?? true }}</dd>
      </dl>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Inspector statuses</h3>
          <ul class="dense">
            <!-- inspector 状态来自远端只读 contract，不包含样本帧、标注文本或命令 payload。 -->
            <li>route_replay={{ cloudArchiveProbeResult?.inspector_statuses.route_replay ?? "blocked_not_proven" }}</li>
            <li>labeling_queue={{ cloudArchiveProbeResult?.inspector_statuses.labeling_queue ?? "blocked_not_proven" }}</li>
            <li>voice_asr_tts={{ cloudArchiveProbeResult?.inspector_statuses.voice_asr_tts ?? "blocked_not_proven" }}</li>
            <li>safe_command={{ cloudArchiveProbeResult?.inspector_statuses.safe_command ?? "blocked_not_proven" }}</li>
          </ul>
          <h3>Inspector summaries</h3>
          <ul class="dense">
            <!-- summary 由 PC 后端白名单字段生成，保持播放、提交、TTS 和命令派发全关闭。 -->
            <li>route_replay_summary={{ cloudArchiveProbeResult?.route_replay_summary ?? "status=blocked_not_loaded; playback_available=false" }}</li>
            <li>labeling_queue_summary={{ cloudArchiveProbeResult?.labeling_queue_summary ?? "status=blocked_not_loaded; submit_enabled=false" }}</li>
            <li>voice_asr_tts_summary={{ cloudArchiveProbeResult?.voice_asr_tts_summary ?? "status=blocked_not_loaded; tts_send_enabled=false" }}</li>
            <li>safe_command_summary={{ cloudArchiveProbeResult?.safe_command_summary ?? "status=blocked_not_loaded; command_dispatch_enabled=false; robot_control_executed=false" }}</li>
          </ul>
          <h3>Dangerous true fields</h3>
          <ul class="dense">
            <li v-for="field in cloudArchiveProbeResult?.dangerous_true_fields ?? []" :key="field">{{ field }}</li>
            <li v-if="!cloudArchiveProbeResult?.dangerous_true_fields.length">none</li>
          </ul>
          <h3>Key false fields</h3>
          <ul class="dense">
            <li v-for="field in cloudArchiveProbeResult?.key_false_fields ?? []" :key="field">{{ field }}</li>
            <li v-if="!cloudArchiveProbeResult?.key_false_fields.length">not_loaded</li>
          </ul>
        </div>
        <div>
          <h3>Blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in cloudArchiveProbeBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h3>Not proven</h3>
          <ul class="dense">
            <li v-for="item in cloudArchiveProbeNotProven()" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </article>

    <article class="snapshot-panel">
      <div class="section-head compact-head">
        <div>
          <h3>Realtime/elevator cloud probe</h3>
          <p class="eyebrow">Read-only local loopback HTTP contract proof for /api/o7/realtime-elevator/snapshot.</p>
        </div>
        <span class="pill danger">{{ realtimeElevatorProbeResult?.probe_status ?? "not_loaded" }}</span>
      </div>

      <label class="single-input">
        <span>Cloud relay base URL</span>
        <input
          v-model="realtimeElevatorProbeBaseUrl"
          aria-label="Realtime elevator cloud probe base URL"
          placeholder="http://127.0.0.1:8088"
        >
      </label>
      <button class="secondary" type="button" @click="loadRealtimeElevatorProbe">
        {{ realtimeElevatorProbeLoading ? "Loading realtime/elevator probe" : "Probe realtime/elevator snapshot" }}
      </button>

      <div v-if="realtimeElevatorProbeError" class="notice" role="alert">
        Realtime/elevator probe API unavailable: {{ realtimeElevatorProbeError }}. primary_actions_enabled=false.
      </div>

      <dl class="kv compact-kv">
        <dt>schema</dt>
        <dd>{{ realtimeElevatorProbeResult?.schema ?? "trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1" }}</dd>
        <dt>source base URL</dt>
        <dd>{{ realtimeElevatorProbeResult?.source_base_url ?? "not_loaded" }}</dd>
        <dt>remote schema</dt>
        <dd>{{ realtimeElevatorProbeResult?.remote_schema ?? "not_loaded" }}</dd>
        <dt>realtime status</dt>
        <dd>{{ realtimeElevatorProbeResult?.realtime_status ?? "not_loaded" }}</dd>
        <dt>snapshot status</dt>
        <dd>{{ realtimeElevatorProbeResult?.snapshot_status ?? "not_loaded" }}</dd>
        <dt>map ref</dt>
        <dd>{{ realtimeElevatorProbeResult?.map_ref_summary ?? "not_loaded" }}</dd>
        <dt>map frame</dt>
        <dd>{{ realtimeElevatorProbeResult?.map_frame_summary ?? "not_loaded" }}</dd>
        <dt>robot pose</dt>
        <dd>{{ realtimeElevatorProbeResult?.robot_pose_summary ?? "blocked_not_proven" }}</dd>
        <dt>pose freshness</dt>
        <dd>{{ realtimeElevatorProbeResult?.pose_freshness_summary ?? "blocked_not_proven" }}</dd>
        <dt>elevator status</dt>
        <dd>{{ realtimeElevatorProbeResult?.elevator_status ?? "blocked_not_proven" }}</dd>
        <dt>current floor evidence</dt>
        <dd>{{ realtimeElevatorProbeResult?.current_floor_evidence_summary ?? "blocked_not_proven" }}</dd>
        <dt>human takeover</dt>
        <dd>{{ realtimeElevatorProbeResult?.human_takeover_summary ?? "blocked_not_proven" }}</dd>
        <dt>fail closed reason</dt>
        <dd>{{ realtimeElevatorProbeResult?.fail_closed_reason ?? "probe_not_loaded" }}</dd>
        <dt>local loopback only</dt>
        <dd>{{ realtimeElevatorProbeResult?.local_loopback_only ?? true }}</dd>
      </dl>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Route membership false fields</h3>
          <ul class="dense">
            <!-- 路线与电梯区域成员关系由后端扫描远端 snapshot 后固定展示 false。 -->
            <li v-for="field in realtimeElevatorProbeResult?.route_membership_false_fields ?? []" :key="field">
              {{ field }}
            </li>
            <li v-if="!realtimeElevatorProbeResult?.route_membership_false_fields.length">not_loaded</li>
          </ul>
          <h3>Dangerous true fields</h3>
          <ul class="dense">
            <li v-for="field in realtimeElevatorProbeResult?.dangerous_true_fields ?? []" :key="field">{{ field }}</li>
            <li v-if="!realtimeElevatorProbeResult?.dangerous_true_fields.length">none</li>
          </ul>
          <h3>Key false fields</h3>
          <ul class="dense">
            <li v-for="field in realtimeElevatorProbeResult?.key_false_fields ?? []" :key="field">{{ field }}</li>
            <li v-if="!realtimeElevatorProbeResult?.key_false_fields.length">not_loaded</li>
          </ul>
        </div>
        <div>
          <h3>Elevator state samples</h3>
          <ul class="dense">
            <!-- 后端已经限量并白名单化 sample，UI 只负责展示摘要，不提供播放或控制入口。 -->
            <li v-for="sample in realtimeElevatorProbeResult?.elevator_state_samples_summary ?? []" :key="sample">
              {{ sample }}
            </li>
            <li v-if="!realtimeElevatorProbeResult?.elevator_state_samples_summary.length">not_loaded</li>
          </ul>
          <h3>Blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in realtimeElevatorProbeBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h3>Not proven</h3>
          <ul class="dense">
            <li v-for="item in realtimeElevatorProbeNotProven()" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </article>

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

      <h3>Local route replay player</h3>
      <div class="notice" role="note">
        local_fixture_cursor_only · sends_to_robot=false · safe_to_control=false · delivery_success=false ·
        primary_actions_enabled=false · cursor_initial_state.safe_to_play=false
      </div>
      <dl class="kv compact-kv">
        <dt>cursor_status</dt>
        <dd>{{ routeReplayNavigationEnabled ? "local_fixture_cursor_ready" : "blocked_not_proven" }}</dd>
        <dt>blocked_reason</dt>
        <dd>{{ routeReplayBlockedReason || "none_local_fixture_only" }}</dd>
        <dt>current frame</dt>
        <dd>{{ routeReplayCursorDisplay() }}</dd>
        <dt>frame_index</dt>
        <dd>{{ currentRouteReplayFrame?.frame_index ?? "blocked_not_proven" }}</dd>
        <dt>timestamp_ms</dt>
        <dd>{{ currentRouteReplayFrame?.timestamp_ms ?? "null" }}</dd>
        <dt>pose</dt>
        <dd>
          x={{ currentRouteReplayFrame?.x_m ?? "null" }},
          y={{ currentRouteReplayFrame?.y_m ?? "null" }},
          yaw={{ currentRouteReplayFrame?.yaw_rad ?? "null" }}
        </dd>
        <dt>velocity</dt>
        <dd>{{ currentRouteReplayFrame?.speed_mps ?? "null" }} mps</dd>
        <dt>state</dt>
        <dd>{{ currentRouteReplayFrame?.state ?? "blocked_not_proven" }}</dd>
        <dt>evidence_ref</dt>
        <dd>{{ currentRouteReplayFrame?.evidence_ref ?? "blocked_not_proven" }}</dd>
      </dl>
      <div class="route-inputs">
        <!-- 这些按钮只改变本地数组下标，不调用 API，也不代表真实云回放或机器人运动。 -->
        <button
          class="secondary"
          type="button"
          :disabled="!routeReplayNavigationEnabled || routeReplayCursor <= 0"
          @click="previousRouteReplayFrame"
        >
          Previous frame
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!routeReplayNavigationEnabled || routeReplayCursor >= routeReplayFrames.length - 1"
          @click="nextRouteReplayFrame"
        >
          Next frame
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!routeReplayNavigationEnabled"
          @click="resetRouteReplayCursor"
        >
          Reset cursor
        </button>
      </div>
      <label class="single-input">
        <span>Frame cursor</span>
        <input
          aria-label="Local route replay frame cursor"
          type="range"
          min="0"
          :max="Math.max(routeReplayFrames.length - 1, 0)"
          :value="routeReplayCursor"
          :disabled="!routeReplayNavigationEnabled"
          @input="setRouteReplayCursorFromInput"
        >
      </label>

      <h3>Route replay trajectory minimap</h3>
      <div class="notice" role="note">
        readonly_fixture_svg_only · no_real_map_loaded · no_robot_motion_claim · safe_to_control=false ·
        playback_available=false · robot_control_executed=false
      </div>
      <div class="two-col snapshot-grid">
        <div>
          <svg
            aria-label="Route replay trajectory minimap"
            role="img"
            viewBox="0 0 100 100"
            width="100%"
            height="220"
            preserveAspectRatio="xMidYMid meet"
            style="display: block; width: 100%; min-height: 220px; border: 1px solid #d7dee6; border-radius: 6px; background: #f7f9fb;"
          >
            <!-- SVG 只消费 sample_frames 的 x_m/y_m，固定 viewBox 防止极端坐标改变布局。 -->
            <rect x="10" y="10" width="80" height="80" fill="#ffffff" stroke="#d7dee6" stroke-width="0.8" />
            <line x1="10" y1="50" x2="90" y2="50" stroke="#d7dee6" stroke-width="0.4" />
            <line x1="50" y1="10" x2="50" y2="90" stroke="#d7dee6" stroke-width="0.4" />
            <polyline
              v-if="routeReplayMinimapStatus === 'readonly_fixture_trajectory_ready'"
              :points="routeReplayMinimapPolyline"
              fill="none"
              stroke="#315f8a"
              stroke-width="2.4"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <circle
              v-for="point in routeReplayMinimapPoints"
              :key="`${point.cursor_index}:${point.frame_index}`"
              :cx="point.svg_x"
              :cy="point.svg_y"
              r="1.8"
              fill="#5f6b7a"
            />
            <circle
              v-if="routeReplayMinimapStatus === 'readonly_fixture_trajectory_ready' && currentRouteReplayMinimapMarker"
              :cx="currentRouteReplayMinimapMarker.svg_x"
              :cy="currentRouteReplayMinimapMarker.svg_y"
              r="4"
              fill="#9a3412"
              stroke="#ffffff"
              stroke-width="1.4"
            />
            <text
              v-if="routeReplayMinimapStatus !== 'readonly_fixture_trajectory_ready'"
              x="50"
              y="50"
              text-anchor="middle"
              dominant-baseline="middle"
              fill="#8a1f1f"
              font-size="6"
            >
              blocked_not_proven
            </text>
            <text
              v-else-if="!currentRouteReplayMinimapMarker"
              x="50"
              y="50"
              text-anchor="middle"
              dominant-baseline="middle"
              fill="#8a1f1f"
              font-size="5"
            >
              current_marker_unknown
            </text>
          </svg>
        </div>
        <div>
          <dl class="kv compact-kv">
            <dt>minimap_status</dt>
            <dd>{{ routeReplayMinimapStatus }}</dd>
            <dt>trajectory_points</dt>
            <dd>{{ routeReplayTrajectoryPoints.length }}</dd>
            <dt>map_frame</dt>
            <dd>{{ archiveResult?.route_replay_inspector.map_frame ?? "blocked_not_proven" }}</dd>
            <dt>current_marker</dt>
            <dd>{{ routeReplayCurrentMarkerStatus }}</dd>
            <dt>safe_to_control</dt>
            <dd>false</dd>
            <dt>playback_available</dt>
            <dd>false</dd>
            <dt>robot_control_executed</dt>
            <dd>false</dd>
          </dl>
        </div>
      </div>

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

      <h3>Local labeling review panel</h3>
      <div class="notice" role="note">
        local_fixture_item_cursor_only · submit_enabled=false · rollback_enabled=false ·
        dataset_export_available=false · real_annotation_api_connected=false ·
        draft_labels.autosave_available=false
      </div>
      <dl class="kv compact-kv">
        <dt>cursor_status</dt>
        <dd>{{ labelingReviewNavigationEnabled ? "local_fixture_item_cursor_ready" : "blocked_not_proven" }}</dd>
        <dt>blocked_reason</dt>
        <dd>{{ labelingReviewBlockedReason || "none_local_fixture_only" }}</dd>
        <dt>current item</dt>
        <dd>{{ labelingReviewCursorDisplay() }}</dd>
        <dt>item_id</dt>
        <dd>{{ currentLabelingReviewItem?.item_id ?? "blocked_not_proven" }}</dd>
        <dt>frame_id</dt>
        <dd>{{ currentLabelingReviewItem?.frame_id ?? "blocked_not_proven" }}</dd>
        <dt>media_ref</dt>
        <dd>{{ currentLabelingReviewItem?.media_ref ?? "blocked_not_proven" }}</dd>
        <dt>evidence_ref</dt>
        <dd>{{ currentLabelingReviewItem?.evidence_ref ?? "blocked_not_proven" }}</dd>
        <dt>current label count</dt>
        <dd>{{ currentLabelingReviewItem?.current_labels.count ?? 0 }}</dd>
        <dt>current label sample</dt>
        <dd><code>{{ jsonSummary(currentLabelingReviewItem?.current_labels.sample ?? []) }}</code></dd>
        <dt>draft label sample</dt>
        <dd><code>{{ jsonSummary(archiveResult?.labeling_queue_inspector.draft_labels.sample ?? []) }}</code></dd>
        <dt>allowed label types</dt>
        <dd><code>{{ jsonSummary(archiveResult?.labeling_queue_inspector.allowed_label_types ?? []) }}</code></dd>
        <dt>label schema</dt>
        <dd><code>{{ jsonSummary(archiveResult?.labeling_queue_inspector.label_schema) }}</code></dd>
      </dl>
      <div class="route-inputs">
        <!-- 这些按钮只改变本地 item cursor，不调用 API，也不会提交、回滚或导出任何标注数据。 -->
        <button
          class="secondary"
          type="button"
          :disabled="!labelingReviewNavigationEnabled || labelingReviewCursor <= 0"
          @click="previousLabelingReviewItem"
        >
          Previous item
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!labelingReviewNavigationEnabled || labelingReviewCursor >= labelingReviewItems.length - 1"
          @click="nextLabelingReviewItem"
        >
          Next item
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!labelingReviewNavigationEnabled"
          @click="resetLabelingReviewCursor"
        >
          Reset item
        </button>
      </div>

      <h3>Local draft annotation editor</h3>
      <div class="notice" role="note">
        browser_memory_only · submit_enabled=false · autosave_available=false ·
        real_annotation_api_connected=false · dataset_export_available=false · cloud_write_executed=false
      </div>
      <dl class="kv compact-kv">
        <dt>current item</dt>
        <dd>{{ currentLabelingReviewItem?.item_id ?? "blocked_not_proven" }}</dd>
        <dt>draft status</dt>
        <dd>{{ localDraftStatus }}</dd>
        <dt>selected label type</dt>
        <dd>{{ currentLocalAnnotationDraft.labelType || "blocked_not_proven" }}</dd>
        <dt>confidence</dt>
        <dd>{{ currentLocalAnnotationDraft.confidence }}</dd>
        <dt>note/metadata summary</dt>
        <dd>{{ localDraftNoteSummary }}</dd>
        <dt>validation status</dt>
        <dd>{{ localDraftValidationStatus }}</dd>
        <dt>blocked reason</dt>
        <dd>{{ localDraftEditorBlockedReason || "none_local_memory_only" }}</dd>
        <dt>submit_enabled</dt>
        <dd>false</dd>
        <dt>autosave_available</dt>
        <dd>false</dd>
        <dt>real_annotation_api_connected</dt>
        <dd>false</dd>
        <dt>dataset_export_available</dt>
        <dd>false</dd>
        <dt>cloud_write_executed</dt>
        <dd>false</dd>
      </dl>
      <div class="two-col snapshot-grid">
        <label class="single-input">
          <span>Selected label type</span>
          <select
            aria-label="Local draft annotation label type"
            :value="currentLocalAnnotationDraft.labelType"
            :disabled="!localDraftInputsEnabled"
            @change="setLocalDraftLabelType"
          >
            <!-- label type 严格来自 allowed_label_types；列表为空时整个 editor fail-closed。 -->
            <option v-for="labelType in localDraftAllowedLabelTypes" :key="labelType" :value="labelType">
              {{ labelType }}
            </option>
          </select>
        </label>
        <label class="single-input">
          <span>Confidence</span>
          <input
            aria-label="Local draft annotation confidence"
            :value="currentLocalAnnotationDraft.confidence"
            :disabled="!localDraftInputsEnabled"
            inputmode="decimal"
            placeholder="0..1"
            @input="setLocalDraftConfidence"
          >
        </label>
      </div>
      <label class="single-input">
        <span>Note</span>
        <textarea
          aria-label="Local draft annotation note"
          :value="currentLocalAnnotationDraft.note"
          :disabled="!localDraftInputsEnabled"
          rows="3"
          placeholder="local note only; no API call"
          @input="setLocalDraftNote"
        />
      </label>
      <div class="route-inputs">
        <!-- reset 只清当前 item 的内存草稿，不新增保存、提交或导出入口。 -->
        <button
          class="secondary"
          type="button"
          :disabled="!localDraftInputsEnabled"
          @click="resetLocalAnnotationDraft"
        >
          Reset draft
        </button>
      </div>

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

      <h3>Local voice ASR/TTS monitor panel</h3>
      <div class="notice" role="note">
        local_fixture_voice_monitor_only · asr_stream_connected=false · tts_send_enabled=false ·
        speaker_dispatch_enabled=false · real_voice_api_connected=false ·
        real_asr_tts_runtime_connected=false · speaker_dispatch.sends_to_robot=false
      </div>
      <dl class="kv compact-kv">
        <dt>panel_status</dt>
        <dd>{{ voiceMonitorPanelStatus }}</dd>
        <dt>blocked_reason</dt>
        <dd>{{ voiceMonitorBlockedReason || "none_local_fixture_only" }}</dd>
        <dt>current ASR event</dt>
        <dd>{{ voiceAsrCursorDisplay() }}</dd>
        <dt>event_type</dt>
        <dd>{{ currentVoiceAsrEvent?.event_type ?? "blocked_not_proven" }}</dd>
        <dt>timestamp_ms</dt>
        <dd>{{ currentVoiceAsrEvent?.timestamp_ms ?? "null" }}</dd>
        <dt>transcript</dt>
        <dd>{{ currentVoiceAsrEvent?.transcript ?? "blocked_not_proven" }}</dd>
        <dt>confidence</dt>
        <dd>{{ currentVoiceAsrEvent?.confidence ?? "null" }}</dd>
        <dt>evidence_ref</dt>
        <dd>{{ currentVoiceAsrEvent?.evidence_ref ?? "blocked_not_proven" }}</dd>
      </dl>
      <div class="route-inputs">
        <!-- 这些按钮只改变本地 ASR event cursor，不连接真实 ASR，也不会发送、播放或派发 TTS。 -->
        <button
          class="secondary"
          type="button"
          :disabled="!voiceAsrNavigationEnabled || voiceAsrEventCursor <= 0"
          @click="previousVoiceAsrEvent"
        >
          Previous ASR event
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!voiceAsrNavigationEnabled || voiceAsrEventCursor >= voiceAsrEvents.length - 1"
          @click="nextVoiceAsrEvent"
        >
          Next ASR event
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!voiceAsrNavigationEnabled"
          @click="resetVoiceAsrEventCursor"
        >
          Reset ASR cursor
        </button>
      </div>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Partial/final comparison</h3>
          <dl class="kv compact-kv">
            <dt>latest_partial.text</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.latest_partial.text ?? "" }}</dd>
            <dt>latest_partial.timestamp_ms</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.latest_partial.timestamp_ms ?? "null" }}</dd>
            <dt>latest_partial.confidence</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.latest_partial.confidence ?? "null" }}</dd>
            <dt>latest_partial.evidence_ref</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.latest_partial.evidence_ref ?? "blocked_not_proven" }}</dd>
            <dt>latest_final.text</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.latest_final.text ?? "" }}</dd>
            <dt>latest_final.timestamp_ms</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.latest_final.timestamp_ms ?? "null" }}</dd>
            <dt>latest_final.confidence</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.latest_final.confidence ?? "null" }}</dd>
            <dt>latest_final.evidence_ref</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.latest_final.evidence_ref ?? "blocked_not_proven" }}</dd>
          </dl>
        </div>
        <div>
          <h3>Readonly TTS draft review</h3>
          <dl class="kv compact-kv">
            <dt>tts_draft.text</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.text ?? "" }}</dd>
            <dt>tts_draft.text_length</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.text_length ?? 0 }}</dd>
            <dt>tts_draft.voice_profile</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.voice_profile ?? "not_loaded" }}</dd>
            <dt>tts_draft.language</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.language ?? "not_loaded" }}</dd>
            <dt>tts_draft.confirmation_required</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.confirmation_required ?? true }}</dd>
            <dt>tts_draft.status</dt>
            <dd>{{ archiveResult?.voice_asr_tts_inspector.tts_draft.status ?? "blocked_not_proven" }}</dd>
          </dl>
        </div>
      </div>

      <h3>Local TTS draft editor</h3>
      <div class="notice" role="note">
        browser_memory_only · confirmation_required=true · tts_send_enabled=false · playback_available=false ·
        speaker_dispatch_enabled=false · real_voice_api_connected=false · real_asr_tts_runtime_connected=false ·
        speaker_dispatch.sends_to_robot=false · cloud_write_executed=false
      </div>
      <dl class="kv compact-kv">
        <dt>draft status</dt>
        <dd>{{ localTtsDraftStatus }}</dd>
        <dt>source transcript summary</dt>
        <dd>{{ localTtsSourceTranscriptSummary }}</dd>
        <dt>draft text length</dt>
        <dd>{{ localTtsDraftTextLength }}</dd>
        <dt>voice profile</dt>
        <dd>{{ currentLocalTtsDraft.voiceProfile || "blocked_not_proven" }}</dd>
        <dt>language</dt>
        <dd>{{ currentLocalTtsDraft.language || "blocked_not_proven" }}</dd>
        <dt>validation status</dt>
        <dd>{{ localTtsDraftValidationStatus }}</dd>
        <dt>blocked reason</dt>
        <dd>{{ voiceMonitorBlockedReason || "none_local_memory_only" }}</dd>
        <dt>confirmation_required</dt>
        <dd>true</dd>
        <dt>tts_send_enabled</dt>
        <dd>false</dd>
        <dt>playback_available</dt>
        <dd>false</dd>
        <dt>speaker_dispatch_enabled</dt>
        <dd>false</dd>
        <dt>real_voice_api_connected</dt>
        <dd>false</dd>
        <dt>real_asr_tts_runtime_connected</dt>
        <dd>false</dd>
        <dt>speaker_dispatch.sends_to_robot</dt>
        <dd>false</dd>
        <dt>cloud_write_executed</dt>
        <dd>false</dd>
      </dl>
      <label class="single-input">
        <span>Draft text</span>
        <textarea
          aria-label="Local TTS draft text"
          :value="currentLocalTtsDraft.text"
          :disabled="!localTtsDraftInputsEnabled"
          rows="3"
          maxlength="160"
          placeholder="1..120 chars, local browser memory only"
          @input="setLocalTtsDraftText"
        />
      </label>
      <div class="two-col snapshot-grid">
        <label class="single-input">
          <span>Voice profile</span>
          <input
            aria-label="Local TTS voice profile"
            :value="currentLocalTtsDraft.voiceProfile"
            :disabled="!localTtsDraftInputsEnabled"
            placeholder="voice profile from fixture"
            @input="setLocalTtsVoiceProfile"
          >
        </label>
        <label class="single-input">
          <span>Language</span>
          <input
            aria-label="Local TTS language"
            :value="currentLocalTtsDraft.language"
            :disabled="!localTtsDraftInputsEnabled"
            placeholder="language from fixture"
            @input="setLocalTtsLanguage"
          >
        </label>
      </div>
      <div class="route-inputs">
        <!-- reset 只清除本地覆盖值，不新增发送、播放、保存或云写入口。 -->
        <button
          class="secondary"
          type="button"
          :disabled="!localTtsDraftInputsEnabled"
          @click="resetLocalTtsDraft"
        >
          Reset TTS draft
        </button>
      </div>

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

      <h3>Safe command inspector</h3>
      <dl class="kv compact-kv">
        <dt>status</dt>
        <dd>{{ archiveResult?.safe_command_inspector.status ?? "blocked_not_proven" }}</dd>
        <dt>selected_task_id</dt>
        <dd>{{ archiveResult?.safe_command_inspector.selected_task_id ?? "null" }}</dd>
        <dt>command_count</dt>
        <dd>{{ archiveResult?.safe_command_inspector.command_count ?? 0 }}</dd>
        <dt>command_session</dt>
        <dd><code>{{ jsonSummary(archiveResult?.safe_command_inspector.command_session) }}</code></dd>
      </dl>

      <h3>Local safe command review panel</h3>
      <div class="notice" role="note">
        local_fixture_command_cursor_only · command_dispatch_enabled=false · manual_control_enabled=false ·
        navigate_goal_enabled=false · keyboard_control_enabled=false · safe_to_control=false · delivery_success=false ·
        primary_actions_enabled=false
      </div>
      <dl class="kv compact-kv">
        <dt>panel_status</dt>
        <dd>{{ safeCommandReviewPanelStatus }}</dd>
        <dt>blocked_reason</dt>
        <dd>{{ safeCommandReviewBlockedReason || "none_local_fixture_only" }}</dd>
        <dt>current command</dt>
        <dd>{{ safeCommandCursorDisplay() }}</dd>
        <dt>command_id</dt>
        <dd>{{ currentSafeCommandSample?.command_id ?? "blocked_not_proven" }}</dd>
        <dt>command_type</dt>
        <dd>{{ currentSafeCommandSample?.command_type ?? "blocked_not_proven" }}</dd>
        <dt>status</dt>
        <dd>{{ currentSafeCommandSample?.status ?? "blocked_not_proven" }}</dd>
        <dt>envelope_ref</dt>
        <dd>{{ currentSafeCommandSample?.envelope_ref ?? "blocked_not_proven" }}</dd>
        <dt>idempotency_key_ref</dt>
        <dd>{{ currentSafeCommandSample?.idempotency_key_ref ?? "blocked_not_proven" }}</dd>
        <dt>evidence_ref</dt>
        <dd>{{ currentSafeCommandSample?.evidence_ref ?? "blocked_not_proven" }}</dd>
      </dl>
      <div class="route-inputs">
        <!-- 这些按钮只改变本地 command cursor，不调用 API、不写后端、不发送机器人命令。 -->
        <button
          class="secondary"
          type="button"
          :disabled="!safeCommandNavigationEnabled || safeCommandCursor <= 0"
          @click="previousSafeCommand"
        >
          Previous command
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!safeCommandNavigationEnabled || safeCommandCursor >= safeCommandSamples.length - 1"
          @click="nextSafeCommand"
        >
          Next command
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!safeCommandNavigationEnabled"
          @click="resetSafeCommandCursor"
        >
          Reset command cursor
        </button>
      </div>

      <h3>Local safe command draft editor</h3>
      <div class="notice" role="note">
        local_browser_memory_only · confirmation_required=true · command_dispatch_enabled=false ·
        manual_control_enabled=false · navigate_goal_enabled=false · keyboard_control_enabled=false ·
        safe_to_control=false
      </div>
      <dl class="kv compact-kv">
        <dt>draft status</dt>
        <dd>{{ localSafeCommandDraftStatus }}</dd>
        <dt>blocked_reason</dt>
        <dd>{{ safeCommandDraftEditorBlockedReason || "none_local_fixture_only" }}</dd>
        <dt>command mode</dt>
        <dd>{{ currentLocalSafeCommandDraft.commandMode }}</dd>
        <dt>validation status</dt>
        <dd>{{ localSafeCommandDraftValidationStatus }}</dd>
        <dt>manual direction</dt>
        <dd>{{ currentLocalSafeCommandDraft.manualDirection || "blocked_not_proven" }}</dd>
        <dt>allowed directions</dt>
        <dd><code>{{ jsonSummary(safeCommandAllowedManualDirections) }}</code></dd>
        <dt>target summary</dt>
        <dd>{{ localSafeCommandTargetSummary }}</dd>
        <dt>idempotency draft/ref</dt>
        <dd>{{ currentLocalSafeCommandDraft.idempotencyDraftRef || "blocked_not_proven" }}</dd>
        <dt>confirmation_required</dt>
        <dd>true</dd>
        <dt>command_dispatch_enabled</dt>
        <dd>false</dd>
        <dt>manual_control_enabled</dt>
        <dd>false</dd>
        <dt>navigate_goal_enabled</dt>
        <dd>false</dd>
        <dt>keyboard_control_enabled</dt>
        <dd>false</dd>
        <dt>real_command_api_connected</dt>
        <dd>false</dd>
        <dt>real_robot_ack_connected</dt>
        <dd>false</dd>
        <dt>robot_control_executed</dt>
        <dd>false</dd>
        <dt>safe_to_control</dt>
        <dd>false</dd>
        <dt>cloud_write_executed</dt>
        <dd>false</dd>
      </dl>
      <div class="two-col snapshot-grid">
        <div>
          <label class="single-input">
            <span>Command mode</span>
            <select
              :value="currentLocalSafeCommandDraft.commandMode"
              aria-label="Local safe command mode"
              :disabled="!safeCommandDraftInputsEnabled"
              @change="setLocalSafeCommandMode"
            >
              <option value="manual_turn">manual_turn</option>
              <option value="navigate_goal">navigate_goal</option>
            </select>
          </label>
          <label class="single-input">
            <span>Manual direction</span>
            <input
              :value="currentLocalSafeCommandDraft.manualDirection"
              aria-label="Local safe command manual direction"
              :disabled="!safeCommandDraftInputsEnabled"
              @input="setLocalSafeCommandDirection"
            >
          </label>
          <label class="single-input">
            <span>Idempotency key note / draft ref</span>
            <input
              :value="currentLocalSafeCommandDraft.idempotencyDraftRef"
              aria-label="Local safe command idempotency draft ref"
              :disabled="!safeCommandDraftInputsEnabled"
              @input="setLocalSafeCommandIdempotencyDraftRef"
            >
          </label>
        </div>
        <div>
          <label class="single-input">
            <span>Target x</span>
            <input
              :value="currentLocalSafeCommandDraft.targetX"
              aria-label="Local safe command target x"
              :disabled="!safeCommandDraftInputsEnabled"
              inputmode="decimal"
              @input="setLocalSafeCommandTargetX"
            >
          </label>
          <label class="single-input">
            <span>Target y</span>
            <input
              :value="currentLocalSafeCommandDraft.targetY"
              aria-label="Local safe command target y"
              :disabled="!safeCommandDraftInputsEnabled"
              inputmode="decimal"
              @input="setLocalSafeCommandTargetY"
            >
          </label>
          <label class="single-input">
            <span>Target yaw</span>
            <input
              :value="currentLocalSafeCommandDraft.targetYaw"
              aria-label="Local safe command target yaw"
              :disabled="!safeCommandDraftInputsEnabled"
              inputmode="decimal"
              @input="setLocalSafeCommandTargetYaw"
            >
          </label>
        </div>
      </div>
      <div class="route-inputs">
        <button
          class="secondary"
          type="button"
          :disabled="!safeCommandDraftInputsEnabled"
          @click="resetLocalSafeCommandDraft"
        >
          Reset command draft
        </button>
      </div>

      <h3>Sample commands</h3>
      <table>
        <thead>
          <tr>
            <th>command_id</th>
            <th>command_type</th>
            <th>status</th>
            <th>envelope_ref</th>
            <th>idempotency_key_ref</th>
            <th>evidence_ref</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!archiveResult?.safe_command_inspector.sample_commands.length">
            <td colspan="6">blocked_not_proven</td>
          </tr>
          <tr
            v-for="command in archiveResult?.safe_command_inspector.sample_commands ?? []"
            :key="`${command.command_id}:${command.command_type}:${command.evidence_ref}`"
          >
            <td>{{ command.command_id }}</td>
            <td>{{ command.command_type }}</td>
            <td>{{ command.status }}</td>
            <td>{{ command.envelope_ref }}</td>
            <td>{{ command.idempotency_key_ref }}</td>
            <td>{{ command.evidence_ref }}</td>
          </tr>
        </tbody>
      </table>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Manual turn envelope</h3>
          <dl class="kv compact-kv">
            <dt>requested_direction</dt>
            <dd>{{ archiveResult?.safe_command_inspector.manual_turn_envelope.requested_direction ?? "not_loaded" }}</dd>
            <dt>sends_to_robot</dt>
            <dd>{{ archiveResult?.safe_command_inspector.manual_turn_envelope.sends_to_robot ?? false }}</dd>
            <dt>velocity_limited</dt>
            <dd>{{ archiveResult?.safe_command_inspector.manual_turn_envelope.velocity_limited ?? true }}</dd>
            <dt>steering_limited</dt>
            <dd>{{ archiveResult?.safe_command_inspector.manual_turn_envelope.steering_limited ?? true }}</dd>
            <dt>evidence_ref</dt>
            <dd>
              {{
                archiveResult?.safe_command_inspector.manual_turn_envelope.evidence_ref ??
                  "missing_manual_turn_command_envelope_trace"
              }}
            </dd>
          </dl>
          <h3>Navigate goal envelope</h3>
          <dl class="kv compact-kv">
            <dt>goal_source</dt>
            <dd>{{ archiveResult?.safe_command_inspector.navigate_goal_envelope.goal_source ?? "not_loaded" }}</dd>
            <dt>sends_to_robot</dt>
            <dd>{{ archiveResult?.safe_command_inspector.navigate_goal_envelope.sends_to_robot ?? false }}</dd>
            <dt>map_frame</dt>
            <dd>{{ archiveResult?.safe_command_inspector.navigate_goal_envelope.map_frame ?? "map" }}</dd>
            <dt>x/y/yaw</dt>
            <dd>
              x={{ archiveResult?.safe_command_inspector.navigate_goal_envelope.x_m ?? "null" }}
              · y={{ archiveResult?.safe_command_inspector.navigate_goal_envelope.y_m ?? "null" }}
              · yaw={{ archiveResult?.safe_command_inspector.navigate_goal_envelope.yaw_rad ?? "null" }}
            </dd>
            <dt>evidence_ref</dt>
            <dd>
              {{
                archiveResult?.safe_command_inspector.navigate_goal_envelope.evidence_ref ??
                  "missing_navigate_goal_command_envelope_trace"
              }}
            </dd>
          </dl>
        </div>
        <div>
          <h3>Limits and map goal slot</h3>
          <dl class="kv compact-kv">
            <dt>velocity_limits</dt>
            <dd><code>{{ jsonSummary(archiveResult?.safe_command_inspector.velocity_limits) }}</code></dd>
            <dt>steering_limits</dt>
            <dd><code>{{ jsonSummary(archiveResult?.safe_command_inspector.steering_limits) }}</code></dd>
            <dt>map_goal_slot</dt>
            <dd><code>{{ jsonSummary(archiveResult?.safe_command_inspector.map_goal_slot) }}</code></dd>
          </dl>
          <h3>Idempotency and confirmation</h3>
          <dl class="kv compact-kv">
            <dt>idempotency_key_requirement</dt>
            <dd><code>{{ jsonSummary(archiveResult?.safe_command_inspector.idempotency_key_requirement) }}</code></dd>
            <dt>confirmation_policy</dt>
            <dd><code>{{ jsonSummary(archiveResult?.safe_command_inspector.confirmation_policy) }}</code></dd>
            <dt>robot_ack_blocked_summary</dt>
            <dd><code>{{ jsonSummary(archiveResult?.safe_command_inspector.robot_ack_blocked_summary) }}</code></dd>
            <dt>evidence_gaps</dt>
            <dd><code>{{ jsonSummary(archiveResult?.safe_command_inspector.evidence_gaps ?? []) }}</code></dd>
          </dl>
          <h3>Safe command false fields</h3>
          <ul class="dense">
            <!-- KR6 false fields 直接来自 inspector，UI 不能根据 command 样本生成控制入口。 -->
            <li v-for="field in safeCommandFalseFields(archiveResult)" :key="field">{{ field }}</li>
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
