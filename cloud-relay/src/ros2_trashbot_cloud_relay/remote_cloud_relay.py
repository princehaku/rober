"""cloud-relay 专用 Python runtime 入口。

当前云中转协议实现仍由 onboard behavior 包维护；这里作为 thin wrapper 暴露
`python -m ros2_trashbot_cloud_relay.remote_cloud_relay`，让 Docker、smoke 和
产品文档都能指向 cloud-relay/ 自己的入口。

本入口同时暴露 `cloud_worker_migration_rehearsal` CLI：
`trashbot.cloud_worker_migration_rehearsal.v1` /
`trashbot.cloud_worker_migration_rehearsal_summary.v1`，证据边界固定为
`software_proof_docker_cloud_worker_migration_rehearsal_gate`，并保持
`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。

本入口也暴露 `cloud_worker_cutover_drain` CLI：
`trashbot.cloud_worker_cutover_drain.v1` /
`trashbot.cloud_worker_cutover_drain_summary.v1`，证据边界固定为
`software_proof_docker_cloud_worker_cutover_drain_gate`，terminal ACK 只代表
Docker/local relay envelope 收口，不代表真实送达或 production worker cutover。

本入口额外暴露 O7 Operator Console 的 cloud-side draft contract helper。
该 helper 只给 PC 工作站提供安全契约快照，不连接 ROS2、不直连小车、不发送控制。
"""

from __future__ import annotations

from typing import Any

# 复用原模块的全部公共符号，测试和后续工具仍可按需从这个入口导入 helper。
# noqa 必须保留，因为 wrapper 的职责就是重新导出，而不是在这里重复实现协议。
from ros2_trashbot_behavior.remote_cloud_relay import *  # noqa: F401,F403
from ros2_trashbot_behavior.remote_cloud_relay import main as _behavior_main

O7_OPERATOR_CONSOLE_SCHEMA = "trashbot.o7.operator_console.v1"
O7_BOARD_MEDIA_PREFLIGHT_SCHEMA = "trashbot.o7_board_media_preflight.v1"
O7_REALTIME_MAP_SNAPSHOT_SCHEMA = "trashbot.o7.realtime_map_snapshot.v1"
O7_ELEVATOR_STATE_SNAPSHOT_SCHEMA = "trashbot.o7.elevator_state_snapshot.v1"


