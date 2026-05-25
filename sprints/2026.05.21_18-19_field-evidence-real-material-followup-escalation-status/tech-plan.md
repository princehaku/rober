# Field Evidence Real Material Followup Escalation Status Tech Plan

Run time: 2026-05-21 18:05 CST

## Goal

Build `field_evidence_real_material_followup_escalation_status` as a software-proof escalation-status rung that converts the 17-18 handoff output into field-owner owner/SLA/next-action/missing-evidence/blocked-reason status while preserving `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否，不能作为 O5 completion sprint。
- 理由：Objective 5 当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/cutover 和真实手机/browser 证据；`OKR.md` 明确要求没有真实外部材料时不要继续堆 O5 metadata depth。
- 次低且相关 Objective：Objective 1，约 81%，但 PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；comment `3269642220` 只是 `software_proof` reply publication，不是 reviewer resolution、真实硬件材料、WAVE ROVER/UART proof 或 HIL。
- 本 sprint 的合法抓手：将 17-18 handoff 输出升级成 field-owner escalation status，推动 O2/O3/O4 真实 field material 获取链路，避免重复 generic wrapper。
- `final.md` 收口时需复核：若真实 O5/O1/field materials 仍未到位，OKR 百分比应保持保守；若真实材料到位，只能按对应证据边界更新。

## Repeated Blocker Avoidance

This sprint is not another generic blocked wrapper. The repeated blocker is missing real field / hardware / external proof. The new capability must make the next non-repo action explicit:

- owner: who must provide or review the material;
- SLA / due status: whether it is due, overdue, blocked, or waiting on field owner;
- next required evidence: exact material names;
- blocked reason: why current claim remains `not_proven`;
- rerun/backfill guidance: what command or process the field owner should run after real materials exist;
- safe phone copy: why controls remain disabled.

## Architecture

Downstream workers should keep the flow metadata-only and fail-closed:

1. Autonomy defines field-evidence escalation groups and route/elevator material semantics.
2. Robot emits a sanitized summary and gate output with `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate`.
3. Full-Stack consumes only sanitized summaries in a read-only panel and keeps Start Delivery / Confirm Dropoff / Cancel disabled.
4. Hardware performs read-only consultation for PR #5 / vendor-source material status and must not edit hardware configuration.
5. Product closes the sprint after worker evidence lands and updates sprint closeout docs plus conservative `OKR.md` / progress log if applicable.

## Shared Contract

Required strings and flags:

- capability: `field_evidence_real_material_followup_escalation_status`
- evidence boundary: `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate`
- source: `software_proof`
- proof status: `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- PR/review evidence: `PRRT_kwDOSWB9286CJ3tX`, `3269642220`
- OKR references: Objective 5, Objective 1

Required missing material groups:

- O5 external: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/cutover, true phone/browser evidence.
- O1 / PR #5 hardware: real 2D LiDAR SKU/source/receipt, real ToF SKU/source/channel material, mounting/wiring/power plan, calibration material, HIL-entry, WAVE ROVER/UART/HIL logs.
- Route/elevator field evidence: real task record, `nav2_fixed_route_runtime_log`, route completion signal, elevator door state, target floor confirmation, human assistance note, dropoff/cancel completion, delivery result, same safe `evidence_ref`.
- O4 real phone: real iPhone/Android behavior, production app, PWA prompt/userChoice, true phone/browser evidence.

## Parallel Worker Plan

Default launch: start 4 worker agents in parallel after this plan is accepted. Hardware is read-only consultation.

### Autonomy Worker

Role id: `autonomy-engineer`

File range:

- May edit Autonomy-owned route/elevator software-proof files only after implementation begins.
- Must not edit this planning sprint unless asked by Product closeout.
- Expected implementation surfaces should stay in `pc-tools/evidence/`, route/elevator diagnostics fixtures, and related docs already owned by Autonomy.

Task:

