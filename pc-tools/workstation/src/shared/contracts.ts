export type ProofStatus = "not_proven";
export type OperatorKrStatus = "draft" | "blocked" | "not_proven";
export type O7LiveEndpointStatus = "configured" | "not_configured" | "blocked";
export type O7LiveEndpointTokenStatus = "present" | "absent";

export interface O7LiveEndpointUrlSummary {
  configured: boolean;
  display_url: string;
  protocol: string;
  host: string;
  path: string;
  unsafe_reason: string;
}

export interface O7LiveEndpointCapability {
  id:
    | "rtc_realtime_pose_elevator"
    | "cloud_archive"
    | "route_replay_source"
    | "annotation_submit_api"
    | "voice_asr_tts_api"
    | "safe_command_api";
  kr_ids: Array<"O7-KR1" | "O7-KR2" | "O7-KR3" | "O7-KR4" | "O7-KR5" | "O7-KR6">;
  title: string;
  env: {
    url: string;
    token: string;
  };
  status: O7LiveEndpointStatus;
  proof_status: ProofStatus;
  url: O7LiveEndpointUrlSummary;
  token: {
    env: string;
    status: O7LiveEndpointTokenStatus;
  };
  missing: string[];
  blocked_reasons: string[];
  required_live_evidence: string[];
  remaining_real_capability_gaps: string[];
}

// O7 live endpoints manifest 只读取环境变量并做安全摘要，不探测网络、不连接云端、不暴露 token。
export interface O7LiveEndpointsManifestResponse extends ProofFlags {
  schema: "trashbot.o7.live_endpoints_manifest.v1";
  schema_version: 1;
  manifest_status: "readiness_manifest_ready";
  endpoint: "/api/o7/live-endpoints/manifest";
  env_only: true;
  network_probe_executed: false;
  sends_commands: false;
  safe_to_control: false;
  connects_cloud_production: false;
  robot_control_executed: false;
  reads_hardware: false;
  token_values_exposed: false;
  url_query_hash_credentials_exposed: false;
  capabilities: O7LiveEndpointCapability[];
  summary: {
    configured: number;
    not_configured: number;
    blocked: number;
    token_present: number;
    token_absent: number;
  };
  required_live_evidence: string[];
  remaining_real_capability_gaps: string[];
  blocked_reasons: string[];
  not_proven: string[];
}

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

export interface O7FieldEvidenceManifestArtifactSummary {
  required: boolean;
  present: boolean;
  path: string;
  size_bytes: number;
  mtime_utc: string | null;
  sha256: string | null;
  reason: string | null;
  file_count?: number;
  files?: Array<{
    path: string;
    size_bytes: number;
    sha256: string;
  }>;
}

export interface O7FieldEvidenceManifestSummary {
  schema: "trashbot.field_evidence_manifest.v1" | "not_loaded";
  run_id: string;
  source: "local_fixture" | "ssh_remote" | "not_loaded";
  mode: "local" | "ssh" | "not_loaded";
  status: string;
  gate_pass: boolean;
  artifact_status: "gated" | "missing" | "blocked";
  blocked_reason: string;
  not_proven: boolean;
  safe_to_control: false;
  delivery_success: false;
  primary_actions_enabled: false;
  artifact_root: string;
  preflight_status: string | null;
  manifest_gate: {
    schema: "trashbot.field_evidence_manifest.v1" | "not_loaded";
    status: "gated" | "blocked_not_proven";
    gate_pass: boolean;
    blocked_reason: string;
    source: "local_fixture" | "ssh_remote" | "not_loaded";
  };
  artifact_health: {
    status: "gated" | "missing" | "blocked";
    required_count: number;
    present_count: number;
    missing_count: number;
    blocked_count: number;
    empty_count: number;
    present_artifacts: string[];
    missing_artifacts: string[];
    blocked_artifacts: string[];
    summary: string;
  };
  artifacts: {
    map_yaml: O7FieldEvidenceManifestArtifactSummary;
    route_csv: O7FieldEvidenceManifestArtifactSummary;
    keyframes: O7FieldEvidenceManifestArtifactSummary;
    rosbag: O7FieldEvidenceManifestArtifactSummary;
    replay_jsonl: O7FieldEvidenceManifestArtifactSummary;
  };
}

// Field evidence consumer ingest 把 manifest 接到 route replay / labeling 两条只读消费链。
// 它只做本地或 SSH 产物的安全摘要，不把前端推成真正的回放、标注提交或现场成功。
export interface O7FieldEvidenceConsumerIngestResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1";
  ingest_status: "fixture_consumer_ready_not_proven" | "blocked_not_proven";
  manifest_input_status: {
    manifest_json: string;
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
  route_replay_input_status: {
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
  labeling_input_status: {
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
  source_manifest_schema: "trashbot.field_evidence_manifest.v1" | "not_loaded";
  manifest: O7FieldEvidenceManifestSummary;
  route_replay_preview: O7RouteReplayPreviewResponse;
  labeling_preview: O7LabelingPreviewResponse;
  consumer_entry: {
    primary_path: "/api/o7/field-evidence-consumer-ingest";
    route_replay_path: "/api/o7/route-replay-preview";
    labeling_path: "/api/o7/labeling-preview";
    fallback_mode: "local_mock" | "ssh_remote" | "blocked_not_proven";
    blocked_reason: string;
  };
  blocked_reasons: string[];
  not_proven: string[];
  next_required_evidence: string[];
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

export interface O7ConsumerTaskListItem {
  task_id: string;
  robot_id: string;
  started_at_ms: number | null;
  finished_at_ms: number | null;
  task_status_summary: string;
  latest_event_at_ms: number | null;
  trajectory_frame_count: number;
  event_count: number;
  evidence_count: number;
  labeling_status: string;
  inference_status: string;
  tunnel_status_summary: string;
  selected: boolean;
}

export interface O7ConsumerTaskListResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.o7_consumer_task_list.v1";
  list_status: "loaded_fail_closed_summary" | "fail_closed";
  source_base_url: string;
  remote_endpoint: string;
  remote_schema: string;
  query_strategy: {
    view: "summary";
    include: [];
    limit: number;
    primary_path: true;
    fail_closed_visible: true;
  };
  task_list: O7ConsumerTaskListItem[];
  blocked_reasons: string[];
  not_proven: string[];
  fail_closed_reason: string;
  local_loopback_only: true;
  safe_to_control: false;
  connects_cloud_production: false;
  robot_control_executed: false;
  delivery_success: false;
  primary_actions_enabled: false;
}

export interface O7ConsumerTaskDetailResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.o7_consumer_task_detail.v1";
  detail_status: "loaded_fail_closed_summary" | "fail_closed";
  source_base_url: string;
  remote_endpoint: string;
  remote_schema: string;
  requested_task_id: string;
  query_strategy: {
    view: "default";
    include: string[];
    primary_path: true;
    fail_closed_visible: true;
  };
  field_evidence: {
    source_contract:
      | "trashbot.field_evidence_manifest.v1"
      | "trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1"
      | "not_loaded";
    input_status:
      | "loaded"
      | "missing"
      | "schema_mismatch"
      | "invalid_shape"
      | "unsafe_claim"
      | "not_provided"
      | "bad_json"
      | "read_error";
    artifact_status: "gated" | "missing" | "blocked";
    manifest_gate: {
      schema: "trashbot.field_evidence_manifest.v1" | "not_loaded";
      status: "gated" | "blocked_not_proven";
      gate_pass: boolean;
      blocked_reason: string;
      source: "local_fixture" | "ssh_remote" | "not_loaded";
    };
    blocked_reason: string;
    not_proven: boolean;
    safe_to_control: false;
    delivery_success: false;
    primary_actions_enabled: false;
  };
  task_summary: {
    task_id: string;
    robot_id: string;
    task_status_summary: string;
    started_at_ms: number | null;
    finished_at_ms: number | null;
  } | null;
  trajectory: {
    status: string;
    frame_count: number;
    sample_frames: Record<string, unknown>[];
  };
  events: {
    status: string;
    count: number;
    sample_events: Record<string, unknown>[];
  };
  evidence: {
    status: string;
    count: number;
    sample_evidence: Record<string, unknown>[];
  };
  labeling: {
    status: string;
    label_count: number;
    sample_items: Record<string, unknown>[];
  };
  inference: {
    status: string;
    count: number;
    sample_results: Record<string, unknown>[];
  };
  tunnel_status: {
    status: string;
    latest_known_status: string;
    temporal_alignment: string;
  };
  blocked_reasons: string[];
  not_proven: string[];
  fail_closed_reason: string;
  local_loopback_only: true;
  safe_to_control: false;
  connects_cloud_production: false;
  robot_control_executed: false;
  delivery_success: false;
  primary_actions_enabled: false;
}

export type RobotApiReadEndpointId =
  | "health"
  | "status"
  | "map_preview"
  | "map_proof_latest"
  | "localize_proof_latest"
  | "nav2_status"
  | "nav2_proof_latest"
  | "nav2_goal_execution_latest"
  | "operator_report_latest"
  | "free_roam_autonomy_latest"
  | "camera_health"
  | "camera_devices"
  | "radar_status"
  | "radar_scan_proof_latest"
  | "radar_raw_packet_proof_latest"
  | "base_status"
  | "base_feedback_samples_latest";

export interface RobotApiEndpointReadback {
  id: RobotApiReadEndpointId;
  endpoint: string;
  http_status: number | null;
  request_status: "loaded" | "blocked" | "fetch_failed" | "bad_json" | "not_object";
  schema: string;
  status: string;
  evidence_ref: string;
  key_values: Record<string, string>;
  blocked_reasons: string[];
  dangerous_true_fields: string[];
}

export interface RobotApiPathPreviewPoint {
  x: number;
  y: number;
  frame_id: string;
  source_index: number | null;
}

export interface RobotApiScanPreviewPoint {
  x_m: number;
  y_m: number;
  range_m: number;
  angle_rad: number;
  frame_id: string;
  source_index: number | null;
}

export interface RobotApiMapPose {
  x: number;
  y: number;
  yaw: number | null;
  frame_id: string;
  source: string;
}

export interface RobotApiFrameTransform {
  parent_frame_id: string;
  child_frame_id: string;
  x: number;
  y: number;
  yaw: number;
  source: string;
}

export interface RobotControlMapPreviewRadarOverlay {
  overlay_status: "loaded" | "partial" | "blocked" | "not_current" | "not_loaded";
  status: "loaded" | "partial" | "blocked" | "not_current" | "not_loaded";
  plain_hint: string;
  wysiwyg_status_plain: string;
  wysiwyg_next_action_plain: string;
  next_action: string;
  next_action_plain: string;
  scan_preview_points: RobotApiScanPreviewPoint[];
  scan_preview_point_count: number;
  scan_preview_source_point_count: number | null;
  scan_preview_frame_id: string;
  points: RobotApiScanPreviewPoint[];
  count: number;
  source_count: number | null;
  frame_id: string;
  source_frame_id: string;
  robot_pose: RobotApiMapPose | null;
  source_endpoint_ids: RobotApiReadEndpointId[];
  blocked_reasons: string[];
  blocked_reason_labels: string[];
  refresh_required: boolean;
  stale_source_points_suppressed: boolean;
  primary_blocked_reason: string;
  current_vs_source_plain: string;
}

export interface RobotApiProofSummary {
  managed_runtime_started: boolean | null;
  scan_once_observed: boolean | null;
  map_once_observed: boolean | null;
  amcl_pose_observed: boolean | null;
  localization_tf_observed: boolean | null;
  planner_server_active: boolean | null;
  path_generation_requested: boolean | null;
  path_generation_succeeded: boolean | null;
  path_generated: boolean | null;
  path_point_count: number | null;
  path_preview_points: RobotApiPathPreviewPoint[];
  path_preview_point_count: number;
  path_preview_source_point_count: number | null;
  path_preview_frame_id: string;
  scan_preview_points: RobotApiScanPreviewPoint[];
  scan_preview_point_count: number;
  scan_preview_source_point_count: number | null;
  scan_preview_frame_id: string;
  robot_pose: RobotApiMapPose | null;
  frame_transforms: {
    base_link_to_laser_frame: RobotApiFrameTransform | null;
  };
  root_causes: string[];
  not_proven: string[];
}

export interface RobotControlOperatorHilMaterialSummary {
  status: "not_loaded" | "missing" | "loaded";
  source_endpoint_id: "operator_report_latest";
  source_path: "operator_report_latest.structured_hil_claims";
  report_status: string;
  evidence_ref: string;
  operator_present: string;
  physical_clearance: string;
  emergency_stop: string;
  external_video: string;
  camera_visible: string;
  wheel_feedback: string;
  lidar_delta: string;
  route_map: string;
  delivery_claim: string;
  site_state: string;
}

export type RobotControlOperatorReportPreflightStatus =
  | "not_required_for_stop"
  | "not_required_for_confirmed_manual"
  | "not_required_for_nav2_minimal_safety_precheck"
  | "passed"
  | "blocked";

export interface RobotControlOperatorReportPreflight {
  status: RobotControlOperatorReportPreflightStatus;
  source_endpoint: "/api/operator/report";
  request_status: "not_required" | "loaded" | "fetch_failed" | "bad_json" | "not_object" | "blocked";
  http_status: number | null;
  report_status: string;
  evidence_ref: string;
  required_fields: string[];
  missing_fields: string[];
  material_summary: RobotControlOperatorHilMaterialSummary;
  failure_reason: string;
  hard_dangerous_true_fields: string[];
}

export interface RobotControlOperatorReportStructuredHilClaims {
  external_video_recorded?: boolean;
  external_video_ref?: string;
  visible_content_proven?: boolean;
  camera_artifacts_ref?: string;
  wheel_feedback_lr_nonzero_proven?: boolean;
  wheel_feedback_ref?: string;
  physical_motion_lidar_delta_proven?: boolean;
  scan_delta_ref?: string;
  real_route_map_proven?: boolean;
  route_map_ref?: string;
  delivery_success?: boolean;
  site_state?: string;
}

// 现场 report 只是人工材料提交合同，不是运动控制或交付成功合同。
// 顶层只允许现场确认、引用和 notes；delivery_success 只能作为 nested claim 存在。
export interface RobotControlOperatorReportRequest {
  operator_present?: boolean;
  evidence_ref?: string;
  physical_clearance_confirmed?: boolean;
  emergency_stop_ready?: boolean;
  observed_motion?: boolean;
  observed_stop?: boolean;
  reported_at?: string;
  operator_notes?: string;
  structured_hil_claims?: RobotControlOperatorReportStructuredHilClaims;
}

export interface RobotControlOperatorReportProxyResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1";
  proxy_status: "report_forwarded" | "report_rejected" | "report_failed";
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: "/api/operator/report";
  remote_method: "POST";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  request_body: RobotControlOperatorReportRequest;
  structured_hil_claims: RobotControlOperatorReportStructuredHilClaims;
  rejected_fields: string[];
  ignored_fields: string[];
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export interface RobotControlNavGoalPreflightRequest {
  goal_frame_id?: "map";
  goal_x?: number;
  goal_y?: number;
  goal_yaw?: number;
  confirm_navigation_preflight?: boolean;
}

export type RobotControlNavGoalPreflightProxyStatus = "preflight_passed" | "preflight_rejected";
export type RobotControlNavGoalPreflightStatus =
  | "ready_for_navigation_goal_not_executed"
  | "preflight_rejected";

export interface RobotControlNavGoalPreflightResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_preflight.v1";
  proxy_status: RobotControlNavGoalPreflightProxyStatus;
  preflight_status: RobotControlNavGoalPreflightStatus;
  minimal_precheck_safety_only: true;
  minimal_precheck_plain: string;
  preflight_blocking_requirements: string[];
  operator_precheck_requirements: string[];
  proxy_guard_requirements: string[];
  camera_preflight_required: false;
  radar_preflight_required: false;
  operator_report_preflight_required: false;
  route_readback_preflight_required: false;
  localization_readback_preflight_required: false;
  nav2_status_readback_preflight_required: false;
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/nav2/goal/preflight";
  remote_methods_used: Array<"GET">;
  remote_read_endpoints: RobotApiEndpointReadback[];
  forbidden_remote_endpoints_not_called: Array<"/api/nav2/start" | "NavigateToPose" | "/cmd_vel" | "/api/base/manual">;
  goal_request: Required<Pick<RobotControlNavGoalPreflightRequest, "goal_frame_id" | "confirm_navigation_preflight">> & {
    goal_x: number;
    goal_y: number;
    goal_yaw: number;
  };
  goal_limits: {
    frame_id: "map";
    x_min_m: number;
    x_max_m: number;
    y_min_m: number;
    y_max_m: number;
    yaw_min_rad: number;
    yaw_max_rad: number;
  };
  operator_report_preflight: RobotControlOperatorReportPreflight;
  localization_summary: {
    request_status: RobotApiEndpointReadback["request_status"];
    status: string;
    localization_reset_observed: boolean;
    nav2_no_motion_localization_runtime_observed: boolean;
    map_to_base_link: boolean;
    source?: string;
  };
  nav2_path_summary: {
    request_status: RobotApiEndpointReadback["request_status"];
    status: string;
    path_generated: boolean;
    path_generation_succeeded: boolean;
    path_point_count: number;
  };
  nav2_status_summary: {
    request_status: RobotApiEndpointReadback["request_status"];
    status: string;
  };
  missing_requirements: string[];
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export interface RobotControlNavGoalExecutionRequest {
  goal_frame_id?: "map";
  goal_x?: number;
  goal_y?: number;
  goal_yaw?: number;
  route_preview_point_count?: number;
  route_preview_source_point_count?: number;
  route_preview_frame_id?: string;
  route_start_x?: number;
  route_start_y?: number;
  route_goal_x?: number;
  route_goal_y?: number;
  result_timeout_s?: number;
  server_timeout_s?: number;
  managed_runtime_opt_in?: boolean;
  managed_startup_s?: number;
  managed_ready_timeout_s?: number;
  base_command_mode?: "ros" | "speed" | "pwm";
  confirm_navigation_execution?: boolean;
}

export interface RobotControlNavGoalExecutionResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_proxy.v1";
  proxy_status: "execution_forwarded" | "execution_rejected" | "execution_failed";
  minimal_precheck_safety_only: true;
  minimal_precheck_plain: string;
  execution_blocking_requirements: string[];
  operator_precheck_requirements: string[];
  proxy_guard_requirements: string[];
  camera_preflight_required: false;
  radar_preflight_required: false;
  operator_report_preflight_required: false;
  route_readback_preflight_required: false;
  localization_readback_preflight_required: false;
  nav2_status_readback_preflight_required: false;
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/nav2/goal/execute";
  remote_endpoint: "/api/nav2/goal/execute";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  goal_request: Required<Pick<RobotControlNavGoalExecutionRequest, "goal_frame_id" | "confirm_navigation_execution">> & {
    goal_x: number;
    goal_y: number;
    goal_yaw: number;
    result_timeout_s: number;
    server_timeout_s: number;
    managed_runtime_opt_in: boolean;
    managed_startup_s: number;
    managed_ready_timeout_s: number;
    base_command_mode?: "ros" | "speed" | "pwm";
    route_preview_point_count: number;
    route_preview_source_point_count: number;
    route_preview_frame_id: string;
    route_start_x: number | null;
    route_start_y: number | null;
    route_goal_x: number | null;
    route_goal_y: number | null;
  };
  goal_execution_key_values: Record<string, string>;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: boolean;
}

export interface RobotControlNavGoalExecutionLatestResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_execution_latest_proxy.v1";
  proxy_status: "latest_loaded" | "latest_rejected" | "latest_failed";
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/nav2/goal/execution/latest";
  remote_endpoint: "/api/nav2/goal/execution/latest";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  goal_execution_key_values: Record<string, string>;
  latest_key_values: Record<string, string>;
  goal_execution_status: string;
  result_status: string;
  nav2_goal_execution_proven: string;
  execution_proof_gap: string;
  goal_execution_hil_pass: string;
  goal_execution_robot_control_executed: string;
  goal_execution_feedback_sample_count: string;
  goal_execution_base_feedback_sample_count: string;
  goal_execution_base_feedback_nonzero_sample_count: string;
  goal_execution_goal_succeeded: string;
  goal_execution_wheel_rerun_needed: string;
  goal_execution_minimal_precheck_safety_only: boolean;
  goal_execution_safety_confirm_required: boolean;
  goal_execution_camera_preflight_required: false;
  goal_execution_radar_preflight_required: false;
  goal_execution_operator_report_preflight_required: false;
  goal_execution_route_wysiwyg_preflight_required: false;
  fixed_goal_execution_endpoint: "/api/robot-control/nav2/goal/execute";
  fixed_goal_execution_latest_endpoint: "/api/robot-control/nav2/goal/execution/latest";
  plain_hint: string;
  execution_status_plain: string;
  next_action_plain: string;
  route_execution_readiness_plain: string;
  route_execution_precheck_plain: string;
  goal_execution_wheel_raw_lr_status_plain: string;
  goal_execution_wheel_raw_lr_next_action_plain: string;
  goal_execution_next_mode_plain: string;
  goal_execution_mode_rerun_plain: string;
  base_command_mode: string;
  goal_execution_base_command_mode: string;
  next_execution_base_command_mode: string;
  goal_execution_base_command_nonzero_observed: string;
  goal_execution_base_command_nonzero_count: string;
  goal_execution_base_command_mode_counts: string;
  goal_execution_base_feedback_lr_nonzero_proven: string;
  goal_execution_base_feedback_imu_attitude_delta_observed: string;
  goal_execution_readback_publishes_cmd_vel: string;
  goal_execution_managed_runtime_requested: string;
  goal_execution_managed_runtime_started: string;
  goal_execution_managed_runtime_lifecycle_ready_ok: string;
  goal_execution_managed_runtime_cleanup_ok: string;
  goal_execution_base_feedback_latest_raw_left: string;
  goal_execution_base_feedback_latest_raw_right: string;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: boolean;
}

export interface RobotControlDeliveryCompleteRequest {
  confirm_delivery_completion?: boolean;
  delivery_evidence_ref?: string;
  operator_notes?: string;
}

