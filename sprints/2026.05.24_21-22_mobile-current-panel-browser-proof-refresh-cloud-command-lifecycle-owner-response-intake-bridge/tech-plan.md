# Tech Plan - Mobile current-panel browser proof refresh cloud command lifecycle owner-response intake bridge

- sprint_type: epic
- sprint: `2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge`
- target capability: `mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge`
- proof boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate`
- latest panel under proof: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`
- Product owner: `product-okr-owner`
- implementation owners: `full-stack-software-engineer`, `robot-software-engineer`, `product-okr-owner`
- validation style: fenced, focused, no broad regression, no full Docker build unless a worker proves it is needed

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接针对 Objective 5；本轮针对 Objective 4 的本地 `mobile/web` current-panel browser proof refresh。
3. 不直接做 Objective 5 的具体证据理由：最新 final 明确写明 `do not add another local-only wrapper as OKR lift`。上一轮 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge` 已经只是 Docker/local support-continuity bridge，且 no OKR percentage lift。当前真实 O5 进展仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof 和 verified terminal result。继续叠 O5 local-only wrapper 不会提高 Objective 5；本轮选择 O4 fallback，只刷新 `mobile/web` current-panel browser proof，让最新 bridge panel 在本地 fresh-profile browser gate 中保持 fail closed、console clean 和边界清晰。

## 同一 blocker/redline 说明

最新 closeout 已把 O5 local-only wrapper 的红线说清楚：`do not add another local-only wrapper as OKR lift`。本轮不是第三次扩展同一 O5 metadata wrapper，而是 pivot 到 O4 current-panel browser proof refresh。该 pivot 的理由是：没有真实 O5 external materials 时，Docker-only 主机能提供的新增价值是用户触点回归防护，而不是 O5 百分比提升。

必须保留的 live evidence：

- PR #5 closed/merged，但 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`。
- PR #7 open 但没有 review threads；不能解除 PR #5 material thread。
- 本机无真实硬件，只有 Docker/local；不能声明 HIL、WAVE ROVER/UART、true phone/browser、O5 external proof、delivery success。
- 上一轮 bridge capability `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge` 只证明 safe summary 和 read-only mobile panel support continuity。

## 固定边界

本轮输出必须保留以下口径：

```text
mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge
software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge
PRRT_kwDOSWB9286CJ3tX
hardware_material_pending
delivery_success=false
primary_actions_enabled=false
safe_to_control=false
not true phone/browser proof
not O5 external proof
not verified terminal result
not public HTTPS/TLS
not 4G/SIM
not OSS/CDN live traffic
not production DB/queue
not HIL
not WAVE ROVER/UART proof
not PR #5 resolved
not delivery success
```

## 并行任务

### Task A - Full-Stack current-panel browser proof refresh

Owner: `full-stack-software-engineer`

Allowed implementation files:

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/web/test_mobile_web_entrypoint.py`
- necessary `mobile/web/fixtures/*` fixture files for the cloud command lifecycle owner-response intake bridge panel
- necessary `docs/product/mobile_user_flow.md` updates

Requirements:

- Add capability `mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge`.
- Use boundary `software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate`.
- Cover latest panel `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`.
- Verify fail-closed behavior: Start Delivery, Confirm Dropoff and Cancel remain disabled; `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` remain visible.
- Verify safe copy and boundary display are present and do not expose raw diagnostics, raw materials, complete artifacts, checksums, credentials, `/cmd_vel`, serial/UART details, WAVE ROVER details, ACK/cursor mutation routes, GitHub mutation, replay/resubmit, material upload or robot command routes.
- Reuse existing browser gate `--capability` / `--evidence-boundary` override if supported instead of creating a duplicate proof script.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge.json >/tmp/cloud_command_lifecycle_owner_response_intake_bridge_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k current_panel_browser_proof_refresh
python3 pc-tools/evidence/phone_browser_acceptance_gate.py --help
python3 pc-tools/evidence/phone_browser_acceptance_gate.py --capability mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge --evidence-boundary software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate
rg -n "mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge|software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence mobile docs/product/mobile_user_flow.md
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures docs/product/mobile_user_flow.md
```

### Task B - Robot/API safe alias read-only consultation

Owner: `robot-software-engineer`

Allowed consultation files:

- `docs/interfaces/ros_runtime_contracts.md`
- `docs/product/remote_4g_mvp.md`

Requirements:

- Read-only confirm whether existing safe alias for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge` is sufficient for the Full-Stack panel and browser gate.
- Do not edit runtime code unless later implementation evidence proves a contract gap; this planning assumes consultation only.
- If docs need clarification, update only the allowed docs files and keep the alias explicitly read-only.
- Confirm no raw diagnostic, no raw material, no `/cmd_vel`, no serial/UART/WAVE ROVER details, no ACK/cursor mutation, no GitHub mutation, no replay/resubmit, no material upload and no robot command side effect.

Acceptance commands:

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|/cmd_vel|ACK|cursor|GitHub|replay|resubmit" docs/interfaces/ros_runtime_contracts.md docs/product/remote_4g_mvp.md onboard/src/ros2_trashbot_behavior
git diff --check -- docs/interfaces/ros_runtime_contracts.md docs/product/remote_4g_mvp.md
```

### Task C - Product closeout after implementation validation

Owner: `product-okr-owner`

Allowed closeout files after implementation:

- `sprints/2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge/tech-done.md`
- `sprints/2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge/side2side_check.md`
- `sprints/2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Requirements:

- Verify Task A and Task B outputs and paste concise validation evidence into `tech-done.md`.
- In `side2side_check.md`, compare planned acceptance with actual panel proof, browser gate result, false-state flags and no-claim boundary.
- In `final.md`, state no OKR percentage lift unless real external/hardware evidence appears.
- In `OKR.md` and `docs/process/okr_progress_log.md`, keep Objective 5 about 68%, Objective 1 about 81%, Objective 2/3/4 about 99%, and explain this was local software proof / browser-gate refresh only.

Closeout validation commands:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|do not add another local-only wrapper|mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge|software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge OKR.md docs/process/okr_progress_log.md
```

## 接口影响

- Full-Stack gate should add browser-proof coverage only; no new user command route and no backend control behavior.
- Robot/API consultation should preserve the existing safe alias as read-only metadata; no command side effect.
- Product closeout updates OKR and progress docs only after implementation validation exists.

## 验收围栏

Planning docs creation must pass:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|do not add another local-only wrapper|mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge|software_proof_docker_mobile_current_panel_browser_proof_refresh_cloud_command_lifecycle_owner_response_intake_bridge_gate|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge
git diff --check -- sprints/2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge
```

## 风险和阻塞

- This sprint is local software proof / browser-gate refresh only; not true phone/browser proof.
- `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint must not imply PR #5 resolution.
- Objective 5 remains blocked by missing public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result.
- Objective 1 remains blocked by missing real LiDAR/ToF procurement/install/calibration/HIL and WAVE ROVER powered bench/UART/HIL logs.
- If the fresh-profile browser gate command is not currently supported for this panel, Task A must first report the exact CLI gap and then implement the smallest compatible extension under the same boundary.
