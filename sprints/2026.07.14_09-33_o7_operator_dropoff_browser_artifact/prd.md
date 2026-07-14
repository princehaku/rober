# PRD - O7 Operator Dropoff Browser Artifact

## Sprint Type

- sprint_type: epic
- Sprint: `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/`
- Owner: `full-stack-software-engineer`

## User Problem

The project now has a selected-task operator dropoff action capture API, but the evidence is still mostly API/unit-test oriented. For a user-touchpoint Objective, the next useful non-repeating proof is that the PC browser surface can drive the selected-task action and show the operator exactly what was recorded, what remains false, and why it is not delivery proof.

## Product Goal

Create a repeatable local browser/DOM evidence artifact for the existing O7 operator dropoff action capture flow.

The artifact should answer:

- Which selected task was used?
- Which UI action was triggered?
- Which O7 endpoint was called?
- Which receipt schema/status came back?
- Which fixed false fields stayed false?
- Which proof boundary prevents mission over-claiming?

## Requirements

1. Use the existing O7 selected-task operator dropoff capture UI and API client path.
2. Generate a sprint-scoped JSON artifact under this sprint's `artifacts/` directory.
3. Keep the artifact sanitized: no raw browser screenshot, token, credential, absolute secret path, raw cloud URL with credentials, or production payload.
4. Include a stable schema such as `trashbot.pc_tools_workstation.o7_operator_dropoff_browser_artifact.v1`.
5. Keep all mission/safety false fields explicit:
   - `real_operator_action_proven=false`
   - `delivery_success=false`
   - `route_execution_success=false`
   - `safe_to_control=false`
   - `hil_pass=false`
   - `robot_control_executed=false`
   - `connects_cloud_production=false`
6. Update `docs/interfaces/o7_realtime_operator_console.md` and `docs/product/pc_tools_workstation.md` with the artifact boundary.
7. Update this sprint's `tech-done.md` with actual changes, validation results, and risks.

## Non-Goals

- Do not add another O7/O6 operator dropoff endpoint.
- Do not claim true phone/browser production evidence.
- Do not run or simulate robot motion.
- Do not touch `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or real hardware.
- Do not change O5/O6/O7 headline percentages unless Product closeout explicitly proves a stronger evidence class.

## Product Acceptance

Product accepts a local software proof only if the worker returns:

- Changed file list.
- Artifact path and key fields.
- Workstation test/build/lint results.
- Scoped diff-check result.
- Clear remaining risk and next owner handoff.
