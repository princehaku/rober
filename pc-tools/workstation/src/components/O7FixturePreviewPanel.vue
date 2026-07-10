<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import {
  getO7CloudArchiveTasks,
  getO7CloudArchiveTasksProbe,
  getO7CloudOperatorConsoleProbe,
  getO7ConsumerTaskDetail,
  getO7ConsumerTaskList,
  getO7ConsumerAnnotationExport,
  getO7LiveEndpointsManifest,
  getO7PreviewsAcceptance,
  getO7RealtimeElevatorProbe,
  getO7RtcSignalingContractProbe,
  loadO7FixturePreview,
  postO7ConsumerAnnotationSubmit,
} from "../client/workstationApi";
import type { O7FixturePreviewInputs, O7FixturePreviewKind, O7FixturePreviewResponses } from "../client/workstationApi";
import type {
  O7AnnotationDatasetExportResult,
  O7AnnotationSubmitLabel,
  O7AnnotationSubmitResult,
  O7ConsumerArtifactAccessProbeSummary,
  O7ConsumerArtifactBundleConsumerIngestSummary,
  O7ConsumerArtifactBundleReadiness,
  O7ConsumerArtifactBundleSummary,
  O7ConsumerDeliveryResultEvidenceSummary,
  O7ConsumerFieldMotionEvidencePacketSummary,
  O7ConsumerNav2GoalExecutionEvidenceSummary,
  O7ConsumerOfflineArtifactSeedSmokeSummary,
  O7ConsumerRouteDeliveryClosurePacketSummary,
  O7ConsumerCurrentFieldEvidenceMaterialSummary,
  O7ConsumerLocalizationPathMaterialReadbackSummary,
  O7ConsumerCleanBaselineNav2PathMaterialSummary,
  O7ConsumerFieldOperatorConfirmationMaterialSummary,
  O7ConsumerRouteExecutionResultDeliveryReadinessSummary,
  O7ConsumerSameTaskFieldMaterialPacketSummary,
  O7ConsumerSameTaskRouteExecutionMaterialPacketSummary,
  O7ConsumerSameTaskMissionEvidenceGateSummary,
  O7ConsumerSameTaskMissionMaterialChecklist,
  O7ConsumerRouteBagEvidenceSummary,
  O7ConsumerRouteBagFullSemanticDecodeMatrixSummary,
  O7ConsumerRouteBagPayloadReplaySummary,
  O7ConsumerRouteBagPoseProgressReplaySummary,
  O7ConsumerRouteBagSemanticReplaySummary,
  O7ConsumerRouteRootSeedGateSummary,
  O7CloudArchiveTasksProbeResponse,
  O7CloudArchiveTasksResponse,
  O7FieldEvidenceConsumerIngestResponse,
  O7ConsumerLabelingMvpReviewItem,
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
const consumerFieldEvidenceManifestJson = ref("");
const consumerTaskDetailResult = ref<O7ConsumerTaskDetailResponse | null>(null);
const consumerTaskDetailError = ref("");
const consumerTaskDetailLoading = ref(false);
const consumerAnnotationSubmitResult = ref<O7AnnotationSubmitResult | null>(null);
const consumerAnnotationSubmitError = ref("");
const consumerAnnotationSubmitLoading = ref(false);
const consumerAnnotationExportResult = ref<O7AnnotationDatasetExportResult | null>(null);
const consumerAnnotationExportError = ref("");
const consumerAnnotationExportLoading = ref(false);
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
  sampleRecords(
    consumerTaskDetailResult.value?.route_replay_mvp?.trajectory.sample_frames ??
      consumerTaskDetailResult.value?.trajectory.sample_frames,
  ).map((frame, cursorIndex) =>
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
  if (detail.route_replay_mvp) {
    return detail.route_replay_mvp.status === "consumer_detail_replay_ready"
      ? ""
      : detail.route_replay_mvp.blocked_reasons[0] ?? "trajectory_missing";
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
const consumerArtifactMediaPreflight = computed(() => consumerTaskDetailResult.value?.artifact_media_preflight ?? null);
const consumerArtifactAccessProbe = computed<O7ConsumerArtifactAccessProbeSummary | null>(
  () => consumerTaskDetailResult.value?.artifact_access_probe ?? consumerArtifactBundleReadiness.value?.artifact_access_probe ?? null,
);
const consumerOfflineArtifactSeedSmoke = computed<O7ConsumerOfflineArtifactSeedSmokeSummary | null>(
  () =>
    consumerTaskDetailResult.value?.offline_artifact_seed_smoke ??
    consumerArtifactBundleReadiness.value?.offline_artifact_seed_smoke ??
    null,
);
const consumerRouteRootSeedGate = computed<O7ConsumerRouteRootSeedGateSummary | null>(
  () =>
    consumerTaskDetailResult.value?.route_root_seed_gate ??
    consumerArtifactBundleReadiness.value?.route_root_seed_gate ??
    null,
);
const consumerRouteBagEvidence = computed<O7ConsumerRouteBagEvidenceSummary | null>(
  () =>
    consumerTaskDetailResult.value?.route_bag_evidence ??
    consumerArtifactBundleReadiness.value?.route_bag_evidence ??
    null,
);
const consumerRouteBagPayloadReplay = computed<O7ConsumerRouteBagPayloadReplaySummary | null>(
  () =>
    consumerTaskDetailResult.value?.route_bag_payload_replay ??
    consumerArtifactBundleReadiness.value?.route_bag_payload_replay ??
    null,
);
const consumerRouteBagSemanticReplay = computed<O7ConsumerRouteBagSemanticReplaySummary | null>(
  () =>
    consumerTaskDetailResult.value?.route_bag_semantic_replay ??
    consumerArtifactBundleReadiness.value?.route_bag_semantic_replay ??
    null,
);
const consumerRouteBagFullSemanticDecodeMatrix = computed<O7ConsumerRouteBagFullSemanticDecodeMatrixSummary | null>(
  () =>
    consumerTaskDetailResult.value?.route_bag_full_semantic_decode_matrix ??
    consumerArtifactBundleReadiness.value?.route_bag_full_semantic_decode_matrix ??
    null,
);
const consumerRouteBagPoseProgressReplay = computed<O7ConsumerRouteBagPoseProgressReplaySummary | null>(
  () =>
    consumerTaskDetailResult.value?.route_bag_pose_progress_replay ??
    consumerArtifactBundleReadiness.value?.route_bag_pose_progress_replay ??
    null,
);
const consumerFieldMotionEvidencePacket = computed<O7ConsumerFieldMotionEvidencePacketSummary | null>(
  () =>
    consumerTaskDetailResult.value?.field_motion_evidence_packet ??
    consumerArtifactBundleReadiness.value?.field_motion_evidence_packet ??
    null,
);
const consumerNav2GoalExecutionEvidence = computed<O7ConsumerNav2GoalExecutionEvidenceSummary | null>(
  () =>
    consumerTaskDetailResult.value?.nav2_goal_execution_evidence ??
    consumerArtifactBundleReadiness.value?.nav2_goal_execution_evidence ??
    null,
);
const consumerDeliveryResultEvidence = computed<O7ConsumerDeliveryResultEvidenceSummary | null>(
  () =>
    consumerTaskDetailResult.value?.delivery_result_evidence ??
    consumerArtifactBundleReadiness.value?.delivery_result_evidence ??
    null,
);
const consumerRouteExecutionResultDeliveryReadiness = computed<
  O7ConsumerRouteExecutionResultDeliveryReadinessSummary | null
>(
  () =>
    consumerTaskDetailResult.value?.route_execution_result_delivery_readiness ??
    consumerArtifactBundleReadiness.value?.route_execution_result_delivery_readiness ??
    null,
);
const consumerRouteDeliveryClosurePacket = computed<O7ConsumerRouteDeliveryClosurePacketSummary | null>(
  () =>
    consumerTaskDetailResult.value?.route_delivery_closure_packet ??
    consumerArtifactBundleReadiness.value?.route_delivery_closure_packet ??
    null,
);
const consumerSameTaskFieldMaterialPacket = computed<O7ConsumerSameTaskFieldMaterialPacketSummary | null>(
  () =>
    consumerTaskDetailResult.value?.same_task_field_material_packet ??
    consumerArtifactBundleReadiness.value?.same_task_field_material_packet ??
    null,
);
const consumerCurrentFieldEvidenceMaterial = computed<O7ConsumerCurrentFieldEvidenceMaterialSummary | null>(
  () => consumerTaskDetailResult.value?.current_field_evidence_material ?? null,
);
const consumerLocalizationPathMaterialReadback = computed<O7ConsumerLocalizationPathMaterialReadbackSummary | null>(
  () =>
    consumerTaskDetailResult.value?.localization_path_material_readback ??
    consumerArtifactBundleReadiness.value?.localization_path_material_readback ??
    null,
);
const consumerCleanBaselineNav2PathMaterial = computed<O7ConsumerCleanBaselineNav2PathMaterialSummary | null>(
  () => consumerTaskDetailResult.value?.clean_baseline_nav2_path_material ?? null,
);
const consumerSameTaskRouteExecutionMaterialPacket = computed<
  O7ConsumerSameTaskRouteExecutionMaterialPacketSummary | null
>(
  () =>
    consumerTaskDetailResult.value?.same_task_route_execution_material_packet ??
    consumerArtifactBundleReadiness.value?.same_task_route_execution_material_packet ??
    null,
);
const consumerSameTaskMissionEvidenceGate = computed<O7ConsumerSameTaskMissionEvidenceGateSummary | null>(
  () =>
    consumerTaskDetailResult.value?.same_task_mission_evidence_gate ??
    consumerArtifactBundleReadiness.value?.same_task_mission_evidence_gate ??
    null,
);
const consumerFieldOperatorConfirmationMaterial = computed<O7ConsumerFieldOperatorConfirmationMaterialSummary | null>(
  () =>
    consumerTaskDetailResult.value?.field_operator_confirmation_material ??
    consumerArtifactBundleReadiness.value?.field_operator_confirmation_material ??
    null,
);
const consumerSameTaskMissionMaterialChecklist = computed<O7ConsumerSameTaskMissionMaterialChecklist | null>(
  () =>
    consumerTaskDetailResult.value?.same_task_mission_material_checklist ??
    consumerArtifactBundleReadiness.value?.same_task_mission_material_checklist ??
    null,
);
const consumerArtifactBundle = computed<O7ConsumerArtifactBundleSummary | null>(
  () => consumerTaskDetailResult.value?.artifact_bundle ?? null,
);
const consumerArtifactBundleConsumerIngest = computed<O7ConsumerArtifactBundleConsumerIngestSummary | null>(
  () => consumerTaskDetailResult.value?.artifact_bundle_consumer_ingest ?? null,
);
const consumerArtifactBundleReadiness = computed<O7ConsumerArtifactBundleReadiness | null>(
  () => consumerTaskDetailResult.value?.artifact_bundle_readiness ?? null,
);
const consumerRouteReplayMvp = computed(() => consumerTaskDetailResult.value?.route_replay_mvp ?? null);
const consumerLabelingMvp = computed(() => consumerTaskDetailResult.value?.labeling_mvp ?? null);
const consumerRouteReplayEventSummaries = computed(() =>
  consumerRouteReplayMvp.value?.events_timeline.sample.length
    ? consumerRouteReplayMvp.value.events_timeline.sample.map((event, index) =>
        [
          `${index + 1}.`,
          `event_type=${event.event_type}`,
          `state=${event.state}`,
          `timestamp_ms=${event.timestamp_ms ?? "null"}`,
          `evidence_ref=${event.evidence_ref}`,
        ].join(" · "),
      )
    : sampleDetailSummaries(consumerTaskDetailResult.value?.events.sample_events, "event"),
);
const consumerRouteReplayEvidenceSummaries = computed(() =>
  consumerRouteReplayMvp.value?.evidence_refs.sample_refs.length
    ? consumerRouteReplayMvp.value.evidence_refs.sample_refs.map((refValue, index) => `${index + 1}. evidence_ref=${refValue}`)
    : sampleDetailSummaries(consumerTaskDetailResult.value?.evidence.sample_evidence, "evidence"),
);
const consumerRouteReplayLabelingSummaries = computed(() =>
  consumerLabelingMvp.value?.review_items.sample.length
    ? consumerLabelingMvp.value.review_items.sample.map((item, index) =>
        [
          `${index + 1}.`,
          `item_id=${item.item_id}`,
          `frame_id=${item.frame_id}`,
          `media_ref=${item.media_ref}`,
          `evidence_ref=${item.evidence_ref}`,
          `current_labels=${item.current_labels.count}`,
        ].join(" · "),
      )
    : sampleDetailSummaries(consumerTaskDetailResult.value?.labeling.sample_items, "labeling"),
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

const consumerRouteReplayMediaDependency = computed(
  () =>
    consumerArtifactBundleReadiness.value?.route_replay_dependency ??
    consumerRouteReplayMvp.value?.media_preflight_dependency ??
    consumerArtifactMediaPreflight.value?.route_replay_dependency ??
    null,
);

const consumerLabelingMediaDependency = computed(
  () =>
    consumerArtifactBundleReadiness.value?.labeling_dependency ??
    consumerLabelingMvp.value?.media_preflight_dependency ??
    consumerArtifactMediaPreflight.value?.labeling_dependency ??
    null,
);

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
  if (detail.labeling_mvp) {
    return detail.labeling_mvp.status === "consumer_detail_labeling_ready"
      ? ""
      : detail.labeling_mvp.blocked_reasons[0] ?? "labeling_missing";
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
  const labelingMvp = consumerLabelingMvp.value;
  if (labelingMvp) {
    return labelingMvp.review_items.sample.map((item, index) => {
      const draft = labelingMvp.draft_labels.sample[index];
      return [
        `#${index + 1}`,
        `review_item=${item.item_id}`,
        `media_ref=${item.media_ref}`,
        `evidence_ref=${item.evidence_ref}`,
        `current_labels=${item.current_labels.count}`,
        `draft_label=${draft ? `${draft.label_type}:${draft.value}:${draft.status}` : "blocked_not_proven"}`,
        `submit_receipt=${labelingMvp.submit_receipt.status}`,
      ].join(" · ");
    });
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

const consumerLabelingMvpCurrentItem = computed<O7ConsumerLabelingMvpReviewItem | null>(() =>
  consumerLabelingMvp.value?.review_items.current_item ?? null,
);

const consumerAnnotationActionBlockedReason = computed(() => {
  const queueBlocked = consumerDetailLabelingQueueBlockedReason.value;
  // submit/export 复用 labeling 主路径关闸，避免绕过 detail readiness 和 task_id 一致性检查。
  if (queueBlocked) {
    return queueBlocked;
  }
  if (!consumerTaskDetailResult.value?.task_summary?.robot_id) {
    return "robot_id_missing";
  }
  if (!consumerLabelingMvpCurrentItem.value) {
    return "review_item_missing";
  }
  if (!consumerLabelingMvp.value?.draft_labels.sample.length) {
    return "draft_label_missing";
  }
  return "";
});

const consumerAnnotationSubmitEnabled = computed(() =>
  !consumerAnnotationSubmitLoading.value && consumerAnnotationActionBlockedReason.value === "",
);

const consumerAnnotationExportEnabled = computed(() =>
  !consumerAnnotationExportLoading.value && consumerAnnotationActionBlockedReason.value === "",
);

function buildConsumerAnnotationSubmitLabels(): O7AnnotationSubmitLabel[] {
  // 只把当前 review item 的第一条 draft 转成 O6 labels 白名单字段，不透传 UI/detail 原始对象。
  const item = consumerLabelingMvpCurrentItem.value;
  const draft = consumerLabelingMvp.value?.draft_labels.sample[0];
  if (!item || !draft) {
    return [];
  }
  return [
    {
      item_id: item.item_id,
      item_type: "consumer_detail_review_item",
      label_type: draft.label_type,
      value: draft.value,
      confidence: null,
      annotator_id: "pc_o7_local_mock",
      evidence_ref: draft.evidence_ref || item.evidence_ref,
      notes: "local/mock submit from PC O7 consumer detail; not production",
    },
  ];
}

const consumerAnnotationSubmitSummary = computed(() => {
  const receipt = consumerAnnotationSubmitResult.value?.submit_receipt;
  // receipt 摘要突出 local/mock 和 not_proven，避免 operator 误读成生产云提交。
  if (!receipt) {
    return `local/mock submit not run · blocker=${consumerAnnotationActionBlockedReason.value || "none"}`;
  }
  return [
    `status=${receipt.status}`,
    `receipt_id=${receipt.receipt_id}`,
    `task_id=${receipt.task_id}`,
    `label_count=${receipt.label_count}`,
    `write_status=${receipt.write_status}`,
    `local_mock_annotation_submit_written=${consumerAnnotationSubmitResult.value?.local_mock_annotation_submit_written ?? false}`,
    `not_proven=true`,
  ].join(" · ");
});

const consumerAnnotationExportSummary = computed(() => {
  const exportResult = consumerAnnotationExportResult.value;
  // export 只展示 task-level JSONL manifest 摘要，不展示真实文件路径或训练集可用声明。
  if (!exportResult) {
    return `local/mock dataset export not run · blocker=${consumerAnnotationActionBlockedReason.value || "none"}`;
  }
  return [
    `status=${exportResult.export_status}`,
    `manifest_id=${exportResult.export_manifest.manifest_id}`,
    `task_id=${exportResult.export_manifest.task_id}`,
    `format=${exportResult.export_manifest.format}`,
    `label_count=${exportResult.export_manifest.label_count}`,
    `row_count=${exportResult.export_manifest.row_count}`,
    `dataset_export_available=${exportResult.dataset_export_available}`,
    `not_proven=true`,
  ].join(" · ");
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
    `real_dataset_export_connected=false`,
    `cloud_write_executed=false`,
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
  if (consumerArtifactBundleReadiness.value) {
    return [
      `artifact_bundle_readiness`,
      `task_id=${consumerArtifactBundleReadiness.value.task_id}`,
      `route_ref_count=${consumerArtifactBundleReadiness.value.counts.route_ref_count}`,
      `review_item_count=${consumerArtifactBundleReadiness.value.counts.review_item_count}`,
      `sample_ref_count=${consumerArtifactBundleReadiness.value.counts.sample_ref_count}`,
      `route_bag_status=${consumerArtifactBundleReadiness.value.route_bag_evidence?.status ?? "blocked_not_proven"}`,
      `route_bag_payload_replay_status=${consumerArtifactBundleReadiness.value.route_bag_payload_replay?.status ?? "blocked_not_proven"}`,
      `route_bag_semantic_replay_status=${consumerArtifactBundleReadiness.value.route_bag_semantic_replay?.status ?? "blocked_not_proven"}`,
      `route_bag_full_semantic_decode_matrix_status=${consumerArtifactBundleReadiness.value.route_bag_full_semantic_decode_matrix?.status ?? "blocked_not_proven"}`,
      `field_motion_status=${consumerArtifactBundleReadiness.value.field_motion_evidence_packet?.status ?? "blocked_not_proven"}`,
      `nav2_goal_status=${consumerArtifactBundleReadiness.value.nav2_goal_execution_evidence?.status ?? "blocked_not_proven"}`,
      `delivery_result_status=${consumerArtifactBundleReadiness.value.delivery_result_evidence?.status ?? "blocked_not_proven"}`,
      `route_execution_result_delivery_readiness_status=${consumerArtifactBundleReadiness.value.route_execution_result_delivery_readiness?.status ?? "blocked_not_proven"}`,
      `route_delivery_closure_packet_status=${consumerArtifactBundleReadiness.value.route_delivery_closure_packet?.status ?? "blocked_not_proven"}`,
      `same_task_field_material_packet_status=${consumerArtifactBundleReadiness.value.same_task_field_material_packet?.status ?? "blocked_not_proven"}`,
      `same_task_route_execution_material_packet_status=${consumerArtifactBundleReadiness.value.same_task_route_execution_material_packet?.status ?? "blocked_not_proven"}`,
      `same_task_mission_gate_status=${consumerArtifactBundleReadiness.value.same_task_mission_evidence_gate?.status ?? "blocked_not_proven"}`,
      `same_task_mission_material_checklist_status=${consumerArtifactBundleReadiness.value.same_task_mission_material_checklist?.status ?? "blocked_not_proven"}`,
      `blocked_reasons=${consumerArtifactBundleReadiness.value.blocked_reasons.length}`,
    ].join(" · ");
  }
  if (detail.labeling_mvp) {
    return [
      `consumer-detail labeling primary path`,
      `task_id=${detail.labeling_mvp.selected_task_id}`,
      `review_item_count=${detail.labeling_mvp.review_items.review_item_count}`,
      `allowed_label_types=${detail.labeling_mvp.allowed_label_types.length}`,
      `draft_label_count=${detail.labeling_mvp.draft_labels.count}`,
      `submit_receipt=${detail.labeling_mvp.submit_receipt.status}`,
    ].join(" · ");
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

function consumerArtifactBundleReadinessSummary(): string {
  const readiness = consumerArtifactBundleReadiness.value;
  // readiness 是 O7 consumer detail 的主入口摘要；没有 bundle 时明确回到 blocked_not_proven。
  if (!readiness) {
    return "blocked_not_proven";
  }
  const routeBagStatus = readiness.route_bag_evidence?.status ?? "blocked_not_proven";
  const routeBagPayloadReplayStatus = readiness.route_bag_payload_replay?.status ?? "blocked_not_proven";
  const routeBagSemanticReplayStatus = readiness.route_bag_semantic_replay?.status ?? "blocked_not_proven";
  const routeBagFullSemanticDecodeMatrixStatus =
    readiness.route_bag_full_semantic_decode_matrix?.status ?? "blocked_not_proven";
  const routeBagPoseProgressReplayStatus = readiness.route_bag_pose_progress_replay?.status ?? "blocked_not_proven";
  const fieldMotionStatus = readiness.field_motion_evidence_packet?.status ?? "blocked_not_proven";
  const nav2GoalStatus = readiness.nav2_goal_execution_evidence?.status ?? "blocked_not_proven";
  const deliveryResultStatus = readiness.delivery_result_evidence?.status ?? "blocked_not_proven";
  const routeExecutionResultDeliveryReadinessStatus =
    readiness.route_execution_result_delivery_readiness?.status ?? "blocked_not_proven";
  const routeDeliveryClosurePacketStatus =
    readiness.route_delivery_closure_packet?.status ?? "blocked_not_proven";
  const sameTaskFieldMaterialPacketStatus =
    readiness.same_task_field_material_packet?.status ?? "blocked_not_proven";
  const sameTaskRouteExecutionMaterialPacketStatus =
    readiness.same_task_route_execution_material_packet?.status ?? "blocked_not_proven";
  const sameTaskMissionGateStatus =
    readiness.same_task_mission_evidence_gate?.status ?? "blocked_not_proven";
  const fieldOperatorConfirmationMaterialStatus =
    readiness.field_operator_confirmation_material?.status ?? "blocked_not_proven";
  const sameTaskMissionMaterialChecklistStatus =
    readiness.same_task_mission_material_checklist?.status ?? "blocked_not_proven";
  return [
    `artifact_bundle_readiness`,
    `status=${readiness.status}`,
    `task_id=${readiness.task_id}`,
    `source_contract=${readiness.source_contract}`,
    `source_origin=${readiness.source_origin}`,
    `route_ref_count=${readiness.counts.route_ref_count}`,
    `replay_ref_count=${readiness.counts.replay_ref_count}`,
    `keyframe_ref_count=${readiness.counts.keyframe_ref_count}`,
    `evidence_ref_count=${readiness.counts.evidence_ref_count}`,
    `review_item_count=${readiness.counts.review_item_count}`,
    `sample_ref_count=${readiness.counts.sample_ref_count}`,
    `review_item_media_ref_count=${readiness.counts.review_item_media_ref_count}`,
    `route_bag_status=${routeBagStatus}`,
    `route_bag_topic_count=${readiness.route_bag_evidence?.topic_count ?? 0}`,
    `route_bag_payload_replay_status=${routeBagPayloadReplayStatus}`,
    `route_bag_payload_sample_count=${readiness.route_bag_payload_replay?.payload_sample_count ?? 0}`,
    `route_bag_semantic_replay_status=${routeBagSemanticReplayStatus}`,
    `route_bag_semantic_decode_ok_count=${readiness.route_bag_semantic_replay?.semantic_decode_ok_count ?? 0}`,
    `route_bag_full_semantic_decode_matrix_status=${routeBagFullSemanticDecodeMatrixStatus}`,
    `route_bag_full_semantic_decode_matrix_coverage_ratio=${readiness.route_bag_full_semantic_decode_matrix?.coverage_ratio ?? 0}`,
    `route_bag_full_semantic_decoded_topic_type_count=${readiness.route_bag_full_semantic_decode_matrix?.decoded_topic_type_count ?? 0}`,
    `route_bag_full_semantic_unsupported_topic_type_count=${readiness.route_bag_full_semantic_decode_matrix?.unsupported_topic_type_count ?? 0}`,
    `route_bag_full_semantic_failed_topic_type_count=${readiness.route_bag_full_semantic_decode_matrix?.failed_topic_type_count ?? 0}`,
    `route_bag_pose_progress_replay_status=${routeBagPoseProgressReplayStatus}`,
    `route_bag_pose_sample_count=${readiness.route_bag_pose_progress_replay?.pose_sample_count ?? 0}`,
    `route_bag_pose_nonzero_observed=${readiness.route_bag_pose_progress_replay?.nonzero_pose_progress_observed ?? false}`,
    `field_motion_status=${fieldMotionStatus}`,
    `nav2_goal_status=${nav2GoalStatus}`,
    `delivery_result_status=${deliveryResultStatus}`,
    `route_execution_result_delivery_readiness_status=${routeExecutionResultDeliveryReadinessStatus}`,
    `route_delivery_closure_packet_status=${routeDeliveryClosurePacketStatus}`,
    `same_task_field_material_packet_status=${sameTaskFieldMaterialPacketStatus}`,
    `same_task_route_execution_material_packet_status=${sameTaskRouteExecutionMaterialPacketStatus}`,
    `same_task_mission_gate_status=${sameTaskMissionGateStatus}`,
    `field_operator_confirmation_material_status=${fieldOperatorConfirmationMaterialStatus}`,
    `same_task_mission_material_checklist_status=${sameTaskMissionMaterialChecklistStatus}`,
    `same_task_terminal_source=${readiness.same_task_mission_evidence_gate?.terminal_result_source ?? "not_loaded"}`,
    `same_task_terminal_schema=${readiness.same_task_mission_evidence_gate?.terminal_source_schema ?? "not_loaded"}`,
  ].join(" · ");
}

function consumerArtifactBundleReadinessCounts(): string[] {
  const readiness = consumerArtifactBundleReadiness.value;
  if (!readiness) {
    return ["blocked_not_proven"];
  }
  return [
    `route_ref_count=${readiness.counts.route_ref_count}`,
    `replay_ref_count=${readiness.counts.replay_ref_count}`,
    `keyframe_ref_count=${readiness.counts.keyframe_ref_count}`,
    `evidence_ref_count=${readiness.counts.evidence_ref_count}`,
    `review_item_count=${readiness.counts.review_item_count}`,
    `sample_ref_count=${readiness.counts.sample_ref_count}`,
    `review_item_media_ref_count=${readiness.counts.review_item_media_ref_count}`,
  ];
}

function consumerArtifactBundleReadinessRefs(): string[] {
  const readiness = consumerArtifactBundleReadiness.value;
  if (!readiness) {
    return ["blocked_not_proven"];
  }
  return [
    `route_refs=${readiness.refs.route_refs.join(",") || "none"}`,
    `replay_refs=${readiness.refs.replay_refs.join(",") || "none"}`,
    `keyframe_refs=${readiness.refs.keyframe_refs.join(",") || "none"}`,
    `evidence_refs=${readiness.refs.evidence_refs.join(",") || "none"}`,
    `review_item_media_refs=${readiness.refs.review_item_media_refs.join(",") || "none"}`,
    `sample_refs=${readiness.refs.sample_refs.join(",") || "none"}`,
  ];
}

function consumerArtifactAccessProbeSummary(): string {
  const probe = consumerArtifactAccessProbe.value;
  // probe 摘要只读 O7 后端已脱敏字段，不展示 allowlist root、原始 ref 或完整 sha256。
  if (!probe) {
    return "artifact_access_probe=blocked_not_proven";
  }
  return [
    `artifact_access_probe`,
    `status=${probe.status}`,
    `source_origin=${probe.source_origin}`,
    `task_id=${probe.task_id}`,
    `requested=${probe.counts.requested_ref_count}`,
    `readable=${probe.counts.readable_ref_count}`,
    `blocked=${probe.counts.blocked_ref_count}`,
    `missing=${probe.counts.missing_ref_count}`,
  ].join(" · ");
}

function consumerOfflineArtifactSeedSmokeSummary(): string {
  const smoke = consumerOfflineArtifactSeedSmoke.value;
  // offline seed smoke 只展示离线路线材料的安全摘要，不把 ref 当成真实媒体或生产云证据。
  if (!smoke) {
    return "offline_artifact_seed_smoke=blocked_not_proven";
  }
  return [
    `offline_artifact_seed_smoke`,
    `status=${smoke.status}`,
    `source_origin=${smoke.source_origin}`,
    `task_id=${smoke.task_id}`,
    `route_ref_count=${smoke.counts.route_ref_count}`,
    `replay_ref_count=${smoke.counts.replay_ref_count}`,
    `keyframe_ref_count=${smoke.counts.keyframe_ref_count}`,
    `evidence_ref_count=${smoke.counts.evidence_ref_count}`,
    `sample_ref_count=${smoke.counts.sample_ref_count}`,
  ].join(" · ");
}

function consumerOfflineArtifactSeedSmokeCounts(): string[] {
  const smoke = consumerOfflineArtifactSeedSmoke.value;
  if (!smoke) {
    return ["blocked_not_proven"];
  }
  return [
    `route_ref_count=${smoke.counts.route_ref_count}`,
    `replay_ref_count=${smoke.counts.replay_ref_count}`,
    `keyframe_ref_count=${smoke.counts.keyframe_ref_count}`,
    `evidence_ref_count=${smoke.counts.evidence_ref_count}`,
    `sample_ref_count=${smoke.counts.sample_ref_count}`,
    `readable_ref_count=${smoke.counts.readable_ref_count}`,
    `blocked_ref_count=${smoke.counts.blocked_ref_count}`,
    `missing_ref_count=${smoke.counts.missing_ref_count}`,
  ];
}

function consumerOfflineArtifactSeedSmokeRefs(): string[] {
  const smoke = consumerOfflineArtifactSeedSmoke.value;
  if (!smoke) {
    return ["blocked_not_proven"];
  }
  return [
    `sample_refs=${smoke.sample_refs.join(",") || "none"}`,
    `sample_sha256_prefixes=${smoke.sample_sha256_prefixes.join(",") || "none"}`,
  ];
}

function consumerOfflineArtifactSeedSmokeBlockedReasons(): string[] {
  const smoke = consumerOfflineArtifactSeedSmoke.value;
  if (!smoke) {
    return ["blocked_not_proven"];
  }
  return smoke.blocked_reasons.length ? smoke.blocked_reasons : ["blocked_not_proven"];
}

function consumerOfflineArtifactSeedSmokeNextEvidence(): string[] {
  const smoke = consumerOfflineArtifactSeedSmoke.value;
  if (!smoke) {
    return ["blocked_not_proven"];
  }
  return smoke.next_required_evidence.length ? smoke.next_required_evidence : ["blocked_not_proven"];
}

function consumerRouteRootSeedGateSummary(): string {
  const gate = consumerRouteRootSeedGate.value;
  // route-root seed gate 只展示 O6 摘要，不能把缺 route_bag 解释成真实路线执行完成。
  if (!gate) {
    return "route_root_seed_gate=blocked_not_proven";
  }
  return [
    `route_root_seed_gate`,
    `status=${gate.status}`,
    `route_root_seed_status=${gate.route_root_seed_status}`,
    `source_origin=${gate.source_origin}`,
    `task_id=${gate.task_id}`,
    `route_bag_required=${String(gate.route_bag_required)}`,
    `route_bag_present=${String(gate.route_bag_present)}`,
  ].join(" · ");
}

function consumerRouteRootSeedGateCounts(): string[] {
  const gate = consumerRouteRootSeedGate.value;
  if (!gate) {
    return ["blocked_not_proven"];
  }
  return [
    `route_frame_count=${gate.counts.route_frame_count}`,
    `derived_replay_frame_count=${gate.counts.derived_replay_frame_count}`,
    `route_ref_count=${gate.counts.route_ref_count}`,
    `manifest_ref_count=${gate.counts.manifest_ref_count}`,
    `replay_ref_count=${gate.counts.replay_ref_count}`,
    `keyframe_ref_count=${gate.counts.keyframe_ref_count}`,
    `evidence_ref_count=${gate.counts.evidence_ref_count}`,
    `sample_ref_count=${gate.counts.sample_ref_count}`,
  ];
}

function consumerRouteRootSeedGateRefs(): string[] {
  const gate = consumerRouteRootSeedGate.value;
  if (!gate) {
    return ["blocked_not_proven"];
  }
  return [`sample_refs=${gate.sample_refs.join(",") || "none"}`];
}

function consumerRouteRootSeedGateFalseFields(): string[] {
  const gate = consumerRouteRootSeedGate.value;
  // route_bag 缺失是可见的 pending evidence，但控制、交付和生产云字段仍必须保持 false。
  return [
    `route_bag_required=${String(gate?.route_bag_required ?? false)}`,
    `route_bag_present=${String(gate?.route_bag_present ?? false)}`,
    `safe_to_control=${String(gate?.safe_to_control ?? false)}`,
    `delivery_success=${String(gate?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(gate?.primary_actions_enabled ?? false)}`,
    `robot_control_executed=${String(gate?.robot_control_executed ?? false)}`,
    `connects_cloud_production=${String(gate?.connects_cloud_production ?? false)}`,
    `media_access_proven=${String(gate?.media_access_proven ?? false)}`,
    `real_oss_connected=${String(gate?.real_oss_connected ?? false)}`,
    `real_cdn_connected=${String(gate?.real_cdn_connected ?? false)}`,
  ];
}

function consumerRouteBagEvidenceSummary(): string {
  const evidence = consumerRouteBagEvidence.value;
  // route bag 摘要只展示 DB3/metadata 结构计数，不展开原始 bag、路径或消息 payload。
  if (!evidence) {
    return "route_bag_evidence=blocked_not_proven";
  }
  return [
    `route_bag_evidence`,
    `status=${evidence.status}`,
    `route_bag_source=${evidence.route_bag_source}`,
    `source_label=${evidence.source_label}`,
    `task_id=${evidence.task_id}`,
    `metadata_present=${evidence.metadata_present}`,
    `db3_present=${evidence.db3_present}`,
    `db3_read_ok=${evidence.db3_read_ok}`,
  ].join(" · ");
}

function consumerRouteBagEvidenceCounts(): string[] {
  const evidence = consumerRouteBagEvidence.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `topic_count=${evidence.topic_count}`,
    `message_count=${evidence.message_count}`,
    `db3_size_bytes=${evidence.db3_size_bytes ?? "null"}`,
    `db3_sha256_prefix=${evidence.db3_sha256_prefix || "not_loaded"}`,
    `timestamp_first_ns=${evidence.timestamp_first_ns ?? "null"}`,
    `timestamp_last_ns=${evidence.timestamp_last_ns ?? "null"}`,
    `sample_topic_names=${evidence.sample_topic_names.join(",") || "none"}`,
  ];
}

function consumerRouteBagEvidenceSources(): string[] {
  const evidence = consumerRouteBagEvidence.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `schema=${evidence.schema}`,
    `source_contract=${evidence.source_contract}`,
    `source_origin=${evidence.source_origin}`,
    `source_path=${evidence.source_path}`,
    `proof_scope=${evidence.proof_scope}`,
    `task_id_source=${evidence.task_id_source}`,
  ];
}

function consumerRouteBagEvidenceFalseFields(): string[] {
  const evidence = consumerRouteBagEvidence.value;
  // DB3 可读不等于 live Nav2 run、路线执行成功或送达成功，所有安全动作字段固定 false。
  return [
    `safe_to_control=${String(evidence?.safe_to_control ?? false)}`,
    `delivery_success=${String(evidence?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(evidence?.primary_actions_enabled ?? false)}`,
    `robot_control_executed=${String(evidence?.robot_control_executed ?? false)}`,
    `connects_cloud_production=${String(evidence?.connects_cloud_production ?? false)}`,
    `media_access_proven=${String(evidence?.media_access_proven ?? false)}`,
    `real_oss_connected=${String(evidence?.real_oss_connected ?? false)}`,
    `real_cdn_connected=${String(evidence?.real_cdn_connected ?? false)}`,
    `route_execution_success=${String(evidence?.proof_boundary.route_execution_success ?? false)}`,
    `live_nav2_run_connected=${String(evidence?.proof_boundary.live_nav2_run_connected ?? false)}`,
  ];
}

function consumerRouteBagPayloadReplaySummary(): string {
  const evidence = consumerRouteBagPayloadReplay.value;
  // payload replay 只展示 DB3 payload 派生摘要，不回显 raw/base64/content/完整 hash 或路径。
  if (!evidence) {
    return "route_bag_payload_replay=blocked_not_proven";
  }
  return [
    `route_bag_payload_replay`,
    `status=${evidence.status}`,
    `route_bag_source=${evidence.route_bag_source}`,
    `source_label=${evidence.source_label}`,
    `task_id=${evidence.task_id}`,
    `metadata_present=${evidence.metadata_present}`,
    `db3_present=${evidence.db3_present}`,
    `db3_read_ok=${evidence.db3_read_ok}`,
  ].join(" · ");
}

function consumerRouteBagPayloadReplayCounts(): string[] {
  const evidence = consumerRouteBagPayloadReplay.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `topic_count=${evidence.topic_count}`,
    `message_count=${evidence.message_count}`,
    `db3_size_bytes=${evidence.db3_size_bytes ?? "null"}`,
    `db3_sha256_prefix=${evidence.db3_sha256_prefix || "not_loaded"}`,
    `timestamp_first_ns=${evidence.timestamp_first_ns ?? "null"}`,
    `timestamp_last_ns=${evidence.timestamp_last_ns ?? "null"}`,
    `payload_sample_count=${evidence.payload_sample_count}`,
    `payload_size_min_bytes=${evidence.payload_size_min_bytes ?? "null"}`,
    `payload_size_max_bytes=${evidence.payload_size_max_bytes ?? "null"}`,
    `payload_size_avg_bytes=${evidence.payload_size_avg_bytes ?? "null"}`,
    `payload_sha256_prefix_samples=${evidence.payload_sha256_prefix_samples.join(",") || "none"}`,
    `sample_topic_names=${evidence.sample_topic_names.join(",") || "none"}`,
  ];
}

function consumerRouteBagPayloadReplaySources(): string[] {
  const evidence = consumerRouteBagPayloadReplay.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `schema=${evidence.schema}`,
    `source_contract=${evidence.source_contract}`,
    `source_origin=${evidence.source_origin}`,
    `source_path=${evidence.source_path}`,
    `proof_scope=${evidence.proof_scope}`,
    `task_id_source=${evidence.task_id_source}`,
  ];
}

function consumerRouteBagPayloadReplayFalseFields(): string[] {
  const evidence = consumerRouteBagPayloadReplay.value;
  // payload replay 只是回放准备，不是路线执行成功或控制成功。
  return [
    `safe_to_control=${String(evidence?.safe_to_control ?? false)}`,
    `delivery_success=${String(evidence?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(evidence?.primary_actions_enabled ?? false)}`,
    `robot_control_executed=${String(evidence?.robot_control_executed ?? false)}`,
    `connects_cloud_production=${String(evidence?.connects_cloud_production ?? false)}`,
    `media_access_proven=${String(evidence?.media_access_proven ?? false)}`,
    `real_oss_connected=${String(evidence?.real_oss_connected ?? false)}`,
    `real_cdn_connected=${String(evidence?.real_cdn_connected ?? false)}`,
    `route_execution_success=${String(evidence?.proof_boundary.route_execution_success ?? false)}`,
    `live_nav2_run_connected=${String(evidence?.proof_boundary.live_nav2_run_connected ?? false)}`,
  ];
}

function consumerRouteBagSemanticReplaySummary(): string {
  const evidence = consumerRouteBagSemanticReplay.value;
  // semantic replay 只展示 LaserScan/Image/TF/Odometry 白名单语义摘要，不展示 raw payload、path 或媒体内容。
  if (!evidence) {
    return "route_bag_semantic_replay=blocked_not_proven";
  }
  return [
    `route_bag_semantic_replay`,
    `status=${evidence.status}`,
    `semantic_decode_status=${evidence.semantic_decode_status}`,
    `route_bag_source=${evidence.route_bag_source}`,
    `source_label=${evidence.source_label}`,
    `task_id=${evidence.task_id}`,
    `metadata_present=${evidence.metadata_present}`,
    `db3_present=${evidence.db3_present}`,
    `db3_read_ok=${evidence.db3_read_ok}`,
  ].join(" · ");
}

function consumerRouteBagSemanticReplayCounts(): string[] {
  const evidence = consumerRouteBagSemanticReplay.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `topic_count=${evidence.topic_count}`,
    `message_count=${evidence.message_count}`,
    `db3_size_bytes=${evidence.db3_size_bytes ?? "null"}`,
    `db3_sha256_prefix=${evidence.db3_sha256_prefix || "not_loaded"}`,
    `timestamp_first_ns=${evidence.timestamp_first_ns ?? "null"}`,
    `timestamp_last_ns=${evidence.timestamp_last_ns ?? "null"}`,
    `semantic_sample_count=${evidence.semantic_sample_count}`,
    `semantic_decode_ok_count=${evidence.semantic_decode_ok_count}`,
    `semantic_decode_failed_count=${evidence.semantic_decode_failed_count}`,
    `semantic_topic_types=${evidence.semantic_topic_types.join(",") || "none"}`,
    `sample_topic_names=${evidence.sample_topic_names.join(",") || "none"}`,
  ];
}

function consumerRouteBagSemanticReplayDecodeSummaries(): string[] {
  const evidence = consumerRouteBagSemanticReplay.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    [
      "laser_scan_summary",
      `sample_count=${evidence.laser_scan_summary.sample_count}`,
      `range_sample_length=${evidence.laser_scan_summary.range_sample_length ?? "null"}`,
      `finite_count=${evidence.laser_scan_summary.finite_count ?? "null"}`,
      `range_min=${evidence.laser_scan_summary.range_min ?? "null"}`,
      `range_max=${evidence.laser_scan_summary.range_max ?? "null"}`,
      `angle_min=${evidence.laser_scan_summary.angle_min ?? "null"}`,
      `angle_max=${evidence.laser_scan_summary.angle_max ?? "null"}`,
      `angle_increment=${evidence.laser_scan_summary.angle_increment ?? "null"}`,
    ].join(" · "),
    [
      "image_summary",
      `sample_count=${evidence.image_summary.sample_count}`,
      `width=${evidence.image_summary.width ?? "null"}`,
      `height=${evidence.image_summary.height ?? "null"}`,
      `encoding=${evidence.image_summary.encoding}`,
      `step=${evidence.image_summary.step ?? "null"}`,
      `data_size=${evidence.image_summary.data_size ?? "null"}`,
    ].join(" · "),
    [
      "tf_summary",
      `sample_count=${evidence.tf_summary.sample_count}`,
      `transform_count=${evidence.tf_summary.transform_count ?? "null"}`,
      `frame_id_samples=${evidence.tf_summary.frame_id_samples.join(",") || "none"}`,
      `child_frame_id_samples=${evidence.tf_summary.child_frame_id_samples.join(",") || "none"}`,
    ].join(" · "),
  ];
}

function consumerRouteBagSemanticReplaySources(): string[] {
  const evidence = consumerRouteBagSemanticReplay.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `schema=${evidence.schema}`,
    `source_contract=${evidence.source_contract}`,
    `source_origin=${evidence.source_origin}`,
    `source_path=${evidence.source_path}`,
    `proof_scope=${evidence.proof_scope}`,
    `task_id_source=${evidence.task_id_source}`,
  ];
}

function consumerRouteBagSemanticReplayFalseFields(): string[] {
  const evidence = consumerRouteBagSemanticReplay.value;
  // 语义摘要 ready 也不代表真实路径执行或真实送达，所有控制/生产字段继续固定 false。
  return [
    `safe_to_control=${String(evidence?.safe_to_control ?? false)}`,
    `delivery_success=${String(evidence?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(evidence?.primary_actions_enabled ?? false)}`,
    `robot_control_executed=${String(evidence?.robot_control_executed ?? false)}`,
    `connects_cloud_production=${String(evidence?.connects_cloud_production ?? false)}`,
    `media_access_proven=${String(evidence?.media_access_proven ?? false)}`,
    `real_oss_connected=${String(evidence?.real_oss_connected ?? false)}`,
    `real_cdn_connected=${String(evidence?.real_cdn_connected ?? false)}`,
    `route_execution_success=${String(evidence?.proof_boundary.route_execution_success ?? false)}`,
    `live_nav2_run_connected=${String(evidence?.proof_boundary.live_nav2_run_connected ?? false)}`,
  ];
}

function consumerRouteBagFullSemanticDecodeMatrixSummary(): string {
  const matrix = consumerRouteBagFullSemanticDecodeMatrix.value;
  // full semantic matrix ready 只说明离线 topic/type 覆盖矩阵可读，不说明 route execution 或 delivery 成功。
  if (!matrix) {
    return "route_bag_full_semantic_decode_matrix=blocked_not_proven";
  }
  return [
    `route_bag_full_semantic_decode_matrix`,
    `status=${matrix.status}`,
    `semantic_decode_matrix_status=${matrix.semantic_decode_matrix_status}`,
    `coverage_ratio=${matrix.coverage_ratio}`,
    `route_bag_source=${matrix.route_bag_source}`,
    `source_label=${matrix.source_label}`,
    `task_id=${matrix.task_id}`,
  ].join(" · ");
}

function consumerRouteBagFullSemanticDecodeMatrixCounts(): string[] {
  const matrix = consumerRouteBagFullSemanticDecodeMatrix.value;
  if (!matrix) {
    return ["blocked_not_proven"];
  }
  return [
    `topic_type_count=${matrix.topic_type_count}`,
    `decoded_topic_type_count=${matrix.decoded_topic_type_count}`,
    `unsupported_topic_type_count=${matrix.unsupported_topic_type_count}`,
    `failed_topic_type_count=${matrix.failed_topic_type_count}`,
    `decoded_message_sample_count=${matrix.decoded_message_sample_count}`,
    `unsupported_message_sample_count=${matrix.unsupported_message_sample_count}`,
    `decode_failed_message_sample_count=${matrix.decode_failed_message_sample_count}`,
    `coverage_ratio=${matrix.coverage_ratio}`,
  ];
}

function consumerRouteBagFullSemanticDecodeMatrixSamples(): string[] {
  const matrix = consumerRouteBagFullSemanticDecodeMatrix.value;
  if (!matrix) {
    return ["blocked_not_proven"];
  }
  if (!matrix.sample_topic_type_matrix.length) {
    return ["sample_topic_type_matrix=none"];
  }
  return matrix.sample_topic_type_matrix.map((item, index) =>
    [
      `${index + 1}.`,
      `topic_name=${item.topic_name}`,
      `topic_type=${item.topic_type}`,
      `decode_status=${item.decode_status}`,
      `decoder_name=${item.decoder_name}`,
      `decoded=${item.decoded_message_sample_count}`,
      `unsupported=${item.unsupported_message_sample_count}`,
      `failed=${item.decode_failed_message_sample_count}`,
      `blocked_reason=${item.blocked_reason}`,
    ].join(" · "),
  );
}

function consumerRouteBagFullSemanticDecodeMatrixSources(): string[] {
  const matrix = consumerRouteBagFullSemanticDecodeMatrix.value;
  if (!matrix) {
    return ["blocked_not_proven"];
  }
  return [
    `schema=${matrix.schema}`,
    `source_contract=${matrix.source_contract}`,
    `source_origin=${matrix.source_origin}`,
    `source_path=${matrix.source_path}`,
    `proof_scope=${matrix.proof_scope}`,
    `task_id_source=${matrix.task_id_source}`,
    `sample_topic_names=${matrix.sample_topic_names.join(",") || "none"}`,
    `sample_topic_types=${matrix.sample_topic_types.join(",") || "none"}`,
  ];
}

function consumerRouteBagFullSemanticDecodeMatrixFalseFields(): string[] {
  const matrix = consumerRouteBagFullSemanticDecodeMatrix.value;
  // coverage matrix 只读展示不能打开生产云、媒体、控制或交付成功语义。
  return [
    `safe_to_control=${String(matrix?.safe_to_control ?? false)}`,
    `delivery_success=${String(matrix?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(matrix?.primary_actions_enabled ?? false)}`,
    `robot_control_executed=${String(matrix?.robot_control_executed ?? false)}`,
    `connects_cloud_production=${String(matrix?.connects_cloud_production ?? false)}`,
    `media_access_proven=${String(matrix?.media_access_proven ?? false)}`,
    `real_oss_connected=${String(matrix?.real_oss_connected ?? false)}`,
    `real_cdn_connected=${String(matrix?.real_cdn_connected ?? false)}`,
    `route_execution_success=${String(matrix?.proof_boundary.route_execution_success ?? false)}`,
    `live_nav2_run_connected=${String(matrix?.proof_boundary.live_nav2_run_connected ?? false)}`,
  ];
}

function consumerRouteBagPoseProgressReplaySummary(): string {
  const evidence = consumerRouteBagPoseProgressReplay.value;
  // 位姿进度只展示安全摘要，不把 frame 或 pose 扩展成真实 live Nav2 证据。
  if (!evidence) {
    return "route_bag_pose_progress_replay=blocked_not_proven";
  }
  return [
    `route_bag_pose_progress_replay`,
    `status=${evidence.status}`,
    `pose_decode_status=${evidence.pose_decode_status}`,
    `route_bag_source=${evidence.route_bag_source}`,
    `source_label=${evidence.source_label}`,
    `task_id=${evidence.task_id}`,
    `metadata_present=${evidence.metadata_present}`,
    `db3_present=${evidence.db3_present}`,
    `db3_read_ok=${evidence.db3_read_ok}`,
  ].join(" · ");
}

function consumerRouteBagPoseProgressReplayCounts(): string[] {
  const evidence = consumerRouteBagPoseProgressReplay.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `topic_count=${evidence.topic_count}`,
    `message_count=${evidence.message_count}`,
    `db3_size_bytes=${evidence.db3_size_bytes ?? "null"}`,
    `db3_sha256_prefix=${evidence.db3_sha256_prefix || "not_loaded"}`,
    `timestamp_first_ns=${evidence.timestamp_first_ns ?? "null"}`,
    `timestamp_last_ns=${evidence.timestamp_last_ns ?? "null"}`,
    `pose_sample_count=${evidence.pose_sample_count}`,
    `pose_decode_ok_count=${evidence.pose_decode_ok_count}`,
    `pose_decode_failed_count=${evidence.pose_decode_failed_count}`,
    `pose_topic_types=${evidence.pose_topic_types.join(",") || "none"}`,
    `pose_frame_pairs=${evidence.pose_frame_pairs
      .map((pair) => `${pair.source_frame_id}->${pair.target_frame_id}x${pair.sample_count}`)
      .join(",") || "none"}`,
    `pose_time_span_ns=${evidence.pose_time_span_ns ?? "null"}`,
    `sample_topic_names=${evidence.sample_topic_names.join(",") || "none"}`,
  ];
}

function consumerRouteBagPoseProgressReplayPoseSummaries(): string[] {
  const evidence = consumerRouteBagPoseProgressReplay.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    [
      "start_pose",
      `frame_id=${evidence.start_pose.frame_id}`,
      `x_m=${evidence.start_pose.x_m ?? "null"}`,
      `y_m=${evidence.start_pose.y_m ?? "null"}`,
      `yaw_rad=${evidence.start_pose.yaw_rad ?? "null"}`,
      `timestamp_ns=${evidence.start_pose.timestamp_ns ?? "null"}`,
    ].join(" · "),
    [
      "end_pose",
      `frame_id=${evidence.end_pose.frame_id}`,
      `x_m=${evidence.end_pose.x_m ?? "null"}`,
      `y_m=${evidence.end_pose.y_m ?? "null"}`,
      `yaw_rad=${evidence.end_pose.yaw_rad ?? "null"}`,
      `timestamp_ns=${evidence.end_pose.timestamp_ns ?? "null"}`,
    ].join(" · "),
    [
      "progress",
      `displacement_m=${evidence.displacement_m}`,
      `nonzero_pose_progress_observed=${evidence.nonzero_pose_progress_observed}`,
    ].join(" · "),
  ];
}

