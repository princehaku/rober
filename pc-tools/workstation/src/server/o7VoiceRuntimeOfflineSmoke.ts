import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import { buildO7VoiceRuntimePreflight } from "./o7VoiceRuntimePreflight";
import type {
  O7VoiceRuntimeOfflineSmokeResult,
  O7VoiceRuntimeOfflineSmokeSelectedTask,
  O7VoiceRuntimeOfflineSmokeTraceEvent,
} from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7VoiceRuntimeOfflineSmokeOptions {
  configJson?: string;
  fixtureJson?: string;
  mode?: string;
  taskId?: string;
  env?: NodeJS.ProcessEnv;
}

const FIXTURE_SCHEMA = "trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_fixture.v1" as const;
const PROOF_BOUNDARY = "software_proof_o7_voice_runtime_offline_smoke_only" as const;
const DEFAULT_TASK = {
  task_id: "task_o3_28_pose_fixed_route_consumer_20260713_0402",
  robot_id: "robot_fixture",
  packet_id: "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
  route_intent_id: "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
} as const;
const SAFE_MODES = new Set(["local_stub", "offline_stub", "disabled_local"]);

const DANGEROUS_TRUE_FIELDS = [
  "real_voice_api_connected",
  "real_asr_tts_runtime_connected",
  "tts_send_enabled",
  "speaker_dispatch_enabled",
  "real_speaker_ack_proven",
  "microphone_opened",
  "speaker_playback_opened",
  "safe_to_control",
  "delivery_success",
  "robot_control_executed",
  "connects_cloud_production",
  "network_probe_executed",
  "writes_o6_archive_events",
  "route_execution_success",
  "hil_pass",
];

const UNSAFE_COPY_PATTERNS = [
  /^https?:\/\//i,
  /^wss?:\/\//i,
  /Bearer\s+[A-Za-z0-9._~+/=-]+/i,
  /\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+/i,
  /\b(postgres|postgresql|mysql|redis|amqp|mongodb):\/\//i,
  /\/cmd_vel\b/,
  /\/api\/base\/manual\b/,
  /NavigateToPose/i,
  /WAVE\s+ROVER/i,
  /\bUART\b/i,
  /\/dev\/(tty|snd|audio|input|cu\.)/i,
  /\braw_audio\b/i,
  /\baudio_base64\b/i,
  /\baudio_url\b/i,
  /\bplayback_url\b/i,
];

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown): string {
  // query/env/fixture 字段必须先变成短文本，避免 undefined 被误读成已配置。
  return value === null || value === undefined ? "" : String(value).trim();
}

function encoded(value: unknown): string {
  // 安全扫描用 JSON 文本覆盖嵌套字段；无法序列化时按空对象处理。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function pathRef(value: unknown): string {
  // 响应只返回 basename，避免把本机绝对路径带到浏览器或日志。
  const raw = text(value);
  if (!raw) {
    return "not_configured";
  }
  if (path.isAbsolute(raw) || raw.includes("/") || raw.includes("\\")) {
    return `file:${path.basename(raw)}`;
  }
  return raw;
}

function containsUnsafeCopy(value: unknown): boolean {
  // offline smoke 不接受 URL、凭证、音频 payload、设备路径、ROS 控制或硬件字样。
  const payload = encoded(value);
  return UNSAFE_COPY_PATTERNS.some((pattern) => pattern.test(payload));
}

function dangerousTrueFields(value: unknown): string[] {
  // 只要输入或 fixture 自称真实连接、播放、控制或送达成功，本轮必须 fail-closed。
  const raw = encoded(value);
  const payload = isObject(value) ? value : {};
  return DANGEROUS_TRUE_FIELDS.filter((field) =>
    payload[field] === true || new RegExp(`"${field}"\\s*:\\s*true`).test(raw),
  );
}

function safeIdentity(value: unknown, fallback: string): string {
  // selected task identity 只允许短 token，不能夹带路径、URL、命令或多行 payload。
  const candidate = text(value) || fallback;
  if (!/^[A-Za-z0-9_.:-]{1,160}$/.test(candidate)) {
    return "";
  }
  return candidate;
}

