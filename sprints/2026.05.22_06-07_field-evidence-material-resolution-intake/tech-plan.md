# Field Evidence Material Resolution Intake Tech Plan

Run time: 2026-05-22 06:07 Asia/Shanghai

> **For agentic workers:** implement this plan with parallel Codex `spawn_agent(agent_type=worker)` calls. Each worker must receive its role prompt from `.codex/agents/<role>.toml`, the task below, exact file scope, exact validation commands, and the required output checklist.

## Goal

Build `field_evidence_material_resolution_intake` as the next software-proof rung after blocker escalation: consume a blocker escalation artifact/summary/Robot alias plus an owner-provided safe resolution packet, require the same safe `evidence_ref`, classify `accepted` / `missing` / `rejected` / `blocked`, and expose a sanitized read-only summary through PC gate, Robot diagnostics, and mobile/web.

## Architecture

- Autonomy owns the canonical PC evidence gate and fixture/test behavior.
- Robot consumes only the sanitized summary and exposes a safe diagnostics alias.
- Full-Stack consumes the Robot alias first and renders a read-only mobile/web panel.
- Hardware performs read-only vendor / PR #5 boundary consultation for `PRRT_kwDOSWB9286CJ3tX`; it does not change hardware config.
- Product performs closeout only after workers return evidence.

## Shared Evidence Boundary

All implementation tasks must preserve:

- Capability: `field_evidence_material_resolution_intake`
- Artifact schema: `trashbot.field_evidence_material_resolution_intake.v1`
- Summary schema: `trashbot.field_evidence_material_resolution_intake_summary.v1`
- Robot alias: `robot_diagnostics_field_evidence_material_resolution_intake_summary`
- Evidence boundary: `software_proof_docker_field_evidence_material_resolution_intake_gate`
- Required false-state flags: `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`
- Safe decision values: `accepted`, `missing`, `rejected`, `blocked`
- Required same-evidence-ref rule: blocker escalation source and owner safe resolution packet must share the same safe `evidence_ref`

Do not expose raw artifact bodies, complete logs, local filesystem paths, credentials, bearer tokens, DB/queue URLs, OSS AK/SK, signed URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, checksums, tracebacks, success/pass/control wording, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true`.

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 68%。Objective 1 约 81%；Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5 的最低优先级缺口：把 O5 external、terminal-result、route/elevator/phone、O1 PR #5 hardware/HIL 等 blocker escalation 转成可消费的 owner resolution intake，而不是继续新增 missing-material wrapper。
3. 本轮仍不能提升 Objective 5 完成度，除非后续 implementation 阶段拿到真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser 或 verified terminal delivery/dropoff/cancel result material。Docker-only fixture / CLI / Robot diagnostics / mobile panel 只能算 `software_proof`。
4. 本轮也不能提升 Objective 1，除非 PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX` 获得真实 2D LiDAR / ToF vendor/source/procurement/install/calibration/HIL-entry evidence and reviewer resolution。PR #5 merged and PR #6 docs-only merged do not equal hardware proof.

## Parallel Owner Plan

### Worker A: Autonomy PC Gate

**Owner:** `autonomy-engineer`

**Files allowed:**

- Create: `pc-tools/evidence/field_evidence_material_resolution_intake.py`
- Create: `pc-tools/evidence/test_field_evidence_material_resolution_intake.py`
- Modify: `docs/interfaces/evidence_contracts.md` or create `docs/interfaces/field_evidence_material_resolution_intake.md`
- Modify: `pc-tools/README.md`

**Task:**

1. Implement a dependency-light Python CLI that accepts a blocker escalation artifact/summary/Robot alias JSON and an owner safe resolution packet JSON.
2. Validate supported schemas and safe fields.
3. Require same safe `evidence_ref`.
4. Produce sanitized artifact + summary with decision `accepted` / `missing` / `rejected` / `blocked`.
5. Fail closed on missing owner packet, missing source blocker escalation, schema mismatch, unsafe copy, evidence-ref mismatch, raw fields, truthy action/control/success flags, success wording, credentials, local paths, ROS topics, `/cmd_vel`, serial/UART or WAVE ROVER details.
6. Document the contract and PC usage without claiming real materials.

**Minimum expected CLI behavior:**

