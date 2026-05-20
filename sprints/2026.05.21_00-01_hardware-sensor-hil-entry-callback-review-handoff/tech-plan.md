# Hardware Sensor HIL-entry Callback Review Handoff Tech Plan

## Goal

Plan the next Epic implementation step for `hardware_sensor_hil_entry_callback_review_handoff`: turn the previous `hardware_sensor_hil_entry_callback_review_decision` software proof into a safe owner handoff path across Hardware PC gate, Robot diagnostics safe alias, and Full-Stack mobile/web read-only panel.

This planning sprint creates only `pre_start.md`, `prd.md`, and `tech-plan.md`. It does not modify product code, tests, `OKR.md`, `docs/process`, or runtime docs.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5 completion。
3. 不针对理由：Objective 5 只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 phone/browser external proof 才能继续提高。本机只有 Docker，没有这些真实外部材料。最近 21-22/22-23/23-24 已连续完成 O5 local software guards：`cloud_media_degradation_status_guard`、`cloud_command_sequence_regression_guard`、`cloud_status_stale_guard`。继续堆本地 O5 metadata 会重复消费同一 external proof blocker。
4. 当前下一低项是 Objective 1，约 81%。本轮转向 O1 的具体证据是 PR #5 `PRRT_kwDOSWB9286CJ3tX` live review thread 仍 `is_resolved=false` / material pending，review 要求 mandatory 2D LiDAR / ToF sensor assumptions cite vendor/local sources and provide real materials。
5. 最近 sprint `sprints/2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision/final.md` 已完成 `hardware_sensor_hil_entry_callback_review_decision` software proof。下一步应进入 `hardware_sensor_hil_entry_callback_review_handoff`，不能重复 callback intake 或 review decision。
6. 本轮即使完成后也不提高 Objective 1，除非真实 2D LiDAR / ToF materials、真实 WAVE ROVER/UART/HIL evidence 和 reviewer resolution 到位。

## Evidence Boundary

Every downstream owner must preserve these exact strings and semantics:

- Evidence boundary: `software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate`
- Source: `source=software_proof`
- Proof status: `not_proven`
- Control status: `safe_to_control=false`
- Delivery status: `delivery_success=false`
- Primary action status: `primary_actions_enabled=false`

Required non-claims:

- Not real 2D LiDAR / ToF.
- Not WAVE ROVER/UART/HIL.
- Not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved.
- Not Objective 5 external proof.
- Not real phone/browser.
- Not route/elevator field pass.
- Not delivery success.

Hardware source boundary is `docs/vendor/VENDOR_INDEX.md`; implementation must cite local vendor files only for source-boundary facts and must not infer missing SKU, wiring, power, mounting, calibration, or HIL materials.

## Parallel Owner Plan

### Owner A：Hardware Infra Engineer - PC Gate

**本轮任务**

Create the PC-only `hardware_sensor_hil_entry_callback_review_handoff` gate. It consumes the prior callback review decision artifact/summary and emits a handoff artifact/summary for owner follow-up.

**Allowed file scope for implementation sprint**

- `pc-tools/evidence/hardware_sensor_hil_entry_callback_review_handoff.py`
- `tests/test_hardware_sensor_hil_entry_callback_review_handoff.py`
- `pc-tools/README.md`
- `docs/product/production_hardware_boundary.md`
- current sprint `tech-done.md` evidence section only after implementation

**Interface requirements**

- Input must accept prior `hardware_sensor_hil_entry_callback_review_decision` artifact or summary.
- Output artifact schema should be `trashbot.hardware_sensor_hil_entry_callback_review_handoff.v1`.
- Output summary schema should be `trashbot.hardware_sensor_hil_entry_callback_review_handoff_summary.v1`.
- Required handoff states should include accepted handoff, blocked missing materials, rejected source decision, unsafe input, evidence-ref mismatch, unsupported schema, and malformed input.
- Summary must expose only handoff status, source review decision status, safe evidence ref, owner handoff, missing required materials, next required evidence, evidence boundary, and non-claim flags.

**Acceptance commands for Owner A**

```bash
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_callback_review_handoff.py tests/test_hardware_sensor_hil_entry_callback_review_handoff.py
python3 -m unittest tests.test_hardware_sensor_hil_entry_callback_review_handoff
python3 pc-tools/evidence/hardware_sensor_hil_entry_callback_review_handoff.py --help
rg -n "hardware_sensor_hil_entry_callback_review_handoff|software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate|source=software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|PRRT_kwDOSWB9286CJ3tX" pc-tools tests docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_sensor_hil_entry_callback_review_handoff.py tests/test_hardware_sensor_hil_entry_callback_review_handoff.py pc-tools/README.md docs/product/production_hardware_boundary.md
```

