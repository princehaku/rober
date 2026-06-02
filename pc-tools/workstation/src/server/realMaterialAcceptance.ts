import fs from "node:fs/promises";
import path from "node:path";
import { PROOF_FLAGS } from "../shared/contracts";
import type {
  RealMaterialArtifactFreshness,
  O5O6ExternalProbeArtifactEndpointSummary,
  O5O6ExternalProbeArtifactResponse,
  RealMaterialCollectionRunbook,
  RealMaterialAcceptanceItem,
  RealMaterialAcceptanceResponse,
  RealMaterialAcceptanceStatus,
} from "../shared/contracts";
import { WORKSTATION_RUNTIME_ROOT } from "./paths";
import { buildO5O6ExternalProbeArtifact } from "./o5O6ExternalProbeArtifact";

const DEFAULT_BROWSER_SMOKE_RESULT = path.join(WORKSTATION_RUNTIME_ROOT, "o7-browser-playback-smoke.json");
const DEFAULT_EXTERNAL_PROBE_RESULT = path.join(WORKSTATION_RUNTIME_ROOT, "o5-o6-external-live-probe.json");
const BROWSER_SMOKE_ENV = "ROBER_O7_BROWSER_SMOKE_RESULT_JSON";
const EXTERNAL_PROBE_ENV = "ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT";
const LONG_STABILITY_REQUIRED_WINDOW_MS = 180000;
const ARTIFACT_STALE_AFTER_SECONDS = 24 * 60 * 60;

function asRecord(value: unknown): Record<string, unknown> | null {
  // 外部 artifact 只接受 object；数组和标量不能进入验收队列。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function safeText(value: unknown, fallback: string): string {
  // queue 面向 operator 展示，长文本先压缩，避免把原始错误堆栈塞进界面。
  return typeof value === "string" && value.trim() ? value.replace(/\s+/g, " ").slice(0, 160) : fallback;
}

function firstReason(reasons: string[], fallback: string): string {
  // blocking_reason 保持单句，完整列表仍留在源 artifact endpoint 里。
  return reasons.find((reason) => reason.length > 0) ?? fallback;
}

function artifactLocation(
  env: NodeJS.ProcessEnv,
  envName: typeof EXTERNAL_PROBE_ENV | typeof BROWSER_SMOKE_ENV,
  defaultPath: string,
): { artifactPath: string; artifactRef: string; source: RealMaterialArtifactFreshness["source"] } {
  // 响应不能泄露真实路径；artifact_ref 只说明 operator 应看 env 还是默认 runtime 文件名。
  const configured = (env[envName] ?? "").trim();
  if (configured) {
    return { artifactPath: configured, artifactRef: `env:${envName}`, source: "env_configured" };
  }
  return {
    artifactPath: defaultPath,
    artifactRef: path.join(".workstation-runtime", path.basename(defaultPath)).split(path.sep).join("/"),
    source: "workstation_runtime",
  };
}

async function artifactFreshness(
  env: NodeJS.ProcessEnv,
  envName: typeof EXTERNAL_PROBE_ENV | typeof BROWSER_SMOKE_ENV,
  defaultPath: string,
): Promise<RealMaterialArtifactFreshness> {
  const checkedAt = new Date().toISOString();
  const location = artifactLocation(env, envName, defaultPath);
  try {
    // 这里只做 stat 只读检查；不打开 artifact 内容，也不触发任何采集脚本。
    const stat = await fs.stat(location.artifactPath);
    const ageSeconds = Math.max(0, Math.floor((Date.now() - stat.mtimeMs) / 1000));
    return {
      status: ageSeconds <= ARTIFACT_STALE_AFTER_SECONDS ? "fresh" : "stale",
      artifact_ref: location.artifactRef,
      source: location.source,
      checked_at: checkedAt,
      mtime: stat.mtime.toISOString(),
      age_seconds: ageSeconds,
      stale_after_seconds: ARTIFACT_STALE_AFTER_SECONDS,
    };
  } catch {
    // stat 失败按缺材料处理；接口仍 fail-closed，不尝试创建文件或补跑 probe。
    return {
      status: "missing",
      artifact_ref: location.artifactRef,
      source: location.source,
      checked_at: checkedAt,
      mtime: null,
      age_seconds: null,
      stale_after_seconds: ARTIFACT_STALE_AFTER_SECONDS,
    };
  }
}

function findEndpoint(
  artifact: O5O6ExternalProbeArtifactResponse,
  expectedEndpoint: "/api/o5/readiness/health" | "/api/o6/archive/health",
): O5O6ExternalProbeArtifactEndpointSummary | null {
  // 只从已脱敏 endpoint 摘要里找固定 allowlist 路径，不处理 raw base URL。
  return artifact.endpoints.find((endpoint) => endpoint.endpoint === expectedEndpoint) ?? null;
}