- Accepted packet with same safe `evidence_ref` prints `field_evidence_material_resolution_intake_ready_not_proven`.
- Missing required resolution material prints or records `missing`.
- Rejected unsafe material records `rejected`.
- Missing source packet or evidence mismatch records `blocked`.

**Validation commands:**

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_intake.py
python3 -m unittest pc-tools.evidence.test_field_evidence_material_resolution_intake
python3 pc-tools/evidence/field_evidence_material_resolution_intake.py --help
rg -n "field_evidence_material_resolution_intake|software_proof_docker_field_evidence_material_resolution_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|same_evidence_ref" pc-tools/evidence/field_evidence_material_resolution_intake.py pc-tools/evidence/test_field_evidence_material_resolution_intake.py docs/interfaces pc-tools/README.md
git diff --check -- pc-tools/evidence/field_evidence_material_resolution_intake.py pc-tools/evidence/test_field_evidence_material_resolution_intake.py docs/interfaces pc-tools/README.md
```

**Output required from worker:**

1. Actual changed files.
2. Validation output snippets.
3. Failure diagnosis if any.
4. Remaining risks.

### Worker B: Robot Diagnostics Alias

**Owner:** `robot-software-engineer`

**Files allowed:**

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/operator_gateway_diagnostics.md`
- Modify: `docs/interfaces/ros_contracts.md` if this repo pattern requires the diagnostics alias table update

**Task:**

1. Add `robot_diagnostics_field_evidence_material_resolution_intake_summary` as a safe diagnostics alias.
2. Consume only sanitized `trashbot.field_evidence_material_resolution_intake_summary.v1` or compatible nested summary from status/diagnostics inputs.
3. Preserve only whitelisted fields: decision, safe evidence ref, accepted/missing/rejected/blocked summaries, next required evidence, owner handoff, evidence boundary, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
4. Fail closed on missing summary, unsupported schema/boundary, unsafe copy, raw artifact, local path, credential, ACK/cursor payload, complete artifact/checksum, success/pass/control copy, or truthy false-state flags.
5. Update diagnostics docs with read-only and no-control boundary.

**Validation commands:**

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_resolution_intake_summary|field_evidence_material_resolution_intake|software_proof_docker_field_evidence_material_resolution_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md
```

**Output required from worker:**

1. Actual changed files.
2. Validation output snippets.
3. Failure diagnosis if any.
4. Remaining risks.

### Worker C: Full-Stack Mobile/Web Read-Only Panel

**Owner:** `full-stack-software-engineer`

**Files allowed:**

- Modify: `mobile/web/app.js`
- Modify: `mobile/web/index.html` only if an explicit mount point is required by existing pattern
- Modify: `mobile/web/styles.css` only if panel styles cannot reuse existing classes
- Create: `mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_intake_summary.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

**Task:**

1. Add a read-only panel for `field_evidence_material_resolution_intake`.
2. Consume `robot_diagnostics_field_evidence_material_resolution_intake_summary` first, then compatible `field_evidence_material_resolution_intake_summary` fallback from existing safe status/diagnostics locations.
3. Render only decision, safe evidence ref, accepted/missing/rejected/blocked summaries, next required evidence, owner handoff, evidence boundary, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
4. Keep Start Delivery, Confirm Dropoff and Cancel disabled by existing gates; do not add copy/export controls unless the backend provides a whitelist-only `safe_copy`.
5. Ensure the panel cannot trigger ACK, cursor, diagnostics fetch, material fetch, Start/Confirm/Cancel, replay, resubmit, or robot command routes.
6. Update mobile user flow docs with Docker-only / not real phone/browser boundary.

**Validation commands:**

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_intake_summary.json >/tmp/field_evidence_material_resolution_intake_mobile_fixture.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "field_evidence_material_resolution_intake|robot_diagnostics_field_evidence_material_resolution_intake_summary|software_proof_docker_field_evidence_material_resolution_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/index.html mobile/web/styles.css mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_intake_summary.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

**Output required from worker:**

1. Actual changed files.
2. Validation output snippets.
3. Failure diagnosis if any.
4. Remaining risks.

### Worker D: Hardware Vendor / PR #5 Boundary Consultation

**Owner:** `robot-hardware-engineer`

