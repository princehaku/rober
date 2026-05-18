# Sprint 2026.05.19_00-01 Elevator Assist Action Feedback Mainline - Side2Side Check

## sprint_type

epic

## 用户价值和产品北极星

- 北极星：让普通手机用户能理解小车在跨楼层送垃圾过程中的真实阶段，尤其是电梯 assisted delivery 的等待开门、进入电梯、请求按楼层、等待目标楼层、驶出电梯和恢复送达。
- 本轮价值：Robot worker 已把 `TrashCollection` action feedback 从粗粒度 `delivering` 推进到 `current_step=elevator:<phase>`，手机/API 后续可消费更细的 phone-safe 阶段状态。

## OKR 映射和 KR 拆解

- Objective 2：支撑 KR6 / KR7，把电梯 assisted delivery 状态链的阶段反馈纳入主 action feedback，而不是只靠 task record 事后复盘。
- Objective 4：支撑 KR6 / KR7，给手机端提供不暴露 raw ROS topic、串口、raw JSON 或底层控制参数的用户可读状态。
- Objective 1：不调整；没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data` 或 `/battery`。
- Objective 5：不调整；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover external proof。

## 对照检查

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 默认 dry-run 路径发布电梯阶段 feedback | 通过 | Robot worker `tech-done.md` 记录 focused unittest `Ran 15 tests OK`，覆盖 `elevator:waiting_elevator_open`、`elevator:requesting_floor_help`、`elevator:resume_delivery` 等阶段。 |
| rehearsal artifact 路径保持 software-proof 边界 | 通过 | Robot worker 记录 `software_proof_docker_elevator_evidence_driven_mainline_gate`，并保持 `delivery_success=false`、`primary_actions_enabled=false`。 |
| 手机/API 消费口径 phone-safe | 通过 | `current_step=elevator:<phase>`，文案中文优先，不暴露 raw ROS topic、`/cmd_vel`、串口、WAVE ROVER 低层参数、raw JSON、凭证或本机路径。 |
| 不虚增真实材料进度 | 通过 | OKR 4.1 保守记录 O2/O4 software proof，O1 保持约 81%，O5 保持约 68%，不写成真实 route/elevator field pass、HIL、真实手机通过或 delivery success。 |

## 风险、阻塞和证据链缺口

- 当前仍是 Docker/local software proof：`software_proof_docker_elevator_assist_default_mainline_gate` / `software_proof_docker_elevator_evidence_driven_mainline_gate`。
- 仍缺真实电梯门状态、真实目标楼层确认、真实人工协助、真实喇叭/TTS、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实手机设备/browser、O5 external proof、真实 dropoff/cancel completion 和 delivery success。
- PR #4 仍需真实 route/elevator field materials 回填；PR #5 仍需真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

## 责任 Engineer 和后续协同

- 已完成：Robot Platform Engineer。
- 需要后续协同：Full-Stack 可在下一轮消费 `TrashCollection.Feedback.current_step=elevator:<phase>`，在 mobile/web 做只读实时阶段展示；不能改变 Start Delivery、Confirm Dropoff、Cancel gating，也不能声明真实手机或 delivery success。
