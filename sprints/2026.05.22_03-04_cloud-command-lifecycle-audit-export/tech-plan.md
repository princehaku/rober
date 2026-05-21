# Cloud Command Lifecycle Audit Export Tech Plan

Run time: 2026-05-22 03:04 Asia/Shanghai

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，能力为 `cloud_command_lifecycle_audit_export`。
3. 本 sprint 不提高真实 proof 百分比：当前主机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal delivery/dropoff/cancel result。
4. 本 sprint 不是 route/elevator/material blocker wrapper 的重复消费。上一轮 `field_evidence_material_blocker_escalation_pack` 已完成材料缺失升级；本轮改做具体功能，把 command enqueue、robot poll/next-command、ACK lookup/accepted/processing、terminal-result pending 串成同一 safe `command_id` / `evidence_ref` 的 phone-safe audit/export timeline。

## Architecture Decision

新增能力 `cloud_command_lifecycle_audit_export` 是 O5 software-proof audit/export layer。

Data flow:

1. Robot/API 从已有 command/status/ACK safe state 生成 lifecycle audit summary。
2. Summary 绑定同一 safe `command_id` / `evidence_ref`，列出 phone-safe lifecycle timeline。
3. Operator diagnostics/status 暴露 Robot safe alias，保持 primary actions disabled。
4. Mobile/web 读取 safe alias 或兼容 nested summary，展示只读 panel，并只复制 backend 提供的 safe copy/export 文本。
5. Product closeout 只把它记录为 `software_proof_docker_cloud_command_lifecycle_audit_export_gate`，不写成真实 external proof 或 delivery success。

Required invariant:

- `capability=cloud_command_lifecycle_audit_export`
- `evidence_boundary=software_proof_docker_cloud_command_lifecycle_audit_export_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Forbidden behavior:

- 不读取或暴露 raw artifact、complete artifact、raw JSON、credentials、Authorization header、signed URL、DB/queue URL、local path、checksum、traceback。
- 不暴露 ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数或底盘控制细节。
- 不自动 replay/resubmit command，不调用 ACK/cursor mutation，不改变 Start Delivery / Confirm Dropoff / Cancel 授权。
- 不把 PR #5 comment `3269642220` 当成 `PRRT_kwDOSWB9286CJ3tX` resolved。
- 不声明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、真实手机/browser、HIL、route/elevator field pass、verified terminal result、dropoff/cancel completion 或 delivery_success。

## Parallel Owner Plan

### Task A - Robot Platform Engineer

Role: `robot-software-engineer`

Goal: implement Robot/API diagnostics/status safe summary for `cloud_command_lifecycle_audit_export`.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/tech-done.md`

Interface requirements:

- Expose `robot_diagnostics_cloud_command_lifecycle_audit_export_summary`.
- Summary schema: `trashbot.cloud_command_lifecycle_audit_export_summary.v1`.
- Required safe fields: safe `command_id`, safe `evidence_ref`, `lifecycle_timeline`, `terminal_result_status`, `next_required_evidence`, `copy_export_text`, evidence boundary, and fixed safety fields.
- Missing or conflicting lifecycle state must fail closed as `not_proven`.
- No runtime control authorization changes.
- All new technical comments in code must be Chinese and meaningful.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_http onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "cloud_command_lifecycle_audit_export|software_proof_docker_cloud_command_lifecycle_audit_export_gate|robot_diagnostics_cloud_command_lifecycle_audit_export_summary|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
```

### Task B - User Touchpoint Full-Stack Engineer

Role: `full-stack-software-engineer`

Goal: implement mobile/web read-only lifecycle audit/export panel, fixture, styles, and docs.

Allowed files:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_audit_export.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/tech-done.md`

Interface requirements:

