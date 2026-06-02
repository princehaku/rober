#!/usr/bin/env node
import fs from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCHEMA = "trashbot.o7.camera_service_readiness.v1";
const CAMERA_SYSTEMD_UNIT = "trashbot-local-webrtc-camera.service";
const DEFAULT_BASE_URL = "http://192.168.1.11:8088/";
const DEFAULT_SSH_TARGET = "root@192.168.1.11";
const DEFAULT_SSH_PORT = "37878";
const HTTP_TIMEOUT_MS = 2500;
const SSH_TIMEOUT_SECONDS = 5;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const workstationRoot = path.resolve(__dirname, "..");
const defaultOutput = path.join(workstationRoot, ".workstation-runtime", "o7-camera-service-readiness.json");

function nowIso() {
  return new Date().toISOString();
}

function outputRef(outputPath) {
  // artifact 对 operator 显示 repo 内相对路径，避免把本机绝对路径变成接口契约。
  const relative = path.relative(workstationRoot, outputPath);
  return relative.startsWith("..") ? path.basename(outputPath) : relative.split(path.sep).join("/");
}

function printJson(payload) {
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

function takeValue(argv, index, name) {
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
  // 超时和端口必须严格整数，避免现场误输入被 Node 隐式转换成危险默认值。
  if (!/^\d+$/.test(String(value))) {
    throw new Error(`${name}_must_be_integer`);
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed <= 0) {
    throw new Error(`${name}_must_be_positive_integer`);
  }
  return parsed;
}

function normalizeBaseUrl(raw) {
  const value = String(raw || DEFAULT_BASE_URL).trim();
  const parsed = new URL(value);
  if (parsed.protocol !== "http:") {
    throw new Error("base_url_protocol_not_allowed");
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error("base_url_must_not_include_credentials_query_or_hash");
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "/");
  return parsed.toString();
}

export function buildCollectorPlan({ argv = [], env = process.env } = {}) {
  let dryRun = false;
  let baseUrl = env.ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL || env.ROBER_O7_CAMERA_SERVICE_BASE_URL || DEFAULT_BASE_URL;
  let sshTarget = env.ROBER_O7_CAMERA_SERVICE_SSH_TARGET || DEFAULT_SSH_TARGET;
  let sshPort = env.ROBER_O7_CAMERA_SERVICE_SSH_PORT || DEFAULT_SSH_PORT;
  let outputPath = env.ROBER_O7_CAMERA_SERVICE_READINESS_OUTPUT || defaultOutput;
  let httpTimeoutMs = env.ROBER_O7_CAMERA_SERVICE_HTTP_TIMEOUT_MS || String(HTTP_TIMEOUT_MS);
  let sshTimeoutSeconds = env.ROBER_O7_CAMERA_SERVICE_SSH_TIMEOUT_SECONDS || String(SSH_TIMEOUT_SECONDS);
  let skipHttp = false;
  let skipSsh = false;

  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--dry-run") {
      dryRun = true;
      continue;
    }
    if (item === "--skip-http") {
      skipHttp = true;
      continue;
    }
    if (item === "--skip-ssh") {
      skipSsh = true;
      continue;
    }
    const base = takeValue(argv, index, "--base-url");
    if (base) {
      baseUrl = base.value;
      index += base.consumed - 1;
      continue;
    }
    const target = takeValue(argv, index, "--ssh-target");
    if (target) {
      sshTarget = target.value;
      index += target.consumed - 1;
      continue;
    }
    const port = takeValue(argv, index, "--ssh-port");
    if (port) {
      sshPort = port.value;
      index += port.consumed - 1;
      continue;
    }
    const output = takeValue(argv, index, "--output");
    if (output) {
      outputPath = output.value;
      index += output.consumed - 1;
      continue;
    }
    const httpTimeout = takeValue(argv, index, "--http-timeout-ms");
    if (httpTimeout) {
      httpTimeoutMs = httpTimeout.value;
      index += httpTimeout.consumed - 1;
      continue;
    }
    const sshTimeout = takeValue(argv, index, "--ssh-timeout-seconds");
    if (sshTimeout) {
      sshTimeoutSeconds = sshTimeout.value;
      index += sshTimeout.consumed - 1;
      continue;
    }
    throw new Error(`unknown_argument:${item}`);
  }

  return {
    dryRun,
    baseUrl: normalizeBaseUrl(baseUrl),
    sshTarget: String(sshTarget || DEFAULT_SSH_TARGET).trim(),
    sshPort: String(parsePositiveInteger(sshPort, "ssh_port")),
    outputPath: path.resolve(outputPath),
    httpTimeoutMs: parsePositiveInteger(httpTimeoutMs, "http_timeout_ms"),
    sshTimeoutSeconds: parsePositiveInteger(sshTimeoutSeconds, "ssh_timeout_seconds"),
    skipHttp,
    skipSsh,
  };
}

