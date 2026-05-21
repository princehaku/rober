# Tech Done

## Worker 2 Full-Stack Evidence

- run_time: 2026-05-21 10:14:01 CST
- owner: User Touchpoint Full-Stack Engineer
- capability: `cloud_manual_takeover_command_safety_guard`
- files_changed:
  - `mobile/web/app.js`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `mobile/web/fixtures/robot_diagnostics_cloud_manual_takeover_command_safety_guard.json`
  - `docs/product/mobile_user_flow.md`
- behavior:
  - `mobile/web` consumes `degradation_state=manual_takeover_required`, `manual_takeover_required=true`, `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `retry_hint=contact_support`, and `ack_semantics=manual_takeover_not_delivery_success` through the existing cloud-readiness surface.
  - Start Delivery / Confirm Dropoff / Cancel stay disabled through the existing `command_safety` and legacy permission gates.
  - The fixture and docs keep the proof boundary at `software_proof_docker_cloud_manual_takeover_command_safety_guard`.
- validation:
  - `node --check mobile/web/app.js` passed.
  - `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` passed: 205 tests.
  - `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_manual_takeover_command_safety_guard.json >/tmp/cloud_manual_takeover_fixture_check.json` passed.
  - `rg -n "cloud_manual_takeover_command_safety_guard|manual_takeover_required|software_proof_docker_cloud_manual_takeover_command_safety_guard|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web docs/product/mobile_user_flow.md` returned matching contract lines.
  - `git diff --check -- mobile/web docs/product/mobile_user_flow.md` passed.
- remaining_risk:
  - This is Docker/local `software_proof` only. It is not real external cloud proof, true phone/browser proof, HIL, WAVE ROVER/UART proof, route/elevator field pass, delivery result, or delivery success.
  - Robot/API Worker 1 must provide the same safe fields at runtime for live integration beyond the fixture.

## Worker 1 Robot Platform Evidence

- run_time: 2026-05-21 10:21:15 CST
- owner: Robot Platform Engineer
- capability: `cloud_manual_takeover_command_safety_guard`
- files_changed:
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `docs/interfaces/ros_runtime_contracts.md`
  - `docs/product/remote_4g_mvp.md`
- behavior:
  - Robot/API now canonicalizes `needs_human_help`, `failed`, and `degradation_state=manual_takeover_required` into `capability=cloud_manual_takeover_command_safety_guard`.
  - The safe state forces `manual_takeover_required=true`, `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `retry_hint=contact_support`, `ack_semantics=manual_takeover_not_delivery_success`, and `proof_boundary=software_proof_docker_cloud_manual_takeover_command_safety_guard`.
  - ACK operator status, mock cloud `remote_readiness`, `/api/status` phone readiness, `/api/diagnostics`, support handoff, voice prompt readiness, and offline/resume summaries preserve diagnostics visibility while redacting raw tokens, ROS topics, `/cmd_vel`, and unsafe success/control flags.
- validation:
  - `python3 -m py_compile ...operator_gateway_http.py ...remote_bridge.py ...remote_bridge_protocol.py` passed.
  - `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py` passed: 517 tests.
  - Required `rg -n "cloud_manual_takeover_command_safety_guard|manual_takeover_required|software_proof_docker_cloud_manual_takeover_command_safety_guard|delivery_success=false|primary_actions_enabled=false|remote_ready=false|safe_to_control=false" ...` returned matching Robot/API and docs lines.
  - `git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/ros_runtime_contracts.md` passed.
- remaining_risk:
  - This is Docker/local `software_proof` only. It is not real external cloud proof, true phone/browser proof, HIL, WAVE ROVER/UART proof, route/elevator field pass, delivery result, or delivery success.
  - Live integration still depends on Product closeout and any concurrent Full-Stack worker changes being merged without changing the canonical field names.

## Worker 3 Product Closeout Evidence

- run_time: 2026-05-21 10:28 CST
- owner: Product Manager / OKR Owner
- capability: `cloud_manual_takeover_command_safety_guard`
- product_north_star: 手机用户在远程控制退化为人工接管时，能看懂当前需要现场/支持介入，同时不会被误导去点击 Start Delivery、Confirm Dropoff 或 Cancel。
- user_value:
  - 把 `manual_takeover_required` 从泛化 command-safety blocker 变成独立可复核状态。
  - 保留 diagnostics/support 可见性，但不暴露 raw diagnostics、ROS topic、`/cmd_vel`、串口/UART、WAVE ROVER、token、traceback 或成功控制语义。
- OKR_mapping:
  - Primary: Objective 5 云中转 + OSS/CDN 数据通路产品化，保持约 68%。
  - Guardrail: Objective 1 硬件协议可信底盘，保持约 81%；PR #5 `PRRT_kwDOSWB9286CJ3tX` 保持 unresolved / material pending。
  - Touchpoint benefit: Objective 4 手机体验只获得 fail-closed 可见性，不计为真实手机/browser proof。
- KR_closeout:
  - KR-A Robot/API 已提供 `manual_takeover_required` safe remote-readiness state。
  - KR-B diagnostics 已保留安全摘要并由 Robot worker 修复 unsafe raw `latest_status.remote_readiness` 泄漏风险，改为 computed safe `remote_readiness`。
  - KR-C mobile/web 已消费 fixture 和 safe fields，并保持 Start Delivery / Confirm Dropoff / Cancel disabled。
  - KR-D Product closeout 将本轮写入 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- files_changed_by_product:
  - `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/tech-done.md`
  - `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/side2side_check.md`
  - `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/final.md`
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
- evidence_boundary:
  - Closed only as `software_proof_docker_cloud_manual_takeover_command_safety_guard`.
  - Required false states stay explicit: `manual_takeover_required`, `delivery_success=false`, `primary_actions_enabled=false`, `remote_ready=false`, `safe_to_control=false`.
  - This is not real external cloud proof, not true phone/browser proof, not HIL, not WAVE ROVER/UART proof, not route/elevator field pass, not delivery result, and not delivery success.
- integrated_worker_validation:
  - Robot: `py_compile` passed; focused unittest passed with `Ran 517 tests in 137.481s OK`; required `rg` passed; scoped diff check passed. First failures were fixed; final diagnostics issue preserving unsafe raw `latest_status.remote_readiness` was patched to computed safe `remote_readiness`.
  - Full-Stack: `node --check` passed; mobile unittest passed with `Ran 205 tests`; fixture JSON check passed; required `rg` passed; scoped diff check passed. First failure was forbidden literal `raw diagnostics`, fixed and rerun.
- remaining_risk:
  - Real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser behavior, WAVE ROVER/UART/HIL, PR #5 material closure, route/elevator field pass, delivery result, and delivery success remain unproven.
  - Objective 5 remains about 68% and Objective 1 remains about 81% until real external cloud/phone or hardware materials arrive.
