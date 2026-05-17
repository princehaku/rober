# Sprint 2026.05.17_20-21 Wave Rover Feedback Replay Gate - Tech Plan

sprint_type: epic

## 1. Goal

实现 WAVE ROVER `T=1001` feedback log replay / interval / topic-alignment gate，作为真实 HIL 前的 Docker-only 验收工具。

目标 artifact 只能证明：`software_proof_docker_wave_rover_feedback_replay_gate`。

目标 artifact 必须保持：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

不得声明：`hil_pass`、真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 route/elevator field pass、真实手机/browser 或 Objective 5 external proof。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不针对 Objective 5，转向 Objective 1。
3. 具体理由：
   - `OKR.md` 第 6 节明确继续 Objective 5 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。当前主机只有 Docker，没有这些外部材料。
   - 最近 `2026.05.17_17-18`、`18-19`、`19-20` route-task result chain 已连续把 PR #4 route/elevator 材料链推进到 dispatch/intake/review-decision，但仍是 Docker-only metadata software proof；Objective 2/3/4 已约 99%，继续本地包装不能越过真实现场 blocker。
   - PR #5 review 指出 hardware baseline、2D LiDAR / ToF、vendor source 和 OKR lowest narrative 问题；最近 hardware chain 已做 baseline/source/procurement/HIL-entry execution-pack，但仍缺真实串口、`T=1001`、2D LiDAR / ToF 真实材料。
   - Objective 1 约 77%，下一条 Docker-only 可行动作是补一个真实 HIL 前必须用到的 replay/interval/topic-alignment gate。它不替代 `hil_pass`，但能降低未来真实硬件材料回填时的验收歧义。

## 2. Evidence Inputs

实现阶段必须围绕以下 input contract：

- `feedback_T1001.log`：每行一个 JSON feedback 或带 timestamp wrapper 的 feedback record；真实 HIL 后产生，本轮用 synthetic fixture。
- `odom_once.jsonl`：一次 `/odom` snapshot normalized record。
- `imu_once.jsonl`：一次 `/imu/data` snapshot normalized record。
- `battery_once.jsonl`：一次 `/battery` snapshot normalized record。
- `evidence_ref`：所有文件必须共享同一 safe evidence ref。

Vendor source boundary：

- 必读入口：`docs/vendor/VENDOR_INDEX.md`。
- WAVE ROVER command / feedback source：`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`。
- Vendor upper-computer UART JSON reference：`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`。
- Vendor command IDs / feedback config reference：`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`。

## 3. Output Contract

PC gate summary 至少包含：

```json
{
  "schema": "trashbot.wave_rover_feedback_replay.v1",
  "evidence_boundary": "software_proof_docker_wave_rover_feedback_replay_gate",
  "source": "software_proof",
  "overall_status": "not_proven",
  "delivery_success": false,
  "primary_actions_enabled": false,
  "feedback_replay_status": "pass_or_blocked",
  "interval_status": "pass_or_blocked",
  "topic_alignment_status": "pass_or_blocked",
  "same_evidence_ref_required": true,
  "not_proven": [
    "real_wave_rover",
    "real_uart",
    "hil_pass",
    "real_odom",
    "real_imu",
    "real_battery",
    "delivery_success"
  ],
  "next_required_evidence": [
    "real feedback_T1001.log",
    "real odom_once.jsonl",
    "real imu_once.jsonl",
    "real battery_once.jsonl",
    "same evidence_ref HIL packet"
  ]
}
```

## 4. Team Plan

### Task A - hardware-engineer - PC replay gate

Owner：hardware-engineer。

Files allowed for implementation sprint:

- `pc-tools/evidence/wave_rover_feedback_replay_gate.py`
- `pc-tools/evidence/test_wave_rover_feedback_replay_gate.py`
- `pc-tools/evidence/fixtures/wave_rover_feedback_replay/`
- `docs/hardware/wave_rover_feedback_replay_gate.md`

Scope:

