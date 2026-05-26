import { PROOF_FLAGS } from "../shared/contracts";
import type { O7CloudOperatorConsoleProbeResponse } from "../shared/contracts";

const EXPECTED_SCHEMA = "trashbot.o7.operator_console.v1";
const PROBE_SCHEMA = "trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1";

const DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "command_dispatch_enabled",
  "manual_control_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "real_command_api_connected",
  "real_robot_ack_connected",
  "real_cloud_archive_connected",
  "real_annotation_api_connected",
  "real_voice_api_connected",
  "real_asr_tts_runtime_connected",
  "asr_stream_connected",
  "tts_send_enabled",
  "speaker_dispatch_enabled",
  "playback_available",
  "submit_enabled",
  "rollback_enabled",
  "dataset_export_available",
  "robot_control_executed",
  "success_claim_allowed",
]);

const KEY_FALSE_FIELDS = [
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "command_dispatch_enabled",
  "manual_control_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "real_command_api_connected",
  "real_robot_ack_connected",
  "tts_send_enabled",
  "submit_enabled",
  "playback_available",
] as const;

function failClosed(reason: string, baseUrl: string, extras: Partial<O7CloudOperatorConsoleProbeResponse> = {}): O7CloudOperatorConsoleProbeResponse {
  // probe 失败也返回结构化契约，UI 不能把 HTTP 失败解释成云端或机器人能力在线。
  return {
    schema: PROBE_SCHEMA,
    probe_status: "fail_closed",
    source_base_url: baseUrl || "not_provided",
    remote_endpoint: "/api/o7/operator-console",
    remote_schema: extras.remote_schema ?? "not_loaded",
    cloud_api_status: extras.cloud_api_status ?? "not_loaded",
    operator_mode: extras.operator_mode ?? "observe_only",
    kr_ids: extras.kr_ids ?? [],
    key_false_fields: extras.key_false_fields ?? KEY_FALSE_FIELDS.map((field) => `${field}=false`),
    blocked_reasons: extras.blocked_reasons ?? [reason],
    not_proven: extras.not_proven ?? ["cloud_operator_console_probe_not_proven"],
    fail_closed_reason: reason,
    local_loopback_only: true,
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    ...PROOF_FLAGS,
  };
}

function normalizeLoopbackBaseUrl(baseUrl: string): { ok: true; normalized: string } | { ok: false; reason: string } {
  // 只允许 operator 明确输入本机回环 HTTP URL，避免 PC 后端变成 SSRF 代理。
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    return { ok: false, reason: "baseUrl_not_provided" };
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return { ok: false, reason: "baseUrl_invalid_url" };
  }
  if (parsed.protocol !== "http:") {
    return { ok: false, reason: "baseUrl_protocol_not_allowed" };
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    return { ok: false, reason: "baseUrl_must_not_include_credentials_query_or_hash" };
  }
  if (!["127.0.0.1", "localhost", "[::1]"].includes(parsed.host.replace(/:\d+$/, "")) && parsed.hostname !== "::1") {
    return { ok: false, reason: "baseUrl_must_be_local_loopback" };
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  return { ok: true, normalized: parsed.toString().replace(/\/$/, "") };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // 远端响应必须是 object；数组、字符串和 null 都按 schema 错误 fail closed。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function stringArray(value: unknown): string[] {
  // probe 只展示远端已脱敏的数组字段，坏类型收敛为空数组。
  return Array.isArray(value) ? value.map(String) : [];
}

function scanDangerousTrueFields(value: unknown, path = ""): string[] {
  // 递归扫描常见危险开关，只要远端把其中任一字段置 true 就整包 fail closed。
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanDangerousTrueFields(item, `${path}[${index}]`));
  }
  return Object.entries(value as Record<string, unknown>).flatMap(([key, nested]) => {
    const currentPath = path ? `${path}.${key}` : key;
    const current = DANGEROUS_TRUE_FIELDS.has(key) && nested === true ? [currentPath] : [];
    return current.concat(scanDangerousTrueFields(nested, currentPath));
  });
}

