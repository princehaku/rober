import fs from "node:fs/promises";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O5O6ExternalProbeArtifactEndpointSummary,
  O5O6ExternalProbeArtifactResponse,
} from "../shared/contracts";
import { WORKSTATION_RUNTIME_ROOT } from "./paths";

const RESPONSE_SCHEMA = "trashbot.pc_tools_workstation.o5_o6_external_probe_artifact.v1";
const PROBE_SCHEMA = "trashbot.o5_o6.external_live_probe.v1";
const ARTIFACT_ENV = "ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT";
const DEFAULT_ARTIFACT_NAME = "o5-o6-external-live-probe.json";

const SENSITIVE_TEXT_PATTERN =
  /(authorization|bearer\s+|token=|baseurl=|password=|secret=|traceback|\/cmd_vel|\/dev\/|\/mnt\/|\/tmp\/|[a-z]:\\|oss:\/\/|mongodb:\/\/|redis:\/\/|postgres:\/\/|mysql:\/\/|https?:\/\/|https?%3a%2f%2f)/i;
const FIXED_SAFETY_POLICY = {
  method_allowlist: ["GET"],
  endpoint_allowlist: ["/api/o5/readiness/health", "/api/o6/archive/health", "/api/o5-o6/cloud-relay-health"],
  forbidden_paths: ["/robots/*", "/cmd_vel"],
  no_post: true,
  no_robot_control: true,
  no_hardware_read: true,
};

type ArtifactSource = "env_configured" | "workstation_runtime" | "not_configured";

function safeText(value: unknown, fallback = "unknown"): string {
  // artifact 可能来自远端 stdout 落盘；所有展示文本先截断再做敏感 marker 过滤。
  const text = typeof value === "string" ? value.replace(/\s+/g, " ").slice(0, 140) : fallback;
  return SENSITIVE_TEXT_PATTERN.test(text) ? "redacted_sensitive_value" : text;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // probe artifact 必须是 JSON object；数组/标量不能承载安全契约。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function safeStringArray(value: unknown, limit = 8): string[] {
  // blocked reasons 只保留短枚举；命中敏感文本的条目直接变成 redacted marker。
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => safeText(item, "unknown")).slice(0, limit);
}

