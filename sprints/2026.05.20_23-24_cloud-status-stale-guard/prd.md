# Cloud Status Stale Guard PRD

## User Value

When the phone/cloud path has an old robot status snapshot, ordinary users need a clear blocked state instead of a generic unavailable or ambiguous ready state. The system must explain that the robot has not recently reported status, keep primary actions disabled, and route the user to refresh/wait/support without implying delivery success.

## OKR Mapping

- Objective 5 KR6: graceful degradation for 4G / cloud-control interruptions.
- Objective 4 support: phone-safe explanation that does not expose raw ROS, JSON, tokens, `/cmd_vel`, serial, or cloud internals.
- No Objective 5 percentage uplift is planned unless real external materials appear during this sprint.

## Product Requirements

1. Robot/API must expose stale status as a dedicated proof boundary:
   - `degradation_state=status_stale`
   - `ack_semantics=stale_status_not_delivery_success`
   - `remote_ready=false`
   - `primary_actions_enabled=false`
   - `delivery_success=false`
   - `proof_boundary=software_proof_docker_cloud_status_stale_guard`
2. Operator readiness and command safety must keep Start Delivery, Confirm Dropoff, and Cancel disabled while Diagnostics remains available.
3. `mobile/web` must consume the stale-status fixture through the existing cloud readiness panel, with phone-safe Chinese copy and no new control endpoint.
4. Docs and sprint closeout must preserve the evidence boundary: Docker/local software proof only.

## Non-goals

- Do not add production cloud infrastructure.
- Do not add new hardware assumptions or change WAVE ROVER/UART/HIL behavior.
- Do not claim real phone/browser acceptance.
- Do not create broad test expansion; use fenced focused verification only.
