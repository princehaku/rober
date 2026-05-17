# Sprint 2026.05.17_22-23 Wave Rover HIL Packet Review Decision - Tech Plan

sprint_type: epic

## 1. Goal

新增 `wave_rover_hil_packet_review_decision` software-proof gate，消费上一轮 `wave_rover_hil_packet_intake` artifact/summary，把 future WAVE ROVER HIL packet 材料转成 review decision、required material 状态、next evidence、owner handoff 和 rerun commands。

目标 artifact 只能证明：`software_proof_docker_wave_rover_hil_packet_review_decision_gate`。

目标 artifact 必须保持：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

不得声明：`hil_pass`、真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 route/elevator field pass、真实手机/browser、Objective 5 external proof 或 delivery success。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否，转向 Objective 1。
- 如不针对，理由：
  - Objective 5 继续提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前主机只有 Docker，没有这些外部材料。
  - Objective 2 / Objective 3 / Objective 4 已约 99%。PR #4 与 PR #5 已把 elevator / hardware baseline 写成必达产品边界，但真实 route/elevator field materials 和真实硬件材料仍缺；继续本地 metadata 不能替代 field pass 或硬件 source。
  - 近几轮 route/elevator result chain 已到 Docker/local software-proof 上限，不应继续堆同一方向。
  - Objective 1 约 79%，且最新两个 sprint `2026.05.17_20-21_wave-rover-feedback-replay-gate` 和 `2026.05.17_21-22_wave-rover-hil-packet-intake` 已完成 replay 与 intake software-proof；下一条可行动作是补 `wave_rover_hil_packet_review_decision`，让未来真实 packet 有 accepted/missing/rejected 评审和 owner handoff。
- final.md 收口时需复核：O5 stop rule 是否仍成立；O1 是否仍只有 synthetic fixture；是否有任何真实 HIL packet 被提供。

## 2. PR / Review Evidence

- PR #5 P1 review thread：默认硬件集合与 mandatory `monocular + 2D LiDAR + ToF` baseline 未对齐；本轮不能用 HIL packet review decision 替代真实 baseline/source 对齐。
- PR #5 P2 review thread：mandatory sensor assumptions 缺 `docs/vendor/` 来源；后续 hardware-engineer 必须引用 `docs/vendor/VENDOR_INDEX.md` 和 vendor 文件，不能凭记忆写 WAVE ROVER、UART、反馈协议或传感器假设。
- PR #4 / PR #5 共同主题：elevator assisted delivery 和硬件 baseline 已是必达产品边界；但当前缺真实电梯、真实 route/elevator field materials、真实 2D LiDAR / ToF source、采购、安装、接线、电源、标定和 HIL-entry 材料。
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/final.md` 未完成风险：仍缺真实 WAVE ROVER、真实 UART、真实 feedback log、真实 topic snapshots 和同一 `evidence_ref` 的 packet。
- `sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/final.md` 未完成风险：仍缺真实 HIL，不得声明 `hil_pass`；仍缺真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 route/elevator field pass、真实手机/browser、Objective 5 external proof 或 delivery success。

## 3. Evidence Inputs

实现阶段必须消费上一轮 intake artifact/summary，而不是直接声称硬件通过。

Expected input fields:

- `schema=trashbot.wave_rover_hil_packet_intake.v1` 或 `summary_schema=trashbot.wave_rover_hil_packet_intake_summary.v1`
- `evidence_boundary=software_proof_docker_wave_rover_hil_packet_intake_gate`
- `source=software_proof`
- `overall_status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`
- `required_files` 包含 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report`
- `not_proven` 包含 real WAVE ROVER / real UART / `hil_pass` / real odom / real imu / real battery / delivery success

Vendor source boundary:

- 必读入口：`docs/vendor/VENDOR_INDEX.md`。
- WAVE ROVER command / feedback source：`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`。
- UART control source：`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`。
- Vendor upper-computer UART JSON reference：`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`。
- Vendor command IDs / feedback config reference：`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`。

## 4. Output Contract

PC gate summary 至少包含：

