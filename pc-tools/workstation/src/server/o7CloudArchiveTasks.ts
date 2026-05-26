import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7CloudArchiveTaskSafeSummaries,
  O7CloudArchiveTasksResponse,
  O7CloudArchiveTaskSummary,
  O7LabelingQueueInspector,
  O7LabelingQueueInspectorLabelSample,
  O7RouteReplayInspector,
  O7SafeCommandInspector,
  O7SafeCommandInspectorCommandSample,
  O7VoiceAsrTtsInspector,
  O7VoiceAsrTtsInspectorAsrEvent,
  O7VoiceAsrTtsInspectorTranscriptSlot,
} from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7CloudArchiveTasksOptions {
  archiveJson?: string;
}

const SUPPORTED_SCHEMA = "trashbot.o7.cloud_archive_fixture.v1" as const;
const TASK_LIMIT = 20;
const SAMPLE_LIMIT = 5;

const FORBIDDEN_COPY = [
  "Authorization",
  "access_key",
  "secret",
  "token",
  "password",
  "postgres://",
  "postgresql://",
  "mysql://",
  "redis://",
  "amqp://",
  "mongodb://",
  "/cmd_vel",
  "/dev/tty",
  "/dev/ttyUSB",
  "/dev/ttyACM",
  "Traceback",
];

const SUCCESS_CLAIM_PATTERNS = [
  /\bdelivery\s+(success|succeeded|completed|complete)\b/i,
  /\bdropoff\s+(success|succeeded|completed|complete)\b/i,
  /\bcloud\s+archive\s+(connected|ready|live|success)\b/i,
  /"delivery_success"\s*:\s*true/i,
];

const CONTROL_CLAIM_PATTERNS = [
  /"safe_to_control"\s*:\s*true/i,
  /"primary_actions_enabled"\s*:\s*true/i,
  /"robot_control_executed"\s*:\s*true/i,
  /"command_dispatch_enabled"\s*:\s*true/i,
  /"manual_control_enabled"\s*:\s*true/i,
  /"navigate_goal_enabled"\s*:\s*true/i,
  /"keyboard_control_enabled"\s*:\s*true/i,
];

const REAL_API_CLAIM_PATTERNS = [
  /"real_cloud_archive_connected"\s*:\s*true/i,
  /"real_realtime_api_connected"\s*:\s*true/i,
  /"real_annotation_api_connected"\s*:\s*true/i,
  /"real_voice_api_connected"\s*:\s*true/i,
  /"real_asr_tts_runtime_connected"\s*:\s*true/i,
  /"real_command_api_connected"\s*:\s*true/i,
  /"real_robot_ack_connected"\s*:\s*true/i,
  /"asr_stream_connected"\s*:\s*true/i,
  /"tts_send_enabled"\s*:\s*true/i,
  /"speaker_dispatch_enabled"\s*:\s*true/i,
];

const SENSITIVE_PATTERNS: Array<[RegExp, string]> = [
  [/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]"],
  [/\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+/gi, "$1=[REDACTED]"],
  [/\b(postgres|postgresql|mysql|redis|amqp|mongodb):\/\/[^,\s]+/gi, "[REDACTED_URL]"],
  [/\/cmd_vel\b/g, "[REDACTED_ROS_TOPIC]"],
  [/\/dev\/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*/gi, "/dev/[REDACTED_DEVICE]"],
  [/\b[A-Za-z]:\\[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/\/(Users|home|tmp|private|var|mnt|run|workspace|ws)\/[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/Traceback \(most recent call last\):[\s\S]*/gi, "[REDACTED_TRACEBACK]"],
];

// 该 adapter 是 O7 统一数据源的最小 software-proof 入口，只读取 operator 显式指定的本地 archive JSON。
// 它不连接 O6 云归档、不轮询 realtime、不提交标注、不发送 TTS、不下发手控/寻路命令。
// 响应只输出白名单摘要和 fixed false 字段，防止历史任务 fixture 被误读为真实云端已接通。

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown): string {
  // 空值统一为空字符串，避免 null/undefined 在 UI 中看起来像真实业务值。
  return value === null || value === undefined ? "" : String(value);
}

function safeText(value: unknown): string {
  // 所有可展示文本都脱敏，archive fixture 不允许泄露本机路径、凭证或控制 topic。
  return SENSITIVE_PATTERNS.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), asText(value));
}

function safeRef(value: unknown): string {
  // evidence/media 引用只保留 basename；绝对路径不会进入 API 响应。
  const raw = asText(value).trim();
  if (!raw) {
    return "";
  }
  if (path.isAbsolute(raw) || raw.includes("/") || raw.includes("\\")) {
    return `file:${path.basename(raw)}`;
  }
  return safeText(raw);
}

function safeNumber(value: unknown): number | null {
  // 只接受真实有限 number，避免把字符串里的不可信 payload 提升为业务时间戳。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function encoded(value: unknown): string {
  // 安全扫描覆盖完整 payload；异常对象退回空对象文本并走正常 fail-closed 分支。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function hasForbiddenCopy(value: unknown): boolean {
  // 命中凭证、串口、ROS 控制 topic 或 traceback 时，不生成任何任务摘要。
  const payload = encoded(value);
  return FORBIDDEN_COPY.some((token) => payload.includes(token));
}