### Owner B：Robot Platform Engineer - Diagnostics Safe Alias

**本轮任务**

Expose `robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary` as a scrubbed diagnostics alias, without changing task execution, ACK, cursor, Nav2, HIL, command, or control behavior.

**Allowed file scope for implementation sprint**

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- current sprint `tech-done.md` evidence section only after implementation

**Interface requirements**

- Diagnostics must consume the PC summary only when schema and required boundary fields match.
- Missing, malformed, unsafe, wrong-source, or unsupported handoff summaries must fail closed.
- Safe alias must include no raw material payload, no raw JSON, no ROS topic names, no serial/UART paths, no local paths, no credentials, no checksums, and no complete internal logs.
- Must preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.

**Acceptance commands for Owner B**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary|hardware_sensor_hil_entry_callback_review_handoff|software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate|source=software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Owner C：User Touchpoint Full-Stack Engineer - Mobile/Web Read-only Panel

**本轮任务**

Add a mobile/web read-only “传感器 HIL 回调复核交接” panel that consumes the Robot diagnostics safe alias or safe fixture summary and keeps all primary actions disabled.

**Allowed file scope for implementation sprint**

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- optional focused fixture under `mobile/web/fixtures/`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- current sprint `tech-done.md` evidence section only after implementation

**Interface requirements**

- Panel must render only handoff status, source review decision status, safe evidence ref, owner handoff, missing required materials, next required evidence, evidence boundary, `software_proof`, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Panel must not provide copy/export controls and must not trigger Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, handoff route, callback route, review route, Nav2, HIL, or robot command requests.
- Panel must filter raw artifacts, raw review artifacts, raw callback packets, raw JSON, ROS topic names, serial/UART paths, credentials, local filesystem paths, complete internal logs, checksums, WAVE ROVER parameters, Objective 5 external proof, real phone/browser proof, HIL, route/elevator field pass, dropoff/cancel completion, and delivery success claims.

**Acceptance commands for Owner C**

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "hardware_sensor_hil_entry_callback_review_handoff|robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary|software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate|source=software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|传感器 HIL 回调复核交接" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Product Closeout - PM / OKR Owner

**本轮任务**

After A/B/C implementation and validation, Product updates the Epic closeout docs and OKR boundary without overstating progress.

**Allowed file scope for closeout**

- `sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/tech-done.md`
- `sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/side2side_check.md`
- `sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

**Closeout requirements**

- Objective 5 remains about 68% unless real external proof arrives.
- Objective 1 remains about 81% unless real 2D LiDAR / ToF materials, WAVE ROVER/UART/HIL evidence, and PR #5 reviewer resolution arrive.
- Explicitly state whether implementation stayed within `software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate`.
- Include Engineer validation logs and failure fixes if any.

## Cross-owner Integration Contract

- Owner A owns schema names and source boundary.
- Owner B may only consume Owner A's safe summary contract and must fail closed on mismatch.
- Owner C may only consume Owner B safe alias or safe fixture summary and must not read raw artifacts.
- No owner may claim `hil_pass`, real hardware material pass, route/elevator field pass, Objective 5 external proof, real phone/browser proof, PR #5 resolved, or delivery success.
- All code comments added in implementation must be Chinese and meaningful; target comment ratio remains above 20%.
- Documentation under `docs/` must be updated by implementation owners where their behavior changes.

## Planning Validation Commands

Run for this planning sprint:

```bash
test -f sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/pre_start.md && test -f sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/prd.md && test -f sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/tech-plan.md
rg -n "sprint_type: epic|hardware_sensor_hil_entry_callback_review_handoff|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate|source=software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff
git diff --check -- sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff
```

## Remaining Risks Before Implementation

- This planning sprint does not add product/runtime code, tests, `OKR.md`, or persistent product docs beyond sprint planning.
- True O1 progress still requires real 2D LiDAR / ToF material and HIL evidence.
- True O5 progress still requires real external cloud/4G/OSS/CDN/DB/queue/phone proof.
- Review handoff can reduce ambiguity, but it cannot close `PRRT_kwDOSWB9286CJ3tX` without real materials or reviewer action.
