# Field Evidence Material Resolution Reviewer ACK Intake Tech Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or the repo `AGENTS.md` Codex `spawn_agent(agent_type=worker)` SOP. Main node must dispatch implementation, tests, fixes, and validation to workers; main node only integrates evidence and sprint closeout.

Run time: 2026-05-22 16:00 Asia/Shanghai

**Goal:** Build `field_evidence_material_resolution_reviewer_ack_intake` as a Docker/local software-proof ACK intake gate after owner-response review handoff.

**Architecture:** The PC gate classifies reviewer/support/field-owner ACK material and emits a canonical safe summary. Robot diagnostics exposes that summary through a metadata-only alias. `mobile/web` renders the alias as a read-only support panel. Hardware stays read-only and verifies PR #5 / WAVE ROVER / 2D LiDAR / ToF evidence boundaries.

**Tech Stack:** Python standard library CLI and `unittest`, ROS2 operator gateway diagnostics Python module, dependency-free `mobile/web` JavaScript/CSS, JSON fixtures, markdown interface/product docs.

---

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective: Objective 5, about 68%.
- 本 sprint 是否针对该最低 Objective: 是，针对 Objective 5 周边 material-resolution governance 的下一 rung，但只做 ACK intake 的 Docker/software-proof readiness。
- 具体理由: Objective 5 仍缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal delivery/dropoff/cancel result；本机无法产出这些真实外部材料。15-16 sprint 已完成 owner-response review handoff，本 sprint 把 handoff 后的 reviewer/support/field-owner ACK 转成可校验状态，避免把口头 ACK 当成真实 proof。
- 次低 Objective: Objective 1 about 81%。PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / hardware_material_pending；comment `3269642220` 是 software-proof only；本 sprint 不产生真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator HIL report 或 reviewer resolution。
- 收口要求: no OKR percentage lift。除非执行期出现真实 O5 external proof、O1 HIL/material proof、true phone/browser proof、route/elevator field proof 或 verified terminal result，否则 `final.md` 和 `OKR.md` 必须保持 no-lift。

## Non-Goals And Proof Boundary

This sprint is explicitly:

- not O5 external proof.
- not public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or production cutover proof.
- not O1 HIL.
- not PR #5 resolution.
- not true phone/browser proof.
- not route/elevator field pass.
- not verified terminal delivery/dropoff/cancel result.
- not dropoff completion, cancel completion, or delivery success.

Every implementation surface must preserve:

- `software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`
- `not_proven`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- no OKR percentage lift

## Interface Contract

### Input

- Previous handoff material from `field_evidence_material_resolution_owner_response_review_handoff`.
- Reviewer/support/field-owner ACK material with a safe actor role and response status.

### Supported ACK States

- `acknowledged`: handoff was received and can proceed to later reviewer material review, still `not_proven`.
- `needs_reassignment`: current reviewer/support/field-owner cannot own the review; next step is Product/support reassignment.
- `blocked_missing_handoff`: ACK references no valid handoff, no safe evidence ref, or missing required handoff material.
- `rejected_unsafe_ack`: ACK contains unsafe success/control/HIL/external-proof/delivery/credential/raw-artifact claims.

### Required Output Fields

