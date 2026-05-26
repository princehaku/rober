# Operator Gateway Route Field Run Modularization Tech Done

sprint_type: micro

## 实际改动

- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_route_field_run.py`，承接 route task field run readiness / intake / review / execution pack 的 schema/gate 常量、默认 blocked summary、`not_proven` helper、unsafe/copy guard、safe summary helper 和四个 summarize 函数。
- 更新 `operator_gateway_diagnostics.py` 为 public import 兼容层，继续 re-export 现有常量、helper 和 `summarize_route_task_field_run_*` 函数，保持测试和外部调用从原模块导入不变。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录本次拆分是 structure-only，不改变 `/api/status`、`/api/diagnostics` payload 语义，也不把 field-run material 升级为真实路线/电梯 field pass、Nav2/HIL、WAVE ROVER 或 delivery success 证明。
- 未触碰 route task field run reconciliation、route terminal rehearsal/review decision、elevator field run、hardware、WAVE ROVER、PR5、mobile real device、`.idea/` 或 `pc-tools/`。

## 验证结果

已运行：

```bash
cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior
cd /mnt/e/rober && git diff --check
```

结果：

- `python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 通过，`Ran 326 tests in 6.877s`，`OK`。
- `python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior` 通过，无输出。
- `git diff --check` 失败于范围外 `.idea/rober.iml` 第 1-14 行 trailing whitespace；该文件为本轮无关改动，未触碰。
- 补跑限定本轮文件 `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_route_field_run.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_14-15_operator-gateway-route-field-run-modularization/tech-done.md` 通过，无输出。

## 剩余风险

- 本轮只做软件结构拆分和单元/静态验证，不包含 ROS2 容器构建、HIL、真实串口、WAVE ROVER feedback、Nav2 实跑或真实手机/浏览器验证。
- route field-run summaries 仍然是 metadata-only software proof，不能作为 delivery success、field pass、Objective 5 外部证明或机器人控制授权。
- 当前仓库存在与本轮无关的 `.idea/`、`pc-tools/` 和前五轮 diagnostics modularization 改动，本轮未覆盖或回滚。