function hasSuccessClaim(value: unknown): boolean {
  // 本地 archive fixture 不能自证云归档已接通或任务交付成功。
  const payload = encoded(value);
  return SUCCESS_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function hasControlClaim(value: unknown): boolean {
  // 任意控制开关为 true 都说明 fixture 越界，必须 fail closed。
  const payload = encoded(value);
  return CONTROL_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function hasRealApiClaim(value: unknown): boolean {
  // 真实云端、实时、标注、语音和命令 API 都不能由 fixture 自证 connected。
  const payload = encoded(value);
  return REAL_API_CLAIM_PATTERNS.some((pattern) => pattern.test(payload));
}

function fixedFalseFields(): O7CloudArchiveTasksResponse["fixed_false_fields"] {
  // fixed_false_fields 让 UI 和测试能集中复核所有危险能力都保持关闭。
  return {
    real_cloud_archive_connected: false,
    real_realtime_api_connected: false,
    real_annotation_api_connected: false,
    real_voice_api_connected: false,
    real_command_api_connected: false,
    real_robot_ack_connected: false,
    real_asr_tts_runtime_connected: false,
    command_dispatch_enabled: false,
    manual_control_enabled: false,
    navigate_goal_enabled: false,
    keyboard_control_enabled: false,
    asr_stream_connected: false,
    tts_send_enabled: false,
    speaker_dispatch_enabled: false,
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    pc_only: true,
    robot_control_executed: false,
  };
}

function defaultCommandEvidenceGaps(value: unknown): string[] {
  // KR6 gaps 必须同时保留 timeout/cancel/stop/recovery，避免 ACK 缺口被命令样本掩盖。
  const fixtureGaps = safeTextList(value, SAMPLE_LIMIT * 2);
  return Array.from(new Set([
    ...fixtureGaps,
    "real_command_api_not_connected",
    "manual_turn_dispatch_not_proven",
    "navigate_goal_dispatch_not_proven",
    "robot_ack_timeout_trace_missing",
    "cancel_ack_trace_missing",
    "stop_ack_trace_missing",
    "recovery_event_trace_missing",
    "hil_or_hardware_safety_not_proven",
  ]));
}

function emptySafeCommandInspector(
  blockedReasons: string[],
  selectedTaskId: string | null = null,
): O7SafeCommandInspector {
  // safe command inspector 失败时清空 command sample，并把所有真实控制字段保持 false。
  return {
    status: "blocked_not_proven",
    selected_task_id: selectedTaskId,
    command_session: {
      command_session_id: "not_loaded",
      source: "local_json_fixture",
      evidence_ref: "not_loaded",
      audit_refs: [],
      status: "blocked_not_proven",
    },
    command_count: 0,
    sample_commands: [],
    manual_turn_envelope: {
      sends_to_robot: false,
      requested_direction: "not_loaded",
      velocity_limited: true,
      steering_limited: true,
      evidence_ref: "missing_manual_turn_command_envelope_trace",
      status: "blocked_not_proven",
    },
    navigate_goal_envelope: {
      sends_to_robot: false,
      goal_source: "not_loaded",
      map_frame: "map",
      x_m: null,
      y_m: null,
      yaw_rad: null,
      evidence_ref: "missing_navigate_goal_command_envelope_trace",
      status: "blocked_not_proven",
    },
    velocity_limits: {
      max_linear_mps: null,
      max_angular_radps: null,
      source: "not_loaded",
      hardware_verified: false,
      status: "blocked_not_proven",
    },
    steering_limits: {
      max_steering_angle_rad: null,
      max_turn_rate_radps: null,
      source: "not_loaded",
      hardware_verified: false,
      status: "blocked_not_proven",
    },
    map_goal_slot: {
      map_frame: "map",
      x_m: null,
      y_m: null,
      yaw_rad: null,
      status: "blocked_not_proven",
      evidence_ref: "missing_map_goal_selection_trace",
    },
    idempotency_key_requirement: {
      required: true,
      key_ref: "missing_idempotency_key_requirement",
      header: "Idempotency-Key",
      status: "blocked_not_proven",
    },
    confirmation_policy: {
      manual_turn_requires_confirmation: true,
      navigate_goal_requires_confirmation: true,
      keyboard_control_requires_hold: true,
      status: "blocked_not_proven",
    },
    robot_ack_blocked_summary: {
      ack_status: "blocked_not_proven",
      last_command_id: "not_loaded",
      ack_ref: "missing_robot_command_ack",
      timeout_ms: null,
      cancel_ack_ref: "missing_robot_cancel_ack",
      stop_ack_ref: "missing_robot_stop_ack",
      recovery_ref: "missing_robot_recovery_event",
      status: "blocked_not_proven",
    },
    evidence_gaps: defaultCommandEvidenceGaps(blockedReasons),
    command_dispatch_enabled: false,
    manual_control_enabled: false,
    navigate_goal_enabled: false,
    keyboard_control_enabled: false,
    real_command_api_connected: false,
    real_robot_ack_connected: false,
    robot_control_executed: false,
    safe_to_control: false,
    primary_actions_enabled: false,
    delivery_success: false,
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_safe_command_api",
      "real_manual_turn_control",
      "real_navigate_goal_dispatch",
      "real_keyboard_control",
      "real_robot_command_ack",
      "real_timeout_cancel_stop_recovery",
      "real_hil_or_hardware_safety",
      "delivery_success",
    ],
  };
}

function voiceBlockedSlot(type: "partial" | "final", status: "empty_not_proven" | "blocked_not_proven"): O7VoiceAsrTtsInspectorTranscriptSlot {
  // ASR 槽位缺失时也返回固定 evidence_ref，避免 UI 自行补一个看似真实的 transcript。
  return {
    text: "",
    timestamp_ms: null,
    confidence: null,
    evidence_ref: type === "partial" ? "missing_asr_partial_transcript_trace" : "missing_asr_final_transcript_trace",
    status,
  };
}

function emptyVoiceAsrTtsInspector(
  blockedReasons: string[],
  selectedTaskId: string | null = null,
): O7VoiceAsrTtsInspector {
  // 语音 inspector 失败时清空样本，并固定 ASR/TTS/speaker/runtime 全部 false。
  return {
    status: "blocked_not_proven",
    selected_task_id: selectedTaskId,
    voice_session: {
      session_id: "not_loaded",
      source: "local_json_fixture",
      evidence_ref: "not_loaded",
      audit_refs: [],
      status: "blocked_not_proven",
    },
    asr_event_count: 0,
    sample_asr_events: [],
    latest_partial: voiceBlockedSlot("partial", "blocked_not_proven"),
    latest_final: voiceBlockedSlot("final", "blocked_not_proven"),
    tts_draft: {
      text: "",
      text_length: 0,
      voice_profile: "not_loaded",
      language: "not_loaded",
      confirmation_required: true,
      status: "blocked_not_proven",
    },
    speaker_dispatch: {
      sends_to_robot: false,
      speaker_dispatch_enabled: false,
      ack_status: "blocked_not_proven",
      speaker_ack_ref: "missing_speaker_dispatch_ack",
      failure_event_ref: "missing_speaker_failure_event",
      failure_refs: [],
      status: "blocked_not_proven",
    },
    media_preflight_dependency: {
      required: true,
      source_schema: "trashbot.o7_board_media_preflight.v1",
      status: "blocked",
      dependency_ref: "board_media_preflight_summary",
      gaps: blockedReasons,
    },
    asr_stream_connected: false,
    tts_send_enabled: false,
    speaker_dispatch_enabled: false,
    real_voice_api_connected: false,
    real_asr_tts_runtime_connected: false,
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_voice_api",
      "real_o7_asr_tts_runtime",
      "real_asr_stream",
      "real_asr_partial_transcript",
      "real_asr_final_transcript",
      "real_tts_send",
      "real_tts_playback",
      "real_speaker_dispatch_ack",
      "real_audio_device",
    ],
  };
}

