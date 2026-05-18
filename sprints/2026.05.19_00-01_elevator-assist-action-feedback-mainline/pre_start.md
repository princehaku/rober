# Sprint 2026.05.19_00-01 Elevator Assist Action Feedback Mainline - Pre Start

- sprint_type: epic
- start_time: 2026-05-19 00:03 Asia/Shanghai
- automation_id: skill-progression-map

## 1. 启动结论

本轮进入 Objective 2 / Objective 4 的电梯 assisted delivery 主链路反馈补齐：让 `TrashCollection` action 在电梯子阶段实时发布可读 feedback，而不是只在任务记录里事后看到 `elevator_phase`。

本轮不是 O5 external proof、不是 O1 HIL、不是 PR #4 真实现场材料回填、不是 PR #5 真实 2D LiDAR / ToF 材料验收。当前主机只有 Docker / local software proof，没有真实 WAVE ROVER、UART、HIL、真实手机、真实电梯、4G、OSS/CDN、production DB/queue 或公网 HTTPS/TLS。

## 2. 证据来源

- `OKR.md` 4.1：Objective 5 约 68% 数字最低，但需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；本机不可提供。
- `OKR.md` 4.1：Objective 1 约 81%，但需要真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF 材料；本机不可提供。
- PR #4：`Add elevator-assisted delivery capability to agents, registry and OKR` 已把电梯 assisted delivery 设为主线能力，后续不能只停留在文档口径。
- PR #5 review：指出硬件边界、最低 OKR 叙事和 2D LiDAR / ToF vendor source 问题；当前 repo 已有多轮硬件 source alignment / procurement / HIL-entry gate，继续无真实材料包装会重复消费 blocker。
- `sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/final.md`：上一轮明确下一步如果仍无真实手机材料，不要继续堆 O4 本地 wrapper，应重新 rerank。
- 代码只读核对：`task_orchestrator.py` 已有电梯 dry-run/rehearsal 子阶段与 task record 记录，但 `_execute_collection` 只在 loaded / delivering / dropoff / returning / done 粗阶段发布 action feedback。

## 3. Blocker 红线核对

最近两轮主要阻塞不是代码可修复失败，而是缺真实材料：

- 真实手机 / production app / PWA prompt/user choice 材料缺失。
- O5 external proof 缺失。
- O1 WAVE ROVER/UART/HIL 和 PR #5 真实传感器材料缺失。
- PR #4 route/elevator 真实现场材料缺失。

本轮不继续新建材料 wrapper，也不把 `software_proof` 写成真实通过；改做不依赖真实材料的行为反馈功能补齐。

## 4. Owner 和范围

- 主责 owner：`robot-software-engineer`
- 收口 owner：`product-okr-owner`

允许改动范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `docs/product/elevator_assisted_delivery.md`
- `docs/interfaces/ros_contracts.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline/`

## 5. 验收口径

- Action feedback 必须能看到电梯子阶段：等待电梯开门、进入电梯、请求帮忙按楼层、等待目标楼层、驶出电梯 / 恢复送达。
- Feedback 文案必须保持中文优先和 phone-safe，不暴露 raw ROS topic、`/cmd_vel`、串口、WAVE ROVER 低层参数、raw JSON、凭证或完整本机路径。
- 失败场景必须继续 fail-closed，并通过 feedback / task record 表达需要人工接管。
- 证据边界保持 `software_proof_docker_elevator_assist_default_mainline_gate` 或 `software_proof_docker_elevator_evidence_driven_mainline_gate`；不得宣称真实电梯、真实喇叭/TTS、真实 Nav2/fixed-route、HIL、dropoff/cancel completion 或 delivery success。
