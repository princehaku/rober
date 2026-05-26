import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7VoicePreviewAsrEventSample,
  O7VoicePreviewResponse,
  O7VoicePreviewTranscriptSlot,
} from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7VoicePreviewOptions {
  fixtureJson?: string;
}

const SUPPORTED_SCHEMA = "trashbot.o7.voice_fixture.v1" as const;
const SAMPLE_EVENT_LIMIT = 3;
const SAMPLE_REF_LIMIT = 8;

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
  "serial",
  "UART",
  "baudrate",
  "WAVE ROVER",
  "Traceback",
];

const SUCCESS_CLAIM_PATTERNS = [
  /\bdelivery\s+(success|succeeded|completed|complete)\b/i,
  /\btts\s+(success|succeeded|completed|complete)\b/i,
  /\basr\s+(success|succeeded|completed|complete)\b/i,
  /\bvoice\s+(success|succeeded|completed|complete)\b/i,
  /"delivery_success"\s*:\s*true/i,
];

const CONTROL_CLAIM_PATTERNS = [
  /"primary_actions_enabled"\s*:\s*true/i,
  /"safe_to_control"\s*:\s*true/i,
  /"robot_control_executed"\s*:\s*true/i,
  /"command_dispatch_enabled"\s*:\s*true/i,
];

const ASR_CONNECTED_CLAIM_PATTERNS = [
  /"asr_stream_connected"\s*:\s*true/i,
  /"asr_connected"\s*:\s*true/i,
  /\basr\s+(stream\s+)?(connected|ready|live)\b/i,
];

const TTS_SEND_CLAIM_PATTERNS = [
  /"tts_send_enabled"\s*:\s*true/i,
  /"tts_send_available"\s*:\s*true/i,
  /\btts\s+(send|dispatch)\s+(enabled|available|ready)\b/i,
];

const SPEAKER_DISPATCH_CLAIM_PATTERNS = [
  /"speaker_dispatch_enabled"\s*:\s*true/i,
  /"speaker_dispatch_available"\s*:\s*true/i,
  /\bspeaker\s+dispatch\s+(enabled|available|ready)\b/i,
];

const REAL_VOICE_CLAIM_PATTERNS = [
  /"real_voice_api_connected"\s*:\s*true/i,
  /"real_asr_tts_runtime_connected"\s*:\s*true/i,
  /"voice_api_connected"\s*:\s*true/i,
  /\breal\s+(voice|asr|tts)\s+(api|runtime)\s+(connected|ready)\b/i,
];

const SPEAKER_ACK_SUCCESS_PATTERNS = [
  /"ack_status"\s*:\s*"(success|succeeded|acked|ok|played|delivered)"/i,
  /"speaker_ack"\s*:\s*true/i,
  /\bspeaker\s+ack\s+(success|succeeded|acked|ok|played|delivered)\b/i,
];

const SENSITIVE_PATTERNS: Array<[RegExp, string]> = [
  [/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]"],
  [/\bAuthorization\s*:\s*[^,\s]+/gi, "Authorization: [REDACTED]"],
  [/\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+/gi, "$1=[REDACTED]"],
  [/\b(postgres|postgresql|mysql|redis|amqp|mongodb):\/\/[^,\s]+/gi, "[REDACTED_URL]"],
  [/\/cmd_vel\b/g, "[REDACTED_ROS_TOPIC]"],
  [/\/dev\/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*/gi, "/dev/[REDACTED_DEVICE]"],
  [/\b[A-Za-z]:\\[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/\/(Users|home|tmp|private|var|mnt|run|workspace|ws)\/[^,\s"]+/g, "[REDACTED_LOCAL_PATH]"],
  [/\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+/gi, "$1=[REDACTED_RATE]"],
  [/WAVE\s+ROVER/gi, "[REDACTED_PLATFORM]"],
  [/Traceback \(most recent call last\):[\s\S]*/gi, "[REDACTED_TRACEBACK]"],
];

// 这个 adapter 只读取用户显式传入的本地语音 JSON fixture，并输出白名单摘要。
// 它不连接云端 voice API、不打开麦克风或喇叭、不播放音频、不发送 TTS，也不接 ROS2。
// ASR/TTS/speaker 相关“已连接、已发送、ACK 成功”声明一律 fail closed，防止 mock 被误读。
// transcript 与引用都限量、脱敏或 basename 化，避免本地路径、凭证和完整事件流外泄。

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown): string {
  // 空值不展示成业务状态，避免 null/undefined 被当作真实 transcript。
  return value === null || value === undefined ? "" : String(value);
}

function safeText(value: unknown): string {
  // 所有用户可见文本都先脱敏；语音 transcript 可能夹带路径或凭证。
  return SENSITIVE_PATTERNS.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), asText(value));
}