function consumerRouteBagPoseProgressReplaySources(): string[] {
  const evidence = consumerRouteBagPoseProgressReplay.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `schema=${evidence.schema}`,
    `source_contract=${evidence.source_contract}`,
    `source_origin=${evidence.source_origin}`,
    `source_path=${evidence.source_path}`,
    `proof_scope=${evidence.proof_scope}`,
    `task_id_source=${evidence.task_id_source}`,
  ];
}

function consumerRouteBagPoseProgressReplayFalseFields(): string[] {
  const evidence = consumerRouteBagPoseProgressReplay.value;
  // 位姿进度 ready 也不代表可控或真实执行，false fields 必须显式保留。
  return [
    `safe_to_control=${String(evidence?.safe_to_control ?? false)}`,
    `delivery_success=${String(evidence?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(evidence?.primary_actions_enabled ?? false)}`,
    `robot_control_executed=${String(evidence?.robot_control_executed ?? false)}`,
    `connects_cloud_production=${String(evidence?.connects_cloud_production ?? false)}`,
    `media_access_proven=${String(evidence?.media_access_proven ?? false)}`,
    `real_oss_connected=${String(evidence?.real_oss_connected ?? false)}`,
    `real_cdn_connected=${String(evidence?.real_cdn_connected ?? false)}`,
    `route_execution_success=${String(evidence?.proof_boundary.route_execution_success ?? false)}`,
    `live_nav2_run_connected=${String(evidence?.proof_boundary.live_nav2_run_connected ?? false)}`,
  ];
}