function emptyRouteReplayInspector(
  blockedReasons: string[],
  selectedTaskId: string | null = null,
): O7RouteReplayInspector {
  // inspector 失败时也返回完整只读结构，前端不用根据缺字段自行补安全状态。
  return {
    status: "blocked_not_proven",
    selected_task_id: selectedTaskId,
    map_frame: "",
    frame_count: 0,
    sample_frames: [],
    event_timeline: [],
    keyframe_refs: [],
    cursor_initial_state: {
      playing: false,
      safe_to_play: false,
      speed: 0,
      frame_index: null,
    },
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_history_route_replay",
      "real_o7_cloud_archive_task_api",
      "safe_route_playback",
      "real_robot_control",
    ],
  };
}

function emptyLabelingQueueInspector(
  blockedReasons: string[],
  selectedTaskId: string | null = null,
): O7LabelingQueueInspector {
  // 标注 inspector 失败时必须清空样本，并固定所有提交、回滚、导出和真实 API 字段为 false。
  return {
    status: "blocked_not_proven",
    selected_task_id: selectedTaskId,
    review_item_count: 0,
    sample_review_items: [],
    label_schema: {
      schema_ref: "",
      version: "",
      required_fields: [],
      allowed_fields: [],
    },
    allowed_label_types: [],
    draft_labels: {
      count: 0,
      sample: [],
      autosave_available: false,
    },
    dataset_export: {
      available: false,
      status: "blocked_not_available",
      export_ref: "",
      supported_formats: [],
      gaps: blockedReasons,
    },
    submit_enabled: false,
    rollback_enabled: false,
    dataset_export_available: false,
    real_annotation_api_connected: false,
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_annotation_api",
      "real_o7_annotation_submit",
      "real_o7_annotation_rollback",
      "real_o7_dataset_export",
    ],
  };
}

function emptySummaries(status: "fixture_summary_only" | "blocked_not_proven"): O7CloudArchiveTaskSafeSummaries {
  // 空摘要也显式带 false 字段，避免前端根据缺字段自行推断。
  return {
    trajectory: { frame_count: 0, sample_refs: [], status },
    events: { event_count: 0, sample_types: [], status },
    labels: { label_count: 0, sample_types: [], real_annotation_api_connected: false, status },
    voice: { asr_event_count: 0, tts_draft_count: 0, real_voice_api_connected: false, status },
    commands: { command_count: 0, sample_kinds: [], real_command_api_connected: false, robot_control_executed: false, status },
  };
}

function blockedResponse(
  status: O7CloudArchiveTasksResponse["input_status"]["status"],
  failureReason: string,
  archivePath = "",
): O7CloudArchiveTasksResponse {
  const blockedReasons = [failureReason];
  // 失败也返回完整 schema，调用方不用靠 HTTP 500 或缺字段判断安全边界。
  return {
    schema: "trashbot.o7.cloud_archive_tasks.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    archive_status: "blocked_not_proven",
    input_status: {
      archive_json: safeRef(archivePath),
      status,
      failure_reason: failureReason,
    },
    source_fixture_schema: "not_loaded",
    real_cloud_archive_connected: false,
    real_realtime_api_connected: false,
    real_annotation_api_connected: false,
    real_voice_api_connected: false,
    real_command_api_connected: false,
    robot_control_executed: false,
    task_list: {
      source: "local_json_fixture",
      total_tasks: 0,
      tasks: [],
      status: "blocked_not_proven",
    },
    selected_task: null,
    latest_task: null,
    safe_summaries: emptySummaries("blocked_not_proven"),
    route_replay_inspector: emptyRouteReplayInspector(blockedReasons),
    labeling_queue_inspector: emptyLabelingQueueInspector(blockedReasons),
    voice_asr_tts_inspector: emptyVoiceAsrTtsInspector(blockedReasons),
    safe_command_inspector: emptySafeCommandInspector(blockedReasons),
    fixed_false_fields: fixedFalseFields(),
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_cloud_archive_task_api",
      "real_o7_realtime_api",
      "real_o7_annotation_api",
      "real_o7_voice_api",
      "real_o7_command_api",
      "real_robot_control",
      "delivery_success",
    ],
  };
}

function taskSummary(value: unknown): O7CloudArchiveTaskSummary {
  // task 摘要只保留 selector 需要的稳定字段，不透传完整任务 payload。
  const task = isObject(value) ? value : {};
  return {
    task_id: safeText(task.task_id || task.id || "task_id_missing"),
    robot_id: safeText(task.robot_id || "robot_id_missing"),
    route_id: safeText(task.route_id || "route_id_missing"),
    status: safeText(task.status || task.task_status || "status_missing"),
    started_at_ms: safeNumber(task.started_at_ms),
    updated_at_ms: safeNumber(task.updated_at_ms ?? task.completed_at_ms),
    evidence_ref: safeRef(task.evidence_ref),
  };
}

function listFromTask(task: JsonObject, key: string): unknown[] {
  // archive fixture 允许按任务内嵌数组给出数据；非数组一律按空处理。
  const value = task[key];
  return Array.isArray(value) ? value : [];
}

function sampleTypes(values: unknown[], keys: string[]): string[] {
  // 类型列表只用于 operator 快速判断数据形态，限量后不会泄露完整 event/label/command。
  return values.slice(0, SAMPLE_LIMIT).map((value) => {
    const item = isObject(value) ? value : {};
    const found = keys.map((key) => item[key]).find((candidate) => asText(candidate).trim());
    return safeText(found || "type_missing");
  });
}