```json
{
  "schema": "trashbot.wave_rover_hil_packet_review_decision.v1",
  "summary_schema": "trashbot.wave_rover_hil_packet_review_decision_summary.v1",
  "evidence_boundary": "software_proof_docker_wave_rover_hil_packet_review_decision_gate",
  "source": "software_proof",
  "overall_status": "not_proven",
  "review_decision": "blocked_pending_real_hil_packet",
  "delivery_success": false,
  "primary_actions_enabled": false,
  "same_evidence_ref_required": true,
  "accepted_required_materials": [],
  "missing_required_materials": [
    "real feedback_T1001.log",
    "real odom_once.jsonl",
    "real imu_once.jsonl",
    "real battery_once.jsonl",
    "operator_hil_report"
  ],
  "rejected_required_materials": [],
  "next_required_evidence": [
    "real WAVE ROVER HIL run",
    "same evidence_ref HIL packet",
    "real feedback_T1001.log",
    "real odom_once.jsonl",
    "real imu_once.jsonl",
    "real battery_once.jsonl",
    "operator_hil_report"
  ],
  "owner_handoff": {
    "hardware-engineer": "collect real HIL packet on a host with WAVE ROVER UART access",
    "robot-software-engineer": "keep diagnostics read-only until review_decision changes with real evidence",
    "full-stack-software-engineer": "keep mobile panel read-only and actions disabled"
  },
  "rerun_commands": [
    "python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --packet-dir <real_packet_dir>",
    "python3 pc-tools/evidence/wave_rover_hil_packet_review_decision.py --intake-summary <summary.json>"
  ],
  "not_proven": [
    "real_wave_rover",
    "real_uart",
    "hil_pass",
    "real_odom",
    "real_imu",
    "real_battery",
    "delivery_success"
  ]
}
```

## 5. Team Plan

### Task A - hardware-engineer - PC HIL packet review decision gate

Owner：hardware-engineer。

Files allowed for implementation sprint:

- `pc-tools/evidence/wave_rover_hil_packet_review_decision.py`
- `pc-tools/evidence/test_wave_rover_hil_packet_review_decision.py`
- `pc-tools/evidence/fixtures/wave_rover_hil_packet_review_decision/`
- `docs/hardware/wave_rover_hil_packet_review_decision.md`

Scope:

- Read `docs/vendor/VENDOR_INDEX.md` and referenced WAVE ROVER files before implementation.
- Consume only intake artifact/summary; do not open serial, do not probe `/dev/*`, do not call ROS graph.
- Reuse safe parsing patterns from the 21-22 intake gate where appropriate, but output new schema names for review decision.
- Validate intake schema, evidence boundary, same `evidence_ref`, material status, safe boundary flags, next evidence, owner handoff and rerun commands.
- Fail closed for missing intake summary, malformed JSON, unsupported schema, evidence_ref mismatch, unsafe local path leakage, `delivery_success=true`, `primary_actions_enabled=true`, or `hil_pass` claim.
- Emit synthetic accepted/missing/rejected fixtures only as software proof.
- Hardware doc must cite `docs/vendor/VENDOR_INDEX.md`, `json_cmd.h`, `uart_ctrl.h`, `base_ctrl.py`, and `config.yaml`.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/wave_rover_hil_packet_review_decision.py pc-tools/evidence/test_wave_rover_hil_packet_review_decision.py
python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_review_decision.py
python3 pc-tools/evidence/wave_rover_hil_packet_review_decision.py --help
rg -n "wave_rover_hil_packet_review_decision|software_proof_docker_wave_rover_hil_packet_review_decision_gate|accepted_required_materials|missing_required_materials|rejected_required_materials|owner_handoff|rerun_commands|not_proven|delivery_success=false|primary_actions_enabled=false|VENDOR_INDEX|json_cmd.h|uart_ctrl.h|base_ctrl.py|config.yaml" pc-tools/evidence docs/hardware
git diff --check -- pc-tools/evidence/wave_rover_hil_packet_review_decision.py pc-tools/evidence/test_wave_rover_hil_packet_review_decision.py docs/hardware/wave_rover_hil_packet_review_decision.md
```

### Task B - robot-software-engineer - diagnostics review decision consumer

Owner：robot-software-engineer。

Files allowed for implementation sprint:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Scope:

- Add metadata-only consumer for `wave_rover_hil_packet_review_decision` summary.
- Support top-level and nested summary envelope if existing diagnostics patterns support that shape.
- Surface review decision, accepted/missing/rejected required materials, next required evidence, owner handoff and rerun commands as diagnostics-safe metadata.
- Fail closed for missing schema, unsupported boundary, evidence_ref mismatch, missing `not_proven`, missing `delivery_success=false`, missing `primary_actions_enabled=false`, or unsafe success copy.
- Never publish command, never enable primary action, never claim HIL.
- Keep existing WAVE ROVER feedback replay and HIL packet intake diagnostics behavior intact.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "wave_rover_hil_packet_review_decision|software_proof_docker_wave_rover_hil_packet_review_decision_gate|accepted_required_materials|missing_required_materials|rejected_required_materials|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - full-stack-software-engineer - mobile read-only review panel

Owner：full-stack-software-engineer。

Files allowed for implementation sprint:

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Scope:

- Add read-only "WAVE ROVER HIL packet review decision" panel.
- Show safe fields only: review decision, safe evidence_ref, accepted/missing/rejected required material summary, next required evidence, owner handoff, rerun commands, boundary flags, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`.
- Do not display raw artifact path, local absolute path, serial device, baudrate, raw ROS topic, traceback, checksum, credentials, `/cmd_vel`, or full raw feedback.
- Preserve Start Delivery / Confirm Dropoff / Cancel gating.
- Keep copy Chinese-first and clear that this is not HIL pass.

