import { PROOF_FLAGS } from "../shared/contracts";
import type { O5O6CloudRelayHealthObjectiveSummary, O5O6CloudRelayHealthResponse } from "../shared/contracts";

const RESPONSE_SCHEMA = "trashbot.pc_tools_workstation.o5_o6_cloud_relay_health.v1";
const O5_ENDPOINT = "/api/o5/readiness/health" as const;
const O6_ENDPOINT = "/api/o6/archive/health" as const;
const BASE_URL_ENV = "ROBER_CLOUD_RELAY_BASE_URL";
const TOKEN_ENVS = ["TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN", "ROBER_CLOUD_RELAY_BEARER_TOKEN"] as const;

const DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "sends_commands",
  "robot_control_executed",
  "delivery_success",
  "primary_actions_enabled",
  "production_ready",
  "production_db_connected",
  "connects_cloud_production",
  "reads_hardware",
  "real_oss_upload",
  "real_inference_model_runtime",
]);

const SENSITIVE_KEY_PATTERN = /(authorization|bearer|token|secret|password|credential|state_path|db_url|queue_url|(^|[_-])(ak|sk)($|[_-])|traceback|serial|uart|wave_rover|ros_topic|cmd_vel)/i;
const SENSITIVE_TEXT_PATTERN = /(authorization|bearer\s+|token=|password=|secret=|traceback|\/cmd_vel|\/dev\/|wave rover|wave_rover|serial|uart|ros topic|oss:\/\/|mongodb:\/\/|redis:\/\/|postgres:\/\/|mysql:\/\/)/i;

function baseObjective(
  objective: "O5" | "O6",
  endpoint: typeof O5_ENDPOINT | typeof O6_ENDPOINT,
  reason: string,
): O5O6CloudRelayHealthObjectiveSummary {
  // 每个 Objective 都先构造完整 fail-closed 摘要，后续只覆盖白名单字段。
  return {
    objective,
    remote_endpoint: endpoint,
    remote_schema: "not_loaded",
    http_status: null,
    capability: objective === "O5" ? "o5_readiness_live_health" : "o6_archive_live_health",
    status: "not_loaded",
    production_ready: false,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    delivery_success: false,
    blocked_count: 1,
    warning_count: 0,
    pass_count: 0,
    blocked_or_warning_count: 1,
    next_required_evidence: [],
    blocked_reasons: [reason],
    not_proven: [`${objective.toLowerCase()}_cloud_relay_health_not_proven`],
    phone_safe_summary: `${objective} relay health not loaded; ${reason}.`,
  };
}

function failClosed(
  reason: string,
  baseUrl: string,
  extras: Partial<O5O6CloudRelayHealthResponse> = {},
): O5O6CloudRelayHealthResponse {
  // fail-closed 也返回固定 shape，UI 不需要从异常推断状态。
  const o5 = extras.o5 ?? baseObjective("O5", O5_ENDPOINT, reason);
  const o6 = extras.o6 ?? baseObjective("O6", O6_ENDPOINT, reason);
  const disallowed = reason === "blocked_disallowed_base_url";
  return {
    schema: RESPONSE_SCHEMA,
    probe_status: extras.probe_status ?? (reason === "baseUrl_not_configured" ? "not_configured" : disallowed ? "blocked_disallowed_base_url" : "blocked"),
    source_base_url: disallowed ? "blocked_disallowed_base_url" : baseUrl || "not_configured",
    base_url_source: extras.base_url_source ?? "not_configured",
    token_status: extras.token_status ?? "absent",
    remote_endpoints: [O5_ENDPOINT, O6_ENDPOINT],
    o5,
    o6,
    summary: summarize(o5, o6),
    config_policy: configPolicy(),
    key_false_fields: fixedFalseFields(),
    dangerous_true_fields: extras.dangerous_true_fields ?? [],
    redaction_status: extras.redaction_status ?? "passed",
    fail_closed_reason: reason,
    blocked_reasons: extras.blocked_reasons ?? [reason],
    not_proven: extras.not_proven ?? ["real_public_cloud_not_proven", "real_4g_not_proven", "production_db_queue_not_proven"],
    connects_cloud_production: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
    ...PROOF_FLAGS,
  };
}

