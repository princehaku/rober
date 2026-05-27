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

// Safe command snapshot 是 O7-KR6 的只读安全命令契约，不能被 UI 解释成真实控制能力。
// 顶层 enabled 字段全部固定 false，是为了给未来云端 command API 留槽时仍然 fail-closed。
export interface O7SafeCommandSnapshot {
  schema: "trashbot.o7.safe_command_snapshot.v1";
  schema_version: 1;
  source: "software_proof";
  snapshot_status: "blocked_not_proven";
  safe_to_control: false;
  primary_actions_enabled: false;
  command_dispatch_enabled: false;
  manual_control_enabled: false;
  navigate_goal_enabled: false;
  keyboard_control_enabled: false;
  real_command_api_connected: false;
  real_robot_ack_connected: false;
  manual_turn_envelope: {
    source_contract: "operator.safe_command_preview.v1";
    status: "blocked_not_proven";
    sends_to_robot: false;
    accepted_input_slots: string[];
    requested_direction: "not_connected";
    velocity_limited: true;
    steering_limited: true;
    evidence_ref: "missing_manual_turn_command_envelope_trace";
  };
  velocity_limits: {
    max_linear_mps: null;
    max_angular_radps: null;
    source: "not_connected";
    status: "blocked_no_robot_hil_limits";
    hardware_verified: false;
  };
  steering_limits: {
    max_steering_angle_rad: null;
    max_turn_rate_radps: null;
    source: "not_connected";
    status: "blocked_no_robot_hil_limits";
    hardware_verified: false;
  };
  navigate_goal_envelope: {
    source_contract: "operator.safe_command_preview.v1";
    status: "blocked_not_proven";
    sends_to_robot: false;
    goal_source: "map_click_disabled";
    requires_map_goal_slot: true;
    evidence_ref: "missing_navigate_goal_command_envelope_trace";
  };
  map_goal_slot: {
    map_frame: "map";
    x_m: null;
    y_m: null;
    yaw_rad: null;
    status: "empty_not_connected";
    evidence_ref: "missing_map_goal_selection_trace";
  };
  cloud_command_endpoint: {
    manual_turn: "POST /api/o7/operator/commands/manual-turn (future, disabled)";
    navigate_goal: "POST /api/o7/operator/commands/navigate-goal (future, disabled)";
    status: "future_disabled";
    sends_to_robot: false;
  };
  idempotency_key_requirement: {
    required: true;
    header: "Idempotency-Key";
    status: "required_not_connected";
    replay_policy: "reject_duplicate_future_contract";
  };
  confirmation_policy: {
    manual_turn_requires_confirmation: true;
    navigate_goal_requires_confirmation: true;
    keyboard_control_requires_hold: true;
    status: "blocked_no_confirmation_ui";
  };
  robot_ack_status: {
    ack_status: "blocked_no_robot_ack_contract";
    last_command_id: "not_connected";
    ack_ref: "missing_robot_command_ack";
    timeout_ms: null;
    cancel_ack_ref: "missing_robot_cancel_ack";
    stop_ack_ref: "missing_robot_stop_ack";
    recovery_ref: "missing_robot_recovery_event";
  };
  evidence_gaps: {
    timeout: "missing_command_timeout_policy_and_trace";
    cancel: "missing_cancel_command_ack_trace";
    stop: "missing_stop_command_ack_trace";
    recovery: "missing_robot_recovery_event_trace";
  };
  blocked_reasons: string[];
  not_proven: string[];
  next_required_evidence: string[];
}

export interface O7SafeCommandPreviewRefSet {
  fixture_ref: string;
  session_evidence_ref: string;
  ack_ref: string;
  cancel_ack_ref: string;
  stop_ack_ref: string;
  recovery_ref: string;
  audit_refs: string[];
}

