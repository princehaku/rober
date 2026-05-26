# PR #5 Mandatory Sensor Material Follow-Up Escalation Status Pre-Start

Run time: 2026-05-23 04:05 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

产品北极星仍是让普通手机用户把垃圾交给小车后，小车可验证地完成固定路线/电梯 assisted delivery 送达；在硬件材料未到位时，support 和 reviewer 必须能清楚看到哪些真实材料仍缺失，而不能把 Docker/local metadata 当成真实硬件、真实 HIL、真实传感器安装或真实送达。

本 sprint 的用户价值很窄：把 `pr5_mandatory_sensor_source_alignment` 之后的真实 2D LiDAR / ToF material follow-up 状态做成 PC gate、Robot diagnostics safe alias 和 `mobile/web` read-only panel。它只回答 PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX` 的下一步材料状态：`pending`、`overdue`、`escalated`、`blocked` 或 `ready_for_reviewer_followup_not_proven`。

本轮不证明 PR #5 resolved、不证明 HIL、不证明 LiDAR/ToF installed、不证明 route/elevator field pass、不证明 true phone/browser、不证明 Objective 5 external proof，也不证明 `delivery_success=true`。

## 背景证据

- `OKR.md` 4.1 当前 Objective 5 约 68%，是最低；Objective 1 约 81%，Objective 2/3/4 约 99%。
- 当前机器只有 Docker/local，没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser 或 verified terminal result materials；因此本轮不继续堆 O5 local metadata。
- 最近两轮 `sprints/2026.05.23_03-04_field-evidence-rerun-acceptance-handoff-intake-followup-escalation-status/final.md` 与 `sprints/2026.05.23_02-03_field-evidence-rerun-acceptance-handoff-intake-review-handoff/final.md` 均扩展 field-evidence acceptance/handoff metadata，均 no OKR percentage lift，且仍缺真实 route/elevator/mobile materials。
- Live PR #5 review threads：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false`，主题是 mandatory 2D LiDAR/ToF sensor assumptions 缺 `docs/vendor/` source / real hardware materials。
- `docs/interfaces/pr5_mandatory_sensor_source_alignment.md` 已把 source-alignment 边界固化为 `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`，并明确本地 vendor 文件不证明项目 2D LiDAR / ToF SKU/source/receipt、采购、安装、接线、电源、标定、HIL-entry、PR thread resolution、Objective 5 external proof 或 delivery success。
- `docs/product/production_hardware_boundary.md` 与 `docs/vendor/VENDOR_INDEX.md` 共同说明：默认硬件集不等于未来 2D LiDAR / ToF 已采购、安装、接线、标定或 HIL-proven；所有硬件事实必须从 `docs/vendor/VENDOR_INDEX.md` 及本地 vendor 文件出发。

## OKR 映射

- Objective 5：最低但本轮不推进。没有真实 external proof，本轮不继续包装 O5 blocker，也不得提高约 68%。
- Objective 1：本轮针对 Objective 1 的 live PR #5 unresolved evidence，但只推进 follow-up escalation status software proof；没有真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、operator HIL report 或 reviewer resolution，Objective 1 约 81% 原则上不提升。
- Objective 2/3：本轮不改变 route/elevator runtime、Nav2/fixed-route、task record、dropoff/cancel 或 delivery result。
- Objective 4：本轮 `mobile/web` 只允许 read-only material follow-up panel，必须保留 `primary_actions_enabled=false`，不证明真实手机/browser 或 production app。

## KR 拆解或更新

本轮不修改 OKR/KR 文案，不预先提升百分比。KR 拆解仅作为当前 sprint 抓手：

1. Hardware：PC gate 消费 `pr5_mandatory_sensor_source_alignment` safe summary 和 follow-up packet，输出 material follow-up status。
2. Robot：diagnostics 提供 safe alias，展示 material status、missing materials、owner/reviewer next step，并 fail closed。
3. Full-Stack：`mobile/web` 展示只读 PR #5 传感器材料跟进升级状态 panel，普通用户主操作继续禁用。
4. Product：三路 worker 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，保持 no OKR percentage lift，除非真实外部/硬件/现场材料出现。