export interface RobotControlDeliveryCompleteResponse {
  schema: "trashbot.pc_tools_workstation.robot_control_delivery_complete_proxy.v1";
  proxy_status: "completion_forwarded" | "completion_rejected" | "completion_failed";
  source: "software_proof";
  proof_status: "not_proven" | "proven";
  safe_to_control: false;
  delivery_success: boolean;
  primary_actions_enabled: false;
  pc_only: true;
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/delivery/complete";
  remote_endpoint: "/api/delivery/complete";
  remote_http_status: number | null;
  status: "blocked" | "delivery_success_confirmed" | "loaded_fail_closed_summary";
  request_body: RobotControlDeliveryCompleteRequest;
  delivery_key_values: Record<string, string>;
  missing_required_material: string[];
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export interface RobotControlDeliveryMaterialRefs {
  operator_evidence_ref: string;
  external_video_ref: string;
  camera_artifacts_ref: string;
  route_map_ref: string;
  site_state: string;
}

export interface RobotControlDeliveryLatestResponse {
  schema: "trashbot.pc_tools_workstation.robot_control_delivery_latest_proxy.v1";
  proxy_status: "latest_loaded" | "latest_rejected" | "latest_failed";
  source: "software_proof";
  proof_status: "not_proven" | "proven";
  safe_to_control: false;
  delivery_success: boolean;
  primary_actions_enabled: false;
  pc_only: true;
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/delivery/latest";
  remote_endpoint: "/api/delivery/latest";
  remote_http_status: number | null;
  status: "blocked" | "delivery_success_confirmed" | "loaded_fail_closed_summary";
  delivery_claim_ready: boolean;
  delivery_material_ready: boolean;
  delivery_key_values: Record<string, string>;
  delivery_material_refs: RobotControlDeliveryMaterialRefs;
  missing_required_material: string[];
  delivery_missing_required_material: string[];
  delivery_missing_required_material_count: number;
  delivery_missing_required_material_plain: string;
  delivery_operator_evidence_ref: string;
  delivery_nav2_status: string;
  delivery_nav2_result_status: string;
  delivery_nav2_feedback_sample_count: string;
  delivery_latest_readback_only: true;
  delivery_complete_sends_motion: false;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export interface RobotControlDeliveryGapCheckResponse {
  schema: "trashbot.pc_tools_workstation.robot_control_delivery_gap_check_proxy.v1";
  proxy_status: "check_loaded" | "check_rejected" | "check_failed";
  source: "software_proof";
  proof_status: "not_proven";
  safe_to_control: false;
  delivery_success: false;
  primary_actions_enabled: false;
  pc_only: true;
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/delivery/check";
  remote_endpoint: "/api/delivery/complete";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  request_body: RobotControlDeliveryCompleteRequest;
  delivery_key_values: Record<string, string>;
  missing_required_material: string[];
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export type RobotControlPreviewStatus =
  | "idle_not_started"
  | "starting_local_peer"
  | "connecting_offer_posted"
  | "streaming"
  | "start_failed"
  | "stopped_by_user"
  | "peer_cleanup_failed";

export type RobotControlActionStatusCardId =
  | "camera_preview"
  | "map_preview"
  | "radar_map_points"
  | "nav2_route"
  | "keyboard_control"
  | "free_move"
  | "mapping_start";

export interface RobotControlActionStatusCard {
  id: RobotControlActionStatusCardId;
  title: string;
  status: string;
  status_label: string;
  summary_plain: string;
  next_action_plain: string;
  wysiwyg_status: string;
  requires_safety_confirmation: boolean;
  can_start_after_safety_confirm: boolean;
  sends_motion_when_clicked: boolean;
  blocks_free_motion: boolean;
  blocks_mapping_start: boolean;
  evidence?: {
    current_on_map?: boolean;
    current_point_count?: number;
    source_point_count?: number;
    frame_id?: string;
    source_frame_id?: string;
    blocked_reasons?: string[];
    radar_lifecycle_running?: boolean;
    radar_lifecycle_state?: string;
    map_radar_status?: string;
    map_radar_point_count?: number;
    map_radar_source_point_count?: number;
    map_radar_blocked_by_lifecycle_not_running?: boolean;
    runtime_scan_status?: string;
    runtime_scan_fresh?: boolean;
    runtime_scan_point_count?: number;
    runtime_scan_source_point_count?: number;
    runtime_scan_frame_id?: string;
    runtime_scan_age_s?: string;
    runtime_scan_source?: string;
    latest_scan_proof_fresh?: boolean;
    radar_scan_observation_status?: string;
    radar_scan_observation_missing_reasons?: string[];
    map_radar_readiness_status?: string;
    map_radar_next_action_plain?: string;
    map_radar_blocked_reason_labels?: string[];
    driver_diagnostics_status?: string;
    driver_diagnostics_next_action_plain?: string;
    driver_serial_bytes_read_total?: string;
    driver_serial_packet_count_total?: string;
    driver_serial_empty_read_count?: string;
    driver_published_scan_count?: string;
    radar_start_configured?: boolean;
    fixed_radar_start_endpoint?: string;
    fixed_radar_refresh_endpoint?: string;
    fixed_radar_map_preview_endpoint?: string;
    radar_refresh_after_start_required?: boolean;
    radar_map_points_loaded_required?: boolean;
    radar_map_point_count_gt_zero_required?: boolean;
    hold_to_move_required?: boolean;
    arm_sends_motion?: boolean;
    requires_keydown_for_motion?: boolean;
    pulse_interval_ms?: number;
    pulse_duration_ms?: number;
    manual_command_mode?: string;
    stop_triggers?: string[];
    wheel_feedback_required_in_same_hold_window?: boolean;
    fixed_keyboard_manual_endpoint?: string;
    fixed_keyboard_stop_endpoint?: string;
    keyboard_start_ready?: boolean;
    keyboard_enabled?: boolean;
    keyboard_armed?: boolean;
    keyboard_sends_motion_while_held?: boolean;
    keyboard_current_direction?: string;
    keyboard_current_hold_pulse_count?: number;
    keyboard_best_continuous_pulse_count?: number;
    keyboard_verified_min_forwarded_pulses?: number;
    keyboard_continuous_pulse_verified?: boolean;
    keyboard_stop_required_after_hold?: boolean;
    keyboard_stop_settled_after_pulse?: boolean;
    keyboard_motion_verified?: boolean;
    route_ready_on_map?: boolean;
    minimal_precheck_safety_only?: boolean;
    fixed_execute_proxy_endpoint?: string;
    execute_sends_motion_when_ready?: boolean;
    requires_same_window_wheel_lr_nonzero?: boolean;
    wheel_feedback_status?: string;
    goal_execution_proven?: boolean;
    goal_execution_hil_pass?: boolean;
    base_command_nonzero_observed?: boolean;
    base_command_nonzero_count?: number;
    base_feedback_sample_count?: number;
    base_feedback_nonzero_sample_count?: number;
    base_feedback_lr_nonzero_proven?: boolean;
    base_feedback_latest_raw_left?: string;
    base_feedback_latest_raw_right?: string;
    imu_attitude_delta_observed?: boolean;
    imu_roll_delta?: string;
    imu_pitch_delta?: string;
    last_base_command_mode?: string;
    next_base_command_mode?: string;
    nav2_stack_running?: boolean;
    nav2_stack_lifecycle_state?: string;
    planner_server_active?: boolean;
    controller_server_active?: boolean;
    controller_server_requested?: boolean;
    controller_idle_not_blocking?: boolean;
    controller_blocking_current_goal?: boolean;
    controller_idle_reason_plain?: string;
    path_generated?: boolean;
    nav2_path_point_count?: number;
    current_blocker_reasons?: string[];
    current_blocker_labels?: string[];
    managed_runtime_autostart?: boolean;
    managed_runtime_requested?: boolean;
    managed_runtime_started?: boolean;
    managed_runtime_lifecycle_ready_ok?: boolean;
    managed_runtime_cleanup_ok?: boolean;
    blockers?: string[];
    free_move_start_ready?: boolean;
    free_move_safety_only?: boolean;
    stop_fallback_required?: boolean;
    camera_blocks_free_motion?: boolean;
    radar_blocks_free_motion?: boolean;
    fixed_free_roam_start_endpoint?: string;
    fixed_free_roam_stop_endpoint?: string;
    free_roam_stop_request_pending?: boolean;
    start_will_clear_stop_request?: boolean;
    start_clears_stop_request_not_blocking?: boolean;
    motion_start_blocked_by_stop_request?: boolean;
    fixed_mapping_start_endpoint?: string;
    fixed_mapping_preview_endpoint?: string;
    mapping_start_ready?: boolean;
    mapping_start_requires_camera_first_frame?: boolean;
    mapping_start_requires_lidar_fresh?: boolean;
    mapping_start_missing_reasons?: string[];
    mapping_acceptance_missing_reasons?: string[];
    mapping_camera_first_frame_ready?: boolean;
    mapping_camera_source_readiness?: string;
    mapping_lidar_fresh_ready?: boolean;
    mapping_lidar_lifecycle_running?: boolean;
    mapping_lidar_lifecycle_state?: string;
    mapping_runtime_scan_fresh?: boolean;
    mapping_runtime_scan_diagnostic_only?: boolean;
    mapping_lidar_fresh_blocked_by_lifecycle?: boolean;
    mapping_lidar_next_action_plain?: string;
    camera_current_frame_visible?: boolean;
    camera_source_first_frame_ready?: boolean;
    camera_source_readiness?: string;
    camera_blocks_mapping_start?: boolean;
    shared_preview_multi_viewer?: boolean;
    shared_capture?: boolean;
    exclusive_camera_claim?: boolean;
    source_first_frame_failed?: boolean;
    source_diagnosis_status?: string;
    source_diagnosis_not_exclusive?: boolean;
    source_failure_reason?: string;
    shared_preview_upstream_active?: boolean;
    shared_preview_content_type_loaded?: boolean;
    shared_preview_last_failure_reason?: string;
    shared_preview_last_remote_http_status?: string;
    last_offer_failure_reason?: string;
    last_offer_format_attempts_summary?: string;
    first_frame_probe_read_ok?: boolean;
    visible_content_proven?: boolean;
    shared_preview_client_count?: number;
    shared_preview_cached_frame_loaded?: boolean;
    fixed_shared_preview_endpoint?: string;
    fixed_shared_preview_status_endpoint?: string;
    auto_joins_shared_preview?: boolean;
    shared_preview_single_upstream?: boolean;
    map_current_visible?: boolean;
    map_free_cell_count?: number;
    path_visible_on_map?: boolean;
    path_point_count?: number;
    path_frame_id?: string;
    robot_pose_visible?: boolean;
    radar_points_visible_on_map?: boolean;
    radar_point_count_on_map?: number;
  };
}

export type RobotControlGoalChecklistItemId =
  | "camera_wysiwyg"
  | "map_wysiwyg"
  | "radar_map_points_wysiwyg"
  | "nav2_route_execution"
  | "keyboard_continuous_control"
  | "free_move"
  | "mapping_start";

export interface RobotControlGoalChecklistItem {
  id: RobotControlGoalChecklistItemId;
  title: string;
  status: "done" | "ready" | "needs_safety_confirm" | "needs_action" | "not_ready";
  status_label: string;
  summary_plain: string;
  evidence_plain: string;
  next_action_plain: string;
  source_card_id: RobotControlActionStatusCardId;
  requires_safety_confirmation: boolean;
  requires_motion: boolean;
  blocks_goal_completion: boolean;
}

export interface RobotControlGoalChecklistSummaryActionItem {
  id: RobotControlGoalChecklistItemId;
  title: string;
  status_label: string;
  next_action_plain: string;
  source_card_id: RobotControlActionStatusCardId;
  requires_safety_confirmation: boolean;
  requires_motion: boolean;
  blocks_goal_completion: boolean;
}

export interface RobotControlGoalChecklistSummary {
  status: "complete" | "in_progress" | "not_started";
  status_label: string;
  total_count: number;
  done_count: number;
  remaining_count: number;
  safety_confirm_needed_count: number;
  motion_needed_count: number;
  ready_action_count: number;
  blocked_action_count: number;
  motion_ready_count: number;
  sensor_blocker_count: number;
  first_incomplete_item_id: RobotControlGoalChecklistItemId | "";
  first_incomplete_source_card_id: RobotControlActionStatusCardId | "";
  first_motion_item_id: RobotControlGoalChecklistItemId | "";
  first_motion_source_card_id: RobotControlActionStatusCardId | "";
  primary_ready_action_item_id: RobotControlGoalChecklistItemId | "";
  primary_ready_action_source_card_id: RobotControlActionStatusCardId | "";
  primary_ready_action_next_action_plain: string;
  primary_ready_action_summary_plain: string;
  safety_precheck_source_card_id: RobotControlActionStatusCardId | "";
  radar_item_id: RobotControlGoalChecklistItemId | "";
  radar_source_card_id: RobotControlActionStatusCardId | "";
  nav2_item_id: RobotControlGoalChecklistItemId | "";
  nav2_source_card_id: RobotControlActionStatusCardId | "";
  mapping_item_id: RobotControlGoalChecklistItemId | "";
  mapping_source_card_id: RobotControlActionStatusCardId | "";
  next_action_plain: string;
  summary_plain: string;
  motion_next_action_plain: string;
  motion_summary_plain: string;
  safety_precheck_next_action_plain: string;
  safety_precheck_summary_plain: string;
  radar_next_action_plain: string;
  radar_summary_plain: string;
  nav2_next_action_plain: string;
  nav2_summary_plain: string;
  mapping_next_action_plain: string;
  mapping_summary_plain: string;
  move_now_status_plain: string;
  mapping_blockers_plain: string;
  progress_plain: string;
  next_action_item_ids: RobotControlGoalChecklistItemId[];
  ready_action_ids: RobotControlGoalChecklistItemId[];
  blocked_action_ids: RobotControlGoalChecklistItemId[];
  next_action_items: RobotControlGoalChecklistSummaryActionItem[];
  ready_action_items: RobotControlGoalChecklistSummaryActionItem[];
  blocked_action_items: RobotControlGoalChecklistSummaryActionItem[];
}

export type RobotControlLiveWysiwygSurfaceId = "camera" | "map" | "radar_map_points";

export interface RobotControlLiveWysiwygSurfaceSummary {
  id: RobotControlLiveWysiwygSurfaceId;
  visible: boolean;
  readback_gap: boolean;
  completed: boolean;
  proof_status: "completed" | "ready_to_refresh" | "blocked";
  missing_evidence: string[];
  proof_plain: string;
  status_plain: string;
  next_action_plain: string;
  fixed_refresh_endpoint: string;
  sends_motion_when_clicked: false;
}

export type RobotControlLiveMotionRunbookActionId =
  | "run_nav2_route"
  | "hold_keyboard"
  | "start_free_move"
  | "start_mapping_when_sensors_ready";

export interface RobotControlLiveMotionRunbookItem {
  id: RobotControlLiveMotionRunbookActionId;
  label: string;
  display_label?: string;
  ready: boolean;
  completed: boolean;
  proof_status: "completed" | "ready_to_verify" | "blocked";
  missing_evidence: string[];
  proof_plain: string;
  minimal_precheck_safety_only: boolean;
  safety_confirm_required: boolean;
  sends_motion_when_executed: boolean;
  start_endpoint: string;
  stop_endpoint: string;
  acceptance_endpoints: string[];
  acceptance_plain: string;
  blocked_reasons: string[];
}

export interface RobotControlFieldAcceptanceStep {
  id: RobotControlLiveMotionRunbookActionId;
  label: string;
  display_label?: string;
  ready: boolean;
  completed: boolean;
  proof_status: RobotControlLiveMotionRunbookItem["proof_status"];
  sends_motion_when_executed: boolean;
  safety_confirm_required: boolean;
  start_endpoint: string;
  stop_endpoint: string;
  acceptance_endpoints: string[];
  missing_evidence: string[];
  proof_plain: string;
  blocked_reasons: string[];
}

export type RobotControlFieldAcceptanceNoMotionReadbackActionId =
  | "readback_all"
  | "refresh_current_wysiwyg"
  | "refresh_camera_first_frame"
  | "refresh_radar_map_overlay";

export interface RobotControlFieldAcceptanceNoMotionReadbackAction {
  id: RobotControlFieldAcceptanceNoMotionReadbackActionId;
  label: string;
  endpoint: string;
  method: "GET" | "POST";
  sequence_endpoints: string[];
  sequence_labels: string[];
  refreshes_summary: boolean;
  refreshes_radar_scan_proof: boolean;
  refreshes_camera_first_frame_probe: boolean;
  refreshes_map_preview: boolean;
  refreshes_radar_status: boolean;
  refreshes_camera_mjpeg_status: boolean;
  summary_plain: string;
  sends_motion_when_clicked: false;
  starts_nav2_when_clicked: false;
  starts_manual_when_clicked: false;
  starts_keyboard_when_clicked: false;
  starts_free_roam_when_clicked: false;
  starts_map_runtime_when_clicked: false;
  starts_radar_lifecycle_when_clicked: false;
  submits_delivery_when_clicked: false;
  stops_motion_when_clicked: false;
}

export interface RobotControlFieldAcceptanceSafetyConfirmReadyAction {
  id: RobotControlLiveMotionRunbookActionId;
  label: string;
  display_label?: string;
  start_endpoint: string;
  stop_endpoint: string;
  acceptance_endpoints: string[];
  requires_safety_confirm: true;
  minimal_precheck_safety_only: true;
  sends_motion_when_executed: true;
  camera_preflight_required: false;
  radar_preflight_required: false;
  operator_report_preflight_required: false;
  route_wysiwyg_preflight_required: false;
  starts_nav2_when_executed: boolean;
  starts_manual_when_executed: boolean;
  starts_keyboard_when_executed: boolean;
  starts_free_roam_when_executed: boolean;
  starts_map_runtime_when_executed: boolean;
  submits_delivery_when_executed: false;
}

export interface RobotControlFieldAcceptanceHardwareAction {
  id: string;
  label: string;
  summary_plain: string;
  blocks_camera_wysiwyg: boolean;
  blocks_mapping_start: boolean;
  blocks_free_move: boolean;
  after_action_readback_endpoint: string;
  after_action_readback_label: string;
  after_action_readback_method: "GET" | "POST";
  after_action_readback_sequence: string[];
  after_action_readback_sequence_labels: string[];
  sends_motion_when_clicked: false;
  starts_nav2_when_clicked: false;
  starts_manual_when_clicked: false;
  starts_keyboard_when_clicked: false;
  starts_free_roam_when_clicked: false;
  starts_map_runtime_when_clicked: false;
  starts_radar_lifecycle_when_clicked: false;
  submits_delivery_when_clicked: false;
  stops_motion_when_clicked: false;
}

export interface RobotControlFieldAcceptanceMissingEvidenceItem {
  id: string;
  label: string;
  action_id: RobotControlLiveMotionRunbookActionId;
  action_label: string;
  action_display_label?: string;
  readback_endpoint: string;
  readback_method: "GET" | "POST";
  requires_motion_before_readback: boolean;
  requires_safety_confirm_before_motion: boolean;
  blocks_field_acceptance: true;
}

export type RobotControlFieldAcceptanceWysiwygRefreshMode =
  | "camera_only"
  | "radar_map_only"
  | "map_only"
  | "all_wysiwyg"
  | "none";

export interface RobotControlFieldAcceptancePacket {
  status: RobotControlLiveClosureSummary["status"];
  summary_plain: string;
  objective_total_count: 4;
  objective_done_count: number;
  objective_remaining_count: number;
  objective_missing_ids: RobotControlLiveObjectiveAuditId[];
  objective_next_id: RobotControlLiveObjectiveAuditId | "none";
  next_step_id: RobotControlLiveMotionRunbookActionId | "none";
  next_step_label: string;
  next_step_display_label?: string;
  next_step_start_endpoint: string;
  next_step_sends_motion: boolean;
  next_step_requires_safety_confirm: boolean;
  ready_step_ids: RobotControlLiveMotionRunbookActionId[];
  blocked_step_ids: RobotControlLiveMotionRunbookActionId[];
  motion_step_ids: RobotControlLiveMotionRunbookActionId[];
  no_motion_step_ids: RobotControlLiveMotionRunbookActionId[];
  safety_confirm_ready_step_ids: RobotControlLiveMotionRunbookActionId[];
  safety_confirm_ready_action_labels: string[];
  safety_confirm_ready_action_display_labels?: string[];
  safety_confirm_ready_action_start_endpoints: string[];
  safety_confirm_ready_actions: RobotControlFieldAcceptanceSafetyConfirmReadyAction[];
  primary_safety_confirm_ready_action_id: RobotControlLiveMotionRunbookActionId | "none";
  primary_safety_confirm_ready_action_label: string;
  primary_safety_confirm_ready_action_display_label?: string;
  primary_safety_confirm_ready_action_start_endpoint: string;
  primary_safety_confirm_ready_action_requires_safety_confirm: boolean;
  primary_safety_confirm_ready_action_sends_motion: boolean;
  hardware_action_ids: string[];
  hardware_action_labels: string[];
  hardware_action_after_readback_endpoints: string[];
  hardware_action_after_readback_sequences: string[];
  hardware_action_after_readback_sequence_labels: string[];
  hardware_actions: RobotControlFieldAcceptanceHardwareAction[];
  primary_hardware_action_id: string;
  primary_hardware_action_label: string;
  primary_hardware_action_after_readback_endpoint: string;
  primary_hardware_action_after_readback_sequence: string[];
  primary_hardware_action_after_readback_sequence_labels: string[];
  primary_hardware_action_blocks_mapping_start: boolean;
  primary_hardware_action_blocks_free_move: boolean;
  missing_evidence_ids: string[];
  missing_evidence_labels: string[];
  missing_evidence_items: RobotControlFieldAcceptanceMissingEvidenceItem[];
  primary_missing_evidence_id: string;
  primary_missing_evidence_label: string;
  primary_missing_evidence_action_id: RobotControlLiveMotionRunbookActionId | "none";
  primary_missing_evidence_action_label: string;
  primary_missing_evidence_action_display_label?: string;
  primary_missing_evidence_readback_endpoint: string;
  primary_missing_evidence_readback_method: "GET" | "POST" | "none";
  primary_missing_evidence_requires_motion_before_readback: boolean;
  primary_missing_evidence_requires_safety_confirm_before_motion: boolean;
  primary_missing_evidence_blocks_field_acceptance: boolean;
  no_motion_readback_action_ids: string[];
  no_motion_readback_action_labels: string[];
  no_motion_readback_action_endpoints: string[];
  no_motion_readback_action_methods: Array<RobotControlFieldAcceptanceNoMotionReadbackAction["method"]>;
  no_motion_readback_action_sequences: string[];
  no_motion_readback_action_sequence_labels: string[];
  no_motion_readback_actions: RobotControlFieldAcceptanceNoMotionReadbackAction[];
  primary_no_motion_readback_action_id: RobotControlFieldAcceptanceNoMotionReadbackActionId | "none";
  primary_no_motion_readback_action_label: string;
  primary_no_motion_readback_action_endpoint: string;
  primary_no_motion_readback_action_method: RobotControlFieldAcceptanceNoMotionReadbackAction["method"] | "none";
  primary_no_motion_readback_action_sequence: string[];
  primary_no_motion_readback_action_sequence_labels: string[];
  primary_no_motion_readback_action_refreshes_summary: boolean;
  primary_no_motion_readback_action_refreshes_radar_scan_proof: boolean;
  primary_no_motion_readback_action_refreshes_camera_first_frame_probe: boolean;
  primary_no_motion_readback_action_refreshes_map_preview: boolean;
  primary_no_motion_readback_action_refreshes_radar_status: boolean;
  primary_no_motion_readback_action_refreshes_camera_mjpeg_status: boolean;
  primary_no_motion_readback_action_sends_motion: boolean;
  remaining_operator_action_summary_plain: string;
  remaining_hardware_action_summary_plain: string;
  remaining_no_motion_action_summary_plain: string;
  remaining_action_summary_plain: string;
  acceptance_endpoints: string[];
  safety_confirm_required: boolean;
  minimal_precheck_safety_only: boolean;
  wysiwyg_ready: boolean;
  wysiwyg_missing_surface_ids: string[];
  wysiwyg_primary_refresh_endpoint: string;
  wysiwyg_primary_refresh_label: string;
  wysiwyg_next_action_plain: string;
  wysiwyg_camera_next_action_plain: string;
  wysiwyg_radar_map_next_action_plain: string;
  wysiwyg_refresh_sequence: string[];
  wysiwyg_refresh_sequence_labels: string[];
  wysiwyg_refresh_mode?: RobotControlFieldAcceptanceWysiwygRefreshMode;
  fixed_wysiwyg_radar_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh";
  fixed_wysiwyg_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe";
  fixed_wysiwyg_map_preview_endpoint: "/api/robot-control/map/preview";
  fixed_wysiwyg_radar_status_endpoint: "/api/robot-control/radar/status";
  fixed_wysiwyg_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status";
  wysiwyg_refreshes_radar_scan_proof: boolean;
  wysiwyg_refreshes_camera_first_frame_probe: boolean;
  wysiwyg_refreshes_map_preview: boolean;
  wysiwyg_refreshes_radar_status: boolean;
  wysiwyg_refreshes_camera_mjpeg_status: boolean;
  wysiwyg_refresh_sends_motion: false;
  wysiwyg_refresh_starts_nav2: false;
  wysiwyg_refresh_starts_manual: false;
  wysiwyg_refresh_starts_keyboard: false;
  wysiwyg_refresh_starts_free_roam: false;
  wysiwyg_refresh_starts_radar_lifecycle: false;
  wysiwyg_refresh_starts_map_runtime: false;
  wysiwyg_refresh_submits_delivery: false;
  wysiwyg_refresh_stops_motion: false;
  mapping_start_ready: boolean;
  mapping_missing_evidence: string[];
  camera_blocks_mapping_start: boolean;
  camera_blocks_free_move: false;
  sends_motion_when_clicked: false;
  starts_nav2_when_clicked: false;
  starts_manual_when_clicked: false;
  starts_free_roam_when_clicked: false;
  starts_map_runtime_when_clicked: false;
  steps: RobotControlFieldAcceptanceStep[];
}

export interface RobotControlNav2RouteAcceptancePacket {
  action_id: "run_nav2_route";
  label: "完整行程执行";
  display_label?: string;
  status: RobotControlLiveClosureSummary["status"];
  proof_status: RobotControlLiveMotionRunbookItem["proof_status"];
  ready: boolean;
  completed: boolean;
  start_endpoint: "/api/robot-control/nav2/goal/execute";
  stop_endpoint: "/api/robot-control/base/stop";
  start_sends_motion: true;
  requires_safety_confirm: boolean;
  minimal_precheck_safety_only: boolean;
  camera_preflight_required: false;
  radar_preflight_required: false;
  route_wysiwyg_preflight_required: false;
  blocked_by_camera_wysiwyg: false;
  blocked_by_radar_wysiwyg: false;
  route_ready_on_map: boolean;
  nav2_goal_succeeded: boolean;
  same_window_wheel_lr_nonzero: boolean;
  delivery_success: boolean;
  needs_same_window_wheel_rerun: boolean;
  delivery_success_required: boolean;
  missing_evidence: string[];
  required_success_markers: string[];
  acceptance_endpoints: string[];
  readback_endpoints: string[];
  fixed_latest_endpoint: "/api/robot-control/nav2/goal/execution/latest";
  fixed_wheel_readback_endpoint: "/api/robot-control/base/feedback-samples";
  fixed_delivery_latest_endpoint: "/api/robot-control/delivery/latest";
  fixed_delivery_complete_endpoint: "/api/robot-control/delivery/complete";
  delivery_complete_sends_motion: false;
  readback_sends_motion: false;
  readback_starts_nav2: false;
  readback_starts_manual: false;
  readback_starts_keyboard: false;
  readback_starts_free_roam: false;
  readback_starts_map_runtime: false;
  readback_submits_delivery: false;
  readback_stops_motion: false;
  command_mode: string;
  next_base_command_mode: string;
  latest_raw_left: string;
  latest_raw_right: string;
  feedback_sample_count: string;
  feedback_nonzero_sample_count: string;
  current_gap_plain: string;
  checklist_plain: string;
  acceptance_plain: string;
  no_extra_precheck_plain: string;
  delivery_next_action_plain: string;
  sends_motion_when_clicked: false;
}

export type RobotControlLiveObjectiveAuditId = "motion" | "wysiwyg" | "precheck" | "mapping";

export interface RobotControlLiveObjectiveAuditItem {
  id: RobotControlLiveObjectiveAuditId;
  title: string;
  state: string;
  summary_plain: string;
  next_action_plain: string;
  item_ids: string[];
  completed: boolean;
  actionable: boolean;
  missing_count: number;
  source_card_id: RobotControlActionStatusCardId;
  sends_motion_when_clicked: false;
}

export interface RobotControlLiveClosureSummary {
  status: "complete" | "ready_for_motion" | "needs_safety_confirm" | "needs_wheel_rerun" | "needs_delivery" | "needs_wysiwyg" | "needs_sensor" | "not_ready";
  status_label: string;
  summary_plain: string;
  next_action_plain: string;
  robot_api_connection_status: "not_configured" | "blocked" | "degraded" | "readable";
  robot_api_connection_plain: string;
  robot_api_connection_next_action_plain: string;
  robot_api_connection_loaded_count: number;
  robot_api_connection_failed_count: number;
  robot_api_connection_blocked_count: number;
  robot_api_connection_failed_endpoint_ids: string[];
  robot_api_connection_blocked_reasons: string[];
  robot_api_connection_recovery_endpoints: string[];
  robot_api_connection_sends_motion_when_clicked: false;
  route_ready_on_map: boolean;
  nav2_route_ready: boolean;
  nav2_goal_succeeded: boolean;
  nav2_goal_execution_proven: boolean;
  wheel_lr_nonzero_proven: boolean;
  needs_same_window_wheel_rerun: boolean;
  delivery_success: boolean;
  delivery_claim_ready: boolean;
  delivery_success_required: boolean;
  delivery_next_action_plain: string;
  fixed_delivery_latest_endpoint: "/api/robot-control/delivery/latest";
  fixed_delivery_complete_endpoint: "/api/robot-control/delivery/complete";
  delivery_latest_readback_only: true;
  delivery_complete_sends_motion: false;
  camera_current_visible: boolean;
  live_wysiwyg_camera_visible: boolean;
  map_current_visible: boolean;
  path_current_visible: boolean;
  live_wysiwyg_map_visible: boolean;
  radar_map_points_visible: boolean;
  primary_action_id: RobotControlLiveMotionRunbookActionId | "none";
  keyboard_continuous_ready: boolean;
  keyboard_continuous_motion_verified: boolean;
  keyboard_continuous_forwarded_pulses: number;
  keyboard_ready: boolean;
  keyboard_safety_confirm_required: boolean;
  keyboard_enable_sends_motion: false;
  keyboard_pulse_interval_ms: number;
  keyboard_pulse_duration_ms: number;
  keyboard_stop_triggers: string[];
  keyboard_acceptance_plain: string;
  keyboard_manual_endpoint: "/api/robot-control/base/manual";
  keyboard_stop_endpoint: "/api/robot-control/base/stop";
  keyboard_feedback_readback_endpoint: "/api/robot-control/base/feedback-samples";
  keyboard_summary_endpoint: "/api/robot-control/summary";
  objective_audit_status: "complete" | "in_progress";
  objective_audit_total_count: 4;
  objective_audit_done_count: number;
  objective_audit_remaining_count: number;
  objective_audit_next_objective_id: RobotControlLiveObjectiveAuditId | "none";
  objective_audit_missing_objective_ids: RobotControlLiveObjectiveAuditId[];
  objective_audit_summary_plain: string;
  objective_audit_items: RobotControlLiveObjectiveAuditItem[];
  fixed_objective_audit_summary_endpoint: "/api/robot-control/summary";
  objective_audit_sends_motion_when_clicked: false;
  map_display_primary_tool: "pc_big_map";
  map_display_primary_url: "/map";
  map_display_legacy_url: "?view=map";
  map_display_primary_action_label: "进入地图大屏";
  map_display_primary_action_opens_new_window: false;
  map_display_primary_action_opens_current_page: true;
  map_display_direct_map_default_observer: true;
  map_display_direct_map_only: true;
  map_display_direct_map_viewport_priority: "fullscreen_map_canvas";
  map_display_direct_map_canvas_height_mode: "viewport_dominant_full_height";
  map_display_direct_map_keeps_page_fullscreen_without_browser_api: true;
  map_display_direct_map_browser_fullscreen_required: false;
  map_display_direct_map_refreshes_radar_scan_proof_on_enter: true;
  map_display_direct_map_refreshes_map_preview_on_enter: true;
  map_display_direct_map_refreshes_radar_status_on_enter: true;
  map_display_direct_map_starts_radar_lifecycle_on_enter: false;
  map_display_default_zoom_percent: "3200%";
  map_display_max_zoom_percent: "6400%";
  map_display_too_small_next_action_plain: string;
  map_display_ros2_companion_answer_plain: string;
  map_display_ros2_companion_plain: string;
  map_display_operator_default_surface: "pc_big_map_direct_view";
  map_display_companion_replaces_pc_ui: false;
  map_display_wysiwyg_overlays: string[];
  map_display_ros2_companion_required: false;
  map_display_ros2_companion_tools: string[];
  map_display_engineering_tools_visible_by_default: false;
  map_display_engineering_tools_action_label: "工程观察：RViz2 / Foxglove";
  map_display_ordinary_user_tool: "pc_big_map";
  map_display_rviz_role_plain: string;
  map_display_rviz_launch_command: "ros2 launch ros2_trashbot_bringup rviz.launch.py";
  map_display_foxglove_role_plain: string;
  map_display_foxglove_bridge_package: "foxglove_bridge";
  map_display_foxglove_bridge_install_command: "sudo apt install ros-humble-foxglove-bridge";
  map_display_foxglove_bridge_launch_command: "ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py";
  map_display_foxglove_websocket_url: "ws://192.168.1.11:8765";
  map_display_foxglove_web_app_url: "https://studio.foxglove.dev";
  map_display_ros2_observe_topics: string[];
  map_display_ros2_observe_motion_topics: false;
  map_display_ros2_observe_control_tools: false;
  map_display_engineering_tools_sends_motion: false;
  map_display_companion_plain: string;
  map_display_sends_motion_when_clicked: false;
  map_display_starts_ros2: false;
  map_display_starts_rviz2: false;
  map_display_starts_foxglove: false;
  map_display_starts_nav2: false;
  map_display_starts_map_runtime: false;
  live_wysiwyg_ready: boolean;
  live_wysiwyg_missing_surface_ids: string[];
  live_wysiwyg_needs_refresh: boolean;
  live_wysiwyg_readback_gap_surface_ids: string[];
  live_wysiwyg_primary_readback_gap_surface_id: string;
  live_wysiwyg_missing_surface_refresh_endpoints: string[];
  live_wysiwyg_missing_surface_refresh_labels: string[];
  live_wysiwyg_primary_refresh_endpoint: string;
  live_wysiwyg_primary_refresh_label: string;
  live_wysiwyg_diagnostic_plain: string;
  live_wysiwyg_camera_diagnostic_plain: string;
  live_wysiwyg_radar_diagnostic_plain: string;
  live_wysiwyg_map_radar_diagnostic_plain: string;
  live_wysiwyg_camera_probe_failure_reason: string;
  live_wysiwyg_camera_source_diagnosis_status: string;
  live_wysiwyg_camera_source_diagnosis_plain_hint: string;
  live_wysiwyg_camera_source_diagnosis_next_action_plain: string;
  live_wysiwyg_camera_source_diagnosis_not_exclusive: string;
  live_wysiwyg_camera_shared_preview_client_count: string;
  live_wysiwyg_camera_shared_preview_upstream_active: string;
  live_wysiwyg_camera_shared_preview_exclusive_camera_claim: string;
  live_wysiwyg_camera_shared_preview_everyone_can_join: true;
  live_wysiwyg_camera_shared_preview_current_frame_visible: boolean;
  live_wysiwyg_camera_shared_preview_gap_plain: string;
  live_wysiwyg_camera_recovery_status: string;
  live_wysiwyg_camera_recovery_next_action_plain: string;
  live_wysiwyg_camera_recovery_sequence: string[];
  live_wysiwyg_camera_recovery_sequence_labels: string[];
  live_wysiwyg_camera_recovery_sends_motion: false;
  camera_first_frame_probe_status: string;
  camera_first_frame_failure_reason: string;
  camera_source_diagnosis_status: string;
  camera_source_diagnosis_not_exclusive: string;
  camera_shared_preview_exclusive_camera_claim: string;
  camera_shared_preview_everyone_can_join: true;
  camera_shared_preview_current_frame_visible: boolean;
  camera_shared_preview_gap_plain: string;
  camera_usb_speed: string;
  camera_recovery_next_action_plain: string;
  camera_hardware_action_required: boolean;
  camera_hardware_action_label: string;
  camera_usb_full_speed_detected: boolean;
  camera_blocks_mapping_start: boolean;
  camera_blocks_free_move: false;
  camera_reprobe_after_hardware_action_required: boolean;
  camera_reprobe_sequence: string[];
  fixed_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe";
  fixed_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status";
  camera_recovery_sends_motion: false;
  camera_recovery_starts_map_runtime: false;
  live_wysiwyg_radar_scan_missing_observations: string[];
  live_wysiwyg_map_radar_blocked_reasons: string[];
  live_wysiwyg_radar_map_overlay_status: string;
  live_wysiwyg_radar_map_current_point_count: string;
  live_wysiwyg_radar_map_source_point_count: string;
  live_wysiwyg_radar_map_stale_source_points_suppressed: boolean;
  live_wysiwyg_radar_map_primary_blocked_reason: string;
  live_wysiwyg_radar_map_current_vs_source_plain: string;
  live_wysiwyg_radar_map_refresh_next_action_plain: string;
  live_wysiwyg_radar_map_refresh_sequence: [
    "/api/robot-control/radar/scan-proof/refresh",
    "/api/robot-control/radar/status",
    "/api/robot-control/map/preview",
    "/api/robot-control/summary",
  ];
  live_wysiwyg_radar_map_refresh_sequence_labels: ["刷新雷达扫描读数", "读取雷达状态", "刷新地图画面", "刷新总览"];
  radar_overlay_status: string;
  radar_overlay_current_point_count: string;
  radar_overlay_source_point_count: string;
  radar_overlay_primary_blocked_reason: string;
  radar_overlay_current_vs_source_plain: string;
  radar_overlay_refresh_next_action_plain: string;
  radar_overlay_needs_refresh: boolean;
  radar_overlay_blocks_wysiwyg: boolean;
  radar_overlay_blocks_free_move: false;
  radar_overlay_recovery_sequence: string[];
  fixed_radar_overlay_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh";
  fixed_radar_overlay_map_preview_endpoint: "/api/robot-control/map/preview";
  radar_overlay_refresh_sends_motion: false;
  radar_overlay_refresh_starts_radar_lifecycle: false;
  radar_overlay_refresh_starts_nav2: false;
  radar_overlay_refresh_starts_manual: false;
  radar_overlay_refresh_starts_keyboard: false;
  radar_overlay_refresh_starts_free_roam: false;
  radar_overlay_refresh_starts_map_runtime: false;
  radar_overlay_refresh_submits_delivery: false;
  radar_overlay_refresh_stops_motion: false;
  fixed_radar_start_endpoint: "/api/robot-control/radar/start";
  fixed_radar_stop_endpoint: "/api/robot-control/radar/stop";
  radar_start_map_wysiwyg_required: true;
  radar_start_map_wysiwyg_sequence: string[];
  radar_start_map_wysiwyg_sequence_labels: string[];
  radar_start_refreshes_scan_proof: true;
  radar_start_refreshes_radar_status: true;
  radar_start_refreshes_map_preview: true;
  radar_start_refreshes_summary: true;
  radar_start_sends_motion: false;
  radar_start_starts_nav2: false;
  radar_start_starts_manual: false;
  radar_start_starts_keyboard: false;
  radar_start_starts_free_roam: false;
  radar_start_starts_map_runtime: false;
  radar_start_submits_delivery: false;
  radar_start_stops_motion: false;
  fixed_live_wysiwyg_radar_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh";
  fixed_live_wysiwyg_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe";
  fixed_live_wysiwyg_map_preview_endpoint: "/api/robot-control/map/preview";
  fixed_live_wysiwyg_radar_status_endpoint: "/api/robot-control/radar/status";
  fixed_live_wysiwyg_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status";
  live_wysiwyg_refresh_plan_available: boolean;
  live_wysiwyg_refresh_sequence: string[];
  live_wysiwyg_refresh_sequence_labels: string[];
  live_wysiwyg_refreshes_radar_scan_proof: true;
  live_wysiwyg_refreshes_camera_first_frame_probe: true;
  live_wysiwyg_refreshes_map_preview: true;
  live_wysiwyg_refreshes_radar_status: true;
  live_wysiwyg_refreshes_camera_mjpeg_status: true;
  live_wysiwyg_refresh_sends_motion: false;
  live_wysiwyg_refresh_starts_nav2: false;
  live_wysiwyg_refresh_starts_manual: false;
  live_wysiwyg_refresh_starts_keyboard: false;
  live_wysiwyg_refresh_starts_free_roam: false;
  live_wysiwyg_refresh_starts_radar_lifecycle: false;
  live_wysiwyg_refresh_starts_map_runtime: false;
  live_wysiwyg_surface_summaries: RobotControlLiveWysiwygSurfaceSummary[];
  free_move_start_ready: boolean;
  free_roam_ready: boolean;
  free_roam_start_ready: boolean;
  free_roam_motion_start_ready: boolean;
  free_roam_motion_ready: boolean;
  free_move_minimal_precheck_safety_only: boolean;
  free_move_safety_confirm_required: boolean;
  free_move_camera_preflight_required: false;
  free_move_radar_preflight_required: false;
  free_move_without_camera_allowed: true;
  free_roam_motion_without_radar_allowed: true;
  free_move_blocked_by_camera_wysiwyg: false;
  free_move_blocked_by_radar_wysiwyg: false;
  fixed_free_roam_start_endpoint: "/api/robot-control/free-roam/autonomy/start";
  fixed_free_roam_stop_endpoint: "/api/robot-control/free-roam/autonomy/stop";
  fixed_free_roam_latest_endpoint: "/api/robot-control/free-roam/autonomy/latest";
  mapping_start_ready: boolean;
  free_roam_mapping_start_ready: boolean;
  free_roam_mapping_ready: boolean;
  free_roam_mapping_start_missing_reasons: string[];
  free_roam_mapping_missing_reasons: string[];
  mapping_start_requires_camera_first_frame: true;
  mapping_start_requires_lidar_fresh: true;
  mapping_start_missing_reasons: string[];
  mapping_acceptance_missing_reasons: string[];
  mapping_start_unblock_plain: string;
  mapping_camera_blocks_start: boolean;
  mapping_lidar_blocks_start: boolean;
  mapping_lidar_fresh_readback_ready: boolean;
  mapping_lidar_fresh_gate_conflict: boolean;
  mapping_lidar_fresh_gate_status: string;
  mapping_lidar_fresh_next_action_plain: string;
  mapping_lidar_fresh_refresh_sequence: string[];
  mapping_lidar_fresh_refresh_sequence_labels: string[];
  mapping_lidar_fresh_refresh_sends_motion: false;
  mapping_lidar_fresh_refresh_starts_radar_lifecycle: false;
  mapping_lidar_fresh_blocks_free_move: false;
  mapping_unblock_allows_free_move: true;
  mapping_unblock_camera_diagnosis_status: string;
  mapping_unblock_camera_not_exclusive: string;
  mapping_unblock_camera_next_action_plain: string;
  mapping_unblock_camera_recovery_next_action_plain: string;
  mapping_unblock_camera_recovery_sequence: string[];
  mapping_unblock_camera_recovery_sequence_labels: string[];
  fixed_mapping_start_endpoint: "/api/robot-control/map/start";
  fixed_mapping_preview_endpoint: "/api/robot-control/map/preview";
  fixed_mapping_unblock_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe";
  fixed_mapping_unblock_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status";
  fixed_mapping_unblock_summary_endpoint: "/api/robot-control/summary";
  mapping_unblock_camera_recovery_sends_motion: false;
  mapping_unblock_sends_motion_when_clicked: false;
  keyboard_control_start_ready: boolean;
  keyboard_continuous_control_ready: boolean;
  keyboard_hold_to_move_required: boolean;
  keyboard_enabled: boolean;
  keyboard_motion_verified: boolean;
  keyboard_stop_settled_after_pulse: boolean;
  keyboard_best_continuous_pulse_count: number;
  keyboard_verified_min_forwarded_pulses: number;
  keyboard_manual_command_mode: string;
  keyboard_continuous_minimal_precheck_safety_only: boolean;
  keyboard_continuous_safety_confirm_required: boolean;
  keyboard_continuous_enable_sends_motion: false;
  keyboard_continuous_hold_to_move_required: true;
  keyboard_continuous_pulse_interval_ms: number;
  keyboard_continuous_pulse_duration_ms: number;
  keyboard_continuous_stop_triggers: string[];
  keyboard_continuous_wheel_feedback_acceptance: "same_hold_window_wheel_lr_nonzero";
  fixed_keyboard_manual_endpoint: "/api/robot-control/base/manual";
  fixed_keyboard_stop_endpoint: "/api/robot-control/base/stop";
  fixed_keyboard_feedback_readback_endpoint: "/api/robot-control/base/feedback-samples";
  fixed_keyboard_summary_endpoint: "/api/robot-control/summary";
  keyboard_continuous_post_hold_feedback_readback_required: true;
  keyboard_continuous_post_hold_summary_refresh_required: true;
  live_motion_runbook_items: RobotControlLiveMotionRunbookItem[];
  live_motion_runbook_action_ids: RobotControlLiveMotionRunbookActionId[];
  live_motion_runbook_ready_action_ids: RobotControlLiveMotionRunbookActionId[];
  live_motion_runbook_blocked_action_ids: RobotControlLiveMotionRunbookActionId[];
  live_motion_runbook_primary_action_id: RobotControlLiveMotionRunbookActionId | "none";
  live_motion_runbook_start_endpoints: string[];
  live_motion_runbook_acceptance_endpoints: string[];
  live_motion_runbook_minimal_precheck_safety_only: boolean;
  live_motion_runbook_safety_confirm_required: boolean;
  live_motion_runbook_summary_plain: string;
  live_motion_runbook_ready_plain: string;
  live_motion_runbook_blocked_plain: string;
  live_motion_runbook_primary_action_plain: string;
  live_motion_runbook_minimal_precheck_plain: string;
  minimal_precheck_safety_only: boolean;
  safety_confirm_required_for_motion: boolean;
  wheel_rerun_minimal_precheck_safety_only: boolean;
  wheel_rerun_safety_confirm_required: boolean;
  wheel_rerun_camera_preflight_required: false;
  wheel_rerun_radar_preflight_required: false;
  wheel_rerun_route_wysiwyg_preflight_required: false;
  wheel_rerun_blocked_by_camera_wysiwyg: false;
  wheel_rerun_blocked_by_radar_wysiwyg: false;
  wheel_rerun_command_mode: string;
  wheel_rerun_last_base_command_mode: string;
  wheel_rerun_next_base_command_mode: string;
  wheel_rerun_feedback_sample_count: string;
  wheel_rerun_feedback_nonzero_sample_count: string;
  wheel_rerun_latest_raw_left: string;
  wheel_rerun_latest_raw_right: string;
  wheel_rerun_imu_attitude_delta_observed: string;
  wheel_rerun_imu_roll_delta: string;
  wheel_rerun_imu_pitch_delta: string;
  wheel_rerun_mode_rerun_status: string;
  wheel_rerun_mode_rerun_plain: string;
  wheel_rerun_next_mode_plain: string;
  wheel_rerun_base_command_nonzero_observed: string;
  wheel_rerun_base_command_nonzero_count: string;
  wheel_rerun_base_command_latest_nonzero_mode: string;
  wheel_rerun_base_command_mode_counts: string;
  wheel_rerun_control_diagnosis_plain: string;
  wheel_rerun_readback_plain: string;
  wheel_rerun_checklist_plain: string;
  wheel_rerun_acceptance_plain: string;
  wheel_rerun_acceptance_endpoints: string[];
  wheel_rerun_ready_for_safety_confirm: boolean;
  wheel_rerun_start_endpoint: "/api/robot-control/nav2/goal/execute";
  wheel_rerun_start_sends_motion: true;
  wheel_rerun_requires_safety_confirm: boolean;
  wheel_rerun_readback_endpoints: string[];
  wheel_rerun_required_success_markers: string[];
  wheel_rerun_current_gap_plain: string;
  wheel_rerun_no_extra_precheck_plain: string;
  wheel_rerun_delivery_success_required: boolean;
  wheel_rerun_delivery_next_action_plain: string;
  fixed_wheel_rerun_endpoint: "/api/robot-control/nav2/goal/execute";
  fixed_wheel_rerun_latest_endpoint: "/api/robot-control/nav2/goal/execution/latest";
  fixed_wheel_rerun_delivery_latest_endpoint: "/api/robot-control/delivery/latest";
  fixed_wheel_rerun_delivery_complete_endpoint: "/api/robot-control/delivery/complete";
  wheel_rerun_delivery_complete_sends_motion: false;
  fixed_wheel_readback_endpoint: "/api/robot-control/base/feedback-samples";
  sends_motion_when_clicked: false;
  blocker_ids: RobotControlGoalChecklistItemId[];
  ready_action_ids: RobotControlGoalChecklistItemId[];
  side_blocker_ids: RobotControlGoalChecklistItemId[];
  side_blocker_count: number;
  ready_action_count: number;
  side_gap_summary_plain: string;
  primary_status_item_id: RobotControlGoalChecklistItemId | "";
  primary_status_source_card_id: RobotControlActionStatusCardId | "";
  next_action_item_id: RobotControlGoalChecklistItemId | "";
  next_action_source_card_id: RobotControlActionStatusCardId | "";
}

export interface RobotControlKeyboardReadbackSummary {
  status: string;
  control_mode: string;
  manual_command_mode: string;
  manual_proxy_endpoint: string;
  stop_proxy_endpoint: string;
  start_ready: string;
  continuous_control_ready: string;
  keyboard_control_start_ready: string;
  keyboard_continuous_control_ready: string;
  hold_to_move_required: string;
  keyboard_hold_to_move_required: string;
  enabled: string;
  keyboard_enabled: string;
  keyboard_motion_verified: string;
  keyboard_continuous_pulse_verified: string;
  keyboard_current_hold_pulse_count: string;
  keyboard_best_continuous_pulse_count: string;
  keyboard_verified_min_forwarded_pulses: string;
  keyboard_safety_confirm_required: string;
  minimal_precheck_safety_only: string;
  plain_hint: string;
  readiness_plain: string;
  continuous_control_contract_plain: string;
  hold_to_move_plain: string;
  stop_triggers_plain: string;
  pulse_timing_plain: string;
  wheel_feedback_acceptance_plain: string;
  next_action_plain: string;
  minimal_precheck_plain: string;
  robot_control_executed: string;
}

export interface RobotControlLiveSummaryResponse extends RobotControlLiveClosureSummary {
  schema: "trashbot.pc_tools_workstation.robot_control_live_summary.v1";
  console_status: RobotControlSummaryResponse["console_status"];
  source_base_url: string;
  normalized_base_url: string;
  observed_at_ms: number;
  workstation_endpoint: "/api/robot-control/live-summary";
  summary_endpoint: "/api/robot-control/summary";
  readback_only: true;
  sends_motion_when_clicked: false;
  starts_nav2: false;
  starts_manual: false;
  starts_keyboard: false;
  starts_free_roam: false;
  starts_map_runtime: false;
  submits_delivery: false;
  stops_motion: false;
  publishes_cmd_vel: false;
  field_acceptance_packet?: RobotControlSummaryResponse["field_acceptance_packet"];
  field_acceptance_status?: RobotControlSummaryResponse["field_acceptance_status"];
  field_acceptance_next_step_id?: RobotControlSummaryResponse["field_acceptance_next_step_id"];
  field_acceptance_next_step_label?: RobotControlSummaryResponse["field_acceptance_next_step_label"];
  field_acceptance_next_step_start_endpoint?: RobotControlSummaryResponse["field_acceptance_next_step_start_endpoint"];
  field_acceptance_next_step_sends_motion?: RobotControlSummaryResponse["field_acceptance_next_step_sends_motion"];
  field_acceptance_next_step_requires_safety_confirm?: RobotControlSummaryResponse["field_acceptance_next_step_requires_safety_confirm"];
  field_acceptance_ready_step_ids?: RobotControlSummaryResponse["field_acceptance_ready_step_ids"];
  field_acceptance_blocked_step_ids?: RobotControlSummaryResponse["field_acceptance_blocked_step_ids"];
  field_acceptance_motion_step_ids?: RobotControlSummaryResponse["field_acceptance_motion_step_ids"];
  field_acceptance_no_motion_step_ids?: RobotControlSummaryResponse["field_acceptance_no_motion_step_ids"];
  field_acceptance_acceptance_endpoints?: RobotControlSummaryResponse["field_acceptance_acceptance_endpoints"];
  field_acceptance_safety_confirm_required?: RobotControlSummaryResponse["field_acceptance_safety_confirm_required"];
  field_acceptance_minimal_precheck_safety_only?: RobotControlSummaryResponse["field_acceptance_minimal_precheck_safety_only"];
  field_acceptance_summary_plain?: RobotControlSummaryResponse["field_acceptance_summary_plain"];
  field_acceptance_wysiwyg_ready?: RobotControlSummaryResponse["field_acceptance_wysiwyg_ready"];
  field_acceptance_wysiwyg_missing_surface_ids?: RobotControlSummaryResponse["field_acceptance_wysiwyg_missing_surface_ids"];
  field_acceptance_wysiwyg_primary_refresh_endpoint?: RobotControlSummaryResponse["field_acceptance_wysiwyg_primary_refresh_endpoint"];
  field_acceptance_wysiwyg_primary_refresh_label?: RobotControlSummaryResponse["field_acceptance_wysiwyg_primary_refresh_label"];
  field_acceptance_wysiwyg_next_action_plain?: RobotControlSummaryResponse["field_acceptance_wysiwyg_next_action_plain"];
  field_acceptance_wysiwyg_camera_next_action_plain?: RobotControlSummaryResponse["field_acceptance_wysiwyg_camera_next_action_plain"];
  field_acceptance_wysiwyg_radar_map_next_action_plain?: RobotControlSummaryResponse["field_acceptance_wysiwyg_radar_map_next_action_plain"];
  field_acceptance_wysiwyg_refresh_sequence?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_sequence"];
  field_acceptance_wysiwyg_refresh_sequence_labels?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_sequence_labels"];
  field_acceptance_wysiwyg_refresh_mode?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_mode"];
  field_acceptance_wysiwyg_refresh_sends_motion?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_sends_motion"];
  field_acceptance_wysiwyg_refresh_starts_nav2?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_starts_nav2"];
  field_acceptance_wysiwyg_refresh_starts_manual?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_starts_manual"];
  field_acceptance_wysiwyg_refresh_starts_keyboard?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_starts_keyboard"];
  field_acceptance_wysiwyg_refresh_starts_free_roam?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_starts_free_roam"];
  field_acceptance_wysiwyg_refresh_starts_radar_lifecycle?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_starts_radar_lifecycle"];
  field_acceptance_wysiwyg_refresh_starts_map_runtime?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_starts_map_runtime"];
  field_acceptance_wysiwyg_refresh_submits_delivery?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_submits_delivery"];
  field_acceptance_wysiwyg_refresh_stops_motion?: RobotControlSummaryResponse["field_acceptance_wysiwyg_refresh_stops_motion"];
  field_acceptance_steps?: RobotControlSummaryResponse["field_acceptance_steps"];
  nav2_route_acceptance_packet?: RobotControlSummaryResponse["nav2_route_acceptance_packet"];
}

export interface RobotControlSummaryResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_summary.v1";
  console_status: "blocked" | "loaded_fail_closed_summary";
  source_base_url: string;
  normalized_base_url: string;
  proxy_policy: {
    vue_direct_robot_api_access: false;
    node_proxy_only: true;
    allowed_methods: Array<"GET" | "POST">;
    allowed_endpoint_class: "status_latest_readback_plus_fixed_control_and_report_proxies";
    unsafe_urls_rejected: true;
  };
  observed_at_ms: number;
  read_endpoints: RobotApiEndpointReadback[];
  o3_proof_summary: RobotApiProofSummary;
  robot_api_connection: {
    status: "not_configured" | "blocked" | "degraded" | "readable";
    loaded_count: number;
    blocked_count: number;
    failed_count: number;
    schema_mismatch_count: number;
    dangerous_true_fields: string[];
    blocked_reasons: string[];
    last_refresh_ms: number;
  };
  current_fact_plain: string;
  action_status_cards?: RobotControlActionStatusCard[];
  goal_checklist?: RobotControlGoalChecklistItem[];
  goal_checklist_summary?: RobotControlGoalChecklistSummary;
  live_closure_summary?: RobotControlLiveClosureSummary;
  goal_summary?: RobotControlGoalChecklistSummary;
  status?: RobotControlLiveClosureSummary["status"];
  live_status?: RobotControlLiveClosureSummary["status"];
  summary_plain?: RobotControlLiveClosureSummary["summary_plain"];
  next_action_plain?: RobotControlLiveClosureSummary["next_action_plain"];
  objective_audit_status?: RobotControlLiveClosureSummary["objective_audit_status"];
  objective_audit_total_count?: RobotControlLiveClosureSummary["objective_audit_total_count"];
  objective_audit_done_count?: RobotControlLiveClosureSummary["objective_audit_done_count"];
  objective_audit_remaining_count?: RobotControlLiveClosureSummary["objective_audit_remaining_count"];
  objective_audit_next_objective_id?: RobotControlLiveClosureSummary["objective_audit_next_objective_id"];
  objective_audit_missing_objective_ids?: RobotControlLiveClosureSummary["objective_audit_missing_objective_ids"];
  objective_audit_summary_plain?: RobotControlLiveClosureSummary["objective_audit_summary_plain"];
  objective_audit_items?: RobotControlLiveClosureSummary["objective_audit_items"];
  fixed_objective_audit_summary_endpoint?: RobotControlLiveClosureSummary["fixed_objective_audit_summary_endpoint"];
  objective_audit_sends_motion_when_clicked?: RobotControlLiveClosureSummary["objective_audit_sends_motion_when_clicked"];
  objective_missing_ids?: RobotControlLiveClosureSummary["objective_audit_missing_objective_ids"];
  objective_next_id?: RobotControlLiveClosureSummary["objective_audit_next_objective_id"];
  motion_objective_complete?: boolean;
  wysiwyg_objective_complete?: RobotControlLiveClosureSummary["live_wysiwyg_ready"];
  precheck_objective_complete?: RobotControlLiveClosureSummary["minimal_precheck_safety_only"];
  mapping_objective_complete?: boolean;
  motion_ready?: boolean;
  motion_complete?: boolean;
  wysiwyg_ready?: RobotControlLiveClosureSummary["live_wysiwyg_ready"];
  wysiwyg_complete?: RobotControlLiveClosureSummary["live_wysiwyg_ready"];
  precheck_ready?: RobotControlLiveClosureSummary["minimal_precheck_safety_only"];
  precheck_complete?: RobotControlLiveClosureSummary["minimal_precheck_safety_only"];
  mapping_ready?: RobotControlLiveClosureSummary["mapping_start_ready"];
  mapping_complete?: boolean;
  map_display_primary_tool?: RobotControlLiveClosureSummary["map_display_primary_tool"];
  map_display_primary_url?: RobotControlLiveClosureSummary["map_display_primary_url"];
  map_display_legacy_url?: RobotControlLiveClosureSummary["map_display_legacy_url"];
  map_display_primary_action_label?: RobotControlLiveClosureSummary["map_display_primary_action_label"];
  map_display_primary_action_opens_new_window?: RobotControlLiveClosureSummary["map_display_primary_action_opens_new_window"];
  map_display_primary_action_opens_current_page?: RobotControlLiveClosureSummary["map_display_primary_action_opens_current_page"];
  map_display_direct_map_default_observer?: RobotControlLiveClosureSummary["map_display_direct_map_default_observer"];
  map_display_direct_map_only?: RobotControlLiveClosureSummary["map_display_direct_map_only"];
  map_display_direct_map_viewport_priority?: RobotControlLiveClosureSummary["map_display_direct_map_viewport_priority"];
  map_display_direct_map_canvas_height_mode?: RobotControlLiveClosureSummary["map_display_direct_map_canvas_height_mode"];
  map_display_direct_map_keeps_page_fullscreen_without_browser_api?: RobotControlLiveClosureSummary["map_display_direct_map_keeps_page_fullscreen_without_browser_api"];
  map_display_direct_map_browser_fullscreen_required?: RobotControlLiveClosureSummary["map_display_direct_map_browser_fullscreen_required"];
  map_display_direct_map_refreshes_radar_scan_proof_on_enter?: RobotControlLiveClosureSummary["map_display_direct_map_refreshes_radar_scan_proof_on_enter"];
  map_display_direct_map_refreshes_map_preview_on_enter?: RobotControlLiveClosureSummary["map_display_direct_map_refreshes_map_preview_on_enter"];
  map_display_direct_map_refreshes_radar_status_on_enter?: RobotControlLiveClosureSummary["map_display_direct_map_refreshes_radar_status_on_enter"];
  map_display_direct_map_starts_radar_lifecycle_on_enter?: RobotControlLiveClosureSummary["map_display_direct_map_starts_radar_lifecycle_on_enter"];
  map_display_default_zoom_percent?: RobotControlLiveClosureSummary["map_display_default_zoom_percent"];
  map_display_max_zoom_percent?: RobotControlLiveClosureSummary["map_display_max_zoom_percent"];
  map_display_too_small_next_action_plain?: RobotControlLiveClosureSummary["map_display_too_small_next_action_plain"];
  map_display_ros2_companion_answer_plain?: RobotControlLiveClosureSummary["map_display_ros2_companion_answer_plain"];
  map_display_ros2_companion_plain?: RobotControlLiveClosureSummary["map_display_ros2_companion_plain"];
  map_display_operator_default_surface?: RobotControlLiveClosureSummary["map_display_operator_default_surface"];
  map_display_companion_replaces_pc_ui?: RobotControlLiveClosureSummary["map_display_companion_replaces_pc_ui"];
  map_display_wysiwyg_overlays?: RobotControlLiveClosureSummary["map_display_wysiwyg_overlays"];
  map_display_ros2_companion_required?: RobotControlLiveClosureSummary["map_display_ros2_companion_required"];
  map_display_ros2_companion_tools?: RobotControlLiveClosureSummary["map_display_ros2_companion_tools"];
  map_display_engineering_tools_visible_by_default?: RobotControlLiveClosureSummary["map_display_engineering_tools_visible_by_default"];
  map_display_engineering_tools_action_label?: RobotControlLiveClosureSummary["map_display_engineering_tools_action_label"];
  map_display_ordinary_user_tool?: RobotControlLiveClosureSummary["map_display_ordinary_user_tool"];
  map_display_rviz_role_plain?: RobotControlLiveClosureSummary["map_display_rviz_role_plain"];
  map_display_rviz_launch_command?: RobotControlLiveClosureSummary["map_display_rviz_launch_command"];
  map_display_foxglove_role_plain?: RobotControlLiveClosureSummary["map_display_foxglove_role_plain"];
  map_display_foxglove_bridge_package?: RobotControlLiveClosureSummary["map_display_foxglove_bridge_package"];
  map_display_foxglove_bridge_install_command?: RobotControlLiveClosureSummary["map_display_foxglove_bridge_install_command"];
  map_display_foxglove_bridge_launch_command?: RobotControlLiveClosureSummary["map_display_foxglove_bridge_launch_command"];
  map_display_foxglove_websocket_url?: RobotControlLiveClosureSummary["map_display_foxglove_websocket_url"];
  map_display_foxglove_web_app_url?: RobotControlLiveClosureSummary["map_display_foxglove_web_app_url"];
  map_display_ros2_observe_topics?: RobotControlLiveClosureSummary["map_display_ros2_observe_topics"];
  map_display_ros2_observe_motion_topics?: RobotControlLiveClosureSummary["map_display_ros2_observe_motion_topics"];
  map_display_ros2_observe_control_tools?: RobotControlLiveClosureSummary["map_display_ros2_observe_control_tools"];
  map_display_engineering_tools_sends_motion?: RobotControlLiveClosureSummary["map_display_engineering_tools_sends_motion"];
  map_display_companion_plain?: RobotControlLiveClosureSummary["map_display_companion_plain"];
  map_display_sends_motion_when_clicked?: RobotControlLiveClosureSummary["map_display_sends_motion_when_clicked"];
  map_display_starts_ros2?: RobotControlLiveClosureSummary["map_display_starts_ros2"];
  map_display_starts_rviz2?: RobotControlLiveClosureSummary["map_display_starts_rviz2"];
  map_display_starts_foxglove?: RobotControlLiveClosureSummary["map_display_starts_foxglove"];
  map_display_starts_nav2?: RobotControlLiveClosureSummary["map_display_starts_nav2"];
  map_display_starts_map_runtime?: RobotControlLiveClosureSummary["map_display_starts_map_runtime"];
  live_wysiwyg_ready?: RobotControlLiveClosureSummary["live_wysiwyg_ready"];
  live_wysiwyg_missing_surface_ids?: RobotControlLiveClosureSummary["live_wysiwyg_missing_surface_ids"];
  live_wysiwyg_missing_reasons?: RobotControlLiveClosureSummary["live_wysiwyg_missing_surface_ids"];
  live_wysiwyg_only_camera_missing?: boolean;
  live_wysiwyg_needs_refresh?: RobotControlLiveClosureSummary["live_wysiwyg_needs_refresh"];
  live_wysiwyg_readback_gap_surface_ids?: RobotControlLiveClosureSummary["live_wysiwyg_readback_gap_surface_ids"];
  live_wysiwyg_primary_readback_gap_surface_id?: RobotControlLiveClosureSummary["live_wysiwyg_primary_readback_gap_surface_id"];
  live_wysiwyg_missing_surface_refresh_endpoints?: RobotControlLiveClosureSummary["live_wysiwyg_missing_surface_refresh_endpoints"];
  live_wysiwyg_missing_surface_refresh_labels?: RobotControlLiveClosureSummary["live_wysiwyg_missing_surface_refresh_labels"];
  live_wysiwyg_primary_refresh_endpoint?: RobotControlLiveClosureSummary["live_wysiwyg_primary_refresh_endpoint"];
  live_wysiwyg_primary_refresh_label?: RobotControlLiveClosureSummary["live_wysiwyg_primary_refresh_label"];
  live_wysiwyg_diagnostic_plain?: RobotControlLiveClosureSummary["live_wysiwyg_diagnostic_plain"];
  live_wysiwyg_camera_diagnostic_plain?: RobotControlLiveClosureSummary["live_wysiwyg_camera_diagnostic_plain"];
  live_wysiwyg_radar_diagnostic_plain?: RobotControlLiveClosureSummary["live_wysiwyg_radar_diagnostic_plain"];
  live_wysiwyg_map_radar_diagnostic_plain?: RobotControlLiveClosureSummary["live_wysiwyg_map_radar_diagnostic_plain"];
  live_wysiwyg_refresh_plan_available?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_plan_available"];
  live_wysiwyg_refresh_sequence?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_sequence"];
  live_wysiwyg_refresh_sequence_labels?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_sequence_labels"];
  live_wysiwyg_focused_refresh_sequence?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_sequence"];
  live_wysiwyg_focused_refresh_sequence_labels?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_sequence_labels"];
  live_wysiwyg_focused_refresh_mode?: RobotControlFieldAcceptanceWysiwygRefreshMode;
  live_wysiwyg_focused_refresh_sends_motion?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_sends_motion"];
  live_wysiwyg_focused_refreshes_camera_first_frame_probe?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_camera_first_frame_probe"];
  live_wysiwyg_focused_refreshes_camera_mjpeg_status?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_camera_mjpeg_status"];
  live_wysiwyg_focused_refreshes_radar_scan_proof?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_radar_scan_proof"];
  live_wysiwyg_focused_refreshes_radar_status?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_radar_status"];
  live_wysiwyg_focused_refreshes_map_preview?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_map_preview"];
  fixed_live_wysiwyg_radar_refresh_endpoint?: RobotControlLiveClosureSummary["fixed_live_wysiwyg_radar_refresh_endpoint"];
  fixed_live_wysiwyg_camera_probe_endpoint?: RobotControlLiveClosureSummary["fixed_live_wysiwyg_camera_probe_endpoint"];
  fixed_live_wysiwyg_map_preview_endpoint?: RobotControlLiveClosureSummary["fixed_live_wysiwyg_map_preview_endpoint"];
  fixed_live_wysiwyg_radar_status_endpoint?: RobotControlLiveClosureSummary["fixed_live_wysiwyg_radar_status_endpoint"];
  fixed_live_wysiwyg_camera_mjpeg_status_endpoint?: RobotControlLiveClosureSummary["fixed_live_wysiwyg_camera_mjpeg_status_endpoint"];
  live_wysiwyg_refresh_sends_motion?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_sends_motion"];
  live_wysiwyg_refresh_starts_nav2?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_starts_nav2"];
  live_wysiwyg_refresh_starts_manual?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_starts_manual"];
  live_wysiwyg_refresh_starts_keyboard?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_starts_keyboard"];
  live_wysiwyg_refresh_starts_free_roam?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_starts_free_roam"];
  live_wysiwyg_refresh_starts_radar_lifecycle?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_starts_radar_lifecycle"];
  live_wysiwyg_refresh_starts_map_runtime?: RobotControlLiveClosureSummary["live_wysiwyg_refresh_starts_map_runtime"];
  live_wysiwyg_surface_summaries?: RobotControlLiveClosureSummary["live_wysiwyg_surface_summaries"];
  primary_action_id?: RobotControlLiveClosureSummary["primary_action_id"];
  route_ready?: RobotControlLiveClosureSummary["route_ready_on_map"];
  route_ready_on_map?: RobotControlLiveClosureSummary["route_ready_on_map"];
  nav2_route_ready?: RobotControlLiveClosureSummary["nav2_route_ready"];
  nav2_complete?: RobotControlLiveClosureSummary["nav2_goal_execution_proven"];
  nav2_goal_succeeded?: RobotControlLiveClosureSummary["nav2_goal_succeeded"];
  nav2_goal_execution_proven?: RobotControlLiveClosureSummary["nav2_goal_execution_proven"];
  trip_execution_ready?: RobotControlNav2RouteAcceptancePacket["ready"];
  trip_execution_complete?: RobotControlNav2RouteAcceptancePacket["completed"];
  trip_execution_missing_evidence?: RobotControlNav2RouteAcceptancePacket["missing_evidence"];
  trip_execution_required_success_markers?: RobotControlNav2RouteAcceptancePacket["required_success_markers"];
  trip_execution_readback_endpoints?: RobotControlNav2RouteAcceptancePacket["readback_endpoints"];
  nav2_post_execute_readback_endpoints?: RobotControlNav2RouteAcceptancePacket["readback_endpoints"];
  nav2_post_execute_readback_sequence_labels?: string[];
  nav2_post_execute_readback_refreshes_map_preview?: boolean;
  nav2_post_execute_readback_refreshes_nav2_latest?: boolean;
  nav2_post_execute_readback_refreshes_wheel_feedback?: boolean;
  nav2_post_execute_readback_refreshes_delivery_latest?: boolean;
  nav2_post_execute_readback_refreshes_summary?: boolean;
  nav2_post_execute_readback_sends_motion?: false;
  nav2_post_execute_readback_starts_nav2?: false;
  nav2_post_execute_readback_starts_manual?: false;
  nav2_post_execute_readback_starts_keyboard?: false;
  nav2_post_execute_readback_starts_free_roam?: false;
  nav2_post_execute_readback_starts_map_runtime?: false;
  nav2_post_execute_readback_submits_delivery?: false;
  nav2_post_execute_readback_stops_motion?: false;
  route_complete?: boolean;
  trip_complete?: boolean;
  wheel_lr_nonzero?: RobotControlLiveClosureSummary["wheel_lr_nonzero_proven"];
  wheel_lr_nonzero_proven?: RobotControlLiveClosureSummary["wheel_lr_nonzero_proven"];
  wheel_feedback_same_window_complete?: RobotControlNav2RouteAcceptancePacket["same_window_wheel_lr_nonzero"];
  same_window_wheel_lr_nonzero_complete?: RobotControlNav2RouteAcceptancePacket["same_window_wheel_lr_nonzero"];
  needs_same_window_wheel_rerun?: RobotControlLiveClosureSummary["needs_same_window_wheel_rerun"];
  route_delivery_success?: RobotControlLiveClosureSummary["delivery_success"];
  delivery_success_current?: RobotControlNav2RouteAcceptancePacket["delivery_success"];
  delivery_success_required?: RobotControlLiveClosureSummary["delivery_success_required"];
  delivery_next_action_plain?: RobotControlLiveClosureSummary["delivery_next_action_plain"];
  fixed_delivery_latest_endpoint?: RobotControlLiveClosureSummary["fixed_delivery_latest_endpoint"];
  fixed_delivery_complete_endpoint?: RobotControlLiveClosureSummary["fixed_delivery_complete_endpoint"];
  delivery_latest_readback_only?: RobotControlLiveClosureSummary["delivery_latest_readback_only"];
  delivery_complete_sends_motion?: RobotControlLiveClosureSummary["delivery_complete_sends_motion"];
  wheel_rerun_ready_for_safety_confirm?: RobotControlLiveClosureSummary["wheel_rerun_ready_for_safety_confirm"];
  wheel_rerun_start_endpoint?: RobotControlLiveClosureSummary["wheel_rerun_start_endpoint"];
  wheel_rerun_start_sends_motion?: RobotControlLiveClosureSummary["wheel_rerun_start_sends_motion"];
  wheel_rerun_requires_safety_confirm?: RobotControlLiveClosureSummary["wheel_rerun_requires_safety_confirm"];
  wheel_rerun_readback_endpoint?: RobotControlLiveClosureSummary["fixed_wheel_readback_endpoint"];
  wheel_rerun_acceptance_endpoints?: RobotControlLiveClosureSummary["wheel_rerun_acceptance_endpoints"];
  wheel_rerun_readback_endpoints?: RobotControlLiveClosureSummary["wheel_rerun_readback_endpoints"];
  wheel_rerun_required_success_markers?: RobotControlLiveClosureSummary["wheel_rerun_required_success_markers"];
  wheel_rerun_current_gap_plain?: RobotControlLiveClosureSummary["wheel_rerun_current_gap_plain"];
  wheel_rerun_next_action_plain?: RobotControlLiveClosureSummary["wheel_rerun_checklist_plain"];
  wheel_rerun_acceptance_plain?: RobotControlLiveClosureSummary["wheel_rerun_acceptance_plain"];
  wheel_rerun_no_extra_precheck_plain?: RobotControlLiveClosureSummary["wheel_rerun_no_extra_precheck_plain"];
  minimal_precheck_safety_only?: RobotControlLiveClosureSummary["minimal_precheck_safety_only"];
  safety_confirm_required_for_motion?: RobotControlLiveClosureSummary["safety_confirm_required_for_motion"];
  live_motion_runbook_items?: RobotControlLiveClosureSummary["live_motion_runbook_items"];
  live_motion_runbook_action_ids?: RobotControlLiveClosureSummary["live_motion_runbook_action_ids"];
  live_motion_runbook_ready_action_ids?: RobotControlLiveClosureSummary["live_motion_runbook_ready_action_ids"];
  live_motion_runbook_blocked_action_ids?: RobotControlLiveClosureSummary["live_motion_runbook_blocked_action_ids"];
  live_motion_runbook_primary_action_id?: RobotControlLiveClosureSummary["live_motion_runbook_primary_action_id"];
  live_motion_runbook_start_endpoints?: RobotControlLiveClosureSummary["live_motion_runbook_start_endpoints"];
  live_motion_runbook_acceptance_endpoints?: RobotControlLiveClosureSummary["live_motion_runbook_acceptance_endpoints"];
  live_motion_runbook_minimal_precheck_safety_only?: RobotControlLiveClosureSummary["live_motion_runbook_minimal_precheck_safety_only"];
  live_motion_runbook_safety_confirm_required?: RobotControlLiveClosureSummary["live_motion_runbook_safety_confirm_required"];
  live_motion_runbook_summary_plain?: RobotControlLiveClosureSummary["live_motion_runbook_summary_plain"];
  live_motion_runbook_ready_plain?: RobotControlLiveClosureSummary["live_motion_runbook_ready_plain"];
  live_motion_runbook_blocked_plain?: RobotControlLiveClosureSummary["live_motion_runbook_blocked_plain"];
  live_motion_runbook_primary_action_plain?: RobotControlLiveClosureSummary["live_motion_runbook_primary_action_plain"];
  live_motion_runbook_minimal_precheck_plain?: RobotControlLiveClosureSummary["live_motion_runbook_minimal_precheck_plain"];
  field_acceptance_packet?: RobotControlFieldAcceptancePacket;
  field_acceptance_status?: RobotControlFieldAcceptancePacket["status"];
  field_acceptance_next_step_id?: RobotControlFieldAcceptancePacket["next_step_id"];
  field_acceptance_next_step_label?: RobotControlFieldAcceptancePacket["next_step_label"];
  field_acceptance_next_step_display_label?: RobotControlFieldAcceptancePacket["next_step_display_label"];
  field_acceptance_next_step_start_endpoint?: RobotControlFieldAcceptancePacket["next_step_start_endpoint"];
  field_acceptance_next_step_sends_motion?: RobotControlFieldAcceptancePacket["next_step_sends_motion"];
  field_acceptance_next_step_requires_safety_confirm?: RobotControlFieldAcceptancePacket["next_step_requires_safety_confirm"];
  field_acceptance_parallel_status_plain?: string;
  field_acceptance_parallel_no_motion_action_id?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_id"];
  field_acceptance_parallel_no_motion_action_label?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_label"];
  field_acceptance_parallel_no_motion_action_endpoint?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_endpoint"];
  field_acceptance_parallel_no_motion_action_method?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_method"];
  field_acceptance_parallel_no_motion_action_sequence?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sequence"];
  field_acceptance_parallel_no_motion_action_sequence_labels?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sequence_labels"];
  field_acceptance_parallel_safety_action_id?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_id"];
  field_acceptance_parallel_safety_action_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_label"];
  field_acceptance_parallel_safety_action_display_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_display_label"];
  field_acceptance_parallel_safety_action_start_endpoint?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_start_endpoint"];
  field_acceptance_parallel_safety_action_acceptance_endpoints?: string[];
  field_acceptance_parallel_hardware_action_id?: RobotControlFieldAcceptancePacket["primary_hardware_action_id"];
  field_acceptance_parallel_hardware_action_label?: RobotControlFieldAcceptancePacket["primary_hardware_action_label"];
  field_acceptance_parallel_hardware_action_after_readback_sequence?: RobotControlFieldAcceptancePacket["primary_hardware_action_after_readback_sequence"];
  field_acceptance_parallel_mapping_missing_evidence?: RobotControlLiveClosureSummary["mapping_start_missing_reasons"];
  field_acceptance_parallel_free_move_allowed_while_mapping_blocked?: boolean;
  field_acceptance_parallel_sends_motion_when_clicked?: false;
  field_acceptance_ready_step_ids?: RobotControlFieldAcceptancePacket["ready_step_ids"];
  field_acceptance_blocked_step_ids?: RobotControlFieldAcceptancePacket["blocked_step_ids"];
  field_acceptance_motion_step_ids?: RobotControlFieldAcceptancePacket["motion_step_ids"];
  field_acceptance_no_motion_step_ids?: RobotControlFieldAcceptancePacket["no_motion_step_ids"];
  field_acceptance_safety_confirm_ready_step_ids?: RobotControlFieldAcceptancePacket["safety_confirm_ready_step_ids"];
  field_acceptance_safety_confirm_ready_action_ids?: RobotControlFieldAcceptancePacket["safety_confirm_ready_step_ids"];
  field_acceptance_safety_confirm_ready_action_labels?: RobotControlFieldAcceptancePacket["safety_confirm_ready_action_labels"];
  field_acceptance_safety_confirm_ready_action_display_labels?: RobotControlFieldAcceptancePacket["safety_confirm_ready_action_display_labels"];
  field_acceptance_safety_confirm_ready_action_endpoints?: RobotControlFieldAcceptancePacket["safety_confirm_ready_action_start_endpoints"];
  field_acceptance_safety_confirm_ready_action_start_endpoints?: RobotControlFieldAcceptancePacket["safety_confirm_ready_action_start_endpoints"];
  field_acceptance_safety_confirm_ready_action_stop_endpoints?: string[];
  field_acceptance_safety_confirm_ready_action_acceptance_endpoints?: string[];
  field_acceptance_safety_confirm_ready_action_minimal_precheck_safety_only?: boolean[];
  field_acceptance_safety_confirm_ready_action_camera_preflight_required?: boolean[];
  field_acceptance_safety_confirm_ready_action_radar_preflight_required?: boolean[];
  field_acceptance_safety_confirm_ready_action_operator_report_preflight_required?: boolean[];
  field_acceptance_safety_confirm_ready_action_route_wysiwyg_preflight_required?: boolean[];
  field_acceptance_safety_confirm_ready_actions?: RobotControlFieldAcceptancePacket["safety_confirm_ready_actions"];
  field_acceptance_primary_safety_confirm_ready_action_id?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_id"];
  field_acceptance_primary_safety_confirm_ready_action_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_label"];
  field_acceptance_primary_safety_confirm_ready_action_display_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_display_label"];
  field_acceptance_primary_safety_confirm_ready_action_start_endpoint?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_start_endpoint"];
  field_acceptance_primary_safety_confirm_ready_action_stop_endpoint?: string;
  field_acceptance_primary_safety_confirm_ready_action_acceptance_endpoints?: string[];
  field_acceptance_primary_safety_confirm_ready_action_minimal_precheck_safety_only?: boolean;
  field_acceptance_primary_safety_confirm_ready_action_camera_preflight_required?: boolean;
  field_acceptance_primary_safety_confirm_ready_action_radar_preflight_required?: boolean;
  field_acceptance_primary_safety_confirm_ready_action_operator_report_preflight_required?: boolean;
  field_acceptance_primary_safety_confirm_ready_action_route_wysiwyg_preflight_required?: boolean;
  field_acceptance_primary_safety_confirm_ready_action_requires_safety_confirm?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_requires_safety_confirm"];
  field_acceptance_primary_safety_confirm_ready_action_sends_motion?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_sends_motion"];
  field_acceptance_primary_safety_action_id?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_id"];
  field_acceptance_primary_safety_action_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_label"];
  field_acceptance_primary_safety_action_display_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_display_label"];
  field_acceptance_primary_safety_action_start_endpoint?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_start_endpoint"];
  field_acceptance_primary_safety_action_stop_endpoint?: string;
  field_acceptance_primary_safety_action_acceptance_endpoints?: string[];
  field_acceptance_primary_safety_action_ready_for_safety_confirm?: boolean;
  field_acceptance_primary_safety_action_minimal_precheck_safety_only?: boolean;
  field_acceptance_primary_safety_action_operator_report_preflight_required?: boolean;
  field_acceptance_primary_safety_action_requires_safety_confirm?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_requires_safety_confirm"];
  field_acceptance_primary_safety_action_sends_motion?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_sends_motion"];
  current_motion_action_required?: boolean;
  current_motion_action_id?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_id"];
  current_motion_action_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_label"];
  current_motion_action_display_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_display_label"];
  current_motion_action_start_endpoint?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_start_endpoint"];
  current_motion_action_stop_endpoint?: string;
  current_motion_action_acceptance_endpoints?: string[];
  current_motion_action_readback_endpoints?: string[];
  current_motion_action_required_success_markers?: RobotControlFieldAcceptanceStep["missing_evidence"];
  current_motion_action_proof_status?: RobotControlFieldAcceptanceStep["proof_status"];
  current_motion_action_missing_evidence?: RobotControlFieldAcceptanceStep["missing_evidence"];
  current_motion_action_proof_plain?: RobotControlFieldAcceptanceStep["proof_plain"];
  current_motion_action_ready_for_safety_confirm?: boolean;
  current_motion_action_requires_safety_confirm?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_requires_safety_confirm"];
  current_motion_action_minimal_precheck_safety_only?: boolean;
  current_motion_action_camera_preflight_required?: boolean;
  current_motion_action_radar_preflight_required?: boolean;
  current_motion_action_operator_report_preflight_required?: boolean;
  current_motion_action_route_wysiwyg_preflight_required?: boolean;
  current_motion_action_sends_motion?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_sends_motion"];
  current_motion_action_starts_nav2?: boolean;
  current_motion_action_starts_manual?: false;
  current_motion_action_starts_keyboard?: false;
  current_motion_action_starts_free_roam?: false;
  current_motion_action_starts_map_runtime?: false;
  current_motion_action_submits_delivery?: false;
  current_motion_action_stops_motion?: false;
  current_motion_action_route_ready_on_map?: RobotControlNav2RouteAcceptancePacket["route_ready_on_map"];
  current_motion_action_nav2_goal_succeeded?: RobotControlNav2RouteAcceptancePacket["nav2_goal_succeeded"];
  current_motion_action_same_window_wheel_lr_nonzero?: RobotControlNav2RouteAcceptancePacket["same_window_wheel_lr_nonzero"];
  current_motion_action_delivery_success?: RobotControlNav2RouteAcceptancePacket["delivery_success"];
  current_motion_action_needs_same_window_wheel_rerun?: RobotControlNav2RouteAcceptancePacket["needs_same_window_wheel_rerun"];
  current_motion_action_delivery_success_required?: RobotControlNav2RouteAcceptancePacket["delivery_success_required"];
  current_motion_action_latest_raw_left?: RobotControlNav2RouteAcceptancePacket["latest_raw_left"];
  current_motion_action_latest_raw_right?: RobotControlNav2RouteAcceptancePacket["latest_raw_right"];
  current_motion_action_feedback_sample_count?: RobotControlNav2RouteAcceptancePacket["feedback_sample_count"];
  current_motion_action_feedback_nonzero_sample_count?: RobotControlNav2RouteAcceptancePacket["feedback_nonzero_sample_count"];
  current_motion_action_current_gap_plain?: RobotControlNav2RouteAcceptancePacket["current_gap_plain"];
  current_motion_action_no_extra_precheck_plain?: RobotControlNav2RouteAcceptancePacket["no_extra_precheck_plain"];
  current_motion_action_delivery_next_action_plain?: RobotControlNav2RouteAcceptancePacket["delivery_next_action_plain"];
  current_motion_verification_pack_status?: "complete" | "ready_for_safety_confirm" | "blocked";
  current_motion_verification_pack_plain?: string;
  current_motion_verification_pack_action_ids?: RobotControlFieldAcceptancePacket["safety_confirm_ready_step_ids"];
  current_motion_verification_pack_action_display_labels?: RobotControlFieldAcceptancePacket["safety_confirm_ready_action_display_labels"];
  current_motion_verification_pack_action_start_endpoints?: RobotControlFieldAcceptancePacket["safety_confirm_ready_action_start_endpoints"];
  current_motion_verification_pack_action_stop_endpoints?: string[];
  current_motion_verification_pack_action_readback_endpoints?: string[];
  current_motion_verification_pack_primary_action_id?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_id"];
  current_motion_verification_pack_primary_action_display_label?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_display_label"];
  current_motion_verification_pack_primary_action_start_endpoint?: RobotControlFieldAcceptancePacket["primary_safety_confirm_ready_action_start_endpoint"];
  current_motion_verification_pack_primary_action_stop_endpoint?: string;
  current_motion_verification_pack_primary_action_readback_endpoints?: string[];
  current_motion_verification_pack_ready_action_count?: number;
  current_motion_verification_pack_missing_evidence?: string[];
  current_motion_verification_pack_required_success_markers?: string[];
  current_motion_verification_pack_requires_safety_confirm?: boolean;
  current_motion_verification_pack_minimal_precheck_safety_only?: boolean;
  current_motion_verification_pack_camera_preflight_required?: boolean;
  current_motion_verification_pack_radar_preflight_required?: boolean;
  current_motion_verification_pack_operator_report_preflight_required?: boolean;
  current_motion_verification_pack_route_wysiwyg_preflight_required?: boolean;
  current_motion_verification_pack_sends_motion_when_executed?: boolean;
  current_motion_verification_pack_sends_motion_when_clicked?: false;
  current_motion_verification_pack_readback_sends_motion?: false;
  current_motion_verification_pack_starts_nav2_when_clicked?: false;
  current_motion_verification_pack_starts_manual_when_clicked?: false;
  current_motion_verification_pack_starts_keyboard_when_clicked?: false;
  current_motion_verification_pack_starts_free_roam_when_clicked?: false;
  current_motion_verification_pack_starts_map_runtime_when_clicked?: false;
  current_motion_verification_pack_submits_delivery_when_clicked?: false;
  current_motion_verification_pack_stops_motion_when_clicked?: false;
  current_keyboard_action_required?: boolean;
  current_keyboard_action_ready?: RobotControlLiveMotionRunbookItem["ready"];
  current_keyboard_action_id?: RobotControlLiveMotionRunbookItem["id"] | "none";
  current_keyboard_action_label?: RobotControlLiveMotionRunbookItem["label"];
  current_keyboard_action_display_label?: RobotControlLiveMotionRunbookItem["display_label"];
  current_keyboard_action_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  current_keyboard_action_stop_endpoint?: RobotControlLiveMotionRunbookItem["stop_endpoint"];
  current_keyboard_action_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  current_keyboard_action_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  current_keyboard_action_required_success_markers?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  current_keyboard_action_proof_status?: RobotControlLiveMotionRunbookItem["proof_status"];
  current_keyboard_action_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  current_keyboard_action_proof_plain?: RobotControlLiveMotionRunbookItem["proof_plain"];
  current_keyboard_action_ready_for_safety_confirm?: RobotControlLiveMotionRunbookItem["ready"];
  current_keyboard_action_requires_safety_confirm?: RobotControlLiveMotionRunbookItem["safety_confirm_required"];
  current_keyboard_action_minimal_precheck_safety_only?: RobotControlLiveMotionRunbookItem["minimal_precheck_safety_only"];
  current_keyboard_action_enable_sends_motion?: RobotControlLiveClosureSummary["keyboard_continuous_enable_sends_motion"];
  current_keyboard_action_hold_to_move_required?: RobotControlLiveClosureSummary["keyboard_continuous_hold_to_move_required"];
  current_keyboard_action_hold_sends_motion?: true;
  current_keyboard_action_starts_nav2?: false;
  current_keyboard_action_starts_manual?: false;
  current_keyboard_action_starts_keyboard?: true;
  current_keyboard_action_starts_free_roam?: false;
  current_keyboard_action_starts_map_runtime?: false;
  current_keyboard_action_submits_delivery?: false;
  current_keyboard_action_stops_motion?: false;
  current_keyboard_action_pulse_interval_ms?: RobotControlLiveClosureSummary["keyboard_continuous_pulse_interval_ms"];
  current_keyboard_action_pulse_duration_ms?: RobotControlLiveClosureSummary["keyboard_continuous_pulse_duration_ms"];
  current_keyboard_action_stop_triggers?: RobotControlLiveClosureSummary["keyboard_continuous_stop_triggers"];
  current_keyboard_action_wheel_feedback_acceptance?: RobotControlLiveClosureSummary["keyboard_continuous_wheel_feedback_acceptance"];
  current_keyboard_action_post_hold_readback_endpoints?: Array<
    RobotControlLiveClosureSummary["fixed_keyboard_feedback_readback_endpoint"] | RobotControlLiveClosureSummary["fixed_keyboard_summary_endpoint"]
  >;
  current_keyboard_action_post_hold_readback_sequence_labels?: string[];
  current_keyboard_action_post_hold_feedback_readback_required?: RobotControlLiveClosureSummary["keyboard_continuous_post_hold_feedback_readback_required"];
  current_keyboard_action_post_hold_summary_refresh_required?: RobotControlLiveClosureSummary["keyboard_continuous_post_hold_summary_refresh_required"];
  current_keyboard_action_post_hold_readback_sends_motion?: false;
  current_keyboard_action_post_hold_readback_starts_nav2?: false;
  current_keyboard_action_post_hold_readback_starts_manual?: false;
  current_keyboard_action_post_hold_readback_starts_keyboard?: false;
  current_keyboard_action_post_hold_readback_starts_free_roam?: false;
  current_keyboard_action_post_hold_readback_starts_map_runtime?: false;
  current_keyboard_action_post_hold_readback_submits_delivery?: false;
  current_keyboard_action_post_hold_readback_stops_motion?: false;
  current_free_move_action_required?: boolean;
  current_free_move_action_ready?: RobotControlLiveMotionRunbookItem["ready"];
  current_free_move_action_id?: RobotControlLiveMotionRunbookItem["id"] | "none";
  current_free_move_action_label?: RobotControlLiveMotionRunbookItem["label"];
  current_free_move_action_display_label?: RobotControlLiveMotionRunbookItem["display_label"];
  current_free_move_action_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  current_free_move_action_stop_endpoint?: RobotControlLiveMotionRunbookItem["stop_endpoint"];
  current_free_move_action_latest_endpoint?: RobotControlLiveClosureSummary["fixed_free_roam_latest_endpoint"];
  current_free_move_action_readback_endpoint?: RobotControlLiveClosureSummary["fixed_free_roam_latest_endpoint"];
  current_free_move_action_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  current_free_move_action_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  current_free_move_action_post_start_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  current_free_move_action_post_start_readback_sequence_labels?: string[];
  current_free_move_action_post_start_readback_refreshes_latest?: boolean;
  current_free_move_action_post_start_readback_refreshes_map_preview?: boolean;
  current_free_move_action_post_start_readback_refreshes_summary?: boolean;
  current_free_move_action_post_start_readback_sends_motion?: false;
  current_free_move_action_post_start_readback_starts_nav2?: false;
  current_free_move_action_post_start_readback_starts_manual?: false;
  current_free_move_action_post_start_readback_starts_keyboard?: false;
  current_free_move_action_post_start_readback_starts_free_roam?: false;
  current_free_move_action_post_start_readback_starts_map_runtime?: false;
  current_free_move_action_post_start_readback_submits_delivery?: false;
  current_free_move_action_post_start_readback_stops_motion?: false;
  current_free_move_action_required_success_markers?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  current_free_move_action_proof_status?: RobotControlLiveMotionRunbookItem["proof_status"];
  current_free_move_action_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  current_free_move_action_proof_plain?: RobotControlLiveMotionRunbookItem["proof_plain"];
  current_free_move_action_acceptance_plain?: RobotControlLiveMotionRunbookItem["acceptance_plain"];
  current_free_move_action_ready_for_safety_confirm?: RobotControlLiveMotionRunbookItem["ready"];
  current_free_move_action_requires_safety_confirm?: RobotControlLiveMotionRunbookItem["safety_confirm_required"];
  current_free_move_action_minimal_precheck_safety_only?: RobotControlLiveMotionRunbookItem["minimal_precheck_safety_only"];
  current_free_move_action_camera_preflight_required?: RobotControlLiveClosureSummary["free_move_camera_preflight_required"];
  current_free_move_action_radar_preflight_required?: RobotControlLiveClosureSummary["free_move_radar_preflight_required"];
  current_free_move_action_without_camera_allowed?: RobotControlLiveClosureSummary["free_move_without_camera_allowed"];
  current_free_move_action_without_radar_allowed?: RobotControlLiveClosureSummary["free_roam_motion_without_radar_allowed"];
  current_free_move_action_blocked_by_camera_wysiwyg?: RobotControlLiveClosureSummary["free_move_blocked_by_camera_wysiwyg"];
  current_free_move_action_blocked_by_radar_wysiwyg?: RobotControlLiveClosureSummary["free_move_blocked_by_radar_wysiwyg"];
  current_free_move_action_sends_motion?: RobotControlLiveMotionRunbookItem["sends_motion_when_executed"];
  current_free_move_action_starts_nav2?: false;
  current_free_move_action_starts_manual?: false;
  current_free_move_action_starts_keyboard?: false;
  current_free_move_action_starts_free_roam?: true;
  current_free_move_action_starts_map_runtime?: false;
  current_free_move_action_submits_delivery?: false;
  current_free_move_action_stops_motion?: false;
  current_mapping_action_required?: boolean;
  current_mapping_action_ready?: RobotControlLiveMotionRunbookItem["ready"];
  current_mapping_action_id?: RobotControlLiveMotionRunbookItem["id"] | "none";
  current_mapping_action_label?: RobotControlLiveMotionRunbookItem["label"];
  current_mapping_action_display_label?: RobotControlLiveMotionRunbookItem["display_label"];
  current_mapping_action_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  current_mapping_action_stop_endpoint?: RobotControlLiveMotionRunbookItem["stop_endpoint"];
  current_mapping_action_preview_endpoint?: RobotControlLiveClosureSummary["fixed_mapping_preview_endpoint"];
  current_mapping_action_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  current_mapping_action_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  current_mapping_action_post_start_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  current_mapping_action_post_start_readback_sequence_labels?: string[];
  current_mapping_action_post_start_readback_refreshes_free_roam_latest?: boolean;
  current_mapping_action_post_start_readback_refreshes_map_preview?: boolean;
  current_mapping_action_post_start_readback_refreshes_summary?: boolean;
  current_mapping_action_post_start_readback_sends_motion?: false;
  current_mapping_action_post_start_readback_starts_nav2?: false;
  current_mapping_action_post_start_readback_starts_manual?: false;
  current_mapping_action_post_start_readback_starts_keyboard?: false;
  current_mapping_action_post_start_readback_starts_free_roam?: false;
  current_mapping_action_post_start_readback_starts_map_runtime?: false;
  current_mapping_action_post_start_readback_submits_delivery?: false;
  current_mapping_action_post_start_readback_stops_motion?: false;
  current_mapping_action_required_success_markers?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  current_mapping_action_proof_status?: RobotControlLiveMotionRunbookItem["proof_status"];
  current_mapping_action_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  current_mapping_action_proof_plain?: RobotControlLiveMotionRunbookItem["proof_plain"];
  current_mapping_action_requires_safety_confirm?: RobotControlLiveMotionRunbookItem["safety_confirm_required"];
  current_mapping_action_safety_confirm_required_when_executed?: true;
  current_mapping_action_minimal_precheck_safety_only?: RobotControlLiveMotionRunbookItem["minimal_precheck_safety_only"];
  current_mapping_action_camera_required?: RobotControlLiveClosureSummary["mapping_start_requires_camera_first_frame"];
  current_mapping_action_radar_required?: RobotControlLiveClosureSummary["mapping_start_requires_lidar_fresh"];
  current_mapping_action_camera_ready?: boolean;
  current_mapping_action_radar_ready?: boolean;
  current_mapping_action_camera_blocks_start?: RobotControlLiveClosureSummary["mapping_camera_blocks_start"];
  current_mapping_action_radar_blocks_start?: RobotControlLiveClosureSummary["mapping_lidar_blocks_start"];
  current_mapping_action_only_camera_missing?: boolean;
  current_mapping_action_radar_overlay_wysiwyg_complete?: boolean;
  current_mapping_action_camera_hardware_action_required?: RobotControlLiveClosureSummary["camera_hardware_action_required"];
  current_mapping_action_camera_hardware_action_label?: RobotControlLiveClosureSummary["camera_hardware_action_label"];
  current_mapping_action_camera_usb_full_speed_detected?: RobotControlLiveClosureSummary["camera_usb_full_speed_detected"];
  current_mapping_action_camera_usb_speed?: RobotControlLiveClosureSummary["camera_usb_speed"];
  current_mapping_action_camera_source_diagnosis_status?: RobotControlLiveClosureSummary["camera_source_diagnosis_status"];
  current_mapping_action_camera_source_diagnosis_not_exclusive?: RobotControlLiveClosureSummary["camera_source_diagnosis_not_exclusive"];
  current_mapping_action_camera_recovery_next_action_plain?: RobotControlLiveClosureSummary["camera_recovery_next_action_plain"];
  current_mapping_action_blocks_free_move?: false;
  current_mapping_action_free_move_allowed_while_blocked?: boolean;
  current_mapping_action_sends_motion?: RobotControlLiveMotionRunbookItem["sends_motion_when_executed"];
  current_mapping_action_starts_map_runtime_when_executed?: true;
  current_mapping_action_starts_nav2?: false;
  current_mapping_action_starts_manual?: false;
  current_mapping_action_starts_keyboard?: false;
  current_mapping_action_starts_free_roam?: false;
  current_mapping_action_submits_delivery?: false;
  current_mapping_action_stops_motion?: false;
  field_acceptance_hardware_action_ids?: RobotControlFieldAcceptancePacket["hardware_action_ids"];
  field_acceptance_hardware_action_labels?: RobotControlFieldAcceptancePacket["hardware_action_labels"];
  field_acceptance_hardware_action_after_readback_endpoints?: RobotControlFieldAcceptancePacket["hardware_action_after_readback_endpoints"];
  field_acceptance_hardware_action_after_readback_sequences?: RobotControlFieldAcceptancePacket["hardware_action_after_readback_sequences"];
  field_acceptance_hardware_action_after_readback_sequence_labels?: RobotControlFieldAcceptancePacket["hardware_action_after_readback_sequence_labels"];
  field_acceptance_hardware_actions?: RobotControlFieldAcceptancePacket["hardware_actions"];
  field_acceptance_primary_hardware_action_id?: RobotControlFieldAcceptancePacket["primary_hardware_action_id"];
  field_acceptance_primary_hardware_action_label?: RobotControlFieldAcceptancePacket["primary_hardware_action_label"];
  field_acceptance_primary_hardware_action_after_readback_endpoint?: RobotControlFieldAcceptancePacket["primary_hardware_action_after_readback_endpoint"];
  field_acceptance_primary_hardware_action_after_readback_sequence?: RobotControlFieldAcceptancePacket["primary_hardware_action_after_readback_sequence"];
  field_acceptance_primary_hardware_action_after_readback_sequence_labels?: RobotControlFieldAcceptancePacket["primary_hardware_action_after_readback_sequence_labels"];
  field_acceptance_primary_hardware_action_blocks_mapping_start?: RobotControlFieldAcceptancePacket["primary_hardware_action_blocks_mapping_start"];
  field_acceptance_primary_hardware_action_blocks_free_move?: RobotControlFieldAcceptancePacket["primary_hardware_action_blocks_free_move"];
  current_hardware_action_required?: boolean;
  current_hardware_action_id?: RobotControlFieldAcceptancePacket["primary_hardware_action_id"];
  current_hardware_action_label?: RobotControlFieldAcceptancePacket["primary_hardware_action_label"];
  current_hardware_action_plain?: RobotControlFieldAcceptancePacket["remaining_hardware_action_summary_plain"];
  current_hardware_action_after_readback_endpoint?: RobotControlFieldAcceptancePacket["primary_hardware_action_after_readback_endpoint"];
  current_hardware_action_after_readback_sequence?: RobotControlFieldAcceptancePacket["primary_hardware_action_after_readback_sequence"];
  current_hardware_action_after_readback_sequence_labels?: RobotControlFieldAcceptancePacket["primary_hardware_action_after_readback_sequence_labels"];
  current_hardware_action_blocks_mapping_start?: RobotControlFieldAcceptancePacket["primary_hardware_action_blocks_mapping_start"];
  current_hardware_action_blocks_free_move?: RobotControlFieldAcceptancePacket["primary_hardware_action_blocks_free_move"];
  current_hardware_action_sends_motion?: false;
  field_acceptance_missing_evidence_ids?: RobotControlFieldAcceptancePacket["missing_evidence_ids"];
  field_acceptance_missing_evidence_labels?: RobotControlFieldAcceptancePacket["missing_evidence_labels"];
  field_acceptance_missing_evidence_items?: RobotControlFieldAcceptancePacket["missing_evidence_items"];
  field_acceptance_primary_missing_id?: RobotControlFieldAcceptancePacket["primary_missing_evidence_id"];
  field_acceptance_primary_missing_label?: RobotControlFieldAcceptancePacket["primary_missing_evidence_label"];
  field_acceptance_primary_missing_action_id?: RobotControlFieldAcceptancePacket["primary_missing_evidence_action_id"];
  field_acceptance_primary_missing_action_label?: RobotControlFieldAcceptanceStep["label"] | "none";
  field_acceptance_primary_missing_action_display_label?: RobotControlFieldAcceptanceStep["display_label"] | "none";
  field_acceptance_primary_missing_action_start_endpoint?: RobotControlFieldAcceptanceStep["start_endpoint"] | "none";
  field_acceptance_primary_missing_action_stop_endpoint?: RobotControlFieldAcceptanceStep["stop_endpoint"] | "none";
  field_acceptance_primary_missing_action_acceptance_endpoints?: RobotControlFieldAcceptanceStep["acceptance_endpoints"];
  field_acceptance_primary_missing_action_sends_motion?: RobotControlFieldAcceptanceStep["sends_motion_when_executed"];
  field_acceptance_primary_missing_action_requires_safety_confirm?: RobotControlFieldAcceptanceStep["safety_confirm_required"];
  field_acceptance_primary_missing_action_minimal_precheck_safety_only?: boolean;
  field_acceptance_primary_missing_action_camera_preflight_required?: boolean;
  field_acceptance_primary_missing_action_radar_preflight_required?: boolean;
  field_acceptance_primary_missing_action_operator_report_preflight_required?: boolean;
  field_acceptance_primary_missing_action_route_wysiwyg_preflight_required?: boolean;
  field_acceptance_primary_readback_endpoint?: RobotControlFieldAcceptancePacket["primary_missing_evidence_readback_endpoint"];
  field_acceptance_primary_readback_method?: RobotControlFieldAcceptancePacket["primary_missing_evidence_readback_method"];
  field_acceptance_primary_requires_motion_before_readback?: RobotControlFieldAcceptancePacket["primary_missing_evidence_requires_motion_before_readback"];
  field_acceptance_primary_requires_safety_confirm_before_motion?: RobotControlFieldAcceptancePacket["primary_missing_evidence_requires_safety_confirm_before_motion"];
  field_acceptance_primary_blocks_field_acceptance?: RobotControlFieldAcceptancePacket["primary_missing_evidence_blocks_field_acceptance"];
  field_acceptance_primary_missing_evidence_id?: RobotControlFieldAcceptancePacket["primary_missing_evidence_id"];
  field_acceptance_primary_missing_evidence_label?: RobotControlFieldAcceptancePacket["primary_missing_evidence_label"];
  field_acceptance_primary_missing_evidence_action_id?: RobotControlFieldAcceptancePacket["primary_missing_evidence_action_id"];
  field_acceptance_primary_missing_evidence_action_label?: RobotControlFieldAcceptancePacket["primary_missing_evidence_action_label"];
  field_acceptance_primary_missing_evidence_action_display_label?: RobotControlFieldAcceptancePacket["primary_missing_evidence_action_display_label"];
  field_acceptance_primary_missing_evidence_readback_endpoint?: RobotControlFieldAcceptancePacket["primary_missing_evidence_readback_endpoint"];
  field_acceptance_primary_missing_evidence_readback_method?: RobotControlFieldAcceptancePacket["primary_missing_evidence_readback_method"];
  field_acceptance_primary_missing_evidence_requires_motion_before_readback?: RobotControlFieldAcceptancePacket["primary_missing_evidence_requires_motion_before_readback"];
  field_acceptance_primary_missing_evidence_requires_safety_confirm_before_motion?: RobotControlFieldAcceptancePacket["primary_missing_evidence_requires_safety_confirm_before_motion"];
  field_acceptance_primary_missing_evidence_blocks_field_acceptance?: RobotControlFieldAcceptancePacket["primary_missing_evidence_blocks_field_acceptance"];
  field_acceptance_no_motion_readback_action_ids?: RobotControlFieldAcceptancePacket["no_motion_readback_action_ids"];
  field_acceptance_no_motion_readback_action_labels?: RobotControlFieldAcceptancePacket["no_motion_readback_action_labels"];
  field_acceptance_no_motion_readback_action_endpoints?: RobotControlFieldAcceptancePacket["no_motion_readback_action_endpoints"];
  field_acceptance_no_motion_readback_action_methods?: RobotControlFieldAcceptancePacket["no_motion_readback_action_methods"];
  field_acceptance_no_motion_readback_action_sequences?: RobotControlFieldAcceptancePacket["no_motion_readback_action_sequences"];
  field_acceptance_no_motion_readback_action_sequence_labels?: RobotControlFieldAcceptancePacket["no_motion_readback_action_sequence_labels"];
  field_acceptance_no_motion_readback_actions?: RobotControlFieldAcceptancePacket["no_motion_readback_actions"];
  field_acceptance_primary_no_motion_readback_id?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_id"];
  field_acceptance_primary_no_motion_readback_label?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_label"];
  field_acceptance_primary_no_motion_readback_endpoint?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_endpoint"];
  field_acceptance_primary_no_motion_readback_method?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_method"];
  field_acceptance_primary_no_motion_readback_sequence?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sequence"];
  field_acceptance_primary_no_motion_readback_sequence_labels?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sequence_labels"];
  field_acceptance_primary_no_motion_readback_sends_motion?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sends_motion"];
  field_acceptance_primary_no_motion_readback_action_id?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_id"];
  field_acceptance_primary_no_motion_readback_action_label?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_label"];
  field_acceptance_primary_no_motion_readback_action_endpoint?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_endpoint"];
  field_acceptance_primary_no_motion_readback_action_method?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_method"];
  field_acceptance_primary_no_motion_readback_action_sequence?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sequence"];
  field_acceptance_primary_no_motion_readback_action_sequence_labels?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sequence_labels"];
  field_acceptance_primary_no_motion_readback_action_refreshes_summary?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_summary"];
  field_acceptance_primary_no_motion_readback_action_refreshes_radar_scan_proof?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_radar_scan_proof"];
  field_acceptance_primary_no_motion_readback_action_refreshes_camera_first_frame_probe?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_camera_first_frame_probe"];
  field_acceptance_primary_no_motion_readback_action_refreshes_map_preview?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_map_preview"];
  field_acceptance_primary_no_motion_readback_action_refreshes_radar_status?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_radar_status"];
  field_acceptance_primary_no_motion_readback_action_refreshes_camera_mjpeg_status?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_camera_mjpeg_status"];
  field_acceptance_primary_no_motion_readback_action_sends_motion?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sends_motion"];
  current_wysiwyg_action_required?: boolean;
  current_wysiwyg_action_id?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_id"];
  current_wysiwyg_action_label?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_label"];
  current_wysiwyg_action_endpoint?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_endpoint"];
  current_wysiwyg_action_method?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_method"];
  current_wysiwyg_action_sequence?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sequence"];
  current_wysiwyg_action_sequence_labels?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sequence_labels"];
  current_wysiwyg_action_refreshes_summary?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_summary"];
  current_wysiwyg_action_refreshes_radar_scan_proof?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_radar_scan_proof"];
  current_wysiwyg_action_refreshes_camera_first_frame_probe?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_camera_first_frame_probe"];
  current_wysiwyg_action_refreshes_map_preview?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_map_preview"];
  current_wysiwyg_action_refreshes_radar_status?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_radar_status"];
  current_wysiwyg_action_refreshes_camera_mjpeg_status?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_refreshes_camera_mjpeg_status"];
  current_wysiwyg_action_sends_motion?: RobotControlFieldAcceptancePacket["primary_no_motion_readback_action_sends_motion"];
  current_wysiwyg_action_starts_radar_lifecycle?: boolean;
  current_wysiwyg_action_starts_map_runtime?: boolean;
  current_wysiwyg_action_starts_nav2?: boolean;
  current_wysiwyg_action_starts_manual?: boolean;
  current_wysiwyg_action_starts_keyboard?: boolean;
  current_wysiwyg_action_starts_free_roam?: boolean;
  current_wysiwyg_action_submits_delivery?: boolean;
  current_wysiwyg_action_stops_motion?: boolean;
  current_wysiwyg_action_missing_surface_ids?: RobotControlFieldAcceptancePacket["wysiwyg_missing_surface_ids"];
  current_wysiwyg_action_refresh_mode?: RobotControlFieldAcceptanceWysiwygRefreshMode;
  current_wysiwyg_next_action_status?: "complete" | "only_camera_hardware_action" | "camera_readback_only" | "radar_map_refresh" | "refresh_current_wysiwyg";
  current_wysiwyg_next_action_plain?: string;
  current_wysiwyg_next_action_radar_overlay_complete?: boolean;
  current_wysiwyg_next_action_only_camera_missing?: boolean;
  current_wysiwyg_next_action_allows_free_move?: boolean;
  current_wysiwyg_next_action_blocks_mapping_start?: boolean;
  current_wysiwyg_next_action_hardware_action_required?: boolean;
  current_wysiwyg_next_action_hardware_action_label?: string;
  current_wysiwyg_next_action_after_readback_sequence?: string[];
  current_wysiwyg_next_action_after_readback_sequence_labels?: string[];
  field_acceptance_remaining_operator_action_summary_plain?: RobotControlFieldAcceptancePacket["remaining_operator_action_summary_plain"];
  field_acceptance_remaining_hardware_action_summary_plain?: RobotControlFieldAcceptancePacket["remaining_hardware_action_summary_plain"];
  field_acceptance_remaining_no_motion_action_summary_plain?: RobotControlFieldAcceptancePacket["remaining_no_motion_action_summary_plain"];
  field_acceptance_remaining_action_summary_plain?: RobotControlFieldAcceptancePacket["remaining_action_summary_plain"];
  field_acceptance_acceptance_endpoints?: RobotControlFieldAcceptancePacket["acceptance_endpoints"];
  field_acceptance_safety_confirm_required?: RobotControlFieldAcceptancePacket["safety_confirm_required"];
  field_acceptance_minimal_precheck_safety_only?: RobotControlFieldAcceptancePacket["minimal_precheck_safety_only"];
  field_acceptance_summary_plain?: RobotControlFieldAcceptancePacket["summary_plain"];
  field_acceptance_wysiwyg_ready?: RobotControlFieldAcceptancePacket["wysiwyg_ready"];
  field_acceptance_wysiwyg_missing_surface_ids?: RobotControlFieldAcceptancePacket["wysiwyg_missing_surface_ids"];
  field_acceptance_wysiwyg_primary_refresh_endpoint?: RobotControlFieldAcceptancePacket["wysiwyg_primary_refresh_endpoint"];
  field_acceptance_wysiwyg_primary_refresh_label?: RobotControlFieldAcceptancePacket["wysiwyg_primary_refresh_label"];
  field_acceptance_wysiwyg_next_action_plain?: RobotControlFieldAcceptancePacket["wysiwyg_next_action_plain"];
  field_acceptance_wysiwyg_camera_next_action_plain?: RobotControlFieldAcceptancePacket["wysiwyg_camera_next_action_plain"];
  field_acceptance_wysiwyg_radar_map_next_action_plain?: RobotControlFieldAcceptancePacket["wysiwyg_radar_map_next_action_plain"];
  field_acceptance_wysiwyg_refresh_sequence?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_sequence"];
  field_acceptance_wysiwyg_refresh_sequence_labels?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_sequence_labels"];
  field_acceptance_wysiwyg_refresh_mode?: RobotControlFieldAcceptanceWysiwygRefreshMode;
  field_acceptance_wysiwyg_refreshes_camera_first_frame_probe?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_camera_first_frame_probe"];
  field_acceptance_wysiwyg_refreshes_camera_mjpeg_status?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_camera_mjpeg_status"];
  field_acceptance_wysiwyg_refreshes_radar_scan_proof?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_radar_scan_proof"];
  field_acceptance_wysiwyg_refreshes_radar_status?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_radar_status"];
  field_acceptance_wysiwyg_refreshes_map_preview?: RobotControlFieldAcceptancePacket["wysiwyg_refreshes_map_preview"];
  field_acceptance_wysiwyg_refresh_sends_motion?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_sends_motion"];
  field_acceptance_wysiwyg_refresh_starts_nav2?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_starts_nav2"];
  field_acceptance_wysiwyg_refresh_starts_manual?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_starts_manual"];
  field_acceptance_wysiwyg_refresh_starts_keyboard?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_starts_keyboard"];
  field_acceptance_wysiwyg_refresh_starts_free_roam?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_starts_free_roam"];
  field_acceptance_wysiwyg_refresh_starts_radar_lifecycle?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_starts_radar_lifecycle"];
  field_acceptance_wysiwyg_refresh_starts_map_runtime?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_starts_map_runtime"];
  field_acceptance_wysiwyg_refresh_submits_delivery?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_submits_delivery"];
  field_acceptance_wysiwyg_refresh_stops_motion?: RobotControlFieldAcceptancePacket["wysiwyg_refresh_stops_motion"];
  field_acceptance_steps?: RobotControlFieldAcceptancePacket["steps"];
  nav2_route_acceptance_packet?: RobotControlNav2RouteAcceptancePacket;
  primary_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  primary_stop_endpoint?: RobotControlLiveMotionRunbookItem["stop_endpoint"];
  primary_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  primary_sends_motion?: RobotControlLiveMotionRunbookItem["sends_motion_when_executed"];
  primary_requires_safety_confirm?: RobotControlLiveMotionRunbookItem["safety_confirm_required"];
  primary_ready?: RobotControlLiveMotionRunbookItem["ready"];
  primary_completed?: RobotControlLiveMotionRunbookItem["completed"];
  primary_proof_status?: RobotControlLiveMotionRunbookItem["proof_status"];
  primary_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  primary_proof_plain?: RobotControlLiveMotionRunbookItem["proof_plain"];
  trip_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  trip_stop_endpoint?: RobotControlLiveMotionRunbookItem["stop_endpoint"];
  trip_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  trip_ready?: RobotControlLiveMotionRunbookItem["ready"];
  trip_completed?: RobotControlLiveMotionRunbookItem["completed"];
  trip_proof_status?: RobotControlLiveMotionRunbookItem["proof_status"];
  trip_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  trip_proof_plain?: RobotControlLiveMotionRunbookItem["proof_plain"];
  keyboard_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  keyboard_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  keyboard_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  keyboard_required_success_markers?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  keyboard_completed?: RobotControlLiveMotionRunbookItem["completed"];
  keyboard_proof_status?: RobotControlLiveMotionRunbookItem["proof_status"];
  keyboard_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  keyboard_proof_plain?: RobotControlLiveMotionRunbookItem["proof_plain"];
  free_move_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  free_move_stop_endpoint?: RobotControlLiveMotionRunbookItem["stop_endpoint"];
  free_move_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  free_move_readback_endpoint?: RobotControlLiveClosureSummary["fixed_free_roam_latest_endpoint"];
  free_move_latest_endpoint?: RobotControlLiveClosureSummary["fixed_free_roam_latest_endpoint"];
  free_move_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  free_move_post_start_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  free_move_post_start_readback_sequence_labels?: string[];
  free_move_post_start_readback_refreshes_latest?: boolean;
  free_move_post_start_readback_refreshes_map_preview?: boolean;
  free_move_post_start_readback_refreshes_summary?: boolean;
  free_move_post_start_readback_sends_motion?: false;
  free_move_post_start_readback_starts_nav2?: false;
  free_move_post_start_readback_starts_manual?: false;
  free_move_post_start_readback_starts_keyboard?: false;
  free_move_post_start_readback_starts_free_roam?: false;
  free_move_post_start_readback_starts_map_runtime?: false;
  free_move_post_start_readback_submits_delivery?: false;
  free_move_post_start_readback_stops_motion?: false;
  free_move_required_success_marker?: string;
  free_move_required_success_markers?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  free_move_proof_status?: RobotControlLiveMotionRunbookItem["proof_status"];
  free_move_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  free_move_proof_plain?: RobotControlLiveMotionRunbookItem["proof_plain"];
  free_move_acceptance_plain?: RobotControlLiveMotionRunbookItem["acceptance_plain"];
  free_roam_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  free_roam_stop_endpoint?: RobotControlLiveMotionRunbookItem["stop_endpoint"];
  free_roam_latest_endpoint?: RobotControlLiveClosureSummary["fixed_free_roam_latest_endpoint"];
  free_roam_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  free_roam_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  free_roam_required_success_markers?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  free_roam_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  mapping_start_endpoint?: RobotControlLiveMotionRunbookItem["start_endpoint"];
  mapping_preview_endpoint?: RobotControlLiveClosureSummary["fixed_mapping_preview_endpoint"];
  mapping_acceptance_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  mapping_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  mapping_post_start_readback_endpoints?: RobotControlLiveMotionRunbookItem["acceptance_endpoints"];
  mapping_post_start_readback_sequence_labels?: string[];
  mapping_post_start_readback_refreshes_free_roam_latest?: boolean;
  mapping_post_start_readback_refreshes_map_preview?: boolean;
  mapping_post_start_readback_refreshes_summary?: boolean;
  mapping_post_start_readback_sends_motion?: false;
  mapping_post_start_readback_starts_nav2?: false;
  mapping_post_start_readback_starts_manual?: false;
  mapping_post_start_readback_starts_keyboard?: false;
  mapping_post_start_readback_starts_free_roam?: false;
  mapping_post_start_readback_starts_map_runtime?: false;
  mapping_post_start_readback_submits_delivery?: false;
  mapping_post_start_readback_stops_motion?: false;
  mapping_required_success_markers?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  mapping_proof_status?: RobotControlLiveMotionRunbookItem["proof_status"];
  mapping_missing_evidence?: RobotControlLiveMotionRunbookItem["missing_evidence"];
  mapping_proof_plain?: RobotControlLiveMotionRunbookItem["proof_plain"];
  camera_ready?: RobotControlLiveClosureSummary["camera_current_visible"];
  camera_first_frame_ready?: RobotControlLiveClosureSummary["camera_current_visible"];
  camera_visible?: RobotControlLiveClosureSummary["camera_current_visible"];
  camera_current_visible?: RobotControlLiveClosureSummary["camera_current_visible"];
  camera_needs_usb_fix?: RobotControlLiveClosureSummary["camera_hardware_action_required"];
  camera_usb_high_speed?: boolean;
  camera_usb_speed?: RobotControlLiveClosureSummary["camera_usb_speed"];
  map_visible?: RobotControlLiveClosureSummary["map_current_visible"];
  map_current_visible?: RobotControlLiveClosureSummary["map_current_visible"];
  path_visible?: RobotControlLiveClosureSummary["path_current_visible"];
  path_current_visible?: RobotControlLiveClosureSummary["path_current_visible"];
  live_wysiwyg_map_visible?: RobotControlLiveClosureSummary["live_wysiwyg_map_visible"];
  live_wysiwyg_camera_visible?: RobotControlLiveClosureSummary["live_wysiwyg_camera_visible"];
  camera_hardware_action_required?: RobotControlLiveClosureSummary["camera_hardware_action_required"];
  camera_hardware_action_label?: RobotControlLiveClosureSummary["camera_hardware_action_label"];
  camera_usb_full_speed_detected?: RobotControlLiveClosureSummary["camera_usb_full_speed_detected"];
  camera_blocks_mapping_start?: RobotControlLiveClosureSummary["camera_blocks_mapping_start"];
  camera_blocks_free_move?: RobotControlLiveClosureSummary["camera_blocks_free_move"];
  camera_reprobe_after_hardware_action_required?: RobotControlLiveClosureSummary["camera_reprobe_after_hardware_action_required"];
  camera_reprobe_sequence?: RobotControlLiveClosureSummary["camera_reprobe_sequence"];
  camera_reprobe_sequence_labels?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sequence_labels"];
  camera_reprobe_sequence_sends_motion?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sends_motion"];
  camera_hardware_action_next_action_plain?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_next_action_plain"];
  camera_source_diagnosis_status?: RobotControlLiveClosureSummary["camera_source_diagnosis_status"];
  camera_source_diagnosis_not_exclusive?: RobotControlLiveClosureSummary["camera_source_diagnosis_not_exclusive"];
  camera_first_frame_probe_status?: RobotControlLiveClosureSummary["camera_first_frame_probe_status"];
  camera_first_frame_failure_reason?: RobotControlLiveClosureSummary["camera_first_frame_failure_reason"];
  camera_source_diagnosis_plain_hint?: RobotControlLiveClosureSummary["live_wysiwyg_camera_source_diagnosis_plain_hint"];
  camera_source_diagnosis_next_action_plain?: RobotControlLiveClosureSummary["live_wysiwyg_camera_source_diagnosis_next_action_plain"];
  camera_recovery_next_action_plain?: RobotControlLiveClosureSummary["camera_recovery_next_action_plain"];
  camera_recovery_sends_motion?: RobotControlLiveClosureSummary["camera_recovery_sends_motion"];
  camera_recovery_starts_map_runtime?: RobotControlLiveClosureSummary["camera_recovery_starts_map_runtime"];
  fixed_camera_probe_endpoint?: RobotControlLiveClosureSummary["fixed_camera_probe_endpoint"];
  fixed_camera_mjpeg_status_endpoint?: RobotControlLiveClosureSummary["fixed_camera_mjpeg_status_endpoint"];
  live_wysiwyg_camera_source_diagnosis_status?: RobotControlLiveClosureSummary["live_wysiwyg_camera_source_diagnosis_status"];
  live_wysiwyg_camera_source_diagnosis_plain_hint?: RobotControlLiveClosureSummary["live_wysiwyg_camera_source_diagnosis_plain_hint"];
  live_wysiwyg_camera_source_diagnosis_next_action_plain?: RobotControlLiveClosureSummary["live_wysiwyg_camera_source_diagnosis_next_action_plain"];
  live_wysiwyg_camera_source_diagnosis_not_exclusive?: RobotControlLiveClosureSummary["live_wysiwyg_camera_source_diagnosis_not_exclusive"];
  live_wysiwyg_camera_shared_preview_client_count?: RobotControlLiveClosureSummary["live_wysiwyg_camera_shared_preview_client_count"];
  live_wysiwyg_camera_shared_preview_upstream_active?: RobotControlLiveClosureSummary["live_wysiwyg_camera_shared_preview_upstream_active"];
  live_wysiwyg_camera_shared_preview_exclusive_camera_claim?: RobotControlLiveClosureSummary["live_wysiwyg_camera_shared_preview_exclusive_camera_claim"];
  live_wysiwyg_camera_shared_preview_everyone_can_join?: RobotControlLiveClosureSummary["live_wysiwyg_camera_shared_preview_everyone_can_join"];
  live_wysiwyg_camera_shared_preview_current_frame_visible?: RobotControlLiveClosureSummary["live_wysiwyg_camera_shared_preview_current_frame_visible"];
  live_wysiwyg_camera_shared_preview_gap_plain?: RobotControlLiveClosureSummary["live_wysiwyg_camera_shared_preview_gap_plain"];
  camera_shared_preview_endpoint?: "/api/robot-control/camera/mjpeg";
  camera_shared_preview_status_endpoint?: RobotControlLiveClosureSummary["fixed_camera_mjpeg_status_endpoint"];
  camera_shared_preview_single_upstream?: true;
  camera_shared_preview_auto_joins?: true;
  camera_shared_preview_everyone_can_join?: RobotControlLiveClosureSummary["camera_shared_preview_everyone_can_join"];
  camera_shared_preview_current_frame_visible?: RobotControlLiveClosureSummary["camera_shared_preview_current_frame_visible"];
  camera_shared_preview_gap_plain?: RobotControlLiveClosureSummary["camera_shared_preview_gap_plain"];
  camera_shared_preview_readback_only?: true;
  camera_shared_preview_starts_camera_exclusive_capture?: false;
  camera_shared_preview_sends_motion?: false;
  camera_shared_preview_starts_nav2?: false;
  camera_shared_preview_starts_manual?: false;
  camera_shared_preview_starts_keyboard?: false;
  camera_shared_preview_starts_free_roam?: false;
  camera_shared_preview_starts_map_runtime?: false;
  camera_shared_preview_submits_delivery?: false;
  camera_shared_preview_stops_motion?: false;
  camera_shared_preview_shared_capture?: RobotControlSummaryResponse["readback_summary"]["camera"]["shared_preview_shared_capture"];
  camera_shared_preview_exclusive_camera_claim?: RobotControlSummaryResponse["readback_summary"]["camera"]["shared_preview_exclusive_camera_claim"];
  camera_shared_preview_contract?: RobotControlSummaryResponse["readback_summary"]["camera"]["shared_preview_contract"];
  camera_shared_preview_multi_viewer_status?: RobotControlSummaryResponse["readback_summary"]["camera"]["shared_preview_multi_viewer_status"];
  camera_shared_preview_multi_viewer_plain?: RobotControlSummaryResponse["readback_summary"]["camera"]["shared_preview_multi_viewer_plain"];
  camera_shared_preview_access_plain?: RobotControlSummaryResponse["readback_summary"]["camera"]["shared_preview_access_plain"];
  camera_shared_preview_realtime_plain?: RobotControlSummaryResponse["readback_summary"]["camera"]["shared_preview_realtime_plain"];
  camera_wysiwyg_recovery_status?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_status"];
  camera_wysiwyg_recovery_next_action_plain?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_next_action_plain"];
  camera_wysiwyg_recovery_sequence?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sequence"];
  camera_wysiwyg_recovery_sequence_labels?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sequence_labels"];
  live_wysiwyg_camera_recovery_status?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_status"];
  live_wysiwyg_camera_recovery_next_action_plain?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_next_action_plain"];
  live_wysiwyg_camera_recovery_sequence?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sequence"];
  live_wysiwyg_camera_recovery_sequence_labels?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sequence_labels"];
  live_wysiwyg_camera_recovery_sends_motion?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sends_motion"];
  camera_wysiwyg_recovery_readback_endpoint?: RobotControlLiveClosureSummary["fixed_camera_probe_endpoint"];
  camera_wysiwyg_recovery_probe_endpoint?: RobotControlLiveClosureSummary["fixed_camera_probe_endpoint"];
  camera_wysiwyg_recovery_status_endpoint?: RobotControlLiveClosureSummary["fixed_camera_mjpeg_status_endpoint"];
  camera_wysiwyg_recovery_summary_endpoint?: RobotControlLiveClosureSummary["fixed_objective_audit_summary_endpoint"];
  camera_wysiwyg_recovery_readback_endpoints?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sequence"];
  camera_wysiwyg_recovery_readback_sequence_labels?: RobotControlLiveClosureSummary["live_wysiwyg_camera_recovery_sequence_labels"];
  camera_wysiwyg_recovery_requires_hardware_action?: RobotControlLiveClosureSummary["camera_hardware_action_required"];
  camera_wysiwyg_recovery_hardware_action_label?: RobotControlLiveClosureSummary["camera_hardware_action_label"];
  camera_wysiwyg_recovery_requires_usb_fix?: RobotControlLiveClosureSummary["camera_hardware_action_required"];
  camera_wysiwyg_recovery_blocks_mapping_start?: RobotControlLiveClosureSummary["camera_blocks_mapping_start"];
  camera_wysiwyg_recovery_blocks_free_move?: RobotControlLiveClosureSummary["camera_blocks_free_move"];
  camera_wysiwyg_recovery_sends_motion?: RobotControlLiveClosureSummary["camera_recovery_sends_motion"];
  camera_wysiwyg_recovery_starts_nav2?: false;
  camera_wysiwyg_recovery_starts_manual?: false;
  camera_wysiwyg_recovery_starts_keyboard?: false;
  camera_wysiwyg_recovery_starts_free_roam?: false;
  camera_wysiwyg_recovery_starts_map_runtime?: RobotControlLiveClosureSummary["camera_recovery_starts_map_runtime"];
  camera_wysiwyg_recovery_submits_delivery?: false;
  camera_wysiwyg_recovery_stops_motion?: false;
  camera_wysiwyg_recovery_source_diagnosis_status?: RobotControlLiveClosureSummary["camera_source_diagnosis_status"];
  camera_wysiwyg_recovery_source_not_exclusive?: RobotControlLiveClosureSummary["camera_source_diagnosis_not_exclusive"];
  camera_wysiwyg_recovery_shared_preview_single_upstream?: true;
  mapping_unblock_camera_recovery_next_action_plain?: RobotControlLiveClosureSummary["mapping_unblock_camera_recovery_next_action_plain"];
  mapping_unblock_camera_recovery_sequence?: RobotControlLiveClosureSummary["mapping_unblock_camera_recovery_sequence"];
  mapping_unblock_camera_recovery_sequence_labels?: RobotControlLiveClosureSummary["mapping_unblock_camera_recovery_sequence_labels"];
  mapping_unblock_camera_recovery_sends_motion?: RobotControlLiveClosureSummary["mapping_unblock_camera_recovery_sends_motion"];
  fixed_mapping_unblock_camera_probe_endpoint?: RobotControlLiveClosureSummary["fixed_mapping_unblock_camera_probe_endpoint"];
  fixed_mapping_unblock_camera_mjpeg_status_endpoint?: RobotControlLiveClosureSummary["fixed_mapping_unblock_camera_mjpeg_status_endpoint"];
  fixed_mapping_unblock_summary_endpoint?: RobotControlLiveClosureSummary["fixed_mapping_unblock_summary_endpoint"];
  radar_visible?: RobotControlLiveClosureSummary["radar_map_points_visible"];
  radar_points_visible?: RobotControlLiveClosureSummary["radar_map_points_visible"];
  radar_ready?: RobotControlLiveClosureSummary["mapping_lidar_fresh_readback_ready"];
  radar_fresh?: RobotControlLiveClosureSummary["mapping_lidar_fresh_readback_ready"];
  radar_map_ready?: RobotControlLiveClosureSummary["radar_map_points_visible"];
  radar_map_points_visible?: RobotControlLiveClosureSummary["radar_map_points_visible"];
  live_wysiwyg_radar_map_overlay_status?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_overlay_status"];
  live_wysiwyg_radar_map_current_point_count?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_current_point_count"];
  live_wysiwyg_radar_map_source_point_count?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_source_point_count"];
  live_wysiwyg_radar_map_stale_source_points_suppressed?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_stale_source_points_suppressed"];
  live_wysiwyg_radar_map_primary_blocked_reason?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_primary_blocked_reason"];
  live_wysiwyg_radar_map_current_vs_source_plain?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_current_vs_source_plain"];
  live_wysiwyg_radar_map_refresh_next_action_plain?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_refresh_next_action_plain"];
  live_wysiwyg_radar_map_refresh_sequence?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_refresh_sequence"];
  live_wysiwyg_radar_map_refresh_sequence_labels?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_refresh_sequence_labels"];
  radar_overlay_status?: RobotControlLiveClosureSummary["radar_overlay_status"];
  radar_overlay_current_point_count?: RobotControlLiveClosureSummary["radar_overlay_current_point_count"];
  radar_overlay_source_point_count?: RobotControlLiveClosureSummary["radar_overlay_source_point_count"];
  radar_overlay_primary_blocked_reason?: RobotControlLiveClosureSummary["radar_overlay_primary_blocked_reason"];
  radar_overlay_current_vs_source_plain?: RobotControlLiveClosureSummary["radar_overlay_current_vs_source_plain"];
  radar_overlay_next_action_plain?: RobotControlLiveClosureSummary["radar_overlay_refresh_next_action_plain"];
  radar_overlay_refresh_next_action_plain?: RobotControlLiveClosureSummary["radar_overlay_refresh_next_action_plain"];
  radar_overlay_needs_refresh?: RobotControlLiveClosureSummary["radar_overlay_needs_refresh"];
  radar_overlay_blocks_wysiwyg?: RobotControlLiveClosureSummary["radar_overlay_blocks_wysiwyg"];
  radar_overlay_blocks_free_move?: RobotControlLiveClosureSummary["radar_overlay_blocks_free_move"];
  radar_overlay_wysiwyg_complete?: boolean;
  radar_overlay_readback_endpoint?: RobotControlLiveClosureSummary["fixed_radar_overlay_refresh_endpoint"];
  radar_overlay_refresh_endpoint?: RobotControlLiveClosureSummary["fixed_radar_overlay_refresh_endpoint"];
  radar_overlay_status_endpoint?: RobotControlLiveClosureSummary["fixed_live_wysiwyg_radar_status_endpoint"];
  radar_overlay_preview_endpoint?: RobotControlLiveClosureSummary["fixed_radar_overlay_map_preview_endpoint"];
  radar_overlay_summary_endpoint?: RobotControlLiveClosureSummary["fixed_objective_audit_summary_endpoint"];
  radar_overlay_refresh_sequence?: RobotControlLiveClosureSummary["radar_overlay_recovery_sequence"];
  radar_overlay_refresh_sequence_labels?: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_refresh_sequence_labels"];
  radar_overlay_recovery_sequence?: RobotControlLiveClosureSummary["radar_overlay_recovery_sequence"];
  fixed_radar_overlay_refresh_endpoint?: RobotControlLiveClosureSummary["fixed_radar_overlay_refresh_endpoint"];
  fixed_radar_overlay_map_preview_endpoint?: RobotControlLiveClosureSummary["fixed_radar_overlay_map_preview_endpoint"];
  radar_overlay_refresh_sends_motion?: RobotControlLiveClosureSummary["radar_overlay_refresh_sends_motion"];
  radar_overlay_refresh_starts_radar_lifecycle?: RobotControlLiveClosureSummary["radar_overlay_refresh_starts_radar_lifecycle"];
  radar_overlay_refresh_starts_nav2?: RobotControlLiveClosureSummary["radar_overlay_refresh_starts_nav2"];
  radar_overlay_refresh_starts_manual?: RobotControlLiveClosureSummary["radar_overlay_refresh_starts_manual"];
  radar_overlay_refresh_starts_keyboard?: RobotControlLiveClosureSummary["radar_overlay_refresh_starts_keyboard"];
  radar_overlay_refresh_starts_free_roam?: RobotControlLiveClosureSummary["radar_overlay_refresh_starts_free_roam"];
  radar_overlay_refresh_starts_map_runtime?: RobotControlLiveClosureSummary["radar_overlay_refresh_starts_map_runtime"];
  radar_overlay_refresh_submits_delivery?: RobotControlLiveClosureSummary["radar_overlay_refresh_submits_delivery"];
  radar_overlay_refresh_stops_motion?: RobotControlLiveClosureSummary["radar_overlay_refresh_stops_motion"];
  fixed_radar_start_endpoint?: RobotControlLiveClosureSummary["fixed_radar_start_endpoint"];
  fixed_radar_stop_endpoint?: RobotControlLiveClosureSummary["fixed_radar_stop_endpoint"];
  radar_start_map_wysiwyg_required?: RobotControlLiveClosureSummary["radar_start_map_wysiwyg_required"];
  radar_start_map_wysiwyg_sequence?: RobotControlLiveClosureSummary["radar_start_map_wysiwyg_sequence"];
  radar_start_map_wysiwyg_sequence_labels?: RobotControlLiveClosureSummary["radar_start_map_wysiwyg_sequence_labels"];
  radar_start_refreshes_scan_proof?: RobotControlLiveClosureSummary["radar_start_refreshes_scan_proof"];
  radar_start_refreshes_radar_status?: RobotControlLiveClosureSummary["radar_start_refreshes_radar_status"];
  radar_start_refreshes_map_preview?: RobotControlLiveClosureSummary["radar_start_refreshes_map_preview"];
  radar_start_refreshes_summary?: RobotControlLiveClosureSummary["radar_start_refreshes_summary"];
  radar_start_sends_motion?: RobotControlLiveClosureSummary["radar_start_sends_motion"];
  radar_start_starts_nav2?: RobotControlLiveClosureSummary["radar_start_starts_nav2"];
  radar_start_starts_manual?: RobotControlLiveClosureSummary["radar_start_starts_manual"];
  radar_start_starts_keyboard?: RobotControlLiveClosureSummary["radar_start_starts_keyboard"];
  radar_start_starts_free_roam?: RobotControlLiveClosureSummary["radar_start_starts_free_roam"];
  radar_start_starts_map_runtime?: RobotControlLiveClosureSummary["radar_start_starts_map_runtime"];
  radar_start_submits_delivery?: RobotControlLiveClosureSummary["radar_start_submits_delivery"];
  radar_start_stops_motion?: RobotControlLiveClosureSummary["radar_start_stops_motion"];
  keyboard_ready?: RobotControlLiveClosureSummary["keyboard_ready"];
  keyboard_continuous_ready?: RobotControlLiveClosureSummary["keyboard_continuous_ready"];
  keyboard_wheel_lr_nonzero?: boolean;
  keyboard_stop_after_release?: boolean;
  keyboard_continuous_motion_verified?: RobotControlLiveClosureSummary["keyboard_continuous_motion_verified"];
  keyboard_continuous_minimal_precheck_safety_only?: RobotControlLiveClosureSummary["keyboard_continuous_minimal_precheck_safety_only"];
  keyboard_continuous_safety_confirm_required?: RobotControlLiveClosureSummary["keyboard_continuous_safety_confirm_required"];
  keyboard_continuous_enable_sends_motion?: RobotControlLiveClosureSummary["keyboard_continuous_enable_sends_motion"];
  keyboard_continuous_hold_to_move_required?: RobotControlLiveClosureSummary["keyboard_continuous_hold_to_move_required"];
  keyboard_continuous_pulse_interval_ms?: RobotControlLiveClosureSummary["keyboard_continuous_pulse_interval_ms"];
  keyboard_continuous_pulse_duration_ms?: RobotControlLiveClosureSummary["keyboard_continuous_pulse_duration_ms"];
  keyboard_continuous_stop_triggers?: RobotControlLiveClosureSummary["keyboard_continuous_stop_triggers"];
  keyboard_continuous_wheel_feedback_acceptance?: RobotControlLiveClosureSummary["keyboard_continuous_wheel_feedback_acceptance"];
  keyboard_safety_confirm_required?: RobotControlLiveClosureSummary["keyboard_safety_confirm_required"];
  keyboard_enable_sends_motion?: RobotControlLiveClosureSummary["keyboard_enable_sends_motion"];
  keyboard_hold_to_move_required?: RobotControlLiveClosureSummary["keyboard_hold_to_move_required"];
  keyboard_pulse_interval_ms?: RobotControlLiveClosureSummary["keyboard_pulse_interval_ms"];
  keyboard_pulse_duration_ms?: RobotControlLiveClosureSummary["keyboard_pulse_duration_ms"];
  keyboard_stop_triggers?: RobotControlLiveClosureSummary["keyboard_stop_triggers"];
  keyboard_acceptance_plain?: RobotControlLiveClosureSummary["keyboard_acceptance_plain"];
  keyboard_manual_endpoint?: RobotControlLiveClosureSummary["keyboard_manual_endpoint"];
  keyboard_stop_endpoint?: RobotControlLiveClosureSummary["keyboard_stop_endpoint"];
  keyboard_feedback_readback_endpoint?: RobotControlLiveClosureSummary["keyboard_feedback_readback_endpoint"];
  keyboard_summary_endpoint?: RobotControlLiveClosureSummary["keyboard_summary_endpoint"];
  fixed_keyboard_manual_endpoint?: RobotControlLiveClosureSummary["fixed_keyboard_manual_endpoint"];
  fixed_keyboard_stop_endpoint?: RobotControlLiveClosureSummary["fixed_keyboard_stop_endpoint"];
  fixed_keyboard_feedback_readback_endpoint?: RobotControlLiveClosureSummary["fixed_keyboard_feedback_readback_endpoint"];
  fixed_keyboard_summary_endpoint?: RobotControlLiveClosureSummary["fixed_keyboard_summary_endpoint"];
  keyboard_post_hold_readback_endpoints?: Array<
    RobotControlLiveClosureSummary["fixed_keyboard_feedback_readback_endpoint"] | RobotControlLiveClosureSummary["fixed_keyboard_summary_endpoint"]
  >;
  keyboard_post_hold_readback_sequence_labels?: string[];
  keyboard_post_hold_feedback_readback_required?: RobotControlLiveClosureSummary["keyboard_continuous_post_hold_feedback_readback_required"];
  keyboard_post_hold_summary_refresh_required?: RobotControlLiveClosureSummary["keyboard_continuous_post_hold_summary_refresh_required"];
  keyboard_post_hold_readback_sends_motion?: false;
  keyboard_post_hold_readback_starts_nav2?: false;
  keyboard_post_hold_readback_starts_manual?: false;
  keyboard_post_hold_readback_starts_keyboard?: false;
  keyboard_post_hold_readback_starts_free_roam?: false;
  keyboard_post_hold_readback_starts_map_runtime?: false;
  keyboard_post_hold_readback_submits_delivery?: false;
  keyboard_post_hold_readback_stops_motion?: false;
  keyboard_continuous_post_hold_feedback_readback_required?: RobotControlLiveClosureSummary["keyboard_continuous_post_hold_feedback_readback_required"];
  keyboard_continuous_post_hold_summary_refresh_required?: RobotControlLiveClosureSummary["keyboard_continuous_post_hold_summary_refresh_required"];
  free_move_start_ready?: RobotControlLiveClosureSummary["free_move_start_ready"];
  free_move_ready?: RobotControlLiveClosureSummary["free_move_start_ready"];
  free_move_running?: RobotControlLiveClosureSummary["free_roam_motion_ready"];
  free_move_complete?: boolean;
  free_roam_start_ready?: RobotControlLiveClosureSummary["free_roam_start_ready"];
  free_roam_ready?: RobotControlLiveClosureSummary["free_roam_ready"];
  free_roam_motion_start_ready?: RobotControlLiveClosureSummary["free_roam_motion_start_ready"];
  free_roam_motion_ready?: RobotControlLiveClosureSummary["free_roam_motion_ready"];
  free_move_minimal_precheck_safety_only?: RobotControlLiveClosureSummary["free_move_minimal_precheck_safety_only"];
  free_move_safety_confirm_required?: RobotControlLiveClosureSummary["free_move_safety_confirm_required"];
  free_move_camera_preflight_required?: RobotControlLiveClosureSummary["free_move_camera_preflight_required"];
  free_move_radar_preflight_required?: RobotControlLiveClosureSummary["free_move_radar_preflight_required"];
  free_move_without_camera_allowed?: RobotControlLiveClosureSummary["free_move_without_camera_allowed"];
  free_roam_motion_without_radar_allowed?: RobotControlLiveClosureSummary["free_roam_motion_without_radar_allowed"];
  free_move_blocked_by_camera_wysiwyg?: RobotControlLiveClosureSummary["free_move_blocked_by_camera_wysiwyg"];
  free_move_blocked_by_radar_wysiwyg?: RobotControlLiveClosureSummary["free_move_blocked_by_radar_wysiwyg"];
  fixed_free_roam_start_endpoint?: RobotControlLiveClosureSummary["fixed_free_roam_start_endpoint"];
  fixed_free_roam_stop_endpoint?: RobotControlLiveClosureSummary["fixed_free_roam_stop_endpoint"];
  fixed_free_roam_latest_endpoint?: RobotControlLiveClosureSummary["fixed_free_roam_latest_endpoint"];
  mapping_start_ready?: RobotControlLiveClosureSummary["mapping_start_ready"];
  mapping_start_missing_reasons?: RobotControlLiveClosureSummary["mapping_start_missing_reasons"];
  mapping_start_missing_evidence?: RobotControlLiveClosureSummary["mapping_start_missing_reasons"];
  mapping_start_only_camera_missing?: boolean;
  mapping_acceptance_ready?: RobotControlLiveClosureSummary["free_roam_mapping_ready"];
  mapping_acceptance_missing_reasons?: RobotControlLiveClosureSummary["mapping_acceptance_missing_reasons"];
  mapping_start_requires_camera_first_frame?: RobotControlLiveClosureSummary["mapping_start_requires_camera_first_frame"];
  mapping_start_requires_lidar_fresh?: RobotControlLiveClosureSummary["mapping_start_requires_lidar_fresh"];
  mapping_start_unblock_plain?: RobotControlLiveClosureSummary["mapping_start_unblock_plain"];
  mapping_camera_blocks_start?: RobotControlLiveClosureSummary["mapping_camera_blocks_start"];
  mapping_lidar_blocks_start?: RobotControlLiveClosureSummary["mapping_lidar_blocks_start"];
  mapping_lidar_fresh_readback_ready?: RobotControlLiveClosureSummary["mapping_lidar_fresh_readback_ready"];
  mapping_lidar_fresh_gate_conflict?: RobotControlLiveClosureSummary["mapping_lidar_fresh_gate_conflict"];
  mapping_lidar_fresh_gate_status?: RobotControlLiveClosureSummary["mapping_lidar_fresh_gate_status"];
  mapping_lidar_fresh_next_action_plain?: RobotControlLiveClosureSummary["mapping_lidar_fresh_next_action_plain"];
  mapping_lidar_fresh_refresh_sequence?: RobotControlLiveClosureSummary["mapping_lidar_fresh_refresh_sequence"];
  mapping_lidar_fresh_refresh_sequence_labels?: RobotControlLiveClosureSummary["mapping_lidar_fresh_refresh_sequence_labels"];
  mapping_lidar_fresh_refresh_sends_motion?: RobotControlLiveClosureSummary["mapping_lidar_fresh_refresh_sends_motion"];
  mapping_lidar_fresh_refresh_starts_radar_lifecycle?: RobotControlLiveClosureSummary["mapping_lidar_fresh_refresh_starts_radar_lifecycle"];
  mapping_lidar_fresh_blocks_free_move?: RobotControlLiveClosureSummary["mapping_lidar_fresh_blocks_free_move"];
  mapping_unblock_allows_free_move?: RobotControlLiveClosureSummary["mapping_unblock_allows_free_move"];
  fixed_mapping_start_endpoint?: RobotControlLiveClosureSummary["fixed_mapping_start_endpoint"];
  fixed_mapping_preview_endpoint?: RobotControlLiveClosureSummary["fixed_mapping_preview_endpoint"];
  free_roam_mapping_start_ready?: RobotControlLiveClosureSummary["free_roam_mapping_start_ready"];
  free_roam_mapping_start_missing_reasons?: RobotControlLiveClosureSummary["free_roam_mapping_start_missing_reasons"];
  free_roam_mapping_ready?: RobotControlLiveClosureSummary["free_roam_mapping_ready"];
  free_roam_mapping_missing_reasons?: RobotControlLiveClosureSummary["free_roam_mapping_missing_reasons"];
  camera_summary?: RobotControlSummaryResponse["readback_summary"]["camera"];
  map_summary?: RobotControlSummaryResponse["readback_summary"]["map"];
  radar_summary?: RobotControlSummaryResponse["readback_summary"]["radar"];
  nav2_summary?: RobotControlSummaryResponse["readback_summary"]["nav2"];
  keyboard_summary?: RobotControlSummaryResponse["readback_summary"]["keyboard"];
  keyboard_control_summary?: RobotControlSummaryResponse["readback_summary"]["keyboard_control"];
  keyboard_teleop_summary?: RobotControlSummaryResponse["readback_summary"]["keyboard_teleop"];
  free_roam_summary?: RobotControlSummaryResponse["readback_summary"]["free_roam"];
  readback_summary: {
    camera: {
      status: string;
      devices_status: string;
      devices_effective_status?: string;
      devices_endpoint_count?: string;
      devices_health_candidate_count?: string;
      devices_plain_hint?: string;
      preview_status: RobotControlPreviewStatus;
      plain_hint: string;
      preview_plain_hint: string;
      preview_next_action: string;
      preview_next_action_plain: string;
      preview_visible_status: string;
      preview_visible_plain: string;
      camera_wysiwyg_status_plain: string;
      camera_wysiwyg_next_action_plain: string;
      shared_preview_client_count: string;
      viewer_count: string;
      shared_preview_upstream_active: string;
      upstream_connected: string;
      shared_preview_content_type_loaded: string;
      shared_preview_cached_frame_loaded: string;
      has_recent_frame: string;
      shared_preview_cached_frame_age_ms: string;
      shared_preview_access_plain: string;
      shared_preview_realtime_plain: string;
      shared_preview_shared_capture: string;
      shared_preview_exclusive_camera_claim: string;
      shared_preview_contract: string;
      shared_preview_multi_viewer_status: string;
      shared_preview_multi_viewer_plain: string;
      shared_preview_last_failure_reason: string;
      shared_preview_last_remote_http_status: string;
      shared_preview_last_failure_at_ms: string;
      video_source: string;
      video_source_mode: string;
      selected_path: string;
      selected_name: string;
      selected_is_uvc_or_usb: string;
      selected_formats_summary: string;
      selected_role: string;
      selected_sibling_video_nodes_summary: string;
      selected_sibling_video_node_count: string;
      source_readiness: string;
      source_failure_reason: string;
      source_diagnosis_status: string;
      source_diagnosis_plain_hint: string;
      source_diagnosis_next_action: string;
      source_diagnosis_next_action_plain: string;
      source_diagnosis_not_exclusive: string;
      uvc_kernel_diagnostics_status?: string;
      uvc_kernel_diagnostics_plain_hint?: string;
      uvc_kernel_diagnostics_next_action?: string;
      uvc_kernel_diagnostics_transport_error_count?: string;
      uvc_kernel_diagnostics_latest_transport_error?: string;
      uvc_usb_topology_status?: string;
      uvc_usb_topology_plain_hint?: string;
      uvc_usb_topology_next_action?: string;
      uvc_usb_topology_video_usb_speed?: string;
      uvc_usb_topology_kernel_usb_address?: string;
      uvc_usb_topology_video_interface_count?: string;
      source_usage_status: string;
      source_usage_owner_count: string;
      source_usage_scope?: "free" | "camera_service_self" | "external_holder" | "unknown";
      source_usage_not_exclusive?: string;
      source_usage_summary: string;
      active_peer_count: string;
      last_offer_error: string;
      last_offer_failure_reason: string;
      last_offer_format_attempts_summary: string;
      first_frame_probe_status: string;
      first_frame_probe_failure_reason: string;
      first_frame_probe_open_ok: string;
      first_frame_probe_read_ok: string;
      first_frame_probe_visible_content_proven: string;
      first_frame_probe_backend_smoke_status: string;
      first_frame_probe_backend_frame_observed: string;
      first_frame_probe_backend_attempts: string;
      first_frame_probe_streamon_io_error_observed: string;
      first_frame_probe_streamon_io_error_count: string;
      first_frame_probe_latest_streamon_io_error: string;
      first_frame_probe_fallback_attempts_summary: string;
      first_frame_probe_checked_at_ms: string;
    };
    lidar: {
      status: string;
      latest_scan_proof_status: string;
      latest_raw_packet_proof_status: string;
      latest_scan_proof_result_status?: string;
      raw_packet_once_observed?: string;
      scan_once_observed?: string;
      scan_hz_observed?: string;
      radar_scan_observation_status?: string;
      radar_scan_observation_missing_reasons?: string;
      radar_map_overlay_readiness_status?: string;
      radar_map_overlay_next_action_plain?: string;
      continuous_scan_status: string;
      lifecycle_running: string;
      lifecycle_state: string;
      continuous_window_observed: string;
      continuity_window_status: string;
      latest_scan_proof_fresh: string;
      driver_diagnostics_status?: string;
      driver_diagnostics_next_action_plain?: string;
      driver_serial_bytes_read_total?: string;
      driver_serial_packet_count_total?: string;
      driver_serial_empty_read_count?: string;
      driver_published_scan_count?: string;
      runtime_scan_status: string;
      runtime_lidar_min_distance_m: string;
      runtime_lidar_age_s: string;
      runtime_scan_source: string;
      scan_preview_point_count: string;
      scan_preview_source_point_count: string;
      scan_preview_frame_id: string;
      radar_start_configured: string;
    };
    radar: {
      status: string;
      plain_hint: string;
      next_action_plain: string;
      radar_status_plain: string;
      radar_next_action_plain: string;
      lifecycle_running: string;
      lifecycle_state: string;
      continuous_scan_status: string;
      latest_scan_proof_fresh: string;
      runtime_scan_status: string;
      driver_diagnostics_status?: string;
      driver_diagnostics_next_action_plain?: string;
      driver_serial_bytes_read_total?: string;
      driver_serial_packet_count_total?: string;
      driver_serial_empty_read_count?: string;
      driver_published_scan_count?: string;
      radar_scan_observation_status?: string;
      radar_scan_observation_missing_reasons?: string;
      radar_map_overlay_readiness_status?: string;
      radar_map_overlay_next_action_plain?: string;
      scan_point_count: string;
      scan_preview_point_count: string;
      scan_preview_source_point_count: string;
      scan_preview_frame_id: string;
      radar_overlay_status: string;
      radar_overlay_point_count: string;
      radar_overlay_source_point_count: string;
      radar_overlay_frame_id: string;
      radar_overlay_source_frame_id: string;
      radar_overlay_wysiwyg_status_plain: string;
      radar_overlay_wysiwyg_next_action_plain: string;
      radar_overlay_blocked_reasons: string;
      radar_overlay_blocked_reason_labels: string;
      map_marker_point_count: string;
      map_marker_source_point_count: string;
      map_marker_frame_id: string;
      map_marker_source_frame_id: string;
    };
    base: {
      status: string;
      latest_feedback_status: string;
      current_feedback_read_status: string;
      current_feedback_failure_reason: string;
      feedback_ack_status: string;
      latest_t1001_observed_count: string;
      wheel_feedback_lr_nonzero_proven: string;
      wheel_feedback_nonzero_observed: string;
      wheel_feedback_latest_left_speed: string;
      wheel_feedback_latest_right_speed: string;
      wheel_left_speed: string;
      wheel_right_speed: string;
      wheel_feedback_latest_raw_left?: string;
      wheel_feedback_latest_raw_right?: string;
      wheel_raw_left: string;
      wheel_raw_right: string;
      wheel_feedback_latest_nonzero_left_speed: string;
      wheel_feedback_latest_nonzero_right_speed: string;
      feedback_voltage_v: string;
      feedback_link_status: string;
    };
    map: {
      status: string;
      map_once_observed: string;
      map_quality_status: string;
      map_free_cell_count: string;
      map_usable_for_navigation: string;
      plain_hint: string;
      next_action_plain: string;
      map_current_visible: string;
      path_current_visible: string;
      radar_overlay_current_visible: string;
      map_next_action_plain: string;
      map_wysiwyg_status_plain: string;
      map_wysiwyg_next_action_plain: string;
      path_preview_status: string;
      path_preview_point_count: string;
      path_preview_frame_id: string;
      path_preview_next_action_plain: string;
      path_wysiwyg_status_plain: string;
      path_wysiwyg_next_action_plain: string;
      robot_pose_status: string;
      radar_overlay_status: string;
      radar_overlay_plain_hint: string;
      radar_overlay_wysiwyg_status_plain: string;
      radar_overlay_wysiwyg_next_action_plain: string;
      radar_overlay_next_action: string;
      radar_overlay_next_action_plain: string;
      radar_overlay_point_count: string;
      radar_overlay_source_point_count: string;
      radar_overlay_refresh_required: string;
      radar_overlay_stale_source_points_suppressed: string;
      radar_overlay_primary_blocked_reason: string;
      radar_overlay_current_vs_source_plain: string;
      radar_overlay_frame_id: string;
      radar_overlay_source_frame_id: string;
      radar_overlay_blocked_reasons: string;
      radar_overlay_blocked_reason_labels: string;
      radar_overlay_scan_preview_point_count: string;
      radar_overlay_scan_preview_source_point_count: string;
      radar_overlay_scan_preview_frame_id: string;
      radar_overlay_robot_pose_status: string;
    };
    localization: {
      status: string;
      amcl_pose_observed: string;
      localization_tf_observed: string;
      robot_pose_status: string;
      robot_pose_frame_id: string;
      robot_pose_x: string;
      robot_pose_y: string;
    };
    nav2: {
      status: string;
      plain_hint: string;
      nav2_status: string;
      nav2_stack_running: string;
      nav2_stack_lifecycle_state: string;
      current_blocker_reasons: string;
      current_blocker_labels: string;
      planner_server_active: string;
      controller_server_active: string;
      controller_server_requested: string;
      map_consumed: string;
      path_generation_attempted: string;
      path_generation_service_available: string;
      path_generation_service_name: string;
      path_generated: string;
      path_generation_succeeded: string;
      path_point_count: string;
      path_preview_point_count: string;
      path_preview_frame_id: string;
      execution_status_plain: string;
      next_action_plain: string;
      route_execution_readiness_plain: string;
      route_execution_precheck_plain: string;
      goal_execution_wheel_raw_lr_status_plain: string;
      goal_execution_wheel_raw_lr_next_action_plain: string;
      goal_execution_next_mode_plain: string;
      goal_execution_mode_rerun_plain: string;
      goal_execution_status: string;
      goal_execution_proven: string;
      goal_execution_hil_pass: string;
      goal_execution_result_status: string;
      goal_execution_evidence_ref: string;
      goal_execution_robot_control_executed: string;
      goal_execution_feedback_sample_count: string;
      goal_execution_base_command_mode: string;
      next_execution_base_command_mode: string;
      goal_execution_mode_rerun_status: string;
      goal_execution_base_command_nonzero_observed: string;
      goal_execution_base_command_nonzero_count: string;
      goal_execution_base_command_latest_nonzero_mode: string;
      goal_execution_base_command_mode_counts: string;
      goal_execution_base_feedback_sample_count: string;
      goal_execution_base_feedback_nonzero_sample_count: string;
      goal_execution_base_feedback_lr_nonzero_proven: string;
      goal_execution_base_feedback_imu_attitude_delta_observed: string;
      goal_execution_base_feedback_imu_roll_delta: string;
      goal_execution_base_feedback_imu_pitch_delta: string;
      goal_execution_base_feedback_latest_left_speed: string;
      goal_execution_base_feedback_latest_right_speed: string;
      goal_execution_base_feedback_latest_raw_left: string;
      goal_execution_base_feedback_latest_raw_right: string;
      goal_execution_readback_publishes_cmd_vel: string;
      goal_execution_managed_runtime_requested: string;
      goal_execution_managed_runtime_started: string;
      goal_execution_managed_runtime_lifecycle_ready_ok: string;
      goal_execution_managed_runtime_cleanup_ok: string;
      goal_execution_sends_base_motion_commands: string;
      goal_execution_uses_base_uart: string;
      goal_execution_goal_frame_id: string;
      goal_execution_goal_x: string;
      goal_execution_goal_y: string;
      goal_execution_generated_at_ms: string;
      goal_execution_response_generated_at_ms: string;
    };
    keyboard: RobotControlKeyboardReadbackSummary;
    keyboard_control: RobotControlKeyboardReadbackSummary;
    keyboard_teleop: RobotControlKeyboardReadbackSummary;
    free_roam: {
      status: string;
      runtime_status: string;
      decision_state: string;
      decision_reason: string;
      stop_required: string;
      stop_request_pending: string;
      free_roam_stop_request_pending: string;
      start_will_clear_stop_request: string;
      start_clears_stop_request_not_blocking: string;
      motion_start_blocked_by_stop_request: string;
      stop_request_status_plain: string;
      artifact_only: string;
      cmd_vel_publish_enabled: string;
      start_ready: string;
      free_move_ready: string;
      free_move_start_ready: string;
      motion_start_ready: string;
      free_roam_motion_start_ready: string;
      free_move_without_camera_allowed: string;
      motion_without_radar_allowed: string;
      free_move_minimal_precheck_safety_only: string;
      free_move_safety_confirm_required: string;
      free_move_camera_preflight_required: string;
      free_move_radar_preflight_required: string;
      motion_ready: string;
      free_roam_motion_ready: string;
      mapping_start_ready: string;
      free_roam_mapping_start_ready: string;
      mapping_start_requires_camera_first_frame: string;
      mapping_start_requires_lidar_fresh: string;
      mapping_start_missing: string;
      mapping_readiness_ready: string;
      mapping_blocked_reasons: string;
      mapping_missing_reasons: string;
      free_roam_mapping_ready: string;
      free_roam_mapping_missing_reasons: string;
      mapping_ready: string;
      mapping_missing: string;
      plain_hint: string;
	      next_action_plain: string;
	      motion_readiness_plain: string;
	      motion_sensor_dependency_status?: string;
	      motion_sensor_dependency_plain?: string;
	      free_move_start_status_plain: string;
      motion_runtime_status_plain: string;
      mapping_acceptance_status_plain: string;
      mapping_start_readiness_plain: string;
      mapping_readiness_plain: string;
      motion_next_action_plain: string;
      mapping_start_next_action_plain: string;
      mapping_next_action_plain: string;
      runtime_artifact_proven: string;
      state_machine_observed: string;
      ros2_runtime_proven: string;
      gate_count: string;
    };
  };
  operator_hil_material_summary: RobotControlOperatorHilMaterialSummary;
  first_jog_readiness_summary: {
    status: "ready_for_first_jog" | "blocked_missing_visual_material" | "blocked_missing_basic_safety" | "not_loaded";
    basic_safety_ready: boolean;
    visual_material_ready: boolean;
    missing_fields: string[];
    next_action: "press_try_move" | "record_visual_material" | "complete_basic_safety_check" | "connect_robot_api";
  };
  safe_command_boundary: {
    manual_endpoint: "/api/base/manual";
    stop_endpoint: "/api/base/stop";
    cmd_vel_topic: "/cmd_vel";
    nav2_goal: "Nav2 NavigateToPose locked";
    nav2_goal_ready: boolean;
    nav2_goal_label: "路线读数已准备，等待地图画面确认" | "图上路线已显示，等待安全确认" | "图上路线和小车位置已显示，等待安全确认" | "图上路线未就绪" | "自动驾驶服务未启动" | "规划服务未就绪" | "控制服务未就绪" | "规划/控制服务未就绪";
    nav2_goal_blockers: string[];
    nav2_goal_wheel_feedback_status: string;
    nav2_goal_next_action: string;
    nav2_goal_next_action_plain: string;
    nav2_goal_minimal_precheck_plain: string;
    nav2_goal_precheck_plain: string;
    navigation_preflight_plain: string;
    nav2_goal_execution_mode_label: string;
    map_start: "map start locked";
    radar_start: "radar start locked";
    keyboard_control: "bounded repeating manual pulse gated";
    keyboard_control_mode: "bounded_repeating_manual_pulse";
    keyboard_manual_command_mode: "ros";
    keyboard_manual_proxy_endpoint: "/api/robot-control/base/manual";
    keyboard_stop_proxy_endpoint: "/api/robot-control/base/stop";
    keyboard_jog_interval_ms: number;
    keyboard_jog_duration_ms: number;
    keyboard_stop_triggers: string[];
    keyboard_hold_to_move_plain: string;
    keyboard_stop_triggers_plain: string;
    keyboard_pulse_timing_plain: string;
    keyboard_reuses_manual_gate: true;
    keyboard_control_start_ready: boolean;
    keyboard_control_status: "start_ready" | "armed" | "active" | "blocked";
    keyboard_control_label: "键盘手控（勾确认后可启用）";
    keyboard_control_next_action: string;
    keyboard_minimal_precheck_plain: string;
    keyboard_teleop_start_ready: boolean;
    keyboard_teleop_status: "start_ready" | "armed" | "active" | "blocked";
    keyboard_teleop_next_action_plain: string;
    free_roam_autonomy: "locked" | "start_ready" | "ready";
    free_roam_autonomy_start_ready: boolean;
    free_roam_motion_start_ready: boolean;
    free_roam_mapping_start_ready: boolean;
    free_roam_mapping_start_missing_reasons: string[];
    free_roam_mapping_ready: boolean;
    free_roam_mapping_missing_reasons: string[];
    free_roam_autonomy_label: "自动扫图（未开放）" | "自由移动（勾确认后可启动）" | "自由移动（运行中）" | "自动扫图";
    free_roam_autonomy_next_action: string;
    free_roam_motion_minimal_precheck_plain: string;
    free_roam_mapping_start_plain: string;
    free_roam_mapping_start_next_action: string;
    free_roam_mapping_acceptance_plain: string;
    free_roam_autonomy_policy: {
      mode: "free_move_requires_safety_confirm_stop_fallback";
      mapping_mode: "mapping_acceptance_requires_camera_and_fresh_radar";
      max_speed_mps: number;
      max_runtime_s: number;
      required_gates: string[];
      mapping_start_required_gates: string[];
      mapping_required_gates: string[];
    };
    free_roam_autonomy_gates: Array<{
      id: string;
      label: string;
      scope?: "free_move_start" | "mapping_acceptance" | "runtime_diagnostic";
      state: "ready" | "blocked" | "not_proven";
      evidence: string;
      next_action: string;
    }>;
    free_roam_autonomy_runtime: {
      status: "not_loaded" | "loaded";
      state: string;
      reason: string;
      stop_required: boolean;
      artifact_only: boolean;
      cmd_vel_publish_enabled: boolean;
      free_roam_mapping_start_missing_reasons?: string[];
      free_roam_mapping_missing_reasons?: string[];
    };
    map_click_goal: "map click goal locked";
    locked_reason: string;
    manual_motion_entry_status: "controlled_jog_requires_safety_confirmation_only";
    manual_motion_entry_label: "低速手控（勾安全确认即可）";
    allowed_directions: Array<"forward" | "back" | "left" | "right" | "stop">;
    non_stop_requires_confirm_hil_checklist: true;
    non_stop_requires_operator_report_preflight: boolean;
    operator_report_preflight_endpoint: "/api/operator/report";
    operator_report_preflight_required_fields: string[];
    speed_limit_mps: number;
    duration_limit_ms: number;
    hil_checklist: Array<{
      id: "operator_safety_confirmed";
      label: string;
    }>;
    command_dispatch_enabled: false;
    manual_control_enabled: false;
    navigate_goal_enabled: false;
    keyboard_control_enabled: false;
    robot_control_executed: false;
  };
  blocked_reasons: string[];
  not_proven: string[];
  safe_to_control: false;
  delivery_success: false;
  primary_actions_enabled: false;
}

export type RobotControlProofRefreshKind =
  | "radar_scan_proof_refresh"
  | "map_proof_refresh"
  | "nav2_no_motion_proof_refresh"
  | "localization_reset";
export type RobotControlProofRefreshProxyStatus = "refresh_forwarded" | "refresh_rejected" | "refresh_failed";

export interface RobotControlProofRefreshProxyResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1";
  refresh_kind: RobotControlProofRefreshKind;
  proxy_status: RobotControlProofRefreshProxyStatus;
  readback_only: true;
  no_motion_refresh: true;
  sends_motion_when_clicked: false;
  starts_radar_lifecycle: false;
  starts_nav2: false;
  starts_manual: false;
  starts_keyboard: false;
  starts_free_roam: false;
  starts_map_runtime: false;
  submits_delivery: false;
  stops_motion: false;
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint:
    | "/api/radar/scan-proof/refresh"
    | "/api/map/proof/refresh"
    | "/api/nav2/proof/refresh"
    | "/api/localize/reset";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  last_result_status: string;
  last_result_schema: string;
  last_result_evidence_ref: string;
  last_refreshed_at_ms: number;
  latest_readback_key_values: Record<string, string>;
  latest_proof_status?: string;
  scan_once_observed?: string;
  scan_hz_observed?: string;
  raw_packet_once_observed?: string;
  tf_observed?: string;
  continuous_scan_status?: string;
  continuous_window_observed?: string;
  continuity_window_status?: string;
  lifecycle_running?: string;
  lifecycle_state?: string;
  latest_scan_proof_fresh?: string;
  map_once_observed?: string;
  path_generated?: string;
  path_generation_succeeded?: string;
  path_point_count?: string;
  post_refresh_latest_readback_status?: string;
  post_refresh_latest_readback_attempt_count?: string;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  non_motion_evidence_actions_observed: string[];
  robot_control_executed: false;
}

export type RobotControlRadarLifecycleAction = "start" | "stop";
export type RobotControlRadarLifecycleProxyStatus = "lifecycle_forwarded" | "lifecycle_rejected" | "lifecycle_failed";
export type RobotControlRadarLifecycleEndpoint = "/api/radar/start" | "/api/radar/stop";

export interface RobotControlRadarLifecycleResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1";
  action: RobotControlRadarLifecycleAction;
  proxy_status: RobotControlRadarLifecycleProxyStatus;
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: RobotControlRadarLifecycleEndpoint;
  remote_method: "POST";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  command_result: {
    mode: string;
    executed: boolean;
    ok: boolean | null;
  };
  sensor_lifecycle_only: true;
  map_preview_endpoint: "/api/robot-control/map/preview";
  post_start_map_preview_required: boolean;
  radar_overlay_wysiwyg_status_plain: string;
  radar_overlay_wysiwyg_next_action_plain: string;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export type RobotControlNav2LifecycleAction = "start" | "stop";
export type RobotControlNav2LifecycleProxyStatus = "lifecycle_forwarded" | "lifecycle_rejected" | "lifecycle_failed";
export type RobotControlNav2LifecycleEndpoint = "/api/nav2/start" | "/api/nav2/stop";

export interface RobotControlNav2LifecycleResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_nav2_lifecycle_proxy.v1";
  action: RobotControlNav2LifecycleAction;
  proxy_status: RobotControlNav2LifecycleProxyStatus;
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: RobotControlNav2LifecycleEndpoint;
  remote_method: "POST";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  command_result: {
    mode: string;
    executed: boolean;
    ok: boolean | null;
  };
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export interface RobotControlRadarStatusResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_radar_status_proxy.v1";
  proxy_status: "status_loaded" | "status_rejected" | "status_failed";
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/radar/status";
  remote_endpoint: "/api/radar/status";
  remote_method: "GET";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  readback_only: true;
  radar_status_readback_only: true;
  sends_motion_when_clicked: false;
  starts_radar_lifecycle: false;
  starts_nav2: false;
  starts_manual: false;
  starts_keyboard: false;
  starts_free_roam: false;
  starts_map_runtime: false;
  submits_delivery: false;
  stops_motion: false;
  radar_key_values: Record<string, string>;
  plain_hint: string;
  next_action_plain: string;
  continuous_scan_status: string;
  lifecycle_running: string;
  lifecycle_state: string;
  latest_scan_proof_fresh: string;
  scan_point_count: string;
  latest_scan_age_ms: string;
  radar_status_plain: string;
  radar_next_action_plain: string;
  radar_scan_required_observations: string;
  radar_scan_observation_status: string;
  radar_scan_observation_missing_reasons: string;
  radar_scan_ready_for_map_overlay: string;
  radar_overlay_ready_for_map: string;
  radar_map_overlay_readiness_status: string;
  radar_map_overlay_next_action_plain: string;
  radar_overlay_point_count: string;
  radar_overlay_source_point_count: string;
  radar_overlay_wysiwyg_status_plain: string;
  radar_overlay_wysiwyg_next_action_plain: string;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export type RobotControlReadOnlyStatusProxyStatus = "status_loaded" | "status_rejected" | "status_failed";
export type RobotControlReadOnlyStatusWorkstationEndpoint =
  | "/api/robot-control/base/status"
  | "/api/robot-control/nav2/status";
export type RobotControlReadOnlyStatusRemoteEndpoint =
  | "/api/base/status"
  | "/api/nav2/status";

// PC 直连状态代理只做固定 GET 读回，给现场脚本和普通 UI 一份稳定 JSON。
// 顶层控制/交付 flag 继续固定 fail-closed，不能从上车状态读回外推成“可控”。
export interface RobotControlReadOnlyStatusResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_read_only_status_proxy.v1";
  proxy_status: RobotControlReadOnlyStatusProxyStatus;
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: RobotControlReadOnlyStatusWorkstationEndpoint;
  remote_endpoint: RobotControlReadOnlyStatusRemoteEndpoint;
  remote_method: "GET";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  status_key_values: Record<string, string>;
  plain_hint: string;
  next_action_plain: string;
  base_command_mode: string;
  nav2_base_command_mode: string;
  nav2_goal_execute_default_base_command_mode: string;
  lifecycle_running: string;
  lifecycle_state: string;
  controller_server_active: string;
  planner_server_active: string;
  path_generated: string;
  path_point_count: string;
  wheel_feedback_lr_nonzero_proven: string;
  wheel_feedback_nonzero_observed: string;
  motion_signal_observed: string;
  motion_signal_source: string;
  latest_t1001_observed_count: string;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  sends_commands: false;
  sends_motion_commands: false;
  robot_control_executed: false;
}

