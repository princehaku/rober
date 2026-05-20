# Cloud Unreachable Malformed Response Guard Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_05-06_cloud-unreachable-malformed-response-guard`
- Target capability: `cloud_unreachable_malformed_response_guard`
- Evidence boundary: `software_proof_docker_cloud_unreachable_malformed_response_guard`
- Required preserved states: `source=software_proof`, `not_proven`, `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for parallel Engineer workers after Product planning.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 is about 68%, below Objective 1 at about 81% and Objectives 2/3/4 at about 99%.
2. This sprint targets Objective 5's Docker/local fail-closed gap, but it does not raise Objective 5 percentage.
3. Reason: Objective 5 percentage movement still needs real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser external proof. This Docker-only host cannot provide those materials.
4. This sprint is acceptable because it is not another wrapper around PR #5 missing materials and not a repeat of the same O5 guards already covered. It fills the explicit `cloud_unreachable` and `malformed_response` gap that `docs/product/mobile_user_flow.md` and `docs/product/remote_4g_mvp.md` mention without same-level guard coverage.
5. Objective 1 / PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending and is outside this sprint.

## Evidence Inputs

- `AGENTS.md` sprint discipline, Epic docs chain, and bounded owner routing.
- `OKR.md` 4.1 current snapshot and section 6 priority guidance.
- Latest sprint: `sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/final.md`.
- Product docs: `docs/product/mobile_user_flow.md` and `docs/product/remote_4g_mvp.md`.
- Recent O5 guard family: `cloud_auth_failure_status_guard`, `cloud_media_degradation_status_guard`, `cloud_command_sequence_regression_guard`, and `cloud_status_stale_guard`.

## Interface Boundary

- New proof family: `cloud_unreachable_malformed_response_guard`.
- Required evidence boundary: `software_proof_docker_cloud_unreachable_malformed_response_guard`.
- Required degradation states:
  - `cloud_unreachable`
  - `malformed_response`
- Required false states: `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `not_proven`.
- Required redaction boundary: no bearer tokens, Authorization headers, credentials, DB/queue URLs, OSS AK/SK, raw cloud response bodies, tracebacks, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, or hardware control internals.

## Worker 1: Robot Platform Engineer

Responsibility: Robot/API guard summary, diagnostics normalization, and focused software proof.

文件范围:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add a Robot/API safe summary for `cloud_unreachable_malformed_response_guard`.
- Normalize both `cloud_unreachable` and `malformed_response` into `remote_ready=false`, `primary_actions_enabled=false`, `delivery_success=false`, and `not_proven`.
- Preserve diagnostics visibility while preventing Start/Confirm/Cancel semantics, ACK/cursor fetch, retry, replay, resubmit, queue advancement, or hidden robot command side effects.
- Fail closed on unsupported schema, missing false states, unsafe success/control wording, raw cloud response, traceback, credentials, DB/queue URLs, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, HIL/pass wording, or delivery success wording.
- Keep technical comments in Chinese and maintain the repo comment-quality rule for any new code.

验收命令:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "cloud_unreachable_malformed_response_guard|cloud_unreachable|malformed_response|software_proof_docker_cloud_unreachable_malformed_response_guard|remote_ready=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard
```

## Worker 2: User Touchpoint Full-Stack Engineer

Responsibility: phone-safe `mobile/web` fail-closed surface and user copy.

文件范围:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Render `cloud_unreachable` and `malformed_response` through the existing cloud readiness / command safety UI surface or a small read-only panel if needed.
- Use Chinese-first safe copy:
  - `cloud_unreachable`: "云端暂时不可达；当前不能下发主操作，请刷新状态或联系支持。"
  - `malformed_response`: "云端响应格式异常；机器人没有确认执行，请刷新状态或联系支持。"
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Keep Diagnostics / Support Handoff visible without adding control endpoints, ACK/cursor requests, retries, resubmits, raw diagnostics fetches, or hidden robot commands.
- Never expose raw JSON, credentials, bearer tokens, Authorization headers, DB/queue URLs, OSS AK/SK, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, local paths, checksums, or complete artifacts.

验收命令:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "cloud_unreachable_malformed_response_guard|cloud_unreachable|malformed_response|software_proof_docker_cloud_unreachable_malformed_response_guard|remote_ready=false|delivery_success=false|primary_actions_enabled=false|云端暂时不可达|云端响应格式异常" mobile/web docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard
git diff --check -- mobile/web docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard
```

## Product Closeout Plan

Product closeout owns after implementation:

- `sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/tech-done.md`
- `sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/side2side_check.md`
- `sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/final.md`
- `OKR.md` and `docs/process/okr_progress_log.md` only if implementation lands and closeout evidence is ready.

Closeout requirements:

- Confirm Robot and Full-Stack synchronized related `docs/` files.
- Confirm no wording claims real external cloud, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, route/elevator field pass, Nav2/fixed-route, WAVE ROVER/UART, HIL, dropoff/cancel completion, delivery result, or delivery success.
- Keep Objective 5 at about 68% unless real external proof appears.
- Stage only intended files and use scoped diff checks.

Product acceptance commands after implementation:

```bash
test -f sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/tech-done.md
test -f sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/side2side_check.md
test -f sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/final.md
rg -n "cloud_unreachable_malformed_response_guard|software_proof_docker_cloud_unreachable_malformed_response_guard|Objective 5|software proof|not real external cloud proof|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard
```

## Planning-only 验收命令

The Product planning step must run:

```bash
test -f sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/pre_start.md && test -f sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/prd.md && test -f sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard/tech-plan.md
rg -n "sprint_type: epic|cloud_unreachable_malformed_response_guard|Objective 5|OKR 最低优先级核对|software_proof_docker_cloud_unreachable_malformed_response_guard|Robot Platform Engineer|User Touchpoint Full-Stack Engineer" sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard
git diff --check -- sprints/2026.05.21_05-06_cloud-unreachable-malformed-response-guard
```

## Boundaries And Non-claims

This sprint must not claim real external cloud proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, true phone/browser proof, real PWA prompt/userChoice, Nav2/SLAM/fixed-route field pass, real route/elevator field pass, WAVE ROVER/UART/HIL, dropoff completion, cancel completion, delivery result, delivery success, Objective 5 percentage movement, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
