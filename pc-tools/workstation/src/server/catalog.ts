import { PROOF_FLAGS } from "../shared/contracts";
import type { RouteDebugSummaryResponse } from "../shared/contracts";
export { buildEvidenceToolsResponse } from "./evidenceAssets";
export { buildTrainingLabelingResponse } from "./datasetAssets";
export { buildHealth, buildProofBoundary } from "./proofBoundary";
export { buildHardwareMaterialsResponse } from "./waveRoverMaterialCoverage";
export { buildO7OperatorConsoleResponse } from "./o7OperatorConsole";
export { buildO7OperatorConsoleAcceptanceResponse } from "./o7OperatorConsoleAcceptance";
export { buildO7PreviewsAcceptanceResponse } from "./o7PreviewsAcceptance";
export { buildO7LiveEndpointsManifest } from "./o7LiveEndpointsManifest";
export { buildO7CloudOperatorConsoleProbe } from "./o7CloudOperatorConsoleProbe";
export { buildO7ConsumerTaskDetail, buildO7ConsumerTaskList, buildO7FieldEvidenceConsumerIngest } from "./o7ConsumerReadAdapter";
export { buildO7CloudArchiveTasksProbe } from "./o7CloudArchiveTasksProbe";
export { buildO7RealtimeElevatorProbe } from "./o7RealtimeElevatorProbe";
export { buildO7RtcSignalingContractProbe } from "./o7RtcSignalingContractProbe";
export { buildO7RealtimeElevatorPreview } from "./o7RealtimeElevatorPreview";
export { buildO7RouteReplayPreview } from "./o7RouteReplayPreview";
export { buildO7LabelingPreview } from "./o7LabelingPreview";
export { buildO7VoicePreview } from "./o7VoicePreview";
export { buildO7SafeCommandPreview } from "./o7SafeCommandPreview";
export { buildO7CloudArchiveTasks } from "./o7CloudArchiveTasks";
export {
  buildMapLifecycleProxy,
  buildNav2NoMotionProofRefreshProxy,
  buildMapProofRefreshProxy,
  buildRadarLifecycleProxy,
  buildRadarScanProofRefreshProxy,
  computeRobotProofRefreshTimeoutMs,
  buildRobotControlSummary,
} from "./robotControlSummary";
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