function consumerFieldMotionEvidencePacketSummary(): string {
  const packet = consumerFieldMotionEvidencePacket.value;
  // field motion 摘要只暴露同一 task 的 frame/motion/log gap，不展示 route bag/live log 原始路径。
  if (!packet) {
    return "field_motion_evidence_packet=blocked_not_proven";
  }
  return [
    `field_motion_evidence_packet`,
    `status=${packet.status}`,
    `task_id=${packet.task_id}`,
    `frame_count=${packet.route_summary.frame_count}`,
    `nonzero_displacement_observed=${packet.route_summary.nonzero_displacement_observed}`,
    `displacement_m=${packet.route_summary.displacement_m}`,
    `live_motion_evidence_present=${packet.motion_log_summary.live_motion_evidence_present}`,
    `route_bag_or_live_nav2_log_present=${packet.route_bag_or_live_nav2_log.present}`,
    `source=${packet.route_bag_or_live_nav2_log.source}`,
  ].join(" · ");
}

function consumerFieldMotionEvidencePacketCounts(): string[] {
  const packet = consumerFieldMotionEvidencePacket.value;
  if (!packet) {
    return ["blocked_not_proven"];
  }
  return [
    `frame_count=${packet.route_summary.frame_count}`,
    `nonzero_displacement_observed=${packet.route_summary.nonzero_displacement_observed}`,
    `displacement_m=${packet.route_summary.displacement_m}`,
    `live_motion_evidence_present=${packet.motion_log_summary.live_motion_evidence_present}`,
    `route_bag_or_live_nav2_log_present=${packet.route_bag_or_live_nav2_log.present}`,
    `route_bag_present=${packet.route_bag_or_live_nav2_log.route_bag_present}`,
    `live_motion_log_present=${packet.route_bag_or_live_nav2_log.live_motion_log_present}`,
  ];
}

function consumerFieldMotionEvidencePacketSources(): string[] {
  const packet = consumerFieldMotionEvidencePacket.value;
  if (!packet) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${packet.source_contract}`,
    `source_origin=${packet.source_origin}`,
    `proof_scope=${packet.proof_scope}`,
    `motion_log_sources=${packet.motion_log_summary.evidence_sources.join(",") || "none"}`,
    `route_bag_or_live_nav2_log_source=${packet.route_bag_or_live_nav2_log.source}`,
  ];
}

function consumerFieldMotionEvidencePacketFalseFields(): string[] {
  const packet = consumerFieldMotionEvidencePacket.value;
  if (!packet) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
    ];
  }
  return [
    `safe_to_control=${packet.safe_to_control}`,
    `delivery_success=${packet.delivery_success}`,
    `primary_actions_enabled=${packet.primary_actions_enabled}`,
    `robot_control_executed=${packet.robot_control_executed}`,
  ];
}

function consumerNav2GoalExecutionEvidenceSummary(): string {
  const evidence = consumerNav2GoalExecutionEvidence.value;
  // Nav2 goal 摘要只说明 O6 回读到的 goal/result 证据，不把 result 解读成真实送达。
  if (!evidence) {
    return "nav2_goal_execution_evidence=blocked_not_proven";
  }
  return [
    `nav2_goal_execution_evidence`,
    `status=${evidence.status}`,
    `task_id=${evidence.task_id}`,
    `goal_requested=${evidence.goal_requested}`,
    `goal_sent=${evidence.goal_sent}`,
    `goal_accepted=${evidence.goal_accepted}`,
    `result_received=${evidence.result_received}`,
    `goal_result_status=${evidence.goal_result_status}`,
    `result_status_code=${evidence.result_status_code ?? "null"}`,
  ].join(" · ");
}

function consumerNav2GoalExecutionEvidenceGoalResult(): string[] {
  const evidence = consumerNav2GoalExecutionEvidence.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${evidence.source_contract}`,
    `source_origin=${evidence.source_origin}`,
    `proof_scope=${evidence.proof_scope}`,
    `source_proof_status=${evidence.source_proof_status}`,
    `evidence_source=${evidence.evidence_source}`,
    `nav2_goal_execution_proven=${evidence.nav2_goal_execution_proven}`,
  ];
}

