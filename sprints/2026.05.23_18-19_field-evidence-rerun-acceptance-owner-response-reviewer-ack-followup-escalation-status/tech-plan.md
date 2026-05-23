# Field Evidence Rerun Acceptance Owner Response Reviewer ACK Followup Escalation Status Tech Plan

Run time: 2026-05-23 18:00 Asia/Shanghai

## Sprint Type

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接完成 Objective 5 external proof。
3. 原因：Objective 5 需要真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof 或 verified terminal result。本机是 Docker-only host，不能生成这些真实材料。
4. Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，且最近两轮已经连续消费 PR #5 mandatory sensor material owner-response intake 和 review-decision；本轮不得再做第三个 PR #5 同根因 wrapper。
5. 本 sprint 针对 Objective 2/3/4 的现场证据链作软件证明推进：从最新已完成的 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff` 进入显式 follow-up escalation status，要求真实材料补齐，不提升 OKR 百分比。

## Capability And Boundary

Capability:

`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`

Evidence boundary:

`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate`

Required preserved flags:

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`
- no OKR percentage lift

## Parallel Sub Agent Plan

Start 3 implementation sub agents in parallel after this plan is accepted by the main runtime. They are not alone in the codebase; they must not revert edits made by others and must keep changes inside their file ranges.

### Autonomy Agent

Role: Autonomy Algorithm Engineer.

Goal: add the PC gate that converts prior reviewer ACK review-handoff safe metadata into follow-up escalation status metadata.

Allowed file range:

- `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py`
- `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

Implementation requirements:

- Accept only safe prior review-handoff metadata.
- Emit fixed safe statuses including `pending_reviewer_ack_followup_not_proven`, `overdue_reviewer_ack_followup_not_proven`, `escalated_missing_real_material_not_proven`, `blocked_missing_reviewer_ack_review_handoff_not_proven`, and `ready_for_real_material_reviewer_followup_not_proven`.
- Preserve `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Include missing real-material fields for O5 external proof, route/elevator field pass, verified terminal result, dropoff/cancel completion, delivery result, true phone/browser proof, and PR #5 hardware material pending risk.
- Do not include raw artifacts, raw JSON dumps, credentials, local absolute paths, serial/UART details, or success/control claims.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py
python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py --help
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate|pending_reviewer_ack_followup_not_proven|overdue_reviewer_ack_followup_not_proven|escalated_missing_real_material_not_proven|blocked_missing_reviewer_ack_review_handoff_not_proven|ready_for_real_material_reviewer_followup_not_proven|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Robot Agent

Role: Robot Platform Engineer.

Goal: expose the follow-up escalation status through Robot diagnostics as a safe alias.

Allowed file range:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary`.
- Prefer the safe alias over raw compatible summaries.
- Whitelist only status, safe `evidence_ref`, missing evidence summary, owner next step, reviewer next step, support next step, boundary, and fail-closed flags.
- Strip raw artifacts, raw JSON, raw ROS topics, `/cmd_vel`, serial/UART paths, credentials, local filesystem paths, checksums, complete artifacts, and control/success copy.
- Preserve `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Full-Stack Agent

Role: User Touchpoint Full-Stack Engineer.

Goal: add a read-only fail-closed `mobile/web` panel for the Robot safe alias.

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Render the panel from `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary`.
- Fall back only to safe compatible summary fields if the Robot alias is absent.
- Show status, missing evidence, owner next step, reviewer next step, support next step, safe `evidence_ref`, boundary, and fail-closed flags.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not expose raw JSON, raw artifacts, ROS topics, `/cmd_vel`, credentials, serial/UART paths, local filesystem paths, checksums, complete artifacts, GitHub action, material upload, procurement action, review action, handoff action, diagnostics fetch, ACK, cursor, or robot command.
- Explicitly state this is not true phone/browser proof, not delivery success, not route/elevator field pass, not verified terminal result, not O5 external proof, not HIL, and not PR #5 resolution.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.json >/tmp/reviewer_ack_followup_escalation_status_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Product Closeout Plan

Product closeout is not part of the three parallel implementation agents. After all implementation agents return with passing evidence, Product Manager / OKR Owner updates:

- `sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status/tech-done.md`
- `sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout requirements:

- No OKR percentage lift unless real materials appear.
- State Objective 5 remains lowest and not proven.
- State PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live review evidence changes.
- State the new capability is local Docker `software_proof` only.
- Preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.

## Integration Acceptance

After the three implementation agents complete, run fenced integration checks:

```bash
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence onboard/src/ros2_trashbot_behavior mobile/web docs/interfaces docs/product
git diff --check -- pc-tools/evidence onboard/src/ros2_trashbot_behavior mobile/web docs/interfaces docs/product
```

## Planning Phase Validation

The current planning-only phase is accepted when these commands pass:

```bash
test -f sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status/pre_start.md
test -f sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status/prd.md
test -f sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate|Autonomy|Robot|Full-Stack" sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status
git diff --check -- sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status
```

## Remaining Risks

- This plan cannot prove real O5 external readiness.
- This plan cannot prove PR #5 hardware readiness or close `PRRT_kwDOSWB9286CJ3tX`.
- This plan cannot prove true phone/browser behavior, route/elevator field pass, verified terminal result, dropoff/cancel completion, delivery result, or delivery success.
- If the implementation agents find incompatible existing schemas, they must preserve fail-closed behavior and return the mismatch for Product/Robot integration review rather than widening raw data exposure.