function o5o6Status(
  artifact: O5O6ExternalProbeArtifactResponse,
  endpoint: O5O6ExternalProbeArtifactEndpointSummary | null,
): RealMaterialAcceptanceStatus {
  // TLS + endpoint schema 都必须来自已有 artifact；缺 artifact 是 not_observed，不伪造成 blocked。
  if (artifact.artifact_status !== "loaded") {
    return "not_observed";
  }
  if (!endpoint) {
    return "not_observed";
  }
  const tlsAccepted = artifact.tls_evidence.tls_status === "observed" && artifact.tls_evidence.tls_observed === true;
  const endpointAccepted =
    endpoint.reachable &&
    endpoint.schema_status === "matched" &&
    ["pass", "observed_fail_closed_contract"].includes(endpoint.contract_status);
  return tlsAccepted && endpointAccepted ? "accepted" : "blocked";
}

function o5o6Reason(
  artifact: O5O6ExternalProbeArtifactResponse,
  endpoint: O5O6ExternalProbeArtifactEndpointSummary | null,
  status: RealMaterialAcceptanceStatus,
): string {
  // reason 优先取 endpoint blocked reason，再退回 artifact 和 TLS 状态。
  if (status === "accepted") {
    return "real_material_artifact_accepted";
  }
  if (artifact.artifact_status !== "loaded") {
    return `external_probe_artifact_${artifact.artifact_status}`;
  }
  if (!endpoint) {
    return "expected_endpoint_not_observed_in_artifact";
  }
  if (!(artifact.tls_evidence.tls_status === "observed" && artifact.tls_evidence.tls_observed === true)) {
    return `tls_${artifact.tls_evidence.tls_status}_not_accepted`;
  }
  return firstReason(endpoint.blocked_reasons, endpoint.failure_category || "endpoint_contract_not_accepted");
}

function o5o6NextAction(objective: "O5" | "O6", status: RealMaterialAcceptanceStatus): string {
  // 下一步动作是 operator 可执行提示，不在服务端启动任何 probe。
  if (status === "accepted") {
    return `${objective}: keep artifact as real-material evidence and wait for OKR owner review`;
  }
  return `${objective}: run the existing O5/O6 external probe against production HTTPS and place its JSON artifact in workstation runtime`;
}

function o5o6Runbook(objective: "O5" | "O6"): RealMaterialCollectionRunbook {
  const endpoint = objective === "O5" ? "/api/o5/readiness/health" : "/api/o6/archive/health";
  return {
    goal: `${objective}: collect production HTTPS external probe material for ${endpoint}`,
    suggested_commands: [
      "cd pc-tools/workstation && ROBER_PC_BASE_URL=http://127.0.0.1:8787 ROBER_CLOUD_BASE_URL=https://<production-cloud-base> ROBER_O5_O6_BEARER_TOKEN=<redacted> npm run o5o6:external-probe -- --output .workstation-runtime/o5-o6-external-live-probe.json",
    ],
    required_env: ["ROBER_PC_BASE_URL", "ROBER_CLOUD_BASE_URL", "ROBER_O5_O6_BEARER_TOKEN"],
    required_artifacts: [".workstation-runtime/o5-o6-external-live-probe.json or ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT"],
    expected_output: "trashbot.o5_o6.external_live_probe.v1 JSON with TLS evidence and endpoint summaries",
    success_criteria: [
      "tls_evidence.tls_status=observed and tls_observed=true",
      `${endpoint} reachable=true and schema_status=matched`,
      "contract_status is observed_fail_closed_contract or pass",
      "safe_to_control=false and robot_control_executed=false remain fixed",
    ],
    failure_handling: [
      "If artifact is missing, run the command manually from a prepared workstation shell.",
      "If TLS is blocked, fix HTTPS certificate, DNS, or reverse proxy before re-running.",
      "If endpoint schema mismatches, inspect the cloud relay/API deployment version before OKR review.",
    ],
    safety_notes: [
      "Recipe only runs an explicit read-only GET probe; this API never executes it.",
      "Do not include raw token, raw base URL, traceback, or artifact absolute path in screenshots.",
    ],
  };
}

