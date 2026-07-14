import { constants } from "node:fs";
import { access, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import path from "node:path";
import { tmpdir } from "node:os";
import { pathToFileURL } from "node:url";
import type { Server } from "node:http";
import { createWorkstationApp } from "./index";

const ARTIFACT_SCHEMA = "trashbot.pc_tools_workstation.o7_live_relay_headless_browser_smoke.v1";
const PROOF_BOUNDARY = "software_proof_o7_live_relay_headless_browser_smoke_only";
const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 17002;
const DEFAULT_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const MAX_PORT_ATTEMPTS = 10;
const CHROME_TIMEOUT_MS = 12_000;

type JsonRecord = Record<string, unknown>;

type ListenAttempt = {
  host: string;
  port: number;
  status: "listening" | "port_in_use" | "failed";
  error?: string;
};

type HeadlessSmokeArgs = {
  artifact: string;
  host: string;
  port: number;
  chromePath: string;
};

type LiveServer = {
  server: Server;
  host: string;
  port: number;
  baseUrl: string;
  listenAttempts: ListenAttempt[];
};

type ChromeJsonObservation = {
  endpoint: string;
  method: "GET";
  url: string;
  browser_runtime: "headless_chrome";
  chrome_path: string;
  duration_ms: number;
  dom_length: number;
  stderr_excerpt: string;
  ok: boolean;
  schema: string;
  status_field?: string;
  status_value?: string;
  payload: JsonRecord;
};

export function parseArgs(argv: string[]): HeadlessSmokeArgs {
  // 现场复验脚本只收长参数，避免 positional 参数顺序漂移导致 artifact 写错目录。
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
    chromePath: args.get("chrome") ?? process.env.CHROME_PATH ?? DEFAULT_CHROME_PATH,
  };
}

function excerpt(text: string, maxLength = 600): string {
  // Chrome stderr 常带 DevTools 日志；artifact 只保留短摘录，避免把环境噪声写成主证据。
  const compact = text.replace(/\s+/g, " ").trim();
  return compact.length <= maxLength ? compact : `${compact.slice(0, maxLength)}...`;
}

function decodeHtmlEntities(value: string): string {
  // --dump-dom 对 application/json 通常包一层 <pre>，这里只做 JSON 需要的实体解码。
  return value
    .replace(/&quot;/g, "\"")
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&#(\d+);/g, (_match, code: string) => String.fromCodePoint(Number(code)));
}

export function extractJsonFromChromeDumpDom(dom: string, label: string): JsonRecord {
  // 真实 Chrome JSON viewer 会输出 HTML；只从 <pre> 或 raw JSON 中取 object，拒绝数组/文本。
  const trimmed = dom.trim();
  const rawJsonText = trimmed.startsWith("{")
    ? trimmed
    : decodeHtmlEntities(trimmed.match(/<pre[^>]*>([\s\S]*?)<\/pre>/i)?.[1]?.trim() ?? "");
  if (!rawJsonText) {
    throw new Error(`${label} headless Chrome DOM did not contain JSON object text`);
  }
  const parsed = JSON.parse(rawJsonText) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error(`${label} headless Chrome JSON payload is not an object`);
  }
  return parsed as JsonRecord;
}

export function chromeDumpDomArgs(url: string, userDataDir: string): string[] {
  // 独立 profile 保证 smoke 不依赖用户已登录 Chrome，也不会污染用户浏览器会话。
  return [
    "--headless=new",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-sync",
    "--hide-scrollbars",
    "--mute-audio",
    "--no-first-run",
    "--no-default-browser-check",
    `--user-data-dir=${userDataDir}`,
    "--dump-dom",
    url,
  ];
}

async function ensureChromeRunnable(chromePath: string): Promise<void> {
  // Chrome 缺失时必须 fail closed；不能自动降级成上一轮 HTTP-only smoke。
  await access(chromePath, constants.X_OK).catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`headless Chrome executable is not available at ${chromePath}: ${message}`);
  });
}

async function listenOnce(host: string, port: number): Promise<{ server: Server; attempt: ListenAttempt }> {
  // 每个端口尝试都创建新的 Express app，避免失败端口留下半初始化 listener。
  const app = createWorkstationApp();
  return new Promise((resolve, reject) => {
    const server = app.listen(port, host);
    const cleanup = (): void => {
      server.off("listening", onListening);
      server.off("error", onError);
    };
    const onListening = (): void => {
      cleanup();
      resolve({ server, attempt: { host, port, status: "listening" } });
    };
    const onError = (error: NodeJS.ErrnoException): void => {
      cleanup();
      server.close();
      reject({ host, port, error });
    };
    server.once("listening", onListening);
    server.once("error", onError);
  });
}