function sampleRefs(values: unknown[]): string[] {
  // 轨迹/关键帧引用只返回安全 basename，完整 archive 不通过该 API 搬运。
  return values.slice(0, SAMPLE_LIMIT).map((value) => {
    const item = isObject(value) ? value : {};
    return safeRef(item.evidence_ref ?? item.frame_ref ?? item.keyframe_ref);
  }).filter(Boolean);
}

function fieldList(value: unknown): string[] {
  // schema 字段列表只展示字符串形式并限量，避免把复杂约束对象原样搬到 UI。
  return Array.isArray(value) ? value.slice(0, SAMPLE_LIMIT).map(safeText).filter(Boolean) : [];
}

function nestedObject(value: unknown): JsonObject {
  // trajectory frame 常把 pose/velocity 放在子对象里；非对象按空对象处理来保持 fail-soft 摘要。
  return isObject(value) ? value : {};
}

function labelSample(value: unknown): O7LabelingQueueInspectorLabelSample {
  // 兼容 label_type/value 和 type/label 两种常见 fixture 形状，输出统一只读 sample。
  const label = isObject(value) ? value : {};
  return {
    label_type: safeText(label.label_type || label.type || "label_type_missing"),
    value: safeText(label.value || label.label || "value_missing"),
    status: safeText(label.status || "fixture_summary_only"),
    evidence_ref: safeRef(label.evidence_ref ?? label.label_ref),
  };
}

function labelsFromItem(item: JsonObject): unknown[] {
  // review item 里可能叫 current_labels，也可能沿用 labels；非数组一律视为空。
  const current = item.current_labels;
  if (Array.isArray(current)) {
    return current;
  }
  if (isObject(current) && Array.isArray(current.labels)) {
    return current.labels;
  }
  return listFromTask(item, "labels");
}

function safeRefList(value: unknown, limit: number): string[] {
  // 引用数组统一限量和 basename 化，防止 archive fixture 被当成文件列表导出接口。
  return Array.isArray(value) ? value.slice(0, limit).map((item) => safeRef(item)).filter(Boolean) : [];
}

function safeTextList(value: unknown, limit: number): string[] {
  // gaps 是用户可见问题列表，只展示短数组和脱敏文本。
  return Array.isArray(value) ? value.slice(0, limit).map((item) => safeText(item)).filter(Boolean) : [];
}

function sampleAsrEvent(value: unknown): O7VoiceAsrTtsInspectorAsrEvent {
  // ASR sample 只保留可复核的白名单字段，不透传音频、设备或原始 payload。
  const event = isObject(value) ? value : {};
  return {
    event_type: safeText(event.event_type ?? event.type ?? "event_type_missing"),
    timestamp_ms: safeNumber(event.timestamp_ms ?? event.t_ms),
    transcript: safeText(event.transcript ?? event.text),
    confidence: safeNumber(event.confidence),
    evidence_ref: safeRef(event.evidence_ref ?? event.event_ref),
  };
}

function eventKind(event: O7VoiceAsrTtsInspectorAsrEvent): "partial" | "final" {
  // 只有明确 final 才进入 final slot，其他 ASR 类型都按 partial 槽位检查。
  return event.event_type.toLowerCase() === "final" ? "final" : "partial";
}

function latestVoiceSlot(
  events: O7VoiceAsrTtsInspectorAsrEvent[],
  type: "partial" | "final",
): O7VoiceAsrTtsInspectorTranscriptSlot {
  // latest 从已脱敏事件中计算，避免回读原始 transcript。
  const latest = [...events].reverse().find((event) => eventKind(event) === type);
  if (!latest) {
    return voiceBlockedSlot(type, "empty_not_proven");
  }
  return {
    text: latest.transcript,
    timestamp_ms: latest.timestamp_ms,
    confidence: latest.confidence,
    evidence_ref: latest.evidence_ref,
    status: "fixture_summary_only",
  };
}

function firstTtsDraft(task: JsonObject): JsonObject {
  // 新 archive 使用 tts_drafts[]，旧 fixture 可能只有 tts_draft 单对象；两者都只读摘要。
  const drafts = listFromTask(task, "tts_drafts").filter(isObject);
  if (drafts.length > 0) {
    return drafts[0] ?? {};
  }
  return isObject(task.tts_draft) ? task.tts_draft : {};
}

function mediaPreflightGaps(value: unknown): string[] {
  // media preflight 是 KR5 的前置依赖；即使 fixture 给出状态，也继续补上真实设备缺口。
  const media = isObject(value) ? value : {};
  const fixtureGaps = safeTextList(media.gaps, SAMPLE_LIMIT);
  return Array.from(new Set([
    ...fixtureGaps,
    "board_media_preflight_not_collected_by_pc",
    "real_audio_input_not_proven",
    "real_audio_playback_not_proven",
    "rtc_media_smoke_not_proven",
  ]));
}

