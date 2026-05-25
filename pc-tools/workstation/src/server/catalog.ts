import { PROOF_FLAGS } from "../shared/contracts";
import type { RouteDebugSummaryResponse } from "../shared/contracts";
export { buildEvidenceToolsResponse } from "./evidenceAssets";
export { buildHealth, buildProofBoundary, buildTrainingLabelingResponse } from "./proofBoundary";
export { buildHardwareMaterialsResponse } from "./waveRoverMaterialCoverage";
import { displayRoot, ROUTE_ROOT } from "./paths";
import { buildLoadedRouteConsoleSummary, type RouteDebugLoadOptions } from "./routeDebugLoader";

// catalog 层只做只读索引和响应拼装，不创建、不删除、不执行任何工具。
// 本轮旧 Python 已从 pc-tools 移除，因此 Evidence Tools 只扫描 JSON fixture。
// Route Debug 由 Node JSON loader 承担，缺输入、坏 JSON 和越界声明都 fail-closed。
// 这里不读取 vendor 硬件事实，也不解释串口、电压、底盘协议或真实现场状态。

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