function configPolicy(): O5O6CloudRelayHealthResponse["config_policy"] {
  // 环境变量名写进响应，便于 operator 配置，但不展示变量值。
  return {
    default_public_probe: false,
    local_loopback_allowed: true,
    private_lan_allowed: true,
    base_url_env: BASE_URL_ENV,
    token_envs: [...TOKEN_ENVS],
  };
}

function fixedFalseFields(): string[] {
  // UI 使用这些字段作为醒目护栏，避免 live health 被误读成控制台。
  return [
    "safe_to_control=false",
    "sends_commands=false",
    "robot_control_executed=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
    "production_ready=false",
  ];
}

function summarize(
  o5: O5O6CloudRelayHealthObjectiveSummary,
  o6: O5O6CloudRelayHealthObjectiveSummary,
): O5O6CloudRelayHealthResponse["summary"] {
  const loaded = [o5, o6].filter((item) => item.remote_schema !== "not_loaded").length;
  return {
    loaded_count: loaded,
    blocked_count: o5.blocked_count + o6.blocked_count,
    warning_count: o5.warning_count + o6.warning_count,
    pass_count: o5.pass_count + o6.pass_count,
    blocked_or_warning_count: o5.blocked_or_warning_count + o6.blocked_or_warning_count,
    production_ready: false,
    archive_api_status: o6.status,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

function configValue(
  queryValue: string,
  envName: string,
  env: NodeJS.ProcessEnv,
): { value: string; source: "query" | "env" | "not_configured" } {
  // query 显式值优先，方便本地 smoke；未给 query 时只读 env，不做默认公网探测。
  const trimmedQuery = queryValue.trim();
  if (trimmedQuery) {
    return { value: trimmedQuery, source: "query" };
  }
  const envValue = (env[envName] ?? "").trim();
  return envValue ? { value: envValue, source: "env" } : { value: "", source: "not_configured" };
}

function tokenValue(env: NodeJS.ProcessEnv): string {
  // bearer 只能来自环境变量，不能从 query 或 URL 读取，避免浏览器历史和日志泄漏凭证。
  for (const envName of TOKEN_ENVS) {
    const value = (env[envName] ?? "").trim();
    if (value) {
      return value;
    }
  }
  return "";
}

function isPrivateLanHost(hostname: string): boolean {
  // 只做字面 host 白名单，不解析 DNS，避免把公网域名解析到内网后绕过审计。
  const host = hostname.toLowerCase();
  if (host === "localhost" || host === "::1" || host === "[::1]") {
    return true;
  }
  const parts = host.split(".").map((part) => Number(part));
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part) || part < 0 || part > 255)) {
    return false;
  }
  const [a, b] = parts as [number, number, number, number];
  return a === 127 || a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
}

function normalizeBaseUrl(baseUrl: string): { ok: true; normalized: string } | { ok: false; reason: string } {
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    return { ok: false, reason: "baseUrl_not_configured" };
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return { ok: false, reason: "baseUrl_invalid_url" };
  }
  if (!["http:", "https:"].includes(parsed.protocol)) {
    return { ok: false, reason: "baseUrl_protocol_not_allowed" };
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    return { ok: false, reason: "baseUrl_must_not_include_credentials_query_or_hash" };
  }
  if (!isPrivateLanHost(parsed.hostname)) {
    return { ok: false, reason: "blocked_disallowed_base_url" };
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  return { ok: true, normalized: parsed.toString().replace(/\/$/, "") };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // 远端 health 必须是 object；数组或标量会被当作 contract 错误。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function numberField(record: Record<string, unknown>, key: string): number {
  // 计数字段只接受有限 number；字符串数字不自动提升，避免坏 contract 被误读。
  const value = record[key];
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function safeText(value: unknown, fallback: string): string {
  // 只保留短枚举/短 copy，命中敏感模式时直接替换成 redacted。
  const text = typeof value === "string" ? value.replace(/\s+/g, " ").slice(0, 120) : fallback;
  return SENSITIVE_TEXT_PATTERN.test(text) ? "redacted_sensitive_value" : text;
}

function safeStringArray(value: unknown, limit = 6): string[] {
  // 数组字段限长并逐项脱敏，避免把远端 details 或路径整包透传。
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => safeText(item, "unknown")).filter((item) => item !== "redacted_sensitive_value").slice(0, limit);
}

