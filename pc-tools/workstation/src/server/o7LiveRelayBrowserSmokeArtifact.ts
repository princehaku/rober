import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import type { Server } from "node:http";
import { createWorkstationApp } from "./index";

const ARTIFACT_SCHEMA = "trashbot.pc_tools_workstation.o7_live_relay_browser_smoke_artifact.v1";
const PROOF_BOUNDARY = "software_proof_o7_live_relay_browser_smoke_artifact_only";
const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 17001;
const MAX_PORT_ATTEMPTS = 10;

type JsonRecord = Record<string, unknown>;

type ListenAttempt = {
  host: string;
  port: number;
  status: "listening" | "port_in_use" | "failed";
  error?: string;
};

type EndpointObservation = {
  endpoint: string;
  method: "GET";
  url: string;
  http_status: number;
  ok: boolean;
  duration_ms: number;
  schema: string;
  payload: JsonRecord;
};

type SmokeArgs = {
  artifact: string;
  host: string;
  port: number;
};

type LiveServer = {
  server: Server;
  host: string;
  port: number;
  baseUrl: string;
  listenAttempts: ListenAttempt[];
};

function parseArgs(argv: string[]): SmokeArgs {
  // 这个脚本必须可以被现场 owner 复制运行，所以只支持显式、可读的长参数。
  const args = new Map<string, string>();
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index] ?? "";
    if (!token.startsWith("--")) {
      throw new Error(`unknown positional argument: ${token}`);
    }
    const key = token.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`missing value for --${key}`);
    }
    args.set(key, value);
    index += 1;
  }

  const artifact = args.get("artifact");
  if (!artifact) {
    throw new Error("missing required --artifact <path>");
  }

  const portText = args.get("port") ?? String(DEFAULT_PORT);
  const port = Number(portText);
  if (!Number.isInteger(port) || port <= 0 || port > 65535) {
    throw new Error(`invalid --port value: ${portText}`);
  }

  return {
    artifact: path.resolve(process.cwd(), artifact),
    host: args.get("host") ?? DEFAULT_HOST,
    port,
  };
}

async function listenOnce(host: string, port: number): Promise<{ server: Server; attempt: ListenAttempt }> {
  // 每次尝试都新建 Express app，避免端口失败后复用半初始化 server 状态。
  const app = createWorkstationApp();
  return new Promise((resolve, reject) => {
    const server = app.listen(port, host);
    const onListening = (): void => {
      cleanup();
      resolve({ server, attempt: { host, port, status: "listening" } });
    };
    const onError = (error: NodeJS.ErrnoException): void => {
      cleanup();
      server.close();
      reject({ host, port, error });
    };
    const cleanup = (): void => {
      server.off("listening", onListening);
      server.off("error", onError);
    };
    server.once("listening", onListening);
    server.once("error", onError);
  });
}

async function startLoopbackServer(host: string, firstPort: number): Promise<LiveServer> {
  // 17001 是 deterministic 首选端口；占用时顺延并把所有尝试写进 artifact。
  const listenAttempts: ListenAttempt[] = [];
  for (let offset = 0; offset < MAX_PORT_ATTEMPTS; offset += 1) {
    const port = firstPort + offset;
    try {
      const { server, attempt } = await listenOnce(host, port);
      listenAttempts.push(attempt);
      return {
        server,
        host,
        port,
        baseUrl: `http://${host}:${port}`,
        listenAttempts,
      };
    } catch (caught) {
      const error = caught as { host: string; port: number; error: NodeJS.ErrnoException };
      const status = error.error.code === "EADDRINUSE" ? "port_in_use" : "failed";
      listenAttempts.push({
        host: error.host,
        port: error.port,
        status,
        error: error.error.message,
      });
      if (status !== "port_in_use") {
        throw new Error(`failed to start loopback server on ${host}:${port}: ${error.error.message}`);
      }
    }
  }
  throw new Error(`no free loopback port found from ${firstPort} to ${firstPort + MAX_PORT_ATTEMPTS - 1}`);
}

async function closeServer(server: Server): Promise<void> {
  // close 也走 Promise，确保最终命令退出前端口已经释放，便于连续复验。
  await new Promise<void>((resolve, reject) => {
    server.close((error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve();
    });
  });
}

