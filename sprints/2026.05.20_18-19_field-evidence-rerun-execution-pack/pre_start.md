# Field Evidence Rerun Execution Pack Pre-Start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.20_18-19_field-evidence-rerun-execution-pack`
- Planned start: 2026-05-20 18:00 Asia/Shanghai
- Product owner: Product Manager / OKR Owner
- Required implementation workers: Autonomy Algorithm Engineer, Robot Platform Engineer, User Touchpoint Full-Stack Engineer
- Product closeout: after the three Engineer workers return changed files, validation snippets, failures, and remaining risks
- Scope of this Product handoff: planning documents only. Do not write product code or test code in this handoff.

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给低成本 ROS2 小车后，小车能沿固定路线完成送达、电梯 assisted delivery、投放或人工取走，并且每一次结果都有可回放证据。

本轮价值是把上一轮 `field_evidence_rerun_queue` 的 queue candidate 变成 field owner 可执行的复跑执行包。执行包需要回答现场 owner 的五个问题：按什么步骤复跑、需要准备哪些材料、谁负责回填、同一 safe `evidence_ref` 如何保持一致、什么情况算 fail/pass 或需要回填。它仍然只是软件证据链的下一环，不是现场复跑本身。

本轮必须保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，证据边界固定为 `software_proof_docker_field_evidence_rerun_execution_pack_gate`。

## Evidence Basis

- `OKR.md` 4.1 当前最低 Objective 5 约 68%。它仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。不能继续把本地 O5 metadata 当进度。
- Objective 1 约 81%。PR #5 已 merge，但 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`；manual reply `3269642220` 不是硬件 proof。本机没有 WAVE ROVER/UART/HIL。
- PR #6 已 merge，属于 README docs-only；无 runtime、hardware、HIL、true phone/browser 或 O5 external tests。
- 最新 sprint `sprints/2026.05.20_17-18_field-evidence-rerun-queue/final.md` 完成了 `field_evidence_rerun_queue`，边界是 `software_proof_docker_field_evidence_rerun_queue_gate`。剩余风险是需要 field owner 提供同一 safe `evidence_ref` 的真实 task record、Nav2/fixed-route runtime log、route completion signal、电梯门/楼层/人工协助、dropoff/cancel completion、delivery result、真实 phone/browser evidence。
- `docs/product/mobile_user_flow.md` 已规定 mobile/web 证据 panel 必须只读，不能暴露 raw JSON、ROS topic、`/cmd_vel`、串口/UART、凭证、local paths、完整 artifact、success/control copy，也不能绕开 Start Delivery / Confirm Dropoff / Cancel 的既有 fail-closed gating。

## OKR Mapping

- Objective 2: primary beneficiary. Execution pack turns route/elevator rerun from queue candidate into现场可执行步骤和回填口径，但不证明 delivery success。
- Objective 3: primary beneficiary. Execution pack要求真实 Nav2/fixed-route runtime log、route completion signal、task record 和同一 safe `evidence_ref`，帮助路线证据进入可复核状态。
- Objective 4: supporting beneficiary. 手机端只读 panel 让非 ROS 用户知道现场复跑执行包状态、owner handoff 和缺口，但不能启用主操作。
- Objective 1: no progress claim. PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 material pending，`3269642220` 仍只是 published reply，不是 WAVE ROVER/UART/HIL 或 2D LiDAR / ToF proof。
- Objective 5: no progress claim. O5 数字最低，但外部证明材料仍不在本 Docker-only 主机内。

## KR Breakdown Or Update

1. KR-Autonomy: create the canonical PC execution-pack gate for `field_evidence_rerun_execution_pack`, consuming the previous `field_evidence_rerun_queue` summary and emitting execution steps, material templates, same-`evidence_ref` rules, fail/pass thresholds, owner handoff, and backfill instructions.
2. KR-Robot: expose `robot_diagnostics_field_evidence_rerun_execution_pack_summary` as a safe diagnostics alias using metadata only, with no raw artifacts or control authorization.
3. KR-Full-stack: add a mobile/web read-only “现场证据复跑执行包” panel that explains execution-pack state and missing materials without sending commands.
4. KR-Product: after engineering evidence lands, update `OKR.md`, `docs/process/okr_progress_log.md`, `tech-done.md`, `side2side_check.md`, and `final.md` conservatively; keep progress unchanged unless real materials arrive.

## Core Lever

The core lever is execution readiness, not proof inflation. The queue candidate already says a rerun can be scheduled as metadata; this sprint should give the field owner a concrete execution pack that can be carried to the real environment, run with one safe `evidence_ref`, and then backfilled for review.

## Priority And Acceptance

Priority order:

1. Autonomy defines the canonical execution pack schema and CLI behavior.
2. Robot exposes only the safe execution-pack summary.
3. Full-stack renders the package read-only on mobile/web.
4. Product later closes out with conservative OKR/progress wording after evidence lands.

Acceptance requires all surfaces to preserve:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- evidence boundary `software_proof_docker_field_evidence_rerun_execution_pack_gate`

## Risks, Blockers, And Evidence Chain

- O5 remains blocked by missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, and external phone/browser proof.
- O1 remains blocked by missing WAVE ROVER/UART/HIL and PR #5 real 2D LiDAR / ToF materials. `PRRT_kwDOSWB9286CJ3tX` must remain unresolved/material pending until reviewer and real materials change that state.
- O2/O3/O4 still need real task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor/human assistance evidence, dropoff/cancel completion, delivery result, and true phone/browser evidence.
- This sprint must not claim true field rerun, real Nav2, real route/elevator field pass, HIL, O5 external proof, PR #5 resolved, or delivery success.

## Sprint Documents To Create Or Update

This Product planning handoff creates:

- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/pre_start.md`
- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/prd.md`
- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/tech-plan.md`

Implementation and closeout later must update:

- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/tech-done.md`
- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/side2side_check.md`
- `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- relevant `docs/` pages touched by Engineering, especially PC evidence, ROS runtime, and mobile user flow docs