export type RobotControlMapLifecycleAction = "list" | "start" | "save" | "reset";
export type RobotControlMapLifecycleProxyStatus = "lifecycle_forwarded" | "lifecycle_rejected" | "lifecycle_failed";
export type RobotControlMapLifecycleEndpoint =
  | "/api/map/list"
  | "/api/map/start"
  | "/api/map/save"
  | "/api/map/reset";

// 地图 lifecycle 只开放固定 endpoint 与短字段白名单，不能退化成任意 Robot API 代理。
export interface RobotControlMapLifecycleRequest {
  map_name?: string;
  artifact_path?: string;
}

export interface RobotControlMapQualitySummary {
  status: "has_usable_map" | "no_free_cells" | "analysis_failed" | "not_checked" | "not_loaded";
  message: string;
  checked_yaml_count: number;
  usable_map_count: number;
  no_free_cell_map_count: number;
  analysis_failed_count: number;
}

export interface RobotControlMapLifecycleResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1";
  action: RobotControlMapLifecycleAction;
  proxy_status: RobotControlMapLifecycleProxyStatus;
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: RobotControlMapLifecycleEndpoint;
  remote_method: "GET" | "POST";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  map_count: number | null;
  map_names: string[];
  map_quality_summary: RobotControlMapQualitySummary;
  map_usable_for_navigation: boolean;
  map_needs_rebuild: boolean;
  command_result: {
    mode: string;
    executed: boolean;
    ok: boolean | null;
  };
  request_body: RobotControlMapLifecycleRequest;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export type RobotControlFreeRoamAutonomyAction = "start" | "stop";
