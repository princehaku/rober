# 2026.05.26 41-42 operator gateway payload cloud external source cleanup

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 `cloud_external_evidence_review_decision_status_source`、`cloud_external_evidence_review_handoff_status_source`、`cloud_external_evidence_review_handoff_followup_source` 的第一段 status-source 查找改为 `first_status_dict(...)`。
  - 为三段查找分别定义字段级 keys tuple，保留旧优先级：`latest_status` 的 `robot_diagnostics_*_summary`、plain `*_summary`、raw key，再到 `diagnostics_source` 的同组三个字段级 alias。
  - 未启用 `fallback_to_diagnostics_source=True`，字段级 alias 缺失时仍默认 `{}`。
  - 保留后续 env var fallback 原顺序，未改变 payload key、summary 变量名、safe-copy 或 `not_proven` 内容。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录 cloud external evidence status-source 已迁移到 resolver，且 env fallback 仍保持原覆盖顺序。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.253s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无输出，退出码 0。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_41-42_operator-gateway-payload-cloud-external-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_41-42_operator-gateway-payload-cloud-external-source-cleanup/tech-done.md`
  - 关键输出：命令无输出，退出码 0。
- 额外核对：`cd /mnt/e/rober/onboard && rg -n "cloud_external_evidence_review_(decision|handoff|handoff_followup)_(keys|status_source|source = first_status_dict)|fallback_to_diagnostics_source=True" src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 关键结果：三个 cloud external evidence status-source 目标均使用 keys tuple + `first_status_dict(...)`；`fallback_to_diagnostics_source=True` 只出现在既有 verified-terminal generic material 区块，不在本轮 cloud external evidence 区块。

## 剩余风险

- 本轮不改变 ROS2 接口、launch、硬件配置、UART/serial 行为，未做 HIL 或真实机器人验证。
- 本轮只清理三个指定 cloud external evidence status-source 查找，env var fallback 和其他 payload 区域保持现状。
