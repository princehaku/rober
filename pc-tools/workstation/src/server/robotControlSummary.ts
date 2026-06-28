import { PROOF_FLAGS } from "../shared/contracts";
import type {
  RobotApiEndpointReadback,
  RobotApiFrameTransform,
  RobotApiMapPose,
  RobotApiPathPreviewPoint,
  RobotApiProofSummary,
  RobotApiReadEndpointId,
  RobotApiScanPreviewPoint,
  RobotControlOperatorHilMaterialSummary,
  RobotControlOperatorReportPreflight,
  RobotControlMapLifecycleAction,
  RobotControlMapLifecycleEndpoint,
  RobotControlMapQualitySummary,
  RobotControlMapLifecycleRequest,
  RobotControlMapLifecycleResponse,
  RobotControlMapPreviewResponse,
  RobotControlMapPreviewRadarOverlay,
  RobotControlNavGoalPreflightRequest,
  RobotControlNavGoalPreflightResponse,
  RobotControlOperatorReportProxyResponse,
  RobotControlOperatorReportRequest,
  RobotControlOperatorReportStructuredHilClaims,
  RobotControlProofRefreshProxyResponse,
  RobotControlProofRefreshKind,
  RobotControlNav2LifecycleAction,
  RobotControlNav2LifecycleEndpoint,
  RobotControlNav2LifecycleResponse,
  RobotControlRadarLifecycleAction,
  RobotControlRadarLifecycleEndpoint,
  RobotControlRadarLifecycleResponse,
  RobotControlSummaryResponse,
} from "../shared/contracts";

type JsonRecord = Record<string, unknown>;
type InternalRobotApiEndpointReadback = RobotApiEndpointReadback & {
  payload: JsonRecord | null;
};
type FreeRoamGateRow = RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_gates"][number];
type RobotControlSummaryBuildOptions = {
  readbackTimeoutMs?: number;
};
type MapPreviewPathPreview = Pick<
  RobotApiProofSummary,
  "path_preview_points" | "path_preview_point_count" | "path_preview_source_point_count" | "path_preview_frame_id"
>;
type MapPreviewOverlayReadback = {
  radarOverlay: RobotControlMapPreviewRadarOverlay;
  pathPreview: MapPreviewPathPreview;
  sourceEndpointIds: RobotApiReadEndpointId[];
};

const ROBOT_CONTROL_SCHEMA = "trashbot.pc_tools_workstation.robot_control_summary.v1" as const;
const DEFAULT_REQUEST_TIMEOUT_MS = 1500;
const SLOW_READBACK_TIMEOUT_MS = 4000;
const HEAVY_READBACK_TIMEOUT_MS = 8000;
export const ROBOT_CONTROL_SUMMARY_HTTP_READBACK_TIMEOUT_MS = 2400;
export const ROBOT_CONTROL_CAMERA_HEALTH_TIMEOUT_MS = HEAVY_READBACK_TIMEOUT_MS;
const CAMERA_FIRST_FRAME_FAILURE_REASONS = [
  "capture_read_returned_false",
  "capture_read_call_timeout",
  "first_frame_timeout",
  "first_frame_total_timeout",
] as const;
export const ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS = 0.12;
export const ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS = 800;
export const ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS = 260;
export const ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS = 240;
const ROBOT_CONTROL_PATH_PREVIEW_POINT_LIMIT = 64;
const ROBOT_CONTROL_SCAN_PREVIEW_POINT_LIMIT = 72;
const ROBOT_CONTROL_SCAN_PREVIEW_MIN_RANGE_M = 0.03;
const ROBOT_CONTROL_SCAN_PREVIEW_MAX_RANGE_M = 8;
export const ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS = ["forward", "back", "left", "right", "stop"] as const;
export const ROBOT_CONTROL_HIL_CHECKLIST = [
  { id: "operator_safety_confirmed", label: "现场安全确认（人在旁边、周围安全、停止手段就绪）" },
] as const;

type RobotReadEndpointConfig = {
  id: RobotApiReadEndpointId;
  endpoint: string;
  timeout_ms: number;
};

const READ_ENDPOINTS: RobotReadEndpointConfig[] = [
  // 真实上位机 /api/status 会顺带聚合 camera/radar/base 子摘要，读取窗口要比 proof latest 更宽。
  { id: "status", endpoint: "/api/status", timeout_ms: HEAVY_READBACK_TIMEOUT_MS },
  { id: "map_proof_latest", endpoint: "/api/map/proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "localize_proof_latest", endpoint: "/api/localize/proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "nav2_status", endpoint: "/api/nav2/status", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "nav2_proof_latest", endpoint: "/api/nav2/proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "nav2_goal_execution_latest", endpoint: "/api/nav2/goal/execution/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "operator_report_latest", endpoint: "/api/operator/report", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "free_roam_autonomy_latest", endpoint: "/api/free-roam/autonomy/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  // camera 端点在真实板端会探测设备与健康摘要，允许更长只读窗口，避免误判成离线。
  { id: "camera_health", endpoint: "/api/camera/health", timeout_ms: HEAVY_READBACK_TIMEOUT_MS },
  { id: "camera_devices", endpoint: "/api/camera/devices", timeout_ms: HEAVY_READBACK_TIMEOUT_MS },
  { id: "radar_status", endpoint: "/api/radar/status", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "radar_scan_proof_latest", endpoint: "/api/radar/scan-proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "radar_raw_packet_proof_latest", endpoint: "/api/radar/raw-packet-proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  // base status 可能触发 T=130 只读反馈窗口；用较宽读取预算，但危险字段扫描仍保持 fail-closed。
  { id: "base_status", endpoint: "/api/base/status", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "base_feedback_samples_latest", endpoint: "/api/base/feedback-samples/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
];

const OPTIONAL_MISSING_READ_ENDPOINT_IDS: ReadonlySet<RobotApiReadEndpointId> = new Set([
  "radar_scan_proof_latest",
  "radar_raw_packet_proof_latest",
  "free_roam_autonomy_latest",
  "nav2_goal_execution_latest",
]);
const OPTIONAL_MISSING_HTTP_STATUSES = new Set([404, 405, 501]);
const MAP_PREVIEW_OVERLAY_ENDPOINT_IDS: ReadonlySet<RobotApiReadEndpointId> = new Set([
  "localize_proof_latest",
  "nav2_status",
  "nav2_proof_latest",
  "free_roam_autonomy_latest",
  "radar_status",
  "radar_scan_proof_latest",
]);
const ALLOWED_ROBOT_READBACK_SCHEMA_PREFIXES = [
  "trashbot.upper_robot_api.v1",
  "trashbot.local_webrtc_camera_",
] as const;
const NAV2_GOAL_BLOCKER_ORDER = [
  "nav2_lifecycle_not_running",
  "nav2_stack_not_running",
  "planner_server_inactive",
  "controller_server_inactive",
  "nav2_map_not_consumed",
  "path_generation_service_unavailable",
  "path_generation_not_attempted",
  "path_generation_not_observed",
  "path_point_count_not_positive",
  "robot_map_pose_not_observed",
] as const;
const FREE_ROAM_GATE_ORDER = [
  "operator_confirmed",
  "stop_available",
  "external_stop_request",
  "motion_hil_unlock",
  "camera_first_frame",
  "lidar_fresh",
  "mapping_active",
  "fresh_map_preview",
  "obstacle_clear",
] as const;

function isRobotReadbackSchemaMismatch(readback: InternalRobotApiEndpointReadback): boolean {
  // schema mismatch 只统计已成功读到的真实合同错配；超时、optional missing 和无 schema 哨兵不应污染连接诊断。
  if (readback.request_status !== "loaded") {
    return false;
  }
  if (["schema_missing", "not_loaded", "not_object"].includes(readback.schema)) {
    return false;
  }
  return !ALLOWED_ROBOT_READBACK_SCHEMA_PREFIXES.some((prefix) => readback.schema.startsWith(prefix));
}

function sortNav2GoalBlockers(blockers: string[]): string[] {
  // blocker 顺序就是普通首屏操作顺序：先恢复 Nav2 服务，再处理路线/位姿读数。
  const order = new Map<string, number>(NAV2_GOAL_BLOCKER_ORDER.map((item, index) => [item, index]));
  return [...blockers].sort((left, right) => {
    const leftOrder = order.get(left) ?? Number.MAX_SAFE_INTEGER;
    const rightOrder = order.get(right) ?? Number.MAX_SAFE_INTEGER;
    return leftOrder === rightOrder ? left.localeCompare(right) : leftOrder - rightOrder;
  });
}

function sortFreeRoamGateRows(gates: FreeRoamGateRow[]): FreeRoamGateRow[] {
  // gate 顺序必须先回答“能不能低速移动”，再回答“能不能按建图验收”。
  const order = new Map<string, number>(FREE_ROAM_GATE_ORDER.map((item, index) => [item, index]));
  const scopeOrder: Record<NonNullable<FreeRoamGateRow["scope"]>, number> = {
    free_move_start: 0,
    runtime_diagnostic: 1,
    mapping_acceptance: 2,
  };
  return [...gates].sort((left, right) => {
    const leftOrder = order.get(left.id) ?? Number.MAX_SAFE_INTEGER;
    const rightOrder = order.get(right.id) ?? Number.MAX_SAFE_INTEGER;
    if (leftOrder !== rightOrder) {
      return leftOrder - rightOrder;
    }
    const leftScope = scopeOrder[left.scope ?? "runtime_diagnostic"];
    const rightScope = scopeOrder[right.scope ?? "runtime_diagnostic"];
    return leftScope === rightScope ? left.id.localeCompare(right.id) : leftScope - rightScope;
  });
}

function defaultFreeRoamGateRows(): FreeRoamGateRow[] {
  return sortFreeRoamGateRows([
    {
      id: "operator_confirmed",
      label: "现场安全确认",
      scope: "free_move_start",
      state: "blocked",
      evidence: "还未勾选现场安全确认",
      next_action: "勾选人在旁边、周围安全、停止手段就绪",
    },
    {
      id: "stop_available",
      label: "停止兜底",
      scope: "free_move_start",
      state: "ready",
      evidence: "PC 固定停止按钮已存在，仍需现场保持可点击",
      next_action: "继续保持现场可接管",
    },
    {
      id: "camera_first_frame",
      label: "画面首帧",
      scope: "mapping_acceptance",
      state: "not_proven",
      evidence: "未读到摄像头首帧",
      next_action: "画面未 ready 时仍可自由移动，但不能按建图验收",
    },
    {
      id: "lidar_fresh",
      label: "雷达监看",
      scope: "mapping_acceptance",
      state: "not_proven",
      evidence: "未读到 fresh 雷达扫描",
      next_action: "雷达未 ready 时仍可自由移动，但不能按建图验收",
    },
    {
      id: "motion_hil_unlock",
      label: "运动发布状态",
      scope: "runtime_diagnostic",
      state: "not_proven",
      evidence: "当前尚未启动自由移动",
      next_action: "勾选现场安全确认后点击开始自由移动（低速）",
    },
  ]);
}

export type RobotProofRefreshConfig = {
  kind: RobotControlProofRefreshKind;
  endpoint: "/api/radar/scan-proof/refresh" | "/api/map/proof/refresh" | "/api/nav2/proof/refresh" | "/api/localize/reset";
  request_body: Record<string, unknown>;
  timeout_cap_ms: number;
  safety_margin_ms: number;
  key_fields: string[];
};

const RADAR_SCAN_PROOF_REFRESH_CONFIG: RobotProofRefreshConfig = {
  kind: "radar_scan_proof_refresh",
  endpoint: "/api/radar/scan-proof/refresh",
  request_body: {
    // 真实上位机冷启动 LiDAR runtime 需要先等 ROS2 driver、raw packet 和 TF 都进入稳定窗口；
    // 固定长 warmup 仍是 no-motion 证据采集，不开放浏览器自定义控制参数。
    timeout_s: 20,
    runtime_warmup_s: 15,
    start_runtime: true,
  },
  timeout_cap_ms: 60_000,
  safety_margin_ms: 10_000,
  key_fields: [
    "status",
    "latest_proof_status",
    "latest_result_status",
    "evidence_ref",
    "scan_once_observed",
    "scan_hz_observed",
    "raw_packet_once_observed",
    "tf_observed",
    "continuous_scan_status",
    "continuous_window_observed",
    "continuity_window_status",
    "lifecycle_running",
    "lifecycle_state",
    "latest_scan_proof_fresh",
    "blocked_reasons",
    "continuity_blocked_reasons",
  ],
};

const MAP_PROOF_REFRESH_CONFIG: RobotProofRefreshConfig = {
  kind: "map_proof_refresh",
  endpoint: "/api/map/proof/refresh",
  request_body: {
    timeout_s: 45,
  },
  timeout_cap_ms: 120_000,
  safety_margin_ms: 20_000,
  key_fields: [
    "status",
    "latest_proof_status",
    "latest_result_status",
    "evidence_ref",
    "map_once_observed",
    "map_file_observed",
    "map_metadata_observed",
    "latest_map_quality_status",
    "latest_map_free_cell_count",
    "latest_map_usable_for_navigation",
    "blocked_reasons",
  ],
};

const NAV2_NO_MOTION_PROOF_REFRESH_CONFIG: RobotProofRefreshConfig = {
  kind: "nav2_no_motion_proof_refresh",
  endpoint: "/api/nav2/proof/refresh",
  request_body: {
    timeout_s: 30,
    managed_runtime_opt_in: true,
    managed_timeout_s: 30,
    initialpose_opt_in: true,
    initialpose_x: 0,
    initialpose_y: 0,
    initialpose_yaw: 0,
    path_generation_opt_in: true,
    path_generation_timeout_s: 30,
    path_goal_frame_id: "map",
    path_goal_x: 0.8,
    path_goal_y: 0,
    path_goal_yaw: 0,
  },
  timeout_cap_ms: 150_000,
  safety_margin_ms: 60_000,
  key_fields: [
    "status",
    "latest_proof_status",
    "latest_result_status",
    "evidence_ref",
    "managed_runtime_started",
    "initialpose_published",
    "path_generation_requested",
    "path_generation_boundary",
    "path_generated",
    "path_generation_succeeded",
    "path_point_count",
    "path_preview_point_count",
    "path_preview_source_point_count",
    "path_preview_frame_id",
    "planner_server_active",
    "root_causes",
    "blocked_reasons",
  ],
};

const LOCALIZATION_RESET_CONFIG: RobotProofRefreshConfig = {
  kind: "localization_reset",
  endpoint: "/api/localize/reset",
  request_body: {
    timeout_s: 30,
    managed_runtime_opt_in: true,
    managed_timeout_s: 30,
    initialpose_opt_in: true,
    initialpose_x: 0,
    initialpose_y: 0,
    initialpose_yaw: 0,
    initialpose_frame_id: "map",
    path_generation_opt_in: false,
  },
  timeout_cap_ms: 120_000,
  safety_margin_ms: 60_000,
  key_fields: [
    "status",
    "latest_proof_status",
    "latest_result_status",
    "evidence_ref",
    "initialpose_published",
    "amcl_pose_observed",
    "localization_tf_observed",
    "managed_runtime_started",
    "managed_runtime_cleanup_ok",
    "localization_reset_observed",
    "root_causes",
    "blocked_reasons",
  ],
};

const NAV2_NO_MOTION_PROOF_LATEST_ENDPOINT = "/api/nav2/proof/latest" as const;
const NAV_GOAL_PREFLIGHT_GOAL_LIMITS = {
  frame_id: "map",
  x_min_m: -3,
  x_max_m: 3,
  y_min_m: -3,
  y_max_m: 3,
  yaw_min_rad: -3.1416,
  yaw_max_rad: 3.1416,
} as const;
const NAV_GOAL_PREFLIGHT_ENDPOINTS: RobotReadEndpointConfig[] = [
  { id: "localize_proof_latest", endpoint: "/api/localize/proof/latest", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "nav2_proof_latest", endpoint: "/api/nav2/proof/latest", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  { id: "nav2_status", endpoint: "/api/nav2/status", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
];

type RobotMapLifecycleConfig = {
  action: RobotControlMapLifecycleAction;
  endpoint: RobotControlMapLifecycleEndpoint;
  method: "GET" | "POST";
};

const MAP_LIFECYCLE_CONFIGS: Record<RobotControlMapLifecycleAction, RobotMapLifecycleConfig> = {
  list: { action: "list", endpoint: "/api/map/list", method: "GET" },
  start: { action: "start", endpoint: "/api/map/start", method: "POST" },
  save: { action: "save", endpoint: "/api/map/save", method: "POST" },
  reset: { action: "reset", endpoint: "/api/map/reset", method: "POST" },
};

const OPERATOR_REPORT_REMOTE_ENDPOINT = "/api/operator/report" as const;
const OPERATOR_REPORT_TIMEOUT_MS = 5000;
export const ROBOT_CONTROL_OPERATOR_REPORT_PREFLIGHT_TIMEOUT_MS = 1500;
export const ROBOT_CONTROL_OPERATOR_REPORT_PREFLIGHT_REQUIRED_FIELDS = [
  "operator_present",
  "physical_clearance_confirmed",
  "emergency_stop_ready",
  "external_video_recorded",
  "external_video_ref",
  "visible_content_proven",
  "camera_artifacts_ref",
  "wheel_feedback_lr_nonzero_proven",
  "wheel_feedback_ref",
  "physical_motion_lidar_delta_proven",
  "scan_delta_ref",
] as const;
export const ROBOT_CONTROL_FIRST_JOG_PREFLIGHT_REQUIRED_FIELDS = [
  "confirm_hil_checklist",
] as const;
const OPERATOR_REPORT_TOP_LEVEL_FIELDS = new Set([
  "operator_present",
  "evidence_ref",
  "physical_clearance_confirmed",
  "emergency_stop_ready",
  "observed_motion",
  "observed_stop",
  "reported_at",
  "operator_notes",
  "structured_hil_claims",
]);
const OPERATOR_REPORT_CLAIM_FIELDS = new Set([
  "external_video_recorded",
  "external_video_ref",
  "visible_content_proven",
  "camera_artifacts_ref",
  "wheel_feedback_lr_nonzero_proven",
  "wheel_feedback_ref",
  "physical_motion_lidar_delta_proven",
  "scan_delta_ref",
  "real_route_map_proven",
  "route_map_ref",
  "delivery_success",
  "site_state",
]);
const OPERATOR_REPORT_BOOLEAN_FIELDS = new Set([
  "operator_present",
  "physical_clearance_confirmed",
  "emergency_stop_ready",
  "observed_motion",
  "observed_stop",
  "external_video_recorded",
  "visible_content_proven",
  "wheel_feedback_lr_nonzero_proven",
  "physical_motion_lidar_delta_proven",
  "real_route_map_proven",
  "delivery_success",
]);
const OPERATOR_REPORT_STRING_LIMITS: Record<string, number> = {
  evidence_ref: 512,
  reported_at: 80,
  operator_notes: 2000,
  external_video_ref: 512,
  camera_artifacts_ref: 512,
  wheel_feedback_ref: 512,
  scan_delta_ref: 512,
  route_map_ref: 512,
  site_state: 160,
};

type RobotRadarLifecycleConfig = {
  action: RobotControlRadarLifecycleAction;
  endpoint: RobotControlRadarLifecycleEndpoint;
};

const RADAR_LIFECYCLE_CONFIGS: Record<RobotControlRadarLifecycleAction, RobotRadarLifecycleConfig> = {
  start: { action: "start", endpoint: "/api/radar/start" },
  stop: { action: "stop", endpoint: "/api/radar/stop" },
};

type RobotNav2LifecycleConfig = {
  action: RobotControlNav2LifecycleAction;
  endpoint: RobotControlNav2LifecycleEndpoint;
};

const NAV2_LIFECYCLE_CONFIGS: Record<RobotControlNav2LifecycleAction, RobotNav2LifecycleConfig> = {
  start: { action: "start", endpoint: "/api/nav2/start" },
  stop: { action: "stop", endpoint: "/api/nav2/stop" },
};

const REFRESH_NON_MOTION_EVIDENCE_ACTION_FIELDS = new Set(["sends_commands", "starts_ros2"]);

const HARD_DANGEROUS_TRUE_FIELDS = new Set([
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "command_dispatch_enabled",
  "manual_control_enabled",
  "navigate_goal_enabled",
  "keyboard_control_enabled",
  "robot_control_executed",
  "sends_motion_commands",
  "sends_base_motion_commands",
  "publishes_cmd_vel",
  "cmd_vel_publish_enabled",
  "calls_base_manual",
  "starts_nav2",
  "opens_serial",
  "opens_base_uart",
  "uses_base_uart",
  "hil_pass",
]);

const NAV2_LIFECYCLE_HARD_DANGEROUS_TRUE_FIELDS = new Set(
  [...HARD_DANGEROUS_TRUE_FIELDS].filter((field) => field !== "starts_nav2"),
);
const DANGEROUS_TRUE_FIELDS = new Set([...HARD_DANGEROUS_TRUE_FIELDS, ...REFRESH_NON_MOTION_EVIDENCE_ACTION_FIELDS]);
const NO_TRUE_FIELD_EXEMPTIONS = new Set<string>();
const STATUS_BASE_FEEDBACK_TRUE_FIELD_EXEMPTIONS = new Set([
  "base.sends_commands",
  "base.feedback_readback.sends_commands",
]);
const BASE_STATUS_FEEDBACK_TRUE_FIELD_EXEMPTIONS = new Set([
  "sends_commands",
  "feedback_readback.sends_commands",
]);
const BASE_FEEDBACK_SAMPLES_TRUE_FIELD_EXEMPTIONS = new Set([
  "sends_commands",
  "latest_result.sends_commands",
]);
const OPERATOR_REPORT_CLAIM_TRUE_FIELD_EXEMPTIONS = new Set([
  "structured_hil_claims.delivery_success",
  "latest_result.structured_hil_claims.delivery_success",
  "latest_result.operator_report.structured_hil_claims.delivery_success",
]);
const NAV2_GOAL_EXECUTION_LATEST_TRUE_FIELD_EXEMPTIONS = new Set([
  // 这是只读“最近一次 NavigateToPose 是否真的触到底盘”的历史证据；PC summary 顶层仍固定不执行控制。
  "robot_control_executed",
  "latest_result.robot_control_executed",
  "sends_motion_commands",
  "latest_result.sends_motion_commands",
  "sends_base_motion_commands",
  "latest_result.sends_base_motion_commands",
  "uses_base_uart",
  "latest_result.uses_base_uart",
  "hil_pass",
  "latest_result.hil_pass",
]);

const STATUS_KEYS = [
  "safe_to_control",
  "delivery_success",
  "primary_actions_enabled",
  "path_generated",
  "path_generation_requested",
  "path_generation_succeeded",
  "path_point_count",
  "path_preview_point_count",
  "path_preview_source_point_count",
  "path_preview_frame_id",
  "managed_runtime_started",
  "scan_once_observed",
  "map_once_observed",
  "amcl_pose_observed",
  "localization_tf_observed",
  "planner_server_active",
  "controller_server_active",
  "controller_server_requested",
  "latest_planner_active",
  "latest_controller_active",
  "latest_controller_requested",
  "latest_map_consumed",
  "latest_path_generated",
  "latest_path_generation_succeeded",
  "latest_path_generation_attempted",
  "latest_path_generation_service_available",
  "latest_path_generation_service_name",
  "latest_path_generation_ready",
  "latest_path_point_count",
  "latest_path_preview_point_count",
  "latest_path_preview_source_point_count",
  "latest_path_preview_frame_id",
  "latest_proof_status",
  "feedback_ack_status",
  "nav2_base_command_mode",
  "latest_t1001_observed_count",
  "t1001_observed_count",
  "wheel_feedback_lr_nonzero_proven",
  "wheel_feedback_nonzero_observed",
  "wheel_feedback_latest_left_speed",
  "wheel_feedback_latest_right_speed",
  "wheel_feedback_latest_raw_left",
  "wheel_feedback_latest_raw_right",
  "wheel_feedback_latest_nonzero_left_speed",
  "wheel_feedback_latest_nonzero_right_speed",
  "wheel_feedback_nonzero_frame_count",
  "wheel_feedback_frame_count",
  "wheel_feedback_source",
  "feedback_voltage_v",
  "feedback_samples_freshness_status",
  "feedback_samples_age_ms",
  "left_speed",
  "right_speed",
  "latest_scan_once_observed",
  "continuous_scan_status",
  "continuous_window_observed",
  "continuity_window_status",
  "lifecycle_running",
  "lifecycle_state",
  "latest_scan_proof_fresh",
  "runtime_status",
  "decision_state",
  "decision_reason",
  "stop_required",
  "artifact_only",
  "cmd_vel_publish_enabled",
] as const;

function asRecord(value: unknown): JsonRecord | null {
  // 代理只接受 JSON object；数组、字符串等 payload 不进入 UI 摘要。
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonRecord) : null;
}

function asString(value: unknown, fallback = "not_loaded"): string {
  // 展示字段统一截断，避免远端错误页或长路径污染控制台布局。
  return typeof value === "string" && value.trim() ? value.trim().slice(0, 180) : fallback;
}

function isPrivateIpv4(hostname: string): boolean {
  // Robot API 只允许回环或 RFC1918 局域网 IPv4，避免 PC 代理变成公网 SSRF 工具。
  const parts = hostname.split(".").map((part) => Number(part));
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part) || part < 0 || part > 255)) {
    return false;
  }
  const a = parts[0] ?? -1;
  const b = parts[1] ?? -1;
  return a === 10 || a === 127 || (a === 192 && b === 168) || (a === 172 && b >= 16 && b <= 31);
}

export function normalizeRobotApiBaseUrl(baseUrl: string): { ok: true; normalized: URL } | { ok: false; reason: string } {
  // 代理层不自行发明默认地址；前端可传入固定上位机地址，但这里仍只负责校验和规范化。
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    return { ok: false, reason: "baseUrl_not_provided" };
  }
  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return { ok: false, reason: "baseUrl_invalid_url" };
  }
  if (parsed.protocol !== "http:") {
    return { ok: false, reason: "baseUrl_protocol_not_allowed" };
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    return { ok: false, reason: "baseUrl_must_not_include_credentials_query_or_hash" };
  }
  if (
    parsed.hostname !== "localhost" &&
    parsed.hostname !== "::1" &&
    parsed.hostname !== "[::1]" &&
    !isPrivateIpv4(parsed.hostname)
  ) {
    return { ok: false, reason: "baseUrl_must_be_loopback_or_private_lan" };
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  return { ok: true, normalized: parsed };
}

export function endpointUrl(base: URL, endpoint: string): string {
  // 允许 base URL 带只读网关前缀，但 endpoint 仍由白名单提供，operator 不能拼危险路径。
  const next = new URL(base.toString());
  const prefix = next.pathname === "/" ? "" : next.pathname.replace(/\/+$/, "");
  next.pathname = `${prefix}${endpoint}`;
  next.search = "";
  next.hash = "";
  return next.toString();
}

export function scanDangerousTrueFields(
  value: unknown,
  path = "",
  fields: ReadonlySet<string> = DANGEROUS_TRUE_FIELDS,
  exemptTruePaths: ReadonlySet<string> = NO_TRUE_FIELD_EXEMPTIONS,
): string[] {
  // 任意层出现危险 true 字段都进入 blocked reason；PC 端仍固定不放开控制按钮。
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => scanDangerousTrueFields(item, `${path}[${index}]`, fields, exemptTruePaths));
  }
  return Object.entries(value as JsonRecord).flatMap(([key, nested]) => {
    const currentPath = path ? `${path}.${key}` : key;
    // 默认不豁免任何危险字段；只有调用方确认是 operator report claim 时才传精确路径白名单。
    const current = fields.has(key) && nested === true && !exemptTruePaths.has(currentPath) ? [currentPath] : [];
    return current.concat(scanDangerousTrueFields(nested, currentPath, fields, exemptTruePaths));
  });
}

function dangerousTrueFieldExemptionsForEndpoint(id: RobotApiReadEndpointId): ReadonlySet<string> {
  // T=130 只读底盘反馈会标记 sends_commands=true；它不是运动命令，不能把 PC summary 整体打成 blocked。
  if (id === "status") {
    return STATUS_BASE_FEEDBACK_TRUE_FIELD_EXEMPTIONS;
  }
  if (id === "base_status") {
    return BASE_STATUS_FEEDBACK_TRUE_FIELD_EXEMPTIONS;
  }
  if (id === "base_feedback_samples_latest") {
    return BASE_FEEDBACK_SAMPLES_TRUE_FIELD_EXEMPTIONS;
  }
  if (id === "operator_report_latest") {
    return OPERATOR_REPORT_CLAIM_TRUE_FIELD_EXEMPTIONS;
  }
  if (id === "nav2_goal_execution_latest") {
    return NAV2_GOAL_EXECUTION_LATEST_TRUE_FIELD_EXEMPTIONS;
  }
  return NO_TRUE_FIELD_EXEMPTIONS;
}

function notLoadedHilMaterialSummary(status: RobotControlOperatorHilMaterialSummary["status"]): RobotControlOperatorHilMaterialSummary {
  // 摘要只用于高级诊断；默认值保持材料缺失，不外推 HIL、delivery 或 safe control。
  return {
    status,
    source_endpoint_id: "operator_report_latest",
    source_path: "operator_report_latest.structured_hil_claims",
    report_status: "not_loaded",
    evidence_ref: "not_loaded",
    operator_present: "not_loaded",
    physical_clearance: "not_loaded",
    emergency_stop: "not_loaded",
    external_video: "not_loaded",
    camera_visible: "not_loaded",
    wheel_feedback: "not_loaded",
    lidar_delta: "not_loaded",
    route_map: "not_loaded",
    delivery_claim: "not_loaded",
    site_state: "not_loaded",
  };
}

function blockedOperatorReportPreflight(
  reason: string,
  materialSummary: RobotControlOperatorHilMaterialSummary = notLoadedHilMaterialSummary("not_loaded"),
  requestStatus: RobotControlOperatorReportPreflight["request_status"] = "blocked",
  httpStatus: number | null = null,
  hardDangerousTrueFields: string[] = [],
): RobotControlOperatorReportPreflight {
  // 点动 preflight 的拒绝态必须列出完整缺项，便于 artifact 证明本机没有调用 /api/base/manual。
  return {
    status: "blocked",
    source_endpoint: OPERATOR_REPORT_REMOTE_ENDPOINT,
    request_status: requestStatus,
    http_status: httpStatus,
    report_status: materialSummary.report_status,
    evidence_ref: materialSummary.evidence_ref,
    required_fields: [...ROBOT_CONTROL_OPERATOR_REPORT_PREFLIGHT_REQUIRED_FIELDS],
    missing_fields: [...ROBOT_CONTROL_OPERATOR_REPORT_PREFLIGHT_REQUIRED_FIELDS],
    material_summary: materialSummary,
    failure_reason: reason,
    hard_dangerous_true_fields: hardDangerousTrueFields,
  };
}

export function notRequiredOperatorReportPreflight(): RobotControlOperatorReportPreflight {
  // stop 是 fail-safe，不能因为现场材料缺失而阻断；但响应仍显式记录没有做点动 preflight。
  return {
    status: "not_required_for_stop",
    source_endpoint: OPERATOR_REPORT_REMOTE_ENDPOINT,
    request_status: "not_required",
    http_status: null,
    report_status: "not_required_for_stop",
    evidence_ref: "not_required_for_stop",
    required_fields: [...ROBOT_CONTROL_OPERATOR_REPORT_PREFLIGHT_REQUIRED_FIELDS],
    missing_fields: [],
    material_summary: notLoadedHilMaterialSummary("not_loaded"),
    failure_reason: "",
    hard_dangerous_true_fields: [],
  };
}

export function notRequiredConfirmedManualOperatorReportPreflight(): RobotControlOperatorReportPreflight {
  // 最新普通首屏口径：非 stop 手控只要求本地安全确认，operator report 材料不再阻塞低速脉冲。
  return {
    ...notRequiredOperatorReportPreflight(),
    status: "not_required_for_confirmed_manual",
    report_status: "not_required_for_confirmed_manual",
    evidence_ref: "not_required_for_confirmed_manual",
    required_fields: [],
  };
}

function notRequiredNav2OperatorReportPreflight(): RobotControlOperatorReportPreflight {
  // Nav2 发车前预检按最新产品口径只要求本地安全确认；operator report 材料不再阻塞导航预检。
  return {
    ...notRequiredOperatorReportPreflight(),
    status: "not_required_for_nav2_minimal_safety_precheck",
    report_status: "not_required_for_nav2_minimal_safety_precheck",
    evidence_ref: "not_required_for_nav2_minimal_safety_precheck",
  };
}

function boolText(value: unknown): string {
  // claim 布尔值必须原样标成 true/false，不能提升成 proof/pass 文案。
  return typeof value === "boolean" ? String(value) : "not_loaded";
}

function claimWithRef(claim: unknown, ref: unknown): string {
  // 每个现场材料都带引用，便于 operator 追溯原始视频、日志或地图产物。
  const refText = asString(ref, "not_loaded");
  return `${boolText(claim)}; ref=${refText}`;
}

function operatorReportRecord(payload: JsonRecord | null): JsonRecord | null {
  // 真实板端可能把 report 包在 latest_result.operator_report；这里只在 report 端点 payload 内找同源记录。
  if (!payload) {
    return null;
  }
  const latestResult = asRecord(payload.latest_result);
  const nestedReport = asRecord(latestResult?.operator_report);
  if (nestedReport) {
    return nestedReport;
  }
  if (asRecord(payload.structured_hil_claims) || payload.operator_present !== undefined) {
    return payload;
  }
  if (latestResult && (asRecord(latestResult.structured_hil_claims) || latestResult.operator_present !== undefined)) {
    return latestResult;
  }
  return payload;
}

function operatorReportClaims(report: JsonRecord | null, payload: JsonRecord | null): JsonRecord | null {
  // claims 优先跟随同一个 operator_report 记录，找不到时才兼容旧顶层 structured_hil_claims。
  return asRecord(report?.structured_hil_claims) ?? asRecord(payload?.structured_hil_claims) ?? asRecord(findFirstKey(payload, ["structured_hil_claims"]));
}

function buildOperatorHilMaterialSummaryFromPayload(payload: JsonRecord | null): RobotControlOperatorHilMaterialSummary {
  // 只消费 /api/operator/report 的 structured_hil_claims，不从其它 readback 猜 HIL 状态。
  if (!payload) {
    return notLoadedHilMaterialSummary("not_loaded");
  }
  const report = operatorReportRecord(payload);
  const claims = operatorReportClaims(report, payload);
  const reportStatus = asString(findFirstKey(report, ["operator_report_status"]) ?? findFirstKey(payload, ["operator_report_status"]) ?? findFirstKey(payload, ["status"]), "not_loaded");
  if (!claims) {
    return {
      ...notLoadedHilMaterialSummary("missing"),
      report_status: reportStatus,
      evidence_ref: asString(findFirstKey(report, ["evidence_ref", "latest_evidence_ref"]) ?? findFirstKey(payload, ["evidence_ref", "latest_evidence_ref"]), "not_loaded"),
      operator_present: boolText(report?.operator_present),
      physical_clearance: boolText(report?.physical_clearance_confirmed),
      emergency_stop: boolText(report?.emergency_stop_ready),
    };
  }
  return {
    status: "loaded",
    source_endpoint_id: "operator_report_latest",
    source_path: "operator_report_latest.structured_hil_claims",
    report_status: reportStatus,
    evidence_ref: asString(findFirstKey(report, ["evidence_ref", "latest_evidence_ref"]) ?? findFirstKey(payload, ["evidence_ref", "latest_evidence_ref"]), "not_loaded"),
    operator_present: boolText(report?.operator_present),
    physical_clearance: boolText(report?.physical_clearance_confirmed),
    emergency_stop: boolText(report?.emergency_stop_ready),
    external_video: claimWithRef(claims.external_video_recorded, claims.external_video_ref),
    camera_visible: claimWithRef(claims.visible_content_proven, claims.camera_artifacts_ref),
    wheel_feedback: claimWithRef(claims.wheel_feedback_lr_nonzero_proven, claims.wheel_feedback_ref),
    lidar_delta: claimWithRef(claims.physical_motion_lidar_delta_proven, claims.scan_delta_ref),
    route_map: claimWithRef(claims.real_route_map_proven, claims.route_map_ref),
    delivery_claim: boolText(claims.delivery_success),
    site_state: asString(claims.site_state, "not_loaded"),
  };
}

function buildOperatorHilMaterialSummary(
  readbacks: InternalRobotApiEndpointReadback[],
): RobotControlOperatorHilMaterialSummary {
  // summary 只接受固定 operator_report_latest endpoint 的 payload，避免其它端点伪造同名 claim。
  const operatorReadback = readbacks.find((item) => item.id === "operator_report_latest");
  return buildOperatorHilMaterialSummaryFromPayload(operatorReadback?.payload ?? null);
}

function textPresent(value: unknown): boolean {
  // ref 必须是非空字符串；布尔 true 不能替代可追溯材料路径。
  return typeof value === "string" && value.trim().length > 0;
}

