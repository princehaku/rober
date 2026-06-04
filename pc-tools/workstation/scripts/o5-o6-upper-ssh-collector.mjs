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
const DEFAULT_SSH_TIMEOUT_SECONDS = 8;
const DEFAULT_PROBE_TIMEOUT_MS = 2500;
const ENDPOINTS = ["/api/o5/readiness/health", "/api/o6/archive/health", "/api/o5-o6/cloud-relay-health"];
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const workstationRoot = path.resolve(__dirname, "..");
const repositoryRoot = path.resolve(workstationRoot, "../..");
const localProbeScript = path.join(repositoryRoot, DEFAULT_REMOTE_SCRIPT);
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

function tokenizeShellLike(value) {
  // 只为 operator 粘贴的 ssh 命令做轻量解析；不执行、不展开变量、不解释 shell 重定向。
  const tokens = [];
  let current = "";
  let quote = null;
  for (const char of String(value || "")) {
    if ((char === "'" || char === "\"") && quote === null) {
      quote = char;
      continue;
    }
    if (char === quote) {
      quote = null;
      continue;
    }
    if (/\s/.test(char) && quote === null) {
      if (current) {
        tokens.push(current);
        current = "";
      }
      continue;
    }
    current += char;
  }
  if (current) {
    tokens.push(current);
  }
  return tokens;
}

