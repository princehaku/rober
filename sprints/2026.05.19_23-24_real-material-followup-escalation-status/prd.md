# Sprint 2026.05.19_23-24 Real Material Followup Escalation Status - PRD

## 1. 用户价值和产品北极星

产品北极星：把 `rober` 做成普通手机用户可用、现场 owner 可验收、Engineer 可复盘的低成本 ROS2 自主垃圾投递机器人。

本轮 PRD 的用户价值是把真实材料缺口从“模板和回填入口”推进成“可追责的升级状态”：

- 现场 owner 能看到每个 material group 的负责人、到期状态、阻塞原因、下一份必须补齐的证据和升级级别。
- Product 能基于 follow-up status 判断是否应继续催 O5 external proof、O1 / PR #5 hardware proof、PR #4 route/elevator proof 或 O4 real phone proof。
- Engineer 能把状态接入 PC gate、Robot diagnostics 和 mobile/web，只做 read-only / fail-closed 展示。
- Reviewer 能看到 `PRRT_kwDOSWB9286CJ3tX` 仍是 `blocked_pending_real_materials`，直到 mandatory sensor baseline 的 `docs/vendor/` source citation 与真实材料齐备。

## 2. OKR 映射

### Objective 5：云中转 + OSS/CDN 数据通路产品化

- 当前约 68%，数字最低。
- 本轮映射：为 O5 external material group 计算 owner、due_status、blocked_reason、next_required_evidence、escalation_level、rerun command/status summary。
- 真实提升条件：必须拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/cutover 等 external proof。
- 不提升条件：Docker-only follow-up status 只是 `software_proof_docker_real_material_followup_escalation_status_gate`。

### Objective 1：硬件协议可信底盘

- 当前约 81%，下一低项。
- 本轮映射：为 O1 / PR #5 hardware group 输出 WAVE ROVER/UART/HIL、2D LiDAR / ToF SKU/source/procurement/installation/wiring/power/calibration/HIL-entry、vendor citation blocker 的升级状态。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 必须保持 unresolved / `blocked_pending_real_materials`，直到真实 source/material 经过后续 review。

### Objective 2 / Objective 3：送达任务、电梯 assisted delivery、导航与固定路线

- 当前均约 99%，但缺真实 route/elevator field materials。
- 本轮映射：为 PR #4 route/elevator group 输出 Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material、delivery_result 的 follow-up status。
- 不提升条件：没有真实 route/elevator evidence 时，不得写成 field pass、delivery success 或 dropoff/cancel completion。

### Objective 4：手机用户体验与量产边界

- 当前约 99%，但缺真实手机和 production app 验收。
- 本轮映射：为 O4 real phone group 输出真实 iPhone/Android behavior、production app、PWA prompt/user choice、true phone/browser acceptance 的 owner/due/escalation 状态。
- 不提升条件：mobile/web 只读 panel 不是真实手机/browser proof。

## 3. KR 拆解或更新

本轮不直接更新 OKR 百分比；只定义后续可验收输入：

- KR-F1：每个 material group 必须输出 `field_owner`、`due_status`、`blocked_reason`、`next_required_evidence`、`escalation_level`、`rerun_command`、`rerun_status_summary`。
- KR-F2：支持四组 material group：`o5_external`、`o1_pr5_hardware`、`pr4_route_elevator`、`o4_real_phone`。
- KR-F3：follow-up status 必须兼容 `real_material_manifest_template` 和 `real_material_evidence_intake` 的 group 语义，不能另起一套证据分类。
- KR-F4：Robot diagnostics 和 mobile/web 只能展示 sanitized summary，不读取 raw manifest、raw materials、credentials、checksum、完整日志或 control 字段。
- KR-F5：所有输出必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 4. 本轮核心抓手

核心抓手是 `real_material_followup_escalation_status`，不是另一个材料 proof wrapper。

最小产品形态：

