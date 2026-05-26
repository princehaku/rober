# Field Evidence Real Material Owner Ack Review Decision Tech Plan

## Sprint Contract

- sprint_type: epic
- capability: `field_evidence_real_material_owner_ack_review_decision`
- evidence_boundary: `software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate`
- fixed_status: `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`
- implementation mode: 4 owner parallel execution with disjoint file ranges.
- hardware boundary: `docs/vendor/VENDOR_INDEX.md` is the required local vendor source entry point; this sprint does not change hardware configuration or claim HIL.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
- 本 sprint 是否针对该 Objective：否。
- 不针对理由：Objective 5 继续提高需要真实外部材料，包括 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser proof。最新 `2026.05.21_22-23_cloud-ack-lookup-pending-status-guard` 已完成 `software_proof_docker_cloud_ack_lookup_pending_status_guard`，并明确没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、true phone/browser 或 delivery success；继续做同类本地 metadata wrapper 不能提高 O5。
- 本轮转向理由：`2026.05.21_21-22_field-evidence-real-material-owner-ack-intake` 已完成 owner acknowledgement intake，下一步可在 Docker-only 环境推进 O2/O3/O4 现场材料链的 `field_evidence_real_material_owner_ack_review_decision`，把 owner ack 转为 `accepted` / `needs_more_evidence` / `rejected` structured review decision。这是可推进的真实材料采集功能入口，但仍保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- final.md 收口时需复核：O5 是否仍缺真实外部材料；如果仍缺，Objective 5 不得提高。

## Shared Evidence Boundary

All owners must preserve:

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false` unless live GitHub evidence changes and real materials exist.

Forbidden claims:

- real route/elevator field pass
- true phone/browser proof
- HIL or WAVE ROVER/UART proof
- real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover
- dropoff/cancel completion
- delivery result or delivery success
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved

## Parallel Owner Plan

### Autonomy Algorithm Engineer

Role id: `autonomy-engineer`

Goal: implement the PC evidence gate that converts owner ack intake into a structured review decision.

Allowed file range:

- `pc-tools/evidence/field_evidence_real_material_owner_ack_review_decision.py`
- `pc-tools/evidence/test_field_evidence_real_material_owner_ack_review_decision.py` or existing nearby evidence tests if repo convention requires that path.
- `docs/` evidence documentation directly describing this PC gate, likely under `docs/process/` or existing evidence docs discovered by the worker.
- Sprint implementation evidence in this sprint directory after planning, limited to `tech-done.md` updates assigned by Product if needed.

Do not modify:

- Robot diagnostics code.
- `mobile/web`.
- Hardware configuration, launch files, vendor files, or PR #5 status.

Expected behavior:

- Accept owner ack intake input with safe `evidence_ref`.
- Produce schema `trashbot.field_evidence_real_material_owner_ack_review_decision.v1`.
- Decision enum: `accepted`, `needs_more_evidence`, `rejected`.
- Reject unsafe copy, raw paths, credentials, ROS topics, serial/UART, WAVE ROVER details, checksums, HIL/pass wording, delivery success wording, and external-proof claims.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_real_material_owner_ack_review_decision.py
python3 -m unittest pc-tools.evidence.test_field_evidence_real_material_owner_ack_review_decision
rg -n "field_evidence_real_material_owner_ack_review_decision|accepted|needs_more_evidence|rejected|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools tests docs
git diff --check -- pc-tools tests docs
```

### Robot Platform Engineer

Role id: `robot-software-engineer`

Goal: expose a diagnostics safe alias / summary for the owner ack review decision.

Allowed file range:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md` or equivalent diagnostics contract doc discovered by the worker.
- Sprint implementation evidence in this sprint directory after planning, limited to `tech-done.md` updates assigned by Product if needed.

Do not modify:

- PC evidence gate.
- `mobile/web`.
- Hardware configuration, vendor files, or cloud relay runtime unless a diagnostics import requires read-only reference.

Expected behavior:

- Add safe alias / summary name `robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary`.
- Expose only review decision, source ack status, safe `evidence_ref`, decision reasons, missing materials, next required evidence, owner handoff, proof boundary, and fixed fail-closed status.
- Never expose raw artifacts, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, credentials, local paths, complete logs, checksums, HIL/pass wording, delivery success, or PR #5 resolved wording.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary|field_evidence_real_material_owner_ack_review_decision|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces
```

