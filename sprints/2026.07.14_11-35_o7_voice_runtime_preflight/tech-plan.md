# Tech Plan - O7 Voice Runtime Preflight

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o7_voice_runtime_preflight_only`
- Implementation mode: single-owner closure.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` section 4.1: Objective 5 is about `85%`.
2. This sprint does not directly target O5 production/cloud cutover because the current environment has no success-class production/cloud evidence, no real 4G/SIM, no production DB/queue/worker/cutover, no OSS/CDN live traffic, and no real phone/browser proof.
3. Reason for not targeting O5: recent O5/O6/O7 work already consumed support-only wrappers and local/mock event-write lanes. The latest accepted final explicitly says the next run should not repeat those surfaces; if no success-class O5 or same-window live route/HIL/delivery/operator evidence is available, choose a materially stronger same-task mission artifact or real voice runtime preflight. This sprint selects real voice runtime preflight as bounded O7 software proof.
4. Expected OKR scoring: O5 stays about `85%`, O6/O7 stay about `93%`, O1 stays about `94%`; no KR should be archived from planning alone.

## Direction and Evidence Boundary

本轮计划方向是 `调整`：从重复 O5 support-only 包装切到 O7 `voice runtime preflight`。它必须证明的是 PC/Node 层能以 fail-closed 方式报告 voice runtime 配置/就绪状态，而不是证明真实 voice runtime 已连接。

Required false fields:

- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `tts_send_enabled=false`
- `speaker_dispatch_enabled=false`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

Rejected claims: production cloud, real voice API, real ASR/TTS runtime, microphone input, speaker output, TTS send, speaker dispatch, real speaker ACK, route execution, delivery success, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, robot movement.

## Owner 分工

- `full-stack-software-engineer`: implement, test, repair, and update `tech-done.md`.
- `product-okr-owner`: accept the plan, later review `tech-done.md`, `side2side_check.md`, `final.md`, and decide OKR wording.
- No parallel owner needed. The scope is PC/O7 Node/workstation and does not touch hardware, ROS2 motion, Nav2, or cloud production.

## 文件范围

Planned implementation owner may edit only the smallest necessary subset under these areas:

- `pc-tools/workstation/src/server/`
- `pc-tools/workstation/src/client/`
- `pc-tools/workstation/src/components/`
- `pc-tools/workstation/src/shared/`
- `pc-tools/workstation/src/**/*.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/tech-done.md`

Implementation owner must not edit:

- WAVE ROVER, UART, ESP32, `/cmd_vel`, `/api/base/manual`, Nav2 launch/runtime, or hardware config.
- Existing closed sprint files.
- `OKR.md` unless Product Owner explicitly asks during acceptance.
- `side2side_check.md` or `final.md` before implementation evidence exists.

This planning task itself is restricted to:

- `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/pre_start.md`
- `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/prd.md`
- `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/tech-plan.md`

## 接口影响

Expected implementation shape, to be finalized by `full-stack-software-engineer`:

1. Add a PC/O7 Node-side voice runtime preflight summary function or endpoint, preferably under the existing workstation O7 voice or consumer-read boundaries.
2. The preflight may read bounded environment/config flags only. It must not connect to real providers, open devices, start streams, play audio, or send HTTP requests to production.
3. The response should include a schema such as `trashbot.pc_tools_workstation.o7_voice_runtime_preflight_result.v1`.
4. The response should include a stable status such as `voice_runtime_preflight_status=ready_for_configured_runtime_check_only` or `blocked_missing_voice_runtime_config`.
5. UI/API display must expose `voice runtime preflight`, proof boundary, fixed false fields, not-proven list, and next required evidence.
6. Any incoming body/config that attempts to set dangerous true fields must fail closed.

No robot-side endpoint, ROS2 topic, serial path, cloud production endpoint, microphone stream, speaker device, TTS provider call, or ASR provider call may be introduced.

## 风险边界

- This sprint is `software_proof_o7_voice_runtime_preflight_only`.
- It can prove config/readiness inspection and fail-closed behavior only.
- It cannot prove real ASR/TTS, real voice API, microphone availability, speaker playback, speaker ACK, TTS dispatch, production cloud, delivery success, route execution, HIL, safe-to-control, robot movement, or O5 external evidence.
- If validation shows the implementation only repeats voice TTS draft or speaker ACK event-write without runtime preflight inspection, Product should reject and send back for repair.
- If validation opens microphone/speaker, calls real cloud/provider, sends TTS, or controls robot, Product should reject and require removal before acceptance.

## 验收命令

Plan-stage commands already required for this planning task:

```bash
test -f sprints/2026.07.14_11-35_o7_voice_runtime_preflight/pre_start.md && test -f sprints/2026.07.14_11-35_o7_voice_runtime_preflight/prd.md && test -f sprints/2026.07.14_11-35_o7_voice_runtime_preflight/tech-plan.md
rg -n "sprint_type: epic|software_proof_o7_voice_runtime_preflight_only|OKR 最低优先级核对|full-stack-software-engineer|voice runtime preflight|real_voice_api_connected=false|real_asr_tts_runtime_connected=false|tts_send_enabled=false|speaker_dispatch_enabled=false|safe_to_control=false|delivery_success=false" sprints/2026.07.14_11-35_o7_voice_runtime_preflight
git diff --check -- sprints/2026.07.14_11-35_o7_voice_runtime_preflight
find sprints/2026.07.14_11-35_o7_voice_runtime_preflight -maxdepth 1 -type f | sort
```

Implementation-stage commands for `full-stack-software-engineer`:

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
rg -n "software_proof_o7_voice_runtime_preflight_only|voice runtime preflight|real_voice_api_connected=false|real_asr_tts_runtime_connected=false|tts_send_enabled=false|speaker_dispatch_enabled=false|safe_to_control=false|delivery_success=false" pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_11-35_o7_voice_runtime_preflight
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_11-35_o7_voice_runtime_preflight
```

If implementation touches O6 archive events unexpectedly, owner must also run the targeted Python relay tests and explain why O6 was required. Default plan assumes O6 is not needed.

## 子 Agent Prompt 要点

When dispatching the implementation owner, include:

- Role: `full-stack-software-engineer`
- Task: implement O7 PC/Node voice runtime preflight software proof.
- File scope: workstation server/client/components/shared tests, `docs/product/pc_tools_workstation.md`, and this sprint `tech-done.md`.
- Required proof boundary: `software_proof_o7_voice_runtime_preflight_only`.
- Required false fields: `real_voice_api_connected=false`, `real_asr_tts_runtime_connected=false`, `tts_send_enabled=false`, `speaker_dispatch_enabled=false`, `safe_to_control=false`, `delivery_success=false`.
- Required validation: workstation tests/build/lint, anchor rg, scoped diff check.

## Product Acceptance Gate

Product should accept only if:

- The evidence is deterministic and reproducible in local/CI workstation mode.
- The output distinguishes configured/offline preflight from real runtime connection.
- All dangerous true fields are rejected or fixed false.
- No real side effects occur.
- `tech-done.md` contains actual changed files, validation output, failure/repair notes if any, remaining risk, and next required live evidence.

Product should keep KR status as `不归档` unless a future, separately authorized sprint supplies real voice runtime evidence plus current mission evidence, which is outside this plan.
