import fs from "node:fs";
import http from "node:http";

const host = "127.0.0.1";
const port = Number(process.env.MOCK_UPPER_PORT ?? "18081");
const rawPath = process.env.MOCK_UPPER_RAW_PATH;
const processStartedMonoNs = process.hrtime.bigint();
let requestSequence = 0;

function writeJson(response, status, payload) {
  const body = JSON.stringify(payload);
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-store",
  });
  response.end(body);
}

function appendRaw(record) {
  // mock 只记录请求，不导入 ROS、串口或任何硬件包。
  if (rawPath) {
    fs.appendFileSync(rawPath, `${JSON.stringify(record)}\n`, "utf8");
  }
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  if (chunks.length === 0) {
    return {};
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function safeProofEnvelope(status) {
  // 所有危险声明固定为 false，确保 PC fail-closed 扫描不会把 mock 当现场证据。
  return {
    schema: "trashbot.loopback_mock_upper.v1",
    status,
    source: "loopback_mock_only",
    proof_status: "not_proven",
    safe_to_control: false,
    robot_control_executed: false,
    hil_pass: false,
    route_execution_success: false,
    delivery_success: false,
    primary_actions_enabled: false,
    sends_commands: false,
    sends_motion_commands: false,
  };
}

const server = http.createServer(async (request, response) => {
  const ingressWallMs = Date.now();
  const ingressMonoNs = process.hrtime.bigint();
  const url = new URL(request.url ?? "/", `http://${host}:${port}`);
  requestSequence += 1;

  if (request.method === "GET" && url.pathname === "/_fixture/health") {
    writeJson(response, 200, {
      ...safeProofEnvelope("ready"),
      pid: process.pid,
      request_count: requestSequence,
      process_uptime_ms: Number(ingressMonoNs - processStartedMonoNs) / 1_000_000,
      raw_path: rawPath ?? null,
    });
    return;
  }

  let body = {};
  let parseError = "";
  try {
    body = await readJson(request);
  } catch (error) {
    parseError = error instanceof Error ? error.message : "json_parse_failed";
  }
  const parsedMonoNs = process.hrtime.bigint();
  const kind = request.method === "POST" && url.pathname === "/api/base/manual"
    ? "manual"
    : request.method === "POST" && url.pathname === "/api/base/stop"
      ? "stop"
      : "support_readback";
  const record = {
    schema: "trashbot.loopback_mock_upper.request.v1",
    sequence: requestSequence,
    kind,
    method: request.method,
    path: url.pathname,
    query: Object.fromEntries(url.searchParams.entries()),
    ingress_wall_ms: ingressWallMs,
    ingress_mono_ns: ingressMonoNs.toString(),
    body_parsed_mono_ns: parsedMonoNs.toString(),
    ingress_to_body_parsed_ms: Number(parsedMonoNs - ingressMonoNs) / 1_000_000,
    parse_error: parseError,
    body,
    latency_trace: body?.latency_trace ?? null,
    hold_session_id: body?.hold_session_id ?? null,
    hold_sequence: body?.hold_sequence ?? null,
    loopback_mock_only: true,
  };
  appendRaw(record);

  if (parseError) {
    writeJson(response, 400, { ...safeProofEnvelope("blocked_invalid_json"), error: parseError });
    return;
  }
  if (kind === "manual" || kind === "stop") {
    const responseStartMonoNs = process.hrtime.bigint();
    writeJson(response, 200, {
      ...safeProofEnvelope(kind === "manual" ? "mock_manual_recorded" : "mock_stop_recorded"),
      latency_timing: {
        clock_id: "mock_upper_process_hrtime",
        mock_upper_ingress_wall_ms: ingressWallMs,
        mock_upper_ingress_mono_ns: ingressMonoNs.toString(),
        mock_upper_body_parsed_mono_ns: parsedMonoNs.toString(),
        mock_upper_response_start_mono_ns: responseStartMonoNs.toString(),
        mock_upper_ingress_to_body_parsed_ms: Number(parsedMonoNs - ingressMonoNs) / 1_000_000,
        mock_upper_body_parsed_to_response_ms: Number(responseStartMonoNs - parsedMonoNs) / 1_000_000,
      },
    });
    return;
  }

  // 页面挂载和 keyup 后的固定只读端点统一返回保守空材料，不触发任何设备动作。
  writeJson(response, 200, safeProofEnvelope("mock_readback_empty"));
});

server.listen(port, host, () => {
  process.stdout.write(`${JSON.stringify({ event: "mock_upper_ready", host, port, pid: process.pid, raw_path: rawPath })}\n`);
});

function shutdown(signal) {
  // 清理只关闭本轮 mock listener；没有子进程、硬件句柄或远端连接。
  server.close(() => {
    process.stdout.write(`${JSON.stringify({ event: "mock_upper_stopped", signal, pid: process.pid })}\n`);
    process.exit(0);
  });
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
