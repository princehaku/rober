# Sprint 2026.05.15_06-07 Route Task Field Run Console - Side2Side Check

sprint_type: epic

## 1. 验收对象

本轮验收对象是 `software_proof_docker_route_task_field_run_console_gate`，目标是确认三条工程 worker 产物是否共同形成 field-run 准备台闭环：

- PC/operator CLI 能生成现场运行步骤、材料采集清单和 same `evidence_ref` verdict。
- Robot diagnostics 只能 metadata-only 消费 summary。
- `mobile/web` 只能只读展示 field-run summary，不改变 Start/Confirm/Cancel gating。
- Product closeout 必须把边界写入 sprint 文档、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 2. 需求对照

| PRD/Tech-plan 要求 | 验收结论 | 证据 |
| --- | --- | --- |
| 输出 `software_proof_docker_route_task_field_run_console_gate` | 通过 | Task A CLI、Task B diagnostics、Task C mobile panel 均按该 boundary 消费或展示。 |
| 保持 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` | 通过 | 三条 worker 均固定 false / not_proven；closeout 与 OKR 同步保留。 |
| 缺材料、坏 JSON、schema/boundary mismatch、unsafe summary fail closed | 通过 | Task A 覆盖缺材料、坏 JSON、unsupported schema/boundary、`evidence_ref` mismatch、unsafe summary、`primary_actions_enabled=true`、输入含 `delivery_success=true`；Task B/C 也覆盖 unsafe/fail-closed 消费。 |
| Robot diagnostics 不触发 collect/dropoff/cancel/ACK/Nav2/HIL | 通过 | Task B diagnostics unittest `Ran 67 tests in 0.053s OK`，文档补充 metadata-only contract。 |
| Mobile panel 只读且 phone-safe | 通过但有补验缺口 | Task C unittest `Ran 37 tests in 0.073s OK`、`node --check` pass；Browser 渲染补验因 `iab` 不可用未运行。 |
| 更新相关 docs | 通过 | `docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 已由对应 worker 更新。 |

## 3. OKR 最低优先级复核

本轮前 `OKR.md` 4.1 最低完成度是 Objective 2 和 Objective 3，均约 65%；Objective 5 约 66%，Objective 1/4 约 73%。本 sprint 针对 O2/O3，理由仍成立：Docker-only 主机无法补齐 O5 外部材料，也无法直接制造真实 Nav2/fixed-route 或 HIL，但可以把下一次真实 field-run 的操作步骤、材料采集和 same `evidence_ref` gate 固化。

收口判断：

- Objective 2 可从约 65% 保守上调到约 66%，因为 field-run console 把任务状态、dropoff/cancel 材料状态、失败/恢复原因和 operator next steps 转成现场可执行准备台。
- Objective 3 可从约 65% 保守上调到约 66%，因为 execution pack、route status、task record 和 completion signal 进入同一 `evidence_ref` 的 PC/operator 准备台，并被 Robot/mobile 只读复用。
- Objective 1、4、5 不上调。

## 4. 边界核对

本轮不证明以下内容：

- 不是真实 Nav2/fixed-route。
- 不是真实路线采集。
- 不是 WAVE ROVER、真实串口/UART、HIL。
- 不是同一 `evidence_ref` 上车实机复账。
- 不是真实 dropoff/cancel completion。
- 不是 `delivery_success=true` 或真实送达。
- 不是真实手机/browser、production app 或真实 PWA prompt/user choice。
- 不是 Objective 5 external proof；not real 公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 5. 结论

验收通过，证据边界为 `software_proof_docker_route_task_field_run_console_gate`。本轮可以更新 closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`，但只能保守提升 Objective 2 与 Objective 3 到约 66%，并必须保留真实运行、硬件、手机/browser 和 O5 external proof 缺口。
