import express from "express";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  buildEvidenceToolsResponse,
  buildHardwareMaterialsResponse,
  buildHealth,
  buildO7CloudArchiveTasks,
  buildO7DemoArchive,
  buildO7CloudArchiveTasksProbe,
  buildO5O6CloudRelayHealth,
  buildO5O6ExternalProbeArtifact,
  buildRealMaterialAcceptance,
  buildO7LiveEndpointsManifest,
  buildO7LiveOperatorPanel,
  buildO7DirectUpperStatus,
  buildO7CloudOperatorConsoleProbe,
  buildO7OperatorConsoleAcceptanceResponse,
  buildO7OperatorConsoleResponse,
  buildO7PreviewsAcceptanceResponse,
  buildO7LabelingPreview,
  buildO7RealtimeElevatorProbe,
  buildO7LocalWebrtcCamera,
  buildO7RealtimeElevatorPreview,
  buildO7RouteReplayPreview,
  buildO7RtcSignalingContractProbe,
  buildO7SafeCommandPreview,
  buildO7VoicePreview,
  buildProofBoundary,
  buildRouteDebugSummary,
  buildTrainingLabelingResponse,
} from "./catalog";
import {
  proxyO7DirectUpperFeedbackRequest,
  proxyO7DirectUpperLocalizeReset,
  proxyO7DirectUpperMapList,
  proxyO7DirectUpperMapLoad,
  proxyO7DirectUpperMapReset,
  proxyO7DirectUpperMapSave,
  proxyO7DirectUpperMapStart,
  proxyO7DirectUpperManual,
  proxyO7DirectUpperOperatorReport,
  proxyO7DirectUpperOperatorReportReadback,
  proxyO7DirectUpperRadarScanProofLatest,
  proxyO7DirectUpperRadarScanProofRefresh,
  proxyO7DirectUpperRadarStart,
  proxyO7DirectUpperRadarStop,
  proxyO7DirectUpperStop,
} from "./o7DirectUpperApi";
import {
  proxyO7LocalWebrtcCameraOffer,
  proxyO7LocalWebrtcCameraPeerClose,
} from "./o7LocalWebrtcCamera";

const PORT = Number(process.env.PORT ?? 8787);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_ROOT = path.resolve(__dirname, "../../dist");

