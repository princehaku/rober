"""cloud-relay 专用 Python runtime 入口。

当前云中转协议实现仍由 onboard behavior 包维护；这里作为 thin wrapper 暴露
`python -m ros2_trashbot_cloud_relay.remote_cloud_relay`，让 Docker、smoke 和
产品文档都能指向 cloud-relay/ 自己的入口。

本入口同时暴露 `cloud_worker_migration_rehearsal` CLI：
`trashbot.cloud_worker_migration_rehearsal.v1` /
`trashbot.cloud_worker_migration_rehearsal_summary.v1`，证据边界固定为
`software_proof_docker_cloud_worker_migration_rehearsal_gate`，并保持
`production_ready=false`、`delivery_success=false`、`primary_actions_enabled=false`。
"""

# 复用原模块的全部公共符号，测试和后续工具仍可按需从这个入口导入 helper。
# noqa 必须保留，因为 wrapper 的职责就是重新导出，而不是在这里重复实现协议。
from ros2_trashbot_behavior.remote_cloud_relay import *  # noqa: F401,F403
from ros2_trashbot_behavior.remote_cloud_relay import main as _behavior_main


def main(argv=None):
    """运行原 relay main，保持 ACK、phone-safe redaction 和 preflight 语义一致。"""

    # cloud-relay 只改变部署入口，不改变 robot bridge 已经依赖的参数和返回码。
    return _behavior_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