async function loadFixture(fixtureJson: string): Promise<{ payload: JsonObject | null; reason: string }> {
  // fixture 是可选的本地 JSON；URL、设备路径和空路径不会进入 fs.readFile。
  const rawPath = text(fixtureJson);
  if (!rawPath) {
    return { payload: null, reason: "fixture_json_not_provided" };
  }
  if (containsUnsafeCopy(rawPath)) {
    return { payload: null, reason: "fixture_json_path_unsafe" };
  }
  try {
    const parsed = JSON.parse(await fs.readFile(path.resolve(rawPath), "utf8")) as unknown;
    if (!isObject(parsed)) {
      return { payload: null, reason: "fixture_json_not_object" };
    }
    return { payload: parsed, reason: "" };
  } catch (error) {
    if (error instanceof SyntaxError) {
      return { payload: null, reason: "fixture_json_bad_json" };
    }
    const code = (error as NodeJS.ErrnoException).code;
    return { payload: null, reason: code === "ENOENT" ? "fixture_json_missing" : "fixture_json_read_error" };
  }
}

function baseResponse(
  overrides: Partial<O7VoiceRuntimeOfflineSmokeResult>,
): O7VoiceRuntimeOfflineSmokeResult {
  // 固定 false 字段集中维护，避免 smoke ready 被误读成真实语音或机器人能力。
  return {
    schema: "trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    endpoint: "/api/o7/voice-runtime/offline-smoke",
    smoke_status: "blocked_by_voice_runtime_preflight",
    proof_boundary: PROOF_BOUNDARY,
    local_offline_only: true,
    fixture_schema: "not_loaded",
    fixture_path_ref: "not_configured",
    selected_task_id: DEFAULT_TASK.task_id,
    selected_robot_id: DEFAULT_TASK.robot_id,
    selected_packet_id: DEFAULT_TASK.packet_id,
    selected_route_intent_id: DEFAULT_TASK.route_intent_id,
    selected_task: {
      ...DEFAULT_TASK,
      source: "default_fixture",
      identity_status: "selected_task_identity_loaded_not_execution_proof",
    },
    preflight_derived_status: {
      preflight_status: "blocked_missing_voice_runtime_config",
      runtime_mode: "not_configured",
      runtime_configured: false,
      config_source: "not_configured",
      config_path_ref: "not_configured",
      no_network_access: true,
      no_device_access: true,
      no_audio_dispatch: true,
      blocked_reasons: ["voice_runtime_config_missing"],
    },
    smoke_trace_events: [],
    smoke_trace_event_count: 0,
    real_voice_api_connected: false,
    real_asr_tts_runtime_connected: false,
    asr_stream_connected: false,
    tts_send_enabled: false,
    speaker_dispatch_enabled: false,
    real_speaker_ack_proven: false,
    microphone_opened: false,
    speaker_playback_opened: false,
    reads_audio_device: false,
    network_probe_executed: false,
    writes_o6_archive_events: false,
    connects_cloud_production: false,
    robot_control_executed: false,
    route_execution_success: false,
    hil_pass: false,
    blocked_reasons: ["voice_runtime_config_missing"],
    not_proven: [
      "real_voice_api_connected=false",
      "real_asr_tts_runtime_connected=false",
      "tts_send_enabled=false",
      "speaker_dispatch_enabled=false",
      "real_speaker_ack_proven=false",
      "microphone_opened=false",
      "speaker_playback_opened=false",
      "safe_to_control=false",
      "delivery_success=false",
      "robot_control_executed=false",
      "route_execution_success=false",
      "hil_pass=false",
    ],
    next_required_evidence: [
      "authorized_real_voice_runtime_smoke",
      "same_task_real_asr_tts_trace",
      "real_microphone_open_readback",
      "real_speaker_playback_readback",
      "real_speaker_ack_for_selected_task",
      "delivery_result_for_selected_task",
    ],
    fail_closed_reason: "none",
    ...overrides,
  };
}

