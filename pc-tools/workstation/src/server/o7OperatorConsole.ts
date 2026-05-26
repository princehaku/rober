import { PROOF_FLAGS } from "../shared/contracts";
import type { O7OperatorConsoleResponse, O7OperatorKrView } from "../shared/contracts";

const CONTRACT_SOURCE = "cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py" as const;

const KR_VIEWS: O7OperatorKrView[] = [
  {
    id: "O7-KR1",
    title: "实时地图与机器人位置",
    status: "blocked",
    cloud_contract: "realtime.map_pose.v1",
    pc_surface: "Map/Pose panel",
    current_view: ["map_ref=draft", "pose=not_proven", "route_membership=blocked"],
    blocked_by: ["cloud realtime stream not connected", "ROS2 /tf forwarding not proven"],
    next_required_contract: "Cloud must expose robot pose snapshots with map frame and freshness timestamp.",
  },
  {
    id: "O7-KR2",
    title: "电梯状态展示",
    status: "blocked",
    cloud_contract: "realtime.elevator_state.v1",
    pc_surface: "Elevator state panel",
    current_view: ["state_chain=draft", "floor_evidence=not_proven", "handoff_reason=blocked"],
    blocked_by: ["elevator event archive not connected", "real elevator evidence not proven"],
    next_required_contract: "Cloud must expose elevator state chain and evidence refs per task.",
  },
  {
    id: "O7-KR3",
    title: "历史路线回放",
    status: "draft",
    cloud_contract: "history.route_replay.v1",
    pc_surface: "Route replay panel",
    current_view: ["task_selector=draft", "trajectory_frames=not_proven", "playback=blocked"],
    blocked_by: ["cloud task archive query not connected", "trajectory frame schema pending"],
    next_required_contract: "Cloud must expose task list, trajectory frames, and timestamped state transitions.",
  },
  {
    id: "O7-KR4",
    title: "数据标注/打标界面",
    status: "draft",
    cloud_contract: "labeling.review_queue.v1",
    pc_surface: "Labeling queue panel",
    current_view: ["queue=draft", "label_schema=not_proven", "submit=blocked"],
    blocked_by: ["annotation API not connected", "training dataset export not proven"],
    next_required_contract: "Cloud must expose review queue, label schema, and submit/rollback audit trail.",
  },
  {
    id: "O7-KR5",
    title: "实时 ASR 监听 + TTS 发言控制",
    status: "blocked",
    cloud_contract: "voice.asr_tts_operator.v1",
    pc_surface: "Voice monitor panel",
    current_view: ["asr_stream=blocked", "tts_draft=not_proven", "speaker_dispatch=blocked"],
    blocked_by: ["ASR event stream not connected", "TTS command ACK contract pending"],
    next_required_contract: "Cloud must expose ASR transcript events and TTS draft command ACK without direct robot control.",
  },
  {
    id: "O7-KR6",
    title: "手动转向控制 + 自动寻路下发",
    status: "blocked",
    cloud_contract: "operator.safe_command_preview.v1",
    pc_surface: "Safe command preview panel",
    current_view: ["manual_control=blocked", "navigate_goal=blocked", "ack=not_proven"],
    blocked_by: ["safe command dispatch disabled", "robot-side ACK and recovery path not proven"],
    next_required_contract: "Cloud must expose idempotent safe command API with confirmation, ACK, timeout, and cancel recovery.",
  },
];

export function buildO7OperatorConsoleResponse(): O7OperatorConsoleResponse {
  // 这里与 cloud-relay helper 固定同一 schema；PC 只消费契约快照，不连接小车。
  // 六个 KR 都保留 draft/blocked/not_proven，避免 UI 把占位面板外推成真实 O7 能力。
  return {
    schema: "trashbot.o7.operator_console.v1",
    ...PROOF_FLAGS,
    contract_source: CONTRACT_SOURCE,
    workstation_endpoint: "/api/o7/operator-console",
    cloud_api_status: "draft_blocked_not_proven",
    robot_connection: "not_connected_by_pc",
    realtime_stream_status: "blocked_not_proven",
    operator_mode: "observe_only",
    manual_control_policy: {
      pc_direct_robot_connection: false,
      cloud_mediated_only: true,
      command_dispatch_enabled: false,
      confirmation_required_before_future_dispatch: true,
      success_claim_allowed: false,
    },
    kr_views: KR_VIEWS,
    command_previews: [
      {
        id: "manual_turn_preview",
        label: "Manual turn envelope",
        status: "blocked_not_proven",
        requires_confirmation: true,
        sends_to_robot: false,
        cloud_endpoint: "POST /api/o7/operator/commands/manual-turn (future, disabled)",
        recovery_path: "Keep observe_only mode until Robot/Hardware provide ACK, timeout, and stop evidence.",
      },
      {
        id: "navigate_goal_preview",
        label: "Navigate goal envelope",
        status: "blocked_not_proven",
        requires_confirmation: true,
        sends_to_robot: false,
        cloud_endpoint: "POST /api/o7/operator/commands/navigate-goal (future, disabled)",
        recovery_path: "Require cloud idempotency key, robot ACK, cancel path, and task archive evidence before enabling.",
      },
      {
        id: "tts_preview",
        label: "TTS utterance envelope",
        status: "blocked_not_proven",
        requires_confirmation: true,
        sends_to_robot: false,
        cloud_endpoint: "POST /api/o7/operator/voice/tts (future, disabled)",
        recovery_path: "Require cloud TTS ACK and speaker-side failure event before any dispatch UI.",
      },
    ],
    blocked_reasons: [
      "cloud_realtime_api_draft",
      "pc_must_not_direct_connect_robot",
      "robot_ack_timeout_recovery_not_proven",
      "real_map_pose_stream_not_proven",
      "real_voice_stream_not_proven",
      "manual_or_navigation_dispatch_disabled",
    ],
    not_proven: [
      "real_o7_realtime_cloud_stream",
      "real_robot_position_latency_lt_2s",
      "real_elevator_state_chain",
      "real_route_replay_archive",
      "real_annotation_submit_api",
      "real_asr_tts_runtime",
      "real_operator_safe_command_dispatch",
      "delivery_success",
    ],
    recovery_paths: [
      "Connect O6 cloud archive and realtime stream before replacing draft values.",
      "Ask Robot Software for robot-side ACK, timeout, cancel, and stop evidence before enabling commands.",
      "Ask Hardware for HIL/safety evidence before treating manual control as safe.",
    ],
  };
}
