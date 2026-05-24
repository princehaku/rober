# Tech Plan - PR5 mandatory sensor material owner-response reviewer ACK intake

- sprint_type: epic
- sprint: `2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake`
- target capability: `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`
- proof boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate`
- Product owner: `product-okr-owner`
- implementation owners: `hardware-engineer`, `robot-software-engineer`, `full-stack-software-engineer`
- validation style: fenced, focused, no full Docker build

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对 Objective 5 的具体理由：O5 当前真实外部材料缺失，仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof 和 verified terminal result；最近多轮 O5 local Docker proof / local wrappers 都没有 OKR lift。继续叠 O5 local-only wrapper 不会提高 OKR 百分比。本轮选择 Objective 1 PR #5 reviewer evidence chain 的下一条可执行 governance rung：`pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`，并明确 no OKR percentage lift。

## 证据输入和固定边界

本轮必须从以下事实出发：

- `OKR.md`：Objective 5 最低约 68%，Objective 1 约 81%，Objective 4 约 99%。
- 最新 final/tech-done：上一轮已完成 `pr5_mandatory_sensor_material_owner_response_review_handoff`，boundary 是 `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`。
- PR #5：closed/merged；`PRRT_kwDOSWB9286CJ3tQ` resolved；`PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`。
- PR #7：open，review threads empty；不能解除 PR #5 `PRRT_kwDOSWB9286CJ3tX`。
- automation memory：上一轮 commit `81dfeb1` 已完成 owner-response review handoff，并保留 `source=software_proof`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

本轮 proof boundary 固定为：

```text
software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate
```

所有 worker 输出必须保留：

```text
source=software_proof
hardware_material_pending
not_proven
delivery_success=false
primary_actions_enabled=false
safe_to_control=false
not HIL
not true phone/browser
not PR #5 resolved
not delivery success
```

## 并行实施计划

### Task A - Hardware PC gate

Owner: `hardware-engineer`

Allowed files:

- `pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py`
- `pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.md`
- `docs/product/production_hardware_boundary.md`

Requirements:

- Read `docs/vendor/VENDOR_INDEX.md` before any hardware/source claim.
- Consume the previous safe handoff summary from `pr5_mandatory_sensor_material_owner_response_review_handoff`.
- Generate a safe reviewer ACK intake artifact/summary with accepted/missing/reassignment/blocked classification.
- Include `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, next required real materials and the fixed proof boundary.
- Do not write GitHub, do not resolve PR #5, do not claim LiDAR/ToF installed proof, WAVE ROVER/UART proof or HIL.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py
python3 -m unittest pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py
rg -n "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake|software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|source=software_proof|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence docs/interfaces docs/product/production_hardware_boundary.md pc-tools/README.md
git diff --check -- pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py pc-tools/README.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.md docs/product/production_hardware_boundary.md
```

### Task B - Robot diagnostics safe alias

Owner: `robot-software-engineer`

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/ros_runtime_contracts.md`
- `docs/product/remote_4g_mvp.md`

Requirements:

- Add a read-only safe alias such as `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary`.
- Expose only sanitized fields: capability, proof boundary, PR thread id, material state, ack status, next evidence, safe copy and false-state flags.
- Do not expose raw artifact internals, serial/UART details, credentials, `/cmd_vel`, ROS control topics, GitHub mutation, ACK/cursor mutation or robot command side effects.
- Preserve fail-closed state in `/api/status` and `/api/diagnostics` / remote relay summaries.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake
rg -n "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake|robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary|software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|source=software_proof|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/ros_runtime_contracts.md docs/product/remote_4g_mvp.md
```

### Task C - Full-Stack mobile read-only panel

Owner: `full-stack-software-engineer`

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Requirements:

- Add a first-screen read-only panel for `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`.
- Show capability, proof boundary, PR #5 thread, reviewer ACK intake status, owner/support/reviewer route, next required materials and safe copy.
- Keep Start Delivery, Confirm Dropoff and Cancel disabled.
- Do not add material upload, GitHub mutation, ACK/cursor update, replay/resubmit or robot command route.
- Do not claim true phone/browser proof; this remains static/local software proof until a real device/browser run exists.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json >/tmp/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake
rg -n "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake|software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|source=software_proof|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product closeout

Owner: `product-okr-owner`

Allowed files after implementation:

- `sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake/tech-done.md`
- `sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake/side2side_check.md`
- `sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Requirements:

- Verify worker outputs and rerun the combined fenced checks.
- Record actual changed files, validation output, failures/fixes and residual risk.
- Keep Objective 5 at about 68% and Objective 1 at about 81% unless real external/hardware evidence appears.
- Preserve no OKR percentage lift if outputs remain local software proof.

Closeout validation commands:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake|software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
```

## 接口影响

- Hardware PC gate produces a new safe summary only; no robot runtime command side effects.
- Robot diagnostics adds a read-only safe alias; existing status/diagnostics consumers must remain backward compatible.
- Mobile panel consumes sanitized Robot diagnostics summary only; no new write API or action path.
- Product closeout updates documentation and OKR snapshot only after implementation evidence exists.

## 风险和阻塞

- Missing real 2D LiDAR / ToF materials still blocks Objective 1 percentage lift.
- Missing public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result still blocks Objective 5 percentage lift.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved; this sprint must not imply reviewer resolution.
- Static/local mobile checks are not true phone/browser proof.
- Focused checks are intentional; no full Docker build is requested in this sprint.
