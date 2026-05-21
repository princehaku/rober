# Verified Terminal Result Material Intake Tech Plan

Run time: 2026-05-22 04:05 Asia/Shanghai

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5 的下一步可行动材料路径：`verified_terminal_result_material_intake`。
3. 本 sprint 不继续堆本地 O5 metadata。上一轮 `cloud_command_lifecycle_audit_export` 已明确下一步需要真实 external proof 或 verified terminal delivery/dropoff/cancel result；本轮把 verified terminal result material 变成可摄取、可校验、可安全展示的 gate。
4. 本 sprint 不提升 Objective 5 百分比，除非 field owner 在本轮实施期间提供真实 terminal delivery/dropoff/cancel result evidence bundle，并且 Product closeout 能按同一 safe `evidence_ref` 验证通过。
5. 本 sprint 不推进 Objective 1 completion。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending；当前 Docker-only 主机不能产生真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF source/procurement/install/calibration 或 reviewer resolution。

## Architecture Decision

`verified_terminal_result_material_intake` is a three-surface software-proof gate:

1. PC evidence intake CLI reads a JSON bundle from a field owner and emits a sanitized summary artifact.
2. Robot diagnostics/status consumes the summary and exposes a safe alias for support/mobile.
3. Mobile/web renders a read-only panel with safe copy support.

The design deliberately separates "material accepted for review" from "delivery succeeded". Every surface must preserve:

- `capability=verified_terminal_result_material_intake`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Interface Contract

### Input Bundle

Expected bundle schema: `trashbot.verified_terminal_result_material_intake.v1`.

Required top-level fields:

- `schema`
- `capability`
- `evidence_boundary`
- `evidence_ref`
- `terminal_result_type`
- `required_materials`
- `material_refs`
- `owner_handoff`
- `not_proven`
- `delivery_success`
- `primary_actions_enabled`
- `safe_to_control`

Allowed `terminal_result_type` values:

- `delivery`
- `dropoff`
- `cancel`

Required material groups:

- task record reference under the same safe `evidence_ref`.
- command lifecycle audit or command/status reference under the same safe `evidence_ref`.
- terminal result payload reference under the same safe `evidence_ref`.
- route/elevator material reference when delivery/dropoff is claimed for route/elevator flow.
- field owner note explaining collection context and remaining gaps.

### Output Summary

Expected summary schema: `trashbot.verified_terminal_result_material_intake_summary.v1`.

Required safe fields:

- `schema`
- `capability`
- `intake_status`
- `terminal_result_type`
- safe `evidence_ref`
- safe `command_id` when present
- `required_materials_summary`
- `blocked_reason`
- `next_required_evidence`
- `owner_handoff`
- `safe_copy`
- `evidence_boundary`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Forbidden in safe output:

- raw artifact bodies, complete JSON dumps, raw robot responses, credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, local paths, checksums, tracebacks, raw ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER control details, hardware device paths, or success/control claims.

## Parallel Owner Plan

Implementation must launch Task A, Task B, and Task C in parallel via `spawn_agent(agent_type=worker)` because file scopes are distinct. Task D runs after worker evidence returns. Each worker prompt must include the five fixed sections from `AGENTS.md`: role system prompt, task, file scope, acceptance commands, and output requirements.

### Task A - Autonomy Algorithm Engineer

Role: `autonomy-engineer`

Goal: add the PC evidence intake CLI and tests for `verified_terminal_result_material_intake`.

Allowed files:

- `pc-tools/evidence/verified_terminal_result_material_intake.py`
- `tests/test_verified_terminal_result_material_intake.py`
- `docs/interfaces/verified_terminal_result_material_intake.md`
- `pc-tools/README.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/tech-done.md`

Interface requirements:

- Read one JSON evidence bundle from `--input`.
- Write sanitized summary artifact to `--output-dir`.
- Validate same safe `evidence_ref` across top-level bundle and nested material refs.
- Validate `terminal_result_type` is `delivery`, `dropoff`, or `cancel`.
- Validate required materials for the selected terminal result type.
- Reject raw artifacts, unsafe fields, local paths, credentials, ROS/control details, hardware details, and success/control overclaims.
- Emit `software_proof_docker_verified_terminal_result_material_intake_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- All new technical code comments must be meaningful Chinese comments.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/verified_terminal_result_material_intake.py tests/test_verified_terminal_result_material_intake.py
python3 -m unittest tests.test_verified_terminal_result_material_intake
python3 pc-tools/evidence/verified_terminal_result_material_intake.py --help
rg -n "verified_terminal_result_material_intake|software_proof_docker_verified_terminal_result_material_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|terminal_result_type|evidence_ref" pc-tools/evidence/verified_terminal_result_material_intake.py tests/test_verified_terminal_result_material_intake.py docs/interfaces/verified_terminal_result_material_intake.md pc-tools/README.md sprints/2026.05.22_04-05_verified-terminal-result-material-intake
git diff --check -- pc-tools/evidence/verified_terminal_result_material_intake.py tests/test_verified_terminal_result_material_intake.py docs/interfaces/verified_terminal_result_material_intake.md pc-tools/README.md sprints/2026.05.22_04-05_verified-terminal-result-material-intake
```

### Task B - Robot Platform Engineer

Role: `robot-software-engineer`

