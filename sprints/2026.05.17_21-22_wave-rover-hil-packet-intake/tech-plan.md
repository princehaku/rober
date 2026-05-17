# Sprint 2026.05.17_21-22 Wave Rover HIL Packet Intake - Tech Plan

sprint_type: epic

## 1. Goal

新增 `wave_rover_hil_packet_intake` software-proof gate，把未来真实 WAVE ROVER HIL packet 的必需文件 contract 接入 PC / Robot diagnostics / mobile web / Product closeout 链路。

目标 artifact 只能证明：`software_proof_docker_wave_rover_hil_packet_intake_gate`。

目标 artifact 必须保持：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

不得声明：`hil_pass`、真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 route/elevator field pass、真实手机/browser、Objective 5 external proof 或 delivery success。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否，转向 Objective 1。
- 如不针对，理由：
  - Objective 5 继续提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前主机只有 Docker，没有这些外部材料。
  - Objective 2 / Objective 3 / Objective 4 已约 99%。PR #4 已把 elevator assisted delivery 放入主链路，但真实 route/elevator field materials 仍缺；继续本地 metadata 不能替代 field pass。
  - PR #5 unresolved review threads 指向 hardware baseline/source 和 2D LiDAR / ToF 材料缺口；最近硬件 ladder 已部分修复/承接，但真实 SKU/source/receipt/install/wiring/calibration/HIL-entry 仍缺。
  - Objective 1 约 78%，且最新 20-21 sprint 已完成 `software_proof_docker_wave_rover_feedback_replay_gate`。下一条可行动作是把真实 HIL packet intake contract 做成 fail-closed gate，为未来上车材料回填降低歧义。
- final.md 收口时需复核：O5 stop rule 是否仍成立；O1 是否仍只有 synthetic fixture；是否有任何真实 HIL packet 被提供。

## 2. Evidence Inputs

实现阶段必须围绕以下 packet contract：

- `feedback_T1001.log`：WAVE ROVER `T=1001` feedback log。真实 HIL 后产生，本轮用 synthetic fixture。
- `odom_once.jsonl`：一次 `/odom` snapshot normalized record。
- `imu_once.jsonl`：一次 `/imu/data` snapshot normalized record。
- `battery_once.jsonl`：一次 `/battery` snapshot normalized record。
- `operator_hil_report`：人工 HIL 报告，至少包含 operator、run timestamp、robot id、serial visibility statement、stop-path statement、result boundary 和 notes。
- `evidence_ref`：所有文件必须共享同一 safe evidence ref。

Vendor source boundary：

- 必读入口：`docs/vendor/VENDOR_INDEX.md`。
- WAVE ROVER command / feedback source：`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`。
- UART control source：`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`。
- Vendor upper-computer UART JSON reference：`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`。
- Vendor command IDs / feedback config reference：`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`。

## 3. Output Contract

PC gate summary 至少包含：

```json
{
  "schema": "trashbot.wave_rover_hil_packet_intake.v1",
  "summary_schema": "trashbot.wave_rover_hil_packet_intake_summary.v1",
  "evidence_boundary": "software_proof_docker_wave_rover_hil_packet_intake_gate",
  "source": "software_proof",
  "overall_status": "not_proven",
  "packet_status": "pass_or_blocked",
  "delivery_success": false,
  "primary_actions_enabled": false,
  "same_evidence_ref_required": true,
  "required_files": [
    "feedback_T1001.log",
    "odom_once.jsonl",
    "imu_once.jsonl",
    "battery_once.jsonl",
    "operator_hil_report"
  ],
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
    "real WAVE ROVER HIL run",
    "real feedback_T1001.log",
    "real odom_once.jsonl",
    "real imu_once.jsonl",
    "real battery_once.jsonl",
    "operator_hil_report",
    "same evidence_ref HIL packet"
  ]
}
```

## 4. Team Plan

### Task A - hardware-engineer - PC HIL packet intake gate

Owner：hardware-engineer。

Files allowed for implementation sprint:

- `pc-tools/evidence/wave_rover_hil_packet_intake.py`
- `pc-tools/evidence/test_wave_rover_hil_packet_intake.py`
- `pc-tools/evidence/fixtures/wave_rover_hil_packet_intake/`
- `docs/hardware/wave_rover_hil_packet_intake.md`

Scope:

