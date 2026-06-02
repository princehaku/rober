import { PROOF_FLAGS } from "../shared/contracts";
import type { O7LiveOperatorPanelResponse } from "../shared/contracts";

const ENDPOINT = "/api/o7/live-operator-panel" as const;

const BLOCKED_REASONS = [
  "base_serial_identity_not_proven",
  "t1001_feedback_not_observed",
  "robot_ack_not_connected",
] as const;

export function buildO7LiveOperatorPanel(): O7LiveOperatorPanelResponse {
  // 这个面板只把已观测事实产品化展示，不探测串口、不请求 /offer、不发送任何底盘控制。
  return {
    schema: "trashbot.o7.live_operator_panel.v1",
    endpoint: ENDPOINT,
    ...PROOF_FLAGS,
    ssh: {
      // SSH 可达来自本轮只读联调口径；8787 未监听必须继续显示为 blocked。
      host: "192.168.1.11",
      port: 37878,
      reachable: true,
      workstation_api_8787_status: "not_listening_observed",
    },
    lidar_radar: {
      // /dev/lidar 缺失和 STC by-id 未证明底盘身份时，不能伪造点云或雷达状态。
      dev_lidar: "missing",
      stc_by_id: "unresolved",
      scan_status: "not_proven",
      pointcloud_fabricated: false,
      source_facts: [
        "remote /dev/lidar not listed",
        "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 points to ttyACM0 but identity is not proven as base",
        "T=1001 WAVE ROVER feedback has not been observed",
      ],
      blocked_reasons: [...BLOCKED_REASONS],
    },
    camera: {
      // 兼容既有 live 面板合同；实时 health/devices 由 local camera API 按 env 拉取。
      base_url: "http://192.168.1.11:8088/",
      health_status: "not_listening_observed",
      video_source: "/dev/video1",
      devices_summary: [
        "set ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/ on the PC dev server",
        "GET /api/o7/local-webrtc-camera performs readonly GET /health and GET /devices",
        "the workstation API does not POST /offer and does not create WebRTC sessions",
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
}
