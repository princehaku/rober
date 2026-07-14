import { promises as fs } from "node:fs";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type { O7VoiceRuntimePreflightResult } from "../shared/contracts";

type JsonObject = Record<string, unknown>;

export interface O7VoiceRuntimePreflightOptions {
  configJson?: string;
  mode?: string;
  env?: NodeJS.ProcessEnv;
}

const CONFIG_SCHEMA = "trashbot.pc_tools_workstation.o7_voice_runtime_preflight_config.v1" as const;
const PROOF_BOUNDARY = "software_proof_o7_voice_runtime_preflight_only" as const;
const SAFE_MODES = new Set(["local_stub", "offline_stub", "disabled_local"]);

const DANGEROUS_TRUE_FIELDS = [
  "real_voice_api_connected",
  "real_asr_tts_runtime_connected",
  "tts_send_enabled",
  "speaker_dispatch_enabled",
  "safe_to_control",
  "delivery_success",
  "robot_control_executed",
  "connects_cloud_production",
  "microphone_opened",
  "speaker_playback_opened",
  "reads_audio_device",
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
  // 所有 query/env/config 字段都先转成短文本，避免 undefined 被误当配置成功。
  return value === null || value === undefined ? "" : String(value).trim();
}

function pathRef(value: unknown): string {
  // 响应只展示 basename；preflight 不把本机绝对路径泄露给浏览器或测试日志。
  const raw = text(value);
  if (!raw) {
    return "not_configured";
  }
  if (path.isAbsolute(raw) || raw.includes("/") || raw.includes("\\")) {
    return `file:${path.basename(raw)}`;
  }
  return raw;
}

function encoded(value: unknown): string {
  // fail-closed 扫描使用 JSON 文本，覆盖嵌套字段和未知扩展字段。
  try {
    return JSON.stringify(value);
  } catch {
    return "{}";
  }
}

function dangerousTrueFields(value: unknown): string[] {
  // 只要 config 自称真实连接、播放、控制或送达成功，本轮 preflight 必须失败。
  const raw = encoded(value);
  const payload = isObject(value) ? value : {};
  return DANGEROUS_TRUE_FIELDS.filter((field) =>
    payload[field] === true || new RegExp(`"${field}"\\s*:\\s*true`).test(raw),
  );
}

function containsUnsafeCopy(value: unknown): boolean {
  // preflight 不允许 URL、凭证、音频 payload、设备路径、ROS 控制或硬件字样进入安全配置。
  const payload = encoded(value);
  return UNSAFE_COPY_PATTERNS.some((pattern) => pattern.test(payload));
}

function normalizeMode(value: unknown): O7VoiceRuntimePreflightResult["runtime_mode"] {
  // 只有本地/离线/禁用态配置能进入 ready；其它 mode 不做宽松映射。
  const mode = text(value);
  return SAFE_MODES.has(mode) ? mode as O7VoiceRuntimePreflightResult["runtime_mode"] : "not_configured";
}

function baseResponse(
  overrides: Partial<O7VoiceRuntimePreflightResult>,
): O7VoiceRuntimePreflightResult {
  // 固定 false 字段在一处维护，避免 UI/API/测试出现一处漏写后被误读成真实 runtime。
  return {
    schema: "trashbot.pc_tools_workstation.o7_voice_runtime_preflight_result.v1",
    schema_version: 1,
    ...PROOF_FLAGS,
    endpoint: "/api/o7/voice-runtime/preflight",
    preflight_status: "blocked_missing_voice_runtime_config",
    proof_boundary: PROOF_BOUNDARY,
    config_source: "not_configured",
    config_schema: "not_loaded",
    config_path_ref: "not_configured",
    runtime_mode: "not_configured",
    runtime_configured: false,
    config_checks: {
      config_loaded: false,
      schema_supported: false,
      local_offline_mode: false,
      no_network_access: true,
      no_device_access: true,
      no_audio_dispatch: true,
      dangerous_true_claims: [],
      unsafe_copy_detected: false,
      status: "blocked",
    },
    real_voice_api_connected: false,
    real_asr_tts_runtime_connected: false,
    asr_stream_connected: false,
    tts_send_enabled: false,
    speaker_dispatch_enabled: false,
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
      "microphone_input_not_opened",
      "speaker_output_not_opened",
      "real_tts_send_not_proven",
      "real_speaker_ack_not_proven",
      "delivery_success=false",
      "safe_to_control=false",
    ],
    next_required_evidence: [
      "authorized_real_voice_runtime_smoke",
      "same_task_voice_runtime_trace",
      "real_microphone_and_speaker_preflight",
      "real_speaker_ack_for_selected_task",
    ],
    fail_closed_reason: "none",
    ...overrides,
  };
}

function failClosed(
  reason: string,
  configSource: O7VoiceRuntimePreflightResult["config_source"],
  configPath: string,
  payload: unknown = {},
): O7VoiceRuntimePreflightResult {
  // fail_closed 仍返回完整 schema 和固定 false 字段，让前端不需要靠异常分支保安全。
  const claims = dangerousTrueFields(payload);
  return baseResponse({
    preflight_status: "fail_closed",
    config_source: configSource,
    config_path_ref: pathRef(configPath),
    config_checks: {
      config_loaded: configSource !== "not_configured",
      schema_supported: isObject(payload) && payload.schema === CONFIG_SCHEMA,
      local_offline_mode: false,
      no_network_access: true,
      no_device_access: true,
      no_audio_dispatch: true,
      dangerous_true_claims: claims,
      unsafe_copy_detected: containsUnsafeCopy(payload) || containsUnsafeCopy(configPath),
      status: "blocked",
    },
    blocked_reasons: [reason],
    fail_closed_reason: reason,
  });
}

