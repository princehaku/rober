# Tech Plan - O7 Consumer Read Query Filters

## OKR Lowest Priority Check

- Current lowest Objective in `OKR.md` section 4.1: Objective 5 at about `85%`.
- This sprint does not target Objective 5 directly.
- Reason: the previous sprint already ran the O5 CDN/TLS external evidence probe and closed on `blocked_http_status_not_success_class`; without a success-class public endpoint or stronger production evidence, another O5 support-only wrapper would repeat the same blocker. The sprint instead targets O7 at about `93%` through a non-repeating PC consumer-read usability gap.

## Owner

- Primary owner: `full-stack-software-engineer`
- Main session role: planning, dispatch, acceptance, and final summary only.

## File Scope

Allowed product/docs/test files:

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/process/okr_progress_log.md`
- `OKR.md`
- `sprints/2026.07.13_14-15_o7_consumer_read_query_filters/tech-done.md`

Do not modify hardware, ROS2 nav/behavior code, O5 probe code, O1/O3 route artifacts, or historical sprint directories outside this sprint.

## Implementation Plan

1. Introduce a small typed O7 consumer list query object in the workstation API/adapter.
2. Validate and normalize optional filters in the PC Node adapter before forwarding to O6.
3. Add UI inputs in the O7 consumer-read primary path and display applied query values.
4. Update tests for default behavior, filtered behavior, and fail-closed unsafe values.
5. Update docs and `tech-done.md` with actual changes, verification, and remaining risk.

## Acceptance Commands

Run from `/Users/m1/apps/rober`:

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_realtime_operator_console.md docs/process/okr_progress_log.md OKR.md sprints/2026.07.13_14-15_o7_consumer_read_query_filters
```

## Risk Boundary

- This is O7/O6 local/mock consumer-read query hardening only.
- It must keep `safe_to_control=false`, `delivery_success=false`, `robot_control_executed=false`, `primary_actions_enabled=false`, and `connects_cloud_production=false`.
- It must not infer production cloud readiness, real route execution, delivery success, HIL, safe-to-control, or O5 external evidence.