function parseSshCommand(value) {
  // 支持 operator 直接粘贴 "ssh root@host -p 37878"；只提取 target/port，忽略远端命令。
  const tokens = tokenizeShellLike(value);
  if (tokens[0] !== "ssh") {
    throw new Error("ssh_command_must_start_with_ssh");
  }
  let target = "";
  let port = "";
  for (let index = 1; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token === "-p" || token === "-P" || token === "--port") {
      const next = tokens[index + 1];
      if (!next) {
        throw new Error("ssh_command_port_requires_value");
      }
      port = next;
      index += 1;
      continue;
    }
    if (token.startsWith("-p") && token.length > 2 && /^\d+$/.test(token.slice(2))) {
      port = token.slice(2);
      continue;
    }
    if (token.startsWith("-")) {
      continue;
    }
    if (!target) {
      target = token;
    }
  }
  if (!target) {
    throw new Error("ssh_command_target_missing");
  }
  return { target, port };
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
  if (!value) {
    throw new Error("base_url_not_configured");
  }
  const parsed = new URL(value);
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
  let syncRemoteProbe = false;
  let sshTarget = env.ROBER_O5_O6_UPPER_SSH_TARGET || DEFAULT_SSH_TARGET;
  let sshTargetSource = env.ROBER_O5_O6_UPPER_SSH_TARGET ? "env" : "default";
  let sshPort = env.ROBER_O5_O6_UPPER_SSH_PORT || DEFAULT_SSH_PORT;
  let sshPortSource = env.ROBER_O5_O6_UPPER_SSH_PORT ? "env" : "default";
  let remoteRoot = env.ROBER_O5_O6_UPPER_REMOTE_ROOT || DEFAULT_REMOTE_ROOT;
  let remoteRootSource = env.ROBER_O5_O6_UPPER_REMOTE_ROOT ? "env" : "default";
  let remoteScript = env.ROBER_O5_O6_UPPER_REMOTE_SCRIPT || DEFAULT_REMOTE_SCRIPT;
  let remoteScriptSource = env.ROBER_O5_O6_UPPER_REMOTE_SCRIPT ? "env" : "default";
  let pcBaseUrl = env.ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL || "";
  let pcBaseUrlSource = pcBaseUrl ? "env" : "absent";
  let cloudBaseUrl = env.ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL || env.ROBER_CLOUD_RELAY_BASE_URL || "";
  let cloudBaseUrlSource = env.ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL ? "env" : env.ROBER_CLOUD_RELAY_BASE_URL ? "env" : "absent";
  let outputPath = env.ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT || defaultOutput;
  let sshTimeoutSeconds = env.ROBER_O5_O6_UPPER_SSH_TIMEOUT_SECONDS || String(DEFAULT_SSH_TIMEOUT_SECONDS);
  let probeTimeoutMs = env.ROBER_O5_O6_UPPER_PROBE_TIMEOUT_MS || String(DEFAULT_PROBE_TIMEOUT_MS);

  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--dry-run") {
      dryRun = true;
      continue;
    }
    if (item === "--sync-remote-probe" || item === "--install-remote-probe") {
      syncRemoteProbe = true;
      continue;
    }
    const sshCommand = takeValue(argv, index, "--ssh-command");
    if (sshCommand) {
      const parsed = parseSshCommand(sshCommand.value);
      sshTarget = parsed.target;
      sshTargetSource = "ssh_command";
      if (parsed.port) {
        sshPort = parsed.port;
        sshPortSource = "ssh_command";
      }
      index += sshCommand.consumed - 1;
      continue;
    }
    const mappings = [
      ["--ssh-target", (value) => { sshTarget = value; sshTargetSource = value ? "cli" : "absent"; }],
      ["--ssh-port", (value) => { sshPort = value; sshPortSource = value ? "cli" : "absent"; }],
      ["--remote-root", (value) => { remoteRoot = value; remoteRootSource = value ? "cli" : "absent"; }],
      ["--remote-script", (value) => { remoteScript = value; remoteScriptSource = value ? "cli" : "absent"; }],
      ["--pc-base-url", (value) => { pcBaseUrl = value; pcBaseUrlSource = value ? "cli" : "absent"; }],
      ["--cloud-base-url", (value) => { cloudBaseUrl = value; cloudBaseUrlSource = value ? "cli" : "absent"; }],
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
    syncRemoteProbe,
    sshTarget: String(sshTarget || "").trim(),
    sshTargetSource,
    sshPort: String(parsePositiveInteger(sshPort, "ssh_port")),
    sshPortSource,
    remoteRoot: String(remoteRoot || DEFAULT_REMOTE_ROOT).trim(),
    remoteRootSource,
    remoteScript: String(remoteScript || DEFAULT_REMOTE_SCRIPT).trim(),
    remoteScriptSource,
    pcBaseUrl: normalizeBaseUrl(pcBaseUrl, { allowEmpty: true }),
    pcBaseUrlExplicit: Boolean(String(pcBaseUrl || "").trim()),
    pcBaseUrlSource,
    cloudBaseUrl: normalizeBaseUrl(cloudBaseUrl, { allowEmpty: true }),
    cloudBaseUrlSource,
    remoteBearerTokenExpected: "remote_environment_only",
    remoteBearerTokenLocalHint:
      env.TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN || env.ROBER_CLOUD_RELAY_BEARER_TOKEN ? "local_env_present_not_forwarded" : "not_observed_locally",
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

export function buildStdinFallbackRemoteCommand(plan) {
  // stdin fallback 不写远端文件，只把本地 probe 作为 python3 - 的程序正文一次性喂入。
  // 仍先 cd 到 repo root，是为了沿用上位机运行上下文，同时不要求远端存在 cloud-relay 子树。
  return [
    `cd ${shellQuote(plan.remoteRoot)} || exit 41`,
    [
      "python3",
      "-",
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

function remoteProbeSyncTarget(plan) {
  // 同步模式只允许默认 probe 位置，避免把这个 helper 变成任意远端写文件工具。
  const targetAllowed = plan.remoteRoot === DEFAULT_REMOTE_ROOT && plan.remoteScript === DEFAULT_REMOTE_SCRIPT;
  return {
    requested: Boolean(plan.syncRemoteProbe),
    mode: "ssh_stdin_write",
    local_probe_ref: "cloud-relay/scripts/o5_o6_external_live_probe.py",
    remote_target_ref: `${DEFAULT_REMOTE_ROOT}/${DEFAULT_REMOTE_SCRIPT}`,
    allowed_write_scope: "single_probe_script_only",
    exact_final_path_only: true,
    target_allowed: targetAllowed,
    blocked_reason: targetAllowed ? null : "remote_probe_sync_target_outside_allowed_path",
  };
}

export function buildProbeInstallRemoteCommand(plan) {
  // 远端写入必须直达最终脚本，避免 tmp/pycache 让安全边界从单文件变成多文件。
  const target = remoteProbeSyncTarget(plan);
  if (!target.target_allowed) {
    return "exit 49";
  }
  return [
    `cd ${shellQuote(DEFAULT_REMOTE_ROOT)} || exit 41`,
    `test -d ${shellQuote(path.posix.dirname(DEFAULT_REMOTE_SCRIPT))} || exit 43`,
    `cat > ${shellQuote(DEFAULT_REMOTE_SCRIPT)} || exit 44`,
    `test -s ${shellQuote(DEFAULT_REMOTE_SCRIPT)} || exit 47`,
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

export function buildProbeInstallSshArgs(plan) {
  // 同步命令只走 SSH stdin 写 probe 文件；argv 中不出现源码、URL token 或 bearer。
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
    buildProbeInstallRemoteCommand(plan),
  ];
}

export function buildStdinFallbackSshArgs(plan) {
  // fallback 仍然只走 sh -lc + python3 -，SSH argv 中不出现 bearer/token 或脚本正文。
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
    buildStdinFallbackRemoteCommand(plan),
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

function pcBaseUrlBlockedReason(plan) {
  // 上位机 SSH 视角下 127.0.0.1 指向上位机自身，所以 PC base URL 必须显式给出。
  return plan.pcBaseUrlExplicit && plan.pcBaseUrl ? null : "pc_base_url_not_configured_for_upper_ssh";
}

function buildPreflightChecks(plan) {
  // preflight 只做参数和合同分类；不会 SSH、不会联网，也不会探测远端文件。
  const checks = [
    {
      id: "ssh_target",
      status: plan.sshTarget ? "configured" : "blocked",
      source: plan.sshTargetSource || "absent",
      blocked_reason: plan.sshTarget ? null : "ssh_target_not_configured",
      next_action: plan.sshTarget ? null : "pass --ssh-command \"ssh root@192.168.1.11 -p 37878\" or --ssh-target root@192.168.1.11",
    },
    {
      id: "ssh_port",
      status: plan.sshPort ? "configured" : "blocked",
      source: plan.sshPortSource || "absent",
      blocked_reason: plan.sshPort ? null : "ssh_port_not_configured",
      next_action: plan.sshPort ? null : "pass --ssh-port 37878 or include -p 37878 in --ssh-command",
    },
    {
      id: "pc_base_url",
      status: pcBaseUrlBlockedReason(plan) ? "blocked" : "configured",
      source: plan.pcBaseUrlSource || "absent",
      blocked_reason: pcBaseUrlBlockedReason(plan),
      next_action: pcBaseUrlBlockedReason(plan) ? pcBaseUrlNextAction() : null,
    },
    {
      id: "cloud_base_url",
      status: plan.cloudBaseUrl ? "configured" : "blocked",
      source: plan.cloudBaseUrlSource || "absent",
      blocked_reason: plan.cloudBaseUrl ? null : "cloud_base_url_not_configured",
      next_action: plan.cloudBaseUrl ? null : "pass --cloud-base-url https://<production-cloud-base> or set ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL",
    },
    {
      id: "remote_bearer_token",
      status: "requires_remote_runtime",
      source: plan.remoteBearerTokenExpected,
      blocked_reason: "remote_bearer_token_not_verified_by_pc_preflight",
      next_action: "configure TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN or ROBER_CLOUD_RELAY_BEARER_TOKEN in the upper-computer runtime before live collection",
    },
    {
      id: "remote_root",
      status: "requires_ssh_probe",
      source: plan.remoteRootSource || "default",
      blocked_reason: "remote_root_not_verified_by_pc_preflight",
      next_action: "run the collector without --dry-run to check remote_root by read-only SSH cd; override with --remote-root if needed",
    },
    {
      id: "remote_probe_script",
      status: "requires_ssh_probe",
      source: plan.remoteScriptSource || "default",
      blocked_reason: "remote_probe_script_not_verified_by_pc_preflight",
      next_action: "live collector checks installed script first and then tries stdin_fallback without writing remote files",
    },
  ];
  if (plan.syncRemoteProbe) {
    const syncTarget = remoteProbeSyncTarget(plan);
    checks.push({
      id: "remote_probe_sync",
      status: plan.dryRun ? "dry_run_not_executed" : syncTarget.target_allowed ? "requested" : "blocked",
      source: "cli",
      blocked_reason: plan.dryRun
        ? "remote_probe_sync_not_executed_dry_run"
        : syncTarget.blocked_reason,
      next_action: plan.dryRun
        ? "rerun without --dry-run only when intentionally syncing the local probe to the default upper-computer path"
        : syncTarget.blocked_reason
          ? "use the default /root/rober/cloud-relay/scripts/o5_o6_external_live_probe.py sync target for this safe helper"
          : null,
    });
  }
  return checks;
}

function buildPreflight(plan) {
  const checks = buildPreflightChecks(plan);
  const blockedReasons = checks
    .map((check) => check.blocked_reason)
    .filter((reason) => typeof reason === "string" && reason.length > 0);
  return {
    schema: "trashbot.o5_o6.upper_ssh_collector_preflight.v1",
    status: blockedReasons.some((reason) => reason.endsWith("_not_configured") || reason === "pc_base_url_not_configured_for_upper_ssh")
      ? "blocked"
      : "ready_for_readonly_ssh_probe",
    checks,
    failure_classification: blockedReasons,
    operator_next_actions: checks.map((check) => check.next_action).filter((action) => typeof action === "string" && action.length > 0),
    accepts_ssh_command_input: true,
    example_ssh_command_input: "ssh root@192.168.1.11 -p 37878",
    remote_bearer_token_local_hint: plan.remoteBearerTokenLocalHint || "not_observed_locally",
    execution_policy: {
      dry_run_no_ssh: plan.dryRun,
      network_probe_executed: false,
      post_executed: false,
      robots_path_accessed: false,
      cmd_vel_accessed: false,
      hardware_read_executed: false,
      robot_control_executed: false,
    },
  };
}

function pcBaseUrlNextAction() {
  // next_action 写成可复制的 operator 动作，但不要求 artifact 暴露真实 PC hostname。
  return "pass --pc-base-url http://<pc-workstation-host>:8787 or set ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL to an address reachable from the upper computer";
}

export function buildBlockedArtifact(plan, reason, collectionOptions = {}) {
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
    pc_base_url: plan.pcBaseUrl ? "configured_redacted" : "not_configured_for_upper_ssh",
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
    ssh_collection: sshCollectionSummary(plan, "blocked", normalizedReason, collectionOptions),
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

function sshCollectionSummary(plan, status, failureCategory = null, options = {}) {
  // SSH 元数据只保留角色、端口和 artifact ref，不回显远端 stderr、token 或完整 URL。
  const executionMode = options.executionMode || "installed_script";
  const attemptedExecutionModes =
    Array.isArray(options.attemptedExecutionModes) && options.attemptedExecutionModes.length > 0
      ? options.attemptedExecutionModes
      : [executionMode];
  return {
    schema: COLLECTOR_SCHEMA,
    status,
    execution_mode: executionMode,
    attempted_execution_modes: attemptedExecutionModes,
    fallback_used: executionMode === "stdin_fallback",
    fallback_reason: options.fallbackReason || null,
    source_host_role: "pc_workstation",
    target_host_role: "upper_computer",
    ssh_target_configured: Boolean(plan.sshTarget),
    ssh_port: Number(plan.sshPort),
    remote_root_configured: Boolean(plan.remoteRoot),
    remote_script: path.basename(plan.remoteScript),
    pc_base_url_configured_for_upper_ssh: !pcBaseUrlBlockedReason(plan),
    pc_base_url_source: plan.pcBaseUrlSource || "absent",
    pc_base_url_next_action: pcBaseUrlBlockedReason(plan) ? pcBaseUrlNextAction() : null,
    preflight: buildPreflight(plan),
    remote_probe_sync: remoteProbeSyncSummary(plan, options.remoteProbeSync),
    output_ref: safeOutputRef(plan.outputPath),
    failure_category: failureCategory,
    remote_exit_code: typeof options.remoteExitCode === "number" ? options.remoteExitCode : null,
    next_action: failureCategory ? collectorNextAction(failureCategory) : null,
    remote_path_override_supported: true,
    stdin_fallback_supported: true,
    stdin_fallback_remote_write: false,
    dry_run: plan.dryRun,
    command_boundary: {
      executes_python_stdlib_probe_once: true,
      streams_local_probe_over_ssh_stdin: executionMode === "stdin_fallback",
      remote_file_write_attempted: Boolean(options.remoteProbeSync?.remoteFileWriteAttempted),
      remote_file_write_executed: Boolean(options.remoteProbeSync?.remoteFileWriteExecuted),
      remote_write_scope: options.remoteProbeSync?.remoteFileWriteExecuted ? "single_probe_script_only" : "none",
      passes_bearer_token_via_cli_or_ssh_args: false,
      post_executed: false,
      robots_path_accessed: false,
      cmd_vel_accessed: false,
      hardware_read_executed: false,
      robot_control_executed: false,
    },
  };
}

function remoteProbeSyncSummary(plan, syncResult = {}) {
  // artifact 需要把远端写入边界说清楚，避免 operator 把同步脚本误读为控制动作。
  const target = remoteProbeSyncTarget(plan);
  const observed = syncResult || {};
  return {
    ...target,
    status: observed.status || (plan.syncRemoteProbe ? (plan.dryRun ? "dry_run_not_executed" : "requested") : "not_requested"),
    ssh_executed: Boolean(observed.sshExecuted),
    remote_file_write_attempted: Boolean(observed.remoteFileWriteAttempted),
    remote_file_write_executed: Boolean(observed.remoteFileWriteExecuted),
    dry_run_no_write: Boolean(plan.dryRun),
    contains_bearer_token: false,
    passes_bearer_token_via_cli_or_ssh_args: false,
    post_executed: false,
    robots_path_accessed: false,
    cmd_vel_accessed: false,
    hardware_read_executed: false,
    robot_control_executed: false,
    remote_exit_code: typeof observed.remoteExitCode === "number" ? observed.remoteExitCode : null,
    failure_category: observed.failureCategory || target.blocked_reason || null,
    next_action: observed.failureCategory ? collectorNextAction(observed.failureCategory) : null,
  };
}

function collectorNextAction(reason) {
  // 下一步只给 operator 可执行入口，不写真实远端绝对路径，避免 artifact 变成现场拓扑清单。
  if (reason === "pc_base_url_not_configured_for_upper_ssh") {
    return pcBaseUrlNextAction();
  }
  if (reason === "remote_repo_root_missing") {
    return "set --remote-root or ROBER_O5_O6_UPPER_REMOTE_ROOT to a checkout that contains cloud-relay/scripts/o5_o6_external_live_probe.py";
  }
  if (reason === "remote_repo_present_but_probe_script_missing") {
    return "collector will retry by SSH stdin fallback; if fallback is unavailable, sync cloud-relay/scripts/o5_o6_external_live_probe.py or set --remote-script/--remote-root to the probe location";
  }
  if (reason === "local_stdin_probe_source_missing") {
    return "restore local cloud-relay/scripts/o5_o6_external_live_probe.py in this checkout, then rerun the read-only SSH collector";
  }
  if (reason === "local_sync_probe_source_missing") {
    return "restore local cloud-relay/scripts/o5_o6_external_live_probe.py in this checkout, then rerun --sync-remote-probe";
  }
  if (reason === "remote_probe_sync_target_outside_allowed_path") {
    return "use the default /root/rober/cloud-relay/scripts/o5_o6_external_live_probe.py sync target for this scoped helper";
  }
  if (reason === "remote_probe_sync_failed" || reason === "remote_probe_sync_did_not_materialize_script") {
    return "verify remote /root/rober/cloud-relay/scripts exists and the final probe path is writable, then rerun --sync-remote-probe";
  }
  if (reason === "ssh_stdin_fallback_probe_failed") {
    return "verify remote python3 can run stdin scripts from the configured repo root, then rerun the read-only SSH collector";
  }
  if (reason === "ssh_stdin_fallback_stdout_bad_json" || reason === "ssh_stdin_fallback_probe_schema_mismatch") {
    return "rerun the SSH stdin fallback and inspect the local probe version plus remote Python stdout contract before OKR review";
  }
  if (reason === "ssh_auth_failed") {
    return "fix SSH key or root login access for the upper computer before rerunning the read-only collector";
  }
  if (reason === "ssh_connection_refused" || reason === "ssh_timeout" || reason === "ssh_network_unreachable") {
    return "verify upper-computer LAN route, SSH port, and sshd status before rerunning the read-only collector";
  }
  if (reason === "remote_stdout_bad_json" || reason === "remote_probe_schema_mismatch") {
    return "rerun the remote Python stdlib probe and inspect the deployed script version before OKR review";
  }
  return "rerun the read-only SSH collector after fixing the classified blocker";
}

function parseProbeStdout(stdout) {
  try {
    return JSON.parse(String(stdout || "").trim());
  } catch {
    return null;
  }
}

function blockedReasonForBadStdout(executionMode) {
  return executionMode === "stdin_fallback" ? "ssh_stdin_fallback_stdout_bad_json" : "remote_stdout_bad_json";
}

function blockedReasonForSchemaMismatch(executionMode) {
  return executionMode === "stdin_fallback" ? "ssh_stdin_fallback_probe_schema_mismatch" : "remote_probe_schema_mismatch";
}

function blockedReasonForRemoteFailure(executionMode, text) {
  const classified = classifySshFailure(text);
  if (executionMode === "stdin_fallback" && classified === "remote_probe_failed") {
    return "ssh_stdin_fallback_probe_failed";
  }
  return classified;
}

function parseRemoteProbe(plan, sshResult, collectionOptions = {}) {
  const executionMode = collectionOptions.executionMode || "installed_script";
  if (sshResult.error) {
    return buildBlockedArtifact(plan, executionMode === "stdin_fallback" ? "ssh_stdin_fallback_probe_failed" : "ssh_spawn_failed", collectionOptions);
  }
  if (sshResult.code === 41) {
    return buildBlockedArtifact(plan, "remote_repo_root_missing", { ...collectionOptions, remoteExitCode: sshResult.code });
  }
  if (sshResult.code === 42) {
    return buildBlockedArtifact(plan, "remote_repo_present_but_probe_script_missing", { ...collectionOptions, remoteExitCode: sshResult.code });
  }
  const parsed = parseProbeStdout(sshResult.stdout);
  if (parsed && typeof parsed === "object" && !Array.isArray(parsed) && parsed.schema === PROBE_SCHEMA) {
    // Python probe 用 exit 2 表达 fail_closed；stdout 有合法 schema 时仍应作为已采集 artifact 处理。
    return decorateRemoteProbe(plan, parsed, { ...collectionOptions, remoteExitCode: sshResult.code });
  }
  if (sshResult.code !== 0) {
    return buildBlockedArtifact(plan, blockedReasonForRemoteFailure(executionMode, `${sshResult.stderr}\n${sshResult.stdout}`), {
      ...collectionOptions,
      remoteExitCode: sshResult.code,
    });
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed) || parsed.schema !== PROBE_SCHEMA) {
    const reason = parsed ? blockedReasonForSchemaMismatch(executionMode) : blockedReasonForBadStdout(executionMode);
    return buildBlockedArtifact(plan, reason, { ...collectionOptions, remoteExitCode: sshResult.code });
  }
  return decorateRemoteProbe(plan, parsed, { ...collectionOptions, remoteExitCode: sshResult.code });
}

function blockedReasonForProbeSyncFailure(sshResult) {
  // 同步失败优先复用 SSH 分类；远端 shell 步骤失败则归到 probe sync 范围内。
  if (sshResult.error) {
    return "remote_probe_sync_failed";
  }
  if (sshResult.code === 41) {
    return "remote_repo_root_missing";
  }
  if (sshResult.code === 49) {
    return "remote_probe_sync_target_outside_allowed_path";
  }
  const classified = classifySshFailure(`${sshResult.stderr}\n${sshResult.stdout}`);
  return classified === "remote_probe_failed" ? "remote_probe_sync_failed" : classified;
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

function decorateRemoteProbe(plan, remoteProbe, collectionOptions = {}) {
  const remoteRunner = typeof remoteProbe.runner === "string" ? remoteProbe.runner : "unknown";
  const blocked = Array.isArray(remoteProbe.blocked_reasons) ? remoteProbe.blocked_reasons.map((item) => safeText(item)).slice(0, 20) : [];
  const tokenReason = remoteProbe.token_status === "present" ? [] : ["remote_bearer_token_absent"];
  const cloudReason = plan.cloudBaseUrl ? [] : ["cloud_base_url_not_configured"];
  const pcReason = pcBaseUrlBlockedReason(plan);
  const endpoints = Array.isArray(remoteProbe.endpoints)
    ? remoteProbe.endpoints.map((endpoint) => {
        if (!pcReason || endpoint?.name !== "pc_aggregate") {
          return endpoint;
        }
        const endpointBlockedReasons = Array.isArray(endpoint.blocked_reasons) ? endpoint.blocked_reasons.map((item) => safeText(item)) : [];
        return {
          ...endpoint,
          failure_category: pcReason,
          blocked_reasons: [...new Set([pcReason, ...endpointBlockedReasons])],
        };
      })
    : remoteProbe.endpoints;
  // token/cloud 缺口不覆盖远端 probe 事实，只追加为 collector 可见 blocked reason。
  return {
    ...remoteProbe,
    runner: `pc_upper_ssh_collector+${safeText(remoteRunner)}`,
    remote_runner: safeText(remoteRunner),
    collector_execution_mode: collectionOptions.executionMode || "installed_script",
    collector_schema: COLLECTOR_SCHEMA,
    source_host_role: "upper_computer",
    viewpoint: "upper_computer_via_pc_ssh_readonly",
    pc_base_url: pcReason ? "not_configured_for_upper_ssh" : remoteProbe.pc_base_url,
    credentials_redacted: remoteProbe.credentials_redacted !== false,
    endpoints,
    ssh_collection: sshCollectionSummary(plan, "collected", null, collectionOptions),
    blocked_reasons: [...new Set([...blocked, ...(pcReason ? [pcReason] : []), ...tokenReason, ...cloudReason])].slice(0, 20),
    safe_to_control: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

function runSsh(plan, spawnImpl = spawn, options = {}) {
  return new Promise((resolve) => {
    const useStdin = typeof options.stdin === "string";
    const args =
      options.executionMode === "stdin_fallback"
        ? buildStdinFallbackSshArgs(plan)
        : options.executionMode === "sync_remote_probe"
          ? buildProbeInstallSshArgs(plan)
          : buildSshArgs(plan);
    const child = spawnImpl("ssh", args, { cwd: workstationRoot, stdio: [useStdin ? "pipe" : "ignore", "pipe", "pipe"] });
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
    if (useStdin) {
      // stdin 只承载本地 probe 源码，不承载 token；写完立即关闭，避免 SSH 进程挂住。
      child.stdin?.end(options.stdin);
    }
  });
}

async function readLocalProbeSource() {
  try {
    // 本地 probe 是 repo 内固定文件；不从 CLI 传路径，防止 operator 误把任意脚本喂给上位机。
    return await fs.readFile(localProbeScript, "utf8");
  } catch {
    return null;
  }
}

async function syncRemoteProbeToUpper(plan, spawnImpl) {
  const target = remoteProbeSyncTarget(plan);
  if (!target.target_allowed) {
    return {
      status: "blocked",
      sshExecuted: false,
      remoteFileWriteAttempted: false,
      remoteFileWriteExecuted: false,
      remoteExitCode: null,
      failureCategory: target.blocked_reason,
    };
  }
  const localSource = await readLocalProbeSource();
  if (!localSource) {
    return {
      status: "blocked",
      sshExecuted: false,
      remoteFileWriteAttempted: false,
      remoteFileWriteExecuted: false,
      remoteExitCode: null,
      failureCategory: "local_sync_probe_source_missing",
    };
  }
  const sshResult = await runSsh(plan, spawnImpl, { executionMode: "sync_remote_probe", stdin: localSource });
  const remoteExitCode = typeof sshResult.code === "number" ? sshResult.code : null;
  if (!sshResult.error && sshResult.code === 0) {
    return {
      status: "synced",
      sshExecuted: true,
      remoteFileWriteAttempted: true,
      remoteFileWriteExecuted: true,
      remoteExitCode,
      failureCategory: null,
    };
  }
  return {
    status: "blocked",
    sshExecuted: true,
    remoteFileWriteAttempted: true,
    remoteFileWriteExecuted: false,
    remoteExitCode,
    failureCategory: blockedReasonForProbeSyncFailure(sshResult),
  };
}

async function writeArtifact(result, outputPath) {
  // 非 dry-run 的 blocked/observed 结果都落同一个 artifact，acceptance queue 只读这个文件。
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
}

export function buildDryRunResult(plan) {
  const pcReason = pcBaseUrlBlockedReason(plan);
  const preflight = buildPreflight(plan);
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
    stdin_fallback: {
      supported: true,
      execution_mode: "stdin_fallback",
      ssh_args: buildStdinFallbackSshArgs(plan),
      local_probe_ref: "cloud-relay/scripts/o5_o6_external_live_probe.py",
      streams_local_probe_over_ssh_stdin: true,
      remote_file_write_executed: false,
      contains_bearer_token: false,
    },
    sync_remote_probe: {
      ...remoteProbeSyncSummary(plan),
      ssh_args: plan.syncRemoteProbe ? buildProbeInstallSshArgs(plan) : [],
      dry_run_no_ssh: true,
      dry_run_no_write: true,
      remote_file_write_executed: false,
    },
    pc_base_url_contract: {
      configured_for_upper_ssh: !pcReason,
      source: plan.pcBaseUrlSource || "absent",
      blocked_reason: pcReason,
      next_action: pcReason ? pcBaseUrlNextAction() : null,
    },
    preflight,
    failure_classification: preflight.failure_classification,
    safety_policy: {
      no_post: true,
      no_robot_control: true,
      no_hardware_read: true,
      forbidden_paths: ["/robots/*", "/cmd_vel"],
      bearer_source: "remote_environment_only",
    },
    blocked_reasons: [
      "dry_run_no_ssh_no_network_no_artifact",
      ...(plan.syncRemoteProbe ? ["remote_probe_sync_not_executed_dry_run"] : []),
      ...(pcReason ? [pcReason] : []),
    ],
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
  const syncResult = effectivePlan.syncRemoteProbe ? await syncRemoteProbeToUpper(effectivePlan, spawnImpl) : null;
  if (syncResult && syncResult.status !== "synced") {
    const result = buildBlockedArtifact(effectivePlan, syncResult.failureCategory, {
      executionMode: "sync_remote_probe",
      attemptedExecutionModes: ["sync_remote_probe"],
      remoteExitCode: syncResult.remoteExitCode,
      remoteProbeSync: syncResult,
    });
    result.artifact_written = true;
    await writeArtifact(result, effectivePlan.outputPath);
    return result;
  }
  const installedOptions = {
    executionMode: "installed_script",
    attemptedExecutionModes: effectivePlan.syncRemoteProbe ? ["sync_remote_probe", "installed_script"] : ["installed_script"],
    remoteProbeSync: syncResult,
  };
  const installedResult = await runSsh(effectivePlan, spawnImpl, installedOptions);
  let result;
  if (effectivePlan.syncRemoteProbe && !installedResult.error && installedResult.code === 42) {
    result = buildBlockedArtifact(effectivePlan, "remote_probe_sync_did_not_materialize_script", {
      ...installedOptions,
      remoteExitCode: installedResult.code,
    });
  } else if (!installedResult.error && installedResult.code === 42) {
    const attemptedExecutionModes = ["installed_script", "stdin_fallback"];
    const fallbackReason = "remote_repo_present_but_probe_script_missing";
    const localSource = await readLocalProbeSource();
    if (!localSource) {
      result = buildBlockedArtifact(effectivePlan, "local_stdin_probe_source_missing", {
        executionMode: "stdin_fallback",
        attemptedExecutionModes,
        fallbackReason,
      });
    } else {
      const fallbackOptions = {
        executionMode: "stdin_fallback",
        attemptedExecutionModes,
        fallbackReason,
      };
      result = parseRemoteProbe(effectivePlan, await runSsh(effectivePlan, spawnImpl, { ...fallbackOptions, stdin: localSource }), fallbackOptions);
    }
  } else {
    result = parseRemoteProbe(effectivePlan, installedResult, installedOptions);
  }
  result.ssh_collection = result.ssh_collection || sshCollectionSummary(effectivePlan, "collected", null, installedOptions);
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
      syncRemoteProbe: false,
      sshTarget: DEFAULT_SSH_TARGET,
      sshPort: DEFAULT_SSH_PORT,
      remoteRoot: DEFAULT_REMOTE_ROOT,
      remoteScript: DEFAULT_REMOTE_SCRIPT,
      pcBaseUrl: "",
      pcBaseUrlExplicit: false,
      pcBaseUrlSource: "absent",
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