export type RobotControlFreeRoamAutonomyProxyStatus = "autonomy_forwarded" | "autonomy_rejected" | "autonomy_failed";
export type RobotControlFreeRoamAutonomyEndpoint =
  | "/api/free-roam/autonomy/start"
  | "/api/free-roam/autonomy/stop";
export type RobotControlFreeRoamAutonomyLatestProxyStatus = "latest_loaded" | "latest_rejected" | "latest_failed";

export interface RobotControlFreeRoamAutonomyRequest {
  confirm_operator_safety?: boolean;
  confirm_mapping_active?: boolean;
}

export interface RobotControlFreeRoamAutonomySensorReadiness {
  ready?: boolean;
  missing?: string[];
  free_move_ready?: boolean;
  free_move_without_camera_allowed?: boolean;
  motion_without_radar_allowed?: boolean;
  degraded_without_radar?: boolean;
  mapping_readiness?: {
    ready?: boolean;
    missing?: string[];
    requires_camera_first_frame?: boolean;
    requires_fresh_radar_scan?: boolean;
    free_move_allowed_when_mapping_not_ready?: boolean;
  };
  camera?: Record<string, unknown>;
  radar?: Record<string, unknown>;
}

export interface RobotControlFreeRoamAutonomyResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_free_roam_autonomy_proxy.v1";
  action: RobotControlFreeRoamAutonomyAction;
  proxy_status: RobotControlFreeRoamAutonomyProxyStatus;
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: RobotControlFreeRoamAutonomyEndpoint;
  remote_method: "POST";
  remote_http_status: number | null;
  status: "blocked" | "requested";
  request_body: RobotControlFreeRoamAutonomyRequest;
  command_result: {
    mode: string;
    executed: boolean;
    ok: boolean | null;
    write_strategy?: string;
    parameters?: string[];
    parameter_count?: number;
    stdout_preview?: string;
  };
  latest_decision_state: string;
  latest_cmd_vel_publish_enabled: boolean;
  start_runtime_wait: {
    waited: boolean;
    ok: boolean;
    attempts?: number;
    http_status?: number | null;
    decision_state?: string;
    cmd_vel_publish_enabled?: boolean;
    failure_reason?: string;
    reason?: string;
  };
  sets_state_machine_parameters: boolean;
  mapping_active_requested?: boolean;
  mapping_active_applied?: boolean;
  direct_cmd_vel_publish: false;
  motion_unlock_requested: boolean;
  does_not_set_motion_unlock: boolean;
  free_move_start_ready: boolean;
  free_move_blocked_reasons: string[];
  mapping_readiness_ready: boolean;
  mapping_blocked_reasons: string[];
  sensor_readiness: RobotControlFreeRoamAutonomySensorReadiness;
  blocked_parameters_not_touched: string[];
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export interface RobotControlFreeRoamAutonomyLatestResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_free_roam_autonomy_latest_proxy.v1";
  proxy_status: RobotControlFreeRoamAutonomyLatestProxyStatus;
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/free-roam/autonomy/latest";
  remote_endpoint: "/api/free-roam/autonomy/latest";
  remote_method: "GET";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  plain_hint: string;
  next_action_plain: string;
  runtime_status: string;
  decision_state: string;
  decision_reason: string;
  stop_request_pending: boolean;
  free_roam_stop_request_pending: boolean;
  start_will_clear_stop_request: boolean;
  start_clears_stop_request_not_blocking: boolean;
  motion_start_blocked_by_stop_request: boolean;
  stop_request_status_plain: string;
  safety_confirmed: boolean;
  free_move_ready: boolean;
  free_move_start_ready: boolean;
  free_roam_motion_start_ready: boolean;
  motion_start_ready: boolean;
  free_roam_motion_ready: boolean;
  motion_ready: boolean;
  motion_without_radar_allowed: boolean;
  free_move_without_camera_allowed: boolean;
  free_roam_mapping_start_ready: boolean;
  mapping_start_ready: boolean;
  free_roam_mapping_start_missing_reasons: string[];
  mapping_start_missing_reasons: string[];
  free_roam_mapping_start_plain: string;
  free_roam_mapping_start_next_action: string;
  free_roam_mapping_ready: boolean;
  free_roam_mapping_missing_reasons: string[];
  mapping_ready: boolean;
  mapping_missing_reasons: string[];
  missing_capabilities: string[];
  mapping_readiness_ready: boolean;
  mapping_blocked_reasons: string[];
  motion_readiness_plain: string;
  free_move_start_status_plain: string;
  motion_runtime_status_plain: string;
  mapping_acceptance_status_plain: string;
  mapping_readiness_plain: string;
  motion_next_action_plain: string;
  mapping_next_action_plain: string;
  latest_key_values: Record<string, string>;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  sends_commands?: false;
  sends_motion_commands?: false;
  robot_control_executed: false;
}

