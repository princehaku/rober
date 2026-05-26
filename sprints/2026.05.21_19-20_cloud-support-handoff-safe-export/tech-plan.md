# Cloud Support Handoff Safe Export Tech Plan

Run time: 2026-05-21 19:20 CST

## Goal

Build `cloud_support_handoff_safe_export` as a phone-safe support handoff/export capability for cloud-hosted/mobile degraded states. It must help support triage stale status, backoff, unreachable cloud, manual takeover, auth failure, media degradation, and pending ACK while preserving `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 次低 Objective：Objective 1，约 81%；Objective 2/3/4 均约 99%。
- 本 sprint 是否针对该最低 Objective：是，针对 Objective 5 的 cloud-hosted/mobile degraded-state support handoff/export。
- 为什么不提升 Objective 5 百分比：本机没有真实硬件，只有 Docker；本 sprint 不产生真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover、true phone/browser proof、HIL、route/elevator field pass 或 delivery success。
- PR / review 边界：PR #5 `PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；comment `3269642220` 只是 software-proof reply publication。PR #6 已 merged 但 README/docs-only，不提供 runtime/hardware/cloud proof。
- 本 sprint 的合法抓手：把已有云 degraded states 做成安全支持导出包，改善用户/支持协同；它是 `software_proof_docker_cloud_support_handoff_safe_export_gate`，不是 external cloud proof。
- `final.md` 收口时需复核：如果没有真实外部材料，Objective 5 仍保持约 68%；若实现落地，只记录支持体验能力进展和软件证明边界。

## Repeated Blocker Avoidance

The repeated blocker is missing real external cloud and true phone/browser proof. The previous final explicitly says not to repeat the same local software-proof wrapper.

This sprint avoids repeating that blocker by shipping a different functional surface: a safe support export bundle. It does not add another readiness label for its own sake. It packages the degraded-state context already shown to the user into a copyable, whitelisted support payload while primary actions remain disabled.

## Architecture

Downstream workers should keep the path metadata-only and fail-closed:

1. Robot/API emits a sanitized support export summary for cloud degraded states.
2. Full-Stack consumes only sanitized summaries and renders a read-only phone panel with copy/export action.
3. Autonomy reviews wording and evidence fields read-only so no route/elevator/Nav2/field-pass claim leaks into the support bundle.
4. Hardware reviews PR #5/vendor boundary read-only so no hardware/HIL claim leaks into the support bundle.
5. Product closes the sprint with conservative OKR and evidence language.

## Shared Contract

Required strings and flags:

- capability: `cloud_support_handoff_safe_export`
- evidence boundary: `software_proof_docker_cloud_support_handoff_safe_export_gate`
- source: `software_proof`
- proof status: `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- OKR references: Objective 5, Objective 1
- PR/review references: `PRRT_kwDOSWB9286CJ3tX`, `3269642220`

Recommended support export fields:

- `schema=trashbot.cloud_support_handoff_safe_export.v1`
- `schema_version=1`
- `capability=cloud_support_handoff_safe_export`
- `degradation_state`
- `blocked_reason`
- `support_next_step`
- `retry_hint`
- `ack_semantics`
- `redaction_status`
- `evidence_boundary=software_proof_docker_cloud_support_handoff_safe_export_gate`
- conservative boolean flags listed above

Forbidden export content:

- raw ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters;
- Authorization headers, bearer tokens, GitHub tokens, DB/queue URLs, OSS AK/SK, credential-bearing URLs;
- local paths, tracebacks, checksums, complete artifacts, raw robot responses, raw diagnostics, raw GitHub review bodies;
- success/control copy or any field implying delivery success, true cloud proof, true phone/browser proof, HIL, or field pass.

## Parallel Owner Plan

Default implementation launch: start 4 worker agents in parallel after this plan is accepted. Robot/API and Full-Stack own implementation. Autonomy and Hardware are read-only consultation. Product closeout happens after worker evidence lands.

### Robot/API Worker

Role id: `robot-software-engineer`

File range:

- May edit Robot/API diagnostics, safe summary, fixture, focused test, and related interface docs needed for `cloud_support_handoff_safe_export`.
- Must not edit mobile/web implementation, hardware configuration, vendor files, or sprint planning docs unless Product asks for closeout.

Task:

- Implement a sanitized safe support export summary for cloud degraded states.
- Include degraded state, blocked reason, support next step, retry hint, ACK semantics, redaction status, evidence boundary, and conservative flags.
- Ensure the export cannot expose raw diagnostics, credentials, ROS topics, serial/UART paths, WAVE ROVER details, DB/queue/OSS secrets, local paths, checksums, tracebacks, or success claims.

Acceptance commands:

```bash
python3 -m py_compile <robot_changed_python_files>
python3 -m unittest <focused_robot_tests>
rg -n "cloud_support_handoff_safe_export|software_proof_docker_cloud_support_handoff_safe_export_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" <robot_changed_files>
git diff --check -- <robot_changed_files>
```

### Full-Stack Worker

Role id: `full-stack-software-engineer`

File range:

- May edit `mobile/web/`, mobile fixtures, focused mobile tests, and phone-facing product/interface docs needed for the read-only support export panel.
- Must not enable Start Delivery, Confirm Dropoff, Cancel, ACK/cursor request, retry, replay, resubmit, GitHub action, or robot command side effect.

Task:

- Add a read-only mobile/web panel for `cloud_support_handoff_safe_export`.
- Consume only sanitized Robot/API summaries.
- Let the user copy/export a phone-safe support bundle.
- Keep controls disabled through `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest <focused_mobile_tests>
rg -n "cloud_support_handoff_safe_export|software_proof_docker_cloud_support_handoff_safe_export_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" mobile/web <mobile_test_files>
git diff --check -- mobile/web <mobile_test_files>
```

### Autonomy Read-Only Worker

Role id: `autonomy-engineer`

File range:

- Read-only consultation unless Product explicitly changes scope.
- May inspect route/elevator/navigation docs and current degraded-state copy.
- Must not edit nav, behavior, mobile, hardware, or sprint planning files in this consultation task.

Task:

- Verify the planned support export cannot be read as real route/elevator field pass, Nav2/fixed-route proof, route completion signal, dropoff/cancel completion, delivery result, or delivery success.
- Provide exact wording guardrails for support bundle labels if needed.

Acceptance commands:

```bash
rg -n "route completion|fixed-route|Nav2|elevator|delivery_success=false|not_proven|safe_to_control=false" docs/product docs/interfaces OKR.md
```

### Hardware Read-Only Worker

Role id: `robot-hardware-engineer`

File range:

- Read-only consultation only.
- Must read `docs/vendor/VENDOR_INDEX.md` and relevant local vendor files before stating hardware facts.
- Must not edit hardware code, launch parameters, vendor files, hardware configuration, mobile, Robot/API, or sprint planning files in this consultation task.

Task:

- Confirm PR #5 `PRRT_kwDOSWB9286CJ3tX` remains hardware-material pending.
- Confirm comment `3269642220` is only software-proof reply publication.
- Confirm support export copy must not claim real 2D LiDAR / ToF material, WAVE ROVER/UART proof, HIL, installation, wiring, power, calibration, or reviewer resolution.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "WAVE ROVER|UART|ToF|LiDAR|2D LiDAR|PRRT_kwDOSWB9286CJ3tX|3269642220" docs/vendor docs/product OKR.md
```

### Product Closeout Worker

Role id: `product-okr-owner`

File range:

- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/tech-done.md`
- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/side2side_check.md`
- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/final.md`
- `OKR.md` only if worker evidence lands and progress snapshot needs conservative closeout.
- `docs/process/okr_progress_log.md` only if `OKR.md` is updated.

Task:

- Verify worker outputs and evidence boundaries.
- Confirm `cloud_support_handoff_safe_export` is recorded as Docker/local software proof only.
- Keep Objective 5 percentage unchanged unless real external proof arrives.
- Ensure docs under `docs/` are updated by implementation owners if product/API/mobile behavior changes.

Acceptance commands:

```bash
test -f sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/tech-done.md
test -f sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/side2side_check.md
test -f sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/final.md
rg -n "cloud_support_handoff_safe_export|software_proof_docker_cloud_support_handoff_safe_export_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_19-20_cloud-support-handoff-safe-export OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.21_19-20_cloud-support-handoff-safe-export OKR.md docs/process/okr_progress_log.md
```

## Main-Node Dispatch Requirements

When implementation starts, dispatch these worker agents in parallel:

- `robot-software-engineer` for Robot/API safe support export summary.
- `full-stack-software-engineer` for mobile/web copy/export panel.
- `autonomy-engineer` for read-only route/elevator/navigation non-claim review.
- `robot-hardware-engineer` for read-only PR #5/vendor-boundary review.

Each prompt must include role System Prompt, task, file range, acceptance commands, and output requirements. Workers are not alone in the codebase and must not revert others' edits.

## Planning-Step Validation

Planning-only validation:

```bash
test -f sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/pre_start.md
test -f sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/prd.md
test -f sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|cloud_support_handoff_safe_export|software_proof_docker_cloud_support_handoff_safe_export_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_19-20_cloud-support-handoff-safe-export
git diff --check -- sprints/2026.05.21_19-20_cloud-support-handoff-safe-export
```

## Non-Goals

- Do not update `OKR.md` during this planning step.
- Do not edit product code, test code, mobile files, onboard files, vendor files, hardware config, launch params, interface docs, or product docs during this planning step.
- Do not claim real external cloud proof, real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, HIL, WAVE ROVER/UART proof, route/elevator field pass, dropoff/cancel completion, delivery result, PR #5 resolution, or delivery success.