export function buildOperatorReportPreflightFromPayload(
  payload: JsonRecord | null,
  httpStatus: number | null,
  requestStatus: RobotControlOperatorReportPreflight["request_status"],
): RobotControlOperatorReportPreflight {
  // 点动 gate 同时要求“人在现场”和“可复核材料引用”，delivery_success 不参与放行。
  const materialSummary = buildOperatorHilMaterialSummaryFromPayload(payload);
  if (!payload || requestStatus !== "loaded") {
    return blockedOperatorReportPreflight("operator_report_preflight_required", materialSummary, requestStatus, httpStatus);
  }
  const hardDangerous = scanDangerousTrueFields(
    payload,
    "",
    HARD_DANGEROUS_TRUE_FIELDS,
    OPERATOR_REPORT_CLAIM_TRUE_FIELD_EXEMPTIONS,
  );
  const report = operatorReportRecord(payload);
  const claims = operatorReportClaims(report, payload);
  const missingFields = [
    report?.operator_present === true ? "" : "operator_present",
    report?.physical_clearance_confirmed === true ? "" : "physical_clearance_confirmed",
    report?.emergency_stop_ready === true ? "" : "emergency_stop_ready",
    claims?.external_video_recorded === true ? "" : "external_video_recorded",
    textPresent(claims?.external_video_ref) ? "" : "external_video_ref",
    claims?.visible_content_proven === true ? "" : "visible_content_proven",
    textPresent(claims?.camera_artifacts_ref) ? "" : "camera_artifacts_ref",
    claims?.wheel_feedback_lr_nonzero_proven === true ? "" : "wheel_feedback_lr_nonzero_proven",
    textPresent(claims?.wheel_feedback_ref) ? "" : "wheel_feedback_ref",
    claims?.physical_motion_lidar_delta_proven === true ? "" : "physical_motion_lidar_delta_proven",
    textPresent(claims?.scan_delta_ref) ? "" : "scan_delta_ref",
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
  ].filter(Boolean);
  return {
    status: missingFields.length ? "blocked" : "passed",
    source_endpoint: OPERATOR_REPORT_REMOTE_ENDPOINT,
    request_status: requestStatus,
    http_status: httpStatus,
    report_status: materialSummary.report_status,
    evidence_ref: materialSummary.evidence_ref,
    required_fields: [...ROBOT_CONTROL_OPERATOR_REPORT_PREFLIGHT_REQUIRED_FIELDS],
    missing_fields: missingFields,
    material_summary: materialSummary,
    failure_reason: missingFields.length ? "operator_report_preflight_required" : "",
    hard_dangerous_true_fields: hardDangerous,
  };
}

export function buildFirstJogOperatorReportPreflightFromPayload(
  payload: JsonRecord | null,
  httpStatus: number | null,
  requestStatus: RobotControlOperatorReportPreflight["request_status"],
): RobotControlOperatorReportPreflight {
  // 首次试动的轮速和 LiDAR delta 是输出证据，不能作为第一次试动的前置死锁条件。
  const materialSummary = buildOperatorHilMaterialSummaryFromPayload(payload);
  if (!payload || requestStatus !== "loaded") {
    return {
      ...blockedOperatorReportPreflight("first_jog_preflight_required", materialSummary, requestStatus, httpStatus),
      required_fields: [...ROBOT_CONTROL_FIRST_JOG_PREFLIGHT_REQUIRED_FIELDS],
      missing_fields: [...ROBOT_CONTROL_FIRST_JOG_PREFLIGHT_REQUIRED_FIELDS],
    };
  }
  const hardDangerous = scanDangerousTrueFields(
    payload,
    "",
    HARD_DANGEROUS_TRUE_FIELDS,
    OPERATOR_REPORT_CLAIM_TRUE_FIELD_EXEMPTIONS,
  );
  const report = operatorReportRecord(payload);
  const claims = operatorReportClaims(report, payload);
  const externalVideoReady = claims?.external_video_recorded === true && textPresent(claims.external_video_ref);
  const cameraVisibleReady = claims?.visible_content_proven === true && textPresent(claims.camera_artifacts_ref);
  const missingFields = [
    report?.operator_present === true ? "" : "operator_present",
    report?.physical_clearance_confirmed === true ? "" : "physical_clearance_confirmed",
    report?.emergency_stop_ready === true ? "" : "emergency_stop_ready",
    externalVideoReady || cameraVisibleReady ? "" : "external_video_or_visible_camera",
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
  ].filter(Boolean);
  return {
    status: missingFields.length ? "blocked" : "passed",
    source_endpoint: OPERATOR_REPORT_REMOTE_ENDPOINT,
    request_status: requestStatus,
    http_status: httpStatus,
    report_status: materialSummary.report_status,
    evidence_ref: materialSummary.evidence_ref,
    required_fields: [...ROBOT_CONTROL_FIRST_JOG_PREFLIGHT_REQUIRED_FIELDS],
    missing_fields: missingFields,
    material_summary: materialSummary,
    failure_reason: missingFields.length ? "first_jog_preflight_required" : "",
    hard_dangerous_true_fields: hardDangerous,
  };
}

function findFirstKey(value: unknown, keys: string[], depth = 0): unknown {
  // Robot API proof 字段可能位于 latest_result/proof/status 多层结构；递归只读查找但限制深度。
  if (!value || typeof value !== "object" || depth > 6) {
    return undefined;
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findFirstKey(item, keys, depth + 1);
      if (found !== undefined) {
        return found;
      }
    }
    return undefined;
  }
  const record = value as JsonRecord;
  for (const key of keys) {
    if (record[key] !== undefined) {
      return record[key];
    }
  }
  for (const nested of Object.values(record)) {
    const found = findFirstKey(nested, keys, depth + 1);
    if (found !== undefined) {
      return found;
    }
  }
  return undefined;
}

function stringList(value: unknown, limit = 8): string[] {
  // root_causes/not_proven 只做短摘要；对象原因压缩成 JSON 片段用于排障。
  if (!Array.isArray(value)) {
    return [];
  }
  return value.slice(0, limit).map((item) => {
    if (typeof item === "string") {
      return item.slice(0, 180);
    }
    if (item && typeof item === "object") {
      return JSON.stringify(item).slice(0, 180);
    }
    return String(item).slice(0, 180);
  });
}

function nav2ProofBlockerReasons(value: unknown, limit = 8): string[] {
  // Nav2 proof.blockers 是当前不能自动驾驶的最直接读数；优先保留 reason，再补 detail。
  const rawBlockers = findFirstKey(value, ["blockers", "blocked_reasons", "root_causes"]);
  if (!Array.isArray(rawBlockers)) {
    return [];
  }
  const reasons: string[] = [];
  for (const item of rawBlockers) {
    if (typeof item === "string") {
      reasons.push(item);
    } else if (item && typeof item === "object") {
      const record = item as JsonRecord;
      const reason = compactValueText(record.reason, 160);
      const detail = compactValueText(record.detail, 160);
      if (reason && reason !== "undefined") {
        reasons.push(reason);
      }
      if (detail && detail !== "undefined") {
        reasons.push(detail);
      }
    }
  }
  return [...new Set(reasons.filter(Boolean))].slice(0, limit);
}

function nav2ProofBlockerLabels(reasons: string[]): string[] {
  // 普通首屏不显示 raw proof 对象，但保留 ROS topic/TF 名称，方便现场按真实根因排查。
  const labels = reasons.map((reason) => {
    if (reason === "/scan_once_not_observed" || reason === "scan_once_not_observed") {
      return "未读到 /scan";
    }
    if (reason === "/amcl_pose_once_not_observed" || reason === "amcl_pose_once_not_observed") {
      return "未读到 /amcl_pose";
    }
    if (reason === "map_to_odom_not_observed") {
      return "未读到 map->odom TF";
    }
    if (reason === "map_to_base_link_blocked_by_missing_map_to_odom") {
      return "缺 map->odom，无法得到小车地图坐标";
    }
    if (reason === "amcl_map_to_odom_tf_not_observed_on_tf") {
      return "AMCL 没有发布 map->odom";
    }
    if (reason === "localization_not_ready_for_path_generation") {
      return "定位未 ready，无法生成图上路线";
    }
    if (reason === "planner_server_inactive") {
      return "规划服务未运行";
    }
    if (reason === "controller_server_inactive") {
      return "控制服务未运行";
    }
    if (reason === "nav2_map_not_consumed") {
      return "地图未被自动驾驶服务消费";
    }
    if (reason === "path_generation_service_unavailable") {
      return "路径生成服务不可用";
    }
    if (reason === "path_generation_not_attempted") {
      return "路径生成还没真正开始";
    }
    if (reason === "nav2_lifecycle_not_running") {
      return "自动驾驶 lifecycle 未运行";
    }
    if (reason === "nav2_stack_not_running") {
      return "自动驾驶服务未启动";
    }
    return reason;
  });
  return [...new Set(labels)].slice(0, 8);
}

function numberList(value: unknown, limit = 8): number[] {
  // origin 这类短数组只保留有限数值，避免异常 payload 进入前端计算。
  if (!Array.isArray(value)) {
    return [];
  }
  return value.slice(0, limit).flatMap((item) => (typeof item === "number" && Number.isFinite(item) ? [item] : []));
}

function compactValueText(value: unknown, limit = 120): string {
  // 上位机 root_causes/localization_tf 等字段常是 object/array；不能退化成 [object Object]。
  if (typeof value === "string") {
    return value.slice(0, limit);
  }
  if (typeof value === "number" || typeof value === "boolean" || value === null) {
    return String(value).slice(0, limit);
  }
  if (value && typeof value === "object") {
    try {
      return JSON.stringify(value).slice(0, limit);
    } catch {
      return "json_value_unserializable";
    }
  }
  return String(value).slice(0, limit);
}

function compactKeyValues(payload: JsonRecord | null, keys: readonly string[] = STATUS_KEYS): Record<string, string> {
  // 关键字段白名单足够支撑控制台判断，不透传完整上位机 payload。
  const entries = keys.flatMap((key) => {
    const found = findFirstKey(payload, [key]);
    return found === undefined ? [] : [[key, compactValueText(found)] as const];
  });
  const result = Object.fromEntries(entries);
  appendFreshBaseFeedbackFrameCount(payload, result, keys);
  appendWheelFeedbackSummaryKeyValues(payload, result, keys);
  appendBaseFeedbackVoltageKeyValue(payload, result, keys);
  appendFeedbackSamplesFreshnessKeyValues(payload, result, keys);
  return result;
}

function appendFreshBaseFeedbackFrameCount(payload: JsonRecord | null, result: Record<string, string>, keys: readonly string[]): void {
  // /api/base/status 内的 feedback_readback 是本次 fresh 读数；优先于可能 stale 的 feedback_samples_latest。
  if (!keys.includes("latest_t1001_observed_count")) {
    return;
  }
  const feedbackReadback = asRecord(findFirstKey(payload, ["feedback_readback"]));
  const feedbackFrames = feedbackReadback?.t1001_feedback_frames;
  const wheelSummary = asRecord(feedbackReadback?.wheel_feedback_summary);
  const frameCount = feedbackReadback?.t1001_feedback_frame_count
    ?? (Array.isArray(feedbackFrames) ? feedbackFrames.length : undefined)
    ?? wheelSummary?.frame_count;
  if (typeof frameCount === "number" || typeof frameCount === "string") {
    result.latest_t1001_observed_count = compactValueText(frameCount);
  }
}

function appendWheelFeedbackSummaryKeyValues(payload: JsonRecord | null, result: Record<string, string>, keys: readonly string[]): void {
  // 真实上位机把 L/R 放在 wheel_feedback_summary.latest_pair；这里同时派生 speed/raw 两套别名，避免 UI 和脚本口径割裂。
  const wheelSummary = asRecord(findFirstKey(payload, ["wheel_feedback_summary"]));
  if (!wheelSummary) {
    return;
  }
  const latestPair = asRecord(wheelSummary.latest_pair);
  const latestNonzeroPair = asRecord(wheelSummary.latest_nonzero_pair);
  const fill = (key: string, value: unknown): void => {
    if (!keys.includes(key) || result[key] !== undefined || value === undefined) {
      return;
    }
    result[key] = compactValueText(value);
  };
  fill("wheel_feedback_latest_left_speed", latestPair?.left_speed);
  fill("wheel_feedback_latest_right_speed", latestPair?.right_speed);
  fill("wheel_feedback_latest_raw_left", latestPair?.left_speed);
  fill("wheel_feedback_latest_raw_right", latestPair?.right_speed);
  fill("left_speed", latestPair?.left_speed);
  fill("right_speed", latestPair?.right_speed);
  fill("wheel_feedback_nonzero_frame_count", wheelSummary.nonzero_frame_count);
  fill("wheel_feedback_frame_count", wheelSummary.frame_count);
  fill("wheel_feedback_source", latestPair?.source ?? wheelSummary.source);
  fill("wheel_feedback_latest_nonzero_left_speed", latestNonzeroPair?.left_speed);
  fill("wheel_feedback_latest_nonzero_right_speed", latestNonzeroPair?.right_speed);
}

function appendBaseFeedbackVoltageKeyValue(payload: JsonRecord | null, result: Record<string, string>, keys: readonly string[]): void {
  // WAVE ROVER T1001 帧里的 v 只用于现场供电排查展示，不能作为运动或 HIL 证明。
  if (!keys.includes("feedback_voltage_v") || result.feedback_voltage_v !== undefined) {
    return;
  }
  const frames = findFirstKey(payload, ["t1001_feedback_frames"]);
  if (!Array.isArray(frames)) {
    return;
  }
  const latestFrame = [...frames].reverse().find((frame) => asRecord(frame)?.v !== undefined);
  const voltage = asRecord(latestFrame)?.v;
  if (typeof voltage === "number" || typeof voltage === "string") {
    result.feedback_voltage_v = compactValueText(voltage);
  }
}

function appendFeedbackSamplesFreshnessKeyValues(payload: JsonRecord | null, result: Record<string, string>, keys: readonly string[]): void {
  // samples latest 可能是历史文件；把 freshness 只作为排障提示，不提升轮速或 HIL 证明。
  if (!keys.includes("feedback_samples_freshness_status") && !keys.includes("feedback_samples_age_ms")) {
    return;
  }
  const freshness = asRecord(findFirstKey(payload, ["freshness"]));
  if (!freshness) {
    return;
  }
  if (keys.includes("feedback_samples_freshness_status") && result.feedback_samples_freshness_status === undefined && freshness.status !== undefined) {
    result.feedback_samples_freshness_status = compactValueText(freshness.status);
  }
  if (keys.includes("feedback_samples_age_ms") && result.feedback_samples_age_ms === undefined && freshness.age_ms !== undefined) {
    result.feedback_samples_age_ms = compactValueText(freshness.age_ms);
  }
}

function summaryValueText(payload: JsonRecord | null, keys: string[], fallback = "not_loaded"): string {
  // summary 既要保留字符串状态，也要保留布尔 continuity/lifecycle 结论，因此统一转成短文本。
  const found = findFirstKey(payload, keys);
  return found === undefined ? fallback : compactValueText(found);
}

function cameraFormatAttemptsSummary(lastOfferError: JsonRecord | null): string {
  // 相机首帧失败时，把上车端逐格式尝试压成短文本，普通首屏不用展开 raw JSON 也能看到真实失败范围。
  const attempts = Array.isArray(lastOfferError?.first_frame_format_attempts)
    ? lastOfferError.first_frame_format_attempts
    : [];
  const parts = attempts
    .map((item) => asRecord(item))
    .filter((item): item is JsonRecord => item !== null)
    .map((attempt) => {
      const fourcc = asString(attempt.label ?? attempt.fourcc, "unknown");
      const status = asString(attempt.status, "unknown");
      if (status === "frame_read") {
        return `${fourcc} 已出帧`;
      }
      if (status === "open_failed") {
        return `${fourcc} 打不开`;
      }
      if (status === "first_frame_unreadable") {
        return `${fourcc} 无首帧`;
      }
      return `${fourcc} ${status}`;
    })
    .filter(Boolean)
    .slice(0, 6);
  return parts.length > 0 ? parts.join("；") : "none";
}

function cameraDisplayDeviceName(value: unknown): string {
  // v4l2 名称常带 `(usb-5310000...)` 这种总线尾巴，普通首屏只需要稳定设备名。
  const text = asString(value)
    .replace(/\s+\(usb-[^)]+\)\s*$/i, "")
    .replace(/\s{2,}/g, " ")
    .trim();
  return text && !["not_loaded", "none", "unknown", "null"].includes(text) ? text : "";
}

function cameraDiagnosisPlainHint(value: unknown, fallbackDeviceName = "UVC 设备"): string {
  // 共享 relay 可能只知道“not_loaded 当前没人占用”；summary 要保留诊断事实，但不能把占位词暴露给普通 UI。
  const hint = asString(value, "").trim();
  if (!hint || ["not_loaded", "none", "unknown", "null"].includes(hint)) {
    return hint;
  }
  const displayName = cameraDisplayDeviceName(fallbackDeviceName);
  const deviceName = displayName && displayName !== "摄像头" ? displayName : "UVC 设备";
  return hint.replace(/：(not_loaded|none|unknown|null|摄像头|USB 摄像头)\s*当前没人占用/g, `：${cameraOwnerFreeText(deviceName)}`);
}

function cameraOwnerFreeText(selectedName: string): string {
  // 英文设备型号后接中文时保留一个空格；中文泛称直接连接，避免“摄像头 当前”这种断裂文案。
  return /[A-Za-z0-9]$/.test(selectedName) ? `${selectedName} 当前没人占用` : `${selectedName}当前没人占用`;
}

function cameraSummaryPreviewGuidance(
  previewStatus: RobotControlSummaryResponse["readback_summary"]["camera"]["preview_status"],
  sourceFirstFrameFailed: boolean,
  sourceDiagnosis: { plain_hint: string; next_action: string; next_action_plain?: string },
): { plain_hint: string; next_action: string; next_action_plain: string } {
  // summary 是普通首屏的主入口；这里把高级诊断压成“现在有没有画面”和“下一步”。
  if (previewStatus === "streaming") {
    return {
      plain_hint: "共享实时画面已有缓存帧，多个页面复用同一条上游流。",
      next_action: "continue_monitoring_shared_preview",
      next_action_plain: "继续监看共享实时画面。",
    };
  }
  if (sourceFirstFrameFailed) {
    const plainHint = sourceDiagnosis.plain_hint && !["not_loaded", "none"].includes(sourceDiagnosis.plain_hint)
      ? sourceDiagnosis.plain_hint
      : "不是页面独占：UVC 设备没有输出视频帧。";
    const nextAction = sourceDiagnosis.next_action && !["not_loaded", "none"].includes(sourceDiagnosis.next_action)
      ? sourceDiagnosis.next_action
      : "check_usb_camera_input_power_or_known_good_uvc";
    const nextActionPlain = sourceDiagnosis.next_action_plain && !["not_loaded", "none"].includes(sourceDiagnosis.next_action_plain)
      ? sourceDiagnosis.next_action_plain
      : cameraActionPlainText(nextAction);
    return { plain_hint: plainHint, next_action: nextAction, next_action_plain: nextActionPlain };
  }
  if (["starting_local_peer", "connecting_offer_posted"].includes(previewStatus)) {
    return {
      plain_hint: "共享实时画面正在等待首帧；返回前不能把黑框当作画面可见。",
      next_action: "wait_or_run_first_frame_probe",
      next_action_plain: "等待首帧，必要时点只读检查复测画面。",
    };
  }
  if (previewStatus === "start_failed" || previewStatus === "peer_cleanup_failed") {
    return {
      plain_hint: "共享实时画面打开或清理失败；先看失败原因，再重试共享预览。",
      next_action: "inspect_shared_preview_failure_and_retry",
      next_action_plain: "查看共享预览失败原因后再重试。",
    };
  }
  return {
    plain_hint: "页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。",
    next_action: "auto_join_shared_mjpeg_preview",
    next_action_plain: "打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。",
  };
}

function cameraActionPlainText(action: string): string {
  // 上车端和 PC relay 仍保留短 token；summary 额外给普通用户能直接执行的下一步。
  const value = action.trim();
  if (!value || value === "not_loaded" || value === "none") {
    return "";
  }
  if (value === "check_usb_camera_input_power_or_known_good_uvc") {
    return "检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。";
  }
  if (value === "continue_monitoring_shared_preview") {
    return "继续监看共享实时画面。";
  }
  if (value === "auto_join_shared_mjpeg_preview") {
    return "打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。";
  }
  if (value === "open_shared_preview_when_needed" || value === "open_shared_preview_or_run_first_frame_probe") {
    return "需要看画面时打开共享预览，或点只读检查复测首帧。";
  }
  if (value === "wait_or_run_first_frame_probe") {
    return "等待首帧，必要时点只读检查复测画面。";
  }
  if (value === "inspect_shared_preview_failure_and_retry") {
    return "查看共享预览失败原因后再重试。";
  }
  if (value === "check_robot_api_base_url_and_retry") {
    return "确认小车地址可访问后重试共享预览状态。";
  }
  return `${value.replace(/_/g, " ")}。`;
}

function cameraPreviewVisibilityPlainSummary(args: {
  previewStatus: RobotControlSummaryResponse["readback_summary"]["camera"]["preview_status"];
  sourceFirstFrameFailed: boolean;
  previewPlainHint: string;
  previewNextActionPlain: string;
}): { visibleStatus: string; visiblePlain: string; wysiwygStatusPlain: string; wysiwygNextActionPlain: string } {
  // 共享 relay 的连接状态不等于画面已经可见；这里给脚本一个直接的所见即所得结论。
  if (args.previewStatus === "streaming") {
    return {
      visibleStatus: "visible_cached_frame",
      visiblePlain: "当前有共享实时画面缓存帧；新页面复用同一条上游流。",
      wysiwygStatusPlain: "画面已可见：共享实时画面已有缓存帧，多个页面复用同一条上游流。",
      wysiwygNextActionPlain: "继续监看共享实时画面。",
    };
  }
  if (args.sourceFirstFrameFailed) {
    return {
      visibleStatus: "not_visible_source_first_frame_failed",
      visiblePlain: `当前没有实时画面；${args.previewPlainHint}`,
      wysiwygStatusPlain: `画面未可见：${args.previewPlainHint}`,
      wysiwygNextActionPlain: args.previewNextActionPlain,
    };
  }
  if (args.previewStatus === "starting_local_peer" || args.previewStatus === "connecting_offer_posted") {
    return {
      visibleStatus: "waiting_for_first_frame",
      visiblePlain: "正在等待共享实时画面首帧；返回前不能把黑框当作画面可见。",
      wysiwygStatusPlain: "画面未证明可见：共享实时画面正在等待首帧。",
      wysiwygNextActionPlain: args.previewNextActionPlain,
    };
  }
  if (args.previewStatus === "start_failed" || args.previewStatus === "peer_cleanup_failed") {
    return {
      visibleStatus: "not_visible_preview_failed",
      visiblePlain: `当前没有实时画面；${args.previewPlainHint}`,
      wysiwygStatusPlain: `画面未可见：${args.previewPlainHint}`,
      wysiwygNextActionPlain: args.previewNextActionPlain,
    };
  }
  return {
    visibleStatus: "not_visible_idle",
    visiblePlain: `当前没有实时画面；${args.previewPlainHint}`,
    wysiwygStatusPlain: `画面未可见：${args.previewPlainHint}`,
    wysiwygNextActionPlain: args.previewNextActionPlain,
  };
}

function cameraDeviceCandidateRole(candidate: JsonRecord | null): string {
  // devices 端点只有布尔能力字段时，PC 也要给普通用户稳定的“这是画面节点还是元数据节点”。
  const explicitRole = asString(candidate?.selected_role ?? candidate?.role, "");
  if (explicitRole) {
    return explicitRole;
  }
  if (candidate?.is_metadata === true) {
    return "metadata";
  }
  if (candidate?.is_decoder === true) {
    return "decoder";
  }
  if (candidate?.is_video_capture === true) {
    return "video_capture";
  }
  return "";
}

function cameraDeviceCandidateName(candidate: JsonRecord | null): string {
  // v4l2_name 最容易把同一 USB 复合设备的 capture/metadata 节点归到一起。
  return cameraDisplayDeviceName(candidate?.v4l2_name ?? candidate?.sysfs_name ?? candidate?.name);
}

function cameraSelectedCandidateFromDevices(devicesPayload: JsonRecord | null, selectedPath: string): JsonRecord {
  // live 上车端有时 health 缺少 sibling 字段，但 devices 只读枚举里能看出同一 UVC 的兄弟节点。
  const sourceCandidates = asRecord(findFirstKey(devicesPayload, ["source_candidates", "source_candidates_summary"]));
  const candidates = Array.isArray(sourceCandidates?.candidates) ? sourceCandidates.candidates : [];
  const records = candidates
    .map((candidate) => asRecord(candidate))
    .filter((candidate): candidate is JsonRecord => candidate !== null);
  const selected = records.find((candidate) => asString(candidate.path ?? candidate.realpath, "") === selectedPath) ?? null;
  if (!selected) {
    return {};
  }
  const selectedName = cameraDeviceCandidateName(selected);
  const siblings = records
    .filter((candidate) => asString(candidate.path ?? candidate.realpath, "") !== selectedPath)
    .filter((candidate) => {
      const candidateName = cameraDeviceCandidateName(candidate);
      return selectedName && candidateName === selectedName;
    })
    .map((candidate) => {
      const path = asString(candidate.path ?? candidate.realpath, "");
      const role = cameraDeviceCandidateRole(candidate) || "unknown";
      return path ? `${path}=${role}` : "";
    })
    .filter(Boolean)
    .slice(0, 4);
  return {
    selected_name: selectedName,
    selected_formats_summary: asString(selected.formats_summary),
    selected_is_uvc_or_usb: selected.is_uvc_or_usb,
    selected_role: cameraDeviceCandidateRole(selected),
    selected_sibling_video_nodes_summary: siblings.length ? siblings.join("；") : "none",
    selected_sibling_video_node_count: siblings.length,
  };
}

function mergeCameraCandidateSummary(primary: JsonRecord, fallback: JsonRecord): JsonRecord {
  // health 是权威选择；devices 只补 health 缺失的 role/sibling/格式，不反向覆盖已给出的事实。
  const primarySiblingSummary = asString(primary.selected_sibling_video_nodes_summary, "");
  const primarySiblingCount = primary.selected_sibling_video_node_count;
  const primarySiblingMissing = !primarySiblingSummary
    || primarySiblingSummary === "none"
    || primarySiblingCount === 0;
  return {
    selected_name: asString(primary.selected_name, "") || asString(fallback.selected_name, ""),
    selected_formats_summary: asString(primary.selected_formats_summary, "") || asString(fallback.selected_formats_summary, ""),
    selected_is_uvc_or_usb: primary.selected_is_uvc_or_usb ?? fallback.selected_is_uvc_or_usb,
    selected_role: asString(primary.selected_role, "") || asString(fallback.selected_role, ""),
    selected_sibling_video_nodes_summary: primarySiblingMissing
      ? asString(fallback.selected_sibling_video_nodes_summary, "") || primarySiblingSummary
      : primarySiblingSummary,
    selected_sibling_video_node_count: primarySiblingMissing
      ? fallback.selected_sibling_video_node_count ?? primarySiblingCount
      : primarySiblingCount,
  };
}

function cameraSelectedCandidateSummary(healthPayload: JsonRecord | null, devicesPayload: JsonRecord | null): JsonRecord {
  // 设备名和格式摘要来自上车端只读 health/devices，PC 只做压缩展示，不重新枚举或打开摄像头。
  const sourceSummary = asRecord(findFirstKey(healthPayload, ["source_summary", "source_candidates_summary"]));
  const currentSelection = asRecord(findFirstKey(healthPayload, ["current_selection"]));
  const summarySelection = asRecord(sourceSummary?.current_selection);
  const selectedPath = asString(currentSelection?.selected_path ?? summarySelection?.selected_path ?? healthPayload?.video_source, "");
  const selectedName = asString(currentSelection?.selected_name ?? summarySelection?.selected_name, "");
  const selectedFormats = asString(currentSelection?.selected_formats_summary ?? summarySelection?.selected_formats_summary, "");
  const selectedIsUvc = currentSelection?.selected_is_uvc_or_usb ?? summarySelection?.selected_is_uvc_or_usb;
  const selectedRole = asString(currentSelection?.selected_role ?? summarySelection?.selected_role, "");
  const siblingNodesSummary = asString(currentSelection?.selected_sibling_video_nodes_summary ?? summarySelection?.selected_sibling_video_nodes_summary, "");
  const siblingNodesCount = currentSelection?.selected_sibling_video_node_count ?? summarySelection?.selected_sibling_video_node_count;
  const devicesFallback = cameraSelectedCandidateFromDevices(devicesPayload, selectedPath);
  if (selectedName || selectedFormats || selectedIsUvc !== undefined || selectedRole || siblingNodesSummary || siblingNodesCount !== undefined) {
    return mergeCameraCandidateSummary({
      selected_name: selectedName,
      selected_formats_summary: selectedFormats,
      selected_is_uvc_or_usb: selectedIsUvc,
      selected_role: selectedRole,
      selected_sibling_video_nodes_summary: siblingNodesSummary,
      selected_sibling_video_node_count: siblingNodesCount,
    }, devicesFallback);
  }
  const candidates = Array.isArray(sourceSummary?.candidates) ? sourceSummary.candidates : [];
  const selectedCandidate = candidates
    .map((candidate) => asRecord(candidate))
    .find((candidate) => asString(candidate?.path) === selectedPath);
  return mergeCameraCandidateSummary({
    selected_name: asString(selectedCandidate?.name, ""),
    selected_formats_summary: asString(selectedCandidate?.formats_summary, ""),
    selected_is_uvc_or_usb: selectedCandidate?.is_uvc_or_usb,
    selected_role: asString(selectedCandidate?.selected_role, ""),
    selected_sibling_video_nodes_summary: "none",
    selected_sibling_video_node_count: 0,
  }, devicesFallback);
}

function radarScanProofReadbackPayload(payload: JsonRecord | null): JsonRecord | null {
  // 上位机 refresh 回包可能同时包含本轮 collector 直接结果和随后读取的 radar status；
  // PC 控制台必须只用最终 scan proof readback 做摘要，避免递归搜索再次捡到旧 collector 字段。
  if (!payload) {
    return null;
  }
  const upperApi = asRecord(payload.upper_api);
  const radarStatusEnvelope = asRecord(upperApi?.radar_status);
  const radarStatus = asRecord(radarStatusEnvelope?.payload) ?? radarStatusEnvelope;
  if (!radarStatus) {
    return payload;
  }
  const latestScanProof = asRecord(radarStatus.latest_scan_proof);
  const scanProofLatest = asRecord(radarStatus.scan_proof_latest);
  const readback: JsonRecord = {};
  if (payload.status !== undefined) {
    readback.status = payload.status;
  }
  const assignFirst = (targetKey: string, values: unknown[]) => {
    const found = values.find((value) => value !== undefined);
    if (found !== undefined) {
      readback[targetKey] = found;
    }
  };
  assignFirst("latest_proof_status", [
    radarStatus.latest_scan_proof_state,
    latestScanProof?.state,
    scanProofLatest?.latest_proof_status,
  ]);
  assignFirst("scan_once_observed", [
    latestScanProof?.scan_once_observed,
    scanProofLatest?.latest_scan_once_observed,
  ]);
  assignFirst("scan_hz_observed", [
    latestScanProof?.scan_hz_observed,
    scanProofLatest?.latest_scan_hz_observed,
  ]);
  assignFirst("raw_packet_once_observed", [
    latestScanProof?.raw_packet_once_observed,
    scanProofLatest?.latest_raw_packet_once_observed,
  ]);
  assignFirst("tf_observed", [
    latestScanProof?.tf_observed,
    scanProofLatest?.latest_tf_observed,
  ]);
  // refresh 成功后优先消费最终 radar_status continuity/lifecycle 结论，避免旧 collector blocker 覆盖最终状态。
  assignFirst("continuous_scan_status", [radarStatus.continuous_scan_status]);
  assignFirst("continuous_window_observed", [radarStatus.continuous_window_observed]);
  assignFirst("continuity_window_status", [radarStatus.continuity_window_status]);
  assignFirst("lifecycle_running", [radarStatus.lifecycle_running]);
  assignFirst("lifecycle_state", [radarStatus.lifecycle_state]);
  assignFirst("latest_scan_proof_fresh", [radarStatus.latest_scan_proof_fresh]);
  const finalBlockedReasons = radarStatus.latest_scan_proof_blocked_reasons ?? latestScanProof?.blocked_reasons;
  if (Array.isArray(finalBlockedReasons) && finalBlockedReasons.length > 0) {
    readback.blocked_reasons = finalBlockedReasons;
  } else if (typeof finalBlockedReasons === "string" && finalBlockedReasons.trim()) {
    readback.blocked_reasons = finalBlockedReasons;
  }
  const continuityBlockedReasons = radarStatus.continuity_blocked_reasons;
  if (Array.isArray(continuityBlockedReasons) && continuityBlockedReasons.length > 0) {
    readback.continuity_blocked_reasons = continuityBlockedReasons;
  } else if (typeof continuityBlockedReasons === "string" && continuityBlockedReasons.trim()) {
    readback.continuity_blocked_reasons = continuityBlockedReasons;
  }
  return Object.keys(readback).length > 0 ? readback : payload;
}

function lidarSummaryFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
  proof: RobotApiProofSummary,
): RobotControlSummaryResponse["readback_summary"]["lidar"] {
  // 普通首屏只消费 summary 压缩字段，因此把 radar status 的 continuity/lifecycle 结论集中收口在这里。
  const runtimeScan = freeRoamRuntimeScanSummaryFromReadbacks(readbacks);
  const radarStatusReadback = readbackById(readbacks, "radar_status");
  const radarScanProofReadback = readbackById(readbacks, "radar_scan_proof_latest");
  const radarRawPacketProofReadback = readbackById(readbacks, "radar_raw_packet_proof_latest");
  const radarStatusPayload = radarStatusReadback?.payload ?? null;
  const radarScanProofPayload = radarScanProofReadback?.payload ?? null;
  const radarRawPacketProofPayload = radarRawPacketProofReadback?.payload ?? null;
  const readbackKeyValueText = (readback: InternalRobotApiEndpointReadback | null, keys: string[], fallback = ""): string => {
    // readback.key_values 是 endpoint 统一压缩后的事实；真实 scan-proof 的 raw_packets_parsed 可能只在这里稳定出现。
    for (const key of keys) {
      const value = readback?.key_values[key];
      if (typeof value === "string" && value.trim()) {
        return value.trim();
      }
    }
    return fallback;
  };
  const latestScanProofResultStatus = readbackKeyValueText(
    radarScanProofReadback,
    ["latest_proof_status", "latest_result_status", "status", "state"],
    summaryValueText(radarScanProofPayload, ["latest_proof_status", "latest_result_status", "status", "state"]),
  );
  const rawPacketObservedFromScan = readbackKeyValueText(
    radarScanProofReadback,
    ["raw_packet_once_observed", "latest_raw_packet_once_observed"],
    summaryValueText(radarScanProofPayload, ["raw_packet_once_observed", "latest_raw_packet_once_observed"], ""),
  );
  const rawPacketObservedFromRawProof = readbackKeyValueText(
    radarRawPacketProofReadback,
    ["raw_packet_once_observed", "latest_raw_packet_once_observed", "packet_once_observed"],
    summaryValueText(radarRawPacketProofPayload, ["raw_packet_once_observed", "latest_raw_packet_once_observed", "packet_once_observed"], ""),
  );
  const rawPacketOnceObserved = latestScanProofResultStatus === "raw_packets_parsed"
    ? "true"
    : rawPacketObservedFromScan || rawPacketObservedFromRawProof || "not_loaded";
  const radarControls = asRecord(findFirstKey(radarStatusPayload, ["controls"]));
  const radarStartControl = asRecord(radarControls?.start);
  const radarStartCommand = asRecord(radarStartControl?.command);
  const radarLifecycleRunning = summaryValueText(radarStatusPayload, ["lifecycle_running"]);
  const radarContinuousStatus = summaryValueText(radarStatusPayload, ["continuous_scan_status"]);
  const radarLifecycleState = summaryValueText(radarStatusPayload, ["lifecycle_state"]);
  const radarEndpointStatus = radarStatusReadback?.status ?? "not_loaded";
  const radarSummaryStatus =
    radarLifecycleRunning === "true" && radarContinuousStatus !== "not_loaded"
      // lifecycle 已经运行时，连续性结论比 latest proof 缺失更贴近现场状态，地图 marker 不能再退回 missing。
      ? radarContinuousStatus
      : radarEndpointStatus === "missing" && radarContinuousStatus !== "not_loaded"
        ? radarContinuousStatus
        : radarEndpointStatus === "not_loaded" && radarLifecycleState !== "not_loaded"
          ? radarLifecycleState
          : radarEndpointStatus;
  return {
    status: radarSummaryStatus,
    latest_scan_proof_status: radarScanProofReadback?.status ?? "not_loaded",
    latest_raw_packet_proof_status: radarRawPacketProofReadback?.status ?? "not_loaded",
    latest_scan_proof_result_status: latestScanProofResultStatus,
    raw_packet_once_observed: rawPacketOnceObserved,
    continuous_scan_status: radarContinuousStatus,
    lifecycle_running: radarLifecycleRunning,
    lifecycle_state: radarLifecycleState,
    continuous_window_observed: summaryValueText(radarStatusPayload, ["continuous_window_observed"]),
    continuity_window_status: summaryValueText(radarStatusPayload, ["continuity_window_status"]),
    latest_scan_proof_fresh: summaryValueText(radarStatusPayload, ["latest_scan_proof_fresh"]),
    runtime_scan_status: runtimeScan.status,
    runtime_lidar_min_distance_m: runtimeScan.min_distance_m,
    runtime_lidar_age_s: runtimeScan.age_s,
    runtime_scan_source: runtimeScan.source,
    scan_preview_point_count: String(proof.scan_preview_point_count),
    scan_preview_source_point_count: proof.scan_preview_source_point_count === null ? "not_loaded" : String(proof.scan_preview_source_point_count),
    scan_preview_frame_id: proof.scan_preview_frame_id || "not_loaded",
    radar_start_configured: summaryValueText(radarStartCommand, ["configured"]),
  };
}