function safeEndpointPath(value: unknown): string {
  // endpoint 只允许展示固定路径；query/hash 可能含 raw base URL，所以即使编码后也要剥离。
  const text = typeof value === "string" ? value.replace(/\s+/g, " ").slice(0, 180).trim() : "";
  const pathOnly = text.split(/[?#]/, 1)[0] || "unknown_endpoint";
  return FIXED_SAFETY_POLICY.endpoint_allowlist.includes(pathOnly) ? pathOnly : "redacted_endpoint";
}

function booleanField(record: Record<string, unknown>, key: string): boolean {
  // 安全字段必须严格等于 false；缺失或非布尔值都不能被解释成 true。
  return record[key] === true;
}

function numberField(record: Record<string, unknown>, key: string): number | null {
  // HTTP 状态码和计数字段只接受有限 number，避免字符串伪造通过。
  const value = record[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function artifactPath(env: NodeJS.ProcessEnv): { path: string; source: ArtifactSource } {
  // env 路径允许自动化接入安全落盘位置；响应永远不回显这个真实路径。
  const configured = (env[ARTIFACT_ENV] ?? "").trim();
  if (configured) {
    return { path: configured, source: "env_configured" };
  }
  return { path: path.join(WORKSTATION_RUNTIME_ROOT, DEFAULT_ARTIFACT_NAME), source: "workstation_runtime" };
}

function failClosed(
  status: O5O6ExternalProbeArtifactResponse["artifact_status"],
  source: ArtifactSource,
  reason: string,
): O5O6ExternalProbeArtifactResponse {
  // 缺 artifact 也必须返回稳定 shape，让 UI 显示配置缺口而不是崩成空白。
  return {
    schema: RESPONSE_SCHEMA,
    ...PROOF_FLAGS,
    artifact_status: status,
    artifact_source: source,
    artifact_path_exposed: false,
    raw_url_exposed: false,
    token_exposed: false,
    traceback_exposed: false,
    updated_at: null,
    probe_status: "not_loaded",
    runner: "not_loaded",
    viewpoint: "not_loaded",
    token_status: "absent",
    credentials_redacted: true,
    summary: {
      endpoint_count: 0,
      reachable_count: 0,
      schema_matched_count: 0,
      fail_closed_count: 0,
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      delivery_success: false,
      primary_actions_enabled: false,
      reads_hardware: false,
    },
    endpoints: [],
    safety_policy: FIXED_SAFETY_POLICY,
    key_false_fields: [
      "safe_to_control=false",
      "sends_commands=false",
      "robot_control_executed=false",
      "delivery_success=false",
      "primary_actions_enabled=false",
      "reads_hardware=false",
    ],
    blocked_reasons: [reason],
    not_proven: ["external_live_probe_artifact_not_loaded", "real_public_https_tls_not_proven", "real_4g_sim_not_proven"],
    safe_to_control: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
  };
}

function summarizeEndpoint(value: unknown): O5O6ExternalProbeArtifactEndpointSummary {
  const record = asRecord(value) ?? {};
  return {
    name: safeText(record.name, "unknown_endpoint"),
    endpoint: safeEndpointPath(record.endpoint),
    reachable: record.reachable === true,
    http_status: numberField(record, "http_status"),
    schema: safeText(record.schema, "not_loaded"),
    schema_status: safeText(record.schema_status, "not_loaded"),
    contract_status: safeText(record.contract_status, "fail_closed"),
    failure_category: safeText(record.failure_category, "unknown"),
    blocked_reasons: safeStringArray(record.blocked_reasons),
    dangerous_true_fields: safeStringArray(record.dangerous_true_fields),
    sensitive_markers: safeStringArray(record.sensitive_markers),
  };
}

function hasUnsafeSafetyTrue(record: Record<string, unknown>): boolean {
  // artifact 顶层安全 false 字段一旦为 true，说明 artifact 不适合进入 UI。
  return [
    "safe_to_control",
    "sends_commands",
    "reads_hardware",
    "robot_control_executed",
    "delivery_success",
    "primary_actions_enabled",
  ].some((key) => booleanField(record, key));
}

export async function buildO5O6ExternalProbeArtifact(
  options: { env?: NodeJS.ProcessEnv } = {},
): Promise<O5O6ExternalProbeArtifactResponse> {
  const env = options.env ?? process.env;
  const selected = artifactPath(env);
  let raw = "";
  let statMtime: string | null = null;
  try {
    // 这里只读单个 JSON artifact；不执行 probe、不联网、不访问机器人或硬件。
    const [content, stat] = await Promise.all([fs.readFile(selected.path, "utf8"), fs.stat(selected.path)]);
    raw = content;
    statMtime = stat.mtime.toISOString();
  } catch {
    return failClosed("missing", selected.source, "artifact_not_found_or_unreadable");
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return failClosed("bad_json", selected.source, "artifact_bad_json");
  }
  const artifact = asRecord(parsed);
  if (!artifact || artifact.schema !== PROBE_SCHEMA) {
    return failClosed("unsupported_schema", selected.source, "artifact_schema_mismatch");
  }
  if (hasUnsafeSafetyTrue(artifact)) {
    return failClosed("unsafe_artifact", selected.source, "artifact_claims_unsafe_true_field");
  }

  const summary = asRecord(artifact.summary) ?? {};
  return {
    schema: RESPONSE_SCHEMA,
    ...PROOF_FLAGS,
    artifact_status: "loaded",
    artifact_source: selected.source,
    artifact_path_exposed: false,
    raw_url_exposed: false,
    token_exposed: false,
    traceback_exposed: false,
    updated_at: safeText(artifact.executed_at, statMtime ?? "unknown"),
    probe_status: safeText(artifact.probe_status, "fail_closed"),
    runner: safeText(artifact.runner, "node_or_unknown"),
    viewpoint: safeText(artifact.viewpoint, "external_or_upper_computer_readonly"),
    token_status: artifact.token_status === "present" ? "present" : "absent",
    credentials_redacted: artifact.credentials_redacted !== false,
    summary: {
      endpoint_count: numberField(summary, "endpoint_count") ?? 0,
      reachable_count: numberField(summary, "reachable_count") ?? 0,
      schema_matched_count: numberField(summary, "schema_matched_count") ?? 0,
      fail_closed_count: numberField(summary, "fail_closed_count") ?? 0,
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      delivery_success: false,
      primary_actions_enabled: false,
      reads_hardware: false,
    },
    endpoints: Array.isArray(artifact.endpoints) ? artifact.endpoints.map(summarizeEndpoint).slice(0, 5) : [],
    safety_policy: FIXED_SAFETY_POLICY,
    key_false_fields: safeStringArray(artifact.key_false_fields, 10),
    blocked_reasons: safeStringArray(artifact.blocked_reasons, 12),
    not_proven: safeStringArray(artifact.not_proven, 12),
    safe_to_control: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
  };
}
