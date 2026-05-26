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


def build_o7_operator_console_contract() -> dict[str, Any]:
    """返回 O7 PC 工作站可消费的 fail-closed cloud 契约快照。"""

    # 该契约故意只描述 draft/blocked/not_proven，避免 PC 端推断真实在线或可控制。
    # 后续接入真实 cloud API 时，必须先补 ACK、超时、取消和恢复路径证据。
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
            "manual_or_navigation_dispatch_disabled",
        ],
        "not_proven": [
            "real_o7_realtime_cloud_stream",
            "real_o7_operator_command_dispatch",
            "delivery_success",
        ],
    }


def main(argv=None):
    """运行原 relay main，保持 ACK、phone-safe redaction 和 preflight 语义一致。"""

    # cloud-relay 只改变部署入口，不改变 robot bridge 已经依赖的参数和返回码。
    return _behavior_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
