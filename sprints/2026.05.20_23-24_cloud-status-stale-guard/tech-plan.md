# Cloud Status Stale Guard Tech Plan

## OKR 最低优先级核对

- Current lowest Objective in `OKR.md` 4.1: Objective 5 at about 68%.
- This sprint targets Objective 5.
- Real O5 completion remains blocked by missing public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, and true phone/browser evidence. This sprint therefore advances a fresh Docker-only fail-closed safety gap without changing completion percentage.

## Evidence-backed Recommendation

1. Deepen Objective 5 through `cloud_status_stale_guard`.
   - Evidence: latest O5 sprint `cloud-command-sequence-regression-guard` left O5 at 68% and named real external materials as the blocker; `operator_gateway_http.py` already has generic `status_stale`, but no dedicated proof boundary or mobile fixture.
   - Action: turn stale robot status into an explicit, phone-safe, fail-closed O5 guard.
2. Do not return to PR #5 hardware closure this round.
   - Evidence: live PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved and asks for vendor-source citation; the published reply is `hardware_material_pending`, not real hardware proof.
   - Action: keep O1 at about 81% and avoid claiming material progress.
3. Do not treat PR #6 as implementation evidence.
   - Evidence: PR #6 is README docs-only and has no review comments.
   - Action: use it only as product framing evidence, not runtime or OKR completion proof.

## Work Packages

### A. Robot/API - owner `robot-software-engineer`

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `docs/product/remote_4g_mvp.md`

Implementation:

- Add `software_proof_docker_cloud_status_stale_guard` as the dedicated status-stale proof boundary.
- Add `stale_status_not_delivery_success` semantics to remote readiness.
- Preserve existing stale detection threshold and keep all primary actions disabled.
- Update focused Robot/API tests and product cloud doc.

Validation commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
rg -n "software_proof_docker_cloud_status_stale_guard|stale_status_not_delivery_success|status_stale" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py docs/product/remote_4g_mvp.md
```

### B. Mobile/Web - owner `full-stack-software-engineer`

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Implementation:

- Add stale-status guard constants/copy and consume the fixture through the existing cloud readiness surface.
- Ensure Start Delivery, Confirm Dropoff, and Cancel remain disabled; Diagnostics remains available.
- Keep copy phone-safe and explicit that this is not delivery success or true phone/browser proof.

Validation commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "software_proof_docker_cloud_status_stale_guard|stale_status_not_delivery_success|status_stale" mobile/web/app.js mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### C. Product Closeout - owner `product-okr-owner`

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_23-24_cloud-status-stale-guard/tech-done.md`
- `sprints/2026.05.20_23-24_cloud-status-stale-guard/side2side_check.md`
- `sprints/2026.05.20_23-24_cloud-status-stale-guard/final.md`

Implementation:

- Close the sprint conservatively as `software_proof_docker_cloud_status_stale_guard`.
- Keep Objective 5 at about 68% unless real external materials arrive.
- Record PR #5 unresolved thread and PR #6 docs-only boundary.

Validation commands:

```bash
test -f sprints/2026.05.20_23-24_cloud-status-stale-guard/tech-done.md
test -f sprints/2026.05.20_23-24_cloud-status-stale-guard/side2side_check.md
test -f sprints/2026.05.20_23-24_cloud-status-stale-guard/final.md
rg -n "cloud_status_stale_guard|software_proof_docker_cloud_status_stale_guard|Objective 5|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_23-24_cloud-status-stale-guard
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_23-24_cloud-status-stale-guard
```

## Integration Risks

- The stale-status guard must not loosen `status_stale` detection or change command execution.
- Mobile copy must not expose raw cloud, token, ROS topic, `/cmd_vel`, serial, UART, or WAVE ROVER details.
- This sprint must not increase OKR percentages without real external evidence.
