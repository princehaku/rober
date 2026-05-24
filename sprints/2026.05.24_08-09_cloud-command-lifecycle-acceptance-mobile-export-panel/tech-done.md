# Cloud Command Lifecycle Acceptance Mobile Export Panel Tech Done

Run time: 2026-05-24 09:00 Asia/Shanghai

## Task A - Full-Stack Mobile Export Panel

### Actual changes

- Added the read-only `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel` surface in `mobile/web/app.js`.
- Added the mobile fixture `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json`.
- Added targeted unittest coverage in `mobile/web/test_mobile_web_entrypoint.py`.
- Updated `docs/product/mobile_user_flow.md` and `docs/product/remote_4g_mvp.md` for the phone/support consumption boundary.

### Validation

- `node --check mobile/web/app.js` passed.
- `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json` passed.
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel` passed: `Ran 2 tests in 0.021s OK`.
- Required marker `rg` passed for `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`, `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`, `accepted_processing_only_not_delivery_success`, `terminal_result_pending`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not true phone/browser proof`.
- Scoped `git diff --check` passed for Task A touched files.

### Failure localization

- First targeted unittest run failed because the new fixture `recovery_hint` contained the forbidden text `raw diagnostics` / `GitHub mutation`. The fixture wording was changed to phone-safe wording without raw-route or mutation labels, then the targeted unittest passed.

### Remaining risk

- This is `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate` only.
- It is not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not HIL, not WAVE ROVER/UART proof, not PR #5 resolution, not verified terminal delivery/dropoff/cancel result, and not delivery success.
- Required false-state flags remain `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## Task B - Robot Compatibility Fix

### Actual changes

- Updated `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` so the HTTP export payload now carries explicit `safe_command_id` and `safe_evidence_ref`.
- Kept both IDs as pending-safe placeholders: `pending_same_safe_command_id` and `pending_same_safe_evidence_ref`.
- Updated `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` to assert the HTTP export and nested source payloads preserve the same safe placeholders.
- Updated `docs/product/remote_4g_mvp.md` to state that pending safe IDs are placeholders for same-ref follow-up, not owner material, command execution proof, or real delivery proof.

### Validation

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` passed.
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet_http_export` passed: `Ran 2 tests in 36.046s OK`.
- Required marker `rg` passed for `cloud_command_lifecycle_replay_acceptance_packet_http_export`, `safe_command_id`, `safe_evidence_ref`, `delivery_success`, `primary_actions_enabled`, `safe_to_control`, `PRRT_kwDOSWB9286CJ3tX`, and `hardware_material_pending`.
- Scoped `git diff --check` passed for Robot/API touched files and this sprint `tech-done.md`.

### Failure localization

- Robot found a compatibility gap: the HTTP export had safe metadata nested under source packet/export structures, but the top-level HTTP payload did not explicitly expose `safe_command_id` / `safe_evidence_ref` for mobile/support consumers.
- The fix was intentionally minimal: add pending-safe placeholders and pass them through the export payload without enabling replay, ACK mutation, cursor mutation, GitHub mutation, Nav2 control, WAVE ROVER/UART access, HIL proof, or delivery success.

### Remaining risk

- Pending IDs are placeholders that point support/field owner work toward same-safe-ref material collection; they are not real owner materials and not a verified command execution result.
- This remains `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate` / HTTP export compatibility only.
- It is not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not HIL, not WAVE ROVER/UART proof, not PR #5 resolved, not delivery success, and not verified terminal delivery/dropoff/cancel result.

## Task C - Product Closeout and OKR Update

### User value and product north star

普通手机用户、field owner 和 support reviewer 现在能在 `mobile/web` 的只读支持面板里看到同一份 command lifecycle acceptance packet 的安全摘要、ACK accepted/processing 语义、terminal result pending、owner handoff、下一步证据需求和 false-state flags。产品北极星仍是低成本 ROS2 自主垃圾投递机器人；本轮只是把 O5 support export 变成手机/支持视图可理解的保守解释层，不把 local/Docker proof 说成真实云、真实手机或真实送达。

### OKR mapping and KR split

- Objective 5：最低 Objective 仍约 68%。本轮把 `cloud_command_lifecycle_replay_acceptance_packet_http_export` 推进到 `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`，属于 O5 KR1/KR6 的 support-surface 和 graceful-degradation 可读性增强。
- Objective 4：获得手机界面可解释性补强，但没有真实手机/browser 设备验收，所以不提升 Objective 4。
- Objective 1/2/3：没有改变硬件、HIL、WAVE ROVER/UART、Nav2/fixed-route、task_orchestrator、route/elevator field pass 或 delivery result。
- 本轮核心抓手：保留 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，并让 support/mobile 看到为什么主操作继续禁用。

### Final fenced validation

- `node --check mobile/web/app.js` passed.
- `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json` passed.
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel` passed.
- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` passed.
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet_http_export` passed.
- Required closeout file check passed for `tech-done.md`, `side2side_check.md`, and `final.md`.
- Required marker `rg` passed for `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`, `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`, `Objective 5`, `not true phone/browser proof`, `no OKR percentage lift`, `not delivery success`, `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Scoped `git diff --check` passed for all touched sprint, OKR, process, product, mobile, and Robot files.
- `git diff --cached --check` passed after staging selected files.

### Failure localization

- Task A first failed on unsafe fixture copy containing `raw diagnostics` / `GitHub mutation`; it was fixed by replacing it with phone-safe wording and rerunning targeted validation.
- Task B found and fixed the top-level HTTP export safe ID compatibility gap described above.
- Product closeout validation did not require implementation changes beyond allowed closeout/OKR/progress files.

### Remaining risk

- Objective 5 remains about 68%; no OKR percentage lift.
- This is not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not HIL, not WAVE ROVER/UART proof, not PR #5 resolved, not route/elevator field pass, not Nav2/fixed-route runtime proof, not verified terminal delivery/dropoff/cancel result, and not delivery success.
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`.