def build_o7_operator_console_contract() -> dict[str, Any]:
    """返回 O7 PC 工作站可消费的 fail-closed cloud 契约快照。"""

    # 该契约故意只描述 draft/blocked/not_proven，避免 PC 端推断真实在线或可控制。
    # 后续接入真实 cloud API 时，必须先补 ACK、超时、取消和恢复路径证据。
    # 媒体 preflight 摘要也保持静态 fail-closed，不导入板端包、不探测真实设备。
    board_media_preflight_summary = {
        "schema": O7_BOARD_MEDIA_PREFLIGHT_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": "software_proof_o7_board_media_preflight_contract",
        "source": "operator_media_preflight",
        "overall_state": "blocked",
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "device_probe_allowed": False,
        "device_probe_attempted": False,
        "software_proof_only": True,
        "blocked_reasons": [
            "board_media_preflight_not_collected_by_pc",
            "rtc_signaling_stun_turn_not_proven",
            "camera_video_source_not_proven",
            "audio_input_output_not_proven",
            "asr_tts_runtime_not_proven",
        ],
        "not_proven": [
            "real_rtc_session",
            "real_camera_video_source",
            "real_audio_capture",
            "real_audio_playback",
            "real_asr_stream",
            "real_tts_playback",
            "orange_pi_media_runtime",
            "on_robot_media_smoke",
        ],
        "next_required_evidence": [
            "resolve_blocked_preflight_items",
            "orange_pi_camera_device_enumeration",
            "orange_pi_audio_input_output_enumeration",
            "rtc_signaling_stun_turn_trace",
            "camera_frame_evidence_with_timestamp",
            "asr_partial_and_final_transcript_trace",
            "tts_audio_playback_trace",
            "cpu_encoding_budget_trace",
            "on_robot_media_smoke_with_no_chassis_motion",
        ],
    }
    # 该 snapshot 只冻结 PC 需要显示的字段名，不采集 /tf、不读地图文件、不承诺 <2s。
    realtime_map_snapshot = {
        "schema": O7_REALTIME_MAP_SNAPSHOT_SCHEMA,
        "schema_version": 1,
        "source": "software_proof",
        "snapshot_status": "blocked_not_proven",
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "map_ref": {
            "value": "not_connected",
            "status": "not_proven",
            "evidence_ref": "missing_cloud_realtime_map_ref",
        },
        "map_frame": {
            "value": "map",
            "status": "contract_placeholder_not_tf",
            "frame_source": "cloud_contract_draft",
        },
        "robot_pose": {
            "x_m": None,
            "y_m": None,
            "yaw_rad": None,
            "pose_source": "not_connected",
            "status": "not_proven",
        },
        "pose_freshness": {
            "last_update_ms": None,
            "age_ms": None,
            "latency_lt_2s_proven": False,
            "status": "blocked_no_realtime_stream",
        },
        "route_membership": {
            "route_id": "not_connected",
            "on_route": False,
            "in_elevator_zone": False,
            "status": "not_proven",
            "reason": "cloud_realtime_map_pose_stream_not_connected",
        },
        "blocked_reasons": [
            "cloud_realtime_api_draft",
            "ros2_tf_forwarding_not_proven",
            "map_artifact_not_connected",
            "robot_position_latency_lt_2s_not_proven",
        ],
        "not_proven": [
            "real_ros2_tf",
            "real_map_artifact",
            "real_robot_pose",
            "real_route_membership",
            "real_elevator_zone_membership",
            "robot_position_latency_lt_2s",
        ],
    }
    # 电梯 snapshot 只提供状态链/楼层证据/接管原因的展示槽位，不证明真实电梯事件。
    elevator_state_snapshot = {
        "schema": O7_ELEVATOR_STATE_SNAPSHOT_SCHEMA,
        "schema_version": 1,
        "source": "software_proof",
        "snapshot_status": "blocked_not_proven",
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "state_chain": [
            {
                "state": "not_connected",
                "status": "not_proven",
                "evidence_ref": "missing_cloud_elevator_state_chain",
            }
        ],
        "current_state": "not_connected",
        "current_floor_evidence": {
            "floor_label": "not_connected",
            "confidence": None,
            "evidence_ref": "missing_floor_evidence",
            "status": "not_proven",
        },
        "target_floor": {
            "floor_label": "not_connected",
            "confirmation_status": "not_proven",
        },
        "human_takeover": {
            "required": True,
            "reason": "real_elevator_state_chain_not_proven",
            "operator_action": "keep_observe_only_until_cloud_archive_and_field_evidence_exist",
        },
        "blocked_reasons": [
            "elevator_event_archive_not_connected",
            "real_elevator_door_state_not_proven",
            "floor_recognition_not_proven",
            "human_takeover_reason_not_backfilled_from_task_record",
        ],
        "not_proven": [
            "real_elevator_state_chain",
            "real_current_floor",
            "real_target_floor_confirmation",
            "real_elevator_arrival",
            "real_human_takeover_reason",
        ],
    }

    return {
        "schema": O7_OPERATOR_CONSOLE_SCHEMA,
        "source": "software_proof",
        "proof_status": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "pc_only": True,
        "contract_source": "cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py",
        "workstation_endpoint": "/api/o7/operator-console",
        "cloud_api_status": "draft_blocked_not_proven",
        "robot_connection": "not_connected_by_pc",
        "realtime_stream_status": "blocked_not_proven",
        "operator_mode": "observe_only",
        "board_media_preflight_required": True,
        "board_media_preflight_schema": O7_BOARD_MEDIA_PREFLIGHT_SCHEMA,
        "board_media_preflight_state": "blocked",
        "board_media_preflight_summary": board_media_preflight_summary,
        "realtime_map_snapshot": realtime_map_snapshot,
        "elevator_state_snapshot": elevator_state_snapshot,
        "manual_control_policy": {
            "pc_direct_robot_connection": False,
            "cloud_mediated_only": True,
            "command_dispatch_enabled": False,
            "confirmation_required_before_future_dispatch": True,
            "success_claim_allowed": False,
        },
        "kr_contracts": [
            "realtime.map_pose.v1",
            "realtime.elevator_state.v1",
            "history.route_replay.v1",
            "labeling.review_queue.v1",
            "voice.asr_tts_operator.v1",
            "operator.safe_command_preview.v1",
        ],
        "blocked_reasons": [
            "cloud_realtime_api_draft",
            "pc_must_not_direct_connect_robot",
            "robot_ack_timeout_recovery_not_proven",
            "board_media_preflight_blocked",
            "realtime_map_snapshot_blocked",
            "elevator_state_snapshot_blocked",
            "manual_or_navigation_dispatch_disabled",
        ],
        "not_proven": [
            "real_o7_realtime_cloud_stream",
            "real_rtc_session",
            "real_camera_video_source",
            "real_audio_capture",
            "real_audio_playback",
            "real_asr_stream",
            "real_tts_playback",
            "on_robot_media_smoke",
            "real_o7_operator_command_dispatch",
            "delivery_success",
        ],
        "next_required_evidence": board_media_preflight_summary["next_required_evidence"],
    }


def main(argv=None):
    """运行原 relay main，保持 ACK、phone-safe redaction 和 preflight 语义一致。"""

    # cloud-relay 只改变部署入口，不改变 robot bridge 已经依赖的参数和返回码。
    return _behavior_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