function baseResult(plan, status, blockedReasons) {
  return {
    schema: SCHEMA,
    schema_version: 1,
    status,
    executed_at: nowIso(),
    dry_run: plan.dryRun,
    base_url: plan.baseUrl,
    ssh_target: plan.sshTarget,
    ssh_port: Number(plan.sshPort),
    output_ref: outputRef(plan.outputPath),
    artifact_written: false,
    http_probe: {
      health: { status: "not_executed", http_status: null, error_category: null, service_status: null },
      devices: { status: "not_executed", http_status: null, error_category: null, device_count: null },
    },
    ssh_probe: {
      status: "not_executed",
      error_category: null,
      uname: null,
      listening_summary: [],
      process_summary: [],
      unit_summary: [],
      script_summary: [],
      systemd_unit: {
        name: CAMERA_SYSTEMD_UNIT,
        installed: null,
        load_state: null,
        active_state: null,
        sub_state: null,
        main_pid: null,
        fragment_path_present: null,
      },
      camera_port_listening: null,
      process_hint_present: null,
      service_unit_hint_present: null,
      service_unit_installed: null,
      service_unit_active: null,
      remote_script_present: null,
    },
    readiness: {
      ready_for_long_stability: false,
      http_health_unreachable: false,
      http_connection_refused: false,
      ssh_unreachable: false,
      port_not_listening: false,
      process_hint_missing: false,
      service_unit_missing_or_inactive: false,
      service_unit_not_installed: false,
      service_unit_inactive: false,
      remote_script_missing: false,
      action_category: "not_observed",
      safe_start_command_hint: null,
      blocked_reasons: blockedReasons,
      next_action:
        "Run this readiness collector until HTTP health, SSH, listening port, and process hints are observed before o7:browser-long-stability.",
    },
    network_probe_executed: false,
    ssh_probe_executed: false,
    post_executed: false,
    webrtc_session_created: false,
    offer_executed: false,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
  };
}

export function buildDryRunResult(plan) {
  return {
    ...baseResult(plan, "dry_run", ["dry_run_no_network_no_ssh_no_post_no_webrtc_no_artifact"]),
    planned_http_gets: [new URL("/health", plan.baseUrl).toString(), new URL("/devices", plan.baseUrl).toString()],
    planned_ssh_readonly_checks: ["uname", "ss_or_netstat_listening_summary", "camera_process_summary", `systemctl_show_${CAMERA_SYSTEMD_UNIT}`],
    network_probe_executed: false,
    ssh_probe_executed: false,
    post_executed: false,
    webrtc_session_created: false,
    offer_executed: false,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
  };
}

function classifyFetchError(error) {
  const text = error instanceof Error ? error.message : String(error || "");
  if (/ECONNREFUSED|ERR_CONNECTION_REFUSED|fetch failed/i.test(text) && /ECONNREFUSED/i.test(text)) {
    return "http_connection_refused";
  }
  if (/Timeout|timed out|AbortError/i.test(text)) {
    return "http_timeout";
  }
  if (/ENOTFOUND|ERR_NAME_NOT_RESOLVED/i.test(text)) {
    return "http_dns_not_resolved";
  }
  if (/EHOSTUNREACH|ENETUNREACH|ERR_ADDRESS_UNREACHABLE/i.test(text)) {
    return "http_network_unreachable";
  }
  return "http_unreachable";
}

