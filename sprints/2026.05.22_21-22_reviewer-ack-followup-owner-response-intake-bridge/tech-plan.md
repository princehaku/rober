# Reviewer ACK Followup Owner Response Intake Bridge Tech Plan

Run time: 2026-05-22 21:22 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge`

Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge_gate`

## Goal

Connect the previous reviewer ACK follow-up escalation status into the existing owner response intake mainline so `accepted_for_owner_response_intake_not_proven` becomes an actual safe source path, not just display copy.

This remains Docker/local `software_proof`. It does not enable robot control, does not prove Objective 5 external cloud readiness, and does not change OKR percentages.

## Architecture

Task A extends the PC owner response intake gate to accept reviewer ACK follow-up escalation safe summaries, Robot aliases, and compatible wrappers. Task B verifies that Robot diagnostics can consume and emit the bridged owner response intake summary safely. Task C proves the phone-facing owner response intake panel can render the bridge fixture while actions remain disabled. Task D closes out only after A/B/C return evidence.

The bridge must preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5 的最低优先级缺口做证据链治理：把 reviewer ACK follow-up escalation status 接入 owner response intake 主链，为后续真实外部材料、owner response、verified terminal result 或 true phone/browser evidence 到位后的复核留入口。
3. 本 sprint 不直接推进真实 Objective 5 external proof。原因是本机只有 Docker，不能产生真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal delivery/dropoff/cancel result。
4. 下一低项 Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`；comment `3269642220` 仍是 `software_proof` / `hardware_material_pending`。本 sprint 不得写成 O1 HIL、2D LiDAR/ToF material ready、PR #5 resolution 或 OKR percentage lift。

## Parallel Owner Tasks

### Task A: Autonomy - PC Owner Response Intake Bridge

Owner: Autonomy Algorithm Engineer

Allowed files:

- `pc-tools/evidence/field_evidence_material_resolution_owner_response_intake.py`
- `pc-tools/evidence/test_field_evidence_material_resolution_owner_response_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

Implementation requirements:

- Extend the PC owner response intake gate so it safely accepts:
  - `trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`
  - `trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`
  - `field_evidence_material_resolution_reviewer_ack_followup_escalation_status` artifact/summary wrappers used by Robot/mobile/status payloads.
- Preserve compatibility with the older `field_evidence_material_resolution_followup_escalation_status` source path.
- Require the bridge source to be `source=software_proof`, `not_proven`, and one of the safe reviewer ACK follow-up states, especially `accepted_for_owner_response_intake_not_proven`.
- Preserve same safe `evidence_ref`; mismatches, missing source, unsupported schema, unsupported boundary, or unsafe copy must fail closed.
- Keep output semantics exactly owner response intake: accepted/missing/rejected/unsafe material classifications only, not review approval, PR closure, hardware proof, phone proof, cloud proof, route/elevator proof, verified terminal result, or delivery success.
- Reject raw artifacts, raw material contents, local paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, raw checksums, success/control claims, true phone/browser claims, Objective 5 external-proof claims, HIL claims, route/elevator field pass claims, `PRRT_kwDOSWB9286CJ3tX` resolution claims, or any `delivery_success=true`.
- Add focused tests for accepted reviewer ACK bridge input, Robot alias input, wrapper input, old source compatibility, mismatched `evidence_ref`, unsafe success/control claims, and missing owner response material.
- Update docs with bridge schema/source compatibility and non-claim boundary.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_owner_response_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools.evidence.test_field_evidence_material_resolution_owner_response_intake
python3 pc-tools/evidence/field_evidence_material_resolution_owner_response_intake.py --help
rg -n "field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge|field_evidence_material_resolution_reviewer_ack_followup_escalation_status|field_evidence_material_resolution_owner_response_intake|accepted_for_owner_response_intake_not_proven|software_proof|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not_proven|PRRT_kwDOSWB9286CJ3tX" pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_material_resolution_owner_response_intake.py pc-tools/evidence/test_field_evidence_material_resolution_owner_response_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B: Robot - Diagnostics Safe Summary Consumption