// Safe command preview 是 O7-KR6 的 PC-only 本地 fixture adapter，不是控制 API。
// 它只把手控/寻路 envelope 压成安全摘要，所有真实发送、ACK 和键盘控制都固定关闭。
export interface O7SafeCommandPreviewResponse extends ProofFlags {
  schema: "trashbot.o7.safe_command_preview.v1";
  schema_version: 1;
  preview_status: "fixture_preview_ready" | "blocked_not_proven";
  input_status: {
    fixture_json: string;
    status:
      | "loaded"
      | "not_provided"
      | "missing"
      | "read_error"
      | "bad_json"
      | "not_object"
      | "unsupported_schema"
      | "unsafe_copy"
      | "success_claim"
      | "control_claim"
      | "dispatch_enabled_claim"
      | "manual_enabled_claim"
      | "navigate_enabled_claim"
      | "keyboard_enabled_claim"
      | "real_command_api_claim"
      | "real_robot_ack_claim"
      | "robot_control_executed_claim"
      | "ack_success_claim"
      | "hardware_verified_claim";
    failure_reason: string;
  };
  source_fixture_schema: "trashbot.o7.safe_command_fixture.v1" | "not_loaded";
  command_dispatch_enabled: false;
  manual_control_enabled: false;
  navigate_goal_enabled: false;
  keyboard_control_enabled: false;
  real_command_api_connected: false;
  real_robot_ack_connected: false;
  robot_control_executed: false;
  command_session: {
    command_session_id: string;
    source: "local_json_fixture";
    evidence_ref: string;
    audit_refs: string[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  manual_turn_envelope_summary: {
    sends_to_robot: false;
    requested_direction: string;
    velocity_limited: true;
    steering_limited: true;
    evidence_ref: string;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  navigate_goal_envelope_summary: {
    sends_to_robot: false;
    goal_source: string;
    map_frame: string;
    x_m: number | null;
    y_m: number | null;
    yaw_rad: number | null;
    evidence_ref: string;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  velocity_limits: {
    max_linear_mps: number | null;
    max_angular_radps: number | null;
    source: string;
    hardware_verified: false;
    status: "fixture_limit_summary_only" | "blocked_not_proven";
  };
  steering_limits: {
    max_steering_angle_rad: number | null;
    max_turn_rate_radps: number | null;
    source: string;
    hardware_verified: false;
    status: "fixture_limit_summary_only" | "blocked_not_proven";
  };
  map_goal_slot: {
    map_frame: string;
    x_m: number | null;
    y_m: number | null;
    yaw_rad: number | null;
    status: "fixture_slot_summary_only" | "blocked_not_proven";
    evidence_ref: string;
  };
  idempotency_key_requirement: {
    required: true;
    key_ref: string;
    header: "Idempotency-Key";
    status: "fixture_requirement_summary_only" | "blocked_not_proven";
  };
  confirmation_policy: {
    manual_turn_requires_confirmation: true;
    navigate_goal_requires_confirmation: true;
    keyboard_control_requires_hold: true;
    status: "fixture_policy_summary_only" | "blocked_not_proven";
  };
  robot_ack_summary: {
    ack_status: "blocked_not_proven";
    last_command_id: string;
    ack_ref: string;
    timeout_ms: number | null;
    cancel_ack_ref: string;
    stop_ack_ref: string;
    recovery_ref: string;
    status: "blocked_not_proven";
  };
  evidence_gaps: string[];
  evidence_refs: O7SafeCommandPreviewRefSet;
  blocked_reasons: string[];
  not_proven: string[];
}

export interface O7CloudArchiveTaskSummary {
  task_id: string;
  robot_id: string;
  route_id: string;
  status: string;
  started_at_ms: number | null;
  updated_at_ms: number | null;
  evidence_ref: string;
}

export interface O7CloudArchiveTaskSafeSummaries {
  trajectory: {
    frame_count: number;
    sample_refs: string[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  events: {
    event_count: number;
    sample_types: string[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  labels: {
    label_count: number;
    sample_types: string[];
    real_annotation_api_connected: false;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  voice: {
    asr_event_count: number;
    tts_draft_count: number;
    real_voice_api_connected: false;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  commands: {
    command_count: number;
    sample_kinds: string[];
    real_command_api_connected: false;
    robot_control_executed: false;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
}

export interface O7RouteReplayInspectorFrame {
  frame_index: number;
  timestamp_ms: number | null;
  x_m: number | null;
  y_m: number | null;
  yaw_rad: number | null;
  speed_mps: number | null;
  state: string;
  evidence_ref: string;
}

export interface O7RouteReplayInspectorEvent {
  event_type: string;
  state: string;
  timestamp_ms: number | null;
  evidence_ref: string;
}

export interface O7RouteReplayInspector {
  status: "fixture_inspector_ready" | "blocked_not_proven";
  selected_task_id: string | null;
  map_frame: string;
  frame_count: number;
  sample_frames: O7RouteReplayInspectorFrame[];
  event_timeline: O7RouteReplayInspectorEvent[];
  keyframe_refs: string[];
  cursor_initial_state: {
    playing: false;
    safe_to_play: false;
    speed: 0;
    frame_index: number | null;
  };
  blocked_reasons: string[];
  not_proven: string[];
}

export interface O7LabelingQueueInspectorLabelSample {
  label_type: string;
  value: string;
  status: string;
  evidence_ref: string;
}

export interface O7LabelingQueueInspectorReviewItem {
  item_id: string;
  task_id: string;
  frame_id: string;
  media_ref: string;
  evidence_ref: string;
  current_labels: {
    count: number;
    sample: O7LabelingQueueInspectorLabelSample[];
  };
}

export interface O7LabelingQueueInspector {
  status: "fixture_labeling_ready" | "blocked_not_proven";
  selected_task_id: string | null;
  review_item_count: number;
  sample_review_items: O7LabelingQueueInspectorReviewItem[];
  label_schema: {
    schema_ref: string;
    version: string;
    required_fields: string[];
    allowed_fields: string[];
  };
  allowed_label_types: string[];
  draft_labels: {
    count: number;
    sample: O7LabelingQueueInspectorLabelSample[];
    autosave_available: false;
  };
  dataset_export: {
    available: false;
    status: "blocked_not_available" | "fixture_summary_only";
    export_ref: string;
    supported_formats: string[];
    gaps: string[];
  };
  submit_enabled: false;
  rollback_enabled: false;
  dataset_export_available: false;
  real_annotation_api_connected: false;
  blocked_reasons: string[];
  not_proven: string[];
}

export interface O7VoiceAsrTtsInspectorAsrEvent {
  event_type: string;
  timestamp_ms: number | null;
  transcript: string;
  confidence: number | null;
  evidence_ref: string;
}

export interface O7VoiceAsrTtsInspectorTranscriptSlot {
  text: string;
  timestamp_ms: number | null;
  confidence: number | null;
  evidence_ref: string;
  status: "fixture_summary_only" | "empty_not_proven" | "blocked_not_proven";
}

export interface O7VoiceAsrTtsInspector {
  status: "fixture_voice_ready" | "blocked_not_proven";
  selected_task_id: string | null;
  voice_session: {
    session_id: string;
    source: "local_json_fixture";
    evidence_ref: string;
    audit_refs: string[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  asr_event_count: number;
  sample_asr_events: O7VoiceAsrTtsInspectorAsrEvent[];
  latest_partial: O7VoiceAsrTtsInspectorTranscriptSlot;
  latest_final: O7VoiceAsrTtsInspectorTranscriptSlot;
  tts_draft: {
    text: string;
    text_length: number;
    voice_profile: string;
    language: string;
    confirmation_required: true;
    status: "fixture_draft_only" | "blocked_not_proven";
  };
  speaker_dispatch: {
    sends_to_robot: false;
    speaker_dispatch_enabled: false;
    ack_status: string;
    speaker_ack_ref: string;
    failure_event_ref: string;
    failure_refs: string[];
    status: "blocked_not_proven";
  };
  media_preflight_dependency: {
    required: true;
    source_schema: "trashbot.o7_board_media_preflight.v1";
    status: string;
    dependency_ref: string;
    gaps: string[];
  };
  asr_stream_connected: false;
  tts_send_enabled: false;
  speaker_dispatch_enabled: false;
  real_voice_api_connected: false;
  real_asr_tts_runtime_connected: false;
  blocked_reasons: string[];
  not_proven: string[];
}

export interface O7SafeCommandInspectorCommandSample {
  command_id: string;
  command_type: string;
  status: string;
  envelope_ref: string;
  idempotency_key_ref: string;
  evidence_ref: string;
}

// safe_command_inspector 是 O7-KR6 在 cloud archive selected task 上的只读检查视图。
// 它复用本地 fixture 白名单字段，所有真实控制、键盘、ACK 和发送能力继续固定 false。
export interface O7SafeCommandInspector {
  status: "fixture_command_ready" | "blocked_not_proven";
  selected_task_id: string | null;
  command_session: {
    command_session_id: string;
    source: "local_json_fixture";
    evidence_ref: string;
    audit_refs: string[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  command_count: number;
  sample_commands: O7SafeCommandInspectorCommandSample[];
  manual_turn_envelope: {
    sends_to_robot: false;
    requested_direction: string;
    velocity_limited: true;
    steering_limited: true;
    evidence_ref: string;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  navigate_goal_envelope: {
    sends_to_robot: false;
    goal_source: string;
    map_frame: string;
    x_m: number | null;
    y_m: number | null;
    yaw_rad: number | null;
    evidence_ref: string;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  velocity_limits: {
    max_linear_mps: number | null;
    max_angular_radps: number | null;
    source: string;
    hardware_verified: false;
    status: "fixture_limit_summary_only" | "blocked_not_proven";
  };
  steering_limits: {
    max_steering_angle_rad: number | null;
    max_turn_rate_radps: number | null;
    source: string;
    hardware_verified: false;
    status: "fixture_limit_summary_only" | "blocked_not_proven";
  };
  map_goal_slot: {
    map_frame: string;
    x_m: number | null;
    y_m: number | null;
    yaw_rad: number | null;
    status: "fixture_slot_summary_only" | "blocked_not_proven";
    evidence_ref: string;
  };
  idempotency_key_requirement: {
    required: true;
    key_ref: string;
    header: "Idempotency-Key";
    status: "fixture_requirement_summary_only" | "blocked_not_proven";
  };
  confirmation_policy: {
    manual_turn_requires_confirmation: true;
    navigate_goal_requires_confirmation: true;
    keyboard_control_requires_hold: true;
    status: "fixture_policy_summary_only" | "blocked_not_proven";
  };
  robot_ack_blocked_summary: {
    ack_status: "blocked_not_proven";
    last_command_id: string;
    ack_ref: string;
    timeout_ms: number | null;
    cancel_ack_ref: string;
    stop_ack_ref: string;
    recovery_ref: string;
    status: "blocked_not_proven";
  };
  evidence_gaps: string[];
  command_dispatch_enabled: false;
  manual_control_enabled: false;
  navigate_goal_enabled: false;
  keyboard_control_enabled: false;
  real_command_api_connected: false;
  real_robot_ack_connected: false;
  robot_control_executed: false;
  safe_to_control: false;
  primary_actions_enabled: false;
  delivery_success: false;
  blocked_reasons: string[];
  not_proven: string[];
}

// Cloud archive task API 是 O7 的统一数据源雏形，但当前只读本地 fixture。
// fixed false 字段覆盖 KR3/KR4/KR5/KR6，避免 UI 把 archive 摘要误读成真实云能力。
export interface O7CloudArchiveTasksResponse extends ProofFlags {
  schema: "trashbot.o7.cloud_archive_tasks.v1";
  schema_version: 1;
  archive_status: "fixture_archive_ready" | "blocked_not_proven";
  input_status: {
    archive_json: string;
    status:
      | "loaded"
      | "not_provided"
      | "missing"
      | "read_error"
      | "bad_json"
      | "not_object"
      | "unsupported_schema"
      | "unsafe_copy"
      | "success_claim"
      | "control_claim"
      | "real_api_claim";
    failure_reason: string;
  };
  source_fixture_schema: "trashbot.o7.cloud_archive_fixture.v1" | "not_loaded";
  real_cloud_archive_connected: false;
  real_realtime_api_connected: false;
  real_annotation_api_connected: false;
  real_voice_api_connected: false;
  real_command_api_connected: false;
  robot_control_executed: false;
  task_list: {
    source: "local_json_fixture";
    total_tasks: number;
    tasks: O7CloudArchiveTaskSummary[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  selected_task: O7CloudArchiveTaskSummary | null;
  latest_task: O7CloudArchiveTaskSummary | null;
  safe_summaries: O7CloudArchiveTaskSafeSummaries;
  route_replay_inspector: O7RouteReplayInspector;
  labeling_queue_inspector: O7LabelingQueueInspector;
  voice_asr_tts_inspector: O7VoiceAsrTtsInspector;
  safe_command_inspector: O7SafeCommandInspector;
  fixed_false_fields: {
    real_cloud_archive_connected: false;
    real_realtime_api_connected: false;
    real_annotation_api_connected: false;
    real_voice_api_connected: false;
    real_command_api_connected: false;
    real_robot_ack_connected: false;
    real_asr_tts_runtime_connected: false;
    command_dispatch_enabled: false;
    manual_control_enabled: false;
    navigate_goal_enabled: false;
    keyboard_control_enabled: false;
    asr_stream_connected: false;
    tts_send_enabled: false;
    speaker_dispatch_enabled: false;
    safe_to_control: false;
    delivery_success: false;
    primary_actions_enabled: false;
    pc_only: true;
    robot_control_executed: false;
  };
  blocked_reasons: string[];
  not_proven: string[];
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

export interface O7RouteReplayPreviewFrame {
  frame_index: number | null;
  timestamp_ms: number | null;
  pose: {
    x_m: number | null;
    y_m: number | null;
    yaw_rad: number | null;
  };
  velocity: {
    linear_mps: number | null;
    angular_radps: number | null;
  };
  state: string;
  evidence_ref: string;
}

export interface O7RouteReplayPreviewTransition {
  from: string;
  to: string;
  timestamp_ms: number | null;
  evidence_ref: string;
}

export interface O7RealtimeElevatorPreviewStateSample {
  state: string;
  status: string;
  timestamp_ms: number | null;
  evidence_ref: string;
}

// Realtime/Elevator preview 是 O7-KR1/KR2 的 PC-only 本地 fixture adapter。
// 它只把 map/pose/elevator 槽位压成安全摘要，不连接云端实时流、ROS2 /tf 或电梯设备。
export interface O7RealtimeElevatorPreviewResponse extends ProofFlags {
  schema: "trashbot.o7.realtime_elevator_preview.v1";
  schema_version: 1;
  preview_status: "fixture_preview_ready" | "blocked_not_proven";
  input_status: {
    fixture_json: string;
    status:
      | "loaded"
      | "not_provided"
      | "missing"
      | "read_error"
      | "bad_json"
      | "not_object"
      | "unsupported_schema"
      | "unsafe_copy"
      | "success_claim"
      | "control_claim"
      | "real_realtime_api_claim"
      | "ros2_tf_connected_claim"
      | "latency_lt_2s_claim"
      | "route_membership_true_claim"
      | "in_elevator_zone_true_claim"
      | "real_elevator_state_claim"
      | "elevator_arrival_claim"
      | "floor_recognition_proven_claim"
      | "human_takeover_proven_claim"
      | "robot_control_executed_claim";
    failure_reason: string;
  };
  source_fixture_schema: "trashbot.o7.realtime_elevator_fixture.v1" | "not_loaded";
  real_realtime_api_connected: false;
  real_ros2_tf_connected: false;
  real_elevator_state_chain_connected: false;
  latency_lt_2s_proven: false;
  robot_control_executed: false;
  session: {
    session_id: string;
    source: "local_json_fixture";
    evidence_ref: string;
    audit_refs: string[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  map_summary: {
    map_ref: string;
    map_frame: string;
    source: "local_json_fixture";
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  robot_pose_summary: {
    x_m: number | null;
    y_m: number | null;
    yaw_rad: number | null;
    pose_source: string;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  pose_freshness_summary: {
    timestamp_ms: number | null;
    age_ms: number | null;
    latency_lt_2s_proven: false;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  route_membership_summary: {
    route_id: string;
    requested_status: string;
    requested_on_route: string;
    requested_in_elevator_zone: string;
    on_route: false;
    in_elevator_zone: false;
    status: "blocked_not_proven";
  };
  elevator_state_chain_summary: {
    current_state: string;
    sample_limit: 5;
    count: number;
    sample: O7RealtimeElevatorPreviewStateSample[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  current_floor_evidence_summary: {
    floor_label: string;
    confidence: number | null;
    evidence_ref: string;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  target_floor_summary: {
    floor_label: string;
    confirmation_status: string;
    evidence_ref: string;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  human_takeover_summary: {
    required: true;
    reason: string;
    operator_action: string;
    evidence_ref: string;
    status: "blocked_not_proven";
  };
  evidence_refs: {
    fixture_ref: string;
    session_evidence_ref: string;
    audit_refs: string[];
    elevator_state_refs: string[];
    floor_evidence_ref: string;
    target_floor_evidence_ref: string;
    human_takeover_evidence_ref: string;
  };
  blocked_reasons: string[];
  not_proven: string[];
}

// Fixture preview 是 O7-KR3 的 PC-only 本地 JSON 预览，不是 O6 云归档或真实回放。
// 顶层开关额外固定 real_cloud_archive_connected=false 和 robot_control_executed=false。
export interface O7RouteReplayPreviewResponse extends ProofFlags {
  schema: "trashbot.o7.route_replay_preview.v1";
  schema_version: 1;
  preview_status: "fixture_preview_ready" | "blocked_not_proven";
  input_status: {
    fixture_json: string;
    status:
      | "loaded"
      | "not_provided"
      | "missing"
      | "read_error"
      | "bad_json"
      | "not_object"
      | "unsupported_schema"
      | "unsafe_copy"
      | "success_claim"
      | "control_claim";
    failure_reason: string;
  };
  source_fixture_schema: "trashbot.o7.route_replay_fixture.v1" | "not_loaded";
  real_cloud_archive_connected: false;
  robot_control_executed: false;
  task: {
    task_id: string;
    robot_id: string;
    route_id: string;
    evidence_ref: string;
  };
  route_metadata: {
    map_frame: string;
    frame_schema: "fixture_trajectory_frame_summary_v1";
    source: "local_json_fixture";
  };
  trajectory: {
    frame_count: number;
    sample_frames: O7RouteReplayPreviewFrame[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  playback_cursor_initial_state: {
    frame_index: 0 | null;
    timestamp_ms: number | null;
    playing: false;
    speed: 0;
    safe_to_play: false;
    status: "preview_cursor_only" | "blocked_not_proven";
  };
  keyframes: {
    count: number;
    sample_refs: string[];
    status: "fixture_refs_only" | "blocked_not_proven";
  };
  evidence_refs: {
    fixture_ref: string;
    task_evidence_ref: string;
    keyframe_refs: string[];
  };
  state_transitions: {
    count: number;
    sample: O7RouteReplayPreviewTransition[];
    gaps: string[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  blocked_reasons: string[];
  not_proven: string[];
}

export interface O7LabelingPreviewLabelSummary {
  label_type: string;
  value: string;
  status: string;
  evidence_ref: string;
}

export interface O7LabelingPreviewItemSample {
  item_id: string;
  task_id: string;
  frame_id: string;
  media_ref: string;
  evidence_ref: string;
  current_labels: {
    count: number;
    sample: O7LabelingPreviewLabelSummary[];
  };
}

export interface O7LabelingPreviewDraftSample extends O7LabelingPreviewLabelSummary {
  item_id: string;
}

// Labeling preview 是 O7-KR4 的 PC-only 本地 fixture adapter，不是标注 API。
// submit/rollback/export 和真实 annotation API 全部固定 false，避免 UI 误开动作。
export interface O7LabelingPreviewResponse extends ProofFlags {
  schema: "trashbot.o7.labeling_preview.v1";
  schema_version: 1;
  preview_status: "fixture_preview_ready" | "blocked_not_proven";
  input_status: {
    fixture_json: string;
    status:
      | "loaded"
      | "not_provided"
      | "missing"
      | "read_error"
      | "bad_json"
      | "not_object"
      | "unsupported_schema"
      | "unsafe_copy"
      | "success_claim"
      | "control_claim"
      | "submit_claim"
      | "rollback_claim"
      | "export_claim";
    failure_reason: string;
  };
  source_fixture_schema: "trashbot.o7.labeling_fixture.v1" | "not_loaded";
  real_annotation_api_connected: false;
  submit_enabled: false;
  rollback_enabled: false;
  dataset_export_available: false;
  robot_control_executed: false;
  queue: {
    queue_id: string;
    source: "local_json_fixture";
    review_item_count: number;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  review_items: {
    sample_limit: 3;
    sample: O7LabelingPreviewItemSample[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  label_schema: {
    schema_ref: string;
    version: string;
    required_fields: string[];
    allowed_fields: string[];
    status: "fixture_schema_summary_only" | "blocked_not_proven";
  };
  allowed_label_types: string[];
  draft_labels: {
    count: number;
    sample: O7LabelingPreviewDraftSample[];
    autosave_available: false;
    status: "fixture_draft_slots_only" | "blocked_not_proven";
  };
  dataset_export: {
    status: "blocked_not_available" | "fixture_gap_summary_only";
    export_ref: string;
    supported_formats: string[];
    gaps: string[];
  };
  evidence_refs: {
    fixture_ref: string;
    queue_evidence_ref: string;
    item_evidence_refs: string[];
  };
  blocked_reasons: string[];
  not_proven: string[];
}

export interface O7VoicePreviewAsrEventSample {
  event_type: "partial" | "final";
  timestamp_ms: number | null;
  transcript: string;
  confidence: number | null;
  evidence_ref: string;
}

export interface O7VoicePreviewTranscriptSlot {
  text: string;
  timestamp_ms: number | null;
  confidence: number | null;
  evidence_ref: string;
  status: "fixture_summary_only" | "empty_not_proven" | "blocked_not_proven";
}

// Voice fixture preview 是 O7-KR5 的 PC-only 本地 JSON 摘要，不连接语音 API、不发送 TTS。
// 这些额外 false 开关把“可读 fixture”和“真实 ASR/TTS runtime”强制分离。
export interface O7VoicePreviewResponse extends ProofFlags {
  schema: "trashbot.o7.voice_preview.v1";
  schema_version: 1;
  preview_status: "fixture_preview_ready" | "blocked_not_proven";
  input_status: {
    fixture_json: string;
    status:
      | "loaded"
      | "not_provided"
      | "missing"
      | "read_error"
      | "bad_json"
      | "not_object"
      | "unsupported_schema"
      | "unsafe_copy"
      | "success_claim"
      | "control_claim"
      | "asr_connected_claim"
      | "tts_send_claim"
      | "speaker_dispatch_claim"
      | "real_voice_claim"
      | "speaker_ack_success_claim";
    failure_reason: string;
  };
  source_fixture_schema: "trashbot.o7.voice_fixture.v1" | "not_loaded";
  real_voice_api_connected: false;
  real_asr_tts_runtime_connected: false;
  asr_stream_connected: false;
  tts_send_enabled: false;
  speaker_dispatch_enabled: false;
  robot_control_executed: false;
  voice_session: {
    session_id: string;
    source: "local_json_fixture";
    evidence_ref: string;
    audit_refs: string[];
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  asr_events: {
    event_count: number;
    sample_limit: 3;
    sample: O7VoicePreviewAsrEventSample[];
    latest_partial: O7VoicePreviewTranscriptSlot;
    latest_final: O7VoicePreviewTranscriptSlot;
    status: "fixture_summary_only" | "blocked_not_proven";
  };
  tts_draft_summary: {
    text: string;
    text_length: number;
    voice_profile: string;
    language: string;
    confirmation_required: true;
    status: "fixture_draft_only" | "blocked_not_proven";
  };
  speaker_dispatch_summary: {
    sends_to_robot: false;
    speaker_dispatch_enabled: false;
    ack_status: string;
    speaker_ack_ref: string;
    failure_event_ref: string;
    failure_refs: string[];
    status: "blocked_not_proven";
  };
  media_preflight_dependency: {
    required: true;
    source_schema: "trashbot.o7_board_media_preflight.v1";
    status: string;
    dependency_ref: "board_media_preflight_summary";
    gaps: string[];
  };
  evidence_refs: {
    fixture_ref: string;
    session_evidence_ref: string;
    asr_event_refs: string[];
    tts_evidence_ref: string;
    audit_refs: string[];
  };
  blocked_reasons: string[];
  not_proven: string[];
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

// Voice ASR/TTS snapshot 只给 O7-KR5 留出可审计字段，所有发送和真实运行态都保持关闭。
// draft/ack 字段分开，是为了后续接云端 voice API 时仍能 fail-closed 地展示确认链。
export interface O7VoiceAsrTtsSnapshot {
  schema: "trashbot.o7.voice_asr_tts_snapshot.v1";
  schema_version: 1;
  source: "software_proof";
  snapshot_status: "blocked_not_proven";
  safe_to_control: false;
  primary_actions_enabled: false;
  asr_stream_connected: false;
  tts_send_enabled: false;
  speaker_dispatch_enabled: false;
  real_voice_api_connected: false;
  real_asr_tts_runtime_connected: false;
  media_preflight_dependency: {
    required: true;
    source_schema: "trashbot.o7_board_media_preflight.v1";
    status: "blocked";
    dependency_ref: "board_media_preflight_summary";
  };
  asr_stream: {
    source_contract: "voice.asr_tts_operator.v1";
    status: "blocked_no_voice_api";
    connection_state: "not_connected";
    last_event_at_ms: null;
    partial_slot: {
      text: "";
      status: "empty_not_connected";
      evidence_ref: "missing_asr_partial_transcript_trace";
    };
    final_slot: {
      text: "";
      status: "empty_not_connected";
      evidence_ref: "missing_asr_final_transcript_trace";
    };
  };
  tts_draft: {
    text: "";
    status: "draft_disabled";
    max_chars: 0;
    language: "zh-CN";
    voice_profile: "not_connected";
    confirmation_required: true;
  };
  speaker_dispatch: {
    status: "blocked_not_available";
    endpoint: "POST /api/o7/operator/voice/tts (future, disabled)";
    sends_to_robot: false;
    idempotency_key_required: true;
    timeout_ms: null;
    recovery_path: string;
  };
  command_ack_audit: {
    ack_status: "blocked_no_ack_contract";
    last_command_id: "not_connected";
    audit_ref: "missing_voice_command_audit_log";
    speaker_ack_ref: "missing_speaker_dispatch_ack";
    failure_event_ref: "missing_speaker_failure_event";
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
  voice_asr_tts_snapshot: O7VoiceAsrTtsSnapshot;
  safe_command_snapshot: O7SafeCommandSnapshot;
  manual_control_policy: {
    pc_direct_robot_connection: false;
    cloud_mediated_only: true;
    command_dispatch_enabled: false;
    manual_control_enabled: false;
    navigate_goal_enabled: false;
    keyboard_control_enabled: false;
    real_command_api_connected: false;
    real_robot_ack_connected: false;
    confirmation_required_before_future_dispatch: true;
    success_claim_allowed: false;
  };
  kr_views: O7OperatorKrView[];
  command_previews: O7OperatorActionPreview[];
  blocked_reasons: string[];
  not_proven: string[];
  recovery_paths: string[];
}

export type O7OperatorConsoleSnapshotKey =
  | "board_media_preflight_summary"
  | "realtime_map_snapshot"
  | "elevator_state_snapshot"
  | "route_replay_snapshot"
  | "labeling_queue_snapshot"
  | "voice_asr_tts_snapshot"
  | "safe_command_snapshot";

export interface O7OperatorConsoleAcceptanceCheck {
  id: string;
  status: "blocked_not_proven";
  expected: false | string[];
  actual: false | string[];
}

// Acceptance guard 只从 O7 console 响应派生只读验收摘要，不连接云端、硬件或 ROS2。
// 它验证六个 KR 对应的快照和 fail-closed 开关仍在，而不是证明 O7 真实能力完成。
export interface O7OperatorConsoleAcceptanceResponse extends ProofFlags {
  schema: "trashbot.o7.operator_console_acceptance.v1";
  source_response_schema: "trashbot.o7.operator_console.v1";
  source_endpoint: "/api/o7/operator-console";
  guard_endpoint: "/api/o7/operator-console/acceptance";
  evidence_boundary: "software_proof_o7_operator_console_acceptance_guard";
  reads_hardware: false;
  sends_commands: false;
  connects_cloud_production: false;
  six_kr_snapshots_present: true;
  snapshot_schema_keys: O7OperatorConsoleSnapshotKey[];
  snapshot_schemas: Record<O7OperatorConsoleSnapshotKey, string>;
  fail_closed_checks: O7OperatorConsoleAcceptanceCheck[];
  disabled_entry_checks: O7OperatorConsoleAcceptanceCheck[];
  dangerous_marker_scan: {
    checked_marker_ids: string[];
    matched_marker_ids: [];
    markers_absent: true;
  };
  acceptance_verdict: "blocked_not_proven_guard_ok";
  not_real_capability_proof: true;
  remaining_gaps: string[];
}

export interface O7CloudOperatorConsoleProbeResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1";
  probe_status: "loaded_fail_closed_contract" | "fail_closed";
  source_base_url: string;
  remote_endpoint: "/api/o7/operator-console";
  remote_schema: string;
  cloud_api_status: string;
  operator_mode: string;
  kr_ids: string[];
  key_false_fields: string[];
  blocked_reasons: string[];
  not_proven: string[];
  fail_closed_reason: string;
  local_loopback_only: true;
  connects_cloud_production: false;
  sends_commands: false;
  reads_hardware: false;
}

export interface O7CloudArchiveTasksProbeResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.o7_cloud_archive_tasks_probe.v1";
  probe_status: "loaded_fail_closed_contract" | "fail_closed";
  source_base_url: string;
  remote_endpoint: "/api/o7/cloud-archive/tasks";
  remote_schema: string;
  archive_status: string;
  task_count: number;
  selected_task_id: string | null;
  latest_task_id: string | null;
  inspector_statuses: {
    route_replay: string;
    labeling_queue: string;
    voice_asr_tts: string;
    safe_command: string;
  };
  route_replay_summary: string;
  labeling_queue_summary: string;
  voice_asr_tts_summary: string;
  safe_command_summary: string;
  key_false_fields: string[];
  dangerous_true_fields: string[];
  blocked_reasons: string[];
  not_proven: string[];
  fail_closed_reason: string;
  local_loopback_only: true;
  connects_cloud_production: false;
  sends_commands: false;
  reads_hardware: false;
}

export interface O7RealtimeElevatorProbeResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1";
  probe_status: "loaded_fail_closed_contract" | "fail_closed";
  source_base_url: string;
  remote_endpoint: "/api/o7/realtime-elevator/snapshot";
  remote_schema: string;
  realtime_status: string;
  snapshot_status: string;
  map_ref_summary: string;
  map_frame_summary: string;
  robot_pose_summary: string;
  pose_freshness_summary: string;
  route_membership_false_fields: string[];
  elevator_status: string;
  elevator_state_samples_summary: string[];
  current_floor_evidence_summary: string;
  human_takeover_summary: string;
  key_false_fields: string[];
  dangerous_true_fields: string[];
  blocked_reasons: string[];
  not_proven: string[];
  fail_closed_reason: string;
  local_loopback_only: true;
  connects_cloud_production: false;
  sends_commands: false;
  reads_hardware: false;
}

export type O7PreviewsAcceptanceSurfaceId =
  | "cloud_operator_console_probe"
  | "cloud_archive_tasks_probe"
  | "realtime_elevator_probe"
  | "route_replay_player"
  | "realtime_map_pose_preview"
  | "elevator_state_timeline_preview"
  | "route_replay_trajectory_minimap"
  | "labeling_review_panel"
  | "local_draft_annotation_editor"
  | "voice_monitor_panel"
  | "local_tts_draft_editor"
  | "safe_command_review_panel"
  | "local_safe_command_draft_editor";

export interface O7PreviewsAcceptanceSurface {
  id: O7PreviewsAcceptanceSurfaceId;
  source_endpoint: string;
  ui_surface: string;
  evidence_boundary: "software_proof_only" | "local_http_contract_only" | "local_fixture_cursor_only";
  software_proof_available: true;
  acceptance_status: "blocked_not_proven";
  blocked_reasons: string[];
  not_proven: string[];
}

export interface O7PreviewsAcceptanceCheck {
  id: string;
  expected: false;
  actual: false;
  status: "blocked_not_proven";
}

// Previews acceptance guard 汇总 O7 Previews 已有的本地/HTTP 合同证据。
// 它只服务 CEO/operator 验收边界，不读取 fixture、硬件、ROS2 或生产云。
export interface O7PreviewsAcceptanceResponse extends ProofFlags {
  schema: "trashbot.o7.previews_acceptance.v1";
  guard_endpoint: "/api/o7/previews/acceptance";
  evidence_boundary: "software_proof_o7_previews_acceptance_guard";
  acceptance_verdict: "blocked_not_proven_guard_ok";
  not_real_capability_proof: true;
  reads_hardware: false;
  sends_commands: false;
  connects_cloud_production: false;
  safe_to_control: false;
  delivery_success: false;
  primary_actions_enabled: false;
  covered_surface_ids: O7PreviewsAcceptanceSurfaceId[];
  surfaces: O7PreviewsAcceptanceSurface[];
  fail_closed_checks: O7PreviewsAcceptanceCheck[];
  fixed_false_fields: {
    reads_hardware: false;
    sends_commands: false;
    connects_cloud_production: false;
    safe_to_control: false;
    delivery_success: false;
    primary_actions_enabled: false;
    playback_available: false;
    submit_enabled: false;
    tts_send_enabled: false;
    command_dispatch_enabled: false;
    manual_control_enabled: false;
    navigate_goal_enabled: false;
    keyboard_control_enabled: false;
    robot_control_executed: false;
    real_realtime_api_connected: false;
    real_ros2_tf_connected: false;
    real_cloud_archive_connected: false;
    real_annotation_api_connected: false;
    real_voice_api_connected: false;
    real_command_api_connected: false;
    real_robot_ack_connected: false;
    real_asr_tts_runtime_connected: false;
    real_cloud_operator_console_connected: false;
    manual_turn_sends_to_robot: false;
    navigate_goal_sends_to_robot: false;
  };
  blocked: string[];
  not_proven: string[];
  software_proof_only: string[];
  remaining_real_capability_gaps: string[];
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
  "/api/o7/operator-console/acceptance",
  "/api/o7/previews/acceptance",
  "/api/o7/cloud-operator-console-probe?baseUrl=<local-loopback-url>",
  "/api/o7/cloud-archive/tasks-probe?baseUrl=<local-loopback-url>",
  "/api/o7/realtime-elevator-preview?fixtureJson=<local-json>",
  "/api/o7/route-replay-preview?fixtureJson=<local-json>",
  "/api/o7/labeling-preview?fixtureJson=<local-json>",
  "/api/o7/voice-preview?fixtureJson=<local-json>",
  "/api/o7/safe-command-preview?fixtureJson=<local-json>",
  "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
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
  "real_o7_realtime_elevator_fixture_preview_runtime",
  "real_o7_ros2_tf_forwarding",
  "real_o7_elevator_state_chain",
  "real_o7_route_replay_archive",
  "real_o7_route_replay_fixture_preview_archive",
  "real_o7_cloud_archive_task_api",
  "real_o7_cloud_archive_tasks_http_probe_production_cloud",
  "real_o7_trajectory_playback",
  "real_o7_labeling_review_queue",
  "real_o7_labeling_fixture_preview_annotation_api",
  "real_o7_annotation_submit",
  "real_o7_dataset_export",
  "real_o7_voice_api",
  "real_o7_asr_tts_runtime",
  "real_o7_safe_command_fixture_preview_dispatch",
  "real_o7_operator_command_dispatch",
  "delivery_success",
] as const;