- Read `docs/vendor/VENDOR_INDEX.md` and referenced WAVE ROVER files before implementation.
- Parse packet directory inputs only; do not open serial, do not probe `/dev/*`, do not call ROS graph.
- Reuse or mirror safe parsing patterns from the 20-21 replay gate where appropriate, but output new schema names for HIL packet intake.
- Validate required files, same `evidence_ref`, operator report presence, safe boundary flags, and no success-claim leakage.
- Fail closed for missing packet directory, missing files, malformed JSON/JSONL/log, unsupported schema, evidence_ref mismatch, unsafe local path leakage, `delivery_success=true`, `primary_actions_enabled=true`, or `hil_pass` claim.
- Emit synthetic pass and failure fixtures only as software proof.
- Hardware doc must cite `docs/vendor/VENDOR_INDEX.md`, `json_cmd.h`, `uart_ctrl.h`, `base_ctrl.py`, and `config.yaml`.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/wave_rover_hil_packet_intake.py pc-tools/evidence/test_wave_rover_hil_packet_intake.py
python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_intake.py
python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --help
rg -n "wave_rover_hil_packet_intake|software_proof_docker_wave_rover_hil_packet_intake_gate|feedback_T1001|operator_hil_report|not_proven|delivery_success=false|primary_actions_enabled=false|VENDOR_INDEX|json_cmd.h|uart_ctrl.h|base_ctrl.py|config.yaml" pc-tools/evidence docs/hardware
git diff --check -- pc-tools/evidence/wave_rover_hil_packet_intake.py pc-tools/evidence/test_wave_rover_hil_packet_intake.py docs/hardware/wave_rover_hil_packet_intake.md
```

### Task B - robot-software-engineer - diagnostics consumer

Owner：robot-software-engineer。

Files allowed for implementation sprint:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Scope:

- Add metadata-only consumer for `wave_rover_hil_packet_intake` summary.
- Support top-level and nested summary envelope if existing diagnostics patterns support that shape.
- Fail closed for missing schema, unsupported boundary, evidence_ref mismatch, missing `not_proven`, missing `delivery_success=false`, missing `primary_actions_enabled=false`, or unsafe success copy.
- Never publish command, never enable primary action, never claim HIL.
- Keep existing WAVE ROVER feedback replay diagnostics behavior intact.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "wave_rover_hil_packet_intake|software_proof_docker_wave_rover_hil_packet_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
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

- Add read-only "WAVE ROVER HIL packet intake" panel.
- Show safe fields only: packet status, safe evidence_ref, missing/required file summary, operator report status, next required evidence, boundary flags, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`.
- Do not display raw artifact path, local absolute path, serial device, baudrate, raw ROS topic, traceback, checksum, credentials, `/cmd_vel`, or full raw feedback.
- Preserve Start Delivery / Confirm Dropoff / Cancel gating.
- Keep copy Chinese-first and clear that this is not HIL pass.

Acceptance commands:

```bash
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "wave_rover_hil_packet_intake|software_proof_docker_wave_rover_hil_packet_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - product-okr-owner - closeout

Owner：product-okr-owner。

Files allowed for implementation sprint:

- `sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/tech-done.md`
- `sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/side2side_check.md`
- `sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Scope:

- Verify A/B/C outputs and logs.
- Update sprint closeout with actual changed files, validation output, failures, residual risks.
- Update OKR only conservatively. If there is no real HIL packet, do not claim Objective 1 `hil_pass`; write this as HIL packet intake software proof.
- Re-state Objective 5 stop rule and PR #4 / PR #5 boundaries.
- Confirm docs under `docs/` changed by implementation owners are synchronized with code behavior.

Acceptance commands:

```bash
test -f sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/tech-done.md && test -f sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/side2side_check.md && test -f sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/final.md
rg -n "software_proof_docker_wave_rover_hil_packet_intake_gate|Objective 1|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|hil_pass" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_21-22_wave-rover-hil-packet-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_21-22_wave-rover-hil-packet-intake
```

## 5. Parallelization

This sprint is cross-owner and must launch 3 implementation workers in parallel after planning:

- hardware-engineer owns PC gate, fixtures, tests, and hardware doc.
- robot-software-engineer owns diagnostics consumer, tests, and ROS contract doc.
- full-stack-software-engineer owns mobile/web read-only panel, fixture/test, and product doc.

Product closeout runs after the three workers finish. The workers are not alone in the codebase; they must not revert edits from other workers and must keep write sets within the listed file scopes.

## 6. Interface Boundaries

- PC gate is the source of the HIL packet intake summary contract.
- Robot diagnostics and mobile/web consume the summary read-only.
- No worker may change WAVE ROVER launch defaults, serial device names, baudrate defaults, `/cmd_vel` behavior, task orchestrator primary actions, cloud/O5 runtime, or route/elevator result chain unless explicitly reassigned.
- Any hardware fact must cite local vendor material, not memory or web search.
- Code technical comments added by implementation workers must be Chinese and meaningful; owners must keep the new code above the project comment-density requirement.

## 7. Required Boundary Language

Every implementation surface and closeout document must preserve these exact tokens:

- `software_proof_docker_wave_rover_hil_packet_intake_gate`
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
test -f sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/pre_start.md && test -f sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/prd.md && test -f sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PR #4|PR #5|software_proof_docker_wave_rover_hil_packet_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|hardware-engineer|robot-software-engineer|full-stack-software-engineer" sprints/2026.05.17_21-22_wave-rover-hil-packet-intake
git diff --check -- sprints/2026.05.17_21-22_wave-rover-hil-packet-intake
```