function freeRoamRuntimeScanSummaryFromReadbacks(readbacks: InternalRobotApiEndpointReadback[]): {
  status: string;
  min_distance_m: string;
  age_s: string;
  source: string;
} {
  // free-roam runtime 直接消费实时 /scan；把结构化 snapshot 提到 lidar summary，避免前端解析 gate 中文文案。
  const latest = freeRoamRuntimeLatestFromReadbacks(readbacks);
  const snapshot = asRecord(latest?.snapshot);
  const age = finitePathCoordinate(snapshot?.lidar_age_s);
  const minDistance = finitePathCoordinate(snapshot?.lidar_min_distance_m);
  if (age === null || minDistance === null) {
    return {
      status: "not_loaded",
      min_distance_m: "not_loaded",
      age_s: "not_loaded",
      source: "not_loaded",
    };
  }
  const fresh = age <= 1.5;
  return {
    status: fresh ? "fresh" : "stale",
    min_distance_m: minDistance.toFixed(2),
    age_s: age.toFixed(2),
    source: "free_roam_runtime_snapshot",
  };
}

function cameraSummaryFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
  firstFrameProbeOverlay: RobotControlCameraFirstFrameProbeOverlay | null = null,
  mjpegRelayOverlay: RobotControlCameraMjpegRelayOverlay | null = null,
): RobotControlSummaryResponse["readback_summary"]["camera"] {
  // Camera 诊断只取 health/devices 的短字段；普通首屏仍只显示简化状态，工程细节留在高级诊断。
  const healthReadback = readbackById(readbacks, "camera_health");
  const devicesReadback = readbackById(readbacks, "camera_devices");
  const healthPayload = healthReadback?.payload ?? null;
  const currentSelection = asRecord(findFirstKey(healthPayload, ["current_selection"]));
  const sourceSummary = asRecord(findFirstKey(healthPayload, ["source_summary"]));
  const sourceSummarySelection = asRecord(sourceSummary?.current_selection);
  const mediaDiagnostics = asRecord(findFirstKey(healthPayload, ["media_diagnostics"]));
  const lastOfferError = asRecord(mediaDiagnostics?.last_offer_error) ?? asRecord(mjpegRelayOverlay?.last_error_payload);
  const selectedCandidate = cameraSelectedCandidateSummary(healthPayload, devicesReadback?.payload ?? null);
  const sourceUsage = asRecord(findFirstKey(healthPayload, ["source_usage"]) ?? mediaDiagnostics?.source_usage);
  const sourceDiagnosis = asRecord(findFirstKey(healthPayload, ["source_diagnosis"]) ?? mediaDiagnostics?.source_diagnosis);
  const sharedPreviewContract = asString(findFirstKey(healthPayload, ["shared_preview_contract"]) ?? mediaDiagnostics?.shared_preview_contract, "single_shared_capture_for_multiple_clients");
  const sourceUsageOwners = Array.isArray(sourceUsage?.owners) ? sourceUsage.owners : [];
  const sourceUsageSummary = sourceUsageOwners
    .map((owner) => {
      const record = asRecord(owner);
      const pid = record?.pid === undefined ? "" : compactValueText(record.pid);
      const command = asString(record?.command, "");
      return [pid ? `pid=${pid}` : "", command].filter(Boolean).join(" ");
    })
    .filter(Boolean)
    .slice(0, 3)
    .join("; ");
  const rawSourceReadiness = summaryValueText(healthPayload, ["source_readiness"]);
  const rawSourceFailureReason = summaryValueText(healthPayload, ["source_failure_reason"]);
  const probeFailureReason = firstFrameProbeOverlay?.failure_reason ?? "";
  const probeVisibleContentObserved = Boolean(
    firstFrameProbeOverlay?.proxy_status === "probe_forwarded"
    && firstFrameProbeOverlay.open_ok === "true"
    && firstFrameProbeOverlay.read_ok === "true"
    && firstFrameProbeOverlay.visible_content_proven === "true",
  );
  const probeFailed = Boolean(firstFrameProbeOverlay && firstFrameProbeOverlay.proxy_status !== "probe_forwarded");
  const sourceReadiness = probeVisibleContentObserved && ["", "not_loaded", "source_selected_not_probed", "first_frame_failed"].includes(rawSourceReadiness)
    ? "first_frame_observed"
    : probeFailed && ["", "not_loaded", "source_selected_not_probed"].includes(rawSourceReadiness)
      ? "first_frame_failed"
      : rawSourceReadiness;
  const sourceFailureReason = probeVisibleContentObserved && ["", "none", "not_loaded", ...CAMERA_FIRST_FRAME_FAILURE_REASONS].includes(rawSourceFailureReason)
    ? "none"
    : probeFailed && ["", "none", "not_loaded"].includes(rawSourceFailureReason)
      ? probeFailureReason || "first_frame_probe_failed"
      : rawSourceFailureReason;
  const sharedPreviewStatus = mjpegRelayOverlay?.upstream_active === true
    ? mjpegRelayOverlay.content_type_loaded
      ? "streaming"
      : "starting_local_peer"
    : "idle_not_started";
  const rawHealthStatus = healthReadback?.status ?? "not_loaded";
  const relayLastFailureReason = asString(mjpegRelayOverlay?.last_failure_reason, "");
  const lastOfferFailureReason = asString(lastOfferError?.failure_reason, "");
  const relayFirstFrameFailureReason = CAMERA_FIRST_FRAME_FAILURE_REASONS.includes(relayLastFailureReason as typeof CAMERA_FIRST_FRAME_FAILURE_REASONS[number])
    ? relayLastFailureReason
    : CAMERA_FIRST_FRAME_FAILURE_REASONS.includes(lastOfferFailureReason as typeof CAMERA_FIRST_FRAME_FAILURE_REASONS[number])
      ? lastOfferFailureReason
      : "";
  const relayHasCameraFirstFrameFact = Boolean(
    mjpegRelayOverlay?.last_failure_reason === "camera_source_first_frame_failed"
    || relayFirstFrameFailureReason
    || mjpegRelayOverlay?.source_diagnosis_status === "uvc_no_frame_not_exclusive",
  );
  const healthReadFailedButRelayHasCameraFact = ["fetch_failed", "bad_json", "not_object"].includes(healthReadback?.request_status ?? "")
    && relayHasCameraFirstFrameFact;
  const cameraStatus = probeVisibleContentObserved && ["", "not_loaded", "source_not_probed", "source_first_frame_failed"].includes(rawHealthStatus)
    ? "ready"
    : healthReadFailedButRelayHasCameraFact
      ? "source_first_frame_failed"
    : sourceReadiness === "first_frame_failed"
    ? "source_first_frame_failed"
    : rawHealthStatus === "ready" && sourceReadiness === "source_selected_not_probed" && sharedPreviewStatus !== "streaming"
      ? "source_not_probed"
      : rawHealthStatus;
  const resolvedSourceReadiness = cameraStatus === "source_first_frame_failed" && sourceReadiness !== "first_frame_observed"
    ? "first_frame_failed"
    : sourceReadiness;
  const resolvedSourceFailureReason = cameraStatus === "source_first_frame_failed"
    && ["", "none", "not_loaded"].includes(sourceFailureReason)
    && relayFirstFrameFailureReason
    ? relayFirstFrameFailureReason
    : sourceFailureReason;
  const sourceFirstFrameFailedForSharedPreview = Boolean(
    cameraStatus === "source_first_frame_failed"
    || resolvedSourceReadiness === "first_frame_failed"
    || relayHasCameraFirstFrameFact
    || CAMERA_FIRST_FRAME_FAILURE_REASONS.includes(resolvedSourceFailureReason as typeof CAMERA_FIRST_FRAME_FAILURE_REASONS[number])
    || CAMERA_FIRST_FRAME_FAILURE_REASONS.includes(lastOfferFailureReason as typeof CAMERA_FIRST_FRAME_FAILURE_REASONS[number]),
  );
  const selectedName = cameraDisplayDeviceName(selectedCandidate.selected_name) || "UVC 设备";
  const sourceUsageLooksFree = ["not_in_use", ""].includes(asString(sourceUsage?.status, ""))
    || compactValueText(sourceUsage?.owner_count ?? "not_loaded") === "0";
  const sourceNoFrameNotExclusive = Boolean(sourceFirstFrameFailedForSharedPreview && sourceUsageLooksFree);
  const probeBackendNoFrameNotExclusive = Boolean(
    firstFrameProbeOverlay?.backend_smoke_status === "backend_no_frame_observed"
    && firstFrameProbeOverlay.backend_frame_observed === "false"
    && sourceUsageLooksFree
  );
  const overlaySourceDiagnosis = {
    status: asString(mjpegRelayOverlay?.source_diagnosis_status, ""),
    plain_hint: cameraDiagnosisPlainHint(mjpegRelayOverlay?.source_diagnosis_plain_hint, selectedName),
    next_action: asString(mjpegRelayOverlay?.source_diagnosis_next_action, ""),
    not_exclusive: asString(mjpegRelayOverlay?.source_diagnosis_not_exclusive, ""),
  };
  const overlayDiagnosisAvailable = Boolean(
    overlaySourceDiagnosis.status
    && !["not_loaded", "none"].includes(overlaySourceDiagnosis.status)
    && overlaySourceDiagnosis.plain_hint
    && !["not_loaded", "none"].includes(overlaySourceDiagnosis.plain_hint)
  );
  const derivedSourceDiagnosis = probeBackendNoFrameNotExclusive
    ? {
      status: "uvc_no_frame_not_exclusive",
      plain_hint: `不是页面独占：${cameraOwnerFreeText(selectedName)}，但 OpenCV/V4L2 后端也没有取到视频帧。`,
      next_action: "check_usb_camera_input_power_or_known_good_uvc",
      next_action_plain: cameraActionPlainText("check_usb_camera_input_power_or_known_good_uvc"),
      not_exclusive: true,
    }
    : overlayDiagnosisAvailable && !asRecord(sourceDiagnosis)
      ? {
        status: overlaySourceDiagnosis.status,
        plain_hint: overlaySourceDiagnosis.plain_hint,
        next_action: overlaySourceDiagnosis.next_action || "check_usb_camera_input_power_or_known_good_uvc",
        next_action_plain: cameraActionPlainText(overlaySourceDiagnosis.next_action || "check_usb_camera_input_power_or_known_good_uvc"),
        not_exclusive: overlaySourceDiagnosis.not_exclusive || "not_loaded",
      }
    : sourceNoFrameNotExclusive && (
      !asRecord(sourceDiagnosis)
      || asString(sourceDiagnosis?.status, "") !== "uvc_no_frame_not_exclusive"
      || compactValueText(sourceDiagnosis?.not_exclusive) !== "true"
    )
      ? {
        status: "uvc_no_frame_not_exclusive",
        plain_hint: `不是页面独占：${cameraOwnerFreeText(selectedName)}，但 UVC 设备没有输出视频帧。`,
        next_action: "check_usb_camera_input_power_or_known_good_uvc",
        next_action_plain: cameraActionPlainText("check_usb_camera_input_power_or_known_good_uvc"),
        not_exclusive: true,
      }
    : {
      status: asString(sourceDiagnosis?.status, "not_loaded"),
      plain_hint: cameraDiagnosisPlainHint(sourceDiagnosis?.plain_hint, selectedName) || "not_loaded",
      next_action: asString(sourceDiagnosis?.next_action, "not_loaded"),
      next_action_plain: cameraActionPlainText(asString(sourceDiagnosis?.next_action, "not_loaded")),
      not_exclusive: sourceDiagnosis?.not_exclusive === undefined ? "not_loaded" : compactValueText(sourceDiagnosis.not_exclusive),
    };
  const sharedPreviewLastFailureReason = mjpegRelayOverlay?.last_failure_reason
    || (sourceFirstFrameFailedForSharedPreview ? "camera_source_first_frame_failed" : "none");
  const sharedPreviewLastRemoteHttpStatus = mjpegRelayOverlay?.last_remote_http_status === null || mjpegRelayOverlay?.last_remote_http_status === undefined
    ? sourceFirstFrameFailedForSharedPreview && healthReadback?.http_status !== null && healthReadback?.http_status !== undefined
      ? compactValueText(healthReadback.http_status)
      : "none"
    : compactValueText(mjpegRelayOverlay.last_remote_http_status);
  const previewGuidance = cameraSummaryPreviewGuidance(sharedPreviewStatus, sourceFirstFrameFailedForSharedPreview, derivedSourceDiagnosis);
  const previewVisibility = cameraPreviewVisibilityPlainSummary({
    previewStatus: sharedPreviewStatus,
    sourceFirstFrameFailed: sourceFirstFrameFailedForSharedPreview,
    previewPlainHint: previewGuidance.plain_hint,
    previewNextActionPlain: previewGuidance.next_action_plain,
  });
  return {
    status: cameraStatus,
    devices_status: devicesReadback?.status ?? "not_loaded",
    // MJPEG relay 状态来自 PC Node 内存表；它只说明共享上游是否存在，不证明画面像素已经可见。
    preview_status: sharedPreviewStatus,
    preview_plain_hint: previewGuidance.plain_hint,
    preview_next_action: previewGuidance.next_action,
    preview_next_action_plain: previewGuidance.next_action_plain,
    preview_visible_status: previewVisibility.visibleStatus,
    preview_visible_plain: previewVisibility.visiblePlain,
    camera_wysiwyg_status_plain: previewVisibility.wysiwygStatusPlain,
    camera_wysiwyg_next_action_plain: previewVisibility.wysiwygNextActionPlain,
    shared_preview_client_count: compactValueText(mjpegRelayOverlay?.client_count ?? 0),
    viewer_count: compactValueText(mjpegRelayOverlay?.client_count ?? 0),
    shared_preview_upstream_active: compactValueText(mjpegRelayOverlay?.upstream_active === true),
    upstream_connected: compactValueText(mjpegRelayOverlay?.upstream_active === true),
    shared_preview_content_type_loaded: compactValueText(mjpegRelayOverlay?.content_type_loaded === true),
    shared_preview_cached_frame_loaded: compactValueText(mjpegRelayOverlay?.cached_frame_loaded === true),
    has_recent_frame: compactValueText(mjpegRelayOverlay?.cached_frame_loaded === true),
    shared_preview_cached_frame_age_ms: mjpegRelayOverlay?.cached_frame_age_ms === null || mjpegRelayOverlay?.cached_frame_age_ms === undefined
      ? "none"
      : compactValueText(mjpegRelayOverlay.cached_frame_age_ms),
    shared_preview_shared_capture: compactValueText(true),
    shared_preview_exclusive_camera_claim: compactValueText(false),
    shared_preview_contract: sharedPreviewContract,
    shared_preview_last_failure_reason: sharedPreviewLastFailureReason,
    shared_preview_last_remote_http_status: sharedPreviewLastRemoteHttpStatus,
    shared_preview_last_failure_at_ms: mjpegRelayOverlay?.last_failure_at_ms === null || mjpegRelayOverlay?.last_failure_at_ms === undefined
      ? "none"
      : compactValueText(mjpegRelayOverlay.last_failure_at_ms),
    video_source: summaryValueText(healthPayload, ["video_source"]),
    video_source_mode: summaryValueText(healthPayload, ["video_source_mode"]),
    selected_path: asString(currentSelection?.selected_path ?? sourceSummarySelection?.selected_path),
    selected_name: cameraDisplayDeviceName(selectedCandidate.selected_name) || "not_loaded",
    selected_is_uvc_or_usb: selectedCandidate.selected_is_uvc_or_usb === undefined
      ? "not_loaded"
      : compactValueText(selectedCandidate.selected_is_uvc_or_usb),
    selected_formats_summary: asString(selectedCandidate.selected_formats_summary, "not_loaded"),
    selected_role: asString(selectedCandidate.selected_role, "not_loaded"),
    selected_sibling_video_nodes_summary: asString(selectedCandidate.selected_sibling_video_nodes_summary, "none"),
    selected_sibling_video_node_count: selectedCandidate.selected_sibling_video_node_count === undefined
      ? "not_loaded"
      : compactValueText(selectedCandidate.selected_sibling_video_node_count),
    // 最终 status 若已由 health/relay 判定为无首帧，readiness 也必须同口径，避免首屏和高级诊断互相矛盾。
    source_readiness: resolvedSourceReadiness,
    source_failure_reason: resolvedSourceFailureReason,
    source_diagnosis_status: derivedSourceDiagnosis.status,
    source_diagnosis_plain_hint: derivedSourceDiagnosis.plain_hint,
    source_diagnosis_next_action: derivedSourceDiagnosis.next_action,
    source_diagnosis_next_action_plain: derivedSourceDiagnosis.next_action_plain,
    source_diagnosis_not_exclusive: compactValueText(derivedSourceDiagnosis.not_exclusive),
    source_usage_status: asString(sourceUsage?.status, "not_loaded"),
    source_usage_owner_count: sourceUsage?.owner_count === undefined ? "not_loaded" : compactValueText(sourceUsage.owner_count),
    source_usage_summary: sourceUsageSummary || "none",
    active_peer_count: summaryValueText(healthPayload, ["active_peer_count", "active_peer_connections"]),
    last_offer_error: asString(lastOfferError?.error, "none"),
    last_offer_failure_reason: asString(lastOfferError?.failure_reason, "none"),
    last_offer_format_attempts_summary: cameraFormatAttemptsSummary(lastOfferError),
    first_frame_probe_status: firstFrameProbeOverlay?.status ?? "not_loaded",
    first_frame_probe_failure_reason: firstFrameProbeOverlay?.failure_reason || "none",
    first_frame_probe_open_ok: firstFrameProbeOverlay?.open_ok ?? "not_loaded",
    first_frame_probe_read_ok: firstFrameProbeOverlay?.read_ok ?? "not_loaded",
    first_frame_probe_visible_content_proven: firstFrameProbeOverlay?.visible_content_proven ?? "not_loaded",
    first_frame_probe_backend_smoke_status: firstFrameProbeOverlay?.backend_smoke_status ?? "not_requested",
    first_frame_probe_backend_frame_observed: firstFrameProbeOverlay?.backend_frame_observed ?? "not_loaded",
    first_frame_probe_backend_attempts: firstFrameProbeOverlay?.backend_attempts ?? "0",
    first_frame_probe_fallback_attempts_summary: firstFrameProbeOverlay?.fallback_attempts_summary ?? "none",
    first_frame_probe_checked_at_ms: firstFrameProbeOverlay ? String(firstFrameProbeOverlay.checked_at_ms) : "not_loaded",
  };
}

export type RobotControlCameraFirstFrameProbeOverlay = {
  checked_at_ms: number;
  proxy_status: "probe_forwarded" | "probe_rejected" | "probe_failed";
  status: string;
  failure_reason: string;
  open_ok: string;
  read_ok: string;
  visible_content_proven: string;
  backend_smoke_status: string;
  backend_frame_observed: string;
  backend_attempts: string;
  fallback_attempts_summary: string;
};

export type RobotControlCameraMjpegRelayOverlay = {
  client_count: number;
  upstream_active: boolean;
  content_type_loaded: boolean;
  cached_frame_loaded: boolean;
  cached_frame_age_ms: number | null;
  shared_capture: true;
  exclusive_camera_claim: false;
  last_failure_reason: string;
  last_remote_http_status: number | null;
  last_failure_at_ms: number | null;
  last_error_payload?: JsonRecord | null;
  source_diagnosis_status?: string;
  source_diagnosis_plain_hint?: string;
  source_diagnosis_next_action?: string;
  source_diagnosis_not_exclusive?: string;
};

function compactTrueFields(fields: string[]): string[] {
  // 响应只保留短字段名，避免把完整对象路径直接塞进卡片和日志摘要。
  return fields.map((field) => field.slice(0, 180));
}

function numericSeconds(value: unknown): number | null {
  // 只接受有限正数秒；其他值视为未配置，避免把异常 body 变成无限等待。
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    return null;
  }
  return value;
}

export function computeRobotProofRefreshTimeoutMs(config: Pick<RobotProofRefreshConfig, "request_body" | "timeout_cap_ms" | "safety_margin_ms">): number {
  // 代理 timeout 由 body 预估时长加安全余量推导，并且封顶，避免卡死 workstation。
  const timeoutS = numericSeconds(config.request_body.timeout_s) ?? 0;
  const warmupS = numericSeconds(config.request_body.runtime_warmup_s) ?? 0;
  const managedS = config.request_body.managed_runtime_opt_in === true ? numericSeconds(config.request_body.managed_timeout_s) ?? 0 : 0;
  const pathGenerationS = numericSeconds(config.request_body.path_generation_timeout_s) ?? 0;
  const calculatedMs = Math.round((timeoutS + warmupS + managedS + pathGenerationS) * 1000 + Math.max(0, Math.trunc(config.safety_margin_ms)));
  return Math.min(config.timeout_cap_ms, calculatedMs);
}

function safeMapName(value: unknown): string | null {
  // map_name 会进入上位机 argv；PC 侧先限短基名，板端还会再校验一次。
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== "string") {
    return "";
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  if (trimmed.length > 64 || !/^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/.test(trimmed)) {
    return "";
  }
  return trimmed;
}

function safeLifecycleArtifactPath(value: unknown): string | null {
  // artifact_path 只作为兼容请求字段；上位机会忽略它，PC 仍拒绝绝对路径和穿越。
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== "string") {
    return "";
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  if (trimmed.length > 120 || trimmed.startsWith("/") || trimmed.includes("..") || !/^[A-Za-z0-9._/-]+$/.test(trimmed)) {
    return "";
  }
  return trimmed;
}

function sanitizeMapLifecycleBody(body: unknown): { ok: true; body: RobotControlMapLifecycleRequest } | { ok: false; reason: string } {
  // 固定代理只接受 map_name/artifact_path 两个短字段；未知字段直接拒绝，不做“忽略后转发”。
  if (body === undefined || body === null) {
    return { ok: true, body: {} };
  }
  const payload = asRecord(body);
  if (!payload) {
    return { ok: false, reason: "request_body_must_be_json_object" };
  }
  const unknownKeys = Object.keys(payload).filter((key) => key !== "map_name" && key !== "artifact_path");
  if (unknownKeys.length > 0) {
    return { ok: false, reason: `request_body_unknown_fields:${unknownKeys.slice(0, 4).join("|")}` };
  }
  const mapName = safeMapName(payload.map_name);
  if (mapName === "") {
    return { ok: false, reason: "map_name_invalid_or_too_long" };
  }
  const artifactPath = safeLifecycleArtifactPath(payload.artifact_path);
  if (artifactPath === "") {
    return { ok: false, reason: "artifact_path_invalid_or_too_long" };
  }
  return {
    ok: true,
    body: {
      ...(mapName ? { map_name: mapName } : {}),
      ...(artifactPath ? { artifact_path: artifactPath } : {}),
    },
  };
}

function sanitizeNavGoalPreflightBody(
  body: unknown,
): { ok: true; body: Required<RobotControlNavGoalPreflightResponse["goal_request"]> } | { ok: false; reason: string } {
  // 目标预检只接受短白名单坐标，不允许 endpoint、action、cmd_vel 或任意 Nav2 参数混入请求。
  const payload = asRecord(body);
  if (!payload) {
    return { ok: false, reason: "request_body_must_be_json_object" };
  }
  const allowed = new Set(["goal_frame_id", "goal_x", "goal_y", "goal_yaw", "confirm_navigation_preflight"]);
  const unknownKeys = Object.keys(payload).filter((key) => !allowed.has(key));
  if (unknownKeys.length > 0) {
    return { ok: false, reason: `request_body_unknown_fields:${unknownKeys.slice(0, 4).join("|")}` };
  }
  if (payload.goal_frame_id !== undefined && payload.goal_frame_id !== "map") {
    return { ok: false, reason: "goal_frame_id_must_be_map" };
  }
  const numberOrDefault = (key: keyof RobotControlNavGoalPreflightRequest, fallback: number): number | null => {
    const value = payload[key];
    if (value === undefined) {
      return fallback;
    }
    return typeof value === "number" && Number.isFinite(value) ? value : null;
  };
  const goalX = numberOrDefault("goal_x", 0);
  const goalY = numberOrDefault("goal_y", 0);
  const goalYaw = numberOrDefault("goal_yaw", 0);
  if (goalX === null || goalY === null || goalYaw === null) {
    return { ok: false, reason: "goal_fields_must_be_finite_numbers" };
  }
  return {
    ok: true,
    body: {
      goal_frame_id: "map",
      goal_x: Math.min(NAV_GOAL_PREFLIGHT_GOAL_LIMITS.x_max_m, Math.max(NAV_GOAL_PREFLIGHT_GOAL_LIMITS.x_min_m, goalX)),
      goal_y: Math.min(NAV_GOAL_PREFLIGHT_GOAL_LIMITS.y_max_m, Math.max(NAV_GOAL_PREFLIGHT_GOAL_LIMITS.y_min_m, goalY)),
      goal_yaw: Math.min(NAV_GOAL_PREFLIGHT_GOAL_LIMITS.yaw_max_rad, Math.max(NAV_GOAL_PREFLIGHT_GOAL_LIMITS.yaw_min_rad, goalYaw)),
      confirm_navigation_preflight: payload.confirm_navigation_preflight === true,
    },
  };
}

function sanitizeOperatorReportString(key: string, value: unknown): { ok: true; value: string } | { ok: false; reason: string } {
  // 字符串字段只做短文本材料引用，不能携带长 raw log、凭证、URL query 或二进制内容。
  if (typeof value !== "string") {
    return { ok: false, reason: `${key}_must_be_string` };
  }
  const limit = OPERATOR_REPORT_STRING_LIMITS[key] ?? 240;
  const trimmed = value.trim();
  if (trimmed.length > limit) {
    return { ok: false, reason: `${key}_too_long` };
  }
  return { ok: true, value: trimmed };
}

function sanitizeOperatorReportValue(key: string, value: unknown): { ok: true; value: boolean | string } | { ok: false; reason: string } {
  // 每个字段按类型白名单收口，避免把安全开关、endpoint、body 片段混进上位机 report。
  if (OPERATOR_REPORT_BOOLEAN_FIELDS.has(key)) {
    return typeof value === "boolean" ? { ok: true, value } : { ok: false, reason: `${key}_must_be_boolean` };
  }
  return sanitizeOperatorReportString(key, value);
}

function sanitizeOperatorReportClaims(
  value: unknown,
): { ok: true; claims: RobotControlOperatorReportStructuredHilClaims } | { ok: false; reason: string; rejected_fields: string[] } {
  // structured_hil_claims 只允许材料 claim 和引用；delivery_success 也只能留在这一层。
  if (value === undefined || value === null) {
    return { ok: true, claims: {} };
  }
  const payload = asRecord(value);
  if (!payload) {
    return { ok: false, reason: "structured_hil_claims_must_be_json_object", rejected_fields: ["structured_hil_claims"] };
  }
  const rejectedFields = Object.keys(payload)
    .filter((key) => !OPERATOR_REPORT_CLAIM_FIELDS.has(key))
    .map((key) => `structured_hil_claims.${key}`);
  if (rejectedFields.length > 0) {
    return { ok: false, reason: `request_body_unknown_fields:${rejectedFields.slice(0, 4).join("|")}`, rejected_fields: rejectedFields };
  }
  const claims: RobotControlOperatorReportStructuredHilClaims = {};
  for (const [key, rawValue] of Object.entries(payload)) {
    const sanitized = sanitizeOperatorReportValue(key, rawValue);
    if (!sanitized.ok) {
      return { ok: false, reason: sanitized.reason, rejected_fields: [`structured_hil_claims.${key}`] };
    }
    Object.assign(claims, { [key]: sanitized.value });
  }
  return { ok: true, claims };
}

function sanitizeOperatorReportBody(
  body: unknown,
): { ok: true; body: RobotControlOperatorReportRequest } | { ok: false; reason: string; rejected_fields: string[] } {
  // operator report 是 fail-closed 提交入口；未知字段拒绝，不能“忽略后继续转发”。
  const payload = asRecord(body);
  if (!payload) {
    return { ok: false, reason: "request_body_must_be_json_object", rejected_fields: ["body"] };
  }
  const rejectedFields = Object.keys(payload).filter((key) => !OPERATOR_REPORT_TOP_LEVEL_FIELDS.has(key));
  if (rejectedFields.length > 0) {
    return { ok: false, reason: `request_body_unknown_fields:${rejectedFields.slice(0, 4).join("|")}`, rejected_fields: rejectedFields };
  }
  const claims = sanitizeOperatorReportClaims(payload.structured_hil_claims);
  if (!claims.ok) {
    return { ok: false, reason: claims.reason, rejected_fields: claims.rejected_fields };
  }
  const sanitizedBody: RobotControlOperatorReportRequest = {};
  for (const [key, rawValue] of Object.entries(payload)) {
    if (key === "structured_hil_claims") {
      continue;
    }
    const sanitized = sanitizeOperatorReportValue(key, rawValue);
    if (!sanitized.ok) {
      return { ok: false, reason: sanitized.reason, rejected_fields: [key] };
    }
    Object.assign(sanitizedBody, { [key]: sanitized.value });
  }
  if (Object.keys(claims.claims).length > 0) {
    sanitizedBody.structured_hil_claims = claims.claims;
  }
  return { ok: true, body: sanitizedBody };
}