- 一个 PC/evidence gate 或 artifact generator，读取或复用 manifest template / intake summary 语义，输出 follow-up escalation status。
- 一个 Robot diagnostics safe alias，向 operator gateway 暴露 phone-safe / diagnostics-safe summary。
- 一个 mobile/web 只读 panel，让现场 owner 看到 material group 的下一步和升级级别。
- 一组 docs / sprint closeout 口径，明确它只推动现场材料补齐，不证明真实通过。

## 5. 需要做什么

后续实现 sprint 必须完成：

1. 新增 `real_material_followup_escalation_status` artifact / gate，覆盖四类 material group。
2. 为每组材料计算 owner、due_status、blocked_reason、next_required_evidence、escalation_level、rerun command/status summary。
3. 将状态与 `real_material_manifest_template` / `real_material_evidence_intake` 对齐，避免重复或冲突字段。
4. Robot diagnostics 增加 safe alias，只读消费 sanitized summary。
5. mobile/web 增加只读 panel，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
6. 更新 `docs/interfaces/`、`docs/product/mobile_user_flow.md` 等相关文档；代码技术注释必须使用中文且比例超过 20%。

## 6. 优先级和验收口径

P0：

- 必须覆盖 Objective 5、Objective 1 / PR #5、PR #4 route/elevator、Objective 4 四组材料。
- 必须出现 `real_material_followup_escalation_status`、`software_proof_docker_real_material_followup_escalation_status_gate`、`Objective 5`、`Objective 1`、`PRRT_kwDOSWB9286CJ3tX`、`blocked_pending_real_materials`。
- 必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

P1：

- Robot 和 Full-Stack 只读展示必须能让现场 owner 明确 next_required_evidence 和 rerun command/status summary。
- Hardware / Autonomy 的材料清单必须和 existing manifest/intake groups 对齐。

P2：

- 提供中文 owner handoff copy，但不能把 handoff copy 当成真实材料。

验收口径：

- 三份规划文档存在。
- required `rg` 命中 sprint 类型、核心 gate、OKR、PR thread、blocker、owner 和实施角色。
- scoped `git diff --check` 对本 sprint 目录通过。

## 7. 对应责任 Engineer

- Product Manager / OKR Owner：本轮负责 PRD、OKR 映射、验收口径和后续 owner 分工。
- Hardware Infra Engineer：主责 O1 / PR #5 material follow-up status；必须读取 `docs/vendor/VENDOR_INDEX.md`，不得猜测 WAVE ROVER、UART、传感器 source、引脚、电压或机械细节。
- Autonomy Algorithm Engineer：主责 PR #4 route/elevator、Nav2/fixed-route、task record、route completion、dropoff/cancel、delivery_result follow-up status。
- Robot Platform Engineer：主责 Robot diagnostics sanitized summary，不能读取 raw materials 或产生控制授权。
- User Touchpoint Full-Stack Engineer：主责 mobile/web 只读 “真实材料升级状态” panel，不能改变主操作 gating。

## 8. 风险、阻塞和需要补齐的证据链

- O5：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover。
- O1 / PR #5：缺真实 WAVE ROVER/UART/HIL packet、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report、2D LiDAR / ToF SKU/source/procurement/installation/wiring/power/calibration/HIL-entry；`PRRT_kwDOSWB9286CJ3tX` 仍是 `blocked_pending_real_materials`。
- PR #4 route/elevator：缺真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、field task record、dropoff/cancel material、delivery_result。
- O4：缺真实 iPhone/Android device behavior、production app、PWA prompt/user choice 和 true phone/browser acceptance。
- 误用风险：如果实现输出 pass/success/control authorization，本轮验收失败，必须退回 `not_proven`。

## 9. 需要创建或更新的 sprint 文档

- 已创建规划目标：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 后续实现必须更新：`tech-done.md`、`side2side_check.md`、`final.md`。
- 后续 closeout 必须按实际交付更新 `OKR.md`、`docs/process/okr_progress_log.md` 和相关 `docs/`，但不得在没有真实材料前提高 OKR 百分比。
