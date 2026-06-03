#!/usr/bin/env node
import fs from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PROBE_SCHEMA = "trashbot.o5_o6.external_live_probe.v1";
const COLLECTOR_SCHEMA = "trashbot.o5_o6.upper_ssh_collector.v1";
const DEFAULT_SSH_TARGET = "root@192.168.1.11";
const DEFAULT_SSH_PORT = "37878";
const DEFAULT_REMOTE_ROOT = "/root/rober";
const DEFAULT_REMOTE_SCRIPT = "cloud-relay/scripts/o5_o6_external_live_probe.py";
const DEFAULT_PC_BASE_URL = "http://127.0.0.1:8787";
const DEFAULT_SSH_TIMEOUT_SECONDS = 8;
const DEFAULT_PROBE_TIMEOUT_MS = 2500;
const ENDPOINTS = ["/api/o5/readiness/health", "/api/o6/archive/health", "/api/o5-o6/cloud-relay-health"];
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const workstationRoot = path.resolve(__dirname, "..");
const defaultOutput = path.join(workstationRoot, ".workstation-runtime", "o5-o6-external-live-probe.json");

function nowIso() {
  return new Date().toISOString();
}

function takeValue(argv, index, name) {
  // CLI 同时支持 "--x value" 和 "--x=value"，方便手工和自动化复用。
  const current = argv[index];
  if (current.startsWith(`${name}=`)) {
    return { value: current.slice(name.length + 1), consumed: 1 };
  }
  if (current === name && argv[index + 1]) {
    return { value: argv[index + 1], consumed: 2 };
  }
  if (current === name) {
    throw new Error(`${name}_requires_value`);
  }
  return null;
}

function parsePositiveInteger(value, name) {
  // 端口和超时必须显式为正整数，避免现场误传空值后落入隐式默认。
  if (!/^\d+$/.test(String(value))) {
    throw new Error(`${name}_must_be_integer`);
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed <= 0) {
    throw new Error(`${name}_must_be_positive_integer`);
  }
  return parsed;
}

function normalizeBaseUrl(raw, { allowEmpty = false } = {}) {
  // base URL 只允许 HTTP(S)，且禁止 credential/query/hash 进入 SSH 命令和 artifact。
  const value = String(raw || "").trim();
  if (!value && allowEmpty) {
    return "";
  }
  const parsed = new URL(value || DEFAULT_PC_BASE_URL);
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("base_url_protocol_not_allowed");
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error("base_url_must_not_include_credentials_query_or_hash");
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  return parsed.toString().replace(/\/$/, "");
}

function safeOutputRef(outputPath) {
  // artifact_ref 只显示 repo 内相对路径，避免把 workstation 绝对路径写进接口材料。
  const relative = path.relative(workstationRoot, outputPath);
  return relative.startsWith("..") ? path.basename(outputPath) : relative.split(path.sep).join("/");
}

function shellQuote(value) {
  // SSH 远端只通过 sh -lc 执行 allowlist 命令；所有动态值先单引号转义。
  return `'${String(value).replaceAll("'", "'\"'\"'")}'`;
}

function safeText(value, fallback = "unknown") {
  // SSH stderr/stdout 只保留粗分类；不把 token、URL、路径或 traceback 原样写入证据。
  const text = typeof value === "string" ? value.replace(/\s+/g, " ").slice(0, 160) : fallback;
  return /(authorization|bearer\s+|token=|password=|secret=|traceback|https?:\/\/|\/mnt\/|[a-z]:\\|\/dev\/|cmd_vel|robots\/)/i.test(text)
    ? "redacted_sensitive_value"
    : text;
}

