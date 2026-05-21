# Verified Terminal Result Material Review Decision Tech Plan

Run time: 2026-05-22 05:06 Asia/Shanghai

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5 的下一步可行动材料路径：`verified_terminal_result_material_review_decision`。
3. 本 sprint 不继续堆本地 O5 metadata。上一轮 `verified_terminal_result_material_intake` 已把 terminal delivery/dropoff/cancel result material 做成可摄取、可校验、可安全展示的 gate；本轮把 intake 输出推进到 review decision 和 owner handoff。
4. 本 sprint 不提升 Objective 5 百分比，除非 field owner 在本轮实施期间提供真实 terminal delivery/dropoff/cancel result evidence bundle，并且 Product closeout 能按同一 safe `evidence_ref` 验证通过。
5. 本 sprint 不推进 Objective 1 completion。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending；comment `3269642220` 只是 software-proof publication；当前 Docker-only 主机不能产生真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF source/procurement/install/calibration 或 reviewer resolution。

## Architecture Decision

`verified_terminal_result_material_review_decision` is a three-surface software-proof gate:

1. PC review-decision CLI reads a prior intake artifact, intake summary, or Robot safe alias and emits a sanitized review-decision summary.
2. Robot diagnostics/status consumes the review-decision summary and exposes a safe alias for support/mobile.
3. Mobile/web renders a read-only panel with safe copy support.

The design deliberately separates "accepted for review" from "delivery succeeded". Every surface must preserve:

- `capability=verified_terminal_result_material_review_decision`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Interface Contract

### Input Sources

Supported input source schemas and aliases:

- `trashbot.verified_terminal_result_material_intake.v1`
- `trashbot.verified_terminal_result_material_intake_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_intake_summary`

Required source fields:

- `capability`
- source `evidence_boundary`
- safe `evidence_ref`
- `terminal_result_type`
- intake/material status summary
- `owner_handoff` when present
- `next_required_evidence` or missing-material summary when present
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Allowed `terminal_result_type` values:

- `delivery`
- `dropoff`
- `cancel`

### Output Summary

Expected summary schema: `trashbot.verified_terminal_result_material_review_decision_summary.v1`.

Required safe fields:

- `schema`
- `capability`
- source intake capability/status
- `review_decision`
- safe `evidence_ref`
- safe `command_id` when present
- `terminal_result_type`
- `decision_reasons`
- `material_status_summary`
- `blocked_reason` or `rejected_reason` when applicable
- `next_required_evidence`
- `owner_handoff`
- `safe_copy`
- `evidence_boundary`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Allowed `review_decision` values:

- `accepted_for_review`
- `needs_material_backfill`
- `rejected`
- `blocked`

Forbidden in safe output:

- raw artifact bodies, complete JSON dumps, raw robot responses, credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, local paths, checksums, tracebacks, raw ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER control details, hardware device paths, reviewer-resolution claims, or success/control claims.

## Parallel Owner Plan

Implementation must launch Task A, Task B, and Task C in parallel via `spawn_agent(agent_type=worker)` because file scopes are distinct. Task D runs after worker evidence returns. Each worker prompt must include the five fixed sections from `AGENTS.md`: role system prompt, task, file scope, acceptance commands, and output requirements.

### Task A - Autonomy Algorithm Engineer

Role: `autonomy-engineer`

Goal: add the PC review-decision CLI and tests for `verified_terminal_result_material_review_decision`.

Allowed files:

- `pc-tools/evidence/verified_terminal_result_material_review_decision.py`
- `tests/test_verified_terminal_result_material_review_decision.py`
- `docs/interfaces/verified_terminal_result_material_review_decision.md`
- `pc-tools/README.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/tech-done.md`

Interface requirements:

- Read one prior intake artifact, intake summary, or Robot safe alias from `--input`.
- Write sanitized review-decision summary artifact to `--output-dir`.
- Validate same safe `evidence_ref` across source fields and nested safe summaries when present.
- Validate `terminal_result_type` is `delivery`, `dropoff`, or `cancel`.
- Emit exactly one decision: `accepted_for_review`, `needs_material_backfill`, `rejected`, or `blocked`.
- Require `owner_handoff` and `next_required_evidence` in safe output.
- Reject raw artifacts, unsafe fields, local paths, credentials, ROS/control details, hardware details, reviewer-resolution claims, and success/control overclaims.
- Emit `software_proof_docker_verified_terminal_result_material_review_decision_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- All new technical code comments must be meaningful Chinese comments.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/verified_terminal_result_material_review_decision.py tests/test_verified_terminal_result_material_review_decision.py
python3 -m unittest tests.test_verified_terminal_result_material_review_decision
python3 pc-tools/evidence/verified_terminal_result_material_review_decision.py --help
rg -n "verified_terminal_result_material_review_decision|software_proof_docker_verified_terminal_result_material_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|accepted_for_review|needs_material_backfill|rejected|blocked|evidence_ref" pc-tools/evidence/verified_terminal_result_material_review_decision.py tests/test_verified_terminal_result_material_review_decision.py docs/interfaces/verified_terminal_result_material_review_decision.md pc-tools/README.md sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
git diff --check -- pc-tools/evidence/verified_terminal_result_material_review_decision.py tests/test_verified_terminal_result_material_review_decision.py docs/interfaces/verified_terminal_result_material_review_decision.md pc-tools/README.md sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
```

