# O1 Same-session WAVE ROVER Wheel Feedback Material Intake Pre-start

## sprint_type

sprint_type: epic

## 启动事实

本轮已读取 `AGENTS.md`、`OKR.md`、`docs/vendor/VENDOR_INDEX.md`、最近 O1 收口文档，以及历史真实上位机 wheel feedback 材料。当前 `OKR.md` 4.1 显示：

- O5 云中转控制面约 85%，是当前最低 Objective。
- O1 硬件协议可信底盘约 86%，是次低 Objective。

O5 当前下一步必须是真实 production cloud、production DB/queue、真实 live endpoint 或真实 browser/手机材料。当前环境没有这些外部材料，且 `2026.07.10_08-14_same_task_mission_artifact_credit_gate` 已明确 local/mock probe、readback-only、checklist-only、support-only 工作不能继续计入主 OKR 增量。因此本轮不继续消费 O5 的同类 blocker，转向 O1 中仍可用真实历史材料推进的软件 Intake。

## 相关证据

- `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/tech-done.md`：近期 O1 只完成 fail-closed software gate，输出固定 `hil_pass=false`、`safe_to_control=false`，不证明真实 WAVE ROVER nonzero L/R 或真实 HIL pass。
- `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/final.md`：下一步要求切到真实上车 run 的 `feedback_T1001.log`、motion command、operator report 与 HIL acceptance record。
- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`：同一手控窗口内包含运动命令、`T=130` feedback request、`T=1001 L/R=61/61`，stop 后回到 `T=1001 L/R=0/0`，并保留 `delivery_success=false`、`safe_to_control=false`、`hil_pass=false`、`primary_actions_enabled=false`。
- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/tech-done.md`：记录真实上位机 `POST /api/base/manual` 与 PC first-jog same-session 证据，wheel feedback L/R 非零已在真实上位机材料中出现，但当时仍有 `physical_motion_lidar_delta_not_proven`。
- `sprints/2026.06.27_00-42_first_jog_motion_feedback_window/tech-done.md`：记录 PC first-jog / manual PWM 真实上位机材料，证明已有真实 WAVE ROVER feedback 窗口材料可被后续合同消费。

## 本轮目标 Objective

- 主目标：O1 硬件协议可信底盘。
- 本轮目标：让 `robot-hardware-engineer` 新增一个当前可复验、脱敏、fail-closed 的 O1 material intake，消费上述真实历史 artifact，输出 `trashbot.wave_rover_same_session_wheel_feedback_material.v1` 或等价清晰命名的合同。
- 本轮不是重新做旧 May 的 HIL packet collection drill，也不是把历史材料冒充当前 live HIL pass。

## 证据边界

本轮所有输出必须固定保守边界：

- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 不证明完整 HIL pass。
- 不证明 delivery success。
- 不证明当前 live HIL。
- 不打开真实控制动作。

允许承认的事实仅限于：历史真实上位机材料中，在同一 manual / first-jog 会话内观察到 motion command、feedback request、`T=1001` wheel feedback、nonzero L/R 样本，以及 stop 后 `0/0` 回落。

## Owner

- 主责 owner：`robot-hardware-engineer`
- 执行方式：单线闭环，由 Hardware owner 后续负责实现、测试、修复和 `tech-done.md` 留档。
- Product / 主节点：只负责验收口径、sprint 收口和最终汇总，不写产品代码、不运行实现命令、不修改硬件配置。

## 范围约束

本 planning sprint 只创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

本轮 planning 禁止修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `docs/product/`
- 产品代码、测试代码、硬件配置或 launch 参数

## 验收口径

planning 完成后，后续 implementation 必须做到：

1. Intake 能消费历史 same_session artifact，提取 `T=1001` 的 `L/R=61/61` 与停车后 `0/0`。
2. Intake 能输出脱敏摘要，不泄露 raw payload、绝对路径、token、URL、traceback 或设备敏感信息。
3. Intake 对缺字段、task/source mismatch、危险 true、unsafe text、无法证明 same-session 的材料 fail-closed。
4. 输出合同必须保留 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
5. `tech-done.md` 必须明确引用采用的历史证据和 vendor 资料来源，并说明该 intake 不等于真实 HIL pass。