function consumerNav2GoalExecutionEvidenceBaseSummary(): string[] {
  const evidence = consumerNav2GoalExecutionEvidence.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `requested_base_command_mode=${evidence.requested_base_command_mode}`,
    `base_command_mode=${evidence.base_command_mode}`,
    `base_motion_command_nonzero_proven=${evidence.base_motion_command_nonzero_proven}`,
    `pose_progress_summary=${evidence.pose_progress_summary}`,
    `base_feedback_summary=${evidence.base_feedback_summary}`,
    `base_command_summary=${evidence.base_command_summary}`,
  ];
}

function consumerNav2GoalExecutionEvidenceFalseFields(): string[] {
  const evidence = consumerNav2GoalExecutionEvidence.value;
  if (!evidence) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "media_access_proven=false",
    ];
  }
  return [
    `safe_to_control=${evidence.safe_to_control}`,
    `delivery_success=${evidence.delivery_success}`,
    `primary_actions_enabled=${evidence.primary_actions_enabled}`,
    `robot_control_executed=${evidence.robot_control_executed}`,
    `connects_cloud_production=${evidence.connects_cloud_production}`,
    `media_access_proven=${evidence.media_access_proven}`,
    `real_oss_connected=${evidence.real_oss_connected}`,
    `real_cdn_connected=${evidence.real_cdn_connected}`,
  ];
}

function consumerDeliveryResultEvidenceSummary(): string {
  const evidence = consumerDeliveryResultEvidence.value;
  // delivery result 摘要只说明同 task 的送达记录/人工确认 readiness，不把 claim 解释成真实成功。
  if (!evidence) {
    return "delivery_result_evidence=blocked_not_proven";
  }
  return [
    `delivery_result_evidence`,
    `status=${evidence.status}`,
    `task_id=${evidence.task_id}`,
    `record_present=${evidence.record_present}`,
    `record_read_ok=${evidence.record_read_ok}`,
    `record_status=${evidence.record_status}`,
    `delivery_result_claimed=${evidence.delivery_result_claimed}`,
    `operator_confirmation_present=${evidence.operator_confirmation_present}`,
  ].join(" · ");
}

function consumerDeliveryResultEvidenceDetails(): string[] {
  const evidence = consumerDeliveryResultEvidence.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${evidence.source_contract}`,
    `source_origin=${evidence.source_origin}`,
    `proof_scope=${evidence.proof_scope}`,
    `record_source=${evidence.record_source}`,
    `source_schema=${evidence.source_schema}`,
    `task_id_source=${evidence.task_id_source}`,
    `linked_nav2_goal_execution_proven=${evidence.linked_nav2_goal_execution_proven}`,
  ];
}

function consumerDeliveryResultEvidenceOperatorSummary(): string[] {
  const evidence = consumerDeliveryResultEvidence.value;
  if (!evidence) {
    return ["blocked_not_proven"];
  }
  return [
    `dropoff_confirmation_type=${evidence.dropoff_confirmation_type}`,
    `completed_at_utc=${evidence.completed_at_utc}`,
    `source_proof_status=${evidence.source_proof_status}`,
    `evidence_source=${evidence.evidence_source}`,
  ];
}

function consumerDeliveryResultEvidenceFalseFields(): string[] {
  const evidence = consumerDeliveryResultEvidence.value;
  if (!evidence) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "media_access_proven=false",
    ];
  }
  return [
    `safe_to_control=${evidence.safe_to_control}`,
    `delivery_success=${evidence.delivery_success}`,
    `primary_actions_enabled=${evidence.primary_actions_enabled}`,
    `robot_control_executed=${evidence.robot_control_executed}`,
    `connects_cloud_production=${evidence.connects_cloud_production}`,
    `media_access_proven=${evidence.media_access_proven}`,
    `real_oss_connected=${evidence.real_oss_connected}`,
    `real_cdn_connected=${evidence.real_cdn_connected}`,
  ];
}

function consumerRouteExecutionResultDeliveryReadinessSummary(): string {
  const readiness = consumerRouteExecutionResultDeliveryReadiness.value;
  // 统一结果链摘要只说明 O6 已有哪一级 readiness，不把 ready 外推成真实 delivery 成功。
  if (!readiness) {
    return "route_execution_result_delivery_readiness=blocked_not_proven";
  }
  return [
    `route_execution_result_delivery_readiness`,
    `status=${readiness.status}`,
    `task_id=${readiness.task_id}`,
    `route_execution_result_status=${readiness.route_execution_result_status}`,
    `delivery_result_readiness_status=${readiness.delivery_result_readiness_status}`,
    `operator_confirmation_readiness_status=${readiness.operator_confirmation_readiness_status}`,
  ].join(" · ");
}

function consumerRouteExecutionResultDeliveryReadinessSources(): string[] {
  const readiness = consumerRouteExecutionResultDeliveryReadiness.value;
  if (!readiness) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${readiness.source_contract}`,
    `source_origin=${readiness.source_origin}`,
    `proof_scope=${readiness.proof_scope}`,
    `source_proof_status=${readiness.source_proof_status}`,
    `route_execution_source=${readiness.route_execution_source}`,
    `delivery_result_source=${readiness.delivery_result_source}`,
    `operator_confirmation_source=${readiness.operator_confirmation_source}`,
  ];
}

function consumerRouteExecutionResultDeliveryReadinessBooleans(): string[] {
  const readiness = consumerRouteExecutionResultDeliveryReadiness.value;
  if (!readiness) {
    return [
      "nav2_goal_execution_ready=false",
      "delivery_result_ready=false",
      "operator_confirmation_ready=false",
    ];
  }
  return [
    `nav2_goal_execution_ready=${readiness.nav2_goal_execution_ready}`,
    `delivery_result_ready=${readiness.delivery_result_ready}`,
    `operator_confirmation_ready=${readiness.operator_confirmation_ready}`,
  ];
}

function consumerRouteExecutionResultDeliveryReadinessFalseFields(): string[] {
  const readiness = consumerRouteExecutionResultDeliveryReadiness.value;
  if (!readiness) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "media_access_proven=false",
    ];
  }
  return [
    `safe_to_control=${readiness.safe_to_control}`,
    `delivery_success=${readiness.delivery_success}`,
    `primary_actions_enabled=${readiness.primary_actions_enabled}`,
    `robot_control_executed=${readiness.robot_control_executed}`,
    `connects_cloud_production=${readiness.connects_cloud_production}`,
    `media_access_proven=${readiness.media_access_proven}`,
    `real_oss_connected=${readiness.real_oss_connected}`,
    `real_cdn_connected=${readiness.real_cdn_connected}`,
  ];
}

function consumerRouteDeliveryClosurePacketSummary(): string {
  const packet = consumerRouteDeliveryClosurePacket.value;
  // 闭合包摘要只说明软件证据闭合情况，不把 ready 外推成真实送达成功。
  if (!packet) {
    return "route_delivery_closure_packet=blocked_not_proven";
  }
  return [
    `route_delivery_closure_packet`,
    `status=${packet.status}`,
    `task_id=${packet.task_id}`,
    `closure_status=${packet.closure_status}`,
  ].join(" · ");
}

function consumerRouteDeliveryClosurePacketSources(): string[] {
  const packet = consumerRouteDeliveryClosurePacket.value;
  if (!packet) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${packet.source_contract}`,
    `source_origin=${packet.source_origin}`,
    `proof_scope=${packet.proof_scope}`,
    `source_proof_status=${packet.source_proof_status}`,
  ];
}

function consumerRouteDeliveryClosurePacketFlags(): string[] {
  const packet = consumerRouteDeliveryClosurePacket.value;
  if (!packet) {
    return [
      "nav2_goal_execution_ready=false",
      "delivery_result_ready=false",
      "operator_confirmation_ready=false",
      "route_pose_progress_ready=false",
      "route_execution_readiness_ready=false",
    ];
  }
  return [
    `nav2_goal_execution_ready=${packet.linked_evidence_flags.nav2_goal_execution_ready}`,
    `delivery_result_ready=${packet.linked_evidence_flags.delivery_result_ready}`,
    `operator_confirmation_ready=${packet.linked_evidence_flags.operator_confirmation_ready}`,
    `route_pose_progress_ready=${packet.linked_evidence_flags.route_pose_progress_ready}`,
    `route_execution_readiness_ready=${packet.linked_evidence_flags.route_execution_readiness_ready}`,
  ];
}

function consumerRouteDeliveryClosurePacketFalseFields(): string[] {
  const packet = consumerRouteDeliveryClosurePacket.value;
  if (!packet) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "media_access_proven=false",
    ];
  }
  return [
    `safe_to_control=${packet.safe_to_control}`,
    `delivery_success=${packet.delivery_success}`,
    `primary_actions_enabled=${packet.primary_actions_enabled}`,
    `robot_control_executed=${packet.robot_control_executed}`,
    `connects_cloud_production=${packet.connects_cloud_production}`,
    `media_access_proven=${packet.media_access_proven}`,
    `real_oss_connected=${packet.real_oss_connected}`,
    `real_cdn_connected=${packet.real_cdn_connected}`,
  ];
}

function consumerSameTaskFieldMaterialPacketSummary(): string {
  const packet = consumerSameTaskFieldMaterialPacket.value;
  // field material packet 只展示 same-task 材料消费摘要，不把 ready 外推成真实送达成功。
  if (!packet) {
    return "same_task_field_material_packet=blocked_not_proven";
  }
  return [
    "same_task_field_material_packet",
    `status=${packet.status}`,
    `task_id=${packet.task_id}`,
    `packet_status=${packet.packet_status}`,
    `present_materials=${packet.present_materials.join(",") || "none"}`,
  ].join(" · ");
}

function consumerSameTaskFieldMaterialPacketSources(): string[] {
  const packet = consumerSameTaskFieldMaterialPacket.value;
  if (!packet) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${packet.source_contract}`,
    `source_origin=${packet.source_origin}`,
    `proof_scope=${packet.proof_scope}`,
    `source_proof_status=${packet.source_proof_status}`,
    `task_id_source=${packet.task_id_source}`,
  ];
}

function consumerSameTaskFieldMaterialPacketFlags(): string[] {
  const packet = consumerSameTaskFieldMaterialPacket.value;
  if (!packet) {
    return [
      "same_task_id_consumed=false",
      "live_or_field_material_consumed=false",
      "route_csv_present=false",
      "keyframes_present=false",
      "route_bag_or_rosbag_present=false",
      "replay_jsonl_present=false",
      "map_yaml_present=false",
    ];
  }
  return [
    `same_task_id_consumed=${packet.same_task_id_consumed}`,
    `live_or_field_material_consumed=${packet.live_or_field_material_consumed}`,
    `route_csv_present=${packet.route_csv_present}`,
    `keyframes_present=${packet.keyframes_present}`,
    `route_bag_or_rosbag_present=${packet.route_bag_or_rosbag_present}`,
    `replay_jsonl_present=${packet.replay_jsonl_present}`,
    `map_yaml_present=${packet.map_yaml_present}`,
  ];
}

function consumerSameTaskFieldMaterialPacketSamples(): string[] {
  const packet = consumerSameTaskFieldMaterialPacket.value;
  if (!packet) {
    return ["sample_refs=none", "missing_materials=none", "material_summaries=none"];
  }
  const materialSummaryLines = Object.entries(packet.material_summaries ?? {}).flatMap(([key, summary]) => {
    // per-material 摘要只展示 basename/hash/count/sample refs，方便对照 O6 readback 实际 shape。
    if (!summary) {
      return [];
    }
    return [
      `material:${key}.present=${summary.present}`,
      `material:${key}.basename=${summary.basename}`,
      `material:${key}.size_bytes=${summary.size_bytes ?? "not_loaded"}`,
      `material:${key}.sha256_prefix=${summary.sha256_prefix}`,
      `material:${key}.count=${summary.count ?? "not_loaded"}`,
      `material:${key}.sample_refs=${summary.sample_refs.join(",") || "none"}`,
    ];
  });
  return [
    `sample_refs=${packet.sample_refs.join(",") || "none"}`,
    `missing_materials=${packet.missing_materials.join(",") || "none"}`,
    `optional_map_gap=${packet.map_yaml_present ? "false" : "true"}`,
    ...materialSummaryLines,
  ];
}

function consumerSameTaskFieldMaterialPacketFalseFields(): string[] {
  const packet = consumerSameTaskFieldMaterialPacket.value;
  if (!packet) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "media_access_proven=false",
    ];
  }
  return [
    `safe_to_control=${packet.safe_to_control}`,
    `delivery_success=${packet.delivery_success}`,
    `primary_actions_enabled=${packet.primary_actions_enabled}`,
    `robot_control_executed=${packet.robot_control_executed}`,
    `connects_cloud_production=${packet.connects_cloud_production}`,
    `media_access_proven=${packet.media_access_proven}`,
    `real_oss_connected=${packet.real_oss_connected}`,
    `real_cdn_connected=${packet.real_cdn_connected}`,
  ];
}

function consumerCurrentFieldEvidenceMaterialSummary(): string {
  const current = consumerCurrentFieldEvidenceMaterial.value;
  // current field evidence 只显示当前现场材料，不把 support-only/blocked 摘要误读成路线执行成功。
  if (!current) {
    return "current_field_evidence_material=blocked_not_proven";
  }
  return [
    "current_field_evidence_material",
    `status=${current.status}`,
    `task_id=${current.task_id}`,
    `material_status=${current.material_status}`,
    `present_materials=${current.present_materials.join(",") || "none"}`,
    `missing_materials=${current.missing_materials.join(",") || "none"}`,
  ].join(" · ");
}

function consumerCurrentFieldEvidenceMaterialSources(): string[] {
  const current = consumerCurrentFieldEvidenceMaterial.value;
  if (!current) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${current.source_contract}`,
    `source_origin=${current.source_origin}`,
    `proof_scope=${current.proof_scope}`,
    `source_proof_status=${current.source_proof_status}`,
    `task_id_source=${current.task_id_source}`,
  ];
}

function consumerCurrentFieldEvidenceMaterialBooleans(): string[] {
  const current = consumerCurrentFieldEvidenceMaterial.value;
  if (!current) {
    return [
      "camera_frame_observed=false",
      "radar_scan_observed=false",
      "map_material_observed=false",
      "nav2_no_motion_path_generated=false",
      "manual_gate_blocked_expected=false",
      "same_task_id_consumed=false",
      "live_or_field_material_consumed=false",
    ];
  }
  return [
    `camera_frame_observed=${current.camera_frame_observed}`,
    `radar_scan_observed=${current.radar_scan_observed}`,
    `map_material_observed=${current.map_material_observed}`,
    `nav2_no_motion_path_generated=${current.nav2_no_motion_path_generated}`,
    `manual_gate_blocked_expected=${current.manual_gate_blocked_expected}`,
    `same_task_id_consumed=${current.same_task_id_consumed}`,
    `live_or_field_material_consumed=${current.live_or_field_material_consumed}`,
  ];
}

function consumerCurrentFieldEvidenceMaterialMaterials(): string[] {
  const current = consumerCurrentFieldEvidenceMaterial.value;
  if (!current) {
    return ["present_materials=none", "missing_materials=none"];
  }
  return [
    `present_materials=${current.present_materials.join(",") || "none"}`,
    `missing_materials=${current.missing_materials.join(",") || "none"}`,
  ];
}

function consumerCurrentFieldEvidenceMaterialBlockedReasons(): string[] {
  const current = consumerCurrentFieldEvidenceMaterial.value;
  if (!current) {
    return ["blocked_not_proven"];
  }
  return current.blocked_reasons.length ? current.blocked_reasons : ["blocked_not_proven"];
}

function consumerCurrentFieldEvidenceMaterialNextEvidence(): string[] {
  const current = consumerCurrentFieldEvidenceMaterial.value;
  if (!current) {
    return ["blocked_not_proven"];
  }
  return current.next_required_evidence.length ? current.next_required_evidence : ["blocked_not_proven"];
}

function consumerCurrentFieldEvidenceMaterialFalseFields(): string[] {
  const current = consumerCurrentFieldEvidenceMaterial.value;
  if (!current) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "hil_pass=false",
    ];
  }
  return [
    `safe_to_control=${current.safe_to_control}`,
    `delivery_success=${current.delivery_success}`,
    `primary_actions_enabled=${current.primary_actions_enabled}`,
    `robot_control_executed=${current.robot_control_executed}`,
    `connects_cloud_production=${current.connects_cloud_production}`,
    `hil_pass=${current.hil_pass}`,
    `real_oss_connected=${current.real_oss_connected}`,
    `real_cdn_connected=${current.real_cdn_connected}`,
  ];
}

function consumerLocalizationPathMaterialReadbackSummary(): string {
  const material = consumerLocalizationPathMaterialReadback.value;
  // localization/path readback 只说明 same-run 定位/路径材料状态，不能把 cross-run comparator 当成当前路径成功。
  if (!material) {
    return "localization_path_material_readback=blocked_not_proven";
  }
  return [
    "localization_path_material_readback",
    `status=${material.status}`,
    `task_id=${material.task_id}`,
    `material_status=${material.material_status}`,
    `same_run_path_point_count=${material.same_run_path_point_count}`,
    `cross_run_clean_baseline_path_comparator_present=${material.cross_run_clean_baseline_path_comparator_present}`,
  ].join(" · ");
}

function consumerLocalizationPathMaterialReadbackSources(): string[] {
  const material = consumerLocalizationPathMaterialReadback.value;
  if (!material) {
    return ["blocked_not_proven"];
  }
  return [
    `source_schema=${material.source_schema}`,
    `source_origin=${material.source_origin}`,
    `source_path=${material.source_path}`,
    `proof_scope=${material.proof_scope}`,
    `source_proof_status=${material.source_proof_status}`,
    `task_id_source=${material.task_id_source}`,
  ];
}

function consumerLocalizationPathMaterialReadbackSameRunFlags(): string[] {
  const material = consumerLocalizationPathMaterialReadback.value;
  if (!material) {
    return [
      "localization_path_material_bridge_present=false",
      "same_run_localization_material_present=false",
      "same_run_map_once_observed=false",
      "same_run_amcl_pose_observed=false",
      "same_run_planner_server_active=false",
      "same_run_path_generation_requested=false",
    ];
  }
  return [
    `localization_path_material_bridge_present=${material.localization_path_material_bridge_present}`,
    `same_run_localization_material_present=${material.same_run_localization_material_present}`,
    `same_run_map_once_observed=${material.same_run_map_once_observed}`,
    `same_run_amcl_pose_observed=${material.same_run_amcl_pose_observed}`,
    `same_run_planner_server_active=${material.same_run_planner_server_active}`,
    `same_run_path_generation_requested=${material.same_run_path_generation_requested}`,
  ];
}

function consumerLocalizationPathMaterialReadbackTfAndPathFlags(): string[] {
  const material = consumerLocalizationPathMaterialReadback.value;
  if (!material) {
    return [
      "same_run_localization_tf_map_to_odom=false",
      "same_run_localization_tf_map_to_base_link=false",
      "same_run_path_generation_succeeded=false",
      "same_run_path_generated=false",
      "same_run_path_point_count=0",
      "same_run_path_proven=false",
    ];
  }
  return [
    `same_run_localization_tf_map_to_odom=${material.same_run_localization_tf_map_to_odom}`,
    `same_run_localization_tf_map_to_base_link=${material.same_run_localization_tf_map_to_base_link}`,
    `same_run_path_generation_succeeded=${material.same_run_path_generation_succeeded}`,
    `same_run_path_generated=${material.same_run_path_generated}`,
    `same_run_path_point_count=${material.same_run_path_point_count}`,
    `same_run_path_proven=${material.same_run_path_proven}`,
  ];
}

function consumerLocalizationPathMaterialReadbackCrossRunComparator(): string[] {
  const material = consumerLocalizationPathMaterialReadback.value;
  const comparator = material?.cross_run_clean_baseline_path_summary ?? null;
  if (!material || !comparator) {
    return [
      `cross_run_clean_baseline_path_comparator_present=${material?.cross_run_clean_baseline_path_comparator_present ?? false}`,
      "cross_run_clean_baseline_path_summary.status=not_loaded",
      "cross_run_clean_baseline_path_summary.path_generation_succeeded=false",
      "cross_run_clean_baseline_path_summary.path_generated=false",
      "cross_run_clean_baseline_path_summary.path_point_count=0",
      "cross_run_clean_baseline_path_summary.same_run_override_allowed=false",
    ];
  }
  return [
    `cross_run_clean_baseline_path_comparator_present=${material.cross_run_clean_baseline_path_comparator_present}`,
    `cross_run_clean_baseline_path_summary.status=${comparator.status}`,
    `cross_run_clean_baseline_path_summary.path_generation_succeeded=${comparator.path_generation_succeeded}`,
    `cross_run_clean_baseline_path_summary.path_generated=${comparator.path_generated}`,
    `cross_run_clean_baseline_path_summary.path_point_count=${comparator.path_point_count}`,
    `cross_run_clean_baseline_path_summary.same_run_override_allowed=${comparator.same_run_override_allowed}`,
  ];
}

function consumerLocalizationPathMaterialReadbackFalseFields(): string[] {
  const material = consumerLocalizationPathMaterialReadback.value;
  if (!material) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "hil_pass=false",
      "nav2_route_execution_success=false",
    ];
  }
  return [
    `safe_to_control=${material.safe_to_control}`,
    `delivery_success=${material.delivery_success}`,
    `primary_actions_enabled=${material.primary_actions_enabled}`,
    `robot_control_executed=${material.robot_control_executed}`,
    `connects_cloud_production=${material.connects_cloud_production}`,
    `hil_pass=${material.hil_pass}`,
    `nav2_route_execution_success=${material.nav2_route_execution_success}`,
  ];
}

function consumerCleanBaselineNav2PathMaterialSummary(): string {
  const material = consumerCleanBaselineNav2PathMaterial.value;
  // clean baseline 材料只说明 no-motion 路径前置证据，不把 retry success 解释成真实路线执行。
  if (!material) {
    return "clean_baseline_nav2_path_material=blocked_not_proven";
  }
  return [
    "clean_baseline_nav2_path_material",
    `status=${material.status}`,
    `task_id=${material.task_id}`,
    `material_status=${material.material_status}`,
    `first_attempt_status=${material.first_attempt_status}`,
    `retry_status=${material.retry_status}`,
    `path_point_count=${material.path_point_count}`,
  ].join(" · ");
}

function consumerCleanBaselineNav2PathMaterialSources(): string[] {
  const material = consumerCleanBaselineNav2PathMaterial.value;
  if (!material) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${material.source_contract}`,
    `source_origin=${material.source_origin}`,
    `proof_scope=${material.proof_scope}`,
    `source_proof_status=${material.source_proof_status}`,
    `task_id_source=${material.task_id_source}`,
  ];
}

