# Field Evidence Material Resolution Owner Response Intake PRD

Run time: 2026-05-22 10:00 Asia/Shanghai

## 用户价值和产品北极星

用户价值：CEO、field owner、支持同学和后续 reviewer 需要一个可校验的入口来接收上一轮 escalation 后的 owner response material。没有真实材料时，系统必须明确显示缺失并保持 fail-closed；未来材料到达时，必须能按同一 safe `evidence_ref` 进入 review，而不是继续靠聊天、截图、口头状态或重复 status wrapper 推进。

产品北极星：机器人只有在真实外部云、真实手机/browser、真实 route/elevator field pass、verified terminal result、真实硬件/HIL 和 reviewer resolution 都能被同一 safe `evidence_ref` 串起来时，才接近可运营闭环。本轮只补齐 owner response material 的 intake 入口，不把入口能力伪装成真实交付结果。

## Product Problem

09-10 sprint 已经把上一轮 handoff 后的缺口表述为 missing/pending/escalated owner action。但 final 也明确说：owner response material 仍 missing/pending/escalated，another local-only wrapper should not be counted as OKR movement。

当前问题不是继续展示“还缺材料”，而是缺少一个严格入口来判断 owner response material 是否真的到达、是否属于同一 safe `evidence_ref`、是否可进入 review、是否仍然缺关键材料、是否包含必须拒绝的 unsafe/success claims。

已知证据边界：

- Objective 5 最低，约 68%，但没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser 或 verified terminal result。
- Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`；comment `3269642220` 只是 software-proof reply。
- Objective 2/3/4 约 99%，但仍缺真实 task record、Nav2/fixed-route runtime、route completion signal、route/elevator field pass、true phone/browser proof、dropoff/cancel completion 和 delivery success。
- 当前主机只有 Docker，没有真实硬件、真实云、真实手机、真实场地、真实串口或 HIL。

## OKR 映射

| Objective | Current status from `OKR.md` 4.1 | This sprint's relationship |
| --- | --- | --- |
| Objective 5: 云中转 + OSS/CDN 数据通路产品化 | About 68%, still the lowest Objective. Missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser, and verified terminal delivery/dropoff/cancel result. | Primary target because it is lowest. This sprint creates an intake entry for owner response material requested by the blocker-resolution chain. No percentage lift is allowed without real accepted material and later review. |
| Objective 1: 硬件协议可信底盘 | About 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending; no real 2D LiDAR / ToF or WAVE ROVER HIL material exists. | Hardware boundary remains pending. The intake may record PR #5 material status, but cannot resolve the thread or raise O1 without real materials and reviewer action. |
| Objective 2/3/4 | About 99%. Still missing real task record, Nav2/fixed-route runtime, route/elevator field pass, true phone/browser proof, dropoff/cancel completion, and delivery success. | The intake may list these as next-required evidence categories, but must not claim field pass, phone acceptance, or delivery success. |

## KR 拆解或更新

- KR-A Autonomy / PC evidence intake: create `field_evidence_material_resolution_owner_response_intake` under `pc-tools/evidence/`, consuming prior followup/escalation status and future owner response material references, then emitting accepted/missing/rejected summaries.
- KR-B Robot diagnostics safe alias: expose `robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary` under `onboard/src/ros2_trashbot_behavior/` as read-only diagnostics metadata.
- KR-C Full-Stack mobile/web panel: render a read-only owner-response intake panel under `mobile/web/` that shows response status, missing/rejected material categories, next review action, and fail-closed control flags.
- KR-D Hardware boundary consultation: verify vendor / PR #5 / 2D LiDAR / ToF / WAVE ROVER / UART / HIL wording against `docs/vendor/VENDOR_INDEX.md` and current evidence. No hardware config changes.
- KR-E Product closeout after implementation: update sprint closeout docs and only update `OKR.md` / progress log conservatively. Expected outcome is no OKR percentage lift unless real materials are received and explicitly reviewed.

## 本轮核心抓手

Build an owner-response intake gate, not another followup/escalation status. The artifact should answer:

- Which previous escalation or handoff is this owner response answering?
- Is there actual owner response material, or is it still missing?
- Does the response use the same safe `evidence_ref`?
- Which material categories are accepted for later review?
- Which categories are missing, rejected, unsafe, stale, or unrelated?
- Does any copy overclaim delivery success, external cloud, phone/browser, HIL, field pass, PR #5 resolution, or hardware readiness?
- What exact next review or owner/CEO action is required?

## Product Requirements

The owner-response intake package must include:

- Capability: `field_evidence_material_resolution_owner_response_intake`.
- Proof boundary: `software_proof_docker_field_evidence_material_resolution_owner_response_intake_gate`.
- Source and status: `source=software_proof`, `not_proven`.
- Control flags: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Lineage: previous `field_evidence_material_resolution_followup_escalation_status`, previous `field_evidence_material_resolution_review_handoff`, and previous review-decision context.
- Material status fields: `owner_response_material_status`, `accepted_materials`, `missing_materials`, `rejected_materials`, `unsafe_materials`, `review_readiness`, `blocked_reason`, `next_required_evidence`, `owner_action`, `ceo_escalation_recommendation`, and safe `evidence_ref`.
- PR/review state: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`, and comment `3269642220` as software-proof reply only.
- Future-review routing: accepted owner response material can become input to a later review-decision sprint, but this sprint itself must not claim review acceptance or OKR lift.

