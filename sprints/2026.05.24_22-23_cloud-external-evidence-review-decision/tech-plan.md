# Tech Plan - Cloud external evidence review decision

- sprint_type: epic
- sprint: `2026.05.24_22-23_cloud-external-evidence-review-decision`
- target capability: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_decision_gate`
- source capability: `trashbot.external_evidence_intake`
- Product owner: `product-okr-owner`
- implementation owners: `full-stack-software-engineer`, `robot-software-engineer`
- validation style: focused fences only; no broad regression; no Docker build unless an Engineer proves it is necessary

## OKR 最低优先级核对

1. 当前 `OKR.md` §4.1 里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 针对 Objective 5，但不声明 OKR 百分比提升。
3. 选择 Objective 5 的理由：最新 `final.md` 明确要求下一步需要 real external evidence，而不是 another local-only wrapper。本轮不继续 owner-response support wrapper；改做 `cloud_external_evidence_review_decision`，把既有 `trashbot.external_evidence_intake` 变成可复核、可拒绝、可要求 backfill 的软件能力，后续真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 材料出现时能进入同一 review decision 流程。
4. 不提升 OKR 的理由：本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser proof、verified terminal result、HIL、WAVE ROVER/UART proof、PR #5 resolution、route/elevator field pass 或 delivery success。因此本 sprint 只能是 `software_proof` / `not_proven` / `no OKR percentage lift`。

## Evidence Inputs Used For Planning

- `OKR.md` §4.1 更新时间 2026-05-24 21:22，Objective 5 约 68% 仍最低；Objective 1 约 81%；Objective 2/3/4 约 99%。
- `sprints/2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge/final.md` says the last sprint was O4 local Chromium proof refresh, not O5 lift.
- PR #5 is merged/closed, but thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved/not outdated with latest reply `hardware_material_pending`.
- PR #7 is open with no review threads/comments.
- Host is Docker-only and has no real hardware.

## Interface Impact

The intended interface is additive and read-only:

- Input: existing `trashbot.external_evidence_intake` safe artifact or diagnostics summary.
- New safe summary: `robot_diagnostics_cloud_external_evidence_review_decision_summary`.
- Expected schema: `trashbot.cloud_external_evidence_review_decision_summary.v1`.
- Evidence boundary: `software_proof_docker_cloud_external_evidence_review_decision_gate`.
- Mobile panel: read-only `cloud_external_evidence_review_decision` panel.

No endpoint may add robot motion, ACK/cursor mutation, GitHub mutation, material upload, replay/resubmit, raw artifact fetch, raw diagnostics fetch, owner-response submission, review mutation, handoff mutation, or command side effects.

## Owner/File Split

### Task A - Full-Stack cloud evidence review-decision and mobile surface

Owner: `full-stack-software-engineer`

Allowed files:

- `pc-tools/evidence/cloud_external_evidence_review_decision.py`
- `pc-tools/evidence/test_cloud_external_evidence_review_decision.py`
- `pc-tools/evidence/fixtures/cloud_external_evidence_review_decision/*`
- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_decision.json`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`
- `cloud-relay/README.md`

Requirements:

- Build the local review-decision gate for existing `trashbot.external_evidence_intake` output.
- Emit only redacted safe fields and deterministic states:
  - `accepted_external_evidence_not_proven`
  - `needs_external_evidence_backfill_not_proven`
  - `rejected_unsafe_external_evidence_not_proven`
  - `blocked_missing_external_evidence_intake_not_proven`
  - `external_evidence_ref_mismatch_not_proven`
- Add a mobile read-only panel that shows safe command/evidence refs, material-family statuses, review decision, next required evidence, `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.
- The panel must keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not expose URLs, credential-bearing endpoints, Authorization headers, bearer tokens, OSS AK/SK, DB/queue URLs, local paths, response bodies, tracebacks, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER, hardware details, full artifact content, checksums, GitHub mutation, or raw PR payloads.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/cloud_external_evidence_review_decision.py
python3 -m unittest pc-tools/evidence/test_cloud_external_evidence_review_decision.py
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_decision.json >/tmp/cloud_external_evidence_review_decision_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_external_evidence_review_decision
rg -n "cloud_external_evidence_review_decision|software_proof_docker_cloud_external_evidence_review_decision_gate|trashbot.external_evidence_intake|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" pc-tools/evidence mobile/web docs/product cloud-relay/README.md
git diff --check -- pc-tools/evidence/cloud_external_evidence_review_decision.py pc-tools/evidence/test_cloud_external_evidence_review_decision.py pc-tools/evidence/fixtures/cloud_external_evidence_review_decision mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_decision.json docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md cloud-relay/README.md
```

### Task B - Robot diagnostics safe alias

Owner: `robot-software-engineer`

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

Requirements:

- Add `robot_diagnostics_cloud_external_evidence_review_decision_summary` as a safe read-only diagnostics alias.
- Consume only safe review-decision fields from Task A.
- Preserve `software_proof`, `not_proven`, `production_ready=false`, `overall_status=blocked`, `external_evidence_complete=false`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.
- Reject or omit raw artifacts and unsafe fields.
- Keep PR #5 `PRRT_kwDOSWB9286CJ3tX` / `hardware_material_pending` as context only; do not imply PR #5 resolution.

Acceptance commands:

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k cloud_external_evidence_review_decision
rg -n "robot_diagnostics_cloud_external_evidence_review_decision_summary|cloud_external_evidence_review_decision|software_proof_docker_cloud_external_evidence_review_decision_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift|/cmd_vel|serial|UART|WAVE ROVER" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Task C - Product closeout after Engineer validation

Owner: `product-okr-owner`

Allowed files after implementation:

- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/tech-done.md`
- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/side2side_check.md`
- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Requirements:

- Verify Task A and Task B evidence before closeout.
- Record actual validation outputs and any failures in `tech-done.md`.
- In `side2side_check.md`, compare planned acceptance criteria against actual safe summary and mobile panel behavior.
- In `final.md`, state whether there is real external evidence. Default expected result on this host is `no OKR percentage lift`.
- Update `OKR.md` and `docs/process/okr_progress_log.md` only after implementation evidence exists.

Closeout validation commands:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|cloud_external_evidence_review_decision|software_proof_docker_cloud_external_evidence_review_decision_gate|trashbot.external_evidence_intake|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|Docker|software_proof|not true phone/browser|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_22-23_cloud-external-evidence-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_22-23_cloud-external-evidence-review-decision OKR.md docs/process/okr_progress_log.md
```

## Parallel Dispatch Plan

Implementation should start with Task A and Task B in parallel because their file ranges do not overlap. Product closeout Task C must wait until both Engineer tasks return validation evidence.

The two Engineer prompts must include:

- Full role system prompt from `.codex/agents/full-stack-software-engineer.toml` or `.codex/agents/robot-software-engineer.toml`.
- This sprint's target capability and proof boundary.
- The exact file scope above.
- The acceptance commands above.
- Output requirements: changed files, validation log snippets, failure diagnosis, remaining risk.

## Risk Boundary

- This sprint is `software_proof` only.
- It is Docker/local proof only.
- It is not true phone/browser proof.
- It is not O5 external proof.
- It is not public HTTPS/TLS proof.
- It is not 4G/SIM proof.
- It is not OSS/CDN live traffic.
- It is not production DB/queue proof.
- It is not worker/cutover proof.
- It is not verified terminal result.
- It is not HIL, WAVE ROVER/UART proof, LiDAR/ToF installed proof, PR #5 resolution, route/elevator field pass, delivery result, or delivery success.
- It carries `no OKR percentage lift` unless real external materials appear and are accepted under the review decision.

## Planning Validation Commands

```bash
test -f sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/pre_start.md && test -f sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/prd.md && test -f sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|Docker|software_proof|not true phone/browser|no OKR percentage lift" sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/pre_start.md sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/prd.md sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/tech-plan.md
git diff --check -- sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/pre_start.md sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/prd.md sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/tech-plan.md
```
