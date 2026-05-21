# Verified Terminal Result Material Intake Pre Start

Run time: 2026-05-22 04:05 Asia/Shanghai

## Sprint Declaration

- sprint_type: epic
- capability: `verified_terminal_result_material_intake`
- evidence_boundary: `software_proof_docker_verified_terminal_result_material_intake_gate`
- target sprint path: `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/`
- current host boundary: Docker-only local environment, no real hardware, no real route/elevator/phone/cloud/HIL/delivery proof.

## User Value And North Star

North star: ordinary phone users and support owners must be able to determine whether a delivery, dropoff, or cancel result is genuinely verified before any product surface implies task completion.

This sprint moves from "missing material escalation" to a concrete intake gate. A field owner can provide a terminal result evidence bundle, and the system will validate the same safe `evidence_ref`, result type, required materials, and no-overclaim fields before producing a safe summary. Until real material is supplied and accepted, all surfaces remain `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## Evidence Inputs

- `OKR.md` 4.1 says Objective 5 remains lowest at about 68%.
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/final.md` says not to keep stacking local O5 metadata; next progress needs real external proof or verified terminal delivery/dropoff/cancel result.
- PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending; PR #6 has no review threads.
- Objective 1 real hardware materials cannot be produced on this Docker-only host.
- `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/final.md` already escalated missing materials. This sprint must not create another generic blocker wrapper.

## Blocker Scan

The recent repeated blocker is missing real-world materials: O5 external proof, O1 hardware/HIL proof, and O2/O3/O4 route/elevator/phone field proof. This sprint does not consume that blocker again as a status wrapper. It creates a specific material intake capability so the next owner-provided terminal result bundle can be checked and summarized without enabling control or claiming success.

## Sprint Goal

Create a software-proof, fail-closed intake path for field-owner terminal result evidence bundles:

1. Accept a JSON evidence bundle for terminal `delivery`, `dropoff`, or `cancel` result review.
2. Validate one safe `evidence_ref` across bundle, task record, route/elevator materials, command lifecycle, and terminal result fields.
3. Reject missing required materials, unsafe fields, raw artifacts, credentials, local paths, ROS/control details, and success overclaims.
4. Emit a phone-safe summary artifact for Robot diagnostics and mobile/web display.
5. Keep all primary actions disabled and all success/control flags false unless future real materials are provided and separately verified.

## Owner Routing

- Autonomy Algorithm Engineer owns the PC evidence intake CLI and summary artifact.
- Robot Platform Engineer owns diagnostics/status safe alias integration.
- User Touchpoint Full-Stack Engineer owns the mobile/web read-only panel and safe copy behavior.
- Product Manager / OKR Owner owns sprint closeout, OKR/progress evidence language, and no-overclaim review.

## Scope Boundary

In scope for implementation:

- New or extended PC evidence intake CLI for `verified_terminal_result_material_intake`.
- Robot diagnostics/status safe summary alias.
- Mobile/web read-only panel with safe copy only.
- Related docs under `docs/interfaces/` and `docs/product/`.
- Sprint closeout docs after worker evidence exists.

Out of scope:

- No production cloud, OSS/CDN, public HTTPS/TLS, 4G/SIM, production DB/queue, worker/cutover proof.
- No real phone/browser/device proof.
- No route/elevator/Nav2/fixed-route field pass.
- No WAVE ROVER/UART/HIL, serial device, hardware config, launch parameter, or vendor material change.
- No Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, or control enablement.
- No `OKR.md` percentage increase unless real materials are provided and verified during closeout.

## Required Sprint Documents

This Epic sprint must create and then complete the full chain:

1. `pre_start.md`
2. `prd.md`
3. `tech-plan.md`
4. `tech-done.md`
5. `side2side_check.md`
6. `final.md`

This planning task creates only the first three files. Implementation workers must update `tech-done.md`; Product closeout must update `side2side_check.md`, `final.md`, and only then decide whether `OKR.md` changes are justified.

