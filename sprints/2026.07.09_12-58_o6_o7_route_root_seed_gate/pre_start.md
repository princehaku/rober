# O6/O7 Route Root Seed Gate Pre-Start

## sprint_type: epic

## 背景

`OKR.md` 4.1 节显示当前最低 active Objective 是 O7，进度约 44%；O6 约 45%，是 O7 历史回放、标注和训练数据链路继续前进的直接数据底座。

上一轮 `sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/final.md` 已经把离线 seed smoke 串到 O6/O7 主路径，但明确留下 route-root seed 还依赖 `route_bag` gate 的风险。这个依赖会让本地/Mock 路线材料无法独立作为 O6/O7 smoke seed 使用，进而阻塞 O7 对 route replay、labeling、artifact readiness 的稳定验证。

本轮只创建 sprint planning docs，不实现代码、不运行 ROS2、不触发云端生产写入、不访问真实串口或底盘。

## 本轮目标

建立一个 Epic sprint 计划：把 route-root seed 从 `route_bag` gate 中解耦，让本地/Mock O6/O7 smoke 能在没有 `route_bag` 的情况下，用 allowlist route root 内的 `route.csv`、manifest、derived replay 和可选 evidence/probe 摘要完成同一 `task_id` 的软件侧贯通验证。

本 sprint 目标是推进 O7 最低 active Objective，同时用 O6 作为数据归档和 consumer detail 的支撑层。

## owner分工 / Owner 分工

- `product-okr-owner`：负责 OKR 对齐、范围裁剪、验收口径和最终收口判断。
- `robot-software-engineer`：主责 O6 route-root seed gate 的后续实现、readback、fail-closed 规则和单元测试。
- `robot-algorithm-engineer`：主责路线材料语义边界，定义 `route.csv`、manifest、derived replay、可选 `route_bag` 的关系。
- `full-stack-software-engineer`：主责 O7 consumer detail / PC readiness 展示，确保只消费 O6 摘要和 blocked reasons。
- `rober-hardware-engineer`：本轮无实现任务；若后续进入真实硬件集成，必须按 `docs/vendor/VENDOR_INDEX.md` 二次确认硬件事实。

## 文件范围

本次 planning-only 动作只允许创建以下三个文件：

- `sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/pre_start.md`
- `sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/prd.md`
- `sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/tech-plan.md`

不得修改产品代码、测试代码、硬件配置、OKR.md 或其他 sprint 文档。

## 接口边界

- route-root seed gate 是本地/Mock software proof，不代表真实生产云、真实路线、真实媒体、真实控制或送达成功。
- `route_bag` 可以作为后续增强输入，但不能作为 route-root seed local/mock smoke 的硬阻塞条件。
- O6 输出只能是摘要、计数、相对/安全 ref、blocked reasons、next required evidence 和安全旗标。
- O7 只消费 O6 consumer detail 摘要，不直接读取任意本地路径、不展示 token、base64 媒体、绝对路径或控制字段。

## safe flags false / 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 预期收口

后续实现完成时，`tech-done.md` 必须给出 O6/O7 单元测试、前端测试或最小 smoke 的真实日志片段，并继续明确所有 safe flags false。若发现该计划不能在 local/mock 范围内闭环，需要在 `side2side_check.md` / `final.md` 中说明原因和剩余风险。