### User Touchpoint Full-Stack Engineer

Role id: `full-stack-software-engineer`

Goal: render the review decision as a mobile/web read-only panel and keep all primary actions fail-closed.

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_owner_ack_review_decision.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json` if needed to wire fixture coverage.
- `docs/product/mobile_user_flow.md`
- Sprint implementation evidence in this sprint directory after planning, limited to `tech-done.md` updates assigned by Product if needed.

Do not modify:

- PC evidence gate.
- Robot diagnostics implementation.
- Hardware configuration, vendor files, or cloud command endpoints.

Expected behavior:

- Add read-only panel for `field_evidence_real_material_owner_ack_review_decision`.
- Display only decision, source ack status, safe `evidence_ref`, missing materials, next required evidence, owner handoff, proof boundary, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Start Delivery / Confirm Dropoff / Cancel remain disabled.
- The panel must not trigger ACK, cursor, diagnostics fetch, review routes, material routes, Start, Confirm, Cancel, or any robot command.
- Unsafe copy, raw JSON, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, credentials, local paths, complete artifacts, checksums, HIL/pass wording, external-proof wording, delivery success, and route/elevator field-pass wording must be filtered or fail closed.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_owner_ack_review_decision.json >/tmp/field_evidence_real_material_owner_ack_review_decision_fixture.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "现场材料 owner ack 复核决策|field_evidence_real_material_owner_ack_review_decision|robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile docs/product/mobile_user_flow.md
```

### Hardware Infra Engineer

Role id: `robot-hardware-engineer`

Goal: perform read-only vendor / PR #5 boundary consultation.

Allowed file range:

- No implementation changes expected.
- Read-only sources:
  - `docs/vendor/VENDOR_INDEX.md`
  - relevant local vendor docs referenced by that index if hardware facts are discussed.
  - `docs/product/production_hardware_boundary.md` or equivalent production hardware boundary docs if present.
  - PR #5 evidence / live thread context when available.
- If a strictly needed documentation correction is discovered, return it as a proposed change for Product decision instead of editing outside this plan's scope.

Expected behavior:

- Confirm this sprint does not modify WAVE ROVER, ESP32, Orange Pi, UART, voltage, firmware, speed mapping, feedback protocol, pinout, or mechanical dimensions.
- Confirm `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending unless live evidence proves otherwise.
- Confirm owner ack review decision cannot close missing 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|2D LiDAR|ToF|HIL-entry|source=software_proof|not_proven" OKR.md docs sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision
git diff --check -- docs/vendor docs/product sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision
```

## Integration And Closeout Plan

Product Manager / OKR Owner will close the sprint after worker results:

- Create / update `tech-done.md` with actual file changes, validation outputs, deviations, and remaining risk.
- Create / update `side2side_check.md` with user-value acceptance against this PRD.
- Create / update `final.md` with OKR closeout and proof boundary.
- Update `OKR.md` and `docs/process/okr_progress_log.md` only if implementation lands and the closeout needs a conservative software-proof entry. Percentages must not increase without real external / hardware / field evidence.

Product acceptance commands after implementation:

```bash
test -f sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/tech-done.md
test -f sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/side2side_check.md
test -f sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/final.md
rg -n "field_evidence_real_material_owner_ack_review_decision|software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision
git diff --check -- OKR.md docs sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision
```

## Current Planning Validation Commands

This planning-only task must pass:

```bash
test -f sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/pre_start.md
test -f sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/prd.md
test -f sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/tech-plan.md
rg -n "field_evidence_real_material_owner_ack_review_decision|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision
git diff --check -- sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision
```

## Remaining Risk

- This plan creates only planning documents. It does not implement PC / Robot / mobile / hardware consultation work yet.
- The next implementation phase must use four parallel worker agents because file ranges are disjoint.
- Real materials remain missing. Without them, this sprint cannot prove HIL, true field pass, delivery result, true phone/browser, PR #5 resolution, or O5 external readiness.
