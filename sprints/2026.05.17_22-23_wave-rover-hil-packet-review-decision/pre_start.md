# Sprint 2026.05.17_22-23 Wave Rover HIL Packet Review Decision - Pre Start

sprint_type: epic

## 1. 开工背景

产品北极星：把 `rober` 做成普通手机用户可以交付垃圾、现场支持可以复测、证据链可以复盘的低成本 ROS2 自主垃圾投递机器人。当前最关键的产品事实不是继续堆云端或路线 metadata，而是让真实 WAVE ROVER HIL packet 回填后能被明确判定为 accepted、missing 或 rejected，避免把不完整材料误写成 `hil_pass`。

当前 `OKR.md` 4.1 更新时间为 2026-05-17 21:22 Asia/Shanghai，最新 sprint 为 `2026.05.17_21-22_wave-rover-hil-packet-intake`。Objective 5 约 68%，数值最低；Objective 1 约 79%；Objective 2 / Objective 3 / Objective 4 均约 99%。

本轮只创建产品/技术计划文档，不改产品代码、测试代码、`OKR.md` 或 `docs/` 其他文件。

## 2. 近期证据

- `OKR.md` 4.1：Objective 5 仍最低，但继续提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof；当前本机只有 Docker，O5 stop rule 继续成立。
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/final.md`：已完成 `software_proof_docker_wave_rover_feedback_replay_gate`，但明确不是 `hil_pass`，也不是真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 或真实送达证明。
- `sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/final.md`：已完成 `software_proof_docker_wave_rover_hil_packet_intake_gate`，把 PC gate、Robot diagnostics、mobile/web 和 Product closeout 串成 HIL packet intake software-proof 链路；仍保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR` 与 PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline`：都把 elevator / hardware baseline 作为必达产品边界；但真实 route/elevator field materials 与真实硬件材料仍未补齐。
- PR #5 review 仍有未解决硬件边界事实：P1 默认硬件集合与 mandatory `monocular + 2D LiDAR + ToF` baseline 未对齐，P2 mandatory sensor assumptions 缺 `docs/vendor/` 来源；该问题不能通过本轮 HIL packet review decision 自动关闭。

## 3. 本轮建议深入 OKR

本轮深入 Objective 1：硬件协议可信底盘。

理由：

1. Objective 5 是数值最低 Objective，但当前缺真实公网、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 和真实手机/browser external proof；继续本地 O5 metadata 不能移动真实产品风险。
2. Objective 2 / Objective 3 / Objective 4 已约 99%，近几轮 route/elevator result chain 已推进到 Docker/local software-proof 上限；继续堆同一方向会重复消费无硬件/无现场材料 blocker。
3. Objective 1 约 79%，是当前最弱可执行方向；20-21 已有 WAVE ROVER feedback replay，21-22 已有 HIL packet intake，但还缺对摄取结果的评审决策和 owner handoff。
4. PR #5 硬件边界事实仍要求产品侧把真实材料、vendor source 和下一步 evidence 明确化；本轮 review decision gate 应把 missing/rejected 材料和下一步 owner 交接写清楚。

## 4. 本轮核心抓手

新增 `wave_rover_hil_packet_review_decision` software-proof gate，消费上一轮 `wave_rover_hil_packet_intake` artifact/summary，输出：

- `accepted_required_materials`
- `missing_required_materials`
- `rejected_required_materials`
- `review_decision`
- `next_required_evidence`
- `owner_handoff`
- `rerun_commands`

目标 artifact 只能证明：

- `software_proof_docker_wave_rover_hil_packet_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本机只能用 synthetic fixture / previous intake summary 做 Docker-local software proof，不得声明 `hil_pass`、真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实手机/browser、真实 route/elevator field pass、真实 Objective 5 external proof 或 delivery success。

## 5. Owner 与责任

- hardware-engineer：新增 PC review-decision gate、fixtures、测试和硬件说明；必须读取 `docs/vendor/VENDOR_INDEX.md` 和 WAVE ROVER vendor 文件；只消费 intake artifact/summary，不打开串口，不探测 `/dev/*`。
- robot-software-engineer：新增 diagnostics metadata-only consumer，展示 review decision / next evidence / owner handoff；不改变 primary action，不启用任何机器人动作。
- full-stack-software-engineer：在 `mobile/web` 增加只读 HIL packet review decision panel；Start Delivery、Confirm Dropoff、Cancel gating 不变。
- product-okr-owner：实现后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，保守记录 O1 软件证明进展和剩余真实证据缺口。

## 6. 风险与阻塞

- 当前主机无真实 WAVE ROVER、真实 UART、真实串口设备和真实 HIL packet；本轮计划和后续实现都只能保持 Docker/local `software_proof`。
- Review decision 只能判定材料是否足以进入下一步真实 HIL 复账，不能替代真实 `/odom`、`/imu/data`、`/battery` 或 WAVE ROVER feedback。
- PR #5 的 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 仍缺，不应通过本轮上调为真实硬件通过。
- 如果后续实现阶段出现 `delivery_success=true`、`primary_actions_enabled=true`、`hil_pass` 或真实设备通过措辞，必须 fail closed 并要求对应 owner 重试。