function failClosed(
  reason: string,
  selectedTask?: Partial<O7VoiceRuntimeOfflineSmokeSelectedTask>,
  fixtureJson = "",
): O7VoiceRuntimeOfflineSmokeResult {
  // fail_closed 仍返回完整 schema 和固定 false 字段，让 UI 无需靠异常分支保安全。
  const task = {
    ...DEFAULT_TASK,
    source: "default_fixture" as const,
    identity_status: "selected_task_identity_loaded_not_execution_proof" as const,
    ...selectedTask,
  };
  return baseResponse({
    smoke_status: "fail_closed",
    fixture_path_ref: pathRef(fixtureJson),
    selected_task_id: task.task_id,
    selected_robot_id: task.robot_id,
    selected_packet_id: task.packet_id,
    selected_route_intent_id: task.route_intent_id,
    selected_task: task,
    smoke_trace_events: [{
      event_index: 1,
      event_type: "preflight_config_checked",
      event_status: "fail_closed",
      task_id: task.task_id,
      detail: `offline_smoke_rejected:${reason}`,
      proof_boundary: PROOF_BOUNDARY,
    }],
    smoke_trace_event_count: 1,
    blocked_reasons: [reason],
    fail_closed_reason: reason,
  });
}

function selectedTaskFromInputs(
  taskId: string,
  fixture: JsonObject | null,
): { task: O7VoiceRuntimeOfflineSmokeSelectedTask | null; reason: string } {
  // task identity 可以来自 query、fixture 或默认样例，但三者不能互相矛盾。
  const fixtureTaskId = text(fixture?.task_id);
  if (taskId && fixtureTaskId && taskId !== fixtureTaskId) {
    return { task: null, reason: "task_id_mismatch" };
  }
  const source = fixtureTaskId ? "fixture_json" : taskId ? "query_task_id" : "default_fixture";
  const task = {
    task_id: safeIdentity(taskId || fixtureTaskId, DEFAULT_TASK.task_id),
    robot_id: safeIdentity(fixture?.robot_id, DEFAULT_TASK.robot_id),
    packet_id: safeIdentity(fixture?.packet_id, DEFAULT_TASK.packet_id),
    route_intent_id: safeIdentity(fixture?.route_intent_id, DEFAULT_TASK.route_intent_id),
    source,
    identity_status: "selected_task_identity_loaded_not_execution_proof",
  } satisfies O7VoiceRuntimeOfflineSmokeSelectedTask;
  if (!task.task_id || !task.robot_id || !task.packet_id || !task.route_intent_id) {
    return { task: null, reason: "selected_task_identity_unsafe" };
  }
  return { task, reason: "" };
}

function buildTraceEvents(task: O7VoiceRuntimeOfflineSmokeSelectedTask): O7VoiceRuntimeOfflineSmokeTraceEvent[] {
  // trace 是 deterministic local/offline stub，不从麦克风、喇叭、provider 或 O6 events 取真实信号。
  return [
    {
      event_index: 1,
      event_type: "preflight_config_checked",
      event_status: "ready_not_real_runtime",
      task_id: task.task_id,
      detail: "preflight_status=ready_for_configured_runtime_check_only; no_network_access=true",
      proof_boundary: PROOF_BOUNDARY,
    },
    {
      event_index: 2,
      event_type: "offline_asr_stub_loaded",
      event_status: "stub_trace_only",
      task_id: task.task_id,
      detail: "microphone_opened=false; asr_stream_connected=false",
      proof_boundary: PROOF_BOUNDARY,
    },
    {
      event_index: 3,
      event_type: "tts_draft_trace_prepared",
      event_status: "draft_not_sent",
      task_id: task.task_id,
      detail: "tts_send_enabled=false; real_voice_api_connected=false",
      proof_boundary: PROOF_BOUNDARY,
    },
    {
      event_index: 4,
      event_type: "speaker_ack_pending_not_real",
      event_status: "pending_not_real_ack",
      task_id: task.task_id,
      detail: "speaker_dispatch_enabled=false; real_speaker_ack_proven=false",
      proof_boundary: PROOF_BOUNDARY,
    },
  ];
}