export interface RobotControlMapPreviewResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_map_preview_proxy.v1";
  proxy_status: "preview_forwarded" | "preview_rejected" | "preview_failed";
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: "/api/map/preview";
  remote_http_status: number | null;
  status: "blocked" | "loaded_fail_closed_summary";
  readback_only: true;
  map_preview_readback_only: true;
  no_motion_refresh: true;
  sends_motion_when_clicked: false;
  starts_radar_lifecycle: false;
  starts_nav2: false;
  starts_manual: false;
  starts_keyboard: false;
  starts_free_roam: false;
  starts_map_runtime: false;
  submits_delivery: false;
  stops_motion: false;
  plain_hint: string;
  map_plain_hint: string;
  map_next_action_plain: string;
  map_name: string;
  map_yaml_name: string;
  map_image_name: string;
  width: number;
  height: number;
  resolution: number | null;
  origin: number[];
  cell_counts: Record<string, number>;
  has_free_cells: boolean;
  navigation_quality: string;
  image_mime_type: "image/png" | "not_loaded";
  image_data_url: string;
  source_image_format: string;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  radar_overlay?: RobotControlMapPreviewRadarOverlay;
  map_wysiwyg_status_plain: string;
  map_wysiwyg_next_action_plain: string;
  radar_overlay_status: RobotControlMapPreviewRadarOverlay["overlay_status"];
  radar_overlay_plain_hint: string;
  radar_overlay_wysiwyg_status_plain: string;
  radar_overlay_wysiwyg_next_action_plain: string;
  radar_overlay_next_action: string;
  radar_overlay_next_action_plain: string;
  radar_overlay_points: RobotApiScanPreviewPoint[];
  radar_overlay_count: number;
  radar_overlay_source_count: number | null;
  radar_overlay_point_count: number;
  radar_overlay_current_point_count: number;
  radar_overlay_source_point_count: number | null;
  radar_overlay_refresh_required: boolean;
  radar_overlay_needs_refresh: boolean;
  radar_overlay_blocks_wysiwyg: boolean;
  radar_overlay_blocks_free_move: false;
  radar_overlay_recovery_sequence: string[];
  fixed_radar_overlay_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh";
  fixed_radar_overlay_map_preview_endpoint: "/api/robot-control/map/preview";
  radar_overlay_refresh_sends_motion: false;
  radar_overlay_refresh_starts_radar_lifecycle: false;
  radar_overlay_stale_source_points_suppressed: boolean;
  radar_overlay_primary_blocked_reason: string;
  radar_overlay_current_vs_source_plain: string;
  radar_overlay_scan_preview_point_count: number;
  radar_overlay_scan_preview_source_point_count: number | null;
  radar_overlay_frame_id: string;
  radar_overlay_source_frame_id: string;
  robot_pose: RobotApiMapPose | null;
  robot_pose_status: "map_pose_observed" | "not_observed";
  path_preview_points: RobotApiPathPreviewPoint[];
  path_preview_status: "path_preview_observed" | "not_observed";
  path_preview_next_action_plain: string;
  next_action_plain: string;
  path_wysiwyg_status_plain: string;
  path_wysiwyg_next_action_plain: string;
  nav2_route_overlay_status: "path_preview_observed" | "not_observed";
  nav2_route_overlay_point_count: number;
  nav2_route_overlay_next_action_plain: string;
  path_preview_point_count: number;
  path_preview_source_point_count: number | null;
  path_preview_frame_id: string;
  path_preview_source_endpoint_ids: RobotApiReadEndpointId[];
  robot_control_executed: false;
}

