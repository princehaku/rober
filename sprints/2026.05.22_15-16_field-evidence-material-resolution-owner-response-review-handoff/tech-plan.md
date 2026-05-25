# Field Evidence Material Resolution Owner Response Review Handoff Tech Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or the repo `AGENTS.md` Codex `spawn_agent(agent_type=worker)` SOP. Main node must dispatch implementation, tests, fixes, and validation to workers; main node only integrates evidence and sprint closeout.

Run time: 2026-05-22 15:04 Asia/Shanghai

**Goal:** Build `field_evidence_material_resolution_owner_response_review_handoff` as a software-proof Docker/local handoff gate that turns owner-response review decisions into support / field owner / reviewer next-step packages.

**Architecture:** The PC gate creates the canonical artifact and tests the classification-to-handoff rules. Robot diagnostics exposes only a sanitized safe alias. `mobile/web` renders the alias as a read-only panel. Hardware consultation remains read-only and only confirms PR/vendor evidence boundaries.

**Tech Stack:** Python standard library CLI and `unittest`, ROS2 operator gateway diagnostics Python module, dependency-free `mobile/web` JavaScript/CSS, JSON fixtures, markdown interface/product docs.

---

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective: Objective 5, about 68%.
- 本 sprint 是否针对该 Objective: 是，针对 Objective 5 的 field-evidence material-resolution chain 的下一 rung。
- 具体理由: Objective 5 仍缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal delivery/dropoff/cancel result，当前 Docker-only host 不能产出这些真实外部材料；本 sprint 只把 14-15 sprint 的 owner-response review decision 推进到 handoff，保持 no OKR percentage lift。
- 次低 Objective: Objective 1 about 81%，但 13-14 sprint 已完成 `wave_rover_hil_packet_collection_drill`，仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator report 或 PR #5 resolution；`PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` and comment `3269642220` is software-proof only。
- final.md 收口时需复核: 是否仍没有真实 O5 external proof、O1 HIL/material proof、PR #5 resolution、true phone/browser evidence 或 delivery result；如没有，必须继续 no-lift closeout。

## Non-Goals And Proof Boundary

This sprint is explicitly:

- not O5 external proof.
- not O1 HIL.
- not PR #5 resolution.
- not true phone/browser proof.
- not public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or production cutover proof.
- not route/elevator field pass.
- not verified terminal delivery/dropoff/cancel result.
- not delivery success.

Every implementation surface must preserve:

- `software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Parallel Owner Tasks

### Task A: Autonomy / PC Gate

**Owner:** `autonomy-engineer`

**Responsibility:** Create the canonical handoff artifact CLI and tests.

**Files:**

- Create: `pc-tools/evidence/field_evidence_material_resolution_owner_response_review_handoff.py`
- Create: `pc-tools/evidence/test_field_evidence_material_resolution_owner_response_review_handoff.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/interfaces/evidence_contracts.md`

**Interface Impact:**

- New artifact schema: `trashbot.field_evidence_material_resolution_owner_response_review_handoff.v1`
- New summary schema: `trashbot.field_evidence_material_resolution_owner_response_review_handoff_summary.v1`
- Capability string: `field_evidence_material_resolution_owner_response_review_handoff`
- Evidence boundary: `software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate`
- Output handoff statuses must include:
  - `ready_for_material_review_handoff_not_proven`
  - `needs_owner_more_evidence_handoff_not_proven`
  - `rejected_unsafe_owner_response_handoff_not_proven`
  - `blocked_missing_owner_response_intake_handoff_not_proven`

**Implementation Requirements:**

- Consume previous review-decision JSON from a file path argument.
- Accept compatible decision fields from `field_evidence_material_resolution_owner_response_review_decision`.
- Generate safe `evidence_ref`, `handoff_status`, `source_review_decision`, `field_owner_handoff`, `support_handoff`, `reviewer_handoff`, `missing_required_materials`, `rejected_unsafe_materials`, `next_required_evidence`, and proof flags.
- Fail closed when the input is missing, malformed, missing owner-response intake, missing safe evidence ref, or contains unsafe success claims.
- Do not expose raw ROS topics, `/cmd_vel`, serial/UART paths, credentials, local paths, complete artifacts, checksums, stack traces, raw material payloads, or control commands.

**Acceptance Commands:**

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_owner_response_review_handoff.py
python3 -m unittest pc-tools.evidence.test_field_evidence_material_resolution_owner_response_review_handoff
python3 pc-tools/evidence/field_evidence_material_resolution_owner_response_review_handoff.py --help
rg -n "field_evidence_material_resolution_owner_response_review_handoff|software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate|delivery_success=false|not_proven|safe_to_control=false" pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_material_resolution_owner_response_review_handoff.py pc-tools/evidence/test_field_evidence_material_resolution_owner_response_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B: Robot Diagnostics Safe Alias

**Owner:** `robot-software-engineer`

**Responsibility:** Expose the handoff through Robot diagnostics as a sanitized safe alias.

**Files:**

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/operator_gateway_diagnostics.md`

**Interface Impact:**

- Add safe alias: `robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary`
- Alias must be read-only, metadata-only, and fail closed when the upstream handoff summary is absent or unsafe.
- No control endpoint, ACK mutation, cursor mutation, replay, resubmit, serial open, WAVE ROVER command, Nav2 route execution, or action result mutation.

