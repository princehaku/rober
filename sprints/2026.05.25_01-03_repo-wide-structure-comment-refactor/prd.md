# Repo-wide Structure and Comment Refactor PRD

## 背景

仓库已经从 ROS2 skeleton 演化出较多 proof、diagnostics、remote relay 和 UI fallback 代码。当前最大风险不是缺少新节点，而是部分模块体量过大、职责混在一个文件里、测试文件随功能膨胀，后续 agent 难以安全修改。典型热点包括：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge.py`
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/trash_detector.py`

## 用户价值

这轮不追求新增产品能力，而是降低后续迭代成本：

- Agent 可以按目录和职责定位代码，减少误改。
- 超大文件被拆成兼容子模块，后续 bug fix 能控制 blast radius。
- 中文注释解释关键取舍，尤其是安全、降级、证据边界和 vendor-source 边界。
- 现有 CLI、ROS2 entry point、HTTP/mobile fallback、diagnostics 输出保持兼容。

## 成功口径

- 4 个 owner 均产出互不重叠的结构化改动或明确 blocked 证据。
- 每个 owner 至少补一处相关 `docs/` 文档，说明新的目录边界和维护规则。
- 现有入口保持兼容：原 import path、setup entry points、launch 文件和测试调用不得失效。
- 运行目标 owner 的测试命令，并由 `robot-software-engineer` 或最终集成验收执行最小全仓验证。
- 最终 `tech-done.md` 写清实际改动、验证结果、剩余风险和未触达范围。

## 非目标

- 不新增真实硬件、4G、公网、OSS/CDN、手机设备或 HIL 证明。
- 不改变 OKR 完成度数字。
- 不做跨包接口重命名。
- 不引入新的框架或大规模格式化。
- 不处理当前 unrelated 删除文件。