export interface RobotControlCameraAnswerSummary {
  type: "answer" | "pranswer";
  sdp: string;
}

export interface RobotControlCameraOfferProxyResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_camera_offer_proxy.v1";
  proxy_status: "offer_forwarded" | "offer_rejected" | "offer_failed";
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: "/api/camera/offer";
  remote_http_status: number | null;
  status: string;
  peer_id: string;
  answer: RobotControlCameraAnswerSummary | null;
  error: string;
  failure_reason: string;
  blocked_reasons: string[];
  robot_control_executed: false;
}

export interface RobotControlCameraCloseProxyResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_camera_close_proxy.v1";
  proxy_status: "peer_closed" | "close_rejected" | "close_failed";
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: "/api/camera/peers/{peer_id}/close";
  remote_http_status: number | null;
  peer_id: string;
  status: string;
  error: string;
  failure_reason: string;
  blocked_reasons: string[];
  robot_control_executed: false;
}

export interface RobotControlCameraMjpegStatusResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_camera_mjpeg_status.v1";
  proxy_status: "status_loaded" | "status_rejected";
  source_base_url: string;
  normalized_base_url: string;
  workstation_endpoint: "/api/robot-control/camera/mjpeg/status";
  remote_endpoint: "/api/camera/mjpeg";
  relay_key: string;
  client_count: number;
  shared_preview_client_count: number;
  viewer_count: number;
  upstream_active: boolean;
  shared_preview_upstream_active: boolean;
  upstream_connected: boolean;
  content_type_loaded: boolean;
  shared_preview_content_type_loaded: boolean;
  content_type: string;
  cached_frame_loaded: boolean;
  shared_preview_cached_frame_loaded: boolean;
  has_recent_frame: boolean;
  cached_frame_age_ms: number | null;
  shared_preview_cached_frame_age_ms: number | null;
  shared_capture: true;
  shared_preview_shared_capture: true;
  exclusive_camera_claim: false;
  shared_preview_exclusive_camera_claim: false;
  shared_preview_contract: "single_shared_capture_for_multiple_clients";
  shared_preview_multi_viewer_status: "single_upstream_multi_viewer";
  shared_preview_multi_viewer_plain: string;
  shared_preview_everyone_can_join: true;
  shared_preview_current_frame_visible: boolean;
  shared_preview_gap_plain: string;
  shared_preview_readback_only: true;
  shared_preview_starts_camera_exclusive_capture: false;
  shared_preview_sends_motion: false;
  shared_preview_starts_nav2: false;
  shared_preview_starts_manual: false;
  shared_preview_starts_keyboard: false;
  shared_preview_starts_free_roam: false;
  shared_preview_starts_map_runtime: false;
  shared_preview_submits_delivery: false;
  shared_preview_stops_motion: false;
  last_failure_reason: string;
  shared_preview_last_failure_reason: string;
  last_remote_http_status: number | null;
  shared_preview_last_remote_http_status: number | null;
  last_failure_at_ms: number | null;
  shared_preview_last_failure_at_ms: number | null;
  source_diagnosis_status: string;
  source_diagnosis_plain_hint: string;
  source_diagnosis_next_action: string;
  source_diagnosis_next_action_plain: string;
  source_diagnosis_not_exclusive: string;
  uvc_kernel_diagnostics_status?: string;
  uvc_kernel_diagnostics_plain_hint?: string;
  uvc_kernel_diagnostics_next_action?: string;
  uvc_kernel_diagnostics_transport_error_count?: string;
  uvc_kernel_diagnostics_latest_transport_error?: string;
  uvc_usb_topology_status?: string;
  uvc_usb_topology_plain_hint?: string;
  uvc_usb_topology_next_action?: string;
  uvc_usb_topology_video_usb_speed?: string;
  uvc_usb_topology_kernel_usb_address?: string;
  uvc_usb_topology_video_interface_count?: string;
  camera_usb_speed: string;
  camera_usb_full_speed_detected: boolean;
  camera_hardware_action_required: boolean;
  camera_hardware_action_label: string;
  camera_blocks_mapping_start: boolean;
  camera_blocks_free_move: false;
  camera_reprobe_after_hardware_action_required: boolean;
  camera_reprobe_sequence: string[];
  fixed_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe";
  fixed_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status";
  fixed_summary_endpoint: "/api/robot-control/summary";
  camera_recovery_sends_motion: false;
  camera_recovery_starts_map_runtime: false;
  readback_only: true;
  camera_status_readback_only: true;
  sends_motion_when_clicked: false;
  starts_camera_exclusive_capture: false;
  starts_radar_lifecycle: false;
  starts_nav2: false;
  starts_manual: false;
  starts_keyboard: false;
  starts_free_roam: false;
  starts_map_runtime: false;
  submits_delivery: false;
  stops_motion: false;
  source_readiness: string;
  source_failure_reason: string;
  last_first_frame_format_attempts_summary: string;
  selected_path: string;
  selected_name: string;
  selected_is_uvc_or_usb: string;
  source_usage_status: string;
  source_usage_owner_count: string;
  source_usage_scope?: "free" | "camera_service_self" | "external_holder" | "unknown";
  source_usage_not_exclusive?: string;
  status: "idle_not_started" | "waiting_for_first_frame" | "streaming" | "source_first_frame_failed" | "blocked";
  plain_hint: string;
  next_action_plain: string;
  preview_status: "idle_not_started" | "waiting_for_first_frame" | "streaming" | "source_first_frame_failed" | "blocked";
  preview_plain_hint: string;
  preview_next_action: string;
  preview_next_action_plain: string;
  preview_visible_status: string;
  preview_visible_plain: string;
  camera_wysiwyg_status_plain: string;
  camera_wysiwyg_next_action_plain: string;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export interface RobotControlCameraFirstFrameProbeProxyResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1";
  proxy_status: "probe_forwarded" | "probe_rejected" | "probe_failed";
  readback_only: true;
  camera_probe_readback_only: true;
  sends_motion_when_clicked: false;
  starts_camera_exclusive_capture: false;
  starts_radar_lifecycle: false;
  starts_nav2: false;
  starts_manual: false;
  starts_keyboard: false;
  starts_free_roam: false;
  starts_map_runtime: false;
  submits_delivery: false;
  stops_motion: false;
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: "/api/camera/first-frame/probe";
  remote_http_status: number | null;
  status: string;
  probe_key_values: {
    schema: string;
    device: string;
    requested_fourcc: string;
    open_ok: string;
    read_ok: string;
    first_frame_timeout: string;
    failure_reason: string;
    visible_content_proven: string;
    visible_content_candidate: string;
    sample_path: string;
    sample_write_ok: string;
    elapsed_ms: string;
    mean_luma: string;
    max_luma: string;
    dynamic_range_luma: string;
    non_black_ratio: string;
    backend_smoke_status: string;
    backend_frame_observed: string;
    backend_attempts: string;
    streamon_io_error_observed: string;
    streamon_io_error_count: string;
    latest_streamon_io_error: string;
    fallback_attempt_count: string;
    fallback_attempts_summary: string;
  };
  failure_reason: string;
  blocked_reasons: string[];
  camera_first_frame_ready: boolean;
  frame_observed: boolean;
  first_frame_observed: boolean;
  source_diagnosis_status: string;
  source_diagnosis_not_exclusive: string;
  source_diagnosis_plain_hint: string;
  source_diagnosis_next_action_plain: string;
  camera_usb_speed: string;
  camera_usb_full_speed_detected: boolean;
  camera_hardware_action_required: boolean;
  camera_hardware_action_label: string;
  camera_blocks_mapping_start: boolean;
  camera_blocks_free_move: false;
  camera_reprobe_after_hardware_action_required: boolean;
  camera_reprobe_sequence: string[];
  fixed_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe";
  fixed_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status";
  fixed_summary_endpoint: "/api/robot-control/summary";
  camera_recovery_sends_motion: false;
  camera_recovery_starts_map_runtime: false;
  dangerous_true_fields: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
}