function blockedOperatorReportResponse(
  sourceBaseUrl: string,
  reason: string,
  rejectedFields: string[] = [],
  requestBody: RobotControlOperatorReportRequest = {},
): RobotControlOperatorReportProxyResponse {
  // 拒绝态也返回固定 false 顶层字段，让前端和 artifact 都能证明没有控制或成功升级。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
    ...PROOF_FLAGS,
    proxy_status: "report_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: OPERATOR_REPORT_REMOTE_ENDPOINT,
    remote_method: "POST",
    remote_http_status: null,
    status: "blocked",
    request_body: requestBody,
    structured_hil_claims: requestBody.structured_hil_claims ?? {},
    rejected_fields: rejectedFields,
    ignored_fields: [],
    failure_reason: reason,
    blocked_reasons: [reason, ...rejectedFields.map((field) => `rejected_field:${field}`)],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

export async function buildOperatorReportProxy(
  baseUrl: string,
  body: unknown,
): Promise<RobotControlOperatorReportProxyResponse> {
  // 固定 POST 代理只服务 /api/operator/report；它不能调用 base/manual、cmd_vel、Nav2 goal、map/radar start。
  const sanitized = sanitizeOperatorReportBody(body);
  if (!sanitized.ok) {
    return blockedOperatorReportResponse(baseUrl, sanitized.reason, sanitized.rejected_fields);
  }
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedOperatorReportResponse(baseUrl, normalized.reason, [], sanitized.body);
  }

  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, OPERATOR_REPORT_REMOTE_ENDPOINT), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sanitized.body),
      signal: AbortSignal.timeout(OPERATOR_REPORT_TIMEOUT_MS),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? `fetch_timeout_${OPERATOR_REPORT_TIMEOUT_MS}ms`
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return {
      ...blockedOperatorReportResponse(baseUrl, reason, [], sanitized.body),
      proxy_status: "report_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    };
  }

  const bodyJson = await response.json().catch(() => null);
  const payload = asRecord(bodyJson);
  if (!payload) {
    return {
      ...blockedOperatorReportResponse(baseUrl, "response_json_not_object", [], sanitized.body),
      proxy_status: "report_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_not_object", `operator_report_http_status_${response.status}`],
    };
  }

  const hardDangerous = scanDangerousTrueFields(
    payload,
    "",
    HARD_DANGEROUS_TRUE_FIELDS,
    OPERATOR_REPORT_CLAIM_TRUE_FIELD_EXEMPTIONS,
  );
  const blockedReasons = [
    ...(response.ok ? [] : [`operator_report_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
    ...remoteFailureReasons(payload, "operator_report"),
  ];
  const forwarded = response.ok && blockedReasons.length === 0;
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
    ...PROOF_FLAGS,
    proxy_status: forwarded ? "report_forwarded" : "report_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: OPERATOR_REPORT_REMOTE_ENDPOINT,
    remote_method: "POST",
    remote_http_status: response.status,
    status: forwarded ? "loaded_fail_closed_summary" : "blocked",
    request_body: sanitized.body,
    structured_hil_claims: sanitized.body.structured_hil_claims ?? {},
    rejected_fields: [],
    ignored_fields: [],
    failure_reason:
      blockedReasons.length > 0
        ? blockedReasons[0] ?? "operator_report_blocked"
        : asString(findFirstKey(payload, ["failure_reason", "error"]), ""),
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    robot_control_executed: false,
  };
}

export async function fetchManualMotionOperatorReportPreflight(baseUrl: URL): Promise<RobotControlOperatorReportPreflight> {
  // 非 stop 点动前必须重新读取上位机最新现场材料，不能只信浏览器 checkbox 的瞬时状态。
  let response: Response;
  try {
    response = await fetch(endpointUrl(baseUrl, OPERATOR_REPORT_REMOTE_ENDPOINT), {
      method: "GET",
      signal: AbortSignal.timeout(ROBOT_CONTROL_OPERATOR_REPORT_PREFLIGHT_TIMEOUT_MS),
    });
  } catch {
    return blockedOperatorReportPreflight(
      "operator_report_preflight_required",
      notLoadedHilMaterialSummary("not_loaded"),
      "fetch_failed",
      null,
    );
  }
  const json = await response.json().catch(() => null);
  const payload = asRecord(json);
  if (!payload) {
    return blockedOperatorReportPreflight(
      "operator_report_preflight_required",
      notLoadedHilMaterialSummary(response.ok ? "missing" : "not_loaded"),
      response.ok ? "not_object" : "blocked",
      response.status,
    );
  }
  return buildOperatorReportPreflightFromPayload(payload, response.status, response.ok ? "loaded" : "blocked");
}

export async function fetchFirstJogOperatorReportPreflight(baseUrl: URL): Promise<RobotControlOperatorReportPreflight> {
  // 首次试动仍必须重新读上位机材料；浏览器 checkbox 不能单独放行真实底盘动作。
  let response: Response;
  try {
    response = await fetch(endpointUrl(baseUrl, OPERATOR_REPORT_REMOTE_ENDPOINT), {
      method: "GET",
      signal: AbortSignal.timeout(ROBOT_CONTROL_OPERATOR_REPORT_PREFLIGHT_TIMEOUT_MS),
    });
  } catch {
    return {
      ...blockedOperatorReportPreflight(
        "first_jog_preflight_required",
        notLoadedHilMaterialSummary("not_loaded"),
        "fetch_failed",
        null,
      ),
      required_fields: [...ROBOT_CONTROL_FIRST_JOG_PREFLIGHT_REQUIRED_FIELDS],
      missing_fields: [...ROBOT_CONTROL_FIRST_JOG_PREFLIGHT_REQUIRED_FIELDS],
    };
  }
  const json = await response.json().catch(() => null);
  const payload = asRecord(json);
  if (!payload) {
    return {
      ...blockedOperatorReportPreflight(
        "first_jog_preflight_required",
        notLoadedHilMaterialSummary(response.ok ? "missing" : "not_loaded"),
        response.ok ? "not_object" : "blocked",
        response.status,
      ),
      required_fields: [...ROBOT_CONTROL_FIRST_JOG_PREFLIGHT_REQUIRED_FIELDS],
      missing_fields: [...ROBOT_CONTROL_FIRST_JOG_PREFLIGHT_REQUIRED_FIELDS],
    };
  }
  return buildFirstJogOperatorReportPreflightFromPayload(payload, response.status, response.ok ? "loaded" : "blocked");
}

function booleanObserved(payload: JsonRecord | null, keys: string[]): boolean {
  // proof 字段可能嵌在 latest_result/status 内；只认显式 true，不用字符串猜测安全状态。
  return keys.some((key) => findFirstKey(payload, [key]) === true);
}

function statusMentions(payload: JsonRecord | null, token: string): boolean {
  // 真实上位机有些 proof 只在 status/latest_result_status 里给事件名；这里只匹配固定 token。
  const statusValues = [
    findFirstKey(payload, ["status"]),
    findFirstKey(payload, ["proof_status"]),
    findFirstKey(payload, ["latest_proof_status"]),
    findFirstKey(payload, ["latest_result_status"]),
  ];
  return statusValues.some((value) => typeof value === "string" && value.includes(token));
}

function nestedBooleanKey(value: unknown, key: string, depth = 0): boolean {
  // TF 证据可能是对象或数组；只要同名字段显式 true 才算 map_to_base_link 可见。
  if (!value || typeof value !== "object" || depth > 5) {
    return false;
  }
  if (Array.isArray(value)) {
    return value.some((item) => nestedBooleanKey(item, key, depth + 1));
  }
  const record = value as JsonRecord;
  if (record[key] === true) {
    return true;
  }
  return Object.values(record).some((item) => nestedBooleanKey(item, key, depth + 1));
}

function mapToBaseLinkObserved(payload: JsonRecord | null): boolean {
  // 定位放行必须看到 map->base_link 链路；字符串 JSON 只解析短文本，避免把任意长日志当结构化证据。
  const candidates = [
    findFirstKey(payload, ["localization_tf_observed"]),
    findFirstKey(payload, ["tf_chain_observed"]),
  ];
  return candidates.some((candidate) => {
    if (nestedBooleanKey(candidate, "map_to_base_link")) {
      return true;
    }
    if (typeof candidate === "string" && candidate.length < 1000) {
      try {
        return nestedBooleanKey(JSON.parse(candidate), "map_to_base_link");
      } catch {
        return candidate.includes("map_to_base_link") && candidate.includes("true");
      }
    }
    return false;
  });
}

function numericField(payload: JsonRecord | null, keys: string[]): number {
  // 路径点数必须是正数；字符串只兼容上位机 latest readback 的短数字摘要。
  const found = findFirstKey(payload, keys);
  if (typeof found === "number" && Number.isFinite(found)) {
    return found;
  }
  if (typeof found === "string" && found.trim() && Number.isFinite(Number(found))) {
    return Number(found);
  }
  return 0;
}

function readbackById(readbacks: InternalRobotApiEndpointReadback[], id: RobotApiReadEndpointId): InternalRobotApiEndpointReadback | null {
  // 固定 id 查找比数组下标稳，后续增删可选 status endpoint 不影响 preflight 判定。
  return readbacks.find((item) => item.id === id) ?? null;
}

function publicReadbacks(readbacks: InternalRobotApiEndpointReadback[]): RobotApiEndpointReadback[] {
  // 内部 payload 只服务本机 preflight 判定，API/artifact 边界必须像 summary 一样只暴露短 readback 摘要。
  return readbacks.map((readback) => {
    const { payload, ...publicReadback } = readback;
    void payload;
    return publicReadback;
  });
}

function blockedNavGoalPreflightResponse(
  sourceBaseUrl: string,
  reason: string,
  goalRequest?: RobotControlNavGoalPreflightResponse["goal_request"],
  readbacks: InternalRobotApiEndpointReadback[] = [],
  operatorReportPreflight?: RobotControlOperatorReportPreflight,
): RobotControlNavGoalPreflightResponse {
  // 本机拒绝也必须返回完整 readback 摘要和禁止调用列表，用 artifact 证明没有执行导航或底盘运动。
  const localize = readbackById(readbacks, "localize_proof_latest");
  const nav2Proof = readbackById(readbacks, "nav2_proof_latest");
  const nav2Status = readbackById(readbacks, "nav2_status");
  const pathPointCount = numericField(nav2Proof?.payload ?? null, ["path_point_count", "latest_path_point_count"]);
  const defaultGoal = goalRequest ?? {
    goal_frame_id: "map",
    goal_x: 0,
    goal_y: 0,
    goal_yaw: 0,
    confirm_navigation_preflight: false,
  };
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_preflight.v1",
    ...PROOF_FLAGS,
    proxy_status: "preflight_rejected",
    preflight_status: "preflight_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    workstation_endpoint: "/api/robot-control/nav2/goal/preflight",
    remote_methods_used: ["GET"],
    remote_read_endpoints: publicReadbacks(readbacks),
    forbidden_remote_endpoints_not_called: ["/api/nav2/start", "NavigateToPose", "/cmd_vel", "/api/base/manual"],
    goal_request: defaultGoal,
    goal_limits: NAV_GOAL_PREFLIGHT_GOAL_LIMITS,
    operator_report_preflight: operatorReportPreflight ?? blockedOperatorReportPreflight(reason),
    localization_summary: {
      request_status: localize?.request_status ?? "blocked",
      status: asString(findFirstKey(localize?.payload, ["status", "latest_proof_status", "latest_result_status"]), "not_loaded"),
      localization_reset_observed: booleanObserved(localize?.payload ?? null, ["localization_reset_observed"]) || statusMentions(localize?.payload ?? null, "localization_reset_observed"),
      nav2_no_motion_localization_runtime_observed: statusMentions(localize?.payload ?? null, "nav2_no_motion_localization_runtime_observed"),
      map_to_base_link: mapToBaseLinkObserved(localize?.payload ?? null),
    },
    nav2_path_summary: {
      request_status: nav2Proof?.request_status ?? "blocked",
      status: asString(findFirstKey(nav2Proof?.payload, ["status", "latest_proof_status", "latest_result_status"]), "not_loaded"),
      path_generated: booleanObserved(nav2Proof?.payload ?? null, ["path_generated", "latest_path_generated"]),
      path_generation_succeeded: booleanObserved(nav2Proof?.payload ?? null, ["path_generation_succeeded"]),
      path_point_count: pathPointCount,
    },
    nav2_status_summary: {
      request_status: nav2Status?.request_status ?? "blocked",
      status: asString(findFirstKey(nav2Status?.payload, ["status", "lifecycle_state", "nav2_status"]), "not_loaded"),
    },
    missing_requirements: [reason],
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: readbacks.flatMap((item) => item.dangerous_true_fields.map((field) => `${item.id}.${field}`)),
    robot_control_executed: false,
  };
}

export async function buildNavGoalPreflightProxy(
  baseUrl: string,
  body: unknown,
): Promise<RobotControlNavGoalPreflightResponse> {
  // 这是“执行导航前最小门禁”，不是导航执行入口；定位/路线只读展示，不能再变成普通用户额外预检。
  const sanitized = sanitizeNavGoalPreflightBody(body);
  if (!sanitized.ok) {
    return blockedNavGoalPreflightResponse(baseUrl, sanitized.reason);
  }
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedNavGoalPreflightResponse(baseUrl, normalized.reason, sanitized.body);
  }

  const readbacks = await Promise.all(NAV_GOAL_PREFLIGHT_ENDPOINTS.map((endpoint) => readEndpoint(normalized.normalized, endpoint)));
  const localize = readbackById(readbacks, "localize_proof_latest");
  const nav2Proof = readbackById(readbacks, "nav2_proof_latest");
  const nav2Status = readbackById(readbacks, "nav2_status");
  const operatorReportPreflight = notRequiredNav2OperatorReportPreflight();
  const hardDangerous = readbacks.flatMap((item) => item.dangerous_true_fields.map((field) => `${item.id}.${field}`));
  const localizationPayloads = [localize?.payload ?? null, nav2Proof?.payload ?? null, nav2Status?.payload ?? null];
  const localizationResetObserved =
    booleanObserved(localize?.payload ?? null, ["localization_reset_observed"]) ||
    statusMentions(localize?.payload ?? null, "localization_reset_observed");
  const localizationRuntimeObserved = localizationPayloads.some((payload) =>
    statusMentions(payload, "nav2_no_motion_localization_runtime_observed") ||
    statusMentions(payload, "nav2_no_motion_path_generation_runtime_observed") ||
    booleanObserved(payload, ["amcl_pose_observed"]),
  );
  const mapToBaseLink = localizationPayloads.some((payload) => mapToBaseLinkObserved(payload));
  const pathGenerated = booleanObserved(nav2Proof?.payload ?? null, ["path_generated", "latest_path_generated"]);
  const pathSucceeded = booleanObserved(nav2Proof?.payload ?? null, ["path_generation_succeeded"]);
  const pathPointCount = numericField(nav2Proof?.payload ?? null, ["path_point_count", "latest_path_point_count"]);
  const missingRequirements = [
    sanitized.body.confirm_navigation_preflight ? "" : "confirm_navigation_preflight_required",
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
  ].filter(Boolean);
  const proxyStatus = missingRequirements.length === 0 ? "preflight_passed" : "preflight_rejected";
  const response: RobotControlNavGoalPreflightResponse = {
    schema: "trashbot.pc_tools_workstation.robot_control_nav_goal_preflight.v1",
    ...PROOF_FLAGS,
    proxy_status: proxyStatus,
    preflight_status: proxyStatus === "preflight_passed" ? "ready_for_navigation_goal_not_executed" : "preflight_rejected",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    workstation_endpoint: "/api/robot-control/nav2/goal/preflight",
    remote_methods_used: ["GET"],
    remote_read_endpoints: publicReadbacks(readbacks),
    forbidden_remote_endpoints_not_called: ["/api/nav2/start", "NavigateToPose", "/cmd_vel", "/api/base/manual"],
    goal_request: sanitized.body,
    goal_limits: NAV_GOAL_PREFLIGHT_GOAL_LIMITS,
    operator_report_preflight: operatorReportPreflight,
    localization_summary: {
      request_status: localize?.request_status ?? "blocked",
      status: asString(findFirstKey(localize?.payload, ["status", "latest_proof_status", "latest_result_status"]), "not_loaded"),
      localization_reset_observed: localizationResetObserved,
      nav2_no_motion_localization_runtime_observed: localizationRuntimeObserved,
      map_to_base_link: mapToBaseLink,
      source: mapToBaseLink || localizationRuntimeObserved ? "localize_or_nav2_proof_latest" : "localize_proof_latest",
    },
    nav2_path_summary: {
      request_status: nav2Proof?.request_status ?? "blocked",
      status: asString(findFirstKey(nav2Proof?.payload, ["status", "latest_proof_status", "latest_result_status"]), "not_loaded"),
      path_generated: pathGenerated,
      path_generation_succeeded: pathSucceeded,
      path_point_count: pathPointCount,
    },
    nav2_status_summary: {
      request_status: nav2Status?.request_status ?? "blocked",
      status: asString(findFirstKey(nav2Status?.payload, ["status", "lifecycle_state", "nav2_status"]), "not_loaded"),
    },
    missing_requirements: missingRequirements,
    failure_reason: missingRequirements[0] ?? "",
    blocked_reasons: missingRequirements,
    hard_dangerous_true_fields: hardDangerous,
    robot_control_executed: false,
  };
  return response;
}

function mapNamesFromPayload(payload: JsonRecord | null): string[] {
  // 地图列表只暴露短文件名摘要，避免把完整上位机路径或大量列表铺进首页。
  const maps = findFirstKey(payload, ["maps"]);
  if (!Array.isArray(maps)) {
    return [];
  }
  return maps.slice(0, 12).flatMap((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      return [];
    }
    const record = item as JsonRecord;
    return typeof record.name === "string" && record.name.trim() ? [record.name.trim().slice(0, 120)] : [];
  });
}

function mapCountFromPayload(payload: JsonRecord | null): number | null {
  // map_count 优先使用上位机字段；缺字段时用 maps 数组长度兜底，仍不证明地图质量。
  const count = findFirstKey(payload, ["map_count"]);
  if (typeof count === "number" && Number.isFinite(count)) {
    return count;
  }
  const maps = findFirstKey(payload, ["maps"]);
  return Array.isArray(maps) ? maps.length : null;
}

function finiteNumberOrZero(value: unknown): number {
  // 上位机质量摘要只接收非负计数；异常值按 0 处理，防止旧 payload 污染 UI。
  return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : 0;
}

function defaultMapQualitySummary(status: RobotControlMapQualitySummary["status"] = "not_loaded"): RobotControlMapQualitySummary {
  // 旧上位机或代理失败都保留稳定结构，未知状态不能被当作有可导航地图。
  return {
    status,
    message: status === "not_loaded" ? "地图质量还没有读取。" : "没有可分析的 YAML 地图。",
    checked_yaml_count: 0,
    usable_map_count: 0,
    no_free_cell_map_count: 0,
    analysis_failed_count: 0,
  };
}

function mapQualitySummaryFromPayload(payload: JsonRecord | null): RobotControlMapQualitySummary {
  // PC 只透出上位机聚合后的短摘要；完整 YAML/PGM 路径留在远端 artifact，不进普通 UI。
  const summary = asRecord(findFirstKey(payload, ["map_quality_summary"]));
  if (!summary) {
    return defaultMapQualitySummary();
  }
  const rawStatus = asString(summary.status, "not_checked");
  const status: RobotControlMapQualitySummary["status"] =
    rawStatus === "has_usable_map" || rawStatus === "no_free_cells" || rawStatus === "analysis_failed" || rawStatus === "not_checked"
      ? rawStatus
      : "not_checked";
  return {
    status,
    message: asString(summary.message, defaultMapQualitySummary(status).message),
    checked_yaml_count: finiteNumberOrZero(summary.checked_yaml_count),
    usable_map_count: finiteNumberOrZero(summary.usable_map_count),
    no_free_cell_map_count: finiteNumberOrZero(summary.no_free_cell_map_count),
    analysis_failed_count: finiteNumberOrZero(summary.analysis_failed_count),
  };
}

function commandResultSummary(payload: JsonRecord | null): RobotControlMapLifecycleResponse["command_result"] {
  // command_result.executed 只作为诊断字段；PC 响应顶层 robot_control_executed 仍固定 false。
  const commandResult = asRecord(findFirstKey(payload, ["command_result"]));
  return {
    mode: asString(commandResult?.mode, "not_loaded"),
    executed: commandResult?.executed === true,
    ok: typeof commandResult?.ok === "boolean" ? commandResult.ok : null,
  };
}

function blockedRadarLifecycleResponse(
  sourceBaseUrl: string,
  config: RobotRadarLifecycleConfig,
  reason: string,
): RobotControlRadarLifecycleResponse {
  // URL、fetch 或危险字段失败时仍返回完整合同，前端不需要为错误态伪造安全字段。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: "lifecycle_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: config.endpoint,
    remote_method: "POST",
    remote_http_status: null,
    status: "blocked",
    command_result: { mode: "not_loaded", executed: false, ok: null },
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function blockedNav2LifecycleResponse(
  sourceBaseUrl: string,
  config: RobotNav2LifecycleConfig,
  reason: string,
): RobotControlNav2LifecycleResponse {
  // Nav2 lifecycle 只恢复/停止服务进程；失败合同不能把它伪装成导航执行结果。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_nav2_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: "lifecycle_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: config.endpoint,
    remote_method: "POST",
    remote_http_status: null,
    status: "blocked",
    command_result: { mode: "not_loaded", executed: false, ok: null },
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function remoteBlockedReasons(payload: JsonRecord | null): string[] {
  // 上位机 guard 的 blocked_reasons 是诊断信息，不自动等同 PC 代理拦截。
  return stringList(findFirstKey(payload, ["blocked_reasons"]), 8);
}

function remoteFailureReasons(payload: JsonRecord | null, prefix: string): string[] {
  // 远端明确 failure 才影响代理状态；command_result.executed 只是诊断字段，不再单独判失败。
  const reasons: string[] = [];
  const failure = asString(findFirstKey(payload, ["failure_reason"]), "");
  if (failure) {
    reasons.push(`${prefix}_remote_failure:${failure}`);
  }
  const error = findFirstKey(payload, ["error"]);
  if (typeof error === "string" && error.trim()) {
    reasons.push(`${prefix}_remote_error:${error.trim().slice(0, 120)}`);
  } else if (error && typeof error === "object") {
    reasons.push(`${prefix}_remote_error`);
  }
  return reasons;
}

export async function buildRadarLifecycleProxy(
  baseUrl: string,
  action: RobotControlRadarLifecycleAction,
): Promise<RobotControlRadarLifecycleResponse> {
  // Radar lifecycle 只代理 start/stop 两个固定传感器 endpoint；浏览器 body 被忽略。
  const config = RADAR_LIFECYCLE_CONFIGS[action];
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedRadarLifecycleResponse(baseUrl, config, normalized.reason);
  }

  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, config.endpoint), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
      signal: AbortSignal.timeout(5000),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? "fetch_timeout_5000ms"
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return {
      ...blockedRadarLifecycleResponse(baseUrl, config, reason),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    };
  }

  let bodyJson: unknown;
  try {
    bodyJson = await response.json();
  } catch {
    return {
      ...blockedRadarLifecycleResponse(baseUrl, config, "response_json_parse_failed"),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_parse_failed", `radar_lifecycle_http_status_${response.status}`],
    };
  }

  const payload = asRecord(bodyJson);
  if (!payload) {
    return {
      ...blockedRadarLifecycleResponse(baseUrl, config, "response_json_not_object"),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_not_object", `radar_lifecycle_http_status_${response.status}`],
    };
  }

  const hardDangerous = scanDangerousTrueFields(payload, "", HARD_DANGEROUS_TRUE_FIELDS);
  const commandResult = commandResultSummary(payload);
  const blockedReasons = [
    ...(response.ok ? [] : [`radar_lifecycle_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
    ...remoteBlockedReasons(payload),
  ];
  const forwarded = response.ok && hardDangerous.length === 0;
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: forwarded ? "lifecycle_forwarded" : "lifecycle_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_method: "POST",
    remote_http_status: response.status,
    status: forwarded ? "loaded_fail_closed_summary" : "blocked",
    command_result: commandResult,
    failure_reason:
      hardDangerous.length > 0
        ? `hard_dangerous_true_field:${hardDangerous[0]}`
        : asString(findFirstKey(payload, ["failure_reason", "error"]), response.ok ? "" : `radar_lifecycle_http_status_${response.status}`),
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    robot_control_executed: false,
  };
}

export async function buildNav2LifecycleProxy(
  baseUrl: string,
  action: RobotControlNav2LifecycleAction,
): Promise<RobotControlNav2LifecycleResponse> {
  // Nav2 lifecycle 只代理 start/stop 两个固定 endpoint；不接受 goal、cmd_vel 或任意 body。
  const config = NAV2_LIFECYCLE_CONFIGS[action];
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedNav2LifecycleResponse(baseUrl, config, normalized.reason);
  }

  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, config.endpoint), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
      signal: AbortSignal.timeout(20_000),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? "fetch_timeout_20000ms"
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return {
      ...blockedNav2LifecycleResponse(baseUrl, config, reason),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    };
  }

  let bodyJson: unknown;
  try {
    bodyJson = await response.json();
  } catch {
    return {
      ...blockedNav2LifecycleResponse(baseUrl, config, "response_json_parse_failed"),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_parse_failed", `nav2_lifecycle_http_status_${response.status}`],
    };
  }

  const payload = asRecord(bodyJson);
  if (!payload) {
    return {
      ...blockedNav2LifecycleResponse(baseUrl, config, "response_json_not_object"),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_not_object", `nav2_lifecycle_http_status_${response.status}`],
    };
  }

  const hardDangerous = scanDangerousTrueFields(payload, "", NAV2_LIFECYCLE_HARD_DANGEROUS_TRUE_FIELDS);
  const commandResult = commandResultSummary(payload);
  const blockedReasons = [
    ...(response.ok ? [] : [`nav2_lifecycle_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
    ...remoteBlockedReasons(payload),
  ];
  const forwarded = response.ok && hardDangerous.length === 0;
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_nav2_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: forwarded ? "lifecycle_forwarded" : "lifecycle_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_method: "POST",
    remote_http_status: response.status,
    status: forwarded ? "loaded_fail_closed_summary" : "blocked",
    command_result: commandResult,
    failure_reason:
      hardDangerous.length > 0
        ? `hard_dangerous_true_field:${hardDangerous[0]}`
        : asString(findFirstKey(payload, ["failure_reason", "error"]), response.ok ? "" : `nav2_lifecycle_http_status_${response.status}`),
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    robot_control_executed: false,
  };
}

function blockedMapLifecycleResponse(
  sourceBaseUrl: string,
  config: RobotMapLifecycleConfig,
  reason: string,
  body: RobotControlMapLifecycleRequest = {},
): RobotControlMapLifecycleResponse {
  // URL、body 或 fetch 被拒时仍返回完整 fail-closed 合同，前端不用另造错误态。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: "lifecycle_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: config.endpoint,
    remote_method: config.method,
    remote_http_status: null,
    status: "blocked",
    map_count: null,
    map_names: [],
    map_quality_summary: defaultMapQualitySummary(),
    map_usable_for_navigation: false,
    map_needs_rebuild: false,
    command_result: { mode: "not_loaded", executed: false, ok: null },
    request_body: body,
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    robot_control_executed: false,
  };
}

function defaultMapPreviewRadarOverlay(reason: string): RobotControlMapPreviewRadarOverlay {
  // 地图预览失败或 URL 不合法时也返回同形 overlay，前端不用猜测雷达层是否存在。
  const explanation = mapRadarOverlayExplanation("not_loaded", reason ? [reason] : [], 0, null);
  const wysiwyg = radarOverlayWysiwygPlainSummary({
    radarStatus: "not_loaded",
    pointCount: "0",
    sourcePointCount: "0",
    frameId: "",
    radarHint: explanation.plain_hint,
    radarNextAction: explanation.next_action_plain,
  });
  return {
    overlay_status: "not_loaded",
    status: "not_loaded",
    plain_hint: explanation.plain_hint,
    wysiwyg_status_plain: wysiwyg.statusPlain,
    wysiwyg_next_action_plain: wysiwyg.nextActionPlain,
    next_action: explanation.next_action,
    next_action_plain: explanation.next_action_plain,
    scan_preview_points: [],
    scan_preview_point_count: 0,
    scan_preview_source_point_count: null,
    scan_preview_frame_id: "",
    points: [],
    count: 0,
    source_count: null,
    frame_id: "",
    robot_pose: null,
    source_endpoint_ids: [],
    blocked_reasons: reason ? [reason] : [],
    blocked_reason_labels: explanation.blocked_reason_labels,
  };
}

function mapPreviewRadarOverlayAliases(
  radarOverlay: RobotControlMapPreviewRadarOverlay,
): Pick<
  RobotControlMapPreviewResponse,
  | "radar_overlay_status"
  | "radar_overlay_plain_hint"
  | "radar_overlay_wysiwyg_status_plain"
  | "radar_overlay_wysiwyg_next_action_plain"
  | "radar_overlay_next_action"
  | "radar_overlay_next_action_plain"
  | "radar_overlay_points"
  | "radar_overlay_count"
  | "radar_overlay_source_count"
  | "radar_overlay_point_count"
  | "radar_overlay_source_point_count"
  | "radar_overlay_scan_preview_point_count"
  | "radar_overlay_scan_preview_source_point_count"
  | "radar_overlay_frame_id"
> {
  // 顶层 alias 与嵌套 overlay 同源，方便现场 curl/jq 一眼确认“地图上到底贴了几个当前雷达点”。
  return {
    radar_overlay_status: radarOverlay.overlay_status,
    radar_overlay_plain_hint: radarOverlay.plain_hint,
    radar_overlay_wysiwyg_status_plain: radarOverlay.wysiwyg_status_plain,
    radar_overlay_wysiwyg_next_action_plain: radarOverlay.wysiwyg_next_action_plain,
    radar_overlay_next_action: radarOverlay.next_action,
    radar_overlay_next_action_plain: radarOverlay.next_action_plain,
    radar_overlay_points: radarOverlay.points,
    radar_overlay_count: radarOverlay.count,
    radar_overlay_source_count: radarOverlay.source_count,
    radar_overlay_point_count: radarOverlay.count,
    radar_overlay_source_point_count: radarOverlay.source_count,
    radar_overlay_scan_preview_point_count: radarOverlay.scan_preview_point_count,
    radar_overlay_scan_preview_source_point_count: radarOverlay.scan_preview_source_point_count,
    radar_overlay_frame_id: radarOverlay.frame_id,
  };
}

function mapRadarOverlayReasonLabel(reason: string): string {
  // overlay token 可能带 endpoint 前缀；普通接口要给现场能直接执行的短标签。
  const normalized = reason.includes(":") ? reason.split(":").slice(1).join(":") : reason;
  const labels: Record<string, string> = {
    robot_pose_missing_for_map_radar_overlay: "小车地图位置未读到",
    runtime_scan_stale_for_map_radar_overlay: "雷达扫描已过期",
    radar_lifecycle_not_running_for_map_radar_overlay: "雷达未运行",
    scan_preview_points_missing_for_map_radar_overlay: "没有可贴图的新雷达点",
    scan_preview_points_missing: "没有可贴图的新雷达点",
  };
  if (normalized.startsWith("fetch_timeout")) {
    return "雷达或定位读取超时";
  }
  return labels[normalized] ?? normalized;
}

function mapRadarOverlayExplanation(
  status: RobotControlMapPreviewRadarOverlay["overlay_status"],
  blockedReasons: string[],
  sourcePointCount: number | null,
  robotPose: RobotApiMapPose | null,
): Pick<RobotControlMapPreviewRadarOverlay, "plain_hint" | "next_action" | "next_action_plain" | "blocked_reason_labels"> {
  const labels = [...new Set(blockedReasons.map(mapRadarOverlayReasonLabel).filter(Boolean))];
  const pointText = sourcePointCount !== null && sourcePointCount > 0 ? `已有雷达来源点 ${sourcePointCount} 个` : "未读到可用雷达点";
  if (status === "loaded") {
    return {
      plain_hint: "雷达点已按当前扫描和小车地图位置贴到地图。",
      next_action: "continue_monitoring_map_radar_overlay",
      next_action_plain: "继续观察地图雷达层。",
      blocked_reason_labels: [],
    };
  }
  if (status === "partial") {
    const hint = robotPose
      ? `${pointText}，但雷达点不完整；地图保留小车位置并等待新点。`
      : `${pointText}，但小车地图位置未读到；当前不能把雷达点贴到地图坐标。`;
    const nextAction = robotPose ? "refresh_radar_scan_for_map_overlay" : "refresh_localization_then_radar_scan";
    return {
      plain_hint: hint,
      next_action: nextAction,
      next_action_plain: robotPose
        ? "刷新雷达扫描，再刷新地图画面。"
        : "先刷新定位，再刷新雷达扫描和地图画面。",
      blocked_reason_labels: labels,
    };
  }
  if (status === "not_current") {
    const hasLifecycleStop = blockedReasons.some((reason) => reason.includes("radar_lifecycle_not_running_for_map_radar_overlay"));
    const hasStaleScan = blockedReasons.some((reason) => reason.includes("runtime_scan_stale_for_map_radar_overlay"));
    const nextAction = hasLifecycleStop ? "start_radar_then_refresh_map_preview" : hasStaleScan ? "refresh_radar_scan_for_map_overlay" : "refresh_map_radar_overlay";
    return {
      plain_hint: `${pointText}，但${labels.join("、") || "雷达状态不是当前"}，所以当前不贴到地图。`,
      next_action: nextAction,
      next_action_plain: hasLifecycleStop
        ? "先启动雷达，再刷新地图画面。"
        : hasStaleScan
          ? "刷新雷达扫描，再刷新地图画面。"
          : "刷新地图画面，让雷达点和地图来自同一轮读数。",
      blocked_reason_labels: labels,
    };
  }
  if (status === "blocked") {
    const nextAction = blockedReasons.some((reason) => reason.includes("robot_pose_missing")) ? "refresh_localization_then_radar_scan" : "start_or_refresh_radar";
    return {
      plain_hint: `地图雷达层材料不足：${labels.join("、") || "未读到雷达或定位材料"}。`,
      next_action: nextAction,
      next_action_plain: nextAction === "refresh_localization_then_radar_scan"
        ? "先刷新定位，再刷新雷达扫描和地图画面。"
        : "启动或刷新雷达后，再刷新地图画面。",
      blocked_reason_labels: labels,
    };
  }
  return {
    plain_hint: blockedReasons.length ? `地图雷达层未加载：${labels.join("、")}。` : "地图雷达层未加载。",
    next_action: "connect_robot_and_refresh_map_preview",
    next_action_plain: "确认小车地址可访问后刷新地图画面。",
    blocked_reason_labels: labels,
  };
}

async function buildMapPreviewOverlayReadback(base: URL): Promise<MapPreviewOverlayReadback> {
  // 地图图片和雷达/位姿 overlay 分开读；overlay 只补“所见即所得”材料，不反向阻塞地图图片。
  const endpoints = READ_ENDPOINTS.filter((endpoint) => MAP_PREVIEW_OVERLAY_ENDPOINT_IDS.has(endpoint.id));
  const readbacks = await Promise.all(endpoints.map((endpoint) => readEndpoint(base, endpoint)));
  const proofSummary = buildProofSummary(readbacks);
  const lidar = lidarSummaryFromReadbacks(readbacks, proofSummary);
  const blockedReasons = readbacks.flatMap((item) => item.blocked_reasons.map((reason) => `${item.id}:${reason}`));
  const hasRadarPoints = proofSummary.scan_preview_point_count > 0 || proofSummary.scan_preview_points.length > 0;
  const hasMapPose = proofSummary.robot_pose !== null;
  const radarRuntimeStale = lidar.runtime_scan_status === "stale";
  const radarLifecycleStopped = lidar.lifecycle_running === "false" || lidar.lifecycle_state === "stopped";
  const radarOverlayCurrent = hasRadarPoints && !radarRuntimeStale && !radarLifecycleStopped;
  const overlayGaps = [
    hasRadarPoints && !hasMapPose ? "robot_pose_missing_for_map_radar_overlay" : "",
    radarRuntimeStale ? "runtime_scan_stale_for_map_radar_overlay" : "",
    radarLifecycleStopped ? "radar_lifecycle_not_running_for_map_radar_overlay" : "",
    hasMapPose && !hasRadarPoints ? "scan_preview_points_missing_for_map_radar_overlay" : "",
  ].filter(Boolean);
  const overlayBlockedReasons = [...blockedReasons, ...overlayGaps];
  const hasCurrentRadarPoints = radarOverlayCurrent;
  const hasVisibleOverlay = hasCurrentRadarPoints || hasMapPose;
  const hasCompleteOverlay = hasCurrentRadarPoints && hasMapPose;
  const overlayStatus: RobotControlMapPreviewRadarOverlay["overlay_status"] = hasRadarPoints && !radarOverlayCurrent
    ? "not_current"
    : hasVisibleOverlay
      ? overlayBlockedReasons.length > 0 || !hasCompleteOverlay ? "partial" : "loaded"
      : overlayBlockedReasons.length > 0 ? "blocked" : "not_loaded";
  const explanation = mapRadarOverlayExplanation(
    overlayStatus,
    overlayBlockedReasons,
    proofSummary.scan_preview_source_point_count,
    proofSummary.robot_pose,
  );
  const visibleRadarPoints = radarOverlayCurrent ? proofSummary.scan_preview_points : [];
  const visibleRadarPointCount = radarOverlayCurrent ? proofSummary.scan_preview_point_count : 0;
  const wysiwyg = radarOverlayWysiwygPlainSummary({
    radarStatus: overlayStatus,
    pointCount: String(visibleRadarPointCount),
    sourcePointCount: proofSummary.scan_preview_source_point_count === null ? "not_loaded" : String(proofSummary.scan_preview_source_point_count),
    frameId: proofSummary.scan_preview_frame_id || "not_loaded",
    radarHint: explanation.plain_hint,
    radarNextAction: explanation.next_action_plain,
  });
  const radarOverlay: RobotControlMapPreviewRadarOverlay = {
    overlay_status: overlayStatus,
    // 兼容普通调试脚本的一眼读法；旧字段仍保留为完整 contract。
    status: overlayStatus,
    plain_hint: explanation.plain_hint,
    wysiwyg_status_plain: wysiwyg.statusPlain,
    wysiwyg_next_action_plain: wysiwyg.nextActionPlain,
    next_action: explanation.next_action,
    next_action_plain: explanation.next_action_plain,
    scan_preview_points: visibleRadarPoints,
    scan_preview_point_count: visibleRadarPointCount,
    scan_preview_source_point_count: proofSummary.scan_preview_source_point_count,
    scan_preview_frame_id: proofSummary.scan_preview_frame_id,
    points: visibleRadarPoints,
    count: visibleRadarPointCount,
    source_count: proofSummary.scan_preview_source_point_count,
    frame_id: proofSummary.scan_preview_frame_id,
    robot_pose: proofSummary.robot_pose,
    source_endpoint_ids: endpoints.map((endpoint) => endpoint.id),
    blocked_reasons: overlayBlockedReasons,
    blocked_reason_labels: explanation.blocked_reason_labels,
  };
  return {
    radarOverlay,
    pathPreview: {
      path_preview_points: proofSummary.path_preview_points,
      path_preview_point_count: proofSummary.path_preview_point_count,
      path_preview_source_point_count: proofSummary.path_preview_source_point_count,
      path_preview_frame_id: proofSummary.path_preview_frame_id,
    },
    sourceEndpointIds: endpoints.map((endpoint) => endpoint.id),
  };
}

function mapPreviewPlainSummary(
  mapStatusPlain: string,
  radarStatusPlain: string,
  mapNextActionPlain: string,
): { plainHint: string; mapPlainHint: string; nextActionPlain: string } {
  // map preview 顶层口径按“地图/路线/小车”和“雷达 marker”分层，避免把旧雷达来源点重复说成当前贴图。
  const { map, radar } = currentFactMapRadarParts(mapStatusPlain, radarStatusPlain);
  const plainParts = [map, radar].filter(Boolean);
  const mapPlainHint = map ? `${map}。` : "地图画面未读到；不能把旧图或空白图当作当前所见。";
  return {
    plainHint: plainParts.length ? `${plainParts.join("；")}。` : mapPlainHint,
    mapPlainHint,
    nextActionPlain: mapNextActionPlain,
  };
}

function blockedMapPreviewResponse(
  sourceBaseUrl: string,
  reason: string,
  radarOverlay: RobotControlMapPreviewRadarOverlay = defaultMapPreviewRadarOverlay(reason),
  pathPreview: MapPreviewPathPreview = {
    path_preview_points: [],
    path_preview_point_count: 0,
    path_preview_source_point_count: null,
    path_preview_frame_id: "",
  },
  pathPreviewSourceEndpointIds: RobotApiReadEndpointId[] = [],
): RobotControlMapPreviewResponse {
  // 地图预览失败也必须保持完整合同，前端才能稳定回退到状态视图。
  const pathStatus = pathPreview.path_preview_point_count > 0 ? "path_preview_observed" : "not_observed";
  const poseStatus = radarOverlay.robot_pose ? "map_pose_observed" : "not_observed";
  const pathNextActionPlain = mapPreviewPathNextActionPlain(pathStatus, poseStatus);
  const mapWysiwyg = mapWysiwygPlainSummary({
    mapObserved: "false",
    pathStatus,
    poseStatus,
    radarStatus: radarOverlay.overlay_status,
    radarHint: radarOverlay.plain_hint,
    pathNextAction: pathNextActionPlain,
    radarNextAction: radarOverlay.next_action_plain,
  });
  const pathWysiwygStatusPlain = pathStatus === "path_preview_observed"
    ? "图上路线已显示在当前地图画面。"
    : "图上路线未显示；不能把旧路线或空路线当作当前所见。";
  const previewPlain = mapPreviewPlainSummary(
    mapWysiwyg.statusPlain,
    radarOverlay.wysiwyg_status_plain,
    mapWysiwyg.nextActionPlain,
  );
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_map_preview_proxy.v1",
    ...PROOF_FLAGS,
    proxy_status: "preview_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: "/api/map/preview",
    remote_http_status: null,
    status: "blocked",
    plain_hint: previewPlain.plainHint,
    map_plain_hint: previewPlain.mapPlainHint,
    map_next_action_plain: previewPlain.nextActionPlain,
    map_name: "",
    map_yaml_name: "",
    map_image_name: "",
    width: 0,
    height: 0,
    resolution: null,
    origin: [],
    cell_counts: {},
    has_free_cells: false,
    navigation_quality: "not_loaded",
    image_mime_type: "not_loaded",
    image_data_url: "",
    source_image_format: "not_loaded",
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    radar_overlay: radarOverlay,
    map_wysiwyg_status_plain: mapWysiwyg.statusPlain,
    map_wysiwyg_next_action_plain: mapWysiwyg.nextActionPlain,
    ...mapPreviewRadarOverlayAliases(radarOverlay),
    robot_pose: radarOverlay.robot_pose,
    robot_pose_status: poseStatus,
    path_preview_points: pathPreview.path_preview_points,
    path_preview_status: pathStatus,
    path_preview_next_action_plain: pathNextActionPlain,
    next_action_plain: previewPlain.nextActionPlain,
    path_wysiwyg_status_plain: pathWysiwygStatusPlain,
    path_wysiwyg_next_action_plain: pathNextActionPlain,
    nav2_route_overlay_status: pathStatus,
    nav2_route_overlay_point_count: pathPreview.path_preview_point_count,
    nav2_route_overlay_next_action_plain: pathNextActionPlain,
    path_preview_point_count: pathPreview.path_preview_point_count,
    path_preview_source_point_count: pathPreview.path_preview_source_point_count,
    path_preview_frame_id: pathPreview.path_preview_frame_id,
    path_preview_source_endpoint_ids: pathPreviewSourceEndpointIds,
    robot_control_executed: false,
  };
}

function mapPreviewPathNextActionPlain(
  pathStatus: RobotControlMapPreviewResponse["path_preview_status"],
  poseStatus: RobotControlMapPreviewResponse["robot_pose_status"],
): string {
  // map preview 是现场正在看的画面；下一步只解释读图动作，不触发路线准备或执行。
  if (pathStatus !== "path_preview_observed") {
    return "先准备图上路线，再刷新地图画面。";
  }
  if (poseStatus !== "map_pose_observed") {
    return "图上路线已显示；小车位置未显示，建议刷新定位或地图后再执行。";
  }
  return "图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。";
}

function mapWysiwygPlainSummary(args: {
  mapObserved: string;
  pathStatus: string;
  poseStatus: string;
  radarStatus: string;
  radarHint: string;
  pathNextAction: string;
  radarNextAction: string;
}): { statusPlain: string; nextActionPlain: string } {
  // 地图总口径把图、路线、小车位置和雷达层一次讲清；脚本不用再拼多个 readback 字段。
  if (args.mapObserved !== "true") {
    return {
      statusPlain: "地图画面未读到；不能把旧图或空白图当作当前所见。",
      nextActionPlain: "先刷新地图画面。",
    };
  }
  if (args.pathStatus !== "path_preview_observed") {
    return {
      statusPlain: "地图画面已读到，但图上路线还未显示。",
      nextActionPlain: args.pathNextAction,
    };
  }
  if (args.poseStatus !== "map_pose_observed") {
    return {
      statusPlain: "地图画面和图上路线已显示，但小车地图位置未显示。",
      nextActionPlain: args.pathNextAction,
    };
  }
  if (args.radarStatus === "loaded") {
    return {
      statusPlain: "地图画面、图上路线、小车位置和雷达标记都已按当前读数显示。",
      nextActionPlain: "继续按当前地图画面确认路线和雷达层。",
    };
  }
  if (args.radarStatus === "partial") {
    return {
      statusPlain: `地图画面、图上路线和小车位置已显示；雷达层只显示局部读数：${args.radarHint}`,
      nextActionPlain: args.radarNextAction,
    };
  }
  if (args.radarStatus === "not_current") {
    return {
      statusPlain: `地图画面、图上路线和小车位置已显示；雷达来源点存在但当前不贴到地图：${args.radarHint}`,
      nextActionPlain: args.radarNextAction,
    };
  }
  return {
    statusPlain: `地图画面、图上路线和小车位置已显示；雷达层还未加载：${args.radarHint}`,
    nextActionPlain: args.radarNextAction,
  };
}

function radarOverlayWysiwygPlainSummary(args: {
  radarStatus: string;
  pointCount: string;
  sourcePointCount: string;
  frameId: string;
  radarHint: string;
  radarNextAction: string;
}): { statusPlain: string; nextActionPlain: string } {
  // 雷达 WYSIWYG 单独说明“地图上实际画了几个 marker”，避免把旧来源点误当成当前贴图。
  const displayedCount = args.pointCount && args.pointCount !== "not_loaded" ? args.pointCount : "0";
  const sourceCount = args.sourcePointCount && args.sourcePointCount !== "not_loaded" ? args.sourcePointCount : "0";
  const frameText = args.frameId && args.frameId !== "not_loaded" ? `，frame=${args.frameId}` : "";
  if (args.radarStatus === "loaded") {
    return {
      statusPlain: `雷达 marker 已贴到当前地图：当前显示 ${displayedCount} 个点${frameText}。`,
      nextActionPlain: "继续观察地图雷达层。",
    };
  }
  if (args.radarStatus === "partial") {
    return {
      statusPlain: `雷达材料已读到 ${sourceCount} 个来源点，当前可用雷达点 ${displayedCount} 个，但地图贴图未完整确认；${args.radarHint}`,
      nextActionPlain: args.radarNextAction,
    };
  }
  if (args.radarStatus === "not_current") {
    return {
      statusPlain: `雷达 marker 未贴到当前地图：当前显示 ${displayedCount} 个点；旧来源点 ${sourceCount} 个只作诊断。${args.radarHint}`,
      nextActionPlain: args.radarNextAction,
    };
  }
  return {
    statusPlain: `雷达 marker 未加载：当前显示 ${displayedCount} 个点；来源点 ${sourceCount} 个。${args.radarHint}`,
    nextActionPlain: args.radarNextAction,
  };
}

export async function buildMapPreviewProxy(baseUrl: string): Promise<RobotControlMapPreviewResponse> {
  // Map preview 是只读固定代理；它只能读上位机 /api/map/preview，不能转成任意文件或控制代理。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedMapPreviewResponse(baseUrl, normalized.reason);
  }
  const overlayReadbackPromise = buildMapPreviewOverlayReadback(normalized.normalized);

  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, "/api/map/preview"), {
      method: "GET",
      signal: AbortSignal.timeout(8_000),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? "fetch_timeout_8000ms"
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    const overlayReadback = await overlayReadbackPromise;
    return {
      ...blockedMapPreviewResponse(
        baseUrl,
        reason,
        overlayReadback.radarOverlay,
        overlayReadback.pathPreview,
        overlayReadback.sourceEndpointIds,
      ),
      proxy_status: "preview_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    };
  }

  let bodyJson: unknown;
  try {
    bodyJson = await response.json();
  } catch {
    const overlayReadback = await overlayReadbackPromise;
    return {
      ...blockedMapPreviewResponse(
        baseUrl,
        "response_json_parse_failed",
        overlayReadback.radarOverlay,
        overlayReadback.pathPreview,
        overlayReadback.sourceEndpointIds,
      ),
      proxy_status: "preview_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_parse_failed", `map_preview_http_status_${response.status}`],
    };
  }

  const payload = asRecord(bodyJson);
  if (!payload) {
    const overlayReadback = await overlayReadbackPromise;
    return {
      ...blockedMapPreviewResponse(
        baseUrl,
        "response_json_not_object",
        overlayReadback.radarOverlay,
        overlayReadback.pathPreview,
        overlayReadback.sourceEndpointIds,
      ),
      proxy_status: "preview_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_not_object", `map_preview_http_status_${response.status}`],
    };
  }

  const hardDangerous = scanDangerousTrueFields(payload, "", HARD_DANGEROUS_TRUE_FIELDS);
  const imageDataUrl = asString(findFirstKey(payload, ["image_data_url"]), "");
  const imageLooksSafe = imageDataUrl.startsWith("data:image/png;base64,") && imageDataUrl.length < 2_000_000;
  const resolutionValue = findFirstKey(payload, ["resolution"]);
  const cellCountsRaw = asRecord(findFirstKey(payload, ["cell_counts"]));
  const cellCounts = cellCountsRaw
    ? Object.fromEntries(
      Object.entries(cellCountsRaw)
        .filter((entry): entry is [string, number] => typeof entry[1] === "number" && Number.isFinite(entry[1])),
    )
    : {};
  const blockedReasons = [
    ...(response.ok ? [] : [`map_preview_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
    ...remoteFailureReasons(payload, "map_preview"),
    ...(imageLooksSafe ? [] : ["map_preview_image_data_url_missing_or_invalid"]),
  ];
  const forwarded = response.ok && blockedReasons.length === 0;
  const overlayReadback = await overlayReadbackPromise;
  const pathStatus = overlayReadback.pathPreview.path_preview_point_count > 0 ? "path_preview_observed" : "not_observed";
  const poseStatus = overlayReadback.radarOverlay.robot_pose ? "map_pose_observed" : "not_observed";
  const pathNextActionPlain = mapPreviewPathNextActionPlain(pathStatus, poseStatus);
  const mapWysiwyg = mapWysiwygPlainSummary({
    mapObserved: forwarded ? "true" : "false",
    pathStatus,
    poseStatus,
    radarStatus: overlayReadback.radarOverlay.overlay_status,
    radarHint: overlayReadback.radarOverlay.plain_hint,
    pathNextAction: pathNextActionPlain,
    radarNextAction: overlayReadback.radarOverlay.next_action_plain,
  });
  const pathWysiwygStatusPlain = pathStatus === "path_preview_observed"
    ? "图上路线已显示在当前地图画面。"
    : "图上路线未显示；不能把旧路线或空路线当作当前所见。";
  const previewPlain = mapPreviewPlainSummary(
    mapWysiwyg.statusPlain,
    overlayReadback.radarOverlay.wysiwyg_status_plain,
    mapWysiwyg.nextActionPlain,
  );
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_map_preview_proxy.v1",
    ...PROOF_FLAGS,
    proxy_status: forwarded ? "preview_forwarded" : "preview_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: "/api/map/preview",
    remote_http_status: response.status,
    status: forwarded ? "loaded_fail_closed_summary" : "blocked",
    plain_hint: previewPlain.plainHint,
    map_plain_hint: previewPlain.mapPlainHint,
    map_next_action_plain: previewPlain.nextActionPlain,
    map_name: asString(findFirstKey(payload, ["map_name"]), ""),
    map_yaml_name: asString(findFirstKey(payload, ["map_yaml_name"]), ""),
    map_image_name: asString(findFirstKey(payload, ["map_image_name"]), ""),
    width: finiteNumberOrZero(findFirstKey(payload, ["width"])),
    height: finiteNumberOrZero(findFirstKey(payload, ["height"])),
    resolution: typeof resolutionValue === "number" && Number.isFinite(resolutionValue) ? resolutionValue : null,
    origin: numberList(findFirstKey(payload, ["origin"]), 3),
    cell_counts: cellCounts,
    has_free_cells: findFirstKey(payload, ["has_free_cells"]) === true,
    navigation_quality: asString(findFirstKey(payload, ["navigation_quality"]), "not_loaded"),
    image_mime_type: imageLooksSafe ? "image/png" : "not_loaded",
    image_data_url: imageLooksSafe ? imageDataUrl : "",
    source_image_format: asString(findFirstKey(payload, ["source_image_format"]), "not_loaded"),
    failure_reason:
      blockedReasons.length > 0
        ? blockedReasons[0] ?? "map_preview_blocked"
        : asString(findFirstKey(payload, ["failure_reason", "error"]), ""),
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    radar_overlay: overlayReadback.radarOverlay,
    map_wysiwyg_status_plain: mapWysiwyg.statusPlain,
    map_wysiwyg_next_action_plain: mapWysiwyg.nextActionPlain,
    ...mapPreviewRadarOverlayAliases(overlayReadback.radarOverlay),
    robot_pose: overlayReadback.radarOverlay.robot_pose,
    robot_pose_status: poseStatus,
    path_preview_points: overlayReadback.pathPreview.path_preview_points,
    path_preview_status: pathStatus,
    path_preview_next_action_plain: pathNextActionPlain,
    next_action_plain: previewPlain.nextActionPlain,
    path_wysiwyg_status_plain: pathWysiwygStatusPlain,
    path_wysiwyg_next_action_plain: pathNextActionPlain,
    nav2_route_overlay_status: pathStatus,
    nav2_route_overlay_point_count: overlayReadback.pathPreview.path_preview_point_count,
    nav2_route_overlay_next_action_plain: pathNextActionPlain,
    path_preview_point_count: overlayReadback.pathPreview.path_preview_point_count,
    path_preview_source_point_count: overlayReadback.pathPreview.path_preview_source_point_count,
    path_preview_frame_id: overlayReadback.pathPreview.path_preview_frame_id,
    path_preview_source_endpoint_ids: overlayReadback.sourceEndpointIds,
    robot_control_executed: false,
  };
}