async function fetchJsonEndpoint(baseUrl, endpoint, timeoutMs) {
  try {
    // HTTP 只允许 GET 板端只读状态端点；不会触发 /offer、session 或控制路径。
    const response = await fetch(new URL(endpoint, baseUrl), {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(timeoutMs),
    });
    const text = await response.text();
    let payload = null;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      return { status: "bad_json", http_status: response.status, error_category: "bad_json", payload: null };
    }
    return {
      status: response.ok ? "reachable" : "http_error",
      http_status: response.status,
      error_category: response.ok ? null : `http_${response.status}`,
      payload,
    };
  } catch (error) {
    const category = classifyFetchError(error);
    return { status: "unreachable", http_status: null, error_category: category, payload: null };
  }
}

function safeMetricValue(value) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    return value.replace(/\s+/g, " ").slice(0, 120);
  }
  return null;
}

function summarizeHealthPayload(payload) {
  const object = payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
  return {
    service_status: safeMetricValue(object.status),
    active_peer_connections: safeMetricValue(object.active_peer_connections),
    system_metrics_present: Boolean(object.system_metrics && typeof object.system_metrics === "object"),
    stability_metrics_present: Boolean(object.stability_metrics && typeof object.stability_metrics === "object"),
  };
}

function summarizeDevicesPayload(payload) {
  const object = payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
  const devices = Array.isArray(object.devices) ? object.devices : [];
  return {
    device_count: devices.length,
    device_kinds: devices
      .map((item) => (item && typeof item === "object" ? safeMetricValue(item.kind ?? item.type ?? item.name) : null))
      .filter((item) => typeof item === "string")
      .slice(0, 12),
  };
}

function buildReadonlySshCommand() {
  // SSH 侧只做系统、监听端口、进程摘要；不读 /dev、不读串口、不碰 ROS2 或底盘控制。
  return [
    "printf '__UNAME__\\n'",
    "uname -a 2>/dev/null || true",
    "printf '__LISTEN__\\n'",
    "(ss -lntp 2>/dev/null || netstat -lntp 2>/dev/null || true) | head -80",
    "printf '__PROCESS__\\n'",
    "ps -eo pid,comm,args 2>/dev/null | grep -Ei 'webrtc|camera|uvicorn|node|python|8088' | grep -v grep | head -40 || true",
    "printf '__UNITS__\\n'",
    "systemctl list-units --type=service --all --no-pager 2>/dev/null | grep -Ei 'camera|webrtc|rtc|video' | head -40 || true",
    "printf '__CAMERA_UNIT__\\n'",
    `systemctl show ${CAMERA_SYSTEMD_UNIT} --no-pager --property=LoadState,ActiveState,SubState,MainPID,FragmentPath 2>/dev/null || true`,
    "printf '__SCRIPTS__\\n'",
    "find /root/rober/onboard/scripts /home /opt /usr/local -maxdepth 4 -type f \\( -iname '*webrtc*' -o -iname '*camera*' -o -iname '*rtc*' \\) 2>/dev/null | head -40 || true",
  ].join("; ");
}

export function parseSystemdUnit(lines) {
  const fields = {};
  for (const line of lines) {
    const index = line.indexOf("=");
    if (index <= 0) {
      continue;
    }
    fields[line.slice(0, index)] = line.slice(index + 1);
  }
  const loadState = fields.LoadState || null;
  const activeState = fields.ActiveState || null;
  const subState = fields.SubState || null;
  const mainPid = fields.MainPID && /^\d+$/.test(fields.MainPID) ? Number(fields.MainPID) : null;
  const fragmentPath = fields.FragmentPath || "";
  return {
    name: CAMERA_SYSTEMD_UNIT,
    installed: loadState === "loaded",
    load_state: loadState,
    active_state: activeState,
    sub_state: subState,
    main_pid: mainPid,
    fragment_path_present: Boolean(fragmentPath),
  };
}