export interface RobotControlBaseFeedbackSamplesProxyResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_base_feedback_samples_proxy.v1";
  proxy_status: "samples_forwarded" | "samples_rejected" | "samples_failed";
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: "/api/base/feedback-samples" | "/api/base/feedback-samples/latest";
  remote_http_status: number | null;
  status: string;
  sample_key_values: {
    schema: string;
    requested_sample_count: string;
    completed_sample_count: string;
    t1001_observed_count: string;
    all_samples_observed_t1001: string;
    partial_samples_observed_t1001: string;
    wheel_feedback_lr_nonzero_proven: string;
    wheel_feedback_nonzero_observed: string;
    wheel_feedback_nonzero_frame_count: string;
    wheel_feedback_latest_left_speed: string;
    wheel_feedback_latest_right_speed: string;
    wheel_feedback_source: string;
    feedback_ack_t1001_observed: string;
    observed_feedback_types: string;
    sends_motion_commands: string;
    robot_control_executed: string;
  };
  wheel_raw_left: string;
  wheel_raw_right: string;
  latest_raw_left: string;
  latest_raw_right: string;
  base_feedback_lr_nonzero_proven: string;
  wheel_feedback_lr_nonzero_proven: string;
  wheel_feedback_source: string;
  wheel_feedback_plain_hint: string;
  wheel_feedback_next_action: string;
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  sends_motion_commands: false;
  robot_control_executed: false;
}