function queryString(value: unknown): string {
  // Express query 可能是数组或对象；只接受单个字符串，其他形态 fail closed 为空。
  // 为空会让 catalog 返回 not_proven/blocked，而不是把异常 query 当路径读取。
  return typeof value === "string" ? value : "";
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

  workstationApp.get("/api/o7/live-operator-panel", async (_req, res) => {
    // Live operator panel 只暴露已观测上位机事实和 blocked control shape，不连接底盘或发送命令。
    res.json(await buildO7LiveOperatorPanel());
  });

  workstationApp.get("/api/o7/direct-upper/status", async (_req, res) => {
    // Direct upper mode 是 PC 本机现场入口；只读状态可绕过 cloud relay，但仍保留 ACK/HIL 证明边界。
    res.json(await buildO7DirectUpperStatus());
  });

  workstationApp.post("/api/o7/direct-upper/base/stop", async (req, res) => {
    // stop 只同源转发到 8787 /api/base/stop；HTTP 成功不等于 robot ACK 或 HIL pass。
    const result = await proxyO7DirectUpperStop({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/base/feedback-request", async (req, res) => {
    // feedback-request 只请求 8787 发送非运动 T=130；HTTP 200 仍不能外推为 T=1001/ACK/HIL。
    const result = await proxyO7DirectUpperFeedbackRequest({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/base/manual", async (req, res) => {
    // manual 先经过 PC 低速/短时白名单，再交给 8787 自身 guardrail；失败时默认不转发。
    const result = await proxyO7DirectUpperManual({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/radar/start", async (req, res) => {
    // radar start 只代理 8787 上位机 API，不让浏览器直连 ROS graph 或 LiDAR 串口。
    const result = await proxyO7DirectUpperRadarStart({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/radar/stop", async (req, res) => {
    // radar stop 同样只走 upper API，不能扩展成底盘 stop 或串口写命令。
    const result = await proxyO7DirectUpperRadarStop({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/radar/scan-proof/refresh", async (req, res) => {
    // scan-proof refresh 只代理 upper 只读刷新；PC 不访问 ROS graph、LiDAR 串口或底盘控制面。
    const result = await proxyO7DirectUpperRadarScanProofRefresh({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.get("/api/o7/direct-upper/radar/scan-proof/latest", async (req, res) => {
    // latest 只读回放 upper artifact；它用于证明同源代理拿到 JSON，而不是把一次 proof 外推成连续雷达 ready。
    const result = await proxyO7DirectUpperRadarScanProofLatest({
      body: {
        evidence_ref: queryString(req.query.evidence_ref),
        fixture_mode: queryString(req.query.fixture_mode),
      },
    });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/map/start", async (req, res) => {
    // map lifecycle 入口由 8787/ROS2 侧实现；PC 只负责同源代理和 fail-closed 展示。
    const result = await proxyO7DirectUpperMapStart({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/map/reset", async (req, res) => {
    // reset 需要 evidence_ref 才能现场复盘，PC 不直接操作 slam_toolbox。
    const result = await proxyO7DirectUpperMapReset({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/map/save", async (req, res) => {
    // save 只转发到 upper API，不由工作站写 map artifact。
    const result = await proxyO7DirectUpperMapSave({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/map/load", async (req, res) => {
    // load 由 upper API 判定 map_id 是否有效，PC 不读取 ROS map_server。
    const result = await proxyO7DirectUpperMapLoad({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.get("/api/o7/direct-upper/map/list", async (req, res) => {
    // list 是只读 map artifact 查询，但仍不能被解释成地图可用于 Nav2。
    const result = await proxyO7DirectUpperMapList({
      body: {
        evidence_ref: queryString(req.query.evidence_ref),
        fixture_mode: queryString(req.query.fixture_mode),
      },
    });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/localize/reset", async (req, res) => {
    // localize reset 只能通过 upper API/ROS2 服务执行，浏览器不发布 /initialpose。
    const result = await proxyO7DirectUpperLocalizeReset({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/direct-upper/operator-report", async (req, res) => {
    // operator report 记录 evidence_ref 和人工说明，不替代 stop/status/ACK/HIL 证据。
    const result = await proxyO7DirectUpperOperatorReport({ body: req.body });
    res.status(result.status).json(result.payload);
  });

  workstationApp.get("/api/o7/direct-upper/operator-report", async (req, res) => {
    // report readback 只读 8787 latest artifact；它不触发 base/manual、stop、ROS2 或串口动作。
    const result = await proxyO7DirectUpperOperatorReportReadback({
      body: {
        evidence_ref: queryString(req.query.evidence_ref),
        fixture_mode: queryString(req.query.fixture_mode),
      },
    });
    res.status(result.status).json(result.payload);
  });

  workstationApp.get("/api/o7/cloud-operator-console-probe", async (req, res) => {
    // Cloud probe 只允许后端探测本机回环 HTTP contract，不能变成外网或生产云代理。
    res.json(await buildO7CloudOperatorConsoleProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/cloud-archive/tasks-probe", async (req, res) => {
    // Archive tasks probe 只拉取本机回环 cloud relay contract，不读取远程 URL、不发送任何控制动作。
    res.json(await buildO7CloudArchiveTasksProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o5-o6/cloud-relay-health", async (req, res) => {
    // O5/O6 health probe 只 GET 两个固定只读 health endpoint；不访问 /robots/*、不 POST、不控制机器人。
    res.json(await buildO5O6CloudRelayHealth({
      baseUrl: queryString(req.query.baseUrl),
    }));
  });

  workstationApp.get("/api/o5-o6/external-probe-artifact", async (_req, res) => {
    // 最近一次 external probe artifact 只做本地只读摘要；不执行探针、不联网、不回显路径或 URL。
    res.json(await buildO5O6ExternalProbeArtifact());
  });

  workstationApp.get("/api/real-material/acceptance", async (_req, res) => {
    // Real-material queue 只消费既有 artifact/smoke JSON，不执行 probe、不访问 /robots/*、不创建 WebRTC。
    res.json(await buildRealMaterialAcceptance());
  });

  workstationApp.get("/api/o7/realtime-elevator-probe", async (req, res) => {
    // Realtime/elevator probe 只拉取本机回环 snapshot contract，不读取 ROS2 /tf、地图或电梯设备。
    res.json(await buildO7RealtimeElevatorProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/rtc-signaling-contract-probe", async (req, res) => {
    // RTC signaling contract probe 只拉取本机回环协议清单，不创建 WebRTC session、视频或 ROS2 /tf 连接。
    res.json(await buildO7RtcSignalingContractProbe(queryString(req.query.baseUrl)));
  });

  workstationApp.get("/api/o7/local-webrtc-camera", async (_req, res) => {
    // Local camera smoke 只读 LAN /health 和 /devices，不调用 /offer，也不创建 WebRTC 或控制入口。
    res.json(await buildO7LocalWebrtcCamera());
  });

  workstationApp.post("/api/o7/local-webrtc-camera/offer", async (req, res) => {
    // 浏览器受 CORS 限制不能直接 POST 远端 /offer；这里仅同源转发 WebRTC 信令，不发送机器人控制。
    const result = await proxyO7LocalWebrtcCameraOffer(req.body);
    res.status(result.status).json(result.payload);
  });

  workstationApp.post("/api/o7/local-webrtc-camera/peers/:peerId/close", async (req, res) => {
    // 清理远端 camera peer，避免页面刷新后 8088 保留 active peer；仍不触碰底盘或 ROS2。
    const result = await proxyO7LocalWebrtcCameraPeerClose(req.params.peerId, req.body);
    res.status(result.status).json(result.payload);
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

  workstationApp.get("/api/o7/demo/archive", async (_req, res) => {
    // Demo archive 只读取仓库内固定 fixture，让 O7 首屏可验证非空数据且不能被 query 越权。
    res.json(await buildO7DemoArchive());
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
