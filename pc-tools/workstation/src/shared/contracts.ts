export type ProofStatus = "not_proven";
export type OperatorKrStatus = "draft" | "blocked" | "not_proven";

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

export interface HardwareMaterialGap {
  group: string;
  fixture_relative_path: string;
  missing_material: string;
  recovery_hint: string;
}

export interface HardwareVendorSource {
  path: string;
  fact_ids: ReadonlyArray<string>;
}

export interface HardwareSerialReference {
  vendor_rpi_default_device: "/dev/ttyAMA0";
  vendor_rpi_alternate_device: "/dev/serial0";
  baudrate: 115200;
  orange_pi_device_status: "not_proven";
}

export interface HardwareCommandFact {
  t: 1 | 11 | 13 | 130 | 131 | 142 | 143;
  name: string;
  source_path: string;
  hardware_verified: false;
}

export interface HardwareFeedbackSchema {
  T1001: {
    base_fields: ReadonlyArray<"L" | "R" | "r" | "p" | "y" | "v">;
    module_conditional_fields: ReadonlyArray<string>;
    source_path: string;
  };
}

// WAVE ROVER material coverage 只证明本地材料文件是否齐备，不证明真实 HIL 或底盘可控。
// Hardware 咨询给出的 not_proven token 固化在契约里，避免 UI 或 API 把 coverage 外推成 pass。
export interface HardwareMaterialsResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.hardware_materials.v1";
  fixture_root: string;
  vendor_sources: ReadonlyArray<HardwareVendorSource>;
  hardware_claim_level: "software_material_coverage";
  serial_reference: HardwareSerialReference;
  command_facts: ReadonlyArray<HardwareCommandFact>;
  feedback_schema: HardwareFeedbackSchema;
  required_materials: HardwareMaterialItem[];
  fixture_groups: HardwareMaterialGroup[];
  groups: HardwareMaterialGroup[];
  coverage_summary: {
    groups_total: number;
    groups_complete: number;
    groups_partial: number;
    groups_missing: number;
    required_per_group: number;
  };
  vendor_facts_bounded: string[];
  gaps: HardwareMaterialGap[];
  fail_closed_tokens: string[];
  not_proven_tokens: string[];
  not_proven_boundaries: string[];
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

export type DatasetAssetReadiness =
  | "empty_not_connected"
  | "assets_present_not_connected"
  | "missing_manifest_not_connected"
  | "missing_images_not_connected"
  | "missing_annotations_not_connected";

export interface DatasetAssetCounts {
  total_assets: number;
  structured_files: number;
  manifest_candidates: number;
  images: number;
  annotations: number;
  ignored_python_files: number;
}

export interface DatasetWorkspaceScan {
  name: "dataset" | "labeling";
  root: string;
  status: DatasetAssetReadiness;
  real_pipeline_connected: false;
  asset_counts: DatasetAssetCounts;
  manifest_candidates: string[];
  image_files: string[];
  annotation_files: string[];
  missing_requirements: string[];
  next_actions: string[];
}

// Training/Labeling 只读扫描本地数据集和标注资产，不执行训练、上传或写文件。
export interface TrainingLabelingResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.training_labeling.v2";
  roots: {
    dataset: string;
    labeling: string;
  };
  real_pipeline_connected: false;
  workspaces: DatasetWorkspaceScan[];
  missing_requirements: string[];
  next_actions: string[];
  boundary_copy: string;
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

export interface O7OperatorKrView {
  id: "O7-KR1" | "O7-KR2" | "O7-KR3" | "O7-KR4" | "O7-KR5" | "O7-KR6";
  title: string;
  status: OperatorKrStatus;
  cloud_contract: string;
  pc_surface: string;
  current_view: string[];
  blocked_by: string[];
  next_required_contract: string;
}

export interface O7OperatorActionPreview {
  id: string;
  label: string;
  status: "blocked_not_proven";
  requires_confirmation: true;
  sends_to_robot: false;
  cloud_endpoint: string;
  recovery_path: string;
}

// 板端媒体 preflight 是上车 smoke 之前的缺口摘要；PC 只能展示，不能把它升级成运行态。
export interface O7BoardMediaPreflightSummary {
  schema: "trashbot.o7_board_media_preflight.v1";
  schema_version: 1;
  evidence_boundary: "software_proof_o7_board_media_preflight_contract";
  source: "operator_media_preflight";
  overall_state: "blocked";
  safe_to_control: false;
  primary_actions_enabled: false;
  device_probe_allowed: false;
  device_probe_attempted: false;
  software_proof_only: true;
  blocked_reasons: string[];
  not_proven: string[];
  next_required_evidence: string[];
}