function voiceAsrTtsInspectorFor(task: JsonObject | null): O7VoiceAsrTtsInspector {
  if (!task) {
    return emptyVoiceAsrTtsInspector(["selected_task_missing"]);
  }

  const selectedTaskId = safeText(task.task_id || task.id || "task_id_missing");
  const asrEventsRaw = listFromTask(task, "asr_events");
  const asrEvents = asrEventsRaw.map(sampleAsrEvent);
  const ttsDraft = firstTtsDraft(task);
  const voiceProfile = isObject(task.voice_profile) ? task.voice_profile : {};
  const voiceSession = isObject(task.voice_session) ? task.voice_session : {};
  const speakerAck = isObject(task.speaker_ack) ? task.speaker_ack : {};
  const mediaPreflight = isObject(task.media_preflight) ? task.media_preflight : {};
  const ttsText = safeText(ttsDraft.text ?? ttsDraft.transcript ?? "");
  const summaryText = ttsText.length > 120 ? `${ttsText.slice(0, 120)}...` : ttsText;
  const blockedReasons = [
    "real_voice_api_not_connected",
    "asr_stream_not_connected",
    "tts_send_disabled",
    "speaker_dispatch_disabled",
    "speaker_ack_not_proven",
    "board_media_preflight_dependency_not_proven",
  ];

  if (asrEventsRaw.length === 0 && Object.keys(ttsDraft).length === 0) {
    return emptyVoiceAsrTtsInspector(["voice_asr_events_and_tts_draft_missing", ...blockedReasons], selectedTaskId);
  }

  return {
    status: "fixture_voice_ready",
    selected_task_id: selectedTaskId,
    voice_session: {
      session_id: safeText(voiceSession.session_id ?? task.voice_session_id ?? task.session_id ?? "not_provided"),
      source: "local_json_fixture",
      evidence_ref: safeRef(voiceSession.evidence_ref ?? task.voice_evidence_ref ?? task.evidence_ref),
      audit_refs: safeRefList(voiceSession.audit_refs ?? task.voice_audit_refs ?? task.audit_refs, SAMPLE_LIMIT),
      status: "fixture_summary_only",
    },
    asr_event_count: asrEventsRaw.length,
    sample_asr_events: asrEvents.slice(0, SAMPLE_LIMIT),
    latest_partial: latestVoiceSlot(asrEvents, "partial"),
    latest_final: latestVoiceSlot(asrEvents, "final"),
    tts_draft: {
      text: summaryText,
      text_length: ttsText.length,
      voice_profile: safeText(ttsDraft.voice_profile ?? voiceProfile.name ?? voiceProfile.profile ?? "not_provided"),
      language: safeText(ttsDraft.language ?? voiceProfile.language ?? "zh-CN") || "zh-CN",
      confirmation_required: true,
      status: Object.keys(ttsDraft).length > 0 ? "fixture_draft_only" : "blocked_not_proven",
    },
    speaker_dispatch: {
      sends_to_robot: false,
      speaker_dispatch_enabled: false,
      ack_status: safeText(speakerAck.ack_status ?? speakerAck.status ?? "blocked_not_proven") || "blocked_not_proven",
      speaker_ack_ref: safeRef(speakerAck.speaker_ack_ref ?? speakerAck.evidence_ref) || "missing_speaker_dispatch_ack",
      failure_event_ref: safeRef(speakerAck.failure_event_ref) || "missing_speaker_failure_event",
      failure_refs: safeRefList(speakerAck.failure_refs, SAMPLE_LIMIT),
      status: "blocked_not_proven",
    },
    media_preflight_dependency: {
      required: true,
      source_schema: "trashbot.o7_board_media_preflight.v1",
      status: safeText(mediaPreflight.status ?? "blocked") || "blocked",
      dependency_ref: safeRef(mediaPreflight.dependency_ref) || "board_media_preflight_summary",
      gaps: mediaPreflightGaps(mediaPreflight),
    },
    asr_stream_connected: false,
    tts_send_enabled: false,
    speaker_dispatch_enabled: false,
    real_voice_api_connected: false,
    real_asr_tts_runtime_connected: false,
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_voice_api",
      "real_o7_asr_tts_runtime",
      "real_asr_stream",
      "real_asr_partial_transcript",
      "real_asr_final_transcript",
      "real_tts_send",
      "real_tts_playback",
      "real_speaker_dispatch_ack",
      "real_speaker_failure_event",
      "real_audio_device",
      "real_rtc_session",
    ],
  };
}

function inferAllowedLabelTypes(labels: unknown[]): string[] {
  // 没有显式 allowed_label_types 时，从 label sample 反推一个只读检查列表。
  return [...new Set(labels.map((label) => labelSample(label).label_type).filter((labelType) => labelType !== "label_type_missing"))]
    .slice(0, SAMPLE_LIMIT);
}

function labelingQueueInspectorFor(task: JsonObject | null): O7LabelingQueueInspector {
  if (!task) {
    return emptyLabelingQueueInspector(["selected_task_missing"]);
  }

  const selectedTaskId = safeText(task.task_id || task.id || "task_id_missing");
  const reviewItems = listFromTask(task, "review_items").filter(isObject);
  const labels = listFromTask(task, "labels");
  const hasReviewItems = reviewItems.length > 0;
  const sourceItems: JsonObject[] = hasReviewItems
    ? reviewItems
    : labels.map((label) => ({
      item_id: isObject(label) ? label.item_id : undefined,
      task_id: selectedTaskId,
      frame_id: isObject(label) ? label.frame_id : undefined,
      media_ref: isObject(label) ? label.media_ref : undefined,
      evidence_ref: isObject(label) ? label.evidence_ref : undefined,
      current_labels: [label],
    }));
  const draftValues = listFromTask(task, "draft_labels");
  const draftSource = draftValues.length > 0 ? draftValues : labels;
  const schema = isObject(task.label_schema) ? task.label_schema : {};
  const datasetExport = isObject(task.dataset_export) ? task.dataset_export : {};
  const allowedTypes = fieldList(task.allowed_label_types);
  const blockedReasons = [
    "real_annotation_api_not_connected",
    "annotation_submit_disabled",
    "annotation_rollback_disabled",
    "dataset_export_disabled",
  ];

  if (sourceItems.length === 0 && labels.length === 0) {
    return emptyLabelingQueueInspector(["labeling_review_items_missing", ...blockedReasons], selectedTaskId);
  }

  return {
    status: "fixture_labeling_ready",
    selected_task_id: selectedTaskId,
    review_item_count: sourceItems.length,
    sample_review_items: sourceItems.slice(0, SAMPLE_LIMIT).map((value, index) => {
      const item = isObject(value) ? value : {};
      const currentLabels = labelsFromItem(item);
      return {
        item_id: safeText(item.item_id || `label_item_${index + 1}`),
        task_id: safeText(item.task_id || selectedTaskId),
        frame_id: safeText(item.frame_id || `frame_${index + 1}`),
        media_ref: safeRef(item.media_ref ?? item.frame_ref),
        evidence_ref: safeRef(item.evidence_ref ?? item.item_ref),
        current_labels: {
          count: currentLabels.length,
          sample: currentLabels.slice(0, 3).map(labelSample),
        },
      };
    }),
    label_schema: {
      schema_ref: safeRef(schema.schema_ref ?? schema.evidence_ref),
      version: safeText(schema.version || ""),
      required_fields: fieldList(schema.required_fields),
      allowed_fields: fieldList(schema.allowed_fields),
    },
    allowed_label_types: (allowedTypes.length > 0 ? allowedTypes : inferAllowedLabelTypes(labels)).slice(0, SAMPLE_LIMIT),
    draft_labels: {
      count: draftSource.length,
      sample: draftSource.slice(0, SAMPLE_LIMIT).map(labelSample),
      autosave_available: false,
    },
    dataset_export: {
      available: false,
      status: Object.keys(datasetExport).length > 0 ? "fixture_summary_only" : "blocked_not_available",
      export_ref: safeRef(datasetExport.export_ref ?? datasetExport.evidence_ref),
      supported_formats: fieldList(datasetExport.supported_formats),
      gaps: fieldList(datasetExport.gaps).length > 0 ? fieldList(datasetExport.gaps) : ["real_dataset_export_api_not_connected"],
    },
    submit_enabled: false,
    rollback_enabled: false,
    dataset_export_available: false,
    real_annotation_api_connected: false,
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_annotation_api",
      "real_o7_annotation_submit",
      "real_o7_annotation_rollback",
      "real_o7_dataset_export",
    ],
  };
}

