# Field Evidence Material Resolution Review Decision PRD

Run time: 2026-05-22 07:08 Asia/Shanghai

## Product Problem

上一轮 `field_evidence_material_resolution_intake` 已经把 owner resolution packet 变成 sanitized summary，但 intake 的 `accepted` 只表示材料入口通过软件证明，不等于 owner review 已完成，也不等于真实送达、真实 field pass、HIL、真实手机/browser、O5 external proof、PR #5 reviewer resolution 或 verified terminal result。

当前缺少一层产品可解释的 review decision：系统需要把 intake summary 转换为 owner 可复核的安全状态，明确是 `accepted_for_owner_review_not_proven`、`needs_more_evidence_not_proven`、`rejected_unsafe_resolution_not_proven`，还是 `blocked_missing_resolution_intake_not_proven`。否则 support / mobile / Robot diagnostics 会继续展示 intake 结果，但不能说明下一步到底是 owner review、补证据、拒绝 unsafe packet，还是先补 intake。

## User Value And Product North Star

用户价值：support 和现场 owner 能看到一条清晰的材料 resolution review decision：哪些材料可以交给 owner review，哪些仍缺同一 safe `evidence_ref` 的证据，哪些因为 unsafe resolution 被拒绝，哪些因为缺 intake 不能复核。手机端只读显示下一步，不让普通用户误触主操作。

产品北极星：普通手机用户只看到安全、明确、可行动的现场材料复核状态；任何未被真实证据证明的材料都不能开启控制动作、不能写成 delivery success、不能提升真实外部云/HIL/field pass 口径。

## OKR Mapping

| Objective | Mapping | Product Decision |
| --- | --- | --- |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 当前最低，约 68%。本轮消费 O5 external / terminal-result / cloud-material resolution intake 的 sanitized summary，但 Docker-only 环境不能证明 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 或 verified terminal result。 | 针对最低 Objective 的证据决策链路，但不提升完成度，除非后续真实外部材料出现并通过 same safe `evidence_ref` 复核。 |
| Objective 1：硬件协议可信底盘 | 约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved；comment `3269642220` 只是 software-proof reply publication。 | Hardware 只读确认 vendor / PR #5 边界，避免把 review-decision gate 写成 WAVE ROVER/UART/HIL、2D LiDAR/ToF procurement/install/calibration 或 reviewer resolution。 |
| Objective 2/3/4：送达、电梯、导航、手机 | 均约 99%，但仍缺真实 route/elevator field pass、真实手机/browser、Nav2/fixed-route runtime、dropoff/cancel completion 和 delivery result。 | 允许把 route/elevator/phone resolution intake 转为 owner-review decision，但只输出 `software_proof` / `not_proven` read-only summary。 |

## KR Breakdown

### KR-A Autonomy PC Gate

- Build `field_evidence_material_resolution_review_decision` PC gate.
- Input: sanitized `field_evidence_material_resolution_intake` artifact/summary/Robot alias.
- Required checks: supported schema, same safe `evidence_ref`, safe source, no unsafe copy, no raw artifacts, no credentials, no local paths, no ROS topics, no `/cmd_vel`, no serial/UART or WAVE ROVER details, no success/control claims.
- Output: sanitized review-decision artifact + summary with one of `accepted_for_owner_review_not_proven`、`needs_more_evidence_not_proven`、`rejected_unsafe_resolution_not_proven`、`blocked_missing_resolution_intake_not_proven`, plus `next_required_evidence`, `owner_review_handoff`, `proof_boundary=software_proof_docker_field_evidence_material_resolution_review_decision_gate`, `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.

### KR-B Robot Diagnostics Alias

- Expose `robot_diagnostics_field_evidence_material_resolution_review_decision_summary` in Robot diagnostics.
- Consume only sanitized summary fields from PC gate or compatible safe status/diagnostics input.
- Fail closed on missing intake summary, unsupported schema/boundary, evidence-ref mismatch, unsafe copy, raw artifact leakage, success/pass/control copy, or truthy false-state flags.

### KR-C Full-Stack Mobile/Web Read-Only Panel

- Add read-only mobile/web panel consuming `robot_diagnostics_field_evidence_material_resolution_review_decision_summary` first, then compatible safe summary fallback.
- Panel shows decision, safe evidence ref, reason, next required evidence, owner review handoff, proof boundary, `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Start Delivery、Confirm Dropoff、Cancel stay disabled by existing gates; no raw diagnostics fetch, no ACK/cursor/material fetch, no replay/resubmit, no robot command route.