Owner: Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`

Implementation requirements:

- Confirm and adjust `robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary` so it consumes the owner response intake summary produced from the reviewer ACK bridge without exposing unsafe fields.
- Preserve only sanitized fields: capability, schema, evidence boundary, source, safe `evidence_ref`, owner response intake status, source reviewer ACK follow-up status, missing/accepted/rejected/unsafe material summaries, next required evidence, phone-safe copy, and fail-closed flags.
- If the PC summary includes a source bridge marker, expose only a safe marker such as `source_bridge=field_evidence_material_resolution_reviewer_ack_followup_escalation_status`; do not expose raw source artifacts.
- Keep `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- Add focused diagnostics tests for bridged source consumption, unsupported source failure, unsafe raw/path/credential/control filtering, and preserved disabled flags.
- Update diagnostics docs with the bridge boundary and non-claim wording.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary|field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge|field_evidence_material_resolution_reviewer_ack_followup_escalation_status|accepted_for_owner_response_intake_not_proven|software_proof|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not_proven|PRRT_kwDOSWB9286CJ3tX" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
```

### Task C: Full-Stack - Mobile Owner Response Intake Bridge Fixture

Owner: User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary.json`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Use the existing owner response intake panel; do not create a new action surface.
- Add a reviewer ACK follow-up bridge fixture/coverage proving the panel can render an owner response intake summary whose source path came from reviewer ACK follow-up escalation status.
- The fixture must include safe source bridge copy, `accepted_for_owner_response_intake_not_proven`, `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not add ACK/cursor fetch, diagnostics fetch, replay, resubmit, material upload/download, owner-response route buttons, review/handoff routes, or robot command endpoints.
- Do not expose raw JSON, raw artifacts, local paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, raw checksums, true phone/browser proof, Objective 5 external proof, HIL, route/elevator field pass, dropoff/cancel completion, verified terminal result, PR #5 resolution, or delivery success.
- Update `docs/product/mobile_user_flow.md` with the owner response intake bridge behavior and explicitly state `not true phone/browser`.

Acceptance commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary.json
rg -n "field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge|field_evidence_material_resolution_reviewer_ack_followup_escalation_status|field_evidence_material_resolution_owner_response_intake|accepted_for_owner_response_intake_not_proven|software_proof|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not true phone/browser|not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product - Closeout After A/B/C

Owner: Product Manager / OKR Owner

Allowed files after A/B/C finish:

- `sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/tech-done.md`
- `sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/side2side_check.md`
- `sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Implementation requirements:

- Wait for A/B/C changed-file lists and validation logs before writing closeout.
- Record actual changes, validation results, failures/deviations, and remaining risks.
- Keep Objective 5 about 68%, Objective 1 about 81%, Objective 2/3/4 about 99% unless real external, hardware, true phone/browser, field, or verified terminal result materials arrive.
- Preserve `PRRT_kwDOSWB9286CJ3tX` as unresolved / `hardware_material_pending` unless live GitHub evidence changes.
- State that the bridge is `software_proof` only, not true phone/browser proof, not delivery success, not O5 external proof, and not PR #5 resolution.

Acceptance commands:

```bash
test -f sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/tech-done.md && test -f sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/side2side_check.md && test -f sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/final.md
rg -n "field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge|Objective 5|no OKR percentage lift|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|not true phone/browser|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven" sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge OKR.md docs/process/okr_progress_log.md
```

## Subagent Dispatch Notes

A/B/C must be started in parallel with `spawn_agent(agent_type=worker)` and the role prompts from `.codex/agents/autonomy-engineer.toml`, `.codex/agents/robot-software-engineer.toml`, and `.codex/agents/full-stack-software-engineer.toml`. Each worker prompt must include role system prompt, task, allowed files, acceptance commands, and output requirements.

Task D must not run until A/B/C implementation evidence is returned.

## Integration Rules

- Do not run broad suites; use the fenced commands above.
- If any validation fails, the owning engineer must inspect the failure, fix root cause within scope, and rerun the focused command.
- Do not touch hardware configuration or vendor assumptions in this sprint.
- Do not revert unrelated worktree changes.
- Code technical comments added by workers must be meaningful Chinese comments and maintain the project comment standard.
- The final implementation may be committed and pushed only after scoped validation passes and unrelated local changes are excluded.

## Non-Claims

This sprint is not Objective 5 external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not true phone/browser proof, not Objective 1 HIL, not WAVE ROVER/UART proof, not route/elevator field pass, not verified terminal result, not dropoff/cancel completion, not cancel completion, not PR #5 resolution, not `PRRT_kwDOSWB9286CJ3tX` resolved, not OKR percentage lift, and not delivery success.

## Planning Validation

Run before implementation dispatch:

```bash
test -f sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/pre_start.md && test -f sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/prd.md && test -f sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge/tech-plan.md
rg -n "sprint_type: epic|field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof|not true phone/browser|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge
git diff --check -- sprints/2026.05.22_21-22_reviewer-ack-followup-owner-response-intake-bridge
```