- `schema=trashbot.field_evidence_material_resolution_reviewer_ack_intake.v1`
- `schema_version=1`
- `capability=field_evidence_material_resolution_reviewer_ack_intake`
- `proof_boundary=software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`
- `ack_status`
- `source_handoff_status`
- `safe_evidence_ref`
- `ack_actor_role`
- `acknowledged_by`
- `reviewer_material_review_next_step`
- `field_owner_supplement_required`
- `reassignment_required`
- `blocked_reason`
- `missing_required_materials`
- `rejected_unsafe_ack_reasons`
- `next_required_evidence`
- `software_proof=true`
- `not_proven=true`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`

## Parallel Owner Tasks

### Task A: Autonomy / PC ACK Intake Gate

**Owner:** `autonomy-engineer`

**Responsibility:** Create the canonical ACK intake artifact CLI and tests.

**Files:**

- Create: `pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_intake.py`
- Create: `pc-tools/evidence/test_field_evidence_material_resolution_reviewer_ack_intake.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/interfaces/evidence_contracts.md`

**Interface Impact:**

- New artifact schema: `trashbot.field_evidence_material_resolution_reviewer_ack_intake.v1`
- New summary schema: `trashbot.field_evidence_material_resolution_reviewer_ack_intake_summary.v1`
- Capability string: `field_evidence_material_resolution_reviewer_ack_intake`
- Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`
- Supported ACK states: `acknowledged`, `needs_reassignment`, `blocked_missing_handoff`, `rejected_unsafe_ack`

**Implementation Requirements:**

- Consume the previous owner-response review-handoff JSON from a file path argument.
- Consume ACK material from a file path argument or a minimal JSON string argument.
- Accept only reviewer/support/field-owner actor roles.
- Generate the required output fields listed in this plan.
- Map `acknowledged` to `reviewer_material_review_next_step=ready_for_reviewer_material_review_not_proven`.
- Map `needs_reassignment` to `reassignment_required=true` and next step `reassign_reviewer_or_support_owner`.
- Map `blocked_missing_handoff` to blocked state and list missing handoff/evidence-ref materials.
- Map unsafe claims to `rejected_unsafe_ack` and list rejection reasons.
- Fail closed when input is missing, malformed, missing safe evidence ref, missing source handoff, or contains unsafe success/control claims.
- Do not expose raw ROS topics, `/cmd_vel`, serial/UART paths, credentials, local paths, complete artifacts, checksums, stack traces, raw material payloads, or control commands.

**Acceptance Commands:**

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_intake.py
python3 -m unittest pc-tools.evidence.test_field_evidence_material_resolution_reviewer_ack_intake
python3 pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_intake.py --help
rg -n "field_evidence_material_resolution_reviewer_ack_intake|software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate|acknowledged|needs_reassignment|blocked_missing_handoff|rejected_unsafe_ack|delivery_success=false|not_proven|safe_to_control=false" pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_material_resolution_reviewer_ack_intake.py pc-tools/evidence/test_field_evidence_material_resolution_reviewer_ack_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B: Robot Diagnostics Safe Alias

**Owner:** `robot-software-engineer`

**Responsibility:** Expose ACK intake through Robot diagnostics as a sanitized safe alias.

**Files:**

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/operator_gateway_diagnostics.md`

**Interface Impact:**

- Add safe alias: `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary`
- Alias must be read-only, metadata-only, and fail closed when the upstream ACK intake summary is absent or unsafe.
- No control endpoint, ACK mutation, cursor mutation, replay, resubmit, serial open, WAVE ROVER command, Nav2 route execution, action result mutation, dropoff completion mutation, or cancel completion mutation.

**Implementation Requirements:**

- Preserve existing diagnostics behavior and safe-summary redaction patterns.
- Include only phone-safe fields from the PC artifact summary.
- Keep `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- Missing input should produce `blocked_missing_reviewer_ack_intake_not_proven` or equivalent blocked/not-proven summary.
- Unsafe `ack_status` or unsafe success/control copy must be rejected or downgraded to blocked.

