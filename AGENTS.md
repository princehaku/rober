# ros_rbs - Autonomous Trash Collection Robot

ROS2 自主自动驾驶扔垃圾小车项目。

## 必读资料入口

硬件、线路、串口、底盘协议、Orange Pi Zero 3、WAVE ROVER、固件、机械安装相关任务，必须先读：

`docs/vendor/VENDOR_INDEX.md`

AI coding / Agent 工作不允许凭记忆猜测硬件细节。涉及引脚、电压、UART 设备、波特率、JSON 指令、速度映射、反馈协议、机械尺寸时，必须以 `docs/vendor/` 下的本地资料为准，并在代码或说明中明确采用的资料来源。

## 架构

5 个包协同工作：

- **ros2_trashbot_interfaces** - 自定义 msg/srv/action
- **ros2_trashbot_nav** - Nav2 导航 + waypoint_manager + map_recorder
- **ros2_trashbot_vision** - 摄像头垃圾检测 (cv_bridge)
- **ros2_trashbot_behavior** - task_orchestrator 状态机 + action server
- **ros2_trashbot_bringup** - 启动文件

## 工作流程

1. **学习阶段**: `learn.launch.py` -> SLAM 建图 + 人工驾驶记录航点
2. **自主阶段**: `autonomous.launch.py` -> 加载地图 -> 巡逻 -> 检测垃圾 -> 导航收集 -> 送至垃圾桶

## 构建命令

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Agent 工作纪律

后续 AI coding / Agent 工作必须保持持续执行和完成前反思：

- **持续执行**：除非用户明确要求只做计划、解释或代码审查，否则默认把任务推进到可交付状态，包括实现、必要验证、修复验证中发现的问题，以及最后总结。
- **完成前反思**：每次代码或文档改动后，必须自检需求是否真正满足，是否误改无关文件，是否留下未处理 TODO，是否存在测试、构建或硬件验证缺口。
- **验证优先**：能运行测试、构建、静态检查或最小可行验证时必须运行；无法运行时，最终说明必须写清楚原因、影响和剩余风险。
- **失败继续定位**：测试、构建或运行验证失败时，默认先阅读错误、定位根因、修复并重新验证；不能把第一轮失败直接作为最终结果交给用户。
- **硬件相关二次确认**：凡涉及 WAVE ROVER、ESP32、Orange Pi、UART 设备、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸，必须再次查阅 `docs/vendor/VENDOR_INDEX.md` 及其指向的本地 vendor 文件，并在代码注释、提交说明或最终说明中明确采用的资料来源。
- **最终回复要求**：最终说明必须包含实际改动、验证结果，以及未完成事项或风险；如果没有未完成事项，也要明确说明验证范围。

## 本地环境记忆

- 当前 Windows 主机有 WSL `Ubuntu-24.04`，但本项目目标是 ROS2 Humble。不要为了 Humble 强行改造 Ubuntu 24.04。
- ROS2 Humble 构建验证优先使用 Docker 官方 Humble 容器挂载仓库，例如挂载 `E:\rober` 到容器 `/ws` 后运行 `colcon build --symlink-install`。

## 子 agent 分工铁律

后续 Codex/AI 工作默认永远使用 子 agent 分工系统，不允许主 agent 一个人把方向、拆解、实现、测试、审查全部包圆。这不仅是分工，而是必须执行到位的闭环系统。