function parseSection(stdout, section) {
  const marker = `__${section}__`;
  const nextMarker = /\n__[A-Z_]+__\n/g;
  const start = stdout.indexOf(marker);
  if (start < 0) {
    return [];
  }
  const bodyStart = start + marker.length;
  nextMarker.lastIndex = bodyStart;
  const next = nextMarker.exec(stdout);
  const body = stdout.slice(bodyStart, next ? next.index : undefined);
  return body
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 40);
}

function classifySshError(text) {
  if (/No route to host|Network is unreachable|EHOSTUNREACH|ENETUNREACH/i.test(text)) {
    return "ssh_network_unreachable";
  }
  if (/Connection refused|connect.*refused/i.test(text)) {
    return "ssh_connection_refused";
  }
  if (/timed out|Connection timeout|ConnectTimeout/i.test(text)) {
    return "ssh_timeout";
  }
  if (/Permission denied|publickey|Authentication/i.test(text)) {
    return "ssh_auth_failed";
  }
  return "ssh_unreachable";
}

async function runSshProbe(plan) {
  return await new Promise((resolve) => {
    const child = spawn(
      "ssh",
      [
        "-o",
        "BatchMode=yes",
        "-o",
        `ConnectTimeout=${plan.sshTimeoutSeconds}`,
        "-p",
        plan.sshPort,
        plan.sshTarget,
        "sh",
        "-lc",
        buildReadonlySshCommand(),
      ],
      { cwd: workstationRoot, stdio: ["ignore", "pipe", "pipe"] },
    );
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += String(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });
    child.on("error", (error) => {
      resolve({ status: "unreachable", error_category: error.message || "ssh_spawn_failed", stdout: "", stderr: "" });
    });
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ status: "reachable", error_category: null, stdout, stderr });
      } else {
        resolve({ status: "unreachable", error_category: classifySshError(`${stderr}\n${stdout}`), stdout, stderr });
      }
    });
  });
}

export function summarizeSshProbe(probe) {
  const listen = parseSection(probe.stdout, "LISTEN");
  const processes = parseSection(probe.stdout, "PROCESS");
  const units = parseSection(probe.stdout, "UNITS");
  const cameraUnit = parseSystemdUnit(parseSection(probe.stdout, "CAMERA_UNIT"));
  const scripts = parseSection(probe.stdout, "SCRIPTS");
  const uname = parseSection(probe.stdout, "UNAME")[0] ?? null;
  const listeningSummary = listen.filter((line) => /:8088\b|LISTEN|tcp/i.test(line)).slice(0, 20);
  const processSummary = processes.slice(0, 20);
  const cameraPortListening = probe.status === "reachable" ? listeningSummary.some((line) => /:8088\b/.test(line)) : null;
  const serviceProcessPattern = /local_webrtc_camera_smoke|webrtc|camera.*smoke|uvicorn.*8088|aiohttp.*8088|node.*8088|python.*8088/i;
  const processHintPresent =
    probe.status === "reachable" ? processSummary.some((line) => serviceProcessPattern.test(line)) : null;
  const serviceUnitHintPresent =
    probe.status === "reachable"
      ? cameraUnit.installed === true || units.some((line) => /camera|webrtc|rtc|video/i.test(line) && !/smartcard/i.test(line))
      : null;
  const serviceUnitInstalled = probe.status === "reachable" ? cameraUnit.installed === true : null;
  const serviceUnitActive = probe.status === "reachable" ? cameraUnit.active_state === "active" : null;
  const remoteScriptPresent =
    probe.status === "reachable" ? scripts.some((line) => /local_webrtc_camera_smoke\.(sh|py)$/i.test(line)) : null;
  return {
    status: probe.status,
    error_category: probe.error_category,
    uname,
    listening_summary: listeningSummary,
    process_summary: processSummary,
    unit_summary: units.filter((line) => !/smartcard/i.test(line)).slice(0, 20),
    script_summary: scripts.slice(0, 20),
    systemd_unit: cameraUnit,
    camera_port_listening: cameraPortListening,
    process_hint_present: processHintPresent,
    service_unit_hint_present: serviceUnitHintPresent,
    service_unit_installed: serviceUnitInstalled,
    service_unit_active: serviceUnitActive,
    remote_script_present: remoteScriptPresent,
  };
}

