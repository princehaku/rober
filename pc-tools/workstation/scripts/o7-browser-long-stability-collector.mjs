#!/usr/bin/env node
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCHEMA = "trashbot.o7.browser_long_stability_collector.v1";
const MIN_STABILITY_MS = 180000;
const DEFAULT_BASE_URL = "http://192.168.1.11:8088/";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const workstationRoot = path.resolve(__dirname, "..");
const delegatedScript = path.join(__dirname, "o7-browser-playback-smoke.mjs");
const defaultOutput = path.join(workstationRoot, ".workstation-runtime", "o7-browser-playback-smoke.json");

function nowIso() {
  return new Date().toISOString();
}

function failClosedResult(reason, overrides = {}) {
  // collector 自身的失败也必须给机器可读 JSON，避免 operator 把静默失败当成未执行。
  return {
    schema: SCHEMA,
    status: "fail_closed",
    executed_at: nowIso(),
    dry_run: false,
    delegated_script: "scripts/o7-browser-playback-smoke.mjs",
    blocked_reason: reason,
    stability_ms: null,
    output_ref: null,
    artifact_written: false,
    network_probe_executed: false,
    post_executed: false,
    webrtc_session_created: false,
    offer_executed_by_browser: false,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    ...overrides,
  };
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
  // 用严格整数解析挡住 "180000abc" 这类误输入，避免真实采集窗口被悄悄缩短。
  if (!/^\d+$/.test(String(value))) {
    throw new Error(`${name}_must_be_integer_ms`);
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed <= 0) {
    throw new Error(`${name}_must_be_positive_integer_ms`);
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
  let baseUrl = env.ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL || env.ROBER_O7_BROWSER_SMOKE_BASE_URL || DEFAULT_BASE_URL;
  let outputPath = env.ROBER_O7_BROWSER_SMOKE_OUTPUT || defaultOutput;
  let stabilityMs = env.ROBER_O7_BROWSER_SMOKE_STABILITY_MS || String(MIN_STABILITY_MS);
  const passthroughArgs = [];

  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--dry-run") {
      dryRun = true;
      continue;
    }
    const stability = takeValue(argv, index, "--stability-ms");
    if (stability) {
      stabilityMs = stability.value;
      index += stability.consumed - 1;
      continue;
    }
    const output = takeValue(argv, index, "--output");
    if (output) {
      outputPath = output.value;
      index += output.consumed - 1;
      continue;
    }
    const base = takeValue(argv, index, "--base-url");
    if (base) {
      baseUrl = base.value;
      index += base.consumed - 1;
      continue;
    }
    passthroughArgs.push(item);
  }

  const requestedStabilityMs = parsePositiveInteger(stabilityMs, "stability_ms");
  const effectiveStabilityMs = Math.max(MIN_STABILITY_MS, requestedStabilityMs);
  return {
    dryRun,
    baseUrl: normalizeBaseUrl(baseUrl),
    outputPath: path.resolve(outputPath),
    requestedStabilityMs,
    effectiveStabilityMs,
    passthroughArgs,
  };
}

export function buildDryRunResult(plan) {
  return {
    schema: SCHEMA,
    status: "dry_run",
    executed_at: nowIso(),
    dry_run: true,
    delegated_script: "scripts/o7-browser-playback-smoke.mjs",
    blocked_reason: "dry_run_no_network_no_post_no_webrtc_no_artifact",
    base_url: plan.baseUrl,
    stability_ms: plan.effectiveStabilityMs,
    min_required_stability_ms: MIN_STABILITY_MS,
    output_ref: path.relative(workstationRoot, plan.outputPath).split(path.sep).join("/"),
    artifact_written: false,
    planned_env: {
      ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL: plan.baseUrl,
      ROBER_O7_BROWSER_SMOKE_STABILITY_MS: String(plan.effectiveStabilityMs),
      ROBER_O7_BROWSER_SMOKE_OUTPUT: path.relative(workstationRoot, plan.outputPath).split(path.sep).join("/"),
    },
    planned_command: "npm run o7:browser-smoke",
    network_probe_executed: false,
    post_executed: false,
    webrtc_session_created: false,
    offer_executed_by_browser: false,
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
  };
}

export async function runCollector({ argv = process.argv.slice(2), env = process.env } = {}) {
  let plan;
  try {
    plan = buildCollectorPlan({ argv, env });
  } catch (error) {
    printJson(failClosedResult(error instanceof Error ? error.message : "collector_argument_invalid"));
    return 2;
  }

  if (plan.dryRun) {
    printJson(buildDryRunResult(plan));
    return 0;
  }

  const childEnv = {
    ...env,
    ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL: plan.baseUrl,
    ROBER_O7_BROWSER_SMOKE_BASE_URL: plan.baseUrl,
    ROBER_O7_BROWSER_SMOKE_STABILITY_MS: String(plan.effectiveStabilityMs),
    ROBER_O7_BROWSER_SMOKE_OUTPUT: plan.outputPath,
  };

  return await new Promise((resolve) => {
    // 真实采集只委托既有 browser smoke；collector 不复制 /offer 逻辑，避免两套行为漂移。
    const child = spawn(process.execPath, [delegatedScript, ...plan.passthroughArgs], {
      cwd: workstationRoot,
      env: childEnv,
      stdio: "inherit",
    });
    child.on("error", (error) => {
      printJson(failClosedResult(error.message, { stability_ms: plan.effectiveStabilityMs, output_ref: plan.outputPath }));
      resolve(2);
    });
    child.on("close", (code) => resolve(typeof code === "number" ? code : 2));
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runCollector().then((code) => {
    process.exitCode = code;
  });
}
