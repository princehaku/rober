import express from "express";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  buildEvidenceToolsResponse,
  buildHardwareMaterialsResponse,
  buildHealth,
  buildO7CloudArchiveTasks,
  buildO7CloudArchiveTasksProbe,
  buildO7LiveEndpointsManifest,
  buildO7ConsumerTaskDetail,
  buildO7ConsumerTaskList,
  buildO7CloudOperatorConsoleProbe,
  buildO7OperatorConsoleAcceptanceResponse,
  buildO7OperatorConsoleResponse,
  buildO7PreviewsAcceptanceResponse,
  buildO7LabelingPreview,
  buildO7FieldEvidenceConsumerIngest,
  buildO7RealtimeElevatorProbe,
  buildO7RealtimeElevatorPreview,
  buildO7RouteReplayPreview,
  buildO7RtcSignalingContractProbe,
  buildO7SafeCommandPreview,
  buildO7VoicePreview,
  buildProofBoundary,
  buildRadarScanProofRefreshProxy,
  buildMapProofRefreshProxy,
  buildRobotControlSummary,
  buildRouteDebugSummary,
  buildTrainingLabelingResponse,
} from "./catalog";
import { endpointUrl, normalizeRobotApiBaseUrl, scanDangerousTrueFields } from "./robotControlSummary";
import type {
  RobotControlCameraAnswerSummary,
  RobotControlCameraCloseProxyResponse,
  RobotControlCameraOfferProxyResponse,
} from "../shared/contracts";

const PORT = Number(process.env.PORT ?? 8787);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_ROOT = path.resolve(__dirname, "../../dist");

function queryString(value: unknown): string {
  // Express query 可能是数组或对象；只接受单个字符串，其他形态 fail closed 为空。
  // 为空会让 catalog 返回 not_proven/blocked，而不是把异常 query 当路径读取。
  return typeof value === "string" ? value : "";
}

function asRecord(value: unknown): Record<string, unknown> | null {
  // camera proxy 只接受/返回 JSON object；数组或字符串一律 fail-closed。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function shortText(value: unknown, fallback: string): string {
  // 响应只保留短摘要，避免把远端 traceback、路径或超长文本直接暴露给 UI。
  return typeof value === "string" && value.trim() ? value.trim().slice(0, 240) : fallback;
}

function normalizeAnswerSdp(value: string): string {
  // 浏览器对 SDP 行结束更严格；这里不改写语义，只统一成 CRLF 并补最后一个 CRLF。
  const crlfNormalized = value.replace(/\r?\n/g, "\r\n");
  return crlfNormalized.endsWith("\r\n") ? crlfNormalized : `${crlfNormalized}\r\n`;
}

function safeAnswer(value: unknown): RobotControlCameraAnswerSummary | null {
  // 前端必须拿到 answer.sdp/type 才能 setRemoteDescription；除此之外不透传更多媒体字段。
  const payload = asRecord(value);
  if (!payload) {
    return null;
  }
  const sdp = typeof payload.sdp === "string" ? payload.sdp : "";
  const type = payload.type === "answer" || payload.type === "pranswer" ? payload.type : null;
  if (!sdp.trim() || !type) {
    return null;
  }
  return { type, sdp: normalizeAnswerSdp(sdp) };
}

function safeAnswerFromPayload(payload: Record<string, unknown> | null): RobotControlCameraAnswerSummary | null {
  // 真实上位机当前返回顶层 answer SDP；本机 proxy 同时兼容嵌套 answer 和顶层 answer。
  return safeAnswer(payload?.answer) ?? safeAnswer(payload);
}

function peerIdText(value: unknown): string {
  // peer_id 只保留短字母数字摘要，避免路径注入或日志污染。
  return typeof value === "string" && /^[A-Za-z0-9_-]{1,120}$/.test(value) ? value : "";
}

