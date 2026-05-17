# Sprint 2026.05.17_09-10 Route Task Field Retest Callback Intake - Side2Side Check

sprint_type: epic

## 1. PRD 对照

| PRD / Tech Plan 验收项 | 本轮结果 | 证据 |
| --- | --- | --- |
| PC callback intake 可消费 dispatch artifact / summary / wrapper / nested JSON | 通过 | Task A 新增 `route_task_field_retest_callback_intake.py` 与 5 个 unittest，CLI `--help` 通过 |
| 输出 `trashbot.route_task_field_retest_callback_intake.v1` 与 `_summary.v1` | 通过 | Task A required `rg` 覆盖 schema 与 `software_proof_docker_route_task_field_retest_callback_intake_gate` |
| 固定 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 | A/B/C required `rg` 与 scoped `git diff --check` 均通过 |
| 缺材料不能采信 callback 进入 result intake | 通过 | Task A 已修复为 `collect_missing_materials_then_rerun_result_intake` |
| Robot diagnostics 只读消费，且不触发 collect/dropoff/cancel/ACK/Nav2/HIL/cursor | 通过 | Task B diagnostics unittest `Ran 140 tests in 0.208s OK` |
| Robot safe summary 保留 `safe_evidence_ref` | 通过 | Task B 已修复 env summary wrapper 误读 `robot_compatible_summary` 的问题 |
| mobile/web 只读展示“现场回执入口” | 通过 | Task C mobile unittest `Ran 36 tests in 0.092s OK`，`node --check mobile/web/app.js` 通过 |
| Start Delivery、Confirm Dropoff、Cancel gating 不变 | 通过 | Task C 测试和 required `rg` 覆盖主操作文案与 fail-closed flags |
| 文档同步 | 通过 | 已更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`，本 Product closeout 更新 sprint / OKR / progress log |

## 2. Evidence Boundary 对照

本轮成立的证据：

- `software_proof_docker_route_task_field_retest_callback_intake_gate`
- Docker-only local callback intake artifact / summary generation and consumption
- Robot diagnostics metadata-only safe summary consumption
- mobile/web phone-safe read-only panel
- A/B/C focused unittest、py_compile、CLI help、`node --check`、required `rg`、scoped `git diff --check`

本轮不成立的证据：

- 真实 route/elevator field pass
- 真实 Nav2/fixed-route runtime
- 真实 route completion signal
- 真实 task record
- 真实 door/floor/human assistance material
- 真实 dropoff/cancel completion
- delivery success
- HIL
- 真实 WAVE ROVER / UART / `T=1001` feedback
- 真实 iPhone/Android 手机或真实 browser 验收
- Objective 5 external proof
- PR #5 2D LiDAR / ToF material proof

## 3. OKR 对照

- Objective 2：通过 callback intake 把 PR #4 route/elevator field material 回填链路从 evidence dispatch 推进到现场回执入口，支持推荐文件名收到状态、缺项、same-`evidence_ref` 检查和下一步回填动作；保守从约 89% 上调到约 90%。
- Objective 3：Nav2/fixed-route runtime log、route completion signal、task record 的材料回填入口更完整，减少现场复测后证据号错配或缺项未登记的风险；保守从约 89% 上调到约 90%。
- Objective 4：mobile/web 新增只读支援 panel，但 O4 已约 99%，且没有真实手机/browser 或 production app proof；保持约 99%。
- Objective 5：本轮无公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover；保持约 68%。
- Objective 1：本轮无真实 WAVE ROVER、UART、HIL、`T=1001` feedback 或 PR #5 2D LiDAR / ToF material proof；保持约 77%。

## 4. 用户验收判断

本轮达成产品侧验收：现场人员可以把 sanitized callback metadata 回填到同一 `evidence_ref` 链路中，PC / Robot / mobile 都能读到安全摘要、缺项和下一步动作。

本轮未达成真实交付验收：仍不能宣称机器人完成路线/电梯现场复测、真实投放、dropoff/cancel completion、delivery success、HIL、真实手机验收或 Objective 5 external proof。
