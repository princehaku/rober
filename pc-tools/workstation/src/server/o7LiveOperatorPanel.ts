import { PROOF_FLAGS } from "../shared/contracts";
import type { O7LiveOperatorPanelResponse } from "../shared/contracts";

const ENDPOINT = "/api/o7/live-operator-panel" as const;
const DEFAULT_UPPER_API_BASE_URL = "http://192.168.1.11:8787";
const REQUEST_TIMEOUT_MS = 1200;

const BLOCKED_REASONS = [
  "base_serial_identity_not_proven",
  "t1001_feedback_not_observed",
  "robot_ack_not_connected",
] as const;

const DEFAULT_SCAN_PROOF_BLOCKERS = ["radar_scan_proof_latest_not_loaded"] as const;
const LOADED_SCAN_PROOF_NOT_OBSERVED_BLOCKERS = ["radar_scan_proof_blocked_or_not_observed"] as const;

type O7LiveOperatorPanelWithBaseBoundary = O7LiveOperatorPanelResponse & {
  control: O7LiveOperatorPanelResponse["control"] & {
    base_boundary: {
      observed_write_device: "/dev/ttyS5";
      baudrate: 115200;
      vendor_command_id: "T=1";
      feedback_request_id: "T=130";
      required_feedback_id: "T=1001";
      t1001_feedback_status: "not_observed_after_t130";
      manual_control_status: "fail_closed_display_only";
      forbidden_endpoint: "/api/base/manual";
      post_base_manual_enabled: false;
    };
  };
};

type UpperStatus = {
  camera?: Record<string, unknown>;
  radar?: Record<string, unknown>;
  base?: Record<string, unknown>;
  map?: Record<string, unknown>;
  slam?: Record<string, unknown>;
};

