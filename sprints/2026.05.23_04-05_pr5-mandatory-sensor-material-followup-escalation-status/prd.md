# PR #5 Mandatory Sensor Material Follow-Up Escalation Status PRD

Run time: 2026-05-23 04:05 Asia/Shanghai

## 用户价值和产品北极星

北极星：普通手机用户不需要懂 ROS2、传感器采购、HIL、PR review thread 或 `docs/vendor/` source tree，也能通过支持人员的安全证据链知道小车是否具备继续现场验收的硬件前提；当 2D LiDAR / ToF material 仍缺失时，系统必须明确“缺什么、谁补、是否逾期、是否应升级”，而不是把 source alignment 或本地 gate 当作真实安装完成。

本轮产品价值：在 `pr5_mandatory_sensor_source_alignment` 之后新增 material follow-up escalation status，把 PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX` 的真实材料缺口转成 PC/Robot/mobile 三端一致的补料状态。它帮助 owner/reviewer 聚焦下一步真实材料，而不是继续堆 Objective 5 local metadata 或重复 field-evidence handoff metadata。

## 问题定义

`pr5_mandatory_sensor_source_alignment` 已回答“当前 mandatory sensor assumptions 有哪些本地 vendor/source 边界，哪些仍是 hardware_material_pending”。但 source alignment 只回答边界，不回答 follow-up 状态：材料是否仍 pending、是否 overdue、是否已 escalated、是否 blocked，或是否 ready for reviewer follow-up but still not proven。

如果没有本轮状态层，PR #5 `PRRT_kwDOSWB9286CJ3tX` 容易长期停留在 unresolved 状态，support 也容易把 “source alignment 已完成” 误读为 “2D LiDAR / ToF material 已真实到位”。

## OKR 映射

- Objective 5 仍最低，约 68%。本轮不直接针对 O5，因为没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实 phone/browser 或 verified terminal result materials；最近 local metadata 已重复且不产生 OKR lift。
- Objective 1 约 81%。本轮针对 Objective 1 的 live PR #5 unresolved review evidence，推进 `PRRT_kwDOSWB9286CJ3tX` 所需真实材料 follow-up 状态；但不提升 O1，除非真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF materials 或 reviewer resolution 到位。
- Objective 2/3/4：本轮不证明 route/elevator/mobile 真实执行，只通过 Robot/mobile 只读展示保持 fail-closed 用户触点。

## KR 拆解或更新

本轮不改 OKR/KR，只对现有 KR 做 sprint-level 拆解：

- KR-A：Hardware PC gate 给出 PR #5 mandatory sensor material status：`pending`、`overdue`、`escalated`、`blocked`、`ready_for_reviewer_followup_not_proven`。
- KR-B：Robot diagnostics 只暴露 safe summary alias，保持 `safe_to_control=false`。
- KR-C：mobile/web 只显示 read-only material follow-up panel，保持 Start Delivery、Confirm Dropoff、Cancel 禁用。
- KR-D：Product closeout 记录 no OKR percentage lift，并把 `software_proof` 与真实 HIL、真实传感器安装、PR reviewer resolution、O5 external proof 分开。

## 范围内

- Capability 名称：`pr5_mandatory_sensor_material_followup_escalation_status`。
- Evidence boundary：`software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`。
- PC-only material follow-up escalation status artifact and summary。
- Robot diagnostics safe alias。
- `mobile/web` read-only material follow-up status panel and fixture。
- Targeted unit tests、fixture validation、scoped docs updates。
- Sprint closeout、OKR/progress log narrative update after engineering completion。

## 范围外

- 不证明 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved，除非 reviewer live thread 实际 resolved。
- 不证明 2D LiDAR / ToF 已采购、安装、接线、电源确认、标定、HIL-entry 或 Nav2/SLAM accepted。
- 不证明真实 WAVE ROVER/UART/HIL、真实 `/odom`、`/imu/data`、`/battery`。
- 不证明真实 delivery、delivery result、dropoff/cancel completion 或 `delivery_success=true`。
- 不证明真实 route/elevator field pass、Nav2/fixed-route runtime pass 或 route completion signal。
- 不证明 true phone/browser、真实 iPhone/Android behavior、production app 或 PWA prompt/userChoice。
- 不证明 Objective 5 external proof、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 不新增机器人控制 endpoint、material upload route、ACK/cursor route、review route、handoff route、follow-up route 或 hidden primary-action enablement。

## 用户/支持人员流程

1. Hardware owner 提供 `pr5_mandatory_sensor_source_alignment` safe summary 和 material follow-up packet。
2. PC-only gate 判断真实材料是否仍 pending、是否 overdue、是否应 escalated、是否 blocked、或是否 ready for reviewer follow-up but not proven。
3. Robot diagnostics 暴露 safe alias，support 可在 diagnostics 中看到 PR #5 material follow-up status 和缺口。
4. `mobile/web` 只读 panel 让 phone/support 视角看到材料状态，但主操作保持禁用。
5. Product closeout 记录本轮只完成 Docker/local software proof，等待真实 2D LiDAR / ToF material、HIL 或 reviewer resolution。

## 需要催补的真实材料

所有材料必须绑定同一 safe `evidence_ref`，不得包含 credentials、raw serial paths、完整本地路径或 raw artifacts：

- 2D LiDAR SKU、vendor/source、receipt 或 procurement record。
- ToF SKU、vendor/source、receipt 或 procurement record。
- 安装位置、机械固定和遮挡/净空材料。
- 接线、电源预算和供电安全材料。
- 标定计划或标定结果。
- HIL-entry 材料、operator HIL report。
- 与 PR #5 `PRRT_kwDOSWB9286CJ3tX` 对应的 reviewer follow-up / resolution evidence。

## 验收口径

必须满足：

- 输出中包含 `pr5_mandatory_sensor_material_followup_escalation_status`。
- 输出中包含 `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`。
- 所有 summary 保留 `source=software_proof`、`software_proof`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- Follow-up status 只能表达 `pending`、`overdue`、`escalated`、`blocked`、`ready_for_reviewer_followup_not_proven`，不能表达完成、通过、已安装、HIL 通过、可控制或送达成功。
- Evidence-ref mismatch、missing source alignment、missing material packet、unsafe wording、success/control wording、external-proof/HIL/PR-resolution claim 均 fail closed。
- `mobile/web` Start Delivery、Confirm Dropoff、Cancel 在 fixture 下保持禁用。
- Product closeout 不提高 OKR 百分比，除非真实材料出现。

## 责任 Engineer

- `rober-hardware-engineer`：PC gate + tests + docs/interfaces or docs/hardware/product boundary refs。
- `robot-software-engineer`：Robot diagnostics safe alias + tests + runtime docs。
- `full-stack-software-engineer`：`mobile/web` read-only panel + fixture + tests + mobile docs。
- `product-okr-owner`：工程完成后的 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 风险与证据链缺口

- 本轮可能被误读为 PR #5 resolved 或 sensor installed；文案必须使用 `not_proven`、`hardware_material_pending` 和 fail-closed 状态，避免 “installed/pass/success/ready to control”。
- 如果 owner/reviewer packet 包含 raw logs、local paths、credentials、serial/UART details、ROS topics 或 complete artifacts，PC/Robot/mobile 必须拒绝或过滤。
- 当前没有真实 O5/O1/O2/O3/O4 材料，Product closeout 必须保守写 no OKR percentage lift。

## 需要创建或更新的 sprint 文档

启动阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

工程完成后再创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
