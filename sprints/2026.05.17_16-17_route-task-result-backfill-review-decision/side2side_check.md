# Sprint 2026.05.17_16-17 Route Task Result Backfill Review Decision - Side2side Check

sprint_type: epic

## 1. 对照结论

状态：`PASS_SOFTWARE_PROOF_DOCKER_ONLY`。

本次 side-by-side check 对照 `prd.md`、`tech-plan.md` 和工作区实际文件。A/B/C 工程输出已落地，Product closeout 按完成收口，但证据边界仍是 Docker/local software proof。

## 2. 需求对照

| 验收项 | 期望 | 当前工作区证据 | 结论 |
| --- | --- | --- | --- |
| PC review decision gate | 新增 `route_task_field_retest_result_backfill_review_decision` artifact / summary | `pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py` 和测试存在；required boundary / schema / material status 字段可检索 | 通过 |
| Robot diagnostics consumer | 只读展示 review decision summary，fail closed | `operator_gateway_diagnostics.py` 和 diagnostics test 已包含 `route_task_field_retest_result_backfill_review_decision` / `_summary` consumer | 通过 |
| mobile/web panel | 只读“路线任务回填复核决策” panel，copy/export whitelist-only | `mobile/web/app.js`、fixture、mobile test、`docs/product/mobile_user_flow.md` 已包含 panel、safe copy 和 `blocked copy unavailable` | 通过 |
| Evidence boundary | `software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`，`not_proven`，`delivery_success=false`，`primary_actions_enabled=false` | PC / Robot / mobile / docs / closeout 均可检索；边界未被写成真实 field pass 或 O5 proof | 通过 |
| OKR closeout | A/B/C 全部通过后可考虑 O2/O3 约 96% -> 约 97% | A/B/C 验证通过，Product required `rg` 与 scoped `git diff --check` 通过 | 通过 |

## 3. OKR 最低优先级核对

Objective 5 仍约 68%，是数值最低 Objective，但缺真实 external proof。本轮选择 Objective 2 / Objective 3 的理由成立：PR #4 elevator-assisted delivery 主线需要把上一轮 result backfill 推进到 review decision；PR #5 hardware materials 仍缺真实 2D LiDAR / ToF source、receipt、procurement、installation、wiring、power、calibration 和 HIL-entry，不能继续包装。

本轮 Objective 2 和 Objective 3 从约 96% 保守更新到约 97%；Objective 1 保持约 77%，Objective 4 保持约 99%，Objective 5 保持约 68%。

## 4. 验收证据片段

- Task A：py_compile pass；focused unittest `Ran 5 tests ... OK`；CLI `--help` pass；required `rg` pass；scoped `git diff --check` pass。
- Task B：py_compile pass；diagnostics unittest `Ran 150 tests in 0.232s OK`；required `rg` pass；scoped `git diff --check` pass。
- Task C：mobile unittest `Ran 46 tests in 0.163s OK`；`node --check mobile/web/app.js` pass；required `rg` pass；scoped `git diff --check` pass。
- Product：required closeout `rg` pass；scoped `git diff --check` pass。

## 5. 剩余风险

本轮形成的是可执行 review decision surface，不是真实现场证明。仍需真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 completion signal、真实 door/floor/human-assistance/dropoff/cancel/delivery result、真实手机/browser、WAVE ROVER、UART、HIL 和 O5 external proof。