function frameNumber(frame: JsonObject, key: string, nested: JsonObject): number | null {
  // 只接受有限 number，字符串数值不会被提升，避免 fixture 文本注入成真实轨迹坐标。
  return safeNumber(frame[key]) ?? safeNumber(nested[key]);
}

function routeReplayInspectorFor(task: JsonObject | null): O7RouteReplayInspector {
  if (!task) {
    return emptyRouteReplayInspector(["selected_task_missing"]);
  }

  const selectedTaskId = safeText(task.task_id || task.id || "task_id_missing");
  const trajectory = listFromTask(task, "trajectory_frames");
  const events = [...listFromTask(task, "events"), ...listFromTask(task, "state_transitions")];
  const sampleFrames = trajectory.slice(0, SAMPLE_LIMIT).map((value, index) => {
    const frame = isObject(value) ? value : {};
    const pose = nestedObject(frame.pose);
    const velocity = nestedObject(frame.velocity);
    const frameIndex = safeNumber(frame.frame_index) ?? index;
    return {
      frame_index: frameIndex,
      timestamp_ms: safeNumber(frame.timestamp_ms),
      x_m: frameNumber(frame, "x_m", pose) ?? safeNumber(pose.x),
      y_m: frameNumber(frame, "y_m", pose) ?? safeNumber(pose.y),
      yaw_rad: frameNumber(frame, "yaw_rad", pose),
      speed_mps: safeNumber(frame.speed_mps) ?? safeNumber(frame.linear_mps) ?? safeNumber(velocity.speed_mps) ?? safeNumber(velocity.linear_mps),
      state: safeText(frame.state || frame.task_state || "state_missing"),
      evidence_ref: safeRef(frame.evidence_ref ?? frame.frame_ref ?? frame.keyframe_ref),
    };
  });
  const keyframeRefs = listFromTask(task, "keyframe_refs").slice(0, SAMPLE_LIMIT).map((value) => (
    isObject(value) ? safeRef(value.evidence_ref ?? value.keyframe_ref ?? value.frame_ref) : safeRef(value)
  )).filter(Boolean);

  return {
    status: trajectory.length > 0 ? "fixture_inspector_ready" : "blocked_not_proven",
    selected_task_id: selectedTaskId,
    map_frame: safeText(task.map_frame || "map"),
    frame_count: trajectory.length,
    sample_frames: sampleFrames,
    event_timeline: events.slice(0, SAMPLE_LIMIT).map((value) => {
      const event = isObject(value) ? value : {};
      return {
        event_type: safeText(event.event_type || event.type || "event_type_missing"),
        state: safeText(event.state || event.to || event.to_state || "state_missing"),
        timestamp_ms: safeNumber(event.timestamp_ms),
        evidence_ref: safeRef(event.evidence_ref ?? event.event_ref),
      };
    }),
    keyframe_refs: keyframeRefs,
    cursor_initial_state: {
      playing: false,
      safe_to_play: false,
      speed: 0,
      frame_index: sampleFrames[0]?.frame_index ?? null,
    },
    blocked_reasons: [
      "real_cloud_archive_not_connected",
      "safe_route_playback_not_enabled",
      "robot_control_disabled",
    ],
    not_proven: [
      "real_o7_history_route_replay",
      "real_o7_cloud_archive_task_api",
      "safe_route_playback",
      "real_robot_control",
    ],
  };
}

function sampleCommand(value: unknown, index: number): O7SafeCommandInspectorCommandSample {
  // command sample 只保留 selector/debug 需要的白名单字段，不携带 payload 或执行结果。
  const command = isObject(value) ? value : {};
  return {
    command_id: safeText(command.command_id ?? command.id ?? `command_${index + 1}`),
    command_type: safeText(command.command_type ?? command.kind ?? command.type ?? "command_type_missing"),
    status: safeText(command.status ?? command.command_status ?? "fixture_summary_only"),
    envelope_ref: safeRef(command.envelope_ref ?? command.command_ref ?? command.evidence_ref),
    idempotency_key_ref: safeRef(command.idempotency_key_ref ?? command.idempotency_ref),
    evidence_ref: safeRef(command.evidence_ref ?? command.audit_ref),
  };
}