### KR-D Hardware Vendor / PR #5 Boundary Consultation

- Hardware owner reads `docs/vendor/VENDOR_INDEX.md` and referenced local vendor files for source-boundary facts.
- Confirm `PRRT_kwDOSWB9286CJ3tX` remains unresolved material/vendor-source boundary, not HIL or reviewer resolution.
- Produce consultation text for implementation owners and Product closeout; no hardware config, launch, firmware, vendor doc or product code changes.

### KR-E Product Closeout

- After implementation workers return, Product updates sprint `tech-done.md`、`side2side_check.md`、`final.md` and conservative OKR / progress-log records if evidence is valid.
- Product keeps Objective 5 around 68%, Objective 1 around 81%, Objective 2/3/4 around 99% unless real external/hardware/field evidence appears.

## Acceptance Criteria

- All surfaces use capability `field_evidence_material_resolution_review_decision`.
- All proof remains `software_proof` and `not_proven`.
- Exact false-state flags remain visible where relevant: `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Safe decisions are limited to `accepted_for_owner_review_not_proven`、`needs_more_evidence_not_proven`、`rejected_unsafe_resolution_not_proven`、`blocked_missing_resolution_intake_not_proven`.
- `accepted_for_owner_review_not_proven` means owner review may proceed; it is not delivery success, HIL, field pass, real phone/browser proof, real public cloud proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution, dropoff/cancel completion, verified terminal result, or OKR completion lift.
- Unsafe raw content is blocked or rejected, not displayed.
- Robot diagnostics alias and mobile panel are read-only and do not mutate ACK, cursor, command, ROS, Nav2, WAVE ROVER, HIL, route/elevator, terminal result or control state.

## Priority And Owner Routing

| Priority | Owner | Responsibility |
| --- | --- | --- |
| P0 | Autonomy | Canonical PC gate and review-decision artifact/summary contract. |
| P0 | Robot | Safe diagnostics alias and fail-closed summary exposure. |
| P0 | Full-Stack | Phone-safe read-only panel without control enablement. |
| P1 | Hardware | Vendor / PR #5 source-boundary consultation for `PRRT_kwDOSWB9286CJ3tX`. |
| P1 | Product | Evidence review, sprint closeout, conservative OKR / progress-log update. |

## Risks And Evidence Gaps

- Docker-only implementation may only have fixtures, not real owner review materials; fixture proof must remain `software_proof`.
- `accepted_for_owner_review_not_proven` could be misread as real proof; every surface must explicitly keep `not_proven` and the false-state flags.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved until reviewer resolves it; this review-decision gate cannot close the thread.
- Real O5 progress still needs public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser 或 verified terminal delivery/dropoff/cancel result material。
- Real O1 progress still needs 2D LiDAR / ToF source/procurement/install/calibration/HIL-entry evidence and WAVE ROVER/UART/HIL evidence.
- Real O2/O3/O4 progress still needs route/elevator field pass, task record, Nav2/fixed-route runtime, dropoff/cancel completion, delivery result and real phone/browser evidence.

## Sprint Documents To Create Or Update

Current planning task creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Future implementation/closeout must create or update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- Implementation docs under `docs/interfaces/`, `docs/product/`, `pc-tools/README.md`, and diagnostics/mobile docs as assigned in `tech-plan.md`.
