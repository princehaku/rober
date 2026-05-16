# Sprint 2026.05.17_00-01 Route Task Field Retest Material Pack - Side2Side Check

sprint_type: epic

## 1. 对照结论

本轮 PRD / tech-plan 的核心目标是把 field retest 的八类真实材料从散落说明前移为可提交目录、可打包校验、可被 Robot diagnostics 和 mobile/web 只读解释的材料包入口。

对照结果：达到 software proof 验收；未达到也未声称真实 field pass。

统一边界：

- `software_proof_docker_route_task_field_retest_material_pack_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- Docker-only

## 2. 用户价值核对

已满足：

- 现场人员可以按八类材料组织 material directory，而不需要理解 ROS2、Nav2、fixed route、task record、raw JSON、串口或云链路。
- PC CLI 能把材料目录转换成 sanitized artifact / summary，并明确 missing/rejected、same evidence ref 和 operator next steps。
- Robot diagnostics 只读消费 summary，缺失或不安全时 fail closed。
- mobile/web 展示“现场材料包” panel，解释 material completeness、八类材料状态、missing/rejected 和下一步补证动作。

未满足：

- 没有真实现场人员提交的完整材料目录。
- 没有真实路线/电梯现场复测，没有真实 Nav2/fixed-route runtime log、真实 route completion signal 或真实 task record。
- 没有真实手机/browser、production app、WAVE ROVER、真实串口/UART、HIL 或 Objective 5 external proof。

## 3. OKR 映射核对

Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。

- 本轮 material pack 把 `door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result` 的材料入口前移到可打包校验阶段。
- 因为仍是 `not_proven` 和 Docker-only software proof，只能保守从约 84% 更新到约 85%。

Objective 3：可验证导航与固定路线。

- 本轮 material pack 把 `nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record` 纳入同一 `evidence_ref` 的材料包入口。
- 因为没有真实 Nav2/fixed-route 实跑，只能保守从约 84% 更新到约 85%。

Objective 4：手机用户体验与低成本量产边界。

- 本轮 mobile/web 只读 panel 让现场人员在手机侧理解材料完整度、缺失、拒绝原因和下一步。
- 因为不是真实手机/browser 或 production app proof，只能保守从约 93% 更新到约 94%。

Objective 5：云中转 + OSS/CDN 数据通路产品化。

- 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- Objective 5 仍约 66%，不因 `route_task_field_retest_material_pack` 提升。

Objective 1：硬件协议可信底盘。

- 本轮未触达 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或真实 2D LiDAR / ToF 材料。
- Objective 1 保持约 75%。

## 4. 风险边界核对

本轮没有写成：

- 真实 field pass
- 真实 Nav2/fixed-route
- 真实电梯
- HIL
- 真实手机/browser
- dropoff/cancel completion
- delivery success
- Objective 5 external proof

本轮继续保留 PR #4 和 PR #5 缺口：

- PR #4 elevator-assisted delivery 仍缺真实 `door_state`、`target_floor_confirmation`、`human_assistance_note` 和同一 `evidence_ref` 的现场材料。
- PR #5 硬件 baseline / 2D LiDAR / ToF / vendor-source 仍缺真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。

## 5. 验收命令

Product closeout 已执行并通过：

```text
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|Objective 2|Objective 3|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_00-01_route-task-field-retest-material-pack OKR.md docs/process/okr_progress_log.md
pass

git diff --check -- sprints/2026.05.17_00-01_route-task-field-retest-material-pack/tech-done.md sprints/2026.05.17_00-01_route-task-field-retest-material-pack/side2side_check.md sprints/2026.05.17_00-01_route-task-field-retest-material-pack/final.md OKR.md docs/process/okr_progress_log.md
pass
```
