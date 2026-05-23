# Field Evidence Rerun Reviewer ACK Owner Response Intake Bridge Tech Plan

Run time: 2026-05-24 03:04 Asia/Shanghai

## Sprint Type

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/O3/O4 约 99%。
2. 本 sprint 不针对 Objective 5 completion。具体理由：`OKR.md` 第 6 节明确只有拿到真实外部材料时才继续推进 O5 completion，包括公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal delivery/dropoff/cancel result；当前本机没有这些材料，不能重复本地 O5 metadata depth。
3. 本 sprint 也不针对 Objective 1 completion。具体理由：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，需要真实 2D LiDAR / ToF SKU/source/receipt、安装、接线、标定、HIL-entry、WAVE ROVER powered bench/UART/HIL logs；当前本机没有真实硬件，只有 Docker，不能 claim HIL 或 PR resolution。
4. 因 O5 外部材料和 O1 真实硬件材料都不可用，本 sprint 转入 `OKR.md` 第 6 节指定的 O2/O3/O4 现场 owner material re-entry bridge：把 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` safe source 接回 owner response intake 主链，要求现场 owner 回填真实 route/elevator/dropoff/cancel/phone materials。
5. 本 sprint 输出只能是 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate`，必须保留 `not_proven`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`，不提升 OKR 百分比。

## Architecture

Capability: `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`

Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate`

Data flow:

1. Autonomy / PC gate extends existing owner response intake gate to accept safe reviewer ACK follow-up escalation status as an alternate source.
2. PC gate validates same safe `evidence_ref`, false-state flags, source boundary and required next-materials list.
3. PC gate emits owner response intake summary plus `source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`.
4. Robot diagnostics exposes only sanitized safe alias fields, including bridge source and next required field-owner materials.
5. `mobile/web` owner response intake panel shows the bridge summary read-only; Start Delivery、Confirm Dropoff、Cancel stay disabled.
6. Product closeout records this as Docker/local fail-closed bridge only, no OKR percentage lift.

## Parallel Owner Split

### Task A: Autonomy / PC Gate Bridge

Owner: Autonomy Algorithm Engineer

Allowed files:

- `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py`
- `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.md`

Implementation requirements:

- Extend the existing owner response intake gate; do not create a separate owner-response mainline.
- Accept sanitized `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` source.
- Emit `source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`.
- Emit evidence boundary `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate`.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Require same safe `evidence_ref` across source and owner response intake; mismatches fail closed.
- Require next required field-owner materials: real task record, dropoff/cancel completion, Nav2/fixed-route runtime log, route completion signal, elevator door status, floor confirmation, human assistance note, delivery result, route/elevator field pass and true phone/browser evidence.
- Fail closed on success wording, control flags, missing `source_bridge`, unsafe true state, raw artifact paths, credentials, ROS topics, `/cmd_vel`, serial/UART details, ACK/cursor mutation, GitHub mutation, upload/review actions or robot command hints.

Acceptance commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_rerun_bridge_autonomy python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_rerun_bridge_autonomy python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate|source_bridge|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|task record|dropoff|cancel|Nav2|route completion|elevator|phone" pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/README.md docs/interfaces/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.md
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/README.md docs/interfaces/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.md
```

### Task B: Robot Diagnostics Safe Alias Bridge

Owner: Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`

Implementation requirements:

- Extend the existing `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary` alias to expose bridge-safe fields.
- Include `source_bridge`, source follow-up status, same safe `evidence_ref`, owner route, reviewer/support route, next required field-owner materials and false-state flags.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Reject raw artifacts, credentials, local paths, raw robot responses, ROS topics, `/cmd_vel`, serial/UART details, ACK/cursor payloads, diagnostics fetch mutation hints, GitHub mutation hints and robot command hints.

Acceptance commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_rerun_bridge_robot python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_rerun_bridge_robot python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate|source_bridge|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|task record|dropoff|cancel|Nav2|route completion|elevator|phone" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
```

### Task C: Full-Stack Mobile Read-only Bridge Panel

Owner: User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Extend the existing owner response intake panel/fixture rather than adding a control surface.
- Display `source_bridge`, source follow-up status, same safe `evidence_ref`, owner route, reviewer/support route, next required field-owner materials and safe copy.
- Preserve disabled Start Delivery, Confirm Dropoff and Cancel behavior.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Avoid success wording, control authorization, material upload/procurement/review actions, raw JSON, raw artifact paths, credentials, ROS topics, `/cmd_vel`, serial/UART details, ACKs, cursors, diagnostics fetch mutation hints and robot commands.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json >/tmp/rober_rerun_bridge_mobile_fixture.json
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_rerun_bridge_mobile python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate|source_bridge|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|task record|dropoff|cancel|Nav2|route completion|elevator|phone" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product / OKR Closeout

Owner: Product Manager / OKR Owner

Allowed files after Tasks A-C return evidence:

- `sprints/2026.05.24_03-04_field-evidence-rerun-reviewer-ack-owner-response-intake-bridge/tech-done.md`
- `sprints/2026.05.24_03-04_field-evidence-rerun-reviewer-ack-owner-response-intake-bridge/side2side_check.md`
- `sprints/2026.05.24_03-04_field-evidence-rerun-reviewer-ack-owner-response-intake-bridge/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout requirements:

- Record actual engineer file changes, validation results, failures, fixes and remaining risks.
- Confirm no OKR percentage lift: Objective 5 remains about 68%, Objective 1 remains about 81%, Objective 2/O3/O4 remain unchanged unless real external/material evidence arrives.
- Confirm PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless GitHub reviewer state actually changes.
- Confirm bridge boundary: `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Confirm this is not O5 external proof, not O1 HIL, not true phone/browser proof, not route/elevator field pass, not dropoff/cancel completion and not delivery success.

Acceptance commands:

```bash
test -f sprints/2026.05.24_03-04_field-evidence-rerun-reviewer-ack-owner-response-intake-bridge/tech-done.md
test -f sprints/2026.05.24_03-04_field-evidence-rerun-reviewer-ack-owner-response-intake-bridge/side2side_check.md
test -f sprints/2026.05.24_03-04_field-evidence-rerun-reviewer-ack-owner-response-intake-bridge/final.md
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift|source_bridge" OKR.md docs/process/okr_progress_log.md sprints/2026.05.24_03-04_field-evidence-rerun-reviewer-ack-owner-response-intake-bridge
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.24_03-04_field-evidence-rerun-reviewer-ack-owner-response-intake-bridge
```

## Integration Acceptance

After Tasks A-C finish, the integration owner must run:

```bash
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_rerun_bridge_integration python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_rerun_bridge_integration python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json >/tmp/rober_rerun_bridge_mobile_fixture_integration.json
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate|robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary|source_bridge|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|task record|dropoff|cancel|Nav2|route completion|elevator|phone|no OKR percentage lift" pc-tools/evidence onboard/src/ros2_trashbot_behavior mobile/web docs/interfaces docs/product
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py pc-tools/README.md docs/interfaces/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Proof Boundary

This sprint can prove only local schema, fail-closed diagnostics and read-only UI bridge behavior. It is not real public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not true phone/browser proof, not HIL, not WAVE ROVER/UART proof, not 2D LiDAR/ToF installed proof, not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, not route/elevator field pass, not Nav2/fixed-route runtime pass, not dropoff/cancel completion, not delivery result and not delivery success.
