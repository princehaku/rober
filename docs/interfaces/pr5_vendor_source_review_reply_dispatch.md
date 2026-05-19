# PR #5 Vendor Source Review Reply Dispatch

`pc-tools/evidence/pr5_vendor_source_review_reply_dispatch.py` converts the
03-04 `pr5_vendor_source_review_packet_summary.json` into a fail-closed,
manual GitHub review reply package for PR #5 unresolved review thread
`PRRT_kwDOSWB9286CJ3tX`.

- Artifact schema: `trashbot.pr5_vendor_source_review_reply_dispatch.v1`
- Summary schema: `trashbot.pr5_vendor_source_review_reply_dispatch_summary.v1`
- Evidence boundary:
  `software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate`
- Source packet boundary:
  `software_proof_docker_pr5_vendor_source_review_packet_gate`
- Required source entrypoint: `docs/vendor/VENDOR_INDEX.md`
- Required state: `source=software_proof`, `not_proven`,
  `hardware_material_pending`, `delivery_success=false`,
  `primary_actions_enabled=false`, and `safe_to_control=false`

The generated Markdown is reply-ready only for manual posting. It does not call
the GitHub write API, resolve `PRRT_kwDOSWB9286CJ3tX`, read serial/UART, query a
ROS graph, touch procurement systems, access cloud resources, or inspect real
hardware.

The reply may cite that local `docs/vendor/` material establishes source
boundary context for Orange Pi Zero 3, WAVE ROVER, UART newline-delimited JSON,
firmware, and vendor app references. That source boundary does not prove real
project `2D LiDAR` or `ToF` SKU/source/receipt, procurement, installation,
wiring, power, calibration, HIL entry, Nav2/SLAM field pass, near-field safety
pass, or delivery success.

Fail-closed states:

- `blocked_missing_pr5_vendor_source_review_packet_summary`
- `blocked_unsupported_pr5_vendor_source_review_packet_summary`
- `blocked_unsafe_pr5_vendor_source_review_reply`

Unsupported schema, thread mismatch, missing `docs/vendor/VENDOR_INDEX.md`
source ref, missing `2D LiDAR` / `ToF` material gaps, unsafe success/control
claims, credentials, raw local paths, raw serial paths, `delivery_success=true`,
or `primary_actions_enabled=true` must fail closed.

Consumers should read the summary first. The summary exposes only sanitized
fields: `thread_id`, `reply_status`, `proof_boundary`, `vendor_source_boundary`,
`missing_materials`, `not_proven`, `next_required_evidence`, `safe_copy`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`. The raw Markdown remains a manual review artifact, not
a Robot command, ACK, cursor, ROS control, `/cmd_vel`, HIL pass, hardware
material proof, field pass, Objective 5 external proof, or delivery proof.
