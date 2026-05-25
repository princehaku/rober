import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildEvidenceToolsResponse,
  buildHardwareMaterialsResponse,
  buildHealth,
  buildProofBoundary,
  buildRouteDebugSummary,
  buildTrainingLabelingResponse,
} from "./catalog";

const app = express();
const PORT = Number(process.env.PORT ?? 8787);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_ROOT = path.resolve(__dirname, "../../dist");

// Express 只承载本地 PC API 和构建后的静态 UI。
// 这里不挂载任何 ROS2、串口、控制或云端生产客户端。
app.use(express.json());

app.get("/api/health", (_req, res) => {
  // health 也保留 fail-closed 字段，避免监控把服务在线误读为机器人在线。
  res.json(buildHealth());
});

app.get("/api/tools/evidence", async (_req, res) => {
  // API 只读索引 JSON fixture，不执行任何外部脚本或现场链路。
  res.json(await buildEvidenceToolsResponse());
});

app.get("/api/tools/hardware-materials", async (_req, res) => {
  // Hardware materials 只读扫描 WAVE ROVER fixture 文件名，不打开串口或执行 HIL。
  res.json(await buildHardwareMaterialsResponse());
});

app.get("/api/tools/training-labeling", async (_req, res) => {
  // 训练/标注第一阶段是占位入口，必须显式声明未接真实流水线。
  res.json(await buildTrainingLabelingResponse());
});

function queryString(value: unknown): string {
  // Express query 可能是数组或对象；只接受单个字符串，其他形态 fail closed 为空。
  // 为空会让 catalog 返回 not_proven/blocked，而不是把异常 query 当路径读取。
  return typeof value === "string" ? value : "";
}

app.get("/api/route/debug-summary", async (req, res) => {
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

app.get("/api/proof-boundary", (_req, res) => {
  // proof boundary 是 UI 的安全锚点，所有控制与交付成功声明都固定关闭。
  res.json(buildProofBoundary());
});

app.use(express.static(DIST_ROOT));

app.use((_req, res) => {
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

app.listen(PORT, "127.0.0.1", () => {
  console.log(`pc-tools workstation API listening on http://127.0.0.1:${PORT}`);
});
