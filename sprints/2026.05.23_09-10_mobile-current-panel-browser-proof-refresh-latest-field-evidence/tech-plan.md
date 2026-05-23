# Mobile Current Panel Browser Proof Refresh Latest Field Evidence Tech Plan

Run time: 2026-05-23 09:07 Asia/Shanghai

## Goal And Boundary

Capability: `mobile_current_panel_browser_proof_refresh_latest_field_evidence`

Evidence boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate`

This Epic sprint refreshes the local current-panel browser proof so it covers the latest `mobile/web` read-only panel:

- `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake`

Required blocked-state proof terms:

- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `not true phone/browser`

No ROS2 API, cloud API, Robot command API, hardware configuration, launch parameter, vendor material, or hardware setting should be changed in this sprint unless a later CEO instruction changes scope. This sprint is local Docker/browser software proof only.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否，主目标是 Objective 4 的 `mobile/web` current-panel browser proof refresh latest field evidence。
- 不直接针对 Objective 5 的具体理由：当前 Docker-only host 没有 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal delivery/dropoff/cancel result。继续堆本地 O5 metadata depth 不能形成新的 O5 completion evidence，也不能提升 O5 百分比。
- Objective 1 当前约 81%，但本 sprint 不碰硬件、不声明 PR #5 resolution。PR #5 live review threads：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`。
- final.md 收口规则：若本轮没有真实外部/手机/硬件/现场材料，Product closeout 必须保持 no OKR percentage lift，并继续写明 `not true phone/browser`。

## Work Split

### Task A Full-Stack: Current Panel Browser Proof Refresh Latest Field Evidence

Owner: `full-stack-software-engineer`

Allowed files:

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence/`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md`

Task detail:

- Extend the current-panel browser proof to cover `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake`.
- Run the fresh-profile browser gate and write evidence under this sprint `evidence/` directory.
- Confirm the gate checks the latest panel, proof boundary, no console errors, and disabled primary actions.
- Update `docs/product/mobile_user_flow.md` so the latest field-evidence reviewer ACK intake panel is documented as read-only, phone-safe, and fail-closed.
- Preserve Chinese technical comments if implementation code is touched; any new technical comment must explain why fail-closed behavior or safe-summary filtering exists.
- Do not enable Start Delivery, Confirm Dropoff, or Cancel in blocked/not_proven fixture states.

Validation commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/evidence --fresh-profile --require-console-zero --capability mobile_current_panel_browser_proof_refresh_latest_field_evidence --evidence-boundary software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
rg -n "mobile_current_panel_browser_proof_refresh_latest_field_evidence|software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser" pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/test_mobile_web_entrypoint.py mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/test_mobile_web_entrypoint.py mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence
```

### Task B Robot: Phone-Safe Diagnostics Summary Consultation

Owner: `robot-software-engineer`

Allowed files:

- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md`

Read-only scope:

- Robot diagnostics summary consumers/producers referenced by the latest current panel.
- `mobile/web` and fixture surfaces needed to confirm safe summary consumption.
- Related docs that define phone-safe diagnostics summaries.

Task detail:

- Check whether the current panel consumes a Robot diagnostics summary that is phone-safe.
- Confirm it does not expose raw ROS topics, `/cmd_vel`, raw control payloads, hardware parameters, WAVE ROVER/UART details, credentials, secret values, local filesystem paths, tracebacks, checksums, or complete artifacts.
- Confirm `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` stay semantically aligned with Robot safe summary fields.
- This task is read-only consultation unless it writes its evidence into this sprint `tech-done.md`.

Validation commands:

```bash
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate|not true phone/browser" sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence mobile/web mobile/fixtures mobile/web/fixtures onboard/src/ros2_trashbot_behavior
git diff --check -- sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence
```

### Task C Product Closeout

Owner: `product-okr-owner`

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/side2side_check.md`
- `sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/final.md`

Task detail:

- Accept or reject Task A and Task B evidence against this plan.
- If browser proof passes but no true external/phone/material evidence appears, keep Objective 5 about 68%, Objective 1 about 81%, and Objective 2 / Objective 3 / Objective 4 about 99%.
- Record that this sprint is `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate` only.
- State no OKR percentage lift unless real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, real hardware, field material, verified terminal delivery/dropoff/cancel result, or equivalent real evidence appears.
- Preserve PR #5 evidence boundary: `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending` unless reviewer actually resolves it.

Validation commands:

```bash
test -f sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-done.md && test -f sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/side2side_check.md && test -f sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/final.md
rg -n "mobile_current_panel_browser_proof_refresh_latest_field_evidence|software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser|no OKR percentage lift" sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence
```

## Planning Task Acceptance

This planning task is accepted when these commands pass:

```bash
test -f sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/pre_start.md && test -f sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/prd.md && test -f sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|mobile_current_panel_browser_proof_refresh_latest_field_evidence|software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser" sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence
git diff --check -- sprints/2026.05.23_09-10_mobile-current-panel-browser-proof-refresh-latest-field-evidence
```

## Risk Boundary

- This planning task creates only the first three Epic documents; it does not create `tech-done.md`, `side2side_check.md`, or `final.md`.
- Local Chromium-family proof is still software proof only; it is not true phone/browser, not real iPhone/Android behavior, not production app proof, and not real PWA prompt/userChoice.
- It is not Objective 5 external proof: not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, and not verified terminal result.
- It is not Objective 1 hardware proof: not WAVE ROVER/UART/HIL, not `/odom`、`/imu/data`、`/battery` real feedback, not 2D LiDAR/ToF material, and not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
- It is not Objective 2 / Objective 3 field proof: not real route/elevator field pass, not Nav2/fixed-route runtime, not dropoff/cancel completion, not delivery result, and not delivery success.

