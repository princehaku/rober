import { PROOF_FLAGS } from "../shared/contracts";
import type {
  O7OperatorConsoleAcceptanceCheck,
  O7OperatorConsoleAcceptanceResponse,
  O7OperatorConsoleResponse,
  O7OperatorConsoleSnapshotKey,
} from "../shared/contracts";
import { buildO7OperatorConsoleResponse } from "./o7OperatorConsole";

const SNAPSHOT_SCHEMA_KEYS: O7OperatorConsoleSnapshotKey[] = [
  "board_media_preflight_summary",
  "realtime_map_snapshot",
  "elevator_state_snapshot",
  "route_replay_snapshot",
  "labeling_queue_snapshot",
  "voice_asr_tts_snapshot",
  "safe_command_snapshot",
];

const KR_SNAPSHOT_KEYS: O7OperatorConsoleSnapshotKey[] = [
  "realtime_map_snapshot",
  "elevator_state_snapshot",
  "route_replay_snapshot",
  "labeling_queue_snapshot",
  "voice_asr_tts_snapshot",
  "safe_command_snapshot",
];

const DANGEROUS_MARKERS = [
  {
    id: "raw_cmd_vel_topic",
    pattern: /\/cmd_vel/i,
  },
  {
    id: "usb_or_acm_serial_device",
    pattern: /\/dev\/tty(?:USB|ACM)\d*/i,
  },
  {
    id: "operator_greenlight_phrase",
    pattern: /ready[-_ ]?to[-_ ]?control/i,
  },
  {
    id: "true_delivery_claim",
    pattern: /delivery_success["'\s:=]+true/i,
  },
  {
    id: "true_control_claim",
    pattern: /success_claim_allowed["'\s:=]+true/i,
  },
  {
    id: "true_green_result_claim",
    pattern: /\b(?:pass|passed|success)["'\s:=]+true\b/i,
  },
];

function makeFalseCheck(id: string, actual: false): O7OperatorConsoleAcceptanceCheck {
  // guard 只接受 literal false；如果未来类型变宽，编译和测试都会逼出显式改动。
  return {
    id,
    status: "blocked_not_proven",
    expected: false,
    actual,
  };
}

function assertAllFalse(checks: O7OperatorConsoleAcceptanceCheck[]): void {
  // 这里直接抛错是为了让 route/test 在安全开关漂移时失败，而不是返回模糊摘要。
  const drifted = checks.filter((check) => check.actual !== false);
  if (drifted.length > 0) {
    throw new Error(`o7_acceptance_guard_fail_closed_drift:${drifted.map((check) => check.id).join(",")}`);
  }
}

function snapshotSchemas(response: O7OperatorConsoleResponse): Record<O7OperatorConsoleSnapshotKey, string> {
  // schema 清单从 source response 读取，避免 acceptance helper 维护第二份 O7 事实。
  return {
    board_media_preflight_summary: response.board_media_preflight_summary.schema,
    realtime_map_snapshot: response.realtime_map_snapshot.schema,
    elevator_state_snapshot: response.elevator_state_snapshot.schema,
    route_replay_snapshot: response.route_replay_snapshot.schema,
    labeling_queue_snapshot: response.labeling_queue_snapshot.schema,
    voice_asr_tts_snapshot: response.voice_asr_tts_snapshot.schema,
    safe_command_snapshot: response.safe_command_snapshot.schema,
  };
}

function dangerousMarkerIds(response: O7OperatorConsoleResponse): string[] {
  // 扫描序列化后的只读响应，重点找危险外推短语和真实控制入口。
  const payload = JSON.stringify(response);
  return DANGEROUS_MARKERS.filter((marker) => marker.pattern.test(payload)).map((marker) => marker.id);
}

export function buildO7OperatorConsoleAcceptanceResponse(): O7OperatorConsoleAcceptanceResponse {
  // Acceptance 只复核 buildO7OperatorConsoleResponse() 的 fail-closed 输出，不读取设备或云端。
  const source = buildO7OperatorConsoleResponse();
  const schemas = snapshotSchemas(source);
  const presentKrSchemas = KR_SNAPSHOT_KEYS.map((key) => schemas[key]);
  const matchedMarkers = dangerousMarkerIds(source);
  const failClosedChecks: O7OperatorConsoleAcceptanceCheck[] = [
    makeFalseCheck("top_level_safe_to_control", source.safe_to_control),
    makeFalseCheck("top_level_primary_actions_enabled", source.primary_actions_enabled),
    makeFalseCheck("top_level_delivery_success", source.delivery_success),
    makeFalseCheck("board_media_safe_to_control", source.board_media_preflight_summary.safe_to_control),
    makeFalseCheck("board_media_primary_actions_enabled", source.board_media_preflight_summary.primary_actions_enabled),
    makeFalseCheck("realtime_map_safe_to_control", source.realtime_map_snapshot.safe_to_control),
    makeFalseCheck("elevator_state_safe_to_control", source.elevator_state_snapshot.safe_to_control),
    makeFalseCheck("route_replay_safe_to_control", source.route_replay_snapshot.safe_to_control),
    makeFalseCheck("labeling_queue_safe_to_control", source.labeling_queue_snapshot.safe_to_control),
    makeFalseCheck("voice_safe_to_control", source.voice_asr_tts_snapshot.safe_to_control),
    makeFalseCheck("safe_command_safe_to_control", source.safe_command_snapshot.safe_to_control),
  ];
  const disabledEntryChecks: O7OperatorConsoleAcceptanceCheck[] = [
    makeFalseCheck("manual_policy_command_dispatch_enabled", source.manual_control_policy.command_dispatch_enabled),
    makeFalseCheck("manual_policy_manual_control_enabled", source.manual_control_policy.manual_control_enabled),
    makeFalseCheck("manual_policy_navigate_goal_enabled", source.manual_control_policy.navigate_goal_enabled),
    makeFalseCheck("manual_policy_keyboard_control_enabled", source.manual_control_policy.keyboard_control_enabled),
    makeFalseCheck("safe_command_command_dispatch_enabled", source.safe_command_snapshot.command_dispatch_enabled),
    makeFalseCheck("safe_command_manual_control_enabled", source.safe_command_snapshot.manual_control_enabled),
    makeFalseCheck("safe_command_navigate_goal_enabled", source.safe_command_snapshot.navigate_goal_enabled),
    makeFalseCheck("safe_command_keyboard_control_enabled", source.safe_command_snapshot.keyboard_control_enabled),
    makeFalseCheck("voice_tts_send_enabled", source.voice_asr_tts_snapshot.tts_send_enabled),
    makeFalseCheck("labeling_submit_enabled", source.labeling_queue_snapshot.submit_enabled),
    makeFalseCheck("route_replay_playback_available", source.route_replay_snapshot.playback_available),
  ];

  assertAllFalse([...failClosedChecks, ...disabledEntryChecks]);
  if (presentKrSchemas.length !== 6 || presentKrSchemas.some((schema) => schema.length === 0) || matchedMarkers.length > 0) {
    // 任何 KR 快照缺失或危险标记出现，都让 guard 失败，避免 API 悄悄降级成绿灯。
    throw new Error(`o7_acceptance_guard_contract_drift:${matchedMarkers.join(",") || "snapshot_schema_count"}`);
  }

  return {
    schema: "trashbot.o7.operator_console_acceptance.v1",
    ...PROOF_FLAGS,
    source_response_schema: source.schema,
    source_endpoint: "/api/o7/operator-console",
    guard_endpoint: "/api/o7/operator-console/acceptance",
    evidence_boundary: "software_proof_o7_operator_console_acceptance_guard",
    reads_hardware: false,
    sends_commands: false,
    connects_cloud_production: false,
    six_kr_snapshots_present: true,
    snapshot_schema_keys: [...SNAPSHOT_SCHEMA_KEYS],
    snapshot_schemas: schemas,
    fail_closed_checks: failClosedChecks,
    disabled_entry_checks: disabledEntryChecks,
    dangerous_marker_scan: {
      checked_marker_ids: DANGEROUS_MARKERS.map((marker) => marker.id),
      matched_marker_ids: [],
      markers_absent: true,
    },
    acceptance_verdict: "blocked_not_proven_guard_ok",
    not_real_capability_proof: true,
    remaining_gaps: [
      "real_o7_realtime_cloud_stream_not_proven",
      "real_route_replay_archive_not_proven",
      "real_labeling_api_not_proven",
      "real_voice_runtime_not_proven",
      "real_safe_command_dispatch_not_proven",
      "real_robot_ack_not_proven",
    ],
  };
}
