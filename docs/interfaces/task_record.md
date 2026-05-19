# Task Record Interface

## task_terminal_completion_mainline

`task_record.py` writes `task_terminal_completion_mainline` into each
collection task record. The field is the Robot-owned, sanitized source for
dropoff/cancel terminal-action status in Docker/local software-proof runs.

- Schema: `trashbot.task_terminal_completion_mainline.v1`
- Evidence boundary:
  `software_proof_docker_task_terminal_completion_mainline_gate`
- Fixed boundary fields: `source=software_proof`, `status=blocked_not_proven`,
  `delivery_success=false`, `primary_actions_enabled=false`,
  `dropoff_completion_proven=false`, and `cancel_completion_proven=false`.

The summary may expose safe `evidence_ref`, `terminal_action`,
`terminal_status`, `operator_confirmation_required`,
`operator_confirmation_status`, `missing_required_materials`,
`next_required_evidence`, `failure_reason`, and route-progress evidence
metadata. Missing real field materials must keep `terminal_status` at
`missing_materials` and must not become a delivery or completion claim.

The field is metadata-only. It must not read hardware, serial/UART, ROS graph,
raw artifacts, cloud resources, or mobile browser state. It must not trigger
collect, dropoff, cancel, ACK POST, cursor advance, Nav2, HIL, terminal ACK,
or any robot command.

The required real-material families are a real task record, real
dropoff/cancel completion material, and same-`evidence_ref` field replay.
Until those materials exist and are reviewed outside this software-proof
summary, both dropoff and cancel completion remain `not_proven`.
