# Sprint 2026.05.20_16-17 Field Evidence Rerun Handoff Intake - Pre Start

## Sprint Type

- sprint_type: epic
- Sprint directory: `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/`
- Start time: 2026-05-20 16:08 Asia/Shanghai
- Product owner: `product-okr-owner`
- Execution model: 4 owner parallel implementation after this planning set is accepted by the main orchestrator.

## Live Evidence Read Before Start

- `AGENTS.md`: requires every sprint to enter sprint records, Epic sprints to create `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`, and implementation/testing to be dispatched to role workers.
- `OKR.md` 4.1, updated 2026-05-20 15:18 Asia/Shanghai: Objective 5 is still lowest at about 68%; Objective 1 is about 81%; Objectives 2/3/4 are about 99% but still lack real field evidence.
- Recent sprint finals:
  - `2026.05.20_12-13_field-evidence-rerun-material-dispatch`: dispatched field rerun material requirements.
  - `2026.05.20_13-14_field-evidence-rerun-callback-intake`: received callback packet material into a safe intake path.
  - `2026.05.20_14-15_field-evidence-rerun-callback-review-decision`: reviewed the callback packet and produced a decision.
  - `2026.05.20_15-16_field-evidence-rerun-callback-review-handoff`: handed the review decision to field owners.
- PR #5 live review evidence:
  - `PRRT_kwDOSWB9286CJ3tQ`: resolved.
  - `PRRT_kwDOSWB9286CJ3tU`: resolved.
  - `PRRT_kwDOSWB9286CJ3tX`: unresolved / `is_resolved=false` / material pending.
  - Manual reply comment `3269642220` is `software_proof`, `not_proven`, and not hardware proof.

## 用户价值和产品北极星

产品北极星：普通手机用户把垃圾交给小车后，小车可以沿固定路线完成送达、电梯 assisted delivery、投放或人工取走，并在失败时让用户和现场 owner 明确知道下一步该补什么证据。

本轮用户价值不是证明真实送达，而是把上一轮 `field_evidence_rerun_callback_review_handoff` 的 owner-safe 交接结果推进到 `field_evidence_rerun_handoff_intake`：现场 owner 回执后，PC gate、Robot diagnostics 和 mobile/web 都能看到交接回执是否可接收、缺什么材料、下一次复跑应由谁执行，并继续阻止任何控制授权误放行。

## OKR 映射

主推进 OKR：Objective 2 / Objective 3 / Objective 4 的 field evidence handoff-intake follow-through。

- Objective 2：把送达、电梯门状态、楼层确认、人工协助、dropoff/cancel completion 和 delivery result 的 owner handoff 变成可回执、可复核的材料入口。
- Objective 3：把真实 Nav2/fixed-route runtime log、route completion signal、field task record 和同一 safe `evidence_ref` 的缺口继续压到回执入口，而不是只停留在 handoff。
- Objective 4：让手机端只读展示“现场证据复跑交接回执”，给普通用户和现场支持同学看懂下一步材料状态，但不改变 Start/Confirm/Cancel gating。

不主推进 Objective 5：`OKR.md` 显示 Objective 5 约 68% 仍最低，但 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。本轮不能再堆一个本地 O5 metadata wrapper。

不主推进 Objective 1：Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending，且现有 reply comment `3269642220` 不是硬件 proof。本机没有真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

## 上轮未完成项和本轮承接

- 上轮已形成 `field_evidence_rerun_material_dispatch -> field_evidence_rerun_callback_intake -> field_evidence_rerun_callback_review_decision -> field_evidence_rerun_callback_review_handoff`。
- 上轮边界固定为 `software_proof` / `not_proven` / `safe_to_control=false` / `delivery_success=false` / `primary_actions_enabled=false`。
- 本轮承接点：新增 `field_evidence_rerun_handoff_intake`，消费上一轮 handoff summary 和 owner-safe handoff intake packet，输出 artifact/summary，再向 Robot diagnostics 和 mobile/web 只读展示。

## Blocker 重复消费核对

- O5 external proof blocker 已多轮存在：缺真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。继续做本地 O5 depth 不会改变 Objective 5 约 68% 的核心缺口。
- O1 hardware material blocker 已多轮存在：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending，缺真实 2D LiDAR / ToF 与 WAVE ROVER/UART/HIL 材料。继续做本地 O1 wrapper 会重复消费同一 blocker。
- 本轮不是重复消费同一 blocker，而是承接最近 O2/O3/O4 field evidence 链路的下一步 handoff-intake，使现场 owner 的回执材料可以被软件链路安全接收和展示。

## 初始验收边界

- 必须保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不得声称 HIL、真实 route/elevator field pass、真实 phone/browser、O5 external proof、真实投放、dropoff/cancel completion 或 delivery success。
- 所有产品、Robot 和 mobile copy 必须继续明确：本机没有真实硬件，只有 Docker；本轮是 metadata-only / fail-closed handoff-intake software proof。

## 需要创建或更新的 Sprint 文档

- 本计划阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实施完成后必须更新：`tech-done.md`、`side2side_check.md`、`final.md`。
- Product closeout 阶段还必须更新：`OKR.md`、`docs/process/okr_progress_log.md`。