function keyFalseFields(remote: Record<string, unknown>): string[] {
  // 字段缺失也按 false 展示，probe 不因缺少未来字段而推断能力已接通。
  const manual = asRecord(remote.manual_control_policy);
  const safeCommand = asRecord(remote.safe_command_snapshot);
  const voice = asRecord(remote.voice_asr_tts_snapshot);
  const labeling = asRecord(remote.labeling_queue_snapshot);
  const route = asRecord(remote.route_replay_snapshot);
  return [
    `safe_to_control=${String(remote.safe_to_control === true)}`,
    `delivery_success=${String(remote.delivery_success === true)}`,
    `primary_actions_enabled=${String(remote.primary_actions_enabled === true)}`,
    `command_dispatch_enabled=${String(manual?.command_dispatch_enabled === true || safeCommand?.command_dispatch_enabled === true)}`,
    `manual_control_enabled=${String(manual?.manual_control_enabled === true || safeCommand?.manual_control_enabled === true)}`,
    `navigate_goal_enabled=${String(manual?.navigate_goal_enabled === true || safeCommand?.navigate_goal_enabled === true)}`,
    `keyboard_control_enabled=${String(manual?.keyboard_control_enabled === true || safeCommand?.keyboard_control_enabled === true)}`,
    `real_command_api_connected=${String(manual?.real_command_api_connected === true || safeCommand?.real_command_api_connected === true)}`,
    `real_robot_ack_connected=${String(manual?.real_robot_ack_connected === true || safeCommand?.real_robot_ack_connected === true)}`,
    `tts_send_enabled=${String(voice?.tts_send_enabled === true)}`,
    `submit_enabled=${String(labeling?.submit_enabled === true)}`,
    `playback_available=${String(route?.playback_available === true)}`,
  ];
}

export async function buildO7CloudOperatorConsoleProbe(baseUrl: string): Promise<O7CloudOperatorConsoleProbeResponse> {
  const normalized = normalizeLoopbackBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosed(normalized.reason, baseUrl);
  }

  try {
    const response = await fetch(`${normalized.normalized}/api/o7/operator-console`, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(2000),
    });
    if (!response.ok) {
      return failClosed(`remote_http_${response.status}`, normalized.normalized);
    }
    const remote = asRecord(await response.json());
    if (!remote) {
      return failClosed("remote_json_not_object", normalized.normalized);
    }
    const remoteSchema = String(remote.schema ?? "not_loaded");
    const falseFields = keyFalseFields(remote);
    const dangerous = scanDangerousTrueFields(remote);
    if (remoteSchema !== EXPECTED_SCHEMA) {
      return failClosed("remote_schema_mismatch", normalized.normalized, { remote_schema: remoteSchema, key_false_fields: falseFields });
    }
    if (dangerous.length > 0) {
      return failClosed("remote_dangerous_true_field", normalized.normalized, {
        remote_schema: remoteSchema,
        key_false_fields: falseFields,
        blocked_reasons: dangerous.map((field) => `dangerous_true:${field}`),
      });
    }
    return {
      schema: PROBE_SCHEMA,
      probe_status: "loaded_fail_closed_contract",
      source_base_url: normalized.normalized,
      remote_endpoint: "/api/o7/operator-console",
      remote_schema: remoteSchema,
      cloud_api_status: String(remote.cloud_api_status ?? "not_loaded"),
      operator_mode: String(remote.operator_mode ?? "observe_only"),
      kr_ids: stringArray(remote.kr_views).length
        ? (remote.kr_views as Array<Record<string, unknown>>).map((view) => String(view.id ?? "unknown"))
        : stringArray(remote.kr_contracts),
      key_false_fields: falseFields,
      blocked_reasons: stringArray(remote.blocked_reasons),
      not_proven: stringArray(remote.not_proven),
      fail_closed_reason: "none_remote_contract_is_still_observe_only",
      local_loopback_only: true,
      connects_cloud_production: false,
      sends_commands: false,
      reads_hardware: false,
      ...PROOF_FLAGS,
    };
  } catch {
    return failClosed("remote_fetch_failed", normalized.normalized);
  }
}
