# Sprint 2026.05.18_08-09 Route Task Field Retest Drill Console - Side2Side Check

sprint_type: epic

## 1. 验收结论

本轮 Product closeout 验收通过，范围限定为 Docker/local `software_proof_docker_route_task_field_retest_drill_console_gate`。Autonomy、Robot、Full-stack 三个 worker 均完成各自 fenced 验证，并已在 `tech-done.md` 保留验证输出和首轮失败修复记录。

## 2. 用户价值和产品北极星

北极星仍是让普通手机用户最终能完成低成本送垃圾任务；本轮面向现场 operator / support user，把上一轮 `route_task_field_retest_operator_drill` 推进成只读 drill console 摘要，让现场人员可按同一 safe `evidence_ref` 查看 command groups、callback checklist、required outputs、rerun summary 和 safe copy 边界。

本轮不是普通用户一键发车能力，也不改变 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor 或 robot command 授权。

## 3. OKR 映射

- Objective 2：补强 PR #4 route/elevator field material 演练层，把门状态、目标楼层、人工协助、失败接管和复跑材料要求放进 drill console，但保持 `not_proven`。
- Objective 3：补强 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result 的 required outputs / rerun summary，但没有实跑证明。
- Objective 4：mobile/web 和 Robot diagnostics 可只读显示 drill console safe summary，帮助 support 收集材料，不改变主操作路径。
- Objective 1：保持约 81%，因为没有真实 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 PR #5 2D LiDAR / ToF 实物材料。
- Objective 5：保持约 68%，因为没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。

## 4. 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Autonomy gate 顶层验收入口 | 通过 | `tests/test_route_task_field_retest_drill_console.py` 复用 PC evidence 测试；worker 报告 `Ran 5 tests in 0.021s OK`。 |
| Robot diagnostics safe alias | 通过 | 输出 `route_task_field_retest_drill_console`、`route_task_field_retest_drill_console_summary`、`robot_diagnostics_route_task_field_retest_drill_console_summary` 三个 sanitized alias；worker 报告 `Ran 176 tests in 0.345s OK`。 |
| Mobile/web 只读面板 | 通过 | 面板展示 operator command groups、callback checklist、required outputs、rerun summary 和 safe copy；worker 报告 `Ran 72 tests OK` 与 `node --check` 通过。 |
| docs/ 同步 | 通过 | `docs/product/mobile_user_flow.md` 已记录 Robot diagnostics alias 和 mobile panel；`pc-tools/evidence/README.md` 已记录 Autonomy gate。 |
| sprint 留档 | 通过 | `tech-done.md` 已包含 Autonomy、Robot、Full-stack 三段及 Product closeout 边界。 |

## 5. 不可宣称内容

- 不是 route/elevator field pass。
- 不是 Nav2/fixed-route proof。
- 不是 task record/completion signal completed。
- 不是 dropoff/cancel completion。
- 不是 delivery success。
- 不是 HIL、WAVE ROVER、UART、真实串口或真实反馈。
- 不是真实 phone/browser/device proof。
- 不是 Objective 5 external proof。

## 6. 剩余证据链

- PR #4 仍需要真实 route/elevator 现场材料：门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- PR #5 仍需要真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- Objective 5 仍需要真实 external cloud/4G/DB/queue/OSS/CDN/production worker 或真实手机/browser 证据。
