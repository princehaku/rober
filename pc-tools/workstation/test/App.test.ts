import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../src/App.vue";
import { buildO7LiveOperatorPanel } from "../src/server/o7LiveOperatorPanel";
import {
  buildO7LocalWebrtcCamera,
  proxyO7LocalWebrtcCameraOffer,
  proxyO7LocalWebrtcCameraPeerClose,
} from "../src/server/o7LocalWebrtcCamera";
import {
  buildO7DirectUpperStatus,
  proxyO7DirectUpperFeedbackRequest,
  proxyO7DirectUpperLocalizeReset,
  proxyO7DirectUpperMapList,
  proxyO7DirectUpperMapSave,
  proxyO7DirectUpperMapStart,
  proxyO7DirectUpperManual,
  proxyO7DirectUpperOperatorReport,
  proxyO7DirectUpperOperatorReportReadback,
  proxyO7DirectUpperRadarScanProofLatest,
  proxyO7DirectUpperRadarScanProofRefresh,
  proxyO7DirectUpperRadarStart,
  proxyO7DirectUpperRadarStop,
  proxyO7DirectUpperStop,
} from "../src/server/o7DirectUpperApi";
import { PROOF_FLAGS } from "../src/shared/contracts";

enableAutoUnmount(afterEach);

const liveOperatorFixture = {
  schema: "trashbot.o7.live_operator_panel.v1",
  endpoint: "/api/o7/live-operator-panel",
  ...PROOF_FLAGS,
  ssh: {
    host: "192.168.1.11",
    port: 37878,
    reachable: true,
    workstation_api_8787_status: "ready",
  },
  lidar_radar: {
    dev_lidar: "/dev/ttyACM0",
    stc_by_id: "resolved_to_ttyACM0",
    scan_status: "not_proven",
    scan_proof_latest: {
      endpoint: "/api/radar/scan-proof/latest",
      artifact_status: "loaded",
      freshness_status: "fresh",
      age_seconds: 14,
      latest_proof_status: "blocked_or_not_observed",
      latest_scan_once_observed: false,
      latest_scan_hz_observed: false,
      latest_raw_packet_once_observed: false,
      blocked_reasons: ["ros2_command_unavailable"],
      readback_sends_commands: false,
      collector_executed_by_pc: false,
    },
    raw_packet_proof_latest: {
      endpoint: "/api/radar/raw-packet-proof/latest",
      http_status: 200,
      artifact_status: "loaded",
      freshness_status: "fresh",
      age_seconds: 7,
      latest_proof_status: "observed_raw_packet_material",
      latest_raw_bytes_observed: true,
      latest_sync_header_observed: true,
      latest_packet_parse_ok: true,
      latest_points_observed: true,
      latest_bytes_read: 4246,
      latest_sync_header_count: 127,
      latest_packets_parse_ok: 24,
      latest_points_total: 384,
      sends_commands: false,
      sends_motion_commands: false,
      robot_control_executed: false,
      safe_to_control: false,
      hil_pass: false,
      collector_executed_by_pc: false,
    },
    pointcloud_fabricated: false,
    source_facts: [
      "/dev/ttyACM0 is reported by upper robot API as the LiDAR serial device",
      "150000 baud, start a5 60, stop a5 00 a5 65 a5 65",
      "ROS2 /scan continuity has not been observed",
      "T=1001 WAVE ROVER feedback has not been observed",
    ],
    blocked_reasons: ["base_serial_identity_not_proven", "t1001_feedback_not_observed", "robot_ack_not_connected"],
  },
  realtime_radar: {
    title: "实时雷达 (/scan)",
    status: "blocked",
    ready: false,
    endpoint: "/api/radar/scan-proof/latest",
    readiness_source: "scan_proof_once_and_hz_only",
    scan_once_observed: false,
    scan_hz_observed: false,
    latest_proof_status: "blocked_or_not_observed",
    artifact_status: "loaded",
    freshness_status: "fresh",
    age_seconds: 14,
    raw_packet_ignored_for_ready: true,
    raw_packet_material_status: "observed_raw_packet_material",
    blocked_reasons: ["ros2_command_unavailable", "scan_once_not_observed", "scan_hz_not_observed"],
    not_ready_reason: "scan_once_or_hz_not_observed",
    safe_to_control: false,
  },
  realtime_map: {
    title: "实时图 (SLAM/map)",
    status: "waiting_for_radar",
    ready: false,
    depends_on_realtime_radar: true,
    map_artifact_status: "not_loaded",
    slam_artifact_status: "not_loaded",
    latest_map_observed: false,
    latest_slam_observed: false,
    blocked_reasons: ["realtime_radar_not_ready"],
    not_ready_reason: "waiting_for_radar",
    pointcloud_fabricated: false,
    safe_to_control: false,
  },
  camera: {
    base_url: "http://192.168.1.11:8088/",
    health_status: "ready",
    video_source: "auto",
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
    blocked_reasons: ["base_serial_identity_not_proven", "t1001_feedback_not_observed", "robot_ack_not_connected"],
    base_boundary: {
      observed_write_device: "/dev/ttyS5",
      baudrate: 115200,
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
  blocked_reasons: ["base_serial_identity_not_proven", "t1001_feedback_not_observed", "robot_ack_not_connected"],
  not_proven: [
    "real_lidar_scan",
    "real_wave_rover_uart_feedback",
    "real_robot_ack",
    "real_manual_control_dispatch",
    "delivery_success",
  ],
};

type LiveOperatorResponse = Awaited<ReturnType<typeof buildO7LiveOperatorPanel>>;
type LiveOperatorWithBaseBoundary = LiveOperatorResponse & {
  control: LiveOperatorResponse["control"] & {
    base_boundary: {
      observed_write_device: string;
      baudrate: number;
      vendor_command_id: string;
      feedback_request_id: string;
      required_feedback_id: string;
      t1001_feedback_status: string;
      manual_control_status: string;
      forbidden_endpoint: string;
      post_base_manual_enabled: false;
    };
  };
};

const localCameraFixture = {
  schema: "trashbot.pc_tools_workstation.o7_local_webrtc_camera.v1",
  endpoint: "/api/o7/local-webrtc-camera",
  remote_self_test_schema: "trashbot.local_webrtc_camera_offer_self_test.v1",
  ...PROOF_FLAGS,
  status: "ready",
  base_url: "http://192.168.1.11:8088",
  base_url_source: "env",
  camera_page_url: "http://192.168.1.11:8088",
  host: "orange-pi-zero3",
  health_http_status: 200,
  devices_http_status: 200,
  remote_schemas: {
    health: "trashbot.local_webrtc_camera_smoke.v1",
    devices: "trashbot.local_webrtc_camera_devices.v1",
  },
  health_status: "ready",
  video_source: "0",
  device_count: 1,
  dependency_statuses: { aiohttp: "ok", aiortc: "ok", cv2: "ok", av: "ok" },
  dependency_summary: ["aiohttp=ok", "aiortc=ok", "cv2=ok", "av=ok"],
  browser_smoke: {
    schema: "trashbot.o7.local_webrtc_browser_playback_smoke.v1",
    status: "ok",
    base_url: "http://192.168.1.11:8088",
    page_url: "http://192.168.1.11:8088",
    executed_at: "2026-06-01T04:12:00.000Z",
    browser_engine: "chromium",
    browser_available: true,
    playwright_available: true,
    start_clicked: true,
    first_frame_received: true,
    video_width: 640,
    video_height: 480,
    first_frame_ms: 1234,
    connection_state: "connected",
    ice_connection_state: "connected",
    ice_gathering_state: "complete",
    signaling_state: "stable",
    failure_category: "none",
    remote_health_status: "ready",
    remote_active_peer_connections: 1,
    offer_http_status: 200,
    offer_error_reason: null,
    offer_error_detail: null,
    observation_window_ms: 30000,
    final_ready_state: 4,
    stable_video_width: 640,
    stable_video_height: 480,
    ontrack_count: 1,
    receiver_track_states: [],
    transceiver_directions: [],
    inbound_video_stats: [],
    selected_candidate_pair: null,
    peer_state_timeline: [],
    post_smoke_remote_health: null,
    stability_summary: {
      status: "not_observed",
      observation_window_ms: 0,
      sample_interval_ms: null,
      sample_count: 0,
      first_packets_received: null,
      last_packets_received: null,
      first_frames_decoded: null,
      last_frames_decoded: null,
      first_frames_received: null,
      last_frames_received: null,
      estimated_fps: null,
      estimated_packet_rate: null,
      video_size_stable: "not_available",
      stable_video_width: null,
      stable_video_height: null,
      connection_remained_connected: "not_available",
      ice_remained_connected: "not_available",
      console_errors_added: 0,
      page_errors_added: 0,
      remote_health_samples: 0,
      remote_health_statuses: [],
      remote_active_peer_connections_first: null,
      remote_active_peer_connections_last: null,
      remote_system_metrics: "not_available",
      remote_stability_metrics: "not_available",
      post_close_active_peer_connections: null,
      remote_active_peer_cleaned: "not_available",
    },
    long_stability_acceptance: {
      status: "not_observed",
      required_window_ms: 180000,
      observed_window_ms: 0,
      blocked_reasons: ["long_stability_artifact_not_observed"],
      safe_to_control: false,
    },
    console_error_count: 0,
    page_error_count: 0,
    server_peer_id: null,
    server_peer_close_status: "not_loaded",
    console_errors: [],
    page_errors: [],
    blocked_reason: "none",
    report_path: "pc-tools/workstation/.workstation-runtime/o7-browser-playback-smoke.json",
    safe_to_control: false,
    sends_commands: false,
    robot_control_executed: false,
    offer_executed_by_browser: true,
    workstation_api_offer_executed: false,
  },
  blocked_reasons: [],
  not_proven: ["webrtc_offer_answer_not_executed_by_workstation"],
  fail_closed_reason: "none_health_devices_loaded_offer_not_executed",
  health_get_executed: true,
  devices_get_executed: true,
  offer_executed: false,
  webrtc_session_created: false,
  sends_commands: false,
  cloud_relay: false,
  robot_control_executed: false,
  fixed_false_fields: {
    safe_to_control: false,
    robot_control_executed: false,
    sends_commands: false,
    cloud_relay: false,
    offer_executed: false,
    webrtc_session_created: false,
  },
};

const directUpperAdapterFixture = {
  version: "2026-06-04.scan-proof-refresh-v1",
  source: "pc-tools/workstation/src/server/o7DirectUpperApi.ts",
  field_default_enabled: true,
  field_default_url: "http://192.168.1.11:8787",
  dev_server_reload_hint: "restart npm run dev if 127.0.0.1:5173 still reports missing adapter or base_url_not_configured for radar/start or scan-proof refresh",
} as const;

const directUpperFixture = {
  schema: "trashbot.pc_tools_workstation.o7_direct_upper_status.v1",
  endpoint: "/api/o7/direct-upper/status",
  ...PROOF_FLAGS,
  mode: "direct_upper_computer_lan_only",
  adapter: directUpperAdapterFixture,
  status: "ready",
  upper_api_base_url: "http://192.168.1.11:8787",
  upper_api_base_url_source: "env",
  request_timeout_ms: 120,
  health_request: { path: "/health", method: "GET", executed: true, ok: true, http_status: 200, failure_reason: "" },
  status_request: { path: "/api/status", method: "GET", executed: true, ok: true, http_status: 200, failure_reason: "" },
  health_summary: { status: "ready", schema: "trashbot.upper_robot_api.health.v1" },
  upper_status_summary: {
    camera_status: "ready",
    radar_scan_status: "not_proven",
    radar_scan_proof_artifact_status: "loaded",
    radar_scan_proof_freshness_status: "fresh",
    radar_scan_proof_age_seconds: 14,
    radar_scan_proof_latest_status: "blocked_or_not_observed",
    radar_scan_proof_fresh_observed: false,
    radar_scan_proof_hz_average_rate_hz: null,
    radar_scan_proof_tf_observed: false,
    radar_scan_proof_all_required_observations_observed: false,
    radar_scan_proof_runtime_summary_fallback_used: false,
    radar_scan_proof_runtime_summary_path: "not_reported",
    radar_continuous_scan_status: "not_proven",
    radar_continuous_blockers: ["scan_continuity_not_observed"],
    radar_scan_proof_blockers: ["ros2_command_unavailable"],
    radar_raw_packet_proof_artifact_status: "loaded",
    radar_raw_packet_proof_freshness_status: "fresh",
    radar_raw_packet_proof_age_seconds: 7,
    radar_raw_packet_proof_latest_status: "observed_raw_packet_material",
    radar_raw_packet_proof_bytes_read: 4246,
    radar_raw_packet_proof_sync_header_count: 127,
    radar_raw_packet_proof_packets_parse_ok: 24,
    radar_raw_packet_proof_points_total: 384,
    radar_raw_packet_proof_safe_to_control: false,
    lidar_port: "/dev/ttyACM0",
    map_lifecycle_status: "waiting_for_mapping",
    map_artifact_ref: "not_loaded",
    localization_status: "not_loaded",
    operator_report_evidence_ref: "missing_operator_report",
    base_port: "/dev/ttyS5",
    base_baudrate: 115200,
    base_write_control_available: true,
    robot_ack_connected: false,
    t1001_observed: false,
  },
  safety_flags: {
    cloud_relay_bypassed: true,
    pc_local_only: true,
    direct_upper_computer_mode: true,
    production_4g_cloud_route_changed: false,
    safe_to_control: false,
    sends_cmd_vel: false,
    sends_wave_rover_json_directly: false,
    robot_control_executed: false,
    robot_ack_connected: false,
    t1001_observed: false,
  },
  local_api_paths: {
    status: "/api/o7/direct-upper/status",
    stop: "/api/o7/direct-upper/base/stop",
    manual: "/api/o7/direct-upper/base/manual",
    feedback_request: "/api/o7/direct-upper/base/feedback-request",
    radar_start: "/api/o7/direct-upper/radar/start",
    radar_stop: "/api/o7/direct-upper/radar/stop",
    scan_proof_refresh: "/api/o7/direct-upper/radar/scan-proof/refresh",
    scan_proof_latest: "/api/o7/direct-upper/radar/scan-proof/latest",
    map_start: "/api/o7/direct-upper/map/start",
    map_reset: "/api/o7/direct-upper/map/reset",
    map_save: "/api/o7/direct-upper/map/save",
    map_load: "/api/o7/direct-upper/map/load",
    map_list: "/api/o7/direct-upper/map/list",
    localize_reset: "/api/o7/direct-upper/localize/reset",
    operator_report: "/api/o7/direct-upper/operator-report",
  },
  blocked_reasons: ["robot_ack_not_connected", "t1001_feedback_not_observed"],
  failure_reason: "none",
  not_proven: ["robot_ack", "t1001_feedback", "hil_pass"],
  safe_to_control: false,
  sends_commands: false,
  robot_control_executed: false,
};

class MockMediaStream {
  constructor(public tracks: unknown[] = []) {}
}

class MockPeerConnection {
  iceGatheringState = "complete";
  connectionState = "new";
  localDescription: RTCSessionDescriptionInit | null = null;
  ontrack: ((event: RTCTrackEvent) => void) | null = null;
  onconnectionstatechange: (() => void) | null = null;

  addTransceiver = vi.fn();
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  getReceivers = vi.fn(() => []);
  getSenders = vi.fn(() => []);
  close = vi.fn();
  createOffer = vi.fn(async () => ({ type: "offer", sdp: "m=video\r\na=recvonly\r\n" }) as RTCSessionDescriptionInit);
  setLocalDescription = vi.fn(async (description: RTCSessionDescriptionInit) => {
    this.localDescription = description;
  });
  setRemoteDescription = vi.fn(async () => {
    this.connectionState = "connected";
    this.ontrack?.({ streams: [new MockMediaStream()], track: {} } as unknown as RTCTrackEvent);
  });
}

function stubWebrtc(): void {
  // 单测只模拟用户点击后的摄像头 recvonly offer，不打开真实摄像头或控制链路。
  vi.stubGlobal("RTCPeerConnection", MockPeerConnection);
  vi.stubGlobal("MediaStream", MockMediaStream);
  Object.defineProperty(HTMLMediaElement.prototype, "play", {
    configurable: true,
    value: vi.fn(async () => undefined),
  });
}

interface StubFetchOptions {
  offerOk?: boolean;
  offerStatus?: number;
  offerPayload?: unknown;
}

function stubFetch(options: StubFetchOptions = {}): ReturnType<typeof vi.fn> {
  const mockedFetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const pathname = url.split("?")[0] ?? url;
    // 首屏只允许 O7 本机只读 API；camera offer 必须由用户点击预览按钮后才出现。
    const manualBody = init?.body ? JSON.parse(String(init.body)) as { direction?: string; speed?: number; duration_ms?: number; evidence_ref?: string; fixture_mode?: boolean } : null;
    const operatorBody = init?.body ? JSON.parse(String(init.body)) as { evidence_ref?: string; map_id?: string; note?: string; fixture_mode?: boolean } : null;
    const operatorCommandByUrl: Record<string, { schema: string; command: string; upperPath: string; method: "GET" | "POST" }> = {
      "/api/o7/direct-upper/base/stop": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_stop.v1",
        command: "stop",
        upperPath: "/api/base/stop",
        method: "POST",
      },
      "/api/o7/direct-upper/radar/start": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_radar_start.v1",
        command: "radar_start",
        upperPath: "/api/radar/start",
        method: "POST",
      },
      "/api/o7/direct-upper/radar/stop": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_radar_stop.v1",
        command: "radar_stop",
        upperPath: "/api/radar/stop",
        method: "POST",
      },
      "/api/o7/direct-upper/radar/scan-proof/refresh": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_radar_scan_proof_refresh.v1",
        command: "radar_scan_proof_refresh",
        upperPath: "/api/radar/scan-proof/refresh",
        method: "POST",
      },
      "/api/o7/direct-upper/map/start": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_map_start.v1",
        command: "map_start",
        upperPath: "/api/map/start",
        method: "POST",
      },
      "/api/o7/direct-upper/map/reset": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_map_reset.v1",
        command: "map_reset",
        upperPath: "/api/map/reset",
        method: "POST",
      },
      "/api/o7/direct-upper/map/save": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_map_save.v1",
        command: "map_save",
        upperPath: "/api/map/save",
        method: "POST",
      },
      "/api/o7/direct-upper/map/load": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_map_load.v1",
        command: "map_load",
        upperPath: "/api/map/load",
        method: "POST",
      },
      "/api/o7/direct-upper/map/list": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_map_list.v1",
        command: "map_list",
        upperPath: "/api/map/list",
        method: "GET",
      },
      "/api/o7/direct-upper/localize/reset": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_localize_reset.v1",
        command: "localize_reset",
        upperPath: "/api/localize/reset",
        method: "POST",
      },
      "/api/o7/direct-upper/operator-report": {
        schema: "trashbot.pc_tools_workstation.o7_direct_upper_operator_report.v1",
        command: "operator_report",
        upperPath: "/api/operator/report",
        method: "POST",
      },
    };
    const operatorCommand = operatorCommandByUrl[pathname];
    const payload =
      url === "/api/o7/live-operator-panel"
        ? liveOperatorFixture
        : url === "/api/o7/local-webrtc-camera"
          ? localCameraFixture
        : url === "/api/o7/direct-upper/status"
          ? directUpperFixture
          : url === "/api/o7/local-webrtc-camera/offer"
              ? options.offerPayload ?? { type: "answer", sdp: "m=video\r\na=sendonly\r\n", peer_id: "peer-test-1" }
              : url === "/api/o7/direct-upper/base/manual"
                ? {
                    schema: "trashbot.pc_tools_workstation.o7_direct_upper_manual.v1",
                    endpoint: "/api/o7/direct-upper/base/manual",
                    ...PROOF_FLAGS,
                    mode: "direct_upper_computer_lan_only",
                    adapter: directUpperAdapterFixture,
                    command: "manual",
                    accepted_by_workstation: true,
                    upper_request: {
                      path: "/api/base/manual",
                      method: "POST",
                      executed: true,
                      ok: true,
                      http_status: 200,
                      failure_reason: "",
                    },
                    upper_api_base_url: "http://192.168.1.11:8787",
                    cloud_relay_bypassed: true,
                    pc_local_only: true,
                    fail_closed: false,
                    failure_reason: "none",
                    command_payload_summary: {
                      direction: manualBody?.direction ?? "not_applicable",
                      speed_mps: manualBody?.speed ?? 0,
                      duration_ms: manualBody?.duration_ms ?? 0,
                      clamped_by_pc: false,
                      depends_on_upper_8787_guardrail: true,
                      evidence_ref: manualBody?.evidence_ref ?? "operator_field_report_pending",
                    },
                    robot_ack_connected: false,
                    t1001_observed: false,
                    safety_flags: directUpperFixture.safety_flags,
                    blocked_reasons: ["robot_ack_not_connected", "t1001_feedback_not_observed"],
                    not_proven: ["robot_ack", "t1001_feedback", "hil_pass", "actual_motion_or_stop_observed"],
                    safe_to_control: false,
                    sends_commands: false,
                    robot_control_executed: false,
                  }
              : operatorCommand
                ? {
                    schema: operatorCommand.schema,
                    endpoint: pathname,
                    ...PROOF_FLAGS,
                    mode: "direct_upper_computer_lan_only",
                    adapter: directUpperAdapterFixture,
                    command: operatorCommand.command,
                    accepted_by_workstation: true,
                    upper_request: {
                      path: operatorCommand.upperPath,
                      method: operatorCommand.method,
                      executed: true,
                      ok: true,
                      http_status: 200,
                      failure_reason: "",
                    },
                    upper_api_base_url: "http://192.168.1.11:8787",
                    cloud_relay_bypassed: true,
                    pc_local_only: true,
                    fail_closed: false,
                    failure_reason: "none",
                    upper_result_summary: operatorCommand.command === "radar_scan_proof_refresh"
                      ? {
                          status: "fresh",
                          proof_status: "full",
                          latest_proof_status: "fresh_scan_proof_observed",
                          artifact_status: "loaded",
                          artifact_path: "artifacts/radar/scan-proof-latest.json",
                          freshness_status: "fresh",
                          freshness_age_seconds: 1,
                          fresh_scan_proof_observed: true,
                          scan_hz_average_rate_hz: 257.987,
                          tf_observed: true,
                          all_required_observations_observed: true,
                          runtime_summary_fallback_used: true,
                          runtime_summary_path: "runtime/lidar_runtime_summary.json",
                          continuous_scan_status: "not_proven",
                          continuous_blocked_reasons: ["scan_continuity_not_observed"],
                          safe_to_control: false,
                          sends_commands: false,
                          robot_control_executed: false,
                          delivery_success: false,
                          blocked_reasons: ["continuous_scan_status_not_proven"],
                          not_proven: ["continuous_radar_not_proven"],
                        }
                      : undefined,
                    command_payload_summary: {
                      direction: "not_applicable",
                      speed_mps: 0,
                      duration_ms: 0,
                      clamped_by_pc: false,
                      depends_on_upper_8787_guardrail: true,
                      map_id: operatorBody?.map_id,
                      evidence_ref: operatorBody?.evidence_ref ?? "operator_field_report_pending",
                      report_note: operatorBody?.note,
                    },
                    robot_ack_connected: false,
                    t1001_observed: false,
                    safety_flags: directUpperFixture.safety_flags,
                    blocked_reasons: ["robot_ack_not_connected", "t1001_feedback_not_observed", "field_evidence_not_proven"],
                    not_proven: ["robot_ack", "t1001_feedback", "hil_pass", "actual_motion_or_stop_observed"],
                    safe_to_control: false,
                    sends_commands: false,
                    robot_control_executed: false,
                  }
              : null;
    if (!payload) {
      throw new Error(`unexpected fetch ${url}`);
    }
    const isOffer = url === "/api/o7/local-webrtc-camera/offer";
    const ok = isOffer ? options.offerOk ?? true : true;
    return {
      ok,
      status: isOffer ? options.offerStatus ?? (ok ? 200 : 409) : 200,
      json: async () => payload,
    } as Response;
  });
  vi.stubGlobal("fetch", mockedFetch);
  return mockedFetch;
}