- Consume `robot_diagnostics_cloud_command_lifecycle_audit_export_summary`, `cloud_command_lifecycle_audit_export_summary`, or compatible nested diagnostics/status summary.
- Render only safe `command_id`, safe `evidence_ref`, lifecycle timeline, terminal result status, next required evidence, safe copy/export text, evidence boundary, `not_proven`, and fixed safety fields.
- Copy/export button is enabled only when backend-provided `copy_export_text` is present and safe; missing safe copy renders blocked/not_proven.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- Panel must not fetch raw diagnostics, command routes, ACK routes, cursor routes, raw artifacts, or replay/resubmit commands.
- All new technical comments in code must be Chinese and meaningful.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_audit_export.json >/tmp/mobile_cloud_command_lifecycle_audit_export_fixture.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "cloud_command_lifecycle_audit_export|software_proof_docker_cloud_command_lifecycle_audit_export_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|command_id|evidence_ref" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
```

### Task C - Hardware Infra Engineer Read-only Consultation

Role: `hardware-engineer`

Goal: prevent O1/HIL/PR #5 overclaim while Robot and Full-Stack implement O5 software-proof audit/export.

Allowed files:

- `docs/product/production_hardware_boundary.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/tech-done.md`

Read-only required sources:

- `docs/vendor/VENDOR_INDEX.md`
- Local vendor files referenced by `docs/vendor/VENDOR_INDEX.md` only if quoting hardware facts.
- Planning evidence: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, `PRRT_kwDOSWB9286CJ3tX` unresolved/material pending, comment `3269642220` software-proof publication only.

Boundary requirements:

- State clearly that this sprint does not prove WAVE ROVER/UART/HIL, real serial, 2D LiDAR/ToF source/procurement/install/calibration, route/elevator field pass, dropoff/cancel completion, verified terminal result, or delivery success.
- No hardware config changes.
- No hardware smoke unless a real device appears; current host is Docker-only.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|2D LiDAR|ToF|HIL|cloud_command_lifecycle_audit_export|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" docs/vendor/VENDOR_INDEX.md docs/product/production_hardware_boundary.md sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
git diff --check -- docs/product/production_hardware_boundary.md sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
```

### Task D - Product Closeout

Role: `product-okr-owner`

Goal: integrate worker evidence, update OKR/progress log/sprint closeout, and preserve evidence boundaries.

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/tech-done.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/side2side_check.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/final.md`

Closeout requirements:

- If no real external materials are supplied, keep Objective 5 around 68%, Objective 1 around 81%, Objective 2/3/4 around 99%.
- Record this as `software_proof_docker_cloud_command_lifecycle_audit_export_gate`.
- Explicitly state `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Confirm docs/ synchronization for every behavior changed by Robot, Full-Stack, and Hardware.
- Confirm PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending unless live reviewer state changes.

Acceptance commands:

```bash
test -f sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/tech-done.md && test -f sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/side2side_check.md && test -f sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/final.md
rg -n "cloud_command_lifecycle_audit_export|software_proof_docker_cloud_command_lifecycle_audit_export_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
```

## Worker Dispatch Notes

Implementation must launch Task A, Task B, and Task C in parallel via `spawn_agent(agent_type=worker)` because file scopes are distinct. Task D runs after worker evidence returns. Robot owns schema arbitration if Robot/mobile summary names drift; Full-Stack must adjust only within mobile scope. Hardware remains read-only unless a boundary doc update is necessary.

Each worker prompt must include the five fixed sections from `AGENTS.md`: role system prompt, task, file scope, acceptance commands, output requirements. Workers must not revert unrelated local changes and must not broaden validation beyond the fenced commands unless a failure requires targeted diagnosis.

## Planning-doc Validation Commands

These commands validate only the planning docs created before worker dispatch:

```bash
test -f sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/pre_start.md && test -f sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/prd.md && test -f sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/tech-plan.md
rg -n "cloud_command_lifecycle_audit_export|software_proof_docker_cloud_command_lifecycle_audit_export_gate|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
git diff --check -- sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export
```

