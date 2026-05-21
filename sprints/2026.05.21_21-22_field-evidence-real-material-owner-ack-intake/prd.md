# Field Evidence Real Material Owner Ack Intake PRD

Run time: 2026-05-21 21:22 CST

## User Value

Field owners and support staff need a clear, phone-safe way to confirm they have received the real-material escalation and to state which evidence they can provide next. Without this intake, the current escalation status tells us what is missing, but not whether the responsible owner accepted the handoff or which rerun/backfill material should be collected under the same safe `evidence_ref`.

## North Star

普通用户仍只通过手机理解送垃圾任务状态和失败原因；现场 owner 和支持同学必须能围绕同一个 safe `evidence_ref` 收集真实 task record、route/elevator runtime、completion signal、dropoff/cancel completion、delivery result 和 true phone/browser evidence，而不是在聊天里散落材料。

## OKR Mapping

- Objective 2: prepares real task/elevator material handoff, but does not prove route/elevator pass.
- Objective 3: preserves same-`evidence_ref` Nav2/fixed-route runtime material requirements, but does not prove Nav2/fixed-route runtime.
- Objective 4: gives mobile/web a read-only owner acknowledgement panel, but does not prove true phone/browser acceptance.
- Objective 5: remains lowest but blocked by external materials; this sprint does not claim O5 progress.
- Objective 1: remains blocked by PR #5 real hardware/source/HIL materials; Hardware only verifies the boundary.

## Product Requirements

1. The PC gate accepts a safe `field_evidence_real_material_followup_escalation_status` artifact or summary plus an owner acknowledgement packet.
2. The output includes `owner_ack_status`, `acknowledged_by`, `acknowledged_at`, safe `evidence_ref`, accepted next evidence, missing next evidence, rejected/unsafe material, owner next action, rerun/backfill guidance, and phone-safe copy.
3. Unsupported schema, missing source escalation, missing owner acknowledgement, `evidence_ref` mismatch, unsafe raw material, credential/path/checksum leakage, or success/control claims must fail closed.
4. Robot diagnostics exposes only a sanitized `robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary` alias.
5. Mobile/web shows the acknowledgement intake as read-only status and keeps Start Delivery, Confirm Dropoff, and Cancel disabled.
6. Docs must state this is not real field pass, not true phone/browser proof, not HIL, not PR #5 resolution, not O5 external proof, not delivery result, and not delivery success.

## Acceptance Criteria

- `field_evidence_real_material_owner_ack_intake` and `software_proof_docker_field_evidence_real_material_owner_ack_intake_gate` appear in PC gate, Robot diagnostics, mobile/web, interface/product docs, sprint docs, `OKR.md`, and `docs/process/okr_progress_log.md`.
- Fenced validations run only targeted py_compile/unit/node checks and scoped diff checks.
- OKR percentages stay conservative unless real materials appear, which is not expected on this Docker-only host.

## Non-goals

- No new hardware facts.
- No HIL, WAVE ROVER, serial/UART, sensor SKU/source/receipt, purchase, wiring, mounting, power, calibration, or PR #5 reviewer-resolution claim.
- No external cloud proof, production queue proof, true phone/browser proof, field pass, completion proof, delivery result, or delivery success.