**Acceptance Commands:**

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary|field_evidence_material_resolution_reviewer_ack_intake|software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
```

### Task C: Full-Stack Mobile Read-Only ACK Panel

**Owner:** `full-stack-software-engineer`

**Responsibility:** Render ACK intake summary in `mobile/web` without enabling primary actions.

**Files:**

- Modify: `mobile/web/app.js`
- Modify: `mobile/web/styles.css`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Create: `mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary.json`
- Modify: `docs/product/mobile_user_flow.md`

**Interface Impact:**

- Add a read-only panel titled in Chinese, for example: `现场材料 reviewer ACK 入口`.
- Consume `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary` first, then compatible nested phone-safe summaries.
- This panel must not affect Start Delivery, Confirm Dropoff, or Cancel authorization.

**Implementation Requirements:**

- Display `ack_status`, source handoff status, safe evidence ref, actor role, reviewer material review next step, reassignment requirement, field owner supplement requirement, missing required materials, rejected unsafe ACK reasons, next required evidence, proof boundary, and flags.
- Missing summary fails closed without raw artifact rendering.
- Chinese-first copy must make clear: this is not true phone/browser proof, not delivery success, not a robot control grant, and not PR #5 resolution.
- Do not expose raw JSON, ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER parameters, credentials, DB/queue URLs, local paths, complete artifacts, checksums, ACK/cursor payloads, HIL/pass wording, route/elevator field-pass claims, delivery success claims, dropoff completion claims, or cancel completion claims.

**Acceptance Commands:**

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary.json >/dev/null
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "field_evidence_material_resolution_reviewer_ack_intake|software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate|not true phone/browser|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary.json docs/product/mobile_user_flow.md
```

### Task D: Hardware Read-Only PR / Vendor Boundary Consultation

**Owner:** `robot-hardware-engineer`

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
- Confirm ACK intake does not resolve PR #5.
- Confirm no real 2D LiDAR/ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry materials are present in this sprint.
- Confirm no real WAVE ROVER/UART/HIL evidence is produced by this sprint.
- Mention `docs/vendor/VENDOR_INDEX.md` as the hardware source boundary.

**Acceptance Commands:**

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "WAVE ROVER|UART|2D LiDAR|ToF|VENDOR_INDEX|PRRT_kwDOSWB9286CJ3tX|3269642220|software_proof|field_evidence_material_resolution_reviewer_ack_intake" docs/vendor docs/product/production_hardware_boundary.md OKR.md sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake
git diff --check -- sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake
```

## Integration Acceptance

Product Manager / OKR Owner must only accept the sprint when all worker outputs report:

- actual changed files.
- validation command results.
- failure localization, if any.
- remaining risks.
- proof boundary remains `software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`.
- ACK states are exactly `acknowledged`, `needs_reassignment`, `blocked_missing_handoff`, and `rejected_unsafe_ack`.
- output next step explicitly says one of: proceed to later reviewer material review, request field owner supplement, reassign reviewer/support owner, or remain blocked.
- no OKR percentage lift unless real evidence appears.

Required final sprint validation after implementation and closeout:

```bash
test -f sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/tech-done.md && test -f sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/side2side_check.md && test -f sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/final.md
rg -n "field_evidence_material_resolution_reviewer_ack_intake|software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not true phone/browser|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|no OKR percentage lift" sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
```

## Planning Acceptance For This Turn

This planning-only task is accepted when:

```bash
test -f sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/pre_start.md && test -f sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/prd.md && test -f sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/tech-plan.md
rg -n "sprint_type: epic|field_evidence_material_resolution_reviewer_ack_intake|software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate|OKR 最低优先级核对|Objective 5|no OKR percentage lift" sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake
git diff --check -- sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/pre_start.md sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/prd.md sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/tech-plan.md
```

## Product Closeout Rules

- `tech-done.md` must record actual worker edits, exact validation results, deviations, and remaining risk.
- `side2side_check.md` must compare PRD acceptance criteria against actual worker evidence.
- `final.md` must explicitly state this sprint is not O5 external proof, not O1 HIL, not PR #5 resolution, not true phone/browser, not verified terminal result, and not delivery success.
- `OKR.md` should not receive a percentage lift for this planning target unless real external/hardware/field/phone/browser/terminal-result evidence appears during execution.
- If implementation discovers ACK intake is redundant with an existing artifact, stop and ask Product for rerank instead of creating another duplicate wrapper.