function safeCommandInspectorFor(task: JsonObject | null): O7SafeCommandInspector {
  if (!task) {
    return emptySafeCommandInspector(["selected_task_missing"]);
  }

  const selectedTaskId = safeText(task.task_id || task.id || "task_id_missing");
  const commands = listFromTask(task, "commands");
  const commandSession = isObject(task.command_session) ? task.command_session : {};
  const manualTurn = isObject(task.manual_turn_envelope) ? task.manual_turn_envelope : {};
  const navigateGoal = isObject(task.navigate_goal_envelope) ? task.navigate_goal_envelope : {};
  const velocityLimits = isObject(task.velocity_limits) ? task.velocity_limits : {};
  const steeringLimits = isObject(task.steering_limits) ? task.steering_limits : {};
  const mapGoalSlot = isObject(task.map_goal_slot) ? task.map_goal_slot : {};
  const idempotency = isObject(task.idempotency_key_requirement) ? task.idempotency_key_requirement : {};
  const confirmation = isObject(task.confirmation_policy) ? task.confirmation_policy : {};
  const robotAck = isObject(task.robot_ack_status)
    ? task.robot_ack_status
    : isObject(task.command_ack)
      ? task.command_ack
      : {};
  const mapFrame = safeText(mapGoalSlot.map_frame ?? navigateGoal.map_frame ?? task.map_frame ?? "map") || "map";
  const blockedReasons = [
    "real_command_api_not_connected",
    "command_dispatch_disabled",
    "manual_control_disabled",
    "navigate_goal_disabled",
    "keyboard_control_disabled",
    "robot_ack_not_proven",
    "hil_or_hardware_safety_not_proven",
    "delivery_success_not_proven",
  ];

  if (commands.length === 0 && Object.keys(manualTurn).length === 0 && Object.keys(navigateGoal).length === 0) {
    return emptySafeCommandInspector(["commands_and_command_envelopes_missing", ...blockedReasons], selectedTaskId);
  }

  return {
    status: "fixture_command_ready",
    selected_task_id: selectedTaskId,
    command_session: {
      command_session_id: safeText(commandSession.command_session_id ?? task.command_session_id ?? "not_provided"),
      source: "local_json_fixture",
      evidence_ref: safeRef(commandSession.evidence_ref ?? task.command_evidence_ref ?? task.evidence_ref),
      audit_refs: safeRefList(commandSession.audit_refs ?? task.command_audit_refs ?? task.audit_refs, SAMPLE_LIMIT),
      status: "fixture_summary_only",
    },
    command_count: commands.length,
    sample_commands: commands.slice(0, SAMPLE_LIMIT).map(sampleCommand),
    manual_turn_envelope: {
      sends_to_robot: false,
      requested_direction: safeText(manualTurn.requested_direction ?? manualTurn.direction ?? "not_provided"),
      velocity_limited: true,
      steering_limited: true,
      evidence_ref: safeRef(manualTurn.evidence_ref) || "missing_manual_turn_command_envelope_trace",
      status: Object.keys(manualTurn).length > 0 ? "fixture_summary_only" : "blocked_not_proven",
    },
    navigate_goal_envelope: {
      sends_to_robot: false,
      goal_source: safeText(navigateGoal.goal_source ?? "fixture_map_goal_slot") || "fixture_map_goal_slot",
      map_frame: safeText(navigateGoal.map_frame ?? mapFrame) || "map",
      x_m: safeNumber(navigateGoal.x_m ?? navigateGoal.x),
      y_m: safeNumber(navigateGoal.y_m ?? navigateGoal.y),
      yaw_rad: safeNumber(navigateGoal.yaw_rad ?? navigateGoal.yaw),
      evidence_ref: safeRef(navigateGoal.evidence_ref) || "missing_navigate_goal_command_envelope_trace",
      status: Object.keys(navigateGoal).length > 0 ? "fixture_summary_only" : "blocked_not_proven",
    },
    velocity_limits: {
      max_linear_mps: safeNumber(velocityLimits.max_linear_mps),
      max_angular_radps: safeNumber(velocityLimits.max_angular_radps),
      source: safeText(velocityLimits.source ?? "local_json_fixture_not_hil") || "local_json_fixture_not_hil",
      hardware_verified: false,
      status: Object.keys(velocityLimits).length > 0 ? "fixture_limit_summary_only" : "blocked_not_proven",
    },
    steering_limits: {
      max_steering_angle_rad: safeNumber(steeringLimits.max_steering_angle_rad),
      max_turn_rate_radps: safeNumber(steeringLimits.max_turn_rate_radps),
      source: safeText(steeringLimits.source ?? "local_json_fixture_not_hil") || "local_json_fixture_not_hil",
      hardware_verified: false,
      status: Object.keys(steeringLimits).length > 0 ? "fixture_limit_summary_only" : "blocked_not_proven",
    },
    map_goal_slot: {
      map_frame: mapFrame,
      x_m: safeNumber(mapGoalSlot.x_m ?? mapGoalSlot.x),
      y_m: safeNumber(mapGoalSlot.y_m ?? mapGoalSlot.y),
      yaw_rad: safeNumber(mapGoalSlot.yaw_rad ?? mapGoalSlot.yaw),
      status: Object.keys(mapGoalSlot).length > 0 ? "fixture_slot_summary_only" : "blocked_not_proven",
      evidence_ref: safeRef(mapGoalSlot.evidence_ref) || "missing_map_goal_selection_trace",
    },
    idempotency_key_requirement: {
      required: true,
      key_ref: safeRef(idempotency.key_ref ?? idempotency.evidence_ref) || "missing_idempotency_key_requirement",
      header: "Idempotency-Key",
      status: Object.keys(idempotency).length > 0 ? "fixture_requirement_summary_only" : "blocked_not_proven",
    },
    confirmation_policy: {
      manual_turn_requires_confirmation: true,
      navigate_goal_requires_confirmation: true,
      keyboard_control_requires_hold: true,
      status: safeText(confirmation.status ?? "fixture_policy_summary_only") === "blocked_not_proven"
        ? "blocked_not_proven"
        : "fixture_policy_summary_only",
    },
    robot_ack_blocked_summary: {
      ack_status: "blocked_not_proven",
      last_command_id: safeText(robotAck.last_command_id ?? "not_provided"),
      ack_ref: safeRef(robotAck.ack_ref ?? robotAck.evidence_ref) || "missing_robot_command_ack",
      timeout_ms: safeNumber(robotAck.timeout_ms),
      cancel_ack_ref: safeRef(robotAck.cancel_ack_ref) || "missing_robot_cancel_ack",
      stop_ack_ref: safeRef(robotAck.stop_ack_ref) || "missing_robot_stop_ack",
      recovery_ref: safeRef(robotAck.recovery_ref) || "missing_robot_recovery_event",
      status: "blocked_not_proven",
    },
    evidence_gaps: defaultCommandEvidenceGaps(task.command_evidence_gaps ?? task.evidence_gaps),
    command_dispatch_enabled: false,
    manual_control_enabled: false,
    navigate_goal_enabled: false,
    keyboard_control_enabled: false,
    real_command_api_connected: false,
    real_robot_ack_connected: false,
    robot_control_executed: false,
    safe_to_control: false,
    primary_actions_enabled: false,
    delivery_success: false,
    blocked_reasons: blockedReasons,
    not_proven: [
      "real_o7_safe_command_api",
      "real_manual_turn_control",
      "real_navigate_goal_dispatch",
      "real_keyboard_control",
      "real_robot_command_ack",
      "real_timeout_cancel_stop_recovery",
      "real_hil_or_hardware_safety",
      "delivery_success",
    ],
  };
}

