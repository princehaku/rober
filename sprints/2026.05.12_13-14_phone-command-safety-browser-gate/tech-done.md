# Sprint 2026.05.12_13-14 Phone Command Safety Browser Gate - Tech Done

## Full-stack Command Safety Browser Gate

- Owner: `full-stack-software-engineer`
- Run time: 2026-05-12 11:13:50 CST.
- Scope: operator browser/API command safety gate, focused tests, and product docs. Robot compatibility section below is preserved for Robot owner evidence.
- Evidence boundary: `software_proof_docker_phone_command_safety_browser_gate`.

### Actual changes

- `/api/status.phone_readiness.evidence_boundary` now reports `software_proof_docker_phone_command_safety_browser_gate`.
- `/api/status.phone_readiness.command_safety` was added with schema `trashbot.command_safety.v1`, `global_block_reason`, per-action gate entries for `start`, `confirm_dropoff`, `cancel`, and `diagnostics`, plus ACK copy that explicitly says ACK is command accepted/processing evidence only.
- Operator first-screen buttons now consume `phone_readiness.command_safety.actions.*.enabled` instead of raw `can_collect` / `can_confirm_dropoff` / `can_cancel`. The raw fields remain available for old clients and are inputs to the new gate.
- Diagnostics remains enabled, but the page shows the same blocking reason so users can collect support evidence without making Start/Confirm green.
- Product docs updated in `docs/product/mobile_user_flow.md` and `docs/product/remote_4g_mvp.md`.

### Covered states

- Ready: primary action follows the existing local action permission and becomes enabled only when remote readiness and manifest summary are safe.
- Status stale: Start/Confirm/Cancel are disabled with a wait-for-status explanation.
- Command pending: Start/Confirm/Cancel are disabled until ACK appears, preventing repeated command submission.
- Auth failed: primary commands are disabled and the phone copy asks for login/access-code recovery.
- Cloud unreachable: primary commands are disabled even if the local page remains observable.
- Malformed response: primary commands are disabled and Diagnostics remains available for support.
- Manifest missing/invalid/stale: primary commands are disabled until diagnostic object references are refreshed or regenerated.

### Browser/API fence

Option B was used. There is no stable standalone local gateway start/smoke entry in this worker scope, so the existing HTTP handler/unit tests cover rendered HTML button wiring and API payload shape:

```text
test_index_page_contains_operator_controls verifies commandSafetyCopy, commandSafetyAck, diagnosticsGateCopy, command_safety, applyCommandSafety, and button disabled expressions using command_safety actions.
test_status and build_phone_readiness tests verify ready, status_stale, command_pending, auth_failed, cloud_unreachable, malformed_response, manifest missing/invalid/stale, and manual takeover gates.
```

### Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

```text
Ran 64 tests in 17.299s

OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```text
passed with no output
```

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/product/mobile_user_flow.md \
  docs/product/remote_4g_mvp.md \
  docs/product/cloud_4g_infrastructure.md \
  sprints/2026.05.12_13-14_phone-command-safety-browser-gate/tech-done.md
```

```text
passed with no output
```

### Remaining risk

- This is local/Docker software proof only. It does not prove real phone device/browser acceptance, production app, real cloud, HTTPS/TLS public ingress, real 4G/SIM, real OSS upload, CDN origin fetch, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or real trash delivery.
- Robot-side compatibility evidence is owned by `robot-software-engineer`; this Full-stack section did not change `remote_bridge` or remote command/status/ack HTTP shape.

## Robot Compatibility Fence

- Owner: `robot-software-engineer`
- Scope: remote bridge command/status/ack/cursor compatibility only.
- Result: passed.
- Evidence command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

- Evidence output:

```text
Ran 31 tests in 15.230s

OK
```

- Compatibility finding: no command/status/ack/cursor regression found in the local Docker/macOS software fence. Existing tests still cover command validation, status posting before command polling, terminal ACK states, duplicate command ACK reuse, cursor restore/persist behavior, and outage/auth/malformed-response paths that must not advance the cursor.
- Evidence boundary: `software_proof_docker_phone_command_safety_browser_gate`; this does not prove real phone device acceptance, real cloud/4G, Nav2/fixed-route execution, WAVE ROVER motion, HIL, or real delivery.
- Full-stack coordination: no Robot-side API shape change requested; Full-stack can continue browser/API button gate work against the existing remote command/status/ack contract.