The package must not include:

- Raw credentials, local paths, complete internal logs, checksums, raw JSON artifacts, raw ROS topic dumps, `/cmd_vel`, UART device names, WAVE ROVER parameters, raw vendor material, GitHub tokens, DB/queue URLs, OSS AK/SK, bearer tokens, tracebacks, or full artifacts.
- Any claim of real external cloud proof, public HTTPS/TLS, production DB/queue proof, OSS/CDN live traffic, real phone/browser proof, route/elevator field pass, HIL, verified terminal result, dropoff/cancel completion, delivery success, PR #5 reviewer resolution, hardware acceptance, or OKR percentage lift.

## Priority And Owner Routing

P0:

- Autonomy Engineer owns the PC evidence intake gate because it validates the material path and same-`evidence_ref` contract.
- Robot Platform Engineer owns the diagnostics safe alias because Robot must expose only fail-closed intake metadata to operator/support surfaces.
- Full-Stack Engineer owns the mobile/web read-only owner-response panel because support and phone users need to see blocked/not-proven status without enabling controls.

P1:

- Hardware Engineer owns read-only vendor/PR #5 boundary consultation. No hardware configuration, launch parameter, or vendor document edits are expected.
- Product Owner owns closeout docs, OKR/progress log review, and the final decision that no percentage should rise without real reviewed evidence.

## 验收口径

- PC evidence gate emits `field_evidence_material_resolution_owner_response_intake` with `software_proof_docker_field_evidence_material_resolution_owner_response_intake_gate`.
- Missing owner response material yields blocked / `not_proven`, not accepted.
- Any accepted material remains `accepted_for_review_not_proven` or equivalent; it is not delivery success and not OKR movement.
- Robot and mobile surfaces preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Mobile/web stays read-only and does not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, diagnostics fetch side effects, or robot command routes.
- Hardware consultation states PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending unless live reviewer evidence changes.
- `OKR.md` percentages remain unchanged unless real external, terminal, field, phone, hardware, HIL, or reviewer-resolution evidence appears and Product records a reviewed basis.

## Risks, Blockers, And Evidence Chain Gaps

- Risk: intake becomes another local wrapper. Mitigation: require accepted/missing/rejected material categories and same safe `evidence_ref`; no material means blocked/not-proven.
- Risk: owner response presence is mistaken for review acceptance. Mitigation: accepted material can only be `accepted_for_review_not_proven`; a later review-decision step must decide product impact.
- Risk: mobile/web copy overpromises. Mitigation: phone-safe copy must use not-proven wording and keep primary actions disabled.
- Risk: PR #5 status drifts. Mitigation: Hardware consultation must call out that `PRRT_kwDOSWB9286CJ3tX` is unresolved and comment `3269642220` is only a software-proof reply unless live evidence changes.
- Remaining evidence gaps: real public cloud/4G/OSS/CDN/DB/queue, true phone/browser, verified terminal result, route/elevator field pass, real owner response material, WAVE ROVER/UART/HIL, installed/procured/calibrated 2D LiDAR / ToF, and reviewer resolution.

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
