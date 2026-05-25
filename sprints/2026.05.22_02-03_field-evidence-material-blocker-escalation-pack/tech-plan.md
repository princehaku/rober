# Field Evidence Material Blocker Escalation Pack Tech Plan

Run time: 2026-05-22 02:03 Asia/Shanghai

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，但不继续做 O5 本地 metadata depth；它把 O5 缺真实 external proof / verified terminal result 的阻塞，与 O1/O2/O3/O4 的真实材料缺口一起升级为 field owner / CEO 可执行 blocker escalation pack。
3. 不直接提高 Objective 5 的理由：当前主机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 或 verified terminal delivery/dropoff/cancel result。继续添加本地 wrapper 会重复消费同一 blocker。

## Architecture Decision

新增能力 `field_evidence_material_blocker_escalation_pack` 是一个 software-proof escalation layer，不是 runtime delivery proof。

数据流：

1. Autonomy PC gate 读取上一轮 owner ack review decision 或 material followup/review chain 的 safe summary/reference。
2. PC gate 输出 `trashbot.field_evidence_material_blocker_escalation_pack.v1` artifact 和 summary。
3. Robot diagnostics 暴露 `robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary` 安全别名。
4. Mobile/web 只读 panel 展示 target owner、blocked reason、owner escalation level、next required evidence 和 field-safe copy。
5. Product closeout 核对 OKR、docs、sprint evidence，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

禁止行为：

- 不读取 raw artifact。
- 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、真实云、OSS/CDN、DB/queue 或 4G。
- 不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- 不把 PR #5 comment `3269642220` 当成 `PRRT_kwDOSWB9286CJ3tX` resolved。
- 不声明 HIL、真实 cloud、真实 phone/browser、route/elevator field pass、dropoff/cancel completion 或 delivery success。

## Parallel Owner Plan

### Task A - Autonomy Engineer

Role: `autonomy-engineer`

Goal: build PC evidence gate and fixtures for `field_evidence_material_blocker_escalation_pack`.

Allowed files:

- `pc-tools/evidence/field_evidence_material_blocker_escalation_pack.py`
- `pc-tools/evidence/test_field_evidence_material_blocker_escalation_pack.py`
- `pc-tools/evidence/fixtures/field_evidence_material_blocker_escalation_pack/*.json`
- `docs/product/elevator_assisted_delivery.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/tech-done.md`

Interface requirements:

- Output schema: `trashbot.field_evidence_material_blocker_escalation_pack.v1`
- Summary schema: `trashbot.field_evidence_material_blocker_escalation_pack_summary.v1`
- Evidence boundary: `software_proof_docker_field_evidence_material_blocker_escalation_pack_gate`
- Required safe fields: `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`
- Required product fields: `next_required_evidence`, `owner_escalation_level`, `blocked_reason`, `target_owner`, `field_safe_copy`

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_blocker_escalation_pack.py pc-tools/evidence/test_field_evidence_material_blocker_escalation_pack.py
python3 -m unittest pc-tools.evidence.test_field_evidence_material_blocker_escalation_pack
python3 -m json.tool pc-tools/evidence/fixtures/field_evidence_material_blocker_escalation_pack/blocked_all_real_materials_missing.json >/tmp/field_escalation_fixture.json
rg -n "field_evidence_material_blocker_escalation_pack|software_proof_docker_field_evidence_material_blocker_escalation_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|next_required_evidence|owner_escalation_level|blocked_reason|target_owner" pc-tools/evidence docs/product/elevator_assisted_delivery.md sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
git diff --check -- pc-tools/evidence docs/product/elevator_assisted_delivery.md sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
```

### Task B - Robot Platform Engineer

Role: `robot-software-engineer`

Goal: expose Robot diagnostics safe alias for the escalation pack summary without changing runtime control authorization.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_api.md`
- `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/tech-done.md`

Interface requirements:

