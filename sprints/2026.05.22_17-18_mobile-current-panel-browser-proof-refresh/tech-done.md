# Mobile Current Panel Browser Proof Refresh Tech Done

Run time: 2026-05-22 17:44 Asia/Shanghai

## sprint_type

epic

## 实际改动

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
  - Added scoped `--capability` and `--evidence-boundary` support so Task A can emit `mobile_current_panel_browser_proof_refresh` and `software_proof_docker_mobile_current_panel_browser_proof_refresh_gate` without adding another local O5 wrapper.
  - Extended current-panel browser assertions to cover the latest material-resolution ladder and reviewer ACK panels:
    - `field_evidence_material_resolution_intake`
    - `field_evidence_material_resolution_review_decision`
    - `field_evidence_material_resolution_review_handoff`
    - `field_evidence_material_resolution_followup_escalation_status`
    - `field_evidence_material_resolution_owner_response_intake`
    - `field_evidence_material_resolution_owner_response_review_decision`
    - `field_evidence_material_resolution_owner_response_review_handoff`
    - `field_evidence_material_resolution_reviewer_ack_intake`
  - Added a fail-closed browser assertion that these panels keep `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and the reviewer ACK panel keeps `not true phone/browser`.
- `mobile/web/test_mobile_web_entrypoint.py`
  - Extended the current browser-entrypoint regression suite; final command output was `Ran 264 tests ... OK`.
- `mobile/test_mobile_web_entrypoint.py`
  - Added targeted unit assertions for the new gate CLI flags, material-resolution/reviewer ACK current-panel IDs, boundaries, and `material_resolution_panels_fail_closed`.
- `docs/product/mobile_user_flow.md`
  - Documented the `mobile_current_panel_browser_proof_refresh` gate mode and its software-proof boundary.
- `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/evidence/`
  - Wrote fresh-profile evidence JSON and screenshots for `390x844` and `768x900`, plus `mobile_current_panel_browser_proof_refresh_summary.json`.

No UI layout, ROS2 API, cloud API, Robot command API, hardware configuration, launch parameter, or `OKR.md` implementation change was made by the Engineer execution tasks.

## Robot Task B 只读核对

Robot Task B changed no files. It confirmed the current panels consume phone-safe Robot diagnostics/status summaries and do not consume raw ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER parameters, credentials, local paths, tracebacks, checksums, or complete artifacts in the current Robot diagnostics current-panel summary path.

Known caveat: two old fixture fragments may still contain historical enabled flags, but Robot Task B confirmed they are not in the current Robot diagnostics current-panel summary path. This caveat does not change the closeout boundary, which remains fail-closed with `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## 用户价值和产品北极星

The refreshed browser proof keeps the phone/web entrypoint aligned with the product north star: ordinary users should see current task/material/support status and understand that Start Delivery, Confirm Dropoff, and Cancel are unavailable while proof is blocked or not proven. This is current-panel visibility and fail-closed evidence only, not a new control capability.

## OKR 映射和 KR 拆解

- Objective 4 KR7 / KR4: accepted as a local Chromium-family refresh showing current panels visible, console-zero, and fail-closed on phone/tablet-ish viewports.
- Objective 5: no lift. The sprint does not provide public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, verified terminal result, or external phone/browser proof.
- Objective 1: no lift. The sprint does not provide WAVE ROVER/UART/HIL, 2D LiDAR/ToF materials, operator HIL report, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
- Objective 2 / Objective 3: no lift. The sprint does not provide route/elevator field pass, Nav2/fixed-route runtime, task record, dropoff/cancel completion, delivery result, or delivery success.

Closeout decision: accept only as `software_proof_docker_mobile_current_panel_browser_proof_refresh_gate`. Capability: `mobile_current_panel_browser_proof_refresh`. Result: no OKR percentage lift.

## 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/evidence --fresh-profile --require-console-zero --capability mobile_current_panel_browser_proof_refresh --evidence-boundary software_proof_docker_mobile_current_panel_browser_proof_refresh_gate
viewport=390x844 passed=true current_panels_status=passed current_boundaries_status=passed material_resolution_panels_fail_closed=true primary_actions_disabled=true phone_safe_status=passed fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0 evidence_boundary=software_proof_docker_mobile_current_panel_browser_proof_refresh_gate
viewport=768x900 passed=true current_panels_status=passed current_boundaries_status=passed material_resolution_panels_fail_closed=true primary_actions_disabled=true phone_safe_status=passed fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0 evidence_boundary=software_proof_docker_mobile_current_panel_browser_proof_refresh_gate
summary=sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/evidence/mobile_current_panel_browser_proof_refresh_summary.json ok=true capability=mobile_current_panel_browser_proof_refresh evidence_boundary=software_proof_docker_mobile_current_panel_browser_proof_refresh_gate fresh_profile=true require_console_zero=true
```

```text
node --check mobile/web/app.js
PASS

node --check mobile/web/service-worker.js
PASS
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 264 tests ... OK
```

Engineer-required `rg` checks and scoped `git diff --check` passed. Product closeout reran the required file checks, required `rg`, and scoped `git diff --check`; results are recorded in `final.md`.

## 失败定位

No gate/runtime/console/current-panel failure remained after the scoped update. The initial inspection found that `phone_browser_acceptance_gate.py` did not support the requested `--capability` / `--evidence-boundary` flags and did not yet include the newest material-resolution / reviewer ACK panels in current-panel and boundary expectations; both were fixed in the gate only.

## 剩余风险

- This is not true phone/browser, not real iPhone/Android device behavior, not a production app, not a real PWA prompt/userChoice, and not field phone acceptance.
- This is not O5 external proof: not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, and not verified terminal result.
- This is not HIL, not WAVE ROVER/UART proof, not real `/odom`、`/imu/data`、`/battery` feedback, not 2D LiDAR/ToF material proof, and not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
- This is not route/elevator field pass, not real Nav2/fixed-route runtime, not dropoff/cancel completion, not delivery result, not delivery success, and not PR #5 resolution.
