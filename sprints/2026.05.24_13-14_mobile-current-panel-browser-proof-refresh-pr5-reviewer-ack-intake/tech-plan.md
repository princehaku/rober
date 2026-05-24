# Tech Plan - Mobile current-panel browser proof refresh PR5 reviewer ACK intake

- sprint_type: epic
- sprint: `2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake`
- target capability: `mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake`
- proof boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate`
- latest panel under proof: `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`
- Product owner: `product-okr-owner`
- implementation owners: `full-stack-software-engineer`, `robot-software-engineer`, `product-okr-owner`
- validation style: fenced, focused, no broad regression, no full Docker build unless a worker proves it is needed

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接针对 Objective 5；本轮针对 Objective 4 的本地 mobile current-panel browser proof refresh。
3. 不直接做 Objective 5 的具体证据理由：最近多轮 O5 local Docker wrappers 均无 OKR lift；当前真实 O5 进展仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof 和 verified terminal result。继续叠 O5 local-only wrapper 不会提高 Objective 5。当前 Docker-only 可执行 fallback 是刷新 O4 `mobile/web` current-panel browser proof，让最新 PR #5 reviewer ACK intake panel 进入本地 fresh-profile browser gate，同时明确 no OKR percentage lift。

## 同一 blocker 红线说明

最近两轮已经连续消费 PR #5 `PRRT_kwDOSWB9286CJ3tX` hardware-material blocker：

- `sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/`：主要结论仍是 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。
- `sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake/`：继续同一 PR #5 thread 的 reviewer ACK intake，最终仍 `is_resolved=false` / `hardware_material_pending`。

根据同一 blocker 最多消费 2 轮红线，本轮必须 pivot，不能第三次继续做 PR #5 material governance wrapper。PR #5 closed/merged 但 thread `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`；Q/U resolved 不等于 X resolved。PR #7 open 但 review threads empty，不能解除 PR #5 material thread。

## 固定边界

本轮输出必须保留以下口径：

```text
mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake
software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate
pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake
PRRT_kwDOSWB9286CJ3tX
hardware_material_pending
delivery_success=false
primary_actions_enabled=false
safe_to_control=false
not true phone/browser proof
not O5 external proof
not HIL
not WAVE ROVER/UART proof
not LiDAR/ToF installed proof
not PR #5 resolved
not delivery success
```

## 并行任务

### Task A - Full-Stack current-panel browser proof refresh

Owner: `full-stack-software-engineer`

Allowed implementation files:

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/test_mobile_web_entrypoint.py`
- necessary `mobile/web/fixtures/*` fixture files for the PR #5 reviewer ACK intake panel
- necessary `docs/product/mobile_user_flow.md` updates

Requirements:

- Add capability `mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake`.
- Use boundary `software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate`.
- Cover latest panel `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`.
- Verify fail-closed behavior: Start Delivery, Confirm Dropoff and Cancel remain disabled; `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` remain visible.
- Verify safe copy and boundary display are present and do not expose raw diagnostics, raw materials, complete artifacts, checksums, credentials, `/cmd_vel`, serial/UART details, WAVE ROVER details, ACK/cursor mutation routes, GitHub mutation, replay/resubmit, material upload or robot command routes.
- Reuse existing browser gate `--capability` / `--evidence-boundary` override if supported instead of creating a duplicate proof script.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json >/tmp/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k current_panel_browser_proof_refresh
python3 pc-tools/evidence/phone_browser_acceptance_gate.py --help
python3 pc-tools/evidence/phone_browser_acceptance_gate.py --capability mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake --evidence-boundary software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate
rg -n "mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake|software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate|pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence mobile docs/product/mobile_user_flow.md
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py mobile/web/fixtures docs/product/mobile_user_flow.md
```

### Task B - Robot safe alias read-only consultation

Owner: `robot-software-engineer`

Allowed consultation files:

- `docs/interfaces/ros_runtime_contracts.md`
- `docs/product/remote_4g_mvp.md`

Requirements:

- Read-only confirm whether existing safe alias `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary` is sufficient for the Full-Stack panel and browser gate.
- Do not edit runtime code unless later implementation evidence proves a contract gap; this planning assumes consultation only.
- If docs need clarification, update only the allowed docs files and keep the alias explicitly read-only.
- Confirm no raw diagnostic, no raw material, no `/cmd_vel`, no serial/UART/WAVE ROVER details, no ACK/cursor mutation, no GitHub mutation, no replay/resubmit, no material upload and no robot command side effect.

Acceptance commands:

```bash
rg -n "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary|pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|/cmd_vel|ACK|cursor|GitHub|replay|resubmit" docs/interfaces/ros_runtime_contracts.md docs/product/remote_4g_mvp.md onboard/src/ros2_trashbot_behavior
git diff --check -- docs/interfaces/ros_runtime_contracts.md docs/product/remote_4g_mvp.md
```

### Task C - Product closeout after implementation validation

Owner: `product-okr-owner`

Allowed closeout files after implementation:

- `sprints/2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake/tech-done.md`
- `sprints/2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake/side2side_check.md`
- `sprints/2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Requirements:

- Verify Task A and Task B outputs and paste concise validation evidence into `tech-done.md`.
- In `side2side_check.md`, compare planned acceptance with actual panel proof, browser gate result, false-state flags and no-claim boundary.
- In `final.md`, state no OKR percentage lift unless real external/hardware evidence appears.
- In `OKR.md` and `docs/process/okr_progress_log.md`, keep Objective 5 about 68%，Objective 1 about 81%，Objective 2/3/4 about 99%，and explain this was local software proof / browser-gate refresh only.

Closeout validation commands:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|同一 blocker|mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake|software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
```

## 接口影响

- Full-Stack gate should add browser-proof coverage only; no new user command route and no backend control behavior.
- Robot consultation should preserve the existing safe alias as read-only metadata; no command side effect.
- Product closeout updates OKR and progress docs only after implementation validation exists.

## 验收围栏

Planning docs creation must pass:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|同一 blocker|mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake|software_proof_docker_mobile_current_panel_browser_proof_refresh_pr5_reviewer_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake
git diff --check -- sprints/2026.05.24_13-14_mobile-current-panel-browser-proof-refresh-pr5-reviewer-ack-intake
```

## 风险和阻塞

- This sprint is local software proof / browser-gate refresh only; not true phone/browser proof.
- `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint must not imply PR #5 resolution.
- Objective 5 remains blocked by missing public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result.
- Objective 1 remains blocked by missing real LiDAR/ToF procurement/install/calibration/HIL and WAVE ROVER powered bench/UART/HIL logs.
- If the fresh-profile browser gate command is not currently supported, Task A must first report the exact CLI gap and then implement the smallest compatible extension under the same boundary.
