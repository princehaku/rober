<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import {
  getO7CloudArchiveTasks,
  getO7CloudArchiveTasksProbe,
  getO7CloudOperatorConsoleProbe,
  getO7ConsumerTaskDetail,
  getO7ConsumerTaskList,
  getO7LiveEndpointsManifest,
  getO7PreviewsAcceptance,
  getO7RealtimeElevatorProbe,
  getO7RtcSignalingContractProbe,
  loadO7FixturePreview,
} from "../client/workstationApi";
import type { O7FixturePreviewInputs, O7FixturePreviewKind, O7FixturePreviewResponses } from "../client/workstationApi";
import type {
  O7CloudArchiveTasksProbeResponse,
  O7CloudArchiveTasksResponse,
  O7FieldEvidenceConsumerIngestResponse,
  O7ConsumerTaskDetailResponse,
  O7ConsumerTaskListResponse,
  O7LabelingQueueInspectorReviewItem,
  O7LiveEndpointsManifestResponse,
  O7PreviewsAcceptanceResponse,
  O7PreviewsAcceptanceSurface,
  O7PreviewsAcceptanceSurfaceId,
  O7SafeCommandInspectorCommandSample,
  O7VoiceAsrTtsInspectorAsrEvent,
  O7CloudOperatorConsoleProbeResponse,
  O7RealtimeElevatorProbeResponse,
  O7RtcSignalingContractProbeResponse,
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

interface RouteReplayDetailFrame {
  frame_index: number;
  cursor_index: number;
  timestamp_ms: number | null;
  x_m: number | null;
  y_m: number | null;
  yaw_rad: number | null;
  speed_mps: number | null;
  state: string;
  evidence_ref: string;
}

interface RealtimePosePreview {
  x_m: number;
  y_m: number;
  yaw_rad: number;
  svg_x: number;
  svg_y: number;
  heading_x: number;
  heading_y: number;
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

interface O7ReadinessGapGroupConfig {
  krId: string;
  krName: string;
  surfaceIds: O7PreviewsAcceptanceSurfaceId[];
}

interface O7ReadinessGapGroup {
  krId: string;
  krName: string;
  matchedSurfaceCount: number;
  surfaceIds: string[];
  blockedReasons: string[];
  notProven: string[];
  readyForRealOperation: false;
}

const previewConfigs: PreviewConfig[] = [
  // 五个入口均为 PC-only fixture preview，不映射成机器人动作。
  { id: "realtimeElevator", title: "Realtime/Elevator", expectedSchema: "trashbot.o7.realtime_elevator_preview.v1" },
  { id: "routeReplay", title: "Route Replay", expectedSchema: "trashbot.o7.route_replay_preview.v1" },
  { id: "labeling", title: "Labeling", expectedSchema: "trashbot.o7.labeling_preview.v1" },
  { id: "voice", title: "Voice", expectedSchema: "trashbot.o7.voice_preview.v1" },
  { id: "safeCommand", title: "Safe Command", expectedSchema: "trashbot.o7.safe_command_preview.v1" },
];

const o7ReadinessGapGroups: O7ReadinessGapGroupConfig[] = [
  {
    krId: "O7-KR1",
    krName: "realtime map/pose",
    surfaceIds: ["realtime_elevator_probe", "realtime_map_pose_preview"],
  },
  {
    krId: "O7-KR2",
    krName: "elevator state",
    surfaceIds: ["realtime_elevator_probe", "elevator_state_timeline_preview"],
  },
  {
    krId: "O7-KR3",
    krName: "route replay",
    surfaceIds: ["route_replay_player", "route_replay_trajectory_minimap"],
  },
  {
    krId: "O7-KR4",
    krName: "labeling",
    surfaceIds: ["labeling_review_panel", "local_draft_annotation_editor"],
  },
  {
    krId: "O7-KR5",
    krName: "ASR/TTS",
    surfaceIds: ["voice_monitor_panel", "local_tts_draft_editor"],
  },
  {
    krId: "O7-KR6",
    krName: "command",
    surfaceIds: ["safe_command_review_panel", "local_safe_command_draft_editor"],
  },
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
const consumerReadBaseUrl = ref("http://127.0.0.1:8088");
const consumerTaskListResult = ref<O7ConsumerTaskListResponse | null>(null);
const consumerTaskListError = ref("");
const consumerTaskListLoading = ref(false);
const consumerSelectedTaskId = ref("");
const consumerTaskDetailResult = ref<O7ConsumerTaskDetailResponse | null>(null);
const consumerTaskDetailError = ref("");
const consumerTaskDetailLoading = ref(false);
const cloudArchiveProbeBaseUrl = ref("http://127.0.0.1:8088");
const cloudArchiveProbeResult = ref<O7CloudArchiveTasksProbeResponse | null>(null);
const cloudArchiveProbeError = ref("");
const cloudArchiveProbeLoading = ref(false);
const realtimeElevatorProbeBaseUrl = ref("http://127.0.0.1:8088");
const realtimeElevatorProbeResult = ref<O7RealtimeElevatorProbeResponse | null>(null);
const realtimeElevatorProbeError = ref("");
const realtimeElevatorProbeLoading = ref(false);
const rtcSignalingContractProbeBaseUrl = ref("http://127.0.0.1:8088");
const rtcSignalingContractProbeResult = ref<O7RtcSignalingContractProbeResponse | null>(null);
const rtcSignalingContractProbeError = ref("");
const rtcSignalingContractProbeLoading = ref(false);
const cloudProbeBaseUrl = ref("http://127.0.0.1:8088");
const cloudProbeResult = ref<O7CloudOperatorConsoleProbeResponse | null>(null);
const cloudProbeError = ref("");
const cloudProbeLoading = ref(false);
const previewsAcceptanceResult = ref<O7PreviewsAcceptanceResponse | null>(null);
const previewsAcceptanceError = ref("");
const previewsAcceptanceLoading = ref(false);
const liveEndpointsManifestResult = ref<O7LiveEndpointsManifestResponse | null>(null);
const liveEndpointsManifestError = ref("");
const liveEndpointsManifestLoading = ref(false);
const fieldEvidenceConsumerIngestManifestJson = ref("");
const fieldEvidenceConsumerIngestRouteReplayJson = ref("");
const fieldEvidenceConsumerIngestLabelingJson = ref("");
const fieldEvidenceConsumerIngestResult = ref<O7FieldEvidenceConsumerIngestResponse | null>(null);
const fieldEvidenceConsumerIngestError = ref("");
const fieldEvidenceConsumerIngestLoading = ref(false);
const routeReplayCursor = ref(0);
const routeReplayPlaying = ref(false);
const routeReplayPlaybackTimer = ref<number | null>(null);
const fixtureRouteReplayCursor = ref(0);
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

function asObjectRecord(value: unknown): Record<string, unknown> | null {
  // consumer detail 的样本字段是 object 列表，非对象一律按缺失处理。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function asFiniteNumber(value: unknown): number | null {
  // 轨迹和时间戳只接受有限数字，字符串数字不自动提升，避免把坏数据误画成可用轨迹。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asCursorLabel(value: unknown, fallback: string): string {
  // 标题和状态只接受短字符串，避免把完整原始 payload 直接展示到页面。
  return typeof value === "string" && value.trim() ? value.trim().slice(0, 160) : fallback;
}

function sampleRecords(value: unknown, limit = 5): Record<string, unknown>[] {
  // 只保留少量样本做前端摘要，避免 detail 页把整段事件流和证据流都展开。
  return Array.isArray(value)
    ? value
        .slice(0, limit)
        .map((item) => asObjectRecord(item))
        .filter((item): item is Record<string, unknown> => Boolean(item))
    : [];
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

function consumerListBlockedReasons(): string[] {
  return consumerTaskListResult.value?.blocked_reasons ?? ["consumer_task_list_not_loaded"];
}

function consumerListNotProven(): string[] {
  return consumerTaskListResult.value?.not_proven ?? ["consumer_task_list_not_proven"];
}

function consumerDetailBlockedReasons(): string[] {
  return consumerTaskDetailResult.value?.blocked_reasons ?? ["consumer_task_detail_not_loaded"];
}

function consumerDetailNotProven(): string[] {
  return consumerTaskDetailResult.value?.not_proven ?? ["consumer_task_detail_not_proven"];
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

function rtcSignalingContractProbeBlockedReasons(): string[] {
  return rtcSignalingContractProbeResult.value?.blocked_reasons ?? ["rtc_signaling_contract_probe_not_loaded"];
}

function rtcSignalingContractProbeNotProven(): string[] {
  return rtcSignalingContractProbeResult.value?.not_proven ?? ["rtc_signaling_contract_probe_not_proven"];
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

function summarizeO7GapGroup(config: O7ReadinessGapGroupConfig): O7ReadinessGapGroup {
  const surfaces = previewsAcceptanceResult.value?.surfaces ?? [];
  // KR 分组只消费 guard 已返回的 surfaces；未加载时 matched=0，不能推断 ready。
  const matched = surfaces.filter((surface: O7PreviewsAcceptanceSurface) => config.surfaceIds.includes(surface.id));
  const blockedReasons = matched.flatMap((surface) => surface.blocked_reasons);
  const notProvenItems = matched.flatMap((surface) => surface.not_proven);
  return {
    krId: config.krId,
    krName: config.krName,
    matchedSurfaceCount: matched.length,
    surfaceIds: config.surfaceIds,
    blockedReasons: blockedReasons.length > 0 ? blockedReasons : ["not_loaded"],
    notProven: notProvenItems.length > 0 ? notProvenItems : ["not_loaded"],
    readyForRealOperation: false,
  };
}

const previewsAcceptanceGapSummary = computed(() =>
  // 这里保持纯前端派生，避免为了 readiness summary 增加后端 API 或 fixture 读取。
  o7ReadinessGapGroups.map((config) => summarizeO7GapGroup(config)),
);

function previewsAcceptanceRemainingGaps(): string[] {
  return previewsAcceptanceResult.value?.remaining_real_capability_gaps ?? ["not_loaded"];
}

function previewsAcceptanceKeyFalseFields(): string[] {
  const fields = previewsAcceptanceResult.value?.fixed_false_fields;
  // Operator 最容易误判的关键 guard 字段在 gap summary 内再展示一次。
  return [
    `safe_to_control=${String(fields?.safe_to_control ?? false)}`,
    `sends_commands=${String(fields?.sends_commands ?? false)}`,
    `connects_cloud_production=${String(fields?.connects_cloud_production ?? false)}`,
    `robot_control_executed=${String(fields?.robot_control_executed ?? false)}`,
  ];
}

function liveEndpointsManifestStatusCounts(): string[] {
  const summary = liveEndpointsManifestResult.value?.summary;
  // 未加载时也按全量 not_configured 展示，避免 operator 把空白理解为已配置。
  return [
    `configured=${String(summary?.configured ?? 0)}`,
    `not_configured=${String(summary?.not_configured ?? 6)}`,
    `blocked=${String(summary?.blocked ?? 0)}`,
    `token_present=${String(summary?.token_present ?? 0)}`,
    `token_absent=${String(summary?.token_absent ?? 6)}`,
  ];
}

function liveEndpointsManifestSafetyFlags(): string[] {
  const manifest = liveEndpointsManifestResult.value;
  // 这些全局开关是 manifest 的安全边界，不随 URL/token 配置而改变。
  return [
    `network_probe_executed=${String(manifest?.network_probe_executed ?? false)}`,
    `sends_commands=${String(manifest?.sends_commands ?? false)}`,
    `safe_to_control=${String(manifest?.safe_to_control ?? false)}`,
    `connects_cloud_production=${String(manifest?.connects_cloud_production ?? false)}`,
    `robot_control_executed=${String(manifest?.robot_control_executed ?? false)}`,
    `reads_hardware=${String(manifest?.reads_hardware ?? false)}`,
    `token_values_exposed=${String(manifest?.token_values_exposed ?? false)}`,
    `url_query_hash_credentials_exposed=${String(manifest?.url_query_hash_credentials_exposed ?? false)}`,
  ];
}

function liveEndpointCapabilities() {
  return liveEndpointsManifestResult.value?.capabilities ?? [];
}

function liveEndpointsRequiredEvidence(): string[] {
  return liveEndpointsManifestResult.value?.required_live_evidence ?? ["not_loaded"];
}

function liveEndpointsRemainingGaps(): string[] {
  return liveEndpointsManifestResult.value?.remaining_real_capability_gaps ?? ["not_loaded"];
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

function normalizeRouteReplayDetailFrame(value: unknown, cursorIndex: number): RouteReplayDetailFrame | null {
  const record = asObjectRecord(value);
  // consumer detail 的轨迹样本可能有轻微字段形状差异，这里只做白名单投影，不做结构修复。
  if (!record) {
    return null;
  }
  const pose = asObjectRecord(record.pose);
  const velocity = asObjectRecord(record.velocity);
  return {
    frame_index:
      asFiniteNumber(record.frame_index ?? record.frameIndex) === null
        ? cursorIndex
        : Math.trunc(asFiniteNumber(record.frame_index ?? record.frameIndex) as number),
    cursor_index: cursorIndex,
    timestamp_ms: asFiniteNumber(record.timestamp_ms ?? record.timestampMs),
    x_m: asFiniteNumber(record.x_m ?? pose?.x_m ?? pose?.x ?? pose?.xM),
    y_m: asFiniteNumber(record.y_m ?? pose?.y_m ?? pose?.y ?? pose?.yM),
    yaw_rad: asFiniteNumber(record.yaw_rad ?? pose?.yaw_rad ?? pose?.yaw ?? pose?.yawRad),
    speed_mps: asFiniteNumber(record.speed_mps ?? velocity?.linear_mps ?? velocity?.linear ?? velocity?.speed_mps),
    state: asCursorLabel(record.state ?? record.status ?? record.event_type, "blocked_not_proven"),
    evidence_ref: asCursorLabel(record.evidence_ref ?? record.evidenceRef, "missing_evidence_ref"),
  };
}

function safeDetailFrameSummary(frame: RouteReplayDetailFrame): string {
  // 帧摘要只展示详情里已给出的坐标和证据，不展开原始轨迹 payload。
  return [
    `frame_index=${frame.frame_index}`,
    `timestamp_ms=${frame.timestamp_ms ?? "null"}`,
    `x_m=${frame.x_m ?? "null"}`,
    `y_m=${frame.y_m ?? "null"}`,
    `yaw_rad=${frame.yaw_rad ?? "null"}`,
    `speed_mps=${frame.speed_mps ?? "null"}`,
    `state=${frame.state}`,
    `evidence_ref=${frame.evidence_ref}`,
  ].join(" · ");
}

function sampleDetailSummaries(value: unknown, label: string, limit = 5): string[] {
  // 只有少量摘要会进入 UI；完整数组仍留在后端 contract 内，不被浏览器展开。
  return sampleRecords(value, limit).map((record, index) => {
    const timestamp = asFiniteNumber(record.timestamp_ms ?? record.timestampMs);
    const state = asCursorLabel(record.state ?? record.status ?? record.event_type, "blocked_not_proven");
    const evidence = asCursorLabel(record.evidence_ref ?? record.evidenceRef, "missing_evidence_ref");
    const primary =
      label === "event"
        ? `event_type=${asCursorLabel(record.event_type ?? record.type, "blocked_not_proven")}`
        : label === "evidence"
          ? `evidence_type=${asCursorLabel(record.evidence_type ?? record.type, "blocked_not_proven")}`
          : label === "labeling"
            ? `item_id=${asCursorLabel(record.item_id, "blocked_not_proven")}; frame_id=${asCursorLabel(record.frame_id, "blocked_not_proven")}`
            : label === "inference"
              ? `result_type=${asCursorLabel(record.result_type ?? record.inference_type, "blocked_not_proven")}`
              : `status=${asCursorLabel(record.status, "blocked_not_proven")}`;
    return [
      `${index + 1}.`,
      primary,
      `state=${state}`,
      `timestamp_ms=${timestamp ?? "null"}`,
      `evidence_ref=${evidence}`,
    ].join(" · ");
  });
}

const routeReplayFrames = computed<RouteReplayDetailFrame[]>(() =>
  sampleRecords(consumerTaskDetailResult.value?.trajectory.sample_frames).map((frame, cursorIndex) =>
    normalizeRouteReplayDetailFrame(frame, cursorIndex),
  ).filter((frame): frame is RouteReplayDetailFrame => Boolean(frame)),
);
const fixtureRouteReplayFrames = computed<RouteReplayDetailFrame[]>(() =>
  (archiveResult.value?.route_replay_inspector.sample_frames ?? []).map((frame, cursorIndex) => ({
    // fixture 回放作为次路径保留，字段来自后端已压缩的 inspector 摘要。
    ...frame,
    cursor_index: cursorIndex,
  })),
);
const labelingReviewItems = computed(() => archiveResult.value?.labeling_queue_inspector.sample_review_items ?? []);
const voiceAsrEvents = computed(() => archiveResult.value?.voice_asr_tts_inspector.sample_asr_events ?? []);
const safeCommandSamples = computed(() => archiveResult.value?.safe_command_inspector.sample_commands ?? []);

function isFiniteNumber(value: unknown): value is number {
  // 轨迹小地图只接受真实 finite number；null、NaN 和字符串都不能进入 SVG 归一化。
  return typeof value === "number" && Number.isFinite(value);
}

function parseSummaryNumber(summary: string, key: string): number | null {
  const match = summary.match(new RegExp(`(?:^|[,\\s])${key}=(-?\\d+(?:\\.\\d+)?)`));
  const parsed = match ? Number(match[1]) : Number.NaN;
  // probe summary 是安全字符串而不是结构化 pose；任何缺失或非 finite 值都不能画 marker。
  return Number.isFinite(parsed) ? parsed : null;
}

function clampSvgCoordinate(value: number): number {
  // 固定 map frame 只做浏览器端预览，极端坐标压在边界内，避免 SVG 视口被数据撑坏。
  return Math.min(Math.max(value, 12), 88);
}

function buildRealtimePosePreview(summary: string): RealtimePosePreview | null {
  const x = parseSummaryNumber(summary, "x_m");
  const y = parseSummaryNumber(summary, "y_m");
  const yaw = parseSummaryNumber(summary, "yaw_rad");
  // 三个字段缺一不可；否则明确 blocked，不能把未知 pose 画成中心点。
  if (x === null || y === null || yaw === null) {
    return null;
  }
  const svgX = clampSvgCoordinate(50 + x * 14);
  const svgY = clampSvgCoordinate(50 - y * 14);
  const headingX = clampSvgCoordinate(svgX + Math.cos(yaw) * 12);
  const headingY = clampSvgCoordinate(svgY - Math.sin(yaw) * 12);
  return { x_m: x, y_m: y, yaw_rad: yaw, svg_x: svgX, svg_y: svgY, heading_x: headingX, heading_y: headingY };
}

const realtimePosePreview = computed<RealtimePosePreview | null>(() =>
  buildRealtimePosePreview(realtimeElevatorProbeResult.value?.robot_pose_summary ?? ""),
);

const realtimeMapVisualizationStatus = computed(() =>
  realtimePosePreview.value ? "readonly_probe_summary_pose_ready" : "blocked_pose_coordinate_unavailable",
);

const realtimePoseMarkerStatus = computed(() => {
  const pose = realtimePosePreview.value;
  // marker 状态只回显已解析的安全摘要字段，不引用真实 /tf 或地图 artifact。
  if (!pose) {
    return "blocked_pose_coordinate_unavailable";
  }
  return `x_m=${pose.x_m}; y_m=${pose.y_m}; yaw_rad=${pose.yaw_rad}`;
});

const realtimeElevatorTimelineSamples = computed(() =>
  (realtimeElevatorProbeResult.value?.elevator_state_samples_summary ?? []).slice(0, 5),
);

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

const fixtureRouteReplayTrajectoryPoints = computed<RouteReplayTrajectoryPoint[]>(() =>
  fixtureRouteReplayFrames.value
    .map((frame, cursorIndex) => ({ frame, cursorIndex }))
    .filter(({ frame }) => isFiniteNumber(frame.x_m) && isFiniteNumber(frame.y_m))
    .map(({ frame, cursorIndex }) => ({
      // fixture 次路径也只画有效 x/y，避免旧调试样本被误读成真实地图。
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

const fixtureRouteReplayMinimapPoints = computed<RouteReplayMinimapPoint[]>(() => {
  const points = fixtureRouteReplayTrajectoryPoints.value;
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
  // 旧 fixture 小地图仍走同一个归一化算法，但不参与 consumer-detail 主路径判断。
  return points.map((point) => normalizeRouteReplayPoint(point, bounds));
});

const routeReplayMinimapPolyline = computed(() =>
  routeReplayMinimapPoints.value.map((point) => `${point.svg_x.toFixed(2)},${point.svg_y.toFixed(2)}`).join(" "),
);

const fixtureRouteReplayMinimapPolyline = computed(() =>
  fixtureRouteReplayMinimapPoints.value.map((point) => `${point.svg_x.toFixed(2)},${point.svg_y.toFixed(2)}`).join(" "),
);

const currentRouteReplayMinimapMarker = computed<RouteReplayMinimapPoint | null>(() => {
  const frame = routeReplayFrames.value[routeReplayCursor.value] ?? null;
  // 当前帧没有有效坐标时不画 marker，避免把未知位置显示成轨迹上的确定点。
  if (!frame || !isFiniteNumber(frame.x_m) || !isFiniteNumber(frame.y_m)) {
    return null;
  }
  return routeReplayMinimapPoints.value.find((point) => point.cursor_index === routeReplayCursor.value) ?? null;
});

const currentFixtureRouteReplayMinimapMarker = computed<RouteReplayMinimapPoint | null>(() => {
  const frame = fixtureRouteReplayFrames.value[fixtureRouteReplayCursor.value] ?? null;
  // fixture 当前帧坐标无效时同样不画 marker，避免 debug fallback 产生确定位置错觉。
  if (!frame || !isFiniteNumber(frame.x_m) || !isFiniteNumber(frame.y_m)) {
    return null;
  }
  return fixtureRouteReplayMinimapPoints.value.find((point) => point.cursor_index === fixtureRouteReplayCursor.value) ?? null;
});

const routeReplayMinimapStatus = computed(() => {
  // 没有有效点时必须阻断；只有 1 个点时仍可浏览当前 marker，但不能画出完整轨迹线。
  if (routeReplayTrajectoryPoints.value.length === 0) {
    return "blocked_not_proven";
  }
  if (routeReplayTrajectoryPoints.value.length === 1) {
    return "readonly_consumer_detail_trajectory_single_point";
  }
  return "readonly_consumer_detail_trajectory_ready";
});

const routeReplayCurrentMarkerStatus = computed(() => {
  // marker 与现有 routeReplayCursor 绑定；当前 sample 坐标无效时必须显式 unknown。
  if (!currentRouteReplayMinimapMarker.value) {
    return "blocked_unknown_current_frame_coordinate";
  }
  return `frame_index=${currentRouteReplayMinimapMarker.value.frame_index}`;
});

const fixtureRouteReplayMinimapStatus = computed(() => {
  // fixture 次路径保持更严格的旧语义：少于两个点不画成轨迹。
  if (fixtureRouteReplayTrajectoryPoints.value.length < 2) {
    return "blocked_not_proven";
  }
  return "readonly_fixture_trajectory_ready";
});

const fixtureRouteReplayCurrentMarkerStatus = computed(() => {
  if (!currentFixtureRouteReplayMinimapMarker.value) {
    return "blocked_unknown_current_frame_coordinate";
  }
  return `frame_index=${currentFixtureRouteReplayMinimapMarker.value.frame_index}`;
});

const routeReplayBlockedReason = computed(() => {
  const detail = consumerTaskDetailResult.value;
  // 逐帧浏览只绑定 consumer detail；未加载、失败态、未知任务或轨迹缺失都必须关闸。
  if (consumerTaskDetailLoading.value) {
    return "consumer_task_detail_loading";
  }
  if (consumerTaskDetailError.value) {
    return "consumer_task_detail_api_unavailable";
  }
  if (!detail) {
    return "consumer_task_detail_not_loaded";
  }
  if (detail.detail_status !== "loaded_fail_closed_summary") {
    return detail.fail_closed_reason || "consumer_task_detail_fail_closed";
  }
  const taskId = detail.task_summary?.task_id?.trim() ?? "";
  const requestedTaskId = consumerSelectedTaskId.value.trim();
  const taskStatus = detail.task_summary?.task_status_summary ?? "";
  if (!taskId || taskId === "unknown_task" || taskId === "not_provided") {
    return "unknown_task";
  }
  if (requestedTaskId && taskId !== requestedTaskId) {
    return "task_id_mismatch";
  }
  if (!taskStatus || /(?:failed|blocked|error|invalid|unknown|expired|cancel|not_proven)/i.test(taskStatus)) {
    return `task_status_not_playable:${taskStatus || "missing"}`;
  }
  if (!routeReplayFrames.value.length) {
    return "trajectory_missing";
  }
  return "";
});

const routeReplayNavigationEnabled = computed(() => routeReplayBlockedReason.value === "");

const fixtureRouteReplayBlockedReason = computed(() => {
  const archive = archiveResult.value as (O7CloudArchiveTasksResponse & { playback_available?: boolean }) | null;
  const inspector = archive?.route_replay_inspector;
  // fixture replay 只是旧调试 fallback；没有本地 archive 或 inspector ready 时必须关闸。
  if (!archive) {
    return "archive_not_loaded";
  }
  if (!inspector?.selected_task_id) {
    return "selected_task_missing";
  }
  if (!fixtureRouteReplayFrames.value.length) {
    return "sample_frames_missing";
  }
  if (archive.playback_available === false) {
    return "playback_available_false";
  }
  if (inspector.status !== "fixture_inspector_ready") {
    return "route_replay_inspector_blocked_not_proven";
  }
  return "";
});

const fixtureRouteReplayNavigationEnabled = computed(() => fixtureRouteReplayBlockedReason.value === "");

function stopRouteReplayPlayback(): void {
  // 播放器只允许在浏览器内推进 cursor；停止时必须清理本地计时器，避免切页后继续跳帧。
  if (routeReplayPlaybackTimer.value !== null) {
    window.clearInterval(routeReplayPlaybackTimer.value);
    routeReplayPlaybackTimer.value = null;
  }
  routeReplayPlaying.value = false;
}

function clampRouteReplayCursor(index: number): void {
  const maxIndex = Math.max(routeReplayFrames.value.length - 1, 0);
  // cursor 只允许落在当前 detail 的 sample frame 范围内，越界时直接压回边界。
  routeReplayCursor.value = Math.min(Math.max(index, 0), maxIndex);
}

function resetRouteReplayCursor(): void {
  stopRouteReplayPlayback();
  clampRouteReplayCursor(0);
}

function previousRouteReplayFrame(): void {
  if (routeReplayNavigationEnabled.value) {
    stopRouteReplayPlayback();
    clampRouteReplayCursor(routeReplayCursor.value - 1);
  }
}

function nextRouteReplayFrame(): void {
  if (routeReplayNavigationEnabled.value) {
    stopRouteReplayPlayback();
    clampRouteReplayCursor(routeReplayCursor.value + 1);
  }
}

function setRouteReplayCursorFromInput(event: Event): void {
  const target = event.target as HTMLInputElement;
  if (routeReplayNavigationEnabled.value) {
    stopRouteReplayPlayback();
    clampRouteReplayCursor(Number(target.value));
  }
}

function tickRouteReplayPlayback(): void {
  const nextIndex = routeReplayCursor.value + 1;
  if (!routeReplayNavigationEnabled.value || routeReplayFrames.value.length === 0) {
    stopRouteReplayPlayback();
    return;
  }
  if (nextIndex >= routeReplayFrames.value.length) {
    stopRouteReplayPlayback();
    return;
  }
  clampRouteReplayCursor(nextIndex);
}

function startRouteReplayPlayback(): void {
  if (!routeReplayNavigationEnabled.value || routeReplayFrames.value.length <= 1) {
    return;
  }
  stopRouteReplayPlayback();
  routeReplayPlaying.value = true;
  routeReplayPlaybackTimer.value = window.setInterval(() => {
    tickRouteReplayPlayback();
  }, 900);
}

function toggleRouteReplayPlayback(): void {
  if (routeReplayPlaying.value) {
    stopRouteReplayPlayback();
    return;
  }
  startRouteReplayPlayback();
}

function clampFixtureRouteReplayCursor(index: number): void {
  const maxIndex = Math.max(fixtureRouteReplayFrames.value.length - 1, 0);
  // fixture cursor 与 consumer cursor 完全隔离，防止加载 archive 改变主路径帧位。
  fixtureRouteReplayCursor.value = Math.min(Math.max(index, 0), maxIndex);
}

function resetFixtureRouteReplayCursor(): void {
  clampFixtureRouteReplayCursor(0);
}

function previousFixtureRouteReplayFrame(): void {
  if (fixtureRouteReplayNavigationEnabled.value) {
    clampFixtureRouteReplayCursor(fixtureRouteReplayCursor.value - 1);
  }
}

function nextFixtureRouteReplayFrame(): void {
  if (fixtureRouteReplayNavigationEnabled.value) {
    clampFixtureRouteReplayCursor(fixtureRouteReplayCursor.value + 1);
  }
}

function setFixtureRouteReplayCursorFromInput(event: Event): void {
  const target = event.target as HTMLInputElement;
  if (fixtureRouteReplayNavigationEnabled.value) {
    clampFixtureRouteReplayCursor(Number(target.value));
  }
}

const consumerRouteReplayTaskSummary = computed(() => consumerTaskDetailResult.value?.task_summary ?? null);
const consumerRouteReplayEventSummaries = computed(() =>
  sampleDetailSummaries(consumerTaskDetailResult.value?.events.sample_events, "event"),
);
const consumerRouteReplayEvidenceSummaries = computed(() =>
  sampleDetailSummaries(consumerTaskDetailResult.value?.evidence.sample_evidence, "evidence"),
);
const consumerRouteReplayLabelingSummaries = computed(() =>
  sampleDetailSummaries(consumerTaskDetailResult.value?.labeling.sample_items, "labeling"),
);
const consumerRouteReplayInferenceSummaries = computed(() =>
  sampleDetailSummaries(consumerTaskDetailResult.value?.inference.sample_results, "inference"),
);
const consumerRouteReplayTunnelSummary = computed(() => {
  const tunnel = consumerTaskDetailResult.value?.tunnel_status;
  // tunnel 只是 latest known snapshot 摘要，不是任务内历史事实；这里只读白名单字段。
  if (!tunnel) {
    return ["blocked_not_proven"];
  }
  return [
    `status=${asCursorLabel(tunnel.status, "blocked_not_proven")}`,
    `latest_known_status=${asCursorLabel(tunnel.latest_known_status, "blocked_not_proven")}`,
    `temporal_alignment=${asCursorLabel(tunnel.temporal_alignment, "latest_known_robot_snapshot_not_task_aligned")}`,
  ];
});

const consumerDetailLabelingQueueBlockedReason = computed(() => {
  const detail = consumerTaskDetailResult.value;
  // 标注队列主路径必须直接绑定 consumer detail；缺 detail、缺样本或任务状态不可审阅时都要关闸。
  if (consumerTaskDetailLoading.value) {
    return "consumer_task_detail_loading";
  }
  if (consumerTaskDetailError.value) {
    return "consumer_task_detail_api_unavailable";
  }
  if (!detail) {
    return "consumer_task_detail_not_loaded";
  }
  if (detail.detail_status !== "loaded_fail_closed_summary") {
    return detail.fail_closed_reason || "consumer_task_detail_fail_closed";
  }
  const taskId = detail.task_summary?.task_id?.trim() ?? "";
  const requestedTaskId = consumerSelectedTaskId.value.trim();
  const taskStatus = detail.task_summary?.task_status_summary ?? "";
  if (!taskId || taskId === "unknown_task" || taskId === "not_provided") {
    return "unknown_task";
  }
  if (requestedTaskId && taskId !== requestedTaskId) {
    return "task_id_mismatch";
  }
  if (!taskStatus || /(?:failed|blocked|error|invalid|unknown|expired|cancel|not_proven)/i.test(taskStatus)) {
    return `task_status_not_reviewable:${taskStatus || "missing"}`;
  }
  if (!detail.labeling.label_count || !detail.labeling.sample_items.length) {
    return "labeling_missing";
  }
  if (!detail.evidence.count || !detail.evidence.sample_evidence.length) {
    return "evidence_missing";
  }
  if (!detail.events.count || !detail.events.sample_events.length) {
    return "events_missing";
  }
  if (!detail.trajectory.frame_count || !routeReplayFrames.value.length) {
    return "trajectory_missing";
  }
  return "";
});

const consumerDetailLabelingQueueNavigationEnabled = computed(
  () => consumerDetailLabelingQueueBlockedReason.value === "",
);

const consumerDetailLabelingQueueRowSummaries = computed(() => {
  // 这里把 labeling / evidence / events / trajectory 串成同一条只读检查线，但只输出短摘要。
  if (!consumerDetailLabelingQueueNavigationEnabled.value) {
    return [];
  }
  const labelItems = sampleRecords(consumerTaskDetailResult.value?.labeling.sample_items, 5);
  const trajectorySummaries = routeReplayFrames.value.map((frame) => safeDetailFrameSummary(frame));
  const eventSummaries = sampleDetailSummaries(consumerTaskDetailResult.value?.events.sample_events, "event", 5);
  const evidenceSummaries = sampleDetailSummaries(consumerTaskDetailResult.value?.evidence.sample_evidence, "evidence", 5);
  const maxLength = Math.min(
    5,
    Math.max(labelItems.length, trajectorySummaries.length, eventSummaries.length, evidenceSummaries.length),
  );
  return Array.from({ length: maxLength }, (_, index) => {
    const item = labelItems[index];
    const itemSummary = item
      ? [
          `item_id=${asCursorLabel(item.item_id, "blocked_not_proven")}`,
          `frame_id=${asCursorLabel(item.frame_id, "blocked_not_proven")}`,
          `status=${asCursorLabel(item.status, "blocked_not_proven")}`,
          `evidence_ref=${asCursorLabel(item.evidence_ref, "missing_evidence_ref")}`,
        ].join(" · ")
      : "blocked_not_proven";
    return [
      `#${index + 1}`,
      itemSummary,
      `trajectory=${trajectorySummaries[index] ?? "blocked_not_proven"}`,
      `event=${eventSummaries[index] ?? "blocked_not_proven"}`,
      `evidence=${evidenceSummaries[index] ?? "blocked_not_proven"}`,
    ].join(" · ");
  });
});

function consumerDetailLabelingQueueFalseFields(): string[] {
  const detail = consumerTaskDetailResult.value;
  // 这些 false 字段让 operator 一眼看见：这里只是只读检查视图，不是 annotation 生产入口。
  return [
    `submit_enabled=false`,
    `export_enabled=false`,
    `rollback_enabled=false`,
    `dataset_export_available=false`,
    `real_annotation_api_connected=false`,
    `connects_cloud_production=${String(detail?.connects_cloud_production ?? false)}`,
    `safe_to_control=${String(detail?.safe_to_control ?? false)}`,
    `primary_actions_enabled=${String(detail?.primary_actions_enabled ?? false)}`,
    `robot_control_executed=${String(detail?.robot_control_executed ?? false)}`,
  ];
}

const consumerDetailLabelingQueueSummary = computed(() => {
  const detail = consumerTaskDetailResult.value;
  // summary 只压缩标签、证据、事件和轨迹的计数，不把完整 payload 灌进 UI。
  if (!detail) {
    return "blocked_not_proven";
  }
  return [
    `consumer-detail labeling primary path`,
    `task_id=${detail.task_summary?.task_id ?? "blocked_not_proven"}`,
    `labeling_status=${detail.labeling.status}`,
    `label_count=${detail.labeling.label_count}`,
    `evidence_count=${detail.evidence.count}`,
    `event_count=${detail.events.count}`,
    `trajectory_frame_count=${detail.trajectory.frame_count}`,
  ].join(" · ");
});

onBeforeUnmount(() => {
  // 组件销毁时必须清掉本地计时器，避免离开页面后仍然推进 cursor。
  stopRouteReplayPlayback();
});

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
  // cursor 只是浏览器本地数组下标，不发送给后端；frame_index 仍来自 consumer detail 样本。
  if (!routeReplayNavigationEnabled.value) {
    return null;
  }
  return routeReplayFrames.value[routeReplayCursor.value] ?? routeReplayFrames.value[0] ?? null;
});

const currentRouteReplayFrameSummary = computed(() =>
  currentRouteReplayFrame.value ? safeDetailFrameSummary(currentRouteReplayFrame.value) : "blocked_not_proven",
);

function routeReplayCursorDisplay(): string {
  const frame = currentRouteReplayFrame.value;
  // blocked 时也显示总 sample 数，方便 operator 区分未加载和已加载但不可浏览。
  if (!frame) {
    return `blocked_not_proven / ${routeReplayFrames.value.length}`;
  }
  return `${routeReplayCursor.value + 1} / ${routeReplayFrames.value.length}`;
}

const currentFixtureRouteReplayFrame = computed(() => {
  // fixture frame 只用于本地 debug fallback，不影响 consumer-detail 主路径。
  if (!fixtureRouteReplayNavigationEnabled.value) {
    return null;
  }
  return fixtureRouteReplayFrames.value[fixtureRouteReplayCursor.value] ?? fixtureRouteReplayFrames.value[0] ?? null;
});

function fixtureRouteReplayCursorDisplay(): string {
  const frame = currentFixtureRouteReplayFrame.value;
  if (!frame) {
    return `blocked_not_proven / ${fixtureRouteReplayFrames.value.length}`;
  }
  return `${fixtureRouteReplayCursor.value + 1} / ${fixtureRouteReplayFrames.value.length}`;
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

async function loadArchiveTasks(): Promise<void> {
  // 只有 operator 点击按钮才读取本地 archive 路径；页面加载不会自动触碰文件系统。
  archiveLoading.value = true;
  archiveError.value = "";
  try {
    archiveResult.value = await getO7CloudArchiveTasks(archiveJson.value);
    resetFixtureRouteReplayCursor();
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

async function loadConsumerTaskList(): Promise<void> {
  // O7 任务列表主入口固定走 O6 consumer read summary 视图，避免前端继续 join 低层接口。
  consumerTaskListLoading.value = true;
  consumerTaskListError.value = "";
  try {
    consumerTaskListResult.value = await getO7ConsumerTaskList(consumerReadBaseUrl.value);
    consumerSelectedTaskId.value = consumerTaskListResult.value.task_list[0]?.task_id ?? "";
  } catch (error) {
    consumerTaskListError.value = error instanceof Error ? error.message : "consumer_task_list_not_available";
  } finally {
    consumerTaskListLoading.value = false;
  }
}

async function loadConsumerTaskDetail(): Promise<void> {
  // O7 详情主入口固定由后端追加 include=trajectory,events,evidence,labeling,inference,tunnel。
  consumerTaskDetailLoading.value = true;
  consumerTaskDetailError.value = "";
  try {
    consumerTaskDetailResult.value = await getO7ConsumerTaskDetail(consumerReadBaseUrl.value, consumerSelectedTaskId.value);
    resetRouteReplayCursor();
  } catch (error) {
    consumerTaskDetailError.value = error instanceof Error ? error.message : "consumer_task_detail_not_available";
  } finally {
    consumerTaskDetailLoading.value = false;
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
  resetFixtureRouteReplayCursor();
  resetLocalTtsDraft();
  resetLocalSafeCommandDraft();
});

watch([consumerSelectedTaskId, consumerReadBaseUrl], () => {
  // consumer 主路径切换任务或 relay 时只清理主路径 cursor，不碰 fixture fallback 状态。
  resetRouteReplayCursor();
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

async function loadRtcSignalingContractProbe(): Promise<void> {
  // 这里只触发 PC 后端回环 contract probe；浏览器不创建 WebRTC、视频 track 或 ROS2 /tf 连接。
  rtcSignalingContractProbeLoading.value = true;
  rtcSignalingContractProbeError.value = "";
  try {
    rtcSignalingContractProbeResult.value = await getO7RtcSignalingContractProbe(rtcSignalingContractProbeBaseUrl.value);
  } catch (err) {
    rtcSignalingContractProbeError.value = err instanceof Error ? err.message : "rtc_signaling_contract_probe_api_unavailable_not_proven";
  } finally {
    rtcSignalingContractProbeLoading.value = false;
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

async function loadLiveEndpointsManifest(): Promise<void> {
  // 该按钮只加载 env readiness manifest；后端不会 ping URL、连接生产、发命令或读取硬件。
  liveEndpointsManifestLoading.value = true;
  liveEndpointsManifestError.value = "";
  try {
    liveEndpointsManifestResult.value = await getO7LiveEndpointsManifest();
  } catch (err) {
    liveEndpointsManifestError.value = err instanceof Error ? err.message : "o7_live_endpoints_manifest_unavailable";
  } finally {
    liveEndpointsManifestLoading.value = false;
  }
}

async function loadFieldEvidenceConsumerIngest(): Promise<void> {
  // 这条入口把 manifest、route replay 和 labeling 绑进同一份只读消费摘要。
  // UI 只发 query，不自己拼装任何机器人状态或成功结论。
  fieldEvidenceConsumerIngestLoading.value = true;
  fieldEvidenceConsumerIngestError.value = "";
  try {
    const params = new URLSearchParams();
    const manifestJson = fieldEvidenceConsumerIngestManifestJson.value.trim();
    const routeReplayJson = fieldEvidenceConsumerIngestRouteReplayJson.value.trim();
    const labelingJson = fieldEvidenceConsumerIngestLabelingJson.value.trim();
    if (manifestJson) {
      params.set("manifestJson", manifestJson);
    }
    if (routeReplayJson) {
      params.set("routeReplayFixtureJson", routeReplayJson);
    }
    if (labelingJson) {
      params.set("labelingFixtureJson", labelingJson);
    }
    const query = params.toString();
    const response = await fetch(
      `/api/o7/field-evidence-consumer-ingest${query ? `?${query}` : ""}`,
    );
    if (!response.ok) {
      throw new Error(`/api/o7/field-evidence-consumer-ingest returned ${response.status}`);
    }
    fieldEvidenceConsumerIngestResult.value = (await response.json()) as O7FieldEvidenceConsumerIngestResponse;
  } catch (err) {
    fieldEvidenceConsumerIngestError.value =
      err instanceof Error ? err.message : "field_evidence_consumer_ingest_unavailable_not_proven";
  } finally {
    fieldEvidenceConsumerIngestLoading.value = false;
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
          <h3>O7 live endpoints manifest</h3>
          <p class="eyebrow">Manual env readiness manifest. No ping, no connect, no command dispatch.</p>
        </div>
        <span class="pill danger">{{ liveEndpointsManifestResult?.manifest_status ?? "not_loaded" }}</span>
      </div>

      <button class="secondary" type="button" @click="loadLiveEndpointsManifest">
        {{ liveEndpointsManifestLoading ? "Loading live endpoints manifest" : "Load live endpoints manifest" }}
      </button>

      <div v-if="liveEndpointsManifestError" class="notice" role="alert">
        O7 live endpoints manifest unavailable: {{ liveEndpointsManifestError }}. network_probe_executed=false.
      </div>

      <dl class="kv compact-kv">
        <dt>schema</dt>
        <dd>{{ liveEndpointsManifestResult?.schema ?? "trashbot.o7.live_endpoints_manifest.v1" }}</dd>
        <dt>endpoint</dt>
        <dd>{{ liveEndpointsManifestResult?.endpoint ?? "/api/o7/live-endpoints/manifest" }}</dd>
        <dt>env only</dt>
        <dd>{{ liveEndpointsManifestResult?.env_only ?? true }}</dd>
        <dt>proof status</dt>
        <dd>{{ liveEndpointsManifestResult?.proof_status ?? "not_proven" }}</dd>
      </dl>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Readiness counts</h3>
          <ul class="dense">
            <li v-for="field in liveEndpointsManifestStatusCounts()" :key="field">{{ field }}</li>
          </ul>
          <h3>Endpoint readiness</h3>
          <ul class="dense">
            <!-- capability 状态只来自后端 env 脱敏摘要；URL 不展示 query/hash/credentials，token 只展示 present/absent。 -->
            <li v-for="capability in liveEndpointCapabilities()" :key="capability.id">
              {{ capability.kr_ids.join("+") }} {{ capability.id }} · status={{ capability.status }} · url={{
                capability.url.display_url
              }} · token={{ capability.token.status }} · missing={{ capability.missing.join(", ") || "none" }} · blocked={{
                capability.blocked_reasons.join(", ") || "none"
              }}
            </li>
            <li v-if="!liveEndpointCapabilities().length">not_loaded</li>
          </ul>
          <h3>Global safety flags</h3>
          <ul class="dense">
            <li v-for="field in liveEndpointsManifestSafetyFlags()" :key="field">{{ field }}</li>
          </ul>
        </div>
        <div>
          <h3>Required live evidence</h3>
          <ul class="dense">
            <li v-for="item in liveEndpointsRequiredEvidence()" :key="item">{{ item }}</li>
          </ul>
          <h3>Remaining real capability gaps</h3>
          <ul class="dense">
            <li v-for="gap in liveEndpointsRemainingGaps()" :key="gap">{{ gap }}</li>
          </ul>
          <h3>Blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in liveEndpointsManifestResult?.blocked_reasons ?? ['not_loaded']" :key="reason">{{ reason }}</li>
          </ul>
        </div>
      </div>
    </article>

    <article class="snapshot-panel">
      <div class="section-head compact-head">
        <div>
          <h3>Field evidence consumer ingest</h3>
          <p class="eyebrow">Manifest entry point for route replay and labeling. Local mock and future SSH share the same summary shape.</p>
        </div>
        <span class="pill danger">{{ fieldEvidenceConsumerIngestResult?.ingest_status ?? "not_loaded" }}</span>
      </div>

      <div class="two-col snapshot-grid">
        <div>
          <label class="single-input">
            <span>Manifest JSON path</span>
            <input
              v-model="fieldEvidenceConsumerIngestManifestJson"
              aria-label="Field evidence manifest JSON path"
              placeholder="pc-tools/evidence/fixtures/field_evidence_manifest.json"
            >
          </label>
          <label class="single-input">
            <span>Route replay fixture JSON path</span>
            <input
              v-model="fieldEvidenceConsumerIngestRouteReplayJson"
              aria-label="Route replay fixture JSON path"
              placeholder="pc-tools/evidence/fixtures/wave_rover_feedback_replay/pass/route_replay.json"
            >
          </label>
          <label class="single-input">
            <span>Labeling fixture JSON path</span>
            <input
              v-model="fieldEvidenceConsumerIngestLabelingJson"
              aria-label="Labeling fixture JSON path"
              placeholder="pc-tools/evidence/fixtures/wave_rover_hil_packet_intake/pass/labeling.json"
            >
          </label>
          <button class="secondary" type="button" @click="loadFieldEvidenceConsumerIngest">
            {{ fieldEvidenceConsumerIngestLoading ? "Loading consumer ingest" : "Load field evidence consumer ingest" }}
          </button>
          <div v-if="fieldEvidenceConsumerIngestError" class="notice" role="alert">
            Field evidence consumer ingest unavailable: {{ fieldEvidenceConsumerIngestError }}.
          </div>
        </div>
        <div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.schema ?? "trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1" }}</dd>
            <dt>source manifest schema</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.source_manifest_schema ?? "not_loaded" }}</dd>
            <dt>manifest status</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.status ?? "not_loaded" }}</dd>
            <dt>manifest gate_pass</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.gate_pass ?? false }}</dd>
            <dt>route replay preview</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.route_replay_preview.preview_status ?? "not_loaded" }}</dd>
            <dt>labeling preview</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.labeling_preview.preview_status ?? "not_loaded" }}</dd>
            <dt>blocked reason</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.consumer_entry.blocked_reason ?? "not_loaded" }}</dd>
            <dt>fallback mode</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.consumer_entry.fallback_mode ?? "blocked_not_proven" }}</dd>
            <dt>safe_to_control</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.safe_to_control ?? false }}</dd>
            <dt>delivery_success</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.delivery_success ?? false }}</dd>
          </dl>
        </div>
      </div>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Manifest summary</h3>
          <dl class="kv compact-kv">
            <dt>run_id</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.run_id ?? "not_loaded" }}</dd>
            <dt>mode</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.mode ?? "not_loaded" }}</dd>
            <dt>artifact_root</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.artifact_root ?? "not_loaded" }}</dd>
            <dt>preflight_status</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.preflight_status ?? "null" }}</dd>
            <dt>gate_pass</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.gate_pass ?? false }}</dd>
            <dt>blocked_reason</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.blocked_reason ?? "not_loaded" }}</dd>
          </dl>
          <h3>Manifest artifacts</h3>
          <ul class="dense">
            <li>map_yaml={{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.map_yaml.present ?? false }} · {{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.map_yaml.reason ?? "none" }}</li>
            <li>route_csv={{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.route_csv.present ?? false }} · {{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.route_csv.reason ?? "none" }}</li>
            <li>keyframes={{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.keyframes.present ?? false }} · {{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.keyframes.reason ?? "none" }}</li>
            <li>rosbag={{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.rosbag.present ?? false }} · {{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.rosbag.reason ?? "none" }}</li>
            <li>replay_jsonl={{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.replay_jsonl.present ?? false }} · {{ fieldEvidenceConsumerIngestResult?.manifest.artifacts.replay_jsonl.reason ?? "none" }}</li>
          </ul>
        </div>
        <div>
          <h3>Route replay consumer</h3>
          <dl class="kv compact-kv">
            <dt>task_id</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.route_replay_preview.task.task_id ?? "not_loaded" }}</dd>
            <dt>route_id</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.route_replay_preview.task.route_id ?? "not_loaded" }}</dd>
            <dt>frame_count</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.route_replay_preview.trajectory.frame_count ?? 0 }}</dd>
            <dt>playback_cursor</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.route_replay_preview.playback_cursor_initial_state.status ?? "not_loaded" }}</dd>
            <dt>blocked_reason</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.route_replay_preview.blocked_reasons[0] ?? "not_loaded" }}</dd>
          </dl>
          <h3>Labeling consumer</h3>
          <dl class="kv compact-kv">
            <dt>queue_id</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.labeling_preview.queue.queue_id ?? "not_loaded" }}</dd>
            <dt>review_item_count</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.labeling_preview.queue.review_item_count ?? 0 }}</dd>
            <dt>label_schema</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.labeling_preview.label_schema.schema_ref ?? "not_loaded" }}</dd>
            <dt>submit_enabled</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.labeling_preview.submit_enabled ?? false }}</dd>
            <dt>blocked_reason</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.labeling_preview.blocked_reasons[0] ?? "not_loaded" }}</dd>
          </dl>
        </div>
      </div>

      <h3>Consumer entry blocked reasons</h3>
      <ul class="dense">
        <li v-for="reason in fieldEvidenceConsumerIngestResult?.blocked_reasons ?? ['not_loaded']" :key="reason">
          {{ reason }}
        </li>
      </ul>
      <h3>Consumer entry not proven</h3>
      <ul class="dense">
        <li v-for="item in fieldEvidenceConsumerIngestResult?.not_proven ?? ['not_loaded']" :key="item">{{ item }}</li>
      </ul>
      <h3>Consumer entry next required evidence</h3>
      <ul class="dense">
        <li v-for="item in fieldEvidenceConsumerIngestResult?.next_required_evidence ?? ['not_loaded']" :key="item">
          {{ item }}
        </li>
      </ul>
    </article>

    <article class="snapshot-panel">
      <div class="section-head compact-head">
        <div>
          <h3>RTC signaling contract probe</h3>
          <p class="eyebrow">Read-only local loopback HTTP contract proof for /api/o7/rtc-signaling/contract.</p>
        </div>
        <span class="pill danger">{{ rtcSignalingContractProbeResult?.probe_status ?? "not_loaded" }}</span>
      </div>

      <label class="single-input">
        <span>Cloud relay base URL</span>
        <input
          v-model="rtcSignalingContractProbeBaseUrl"
          aria-label="RTC signaling contract probe base URL"
          placeholder="http://127.0.0.1:8088"
        >
      </label>
      <button class="secondary" type="button" @click="loadRtcSignalingContractProbe">
        {{ rtcSignalingContractProbeLoading ? "Loading RTC contract probe" : "Probe RTC signaling contract" }}
      </button>

      <div v-if="rtcSignalingContractProbeError" class="notice" role="alert">
        RTC signaling contract probe API unavailable: {{ rtcSignalingContractProbeError }}.
        network_probe_executed=false.
      </div>

      <dl class="kv compact-kv">
        <dt>schema</dt>
        <dd>{{ rtcSignalingContractProbeResult?.schema ?? "trashbot.pc_tools_workstation.o7_rtc_signaling_contract_probe.v1" }}</dd>
        <dt>source base URL</dt>
        <dd>{{ rtcSignalingContractProbeResult?.source_base_url ?? "not_loaded" }}</dd>
        <dt>remote schema</dt>
        <dd>{{ rtcSignalingContractProbeResult?.remote_schema ?? "not_loaded" }}</dd>
        <dt>contract status</dt>
        <dd>{{ rtcSignalingContractProbeResult?.contract_status ?? "not_loaded" }}</dd>
        <dt>fail closed reason</dt>
        <dd>{{ rtcSignalingContractProbeResult?.fail_closed_reason ?? "probe_not_loaded" }}</dd>
        <dt>local loopback only</dt>
        <dd>{{ rtcSignalingContractProbeResult?.local_loopback_only ?? true }}</dd>
        <dt>network probe executed</dt>
        <dd>{{ rtcSignalingContractProbeResult?.network_probe_executed ?? false }}</dd>
      </dl>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Protocol surface keys</h3>
          <ul class="dense">
            <!-- 只展示 protocol_surfaces 的 key，不透传 signaling、credential 或未来 URL payload。 -->
            <li v-for="key in rtcSignalingContractProbeResult?.protocol_surface_keys ?? []" :key="key">{{ key }}</li>
            <li v-if="!rtcSignalingContractProbeResult?.protocol_surface_keys.length">not_loaded</li>
          </ul>
          <h3>Core false fields</h3>
          <ul class="dense">
            <!-- PC probe 是 HTTP contract probe，固定不执行真实 RTC/WebRTC/video/ROS2 /tf 探测。 -->
            <li v-for="field in rtcSignalingContractProbeResult?.key_false_fields ?? []" :key="field">{{ field }}</li>
            <li v-if="!rtcSignalingContractProbeResult?.key_false_fields.length">not_loaded</li>
          </ul>
          <h3>Dangerous true fields</h3>
          <ul class="dense">
            <li v-for="field in rtcSignalingContractProbeResult?.dangerous_true_fields ?? []" :key="field">{{ field }}</li>
            <li v-if="!rtcSignalingContractProbeResult?.dangerous_true_fields.length">none</li>
          </ul>
        </div>
        <div>
          <h3>Required evidence refs</h3>
          <ul class="dense">
            <li v-for="refName in rtcSignalingContractProbeResult?.required_evidence_refs ?? []" :key="refName">
              {{ refName }}
            </li>
            <li v-if="!rtcSignalingContractProbeResult?.required_evidence_refs.length">not_loaded</li>
          </ul>
          <h3>Blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in rtcSignalingContractProbeBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h3>Not proven</h3>
          <ul class="dense">
            <li v-for="item in rtcSignalingContractProbeNotProven()" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </article>

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
          <h3>O7 real capability gap summary</h3>
          <ul class="dense">
            <!-- 每个 KR 的 readiness 只来自 acceptance guard surfaces；未加载 guard 时保持 not_loaded。 -->
            <li v-for="group in previewsAcceptanceGapSummary" :key="group.krId">
              {{ group.krId }} {{ group.krName }} · matched surface count={{ group.matchedSurfaceCount }} · surfaces={{
                group.surfaceIds.join(", ")
              }} · ready_for_real_operation={{ group.readyForRealOperation }} · blocked={{
                group.blockedReasons.join(", ")
              }} · not_proven={{ group.notProven.join(", ") }}
            </li>
          </ul>
          <h3>Remaining real capability gaps</h3>
          <ul class="dense">
            <li v-for="gap in previewsAcceptanceRemainingGaps()" :key="gap">{{ gap }}</li>
          </ul>
          <h3>Key guard false fields</h3>
          <ul class="dense">
            <li v-for="field in previewsAcceptanceKeyFalseFields()" :key="field">{{ field }}</li>
          </ul>
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
          <h3>O7 consumer read primary path</h3>
          <p class="eyebrow">Primary task list/detail path via O6 consumer read summary + detail strategy.</p>
        </div>
        <span class="pill danger">{{ consumerTaskListResult?.list_status ?? "not_loaded" }}</span>
      </div>

      <label class="single-input">
        <span>Consumer relay base URL</span>
        <input
          v-model="consumerReadBaseUrl"
          aria-label="O7 consumer read base URL"
          placeholder="http://127.0.0.1:8088"
        >
      </label>
      <div class="route-inputs">
        <button class="secondary" type="button" @click="loadConsumerTaskList">
          {{ consumerTaskListLoading ? "Loading consumer task list" : "Load consumer task list" }}
        </button>
        <button class="secondary" type="button" @click="loadConsumerTaskDetail">
          {{ consumerTaskDetailLoading ? "Loading consumer task detail" : "Load consumer task detail" }}
        </button>
      </div>

      <label class="single-input">
        <span>Selected task ID</span>
        <input
          v-model="consumerSelectedTaskId"
          aria-label="O7 consumer selected task ID"
          placeholder="task_id from consumer task list"
        >
      </label>

      <div v-if="consumerTaskListError" class="notice" role="alert">
        Consumer task list API unavailable: {{ consumerTaskListError }}. safe_to_control=false.
      </div>
      <div v-if="consumerTaskDetailError" class="notice" role="alert">
        Consumer task detail API unavailable: {{ consumerTaskDetailError }}. safe_to_control=false.
      </div>

      <div class="two-col snapshot-grid">
        <div>
          <h3>List strategy</h3>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerTaskListResult?.schema ?? "trashbot.pc_tools_workstation.o7_consumer_task_list.v1" }}</dd>
            <dt>remote endpoint</dt>
            <dd><code>{{ consumerTaskListResult?.remote_endpoint ?? "/api/o6/consumer/tasks?view=summary&limit=50" }}</code></dd>
            <dt>view</dt>
            <dd>{{ consumerTaskListResult?.query_strategy.view ?? "summary" }}</dd>
            <dt>include</dt>
            <dd>{{ consumerTaskListResult?.query_strategy.include.join(",") ?? "none" }}</dd>
            <dt>primary path</dt>
            <dd>{{ consumerTaskListResult?.query_strategy.primary_path ?? true }}</dd>
            <dt>fail-closed visible</dt>
            <dd>{{ consumerTaskListResult?.query_strategy.fail_closed_visible ?? true }}</dd>
            <dt>task count</dt>
            <dd>{{ consumerTaskListResult?.task_list.length ?? 0 }}</dd>
          </dl>
          <table>
            <thead>
              <tr>
                <th>task_id</th>
                <th>status</th>
                <th>labels</th>
                <th>inference</th>
                <th>tunnel</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!consumerTaskListResult?.task_list.length">
                <td colspan="5">blocked_not_proven</td>
              </tr>
              <tr
                v-for="task in consumerTaskListResult?.task_list ?? []"
                :key="task.task_id"
                @click="consumerSelectedTaskId = task.task_id"
              >
                <td>{{ task.task_id }}</td>
                <td>{{ task.task_status_summary }}</td>
                <td>{{ task.labeling_status }}</td>
                <td>{{ task.inference_status }}</td>
                <td>{{ task.tunnel_status_summary }}</td>
              </tr>
            </tbody>
          </table>
          <h3>List blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in consumerListBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h3>List not proven</h3>
          <ul class="dense">
            <li v-for="item in consumerListNotProven()" :key="item">{{ item }}</li>
          </ul>
        </div>

        <div>
          <h3>Detail strategy</h3>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerTaskDetailResult?.schema ?? "trashbot.pc_tools_workstation.o7_consumer_task_detail.v1" }}</dd>
            <dt>remote endpoint</dt>
            <dd><code>{{ consumerTaskDetailResult?.remote_endpoint ?? "/api/o6/consumer/tasks/<task_id>" }}</code></dd>
            <dt>requested task</dt>
            <dd>{{ (consumerTaskDetailResult?.requested_task_id ?? consumerSelectedTaskId) || "not_loaded" }}</dd>
            <dt>view</dt>
            <dd>{{ consumerTaskDetailResult?.query_strategy.view ?? "default" }}</dd>
            <dt>include</dt>
            <dd>{{ consumerTaskDetailResult?.query_strategy.include.join(",") ?? "trajectory,events,evidence,labeling,inference,tunnel" }}</dd>
            <dt>fail-closed visible</dt>
            <dd>{{ consumerTaskDetailResult?.query_strategy.fail_closed_visible ?? true }}</dd>
            <dt>safe_to_control</dt>
            <dd>{{ consumerTaskDetailResult?.safe_to_control ?? false }}</dd>
            <dt>connects_cloud_production</dt>
            <dd>{{ consumerTaskDetailResult?.connects_cloud_production ?? false }}</dd>
            <dt>robot_control_executed</dt>
            <dd>{{ consumerTaskDetailResult?.robot_control_executed ?? false }}</dd>
          </dl>
          <h3>Task summary</h3>
          <dl class="kv compact-kv">
            <dt>task_id</dt>
            <dd>{{ consumerTaskDetailResult?.task_summary?.task_id ?? "blocked_not_proven" }}</dd>
            <dt>robot_id</dt>
            <dd>{{ consumerTaskDetailResult?.task_summary?.robot_id ?? "blocked_not_proven" }}</dd>
            <dt>task_status_summary</dt>
            <dd>{{ consumerTaskDetailResult?.task_summary?.task_status_summary ?? "blocked_not_proven" }}</dd>
            <dt>trajectory</dt>
            <dd>{{ consumerTaskDetailResult?.trajectory.frame_count ?? 0 }} / {{ consumerTaskDetailResult?.trajectory.status ?? "blocked_not_proven" }}</dd>
            <dt>events</dt>
            <dd>{{ consumerTaskDetailResult?.events.count ?? 0 }} / {{ consumerTaskDetailResult?.events.status ?? "blocked_not_proven" }}</dd>
            <dt>evidence</dt>
            <dd>{{ consumerTaskDetailResult?.evidence.count ?? 0 }} / {{ consumerTaskDetailResult?.evidence.status ?? "blocked_not_proven" }}</dd>
            <dt>labeling</dt>
            <dd>{{ consumerTaskDetailResult?.labeling.label_count ?? 0 }} / {{ consumerTaskDetailResult?.labeling.status ?? "blocked_not_proven" }}</dd>
            <dt>inference</dt>
            <dd>{{ consumerTaskDetailResult?.inference.count ?? 0 }} / {{ consumerTaskDetailResult?.inference.status ?? "blocked_not_proven" }}</dd>
            <dt>tunnel</dt>
            <dd>{{ consumerTaskDetailResult?.tunnel_status.latest_known_status ?? "blocked_not_proven" }}</dd>
          </dl>
          <h3>Detail samples</h3>
          <ul class="dense">
            <li>trajectory={{ consumerTaskDetailResult?.trajectory.sample_frames.length ?? 0 }}</li>
            <li>events={{ consumerTaskDetailResult?.events.sample_events.length ?? 0 }}</li>
            <li>evidence={{ consumerTaskDetailResult?.evidence.sample_evidence.length ?? 0 }}</li>
            <li>labeling={{ consumerTaskDetailResult?.labeling.sample_items.length ?? 0 }}</li>
            <li>inference={{ consumerTaskDetailResult?.inference.sample_results.length ?? 0 }}</li>
            <li>temporal_alignment={{ consumerTaskDetailResult?.tunnel_status.temporal_alignment ?? "latest_known_robot_snapshot_not_task_aligned" }}</li>
          </ul>
          <h3>Detail blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in consumerDetailBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h3>Detail not proven</h3>
          <ul class="dense">
            <li v-for="item in consumerDetailNotProven()" :key="item">{{ item }}</li>
          </ul>

          <h3>Consumer-detail labeling queue primary path</h3>
          <div class="notice" role="note">
            consumer-detail labeling primary path · submit_enabled=false · export_enabled=false ·
            rollback_enabled=false · dataset_export_available=false · real_annotation_api_connected=false ·
            safe_to_control=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>cursor_status</dt>
            <dd>{{ consumerDetailLabelingQueueNavigationEnabled ? "consumer_detail_labeling_queue_ready" : "blocked_not_proven" }}</dd>
            <dt>blocked_reason</dt>
            <dd>{{ consumerDetailLabelingQueueBlockedReason || "none_consumer_detail_only" }}</dd>
            <dt>summary</dt>
            <dd>{{ consumerDetailLabelingQueueSummary }}</dd>
            <dt>current task</dt>
            <dd>{{ consumerTaskDetailResult?.task_summary?.task_id ?? "blocked_not_proven" }}</dd>
            <dt>labeling status</dt>
            <dd>{{ consumerTaskDetailResult?.labeling.status ?? "blocked_not_proven" }}</dd>
            <dt>label count</dt>
            <dd>{{ consumerTaskDetailResult?.labeling.label_count ?? 0 }}</dd>
            <dt>evidence count</dt>
            <dd>{{ consumerTaskDetailResult?.evidence.count ?? 0 }}</dd>
            <dt>event count</dt>
            <dd>{{ consumerTaskDetailResult?.events.count ?? 0 }}</dd>
            <dt>trajectory frame count</dt>
            <dd>{{ consumerTaskDetailResult?.trajectory.frame_count ?? 0 }}</dd>
            <dt>submit_enabled</dt>
            <dd>false</dd>
            <dt>export_enabled</dt>
            <dd>false</dd>
            <dt>rollback_enabled</dt>
            <dd>false</dd>
            <dt>real_annotation_api_connected</dt>
            <dd>false</dd>
            <dt>dataset_export_available</dt>
            <dd>false</dd>
            <dt>connects_cloud_production</dt>
            <dd>{{ consumerTaskDetailResult?.connects_cloud_production ?? false }}</dd>
            <dt>safe_to_control</dt>
            <dd>{{ consumerTaskDetailResult?.safe_to_control ?? false }}</dd>
            <dt>primary_actions_enabled</dt>
            <dd>{{ consumerTaskDetailResult?.primary_actions_enabled ?? false }}</dd>
            <dt>robot_control_executed</dt>
            <dd>{{ consumerTaskDetailResult?.robot_control_executed ?? false }}</dd>
          </dl>
          <h3>Labeling queue check rows</h3>
          <ul class="dense">
            <li v-if="!consumerDetailLabelingQueueRowSummaries.length">blocked_not_proven</li>
            <li v-for="row in consumerDetailLabelingQueueRowSummaries" :key="row">{{ row }}</li>
          </ul>
          <h3>Labeling queue false fields</h3>
          <ul class="dense">
            <li v-for="field in consumerDetailLabelingQueueFalseFields()" :key="field">{{ field }}</li>
          </ul>
          <h3>Consumer-detail labeling queue notes</h3>
          <ul class="dense">
            <li>consumer-detail labeling primary path uses task detail labels plus evidence/events/trajectory checks</li>
            <li>submit/export/rollback stay closed; archive fixture review panel only survives as debug fallback</li>
            <li>missing detail, labeling, evidence, events or trajectory keeps the view blocked_not_proven</li>
          </ul>

          <h3>Consumer-detail route replay player</h3>
          <div class="notice" role="note">
            local_detail_cursor_only · sends_to_robot=false · safe_to_control=false · primary_actions_enabled=false ·
            local_state_only=true · playback_available=false
          </div>
          <dl class="kv compact-kv">
            <dt>cursor_status</dt>
            <dd>{{ routeReplayNavigationEnabled ? "local_consumer_detail_cursor_ready" : "blocked_not_proven" }}</dd>
            <dt>blocked_reason</dt>
            <dd>{{ routeReplayBlockedReason || "none_consumer_detail_only" }}</dd>
            <dt>current frame</dt>
            <dd>{{ routeReplayCursorDisplay() }}</dd>
            <dt>frame_index</dt>
            <dd>{{ currentRouteReplayFrame?.frame_index ?? "blocked_not_proven" }}</dd>
            <dt>timestamp_ms</dt>
            <dd>{{ currentRouteReplayFrame?.timestamp_ms ?? "null" }}</dd>
            <dt>state</dt>
            <dd>{{ currentRouteReplayFrame?.state ?? "blocked_not_proven" }}</dd>
            <dt>evidence_ref</dt>
            <dd>{{ currentRouteReplayFrame?.evidence_ref ?? "blocked_not_proven" }}</dd>
            <dt>frame_summary</dt>
            <dd>{{ currentRouteReplayFrameSummary }}</dd>
            <dt>playing</dt>
            <dd>{{ routeReplayPlaying }}</dd>
            <dt>trajectory_points</dt>
            <dd>{{ routeReplayTrajectoryPoints.length }}</dd>
          </dl>
          <div class="route-inputs">
            <button class="secondary" type="button" :disabled="!routeReplayNavigationEnabled" @click="toggleRouteReplayPlayback">
              {{ routeReplayPlaying ? "Pause" : "Play" }}
            </button>
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
            <button class="secondary" type="button" :disabled="!routeReplayNavigationEnabled" @click="resetRouteReplayCursor">
              Reset cursor
            </button>
          </div>
          <label class="single-input">
            <span>Frame cursor</span>
            <input
              aria-label="Consumer route replay frame cursor"
              type="range"
              min="0"
              :max="Math.max(routeReplayFrames.length - 1, 0)"
              :value="routeReplayCursor"
              :disabled="!routeReplayNavigationEnabled"
              @input="setRouteReplayCursorFromInput"
            >
          </label>

          <h3>Consumer-detail trajectory minimap</h3>
          <div class="notice" role="note">
            readonly_consumer_detail_trajectory_only · no_real_map_loaded · no_robot_motion_claim · safe_to_control=false ·
            primary_actions_enabled=false · robot_control_executed=false
          </div>
          <div class="two-col snapshot-grid">
            <div>
              <svg
                aria-label="Consumer-detail route replay trajectory minimap"
                role="img"
                viewBox="0 0 100 100"
                width="100%"
                height="220"
                preserveAspectRatio="xMidYMid meet"
                style="display: block; width: 100%; min-height: 220px; border: 1px solid #d7dee6; border-radius: 6px; background: #f7f9fb;"
              >
                <!-- 这里只消费 consumer detail 的 x/y 样本，固定 viewBox 防止极端值把布局撑坏。 -->
                <rect x="10" y="10" width="80" height="80" fill="#ffffff" stroke="#d7dee6" stroke-width="0.8" />
                <line x1="10" y1="50" x2="90" y2="50" stroke="#d7dee6" stroke-width="0.4" />
                <line x1="50" y1="10" x2="50" y2="90" stroke="#d7dee6" stroke-width="0.4" />
                <polyline
                  v-if="routeReplayMinimapStatus !== 'blocked_not_proven'"
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
                  v-if="routeReplayMinimapStatus !== 'blocked_not_proven' && currentRouteReplayMinimapMarker"
                  :cx="currentRouteReplayMinimapMarker.svg_x"
                  :cy="currentRouteReplayMinimapMarker.svg_y"
                  r="4"
                  fill="#9a3412"
                  stroke="#ffffff"
                  stroke-width="1.4"
                />
                <text
                  v-if="routeReplayMinimapStatus === 'blocked_not_proven'"
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
                <dd>{{ consumerTaskDetailResult?.trajectory.status ?? "blocked_not_proven" }}</dd>
                <dt>current_marker</dt>
                <dd>{{ routeReplayCurrentMarkerStatus }}</dd>
                <dt>task_status_summary</dt>
                <dd>{{ consumerRouteReplayTaskSummary?.task_status_summary ?? "blocked_not_proven" }}</dd>
                <dt>safe_to_control</dt>
                <dd>false</dd>
                <dt>primary_actions_enabled</dt>
                <dd>false</dd>
                <dt>robot_control_executed</dt>
                <dd>false</dd>
              </dl>
            </div>
          </div>

          <h3>Route replay frame samples</h3>
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
              <tr v-if="!routeReplayFrames.length">
                <td colspan="8">blocked_not_proven</td>
              </tr>
              <tr v-for="frame in routeReplayFrames" :key="`${frame.cursor_index}:${frame.frame_index}`">
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

          <h3>Route replay sample summaries</h3>
          <div class="two-col snapshot-grid">
            <div>
              <h4>Events</h4>
              <ul class="dense">
                <li v-for="item in consumerRouteReplayEventSummaries" :key="item">{{ item }}</li>
                <li v-if="!consumerRouteReplayEventSummaries.length">blocked_not_proven</li>
              </ul>
              <h4>Evidence</h4>
              <ul class="dense">
                <li v-for="item in consumerRouteReplayEvidenceSummaries" :key="item">{{ item }}</li>
                <li v-if="!consumerRouteReplayEvidenceSummaries.length">blocked_not_proven</li>
              </ul>
            </div>
            <div>
              <h4>Labeling</h4>
              <ul class="dense">
                <li v-for="item in consumerRouteReplayLabelingSummaries" :key="item">{{ item }}</li>
                <li v-if="!consumerRouteReplayLabelingSummaries.length">blocked_not_proven</li>
              </ul>
              <h4>Inference</h4>
              <ul class="dense">
                <li v-for="item in consumerRouteReplayInferenceSummaries" :key="item">{{ item }}</li>
                <li v-if="!consumerRouteReplayInferenceSummaries.length">blocked_not_proven</li>
              </ul>
              <h4>Tunnel</h4>
              <ul class="dense">
                <li v-for="item in consumerRouteReplayTunnelSummary" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
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
        <dt>probe observed at ms</dt>
        <dd>{{ realtimeElevatorProbeResult?.probe_observed_at_ms ?? "not_loaded" }}</dd>
        <dt>remote pose timestamp ms</dt>
        <dd>{{ realtimeElevatorProbeResult?.remote_pose_timestamp_ms ?? "not_loaded" }}</dd>
        <dt>remote pose age ms</dt>
        <dd>{{ realtimeElevatorProbeResult?.remote_pose_age_ms ?? "not_loaded" }}</dd>
        <dt>freshness gate status</dt>
        <dd>{{ realtimeElevatorProbeResult?.freshness_gate_status ?? "blocked_not_proven" }}</dd>
        <dt>latency_lt_2s_proven</dt>
        <dd>{{ realtimeElevatorProbeResult?.latency_lt_2s_proven ?? false }}</dd>
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

      <div class="two-col snapshot-grid">
        <div>
          <h3>Realtime map pose preview</h3>
          <div class="notice" role="note">
            readonly_probe_summary_svg_only · no_real_map_loaded · no_ros2_tf_read · no_realtime_api_from_browser ·
            safe_to_control=false
          </div>
          <svg
            aria-label="Realtime map pose preview"
            role="img"
            viewBox="0 0 100 100"
            width="100%"
            height="220"
            preserveAspectRatio="xMidYMid meet"
            style="display: block; width: 100%; min-height: 220px; border: 1px solid #d7dee6; border-radius: 6px; background: #f7f9fb;"
          >
            <!-- SVG 只由 robot_pose_summary 字符串派生，不能回退到真实地图、/tf 或默认中心 marker。 -->
            <rect x="10" y="10" width="80" height="80" fill="#ffffff" stroke="#d7dee6" stroke-width="0.8" />
            <line x1="10" y1="50" x2="90" y2="50" stroke="#d7dee6" stroke-width="0.5" />
            <line x1="50" y1="10" x2="50" y2="90" stroke="#d7dee6" stroke-width="0.5" />
            <text x="12" y="18" fill="#5f6b7a" font-size="4">map frame</text>
            <g v-if="realtimePosePreview">
              <!-- heading 只表示 fixture/probe 摘要 yaw，不代表真实机器人朝向或可控制状态。 -->
              <line
                :x1="realtimePosePreview.svg_x"
                :y1="realtimePosePreview.svg_y"
                :x2="realtimePosePreview.heading_x"
                :y2="realtimePosePreview.heading_y"
                stroke="#9a3412"
                stroke-width="2.8"
                stroke-linecap="round"
              />
              <circle
                :cx="realtimePosePreview.svg_x"
                :cy="realtimePosePreview.svg_y"
                r="4.5"
                fill="#315f8a"
                stroke="#ffffff"
                stroke-width="1.5"
              />
            </g>
            <text
              v-else
              x="50"
              y="50"
              text-anchor="middle"
              dominant-baseline="middle"
              fill="#8a1f1f"
              font-size="5"
            >
              blocked_pose_coordinate_unavailable
            </text>
          </svg>
        </div>
        <div>
          <h3>Pose safety fields</h3>
          <dl class="kv compact-kv">
            <dt>map_visualization_status</dt>
            <dd>{{ realtimeMapVisualizationStatus }}</dd>
            <dt>pose_marker</dt>
            <dd>{{ realtimePoseMarkerStatus }}</dd>
            <dt>map_frame/ref</dt>
            <dd>
              {{ realtimeElevatorProbeResult?.map_frame_summary ?? "not_loaded" }} /
              {{ realtimeElevatorProbeResult?.map_ref_summary ?? "not_loaded" }}
            </dd>
            <dt>latency_lt_2s_proven</dt>
            <dd>false</dd>
            <dt>probe_observed_at_ms</dt>
            <dd>{{ realtimeElevatorProbeResult?.probe_observed_at_ms ?? "not_loaded" }}</dd>
            <dt>remote_pose_timestamp_ms</dt>
            <dd>{{ realtimeElevatorProbeResult?.remote_pose_timestamp_ms ?? "not_loaded" }}</dd>
            <dt>remote_pose_age_ms</dt>
            <dd>{{ realtimeElevatorProbeResult?.remote_pose_age_ms ?? "not_loaded" }}</dd>
            <dt>freshness_gate_status</dt>
            <dd>{{ realtimeElevatorProbeResult?.freshness_gate_status ?? "blocked_not_proven" }}</dd>
            <dt>real_ros2_tf_connected</dt>
            <dd>false</dd>
            <dt>real_realtime_api_connected</dt>
            <dd>false</dd>
            <dt>safe_to_control</dt>
            <dd>false</dd>
            <dt>robot_control_executed</dt>
            <dd>false</dd>
          </dl>
        </div>
      </div>

      <div class="two-col snapshot-grid">
        <div>
          <h3>Elevator state timeline preview</h3>
          <div class="notice" role="note">
            readonly_probe_summary_timeline_only · no_elevator_device_read · no_auto_refresh · safe_to_control=false
          </div>
          <ol class="dense">
            <!-- timeline 只展示 probe 已限量摘要的前 5 条，不能推断完整电梯状态链已接通。 -->
            <li v-for="(sample, index) in realtimeElevatorTimelineSamples" :key="`${index}:${sample}`">
              sample_index={{ index }} · {{ sample }}
            </li>
            <li v-if="!realtimeElevatorTimelineSamples.length">blocked_not_proven</li>
          </ol>
        </div>
        <div>
          <h3>Timeline safety fields</h3>
          <dl class="kv compact-kv">
            <dt>real_elevator_state_chain_connected</dt>
            <dd>false</dd>
            <dt>floor_recognition_proven</dt>
            <dd>false</dd>
            <dt>human_takeover_proven</dt>
            <dd>false</dd>
            <dt>safe_to_control</dt>
            <dd>false</dd>
          </dl>
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
        <dd>{{ fixtureRouteReplayNavigationEnabled ? "local_fixture_cursor_ready" : "blocked_not_proven" }}</dd>
        <dt>blocked_reason</dt>
        <dd>{{ fixtureRouteReplayBlockedReason || "none_local_fixture_only" }}</dd>
        <dt>current frame</dt>
        <dd>{{ fixtureRouteReplayCursorDisplay() }}</dd>
        <dt>frame_index</dt>
        <dd>{{ currentFixtureRouteReplayFrame?.frame_index ?? "blocked_not_proven" }}</dd>
        <dt>timestamp_ms</dt>
        <dd>{{ currentFixtureRouteReplayFrame?.timestamp_ms ?? "null" }}</dd>
        <dt>pose</dt>
        <dd>
          x={{ currentFixtureRouteReplayFrame?.x_m ?? "null" }},
          y={{ currentFixtureRouteReplayFrame?.y_m ?? "null" }},
          yaw={{ currentFixtureRouteReplayFrame?.yaw_rad ?? "null" }}
        </dd>
        <dt>velocity</dt>
        <dd>{{ currentFixtureRouteReplayFrame?.speed_mps ?? "null" }} mps</dd>
        <dt>state</dt>
        <dd>{{ currentFixtureRouteReplayFrame?.state ?? "blocked_not_proven" }}</dd>
        <dt>evidence_ref</dt>
        <dd>{{ currentFixtureRouteReplayFrame?.evidence_ref ?? "blocked_not_proven" }}</dd>
      </dl>
      <div class="route-inputs">
        <!-- 这些按钮只改变本地数组下标，不调用 API，也不代表真实云回放或机器人运动。 -->
        <button
          class="secondary"
          type="button"
          :disabled="!fixtureRouteReplayNavigationEnabled || fixtureRouteReplayCursor <= 0"
          @click="previousFixtureRouteReplayFrame"
        >
          Previous frame
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!fixtureRouteReplayNavigationEnabled || fixtureRouteReplayCursor >= fixtureRouteReplayFrames.length - 1"
          @click="nextFixtureRouteReplayFrame"
        >
          Next frame
        </button>
        <button
          class="secondary"
          type="button"
          :disabled="!fixtureRouteReplayNavigationEnabled"
          @click="resetFixtureRouteReplayCursor"
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
          :max="Math.max(fixtureRouteReplayFrames.length - 1, 0)"
          :value="fixtureRouteReplayCursor"
          :disabled="!fixtureRouteReplayNavigationEnabled"
          @input="setFixtureRouteReplayCursorFromInput"
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
              v-if="fixtureRouteReplayMinimapStatus === 'readonly_fixture_trajectory_ready'"
              :points="fixtureRouteReplayMinimapPolyline"
              fill="none"
              stroke="#315f8a"
              stroke-width="2.4"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <circle
              v-for="point in fixtureRouteReplayMinimapPoints"
              :key="`${point.cursor_index}:${point.frame_index}`"
              :cx="point.svg_x"
              :cy="point.svg_y"
              r="1.8"
              fill="#5f6b7a"
            />
            <circle
              v-if="fixtureRouteReplayMinimapStatus === 'readonly_fixture_trajectory_ready' && currentFixtureRouteReplayMinimapMarker"
              :cx="currentFixtureRouteReplayMinimapMarker.svg_x"
              :cy="currentFixtureRouteReplayMinimapMarker.svg_y"
              r="4"
              fill="#9a3412"
              stroke="#ffffff"
              stroke-width="1.4"
            />
            <text
              v-if="fixtureRouteReplayMinimapStatus !== 'readonly_fixture_trajectory_ready'"
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
              v-else-if="!currentFixtureRouteReplayMinimapMarker"
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
            <dd>{{ fixtureRouteReplayMinimapStatus }}</dd>
            <dt>trajectory_points</dt>
            <dd>{{ fixtureRouteReplayTrajectoryPoints.length }}</dd>
            <dt>map_frame</dt>
            <dd>{{ archiveResult?.route_replay_inspector.map_frame ?? "blocked_not_proven" }}</dd>
            <dt>current_marker</dt>
            <dd>{{ fixtureRouteReplayCurrentMarkerStatus }}</dd>
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

      <h3>Labeling queue inspector debug fallback</h3>
      <dl class="kv compact-kv">
        <dt>status</dt>
        <dd>{{ archiveResult?.labeling_queue_inspector.status ?? "blocked_not_proven" }}</dd>
        <dt>selected_task_id</dt>
        <dd>{{ archiveResult?.labeling_queue_inspector.selected_task_id ?? "null" }}</dd>
        <dt>review_item_count</dt>
        <dd>{{ archiveResult?.labeling_queue_inspector.review_item_count ?? 0 }}</dd>
      </dl>

      <h3>Debug fallback: archive fixture labeling review panel</h3>
      <div class="notice" role="note">
        debug_fallback_only · local_fixture_item_cursor_only · consumer-detail labeling primary path stays isolated ·
        submit_enabled=false · rollback_enabled=false · dataset_export_available=false ·
        real_annotation_api_connected=false · draft_labels.autosave_available=false
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
