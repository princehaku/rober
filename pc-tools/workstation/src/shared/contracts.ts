export type ProofStatus = "not_proven";

// 工作站只证明本地 Node/Vue 软件入口可用，不证明机器人、ROS2、硬件或现场任务成功。
// 这些字段集中在共享契约里，是为了让 API、UI、测试共用同一个 fail-closed 底座。
// 如果后续要打开真实控制能力，必须先改这里的 literal false，并补硬件和 ROS2 验收证据。
export interface ProofFlags {
  source: "software_proof";
  proof_status: ProofStatus;
  safe_to_control: false;
  delivery_success: false;
  primary_actions_enabled: false;
  pc_only: true;
}

// Evidence Tools 现在索引 JSON fixture 资产，不再索引或执行旧 Python 文件。
// group 对应 fixtures 下的一级目录，便于 reviewer 按证据主题定位材料。
// fixture_files 只暴露仓库相对路径，避免把本机绝对路径泄露到 UI。
export interface EvidenceFixtureRecord {
  group: string;
  category: string;
  fixture_count: number;
  fixture_files: string[];
  summary: string;
}

// Evidence 页面只展示 Node-native 资产索引，不把 fixture 存在解释成现场证据通过。
// total_json_fixtures 是可读索引计数，不是测试通过数或 HIL 通过数。
export interface EvidenceToolsResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.evidence_tools.v2";
  fixture_root: string;
  total_asset_groups: number;
  total_json_fixtures: number;
  categories: Record<string, number>;
  assets: EvidenceFixtureRecord[];
}

export type HardwareMaterialStatus =
  | "material_coverage_complete_software_proof_only"
  | "material_coverage_partial_software_proof_only"
  | "material_coverage_missing_software_proof_only";

export interface HardwareMaterialItem {
  id: string;
  required_path: string;
  description: string;
}

export interface HardwareMaterialGroup {
  group: string;
  fixture_relative_path: string;
  present_materials: string[];
  missing_materials: string[];
  coverage_counts: {
    present: number;
    missing: number;
    required: number;
  };
  status: HardwareMaterialStatus;
}

// WAVE ROVER material coverage 只证明本地材料文件是否齐备，不证明真实 HIL 或底盘可控。
// Hardware 咨询给出的 not_proven token 固化在契约里，避免 UI 或 API 把 coverage 外推成 pass。
export interface HardwareMaterialsResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.hardware_materials.v1";
  fixture_root: string;
  required_materials: HardwareMaterialItem[];
  groups: HardwareMaterialGroup[];
  coverage_summary: {
    groups_total: number;
    groups_complete: number;
    groups_partial: number;
    groups_missing: number;
    required_per_group: number;
  };
  vendor_facts_bounded: string[];
  fail_closed_tokens: string[];
  not_proven_tokens: string[];
  boundary_copy: string;
}

// Route Debug 入口由 Node JSON loader 承担，只读取本地 JSON 并生成 safe summary。
// loader_capabilities 描述的是软件读取能力，不是 Nav2、串口或真实底盘状态。
export interface RouteDebugSummaryResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.route_debug_summary.v2";
  route_root: string;
  node_route_json_loader: {
    name: "node_route_json_loader";
    implementation: "pc-tools/workstation/src/server/routeDebugLoader.ts";
    accepts_local_json: true;
    executes_control: false;
  };
  route_console_summary: {
    schema: "trashbot.pc_route_debug_console.v1";
    evidence_boundary: "software_proof_docker_pc_route_debug_console_gate";
    route_progress: Record<string, unknown> | null;
    keyframe_preflight: Record<string, unknown> | null;
    current_position: Record<string, unknown> | null;
    current_checkpoint: unknown;
    target: Record<string, unknown> | null;
    match_status: string;
    failure: {
      status: string;
      failure_code?: string;
      failure_reason?: string;
      last_error?: string;
      blocked_reasons: string[];
      fail_closed_conditions: string[];
    };
    recent_task: Record<string, unknown> | null;
    route_elevator_reconciliation: {
      lookup_status: string;
      evidence_boundary: "software_proof_docker_pc_route_elevator_console_integration_gate";
      status?: string;
      reconciliation_verdict?: string;
      source_schema?: string;
      source_ref?: string;
      evidence_ref?: string;
      materials_status?: Record<string, unknown>;
      operator_next_steps?: unknown[];
      not_proven?: unknown[];
      delivery_success?: false;
      primary_actions_enabled?: false;
    };
    not_proven: string[];
    delivery_success: false;
    primary_actions_enabled: false;
    console_controls: "read_only";
  };
  missing_fields: string[];
  blocked_reasons: string[];
  input_status: {
    statusJson: string;
    taskRecord: string;
    taskRecordDir: string;
    elevatorRouteReconciliation: string;
  };
}

// Training/Labeling 仍是占位入口，不能被 UI 文案升级成真实流水线。
export interface TrainingLabelingResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.training_labeling.v1";
  entries: Array<{
    name: string;
    path: string;
    status: "placeholder_not_connected";
    real_pipeline_connected: false;
  }>;
}

// Proof Boundary 是跨页面解释源，明确 Node/Vue 当前能证明和不能证明的范围。
export interface ProofBoundaryResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.proof_boundary.v2";
  can_prove: string[];
  not_proven: string[];
  enforced_fields: ProofFlags;
  control_policy: {
    workstation_executes_control: false;
    route_loader_mode: "local_json_readonly";
    recovery_path: string;
  };
}

// Health 只证明 Node API 存活，不证明机器人在线。
export interface HealthResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.health.v1";
  version: string;
  mode: "pc_only_readonly_workstation";
  api_routes: string[];
}

export const WORKSTATION_VERSION = "0.2.0";

// 所有响应必须继承这些字段，避免页面或 API 分支遗漏 fail-closed 语义。
export const PROOF_FLAGS: ProofFlags = {
  source: "software_proof",
  proof_status: "not_proven",
  safe_to_control: false,
  delivery_success: false,
  primary_actions_enabled: false,
  pc_only: true,
};

// API 路由列表给 health 和 UI 共用，减少文档和实现漂移。
export const API_ROUTES = [
  "/api/health",
  "/api/tools/evidence",
  "/api/tools/hardware-materials",
  "/api/tools/training-labeling",
  "/api/route/debug-summary",
  "/api/proof-boundary",
] as const;

// 不可证明项覆盖本轮明确禁止外推的真实链路。
// 这些条目是边界声明，不代表工作站检测过对应硬件或服务。
export const NOT_PROVEN_ITEMS = [
  "real_ros2_runtime",
  "real_nav2_fixed_route_run",
  "real_hardware_or_hil",
  "real_wave_rover_uart_feedback",
  "real_phone_or_cloud_delivery",
  "real_training_or_labeling_pipeline",
  "delivery_success",
] as const;
