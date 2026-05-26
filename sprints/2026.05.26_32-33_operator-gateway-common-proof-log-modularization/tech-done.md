# 2026.05.26 32-33 Operator Gateway Common Proof/Log Modularization Tech Done

## sprint_type

micro

## 实际改动

- 新增 `operator_gateway_diagnostics_common.py`，承载 hardware proof summary、HIL risk 判定、review decision JSONL 读取、log refs normalize 和 `safe_int` helper。
- 更新 `operator_gateway_diagnostics.py`，继续从 facade re-export 原有公开名称，`build_diagnostics_payload` 调用点和 payload key 未改。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 common proof/log helper 的模块边界和兼容性口径。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.184s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无输出，退出码 0。
- 通过：`cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_common.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_32-33_operator-gateway-common-proof-log-modularization/tech-done.md`
  - 关键输出：命令无输出，退出码 0。

## 剩余风险

- 本轮只做 helper code organization，未运行真实硬件、串口、WAVE ROVER、HIL、Nav2 或 ROS2 launch 验证。
- `load_review_decision_log` 的合法 decision 集合继续引用 vision review 模块的 `REVIEW_DECISION_VALUES`，本轮不改变有效值集合。
