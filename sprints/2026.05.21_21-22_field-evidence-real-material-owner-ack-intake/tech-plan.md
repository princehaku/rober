# Field Evidence Real Material Owner Ack Intake Tech Plan

Run time: 2026-05-21 21:22 CST

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5 百分比提升。
3. 原因：最新 19-20 和 20-21 sprint 已连续落地 O5 local metadata / command-safety proof；当前缺口需要真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser evidence，本机 Docker-only 无法提供。继续做第三个泛 O5 wrapper 会违反 recent final 的 stop rule。
4. 次低 Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending，comment `3269642220` 只是 software-proof publication；本机没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/mounting/wiring/power/calibration/HIL-entry 或 WAVE ROVER/UART/HIL materials。
5. 本 sprint 选择 Objective 2/3/4 field-material owner acknowledgement intake，承接 `field_evidence_real_material_followup_escalation_status`，推动真实材料回填链路，而不是提高 O1/O5 百分比。

## Target Contract

Capability:

`field_evidence_real_material_owner_ack_intake`

Schemas:

- `trashbot.field_evidence_real_material_owner_ack_intake.v1`
- `trashbot.field_evidence_real_material_owner_ack_intake_summary.v1`
- `trashbot.robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary.v1`

Proof boundary:

`software_proof_docker_field_evidence_real_material_owner_ack_intake_gate`

Required false states:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## Workstream A: Autonomy PC Gate

Owner: `autonomy-engineer`

Allowed files:

- `pc-tools/evidence/field_evidence_real_material_owner_ack_intake.py`
- `pc-tools/evidence/test_field_evidence_real_material_owner_ack_intake.py`
- `docs/interfaces/evidence_contracts.md`
- `pc-tools/README.md`

Implementation:

- Add a dependency-free PC gate that reads source escalation summary/artifact and an owner acknowledgement packet.
- Preserve same safe `evidence_ref`; fail closed on mismatch, missing ack, unsupported schema, unsafe copy, raw paths, credentials, checksums, raw serial/UART/ROS details, success claims, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true`.
- Emit accepted/missing/rejected/blocked evidence categories and owner next steps.

Validation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/field_evidence_real_material_owner_ack_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools.evidence.test_field_evidence_real_material_owner_ack_intake
python3 pc-tools/evidence/field_evidence_real_material_owner_ack_intake.py --help
rg -n "field_evidence_real_material_owner_ack_intake|software_proof_docker_field_evidence_real_material_owner_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" pc-tools/evidence docs/interfaces/evidence_contracts.md pc-tools/README.md
git diff --check -- pc-tools/evidence/field_evidence_real_material_owner_ack_intake.py pc-tools/evidence/test_field_evidence_real_material_owner_ack_intake.py docs/interfaces/evidence_contracts.md pc-tools/README.md
```

## Workstream B: Robot Diagnostics

Owner: `robot-software-engineer`

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`

Implementation:

- Add `summarize_field_evidence_real_material_owner_ack_intake` or equivalent safe alias path.
- Consume canonical summary from latest status/diagnostics, output `robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary`.
- Do not expose raw packets, local paths, credentials, ROS topics, serial/UART/WAVE ROVER details, HIL/pass wording, checksums, complete artifacts, success/control claims, or enabled action flags.

Validation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "field_evidence_real_material_owner_ack_intake|robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary|software_proof_docker_field_evidence_real_material_owner_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
```

## Workstream C: Mobile/Web Touchpoint

Owner: `full-stack-software-engineer`

Allowed files:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_owner_ack_intake.json`
- `docs/product/mobile_user_flow.md`

Implementation:

- Add a read-only panel for `robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary`.
- Render owner ack status, safe `evidence_ref`, acknowledged owner/time, accepted/missing/blocked next evidence, next action, rerun/backfill guidance, and safe copy.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled; do not add raw fetch, ACK/cursor, replay, resubmit, or robot control endpoints.

Validation:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_owner_ack_intake.json >/dev/null
rg -n "field_evidence_real_material_owner_ack_intake|software_proof_docker_field_evidence_real_material_owner_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_owner_ack_intake.json docs/product/mobile_user_flow.md
```

## Workstream D: Hardware Boundary Consultation

Owner: `hardware-engineer`

Allowed files:

- No write scope unless a clear boundary wording defect is found in docs. If writing becomes necessary, stop and report scope before editing.

Read and verify:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/product/production_hardware_boundary.md`
- PR #5 thread state from current handoff.

Validation:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|2D LiDAR|ToF|WAVE ROVER|UART|HIL" OKR.md docs/product/production_hardware_boundary.md docs/vendor/VENDOR_INDEX.md
```

## Product Closeout

Owner: `product-okr-owner`

Allowed files:

- `sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake/tech-done.md`
- `sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake/side2side_check.md`
- `sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Validation:

```bash
test -f sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake/tech-done.md
test -f sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake/side2side_check.md
test -f sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake/final.md
rg -n "field_evidence_real_material_owner_ack_intake|software_proof_docker_field_evidence_real_material_owner_ack_intake_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake
```
