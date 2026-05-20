# Cloud Command Sequence Regression Guard Tech Plan

## OKR Lowest-priority Check

1. Current lowest Objective in `OKR.md` 4.1: Objective 5, about 68%.
2. This sprint targets Objective 5.
3. Boundary: it cannot raise O5 completion because no real external cloud, OSS/CDN, DB/queue, 4G/SIM, phone/browser, or production worker/cutover evidence is available on this Docker-only host.

## Architecture

Add a local software-proof guard for optional cloud command queue sequence metadata:

- `remote_bridge_protocol.validate_command` should preserve a safe optional `queue_sequence`.
- `RemoteBridgeWorker` should track the highest terminal `queue_sequence` only after the corresponding terminal ACK is accepted by the cloud.
- A lower/equal sequence for a different command id should produce a terminal `ignored` ACK and a phone-safe degraded status.
- Operator gateway readiness/command safety should treat `command_sequence_regression` like other fail-closed remote degradation states.
- `mobile/web` should display the read-only cloud readiness state and never enable Start Delivery / Confirm Dropoff / Cancel from it.

## File Scope

Robot Platform Engineer may edit:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `docs/product/remote_4g_mvp.md`

User Touchpoint Full-Stack Engineer may edit:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Product Manager / OKR Owner may edit:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_22-23_cloud-command-sequence-regression-guard/tech-done.md`
- `sprints/2026.05.20_22-23_cloud-command-sequence-regression-guard/side2side_check.md`
- `sprints/2026.05.20_22-23_cloud-command-sequence-regression-guard/final.md`

## Acceptance Commands

Robot Platform Engineer:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
rg -n "command_sequence_regression|software_proof_docker_cloud_command_sequence_regression_guard|sequence_regression_not_delivery_success" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py docs/product/remote_4g_mvp.md
```

User Touchpoint Full-Stack Engineer:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "command_sequence_regression|software_proof_docker_cloud_command_sequence_regression_guard|sequence_regression_not_delivery_success" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Product closeout:

```bash
rg -n "command_sequence_regression|Objective 5|software_proof_docker_cloud_command_sequence_regression_guard|not real production queue ordering" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_22-23_cloud-command-sequence-regression-guard
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_22-23_cloud-command-sequence-regression-guard
```

## Risks

- This is local Docker software proof only.
- Queue metadata is optional and must not replace the opaque cursor contract.
- If a worker reports unrelated failures, keep the fix fenced to the files above or return a blocker.