async function startLoopbackServer(host: string, firstPort: number): Promise<LiveServer> {
  // 默认 17002，避免覆盖上一轮 17001；占用时顺延并把尝试过程写入 artifact。
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
  // 明确等待 close 完成，保证连续 smoke 不因为端口释放竞态失败。
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

async function waitForHealth(baseUrl: string): Promise<void> {
  // readiness 只确认 live server 已监听；最终证据仍来自 Chrome --dump-dom。
  const deadline = Date.now() + 3000;
  let lastError = "health_not_attempted";
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/api/health`, { signal: AbortSignal.timeout(500) });
      if (response.ok) {
        return;
      }
      lastError = `HTTP ${response.status}`;
    } catch (caught) {
      lastError = caught instanceof Error ? caught.message : String(caught);
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`loopback server did not become healthy: ${lastError}`);
}

async function runChromeDumpDom(chromePath: string, url: string, userDataDir: string): Promise<{ stdout: string; stderr: string; durationMs: number }> {
  // execFile 直接运行本机 Chrome 二进制，避免把 jsdom、fetch 或 curl 伪装成浏览器 proof。
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    execFile(
      chromePath,
      chromeDumpDomArgs(url, userDataDir),
      { timeout: CHROME_TIMEOUT_MS, maxBuffer: 4 * 1024 * 1024 },
      (error, stdout, stderr) => {
        const durationMs = Date.now() - startedAt;
        if (error) {
          reject(
            new Error(
              [
                `headless Chrome failed for ${url}`,
                `duration_ms=${durationMs}`,
                `error=${error.message}`,
                `stderr=${excerpt(stderr)}`,
                `stdout=${excerpt(stdout)}`,
              ].join(" "),
            ),
          );
          return;
        }
        resolve({ stdout, stderr, durationMs });
      },
    );
  });
}

async function loadJsonWithChrome(
  chromePath: string,
  baseUrl: string,
  endpoint: string,
  userDataDir: string,
  statusField?: string,
): Promise<ChromeJsonObservation> {
  // endpoint observation 记录的是 Chrome 看到的 JSON，不是 Node fetch 的 HTTP-only payload。
  const url = `${baseUrl}${endpoint}`;
  const { stdout, stderr, durationMs } = await runChromeDumpDom(chromePath, url, userDataDir);
  const payload = extractJsonFromChromeDumpDom(stdout, endpoint);
  const schema = String(payload.schema ?? "missing_schema");
  const statusValue = statusField ? String(payload[statusField] ?? "missing_status") : undefined;
  return {
    endpoint,
    method: "GET",
    url,
    browser_runtime: "headless_chrome",
    chrome_path: chromePath,
    duration_ms: durationMs,
    dom_length: stdout.length,
    stderr_excerpt: excerpt(stderr),
    ok: true,
    schema,
    status_field: statusField,
    status_value: statusValue,
    payload,
  };
}

function requireObservation(
  observation: ChromeJsonObservation,
  expectedSchema: string,
  expectedStatus?: { field: string; value: string },
): void {
  // schema/status 是本轮验收锚点；任一漂移都不写 ready artifact。
  if (observation.schema !== expectedSchema) {
    throw new Error(`${observation.endpoint} schema mismatch: ${observation.schema}`);
  }
  if (expectedStatus && observation.payload[expectedStatus.field] !== expectedStatus.value) {
    throw new Error(
      `${observation.endpoint} ${expectedStatus.field} mismatch: ${String(observation.payload[expectedStatus.field])}`,
    );
  }
}

function requireNotTrue(payload: JsonRecord, field: string, source: string): string {
  // 响应中危险字段只要为 true 就失败；缺字段不被解释成成功。
  if (payload[field] === true) {
    throw new Error(`${source} dangerous true field: ${field}`);
  }
  return `${source}.${field}=false_or_absent`;
}

function collectResponseFalseFieldChecks(observations: ChromeJsonObservation[]): string[] {
  // 三个 endpoint 一起扫，确保浏览器看到的合同没有把安全或任务成功字段打开。
  const dangerousFields = [
    "delivery_success",
    "safe_to_control",
    "route_execution_success",
    "hil_pass",
    "robot_control_executed",
    "connects_cloud_production",
    "primary_actions_enabled",
  ];
  return observations.flatMap((observation) =>
    dangerousFields.map((field) => requireNotTrue(observation.payload, field, observation.endpoint)),
  );
}

export async function runHeadlessBrowserSmoke(args: HeadlessSmokeArgs): Promise<JsonRecord> {
  await ensureChromeRunnable(args.chromePath);
  const liveServer = await startLoopbackServer(args.host, args.port);
  const generatedAtMs = Date.now();
  const userDataDir = await mkdtemp(path.join(tmpdir(), "rober-o7-headless-smoke-"));
  try {
    await waitForHealth(liveServer.baseUrl);
    const probeQuery = new URLSearchParams({ baseUrl: liveServer.baseUrl }).toString();
    const health = await loadJsonWithChrome(args.chromePath, liveServer.baseUrl, "/api/health", userDataDir);
    const operatorConsole = await loadJsonWithChrome(
      args.chromePath,
      liveServer.baseUrl,
      "/api/o7/operator-console",
      userDataDir,
    );
    const cloudOperatorConsoleProbe = await loadJsonWithChrome(
      args.chromePath,
      liveServer.baseUrl,
      `/api/o7/cloud-operator-console-probe?${probeQuery}`,
      userDataDir,
      "probe_status",
    );

    requireObservation(health, "trashbot.pc_tools_workstation.health.v1");
    requireObservation(operatorConsole, "trashbot.o7.operator_console.v1");
    requireObservation(
      cloudOperatorConsoleProbe,
      "trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1",
      { field: "probe_status", value: "loaded_fail_closed_contract" },
    );

    const observations = [health, operatorConsole, cloudOperatorConsoleProbe];
    const responseFalseFieldChecks = collectResponseFalseFieldChecks(observations);

    return {
      schema: ARTIFACT_SCHEMA,
      generated_at_ms: generatedAtMs,
      generated_at_iso: new Date(generatedAtMs).toISOString(),
      proof_boundary: PROOF_BOUNDARY,
      artifact_status: "headless_browser_smoke_ready_not_delivery_proof",
      endpoint_transport: "live_loopback_http_socket",
      browser_runtime: "headless_chrome",
      browser_smoke_status: "live_headless_chrome_executed",
      server_started: true,
      server_host: liveServer.host,
      server_port: liveServer.port,
      server_base_url: liveServer.baseUrl,
      listen_attempts: liveServer.listenAttempts,
      http_smoke_executed: true,
      headless_browser_smoke_executed: true,
      chrome_path: args.chromePath,
      chrome_execution_mode: "--headless=new --dump-dom",
      health_schema: health.schema,
      operator_console_schema: operatorConsole.schema,
      cloud_operator_console_probe_schema: cloudOperatorConsoleProbe.schema,
      probe_status: String(cloudOperatorConsoleProbe.payload.probe_status ?? "missing_probe_status"),
      response_false_field_checks: responseFalseFieldChecks,
      browser_observations: {
        health,
        operator_console: operatorConsole,
        cloud_operator_console_probe: cloudOperatorConsoleProbe,
      },
      command_summary: {
        script: "src/server/o7LiveRelayHeadlessBrowserSmoke.ts",
        preferred_command:
          "cd pc-tools/workstation && npm run smoke:o7-live-relay-headless-browser -- --artifact ../../sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/artifacts/o7_live_relay_headless_browser_smoke.json",
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
        "artifact_status=headless_browser_smoke_ready_not_delivery_proof",
        "endpoint_transport=live_loopback_http_socket",
        "browser_runtime=headless_chrome",
        "browser_smoke_status=live_headless_chrome_executed",
        "server_started=true",
        "http_smoke_executed=true",
        "headless_browser_smoke_executed=true",
        "delivery_success=false",
        "safe_to_control=false",
        "route_execution_success=false",
        "hil_pass=false",
        "robot_control_executed=false",
        "connects_cloud_production=false",
      ],
      delivery_success: false,
      safe_to_control: false,
      route_execution_success: false,
      hil_pass: false,
      robot_control_executed: false,
      connects_cloud_production: false,
    };
  } finally {
    await rm(userDataDir, { recursive: true, force: true });
    await closeServer(liveServer.server);
  }
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const artifact = await runHeadlessBrowserSmoke(args);
  await mkdir(path.dirname(args.artifact), { recursive: true });
  await writeFile(args.artifact, `${JSON.stringify(artifact, null, 2)}\n`, "utf8");
  console.log(
    [
      "o7_live_relay_headless_browser_smoke_ready",
      `artifact=${args.artifact}`,
      `endpoint_transport=${String(artifact.endpoint_transport)}`,
      `browser_runtime=${String(artifact.browser_runtime)}`,
      `browser_smoke_status=${String(artifact.browser_smoke_status)}`,
      `server_started=${String(artifact.server_started)}`,
      `http_smoke_executed=${String(artifact.http_smoke_executed)}`,
      `headless_browser_smoke_executed=${String(artifact.headless_browser_smoke_executed)}`,
    ].join(" "),
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