- Parse `feedback_T1001.log` as file input only; do not open serial.
- Normalize supported T=1001 feedback records.
- Compute interval summary from record timestamps or wrapper timestamps.
- Fail closed when feedback is empty, malformed, unordered, timestamp-less when interval check is required, missing required keys, or unsafe fields appear.
- Load `odom_once.jsonl` / `imu_once.jsonl` / `battery_once.jsonl` and check same evidence ref plus minimal field presence.
- Emit `schema=trashbot.wave_rover_feedback_replay.v1` and fixed boundary flags.
- Add synthetic pass and failure fixtures.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/wave_rover_feedback_replay_gate.py pc-tools/evidence/test_wave_rover_feedback_replay_gate.py
python3 -m unittest pc-tools/evidence/test_wave_rover_feedback_replay_gate.py
python3 pc-tools/evidence/wave_rover_feedback_replay_gate.py --help
rg -n "wave_rover_feedback_replay|software_proof_docker_wave_rover_feedback_replay_gate|T=1001|feedback_T1001|not_proven|delivery_success=false|primary_actions_enabled=false|VENDOR_INDEX|json_cmd.h" pc-tools/evidence docs/hardware
git diff --check -- pc-tools/evidence/wave_rover_feedback_replay_gate.py pc-tools/evidence/test_wave_rover_feedback_replay_gate.py docs/hardware/wave_rover_feedback_replay_gate.md
```

### Task B - robot-software-engineer - diagnostics consumer

Owner：robot-software-engineer。

Files allowed for implementation sprint:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Scope:

- Add metadata-only consumer for `wave_rover_feedback_replay` summary.
- Support top-level and nested summary envelope if existing diagnostics patterns support that shape.
- Fail closed for missing schema, unsupported boundary, evidence_ref mismatch, missing `not_proven`, or missing `delivery_success=false` / `primary_actions_enabled=false`.
- Never publish command, never enable primary action, never claim HIL.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "wave_rover_feedback_replay|software_proof_docker_wave_rover_feedback_replay_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - full-stack-software-engineer - mobile read-only panel

Owner：full-stack-software-engineer。

Files allowed for implementation sprint:

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Scope:

- Add read-only “WAVE ROVER feedback replay” panel.
- Show safe fields only: replay verdict, interval summary, topic alignment, evidence boundary, next required evidence, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`.
- Do not display raw artifact path, local absolute path, serial device, baudrate, raw ROS topic, traceback, checksum, credentials, `/cmd_vel`, or full raw feedback.
- Preserve Start Delivery / Confirm Dropoff / Cancel gating.

Acceptance commands:

```bash
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "wave_rover_feedback_replay|software_proof_docker_wave_rover_feedback_replay_gate|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - product-okr-owner - closeout

Owner：product-okr-owner。

Files allowed for implementation sprint:

- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/tech-done.md`
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/side2side_check.md`
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Scope:

- Verify A/B/C outputs and logs.
- Update sprint closeout with actual changed files, validation output, failures, residual risks.
- Update OKR only conservatively. If there is no real HIL, do not claim Objective 1 `hil_pass`; write this as HIL-prep replay gate software proof.
- Re-state Objective 5 stop rule and PR #4/#5 boundaries.

Acceptance commands:

```bash
test -f sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/tech-done.md && test -f sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/side2side_check.md && test -f sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/final.md
rg -n "software_proof_docker_wave_rover_feedback_replay_gate|Objective 1|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|hil_pass" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate
```

## 5. Parallelization

This sprint is cross-owner and should launch 3 implementation workers in parallel after planning:

- hardware-engineer owns PC gate and fixture.
- robot-software-engineer owns diagnostics consumer.
- full-stack-software-engineer owns mobile/web read-only panel.

Product closeout runs after the three workers finish. The workers are not alone in the codebase; they must not revert edits from other workers and must keep their write sets within the listed file scopes.

## 6. Interface Boundaries

- PC gate is the source of the replay summary contract.
- Robot diagnostics and mobile/web must consume the summary read-only.
- No worker may change WAVE ROVER launch defaults, serial device names, baudrate defaults, `/cmd_vel` behavior, task orchestrator primary actions, cloud/O5 runtime, or route/elevator result chain unless explicitly reassigned.
- Any hardware fact must cite local vendor material, not memory or web search.

## 7. Required Boundary Language

Every implementation surface and closeout document must preserve these exact tokens:

- `software_proof_docker_wave_rover_feedback_replay_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

Disallowed success language unless real HIL evidence exists:

- `hil_pass`
- real WAVE ROVER pass
- real UART pass
- real `/odom` pass
- real `/imu/data` pass
- real `/battery` pass
- delivery success
- route/elevator field pass
- Objective 5 external proof

## 8. Planning Validation Commands

Product planning docs must pass:

```bash
test -f sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/pre_start.md && test -f sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/prd.md && test -f sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PR #4|PR #5|software_proof_docker_wave_rover_feedback_replay_gate|not_proven|delivery_success=false|primary_actions_enabled=false|hardware-engineer|robot-software-engineer|full-stack-software-engineer" sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate
git diff --check -- sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate
```