**Implementation Requirements:**

- Preserve existing diagnostics behavior and safe-summary redaction patterns.
- Include only phone-safe fields from the PC artifact summary.
- Keep `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- Missing input should produce `blocked_missing_owner_response_review_handoff_not_proven` or equivalent blocked/not-proven summary.

**Acceptance Commands:**

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary|field_evidence_material_resolution_owner_response_review_handoff|software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate|delivery_success=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
```

### Task C: Full-Stack Mobile Read-Only Panel

**Owner:** `full-stack-software-engineer`

**Responsibility:** Render the handoff summary in `mobile/web` without enabling primary actions.

**Files:**

- Modify: `mobile/web/app.js`
- Modify: `mobile/web/styles.css`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Create: `mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary.json`
- Modify: `docs/product/mobile_user_flow.md`

**Interface Impact:**

- Add a read-only panel titled in Chinese, for example: `现场材料 owner response 复核交接`.
- Consume `robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary` first, then compatible nested phone-safe summaries.
- This panel must not affect existing Start Delivery, Confirm Dropoff, or Cancel authorization.

**Implementation Requirements:**

- Display `handoff_status`, source review decision, safe `evidence_ref`, `field_owner_handoff`, `support_handoff`, `reviewer_handoff`, missing required materials, rejected unsafe materials, next required evidence, proof boundary, and flags.
- Missing summary fails closed without raw artifact rendering.
- Chinese-first copy must make clear: this is not true phone/browser proof, not delivery success, and not a robot control grant.
- Do not expose raw JSON, ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER parameters, credentials, DB/queue URLs, local paths, complete artifacts, checksums, ACK/cursor payloads, HIL/pass wording, route/elevator field-pass claims, delivery success claims, dropoff completion claims, or cancel completion claims.

**Acceptance Commands:**

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary.json >/dev/null
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "field_evidence_material_resolution_owner_response_review_handoff|software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate|not true phone/browser|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary.json docs/product/mobile_user_flow.md
```

### Task D: Hardware Read-Only PR / Vendor Boundary Consultation

**Owner:** `rober-hardware-engineer`

**Responsibility:** Confirm hardware and PR #5 boundaries without writing product code, tests, launch params, or hardware config.

**Files:**

- Read-only: `docs/vendor/VENDOR_INDEX.md`
- Read-only: vendor docs referenced by `docs/vendor/VENDOR_INDEX.md` only when needed for WAVE ROVER / UART / 2D LiDAR / ToF statements.
- Read-only: `docs/product/production_hardware_boundary.md`
- Read-only: live or recorded PR #5 thread evidence for `PRRT_kwDOSWB9286CJ3tX`

**Interface Impact:**

- No code interface changes.
- Consultation output must be consumed by Product closeout and sprint docs only.

**Consultation Requirements:**

- Confirm `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` unless live GitHub evidence proves otherwise.
- Confirm comment `3269642220` is software-proof only and not reviewer resolution.
- Confirm no real 2D LiDAR/ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry materials are present in this sprint.
- Confirm no real WAVE ROVER/UART/HIL evidence is produced by this sprint.
- Mention `docs/vendor/VENDOR_INDEX.md` as the hardware source boundary.

**Acceptance Commands:**

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "WAVE ROVER|UART|2D LiDAR|ToF|VENDOR_INDEX|PRRT_kwDOSWB9286CJ3tX|3269642220|software_proof" docs/vendor docs/product/production_hardware_boundary.md OKR.md sprints/2026.05.22_15-16_field-evidence-material-resolution-owner-response-review-handoff
git diff --check -- sprints/2026.05.22_15-16_field-evidence-material-resolution-owner-response-review-handoff
```

## Integration Acceptance

Product Manager / OKR Owner must only accept the sprint when all worker outputs report:

- actual changed files.
- validation command results.
- failure localization, if any.
- remaining risks.
- proof boundary remains `software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate`.
- no OKR percentage lift unless real evidence appears.

Required final sprint validation after implementation and closeout:

```bash
test -f sprints/2026.05.22_15-16_field-evidence-material-resolution-owner-response-review-handoff/tech-done.md && test -f sprints/2026.05.22_15-16_field-evidence-material-resolution-owner-response-review-handoff/side2side_check.md && test -f sprints/2026.05.22_15-16_field-evidence-material-resolution-owner-response-review-handoff/final.md
rg -n "field_evidence_material_resolution_owner_response_review_handoff|software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not true phone/browser|delivery_success=false|no OKR percentage lift" sprints/2026.05.22_15-16_field-evidence-material-resolution-owner-response-review-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_15-16_field-evidence-material-resolution-owner-response-review-handoff OKR.md docs/process/okr_progress_log.md
```

## Product Closeout Rules

- `tech-done.md` must record actual worker edits, exact validation results, deviations, and remaining risk.
- `side2side_check.md` must compare PRD acceptance criteria against actual worker evidence.
- `final.md` must explicitly state this sprint is not O5 external proof, not O1 HIL, not PR #5 resolution, not true phone/browser, and not delivery success.
- `OKR.md` should not receive a percentage lift for this planning target unless real external/hardware/field evidence appears during execution.
- If implementation discovers the handoff is redundant with an existing artifact, stop and ask Product for rerank instead of creating another duplicate wrapper.