## 本轮核心抓手

Capability:

- `pr5_mandatory_sensor_material_followup_escalation_status`

Evidence boundary:

- `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`

必须保留：

- `source=software_proof`
- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless live reviewer state changes.

## 需要做什么

- Hardware Engineer 实现 PC-only PR #5 mandatory sensor material follow-up escalation status gate、focused tests 和 `docs/interfaces/` 或 hardware/product boundary refs。
- Robot Platform Engineer 增加 Robot diagnostics safe alias、focused diagnostics tests 和 `docs/interfaces/ros_runtime_contracts.md`。
- Full-Stack Engineer 增加 `mobile/web` read-only panel、fixture、focused mobile tests 和 `docs/product/mobile_user_flow.md`。
- Product Owner 在三路工程返回后做 closeout，补齐 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，不得提前预生成。

## 优先级和验收口径

P0:

- PC/Robot/mobile 必须显示 `pr5_mandatory_sensor_material_followup_escalation_status` 和 `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`。
- 只允许输出 `pending`、`overdue`、`escalated`、`blocked`、`ready_for_reviewer_followup_not_proven` 这类补料/复核状态，不允许输出 installed/proven/pass/success/control enabled。
- 必须明确 owner/reviewer 下一步需要的真实材料：2D LiDAR / ToF SKU/source/receipt、采购、安装、接线、电源、标定、HIL-entry、operator HIL report 和 PR #5 reviewer resolution。
- Missing source alignment、missing material follow-up packet、evidence_ref mismatch、unsafe copy、success/control claim、HIL claim、field-pass claim、O5 external-proof claim、PR thread resolved claim 都必须 fail closed。
- Robot/mobile 只消费 safe summary，不暴露 raw artifacts、ROS topics、`/cmd_vel`、串口/UART、WAVE ROVER 参数、credentials、local paths、checksums、tracebacks 或 complete artifacts。
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 不得被本轮改成 true。

P1:

- 工程文档同步到 `docs/interfaces/`、`docs/product/` 或 hardware/product boundary refs。
- Product closeout 同步 `OKR.md` 与 `docs/process/okr_progress_log.md`，并说明 no OKR percentage lift。

## 对应责任 Engineer

- A. `robot-hardware-engineer`：PC gate + tests + `docs/interfaces/` 或 hardware/product boundary refs。
- B. `robot-software-engineer`：Robot diagnostics safe alias + focused diagnostics tests + `docs/interfaces/ros_runtime_contracts.md`。
- C. `full-stack-software-engineer`：`mobile/web` read-only panel + fixture + focused mobile tests + `docs/product/mobile_user_flow.md`。
- D. `product-okr-owner`：A/B/C 完成后的 sprint closeout、OKR/progress narrative 更新和证据边界复核。

## 风险、阻塞和需要补齐的证据链

- O5 blocker：真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser、verified terminal result materials 仍缺失。
- O1 blocker：真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、采购、安装、接线、电源、标定、operator HIL report、PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution 仍缺失。
- O2/O3/O4 真实材料仍缺：真实 task record、Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass、真实 iPhone/Android/browser evidence。
- 本轮只允许进入 `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`，不得写成真实 delivery success、verified terminal result、route/elevator pass、true phone/browser、HIL、O5 external proof、LiDAR/ToF installed 或 PR #5 resolved。

## 需要创建或更新的 sprint 文档

本启动任务创建：

- `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/pre_start.md`
- `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/prd.md`
- `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/tech-plan.md`

工程完成后 Product closeout 才能创建或更新：

- `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/tech-done.md`
- `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.23_04-05_pr5-mandatory-sensor-material-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