**Files allowed:**

- Read only: `docs/vendor/VENDOR_INDEX.md`
- Read only: vendor files referenced by `docs/vendor/VENDOR_INDEX.md`
- Read only: PR #5 / PR #6 local docs if present under `docs/interfaces/` or `docs/product/`
- No product code, test code, hardware config, launch, CMake, firmware, or docs writes in this consultation task unless Product explicitly expands scope later.

**Task:**

1. Confirm from local vendor index and referenced local vendor docs what can and cannot be claimed for mandatory sensor assumptions.
2. Confirm that `PRRT_kwDOSWB9286CJ3tX` remains a hardware material / vendor-source boundary issue, not HIL or reviewer resolution.
3. Produce consultation text for Product and implementation workers: source citations to use, claims to avoid, and exact boundary phrases for `not_proven`.
4. Do not modify hardware config or vendor docs.

**Validation commands:**

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "WAVE ROVER|UART|JSON|2D LiDAR|ToF|PRRT_kwDOSWB9286CJ3tX|not_proven|software_proof" docs/vendor docs/interfaces docs/product pc-tools/README.md
git diff --check -- docs/vendor docs/interfaces docs/product pc-tools/README.md
```

**Output required from worker:**

1. Files read and any files changed; expected changed files should be none for this task.
2. Validation output snippets.
3. Hardware/source-boundary findings.
4. Remaining risks.

### Worker E: Product Closeout After Workers

**Owner:** `product-okr-owner`

**Files allowed after implementation:**

- Create/modify: `sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/tech-done.md`
- Create/modify: `sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/side2side_check.md`
- Create/modify: `sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

**Task:**

1. Integrate worker evidence and verify no owner overclaimed beyond `software_proof`.
2. Confirm docs under `docs/` were synchronized by implementation owners.
3. Keep Objective 5 around 68%, Objective 1 around 81%, Objective 2/3/4 around 99% unless real evidence appeared.
4. Record that `accepted` is not delivery success, HIL, field pass, real phone/browser proof, real public cloud proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution, dropoff/cancel completion, or verified terminal delivery result.
5. Write final closeout and remaining evidence gaps.

**Validation commands:**

```bash
test -f sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/tech-done.md
test -f sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/side2side_check.md
test -f sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/final.md
rg -n "field_evidence_material_resolution_intake|software_proof_docker_field_evidence_material_resolution_intake_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_06-07_field-evidence-material-resolution-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_06-07_field-evidence-material-resolution-intake
```

**Output required from worker:**

1. Actual changed files.
2. Validation output snippets.
3. Failure diagnosis if any.
4. Remaining risks.

## Dispatch Rule For Next Turn

When implementation starts, dispatch Worker A, Worker B, Worker C, and Worker D in the same parallel launch round. Worker E waits until implementation evidence returns. Do not serialize A/B/C/D unless a runtime lacks subagent capability.

## Cross-Owner Interface Contract

- Worker A defines canonical summary keys and fixture behavior.
- Worker B must consume Worker A summary only through safe summary fields; no raw artifact reads.
- Worker C must consume Worker B alias first; fallback to Worker A compatible summary is allowed only from existing safe status/diagnostics surfaces.
- Worker D provides source-boundary text only; it does not change schemas or hardware behavior.
- Product validates all evidence boundaries before `OKR.md` closeout.

## Required Planning Validation

This planning task must pass:

```bash
test -f sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/pre_start.md
test -f sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/prd.md
test -f sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/tech-plan.md
rg -n "field_evidence_material_resolution_intake|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.22_06-07_field-evidence-material-resolution-intake
git diff --check -- sprints/2026.05.22_06-07_field-evidence-material-resolution-intake
```

## Remaining Risks Before Implementation

- The plan assumes owner-provided safe resolution packet shape can be represented as a small JSON fixture; Worker A must keep schema narrow and fail closed rather than inventing real material.
- Hardware consultation can cite local vendor files, but it cannot resolve PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- The Docker-only host cannot validate real mobile browser behavior, production cloud ingress, OSS/CDN traffic, production DB/queue, WAVE ROVER/UART, HIL, Nav2/fixed-route runtime, real elevator, dropoff completion, cancel completion, terminal delivery result, or delivery success.
