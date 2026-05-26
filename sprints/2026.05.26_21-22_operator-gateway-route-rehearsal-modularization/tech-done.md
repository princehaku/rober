# Route Rehearsal Diagnostics Modularization Tech Done

## sprint_type

micro

## 实际改动

- 新增 `operator_gateway_diagnostics_route_rehearsal.py`，承载 route/task rehearsal artifact、execution bundle、operator review、PC route debug console、PC route/elevator console integration 的 schema/gate 常量、脱敏 helper、默认 blocked summary、`not_proven` helper 和 summarize 函数。
- `operator_gateway_diagnostics.py` 改为从新内部模块 re-export 上述常量、helper 和 summarize 函数，保持既有 public import/API 兼容。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录本次拆分是 structure-only，payload/schema/gate/alias/false-state/`not_proven`/命令可用性不变。

## 验证结果

```bash
cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

结果：通过，`Ran 326 tests in 7.084s`，`OK`。

```bash
cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior
```

结果：通过，无输出。

```bash
cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_route_rehearsal.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_21-22_operator-gateway-route-rehearsal-modularization/tech-done.md
```

结果：通过，无输出。

## 剩余风险

- 本轮是 metadata-only software proof，仅验证 Python unittest、compileall 和 diff whitespace；不包含 ROS2 colcon 构建、HIL、真实串口、WAVE ROVER feedback、真实 Nav2/fixed-route 执行或硬件上车验证。
- 当前 worktree 已存在其他未提交拆分和 sprint 文档 dirty 状态；本轮未回滚、未覆盖范围外文件。

## 协同需求

- 暂不需要 Product、Hardware、Autonomy 或 Full-Stack 协同。
- 若后续把 metadata-only 诊断提升为真实控制或上车证据，需要 Hardware/Autonomy 提供独立真实运行证据契约。
