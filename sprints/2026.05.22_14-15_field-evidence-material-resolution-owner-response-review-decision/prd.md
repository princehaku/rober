# Field Evidence Material Resolution Owner Response Review Decision PRD

Run time: 2026-05-22 14:03 Asia/Shanghai

## 用户价值和产品北极星

用户价值：CEO、field owner、support、reviewer 和执行同学需要把上一轮 `field_evidence_material_resolution_owner_response_intake` 的 owner response material 从"已收件/未收件"推进到可执行的 review decision。没有 intake 或材料不完整时，系统必须明确 blocked / needs more evidence；材料安全但仍未证明时，只能进入后续 material review，不能被当成 delivery success、O5 external proof、HIL、真实手机/browser、PR #5 reviewer resolution 或 OKR 百分比提升。

产品北极星：机器人要成为普通手机用户可放心使用的低成本送垃圾机器人，必须让每一份现场、云端、硬件和 reviewer 材料都能沿同一 safe `evidence_ref` 被审查、拒绝、补证或交接。当前 sprint 只补齐 owner response material 的 review-decision 梯级，保持 `software_proof` 和 `not_proven`，不把流程节点包装成真实业务完成。

## Product Problem

10-11 sprint 已经完成 `field_evidence_material_resolution_owner_response_intake`，但 intake 只回答"材料是否进入安全入口"。产品仍缺一个结构化决策层来回答：

- owner response material 是否可以进入后续 material review；
- 是否仍缺真实 terminal result、field pass、cloud/4G/OSS/CDN/DB/queue、phone/browser、hardware/HIL 或 PR #5 reviewer-resolution 材料；
- 是否包含必须拒绝的 unsafe copy、success claim、raw artifact、credential、hardware proof overclaim 或 delivery-success overclaim；
- 如果 blocked，下一步是 owner 补证、CEO 决策升级，还是等待真实环境材料。

已知证据边界：

- Objective 5 仍最低，约 68%，但没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 或 verified terminal result material。
- Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`；comment `3269642220` 只是 software-proof reply。
- Objective 2/3/4 约 99%，但仍缺真实 task record、Nav2/fixed-route runtime、route completion signal、route/elevator field pass、true phone/browser proof、dropoff/cancel completion 和 delivery success。
- 当前主机只有 Docker，没有真实硬件、真实云、真实手机、真实场地、真实串口或 HIL。

## OKR 映射

| Objective | Current status from `OKR.md` 4.1 | This sprint's relationship |
| --- | --- | --- |
| Objective 5: 云中转 + OSS/CDN 数据通路产品化 | About 68%, still the lowest Objective. Missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, and verified terminal delivery/dropoff/cancel result material. | Primary OKR lane because it is lowest. This sprint improves the material-resolution evidence chain by classifying owner response material into review decisions. No percentage lift is allowed without real reviewed external or terminal-result evidence. |
| Objective 1: 硬件协议可信底盘 | About 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending; no real 2D LiDAR / ToF or WAVE ROVER HIL material exists. | Hardware wording must stay conservative. The review decision may mention PR #5 status, but cannot resolve the thread or raise O1 without real vendor/procurement/install/calibration/HIL material and reviewer action. |
| Objective 2/3/4 | About 99%. Still missing real task record, Nav2/fixed-route runtime, route/elevator field pass, true phone/browser proof, dropoff/cancel completion, and delivery success. | The review decision may list these as missing evidence categories, but must not claim field pass, phone acceptance, route completion, or delivery success. |

## KR 拆解或更新

- KR-A Autonomy / PC review decision gate: create `field_evidence_material_resolution_owner_response_review_decision` under `pc-tools/evidence/`, consuming prior owner response intake and emitting one of the supported review decisions.
- KR-B Robot diagnostics safe alias: expose `robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary` as read-only diagnostics metadata that preserves not-proven control flags.
- KR-C Full-Stack mobile/web panel: render a read-only owner-response review decision panel under `mobile/web/`, showing decision, reasons, missing/rejected material categories, and next action without enabling controls.
- KR-D Hardware boundary consultation: verify PR #5, WAVE ROVER, UART, HIL, 2D LiDAR and ToF wording against `docs/vendor/VENDOR_INDEX.md` and current evidence. No hardware config or vendor edits.
- KR-E Product closeout after implementation: create `tech-done.md`, `side2side_check.md`, and `final.md`; update `OKR.md` and progress log only with conservative no-lift closeout unless real reviewed evidence appears.

## 本轮核心抓手

Build a review decision gate, not another intake or followup wrapper. The artifact must turn owner response material into a product-safe decision:

- `accepted_for_material_review_not_proven`: material is safe enough for a later material review, but still not proof.
- `needs_more_evidence_not_proven`: material exists but lacks required categories, same `evidence_ref`, or reviewable content.
- `rejected_unsafe_material_response_not_proven`: material contains unsafe content, success overclaims, raw artifacts, credentials, hardware/control leakage, or incompatible lineage.
- `blocked_missing_owner_response_intake_not_proven`: the previous intake safe artifact/summary is missing, invalid, or not tied to the expected `evidence_ref`.

## 需要做什么

The next execution phase must:

- Implement a PC gate that consumes `field_evidence_material_resolution_owner_response_intake` safe output and emits `field_evidence_material_resolution_owner_response_review_decision`.
- Preserve `software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate`, `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Carry forward safe lineage: prior intake capability, safe `evidence_ref`, PR #5 unresolved state, material categories, and next required evidence.
- Add a Robot diagnostics safe alias and mobile/web read-only panel that show decision status without allowing Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, diagnostics fetch side effects, or robot command routes.
- Update relevant `docs/` files during implementation if interface or mobile/product surfaces change.
- Close sprint with no OKR percentage lift unless real material arrives and is reviewed under the same safe `evidence_ref`.

