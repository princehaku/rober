# Field Evidence Rerun Execution Callback Intake Pre-Start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_01-02_field-evidence-rerun-execution-callback-intake`
- Planned start: 2026-05-21 01:00 Asia/Shanghai
- Product owner: Product Manager / OKR Owner
- Required implementation workers: Autonomy Algorithm Engineer, Robot Platform Engineer, User Touchpoint Full-Stack Engineer
- Product closeout: after the three Engineer workers return changed files, validation snippets, failures, and remaining risks
- Scope of this Product handoff: planning documents only. Do not write product code, test code, OKR.md, or other docs in this handoff.

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给低成本 ROS2 小车后，小车能沿固定路线完成送达、电梯 assisted delivery、投放或人工取走，并且每一次结果都有可回放证据。

本轮价值是把上一轮 `field_evidence_rerun_execution_pack` 之后的真实现场执行回执变成可复核入口。field owner 后续会带着 execution pack 去真实环境执行；本 sprint 只规划一个 callback intake gate，用来消费 execution pack 和 field owner execution callback packet，把回执中的 task record、Nav2/fixed-route runtime log、route completion signal、电梯门/楼层/人工协助、dropoff/cancel completion、delivery result 和真实 phone/browser evidence 分类为 accepted、missing、rejected 或 blocked。

本轮必须保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，证据边界固定为 `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`。它不证明真实现场通过，只证明 Docker/local 可以安全接收和分类现场回执材料。

## Evidence Basis

- `OKR.md` 4.1 当前最低 Objective 5 约 68%。它仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。`OKR.md` §6 明确没有真实 external proof 时不要重复本地 O5 metadata depth。
- Objective 1 约 81%。PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending，要求 vendor sources for mandatory sensor assumptions；本机没有真实 WAVE ROVER/UART/HIL。最近 `hardware_sensor_hil_entry_callback_review_handoff` 已经做过硬件材料 wrapper，不应重复消费同一 blocker。
- PR #6 是 docs-only；没有 runtime、hardware、HIL、true phone/browser 或 Objective 5 external proof。
- 最新 field chain 已到 `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/`。该 sprint final 明确下一步需要 field owner 回填同一 safe `evidence_ref` 的真实 task record、Nav2/fixed-route runtime log、route completion signal、电梯门/楼层/人工协助、dropoff/cancel completion、delivery result 和真实 phone/browser evidence。
- 本机只有 Docker/local software proof，不允许把 callback packet、diagnostics summary、mobile panel 或 accepted material classification 写成真实 field rerun pass、真实 phone/browser pass、HIL、O5 external proof 或 delivery_success。

## OKR Mapping

- Objective 2: primary beneficiary. Callback intake 把 route/elevator 现场复跑回执变成 accepted/missing/rejected/blocked 材料状态，帮助送达闭环进入后续复核；不证明 delivery success。
- Objective 3: primary beneficiary. Callback intake 强制同一 safe `evidence_ref` 的 task record、Nav2/fixed-route runtime log 和 route completion signal，帮助路线证据进入可复核状态。
- Objective 4: supporting beneficiary. 手机端只读 panel 让非 ROS 用户知道执行回执哪些材料被接受、缺失、拒绝或阻塞，但不能启用主操作。
- Objective 1: no progress claim. PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 material pending；本轮不是 WAVE ROVER/UART/HIL、2D LiDAR / ToF vendor source、receipt、installation、wiring、power、calibration 或 HIL-entry proof。
- Objective 5: no progress claim. O5 数字最低，但外部证明材料仍不在本 Docker-only 主机内。

## KR Breakdown Or Update

1. KR-Autonomy: create the canonical PC callback-intake gate for `field_evidence_rerun_execution_callback_intake`, consuming `field_evidence_rerun_execution_pack` plus a field owner execution callback packet and emitting accepted/missing/rejected/blocked material classifications.
2. KR-Robot: expose `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary` as a safe diagnostics alias using metadata only, with no raw artifacts or control authorization.
3. KR-Full-stack: add a mobile/web read-only "现场证据复跑执行回执入口" panel that explains callback intake state and remaining material gaps without sending commands.
4. KR-Product: after engineering evidence lands, update `OKR.md`, `docs/process/okr_progress_log.md`, `tech-done.md`, `side2side_check.md`, and `final.md` conservatively; keep progress unchanged unless real materials appear and are separately verified.

## Core Lever

The core lever is callback classification, not proof inflation. The execution pack tells field owner what to run; this sprint defines how the returned callback packet is accepted or rejected under one safe `evidence_ref`, while preserving a strict Docker/local `software_proof` boundary.

## Priority And Acceptance

Priority order:

1. Autonomy defines the canonical callback-intake schema and CLI behavior.
2. Robot exposes only the safe callback-intake summary.
3. Full-stack renders the callback-intake state read-only on mobile/web.
4. Product later closes out with conservative OKR/progress wording after evidence lands.

Acceptance requires all surfaces to preserve:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- evidence boundary `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`

## Risks, Blockers, And Evidence Chain

- O5 remains blocked by missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, and external phone/browser proof.
- O1 remains blocked by missing WAVE ROVER/UART/HIL and PR #5 real 2D LiDAR / ToF vendor/material evidence. `PRRT_kwDOSWB9286CJ3tX` must remain unresolved/material pending until reviewer and real materials change that state.
- O2/O3/O4 still need real task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor/human assistance evidence, dropoff/cancel completion, delivery result, and true phone/browser evidence.
- This sprint must not claim true field rerun pass, real Nav2, real route/elevator field pass, HIL, O5 external proof, PR #5 resolved, or delivery success.

## Sprint Documents To Create Or Update

This Product planning handoff creates:

- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/pre_start.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/prd.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/tech-plan.md`

Implementation and closeout later must update:

- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/tech-done.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/side2side_check.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- relevant `docs/` pages touched by Engineering, especially PC evidence contracts, ROS runtime contracts, and mobile user flow docs
