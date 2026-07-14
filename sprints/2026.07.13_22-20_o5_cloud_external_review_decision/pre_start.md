# Pre Start - O5 Cloud External Evidence Review Decision

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_22-20_o5_cloud_external_review_decision/`
- Start time: 2026-07-13 22:20 CST
- Product owner: `product-okr-owner`
- Primary implementation owner: `full-stack-software-engineer`
- Target OKR: Objective 5, cloud relay control plane productionization

## Previous State

O5 remains the lowest current Objective at about `85%`. The latest O5 work produced a fail-closed CDN/TLS external evidence probe and then consumed that probe in the cutover readiness packet, but the public endpoint stayed `blocked_http_status_not_success_class` with HTTP `4xx`.

The latest sprint `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/` closed as O6/O7 support-only bounded route gate intake/readback. It explicitly recommended not repeating O6/O7 wrappers and returning only to O5 with stronger production evidence or to O1/O3 with explicit operator-approved live HIL/route evidence.

## Blocker Rotation

This sprint must not repeat:

- CDN/TLS 4xx probing while the public endpoint is still expected to return non-success.
- O5 readiness packet support-only aggregation without a new source slot.
- O6/O7 readback, bundle export, delivery-result, phone/browser terminal-material, bounded-route-gate, query-filter, mission-event, or inference wrappers.
- O1/O3 stop-path, mock stop HIL, route packet, gate, or bounded command plan packaging.

## Current Opportunity

The docs already describe `cloud_external_evidence_review_decision` as the O5 review step after `trashbot.external_evidence_intake`, and fixtures exist under `pc-tools/evidence/fixtures/cloud_external_evidence_review_decision/`. The script itself is missing, and the current O5 cutover readiness packet does not consume this review-decision artifact.

This is an actionable software gap that does not require real hardware, robot motion, credentials, production DB, real OSS/CDN, 4G/SIM, or live public endpoint success. The proof must remain local/software-only and fail closed.

## Expected Outcome

Create the missing local review-decision tool and connect its sanitized summary into O5 readiness consumption. This gives future real external materials a machine-readable review stage without claiming production readiness.

Accepted boundary:

- `software_proof_o5_cloud_external_evidence_review_decision_only`
- `delivery_success=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `hil_pass=false`
- `production_ready=false`
- `connects_cloud_production=false`
