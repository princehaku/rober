# Field Evidence Rerun Execution Result Acceptance Backfill Tech Plan

Run time: 2026-05-21 12:02 CST

> For implementation workers: use subagent-driven development. This sprint has 3 parallel Engineer owners with disjoint file scopes, plus Product closeout after implementation. Do not let the main session write product code, tests, hardware config, or runtime implementation.

## Goal

Build `field_evidence_rerun_execution_result_acceptance_backfill`, the controlled backfill entrance after the execution-result acceptance packet.

The implementation must produce only `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate` evidence and must keep `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Architecture

- Autonomy owns the PC evidence gate that validates/sanitizes the field owner backfill manifest and emits a safe summary.
- Robot owns the operator gateway diagnostics alias that exposes only safe metadata and fails closed.
- Full-Stack owns the mobile/web read-only panel that shows the backfill state without enabling primary actions.
- Product owns post-implementation closeout only after the three Engineer streams return evidence.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：部分相关但不提升 Objective 5。
- 理由：Objective 5 要提升仍需真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或真实手机/browser proof；本机只有 Docker，且上一轮明确不能重复 local wrapper。本 sprint 选择 acceptance packet 后的受控回填入口，服务于后续真实 route/elevator/mobile/O5/O1 材料进入 review decision，但自身保持 software-proof/not_proven。
- final.md 收口时需复核：是否出现真实 O5 external proof、真实 O1 hardware/HIL materials、或真实 same-safe-`evidence_ref` route/elevator/mobile field materials；若没有，`OKR.md` 不得提高百分比。

## Shared Contract

All owners must preserve these fields and wording:

- `field_evidence_rerun_execution_result_acceptance_backfill`
- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false`
- comment `3269642220` is a software-proof reply only

Forbidden claims:

- real HIL
- WAVE ROVER/UART proof
- real field rerun
- real phone/browser proof
- O5 external proof
- delivery_success
- PR #5 reviewer resolution

Forbidden exposure:

- raw ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters
- credentials, bearer tokens, Authorization headers, OSS AK/SK, DB/queue URLs
- raw artifacts, complete artifacts, local paths, checksums, tracebacks
- success phrasing or control-enable copy

## Parallel Owner Plan

### Owner 1: Autonomy Algorithm Engineer

Role id: `autonomy-engineer`

Files:

- Create: `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill.py`
- Create: `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_backfill.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/interfaces/evidence_contracts.md`

Responsibilities:

1. Implement a CLI gate that accepts an acceptance-packet/backfill material input and writes a sanitized manifest/summary for `field_evidence_rerun_execution_result_acceptance_backfill`.
2. Require a safe `evidence_ref` and preserve same-evidence-ref semantics across task record, Nav2/fixed-route runtime log, route completion signal, elevator evidence, dropoff/cancel completion, delivery result, and true phone/browser evidence categories.
3. Mark missing, blocked, template, mismatch, unsafe, sensitive, and success-claim materials as blocked/not_proven.
4. Emit only safe summary fields for Robot/mobile.
5. Add targeted tests for happy safe manifest, missing materials, evidence-ref mismatch, and sensitive/success-claim rejection.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill.py
python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_backfill.py
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill.py --help
rg -n "field_evidence_rerun_execution_result_acceptance_backfill|software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_backfill.py pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_backfill.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Owner 2: Robot Platform Engineer

Role id: `robot-software-engineer`

Files:

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/ros_runtime_contracts.md`

Responsibilities:

1. Add Robot diagnostics support for `field_evidence_rerun_execution_result_acceptance_backfill` safe summary.
2. Expose only phone-safe metadata and preserve fail-closed fields.
3. Do not expose raw manifest contents, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, or complete artifacts.
4. Ensure missing/invalid summary stays `not_proven` and primary actions remain disabled.
5. Add targeted diagnostics tests without broad unrelated regression sweeps.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "field_evidence_rerun_execution_result_acceptance_backfill|software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Owner 3: User Touchpoint Full-Stack Engineer

Role id: `full-stack-software-engineer`

Files:

- Modify: `mobile/web/app.js`
- Create: `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

Responsibilities:

1. Add a read-only “现场证据复跑执行结果验收回填” panel for `field_evidence_rerun_execution_result_acceptance_backfill`.
2. Consume status/diagnostics/phone_readiness compatible safe summary fields without fetching raw artifacts.
3. Show only backfill status, safe `evidence_ref`, missing/blocked categories, owner next steps, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
4. Keep Start Delivery, Confirm Dropoff, and Cancel disabled under the fixture.
5. Add a fixture and targeted mobile test for render, fail-closed controls, and redaction boundaries.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill.json >/tmp/field_evidence_rerun_execution_result_acceptance_backfill_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_rerun_execution_result_acceptance_backfill|software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Product Closeout After Implementation

Role id: `product-okr-owner`

Files:

- Modify: `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/tech-done.md`
- Modify: `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/side2side_check.md`
- Modify: `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

Responsibilities:

1. Integrate the three Engineer reports and record actual changed files, validation results, deviations, and remaining risks.
2. Keep `OKR.md` conservative: Objective 5 remains around 68% unless real O5 external evidence appears; Objective 1 remains around 81% unless real PR #5/hardware/HIL material appears; Objectives 2/3/4 remain around 99% unless real field/mobile/delivery evidence appears.
3. Write final closeout so this sprint is accepted only as `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate`.
4. Explicitly state that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless a live reviewer resolution is present.

Acceptance commands:

```bash
test -f sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/tech-done.md && test -f sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/side2side_check.md && test -f sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/final.md
rg -n "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill OKR.md docs/process/okr_progress_log.md
```

## Dispatch Requirements

Implementation must start 3 parallel Engineer workers in one dispatch set:

- Autonomy Algorithm Engineer for PC evidence gate files.
- Robot Platform Engineer for diagnostics/runtime contract files.
- User Touchpoint Full-Stack Engineer for mobile/web files.

Product closeout starts only after the three Engineer workers return. If any owner fails validation, send the failure back to the same owner before closeout.

## Planning Validation Commands

The Product Owner planning task must run:

```bash
test -f sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/pre_start.md && test -f sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/prd.md && test -f sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_rerun_execution_result_acceptance_backfill|software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill
git diff --check -- sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill
```
