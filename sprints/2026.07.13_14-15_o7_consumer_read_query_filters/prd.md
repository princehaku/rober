# PRD - O7 Consumer Read Query Filters

## Problem

The PC O7 consumer-read panel is the primary operator path for task list/detail and material inspection. It currently loads the O6 consumer list with a fixed summary query, so operators cannot narrow task discovery by robot, exact task, UTC date, status, or list size from the O7 surface.

## User Value

Operators need to find the right task evidence quickly before opening detail, replay, labeling, or mission material panels. Exposing safe query filters in O7 reduces broad manual scanning and makes the PC tool a usable consumer of the O6 read model rather than a static latest-list viewer.

## Scope

- Add O7 PC consumer-read list query inputs for `robot_id`, `task_id`, `date=YYYY-MM-DD`, `status`, `limit`, and optionally `before_started_at_ms`.
- Forward only validated, trimmed query values from browser -> PC Node adapter -> O6 `/api/o6/consumer/tasks`.
- Surface the applied query strategy in the response and UI.
- Keep all proof/safety fields false and keep the path loopback-only.
- Update O7 interface documentation and sprint closeout.

## Acceptance

- Safe empty filters preserve existing behavior: `view=summary`, `limit=50`, no include sections.
- Non-empty safe filters are encoded into the O7 adapter request and forwarded to O6 consumer read with AND semantics owned by O6.
- Unsafe values fail closed before leaking paths, credentials, URLs, raw payloads, or control words.
- UI shows current filter values and applied query strategy without enabling control, playback, submit, export, or production cloud claims.
- Workstation tests cover default and filtered request URLs, plus at least one fail-closed unsafe query path.

## Proof Boundary

Accepted as `software_proof_o7_consumer_read_query_filters_only`.

Rejected as production cloud, real robot data, real annotation/export, route execution, delivery/operator acceptance, HIL, safe-to-control, O5 external evidence, or real phone/browser proof.