export function buildCollectorPlan({ argv = [], env = process.env } = {}) {
  let dryRun = false;
  let sshTarget = env.ROBER_O5_O6_UPPER_SSH_TARGET || DEFAULT_SSH_TARGET;
  let sshPort = env.ROBER_O5_O6_UPPER_SSH_PORT || DEFAULT_SSH_PORT;
  let remoteRoot = env.ROBER_O5_O6_UPPER_REMOTE_ROOT || DEFAULT_REMOTE_ROOT;
  let remoteScript = env.ROBER_O5_O6_UPPER_REMOTE_SCRIPT || DEFAULT_REMOTE_SCRIPT;
  let pcBaseUrl = env.ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL || DEFAULT_PC_BASE_URL;
  let cloudBaseUrl = env.ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL || env.ROBER_CLOUD_RELAY_BASE_URL || "";
  let outputPath = env.ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT || defaultOutput;
  let sshTimeoutSeconds = env.ROBER_O5_O6_UPPER_SSH_TIMEOUT_SECONDS || String(DEFAULT_SSH_TIMEOUT_SECONDS);
  let probeTimeoutMs = env.ROBER_O5_O6_UPPER_PROBE_TIMEOUT_MS || String(DEFAULT_PROBE_TIMEOUT_MS);

  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--dry-run") {
      dryRun = true;
      continue;
    }
    const mappings = [
      ["--ssh-target", (value) => { sshTarget = value; }],
      ["--ssh-port", (value) => { sshPort = value; }],
      ["--remote-root", (value) => { remoteRoot = value; }],
      ["--remote-script", (value) => { remoteScript = value; }],
      ["--pc-base-url", (value) => { pcBaseUrl = value; }],
      ["--cloud-base-url", (value) => { cloudBaseUrl = value; }],
      ["--output", (value) => { outputPath = value; }],
      ["--timeout-seconds", (value) => { sshTimeoutSeconds = value; }],
      ["--probe-timeout-ms", (value) => { probeTimeoutMs = value; }],
    ];
    const matched = mappings.find(([name]) => takeValue(argv, index, name));
    if (matched) {
      const parsed = takeValue(argv, index, matched[0]);
      matched[1](parsed.value);
      index += parsed.consumed - 1;
      continue;
    }
    throw new Error(`unknown_argument:${item}`);
  }

  return {
    dryRun,
    sshTarget: String(sshTarget || DEFAULT_SSH_TARGET).trim(),
    sshPort: String(parsePositiveInteger(sshPort, "ssh_port")),
    remoteRoot: String(remoteRoot || DEFAULT_REMOTE_ROOT).trim(),
    remoteScript: String(remoteScript || DEFAULT_REMOTE_SCRIPT).trim(),
    pcBaseUrl: normalizeBaseUrl(pcBaseUrl),
    cloudBaseUrl: normalizeBaseUrl(cloudBaseUrl, { allowEmpty: true }),
    outputPath: path.resolve(outputPath),
    sshTimeoutSeconds: parsePositiveInteger(sshTimeoutSeconds, "ssh_timeout_seconds"),
    probeTimeoutMs: parsePositiveInteger(probeTimeoutMs, "probe_timeout_ms"),
  };
}

export function buildRemoteCommand(plan) {
  // 远端命令只做 cd、script 存在性检查和 Python stdlib probe 一次性只读运行。
  // 不传 bearer token；真实凭证必须在上位机环境中存在，避免 PC 命令行泄漏 secret。
  return [
    `cd ${shellQuote(plan.remoteRoot)} || exit 41`,
    `test -f ${shellQuote(plan.remoteScript)} || exit 42`,
    [
      "python3",
      shellQuote(plan.remoteScript),
      "--once-json",
      "--pc-base-url",
      shellQuote(plan.pcBaseUrl),
      "--cloud-base-url",
      shellQuote(plan.cloudBaseUrl),
      "--timeout-ms",
      shellQuote(String(plan.probeTimeoutMs)),
    ].join(" "),
  ].join("; ");
}

export function buildSshArgs(plan) {
  // BatchMode 避免自动化卡在密码交互；ConnectTimeout 给 daily scan 一个硬边界。
  return [
    "-o",
    "BatchMode=yes",
    "-o",
    `ConnectTimeout=${plan.sshTimeoutSeconds}`,
    "-p",
    plan.sshPort,
    plan.sshTarget,
    "sh",
    "-lc",
    buildRemoteCommand(plan),
  ];
}

function endpointBlocked(name, endpoint, reason) {
  // blocked artifact 仍保持 external probe endpoint shape，acceptance queue 可以照常消费。
  return {
    name,
    endpoint,
    expected_schema:
      name === "o5_readiness"
        ? "trashbot.o5.readiness_health.v1"
        : name === "o6_archive"
          ? "trashbot.o6.archive_health.v1"
          : "trashbot.pc_tools_workstation.o5_o6_cloud_relay_health.v1",
    reachable: false,
    http_status: null,
    schema: "not_loaded",
    schema_status: "not_loaded",
    contract_status: "fail_closed",
    failure_category: reason,
    blocked_reasons: [reason],
    dangerous_true_fields: [],
    sensitive_markers: [],
  };
}

function tlsBlocked(reason) {
  return {
    tls_status: reason === "cloud_base_url_not_configured" ? "not_configured" : "blocked",
    scheme: "not_configured",
    hostname_redacted: "not_configured",
    host_status: reason,
    port: null,
    tls_observed: false,
    tls_version: "not_observed",
    cipher_status: "not_observed",
    cipher_bits: null,
    certificate: {
      not_before: "not_available",
      not_after: "not_available",
      certificate_expiry_days: null,
      issuer_summary: { field_count: 0, common_name_status: "absent", organization_status: "absent", country_status: "absent" },
      subject_summary: { field_count: 0, common_name_status: "absent", organization_status: "absent", country_status: "absent" },
      subject_alt_name_summary: { dns_name_count: 0, ip_address_count: 0 },
    },
    verification_error: reason,
  };
}