function deriveActionCategory(ssh, unique) {
  // action_category 是 operator 下一步机器分类；它只基于只读 HTTP/SSH 证据，不启动远端服务。
  if (unique.length === 0) {
    return "ready_for_long_stability";
  }
  if (ssh.status === "unreachable") {
    return "ssh_unreachable";
  }
  if (ssh.process_hint_present === true && ssh.camera_port_listening === false) {
    return "service_process_present_but_port_closed";
  }
  if (ssh.service_unit_installed === false) {
    return "service_unit_not_installed";
  }
  if (ssh.service_unit_active === false) {
    return "service_unit_inactive";
  }
  if (ssh.service_unit_hint_present === false && ssh.remote_script_present === true) {
    return "remote_script_present_but_service_inactive";
  }
  if (ssh.service_unit_hint_present === false) {
    return "service_unit_missing_or_inactive";
  }
  if (ssh.remote_script_present === false) {
    return "remote_script_missing";
  }
  if (unique.includes("http_connection_refused") || unique.includes("port_not_listening")) {
    return "service_not_listening_on_8088";
  }
  return "readiness_blocked";
}

function safeStartCommandHint(actionCategory, ssh) {
  // 这里只给人工可复制的安全启动线索，不通过 collector 自动执行，避免把诊断工具变成后台部署器。
  if ((actionCategory === "service_unit_not_installed" || actionCategory === "service_unit_inactive") && ssh.remote_script_present === true) {
    return "ssh <board-lan-host> -p <ssh-port> 'cd <rober-worktree> && bash onboard/scripts/install_o7_camera_service.sh --dry-run && bash onboard/scripts/install_o7_camera_service.sh'";
  }
  if (actionCategory === "remote_script_present_but_service_inactive" && ssh.remote_script_present === true) {
    return "ssh <board-lan-host> -p <ssh-port> 'cd <rober-worktree> && bash onboard/scripts/install_o7_camera_service.sh --dry-run'";
  }
  return null;
}

