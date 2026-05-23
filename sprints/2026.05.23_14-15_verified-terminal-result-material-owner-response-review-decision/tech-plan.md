# Verified Terminal Result Material Owner Response Review Decision Tech Plan

Run time: 2026-05-23 14:15 Asia/Shanghai

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，目标能力为 `verified_terminal_result_material_owner_response_review_decision`。
3. 本 sprint 承接上一轮 `verified_terminal_result_material_owner_response_intake`，把 owner response intake safe metadata 转成 owner-response review-decision metadata。
4. 当前仍无真实外部材料、真实 terminal delivery/dropoff/cancel result、真实手机/browser、真实 4G/SIM、真实 OSS/CDN live traffic、真实 production DB/queue、真实 WAVE ROVER/UART/HIL 或真实 2D LiDAR/ToF 材料，所以本轮不提升百分比，只补 support-safe review decision rung。
5. 本 sprint 是 Docker/local `software_proof`，默认 `no OKR percentage lift`。只有真实 terminal delivery/dropoff/cancel result material 或真实 O5 external evidence 到位、同一 safe `evidence_ref` 且后续 review 通过，才可能在未来调整 Objective 5。
6. PR #5 live review evidence 不能写成已解决：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`。

## Architecture Decision

`verified_terminal_result_material_owner_response_review_decision` is a three-surface safe review-decision:

1. PC-only gate reads prior owner response intake metadata and emits owner-response review-decision classification.
2. Robot diagnostics/status exposes a safe alias for the owner-response review-decision summary.
3. Mobile/web renders a read-only owner-response review-decision panel for field owner/support/reviewer visibility.

Every surface must preserve:

- `capability=verified_terminal_result_material_owner_response_review_decision`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate`
- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`

## Interface Contract

Supported input source schemas and aliases:

- `trashbot.verified_terminal_result_material_owner_response_intake.v1`
- `trashbot.verified_terminal_result_material_owner_response_intake_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary.v1`
- compatible nested diagnostics/status summaries that preserve the same safe `evidence_ref`

Expected output schemas:

- Artifact: `trashbot.verified_terminal_result_material_owner_response_review_decision.v1`
- Summary: `trashbot.verified_terminal_result_material_owner_response_review_decision_summary.v1`
- Robot alias: `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary.v1`

Required statuses:

- `accepted_terminal_result_material_owner_response_review_decision_not_proven`
- `missing_terminal_result_material_owner_response_review_decision_not_proven`
- `rejected_terminal_result_material_owner_response_review_decision_not_proven`
- `unsafe_terminal_result_material_owner_response_review_decision_not_proven`
- `blocked_missing_terminal_result_owner_response_intake_not_proven`
- `blocked_evidence_ref_mismatch_not_proven`

Required safe output fields:

- `schema`
- `capability`
- `source_schema`
- `source=software_proof`
- safe `evidence_ref`
- safe `command_id` when present
- `terminal_result_type`
- `source_owner_response_status`
- `review_decision`
- `decision_reasons`
- `field_owner`
- `support_owner`
- `reviewer_route`
- `accepted_materials`
- `missing_materials`
- `rejected_materials`
- `unsafe_materials`
- `blocked_reason` when applicable
- `next_required_evidence`
- `safe_copy`
- `evidence_boundary`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`

Forbidden in safe output:

- raw artifact bodies, complete JSON dumps, raw owner response bodies, raw review packets, raw terminal material, credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, local paths, checksums, tracebacks, raw ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER control details, hardware device paths, ACK/cursor mutation hints, replay/resubmit hints, reviewer-resolution claims, success claims, or control claims.

Forbidden claims in implementation, docs, tests, and closeout:

- real terminal delivery/dropoff/cancel result
- O5 external proof
- true phone/browser proof
- public HTTPS/TLS
- 4G/SIM
- OSS/CDN live traffic
- production DB/queue
- worker/cutover
- route/elevator field pass
- Nav2/fixed-route runtime pass
- HIL
- WAVE ROVER/UART proof
- real 2D LiDAR/ToF installed proof
- PR #5 resolution
- delivery success

## Parallel Engineer Plan

Launch Task A, Task B, and Task C in parallel via `spawn_agent(agent_type=worker)` because file scopes are distinct and do not overlap. Each worker must use the role prompt from `.codex/agents/<role>.toml`, must not revert other work, and must return changed files, validation output, failure localization, and residual risks.

Task D is Product closeout and must run only after A/B/C return with passing or explicitly bounded validation evidence.

### Task A - Autonomy Algorithm Engineer

Goal: add the PC-only owner-response review-decision gate, tests, interface docs, and README entry for `verified_terminal_result_material_owner_response_review_decision`.

Allowed files:

- `pc-tools/evidence/verified_terminal_result_material_owner_response_review_decision.py`
- `tests/test_verified_terminal_result_material_owner_response_review_decision.py`
- `docs/interfaces/verified_terminal_result_material_owner_response_review_decision.md`
- `pc-tools/README.md`

Interface impact:

- Adds a file-only PC gate that consumes owner response intake safe metadata.
- Emits artifact and summary schemas `trashbot.verified_terminal_result_material_owner_response_review_decision.v1` and `trashbot.verified_terminal_result_material_owner_response_review_decision_summary.v1`.
- Must reject missing intake, mismatched `evidence_ref`, unsafe fields, raw material, and success/control wording.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/verified_terminal_result_material_owner_response_review_decision.py tests/test_verified_terminal_result_material_owner_response_review_decision.py
python3 -m unittest tests.test_verified_terminal_result_material_owner_response_review_decision
python3 pc-tools/evidence/verified_terminal_result_material_owner_response_review_decision.py --help
rg -n "verified_terminal_result_material_owner_response_review_decision|software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|accepted_terminal_result_material_owner_response_review_decision_not_proven|missing_terminal_result_material_owner_response_review_decision_not_proven|rejected_terminal_result_material_owner_response_review_decision_not_proven|unsafe_terminal_result_material_owner_response_review_decision_not_proven|blocked_missing_terminal_result_owner_response_intake_not_proven|blocked_evidence_ref_mismatch_not_proven|evidence_ref" pc-tools/evidence/verified_terminal_result_material_owner_response_review_decision.py tests/test_verified_terminal_result_material_owner_response_review_decision.py docs/interfaces/verified_terminal_result_material_owner_response_review_decision.md pc-tools/README.md sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
git diff --check -- pc-tools/evidence/verified_terminal_result_material_owner_response_review_decision.py tests/test_verified_terminal_result_material_owner_response_review_decision.py docs/interfaces/verified_terminal_result_material_owner_response_review_decision.md pc-tools/README.md sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
```