function asRecord(value: unknown, label: string): JsonRecord {
  // 只接受 JSON object；数组或 primitive 不能作为 contract proof。
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} JSON payload is not an object`);
  }
  return value as JsonRecord;
}

async function fetchJson(baseUrl: string, endpoint: string): Promise<EndpointObservation> {
  // Node fetch 通过真实 loopback HTTP socket 访问 live server，不复用 vitest/jsdom stub。
  const url = `${baseUrl}${endpoint}`;
  const startedAt = Date.now();
  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    signal: AbortSignal.timeout(3000),
  });
  const payload = asRecord(await response.json(), endpoint);
  return {
    endpoint,
    method: "GET",
    url,
    http_status: response.status,
    ok: response.ok,
    duration_ms: Date.now() - startedAt,
    schema: String(payload.schema ?? "missing_schema"),
    payload,
  };
}

function requireObservation(
  observation: EndpointObservation,
  expectedSchema: string,
  expectedStatus?: { field: string; value: string },
): void {
  // schema/status 双重断言让 artifact 不能在 endpoint 退化时继续写 success。
  if (!observation.ok) {
    throw new Error(`${observation.endpoint} returned HTTP ${observation.http_status}`);
  }
  if (observation.schema !== expectedSchema) {
    throw new Error(`${observation.endpoint} schema mismatch: ${observation.schema}`);
  }
  if (expectedStatus && observation.payload[expectedStatus.field] !== expectedStatus.value) {
    throw new Error(
      `${observation.endpoint} ${expectedStatus.field} mismatch: ${String(observation.payload[expectedStatus.field])}`,
    );
  }
}

function requireFalse(payload: JsonRecord, field: string, source: string): string {
  // 缺字段不代表 true；这里只对存在且为 true 的危险字段 fail fast。
  if (payload[field] === true) {
    throw new Error(`${source} dangerous true field: ${field}`);
  }
  return `${field}=false`;
}

async function runSmoke(args: SmokeArgs): Promise<JsonRecord> {
  const liveServer = await startLoopbackServer(args.host, args.port);
  const generatedAtMs = Date.now();
  try {
    const health = await fetchJson(liveServer.baseUrl, "/api/health");
    requireObservation(health, "trashbot.pc_tools_workstation.health.v1");

    const operatorConsole = await fetchJson(liveServer.baseUrl, "/api/o7/operator-console");
    requireObservation(operatorConsole, "trashbot.o7.operator_console.v1");

    const probeQuery = new URLSearchParams({ baseUrl: liveServer.baseUrl }).toString();
    const cloudOperatorConsoleProbe = await fetchJson(
      liveServer.baseUrl,
      `/api/o7/cloud-operator-console-probe?${probeQuery}`,
    );
    requireObservation(
      cloudOperatorConsoleProbe,
      "trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1",
      { field: "probe_status", value: "loaded_fail_closed_contract" },
    );

    const responseFalseFields = [
      requireFalse(operatorConsole.payload, "safe_to_control", "operator_console"),
      requireFalse(operatorConsole.payload, "delivery_success", "operator_console"),
      requireFalse(operatorConsole.payload, "primary_actions_enabled", "operator_console"),
      requireFalse(cloudOperatorConsoleProbe.payload, "safe_to_control", "cloud_operator_console_probe"),
      requireFalse(cloudOperatorConsoleProbe.payload, "delivery_success", "cloud_operator_console_probe"),
      requireFalse(cloudOperatorConsoleProbe.payload, "connects_cloud_production", "cloud_operator_console_probe"),
    ];

    return {
      schema: ARTIFACT_SCHEMA,
      generated_at_ms: generatedAtMs,
      generated_at_iso: new Date(generatedAtMs).toISOString(),
      proof_boundary: PROOF_BOUNDARY,
      artifact_status: "live_relay_browser_smoke_ready_not_delivery_proof",
      endpoint_transport: "live_loopback_http_socket",
      server_started: true,
      server_host: liveServer.host,
      server_port: liveServer.port,
      server_base_url: liveServer.baseUrl,
      listen_attempts: liveServer.listenAttempts,
      http_smoke_executed: true,
      browser_smoke_status: "not_run_http_only_minimum",
      browser_runtime: "not_configured_in_workstation_package",
      browser_smoke_note: "Live HTTP socket smoke executed; browser automation was not run in this project runtime.",
      health_schema: health.schema,
      operator_console_schema: operatorConsole.schema,
      cloud_operator_console_probe_schema: cloudOperatorConsoleProbe.schema,
      probe_status: String(cloudOperatorConsoleProbe.payload.probe_status ?? "missing_probe_status"),
      response_false_fields: responseFalseFields,
      http_observations: {
        health,
        operator_console: operatorConsole,
        cloud_operator_console_probe: cloudOperatorConsoleProbe,
      },
      command_summary: {
        script: "src/server/o7LiveRelayBrowserSmokeArtifact.ts",
        preferred_command:
          "cd pc-tools/workstation && npm run smoke:o7-live-relay-browser -- --artifact ../../sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/artifacts/o7_live_relay_browser_smoke_artifact.json",
        argv: process.argv.slice(2),
      },
      not_proven: [
        "production_cloud_success",
        "public_https_tls",
        "4g_or_sim_path",
        "production_db_or_queue",
        "oss_or_cdn_live_traffic",
        "real_phone_browser_production_path",
        "route_execution",
        "delivery_success",
        "operator_acceptance",
        "hil_pass",
        "safe_to_control",
        "robot_control_side_effect",
      ],
      acceptance_anchors: [
        `schema=${ARTIFACT_SCHEMA}`,
        `proof_boundary=${PROOF_BOUNDARY}`,
        "endpoint_transport=live_loopback_http_socket",
        "server_started=true",
        "http_smoke_executed=true",
        "delivery_success=false",
        "safe_to_control=false",
        "route_execution_success=false",
        "hil_pass=false",
      ],
      delivery_success: false,
      safe_to_control: false,
      route_execution_success: false,
      hil_pass: false,
      robot_control_executed: false,
      connects_cloud_production: false,
    };
  } finally {
    await closeServer(liveServer.server);
  }
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const artifact = await runSmoke(args);
  await mkdir(path.dirname(args.artifact), { recursive: true });
  await writeFile(args.artifact, `${JSON.stringify(artifact, null, 2)}\n`, "utf8");
  console.log(
    [
      "o7_live_relay_browser_smoke_artifact_ready",
      `artifact=${args.artifact}`,
      `endpoint_transport=${String(artifact.endpoint_transport)}`,
      `server_started=${String(artifact.server_started)}`,
      `http_smoke_executed=${String(artifact.http_smoke_executed)}`,
      `browser_smoke_status=${String(artifact.browser_smoke_status)}`,
    ].join(" "),
  );
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
