# Tech Plan - O6/O7 Voice TTS Draft Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/`
- Owner: `full-stack-software-engineer`
- Scope type: O6/O7 API contract and workstation adapter/UI proof
- Proof boundary: `software_proof_o6_o7_voice_tts_draft_event_write_only`

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5, about `85%`.
- 本 sprint 是否针对该 Objective：否。
- 理由：O5 next scoring evidence requires success-class production/cloud evidence or explicit operator-approved live route/HIL/delivery evidence. Recent O5 support-only sprints already consumed CDN/TLS 4xx, review-decision, terminal-result bridge/reconciliation, and delivery-state success gate boundaries. Repeating those gates would violate the non-repeating blocker rule.
- 本 sprint targets the next actionable low-progress surface: O7/O6 selected-task voice action-write, which consumes a `task_id` and writes an O6 archive event instead of adding another readback wrapper.
- final.md 收口时需复核：O5 evidence remained unavailable and this sprint did not claim O5 progress.

## Implementation Plan

1. O6 event contract:
   - Extend the allowed O6 archive event types with a safe voice/TTS draft event type.
   - Keep all O6 event archive safety guards unchanged: no raw audio, no production cloud, no real voice runtime, no robot control, and no delivery success claims.
   - Add or update O6 tests to prove the event type writes and dangerous true claims fail closed.
2. O7 adapter/server:
   - Add `POST /api/o7/consumer-read/tasks/:taskId/voice/tts-draft/request`.
   - Validate local-loopback `baseUrl`, path/body task id consistency, draft text limits, optional voice/locale fields, event id, and evidence refs.
   - Forward a fixed safe O6 `POST /api/o6/archive/events` request.
   - Return receipt schema `trashbot.pc_tools_workstation.o7_voice_tts_draft_request_result.v1`.
3. PC touchpoint/docs:
   - Add the API constant and expose the action in the selected-task consumer-read surface if it fits existing component patterns.
   - Update O7 and O6 interface docs so operators see the draft/event-write boundary.
4. Sprint closeout:
   - `tech-done.md` must record actual files changed, validation outputs, failure analysis, and remaining risks.

## File Scope

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
- `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/tech-done.md`

Do not modify hardware, Nav2, WAVE ROVER, launch, Docker, historical sprint directories, or unrelated generated artifacts.

## Acceptance Commands

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
rg -n "voice/tts-draft/request|o7_voice_tts_draft_request|software_proof_o6_o7_voice_tts_draft_event_write_only|voice.tts" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src/server pc-tools/workstation/src/client pc-tools/workstation/src/components pc-tools/workstation/test docs/interfaces docs/product sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write
```

If any command fails, the owner must diagnose, fix, and rerun before returning.

## Risks

- This sprint will not raise O5 because it does not create production/cloud or live delivery evidence.
- O7 remains local/mock until a real voice API, ASR/TTS runtime, speaker ACK, and safety policy are connected.
- If UI wiring is too coupled for this sprint, the owner may deliver server/API/docs with tests and record UI as remaining risk, but the endpoint and receipt must be complete.
