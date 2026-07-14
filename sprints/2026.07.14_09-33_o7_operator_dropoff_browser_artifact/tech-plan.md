# Tech Plan - O7 Operator Dropoff Browser Artifact

## Sprint Type

- sprint_type: epic
- Sprint: `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/`
- Owner: `full-stack-software-engineer`

## OKR Lowest Priority Check

Current lowest Objective from `OKR.md` section 4:

- Objective 5: about `85%`.

This sprint does not directly target O5 because the latest O5 path is blocked on success-class production/cloud evidence or same-window live route/HIL/operator evidence. Recent O5 local gates are explicitly retired from immediate reuse. This sprint targets O7/O6 only because it can produce a distinct, non-repeating user-touchpoint evidence artifact in the current environment.

Expected OKR accounting:

- O5 remains about `85%`.
- O6 remains about `93%`.
- O7 remains about `93%` unless Product accepts the browser artifact as a conservative O7 evidence-quality increment.
- KR archival: `不归档`.

## Implementation Plan

Full-stack owner should:

1. Add a sprint-scoped DOM/browser smoke artifact generation path to the existing workstation UI test that already triggers `记录 operator dropoff capture`.
2. Write the JSON artifact to:
   - `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/artifacts/o7_operator_dropoff_browser_artifact.json`
3. Include at minimum:
   - `schema=trashbot.pc_tools_workstation.o7_operator_dropoff_browser_artifact.v1`
   - `proof_boundary=software_proof_o7_operator_dropoff_browser_artifact_only`
   - selected `task_id`
   - triggered UI button label
   - endpoint URL path
   - receipt schema and capture status
   - `event_type=operator.dropoff_acceptance`
   - `real_operator_action_proven=false`
   - `delivery_success=false`
   - `route_execution_success=false`
   - `safe_to_control=false`
   - `hil_pass=false`
   - `robot_control_executed=false`
   - `connects_cloud_production=false`
   - `not_proven`
4. Add/adjust assertions so future UI drift fails the test.
5. Update:
   - `docs/interfaces/o7_realtime_operator_console.md`
   - `docs/product/pc_tools_workstation.md`
   - `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/tech-done.md`

## File Scope

Allowed implementation files:

- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/artifacts/o7_operator_dropoff_browser_artifact.json`
- `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/tech-done.md`

Do not edit adapter/server/API endpoint files unless the existing UI test cannot expose the needed artifact fields. If that happens, stop and report why before expanding scope.

## Interface Impact

No new runtime API is expected. The change should be test/evidence/documentation only, using the existing:

- `POST /api/o7/consumer-read/tasks/:taskId/operator/dropoff-acceptance/request?baseUrl=<local-loopback-url>`
- `trashbot.pc_tools_workstation.o7_operator_dropoff_action_capture_result.v1`

## Validation Commands

Run from `/Users/m1/apps/rober`:

```bash
cd pc-tools/workstation && npm run test -- test/App.test.ts -t "operator dropoff"
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
python3 -m json.tool sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/artifacts/o7_operator_dropoff_browser_artifact.json
rg -n "o7_operator_dropoff_browser_artifact|software_proof_o7_operator_dropoff_browser_artifact_only|real_operator_action_proven=false|delivery_success=false" pc-tools/workstation/test/App.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact
git diff --check -- pc-tools/workstation/test/App.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact
```

If a command fails, Full-stack owner must diagnose, fix within file scope, and rerun.

## Risk Boundary

This sprint is not route execution, delivery, HIL, safe-to-control, production cloud, production DB/queue, OSS/CDN, 4G/SIM, true mobile phone proof, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or robot movement.
