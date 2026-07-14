# PRD - O7 Voice Runtime Preflight

## Product Summary

This sprint plans an O7 PC workstation capability named `voice runtime preflight`. The goal is to provide a bounded software proof that the PC/Node layer can inspect voice runtime configuration and report readiness/fail-closed state before any real ASR/TTS, microphone, speaker, cloud, delivery, or robot-control integration is attempted.

Proof boundary is fixed as `software_proof_o7_voice_runtime_preflight_only`.

## 用户价值和产品北极星

普通用户最终不应该读 ROS2、串口、raw JSON 或工程日志来判断机器人是否能播报状态。语音和喇叭是降低门槛的用户触点：小车准备出发、到达垃圾站、需要人工取走、需要协助时，用户应听到明确提示。

本轮不是上线真实语音，而是把“真实语音 runtime 是否可接入”的前置检查做成可测试合同。它服务的北极星是：机器人交付状态对普通用户可理解、可复盘、可安全失败。

## Problem

Recent O6/O7 voice work created local/mock event-write surfaces:

- voice TTS draft event write
- voice speaker ACK/failure event write

These surfaces are useful but still only prove selected-task event construction and local archive/readback. They do not show whether PC/Node has a safe preflight contract for a real voice runtime.

Without a bounded preflight, the next real voice integration risks mixing three things that must stay separate:

- configuration/readiness inspection
- real ASR/TTS provider or local runtime access
- actual speaker dispatch or robot mission behavior

## Goal

Create a plan for implementation of a PC/O7 `voice runtime preflight` software proof that:

1. Detects configured voice runtime mode from Node/PC environment or local config.
2. Returns a structured preflight summary with proof boundary and fixed false fields.
3. Fails closed when required config is missing, unsafe, points outside allowed local/offline scope, or claims real capability in this environment.
4. Does not open microphone or speaker devices.
5. Does not call real voice APIs, cloud APIs, ASR/TTS providers, or production endpoints.
6. Does not send TTS, dispatch audio, or control the robot.

## Non Goals

- No production cloud integration.
- No real ASR provider call.
- No real TTS provider call.
- No microphone open, recording, streaming, or wake-word listening.
- No speaker playback, speaker dispatch, speaker ACK, or audio-device probing that produces sound.
- No route execution, delivery success, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or robot movement.
- No OKR percentage increase by plan creation alone.

## OKR 映射和方向判断

- O5 is the numerically lowest Objective at about `85%`, but its missing evidence is success-class production/cloud or explicit same-window live route/HIL/delivery/operator evidence. Current environment lacks that authorization, and recent support-only O5/O6/O7 slices must not be repeated.
- O7 remains about `93%`; this sprint targets an O7 PC workstation preflight gap that is adjacent to voice user touchpoints and distinct from prior event-write wrappers.
- Direction judgment: `调整` from repeated O5 support-only packaging to a bounded O7 preflight. This is a tactical pivot, not a replacement of O5.

## Required Product Contract

The implementation owner must design the output so product acceptance can verify these fields:

- `proof_boundary=software_proof_o7_voice_runtime_preflight_only`
- `voice_runtime_preflight_status=<ready|blocked|fail_closed variant>`
- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `tts_send_enabled=false`
- `speaker_dispatch_enabled=false`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

The user-facing or operator-facing copy must make clear that the preflight checks configuration/readiness only. It must not say real voice runtime, speaker output, delivery success, safe control, or production cloud is proven.

## Acceptance Criteria

Implementation acceptance should require:

1. A deterministic Node/PC API or module returns a voice runtime preflight summary.
2. Missing config produces a blocked/fail-closed status, not a runtime crash or optimistic ready state.
3. Unsafe true claims for real runtime, TTS send, speaker dispatch, delivery, robot control, or cloud production fail closed.
4. UI/API readback exposes the proof boundary and fixed false fields.
5. Tests cover positive safe preflight, missing config, unsafe true claims, and no real side effects.
6. Build, lint, targeted tests, and scoped diff check pass.
7. Sprint `tech-done.md` records actual changes, validation evidence, first failures/repairs if any, and remaining risks.

## KR 拆解、更新和历史归档

- KR update this plan enables: O7 voice runtime preflight support surface, pending implementation evidence.
- KR archival this sprint: none at planning stage.
- Historical record target after implementation: this sprint's `tech-done.md`, `side2side_check.md`, and `final.md` should record evidence source, proof boundary, acceptance result, and `KR 不归档` unless a future implementation unexpectedly includes current real runtime evidence, which is explicitly out of scope here.

## Priority

P0 for next implementation because it is the selected non-repeating lane after the 10:34 sprint. It is still bounded software proof and must not displace real O5 production/cloud or live route/HIL/delivery/operator evidence if those become available.

## Responsibility

- Product acceptance: `product-okr-owner`
- Implementation/testing/repair/doc sync: `full-stack-software-engineer`

## Risks and Evidence Gaps

- Real voice provider credentials or runtime may not exist; this is expected and should produce fail-closed readiness, not a blocker for software proof.
- Preflight can drift into a thin wrapper if it only repeats event-write fields. It must inspect runtime/config readiness, not write another selected-task event.
- No real voice runtime, ASR/TTS, microphone, speaker, production cloud, route execution, delivery, HIL, or safe-to-control evidence will be proven by this sprint.

## Required Sprint Documents

- Created now: `pre_start.md`, `prd.md`, `tech-plan.md`
- Created only after implementation: `tech-done.md`
- Created only after acceptance/closeout: `side2side_check.md`, `final.md`
