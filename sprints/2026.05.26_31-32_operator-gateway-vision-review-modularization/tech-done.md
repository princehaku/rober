# Operator Gateway Vision Review Modularization Tech Done

## sprint_type

micro

## 实际改动

- 新增 `operator_gateway_diagnostics_vision_review.py`，承载 vision review queue、review progress、decision distribution、manifest integrity 和 vision manifest summary 的纯软件 diagnostics helper。
- 更新 `operator_gateway_diagnostics.py`，保留兼容 facade，从新模块 re-export `REVIEW_QUEUE_LIMIT`、`LOW_CONFIDENCE_REVIEW_THRESHOLD`、`REVIEW_DECISION_VALUES`、`REVIEW_DECISION_ORDER` 和既有 vision review / integrity helper；`build_diagnostics_payload` 仍通过原名称生成 `vision_samples` payload。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 vision review diagnostics 的模块边界和不变更范围。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.158s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无错误输出，退出码 `0`
- 通过：`cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_vision_review.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_31-32_operator-gateway-vision-review-modularization/tech-done.md`
  - 关键输出：命令无 whitespace error 输出，退出码 `0`

## 输入 / 输出 / 指标变化

- 输入不变：仍读取 vision sample manifest path 和 review decision JSONL index。
- 输出不变：`vision_samples`、review queue、progress summary、decision distribution、manifest integrity 字段、默认值和错误信息语义保持兼容。
- 指标不变：review queue limit 仍为 `5`，low-confidence threshold 仍为 `75`，decision order 仍为 `approved -> rejected -> needs_retry`。

## 剩余风险

- 本轮只做代码组织拆分，不提供真实视觉识别率、路线执行、HIL、相机安装或上车闭环证据。
- 仓库已有其他未跟踪 modularization 文件和 sprint 文档状态变化，本轮未清理、未回滚。

## 协同需求

- 不需要 Hardware 协同：未改硬件、vendor、相机安装或底盘假设。
- 不需要 Robot Platform 协同：未改 ROS2 接口、launch 或行为状态机。
- 不需要 Full-Stack 协同：payload key、alias 和导入路径保持不变。