- Add safe alias `robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary`.
- Preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Do not expose raw artifacts, local paths, credentials, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, baudrate, WAVE ROVER parameters, or raw JSON.
- Missing/unsupported summary must fail closed as `not_proven`.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary|field_evidence_material_blocker_escalation_pack|software_proof_docker_field_evidence_material_blocker_escalation_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
```

### Task C - User Touchpoint Full-Stack Engineer

Role: `full-stack-software-engineer`

Goal: add a read-only mobile/web panel for the escalation pack while keeping all primary actions disabled.

Allowed files:

- `mobile/web/app.js`
- `mobile/web/index.html`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_material_blocker_escalation_pack.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/tech-done.md`

Interface requirements:

- Consume `field_evidence_material_blocker_escalation_pack_summary`, `robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary`, or compatible nested diagnostics summary.
- Show only target owner, escalation level, blocked reason, next required evidence, field-safe copy, `not_proven`, and evidence boundary.
- Missing summary renders blocked/not_proven.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled; no command/ACK/cursor route is called by this panel.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_material_blocker_escalation_pack.json >/tmp/mobile_field_escalation_fixture.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "field_evidence_material_blocker_escalation_pack|software_proof_docker_field_evidence_material_blocker_escalation_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|next_required_evidence|owner_escalation_level|blocked_reason|target_owner" mobile docs/product/mobile_user_flow.md sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
git diff --check -- mobile docs/product/mobile_user_flow.md sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
```

### Task D - Hardware Infra Engineer Read-only Consultation

Role: `rober-hardware-engineer`

Goal: confirm hardware/source boundaries for PR #5 material pending and prevent HIL or sensor material overclaim.

Allowed files:

- `docs/product/production_hardware_boundary.md`
- `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/tech-done.md`

Read-only required sources:

- `docs/vendor/VENDOR_INDEX.md`
- Local vendor files referenced by `docs/vendor/VENDOR_INDEX.md` only if hardware facts are quoted.
- GitHub PR #5 thread state from planning evidence: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, `PRRT_kwDOSWB9286CJ3tX` unresolved/material pending, comment `3269642220` software-proof only.

Interface requirements:

- Document that current vendor tree does not prove project 2D LiDAR/ToF source, receipt, installation, wiring, power, calibration, HIL-entry, Nav2 field pass, route/elevator pass, or delivery result.
- No hardware config changes.
- No serial/UART/HIL smoke unless real device appears; current host is Docker-only.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|2D LiDAR|ToF|HIL|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" docs/vendor/VENDOR_INDEX.md docs/product/production_hardware_boundary.md sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
git diff --check -- docs/product/production_hardware_boundary.md sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
```

### Task E - Product Closeout

Role: `product-okr-owner`

Goal: integrate worker evidence, update sprint closeout docs, and preserve OKR evidence boundaries.

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/tech-done.md`
- `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/side2side_check.md`
- `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/final.md`

Closeout requirements:

- If no real materials are supplied, keep Objective 5 around 68%, Objective 1 around 81%, Objective 2/3/4 around 99%.
- Record this as `software_proof_docker_field_evidence_material_blocker_escalation_pack_gate` only.
- Explicitly state `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Confirm docs/ synchronization for any feature behavior changed by workers.

Acceptance commands:

```bash
test -f sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/tech-done.md && test -f sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/side2side_check.md && test -f sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/final.md
rg -n "field_evidence_material_blocker_escalation_pack|software_proof_docker_field_evidence_material_blocker_escalation_pack_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
```

## Worker Dispatch Notes

The main node should launch Task A, B, C, and D in parallel via `spawn_agent(agent_type=worker)` because file scopes are distinct. Product closeout runs after worker evidence returns. If implementation reveals shared schema drift between PC gate, Robot diagnostics, and mobile panel, Robot owns interface arbitration and the other owners adjust within their scopes.

Each worker prompt must include the fixed five sections from `AGENTS.md`: role system prompt, task, file scope, acceptance commands, output requirements. Workers must not revert unrelated local changes and must not broaden validation beyond the fenced commands unless a failure requires targeted diagnosis.

## Planning-doc Validation Commands

These commands validate only the planning docs created before worker dispatch:

```bash
test -f sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/pre_start.md && test -f sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/prd.md && test -f sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/tech-plan.md
rg -n "field_evidence_material_blocker_escalation_pack|software_proof_docker_field_evidence_material_blocker_escalation_pack_gate|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
git diff --check -- sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack
```

