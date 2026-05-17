# Sprint 2026.05.17_21-22 Wave Rover HIL Packet Intake - Pre Start

sprint_type: epic

## 1. 开工背景

产品北极星：把 `rober` 做成普通手机用户可以交付垃圾、现场支持可以复测、证据链可以复盘的低成本 ROS2 自主垃圾投递机器人。下一轮不能继续堆没有外部材料的 Objective 5 metadata，也不能把本地 fixture 写成真实 HIL；本轮要把 Objective 1 的真实底盘证据入口准备好。

当前 `OKR.md` 4.1 更新时间为 2026-05-17 20:19 Asia/Shanghai，最新 sprint 为 `2026.05.17_20-21_wave-rover-feedback-replay-gate`。Objective 5 约 68%，数值最低；Objective 1 约 78%；Objective 2 / Objective 3 / Objective 4 均约 99%。

## 2. 近期证据

- `OKR.md` 4.1：Objective 5 仍最低，但继续推进需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或真实手机/browser external proof；当前本机只有 Docker。
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/final.md`：已完成 `software_proof_docker_wave_rover_feedback_replay_gate`，但仍是 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，不等于 `hil_pass`。
- PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR`：已合并，把 elevator assisted delivery 放入主行为链和证据链；近期 Objective 2 / Objective 3 已推进到约 99%，真实现场材料仍缺。
- PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline`：仍有 unresolved review threads，指出 `docs/product/production_hardware_boundary.md` 默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` baseline 矛盾、`OKR.md` lowest-objective 叙述漂移、强制传感器假设缺 `docs/vendor/` 来源。最近硬件 ladder 已部分承接，但真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry 材料仍缺。
- `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 事实来源为本地 vendor 资料，UART 是 newline-delimited JSON，Raspberry Pi 参考默认 `/dev/ttyAMA0` at `115200`，Orange Pi 实际串口必须上车确认；本轮不得猜测串口或打开串口。

## 3. 本轮建议深入 OKR

本轮深入 Objective 1：硬件协议可信底盘。

理由：

1. Objective 5 是数值最低 Objective，但 O5 stop rule 继续成立；当前缺真实公网、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 和真实手机/browser external proof。
2. Objective 2 / Objective 3 / Objective 4 已约 99%，PR #4 route/elevator 仍缺真实现场材料，但继续本地 metadata 不能替代 field pass。
3. PR #5 硬件材料缺口仍存在，但本轮不再围绕 2D LiDAR / ToF 采购 wrapper 机械堆叠，而是转向 Objective 1 最直接可行动作：让未来真实 WAVE ROVER HIL packet 有可摄取、可复核、可分发的验收入口。
4. 20-21 sprint 已有 replay / interval / topic-alignment 软件围栏；下一步应把真实 HIL packet 的文件 contract、PC gate、Robot diagnostics、mobile read-only panel 和 Product closeout 串成同一 `evidence_ref` 链。

## 4. 本轮核心抓手

新增 `wave_rover_hil_packet_intake` software-proof gate，把未来真实 HIL packet 接入 PC / Robot / mobile 只读验收链。

目标 artifact 只能证明：

- `software_proof_docker_wave_rover_hil_packet_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

目标 HIL packet 输入 contract：

- `feedback_T1001.log`
- `odom_once.jsonl`
- `imu_once.jsonl`
- `battery_once.jsonl`
- `operator_hil_report`
- 同一 `evidence_ref`

本机只能用 synthetic fixture 验证，不得声明 `hil_pass`、真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实手机/browser、真实路线/电梯 field pass 或 delivery success。

## 5. Owner 与责任

- hardware-engineer：新增 PC gate、fixtures、测试和 `docs/hardware/wave_rover_hil_packet_intake.md`；必须读取 `docs/vendor/VENDOR_INDEX.md` 和 WAVE ROVER vendor 文件；只做 software proof，不打开串口。
- robot-software-engineer：新增 metadata-only diagnostics consumer，更新 diagnostics 测试与 `docs/interfaces/ros_contracts.md`；不改变 primary action。
- full-stack-software-engineer：在 `mobile/web` 增加只读 HIL packet intake panel，更新 fixture/test 和 `docs/product/mobile_user_flow.md`；Start / Confirm / Cancel gating 不变。
- product-okr-owner：实现后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，保守记录进展和剩余证据缺口。

## 6. 风险与阻塞

- 当前主机无真实 WAVE ROVER、真实 UART、真实串口设备和真实 HIL packet；本轮只能做 Docker/local synthetic fixture software proof。
- PR #5 的真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry 仍缺，不应通过本轮上调为真实硬件通过。
- 如果实现阶段未能保持 `delivery_success=false` 和 `primary_actions_enabled=false`，必须 fail closed 并要求对应 owner 重试。
- 如果 Robot 或 mobile surface 暴露 raw artifact、串口、baudrate、local path、traceback、checksum、`/cmd_vel` 或 raw feedback，必须视为验收失败。
