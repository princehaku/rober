# Pre Start - O6/O7 Voice TTS Draft Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/`
- Start time: 2026-07-14 06:27 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Target Objectives: O7 primary, O6 secondary
- Lowest Objective review: O5 remains the lowest Objective at about `85%`, but current progress requires real production/cloud evidence or explicit operator-approved live route/HIL/delivery evidence.

## Previous Context

The latest closed sprint `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/` accepted only `software_proof_o5_delivery_state_live_success_gate_only`. It correctly left `current_live_evidence_observed=false`, `delivery_success_accepted_for_state_machine=false`, `safe_to_control=false`, and `hil_pass=false`.

The prior sprint `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/` also stayed local/mock and fail-closed. Repeating another O5 terminal-result, reconciliation, success-gate, readiness, review, or CDN/TLS 4xx wrapper would consume the same missing real evidence boundary without improving OKR quality.

## Direction

This sprint pivots to a distinct O7/O6 user-action contract: a selected-task TTS draft request that writes a safe local/mock voice event into O6 archive and returns an O7 receipt. It must consume a concrete `task_id`, not just expose another readback or preview.

## Non-Goals

- Do not connect a real voice API.
- Do not send TTS audio to a speaker.
- Do not dispatch robot control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, or WAVE ROVER UART.
- Do not claim delivery success, safe-to-control, HIL, production cloud, real ASR/TTS runtime, or real phone/browser proof.

## Blocker Repeat Check

- O5 production/cloud success evidence remains unavailable in this environment.
- O1/O3 current live route/HIL/delivery evidence still requires explicit operator approval and same-window field evidence.
- This sprint does not repeat the latest O5 blocker. It targets O7/O6 voice action-write, a separate user-touchpoint contract not covered by the recent terminal-result and delivery-state work.
