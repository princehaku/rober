# Sprint 2026.05.15_02-03 Route Task Field Run Review Console - Side2Side Check

sprint_type: epic

## 1. PRD 对照

| PRD 成功标准 | 验收结果 | 证据 |
| --- | --- | --- |
| 产出 `schema=trashbot.route_task_field_run_review_console.v1` 的 review report | 通过 | Task A 新增 `route_task_field_run_review.py`，固定 boundary `software_proof_docker_route_task_field_run_review_console_gate` |
| 输出 review decision、missing/mismatch、commands、operator next steps、phone-safe summary、`not_proven` | 通过 | Task A targeted tests `Ran 6 tests OK`；mismatch decision reason same `evidence_ref` 返工后复验通过 |
| diagnostics 只读消费 summary | 通过 | Task B 新增 `route_task_field_run_review` / `route_task_field_run_review_summary` metadata-only summary，unittest `Ran 59 tests OK` |
| mobile 首屏只读展示，不改变 Start/Confirm/Cancel gating | 通过 | Task C 新增 read-only panel，mobile unittest `Ran 10 tests OK`，schema 对齐返工后复验通过 |
| 不宣称真实路线、HIL、dropoff/cancel completion 或 delivery success | 通过 | `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 OKR 边界均已写入 closeout |

## 2. OKR 最低优先级回顾

当前最低 Objective 仍是 Objective 5，约 68%。本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料，因此不提升 Objective 5。

本轮转向 Objective 2 / Objective 3 的理由仍成立：field-run intake/crosscheck 已有，但现场复核还缺 operator/support 可读的 review decision 和重跑清单。本轮完成后，Objective 2 / Objective 3 可从约 84% 保守上调到约 85%。

## 3. 用户价值核对

本轮把“材料是否足够、哪里不一致、下一步重跑什么、为什么不能算成功”从工程 JSON 变成 operator/support 可读入口，服务现场 field run 复盘，而不是让用户或现场人员手动比对多份 route/task 材料。

## 4. 边界核对

已明确不证明：

- 真实 Nav2/fixed-route。
- 真实路线采集。
- WAVE ROVER。
- 真实串口/UART。
- HIL。
- 同一 `evidence_ref` 上车复账。
- dropoff/cancel completion。
- delivery success。
- Objective 5 external proof。

## 5. 结论

本轮满足 PRD 的软件 proof 验收口径，可以作为 Objective 2 / Objective 3 的保守进度增量；不能作为 Objective 1、Objective 4 或 Objective 5 的进度增量，也不能替代真实现场联跑或硬件证据。