function safeRef(value: unknown): string {
  // evidence/audit 引用只保留文件名，PC preview 不泄露本机目录结构。
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
  // 只接受真实有限数字，字符串数字不自动提升，避免不可信 payload 伪装类型。
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function encoded(value: unknown): string {
  // fail-closed 扫描覆盖完整 fixture；不可序列化时按空对象处理。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function hasPattern(value: unknown, patterns: RegExp[]): boolean {
  // 深层危险声明统一在 JSON 文本上扫描，避免嵌套字段绕过。
  const payload = encoded(value);
  return patterns.some((pattern) => pattern.test(payload));
}

function hasForbiddenCopy(value: unknown): boolean {
  // 命中凭证、串口、ROS 控制 topic 或 traceback 时，整个 fixture 不再摘要。
  const payload = encoded(value);
  return FORBIDDEN_COPY.some((token) => payload.includes(token));
}

function safeStringList(value: unknown, limit: number): string[] {
  // audit/evidence refs 限量输出，避免 preview 变成原始日志导出通道。
  if (!Array.isArray(value)) {
    return [];
  }
  return value.slice(0, limit).map((item) => safeRef(item)).filter(Boolean);
}

function eventType(value: unknown): "partial" | "final" {
  // 非 final 统一按 partial 展示，避免未知事件类型扩张 UI 状态机。
  return safeText(value).toLowerCase() === "final" ? "final" : "partial";
}

function sampleAsrEvent(value: unknown): O7VoicePreviewAsrEventSample {
  // ASR sample 只保留 transcript 槽位，不透传原始事件 payload 或音频引用。
  const event = isObject(value) ? value : {};
  return {
    event_type: eventType(event.event_type ?? event.type),
    timestamp_ms: safeNumber(event.timestamp_ms ?? event.t_ms),
    transcript: safeText(event.transcript ?? event.text),
    confidence: safeNumber(event.confidence),
    evidence_ref: safeRef(event.evidence_ref),
  };
}

function latestSlot(events: O7VoicePreviewAsrEventSample[], type: "partial" | "final"): O7VoicePreviewTranscriptSlot {
  // latest slot 从已白名单化的 sample 全量事件中找最后一条，不回看原始对象。
  const latest = [...events].reverse().find((event) => event.event_type === type);
  if (!latest) {
    return {
      text: "",
      timestamp_ms: null,
      confidence: null,
      evidence_ref: type === "partial" ? "missing_asr_partial_transcript_trace" : "missing_asr_final_transcript_trace",
      status: "empty_not_proven",
    };
  }
  return {
    text: latest.transcript,
    timestamp_ms: latest.timestamp_ms,
    confidence: latest.confidence,
    evidence_ref: latest.evidence_ref,
    status: "fixture_summary_only",
  };
}

function mediaPreflightGaps(value: unknown): string[] {
  // media preflight 只表达依赖缺口；即使 fixture 给出字段，也不升级为 pass。
  const media = isObject(value) ? value : {};
  const fixtureGaps = Array.isArray(media.gaps) ? media.gaps.map((item) => safeText(item)).filter(Boolean) : [];
  return Array.from(
    new Set([
      ...fixtureGaps,
      "board_media_preflight_not_collected_by_pc",
      "real_audio_input_not_proven",
      "real_audio_playback_not_proven",
      "rtc_media_smoke_not_proven",
    ]),
  );
}

function blockedResponse(
  status: O7VoicePreviewResponse["input_status"]["status"],
  failureReason: string,
  fixturePath = "",
): O7VoicePreviewResponse {
  // 所有失败都返回同一 schema 和固定 false 开关，调用方不能从 HTTP 状态推断能力。
  const blockedSlot = (type: "partial" | "final"): O7VoicePreviewTranscriptSlot => ({
    text: "",
    timestamp_ms: null,
    confidence: null,
    evidence_ref: type === "partial" ? "missing_asr_partial_transcript_trace" : "missing_asr_final_transcript_trace",
    status: "blocked_not_proven",
  });
  return {
    schema: "trashbot.o7.voice_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "blocked_not_proven",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status,
      failure_reason: failureReason,
    },
    source_fixture_schema: "not_loaded",
    real_voice_api_connected: false,
    real_asr_tts_runtime_connected: false,
    asr_stream_connected: false,
    tts_send_enabled: false,
    speaker_dispatch_enabled: false,
    robot_control_executed: false,
    voice_session: {
      session_id: "not_loaded",
      source: "local_json_fixture",
      evidence_ref: "not_loaded",
      audit_refs: [],
      status: "blocked_not_proven",
    },
    asr_events: {
      event_count: 0,
      sample_limit: SAMPLE_EVENT_LIMIT,
      sample: [],
      latest_partial: blockedSlot("partial"),
      latest_final: blockedSlot("final"),
      status: "blocked_not_proven",
    },
    tts_draft_summary: {
      text: "",
      text_length: 0,
      voice_profile: "not_loaded",
      language: "not_loaded",
      confirmation_required: true,
      status: "blocked_not_proven",
    },
    speaker_dispatch_summary: {
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
      gaps: [failureReason, "fixture_preview_blocked", "board_media_preflight_not_collected_by_pc"],
    },
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      session_evidence_ref: "not_loaded",
      asr_event_refs: [],
      tts_evidence_ref: "not_loaded",
      audit_refs: [],
    },
    blocked_reasons: [failureReason],
    not_proven: [
      "real_voice_api_connected",
      "real_asr_tts_runtime_connected",
      "real_asr_stream",
      "real_asr_partial_transcript",
      "real_asr_final_transcript",
      "real_tts_send",
      "real_tts_playback",
      "real_speaker_dispatch_ack",
      "real_audio_device",
      "delivery_success",
    ],
  };
}