## Product Requirements

The review-decision package must include:

- Capability: `field_evidence_material_resolution_owner_response_review_decision`.
- Proof boundary: `software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate`.
- Source and status: `source=software_proof`, `not_proven`.
- Control flags: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Supported decisions: `accepted_for_material_review_not_proven`, `needs_more_evidence_not_proven`, `rejected_unsafe_material_response_not_proven`, `blocked_missing_owner_response_intake_not_proven`.
- Required fields: safe `evidence_ref`, previous intake reference, `owner response material` status, `decision_reasons`, `accepted_materials`, `missing_materials`, `rejected_materials`, `unsafe_materials`, `next_required_evidence`, `owner_action`, `ceo_escalation_recommendation`, `review_handoff_recommendation`, and phone-safe summary copy.
- PR/review state: `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`, and comment `3269642220` remains software-proof reply only.

The package must not include:

- Raw credentials, local paths, complete internal logs, checksums, raw JSON artifacts, raw ROS topic dumps, `/cmd_vel`, UART device names, WAVE ROVER parameters, raw vendor material, GitHub tokens, DB/queue URLs, OSS AK/SK, bearer tokens, tracebacks, or full artifacts.
- Any claim of real external cloud proof, public HTTPS/TLS, production DB/queue proof, OSS/CDN live traffic, real phone/browser proof, route/elevator field pass, HIL, verified terminal result, dropoff/cancel completion, delivery success, PR #5 reviewer resolution, hardware acceptance, or OKR percentage lift.

## Priority And Owner Routing

P0:

- Autonomy Engineer owns the PC review-decision gate because it validates material lineage, safety, and decision semantics.
- Robot Platform Engineer owns the diagnostics safe alias because Robot must expose only fail-closed decision metadata to support/operator surfaces.
- Full-Stack Engineer owns the mobile/web read-only review decision panel because support and phone users need to understand why material is accepted for review, needs more evidence, rejected, or blocked.

P1:

- Hardware Engineer owns read-only vendor/PR #5 boundary consultation and must cite `docs/vendor/VENDOR_INDEX.md` when hardware terms are used.
- Product Owner owns closeout docs and the OKR no-lift decision after implementation evidence returns.

## 验收口径

- PC evidence gate emits `field_evidence_material_resolution_owner_response_review_decision` with `software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate`.
- Missing previous intake yields `blocked_missing_owner_response_intake_not_proven`.
- Safe but incomplete owner response material yields `needs_more_evidence_not_proven`.
- Unsafe material yields `rejected_unsafe_material_response_not_proven`.
- Safe material can only yield `accepted_for_material_review_not_proven`; it is not delivery success, not terminal result acceptance, and not OKR movement.
- Robot and mobile surfaces preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Mobile/web stays read-only and does not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, diagnostics fetch side effects, or robot command routes.
- Hardware consultation states PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending unless live reviewer evidence changes.
- `OKR.md` percentages remain unchanged unless real external, terminal, field, phone, hardware, HIL, or reviewer-resolution evidence appears and Product records a reviewed basis.

## Risks, Blockers, And Evidence Chain Gaps

- Risk: review decision becomes another local wrapper. Mitigation: require one of four explicit decisions and tie the result to prior intake plus safe `evidence_ref`.
- Risk: `accepted_for_material_review_not_proven` is mistaken for material acceptance or delivery success. Mitigation: all surfaces must state not-proven and require a later material review.
- Risk: mobile/web copy overpromises. Mitigation: phone-safe copy must use blocked / needs evidence / rejected / accepted-for-review wording and keep primary actions disabled.
- Risk: PR #5 status drifts. Mitigation: Hardware consultation must call out that `PRRT_kwDOSWB9286CJ3tX` is unresolved and comment `3269642220` is only software proof unless live evidence changes.
- Remaining evidence gaps: real public cloud/4G/OSS/CDN/DB/queue, true phone/browser, verified terminal result, route/elevator field pass, real owner response material accepted by review, WAVE ROVER/UART/HIL, installed/procured/calibrated 2D LiDAR / ToF, and reviewer resolution.

## Sprint Documents To Create Or Update

Planning pass creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Implementation and closeout must later create or update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- Relevant `docs/` files touched by implementation owners if contracts or product surfaces change
- `OKR.md` and `docs/process/okr_progress_log.md` only if closeout evidence justifies conservative wording or real-material review; expected result is no percentage lift
