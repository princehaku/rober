import { PROOF_FLAGS } from "../shared/contracts";
import type { O7RtcSignalingContractProbeResponse } from "../shared/contracts";

const EXPECTED_SCHEMA = "trashbot.o7.rtc_signaling_contract.v1";
const PROBE_SCHEMA = "trashbot.pc_tools_workstation.o7_rtc_signaling_contract_probe.v1";
const REMOTE_ENDPOINT = "/api/o7/rtc-signaling/contract" as const;

const DANGEROUS_TRUE_FIELDS = new Set([
  "network_probe_executed",
  "webrtc_session_created",
  "media_transport_connected",
  "video_track_received",
  "realtime_pose_stream_connected",
  "real_ros2_tf_connected",
  "safe_to_control",
  "sends_commands",
  "reads_hardware",
  "robot_control_executed",
  "delivery_success",
  "primary_actions_enabled",
  "command_dispatch",
  "manual_control",
  "navigate_goal",
  "keyboard_control",
  "hardware_probe",
  "network_probe_from_contract_endpoint",
  "credential_values_exposed",
  "success_claim_allowed",
]);

const DEFAULT_FALSE_FIELDS = [
  "network_probe_executed=false",
  "webrtc_session_created=false",
  "media_transport_connected=false",
  "video_track_received=false",
  "realtime_pose_stream_connected=false",
  "real_ros2_tf_connected=false",
  "safe_to_control=false",
  "sends_commands=false",
  "reads_hardware=false",
  "robot_control_executed=false",
  "delivery_success=false",
] as const;

function failClosed(
  reason: string,
  baseUrl: string,
  extras: Partial<O7RtcSignalingContractProbeResponse> = {},
): O7RtcSignalingContractProbeResponse {
  // probe 失败时仍返回完整 fail-closed 响应，UI 不能把空响应解释成 RTC/视频已接通。
  return {
    schema: PROBE_SCHEMA,
    probe_status: "fail_closed",
    source_base_url: baseUrl || "not_provided",
    remote_endpoint: REMOTE_ENDPOINT,
    remote_schema: extras.remote_schema ?? "not_loaded",
    contract_status: extras.contract_status ?? "not_loaded",
    key_false_fields: extras.key_false_fields ?? [...DEFAULT_FALSE_FIELDS],
    protocol_surface_keys: extras.protocol_surface_keys ?? [],
    required_evidence_refs: extras.required_evidence_refs ?? [],
    blocked_reasons: extras.blocked_reasons ?? [reason],
    not_proven: extras.not_proven ?? ["rtc_signaling_contract_probe_not_proven"],
    dangerous_true_fields: extras.dangerous_true_fields ?? [],
    fail_closed_reason: reason,
    local_loopback_only: true,
    network_probe_executed: false,
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    ...PROOF_FLAGS,
  };
}

function normalizeLoopbackBaseUrl(baseUrl: string): { ok: true; normalized: string } | { ok: false; reason: string } {
  // 只允许 operator 手动输入本机 HTTP 回环，避免 PC 后端被用作外网 SSRF 或生产云探测代理。
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
  // 远端 contract 必须是 object；数组、字符串和 null 都按坏响应 fail closed。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function stringArray(value: unknown): string[] {
  // 只把后端已声明的证据引用或 not_proven 文本转成短字符串数组，不展开原始 payload。
  return Array.isArray(value) ? value.map(String) : [];
}

function scanDangerousTrueFields(value: unknown, path = ""): string[] {
  // 任一危险开关为 true 都说明远端 contract 不再是只读 fail-closed，必须整体降级。
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
  // 缺失字段按 false 摘要，避免旧 contract 被 UI 推断成真实 RTC 能力存在。
  return DEFAULT_FALSE_FIELDS.map((field) => {
    const key = field.replace("=false", "");
    return `${key}=${String(remote[key] === true)}`;
  });
}

function protocolSurfaceKeys(remote: Record<string, unknown>): string[] {
  // UI 只需要知道协议面 key 是否存在，不能透传 signaling/credential 细节或未来 URL payload。
  const surfaces = asRecord(remote.protocol_surfaces);
  return surfaces ? Object.keys(surfaces).sort() : [];
}

function requiredEvidenceRefs(remote: Record<string, unknown>): string[] {
  // 证据引用来源合并为纯字符串列表，不包含 token/auth/URL 或 credential-bearing payload。
  const surfaces = asRecord(remote.protocol_surfaces);
  const observability = asRecord(surfaces?.observability_evidence_refs);
  return Array.from(new Set([
    ...stringArray(observability?.required_refs),
    ...stringArray(remote.next_required_evidence),
  ]));
}

export async function buildO7RtcSignalingContractProbe(baseUrl: string): Promise<O7RtcSignalingContractProbeResponse> {
  const normalized = normalizeLoopbackBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosed(normalized.reason, baseUrl);
  }

  try {
    const response = await fetch(`${normalized.normalized}${REMOTE_ENDPOINT}`, {
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
    const surfaceKeys = protocolSurfaceKeys(remote);
    const evidenceRefs = requiredEvidenceRefs(remote);
    const dangerous = scanDangerousTrueFields(remote);
    const extras: Partial<O7RtcSignalingContractProbeResponse> = {
      remote_schema: remoteSchema,
      contract_status: String(remote.contract_status ?? "not_loaded"),
      key_false_fields: falseFields,
      protocol_surface_keys: surfaceKeys,
      required_evidence_refs: evidenceRefs,
    };
    if (remoteSchema !== EXPECTED_SCHEMA) {
      return failClosed("remote_schema_mismatch", normalized.normalized, extras);
    }
    if (dangerous.length > 0) {
      return failClosed("remote_dangerous_true_field", normalized.normalized, {
        ...extras,
        dangerous_true_fields: dangerous,
        blocked_reasons: dangerous.map((field) => `dangerous_true:${field}`),
      });
    }
    return {
      schema: PROBE_SCHEMA,
      probe_status: "loaded_fail_closed_contract",
      source_base_url: normalized.normalized,
      remote_endpoint: REMOTE_ENDPOINT,
      remote_schema: remoteSchema,
      contract_status: String(remote.contract_status ?? "static_fail_closed_contract"),
      key_false_fields: falseFields,
      protocol_surface_keys: surfaceKeys,
      required_evidence_refs: evidenceRefs,
      blocked_reasons: stringArray(remote.blocked_reasons),
      not_proven: stringArray(remote.not_proven),
      dangerous_true_fields: [],
      fail_closed_reason: "none_remote_contract_is_still_static_fail_closed",
      local_loopback_only: true,
      network_probe_executed: false,
      connects_cloud_production: false,
      sends_commands: false,
      reads_hardware: false,
      ...PROOF_FLAGS,
    };
  } catch {
    return failClosed("remote_fetch_failed", normalized.normalized);
  }
}