### Task B - Robot Platform Engineer

Goal: expose an `operator_gateway_diagnostics` safe alias and tests for `robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary`.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`

Interface impact:

- Adds Robot diagnostics/status consumption for the owner-response review-decision summary.
- Exposes `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary.v1`.
- Must keep `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` even when owner response material is accepted for later handoff.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "verified_terminal_result_material_owner_response_review_decision|robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary|software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
```

### Task C - User Touchpoint Full-Stack Engineer

Goal: add a `mobile/web` read-only owner-response review-decision panel, fixture, tests, and product docs.

Allowed files:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_review_decision.json`
- `docs/product/mobile_user_flow.md`

Interface impact:

- Adds read-only panel consumption of `robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary`.
- Shows only safe review decision, safe `evidence_ref`, decision reasons, accepted/missing/rejected/unsafe material classifications, next required evidence, backend `safe_copy`, and proof flags.
- Must not enable Start Delivery, Confirm Dropoff, Cancel, diagnostics fetches for raw material, ACK/cursor actions, review routes, handoff routes, replay/resubmit, or any control path.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_review_decision.json >/tmp/robot_diagnostics_verified_terminal_result_material_owner_response_review_decision.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "verified_terminal_result_material_owner_response_review_decision|robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary|software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|owner response review decision|evidence_ref" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
```

### Task D - Product Manager / OKR Owner Closeout

Goal: after A/B/C return, integrate worker evidence and update sprint closeout and OKR/progress records with conservative proof language.

Allowed files:

- `sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/tech-done.md`
- `sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/side2side_check.md`
- `sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Interface impact:

- No runtime interface changes. Product closeout only records evidence returned by A/B/C.
- Must preserve `no OKR percentage lift` unless real external or terminal-result material is introduced and reviewed outside the Docker/local proof boundary.
- Must state that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless live review evidence changes before closeout.

Acceptance commands:

```bash
test -f sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/tech-done.md
test -f sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/side2side_check.md
test -f sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/final.md
rg -n "verified_terminal_result_material_owner_response_review_decision|software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" OKR.md docs/process/okr_progress_log.md sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
```

## Validation Fence For Planning

```bash
test -f sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/pre_start.md
test -f sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/prd.md
test -f sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/tech-plan.md
rg -n "sprint_type: epic|verified_terminal_result_material_owner_response_review_decision|OKR 最低优先级核对|Objective 5|software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate|PRRT_kwDOSWB9286CJ3tX|no OKR percentage lift" sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
git diff --check -- sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision
```

Implementation owners must run only scoped fenced commands unless a failure requires targeted diagnosis and rerun. Broad builds and hardware smokes are out of scope for this planning sprint because the current host is Docker/local only and this plan does not touch WAVE ROVER, UART, launch hardware parameters, or HIL paths.
