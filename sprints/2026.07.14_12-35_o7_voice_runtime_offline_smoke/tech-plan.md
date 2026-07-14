# Tech Plan - O7 Voice Runtime Offline Smoke

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o7_voice_runtime_offline_smoke_only`
- Implementation mode: single-owner closure.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` section 4.1: Objective 5 is about `85%`.
2. This sprint does not directly target O5 because the current environment has no `ROBER_CDN_PROBE_BASE_URL`, no success-class production/cloud evidence, no real 4G/SIM, no production DB/queue/worker/cutover, no OSS/CDN live traffic, and no real phone/browser proof.
3. Recent O5 support-only gates and O7 voice wrappers are already consumed. This sprint deliberately avoids another O5 wrapper and avoids repeating `voice runtime preflight`; it creates a bounded offline smoke trace that can be used as the next handoff toward real voice runtime smoke.
4. Expected OKR scoring: O5 stays about `85%`, O1 stays about `94%`, O6/O7 stay about `93%`; no KR should be archived.

## Direction and Evidence Boundary

本轮方向是 `调整`：从 O5/O7 support-only wrapper 循环切到 O7 `voice runtime offline smoke trace`。它必须证明的是 PC/Node 层可以用安全 local/offline 配置生成同任务 voice runtime smoke trace；它不证明真实 provider、真实音频设备、speaker dispatch 或 speaker ACK。

Required false fields:

- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `tts_send_enabled=false`
- `speaker_dispatch_enabled=false`
- `real_speaker_ack_proven=false`
- `microphone_opened=false`
- `speaker_playback_opened=false`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

Rejected claims: production cloud, real voice API, real ASR/TTS runtime, microphone input, speaker output, TTS send, speaker dispatch, real speaker ACK, route execution, delivery success, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, robot movement.

## Owner 分工

- `full-stack-software-engineer`: implement, test, repair, and update `tech-done.md`.
- `product-okr-owner`: review `tech-done.md`, update `side2side_check.md`, `final.md`, `OKR.md`, and progress log after implementation evidence exists.
- No parallel owner needed. Scope is PC/O7 workstation only.

## 文件范围

Implementation owner may edit only the smallest necessary subset under:

- `pc-tools/workstation/src/server/`
- `pc-tools/workstation/src/client/`
- `pc-tools/workstation/src/components/`
- `pc-tools/workstation/src/shared/`
- `pc-tools/workstation/test/`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/tech-done.md`

Implementation owner must not edit:

- WAVE ROVER, UART, ESP32, `/cmd_vel`, `/api/base/manual`, Nav2 launch/runtime, or hardware config.
- Existing closed sprint files.
- `OKR.md`, `docs/process/okr_progress_log.md`, `side2side_check.md`, or `final.md` before Product acceptance.

## 接口影响

Expected implementation shape, to be finalized by `full-stack-software-engineer`:

1. Add `trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1`.
2. Add a PC/Node endpoint such as `GET /api/o7/voice-runtime/offline-smoke`.
3. Reuse the safety model from `o7VoiceRuntimePreflight.ts` where practical, but produce a distinct smoke trace rather than returning only preflight status.
4. Support a safe `task_id` and `mode=offline_stub|local_stub|disabled_local`; default selected task may be the existing fixture task when no real task is provided.
5. Emit deterministic trace events such as `preflight_config_checked`, `offline_asr_stub_loaded`, `tts_draft_trace_prepared`, `speaker_ack_pending_not_real`.
6. Ensure fail-closed behavior for unsafe text, URL/credentials/device/audio payload/control strings, unsupported mode, task mismatch, and dangerous true fields.
7. UI/API display must expose endpoint, proof boundary, trace events, false fields, blocked reasons, and next required real evidence.

No robot-side endpoint, ROS2 topic, serial path, cloud production endpoint, microphone stream, speaker device, TTS provider call, ASR provider call, O6 write, or robot control may be introduced.

## 验收命令

Implementation owner must run and report:

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
rg -n "software_proof_o7_voice_runtime_offline_smoke_only|voice runtime offline smoke|/api/o7/voice-runtime/offline-smoke|trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1|real_voice_api_connected=false|real_asr_tts_runtime_connected=false|tts_send_enabled=false|speaker_dispatch_enabled=false|real_speaker_ack_proven=false|microphone_opened=false|speaker_playback_opened=false|safe_to_control=false|delivery_success=false" pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke
```

If implementation touches O6 archive events unexpectedly, owner must also run targeted Python relay tests and explain why O6 was required. Default plan assumes O6 is not needed.

## 子 Agent Prompt 要点

When dispatching the implementation owner, include:

- Role: `full-stack-software-engineer`
- Task: implement O7 PC/Node voice runtime offline smoke trace.
- File scope: workstation server/client/components/shared/tests, `docs/product/pc_tools_workstation.md`, and this sprint `tech-done.md`.
- Required proof boundary: `software_proof_o7_voice_runtime_offline_smoke_only`.
- Required false fields listed above.
- Required validation commands listed above.

## Product Acceptance Gate

Product should accept only if:

- The result is a deterministic offline smoke trace, not just a repeat of preflight.
- The implementation remains local/offline and side-effect free.
- All dangerous true fields are rejected or fixed false.
- `tech-done.md` contains changed files, validation output, failure/repair notes if any, remaining risk, and next required live evidence.

Product should keep KR status as `不归档`; this sprint is not mission-grade evidence.
