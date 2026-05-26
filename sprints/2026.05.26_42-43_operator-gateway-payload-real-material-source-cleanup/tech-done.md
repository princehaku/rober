# operator gateway payload real material source cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py` 将 `real_material_readiness_board_source`、`real_material_evidence_intake_source`、`real_material_followup_escalation_status_source` 的重复三元链改为 `first_status_dict`。
- 三个 source 均保留旧候选顺序：`latest_status` raw key、summary key、`robot_diagnostics_*_summary`，再到 `diagnostics_source` 的同三组字段级 alias，最后默认 `{}`。
- 未启用 `fallback_to_diagnostics_source=True`，因为 real material 证据只能来自字段级 alias，不能把整包 diagnostics 当成真实材料证据。
- `docs/interfaces/operator_gateway_diagnostics.md` 同步记录 real material source resolver 边界和兼容性约束。

## 验证结果

已通过：

```bash
cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
......................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 326 tests in 7.205s

OK
```

```bash
cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior
```

结果：退出码 0，无输出。

```bash
cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_42-43_operator-gateway-payload-real-material-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_42-43_operator-gateway-payload-real-material-source-cleanup/tech-done.md
```

结果：退出码 0，无输出。

## 剩余风险

- 本 sprint 未改 ROS2 接口、launch、硬件配置、UART/serial 行为，也未做 HIL 或真实机器人运行验证。
