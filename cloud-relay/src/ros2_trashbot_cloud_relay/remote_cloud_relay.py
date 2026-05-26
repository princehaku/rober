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
O7_ROUTE_REPLAY_SNAPSHOT_SCHEMA = "trashbot.o7.route_replay_snapshot.v1"
O7_LABELING_QUEUE_SNAPSHOT_SCHEMA = "trashbot.o7.labeling_queue_snapshot.v1"
O7_VOICE_ASR_TTS_SNAPSHOT_SCHEMA = "trashbot.o7.voice_asr_tts_snapshot.v1"
O7_SAFE_COMMAND_SNAPSHOT_SCHEMA = "trashbot.o7.safe_command_snapshot.v1"


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
    # 路线回放 snapshot 只定义 O6 归档/轨迹 API 的字段槽位，不证明有历史任务可播放。
    route_replay_snapshot = {
        "schema": O7_ROUTE_REPLAY_SNAPSHOT_SCHEMA,
        "schema_version": 1,
        "source": "software_proof",
        "snapshot_status": "blocked_not_proven",
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "playback_available": False,
        "real_archive_connected": False,
        "task_selector": {
            "source_contract": "history.route_replay.v1",
            "status": "blocked_no_cloud_task_archive",
            "available_task_count": 0,
            "selected_task_id": "not_connected",
            "task_list_ref": "missing_o6_cloud_task_archive",
            "selection_required": True,
        },
        "selected_task": {
            "task_id": "not_connected",
            "robot_id": "not_connected",
            "route_id": "not_connected",
            "started_at_ms": None,
            "completed_at_ms": None,
            "status": "not_proven",
            "evidence_ref": "missing_selected_task_record",
        },
        "trajectory": {
            "frame_count": 0,
            "sample_frames": [],
            "frame_schema": "pending_cloud_trajectory_frame_v1",
            "map_frame": "not_connected",
            "status": "blocked_no_trajectory_api",
        },
        "playback_cursor": {
            "frame_index": None,
            "timestamp_ms": None,
            "playing": False,
            "speed": 0,
            "status": "blocked_not_available",
        },
        "keyframes": {
            "count": 0,
            "sample_refs": [],
            "status": "blocked_no_keyframe_archive",
        },
        "evidence_refs": {
            "task_archive": "missing_o6_cloud_task_archive",
            "trajectory_api": "missing_trajectory_api",
            "keyframe_archive": "missing_keyframe_archive",
            "state_transition_archive": "missing_state_transition_archive",
        },
        "state_transitions": {
            "count": 0,
            "sample": [],
            "status": "blocked_no_state_transition_archive",
            "gaps": [
                "cloud_task_archive_not_connected",
                "trajectory_frame_schema_not_backfilled",
                "keyframe_evidence_refs_not_backfilled",
                "state_transition_timeline_not_backfilled",
            ],
        },
        "blocked_reasons": [
            "o6_cloud_task_archive_not_connected",
            "history_route_replay_api_draft",
            "trajectory_frames_not_available",
            "keyframe_evidence_refs_not_available",
            "state_transitions_not_available",
        ],
        "not_proven": [
            "real_history_task_list",
            "real_selected_task",
            "real_trajectory_frames",
            "real_route_playback_cursor",
            "real_keyframe_evidence_refs",
            "real_state_transition_timeline",
            "cloud_archive_query_latency",
        ],
        "next_required_evidence": [
            "o6_cloud_task_archive_query_contract",
            "history_route_replay_task_list_fixture",
            "trajectory_frame_schema_with_map_frame_and_timestamp",
            "keyframe_evidence_ref_archive_sample",
            "state_transition_timeline_archive_sample",
            "pc_playback_cursor_bound_to_cloud_frames_without_robot_control",
        ],
    }
    # 标注队列 snapshot 只冻结 O7-KR4 的云端字段，不声明真实 O6 annotation API 已连接。
    labeling_queue_snapshot = {
        "schema": O7_LABELING_QUEUE_SNAPSHOT_SCHEMA,
        "schema_version": 1,
        "source": "software_proof",
        "snapshot_status": "blocked_not_proven",
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "submit_enabled": False,
        "rollback_enabled": False,
        "real_annotation_api_connected": False,
        "dataset_export_available": False,
        "review_queue": {
            "source_contract": "labeling.review_queue.v1",
            "status": "blocked_no_annotation_api",
            "available_item_count": 0,
            "assigned_operator": "not_connected",
            "queue_ref": "missing_o6_annotation_review_queue",
            "selection_required": True,
        },
        "selected_item": {
            "item_id": "not_connected",
            "task_id": "not_connected",
            "frame_id": "not_connected",
            "media_ref": "missing_review_item_media_ref",
            "evidence_ref": "missing_selected_labeling_item_record",
            "status": "not_proven",
        },
        "label_schema": {
            "schema_ref": "missing_label_schema",
            "version": "not_connected",
            "status": "blocked_no_label_schema_api",
            "required_fields": [],
        },
        "allowed_label_types": [
            {
                "type": "elevator_door_state",
                "status": "contract_placeholder_not_api",
                "values": ["open", "closed", "unknown"],
            },
            {
                "type": "floor_label",
                "status": "contract_placeholder_not_api",
                "values": [],
            },
            {
                "type": "obstacle_type",
                "status": "contract_placeholder_not_api",
                "values": ["none", "person", "cart", "trash_bag", "unknown"],
            },
        ],
        "draft_labels": {
            "count": 0,
            "items": [],
            "status": "blocked_no_selected_item",
            "autosave_available": False,
        },
        "submit_audit": {
            "status": "blocked_not_available",
            "endpoint": "POST /api/o6/annotations (future, disabled)",
            "last_submit_id": "not_connected",
            "idempotency_key_required": True,
            "audit_ref": "missing_submit_audit_log",
        },
        "rollback_audit": {
            "status": "blocked_not_available",
            "endpoint": "POST /api/o6/annotations/rollback (future, disabled)",
            "last_rollback_id": "not_connected",
            "requires_reason": True,
            "audit_ref": "missing_rollback_audit_log",
        },
        "dataset_export": {
            "status": "blocked_not_available",
            "export_ref": "missing_training_dataset_export",
            "supported_formats": [],
            "gaps": [
                "o6_annotation_api_not_connected",
                "accepted_label_schema_not_proven",
                "reviewed_items_not_available",
                "dataset_manifest_export_not_available",
                "training_split_policy_not_defined",
            ],
        },
        "blocked_reasons": [
            "o6_annotation_api_not_connected",
            "labeling_review_queue_api_draft",
            "label_schema_not_available",
            "selected_review_item_not_available",
            "submit_audit_not_available",
            "rollback_audit_not_available",
            "training_dataset_export_not_available",
        ],
        "not_proven": [
            "real_labeling_review_queue",
            "real_selected_labeling_item",
            "real_frame_or_screenshot_media",
            "real_label_schema",
            "real_allowed_label_types_from_cloud",
            "real_draft_label_autosave",
            "real_annotation_submit",
            "real_annotation_rollback",
            "real_training_dataset_export",
        ],
        "next_required_evidence": [
            "o6_annotation_review_queue_query_contract",
            "label_schema_fixture_with_allowed_types",
            "selected_review_item_with_media_evidence_ref",
            "draft_label_payload_schema",
            "submit_annotation_audit_log_sample",
            "rollback_annotation_audit_log_sample",
            "dataset_export_manifest_contract",
            "pc_labeling_panel_bound_to_cloud_api_without_robot_control",
        ],
    }
    # 语音 snapshot 只冻结 O7-KR5 字段，不连接 ASR/TTS runtime、不发送 TTS、不读取音频设备。
    voice_asr_tts_snapshot = {
        "schema": O7_VOICE_ASR_TTS_SNAPSHOT_SCHEMA,
        "schema_version": 1,
        "source": "software_proof",
        "snapshot_status": "blocked_not_proven",
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "asr_stream_connected": False,
        "tts_send_enabled": False,
        "speaker_dispatch_enabled": False,
        "real_voice_api_connected": False,
        "real_asr_tts_runtime_connected": False,
        "media_preflight_dependency": {
            "required": True,
            "source_schema": O7_BOARD_MEDIA_PREFLIGHT_SCHEMA,
            "status": "blocked",
            "dependency_ref": "board_media_preflight_summary",
        },
        "asr_stream": {
            "source_contract": "voice.asr_tts_operator.v1",
            "status": "blocked_no_voice_api",
            "connection_state": "not_connected",
            "last_event_at_ms": None,
            "partial_slot": {
                "text": "",
                "status": "empty_not_connected",
                "evidence_ref": "missing_asr_partial_transcript_trace",
            },
            "final_slot": {
                "text": "",
                "status": "empty_not_connected",
                "evidence_ref": "missing_asr_final_transcript_trace",
            },
        },
        "tts_draft": {
            "text": "",
            "status": "draft_disabled",
            "max_chars": 0,
            "language": "zh-CN",
            "voice_profile": "not_connected",
            "confirmation_required": True,
        },
        "speaker_dispatch": {
            "status": "blocked_not_available",
            "endpoint": "POST /api/o7/operator/voice/tts (future, disabled)",
            "sends_to_robot": False,
            "idempotency_key_required": True,
            "timeout_ms": None,
            "recovery_path": (
                "Keep observe_only mode until cloud voice ACK, speaker ACK, "
                "failure event, and board media smoke exist."
            ),
        },
        "command_ack_audit": {
            "ack_status": "blocked_no_ack_contract",
            "last_command_id": "not_connected",
            "audit_ref": "missing_voice_command_audit_log",
            "speaker_ack_ref": "missing_speaker_dispatch_ack",
            "failure_event_ref": "missing_speaker_failure_event",
        },
        "blocked_reasons": [
            "voice_api_not_connected",
            "asr_event_stream_not_connected",
            "tts_command_ack_contract_pending",
            "speaker_dispatch_ack_not_proven",
            "board_media_preflight_blocked",
            "real_asr_tts_runtime_not_connected",
        ],
        "not_proven": [
            "real_voice_api_connected",
            "real_asr_stream",
            "real_asr_partial_transcript",
            "real_asr_final_transcript",
            "real_tts_draft_send",
            "real_tts_playback",
            "real_speaker_dispatch_ack",
            "real_audio_device",
            "real_rtc_session",
            "real_asr_tts_runtime_connected",
        ],
        "next_required_evidence": [
            "voice_asr_tts_cloud_api_contract",
            "asr_stream_connection_trace_with_partial_and_final_events",
            "tts_draft_payload_schema_with_voice_profile",
            "tts_command_ack_and_audit_log_sample",
            "speaker_dispatch_ack_or_failure_event_sample",
            "board_media_preflight_audio_input_output_pass",
            "rtc_media_smoke_with_no_chassis_motion",
        ],
    }
    # 安全命令 snapshot 只冻结 O7-KR6 的手控/寻路 envelope，不连接云端命令 API。
    # 所有 dispatch、键盘、导航和 robot ACK 字段固定关闭，防止 PC UI 误变成控制台。
    safe_command_snapshot = {
        "schema": O7_SAFE_COMMAND_SNAPSHOT_SCHEMA,
        "schema_version": 1,
        "source": "software_proof",
        "snapshot_status": "blocked_not_proven",
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "command_dispatch_enabled": False,
        "manual_control_enabled": False,
        "navigate_goal_enabled": False,
        "keyboard_control_enabled": False,
        "real_command_api_connected": False,
        "real_robot_ack_connected": False,
        "manual_turn_envelope": {
            "source_contract": "operator.safe_command_preview.v1",
            "status": "blocked_not_proven",
            "sends_to_robot": False,
            "accepted_input_slots": ["ui_turn_left", "ui_turn_right", "keyboard_arrow_keys_disabled"],
            "requested_direction": "not_connected",
            "velocity_limited": True,
            "steering_limited": True,
            "evidence_ref": "missing_manual_turn_command_envelope_trace",
        },
        "velocity_limits": {
            "max_linear_mps": None,
            "max_angular_radps": None,
            "source": "not_connected",
            "status": "blocked_no_robot_hil_limits",
            "hardware_verified": False,
        },
        "steering_limits": {
            "max_steering_angle_rad": None,
            "max_turn_rate_radps": None,
            "source": "not_connected",
            "status": "blocked_no_robot_hil_limits",
            "hardware_verified": False,
        },
        "navigate_goal_envelope": {
            "source_contract": "operator.safe_command_preview.v1",
            "status": "blocked_not_proven",
            "sends_to_robot": False,
            "goal_source": "map_click_disabled",
            "requires_map_goal_slot": True,
            "evidence_ref": "missing_navigate_goal_command_envelope_trace",
        },
        "map_goal_slot": {
            "map_frame": "map",
            "x_m": None,
            "y_m": None,
            "yaw_rad": None,
            "status": "empty_not_connected",
            "evidence_ref": "missing_map_goal_selection_trace",
        },
        "cloud_command_endpoint": {
            "manual_turn": "POST /api/o7/operator/commands/manual-turn (future, disabled)",
            "navigate_goal": "POST /api/o7/operator/commands/navigate-goal (future, disabled)",
            "status": "future_disabled",
            "sends_to_robot": False,
        },
        "idempotency_key_requirement": {
            "required": True,
            "header": "Idempotency-Key",
            "status": "required_not_connected",
            "replay_policy": "reject_duplicate_future_contract",
        },
        "confirmation_policy": {
            "manual_turn_requires_confirmation": True,
            "navigate_goal_requires_confirmation": True,
            "keyboard_control_requires_hold": True,
            "status": "blocked_no_confirmation_ui",
        },
        "robot_ack_status": {
            "ack_status": "blocked_no_robot_ack_contract",
            "last_command_id": "not_connected",
            "ack_ref": "missing_robot_command_ack",
            "timeout_ms": None,
            "cancel_ack_ref": "missing_robot_cancel_ack",
            "stop_ack_ref": "missing_robot_stop_ack",
            "recovery_ref": "missing_robot_recovery_event",
        },
        "evidence_gaps": {
            "timeout": "missing_command_timeout_policy_and_trace",
            "cancel": "missing_cancel_command_ack_trace",
            "stop": "missing_stop_command_ack_trace",
            "recovery": "missing_robot_recovery_event_trace",
        },
        "blocked_reasons": [
            "safe_command_api_not_connected",
            "manual_turn_command_dispatch_disabled",
            "navigate_goal_dispatch_disabled",
            "keyboard_control_disabled",
            "velocity_and_steering_limits_not_hil_verified",
            "robot_ack_timeout_cancel_stop_recovery_not_proven",
        ],
        "not_proven": [
            "real_manual_turn_control",
            "real_velocity_control",
            "real_steering_control",
            "real_keyboard_control",
            "real_navigate_goal_dispatch",
            "real_cloud_command_api_connected",
            "real_robot_command_ack",
            "real_timeout_cancel_stop_recovery",
            "real_chassis_safety",
        ],
        "next_required_evidence": [
            "cloud_safe_command_api_contract_with_bearer_auth",
            "idempotency_key_replay_rejection_trace",
            "manual_turn_payload_schema_with_velocity_and_steering_limits",
            "navigate_goal_payload_schema_with_map_frame_and_goal_slot",
            "operator_confirmation_ui_policy_trace",
            "robot_command_ack_timeout_trace",
            "cancel_stop_recovery_ack_trace",
            "hardware_hil_or_controlled_field_safety_evidence",
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
        "route_replay_snapshot": route_replay_snapshot,
        "labeling_queue_snapshot": labeling_queue_snapshot,
        "voice_asr_tts_snapshot": voice_asr_tts_snapshot,
        "safe_command_snapshot": safe_command_snapshot,
        "manual_control_policy": {
            "pc_direct_robot_connection": False,
            "cloud_mediated_only": True,
            "command_dispatch_enabled": False,
            "manual_control_enabled": False,
            "navigate_goal_enabled": False,
            "keyboard_control_enabled": False,
            "real_command_api_connected": False,
            "real_robot_ack_connected": False,
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
            "route_replay_snapshot_blocked",
            "labeling_queue_snapshot_blocked",
            "voice_asr_tts_snapshot_blocked",
            "safe_command_snapshot_blocked",
            "o6_cloud_task_archive_not_connected",
            "o6_annotation_api_not_connected",
            "voice_api_not_connected",
            "manual_or_navigation_dispatch_disabled",
        ],
        "not_proven": [
            "real_o7_realtime_cloud_stream",
            "real_route_replay_archive",
            "real_route_replay_task_selector",
            "real_route_replay_trajectory_frames",
            "real_route_replay_state_transitions",
            "real_labeling_review_queue",
            "real_selected_labeling_item",
            "real_annotation_submit",
            "real_annotation_rollback",
            "real_training_dataset_export",
            "real_voice_api_connected",
            "real_asr_stream",
            "real_asr_partial_transcript",
            "real_asr_final_transcript",
            "real_rtc_session",
            "real_camera_video_source",
            "real_audio_capture",
            "real_audio_playback",
            "real_asr_stream",
            "real_tts_playback",
            "on_robot_media_smoke",
            "real_manual_turn_control",
            "real_velocity_control",
            "real_steering_control",
            "real_keyboard_control",
            "real_navigate_goal_dispatch",
            "real_robot_command_ack",
            "real_timeout_cancel_stop_recovery",
            "real_o7_operator_command_dispatch",
            "delivery_success",
        ],
        "next_required_evidence": (
            board_media_preflight_summary["next_required_evidence"]
            + route_replay_snapshot["next_required_evidence"]
            + labeling_queue_snapshot["next_required_evidence"]
            + voice_asr_tts_snapshot["next_required_evidence"]
            + safe_command_snapshot["next_required_evidence"]
        ),
    }


def main(argv=None):
    """运行原 relay main，保持 ACK、phone-safe redaction 和 preflight 语义一致。"""

    # cloud-relay 只改变部署入口，不改变 robot bridge 已经依赖的参数和返回码。
    return _behavior_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