function o7Runbook(): RealMaterialCollectionRunbook {
  return {
    goal: "O7: collect 180s+ same-LAN browser playback stability material",
    suggested_commands: [
      "cd pc-tools/workstation && ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://<board-lan-host>:8088 ROBER_O7_BROWSER_SMOKE_STABILITY_MS=180000 npm run o7:browser-smoke",
    ],
    required_env: ["ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL", "ROBER_O7_BROWSER_SMOKE_STABILITY_MS=180000"],
    required_artifacts: [".workstation-runtime/o7-browser-playback-smoke.json or ROBER_O7_BROWSER_SMOKE_RESULT_JSON"],
    expected_output: "trashbot.o7.local_webrtc_browser_playback_smoke.v1 JSON with first frame and stability_summary",
    success_criteria: [
      "status=ok and first_frame_received=true",
      "stability_summary.observation_window_ms >= 180000",
      "connection and ICE remain connected, video size stays stable, and console/page error deltas are 0",
      "post-close active peer count is 0 and remote_active_peer_cleaned=cleaned",
    ],
    failure_handling: [
      "If artifact is missing, run the browser smoke manually after confirming the board camera URL.",
      "If status is needs_long_run, re-run with ROBER_O7_BROWSER_SMOKE_STABILITY_MS=180000 or higher.",
      "If first frame or ICE fails, inspect browser console, LAN reachability, and board camera health logs.",
    ],
    safety_notes: [
      "This recipe creates a browser media session only when the operator runs it explicitly.",
      "The acceptance API only reads the JSON artifact and never sends /offer or robot control commands.",
    ],
  };
}

async function readBrowserSmokeArtifact(env: NodeJS.ProcessEnv): Promise<{
  artifact_status: "loaded" | "missing" | "bad_json";
  observed_at: string | null;
  record: Record<string, unknown> | null;
}> {
  const artifactPath = (env[BROWSER_SMOKE_ENV] ?? "").trim() || DEFAULT_BROWSER_SMOKE_RESULT;
  try {
    // 这里只读 browser smoke JSON；不访问 LAN camera health、不 POST /offer、不创建 WebRTC session。
    const raw = await fs.readFile(artifactPath, "utf8");
    const parsed = JSON.parse(raw);
    return { artifact_status: "loaded", observed_at: safeText(asRecord(parsed)?.executed_at, "unknown"), record: asRecord(parsed) };
  } catch (error) {
    // JSON parse 错误和缺文件都 fail closed；不把坏 artifact 当成真实材料。
    const code = typeof error === "object" && error && "code" in error ? String((error as { code?: unknown }).code) : "";
    return { artifact_status: code === "ENOENT" ? "missing" : "bad_json", observed_at: null, record: null };
  }
}

function o7Status(record: Record<string, unknown> | null): RealMaterialAcceptanceStatus {
  // O7 长稳态要消费显式 smoke JSON 的 stability_summary，不能由 UI 或健康接口推断。
  if (!record || record.status === "not_run") {
    return "not_observed";
  }
  const stability = asRecord(record.stability_summary);
  const observedWindowMs = typeof stability?.observation_window_ms === "number" ? stability.observation_window_ms : 0;
  const healthy =
    record.status === "ok" &&
    record.first_frame_received === true &&
    stability?.status === "observed" &&
    stability.connection_remained_connected === "connected" &&
    stability.ice_remained_connected === "connected" &&
    stability.video_size_stable === "stable" &&
    stability.console_errors_added === 0 &&
    stability.page_errors_added === 0 &&
    stability.post_close_active_peer_connections === 0 &&
    stability.remote_active_peer_cleaned === "cleaned";
  if (healthy && observedWindowMs >= LONG_STABILITY_REQUIRED_WINDOW_MS) {
    return "accepted";
  }
  if (healthy && observedWindowMs > 0) {
    return "needs_long_run";
  }
  return "blocked";
}

function o7Reason(record: Record<string, unknown> | null, artifactStatus: string, status: RealMaterialAcceptanceStatus): string {
  // O7 reason 对齐已有 long-stability guard 的机器语义。
  if (status === "accepted") {
    return "browser_long_stability_artifact_accepted";
  }
  if (!record) {
    return `browser_smoke_artifact_${artifactStatus}`;
  }
  const stability = asRecord(record.stability_summary);
  const observedWindowMs = typeof stability?.observation_window_ms === "number" ? stability.observation_window_ms : 0;
  if (status === "needs_long_run") {
    return "observation_window_below_180000ms";
  }
  if (record.first_frame_received !== true) {
    return "first_frame_not_received";
  }
  if (stability?.status !== "observed") {
    return "stability_summary_not_observed";
  }
  if (observedWindowMs < LONG_STABILITY_REQUIRED_WINDOW_MS) {
    return "observation_window_below_180000ms";
  }
  return "browser_long_stability_health_check_failed";
}