function consumerCleanBaselineNav2PathMaterialStatusFlags(): string[] {
  const material = consumerCleanBaselineNav2PathMaterial.value;
  if (!material) {
    return [
      "path_generation_succeeded=false",
      "path_generated=false",
      "planner_server_active=false",
      "managed_runtime_started=false",
      "managed_runtime_cleanup_ok=false",
      "cleanup_readback_clean=false",
    ];
  }
  return [
    `path_generation_succeeded=${material.path_generation_succeeded}`,
    `path_generated=${material.path_generated}`,
    `planner_server_active=${material.planner_server_active}`,
    `managed_runtime_started=${material.managed_runtime_started}`,
    `managed_runtime_cleanup_ok=${material.managed_runtime_cleanup_ok}`,
    `cleanup_readback_clean=${material.cleanup_readback_clean}`,
  ];
}

function consumerCleanBaselineNav2PathMaterialAttemptSummary(): string[] {
  const material = consumerCleanBaselineNav2PathMaterial.value;
  if (!material) {
    return [
      "first_failure_reason=blocked_not_proven",
      "first_failure_root_cause=blocked_not_proven",
      "initialpose_published=false",
      "amcl_pose_observed=false",
      "map_server_active=false",
      "amcl_active=false",
    ];
  }
  return [
    `first_failure_reason=${material.first_failure_reason}`,
    `first_failure_root_cause=${material.first_failure_root_cause}`,
    `initialpose_published=${material.initialpose_published}`,
    `amcl_pose_observed=${material.amcl_pose_observed}`,
    `map_server_active=${material.map_server_active}`,
    `amcl_active=${material.amcl_active}`,
  ];
}

function consumerCleanBaselineNav2PathMaterialBlockedReasons(): string[] {
  const material = consumerCleanBaselineNav2PathMaterial.value;
  if (!material) {
    return ["blocked_not_proven"];
  }
  return material.blocked_reasons.length ? material.blocked_reasons : ["blocked_not_proven"];
}

function consumerCleanBaselineNav2PathMaterialNextEvidence(): string[] {
  const material = consumerCleanBaselineNav2PathMaterial.value;
  if (!material) {
    return ["blocked_not_proven"];
  }
  return material.next_required_evidence.length ? material.next_required_evidence : ["blocked_not_proven"];
}

function consumerCleanBaselineNav2PathMaterialFalseFields(): string[] {
  const material = consumerCleanBaselineNav2PathMaterial.value;
  if (!material) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "hil_pass=false",
    ];
  }
  return [
    `safe_to_control=${material.safe_to_control}`,
    `delivery_success=${material.delivery_success}`,
    `primary_actions_enabled=${material.primary_actions_enabled}`,
    `robot_control_executed=${material.robot_control_executed}`,
    `connects_cloud_production=${material.connects_cloud_production}`,
    `hil_pass=${material.hil_pass}`,
  ];
}

function consumerFieldOperatorConfirmationMaterialSummary(): string {
  const material = consumerFieldOperatorConfirmationMaterial.value;
  // operator material 只读展示人工材料状态，不把 report/confirmation 推断为送达或控制成功。
  if (!material) {
    return "field_operator_confirmation_material=blocked_not_proven";
  }
  return [
    "field_operator_confirmation_material",
    `status=${material.status}`,
    `task_id=${material.task_id}`,
    `material_status=${material.material_status}`,
    `operator_report_present=${material.operator_report_present}`,
    `operator_confirmation_present=${material.operator_confirmation_present}`,
  ].join(" · ");
}

function consumerFieldOperatorConfirmationMaterialSources(): string[] {
  const material = consumerFieldOperatorConfirmationMaterial.value;
  if (!material) {
    return ["blocked_not_proven"];
  }
  return [
    `source_schema=${material.source_schema}`,
    `source_origin=${material.source_origin}`,
    `source_path=${material.source_path}`,
    `proof_scope=${material.proof_scope}`,
    `source_proof_status=${material.source_proof_status}`,
  ];
}

function consumerFieldOperatorConfirmationMaterialStatuses(): string[] {
  const material = consumerFieldOperatorConfirmationMaterial.value;
  if (!material) {
    return [
      "operator_report_status=blocked_not_proven",
      "operator_confirmation_status=blocked_not_proven",
      "reported_at=not_loaded",
      "support_only_reason=field_operator_confirmation_material_missing_or_blocked",
    ];
  }
  return [
    `operator_report_status=${material.operator_report_status}`,
    `operator_confirmation_status=${material.operator_confirmation_status}`,
    `reported_at=${material.reported_at}`,
    `support_only_reason=${material.support_only_reason}`,
  ];
}

function consumerFieldOperatorConfirmationMaterialBooleans(): string[] {
  const material = consumerFieldOperatorConfirmationMaterial.value;
  if (!material) {
    return [
      "operator_present=false",
      "physical_clearance_confirmed=false",
      "emergency_stop_ready=false",
      "observed_motion=false",
      "observed_stop=false",
      "same_task_id_consumed=false",
      "operator_material_consumed=false",
      "linked_route_material_present=false",
      "linked_delivery_material_present=false",
    ];
  }
  return [
    `operator_present=${material.operator_present}`,
    `physical_clearance_confirmed=${material.physical_clearance_confirmed}`,
    `emergency_stop_ready=${material.emergency_stop_ready}`,
    `observed_motion=${material.observed_motion}`,
    `observed_stop=${material.observed_stop}`,
    `same_task_id_consumed=${material.same_task_id_consumed}`,
    `operator_material_consumed=${material.operator_material_consumed}`,
    `linked_route_material_present=${material.linked_route_material_present}`,
    `linked_delivery_material_present=${material.linked_delivery_material_present}`,
  ];
}

function consumerFieldOperatorConfirmationMaterialSummaries(): string[] {
  const material = consumerFieldOperatorConfirmationMaterial.value;
  if (!material) {
    return ["material_summaries=none"];
  }
  const rows = Object.entries(material.material_summaries ?? {}).flatMap(([key, summary]) => {
    // material_summaries 已由 adapter 白名单化；这里只拼接短字段供 DOM smoke 覆盖。
    if (!summary) {
      return [];
    }
    return [
      `material:${key}.present=${summary.present}`,
      `material:${key}.status=${summary.status}`,
      `material:${key}.reported_at=${summary.reported_at}`,
      `material:${key}.count=${summary.count ?? "not_loaded"}`,
      `material:${key}.sample_refs=${summary.sample_refs.join(",") || "none"}`,
    ];
  });
  return rows.length ? rows : ["material_summaries=none"];
}

function consumerFieldOperatorConfirmationMaterialFalseFields(): string[] {
  const material = consumerFieldOperatorConfirmationMaterial.value;
  if (!material) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "route_execution_success=false",
      "hil_pass=false",
    ];
  }
  return [
    `safe_to_control=${material.safe_to_control}`,
    `delivery_success=${material.delivery_success}`,
    `primary_actions_enabled=${material.primary_actions_enabled}`,
    `robot_control_executed=${material.robot_control_executed}`,
    `connects_cloud_production=${material.connects_cloud_production}`,
    `route_execution_success=${material.route_execution_success}`,
    `hil_pass=${material.hil_pass}`,
  ];
}

function consumerSameTaskRouteExecutionMaterialPacketSummary(): string {
  const packet = consumerSameTaskRouteExecutionMaterialPacket.value;
  // route execution material packet 必须独立展示 O6 顶层 status，不能只靠 checklist 引用。
  if (!packet) {
    return "same_task_route_execution_material_packet=blocked_not_proven";
  }
  return [
    "same_task_route_execution_material_packet",
    `status=${packet.status}`,
    `task_id=${packet.task_id}`,
    `packet_status=${packet.packet_status}`,
    `same_task_field_material_packet_status=${packet.same_task_field_material_packet_status}`,
    `present_materials=${packet.present_materials.join(",") || "none"}`,
  ].join(" · ");
}

