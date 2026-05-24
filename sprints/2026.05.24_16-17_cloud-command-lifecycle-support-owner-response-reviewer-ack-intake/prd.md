# PRD - Cloud command lifecycle support owner-response reviewer ACK intake

- sprint_type: epic
- sprint: `2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate`

## User Value

Support and field-owner reviewers need a safe way to acknowledge the latest cloud command lifecycle owner-response review handoff without making the phone surface look actionable. The value is a clear reviewer ACK intake state that says who acknowledged, what still blocks progress, and why controls remain disabled.

## Product North Star

The phone-facing cloud command lifecycle remains support-safe and fail-closed. A normal user can see that the command lifecycle is waiting on reviewer/owner material without seeing raw cloud, ROS, serial, hardware, or GitHub implementation details.

## Evidence Basis

- Current `OKR.md` keeps Objective 5 lowest at about 68%.
- Latest O5 sprint closed the owner-response review-handoff rung as `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate`.
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint must not turn that into PR #5 resolution.
- PR #7 has no review threads/comments and does not add an actionable review blocker.

## Acceptance

- Robot/API exposes a safe summary alias for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`.
- `mobile/web` displays a read-only panel after the review-handoff panel.
- The panel and safe summary preserve one safe command id, one safe `evidence_ref`, reviewer ACK status, source handoff status, owner/support/reviewer routing, ACK reasons, next required evidence, proof boundary, and fail-closed flags.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- `OKR.md` remains conservative unless real external materials appear; expected result is no OKR percentage lift.

## Non-Goals

- No command replay/resubmit.
- No ACK cursor mutation.
- No owner-response submission.
- No review/handoff mutation.
- No GitHub mutation or thread resolution.
- No raw material upload/fetch.
- No Nav2, WAVE ROVER, UART, `/cmd_vel`, HIL, or delivery proof.
