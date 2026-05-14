# Sprint 2026.05.14_22-03 Route Task Rehearsal Operator Review - Side2Side Check

sprint_type: epic

## 对照目标

本轮 PRD/tech-plan 的验收目标是把 `route_task_rehearsal_execution_bundle.json` 转成操作员可读、phone/support-safe、metadata-only 的 operator review 链路，并在 diagnostics 与 `mobile/web` 中只读展示。控制动作、ACK、cursor、HIL、dropoff/cancel completion 与 delivery success 均不得被该 metadata 放行或证明。

## Side-by-side 核对

| 目标 | 实际结果 | 判定 |
| --- | --- | --- |
| Autonomy 生成 operator review package | 已新增 `pc-tools/evidence/route_task_rehearsal_operator_review.py`，输出 `trashbot.route_task_rehearsal_operator_review.v1`、`software_proof_docker_route_task_rehearsal_operator_review_gate`、`next_rehearsal_decision`、`not_proven`、whitelist-only `safe_copy`、`primary_actions_enabled=false`、`delivery_success=false`。 | 通过 |
| Robot diagnostics 只读消费 review | 已新增 `route_task_rehearsal_operator_review` diagnostics summary，支持 explicit ref 与环境变量；missing/read_error/unsupported schema/crosscheck fail/unsafe copy 均保守降级。 | 通过 |
| metadata-only 不触发控制路径 | Robot 围栏证明不触发 Start/Confirm/Cancel、ACK POST、cursor/persistence、HIL、dropoff/cancel completion 或 delivery success。 | 通过 |
| Mobile 首屏只读展示 | `mobile/web` 新增“路线/任务排练复盘”摘要，展示 overall status、evidence ref、crosscheck/HIL boundary、mismatch、decision、`not_proven` 与 boundary；copy 只用 `safe_copy`。 | 通过 |
| Start/Confirm/Cancel fail-closed 不变 | Full-stack 汇总确认 fail-closed 逻辑未改，operator review 不新增控制授权条件。 | 通过 |
| docs 同步 | 已更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。 | 通过 |
| OKR 边界 | Objective 2/3 可从约 80% 谨慎上调到约 81%；Objective 1/5 不上调；Objective 4 不调整。 | 通过 |

## 用户价值验收

本轮结果让操作员和支持人员可以从一个 review package 或手机首屏摘要中直接看到：本次排练关联的 evidence、crosscheck/HIL 边界、mismatch、下一轮动作建议和未证明项。它减少了翻 raw artifact 的成本，但仍明确告诉用户这不是实机路线、不是投放完成、不是 delivery success。

## 风险边界复核

- `software_proof_docker_route_task_rehearsal_operator_review_gate` 是 Docker/local software proof。
- `not_proven` 仍覆盖真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion 与 delivery success。
- O5 仍没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料。
- O1 仍没有真实硬件、串口、底盘反馈或 HIL。

## Product 判定

验收通过。O2/O3 允许各上调约 1pp 到约 81%，因为本轮确实把任务/路线软件排练证据推进到操作员可读决策与手机只读展示；但本轮不构成真实路线运行、HIL、dropoff/cancel completion、delivery success 或 O5 external proof。