async function fetchUpperStatus(env: NodeJS.ProcessEnv = process.env): Promise<UpperStatus | null> {
  const baseUrl = (env.ROBER_UPPER_API_BASE_URL || DEFAULT_UPPER_API_BASE_URL).replace(/\/+$/, "");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${baseUrl}/api/status`, { signal: controller.signal });
    if (!response.ok) {
      return null;
    }
    const payload = await response.json();
    return payload && typeof payload === "object" ? (payload as UpperStatus) : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

function stringField(record: Record<string, unknown> | undefined, key: string, fallback: string): string {
  const value = record?.[key];
  return typeof value === "string" ? value : fallback;
}

function numberField(record: Record<string, unknown> | undefined, key: string, fallback: number): number {
  const value = record?.[key];
  return typeof value === "number" ? value : fallback;
}

function nullableNumberField(record: Record<string, unknown> | undefined, key: string): number | null {
  const value = record?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function boolField(record: Record<string, unknown> | undefined, key: string, fallback: boolean): boolean {
  const value = record?.[key];
  return typeof value === "boolean" ? value : fallback;
}

function readyStatusField(record: Record<string, unknown> | undefined, key: string): boolean {
  const value = record?.[key];
  return typeof value === "string" && ["ready", "loaded", "observed", "available", "proven"].includes(value);
}

function nestedRecord(record: Record<string, unknown> | undefined, key: string): Record<string, unknown> | undefined {
  const value = record?.[key];
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : undefined;
}

function stringArrayField(record: Record<string, unknown> | undefined, key: string, fallback: readonly string[]): string[] {
  const value = record?.[key];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [...fallback];
}

function scanProofBlockers(scanProofLatest: Record<string, unknown> | undefined): string[] {
  const directBlockers = stringArrayField(scanProofLatest, "blockers", []);
  const blockedReasons = stringArrayField(scanProofLatest, "blocked_reasons", []);
  const artifact = nestedRecord(scanProofLatest, "artifact");
  const artifactBlockers = stringArrayField(artifact, "blockers", []);
  const blockers = [...directBlockers, ...blockedReasons, ...artifactBlockers];
  if (blockers.length) {
    return [...new Set(blockers)];
  }

  const artifactStatus = stringField(artifact, "status", stringField(scanProofLatest, "artifact_status", "not_loaded"));
  const latestProofStatus = stringField(scanProofLatest, "latest_proof_status", "not_loaded");
  if (artifactStatus === "loaded" && latestProofStatus === "blocked_or_not_observed") {
    // artifact 已加载但远端摘要没有 blocker 明细时，不能误报成 proof 未加载。
    return [...LOADED_SCAN_PROOF_NOT_OBSERVED_BLOCKERS];
  }

  // 机器可读 blocker 可能随 artifact schema 演进；只有 artifact 缺失/未加载时才显示未加载。
  return [...DEFAULT_SCAN_PROOF_BLOCKERS];
}

export async function buildO7LiveOperatorPanel(): Promise<O7LiveOperatorPanelResponse> {
  const upperStatus = await fetchUpperStatus();
  const upperCamera = upperStatus?.camera;
  const upperRadar = upperStatus?.radar;
  const upperBase = upperStatus?.base;
  const upperMap = upperStatus?.map;
  const upperSlam = upperStatus?.slam;
  const observedLidarPort = stringField(upperRadar, "observed_lidar_port", "");
  const scanProofLatest = nestedRecord(upperRadar, "scan_proof_latest");
  const scanProofArtifact = nestedRecord(scanProofLatest, "artifact");
  const scanProofFreshness = nestedRecord(scanProofLatest, "freshness");
  const scanProofStatus = stringField(scanProofLatest, "latest_proof_status", "not_loaded");
  const latestScanOnceObserved = boolField(scanProofLatest, "latest_scan_once_observed", boolField(scanProofLatest, "scan_once_observed", false));
  const latestScanHzObserved = boolField(scanProofLatest, "latest_scan_hz_observed", boolField(scanProofLatest, "scan_hz_observed", false));
  const scanProofBlockerList = scanProofBlockers(scanProofLatest);
  const rawPacketProofLatest = nestedRecord(upperRadar, "raw_packet_proof_latest");
  const rawPacketProofArtifact = nestedRecord(rawPacketProofLatest, "artifact");
  const rawPacketProofFreshness = nestedRecord(rawPacketProofLatest, "freshness");
  const rawPacketProofStatus = stringField(rawPacketProofLatest, "latest_proof_status", "not_loaded");
  const basePort = stringField(upperBase, "port", "/dev/ttyS5");
  const baseBaudrate = numberField(upperBase, "baudrate", 115200);
  const realtimeRadarReady = latestScanOnceObserved && latestScanHzObserved;
  const realtimeRadarBlockers = realtimeRadarReady
    ? []
    : [
        ...scanProofBlockerList,
        ...(latestScanOnceObserved ? [] : ["scan_once_not_observed"]),
        ...(latestScanHzObserved ? [] : ["scan_hz_not_observed"]),
      ];
  const mapArtifact = nestedRecord(upperMap, "artifact") ?? nestedRecord(upperMap, "map_artifact");
  const slamArtifact = nestedRecord(upperSlam, "artifact") ?? nestedRecord(upperSlam, "slam_artifact");
  const mapArtifactStatus = stringField(mapArtifact, "status", stringField(upperMap, "artifact_status", "not_loaded"));
  const slamArtifactStatus = stringField(slamArtifact, "status", stringField(upperSlam, "artifact_status", "not_loaded"));
  const latestMapObserved =
    boolField(upperMap, "latest_map_observed", boolField(upperMap, "map_artifact_observed", false)) ||
    readyStatusField(upperMap, "status") ||
    readyStatusField(upperMap, "latest_map_status") ||
    readyStatusField(mapArtifact, "status");
  const latestSlamObserved =
    boolField(upperSlam, "latest_slam_observed", boolField(upperSlam, "slam_artifact_observed", false)) ||
    readyStatusField(upperSlam, "status") ||
    readyStatusField(upperSlam, "latest_slam_status") ||
    readyStatusField(slamArtifact, "status");
  const realtimeMapReady = realtimeRadarReady && (latestMapObserved || latestSlamObserved);
  const realtimeMapStatus = realtimeMapReady ? "ready" : realtimeRadarReady ? "waiting_for_mapping" : "waiting_for_radar";
  const realtimeMapBlockers =
    realtimeMapStatus === "waiting_for_radar" ? ["realtime_radar_not_ready"] : realtimeMapStatus === "waiting_for_mapping" ? ["slam_map_artifact_not_observed"] : [];
  // 这个面板只把已观测事实产品化展示，不探测串口、不请求 /offer、不发送任何底盘控制。
  const response: O7LiveOperatorPanelWithBaseBoundary = {
    schema: "trashbot.o7.live_operator_panel.v1",
    endpoint: ENDPOINT,
    ...PROOF_FLAGS,
    ssh: {
      // SSH 可达来自本轮只读联调口径；8787 状态只读消费统一 API，不影响控制锁。
      host: "192.168.1.11",
      port: 37878,
      reachable: true,
      workstation_api_8787_status: upperStatus ? "ready" : "not_listening_observed",
    },
    lidar_radar: {
      // 雷达已按 /dev/ttyACM0 归位，但 /scan 未采样前不能伪造点云或建图状态。
      dev_lidar: observedLidarPort || "missing",
      stc_by_id: observedLidarPort === "/dev/ttyACM0" ? "resolved_to_ttyACM0" : "unresolved",
      scan_status: "not_proven",
      scan_proof_latest: {
        // 只消费 8787 统一 status 内的 readback 摘要；PC 不执行 collector、不启动 ROS2、不打开串口。
        endpoint: "/api/radar/scan-proof/latest",
        artifact_status: stringField(scanProofArtifact, "status", stringField(scanProofLatest, "artifact_status", "not_loaded")),
        freshness_status: stringField(scanProofFreshness, "status", stringField(scanProofLatest, "freshness_status", "unknown")),
        age_seconds: nullableNumberField(scanProofFreshness, "age_seconds") ?? nullableNumberField(scanProofLatest, "age_seconds"),
        latest_proof_status: scanProofStatus,
        latest_scan_once_observed: latestScanOnceObserved,
        latest_scan_hz_observed: latestScanHzObserved,
        latest_raw_packet_once_observed: boolField(scanProofLatest, "latest_raw_packet_once_observed", false),
        blocked_reasons: scanProofBlockerList,
        readback_sends_commands: false,
        collector_executed_by_pc: false,
      },
      raw_packet_proof_latest: {
        // raw packet proof 是 8787 只读摘要；PC 只展示 raw bytes/packet/point 证据，不采集、不发启动字节。
        endpoint: "/api/radar/raw-packet-proof/latest",
        http_status: nullableNumberField(rawPacketProofLatest, "http_status"),
        artifact_status: stringField(rawPacketProofArtifact, "status", stringField(rawPacketProofLatest, "artifact_status", "not_loaded")),
        freshness_status: stringField(rawPacketProofFreshness, "status", stringField(rawPacketProofLatest, "freshness_status", "unknown")),
        age_seconds: nullableNumberField(rawPacketProofFreshness, "age_seconds") ?? nullableNumberField(rawPacketProofLatest, "age_seconds"),
        latest_proof_status: rawPacketProofStatus,
        latest_raw_bytes_observed: boolField(rawPacketProofLatest, "latest_raw_bytes_observed", false),
        latest_sync_header_observed: boolField(rawPacketProofLatest, "latest_sync_header_observed", false),
        latest_packet_parse_ok: boolField(rawPacketProofLatest, "latest_packet_parse_ok", false),
        latest_points_observed: boolField(rawPacketProofLatest, "latest_points_observed", false),
        latest_bytes_read: nullableNumberField(rawPacketProofLatest, "latest_bytes_read"),
        latest_sync_header_count: nullableNumberField(rawPacketProofLatest, "latest_sync_header_count"),
        latest_packets_parse_ok: nullableNumberField(rawPacketProofLatest, "latest_packets_parse_ok"),
        latest_points_total: nullableNumberField(rawPacketProofLatest, "latest_points_total"),
        sends_commands: false,
        sends_motion_commands: false,
        robot_control_executed: false,
        safe_to_control: false,
        hil_pass: false,
        collector_executed_by_pc: false,
      },
      pointcloud_fabricated: false,
      source_facts: [
        observedLidarPort
          ? `${observedLidarPort} is reported by upper robot API as the LiDAR serial device`
          : "upper robot API did not report an observed LiDAR serial device",
        `${numberField(upperRadar, "baudrate", 150000)} baud, start ${stringField(upperRadar, "start_command_hex", "a5 60")}, stop ${stringField(upperRadar, "stop_command_hex", "a5 00 a5 65 a5 65")}`,
        `latest scan proof artifact ${stringField(scanProofArtifact, "status", "not_loaded")} / ${scanProofStatus}`,
        `latest raw packet proof artifact ${stringField(rawPacketProofArtifact, "status", "not_loaded")} / ${rawPacketProofStatus}`,
        realtimeRadarReady ? "ROS2 /scan once and hz have been observed" : "ROS2 /scan continuity has not been observed",
        "T=1001 WAVE ROVER feedback has not been observed",
      ],
      blocked_reasons: [...BLOCKED_REASONS, ...scanProofBlockerList],
    },
    realtime_radar: {
      // 只认 /scan once 与 /scan hz 两个真实 ROS2 topic 观测；raw packet 材料不能点亮雷达 ready。
      title: "实时雷达 (/scan)",
      status: realtimeRadarReady ? "ready" : "blocked",
      ready: realtimeRadarReady,
      endpoint: "/api/radar/scan-proof/latest",
      readiness_source: "scan_proof_once_and_hz_only",
      scan_once_observed: latestScanOnceObserved,
      scan_hz_observed: latestScanHzObserved,
      latest_proof_status: scanProofStatus,
      artifact_status: stringField(scanProofArtifact, "status", stringField(scanProofLatest, "artifact_status", "not_loaded")),
      freshness_status: stringField(scanProofFreshness, "status", stringField(scanProofLatest, "freshness_status", "unknown")),
      age_seconds: nullableNumberField(scanProofFreshness, "age_seconds") ?? nullableNumberField(scanProofLatest, "age_seconds"),
      raw_packet_ignored_for_ready: true,
      raw_packet_material_status: rawPacketProofStatus,
      blocked_reasons: [...new Set(realtimeRadarBlockers)],
      not_ready_reason: realtimeRadarReady ? "none" : "scan_once_or_hz_not_observed",
      safe_to_control: false,
    },
    realtime_map: {
      // 地图 readiness 依赖上游 /scan；没有 scan 时直接等待雷达，避免把 SLAM/map 缺口混成一个标题。
      title: "实时图 (SLAM/map)",
      status: realtimeMapStatus,
      ready: realtimeMapReady,
      depends_on_realtime_radar: true,
      map_artifact_status: mapArtifactStatus,
      slam_artifact_status: slamArtifactStatus,
      latest_map_observed: latestMapObserved,
      latest_slam_observed: latestSlamObserved,
      blocked_reasons: realtimeMapBlockers,
      not_ready_reason: realtimeMapStatus === "ready" ? "none" : realtimeMapStatus,
      pointcloud_fabricated: false,
      safe_to_control: false,
    },
    camera: {
      // 兼容既有 live 面板合同；实时 health/devices 由 local camera API 和 8787 camera proxy 拉取。
      base_url: "http://192.168.1.11:8088/",
      health_status: stringField(upperCamera, "status", "not_listening_observed"),
      video_source: stringField(upperCamera, "video_source", "/dev/video1"),
      devices_summary: [
        "set ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 on the PC dev server",
        "GET /api/o7/local-webrtc-camera and /api/o7/live-operator-panel read the unified upper API",
        "the user console may POST /api/o7/local-webrtc-camera/offer for camera media preview only",
        "/dev/video1 USB camera was previously observed as the usable capture source",
      ],
      offer_auto_post_enabled: false,
      lan_page_url: "http://192.168.1.11:8088/",
    },
    control: {
      // 控制 UI 只展示 future control shape；所有按钮点击只能落到本地 blocked 状态。
      visible_directions: ["forward", "back", "left", "right", "stop"],
      speed: {
        default_value: 0.2,
        min: 0,
        max: 0.5,
        step: 0.05,
        unit: "m/s",
      },
      command_dispatch_enabled: false,
      sends_commands: false,
      robot_ack_connected: false,
      blocked_reasons: [...BLOCKED_REASONS],
      base_boundary: {
        // PC 只展示现场已观测写入口和反馈缺口；真实控制必须另走带 ACK/停车兜底的新合同。
        observed_write_device: basePort as "/dev/ttyS5",
        baudrate: baseBaudrate as 115200,
        vendor_command_id: "T=1",
        feedback_request_id: "T=130",
        required_feedback_id: "T=1001",
        t1001_feedback_status: "not_observed_after_t130",
        manual_control_status: "fail_closed_display_only",
        forbidden_endpoint: "/api/base/manual",
        post_base_manual_enabled: false,
      },
    },
    fixed_false_flags: {
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      delivery_success: false,
      primary_actions_enabled: false,
    },
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    delivery_success: false,
    primary_actions_enabled: false,
    blocked_reasons: [...BLOCKED_REASONS],
    not_proven: [
      "real_lidar_scan",
      "real_wave_rover_uart_feedback",
      "real_robot_ack",
      "real_manual_control_dispatch",
      "delivery_success",
    ],
  };
  return response;
}
