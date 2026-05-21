# Field Evidence Real Material Request Dispatch Pre-Start

Run time: 2026-05-21 14:15 CST

## Sprint Declaration

- sprint_type: epic
- capability: `field_evidence_real_material_request_dispatch`
- evidence boundary: `software_proof_docker_field_evidence_real_material_request_dispatch_gate`
- primary owner: Product Manager / OKR Owner
- implementation owners for the next execution stage:
  - Autonomy Algorithm Engineer: field evidence source taxonomy and Nav2/fixed-route material requirements.
  - Robot Platform Engineer: diagnostics-safe request artifact and Robot/API consumption boundary.
  - User Touchpoint Full-Stack Engineer: field-owner/mobile-readable request surface and true phone/browser evidence checklist.
  - Hardware Infra Engineer: elevator, human-assistance, and hardware-adjacent material evidence boundaries only; no new hardware claim.

## Background Evidence

- `OKR.md` 4.1 currently keeps Objective 5 at about 68%, the lowest numeric objective. The latest sprint `sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/final.md` closed only as `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`; it is not real external cloud proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not true phone/browser proof, not delivery result, and not delivery success.
- Objective 1 remains about 81%. PR #5 threads `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved, but `PRRT_kwDOSWB9286CJ3tX` remains unresolved and asks for mandatory sensor assumptions to cite vendor sources. Comment id `3269642220` was published, but it is only a software-proof reply publication and not reviewer resolution.
- The previous O2/O3/O4 field ladder sprint `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/final.md` already completed the acceptance backfill gate as `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate`. This sprint must not repeat another backfill wrapper.

## User Value And Product North Star

The user value is to stop asking field owners for vague "rerun evidence" and instead dispatch one executable real-material request that tells them exactly what to collect, how it must share the same safe `evidence_ref`, and which claims remain blocked until those materials arrive.

The product north star remains a trustworthy autonomous trash-delivery loop: a phone user can start, monitor, and complete a safe route/elevator/dropoff task only when real robot, route, elevator, cloud, and phone evidence match the same evidence chain. This sprint advances that north star by turning the evidence gap into a field-owner action package, not by claiming new robot capability.

## OKR Mapping

- Objective 5 stays the lowest at about 68%. It is not targeted for progress because required real external materials are unavailable: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/migration/cutover, production app/device, and true phone/browser evidence.
- Objective 1 stays about 81%. It is not targeted for progress because `PRRT_kwDOSWB9286CJ3tX` is unresolved and real 2D LiDAR / ToF source, receipt, procurement, installation, wiring, power, calibration, HIL-entry, WAVE ROVER/UART/HIL materials remain missing. Comment `3269642220` is not enough.
- Objectives 2/3/4 are near-complete but blocked on real field materials. This sprint targets the material request needed to convert O2/O3/O4 from software-proof readiness toward future real field acceptance.

## Core Lever

Read the safe evidence state from the previous acceptance backfill summary, then generate a field-owner executable request for:

- `task_record`
- `nav2_fixed_route_runtime_log`
- `route_completion_signal`
- `elevator_door_floor_evidence`
- `human_assistance_note`
- `dropoff_cancel_completion`
- `delivery_result`
- `true_phone_browser_evidence`
- `diagnostics_mobile_safe_summary`

The request must preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Scope Boundary

In scope for planning:

- Create planning docs that define the product requirement, KR split, execution owners, file scope, and acceptance commands for `field_evidence_real_material_request_dispatch`.
- Keep the sprint explicitly `software_proof_docker_field_evidence_real_material_request_dispatch_gate`.
- Make the next engineering work actionable without treating planning docs as business completion.

Out of scope:

- No product code, tests, hardware configuration, mobile UI, API, or diagnostics code changes in this planning task.
- No changes to `OKR.md` in this planning task; progress can be updated only after execution and evidence closeout.
- No claim of real phone/browser proof, real route/elevator field pass, HIL, WAVE ROVER/UART proof, O5 external cloud proof, PR #5 reviewer resolution, delivery result, or delivery success.

## Blocker Reuse Check

The last two relevant sprints did not solve the real-material absence:

- `field_evidence_rerun_execution_result_acceptance_backfill` completed the software-proof backfill gate.
- `cloud_hosted_mobile_web_degradation_passthrough` completed a hosted mobile degraded-state software proof.

Because repeating the backfill gate would consume the same blocker again, this sprint pivots to real-material request dispatch. The blocker is not ignored; it is converted into a concrete field-owner ask.

## Required Sprint Documents

This epic sprint starts with:

- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/pre_start.md`
- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/prd.md`
- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/tech-plan.md`

Execution closeout must later add:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