export type RobotControlBaseDirection = "forward" | "back" | "left" | "right" | "stop";
export type RobotControlBaseCommandKind = "manual" | "stop";
export type RobotControlBaseProxyStatus = "command_forwarded" | "command_rejected" | "command_failed";
export type RobotControlEvidenceCaptureStatus = "captured" | "partial" | "blocked";
export type RobotControlEvidenceCapturePhase = "before" | "after";
export type RobotControlEvidenceCaptureEndpointId =
  | "base_status"
  | "base_feedback_samples_latest"
  | "radar_status"
  | "radar_scan_proof_latest";
export type RobotControlEvidenceCaptureEndpointPath =
  | "/api/base/status"
  | "/api/base/feedback-samples/latest"
  | "/api/radar/status"
  | "/api/radar/scan-proof/latest";

export interface RobotControlEvidenceEndpointCapture {
  phase: RobotControlEvidenceCapturePhase;
  id: RobotControlEvidenceCaptureEndpointId;
  endpoint: RobotControlEvidenceCaptureEndpointPath;
  method: "GET";
  request_status: "loaded" | "failed" | "blocked";
  http_status: number | null;
  status: string;
  schema: string;
  key_values: Record<string, string>;
  failure_reason: string;
}

export type RobotControlEvidenceReadbackSummary = Partial<
  Record<RobotControlEvidenceCaptureEndpointId, RobotControlEvidenceEndpointCapture>
>;

// 点动请求只描述 workstation 到上位机的固定代理合同。
// UI 不能借这份合同推导出“可控”或“HIL 已通过”。
export interface RobotControlBaseCommandRequest {
  direction: RobotControlBaseDirection;
  speed: number;
  duration_ms: number;
  confirm_hil_checklist: boolean;
}

export interface RobotControlBaseCommandProxyResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1";
  command_kind: RobotControlBaseCommandKind;
  proxy_status: RobotControlBaseProxyStatus;
  source_base_url: string;
  normalized_base_url: string;
  remote_endpoint: "/api/base/manual" | "/api/base/stop";
  remote_http_status: number | null;
  status: string;
  requested_direction: RobotControlBaseDirection;
  applied_direction: RobotControlBaseDirection;
  requested_speed_mps: number | null;
  clamped_speed_mps: number;
  requested_duration_ms: number | null;
  clamped_duration_ms: number;
  confirm_hil_checklist: boolean;
  minimal_precheck_safety_only: true;
  safety_confirmation_field: "confirm_hil_checklist";
  safety_confirmation_received: boolean;
  operator_report_preflight_required: false;
  camera_or_radar_required_for_motion: false;
  minimal_precheck_plain: string;
  non_stop_requires_confirm_hil_checklist: true;
  hil_checklist_gate_status: "stop_allowed_without_checklist" | "manual_allowed" | "manual_blocked_missing_checklist";
  checklist_missing: string[];
  operator_report_preflight: RobotControlOperatorReportPreflight;
  request_contract: {
    max_speed_mps: number;
    max_duration_ms: number;
    allowed_directions: RobotControlBaseDirection[];
  };
  evidence_capture_status: RobotControlEvidenceCaptureStatus;
  evidence_capture_endpoints: RobotControlEvidenceEndpointCapture[];
  evidence_capture_blocked_reasons: string[];
  before_readback: RobotControlEvidenceReadbackSummary;
  after_readback: RobotControlEvidenceReadbackSummary;
  remote_motion_key_values?: Record<string, string>;
  motion_evidence_summary: string;
  motion_evidence_gaps: string[];
  failure_reason: string;
  blocked_reasons: string[];
  hard_dangerous_true_fields: string[];
  robot_control_executed: false;
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
  probe_observed_at_ms: number;
  remote_pose_timestamp_ms: number | null;
  remote_pose_age_ms: number | null;
  freshness_gate_status: string;
  latency_lt_2s_proven: false;
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

export interface O7RtcSignalingContractProbeResponse extends ProofFlags {
  schema: "trashbot.pc_tools_workstation.o7_rtc_signaling_contract_probe.v1";
  probe_status: "loaded_fail_closed_contract" | "fail_closed";
  source_base_url: string;
  remote_endpoint: "/api/o7/rtc-signaling/contract";
  remote_schema: string;
  contract_status: string;
  key_false_fields: string[];
  protocol_surface_keys: string[];
  required_evidence_refs: string[];
  blocked_reasons: string[];
  not_proven: string[];
  dangerous_true_fields: string[];
  fail_closed_reason: string;
  local_loopback_only: true;
  network_probe_executed: false;
  connects_cloud_production: false;
  sends_commands: false;
  reads_hardware: false;
}

export type O7PreviewsAcceptanceSurfaceId =
  | "cloud_operator_console_probe"
  | "cloud_archive_tasks_probe"
  | "rtc_signaling_contract_probe"
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
  workstation_host: "0.0.0.0";
  workstation_port: 7001;
  workstation_listen_address: "http://0.0.0.0:7001";
  default_robot_api_base_url: "http://192.168.1.11:8787";
  server_started_at_ms: number;
  server_started_at_iso: string;
  health_readback_only: true;
  robot_api_probe_executed: false;
  sends_motion_when_clicked: false;
  starts_nav2: false;
  starts_manual: false;
  starts_keyboard: false;
  starts_free_roam: false;
  starts_map_runtime: false;
  submits_delivery: false;
  stops_motion: false;
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
  "/api/o7/live-endpoints/manifest",
  "/api/o7/cloud-operator-console-probe?baseUrl=<local-loopback-url>",
  "/api/o7/cloud-archive/tasks-probe?baseUrl=<local-loopback-url>",
  "/api/o7/rtc-signaling-contract-probe?baseUrl=<local-loopback-url>",
  "/api/o7/realtime-elevator-probe?baseUrl=<local-loopback-url>",
  "/api/o7/realtime-elevator-preview?fixtureJson=<local-json>",
  "/api/o7/route-replay-preview?fixtureJson=<local-json>",
  "/api/o7/labeling-preview?fixtureJson=<local-json>",
  "/api/o7/field-evidence-consumer-ingest?manifestJson=<local-json>&routeReplayFixtureJson=<local-json>&labelingFixtureJson=<local-json>",
  "/api/o7/voice-preview?fixtureJson=<local-json>",
  "/api/o7/safe-command-preview?fixtureJson=<local-json>",
  "/api/o7/cloud-archive/tasks?archiveJson=<local-json>",
  "/api/robot-control/summary?baseUrl=<robot-api-base-url>",
  "/api/robot-control/base/manual?baseUrl=<robot-api-base-url>",
  "/api/robot-control/base/first-jog?baseUrl=<robot-api-base-url>",
  "/api/robot-control/base/stop?baseUrl=<robot-api-base-url>",
  "/api/robot-control/base/feedback-samples?baseUrl=<robot-api-base-url>",
  "/api/robot-control/radar/status?baseUrl=<robot-api-base-url>",
  "/api/robot-control/radar/scan-proof/refresh?baseUrl=<robot-api-base-url>",
  "/api/robot-control/radar/start?baseUrl=<robot-api-base-url>",
  "/api/robot-control/radar/stop?baseUrl=<robot-api-base-url>",
  "/api/robot-control/map/proof/refresh?baseUrl=<robot-api-base-url>",
  "/api/robot-control/map/list?baseUrl=<robot-api-base-url>",
  "/api/robot-control/map/preview?baseUrl=<robot-api-base-url>",
  "/api/robot-control/map/start?baseUrl=<robot-api-base-url>",
  "/api/robot-control/map/save?baseUrl=<robot-api-base-url>",
  "/api/robot-control/map/reset?baseUrl=<robot-api-base-url>",
  "/api/robot-control/free-roam/autonomy/start?baseUrl=<robot-api-base-url>",
  "/api/robot-control/free-roam/autonomy/stop?baseUrl=<robot-api-base-url>",
  "/api/robot-control/nav2/start?baseUrl=<robot-api-base-url>",
  "/api/robot-control/nav2/stop?baseUrl=<robot-api-base-url>",
  "/api/robot-control/nav2/proof/refresh?baseUrl=<robot-api-base-url>",
  "/api/robot-control/nav2/goal/preflight?baseUrl=<robot-api-base-url>",
  "/api/robot-control/nav2/goal/execute?baseUrl=<robot-api-base-url>",
  "/api/robot-control/nav2/goal/execution/latest?baseUrl=<robot-api-base-url>",
  "/api/robot-control/delivery/latest?baseUrl=<robot-api-base-url>",
  "/api/robot-control/delivery/check?baseUrl=<robot-api-base-url>",
  "/api/robot-control/delivery/complete?baseUrl=<robot-api-base-url>",
  "/api/robot-control/localize/reset?baseUrl=<robot-api-base-url>",
  "/api/robot-control/camera/offer?baseUrl=<robot-api-base-url>",
  "/api/robot-control/camera/first-frame/probe?baseUrl=<robot-api-base-url>",
  "/api/robot-control/camera/peers/<peer-id>/close?baseUrl=<robot-api-base-url>",
  "/api/robot-control/operator/report?baseUrl=<robot-api-base-url>",
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
  "real_o7_field_evidence_manifest",
  "real_o7_field_evidence_consumer_ingest",
  "real_o7_annotation_submit",
  "real_o7_dataset_export",
  "real_o7_voice_api",
  "real_o7_asr_tts_runtime",
  "real_o7_safe_command_fixture_preview_dispatch",
  "real_o7_operator_command_dispatch",
  "delivery_success",
] as const;