export interface O7RealtimeMapSnapshot {
  schema: "trashbot.o7.realtime_map_snapshot.v1";
  schema_version: 1;
  source: "software_proof";
  snapshot_status: "blocked_not_proven";
  safe_to_control: false;
  primary_actions_enabled: false;
  map_ref: {
    value: string;
    status: "not_proven";
    evidence_ref: string;
  };
  map_frame: {
    value: "map";
    status: "contract_placeholder_not_tf";
    frame_source: "cloud_contract_draft";
  };
  robot_pose: {
    x_m: null;
    y_m: null;
    yaw_rad: null;
    pose_source: "not_connected";
    status: "not_proven";
  };
  pose_freshness: {
    last_update_ms: null;
    age_ms: null;
    latency_lt_2s_proven: false;
    status: "blocked_no_realtime_stream";
  };
  route_membership: {
    route_id: string;
    on_route: false;
    in_elevator_zone: false;
    status: "not_proven";
    reason: string;
  };
  blocked_reasons: string[];
  not_proven: string[];
}

export interface O7ElevatorStateSnapshot {
  schema: "trashbot.o7.elevator_state_snapshot.v1";
  schema_version: 1;
  source: "software_proof";
  snapshot_status: "blocked_not_proven";
  safe_to_control: false;
  primary_actions_enabled: false;
  state_chain: Array<{
    state: string;
    status: "not_proven";
    evidence_ref: string;
  }>;
  current_state: string;
  current_floor_evidence: {
    floor_label: string;
    confidence: null;
    evidence_ref: string;
    status: "not_proven";
  };
  target_floor: {
    floor_label: string;
    confirmation_status: "not_proven";
  };
  human_takeover: {
    required: true;
    reason: string;
    operator_action: string;
  };
  blocked_reasons: string[];
  not_proven: string[];
}

// 历史路线回放 snapshot 只定义 O7-KR3 需要的字段槽位，不能被 UI 当作真实归档。
// playback_available 和 real_archive_connected 固定 false，是为了让未来接 O6 API 前保持关闸。
export interface O7RouteReplaySnapshot {
  schema: "trashbot.o7.route_replay_snapshot.v1";
  schema_version: 1;
  source: "software_proof";
  snapshot_status: "blocked_not_proven";
  safe_to_control: false;
  primary_actions_enabled: false;
  playback_available: false;
  real_archive_connected: false;
  task_selector: {
    source_contract: "history.route_replay.v1";
    status: "blocked_no_cloud_task_archive";
    available_task_count: 0;
    selected_task_id: "not_connected";
    task_list_ref: "missing_o6_cloud_task_archive";
    selection_required: true;
  };
  selected_task: {
    task_id: "not_connected";
    robot_id: "not_connected";
    route_id: "not_connected";
    started_at_ms: null;
    completed_at_ms: null;
    status: "not_proven";
    evidence_ref: "missing_selected_task_record";
  };
  trajectory: {
    frame_count: 0;
    sample_frames: [];
    frame_schema: "pending_cloud_trajectory_frame_v1";
    map_frame: "not_connected";
    status: "blocked_no_trajectory_api";
  };
  playback_cursor: {
    frame_index: null;
    timestamp_ms: null;
    playing: false;
    speed: 0;
    status: "blocked_not_available";
  };
  keyframes: {
    count: 0;
    sample_refs: [];
    status: "blocked_no_keyframe_archive";
  };
  evidence_refs: {
    task_archive: "missing_o6_cloud_task_archive";
    trajectory_api: "missing_trajectory_api";
    keyframe_archive: "missing_keyframe_archive";
    state_transition_archive: "missing_state_transition_archive";
  };
  state_transitions: {
    count: 0;
    sample: [];
    status: "blocked_no_state_transition_archive";
    gaps: string[];
  };
  blocked_reasons: string[];
  not_proven: string[];
  next_required_evidence: string[];
}