function summarize(statuses: RealMaterialAcceptanceStatus[]): Record<RealMaterialAcceptanceStatus, number> {
  // summary 固定包含四个状态，UI 可以稳定展示空队列。
  return statuses.reduce(
    (acc, status) => ({ ...acc, [status]: acc[status] + 1 }),
    { accepted: 0, needs_long_run: 0, not_observed: 0, blocked: 0 },
  );
}

export async function buildRealMaterialAcceptance(
  options: { env?: NodeJS.ProcessEnv } = {},
): Promise<RealMaterialAcceptanceResponse> {
  const env = options.env ?? process.env;
  const [externalArtifact, browserSmoke, externalFreshness, browserFreshness] = await Promise.all([
    buildO5O6ExternalProbeArtifact({ env }),
    readBrowserSmokeArtifact(env),
    artifactFreshness(env, EXTERNAL_PROBE_ENV, DEFAULT_EXTERNAL_PROBE_RESULT),
    artifactFreshness(env, BROWSER_SMOKE_ENV, DEFAULT_BROWSER_SMOKE_RESULT),
  ]);
  const o5Endpoint = findEndpoint(externalArtifact, "/api/o5/readiness/health");
  const o6Endpoint = findEndpoint(externalArtifact, "/api/o6/archive/health");
  const o5StatusValue = o5o6Status(externalArtifact, o5Endpoint);
  const o6StatusValue = o5o6Status(externalArtifact, o6Endpoint);
  const o7StatusValue = o7Status(browserSmoke.record);
  const items: RealMaterialAcceptanceItem[] = [
    {
      id: "o5_tls_external_probe",
      objective: "O5",
      title: "O5 TLS / external probe material",
      status: o5StatusValue,
      source_endpoint: "/api/o5-o6/external-probe-artifact",
      source_artifact_status: externalArtifact.artifact_status,
      blocking_reason: o5o6Reason(externalArtifact, o5Endpoint, o5StatusValue),
      next_action: o5o6NextAction("O5", o5StatusValue),
      collection_runbook: o5o6Runbook("O5"),
      artifact_freshness: externalFreshness,
      proof_boundary: "existing_external_probe_artifact_tls_endpoint_summary_only",
      observed_at: externalArtifact.updated_at,
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
    },
    {
      id: "o6_archive_external_probe",
      objective: "O6",
      title: "O6 archive external probe material",
      status: o6StatusValue,
      source_endpoint: "/api/o5-o6/external-probe-artifact",
      source_artifact_status: externalArtifact.artifact_status,
      blocking_reason: o5o6Reason(externalArtifact, o6Endpoint, o6StatusValue),
      next_action: o5o6NextAction("O6", o6StatusValue),
      collection_runbook: o5o6Runbook("O6"),
      artifact_freshness: externalFreshness,
      proof_boundary: "existing_external_probe_artifact_archive_endpoint_summary_only",
      observed_at: externalArtifact.updated_at,
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
    },
    {
      id: "o7_browser_long_stability",
      objective: "O7",
      title: "O7 browser 3-5min long stability material",
      status: o7StatusValue,
      source_endpoint: "/api/o7/local-webrtc-camera",
      source_artifact_status: browserSmoke.artifact_status,
      blocking_reason: o7Reason(browserSmoke.record, browserSmoke.artifact_status, o7StatusValue),
      next_action:
        o7StatusValue === "accepted"
          ? "O7: keep 180s+ browser smoke artifact and wait for OKR owner review"
          : "O7: run the existing browser playback smoke for at least 180000ms and place its JSON artifact in workstation runtime",
      collection_runbook: o7Runbook(),
      artifact_freshness: browserFreshness,
      proof_boundary: "existing_browser_smoke_json_long_stability_summary_only",
      observed_at: browserSmoke.observed_at,
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
    },
  ];
  const summary = summarize(items.map((item) => item.status));
  return {
    schema: "trashbot.pc_tools_workstation.real_material_acceptance.v1",
    ...PROOF_FLAGS,
    endpoint: "/api/real-material/acceptance",
    source_endpoints: ["/api/o5-o6/external-probe-artifact", "/api/o7/local-webrtc-camera"],
    queue_status: summary.accepted === items.length ? "accepted" : "action_required",
    items,
    summary,
    fail_closed_flags: {
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
    },
    execution_policy: {
      reads_existing_artifacts_only: true,
      network_probe_executed: false,
      hardware_read_executed: false,
      post_executed: false,
      robots_path_accessed: false,
      webrtc_session_created: false,
      sends_commands: false,
    },
    next_actions: items.filter((item) => item.status !== "accepted").map((item) => item.next_action),
    not_proven: [
      "real_robot_control_not_executed",
      "real_4g_sim_not_proven",
      "real_production_db_queue_not_proven",
      "real_180s_browser_artifact_required_when_not_accepted",
    ],
  };
}