export async function buildMapLifecycleProxy(
  baseUrl: string,
  action: RobotControlMapLifecycleAction,
  body: unknown = {},
): Promise<RobotControlMapLifecycleResponse> {
  // 这里是建图 lifecycle 的唯一固定代理：action 决定白名单 endpoint，浏览器不能传动态路径。
  const config = MAP_LIFECYCLE_CONFIGS[action];
  const sanitized = config.method === "GET" ? { ok: true as const, body: {} } : sanitizeMapLifecycleBody(body);
  if (!sanitized.ok) {
    return blockedMapLifecycleResponse(baseUrl, config, sanitized.reason);
  }
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedMapLifecycleResponse(baseUrl, config, normalized.reason, sanitized.body);
  }

  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, config.endpoint), {
      method: config.method,
      headers: config.method === "POST" ? { "Content-Type": "application/json" } : undefined,
      body: config.method === "POST" ? JSON.stringify(sanitized.body) : undefined,
      signal: AbortSignal.timeout(config.action === "start" || config.action === "save" ? 120_000 : 5_000),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? `fetch_timeout_${config.action === "start" || config.action === "save" ? 120_000 : 5_000}ms`
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return {
      ...blockedMapLifecycleResponse(baseUrl, config, reason, sanitized.body),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    };
  }

  let bodyJson: unknown;
  try {
    bodyJson = await response.json();
  } catch {
    return {
      ...blockedMapLifecycleResponse(baseUrl, config, "response_json_parse_failed", sanitized.body),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_parse_failed", `map_lifecycle_http_status_${response.status}`],
    };
  }

  const payload = asRecord(bodyJson);
  if (!payload) {
    return {
      ...blockedMapLifecycleResponse(baseUrl, config, "response_json_not_object", sanitized.body),
      proxy_status: "lifecycle_failed",
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_http_status: response.status,
      blocked_reasons: ["response_json_not_object", `map_lifecycle_http_status_${response.status}`],
    };
  }

  const hardDangerous = scanDangerousTrueFields(payload, "", HARD_DANGEROUS_TRUE_FIELDS);
  const commandResult = commandResultSummary(payload);
  const mapQualitySummary = mapQualitySummaryFromPayload(payload);
  const mapUsableForNavigation = payload.map_usable_for_navigation === true || mapQualitySummary.status === "has_usable_map";
  const mapNeedsRebuild = payload.map_needs_rebuild === true || mapQualitySummary.status === "no_free_cells" || mapQualitySummary.status === "analysis_failed";
  const blockedReasons = [
    ...(response.ok ? [] : [`map_lifecycle_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
    ...remoteFailureReasons(payload, "map_lifecycle"),
  ];
  const forwarded = response.ok && blockedReasons.length === 0;
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1",
    ...PROOF_FLAGS,
    action: config.action,
    proxy_status: forwarded ? "lifecycle_forwarded" : "lifecycle_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_method: config.method,
    remote_http_status: response.status,
    status: forwarded ? "loaded_fail_closed_summary" : "blocked",
    map_count: mapCountFromPayload(payload),
    map_names: mapNamesFromPayload(payload),
    map_quality_summary: mapQualitySummary,
    map_usable_for_navigation: mapUsableForNavigation,
    map_needs_rebuild: mapNeedsRebuild,
    command_result: commandResult,
    request_body: sanitized.body,
    failure_reason:
      blockedReasons.length > 0
        ? blockedReasons[0] ?? "map_lifecycle_blocked"
        : asString(findFirstKey(payload, ["failure_reason", "error"]), ""),
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    robot_control_executed: false,
  };
}

async function readEndpoint(base: URL, config: RobotReadEndpointConfig, timeoutOverrideMs?: number): Promise<InternalRobotApiEndpointReadback> {
  // 每条读请求都按白名单 endpoint 带独立超时；慢端点允许更宽窗口，但范围仍局限在只读 GET。
  const { id, endpoint, timeout_ms } = config;
  const effectiveTimeoutMs = timeoutOverrideMs && Number.isFinite(timeoutOverrideMs)
    ? Math.max(1, Math.min(timeout_ms, Math.floor(timeoutOverrideMs)))
    : timeout_ms;
  const url = endpointUrl(base, endpoint);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      signal: AbortSignal.timeout(effectiveTimeoutMs),
    });
  } catch (error) {
    const timeoutReason =
      error instanceof Error && error.name === "TimeoutError"
        ? `fetch_timeout_${effectiveTimeoutMs}ms`
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return {
      id,
      endpoint,
      http_status: null,
      request_status: "fetch_failed",
      schema: "not_loaded",
      status: "fetch_failed",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: [timeoutReason],
      dangerous_true_fields: [],
      payload: null,
    };
  }

  if (OPTIONAL_MISSING_HTTP_STATUSES.has(response.status) && OPTIONAL_MISSING_READ_ENDPOINT_IDS.has(id)) {
    // 旧上位机可能还没有该 latest 端点；只读 artifact 缺失不能把 PC 整体连接打成 blocked。
    return {
      id,
      endpoint,
      http_status: response.status,
      request_status: "loaded",
      schema: "not_loaded",
      status: "missing",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: [],
      dangerous_true_fields: [],
      payload: null,
    };
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return {
      id,
      endpoint,
      http_status: response.status,
      request_status: "bad_json",
      schema: "not_loaded",
      status: "bad_json",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: ["response_json_parse_failed"],
      dangerous_true_fields: [],
      payload: null,
    };
  }

  const payload = asRecord(body);
  if (!payload) {
    return {
      id,
      endpoint,
      http_status: response.status,
      request_status: "not_object",
      schema: "not_object",
      status: "not_object",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: ["response_json_not_object"],
      dangerous_true_fields: [],
      payload: null,
    };
  }

  if (OPTIONAL_MISSING_HTTP_STATUSES.has(response.status) && OPTIONAL_MISSING_READ_ENDPOINT_IDS.has(id)) {
    // 旧上位机可能还没有独立 latest 端点；这只说明证据缺失，不该把整机连接打成 blocked。
    return {
      id,
      endpoint,
      http_status: response.status,
      request_status: "loaded",
      schema: asString(payload.schema, "schema_missing"),
      status: "missing",
      evidence_ref: "not_loaded",
      key_values: {},
      blocked_reasons: [],
      dangerous_true_fields: [],
      payload,
    };
  }

  const dangerous = scanDangerousTrueFields(
    payload,
    "",
    DANGEROUS_TRUE_FIELDS,
    dangerousTrueFieldExemptionsForEndpoint(id),
  );
  const status = asString(findFirstKey(payload, ["status", "latest_proof_status", "state"]), response.ok ? "loaded" : "blocked");
  return {
    id,
    endpoint,
    http_status: response.status,
    request_status: response.ok && dangerous.length === 0 ? "loaded" : "blocked",
    schema: asString(payload.schema, "schema_missing"),
    status,
    evidence_ref: asString(findFirstKey(payload, ["evidence_ref", "latest_evidence_ref"]), "not_loaded"),
    key_values: compactKeyValues(payload),
    blocked_reasons: [
      ...(response.ok ? [] : [`http_status_${response.status}`]),
      ...dangerous.map((field) => `dangerous_true_field:${field}`),
    ],
    dangerous_true_fields: dangerous,
    payload,
  };
}

function blockedRefreshResponse(
  sourceBaseUrl: string,
  reason: string,
  config: RobotProofRefreshConfig,
): RobotControlProofRefreshProxyResponse {
  // 固定 POST 刷新端点在 URL 不合法时也必须返回同一套 fail-closed 字段，避免 UI 分叉。
  const observedAt = Date.now();
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
    ...PROOF_FLAGS,
    refresh_kind: config.kind,
    proxy_status: "refresh_rejected",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    remote_endpoint: config.endpoint,
    remote_http_status: null,
    status: "blocked",
    last_result_status: "blocked_not_proven",
    last_result_schema: "not_loaded",
    last_result_evidence_ref: "not_loaded",
    last_refreshed_at_ms: observedAt,
    latest_readback_key_values: {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    non_motion_evidence_actions_observed: [],
    robot_control_executed: false,
  };
}

function failedRefreshResponse(
  sourceBaseUrl: string,
  normalizedBaseUrl: URL,
  reason: string,
  config: RobotProofRefreshConfig,
  observedAt: number,
  extras: Partial<RobotControlProofRefreshProxyResponse> = {},
): RobotControlProofRefreshProxyResponse {
  // POST 失败和 Nav2 latest 兜底共用一套响应骨架，避免在错误态漏掉 fail-closed 字段。
  return {
    schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
    ...PROOF_FLAGS,
    refresh_kind: config.kind,
    proxy_status: "refresh_failed",
    source_base_url: sourceBaseUrl,
    normalized_base_url: normalizedBaseUrl.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_http_status: null,
    status: "blocked",
    last_result_status: "fetch_failed",
    last_result_schema: "not_loaded",
    last_result_evidence_ref: "not_loaded",
    last_refreshed_at_ms: observedAt,
    latest_readback_key_values: {},
    failure_reason: reason,
    blocked_reasons: [reason],
    hard_dangerous_true_fields: [],
    non_motion_evidence_actions_observed: [],
    robot_control_executed: false,
    ...extras,
  };
}

async function nav2LatestReadbackAfterPostFailure(
  baseUrl: string,
  normalizedBaseUrl: URL,
  config: RobotProofRefreshConfig,
  observedAt: number,
  postFailureReason: string,
): Promise<RobotControlProofRefreshProxyResponse> {
  // 只给 Nav2 no-motion refresh 提供固定 latest GET 兜底；不能扩展成任意 GET/POST 代理。
  if (config.kind !== "nav2_no_motion_proof_refresh") {
    return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt);
  }

  let latestResponse: Response;
  try {
    latestResponse = await fetch(endpointUrl(normalizedBaseUrl, NAV2_NO_MOTION_PROOF_LATEST_ENDPOINT), {
      method: "GET",
      signal: AbortSignal.timeout(DEFAULT_REQUEST_TIMEOUT_MS),
    });
  } catch (error) {
    const latestFailure =
      error instanceof Error && error.name === "TimeoutError"
        ? `latest_fetch_timeout_${DEFAULT_REQUEST_TIMEOUT_MS}ms`
        : error instanceof Error
          ? `latest_fetch_failed:${error.message.slice(0, 160)}`
          : "latest_fetch_failed";
    return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
      blocked_reasons: [postFailureReason, latestFailure],
    });
  }

  const latestBody = await latestResponse.json().catch(() => null);
  const latestPayload = asRecord(latestBody);
  if (!latestResponse.ok || !latestPayload) {
    return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
      blocked_reasons: [
        postFailureReason,
        latestPayload ? `latest_http_status_${latestResponse.status}` : "latest_response_json_not_object",
      ],
    });
  }

  const hardDangerous = scanDangerousTrueFields(latestPayload, "", HARD_DANGEROUS_TRUE_FIELDS);
  if (hardDangerous.length > 0) {
    return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
      failure_reason: `hard_dangerous_true_field:${hardDangerous[0]}`,
      blocked_reasons: [
        postFailureReason,
        ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
      ],
      hard_dangerous_true_fields: hardDangerous,
    });
  }

  return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
    last_result_status: asString(
      findFirstKey(latestPayload, ["status", "latest_proof_status", "latest_result_status", "refresh_status", "result_status"]),
      "loaded",
    ),
    last_result_schema: asString(latestPayload.schema, "schema_missing"),
    last_result_evidence_ref: asString(findFirstKey(latestPayload, ["evidence_ref", "latest_evidence_ref", "result_evidence_ref"]), "not_loaded"),
    latest_readback_key_values: compactKeyValues(latestPayload, config.key_fields),
    blocked_reasons: [postFailureReason, "post_timeout_latest_readback_loaded"],
  });
}

async function buildProofRefreshProxy(
  baseUrl: string,
  config: RobotProofRefreshConfig,
): Promise<RobotControlProofRefreshProxyResponse> {
  // refresh 端点只允许固定 POST 路径和固定 body，不能由前端拼接任意控制参数。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return blockedRefreshResponse(baseUrl, normalized.reason, config);
  }

  const timeout_ms = computeRobotProofRefreshTimeoutMs(config);
  const observedAt = Date.now();
  let response: Response;
  try {
    response = await fetch(endpointUrl(normalized.normalized, config.endpoint), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config.request_body),
      signal: AbortSignal.timeout(timeout_ms),
    });
  } catch (error) {
    const reason =
      error instanceof Error && error.name === "TimeoutError"
        ? `fetch_timeout_${timeout_ms}ms`
        : error instanceof Error
          ? error.message.slice(0, 180)
          : "fetch_failed";
    return nav2LatestReadbackAfterPostFailure(baseUrl, normalized.normalized, config, observedAt, reason);
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return {
      schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
      ...PROOF_FLAGS,
      refresh_kind: config.kind,
      proxy_status: "refresh_failed",
      source_base_url: baseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: config.endpoint,
      remote_http_status: response.status,
      status: "blocked",
      last_result_status: "bad_json",
      last_result_schema: "not_loaded",
      last_result_evidence_ref: "not_loaded",
      last_refreshed_at_ms: observedAt,
      latest_readback_key_values: {},
      failure_reason: "response_json_parse_failed",
      blocked_reasons: ["response_json_parse_failed", `refresh_http_status_${response.status}`],
      hard_dangerous_true_fields: [],
      non_motion_evidence_actions_observed: [],
      robot_control_executed: false,
    };
  }

  const payload = asRecord(body);
  if (!payload) {
    return {
      schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
      ...PROOF_FLAGS,
      refresh_kind: config.kind,
      proxy_status: "refresh_failed",
      source_base_url: baseUrl,
      normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
      remote_endpoint: config.endpoint,
      remote_http_status: response.status,
      status: "blocked",
      last_result_status: "not_object",
      last_result_schema: "not_object",
      last_result_evidence_ref: "not_loaded",
      last_refreshed_at_ms: observedAt,
      latest_readback_key_values: {},
      failure_reason: "response_json_not_object",
      blocked_reasons: ["response_json_not_object", `refresh_http_status_${response.status}`],
      hard_dangerous_true_fields: [],
      non_motion_evidence_actions_observed: [],
      robot_control_executed: false,
    };
  }

  const hardDangerous = scanDangerousTrueFields(payload, "", HARD_DANGEROUS_TRUE_FIELDS);
  const nonMotionEvidenceActionsObserved = compactTrueFields(
    scanDangerousTrueFields(payload, "", REFRESH_NON_MOTION_EVIDENCE_ACTION_FIELDS),
  );
  const lastResultStatus = asString(
    findFirstKey(payload, ["status", "latest_proof_status", "latest_result_status", "refresh_status", "result_status"]),
    response.ok ? "loaded" : "blocked",
  );
  const lastResultSchema = asString(payload.schema, "schema_missing");
  const lastResultEvidenceRef = asString(findFirstKey(payload, ["evidence_ref", "latest_evidence_ref", "result_evidence_ref"]), "not_loaded");
  const blockedReasons = [
    ...(response.ok ? [] : [`refresh_http_status_${response.status}`]),
    ...hardDangerous.map((field) => `hard_dangerous_true_field:${field}`),
  ];
  const refreshSuccessful = response.ok && hardDangerous.length === 0;
  const readbackPayload = config.kind === "radar_scan_proof_refresh" ? radarScanProofReadbackPayload(payload) : payload;

  return {
    schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
    ...PROOF_FLAGS,
    refresh_kind: config.kind,
    proxy_status: refreshSuccessful ? "refresh_forwarded" : "refresh_failed",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    remote_endpoint: config.endpoint,
    remote_http_status: response.status,
    status: refreshSuccessful ? "loaded_fail_closed_summary" : "blocked",
    last_result_status: lastResultStatus,
    last_result_schema: lastResultSchema,
    last_result_evidence_ref: lastResultEvidenceRef,
    last_refreshed_at_ms: observedAt,
    latest_readback_key_values: compactKeyValues(readbackPayload, config.key_fields),
    failure_reason:
      hardDangerous.length > 0
        ? `hard_dangerous_true_field:${hardDangerous[0]}`
        : response.ok
          ? ""
          : `refresh_http_status_${response.status}`,
    blocked_reasons: blockedReasons,
    hard_dangerous_true_fields: hardDangerous,
    non_motion_evidence_actions_observed: nonMotionEvidenceActionsObserved,
    robot_control_executed: false,
  };
}

export async function buildRadarScanProofRefreshProxy(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // Radar refresh 只允许固定 no-motion scan proof body，不开放任意参数或动作扩展。
  return buildProofRefreshProxy(baseUrl, RADAR_SCAN_PROOF_REFRESH_CONFIG);
}

export async function buildMapProofRefreshProxy(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // Map refresh 只允许固定 no-motion map proof body，不开放导航、建图或控制参数。
  return buildProofRefreshProxy(baseUrl, MAP_PROOF_REFRESH_CONFIG);
}

export async function buildNav2NoMotionProofRefreshProxy(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // Nav2 refresh 只请求 no-motion planner path proof，不启动 Nav2、不发 goal，也不触碰底盘控制链路。
  return buildProofRefreshProxy(baseUrl, NAV2_NO_MOTION_PROOF_REFRESH_CONFIG);
}

export async function buildLocalizationResetProxy(baseUrl: string): Promise<RobotControlProofRefreshProxyResponse> {
  // 定位 reset 只请求固定 no-motion /initialpose + AMCL proof body，不开放任意 endpoint 或路径生成。
  return buildProofRefreshProxy(baseUrl, LOCALIZATION_RESET_CONFIG);
}

function pickReadback(readbacks: RobotApiEndpointReadback[], id: RobotApiReadEndpointId): RobotApiEndpointReadback | null {
  // 分区摘要按 endpoint id 查找，缺失时明确 unknown，不由 UI 猜测。
  return readbacks.find((item) => item.id === id) ?? null;
}

function proofBoolean(readbacks: RobotApiEndpointReadback[], keys: string[]): boolean | null {
  // proof 是累积证据：旧端点的 false 不能覆盖最新 Nav2 proof 里的 true。
  let falseObserved = false;
  for (const readback of readbacks) {
    for (const key of keys) {
      const value = readback.key_values[key];
      if (value === "true") {
        return true;
      }
      if (value === "false") {
        falseObserved = true;
      }
      if (key === "localization_tf_observed" && typeof value === "string") {
        try {
          const parsed = JSON.parse(value) as JsonRecord;
          if (parsed.map_to_odom === true && parsed.map_to_base_link === true) {
            return true;
          }
          if (parsed.map_to_odom === false || parsed.map_to_base_link === false) {
            falseObserved = true;
          }
        } catch {
          // 非 JSON 字符串按普通摘要处理，避免把异常内容提升为 proof。
        }
      }
    }
  }
  return falseObserved ? false : null;
}

function proofNumber(readbacks: RobotApiEndpointReadback[], keys: string[]): number | null {
  // path_point_count 是累计 proof 指标，旧失败的 0 不能覆盖后续成功路线点数。
  let best: number | null = null;
  for (const readback of readbacks) {
    for (const key of keys) {
      const value = readback.key_values[key];
      if (value !== undefined && Number.isFinite(Number(value))) {
        best = Math.max(best ?? Number(value), Number(value));
      }
    }
  }
  return best;
}

function proofText(readbacks: RobotApiEndpointReadback[], keys: string[]): string | null {
  // readback key_values 已经是压缩短文本；这里取最后一个非空值，避免旧失败摘要盖住新状态。
  let latest: string | null = null;
  for (const readback of readbacks) {
    for (const key of keys) {
      const value = readback.key_values[key];
      if (typeof value === "string" && value.trim()) {
        latest = value.trim();
      }
    }
  }
  return latest;
}

function finitePathCoordinate(value: unknown): number | null {
  // 路线点来自上位机 artifact；只接受有限数字，防止异常字符串进入 SVG 坐标。
  const numberValue = typeof value === "number" ? value : typeof value === "string" && value.trim() ? Number(value) : NaN;
  return Number.isFinite(numberValue) ? numberValue : null;
}

function proofPathPreview(readbacks: InternalRobotApiEndpointReadback[]): Pick<
  RobotApiProofSummary,
  "path_preview_points" | "path_preview_point_count" | "path_preview_source_point_count" | "path_preview_frame_id"
> {
  // 只从 Nav2 proof/status 原始 payload 抽取结构化点；status 里嵌套的 proof_latest 是 live 上位机的常见兜底。
  const candidatePayloads = [
    readbackById(readbacks, "nav2_proof_latest")?.payload ?? null,
    readbackById(readbacks, "nav2_status")?.payload ?? null,
  ].filter((payload): payload is JsonRecord => payload !== null);
  const points: RobotApiPathPreviewPoint[] = [];
  let sourcePayload: JsonRecord | null = null;
  for (const payload of candidatePayloads) {
    const rawPoints = findFirstKey(payload, ["path_preview_points"]);
    if (!Array.isArray(rawPoints)) {
      continue;
    }
    for (const rawPoint of rawPoints.slice(0, ROBOT_CONTROL_PATH_PREVIEW_POINT_LIMIT)) {
      const record = asRecord(rawPoint);
      const x = finitePathCoordinate(record?.x);
      const y = finitePathCoordinate(record?.y);
      if (!record || x === null || y === null) {
        continue;
      }
      const frameId = asString(record.frame_id, asString(findFirstKey(payload, ["path_preview_frame_id"]), ""));
      const sourceIndex = finitePathCoordinate(record.source_index);
      points.push({
        x,
        y,
        frame_id: frameId,
        source_index: sourceIndex === null ? null : Math.trunc(sourceIndex),
      });
    }
    if (points.length > 0) {
      sourcePayload = payload;
      break;
    }
  }
  const countFallback = proofNumber(readbacks, ["path_preview_source_point_count", "latest_path_preview_source_point_count"])
    ?? proofNumber(readbacks, ["path_point_count", "latest_path_point_count"]);
  const frameFallback = proofText(readbacks, ["path_preview_frame_id", "latest_path_preview_frame_id"]) ?? "";
  return {
    path_preview_points: points,
    path_preview_point_count: points.length || proofNumber(readbacks, ["path_preview_point_count", "latest_path_preview_point_count"]) || 0,
    path_preview_source_point_count: countFallback,
    path_preview_frame_id: asString(findFirstKey(sourcePayload, ["path_preview_frame_id"]), points[0]?.frame_id ?? frameFallback),
  };
}

function finiteScanRange(value: unknown): number | null {
  // LaserScan ranges 里可能有 inf/null/字符串；只接受有限正数，避免无效点污染地图视图。
  const numberValue = typeof value === "number" ? value : typeof value === "string" && value.trim() ? Number(value) : NaN;
  if (!Number.isFinite(numberValue) || numberValue < ROBOT_CONTROL_SCAN_PREVIEW_MIN_RANGE_M || numberValue > ROBOT_CONTROL_SCAN_PREVIEW_MAX_RANGE_M) {
    return null;
  }
  return numberValue;
}

function appendStructuredScanPreviewPoints(rawPoints: unknown, payload: JsonRecord | null, points: RobotApiScanPreviewPoint[]): void {
  // 新版上位机若直接给出结构化点，就优先按点读取；字段缺失的点直接跳过。
  if (!Array.isArray(rawPoints)) {
    return;
  }
  for (const rawPoint of rawPoints.slice(0, ROBOT_CONTROL_SCAN_PREVIEW_POINT_LIMIT)) {
    const record = asRecord(rawPoint);
    const range = finiteScanRange(record?.range_m ?? record?.range ?? record?.distance_m);
    const angle = finitePathCoordinate(record?.angle_rad ?? record?.angle);
    if (!record || range === null || angle === null) {
      continue;
    }
    const x = finitePathCoordinate(record.x_m ?? record.x) ?? range * Math.cos(angle);
    const y = finitePathCoordinate(record.y_m ?? record.y) ?? range * Math.sin(angle);
    const sourceIndex = finitePathCoordinate(record.source_index);
    points.push({
      x_m: x,
      y_m: y,
      range_m: range,
      angle_rad: angle,
      frame_id: asString(record.frame_id, asString(findFirstKey(payload, ["scan_preview_frame_id", "frame_id"]), "")),
      source_index: sourceIndex === null ? null : Math.trunc(sourceIndex),
    });
  }
}

function appendRangeScanPreviewPoints(payload: JsonRecord | null, points: RobotApiScanPreviewPoint[]): number | null {
  // 旧 artifact 常见形态是 LaserScan ranges；只抽样生成相对雷达点，不推导机器人全局坐标。
  const rawRanges = findFirstKey(payload, ["ranges"]);
  if (!Array.isArray(rawRanges)) {
    return null;
  }
  const angleMin = finitePathCoordinate(findFirstKey(payload, ["angle_min"])) ?? -Math.PI;
  const angleIncrement = finitePathCoordinate(findFirstKey(payload, ["angle_increment"]))
    ?? (rawRanges.length > 1 ? (2 * Math.PI) / rawRanges.length : 0);
  const frameId = asString(findFirstKey(payload, ["frame_id", "scan_frame_id"]), "");
  const step = Math.max(1, Math.ceil(rawRanges.length / ROBOT_CONTROL_SCAN_PREVIEW_POINT_LIMIT));
  for (let index = 0; index < rawRanges.length && points.length < ROBOT_CONTROL_SCAN_PREVIEW_POINT_LIMIT; index += step) {
    const range = finiteScanRange(rawRanges[index]);
    if (range === null) {
      continue;
    }
    const angle = angleMin + angleIncrement * index;
    points.push({
      x_m: range * Math.cos(angle),
      y_m: range * Math.sin(angle),
      range_m: range,
      angle_rad: angle,
      frame_id: frameId,
      source_index: index,
    });
  }
  return rawRanges.length;
}

function proofScanPreview(readbacks: InternalRobotApiEndpointReadback[]): Pick<
  RobotApiProofSummary,
  "scan_preview_points" | "scan_preview_point_count" | "scan_preview_source_point_count" | "scan_preview_frame_id"
> {
  // 雷达点位只读 latest/status payload；没有点或 ranges 时返回空数组，前端明确展示“点位未读取”。
  const scanProofPayload = readbackById(readbacks, "radar_scan_proof_latest")?.payload ?? null;
  const radarStatusPayload = readbackById(readbacks, "radar_status")?.payload ?? null;
  const candidatePayloads = [scanProofPayload, radarStatusPayload].filter((payload): payload is JsonRecord => payload !== null);
  const points: RobotApiScanPreviewPoint[] = [];
  let sourceCount: number | null = null;
  for (const payload of candidatePayloads) {
    appendStructuredScanPreviewPoints(findFirstKey(payload, ["scan_preview_points", "scan_points"]), payload, points);
    if (points.length === 0) {
      sourceCount = appendRangeScanPreviewPoints(payload, points) ?? sourceCount;
    } else {
      // source count 要优先取当前雷达 payload，避免跨 endpoint 递归时退回到抽样后的点数。
      sourceCount =
        finitePathCoordinate(findFirstKey(payload, ["scan_preview_source_point_count", "scan_point_count"]))
        ?? proofNumber(readbacks, ["scan_preview_source_point_count", "scan_point_count"])
        ?? points.length;
    }
    if (points.length > 0) {
      return {
        scan_preview_points: points.slice(0, ROBOT_CONTROL_SCAN_PREVIEW_POINT_LIMIT),
        scan_preview_point_count: Math.min(points.length, ROBOT_CONTROL_SCAN_PREVIEW_POINT_LIMIT),
        scan_preview_source_point_count: sourceCount,
        scan_preview_frame_id: points[0]?.frame_id ?? "",
      };
    }
  }
  return {
    scan_preview_points: [],
    scan_preview_point_count: 0,
    scan_preview_source_point_count: sourceCount,
    scan_preview_frame_id: "",
  };
}

function proofRobotPose(readbacks: InternalRobotApiEndpointReadback[]): RobotApiMapPose | null {
  // 机器人位置只能来自定位/Nav2 proof 的结构化坐标；只有 observed=true 不足以画真实地图坐标。
  const sourceIds: RobotApiReadEndpointId[] = ["localize_proof_latest", "nav2_proof_latest", "nav2_status", "status"];
  let rawPose: JsonRecord | null = null;
  let sourceId: RobotApiReadEndpointId = "localize_proof_latest";
  for (const id of sourceIds) {
    const payload = readbackById(readbacks, id)?.payload ?? null;
    const candidate = asRecord(findFirstKey(payload, ["amcl_pose", "robot_pose", "map_pose"]));
    if (candidate) {
      rawPose = candidate;
      sourceId = id;
      break;
    }
  }
  if (!rawPose) {
    return null;
  }
  const x = finitePathCoordinate(rawPose.x ?? rawPose.x_m);
  const y = finitePathCoordinate(rawPose.y ?? rawPose.y_m);
  if (x === null || y === null) {
    return null;
  }
  const yaw = finitePathCoordinate(rawPose.yaw ?? rawPose.yaw_rad);
  return {
    x,
    y,
    yaw,
    frame_id: asString(rawPose.frame_id, "map"),
    source: asString(rawPose.source, `${sourceId}.amcl_pose`),
  };
}

function proofFrameTransform(readbacks: InternalRobotApiEndpointReadback[], keys: string[], fallbackParent: string, fallbackChild: string): RobotApiFrameTransform | null {
  // 外参必须来自 proof/status 的显式结构化 transform；没有数值时保持 null，前端不能猜安装偏移。
  const sourceIds: RobotApiReadEndpointId[] = ["localize_proof_latest", "nav2_proof_latest", "nav2_status", "status"];
  let rawTransform: JsonRecord | null = null;
  let sourceId: RobotApiReadEndpointId = "localize_proof_latest";
  for (const id of sourceIds) {
    const payload = readbackById(readbacks, id)?.payload ?? null;
    const candidate = asRecord(findFirstKey(payload, keys));
    if (candidate) {
      rawTransform = candidate;
      sourceId = id;
      break;
    }
  }
  if (!rawTransform) {
    return null;
  }
  const translation = asRecord(rawTransform.translation) ?? rawTransform;
  const rotation = asRecord(rawTransform.rotation) ?? rawTransform;
  const x = finitePathCoordinate(translation.x ?? translation.x_m);
  const y = finitePathCoordinate(translation.y ?? translation.y_m);
  if (x === null || y === null) {
    return null;
  }
  const yaw = finitePathCoordinate(rotation.yaw ?? rotation.yaw_rad) ?? 0;
  return {
    parent_frame_id: asString(rawTransform.parent_frame_id ?? rawTransform.parent, fallbackParent),
    child_frame_id: asString(rawTransform.child_frame_id ?? rawTransform.child, fallbackChild),
    x,
    y,
    yaw,
    source: asString(rawTransform.source, `${sourceId}.frame_transform`),
  };
}

function proofFrameTransforms(readbacks: InternalRobotApiEndpointReadback[]): RobotApiProofSummary["frame_transforms"] {
  return {
    base_link_to_laser_frame: proofFrameTransform(
      readbacks,
      ["base_link_to_laser_frame_transform", "base_to_laser_transform", "laser_frame_transform"],
      "base_link",
      "laser_frame",
    ),
  };
}

function buildProofSummary(readbacks: InternalRobotApiEndpointReadback[]): RobotApiProofSummary {
  // O3 proof 只聚合已读回来的 status/latest 字段；没有字段时保持 null/not_proven。
  const payload = readbacks;
  const rootCauses = stringList(findFirstKey(payload, ["root_causes"]));
  const notProven = stringList(findFirstKey(payload, ["not_proven"]), 12);
  const pathGenerated = proofBoolean(readbacks, ["path_generated", "latest_path_generated"]);
  const pathSucceeded = proofBoolean(readbacks, ["path_generation_succeeded", "latest_path_generation_succeeded"]);
  const proofComplete = pathGenerated === true || pathSucceeded === true;
  const pathPreview = proofPathPreview(readbacks);
  const scanPreview = proofScanPreview(readbacks);
  const robotPose = proofRobotPose(readbacks);
  const frameTransforms = proofFrameTransforms(readbacks);
  return {
    managed_runtime_started: proofBoolean(readbacks, ["managed_runtime_started"]),
    scan_once_observed: proofBoolean(readbacks, ["scan_once_observed", "latest_scan_once_observed"]),
    map_once_observed: proofBoolean(readbacks, ["map_once_observed", "latest_map_once_observed"]),
    amcl_pose_observed: proofBoolean(readbacks, ["amcl_pose_observed", "latest_amcl_pose_observed"]),
    localization_tf_observed: proofBoolean(readbacks, ["localization_tf_observed", "tf_fresh", "latest_tf_fresh"]),
    planner_server_active: proofBoolean(readbacks, ["planner_server_active", "planner_active", "latest_planner_active"]),
    path_generation_requested: proofBoolean(readbacks, ["path_generation_requested", "latest_path_generation_requested"]),
    path_generation_succeeded: pathSucceeded,
    path_generated: pathGenerated,
    path_point_count: proofNumber(readbacks, ["path_point_count", "latest_path_point_count"]),
    ...pathPreview,
    ...scanPreview,
    robot_pose: robotPose,
    frame_transforms: frameTransforms,
    root_causes: rootCauses.length && !proofComplete ? rootCauses : [],
    not_proven: notProven.length && !proofComplete ? notProven : [],
  };
}

function booleanSummaryValue(value: boolean | null): string {
  // readback_summary 面向首屏和调试面板，只暴露短字符串，避免前端重复实现 null/boolean 口径。
  return value === null ? "not_loaded" : String(value);
}

function mapProofText(mapProof: InternalRobotApiEndpointReadback | null, keys: string[]): string | null {
  // 真实上位机会把地图质量塞进 latest_result.proof 多层结构；PC 只读消费已有 proof，不触发刷新或建图。
  const found = findFirstKey(asRecord(mapProof?.payload), keys);
  return found === undefined ? null : compactValueText(found);
}

function mapSummaryFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
  proof: RobotApiProofSummary,
  lidar: RobotControlSummaryResponse["readback_summary"]["lidar"],
): RobotControlSummaryResponse["readback_summary"]["map"] {
  // 地图摘要把 proof/latest 的关键事实提升到 readback_summary，方便普通 UI 直接解释地图是否真的读到。
  const mapProof = readbackById(readbacks, "map_proof_latest");
  const hasScanPreviewPoints = proof.scan_preview_point_count > 0;
  const radarRuntimeStale = lidar.runtime_scan_status === "stale";
  const radarLifecycleStopped = lidar.lifecycle_running === "false" || lidar.lifecycle_state === "stopped";
  const radarOverlayCurrent = hasScanPreviewPoints && !radarRuntimeStale && !radarLifecycleStopped;
  const radarOverlayBlockedReasons = [
    ...(!hasScanPreviewPoints ? ["scan_preview_points_missing"] : []),
    ...(radarRuntimeStale ? ["runtime_scan_stale_for_map_radar_overlay"] : []),
    ...(radarLifecycleStopped ? ["radar_lifecycle_not_running_for_map_radar_overlay"] : []),
    ...(!proof.robot_pose ? ["robot_pose_missing_for_map_radar_overlay"] : []),
  ];
  const radarOverlayStatus = radarOverlayCurrent && proof.robot_pose
    ? "loaded"
    : radarOverlayCurrent
      ? "partial"
      : hasScanPreviewPoints
        ? "not_current"
        : "not_loaded";
  const radarOverlayExplanation = mapRadarOverlayExplanation(
    radarOverlayStatus,
    radarOverlayBlockedReasons,
    proof.scan_preview_source_point_count,
    proof.robot_pose,
  );
  const pathPreviewStatus = proof.path_preview_point_count > 0 ? "path_preview_observed" : "not_observed";
  const robotPoseStatus = proof.robot_pose ? "map_pose_observed" : "not_observed";
  const radarOverlayPointCount = String(radarOverlayCurrent ? proof.scan_preview_point_count : 0);
  const radarOverlaySourcePointCount = proof.scan_preview_source_point_count === null ? "not_loaded" : String(proof.scan_preview_source_point_count);
  const radarOverlayFrameId = proof.scan_preview_frame_id || "not_loaded";
  const pathNextActionPlain = mapPreviewPathNextActionPlain(pathPreviewStatus, robotPoseStatus);
  const mapWysiwyg = mapWysiwygPlainSummary({
    mapObserved: booleanSummaryValue(proof.map_once_observed),
    pathStatus: pathPreviewStatus,
    poseStatus: robotPoseStatus,
    radarStatus: radarOverlayStatus,
    radarHint: radarOverlayExplanation.plain_hint,
    pathNextAction: pathNextActionPlain,
    radarNextAction: radarOverlayExplanation.next_action_plain,
  });
  const radarOverlayWysiwyg = radarOverlayWysiwygPlainSummary({
    radarStatus: radarOverlayStatus,
    pointCount: radarOverlayPointCount,
    sourcePointCount: radarOverlaySourcePointCount,
    frameId: radarOverlayFrameId,
    radarHint: radarOverlayExplanation.plain_hint,
    radarNextAction: radarOverlayExplanation.next_action_plain,
  });
  return {
    status: mapProof?.status ?? "not_loaded",
    map_once_observed: booleanSummaryValue(proof.map_once_observed),
    map_quality_status:
      proofText(readbacks, ["latest_map_quality_status", "map_quality_status"]) ??
      mapProofText(mapProof, ["latest_map_quality_status", "map_quality_status"]) ??
      "not_loaded",
    map_free_cell_count:
      proofText(readbacks, ["latest_map_free_cell_count", "map_free_cell_count", "free_cell_count", "free_cells"]) ??
      mapProofText(mapProof, ["latest_map_free_cell_count", "map_free_cell_count", "free_cell_count", "free_cells"]) ??
      "not_loaded",
    map_usable_for_navigation:
      proofText(readbacks, ["latest_map_usable_for_navigation", "map_usable_for_navigation"]) ??
      mapProofText(mapProof, ["latest_map_usable_for_navigation", "map_usable_for_navigation"]) ??
      "not_loaded",
    map_wysiwyg_status_plain: mapWysiwyg.statusPlain,
    map_wysiwyg_next_action_plain: mapWysiwyg.nextActionPlain,
    path_preview_status: pathPreviewStatus,
    path_preview_point_count: String(proof.path_preview_point_count),
    path_preview_frame_id: proof.path_preview_frame_id || "not_loaded",
    path_preview_next_action_plain: pathNextActionPlain,
    robot_pose_status: robotPoseStatus,
    radar_overlay_status: radarOverlayStatus,
    radar_overlay_plain_hint: radarOverlayExplanation.plain_hint,
    radar_overlay_wysiwyg_status_plain: radarOverlayWysiwyg.statusPlain,
    radar_overlay_wysiwyg_next_action_plain: radarOverlayWysiwyg.nextActionPlain,
    radar_overlay_next_action: radarOverlayExplanation.next_action,
    radar_overlay_next_action_plain: radarOverlayExplanation.next_action_plain,
    radar_overlay_point_count: radarOverlayPointCount,
    radar_overlay_source_point_count: radarOverlaySourcePointCount,
    radar_overlay_frame_id: radarOverlayFrameId,
    radar_overlay_blocked_reasons: radarOverlayBlockedReasons.join(",") || "none",
    radar_overlay_blocked_reason_labels: radarOverlayExplanation.blocked_reason_labels.join(",") || "none",
    radar_overlay_scan_preview_point_count: radarOverlayPointCount,
    radar_overlay_scan_preview_source_point_count: radarOverlaySourcePointCount,
    radar_overlay_scan_preview_frame_id: radarOverlayFrameId,
    radar_overlay_robot_pose_status: robotPoseStatus,
  };
}

function localizationSummaryFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
  proof: RobotApiProofSummary,
): RobotControlSummaryResponse["readback_summary"]["localization"] {
  // 只有结构化 map pose 才能说“地图上看得到小车”；单纯 TF/AMCL observed 不能伪造坐标。
  const localizeProof = readbackById(readbacks, "localize_proof_latest");
  const pose = proof.robot_pose;
  const poseStatus = pose
    ? "map_pose_observed"
    : proof.amcl_pose_observed === true || proof.localization_tf_observed === true
      ? "pose_signal_observed_without_map_coordinates"
      : "not_observed";
  return {
    status: localizeProof?.status ?? "not_loaded",
    amcl_pose_observed: booleanSummaryValue(proof.amcl_pose_observed),
    localization_tf_observed: booleanSummaryValue(proof.localization_tf_observed),
    robot_pose_status: poseStatus,
    robot_pose_frame_id: pose?.frame_id ?? "not_loaded",
    robot_pose_x: pose ? String(pose.x) : "not_loaded",
    robot_pose_y: pose ? String(pose.y) : "not_loaded",
  };
}

function nav2SummaryFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
  proof: RobotApiProofSummary,
): RobotControlSummaryResponse["readback_summary"]["nav2"] {
  // Nav2 摘要优先呈现最近完整路线执行结果；路线规划状态仍由 path_* 和 nav2_status 字段单独解释。
  const nav2Proof = readbackById(readbacks, "nav2_proof_latest");
  const nav2Status = readbackById(readbacks, "nav2_status");
  const statusReadback = readbackById(readbacks, "status");
  const baseStatusReadback = readbackById(readbacks, "base_status");
  const goalExecution = readbackById(readbacks, "nav2_goal_execution_latest");
  const currentBlockerReasons = nav2ProofBlockerReasons(nav2Proof?.payload);
  const goalPayload = goalExecution?.payload ?? null;
  const goalResultPayload = asRecord(goalPayload?.latest_result) ?? goalPayload;
  const baseCommandSummary = asRecord(goalResultPayload?.base_command_summary);
  const baseFeedbackSummary = asRecord(goalResultPayload?.base_feedback_summary);
  const latestNonzeroPair = asRecord(baseFeedbackSummary?.latest_nonzero_pair);
  const latestPair = asRecord(baseFeedbackSummary?.latest_pair);
  const goalExecutionStatus = summaryValueText(goalResultPayload, ["status"], goalExecution?.status ?? "not_loaded");
  const nav2StatusPayload = nav2Status?.payload ?? null;
  const lifecycleManager = asRecord(nav2StatusPayload?.lifecycle_manager);
  const statusBlockerReasons = nav2ProofBlockerReasons(nav2StatusPayload);
  const goalExecutionProven = nav2GoalExecutionProvenText(goalResultPayload);
  const goalExecutionResultStatus = summaryValueText(goalResultPayload, ["result_status"]);
  const wheelFeedbackProven = summaryValueText(baseFeedbackSummary, ["wheel_feedback_lr_nonzero_proven"]);
  const lastBaseMode = summaryValueText(goalResultPayload, ["base_command_mode"]);
  const configuredNextBaseMode = statusReadback?.key_values.nav2_base_command_mode
    ?? baseStatusReadback?.key_values.nav2_base_command_mode
    ?? "not_loaded";
  const baseCommandNonzeroObserved = summaryValueText(baseCommandSummary, ["nonzero_command_observed"]);
  const baseCommandNonzeroCount = summaryValueText(baseCommandSummary, ["nonzero_command_count"]);
  const parsedBaseCommandNonzeroCount = Number(baseCommandNonzeroCount);
  const baseCommandModeCanFallback = ["ros", "pwm", "speed"].includes(lastBaseMode)
    && Number.isFinite(parsedBaseCommandNonzeroCount)
    && parsedBaseCommandNonzeroCount > 0;
  const baseCommandLatestNonzeroMode = summaryValueText(baseCommandSummary, ["latest_nonzero_command_mode"]);
  const baseCommandModeCounts = summaryValueText(baseCommandSummary, ["command_mode_counts"], "{}");
  const effectiveBaseCommandLatestNonzeroMode = baseCommandLatestNonzeroMode === "not_loaded" && baseCommandModeCanFallback
    ? lastBaseMode
    : baseCommandLatestNonzeroMode;
  const effectiveBaseCommandModeCounts = baseCommandModeCounts === "{}" && baseCommandModeCanFallback
    ? JSON.stringify({ [lastBaseMode]: parsedBaseCommandNonzeroCount })
    : baseCommandModeCounts;
  const goalSucceeded = goalExecutionStatus === "goal_succeeded" || goalExecutionResultStatus === "succeeded";
  const nextBaseMode = nav2NextExecutionBaseCommandMode({
    configuredNextBaseMode,
    lastBaseMode,
    goalSucceeded,
    wheelFeedbackProven,
    baseCommandNonzeroObserved,
    parsedBaseCommandNonzeroCount,
  });
  const modeRerunStatus = !["", "not_loaded"].includes(lastBaseMode)
    && !["", "not_loaded"].includes(nextBaseMode)
    && lastBaseMode !== nextBaseMode
    ? `pending_${nextBaseMode}_rerun_after_${lastBaseMode}`
    : "not_required";
  const summaryStatus = goalExecutionProven === "true" && goalExecutionStatus !== "not_loaded"
    ? goalExecutionStatus
    : goalSucceeded && wheelFeedbackProven === "false"
      ? "goal_succeeded_wheel_feedback_not_proven"
    : nav2Proof?.status ?? "not_loaded";
  const latestMapConsumed = proofText(readbacks, ["latest_map_consumed", "map_consumed"]) ?? "not_loaded";
  const latestPathGenerationAttempted = proofText(readbacks, ["latest_path_generation_attempted", "path_generation_attempted"]) ?? "not_loaded";
  const latestPathGenerationServiceAvailable = proofText(readbacks, ["latest_path_generation_service_available", "path_generation_service_available"]) ?? "not_loaded";
  const latestPathGenerationServiceName = proofText(readbacks, ["latest_path_generation_service_name", "path_generation_service_name"]) ?? "not_loaded";
  const syntheticBlockerReasons = [
    latestMapConsumed === "false" ? "nav2_map_not_consumed" : "",
    latestPathGenerationServiceAvailable === "false" ? "path_generation_service_unavailable" : "",
    latestPathGenerationAttempted === "false" && proof.path_generation_requested === true ? "path_generation_not_attempted" : "",
  ].filter(Boolean);
  const effectiveCurrentBlockerReasons = [...new Set([...currentBlockerReasons, ...statusBlockerReasons, ...syntheticBlockerReasons])];
  const effectiveCurrentBlockerLabels = nav2ProofBlockerLabels(effectiveCurrentBlockerReasons);
  const latestLeft = summaryValueText(latestNonzeroPair ?? latestPair, ["left_speed"]);
  const latestRight = summaryValueText(latestNonzeroPair ?? latestPair, ["right_speed"]);
  const imuDeltaObserved = summaryValueText(baseFeedbackSummary, ["imu_attitude_delta_observed"]);
  const readbackPlain = nav2ReadbackPlainSummary({
    summaryStatus,
    goalSucceeded,
    goalExecutionProven,
    wheelFeedbackProven,
    latestLeft,
    latestRight,
    baseCommandNonzeroObserved,
    baseCommandNonzeroCount,
    imuDeltaObserved,
    nextBaseMode,
    proof,
    effectiveCurrentBlockerLabels,
  });
  const routeExecutionPlain = nav2RouteExecutionPlainSummary({
    goalSucceeded,
    goalExecutionProven,
    wheelFeedbackProven,
    latestLeft,
    latestRight,
    nextBaseMode,
    proof,
    effectiveCurrentBlockerLabels,
  });
  const wheelRawPlain = nav2WheelRawLrPlainSummary({
    goalSucceeded,
    wheelFeedbackProven,
    latestLeft,
    latestRight,
    baseCommandNonzeroObserved,
    baseCommandNonzeroCount,
    imuDeltaObserved,
    nextBaseMode,
  });
  return {
    status: summaryStatus,
    nav2_status: nav2Status?.status ?? "not_loaded",
    nav2_stack_running: summaryValueText(nav2StatusPayload, ["lifecycle_running"], summaryValueText(lifecycleManager, ["running"])),
    nav2_stack_lifecycle_state: summaryValueText(nav2StatusPayload, ["lifecycle_state"], summaryValueText(lifecycleManager, ["state"])),
    current_blocker_reasons: effectiveCurrentBlockerReasons.join(",") || "none",
    current_blocker_labels: effectiveCurrentBlockerLabels.join("、") || "not_loaded",
    planner_server_active: proofText(readbacks, ["planner_server_active", "planner_active", "latest_planner_active"]) ?? booleanSummaryValue(proof.planner_server_active),
    controller_server_active: proofText(readbacks, ["controller_server_active", "latest_controller_active"]) ?? "not_loaded",
    controller_server_requested: proofText(readbacks, ["controller_server_requested", "latest_controller_requested"]) ?? "not_loaded",
    map_consumed: latestMapConsumed,
    path_generation_attempted: latestPathGenerationAttempted,
    path_generation_service_available: latestPathGenerationServiceAvailable,
    path_generation_service_name: latestPathGenerationServiceName,
    path_generated: booleanSummaryValue(proof.path_generated),
    path_generation_succeeded: booleanSummaryValue(proof.path_generation_succeeded),
    path_point_count: proof.path_point_count === null ? "not_loaded" : String(proof.path_point_count),
    path_preview_point_count: String(proof.path_preview_point_count),
    path_preview_frame_id: proof.path_preview_frame_id || "not_loaded",
    execution_status_plain: readbackPlain.execution_status_plain,
    next_action_plain: readbackPlain.next_action_plain,
    route_execution_readiness_plain: routeExecutionPlain.readinessPlain,
    route_execution_precheck_plain: routeExecutionPlain.precheckPlain,
    goal_execution_wheel_raw_lr_status_plain: wheelRawPlain.statusPlain,
    goal_execution_wheel_raw_lr_next_action_plain: wheelRawPlain.nextActionPlain,
    goal_execution_status: goalExecutionStatus,
    goal_execution_proven: goalExecutionProven,
    goal_execution_hil_pass: summaryValueText(goalResultPayload, ["hil_pass"]),
    goal_execution_result_status: goalExecutionResultStatus,
    goal_execution_evidence_ref: summaryValueText(goalResultPayload, ["evidence_ref"]),
    goal_execution_robot_control_executed: summaryValueText(goalResultPayload, ["robot_control_executed"]),
    goal_execution_feedback_sample_count: summaryValueText(goalResultPayload, ["feedback_sample_count", "nav2_feedback_sample_count"]),
    goal_execution_base_command_mode: lastBaseMode,
    next_execution_base_command_mode: nextBaseMode,
    goal_execution_mode_rerun_status: modeRerunStatus,
    goal_execution_base_command_nonzero_observed: baseCommandNonzeroObserved,
    goal_execution_base_command_nonzero_count: baseCommandNonzeroCount,
    goal_execution_base_command_latest_nonzero_mode: effectiveBaseCommandLatestNonzeroMode,
    goal_execution_base_command_mode_counts: effectiveBaseCommandModeCounts,
    goal_execution_base_feedback_sample_count: summaryValueText(baseFeedbackSummary, ["sample_count"]),
    goal_execution_base_feedback_nonzero_sample_count: summaryValueText(baseFeedbackSummary, ["nonzero_sample_count"]),
    goal_execution_base_feedback_lr_nonzero_proven: summaryValueText(baseFeedbackSummary, ["wheel_feedback_lr_nonzero_proven"]),
    goal_execution_base_feedback_imu_attitude_delta_observed: summaryValueText(baseFeedbackSummary, ["imu_attitude_delta_observed"]),
    goal_execution_base_feedback_imu_roll_delta: summaryValueText(asRecord(baseFeedbackSummary?.imu_attitude_delta_summary), ["max_abs_roll_delta"]),
    goal_execution_base_feedback_imu_pitch_delta: summaryValueText(asRecord(baseFeedbackSummary?.imu_attitude_delta_summary), ["max_abs_pitch_delta"]),
    goal_execution_base_feedback_latest_left_speed: latestLeft,
    goal_execution_base_feedback_latest_right_speed: latestRight,
    goal_execution_base_feedback_latest_raw_left: latestLeft,
    goal_execution_base_feedback_latest_raw_right: latestRight,
    goal_execution_sends_base_motion_commands: summaryValueText(goalResultPayload, ["sends_base_motion_commands"]),
    goal_execution_uses_base_uart: summaryValueText(goalResultPayload, ["uses_base_uart"]),
    goal_execution_goal_frame_id: summaryValueText(goalResultPayload, ["goal_frame_id", "frame_id"]),
    goal_execution_goal_x: summaryValueText(goalResultPayload, ["goal_x", "x"]),
    goal_execution_goal_y: summaryValueText(goalResultPayload, ["goal_y", "y"]),
    goal_execution_generated_at_ms: summaryValueText(goalResultPayload, ["generated_at_ms", "nav2_generated_at_ms"]),
    goal_execution_response_generated_at_ms: summaryValueText(goalPayload, ["response_generated_at_ms", "generated_at_ms"]),
  };
}

function nav2RouteExecutionPlainSummary(args: {
  goalSucceeded: boolean;
  goalExecutionProven: string;
  wheelFeedbackProven: string;
  latestLeft: string;
  latestRight: string;
  nextBaseMode: string;
  proof: RobotApiProofSummary;
  effectiveCurrentBlockerLabels: string[];
}): { readinessPlain: string; precheckPlain: string } {
  // 这两个字段只回答普通操作员最关心的两件事：能不能按图执行、发车前还要勾什么。
  const pathReady = args.proof.path_generated === true
    || args.proof.path_generation_succeeded === true
    || (args.proof.path_point_count ?? 0) > 0
    || args.proof.path_preview_point_count > 0;
  const modeText = ["", "not_loaded"].includes(args.nextBaseMode)
    ? "当前模式"
    : `${args.nextBaseMode.toUpperCase()} 模式`;
  const minimalPrecheck = `只需勾选行程前安全确认；相机、雷达和 operator report 不作为额外发车前置；执行会用 ${modeText}跑图上路线。`;
  if (args.goalExecutionProven === "true" || args.wheelFeedbackProven === "true") {
    return {
      readinessPlain: "完整路线执行已证明；同窗口 wheel raw L/R 已非零。",
      precheckPlain: "下一步是送达确认；送达确认不会发车。",
    };
  }
  if (args.goalSucceeded && args.wheelFeedbackProven === "false") {
    return {
      readinessPlain: `图上路线可重跑复验；上次路线 action 成功，但同窗口 wheel raw L/R=${args.latestLeft}/${args.latestRight} 未非零。`,
      precheckPlain: minimalPrecheck,
    };
  }
  if (pathReady) {
    return {
      readinessPlain: "图上路线可执行；完整路线执行和同窗口 wheel raw L/R 还未证明。",
      precheckPlain: minimalPrecheck,
    };
  }
  const blockerText = args.effectiveCurrentBlockerLabels.length > 0 && args.effectiveCurrentBlockerLabels.join("、") !== "not_loaded"
    ? `当前缺口：${args.effectiveCurrentBlockerLabels.join("、")}。`
    : "当前缺口：图上路线还未准备完成。";
  return {
    readinessPlain: `图上路线还不可执行；${blockerText}`,
    precheckPlain: "路线准备完成后，执行只需勾选行程前安全确认。",
  };
}

function nav2ReadbackPlainSummary(args: {
  summaryStatus: string;
  goalSucceeded: boolean;
  goalExecutionProven: string;
  wheelFeedbackProven: string;
  latestLeft: string;
  latestRight: string;
  baseCommandNonzeroObserved: string;
  baseCommandNonzeroCount: string;
  imuDeltaObserved: string;
  nextBaseMode: string;
  proof: RobotApiProofSummary;
  effectiveCurrentBlockerLabels: string[];
}): { execution_status_plain: string; next_action_plain: string } {
  // Nav2 readback 是脚本最常读的区块；这里给普通白话，避免外部再拼 wheel/raw/mode token。
  const pathReady = args.proof.path_generated === true
    || args.proof.path_generation_succeeded === true
    || (args.proof.path_point_count ?? 0) > 0
    || args.proof.path_preview_point_count > 0;
  const nextMode = ["", "not_loaded"].includes(args.nextBaseMode)
    ? "当前模式"
    : nav2GoalNextActionPlainText(args.nextBaseMode.toUpperCase());
  const nonzeroCommandCount = Number(args.baseCommandNonzeroCount);
  const hasMotionCommand = args.baseCommandNonzeroObserved === "true"
    || (Number.isFinite(nonzeroCommandCount) && nonzeroCommandCount > 0);
  const motionMaterial = args.imuDeltaObserved === "true"
    ? "已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或控制服务。"
    : hasMotionCommand
      ? "已看到非零底盘命令，下一步重点复验执行窗口轮速 L/R。"
      : "还没有读到足够的底盘运动材料。";
  if (args.goalExecutionProven === "true" || args.wheelFeedbackProven === "true") {
    return {
      execution_status_plain: "本轮路线执行和执行窗口轮速 L/R 已证明。",
      next_action_plain: "继续送达确认；送达确认不会发车。",
    };
  }
  if (args.goalSucceeded && args.wheelFeedbackProven === "false") {
    return {
      execution_status_plain: `上次路线结果成功，但执行窗口轮速 L/R=${args.latestLeft}/${args.latestRight} 未非零；${motionMaterial}`,
      next_action_plain: `勾选行程前安全确认后用 ${nextMode}重跑图上路线，并在同窗口确认轮速 L/R 非零。`,
    };
  }
  if (pathReady) {
    return {
      execution_status_plain: "图上路线已准备，但本轮完整执行和轮速 L/R 还未证明。",
      next_action_plain: "勾选行程前安全确认后执行图上路线，并在同窗口确认轮速 L/R 非零。",
    };
  }
  const blockers = args.effectiveCurrentBlockerLabels.length > 0 && args.effectiveCurrentBlockerLabels.join("、") !== "not_loaded"
    ? `当前根因：${args.effectiveCurrentBlockerLabels.join("、")}。`
    : "";
  return {
    execution_status_plain: `图上路线还未准备完成。${blockers}`,
    next_action_plain: "先准备图上路线并刷新地图画面，再勾选安全确认执行。",
  };
}

function nav2WheelRawLrPlainSummary(args: {
  goalSucceeded: boolean;
  wheelFeedbackProven: string;
  latestLeft: string;
  latestRight: string;
  baseCommandNonzeroObserved: string;
  baseCommandNonzeroCount: string;
  imuDeltaObserved: string;
  nextBaseMode: string;
}): { statusPlain: string; nextActionPlain: string } {
  // wheel raw L/R 是完整路线执行的硬证据；单独总结，避免脚本从长句里解析。
  if (args.wheelFeedbackProven === "true") {
    return {
      statusPlain: `执行窗口 wheel raw L/R 已非零：L=${args.latestLeft}，R=${args.latestRight}。`,
      nextActionPlain: "继续送达确认；送达确认不会发车。",
    };
  }
  if (args.goalSucceeded && args.wheelFeedbackProven === "false") {
    const commandText = args.baseCommandNonzeroObserved === "true"
      ? `已看到 ${args.baseCommandNonzeroCount} 次非零底盘命令`
      : "未看到非零底盘命令";
    const imuText = args.imuDeltaObserved === "true" ? "，IMU 姿态有变化" : "";
    const modeText = args.nextBaseMode && !["not_loaded", ""].includes(args.nextBaseMode)
      ? `${args.nextBaseMode.toUpperCase()} 模式`
      : "当前配置模式";
    return {
      statusPlain: `上次路线 action 成功，但执行窗口 wheel raw L/R=${args.latestLeft}/${args.latestRight} 未非零；${commandText}${imuText}。`,
      nextActionPlain: `勾选行程前安全确认后用 ${modeText}重跑图上路线，并在同窗口确认 wheel raw L/R 非零。`,
    };
  }
  return {
    statusPlain: "本轮完整路线执行的 wheel raw L/R 还未证明。",
    nextActionPlain: "先准备图上路线并执行，再在同窗口确认 wheel raw L/R 非零。",
  };
}

function nav2NextExecutionBaseCommandMode(args: {
  configuredNextBaseMode: string;
  lastBaseMode: string;
  goalSucceeded: boolean;
  wheelFeedbackProven: string;
  baseCommandNonzeroObserved: string;
  parsedBaseCommandNonzeroCount: number;
}): string {
  // Vendor index 要求 T=13 未经硬件闭环时可回退 T=1；避免 ROS/T=13 零轮速后无限继续 ROS 重跑。
  const configured = args.configuredNextBaseMode || "not_loaded";
  const last = args.lastBaseMode || "not_loaded";
  const nonzeroCommandObserved = args.baseCommandNonzeroObserved === "true"
    || (Number.isFinite(args.parsedBaseCommandNonzeroCount) && args.parsedBaseCommandNonzeroCount > 0);
  const wheelZeroAfterCommand = args.goalSucceeded
    && args.wheelFeedbackProven === "false"
    && nonzeroCommandObserved;
  if (wheelZeroAfterCommand && last === "ros") {
    return "speed";
  }
  if (wheelZeroAfterCommand && last === "pwm") {
    return "ros";
  }
  return configured;
}

function nav2GoalExecutionProvenText(goalResultPayload: JsonRecord | null): string {
  // 完整 Nav2 路线必须由同窗口 wheel raw L/R 非零收口；IMU/hil 字段只保留为诊断材料。
  const hilPass = summaryValueText(goalResultPayload, ["hil_pass"]);
  const explicit = summaryValueText(goalResultPayload, ["nav2_goal_execution_proven"]);
  const baseFeedbackSummary = asRecord(goalResultPayload?.base_feedback_summary);
  const wheelFeedback = summaryValueText(baseFeedbackSummary, ["wheel_feedback_lr_nonzero_proven"]);
  if (explicit === "true" && wheelFeedback === "true") {
    return "true";
  }
  if (explicit === "false" && wheelFeedback !== "true") {
    return explicit;
  }

  const robotControlExecuted = summaryValueText(goalResultPayload, ["robot_control_executed"]);
  const sendsMotionCommands = summaryValueText(goalResultPayload, ["sends_motion_commands"]);
  const sendsBaseMotionCommands = summaryValueText(goalResultPayload, ["sends_base_motion_commands"]);
  const usesBaseUart = summaryValueText(goalResultPayload, ["uses_base_uart"]);
  const status = summaryValueText(goalResultPayload, ["status"]);
  const resultStatus = summaryValueText(goalResultPayload, ["result_status"]);
  const feedbackCountText = summaryValueText(goalResultPayload, ["feedback_sample_count", "nav2_feedback_sample_count"]);
  const feedbackCount = Math.max(
    Number(feedbackCountText),
    Number(summaryValueText(baseFeedbackSummary, ["sample_count"])),
  );
  const succeeded = status === "goal_succeeded" || resultStatus === "succeeded";
  const motionCommandAllowed = sendsMotionCommands === "true"
    || sendsBaseMotionCommands === "true"
    || (sendsMotionCommands !== "false" && sendsBaseMotionCommands !== "false" && hilPass !== "false");
  if (
    robotControlExecuted === "true"
    && motionCommandAllowed
    && usesBaseUart !== "false"
    && succeeded
    && Number.isFinite(feedbackCount)
    && feedbackCount > 0
    && wheelFeedback === "true"
  ) {
    return "true";
  }
  if (
    hilPass === "false"
    || explicit === "false"
    || wheelFeedback === "false"
    || robotControlExecuted === "false"
    || sendsMotionCommands === "false"
    || sendsBaseMotionCommands === "false"
    || usesBaseUart === "false"
  ) {
    return "false";
  }
  return "not_loaded";
}

function freeRoamSummaryFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
  freeRoamRuntimeGates: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_gates"] | null = null,
  freeRoamRuntime: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_runtime"] | null = null,
): RobotControlSummaryResponse["readback_summary"]["free_roam"] {
  // free-roam 摘要把自动扫图 artifact 的最近状态提升给首屏；它只解释状态，不代表 PC 可以直接发车。
  const readback = readbackById(readbacks, "free_roam_autonomy_latest");
  const payload = readback?.payload ?? null;
  const latest = freeRoamRuntimeLatestFromReadbacks(readbacks);
  const decision = asRecord(latest?.decision);
  const rawGates = Array.isArray(decision?.gates) ? decision.gates : [];
  const payloadGateCount = summaryValueText(payload, ["gate_count"]);
  const gateCount = rawGates.length > 0 ? String(rawGates.length) : payloadGateCount && payloadGateCount !== "not_loaded" ? payloadGateCount : "0";
  const stopGates = (freeRoamRuntimeGates ?? []).filter((gate) => gate.id === "stop_available");
  const stopFallbackReady = stopGates.length === 0 || stopGates.every((gate) => gate.state === "ready");
  const startReady = Boolean(freeRoamRuntime?.status === "loaded" && stopFallbackReady);
  const motionReady = Boolean(startReady && freeRoamRuntime?.cmd_vel_publish_enabled === true);
  const mappingRequiredIds = ["camera_first_frame", "lidar_fresh", "mapping_active", "fresh_map_preview"];
  const mappingGateById = new Map((freeRoamRuntimeGates ?? [])
    .filter((gate) => gate.scope === "mapping_acceptance")
    .map((gate) => [gate.id, gate]));
  const mappingMissing = mappingRequiredIds.filter((id) => mappingGateById.get(id)?.state !== "ready");
  const mappingReady = startReady && mappingMissing.length === 0;
  const nextActionStatus = mappingReady ? "ready" : startReady ? "start_ready" : "locked";
  const externalStopRequested = freeRoamRuntime?.state === "stopping" && /现场请求停止|external_stop/i.test(freeRoamRuntime.reason);
  const derivedStatus = mappingReady
    ? "mapping_ready"
    : motionReady
      ? "motion_ready"
      : startReady
        ? "start_ready"
        : readback?.status ?? "not_loaded";
  const motionReadinessPlain = freeRoamMotionReadinessPlain(startReady, motionReady, externalStopRequested);
  const mappingReadinessPlain = freeRoamMappingReadinessPlain(startReady, mappingReady, mappingMissing);
  return {
    status: derivedStatus,
    runtime_status: asString(payload?.runtime_status, latest ? "loaded" : "not_loaded"),
    decision_state: asString(decision?.state, asString(payload?.decision_state, "not_loaded")),
    decision_reason: asString(decision?.reason, asString(payload?.decision_reason, "not_loaded")),
    stop_required: decision ? booleanSummaryValue(decision.stop_required === true) : summaryValueText(payload, ["stop_required"]) ?? "not_loaded",
    artifact_only: latest ? booleanSummaryValue(latest.artifact_only !== false) : summaryValueText(payload, ["artifact_only"]) ?? "not_loaded",
    cmd_vel_publish_enabled: latest ? booleanSummaryValue(latest.cmd_vel_publish_enabled === true) : summaryValueText(payload, ["cmd_vel_publish_enabled"]) ?? "not_loaded",
    start_ready: booleanSummaryValue(startReady),
    motion_start_ready: booleanSummaryValue(startReady),
    motion_ready: booleanSummaryValue(motionReady),
    mapping_ready: booleanSummaryValue(mappingReady),
    mapping_missing: mappingMissing.length ? mappingMissing.join(",") : "none",
    next_action_plain: freeRoamAutonomyNextAction(nextActionStatus, mappingReady, mappingMissing, freeRoamRuntime),
    motion_readiness_plain: motionReadinessPlain,
    mapping_readiness_plain: mappingReadinessPlain,
    motion_next_action_plain: freeRoamMotionNextAction(startReady, motionReady, externalStopRequested),
    mapping_next_action_plain: freeRoamMappingNextAction(startReady, mappingReady, mappingMissing),
    runtime_artifact_proven: summaryValueText(payload, ["free_roam_runtime_artifact_proven"]) ?? "not_loaded",
    state_machine_observed: summaryValueText(payload, ["free_roam_state_machine_observed"]) ?? "not_loaded",
    ros2_runtime_proven: summaryValueText(payload, ["ros2_runtime_proven"]) ?? "not_loaded",
    gate_count: gateCount,
  };
}

function failClosed(reason: string, sourceBaseUrl: string): RobotControlSummaryResponse {
  // URL 被拒或未配置时也返回完整合同，前端可以稳定展示七区块和恢复路径。
  const observedAt = Date.now();
  return {
    schema: ROBOT_CONTROL_SCHEMA,
    console_status: "blocked",
    source_base_url: sourceBaseUrl,
    normalized_base_url: "not_loaded",
    proxy_policy: {
      vue_direct_robot_api_access: false,
      node_proxy_only: true,
      allowed_methods: ["GET", "POST"],
      allowed_endpoint_class: "status_latest_readback_plus_fixed_control_and_report_proxies",
      unsafe_urls_rejected: true,
    },
    observed_at_ms: observedAt,
    read_endpoints: [],
    o3_proof_summary: {
      managed_runtime_started: null,
      scan_once_observed: null,
      map_once_observed: null,
      amcl_pose_observed: null,
      localization_tf_observed: null,
      planner_server_active: null,
      path_generation_requested: null,
      path_generation_succeeded: null,
      path_generated: null,
      path_point_count: null,
      path_preview_points: [],
      path_preview_point_count: 0,
      path_preview_source_point_count: null,
      path_preview_frame_id: "",
      scan_preview_points: [],
      scan_preview_point_count: 0,
      scan_preview_source_point_count: null,
      scan_preview_frame_id: "",
      robot_pose: null,
      frame_transforms: {
        base_link_to_laser_frame: null,
      },
      root_causes: [reason],
      not_proven: ["robot_api_not_loaded", "path_generated", "delivery_success"],
    },
    robot_api_connection: {
      status: sourceBaseUrl.trim() ? "blocked" : "not_configured",
      loaded_count: 0,
      blocked_count: 0,
      failed_count: 0,
      schema_mismatch_count: 0,
      dangerous_true_fields: [],
      blocked_reasons: [reason],
      last_refresh_ms: observedAt,
    },
    current_fact_plain: sourceBaseUrl.trim()
      ? "当前事实未读到；上位机这次没有回应，先检查小车电源、网络和 Robot API 服务。"
      : "当前事实未读到；先填写或确认小车地址。",
    readback_summary: {
      camera: {
        status: "not_loaded",
        devices_status: "not_loaded",
        preview_status: "idle_not_started",
        preview_plain_hint: "页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。",
        preview_next_action: "auto_join_shared_mjpeg_preview",
        preview_next_action_plain: "打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。",
        preview_visible_status: "not_visible_idle",
        preview_visible_plain: "当前没有实时画面；页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。",
        camera_wysiwyg_status_plain: "画面未可见：页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。",
        camera_wysiwyg_next_action_plain: "打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。",
        shared_preview_client_count: "0",
        viewer_count: "0",
        shared_preview_upstream_active: "false",
        upstream_connected: "false",
        shared_preview_content_type_loaded: "false",
        shared_preview_cached_frame_loaded: "false",
        has_recent_frame: "false",
        shared_preview_cached_frame_age_ms: "none",
        shared_preview_shared_capture: "true",
        shared_preview_exclusive_camera_claim: "false",
        shared_preview_contract: "single_shared_capture_for_multiple_clients",
        shared_preview_last_failure_reason: "none",
        shared_preview_last_remote_http_status: "none",
        shared_preview_last_failure_at_ms: "none",
        video_source: "not_loaded",
        video_source_mode: "not_loaded",
        selected_path: "not_loaded",
        selected_name: "not_loaded",
        selected_is_uvc_or_usb: "not_loaded",
        selected_formats_summary: "not_loaded",
        selected_role: "not_loaded",
        selected_sibling_video_nodes_summary: "none",
        selected_sibling_video_node_count: "not_loaded",
        source_readiness: "not_loaded",
        source_failure_reason: "not_loaded",
        source_diagnosis_status: "not_loaded",
        source_diagnosis_plain_hint: "not_loaded",
        source_diagnosis_next_action: "not_loaded",
        source_diagnosis_next_action_plain: "",
        source_diagnosis_not_exclusive: "not_loaded",
        source_usage_status: "not_loaded",
        source_usage_owner_count: "not_loaded",
        source_usage_summary: "not_loaded",
        active_peer_count: "not_loaded",
        last_offer_error: "none",
        last_offer_failure_reason: "none",
        last_offer_format_attempts_summary: "none",
        first_frame_probe_status: "not_loaded",
        first_frame_probe_failure_reason: "none",
        first_frame_probe_open_ok: "not_loaded",
        first_frame_probe_read_ok: "not_loaded",
        first_frame_probe_visible_content_proven: "not_loaded",
        first_frame_probe_backend_smoke_status: "not_requested",
        first_frame_probe_backend_frame_observed: "not_loaded",
        first_frame_probe_backend_attempts: "0",
        first_frame_probe_fallback_attempts_summary: "none",
        first_frame_probe_checked_at_ms: "not_loaded",
      },
      lidar: {
        status: "not_loaded",
        latest_scan_proof_status: "not_loaded",
        latest_raw_packet_proof_status: "not_loaded",
        latest_scan_proof_result_status: "not_loaded",
        raw_packet_once_observed: "not_loaded",
        continuous_scan_status: "not_loaded",
        lifecycle_running: "not_loaded",
        lifecycle_state: "not_loaded",
        continuous_window_observed: "not_loaded",
        continuity_window_status: "not_loaded",
        latest_scan_proof_fresh: "not_loaded",
        runtime_scan_status: "not_loaded",
        runtime_lidar_min_distance_m: "not_loaded",
        runtime_lidar_age_s: "not_loaded",
        runtime_scan_source: "not_loaded",
        scan_preview_point_count: "0",
        scan_preview_source_point_count: "not_loaded",
        scan_preview_frame_id: "not_loaded",
        radar_start_configured: "not_loaded",
      },
      base: {
        status: "not_loaded",
        latest_feedback_status: "not_loaded",
        current_feedback_read_status: "not_loaded",
        current_feedback_failure_reason: "not_loaded",
        feedback_ack_status: "not_loaded",
        latest_t1001_observed_count: "not_loaded",
        wheel_feedback_lr_nonzero_proven: "not_loaded",
        wheel_feedback_nonzero_observed: "not_loaded",
        wheel_feedback_latest_left_speed: "not_loaded",
        wheel_feedback_latest_right_speed: "not_loaded",
        wheel_left_speed: "not_loaded",
        wheel_right_speed: "not_loaded",
        wheel_raw_left: "not_loaded",
        wheel_raw_right: "not_loaded",
        wheel_feedback_latest_nonzero_left_speed: "not_loaded",
        wheel_feedback_latest_nonzero_right_speed: "not_loaded",
        feedback_voltage_v: "not_loaded",
        feedback_link_status: "not_observed",
      },
      map: {
        status: "not_loaded",
        map_once_observed: "not_loaded",
        map_quality_status: "not_loaded",
        map_free_cell_count: "not_loaded",
        map_usable_for_navigation: "not_loaded",
        map_wysiwyg_status_plain: "地图画面未读到；不能把旧图或空白图当作当前所见。",
        map_wysiwyg_next_action_plain: "先刷新地图画面。",
        path_preview_status: "not_observed",
        path_preview_point_count: "0",
        path_preview_frame_id: "not_loaded",
        path_preview_next_action_plain: "先准备图上路线，再刷新地图画面。",
        robot_pose_status: "not_loaded",
        radar_overlay_status: "not_loaded",
        radar_overlay_plain_hint: "地图雷达层未加载。",
        radar_overlay_wysiwyg_status_plain: "雷达 marker 未加载：当前显示 0 个点；来源点 0 个。地图雷达层未加载。",
        radar_overlay_wysiwyg_next_action_plain: "确认小车地址可访问后刷新地图画面。",
        radar_overlay_next_action: "connect_robot_and_refresh_map_preview",
        radar_overlay_next_action_plain: "确认小车地址可访问后刷新地图画面。",
        radar_overlay_point_count: "0",
        radar_overlay_source_point_count: "0",
        radar_overlay_frame_id: "not_loaded",
        radar_overlay_blocked_reasons: "not_loaded",
        radar_overlay_blocked_reason_labels: "not_loaded",
        radar_overlay_scan_preview_point_count: "0",
        radar_overlay_scan_preview_source_point_count: "0",
        radar_overlay_scan_preview_frame_id: "not_loaded",
        radar_overlay_robot_pose_status: "not_loaded",
      },
      localization: {
        status: "not_loaded",
        amcl_pose_observed: "not_loaded",
        localization_tf_observed: "not_loaded",
        robot_pose_status: "not_observed",
        robot_pose_frame_id: "not_loaded",
        robot_pose_x: "not_loaded",
        robot_pose_y: "not_loaded",
      },
      nav2: {
        status: "not_loaded",
        nav2_status: "not_loaded",
        nav2_stack_running: "not_loaded",
        nav2_stack_lifecycle_state: "not_loaded",
        current_blocker_reasons: "none",
        current_blocker_labels: "not_loaded",
        planner_server_active: "not_loaded",
        controller_server_active: "not_loaded",
        controller_server_requested: "not_loaded",
        map_consumed: "not_loaded",
        path_generation_attempted: "not_loaded",
        path_generation_service_available: "not_loaded",
        path_generation_service_name: "not_loaded",
        path_generated: "not_loaded",
        path_generation_succeeded: "not_loaded",
        path_point_count: "not_loaded",
        path_preview_point_count: "0",
        path_preview_frame_id: "not_loaded",
        execution_status_plain: "图上路线还未准备完成。",
        next_action_plain: "先准备图上路线并刷新地图画面，再勾选安全确认执行。",
        route_execution_readiness_plain: "图上路线还不可执行；当前缺口：图上路线还未准备完成。",
        route_execution_precheck_plain: "路线准备完成后，执行只需勾选行程前安全确认。",
        goal_execution_wheel_raw_lr_status_plain: "本轮完整路线执行的 wheel raw L/R 还未证明。",
        goal_execution_wheel_raw_lr_next_action_plain: "先准备图上路线并执行，再在同窗口确认 wheel raw L/R 非零。",
        goal_execution_status: "not_loaded",
        goal_execution_proven: "not_loaded",
        goal_execution_hil_pass: "not_loaded",
        goal_execution_result_status: "not_loaded",
        goal_execution_evidence_ref: "not_loaded",
        goal_execution_robot_control_executed: "not_loaded",
        goal_execution_feedback_sample_count: "not_loaded",
        goal_execution_base_command_mode: "not_loaded",
        next_execution_base_command_mode: "not_loaded",
        goal_execution_mode_rerun_status: "not_loaded",
        goal_execution_base_command_nonzero_observed: "not_loaded",
        goal_execution_base_command_nonzero_count: "not_loaded",
        goal_execution_base_command_latest_nonzero_mode: "not_loaded",
        goal_execution_base_command_mode_counts: "{}",
        goal_execution_base_feedback_sample_count: "not_loaded",
        goal_execution_base_feedback_nonzero_sample_count: "not_loaded",
        goal_execution_base_feedback_lr_nonzero_proven: "not_loaded",
        goal_execution_base_feedback_imu_attitude_delta_observed: "not_loaded",
        goal_execution_base_feedback_imu_roll_delta: "not_loaded",
        goal_execution_base_feedback_imu_pitch_delta: "not_loaded",
        goal_execution_base_feedback_latest_left_speed: "not_loaded",
        goal_execution_base_feedback_latest_right_speed: "not_loaded",
        goal_execution_base_feedback_latest_raw_left: "not_loaded",
        goal_execution_base_feedback_latest_raw_right: "not_loaded",
        goal_execution_sends_base_motion_commands: "not_loaded",
        goal_execution_uses_base_uart: "not_loaded",
        goal_execution_goal_frame_id: "not_loaded",
        goal_execution_goal_x: "not_loaded",
        goal_execution_goal_y: "not_loaded",
        goal_execution_generated_at_ms: "not_loaded",
        goal_execution_response_generated_at_ms: "not_loaded",
      },
      keyboard: keyboardSummaryReadback(),
      free_roam: {
        status: "not_loaded",
        runtime_status: "not_loaded",
        decision_state: "not_loaded",
        decision_reason: "not_loaded",
        stop_required: "not_loaded",
        artifact_only: "not_loaded",
        cmd_vel_publish_enabled: "not_loaded",
        start_ready: "false",
        motion_start_ready: "false",
        motion_ready: "false",
        mapping_ready: "false",
        mapping_missing: "not_loaded",
        next_action_plain: "先连接上车自由移动状态机，并确认停止兜底可用",
        motion_readiness_plain: "自由移动未就绪；先连接上车状态机并确认停止兜底。",
        mapping_readiness_plain: "建图验收未 ready；还在等待上车状态机。",
        motion_next_action_plain: "先连接上车自由移动状态机，并确认停止兜底可用。",
        mapping_next_action_plain: "先连接上车自由移动状态机，并继续读取建图验收材料。",
        runtime_artifact_proven: "not_loaded",
        state_machine_observed: "not_loaded",
        ros2_runtime_proven: "not_loaded",
        gate_count: "0",
      },
    },
    operator_hil_material_summary: notLoadedHilMaterialSummary("not_loaded"),
    first_jog_readiness_summary: buildFirstJogReadinessSummary(notLoadedHilMaterialSummary("not_loaded")),
    safe_command_boundary: lockedBoundary(),
    blocked_reasons: [reason],
    not_proven: ["robot_api_readback", "O7", "path_generated", "delivery_success"],
    ...PROOF_FLAGS,
  };
}

function freeRoamRuntimeGatesFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
): RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_gates"] | null {
  const latest = freeRoamRuntimeLatestFromReadbacks(readbacks);
  if (!latest) {
    return null;
  }
  const decision = asRecord(latest.decision);
  const snapshot = asRecord(latest.snapshot);
  const externalStopRequested = snapshot?.external_stop_requested === true;
  const runtimeLidarAgeS = finitePathCoordinate(snapshot?.lidar_age_s);
  const runtimeLidarMinDistanceM = finitePathCoordinate(snapshot?.lidar_min_distance_m);
  const runtimeLidarFreshFromSnapshot = Boolean(
    runtimeLidarAgeS !== null
    && runtimeLidarAgeS <= 1.5
    && runtimeLidarMinDistanceM !== null,
  );
  const rawGates = Array.isArray(decision?.gates) ? decision.gates : [];
  const hasRuntimeMappingGate = rawGates
    .map((item) => asRecord(item))
    .some((gate) => asString(gate?.id, "") === "mapping_active");
  const runtimeMappingActive = typeof snapshot?.mapping_active === "boolean" ? snapshot.mapping_active : null;
  const mapRuntimeStarted = proofBoolean(readbacks, ["managed_runtime_started"]) === true;
  const gateScope = (id: string): "free_move_start" | "mapping_acceptance" | "runtime_diagnostic" => {
    // 上车端 gate 是运行时事实；PC 首屏必须把“启动移动”和“建图验收”拆开，避免雷达阻塞低速自由移动。
    if (id === "operator_confirmed" || id === "stop_available") {
      return "free_move_start";
    }
    if (id === "mapping_active" || id === "lidar_fresh" || id === "obstacle_clear" || id === "camera_first_frame" || id === "fresh_map_preview") {
      return "mapping_acceptance";
    }
    return "runtime_diagnostic";
  };
  const gateRows: FreeRoamGateRow[] = rawGates
    .map((item) => asRecord(item))
    .filter((item): item is JsonRecord => item !== null)
    .map((gate) => {
      const rawState = asString(gate.state, "blocked");
      const state: "ready" | "blocked" | "not_proven" = rawState === "ready" || rawState === "not_proven" ? rawState : "blocked";
      const id = asString(gate.id, "free_roam_runtime_gate");
      return {
        id,
        label: asString(gate.label, "自动扫图门禁"),
        scope: gateScope(id),
        state,
        evidence: asString(gate.evidence, "未读到自动扫图门禁证据"),
        next_action: asString(gate.next_action, "等待上车端自动扫图节点更新"),
      };
    });
  const hasGate = (id: string): boolean => gateRows.some((gate) => gate.id === id);
  const mappingActiveGate = gateRows.find((gate) => gate.id === "mapping_active");
  if (mappingActiveGate && mappingActiveGate.state !== "ready" && !/低速自由移动|现场监看/.test(mappingActiveGate.next_action)) {
    // 旧上车 artifact 的 mapping gate 文案只说启动建图；PC 要补上“这不是低速移动前置”的产品口径。
    mappingActiveGate.next_action = "先启动扫地式建图记录；这不影响现场监看的低速自由移动";
  }
  const radarStatusPayload = readbackById(readbacks, "radar_status")?.payload ?? null;
  const radarScanProofPayload = readbackById(readbacks, "radar_scan_proof_latest")?.payload ?? null;
  const radarFreshValues = [
    summaryValueText(radarStatusPayload, ["latest_scan_proof_fresh"], ""),
    summaryValueText(radarScanProofPayload, ["latest_scan_proof_fresh"], ""),
  ].filter((value) => value !== "");
  const radarFreshReadbackLoaded = radarFreshValues.length > 0;
  const radarFreshProven = radarFreshValues.some((value) => value === "true");
  const runtimeLidarFreshGate = gateRows.find((gate) => gate.id === "lidar_fresh");
  if (runtimeLidarFreshGate && runtimeLidarFreshFromSnapshot) {
    // free-roam runtime 直接消费实时 /scan；它比过期 proof artifact 更贴近当前地图雷达所见即所得。
    runtimeLidarFreshGate.state = "ready";
    runtimeLidarFreshGate.evidence = `free-roam runtime /scan 新鲜：距离 ${runtimeLidarMinDistanceM?.toFixed(2)}m，延迟 ${runtimeLidarAgeS?.toFixed(2)}s`;
    runtimeLidarFreshGate.next_action = radarFreshReadbackLoaded && !radarFreshProven
      ? "proof latest 可能过期；建图按 runtime scan 继续监看，必要时再刷新雷达 proof"
      : "继续保持雷达运行";
  } else if (runtimeLidarFreshGate && radarFreshReadbackLoaded && !radarFreshProven) {
    // 没有同轮 runtime scan 快照时，建图验收必须以最新 proof freshness 为准；旧 gate 不能覆盖 stale readback。
    runtimeLidarFreshGate.state = "not_proven";
    runtimeLidarFreshGate.evidence = "雷达最新扫描未刷新";
    runtimeLidarFreshGate.next_action = "先刷新雷达；刷新前只能按自由移动记录";
  }
  const lidarFreshGate = gateRows.find((gate) => gate.id === "lidar_fresh");
  const lidarFreshExpired = Boolean(
    lidarFreshGate
    && lidarFreshGate.state !== "ready"
    && /未刷新|过期|未运行|stale|not_fresh|stopped|lifecycle_not_running/i.test(`${lidarFreshGate.evidence} ${lidarFreshGate.next_action}`),
  );
  if (lidarFreshExpired) {
    const obstacleGate = gateRows.find((gate) => gate.id === "obstacle_clear");
    if (obstacleGate && /(?:最近障碍|障碍|距离)\s*[0-9]+(?:\.[0-9]+)?\s*m/i.test(obstacleGate.evidence)) {
      // 雷达已过期或未运行时不能继续把旧障碍距离贴到地图；只保留“需要刷新”的事实。
      obstacleGate.state = "not_proven";
      obstacleGate.evidence = "雷达未刷新，障碍距离不可用";
      obstacleGate.next_action = "先刷新雷达；刷新前不把旧障碍距离贴到地图";
    }
  }
  if (!hasRuntimeMappingGate) {
    // 新 runtime 的 mapping_active gate 优先；只有旧 runtime 没有该 gate 时才从 snapshot/map proof 兼容补齐。
    const active = runtimeMappingActive === true || (runtimeMappingActive === null && mapRuntimeStarted);
    gateRows.push({
      id: "mapping_active",
      label: "地图记录",
      scope: "mapping_acceptance",
      state: active ? "ready" : "not_proven",
      evidence: active ? "当前读回已证明地图记录 runtime 已启动" : "free-roam runtime 显示地图记录未启动",
      next_action: active ? "继续保持地图记录并监看画面" : "先启动扫地式建图记录；这不影响现场监看的低速自由移动",
    });
  }
  if (externalStopRequested && !hasGate("external_stop_request")) {
    // stop 是上一次会话留下的安全状态；它不是雷达问题，下一次 start 会在现场确认后显式清掉。
    gateRows.push({
      id: "external_stop_request",
      label: "停止请求",
      scope: "runtime_diagnostic",
      state: "not_proven",
      evidence: "上车自由移动状态机仍处于停止请求",
      next_action: "勾选现场安全确认后点击开始自由移动；start 会清除停止请求并打开低速运动双锁",
    });
  }
  if (!hasGate("camera_first_frame")) {
    const cameraHealthPayload = readbackById(readbacks, "camera_health")?.payload ?? null;
    const cameraStatus = readbackById(readbacks, "camera_health")?.status ?? summaryValueText(cameraHealthPayload, ["status"], "");
    const sourceReadiness = summaryValueText(cameraHealthPayload, ["source_readiness"], "");
    const sourceFailureReason = summaryValueText(cameraHealthPayload, ["source_failure_reason"], "");
    const visibleContent = summaryValueText(cameraHealthPayload, ["visible_content_proven"], "");
    const sourceDiagnosis = asRecord(findFirstKey(cameraHealthPayload, ["source_diagnosis"]));
    const sourceUsage = asRecord(findFirstKey(cameraHealthPayload, ["source_usage"]));
    const usageLooksFree = ["not_in_use", ""].includes(asString(sourceUsage?.status, ""))
      || compactValueText(sourceUsage?.owner_count ?? "not_loaded") === "0";
    const notExclusive = sourceDiagnosis?.not_exclusive === true
      || asString(sourceDiagnosis?.status, "") === "uvc_no_frame_not_exclusive"
      || (usageLooksFree && CAMERA_FIRST_FRAME_FAILURE_REASONS.includes(sourceFailureReason as typeof CAMERA_FIRST_FRAME_FAILURE_REASONS[number]));
    const ready = sourceReadiness === "first_frame_observed" || visibleContent === "true";
    const failed = cameraStatus === "source_first_frame_failed" || sourceReadiness === "first_frame_failed";
    gateRows.push({
      id: "camera_first_frame",
      label: "画面首帧",
      scope: "mapping_acceptance",
      state: ready ? "ready" : "not_proven",
      evidence: ready
        ? "摄像头首帧已读到"
        : failed && notExclusive
          ? "画面首帧未出，不是页面独占"
          : failed ? "画面首帧未出" : "未读到摄像头首帧证据",
      next_action: ready
        ? "继续监看共享预览"
        : failed
          ? "检查 USB/摄像头输入/供电，必要时换 known-good UVC；自由移动可继续监看"
          : "先打开共享预览或检查画面；自由移动可继续监看",
    });
  }
  if (!hasGate("lidar_fresh")) {
    const lidarFreshReady = runtimeLidarFreshFromSnapshot || radarFreshProven;
    gateRows.push({
      id: "lidar_fresh",
      label: "雷达新鲜",
      scope: "mapping_acceptance",
      state: lidarFreshReady ? "ready" : "not_proven",
      evidence: lidarFreshReady
        ? "雷达扫描已刷新"
        : "雷达最新扫描未刷新",
      next_action: lidarFreshReady
        ? "继续保持雷达运行"
        : "先刷新雷达；刷新前只能按自由移动记录",
    });
  }
  if (!hasGate("fresh_map_preview")) {
    gateRows.push({
      id: "fresh_map_preview",
      label: "地图画面",
      scope: "mapping_acceptance",
      state: "not_proven",
      evidence: "地图画面未刷新",
      next_action: "刷新地图画面后再按建图验收",
    });
  }
  const cmdVelPublishEnabled = latest.cmd_vel_publish_enabled === true;
  const startFallbackReady = gateRows.some((gate) => gate.id === "stop_available" && gate.state === "ready");
  const motionGateState: "ready" | "blocked" | "not_proven" = cmdVelPublishEnabled
    ? "ready"
    : startFallbackReady
      ? "not_proven"
      : "blocked";
  gateRows.push({
    id: "motion_hil_unlock",
    label: "运动发布状态",
    scope: "runtime_diagnostic",
    state: motionGateState,
    evidence: cmdVelPublishEnabled
      ? "自由移动状态机已打开运动发布"
      : startFallbackReady
        ? "当前尚未启动自由移动，点击开始后由上车端打开运动双锁"
        : "自由移动状态机默认只写记录，不发布运动",
    next_action: cmdVelPublishEnabled
      ? "PC 继续只读监看地图、雷达和停止兜底，不在 summary 中直接发车"
      : startFallbackReady
        ? "勾选现场安全确认后点击开始自由移动（低速）"
        : "先确认上车端停止兜底和自动扫图 runtime",
  });
  return gateRows.length > 0 ? sortFreeRoamGateRows(gateRows) : null;
}

function freeRoamRuntimeLatestFromReadbacks(readbacks: InternalRobotApiEndpointReadback[]): JsonRecord | null {
  // 优先消费独立 latest 端点；旧上位机没有该端点时，再看 /api/status 聚合字段。
  const endpointPayload = readbackById(readbacks, "free_roam_autonomy_latest")?.payload ?? null;
  const statusPayload = readbackById(readbacks, "status")?.payload ?? null;
  const statusFreeRoam = asRecord(statusPayload?.free_roam_autonomy);
  const statusLatest = asRecord(statusFreeRoam?.latest);
  return asRecord(endpointPayload?.latest_result)
    ?? asRecord(statusLatest?.latest_result)
    ?? asRecord(statusFreeRoam?.latest_result);
}

function freeRoamRuntimeSummaryFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
): RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_runtime"] | null {
  // runtime 摘要只解释上车状态机最近一次判断；PC 按钮仍保持锁定。
  const latest = freeRoamRuntimeLatestFromReadbacks(readbacks);
  if (!latest) {
    return null;
  }
  const decision = asRecord(latest.decision);
  return {
    status: "loaded",
    state: asString(decision?.state, "not_loaded"),
    reason: asString(decision?.reason, "not_loaded"),
    stop_required: decision?.stop_required === true,
    artifact_only: latest.artifact_only !== false,
    cmd_vel_publish_enabled: latest.cmd_vel_publish_enabled === true,
  };
}

function freeRoamMappingMissingIds(
  freeRoamRuntimeGates: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_gates"] | null,
): string[] {
  // 自由移动不依赖相机/雷达；建图验收才需要这些材料同时 ready。
  const mappingRequiredIds = ["camera_first_frame", "lidar_fresh", "mapping_active", "fresh_map_preview"];
  const mappingGateById = new Map((freeRoamRuntimeGates ?? [])
    .filter((gate) => gate.scope === "mapping_acceptance")
    .map((gate) => [gate.id, gate]));
  return mappingRequiredIds.filter((id) => mappingGateById.get(id)?.state !== "ready");
}

function joinChineseList(items: string[]): string {
  // 短中文列表不加技术分隔符，普通首屏读起来更像一句话。
  return items.join("和");
}

function freeRoamMissingPlainLabels(missingReasons: string[]): string[] {
  // summary 顶层下一步不暴露内部 gate token，避免普通页面还要自己维护翻译表。
  const labels: Record<string, string> = {
    camera_first_frame: "画面首帧",
    lidar_fresh: "雷达新鲜",
    mapping_active: "地图记录",
    fresh_map_preview: "地图画面",
  };
  return missingReasons.map((reason) => labels[reason] ?? reason).filter(Boolean);
}

function freeRoamAutonomyNextAction(
  status: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy"],
  mappingReady: boolean,
  mappingMissingReasons: string[],
  freeRoamRuntime: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_runtime"] | null = null,
): string {
  // 自由移动和建图验收分层：能动不等于可验收建图，下一步必须把这两件事讲清楚。
  const missingText = freeRoamMissingPlainLabels(mappingMissingReasons).join("、");
  const externalStopRequested = freeRoamRuntime?.state === "stopping" && /现场请求停止|external_stop/i.test(freeRoamRuntime.reason);
  if (status === "ready" && mappingReady) {
    return "已进入自动扫图条件；继续低速监看地图、雷达和画面";
  }
  if (status === "ready") {
    return missingText
      ? `自由移动运行中；建图验收还差：${missingText}`
      : "自由移动运行中；继续监看建图验收材料";
  }
  if (status === "start_ready") {
    const motionAction = externalStopRequested
      ? "当前处于停止请求；勾选现场安全确认后可先自由移动，开始时会先解除停止请求"
      : mappingReady
        ? "勾选现场安全确认后可开始自动扫图（低速）"
        : "勾选现场安全确认后可先自由移动";
    if (mappingReady) {
      return motionAction;
    }
    return missingText
      ? `${motionAction}；建图验收还差：${missingText}`
      : `${motionAction}；继续读取建图验收材料`;
  }
  return "先连接上车自由移动状态机，并确认停止兜底可用";
}

function freeRoamMotionNextAction(startReady: boolean, motionReady: boolean, externalStopRequested: boolean): string {
  // 自由移动只看安全确认和停止兜底；相机/雷达/地图记录只影响建图验收，不该写成不能动。
  if (motionReady) {
    return "自由移动运行中；需要收口时点击停止自由移动或红色停止。";
  }
  if (startReady) {
    const stopPrefix = externalStopRequested
      ? "当前处于停止请求；开始自由移动会先解除停止请求。"
      : "";
    return `${stopPrefix}勾选现场安全确认后可先自由移动；相机和雷达只影响建图验收。`;
  }
  return "先连接上车自由移动状态机，并确认停止兜底可用。";
}

function freeRoamMotionReadinessPlain(startReady: boolean, motionReady: boolean, externalStopRequested: boolean): string {
  // 这句只回答“能不能先自己低速移动”，不夹带建图传感器缺口，方便首屏和脚本直接展示。
  if (motionReady) {
    return "自由移动正在运行；相机和雷达不作为继续移动的前置。";
  }
  if (startReady) {
    return externalStopRequested
      ? "可先自由移动；当前有停止请求，开始自由移动会先清除停止请求。"
      : "可先自由移动；只需要现场安全确认和停止兜底。";
  }
  return "自由移动未就绪；先连接上车状态机并确认停止兜底。";
}

function freeRoamMappingReadinessPlain(startReady: boolean, mappingReady: boolean, mappingMissingReasons: string[]): string {
  // 建图是验收条件；只有画面、雷达、地图记录和地图画面都 ready 时才说可按建图记录。
  if (mappingReady) {
    return "建图验收已 ready：画面、雷达、地图记录和地图画面都可用。";
  }
  const missingText = freeRoamMissingPlainLabels(mappingMissingReasons).join("、");
  if (!startReady) {
    return missingText
      ? `建图验收未 ready；还差：${missingText}。`
      : "建图验收未 ready；还在等待上车状态机。";
  }
  return missingText
    ? `建图验收未 ready；还差：${missingText}；不影响先低速自由移动。`
    : "建图验收材料还在读取；不影响先低速自由移动。";
}

function freeRoamMappingNextAction(startReady: boolean, mappingReady: boolean, mappingMissingReasons: string[]): string {
  // 建图验收单独解释缺口，让脚本不用从“能动”的下一步里反推传感器条件。
  if (mappingReady) {
    return "建图验收已 ready；继续低速监看地图、雷达和画面。";
  }
  const missingText = freeRoamMissingPlainLabels(mappingMissingReasons).join("、");
  if (!startReady) {
    return missingText
      ? `先连接上车自由移动状态机；建图验收还差：${missingText}。`
      : "先连接上车自由移动状态机，并继续读取建图验收材料。";
  }
  return missingText
    ? `建图验收还差：${missingText}；不影响先低速自由移动。`
    : "继续读取建图验收材料；不影响先低速自由移动。";
}

function nav2GoalBoundaryFromProof(proof: RobotApiProofSummary | null): Pick<
  RobotControlSummaryResponse["safe_command_boundary"],
  "nav2_goal_ready" | "nav2_goal_label" | "nav2_goal_blockers" | "nav2_goal_wheel_feedback_status" | "nav2_goal_next_action" | "nav2_goal_next_action_plain" | "nav2_goal_execution_mode_label"
> {
  // summary 只把路线读数作为硬条件；小车 map 位姿是 WYSIWYG 建议，不再阻塞最小发车确认。
  const blockers = [
    proof?.path_generated === true || proof?.path_generation_succeeded === true ? "" : "path_generation_not_observed",
    (proof?.path_point_count ?? 0) > 0 || (proof?.path_preview_point_count ?? 0) > 0 ? "" : "path_point_count_not_positive",
  ].filter(Boolean);
  const ready = blockers.length === 0;
  const poseHint = proof?.robot_pose ? "" : "；小车位置未显示时建议先重新定位或刷新地图";
  return {
    nav2_goal_ready: ready,
    nav2_goal_label: ready ? "路线读数已准备，等待地图画面确认" : "图上路线未就绪",
    nav2_goal_blockers: blockers,
    nav2_goal_wheel_feedback_status: "not_loaded",
    nav2_goal_next_action: ready ? `勾选行程前安全确认后执行图上路线${poseHint}` : "先生成图上路线",
    nav2_goal_next_action_plain: nav2GoalNextActionPlainText(ready ? `勾选行程前安全确认后执行图上路线${poseHint}` : "先生成图上路线"),
    nav2_goal_execution_mode_label: "not_loaded",
  };
}

function nav2GoalNextActionPlainText(action: string): string {
  // 普通用户只需要知道下一步怎么做；保留原 token/术语字段给高级诊断。
  return action
    .replace(/Nav2 planner 和 Nav2 controller/g, "规划服务和控制服务")
    .replace(/Nav2 planner/g, "规划服务")
    .replace(/Nav2 controller/g, "控制服务")
    .replace(/或 controller/g, "或控制服务")
    .replace(/\bcontroller\b/g, "控制服务")
    .replace(/路线 action 成功/g, "路线结果成功")
    .replace(/wheel raw L\/R/g, "执行窗口轮速 L/R")
    .replace(/\bPWM\b/g, "PWM 模式")
    .replace(/\bROS\b/g, "ROS 模式")
    .replace(/\bSPEED\b/g, "SPEED 模式")
    .replace(/和 执行窗口/g, "和执行窗口")
    .replace(/但 执行窗口/g, "但执行窗口")
    .replace(/复验 执行窗口/g, "复验执行窗口")
    .replace(/模式 重跑/g, "模式重跑")
    .replace(/\sruntime\b/gi, " runtime");
}

function nav2GoalBoundaryGuidance(
  proof: RobotApiProofSummary | null,
  nav2: RobotControlSummaryResponse["readback_summary"]["nav2"] | null = null,
): Pick<
  RobotControlSummaryResponse["safe_command_boundary"],
  "nav2_goal_ready" | "nav2_goal_label" | "nav2_goal_blockers" | "nav2_goal_wheel_feedback_status" | "nav2_goal_next_action" | "nav2_goal_next_action_plain" | "nav2_goal_execution_mode_label"
> {
  // 这组字段是给普通 PC 首屏/API 的短口径：路线能不能点、上次执行为什么不算完整、下一次应该怎么复验。
  const base = nav2GoalBoundaryFromProof(proof);
  if (!nav2) {
    return base;
  }
  const succeeded = nav2.goal_execution_status === "goal_succeeded" || nav2.goal_execution_result_status === "succeeded";
  const proven = nav2.goal_execution_proven === "true";
  const wheelProven = nav2.goal_execution_base_feedback_lr_nonzero_proven === "true";
  const left = nav2.goal_execution_base_feedback_latest_raw_left || nav2.goal_execution_base_feedback_latest_left_speed || "not_loaded";
  const right = nav2.goal_execution_base_feedback_latest_raw_right || nav2.goal_execution_base_feedback_latest_right_speed || "not_loaded";
  const currentMode = nav2.goal_execution_base_command_mode || "not_loaded";
  const nextMode = nav2.next_execution_base_command_mode || "not_loaded";
  const baseCommandCount = Number(nav2.goal_execution_base_command_nonzero_count);
  const executionMotionMaterialObserved = nav2.goal_execution_base_command_nonzero_observed === "true"
    || (Number.isFinite(baseCommandCount) && baseCommandCount > 0)
    || nav2.goal_execution_sends_base_motion_commands === "true"
    || nav2.goal_execution_base_feedback_imu_attitude_delta_observed === "true";
  const plannerInactive = nav2.planner_server_active === "false";
  const controllerInactive = nav2.controller_server_active === "false";
  const nav2StackNotRunning = nav2.nav2_stack_running === "false";
  const controllerRequested = nav2.controller_server_requested === "true";
  const nav2LifecycleBlocked = nav2.current_blocker_reasons.split(",").includes("nav2_lifecycle_not_running");
  // no-motion planner proof 会在生成路线后清理 managed runtime；execute endpoint 会托管启动 runtime，不能因此挡住已读到的路线。
  const nav2StackBlocksGoal = nav2StackNotRunning && !base.nav2_goal_ready;
  const plannerBlocksGoal = !nav2StackBlocksGoal && plannerInactive && (!base.nav2_goal_ready || !nav2StackNotRunning);
  const controllerBlocksGoal = !nav2StackBlocksGoal && controllerInactive && controllerRequested;
  const serviceAwareBlockers = [
    ...base.nav2_goal_blockers,
    nav2StackBlocksGoal ? (nav2LifecycleBlocked ? "nav2_lifecycle_not_running" : "nav2_stack_not_running") : "",
    plannerBlocksGoal ? "planner_server_inactive" : "",
    controllerBlocksGoal ? "controller_server_inactive" : "",
  ].filter(Boolean);
  const nav2ServiceBlockers = sortNav2GoalBlockers([...new Set(serviceAwareBlockers)]);
  const inactiveServiceNames = [
    nav2StackBlocksGoal ? "自动驾驶服务（不发车）" : "",
    plannerBlocksGoal ? "规划服务" : "",
    controllerBlocksGoal ? "控制服务" : "",
  ].filter(Boolean);
  const serviceInactiveText = [
    nav2StackBlocksGoal ? "自动驾驶服务当前未启动" : "",
    plannerBlocksGoal ? "规划服务当前未运行" : "",
    controllerBlocksGoal ? "控制服务当前未运行" : "",
  ].filter(Boolean);
  const serviceInactiveSuffix = serviceInactiveText.length
    ? `；${serviceInactiveText.join("，")}，重跑前需先${nav2StackNotRunning ? "启动" : "恢复"}${joinChineseList(inactiveServiceNames)}`
    : "";
  const nav2ServiceInactive = nav2StackBlocksGoal || plannerBlocksGoal || controllerBlocksGoal;
  const managedRuntimeHint = nav2LifecycleBlocked && base.nav2_goal_ready
    ? "；执行时会自动启动自动驾驶 runtime"
    : "";
  const executionMotionText = nav2.goal_execution_base_feedback_imu_attitude_delta_observed === "true"
    ? nav2ServiceInactive
      ? "；已看到旧执行的非零底盘命令和 IMU 姿态变化，旧执行主因不是雷达或相机"
      : "；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或 controller"
    : executionMotionMaterialObserved
      ? nav2ServiceInactive
        ? "；已看到旧执行运动材料，旧执行主因不是雷达或相机"
        : "；已看到执行运动材料，主因不是雷达、相机或 controller"
      : "";
  const modeChanged = !["", "not_loaded"].includes(currentMode) && !["", "not_loaded"].includes(nextMode) && currentMode !== nextMode;
  const modeLabel = modeChanged
    ? `上次 ${currentMode}，下次 ${nextMode}`
    : !["", "not_loaded"].includes(nextMode)
      ? `下次 ${nextMode}`
      : !["", "not_loaded"].includes(currentMode) ? `上次 ${currentMode}` : "not_loaded";
  if (proven || wheelProven) {
    const nextAction = "本轮路线和 wheel raw L/R 已证明，继续送达确认";
    return {
      ...base,
      nav2_goal_wheel_feedback_status: "wheel_lr_nonzero_proven",
      nav2_goal_next_action: nextAction,
      nav2_goal_next_action_plain: nav2GoalNextActionPlainText(nextAction),
      nav2_goal_execution_mode_label: modeLabel,
    };
  }
  if (succeeded && nav2.goal_execution_base_feedback_lr_nonzero_proven === "false") {
    const rerunMode = !["", "not_loaded"].includes(nextMode) ? nextMode.toUpperCase() : "当前模式";
    const serviceRestoreActions = inactiveServiceNames.length
      ? [`${nav2StackNotRunning ? "启动" : "恢复"}${joinChineseList(inactiveServiceNames)}`]
      : [];
    const routeReadinessActions = base.nav2_goal_ready ? [] : ["生成图上路线"];
    const routePrepActions = [
      ...serviceRestoreActions,
      ...routeReadinessActions,
    ];
    const rerunNextAction = !base.nav2_goal_ready
      ? `当前图上路线未就绪，先${routePrepActions.join("，再")}，再勾选行程前安全确认后用 ${rerunMode} 重跑并复验 wheel raw L/R`
      : inactiveServiceNames.length
        ? `当前自动驾驶服务未就绪，先${routePrepActions.join("，再")}，再勾选行程前安全确认后用 ${rerunMode} 重跑并复验 wheel raw L/R`
        : `勾选行程前安全确认后用 ${rerunMode} 重跑图上路线${managedRuntimeHint}`;
    const nextAction = `上次路线 action 成功但 wheel raw L/R=${left}/${right} 未非零${executionMotionText}${routePrepActions.length ? "" : serviceInactiveSuffix}；${rerunNextAction}`;
    return {
      ...base,
      nav2_goal_ready: nav2ServiceInactive ? false : base.nav2_goal_ready,
      nav2_goal_label: nav2StackBlocksGoal
        ? "自动驾驶服务未启动"
        : plannerBlocksGoal && controllerBlocksGoal && base.nav2_goal_ready
        ? "规划/控制服务未就绪"
        : plannerBlocksGoal && base.nav2_goal_ready
          ? "规划服务未就绪"
          : controllerBlocksGoal && base.nav2_goal_ready ? "控制服务未就绪" : base.nav2_goal_label,
      nav2_goal_blockers: nav2ServiceBlockers,
      nav2_goal_wheel_feedback_status: "goal_succeeded_but_wheel_lr_zero",
      nav2_goal_next_action: nextAction,
      nav2_goal_next_action_plain: nav2GoalNextActionPlainText(nextAction),
      nav2_goal_execution_mode_label: modeLabel,
    };
  }
  if (base.nav2_goal_ready && nav2ServiceInactive) {
    const serviceLabel = nav2StackBlocksGoal
      ? "自动驾驶服务未启动"
      : plannerBlocksGoal && controllerBlocksGoal
      ? "规划/控制服务未就绪"
      : plannerBlocksGoal ? "规划服务未就绪" : "控制服务未就绪";
    const serviceNextAction = inactiveServiceNames.length
      ? `先${nav2StackNotRunning ? "启动" : "恢复"}${joinChineseList(inactiveServiceNames)}，再勾选行程前安全确认后执行图上路线，并在同窗口复验 wheel raw L/R`
      : "先恢复自动驾驶服务，再勾选行程前安全确认后执行图上路线，并在同窗口复验 wheel raw L/R";
    return {
      ...base,
      nav2_goal_ready: false,
      nav2_goal_label: serviceLabel,
      nav2_goal_blockers: nav2ServiceBlockers,
      nav2_goal_wheel_feedback_status: "awaiting_route_execution",
      nav2_goal_next_action: serviceNextAction,
      nav2_goal_next_action_plain: nav2GoalNextActionPlainText(serviceNextAction),
      nav2_goal_execution_mode_label: modeLabel,
    };
  }
  if (base.nav2_goal_ready) {
    const poseHint = proof?.robot_pose ? "" : "；小车位置未显示时建议先重新定位或刷新地图";
    const nextAction = `勾选行程前安全确认后执行图上路线${managedRuntimeHint}，并在同窗口复验 wheel raw L/R${poseHint}`;
    return {
      ...base,
      nav2_goal_wheel_feedback_status: "awaiting_route_execution",
      nav2_goal_next_action: nextAction,
      nav2_goal_next_action_plain: nav2GoalNextActionPlainText(nextAction),
      nav2_goal_execution_mode_label: modeLabel,
    };
  }
  const fallbackNextAction = inactiveServiceNames.length
    ? `先${nav2StackNotRunning ? "启动" : "恢复"}${joinChineseList(inactiveServiceNames)}，再生成图上路线`
    : base.nav2_goal_next_action;
  return {
    ...base,
    nav2_goal_label: nav2StackBlocksGoal ? "自动驾驶服务未启动" : base.nav2_goal_label,
    nav2_goal_blockers: nav2ServiceBlockers,
    nav2_goal_next_action: fallbackNextAction,
    nav2_goal_next_action_plain: nav2GoalNextActionPlainText(fallbackNextAction),
    nav2_goal_execution_mode_label: modeLabel,
  };
}

function lockedBoundary(
  freeRoamRuntimeGates: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_gates"] | null = null,
  freeRoamRuntime: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_runtime"] | null = null,
  proof: RobotApiProofSummary | null = null,
  nav2: RobotControlSummaryResponse["readback_summary"]["nav2"] | null = null,
): RobotControlSummaryResponse["safe_command_boundary"] {
  // 控制边界集中在后端返回，避免前端以后误加 enabled 状态。
  const startGates = (freeRoamRuntimeGates ?? []).filter((gate) => gate.id === "stop_available");
  const stopFallbackReady = startGates.length === 0 || startGates.every((gate) => gate.state === "ready");
  const freeRoamStartReady = Boolean(
    freeRoamRuntime?.status === "loaded"
    && stopFallbackReady,
  );
  const freeRoamReady = Boolean(
    freeRoamRuntime?.status === "loaded"
    && freeRoamRuntime.cmd_vel_publish_enabled
    && stopFallbackReady,
  );
  const freeRoamMappingMissingReasons = freeRoamMappingMissingIds(freeRoamRuntimeGates);
  const freeRoamMappingReady = freeRoamStartReady && freeRoamMappingMissingReasons.length === 0;
  const freeRoamStatus = freeRoamReady ? "ready" : freeRoamStartReady ? "start_ready" : "locked";
  const freeRoamNextAction = freeRoamAutonomyNextAction(freeRoamStatus, freeRoamMappingReady, freeRoamMappingMissingReasons, freeRoamRuntime);
  const keyboardNextAction = "勾选现场安全确认后点击启用键盘；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停";
  const keyboardStopTriggers = ["key_released", "window_blur", "page_hidden", "direction_changed", "button_stop"];
  const nav2MinimalPrecheckPlain = "执行图上路线只复核现场安全确认和固定白名单；相机、雷达和 operator report 不作为发车前额外预检。";
  return {
    manual_endpoint: "/api/base/manual",
    stop_endpoint: "/api/base/stop",
    cmd_vel_topic: "/cmd_vel",
    nav2_goal: "Nav2 NavigateToPose locked",
    ...nav2GoalBoundaryGuidance(proof, nav2),
    nav2_goal_minimal_precheck_plain: nav2MinimalPrecheckPlain,
    nav2_goal_precheck_plain: nav2MinimalPrecheckPlain,
    navigation_preflight_plain: nav2MinimalPrecheckPlain,
    map_start: "map start locked",
    radar_start: "radar start locked",
    keyboard_control: "bounded repeating manual pulse gated",
    keyboard_control_mode: "bounded_repeating_manual_pulse",
    keyboard_manual_command_mode: "ros",
    keyboard_manual_proxy_endpoint: "/api/robot-control/base/manual",
    keyboard_stop_proxy_endpoint: "/api/robot-control/base/stop",
    keyboard_jog_interval_ms: ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS,
    keyboard_jog_duration_ms: ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS,
    keyboard_stop_triggers: keyboardStopTriggers,
    keyboard_hold_to_move_plain: "必须按住 W/A/S/D 或方向键才会连续低速移动；只启用键盘但不按方向不会发车。",
    keyboard_stop_triggers_plain: "松开按键、窗口失焦、页面隐藏、切换方向或点击停止都会发送停止请求。",
    keyboard_pulse_timing_plain: `按住时约每 ${ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS / 1000} 秒发送一次 ${ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS / 1000} 秒低速脉冲。`,
    keyboard_reuses_manual_gate: true,
    keyboard_control_start_ready: true,
    keyboard_control_status: "start_ready",
    keyboard_control_label: "键盘手控（勾确认后可启用）",
    keyboard_control_next_action: keyboardNextAction,
    keyboard_minimal_precheck_plain: "键盘连续手控只复用现场安全确认；启用键盘不发车，只有按住方向键/WASD 才发送低速短脉冲。",
    keyboard_teleop_start_ready: true,
    keyboard_teleop_status: "start_ready",
    keyboard_teleop_next_action_plain: keyboardNextAction,
    free_roam_autonomy: freeRoamStatus,
    free_roam_autonomy_start_ready: freeRoamStartReady,
    free_roam_motion_start_ready: freeRoamStartReady,
    free_roam_mapping_ready: freeRoamMappingReady,
    free_roam_mapping_missing_reasons: freeRoamMappingMissingReasons,
    free_roam_autonomy_label: freeRoamReady
      ? freeRoamMappingReady ? "自动扫图" : "自由移动（运行中）"
      : freeRoamStartReady
        ? "自由移动（勾确认后可启动）"
        : "自动扫图（未开放）",
    free_roam_autonomy_next_action: freeRoamNextAction,
    free_roam_motion_minimal_precheck_plain: "自由移动只要求现场安全确认和停止兜底；相机、雷达、地图记录只影响建图验收。",
    free_roam_mapping_acceptance_plain: "建图验收要求画面首帧、雷达新鲜、地图记录和地图画面 ready；这些缺口不阻止先低速自由移动。",
    free_roam_autonomy_policy: {
      // 自由移动与建图验收分层：低速移动只看安全确认和停止兜底，建图才要求画面/雷达材料。
      mode: "free_move_requires_safety_confirm_stop_fallback",
      mapping_mode: "mapping_acceptance_requires_camera_and_fresh_radar",
      max_speed_mps: ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
      max_runtime_s: 60,
      required_gates: [
        "operator_safety_confirmed",
        "operator_stop_fallback",
      ],
      mapping_required_gates: [
        "camera_first_frame",
        "fresh_radar_scan",
        "map_recording_active",
        "fresh_map_preview",
      ],
    },
    free_roam_autonomy_gates: freeRoamRuntimeGates ?? defaultFreeRoamGateRows(),
    free_roam_autonomy_runtime: freeRoamRuntime ?? {
      status: "not_loaded",
      state: "not_loaded",
      reason: "not_loaded",
      stop_required: true,
      artifact_only: true,
      cmd_vel_publish_enabled: false,
    },
    map_click_goal: "map click goal locked",
    locked_reason: "bounded manual and keyboard pulse control require operator safety confirmation; primary autonomy and safe_control remain locked",
    manual_motion_entry_status: "controlled_jog_requires_safety_confirmation_only",
    manual_motion_entry_label: "低速手控（勾安全确认即可）",
    allowed_directions: [...ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS],
    non_stop_requires_confirm_hil_checklist: true,
    non_stop_requires_operator_report_preflight: false,
    operator_report_preflight_endpoint: OPERATOR_REPORT_REMOTE_ENDPOINT,
    operator_report_preflight_required_fields: [],
    speed_limit_mps: ROBOT_CONTROL_MANUAL_SPEED_LIMIT_MPS,
    duration_limit_ms: ROBOT_CONTROL_MANUAL_DURATION_LIMIT_MS,
    hil_checklist: [...ROBOT_CONTROL_HIL_CHECKLIST],
    command_dispatch_enabled: false,
    manual_control_enabled: false,
    navigate_goal_enabled: false,
    keyboard_control_enabled: false,
    robot_control_executed: false,
  };
}

function materialClaimReady(value: string): boolean {
  // operator summary 使用 "true; ref=..." 表达可追溯材料；not_loaded 不能被当成 ready。
  return value.startsWith("true; ref=") && !value.endsWith("not_loaded");
}

function buildFirstJogReadinessSummary(
  materialSummary: RobotControlOperatorHilMaterialSummary,
): RobotControlSummaryResponse["first_jog_readiness_summary"] {
  // first-jog 的硬门禁已经收敛为本地安全确认；summary 只提供旧 operator report 的参考材料状态。
  if (materialSummary.status !== "loaded") {
    return {
      status: "not_loaded",
      basic_safety_ready: false,
      visual_material_ready: false,
      missing_fields: ["operator_report_latest"],
      next_action: "connect_robot_api",
    };
  }
  const basicMissing = [
    materialSummary.operator_present === "true" ? "" : "operator_present",
    materialSummary.physical_clearance === "true" ? "" : "physical_clearance_confirmed",
    materialSummary.emergency_stop === "true" ? "" : "emergency_stop_ready",
  ].filter(Boolean);
  const visualReady = materialClaimReady(materialSummary.external_video) || materialClaimReady(materialSummary.camera_visible);
  const basicReady = basicMissing.length === 0;
  return {
    status: basicReady ? "ready_for_first_jog" : "blocked_missing_basic_safety",
    basic_safety_ready: basicReady,
    visual_material_ready: visualReady,
    missing_fields: basicMissing,
    next_action: basicReady ? "press_try_move" : "complete_basic_safety_check",
  };
}

function currentBaseFeedbackReadState(payload: JsonRecord | null): { status: string; reason: string } {
  // 当前底盘反馈状态可能来自 /api/base/status，也可能嵌在 /api/status.base；两个来源都只读，不代表运动。
  const currentFeedbackReadback = asRecord(findFirstKey(payload, ["feedback_readback"]));
  const currentSerialRead = asRecord(currentFeedbackReadback?.serial_read);
  const currentSerialError = asRecord(currentSerialRead?.error);
  const currentFeedbackAck = asRecord(findFirstKey(payload, ["feedback_ack"]));
  const currentT1001Observed = currentFeedbackAck?.t1001_observed;
  if (currentSerialRead?.ok === false) {
    return {
      status: "read_error",
      reason: compactValueText(currentSerialError?.message ?? currentSerialError?.type ?? "serial_read_failed", 220),
    };
  }
  if (currentT1001Observed === false) {
    return {
      status: "t1001_not_observed",
      reason: compactValueText(currentFeedbackAck?.reason ?? "T=1001 not observed after current T=130 request", 220),
    };
  }
  if (currentT1001Observed === true) {
    return { status: "t1001_observed", reason: "" };
  }
  return { status: "not_loaded", reason: "" };
}

function mergeCurrentBaseFeedbackReadStates(
  states: Array<{ status: string; reason: string }>,
): { status: string; reason: string } {
  // 多个 fresh readback 有冲突时按更保守的口径显示，避免较好的端点盖住另一个端点的当前错误。
  const order = new Map([
    ["read_error", 0],
    ["t1001_not_observed", 1],
    ["t1001_observed", 2],
    ["not_loaded", 3],
  ]);
  return [...states].sort((left, right) => (order.get(left.status) ?? 9) - (order.get(right.status) ?? 9))[0]
    ?? { status: "not_loaded", reason: "" };
}

function baseSummaryFromReadbacks(readbacks: InternalRobotApiEndpointReadback[]): RobotControlSummaryResponse["readback_summary"]["base"] {
  // T=1001 只说明 WAVE ROVER feedback 链路有回包，不代表轮速非零、真实运动或 HIL pass。
  const baseStatus = pickReadback(readbacks, "base_status");
  const feedbackLatest = pickReadback(readbacks, "base_feedback_samples_latest");
  const basePayload = readbackById(readbacks, "base_status")?.payload ?? null;
  const statusPayload = readbackById(readbacks, "status")?.payload ?? null;
  const currentFeedbackState = mergeCurrentBaseFeedbackReadStates([
    currentBaseFeedbackReadState(asRecord(basePayload)),
    currentBaseFeedbackReadState(asRecord(findFirstKey(statusPayload, ["base"]))),
  ]);
  const currentFeedbackReadStatus = currentFeedbackState.status;
  const currentFeedbackFailureReason = currentFeedbackState.reason;
  const statusT1001 = baseStatus?.key_values.latest_t1001_observed_count;
  const latestT1001 = feedbackLatest?.key_values.latest_t1001_observed_count ?? feedbackLatest?.key_values.t1001_observed_count;
  const observedCount = statusT1001 ?? latestT1001 ?? "not_loaded";
  const baseStatusHasFreshT1001 = statusT1001 !== undefined && statusT1001 !== "not_loaded" && Number(statusT1001) > 0;
  const latestFeedbackStatus = currentFeedbackReadStatus === "read_error"
    ? "current_read_error"
    : currentFeedbackReadStatus === "t1001_not_observed"
      ? "current_t1001_not_observed"
      : baseStatusHasFreshT1001
    ? "fresh_base_status_readback"
    : feedbackLatest?.key_values.feedback_samples_freshness_status
      ?? baseStatus?.key_values.feedback_samples_freshness_status
      ?? feedbackLatest?.status
      ?? "not_loaded";
  const ackStatus = currentFeedbackReadStatus === "t1001_observed"
    ? "t1001_observed"
    : currentFeedbackReadStatus === "t1001_not_observed"
      ? "t1001_not_observed"
      : currentFeedbackReadStatus === "read_error"
        ? "read_error"
        : baseStatus?.key_values.feedback_ack_status ?? (Number(observedCount) > 0 ? "t1001_observed" : "not_loaded");
  const wheelFeedbackProven = baseStatus?.key_values.wheel_feedback_lr_nonzero_proven
    ?? feedbackLatest?.key_values.wheel_feedback_lr_nonzero_proven
    ?? "not_loaded";
  const wheelFeedbackObserved = baseStatus?.key_values.wheel_feedback_nonzero_observed
    ?? feedbackLatest?.key_values.wheel_feedback_nonzero_observed
    ?? "not_loaded";
  const latestLeft = baseStatus?.key_values.wheel_feedback_latest_left_speed
    ?? baseStatus?.key_values.wheel_feedback_latest_raw_left
    ?? feedbackLatest?.key_values.wheel_feedback_latest_left_speed
    ?? feedbackLatest?.key_values.wheel_feedback_latest_raw_left
    ?? feedbackLatest?.key_values.left_speed
    ?? "not_loaded";
  const latestRight = baseStatus?.key_values.wheel_feedback_latest_right_speed
    ?? baseStatus?.key_values.wheel_feedback_latest_raw_right
    ?? feedbackLatest?.key_values.wheel_feedback_latest_right_speed
    ?? feedbackLatest?.key_values.wheel_feedback_latest_raw_right
    ?? feedbackLatest?.key_values.right_speed
    ?? "not_loaded";
  const latestNonzeroLeft = baseStatus?.key_values.wheel_feedback_latest_nonzero_left_speed
    ?? feedbackLatest?.key_values.wheel_feedback_latest_nonzero_left_speed
    ?? "not_loaded";
  const latestNonzeroRight = baseStatus?.key_values.wheel_feedback_latest_nonzero_right_speed
    ?? feedbackLatest?.key_values.wheel_feedback_latest_nonzero_right_speed
    ?? "not_loaded";
  const feedbackVoltage = baseStatus?.key_values.feedback_voltage_v
    ?? feedbackLatest?.key_values.feedback_voltage_v
    ?? "not_loaded";
  return {
    status: baseStatus?.status ?? "not_loaded",
    latest_feedback_status: latestFeedbackStatus,
    current_feedback_read_status: currentFeedbackReadStatus,
    current_feedback_failure_reason: currentFeedbackFailureReason || "not_loaded",
    feedback_ack_status: ackStatus,
    latest_t1001_observed_count: observedCount,
    wheel_feedback_lr_nonzero_proven: wheelFeedbackProven,
    wheel_feedback_nonzero_observed: wheelFeedbackObserved,
    wheel_feedback_latest_left_speed: latestLeft,
    wheel_feedback_latest_right_speed: latestRight,
    wheel_left_speed: latestLeft,
    wheel_right_speed: latestRight,
    wheel_feedback_latest_raw_left: latestLeft,
    wheel_feedback_latest_raw_right: latestRight,
    wheel_raw_left: latestLeft,
    wheel_raw_right: latestRight,
    wheel_feedback_latest_nonzero_left_speed: latestNonzeroLeft,
    wheel_feedback_latest_nonzero_right_speed: latestNonzeroRight,
    feedback_voltage_v: feedbackVoltage,
    feedback_link_status: currentFeedbackReadStatus === "read_error"
      ? "current_t130_read_error"
      : currentFeedbackReadStatus === "t1001_not_observed"
        ? "current_t130_no_t1001"
        : wheelFeedbackProven === "true" || wheelFeedbackObserved === "true"
      ? "t1001_lr_nonzero_material_observed_not_hil"
      : Number(observedCount) > 0 ? "t1001_observed_not_motion_proof" : "not_observed",
  };
}

function keyboardSummaryReadback(): RobotControlSummaryResponse["readback_summary"]["keyboard"] {
  // 键盘连续手控对脚本也应是一块直接可读事实；这里不代表已启用，也不发送任何脉冲。
  const readinessPlain = "可启用键盘；启用本身不发车，按住方向键/WASD 才连续低速移动。";
  const holdToMovePlain = "必须按住 W/A/S/D 或方向键才会连续低速移动；只启用键盘但不按方向不会发车。";
  const plainHint = "可启用键盘；启用本身不发车，必须按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页/换方向或点停止都会停。";
  return {
    status: "start_ready",
    control_mode: "bounded_repeating_manual_pulse",
    manual_command_mode: "ros",
    manual_proxy_endpoint: "/api/robot-control/base/manual",
    stop_proxy_endpoint: "/api/robot-control/base/stop",
    start_ready: "true",
    enabled: "false",
    plain_hint: plainHint,
    readiness_plain: readinessPlain,
    continuous_control_contract_plain: `按住时约每 ${ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS / 1000} 秒发送一次 ${ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS / 1000} 秒 ROS 低速脉冲；松开、失焦、切页、换方向或点击停止都会停。`,
    hold_to_move_plain: holdToMovePlain,
    stop_triggers_plain: "松开按键、窗口失焦、页面隐藏、切换方向或点击停止都会发送停止请求。",
    pulse_timing_plain: `按住时约每 ${ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS / 1000} 秒发送一次 ${ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS / 1000} 秒低速脉冲。`,
    next_action_plain: "勾选现场安全确认后点击启用键盘；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停。",
    minimal_precheck_plain: "键盘连续手控只复用现场安全确认；启用键盘不发车，只有按住方向键/WASD 才发送低速短脉冲。",
    robot_control_executed: "false",
  };
}

function plainFactPart(value: string | undefined, fallback = ""): string {
  // 顶层当前事实只拼后端已验证的只读短句；空值和 not_loaded 不进入汇总，避免误导现场。
  const text = asString(value, fallback).trim();
  if (!text || text === "not_loaded" || text === "none") {
    return "";
  }
  return text.replace(/[。.!?]+$/, "");
}

function currentFactMapRadarParts(
  mapStatus: string,
  radarStatus: string,
): { map: string; radar: string } {
  // 地图主句如果已经用分号追加了雷达诊断，顶层事实改由 radar overlay 专门说明，避免旧来源点和当前 marker 重复出现。
  const map = plainFactPart(mapStatus);
  const radar = plainFactPart(radarStatus);
  if (!map || !radar) {
    return { map, radar };
  }
  if (map.includes("；雷达")) {
    return { map: map.split("；雷达")[0] ?? map, radar };
  }
  if (map.includes("雷达标记都已按当前读数显示")) {
    return { map, radar: "" };
  }
  return { map, radar };
}

function summaryCurrentFactPlain(
  readback: RobotControlSummaryResponse["readback_summary"],
  boundary: RobotControlSummaryResponse["safe_command_boundary"],
): string {
  // 这是给脚本和外部面板的一句话事实；Vue 仍保留本地 pending 态的更细实时文案。
  const camera = plainFactPart(readback.camera.camera_wysiwyg_status_plain);
  const { map, radar } = currentFactMapRadarParts(
    readback.map.map_wysiwyg_status_plain,
    readback.map.radar_overlay_wysiwyg_status_plain,
  );
  const nav2 = plainFactPart(readback.nav2.execution_status_plain || readback.nav2.route_execution_readiness_plain);
  const keyboard = plainFactPart(readback.keyboard.hold_to_move_plain || readback.keyboard.readiness_plain);
  const freeMove = plainFactPart(readback.free_roam.motion_readiness_plain);
  const mapping = plainFactPart(readback.free_roam.mapping_readiness_plain);
  const minimal = plainFactPart(boundary.nav2_goal_minimal_precheck_plain);
  const parts = [
    camera,
    map,
    radar,
    nav2 ? `自动驾驶：${nav2}` : "",
    keyboard ? `键盘：${keyboard}` : "",
    freeMove ? `自由移动：${freeMove}` : "",
    mapping ? `建图：${mapping}` : "",
    minimal ? `发车前：${minimal}` : "",
  ].filter(Boolean);
  return parts.length > 0
    ? `${parts.join("；")}。`
    : "当前事实未读到；先确认小车地址和上位机 Robot API。";
}

export async function buildRobotControlSummary(
  baseUrl: string,
  firstFrameProbeOverlay: RobotControlCameraFirstFrameProbeOverlay | null = null,
  mjpegRelayOverlay: RobotControlCameraMjpegRelayOverlay | null = null,
  options: RobotControlSummaryBuildOptions = {},
): Promise<RobotControlSummaryResponse> {
  // 这是 PC Robot Control Console V1 的唯一 Robot API 入口；浏览器永远不直连上位机。
  const normalized = normalizeRobotApiBaseUrl(baseUrl);
  if (!normalized.ok) {
    return failClosed(normalized.reason, baseUrl);
  }

  const observedAt = Date.now();
  const readbacks = await Promise.all(
    READ_ENDPOINTS.map((item) => readEndpoint(normalized.normalized, item, options.readbackTimeoutMs)),
  );
  const readEndpoints: RobotApiEndpointReadback[] = readbacks.map((item) => ({
    // summary 对外只暴露压缩 readback；完整 payload 只在本函数内用于现场材料摘要。
    id: item.id,
    endpoint: item.endpoint,
    http_status: item.http_status,
    request_status: item.request_status,
    schema: item.schema,
    status: item.status,
    evidence_ref: item.evidence_ref,
    key_values: item.key_values,
    blocked_reasons: item.blocked_reasons,
    dangerous_true_fields: item.dangerous_true_fields,
  }));
  const dangerous = readbacks.flatMap((item) => item.dangerous_true_fields.map((field) => `${item.id}.${field}`));
  const loadedCount = readbacks.filter((item) => item.request_status === "loaded").length;
  const failedCount = readbacks.filter((item) => item.request_status === "fetch_failed" || item.request_status === "bad_json" || item.request_status === "not_object").length;
  const blockedCount = readbacks.filter((item) => item.request_status === "blocked").length;
  const schemaMismatchCount = readbacks.filter(isRobotReadbackSchemaMismatch).length;
  const blockedReasons = [
    ...readbacks.flatMap((item) => item.blocked_reasons.map((reason) => `${item.id}:${reason}`)),
    ...dangerous.map((field) => `dangerous_true_field:${field}`),
  ];
  const hardBlockedReasons = [
    ...readbacks
      .filter((item) => item.request_status === "blocked")
      .flatMap((item) => item.blocked_reasons.map((reason) => `${item.id}:${reason}`)),
    ...dangerous.map((field) => `dangerous_true_field:${field}`),
  ];
  const proofSummary = buildProofSummary(readbacks);
  const operatorHilMaterialSummary = buildOperatorHilMaterialSummary(readbacks);
  const freeRoamRuntimeGates = freeRoamRuntimeGatesFromReadbacks(readbacks);
  const freeRoamRuntime = freeRoamRuntimeSummaryFromReadbacks(readbacks);
  const nav2Summary = nav2SummaryFromReadbacks(readbacks, proofSummary);
  const lidarSummary = lidarSummaryFromReadbacks(readbacks, proofSummary);
  const readbackSummary: RobotControlSummaryResponse["readback_summary"] = {
    camera: cameraSummaryFromReadbacks(readbacks, firstFrameProbeOverlay, mjpegRelayOverlay),
    lidar: lidarSummary,
    base: baseSummaryFromReadbacks(readbacks),
    map: mapSummaryFromReadbacks(readbacks, proofSummary, lidarSummary),
    localization: localizationSummaryFromReadbacks(readbacks, proofSummary),
    nav2: nav2Summary,
    keyboard: keyboardSummaryReadback(),
    free_roam: freeRoamSummaryFromReadbacks(readbacks, freeRoamRuntimeGates, freeRoamRuntime),
  };
  const safeCommandBoundary = lockedBoundary(freeRoamRuntimeGates, freeRoamRuntime, proofSummary, nav2Summary);

  return {
    schema: ROBOT_CONTROL_SCHEMA,
    console_status: hardBlockedReasons.length ? "blocked" : "loaded_fail_closed_summary",
    source_base_url: baseUrl,
    normalized_base_url: normalized.normalized.toString().replace(/\/$/, ""),
    proxy_policy: {
      vue_direct_robot_api_access: false,
      node_proxy_only: true,
      allowed_methods: ["GET", "POST"],
      allowed_endpoint_class: "status_latest_readback_plus_fixed_control_and_report_proxies",
      unsafe_urls_rejected: true,
    },
    observed_at_ms: observedAt,
    read_endpoints: readEndpoints,
    o3_proof_summary: proofSummary,
    robot_api_connection: {
      status: dangerous.length || blockedCount > 0 ? "blocked" : failedCount > 0 ? "degraded" : "readable",
      loaded_count: loadedCount,
      blocked_count: blockedCount,
      failed_count: failedCount,
      schema_mismatch_count: schemaMismatchCount,
      dangerous_true_fields: dangerous,
      blocked_reasons: blockedReasons,
      last_refresh_ms: observedAt,
    },
    current_fact_plain: summaryCurrentFactPlain(readbackSummary, safeCommandBoundary),
    readback_summary: readbackSummary,
    operator_hil_material_summary: operatorHilMaterialSummary,
    first_jog_readiness_summary: buildFirstJogReadinessSummary(operatorHilMaterialSummary),
    safe_command_boundary: safeCommandBoundary,
    blocked_reasons: blockedReasons.length ? blockedReasons : ["dangerous actions locked by V1 boundary"],
    not_proven: ["O7", "path_generated", "delivery_success", "safe_to_control_true", "real_robot_ack"],
    ...PROOF_FLAGS,
  };
}