function safeSummariesFor(task: JsonObject | null): O7CloudArchiveTaskSafeSummaries {
  if (!task) {
    return emptySummaries("blocked_not_proven");
  }
  const trajectory = listFromTask(task, "trajectory_frames");
  const events = listFromTask(task, "events");
  const labels = listFromTask(task, "labels");
  const asrEvents = listFromTask(task, "asr_events");
  const ttsDrafts = listFromTask(task, "tts_drafts");
  const commands = listFromTask(task, "commands");
  return {
    trajectory: {
      frame_count: trajectory.length,
      sample_refs: sampleRefs(trajectory),
      status: "fixture_summary_only",
    },
    events: {
      event_count: events.length,
      sample_types: sampleTypes(events, ["event_type", "type", "state"]),
      status: "fixture_summary_only",
    },
    labels: {
      label_count: labels.length,
      sample_types: sampleTypes(labels, ["label_type", "type"]),
      real_annotation_api_connected: false,
      status: "fixture_summary_only",
    },
    voice: {
      asr_event_count: asrEvents.length,
      tts_draft_count: ttsDrafts.length,
      real_voice_api_connected: false,
      status: "fixture_summary_only",
    },
    commands: {
      command_count: commands.length,
      sample_kinds: sampleTypes(commands, ["command_type", "kind", "type"]),
      real_command_api_connected: false,
      robot_control_executed: false,
      status: "fixture_summary_only",
    },
  };
}

function latestTask(tasks: JsonObject[]): JsonObject | null {
  // latest 只基于 fixture 时间戳排序；没有时间戳时回退到最后一个任务，仍是 software proof。
  if (tasks.length === 0) {
    return null;
  }
  return [...tasks].sort((left, right) => {
    const leftTime = safeNumber(left.updated_at_ms ?? left.started_at_ms) ?? -1;
    const rightTime = safeNumber(right.updated_at_ms ?? right.started_at_ms) ?? -1;
    return rightTime - leftTime;
  })[0] ?? tasks[tasks.length - 1] ?? null;
}

export async function buildO7CloudArchiveTasks(options: O7CloudArchiveTasksOptions = {}): Promise<O7CloudArchiveTasksResponse> {
  const archiveJson = options.archiveJson?.trim() ?? "";
  if (!archiveJson) {
    return blockedResponse("not_provided", "archive_json_not_provided");
  }

  let raw = "";
  try {
    raw = await fs.readFile(archiveJson, "utf8");
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    return blockedResponse(code === "ENOENT" ? "missing" : "read_error", "archive_json_read_failed", archiveJson);
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return blockedResponse("bad_json", "archive_json_bad_json", archiveJson);
  }

  if (!isObject(parsed)) {
    return blockedResponse("not_object", "archive_json_not_object", archiveJson);
  }
  if (parsed.schema !== SUPPORTED_SCHEMA) {
    return blockedResponse("unsupported_schema", "archive_json_unsupported_schema", archiveJson);
  }
  if (hasForbiddenCopy(parsed)) {
    return blockedResponse("unsafe_copy", "archive_json_unsafe_copy", archiveJson);
  }
  if (hasSuccessClaim(parsed)) {
    return blockedResponse("success_claim", "archive_json_success_claim", archiveJson);
  }
  if (hasControlClaim(parsed)) {
    return blockedResponse("control_claim", "archive_json_control_claim", archiveJson);
  }
  if (hasRealApiClaim(parsed)) {
    return blockedResponse("real_api_claim", "archive_json_real_api_claim", archiveJson);
  }

  const taskObjects = (Array.isArray(parsed.tasks) ? parsed.tasks : []).filter(isObject);
  const selectedId = safeText(parsed.selected_task_id);
  const selected = taskObjects.find((task) => safeText(task.task_id || task.id) === selectedId) ?? latestTask(taskObjects);
  const latest = latestTask(taskObjects);

  return {
    schema: "trashbot.o7.cloud_archive_tasks.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    archive_status: "fixture_archive_ready",
    input_status: {
      archive_json: safeRef(archiveJson),
      status: "loaded",
      failure_reason: "",
    },
    source_fixture_schema: SUPPORTED_SCHEMA,
    real_cloud_archive_connected: false,
    real_realtime_api_connected: false,
    real_annotation_api_connected: false,
    real_voice_api_connected: false,
    real_command_api_connected: false,
    robot_control_executed: false,
    task_list: {
      source: "local_json_fixture",
      total_tasks: taskObjects.length,
      tasks: taskObjects.slice(0, TASK_LIMIT).map(taskSummary),
      status: "fixture_summary_only",
    },
    selected_task: selected ? taskSummary(selected) : null,
    latest_task: latest ? taskSummary(latest) : null,
    safe_summaries: safeSummariesFor(selected),
    route_replay_inspector: routeReplayInspectorFor(selected),
    labeling_queue_inspector: labelingQueueInspectorFor(selected),
    voice_asr_tts_inspector: voiceAsrTtsInspectorFor(selected),
    safe_command_inspector: safeCommandInspectorFor(selected),
    fixed_false_fields: fixedFalseFields(),
    blocked_reasons: [
      "real_cloud_archive_not_connected",
      "real_realtime_api_not_connected",
      "real_annotation_api_not_connected",
      "real_voice_api_not_connected",
      "real_command_api_not_connected",
      "robot_control_disabled",
    ],
    not_proven: [
      "real_o7_cloud_archive_task_api",
      "real_o7_history_route_replay",
      "real_o7_annotation_api",
      "real_o7_voice_api",
      "real_o7_command_api",
      "real_robot_control",
      "delivery_success",
    ],
  };
}