async function confirmOperator(wrapper: ReturnType<typeof mount>): Promise<void> {
  // 所有控制类单测都显式走确认门，避免 keyboard 或按钮绕过现场确认。
  await wrapper.find<HTMLInputElement>('input[aria-label="operator confirmation"]').setValue(true);
  await flushPromises();
  await wrapper.vm.$nextTick();
}

describe("O7 live operator first screen", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders the simplified user console with 8787, 8088, radar, and base fail-closed boundaries", async () => {
    stubWebrtc();
    const mockedFetch = stubFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    const text = wrapper.text();
    expect(text).toContain("Rober 控制台");
    expect(text).toContain("预览");
    expect(text).toContain("地图");
    expect(text).toContain("操控");
    expect(text).toContain("状态");
    expect(text).toContain("8787 API ready");
    expect(text).toContain("摄像头8088 ready");
    expect(text).toContain("实时雷达 (/scan)");
    expect(text).toContain("实时图 (SLAM/map)");
    expect(text).toContain("blocked · once=no · hz=no");
    expect(text).toContain("waiting_for_radar · 先等待真实 /scan once+hz");
    expect(text).toContain("scan_once_not_observed");
    expect(text).toContain("scan_hz_not_observed");
    expect(text).toContain("Raw packet proof");
    expect(text).toContain("observed_raw_packet_material");
    expect(text).toContain("bytes 4246");
    expect(text).toContain("sync 127");
    expect(text).toContain("packets 24");
    expect(text).toContain("points 384");
    expect(text).toContain("safe_to_control=false");
    expect(text).toContain("/dev/ttyS5 @ 115200");
    expect(text).toContain("T=1001 not_observed_after_t130");
    expect(text).toContain("manual control fail_closed_display_only");
    expect(text).toContain("控制锁定：底盘串口/反馈/ACK 未确认");
    expect(text).toContain("PC 本机 8787 接口");
    expect(text).toContain("ready · /dev/ttyS5 · /dev/ttyACM0");
    expect(text).toContain("/api/o7/direct-upper/status");
    expect(text).toContain("/api/o7/direct-upper/base/stop");
    expect(text).toContain("/api/o7/direct-upper/base/feedback-request");
    expect(text).toContain("/api/o7/direct-upper/base/manual");
    expect(text).toContain("雷达 / 建图 / 定位");
    expect(text).toContain("Radar start");
    expect(text).toContain("Refresh scan proof");
    expect(text).toContain("Map save");
    expect(text).toContain("Localize reset");
    expect(text).toContain("Report evidence ref");
    expect(text).toContain("fixture mode");
    expect(text).toContain("operator confirmation");
    expect(text).toContain("real upper mode · radar/report/scan-proof refresh use field_default if env is absent; base/map/localize still require env");
    expect(text).toContain("adapter=2026-06-04.scan-proof-refresh-v1");
    expect(text).toContain("field_default=http://192.168.1.11:8787");
    expect(text).toContain("/api/o7/direct-upper/radar/start");
    expect(text).toContain("/api/o7/direct-upper/radar/scan-proof/refresh");
    expect(text).toContain("/api/o7/direct-upper/map/save");
    expect(text).toContain("/api/o7/direct-upper/localize/reset");
    expect(text).toContain("/api/o7/direct-upper/operator-report");
    expect(text).toContain("map=not_loaded · localize=not_loaded · report=missing_operator_report");
    expect(text).toContain("loaded · fresh · 14s · blocked_or_not_observed");
    expect(text).toContain("fresh=false · hz=n/a · tf=missing · fallback=false · continuous=not_proven");
    expect(text).toContain("scan_continuity_not_observed");
    expect(text).toContain("http://192.168.1.11:8787");
    expect(text).toContain("摄像头已就绪，点击重新连接预览");
    expect(text).not.toContain("雷达未接入 / 等待建图");
    expect(text).not.toContain("External Probe Artifact");
    expect(text).not.toContain("Real Material Acceptance");
    expect(text).not.toContain("ASR");
    expect(text).not.toContain("TTS");
    expect(text).not.toContain("ready to control");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toEqual([
      "/api/o7/live-operator-panel",
      "/api/o7/local-webrtc-camera",
      "/api/o7/direct-upper/status",
    ]);
  });

  it("creates the camera offer only after the operator clicks reconnect preview", async () => {
    stubWebrtc();
    const mockedFetch = stubFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/local-webrtc-camera/offer");

    await wrapper.findAll("button").find((button) => button.text() === "重新连接预览")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const calledUrls = mockedFetch.mock.calls.map(([url]) => String(url));
    expect(calledUrls.filter((url) => url === "/api/o7/local-webrtc-camera/offer")).toHaveLength(1);
    expect(wrapper.text()).toContain("摄像头画面已连接");
    expect(calledUrls).not.toContain("/api/base/manual");
    expect(wrapper.text()).not.toContain("ready to control");
  });

  it("shows a readable camera peer conflict when explicit reconnect receives offer 409", async () => {
    stubWebrtc();
    const mockedFetch = stubFetch({
      offerOk: false,
      offerStatus: 409,
      offerPayload: { error: "peer_conflict", safe_to_control: false },
    });

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/local-webrtc-camera/offer");

    await wrapper.findAll("button").find((button) => button.text() === "重新连接预览")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const calledUrls = mockedFetch.mock.calls.map(([url]) => String(url));
    expect(calledUrls.filter((url) => url === "/api/o7/local-webrtc-camera/offer")).toHaveLength(1);
    expect(wrapper.text()).toContain("摄像头已有预览连接，关闭其他页面或稍后再点重新连接预览");
    expect(calledUrls).not.toContain("/api/base/manual");
    expect(wrapper.text()).toContain("控制锁定：底盘串口/反馈/ACK 未确认");
    expect(wrapper.text()).not.toContain("ready to control");
  });

  it("routes every direction button through the same-origin direct-upper manual proxy while preserving fail-closed copy", async () => {
    stubWebrtc();
    const mockedFetch = stubFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await confirmOperator(wrapper);

    for (const label of ["前进", "后退", "左转", "右转", "Stop"]) {
      await wrapper.findAll("button").find((button) => button.text() === label)?.trigger("click");
      await flushPromises();
      await wrapper.vm.$nextTick();
    }

    const calledUrls = mockedFetch.mock.calls.map(([url]) => String(url));
    const manualCalls = mockedFetch.mock.calls.filter(([url]) => String(url) === "/api/o7/direct-upper/base/manual");
    const stopCalls = mockedFetch.mock.calls.filter(([url]) => String(url) === "/api/o7/direct-upper/base/stop");
    expect(manualCalls).toHaveLength(4);
    expect(stopCalls).toHaveLength(1);
    expect(manualCalls.map(([, init]) => JSON.parse(String(init?.body)).direction)).toEqual([
      "forward",
      "back",
      "left",
      "right",
    ]);
    expect(manualCalls.map(([, init]) => JSON.parse(String(init?.body)).evidence_ref)).toEqual([
      "operator_field_report_pending",
      "operator_field_report_pending",
      "operator_field_report_pending",
      "operator_field_report_pending",
    ]);
    expect(manualCalls.map(([, init]) => JSON.parse(String(init?.body)).duration_ms)).toEqual([250, 250, 350, 350]);
    expect(manualCalls.map(([, init]) => JSON.parse(String(init?.body)).speed)).toEqual([0.2, 0.2, 0.08, 0.08]);
    expect(JSON.parse(String(stopCalls[0]?.[1]?.body))).toMatchObject({
      evidence_ref: "operator_field_report_pending",
      fixture_mode: false,
    });
    expect(wrapper.text()).toContain("Stop 已发送（仍锁定）：/api/base/stop HTTP 200");
    expect(wrapper.text()).toContain("ACK not observed / T=1001 not observed");
    expect(wrapper.text()).toContain("锁定原因 robot_ack_not_connected / t1001_feedback_not_observed");
    expect(calledUrls).not.toContain("/api/base/manual");
    expect(calledUrls).not.toContain("/api/base/stop");
    expect(calledUrls.join("\n")).not.toContain("/cmd_vel");
    expect(calledUrls.join("\n")).not.toContain("wave_rover");
    expect(wrapper.text()).not.toContain("ready to control");
  });

  it("supports WASD plus Space/X manual shortcuts while ignoring editable focus and repeat keydown", async () => {
    stubWebrtc();
    const mockedFetch = stubFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await confirmOperator(wrapper);

    const slider = wrapper.find<HTMLInputElement>('input[aria-label="速度"]');
    await slider.setValue(0.02);
    slider.element.dispatchEvent(new KeyboardEvent("keydown", { key: "w", bubbles: true }));
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "a", repeat: true }));

    for (const eventInit of [
      { key: "w" },
      { key: "a" },
      { key: "s" },
      { key: "d" },
      { key: " " },
      { key: "x" },
    ]) {
      window.dispatchEvent(new KeyboardEvent("keydown", eventInit));
      await flushPromises();
      await wrapper.vm.$nextTick();
    }

    const manualCalls = mockedFetch.mock.calls.filter(([url]) => String(url) === "/api/o7/direct-upper/base/manual");
    const bodies = manualCalls.map(([, init]) => JSON.parse(String(init?.body)));
    expect(bodies.map((body) => body.direction)).toEqual(["forward", "left", "back", "right", "stop", "stop"]);
    expect(bodies.map((body) => body.duration_ms)).toEqual([250, 350, 250, 350, 250, 250]);
    expect(bodies.map((body) => body.speed)).toEqual([0.02, 0.08, 0.02, 0.08, 0, 0]);
    expect(wrapper.text()).toContain("Stop 已发送（仍锁定）：/api/base/manual HTTP 200");
    expect(wrapper.text()).toContain("safe_to_control=false");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/base/manual");
  });

  it("blocks manual keyboard control until operator confirmation is checked", async () => {
    stubWebrtc();
    const mockedFetch = stubFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "w" }));
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("前进 未发送：请先勾选 operator confirmation");
    expect(wrapper.text()).toContain("evidence_ref=operator_field_report_pending");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/o7/direct-upper/base/manual");
  });

  it("routes radar, scan proof refresh, map, localize, and operator report controls through workstation direct-upper proxies with not_proven copy", async () => {
    stubWebrtc();
    const mockedFetch = stubFetch();

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await confirmOperator(wrapper);

    for (const label of ["Radar start", "Radar stop", "Refresh scan proof", "Map start", "Map reset", "Map save", "Map load", "Map list", "Localize reset"]) {
      await vi.waitFor(() => {
        const button = wrapper.findAll("button").find((item) => item.text() === label);
        expect(button?.attributes("disabled")).toBeUndefined();
      });
      const button = wrapper.findAll("button").find((item) => item.text() === label);
      expect(button).toBeTruthy();
      await button?.trigger("click");
      await flushPromises();
      await wrapper.vm.$nextTick();
      if (label === "Refresh scan proof") {
        const scanProofText = wrapper.text();
        expect(scanProofText).toContain("Refresh scan proof 已触发但 upper 仍 not_proven（仍锁定）");
        expect(scanProofText).toContain("upper_result=fresh/full/fresh_scan_proof_observed");
        expect(scanProofText).toContain("fresh=true");
        expect(scanProofText).toContain("hz=257.987");
        expect(scanProofText).toContain("tf=observed");
        expect(scanProofText).toContain("fallback=true");
        expect(scanProofText).toContain("continuous=not_proven");
        expect(scanProofText).toContain("continuous_blockers=scan_continuity_not_observed");
        expect(scanProofText).toContain("upper_blockers=continuous_scan_status_not_proven");
        expect(scanProofText).toContain("upper_not_proven=continuous_radar_not_proven");
        expect(scanProofText).toContain("artifact=loaded:artifacts/radar/scan-proof-latest.json");
        expect(scanProofText).toContain("freshness=fresh/1s");
        expect(scanProofText).toContain("read-only proof refresh，不启动 driver、不控底盘；not_proven=HIL/PC WASD/Nav2/map/delivery");
      }
    }
    await vi.waitFor(() => {
      const button = wrapper.findAll("button").find((item) => item.text() === "Report evidence ref");
      expect(button?.attributes("disabled")).toBeUndefined();
    });
    await wrapper.findAll("button").find((button) => button.text() === "Report evidence ref")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const calledUrls = mockedFetch.mock.calls.map(([url]) => String(url));
    expect(calledUrls).toContain("/api/o7/direct-upper/radar/start");
    expect(calledUrls).toContain("/api/o7/direct-upper/radar/stop");
    expect(calledUrls).toContain("/api/o7/direct-upper/radar/scan-proof/refresh");
    expect(calledUrls).toContain("/api/o7/direct-upper/map/start");
    expect(calledUrls).toContain("/api/o7/direct-upper/map/reset");
    expect(calledUrls).toContain("/api/o7/direct-upper/map/save");
    expect(calledUrls).toContain("/api/o7/direct-upper/map/load");
    expect(calledUrls.some((url) => url.startsWith("/api/o7/direct-upper/map/list?"))).toBe(true);
    expect(calledUrls).toContain("/api/o7/direct-upper/localize/reset");
    expect(calledUrls).toContain("/api/o7/direct-upper/operator-report");
    expect(calledUrls.join("\n")).not.toContain("http://192.168.1.11:8787/api");
    expect(calledUrls.join("\n")).not.toContain("/cmd_vel");
    expect(calledUrls.join("\n")).not.toContain("/api/radar/start");
    expect(calledUrls.join("\n")).not.toContain("/api/radar/scan-proof/refresh");
    expect(wrapper.text()).toContain("Operator report 已发送（仍锁定）：/api/operator/report HTTP 200");
    expect(wrapper.text()).toContain("锁定原因 robot_ack_not_connected / t1001_feedback_not_observed / field_evidence_not_proven");
    expect(wrapper.text()).toContain("safe_to_control=false");
    const saveCall = mockedFetch.mock.calls.find(([url]) => String(url) === "/api/o7/direct-upper/map/save");
    const mapListCall = mockedFetch.mock.calls.find(([url]) => String(url).startsWith("/api/o7/direct-upper/map/list?"));
    expect(saveCall).toBeTruthy();
    expect(String(mapListCall?.[0])).toContain("evidence_ref=operator_field_report_pending");
    expect(JSON.parse(String(saveCall?.[1]?.body))).toMatchObject({
      map_id: "latest",
      evidence_ref: "operator_field_report_pending",
      fixture_mode: false,
    });
  });

  it("clicks Radar start without env in real mode and reports an executed upper HTTP failure instead of base-url not configured", async () => {
    stubWebrtc();
    let radarStartPayload: unknown = null;
    const jsonResponse = (payload: unknown, status = 200): Response => ({
      ok: status >= 200 && status < 300,
      status,
      json: async () => payload,
    }) as Response;
    const mockedFetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/o7/live-operator-panel") {
        return jsonResponse(liveOperatorFixture);
      }
      if (url === "/api/o7/local-webrtc-camera") {
        return jsonResponse(localCameraFixture);
      }
      if (url === "/api/o7/direct-upper/status") {
        return jsonResponse(await buildO7DirectUpperStatus({ env: {} }));
      }
      if (url === "/api/o7/direct-upper/radar/start") {
        const result = await proxyO7DirectUpperRadarStart({
          env: {},
          body: JSON.parse(String(init?.body ?? "{}")),
        });
        radarStartPayload = result.payload;
        return jsonResponse(result.payload, result.status);
      }
      if (url === "http://192.168.1.11:8787/health") {
        return jsonResponse({ schema: "trashbot.upper_robot_api.health.v1", status: "ready" });
      }
      if (url === "http://192.168.1.11:8787/api/status") {
        return jsonResponse({
          camera: { status: "ready" },
          radar: { scan_status: "not_proven" },
          base: { port: "/dev/ttyS5", baudrate: 115200, write_control_available: false },
        });
      }
      if (url === "http://192.168.1.11:8787/api/radar/start") {
        return jsonResponse({ error: "ros2_driver_not_running" }, 503);
      }
      throw new Error(`unexpected fetch ${url}`);
    });
    vi.stubGlobal("fetch", mockedFetch);

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await confirmOperator(wrapper);

    await wrapper.findAll("button").find((button) => button.text() === "Radar start")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const text = wrapper.text();
    expect(text).toContain("Radar start 失败：upper_http_503");
    expect(text).toContain("/api/radar/start HTTP 503");
    expect(text).toContain("source=field_default");
    expect(text).toContain("adapter=2026-06-04.scan-proof-refresh-v1");
    expect(text).toContain("safe_to_control=false");
    expect(text).toContain("robot_ack_not_connected / t1001_feedback_not_observed / field_evidence_not_proven");
    expect(text).not.toContain("Radar start 失败：base_url_not_configured");
    expect(text).not.toContain("/api/radar/start not_executed");
    expect(radarStartPayload).toMatchObject({
      accepted_by_workstation: false,
      upper_api_base_url_source: "field_default",
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      upper_request: {
        path: "/api/radar/start",
        method: "POST",
        executed: true,
        ok: false,
        http_status: 503,
        failure_reason: "upper_http_503",
      },
    });
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toContain("http://192.168.1.11:8787/api/radar/start");
  });

  it("shows remote scan-proof not_proven blockers when refresh returns upper HTTP 200", async () => {
    stubWebrtc();
    const jsonResponse = (payload: unknown, status = 200): Response => ({
      ok: status >= 200 && status < 300,
      status,
      json: async () => payload,
    }) as Response;
    const mockedFetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/o7/live-operator-panel") {
        return jsonResponse(liveOperatorFixture);
      }
      if (url === "/api/o7/local-webrtc-camera") {
        return jsonResponse(localCameraFixture);
      }
      if (url === "/api/o7/direct-upper/status") {
        return jsonResponse(directUpperFixture);
      }
      if (url === "/api/o7/direct-upper/radar/scan-proof/refresh") {
        const result = await proxyO7DirectUpperRadarScanProofRefresh({
          env: {},
          body: JSON.parse(String(init?.body ?? "{}")),
        });
        return jsonResponse(result.payload, result.status);
      }
      if (url === "http://192.168.1.11:8787/api/radar/scan-proof/refresh") {
        return jsonResponse({
          schema: "trashbot.upper_robot_api.radar_scan_proof_refresh.v1",
          status: "not_proven",
          proof_status: "not_proven",
          latest_proof_status: "blocked_or_not_observed",
          artifact: { status: "loaded", path: "artifacts/radar/scan-proof-latest.json" },
          freshness: { status: "fresh", age_seconds: 1 },
          proof_summary: {
            scan_hz_average_rate_hz: 244.481,
            tf_observed: true,
            all_required_observations_observed: true,
          },
          latest_result: {
            proof: {
              runtime_summary_fallback_used: true,
              runtime_summary_path: "runtime/lidar_runtime_summary.json",
            },
          },
          continuous_scan_status: "not_proven",
          continuous_blocked_reasons: ["scan_continuity_not_observed"],
          blocked_reasons: ["ros2_command_unavailable", "upper_api_scan_not_proven"],
          not_proven: ["upper_api_scan_not_proven"],
          safe_to_control: false,
          sends_commands: false,
          robot_control_executed: false,
        });
      }
      throw new Error(`unexpected fetch ${url}`);
    });
    vi.stubGlobal("fetch", mockedFetch);

    const wrapper = mount(App);
    await flushPromises();
    await wrapper.vm.$nextTick();
    await confirmOperator(wrapper);

    await wrapper.findAll("button").find((button) => button.text() === "Refresh scan proof")?.trigger("click");
    await flushPromises();
    await wrapper.vm.$nextTick();

    const text = wrapper.text();
    expect(text).toContain("Refresh scan proof 已触发但 upper 仍 not_proven（仍锁定）");
    expect(text).toContain("upper_result=not_proven/not_proven/blocked_or_not_observed");
    expect(text).toContain("hz=244.481");
    expect(text).toContain("tf=observed");
    expect(text).toContain("fallback=true");
    expect(text).toContain("continuous=not_proven");
    expect(text).toContain("continuous_blockers=scan_continuity_not_observed");
    expect(text).toContain("upper_blockers=ros2_command_unavailable / upper_api_scan_not_proven");
    expect(text).toContain("artifact=loaded:artifacts/radar/scan-proof-latest.json");
    expect(text).toContain("safe_to_control=false");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toContain("http://192.168.1.11:8787/api/radar/scan-proof/refresh");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/api/base/manual");
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).not.toContain("/cmd_vel");
  });
});