function scanDangerousTrueFields(value: unknown, path = ""): string[] {
  // 递归扫描控制/生产相关 true 字段，远端一旦越界，聚合响应必须 blocked。
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

function scanSensitiveMarkers(value: unknown, path = ""): string[] {
  // 响应只做安全摘要；远端 payload 出现敏感 key/text 时不透传原值，只返回 marker path。
  if (!value || typeof value !== "object") {
    return typeof value === "string" && SENSITIVE_TEXT_PATTERN.test(value) ? [path || "payload"] : [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanSensitiveMarkers(item, `${path}[${index}]`));
  }
  return Object.entries(value as Record<string, unknown>).flatMap(([key, nested]) => {
    const currentPath = path ? `${path}.${key}` : key;
    const keyHit = SENSITIVE_KEY_PATTERN.test(key) ? [currentPath] : [];
    return keyHit.concat(scanSensitiveMarkers(nested, currentPath));
  });
}

function o5Summary(remote: Record<string, unknown>, httpStatus: number): O5O6CloudRelayHealthObjectiveSummary {
  const blocked = numberField(remote, "blocked_count");
  const warning = numberField(remote, "warning_count");
  const pass = numberField(remote, "pass_count");
  return {
    objective: "O5",
    remote_endpoint: O5_ENDPOINT,
    remote_schema: safeText(remote.schema, "not_loaded"),
    http_status: httpStatus,
    capability: safeText(remote.capability, "o5_readiness_live_health"),
    status: safeText(remote.overall_status, "blocked"),
    production_ready: false,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    delivery_success: false,
    blocked_count: blocked,
    warning_count: warning,
    pass_count: pass,
    blocked_or_warning_count: blocked + warning,
    next_required_evidence: safeStringArray(remote.next_required_evidence),
    blocked_reasons: safeStringArray(remote.real_material_gaps),
    not_proven: safeStringArray(remote.not_proven),
    phone_safe_summary: safeText(remote.safe_summary, "O5 readiness live health loaded; production_ready=false."),
  };
}

function o6Summary(remote: Record<string, unknown>, httpStatus: number): O5O6CloudRelayHealthObjectiveSummary {
  const archiveStatus = safeText(remote.archive_api_status, "blocked_not_loaded");
  const blocked = archiveStatus === "ready" || archiveStatus === "empty" ? 0 : 1;
  return {
    objective: "O6",
    remote_endpoint: O6_ENDPOINT,
    remote_schema: safeText(remote.schema, "not_loaded"),
    http_status: httpStatus,
    capability: safeText(remote.capability, "o6_archive_live_health"),
    status: archiveStatus,
    production_ready: false,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    delivery_success: false,
    blocked_count: blocked,
    warning_count: archiveStatus === "empty" ? 1 : 0,
    pass_count: archiveStatus === "ready" ? 1 : 0,
    blocked_or_warning_count: blocked + (archiveStatus === "empty" ? 1 : 0),
    next_required_evidence: safeStringArray(remote.next_required_evidence),
    blocked_reasons: safeStringArray(remote.error ? [remote.error] : []),
    not_proven: safeStringArray(remote.not_proven),
    phone_safe_summary: `O6 archive_api_status=${archiveStatus}; task_count=${numberField(remote, "task_count")}; event_count=${numberField(remote, "event_count")}.`,
  };
}

async function fetchHealth(
  baseUrl: string,
  endpoint: typeof O5_ENDPOINT | typeof O6_ENDPOINT,
  token: string,
): Promise<{ status: number; body: Record<string, unknown> | null; badJson: boolean }> {
  // 这里只能 GET 固定 health endpoint；不会访问 /robots/*、不会 POST，也不会携带浏览器 token。
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${baseUrl}${endpoint}`, {
    method: "GET",
    headers,
    signal: AbortSignal.timeout(2500),
  });
  const json = await response.json().catch(() => undefined);
  const body = asRecord(json);
  return { status: response.status, body, badJson: body === null };
}

export async function buildO5O6CloudRelayHealth(options: { baseUrl?: string; env?: NodeJS.ProcessEnv } = {}): Promise<O5O6CloudRelayHealthResponse> {
  const env = options.env ?? process.env;
  const baseConfig = configValue(options.baseUrl ?? "", BASE_URL_ENV, env);
  const token = tokenValue(env);
  const normalized = normalizeBaseUrl(baseConfig.value);
  if (!normalized.ok) {
    return failClosed(normalized.reason, "", { base_url_source: baseConfig.source, token_status: token ? "present" : "absent" });
  }

  try {
    const [o5Remote, o6Remote] = await Promise.all([
      fetchHealth(normalized.normalized, O5_ENDPOINT, token),
      fetchHealth(normalized.normalized, O6_ENDPOINT, token),
    ]);
    const o5 = o5Remote.body ? o5Summary(o5Remote.body, o5Remote.status) : baseObjective("O5", O5_ENDPOINT, o5Remote.badJson ? "remote_bad_json" : `remote_http_${o5Remote.status}`);
    const o6 = o6Remote.body ? o6Summary(o6Remote.body, o6Remote.status) : baseObjective("O6", O6_ENDPOINT, o6Remote.badJson ? "remote_bad_json" : `remote_http_${o6Remote.status}`);
    const dangerous = [
      ...scanDangerousTrueFields(o5Remote.body).map((field) => `o5.${field}`),
      ...scanDangerousTrueFields(o6Remote.body).map((field) => `o6.${field}`),
    ];
    const sensitive = [
      ...scanSensitiveMarkers(o5Remote.body).map((field) => `o5.${field}`),
      ...scanSensitiveMarkers(o6Remote.body).map((field) => `o6.${field}`),
    ];
    const schemaOk = o5.remote_schema === "trashbot.o5.readiness_health.v1" && o6.remote_schema === "trashbot.o6.archive_health.v1";
    const httpOk = o5Remote.status >= 200 && o5Remote.status < 300 && o6Remote.status >= 200 && o6Remote.status < 300;
    const jsonOk = !o5Remote.badJson && !o6Remote.badJson;
    const blockedReasons = [
      ...(jsonOk ? [] : ["remote_bad_json"]),
      ...(schemaOk ? [] : ["remote_schema_mismatch"]),
      ...(httpOk ? [] : [`remote_http_status_o5_${o5Remote.status}_o6_${o6Remote.status}`]),
      ...dangerous.map((field) => `dangerous_true:${field}`),
      ...sensitive.map((field) => `sensitive_marker:${field}`),
    ];
    if (blockedReasons.length > 0) {
      const primaryBlockedReason = blockedReasons[0] ?? "remote_contract_blocked";
      return failClosed(primaryBlockedReason, normalized.normalized, {
        probe_status: o5.remote_schema !== "not_loaded" || o6.remote_schema !== "not_loaded" ? "partial_fail_closed_contract" : "blocked",
        base_url_source: baseConfig.source,
        token_status: token ? "present" : "absent",
        o5,
        o6,
        dangerous_true_fields: dangerous,
        redaction_status: sensitive.length > 0 ? "blocked" : "passed",
        blocked_reasons: blockedReasons,
      });
    }
    return {
      schema: RESPONSE_SCHEMA,
      probe_status: "loaded_fail_closed_contract",
      source_base_url: normalized.normalized,
      base_url_source: baseConfig.source,
      token_status: token ? "present" : "absent",
      remote_endpoints: [O5_ENDPOINT, O6_ENDPOINT],
      o5,
      o6,
      summary: summarize(o5, o6),
      config_policy: configPolicy(),
      key_false_fields: fixedFalseFields(),
      dangerous_true_fields: [],
      redaction_status: "passed",
      fail_closed_reason: "none_remote_contracts_are_health_only",
      blocked_reasons: [...o5.blocked_reasons, ...o6.blocked_reasons].slice(0, 10),
      not_proven: Array.from(new Set([...o5.not_proven, ...o6.not_proven, "real_public_cloud_not_proven", "real_4g_not_proven"])).slice(0, 12),
      connects_cloud_production: false,
      sends_commands: false,
      reads_hardware: false,
      robot_control_executed: false,
      ...PROOF_FLAGS,
    };
  } catch {
    return failClosed("remote_fetch_failed", normalized.normalized, {
      base_url_source: baseConfig.source,
      token_status: token ? "present" : "absent",
    });
  }
}
