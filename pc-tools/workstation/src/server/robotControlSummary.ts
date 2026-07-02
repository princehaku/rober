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
  RobotControlGoalChecklistSummary,
  RobotControlFieldAcceptancePacket,
  RobotControlFieldAcceptanceNoMotionReadbackAction,
  RobotControlFieldAcceptanceNoMotionReadbackActionId,
  RobotControlFieldAcceptanceSafetyConfirmReadyAction,
  RobotControlFieldAcceptanceHardwareAction,
  RobotControlFieldAcceptanceMissingEvidenceItem,
  RobotControlFieldAcceptanceWysiwygRefreshMode,
  RobotControlLiveClosureSummary,
  RobotControlLiveObjectiveAuditItem,
  RobotControlNav2RouteAcceptancePacket,
  RobotControlLiveWysiwygSurfaceSummary,
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

function fieldAcceptanceWysiwygRefreshMode(
  missingSurfaceIds: string[],
): RobotControlFieldAcceptanceWysiwygRefreshMode {
  // 现场 curl 和 PC 按钮必须共享同一套最小刷新口径，避免“只差相机”时误触雷达/地图刷新。
  if (missingSurfaceIds.length === 1 && missingSurfaceIds[0] === "camera") {
    return "camera_only";
  }
  if (missingSurfaceIds.length === 1 && missingSurfaceIds[0] === "radar_map_points") {
    return "radar_map_only";
  }
  if (missingSurfaceIds.length === 1 && missingSurfaceIds[0] === "map") {
    return "map_only";
  }
  return missingSurfaceIds.length > 0 ? "all_wysiwyg" : "none";
}

function fieldAcceptanceFocusedWysiwygRefreshPlan(mode: RobotControlFieldAcceptanceWysiwygRefreshMode): {
  sequence: string[];
  labels: string[];
} {
  // 这个 plan 只描述现场验收按钮的最小只读链路；真正发车动作由 motion runbook 另行门禁。
  if (mode === "camera_only") {
    return {
      sequence: [
        "/api/robot-control/camera/first-frame/probe",
        "/api/robot-control/camera/mjpeg/status",
        "/api/robot-control/summary",
      ],
      labels: ["复测相机首帧", "读取相机 MJPEG 状态", "刷新总览"],
    };
  }
  if (mode === "radar_map_only") {
    return {
      sequence: [
        "/api/robot-control/radar/scan-proof/refresh",
        "/api/robot-control/radar/status",
        "/api/robot-control/map/preview",
      ],
      labels: ["刷新雷达扫描读数", "读取雷达状态", "刷新地图画面"],
    };
  }
  if (mode === "map_only") {
    return {
      sequence: [
        "/api/robot-control/map/preview",
        "/api/robot-control/radar/status",
        "/api/robot-control/summary",
      ],
      labels: ["刷新地图画面", "读取雷达状态", "刷新总览"],
    };
  }
  if (mode === "none") {
    return { sequence: [], labels: [] };
  }
  return {
    sequence: [
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/camera/first-frame/probe",
      "/api/robot-control/camera/mjpeg/status",
      "/api/robot-control/summary",
    ],
    labels: ["刷新雷达扫描读数", "读取雷达状态", "刷新地图画面", "复测相机首帧", "读取相机 MJPEG 状态", "刷新总览"],
  };
}

function fieldAcceptanceNoMotionReadbackMethod(endpoint: string): RobotControlFieldAcceptanceNoMotionReadbackAction["method"] {
  return endpoint.includes("/refresh") || endpoint.includes("/probe") || endpoint.includes("/feedback-samples") ? "POST" : "GET";
}

function fieldAcceptanceMissingEvidenceLabel(id: string): string {
  // 缺失证据清单是给现场照着做的，保留稳定 id 的同时给出普通用户能理解的中文标签。
  const labels: Record<string, string> = {
    route_ready_on_map: "图上行程已显示",
    nav2_goal_succeeded: "Nav2 到点成功",
    same_window_wheel_lr_nonzero: "同窗口 wheel L/R 非零",
    delivery_success: "送达确认",
    same_hold_window_wheel_lr_nonzero: "按住同窗口 wheel L/R 非零",
    stop_after_release: "松开/失焦后 stop 已落稳",
    free_roam_latest_motion_ready: "自由移动运行读数",
    camera_first_frame: "相机首帧",
    lidar_fresh: "雷达新鲜读数",
    mapping_active: "建图已启动",
    fresh_map_preview: "地图画面已刷新",
  };
  return labels[id] ?? id.replace(/_/g, " ");
}

function fieldAcceptanceMissingEvidenceReadbackEndpoint(id: string, fallbackEndpoints: string[]): string {
  // 每个证据优先落到最直接的只读读回；fallback 保留 runbook 原验收端点，便于后续扩展新证据。
  const endpointById: Record<string, string> = {
    route_ready_on_map: "/api/robot-control/map/preview",
    nav2_goal_succeeded: "/api/robot-control/nav2/goal/execution/latest",
    same_window_wheel_lr_nonzero: "/api/robot-control/base/feedback-samples",
    delivery_success: "/api/robot-control/delivery/latest",
    same_hold_window_wheel_lr_nonzero: "/api/robot-control/base/feedback-samples",
    stop_after_release: "/api/robot-control/base/feedback-samples",
    free_roam_latest_motion_ready: "/api/robot-control/free-roam/autonomy/latest",
    camera_first_frame: "/api/robot-control/camera/first-frame/probe",
    lidar_fresh: "/api/robot-control/radar/scan-proof/refresh",
    mapping_active: "/api/robot-control/map/preview",
    fresh_map_preview: "/api/robot-control/map/preview",
  };
  return endpointById[id] ?? fallbackEndpoints[0] ?? "/api/robot-control/summary";
}

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
export const NAV2_GOAL_PREFLIGHT_BLOCKING_REQUIREMENTS = [
  "confirm_navigation_preflight",
  "goal_limits",
  "hard_dangerous_true_fields",
] as const;
export const NAV2_GOAL_PREFLIGHT_OPERATOR_PRECHECK_REQUIREMENTS = ["confirm_navigation_preflight"] as const;
export const NAV2_GOAL_PREFLIGHT_PROXY_GUARD_REQUIREMENTS = ["goal_limits", "hard_dangerous_true_fields"] as const;
export const NAV2_GOAL_EXECUTION_BLOCKING_REQUIREMENTS = [
  "confirm_navigation_execution",
  "goal_limits",
  "hard_dangerous_true_fields",
] as const;
export const NAV2_GOAL_EXECUTION_OPERATOR_PRECHECK_REQUIREMENTS = ["confirm_navigation_execution"] as const;
export const NAV2_GOAL_EXECUTION_PROXY_GUARD_REQUIREMENTS = ["goal_limits", "hard_dangerous_true_fields"] as const;
export const NAV2_GOAL_MINIMAL_PRECHECK_PLAIN = "执行图上路线只要求现场安全确认；目标白名单和危险 true 字段属于固定代理安全护栏，不是普通用户额外预检；相机、雷达、现场报告、路线读回、定位读回和自动驾驶状态只做显示或复验。";
const ROBOT_CONTROL_SCAN_PREVIEW_POINT_LIMIT = 72;
const ROBOT_CONTROL_SCAN_PREVIEW_MIN_RANGE_M = 0.03;
const ROBOT_CONTROL_SCAN_PREVIEW_MAX_RANGE_M = 8;
const FREE_ROAM_MAPPING_START_REQUIRED_IDS = ["camera_first_frame", "lidar_fresh"] as const;
const FREE_ROAM_MAPPING_ACCEPTANCE_REQUIRED_IDS = ["camera_first_frame", "lidar_fresh", "mapping_active", "fresh_map_preview"] as const;
export const ROBOT_CONTROL_ALLOWED_MANUAL_DIRECTIONS = ["forward", "back", "left", "right", "stop"] as const;
export const ROBOT_CONTROL_HIL_CHECKLIST = [
  { id: "operator_safety_confirmed", label: "现场安全确认（人在旁边、周围安全、停止手段就绪）" },
] as const;

type RobotReadEndpointConfig = {
  id: RobotApiReadEndpointId;
  endpoint: string;
  timeout_ms: number;
  summary_timeout_ms?: number;
};

const READ_ENDPOINTS: RobotReadEndpointConfig[] = [
  // `/api/health` 是上车轻量活性探针，不聚合硬件状态；先读它可区分 API 活着和重状态端点退化。
  { id: "health", endpoint: "/api/health", timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS, summary_timeout_ms: DEFAULT_REQUEST_TIMEOUT_MS },
  // 真实上位机 /api/status 会顺带聚合 camera/radar/base 子摘要，读取窗口要比 proof latest 更宽。
  { id: "status", endpoint: "/api/status", timeout_ms: HEAVY_READBACK_TIMEOUT_MS, summary_timeout_ms: ROBOT_CONTROL_SUMMARY_HTTP_READBACK_TIMEOUT_MS },
  { id: "map_proof_latest", endpoint: "/api/map/proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  // map preview 是当前 PC 地图画面同源证据；summary 只消费其中 overlay 摘要，不发送任何运动或建图命令。
  { id: "map_preview", endpoint: "/api/map/preview", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "localize_proof_latest", endpoint: "/api/localize/proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "nav2_status", endpoint: "/api/nav2/status", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "nav2_proof_latest", endpoint: "/api/nav2/proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "nav2_goal_execution_latest", endpoint: "/api/nav2/goal/execution/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "operator_report_latest", endpoint: "/api/operator/report", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "free_roam_autonomy_latest", endpoint: "/api/free-roam/autonomy/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  // camera 端点在真实板端会探测设备与健康摘要，允许更长只读窗口，避免误判成离线。
  { id: "camera_health", endpoint: "/api/camera/health", timeout_ms: HEAVY_READBACK_TIMEOUT_MS, summary_timeout_ms: ROBOT_CONTROL_SUMMARY_HTTP_READBACK_TIMEOUT_MS },
  { id: "camera_devices", endpoint: "/api/camera/devices", timeout_ms: HEAVY_READBACK_TIMEOUT_MS, summary_timeout_ms: ROBOT_CONTROL_SUMMARY_HTTP_READBACK_TIMEOUT_MS },
  { id: "radar_status", endpoint: "/api/radar/status", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "radar_scan_proof_latest", endpoint: "/api/radar/scan-proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  { id: "radar_raw_packet_proof_latest", endpoint: "/api/radar/raw-packet-proof/latest", timeout_ms: SLOW_READBACK_TIMEOUT_MS },
  // latest samples 只读 bridge 已落盘反馈，不发送控制；现场常要 5-6 秒才回，给 wheel L/R 验收留足窗口。
  { id: "base_feedback_samples_latest", endpoint: "/api/base/feedback-samples/latest", timeout_ms: HEAVY_READBACK_TIMEOUT_MS, summary_timeout_ms: HEAVY_READBACK_TIMEOUT_MS },
  // fresh base/status 可能触发当前底盘反馈读数，首屏仍短预算，避免慢串口窗口拖住普通页面。
  { id: "base_status", endpoint: "/api/base/status", timeout_ms: HEAVY_READBACK_TIMEOUT_MS, summary_timeout_ms: ROBOT_CONTROL_SUMMARY_HTTP_READBACK_TIMEOUT_MS },
];

const OPTIONAL_MISSING_READ_ENDPOINT_IDS: ReadonlySet<RobotApiReadEndpointId> = new Set([
  "radar_scan_proof_latest",
  "radar_raw_packet_proof_latest",
  "free_roam_autonomy_latest",
  "nav2_goal_execution_latest",
  "map_preview",
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
const SUMMARY_SERIAL_READ_ENDPOINT_IDS: ReadonlySet<RobotApiReadEndpointId> = new Set([
  "status",
]);
const ALLOWED_ROBOT_READBACK_SCHEMA_PREFIXES = [
  "trashbot.upper_robot_api.v1",
  "trashbot.local_webrtc_camera_",
] as const;
const NAV2_GOAL_BLOCKER_ORDER = [
  "robot_api_nav2_read_failed",
  "robot_api_map_localize_read_failed",
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
      next_action: "画面未就绪时仍可自由移动，但不能按建图验收",
    },
    {
      id: "lidar_fresh",
      label: "雷达监看",
      scope: "mapping_acceptance",
      state: "not_proven",
      evidence: "未读到 fresh 雷达扫描",
      next_action: "雷达未就绪时仍可自由移动，但不能按建图验收",
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

const PROOF_REFRESH_NO_MOTION_FLAGS = {
  // proof refresh POST 只刷新证据，不允许被现场脚本误当成运动或 runtime 开关。
  readback_only: true,
  no_motion_refresh: true,
  sends_motion_when_clicked: false,
  starts_radar_lifecycle: false,
  starts_nav2: false,
  starts_manual: false,
  starts_keyboard: false,
  starts_free_roam: false,
  starts_map_runtime: false,
  submits_delivery: false,
  stops_motion: false,
} satisfies Pick<
  RobotControlProofRefreshProxyResponse,
  | "readback_only"
  | "no_motion_refresh"
  | "sends_motion_when_clicked"
  | "starts_radar_lifecycle"
  | "starts_nav2"
  | "starts_manual"
  | "starts_keyboard"
  | "starts_free_roam"
  | "starts_map_runtime"
  | "submits_delivery"
  | "stops_motion"
>;

const MAP_PREVIEW_READBACK_ONLY_FLAGS = {
  // 地图 preview 是 GET 读回；它可以刷新画面证据，但不能启动雷达、Nav2、建图或底盘运动。
  readback_only: true,
  map_preview_readback_only: true,
  no_motion_refresh: true,
  sends_motion_when_clicked: false,
  starts_radar_lifecycle: false,
  starts_nav2: false,
  starts_manual: false,
  starts_keyboard: false,
  starts_free_roam: false,
  starts_map_runtime: false,
  submits_delivery: false,
  stops_motion: false,
} satisfies Pick<
  RobotControlMapPreviewResponse,
  | "readback_only"
  | "map_preview_readback_only"
  | "no_motion_refresh"
  | "sends_motion_when_clicked"
  | "starts_radar_lifecycle"
  | "starts_nav2"
  | "starts_manual"
  | "starts_keyboard"
  | "starts_free_roam"
  | "starts_map_runtime"
  | "submits_delivery"
  | "stops_motion"
>;

const RADAR_SCAN_PROOF_REFRESH_CONFIG: RobotProofRefreshConfig = {
  kind: "radar_scan_proof_refresh",
  endpoint: "/api/radar/scan-proof/refresh",
  request_body: {
    // 雷达启动归 `/radar/start` 管；proof refresh 只读已有 topic，避免无 runtime command 时把成功扫描误判 blocked。
    timeout_s: 12,
  },
  timeout_cap_ms: 120_000,
  safety_margin_ms: 78_000,
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
const RADAR_SCAN_PROOF_LATEST_ENDPOINT = "/api/radar/scan-proof/latest" as const;
// 真实上车 refresh 成功后，scan proof artifact 可能晚于 HTTP 回包落盘；多等一轮避免按钮误报 stale。
const RADAR_SCAN_PROOF_POST_REFRESH_READBACK_DELAYS_MS = [0, 250, 750, 1500] as const;
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
  "base_command_mode",
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

function robotApiPortDriftReason(base: URL): string {
  // 现场 PC Node 固定跑在 7001，小车上位机 Robot API 固定跑在 8787；7071 常被 Clash 占用或根本无服务。
  const port = base.port || (base.protocol === "http:" ? "80" : "");
  if (base.hostname === "192.168.1.11" && port === "7001") {
    return "robot_api_port_7001_mismatch_use_8787";
  }
  if (base.hostname === "192.168.1.11" && port === "7071") {
    return "robot_api_port_7071_mismatch_use_8787";
  }
  return "";
}

function robotApiPortDriftPlain(reason: string): string {
  // 这句必须出现在普通首屏和脚本读数里，避免把端口写错误判成 Nav2、摄像头或雷达坏了。
  if (reason === "robot_api_port_7001_mismatch_use_8787") {
    return "小车地址端口写错：7001 是 PC 页面服务端口，小车上位机 Robot API 是 192.168.1.11:8787；不要把 Robot API 填成 7001";
  }
  if (reason === "robot_api_port_7071_mismatch_use_8787") {
    return "小车地址端口写错：PC 页面是 0.0.0.0:7001，小车上位机 Robot API 是 192.168.1.11:8787；不要把 Robot API 填成 7071";
  }
  return "";
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
    required_fields: [],
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
    if (reason === "robot_api_nav2_read_failed") {
      return "自动驾驶状态读取失败";
    }
    if (reason === "robot_api_map_localize_read_failed") {
      return "地图/定位读取失败";
    }
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
      return "定位未就绪，无法生成图上路线";
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
  appendNav2GoalExecutionLifecycleKeyValues(payload, result, keys);
  return result;
}

function robotReadbackUnavailable(readback: InternalRobotApiEndpointReadback | null | undefined): boolean {
  // 只读端点读不到时不能继续把问题说成“还没生成路线”；普通用户需要先处理地址/API 可读性。
  return ["fetch_failed", "bad_json", "not_object", "blocked"].includes(readback?.request_status ?? "");
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

function lifecycleStateIsActive(value: unknown): boolean | null {
  // Nav2 lifecycle 文本常是 "active [3] (...)"；不能用 includes("active")，否则 inactive 会误判。
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    return null;
  }
  if (/^active\b/.test(normalized)) {
    return true;
  }
  if (/^(inactive|unconfigured|finalized|waiting|not_observed|not_loaded)\b/.test(normalized)) {
    return false;
  }
  return null;
}

function appendNav2GoalExecutionLifecycleKeyValues(payload: JsonRecord | null, result: Record<string, string>, keys: readonly string[]): void {
  // O11 是完整 NavigateToPose 执行证据；它的 managed runtime 比 O10 planner-only proof 更适合回答 controller 是否已请求。
  const latestResult = asRecord(payload?.latest_result);
  const runtime = asRecord(latestResult?.managed_runtime) ?? asRecord(payload?.managed_runtime);
  const lifecycleReady = asRecord(runtime?.lifecycle_ready);
  const states = asRecord(lifecycleReady?.states);
  const requested = runtime?.requested === true || runtime?.requested === "true" || runtime?.started === true || runtime?.started === "true";
  const lifecycleAllActive = lifecycleReady?.ok === true || lifecycleReady?.ok === "true";
  const fill = (key: string, value: unknown): void => {
    if (!keys.includes(key) || result[key] !== undefined || value === undefined || value === null) {
      return;
    }
    result[key] = compactValueText(value);
  };
  const fillService = (service: "planner_server" | "controller_server"): void => {
    const stateActive = lifecycleStateIsActive(states?.[service]);
    fill(`${service}_requested`, requested || states?.[service] !== undefined ? "true" : undefined);
    if (lifecycleAllActive) {
      fill(`${service}_active`, "true");
      return;
    }
    if (stateActive !== null) {
      fill(`${service}_active`, String(stateActive));
    }
  };
  fillService("planner_server");
  fillService("controller_server");
}

function cameraFormatAttemptsSummary(lastOfferError: JsonRecord | null): string {
  // 相机首帧失败时，把上车端逐格式尝试压成短文本，普通首屏不用展开 raw JSON 也能看到真实失败范围。
  const attempts = Array.isArray(lastOfferError?.first_frame_format_attempts)
    ? lastOfferError.first_frame_format_attempts
    : Array.isArray(lastOfferError?.last_first_frame_format_attempts)
      ? lastOfferError.last_first_frame_format_attempts
    : [];
  const parts = attempts
    .map((item) => asRecord(item))
    .filter((item): item is JsonRecord => item !== null)
    .map((attempt) => {
      const fourcc = asString(attempt.label ?? attempt.fourcc, "unknown");
      const openSource = asString(attempt.open_source, "");
      const openBackend = asString(attempt.open_backend, "");
      const openMethod = openSource || openBackend
        ? `(${[openSource, openBackend].filter((item) => item && item !== "default").join("/") || "default"})`
        : "";
      const label = `${fourcc}${openMethod}`;
      const status = asString(attempt.status, "unknown");
      if (status === "frame_read") {
        return `${label} 已出帧`;
      }
      if (status === "open_failed") {
        return `${label} 打不开`;
      }
      if (status === "first_frame_unreadable") {
        return `${label} 无首帧`;
      }
      return `${label} ${status}`;
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

function cameraSourceUsageScope(
  status: unknown,
  ownerCount: unknown,
): "free" | "camera_service_self" | "external_holder" | "unknown" {
  // 共享预览的相机服务 self-owner 是单上游正常形态，不应被普通用户理解成外部独占。
  const usageStatus = asString(status, "");
  const usageOwnerCount = compactValueText(ownerCount ?? "");
  if (usageStatus === "not_in_use" || usageOwnerCount === "0") {
    return "free";
  }
  if (usageStatus === "in_use_by_camera_service" || usageStatus === "camera_service_self") {
    return "camera_service_self";
  }
  if (usageStatus && !["not_loaded", "none", "unknown", "null"].includes(usageStatus)) {
    return "external_holder";
  }
  return "unknown";
}

function cameraSourceUsageNotExclusive(scope: "free" | "camera_service_self" | "external_holder" | "unknown"): string {
  // 继续输出 compact 字符串，保持 readback_summary 现有兼容风格。
  return scope === "free" || scope === "camera_service_self" ? "true" : "false";
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
    const nextActionPlain = cameraPlainTextOrActionPlain(sourceDiagnosis.next_action_plain, nextAction);
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
  const normalized = value.replace(/\s+/g, "_").toLowerCase();
  if (normalized === "check_usb_camera_input_power_or_known_good_uvc") {
    return "检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。";
  }
  if (normalized === "check_usb_cable_port_power_or_known_good_uvc") {
    return "检查 USB 线、接口和摄像头供电，必要时换 known-good UVC 复测；共享预览不是页面独占。";
  }
  if (normalized === "move_camera_to_high_speed_usb_port_or_powered_hub") {
    return "摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。";
  }
  if (normalized === "continue_monitoring_shared_preview") {
    return "继续监看共享实时画面。";
  }
  if (normalized === "open_shared_preview") {
    return "打开共享实时预览；页面会复用同一条上游流。";
  }
  if (normalized === "auto_join_shared_mjpeg_preview") {
    return "打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。";
  }
  if (normalized === "open_shared_preview_when_needed" || normalized === "open_shared_preview_or_run_first_frame_probe") {
    return "需要看画面时打开共享预览，或点只读检查复测首帧。";
  }
  if (normalized === "wait_or_run_first_frame_probe") {
    return "等待首帧，必要时点只读检查复测画面。";
  }
  if (normalized === "inspect_shared_preview_failure_and_retry") {
    return "查看共享预览失败原因后再重试。";
  }
  if (normalized === "check_robot_api_base_url_and_retry") {
    return "确认小车地址可访问后重试共享预览状态。";
  }
  return `${value.replace(/_/g, " ")}。`;
}

function cameraPlainTextOrActionPlain(plainText: string | undefined, action: string): string {
  // 有些 relay/上车路径会把 token 先转成英文空格句；普通用户文案必须再映射回中文。
  const mapped = cameraActionPlainText(action);
  const plain = (plainText ?? "").trim();
  if (!plain || ["not_loaded", "none"].includes(plain)) {
    return mapped;
  }
  const asciiFallback = /^[A-Za-z0-9_ ./-]+。?$/.test(plain);
  return asciiFallback && mapped ? mapped : plain;
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

function cameraSharedPreviewPlainSummary(args: {
  previewStatus: RobotControlSummaryResponse["readback_summary"]["camera"]["preview_status"];
  clientCount: string;
  relayKey: string;
  cachedFrameLoaded: boolean;
  cachedFrameAgeMs: string;
  previewVisiblePlain: string;
}): { accessPlain: string; realtimePlain: string; multiViewerPlain: string } {
  // 共享预览入口和画面可见是两件事：谁都能接入，不代表上游已经吐出可见帧。
  const viewerText = `当前 ${args.clientCount} 个页面观看`;
  const accessPlain = `共享预览不是页面独占；谁打开页面都接入同一条上游流，${viewerText}。`;
  const relayKeyText = args.relayKey && args.relayKey !== "not_loaded" ? "同一小车地址" : "小车地址未生成";
  const multiViewerPlain = `多人实时预览共用单条上游流；谁打开页面都接入同一个共享 relay（${relayKeyText}），${viewerText}，不会因为新页面进入而独占摄像头。`;
  if (args.previewStatus === "streaming" && args.cachedFrameLoaded) {
    const ageText = args.cachedFrameAgeMs === "none" ? "" : `，缓存帧约 ${args.cachedFrameAgeMs}ms 前更新`;
    return {
      accessPlain,
      multiViewerPlain,
      realtimePlain: `实时预览已可见；多个页面复用同一条上游流${ageText}。`,
    };
  }
  if (args.previewStatus === "starting_local_peer" || args.previewStatus === "connecting_offer_posted") {
    return {
      accessPlain,
      multiViewerPlain,
      realtimePlain: "共享预览正在等待首帧；首帧出现前不能把黑框当作画面可见。",
    };
  }
  return {
    accessPlain,
    multiViewerPlain,
    realtimePlain: args.previewVisiblePlain,
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
  const mediaDiagnostics = asRecord(findFirstKey(healthPayload, ["media_diagnostics"]));
  const sourceDiagnosis = asRecord(findFirstKey(healthPayload, ["source_diagnosis"]) ?? mediaDiagnostics?.source_diagnosis);
  const sourceUsage = asRecord(findFirstKey(healthPayload, ["source_usage"]) ?? mediaDiagnostics?.source_usage);
  const selectedPath = asString(
    currentSelection?.selected_path
      ?? summarySelection?.selected_path
      ?? healthPayload?.selected_path
      ?? sourceDiagnosis?.selected_path
      ?? sourceUsage?.device
      ?? healthPayload?.video_source,
    "",
  );
  const selectedName = asString(
    currentSelection?.selected_name
      ?? summarySelection?.selected_name
      ?? healthPayload?.selected_name
      ?? sourceDiagnosis?.selected_name,
    "",
  );
  const selectedFormats = asString(currentSelection?.selected_formats_summary ?? summarySelection?.selected_formats_summary, "");
  const selectedIsUvc = currentSelection?.selected_is_uvc_or_usb ?? summarySelection?.selected_is_uvc_or_usb ?? sourceDiagnosis?.selected_is_uvc_or_usb;
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
  const radarStatus = asRecord(radarStatusEnvelope?.payload) ?? radarStatusEnvelope ?? payload;
  const latestResult = asRecord(payload.latest_result);
  const latestResultProof = asRecord(latestResult?.proof);
  const latestScanProof = asRecord(radarStatus.latest_scan_proof) ?? asRecord(payload.latest_scan_proof) ?? payload;
  const scanProofLatest = asRecord(radarStatus.scan_proof_latest) ?? asRecord(payload.scan_proof_latest) ?? payload;
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
    payload.latest_proof_status,
  ]);
  assignFirst("scan_once_observed", [
    latestScanProof?.scan_once_observed,
    latestResultProof?.scan_once_observed,
    scanProofLatest?.latest_scan_once_observed,
    payload.scan_once_observed,
    payload.latest_scan_once_observed,
  ]);
  assignFirst("scan_hz_observed", [
    latestScanProof?.scan_hz_observed,
    latestResultProof?.scan_hz_observed,
    scanProofLatest?.latest_scan_hz_observed,
    payload.scan_hz_observed,
    payload.latest_scan_hz_observed,
  ]);
  assignFirst("raw_packet_once_observed", [
    latestScanProof?.raw_packet_once_observed,
    latestResultProof?.raw_packet_once_observed,
    scanProofLatest?.latest_raw_packet_once_observed,
    payload.raw_packet_once_observed,
    payload.latest_raw_packet_once_observed,
  ]);
  assignFirst("tf_observed", [
    latestScanProof?.tf_observed,
    latestResultProof?.tf_observed,
    scanProofLatest?.latest_tf_observed,
    payload.tf_observed,
    payload.latest_tf_observed,
  ]);
  // refresh 成功后优先消费最终 radar_status continuity/lifecycle 结论，避免旧 collector blocker 覆盖最终状态。
  assignFirst("continuous_scan_status", [radarStatus.continuous_scan_status, payload.continuous_scan_status]);
  assignFirst("continuous_window_observed", [radarStatus.continuous_window_observed, payload.continuous_window_observed]);
  assignFirst("continuity_window_status", [radarStatus.continuity_window_status, payload.continuity_window_status]);
  assignFirst("lifecycle_running", [radarStatus.lifecycle_running, payload.lifecycle_running]);
  assignFirst("lifecycle_state", [radarStatus.lifecycle_state, payload.lifecycle_state]);
  // latest endpoint 的 proof 结构没有单独 fresh 字段；refresh 后 all_required 为 true 即代表本轮 latest 已可作为当前读数。
  assignFirst("latest_scan_proof_fresh", [
    radarStatus.latest_scan_proof_fresh,
    payload.latest_scan_proof_fresh,
    latestResultProof?.all_required_observations_observed,
  ]);
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
  const scanOnceObserved = readbackKeyValueText(
    radarScanProofReadback,
    ["scan_once_observed", "latest_scan_once_observed"],
    summaryValueText(radarScanProofPayload, ["scan_once_observed", "latest_scan_once_observed"], ""),
  ) || readbackKeyValueText(radarStatusReadback, ["scan_once_observed"], "");
  const scanHzObserved = readbackKeyValueText(
    radarScanProofReadback,
    ["scan_hz_observed", "latest_scan_hz_observed"],
    summaryValueText(radarScanProofPayload, ["scan_hz_observed", "latest_scan_hz_observed"], ""),
  ) || readbackKeyValueText(radarStatusReadback, ["scan_hz_observed"], "");
  const radarControls = asRecord(findFirstKey(radarStatusPayload, ["controls"]));
  const radarStartControl = asRecord(radarControls?.start);
  const radarStartCommand = asRecord(radarStartControl?.command);
  const radarLifecycleRunning = summaryValueText(radarStatusPayload, ["lifecycle_running"]);
  const radarContinuousStatus = summaryValueText(radarStatusPayload, ["continuous_scan_status"]);
  const radarLifecycleState = summaryValueText(radarStatusPayload, ["lifecycle_state"]);
  const latestScanProofFresh = summaryValueText(radarStatusPayload, ["latest_scan_proof_fresh"]);
  const driverDiagnostics = asRecord(radarStatusPayload?.driver_diagnostics_latest);
  const driverDiagnosticsSerial = asRecord(driverDiagnostics?.serial);
  const driverDiagnosticsRuntime = asRecord(driverDiagnostics?.runtime);
  const missingObservations = radarMissingScanObservations(
    radarStatusReadback,
    radarScanProofReadback,
    radarStatusPayload,
    radarScanProofPayload,
  );
  const missingObservationText = missingObservations.length > 0 ? missingObservations.join(",") : "none";
  const radarStopped = radarLifecycleRunning === "false" || radarLifecycleState === "stopped" || radarContinuousStatus === "lifecycle_not_running";
  const radarScanObservationStatus = latestScanProofFresh === "true"
    ? "all_required_observations_observed"
    : missingObservations.length > 0
      ? "missing_required_observations"
      : "latest_scan_not_fresh";
  const radarMapOverlayReadinessStatus = radarStopped
    ? "blocked_radar_lifecycle_not_running"
    : latestScanProofFresh === "true"
      ? "scan_ready_refresh_map_preview"
      : missingObservations.length > 0
        ? "blocked_missing_scan_observations"
        : "blocked_latest_scan_not_fresh";
  const radarMapOverlayNextActionPlain = radarMapOverlayReadinessStatus === "scan_ready_refresh_map_preview"
    ? "雷达扫描材料已就绪；刷新地图画面，确认地图上实际显示的雷达点数。"
    : radarMapOverlayReadinessStatus === "blocked_missing_scan_observations"
      ? `先补齐雷达扫描材料：${radarObservationLabelPlain(missingObservations)}；有新扫描后再刷新地图画面。`
      : radarStopped
        ? "先启动雷达并等待新扫描，再刷新地图画面确认雷达点。"
        : "先刷新雷达扫描读数，确认拿到新扫描后再刷新地图画面。";
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
    scan_once_observed: scanOnceObserved || "not_loaded",
    scan_hz_observed: scanHzObserved || "not_loaded",
    radar_scan_observation_status: radarScanObservationStatus,
    radar_scan_observation_missing_reasons: missingObservationText,
    radar_map_overlay_readiness_status: radarMapOverlayReadinessStatus,
    radar_map_overlay_next_action_plain: radarMapOverlayNextActionPlain,
    continuous_scan_status: radarContinuousStatus,
    lifecycle_running: radarLifecycleRunning,
    lifecycle_state: radarLifecycleState,
    continuous_window_observed: summaryValueText(radarStatusPayload, ["continuous_window_observed"]),
    continuity_window_status: summaryValueText(radarStatusPayload, ["continuity_window_status"]),
    latest_scan_proof_fresh: latestScanProofFresh,
    driver_diagnostics_status: summaryValueText(radarStatusPayload, ["driver_diagnostics_status"], summaryValueText(driverDiagnostics, ["diagnosis_status"])),
    driver_diagnostics_next_action_plain: summaryValueText(radarStatusPayload, ["driver_diagnostics_next_action_plain"], summaryValueText(driverDiagnostics, ["next_action_plain"])),
    driver_serial_bytes_read_total: summaryValueText(driverDiagnosticsSerial, ["bytes_read_total"]),
    driver_serial_packet_count_total: summaryValueText(driverDiagnosticsSerial, ["packet_count_total"]),
    driver_serial_empty_read_count: summaryValueText(driverDiagnosticsSerial, ["empty_read_count"]),
    driver_published_scan_count: summaryValueText(driverDiagnosticsRuntime, ["published_scan_count"]),
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

function radarMissingScanObservations(
  radarStatusReadback: InternalRobotApiEndpointReadback | null,
  radarScanProofReadback: InternalRobotApiEndpointReadback | null,
  radarStatusPayload: JsonRecord | null,
  radarScanProofPayload: JsonRecord | null,
): string[] {
  // 优先使用上车端 blocked reason，避免 PC 只按缺字段猜测雷达 proof 缺口。
  const rawReasons = [
    radarStatusReadback?.key_values.blocked_reasons,
    radarStatusReadback?.key_values.continuity_blocked_reasons,
    radarScanProofReadback?.key_values.blocked_reasons,
    radarStatusPayload?.blocked_reasons,
    radarStatusPayload?.continuity_blocked_reasons,
    radarScanProofPayload?.blocked_reasons,
  ];
  const missing = new Set<string>();
  for (const reason of rawReasons) {
    const text = Array.isArray(reason) ? reason.join(",") : typeof reason === "string" ? reason : reason === undefined ? "" : JSON.stringify(reason);
    for (const match of text.matchAll(/required_observations_missing:([^"\][]+)/g)) {
      for (const item of (match[1] ?? "").split(",")) {
        const normalized = item.trim();
        if (["scan_once", "scan_hz", "raw_packet_once"].includes(normalized)) {
          missing.add(normalized);
        }
      }
    }
  }
  const explicitChecks = [
    ["scan_once_observed", "scan_once"],
    ["latest_scan_once_observed", "scan_once"],
    ["scan_hz_observed", "scan_hz"],
    ["latest_scan_hz_observed", "scan_hz"],
    ["raw_packet_once_observed", "raw_packet_once"],
    ["latest_raw_packet_once_observed", "raw_packet_once"],
  ] as const;
  for (const [key, label] of explicitChecks) {
    const value = radarScanProofReadback?.key_values[key]
      || radarStatusReadback?.key_values[key]
      || summaryValueText(radarScanProofPayload, [key], "")
      || summaryValueText(radarStatusPayload, [key], "");
    if (value === "false") {
      missing.add(label);
    }
  }
  return ["scan_once", "scan_hz", "raw_packet_once"].filter((item) => missing.has(item));
}

function radarObservationLabel(reason: string): string {
  // 原始 reason 继续保留给自动化；普通用户文案只说现场该补什么。
  return ({
    scan_once: "没有读到一帧雷达",
    scan_hz: "雷达频率未确认",
    raw_packet_once: "雷达原始包未确认",
  } as Record<string, string>)[reason] || reason.replace(/_/g, " ");
}

function radarObservationLabelPlain(reasons: string[]): string {
  // 多个缺口用中文顿号连接，避免把 scan_once 这类工程字段露到普通首屏。
  return reasons.map(radarObservationLabel).join("、") || "雷达新扫描未确认";
}

function radarSummaryFromReadbacks(
  lidar: RobotControlSummaryResponse["readback_summary"]["lidar"],
  map: RobotControlSummaryResponse["readback_summary"]["map"],
): RobotControlSummaryResponse["readback_summary"]["radar"] {
  // 雷达本体和地图 marker 是两层事实：本体 ready 不等于地图已经画出 marker。
  // lifecycle 与 fresh 只说明传感器链路，本函数仍以 map overlay 作为可见 marker 的唯一口径。
  const radarReady = lidar.lifecycle_running === "true" && lidar.latest_scan_proof_fresh === "true";
  const radarStopped = lidar.lifecycle_running === "false"
    || lidar.lifecycle_state === "stopped"
    || lidar.continuous_scan_status === "lifecycle_not_running";
  // overlayPointCount 是地图上实际画出来的点数；sourcePointCount 只用于解释为什么没有贴图。
  const overlayPointCount = map.radar_overlay_point_count || "0";
  const overlaySourcePointCount = map.radar_overlay_source_point_count || lidar.scan_preview_source_point_count || "not_loaded";
  const overlayFrameId = map.radar_overlay_frame_id || "not_loaded";
  const overlaySourceFrameId = map.radar_overlay_source_frame_id || lidar.scan_preview_frame_id || "not_loaded";
  // 地图层 loaded 或点数大于 0 才能称为 marker 可见，避免把旧扫描来源点误说成所见即所得。
  const overlayPointCountNumber = Number(overlayPointCount);
  const overlayLoaded = map.radar_overlay_status === "loaded" || overlayPointCountNumber > 0;
  const overlayVisibleOnMap = ["loaded", "partial"].includes(map.radar_overlay_status)
    && Number.isFinite(overlayPointCountNumber)
    && overlayPointCountNumber > 0;
  const status = radarReady ? "radar_ready" : radarStopped ? "radar_stopped" : lidar.status || "not_loaded";
  const missingObservationText = lidar.radar_scan_observation_missing_reasons || "none";
  const hasMissingObservations = missingObservationText !== "none" && missingObservationText !== "not_loaded";
  const missingObservations = missingObservationText.split(",").map((item) => item.trim()).filter(Boolean);
  const missingObservationPlain = radarObservationLabelPlain(missingObservations);
  // ready 但 marker 为 0 时仍要显式写 0 个点，方便脚本和现场人员对照地图画面。
  const radarStatusPlain = overlayVisibleOnMap
    // 地图上已经画出的雷达点必须优先作为普通用户事实；scan proof 缺口保留在拆分诊断字段中。
    ? plainFactPart(map.radar_overlay_wysiwyg_status_plain) || `地图雷达点当前显示 ${overlayPointCount} 个。`
    : radarReady
    ? overlayLoaded
      ? `雷达已运行且扫描是新的；地图雷达点当前显示 ${overlayPointCount} 个。`
      : `雷达已运行且扫描是新的；地图雷达点当前显示 ${overlayPointCount} 个，仍需以同轮地图预览为准。`
    : radarStopped
      // 雷达停了就不能把来源点当作当前地图 marker；这是本轮 WYSIWYG 的关键边界。
      ? `雷达未运行或扫描已停；地图雷达点当前显示 ${overlayPointCount} 个，旧来源点 ${overlaySourcePointCount} 个只作诊断。`
      : hasMissingObservations
        ? `雷达已运行但扫描材料不完整：${missingObservationPlain}；地图雷达点当前显示 ${overlayPointCount} 个。`
        : `雷达状态未完全就绪；地图雷达点当前显示 ${overlayPointCount} 个，需确认雷达正在运行且有新扫描。`;
  // 下一步只引导 operator 做显式 start/refresh，不在 summary 构建时替 operator 发命令。
  const radarNextActionPlain = overlayVisibleOnMap
    ? plainFactPart(map.radar_overlay_wysiwyg_next_action_plain) || "继续观察地图雷达层。"
    : radarReady
    ? overlayLoaded
      ? "继续监看地图雷达点；若现场变化，刷新地图画面读取同轮贴图。"
      : "刷新地图画面，确认地图上实际显示的雷达点数。"
    : radarStopped
      ? "先启动雷达并等待新扫描，再刷新地图画面确认雷达点。"
    : hasMissingObservations
        ? lidar.radar_map_overlay_next_action_plain || `先补齐雷达扫描材料：${missingObservationPlain}；有新扫描后再刷新地图画面。`
        : "先刷新雷达扫描读数，再读取雷达状态；就绪后刷新地图画面确认雷达点。";
  return {
    status,
    plain_hint: radarPlainHint(radarStatusPlain, radarNextActionPlain),
    next_action_plain: radarNextActionPlain,
    radar_status_plain: radarStatusPlain,
    radar_next_action_plain: radarNextActionPlain,
    lifecycle_running: lidar.lifecycle_running,
    lifecycle_state: lidar.lifecycle_state,
    continuous_scan_status: lidar.continuous_scan_status,
    latest_scan_proof_fresh: lidar.latest_scan_proof_fresh,
    runtime_scan_status: lidar.runtime_scan_status,
    driver_diagnostics_status: lidar.driver_diagnostics_status || "not_loaded",
    driver_diagnostics_next_action_plain: lidar.driver_diagnostics_next_action_plain || "not_loaded",
    driver_serial_bytes_read_total: lidar.driver_serial_bytes_read_total || "not_loaded",
    driver_serial_packet_count_total: lidar.driver_serial_packet_count_total || "not_loaded",
    driver_serial_empty_read_count: lidar.driver_serial_empty_read_count || "not_loaded",
    driver_published_scan_count: lidar.driver_published_scan_count || "not_loaded",
    radar_scan_observation_status: lidar.radar_scan_observation_status || "not_loaded",
    radar_scan_observation_missing_reasons: missingObservationText,
    radar_map_overlay_readiness_status: lidar.radar_map_overlay_readiness_status || "not_loaded",
    radar_map_overlay_next_action_plain: lidar.radar_map_overlay_next_action_plain || radarNextActionPlain,
    scan_point_count: lidar.scan_preview_point_count,
    scan_preview_point_count: lidar.scan_preview_point_count,
    scan_preview_source_point_count: lidar.scan_preview_source_point_count,
    scan_preview_frame_id: lidar.scan_preview_frame_id,
    radar_overlay_status: map.radar_overlay_status,
    radar_overlay_point_count: overlayPointCount,
    radar_overlay_source_point_count: overlaySourcePointCount,
    radar_overlay_frame_id: overlayFrameId,
    radar_overlay_source_frame_id: overlaySourceFrameId,
    radar_overlay_wysiwyg_status_plain: map.radar_overlay_wysiwyg_status_plain,
    radar_overlay_wysiwyg_next_action_plain: map.radar_overlay_wysiwyg_next_action_plain,
    radar_overlay_blocked_reasons: map.radar_overlay_blocked_reasons,
    radar_overlay_blocked_reason_labels: map.radar_overlay_blocked_reason_labels,
    // map_marker_* 是给外部脚本的直观别名，值必须始终等于当前地图 overlay 读数。
    map_marker_point_count: overlayPointCount,
    map_marker_source_point_count: overlaySourcePointCount,
    map_marker_frame_id: overlayFrameId,
    map_marker_source_frame_id: overlaySourceFrameId,
  };
}

function radarPlainHint(statusPlain: string, nextActionPlain: string): string {
  // 脚本只读一个字段时也要知道下一步；拆分字段仍保留 status/next_action 供高级诊断。
  const status = statusPlain.trim().replace(/[。；\s]+$/g, "");
  const next = nextActionPlain.trim().replace(/^下一步[:：]?\s*/, "").replace(/[。；\s]+$/g, "");
  if (!status && !next) {
    return "雷达事实未读到；先刷新 Robot Control summary。";
  }
  if (!next || status.includes(next) || next.includes(status)) {
    return `${status}。`;
  }
  return `${status}。下一步：${next}。`;
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
  const devicesPayload = devicesReadback?.payload ?? null;
  const healthRequestStatus = healthReadback?.request_status ?? "not_loaded";
  const cameraHealthLoaded = healthRequestStatus === "loaded";
  const devicesRecord = asRecord(devicesPayload);
  const currentSelection = asRecord(findFirstKey(healthPayload, ["current_selection"]));
  const sourceSummary = asRecord(findFirstKey(healthPayload, ["source_summary"]));
  const sourceSummarySelection = asRecord(sourceSummary?.current_selection);
  const mediaDiagnostics = asRecord(findFirstKey(healthPayload, ["media_diagnostics"]));
  const lastOfferError = asRecord(mediaDiagnostics?.last_offer_error)
    ?? asRecord(findFirstKey(healthPayload, ["last_first_frame_error"]))
    ?? asRecord(mjpegRelayOverlay?.last_error_payload);
  const overlaySelectedCandidate = {
    selected_name: asString(mjpegRelayOverlay?.selected_name, ""),
    selected_is_uvc_or_usb: mjpegRelayOverlay?.selected_is_uvc_or_usb,
  };
  const selectedCandidate = mergeCameraCandidateSummary(
    cameraSelectedCandidateSummary(healthPayload, devicesPayload),
    overlaySelectedCandidate,
  );
  const overlaySourceUsage: JsonRecord | null = mjpegRelayOverlay?.source_usage_status || mjpegRelayOverlay?.source_usage_owner_count
    ? {
      status: mjpegRelayOverlay.source_usage_status,
      owner_count: mjpegRelayOverlay.source_usage_owner_count,
      device: mjpegRelayOverlay.selected_path,
      owners: [],
    }
    : null;
  const sourceUsage = asRecord(findFirstKey(healthPayload, ["source_usage"]) ?? mediaDiagnostics?.source_usage) ?? overlaySourceUsage;
  const sourceDiagnosis = asRecord(findFirstKey(healthPayload, ["source_diagnosis"]) ?? mediaDiagnostics?.source_diagnosis);
  const uvcKernelDiagnostics = asRecord(findFirstKey(healthPayload, ["uvc_kernel_diagnostics"]) ?? mediaDiagnostics?.uvc_kernel_diagnostics);
  const uvcUsbTopology = asRecord(findFirstKey(healthPayload, ["uvc_usb_topology"]) ?? mediaDiagnostics?.uvc_usb_topology);
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
  const sourceUsageScope = cameraSourceUsageScope(sourceUsage?.status, sourceUsage?.owner_count);
  const sourceUsageNotExclusive = cameraSourceUsageNotExclusive(sourceUsageScope);
  const sourceUsageNotExclusiveForNoFrame = sourceUsageNotExclusive === "true";
  const sourceNoFrameNotExclusive = Boolean(sourceFirstFrameFailedForSharedPreview && sourceUsageNotExclusiveForNoFrame);
  const uvcKernelTransportErrorsObserved = asString(uvcKernelDiagnostics?.status, "") === "uvc_usb_transport_errors_observed"
    || asString(sourceDiagnosis?.uvc_kernel_diagnostics_status, "") === "uvc_usb_transport_errors_observed";
  const uvcVideoOnFullSpeedUsb = asString(uvcUsbTopology?.status, "") === "uvc_video_on_full_speed_usb"
    || asString(sourceDiagnosis?.uvc_usb_topology_status, "") === "uvc_video_on_full_speed_usb";
  const uvcFullSpeedPlainHint = asString(uvcUsbTopology?.plain_hint, "")
    || `不是页面独占：${selectedName} 当前无人占用，但摄像头挂在 USB 12M full-speed，视频流会 STREAMON I/O error；换高速 USB 口/线、减少转接并确认供电后复测。`;
  const probeBackendNoFrameNotExclusive = Boolean(
    firstFrameProbeOverlay?.backend_smoke_status === "backend_no_frame_observed"
    && firstFrameProbeOverlay.backend_frame_observed === "false"
    && sourceUsageScope !== "external_holder"
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
  const overlayDiagnosisIsPositiveFirstFrame = overlaySourceDiagnosis.status === "first_frame_observed";
  const overlayDiagnosisCanStandAlone = !overlayDiagnosisIsPositiveFirstFrame || cameraHealthLoaded;
  const derivedSourceDiagnosis = sourceNoFrameNotExclusive && uvcVideoOnFullSpeedUsb
    ? {
      status: "uvc_full_speed_usb_not_exclusive",
      plain_hint: uvcFullSpeedPlainHint,
      next_action: "move_camera_to_high_speed_usb_port_or_powered_hub",
      next_action_plain: cameraActionPlainText("move_camera_to_high_speed_usb_port_or_powered_hub"),
      not_exclusive: true,
    }
    : sourceNoFrameNotExclusive && uvcKernelTransportErrorsObserved
    ? {
      status: "uvc_transport_error_not_exclusive",
      plain_hint: `不是页面独占：${selectedName} 当前无人占用，但内核日志已有 UVC/USB 传输错误；检查 USB 线、接口、摄像头供电或换 known-good UVC 复测。`,
      next_action: "check_usb_cable_port_power_or_known_good_uvc",
      next_action_plain: cameraActionPlainText("check_usb_cable_port_power_or_known_good_uvc"),
      not_exclusive: true,
    }
    : probeBackendNoFrameNotExclusive
    ? {
      status: "uvc_no_frame_not_exclusive",
      plain_hint: `不是页面独占：${cameraOwnerFreeText(selectedName)}，但 OpenCV/V4L2 后端也没有取到视频帧。`,
      next_action: "check_usb_camera_input_power_or_known_good_uvc",
      next_action_plain: cameraActionPlainText("check_usb_camera_input_power_or_known_good_uvc"),
      not_exclusive: true,
    }
    : overlayDiagnosisAvailable && overlayDiagnosisCanStandAlone && !asRecord(sourceDiagnosis)
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
        plain_hint: sourceUsageScope === "camera_service_self"
          ? `不是页面独占：相机服务正在用单上游共享预览读取 ${selectedName}，但 UVC 设备没有输出视频帧。`
          : `不是页面独占：${cameraOwnerFreeText(selectedName)}，但 UVC 设备没有输出视频帧。`,
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
  const sourceFirstFrameObserved = Boolean(
    // 正向首帧证明必须来自当前 health/probe；relay overlay 可能是旧状态，不能在 health 超时时放行建图。
    resolvedSourceReadiness === "first_frame_observed"
    || (cameraHealthLoaded && asString(sourceDiagnosis?.status, "") === "first_frame_observed")
    || probeVisibleContentObserved,
  );
  const rawPreviewGuidance = cameraSummaryPreviewGuidance(sharedPreviewStatus, sourceFirstFrameFailedForSharedPreview, derivedSourceDiagnosis);
  const previewGuidance = sourceFirstFrameObserved && sharedPreviewStatus !== "streaming" && !sourceFirstFrameFailedForSharedPreview
    ? {
      plain_hint: "相机源首帧已读到；本页共享实时预览还没显示缓存帧。",
      next_action: "open_shared_preview",
      next_action_plain: cameraActionPlainText("open_shared_preview"),
    }
    : rawPreviewGuidance;
  const previewVisibility = cameraPreviewVisibilityPlainSummary({
    previewStatus: sharedPreviewStatus,
    sourceFirstFrameFailed: sourceFirstFrameFailedForSharedPreview,
    previewPlainHint: previewGuidance.plain_hint,
    previewNextActionPlain: previewGuidance.next_action_plain,
  });
  const sharedPreviewClientCount = compactValueText(mjpegRelayOverlay?.client_count ?? 0);
  const sharedPreviewCachedFrameLoaded = mjpegRelayOverlay?.cached_frame_loaded === true;
  const sharedPreviewCachedFrameAgeMs = mjpegRelayOverlay?.cached_frame_age_ms === null || mjpegRelayOverlay?.cached_frame_age_ms === undefined
    ? "none"
    : compactValueText(mjpegRelayOverlay.cached_frame_age_ms);
  const sharedPreviewPlain = cameraSharedPreviewPlainSummary({
    previewStatus: sharedPreviewStatus,
    clientCount: sharedPreviewClientCount,
    relayKey: asString(mjpegRelayOverlay?.relay_key, "not_loaded"),
    cachedFrameLoaded: sharedPreviewCachedFrameLoaded,
    cachedFrameAgeMs: sharedPreviewCachedFrameAgeMs,
    previewVisiblePlain: previewVisibility.visiblePlain,
  });
  const sourceDiagnosisNextActionPlain = cameraPlainTextOrActionPlain(
    derivedSourceDiagnosis.next_action_plain,
    derivedSourceDiagnosis.next_action,
  ) || previewGuidance.next_action_plain;
  const lastOfferFormatAttemptsSummary = cameraFormatAttemptsSummary(lastOfferError);
  const inferredProbeFailureReason = ["", "none", "not_loaded"].includes(resolvedSourceFailureReason)
    ? relayFirstFrameFailureReason || lastOfferFailureReason || sharedPreviewLastFailureReason
    : resolvedSourceFailureReason;
  const firstFrameProbeStatus = firstFrameProbeOverlay?.status
    ?? (sourceFirstFrameFailedForSharedPreview ? "source_first_frame_failed" : "not_loaded");
  const firstFrameProbeFailureReason = firstFrameProbeOverlay?.failure_reason
    || (sourceFirstFrameFailedForSharedPreview ? inferredProbeFailureReason || "camera_source_first_frame_failed" : "none");
  const firstFrameProbeReadOk = firstFrameProbeOverlay?.read_ok
    ?? (sourceFirstFrameFailedForSharedPreview ? "false" : "not_loaded");
  const firstFrameProbeVisibleContentProven = firstFrameProbeOverlay?.visible_content_proven
    ?? (sourceFirstFrameFailedForSharedPreview ? "false" : "not_loaded");
  const firstFrameProbeFallbackAttemptsSummary = firstFrameProbeOverlay?.fallback_attempts_summary
    ?? (sourceFirstFrameFailedForSharedPreview ? lastOfferFormatAttemptsSummary : "none");
  const firstFrameProbeStreamonIoErrorObserved = firstFrameProbeOverlay?.streamon_io_error_observed ?? "false";
  const firstFrameProbeStreamonIoErrorCount = firstFrameProbeOverlay?.streamon_io_error_count ?? "0";
  const firstFrameProbeLatestStreamonIoError = firstFrameProbeOverlay?.latest_streamon_io_error ?? "none";
  const firstFrameProbeCheckedAtMs = firstFrameProbeOverlay
    ? String(firstFrameProbeOverlay.checked_at_ms)
    : sourceFirstFrameFailedForSharedPreview && mjpegRelayOverlay?.last_failure_at_ms !== null && mjpegRelayOverlay?.last_failure_at_ms !== undefined
      ? compactValueText(mjpegRelayOverlay.last_failure_at_ms)
      : "not_loaded";
  const selectedPathReadback = asString(
    currentSelection?.selected_path
      ?? sourceSummarySelection?.selected_path
      ?? healthPayload?.selected_path
      ?? sourceDiagnosis?.selected_path
      ?? mjpegRelayOverlay?.selected_path
      ?? sourceUsage?.device
      ?? healthPayload?.video_source,
    "not_loaded",
  );
  const selectedDisplayName = cameraDisplayDeviceName(selectedCandidate.selected_name) || "not_loaded";
  const devicesEndpointCount = Array.isArray(devicesRecord?.devices) ? devicesRecord.devices.length : 0;
  const healthSourceCandidateCount = Array.isArray(sourceSummary?.candidates) ? sourceSummary.candidates.length : 0;
  const devicesFromHealthFallback = Boolean(devicesReadback?.status === "loaded" && devicesEndpointCount === 0 && healthSourceCandidateCount > 0);
  const devicesEffectiveStatus = devicesFromHealthFallback
    ? "loaded_from_health_source_summary"
    : devicesReadback?.status ?? "not_loaded";
  const selectedDevicePlain = selectedDisplayName !== "not_loaded"
    ? selectedPathReadback !== "not_loaded" ? `${selectedDisplayName} (${selectedPathReadback})` : selectedDisplayName
    : "当前选择未读到";
  const devicesPlainHint = devicesFromHealthFallback
    ? `相机设备列表返回 0 个设备，但上位机相机健康检查已读到 ${healthSourceCandidateCount} 个候选；当前选择 ${selectedDevicePlain}，继续按无首帧诊断排查。`
    : devicesReadback?.status === "loaded"
      ? `相机设备列表已返回 ${devicesEndpointCount} 个设备；当前选择 ${selectedDevicePlain}。`
      : "相机设备列表未读到；先刷新页面状态或检查上位机相机健康检查。";
  return {
    status: cameraStatus,
    devices_status: devicesReadback?.status ?? "not_loaded",
    devices_effective_status: devicesEffectiveStatus,
    devices_endpoint_count: compactValueText(devicesEndpointCount),
    devices_health_candidate_count: compactValueText(healthSourceCandidateCount),
    devices_plain_hint: devicesPlainHint,
    // MJPEG relay 状态来自 PC Node 内存表；它只说明共享上游是否存在，不证明画面像素已经可见。
    preview_status: sharedPreviewStatus,
    plain_hint: cameraPlainHint(previewVisibility.wysiwygStatusPlain, sharedPreviewPlain.accessPlain, previewVisibility.wysiwygNextActionPlain),
    preview_plain_hint: previewGuidance.plain_hint,
    preview_next_action: previewGuidance.next_action,
    preview_next_action_plain: previewGuidance.next_action_plain,
    preview_visible_status: previewVisibility.visibleStatus,
    preview_visible_plain: previewVisibility.visiblePlain,
    camera_wysiwyg_status_plain: previewVisibility.wysiwygStatusPlain,
    camera_wysiwyg_next_action_plain: previewVisibility.wysiwygNextActionPlain,
    shared_preview_client_count: sharedPreviewClientCount,
    viewer_count: sharedPreviewClientCount,
    shared_preview_upstream_active: compactValueText(mjpegRelayOverlay?.upstream_active === true),
    upstream_connected: compactValueText(mjpegRelayOverlay?.upstream_active === true),
    shared_preview_content_type_loaded: compactValueText(mjpegRelayOverlay?.content_type_loaded === true),
    shared_preview_cached_frame_loaded: compactValueText(sharedPreviewCachedFrameLoaded),
    has_recent_frame: compactValueText(sharedPreviewCachedFrameLoaded),
    shared_preview_cached_frame_age_ms: sharedPreviewCachedFrameAgeMs,
    shared_preview_access_plain: sharedPreviewPlain.accessPlain,
    shared_preview_realtime_plain: sharedPreviewPlain.realtimePlain,
    shared_preview_shared_capture: compactValueText(true),
    shared_preview_exclusive_camera_claim: compactValueText(false),
    shared_preview_contract: sharedPreviewContract,
    shared_preview_multi_viewer_status: "single_upstream_multi_viewer",
    shared_preview_multi_viewer_plain: sharedPreviewPlain.multiViewerPlain,
    shared_preview_last_failure_reason: sharedPreviewLastFailureReason,
    shared_preview_last_remote_http_status: sharedPreviewLastRemoteHttpStatus,
    shared_preview_last_failure_at_ms: mjpegRelayOverlay?.last_failure_at_ms === null || mjpegRelayOverlay?.last_failure_at_ms === undefined
      ? "none"
      : compactValueText(mjpegRelayOverlay.last_failure_at_ms),
    video_source: summaryValueText(healthPayload, ["video_source"]),
    video_source_mode: summaryValueText(healthPayload, ["video_source_mode"]),
    selected_path: selectedPathReadback,
    selected_name: selectedDisplayName,
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
    source_diagnosis_next_action_plain: sourceDiagnosisNextActionPlain,
    source_diagnosis_not_exclusive: compactValueText(derivedSourceDiagnosis.not_exclusive),
    uvc_kernel_diagnostics_status: asString(uvcKernelDiagnostics?.status, "not_loaded"),
    uvc_kernel_diagnostics_plain_hint: asString(uvcKernelDiagnostics?.plain_hint, "not_loaded"),
    uvc_kernel_diagnostics_next_action: asString(uvcKernelDiagnostics?.next_action, "not_loaded"),
    uvc_kernel_diagnostics_transport_error_count: uvcKernelDiagnostics?.transport_error_count === undefined
      ? "not_loaded"
      : compactValueText(uvcKernelDiagnostics.transport_error_count),
    uvc_kernel_diagnostics_latest_transport_error: asString(uvcKernelDiagnostics?.latest_transport_error, ""),
    uvc_usb_topology_status: asString(uvcUsbTopology?.status ?? sourceDiagnosis?.uvc_usb_topology_status ?? findFirstKey(healthPayload, ["uvc_usb_topology_status"]), "not_loaded"),
    uvc_usb_topology_plain_hint: asString(uvcUsbTopology?.plain_hint ?? findFirstKey(healthPayload, ["uvc_usb_topology_plain_hint"]), "not_loaded"),
    uvc_usb_topology_next_action: asString(uvcUsbTopology?.next_action ?? findFirstKey(healthPayload, ["uvc_usb_topology_next_action"]), "not_loaded"),
    uvc_usb_topology_video_usb_speed: asString(uvcUsbTopology?.video_usb_speed ?? sourceDiagnosis?.uvc_usb_topology_video_usb_speed ?? findFirstKey(healthPayload, ["uvc_usb_topology_video_usb_speed"]), "not_loaded"),
    uvc_usb_topology_kernel_usb_address: asString(uvcUsbTopology?.kernel_usb_address ?? findFirstKey(healthPayload, ["uvc_usb_topology_kernel_usb_address"]), "not_loaded"),
    uvc_usb_topology_video_interface_count: uvcUsbTopology?.video_interface_count === undefined
      ? summaryValueText(healthPayload, ["uvc_usb_topology_video_interface_count"])
      : compactValueText(uvcUsbTopology.video_interface_count),
    source_usage_status: asString(sourceUsage?.status, "not_loaded"),
    source_usage_owner_count: sourceUsage?.owner_count === undefined ? "not_loaded" : compactValueText(sourceUsage.owner_count),
    source_usage_scope: sourceUsageScope,
    source_usage_not_exclusive: sourceUsageNotExclusive,
    source_usage_summary: sourceUsageSummary || "none",
    active_peer_count: summaryValueText(healthPayload, ["active_peer_count", "active_peer_connections"]),
    last_offer_error: asString(lastOfferError?.error, "none"),
    last_offer_failure_reason: asString(lastOfferError?.failure_reason, "none"),
    last_offer_format_attempts_summary: lastOfferFormatAttemptsSummary,
    first_frame_probe_status: firstFrameProbeStatus,
    first_frame_probe_failure_reason: firstFrameProbeFailureReason,
    first_frame_probe_open_ok: firstFrameProbeOverlay?.open_ok ?? "not_loaded",
    first_frame_probe_read_ok: firstFrameProbeReadOk,
    first_frame_probe_visible_content_proven: firstFrameProbeVisibleContentProven,
    first_frame_probe_backend_smoke_status: firstFrameProbeOverlay?.backend_smoke_status ?? "not_requested",
    first_frame_probe_backend_frame_observed: firstFrameProbeOverlay?.backend_frame_observed ?? "not_loaded",
    first_frame_probe_backend_attempts: firstFrameProbeOverlay?.backend_attempts ?? "0",
    first_frame_probe_streamon_io_error_observed: firstFrameProbeStreamonIoErrorObserved,
    first_frame_probe_streamon_io_error_count: firstFrameProbeStreamonIoErrorCount,
    first_frame_probe_latest_streamon_io_error: firstFrameProbeLatestStreamonIoError,
    first_frame_probe_fallback_attempts_summary: firstFrameProbeFallbackAttemptsSummary,
    first_frame_probe_checked_at_ms: firstFrameProbeCheckedAtMs,
  };
}

function cameraPlainHint(wysiwygStatusPlain: string, sharedAccessPlain: string, nextActionPlain: string): string {
  // summary 的相机一字段事实给普通脚本读；底层 WYSIWYG 字段保持兼容原文，这里只做用户口径转换。
  const normalize = (value: string): string => value
    .trim()
    .replace(/画面未可见/g, "画面未显示")
    .replace(/画面已可见/g, "已经看到画面")
    .replace(/不当作画面可见/g, "不当作已经看到画面")
    .replace(/[。；\s]+$/g, "");
  const normalizeStatus = (value: string): string => normalize(value)
    // 上车 health 有时把动作建议拼在状态句后面；summary 顶层只保留一次下一步，避免普通用户读到重复动作。
    .replace(/；检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测$/g, "")
    .replace(/；共享预览不是页面独占$/g, "");
  const normalizeNext = (value: string): string => normalize(value)
    // 非独占事实已经由 sharedAccessPlain 单独说明，下一步只保留需要执行的排查动作。
    .replace(/；共享预览不是页面独占$/g, "");
  const parts = [normalizeStatus(wysiwygStatusPlain), normalize(sharedAccessPlain)]
    .filter((item) => item && !["not_loaded", "none"].includes(item));
  const uniqueParts = Array.from(new Set(parts));
  const next = normalizeNext(nextActionPlain);
  if (next) {
    uniqueParts.push(`下一步：${next}`);
  }
  return uniqueParts.length > 0 ? `${uniqueParts.join("。")}。` : "画面事实未读到；先刷新 Robot Control summary。";
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
  streamon_io_error_observed: string;
  streamon_io_error_count: string;
  latest_streamon_io_error: string;
  fallback_attempts_summary: string;
};

export type RobotControlCameraMjpegRelayOverlay = {
  relay_key?: string;
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
  source_readiness?: string;
  source_failure_reason?: string;
  selected_path?: string;
  selected_name?: string;
  selected_is_uvc_or_usb?: boolean | string;
  source_usage_status?: string;
  source_usage_owner_count?: string;
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
    minimal_precheck_safety_only: true,
    minimal_precheck_plain: NAV2_GOAL_MINIMAL_PRECHECK_PLAIN,
    preflight_blocking_requirements: [...NAV2_GOAL_PREFLIGHT_BLOCKING_REQUIREMENTS],
    operator_precheck_requirements: [...NAV2_GOAL_PREFLIGHT_OPERATOR_PRECHECK_REQUIREMENTS],
    proxy_guard_requirements: [...NAV2_GOAL_PREFLIGHT_PROXY_GUARD_REQUIREMENTS],
    camera_preflight_required: false,
    radar_preflight_required: false,
    operator_report_preflight_required: false,
    route_readback_preflight_required: false,
    localization_readback_preflight_required: false,
    nav2_status_readback_preflight_required: false,
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
    minimal_precheck_safety_only: true,
    minimal_precheck_plain: NAV2_GOAL_MINIMAL_PRECHECK_PLAIN,
    preflight_blocking_requirements: [...NAV2_GOAL_PREFLIGHT_BLOCKING_REQUIREMENTS],
    operator_precheck_requirements: [...NAV2_GOAL_PREFLIGHT_OPERATOR_PRECHECK_REQUIREMENTS],
    proxy_guard_requirements: [...NAV2_GOAL_PREFLIGHT_PROXY_GUARD_REQUIREMENTS],
    camera_preflight_required: false,
    radar_preflight_required: false,
    operator_report_preflight_required: false,
    route_readback_preflight_required: false,
    localization_readback_preflight_required: false,
    nav2_status_readback_preflight_required: false,
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
    sensor_lifecycle_only: true,
    map_preview_endpoint: "/api/robot-control/map/preview",
    post_start_map_preview_required: config.action === "start",
    radar_overlay_wysiwyg_status_plain: config.action === "start"
      ? "雷达启动未完成；地图雷达点仍以地图预览 radar_overlay 为准，不能把启动请求当作已贴图。"
      : "雷达停止未完成；地图雷达点仍以地图预览 radar_overlay 为准。",
    radar_overlay_wysiwyg_next_action_plain: config.action === "start"
      ? "先修复雷达启动失败，再刷新地图画面确认 radar_overlay_status 和点数。"
      : "先修复雷达停止失败，再刷新雷达状态和地图画面。",
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
    sensor_lifecycle_only: true,
    map_preview_endpoint: "/api/robot-control/map/preview",
    post_start_map_preview_required: config.action === "start",
    radar_overlay_wysiwyg_status_plain: config.action === "start"
      ? "雷达启动请求已转发；地图上是否显示雷达点必须以后续地图预览的 radar_overlay_status 和点数为准。"
      : "雷达停止请求已转发；旧雷达点不能当作当前地图标记，后续地图预览应显示 0 个当前雷达点或 not_current/not_loaded。",
    radar_overlay_wysiwyg_next_action_plain: config.action === "start"
      ? "等待新扫描后刷新地图画面，确认 radar_overlay_status=loaded 且 radar_overlay_point_count 大于 0。"
      : "刷新地图画面，确认旧雷达点不再贴到当前地图。",
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
    source_frame_id: "",
    robot_pose: null,
    source_endpoint_ids: [],
    blocked_reasons: reason ? [reason] : [],
    blocked_reason_labels: explanation.blocked_reason_labels,
    refresh_required: true,
    stale_source_points_suppressed: false,
    primary_blocked_reason: mapRadarOverlayPrimaryBlockedReason(reason ? [reason] : []),
    current_vs_source_plain: mapRadarOverlayCurrentVsSourcePlain("0", "0", false, explanation.next_action_plain),
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
  | "radar_overlay_current_point_count"
  | "radar_overlay_source_point_count"
  | "radar_overlay_refresh_required"
  | "radar_overlay_stale_source_points_suppressed"
  | "radar_overlay_primary_blocked_reason"
  | "radar_overlay_current_vs_source_plain"
  | "radar_overlay_needs_refresh"
  | "radar_overlay_blocks_wysiwyg"
  | "radar_overlay_blocks_free_move"
  | "radar_overlay_recovery_sequence"
  | "fixed_radar_overlay_refresh_endpoint"
  | "fixed_radar_overlay_map_preview_endpoint"
  | "radar_overlay_refresh_sends_motion"
  | "radar_overlay_refresh_starts_radar_lifecycle"
  | "radar_overlay_scan_preview_point_count"
  | "radar_overlay_scan_preview_source_point_count"
  | "radar_overlay_frame_id"
  | "radar_overlay_source_frame_id"
> {
  // 顶层 alias 与嵌套 overlay 同源，方便现场 curl/jq 一眼确认“地图上到底贴了几个当前雷达点”。
  const blocksWysiwyg = radarOverlay.overlay_status !== "loaded" || radarOverlay.count <= 0;
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
    radar_overlay_current_point_count: radarOverlay.count,
    radar_overlay_source_point_count: radarOverlay.source_count,
    radar_overlay_refresh_required: radarOverlay.refresh_required,
    radar_overlay_stale_source_points_suppressed: radarOverlay.stale_source_points_suppressed,
    radar_overlay_primary_blocked_reason: radarOverlay.primary_blocked_reason,
    radar_overlay_current_vs_source_plain: radarOverlay.current_vs_source_plain,
    radar_overlay_needs_refresh: radarOverlay.refresh_required,
    radar_overlay_blocks_wysiwyg: blocksWysiwyg,
    radar_overlay_blocks_free_move: false,
    radar_overlay_recovery_sequence: [
      "/api/robot-control/radar/scan-proof/refresh",
      "/api/robot-control/radar/status",
      "/api/robot-control/map/preview",
      "/api/robot-control/summary",
    ],
    fixed_radar_overlay_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh",
    fixed_radar_overlay_map_preview_endpoint: "/api/robot-control/map/preview",
    radar_overlay_refresh_sends_motion: false,
    radar_overlay_refresh_starts_radar_lifecycle: false,
    radar_overlay_scan_preview_point_count: radarOverlay.scan_preview_point_count,
    radar_overlay_scan_preview_source_point_count: radarOverlay.scan_preview_source_point_count,
    radar_overlay_frame_id: radarOverlay.frame_id,
    radar_overlay_source_frame_id: radarOverlay.source_frame_id,
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

function mapRadarOverlayPrimaryBlockedReason(blockedReasons: string[]): string {
  // 主原因优先给可执行动作：雷达没运行先启动，雷达旧读数先刷新，新点缺失再看扫描/解析，最后看定位。
  const normalized = blockedReasons.map((reason) => (reason.includes(":") ? reason.split(":").slice(1).join(":") : reason));
  const priority = [
    "radar_lifecycle_not_running_for_map_radar_overlay",
    "runtime_scan_stale_for_map_radar_overlay",
    "scan_preview_points_missing_for_map_radar_overlay",
    "scan_preview_points_missing",
    "robot_pose_missing_for_map_radar_overlay",
  ];
  return priority.find((reason) => normalized.includes(reason))
    ?? normalized.find((reason) => reason && reason !== "none")
    ?? "none";
}

function mapRadarOverlayStaleSourcePointsSuppressed(
  radarStatus: string,
  pointCount: string | number,
  sourcePointCount: string | number | null,
): boolean {
  // 旧来源点存在但当前贴图点为 0 时必须显式抑制，不能为了“看起来有点”而画到当前地图。
  const current = Number(pointCount);
  const source = sourcePointCount === null ? Number.NaN : Number(sourcePointCount);
  return radarStatus === "not_current"
    && Number.isFinite(current)
    && Number.isFinite(source)
    && current === 0
    && source > 0;
}

function mapRadarOverlayCurrentVsSourcePlain(
  pointCount: string | number,
  sourcePointCount: string | number | null,
  staleSourcePointsSuppressed: boolean,
  nextActionPlain: string,
): string {
  // 这句专门服务脚本和普通首屏：当前地图上几个点、旧材料几个点、下一步做什么，一句话说清。
  const currentText = pointCount === null || pointCount === "" ? "not_loaded" : String(pointCount);
  const sourceText = sourcePointCount === null || sourcePointCount === "" ? "not_loaded" : String(sourcePointCount);
  const staleText = staleSourcePointsSuppressed ? "；旧来源点已抑制，未贴到当前地图" : "";
  const nextText = nextActionPlain && !["none", "not_loaded"].includes(nextActionPlain)
    ? `；下一步：${nextActionPlain.replace(/[。；\s]+$/g, "")}`
    : "";
  return `地图雷达点：当前 ${currentText} 个，来源 ${sourceText} 个${staleText}${nextText}。`;
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
        ? "先启动雷达并等待新扫描，再刷新地图画面确认雷达点。"
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
  const hasLifecycleStop = blockedReasons.some((reason) => reason.includes("radar_lifecycle_not_running_for_map_radar_overlay"));
  const hasStaleScan = blockedReasons.some((reason) => reason.includes("runtime_scan_stale_for_map_radar_overlay"));
  const hasMissingPoints = blockedReasons.some((reason) => reason.includes("scan_preview_points_missing"));
  const nextAction = hasLifecycleStop
    ? "start_radar_then_refresh_map_preview"
    : hasStaleScan || hasMissingPoints
      ? "refresh_radar_scan_for_map_overlay"
      : "connect_robot_and_refresh_map_preview";
  const nextActionPlain = hasLifecycleStop
    ? "先启动雷达并等待新扫描，再刷新地图画面确认雷达点。"
    : hasStaleScan
      ? "刷新雷达扫描，再刷新地图画面。"
      : hasMissingPoints
        ? "先刷新雷达扫描；有新点后再刷新地图画面确认雷达点。"
        : "确认小车地址可访问后刷新地图画面。";
  return {
    plain_hint: blockedReasons.length ? `地图雷达层未加载：${labels.join("、")}。` : "地图雷达层未加载。",
    next_action: nextAction,
    next_action_plain: nextActionPlain,
    blocked_reason_labels: labels,
  };
}

function mapPreviewOverlayStatus(value: unknown): RobotControlMapPreviewRadarOverlay["overlay_status"] | null {
  // 上车 map preview 自带 overlay 时，以它为当前地图画面的事实；只接受已知状态，避免任意字符串污染 UI。
  const status = asString(value, "");
  return status === "loaded" || status === "partial" || status === "blocked" || status === "not_current" || status === "not_loaded"
    ? status
    : null;
}

function mapPreviewRobotPoseFromPayload(value: unknown): RobotApiMapPose | null {
  // 地图预览里的 robot_pose 已经是 map 坐标；没有完整 x/y 时不能拿来贴雷达点。
  const rawPose = asRecord(value);
  if (!rawPose) {
    return null;
  }
  const x = finitePathCoordinate(rawPose.x ?? rawPose.x_m);
  const y = finitePathCoordinate(rawPose.y ?? rawPose.y_m);
  if (x === null || y === null) {
    return null;
  }
  return {
    x,
    y,
    yaw: finitePathCoordinate(rawPose.yaw ?? rawPose.yaw_rad) ?? 0,
    frame_id: asString(rawPose.frame_id, "map"),
    source: asString(rawPose.source, "/api/map/preview.radar_overlay.robot_pose"),
  };
}

function mapPreviewRadarOverlayFromPayload(payload: JsonRecord): RobotControlMapPreviewRadarOverlay | null {
  // 新版上车 /api/map/preview 会直接返回当前地图雷达层；PC proxy 必须优先信任这份“画面本体”证据。
  const rawOverlay = asRecord(payload.radar_overlay);
  const source = rawOverlay ?? payload;
  const overlayStatus = mapPreviewOverlayStatus(rawOverlay ? (source.overlay_status ?? source.status) : payload.radar_overlay_status);
  if (!overlayStatus) {
    return null;
  }
  const points: RobotApiScanPreviewPoint[] = [];
  appendStructuredScanPreviewPoints(source.scan_preview_points ?? source.points ?? payload.radar_overlay_points, source, points);
  const pointCount = finitePathCoordinate(source.scan_preview_point_count ?? source.count ?? payload.radar_overlay_point_count) ?? points.length;
  const sourcePointCount = finitePathCoordinate(source.scan_preview_source_point_count ?? source.source_count ?? payload.radar_overlay_source_point_count) ?? pointCount;
  const sourceFrameId = asString(source.scan_preview_frame_id ?? source.source_frame_id ?? payload.radar_overlay_source_frame_id, points[0]?.frame_id ?? "");
  const frameId = overlayStatus === "loaded" || overlayStatus === "partial"
    ? asString(source.frame_id ?? payload.radar_overlay_frame_id, sourceFrameId)
    : "not_loaded";
  const robotPose = mapPreviewRobotPoseFromPayload(source.robot_pose);
  const blockedReasons = stringList(source.blocked_reasons ?? payload.radar_overlay_blocked_reasons, 8);
  const effectiveBlockedReasons = overlayStatus === "loaded" ? [] : blockedReasons;
  const explanation = mapRadarOverlayExplanation(overlayStatus, effectiveBlockedReasons, sourcePointCount, robotPose);
  const staleSourcePointsSuppressed = mapRadarOverlayStaleSourcePointsSuppressed(overlayStatus, pointCount, sourcePointCount);
  const wysiwyg = radarOverlayWysiwygPlainSummary({
    radarStatus: overlayStatus,
    pointCount: String(pointCount),
    sourcePointCount: String(sourcePointCount),
    frameId,
    radarHint: explanation.plain_hint,
    radarNextAction: explanation.next_action_plain,
  });
  return {
    overlay_status: overlayStatus,
    status: overlayStatus,
    plain_hint: asString(source.plain_hint, explanation.plain_hint),
    wysiwyg_status_plain: asString(source.wysiwyg_status_plain, wysiwyg.statusPlain),
    wysiwyg_next_action_plain: asString(source.wysiwyg_next_action_plain, wysiwyg.nextActionPlain),
    next_action: asString(source.next_action, explanation.next_action),
    next_action_plain: asString(source.next_action_plain, explanation.next_action_plain),
    scan_preview_points: points,
    scan_preview_point_count: pointCount,
    scan_preview_source_point_count: sourcePointCount,
    scan_preview_frame_id: sourceFrameId,
    points,
    count: pointCount,
    source_count: sourcePointCount,
    frame_id: frameId,
    source_frame_id: sourceFrameId,
    robot_pose: robotPose,
    source_endpoint_ids: ["map_preview"],
    blocked_reasons: effectiveBlockedReasons,
    blocked_reason_labels: explanation.blocked_reason_labels,
    refresh_required: explanation.next_action !== "continue_monitoring_map_radar_overlay",
    stale_source_points_suppressed: staleSourcePointsSuppressed,
    primary_blocked_reason: mapRadarOverlayPrimaryBlockedReason(effectiveBlockedReasons),
    current_vs_source_plain: mapRadarOverlayCurrentVsSourcePlain(
      pointCount,
      sourcePointCount,
      staleSourcePointsSuppressed,
      explanation.next_action_plain,
    ),
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
  // 地图上画的点来自 scan proof；free-roam runtime 距离新鲜不能替代这批点自身的新鲜度。
  const latestScanProofStale = lidar.latest_scan_proof_fresh === "false"
    || lidar.continuous_scan_status.includes("stale")
    || lidar.continuity_window_status.includes("stale");
  const radarRuntimeStale = latestScanProofStale || lidar.runtime_scan_status === "stale";
  const radarLifecycleStopped = lidar.lifecycle_running === "false" || lidar.lifecycle_state === "stopped";
  const radarOverlayCurrent = hasRadarPoints && !radarRuntimeStale && !radarLifecycleStopped;
  const overlayGaps = [
    hasRadarPoints && !hasMapPose ? "robot_pose_missing_for_map_radar_overlay" : "",
    radarRuntimeStale ? "runtime_scan_stale_for_map_radar_overlay" : "",
    radarLifecycleStopped ? "radar_lifecycle_not_running_for_map_radar_overlay" : "",
    hasMapPose && !hasRadarPoints ? "scan_preview_points_missing_for_map_radar_overlay" : "",
  ].filter(Boolean);
  const overlayBlockedReasons = [...blockedReasons, ...overlayGaps];
  const overlayStatus: RobotControlMapPreviewRadarOverlay["overlay_status"] = radarOverlayCurrent && hasMapPose
    ? "loaded"
    : radarOverlayCurrent
      ? "partial"
      : hasRadarPoints
        ? "not_current"
        : "not_loaded";
  const explanation = mapRadarOverlayExplanation(
    overlayStatus,
    overlayBlockedReasons,
    proofSummary.scan_preview_source_point_count,
    proofSummary.robot_pose,
  );
  const visibleRadarPoints = radarOverlayCurrent ? proofSummary.scan_preview_points : [];
  const visibleRadarPointCount = radarOverlayCurrent ? proofSummary.scan_preview_point_count : 0;
  const visibleRadarFrameId = radarOverlayCurrent ? proofSummary.scan_preview_frame_id : "";
  const staleSourcePointsSuppressed = mapRadarOverlayStaleSourcePointsSuppressed(
    overlayStatus,
    visibleRadarPointCount,
    proofSummary.scan_preview_source_point_count,
  );
  const wysiwyg = radarOverlayWysiwygPlainSummary({
    radarStatus: overlayStatus,
    pointCount: String(visibleRadarPointCount),
    sourcePointCount: proofSummary.scan_preview_source_point_count === null ? "not_loaded" : String(proofSummary.scan_preview_source_point_count),
    frameId: visibleRadarFrameId || "not_loaded",
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
    // frame_id 只描述当前实际贴到地图上的雷达点；旧来源 frame 放到 source_frame_id。
    frame_id: visibleRadarFrameId,
    source_frame_id: proofSummary.scan_preview_frame_id,
    robot_pose: proofSummary.robot_pose,
    source_endpoint_ids: endpoints.map((endpoint) => endpoint.id),
    blocked_reasons: overlayBlockedReasons,
    blocked_reason_labels: explanation.blocked_reason_labels,
    refresh_required: explanation.next_action !== "continue_monitoring_map_radar_overlay",
    stale_source_points_suppressed: staleSourcePointsSuppressed,
    primary_blocked_reason: mapRadarOverlayPrimaryBlockedReason(overlayBlockedReasons),
    current_vs_source_plain: mapRadarOverlayCurrentVsSourcePlain(
      visibleRadarPointCount,
      proofSummary.scan_preview_source_point_count,
      staleSourcePointsSuppressed,
      explanation.next_action_plain,
    ),
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
  // map preview 顶层口径按“地图/路线/小车”和“地图雷达点”分层，避免把旧雷达来源点重复说成当前贴图。
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
    mapRadarUserFacingStatusPlainFromOverlay(radarOverlay),
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
    ...MAP_PREVIEW_READBACK_ONLY_FLAGS,
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
    next_action_plain: pathNextActionPlain,
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
  // 雷达 WYSIWYG 单独说明“地图上实际画了几个雷达点”，避免把旧来源点误当成当前贴图。
  const displayedCount = args.pointCount && args.pointCount !== "not_loaded" ? args.pointCount : "0";
  const sourceCount = args.sourcePointCount && args.sourcePointCount !== "not_loaded" ? args.sourcePointCount : "0";
  const frameText = args.frameId && args.frameId !== "not_loaded" ? `，frame=${args.frameId}` : "";
  if (args.radarStatus === "loaded") {
    return {
      statusPlain: `雷达点已贴到当前地图：当前显示 ${displayedCount} 个点${frameText}。`,
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
      statusPlain: `雷达点未贴到当前地图：当前显示 ${displayedCount} 个点；旧来源点 ${sourceCount} 个只作诊断。${args.radarHint}`,
      nextActionPlain: args.radarNextAction,
    };
  }
  return {
    statusPlain: `地图雷达点未加载：当前显示 ${displayedCount} 个点；来源点 ${sourceCount} 个。${args.radarHint}`,
    nextActionPlain: args.radarNextAction,
  };
}

function mapRadarUserFacingStatusPlain(args: {
  radarStatus: string;
  pointCount: string;
  sourcePointCount: string;
  frameId: string;
  blockedReasonLabels: string[];
}): string {
  // 普通入口只说“地图雷达点”，marker/overlay 细节留在拆分诊断字段里。
  const displayedCount = args.pointCount && args.pointCount !== "not_loaded" ? args.pointCount : "0";
  const sourceCount = args.sourcePointCount && args.sourcePointCount !== "not_loaded" ? args.sourcePointCount : "0";
  const frameText = args.frameId && args.frameId !== "not_loaded" ? `，frame=${args.frameId}` : "";
  const reasonText = args.blockedReasonLabels.filter((label) => label && label !== "none").join("、");
  const reasonSuffix = reasonText ? `；原因：${reasonText}` : "";
  if (args.radarStatus === "loaded") {
    return `地图雷达点已按当前读数显示：当前显示 ${displayedCount} 个点${frameText}。`;
  }
  if (args.radarStatus === "partial") {
    return `地图雷达点未完整显示：当前显示 ${displayedCount} 个点，来源点 ${sourceCount} 个${reasonSuffix}。`;
  }
  if (args.radarStatus === "not_current") {
    return `地图雷达点当前显示 ${displayedCount} 个，旧来源点 ${sourceCount} 个只作诊断${reasonSuffix}。`;
  }
  if (args.radarStatus === "blocked") {
    return `地图雷达点未显示：当前显示 ${displayedCount} 个点，来源点 ${sourceCount} 个${reasonSuffix}。`;
  }
  return `地图雷达点未加载：当前显示 ${displayedCount} 个点，来源点 ${sourceCount} 个${reasonSuffix}。`;
}

function mapRadarUserFacingStatusPlainFromOverlay(radarOverlay: RobotControlMapPreviewRadarOverlay): string {
  return mapRadarUserFacingStatusPlain({
    radarStatus: radarOverlay.overlay_status,
    pointCount: String(radarOverlay.count),
    sourcePointCount: radarOverlay.source_count === null ? "not_loaded" : String(radarOverlay.source_count),
    frameId: radarOverlay.frame_id || "not_loaded",
    blockedReasonLabels: radarOverlay.blocked_reason_labels,
  });
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
  const radarOverlay = mapPreviewRadarOverlayFromPayload(payload) ?? overlayReadback.radarOverlay;
  const pathStatus = overlayReadback.pathPreview.path_preview_point_count > 0 ? "path_preview_observed" : "not_observed";
  const poseStatus = radarOverlay.robot_pose ? "map_pose_observed" : "not_observed";
  const pathNextActionPlain = mapPreviewPathNextActionPlain(pathStatus, poseStatus);
  const mapWysiwyg = mapWysiwygPlainSummary({
    mapObserved: forwarded ? "true" : "false",
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
    mapRadarUserFacingStatusPlainFromOverlay(overlayReadback.radarOverlay),
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
    ...MAP_PREVIEW_READBACK_ONLY_FLAGS,
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
    radar_overlay: radarOverlay,
    map_wysiwyg_status_plain: mapWysiwyg.statusPlain,
    map_wysiwyg_next_action_plain: mapWysiwyg.nextActionPlain,
    ...mapPreviewRadarOverlayAliases(radarOverlay),
    robot_pose: radarOverlay.robot_pose,
    robot_pose_status: poseStatus,
    path_preview_points: overlayReadback.pathPreview.path_preview_points,
    path_preview_status: pathStatus,
    path_preview_next_action_plain: pathNextActionPlain,
    next_action_plain: pathNextActionPlain,
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

function summaryReadbackTimeoutMs(config: RobotReadEndpointConfig, options: RobotControlSummaryBuildOptions): number | undefined {
  // 测试可注入统一短超时；生产默认对会拖首屏的聚合/设备/底盘慢读做 summary 级短预算。
  return options.readbackTimeoutMs ?? config.summary_timeout_ms;
}

async function readSummaryEndpoints(
  base: URL,
  options: RobotControlSummaryBuildOptions,
): Promise<InternalRobotApiEndpointReadback[]> {
  // 真实上位机 HTTP 服务接近单 worker；底盘慢读走短预算并行，最后串行读状态聚合，避免普通首屏被串口窗口拖住。
  const fastConfigs = READ_ENDPOINTS.filter((item) => !SUMMARY_SERIAL_READ_ENDPOINT_IDS.has(item.id));
  const fastReadbacks = await Promise.all(
    fastConfigs.map((item) => readEndpoint(base, item, summaryReadbackTimeoutMs(item, options))),
  );
  const serialReadbacks: InternalRobotApiEndpointReadback[] = [];
  for (const id of ["status"] as const) {
    const config = READ_ENDPOINTS.find((item) => item.id === id);
    if (config) {
      serialReadbacks.push(await readEndpoint(base, config, summaryReadbackTimeoutMs(config, options)));
    }
  }
  const byId = new Map([...fastReadbacks, ...serialReadbacks].map((item) => [item.id, item]));
  return READ_ENDPOINTS
    .map((item) => byId.get(item.id))
    .filter((item): item is InternalRobotApiEndpointReadback => Boolean(item));
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
    ...PROOF_REFRESH_NO_MOTION_FLAGS,
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
    ...PROOF_REFRESH_NO_MOTION_FLAGS,
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

function proofRefreshTopLevelAliases(readbackKeyValues: Record<string, string>): Partial<RobotControlProofRefreshProxyResponse> {
  // 顶层 alias 只复制固定 key_fields 的只读摘要，方便现场脚本直接读取，不扩大代理可读/可写范围。
  const aliasKeys = [
    "latest_proof_status",
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
    "map_once_observed",
    "path_generated",
    "path_generation_succeeded",
    "path_point_count",
  ] as const;
  const aliases: Partial<RobotControlProofRefreshProxyResponse> = {};
  for (const key of aliasKeys) {
    const value = readbackKeyValues[key];
    if (value !== undefined && value !== "") {
      aliases[key] = value;
    }
  }
  return aliases;
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

  const latestReadbackKeyValues = compactKeyValues(latestPayload, config.key_fields);
  return failedRefreshResponse(baseUrl, normalizedBaseUrl, postFailureReason, config, observedAt, {
    last_result_status: asString(
      findFirstKey(latestPayload, ["status", "latest_proof_status", "latest_result_status", "refresh_status", "result_status"]),
      "loaded",
    ),
    last_result_schema: asString(latestPayload.schema, "schema_missing"),
    last_result_evidence_ref: asString(findFirstKey(latestPayload, ["evidence_ref", "latest_evidence_ref", "result_evidence_ref"]), "not_loaded"),
    latest_readback_key_values: latestReadbackKeyValues,
    ...proofRefreshTopLevelAliases(latestReadbackKeyValues),
    blocked_reasons: [postFailureReason, "post_timeout_latest_readback_loaded"],
  });
}

function radarRefreshNeedsLatestReadback(readbackKeyValues: Record<string, string>): boolean {
  // 真实 refresh 回包有时只返回 refreshed；成功但关键字段不完整时也要补读固定 latest。
  const observationsComplete = readbackKeyValues.scan_once_observed === "true" &&
    readbackKeyValues.scan_hz_observed === "true" &&
    readbackKeyValues.raw_packet_once_observed === "true" &&
    readbackKeyValues.tf_observed === "true";
  return !observationsComplete || readbackKeyValues.latest_scan_proof_fresh !== "true";
}

function sleepMs(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function radarLatestReadbackAfterRefresh(
  normalizedBaseUrl: URL,
  refreshReadbackKeyValues: Record<string, string>,
): Promise<{
  latestReadbackKeyValues: Record<string, string>;
  postRefreshLatestReadbackStatus: string;
  postRefreshLatestReadbackAttemptCount: string;
}> {
  // 这里只允许固定 no-motion latest GET，避免把雷达刷新按钮变成新的任意代理或 runtime 启动入口。
  if (!radarRefreshNeedsLatestReadback(refreshReadbackKeyValues)) {
    return {
      latestReadbackKeyValues: refreshReadbackKeyValues,
      postRefreshLatestReadbackStatus: "not_required",
      postRefreshLatestReadbackAttemptCount: "0",
    };
  }

  let lastStatus = "not_fresh_after_retry";
  let attemptCount = 0;
  for (const delayMs of RADAR_SCAN_PROOF_POST_REFRESH_READBACK_DELAYS_MS) {
    if (delayMs > 0) {
      await sleepMs(delayMs);
    }
    attemptCount += 1;

    let latestResponse: Response;
    try {
      latestResponse = await fetch(endpointUrl(normalizedBaseUrl, RADAR_SCAN_PROOF_LATEST_ENDPOINT), {
        method: "GET",
        signal: AbortSignal.timeout(DEFAULT_REQUEST_TIMEOUT_MS),
      });
    } catch (error) {
      lastStatus = error instanceof Error && error.name === "TimeoutError"
        ? `latest_fetch_timeout_${DEFAULT_REQUEST_TIMEOUT_MS}ms`
        : "latest_fetch_failed";
      continue;
    }

    const latestBody = await latestResponse.json().catch(() => null);
    const latestEnvelope = asRecord(latestBody);
    const latestPayload = asRecord(latestEnvelope?.payload) ?? latestEnvelope;
    if (!latestResponse.ok || !latestPayload) {
      lastStatus = latestPayload ? `latest_http_status_${latestResponse.status}` : "latest_response_json_not_object";
      continue;
    }

    const hardDangerous = scanDangerousTrueFields(latestPayload, "", HARD_DANGEROUS_TRUE_FIELDS);
    if (hardDangerous.length > 0) {
      return {
        latestReadbackKeyValues: refreshReadbackKeyValues,
        postRefreshLatestReadbackStatus: `latest_hard_dangerous_true_field:${hardDangerous[0]}`,
        postRefreshLatestReadbackAttemptCount: String(attemptCount),
      };
    }

    const latestReadbackPayload = radarScanProofReadbackPayload(latestPayload);
    const latestReadbackKeyValues = compactKeyValues(latestReadbackPayload, RADAR_SCAN_PROOF_REFRESH_CONFIG.key_fields);
    if (latestReadbackKeyValues.latest_scan_proof_fresh === "true") {
      return {
        latestReadbackKeyValues,
        postRefreshLatestReadbackStatus: "fresh_after_retry",
        postRefreshLatestReadbackAttemptCount: String(attemptCount),
      };
    }
    lastStatus = "not_fresh_after_retry";
  }

  return {
    latestReadbackKeyValues: refreshReadbackKeyValues,
    postRefreshLatestReadbackStatus: lastStatus,
    postRefreshLatestReadbackAttemptCount: String(attemptCount),
  };
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
      ...PROOF_REFRESH_NO_MOTION_FLAGS,
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
      ...PROOF_REFRESH_NO_MOTION_FLAGS,
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
  const refreshResultAllowsLatestReadback = refreshSuccessful && !lastResultStatus.toLowerCase().includes("blocked") &&
    !lastResultStatus.toLowerCase().includes("failed") &&
    !lastResultStatus.toLowerCase().includes("error");
  const readbackPayload = config.kind === "radar_scan_proof_refresh" ? radarScanProofReadbackPayload(payload) : payload;
  const refreshReadbackKeyValues = compactKeyValues(readbackPayload, config.key_fields);
  const radarPostRefreshReadback = config.kind === "radar_scan_proof_refresh" && refreshResultAllowsLatestReadback
    ? await radarLatestReadbackAfterRefresh(normalized.normalized, refreshReadbackKeyValues)
    : {
        latestReadbackKeyValues: refreshReadbackKeyValues,
        postRefreshLatestReadbackStatus: "",
        postRefreshLatestReadbackAttemptCount: "",
      };
  const latestReadbackKeyValues = radarPostRefreshReadback.latestReadbackKeyValues;

  return {
    schema: "trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1",
    ...PROOF_FLAGS,
    ...PROOF_REFRESH_NO_MOTION_FLAGS,
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
    latest_readback_key_values: latestReadbackKeyValues,
    ...proofRefreshTopLevelAliases(latestReadbackKeyValues),
    post_refresh_latest_readback_status: radarPostRefreshReadback.postRefreshLatestReadbackStatus || undefined,
    post_refresh_latest_readback_attempt_count: radarPostRefreshReadback.postRefreshLatestReadbackAttemptCount || undefined,
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

function readbackText(readback: RobotApiEndpointReadback | null | undefined, keys: string[]): string | null {
  // 单个端点内按 key 优先级取值；用于“当前状态优先”的字段，避免历史 artifact 覆盖 live 状态。
  for (const key of keys) {
    const value = readback?.key_values[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return null;
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
  const mapPreview = readbackById(readbacks, "map_preview");
  const mapPreviewOverlay = mapPreview?.payload ? mapPreviewRadarOverlayFromPayload(mapPreview.payload) : null;
  const hasScanPreviewPoints = proof.scan_preview_point_count > 0;
  // 地图雷达层使用 scan proof 点位；proof 不 fresh 时不能被 free-roam runtime scan 覆盖成当前贴图。
  const latestScanProofStale = lidar.latest_scan_proof_fresh === "false"
    || lidar.continuous_scan_status.includes("stale")
    || lidar.continuity_window_status.includes("stale");
  const radarRuntimeStale = latestScanProofStale || lidar.runtime_scan_status === "stale";
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
  const effectiveRadarOverlayStatus = mapPreviewOverlay?.overlay_status ?? radarOverlayStatus;
  const effectiveRadarOverlayBlockedReasons = mapPreviewOverlay?.blocked_reasons ?? radarOverlayBlockedReasons;
  const effectiveRadarOverlayExplanation = mapPreviewOverlay
    ? {
        plain_hint: mapPreviewOverlay.plain_hint,
        next_action: mapPreviewOverlay.next_action,
        next_action_plain: mapPreviewOverlay.next_action_plain,
        blocked_reason_labels: mapPreviewOverlay.blocked_reason_labels,
      }
    : mapRadarOverlayExplanation(
      radarOverlayStatus,
      radarOverlayBlockedReasons,
      proof.scan_preview_source_point_count,
      proof.robot_pose,
    );
  const pathPreviewStatus = proof.path_preview_point_count > 0 ? "path_preview_observed" : "not_observed";
  const effectiveRobotPose = mapPreviewOverlay?.robot_pose ?? proof.robot_pose;
  const robotPoseStatus = effectiveRobotPose ? "map_pose_observed" : "not_observed";
  const fallbackRadarOverlayPointCount = String(radarOverlayCurrent ? proof.scan_preview_point_count : 0);
  const fallbackRadarOverlaySourcePointCount = proof.scan_preview_source_point_count === null ? "not_loaded" : String(proof.scan_preview_source_point_count);
  const radarOverlayPointCount = mapPreviewOverlay ? String(mapPreviewOverlay.count) : fallbackRadarOverlayPointCount;
  const radarOverlaySourcePointCount = mapPreviewOverlay
    ? mapPreviewOverlay.source_count === null ? "not_loaded" : String(mapPreviewOverlay.source_count)
    : fallbackRadarOverlaySourcePointCount;
  const radarOverlayStaleSourcePointsSuppressed = mapPreviewOverlay?.stale_source_points_suppressed ?? mapRadarOverlayStaleSourcePointsSuppressed(
    effectiveRadarOverlayStatus,
    radarOverlayPointCount,
    radarOverlaySourcePointCount,
  );
  const fallbackRadarOverlaySourceFrameId = proof.scan_preview_frame_id || "not_loaded";
  const radarOverlaySourceFrameId = mapPreviewOverlay?.source_frame_id || fallbackRadarOverlaySourceFrameId;
  const radarOverlayFrameId = mapPreviewOverlay
    ? mapPreviewOverlay.frame_id || "not_loaded"
    : radarOverlayCurrent ? fallbackRadarOverlaySourceFrameId : "not_loaded";
  const pathNextActionPlain = mapPreviewPathNextActionPlain(pathPreviewStatus, robotPoseStatus);
  const mapCurrentVisible = booleanSummaryValue(proof.map_once_observed) === "true";
  const pathCurrentVisible = pathPreviewStatus === "path_preview_observed";
  const radarOverlayCurrentVisible = effectiveRadarOverlayStatus === "loaded" && Number(radarOverlayPointCount) > 0;
  const pathWysiwygStatusPlain = pathPreviewStatus === "path_preview_observed"
    ? "图上路线已显示在当前地图画面。"
    : "图上路线未显示；不能把旧路线或空路线当作当前所见。";
  const mapWysiwyg = mapWysiwygPlainSummary({
    mapObserved: booleanSummaryValue(proof.map_once_observed),
    pathStatus: pathPreviewStatus,
    poseStatus: robotPoseStatus,
    radarStatus: effectiveRadarOverlayStatus,
    radarHint: effectiveRadarOverlayExplanation.plain_hint,
    pathNextAction: pathNextActionPlain,
    radarNextAction: effectiveRadarOverlayExplanation.next_action_plain,
  });
  const radarOverlayWysiwyg = radarOverlayWysiwygPlainSummary({
    radarStatus: effectiveRadarOverlayStatus,
    pointCount: radarOverlayPointCount,
    sourcePointCount: radarOverlaySourcePointCount,
    frameId: radarOverlayFrameId,
    radarHint: effectiveRadarOverlayExplanation.plain_hint,
    radarNextAction: effectiveRadarOverlayExplanation.next_action_plain,
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
    plain_hint: mapSummaryPlainHint(
      mapWysiwyg.statusPlain,
      pathWysiwygStatusPlain,
      mapRadarUserFacingStatusPlain({
        radarStatus: effectiveRadarOverlayStatus,
        pointCount: radarOverlayPointCount,
        sourcePointCount: radarOverlaySourcePointCount,
        frameId: radarOverlayFrameId,
        blockedReasonLabels: effectiveRadarOverlayExplanation.blocked_reason_labels,
      }),
      mapWysiwyg.nextActionPlain,
    ),
    next_action_plain: pathNextActionPlain,
    map_current_visible: String(mapCurrentVisible),
    path_current_visible: String(pathCurrentVisible),
    radar_overlay_current_visible: String(radarOverlayCurrentVisible),
    map_next_action_plain: mapWysiwyg.nextActionPlain,
    map_wysiwyg_status_plain: mapWysiwyg.statusPlain,
    map_wysiwyg_next_action_plain: mapWysiwyg.nextActionPlain,
    path_preview_status: pathPreviewStatus,
    path_preview_point_count: String(proof.path_preview_point_count),
    path_preview_frame_id: proof.path_preview_frame_id || "not_loaded",
    path_preview_next_action_plain: pathNextActionPlain,
    path_wysiwyg_status_plain: pathWysiwygStatusPlain,
    path_wysiwyg_next_action_plain: pathNextActionPlain,
    robot_pose_status: robotPoseStatus,
    radar_overlay_status: effectiveRadarOverlayStatus,
    radar_overlay_plain_hint: effectiveRadarOverlayExplanation.plain_hint,
    radar_overlay_wysiwyg_status_plain: radarOverlayWysiwyg.statusPlain,
    radar_overlay_wysiwyg_next_action_plain: radarOverlayWysiwyg.nextActionPlain,
    radar_overlay_next_action: effectiveRadarOverlayExplanation.next_action,
    radar_overlay_next_action_plain: effectiveRadarOverlayExplanation.next_action_plain,
    radar_overlay_point_count: radarOverlayPointCount,
    radar_overlay_source_point_count: radarOverlaySourcePointCount,
    radar_overlay_refresh_required: String(effectiveRadarOverlayExplanation.next_action !== "continue_monitoring_map_radar_overlay"),
    radar_overlay_stale_source_points_suppressed: String(radarOverlayStaleSourcePointsSuppressed),
    radar_overlay_primary_blocked_reason: mapRadarOverlayPrimaryBlockedReason(effectiveRadarOverlayBlockedReasons),
    radar_overlay_current_vs_source_plain: mapRadarOverlayCurrentVsSourcePlain(
      radarOverlayPointCount,
      radarOverlaySourcePointCount,
      radarOverlayStaleSourcePointsSuppressed,
      effectiveRadarOverlayExplanation.next_action_plain,
    ),
    radar_overlay_frame_id: radarOverlayFrameId,
    radar_overlay_source_frame_id: radarOverlaySourceFrameId,
    radar_overlay_blocked_reasons: effectiveRadarOverlayBlockedReasons.join(",") || "none",
    radar_overlay_blocked_reason_labels: effectiveRadarOverlayExplanation.blocked_reason_labels.join(",") || "none",
    radar_overlay_scan_preview_point_count: radarOverlayPointCount,
    radar_overlay_scan_preview_source_point_count: radarOverlaySourcePointCount,
    radar_overlay_scan_preview_frame_id: radarOverlaySourceFrameId,
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

function mapSummaryPlainHint(mapStatusPlain: string, pathStatusPlain: string, radarStatusPlain: string, nextActionPlain: string): string {
  // summary 的地图一字段事实要同时覆盖地图画面、路线和地图雷达点；旧雷达点不能冒充当前贴图。
  const { map, radar } = currentFactMapRadarParts(mapStatusPlain, radarStatusPlain);
  const parts = [map, pathStatusPlain, radar]
    .map((item) => item.trim().replace(/[。；\s]+$/g, ""))
    .filter((item) => item && !["not_loaded", "none"].includes(item));
  const uniqueParts = Array.from(new Set(parts));
  const next = nextActionPlain.trim().replace(/[。；\s]+$/g, "");
  if (next) {
    uniqueParts.push(`下一步：${next}`);
  }
  return uniqueParts.length > 0 ? `${uniqueParts.join("。")}。` : "地图事实未读到；先刷新 Robot Control summary。";
}

function nav2SummaryFromReadbacks(
  readbacks: InternalRobotApiEndpointReadback[],
  proof: RobotApiProofSummary,
): RobotControlSummaryResponse["readback_summary"]["nav2"] {
  // Nav2 摘要优先呈现最近完整路线执行结果；路线规划状态仍由 path_* 和 nav2_status 字段单独解释。
  const nav2Proof = readbackById(readbacks, "nav2_proof_latest");
  const nav2Status = readbackById(readbacks, "nav2_status");
  const mapProof = readbackById(readbacks, "map_proof_latest");
  const localizeProof = readbackById(readbacks, "localize_proof_latest");
  const statusReadback = readbackById(readbacks, "status");
  const baseStatusReadback = readbackById(readbacks, "base_status");
  const goalExecution = readbackById(readbacks, "nav2_goal_execution_latest");
  const currentBlockerReasons = nav2ProofBlockerReasons(nav2Proof?.payload);
  const goalPayload = goalExecution?.payload ?? null;
  const goalResultPayload = asRecord(goalPayload?.latest_result) ?? goalPayload;
  const baseCommandSummary = asRecord(goalResultPayload?.base_command_summary);
  const baseFeedbackSummary = asRecord(goalResultPayload?.base_feedback_summary);
  const managedRuntime = asRecord(goalResultPayload?.managed_runtime);
  const managedRuntimeCleanup = asRecord(managedRuntime?.cleanup);
  const managedRuntimeLifecycleReady = asRecord(managedRuntime?.lifecycle_ready);
  const latestNonzeroPair = asRecord(baseFeedbackSummary?.latest_nonzero_pair);
  const latestPair = asRecord(baseFeedbackSummary?.latest_pair);
  const goalExecutionStatus = summaryValueText(goalResultPayload, ["status"], goalExecution?.status ?? "not_loaded");
  const nav2StatusPayload = nav2Status?.payload ?? null;
  const lifecycleManager = asRecord(nav2StatusPayload?.lifecycle_manager);
  const nav2StackRunning = summaryValueText(nav2StatusPayload, ["lifecycle_running"], summaryValueText(lifecycleManager, ["running"]));
  const nav2StackLifecycleState = summaryValueText(nav2StatusPayload, ["lifecycle_state"], summaryValueText(lifecycleManager, ["state"]));
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
  const modePlain = nav2ExecutionModePlainFields({
    lastBaseMode,
    nextBaseMode,
    goalSucceeded,
    wheelFeedbackProven,
  });
  const summaryStatus = goalExecutionProven === "true" && goalExecutionStatus !== "not_loaded"
    ? goalExecutionStatus
    : goalSucceeded && wheelFeedbackProven === "false"
      ? "goal_succeeded_wheel_feedback_not_proven"
    : nav2Proof?.status ?? "not_loaded";
  const latestMapConsumed = proofText(readbacks, ["latest_map_consumed", "map_consumed"]) ?? "not_loaded";
  const latestPathGenerationAttempted = proofText(readbacks, ["latest_path_generation_attempted", "path_generation_attempted"]) ?? "not_loaded";
  const latestPathGenerationServiceAvailable = proofText(readbacks, ["latest_path_generation_service_available", "path_generation_service_available"]) ?? "not_loaded";
  const latestPathGenerationServiceName = proofText(readbacks, ["latest_path_generation_service_name", "path_generation_service_name"]) ?? "not_loaded";
  const currentPlannerServerActive = readbackText(nav2Status, ["planner_server_active", "latest_planner_active"])
    ?? readbackText(nav2Proof, ["planner_server_active", "planner_active", "latest_planner_active"])
    ?? booleanSummaryValue(proof.planner_server_active);
  const currentControllerServerActive = readbackText(nav2Status, ["controller_server_active", "latest_controller_active"])
    ?? readbackText(nav2Proof, ["controller_server_active", "latest_controller_active"])
    ?? "not_loaded";
  const currentControllerServerRequested = readbackText(nav2Status, ["controller_server_requested", "latest_controller_requested"])
    ?? readbackText(nav2Proof, ["controller_server_requested", "latest_controller_requested"])
    ?? "not_loaded";
  const routeAlreadyReady = readbackPathReady(proof);
  const nav2ReadbackUnavailable = robotReadbackUnavailable(nav2Proof) && robotReadbackUnavailable(nav2Status);
  const mapLocalizeReadbackUnavailable = robotReadbackUnavailable(mapProof) && robotReadbackUnavailable(localizeProof);
  const syntheticBlockerReasons = [
    nav2ReadbackUnavailable ? "robot_api_nav2_read_failed" : "",
    !routeAlreadyReady && nav2ReadbackUnavailable && mapLocalizeReadbackUnavailable ? "robot_api_map_localize_read_failed" : "",
    latestMapConsumed === "false" ? "nav2_map_not_consumed" : "",
    latestPathGenerationServiceAvailable === "false" ? "path_generation_service_unavailable" : "",
    latestPathGenerationAttempted === "false" && proof.path_generation_requested === true ? "path_generation_not_attempted" : "",
  ].filter(Boolean);
  const effectiveCurrentBlockerReasons = [...new Set([...currentBlockerReasons, ...statusBlockerReasons, ...syntheticBlockerReasons])];
  const effectiveCurrentBlockerLabels = nav2ProofBlockerLabels(effectiveCurrentBlockerReasons);
  const managedRuntimeAutoStartReady = (
    effectiveCurrentBlockerReasons.includes("nav2_lifecycle_not_running")
    || nav2StackRunning === "false"
    || ["stopped", "inactive", "unconfigured"].includes(nav2StackLifecycleState)
  );
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
    managedRuntimeAutoStartReady,
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
    managedRuntimeAutoStartReady,
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
    managedRuntimeAutoStartReady,
    pathReady: readbackPathReady(proof),
  });
  return {
    status: summaryStatus,
    plain_hint: nav2PlainHint(readbackPlain.execution_status_plain, readbackPlain.next_action_plain),
    nav2_status: nav2Status?.status ?? "not_loaded",
    nav2_stack_running: nav2StackRunning,
    nav2_stack_lifecycle_state: nav2StackLifecycleState,
    current_blocker_reasons: effectiveCurrentBlockerReasons.join(",") || "none",
    current_blocker_labels: effectiveCurrentBlockerLabels.join("、") || "not_loaded",
    planner_server_active: currentPlannerServerActive,
    controller_server_active: currentControllerServerActive,
    controller_server_requested: currentControllerServerRequested,
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
    goal_execution_next_mode_plain: modePlain.nextModePlain,
    goal_execution_mode_rerun_plain: modePlain.rerunPlain,
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
    goal_execution_readback_publishes_cmd_vel: summaryValueText(goalPayload, ["readback_publishes_cmd_vel"], summaryValueText(goalResultPayload, ["publishes_cmd_vel"])),
    goal_execution_managed_runtime_requested: summaryValueText(managedRuntime, ["requested"]),
    goal_execution_managed_runtime_started: summaryValueText(managedRuntime, ["started"]),
    goal_execution_managed_runtime_lifecycle_ready_ok: summaryValueText(managedRuntimeLifecycleReady, ["ok"]),
    goal_execution_managed_runtime_cleanup_ok: summaryValueText(managedRuntimeCleanup, ["ok"]),
    goal_execution_sends_base_motion_commands: summaryValueText(goalResultPayload, ["sends_base_motion_commands"]),
    goal_execution_uses_base_uart: summaryValueText(goalResultPayload, ["uses_base_uart"]),
    goal_execution_goal_frame_id: summaryValueText(goalResultPayload, ["goal_frame_id", "frame_id"]),
    goal_execution_goal_x: summaryValueText(goalResultPayload, ["goal_x", "x"]),
    goal_execution_goal_y: summaryValueText(goalResultPayload, ["goal_y", "y"]),
    goal_execution_generated_at_ms: summaryValueText(goalResultPayload, ["generated_at_ms", "nav2_generated_at_ms"]),
    goal_execution_response_generated_at_ms: summaryValueText(goalPayload, ["response_generated_at_ms", "generated_at_ms"]),
  };
}

function nav2PlainHint(executionStatusPlain: string, nextActionPlain: string): string {
  // 外部脚本常只读一个字段；这里把“当前证明状态”和“下一步”压成一句，但不改变任何发车门禁。
  const status = nav2PlainUserFacingText(executionStatusPlain).trim().replace(/[。；\s]+$/g, "");
  const next = nav2PlainUserFacingText(nextActionPlain).trim().replace(/^下一步[:：]?\s*/, "").replace(/[。；\s]+$/g, "");
  if (!status && !next) {
    return "自动驾驶事实未读到；先刷新 Robot Control summary。";
  }
  if (!next) {
    return status;
  }
  if (!status) {
    return `下一步：${next}。`;
  }
  return `${status}。下一步：${next}。`;
}

function nav2PlainUserFacingText(text: string): string {
  // summary 的 plain_hint 面向普通脚本和首屏；高级 wheel raw 名称仍保留在拆分字段里。
  return text
    .replace(/Nav2 planner 和 Nav2 controller/g, "规划服务和控制服务")
    .replace(/Nav2 planner/g, "规划服务")
    .replace(/Nav2 controller/g, "控制服务")
    .replace(/或 controller/g, "或控制服务")
    .replace(/\bcontroller\b/g, "控制服务")
    .replace(/执行窗口 wheel raw L\/R/g, "执行窗口轮速 L/R")
    .replace(/同窗口 wheel raw L\/R/g, "同窗口轮速 L/R")
    .replace(/但 wheel raw L\/R/g, "但执行窗口轮速 L/R")
    .replace(/wheel raw L\/R/g, "执行窗口轮速 L/R")
    .replace(/路线 action 成功/g, "路线结果成功")
    .replace(/未 active/g, "未运行");
}

function readbackPathReady(proof: RobotApiProofSummary): boolean {
  // 路线是否可执行必须以同一轮 map/path preview 事实为准，避免只看 service 状态误挡 managed execute。
  return proof.path_generated === true
    || proof.path_generation_succeeded === true
    || (proof.path_point_count ?? 0) > 0
    || proof.path_preview_point_count > 0;
}

function nav2ManagedRuntimeAutoStartText(enabled: boolean, pathReady: boolean): string {
  // Nav2 goal execute 已托管启动 runtime；在路线就绪时要把这个事实前置给普通用户。
  return enabled && pathReady ? "；执行时会自动启动自动驾驶 runtime" : "";
}

function nav2BlockedNextActionPlain(labels: string[]): string {
  // 读取失败优先于路线生成提示；否则用户会反复点“准备路线”却没看到小车地址/API 根因。
  if (labels.includes("自动驾驶状态读取失败") || labels.includes("地图/定位读取失败")) {
    return "先确认小车地址和上位机 API 可读，再刷新地图/自动驾驶状态并准备图上路线。";
  }
  if (labels.length > 0 && labels.join("、") !== "not_loaded") {
    return "先按当前根因处理，再准备图上路线并刷新地图画面。";
  }
  return "先准备图上路线并刷新地图画面，再勾选安全确认执行。";
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
  managedRuntimeAutoStartReady: boolean;
}): { readinessPlain: string; precheckPlain: string } {
  // 这两个字段只回答普通操作员最关心的两件事：能不能按图执行、发车前还要勾什么。
  const pathReady = readbackPathReady(args.proof);
  const runtimeAutoStartText = nav2ManagedRuntimeAutoStartText(args.managedRuntimeAutoStartReady, pathReady);
  const modeText = ["", "not_loaded"].includes(args.nextBaseMode)
    ? "当前模式"
    : `${args.nextBaseMode.toUpperCase()} 模式`;
  const modeActionText = modeText === "当前模式" ? modeText : ` ${modeText}`;
  const minimalPrecheck = `只需勾选行程前安全确认；相机、雷达和现场报告不作为额外发车前置；执行会用${modeActionText}跑图上路线${runtimeAutoStartText}。`;
  if (args.goalExecutionProven === "true" || args.wheelFeedbackProven === "true") {
    return {
      readinessPlain: "完整路线执行已证明；同窗口轮速 L/R 已非零。",
      precheckPlain: "下一步是送达确认；送达确认不会发车。",
    };
  }
  if (args.goalSucceeded && args.wheelFeedbackProven === "false") {
    return {
      readinessPlain: `图上路线可重跑复验；上次路线结果成功，但同窗口轮速 L/R=${args.latestLeft}/${args.latestRight} 未非零。`,
      precheckPlain: minimalPrecheck,
    };
  }
  if (pathReady) {
    return {
      readinessPlain: "图上路线可执行；完整路线执行和同窗口轮速 L/R 还未证明。",
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
  managedRuntimeAutoStartReady: boolean;
}): { execution_status_plain: string; next_action_plain: string } {
  // Nav2 readback 是脚本最常读的区块；这里给普通白话，避免外部再拼 wheel/raw/mode token。
  const pathReady = readbackPathReady(args.proof);
  const runtimeAutoStartText = nav2ManagedRuntimeAutoStartText(args.managedRuntimeAutoStartReady, pathReady);
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
      next_action_plain: `勾选行程前安全确认后用 ${nextMode}重跑图上路线${runtimeAutoStartText}，并在同窗口确认轮速 L/R 非零。`,
    };
  }
  if (pathReady) {
    return {
      execution_status_plain: "图上路线已准备，但本轮完整执行和轮速 L/R 还未证明。",
      next_action_plain: `勾选行程前安全确认后执行图上路线${runtimeAutoStartText}，并在同窗口确认轮速 L/R 非零。`,
    };
  }
  const blockers = args.effectiveCurrentBlockerLabels.length > 0 && args.effectiveCurrentBlockerLabels.join("、") !== "not_loaded"
    ? `当前根因：${args.effectiveCurrentBlockerLabels.join("、")}。`
    : "";
  return {
    execution_status_plain: `图上路线还未准备完成。${blockers}`,
    next_action_plain: nav2BlockedNextActionPlain(args.effectiveCurrentBlockerLabels),
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
  managedRuntimeAutoStartReady?: boolean;
  pathReady?: boolean;
}): { statusPlain: string; nextActionPlain: string } {
  // 字段名沿用旧接口，普通文案只讲“轮速 L/R”，避免把 raw 术语带回首屏。
  if (args.wheelFeedbackProven === "true") {
    return {
      statusPlain: `执行窗口轮速 L/R 已非零：L=${args.latestLeft}，R=${args.latestRight}。`,
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
    const runtimeAutoStartText = nav2ManagedRuntimeAutoStartText(args.managedRuntimeAutoStartReady === true, args.pathReady === true);
    return {
      statusPlain: `上次路线结果成功，但执行窗口轮速 L/R=${args.latestLeft}/${args.latestRight} 未非零；${commandText}${imuText}。`,
      nextActionPlain: `勾选行程前安全确认后用 ${modeText}重跑图上路线${runtimeAutoStartText}，并在同窗口确认轮速 L/R 非零。`,
    };
  }
  return {
    statusPlain: "本轮完整路线执行的轮速 L/R 还未证明。",
    nextActionPlain: "先准备图上路线并执行，再在同窗口确认轮速 L/R 非零。",
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

function nav2ExecutionModePlainFields(args: {
  lastBaseMode: string;
  nextBaseMode: string;
  goalSucceeded: boolean;
  wheelFeedbackProven: string;
}): { nextModePlain: string; rerunPlain: string } {
  // 模式字段回答“下次到底用哪条控制链”，避免普通用户把旧 PWM/ROS 结果当成本轮结论。
  const last = args.lastBaseMode && args.lastBaseMode !== "not_loaded" ? args.lastBaseMode : "not_loaded";
  const next = args.nextBaseMode && args.nextBaseMode !== "not_loaded" ? args.nextBaseMode : "not_loaded";
  const wheelZero = args.goalSucceeded && args.wheelFeedbackProven === "false";
  if (next === "not_loaded") {
    return {
      nextModePlain: "下次执行模式未读到；默认由执行接口按固定策略选择。",
      rerunPlain: "还没有可用的路线执行模式复验结论。",
    };
  }
  if (wheelZero && last !== "not_loaded" && last !== next) {
    return {
      nextModePlain: `下次将用 ${next.toUpperCase()} 模式重跑图上路线。`,
      rerunPlain: `上次 ${last.toUpperCase()} 模式路线返回成功但轮速 L/R 仍未非零，本次切到 ${next.toUpperCase()} 模式复验控制链。`,
    };
  }
  if (wheelZero) {
    return {
      nextModePlain: `下次继续用 ${next.toUpperCase()} 模式重跑图上路线。`,
      rerunPlain: "上次路线返回成功但轮速 L/R 仍未非零，本次重点复验同窗口轮速反馈。",
    };
  }
  return {
    nextModePlain: `下次执行会使用 ${next.toUpperCase()} 模式。`,
    rerunPlain: "当前没有控制模式切换复验要求。",
  };
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
  manualMotionFallbackReady = false,
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
  const motionStartReady = startReady || manualMotionFallbackReady;
  const manualMotionFallbackActive = !startReady && manualMotionFallbackReady;
  const motionReady = Boolean(startReady && freeRoamRuntime?.cmd_vel_publish_enabled === true);
  const mappingGateById = new Map((freeRoamRuntimeGates ?? [])
    .filter((gate) => gate.scope === "mapping_acceptance")
    .map((gate) => [gate.id, gate]));
  const remoteMappingStartMissing = freeRoamRuntimeMissingList(latest?.free_roam_mapping_start_missing_reasons ?? payload?.free_roam_mapping_start_missing_reasons);
  const remoteMappingMissing = freeRoamRuntimeMissingList(latest?.free_roam_mapping_missing_reasons ?? latest?.mapping_missing_reasons ?? payload?.free_roam_mapping_missing_reasons ?? payload?.mapping_missing_reasons);
  const mappingStartMissing = remoteMappingStartMissing.length
    ? remoteMappingStartMissing
    : FREE_ROAM_MAPPING_START_REQUIRED_IDS.filter((id) => mappingGateById.get(id)?.state !== "ready");
  const mappingMissing = remoteMappingMissing.length
    ? remoteMappingMissing
    : FREE_ROAM_MAPPING_ACCEPTANCE_REQUIRED_IDS.filter((id) => mappingGateById.get(id)?.state !== "ready");
  const mappingStartReady = startReady && mappingStartMissing.length === 0;
  const mappingReady = startReady && mappingMissing.length === 0;
  const nextActionStatus = mappingReady ? "ready" : startReady ? "start_ready" : "locked";
  const externalStopRequested = freeRoamExternalStopRequested(freeRoamRuntime, freeRoamRuntimeGates);
  const derivedStatus = mappingReady
    ? "mapping_ready"
    : motionReady
      ? "motion_ready"
      : startReady
        ? "start_ready"
        : readback?.status ?? "not_loaded";
  const motionReadinessPlain = freeRoamMotionReadinessPlain(startReady, motionReady, externalStopRequested, manualMotionFallbackActive);
  const mappingReadinessPlain = freeRoamMappingReadinessPlain(startReady, mappingReady, mappingMissing);
  const motionSensorDependency = freeRoamMotionSensorDependencyPlain(startReady || manualMotionFallbackActive || motionReady);
  const mappingMissingText = mappingMissing.length ? mappingMissing.join(",") : "none";
  const nextActionPlain = freeRoamAutonomyNextAction(nextActionStatus, mappingReady, mappingMissing, freeRoamRuntime, manualMotionFallbackActive);
  const startWillClearStopRequest = motionStartReady && externalStopRequested;
  const startClearsStopRequestNotBlocking = startWillClearStopRequest && !manualMotionFallbackActive;
  const stopRequestStatusPlain = freeRoamStopRequestStatusPlain(motionStartReady, externalStopRequested);
  return {
    status: derivedStatus,
    runtime_status: asString(payload?.runtime_status, latest ? "loaded" : "not_loaded"),
    decision_state: asString(decision?.state, asString(payload?.decision_state, "not_loaded")),
    decision_reason: asString(decision?.reason, asString(payload?.decision_reason, "not_loaded")),
    stop_required: decision ? booleanSummaryValue(decision.stop_required === true) : summaryValueText(payload, ["stop_required"]) ?? "not_loaded",
    stop_request_pending: booleanSummaryValue(externalStopRequested),
    free_roam_stop_request_pending: booleanSummaryValue(externalStopRequested),
    start_will_clear_stop_request: booleanSummaryValue(startWillClearStopRequest),
    start_clears_stop_request_not_blocking: booleanSummaryValue(startClearsStopRequestNotBlocking),
    motion_start_blocked_by_stop_request: "false",
    stop_request_status_plain: stopRequestStatusPlain,
    artifact_only: latest ? booleanSummaryValue(latest.artifact_only !== false) : summaryValueText(payload, ["artifact_only"]) ?? "not_loaded",
    cmd_vel_publish_enabled: latest ? booleanSummaryValue(latest.cmd_vel_publish_enabled === true) : summaryValueText(payload, ["cmd_vel_publish_enabled"]) ?? "not_loaded",
    start_ready: booleanSummaryValue(startReady),
    free_move_ready: booleanSummaryValue(startReady),
    free_move_start_ready: booleanSummaryValue(startReady),
    motion_start_ready: booleanSummaryValue(motionStartReady),
    free_roam_motion_start_ready: booleanSummaryValue(motionStartReady),
    free_move_without_camera_allowed: booleanSummaryValue(motionStartReady),
    motion_without_radar_allowed: booleanSummaryValue(motionStartReady),
    free_move_minimal_precheck_safety_only: "true",
    free_move_safety_confirm_required: booleanSummaryValue(motionStartReady),
    free_move_camera_preflight_required: "false",
    free_move_radar_preflight_required: "false",
    motion_ready: booleanSummaryValue(motionReady),
    free_roam_motion_ready: booleanSummaryValue(motionReady),
    mapping_start_ready: booleanSummaryValue(mappingStartReady),
    free_roam_mapping_start_ready: booleanSummaryValue(mappingStartReady),
    mapping_start_requires_camera_first_frame: "true",
    mapping_start_requires_lidar_fresh: "true",
    mapping_start_missing: mappingStartMissing.length ? mappingStartMissing.join(",") : "none",
    mapping_readiness_ready: booleanSummaryValue(mappingReady),
    mapping_blocked_reasons: mappingMissingText,
    mapping_missing_reasons: mappingMissingText,
    free_roam_mapping_ready: booleanSummaryValue(mappingReady),
    free_roam_mapping_missing_reasons: mappingMissingText,
    mapping_ready: booleanSummaryValue(mappingReady),
    mapping_missing: mappingMissingText,
    plain_hint: freeRoamPlainHint(motionReadinessPlain, mappingReadinessPlain, nextActionPlain),
    next_action_plain: nextActionPlain,
    motion_readiness_plain: motionReadinessPlain,
    motion_sensor_dependency_status: startReady || manualMotionFallbackActive || motionReady ? "not_required_for_motion" : "unknown_until_motion_ready",
    motion_sensor_dependency_plain: motionSensorDependency,
    free_move_start_status_plain: freeRoamStartStatusPlain(startReady, motionReady, externalStopRequested, manualMotionFallbackActive),
    motion_runtime_status_plain: freeRoamMotionRuntimeStatusPlain(startReady, motionReady),
    mapping_acceptance_status_plain: mappingReadinessPlain,
    mapping_start_readiness_plain: freeRoamMappingStartReadinessPlain(startReady, mappingStartReady, mappingStartMissing),
    mapping_readiness_plain: mappingReadinessPlain,
    motion_next_action_plain: freeRoamMotionNextAction(startReady, motionReady, externalStopRequested, manualMotionFallbackActive),
    mapping_start_next_action_plain: freeRoamMappingStartNextAction(startReady, mappingStartReady, mappingStartMissing),
    mapping_next_action_plain: freeRoamMappingNextAction(startReady, mappingReady, mappingMissing),
    runtime_artifact_proven: summaryValueText(payload, ["free_roam_runtime_artifact_proven"]) ?? "not_loaded",
    state_machine_observed: summaryValueText(payload, ["free_roam_state_machine_observed"]) ?? "not_loaded",
    ros2_runtime_proven: summaryValueText(payload, ["ros2_runtime_proven"]) ?? "not_loaded",
    gate_count: gateCount,
  };
}

function freeRoamExternalStopRequested(
  freeRoamRuntime: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_runtime"] | null,
  freeRoamRuntimeGates: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_gates"] | null = null,
): boolean {
  // stop_required=true 也会出现在“未勾安全确认”的 locked 态；只有显式外部停止才按停止请求解释。
  return Boolean(
    freeRoamRuntime?.state === "stopping" && /现场请求停止|external_stop/i.test(freeRoamRuntime.reason)
    || (freeRoamRuntimeGates ?? []).some((gate) => gate.id === "external_stop_request"),
  );
}

function freeRoamStopRequestStatusPlain(motionStartReady: boolean, externalStopRequested: boolean): string {
  if (!externalStopRequested) {
    return "当前没有外部停止请求；自由移动启动不需要先清除停止请求。";
  }
  if (motionStartReady) {
    return "停止请求会在开始自由移动时自动解除，不作为启动阻塞。";
  }
  return "当前有停止请求；先恢复自由移动启动条件，再清除停止请求。";
}

function freeRoamPlainHint(motionReadinessPlain: string, mappingReadinessPlain: string, nextActionPlain: string): string {
  // 外部脚本只读一个字段时，也必须看出“能先移动”和“建图验收缺什么”是两层能力。
  const parts = [motionReadinessPlain, mappingReadinessPlain]
    .map((item) => item.trim().replace(/[。；\s]+$/g, ""))
    .filter((item) => item && !["not_loaded", "none"].includes(item));
  const next = nextActionPlain.trim().replace(/[。；\s]+$/g, "");
  const uniqueParts = Array.from(new Set(parts));
  const nextParts = freeRoamPlainNextParts(next, uniqueParts);
  if (nextParts.length > 0) {
    uniqueParts.push(`下一步：${nextParts.join("；")}`);
  }
  return uniqueParts.length > 0 ? `${uniqueParts.join("。")}。` : "自由移动事实未读到；先刷新 Robot Control summary。";
}

function freeRoamMotionSensorDependencyPlain(motionCanStart: boolean): string {
  // 用户最容易把相机/雷达缺口误读成“车不能动”；这里给脚本和首屏一个稳定的门禁事实。
  return motionCanStart
    ? "自由移动启动只看现场安全确认和停止兜底；相机、雷达和地图记录只影响建图验收。"
    : "自由移动启动条件未读到；相机、雷达和地图记录仍只作为建图验收材料。";
}

function freeRoamPlainNextParts(nextActionPlain: string, existingParts: string[]): string[] {
  // next_action_plain 来自安全边界，常把 motion 和 mapping 两层重复拼回去；总事实只保留新增动作。
  const motionText = existingParts.find((part) => part.includes("自由移动")) ?? "";
  const mappingText = existingParts.find((part) => part.includes("建图验收")) ?? "";
  const stopAlreadyExplained = motionText.includes("停止请求");
  const runningAlreadyExplained = motionText.includes("正在运行");
  return nextActionPlain
    .split(/[；;。]/)
    .map((item) => item.trim().replace(/[。；\s]+$/g, ""))
    .map((item) => (stopAlreadyExplained ? item.replace(/，开始时会先解除停止请求$/g, "") : item))
    .filter((item) => {
      if (!item || ["not_loaded", "none"].includes(item)) {
        return false;
      }
      if (stopAlreadyExplained && item.startsWith("当前处于停止请求")) {
        return false;
      }
      if (runningAlreadyExplained && item.includes("勾选现场安全确认后可先自由移动")) {
        return false;
      }
      if (item.startsWith("建图验收还差") && mappingText.includes("建图验收未就绪")) {
        return false;
      }
      if (item.includes("不影响先低速自由移动") && mappingText.includes("不影响先低速自由移动")) {
        return false;
      }
      return !existingParts.some((part) => part.includes(item) || item.includes(part));
    });
}

function failClosed(reason: string, sourceBaseUrl: string): RobotControlSummaryResponse {
  // URL 被拒或未配置时也返回完整合同，前端可以稳定展示七区块和恢复路径。
  const observedAt = Date.now();
  const goalSummary: RobotControlGoalChecklistSummary = {
    status: "not_started",
    status_label: "未开始",
    total_count: 0,
    done_count: 0,
    remaining_count: 0,
    safety_confirm_needed_count: 0,
    motion_needed_count: 0,
    ready_action_count: 0,
    blocked_action_count: 0,
    motion_ready_count: 0,
    sensor_blocker_count: 0,
    first_incomplete_item_id: "",
    first_incomplete_source_card_id: "",
    first_motion_item_id: "",
    first_motion_source_card_id: "",
    primary_ready_action_item_id: "",
    primary_ready_action_source_card_id: "",
    primary_ready_action_next_action_plain: sourceBaseUrl.trim() ? "先恢复小车连接并刷新状态。" : "先确认小车地址。",
    primary_ready_action_summary_plain: "未读到可先执行动作；先恢复小车连接。",
    safety_precheck_source_card_id: "",
    radar_item_id: "",
    radar_source_card_id: "",
    nav2_item_id: "",
    nav2_source_card_id: "",
    mapping_item_id: "",
    mapping_source_card_id: "",
    next_action_plain: sourceBaseUrl.trim() ? "先恢复小车连接并刷新状态。" : "先确认小车地址。",
    summary_plain: "本轮目标检查未读到；先恢复小车连接。",
    motion_next_action_plain: sourceBaseUrl.trim() ? "先恢复小车连接并刷新状态。" : "先确认小车地址。",
    motion_summary_plain: "车能不能先动还未读到；先恢复小车连接。",
    safety_precheck_next_action_plain: sourceBaseUrl.trim() ? "先恢复小车连接并刷新状态。" : "先确认小车地址。",
    safety_precheck_summary_plain: "发车前最小确认还未读到；先恢复小车连接。",
    radar_next_action_plain: sourceBaseUrl.trim() ? "先恢复小车连接并刷新状态。" : "先确认小车地址。",
    radar_summary_plain: "雷达贴图状态还未读到；先恢复小车连接。",
    nav2_next_action_plain: sourceBaseUrl.trim() ? "先恢复小车连接并刷新状态。" : "先确认小车地址。",
    nav2_summary_plain: "完整行程状态还未读到；先恢复小车连接。",
    mapping_next_action_plain: sourceBaseUrl.trim() ? "先恢复小车连接并刷新状态。" : "先确认小车地址。",
    mapping_summary_plain: "建图条件还未读到；先恢复小车连接。",
    move_now_status_plain: "当前还不能判断能否先动；先恢复小车连接并刷新状态。",
    mapping_blockers_plain: "建图缺口未读到；先恢复小车连接。",
    progress_plain: "0/0",
    next_action_item_ids: [],
    ready_action_ids: [],
    blocked_action_ids: [],
    next_action_items: [],
    ready_action_items: [],
    blocked_action_items: [],
  };
  const notLoadedNav2Summary: RobotControlSummaryResponse["readback_summary"]["nav2"] = {
    status: "not_loaded",
    plain_hint: "图上路线还未准备完成。下一步：先准备图上路线并刷新地图画面，再勾选安全确认执行。",
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
    goal_execution_wheel_raw_lr_status_plain: "本轮完整路线执行的轮速 L/R 还未证明。",
    goal_execution_wheel_raw_lr_next_action_plain: "先准备图上路线并执行，再在同窗口确认轮速 L/R 非零。",
    goal_execution_next_mode_plain: "下次执行模式未读到；默认由执行接口按固定策略选择。",
    goal_execution_mode_rerun_plain: "还没有可用的路线执行模式复验结论。",
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
    goal_execution_readback_publishes_cmd_vel: "not_loaded",
    goal_execution_managed_runtime_requested: "not_loaded",
    goal_execution_managed_runtime_started: "not_loaded",
    goal_execution_managed_runtime_lifecycle_ready_ok: "not_loaded",
    goal_execution_managed_runtime_cleanup_ok: "not_loaded",
    goal_execution_sends_base_motion_commands: "not_loaded",
    goal_execution_uses_base_uart: "not_loaded",
    goal_execution_goal_frame_id: "not_loaded",
    goal_execution_goal_x: "not_loaded",
    goal_execution_goal_y: "not_loaded",
    goal_execution_generated_at_ms: "not_loaded",
    goal_execution_response_generated_at_ms: "not_loaded",
  };
  const keyboardReadback = keyboardSummaryReadback();
  const payload: RobotControlSummaryResponse = {
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
    action_status_cards: [],
    goal_checklist: [],
    goal_checklist_summary: goalSummary,
    goal_summary: goalSummary,
    nav2_summary: notLoadedNav2Summary,
    readback_summary: {
      camera: {
        status: "not_loaded",
        devices_status: "not_loaded",
        devices_effective_status: "not_loaded",
        devices_endpoint_count: "0",
        devices_health_candidate_count: "0",
        devices_plain_hint: "相机设备列表未读到；先刷新页面状态或检查上位机相机健康检查。",
        preview_status: "idle_not_started",
        plain_hint: "画面未显示：页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作已经看到画面。共享预览不是页面独占；谁打开页面都接入同一条上游流，当前 0 个页面观看。下一步：打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。",
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
        shared_preview_access_plain: "共享预览不是页面独占；谁打开页面都接入同一条上游流，当前 0 个页面观看。",
        shared_preview_realtime_plain: "当前没有实时画面；页面会自动接入共享 MJPEG 预览；多个页面复用同一条上游流，未出帧前不当作画面可见。",
        shared_preview_shared_capture: "true",
        shared_preview_exclusive_camera_claim: "false",
        shared_preview_contract: "single_shared_capture_for_multiple_clients",
        shared_preview_multi_viewer_status: "single_upstream_multi_viewer",
        shared_preview_multi_viewer_plain: "多人实时预览共用单条上游流；谁打开页面都接入同一个共享 relay（小车地址未生成），当前 0 个页面观看，不会因为新页面进入而独占摄像头。",
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
        first_frame_probe_streamon_io_error_observed: "false",
        first_frame_probe_streamon_io_error_count: "0",
        first_frame_probe_latest_streamon_io_error: "none",
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
      radar: {
        status: "not_loaded",
        plain_hint: "雷达状态未加载；地图雷达点当前显示 0 个。下一步：确认小车地址可访问后刷新雷达状态和地图画面。",
        next_action_plain: "确认小车地址可访问后刷新雷达状态和地图画面。",
        radar_status_plain: "雷达状态未加载；地图雷达点当前显示 0 个。",
        radar_next_action_plain: "确认小车地址可访问后刷新雷达状态和地图画面。",
        lifecycle_running: "not_loaded",
        lifecycle_state: "not_loaded",
        continuous_scan_status: "not_loaded",
        latest_scan_proof_fresh: "not_loaded",
        runtime_scan_status: "not_loaded",
        scan_point_count: "0",
        scan_preview_point_count: "0",
        scan_preview_source_point_count: "0",
        scan_preview_frame_id: "not_loaded",
        radar_overlay_status: "not_loaded",
        radar_overlay_point_count: "0",
        radar_overlay_source_point_count: "0",
        radar_overlay_frame_id: "not_loaded",
        radar_overlay_source_frame_id: "not_loaded",
        radar_overlay_wysiwyg_status_plain: "地图雷达点未加载：当前显示 0 个点；来源点 0 个。地图雷达层未加载。",
        radar_overlay_wysiwyg_next_action_plain: "确认小车地址可访问后刷新地图画面。",
        radar_overlay_blocked_reasons: "not_loaded",
        radar_overlay_blocked_reason_labels: "not_loaded",
        map_marker_point_count: "0",
        map_marker_source_point_count: "0",
        map_marker_frame_id: "not_loaded",
        map_marker_source_frame_id: "not_loaded",
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
        plain_hint: "地图画面未读到；不能把旧图或空白图当作当前所见。图上路线未显示；不能把旧路线或空路线当作当前所见。地图雷达点未加载：当前显示 0 个点；来源点 0 个。地图雷达层未加载。下一步：先刷新地图画面。",
        next_action_plain: "先准备图上路线，再刷新地图画面。",
        map_current_visible: "false",
        path_current_visible: "false",
        radar_overlay_current_visible: "false",
        map_next_action_plain: "先刷新地图画面。",
        map_wysiwyg_status_plain: "地图画面未读到；不能把旧图或空白图当作当前所见。",
        map_wysiwyg_next_action_plain: "先刷新地图画面。",
        path_preview_status: "not_observed",
        path_preview_point_count: "0",
        path_preview_frame_id: "not_loaded",
        path_preview_next_action_plain: "先准备图上路线，再刷新地图画面。",
        path_wysiwyg_status_plain: "图上路线未显示；不能把旧路线或空路线当作当前所见。",
        path_wysiwyg_next_action_plain: "先准备图上路线，再刷新地图画面。",
        robot_pose_status: "not_loaded",
        radar_overlay_status: "not_loaded",
        radar_overlay_plain_hint: "地图雷达层未加载。",
        radar_overlay_wysiwyg_status_plain: "地图雷达点未加载：当前显示 0 个点；来源点 0 个。地图雷达层未加载。",
        radar_overlay_wysiwyg_next_action_plain: "确认小车地址可访问后刷新地图画面。",
        radar_overlay_next_action: "connect_robot_and_refresh_map_preview",
        radar_overlay_next_action_plain: "确认小车地址可访问后刷新地图画面。",
        radar_overlay_point_count: "0",
        radar_overlay_source_point_count: "0",
        radar_overlay_refresh_required: "true",
        radar_overlay_stale_source_points_suppressed: "false",
        radar_overlay_primary_blocked_reason: "not_loaded",
        radar_overlay_current_vs_source_plain: "地图雷达点：当前 0 个，来源 0 个；下一步：确认小车地址可访问后刷新地图画面。",
        radar_overlay_frame_id: "not_loaded",
        radar_overlay_source_frame_id: "not_loaded",
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
      nav2: notLoadedNav2Summary,
      keyboard: keyboardReadback,
      keyboard_control: keyboardReadback,
      keyboard_teleop: keyboardReadback,
      free_roam: {
        status: "not_loaded",
        runtime_status: "not_loaded",
        decision_state: "not_loaded",
        decision_reason: "not_loaded",
        stop_required: "not_loaded",
        stop_request_pending: "false",
        free_roam_stop_request_pending: "false",
        start_will_clear_stop_request: "false",
        start_clears_stop_request_not_blocking: "false",
        motion_start_blocked_by_stop_request: "false",
        stop_request_status_plain: "停止请求状态未读到；先连接上车自由移动状态机。",
        artifact_only: "not_loaded",
        cmd_vel_publish_enabled: "not_loaded",
        start_ready: "false",
        free_move_ready: "false",
        free_move_start_ready: "false",
        motion_start_ready: "false",
        free_roam_motion_start_ready: "false",
        free_move_without_camera_allowed: "false",
        motion_without_radar_allowed: "false",
        free_move_minimal_precheck_safety_only: "true",
        free_move_safety_confirm_required: "false",
        free_move_camera_preflight_required: "false",
        free_move_radar_preflight_required: "false",
        motion_ready: "false",
        free_roam_motion_ready: "false",
        mapping_start_ready: "false",
        free_roam_mapping_start_ready: "false",
        mapping_start_requires_camera_first_frame: "true",
        mapping_start_requires_lidar_fresh: "true",
        mapping_start_missing: "not_loaded",
        mapping_readiness_ready: "false",
        mapping_blocked_reasons: "not_loaded",
        mapping_missing_reasons: "not_loaded",
        free_roam_mapping_ready: "false",
        free_roam_mapping_missing_reasons: "not_loaded",
        mapping_ready: "false",
        mapping_missing: "not_loaded",
        plain_hint: "自由移动未就绪；先连接上车状态机并确认停止兜底。建图验收未就绪；还在等待上车状态机。下一步：先连接上车自由移动状态机，并确认停止兜底可用。",
        next_action_plain: "先连接上车自由移动状态机，并确认停止兜底可用",
        motion_readiness_plain: "自由移动未就绪；先连接上车状态机并确认停止兜底。",
        motion_sensor_dependency_status: "unknown_until_motion_ready",
        motion_sensor_dependency_plain: "自由移动启动条件未读到；相机、雷达和地图记录仍只作为建图验收材料。",
        free_move_start_status_plain: "自由移动暂不可启动；先连接上车自由移动状态机并确认停止兜底。",
        motion_runtime_status_plain: "当前未在自由移动运行态；上车自由移动状态机还未就绪。",
        mapping_acceptance_status_plain: "建图验收未就绪；还在等待上车状态机。",
        mapping_start_readiness_plain: "建图启动未就绪；还在等待上车自由移动状态机。",
        mapping_readiness_plain: "建图验收未就绪；还在等待上车状态机。",
        motion_next_action_plain: "先连接上车自由移动状态机，并确认停止兜底可用。",
        mapping_start_next_action_plain: "先连接上车自由移动状态机，并继续读取相机和雷达。",
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
  payload.camera_summary = payload.readback_summary.camera;
  payload.map_summary = payload.readback_summary.map;
  payload.radar_summary = payload.readback_summary.radar;
  payload.nav2_summary = payload.readback_summary.nav2;
  payload.keyboard_summary = payload.readback_summary.keyboard;
  payload.keyboard_control_summary = payload.readback_summary.keyboard_control;
  payload.keyboard_teleop_summary = payload.readback_summary.keyboard_teleop;
  payload.free_roam_summary = payload.readback_summary.free_roam;
  return payload;
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
  const radarStatusPayload = readbackById(readbacks, "radar_status")?.payload ?? null;
  const radarScanProofPayload = readbackById(readbacks, "radar_scan_proof_latest")?.payload ?? null;
  const radarLifecycleStopped = summaryValueText(radarStatusPayload, ["lifecycle_running"], "") === "false"
    || summaryValueText(radarStatusPayload, ["lifecycle_state"], "") === "stopped"
    || summaryValueText(radarStatusPayload, ["continuous_scan_status"], "") === "lifecycle_not_running"
    || ["lifecycle_not_running", "radar_stopped"].includes(summaryValueText(radarStatusPayload, ["status"], ""));
  const runtimeLidarFreshForMapping = runtimeLidarFreshFromSnapshot && !radarLifecycleStopped;
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
  const radarFreshValues = [
    summaryValueText(radarStatusPayload, ["latest_scan_proof_fresh"], ""),
    summaryValueText(radarScanProofPayload, ["latest_scan_proof_fresh"], ""),
  ].filter((value) => value !== "");
  const radarFreshReadbackLoaded = radarFreshValues.length > 0;
  const radarFreshProven = radarFreshValues.some((value) => value === "true");
  const runtimeLidarFreshGate = gateRows.find((gate) => gate.id === "lidar_fresh");
  if (runtimeLidarFreshGate && radarLifecycleStopped) {
    // runtime snapshot 可能是停止前留下的旧距离；雷达 lifecycle 已停时不能再作为建图启动 fresh 证据。
    runtimeLidarFreshGate.state = "not_proven";
    runtimeLidarFreshGate.evidence = "雷达未运行，旧 runtime scan 不能作为建图新鲜扫描";
    runtimeLidarFreshGate.next_action = "先启动雷达并等待新扫描，再刷新地图画面确认雷达点";
  } else if (runtimeLidarFreshGate && runtimeLidarFreshForMapping) {
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
    const lidarFreshReady = !radarLifecycleStopped && (runtimeLidarFreshForMapping || radarFreshProven);
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
  const mappingStartMissing = freeRoamRuntimeMissingList(latest.free_roam_mapping_start_missing_reasons);
  const mappingMissing = freeRoamRuntimeMissingList(latest.free_roam_mapping_missing_reasons ?? latest.mapping_missing_reasons);
  return {
    status: "loaded",
    state: asString(decision?.state, "not_loaded"),
    reason: asString(decision?.reason, "not_loaded"),
    stop_required: decision?.stop_required === true,
    artifact_only: latest.artifact_only !== false,
    cmd_vel_publish_enabled: latest.cmd_vel_publish_enabled === true,
    ...(mappingStartMissing.length > 0 ? { free_roam_mapping_start_missing_reasons: mappingStartMissing } : {}),
    ...(mappingMissing.length > 0 ? { free_roam_mapping_missing_reasons: mappingMissing } : {}),
  };
}

function normalizeFreeRoamMappingMissingId(value: string): string {
  // 上车端有时返回“未观测”状态词；summary 对外统一使用稳定 gate id。
  const normalized: Record<string, string> = {
    camera_first_frame_not_observed: "camera_first_frame",
    camera_health_unreachable: "camera_first_frame",
    radar_scan_proof_not_fresh: "lidar_fresh",
    lidar_not_fresh: "lidar_fresh",
  };
  return normalized[value] ?? value;
}

function freeRoamRuntimeMissingList(value: unknown): string[] {
  // runtime latest 已经给出短缺口时优先消费；空值和占位词表示未提供，不覆盖 gate fallback。
  const rawItems = Array.isArray(value)
    ? value
    : typeof value === "string"
      ? value.split(",")
      : [];
  return Array.from(new Set(rawItems
    .map((item) => asString(item, "").trim())
    .filter((item) => item && !["none", "not_loaded", "null", "undefined", "[]"].includes(item))
    .map(normalizeFreeRoamMappingMissingId)));
}

function freeRoamMappingMissingIds(
  freeRoamRuntimeGates: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_gates"] | null,
  freeRoamRuntime: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_runtime"] | null = null,
): string[] {
  // 自由移动不依赖相机/雷达；建图验收才需要这些材料同时就绪。
  const remoteMissing = freeRoamRuntimeMissingList((freeRoamRuntime as unknown as JsonRecord | null)?.free_roam_mapping_missing_reasons);
  if (remoteMissing.length > 0) {
    return remoteMissing;
  }
  const mappingGateById = new Map((freeRoamRuntimeGates ?? [])
    .filter((gate) => gate.scope === "mapping_acceptance")
    .map((gate) => [gate.id, gate]));
  return FREE_ROAM_MAPPING_ACCEPTANCE_REQUIRED_IDS.filter((id) => mappingGateById.get(id)?.state !== "ready");
}

function freeRoamMappingStartMissingIds(
  freeRoamRuntimeGates: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_gates"] | null,
  freeRoamRuntime: RobotControlSummaryResponse["safe_command_boundary"]["free_roam_autonomy_runtime"] | null = null,
): string[] {
  // 建图启动只看传感器入口；地图记录和地图画面属于启动后的验收材料。
  const remoteStartMissing = freeRoamRuntimeMissingList((freeRoamRuntime as unknown as JsonRecord | null)?.free_roam_mapping_start_missing_reasons);
  if (remoteStartMissing.length > 0) {
    return remoteStartMissing;
  }
  const mappingGateById = new Map((freeRoamRuntimeGates ?? [])
    .filter((gate) => gate.scope === "mapping_acceptance")
    .map((gate) => [gate.id, gate]));
  return FREE_ROAM_MAPPING_START_REQUIRED_IDS.filter((id) => mappingGateById.get(id)?.state !== "ready");
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
  manualMotionFallbackActive = false,
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
      ? "停止请求会在开始自由移动时自动解除，不作为启动阻塞；勾选现场安全确认后可先自由移动"
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
  if (manualMotionFallbackActive) {
    return "可先勾选现场安全确认，用键盘或低速手控移动；要启动上车自由移动状态机，先连接状态机并确认停止兜底";
  }
  return "先连接上车自由移动状态机，并确认停止兜底可用";
}

function freeRoamMotionNextAction(startReady: boolean, motionReady: boolean, externalStopRequested: boolean, manualMotionFallbackActive = false): string {
  // 自由移动只看安全确认和停止兜底；相机/雷达/地图记录只影响建图验收，不该写成不能动。
  if (motionReady) {
    return "自由移动运行中；需要收口时点击停止自由移动或红色停止。";
  }
  if (startReady) {
    const stopPrefix = externalStopRequested
      ? "停止请求会在开始自由移动时自动解除，不作为启动阻塞。"
      : "";
    return `${stopPrefix}勾选现场安全确认后可先自由移动；相机和雷达只影响建图验收。`;
  }
  if (manualMotionFallbackActive) {
    return "上车自由移动状态机未加载；可先勾选现场安全确认，用键盘或低速手控移动；相机和雷达只影响建图。";
  }
  return "先连接上车自由移动状态机，并确认停止兜底可用。";
}

function freeRoamMotionReadinessPlain(startReady: boolean, motionReady: boolean, externalStopRequested: boolean, manualMotionFallbackActive = false): string {
  // 这句只回答“能不能先自己低速移动”，不夹带建图传感器缺口，方便首屏和脚本直接展示。
  if (motionReady) {
    return "自由移动正在运行；相机和雷达不作为继续移动的前置。";
  }
  if (startReady) {
    return externalStopRequested
      ? "可先自由移动；停止请求会在开始时自动解除，不作为启动阻塞。"
      : "可先自由移动；只需要现场安全确认和停止兜底。";
  }
  if (manualMotionFallbackActive) {
    return "可先低速移动；上车自由移动状态机未加载时，先用键盘或低速手控，画面和雷达只影响建图。";
  }
  return "自由移动未就绪；先连接上车状态机并确认停止兜底。";
}

function freeRoamStartStatusPlain(startReady: boolean, motionReady: boolean, externalStopRequested: boolean, manualMotionFallbackActive = false): string {
  // 和独立 latest endpoint 保持同一层语义：motion_ready=false 只说明未运行，不代表 start 被阻塞。
  if (motionReady) {
    return "自由移动已启动；继续保持现场可接管，必要时点击停止。";
  }
  if (startReady) {
    return externalStopRequested
      ? "自由移动可启动；点击开始会先清除停止请求，不作为启动阻塞。"
      : "自由移动可启动；只需现场安全确认和停止兜底。";
  }
  if (manualMotionFallbackActive) {
    return "上车自由移动状态机未加载；可先用键盘或低速手控移动。";
  }
  return "自由移动暂不可启动；先连接上车自由移动状态机并确认停止兜底。";
}

function freeRoamMotionRuntimeStatusPlain(startReady: boolean, motionReady: boolean): string {
  // 运行态和启动门禁分开写，避免现场把未运行误判为不能启动。
  if (motionReady) {
    return "自由移动正在运行并发布低速运动；继续监看现场，必要时点击停止。";
  }
  if (startReady) {
    return "当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。";
  }
  return "当前未在自由移动运行态；上车自由移动状态机还未就绪。";
}

function freeRoamMappingReadinessPlain(startReady: boolean, mappingReady: boolean, mappingMissingReasons: string[]): string {
  // 建图是验收条件；只有画面、雷达、地图记录和地图画面都就绪时才说可按建图记录。
  if (mappingReady) {
    return "建图验收已就绪：画面、雷达、地图记录和地图画面都可用。";
  }
  const missingText = freeRoamMissingPlainLabels(mappingMissingReasons).join("、");
  if (!startReady) {
    return missingText
      ? `建图验收未就绪；还差：${missingText}。`
      : "建图验收未就绪；还在等待上车状态机。";
  }
  return missingText
    ? `建图验收未就绪；还差：${missingText}；不影响先低速自由移动。`
    : "建图验收材料还在读取；不影响先低速自由移动。";
}

function freeRoamMappingStartReadinessPlain(startReady: boolean, mappingStartReady: boolean, mappingStartMissingReasons: string[]): string {
  // 启动建图和验收建图分开说：相机/雷达就绪后就可以进建图记录，地图画面等完成后再验收。
  if (mappingStartReady) {
    return "建图启动已就绪：画面首帧和雷达新鲜都可用；地图记录和地图画面用于建图验收。";
  }
  const missingText = freeRoamMissingPlainLabels(mappingStartMissingReasons).join("、");
  if (!startReady) {
    return missingText
      ? `建图启动未就绪；还差：${missingText}；同时等待上车自由移动状态机。`
      : "建图启动未就绪；还在等待上车自由移动状态机。";
  }
  return missingText
    ? `建图启动未就绪；还差：${missingText}；地图记录和地图画面只影响建图验收。`
    : "建图启动材料还在读取；地图记录和地图画面只影响建图验收。";
}

function freeRoamMappingStartNextAction(startReady: boolean, mappingStartReady: boolean, mappingStartMissingReasons: string[]): string {
  // 给普通页面一个直接动作：先补齐相机/雷达，再由按钮显式启动建图记录。
  if (mappingStartReady) {
    return "相机和雷达已满足建图启动；勾选现场安全确认后可启动建图记录，再看地图画面完成验收。";
  }
  const missingText = freeRoamMissingPlainLabels(mappingStartMissingReasons).join("、");
  if (!startReady) {
    return missingText
      ? `先连接上车自由移动状态机；建图启动还差：${missingText}。`
      : "先连接上车自由移动状态机，并继续读取相机和雷达。";
  }
  return missingText
    ? `先补齐建图启动材料：${missingText}；低速自由移动不受影响。`
    : "继续读取相机和雷达；低速自由移动不受影响。";
}

function freeRoamMappingNextAction(startReady: boolean, mappingReady: boolean, mappingMissingReasons: string[]): string {
  // 建图验收单独解释缺口，让脚本不用从“能动”的下一步里反推传感器条件。
  if (mappingReady) {
    return "建图验收已就绪；继续低速监看地图、雷达和画面。";
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
  const pathVisibleOnMap = (proof?.path_preview_point_count ?? 0) > 0;
  const robotPoseVisibleOnMap = Boolean(proof?.robot_pose);
  const readyLabel = pathVisibleOnMap && robotPoseVisibleOnMap
    ? "图上路线和小车位置已显示，等待安全确认"
    : pathVisibleOnMap
      ? "图上路线已显示，等待安全确认"
      : "路线读数已准备，等待地图画面确认";
  const poseHint = proof?.robot_pose ? "" : "；小车位置未显示时建议先重新定位或刷新地图";
  return {
    nav2_goal_ready: ready,
    nav2_goal_label: ready ? readyLabel : "图上路线未就绪",
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
  const nav2CurrentBlockers = nav2.current_blocker_reasons
    .split(",")
    .map((reason) => reason.trim())
    .filter((reason) => reason && reason !== "none" && reason !== "not_loaded");
  // no-motion planner proof 会在生成路线后清理 managed runtime；execute endpoint 会托管启动 runtime，不能因此挡住已读到的路线。
  const nav2StackBlocksGoal = nav2StackNotRunning && !base.nav2_goal_ready;
  const managedRuntimeAutostarts = nav2LifecycleBlocked && base.nav2_goal_ready && !nav2StackBlocksGoal;
  const safeBoundaryCurrentBlockers = nav2CurrentBlockers.filter((reason) => {
    // 可执行路线由 execute 端托管启动 runtime；这时 lifecycle stopped 只应作为提示，不能继续出现在发车 blocker 里。
    if (managedRuntimeAutostarts && reason === "nav2_lifecycle_not_running") {
      return false;
    }
    return true;
  });
  const plannerBlocksGoal = !nav2StackBlocksGoal && plannerInactive && (!base.nav2_goal_ready || !nav2StackNotRunning);
  const controllerBlocksGoal = !nav2StackBlocksGoal && controllerInactive && controllerRequested;
  const serviceAwareBlockers = [
    ...base.nav2_goal_blockers,
    ...safeBoundaryCurrentBlockers,
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
  const managedRuntimeHint = managedRuntimeAutostarts
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
        : `勾选行程前安全确认后用 ${rerunMode} 重跑图上路线${managedRuntimeHint}，并复验 wheel raw L/R`;
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
  const boundaryBlockerLabels = nav2.current_blocker_labels && nav2.current_blocker_labels !== "not_loaded"
    ? nav2.current_blocker_labels.split("、").map((label) => label.trim()).filter(Boolean)
    : [];
  const blockedNextAction = nav2BlockedNextActionPlain(boundaryBlockerLabels);
  const fallbackNextAction = inactiveServiceNames.length
    ? `先${nav2StackNotRunning ? "启动" : "恢复"}${joinChineseList(inactiveServiceNames)}，再生成图上路线`
    : blockedNextAction || base.nav2_goal_next_action;
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
  manualMotionFallbackReady = false,
): RobotControlSummaryResponse["safe_command_boundary"] {
  // 控制边界集中在后端返回，避免前端以后误加 enabled 状态。
  const startGates = (freeRoamRuntimeGates ?? []).filter((gate) => gate.id === "stop_available");
  const stopFallbackReady = startGates.length === 0 || startGates.every((gate) => gate.state === "ready");
  const freeRoamStartReady = Boolean(
    freeRoamRuntime?.status === "loaded"
    && stopFallbackReady,
  );
  const freeRoamMotionStartReady = freeRoamStartReady || manualMotionFallbackReady;
  const manualMotionFallbackActive = !freeRoamStartReady && manualMotionFallbackReady;
  const freeRoamReady = Boolean(
    freeRoamRuntime?.status === "loaded"
    && freeRoamRuntime.cmd_vel_publish_enabled
    && stopFallbackReady,
  );
  const freeRoamMappingMissingReasons = freeRoamMappingMissingIds(freeRoamRuntimeGates, freeRoamRuntime);
  const freeRoamMappingStartMissingReasons = freeRoamMappingStartMissingIds(freeRoamRuntimeGates, freeRoamRuntime);
  const freeRoamMappingStartReady = freeRoamStartReady && freeRoamMappingStartMissingReasons.length === 0;
  const freeRoamMappingReady = freeRoamStartReady && freeRoamMappingMissingReasons.length === 0;
  const freeRoamStatus = freeRoamReady ? "ready" : freeRoamStartReady ? "start_ready" : "locked";
  const freeRoamNextAction = freeRoamAutonomyNextAction(freeRoamStatus, freeRoamMappingReady, freeRoamMappingMissingReasons, freeRoamRuntime, manualMotionFallbackActive);
  const keyboardNextAction = "勾选现场安全确认后点击启用键盘；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停";
  const keyboardStopTriggers = ["key_released", "window_blur", "page_hidden", "direction_changed", "button_stop"];
  const nav2MinimalPrecheckPlain = "执行图上路线只要求现场安全确认；固定白名单是代理护栏，不是普通用户额外预检；相机、雷达和现场报告不作为发车前额外预检。";
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
    free_roam_motion_start_ready: freeRoamMotionStartReady,
    free_roam_mapping_start_ready: freeRoamMappingStartReady,
    free_roam_mapping_start_missing_reasons: freeRoamMappingStartMissingReasons,
    free_roam_mapping_ready: freeRoamMappingReady,
    free_roam_mapping_missing_reasons: freeRoamMappingMissingReasons,
    free_roam_autonomy_label: freeRoamReady
      ? freeRoamMappingReady ? "自动扫图" : "自由移动（运行中）"
      : freeRoamStartReady
        ? "自由移动（勾确认后可启动）"
        : "自动扫图（未开放）",
    free_roam_autonomy_next_action: freeRoamNextAction,
    free_roam_motion_minimal_precheck_plain: "自由移动只要求现场安全确认和停止兜底；相机、雷达、地图记录只影响建图验收。",
    free_roam_mapping_start_plain: freeRoamMappingStartReadinessPlain(freeRoamStartReady, freeRoamMappingStartReady, freeRoamMappingStartMissingReasons),
    free_roam_mapping_start_next_action: freeRoamMappingStartNextAction(freeRoamStartReady, freeRoamMappingStartReady, freeRoamMappingStartMissingReasons),
    free_roam_mapping_acceptance_plain: "建图验收要求画面首帧、雷达新鲜、地图记录和地图画面就绪；这些缺口不阻止先低速自由移动。",
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
      mapping_start_required_gates: [
        "camera_first_frame",
        "fresh_radar_scan",
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
  // operator summary 使用 "true; ref=..." 表达可追溯材料；not_loaded 不能被当成就绪。
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
    continuous_control_ready: "true",
    keyboard_control_start_ready: "true",
    keyboard_continuous_control_ready: "true",
    hold_to_move_required: "true",
    keyboard_hold_to_move_required: "true",
    enabled: "false",
    keyboard_enabled: "false",
    keyboard_motion_verified: "false",
    keyboard_continuous_pulse_verified: "false",
    keyboard_current_hold_pulse_count: "0",
    keyboard_best_continuous_pulse_count: "0",
    keyboard_verified_min_forwarded_pulses: "2",
    keyboard_safety_confirm_required: "true",
    minimal_precheck_safety_only: "true",
    plain_hint: plainHint,
    readiness_plain: readinessPlain,
    continuous_control_contract_plain: `按住时约每 ${ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS / 1000} 秒发送一次 ${ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS / 1000} 秒 ROS 低速脉冲；松开、失焦、切页、换方向或点击停止都会停。`,
    hold_to_move_plain: holdToMovePlain,
    stop_triggers_plain: "松开按键、窗口失焦、页面隐藏、切换方向或点击停止都会发送停止请求。",
    pulse_timing_plain: `按住时约每 ${ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS / 1000} 秒发送一次 ${ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS / 1000} 秒低速脉冲。`,
    wheel_feedback_acceptance_plain: "键盘连续手控验收只看同一次按住窗口的 manual pulse 回包：需要读到 wheel L/R 非零；全局只读采样或旧材料不能替代本次按住读数。",
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

function plainFactWithoutLeadingLabel(value: string, label: string): string {
  // 总览外层已经带了分组名；这里去掉内层重复前缀，避免“建图启动：建图启动未就绪”。
  return value
    .replace(new RegExp(`^${label}[：:]?`), "")
    .trim();
}

function currentFactMapRadarParts(
  mapStatus: string,
  radarStatus: string,
): { map: string; radar: string } {
  // 地图主句如果已经用分号追加了雷达诊断，顶层事实改由雷达 summary 专门说明，避免旧来源点和当前雷达点重复出现。
  const map = plainFactPart(mapStatus);
  const radar = plainFactPart(radarStatus);
  if (!map || !radar) {
    return { map, radar };
  }
  if (map.includes("；雷达")) {
    return { map: map.split("；雷达")[0] ?? map, radar };
  }
  if (map.includes("雷达标记都已按当前读数显示")) {
    return { map: map.replace(/和雷达标记都已按当前读数显示/g, "都已按当前读数显示"), radar };
  }
  return { map, radar };
}

function currentFactCameraPart(cameraStatus: string): string {
  // 顶层总事实面向普通用户和现场脚本；保留底层 readback 原文，只在这里把“可见”改成更口语的“显示/看到”。
  return plainFactPart(cameraStatus)
    .replace(/画面未可见/g, "画面未显示")
    .replace(/画面已可见/g, "已经看到画面")
    .replace(/不当作画面可见/g, "不当作已经看到画面");
}

function summaryCurrentFactPlain(
  readback: RobotControlSummaryResponse["readback_summary"],
  boundary: RobotControlSummaryResponse["safe_command_boundary"],
): string {
  // 这是给脚本和外部面板的一句话事实；Vue 仍保留本地 pending 态的更细实时文案。
  const camera = currentFactCameraPart(readback.camera.camera_wysiwyg_status_plain);
  const { map, radar } = currentFactMapRadarParts(
    readback.map.map_wysiwyg_status_plain,
    readback.radar.plain_hint || readback.radar.radar_overlay_wysiwyg_status_plain,
  );
  const nav2 = plainFactPart(readback.nav2.plain_hint || readback.nav2.execution_status_plain || readback.nav2.route_execution_readiness_plain);
  const keyboard = plainFactPart(readback.keyboard.hold_to_move_plain || readback.keyboard.readiness_plain);
  const freeMove = plainFactPart(readback.free_roam.motion_readiness_plain);
  const mappingStart = plainFactPart(readback.free_roam.mapping_start_readiness_plain);
  const mapping = plainFactPart(readback.free_roam.mapping_readiness_plain);
  const minimal = plainFactPart(boundary.nav2_goal_minimal_precheck_plain);
  const parts = [
    camera,
    map,
    radar,
    nav2 ? `自动驾驶：${nav2}` : "",
    keyboard ? `键盘：${keyboard}` : "",
    freeMove ? `自由移动：${freeMove}` : "",
    mappingStart ? `建图启动：${plainFactWithoutLeadingLabel(mappingStart, "建图启动")}` : "",
    mapping ? `建图验收：${plainFactWithoutLeadingLabel(mapping, "建图验收")}` : "",
    minimal ? `发车前：${minimal}` : "",
  ].filter(Boolean);
  return parts.length > 0
    ? `${parts.join("；")}。`
    : "当前事实未读到；先确认小车地址和上位机 Robot API。";
}

function actionCardText(value: string | undefined, fallback: string): string {
  // 动作卡只吃后端已清洗的 plain 字段；占位 token 不进入普通用户首屏。
  return plainFactPart(value, fallback) || fallback;
}

function actionCardNumber(value: string | undefined): number {
  // 结构化卡片要给脚本稳定数字；not_loaded/空值一律 fail closed 成 0。
  const parsed = Number(value ?? "");
  return Number.isFinite(parsed) ? parsed : 0;
}

function actionCardReasonList(value: string | undefined): string[] {
  // 后端 readback 用逗号字符串兼容旧接口；新卡片里拆回数组，便于验收脚本逐项判断。
  const compact = (value ?? "").trim();
  if (!compact || compact === "none" || compact === "not_loaded") {
    return [];
  }
  return compact
    .split(",")
    .map((item) => item.trim().replace(/map_radar_overlay|radar_overlay/g, "map_radar_points"))
    .filter(Boolean);
}

function actionCardLabelList(value: string | undefined): string[] {
  // 中文标签通常用顿号拼接；也兼容逗号，避免现场脚本还要理解后端展示文案格式。
  const compact = (value ?? "").trim();
  if (!compact || compact === "none" || compact === "not_loaded") {
    return [];
  }
  return compact
    .split(/[、,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function actionCardBoolean(value: string | undefined, fallback = false): boolean {
  // readback_summary 为兼容脚本使用字符串；动作卡 evidence 要给 DOM/脚本稳定布尔值。
  if (value === "true") return true;
  if (value === "false") return false;
  return fallback;
}

function nav2ControllerIdleReasonPlain(nav2: RobotControlSummaryResponse["readback_summary"]["nav2"]): string {
  // controller 只有在被请求执行目标时才应 active；未请求时 inactive 是空闲事实，不应误写成自动驾驶 blocker。
  if (nav2.controller_server_active === "false" && nav2.controller_server_requested === "false") {
    return "控制服务当前未被请求，属于等待重跑的空闲读数，不是当前自动驾驶阻塞。";
  }
  if (nav2.controller_server_active === "false" && nav2.controller_server_requested === "true") {
    return "控制服务已被请求但当前未运行，重跑前需要先恢复控制服务。";
  }
  if (nav2.controller_server_active === "true") {
    return "控制服务当前已运行。";
  }
  return "控制服务当前状态未读到。";
}

function mapWysiwygVisibleFromPlain(statusPlain: string): boolean {
  // 地图目标只验收地图画面本身；图上路线、车位和雷达点有独立目标项，不能把它们的缺口反算成地图不可见。
  const plain = plainFactPart(statusPlain).trim();
  if (!plain || /^(当前)?地图画面未(读到|显示|加载)/.test(plain) || /^当前地图未显示/.test(plain)) {
    return false;
  }
  return /地图画面.*(已显示|已读到|已按当前读数显示)/.test(plain);
}

function buildActionStatusCards(
  readback: RobotControlSummaryResponse["readback_summary"],
  boundary: RobotControlSummaryResponse["safe_command_boundary"],
): RobotControlSummaryResponse["action_status_cards"] {
  // 这些卡片是首屏“现在能做什么”的结构化摘要，不新增任何控制能力或放行条件。
  const cameraVisible = readback.camera.camera_wysiwyg_status_plain.startsWith("画面已可见");
  const cameraSourceFirstFrameReady = readback.camera.source_readiness === "first_frame_observed"
    || cameraVisible
    || actionCardBoolean(readback.camera.first_frame_probe_read_ok, false)
    || actionCardBoolean(readback.camera.first_frame_probe_visible_content_proven, false);
  const mapVisible = mapWysiwygVisibleFromPlain(readback.map.map_wysiwyg_status_plain);
  const mapPathVisible = readback.map.path_preview_status === "path_preview_observed";
  const mapRobotPoseVisible = readback.map.robot_pose_status === "map_pose_observed";
  const mapNextActionPlain = mapVisible
    ? "地图画面已显示；继续确认图上路线和小车位置，雷达点另看“地图雷达点”。"
    : actionCardText(readback.map.map_wysiwyg_next_action_plain, "刷新地图画面");
  const radarPointCount = Number(readback.radar.map_marker_point_count || readback.radar.radar_overlay_point_count || "0");
  const radarCurrent = Number.isFinite(radarPointCount) && radarPointCount > 0 && ["loaded", "partial"].includes(readback.radar.radar_overlay_status);
  const radarCurrentPointCount = actionCardNumber(readback.radar.map_marker_point_count || readback.radar.radar_overlay_point_count);
  const radarSourcePointCount = actionCardNumber(readback.radar.map_marker_source_point_count || readback.radar.radar_overlay_source_point_count);
  const radarSummaryPlain = radarCurrent
    ? readback.radar.radar_overlay_wysiwyg_status_plain
    : readback.radar.plain_hint || readback.radar.radar_status_plain;
  const radarNextActionPlain = radarCurrent
    ? readback.radar.radar_overlay_wysiwyg_next_action_plain || readback.radar.radar_map_overlay_next_action_plain
    : readback.radar.radar_next_action_plain || readback.radar.radar_overlay_wysiwyg_next_action_plain;
  const mappingStartMissingReasons = boundary.free_roam_mapping_start_missing_reasons;
  const mappingLidarFreshReady = !mappingStartMissingReasons.includes("lidar_fresh");
  const mappingLidarLifecycleRunning = readback.lidar.lifecycle_running === "true";
  const mappingRuntimeScanFresh = readback.lidar.runtime_scan_status === "fresh";
  const mappingRuntimeScanDiagnosticOnly = mappingRuntimeScanFresh && !mappingLidarFreshReady;
  const mappingLidarFreshBlockedByLifecycle = mappingStartMissingReasons.includes("lidar_fresh")
    && readback.lidar.lifecycle_running === "false";
  const nav2NeedsWheelRerun = boundary.nav2_goal_wheel_feedback_status === "goal_succeeded_but_wheel_lr_zero";
  const nav2ManagedRuntimeRequested = actionCardBoolean(readback.nav2.goal_execution_managed_runtime_requested, false);
  const nav2ManagedRuntimeStarted = actionCardBoolean(readback.nav2.goal_execution_managed_runtime_started, false);
  const nav2ManagedRuntimeLifecycleReadyOk = actionCardBoolean(readback.nav2.goal_execution_managed_runtime_lifecycle_ready_ok, false);
  const nav2ManagedRuntimeCleanupOk = actionCardBoolean(readback.nav2.goal_execution_managed_runtime_cleanup_ok, false);
  const nav2ManagedRuntimeAutostart = nav2ManagedRuntimeRequested
    || nav2ManagedRuntimeStarted
    || nav2ManagedRuntimeLifecycleReadyOk
    || boundary.nav2_goal_ready;
  const nav2ControllerIdleNotBlocking = readback.nav2.controller_server_active === "false"
    && readback.nav2.controller_server_requested === "false";
  const nav2ControllerBlockingCurrentGoal = readback.nav2.controller_server_active === "false"
    && readback.nav2.controller_server_requested === "true";
  const nav2ControllerIdleReason = nav2ControllerIdleReasonPlain(readback.nav2);
  const freeRoamStopRequestPendingValue = readback.free_roam.free_roam_stop_request_pending !== "not_loaded"
    ? readback.free_roam.free_roam_stop_request_pending
    : readback.free_roam.stop_request_pending;
  const freeRoamStopRequestPending = freeRoamStopRequestPendingValue === "true"
    || (freeRoamStopRequestPendingValue !== "false"
      && (readback.free_roam.stop_required === "true" || readback.free_roam.decision_state === "stopping"));
  const freeRoamStartWillClearStopRequest = readback.free_roam.start_will_clear_stop_request === "true"
    || (freeRoamStopRequestPending && boundary.free_roam_motion_start_ready);
  const freeRoamMotionBlockedByStopRequest = readback.free_roam.motion_start_blocked_by_stop_request === "true";
  return [
    {
      id: "camera_preview",
      title: "画面",
      status: cameraVisible ? "visible" : "not_visible",
      status_label: cameraVisible ? "已显示" : "未显示",
      summary_plain: actionCardText(currentFactCameraPart(readback.camera.camera_wysiwyg_status_plain), "画面状态未读到"),
      next_action_plain: actionCardText(readback.camera.camera_wysiwyg_next_action_plain, "打开共享预览或复测首帧"),
      wysiwyg_status: cameraVisible ? "visible_frame" : "no_current_frame",
      requires_safety_confirmation: false,
      can_start_after_safety_confirm: false,
      sends_motion_when_clicked: false,
      blocks_free_motion: false,
      blocks_mapping_start: !cameraSourceFirstFrameReady,
      evidence: {
        camera_current_frame_visible: cameraVisible,
        camera_source_first_frame_ready: cameraSourceFirstFrameReady,
        camera_source_readiness: readback.camera.source_readiness,
        camera_blocks_mapping_start: !cameraSourceFirstFrameReady,
        shared_preview_multi_viewer: readback.camera.shared_preview_multi_viewer_status === "single_upstream_multi_viewer",
        shared_capture: actionCardBoolean(readback.camera.shared_preview_shared_capture, true),
        exclusive_camera_claim: actionCardBoolean(readback.camera.shared_preview_exclusive_camera_claim, false),
        source_first_frame_failed: readback.camera.status === "source_first_frame_failed" || readback.camera.source_readiness === "first_frame_failed",
        source_diagnosis_status: readback.camera.source_diagnosis_status,
        source_diagnosis_not_exclusive: actionCardBoolean(readback.camera.source_diagnosis_not_exclusive, false),
        source_failure_reason: readback.camera.source_failure_reason,
        shared_preview_upstream_active: actionCardBoolean(readback.camera.shared_preview_upstream_active, false),
        shared_preview_content_type_loaded: actionCardBoolean(readback.camera.shared_preview_content_type_loaded, false),
        shared_preview_last_failure_reason: readback.camera.shared_preview_last_failure_reason,
        shared_preview_last_remote_http_status: readback.camera.shared_preview_last_remote_http_status,
        last_offer_failure_reason: readback.camera.last_offer_failure_reason,
        last_offer_format_attempts_summary: readback.camera.last_offer_format_attempts_summary,
        first_frame_probe_read_ok: actionCardBoolean(readback.camera.first_frame_probe_read_ok, false),
        visible_content_proven: actionCardBoolean(readback.camera.first_frame_probe_visible_content_proven, cameraVisible),
        shared_preview_client_count: actionCardNumber(readback.camera.shared_preview_client_count),
        shared_preview_cached_frame_loaded: actionCardBoolean(readback.camera.shared_preview_cached_frame_loaded, false),
        fixed_shared_preview_endpoint: "/api/robot-control/camera/mjpeg",
        fixed_shared_preview_status_endpoint: "/api/robot-control/camera/mjpeg/status",
        auto_joins_shared_preview: true,
        shared_preview_single_upstream: readback.camera.shared_preview_multi_viewer_status === "single_upstream_multi_viewer",
      },
    },
    {
      id: "map_preview",
      title: "地图",
      status: mapVisible ? "visible" : "not_visible",
      status_label: mapVisible ? "已显示" : "未显示",
      summary_plain: actionCardText(readback.map.map_wysiwyg_status_plain, "地图画面未读到"),
      next_action_plain: mapNextActionPlain,
      wysiwyg_status: mapVisible ? "current_map_visible" : "map_not_visible",
      requires_safety_confirmation: false,
      can_start_after_safety_confirm: false,
      sends_motion_when_clicked: false,
      blocks_free_motion: false,
      blocks_mapping_start: false,
      evidence: {
        map_current_visible: mapVisible,
        map_free_cell_count: actionCardNumber(readback.map.map_free_cell_count),
        path_visible_on_map: mapPathVisible,
        path_point_count: actionCardNumber(readback.map.path_preview_point_count),
        path_frame_id: readback.map.path_preview_frame_id || "not_loaded",
        robot_pose_visible: mapRobotPoseVisible,
        radar_points_visible_on_map: radarCurrent,
        radar_point_count_on_map: radarCurrent ? radarCurrentPointCount : 0,
      },
    },
    {
      id: "radar_map_points",
      title: "地图雷达点",
      status: radarCurrent ? "current_on_map" : "not_current",
      status_label: radarCurrent ? "已贴图" : "未贴当前图",
      summary_plain: actionCardText(radarSummaryPlain, "地图雷达点状态未读到"),
      next_action_plain: actionCardText(radarNextActionPlain, "启动雷达并刷新地图画面"),
      wysiwyg_status: radarCurrent ? "current_points_visible" : "old_or_missing_points_not_drawn",
      requires_safety_confirmation: false,
      can_start_after_safety_confirm: false,
      sends_motion_when_clicked: false,
      blocks_free_motion: false,
      blocks_mapping_start: !radarCurrent,
      evidence: {
        current_on_map: radarCurrent,
        current_point_count: radarCurrent ? radarCurrentPointCount : 0,
        source_point_count: radarSourcePointCount,
        frame_id: radarCurrent ? readback.radar.map_marker_frame_id || readback.radar.radar_overlay_frame_id || "not_loaded" : "not_loaded",
        source_frame_id: readback.radar.map_marker_source_frame_id || readback.radar.radar_overlay_source_frame_id || "not_loaded",
        blocked_reasons: actionCardReasonList(readback.radar.radar_overlay_blocked_reasons),
        radar_lifecycle_running: readback.radar.lifecycle_running === "true",
        radar_lifecycle_state: readback.radar.lifecycle_state,
        map_radar_status: readback.radar.radar_overlay_status,
        map_radar_point_count: actionCardNumber(readback.radar.radar_overlay_point_count),
        map_radar_source_point_count: actionCardNumber(readback.radar.radar_overlay_source_point_count),
        map_radar_blocked_by_lifecycle_not_running: actionCardReasonList(readback.radar.radar_overlay_blocked_reasons)
          .some((reason) => reason.includes("radar_lifecycle_not_running")) || readback.radar.lifecycle_running === "false",
        runtime_scan_status: readback.lidar.runtime_scan_status,
        runtime_scan_fresh: readback.lidar.runtime_scan_status === "fresh",
        runtime_scan_point_count: actionCardNumber(readback.lidar.scan_preview_point_count),
        runtime_scan_source_point_count: actionCardNumber(readback.lidar.scan_preview_source_point_count),
        runtime_scan_frame_id: readback.lidar.scan_preview_frame_id,
        runtime_scan_age_s: readback.lidar.runtime_lidar_age_s,
        runtime_scan_source: readback.lidar.runtime_scan_source,
        latest_scan_proof_fresh: actionCardBoolean(readback.radar.latest_scan_proof_fresh, false),
        radar_scan_observation_status: readback.radar.radar_scan_observation_status,
        radar_scan_observation_missing_reasons: actionCardReasonList(readback.radar.radar_scan_observation_missing_reasons),
        map_radar_readiness_status: readback.radar.radar_map_overlay_readiness_status,
        map_radar_next_action_plain: readback.radar.radar_map_overlay_next_action_plain,
        map_radar_blocked_reason_labels: actionCardLabelList(readback.radar.radar_overlay_blocked_reason_labels),
        driver_diagnostics_status: readback.radar.driver_diagnostics_status,
        driver_diagnostics_next_action_plain: readback.radar.driver_diagnostics_next_action_plain,
        driver_serial_bytes_read_total: readback.radar.driver_serial_bytes_read_total,
        driver_serial_packet_count_total: readback.radar.driver_serial_packet_count_total,
        driver_serial_empty_read_count: readback.radar.driver_serial_empty_read_count,
        driver_published_scan_count: readback.radar.driver_published_scan_count,
        radar_start_configured: readback.lidar.radar_start_configured !== "false",
        fixed_radar_start_endpoint: "/api/robot-control/radar/start",
        fixed_radar_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh",
        fixed_radar_map_preview_endpoint: "/api/robot-control/map/preview",
        radar_refresh_after_start_required: !radarCurrent,
        radar_map_points_loaded_required: true,
        radar_map_point_count_gt_zero_required: true,
      },
    },
    {
      id: "nav2_route",
      title: "图上路线",
      status: boundary.nav2_goal_ready ? (nav2NeedsWheelRerun ? "ready_needs_wheel_rerun" : "ready") : "not_ready",
      status_label: boundary.nav2_goal_ready ? (nav2NeedsWheelRerun ? "可重跑复验" : "可执行") : "未就绪",
      summary_plain: nav2ControllerIdleNotBlocking
        ? `${actionCardText(readback.nav2.route_execution_readiness_plain || readback.nav2.execution_status_plain, "图上路线状态未读到")}；${nav2ControllerIdleReason}`
        : actionCardText(readback.nav2.route_execution_readiness_plain || readback.nav2.execution_status_plain, "图上路线状态未读到"),
      next_action_plain: actionCardText(boundary.nav2_goal_next_action_plain || readback.nav2.next_action_plain, "准备图上路线"),
      wysiwyg_status: boundary.nav2_goal_ready ? "route_ready_on_map" : "route_not_ready",
      requires_safety_confirmation: true,
      can_start_after_safety_confirm: boundary.nav2_goal_ready,
      sends_motion_when_clicked: true,
      blocks_free_motion: false,
      blocks_mapping_start: false,
      evidence: {
        route_ready_on_map: boundary.nav2_goal_ready,
        minimal_precheck_safety_only: true,
        fixed_execute_proxy_endpoint: "/api/robot-control/nav2/goal/execute",
        execute_sends_motion_when_ready: boundary.nav2_goal_ready,
        requires_same_window_wheel_lr_nonzero: true,
        wheel_feedback_status: boundary.nav2_goal_wheel_feedback_status,
        goal_execution_proven: actionCardBoolean(readback.nav2.goal_execution_proven, false),
        goal_execution_hil_pass: actionCardBoolean(readback.nav2.goal_execution_hil_pass, false),
        base_command_nonzero_observed: actionCardBoolean(readback.nav2.goal_execution_base_command_nonzero_observed, false),
        base_command_nonzero_count: actionCardNumber(readback.nav2.goal_execution_base_command_nonzero_count),
        base_feedback_sample_count: actionCardNumber(readback.nav2.goal_execution_base_feedback_sample_count),
        base_feedback_nonzero_sample_count: actionCardNumber(readback.nav2.goal_execution_base_feedback_nonzero_sample_count),
        base_feedback_lr_nonzero_proven: actionCardBoolean(readback.nav2.goal_execution_base_feedback_lr_nonzero_proven, false),
        base_feedback_latest_raw_left: readback.nav2.goal_execution_base_feedback_latest_raw_left,
        base_feedback_latest_raw_right: readback.nav2.goal_execution_base_feedback_latest_raw_right,
        imu_attitude_delta_observed: actionCardBoolean(readback.nav2.goal_execution_base_feedback_imu_attitude_delta_observed, false),
        imu_roll_delta: readback.nav2.goal_execution_base_feedback_imu_roll_delta,
        imu_pitch_delta: readback.nav2.goal_execution_base_feedback_imu_pitch_delta,
        last_base_command_mode: readback.nav2.goal_execution_base_command_mode,
        next_base_command_mode: readback.nav2.next_execution_base_command_mode,
        nav2_stack_running: actionCardBoolean(readback.nav2.nav2_stack_running, false),
        nav2_stack_lifecycle_state: readback.nav2.nav2_stack_lifecycle_state,
        planner_server_active: actionCardBoolean(readback.nav2.planner_server_active, false),
        controller_server_active: actionCardBoolean(readback.nav2.controller_server_active, false),
        controller_server_requested: actionCardBoolean(readback.nav2.controller_server_requested, false),
        controller_idle_not_blocking: nav2ControllerIdleNotBlocking,
        controller_blocking_current_goal: nav2ControllerBlockingCurrentGoal,
        controller_idle_reason_plain: nav2ControllerIdleReason,
        path_generated: actionCardBoolean(readback.nav2.path_generated, false),
        nav2_path_point_count: actionCardNumber(readback.nav2.path_point_count || readback.nav2.path_preview_point_count),
        current_blocker_reasons: actionCardReasonList(readback.nav2.current_blocker_reasons),
        current_blocker_labels: actionCardLabelList(readback.nav2.current_blocker_labels),
        managed_runtime_autostart: nav2ManagedRuntimeAutostart,
        managed_runtime_requested: nav2ManagedRuntimeRequested,
        managed_runtime_started: nav2ManagedRuntimeStarted,
        managed_runtime_lifecycle_ready_ok: nav2ManagedRuntimeLifecycleReadyOk,
        managed_runtime_cleanup_ok: nav2ManagedRuntimeCleanupOk,
        blockers: boundary.nav2_goal_blockers,
      },
    },
    {
      id: "keyboard_control",
      title: "键盘手控",
      status: boundary.keyboard_control_status,
      status_label: boundary.keyboard_control_start_ready ? "可启用" : "未就绪",
      summary_plain: actionCardText(readback.keyboard.hold_to_move_plain || readback.keyboard.readiness_plain, "键盘手控状态未读到"),
      next_action_plain: actionCardText(readback.keyboard.next_action_plain || boundary.keyboard_control_next_action, "勾选安全确认后启用键盘"),
      wysiwyg_status: "hold_to_move_contract",
      requires_safety_confirmation: true,
      can_start_after_safety_confirm: boundary.keyboard_control_start_ready,
      sends_motion_when_clicked: false,
      blocks_free_motion: false,
      blocks_mapping_start: false,
      evidence: {
        hold_to_move_required: true,
        arm_sends_motion: false,
        requires_keydown_for_motion: true,
        pulse_interval_ms: ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS,
        pulse_duration_ms: ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS,
        manual_command_mode: readback.keyboard.manual_command_mode || "ros",
        stop_triggers: boundary.keyboard_stop_triggers,
        wheel_feedback_required_in_same_hold_window: true,
        fixed_keyboard_manual_endpoint: "/api/robot-control/base/manual",
        fixed_keyboard_stop_endpoint: "/api/robot-control/base/stop",
        keyboard_start_ready: boundary.keyboard_control_start_ready,
        keyboard_enabled: actionCardBoolean(readback.keyboard.enabled, false),
        keyboard_armed: false,
        keyboard_sends_motion_while_held: false,
        keyboard_current_direction: "none",
        keyboard_current_hold_pulse_count: 0,
        keyboard_best_continuous_pulse_count: 0,
        keyboard_verified_min_forwarded_pulses: 2,
        keyboard_continuous_pulse_verified: false,
        keyboard_stop_required_after_hold: true,
        keyboard_stop_settled_after_pulse: false,
        keyboard_motion_verified: false,
      },
    },
    {
      id: "free_move",
      title: "自由移动",
      status: boundary.free_roam_autonomy,
      status_label: boundary.free_roam_motion_start_ready ? (boundary.free_roam_autonomy === "ready" ? "运行中" : "可启动") : "未就绪",
      summary_plain: actionCardText(readback.free_roam.motion_readiness_plain, "自由移动状态未读到"),
      next_action_plain: actionCardText(readback.free_roam.motion_next_action_plain || boundary.free_roam_autonomy_next_action, "勾选安全确认后启动自由移动"),
      wysiwyg_status: boundary.free_roam_motion_start_ready ? "motion_start_ready" : "motion_not_ready",
      requires_safety_confirmation: true,
      can_start_after_safety_confirm: boundary.free_roam_motion_start_ready,
      sends_motion_when_clicked: true,
      blocks_free_motion: false,
      blocks_mapping_start: false,
      evidence: {
        free_move_start_ready: boundary.free_roam_motion_start_ready,
        free_move_safety_only: true,
        stop_fallback_required: true,
        camera_blocks_free_motion: false,
        radar_blocks_free_motion: false,
        fixed_free_roam_start_endpoint: "/api/robot-control/free-roam/autonomy/start",
        fixed_free_roam_stop_endpoint: "/api/robot-control/free-roam/autonomy/stop",
        free_roam_stop_request_pending: freeRoamStopRequestPending,
        start_will_clear_stop_request: freeRoamStartWillClearStopRequest,
        start_clears_stop_request_not_blocking: freeRoamStartWillClearStopRequest && !freeRoamMotionBlockedByStopRequest,
        motion_start_blocked_by_stop_request: freeRoamMotionBlockedByStopRequest,
        fixed_mapping_start_endpoint: "/api/robot-control/map/start",
        fixed_mapping_preview_endpoint: "/api/robot-control/map/preview",
        mapping_start_ready: boundary.free_roam_mapping_start_ready,
        mapping_camera_first_frame_ready: cameraSourceFirstFrameReady,
        mapping_camera_source_readiness: readback.camera.source_readiness,
        mapping_lidar_fresh_ready: mappingLidarFreshReady,
        mapping_lidar_lifecycle_running: mappingLidarLifecycleRunning,
        mapping_lidar_lifecycle_state: readback.lidar.lifecycle_state,
        mapping_runtime_scan_fresh: mappingRuntimeScanFresh,
        mapping_runtime_scan_diagnostic_only: mappingRuntimeScanDiagnosticOnly,
        mapping_lidar_fresh_blocked_by_lifecycle: mappingLidarFreshBlockedByLifecycle,
        mapping_lidar_next_action_plain: readback.lidar.radar_map_overlay_next_action_plain || readback.radar.radar_next_action_plain,
        mapping_start_missing_reasons: boundary.free_roam_mapping_start_missing_reasons,
        mapping_acceptance_missing_reasons: boundary.free_roam_mapping_missing_reasons,
      },
    },
    {
      id: "mapping_start",
      title: "建图启动",
      status: boundary.free_roam_mapping_start_ready ? "ready" : "not_ready",
      status_label: boundary.free_roam_mapping_start_ready ? "可启动" : "未就绪",
      summary_plain: actionCardText(readback.free_roam.mapping_start_readiness_plain || boundary.free_roam_mapping_start_plain, "建图启动状态未读到"),
      next_action_plain: actionCardText(readback.free_roam.mapping_start_next_action_plain || boundary.free_roam_mapping_start_next_action, "补齐画面首帧和雷达新鲜度"),
      wysiwyg_status: boundary.free_roam_mapping_start_ready ? "camera_and_radar_ready" : "camera_or_radar_missing",
      requires_safety_confirmation: boundary.free_roam_mapping_start_ready,
      can_start_after_safety_confirm: boundary.free_roam_mapping_start_ready,
      sends_motion_when_clicked: boundary.free_roam_mapping_start_ready,
      blocks_free_motion: false,
      blocks_mapping_start: !boundary.free_roam_mapping_start_ready,
      evidence: {
        free_move_start_ready: boundary.free_roam_motion_start_ready,
        free_move_safety_only: true,
        camera_blocks_free_motion: false,
        radar_blocks_free_motion: false,
        mapping_start_ready: boundary.free_roam_mapping_start_ready,
        mapping_start_requires_camera_first_frame: true,
        mapping_start_requires_lidar_fresh: true,
        mapping_camera_first_frame_ready: cameraSourceFirstFrameReady,
        mapping_camera_source_readiness: readback.camera.source_readiness,
        mapping_lidar_fresh_ready: mappingLidarFreshReady,
        mapping_lidar_lifecycle_running: mappingLidarLifecycleRunning,
        mapping_lidar_lifecycle_state: readback.lidar.lifecycle_state,
        mapping_runtime_scan_fresh: mappingRuntimeScanFresh,
        mapping_runtime_scan_diagnostic_only: mappingRuntimeScanDiagnosticOnly,
        mapping_lidar_fresh_blocked_by_lifecycle: mappingLidarFreshBlockedByLifecycle,
        mapping_lidar_next_action_plain: readback.lidar.radar_map_overlay_next_action_plain || readback.radar.radar_next_action_plain,
        mapping_start_missing_reasons: boundary.free_roam_mapping_start_missing_reasons,
        mapping_acceptance_missing_reasons: boundary.free_roam_mapping_missing_reasons,
        fixed_free_roam_start_endpoint: "/api/robot-control/free-roam/autonomy/start",
        fixed_mapping_start_endpoint: "/api/robot-control/map/start",
        fixed_mapping_preview_endpoint: "/api/robot-control/map/preview",
      },
    },
  ];
}

function actionCardById(
  cards: NonNullable<RobotControlSummaryResponse["action_status_cards"]>,
  id: NonNullable<RobotControlSummaryResponse["action_status_cards"]>[number]["id"],
): NonNullable<RobotControlSummaryResponse["action_status_cards"]>[number] {
  // 清单复用动作卡的同轮事实，避免目标检查和首屏动作状态漂移。
  return cards.find((card) => card.id === id) ?? {
    id,
    title: id,
    status: "not_ready",
    status_label: "未就绪",
    summary_plain: "状态未读到",
    next_action_plain: "先刷新小车状态",
    wysiwyg_status: "not_loaded",
    requires_safety_confirmation: false,
    can_start_after_safety_confirm: false,
    sends_motion_when_clicked: false,
    blocks_free_motion: false,
    blocks_mapping_start: false,
  };
}

function actionCardWysiwygPlain(value: string): string {
  // 普通目标检查不能泄露枚举 token；只保留现场能理解的短读数。
  const labels: Record<string, string> = {
    visible_frame: "当前画面已显示",
    no_current_frame: "当前画面未显示",
    current_map_visible: "当前地图已显示",
    map_not_visible: "当前地图未显示",
    current_points_visible: "当前地图雷达点已显示",
    old_or_missing_points_not_drawn: "旧雷达点或缺点未贴到当前地图",
    route_ready_on_map: "图上路线已准备",
    route_not_ready: "图上路线未准备",
    hold_to_move_contract: "按住才连续移动，松开会停",
    motion_start_ready: "自由移动可启动",
    motion_not_ready: "自由移动未就绪",
    camera_and_radar_ready: "画面和雷达已就绪",
    camera_or_radar_missing: "画面或雷达未就绪",
  };
  return labels[value] ?? value.replace(/_/g, " ");
}

function buildGoalChecklist(
  cards: NonNullable<RobotControlSummaryResponse["action_status_cards"]>,
  readback: RobotControlSummaryResponse["readback_summary"],
  boundary: RobotControlSummaryResponse["safe_command_boundary"],
): RobotControlSummaryResponse["goal_checklist"] {
  // 目标检查只做只读验收口径聚合；ready 不等于 done，真实运动项仍需要现场执行证据。
  const camera = actionCardById(cards, "camera_preview");
  const map = actionCardById(cards, "map_preview");
  const radar = actionCardById(cards, "radar_map_points");
  const nav2 = actionCardById(cards, "nav2_route");
  const keyboard = actionCardById(cards, "keyboard_control");
  const freeMove = actionCardById(cards, "free_move");
  const mapping = actionCardById(cards, "mapping_start");
  const nav2Done = readback.nav2.route_execution_readiness_plain.startsWith("完整路线执行已证明");
  const nav2Title = nav2.status === "ready_needs_wheel_rerun"
    ? "重跑图上行程并复验轮速"
    : "完整行程执行";
  const keyboardReady = boundary.keyboard_control_start_ready;
  const freeMoveRunning = boundary.free_roam_autonomy === "ready";
  return [
    {
      id: "camera_wysiwyg",
      title: "画面所见即所得",
      status: camera.status === "visible" ? "done" : "needs_action",
      status_label: camera.status === "visible" ? "已满足" : "待处理",
      summary_plain: camera.summary_plain,
      evidence_plain: `画面读数：${actionCardWysiwygPlain(camera.wysiwyg_status)}`,
      next_action_plain: camera.next_action_plain,
      source_card_id: "camera_preview",
      requires_safety_confirmation: false,
      requires_motion: false,
      blocks_goal_completion: camera.status !== "visible",
    },
    {
      id: "map_wysiwyg",
      title: "地图所见即所得",
      status: map.status === "visible" ? "done" : "needs_action",
      status_label: map.status === "visible" ? "已满足" : "待处理",
      summary_plain: map.summary_plain,
      evidence_plain: `地图读数：${actionCardWysiwygPlain(map.wysiwyg_status)}`,
      next_action_plain: map.next_action_plain,
      source_card_id: "map_preview",
      requires_safety_confirmation: false,
      requires_motion: false,
      blocks_goal_completion: map.status !== "visible",
    },
    {
      id: "radar_map_points_wysiwyg",
      title: "雷达点贴到地图",
      status: radar.status === "current_on_map" ? "done" : "needs_action",
      status_label: radar.status === "current_on_map" ? "已满足" : "待处理",
      summary_plain: radar.summary_plain,
      evidence_plain: `地图雷达点读数：${actionCardWysiwygPlain(radar.wysiwyg_status)}`,
      next_action_plain: radar.next_action_plain,
      source_card_id: "radar_map_points",
      requires_safety_confirmation: false,
      requires_motion: false,
      blocks_goal_completion: radar.status !== "current_on_map",
    },
    {
      id: "nav2_route_execution",
      title: nav2Title,
      status: nav2Done ? "done" : boundary.nav2_goal_ready ? "needs_safety_confirm" : "not_ready",
      status_label: nav2Done ? "已完成" : boundary.nav2_goal_ready ? "待安全确认" : "未就绪",
      summary_plain: nav2.summary_plain,
      evidence_plain: actionCardText(readback.nav2.goal_execution_wheel_raw_lr_status_plain, `${nav2Title}读数未读到`),
      next_action_plain: nav2.next_action_plain,
      source_card_id: "nav2_route",
      requires_safety_confirmation: !nav2Done,
      requires_motion: !nav2Done,
      blocks_goal_completion: !nav2Done,
    },
    {
      id: "keyboard_continuous_control",
      title: "键盘连续手控",
      status: keyboardReady ? "needs_safety_confirm" : "not_ready",
      status_label: keyboardReady ? "待安全确认" : "未就绪",
      summary_plain: keyboard.summary_plain,
      evidence_plain: actionCardText(readback.keyboard.continuous_control_contract_plain, "键盘连续控制合同未读到"),
      next_action_plain: keyboard.next_action_plain,
      source_card_id: "keyboard_control",
      requires_safety_confirmation: true,
      requires_motion: true,
      blocks_goal_completion: true,
    },
    {
      id: "free_move",
      title: "自由自助移动",
      status: freeMoveRunning ? "ready" : boundary.free_roam_motion_start_ready ? "needs_safety_confirm" : "not_ready",
      status_label: freeMoveRunning ? "运行中" : boundary.free_roam_motion_start_ready ? "待安全确认" : "未就绪",
      summary_plain: freeMove.summary_plain,
      evidence_plain: actionCardText(readback.free_roam.motion_readiness_plain, "自由移动读数未读到"),
      next_action_plain: freeMove.next_action_plain,
      source_card_id: "free_move",
      requires_safety_confirmation: !freeMoveRunning,
      requires_motion: true,
      blocks_goal_completion: !freeMoveRunning,
    },
    {
      id: "mapping_start",
      title: "传感器就绪后建图",
      status: boundary.free_roam_mapping_start_ready ? "needs_safety_confirm" : "not_ready",
      status_label: boundary.free_roam_mapping_start_ready ? "待安全确认" : "未就绪",
      summary_plain: mapping.summary_plain,
      evidence_plain: actionCardText(readback.free_roam.mapping_start_readiness_plain, "建图启动读数未读到"),
      next_action_plain: mapping.next_action_plain,
      source_card_id: "mapping_start",
      requires_safety_confirmation: boundary.free_roam_mapping_start_ready,
      requires_motion: boundary.free_roam_mapping_start_ready,
      blocks_goal_completion: true,
    },
  ];
}

function buildGoalChecklistSummary(
  checklist: NonNullable<RobotControlSummaryResponse["goal_checklist"]>,
): RobotControlSummaryResponse["goal_checklist_summary"] {
  // 汇总只决定“先看哪一项”，不会把 ready 状态升级成完成，也不会触发任何动作。
  const totalCount = checklist.length;
  const doneCount = checklist.filter((item) => item.status === "done").length;
  const remaining = checklist.filter((item) => item.blocks_goal_completion);
  const safetyConfirmNeededCount = remaining.filter((item) => item.requires_safety_confirmation).length;
  const motionNeededCount = remaining.filter((item) => item.requires_motion).length;
  const firstIncomplete = remaining[0] ?? null;
  const toActionItem = (item: NonNullable<RobotControlSummaryResponse["goal_checklist"]>[number]) => ({
    id: item.id,
    title: item.title,
    status_label: item.status_label,
    next_action_plain: item.next_action_plain,
    source_card_id: item.source_card_id,
    requires_safety_confirmation: item.requires_safety_confirmation,
    requires_motion: item.requires_motion,
    blocks_goal_completion: item.blocks_goal_completion,
  });
  const nextActionItems = remaining.map(toActionItem);
  const nav2ReadyForRerun = remaining.some((item) =>
    item.id === "nav2_route_execution" && (item.status === "ready" || item.status === "needs_safety_confirm")
  );
  const readyActionPriority: Record<string, number> = nav2ReadyForRerun
    ? {
      nav2_route_execution: 0,
      keyboard_continuous_control: 1,
      free_move: 2,
      mapping_start: 3,
    }
    : {
      free_move: 0,
      keyboard_continuous_control: 1,
      nav2_route_execution: 2,
      mapping_start: 3,
    };
  const sortReadyActionItems = (items: ReturnType<typeof toActionItem>[]): ReturnType<typeof toActionItem>[] =>
    [...items].sort((left, right) => (readyActionPriority[left.id] ?? 50) - (readyActionPriority[right.id] ?? 50));
  const readyActionItems = remaining
    .filter((item) => item.status === "ready" || item.status === "needs_safety_confirm")
    .map(toActionItem);
  const orderedReadyActionItems = sortReadyActionItems(readyActionItems);
  const primaryReadyAction = orderedReadyActionItems[0] ?? null;
  const blockedActionItems = remaining
    .filter((item) => item.status === "not_ready" || item.status === "needs_action")
    .map(toActionItem);
  const motionReadyItems = orderedReadyActionItems.filter((item) => item.requires_motion);
  const sensorBlockerItems = blockedActionItems.filter((item) =>
    ["camera_wysiwyg", "radar_map_points_wysiwyg", "mapping_start"].includes(item.id)
  );
  const moveNowStatusPlain = motionReadyItems.length > 0
    ? `可先动：${motionReadyItems.map((item) => item.title).join("、")}；发车前只需现场安全确认；相机和雷达只影响建图验收。`
    : "当前还没有可直接发车的入口；先处理自由移动、键盘或图上行程门禁。";
  const mappingBlockersPlain = sensorBlockerItems.length > 0
    ? `建图缺口：${sensorBlockerItems.map((item) => item.title).join("、")}；这些缺口不阻止先低速自由移动。`
    : "建图启动条件已满足；勾选现场安全确认后可启动建图。";
  const progressPlain = `${doneCount}/${totalCount}`;
  const actionIds = (items: ReturnType<typeof toActionItem>[]) => items.map((item) => item.id);
  const itemById = (id: NonNullable<RobotControlSummaryResponse["goal_checklist"]>[number]["id"]) => checklist.find((item) => item.id === id) ?? null;
  const freeMove = itemById("free_move");
  const keyboard = itemById("keyboard_continuous_control");
  const radar = itemById("radar_map_points_wysiwyg");
  const nav2 = itemById("nav2_route_execution");
  const mapping = itemById("mapping_start");
  const firstMotion = [freeMove, keyboard, nav2].find((item) => item && (item.status === "ready" || item.status === "needs_safety_confirm")) ?? null;
  const firstSafetyPrecheck = [freeMove, nav2, keyboard, mapping].find((item) => item?.status === "needs_safety_confirm") ?? null;
  const motionSummary = (() => {
    if (freeMove?.status === "ready") {
      return "自由移动已运行；相机和雷达只影响建图验收，不影响继续现场监看。";
    }
    if (freeMove?.status === "needs_safety_confirm") {
      return `可先自由移动；相机和雷达只影响建图验收。下一步：${freeMove.next_action_plain}`;
    }
    if (keyboard?.status === "needs_safety_confirm") {
      return `自由移动状态机未就绪时，仍可先用键盘连续手控；相机和雷达不作为键盘发车硬门禁。下一步：${keyboard.next_action_plain}`;
    }
    if (nav2?.status === "needs_safety_confirm") {
      return `图上行程可执行；发车只需要现场安全确认，雷达和相机问题不应改写这个读数。下一步：${nav2.next_action_plain}`;
    }
    return "当前还没有可直接发车的入口；先处理自由移动、键盘或图上行程门禁。";
  })();
  const safetyPrecheckSummary = (() => {
    if (firstSafetyPrecheck) {
      return `发车前预检已精简：只需要现场安全确认；相机和雷达不作为移动或行程发车前额外预检。下一步：${firstSafetyPrecheck.next_action_plain}`;
    }
    return "当前没有待安全确认的发车入口；继续按画面、雷达、行程和建图缺口处理。";
  })();
  const radarSummary = (() => {
    if (radar?.status === "done") {
      return "雷达点已贴到当前地图；雷达标记所见即所得。";
    }
    if (radar) {
      return `雷达点还没有贴到当前地图；先按同轮地图画面确认，不把旧点当当前标记。下一步：${radar.next_action_plain}`;
    }
    return "雷达贴图状态还未读到；先刷新小车状态。";
  })();
  const nav2Summary = (() => {
    if (nav2?.status === "done") {
      return "完整图上行程已证明；同窗口轮速 L/R 已闭环。";
    }
    if (nav2?.status === "needs_safety_confirm") {
      return `完整图上行程可复验；发车前只需要行程安全确认。下一步：${nav2.next_action_plain}`;
    }
    if (nav2) {
      return `完整图上行程还未就绪；先补齐图上路线和当前位置显示。下一步：${nav2.next_action_plain}`;
    }
    return "完整行程状态还未读到；先刷新小车状态。";
  })();
  const mappingSummary = (() => {
    if (mapping?.status === "needs_safety_confirm") {
      return `相机和雷达已就绪；建图启动只等现场安全确认。下一步：${mapping.next_action_plain}`;
    }
    if (mapping) {
      return `建图暂不可启动；相机和雷达只影响建图验收，不阻止已具备条件的低速移动。下一步：${mapping.next_action_plain}`;
    }
    return "建图条件还未读到；先刷新小车状态。";
  })();
  if (totalCount === 0) {
    return {
      status: "not_started",
      status_label: "未开始",
      total_count: 0,
      done_count: 0,
      remaining_count: 0,
      safety_confirm_needed_count: 0,
      motion_needed_count: 0,
      ready_action_count: 0,
      blocked_action_count: 0,
      motion_ready_count: 0,
      sensor_blocker_count: 0,
      first_incomplete_item_id: "",
      first_incomplete_source_card_id: "",
      first_motion_item_id: "",
      first_motion_source_card_id: "",
      primary_ready_action_item_id: "",
      primary_ready_action_source_card_id: "",
      primary_ready_action_next_action_plain: "先刷新小车状态。",
      primary_ready_action_summary_plain: "未读到可先执行动作；先刷新小车状态。",
      safety_precheck_source_card_id: "",
      radar_item_id: "",
      radar_source_card_id: "",
      nav2_item_id: "",
      nav2_source_card_id: "",
      mapping_item_id: "",
      mapping_source_card_id: "",
      next_action_plain: "先刷新小车状态。",
      summary_plain: "本轮目标检查未读到；先刷新小车状态。",
      motion_next_action_plain: "先刷新小车状态。",
      motion_summary_plain: "车能不能先动还未读到；先刷新小车状态。",
      safety_precheck_next_action_plain: "先刷新小车状态。",
      safety_precheck_summary_plain: "发车前最小确认还未读到；先刷新小车状态。",
      radar_next_action_plain: "先刷新小车状态。",
      radar_summary_plain: "雷达贴图状态还未读到；先刷新小车状态。",
      nav2_next_action_plain: "先刷新小车状态。",
      nav2_summary_plain: "完整行程状态还未读到；先刷新小车状态。",
      mapping_next_action_plain: "先刷新小车状态。",
      mapping_summary_plain: "建图条件还未读到；先刷新小车状态。",
      move_now_status_plain: "当前还不能判断能否先动；先刷新小车状态。",
      mapping_blockers_plain: "建图缺口未读到；先刷新小车状态。",
      progress_plain: progressPlain,
      next_action_item_ids: [],
      ready_action_ids: [],
      blocked_action_ids: [],
      next_action_items: [],
      ready_action_items: [],
      blocked_action_items: [],
    };
  }
  if (!firstIncomplete) {
    return {
      status: "complete",
      status_label: "已完成",
      total_count: totalCount,
      done_count: doneCount,
      remaining_count: 0,
      safety_confirm_needed_count: 0,
      motion_needed_count: 0,
      ready_action_count: 0,
      blocked_action_count: 0,
      motion_ready_count: motionReadyItems.length,
      sensor_blocker_count: 0,
      first_incomplete_item_id: "",
      first_incomplete_source_card_id: "",
      first_motion_item_id: firstMotion?.id ?? "",
      first_motion_source_card_id: firstMotion?.source_card_id ?? "",
      primary_ready_action_item_id: "",
      primary_ready_action_source_card_id: "",
      primary_ready_action_next_action_plain: "本轮目标检查已完成；继续保持现场监看。",
      primary_ready_action_summary_plain: "本轮目标检查已完成；当前没有待执行的 ready 动作。",
      safety_precheck_source_card_id: firstSafetyPrecheck?.source_card_id ?? "",
      radar_item_id: radar?.id ?? "",
      radar_source_card_id: radar?.source_card_id ?? "",
      nav2_item_id: nav2?.id ?? "",
      nav2_source_card_id: nav2?.source_card_id ?? "",
      mapping_item_id: mapping?.id ?? "",
      mapping_source_card_id: mapping?.source_card_id ?? "",
      next_action_plain: "本轮目标检查已完成；继续保持现场监看。",
      summary_plain: `本轮目标检查 ${doneCount}/${totalCount} 项已完成。`,
      motion_next_action_plain: firstMotion?.next_action_plain ?? "本轮目标检查已完成；继续保持现场监看。",
      motion_summary_plain: motionSummary,
      safety_precheck_next_action_plain: firstSafetyPrecheck?.next_action_plain ?? "本轮目标检查已完成；继续保持现场监看。",
      safety_precheck_summary_plain: safetyPrecheckSummary,
      radar_next_action_plain: radar?.next_action_plain ?? "本轮目标检查已完成；继续保持现场监看。",
      radar_summary_plain: radarSummary,
      nav2_next_action_plain: nav2?.next_action_plain ?? "本轮目标检查已完成；继续保持现场监看。",
      nav2_summary_plain: nav2Summary,
      mapping_next_action_plain: mapping?.next_action_plain ?? "本轮目标检查已完成；继续保持现场监看。",
      mapping_summary_plain: mappingSummary,
      move_now_status_plain: motionReadyItems.length > 0 ? moveNowStatusPlain : "本轮目标检查已完成；当前没有待执行动作。",
      mapping_blockers_plain: "建图缺口已清零。",
      progress_plain: progressPlain,
      next_action_item_ids: [],
      ready_action_ids: [],
      blocked_action_ids: [],
      next_action_items: [],
      ready_action_items: [],
      blocked_action_items: [],
    };
  }
  const safetyText = safetyConfirmNeededCount > 0 ? `，其中 ${safetyConfirmNeededCount} 项需要现场安全确认` : "";
  const motionText = motionNeededCount > 0 ? `，${motionNeededCount} 项需要真实运动验证` : "";
  const readyActionText = orderedReadyActionItems.length > 0
    // 有可现场收口项时，先告诉 operator 可以做什么；相机/雷达缺口不能把可动车入口压到后面。
    ? `现场可先收口 ${orderedReadyActionItems.length} 项：${orderedReadyActionItems.map((item) => item.title).join("、")}；`
    : "";
  const blockedActionText = blockedActionItems.length > 0
    ? `未就绪项：${blockedActionItems.map((item) => item.title).join("、")}。`
    : "";
  const primarySummaryText = primaryReadyAction
    ? `${readyActionText}先做：${primaryReadyAction.title}；${blockedActionText}`
    : `先补条件：${firstIncomplete.title}。`;
  return {
    status: "in_progress",
    status_label: "进行中",
    total_count: totalCount,
    done_count: doneCount,
    remaining_count: remaining.length,
    safety_confirm_needed_count: safetyConfirmNeededCount,
    motion_needed_count: motionNeededCount,
    ready_action_count: orderedReadyActionItems.length,
    blocked_action_count: blockedActionItems.length,
    motion_ready_count: motionReadyItems.length,
    sensor_blocker_count: sensorBlockerItems.length,
    first_incomplete_item_id: firstIncomplete.id,
    first_incomplete_source_card_id: firstIncomplete.source_card_id,
    first_motion_item_id: firstMotion?.id ?? "",
    first_motion_source_card_id: firstMotion?.source_card_id ?? "",
    primary_ready_action_item_id: primaryReadyAction?.id ?? "",
    primary_ready_action_source_card_id: primaryReadyAction?.source_card_id ?? "",
    primary_ready_action_next_action_plain: primaryReadyAction?.next_action_plain ?? firstIncomplete.next_action_plain,
    primary_ready_action_summary_plain: primaryReadyAction
      ? `可先做：${primaryReadyAction.title}；${primaryReadyAction.next_action_plain}`
      : `暂时没有可先执行动作；先处理：${firstIncomplete.title}。`,
    safety_precheck_source_card_id: firstSafetyPrecheck?.source_card_id ?? "",
    radar_item_id: radar?.id ?? "",
    radar_source_card_id: radar?.source_card_id ?? "",
    nav2_item_id: nav2?.id ?? "",
    nav2_source_card_id: nav2?.source_card_id ?? "",
    mapping_item_id: mapping?.id ?? "",
    mapping_source_card_id: mapping?.source_card_id ?? "",
    next_action_plain: primaryReadyAction?.next_action_plain ?? firstIncomplete.next_action_plain,
    summary_plain: `本轮目标检查 ${doneCount}/${totalCount} 项已完成，还差 ${remaining.length} 项${safetyText}${motionText}；${primarySummaryText}`,
    motion_next_action_plain: firstMotion?.next_action_plain ?? "当前还没有可直接发车的入口；先处理自由移动、键盘或图上行程门禁。",
    motion_summary_plain: motionSummary,
    safety_precheck_next_action_plain: firstSafetyPrecheck?.next_action_plain ?? "当前没有待安全确认的发车入口；继续按画面、雷达、行程和建图缺口处理。",
    safety_precheck_summary_plain: safetyPrecheckSummary,
    radar_next_action_plain: radar?.next_action_plain ?? "雷达贴图状态还未读到；先刷新小车状态。",
    radar_summary_plain: radarSummary,
    nav2_next_action_plain: nav2?.next_action_plain ?? "完整行程状态还未读到；先刷新小车状态。",
    nav2_summary_plain: nav2Summary,
    mapping_next_action_plain: mapping?.next_action_plain ?? "建图条件还未读到；先刷新小车状态。",
    mapping_summary_plain: mappingSummary,
    move_now_status_plain: moveNowStatusPlain,
    mapping_blockers_plain: mappingBlockersPlain,
    progress_plain: progressPlain,
    next_action_item_ids: actionIds(nextActionItems),
    ready_action_ids: actionIds(orderedReadyActionItems),
    blocked_action_ids: actionIds(blockedActionItems),
    next_action_items: nextActionItems,
    ready_action_items: orderedReadyActionItems,
    blocked_action_items: blockedActionItems,
  };
}

type LiveRobotApiConnectionSummary = Pick<
  RobotControlSummaryResponse["robot_api_connection"],
  "status" | "loaded_count" | "blocked_count" | "failed_count" | "blocked_reasons"
> & {
  failed_endpoint_ids: string[];
  recovery_endpoints: string[];
};

function robotApiConnectionPlain(summary: LiveRobotApiConnectionSummary): string {
  // 连接总诊断要放在普通首屏，避免用户把“画面/地图未显示”误判成操作步骤问题。
  if (summary.status === "readable") {
    return `小车连接可读：已读取 ${summary.loaded_count} 个只读端点。`;
  }
  if (summary.status === "blocked") {
    return "小车连接被代理安全护栏拦住；不会执行任何运动命令。";
  }
  if (summary.loaded_count === 0) {
    const failedText = summary.failed_endpoint_ids.length
      ? `失败端点：${summary.failed_endpoint_ids.slice(0, 6).join("、")}。`
      : "";
    return `小车连接不可用：Robot API 只读端点这轮没有返回。${failedText}`;
  }
  const failedText = summary.failed_endpoint_ids.length
    ? `失败端点：${summary.failed_endpoint_ids.slice(0, 6).join("、")}。`
    : "";
  return `小车连接不完整：已读到 ${summary.loaded_count} 个端点，失败 ${summary.failed_count} 个。${failedText}`;
}

function robotApiConnectionNextActionPlain(summary: LiveRobotApiConnectionSummary): string {
  // 这里只给恢复连接的 no-motion 下一步；真实发车仍由各动作按钮和安全确认控制。
  if (summary.status === "readable") {
    return "小车连接可读；继续按当前卡点处理。";
  }
  if (summary.status === "blocked") {
    return "先修正小车地址或安全护栏命中的危险字段，再刷新 PC 状态。";
  }
  if (summary.loaded_count === 0) {
    return "先确认小车电源、网络、8787 Robot API 服务和 SSH 登录状态，再刷新 PC 状态。";
  }
  return "先刷新 PC 状态；若同一只读端点继续失败，检查对应上车服务。";
}

function buildLiveClosureSummary(
  cards: NonNullable<RobotControlSummaryResponse["action_status_cards"]>,
  goalSummary: NonNullable<RobotControlSummaryResponse["goal_checklist_summary"]>,
  readback: RobotControlSummaryResponse["readback_summary"],
  boundary: RobotControlSummaryResponse["safe_command_boundary"],
  operatorHilMaterialSummary: RobotControlOperatorHilMaterialSummary,
  robotApiConnection: LiveRobotApiConnectionSummary,
): RobotControlSummaryResponse["live_closure_summary"] {
  // 这个汇总只把同轮只读证据压成普通用户能懂的一块牌，不新增任何发车或解锁条件。
  const camera = actionCardById(cards, "camera_preview");
  const map = actionCardById(cards, "map_preview");
  const radar = actionCardById(cards, "radar_map_points");
  const nav2 = actionCardById(cards, "nav2_route");
  const keyboard = actionCardById(cards, "keyboard_control");
  const routeReadyOnMap = nav2.evidence?.route_ready_on_map === true || boundary.nav2_goal_ready;
  const nav2GoalExecutionProven = nav2.evidence?.goal_execution_proven === true
    || readback.nav2.goal_execution_status === "goal_succeeded";
  const wheelLrNonzeroProven = nav2.evidence?.base_feedback_lr_nonzero_proven === true;
  const needsSameWindowWheelRerun = routeReadyOnMap
    && nav2GoalExecutionProven
    && !wheelLrNonzeroProven;
  const deliveryClaimReady = operatorHilMaterialSummary.delivery_claim === "true";
  const cameraCurrentVisible = camera.evidence?.camera_current_frame_visible === true || camera.status === "visible";
  const mapCurrentVisible = map.evidence?.map_current_visible === true || map.status === "visible";
  const pathCurrentVisible = readback.map.path_current_visible === "true" || routeReadyOnMap;
  const radarMapPointsVisible = radar.evidence?.current_on_map === true || radar.status === "current_on_map";
  const liveWysiwygMissingSurfaceIds = [
    ...(!cameraCurrentVisible ? ["camera"] : []),
    ...(!mapCurrentVisible ? ["map"] : []),
    ...(!radarMapPointsVisible ? ["radar_map_points"] : []),
  ];
  const mapUnread = /fetch_failed|not_loaded|not_proven/.test(readback.map.status || "")
    || !["true", "map_once_observed"].includes(String(readback.map.map_once_observed || ""));
  const liveWysiwygReadbackGapSurfaceIds = [
    ...(!cameraCurrentVisible && /fetch_failed|not_loaded|not_proven/.test(readback.camera.status || "") ? ["camera"] : []),
    ...(!mapCurrentVisible && mapUnread ? ["map"] : []),
    ...(!radarMapPointsVisible && /fetch_failed|not_loaded|not_proven/.test(readback.radar.status || "") ? ["radar_map_points"] : []),
  ];
  const splitDiagnosticList = (value: string | undefined): string[] => (value || "")
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item && item !== "none" && item !== "not_loaded")
    .slice(0, 8);
  const diagnosticLabel = (item: string): string => ({
    scan_once: "没有读到一帧雷达",
    scan_hz: "雷达频率未确认",
    raw_packet_once: "雷达原始包未确认",
    scan_preview_points_missing: "地图缺雷达点",
    runtime_scan_stale_for_map_radar_overlay: "雷达点不是当前新读数",
    robot_pose_missing_for_map_radar_overlay: "小车地图位置未读到",
  }[item] || item.replace(/_/g, " "));
  const diagnosticLabelsPlain = (items: string[]): string => items.map(diagnosticLabel).join("；") || "无";
  const cameraFailureLabel = (reason: string): string => ({
    first_frame_total_timeout: "读取首帧超时",
    camera_source_first_frame_failed: "相机源没有首帧",
    source_first_frame_failed: "相机源没有首帧",
    timeout: "读取首帧超时",
  }[reason] || reason.replace(/_/g, " "));
  const cameraProbeStatusLabel = (status: string): string => ({
    source_first_frame_failed: "首帧失败",
    first_frame_failed: "首帧失败",
    blocked: "未通过",
    not_loaded: "未读取",
  }[status] || status.replace(/_/g, " "));
  const cameraProbeFailureReason = readback.camera.first_frame_probe_failure_reason
    || readback.camera.source_failure_reason
    || "none";
  const meaningfulCameraText = (value: string | undefined): string => {
    const text = (value || "").trim();
    return text && text !== "not_loaded" && text !== "none" ? text : "";
  };
  const plainSentencePart = (value: string): string => value.replace(/[。；;.\s]+$/u, "");
  const cameraSourceDiagnosisHint = plainSentencePart(meaningfulCameraText(readback.camera.source_diagnosis_plain_hint));
  const cameraSourceDiagnosisNextAction = plainSentencePart(meaningfulCameraText(readback.camera.source_diagnosis_next_action_plain));
  const cameraSourceDiagnosisStatus = meaningfulCameraText(readback.camera.source_diagnosis_status);
  const cameraSourceDiagnosisLabel = (status: string): string => ({
    uvc_full_speed_usb_not_exclusive: "USB full-speed",
    uvc_transport_error_not_exclusive: "UVC/USB 传输错误",
    uvc_no_frame_not_exclusive: "UVC 无首帧",
    source_first_frame_failed: "相机源无首帧",
    first_frame_failed: "首帧失败",
  }[status] || status.replace(/_/g, " "));
  const cameraSourceDiagnosisNotExclusive = readback.camera.source_diagnosis_not_exclusive === "true"
    || readback.camera.source_usage_not_exclusive === "true";
  const cameraSourceDiagnosisTail = [
    cameraSourceDiagnosisStatus ? `诊断=${cameraSourceDiagnosisLabel(cameraSourceDiagnosisStatus)}` : "",
    cameraSourceDiagnosisNotExclusive ? "已排除页面独占" : "",
    cameraSourceDiagnosisHint,
    cameraSourceDiagnosisNextAction ? `下一步：${cameraSourceDiagnosisNextAction}` : "",
  ].filter(Boolean).join("；");
  const radarScanMissingObservations = splitDiagnosticList(readback.radar.radar_scan_observation_missing_reasons);
  const mapRadarBlockedReasons = splitDiagnosticList(readback.map.radar_overlay_blocked_reasons);
  const radarMapOverlayStatus = readback.map.radar_overlay_status || readback.radar.radar_overlay_status || "not_loaded";
  const radarMapCurrentPointCount = readback.map.radar_overlay_point_count || readback.radar.radar_overlay_point_count || "not_loaded";
  const radarMapSourcePointCount = readback.map.radar_overlay_source_point_count || readback.radar.radar_overlay_source_point_count || "not_loaded";
  const parsedRadarMapCurrentPointCount = Number(radarMapCurrentPointCount);
  const parsedRadarMapSourcePointCount = Number(radarMapSourcePointCount);
  const radarMapStaleSourcePointsSuppressed = !radarMapPointsVisible
    && Number.isFinite(parsedRadarMapCurrentPointCount)
    && Number.isFinite(parsedRadarMapSourcePointCount)
    && parsedRadarMapCurrentPointCount === 0
    && parsedRadarMapSourcePointCount > 0;
  const radarMapRefreshNextActionPlain = radarMapPointsVisible
    ? "当前地图已有雷达点；继续监看同轮地图画面。"
    : radarMapStaleSourcePointsSuppressed
      ? `旧雷达来源点 ${radarMapSourcePointCount} 个已抑制；先刷新雷达扫描读数，再刷新地图画面，确认同轮雷达点贴图。`
      : "先刷新雷达扫描读数，再刷新地图画面，确认地图雷达点来自同轮新读数。";
  const radarOverlayNeedsRefresh = !radarMapPointsVisible;
  const radarOverlayBlocksWysiwyg = !radarMapPointsVisible;
  const radarOverlayRecoverySequence: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_refresh_sequence"] = [
    "/api/robot-control/radar/scan-proof/refresh",
    "/api/robot-control/radar/status",
    "/api/robot-control/map/preview",
    "/api/robot-control/summary",
  ];
  const radarOverlayRecoverySequenceLabels: RobotControlLiveClosureSummary["live_wysiwyg_radar_map_refresh_sequence_labels"] = [
    "刷新雷达扫描读数",
    "读取雷达状态",
    "刷新地图画面",
    "刷新总览",
  ];
  const radarStartMapWysiwygSequence = [
    "/api/robot-control/radar/start",
    "/api/robot-control/summary",
    "/api/robot-control/radar/scan-proof/refresh",
    "/api/robot-control/radar/status",
    "/api/robot-control/map/preview",
  ];
  const radarStartMapWysiwygSequenceLabels = [
    "启动雷达",
    "读取当前卡点",
    "刷新雷达扫描读数",
    "读取雷达状态",
    "刷新地图画面",
  ];
  const radarMapCurrentVsSourcePlain = radarMapPointsVisible
    ? `地图雷达点：当前 ${radarMapCurrentPointCount} 个，来源 ${radarMapSourcePointCount} 个；状态=${radarMapOverlayStatus}，已贴到当前地图。`
    : radarMapStaleSourcePointsSuppressed
      ? `地图雷达点：当前 ${radarMapCurrentPointCount} 个，来源 ${radarMapSourcePointCount} 个；状态=${radarMapOverlayStatus}，旧来源点已抑制，未贴到当前地图。下一步：${radarMapRefreshNextActionPlain}`
      : `地图雷达点：当前 ${radarMapCurrentPointCount} 个，来源 ${radarMapSourcePointCount} 个；状态=${radarMapOverlayStatus}。下一步：${radarMapRefreshNextActionPlain}`;
  const cameraUsbSpeed = readback.camera.uvc_usb_topology_video_usb_speed || "not_loaded";
  const cameraUsbFullSpeedDetected = cameraUsbSpeed === "12M" || readback.camera.source_diagnosis_status === "uvc_full_speed_usb_not_exclusive";
  const cameraHardwareActionRequired = cameraUsbFullSpeedDetected && !cameraCurrentVisible;
  const cameraHardwareActionLabel = cameraHardwareActionRequired ? "换高速USB后复测" : "复测相机首帧";
  const cameraRecoveryStatus = cameraCurrentVisible
    ? "visible"
    : cameraSourceDiagnosisNotExclusive
      ? "not_exclusive_needs_source_check"
      : cameraSourceDiagnosisStatus
        ? "source_diagnosed"
        : liveWysiwygReadbackGapSurfaceIds.includes("camera")
          ? "needs_readback"
          : "needs_probe";
  const cameraRecoveryHasSpecificSourceAction = Boolean(cameraSourceDiagnosisNextAction)
    && !/打开页面会自动接入共享 MJPEG|只读检查复测首帧/u.test(cameraSourceDiagnosisNextAction);
  const cameraRecoverySpecificSourceAction = cameraSourceDiagnosisNotExclusive
    ? cameraSourceDiagnosisNextAction.replace(/；共享预览不是页面独占$/u, "")
    : cameraSourceDiagnosisNextAction;
  const cameraRecoveryNextActionPlain = cameraCurrentVisible
    ? "相机画面已显示；继续监看共享实时预览。"
    : cameraHardwareActionRequired
      ? `相机不是页面独占；诊断显示 ${cameraSourceDiagnosisLabel(cameraSourceDiagnosisStatus)}；先${cameraHardwareActionLabel}，再读取共享预览状态。当前硬件提示：${cameraRecoverySpecificSourceAction || "摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub 后复测"}。`
      : cameraRecoveryHasSpecificSourceAction
      ? cameraSourceDiagnosisNotExclusive
        ? `相机不是页面独占；诊断显示 ${cameraSourceDiagnosisLabel(cameraSourceDiagnosisStatus)}；先复测相机首帧并读取共享预览状态。若仍无画面，${cameraRecoverySpecificSourceAction}。`
        : `先复测相机首帧并读取共享预览状态；若仍无画面，按诊断处理：${cameraRecoverySpecificSourceAction}。`
      : cameraSourceDiagnosisNotExclusive
        ? "相机不是页面独占；先复测相机首帧并读取共享预览状态。若仍无画面，检查 USB 线、接口、摄像头供电或换 known-good UVC 后再复测。"
        : "先复测相机首帧并读取共享预览状态；拿到首帧后再刷新当前所见和建图条件。";
  const cameraRecoverySequence = [
    "/api/robot-control/camera/first-frame/probe",
    "/api/robot-control/camera/mjpeg/status",
    "/api/robot-control/summary",
  ];
  const cameraRecoverySequenceLabels = [
    "复测相机首帧",
    "读取共享预览状态",
    "刷新当前卡点",
  ];
  const cameraDiagnosticPlain = cameraCurrentVisible
    ? "画面诊断：当前页面已有实时画面。"
    : cameraSourceDiagnosisTail
      ? `画面诊断：首帧未证明；状态=${cameraProbeStatusLabel(readback.camera.first_frame_probe_status || "not_loaded")}；原因=${cameraFailureLabel(cameraProbeFailureReason || "not_loaded")}；${cameraSourceDiagnosisTail}。`
      : `画面诊断：首帧未证明；状态=${cameraProbeStatusLabel(readback.camera.first_frame_probe_status || "not_loaded")}；原因=${cameraFailureLabel(cameraProbeFailureReason || "not_loaded")}。`;
  const radarDiagnosticPlain = radarMapPointsVisible
    ? "雷达诊断：当前雷达点已贴到地图。"
    : radarMapStaleSourcePointsSuppressed
      ? `雷达诊断：服务=${readback.radar.lifecycle_running || "not_loaded"}/${readback.radar.lifecycle_state || "not_loaded"}；新读数=${readback.radar.latest_scan_proof_fresh || "not_loaded"}；旧来源点 ${radarMapSourcePointCount} 个未贴图。下一步：刷新雷达扫描读数，再刷新地图画面。`
      : `雷达诊断：服务=${readback.radar.lifecycle_running || "not_loaded"}/${readback.radar.lifecycle_state || "not_loaded"}；新读数=${readback.radar.latest_scan_proof_fresh || "not_loaded"}；还差=${diagnosticLabelsPlain(radarScanMissingObservations)}。`;
  const mapRadarDiagnosticPlain = radarMapPointsVisible
    ? "地图雷达诊断：当前地图已有雷达点。"
    : radarMapStaleSourcePointsSuppressed
      ? `地图雷达诊断：当前点=${readback.map.radar_overlay_point_count || "not_loaded"}；来源点=${readback.map.radar_overlay_source_point_count || "not_loaded"}；旧来源点已抑制，不贴到当前地图。下一步：刷新雷达扫描读数，再刷新地图画面。`
      : `地图雷达诊断：当前点=${readback.map.radar_overlay_point_count || "not_loaded"}；来源点=${readback.map.radar_overlay_source_point_count || "not_loaded"}；还差=${diagnosticLabelsPlain(mapRadarBlockedReasons)}。`;
  const liveWysiwygDiagnosticPlain = `${cameraDiagnosticPlain} ${radarDiagnosticPlain} ${mapRadarDiagnosticPlain}`;
  const liveSurfaceEvidenceLabel = (id: string): string => ({
    camera_current_frame_visible: "当前页面画面帧",
    camera_first_frame: "相机首帧",
    map_current_image_visible: "当前地图画面",
    radar_current_map_points_visible: "当前地图雷达点",
    scan_preview_points_missing: "地图缺雷达点",
    runtime_scan_stale_for_map_radar_overlay: "雷达点不是当前新读数",
    robot_pose_missing_for_map_radar_overlay: "小车地图位置未读到",
  }[id] || diagnosticLabel(id));
  const liveSurfaceProofStatus = (
    visible: boolean,
    readbackGap: boolean,
  ): RobotControlLiveWysiwygSurfaceSummary["proof_status"] => {
    // 已显示、可只读刷新、读回断档三种状态分开，普通页面才能把下一步落到具体入口。
    if (visible) {
      return "completed";
    }
    return readbackGap ? "blocked" : "ready_to_refresh";
  };
  const liveSurfaceProofPlain = (
    label: string,
    visible: boolean,
    visiblePlain: string,
    missingEvidence: string[],
  ): string => {
    if (visible) {
      return `${label}已对齐：${visiblePlain}。`;
    }
    const missingPlain = missingEvidence.map(liveSurfaceEvidenceLabel).join("、") || "当前显示";
    return `${label}未对齐；还差：${missingPlain}。`;
  };
  const cameraSurfaceMissingEvidence = cameraCurrentVisible
    ? []
    : cameraSourceDiagnosisNotExclusive
      ? ["camera_first_frame"]
      : ["camera_current_frame_visible"];
  const mapSurfaceMissingEvidence = mapCurrentVisible ? [] : ["map_current_image_visible"];
  const radarSurfaceMissingEvidence = radarMapPointsVisible
    ? []
    : Array.from(new Set(mapRadarBlockedReasons.length > 0 ? mapRadarBlockedReasons : ["radar_current_map_points_visible"]));
  const liveWysiwygSurfaceSummaries: NonNullable<RobotControlSummaryResponse["live_closure_summary"]>["live_wysiwyg_surface_summaries"] = [
    {
      id: "camera",
      visible: cameraCurrentVisible,
      readback_gap: liveWysiwygReadbackGapSurfaceIds.includes("camera"),
      completed: cameraCurrentVisible,
      proof_status: liveSurfaceProofStatus(cameraCurrentVisible, liveWysiwygReadbackGapSurfaceIds.includes("camera")),
      missing_evidence: cameraSurfaceMissingEvidence,
      proof_plain: liveSurfaceProofPlain("画面", cameraCurrentVisible, "当前页面已有实时画面", cameraSurfaceMissingEvidence),
      status_plain: readback.camera.camera_wysiwyg_status_plain || camera.summary_plain,
      next_action_plain: readback.camera.camera_wysiwyg_next_action_plain || camera.next_action_plain,
      fixed_refresh_endpoint: "/api/robot-control/camera/first-frame/probe",
      sends_motion_when_clicked: false,
    },
    {
      id: "map",
      visible: mapCurrentVisible,
      readback_gap: liveWysiwygReadbackGapSurfaceIds.includes("map"),
      completed: mapCurrentVisible,
      proof_status: liveSurfaceProofStatus(mapCurrentVisible, liveWysiwygReadbackGapSurfaceIds.includes("map")),
      missing_evidence: mapSurfaceMissingEvidence,
      proof_plain: liveSurfaceProofPlain("地图", mapCurrentVisible, "当前地图画面已显示", mapSurfaceMissingEvidence),
      status_plain: readback.map.map_wysiwyg_status_plain || map.summary_plain,
      next_action_plain: readback.map.map_wysiwyg_next_action_plain || readback.map.map_next_action_plain || map.next_action_plain,
      fixed_refresh_endpoint: "/api/robot-control/map/preview",
      sends_motion_when_clicked: false,
    },
    {
      id: "radar_map_points",
      visible: radarMapPointsVisible,
      readback_gap: liveWysiwygReadbackGapSurfaceIds.includes("radar_map_points"),
      completed: radarMapPointsVisible,
      proof_status: liveSurfaceProofStatus(radarMapPointsVisible, liveWysiwygReadbackGapSurfaceIds.includes("radar_map_points")),
      missing_evidence: radarSurfaceMissingEvidence,
      proof_plain: liveSurfaceProofPlain("雷达点", radarMapPointsVisible, "当前地图已有雷达点", radarSurfaceMissingEvidence),
      status_plain: readback.radar.radar_overlay_wysiwyg_status_plain || radar.summary_plain,
      next_action_plain: readback.radar.radar_overlay_wysiwyg_next_action_plain || readback.radar.radar_next_action_plain || radar.next_action_plain,
      fixed_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh",
      sends_motion_when_clicked: false,
    },
  ];
  const liveWysiwygSurfaceLabel = (id: string): string => ({
    camera: cameraHardwareActionRequired ? "换高速USB后复测相机首帧" : "复测相机首帧",
    map: "刷新地图画面",
    radar_map_points: "刷新雷达扫描读数",
  }[id] ?? id);
  const liveWysiwygMissingSurfaceRefreshItems = liveWysiwygMissingSurfaceIds
    .map((id) => liveWysiwygSurfaceSummaries.find((surface) => surface.id === id))
    .filter((surface): surface is RobotControlLiveWysiwygSurfaceSummary => Boolean(surface));
  const liveWysiwygMissingSurfaceRefreshEndpoints = liveWysiwygMissingSurfaceRefreshItems.map((surface) => surface.fixed_refresh_endpoint);
  const liveWysiwygMissingSurfaceRefreshLabels = liveWysiwygMissingSurfaceRefreshItems.map((surface) => liveWysiwygSurfaceLabel(surface.id));
  const liveWysiwygPrimaryRefreshItem = (
    // 相机已经诊断成硬件/USB blocker 时，优先给普通用户一个能 no-motion 修复的雷达贴图动作。
    cameraHardwareActionRequired
      ? liveWysiwygMissingSurfaceRefreshItems.find((surface) => surface.id === "radar_map_points")
      : null
  ) ?? liveWysiwygMissingSurfaceRefreshItems[0] ?? null;
  const liveWysiwygPrimarySurfaceId = liveWysiwygPrimaryRefreshItem?.id ?? "none";
  const liveWysiwygPrimaryRefreshEndpoint = liveWysiwygPrimaryRefreshItem?.fixed_refresh_endpoint ?? "none";
  const liveWysiwygPrimaryRefreshLabel = liveWysiwygPrimaryRefreshItem
    ? liveWysiwygSurfaceLabel(liveWysiwygPrimaryRefreshItem.id)
    : "无";
  const freeMoveStartReady = boundary.free_roam_motion_start_ready || goalSummary.ready_action_ids.includes("free_move");
  const freeRoamMotionReady = readback.free_roam.free_roam_motion_ready === "true" || readback.free_roam.motion_ready === "true";
  const rawMappingStartMissingReasons = boundary.free_roam_mapping_start_missing_reasons;
  const mappingAcceptanceMissingReasons = boundary.free_roam_mapping_missing_reasons;
  const rawMappingLidarBlocksStart = rawMappingStartMissingReasons.includes("lidar_fresh");
  const mappingLidarFreshReadbackReady = readback.radar.latest_scan_proof_fresh === "true"
    && readback.radar.lifecycle_running === "true"
    && ["loaded", "partial"].includes(radarMapOverlayStatus);
  const mappingLidarFreshGateConflict = rawMappingLidarBlocksStart && mappingLidarFreshReadbackReady;
  const mappingStartMissingReasons = rawMappingStartMissingReasons.filter((reason) =>
    !(reason === "lidar_fresh" && mappingLidarFreshReadbackReady)
  );
  const mappingStartReady = boundary.free_roam_mapping_start_ready
    || goalSummary.ready_action_ids.includes("mapping_start")
    || (freeMoveStartReady && mappingStartMissingReasons.length === 0);
  const mappingCameraBlocksStart = mappingStartMissingReasons.includes("camera_first_frame");
  const mappingLidarBlocksStart = mappingStartMissingReasons.includes("lidar_fresh");
  const mappingLidarFreshGateStatus = mappingLidarFreshGateConflict
    ? "readback_ready_boundary_missing"
    : mappingLidarBlocksStart
      ? "missing"
      : mappingLidarFreshReadbackReady
        ? "ready"
        : "not_loaded";
  const mappingLidarFreshRefreshSequence = [
    "/api/robot-control/radar/scan-proof/refresh",
    "/api/robot-control/radar/status",
    "/api/robot-control/summary",
  ];
  const mappingLidarFreshRefreshSequenceLabels = [
    "刷新雷达扫描读数",
    "读取雷达状态",
    "刷新总览",
  ];
  const mappingLidarFreshNextActionPlain = mappingLidarFreshGateConflict
    ? "雷达读回已显示 fresh 且地图贴图已加载，但建图安全边界仍缺 lidar_fresh；先只读刷新雷达扫描、读取雷达状态，再刷新 summary 复核 gate。"
    : mappingLidarBlocksStart
      ? "建图启动仍缺雷达新鲜读数；先只读刷新雷达扫描并读取雷达状态，再刷新 summary。"
      : mappingLidarFreshReadbackReady
        ? "建图雷达新鲜 gate 已满足；继续处理相机首帧或其他建图条件。"
        : "建图雷达新鲜读回尚未证明；先只读刷新雷达扫描、读取雷达状态，再刷新 summary，避免把旧读数当作 ready。";
  const mappingStartMissingPlain = [
    ...(mappingCameraBlocksStart ? ["画面首帧"] : []),
    ...(mappingLidarBlocksStart ? ["雷达新鲜"] : []),
    ...mappingStartMissingReasons.filter((reason) => !["camera_first_frame", "lidar_fresh"].includes(reason)),
  ].join("、") || "传感器条件";
  const mappingStartUnblockPlain = (() => {
    if (mappingStartReady) {
      return "建图启动已就绪：画面首帧和雷达新鲜都满足；勾现场安全确认后可启动建图记录。";
    }
    const cameraDiagnosisPlain = plainSentencePart(
      meaningfulCameraText(readback.camera.source_diagnosis_plain_hint)
      || meaningfulCameraText(readback.camera.source_diagnosis_next_action_plain)
      || meaningfulCameraText(readback.camera.camera_wysiwyg_next_action_plain)
      || meaningfulCameraText(camera.next_action_plain),
    );
    const cameraTail = mappingCameraBlocksStart
      ? `当前相机提示：${cameraDiagnosisPlain}`
      : "相机首帧已满足。";
    return `建图启动还差：${mappingStartMissingPlain}；自由移动仍可先做，不被相机/雷达画面缺口阻塞。${cameraTail}；只读复测相机首帧和 MJPEG 状态，首帧 ready 后再启动建图。`;
  })();
  const cameraReprobeSequence = [
    "/api/robot-control/camera/first-frame/probe",
    "/api/robot-control/camera/mjpeg/status",
    "/api/robot-control/summary",
  ];
  const keyboardControlStartReady = keyboard.evidence?.keyboard_start_ready === true
    || readback.keyboard.keyboard_control_start_ready === "true";
  const keyboardContinuousControlReady = keyboardControlStartReady
    && readback.keyboard.continuous_control_ready === "true";
  const keyboardHoldToMoveRequired = keyboard.evidence?.hold_to_move_required === true
    || readback.keyboard.hold_to_move_required === "true";
  const keyboardEnabled = keyboard.evidence?.keyboard_enabled === true
    || readback.keyboard.enabled === "true";
  const keyboardMotionVerified = keyboard.evidence?.keyboard_motion_verified === true;
  const keyboardStopSettledAfterPulse = keyboard.evidence?.keyboard_stop_settled_after_pulse === true;
  const keyboardBestContinuousPulseCount = keyboard.evidence?.keyboard_best_continuous_pulse_count ?? 0;
  const keyboardVerifiedMinForwardedPulses = keyboard.evidence?.keyboard_verified_min_forwarded_pulses ?? 2;
  const minimalPrecheckSafetyOnly = nav2.evidence?.minimal_precheck_safety_only === true
    || boundary.nav2_goal_minimal_precheck_plain.includes("只需要现场安全确认");
  const wheelRerunCommandMode = nav2.evidence?.next_base_command_mode || readback.nav2.next_execution_base_command_mode || "not_loaded";
  const wheelRerunLastBaseCommandMode = readback.nav2.goal_execution_base_command_mode || readback.nav2.goal_execution_base_command_latest_nonzero_mode || "not_loaded";
  const wheelRerunNextBaseCommandMode = wheelRerunCommandMode;
  const wheelRerunFeedbackSampleCount = readback.nav2.goal_execution_base_feedback_sample_count || "not_loaded";
  const wheelRerunFeedbackNonzeroSampleCount = readback.nav2.goal_execution_base_feedback_nonzero_sample_count || "not_loaded";
  const wheelRerunLatestRawLeft = readback.nav2.goal_execution_base_feedback_latest_raw_left
    || readback.nav2.goal_execution_base_feedback_latest_left_speed
    || "not_loaded";
  const wheelRerunLatestRawRight = readback.nav2.goal_execution_base_feedback_latest_raw_right
    || readback.nav2.goal_execution_base_feedback_latest_right_speed
    || "not_loaded";
  const wheelRerunImuDeltaObserved = readback.nav2.goal_execution_base_feedback_imu_attitude_delta_observed || "not_loaded";
  const wheelRerunImuRollDelta = readback.nav2.goal_execution_base_feedback_imu_roll_delta || "not_loaded";
  const wheelRerunImuPitchDelta = readback.nav2.goal_execution_base_feedback_imu_pitch_delta || "not_loaded";
  const wheelRerunModeRerunStatus = readback.nav2.goal_execution_mode_rerun_status || "not_loaded";
  const wheelRerunModeRerunPlain = readback.nav2.goal_execution_mode_rerun_plain || "还没有可用的路线执行模式复验结论。";
  const wheelRerunNextModePlain = readback.nav2.goal_execution_next_mode_plain || "下次底盘模式未读到。";
  const wheelRerunBaseCommandNonzeroObserved = readback.nav2.goal_execution_base_command_nonzero_observed || "not_loaded";
  const wheelRerunBaseCommandNonzeroCount = readback.nav2.goal_execution_base_command_nonzero_count || "not_loaded";
  const wheelRerunBaseCommandLatestNonzeroMode = readback.nav2.goal_execution_base_command_latest_nonzero_mode || "not_loaded";
  const wheelRerunBaseCommandModeCounts = readback.nav2.goal_execution_base_command_mode_counts || "not_loaded";
  const wheelRerunControlDiagnosisPlain = needsSameWindowWheelRerun
    ? [
      wheelRerunModeRerunPlain,
      `上次 ${wheelRerunLastBaseCommandMode.toUpperCase()} 模式已记录 ${wheelRerunBaseCommandNonzeroCount} 次非零底盘命令，最新非零命令模式=${wheelRerunBaseCommandLatestNonzeroMode}；IMU 姿态变化=${wheelRerunImuDeltaObserved}，轮速 L/R 仍为 ${wheelRerunLatestRawLeft}/${wheelRerunLatestRawRight}。`,
      `下一次执行会用 ${wheelRerunNextBaseCommandMode.toUpperCase()} 模式复验控制链；这不是雷达、相机或地图所见缺口。`,
    ].join(" ")
    : "当前不需要底盘模式复验。";
  const wheelRerunReadbackPlain = needsSameWindowWheelRerun
    ? `上次执行窗口轮速 L/R=${wheelRerunLatestRawLeft}/${wheelRerunLatestRawRight}，样本 ${wheelRerunFeedbackSampleCount} 个，非零样本 ${wheelRerunFeedbackNonzeroSampleCount} 个；${wheelRerunNextModePlain} 重跑后读取 latest 与只读轮速采样。`
    : "当前不需要轮速复验。";
  const wheelRerunAcceptanceEndpoints = [
    "/api/robot-control/map/preview",
    "/api/robot-control/nav2/goal/execution/latest",
    "/api/robot-control/base/feedback-samples",
    "/api/robot-control/delivery/latest",
    "/api/robot-control/summary",
  ];
  const wheelRerunChecklistPlain = needsSameWindowWheelRerun
    ? "重跑闭环：先勾现场安全确认，再执行图上路线；执行后依次读取地图路线画面、latest、底盘轮速采样和 summary，确认图上路线仍可见并确认同窗口 wheel L/R 非零；轮速闭环后再到送达区做送达确认，确认送达不发车。"
    : "当前不需要重跑图上路线；如果后续出现同窗口轮速缺口，再按安全确认、执行、轮速读回、送达确认顺序收口。";
  const wheelRerunAcceptancePlain = "验收口径：地图仍显示本轮图上路线，Nav2 latest 为 goal_succeeded，同一执行窗口 wheel L/R 非零，summary 不再显示 needs_wheel_rerun，最后送达确认与本轮行程材料对齐。";
  const wheelRerunRequiredSuccessMarkers = [
    "map_route_visible",
    "nav2_goal_succeeded",
    "same_window_wheel_lr_nonzero",
    "delivery_success",
  ];
  const wheelRerunReadyForSafetyConfirm = needsSameWindowWheelRerun && routeReadyOnMap;
  const wheelRerunCurrentGapPlain = needsSameWindowWheelRerun
    ? `当前缺口：同窗口 wheel L/R 非零尚未闭环；当前读数 L/R=${wheelRerunLatestRawLeft}/${wheelRerunLatestRawRight}，非零样本 ${wheelRerunFeedbackNonzeroSampleCount}/${wheelRerunFeedbackSampleCount}。`
    : "当前不需要同窗口轮速复验。";
  const wheelRerunNoExtraPrecheckPlain = "重跑图上路线的发车前预检只看现场安全确认；相机、雷达、地图所见缺口不作为额外发车前置，路线执行后再按读回端点验收。";
  const wheelRerunDeliveryNextActionPlain = deliveryClaimReady
    ? "送达成功已经写入当前材料；轮速复验通过后可直接进入本轮闭环复核。"
    : "轮速复验通过后，到送达区逐项确认并提交送达确认；该提交只写送达材料，不发车。";
  const evidenceLabelPlain = (id: string): string => ({
    nav2_goal_succeeded: "图上行程到点成功",
    same_window_wheel_lr_nonzero: "同窗口 wheel L/R 非零",
    delivery_success: "送达确认",
    same_hold_window_wheel_lr_nonzero: "按住同窗口 wheel L/R 非零",
    stop_after_release: "松开/失焦后 stop 已落稳",
    free_roam_latest_motion_ready: "自由移动运行读数",
    camera_first_frame: "相机首帧",
    lidar_fresh: "雷达新鲜读数",
  }[id] ?? id.replace(/_/g, " "));
  const evidencePlain = (items: string[]): string => items.map(evidenceLabelPlain).join("、") || "无";
  const runNav2RouteMissingEvidence = [
    ...(!nav2GoalExecutionProven ? ["nav2_goal_succeeded"] : []),
    ...(!wheelLrNonzeroProven ? ["same_window_wheel_lr_nonzero"] : []),
    ...(!deliveryClaimReady ? ["delivery_success"] : []),
  ];
  const keyboardMissingEvidence = [
    ...(!keyboardMotionVerified ? ["same_hold_window_wheel_lr_nonzero"] : []),
    ...(!keyboardStopSettledAfterPulse ? ["stop_after_release"] : []),
  ];
  const freeMoveMotionProven = readback.free_roam.motion_ready === "true"
    || readback.free_roam.free_roam_motion_ready === "true";
  const freeMoveMissingEvidence = freeMoveMotionProven ? [] : ["free_roam_latest_motion_ready"];
  const mappingMissingEvidence = mappingStartReady ? [] : mappingStartMissingReasons;
  const proofStatus = (ready: boolean, missing: string[]): "completed" | "ready_to_verify" | "blocked" => {
    if (missing.length === 0) {
      return "completed";
    }
    return ready ? "ready_to_verify" : "blocked";
  };
  const proofPlain = (ready: boolean, missing: string[], donePlain: string, verifyPlain: string, blockedPlain: string): string => {
    if (missing.length === 0) {
      return donePlain;
    }
    if (ready) {
      return `${verifyPlain}；还差：${evidencePlain(missing)}。`;
    }
    return `${blockedPlain}；还差：${evidencePlain(missing)}。`;
  };
  const runNav2RouteDisplayLabel = needsSameWindowWheelRerun ? "重跑图上行程并复验轮速" : "完整行程执行";
  const liveMotionRunbookItems: NonNullable<RobotControlSummaryResponse["live_closure_summary"]>["live_motion_runbook_items"] = [
    {
      id: "run_nav2_route",
      label: "完整行程执行",
      display_label: runNav2RouteDisplayLabel,
      ready: routeReadyOnMap || needsSameWindowWheelRerun,
      completed: runNav2RouteMissingEvidence.length === 0,
      proof_status: proofStatus(routeReadyOnMap || needsSameWindowWheelRerun, runNav2RouteMissingEvidence),
      missing_evidence: runNav2RouteMissingEvidence,
      proof_plain: proofPlain(
        routeReadyOnMap || needsSameWindowWheelRerun,
        runNav2RouteMissingEvidence,
        "完整行程已闭环：Nav2 到点、同窗口轮速和送达确认都已满足。",
        "可复验完整行程：勾现场安全确认后执行图上路线，执行后按验收端点读回",
        "完整行程暂不可复验",
      ),
      minimal_precheck_safety_only: minimalPrecheckSafetyOnly,
      safety_confirm_required: routeReadyOnMap || needsSameWindowWheelRerun,
      sends_motion_when_executed: true,
      start_endpoint: "/api/robot-control/nav2/goal/execute",
      stop_endpoint: "/api/robot-control/base/stop",
      acceptance_endpoints: [
        "/api/robot-control/map/preview",
        "/api/robot-control/nav2/goal/execution/latest",
        "/api/robot-control/base/feedback-samples",
        "/api/robot-control/delivery/latest",
        "/api/robot-control/summary",
      ],
      acceptance_plain: "执行后读取地图路线画面、latest、同窗口 wheel L/R、送达 latest 和 summary，确认图上路线、到点成功、轮速非零且送达确认已记录。",
      blocked_reasons: routeReadyOnMap || needsSameWindowWheelRerun ? [] : ["route_not_ready_on_map"],
    },
    {
      id: "hold_keyboard",
      label: "键盘连续手控",
      display_label: "键盘连续手控",
      ready: keyboardContinuousControlReady,
      completed: keyboardMissingEvidence.length === 0,
      proof_status: proofStatus(keyboardContinuousControlReady, keyboardMissingEvidence),
      missing_evidence: keyboardMissingEvidence,
      proof_plain: proofPlain(
        keyboardContinuousControlReady,
        keyboardMissingEvidence,
        "键盘连续手控已闭环：按住窗口轮速非零，松开/失焦后 stop 已落稳。",
        "可验证键盘连续手控：勾现场安全确认后按住方向键或 WASD，再读轮速与 summary",
        "键盘连续手控暂不可验证",
      ),
      minimal_precheck_safety_only: true,
      safety_confirm_required: keyboardContinuousControlReady,
      sends_motion_when_executed: true,
      start_endpoint: "/api/robot-control/base/manual",
      stop_endpoint: "/api/robot-control/base/stop",
      acceptance_endpoints: [
        "/api/robot-control/base/feedback-samples",
        "/api/robot-control/summary",
      ],
      acceptance_plain: "启用后按住方向键或 WASD，松开会 stop；按住窗口后读取 wheel L/R 非零和 summary。",
      blocked_reasons: keyboardContinuousControlReady ? [] : ["keyboard_continuous_not_ready"],
    },
    {
      id: "start_free_move",
      label: "自由自助移动",
      display_label: "自由自助移动",
      ready: freeMoveStartReady,
      completed: freeMoveMissingEvidence.length === 0,
      proof_status: proofStatus(freeMoveStartReady, freeMoveMissingEvidence),
      missing_evidence: freeMoveMissingEvidence,
      proof_plain: proofPlain(
        freeMoveStartReady,
        freeMoveMissingEvidence,
        "自由自助移动已闭环：free-roam latest 已证明可运行。",
        "可验证自由自助移动：勾现场安全确认后启动，再读 free-roam latest、地图预览和 summary",
        "自由自助移动暂不可验证",
      ),
      minimal_precheck_safety_only: true,
      safety_confirm_required: freeMoveStartReady,
      sends_motion_when_executed: true,
      start_endpoint: "/api/robot-control/free-roam/autonomy/start",
      stop_endpoint: "/api/robot-control/free-roam/autonomy/stop",
      acceptance_endpoints: [
        "/api/robot-control/free-roam/autonomy/latest",
        "/api/robot-control/map/preview",
        "/api/robot-control/summary",
      ],
      acceptance_plain: "启动后读取 free-roam latest、地图预览和 summary；相机、雷达不作为自由移动发车前置。",
      blocked_reasons: freeMoveStartReady ? [] : ["free_move_not_ready"],
    },
    {
      id: "start_mapping_when_sensors_ready",
      label: "传感器就绪后建图",
      display_label: "传感器就绪后建图",
      ready: mappingStartReady,
      completed: mappingMissingEvidence.length === 0,
      proof_status: proofStatus(mappingStartReady, mappingMissingEvidence),
      missing_evidence: mappingMissingEvidence,
      proof_plain: proofPlain(
        mappingStartReady,
        mappingMissingEvidence,
        "建图启动条件已满足：相机首帧和雷达新鲜读数都 ready。",
        "可启动建图：勾现场安全确认后启动建图，再读地图预览和 summary",
        "建图暂不可启动",
      ),
      minimal_precheck_safety_only: true,
      safety_confirm_required: mappingStartReady,
      sends_motion_when_executed: true,
      start_endpoint: "/api/robot-control/map/start",
      stop_endpoint: "/api/robot-control/free-roam/autonomy/stop",
      acceptance_endpoints: [
        "/api/robot-control/free-roam/autonomy/latest",
        "/api/robot-control/map/preview",
        "/api/robot-control/summary",
      ],
      acceptance_plain: "相机首帧和雷达 fresh 后启动建图；随后读取 free-roam latest、地图预览和 summary 确认状态机和地图所见即所得。",
      blocked_reasons: mappingStartReady ? [] : mappingStartMissingReasons,
    },
  ];
  const liveMotionRunbookReadyItems = liveMotionRunbookItems.filter((item) => item.ready);
  const liveMotionRunbookBlockedItems = liveMotionRunbookItems.filter((item) => !item.ready);
  const liveMotionRunbookPrimaryActionId = (() => {
    if (needsSameWindowWheelRerun && liveMotionRunbookReadyItems.some((item) => item.id === "run_nav2_route")) {
      return "run_nav2_route" as const;
    }
    return liveMotionRunbookReadyItems[0]?.id ?? "none";
  })();
  const liveMotionRunbookStartEndpoints = Array.from(new Set(liveMotionRunbookReadyItems.map((item) => item.start_endpoint)));
  const liveMotionRunbookAcceptanceEndpoints = Array.from(new Set(liveMotionRunbookItems.flatMap((item) => item.acceptance_endpoints)));
  const liveMotionRunbookReadyLabels = liveMotionRunbookReadyItems.map((item) => item.display_label ?? item.label);
  const liveMotionRunbookBlockedLabels = liveMotionRunbookBlockedItems.map((item) => item.display_label ?? item.label);
  const liveMotionRunbookPrimaryAction = liveMotionRunbookItems.find((item) => item.id === liveMotionRunbookPrimaryActionId);
  const liveMotionRunbookPrimaryActionLabel = liveMotionRunbookPrimaryAction?.display_label ?? liveMotionRunbookPrimaryAction?.label ?? "暂无";
  const liveMotionRunbookReadyPlain = liveMotionRunbookReadyLabels.length > 0
    ? `可先执行：${liveMotionRunbookReadyLabels.join("、")}。`
    : "暂无可执行运动入口；先刷新小车状态。";
  const liveMotionRunbookBlockedPlain = liveMotionRunbookBlockedLabels.length > 0
    ? `暂不可执行：${liveMotionRunbookBlockedLabels.join("、")}。`
    : "暂无被阻塞的运动入口。";
  const liveMotionRunbookMinimalPrecheckPlain = "发车前预检已精简：执行运动只需勾现场安全确认；相机、雷达和现场报告不作为额外发车前置。";
  const liveMotionRunbookSummaryPlain = `${liveMotionRunbookReadyPlain}${liveMotionRunbookBlockedPlain}主推荐：${liveMotionRunbookPrimaryActionLabel}；${liveMotionRunbookMinimalPrecheckPlain}`;
  const nav2GoalSucceeded = nav2GoalExecutionProven;
  const allWysiwygReady = cameraCurrentVisible && mapCurrentVisible && radarMapPointsVisible;
  const status = (() => {
    if (nav2GoalSucceeded && wheelLrNonzeroProven && deliveryClaimReady && allWysiwygReady) {
      return "complete";
    }
    if (needsSameWindowWheelRerun) {
      return "needs_wheel_rerun";
    }
    if (nav2GoalSucceeded && wheelLrNonzeroProven && !deliveryClaimReady) {
      return "needs_delivery";
    }
    if (!allWysiwygReady) {
      return "needs_wysiwyg";
    }
    if (routeReadyOnMap || freeMoveStartReady || goalSummary.motion_ready_count > 0) {
      return "needs_safety_confirm";
    }
    if (mappingStartReady) {
      return "needs_sensor";
    }
    return "not_ready";
  })();
  const labels: Record<NonNullable<RobotControlSummaryResponse["live_closure_summary"]>["status"], string> = {
    complete: "已闭环",
    ready_for_motion: "可先动",
    needs_safety_confirm: "待安全确认",
    needs_wheel_rerun: "待轮速复验",
    needs_delivery: "待送达",
    needs_wysiwyg: "待当前所见",
    needs_sensor: "待传感器",
    not_ready: "未就绪",
  };
  const robotApiConnectionNextAction = robotApiConnectionNextActionPlain(robotApiConnection);
  const robotApiConnectionAllReadsFailed = robotApiConnection.status === "degraded" && robotApiConnection.loaded_count === 0;
  const nextActionPlain = (() => {
    if (robotApiConnectionAllReadsFailed) {
      return robotApiConnectionNextAction;
    }
    if (needsSameWindowWheelRerun) {
      return "勾现场安全确认后重跑图上路线，并在同一个执行窗口复验轮速 L/R 非零。";
    }
    if (nav2GoalSucceeded && wheelLrNonzeroProven && !deliveryClaimReady) {
      return "路线和轮速已闭环；下一步在现场确认投递成功并记录送达确认。";
    }
    if (!cameraCurrentVisible) {
      return camera.next_action_plain;
    }
    if (!radarMapPointsVisible) {
      return radar.next_action_plain;
    }
    if (routeReadyOnMap || freeMoveStartReady) {
      return goalSummary.safety_precheck_next_action_plain || goalSummary.motion_next_action_plain;
    }
    return goalSummary.next_action_plain || "先刷新小车状态。";
  })();
  const summaryPlain = (() => {
    if (robotApiConnectionAllReadsFailed) {
      return "当前卡点：PC 已打开，但小车 Robot API 这轮没有任何只读端点返回；先恢复上车连接。";
    }
    if (needsSameWindowWheelRerun) {
      return "当前卡点：图上路线已经有执行成功读数，但同窗口轮速 L/R 还没有非零闭环。";
    }
    if (status === "needs_delivery") {
      return "当前卡点：行程和轮速已满足，送达成功还未写入当前材料。";
    }
    if (status === "needs_wysiwyg") {
      return `当前所见还没齐：画面${cameraCurrentVisible ? "已显示" : "未显示"}，地图${mapCurrentVisible ? "已显示" : "未显示"}，雷达点${radarMapPointsVisible ? "已贴图" : "未贴图"}。`;
    }
    if (status === "needs_safety_confirm") {
      return "车可以进入下一步运动入口；发车前预检保持最小，只需要现场安全确认。";
    }
    if (status === "complete") {
      return "图上路线、同窗口轮速、送达和当前所见都已闭环。";
    }
    return goalSummary.summary_plain || "本轮闭环状态还未读到；先刷新小车状态。";
  })();
  const primaryStatusTarget = (() => {
    // “当前卡点”按钮必须跟状态文案一致；不能在轮速复验时跳去画面卡，避免现场找错入口。
    if (needsSameWindowWheelRerun || status === "needs_delivery") {
      return { itemId: "nav2_route_execution" as const, sourceCardId: "nav2_route" as const };
    }
    if (status === "needs_wysiwyg") {
      if (!cameraCurrentVisible) {
        return { itemId: "camera_wysiwyg" as const, sourceCardId: "camera_preview" as const };
      }
      if (!mapCurrentVisible) {
        return { itemId: "map_wysiwyg" as const, sourceCardId: "map_preview" as const };
      }
      return { itemId: "radar_map_points_wysiwyg" as const, sourceCardId: "radar_map_points" as const };
    }
    if (status === "needs_sensor") {
      return { itemId: "mapping_start" as const, sourceCardId: "mapping_start" as const };
    }
    if (status === "needs_safety_confirm") {
      if (freeMoveStartReady) {
        return { itemId: "free_move" as const, sourceCardId: "free_move" as const };
      }
      if (keyboardContinuousControlReady) {
        return { itemId: "keyboard_continuous_control" as const, sourceCardId: "keyboard_control" as const };
      }
      if (routeReadyOnMap) {
        return { itemId: "nav2_route_execution" as const, sourceCardId: "nav2_route" as const };
      }
    }
    return {
      itemId: goalSummary.first_incomplete_item_id || goalSummary.primary_ready_action_item_id,
      sourceCardId: goalSummary.first_incomplete_source_card_id || goalSummary.primary_ready_action_source_card_id,
    };
  })();
  const liveSideBlockerStillCurrent = (item: (typeof goalSummary.blocked_action_items)[number]): boolean => {
    // live 摘要只描述当前所见；如果同轮画布已经可见，就不能继续把旧 checklist blocker 写进“其它缺口”。
    if (item.id === "camera_wysiwyg") {
      return !cameraCurrentVisible;
    }
    if (item.id === "map_wysiwyg") {
      return !mapCurrentVisible;
    }
    if (item.id === "radar_map_points_wysiwyg") {
      return !radarMapPointsVisible;
    }
    return true;
  };
  const sideBlockerItems = goalSummary.blocked_action_items
    .filter((item) => item.id !== primaryStatusTarget.itemId)
    .filter(liveSideBlockerStillCurrent);
  const readyActionItems = goalSummary.ready_action_items;
  const sideBlockerTitles = sideBlockerItems.map((item) => item.title).join("、") || "暂无";
  const readyActionTitles = readyActionItems.map((item) => item.title).join("、") || "暂无";
  const sideGapSummaryPlain = `其它缺口：${sideBlockerTitles}；可先做：${readyActionTitles}。`;
  const liveWysiwygRefreshSequence = [
    "/api/robot-control/radar/scan-proof/refresh",
    "/api/robot-control/radar/status",
    "/api/robot-control/map/preview",
    "/api/robot-control/camera/first-frame/probe",
    "/api/robot-control/camera/mjpeg/status",
    "/api/robot-control/summary",
  ];
  const liveWysiwygRefreshSequenceLabels = [
    "刷新雷达扫描读数",
    "读取雷达状态",
    "刷新地图画面",
    "复测相机首帧",
    "读取相机 MJPEG 状态",
    "刷新总览",
  ];
  const mapDisplayRos2ObserveTopics = [
    "/map",
    "/scan",
    "/tf",
    "/plan",
    "/local_plan",
    "/amcl_pose",
    "/global_costmap/costmap",
    "/local_costmap/costmap",
  ];
  const mapDisplayRvizRolePlain = "RViz2 只给本地工程调试看 /map、/scan、TF、路径、定位和 costmap；普通用户不需要打开。";
  const mapDisplayFoxgloveRolePlain = "Foxglove 用于远程浏览器大屏观察；先在 ROS2 环境安装并启动 foxglove_bridge，再连接 ws://192.168.1.11:8765。";
  const mapDisplayFoxgloveWebAppUrl = "https://studio.foxglove.dev";
  const mapDisplayEngineeringToolsActionLabel = "工程观察：RViz2 / Foxglove";
  const mapDisplayTooSmallNextActionPlain = "地图太小先点“进入地图大屏”打开 /map，PC 首页和 /map 都把地图画布作为主视图，只保留缩放、只读刷新和工程观察入口；建图、保存和其他卡片都会收起；不需要先开 RViz2。";
  const mapDisplayRos2CompanionAnswerPlain = "ROS2 配套：本地工程调试用 RViz2；远程浏览器观察用 Foxglove bridge + Foxglove Web；普通用户仍默认使用 PC 大地图和 /map。";
  const mapDisplayCompanionPlain = `普通用户地图：进入 /map 使用 PC 大地图，默认 3200% 现场大图，地图画布按 viewport-dominant full-height 处理，点“适配”回到 100% 全图，点“细节放大”可查看局部，最高 6400%，地图、路线、小车位置和雷达点共用同一张 WYSIWYG 画布；${mapDisplayTooSmallNextActionPlain}${mapDisplayRos2CompanionAnswerPlain}ROS2 配套只作工程观察，本地用 RViz2，远程浏览器观察先部署 Foxglove bridge 后打开 Foxglove Web 连接 ws://192.168.1.11:8765；观察项固定为地图、雷达、TF、路径、定位和 costmap，不提供 GoalTool，不发送底盘移动命令。`;
  const keyboardAcceptancePlain = "键盘连续手控验收只看同一次按住窗口的 manual pulse 回包：需要读到 wheel L/R 非零；全局只读采样或旧材料不能替代本次按住读数。";
  const nav2ObjectiveDone = routeReadyOnMap && nav2GoalSucceeded && wheelLrNonzeroProven && !needsSameWindowWheelRerun;
  const keyboardObjectiveDone = keyboardMotionVerified && keyboardStopSettledAfterPulse;
  const freeMoveObjectiveDone = readback.free_roam.motion_ready === "true"
    || readback.free_roam.free_roam_motion_ready === "true";
  const motionObjectiveDoneCount = [
    nav2ObjectiveDone,
    keyboardObjectiveDone,
    freeMoveObjectiveDone,
  ].filter(Boolean).length;
  const motionObjectiveCompleted = motionObjectiveDoneCount === 3;
  const motionObjectiveActionable = routeReadyOnMap || keyboardContinuousControlReady || freeMoveStartReady;
  const motionObjectiveSourceCardId: RobotControlLiveObjectiveAuditItem["source_card_id"] = needsSameWindowWheelRerun
    ? "nav2_route"
    : (goalSummary.primary_ready_action_source_card_id || goalSummary.first_motion_source_card_id || "free_move") as RobotControlLiveObjectiveAuditItem["source_card_id"];
  const motionObjectiveNextActionPlain = needsSameWindowWheelRerun
    ? nextActionPlain
    : goalSummary.primary_ready_action_next_action_plain || nextActionPlain;
  const wysiwygObjectiveDoneCount = [
    cameraCurrentVisible,
    mapCurrentVisible,
    radarMapPointsVisible,
  ].filter(Boolean).length;
  const wysiwygObjectiveCompleted = wysiwygObjectiveDoneCount === 3;
  const mappingObjectiveCompleted = freeMoveStartReady && mappingStartReady;
  const mappingObjectiveMissingCount = [!freeMoveStartReady, !mappingStartReady].filter(Boolean).length;
  const objectiveAuditItems: RobotControlLiveObjectiveAuditItem[] = [
    {
      id: "motion",
      title: "行程/键盘/自由移动",
      state: motionObjectiveCompleted ? "已完成" : motionObjectiveActionable ? "可处理" : "未就绪",
      summary_plain: `图上行程：${nav2ObjectiveDone ? "已闭环" : routeReadyOnMap ? "待轮速复验" : "未就绪"}；键盘：${keyboardObjectiveDone ? "已验证" : keyboardContinuousControlReady ? "可验证" : "未就绪"}；自由移动：${freeMoveObjectiveDone ? "运行中" : freeMoveStartReady ? "可启动" : "未就绪"}。`,
      next_action_plain: motionObjectiveNextActionPlain,
      item_ids: ["nav2_route_execution", "keyboard_continuous_control", "free_move"],
      completed: motionObjectiveCompleted,
      actionable: motionObjectiveActionable,
      missing_count: 3 - motionObjectiveDoneCount,
      source_card_id: motionObjectiveSourceCardId,
      sends_motion_when_clicked: false,
    },
    {
      id: "wysiwyg",
      title: "画面/地图/雷达点",
      state: wysiwygObjectiveCompleted ? "已完成" : "待处理",
      summary_plain: `画面：${cameraCurrentVisible ? "已显示" : "未显示"}；地图：${mapCurrentVisible ? "已显示" : "未显示"}；雷达点：${radarMapPointsVisible ? "已贴图" : "未贴图"}。`,
      next_action_plain: liveWysiwygPrimaryRefreshLabel === "当前所见已满足"
        ? "当前画面、地图和雷达点已按同轮读数显示。"
        : `下一步：${liveWysiwygPrimaryRefreshLabel}。`,
      item_ids: ["camera_wysiwyg", "map_wysiwyg", "radar_map_points_wysiwyg"],
      completed: wysiwygObjectiveCompleted,
      actionable: !wysiwygObjectiveCompleted,
      missing_count: 3 - wysiwygObjectiveDoneCount,
      source_card_id: liveWysiwygPrimarySurfaceId === "camera"
        ? "camera_preview"
        : liveWysiwygPrimarySurfaceId === "radar_map_points"
          ? "radar_map_points"
          : "map_preview",
      sends_motion_when_clicked: false,
    },
    {
      id: "precheck",
      title: "发车前确认",
      state: minimalPrecheckSafetyOnly ? "只需勾确认" : "未收敛",
      summary_plain: minimalPrecheckSafetyOnly
        ? "发车前预检已精简：执行运动只需勾现场安全确认；相机、雷达和现场报告不作为额外发车前置。"
        : "发车前预检还未收敛到最小安全确认。",
      next_action_plain: goalSummary.safety_precheck_next_action_plain || "当前没有待安全确认的入口。",
      item_ids: ["safety_confirmation"],
      completed: minimalPrecheckSafetyOnly,
      actionable: goalSummary.safety_confirm_needed_count > 0,
      missing_count: minimalPrecheckSafetyOnly ? 0 : 1,
      source_card_id: (goalSummary.safety_precheck_source_card_id || "nav2_route") as RobotControlLiveObjectiveAuditItem["source_card_id"],
      sends_motion_when_clicked: false,
    },
    {
      id: "mapping",
      title: "自由移动到建图",
      state: mappingStartReady ? "可建图" : freeMoveStartReady ? "先自由移动" : "未就绪",
      summary_plain: `自由移动：${freeMoveStartReady ? "可启动" : "未就绪"}；建图启动：${mappingStartReady ? "可启动" : `未就绪，还差 ${mappingStartMissingPlain}`}。`,
      next_action_plain: mappingStartUnblockPlain,
      item_ids: ["free_move", "mapping_start"],
      completed: mappingObjectiveCompleted,
      actionable: freeMoveStartReady || mappingStartReady,
      missing_count: mappingObjectiveMissingCount,
      source_card_id: mappingStartReady ? "mapping_start" : "free_move",
      sends_motion_when_clicked: false,
    },
  ];
  const objectiveAuditMissingIds = objectiveAuditItems.filter((item) => !item.completed).map((item) => item.id);
  const objectiveAuditDoneCount = objectiveAuditItems.length - objectiveAuditMissingIds.length;
  const objectiveAuditNextObjective = objectiveAuditItems.find((item) => !item.completed && item.actionable)
    ?? objectiveAuditItems.find((item) => !item.completed)
    ?? null;
  const objectiveAuditMissingPlain = (item: RobotControlLiveObjectiveAuditItem): string => {
    // 顶层摘要必须说当前真实缺口，避免“画面/地图/雷达点”这种大类掩盖地图和雷达已可见的事实。
    if (item.id === "motion") {
      const motionGaps = [
        ...(!nav2ObjectiveDone
          ? [`图上行程还差${[
            ...(!routeReadyOnMap ? ["路线显示"] : []),
            ...(!nav2GoalSucceeded ? ["到点成功"] : []),
            ...(!wheelLrNonzeroProven ? ["同窗口轮速 L/R 非零"] : []),
            ...(!deliveryClaimReady ? ["送达确认"] : []),
          ].join("、")}`]
          : []),
        ...(!keyboardObjectiveDone
          ? [`键盘还差${[
            ...(!keyboardMotionVerified ? ["按住读到轮速 L/R 非零"] : []),
            ...(!keyboardStopSettledAfterPulse ? ["松开后停稳"] : []),
          ].join("、")}`]
          : []),
        ...(!freeMoveObjectiveDone ? ["自由移动还差启动读回"] : []),
      ];
      return motionGaps.join("；") || item.title;
    }
    if (item.id === "wysiwyg") {
      const cameraMissingPlain = cameraHardwareActionRequired
        ? `画面未显示（${cameraHardwareActionLabel}）`
        : "画面未显示";
      const missingSurfaces = [
        ...(!cameraCurrentVisible ? [cameraMissingPlain] : []),
        ...(!mapCurrentVisible ? ["地图未显示"] : []),
        ...(!radarMapPointsVisible ? ["雷达点未贴图"] : []),
      ];
      return missingSurfaces.join("、") || item.title;
    }
    if (item.id === "mapping") {
      return mappingStartReady ? "建图待启动" : `建图启动还差${mappingStartMissingPlain}`;
    }
    return item.title;
  };
  const objectiveAuditSummaryPlain = objectiveAuditMissingIds.length === 0
    ? "四项目标均已完成；继续保持现场监看。"
    : `四项目标完成 ${objectiveAuditDoneCount}/4；下一项：${objectiveAuditNextObjective?.title ?? "继续现场监看"}；未完成：${objectiveAuditItems.filter((item) => !item.completed).map(objectiveAuditMissingPlain).join("、")}。`;
  const cameraSharedPreviewClientCount = readback.camera.shared_preview_client_count || "0";
  const cameraSharedPreviewUpstreamActive = readback.camera.shared_preview_upstream_active || "not_loaded";
  const cameraSharedPreviewExclusiveClaim = readback.camera.shared_preview_exclusive_camera_claim || "not_loaded";
  const cameraSharedPreviewGapPlain = cameraCurrentVisible
    ? `共享画面已显示；当前 ${cameraSharedPreviewClientCount} 个页面共用同一条上游流，后进页面不会独占摄像头。`
    : cameraHardwareActionRequired
      ? `共享入口可加入且不独占摄像头；当前相机源未出首帧，请${cameraHardwareActionLabel}，再按只读链路复测。`
      : `共享入口可加入且不独占摄像头；当前还没有可显示画面帧，先按只读链路复测相机首帧和共享预览状态。`;
  return {
    status,
    status_label: labels[status],
    summary_plain: summaryPlain,
    next_action_plain: nextActionPlain,
    robot_api_connection_status: robotApiConnection.status,
    robot_api_connection_plain: robotApiConnectionPlain(robotApiConnection),
    robot_api_connection_next_action_plain: robotApiConnectionNextAction,
    robot_api_connection_loaded_count: robotApiConnection.loaded_count,
    robot_api_connection_failed_count: robotApiConnection.failed_count,
    robot_api_connection_blocked_count: robotApiConnection.blocked_count,
    robot_api_connection_failed_endpoint_ids: robotApiConnection.failed_endpoint_ids,
    robot_api_connection_blocked_reasons: robotApiConnection.blocked_reasons,
    robot_api_connection_recovery_endpoints: robotApiConnection.recovery_endpoints,
    robot_api_connection_sends_motion_when_clicked: false,
    route_ready_on_map: routeReadyOnMap,
    nav2_route_ready: routeReadyOnMap,
    nav2_goal_succeeded: nav2GoalSucceeded,
    nav2_goal_execution_proven: nav2GoalExecutionProven,
    wheel_lr_nonzero_proven: wheelLrNonzeroProven,
    needs_same_window_wheel_rerun: needsSameWindowWheelRerun,
    delivery_success: deliveryClaimReady,
    delivery_claim_ready: deliveryClaimReady,
    delivery_success_required: !deliveryClaimReady,
    delivery_next_action_plain: wheelRerunDeliveryNextActionPlain,
    fixed_delivery_latest_endpoint: "/api/robot-control/delivery/latest",
    fixed_delivery_complete_endpoint: "/api/robot-control/delivery/complete",
    delivery_latest_readback_only: true,
    delivery_complete_sends_motion: false,
    camera_current_visible: cameraCurrentVisible,
    live_wysiwyg_camera_visible: cameraCurrentVisible,
    map_current_visible: mapCurrentVisible,
    path_current_visible: pathCurrentVisible,
    live_wysiwyg_map_visible: mapCurrentVisible,
    radar_map_points_visible: radarMapPointsVisible,
    primary_action_id: liveMotionRunbookPrimaryActionId,
    keyboard_continuous_ready: keyboardContinuousControlReady,
    keyboard_continuous_motion_verified: keyboardMotionVerified,
    keyboard_continuous_forwarded_pulses: keyboardBestContinuousPulseCount,
    keyboard_ready: keyboardContinuousControlReady,
    keyboard_safety_confirm_required: keyboardContinuousControlReady,
    keyboard_enable_sends_motion: false,
    keyboard_pulse_interval_ms: ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS,
    keyboard_pulse_duration_ms: ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS,
    keyboard_stop_triggers: ["key_release", "window_blur", "page_hidden", "direction_change", "stop_button"],
    keyboard_acceptance_plain: keyboardAcceptancePlain,
    keyboard_manual_endpoint: "/api/robot-control/base/manual",
    keyboard_stop_endpoint: "/api/robot-control/base/stop",
    keyboard_feedback_readback_endpoint: "/api/robot-control/base/feedback-samples",
    keyboard_summary_endpoint: "/api/robot-control/summary",
    objective_audit_status: objectiveAuditMissingIds.length === 0 ? "complete" : "in_progress",
    objective_audit_total_count: 4,
    objective_audit_done_count: objectiveAuditDoneCount,
    objective_audit_remaining_count: objectiveAuditMissingIds.length,
    objective_audit_next_objective_id: objectiveAuditNextObjective?.id ?? "none",
    objective_audit_missing_objective_ids: objectiveAuditMissingIds,
    objective_audit_summary_plain: objectiveAuditSummaryPlain,
    objective_audit_items: objectiveAuditItems,
    fixed_objective_audit_summary_endpoint: "/api/robot-control/summary",
    objective_audit_sends_motion_when_clicked: false,
    map_display_primary_tool: "pc_big_map",
    map_display_primary_url: "/map",
    map_display_legacy_url: "?view=map",
    map_display_primary_action_label: "进入地图大屏",
    map_display_primary_action_opens_new_window: false,
    map_display_primary_action_opens_current_page: true,
    map_display_direct_map_default_observer: true,
    map_display_direct_map_only: true,
    map_display_direct_map_viewport_priority: "fullscreen_map_canvas",
    map_display_direct_map_canvas_height_mode: "viewport_dominant_full_height",
    map_display_direct_map_keeps_page_fullscreen_without_browser_api: true,
    map_display_direct_map_browser_fullscreen_required: false,
    map_display_direct_map_refreshes_radar_scan_proof_on_enter: true,
    map_display_direct_map_refreshes_map_preview_on_enter: true,
    map_display_direct_map_refreshes_radar_status_on_enter: true,
    map_display_direct_map_starts_radar_lifecycle_on_enter: false,
    map_display_default_zoom_percent: "3200%",
    map_display_max_zoom_percent: "6400%",
    map_display_too_small_next_action_plain: mapDisplayTooSmallNextActionPlain,
    map_display_ros2_companion_answer_plain: mapDisplayRos2CompanionAnswerPlain,
    map_display_ros2_companion_plain: mapDisplayRos2CompanionAnswerPlain,
    map_display_operator_default_surface: "pc_big_map_direct_view",
    map_display_companion_replaces_pc_ui: false,
    map_display_wysiwyg_overlays: ["image", "route", "robot", "radar"],
    map_display_ros2_companion_required: false,
    map_display_ros2_companion_tools: ["rviz2", "foxglove"],
    map_display_engineering_tools_visible_by_default: false,
    map_display_engineering_tools_action_label: mapDisplayEngineeringToolsActionLabel,
    map_display_ordinary_user_tool: "pc_big_map",
    map_display_rviz_role_plain: mapDisplayRvizRolePlain,
    map_display_rviz_launch_command: "ros2 launch ros2_trashbot_bringup rviz.launch.py",
    map_display_foxglove_role_plain: mapDisplayFoxgloveRolePlain,
    map_display_foxglove_bridge_package: "foxglove_bridge",
    map_display_foxglove_bridge_install_command: "sudo apt install ros-humble-foxglove-bridge",
    map_display_foxglove_bridge_launch_command: "ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py",
    map_display_foxglove_websocket_url: "ws://192.168.1.11:8765",
    map_display_foxglove_web_app_url: mapDisplayFoxgloveWebAppUrl,
    map_display_ros2_observe_topics: mapDisplayRos2ObserveTopics,
    map_display_ros2_observe_motion_topics: false,
    map_display_ros2_observe_control_tools: false,
    map_display_engineering_tools_sends_motion: false,
    map_display_companion_plain: mapDisplayCompanionPlain,
    map_display_sends_motion_when_clicked: false,
    map_display_starts_ros2: false,
    map_display_starts_rviz2: false,
    map_display_starts_foxglove: false,
    map_display_starts_nav2: false,
    map_display_starts_map_runtime: false,
    live_wysiwyg_ready: liveWysiwygMissingSurfaceIds.length === 0,
    live_wysiwyg_missing_surface_ids: liveWysiwygMissingSurfaceIds,
    live_wysiwyg_needs_refresh: liveWysiwygMissingSurfaceIds.length > 0,
    live_wysiwyg_readback_gap_surface_ids: liveWysiwygReadbackGapSurfaceIds,
    live_wysiwyg_primary_readback_gap_surface_id: liveWysiwygReadbackGapSurfaceIds[0] ?? "none",
    live_wysiwyg_missing_surface_refresh_endpoints: liveWysiwygMissingSurfaceRefreshEndpoints,
    live_wysiwyg_missing_surface_refresh_labels: liveWysiwygMissingSurfaceRefreshLabels,
    live_wysiwyg_primary_refresh_endpoint: liveWysiwygPrimaryRefreshEndpoint,
    live_wysiwyg_primary_refresh_label: liveWysiwygPrimaryRefreshLabel,
    live_wysiwyg_diagnostic_plain: liveWysiwygDiagnosticPlain,
    live_wysiwyg_camera_diagnostic_plain: cameraDiagnosticPlain,
    live_wysiwyg_radar_diagnostic_plain: radarDiagnosticPlain,
    live_wysiwyg_map_radar_diagnostic_plain: mapRadarDiagnosticPlain,
    live_wysiwyg_camera_probe_failure_reason: cameraProbeFailureReason,
    live_wysiwyg_camera_source_diagnosis_status: readback.camera.source_diagnosis_status || "not_loaded",
    live_wysiwyg_camera_source_diagnosis_plain_hint: readback.camera.source_diagnosis_plain_hint || "not_loaded",
    live_wysiwyg_camera_source_diagnosis_next_action_plain: readback.camera.source_diagnosis_next_action_plain || "not_loaded",
    live_wysiwyg_camera_source_diagnosis_not_exclusive: readback.camera.source_diagnosis_not_exclusive || "not_loaded",
    live_wysiwyg_camera_shared_preview_client_count: cameraSharedPreviewClientCount,
    live_wysiwyg_camera_shared_preview_upstream_active: cameraSharedPreviewUpstreamActive,
    live_wysiwyg_camera_shared_preview_exclusive_camera_claim: cameraSharedPreviewExclusiveClaim,
    live_wysiwyg_camera_shared_preview_everyone_can_join: true,
    live_wysiwyg_camera_shared_preview_current_frame_visible: cameraCurrentVisible,
    live_wysiwyg_camera_shared_preview_gap_plain: cameraSharedPreviewGapPlain,
    live_wysiwyg_camera_recovery_status: cameraRecoveryStatus,
    live_wysiwyg_camera_recovery_next_action_plain: cameraRecoveryNextActionPlain,
    live_wysiwyg_camera_recovery_sequence: cameraRecoverySequence,
    live_wysiwyg_camera_recovery_sequence_labels: cameraRecoverySequenceLabels,
    live_wysiwyg_camera_recovery_sends_motion: false,
    camera_first_frame_probe_status: readback.camera.first_frame_probe_status || "not_loaded",
    camera_first_frame_failure_reason: readback.camera.first_frame_probe_failure_reason || cameraProbeFailureReason,
    camera_source_diagnosis_status: readback.camera.source_diagnosis_status || "not_loaded",
    camera_source_diagnosis_not_exclusive: readback.camera.source_diagnosis_not_exclusive || "not_loaded",
    camera_shared_preview_exclusive_camera_claim: cameraSharedPreviewExclusiveClaim,
    camera_shared_preview_everyone_can_join: true,
    camera_shared_preview_current_frame_visible: cameraCurrentVisible,
    camera_shared_preview_gap_plain: cameraSharedPreviewGapPlain,
    camera_usb_speed: cameraUsbSpeed,
    camera_recovery_next_action_plain: cameraRecoveryNextActionPlain,
    camera_hardware_action_required: cameraHardwareActionRequired,
    camera_hardware_action_label: cameraHardwareActionLabel,
    camera_usb_full_speed_detected: cameraUsbFullSpeedDetected,
    camera_blocks_mapping_start: mappingCameraBlocksStart,
    camera_blocks_free_move: false,
    camera_reprobe_after_hardware_action_required: cameraHardwareActionRequired,
    camera_reprobe_sequence: cameraReprobeSequence,
    fixed_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe",
    fixed_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status",
    camera_recovery_sends_motion: false,
    camera_recovery_starts_map_runtime: false,
    live_wysiwyg_radar_scan_missing_observations: radarScanMissingObservations,
    live_wysiwyg_map_radar_blocked_reasons: mapRadarBlockedReasons,
    live_wysiwyg_radar_map_overlay_status: radarMapOverlayStatus,
    live_wysiwyg_radar_map_current_point_count: radarMapCurrentPointCount,
    live_wysiwyg_radar_map_source_point_count: radarMapSourcePointCount,
    live_wysiwyg_radar_map_stale_source_points_suppressed: radarMapStaleSourcePointsSuppressed,
    live_wysiwyg_radar_map_primary_blocked_reason: mapRadarBlockedReasons[0] ?? "none",
    live_wysiwyg_radar_map_current_vs_source_plain: radarMapCurrentVsSourcePlain,
    live_wysiwyg_radar_map_refresh_next_action_plain: radarMapRefreshNextActionPlain,
    live_wysiwyg_radar_map_refresh_sequence: radarOverlayRecoverySequence,
    live_wysiwyg_radar_map_refresh_sequence_labels: radarOverlayRecoverySequenceLabels,
    radar_overlay_status: radarMapOverlayStatus,
    radar_overlay_current_point_count: radarMapCurrentPointCount,
    radar_overlay_source_point_count: radarMapSourcePointCount,
    radar_overlay_primary_blocked_reason: mapRadarBlockedReasons[0] ?? "none",
    radar_overlay_current_vs_source_plain: radarMapCurrentVsSourcePlain,
    radar_overlay_refresh_next_action_plain: radarMapRefreshNextActionPlain,
    radar_overlay_needs_refresh: radarOverlayNeedsRefresh,
    radar_overlay_blocks_wysiwyg: radarOverlayBlocksWysiwyg,
    radar_overlay_blocks_free_move: false,
    radar_overlay_recovery_sequence: radarOverlayRecoverySequence,
    fixed_radar_overlay_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh",
    fixed_radar_overlay_map_preview_endpoint: "/api/robot-control/map/preview",
    radar_overlay_refresh_sends_motion: false,
    radar_overlay_refresh_starts_radar_lifecycle: false,
    fixed_radar_start_endpoint: "/api/robot-control/radar/start",
    fixed_radar_stop_endpoint: "/api/robot-control/radar/stop",
    radar_start_map_wysiwyg_required: true,
    radar_start_map_wysiwyg_sequence: radarStartMapWysiwygSequence,
    radar_start_map_wysiwyg_sequence_labels: radarStartMapWysiwygSequenceLabels,
    radar_start_refreshes_scan_proof: true,
    radar_start_refreshes_radar_status: true,
    radar_start_refreshes_map_preview: true,
    radar_start_refreshes_summary: true,
    radar_start_sends_motion: false,
    radar_start_starts_nav2: false,
    radar_start_starts_manual: false,
    radar_start_starts_keyboard: false,
    radar_start_starts_free_roam: false,
    radar_start_starts_map_runtime: false,
    radar_start_submits_delivery: false,
    radar_start_stops_motion: false,
    fixed_live_wysiwyg_radar_refresh_endpoint: "/api/robot-control/radar/scan-proof/refresh",
    fixed_live_wysiwyg_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe",
    fixed_live_wysiwyg_map_preview_endpoint: "/api/robot-control/map/preview",
    fixed_live_wysiwyg_radar_status_endpoint: "/api/robot-control/radar/status",
    fixed_live_wysiwyg_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status",
    live_wysiwyg_refresh_plan_available: true,
    live_wysiwyg_refresh_sequence: liveWysiwygRefreshSequence,
    live_wysiwyg_refresh_sequence_labels: liveWysiwygRefreshSequenceLabels,
    live_wysiwyg_refreshes_radar_scan_proof: true,
    live_wysiwyg_refreshes_camera_first_frame_probe: true,
    live_wysiwyg_refreshes_map_preview: true,
    live_wysiwyg_refreshes_radar_status: true,
    live_wysiwyg_refreshes_camera_mjpeg_status: true,
    live_wysiwyg_refresh_sends_motion: false,
    live_wysiwyg_refresh_starts_nav2: false,
    live_wysiwyg_refresh_starts_manual: false,
    live_wysiwyg_refresh_starts_keyboard: false,
    live_wysiwyg_refresh_starts_free_roam: false,
    live_wysiwyg_refresh_starts_radar_lifecycle: false,
    live_wysiwyg_refresh_starts_map_runtime: false,
    live_wysiwyg_surface_summaries: liveWysiwygSurfaceSummaries,
    free_move_start_ready: freeMoveStartReady,
    free_roam_ready: freeMoveStartReady,
    free_roam_start_ready: freeMoveStartReady,
    free_roam_motion_start_ready: freeMoveStartReady,
    free_roam_motion_ready: freeRoamMotionReady,
    free_move_minimal_precheck_safety_only: true,
    free_move_safety_confirm_required: freeMoveStartReady,
    free_move_camera_preflight_required: false,
    free_move_radar_preflight_required: false,
    free_move_without_camera_allowed: true,
    free_roam_motion_without_radar_allowed: true,
    free_move_blocked_by_camera_wysiwyg: false,
    free_move_blocked_by_radar_wysiwyg: false,
    fixed_free_roam_start_endpoint: "/api/robot-control/free-roam/autonomy/start",
    fixed_free_roam_stop_endpoint: "/api/robot-control/free-roam/autonomy/stop",
    fixed_free_roam_latest_endpoint: "/api/robot-control/free-roam/autonomy/latest",
    mapping_start_ready: mappingStartReady,
    free_roam_mapping_start_ready: mappingStartReady,
    free_roam_mapping_ready: boundary.free_roam_mapping_ready,
    free_roam_mapping_start_missing_reasons: mappingStartMissingReasons,
    free_roam_mapping_missing_reasons: mappingAcceptanceMissingReasons,
    mapping_start_requires_camera_first_frame: true,
    mapping_start_requires_lidar_fresh: true,
    mapping_start_missing_reasons: mappingStartMissingReasons,
    mapping_acceptance_missing_reasons: mappingAcceptanceMissingReasons,
    mapping_start_unblock_plain: mappingStartUnblockPlain,
    mapping_camera_blocks_start: mappingCameraBlocksStart,
    mapping_lidar_blocks_start: mappingLidarBlocksStart,
    mapping_lidar_fresh_readback_ready: mappingLidarFreshReadbackReady,
    mapping_lidar_fresh_gate_conflict: mappingLidarFreshGateConflict,
    mapping_lidar_fresh_gate_status: mappingLidarFreshGateStatus,
    mapping_lidar_fresh_next_action_plain: mappingLidarFreshNextActionPlain,
    mapping_lidar_fresh_refresh_sequence: mappingLidarFreshRefreshSequence,
    mapping_lidar_fresh_refresh_sequence_labels: mappingLidarFreshRefreshSequenceLabels,
    mapping_lidar_fresh_refresh_sends_motion: false,
    mapping_lidar_fresh_refresh_starts_radar_lifecycle: false,
    mapping_lidar_fresh_blocks_free_move: false,
    mapping_unblock_allows_free_move: true,
    mapping_unblock_camera_diagnosis_status: readback.camera.source_diagnosis_status || "not_loaded",
    mapping_unblock_camera_not_exclusive: readback.camera.source_diagnosis_not_exclusive || "not_loaded",
    mapping_unblock_camera_next_action_plain: readback.camera.source_diagnosis_next_action_plain || readback.camera.camera_wysiwyg_next_action_plain || camera.next_action_plain,
    mapping_unblock_camera_recovery_next_action_plain: cameraRecoveryNextActionPlain,
    mapping_unblock_camera_recovery_sequence: cameraRecoverySequence,
    mapping_unblock_camera_recovery_sequence_labels: cameraRecoverySequenceLabels,
    fixed_mapping_start_endpoint: "/api/robot-control/map/start",
    fixed_mapping_preview_endpoint: "/api/robot-control/map/preview",
    fixed_mapping_unblock_camera_probe_endpoint: "/api/robot-control/camera/first-frame/probe",
    fixed_mapping_unblock_camera_mjpeg_status_endpoint: "/api/robot-control/camera/mjpeg/status",
    fixed_mapping_unblock_summary_endpoint: "/api/robot-control/summary",
    mapping_unblock_camera_recovery_sends_motion: false,
    mapping_unblock_sends_motion_when_clicked: false,
    keyboard_control_start_ready: keyboardControlStartReady,
    keyboard_continuous_control_ready: keyboardContinuousControlReady,
    keyboard_hold_to_move_required: keyboardHoldToMoveRequired,
    keyboard_enabled: keyboardEnabled,
    keyboard_motion_verified: keyboardMotionVerified,
    keyboard_stop_settled_after_pulse: keyboardStopSettledAfterPulse,
    keyboard_best_continuous_pulse_count: keyboardBestContinuousPulseCount,
    keyboard_verified_min_forwarded_pulses: keyboardVerifiedMinForwardedPulses,
    keyboard_manual_command_mode: readback.keyboard.manual_command_mode || "not_loaded",
    keyboard_continuous_minimal_precheck_safety_only: true,
    keyboard_continuous_safety_confirm_required: keyboardContinuousControlReady,
    keyboard_continuous_enable_sends_motion: false,
    keyboard_continuous_hold_to_move_required: true,
    keyboard_continuous_pulse_interval_ms: ROBOT_CONTROL_KEYBOARD_JOG_INTERVAL_MS,
    keyboard_continuous_pulse_duration_ms: ROBOT_CONTROL_KEYBOARD_JOG_DURATION_MS,
    keyboard_continuous_stop_triggers: ["key_release", "window_blur", "page_hidden", "direction_change", "stop_button"],
    keyboard_continuous_wheel_feedback_acceptance: "same_hold_window_wheel_lr_nonzero",
    fixed_keyboard_manual_endpoint: "/api/robot-control/base/manual",
    fixed_keyboard_stop_endpoint: "/api/robot-control/base/stop",
    fixed_keyboard_feedback_readback_endpoint: "/api/robot-control/base/feedback-samples",
    fixed_keyboard_summary_endpoint: "/api/robot-control/summary",
    keyboard_continuous_post_hold_feedback_readback_required: true,
    keyboard_continuous_post_hold_summary_refresh_required: true,
    live_motion_runbook_items: liveMotionRunbookItems,
    live_motion_runbook_action_ids: liveMotionRunbookItems.map((item) => item.id),
    live_motion_runbook_ready_action_ids: liveMotionRunbookReadyItems.map((item) => item.id),
    live_motion_runbook_blocked_action_ids: liveMotionRunbookBlockedItems.map((item) => item.id),
    live_motion_runbook_primary_action_id: liveMotionRunbookPrimaryActionId,
    live_motion_runbook_start_endpoints: liveMotionRunbookStartEndpoints,
    live_motion_runbook_acceptance_endpoints: liveMotionRunbookAcceptanceEndpoints,
    live_motion_runbook_minimal_precheck_safety_only: liveMotionRunbookItems.every((item) => item.minimal_precheck_safety_only),
    live_motion_runbook_safety_confirm_required: liveMotionRunbookReadyItems.some((item) => item.safety_confirm_required),
    live_motion_runbook_summary_plain: liveMotionRunbookSummaryPlain,
    live_motion_runbook_ready_plain: liveMotionRunbookReadyPlain,
    live_motion_runbook_blocked_plain: liveMotionRunbookBlockedPlain,
    live_motion_runbook_primary_action_plain: liveMotionRunbookPrimaryActionLabel,
    live_motion_runbook_minimal_precheck_plain: liveMotionRunbookMinimalPrecheckPlain,
    minimal_precheck_safety_only: minimalPrecheckSafetyOnly,
    safety_confirm_required_for_motion: goalSummary.safety_confirm_needed_count > 0,
    wheel_rerun_minimal_precheck_safety_only: needsSameWindowWheelRerun && minimalPrecheckSafetyOnly,
    wheel_rerun_safety_confirm_required: needsSameWindowWheelRerun && goalSummary.safety_confirm_needed_count > 0,
    wheel_rerun_camera_preflight_required: false,
    wheel_rerun_radar_preflight_required: false,
    wheel_rerun_route_wysiwyg_preflight_required: false,
    wheel_rerun_blocked_by_camera_wysiwyg: false,
    wheel_rerun_blocked_by_radar_wysiwyg: false,
    wheel_rerun_command_mode: wheelRerunCommandMode,
    wheel_rerun_last_base_command_mode: wheelRerunLastBaseCommandMode,
    wheel_rerun_next_base_command_mode: wheelRerunNextBaseCommandMode,
    wheel_rerun_feedback_sample_count: wheelRerunFeedbackSampleCount,
    wheel_rerun_feedback_nonzero_sample_count: wheelRerunFeedbackNonzeroSampleCount,
    wheel_rerun_latest_raw_left: wheelRerunLatestRawLeft,
    wheel_rerun_latest_raw_right: wheelRerunLatestRawRight,
    wheel_rerun_imu_attitude_delta_observed: wheelRerunImuDeltaObserved,
    wheel_rerun_imu_roll_delta: wheelRerunImuRollDelta,
    wheel_rerun_imu_pitch_delta: wheelRerunImuPitchDelta,
    wheel_rerun_mode_rerun_status: wheelRerunModeRerunStatus,
    wheel_rerun_mode_rerun_plain: wheelRerunModeRerunPlain,
    wheel_rerun_next_mode_plain: wheelRerunNextModePlain,
    wheel_rerun_base_command_nonzero_observed: wheelRerunBaseCommandNonzeroObserved,
    wheel_rerun_base_command_nonzero_count: wheelRerunBaseCommandNonzeroCount,
    wheel_rerun_base_command_latest_nonzero_mode: wheelRerunBaseCommandLatestNonzeroMode,
    wheel_rerun_base_command_mode_counts: wheelRerunBaseCommandModeCounts,
    wheel_rerun_control_diagnosis_plain: wheelRerunControlDiagnosisPlain,
    wheel_rerun_readback_plain: wheelRerunReadbackPlain,
    wheel_rerun_checklist_plain: wheelRerunChecklistPlain,
    wheel_rerun_acceptance_plain: wheelRerunAcceptancePlain,
    wheel_rerun_acceptance_endpoints: wheelRerunAcceptanceEndpoints,
    wheel_rerun_ready_for_safety_confirm: wheelRerunReadyForSafetyConfirm,
    wheel_rerun_start_endpoint: "/api/robot-control/nav2/goal/execute",
    wheel_rerun_start_sends_motion: true,
    wheel_rerun_requires_safety_confirm: needsSameWindowWheelRerun && goalSummary.safety_confirm_needed_count > 0,
    wheel_rerun_readback_endpoints: wheelRerunAcceptanceEndpoints,
    wheel_rerun_required_success_markers: wheelRerunRequiredSuccessMarkers,
    wheel_rerun_current_gap_plain: wheelRerunCurrentGapPlain,
    wheel_rerun_no_extra_precheck_plain: wheelRerunNoExtraPrecheckPlain,
    wheel_rerun_delivery_success_required: !deliveryClaimReady,
    wheel_rerun_delivery_next_action_plain: wheelRerunDeliveryNextActionPlain,
    fixed_wheel_rerun_endpoint: "/api/robot-control/nav2/goal/execute",
    fixed_wheel_rerun_latest_endpoint: "/api/robot-control/nav2/goal/execution/latest",
    fixed_wheel_rerun_delivery_latest_endpoint: "/api/robot-control/delivery/latest",
    fixed_wheel_rerun_delivery_complete_endpoint: "/api/robot-control/delivery/complete",
    wheel_rerun_delivery_complete_sends_motion: false,
    fixed_wheel_readback_endpoint: "/api/robot-control/base/feedback-samples",
    sends_motion_when_clicked: false,
    blocker_ids: goalSummary.blocked_action_ids,
    ready_action_ids: goalSummary.ready_action_ids,
    side_blocker_ids: sideBlockerItems.map((item) => item.id),
    side_blocker_count: sideBlockerItems.length,
    ready_action_count: readyActionItems.length,
    side_gap_summary_plain: sideGapSummaryPlain,
    primary_status_item_id: primaryStatusTarget.itemId,
    primary_status_source_card_id: primaryStatusTarget.sourceCardId,
    next_action_item_id: primaryStatusTarget.itemId,
    next_action_source_card_id: primaryStatusTarget.sourceCardId,
  };
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
  const readbacks = await readSummaryEndpoints(normalized.normalized, options);
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
  const connectionStatus: RobotControlSummaryResponse["robot_api_connection"]["status"] = dangerous.length || blockedCount > 0
    ? "blocked"
    : failedCount > 0 ? "degraded" : "readable";
  const failedEndpointIds = readbacks
    .filter((item) => item.request_status === "fetch_failed" || item.request_status === "bad_json" || item.request_status === "not_object")
    .map((item) => item.id);
  const blockedReasons = [
    ...readbacks.flatMap((item) => item.blocked_reasons.map((reason) => `${item.id}:${reason}`)),
    ...dangerous.map((field) => `dangerous_true_field:${field}`),
  ];
  const portDriftReason = failedCount > 0 && loadedCount === 0 ? robotApiPortDriftReason(normalized.normalized) : "";
  const portDriftPlain = robotApiPortDriftPlain(portDriftReason);
  const connectionBlockedReasons = [
    ...(portDriftReason ? [portDriftReason] : []),
    ...blockedReasons,
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
  const mapSummary = mapSummaryFromReadbacks(readbacks, proofSummary, lidarSummary);
  const keyboardReadback = keyboardSummaryReadback();
  const readbackSummary: RobotControlSummaryResponse["readback_summary"] = {
    camera: cameraSummaryFromReadbacks(readbacks, firstFrameProbeOverlay, mjpegRelayOverlay),
    lidar: lidarSummary,
    radar: radarSummaryFromReadbacks(lidarSummary, mapSummary),
    base: baseSummaryFromReadbacks(readbacks),
    map: mapSummary,
    localization: localizationSummaryFromReadbacks(readbacks, proofSummary),
    nav2: nav2Summary,
    keyboard: keyboardReadback,
    keyboard_control: keyboardReadback,
    keyboard_teleop: keyboardReadback,
    free_roam: freeRoamSummaryFromReadbacks(readbacks, freeRoamRuntimeGates, freeRoamRuntime, true),
  };
  const safeCommandBoundary = lockedBoundary(freeRoamRuntimeGates, freeRoamRuntime, proofSummary, nav2Summary, true);
  const actionStatusCards = buildActionStatusCards(readbackSummary, safeCommandBoundary);
  const goalChecklist = buildGoalChecklist(actionStatusCards ?? [], readbackSummary, safeCommandBoundary);
  const goalSummary = buildGoalChecklistSummary(goalChecklist ?? []) as NonNullable<RobotControlSummaryResponse["goal_checklist_summary"]>;
  const liveClosureSummary = buildLiveClosureSummary(
    actionStatusCards ?? [],
    goalSummary,
    readbackSummary,
    safeCommandBoundary,
    operatorHilMaterialSummary,
    {
      status: connectionStatus,
      loaded_count: loadedCount,
      blocked_count: blockedCount,
      failed_count: failedCount,
      blocked_reasons: connectionBlockedReasons,
      failed_endpoint_ids: failedEndpointIds,
      recovery_endpoints: [
        "/api/robot-control/summary",
        "/api/robot-control/map/preview",
        "/api/robot-control/radar/status",
        "/api/robot-control/camera/mjpeg/status",
      ],
    },
  ) as NonNullable<RobotControlSummaryResponse["live_closure_summary"]>;

  const objectiveAuditItem = (id: RobotControlLiveObjectiveAuditItem["id"]) =>
    liveClosureSummary.objective_audit_items.find((item) => item.id === id);
  const motionObjectiveAlias = objectiveAuditItem("motion");
  const precheckObjectiveAlias = objectiveAuditItem("precheck");
  const mappingObjectiveAlias = objectiveAuditItem("mapping");
  const runNav2RouteRunbookItem = liveClosureSummary.live_motion_runbook_items.find((item) => item.id === "run_nav2_route");
  const keyboardRunbookItem = liveClosureSummary.live_motion_runbook_items.find((item) => item.id === "hold_keyboard");
  const freeMoveRunbookItem = liveClosureSummary.live_motion_runbook_items.find((item) => item.id === "start_free_move");
  const mappingRunbookItem = liveClosureSummary.live_motion_runbook_items.find((item) => item.id === "start_mapping_when_sensors_ready");
  const primaryRunbookItem = liveClosureSummary.live_motion_runbook_items.find((item) => item.id === liveClosureSummary.live_motion_runbook_primary_action_id);
  const keyboardStopAfterRelease = keyboardRunbookItem ? !keyboardRunbookItem.missing_evidence.includes("stop_after_release") : false;
  const keyboardActionAcceptanceEndpoints = keyboardRunbookItem?.acceptance_endpoints ?? [
    liveClosureSummary.keyboard_feedback_readback_endpoint,
    liveClosureSummary.keyboard_summary_endpoint,
  ];
  const keyboardActionMissingEvidence = keyboardRunbookItem?.missing_evidence ?? [];
  const keyboardActionStartEndpoint = keyboardRunbookItem?.start_endpoint ?? liveClosureSummary.keyboard_manual_endpoint;
  const keyboardActionStopEndpoint = keyboardRunbookItem?.stop_endpoint ?? liveClosureSummary.keyboard_stop_endpoint;
  const keyboardPostHoldReadbackEndpoints = [
    liveClosureSummary.fixed_keyboard_feedback_readback_endpoint,
    liveClosureSummary.fixed_keyboard_summary_endpoint,
  ];
  const keyboardActionRequiredSuccessMarkers = ["same_hold_window_wheel_lr_nonzero", "stop_after_release"];
  const routeComplete = runNav2RouteRunbookItem?.completed === true;
  const freeMoveComplete = freeMoveRunbookItem?.completed === true;
  const freeMoveActionAcceptanceEndpoints = freeMoveRunbookItem?.acceptance_endpoints ?? [
    liveClosureSummary.fixed_free_roam_latest_endpoint,
    liveClosureSummary.fixed_mapping_preview_endpoint,
    "/api/robot-control/summary",
  ];
  const freeMoveActionRequiredSuccessMarkers = ["free_roam_latest_motion_ready"];
  const freeMoveActionMissingEvidence = freeMoveRunbookItem?.missing_evidence ?? [];
  const freeMoveActionStartEndpoint = freeMoveRunbookItem?.start_endpoint ?? liveClosureSummary.fixed_free_roam_start_endpoint;
  const freeMoveActionStopEndpoint = freeMoveRunbookItem?.stop_endpoint ?? liveClosureSummary.fixed_free_roam_stop_endpoint;
  const mappingActionAcceptanceEndpoints = mappingRunbookItem?.acceptance_endpoints ?? [
    liveClosureSummary.fixed_free_roam_latest_endpoint,
    liveClosureSummary.fixed_mapping_preview_endpoint,
    "/api/robot-control/summary",
  ];
  const mappingActionRequiredSuccessMarkers = ["camera_first_frame", "lidar_fresh"];
  const mappingActionMissingEvidence = mappingRunbookItem?.missing_evidence ?? liveClosureSummary.mapping_start_missing_reasons;
  const mappingActionStartEndpoint = mappingRunbookItem?.start_endpoint ?? liveClosureSummary.fixed_mapping_start_endpoint;
  const mappingActionStopEndpoint = mappingRunbookItem?.stop_endpoint ?? liveClosureSummary.fixed_free_roam_stop_endpoint;
  const cameraUsbSpeed = String(liveClosureSummary.camera_usb_speed ?? "").trim().toLowerCase();
  const cameraUsbHighSpeed = !liveClosureSummary.camera_usb_full_speed_detected
    && cameraUsbSpeed !== ""
    && !["not_loaded", "unknown", "12m", "12mbps", "full-speed"].includes(cameraUsbSpeed);
  const liveWysiwygOnlyCameraMissing = liveClosureSummary.live_wysiwyg_missing_surface_ids.length === 1
    && liveClosureSummary.live_wysiwyg_missing_surface_ids[0] === "camera";
  const mappingStartOnlyCameraMissing = liveClosureSummary.mapping_start_missing_reasons.length === 1
    && liveClosureSummary.mapping_start_missing_reasons[0] === "camera_first_frame";
  const radarOverlayWysiwygComplete = liveClosureSummary.radar_overlay_status === "loaded"
    && liveClosureSummary.radar_map_points_visible
    && !liveClosureSummary.radar_overlay_blocks_wysiwyg;
  const fieldAcceptanceSteps = liveClosureSummary.live_motion_runbook_items.map((item) => ({
    id: item.id,
    label: item.label,
    display_label: item.display_label ?? item.label,
    ready: item.ready,
    completed: item.completed,
    proof_status: item.proof_status,
    sends_motion_when_executed: item.sends_motion_when_executed,
    safety_confirm_required: item.safety_confirm_required,
    start_endpoint: item.start_endpoint,
    stop_endpoint: item.stop_endpoint,
    acceptance_endpoints: item.acceptance_endpoints,
    missing_evidence: item.missing_evidence,
    proof_plain: item.proof_plain,
    blocked_reasons: item.blocked_reasons,
  }));
  const fieldAcceptanceNextStep = fieldAcceptanceSteps.find((item) => item.id === liveClosureSummary.live_motion_runbook_primary_action_id)
    ?? fieldAcceptanceSteps.find((item) => item.ready && !item.completed)
    ?? fieldAcceptanceSteps.find((item) => !item.completed)
    ?? null;
  const fieldAcceptanceMotionStepIds = fieldAcceptanceSteps
    .filter((item) => item.sends_motion_when_executed)
    .map((item) => item.id);
  const fieldAcceptanceSafetyConfirmReadyStepIds = fieldAcceptanceSteps
    .filter((item) => item.ready && !item.completed && item.sends_motion_when_executed && item.safety_confirm_required)
    .map((item) => item.id);
  const fieldAcceptanceSafetyConfirmReadyDisplayLabels = fieldAcceptanceSteps
    .filter((item) => fieldAcceptanceSafetyConfirmReadyStepIds.includes(item.id))
    .map((item) => item.display_label ?? item.label);
  const fieldAcceptanceSafetyConfirmReadyActions: RobotControlFieldAcceptanceSafetyConfirmReadyAction[] = fieldAcceptanceSteps
    .filter((item) => fieldAcceptanceSafetyConfirmReadyStepIds.includes(item.id))
    .map((item) => ({
      id: item.id,
      label: item.label,
      display_label: item.display_label ?? item.label,
      start_endpoint: item.start_endpoint,
      stop_endpoint: item.stop_endpoint,
      acceptance_endpoints: item.acceptance_endpoints,
      requires_safety_confirm: true,
      minimal_precheck_safety_only: true,
      sends_motion_when_executed: true,
      camera_preflight_required: false,
      radar_preflight_required: false,
      operator_report_preflight_required: false,
      route_wysiwyg_preflight_required: false,
      starts_nav2_when_executed: item.id === "run_nav2_route",
      starts_manual_when_executed: item.id === "hold_keyboard",
      starts_keyboard_when_executed: item.id === "hold_keyboard",
      starts_free_roam_when_executed: item.id === "start_free_move",
      starts_map_runtime_when_executed: item.id === "start_mapping_when_sensors_ready",
      submits_delivery_when_executed: false,
    }));
  const fieldAcceptancePrimarySafetyConfirmReadyAction = fieldAcceptanceSafetyConfirmReadyActions
    .find((item) => item.id === fieldAcceptanceNextStep?.id)
    ?? fieldAcceptanceSafetyConfirmReadyActions[0]
    ?? null;
  const fieldAcceptanceCameraRecoveryActionPlain = liveClosureSummary.camera_recovery_next_action_plain
    .replace(/当前硬件提示/g, "当前设备提示");
  const fieldAcceptanceHardwareActionIds = [
    ...(liveClosureSummary.camera_hardware_action_required && !liveClosureSummary.camera_current_visible
      ? ["camera_usb_recovery"]
      : []),
  ];
  const fieldAcceptanceHardwareActions: RobotControlFieldAcceptanceHardwareAction[] = fieldAcceptanceHardwareActionIds.includes("camera_usb_recovery")
    ? [{
      id: "camera_usb_recovery",
      label: liveClosureSummary.camera_hardware_action_label,
      summary_plain: `需要先处理相机设备链路：${fieldAcceptanceCameraRecoveryActionPlain}处理后再只读复测相机首帧、共享预览状态和总览。`,
      blocks_camera_wysiwyg: true,
      blocks_mapping_start: true,
      blocks_free_move: false,
      after_action_readback_endpoint: liveClosureSummary.fixed_camera_probe_endpoint,
      after_action_readback_label: "复测相机首帧",
      after_action_readback_method: "POST",
      after_action_readback_sequence: liveClosureSummary.camera_reprobe_sequence,
      after_action_readback_sequence_labels: liveClosureSummary.live_wysiwyg_camera_recovery_sequence_labels,
      sends_motion_when_clicked: false,
      starts_nav2_when_clicked: false,
      starts_manual_when_clicked: false,
      starts_keyboard_when_clicked: false,
      starts_free_roam_when_clicked: false,
      starts_map_runtime_when_clicked: false,
      starts_radar_lifecycle_when_clicked: false,
      submits_delivery_when_clicked: false,
      stops_motion_when_clicked: false,
    }]
    : [];
  const fieldAcceptancePrimaryHardwareAction = fieldAcceptanceHardwareActions[0] ?? null;
  const fieldAcceptanceMissingEvidenceItems: RobotControlFieldAcceptanceMissingEvidenceItem[] = fieldAcceptanceSteps
    .filter((item) => !item.completed)
    .flatMap((step) => step.missing_evidence.map((id) => {
      const readbackEndpoint = fieldAcceptanceMissingEvidenceReadbackEndpoint(id, step.acceptance_endpoints);
      const canReadWithoutMotion = ["route_ready_on_map", "camera_first_frame", "lidar_fresh", "fresh_map_preview"].includes(id);
      return {
        id,
        label: fieldAcceptanceMissingEvidenceLabel(id),
        action_id: step.id,
        action_label: step.label,
        action_display_label: step.display_label ?? step.label,
        readback_endpoint: readbackEndpoint,
        readback_method: fieldAcceptanceNoMotionReadbackMethod(readbackEndpoint),
        requires_motion_before_readback: step.sends_motion_when_executed && !canReadWithoutMotion,
        requires_safety_confirm_before_motion: step.safety_confirm_required,
        blocks_field_acceptance: true,
      };
    }));
  const fieldAcceptancePrimaryMissingEvidence = fieldAcceptanceMissingEvidenceItems[0] ?? null;
  const fieldAcceptancePrimaryMissingEvidenceAction = fieldAcceptanceSteps
    .find((item) => item.id === fieldAcceptancePrimaryMissingEvidence?.action_id)
    ?? null;
  const fieldAcceptancePrimaryMissingEvidenceSafetyAction = fieldAcceptanceSafetyConfirmReadyActions
    .find((item) => item.id === fieldAcceptancePrimaryMissingEvidence?.action_id)
    ?? null;
  const fieldAcceptanceWysiwygRefreshModeValue = fieldAcceptanceWysiwygRefreshMode(
    liveClosureSummary.live_wysiwyg_missing_surface_ids,
  );
  const fieldAcceptanceWysiwygRefreshPlan = fieldAcceptanceFocusedWysiwygRefreshPlan(fieldAcceptanceWysiwygRefreshModeValue);
  const fieldAcceptanceCameraOnlyMissing = fieldAcceptanceWysiwygRefreshModeValue === "camera_only";
  const fieldAcceptanceNoMotionReadbackActionIds: RobotControlFieldAcceptanceNoMotionReadbackActionId[] = [
    "readback_all",
  ];
  if (fieldAcceptanceCameraOnlyMissing) {
    fieldAcceptanceNoMotionReadbackActionIds.push("refresh_camera_first_frame");
  } else if (!liveClosureSummary.live_wysiwyg_ready) {
    fieldAcceptanceNoMotionReadbackActionIds.push("refresh_current_wysiwyg");
  }
  if (liveClosureSummary.radar_overlay_needs_refresh) {
    fieldAcceptanceNoMotionReadbackActionIds.push("refresh_radar_map_overlay");
  }
  const fieldAcceptanceNoMotionReadbackActionLabels = [
    "复验全部读数",
    ...(fieldAcceptanceCameraOnlyMissing ? ["复测相机首帧"] : !liveClosureSummary.live_wysiwyg_ready ? ["刷新当前所见"] : []),
    ...(liveClosureSummary.radar_overlay_needs_refresh ? ["刷新雷达贴图"] : []),
  ];
  const fieldAcceptanceNoMotionReadbackActionLabelById: Record<RobotControlFieldAcceptanceNoMotionReadbackActionId, string> = {
    readback_all: "复验全部读数",
    refresh_current_wysiwyg: "刷新当前所见",
    refresh_camera_first_frame: "复测相机首帧",
    refresh_radar_map_overlay: "刷新雷达贴图",
  };
  const fieldAcceptanceNoMotionReadbackActionEndpointById: Record<RobotControlFieldAcceptanceNoMotionReadbackActionId, string> = {
    readback_all: "/api/robot-control/summary",
    refresh_current_wysiwyg: fieldAcceptanceWysiwygRefreshPlan.sequence[0] || liveClosureSummary.live_wysiwyg_primary_refresh_endpoint || "/api/robot-control/summary",
    refresh_camera_first_frame: liveClosureSummary.fixed_live_wysiwyg_camera_probe_endpoint,
    refresh_radar_map_overlay: liveClosureSummary.fixed_live_wysiwyg_radar_refresh_endpoint,
  };
  const fieldAcceptanceNoMotionReadbackActionSequenceById: Record<RobotControlFieldAcceptanceNoMotionReadbackActionId, string[]> = {
    readback_all: Array.from(new Set([
      ...fieldAcceptanceSteps.flatMap((item) => item.acceptance_endpoints),
      ...fieldAcceptanceWysiwygRefreshPlan.sequence,
      "/api/robot-control/summary",
    ])),
    refresh_current_wysiwyg: fieldAcceptanceWysiwygRefreshPlan.sequence.length > 0
      ? fieldAcceptanceWysiwygRefreshPlan.sequence
      : ["/api/robot-control/summary"],
    refresh_camera_first_frame: [
      liveClosureSummary.fixed_live_wysiwyg_camera_probe_endpoint,
      liveClosureSummary.fixed_live_wysiwyg_camera_mjpeg_status_endpoint,
      "/api/robot-control/summary",
    ],
    refresh_radar_map_overlay: [
      liveClosureSummary.fixed_live_wysiwyg_radar_refresh_endpoint,
      liveClosureSummary.fixed_live_wysiwyg_radar_status_endpoint,
      liveClosureSummary.fixed_live_wysiwyg_map_preview_endpoint,
      "/api/robot-control/summary",
    ],
  };
  const fieldAcceptanceNoMotionReadbackActionSequenceLabelsById: Record<RobotControlFieldAcceptanceNoMotionReadbackActionId, string[]> = {
    readback_all: fieldAcceptanceNoMotionReadbackActionSequenceById.readback_all.map((endpoint) => {
      if (endpoint.includes("/camera/first-frame/probe")) return "复测相机首帧";
      if (endpoint.includes("/camera/mjpeg/status")) return "读取相机 MJPEG 状态";
      if (endpoint.includes("/radar/scan-proof/refresh")) return "刷新雷达扫描读数";
      if (endpoint.includes("/radar/status")) return "读取雷达状态";
      if (endpoint.includes("/map/preview")) return "刷新地图画面";
      if (endpoint.includes("/base/feedback-samples")) return "复验轮速采样";
      if (endpoint.includes("/nav2/goal/execution/latest")) return "读取最近行程";
      if (endpoint.includes("/delivery/latest")) return "读取送达确认";
      if (endpoint.includes("/free-roam/autonomy/latest")) return "读取自由移动状态";
      if (endpoint.includes("/summary")) return "刷新总览";
      return "只读复验";
    }),
    refresh_current_wysiwyg: fieldAcceptanceWysiwygRefreshPlan.labels.length > 0
      ? fieldAcceptanceWysiwygRefreshPlan.labels
      : ["刷新总览"],
    refresh_camera_first_frame: ["复测相机首帧", "读取相机 MJPEG 状态", "刷新总览"],
    refresh_radar_map_overlay: ["刷新雷达扫描读数", "读取雷达状态", "刷新地图画面", "刷新总览"],
  };
  const fieldAcceptanceNoMotionReadbackActionSummaryById: Record<RobotControlFieldAcceptanceNoMotionReadbackActionId, string> = {
    readback_all: `只读刷新行程、键盘、自由移动、画面、雷达和地图状态，不执行动作；链路：${fieldAcceptanceNoMotionReadbackActionSequenceLabelsById.readback_all.join("、")}。`,
    refresh_current_wysiwyg: `只读处理当前所见缺口：${fieldAcceptanceNoMotionReadbackActionSequenceLabelsById.refresh_current_wysiwyg.join("、")}。`,
    refresh_camera_first_frame: "只读复测相机首帧、读取共享 MJPEG 状态，再刷新总览；用于确认画面 WYSIWYG 和建图首帧是否解除。",
    refresh_radar_map_overlay: "只读刷新雷达扫描读数、读取雷达状态、刷新地图画面，再刷新总览确认雷达点贴到当前地图。",
  };
  const fieldAcceptanceNoMotionReadbackActions: RobotControlFieldAcceptanceNoMotionReadbackAction[] = fieldAcceptanceNoMotionReadbackActionIds
    .map((id) => {
      const endpoint = fieldAcceptanceNoMotionReadbackActionEndpointById[id];
      const sequence = fieldAcceptanceNoMotionReadbackActionSequenceById[id];
      return {
        id,
        label: fieldAcceptanceNoMotionReadbackActionLabelById[id],
        endpoint,
        method: fieldAcceptanceNoMotionReadbackMethod(endpoint),
        sequence_endpoints: sequence,
        sequence_labels: fieldAcceptanceNoMotionReadbackActionSequenceLabelsById[id],
        refreshes_summary: sequence.some((item) => item.includes("/summary")),
        refreshes_radar_scan_proof: sequence.some((item) => item.includes("/radar/scan-proof/refresh")),
        refreshes_camera_first_frame_probe: sequence.some((item) => item.includes("/camera/first-frame/probe")),
        refreshes_map_preview: sequence.some((item) => item.includes("/map/preview")),
        refreshes_radar_status: sequence.some((item) => item.includes("/radar/status")),
        refreshes_camera_mjpeg_status: sequence.some((item) => item.includes("/camera/mjpeg/status")),
        summary_plain: fieldAcceptanceNoMotionReadbackActionSummaryById[id],
        sends_motion_when_clicked: false,
        starts_nav2_when_clicked: false,
        starts_manual_when_clicked: false,
        starts_keyboard_when_clicked: false,
        starts_free_roam_when_clicked: false,
        starts_map_runtime_when_clicked: false,
        starts_radar_lifecycle_when_clicked: false,
        submits_delivery_when_clicked: false,
        stops_motion_when_clicked: false,
      };
    });
  const fieldAcceptancePrimaryNoMotionReadbackActionId: RobotControlFieldAcceptanceNoMotionReadbackActionId | "none" = liveClosureSummary.radar_overlay_needs_refresh
    && fieldAcceptanceWysiwygRefreshModeValue !== "all_wysiwyg"
      ? "refresh_radar_map_overlay"
    : fieldAcceptanceCameraOnlyMissing
      ? "refresh_camera_first_frame"
    : !liveClosureSummary.live_wysiwyg_ready
      ? "refresh_current_wysiwyg"
      : "readback_all";
  const fieldAcceptancePrimaryNoMotionReadbackAction = fieldAcceptanceNoMotionReadbackActions
    .find((item) => item.id === fieldAcceptancePrimaryNoMotionReadbackActionId)
    ?? fieldAcceptanceNoMotionReadbackActions[0]
    ?? null;
  const fieldAcceptanceOperatorActionPlain = fieldAcceptanceSafetyConfirmReadyStepIds.length > 0
    ? `需要现场安全确认的运动验收：${fieldAcceptanceSafetyConfirmReadyDisplayLabels.join("、")}；勾一次安全确认后再手动执行，执行后只读读回复验。`
    : "当前没有只等安全确认的运动验收入口。";
  const fieldAcceptanceHardwareActionPlain = fieldAcceptanceHardwareActionIds.includes("camera_usb_recovery")
    ? `需要设备处理：${liveClosureSummary.camera_hardware_action_label}；${fieldAcceptanceCameraRecoveryActionPlain}该相机缺口阻塞画面和建图首帧，不阻塞低速自由移动。`
    : "当前没有必须先处理的设备动作；可继续按现场验收包复验。";
  const fieldAcceptanceNoMotionActionPlain = `可随时只读复验：${fieldAcceptanceNoMotionReadbackActionLabels.join("、")}；这些读回只刷新状态，不启动车辆、不进入手控、不会进入建图或雷达流程。`;
  const fieldAcceptanceRemainingActionPlain = `${fieldAcceptanceOperatorActionPlain} ${fieldAcceptanceHardwareActionPlain} ${fieldAcceptanceNoMotionActionPlain}`;
  const fieldAcceptanceWysiwygNextActions = [
    liveClosureSummary.live_wysiwyg_missing_surface_ids.includes("camera")
      ? liveClosureSummary.live_wysiwyg_camera_recovery_next_action_plain
      : "",
    liveClosureSummary.live_wysiwyg_missing_surface_ids.includes("radar_map_points")
      ? liveClosureSummary.live_wysiwyg_radar_map_refresh_next_action_plain
      : "",
  ].filter((item) => item.trim().length > 0);
  const fieldAcceptanceWysiwygNextActionPlain = liveClosureSummary.live_wysiwyg_ready
    ? "当前所见已满足：画面、地图、路线、小车位置和雷达点都按当前读数显示。"
    : fieldAcceptanceWysiwygNextActions.join("；")
      || `当前所见还差 ${liveClosureSummary.live_wysiwyg_missing_surface_ids.join(",") || "unknown"}；点击${liveClosureSummary.live_wysiwyg_primary_refresh_label || "刷新当前所见"}只刷新证据。`;
  const fieldAcceptancePacket: RobotControlFieldAcceptancePacket = {
    status: liveClosureSummary.status,
    summary_plain: `现场验收包：${liveClosureSummary.objective_audit_summary_plain} ${liveClosureSummary.live_motion_runbook_summary_plain} 下一步：${liveClosureSummary.next_action_plain}`,
    objective_total_count: liveClosureSummary.objective_audit_total_count,
    objective_done_count: liveClosureSummary.objective_audit_done_count,
    objective_remaining_count: liveClosureSummary.objective_audit_remaining_count,
    objective_missing_ids: liveClosureSummary.objective_audit_missing_objective_ids,
    objective_next_id: liveClosureSummary.objective_audit_next_objective_id,
    next_step_id: fieldAcceptanceNextStep?.id ?? "none",
    next_step_label: fieldAcceptanceNextStep?.label ?? "无待执行步骤",
    next_step_display_label: fieldAcceptanceNextStep?.display_label ?? fieldAcceptanceNextStep?.label ?? "无待执行步骤",
    next_step_start_endpoint: fieldAcceptanceNextStep?.start_endpoint ?? "none",
    next_step_sends_motion: fieldAcceptanceNextStep?.sends_motion_when_executed ?? false,
    next_step_requires_safety_confirm: fieldAcceptanceNextStep?.safety_confirm_required ?? false,
    ready_step_ids: liveClosureSummary.live_motion_runbook_ready_action_ids,
    blocked_step_ids: liveClosureSummary.live_motion_runbook_blocked_action_ids,
    motion_step_ids: fieldAcceptanceMotionStepIds,
    no_motion_step_ids: fieldAcceptanceSteps
      .filter((item) => !item.sends_motion_when_executed)
      .map((item) => item.id),
    safety_confirm_ready_step_ids: fieldAcceptanceSafetyConfirmReadyStepIds,
    safety_confirm_ready_action_labels: fieldAcceptanceSafetyConfirmReadyActions.map((item) => item.label),
    safety_confirm_ready_action_display_labels: fieldAcceptanceSafetyConfirmReadyDisplayLabels,
    safety_confirm_ready_action_start_endpoints: fieldAcceptanceSafetyConfirmReadyActions.map((item) => item.start_endpoint),
    safety_confirm_ready_actions: fieldAcceptanceSafetyConfirmReadyActions,
    primary_safety_confirm_ready_action_id: fieldAcceptancePrimarySafetyConfirmReadyAction?.id ?? "none",
    primary_safety_confirm_ready_action_label: fieldAcceptancePrimarySafetyConfirmReadyAction?.label ?? "无待执行运动验收",
    primary_safety_confirm_ready_action_display_label: fieldAcceptancePrimarySafetyConfirmReadyAction?.display_label
      ?? fieldAcceptancePrimarySafetyConfirmReadyAction?.label
      ?? "无待执行运动验收",
    primary_safety_confirm_ready_action_start_endpoint: fieldAcceptancePrimarySafetyConfirmReadyAction?.start_endpoint ?? "none",
    primary_safety_confirm_ready_action_requires_safety_confirm: fieldAcceptancePrimarySafetyConfirmReadyAction?.requires_safety_confirm ?? false,
    primary_safety_confirm_ready_action_sends_motion: fieldAcceptancePrimarySafetyConfirmReadyAction?.sends_motion_when_executed ?? false,
    hardware_action_ids: fieldAcceptanceHardwareActionIds,
    hardware_action_labels: fieldAcceptanceHardwareActions.map((item) => item.label),
    hardware_action_after_readback_endpoints: fieldAcceptanceHardwareActions.map((item) => item.after_action_readback_endpoint),
    hardware_action_after_readback_sequences: fieldAcceptanceHardwareActions.map((item) => item.after_action_readback_sequence.join("|")),
    hardware_action_after_readback_sequence_labels: fieldAcceptanceHardwareActions.map((item) => item.after_action_readback_sequence_labels.join("|")),
    hardware_actions: fieldAcceptanceHardwareActions,
    primary_hardware_action_id: fieldAcceptancePrimaryHardwareAction?.id ?? "none",
    primary_hardware_action_label: fieldAcceptancePrimaryHardwareAction?.label ?? "无设备处理动作",
    primary_hardware_action_after_readback_endpoint: fieldAcceptancePrimaryHardwareAction?.after_action_readback_endpoint ?? "none",
    primary_hardware_action_after_readback_sequence: fieldAcceptancePrimaryHardwareAction?.after_action_readback_sequence ?? [],
    primary_hardware_action_after_readback_sequence_labels: fieldAcceptancePrimaryHardwareAction?.after_action_readback_sequence_labels ?? [],
    primary_hardware_action_blocks_mapping_start: fieldAcceptancePrimaryHardwareAction?.blocks_mapping_start ?? false,
    primary_hardware_action_blocks_free_move: fieldAcceptancePrimaryHardwareAction?.blocks_free_move ?? false,
    missing_evidence_ids: fieldAcceptanceMissingEvidenceItems.map((item) => item.id),
    missing_evidence_labels: fieldAcceptanceMissingEvidenceItems.map((item) => item.label),
    missing_evidence_items: fieldAcceptanceMissingEvidenceItems,
    primary_missing_evidence_id: fieldAcceptancePrimaryMissingEvidence?.id ?? "none",
    primary_missing_evidence_label: fieldAcceptancePrimaryMissingEvidence?.label ?? "无缺失证据",
    primary_missing_evidence_action_id: fieldAcceptancePrimaryMissingEvidence?.action_id ?? "none",
    primary_missing_evidence_action_label: fieldAcceptancePrimaryMissingEvidenceAction?.label ?? "无对应动作",
    primary_missing_evidence_action_display_label: fieldAcceptancePrimaryMissingEvidenceAction?.display_label
      ?? fieldAcceptancePrimaryMissingEvidenceAction?.label
      ?? "无对应动作",
    primary_missing_evidence_readback_endpoint: fieldAcceptancePrimaryMissingEvidence?.readback_endpoint ?? "none",
    primary_missing_evidence_readback_method: fieldAcceptancePrimaryMissingEvidence?.readback_method ?? "none",
    primary_missing_evidence_requires_motion_before_readback: fieldAcceptancePrimaryMissingEvidence?.requires_motion_before_readback ?? false,
    primary_missing_evidence_requires_safety_confirm_before_motion: fieldAcceptancePrimaryMissingEvidence?.requires_safety_confirm_before_motion ?? false,
    primary_missing_evidence_blocks_field_acceptance: fieldAcceptancePrimaryMissingEvidence?.blocks_field_acceptance ?? false,
    no_motion_readback_action_ids: fieldAcceptanceNoMotionReadbackActionIds,
    no_motion_readback_action_labels: fieldAcceptanceNoMotionReadbackActions.map((item) => item.label),
    no_motion_readback_action_endpoints: fieldAcceptanceNoMotionReadbackActions.map((item) => item.endpoint),
    no_motion_readback_action_methods: fieldAcceptanceNoMotionReadbackActions.map((item) => item.method),
    no_motion_readback_action_sequences: fieldAcceptanceNoMotionReadbackActions.map((item) => item.sequence_endpoints.join("|")),
    no_motion_readback_action_sequence_labels: fieldAcceptanceNoMotionReadbackActions.map((item) => item.sequence_labels.join("|")),
    no_motion_readback_actions: fieldAcceptanceNoMotionReadbackActions,
    primary_no_motion_readback_action_id: fieldAcceptancePrimaryNoMotionReadbackAction?.id ?? "none",
    primary_no_motion_readback_action_label: fieldAcceptancePrimaryNoMotionReadbackAction?.label ?? "无只读复验动作",
    primary_no_motion_readback_action_endpoint: fieldAcceptancePrimaryNoMotionReadbackAction?.endpoint ?? "none",
    primary_no_motion_readback_action_method: fieldAcceptancePrimaryNoMotionReadbackAction?.method ?? "none",
    primary_no_motion_readback_action_sequence: fieldAcceptancePrimaryNoMotionReadbackAction?.sequence_endpoints ?? [],
    primary_no_motion_readback_action_sequence_labels: fieldAcceptancePrimaryNoMotionReadbackAction?.sequence_labels ?? [],
    primary_no_motion_readback_action_refreshes_summary: fieldAcceptancePrimaryNoMotionReadbackAction?.refreshes_summary ?? false,
    primary_no_motion_readback_action_refreshes_radar_scan_proof: fieldAcceptancePrimaryNoMotionReadbackAction?.refreshes_radar_scan_proof ?? false,
    primary_no_motion_readback_action_refreshes_camera_first_frame_probe: fieldAcceptancePrimaryNoMotionReadbackAction?.refreshes_camera_first_frame_probe ?? false,
    primary_no_motion_readback_action_refreshes_map_preview: fieldAcceptancePrimaryNoMotionReadbackAction?.refreshes_map_preview ?? false,
    primary_no_motion_readback_action_refreshes_radar_status: fieldAcceptancePrimaryNoMotionReadbackAction?.refreshes_radar_status ?? false,
    primary_no_motion_readback_action_refreshes_camera_mjpeg_status: fieldAcceptancePrimaryNoMotionReadbackAction?.refreshes_camera_mjpeg_status ?? false,
    primary_no_motion_readback_action_sends_motion: fieldAcceptancePrimaryNoMotionReadbackAction?.sends_motion_when_clicked ?? false,
    remaining_operator_action_summary_plain: fieldAcceptanceOperatorActionPlain,
    remaining_hardware_action_summary_plain: fieldAcceptanceHardwareActionPlain,
    remaining_no_motion_action_summary_plain: fieldAcceptanceNoMotionActionPlain,
    remaining_action_summary_plain: fieldAcceptanceRemainingActionPlain,
    acceptance_endpoints: Array.from(new Set(fieldAcceptanceSteps.flatMap((item) => item.acceptance_endpoints))),
    safety_confirm_required: liveClosureSummary.live_motion_runbook_safety_confirm_required,
    minimal_precheck_safety_only: liveClosureSummary.live_motion_runbook_minimal_precheck_safety_only,
    wysiwyg_ready: liveClosureSummary.live_wysiwyg_ready,
    wysiwyg_missing_surface_ids: liveClosureSummary.live_wysiwyg_missing_surface_ids,
    wysiwyg_primary_refresh_endpoint: liveClosureSummary.live_wysiwyg_primary_refresh_endpoint,
    wysiwyg_primary_refresh_label: liveClosureSummary.live_wysiwyg_primary_refresh_label,
    wysiwyg_next_action_plain: fieldAcceptanceWysiwygNextActionPlain,
    wysiwyg_camera_next_action_plain: liveClosureSummary.live_wysiwyg_camera_recovery_next_action_plain,
    wysiwyg_radar_map_next_action_plain: liveClosureSummary.live_wysiwyg_radar_map_refresh_next_action_plain,
    wysiwyg_refresh_sequence: fieldAcceptanceWysiwygRefreshPlan.sequence,
    wysiwyg_refresh_sequence_labels: fieldAcceptanceWysiwygRefreshPlan.labels,
    wysiwyg_refresh_mode: fieldAcceptanceWysiwygRefreshModeValue,
    fixed_wysiwyg_radar_refresh_endpoint: liveClosureSummary.fixed_live_wysiwyg_radar_refresh_endpoint,
    fixed_wysiwyg_camera_probe_endpoint: liveClosureSummary.fixed_live_wysiwyg_camera_probe_endpoint,
    fixed_wysiwyg_map_preview_endpoint: liveClosureSummary.fixed_live_wysiwyg_map_preview_endpoint,
    fixed_wysiwyg_radar_status_endpoint: liveClosureSummary.fixed_live_wysiwyg_radar_status_endpoint,
    fixed_wysiwyg_camera_mjpeg_status_endpoint: liveClosureSummary.fixed_live_wysiwyg_camera_mjpeg_status_endpoint,
    wysiwyg_refreshes_radar_scan_proof: fieldAcceptanceWysiwygRefreshPlan.sequence.includes("/api/robot-control/radar/scan-proof/refresh"),
    wysiwyg_refreshes_camera_first_frame_probe: fieldAcceptanceWysiwygRefreshPlan.sequence.includes("/api/robot-control/camera/first-frame/probe"),
    wysiwyg_refreshes_map_preview: fieldAcceptanceWysiwygRefreshPlan.sequence.includes("/api/robot-control/map/preview"),
    wysiwyg_refreshes_radar_status: fieldAcceptanceWysiwygRefreshPlan.sequence.includes("/api/robot-control/radar/status"),
    wysiwyg_refreshes_camera_mjpeg_status: fieldAcceptanceWysiwygRefreshPlan.sequence.includes("/api/robot-control/camera/mjpeg/status"),
    wysiwyg_refresh_sends_motion: false,
    wysiwyg_refresh_starts_nav2: false,
    wysiwyg_refresh_starts_manual: false,
    wysiwyg_refresh_starts_keyboard: false,
    wysiwyg_refresh_starts_free_roam: false,
    wysiwyg_refresh_starts_radar_lifecycle: false,
    wysiwyg_refresh_starts_map_runtime: false,
    wysiwyg_refresh_submits_delivery: false,
    wysiwyg_refresh_stops_motion: false,
    mapping_start_ready: liveClosureSummary.mapping_start_ready,
    mapping_missing_evidence: mappingRunbookItem?.missing_evidence ?? liveClosureSummary.mapping_start_missing_reasons,
    camera_blocks_mapping_start: liveClosureSummary.camera_blocks_mapping_start,
    camera_blocks_free_move: liveClosureSummary.camera_blocks_free_move,
    sends_motion_when_clicked: false,
    starts_nav2_when_clicked: false,
    starts_manual_when_clicked: false,
    starts_free_roam_when_clicked: false,
    starts_map_runtime_when_clicked: false,
    steps: fieldAcceptanceSteps,
  };
  const nav2RouteAcceptancePacket: RobotControlNav2RouteAcceptancePacket = {
    action_id: "run_nav2_route",
    label: "完整行程执行",
    display_label: liveClosureSummary.needs_same_window_wheel_rerun ? "重跑图上行程并复验轮速" : "完整行程执行",
    status: liveClosureSummary.status,
    proof_status: runNav2RouteRunbookItem?.proof_status ?? "blocked",
    ready: runNav2RouteRunbookItem?.ready ?? false,
    completed: runNav2RouteRunbookItem?.completed ?? false,
    start_endpoint: "/api/robot-control/nav2/goal/execute",
    stop_endpoint: "/api/robot-control/base/stop",
    start_sends_motion: true,
    requires_safety_confirm: liveClosureSummary.wheel_rerun_requires_safety_confirm,
    minimal_precheck_safety_only: liveClosureSummary.wheel_rerun_minimal_precheck_safety_only,
    camera_preflight_required: false,
    radar_preflight_required: false,
    route_wysiwyg_preflight_required: false,
    blocked_by_camera_wysiwyg: false,
    blocked_by_radar_wysiwyg: false,
    route_ready_on_map: liveClosureSummary.route_ready_on_map,
    nav2_goal_succeeded: liveClosureSummary.nav2_goal_succeeded,
    same_window_wheel_lr_nonzero: liveClosureSummary.wheel_lr_nonzero_proven,
    delivery_success: liveClosureSummary.delivery_success,
    needs_same_window_wheel_rerun: liveClosureSummary.needs_same_window_wheel_rerun,
    delivery_success_required: liveClosureSummary.delivery_success_required,
    missing_evidence: runNav2RouteRunbookItem?.missing_evidence ?? [],
    required_success_markers: liveClosureSummary.wheel_rerun_required_success_markers,
    acceptance_endpoints: runNav2RouteRunbookItem?.acceptance_endpoints ?? liveClosureSummary.wheel_rerun_acceptance_endpoints,
    readback_endpoints: liveClosureSummary.wheel_rerun_readback_endpoints,
    fixed_latest_endpoint: "/api/robot-control/nav2/goal/execution/latest",
    fixed_wheel_readback_endpoint: "/api/robot-control/base/feedback-samples",
    fixed_delivery_latest_endpoint: "/api/robot-control/delivery/latest",
    fixed_delivery_complete_endpoint: "/api/robot-control/delivery/complete",
    delivery_complete_sends_motion: false,
    readback_sends_motion: false,
    readback_starts_nav2: false,
    readback_starts_manual: false,
    readback_starts_keyboard: false,
    readback_starts_free_roam: false,
    readback_starts_map_runtime: false,
    readback_submits_delivery: false,
    readback_stops_motion: false,
    command_mode: liveClosureSummary.wheel_rerun_command_mode,
    next_base_command_mode: liveClosureSummary.wheel_rerun_next_base_command_mode,
    latest_raw_left: liveClosureSummary.wheel_rerun_latest_raw_left,
    latest_raw_right: liveClosureSummary.wheel_rerun_latest_raw_right,
    feedback_sample_count: liveClosureSummary.wheel_rerun_feedback_sample_count,
    feedback_nonzero_sample_count: liveClosureSummary.wheel_rerun_feedback_nonzero_sample_count,
    current_gap_plain: liveClosureSummary.wheel_rerun_current_gap_plain,
    checklist_plain: liveClosureSummary.wheel_rerun_checklist_plain,
    acceptance_plain: liveClosureSummary.wheel_rerun_acceptance_plain,
    no_extra_precheck_plain: liveClosureSummary.wheel_rerun_no_extra_precheck_plain,
    delivery_next_action_plain: liveClosureSummary.wheel_rerun_delivery_next_action_plain,
    sends_motion_when_clicked: false,
  };
  const fieldAcceptancePrimarySafetyAction = fieldAcceptancePacket.safety_confirm_ready_actions.find(
    (action) => action.id === fieldAcceptancePacket.primary_safety_confirm_ready_action_id,
  );
  const fieldAcceptanceSafetyConfirmReadyActionAcceptanceEndpoints = fieldAcceptancePacket.safety_confirm_ready_actions.map(
    (action) => action.acceptance_endpoints.join("|"),
  );
  const fieldAcceptanceParallelStatusPlain = [
    fieldAcceptancePacket.primary_no_motion_readback_action_id === "none"
      ? "只读复验：暂无"
      : `只读复验：${fieldAcceptancePacket.primary_no_motion_readback_action_label}`,
    fieldAcceptancePacket.primary_safety_confirm_ready_action_id === "none"
      ? "安全确认后动作：暂无"
      : `安全确认后动作：${fieldAcceptancePacket.primary_safety_confirm_ready_action_display_label ?? fieldAcceptancePacket.primary_safety_confirm_ready_action_label}`,
    fieldAcceptancePacket.primary_hardware_action_id === "none"
      ? "设备处理：暂无"
      : `设备处理：${fieldAcceptancePacket.primary_hardware_action_label}`,
    `建图缺口：${liveClosureSummary.mapping_start_missing_reasons.join("、") || "暂无"}`,
    `自由移动：${liveClosureSummary.free_move_start_ready ? "可在安全确认后先做" : "暂不可做"}`,
  ].join("；");

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
      status: connectionStatus,
      loaded_count: loadedCount,
      blocked_count: blockedCount,
      failed_count: failedCount,
      schema_mismatch_count: schemaMismatchCount,
      dangerous_true_fields: dangerous,
      blocked_reasons: connectionBlockedReasons,
      last_refresh_ms: observedAt,
    },
    current_fact_plain: [portDriftPlain, summaryCurrentFactPlain(readbackSummary, safeCommandBoundary)]
      .filter(Boolean)
      .join("；"),
    action_status_cards: actionStatusCards,
    goal_checklist: goalChecklist,
    goal_checklist_summary: goalSummary,
    live_closure_summary: liveClosureSummary,
    goal_summary: goalSummary,
    // 当前卡点和四项目标总览放到 summary 顶层，便于现场只用一条 curl 判断下一步。
    status: liveClosureSummary.status,
    live_status: liveClosureSummary.status,
    summary_plain: liveClosureSummary.summary_plain,
    next_action_plain: liveClosureSummary.next_action_plain,
    objective_audit_status: liveClosureSummary.objective_audit_status,
    objective_audit_total_count: liveClosureSummary.objective_audit_total_count,
    objective_audit_done_count: liveClosureSummary.objective_audit_done_count,
    objective_audit_remaining_count: liveClosureSummary.objective_audit_remaining_count,
    objective_audit_next_objective_id: liveClosureSummary.objective_audit_next_objective_id,
    objective_audit_missing_objective_ids: liveClosureSummary.objective_audit_missing_objective_ids,
    objective_audit_summary_plain: liveClosureSummary.objective_audit_summary_plain,
    objective_audit_items: liveClosureSummary.objective_audit_items,
    fixed_objective_audit_summary_endpoint: liveClosureSummary.fixed_objective_audit_summary_endpoint,
    objective_audit_sends_motion_when_clicked: liveClosureSummary.objective_audit_sends_motion_when_clicked,
    objective_missing_ids: liveClosureSummary.objective_audit_missing_objective_ids,
    objective_next_id: liveClosureSummary.objective_audit_next_objective_id,
    motion_objective_complete: motionObjectiveAlias?.completed === true,
    wysiwyg_objective_complete: liveClosureSummary.live_wysiwyg_ready,
    precheck_objective_complete: precheckObjectiveAlias?.completed === true,
    mapping_objective_complete: mappingObjectiveAlias?.completed === true,
    motion_ready: motionObjectiveAlias?.actionable === true,
    motion_complete: motionObjectiveAlias?.completed === true,
    wysiwyg_ready: liveClosureSummary.live_wysiwyg_ready,
    wysiwyg_complete: liveClosureSummary.live_wysiwyg_ready,
    precheck_ready: liveClosureSummary.minimal_precheck_safety_only,
    precheck_complete: precheckObjectiveAlias?.completed === true,
    mapping_ready: liveClosureSummary.mapping_start_ready,
    mapping_complete: mappingObjectiveAlias?.completed === true,
    // summary 是现场最常 curl 的入口；地图和 ROS2 旁路观察信息必须放顶层，避免现场再翻嵌套对象。
    map_display_primary_tool: liveClosureSummary.map_display_primary_tool,
    map_display_primary_url: liveClosureSummary.map_display_primary_url,
    map_display_legacy_url: liveClosureSummary.map_display_legacy_url,
    map_display_primary_action_label: liveClosureSummary.map_display_primary_action_label,
    map_display_primary_action_opens_new_window: liveClosureSummary.map_display_primary_action_opens_new_window,
    map_display_primary_action_opens_current_page: liveClosureSummary.map_display_primary_action_opens_current_page,
    map_display_direct_map_default_observer: liveClosureSummary.map_display_direct_map_default_observer,
    map_display_direct_map_only: liveClosureSummary.map_display_direct_map_only,
    map_display_direct_map_viewport_priority: liveClosureSummary.map_display_direct_map_viewport_priority,
    map_display_direct_map_canvas_height_mode: liveClosureSummary.map_display_direct_map_canvas_height_mode,
    map_display_direct_map_keeps_page_fullscreen_without_browser_api: liveClosureSummary.map_display_direct_map_keeps_page_fullscreen_without_browser_api,
    map_display_direct_map_browser_fullscreen_required: liveClosureSummary.map_display_direct_map_browser_fullscreen_required,
    map_display_direct_map_refreshes_radar_scan_proof_on_enter: liveClosureSummary.map_display_direct_map_refreshes_radar_scan_proof_on_enter,
    map_display_direct_map_refreshes_map_preview_on_enter: liveClosureSummary.map_display_direct_map_refreshes_map_preview_on_enter,
    map_display_direct_map_refreshes_radar_status_on_enter: liveClosureSummary.map_display_direct_map_refreshes_radar_status_on_enter,
    map_display_direct_map_starts_radar_lifecycle_on_enter: liveClosureSummary.map_display_direct_map_starts_radar_lifecycle_on_enter,
    map_display_default_zoom_percent: liveClosureSummary.map_display_default_zoom_percent,
    map_display_max_zoom_percent: liveClosureSummary.map_display_max_zoom_percent,
    map_display_too_small_next_action_plain: liveClosureSummary.map_display_too_small_next_action_plain,
    map_display_ros2_companion_answer_plain: liveClosureSummary.map_display_ros2_companion_answer_plain,
    map_display_ros2_companion_plain: liveClosureSummary.map_display_ros2_companion_plain,
    map_display_operator_default_surface: liveClosureSummary.map_display_operator_default_surface,
    map_display_companion_replaces_pc_ui: liveClosureSummary.map_display_companion_replaces_pc_ui,
    map_display_wysiwyg_overlays: liveClosureSummary.map_display_wysiwyg_overlays,
    map_display_ros2_companion_required: liveClosureSummary.map_display_ros2_companion_required,
    map_display_ros2_companion_tools: liveClosureSummary.map_display_ros2_companion_tools,
    map_display_engineering_tools_visible_by_default: liveClosureSummary.map_display_engineering_tools_visible_by_default,
    map_display_engineering_tools_action_label: liveClosureSummary.map_display_engineering_tools_action_label,
    map_display_ordinary_user_tool: liveClosureSummary.map_display_ordinary_user_tool,
    map_display_rviz_role_plain: liveClosureSummary.map_display_rviz_role_plain,
    map_display_rviz_launch_command: liveClosureSummary.map_display_rviz_launch_command,
    map_display_foxglove_role_plain: liveClosureSummary.map_display_foxglove_role_plain,
    map_display_foxglove_bridge_package: liveClosureSummary.map_display_foxglove_bridge_package,
    map_display_foxglove_bridge_install_command: liveClosureSummary.map_display_foxglove_bridge_install_command,
    map_display_foxglove_bridge_launch_command: liveClosureSummary.map_display_foxglove_bridge_launch_command,
    map_display_foxglove_websocket_url: liveClosureSummary.map_display_foxglove_websocket_url,
    map_display_foxglove_web_app_url: liveClosureSummary.map_display_foxglove_web_app_url,
    map_display_ros2_observe_topics: liveClosureSummary.map_display_ros2_observe_topics,
    map_display_ros2_observe_motion_topics: liveClosureSummary.map_display_ros2_observe_motion_topics,
    map_display_ros2_observe_control_tools: liveClosureSummary.map_display_ros2_observe_control_tools,
    map_display_engineering_tools_sends_motion: liveClosureSummary.map_display_engineering_tools_sends_motion,
    map_display_companion_plain: liveClosureSummary.map_display_companion_plain,
    map_display_sends_motion_when_clicked: liveClosureSummary.map_display_sends_motion_when_clicked,
    map_display_starts_ros2: liveClosureSummary.map_display_starts_ros2,
    map_display_starts_rviz2: liveClosureSummary.map_display_starts_rviz2,
    map_display_starts_foxglove: liveClosureSummary.map_display_starts_foxglove,
    map_display_starts_nav2: liveClosureSummary.map_display_starts_nav2,
    map_display_starts_map_runtime: liveClosureSummary.map_display_starts_map_runtime,
    // 四项目标总览也透到 summary 顶层，现场脚本不必在多个 endpoint 和嵌套路径之间切换。
    live_wysiwyg_ready: liveClosureSummary.live_wysiwyg_ready,
    live_wysiwyg_missing_surface_ids: liveClosureSummary.live_wysiwyg_missing_surface_ids,
    // 兼容现场脚本的直观命名：这里的 reason 与 surface id 保持同源，避免脚本再猜字段。
    live_wysiwyg_missing_reasons: liveClosureSummary.live_wysiwyg_missing_surface_ids,
    live_wysiwyg_only_camera_missing: liveWysiwygOnlyCameraMissing,
    live_wysiwyg_needs_refresh: liveClosureSummary.live_wysiwyg_needs_refresh,
    live_wysiwyg_readback_gap_surface_ids: liveClosureSummary.live_wysiwyg_readback_gap_surface_ids,
    live_wysiwyg_primary_readback_gap_surface_id: liveClosureSummary.live_wysiwyg_primary_readback_gap_surface_id,
    live_wysiwyg_missing_surface_refresh_endpoints: liveClosureSummary.live_wysiwyg_missing_surface_refresh_endpoints,
    live_wysiwyg_missing_surface_refresh_labels: liveClosureSummary.live_wysiwyg_missing_surface_refresh_labels,
    live_wysiwyg_primary_refresh_endpoint: liveClosureSummary.live_wysiwyg_primary_refresh_endpoint,
    live_wysiwyg_primary_refresh_label: liveClosureSummary.live_wysiwyg_primary_refresh_label,
    live_wysiwyg_diagnostic_plain: liveClosureSummary.live_wysiwyg_diagnostic_plain,
    live_wysiwyg_camera_diagnostic_plain: liveClosureSummary.live_wysiwyg_camera_diagnostic_plain,
    live_wysiwyg_radar_diagnostic_plain: liveClosureSummary.live_wysiwyg_radar_diagnostic_plain,
    live_wysiwyg_map_radar_diagnostic_plain: liveClosureSummary.live_wysiwyg_map_radar_diagnostic_plain,
    live_wysiwyg_refresh_plan_available: liveClosureSummary.live_wysiwyg_refresh_plan_available,
    live_wysiwyg_refresh_sequence: liveClosureSummary.live_wysiwyg_refresh_sequence,
    live_wysiwyg_refresh_sequence_labels: liveClosureSummary.live_wysiwyg_refresh_sequence_labels,
    live_wysiwyg_focused_refresh_sequence: fieldAcceptancePacket.wysiwyg_refresh_sequence,
    live_wysiwyg_focused_refresh_sequence_labels: fieldAcceptancePacket.wysiwyg_refresh_sequence_labels,
    live_wysiwyg_focused_refresh_mode: fieldAcceptanceWysiwygRefreshModeValue,
    live_wysiwyg_focused_refresh_sends_motion: fieldAcceptancePacket.wysiwyg_refresh_sends_motion,
    live_wysiwyg_focused_refreshes_camera_first_frame_probe: fieldAcceptancePacket.wysiwyg_refreshes_camera_first_frame_probe,
    live_wysiwyg_focused_refreshes_camera_mjpeg_status: fieldAcceptancePacket.wysiwyg_refreshes_camera_mjpeg_status,
    live_wysiwyg_focused_refreshes_radar_scan_proof: fieldAcceptancePacket.wysiwyg_refreshes_radar_scan_proof,
    live_wysiwyg_focused_refreshes_radar_status: fieldAcceptancePacket.wysiwyg_refreshes_radar_status,
    live_wysiwyg_focused_refreshes_map_preview: fieldAcceptancePacket.wysiwyg_refreshes_map_preview,
    fixed_live_wysiwyg_radar_refresh_endpoint: liveClosureSummary.fixed_live_wysiwyg_radar_refresh_endpoint,
    fixed_live_wysiwyg_camera_probe_endpoint: liveClosureSummary.fixed_live_wysiwyg_camera_probe_endpoint,
    fixed_live_wysiwyg_map_preview_endpoint: liveClosureSummary.fixed_live_wysiwyg_map_preview_endpoint,
    fixed_live_wysiwyg_radar_status_endpoint: liveClosureSummary.fixed_live_wysiwyg_radar_status_endpoint,
    fixed_live_wysiwyg_camera_mjpeg_status_endpoint: liveClosureSummary.fixed_live_wysiwyg_camera_mjpeg_status_endpoint,
    fixed_radar_start_endpoint: liveClosureSummary.fixed_radar_start_endpoint,
    fixed_radar_stop_endpoint: liveClosureSummary.fixed_radar_stop_endpoint,
    radar_start_map_wysiwyg_required: liveClosureSummary.radar_start_map_wysiwyg_required,
    radar_start_map_wysiwyg_sequence: liveClosureSummary.radar_start_map_wysiwyg_sequence,
    radar_start_map_wysiwyg_sequence_labels: liveClosureSummary.radar_start_map_wysiwyg_sequence_labels,
    radar_start_refreshes_scan_proof: liveClosureSummary.radar_start_refreshes_scan_proof,
    radar_start_refreshes_radar_status: liveClosureSummary.radar_start_refreshes_radar_status,
    radar_start_refreshes_map_preview: liveClosureSummary.radar_start_refreshes_map_preview,
    radar_start_refreshes_summary: liveClosureSummary.radar_start_refreshes_summary,
    radar_start_sends_motion: liveClosureSummary.radar_start_sends_motion,
    radar_start_starts_nav2: liveClosureSummary.radar_start_starts_nav2,
    radar_start_starts_manual: liveClosureSummary.radar_start_starts_manual,
    radar_start_starts_keyboard: liveClosureSummary.radar_start_starts_keyboard,
    radar_start_starts_free_roam: liveClosureSummary.radar_start_starts_free_roam,
    radar_start_starts_map_runtime: liveClosureSummary.radar_start_starts_map_runtime,
    radar_start_submits_delivery: liveClosureSummary.radar_start_submits_delivery,
    radar_start_stops_motion: liveClosureSummary.radar_start_stops_motion,
    live_wysiwyg_refresh_sends_motion: liveClosureSummary.live_wysiwyg_refresh_sends_motion,
    live_wysiwyg_refresh_starts_nav2: liveClosureSummary.live_wysiwyg_refresh_starts_nav2,
    live_wysiwyg_refresh_starts_manual: liveClosureSummary.live_wysiwyg_refresh_starts_manual,
    live_wysiwyg_refresh_starts_keyboard: liveClosureSummary.live_wysiwyg_refresh_starts_keyboard,
    live_wysiwyg_refresh_starts_free_roam: liveClosureSummary.live_wysiwyg_refresh_starts_free_roam,
    live_wysiwyg_refresh_starts_radar_lifecycle: liveClosureSummary.live_wysiwyg_refresh_starts_radar_lifecycle,
    live_wysiwyg_refresh_starts_map_runtime: liveClosureSummary.live_wysiwyg_refresh_starts_map_runtime,
    live_wysiwyg_surface_summaries: liveClosureSummary.live_wysiwyg_surface_summaries,
    primary_action_id: liveClosureSummary.primary_action_id,
    route_ready: liveClosureSummary.route_ready_on_map,
    route_ready_on_map: liveClosureSummary.route_ready_on_map,
    nav2_route_ready: liveClosureSummary.nav2_route_ready,
    nav2_complete: liveClosureSummary.nav2_goal_execution_proven,
    nav2_goal_succeeded: liveClosureSummary.nav2_goal_succeeded,
    nav2_goal_execution_proven: liveClosureSummary.nav2_goal_execution_proven,
    // 顶层字段全部复用 Nav2 验收包，避免现场脚本和页面卡片出现两套口径。
    trip_execution_ready: nav2RouteAcceptancePacket.ready,
    trip_execution_complete: nav2RouteAcceptancePacket.completed,
    trip_execution_missing_evidence: nav2RouteAcceptancePacket.missing_evidence,
    trip_execution_required_success_markers: nav2RouteAcceptancePacket.required_success_markers,
    trip_execution_readback_endpoints: nav2RouteAcceptancePacket.readback_endpoints,
    route_complete: routeComplete,
    trip_complete: routeComplete,
    wheel_lr_nonzero: liveClosureSummary.wheel_lr_nonzero_proven,
    wheel_lr_nonzero_proven: liveClosureSummary.wheel_lr_nonzero_proven,
    wheel_feedback_same_window_complete: nav2RouteAcceptancePacket.same_window_wheel_lr_nonzero,
    same_window_wheel_lr_nonzero_complete: nav2RouteAcceptancePacket.same_window_wheel_lr_nonzero,
    needs_same_window_wheel_rerun: liveClosureSummary.needs_same_window_wheel_rerun,
    route_delivery_success: liveClosureSummary.delivery_success,
    delivery_success_current: nav2RouteAcceptancePacket.delivery_success,
    delivery_success_required: liveClosureSummary.delivery_success_required,
    delivery_next_action_plain: liveClosureSummary.delivery_next_action_plain,
    fixed_delivery_latest_endpoint: liveClosureSummary.fixed_delivery_latest_endpoint,
    fixed_delivery_complete_endpoint: liveClosureSummary.fixed_delivery_complete_endpoint,
    delivery_latest_readback_only: liveClosureSummary.delivery_latest_readback_only,
    delivery_complete_sends_motion: liveClosureSummary.delivery_complete_sends_motion,
    wheel_rerun_ready_for_safety_confirm: liveClosureSummary.wheel_rerun_ready_for_safety_confirm,
    wheel_rerun_start_endpoint: liveClosureSummary.wheel_rerun_start_endpoint,
    wheel_rerun_start_sends_motion: liveClosureSummary.wheel_rerun_start_sends_motion,
    wheel_rerun_requires_safety_confirm: liveClosureSummary.wheel_rerun_requires_safety_confirm,
    wheel_rerun_readback_endpoint: liveClosureSummary.fixed_wheel_readback_endpoint,
    wheel_rerun_acceptance_endpoints: liveClosureSummary.wheel_rerun_acceptance_endpoints,
    wheel_rerun_readback_endpoints: liveClosureSummary.wheel_rerun_readback_endpoints,
    wheel_rerun_required_success_markers: liveClosureSummary.wheel_rerun_required_success_markers,
    wheel_rerun_current_gap_plain: liveClosureSummary.wheel_rerun_current_gap_plain,
    wheel_rerun_next_action_plain: liveClosureSummary.wheel_rerun_checklist_plain,
    wheel_rerun_acceptance_plain: liveClosureSummary.wheel_rerun_acceptance_plain,
    wheel_rerun_no_extra_precheck_plain: liveClosureSummary.wheel_rerun_no_extra_precheck_plain,
    minimal_precheck_safety_only: liveClosureSummary.minimal_precheck_safety_only,
    safety_confirm_required_for_motion: liveClosureSummary.safety_confirm_required_for_motion,
    live_motion_runbook_items: liveClosureSummary.live_motion_runbook_items,
    live_motion_runbook_action_ids: liveClosureSummary.live_motion_runbook_action_ids,
    live_motion_runbook_ready_action_ids: liveClosureSummary.live_motion_runbook_ready_action_ids,
    live_motion_runbook_blocked_action_ids: liveClosureSummary.live_motion_runbook_blocked_action_ids,
    live_motion_runbook_primary_action_id: liveClosureSummary.live_motion_runbook_primary_action_id,
    live_motion_runbook_start_endpoints: liveClosureSummary.live_motion_runbook_start_endpoints,
    live_motion_runbook_acceptance_endpoints: liveClosureSummary.live_motion_runbook_acceptance_endpoints,
    live_motion_runbook_minimal_precheck_safety_only: liveClosureSummary.live_motion_runbook_minimal_precheck_safety_only,
    live_motion_runbook_safety_confirm_required: liveClosureSummary.live_motion_runbook_safety_confirm_required,
    live_motion_runbook_summary_plain: liveClosureSummary.live_motion_runbook_summary_plain,
    live_motion_runbook_ready_plain: liveClosureSummary.live_motion_runbook_ready_plain,
    live_motion_runbook_blocked_plain: liveClosureSummary.live_motion_runbook_blocked_plain,
    live_motion_runbook_primary_action_plain: liveClosureSummary.live_motion_runbook_primary_action_plain,
    live_motion_runbook_minimal_precheck_plain: liveClosureSummary.live_motion_runbook_minimal_precheck_plain,
    field_acceptance_packet: fieldAcceptancePacket,
    field_acceptance_status: fieldAcceptancePacket.status,
    field_acceptance_next_step_id: fieldAcceptancePacket.next_step_id,
    field_acceptance_next_step_label: fieldAcceptancePacket.next_step_label,
    field_acceptance_next_step_display_label: fieldAcceptancePacket.next_step_display_label,
    field_acceptance_next_step_start_endpoint: fieldAcceptancePacket.next_step_start_endpoint,
    field_acceptance_next_step_sends_motion: fieldAcceptancePacket.next_step_sends_motion,
    field_acceptance_next_step_requires_safety_confirm: fieldAcceptancePacket.next_step_requires_safety_confirm,
    field_acceptance_parallel_status_plain: fieldAcceptanceParallelStatusPlain,
    field_acceptance_parallel_no_motion_action_id: fieldAcceptancePacket.primary_no_motion_readback_action_id,
    field_acceptance_parallel_no_motion_action_label: fieldAcceptancePacket.primary_no_motion_readback_action_label,
    field_acceptance_parallel_no_motion_action_endpoint: fieldAcceptancePacket.primary_no_motion_readback_action_endpoint,
    field_acceptance_parallel_no_motion_action_method: fieldAcceptancePacket.primary_no_motion_readback_action_method,
    field_acceptance_parallel_no_motion_action_sequence: fieldAcceptancePacket.primary_no_motion_readback_action_sequence,
    field_acceptance_parallel_no_motion_action_sequence_labels: fieldAcceptancePacket.primary_no_motion_readback_action_sequence_labels,
    field_acceptance_parallel_safety_action_id: fieldAcceptancePacket.primary_safety_confirm_ready_action_id,
    field_acceptance_parallel_safety_action_label: fieldAcceptancePacket.primary_safety_confirm_ready_action_label,
    field_acceptance_parallel_safety_action_display_label: fieldAcceptancePacket.primary_safety_confirm_ready_action_display_label,
    field_acceptance_parallel_safety_action_start_endpoint: fieldAcceptancePacket.primary_safety_confirm_ready_action_start_endpoint,
    field_acceptance_parallel_safety_action_acceptance_endpoints: fieldAcceptancePrimarySafetyAction?.acceptance_endpoints ?? [],
    field_acceptance_parallel_hardware_action_id: fieldAcceptancePacket.primary_hardware_action_id,
    field_acceptance_parallel_hardware_action_label: fieldAcceptancePacket.primary_hardware_action_label,
    field_acceptance_parallel_hardware_action_after_readback_sequence: fieldAcceptancePacket.primary_hardware_action_after_readback_sequence,
    field_acceptance_parallel_mapping_missing_evidence: liveClosureSummary.mapping_start_missing_reasons,
    field_acceptance_parallel_free_move_allowed_while_mapping_blocked: liveClosureSummary.free_move_start_ready && !liveClosureSummary.mapping_start_ready,
    field_acceptance_parallel_sends_motion_when_clicked: false,
    field_acceptance_ready_step_ids: fieldAcceptancePacket.ready_step_ids,
    field_acceptance_blocked_step_ids: fieldAcceptancePacket.blocked_step_ids,
    field_acceptance_motion_step_ids: fieldAcceptancePacket.motion_step_ids,
    field_acceptance_no_motion_step_ids: fieldAcceptancePacket.no_motion_step_ids,
    field_acceptance_safety_confirm_ready_step_ids: fieldAcceptancePacket.safety_confirm_ready_step_ids,
    field_acceptance_safety_confirm_ready_action_ids: fieldAcceptancePacket.safety_confirm_ready_step_ids,
    field_acceptance_safety_confirm_ready_action_labels: fieldAcceptancePacket.safety_confirm_ready_action_labels,
    field_acceptance_safety_confirm_ready_action_display_labels: fieldAcceptancePacket.safety_confirm_ready_action_display_labels,
    field_acceptance_safety_confirm_ready_action_endpoints: fieldAcceptancePacket.safety_confirm_ready_action_start_endpoints,
    field_acceptance_safety_confirm_ready_action_start_endpoints: fieldAcceptancePacket.safety_confirm_ready_action_start_endpoints,
    field_acceptance_safety_confirm_ready_action_stop_endpoints: fieldAcceptancePacket.safety_confirm_ready_actions.map((action) => action.stop_endpoint),
    field_acceptance_safety_confirm_ready_action_acceptance_endpoints: fieldAcceptanceSafetyConfirmReadyActionAcceptanceEndpoints,
    field_acceptance_safety_confirm_ready_action_minimal_precheck_safety_only: fieldAcceptancePacket.safety_confirm_ready_actions.map((action) => action.minimal_precheck_safety_only),
    field_acceptance_safety_confirm_ready_action_camera_preflight_required: fieldAcceptancePacket.safety_confirm_ready_actions.map((action) => action.camera_preflight_required),
    field_acceptance_safety_confirm_ready_action_radar_preflight_required: fieldAcceptancePacket.safety_confirm_ready_actions.map((action) => action.radar_preflight_required),
    field_acceptance_safety_confirm_ready_action_route_wysiwyg_preflight_required: fieldAcceptancePacket.safety_confirm_ready_actions.map((action) => action.route_wysiwyg_preflight_required),
    field_acceptance_safety_confirm_ready_actions: fieldAcceptancePacket.safety_confirm_ready_actions,
    field_acceptance_primary_safety_confirm_ready_action_id: fieldAcceptancePacket.primary_safety_confirm_ready_action_id,
    field_acceptance_primary_safety_confirm_ready_action_label: fieldAcceptancePacket.primary_safety_confirm_ready_action_label,
    field_acceptance_primary_safety_confirm_ready_action_display_label: fieldAcceptancePacket.primary_safety_confirm_ready_action_display_label,
    field_acceptance_primary_safety_confirm_ready_action_start_endpoint: fieldAcceptancePacket.primary_safety_confirm_ready_action_start_endpoint,
    field_acceptance_primary_safety_confirm_ready_action_stop_endpoint: fieldAcceptancePrimarySafetyAction?.stop_endpoint ?? "none",
    field_acceptance_primary_safety_confirm_ready_action_acceptance_endpoints: fieldAcceptancePrimarySafetyAction?.acceptance_endpoints ?? [],
    field_acceptance_primary_safety_confirm_ready_action_minimal_precheck_safety_only: fieldAcceptancePrimarySafetyAction?.minimal_precheck_safety_only ?? false,
    field_acceptance_primary_safety_confirm_ready_action_camera_preflight_required: fieldAcceptancePrimarySafetyAction?.camera_preflight_required ?? false,
    field_acceptance_primary_safety_confirm_ready_action_radar_preflight_required: fieldAcceptancePrimarySafetyAction?.radar_preflight_required ?? false,
    field_acceptance_primary_safety_confirm_ready_action_route_wysiwyg_preflight_required: fieldAcceptancePrimarySafetyAction?.route_wysiwyg_preflight_required ?? false,
    field_acceptance_primary_safety_confirm_ready_action_requires_safety_confirm: fieldAcceptancePacket.primary_safety_confirm_ready_action_requires_safety_confirm,
    field_acceptance_primary_safety_confirm_ready_action_sends_motion: fieldAcceptancePacket.primary_safety_confirm_ready_action_sends_motion,
    current_motion_action_required: fieldAcceptancePacket.primary_safety_confirm_ready_action_id !== "none",
    current_motion_action_id: fieldAcceptancePacket.primary_safety_confirm_ready_action_id,
    current_motion_action_label: fieldAcceptancePacket.primary_safety_confirm_ready_action_label,
    current_motion_action_display_label: fieldAcceptancePacket.primary_safety_confirm_ready_action_display_label,
    current_motion_action_start_endpoint: fieldAcceptancePacket.primary_safety_confirm_ready_action_start_endpoint,
    current_motion_action_stop_endpoint: fieldAcceptancePrimarySafetyAction?.stop_endpoint ?? "none",
    current_motion_action_acceptance_endpoints: fieldAcceptancePrimarySafetyAction?.acceptance_endpoints ?? [],
    current_motion_action_readback_endpoints: fieldAcceptancePrimarySafetyAction?.acceptance_endpoints ?? [],
    current_motion_action_required_success_markers: nav2RouteAcceptancePacket.required_success_markers,
    current_motion_action_proof_status: fieldAcceptanceNextStep?.proof_status ?? "blocked",
    current_motion_action_missing_evidence: fieldAcceptanceNextStep?.missing_evidence ?? [],
    current_motion_action_proof_plain: fieldAcceptanceNextStep?.proof_plain ?? "当前运动动作未加载。",
    current_motion_action_requires_safety_confirm: fieldAcceptancePacket.primary_safety_confirm_ready_action_requires_safety_confirm,
    current_motion_action_minimal_precheck_safety_only: fieldAcceptancePrimarySafetyAction?.minimal_precheck_safety_only ?? false,
    current_motion_action_camera_preflight_required: fieldAcceptancePrimarySafetyAction?.camera_preflight_required ?? false,
    current_motion_action_radar_preflight_required: fieldAcceptancePrimarySafetyAction?.radar_preflight_required ?? false,
    current_motion_action_route_wysiwyg_preflight_required: fieldAcceptancePrimarySafetyAction?.route_wysiwyg_preflight_required ?? false,
    current_motion_action_sends_motion: fieldAcceptancePacket.primary_safety_confirm_ready_action_sends_motion,
    current_motion_action_route_ready_on_map: nav2RouteAcceptancePacket.route_ready_on_map,
    current_motion_action_nav2_goal_succeeded: nav2RouteAcceptancePacket.nav2_goal_succeeded,
    current_motion_action_same_window_wheel_lr_nonzero: nav2RouteAcceptancePacket.same_window_wheel_lr_nonzero,
    current_motion_action_delivery_success: nav2RouteAcceptancePacket.delivery_success,
    current_motion_action_needs_same_window_wheel_rerun: nav2RouteAcceptancePacket.needs_same_window_wheel_rerun,
    current_motion_action_delivery_success_required: nav2RouteAcceptancePacket.delivery_success_required,
    current_motion_action_latest_raw_left: nav2RouteAcceptancePacket.latest_raw_left,
    current_motion_action_latest_raw_right: nav2RouteAcceptancePacket.latest_raw_right,
    current_motion_action_feedback_sample_count: nav2RouteAcceptancePacket.feedback_sample_count,
    current_motion_action_feedback_nonzero_sample_count: nav2RouteAcceptancePacket.feedback_nonzero_sample_count,
    current_motion_action_current_gap_plain: nav2RouteAcceptancePacket.current_gap_plain,
    current_motion_action_no_extra_precheck_plain: nav2RouteAcceptancePacket.no_extra_precheck_plain,
    current_motion_action_delivery_next_action_plain: nav2RouteAcceptancePacket.delivery_next_action_plain,
    current_keyboard_action_required: true,
    current_keyboard_action_ready: keyboardRunbookItem?.ready ?? liveClosureSummary.keyboard_continuous_ready,
    current_keyboard_action_id: keyboardRunbookItem?.id ?? "hold_keyboard",
    current_keyboard_action_label: keyboardRunbookItem?.label ?? "键盘连续手控",
    current_keyboard_action_display_label: keyboardRunbookItem?.display_label ?? "键盘连续手控",
    current_keyboard_action_start_endpoint: keyboardActionStartEndpoint,
    current_keyboard_action_stop_endpoint: keyboardActionStopEndpoint,
    current_keyboard_action_acceptance_endpoints: keyboardActionAcceptanceEndpoints,
    current_keyboard_action_readback_endpoints: keyboardActionAcceptanceEndpoints,
    current_keyboard_action_required_success_markers: keyboardActionRequiredSuccessMarkers,
    current_keyboard_action_proof_status: keyboardRunbookItem?.proof_status ?? "blocked",
    current_keyboard_action_missing_evidence: keyboardActionMissingEvidence,
    current_keyboard_action_proof_plain: keyboardRunbookItem?.proof_plain ?? "键盘连续手控未出现在当前 runbook。",
    current_keyboard_action_requires_safety_confirm: keyboardRunbookItem?.safety_confirm_required ?? liveClosureSummary.keyboard_continuous_safety_confirm_required,
    current_keyboard_action_minimal_precheck_safety_only: keyboardRunbookItem?.minimal_precheck_safety_only ?? liveClosureSummary.keyboard_continuous_minimal_precheck_safety_only,
    current_keyboard_action_enable_sends_motion: liveClosureSummary.keyboard_continuous_enable_sends_motion,
    current_keyboard_action_hold_to_move_required: liveClosureSummary.keyboard_continuous_hold_to_move_required,
    current_keyboard_action_hold_sends_motion: true,
    current_keyboard_action_pulse_interval_ms: liveClosureSummary.keyboard_continuous_pulse_interval_ms,
    current_keyboard_action_pulse_duration_ms: liveClosureSummary.keyboard_continuous_pulse_duration_ms,
    current_keyboard_action_stop_triggers: liveClosureSummary.keyboard_continuous_stop_triggers,
    current_keyboard_action_wheel_feedback_acceptance: liveClosureSummary.keyboard_continuous_wheel_feedback_acceptance,
    current_keyboard_action_post_hold_readback_endpoints: keyboardPostHoldReadbackEndpoints,
    current_keyboard_action_post_hold_readback_sequence_labels: ["复验键盘轮速采样", "刷新总览"],
    current_keyboard_action_post_hold_feedback_readback_required: liveClosureSummary.keyboard_continuous_post_hold_feedback_readback_required,
    current_keyboard_action_post_hold_summary_refresh_required: liveClosureSummary.keyboard_continuous_post_hold_summary_refresh_required,
    current_free_move_action_required: true,
    current_free_move_action_ready: freeMoveRunbookItem?.ready ?? liveClosureSummary.free_move_start_ready,
    current_free_move_action_id: freeMoveRunbookItem?.id ?? "start_free_move",
    current_free_move_action_label: freeMoveRunbookItem?.label ?? "自由自助移动",
    current_free_move_action_display_label: freeMoveRunbookItem?.display_label ?? "自由自助移动",
    current_free_move_action_start_endpoint: freeMoveActionStartEndpoint,
    current_free_move_action_stop_endpoint: freeMoveActionStopEndpoint,
    current_free_move_action_latest_endpoint: liveClosureSummary.fixed_free_roam_latest_endpoint,
    current_free_move_action_readback_endpoint: liveClosureSummary.fixed_free_roam_latest_endpoint,
    current_free_move_action_acceptance_endpoints: freeMoveActionAcceptanceEndpoints,
    current_free_move_action_readback_endpoints: freeMoveActionAcceptanceEndpoints,
    current_free_move_action_required_success_markers: freeMoveActionRequiredSuccessMarkers,
    current_free_move_action_proof_status: freeMoveRunbookItem?.proof_status ?? "blocked",
    current_free_move_action_missing_evidence: freeMoveActionMissingEvidence,
    current_free_move_action_proof_plain: freeMoveRunbookItem?.proof_plain ?? "自由自助移动未出现在当前 runbook。",
    current_free_move_action_requires_safety_confirm: freeMoveRunbookItem?.safety_confirm_required ?? true,
    current_free_move_action_minimal_precheck_safety_only: freeMoveRunbookItem?.minimal_precheck_safety_only ?? liveClosureSummary.free_move_minimal_precheck_safety_only,
    current_free_move_action_camera_preflight_required: liveClosureSummary.free_move_camera_preflight_required,
    current_free_move_action_radar_preflight_required: liveClosureSummary.free_move_radar_preflight_required,
    current_free_move_action_without_camera_allowed: liveClosureSummary.free_move_without_camera_allowed,
    current_free_move_action_without_radar_allowed: liveClosureSummary.free_roam_motion_without_radar_allowed,
    current_free_move_action_blocked_by_camera_wysiwyg: liveClosureSummary.free_move_blocked_by_camera_wysiwyg,
    current_free_move_action_blocked_by_radar_wysiwyg: liveClosureSummary.free_move_blocked_by_radar_wysiwyg,
    current_free_move_action_sends_motion: freeMoveRunbookItem?.sends_motion_when_executed ?? true,
    current_mapping_action_required: true,
    current_mapping_action_ready: mappingRunbookItem?.ready ?? liveClosureSummary.mapping_start_ready,
    current_mapping_action_id: mappingRunbookItem?.id ?? "start_mapping_when_sensors_ready",
    current_mapping_action_label: mappingRunbookItem?.label ?? "传感器就绪后建图",
    current_mapping_action_display_label: mappingRunbookItem?.display_label ?? "传感器就绪后建图",
    current_mapping_action_start_endpoint: mappingActionStartEndpoint,
    current_mapping_action_stop_endpoint: mappingActionStopEndpoint,
    current_mapping_action_preview_endpoint: liveClosureSummary.fixed_mapping_preview_endpoint,
    current_mapping_action_acceptance_endpoints: mappingActionAcceptanceEndpoints,
    current_mapping_action_readback_endpoints: mappingActionAcceptanceEndpoints,
    current_mapping_action_required_success_markers: mappingActionRequiredSuccessMarkers,
    current_mapping_action_proof_status: mappingRunbookItem?.proof_status ?? "blocked",
    current_mapping_action_missing_evidence: mappingActionMissingEvidence,
    current_mapping_action_proof_plain: mappingRunbookItem?.proof_plain ?? "传感器就绪后建图未出现在当前 runbook。",
    current_mapping_action_requires_safety_confirm: mappingRunbookItem?.safety_confirm_required ?? liveClosureSummary.mapping_start_ready,
    current_mapping_action_safety_confirm_required_when_executed: true,
    current_mapping_action_minimal_precheck_safety_only: mappingRunbookItem?.minimal_precheck_safety_only ?? true,
    current_mapping_action_camera_required: liveClosureSummary.mapping_start_requires_camera_first_frame,
    current_mapping_action_radar_required: liveClosureSummary.mapping_start_requires_lidar_fresh,
    current_mapping_action_camera_ready: !liveClosureSummary.mapping_camera_blocks_start,
    current_mapping_action_radar_ready: !liveClosureSummary.mapping_lidar_blocks_start,
    current_mapping_action_camera_blocks_start: liveClosureSummary.mapping_camera_blocks_start,
    current_mapping_action_radar_blocks_start: liveClosureSummary.mapping_lidar_blocks_start,
    current_mapping_action_only_camera_missing: mappingStartOnlyCameraMissing,
    current_mapping_action_radar_overlay_wysiwyg_complete: radarOverlayWysiwygComplete,
    current_mapping_action_camera_hardware_action_required: liveClosureSummary.camera_hardware_action_required,
    current_mapping_action_camera_hardware_action_label: liveClosureSummary.camera_hardware_action_label,
    current_mapping_action_camera_usb_full_speed_detected: liveClosureSummary.camera_usb_full_speed_detected,
    current_mapping_action_camera_usb_speed: liveClosureSummary.camera_usb_speed,
    current_mapping_action_camera_source_diagnosis_status: liveClosureSummary.camera_source_diagnosis_status,
    current_mapping_action_camera_source_diagnosis_not_exclusive: liveClosureSummary.camera_source_diagnosis_not_exclusive,
    current_mapping_action_camera_recovery_next_action_plain: liveClosureSummary.camera_recovery_next_action_plain,
    current_mapping_action_blocks_free_move: false,
    current_mapping_action_free_move_allowed_while_blocked: liveClosureSummary.free_move_start_ready && !liveClosureSummary.mapping_start_ready,
    current_mapping_action_sends_motion: mappingRunbookItem?.sends_motion_when_executed ?? true,
    current_mapping_action_starts_map_runtime_when_executed: true,
    current_mapping_action_starts_nav2: false,
    current_mapping_action_starts_keyboard: false,
    current_mapping_action_submits_delivery: false,
    field_acceptance_hardware_action_ids: fieldAcceptancePacket.hardware_action_ids,
    field_acceptance_hardware_action_labels: fieldAcceptancePacket.hardware_action_labels,
    field_acceptance_hardware_action_after_readback_endpoints: fieldAcceptancePacket.hardware_action_after_readback_endpoints,
    field_acceptance_hardware_action_after_readback_sequences: fieldAcceptancePacket.hardware_action_after_readback_sequences,
    field_acceptance_hardware_action_after_readback_sequence_labels: fieldAcceptancePacket.hardware_action_after_readback_sequence_labels,
    field_acceptance_hardware_actions: fieldAcceptancePacket.hardware_actions,
    field_acceptance_primary_hardware_action_id: fieldAcceptancePacket.primary_hardware_action_id,
    field_acceptance_primary_hardware_action_label: fieldAcceptancePacket.primary_hardware_action_label,
    field_acceptance_primary_hardware_action_after_readback_endpoint: fieldAcceptancePacket.primary_hardware_action_after_readback_endpoint,
    field_acceptance_primary_hardware_action_after_readback_sequence: fieldAcceptancePacket.primary_hardware_action_after_readback_sequence,
    field_acceptance_primary_hardware_action_after_readback_sequence_labels: fieldAcceptancePacket.primary_hardware_action_after_readback_sequence_labels,
    field_acceptance_primary_hardware_action_blocks_mapping_start: fieldAcceptancePacket.primary_hardware_action_blocks_mapping_start,
    field_acceptance_primary_hardware_action_blocks_free_move: fieldAcceptancePacket.primary_hardware_action_blocks_free_move,
    current_hardware_action_required: fieldAcceptancePacket.primary_hardware_action_id !== "none",
    current_hardware_action_id: fieldAcceptancePacket.primary_hardware_action_id,
    current_hardware_action_label: fieldAcceptancePacket.primary_hardware_action_label,
    current_hardware_action_plain: fieldAcceptancePacket.remaining_hardware_action_summary_plain,
    current_hardware_action_after_readback_endpoint: fieldAcceptancePacket.primary_hardware_action_after_readback_endpoint,
    current_hardware_action_after_readback_sequence: fieldAcceptancePacket.primary_hardware_action_after_readback_sequence,
    current_hardware_action_after_readback_sequence_labels: fieldAcceptancePacket.primary_hardware_action_after_readback_sequence_labels,
    current_hardware_action_blocks_mapping_start: fieldAcceptancePacket.primary_hardware_action_blocks_mapping_start,
    current_hardware_action_blocks_free_move: fieldAcceptancePacket.primary_hardware_action_blocks_free_move,
    current_hardware_action_sends_motion: false,
    field_acceptance_missing_evidence_ids: fieldAcceptancePacket.missing_evidence_ids,
    field_acceptance_missing_evidence_labels: fieldAcceptancePacket.missing_evidence_labels,
    field_acceptance_missing_evidence_items: fieldAcceptancePacket.missing_evidence_items,
    field_acceptance_primary_missing_id: fieldAcceptancePacket.primary_missing_evidence_id,
    field_acceptance_primary_missing_label: fieldAcceptancePacket.primary_missing_evidence_label,
    field_acceptance_primary_missing_action_id: fieldAcceptancePacket.primary_missing_evidence_action_id,
    field_acceptance_primary_missing_action_label: fieldAcceptancePacket.primary_missing_evidence_action_label,
    field_acceptance_primary_missing_action_display_label: fieldAcceptancePacket.primary_missing_evidence_action_display_label,
    field_acceptance_primary_missing_action_start_endpoint: fieldAcceptancePrimaryMissingEvidenceAction?.start_endpoint ?? "none",
    field_acceptance_primary_missing_action_stop_endpoint: fieldAcceptancePrimaryMissingEvidenceAction?.stop_endpoint ?? "none",
    field_acceptance_primary_missing_action_acceptance_endpoints: fieldAcceptancePrimaryMissingEvidenceAction?.acceptance_endpoints ?? [],
    field_acceptance_primary_missing_action_sends_motion: fieldAcceptancePrimaryMissingEvidenceAction?.sends_motion_when_executed ?? false,
    field_acceptance_primary_missing_action_requires_safety_confirm: fieldAcceptancePrimaryMissingEvidenceAction?.safety_confirm_required ?? false,
    field_acceptance_primary_missing_action_minimal_precheck_safety_only: fieldAcceptancePrimaryMissingEvidenceSafetyAction?.minimal_precheck_safety_only ?? false,
    field_acceptance_primary_missing_action_camera_preflight_required: fieldAcceptancePrimaryMissingEvidenceSafetyAction?.camera_preflight_required ?? false,
    field_acceptance_primary_missing_action_radar_preflight_required: fieldAcceptancePrimaryMissingEvidenceSafetyAction?.radar_preflight_required ?? false,
    field_acceptance_primary_missing_action_operator_report_preflight_required: fieldAcceptancePrimaryMissingEvidenceSafetyAction?.operator_report_preflight_required ?? false,
    field_acceptance_primary_missing_action_route_wysiwyg_preflight_required: fieldAcceptancePrimaryMissingEvidenceSafetyAction?.route_wysiwyg_preflight_required ?? false,
    field_acceptance_primary_readback_endpoint: fieldAcceptancePacket.primary_missing_evidence_readback_endpoint,
    field_acceptance_primary_readback_method: fieldAcceptancePacket.primary_missing_evidence_readback_method,
    field_acceptance_primary_requires_motion_before_readback: fieldAcceptancePacket.primary_missing_evidence_requires_motion_before_readback,
    field_acceptance_primary_requires_safety_confirm_before_motion: fieldAcceptancePacket.primary_missing_evidence_requires_safety_confirm_before_motion,
    field_acceptance_primary_blocks_field_acceptance: fieldAcceptancePacket.primary_missing_evidence_blocks_field_acceptance,
    field_acceptance_primary_missing_evidence_id: fieldAcceptancePacket.primary_missing_evidence_id,
    field_acceptance_primary_missing_evidence_label: fieldAcceptancePacket.primary_missing_evidence_label,
    field_acceptance_primary_missing_evidence_action_id: fieldAcceptancePacket.primary_missing_evidence_action_id,
    field_acceptance_primary_missing_evidence_action_label: fieldAcceptancePacket.primary_missing_evidence_action_label,
    field_acceptance_primary_missing_evidence_action_display_label: fieldAcceptancePacket.primary_missing_evidence_action_display_label,
    field_acceptance_primary_missing_evidence_readback_endpoint: fieldAcceptancePacket.primary_missing_evidence_readback_endpoint,
    field_acceptance_primary_missing_evidence_readback_method: fieldAcceptancePacket.primary_missing_evidence_readback_method,
    field_acceptance_primary_missing_evidence_requires_motion_before_readback: fieldAcceptancePacket.primary_missing_evidence_requires_motion_before_readback,
    field_acceptance_primary_missing_evidence_requires_safety_confirm_before_motion: fieldAcceptancePacket.primary_missing_evidence_requires_safety_confirm_before_motion,
    field_acceptance_primary_missing_evidence_blocks_field_acceptance: fieldAcceptancePacket.primary_missing_evidence_blocks_field_acceptance,
    field_acceptance_no_motion_readback_action_ids: fieldAcceptancePacket.no_motion_readback_action_ids,
    field_acceptance_no_motion_readback_action_labels: fieldAcceptancePacket.no_motion_readback_action_labels,
    field_acceptance_no_motion_readback_action_endpoints: fieldAcceptancePacket.no_motion_readback_action_endpoints,
    field_acceptance_no_motion_readback_action_methods: fieldAcceptancePacket.no_motion_readback_action_methods,
    field_acceptance_no_motion_readback_action_sequences: fieldAcceptancePacket.no_motion_readback_action_sequences,
    field_acceptance_no_motion_readback_action_sequence_labels: fieldAcceptancePacket.no_motion_readback_action_sequence_labels,
    field_acceptance_no_motion_readback_actions: fieldAcceptancePacket.no_motion_readback_actions,
    field_acceptance_primary_no_motion_readback_id: fieldAcceptancePacket.primary_no_motion_readback_action_id,
    field_acceptance_primary_no_motion_readback_label: fieldAcceptancePacket.primary_no_motion_readback_action_label,
    field_acceptance_primary_no_motion_readback_endpoint: fieldAcceptancePacket.primary_no_motion_readback_action_endpoint,
    field_acceptance_primary_no_motion_readback_method: fieldAcceptancePacket.primary_no_motion_readback_action_method,
    field_acceptance_primary_no_motion_readback_sequence: fieldAcceptancePacket.primary_no_motion_readback_action_sequence,
    field_acceptance_primary_no_motion_readback_sequence_labels: fieldAcceptancePacket.primary_no_motion_readback_action_sequence_labels,
    field_acceptance_primary_no_motion_readback_sends_motion: fieldAcceptancePacket.primary_no_motion_readback_action_sends_motion,
    field_acceptance_primary_no_motion_readback_action_id: fieldAcceptancePacket.primary_no_motion_readback_action_id,
    field_acceptance_primary_no_motion_readback_action_label: fieldAcceptancePacket.primary_no_motion_readback_action_label,
    field_acceptance_primary_no_motion_readback_action_endpoint: fieldAcceptancePacket.primary_no_motion_readback_action_endpoint,
    field_acceptance_primary_no_motion_readback_action_method: fieldAcceptancePacket.primary_no_motion_readback_action_method,
    field_acceptance_primary_no_motion_readback_action_sequence: fieldAcceptancePacket.primary_no_motion_readback_action_sequence,
    field_acceptance_primary_no_motion_readback_action_sequence_labels: fieldAcceptancePacket.primary_no_motion_readback_action_sequence_labels,
    field_acceptance_primary_no_motion_readback_action_refreshes_summary: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_summary,
    field_acceptance_primary_no_motion_readback_action_refreshes_radar_scan_proof: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_radar_scan_proof,
    field_acceptance_primary_no_motion_readback_action_refreshes_camera_first_frame_probe: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_camera_first_frame_probe,
    field_acceptance_primary_no_motion_readback_action_refreshes_map_preview: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_map_preview,
    field_acceptance_primary_no_motion_readback_action_refreshes_radar_status: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_radar_status,
    field_acceptance_primary_no_motion_readback_action_refreshes_camera_mjpeg_status: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_camera_mjpeg_status,
    field_acceptance_primary_no_motion_readback_action_sends_motion: fieldAcceptancePacket.primary_no_motion_readback_action_sends_motion,
    current_wysiwyg_action_required: fieldAcceptancePacket.primary_no_motion_readback_action_id !== "none",
    current_wysiwyg_action_id: fieldAcceptancePacket.primary_no_motion_readback_action_id,
    current_wysiwyg_action_label: fieldAcceptancePacket.primary_no_motion_readback_action_label,
    current_wysiwyg_action_endpoint: fieldAcceptancePacket.primary_no_motion_readback_action_endpoint,
    current_wysiwyg_action_method: fieldAcceptancePacket.primary_no_motion_readback_action_method,
    current_wysiwyg_action_sequence: fieldAcceptancePacket.primary_no_motion_readback_action_sequence,
    current_wysiwyg_action_sequence_labels: fieldAcceptancePacket.primary_no_motion_readback_action_sequence_labels,
    current_wysiwyg_action_refreshes_summary: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_summary,
    current_wysiwyg_action_refreshes_radar_scan_proof: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_radar_scan_proof,
    current_wysiwyg_action_refreshes_camera_first_frame_probe: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_camera_first_frame_probe,
    current_wysiwyg_action_refreshes_map_preview: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_map_preview,
    current_wysiwyg_action_refreshes_radar_status: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_radar_status,
    current_wysiwyg_action_refreshes_camera_mjpeg_status: fieldAcceptancePacket.primary_no_motion_readback_action_refreshes_camera_mjpeg_status,
    current_wysiwyg_action_sends_motion: fieldAcceptancePacket.primary_no_motion_readback_action_sends_motion,
    current_wysiwyg_action_starts_radar_lifecycle: fieldAcceptancePacket.wysiwyg_refresh_starts_radar_lifecycle,
    current_wysiwyg_action_starts_map_runtime: fieldAcceptancePacket.wysiwyg_refresh_starts_map_runtime,
    current_wysiwyg_action_starts_nav2: fieldAcceptancePacket.wysiwyg_refresh_starts_nav2,
    current_wysiwyg_action_starts_manual: fieldAcceptancePacket.wysiwyg_refresh_starts_manual,
    current_wysiwyg_action_starts_keyboard: fieldAcceptancePacket.wysiwyg_refresh_starts_keyboard,
    current_wysiwyg_action_starts_free_roam: fieldAcceptancePacket.wysiwyg_refresh_starts_free_roam,
    current_wysiwyg_action_submits_delivery: fieldAcceptancePacket.wysiwyg_refresh_submits_delivery,
    current_wysiwyg_action_stops_motion: fieldAcceptancePacket.wysiwyg_refresh_stops_motion,
    current_wysiwyg_action_missing_surface_ids: fieldAcceptancePacket.wysiwyg_missing_surface_ids,
    current_wysiwyg_action_refresh_mode: fieldAcceptancePacket.wysiwyg_refresh_mode,
    field_acceptance_remaining_operator_action_summary_plain: fieldAcceptancePacket.remaining_operator_action_summary_plain,
    field_acceptance_remaining_hardware_action_summary_plain: fieldAcceptancePacket.remaining_hardware_action_summary_plain,
    field_acceptance_remaining_no_motion_action_summary_plain: fieldAcceptancePacket.remaining_no_motion_action_summary_plain,
    field_acceptance_remaining_action_summary_plain: fieldAcceptancePacket.remaining_action_summary_plain,
    field_acceptance_acceptance_endpoints: fieldAcceptancePacket.acceptance_endpoints,
    field_acceptance_safety_confirm_required: fieldAcceptancePacket.safety_confirm_required,
    field_acceptance_minimal_precheck_safety_only: fieldAcceptancePacket.minimal_precheck_safety_only,
    field_acceptance_summary_plain: fieldAcceptancePacket.summary_plain,
    field_acceptance_wysiwyg_ready: fieldAcceptancePacket.wysiwyg_ready,
    field_acceptance_wysiwyg_missing_surface_ids: fieldAcceptancePacket.wysiwyg_missing_surface_ids,
    field_acceptance_wysiwyg_primary_refresh_endpoint: fieldAcceptancePacket.wysiwyg_primary_refresh_endpoint,
    field_acceptance_wysiwyg_primary_refresh_label: fieldAcceptancePacket.wysiwyg_primary_refresh_label,
    field_acceptance_wysiwyg_next_action_plain: fieldAcceptancePacket.wysiwyg_next_action_plain,
    field_acceptance_wysiwyg_camera_next_action_plain: fieldAcceptancePacket.wysiwyg_camera_next_action_plain,
    field_acceptance_wysiwyg_radar_map_next_action_plain: fieldAcceptancePacket.wysiwyg_radar_map_next_action_plain,
    field_acceptance_wysiwyg_refresh_sequence: fieldAcceptancePacket.wysiwyg_refresh_sequence,
    field_acceptance_wysiwyg_refresh_sequence_labels: fieldAcceptancePacket.wysiwyg_refresh_sequence_labels,
    field_acceptance_wysiwyg_refresh_mode: fieldAcceptanceWysiwygRefreshModeValue,
    field_acceptance_wysiwyg_refreshes_camera_first_frame_probe: fieldAcceptancePacket.wysiwyg_refreshes_camera_first_frame_probe,
    field_acceptance_wysiwyg_refreshes_camera_mjpeg_status: fieldAcceptancePacket.wysiwyg_refreshes_camera_mjpeg_status,
    field_acceptance_wysiwyg_refreshes_radar_scan_proof: fieldAcceptancePacket.wysiwyg_refreshes_radar_scan_proof,
    field_acceptance_wysiwyg_refreshes_radar_status: fieldAcceptancePacket.wysiwyg_refreshes_radar_status,
    field_acceptance_wysiwyg_refreshes_map_preview: fieldAcceptancePacket.wysiwyg_refreshes_map_preview,
    field_acceptance_wysiwyg_refresh_sends_motion: fieldAcceptancePacket.wysiwyg_refresh_sends_motion,
    field_acceptance_wysiwyg_refresh_starts_nav2: fieldAcceptancePacket.wysiwyg_refresh_starts_nav2,
    field_acceptance_wysiwyg_refresh_starts_manual: fieldAcceptancePacket.wysiwyg_refresh_starts_manual,
    field_acceptance_wysiwyg_refresh_starts_keyboard: fieldAcceptancePacket.wysiwyg_refresh_starts_keyboard,
    field_acceptance_wysiwyg_refresh_starts_free_roam: fieldAcceptancePacket.wysiwyg_refresh_starts_free_roam,
    field_acceptance_wysiwyg_refresh_starts_radar_lifecycle: fieldAcceptancePacket.wysiwyg_refresh_starts_radar_lifecycle,
    field_acceptance_wysiwyg_refresh_starts_map_runtime: fieldAcceptancePacket.wysiwyg_refresh_starts_map_runtime,
    field_acceptance_wysiwyg_refresh_submits_delivery: fieldAcceptancePacket.wysiwyg_refresh_submits_delivery,
    field_acceptance_wysiwyg_refresh_stops_motion: fieldAcceptancePacket.wysiwyg_refresh_stops_motion,
    field_acceptance_steps: fieldAcceptancePacket.steps,
    nav2_route_acceptance_packet: nav2RouteAcceptancePacket,
    primary_start_endpoint: primaryRunbookItem?.start_endpoint ?? "none",
    primary_stop_endpoint: primaryRunbookItem?.stop_endpoint ?? "none",
    primary_acceptance_endpoints: primaryRunbookItem?.acceptance_endpoints ?? [],
    primary_sends_motion: primaryRunbookItem?.sends_motion_when_executed ?? false,
    primary_requires_safety_confirm: primaryRunbookItem?.safety_confirm_required ?? false,
    primary_ready: primaryRunbookItem?.ready ?? false,
    primary_completed: primaryRunbookItem?.completed ?? false,
    primary_proof_status: primaryRunbookItem?.proof_status ?? "blocked",
    primary_missing_evidence: primaryRunbookItem?.missing_evidence ?? [],
    primary_proof_plain: primaryRunbookItem?.proof_plain ?? "当前没有主推荐动作。",
    trip_start_endpoint: runNav2RouteRunbookItem?.start_endpoint ?? liveClosureSummary.wheel_rerun_start_endpoint,
    trip_stop_endpoint: runNav2RouteRunbookItem?.stop_endpoint ?? "/api/robot-control/base/stop",
    trip_acceptance_endpoints: runNav2RouteRunbookItem?.acceptance_endpoints ?? liveClosureSummary.wheel_rerun_readback_endpoints,
    trip_ready: runNav2RouteRunbookItem?.ready ?? false,
    trip_completed: runNav2RouteRunbookItem?.completed ?? false,
    trip_proof_status: runNav2RouteRunbookItem?.proof_status ?? "blocked",
    trip_missing_evidence: runNav2RouteRunbookItem?.missing_evidence ?? [],
    trip_proof_plain: runNav2RouteRunbookItem?.proof_plain ?? "完整行程执行未出现在当前 runbook。",
    keyboard_start_endpoint: keyboardActionStartEndpoint,
    keyboard_acceptance_endpoints: keyboardActionAcceptanceEndpoints,
    keyboard_readback_endpoints: keyboardActionAcceptanceEndpoints,
    keyboard_required_success_markers: keyboardActionRequiredSuccessMarkers,
    keyboard_completed: keyboardRunbookItem?.completed ?? false,
    keyboard_proof_status: keyboardRunbookItem?.proof_status ?? "blocked",
    keyboard_missing_evidence: keyboardActionMissingEvidence,
    keyboard_proof_plain: keyboardRunbookItem?.proof_plain ?? "键盘连续手控未出现在当前 runbook。",
    free_move_start_endpoint: freeMoveActionStartEndpoint,
    free_move_stop_endpoint: freeMoveActionStopEndpoint,
    free_move_acceptance_endpoints: freeMoveActionAcceptanceEndpoints,
    free_move_readback_endpoint: liveClosureSummary.fixed_free_roam_latest_endpoint,
    free_move_latest_endpoint: liveClosureSummary.fixed_free_roam_latest_endpoint,
    free_move_readback_endpoints: freeMoveActionAcceptanceEndpoints,
    free_move_required_success_marker: freeMoveActionMissingEvidence[0] ?? "none",
    free_move_required_success_markers: freeMoveActionRequiredSuccessMarkers,
    free_move_proof_status: freeMoveRunbookItem?.proof_status ?? "blocked",
    free_move_missing_evidence: freeMoveActionMissingEvidence,
    free_move_proof_plain: freeMoveRunbookItem?.proof_plain ?? "自由自助移动未出现在当前 runbook。",
    free_roam_start_endpoint: freeMoveActionStartEndpoint,
    free_roam_stop_endpoint: freeMoveActionStopEndpoint,
    free_roam_latest_endpoint: liveClosureSummary.fixed_free_roam_latest_endpoint,
    free_roam_acceptance_endpoints: freeMoveActionAcceptanceEndpoints,
    free_roam_readback_endpoints: freeMoveActionAcceptanceEndpoints,
    free_roam_required_success_markers: freeMoveActionRequiredSuccessMarkers,
    free_roam_missing_evidence: freeMoveActionMissingEvidence,
    mapping_start_endpoint: mappingActionStartEndpoint,
    mapping_preview_endpoint: liveClosureSummary.fixed_mapping_preview_endpoint,
    mapping_acceptance_endpoints: mappingActionAcceptanceEndpoints,
    mapping_readback_endpoints: mappingActionAcceptanceEndpoints,
    mapping_required_success_markers: mappingActionRequiredSuccessMarkers,
    mapping_proof_status: mappingRunbookItem?.proof_status ?? "blocked",
    mapping_missing_evidence: mappingActionMissingEvidence,
    mapping_proof_plain: mappingRunbookItem?.proof_plain ?? "传感器就绪后建图未出现在当前 runbook。",
    camera_ready: liveClosureSummary.camera_current_visible,
    camera_first_frame_ready: liveClosureSummary.camera_current_visible,
    camera_visible: liveClosureSummary.camera_current_visible,
    camera_current_visible: liveClosureSummary.camera_current_visible,
    camera_needs_usb_fix: liveClosureSummary.camera_hardware_action_required,
    camera_usb_high_speed: cameraUsbHighSpeed,
    camera_usb_speed: liveClosureSummary.camera_usb_speed,
    map_visible: liveClosureSummary.map_current_visible,
    map_current_visible: liveClosureSummary.map_current_visible,
    path_visible: liveClosureSummary.path_current_visible,
    path_current_visible: liveClosureSummary.path_current_visible,
    live_wysiwyg_map_visible: liveClosureSummary.live_wysiwyg_map_visible,
    live_wysiwyg_camera_visible: liveClosureSummary.live_wysiwyg_camera_visible,
    camera_hardware_action_required: liveClosureSummary.camera_hardware_action_required,
    camera_hardware_action_label: liveClosureSummary.camera_hardware_action_label,
    camera_usb_full_speed_detected: liveClosureSummary.camera_usb_full_speed_detected,
    camera_blocks_mapping_start: liveClosureSummary.camera_blocks_mapping_start,
    camera_blocks_free_move: liveClosureSummary.camera_blocks_free_move,
    camera_reprobe_after_hardware_action_required: liveClosureSummary.camera_reprobe_after_hardware_action_required,
    camera_reprobe_sequence: liveClosureSummary.camera_reprobe_sequence,
    camera_reprobe_sequence_labels: liveClosureSummary.live_wysiwyg_camera_recovery_sequence_labels,
    camera_reprobe_sequence_sends_motion: liveClosureSummary.live_wysiwyg_camera_recovery_sends_motion,
    camera_hardware_action_next_action_plain: liveClosureSummary.live_wysiwyg_camera_recovery_next_action_plain,
    camera_source_diagnosis_status: liveClosureSummary.camera_source_diagnosis_status,
    camera_source_diagnosis_not_exclusive: liveClosureSummary.camera_source_diagnosis_not_exclusive,
    camera_source_diagnosis_plain_hint: liveClosureSummary.live_wysiwyg_camera_source_diagnosis_plain_hint,
    camera_source_diagnosis_next_action_plain:
      liveClosureSummary.live_wysiwyg_camera_source_diagnosis_next_action_plain === "not_loaded"
        ? liveClosureSummary.camera_recovery_next_action_plain
        : liveClosureSummary.live_wysiwyg_camera_source_diagnosis_next_action_plain,
    camera_recovery_next_action_plain: liveClosureSummary.camera_recovery_next_action_plain,
    camera_recovery_sends_motion: liveClosureSummary.camera_recovery_sends_motion,
    camera_recovery_starts_map_runtime: liveClosureSummary.camera_recovery_starts_map_runtime,
    fixed_camera_probe_endpoint: liveClosureSummary.fixed_camera_probe_endpoint,
    fixed_camera_mjpeg_status_endpoint: liveClosureSummary.fixed_camera_mjpeg_status_endpoint,
    live_wysiwyg_camera_source_diagnosis_status: liveClosureSummary.live_wysiwyg_camera_source_diagnosis_status,
    live_wysiwyg_camera_source_diagnosis_plain_hint: liveClosureSummary.live_wysiwyg_camera_source_diagnosis_plain_hint,
    live_wysiwyg_camera_source_diagnosis_next_action_plain:
      liveClosureSummary.live_wysiwyg_camera_source_diagnosis_next_action_plain,
    live_wysiwyg_camera_source_diagnosis_not_exclusive:
      liveClosureSummary.live_wysiwyg_camera_source_diagnosis_not_exclusive,
    live_wysiwyg_camera_shared_preview_client_count: liveClosureSummary.live_wysiwyg_camera_shared_preview_client_count,
    live_wysiwyg_camera_shared_preview_upstream_active: liveClosureSummary.live_wysiwyg_camera_shared_preview_upstream_active,
    live_wysiwyg_camera_shared_preview_exclusive_camera_claim: liveClosureSummary.live_wysiwyg_camera_shared_preview_exclusive_camera_claim,
    live_wysiwyg_camera_shared_preview_everyone_can_join: liveClosureSummary.live_wysiwyg_camera_shared_preview_everyone_can_join,
    live_wysiwyg_camera_shared_preview_current_frame_visible:
      liveClosureSummary.live_wysiwyg_camera_shared_preview_current_frame_visible,
    live_wysiwyg_camera_shared_preview_gap_plain: liveClosureSummary.live_wysiwyg_camera_shared_preview_gap_plain,
    camera_shared_preview_endpoint: "/api/robot-control/camera/mjpeg",
    camera_shared_preview_status_endpoint: liveClosureSummary.fixed_camera_mjpeg_status_endpoint,
    camera_shared_preview_single_upstream: true,
    camera_shared_preview_auto_joins: true,
    camera_shared_preview_everyone_can_join: liveClosureSummary.camera_shared_preview_everyone_can_join,
    camera_shared_preview_current_frame_visible: liveClosureSummary.camera_shared_preview_current_frame_visible,
    camera_shared_preview_gap_plain: liveClosureSummary.camera_shared_preview_gap_plain,
    camera_shared_preview_readback_only: true,
    camera_shared_preview_starts_camera_exclusive_capture: false,
    camera_shared_preview_sends_motion: false,
    camera_shared_preview_shared_capture: readbackSummary.camera.shared_preview_shared_capture,
    camera_shared_preview_exclusive_camera_claim: readbackSummary.camera.shared_preview_exclusive_camera_claim,
    camera_shared_preview_contract: readbackSummary.camera.shared_preview_contract,
    camera_shared_preview_multi_viewer_status: readbackSummary.camera.shared_preview_multi_viewer_status,
    camera_shared_preview_multi_viewer_plain: readbackSummary.camera.shared_preview_multi_viewer_plain,
    camera_shared_preview_access_plain: readbackSummary.camera.shared_preview_access_plain,
    camera_shared_preview_realtime_plain: readbackSummary.camera.shared_preview_realtime_plain,
    camera_wysiwyg_recovery_status: liveClosureSummary.live_wysiwyg_camera_recovery_status,
    camera_wysiwyg_recovery_next_action_plain: liveClosureSummary.live_wysiwyg_camera_recovery_next_action_plain,
    camera_wysiwyg_recovery_sequence: liveClosureSummary.live_wysiwyg_camera_recovery_sequence,
    camera_wysiwyg_recovery_sequence_labels: liveClosureSummary.live_wysiwyg_camera_recovery_sequence_labels,
    live_wysiwyg_camera_recovery_status: liveClosureSummary.live_wysiwyg_camera_recovery_status,
    live_wysiwyg_camera_recovery_next_action_plain: liveClosureSummary.live_wysiwyg_camera_recovery_next_action_plain,
    live_wysiwyg_camera_recovery_sequence: liveClosureSummary.live_wysiwyg_camera_recovery_sequence,
    live_wysiwyg_camera_recovery_sequence_labels: liveClosureSummary.live_wysiwyg_camera_recovery_sequence_labels,
    live_wysiwyg_camera_recovery_sends_motion: liveClosureSummary.live_wysiwyg_camera_recovery_sends_motion,
    camera_wysiwyg_recovery_readback_endpoint: liveClosureSummary.fixed_camera_probe_endpoint,
    camera_wysiwyg_recovery_probe_endpoint: liveClosureSummary.fixed_camera_probe_endpoint,
    camera_wysiwyg_recovery_status_endpoint: liveClosureSummary.fixed_camera_mjpeg_status_endpoint,
    camera_wysiwyg_recovery_summary_endpoint: liveClosureSummary.fixed_objective_audit_summary_endpoint,
    camera_wysiwyg_recovery_readback_endpoints: liveClosureSummary.live_wysiwyg_camera_recovery_sequence,
    camera_wysiwyg_recovery_readback_sequence_labels: liveClosureSummary.live_wysiwyg_camera_recovery_sequence_labels,
    camera_wysiwyg_recovery_requires_hardware_action: liveClosureSummary.camera_hardware_action_required,
    camera_wysiwyg_recovery_hardware_action_label: liveClosureSummary.camera_hardware_action_label,
    camera_wysiwyg_recovery_requires_usb_fix: liveClosureSummary.camera_hardware_action_required,
    camera_wysiwyg_recovery_blocks_mapping_start: liveClosureSummary.camera_blocks_mapping_start,
    camera_wysiwyg_recovery_blocks_free_move: liveClosureSummary.camera_blocks_free_move,
    camera_wysiwyg_recovery_sends_motion: liveClosureSummary.camera_recovery_sends_motion,
    camera_wysiwyg_recovery_starts_map_runtime: liveClosureSummary.camera_recovery_starts_map_runtime,
    camera_wysiwyg_recovery_source_diagnosis_status: liveClosureSummary.camera_source_diagnosis_status,
    camera_wysiwyg_recovery_source_not_exclusive: liveClosureSummary.camera_source_diagnosis_not_exclusive,
    camera_wysiwyg_recovery_shared_preview_single_upstream: true,
    mapping_unblock_camera_recovery_next_action_plain: liveClosureSummary.mapping_unblock_camera_recovery_next_action_plain,
    mapping_unblock_camera_recovery_sequence: liveClosureSummary.mapping_unblock_camera_recovery_sequence,
    mapping_unblock_camera_recovery_sequence_labels: liveClosureSummary.mapping_unblock_camera_recovery_sequence_labels,
    mapping_unblock_camera_recovery_sends_motion: liveClosureSummary.mapping_unblock_camera_recovery_sends_motion,
    fixed_mapping_unblock_camera_probe_endpoint: liveClosureSummary.fixed_mapping_unblock_camera_probe_endpoint,
    fixed_mapping_unblock_camera_mjpeg_status_endpoint: liveClosureSummary.fixed_mapping_unblock_camera_mjpeg_status_endpoint,
    fixed_mapping_unblock_summary_endpoint: liveClosureSummary.fixed_mapping_unblock_summary_endpoint,
    radar_visible: liveClosureSummary.radar_map_points_visible,
    radar_points_visible: liveClosureSummary.radar_map_points_visible,
    radar_ready: liveClosureSummary.mapping_lidar_fresh_readback_ready,
    radar_fresh: liveClosureSummary.mapping_lidar_fresh_readback_ready,
    radar_map_ready: liveClosureSummary.radar_map_points_visible,
    radar_map_points_visible: liveClosureSummary.radar_map_points_visible,
    live_wysiwyg_radar_map_overlay_status: liveClosureSummary.live_wysiwyg_radar_map_overlay_status,
    live_wysiwyg_radar_map_current_point_count: liveClosureSummary.live_wysiwyg_radar_map_current_point_count,
    live_wysiwyg_radar_map_source_point_count: liveClosureSummary.live_wysiwyg_radar_map_source_point_count,
    live_wysiwyg_radar_map_stale_source_points_suppressed: liveClosureSummary.live_wysiwyg_radar_map_stale_source_points_suppressed,
    live_wysiwyg_radar_map_primary_blocked_reason: liveClosureSummary.live_wysiwyg_radar_map_primary_blocked_reason,
    live_wysiwyg_radar_map_current_vs_source_plain: liveClosureSummary.live_wysiwyg_radar_map_current_vs_source_plain,
    live_wysiwyg_radar_map_refresh_next_action_plain: liveClosureSummary.live_wysiwyg_radar_map_refresh_next_action_plain,
    live_wysiwyg_radar_map_refresh_sequence: liveClosureSummary.live_wysiwyg_radar_map_refresh_sequence,
    live_wysiwyg_radar_map_refresh_sequence_labels: liveClosureSummary.live_wysiwyg_radar_map_refresh_sequence_labels,
    radar_overlay_status: liveClosureSummary.radar_overlay_status,
    radar_overlay_current_point_count: liveClosureSummary.radar_overlay_current_point_count,
    radar_overlay_source_point_count: liveClosureSummary.radar_overlay_source_point_count,
    radar_overlay_primary_blocked_reason: liveClosureSummary.radar_overlay_primary_blocked_reason,
    radar_overlay_current_vs_source_plain: liveClosureSummary.radar_overlay_current_vs_source_plain,
    radar_overlay_refresh_next_action_plain: liveClosureSummary.radar_overlay_refresh_next_action_plain,
    radar_overlay_needs_refresh: liveClosureSummary.radar_overlay_needs_refresh,
    radar_overlay_blocks_wysiwyg: liveClosureSummary.radar_overlay_blocks_wysiwyg,
    radar_overlay_blocks_free_move: liveClosureSummary.radar_overlay_blocks_free_move,
    radar_overlay_wysiwyg_complete: radarOverlayWysiwygComplete,
    radar_overlay_readback_endpoint: liveClosureSummary.fixed_radar_overlay_refresh_endpoint,
    radar_overlay_refresh_endpoint: liveClosureSummary.fixed_radar_overlay_refresh_endpoint,
    radar_overlay_status_endpoint: liveClosureSummary.fixed_live_wysiwyg_radar_status_endpoint,
    radar_overlay_preview_endpoint: liveClosureSummary.fixed_radar_overlay_map_preview_endpoint,
    radar_overlay_summary_endpoint: liveClosureSummary.fixed_objective_audit_summary_endpoint,
    radar_overlay_recovery_sequence: liveClosureSummary.radar_overlay_recovery_sequence,
    fixed_radar_overlay_refresh_endpoint: liveClosureSummary.fixed_radar_overlay_refresh_endpoint,
    fixed_radar_overlay_map_preview_endpoint: liveClosureSummary.fixed_radar_overlay_map_preview_endpoint,
    radar_overlay_refresh_sends_motion: liveClosureSummary.radar_overlay_refresh_sends_motion,
    radar_overlay_refresh_starts_radar_lifecycle: liveClosureSummary.radar_overlay_refresh_starts_radar_lifecycle,
    keyboard_ready: liveClosureSummary.keyboard_ready,
    keyboard_continuous_ready: liveClosureSummary.keyboard_continuous_ready,
    keyboard_wheel_lr_nonzero: liveClosureSummary.keyboard_continuous_motion_verified,
    keyboard_stop_after_release: keyboardStopAfterRelease,
    keyboard_continuous_motion_verified: liveClosureSummary.keyboard_continuous_motion_verified,
    keyboard_continuous_minimal_precheck_safety_only: liveClosureSummary.keyboard_continuous_minimal_precheck_safety_only,
    keyboard_continuous_safety_confirm_required: liveClosureSummary.keyboard_continuous_safety_confirm_required,
    keyboard_continuous_enable_sends_motion: liveClosureSummary.keyboard_continuous_enable_sends_motion,
    keyboard_continuous_hold_to_move_required: liveClosureSummary.keyboard_continuous_hold_to_move_required,
    keyboard_continuous_pulse_interval_ms: liveClosureSummary.keyboard_continuous_pulse_interval_ms,
    keyboard_continuous_pulse_duration_ms: liveClosureSummary.keyboard_continuous_pulse_duration_ms,
    keyboard_continuous_stop_triggers: liveClosureSummary.keyboard_continuous_stop_triggers,
    keyboard_continuous_wheel_feedback_acceptance: liveClosureSummary.keyboard_continuous_wheel_feedback_acceptance,
    keyboard_safety_confirm_required: liveClosureSummary.keyboard_safety_confirm_required,
    keyboard_enable_sends_motion: liveClosureSummary.keyboard_enable_sends_motion,
    keyboard_hold_to_move_required: liveClosureSummary.keyboard_hold_to_move_required,
    keyboard_pulse_interval_ms: liveClosureSummary.keyboard_pulse_interval_ms,
    keyboard_pulse_duration_ms: liveClosureSummary.keyboard_pulse_duration_ms,
    keyboard_stop_triggers: liveClosureSummary.keyboard_stop_triggers,
    keyboard_acceptance_plain: liveClosureSummary.keyboard_acceptance_plain,
    keyboard_manual_endpoint: liveClosureSummary.keyboard_manual_endpoint,
    keyboard_stop_endpoint: liveClosureSummary.keyboard_stop_endpoint,
    keyboard_feedback_readback_endpoint: liveClosureSummary.keyboard_feedback_readback_endpoint,
    keyboard_summary_endpoint: liveClosureSummary.keyboard_summary_endpoint,
    fixed_keyboard_manual_endpoint: liveClosureSummary.fixed_keyboard_manual_endpoint,
    fixed_keyboard_stop_endpoint: liveClosureSummary.fixed_keyboard_stop_endpoint,
    fixed_keyboard_feedback_readback_endpoint: liveClosureSummary.fixed_keyboard_feedback_readback_endpoint,
    fixed_keyboard_summary_endpoint: liveClosureSummary.fixed_keyboard_summary_endpoint,
    keyboard_post_hold_readback_endpoints: keyboardPostHoldReadbackEndpoints,
    keyboard_post_hold_readback_sequence_labels: ["复验键盘轮速采样", "刷新总览"],
    keyboard_post_hold_feedback_readback_required: liveClosureSummary.keyboard_continuous_post_hold_feedback_readback_required,
    keyboard_post_hold_summary_refresh_required: liveClosureSummary.keyboard_continuous_post_hold_summary_refresh_required,
    keyboard_continuous_post_hold_feedback_readback_required: liveClosureSummary.keyboard_continuous_post_hold_feedback_readback_required,
    keyboard_continuous_post_hold_summary_refresh_required: liveClosureSummary.keyboard_continuous_post_hold_summary_refresh_required,
    free_move_start_ready: liveClosureSummary.free_move_start_ready,
    free_move_ready: liveClosureSummary.free_move_start_ready,
    free_move_running: liveClosureSummary.free_roam_motion_ready,
    free_move_complete: freeMoveComplete,
    free_roam_start_ready: liveClosureSummary.free_roam_start_ready,
    free_roam_ready: liveClosureSummary.free_roam_ready,
    free_roam_motion_start_ready: liveClosureSummary.free_roam_motion_start_ready,
    free_roam_motion_ready: liveClosureSummary.free_roam_motion_ready,
    free_move_minimal_precheck_safety_only: liveClosureSummary.free_move_minimal_precheck_safety_only,
    free_move_safety_confirm_required: liveClosureSummary.free_move_safety_confirm_required,
    free_move_camera_preflight_required: liveClosureSummary.free_move_camera_preflight_required,
    free_move_radar_preflight_required: liveClosureSummary.free_move_radar_preflight_required,
    free_move_without_camera_allowed: liveClosureSummary.free_move_without_camera_allowed,
    free_roam_motion_without_radar_allowed: liveClosureSummary.free_roam_motion_without_radar_allowed,
    free_move_blocked_by_camera_wysiwyg: liveClosureSummary.free_move_blocked_by_camera_wysiwyg,
    free_move_blocked_by_radar_wysiwyg: liveClosureSummary.free_move_blocked_by_radar_wysiwyg,
    fixed_free_roam_start_endpoint: liveClosureSummary.fixed_free_roam_start_endpoint,
    fixed_free_roam_stop_endpoint: liveClosureSummary.fixed_free_roam_stop_endpoint,
    fixed_free_roam_latest_endpoint: liveClosureSummary.fixed_free_roam_latest_endpoint,
    mapping_start_ready: liveClosureSummary.mapping_start_ready,
    mapping_start_missing_reasons: liveClosureSummary.mapping_start_missing_reasons,
    mapping_start_missing_evidence: liveClosureSummary.mapping_start_missing_reasons,
    mapping_start_only_camera_missing: mappingStartOnlyCameraMissing,
    mapping_acceptance_ready: liveClosureSummary.free_roam_mapping_ready,
    mapping_acceptance_missing_reasons: liveClosureSummary.mapping_acceptance_missing_reasons,
    mapping_start_requires_camera_first_frame: liveClosureSummary.mapping_start_requires_camera_first_frame,
    mapping_start_requires_lidar_fresh: liveClosureSummary.mapping_start_requires_lidar_fresh,
    mapping_start_unblock_plain: liveClosureSummary.mapping_start_unblock_plain,
    mapping_camera_blocks_start: liveClosureSummary.mapping_camera_blocks_start,
    mapping_lidar_blocks_start: liveClosureSummary.mapping_lidar_blocks_start,
    mapping_lidar_fresh_readback_ready: liveClosureSummary.mapping_lidar_fresh_readback_ready,
    mapping_lidar_fresh_gate_conflict: liveClosureSummary.mapping_lidar_fresh_gate_conflict,
    mapping_lidar_fresh_gate_status: liveClosureSummary.mapping_lidar_fresh_gate_status,
    mapping_lidar_fresh_next_action_plain: liveClosureSummary.mapping_lidar_fresh_next_action_plain,
    mapping_lidar_fresh_refresh_sequence: liveClosureSummary.mapping_lidar_fresh_refresh_sequence,
    mapping_lidar_fresh_refresh_sequence_labels: liveClosureSummary.mapping_lidar_fresh_refresh_sequence_labels,
    mapping_lidar_fresh_refresh_sends_motion: liveClosureSummary.mapping_lidar_fresh_refresh_sends_motion,
    mapping_lidar_fresh_refresh_starts_radar_lifecycle: liveClosureSummary.mapping_lidar_fresh_refresh_starts_radar_lifecycle,
    mapping_lidar_fresh_blocks_free_move: liveClosureSummary.mapping_lidar_fresh_blocks_free_move,
    mapping_unblock_allows_free_move: liveClosureSummary.mapping_unblock_allows_free_move,
    fixed_mapping_start_endpoint: liveClosureSummary.fixed_mapping_start_endpoint,
    fixed_mapping_preview_endpoint: liveClosureSummary.fixed_mapping_preview_endpoint,
    free_roam_mapping_start_ready: liveClosureSummary.free_roam_mapping_start_ready,
    free_roam_mapping_start_missing_reasons: liveClosureSummary.free_roam_mapping_start_missing_reasons,
    free_roam_mapping_ready: liveClosureSummary.free_roam_mapping_ready,
    free_roam_mapping_missing_reasons: liveClosureSummary.free_roam_mapping_missing_reasons,
    camera_summary: readbackSummary.camera,
    map_summary: readbackSummary.map,
    radar_summary: readbackSummary.radar,
    nav2_summary: nav2Summary,
    keyboard_summary: readbackSummary.keyboard,
    keyboard_control_summary: readbackSummary.keyboard_control,
    keyboard_teleop_summary: readbackSummary.keyboard_teleop,
    free_roam_summary: readbackSummary.free_roam,
    readback_summary: readbackSummary,
    operator_hil_material_summary: operatorHilMaterialSummary,
    first_jog_readiness_summary: buildFirstJogReadinessSummary(operatorHilMaterialSummary),
    safe_command_boundary: safeCommandBoundary,
    blocked_reasons: connectionBlockedReasons.length ? connectionBlockedReasons : ["dangerous actions locked by V1 boundary"],
    not_proven: ["O7", "path_generated", "delivery_success", "safe_to_control_true", "real_robot_ack"],
    ...PROOF_FLAGS,
  };
}
