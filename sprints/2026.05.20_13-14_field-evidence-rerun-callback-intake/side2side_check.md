# Sprint 2026.05.20_13-14 Field Evidence Rerun Callback Intake - Side2Side Check

## 1. 验收对照

| PRD / Tech Plan 验收口径 | 收口判断 | 证据 |
| --- | --- | --- |
| PC gate 输出 `trashbot.field_evidence_rerun_callback_intake.v1` 和 summary v1 | 通过 | Autonomy worker 新增 PC gate、5 个 unittest、README 与 evidence contract；验证 `Ran 5 tests in 0.051s OK`。 |
| callback packet 缺失、字段缺失、schema 不支持、same evidence ref 不匹配、unsafe copy 或 success/control flag 时 fail closed | 通过 | Autonomy tests 覆盖 missing/bad JSON/unsupported/mismatch/unsafe/success/unknown class；边界为 `software_proof_docker_field_evidence_rerun_callback_intake_gate`。 |
| Robot diagnostics 只读暴露 safe alias | 通过 | Robot worker 新增 `robot_diagnostics_field_evidence_rerun_callback_intake_summary`，diagnostics unittest `Ran 229 tests in 0.695s OK`。 |
| mobile/web 只读显示 accepted/missing/rejected/blocked，且控制 gating 不变 | 通过 | Full-Stack worker 新增“现场证据复跑回执入口”panel、fixtures 和 tests；`mobile/web` tests `Ran 165 tests in 1.157s OK`。 |
| 文档同步 | 通过 | `pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 已同步。 |
| Product closeout 保守更新 OKR 和 progress log | 通过 | `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md` 已更新，百分比保持 O5 约 68%、O1 约 81%、O2/O3/O4 约 99%。 |

## 2. 用户价值侧验收

本轮把现场复跑材料的产品状态从“已派发要求”推进到“可提交回执并统一校验”。对普通手机用户和现场支持同学来说，新增价值是能在 mobile/web 看到哪些真实材料 accepted、missing、rejected 或 blocked，以及下一步由谁补齐什么材料；不需要阅读 raw artifact、ROS topic、serial/UART、WAVE ROVER detail 或 GitHub review thread。

## 3. 证据边界复核

本轮所有 surfaces 必须保持：

- `software_proof_docker_field_evidence_rerun_callback_intake_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

未发现 engineer 结果要求上调 OKR 百分比。本轮不证明真实 external cloud proof、真实硬件/HIL、真实 route/elevator field pass、真实 phone/browser、dropoff/cancel completion 或 delivery success。

## 4. PR #5 线程状态

- `PRRT_kwDOSWB9286CJ3tQ`：resolved。
- `PRRT_kwDOSWB9286CJ3tU`：resolved。
- `PRRT_kwDOSWB9286CJ3tX`：unresolved / material pending。
- manual reply `3269642220` 是保守人工回复，不是 2D LiDAR / ToF、WAVE ROVER/UART/HIL 或现场硬件 proof。

## 5. 剩余验收缺口

仍需现场 owner 回填同一 safe `evidence_ref` 下的真实材料：route completion signal、field task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助 summaries、dropoff completion、cancel completion、delivery result、真实手机/browser evidence，以及 PR #5 要求的真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