function unsafeProxyFailure(
  sourceBaseUrl: string,
  reason: string,
  remoteEndpoint: RobotControlCameraOfferProxyResponse["remote_endpoint"],
): RobotControlCameraOfferProxyResponse;
function unsafeProxyFailure(
  sourceBaseUrl: string,
  reason: string,
  remoteEndpoint: RobotControlCameraCloseProxyResponse["remote_endpoint"],
  peerId: string,
): RobotControlCameraCloseProxyResponse;
function unsafeProxyFailure(
  sourceBaseUrl: string,
  reason: string,
  remoteEndpoint: string,
  peerId = "",
): RobotControlCameraOfferProxyResponse | RobotControlCameraCloseProxyResponse {
  // URL/请求体验证失败时也返回固定 false 合同，避免前端为了错误态另写一套逻辑。
  const common = {
    source: "software_proof" as const,
    proof_status: "not_proven" as const,
    safe_to_control: false as const,
    delivery_success: false as const,
    primary_actions_enabled: false as const,
    pc_only: true as const,
    robot_control_executed: false as const,
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_http_status: null,
    blocked_reasons: [reason],
  };
  if (remoteEndpoint === "/api/camera/offer") {
    return {
      schema: "trashbot.pc_tools_workstation.robot_control_camera_offer_proxy.v1",
      proxy_status: "offer_rejected",
      remote_endpoint: "/api/camera/offer",
      status: "blocked",
      peer_id: "",
      answer: null,
      error: reason,
      failure_reason: reason,
      ...common,
    };
  }
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_camera_close_proxy.v1",
    proxy_status: "close_rejected",
    remote_endpoint: "/api/camera/peers/{peer_id}/close",
    peer_id: peerId,
    status: "blocked",
    error: reason,
    failure_reason: reason,
    ...common,
  };
}

async function fetchCameraProxySummary(
  baseUrl: string,
  endpoint: string,
  body: Record<string, unknown>,
): Promise<{ remote_http_status: number | null; payload: Record<string, unknown> | null; error: string }> {
  // camera proxy 只向白名单 endpoint 发 POST JSON，不允许动态路径或浏览器跨域直连。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return { remote_http_status: null, payload: null, error: normalized.reason };
  }
  try {
    const response = await fetch(endpointUrl(normalized.normalized, endpoint), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    });
    const json = await response.json().catch(() => null);
    return {
      remote_http_status: response.status,
      payload: asRecord(json),
      error: "",
    };
  } catch (error) {
    return {
      remote_http_status: null,
      payload: null,
      error: error instanceof Error ? shortText(error.message, "upper_api_unreachable") : "upper_api_unreachable",
    };
  }
}