Acceptance commands:

```bash
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "wave_rover_hil_packet_review_decision|software_proof_docker_wave_rover_hil_packet_review_decision_gate|accepted_required_materials|missing_required_materials|rejected_required_materials|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - product-okr-owner - closeout

Owner：product-okr-owner。

Files allowed for implementation sprint:

- `sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/tech-done.md`
- `sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/side2side_check.md`
- `sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Scope:

- Verify A/B/C outputs and logs.
- Update sprint closeout with actual changed files, validation output, failures, residual risks.
- Update OKR only conservatively. If there is no real HIL packet, do not claim Objective 1 `hil_pass`; write this as HIL packet review decision software proof.
- Re-state Objective 5 stop rule and PR #4 / PR #5 boundaries.
- Confirm docs under `docs/` changed by implementation owners are synchronized with code behavior.

Acceptance commands:

```bash
test -f sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/tech-done.md && test -f sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/side2side_check.md && test -f sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/final.md
rg -n "software_proof_docker_wave_rover_hil_packet_review_decision_gate|Objective 1|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|hil_pass" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision
```

## 6. Parallelization

This sprint is cross-owner and must launch 3 implementation workers in parallel after planning:

- hardware-engineer owns PC review-decision gate, fixtures, tests, and hardware doc.
- robot-software-engineer owns diagnostics consumer, tests, and ROS contract doc.
- full-stack-software-engineer owns mobile/web read-only panel, fixture/test, and product doc.

Product closeout runs after the three workers finish. The workers are not alone in the codebase; they must not revert edits from other workers and must keep write sets within the listed file scopes.

## 7. Interface Boundaries

- PC gate is the source of the HIL packet review decision summary contract.
- Robot diagnostics and mobile/web consume the summary read-only.
- No worker may change WAVE ROVER launch defaults, serial device names, baudrate defaults, `/cmd_vel` behavior, task orchestrator primary actions, cloud/O5 runtime, route/elevator result chain, or previous HIL packet intake schema unless explicitly reassigned.
- Any hardware fact must cite local vendor material, not memory or web search.
- Code technical comments added by implementation workers must be Chinese and meaningful; owners must keep the new code above the project comment-density requirement.

## 8. Required Boundary Language

Every implementation surface and closeout document must preserve these exact tokens:

- `software_proof_docker_wave_rover_hil_packet_review_decision_gate`
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

## 9. Planning Validation Commands

Product planning docs must pass:

```bash
test -f sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/pre_start.md && test -f sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/prd.md && test -f sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PR #4|PR #5|software_proof_docker_wave_rover_hil_packet_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|hardware-engineer|robot-software-engineer|full-stack-software-engineer" sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision
git diff --check -- sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision
```
