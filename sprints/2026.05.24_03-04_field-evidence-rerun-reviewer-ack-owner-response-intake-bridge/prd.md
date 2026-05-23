# Field Evidence Rerun Reviewer ACK Owner Response Intake Bridge PRD

Run time: 2026-05-24 03:04 Asia/Shanghai

## Product North Star

真实证据优先。Docker/local 只能建立 fail-closed 材料回流路径；只有真实外部材料、真实 route/elevator field evidence、真实手机/browser 证据或 HIL 到位后，才允许推进 OKR 百分比或控制能力。

## User Value

现场 owner 已收到 reviewer ACK follow-up escalation status，但如果它停在一个孤立状态里，owner 仍不知道该从哪里回填真实 O2/O3/O4 材料。本 capability 的价值是把该 safe source 接回 owner response intake 主链，让现场 owner 看到：需要补哪类真实材料、必须沿同一 safe `evidence_ref` 回填、当前仍 `not_proven`、不能启用控制、不能当作 delivery success。

## Problem Statement

Objective 5 约 68%，仍是当前最低 Objective，但 `OKR.md` 第 6 节明确只有真实外部材料才继续 O5 completion；本机没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result。

Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，缺真实 2D LiDAR / ToF SKU/source/receipt、安装、接线、标定、HIL-entry、WAVE ROVER powered bench/UART/HIL logs；本机没有真实硬件，只有 Docker。

因此本轮不能重复 O5 local metadata，也不能推进 O1 hardware proof，只能转向 `OKR.md` 指定的下一条 O2/O3/O4 现场材料回流路径：把 field-evidence rerun reviewer ACK follow-up safe source bridge 回 owner response intake 主链。

## OKR Mapping

- Objective 5：最低约 68%，本 sprint 不针对 O5 completion；没有真实外部材料，不能提升百分比。
- Objective 1：约 81%，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；没有真实硬件材料，不能提升百分比。
- Objective 2/O3/O4：本轮服务于现场 route/elevator/dropoff/cancel/phone materials 的 re-entry bridge，但仍不证明真实 field pass。
- Evidence boundary：`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate`。
- Capability：`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`。

## KR Breakdown

KR1 Autonomy / PC gate:

- 扩展 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`，安全接受 reviewer ACK follow-up escalation status source。
- 输出 `source_bridge`，值必须指向 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`。
- 保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 要求真实材料清单包括 task record、dropoff/cancel completion、Nav2/fixed-route runtime log、route completion signal、电梯门状态、楼层确认、人工协助记录、delivery result、route/elevator field pass、真实手机/browser 证据。

KR2 Robot diagnostics safe alias:

- 让 `operator_gateway_diagnostics.py` 的 owner response intake safe alias 能展示 `source_bridge`。
- 只暴露 sanitized bridge summary、source status、same evidence ref、next required evidence 和 false-state flags。
- 拒绝 raw artifacts、credentials、ROS topics、`/cmd_vel`、serial/UART details、ACK/cursor mutation、GitHub mutation 或 robot command hints。

KR3 Full-Stack mobile read-only panel:

- 在 `mobile/web` 既有 owner response intake panel 中展示 bridge summary。
- 展示 source bridge、现场 owner next materials、same evidence ref、`not_proven` 和 false-state flags。
- Start Delivery、Confirm Dropoff、Cancel 必须保持 disabled；`primary_actions_enabled=false` 必须可见或被 tests 覆盖。

KR4 Product / OKR closeout:

- 工程实现后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
- 不改 Objective 5、Objective 1、Objective 2/O3/O4 的百分比。
- 明确本轮是 bridge，不是真实材料、不是 field pass、不是 phone/browser proof、不是 delivery success。

## Core Product Grip

The gate must answer one operational question: "Can the prior reviewer ACK follow-up escalation status safely re-enter the owner response intake mainline so the field owner can provide real O2/O3/O4 materials under the same safe evidence ref?"

It must not imply:

- O5 external proof exists
- PR #5 `PRRT_kwDOSWB9286CJ3tX` is resolved
- real 2D LiDAR / ToF or WAVE ROVER HIL exists
- true phone/browser proof exists
- route/elevator field pass exists
- dropoff/cancel completion or delivery result exists
- delivery_success is true
- robot is safe to control

## Priority And Acceptance Criteria

P0:

- `source_bridge` is emitted and points to the reviewer ACK follow-up escalation status source.
- Same safe `evidence_ref` is enforced or mismatch fails closed.
- All outputs preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate` appears in PC, Robot, mobile, docs, and tests.

P1:

- PC gate, Robot diagnostics and mobile panel list the next true materials required from the field owner.
- Unsafe success/control/raw-material copy fails closed.
- Mobile UI remains read-only and does not add upload, review, ACK, cursor, replay, resubmit, or command actions.

P2:

- Product closeout records no OKR percentage lift and points the next run at real materials, not another local wrapper.
- `docs/process/okr_progress_log.md` records the same evidence boundary after implementation.

## Responsible Engineers

- Autonomy Algorithm Engineer: PC evidence gate, focused tests, `pc-tools` docs and interface doc.
- Robot Platform Engineer: diagnostics safe alias, diagnostics tests, operator gateway docs and product touchpoint docs.
- User Touchpoint Full-Stack Engineer: mobile read-only panel, fixture, UI tests and mobile product docs.
- Product Manager / OKR Owner: closeout docs, `OKR.md`, process log after engineer evidence exists.

## Evidence Chain And Remaining Risks

Required real evidence still missing:

- Objective 5: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/migration/cutover, true phone/browser proof, verified terminal delivery/dropoff/cancel result.
- Objective 1 / PR #5: 2D LiDAR / ToF SKU/source/receipt, procurement, mounting, wiring, power, calibration, HIL-entry, WAVE ROVER powered bench/UART/HIL logs, operator HIL report and reviewer resolution.
- Objective 2/O3/O4: same safe `evidence_ref` with real task record, dropoff/cancel completion, Nav2/fixed-route runtime log, route completion signal, elevator door status, floor confirmation, human assistance note, delivery result, route/elevator field pass and true phone/browser evidence.

Remaining risk: this sprint can make the field-owner material re-entry path actionable, but it cannot prove field success or move OKR percentages until real owner materials arrive.