Goal: expose a Robot diagnostics/status safe alias for the intake summary while keeping all controls disabled.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/tech-done.md`

Interface requirements:

- Consume `verified_terminal_result_material_intake`, `verified_terminal_result_material_intake_summary`, or compatible nested diagnostics/status summary.
- Expose `robot_diagnostics_verified_terminal_result_material_intake_summary`.
- Preserve summary schema `trashbot.verified_terminal_result_material_intake_summary.v1`.
- Force fail-closed values in the exposed summary: `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Do not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, or robot control.
- Strip or block unsafe raw fields before diagnostics output.
- All new technical code comments must be meaningful Chinese comments.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "verified_terminal_result_material_intake|robot_diagnostics_verified_terminal_result_material_intake_summary|software_proof_docker_verified_terminal_result_material_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.22_04-05_verified-terminal-result-material-intake
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.22_04-05_verified-terminal-result-material-intake
```

### Task C - User Touchpoint Full-Stack Engineer

Role: `full-stack-software-engineer`

Goal: add a mobile/web read-only terminal-result material intake panel with safe copy support.

Allowed files:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_intake.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/tech-done.md`

Interface requirements:

- Consume `robot_diagnostics_verified_terminal_result_material_intake_summary`, `verified_terminal_result_material_intake_summary`, or compatible nested diagnostics/status summary.
- Render only intake status, terminal result type, safe `evidence_ref`, safe `command_id`, required materials summary, blocked reason, next required evidence, owner handoff, evidence boundary, and safe copy.
- Copy button is enabled only when backend-provided `safe_copy` is present and contains no unsafe raw fields.
- Missing or unsafe summary renders blocked / `not_proven`.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- The panel must not fetch raw diagnostics, raw artifacts, ACK routes, cursor routes, command routes, or replay/resubmit any request.
- All new technical code comments must be meaningful Chinese comments.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_intake.json >/tmp/robot_diagnostics_verified_terminal_result_material_intake.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "verified_terminal_result_material_intake|software_proof_docker_verified_terminal_result_material_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|terminal result|evidence_ref" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.22_04-05_verified-terminal-result-material-intake
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.22_04-05_verified-terminal-result-material-intake
```

### Task D - Product Manager / OKR Owner Closeout

Role: `product-okr-owner`

Goal: integrate worker evidence, update sprint closeout, and update OKR/progress only with conservative proof language.

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/tech-done.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/side2side_check.md`
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/final.md`

Closeout requirements:

- Keep Objective 5 around 68% unless real terminal delivery/dropoff/cancel result materials are supplied and verified during the sprint.
- Keep Objective 1 around 81% unless PR #5 `PRRT_kwDOSWB9286CJ3tX` receives real material and live reviewer resolution.
- Keep Objective 2/3/4 around 99% unless real route/elevator/Nav2/fixed-route/phone materials are supplied and verified.
- Record this sprint as `software_proof_docker_verified_terminal_result_material_intake_gate`.
- Explicitly state `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Confirm docs synchronization for every implementation owner.
- Confirm no implementation owner treated a truthy terminal result field as delivery success.

Acceptance commands:

```bash
test -f sprints/2026.05.22_04-05_verified-terminal-result-material-intake/tech-done.md && test -f sprints/2026.05.22_04-05_verified-terminal-result-material-intake/side2side_check.md && test -f sprints/2026.05.22_04-05_verified-terminal-result-material-intake/final.md
rg -n "verified_terminal_result_material_intake|software_proof_docker_verified_terminal_result_material_intake_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_04-05_verified-terminal-result-material-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_04-05_verified-terminal-result-material-intake
```

## Interface Impact

- Adds one PC evidence CLI and one summary schema.
- Adds one Robot diagnostics/status alias: `robot_diagnostics_verified_terminal_result_material_intake_summary`.
- Adds one mobile/web read-only panel.
- Does not change ROS2 action contracts, launch parameters, hardware configs, serial/UART behavior, cloud command mutation semantics, or mobile primary action authorization.
- Documentation impact is limited to new/updated evidence interface docs, operator gateway diagnostics docs, remote/mobile product docs, and sprint closeout docs.

## Validation Fence

Planning-doc validation for this phase:

```bash
test -f sprints/2026.05.22_04-05_verified-terminal-result-material-intake/pre_start.md && test -f sprints/2026.05.22_04-05_verified-terminal-result-material-intake/prd.md && test -f sprints/2026.05.22_04-05_verified-terminal-result-material-intake/tech-plan.md
rg -n "verified_terminal_result_material_intake|software_proof_docker_verified_terminal_result_material_intake_gate|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.22_04-05_verified-terminal-result-material-intake
git diff --check -- sprints/2026.05.22_04-05_verified-terminal-result-material-intake
```

Implementation owners must run only their scoped fenced commands unless a failure requires targeted diagnosis and rerun. Broad repo-wide tests are not required for this planning phase.

## Worker Dispatch Notes

Launch Task A, Task B, and Task C in parallel. Task D waits until worker evidence is returned. Robot owns schema arbitration if Robot/mobile field names drift. Full-Stack must adapt only within mobile scope. Autonomy owns the source summary contract. Product owns closeout wording and OKR/progress update boundaries.

Each worker must return:

1. actual changed file list.
2. validation command outputs or concise log snippets.
3. failure diagnosis if any.
4. remaining risk.

## Risk Boundary

- If no real terminal result evidence bundle is supplied, the sprint still produces a useful intake gate but must close with no OKR percentage increase.
- If a bundle is supplied but lacks same safe `evidence_ref`, required materials, or safe copy, the correct outcome is blocked / `not_proven`.
- If mobile/web displays the panel successfully, that remains local browser/software proof only and not real phone/browser proof.
- If Robot diagnostics exposes the alias successfully, that remains status/diagnostics proof only and not safe-to-control proof.
- If PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved, Product closeout must say so explicitly.

