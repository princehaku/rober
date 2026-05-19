# Sprint 2026.05.19_12-13 Task Terminal Field Material Intake - Side2Side Check

## sprint_type: epic

Run time: 2026-05-19 12:25 Asia/Shanghai。

## 1. 对照对象

本轮对照 `prd.md` / `tech-plan.md` 的验收口径：

- Robot diagnostics 必须提供 `robot_diagnostics_task_terminal_field_material_intake_summary` safe alias。
- mobile/web 必须新增只读“现场材料回填入口”panel。
- Autonomy 必须只读确认 route/elevator/Nav2 evidence fields 不被写成 Objective 3 通过证据。
- Product closeout 必须保守更新 sprint、`OKR.md` 和 `docs/process/okr_progress_log.md`，不得提高 Objective 5 或 Objective 1 真实进度。

## 2. 用户价值核对

用户价值成立但边界保守：现场 owner 后续提交真实 dropoff/cancel terminal materials、route/elevator field materials、real phone/browser evidence 时，Robot diagnostics 和 mobile/web 已有同一 safe `evidence_ref` 的 fail-closed 回填入口，能显示 accepted safe refs、missing materials、next required evidence 和 phone-safe copy。

这不是业务闭环完成。本轮没有真实 field materials、真实手机/browser、真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL 或 O5 external proof。

## 3. 工程结果对照

| 检查项 | 结果 | 证据边界 |
| --- | --- | --- |
| Robot diagnostics safe alias | 通过 worker 验证，`robot_diagnostics_task_terminal_field_material_intake_summary` 已落地 | `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` |
| mobile/web 只读 panel | 通过 worker 验证，“现场材料回填入口”panel 已落地 | 只读展示，不改 Start Delivery、Confirm Dropoff、Cancel gating |
| Autonomy 语义咨询 | 通过只读咨询，route/elevator/Nav2 字段只作为 missing / next-required evidence | 不使用 `route_passed`、`fixed_route_passed`、`nav2_passed`、`field_pass` 或 completion claim |
| Product OKR closeout | 已按 worker 结果收口 | O5 保持约 68%，O1 保持约 81%，O2/O3/O4 保持约 99% |

## 4. 验证结果对照

Robot worker 报告：

```text
py_compile pass
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 206 tests in 0.512s
OK
required rg pass
scoped git diff --check pass
```

Full-Stack worker 报告：

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 122 tests in 0.863s
OK
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py pass
node --check mobile/web/app.js pass
required rg pass
scoped git diff --check pass
```

Browser QA 不计入通过证据：本地 PWA/service-worker 缓存让 in-app browser 停在旧 offline shell，截图命令超时。

## 5. OKR 与 PR 边界核对

- Objective 5：不提高；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1：不提高；没有真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 2D LiDAR / ToF 真实材料。
- Objective 2：只记录 terminal field material intake 可回填性；不证明真实 dropoff/cancel completion、delivery result 或 delivery_success。
- Objective 3：只记录 route/elevator/Nav2 evidence fields 可作为缺材料和下一步证据；不证明真实 route/elevator field pass、真实 Nav2/fixed-route 或 route completion signal。
- Objective 4：只记录手机端只读可见性；不证明真实 iPhone/Android、production app、真实 PWA prompt/user choice 或真实手机/browser external proof。
- PR #4：本轮为 route/elevator terminal field materials 后续回填提供入口，不证明 PR #4 field pass。
- PR #5：本轮不补 2D LiDAR / ToF 真实材料，不改硬件事实。

## 6. 验收结论

本轮达到 PRD/tech-plan 的 software-proof 目标：`task_terminal_field_material_intake` 已形成 Robot diagnostics safe alias + mobile/web 只读 panel + Autonomy 语义边界 + Product OKR closeout。

验收不包含真实现场通过。后续要提高真实 OKR completion，必须补同一 safe `evidence_ref` 下的真实 materials：真实 task record、真实 dropoff/cancel terminal materials、真实 route/elevator field materials、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 delivery result、真实手机/browser evidence，或 O5/O1 对应真实 external / HIL materials。
