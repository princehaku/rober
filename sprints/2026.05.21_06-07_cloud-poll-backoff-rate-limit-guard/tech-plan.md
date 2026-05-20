# Cloud Poll Backoff Rate Limit Guard Tech Plan

## Implementation Trigger

This plan is complete enough to enter implementation. The main session should dispatch Robot and Full-Stack workers in parallel, then Product closeout after their verification. Do not pause for another product approval unless a worker finds that `cloud_poll_backoff` is already fully implemented.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 针对 Objective 5。
3. 选择理由：Objective 5 的百分比提升仍依赖真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser evidence；当前 Docker-only 主机无法提供这些材料。最新 `cloud_unreachable` / `malformed_response` guard final 已禁止重复 local O5 guard depth，除非存在 fresh unguarded failure mode。本轮 fresh gap 是 poll backoff/rate-limit：`docs/product/cloud_4g_infrastructure.md` 明确要求机器人轮询间隔可控，避免低价值高频空轮询；近期 O5 guards 未建立 `cloud_poll_backoff` 的 Robot/mobile fail-closed 状态。

## Architecture

Add one new O5 software-proof state across Robot diagnostics and mobile/web:

- Canonical state: `cloud_poll_backoff`
- Evidence boundary: `software_proof_docker_cloud_poll_backoff_rate_limit_guard`
- Safe readiness fields: `remote_ready=false`, `safe_to_control=false`, `primary_actions_enabled=false`, `delivery_success=false`
- Retry hint: `wait_for_backoff_window`
- User copy: Chinese phone-safe text that says remote control is waiting for a retry window and primary actions are disabled.

The guard must not execute robot actions, change route/elevator behavior, mutate hardware config, or claim field proof.

## Files And Owners

### Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/operator_gateway_diagnostics.md`

Responsibilities:

- Add or reuse bounded poll/backoff metadata in `remote_bridge.py`.
- Convert repeated poll failure / empty-poll pressure into safe diagnostics/status state `cloud_poll_backoff`.
- Preserve existing priority ordering for more specific O5 states.
- Ensure all new technical comments are Chinese and meaningful.
- Update Robot-facing docs.

### User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_cloud_poll_backoff_rate_limit_guard.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Responsibilities:

- Add read-only phone rendering for `cloud_poll_backoff`.
- Keep Start Delivery / Confirm Dropoff / Cancel disabled.
- Add fixture and focused mobile test coverage.
- Ensure user-facing copy is Chinese and does not expose raw cloud, ROS, or hardware details.

### Product Manager / OKR Owner

Allowed closeout files after implementation:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/tech-done.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/side2side_check.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/final.md`

Responsibilities:

- Keep Objective 5 percentage unchanged unless real external evidence is supplied.
- Record worker validation and evidence boundary.
- Confirm docs under `docs/` were synchronized.

### Read-Only Consults

- Hardware Infra Engineer: confirm no WAVE ROVER, UART, HIL, 2D LiDAR, ToF, PR #5 `PRRT_kwDOSWB9286CJ3tX`, or vendor-material claim was introduced.
- Autonomy Algorithm Engineer: confirm no Nav2/fixed-route, route/elevator field pass, route completion, dropoff/cancel, or delivery result claim was introduced.

## Task Breakdown

### Task 1: Robot Guard

- Add `cloud_poll_backoff` status derivation when poll failure count/backoff window or empty-poll pressure reaches the configured local threshold.
- Keep thresholds parameterized or locally configurable; do not hard-code production claims.
- Add safe summary fields only: `degradation_state`, `remote_ready`, `safe_to_control`, `primary_actions_enabled`, `delivery_success`, `retry_hint`, `proof_boundary`, optional `backoff_until` or redacted duration.
- Do not include cloud base URL, token, Authorization header, state path, traceback, `/cmd_vel`, raw ROS topics, serial device, WAVE ROVER details, or `delivery_success=true`.

### Task 2: Robot Tests And Docs

- Add focused tests for:
  - repeated poll failure enters `cloud_poll_backoff`;
  - primary actions remain disabled;
  - more specific states still win over generic backoff;
  - redaction excludes unsafe fields;
  - ACK/delivery success semantics remain false.
- Update `docs/product/remote_4g_mvp.md` and `docs/interfaces/operator_gateway_diagnostics.md`.

### Task 3: Mobile Rendering

- Add fixture `robot_diagnostics_cloud_poll_backoff_rate_limit_guard.json`.
- Render Chinese safe copy and retry guidance.
- Keep primary controls disabled and avoid raw JSON/ROS/hardware wording.
- Add focused mobile tests and doc sync in `docs/product/mobile_user_flow.md`.

### Task 4: Product Closeout

- Create `tech-done.md`, `side2side_check.md`, and `final.md` after worker results.
- Update `OKR.md` and `docs/process/okr_progress_log.md` conservatively.
- State clearly that this is `software_proof_docker_cloud_poll_backoff_rate_limit_guard` and not real O5 external proof.

## 验收命令

Robot worker must run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py

rg -n "cloud_poll_backoff|software_proof_docker_cloud_poll_backoff_rate_limit_guard|remote_ready=false|primary_actions_enabled=false|delivery_success=false|wait_for_backoff_window" \
  onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md

git diff --check -- \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  docs/product/remote_4g_mvp.md \
  docs/interfaces/operator_gateway_diagnostics.md
```

Full-Stack worker must run:

```bash
node --check mobile/web/app.js

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py

python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_poll_backoff_rate_limit_guard.json >/tmp/cloud_poll_backoff_fixture_check.json

rg -n "cloud_poll_backoff|software_proof_docker_cloud_poll_backoff_rate_limit_guard|remote_ready=false|primary_actions_enabled=false|delivery_success=false|wait_for_backoff_window" \
  mobile/web docs/product/mobile_user_flow.md

git diff --check -- \
  mobile/web/app.js \
  mobile/web/fixtures/robot_diagnostics_cloud_poll_backoff_rate_limit_guard.json \
  mobile/web/test_mobile_web_entrypoint.py \
  docs/product/mobile_user_flow.md
```

Product closeout must run:

```bash
test -f sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/tech-done.md
test -f sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/side2side_check.md
test -f sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/final.md

rg -n "Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_poll_backoff_rate_limit_guard|not real external cloud proof|delivery_success=false|primary_actions_enabled=false" \
  OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard

git diff --check -- \
  OKR.md \
  docs/process/okr_progress_log.md \
  sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard
```

Planning validation for this handoff:

```bash
test -f sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/pre_start.md
test -f sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/prd.md
test -f sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof|Docker|验收命令|文件范围" sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard
git diff --check -- sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard
```

## 文件范围

Planning files already scoped to:

- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/pre_start.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/prd.md`
- `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/tech-plan.md`

Implementation must not edit unrelated sprint folders, unrelated docs, hardware config, Nav2/fixed-route code, or vendor files.

## Evidence Boundary

This sprint can only close as Docker/local software proof unless real external evidence appears. Final wording must explicitly say it is not real public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not production worker/cutover, not true phone/browser proof, not HIL, not route/elevator field pass, not delivery success, and not PR #5 reviewer resolution.
