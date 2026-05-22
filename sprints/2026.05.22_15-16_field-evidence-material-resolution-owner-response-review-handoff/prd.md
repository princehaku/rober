# Field Evidence Material Resolution Owner Response Review Handoff PRD

Run time: 2026-05-22 15:04 Asia/Shanghai

## 1. 用户价值和产品北极星

用户价值：field owner、support 和 reviewer 需要把上一轮 owner-response review decision 变成明确的下一步交接动作。当前 accepted / needs-more-evidence / rejected-unsafe / blocked-missing-intake 只是分类结果；如果没有 handoff artifact，现场 owner 仍不知道哪些材料可交 reviewer、哪些要补证、哪些因 unsafe 被拒绝、哪些因为缺 intake 不能继续流转。

产品北极星：`rober` 的目标是普通手机用户可用的低成本 ROS2 送垃圾机器人。材料治理的价值不是制造流程文件，而是让真实 route/elevator/terminal/hardware 材料到位后能安全、可追溯地被复核，最终服务真实送达闭环。本 PRD 不把 handoff 产物当作真实云、真实手机、真实硬件或真实送达。

## 2. OKR 映射

| Objective | Mapping |
| --- | --- |
| Objective 5 | 当前最低，约 68%。本轮继续 field-evidence material-resolution chain，但仅交付 `software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate`，不提升 OKR 百分比。 |
| Objective 1 | 约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false`; comment `3269642220` is software-proof only. 本轮不证明真实 WAVE ROVER/UART/HIL 或 2D LiDAR/ToF material。 |
| Objective 2 | 约 99%。本轮不改变 task_orchestrator、route/elevator runtime、dropoff/cancel result 或 delivery result。 |
| Objective 3 | 约 99%。本轮不证明真实 route collection、Nav2/fixed-route runtime log、route completion signal 或 keyframe field pass。 |
| Objective 4 | 约 99%。本轮 mobile/web 只读展示 handoff summary，保持 `primary_actions_enabled=false`; this is not true phone/browser proof。 |

## 3. KR 拆解或更新

### KR-A: Autonomy / PC gate

Build `field_evidence_material_resolution_owner_response_review_handoff` as a deterministic PC artifact gate that consumes the previous owner-response review-decision artifact or compatible fixture.

Acceptance:

- Produces handoff statuses for accepted, needs-more-evidence, rejected-unsafe, and blocked-missing-intake cases.
- Emits `software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate`.
- Always preserves `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Does not emit raw ROS topics, `/cmd_vel`, serial/UART paths, credentials, local filesystem paths, complete artifacts, checksums, or success claims.

### KR-B: Robot diagnostics safe alias

Expose a sanitized Robot diagnostics summary alias for the handoff artifact.

Acceptance:

- Adds `robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary` or equivalent safe alias.
- Keeps summary read-only and metadata-only.
- Missing/invalid handoff data fails closed to a blocked/not-proven state.
- Does not add Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, serial open, WAVE ROVER command, Nav2, route execution, or robot control behavior.

### KR-C: Full-Stack mobile read-only panel

Add a read-only `mobile/web` panel for the handoff summary.

Acceptance:

- Panel shows handoff status, decision source, safe `evidence_ref`, owner/support/reviewer next steps, missing required evidence, unsafe rejection reasons, evidence boundary, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Panel consumes Robot safe summary first, then compatible nested phone-safe summaries only.
- Start Delivery / Confirm Dropoff / Cancel remain disabled unless the existing independent command-safety gates allow them; this handoff must not enable primary actions.
- The panel text must be Chinese-first for field/support use and must not claim true phone/browser proof.

### KR-D: Hardware read-only PR/vendor boundary consultation

Confirm hardware and PR #5 boundary without changing hardware files.

Acceptance:

- Re-read `docs/vendor/VENDOR_INDEX.md` and relevant vendor/source-boundary docs before any hardware statement.
- Re-state that `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless live evidence says otherwise.
- Confirm this handoff cannot replace real 2D LiDAR/ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry material.
- Produce no product-code, test-code, or hardware-configuration writes.

## 4. 本轮核心抓手

本轮只做 review decision -> review handoff 的产品能力。它把上一轮 decision 变成可交接的行动包，而不是制造新的 intake、重复 escalation、或再次包装同一个 blocker。

The handoff artifact must answer:

- Who should receive this material next: support, field owner, reviewer, or owner intake.
- What is the current safe classification.
- What evidence is missing before review can continue.
- Which materials are rejected unsafe and must not be reused as proof.
- Which blocked cases need intake before any review.

## 5. 需要做什么

1. Create a PC gate and tests for the handoff artifact.
2. Add a Robot diagnostics safe alias and tests.
3. Add a mobile read-only panel, fixture, tests, and product doc update.
4. Perform hardware read-only boundary consultation against vendor docs and PR #5 unresolved evidence.
5. After implementation, update `tech-done.md`, `side2side_check.md`, and `final.md` with validation evidence and no-lift OKR closeout.

## 6. 优先级和验收口径

Priority: P0 for sprint execution, because it is the next actionable rung after `field_evidence_material_resolution_owner_response_review_decision` and does not require real hardware or external cloud materials.

Acceptance gates:

- PC gate, Robot alias, and mobile panel exist and use the same capability name.
- Required proof boundary string appears across PC, Robot, mobile, tests, docs, and sprint closeout.
- All output remains `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Handoff categories cover accepted, needs-more-evidence, rejected-unsafe, and blocked-missing-intake.
- No surface claims O5 external proof, O1 HIL, PR #5 resolution, true phone/browser proof, verified terminal result, route/elevator field pass, or delivery success.

## 7. 对应责任 Engineer

| Priority | Owner | Task |
| --- | --- | --- |
| P0 | Autonomy Algorithm Engineer | PC gate and artifact contract |
| P0 | Robot Platform Engineer | Robot diagnostics safe alias |
| P0 | User Touchpoint Full-Stack Engineer | Mobile read-only handoff panel |
| P0 | Hardware Infra Engineer | Read-only vendor / PR #5 boundary consultation |
| P0 | Product Manager / OKR Owner | Sprint acceptance, no-lift OKR review, closeout docs |

## 8. 风险、阻塞和需要补齐的证据链

- Real O5 evidence remains missing: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, verified terminal delivery/dropoff/cancel result, and delivery success.
- Real O1 evidence remains missing: WAVE ROVER powered bench, UART/HIL logs, `feedback_T1001.log`, `/odom`, `/imu/data`, `/battery`, operator HIL report, real 2D LiDAR/ToF material, and PR #5 reviewer resolution.
- Real O2/O3/O4 evidence remains missing: task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor evidence, human assistance, dropoff/cancel completion, true phone/browser, and route/elevator field pass.
- Handoff artifacts can improve routing quality but cannot close the evidence chain without real owner material backfill.

## 9. 需要创建或更新的 sprint 文档

- Now: `pre_start.md`, `prd.md`, `tech-plan.md`
- During implementation: `tech-done.md`
- During acceptance: `side2side_check.md`
- During closeout: `final.md`

No `OKR.md` update is planned during planning. Any later `OKR.md` update must keep no percentage lift unless real evidence appears.