export function createWorkstationApp(): express.Express {
  const workstationApp = express();

  // Express 只承载本地 PC API 和构建后的静态 UI。
  // 这里不挂载任何 ROS2、串口、控制或云端生产客户端。
  workstationApp.use(express.json());

  workstationApp.get("/api/health", (_req, res) => {
    // health 也保留 fail-closed 字段，避免监控把服务在线误读为机器人在线。
    res.json(buildHealth());
  });

  workstationApp.get("/api/tools/evidence", async (_req, res) => {
    // API 只读索引 JSON fixture，不执行任何外部脚本或现场链路。
    res.json(await buildEvidenceToolsResponse());
  });

  workstationApp.get("/api/tools/hardware-materials", async (_req, res) => {
    // Hardware materials 只读扫描 WAVE ROVER fixture 文件名，不打开串口或执行 HIL。
    res.json(await buildHardwareMaterialsResponse());
  });

  workstationApp.get("/api/hardware/wave-rover/material-coverage", async (_req, res) => {
    // 新路径按本轮 tech-plan 命名；响应与旧 tools 路径一致，便于 UI 和 reviewer 复核。
    res.json(await buildHardwareMaterialsResponse());
  });

  workstationApp.get("/api/tools/training-labeling", async (_req, res) => {
    // 训练/标注第一阶段是占位入口，必须显式声明未接真实流水线。
    res.json(await buildTrainingLabelingResponse());
  });

  workstationApp.get("/api/route/debug-summary", async (req, res) => {
    // route 摘要可读取用户指定的本地 JSON，但仍不执行 Python、ROS2 或控制动作。
    res.json(
      await buildRouteDebugSummary({
        statusJson: queryString(req.query.statusJson),
        taskRecord: queryString(req.query.taskRecord),
        taskRecordDir: queryString(req.query.taskRecordDir),
        elevatorRouteReconciliation: queryString(req.query.elevatorRouteReconciliation),
      }),
    );
  });

  workstationApp.get("/api/o7/operator-console", (_req, res) => {
    // O7 console 只返回 cloud contract draft，不连接机器人、不发送控制命令。
    res.json(buildO7OperatorConsoleResponse());
  });

  workstationApp.get("/api/o7/operator-console/acceptance", (_req, res) => {
    // Acceptance guard 只复核 O7 console 响应，不读取硬件、不发命令、不连接云端生产。
    res.json(buildO7OperatorConsoleAcceptanceResponse());
  });

  workstationApp.get("/api/o7/previews/acceptance", (_req, res) => {
    // Previews guard 汇总本地/HTTP 预览证据边界，不读取 fixture、不探测云端、不触发控制。
    res.json(buildO7PreviewsAcceptanceResponse());
  });

  workstationApp.get("/api/o7/live-endpoints/manifest", (_req, res) => {
    // Live endpoints manifest 只读取 env 配置并脱敏，不执行 ping/connect/send 或硬件读取。
    res.json(buildO7LiveEndpointsManifest());
  });

  workstationApp.get("/api/o7/cloud-operator-console-probe", async (req, res) => {
    // Cloud probe 只允许后端探测本机回环 HTTP contract，不能变成外网或生产云代理。
    res.json(await buildO7CloudOperatorConsoleProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/consumer-read/tasks", async (req, res) => {
    // O7 列表主入口只读代理本机回环 O6 consumer read，不直连公网或机器人。
    res.json(await buildO7ConsumerTaskList(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/consumer-read/tasks/:taskId", async (req, res) => {
    // 本地 field evidence manifest 只作为远端缺字段时的只读补齐来源，不改变远端轨迹/事件等摘要。
    res.json(
      await buildO7ConsumerTaskDetail(
        queryString(req.query.baseUrl),
        req.params.taskId ?? "",
        queryString(req.query.fieldEvidenceManifestJson),
      ),
    );
  });

  workstationApp.get("/api/o7/cloud-archive/tasks-probe", async (req, res) => {
    // Archive tasks probe 只拉取本机回环 cloud relay contract，不读取远程 URL、不发送任何控制动作。
    res.json(await buildO7CloudArchiveTasksProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/realtime-elevator-probe", async (req, res) => {
    // Realtime/elevator probe 只拉取本机回环 snapshot contract，不读取 ROS2 /tf、地图或电梯设备。
    res.json(await buildO7RealtimeElevatorProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/rtc-signaling-contract-probe", async (req, res) => {
    // RTC signaling contract probe 只拉取本机回环协议清单，不创建 WebRTC session、视频或 ROS2 /tf 连接。
    res.json(await buildO7RtcSignalingContractProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/realtime-elevator-preview", async (req, res) => {
    // Realtime/elevator preview 只读取本地 fixture 摘要，不连接云端实时流、ROS2 /tf 或电梯设备。
    res.json(await buildO7RealtimeElevatorPreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/route-replay-preview", async (req, res) => {
    // Route replay preview 只读取 query 指定的本地 JSON fixture，并固定关闭云归档和控制声明。
    res.json(await buildO7RouteReplayPreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/labeling-preview", async (req, res) => {
    // Labeling preview 只读取本地 fixture 摘要，提交、回滚、导出和机器人控制全部关闭。
    res.json(await buildO7LabelingPreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/field-evidence-consumer-ingest", async (req, res) => {
    // Field evidence consumer ingest 把 manifest 入口和 route replay / labeling 两条只读链拼成一份摘要。
    res.json(
      await buildO7FieldEvidenceConsumerIngest({
        manifestJson: queryString(req.query.manifestJson),
        routeReplayFixtureJson: queryString(req.query.routeReplayFixtureJson),
        labelingFixtureJson: queryString(req.query.labelingFixtureJson),
      }),
    );
  });

  workstationApp.get("/api/o7/voice-preview", async (req, res) => {
    // Voice preview 只读取本地 ASR/TTS fixture 摘要，不连接语音 API、不发送 TTS、不播放音频。
    res.json(await buildO7VoicePreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/safe-command-preview", async (req, res) => {
    // Safe command preview 只读取本地命令 envelope fixture，不连接云端、ROS2、Nav2 或硬件。
    res.json(await buildO7SafeCommandPreview({ fixtureJson: queryString(req.query.fixtureJson) }));
  });

  workstationApp.get("/api/o7/cloud-archive/tasks", async (req, res) => {
    // Cloud archive tasks 只读取用户指定的本地 archive fixture，不连接 O6 云端或真实 API。
    res.json(await buildO7CloudArchiveTasks({ archiveJson: queryString(req.query.archiveJson) }));
  });

  workstationApp.get("/api/robot-control/summary", async (req, res) => {
    // Robot Control V1 只读代理上位机 GET status/latest/readback，拒绝浏览器直连和危险 URL。
    res.json(await buildRobotControlSummary(queryString(req.query.baseUrl)));
  });

  workstationApp.post("/api/robot-control/radar/scan-proof/refresh", async (req, res) => {
    // Radar refresh 只允许固定 POST body，不接受浏览器把它改造成通用控制代理。
    const response = await buildRadarScanProofRefreshProxy(queryString(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  workstationApp.post("/api/robot-control/map/proof/refresh", async (req, res) => {
    // Map refresh 只允许固定 POST body，不接受浏览器把它改造成建图/导航控制代理。
    const response = await buildMapProofRefreshProxy(queryString(req.query.baseUrl));
    res
      .status(response.proxy_status === "refresh_forwarded" ? 200 : response.proxy_status === "refresh_rejected" ? 400 : 502)
      .json(response);
  });

  workstationApp.post("/api/robot-control/camera/offer", async (req, res) => {
    // camera offer 只允许本机 Node 代理固定上位机 endpoint，不开放任意 Robot API POST。
    const sourceBaseUrl = queryString(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    if (!normalized.ok) {
      res.status(400).json(unsafeProxyFailure(sourceBaseUrl, normalized.reason, "/api/camera/offer"));
      return;
    }
    const payload = asRecord(req.body);
    const sdp = typeof payload?.sdp === "string" ? payload.sdp.trim() : "";
    const type = payload?.type === "offer" ? "offer" : "";
    if (!payload || !sdp || type !== "offer") {
      res.status(400).json(unsafeProxyFailure(sourceBaseUrl, "invalid_offer_request", "/api/camera/offer"));
      return;
    }
    const remote = await fetchCameraProxySummary(sourceBaseUrl, "/api/camera/offer", { type, sdp });
    if (remote.error) {
      res.status(502).json(unsafeProxyFailure(sourceBaseUrl, remote.error, "/api/camera/offer"));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload);
    const answer = safeAnswerFromPayload(remote.payload);
    const responseBody: RobotControlCameraOfferProxyResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_camera_offer_proxy.v1",
      proxy_status:
        remote.remote_http_status === 200 && dangerous.length === 0 && answer ? "offer_forwarded" : "offer_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/camera/offer",
      remote_http_status: remote.remote_http_status,
      status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "loaded" : "blocked"),
      peer_id: peerIdText(remote.payload?.peer_id),
      answer,
      error: shortText(remote.payload?.error, ""),
      failure_reason:
        dangerous.length > 0
          ? `dangerous_true_field:${dangerous[0]}`
          : !answer
            ? "remote_answer_missing"
            : remote.remote_http_status === 200
              ? ""
              : `offer_http_status_${remote.remote_http_status}`,
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`offer_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
        ...(answer ? [] : ["remote_answer_missing"]),
      ],
    };
    res.status(responseBody.proxy_status === "offer_forwarded" ? 200 : 502).json(responseBody);
  });

  workstationApp.post("/api/robot-control/camera/peers/:peerId/close", async (req, res) => {
    // peer cleanup 只允许关闭已知 peer_id；不接受任意路径、query 拼接或控制类 POST。
    const sourceBaseUrl = queryString(req.query.baseUrl);
    const normalized = normalizeRobotApiBaseUrl(sourceBaseUrl);
    const peerId = peerIdText(req.params.peerId ?? "");
    if (!normalized.ok) {
      res
        .status(400)
        .json(unsafeProxyFailure(sourceBaseUrl, normalized.reason, "/api/camera/peers/{peer_id}/close", peerId));
      return;
    }
    if (!peerId) {
      res
        .status(400)
        .json(unsafeProxyFailure(sourceBaseUrl, "peer_id_invalid", "/api/camera/peers/{peer_id}/close", peerId));
      return;
    }
    const remote = await fetchCameraProxySummary(sourceBaseUrl, `/api/camera/peers/${peerId}/close`, {});
    if (remote.error) {
      res
        .status(502)
        .json(unsafeProxyFailure(sourceBaseUrl, remote.error, "/api/camera/peers/{peer_id}/close", peerId));
      return;
    }
    const dangerous = scanDangerousTrueFields(remote.payload);
    const responseBody: RobotControlCameraCloseProxyResponse = {
      schema: "trashbot.pc_tools_workstation.robot_control_camera_close_proxy.v1",
      proxy_status:
        remote.remote_http_status === 200 && dangerous.length === 0 ? "peer_closed" : "close_failed",
      source: "software_proof",
      proof_status: "not_proven",
      safe_to_control: false,
      delivery_success: false,
      primary_actions_enabled: false,
      pc_only: true,
      robot_control_executed: false,
      source_base_url: sourceBaseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: "/api/camera/peers/{peer_id}/close",
      remote_http_status: remote.remote_http_status,
      peer_id: peerId,
      status: shortText(remote.payload?.status, remote.remote_http_status === 200 ? "closed" : "blocked"),
      error: shortText(remote.payload?.error, ""),
      failure_reason:
        dangerous.length > 0
          ? `dangerous_true_field:${dangerous[0]}`
          : remote.remote_http_status === 200
            ? ""
            : `close_http_status_${remote.remote_http_status}`,
      blocked_reasons: [
        ...(remote.remote_http_status === 200 ? [] : [`close_http_status_${remote.remote_http_status}`]),
        ...dangerous.map((field) => `dangerous_true_field:${field}`),
      ],
    };
    res.status(responseBody.proxy_status === "peer_closed" ? 200 : 502).json(responseBody);
  });

  workstationApp.get("/api/proof-boundary", (_req, res) => {
    // proof boundary 是 UI 的安全锚点，所有控制与交付成功声明都固定关闭。
    res.json(buildProofBoundary());
  });

  workstationApp.use(express.static(DIST_ROOT));

  workstationApp.use((_req, res) => {
    // 构建后可由同一 Node 进程托管静态 UI；缺 dist 时仍返回明确失败。
    res.sendFile(path.join(DIST_ROOT, "index.html"), (error) => {
      if (error) {
        res.status(404).json({
          ...buildProofBoundary(),
          status: "dist_not_built_not_proven",
        });
      }
    });
  });

  return workstationApp;
}

export const app = createWorkstationApp();

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  app.listen(PORT, "127.0.0.1", () => {
    console.log(`pc-tools workstation API listening on http://127.0.0.1:${PORT}`);
  });
}