function keyFalseFields() {
  return [
    "safe_to_control=false",
    "sends_commands=false",
    "robot_control_executed=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
    "reads_hardware=false",
  ];
}

export function buildBlockedArtifact(plan, reason) {
  const normalizedReason = safeText(reason, "ssh_collection_blocked");
  const endpoints = [
    endpointBlocked("o5_readiness", ENDPOINTS[0], normalizedReason),
    endpointBlocked("o6_archive", ENDPOINTS[1], normalizedReason),
    endpointBlocked("pc_aggregate", ENDPOINTS[2], normalizedReason),
  ];
  return {
    schema: PROBE_SCHEMA,
    runner: "pc_upper_ssh_collector",
    collector_schema: COLLECTOR_SCHEMA,
    source_host_role: "upper_computer",
    executed_at: nowIso(),
    probe_status: "fail_closed",
    viewpoint: "upper_computer_via_pc_ssh_readonly",
    pc_base_url: plan.pcBaseUrl ? "configured_redacted" : "not_configured",
    cloud_base_url: plan.cloudBaseUrl ? "configured_redacted" : "not_configured",
    token_status: "absent",
    credentials_redacted: true,
    tls_evidence: tlsBlocked(plan.cloudBaseUrl ? normalizedReason : "cloud_base_url_not_configured"),
    endpoints,
    summary: {
      endpoint_count: endpoints.length,
      reachable_count: 0,
      schema_matched_count: 0,
      fail_closed_count: endpoints.length,
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      delivery_success: false,
      primary_actions_enabled: false,
      reads_hardware: false,
    },
    safety_policy: {
      method_allowlist: ["GET"],
      endpoint_allowlist: ENDPOINTS,
      forbidden_paths: ["/robots/*", "/cmd_vel"],
      bearer_source: "remote_environment_only",
      no_post: true,
      no_robot_control: true,
      no_hardware_read: true,
    },
    key_false_fields: keyFalseFields(),
    ssh_collection: sshCollectionSummary(plan, "blocked", normalizedReason),
    blocked_reasons: [normalizedReason],
    not_proven: [
      "upper_ssh_probe_not_observed",
      "real_public_https_tls_not_proven",
      "real_4g_sim_not_proven",
      "production_db_queue_not_proven",
      "real_oss_cdn_live_traffic_not_proven",
      "real_phone_browser_not_proven",
      "delivery_success_not_proven",
    ],
    safe_to_control: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

function sshCollectionSummary(plan, status, failureCategory = null) {
  // SSH 元数据只保留角色、端口和 artifact ref，不回显远端 stderr、token 或完整 URL。
  return {
    schema: COLLECTOR_SCHEMA,
    status,
    source_host_role: "pc_workstation",
    target_host_role: "upper_computer",
    ssh_target_configured: Boolean(plan.sshTarget),
    ssh_port: Number(plan.sshPort),
    remote_root_configured: Boolean(plan.remoteRoot),
    remote_script: path.basename(plan.remoteScript),
    output_ref: safeOutputRef(plan.outputPath),
    failure_category: failureCategory,
    dry_run: plan.dryRun,
    command_boundary: {
      executes_python_stdlib_probe_once: true,
      passes_bearer_token_via_cli_or_ssh_args: false,
      post_executed: false,
      robots_path_accessed: false,
      cmd_vel_accessed: false,
      hardware_read_executed: false,
      robot_control_executed: false,
    },
  };
}

function parseRemoteProbe(plan, sshResult) {
  if (sshResult.error) {
    return buildBlockedArtifact(plan, "ssh_spawn_failed");
  }
  if (sshResult.code === 41) {
    return buildBlockedArtifact(plan, "remote_repo_root_missing");
  }
  if (sshResult.code === 42) {
    return buildBlockedArtifact(plan, "remote_probe_script_missing");
  }
  if (sshResult.code !== 0) {
    return buildBlockedArtifact(plan, classifySshFailure(`${sshResult.stderr}\n${sshResult.stdout}`));
  }
  let parsed;
  try {
    parsed = JSON.parse(String(sshResult.stdout || "").trim());
  } catch {
    return buildBlockedArtifact(plan, "remote_stdout_bad_json");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed) || parsed.schema !== PROBE_SCHEMA) {
    return buildBlockedArtifact(plan, "remote_probe_schema_mismatch");
  }
  return decorateRemoteProbe(plan, parsed);
}

function classifySshFailure(text) {
  if (/Permission denied|publickey|Authentication/i.test(text)) {
    return "ssh_auth_failed";
  }
  if (/Connection refused|connect.*refused/i.test(text)) {
    return "ssh_connection_refused";
  }
  if (/timed out|Connection timeout|ConnectTimeout/i.test(text)) {
    return "ssh_timeout";
  }
  if (/No route to host|Network is unreachable|EHOSTUNREACH|ENETUNREACH/i.test(text)) {
    return "ssh_network_unreachable";
  }
  return "remote_probe_failed";
}

function decorateRemoteProbe(plan, remoteProbe) {
  const remoteRunner = typeof remoteProbe.runner === "string" ? remoteProbe.runner : "unknown";
  const blocked = Array.isArray(remoteProbe.blocked_reasons) ? remoteProbe.blocked_reasons.map((item) => safeText(item)).slice(0, 20) : [];
  const tokenReason = remoteProbe.token_status === "present" ? [] : ["remote_bearer_token_absent"];
  const cloudReason = plan.cloudBaseUrl ? [] : ["cloud_base_url_not_configured"];
  // token/cloud 缺口不覆盖远端 probe 事实，只追加为 collector 可见 blocked reason。
  return {
    ...remoteProbe,
    runner: `pc_upper_ssh_collector+${safeText(remoteRunner)}`,
    remote_runner: safeText(remoteRunner),
    collector_schema: COLLECTOR_SCHEMA,
    source_host_role: "upper_computer",
    viewpoint: "upper_computer_via_pc_ssh_readonly",
    credentials_redacted: remoteProbe.credentials_redacted !== false,
    ssh_collection: sshCollectionSummary(plan, "collected", null),
    blocked_reasons: [...new Set([...blocked, ...tokenReason, ...cloudReason])].slice(0, 20),
    safe_to_control: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

function runSsh(plan, spawnImpl = spawn) {
  return new Promise((resolve) => {
    const child = spawnImpl("ssh", buildSshArgs(plan), { cwd: workstationRoot, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += String(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });
    child.on("error", (error) => {
      resolve({ code: null, stdout: "", stderr: "", error });
    });
    child.on("close", (code) => {
      resolve({ code, stdout, stderr, error: null });
    });
  });
}

async function writeArtifact(result, outputPath) {
  // 非 dry-run 的 blocked/observed 结果都落同一个 artifact，acceptance queue 只读这个文件。
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
}

export function buildDryRunResult(plan) {
  return {
    schema: COLLECTOR_SCHEMA,
    status: "dry_run",
    dry_run: true,
    artifact_written: false,
    output_ref: safeOutputRef(plan.outputPath),
    ssh_command: {
      binary: "ssh",
      args: buildSshArgs(plan),
      contains_bearer_token: false,
    },
    safety_policy: {
      no_post: true,
      no_robot_control: true,
      no_hardware_read: true,
      forbidden_paths: ["/robots/*", "/cmd_vel"],
      bearer_source: "remote_environment_only",
    },
    blocked_reasons: ["dry_run_no_ssh_no_network_no_artifact"],
    safe_to_control: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

export async function collectUpperSshArtifact({ plan, spawnImpl = spawn } = {}) {
  const effectivePlan = plan || buildCollectorPlan();
  const result = parseRemoteProbe(effectivePlan, await runSsh(effectivePlan, spawnImpl));
  result.ssh_collection = result.ssh_collection || sshCollectionSummary(effectivePlan, "collected", null);
  result.artifact_written = true;
  await writeArtifact(result, effectivePlan.outputPath);
  return result;
}

export async function runCollector({ argv = process.argv.slice(2), env = process.env, spawnImpl = spawn } = {}) {
  let plan;
  try {
    plan = buildCollectorPlan({ argv, env });
  } catch (error) {
    const fallback = {
      dryRun: false,
      sshTarget: DEFAULT_SSH_TARGET,
      sshPort: DEFAULT_SSH_PORT,
      remoteRoot: DEFAULT_REMOTE_ROOT,
      remoteScript: DEFAULT_REMOTE_SCRIPT,
      pcBaseUrl: DEFAULT_PC_BASE_URL,
      cloudBaseUrl: "",
      outputPath: defaultOutput,
    };
    const result = buildBlockedArtifact(fallback, error instanceof Error ? error.message : "collector_argument_invalid");
    process.stdout.write(`${JSON.stringify(result)}\n`);
    return 2;
  }
  if (plan.dryRun) {
    process.stdout.write(`${JSON.stringify(buildDryRunResult(plan))}\n`);
    return 0;
  }
  const result = await collectUpperSshArtifact({ plan, spawnImpl });
  process.stdout.write(`${JSON.stringify(result)}\n`);
  return result.probe_status === "observed_fail_closed_contract" ? 0 : 2;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runCollector().then((code) => {
    process.exitCode = code;
  });
}
