# Sprint 2026.05.18_04-05 Route Task Field Retest Material Pack - Side2Side Check

sprint_type: epic

## 1. 用户价值对照

目标用户价值：现场 owner 拿到上一轮 result review handoff 后，必须知道下一次真实 route/elevator 回填要采什么材料、用哪个 safe `evidence_ref`、由谁采、如何提交 callback、如何 rerun。

本轮结果：`route_task_field_retest_material_pack` 已把 handoff 转成 field capture checklist、callback payload skeleton、owner work orders 和 rerun commands，并通过 PC gate / Robot diagnostics / mobile/web 只读面一致暴露。该结果满足“准备真实回填”的产品价值，但不等同真实现场通过。

## 2. OKR 映射对照

- Objective 2：满足 route/elevator field materials 的准备链路，把 PR #4 主链路要求推进到可执行材料包；仍不是真实送达、电梯通过、dropoff/cancel completion 或 delivery success。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 等真实路线证据纳入 callback skeleton；仍不是实际路线采集或 Nav2/fixed-route 实跑。
- Objective 4：手机端可只读查看材料包，且控制按钮授权不变；仍不是真实手机/browser 或 production app proof。
- Objective 5：不推进；没有真实外部云、4G、OSS/CDN、DB/queue 或 worker/cutover proof。
- Objective 1：不推进；没有真实 WAVE ROVER、UART、HIL packet 或 PR #5 真实硬件 source 材料。

## 3. 验收口径对照

- PC gate：已保留旧 `--material-dir` 兼容并新增 handoff 模式，输出 material pack artifact / summary，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot diagnostics：已新增 `robot_diagnostics_route_task_field_retest_material_pack_summary` alias 和 nested diagnostics 消费，保持 metadata-only。
- mobile/web：已新增只读“路线/电梯现场材料包”面板，copy/export whitelist-only，Start / Confirm / Cancel gating 不变。
- Product：已更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`。

## 4. 证据边界检查

本轮边界固定为 `software_proof_docker_route_task_field_retest_material_pack_gate`。以下均未发生，也不得在 OKR 中写成已完成：

- 真实 route/elevator field pass。
- 真实 Nav2/fixed-route。
- 真实 task record / completion signal。
- 真实 dropoff/cancel completion。
- `delivery_success=true`。
- 真实手机/browser、production app 或 PWA prompt/user choice。
- HIL、WAVE ROVER、UART 或真实硬件 feedback。
- O5 external proof。

## 5. Side2Side 结论

验收结论：通过 Product side2side。A/B/C worker 证据覆盖本轮 PRD 和 tech-plan 的软件证明口径；OKR 只保持 Objective 2 / 3 / 4 约 99%，Objective 1 约 81%，Objective 5 约 68%，没有把 material pack 写成真实现场闭环。