export function deriveReadiness(result) {
  const blocked = [];
  const health = result.http_probe.health;
  const devices = result.http_probe.devices;
  const ssh = result.ssh_probe;
  if (health.status !== "reachable") {
    blocked.push(health.error_category === "http_connection_refused" ? "http_connection_refused" : "http_health_unreachable");
  }
  if (devices.status !== "reachable") {
    blocked.push(devices.error_category === "http_connection_refused" ? "http_devices_connection_refused" : "http_devices_unreachable");
  }
  if (ssh.status === "unreachable") {
    blocked.push("ssh_unreachable");
  }
  if (ssh.camera_port_listening === false) {
    blocked.push("port_not_listening");
  }
  if (ssh.process_hint_present === false) {
    blocked.push("process_hint_missing");
  }
  if (ssh.service_unit_hint_present === false) {
    blocked.push("service_unit_missing_or_inactive");
  }
  if (ssh.service_unit_installed === false) {
    blocked.push("service_unit_not_installed");
  }
  if (ssh.service_unit_active === false) {
    blocked.push("service_unit_inactive");
  }
  if (ssh.remote_script_present === false) {
    blocked.push("remote_script_missing");
  }

  const unique = [...new Set(blocked)];
  const ready = unique.length === 0 && health.status === "reachable" && devices.status === "reachable" && ssh.status === "reachable";
  const actionCategory = deriveActionCategory(ssh, unique);
  return {
    ready_for_long_stability: ready,
    http_health_unreachable: health.status !== "reachable",
    http_connection_refused: unique.includes("http_connection_refused"),
    ssh_unreachable: ssh.status === "unreachable",
    port_not_listening: unique.includes("port_not_listening"),
    process_hint_missing: unique.includes("process_hint_missing"),
    service_unit_missing_or_inactive: ssh.service_unit_hint_present === false,
    service_unit_not_installed: unique.includes("service_unit_not_installed"),
    service_unit_inactive: unique.includes("service_unit_inactive"),
    remote_script_missing: unique.includes("remote_script_missing"),
    action_category: actionCategory,
    safe_start_command_hint: safeStartCommandHint(actionCategory, ssh),
    blocked_reasons: ready ? [] : unique,
    next_action: ready
      ? "Run npm run o7:browser-long-stability and keep the generated browser smoke artifact for OKR review."
      : actionCategory === "service_unit_not_installed"
        ? "Install the versioned trashbot-local-webrtc-camera systemd unit with install_o7_camera_service.sh, then rerun readiness."
      : actionCategory === "service_unit_inactive"
        ? "Start or restart trashbot-local-webrtc-camera.service, then rerun readiness before long stability."
      : actionCategory === "remote_script_present_but_service_inactive"
        ? "Board SSH is reachable and the local WebRTC camera script exists, but no 8088 listener or service unit is active; start the script/service manually, then rerun readiness."
      : "Fix board HTTP/WebRTC camera service readiness first; do not blindly re-run the 180s browser stability collector.",
  };
}

async function writeArtifact(result, outputPath) {
  // 非 dry-run 才落 readiness artifact；acceptance API 仍只读 browser smoke，不会自动执行这里。
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
}

function failClosedResult(plan, reason) {
  return {
    ...baseResult(plan, "fail_closed", [reason]),
    readiness: {
      ...baseResult(plan, "fail_closed", [reason]).readiness,
      blocked_reasons: [reason],
    },
  };
}

export async function runCollector({ argv = process.argv.slice(2), env = process.env } = {}) {
  let plan;
  try {
    plan = buildCollectorPlan({ argv, env });
  } catch (error) {
    const fallback = {
      dryRun: false,
      baseUrl: DEFAULT_BASE_URL,
      sshTarget: DEFAULT_SSH_TARGET,
      sshPort: DEFAULT_SSH_PORT,
      outputPath: defaultOutput,
    };
    printJson(failClosedResult(fallback, error instanceof Error ? error.message : "collector_argument_invalid"));
    return 2;
  }

  if (plan.dryRun) {
    printJson(buildDryRunResult(plan));
    return 0;
  }

  const result = baseResult(plan, "blocked", []);
  if (!plan.skipHttp) {
    result.network_probe_executed = true;
    const [health, devices] = await Promise.all([
      fetchJsonEndpoint(plan.baseUrl, "/health", plan.httpTimeoutMs),
      fetchJsonEndpoint(plan.baseUrl, "/devices", plan.httpTimeoutMs),
    ]);
    result.http_probe.health = { ...health, ...summarizeHealthPayload(health.payload) };
    result.http_probe.devices = { ...devices, ...summarizeDevicesPayload(devices.payload) };
    delete result.http_probe.health.payload;
    delete result.http_probe.devices.payload;
  }
  if (!plan.skipSsh) {
    result.ssh_probe_executed = true;
    result.ssh_probe = summarizeSshProbe(await runSshProbe(plan));
  }
  result.readiness = deriveReadiness(result);
  result.status = result.readiness.ready_for_long_stability ? "ready_for_long_stability" : "blocked";
  result.artifact_written = true;
  await writeArtifact(result, plan.outputPath);
  printJson(result);
  return result.readiness.ready_for_long_stability ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runCollector().then((code) => {
    process.exitCode = code;
  });
}