### Task B - Robot Platform Engineer

Role: `robot-software-engineer`

Goal: expose a Robot diagnostics/status safe alias for the review-decision summary while keeping all controls disabled.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/tech-done.md`

Interface requirements:

- Consume `verified_terminal_result_material_review_decision`, `verified_terminal_result_material_review_decision_summary`, or compatible nested diagnostics/status summary.
- Expose `robot_diagnostics_verified_terminal_result_material_review_decision_summary`.
- Preserve summary schema `trashbot.verified_terminal_result_material_review_decision_summary.v1`.
- Force fail-closed values in the exposed summary: `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Do not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, or robot control.
- Strip or block unsafe raw fields before diagnostics output.
- All new technical code comments must be meaningful Chinese comments.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "verified_terminal_result_material_review_decision|robot_diagnostics_verified_terminal_result_material_review_decision_summary|software_proof_docker_verified_terminal_result_material_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
```

### Task C - User Touchpoint Full-Stack Engineer

Role: `full-stack-software-engineer`

Goal: add a mobile/web read-only terminal-result material review-decision panel with safe copy support.

Allowed files:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_review_decision.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/tech-done.md`

Interface requirements:

- Consume `robot_diagnostics_verified_terminal_result_material_review_decision_summary`, `verified_terminal_result_material_review_decision_summary`, or compatible nested diagnostics/status summary.
- Render only review decision, source intake status, terminal result type, safe `evidence_ref`, safe `command_id`, decision reasons, material status summary, blocked/rejected reason, next required evidence, owner handoff, evidence boundary, and safe copy.
- Copy button is enabled only when backend-provided `safe_copy` is present and contains no unsafe raw fields.
- Missing or unsafe summary renders blocked / `not_proven`.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- The panel must not fetch raw diagnostics, raw artifacts, ACK routes, cursor routes, command routes, review routes, or replay/resubmit any request.
- All new technical code comments must be meaningful Chinese comments.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_review_decision.json >/tmp/robot_diagnostics_verified_terminal_result_material_review_decision.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "verified_terminal_result_material_review_decision|software_proof_docker_verified_terminal_result_material_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|review decision|evidence_ref" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
```

### Task D - Product Manager / OKR Owner Closeout

Role: `product-okr-owner`

Goal: integrate worker evidence, update sprint closeout, and update OKR/progress only with conservative proof language.

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/tech-done.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/side2side_check.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/final.md`

Closeout requirements:

- Keep Objective 5 around 68% unless real terminal delivery/dropoff/cancel result materials are supplied and verified during the sprint.
- Keep Objective 1 around 81% unless PR #5 `PRRT_kwDOSWB9286CJ3tX` receives real material and live reviewer resolution; comment `3269642220` alone is not enough.
- Keep Objective 2/3/4 around 99% unless real route/elevator/Nav2/fixed-route/phone materials are supplied and verified.
- Record this sprint as `software_proof_docker_verified_terminal_result_material_review_decision_gate`.
- Explicitly state `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Confirm docs synchronization for every implementation owner.
- Confirm no implementation owner treated `accepted_for_review` as delivery success.

Acceptance commands:

```bash
test -f sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/tech-done.md && test -f sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/side2side_check.md && test -f sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/final.md
rg -n "verified_terminal_result_material_review_decision|software_proof_docker_verified_terminal_result_material_review_decision_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|3269642220|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
```

## Interface Impact

- Adds one PC evidence review-decision CLI and one summary schema.
- Adds one Robot diagnostics/status alias: `robot_diagnostics_verified_terminal_result_material_review_decision_summary`.
- Adds one mobile/web read-only panel.
- Does not change ROS2 action contracts, launch parameters, hardware configs, serial/UART behavior, cloud command mutation semantics, or mobile primary action authorization.
- Documentation impact is limited to new/updated evidence interface docs, operator gateway diagnostics docs, remote/mobile product docs, and sprint closeout docs.

## Validation Fence

Planning-doc validation for this phase:

```bash
test -f sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/pre_start.md && test -f sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/prd.md && test -f sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/tech-plan.md
rg -n "sprint_type: epic|verified_terminal_result_material_review_decision|software_proof_docker_verified_terminal_result_material_review_decision_gate|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
git diff --check -- sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision
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

- If no real terminal result evidence bundle is supplied, the sprint still produces a useful review-decision gate but must close with no OKR percentage increase.
- If the prior intake output lacks same safe `evidence_ref`, required materials, or safe copy, the correct outcome is `needs_material_backfill`, `rejected`, or `blocked`, not success.
- If mobile/web displays the panel successfully, that remains local browser/software proof only and not real phone/browser proof.
- If Robot diagnostics exposes the alias successfully, that remains status/diagnostics proof only and not safe-to-control proof.
- If PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved, Product closeout must say so explicitly.