function consumerSameTaskRouteExecutionMaterialPacketSources(): string[] {
  const packet = consumerSameTaskRouteExecutionMaterialPacket.value;
  if (!packet) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${packet.source_contract}`,
    `source_origin=${packet.source_origin}`,
    `proof_scope=${packet.proof_scope}`,
    `source_proof_status=${packet.source_proof_status}`,
    `task_id_source=${packet.task_id_source}`,
    `source_sections=${packet.source_sections.join(",") || "none"}`,
  ];
}

function consumerSameTaskRouteExecutionMaterialPacketFlags(): string[] {
  const packet = consumerSameTaskRouteExecutionMaterialPacket.value;
  if (!packet) {
    return [
      "same_task_id_consumed=false",
      "route_execution_material_consumed=false",
      "live_or_field_command_evidence_present=false",
      "delivery_or_operator_material_consumed=false",
      "route_execution_credit_candidate=false",
      "route_execution_materials_connected=false",
      "live_nav2_route_execution_connected=false",
      "delivery_success_proven=false",
    ];
  }
  return [
    `same_task_id_consumed=${packet.same_task_id_consumed}`,
    `route_execution_material_consumed=${packet.route_execution_material_consumed}`,
    `live_or_field_command_evidence_present=${packet.live_or_field_command_evidence_present}`,
    `delivery_or_operator_material_consumed=${packet.delivery_or_operator_material_consumed}`,
    `route_execution_credit_candidate=${packet.route_execution_credit_candidate}`,
    `route_execution_materials_connected=${packet.proof_boundary.route_execution_materials_connected}`,
    `live_nav2_route_execution_connected=${packet.proof_boundary.live_nav2_route_execution_connected}`,
    `delivery_success_proven=${packet.proof_boundary.delivery_success_proven}`,
  ];
}

function consumerSameTaskRouteExecutionMaterialPacketCreditSummary(): string[] {
  const packet = consumerSameTaskRouteExecutionMaterialPacket.value;
  // credit 摘要只说明是否具备可计分材料，不把 candidate 解释成真实送达或可控。
  if (!packet) {
    return [
      "credit_support_only_reason=blocked_not_proven",
      "credit_required_evidence=same_task_route_execution_material_packet_for_selected_task",
    ];
  }
  return [
    `credit_support_only_reason=${packet.credit_support_only_reason}`,
    `credit_required_evidence=${packet.credit_required_evidence.join(",") || "none"}`,
  ];
}

function consumerSameTaskRouteExecutionMaterialPacketSamples(): string[] {
  const packet = consumerSameTaskRouteExecutionMaterialPacket.value;
  if (!packet) {
    return ["sample_refs=none", "missing_materials=none", "material_summaries=none"];
  }
  const materialSummaryLines = Object.entries(packet.material_summaries ?? {}).flatMap(([key, summary]) => {
    // 每个材料摘要只展示 basename/hash/count/sample refs，避免把 raw route/result payload 暴露到 UI。
    if (!summary) {
      return [];
    }
    return [
      `material:${key}.present=${summary.present}`,
      `material:${key}.status=${summary.status}`,
      `material:${key}.basename=${summary.basename}`,
      `material:${key}.size_bytes=${summary.size_bytes ?? "not_loaded"}`,
      `material:${key}.sha256_prefix=${summary.sha256_prefix}`,
      `material:${key}.count=${summary.count ?? "not_loaded"}`,
      `material:${key}.sample_refs=${summary.sample_refs.join(",") || "none"}`,
    ];
  });
  return [
    `sample_refs=${packet.sample_refs.join(",") || "none"}`,
    `missing_materials=${packet.missing_materials.join(",") || "none"}`,
    ...materialSummaryLines,
  ];
}

function consumerSameTaskRouteExecutionMaterialPacketRouteSummary(): string[] {
  const packet = consumerSameTaskRouteExecutionMaterialPacket.value;
  if (!packet) {
    return [
      "route_execution_result_status=blocked_not_proven",
      "pose_progress_replay_status=blocked_not_proven",
    ];
  }
  const routeSummary = packet.route_execution_result_summary;
  const poseSummary = packet.pose_progress_replay_timeline_summary;
  return [
    `route_execution_result_status=${routeSummary.status}`,
    `route_execution_result_source=${routeSummary.source}`,
    `route_execution_result_count=${routeSummary.result_count ?? "not_loaded"}`,
    `route_execution_result_sample_refs=${routeSummary.sample_refs.join(",") || "none"}`,
    `nav2_goal_status=${routeSummary.nav2_goal_status}`,
    `delivery_result_status=${routeSummary.delivery_result_status}`,
    `pose_progress_replay_status=${poseSummary.status}`,
    `pose_progress_source=${poseSummary.source}`,
    `pose_sample_count=${poseSummary.pose_sample_count ?? "not_loaded"}`,
    `replay_frame_count=${poseSummary.replay_frame_count ?? "not_loaded"}`,
    `nonzero_pose_progress_observed=${poseSummary.nonzero_pose_progress_observed}`,
    `displacement_m=${poseSummary.displacement_m ?? "not_loaded"}`,
    `timeline_span_ms=${poseSummary.timeline_span_ms ?? "not_loaded"}`,
    `pose_progress_sample_refs=${poseSummary.sample_refs.join(",") || "none"}`,
  ];
}

function consumerSameTaskRouteExecutionMaterialPacketFalseFields(): string[] {
  const packet = consumerSameTaskRouteExecutionMaterialPacket.value;
  if (!packet) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "media_access_proven=false",
    ];
  }
  return [
    `safe_to_control=${packet.safe_to_control}`,
    `delivery_success=${packet.delivery_success}`,
    `primary_actions_enabled=${packet.primary_actions_enabled}`,
    `robot_control_executed=${packet.robot_control_executed}`,
    `connects_cloud_production=${packet.connects_cloud_production}`,
    `media_access_proven=${packet.media_access_proven}`,
    `real_oss_connected=${packet.real_oss_connected}`,
    `real_cdn_connected=${packet.real_cdn_connected}`,
  ];
}

function consumerSameTaskMissionEvidenceGateSummary(): string {
  const gate = consumerSameTaskMissionEvidenceGate.value;
  // gate ready 仅表示同 task_id 证据配对可读，不表示真实送达成功或 production cloud 已接通。
  if (!gate) {
    return "same_task_mission_evidence_gate=blocked_not_proven";
  }
  return [
    `same_task_mission_evidence_gate`,
    `status=${gate.status}`,
    `task_id=${gate.task_id}`,
    `gate_status=${gate.gate_status}`,
    `mission_artifact_delta=${gate.mission_artifact_delta}`,
    `okr_credit_allowed=${gate.okr_credit_allowed}`,
  ].join(" · ");
}

function consumerSameTaskMissionEvidenceGateSources(): string[] {
  const gate = consumerSameTaskMissionEvidenceGate.value;
  if (!gate) {
    return ["blocked_not_proven"];
  }
  return [
    `source_contract=${gate.source_contract}`,
    `source_origin=${gate.source_origin}`,
    `proof_scope=${gate.proof_scope}`,
    `source_proof_status=${gate.source_proof_status}`,
    `terminal_result_source=${gate.terminal_result_source}`,
    `terminal_result_ref=${gate.terminal_result_ref}`,
    `terminal_source_schema=${gate.terminal_source_schema}`,
    `terminal_result_status=${gate.terminal_result_status}`,
    `route_execution_materials_status=${gate.route_execution_materials_status}`,
    `support_only_reason=${gate.support_only_reason}`,
  ];
}

function consumerSameTaskMissionEvidenceGateFlags(): string[] {
  const gate = consumerSameTaskMissionEvidenceGate.value;
  if (!gate) {
    return [
      "same_task_id=false",
      "terminal_result_ready=false",
      "cloud_terminal_source_ready=false",
      "route_execution_readiness_ready=false",
      "route_delivery_closure_ready=false",
      "route_pose_progress_ready=false",
    ];
  }
  return [
    `same_task_id=${gate.linked_evidence_flags.same_task_id}`,
    `same_task_id_consumed=${gate.same_task_id_consumed}`,
    `terminal_result_ready=${gate.linked_evidence_flags.terminal_result_ready}`,
    `cloud_terminal_source_ready=${gate.linked_evidence_flags.cloud_terminal_source_ready}`,
    `route_execution_readiness_ready=${gate.linked_evidence_flags.route_execution_readiness_ready}`,
    `route_delivery_closure_ready=${gate.linked_evidence_flags.route_delivery_closure_ready}`,
    `route_pose_progress_ready=${gate.linked_evidence_flags.route_pose_progress_ready}`,
    `live_or_field_command_executed=${gate.live_or_field_command_executed}`,
  ];
}

function consumerSameTaskMissionEvidenceGateFalseFields(): string[] {
  const gate = consumerSameTaskMissionEvidenceGate.value;
  if (!gate) {
    return [
      "safe_to_control=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
      "media_access_proven=false",
      "delivery_success_proven=false",
    ];
  }
  return [
    `safe_to_control=${gate.safe_to_control}`,
    `delivery_success=${gate.delivery_success}`,
    `primary_actions_enabled=${gate.primary_actions_enabled}`,
    `robot_control_executed=${gate.robot_control_executed}`,
    `connects_cloud_production=${gate.connects_cloud_production}`,
    `media_access_proven=${gate.media_access_proven}`,
    `delivery_success_proven=${gate.proof_boundary.delivery_success_proven}`,
    `real_production_cloud_connected=${gate.proof_boundary.real_production_cloud_connected}`,
    `real_oss_connected=${gate.real_oss_connected}`,
    `real_cdn_connected=${gate.real_cdn_connected}`,
  ];
}

function consumerSameTaskMissionMaterialChecklistSummary(): string {
  const checklist = consumerSameTaskMissionMaterialChecklist.value;
  // checklist 是 operator 补材料视图，不把 materials_ready 解释成真实送达或控制准入。
  if (!checklist) {
    return "same_task_mission_material_checklist=blocked_not_proven";
  }
  return [
    "same_task_mission_material_checklist",
    `status=${checklist.status}`,
    `overall_status=${checklist.overall_status}`,
    `task_id=${checklist.task_id}`,
    `source_gate_status=${checklist.source_gate_status}`,
    `okr_credit_allowed=${checklist.okr_credit_allowed}`,
    `items=${checklist.items.length}`,
  ].join(" · ");
}

function consumerSameTaskMissionMaterialChecklistGateFields(): string[] {
  const checklist = consumerSameTaskMissionMaterialChecklist.value;
  if (!checklist) {
    return [
      "okr_credit_allowed=false",
      "support_only_reason=blocked_not_proven",
      "same_task_id_consumed=false",
      "live_or_field_command_executed=false",
    ];
  }
  return [
    `okr_credit_allowed=${checklist.okr_credit_allowed}`,
    `support_only_reason=${checklist.support_only_reason}`,
    `same_task_id_consumed=${checklist.same_task_id_consumed}`,
    `live_or_field_command_executed=${checklist.live_or_field_command_executed}`,
  ];
}

function consumerSameTaskMissionMaterialChecklistFalseFields(): string[] {
  const checklist = consumerSameTaskMissionMaterialChecklist.value;
  if (!checklist) {
    return [
      "delivery_success=false",
      "safe_to_control=false",
      "primary_actions_enabled=false",
      "robot_control_executed=false",
      "connects_cloud_production=false",
    ];
  }
  return [
    `delivery_success=${checklist.delivery_success}`,
    `safe_to_control=${checklist.safe_to_control}`,
    `primary_actions_enabled=${checklist.primary_actions_enabled}`,
    `robot_control_executed=${checklist.robot_control_executed}`,
    `connects_cloud_production=${checklist.connects_cloud_production}`,
  ];
}

function consumerSameTaskMissionMaterialChecklistItemRows(): string[] {
  const checklist = consumerSameTaskMissionMaterialChecklist.value;
  // item 行只拼接后端安全摘要，方便 DOM smoke 覆盖 operator 可执行材料清单。
  if (!checklist?.items.length) {
    return ["blocked_not_proven"];
  }
  return checklist.items.map((item) =>
    [
      `id=${item.id}`,
      `label=${item.label}`,
      `material_status=${item.material_status}`,
      `owner_hint=${item.owner_hint}`,
      `source_summary=${item.source_summary}`,
      `next_required_evidence=${item.next_required_evidence.join("|") || "none"}`,
      `blocked_reasons=${item.blocked_reasons.join("|") || "none"}`,
    ].join(" · "),
  );
}

function consumerArtifactAccessProbeCounts(): string[] {
  const probe = consumerArtifactAccessProbe.value;
  if (!probe) {
    return ["blocked_not_proven"];
  }
  return [
    `requested_ref_count=${probe.counts.requested_ref_count}`,
    `readable_ref_count=${probe.counts.readable_ref_count}`,
    `blocked_ref_count=${probe.counts.blocked_ref_count}`,
    `missing_ref_count=${probe.counts.missing_ref_count}`,
    `sample_refs=${probe.sample_refs.join(",") || "none"}`,
    `sha256_prefixes=${probe.sample_sha256_prefixes.join(",") || "none"}`,
  ];
}

function consumerArtifactAccessProbeSampleRows(): string[] {
  const probe = consumerArtifactAccessProbe.value;
  if (!probe?.sample_probes.length) {
    return ["blocked_not_proven"];
  }
  return probe.sample_probes.map((sample, index) =>
    [
      `${index + 1}.`,
      `ref_kind=${sample.ref_kind}`,
      `ref=${sample.ref}`,
      `exists=${String(sample.exists)}`,
      `size_bytes=${sample.size_bytes ?? "null"}`,
      `detected_type=${sample.detected_type}`,
      `sha256=${sample.sha256_prefix || "none"}`,
      `blocked_reason=${sample.blocked_reason}`,
    ].join(" · "),
  );
}

function consumerArtifactAccessProbeFalseFields(): string[] {
  const probe = consumerArtifactAccessProbe.value;
  // 这些 false 字段直接对应 O6/O7 proof boundary，避免 access probe 被误读成真实 OSS/CDN 可读。
  return [
    `allowlist_root_echoed=${String(probe?.allowlist_root_echoed ?? false)}`,
    `file_read_attempted=${String(probe?.proof_boundary.file_read_attempted ?? false)}`,
    `media_access_proven=${String(probe?.media_access_proven ?? false)}`,
    `real_oss_connected=${String(probe?.real_oss_connected ?? false)}`,
    `real_cdn_connected=${String(probe?.real_cdn_connected ?? false)}`,
    `robot_control_executed=${String(probe?.robot_control_executed ?? false)}`,
    `safe_to_control=${String(probe?.safe_to_control ?? false)}`,
    `delivery_success=${String(probe?.delivery_success ?? false)}`,
    `primary_actions_enabled=${String(probe?.primary_actions_enabled ?? false)}`,
  ];
}

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
  // 本地 manifest 只作为 field_evidence 缺口补齐输入，详情其余部分仍来自 O6 远端响应。
  consumerTaskDetailLoading.value = true;
  consumerTaskDetailError.value = "";
  consumerAnnotationSubmitResult.value = null;
  consumerAnnotationSubmitError.value = "";
  consumerAnnotationExportResult.value = null;
  consumerAnnotationExportError.value = "";
  try {
    consumerTaskDetailResult.value = await getO7ConsumerTaskDetail(
      consumerReadBaseUrl.value,
      consumerSelectedTaskId.value,
      consumerFieldEvidenceManifestJson.value,
    );
    resetRouteReplayCursor();
  } catch (error) {
    consumerTaskDetailError.value = error instanceof Error ? error.message : "consumer_task_detail_not_available";
  } finally {
    consumerTaskDetailLoading.value = false;
  }
}

async function submitConsumerAnnotation(): Promise<void> {
  // submit 按钮只调用 PC 后端 adapter；失败也要展示 fail-closed receipt，而不是吞掉错误。
  if (consumerAnnotationActionBlockedReason.value) {
    consumerAnnotationSubmitError.value = consumerAnnotationActionBlockedReason.value;
    return;
  }
  const taskId = consumerTaskDetailResult.value?.task_summary?.task_id ?? consumerSelectedTaskId.value;
  const robotId = consumerTaskDetailResult.value?.task_summary?.robot_id ?? "";
  consumerAnnotationSubmitLoading.value = true;
  consumerAnnotationSubmitError.value = "";
  try {
    consumerAnnotationSubmitResult.value = await postO7ConsumerAnnotationSubmit(
      consumerReadBaseUrl.value,
      taskId,
      robotId,
      buildConsumerAnnotationSubmitLabels(),
    );
  } catch (error) {
    consumerAnnotationSubmitError.value = error instanceof Error ? error.message : "consumer_annotation_submit_not_available";
  } finally {
    consumerAnnotationSubmitLoading.value = false;
  }
}

async function exportConsumerAnnotationDataset(): Promise<void> {
  // export 是 task-level local/mock JSONL 摘要，不触发真实训练集生产或云端下载。
  if (consumerAnnotationActionBlockedReason.value) {
    consumerAnnotationExportError.value = consumerAnnotationActionBlockedReason.value;
    return;
  }
  const taskId = consumerTaskDetailResult.value?.task_summary?.task_id ?? consumerSelectedTaskId.value;
  consumerAnnotationExportLoading.value = true;
  consumerAnnotationExportError.value = "";
  try {
    consumerAnnotationExportResult.value = await getO7ConsumerAnnotationExport(consumerReadBaseUrl.value, taskId);
  } catch (error) {
    consumerAnnotationExportError.value = error instanceof Error ? error.message : "consumer_annotation_export_not_available";
  } finally {
    consumerAnnotationExportLoading.value = false;
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
  consumerAnnotationSubmitResult.value = null;
  consumerAnnotationSubmitError.value = "";
  consumerAnnotationExportResult.value = null;
  consumerAnnotationExportError.value = "";
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
            <dt>manifest gate</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.manifest_gate.status ?? "blocked_not_proven" }}</dd>
            <dt>artifact_status</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.manifest.artifact_status ?? "blocked" }}</dd>
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
            <dt>primary_actions_enabled</dt>
            <dd>{{ fieldEvidenceConsumerIngestResult?.primary_actions_enabled ?? false }}</dd>
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
      <label class="single-input">
        <span>Local field evidence manifest JSON</span>
        <input
          v-model="consumerFieldEvidenceManifestJson"
          aria-label="O7 consumer local field evidence manifest JSON"
          placeholder="pc-tools/evidence/fixtures/field_evidence_manifest.json"
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
                <th>origin</th>
                <th>field evidence</th>
                <th>labels</th>
                <th>inference</th>
                <th>tunnel</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!consumerTaskListResult?.task_list.length">
                <td colspan="7">blocked_not_proven</td>
              </tr>
              <tr
                v-for="task in consumerTaskListResult?.task_list ?? []"
                :key="task.task_id"
                @click="consumerSelectedTaskId = task.task_id"
              >
                <td>{{ task.task_id }}</td>
                <td>{{ task.task_status_summary }}</td>
                <td>{{ task.task_origin }}</td>
                <td>{{ task.field_evidence_source }} / {{ task.field_evidence_artifact_status }}</td>
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
            <dd>{{ consumerTaskDetailResult?.query_strategy.include.join(",") ?? "trajectory,events,evidence,field_evidence,labeling,inference,tunnel,artifact_access_probe,offline_artifact_seed_smoke,route_root_seed_gate,route_bag_evidence,route_bag_payload_replay,route_bag_semantic_replay,route_bag_full_semantic_decode_matrix,route_bag_pose_progress_replay,nav2_goal_execution_evidence,delivery_result_evidence,route_execution_result_delivery_readiness,route_delivery_closure_packet,same_task_field_material_packet,current_field_evidence_material,clean_baseline_nav2_path_material,localization_path_material_readback,same_task_route_execution_material_packet,same_task_mission_evidence_gate" }}</dd>
            <dt>fail-closed visible</dt>
            <dd>{{ consumerTaskDetailResult?.query_strategy.fail_closed_visible ?? true }}</dd>
            <dt>field evidence contract</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.source_contract ?? "not_loaded" }}</dd>
            <dt>field evidence origin</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.source_origin ?? "not_loaded" }}</dd>
            <dt>task origin</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.task_origin ?? "not_loaded" }}</dd>
            <dt>field evidence input</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.input_status ?? "missing" }}</dd>
            <dt>local manifest query</dt>
            <dd><code>{{ consumerFieldEvidenceManifestJson || "not_provided" }}</code></dd>
            <dt>manifest_gate</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.manifest_gate.status ?? "blocked_not_proven" }}</dd>
            <dt>artifact_status</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.artifact_status ?? "blocked" }}</dd>
            <dt>safe_to_control</dt>
            <dd>{{ consumerTaskDetailResult?.safe_to_control ?? false }}</dd>
            <dt>delivery_success</dt>
            <dd>{{ consumerTaskDetailResult?.delivery_success ?? false }}</dd>
            <dt>primary_actions_enabled</dt>
            <dd>{{ consumerTaskDetailResult?.primary_actions_enabled ?? false }}</dd>
            <dt>connects_cloud_production</dt>
            <dd>{{ consumerTaskDetailResult?.connects_cloud_production ?? false }}</dd>
            <dt>robot_control_executed</dt>
            <dd>{{ consumerTaskDetailResult?.robot_control_executed ?? false }}</dd>
          </dl>
          <h3>Field evidence boundary</h3>
          <dl class="kv compact-kv">
            <dt>blocked_reason</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.blocked_reason ?? "not_loaded" }}</dd>
            <dt>not_proven</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.not_proven ?? true }}</dd>
            <dt>manifest source</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.manifest_gate.source ?? "not_loaded" }}</dd>
            <dt>manifest run</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.manifest_run_id ?? "not_loaded" }}</dd>
            <dt>artifact root</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.artifact_root || "not_loaded" }}</dd>
            <dt>artifact health</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.artifact_health_summary ?? "not_loaded" }}</dd>
            <dt>manifest gate_pass</dt>
            <dd>{{ consumerTaskDetailResult?.field_evidence.manifest_gate.gate_pass ?? false }}</dd>
          </dl>
          <h3>Field evidence artifacts</h3>
          <ul class="dense">
            <li>present={{ consumerTaskDetailResult?.field_evidence.present_artifacts?.join(",") || "none" }}</li>
            <li>missing={{ consumerTaskDetailResult?.field_evidence.missing_artifacts?.join(",") || "none" }}</li>
          </ul>
          <h3>Artifact bundle readiness</h3>
          <div class="notice" role="note">
            artifact_bundle_readiness 主路径 · bundle / consumer_ingest / preflight 优先 · route_bag_evidence / route_bag_payload_replay / route_bag_semantic_replay / route_bag_full_semantic_decode_matrix / route_delivery_closure_packet / same_task_field_material_packet / same_task_route_execution_material_packet / same_task_mission_evidence_gate / field_operator_confirmation_material 只读汇总 · route replay / labeling 旧 fallback 只做兼容
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerArtifactBundleReadiness?.schema ?? "trashbot.pc_tools_workstation.o7_consumer_artifact_bundle_readiness.v1" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerArtifactBundleReadiness?.status ?? "blocked_not_proven" }}</dd>
            <dt>source_contract</dt>
            <dd>{{ consumerArtifactBundleReadiness?.source_contract ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerArtifactBundleReadiness?.source_origin ?? "not_loaded" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerArtifactBundleReadiness?.task_id ?? "not_loaded" }}</dd>
            <dt>route_ref_count</dt>
            <dd>{{ consumerArtifactBundleReadiness?.counts.route_ref_count ?? 0 }}</dd>
            <dt>replay_ref_count</dt>
            <dd>{{ consumerArtifactBundleReadiness?.counts.replay_ref_count ?? 0 }}</dd>
            <dt>keyframe_ref_count</dt>
            <dd>{{ consumerArtifactBundleReadiness?.counts.keyframe_ref_count ?? 0 }}</dd>
            <dt>evidence_ref_count</dt>
            <dd>{{ consumerArtifactBundleReadiness?.counts.evidence_ref_count ?? 0 }}</dd>
            <dt>review_item_count</dt>
            <dd>{{ consumerArtifactBundleReadiness?.counts.review_item_count ?? 0 }}</dd>
            <dt>sample_ref_count</dt>
            <dd>{{ consumerArtifactBundleReadiness?.counts.sample_ref_count ?? 0 }}</dd>
            <dt>review_item_media_ref_count</dt>
            <dd>{{ consumerArtifactBundleReadiness?.counts.review_item_media_ref_count ?? 0 }}</dd>
          </dl>
          <h4>Readiness summary</h4>
          <ul class="dense">
            <li>{{ consumerArtifactBundleReadinessSummary() }}</li>
            <li v-for="line in consumerArtifactBundleReadinessCounts()" :key="line">{{ line }}</li>
          </ul>
          <h4>Bundle source</h4>
          <dl class="kv compact-kv">
            <dt>artifact bundle schema</dt>
            <dd>{{ consumerArtifactBundle?.schema ?? "not_loaded" }}</dd>
            <dt>artifact bundle source</dt>
            <dd>{{ consumerArtifactBundle?.source ?? "not_loaded" }}</dd>
            <dt>artifact bundle status</dt>
            <dd>{{ consumerArtifactBundle?.bundle_status ?? "blocked_not_proven" }}</dd>
            <dt>artifact bundle ingest schema</dt>
            <dd>{{ consumerArtifactBundleConsumerIngest?.schema ?? "not_loaded" }}</dd>
            <dt>artifact bundle ingest status</dt>
            <dd>{{ consumerArtifactBundleConsumerIngest?.status ?? "blocked_not_proven" }}</dd>
          </dl>
          <h4>Bundle refs</h4>
          <ul class="dense">
            <li v-for="line in consumerArtifactBundleReadinessRefs()" :key="line">{{ line }}</li>
          </ul>
          <h4>Offline artifact seed smoke</h4>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerOfflineArtifactSeedSmoke?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerOfflineArtifactSeedSmoke?.status ?? "blocked_not_proven" }}</dd>
            <dt>source_contract</dt>
            <dd>{{ consumerOfflineArtifactSeedSmoke?.source_contract ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerOfflineArtifactSeedSmoke?.source_origin ?? "not_loaded" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerOfflineArtifactSeedSmoke?.task_id ?? "not_loaded" }}</dd>
          </dl>
          <h5>Seed smoke summary</h5>
          <ul class="dense">
            <li>{{ consumerOfflineArtifactSeedSmokeSummary() }}</li>
            <li v-for="line in consumerOfflineArtifactSeedSmokeCounts()" :key="line">{{ line }}</li>
          </ul>
          <h5>Seed smoke refs</h5>
          <ul class="dense">
            <li v-for="line in consumerOfflineArtifactSeedSmokeRefs()" :key="line">{{ line }}</li>
          </ul>
          <h5>Seed smoke blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerOfflineArtifactSeedSmokeBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Seed smoke next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerOfflineArtifactSeedSmokeNextEvidence()" :key="item">{{ item }}</li>
          </ul>
          <h4>Route-root seed gate</h4>
          <div class="notice" role="note">
            route_root_seed_gate · consumes trashbot.o6.route_root_seed_gate.v1 only · route_bag_required=false ·
            route_bag_present=false · basename refs only · safe_to_control=false · delivery_success=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerRouteRootSeedGate?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerRouteRootSeedGate?.status ?? "blocked_not_proven" }}</dd>
            <dt>route_root_seed_status</dt>
            <dd>{{ consumerRouteRootSeedGate?.route_root_seed_status ?? "blocked_not_proven" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerRouteRootSeedGate?.source_origin ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerRouteRootSeedGate?.proof_scope ?? "not_loaded" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerRouteRootSeedGate?.task_id ?? "not_loaded" }}</dd>
            <dt>route_bag_required</dt>
            <dd>{{ consumerRouteRootSeedGate?.route_bag_required ?? false }}</dd>
            <dt>route_bag_present</dt>
            <dd>{{ consumerRouteRootSeedGate?.route_bag_present ?? false }}</dd>
          </dl>
          <h5>Route-root summary</h5>
          <ul class="dense">
            <li>{{ consumerRouteRootSeedGateSummary() }}</li>
            <li v-for="line in consumerRouteRootSeedGateCounts()" :key="line">{{ line }}</li>
          </ul>
          <h5>Route-root refs</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteRootSeedGateRefs()" :key="line">{{ line }}</li>
          </ul>
          <h5>Route-root blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerRouteRootSeedGate?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Route-root next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerRouteRootSeedGate?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Route-root false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteRootSeedGateFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Route bag evidence</h4>
          <div class="notice" role="note">
            route_bag_evidence 同 task_id 只读摘要 · DB3 topic/message/timestamp summary only · raw payload/path/base64 hidden ·
            safe_to_control=false · delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerRouteBagEvidence?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerRouteBagEvidence?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerRouteBagEvidence?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerRouteBagEvidence?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerRouteBagEvidence?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Route bag summary</h5>
          <ul class="dense">
            <li>{{ consumerRouteBagEvidenceSummary() }}</li>
            <li v-for="line in consumerRouteBagEvidenceCounts()" :key="line">{{ line }}</li>
          </ul>
          <h5>Route bag source</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagEvidenceSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Route bag blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerRouteBagEvidence?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Route bag next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerRouteBagEvidence?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Route bag false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagEvidenceFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Route bag payload replay</h4>
          <div class="notice" role="note">
            route_bag_payload_replay 同 task_id 只读摘要 · topic/message/timestamp + payload size/hash prefix only · raw payload/base64/content/path hidden ·
            safe_to_control=false · delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerRouteBagPayloadReplay?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerRouteBagPayloadReplay?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerRouteBagPayloadReplay?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerRouteBagPayloadReplay?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerRouteBagPayloadReplay?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Payload replay summary</h5>
          <ul class="dense">
            <li>{{ consumerRouteBagPayloadReplaySummary() }}</li>
            <li v-for="line in consumerRouteBagPayloadReplayCounts()" :key="line">{{ line }}</li>
          </ul>
          <h5>Payload replay source</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagPayloadReplaySources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Payload replay blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerRouteBagPayloadReplay?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Payload replay next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerRouteBagPayloadReplay?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Payload replay false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagPayloadReplayFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Route bag semantic replay</h4>
          <div class="notice" role="note">
            route_bag_semantic_replay 同 task_id 只读摘要 · decode status + LaserScan/Image/TF/Odometry summary only · raw payload/base64/content/path/token hidden ·
            safe_to_control=false · delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerRouteBagSemanticReplay?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerRouteBagSemanticReplay?.status ?? "blocked_not_proven" }}</dd>
            <dt>semantic_decode_status</dt>
            <dd>{{ consumerRouteBagSemanticReplay?.semantic_decode_status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerRouteBagSemanticReplay?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerRouteBagSemanticReplay?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerRouteBagSemanticReplay?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Semantic replay summary</h5>
          <ul class="dense">
            <li>{{ consumerRouteBagSemanticReplaySummary() }}</li>
            <li v-for="line in consumerRouteBagSemanticReplayCounts()" :key="line">{{ line }}</li>
          </ul>
          <h5>Semantic decode summaries</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagSemanticReplayDecodeSummaries()" :key="line">{{ line }}</li>
          </ul>
          <h5>Semantic replay source</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagSemanticReplaySources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Semantic replay blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerRouteBagSemanticReplay?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Semantic replay next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerRouteBagSemanticReplay?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Semantic replay false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagSemanticReplayFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Route bag full semantic decode matrix</h4>
          <div class="notice" role="note">
            route_bag_full_semantic_decode_matrix 同 task_id 只读摘要 · decoded/unsupported/failed coverage matrix only · raw payload/base64/content/path/token hidden ·
            ready_not_route_execution_proof 只表示离线语义覆盖可读 · safe_to_control=false · delivery_success=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerRouteBagFullSemanticDecodeMatrix?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerRouteBagFullSemanticDecodeMatrix?.status ?? "blocked_not_proven" }}</dd>
            <dt>semantic_decode_matrix_status</dt>
            <dd>{{ consumerRouteBagFullSemanticDecodeMatrix?.semantic_decode_matrix_status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerRouteBagFullSemanticDecodeMatrix?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerRouteBagFullSemanticDecodeMatrix?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerRouteBagFullSemanticDecodeMatrix?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Full semantic matrix summary</h5>
          <ul class="dense">
            <li>{{ consumerRouteBagFullSemanticDecodeMatrixSummary() }}</li>
            <li v-for="line in consumerRouteBagFullSemanticDecodeMatrixCounts()" :key="line">{{ line }}</li>
          </ul>
          <h5>Full semantic matrix sample topic types</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagFullSemanticDecodeMatrixSamples()" :key="line">{{ line }}</li>
          </ul>
          <h5>Full semantic matrix source</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagFullSemanticDecodeMatrixSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Full semantic matrix blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerRouteBagFullSemanticDecodeMatrix?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Full semantic matrix next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerRouteBagFullSemanticDecodeMatrix?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Full semantic matrix false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagFullSemanticDecodeMatrixFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Route bag pose progress replay</h4>
          <div class="notice" role="note">
            route_bag_pose_progress_replay 同 task_id 只读摘要 · sample/decode counts + topic types + frame pairs + start/end pose + displacement only ·
            raw payload/base64/content/path/token hidden · safe_to_control=false · delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerRouteBagPoseProgressReplay?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerRouteBagPoseProgressReplay?.status ?? "blocked_not_proven" }}</dd>
            <dt>pose_decode_status</dt>
            <dd>{{ consumerRouteBagPoseProgressReplay?.pose_decode_status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerRouteBagPoseProgressReplay?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerRouteBagPoseProgressReplay?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerRouteBagPoseProgressReplay?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Pose progress summary</h5>
          <ul class="dense">
            <li>{{ consumerRouteBagPoseProgressReplaySummary() }}</li>
            <li v-for="line in consumerRouteBagPoseProgressReplayCounts()" :key="line">{{ line }}</li>
          </ul>
          <h5>Pose endpoints</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagPoseProgressReplayPoseSummaries()" :key="line">{{ line }}</li>
          </ul>
          <h5>Pose progress source</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagPoseProgressReplaySources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Pose progress blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerRouteBagPoseProgressReplay?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Pose progress next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerRouteBagPoseProgressReplay?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Pose progress false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteBagPoseProgressReplayFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Field motion evidence packet</h4>
          <div class="notice" role="note">
            field_motion_evidence_packet 同 task_id 摘要 · route frame count / motion log sources / route_bag live log gap only ·
            safe_to_control=false · delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerFieldMotionEvidencePacket?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerFieldMotionEvidencePacket?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerFieldMotionEvidencePacket?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerFieldMotionEvidencePacket?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerFieldMotionEvidencePacket?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Field motion summary</h5>
          <ul class="dense">
            <li>{{ consumerFieldMotionEvidencePacketSummary() }}</li>
            <li v-for="line in consumerFieldMotionEvidencePacketCounts()" :key="line">{{ line }}</li>
          </ul>
          <h5>Field motion sources</h5>
          <ul class="dense">
            <li v-for="line in consumerFieldMotionEvidencePacketSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Field motion blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerFieldMotionEvidencePacket?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Field motion next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerFieldMotionEvidencePacket?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Field motion false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerFieldMotionEvidencePacketFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Nav2 goal execution evidence</h4>
          <div class="notice" role="note">
            Nav2 goal evidence 同 task_id 只读摘要 · goal/result/base command readiness · safe_to_control=false ·
            delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerNav2GoalExecutionEvidence?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerNav2GoalExecutionEvidence?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerNav2GoalExecutionEvidence?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerNav2GoalExecutionEvidence?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerNav2GoalExecutionEvidence?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Nav2 goal summary</h5>
          <ul class="dense">
            <li>{{ consumerNav2GoalExecutionEvidenceSummary() }}</li>
            <li v-for="line in consumerNav2GoalExecutionEvidenceGoalResult()" :key="line">{{ line }}</li>
          </ul>
          <h5>Nav2 base summary</h5>
          <ul class="dense">
            <li v-for="line in consumerNav2GoalExecutionEvidenceBaseSummary()" :key="line">{{ line }}</li>
          </ul>
          <h5>Nav2 blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerNav2GoalExecutionEvidence?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Nav2 next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerNav2GoalExecutionEvidence?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Nav2 false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerNav2GoalExecutionEvidenceFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Delivery result evidence</h4>
          <div class="notice" role="note">
            delivery result evidence 同 task_id 只读摘要 · record/operator confirmation readiness only · safe_to_control=false ·
            delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerDeliveryResultEvidence?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerDeliveryResultEvidence?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerDeliveryResultEvidence?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerDeliveryResultEvidence?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerDeliveryResultEvidence?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Delivery result summary</h5>
          <ul class="dense">
            <li>{{ consumerDeliveryResultEvidenceSummary() }}</li>
            <li v-for="line in consumerDeliveryResultEvidenceDetails()" :key="line">{{ line }}</li>
          </ul>
          <h5>Delivery operator summary</h5>
          <ul class="dense">
            <li v-for="line in consumerDeliveryResultEvidenceOperatorSummary()" :key="line">{{ line }}</li>
          </ul>
          <h5>Delivery blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerDeliveryResultEvidence?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Delivery next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerDeliveryResultEvidence?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Delivery false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerDeliveryResultEvidenceFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Route execution result delivery readiness</h4>
          <div class="notice" role="note">
            route execution result / delivery / operator confirmation readiness 只读摘要 · readiness only · safe_to_control=false ·
            delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerRouteExecutionResultDeliveryReadiness?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerRouteExecutionResultDeliveryReadiness?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerRouteExecutionResultDeliveryReadiness?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerRouteExecutionResultDeliveryReadiness?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerRouteExecutionResultDeliveryReadiness?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Route execution readiness summary</h5>
          <ul class="dense">
            <li>{{ consumerRouteExecutionResultDeliveryReadinessSummary() }}</li>
            <li v-for="line in consumerRouteExecutionResultDeliveryReadinessSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Linked readiness booleans</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteExecutionResultDeliveryReadinessBooleans()" :key="line">{{ line }}</li>
          </ul>
          <h5>Route execution readiness blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerRouteExecutionResultDeliveryReadiness?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Route execution readiness next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerRouteExecutionResultDeliveryReadiness?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Route execution readiness false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteExecutionResultDeliveryReadinessFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Route delivery closure packet</h4>
          <div class="notice" role="note">
            route delivery closure packet 只读摘要 · closure status + linked evidence flags only · safe_to_control=false ·
            delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerRouteDeliveryClosurePacket?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerRouteDeliveryClosurePacket?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerRouteDeliveryClosurePacket?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerRouteDeliveryClosurePacket?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerRouteDeliveryClosurePacket?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Closure packet summary</h5>
          <ul class="dense">
            <li>{{ consumerRouteDeliveryClosurePacketSummary() }}</li>
            <li v-for="line in consumerRouteDeliveryClosurePacketSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Linked evidence flags</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteDeliveryClosurePacketFlags()" :key="line">{{ line }}</li>
          </ul>
          <h5>Closure packet blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerRouteDeliveryClosurePacket?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Closure packet next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerRouteDeliveryClosurePacket?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Closure packet false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerRouteDeliveryClosurePacketFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Same task field material packet</h4>
          <div class="notice" role="note">
            same_task_field_material_packet 只读摘要 · 同 task_id 的 route/keyframe/route bag/replay 材料消费状态 ·
            map_yaml 缺失只记 optional gap，不阻断其他材料展示 · basename refs only · safe_to_control=false ·
            delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerSameTaskFieldMaterialPacket?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerSameTaskFieldMaterialPacket?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerSameTaskFieldMaterialPacket?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerSameTaskFieldMaterialPacket?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerSameTaskFieldMaterialPacket?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Field material summary</h5>
          <ul class="dense">
            <li>{{ consumerSameTaskFieldMaterialPacketSummary() }}</li>
            <li v-for="line in consumerSameTaskFieldMaterialPacketSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Field material flags</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskFieldMaterialPacketFlags()" :key="line">{{ line }}</li>
          </ul>
          <h5>Field material refs</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskFieldMaterialPacketSamples()" :key="line">{{ line }}</li>
          </ul>
          <h5>Field material blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerSameTaskFieldMaterialPacket?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Field material next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerSameTaskFieldMaterialPacket?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Field material false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskFieldMaterialPacketFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Current field evidence material</h4>
          <div class="notice" role="note">
            current_field_evidence_material 只读摘要 · current field status + present/missing materials + camera/radar/map/nav2/manual gate booleans ·
            support-only/current evidence 不等于 route execution success · safe_to_control=false · delivery_success=false · primary_actions_enabled=false ·
            robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerCurrentFieldEvidenceMaterial?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerCurrentFieldEvidenceMaterial?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerCurrentFieldEvidenceMaterial?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerCurrentFieldEvidenceMaterial?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerCurrentFieldEvidenceMaterial?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Current field summary</h5>
          <ul class="dense">
            <li>{{ consumerCurrentFieldEvidenceMaterialSummary() }}</li>
            <li v-for="line in consumerCurrentFieldEvidenceMaterialSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Current field booleans</h5>
          <ul class="dense">
            <li v-for="line in consumerCurrentFieldEvidenceMaterialBooleans()" :key="line">{{ line }}</li>
          </ul>
          <h5>Current field materials</h5>
          <ul class="dense">
            <li v-for="line in consumerCurrentFieldEvidenceMaterialMaterials()" :key="line">{{ line }}</li>
          </ul>
          <h5>Current field blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerCurrentFieldEvidenceMaterialBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Current field next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerCurrentFieldEvidenceMaterialNextEvidence()" :key="item">{{ item }}</li>
          </ul>
          <h5>Current field false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerCurrentFieldEvidenceMaterialFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Localization path material readback</h4>
          <div class="notice" role="note">
            localization_path_material_readback 只读摘要 · same-run localization/path flags + cross-run clean-baseline comparator boundary ·
            兼容 O6 旧 `_readback` ready status、旧 TF alias 和缺失 bridge alias，但页面统一按 O7 归一字段展示 ·
            comparator 只做历史对照，不能覆盖当前 same_run_path=false 结论，不等于 route execution success、delivery success 或可控 ·
            safe_to_control=false · delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerLocalizationPathMaterialReadback?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerLocalizationPathMaterialReadback?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerLocalizationPathMaterialReadback?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerLocalizationPathMaterialReadback?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerLocalizationPathMaterialReadback?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Localization path summary</h5>
          <ul class="dense">
            <li>{{ consumerLocalizationPathMaterialReadbackSummary() }}</li>
            <li v-for="line in consumerLocalizationPathMaterialReadbackSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Same-run localization flags</h5>
          <ul class="dense">
            <li v-for="line in consumerLocalizationPathMaterialReadbackSameRunFlags()" :key="line">{{ line }}</li>
          </ul>
          <h5>TF and same-run path false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerLocalizationPathMaterialReadbackTfAndPathFlags()" :key="line">{{ line }}</li>
          </ul>
          <h5>Cross-run comparator boundary</h5>
          <ul class="dense">
            <li v-for="line in consumerLocalizationPathMaterialReadbackCrossRunComparator()" :key="line">{{ line }}</li>
          </ul>
          <h5>Localization path blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerLocalizationPathMaterialReadback?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Localization path next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerLocalizationPathMaterialReadback?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Localization path false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerLocalizationPathMaterialReadbackFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Clean baseline Nav2 path material</h4>
          <div class="notice" role="note">
            clean_baseline_nav2_path_material 只读摘要 · first failure + retry success + path_point_count + cleanup readback ·
            只说明 no-motion Nav2 path preflight 材料可读，不等于 route execution success、delivery success 或可控 ·
            safe_to_control=false · delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerCleanBaselineNav2PathMaterial?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerCleanBaselineNav2PathMaterial?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerCleanBaselineNav2PathMaterial?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerCleanBaselineNav2PathMaterial?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerCleanBaselineNav2PathMaterial?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Clean baseline summary</h5>
          <ul class="dense">
            <li>{{ consumerCleanBaselineNav2PathMaterialSummary() }}</li>
            <li v-for="line in consumerCleanBaselineNav2PathMaterialSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Retry and cleanup flags</h5>
          <ul class="dense">
            <li v-for="line in consumerCleanBaselineNav2PathMaterialStatusFlags()" :key="line">{{ line }}</li>
          </ul>
          <h5>First failure and Nav2 preflight</h5>
          <ul class="dense">
            <li v-for="line in consumerCleanBaselineNav2PathMaterialAttemptSummary()" :key="line">{{ line }}</li>
          </ul>
          <h5>Clean baseline blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerCleanBaselineNav2PathMaterialBlockedReasons()" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Clean baseline next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerCleanBaselineNav2PathMaterialNextEvidence()" :key="item">{{ item }}</li>
          </ul>
          <h5>Clean baseline false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerCleanBaselineNav2PathMaterialFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Field operator confirmation material</h4>
          <div class="notice" role="note">
            field_operator_confirmation_material 只读摘要 · operator report / operator confirmation / safety preflight booleans only ·
            ready_not_delivery_proof 不等于 delivery_success、route_execution_success、HIL pass 或控制准入 · safe_to_control=false ·
            delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerFieldOperatorConfirmationMaterial?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerFieldOperatorConfirmationMaterial?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerFieldOperatorConfirmationMaterial?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerFieldOperatorConfirmationMaterial?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerFieldOperatorConfirmationMaterial?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Operator material summary</h5>
          <ul class="dense">
            <li>{{ consumerFieldOperatorConfirmationMaterialSummary() }}</li>
            <li v-for="line in consumerFieldOperatorConfirmationMaterialSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Operator report statuses</h5>
          <ul class="dense">
            <li v-for="line in consumerFieldOperatorConfirmationMaterialStatuses()" :key="line">{{ line }}</li>
          </ul>
          <h5>Operator safety and linked materials</h5>
          <ul class="dense">
            <li v-for="line in consumerFieldOperatorConfirmationMaterialBooleans()" :key="line">{{ line }}</li>
          </ul>
          <h5>Operator material summaries</h5>
          <ul class="dense">
            <li v-for="line in consumerFieldOperatorConfirmationMaterialSummaries()" :key="line">{{ line }}</li>
          </ul>
          <h5>Operator material blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerFieldOperatorConfirmationMaterial?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Operator material next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerFieldOperatorConfirmationMaterial?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Operator material false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerFieldOperatorConfirmationMaterialFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Same task route execution material packet</h4>
          <div class="notice" role="note">
            same_task_route_execution_material_packet 只读摘要 · O6 顶层 status + 同 task route execution result / pose progress / replay timeline material ·
            checklist 只能引用该 packet，不能替代 packet 自身验收；即使 route_execution_credit_candidate=true，也不等于 delivery_success=true、safe_to_control=true
            或启用任何 primary action · safe_to_control=false · delivery_success=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerSameTaskRouteExecutionMaterialPacket?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerSameTaskRouteExecutionMaterialPacket?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerSameTaskRouteExecutionMaterialPacket?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerSameTaskRouteExecutionMaterialPacket?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerSameTaskRouteExecutionMaterialPacket?.source_origin ?? "not_loaded" }}</dd>
          </dl>
          <h5>Route execution material summary</h5>
          <ul class="dense">
            <li>{{ consumerSameTaskRouteExecutionMaterialPacketSummary() }}</li>
            <li v-for="line in consumerSameTaskRouteExecutionMaterialPacketSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Same-task and material flags</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskRouteExecutionMaterialPacketFlags()" :key="line">{{ line }}</li>
          </ul>
          <h5>Credit material summary</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskRouteExecutionMaterialPacketCreditSummary()" :key="line">{{ line }}</li>
          </ul>
          <h5>Route result and pose timeline</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskRouteExecutionMaterialPacketRouteSummary()" :key="line">{{ line }}</li>
          </ul>
          <h5>Route execution material refs</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskRouteExecutionMaterialPacketSamples()" :key="line">{{ line }}</li>
          </ul>
          <h5>Route execution material blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerSameTaskRouteExecutionMaterialPacket?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Route execution material next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerSameTaskRouteExecutionMaterialPacket?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Route execution material false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskRouteExecutionMaterialPacketFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Same task mission evidence gate</h4>
          <div class="notice" role="note">
            same_task_mission_evidence_gate 只读摘要 · O5 terminal/cloud source 与 route execution materials 同 task_id 配对检查 ·
            ready_not_success_proof 不等于真实送达成功；若 okr_credit_allowed=false，当前证据只能算 support-only/blocked，不计 O5/O6/O7 主进度 · safe_to_control=false · delivery_success=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerSameTaskMissionEvidenceGate?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerSameTaskMissionEvidenceGate?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerSameTaskMissionEvidenceGate?.task_id ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerSameTaskMissionEvidenceGate?.proof_scope ?? "not_loaded" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerSameTaskMissionEvidenceGate?.source_origin ?? "not_loaded" }}</dd>
            <dt>terminal source</dt>
            <dd>{{ consumerSameTaskMissionEvidenceGate?.terminal_result_source ?? "not_loaded" }}</dd>
            <dt>terminal schema</dt>
            <dd>{{ consumerSameTaskMissionEvidenceGate?.terminal_source_schema ?? "not_loaded" }}</dd>
          </dl>
          <h5>Same task gate summary</h5>
          <ul class="dense">
            <li>{{ consumerSameTaskMissionEvidenceGateSummary() }}</li>
            <li v-for="line in consumerSameTaskMissionEvidenceGateSources()" :key="line">{{ line }}</li>
          </ul>
          <h5>Same task linked flags</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskMissionEvidenceGateFlags()" :key="line">{{ line }}</li>
          </ul>
          <h5>Same task blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerSameTaskMissionEvidenceGate?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Same task next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerSameTaskMissionEvidenceGate?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Same task false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskMissionEvidenceGateFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Same task mission material checklist</h4>
          <div class="notice" role="note">
            same_task_mission_material_checklist operator 材料清单 · 来源是 O6 same_task_mission_evidence_gate 主路径 ·
            materials_ready_not_success_proof 只表示材料可读；okr_credit_allowed=false 时必须保留 support-only/blocked 语义，不启用 submit/TTS/nav/control · delivery_success=false · safe_to_control=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerSameTaskMissionMaterialChecklist?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerSameTaskMissionMaterialChecklist?.status ?? "blocked_not_proven" }}</dd>
            <dt>overall_status</dt>
            <dd>{{ consumerSameTaskMissionMaterialChecklist?.overall_status ?? "blocked_not_proven" }}</dd>
            <dt>source_gate_schema</dt>
            <dd>{{ consumerSameTaskMissionMaterialChecklist?.source_gate_schema ?? "not_loaded" }}</dd>
            <dt>source_gate_status</dt>
            <dd>{{ consumerSameTaskMissionMaterialChecklist?.source_gate_status ?? "blocked_not_proven" }}</dd>
          </dl>
          <h5>Checklist summary</h5>
          <ul class="dense">
            <li>{{ consumerSameTaskMissionMaterialChecklistSummary() }}</li>
            <li v-for="line in consumerSameTaskMissionMaterialChecklistGateFields()" :key="line">{{ line }}</li>
          </ul>
          <h5>Checklist items</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskMissionMaterialChecklistItemRows()" :key="line">{{ line }}</li>
          </ul>
          <h5>Checklist blockers</h5>
          <ul class="dense">
            <li v-for="reason in consumerSameTaskMissionMaterialChecklist?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h5>Checklist next evidence</h5>
          <ul class="dense">
            <li v-for="item in consumerSameTaskMissionMaterialChecklist?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h5>Checklist false fields</h5>
          <ul class="dense">
            <li v-for="line in consumerSameTaskMissionMaterialChecklistFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h4>Bundle blockers</h4>
          <ul class="dense">
            <li v-for="reason in consumerArtifactBundleReadiness?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h4>Bundle next evidence</h4>
          <ul class="dense">
            <li v-for="item in consumerArtifactBundleReadiness?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h3>Artifact access probe</h3>
          <div class="notice" role="note">
            artifact_access_probe 二级消费 · basename refs / sha256 prefix only · allowlist_root_echoed=false · real_oss_connected=false · real_cdn_connected=false
          </div>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerArtifactAccessProbe?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerArtifactAccessProbe?.status ?? "blocked_not_proven" }}</dd>
            <dt>source_origin</dt>
            <dd>{{ consumerArtifactAccessProbe?.source_origin ?? "not_loaded" }}</dd>
            <dt>proof_scope</dt>
            <dd>{{ consumerArtifactAccessProbe?.proof_scope ?? "not_loaded" }}</dd>
            <dt>allowlist_root_configured</dt>
            <dd>{{ consumerArtifactAccessProbe?.allowlist_root_configured ?? false }}</dd>
            <dt>max_file_size_bytes</dt>
            <dd>{{ consumerArtifactAccessProbe?.max_file_size_bytes ?? "null" }}</dd>
          </dl>
          <h4>Access summary</h4>
          <ul class="dense">
            <li>{{ consumerArtifactAccessProbeSummary() }}</li>
            <li v-for="line in consumerArtifactAccessProbeCounts()" :key="line">{{ line }}</li>
          </ul>
          <h4>Access probe samples</h4>
          <ul class="dense">
            <li v-for="line in consumerArtifactAccessProbeSampleRows()" :key="line">{{ line }}</li>
          </ul>
          <h4>Access blockers</h4>
          <ul class="dense">
            <li v-for="reason in consumerArtifactAccessProbe?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h4>Access next evidence</h4>
          <ul class="dense">
            <li v-for="item in consumerArtifactAccessProbe?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h4>Access false fields</h4>
          <ul class="dense">
            <li v-for="line in consumerArtifactAccessProbeFalseFields()" :key="line">{{ line }}</li>
          </ul>
          <h3>Artifact/media preflight</h3>
          <dl class="kv compact-kv">
            <dt>schema</dt>
            <dd>{{ consumerArtifactMediaPreflight?.schema ?? "not_loaded" }}</dd>
            <dt>status</dt>
            <dd>{{ consumerArtifactMediaPreflight?.status ?? "blocked_not_proven" }}</dd>
            <dt>task_id</dt>
            <dd>{{ consumerArtifactMediaPreflight?.task_id ?? "blocked_not_proven" }}</dd>
            <dt>route_ref_count</dt>
            <dd>{{ consumerArtifactMediaPreflight?.counts.route_ref_count ?? 0 }}</dd>
            <dt>replay_ref_count</dt>
            <dd>{{ consumerArtifactMediaPreflight?.counts.replay_ref_count ?? 0 }}</dd>
            <dt>keyframe_ref_count</dt>
            <dd>{{ consumerArtifactMediaPreflight?.counts.keyframe_ref_count ?? 0 }}</dd>
            <dt>review_item_media_ref_count</dt>
            <dd>{{ consumerArtifactMediaPreflight?.counts.review_item_media_ref_count ?? 0 }}</dd>
            <dt>real_media_read_executed</dt>
            <dd>{{ consumerArtifactMediaPreflight?.proof_boundary.real_media_read_executed ?? false }}</dd>
            <dt>real_oss_connected</dt>
            <dd>{{ consumerArtifactMediaPreflight?.real_oss_connected ?? false }}</dd>
            <dt>real_cdn_connected</dt>
            <dd>{{ consumerArtifactMediaPreflight?.real_cdn_connected ?? false }}</dd>
          </dl>
          <ul class="dense">
            <li>consumer_sections={{ consumerArtifactMediaPreflight?.consumer_section_names?.join(",") || "none" }}</li>
            <li>blocked_reasons={{ consumerArtifactMediaPreflight?.blocked_reasons?.join(",") || "none" }}</li>
            <li>next_required_evidence={{ consumerArtifactMediaPreflight?.next_required_evidence?.join(",") || "none" }}</li>
          </ul>
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
            consumer-detail labeling primary path · artifact_bundle_readiness 优先 · local/mock submit/export via PC adapter · proof_status=not_proven ·
            submit_enabled=false for real API · dataset_export_available=false for real dataset ·
            real_annotation_api_connected=false · real_dataset_export_connected=false · connects_cloud_production=false ·
            safe_to_control=false · primary_actions_enabled=false · robot_control_executed=false
          </div>
          <div class="route-inputs">
            <button
              class="secondary"
              type="button"
              :disabled="!consumerAnnotationSubmitEnabled"
              @click="submitConsumerAnnotation"
            >
              {{ consumerAnnotationSubmitLoading ? "正在提交 local/mock 标注" : "提交 local/mock 标注" }}
            </button>
            <button
              class="secondary"
              type="button"
              :disabled="!consumerAnnotationExportEnabled"
              @click="exportConsumerAnnotationDataset"
            >
              {{ consumerAnnotationExportLoading ? "正在导出 local/mock 数据集" : "导出 local/mock 数据集" }}
            </button>
          </div>
          <div v-if="consumerAnnotationSubmitError" class="notice" role="alert">
            Local/mock annotation submit blocked: {{ consumerAnnotationSubmitError }}. not_proven=true.
          </div>
          <div v-if="consumerAnnotationExportError" class="notice" role="alert">
            Local/mock dataset export blocked: {{ consumerAnnotationExportError }}. not_proven=true.
          </div>
          <dl class="kv compact-kv">
            <dt>mvp_schema</dt>
            <dd>{{ consumerLabelingMvp?.schema ?? "trashbot.pc_tools_workstation.o7_consumer_labeling_mvp.v1" }}</dd>
            <dt>mvp_status</dt>
            <dd>{{ consumerLabelingMvp?.status ?? "blocked_not_proven" }}</dd>
            <dt>cursor_status</dt>
            <dd>{{ consumerDetailLabelingQueueNavigationEnabled ? "consumer_detail_labeling_queue_ready" : "blocked_not_proven" }}</dd>
            <dt>blocked_reason</dt>
            <dd>{{ consumerDetailLabelingQueueBlockedReason || "none_consumer_detail_only" }}</dd>
            <dt>summary</dt>
            <dd>{{ consumerDetailLabelingQueueSummary }}</dd>
            <dt>current task</dt>
            <dd>{{ consumerTaskDetailResult?.task_summary?.task_id ?? "blocked_not_proven" }}</dd>
            <dt>current review item</dt>
            <dd>{{ consumerLabelingMvpCurrentItem?.item_id ?? "blocked_not_proven" }}</dd>
            <dt>media_ref</dt>
            <dd>{{ consumerLabelingMvpCurrentItem?.media_ref ?? "blocked_not_proven" }}</dd>
            <dt>review evidence_ref</dt>
            <dd>{{ consumerLabelingMvpCurrentItem?.evidence_ref ?? "blocked_not_proven" }}</dd>
            <dt>current labels</dt>
            <dd><code>{{ jsonSummary(consumerLabelingMvpCurrentItem?.current_labels.sample ?? []) }}</code></dd>
            <dt>draft labels</dt>
            <dd><code>{{ jsonSummary(consumerLabelingMvp?.draft_labels.sample ?? []) }}</code></dd>
            <dt>label schema</dt>
            <dd><code>{{ jsonSummary(consumerLabelingMvp?.label_schema) }}</code></dd>
            <dt>allowed label types</dt>
            <dd><code>{{ jsonSummary(consumerLabelingMvp?.allowed_label_types ?? []) }}</code></dd>
            <dt>submit receipt</dt>
            <dd>{{ consumerLabelingMvp?.submit_receipt.status ?? "submit_blocked_fail_closed" }}</dd>
            <dt>submit blocked reason</dt>
            <dd>{{ consumerLabelingMvp?.submit_receipt.blocked_reason ?? "annotation_api_not_connected" }}</dd>
            <dt>media dependency status</dt>
            <dd>{{ consumerLabelingMediaDependency?.status ?? "blocked_not_proven" }}</dd>
            <dt>route_ref</dt>
            <dd>{{ consumerLabelingMediaDependency?.route_ref ?? "blocked_not_proven" }}</dd>
            <dt>replay_ref</dt>
            <dd>{{ consumerLabelingMediaDependency?.replay_ref ?? "blocked_not_proven" }}</dd>
            <dt>keyframe_ref</dt>
            <dd>{{ consumerLabelingMediaDependency?.keyframe_ref ?? "blocked_not_proven" }}</dd>
            <dt>action blocker</dt>
            <dd>{{ consumerAnnotationActionBlockedReason || "none_local_mock_only" }}</dd>
            <dt>local/mock submit schema</dt>
            <dd>{{ consumerAnnotationSubmitResult?.schema ?? "trashbot.pc_tools_workstation.o7_annotation_submit_result.v1" }}</dd>
            <dt>local/mock submit adapter status</dt>
            <dd>{{ consumerAnnotationSubmitResult?.adapter_status ?? "not_run" }}</dd>
            <dt>local/mock submit result</dt>
            <dd>{{ consumerAnnotationSubmitSummary }}</dd>
            <dt>local/mock export schema</dt>
            <dd>{{ consumerAnnotationExportResult?.schema ?? "trashbot.pc_tools_workstation.o7_annotation_dataset_export_result.v1" }}</dd>
            <dt>local/mock export adapter status</dt>
            <dd>{{ consumerAnnotationExportResult?.adapter_status ?? "not_run" }}</dd>
            <dt>local/mock export result</dt>
            <dd>{{ consumerAnnotationExportSummary }}</dd>
            <dt>local/mock export rows</dt>
            <dd><code>{{ jsonSummary(consumerAnnotationExportResult?.sample_rows ?? []) }}</code></dd>
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
            <dt>field motion summary</dt>
            <dd>{{ consumerFieldMotionEvidencePacketSummary() }}</dd>
            <dt>submit_enabled</dt>
            <dd>false</dd>
            <dt>export_enabled</dt>
            <dd>false_real_dataset_export; local_mock_button={{ consumerAnnotationExportEnabled }}</dd>
            <dt>rollback_enabled</dt>
            <dd>false</dd>
            <dt>real_annotation_api_connected</dt>
            <dd>false</dd>
            <dt>real_dataset_export_connected</dt>
            <dd>false</dd>
            <dt>cloud_write_executed</dt>
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
          <h3>Labeling dependency media refs</h3>
          <ul class="dense">
            <li v-for="refValue in consumerLabelingMediaDependency?.review_item_media_refs ?? []" :key="refValue">{{ refValue }}</li>
            <li v-if="!consumerLabelingMediaDependency?.review_item_media_refs?.length">blocked_not_proven</li>
          </ul>
          <h3>Labeling dependency blocked reasons</h3>
          <ul class="dense">
            <li v-for="reason in consumerLabelingMediaDependency?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
          </ul>
          <h3>Labeling dependency next required evidence</h3>
          <ul class="dense">
            <li v-for="item in consumerLabelingMediaDependency?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
          </ul>
          <h3>Consumer-detail labeling queue notes</h3>
          <ul class="dense">
            <li>consumer-detail labeling primary path uses task detail labels plus evidence/events/trajectory checks</li>
            <li>local/mock submit/export only calls PC backend adapter; browser never calls O6 directly</li>
            <li>real submit/export/rollback stay closed; archive fixture review panel only survives as debug fallback</li>
            <li>missing detail, labeling, evidence, events or trajectory keeps the view blocked_not_proven</li>
          </ul>

          <h3>Consumer-detail route replay player</h3>
          <div class="notice" role="note">
            artifact_bundle_readiness 优先 · local_detail_cursor_only · sends_to_robot=false · safe_to_control=false · primary_actions_enabled=false ·
            local_state_only=true · playback_available=false
          </div>
          <dl class="kv compact-kv">
            <dt>mvp_schema</dt>
            <dd>{{ consumerRouteReplayMvp?.schema ?? "trashbot.pc_tools_workstation.o7_consumer_route_replay_mvp.v1" }}</dd>
            <dt>mvp_status</dt>
            <dd>{{ consumerRouteReplayMvp?.status ?? "blocked_not_proven" }}</dd>
            <dt>cursor_status</dt>
            <dd>{{ routeReplayNavigationEnabled ? "local_consumer_detail_cursor_ready" : "blocked_not_proven" }}</dd>
            <dt>blocked_reason</dt>
            <dd>{{ routeReplayBlockedReason || "none_consumer_detail_only" }}</dd>
            <dt>trajectory frame count</dt>
            <dd>{{ consumerRouteReplayMvp?.trajectory.frame_count ?? consumerTaskDetailResult?.trajectory.frame_count ?? 0 }}</dd>
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
            <dt>playback_available</dt>
            <dd>{{ consumerRouteReplayMvp?.cursor_contract.playback_available ?? false }}</dd>
            <dt>safe_to_play</dt>
            <dd>{{ consumerRouteReplayMvp?.cursor_contract.safe_to_play ?? false }}</dd>
            <dt>media dependency status</dt>
            <dd>{{ consumerRouteReplayMediaDependency?.status ?? "blocked_not_proven" }}</dd>
            <dt>route_ref</dt>
            <dd>{{ consumerRouteReplayMediaDependency?.route_ref ?? "blocked_not_proven" }}</dd>
            <dt>replay_ref</dt>
            <dd>{{ consumerRouteReplayMediaDependency?.replay_ref ?? "blocked_not_proven" }}</dd>
            <dt>keyframe_ref</dt>
            <dd>{{ consumerRouteReplayMediaDependency?.keyframe_ref ?? "blocked_not_proven" }}</dd>
            <dt>field motion summary</dt>
            <dd>{{ consumerFieldMotionEvidencePacketSummary() }}</dd>
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
              <h4>Media dependency blocked reasons</h4>
              <ul class="dense">
                <li v-for="reason in consumerRouteReplayMediaDependency?.blocked_reasons ?? ['blocked_not_proven']" :key="reason">{{ reason }}</li>
              </ul>
            </div>
            <div>
              <h4>Labeling</h4>
              <ul class="dense">
                <li v-for="item in consumerRouteReplayLabelingSummaries" :key="item">{{ item }}</li>
                <li v-if="!consumerRouteReplayLabelingSummaries.length">blocked_not_proven</li>
              </ul>
              <h4>Keyframes</h4>
              <ul class="dense">
                <li v-for="refValue in consumerRouteReplayMvp?.evidence_refs.keyframe_refs ?? []" :key="refValue">
                  {{ refValue }}
                </li>
                <li v-if="!consumerRouteReplayMvp?.evidence_refs.keyframe_refs.length">blocked_not_proven</li>
              </ul>
              <h4>Media dependency sample refs</h4>
              <ul class="dense">
                <li v-for="refValue in consumerRouteReplayMediaDependency?.sample_refs ?? []" :key="refValue">{{ refValue }}</li>
                <li v-if="!consumerRouteReplayMediaDependency?.sample_refs?.length">blocked_not_proven</li>
              </ul>
              <h4>Media dependency next required evidence</h4>
              <ul class="dense">
                <li v-for="item in consumerRouteReplayMediaDependency?.next_required_evidence ?? ['blocked_not_proven']" :key="item">{{ item }}</li>
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