async function loadConfig(configJson: string): Promise<{ payload: JsonObject | null; reason: string }> {
  // 只读取显式指定的 JSON config；URL、设备路径和空路径不会进入 fs.readFile。
  const rawPath = text(configJson);
  if (!rawPath) {
    return { payload: null, reason: "config_json_not_provided" };
  }
  if (containsUnsafeCopy(rawPath)) {
    return { payload: null, reason: "config_json_path_unsafe" };
  }
  try {
    const parsed = JSON.parse(await fs.readFile(path.resolve(rawPath), "utf8")) as unknown;
    if (!isObject(parsed)) {
      return { payload: null, reason: "config_json_not_object" };
    }
    return { payload: parsed, reason: "" };
  } catch (error) {
    if (error instanceof SyntaxError) {
      return { payload: null, reason: "config_json_bad_json" };
    }
    const code = (error as NodeJS.ErrnoException).code;
    return { payload: null, reason: code === "ENOENT" ? "config_json_missing" : "config_json_read_error" };
  }
}

function responseFromMode(
  modeText: string,
  configSource: O7VoiceRuntimePreflightResult["config_source"],
): O7VoiceRuntimePreflightResult {
  // mode 分支用于 CI 或离线开发：只证明“配置检查可执行”，不是 runtime 已连接。
  const runtimeMode = normalizeMode(modeText);
  if (runtimeMode === "not_configured") {
    return failClosed("voice_runtime_mode_not_safe_local_or_offline", configSource, "", { runtime_mode: modeText });
  }
  return baseResponse({
    preflight_status: "ready_for_configured_runtime_check_only",
    config_source: configSource,
    config_schema: "not_loaded",
    runtime_mode: runtimeMode,
    runtime_configured: true,
    config_checks: {
      config_loaded: true,
      schema_supported: true,
      local_offline_mode: true,
      no_network_access: true,
      no_device_access: true,
      no_audio_dispatch: true,
      dangerous_true_claims: [],
      unsafe_copy_detected: false,
      status: "ready",
    },
    blocked_reasons: ["real_voice_runtime_not_connected", "configured_check_only"],
  });
}

function responseFromConfig(
  configJson: string,
  payload: JsonObject,
  configSource: O7VoiceRuntimePreflightResult["config_source"],
): O7VoiceRuntimePreflightResult {
  // config JSON 只承认本地 schema + local/offline mode + runtime_configured=true。
  if (payload.schema !== CONFIG_SCHEMA) {
    return failClosed("voice_runtime_config_schema_unsupported", configSource, configJson, payload);
  }
  const claims = dangerousTrueFields(payload);
  if (claims.length > 0) {
    return failClosed(`dangerous_true_fields:${claims.join(",")}`, configSource, configJson, payload);
  }
  if (containsUnsafeCopy(payload)) {
    return failClosed("voice_runtime_config_contains_unsafe_copy", configSource, configJson, payload);
  }
  const runtimeMode = normalizeMode(payload.runtime_mode);
  if (runtimeMode === "not_configured") {
    return failClosed("voice_runtime_mode_not_safe_local_or_offline", configSource, configJson, payload);
  }
  if (payload.runtime_configured !== true) {
    return baseResponse({
      preflight_status: "blocked_voice_runtime_config_not_ready",
      config_source: configSource,
      config_schema: CONFIG_SCHEMA,
      config_path_ref: pathRef(configJson),
      runtime_mode: runtimeMode,
      runtime_configured: false,
      config_checks: {
        config_loaded: true,
        schema_supported: true,
        local_offline_mode: true,
        no_network_access: true,
        no_device_access: true,
        no_audio_dispatch: true,
        dangerous_true_claims: [],
        unsafe_copy_detected: false,
        status: "blocked",
      },
      blocked_reasons: ["runtime_configured_false"],
    });
  }
  return baseResponse({
    preflight_status: "ready_for_configured_runtime_check_only",
    config_source: configSource,
    config_schema: CONFIG_SCHEMA,
    config_path_ref: pathRef(configJson),
    runtime_mode: runtimeMode,
    runtime_configured: true,
    config_checks: {
      config_loaded: true,
      schema_supported: true,
      local_offline_mode: true,
      no_network_access: true,
      no_device_access: true,
      no_audio_dispatch: true,
      dangerous_true_claims: [],
      unsafe_copy_detected: false,
      status: "ready",
    },
    blocked_reasons: ["real_voice_runtime_not_connected", "configured_check_only"],
  });
}

export async function buildO7VoiceRuntimePreflight(
  options: O7VoiceRuntimePreflightOptions = {},
): Promise<O7VoiceRuntimePreflightResult> {
  // 优先 query config，其次 env config，再其次 query/env mode；全部都不访问网络或音频设备。
  const env = options.env ?? process.env;
  const queryConfig = text(options.configJson);
  const envConfig = text(env.O7_VOICE_RUNTIME_PREFLIGHT_CONFIG_JSON);
  const configJson = queryConfig || envConfig;
  if (configJson) {
    const source = queryConfig ? "query_config_json" : "env_config_json";
    const loaded = await loadConfig(configJson);
    if (!loaded.payload) {
      return failClosed(loaded.reason, source, configJson, {});
    }
    return responseFromConfig(configJson, loaded.payload, source);
  }
  const queryMode = text(options.mode);
  const envMode = text(env.O7_VOICE_RUNTIME_PREFLIGHT_MODE);
  if (queryMode || envMode) {
    return responseFromMode(queryMode || envMode, queryMode ? "query_mode" : "env_mode");
  }
  return baseResponse({});
}