describe("O7 live operator contracts", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("keeps the panel API fail-closed while exposing the upper API and hardware evidence gaps", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        camera: { status: "ready", video_source: "auto" },
        radar: {
          observed_lidar_port: "/dev/ttyACM0",
          baudrate: 150000,
          start_command_hex: "a5 60",
          stop_command_hex: "a5 00 a5 65 a5 65",
          scan_proof_latest: {
            artifact: { status: "loaded" },
            freshness: { status: "fresh", age_seconds: 12 },
            latest_proof_status: "blocked_or_not_observed",
            latest_scan_once_observed: false,
            latest_scan_hz_observed: false,
            latest_raw_packet_once_observed: false,
          },
          raw_packet_proof_latest: {
            endpoint: "/api/radar/raw-packet-proof/latest",
            http_status: 200,
            artifact: { status: "loaded" },
            freshness: { status: "fresh", age_seconds: 4 },
            latest_proof_status: "observed_raw_packet_material",
            latest_raw_bytes_observed: true,
            latest_sync_header_observed: true,
            latest_packet_parse_ok: true,
            latest_points_observed: true,
            latest_bytes_read: 4246,
            latest_sync_header_count: 127,
            latest_packets_parse_ok: 24,
            latest_points_total: 384,
          },
        },
        base: { port: "/dev/ttyS5", baudrate: 115200 },
      }),
    }));

    const response = (await buildO7LiveOperatorPanel()) as LiveOperatorWithBaseBoundary;

    expect(response.schema).toBe("trashbot.o7.live_operator_panel.v1");
    expect(response.ssh).toEqual({
      host: "192.168.1.11",
      port: 37878,
      reachable: true,
      workstation_api_8787_status: "ready",
    });
    expect(response.camera.base_url).toBe("http://192.168.1.11:8088/");
    expect(response.camera.health_status).toBe("ready");
    expect(response.camera.video_source).toBe("auto");
    expect(response.lidar_radar.dev_lidar).toBe("/dev/ttyACM0");
    expect(response.lidar_radar.stc_by_id).toBe("resolved_to_ttyACM0");
    expect(response.lidar_radar.scan_status).toBe("not_proven");
    expect(response.lidar_radar.pointcloud_fabricated).toBe(false);
    expect(response.lidar_radar.scan_proof_latest).toMatchObject({
      latest_scan_once_observed: false,
      latest_scan_hz_observed: false,
    });
    expect(response.lidar_radar.raw_packet_proof_latest).toMatchObject({
      endpoint: "/api/radar/raw-packet-proof/latest",
      http_status: 200,
      artifact_status: "loaded",
      freshness_status: "fresh",
      age_seconds: 4,
      latest_proof_status: "observed_raw_packet_material",
      latest_raw_bytes_observed: true,
      latest_sync_header_observed: true,
      latest_packet_parse_ok: true,
      latest_points_observed: true,
      latest_bytes_read: 4246,
      latest_sync_header_count: 127,
      latest_packets_parse_ok: 24,
      latest_points_total: 384,
      sends_commands: false,
      sends_motion_commands: false,
      robot_control_executed: false,
      safe_to_control: false,
      hil_pass: false,
      collector_executed_by_pc: false,
    });
    expect(response.realtime_radar).toMatchObject({
      title: "实时雷达 (/scan)",
      status: "blocked",
      ready: false,
      readiness_source: "scan_proof_once_and_hz_only",
      scan_once_observed: false,
      scan_hz_observed: false,
      raw_packet_ignored_for_ready: true,
      raw_packet_material_status: "observed_raw_packet_material",
      not_ready_reason: "scan_once_or_hz_not_observed",
      safe_to_control: false,
    });
    expect(response.realtime_radar.blocked_reasons).toEqual(expect.arrayContaining([
      "radar_scan_proof_blocked_or_not_observed",
      "scan_once_not_observed",
      "scan_hz_not_observed",
    ]));
    expect(response.realtime_map).toMatchObject({
      title: "实时图 (SLAM/map)",
      status: "waiting_for_radar",
      ready: false,
      depends_on_realtime_radar: true,
      map_artifact_status: "not_loaded",
      slam_artifact_status: "not_loaded",
      latest_map_observed: false,
      latest_slam_observed: false,
      blocked_reasons: ["realtime_radar_not_ready"],
      not_ready_reason: "waiting_for_radar",
      pointcloud_fabricated: false,
      safe_to_control: false,
    });
    expect(response.control.base_boundary).toEqual({
      observed_write_device: "/dev/ttyS5",
      baudrate: 115200,
      vendor_command_id: "T=1",
      feedback_request_id: "T=130",
      required_feedback_id: "T=1001",
      t1001_feedback_status: "not_observed_after_t130",
      manual_control_status: "fail_closed_display_only",
      forbidden_endpoint: "/api/base/manual",
      post_base_manual_enabled: false,
    });
    expect(response.control.command_dispatch_enabled).toBe(false);
    expect(response.control.sends_commands).toBe(false);
    expect(response.control.robot_ack_connected).toBe(false);
    expect(response.safe_to_control).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(response.delivery_success).toBe(false);
  });

  it("does not probe the camera service when no camera base URL is configured", async () => {
    const mockedFetch = vi.fn();
    vi.stubGlobal("fetch", mockedFetch);

    const response = await buildO7LocalWebrtcCamera({
      env: {
        ROBER_O7_BROWSER_SMOKE_RESULT_JSON: "/tmp/rober-missing-browser-smoke.json",
      },
    });

    expect(response.status).toBe("not_configured");
    expect(response.health_get_executed).toBe(false);
    expect(response.devices_get_executed).toBe(false);
    expect(response.offer_executed).toBe(false);
    expect(response.webrtc_session_created).toBe(false);
    expect(response.sends_commands).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  it("rejects camera offer proxy calls before configuration and keeps robot control fields false", async () => {
    const mockedFetch = vi.fn();
    vi.stubGlobal("fetch", mockedFetch);

    const result = await proxyO7LocalWebrtcCameraOffer({ type: "offer", sdp: "m=video\r\n" }, {});

    expect(result.status).toBe(400);
    expect(result.payload).toMatchObject({
      error: "base_url_not_configured",
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
    });
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  it("rejects invalid peer close ids locally instead of proxying arbitrary paths", async () => {
    const mockedFetch = vi.fn();
    vi.stubGlobal("fetch", mockedFetch);

    const result = await proxyO7LocalWebrtcCameraPeerClose("../../../api/base/manual", { reason: "test" }, {
      ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787",
    });

    expect(result.status).toBe(400);
    expect(result.payload).toMatchObject({
      error: "peer_id_invalid",
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
    });
    expect(mockedFetch).not.toHaveBeenCalled();
  });
});

describe("O7 direct upper PC API", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("uses the field default upper 8787 URL for status without env while keeping base controls explicit", async () => {
    const mockedFetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      return {
        ok: true,
        status: 200,
        json: async () =>
          url.endsWith("/health")
            ? { schema: "trashbot.upper_robot_api.health.v1", status: "ready" }
            : url.endsWith("/api/status")
              ? { camera: { status: "ready" }, radar: { scan_status: "not_proven" }, base: { write_control_available: false } }
              : { accepted: true, upper_path: url.replace("http://192.168.1.11:8787", "") },
      } as Response;
    });
    vi.stubGlobal("fetch", mockedFetch);

    const response = await buildO7DirectUpperStatus({ env: {} });
    const stop = await proxyO7DirectUpperStop({ env: {} });
    const feedback = await proxyO7DirectUpperFeedbackRequest({ env: {} });
    const manual = await proxyO7DirectUpperManual({
      env: {},
      body: { direction: "forward", speed: 0.04, duration_ms: 250, evidence_ref: "operator_field_report_pending" },
    });

    expect(response.status).toBe("ready");
    expect(response.upper_api_base_url).toBe("http://192.168.1.11:8787");
    expect(response.upper_api_base_url_source).toBe("field_default");
    expect(response.health_request.executed).toBe(true);
    expect(response.status_request.executed).toBe(true);
    expect(response.safety_flags.cloud_relay_bypassed).toBe(true);
    expect(response.safety_flags.pc_local_only).toBe(true);
    expect(response.safety_flags.production_4g_cloud_route_changed).toBe(false);
    expect(response.safe_to_control).toBe(false);
    expect(response.robot_control_executed).toBe(false);
    expect(stop.status).toBe(400);
    expect(stop.payload.upper_api_base_url_source).toBe("not_configured");
    expect(stop.payload.failure_reason).toBe("base_url_not_configured");
    expect(stop.payload.upper_request).toMatchObject({
      path: "/api/base/stop",
      executed: false,
      http_status: null,
      failure_reason: "base_url_not_configured",
    });
    expect(feedback.status).toBe(400);
    expect(feedback.payload.upper_api_base_url_source).toBe("not_configured");
    expect(feedback.payload.failure_reason).toBe("base_url_not_configured");
    expect(feedback.payload.upper_request).toMatchObject({
      path: "/api/base/feedback-request",
      executed: false,
      http_status: null,
      failure_reason: "base_url_not_configured",
    });
    expect(manual.status).toBe(400);
    expect(manual.payload.upper_api_base_url_source).toBe("not_configured");
    expect(manual.payload.failure_reason).toBe("base_url_not_configured");
    expect(manual.payload.upper_request).toMatchObject({
      path: "/api/base/manual",
      executed: false,
      http_status: null,
      failure_reason: "base_url_not_configured",
    });
    expect(manual.payload.command_payload_summary).toMatchObject({
      direction: "forward",
      speed_mps: 0.04,
      duration_ms: 250,
      evidence_ref: "operator_field_report_pending",
    });
    expect([stop, feedback, manual].every((result) => result.payload.safe_to_control === false)).toBe(true);
    expect([stop, feedback, manual].every((result) => result.payload.robot_ack_connected === false)).toBe(true);
    expect([stop, feedback, manual].every((result) => result.payload.t1001_observed === false)).toBe(true);
    expect([stop, feedback, manual].every((result) => result.payload.robot_control_executed === false)).toBe(true);
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toEqual([
      "http://192.168.1.11:8787/health",
      "http://192.168.1.11:8787/api/status",
    ]);
  });

  it("proxies radar start and stop through the field default upper 8787 URL without ACK/T1001 gating", async () => {
    const mockedFetch = vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      status: 200,
      json: async () => ({ accepted: true, upper_path: String(input).replace("http://192.168.1.11:8787", "") }),
    }) as Response);
    vi.stubGlobal("fetch", mockedFetch);

    const start = await proxyO7DirectUpperRadarStart({ env: {}, body: { evidence_ref: "o7-radar-default-url-test" } });
    const stop = await proxyO7DirectUpperRadarStop({ env: {}, body: { evidence_ref: "o7-radar-default-url-test" } });

    expect(start.status).toBe(200);
    expect(start.payload.upper_api_base_url).toBe("http://192.168.1.11:8787");
    expect(start.payload.upper_api_base_url_source).toBe("field_default");
    expect(start.payload.failure_reason).toBe("none");
    expect(start.payload.upper_request).toMatchObject({
      path: "/api/radar/start",
      method: "POST",
      executed: true,
      ok: true,
      http_status: 200,
      failure_reason: "",
    });
    expect(start.payload.blocked_reasons).toEqual([
      "robot_ack_not_connected",
      "t1001_feedback_not_observed",
      "field_evidence_not_proven",
    ]);
    expect(start.payload.safe_to_control).toBe(false);
    expect(start.payload.sends_commands).toBe(false);
    expect(start.payload.robot_control_executed).toBe(false);

    expect(stop.status).toBe(200);
    expect(stop.payload.upper_api_base_url_source).toBe("field_default");
    expect(stop.payload.failure_reason).toBe("none");
    expect(stop.payload.upper_request).toMatchObject({
      path: "/api/radar/stop",
      method: "POST",
      executed: true,
      ok: true,
      http_status: 200,
    });
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toEqual([
      "http://192.168.1.11:8787/api/radar/start",
      "http://192.168.1.11:8787/api/radar/stop",
    ]);
  });

  it("proxies read-only scan proof refresh through the field default route without claiming runtime success", async () => {
    const mockedFetch = vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      status: 200,
      json: async () => ({
        schema: "trashbot.upper_robot_api.radar_scan_proof_refresh.v1",
        status: "refreshed",
        proof_state: "scan_once_hz_raw_packet_tf_observed",
        artifact: { status: "loaded" },
        freshness: { status: "fresh", age_seconds: 0 },
        proof_summary: {
          proof_status: "scan_once_hz_raw_packet_tf_observed",
          scan_hz_average_rate_hz: 257.987,
          tf_observed: true,
          all_required_observations_observed: true,
        },
        latest_result: {
          proof: {
            runtime_summary_fallback_used: true,
            runtime_summary_path: "runtime/lidar_runtime_summary.json",
          },
        },
        continuous_scan_status: "not_proven",
        continuous_blocked_reasons: ["scan_continuity_not_observed"],
        requested_path: String(input).replace("http://192.168.1.11:8787", ""),
      }),
    }) as Response);
    vi.stubGlobal("fetch", mockedFetch);

    const refresh = await proxyO7DirectUpperRadarScanProofRefresh({
      env: {},
      body: { evidence_ref: "o7-scan-proof-refresh-field-default" },
    });

    expect(refresh.status).toBe(200);
    expect(refresh.payload.schema).toBe("trashbot.pc_tools_workstation.o7_direct_upper_radar_scan_proof_refresh.v1");
    expect(refresh.payload.command).toBe("radar_scan_proof_refresh");
    expect(refresh.payload.upper_api_base_url_source).toBe("field_default");
    expect(refresh.payload.upper_request).toMatchObject({
      path: "/api/radar/scan-proof/refresh",
      method: "POST",
      executed: true,
      ok: true,
      http_status: 200,
    });
    expect(refresh.payload.command_payload_summary.evidence_ref).toBe("o7-scan-proof-refresh-field-default");
    expect(refresh.payload.upper_result_summary).toMatchObject({
      status: "refreshed",
      proof_status: "scan_once_hz_raw_packet_tf_observed",
      latest_proof_status: "scan_once_hz_raw_packet_tf_observed",
      artifact_status: "loaded",
      artifact_path: "not_reported",
      freshness_status: "fresh",
      freshness_age_seconds: 0,
      fresh_scan_proof_observed: true,
      scan_hz_average_rate_hz: 257.987,
      tf_observed: true,
      all_required_observations_observed: true,
      runtime_summary_fallback_used: true,
      runtime_summary_path: "runtime/lidar_runtime_summary.json",
      continuous_scan_status: "not_proven",
      continuous_blocked_reasons: ["scan_continuity_not_observed"],
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      delivery_success: false,
      blocked_reasons: ["continuous_scan_status_not_proven", "scan_continuity_not_observed"],
      not_proven: ["continuous_radar_not_proven"],
    });
    expect(refresh.payload.fail_closed).toBe(true);
    expect(refresh.payload.not_proven).toEqual(expect.arrayContaining([
      "continuous_radar_not_proven",
      "driver_start_stop",
      "pc_wasd_control",
      "nav2_consumption",
      "slam_map",
      "delivery_success",
      "hil_pass",
    ]));
    expect(refresh.payload.safe_to_control).toBe(false);
    expect(refresh.payload.sends_commands).toBe(false);
    expect(refresh.payload.robot_control_executed).toBe(false);
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toEqual([
      "http://192.168.1.11:8787/api/radar/scan-proof/refresh",
    ]);
  });

  it("waits for slow upper scan proof refresh instead of using the short status timeout", async () => {
    const mockedFetch = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      void init?.signal;
      await new Promise((resolve) => setTimeout(resolve, 5));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          schema: "trashbot.upper_robot_api.radar_scan_proof_refresh.v1",
          status: "refreshed",
          proof_state: "scan_once_hz_raw_packet_tf_observed",
          latest_result: {
            proof: {
              status: "scan_once_hz_raw_packet_tf_observed",
              scan_hz_average_rate_hz: 175.443,
              tf_observed: true,
              all_required_observations_observed: true,
              runtime_summary_fallback_used: true,
              runtime_summary_path: "/tmp/o1_lidar_ros2_scan_smoke/summary.json",
            },
          },
          continuous_scan_status: "not_proven",
          continuous_blocked_reasons: ["scan_continuity_not_observed"],
          blockers_summary: [],
          safe_to_control: false,
          robot_control_executed: false,
        }),
      } as Response;
    });
    vi.stubGlobal("fetch", mockedFetch);

    const refresh = await proxyO7DirectUpperRadarScanProofRefresh({
      env: { ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787" },
    });

    expect(refresh.status).toBe(200);
    const firstCall = mockedFetch.mock.calls[0] as [RequestInfo | URL, RequestInit?] | undefined;
    const refreshSignal = firstCall?.[1]?.signal;
    expect(refreshSignal).toBeInstanceOf(AbortSignal);
    expect((refreshSignal as AbortSignal).aborted).toBe(false);
    expect(refresh.payload.upper_result_summary).toMatchObject({
      proof_status: "scan_once_hz_raw_packet_tf_observed",
      scan_hz_average_rate_hz: 175.443,
      tf_observed: true,
      runtime_summary_fallback_used: true,
      continuous_scan_status: "not_proven",
    });
  });

  it("proxies read-only scan proof latest as JSON instead of falling through to the SPA shell", async () => {
    const mockedFetch = vi.fn(async (_input: RequestInfo | URL) => ({
      ok: true,
      status: 200,
      json: async () => ({
        schema: "trashbot.upper_robot_api.v1.lidar_scan_proof_latest_result",
        artifact: { status: "loaded", path: "runtime/lidar_scan_proof_latest.json" },
        latest_result: {
          proof: {
            status: "scan_once_hz_raw_packet_tf_observed",
            scan_hz_average_rate_hz: 175.443,
            tf_observed: true,
            all_required_observations_observed: true,
            runtime_summary_fallback_used: true,
            runtime_summary_path: "/tmp/o1_lidar_ros2_scan_smoke/summary.json",
          },
        },
        safe_to_control: false,
        sends_commands: false,
        robot_control_executed: false,
      }),
    }) as Response);
    vi.stubGlobal("fetch", mockedFetch);

    const latest = await proxyO7DirectUpperRadarScanProofLatest({
      env: {},
      body: { evidence_ref: "o7-scan-proof-latest-field-default" },
    });

    expect(latest.status).toBe(200);
    expect(latest.payload.schema).toBe("trashbot.pc_tools_workstation.o7_direct_upper_radar_scan_proof_latest.v1");
    expect(latest.payload.endpoint).toBe("/api/o7/direct-upper/radar/scan-proof/latest");
    expect(latest.payload.command).toBe("radar_scan_proof_latest");
    expect(latest.payload.upper_api_base_url_source).toBe("field_default");
    expect(latest.payload.upper_request).toMatchObject({
      path: "/api/radar/scan-proof/latest",
      method: "GET",
      executed: true,
      ok: true,
      http_status: 200,
    });
    expect(latest.payload.upper_result_summary).toMatchObject({
      proof_status: "scan_once_hz_raw_packet_tf_observed",
      latest_proof_status: "scan_once_hz_raw_packet_tf_observed",
      artifact_status: "loaded",
      scan_hz_average_rate_hz: 175.443,
      tf_observed: true,
      all_required_observations_observed: true,
      runtime_summary_fallback_used: true,
      continuous_scan_status: "not_proven",
      safe_to_control: false,
      robot_control_executed: false,
    });
    expect(latest.payload.not_proven).toEqual(expect.arrayContaining(["continuous_radar_not_proven", "hil_pass"]));
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toEqual([
      "http://192.168.1.11:8787/api/radar/scan-proof/latest",
    ]);
  });

  it("surfaces upper scan proof not_proven summary on HTTP 200 without marking refresh complete", async () => {
    const mockedFetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        schema: "trashbot.upper_robot_api.radar_scan_proof_refresh.v1",
        status: "not_proven",
        proof_status: "not_proven",
        latest_proof_status: "blocked_or_not_observed",
        artifact: { status: "loaded", path: "artifacts/radar/scan-proof-latest.json" },
        freshness: { status: "fresh", age_seconds: 2 },
        latest_scan_hz_average_rate_hz: 257.987,
        latest_tf_observed: true,
        latest_all_required_observations_observed: true,
        runtime_summary_fallback_used: true,
        runtime_summary_path: "runtime/lidar_runtime_summary.json",
        continuous_scan_status: "not_proven",
        continuous_blocked_reasons: ["scan_continuity_not_observed"],
        blockers: ["ros2_command_unavailable"],
        blocked_reasons: ["upper_api_scan_not_proven"],
        not_proven: ["upper_api_scan_not_proven"],
        safe_to_control: false,
        sends_commands: false,
        robot_control_executed: false,
      }),
    }) as Response);
    vi.stubGlobal("fetch", mockedFetch);

    const refresh = await proxyO7DirectUpperRadarScanProofRefresh({
      env: {},
      body: { evidence_ref: "o7-scan-proof-refresh-not-proven" },
    });

    expect(refresh.status).toBe(200);
    expect(refresh.payload.accepted_by_workstation).toBe(true);
    expect(refresh.payload.failure_reason).toBe("none");
    expect(refresh.payload.fail_closed).toBe(true);
    expect(refresh.payload.upper_request).toMatchObject({
      path: "/api/radar/scan-proof/refresh",
      method: "POST",
      executed: true,
      ok: true,
      http_status: 200,
      failure_reason: "",
    });
    expect(refresh.payload.upper_result_summary).toMatchObject({
      status: "not_proven",
      proof_status: "not_proven",
      latest_proof_status: "blocked_or_not_observed",
      artifact_status: "loaded",
      artifact_path: "artifacts/radar/scan-proof-latest.json",
      freshness_status: "fresh",
      freshness_age_seconds: 2,
      scan_hz_average_rate_hz: 257.987,
      tf_observed: true,
      all_required_observations_observed: true,
      runtime_summary_fallback_used: true,
      runtime_summary_path: "runtime/lidar_runtime_summary.json",
      continuous_scan_status: "not_proven",
      continuous_blocked_reasons: ["scan_continuity_not_observed"],
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      delivery_success: false,
      blocked_reasons: [
        "ros2_command_unavailable",
        "upper_api_scan_not_proven",
        "continuous_scan_status_not_proven",
        "scan_continuity_not_observed",
      ],
      not_proven: ["upper_api_scan_not_proven", "continuous_radar_not_proven"],
    });
    expect(refresh.payload.blocked_reasons).toEqual(expect.arrayContaining([
      "ros2_command_unavailable",
      "upper_api_scan_not_proven",
      "continuous_scan_status_not_proven",
      "scan_continuity_not_observed",
      "robot_ack_not_connected",
      "t1001_feedback_not_observed",
      "field_evidence_not_proven",
    ]));
    expect(refresh.payload.not_proven).toEqual(expect.arrayContaining([
      "upper_api_scan_not_proven",
      "continuous_radar_not_proven",
      "driver_start_stop",
      "pc_wasd_control",
      "nav2_consumption",
      "slam_map",
      "delivery_success",
      "hil_pass",
    ]));
    expect(refresh.payload.safe_to_control).toBe(false);
    expect(refresh.payload.sends_commands).toBe(false);
    expect(refresh.payload.robot_control_executed).toBe(false);
  });

  it("keeps map/localize off the field default route while allowing operator report readback", async () => {
    const mockedFetch = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      const body = init?.body ? JSON.parse(String(init.body)) as { evidence_ref?: string; note?: string } : {};
      return {
        ok: true,
        status: 200,
        json: async () => ({
          schema: "trashbot.upper_robot_api.operator_report.v1",
          evidence_ref: body.evidence_ref ?? "o7-report-field-default",
          operator_report_status: init?.method === "GET" ? "ready_for_review" : "unsafe_or_incomplete",
        }),
      } as Response;
    });
    vi.stubGlobal("fetch", mockedFetch);

    const mapStart = await proxyO7DirectUpperMapStart({ env: {}, body: { evidence_ref: "o7-map-no-env" } });
    const localizeReset = await proxyO7DirectUpperLocalizeReset({ env: {}, body: { evidence_ref: "o7-localize-no-env" } });
    const reportPost = await proxyO7DirectUpperOperatorReport({
      env: {},
      body: { evidence_ref: "o7-report-field-default", note: "field default report write/readback" },
    });
    const reportReadback = await proxyO7DirectUpperOperatorReportReadback({
      env: {},
      body: { evidence_ref: "o7-report-field-default" },
    });

    expect(mapStart.status).toBe(400);
    expect(mapStart.payload.failure_reason).toBe("base_url_not_configured");
    expect(mapStart.payload.upper_api_base_url_source).toBe("not_configured");
    expect(mapStart.payload.upper_request.executed).toBe(false);
    expect(localizeReset.status).toBe(400);
    expect(localizeReset.payload.failure_reason).toBe("base_url_not_configured");
    expect(localizeReset.payload.upper_request.executed).toBe(false);

    expect(reportPost.status).toBe(200);
    expect(reportPost.payload.upper_api_base_url).toBe("http://192.168.1.11:8787");
    expect(reportPost.payload.upper_api_base_url_source).toBe("field_default");
    expect(reportPost.payload.upper_request).toMatchObject({
      path: "/api/operator/report",
      method: "POST",
      executed: true,
      ok: true,
      http_status: 200,
    });
    expect(reportPost.payload.command_payload_summary).toMatchObject({
      evidence_ref: "o7-report-field-default",
      report_note: "field default report write/readback",
    });
    expect(reportPost.payload.safe_to_control).toBe(false);
    expect(reportPost.payload.robot_control_executed).toBe(false);

    expect(reportReadback.status).toBe(200);
    expect(reportReadback.payload.upper_request).toMatchObject({
      path: "/api/operator/report",
      method: "GET",
      executed: true,
      ok: true,
      http_status: 200,
    });
    expect(reportReadback.payload.upper_api_base_url_source).toBe("field_default");
    expect(reportReadback.payload.safe_to_control).toBe(false);
    expect(reportReadback.payload.robot_control_executed).toBe(false);
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toEqual([
      "http://192.168.1.11:8787/api/operator/report",
      "http://192.168.1.11:8787/api/operator/report",
    ]);
  });

  it("keeps map/localize fixture mode explicit without operator report upper fetch", async () => {
    const mockedFetch = vi.fn();
    vi.stubGlobal("fetch", mockedFetch);

    const mapSaveFixture = await proxyO7DirectUpperMapSave({
      env: {},
      body: { evidence_ref: "o7-map-fixture", map_id: "field-map-a", fixture_mode: true },
    });
    const mapListFixture = await proxyO7DirectUpperMapList({
      env: {},
      body: { evidence_ref: "o7-map-fixture", fixture_mode: true },
    });
    const localizeFixture = await proxyO7DirectUpperLocalizeReset({
      env: {},
      body: { evidence_ref: "o7-localize-fixture", fixture_mode: true },
    });
    const reportFixture = await proxyO7DirectUpperOperatorReport({
      env: {},
      body: { evidence_ref: "o7-report-fixture", note: "fixture only", fixture_mode: true },
    });

    expect(mapSaveFixture.status).toBe(200);
    expect(mapSaveFixture.payload.upper_api_base_url_source).toBe("fixture");
    expect(mapSaveFixture.payload.upper_request).toMatchObject({
      path: "/api/map/save",
      executed: false,
      ok: true,
      failure_reason: "fixture_mode_no_upper_fetch",
    });
    expect(mapSaveFixture.payload.command_payload_summary).toMatchObject({
      map_id: "field-map-a",
      evidence_ref: "o7-map-fixture",
    });
    expect(mapSaveFixture.payload.blocked_reasons).toEqual(expect.arrayContaining([
      "fixture_mode_no_upper_runtime",
      "field_evidence_not_proven",
    ]));

    expect(mapListFixture.payload.upper_request).toMatchObject({ path: "/api/map/list", method: "GET", executed: false });
    expect(localizeFixture.payload.upper_request.path).toBe("/api/localize/reset");
    expect(reportFixture.payload.command_payload_summary).toMatchObject({
      evidence_ref: "o7-report-fixture",
      report_note: "fixture only",
    });
    expect(reportFixture.payload.safe_to_control).toBe(false);
    expect(reportFixture.payload.robot_control_executed).toBe(false);
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  it("summarizes /health and /api/status from upper 8787 without claiming ACK or HIL", async () => {
    const mockedFetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      return {
        ok: true,
        status: 200,
        json: async () =>
          url.endsWith("/health")
            ? { schema: "trashbot.upper_robot_api.health.v1", status: "ready" }
            : {
                camera: { status: "ready" },
                radar: {
                  scan_status: "not_proven",
                  observed_lidar_port: "/dev/ttyACM0",
                  latest_scan_proof: {
                    observed: true,
                    scan_hz_average_rate_hz: 244.481,
                    tf_observed: true,
                    all_required_observations_observed: true,
                    runtime_summary_fallback_used: true,
                    runtime_summary_path: "runtime/lidar_runtime_summary.json",
                  },
                  continuous_scan_status: "not_proven",
                  continuous_blockers: ["scan_continuity_not_observed"],
                  raw_packet_proof_latest: {
                    artifact: { status: "loaded" },
                    freshness: { status: "fresh", age_seconds: 5 },
                    latest_proof_status: "observed_raw_packet_material",
                    latest_bytes_read: 4246,
                    latest_sync_header_count: 127,
                    latest_packets_parse_ok: 24,
                    latest_points_total: 384,
                  },
                },
                base: { port: "/dev/ttyS5", baudrate: 115200, write_control_available: true },
              },
      } as Response;
    });
    vi.stubGlobal("fetch", mockedFetch);

    const response = await buildO7DirectUpperStatus({
      env: { ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787/" },
    });

    expect(response.status).toBe("ready");
    expect(response.upper_api_base_url).toBe("http://127.0.0.1:8787");
    expect(response.upper_status_summary).toMatchObject({
      camera_status: "ready",
      radar_scan_status: "not_proven",
      radar_scan_proof_fresh_observed: true,
      radar_scan_proof_hz_average_rate_hz: 244.481,
      radar_scan_proof_tf_observed: true,
      radar_scan_proof_all_required_observations_observed: true,
      radar_scan_proof_runtime_summary_fallback_used: true,
      radar_scan_proof_runtime_summary_path: "runtime/lidar_runtime_summary.json",
      radar_continuous_scan_status: "not_proven",
      radar_continuous_blockers: ["scan_continuity_not_observed"],
      radar_raw_packet_proof_artifact_status: "loaded",
      radar_raw_packet_proof_freshness_status: "fresh",
      radar_raw_packet_proof_age_seconds: 5,
      radar_raw_packet_proof_latest_status: "observed_raw_packet_material",
      radar_raw_packet_proof_bytes_read: 4246,
      radar_raw_packet_proof_sync_header_count: 127,
      radar_raw_packet_proof_packets_parse_ok: 24,
      radar_raw_packet_proof_points_total: 384,
      radar_raw_packet_proof_safe_to_control: false,
      lidar_port: "/dev/ttyACM0",
      map_lifecycle_status: "not_loaded",
      map_artifact_ref: "not_loaded",
      localization_status: "not_loaded",
      operator_report_evidence_ref: "missing_operator_report",
      base_port: "/dev/ttyS5",
      base_baudrate: 115200,
      base_write_control_available: true,
      robot_ack_connected: false,
      t1001_observed: false,
    });
    expect(response.local_api_paths.manual).toBe("/api/o7/direct-upper/base/manual");
    expect(response.local_api_paths.feedback_request).toBe("/api/o7/direct-upper/base/feedback-request");
    expect(response.local_api_paths.radar_start).toBe("/api/o7/direct-upper/radar/start");
    expect(response.local_api_paths.scan_proof_refresh).toBe("/api/o7/direct-upper/radar/scan-proof/refresh");
    expect(response.local_api_paths.scan_proof_latest).toBe("/api/o7/direct-upper/radar/scan-proof/latest");
    expect(response.local_api_paths.map_save).toBe("/api/o7/direct-upper/map/save");
    expect(response.local_api_paths.localize_reset).toBe("/api/o7/direct-upper/localize/reset");
    expect(response.local_api_paths.operator_report).toBe("/api/o7/direct-upper/operator-report");
    expect(response.safety_flags.robot_control_executed).toBe(false);
    expect(mockedFetch.mock.calls.map(([url]) => String(url))).toEqual([
      "http://127.0.0.1:8787/health",
      "http://127.0.0.1:8787/api/status",
    ]);
  });

  it("keeps stop fail-closed when upper /api/base/stop fails", async () => {
    const mockedFetch = vi.fn(async () => ({
      ok: false,
      status: 503,
      json: async () => ({ error: "serial_unavailable" }),
    }) as Response);
    vi.stubGlobal("fetch", mockedFetch);

    const result = await proxyO7DirectUpperStop({
      env: { ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787" },
    });

    expect(result.status).toBe(502);
    expect(result.payload.fail_closed).toBe(true);
    expect(result.payload.upper_request).toMatchObject({
      path: "/api/base/stop",
      method: "POST",
      executed: true,
      ok: false,
      http_status: 503,
    });
    expect(result.payload.robot_ack_connected).toBe(false);
    expect(result.payload.t1001_observed).toBe(false);
    expect(result.payload.robot_control_executed).toBe(false);
  });

  it("proxies feedback-request as non-motion T=130 request without claiming T=1001 or ACK", async () => {
    const mockedFetch = vi.fn(async (_input: RequestInfo | URL) => {
      void _input;
      return {
        ok: true,
        status: 200,
        json: async () => ({ request_sent: true, feedback_ack: { t1001_observed: true } }),
      } as Response;
    });
    vi.stubGlobal("fetch", mockedFetch);

    const result = await proxyO7DirectUpperFeedbackRequest({
      env: { ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787/" },
    });

    expect(result.status).toBe(200);
    expect(result.payload.schema).toBe("trashbot.pc_tools_workstation.o7_direct_upper_feedback_request.v1");
    expect(result.payload.command).toBe("feedback_request");
    expect(result.payload.upper_request).toMatchObject({
      path: "/api/base/feedback-request",
      method: "POST",
      executed: true,
      ok: true,
      http_status: 200,
    });
    expect(result.payload.command_payload_summary).toMatchObject({
      direction: "not_applicable",
      speed_mps: 0,
      duration_ms: 0,
      feedback_request_id: "T=130",
      required_feedback_id: "T=1001",
    });
    expect(result.payload.robot_ack_connected).toBe(false);
    expect(result.payload.t1001_observed).toBe(false);
    expect(result.payload.safe_to_control).toBe(false);
    expect(result.payload.robot_control_executed).toBe(false);
    expect(String(mockedFetch.mock.calls[0]?.[0])).toBe("http://127.0.0.1:8787/api/base/feedback-request");
  });

  it("keeps feedback-request fail-closed on bad upper JSON", async () => {
    const mockedFetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => "not an object",
    }) as Response);
    vi.stubGlobal("fetch", mockedFetch);

    const result = await proxyO7DirectUpperFeedbackRequest({
      env: { ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787" },
    });

    expect(result.status).toBe(502);
    expect(result.payload.fail_closed).toBe(true);
    expect(result.payload.failure_reason).toBe("bad_json");
    expect(result.payload.upper_request).toMatchObject({
      path: "/api/base/feedback-request",
      executed: true,
      ok: false,
      http_status: 200,
      failure_reason: "bad_json",
    });
    expect(result.payload.safe_to_control).toBe(false);
    expect(result.payload.robot_control_executed).toBe(false);
  });

  it("rejects invalid manual direction locally before any upper fetch", async () => {
    const mockedFetch = vi.fn();
    vi.stubGlobal("fetch", mockedFetch);

    const result = await proxyO7DirectUpperManual({
      env: { ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787" },
      body: { direction: "../../../api/base/manual", speed: 9, duration_ms: 999_000 },
    });

    expect(result.status).toBe(400);
    expect(result.payload.failure_reason).toBe("invalid_direction");
    expect(result.payload.accepted_by_workstation).toBe(false);
    expect(result.payload.upper_request.executed).toBe(false);
    expect(result.payload.command_payload_summary.direction).toBe("not_applicable");
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  it("clamps manual speed and duration before forwarding to the upper 8787 guardrail", async () => {
    const mockedFetch = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => ({
      ok: true,
      status: 200,
      json: async () => ({ accepted: true, feedback_ack: { t1001_observed: false } }),
      request_body: init?.body,
    }) as Response & { request_body?: BodyInit | null });
    vi.stubGlobal("fetch", mockedFetch);

    const result = await proxyO7DirectUpperManual({
      env: { ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787/" },
      body: { direction: "forward", speed: 0.5, duration_ms: 900_000 },
    });

    expect(result.status).toBe(200);
    expect(result.payload.accepted_by_workstation).toBe(true);
    expect(result.payload.fail_closed).toBe(false);
    expect(result.payload.command_payload_summary).toEqual({
      direction: "forward",
      speed_mps: 0.08,
      duration_ms: 350,
      clamped_by_pc: true,
      depends_on_upper_8787_guardrail: true,
      evidence_ref: "missing_operator_evidence_ref",
    });
    expect(result.payload.robot_ack_connected).toBe(false);
    expect(result.payload.t1001_observed).toBe(false);
    expect(result.payload.robot_control_executed).toBe(false);
    expect(mockedFetch).toHaveBeenCalledTimes(1);
    expect(String(mockedFetch.mock.calls[0]?.[0])).toBe("http://127.0.0.1:8787/api/base/manual");
    expect(JSON.parse(String(mockedFetch.mock.calls[0]?.[1]?.body))).toEqual({
      direction: "forward",
      speed: 0.08,
      duration_ms: 350,
    });
  });

  it("records manual fixture pulses without fetching upper 8787 or claiming HIL", async () => {
    const mockedFetch = vi.fn();
    vi.stubGlobal("fetch", mockedFetch);

    const result = await proxyO7DirectUpperManual({
      env: {},
      body: {
        direction: "left",
        speed: 0.5,
        duration_ms: 900_000,
        evidence_ref: "o7-manual-fixture",
        fixture_mode: true,
      },
    });

    expect(result.status).toBe(200);
    expect(result.payload.upper_api_base_url_source).toBe("fixture");
    expect(result.payload.upper_request).toMatchObject({
      path: "/api/base/manual",
      executed: false,
      ok: true,
      failure_reason: "fixture_mode_no_upper_fetch",
    });
    expect(result.payload.command_payload_summary).toEqual({
      direction: "left",
      speed_mps: 0.08,
      duration_ms: 350,
      clamped_by_pc: true,
      depends_on_upper_8787_guardrail: true,
      evidence_ref: "o7-manual-fixture",
    });
    expect(result.payload.safe_to_control).toBe(false);
    expect(result.payload.robot_control_executed).toBe(false);
    expect(result.payload.not_proven).toContain("upper_8787_runtime");
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  it("keeps manual proxy alive past the short status timeout so upper auto-stop feedback can return", async () => {
    vi.useFakeTimers();
    const mockedFetch = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => new Promise<Response>((resolve, reject) => {
      // manual 的远端窗口需要覆盖运动 pulse、自动停车和 T=130/T=1001 回读，不能复用 status 的 1.2s 短超时。
      const signal = init?.signal;
      signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      setTimeout(() => {
        resolve({
          ok: true,
          status: 200,
          json: async () => ({ accepted: true, auto_stop: { posted: true }, feedback_ack: { t1001_observed: false } }),
        } as Response);
      }, 1300);
    }));
    vi.stubGlobal("fetch", mockedFetch);

    const resultPromise = proxyO7DirectUpperManual({
      env: { ROBER_UPPER_API_BASE_URL: "http://127.0.0.1:8787" },
      body: { direction: "right", speed: 0.08, duration_ms: 350 },
    });
    await vi.advanceTimersByTimeAsync(1300);
    const result = await resultPromise;

    expect(result.status).toBe(200);
    expect(result.payload.accepted_by_workstation).toBe(true);
    expect(result.payload.upper_request).toMatchObject({
      path: "/api/base/manual",
      executed: true,
      ok: true,
      http_status: 200,
      failure_reason: "",
    });
  });

  it("keeps map waiting for mapping when /scan once and hz are observed but no SLAM map artifact exists", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        camera: { status: "ready", video_source: "auto" },
        radar: {
          observed_lidar_port: "/dev/ttyACM0",
          scan_proof_latest: {
            artifact: { status: "loaded" },
            freshness: { status: "fresh", age_seconds: 2 },
            latest_proof_status: "scan_once_hz_observed",
            latest_scan_once_observed: true,
            latest_scan_hz_observed: true,
            latest_raw_packet_once_observed: false,
          },
          raw_packet_proof_latest: {
            artifact: { status: "loaded" },
            freshness: { status: "fresh", age_seconds: 2 },
            latest_proof_status: "observed_raw_packet_material",
            latest_raw_bytes_observed: true,
          },
        },
        base: { port: "/dev/ttyS5", baudrate: 115200 },
      }),
    }));

    const response = await buildO7LiveOperatorPanel();

    expect(response.realtime_radar).toMatchObject({
      status: "ready",
      ready: true,
      scan_once_observed: true,
      scan_hz_observed: true,
      raw_packet_ignored_for_ready: true,
      blocked_reasons: [],
      not_ready_reason: "none",
    });
    expect(response.realtime_map).toMatchObject({
      status: "waiting_for_mapping",
      ready: false,
      map_artifact_status: "not_loaded",
      slam_artifact_status: "not_loaded",
      latest_map_observed: false,
      latest_slam_observed: false,
      blocked_reasons: ["slam_map_artifact_not_observed"],
      not_ready_reason: "waiting_for_mapping",
    });
  });
});