export async function buildO7VoiceRuntimeOfflineSmoke(
  options: O7VoiceRuntimeOfflineSmokeOptions = {},
): Promise<O7VoiceRuntimeOfflineSmokeResult> {
  // offline smoke 先消费可选 fixture，再用 preflight builder 派生配置状态；全程不访问网络或音频设备。
  const env = options.env ?? process.env;
  const fixtureJson = text(options.fixtureJson);
  const mode = text(options.mode);
  const taskId = text(options.taskId);
  let fixture: JsonObject | null = null;
  if (fixtureJson) {
    const loaded = await loadFixture(fixtureJson);
    if (!loaded.payload) {
      return failClosed(loaded.reason, undefined, fixtureJson);
    }
    fixture = loaded.payload;
  }
  const fixtureMode = text(fixture?.runtime_mode);
  const effectiveMode = mode || fixtureMode;
  const rawInputSummary = { mode: effectiveMode, task_id: taskId, fixture };
  const claims = dangerousTrueFields(rawInputSummary);
  if (claims.length > 0) {
    return failClosed(`dangerous_true_fields:${claims.join(",")}`, undefined, fixtureJson);
  }
  if (containsUnsafeCopy(rawInputSummary)) {
    return failClosed("voice_runtime_offline_smoke_input_unsafe", undefined, fixtureJson);
  }
  if (fixture && fixture.schema !== FIXTURE_SCHEMA) {
    return failClosed("voice_runtime_offline_smoke_fixture_schema_unsupported", undefined, fixtureJson);
  }
  if (effectiveMode && !SAFE_MODES.has(effectiveMode)) {
    return failClosed("voice_runtime_mode_not_safe_local_or_offline", undefined, fixtureJson);
  }
  const selected = selectedTaskFromInputs(taskId, fixture);
  if (!selected.task) {
    return failClosed(selected.reason, undefined, fixtureJson);
  }
  const preflight = await buildO7VoiceRuntimePreflight({
    configJson: options.configJson,
    mode: effectiveMode,
    env,
  });
  const preflightSummary = {
    preflight_status: preflight.preflight_status,
    runtime_mode: preflight.runtime_mode,
    runtime_configured: preflight.runtime_configured,
    config_source: preflight.config_source,
    config_path_ref: preflight.config_path_ref,
    no_network_access: preflight.config_checks.no_network_access,
    no_device_access: preflight.config_checks.no_device_access,
    no_audio_dispatch: preflight.config_checks.no_audio_dispatch,
    blocked_reasons: preflight.blocked_reasons,
  };
  if (preflight.preflight_status === "fail_closed") {
    return failClosed(preflight.fail_closed_reason, selected.task, fixtureJson);
  }
  if (preflight.preflight_status !== "ready_for_configured_runtime_check_only") {
    return baseResponse({
      smoke_status: "blocked_by_voice_runtime_preflight",
      fixture_schema: fixture ? FIXTURE_SCHEMA : "not_loaded",
      fixture_path_ref: pathRef(fixtureJson),
      selected_task_id: selected.task.task_id,
      selected_robot_id: selected.task.robot_id,
      selected_packet_id: selected.task.packet_id,
      selected_route_intent_id: selected.task.route_intent_id,
      selected_task: selected.task,
      preflight_derived_status: preflightSummary,
      blocked_reasons: ["voice_runtime_preflight_not_ready", ...preflight.blocked_reasons],
    });
  }
  const traceEvents = buildTraceEvents(selected.task);
  return baseResponse({
    smoke_status: "ready_for_offline_smoke_trace_only",
    fixture_schema: fixture ? FIXTURE_SCHEMA : "not_loaded",
    fixture_path_ref: pathRef(fixtureJson),
    selected_task_id: selected.task.task_id,
    selected_robot_id: selected.task.robot_id,
    selected_packet_id: selected.task.packet_id,
    selected_route_intent_id: selected.task.route_intent_id,
    selected_task: selected.task,
    preflight_derived_status: preflightSummary,
    smoke_trace_events: traceEvents,
    smoke_trace_event_count: traceEvents.length,
    blocked_reasons: [
      "real_voice_runtime_not_connected",
      "offline_smoke_trace_only",
      "real_speaker_ack_not_proven",
      "delivery_success_false",
      "safe_to_control_false",
    ],
  });
}
