import { promises as fs } from "node:fs";
import path from "node:path";
import {
  API_ROUTES,
  NOT_PROVEN_ITEMS,
  PROOF_FLAGS,
  WORKSTATION_VERSION,
} from "../shared/contracts";
import type {
  EvidenceFixtureRecord,
  EvidenceToolsResponse,
  HealthResponse,
  ProofBoundaryResponse,
  RouteDebugSummaryResponse,
  TrainingLabelingResponse,
} from "../shared/contracts";
import { buildLoadedRouteConsoleSummary, type RouteDebugLoadOptions } from "./routeDebugLoader";

const REPO_ROOT = path.resolve(process.cwd(), "../..");
const EVIDENCE_ROOT = path.join(REPO_ROOT, "pc-tools", "evidence");
const EVIDENCE_FIXTURE_ROOT = path.join(EVIDENCE_ROOT, "fixtures");
const ROUTE_ROOT = path.join(REPO_ROOT, "pc-tools", "route");

// catalog 层只做只读索引和响应拼装，不创建、不删除、不执行任何工具。
// 本轮旧 Python 已从 pc-tools 移除，因此 Evidence Tools 只扫描 JSON fixture。
// Route Debug 由 Node JSON loader 承担，缺输入、坏 JSON 和越界声明都 fail-closed。
// 这里不读取 vendor 硬件事实，也不解释串口、电压、底盘协议或真实现场状态。
const CATEGORY_RULES: Array<[string, string]> = [
  ["wave_rover", "hardware evidence"],
  ["hardware", "hardware evidence"],
  ["cloud", "cloud evidence"],
  ["mobile", "mobile evidence"],
  ["phone", "mobile evidence"],
  ["route", "route evidence"],
  ["elevator", "route evidence"],
  ["field", "field evidence"],
  ["terminal", "terminal evidence"],
];

function displayRoot(absPath: string): string {
  // API 只暴露仓库内相对路径，避免把本机盘符或用户目录泄露到 UI。
  return path.relative(REPO_ROOT, absPath).split(path.sep).join("/");
}

function classifyAsset(name: string): string {
  // 分类只用于 UI 分组，不参与 pass/fail 或现场证明判定。
  const normalized = name.toLowerCase();
  return CATEGORY_RULES.find(([needle]) => normalized.includes(needle))?.[1] ?? "general evidence";
}

async function listJsonFixtures(root: string): Promise<string[]> {
  // 缺目录时返回空索引而不是抛 500，调用方会继续保留 not_proven 语义。
  try {
    const entries = await fs.readdir(root, { withFileTypes: true });
    const nested = await Promise.all(
      entries.map(async (entry) => {
        const absPath = path.join(root, entry.name);
        if (entry.isDirectory()) {
          return listJsonFixtures(absPath);
        }
        return entry.isFile() && entry.name.endsWith(".json") ? [absPath] : [];
      }),
    );
    return nested.flat().sort((left, right) => left.localeCompare(right));
  } catch {
    return [];
  }
}

async function readableJsonCount(files: string[]): Promise<number> {
  // 读取并解析 JSON 是为了证明 fixture 索引可读，但不把内容搬进 API 响应。
  const results = await Promise.all(
    files.map(async (file) => {
      try {
        JSON.parse(await fs.readFile(file, "utf8"));
        return 1;
      } catch {
        return 0;
      }
    }),
  );
  return results.reduce<number>((sum, value) => sum + value, 0);
}

function groupFromFixture(file: string): string {
  // fixtures 下一级目录是证据主题；根目录散落 JSON 时归入 root。
  const relative = path.relative(EVIDENCE_FIXTURE_ROOT, file).split(path.sep);
  return relative.length > 1 ? (relative[0] ?? "root") : "root";
}