- Define the route/elevator field evidence escalation taxonomy consumed by `field_evidence_real_material_followup_escalation_status`.
- Include real task record, Nav2/fixed-route runtime log, route completion signal, door state, target floor confirmation, human assistance note, dropoff/cancel completion, delivery result, and same safe `evidence_ref`.
- Keep every output `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

Acceptance commands:

```bash
python3 -m py_compile <autonomy_changed_python_files>
python3 -m unittest <focused_autonomy_tests>
rg -n "field_evidence_real_material_followup_escalation_status|software_proof_docker_field_evidence_real_material_followup_escalation_status_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" <autonomy_changed_files>
git diff --check -- <autonomy_changed_files>
```

### Robot Worker

Role id: `robot-software-engineer`

File range:

- May edit Robot diagnostics, gate, fixture, and focused test files needed to expose the sanitized escalation status.
- Must not edit hardware configuration, vendor files, or product planning docs unless Product asks for closeout.

Task:

- Implement or wire a sanitized Robot diagnostics summary for `field_evidence_real_material_followup_escalation_status`.
- Ensure the summary includes owner, due status, next required evidence, blocked reason, escalation level, rerun/backfill guidance, and safe flags.
- Ensure the summary rejects or redacts raw artifacts, credentials, ROS topics, serial/UART paths, WAVE ROVER details, local paths, checksums, tracebacks, and success claims.

Acceptance commands:

```bash
python3 -m py_compile <robot_changed_python_files>
python3 -m unittest <focused_robot_tests>
rg -n "field_evidence_real_material_followup_escalation_status|software_proof_docker_field_evidence_real_material_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" <robot_changed_files>
git diff --check -- <robot_changed_files>
```

### Full-Stack Worker

Role id: `full-stack-software-engineer`

File range:

- May edit `mobile/web/`, mobile fixtures, focused mobile tests, and phone-facing docs needed for the read-only escalation status surface.
- Must not enable Start Delivery, Confirm Dropoff, or Cancel.

Task:

- Add a read-only phone-safe panel for `field_evidence_real_material_followup_escalation_status`.
- Consume only sanitized Robot/status summaries.
- Show owner, SLA/due status, next required evidence, blocked reason, escalation level, and safe copy.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled through `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest <focused_mobile_tests>
rg -n "field_evidence_real_material_followup_escalation_status|software_proof_docker_field_evidence_real_material_followup_escalation_status_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" mobile/web <mobile_test_files>
git diff --check -- mobile/web <mobile_test_files>
```

### Hardware Worker

Role id: `rober-hardware-engineer`

File range:

- Read-only consultation only.
- Must read `docs/vendor/VENDOR_INDEX.md` and relevant local vendor files before stating hardware facts.
- Must not edit hardware code, launch parameters, vendor files, or hardware configuration in this sprint unless real materials are supplied and Product explicitly changes scope.

Task:

- Confirm PR #5 `PRRT_kwDOSWB9286CJ3tX` remains hardware-material pending from repo-local and live review evidence.
- Confirm comment `3269642220` / published reply is only software-proof reply publication.
- List exactly what real material would be required before this can become O1 hardware proof.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "WAVE ROVER|UART|ToF|LiDAR|2D LiDAR|PRRT_kwDOSWB9286CJ3tX|3269642220" docs/vendor docs/product OKR.md
```

### Product Closeout Worker

Role id: `product-okr-owner`

File range:

- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/tech-done.md`
- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/final.md`
- `OKR.md` only if worker evidence lands and progress snapshot needs conservative closeout.
- `docs/process/okr_progress_log.md` only if `OKR.md` is updated.

Task:

- Verify all worker evidence and failure boundaries.
- Confirm `OKR.md` progress remains conservative unless real materials arrive.
- Write final sprint closeout with actual changed files, validation output, remaining risk, and no success overclaim.

Acceptance commands:

```bash
test -f sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/tech-done.md
test -f sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/side2side_check.md
test -f sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/final.md
rg -n "field_evidence_real_material_followup_escalation_status|software_proof_docker_field_evidence_real_material_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|3269642220|Objective 5|Objective 1|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status OKR.md docs/process/okr_progress_log.md
```

## Main-Node Dispatch Requirements

When implementation starts, dispatch 4 parallel worker agents in one batch:

- `autonomy-engineer`
- `robot-software-engineer`
- `full-stack-software-engineer`
- `rober-hardware-engineer` read-only consultation

Each prompt must include the role System Prompt, task, file range, acceptance commands, and output requirements. Workers are not alone in the codebase and must not revert others' edits.

## Validation For This Planning Step

Planning-only validation:

```bash
test -f sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/pre_start.md
test -f sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/prd.md
test -f sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_real_material_followup_escalation_status|software_proof_docker_field_evidence_real_material_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|3269642220|Objective 5|Objective 1|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status
git diff --check -- sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status
```

## Non-Goals

- Do not update `OKR.md` during this planning step.
- Do not edit product code, tests, mobile files, onboard files, vendor files, hardware config, launch params, or docs/interface during this planning step.
- Do not claim real field pass, real phone/browser proof, HIL, WAVE ROVER/UART proof, Objective 5 external proof, PR #5 resolution, delivery result, or delivery success.