async function loadFixture(filePath: string): Promise<{ payload: JsonObject | null; status: string; reason: string }> {
  // 只读 query 指定的单个 JSON 文件；目录、坏 JSON 和非对象都转换成 blocked 响应。
  if (!filePath.trim()) {
    return { payload: null, status: "not_provided", reason: "fixture_json_not_provided" };
  }
  try {
    const content = await fs.readFile(path.resolve(filePath), "utf8");
    const parsed = JSON.parse(content) as unknown;
    if (!isObject(parsed)) {
      return { payload: null, status: "not_object", reason: "fixture_json_not_object" };
    }
    return { payload: parsed, status: "loaded", reason: "" };
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      return { payload: null, status: "missing", reason: "fixture_json_missing" };
    }
    if (error instanceof SyntaxError) {
      return { payload: null, status: "bad_json", reason: "fixture_json_bad_json" };
    }
    return { payload: null, status: "read_error", reason: "fixture_json_read_error" };
  }
}

export async function buildO7VoicePreview(
  options: O7VoicePreviewOptions = {},
): Promise<O7VoicePreviewResponse> {
  // 主入口按固定顺序关闸：先验证 schema，再拦截任何真实连接、发送或 ACK 成功声明。
  const fixturePath = asText(options.fixtureJson).trim();
  const loaded = await loadFixture(fixturePath);
  if (!loaded.payload) {
    return blockedResponse(loaded.status as O7VoicePreviewResponse["input_status"]["status"], loaded.reason, fixturePath);
  }
  if (loaded.payload.schema !== SUPPORTED_SCHEMA) {
    return blockedResponse("unsupported_schema", "unsupported_fixture_schema", fixturePath);
  }
  if (hasForbiddenCopy(loaded.payload)) {
    return blockedResponse("unsafe_copy", "fixture_contains_unsafe_copy", fixturePath);
  }
  if (hasPattern(loaded.payload, SUCCESS_CLAIM_PATTERNS)) {
    return blockedResponse("success_claim", "fixture_contains_success_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, CONTROL_CLAIM_PATTERNS)) {
    return blockedResponse("control_claim", "fixture_contains_control_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, ASR_CONNECTED_CLAIM_PATTERNS)) {
    return blockedResponse("asr_connected_claim", "fixture_contains_asr_connected_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, TTS_SEND_CLAIM_PATTERNS)) {
    return blockedResponse("tts_send_claim", "fixture_contains_tts_send_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, SPEAKER_DISPATCH_CLAIM_PATTERNS)) {
    return blockedResponse("speaker_dispatch_claim", "fixture_contains_speaker_dispatch_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, REAL_VOICE_CLAIM_PATTERNS)) {
    return blockedResponse("real_voice_claim", "fixture_contains_real_voice_runtime_or_api_claim", fixturePath);
  }
  if (hasPattern(loaded.payload, SPEAKER_ACK_SUCCESS_PATTERNS)) {
    return blockedResponse("speaker_ack_success_claim", "fixture_contains_speaker_ack_success_claim", fixturePath);
  }

  const asrEventsRaw = Array.isArray(loaded.payload.asr_events) ? loaded.payload.asr_events : [];
  const asrEvents = asrEventsRaw.map((event) => sampleAsrEvent(event));
  const ttsDraft = isObject(loaded.payload.tts_draft) ? loaded.payload.tts_draft : {};
  const voiceProfile = isObject(loaded.payload.voice_profile) ? loaded.payload.voice_profile : {};
  const speakerAck = isObject(loaded.payload.speaker_ack) ? loaded.payload.speaker_ack : {};
  const mediaPreflight = isObject(loaded.payload.media_preflight) ? loaded.payload.media_preflight : {};
  const auditRefs = safeStringList(loaded.payload.audit_refs, SAMPLE_REF_LIMIT);
  const ttsText = safeText(ttsDraft.text ?? ttsDraft.transcript ?? "");
  const language = safeText(ttsDraft.language ?? voiceProfile.language ?? "zh-CN") || "zh-CN";
  const profile = safeText(ttsDraft.voice_profile ?? voiceProfile.name ?? voiceProfile.profile ?? "not_provided");
  const evidenceRef = safeRef(loaded.payload.evidence_ref);
  const asrEventRefs = asrEvents.map((event) => event.evidence_ref).filter(Boolean).slice(0, SAMPLE_REF_LIMIT);
  const failureRefs = safeStringList(speakerAck.failure_refs, SAMPLE_REF_LIMIT);

  return {
    schema: "trashbot.o7.voice_preview.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    preview_status: "fixture_preview_ready",
    input_status: {
      fixture_json: safeRef(fixturePath),
      status: "loaded",
      failure_reason: "",
    },
    source_fixture_schema: SUPPORTED_SCHEMA,
    real_voice_api_connected: false,
    real_asr_tts_runtime_connected: false,
    asr_stream_connected: false,
    tts_send_enabled: false,
    speaker_dispatch_enabled: false,
    robot_control_executed: false,
    voice_session: {
      session_id: safeText(loaded.payload.session_id || "not_provided"),
      source: "local_json_fixture",
      evidence_ref: evidenceRef,
      audit_refs: auditRefs,
      status: "fixture_summary_only",
    },
    asr_events: {
      event_count: asrEventsRaw.length,
      sample_limit: SAMPLE_EVENT_LIMIT,
      sample: asrEvents.slice(0, SAMPLE_EVENT_LIMIT),
      latest_partial: latestSlot(asrEvents, "partial"),
      latest_final: latestSlot(asrEvents, "final"),
      status: "fixture_summary_only",
    },
    tts_draft_summary: {
      text: ttsText,
      text_length: ttsText.length,
      voice_profile: profile,
      language,
      confirmation_required: true,
      status: "fixture_draft_only",
    },
    speaker_dispatch_summary: {
      sends_to_robot: false,
      speaker_dispatch_enabled: false,
      ack_status: safeText(speakerAck.ack_status ?? speakerAck.status ?? "blocked_not_proven") || "blocked_not_proven",
      speaker_ack_ref: safeRef(speakerAck.speaker_ack_ref ?? speakerAck.evidence_ref) || "missing_speaker_dispatch_ack",
      failure_event_ref: safeRef(speakerAck.failure_event_ref) || "missing_speaker_failure_event",
      failure_refs: failureRefs,
      status: "blocked_not_proven",
    },
    media_preflight_dependency: {
      required: true,
      source_schema: "trashbot.o7_board_media_preflight.v1",
      status: safeText(mediaPreflight.status ?? "blocked") || "blocked",
      dependency_ref: "board_media_preflight_summary",
      gaps: mediaPreflightGaps(mediaPreflight),
    },
    evidence_refs: {
      fixture_ref: safeRef(fixturePath),
      session_evidence_ref: evidenceRef,
      asr_event_refs: asrEventRefs,
      tts_evidence_ref: safeRef(ttsDraft.evidence_ref),
      audit_refs: auditRefs,
    },
    blocked_reasons: [
      "real_voice_api_not_connected",
      "asr_stream_not_connected",
      "tts_send_disabled",
      "speaker_dispatch_disabled",
      "speaker_ack_not_proven",
      "board_media_preflight_dependency_not_proven",
      "delivery_success_not_proven",
    ],
    not_proven: [
      "real_voice_api_connected",
      "real_asr_tts_runtime_connected",
      "real_asr_stream",
      "real_asr_partial_transcript",
      "real_asr_final_transcript",
      "real_tts_send",
      "real_tts_playback",
      "real_speaker_dispatch_ack",
      "real_speaker_failure_event",
      "real_audio_device",
      "real_rtc_session",
      "delivery_success",
    ],
  };
}