export async function buildEvidenceToolsResponse(): Promise<EvidenceToolsResponse> {
  // Evidence Tools 不再扫描 .py，不读取 docstring，也不保留旧 gate 执行语义。
  const fixtures = await listJsonFixtures(EVIDENCE_FIXTURE_ROOT);
  const groups = fixtures.reduce<Record<string, string[]>>((acc, file) => {
    const group = groupFromFixture(file);
    acc[group] = [...(acc[group] ?? []), displayRoot(file)];
    return acc;
  }, {});

  const assets: EvidenceFixtureRecord[] = Object.entries(groups)
    .map(([group, files]) => ({
      group,
      category: classifyAsset(group),
      fixture_count: files.length,
      fixture_files: files.sort((left, right) => left.localeCompare(right)),
      summary: "JSON fixture index; software proof only; no field success implied.",
    }))
    .sort((left, right) => left.group.localeCompare(right.group));

  const categories = assets.reduce<Record<string, number>>((acc, asset) => {
    // 分类计数帮助 reviewer 扫描 fixture 主题，不代表通过数量。
    acc[asset.category] = (acc[asset.category] ?? 0) + asset.fixture_count;
    return acc;
  }, {});

  return {
    schema: "trashbot.pc_tools_workstation.evidence_tools.v2",
    ...PROOF_FLAGS,
    fixture_root: displayRoot(EVIDENCE_FIXTURE_ROOT),
    total_asset_groups: assets.length,
    total_json_fixtures: await readableJsonCount(fixtures),
    categories,
    assets,
  };
}

export async function buildRouteDebugSummary(options: RouteDebugLoadOptions = {}): Promise<RouteDebugSummaryResponse> {
  // Route Debug 只暴露 Node JSON Loader 能力，不再把旧调试脚本当 gate 文件。
  const loaded = await buildLoadedRouteConsoleSummary(options);

  return {
    schema: "trashbot.pc_tools_workstation.route_debug_summary.v2",
    ...PROOF_FLAGS,
    route_root: displayRoot(ROUTE_ROOT),
    node_route_json_loader: {
      name: "node_route_json_loader",
      implementation: "pc-tools/workstation/src/server/routeDebugLoader.ts",
      accepts_local_json: true,
      executes_control: false,
    },
    route_console_summary: loaded.route_console_summary,
    missing_fields: [...(options.statusJson ? [] : ["status_json"]), "real_nav2_runtime"],
    blocked_reasons: loaded.blocked_reasons,
    input_status: loaded.input_status,
  };
}

export async function buildTrainingLabelingResponse(): Promise<TrainingLabelingResponse> {
  // Training/Labeling 仍未接真实流水线，页面只能显示占位状态。
  const entries = ["training", "labeling"].map((name) => ({
    name,
    path: `pc-tools/${name}`,
    status: "placeholder_not_connected" as const,
    real_pipeline_connected: false as const,
  }));

  return {
    schema: "trashbot.pc_tools_workstation.training_labeling.v1",
    ...PROOF_FLAGS,
    entries,
  };
}

export function buildProofBoundary(): ProofBoundaryResponse {
  // Proof Boundary 把 Node/Vue 可证明的软件形状与真实机器人能力明确分开。
  return {
    schema: "trashbot.pc_tools_workstation.proof_boundary.v2",
    ...PROOF_FLAGS,
    can_prove: [
      "Node/Vue workstation can index local JSON fixtures under pc-tools/evidence/fixtures",
      "Node Route JSON Loader can read local status/task/reconciliation JSON into a safe summary",
      "UI/API expose fail-closed software proof fields",
    ],
    not_proven: [...NOT_PROVEN_ITEMS],
    enforced_fields: PROOF_FLAGS,
    control_policy: {
      workstation_executes_control: false,
      route_loader_mode: "local_json_readonly",
      recovery_path: "Load local JSON proof files in the Node workstation and attach resulting summaries to sprint evidence.",
    },
  };
}

export function buildHealth(): HealthResponse {
  // health 只证明 Node API 存活，不证明机器人、ROS2 或云端链路存活。
  return {
    schema: "trashbot.pc_tools_workstation.health.v1",
    ...PROOF_FLAGS,
    version: WORKSTATION_VERSION,
    mode: "pc_only_readonly_workstation",
    api_routes: [...API_ROUTES],
  };
}
