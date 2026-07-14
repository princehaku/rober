# Tech Plan - O6/O7 Voice Speaker ACK Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/`
- Owner: `full-stack-software-engineer`
- Product owner: `product-okr-owner`
- Scope type: O6/O7 selected-task action/write contract and workstation receipt proof
- Proof boundary: `software_proof_o6_o7_voice_speaker_ack_event_write_only`
- Planning status: only `pre_start.md`, `prd.md`, and `tech-plan.md` are created in this task.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5, about `85%`.
- 本 sprint 是否针对该最低 Objective：否。
- 理由：O5 now requires success-class production/cloud evidence or explicit live route/HIL/operator evidence. Recent O5/operator/terminal/delivery-state gates and the latest O7 operator dropoff browser artifact have already consumed support-only surfaces. Repeating O5 gates or operator dropoff artifacts would violate the non-repeating blocker rule.
- 本 sprint 的合理性：the 06:27 voice sprint left speaker ACK/failure events as explicit remaining risk. This sprint creates a distinct O6/O7 selected-task action/write path that writes `voice.speaker_ack` or `voice.speaker_failure` into O6 events and returns a bounded O7 receipt.
- Closeout requirement: final acceptance must keep O5/O6/O7 percentages flat unless implementation produces real production/cloud, live route, delivery/operator, HIL, or real speaker runtime evidence.

## Implementation Plan

1. O6 event contract:
   - Add safe event types `voice.speaker_ack` and `voice.speaker_failure` to the O6 archive events allow-list.
   - Keep archive writes local/mock and selected-task scoped.
   - Reject or fail-close any payload claiming `speaker_dispatch_enabled=true`, `real_speaker_ack_proven=true`, `tts_send_enabled=true`, `real_voice_api_connected=true`, `real_asr_tts_runtime_connected=true`, `safe_to_control=true`, `delivery_success=true`, `robot_control_executed=true`, or `connects_cloud_production=true`.
   - Add O6 tests for ack write, failure write, selected-task readback, and dangerous true rejection.
2. O7 adapter/server:
   - Add `POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>`.
   - Validate loopback-only `baseUrl`, no credentials, no injected query/hash, path/body `task_id` consistency, allowed `ack_status`, safe event id, safe reason code, and sanitized evidence refs.
   - Map `ack_status=ack` to `event_type=voice.speaker_ack`.
   - Map `ack_status=failure` to `event_type=voice.speaker_failure`.
   - Forward a fixed safe `POST /api/o6/archive/events` request.
   - Return receipt schema `trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1`.
3. Workstation touchpoint:
   - Add API/client contract and fixture/test coverage under a `voice_speaker_ack_event` naming marker.
   - Render receipt fields and fixed false fields if this follows the existing selected-task action panel pattern.
   - Avoid any visible claim that audio was played or a real ACK was received.
4. Documentation and sprint closeout:
   - Update O6/O7 interface docs and PC product docs in the implementation sprint.
   - `tech-done.md` must record actual files changed, validation outputs, first-failure analysis if any, and remaining risks.
   - `side2side_check.md` and `final.md` must be written only after implementation verification, not in this planning task.

## Implementation File Scope For Next Owner

Allowed implementation files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/tech-done.md`
- `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/side2side_check.md`
- `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/final.md`

Do not modify WAVE ROVER hardware code, Nav2 route execution code, launch files, Docker files, historical sprint directories, `OKR.md`, or `docs/process/okr_progress_log.md` unless a later explicit Product closeout task permits it.

## Interface Contract

O7 endpoint:

```text
POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>
```

O6 write target:

```text
POST /api/o6/archive/events
```

O7 receipt schema:

```text
trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1
```

Allowed event types:

```text
voice.speaker_ack
voice.speaker_failure
```

Required proof boundary:

```text
software_proof_o6_o7_voice_speaker_ack_event_write_only
```

Required false fields:

```text
speaker_dispatch_enabled=false
real_speaker_ack_proven=false
tts_send_enabled=false
real_voice_api_connected=false
real_asr_tts_runtime_connected=false
safe_to_control=false
delivery_success=false
robot_control_executed=false
connects_cloud_production=false
```

## Acceptance Commands For Implementation Owner

The implementation owner must run:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

```bash
cd pc-tools/workstation && npm run test
```

```bash
cd pc-tools/workstation && npm run build
```

```bash
cd pc-tools/workstation && npm run lint
```

```bash
rg -n "voice_speaker_ack_event|voice/speaker-ack/request|software_proof_o6_o7_voice_speaker_ack_event_write_only|voice.speaker_ack|voice.speaker_failure|o7_voice_speaker_ack_event_result" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src/server pc-tools/workstation/src/client pc-tools/workstation/src/components pc-tools/workstation/test docs/interfaces docs/product sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write
```

If any command fails, the owner must diagnose, fix, and rerun before returning.

## Planning Validation Commands

This planning task must run:

```bash
rg -n "voice_speaker_ack_event|voice/speaker-ack/request|software_proof_o6_o7_voice_speaker_ack_event_write_only|voice.speaker_ack|voice.speaker_failure|OKR 最低优先级核对" sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write
```

```bash
git diff --check -- sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write
```

## Risks And Blockers

- This sprint does not improve O5 because it lacks success-class production/cloud evidence.
- This sprint does not prove real audio, real speaker dispatch, real speaker ACK, real voice API, or real ASR/TTS runtime.
- This sprint does not prove route execution, delivery/operator acceptance, HIL, safe-to-control, or robot control.
- If UI wiring is too coupled, the owner may return server/API/O6/docs/test completion with UI as a stated risk, but the O7 endpoint, O6 event write, receipt schema, false fields, and fail-closed tests must be complete.