// 标注队列 snapshot 只定义 O7-KR4 的字段槽位；提交、回滚和导出必须显式关闭。
// allowed_label_types 是未来云端 schema 的占位清单，不代表真实 annotation API 已返回。
export interface O7LabelingQueueSnapshot {
  schema: "trashbot.o7.labeling_queue_snapshot.v1";
  schema_version: 1;
  source: "software_proof";
  snapshot_status: "blocked_not_proven";
  safe_to_control: false;
  primary_actions_enabled: false;
  submit_enabled: false;
  rollback_enabled: false;
  real_annotation_api_connected: false;
  dataset_export_available: false;
  review_queue: {
    source_contract: "labeling.review_queue.v1";
    status: "blocked_no_annotation_api";
    available_item_count: 0;
    assigned_operator: "not_connected";
    queue_ref: "missing_o6_annotation_review_queue";
    selection_required: true;
  };
  selected_item: {
    item_id: "not_connected";
    task_id: "not_connected";
    frame_id: "not_connected";
    media_ref: "missing_review_item_media_ref";
    evidence_ref: "missing_selected_labeling_item_record";
    status: "not_proven";
  };
  label_schema: {
    schema_ref: "missing_label_schema";
    version: "not_connected";
    status: "blocked_no_label_schema_api";
    required_fields: [];
  };
  allowed_label_types: Array<{
    type: "elevator_door_state" | "floor_label" | "obstacle_type";
    status: "contract_placeholder_not_api";
    values: string[];
  }>;
  draft_labels: {
    count: 0;
    items: [];
    status: "blocked_no_selected_item";
    autosave_available: false;
  };
  submit_audit: {
    status: "blocked_not_available";
    endpoint: "POST /api/o6/annotations (future, disabled)";
    last_submit_id: "not_connected";
    idempotency_key_required: true;
    audit_ref: "missing_submit_audit_log";
  };
  rollback_audit: {
    status: "blocked_not_available";
    endpoint: "POST /api/o6/annotations/rollback (future, disabled)";
    last_rollback_id: "not_connected";
    requires_reason: true;
    audit_ref: "missing_rollback_audit_log";
  };
  dataset_export: {
    status: "blocked_not_available";
    export_ref: "missing_training_dataset_export";
    supported_formats: [];
    gaps: string[];
  };
  blocked_reasons: string[];
  not_proven: string[];
  next_required_evidence: string[];
}

// O7 Operator Console 是 cloud-contract driven 的最小视图，不能由前端伪造机器人事实。
// command_previews 只表达将来安全 API 的 envelope，不代表按钮会发送真实控制。
export interface O7OperatorConsoleResponse extends ProofFlags {
  schema: "trashbot.o7.operator_console.v1";
  contract_source: "cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py";
  workstation_endpoint: "/api/o7/operator-console";
  cloud_api_status: "draft_blocked_not_proven";
  robot_connection: "not_connected_by_pc";
  realtime_stream_status: "blocked_not_proven";
  operator_mode: "observe_only";
  board_media_preflight_required: true;
  board_media_preflight_schema: "trashbot.o7_board_media_preflight.v1";
  board_media_preflight_state: "blocked";
  board_media_preflight_summary: O7BoardMediaPreflightSummary;
  realtime_map_snapshot: O7RealtimeMapSnapshot;
  elevator_state_snapshot: O7ElevatorStateSnapshot;
  route_replay_snapshot: O7RouteReplaySnapshot;
  labeling_queue_snapshot: O7LabelingQueueSnapshot;
  manual_control_policy: {
    pc_direct_robot_connection: false;
    cloud_mediated_only: true;
    command_dispatch_enabled: false;
    confirmation_required_before_future_dispatch: true;
    success_claim_allowed: false;
  };
  kr_views: O7OperatorKrView[];
  command_previews: O7OperatorActionPreview[];
  blocked_reasons: string[];
  not_proven: string[];
  recovery_paths: string[];
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
  "/api/hardware/wave-rover/material-coverage",
  "/api/tools/hardware-materials",
  "/api/tools/training-labeling",
  "/api/route/debug-summary",
  "/api/o7/operator-console",
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
  "real_o7_realtime_cloud_stream",
  "real_o7_route_replay_archive",
  "real_o7_trajectory_playback",
  "real_o7_labeling_review_queue",
  "real_o7_annotation_submit",
  "real_o7_dataset_export",
  "real_o7_operator_command_dispatch",
  "delivery_success",
] as const;
