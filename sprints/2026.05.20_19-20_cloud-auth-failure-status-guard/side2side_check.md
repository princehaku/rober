# Cloud Auth Failure Status Guard Side2Side Check

## Acceptance Result

- sprint_type: epic
- Sprint: `2026.05.20_19-20_cloud-auth-failure-status-guard`
- Evidence boundary: `software_proof_docker_cloud_auth_failure_status_guard`
- Result: accepted as Docker/local software proof.

## Checklist

| Requirement | Result |
| --- | --- |
| Robot bridge emits explicit auth failure state | Passed: `auth_failed`, `check_auth`, `auth_failed_not_delivery_success`, and proof boundary are present. |
| Operator HTTP readiness fails closed | Passed: auth failure keeps `remote_ready=false` and `primary_actions_enabled=false`. |
| Diagnostics redacts auth/runtime material | Passed: auth failure redaction is active while non-auth diagnostics `log_refs` compatibility is preserved. |
| Mobile/web renders phone-safe copy | Passed: fixture and UI expose login/access-code guidance and “这不是送达成功”. |
| Main actions remain disabled | Passed: Start Delivery / Confirm Dropoff / Cancel remain fail-closed. |
| Non-claims preserved | Passed: docs and sprint records keep real cloud, real phone, HIL, and delivery success outside the proof boundary. |

## Verification Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile ...remote_bridge.py ...operator_gateway_http.py ...operator_gateway_diagnostics.py
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 413 tests in 93.162s
OK

node --check mobile/web/app.js
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 177 tests in 1.279s
OK

python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_auth_failure_status_guard.json >/dev/null
passed

required rg scans
passed

scoped git diff --check
passed
```

## Boundary

This check does not prove real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, real phone/browser validation, WAVE ROVER/UART/HIL, route/elevator field pass, dropoff/cancel completion, delivery result, delivery success, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
