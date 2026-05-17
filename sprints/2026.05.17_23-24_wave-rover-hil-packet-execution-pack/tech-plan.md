# Sprint 2026.05.17_23-24 Wave Rover HIL Packet Execution Pack - Tech Plan

sprint_type: epic

## 1. Goal

新增 `wave_rover_hil_packet_execution_pack` software-proof gate，消费上一轮 `wave_rover_hil_packet_review_decision` artifact/summary，把 review decision 转成真实 WAVE ROVER HIL packet 的执行包：材料模板、采集顺序、owner handoff、backfill guidance 和 rerun commands。

目标 artifact 只能证明：`software_proof_docker_wave_rover_hil_packet_execution_pack_gate`。

目标 artifact 必须保持：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

不得声明：`hil_pass`、真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 route/elevator field pass、真实手机/browser、Objective 5 external proof 或 delivery success。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否，转向 Objective 1。
- 如不针对，理由：
  - Objective 5 继续提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前主机只有 Docker，没有这些外部材料。
  - Objective 2 / Objective 3 / Objective 4 已约 99%，继续本地 metadata 不能替代 route/elevator field pass、真实手机或 delivery success。
  - Objective 1 当前约 80%，是下一低完成度；上一轮 review decision final 明确缺真实 HIL packet 材料，且下一条 Docker-only 可行动作是把 review decision 固化为可交给真实硬件环境执行的 execution pack。
- final.md 收口时需复核：O5 stop rule 是否仍成立；O1 是否仍只有 software-proof execution pack；是否有任何真实 HIL packet 被提供。

## 2. PR / Review Evidence

- PR #5 P1 review thread：默认硬件集合与 mandatory `monocular + 2D LiDAR + ToF` baseline 未对齐；本轮不能用 WAVE ROVER execution pack 替代真实 sensor baseline/source 材料。
- PR #5 P2 review thread：mandatory sensor assumptions 缺 `docs/vendor/` 来源；hardware-engineer 必须引用 `docs/vendor/VENDOR_INDEX.md` 和 WAVE ROVER vendor 文件。
- PR #4 / PR #5 共同主题：elevator assisted delivery 和硬件 baseline 已是必达产品边界；但当前缺真实电梯、真实 route/elevator field materials、真实 2D LiDAR / ToF source、采购、安装、接线、电源、标定和 HIL-entry 材料。
- `sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/final.md` 未完成风险：仍缺真实 WAVE ROVER、真实 UART、真实串口日志、真实 `feedback_T1001.log`、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 和同一 `evidence_ref` 的上车实机复账。

## 3. Evidence Inputs

实现阶段必须消费上一轮 review decision artifact/summary，而不是直接声称硬件通过。

Expected input fields:

- `schema=trashbot.wave_rover_hil_packet_review_decision.v1` 或 `summary_schema=trashbot.wave_rover_hil_packet_review_decision_summary.v1`
- `evidence_boundary=software_proof_docker_wave_rover_hil_packet_review_decision_gate`
- `source=software_proof`
- `overall_status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`
- `review_decision=blocked_pending_real_hil_packet`
- `next_required_evidence` 包含真实 WAVE ROVER HIL run、same evidence_ref HIL packet、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 和 `operator_hil_report`
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
  "schema": "trashbot.wave_rover_hil_packet_execution_pack.v1",
  "summary_schema": "trashbot.wave_rover_hil_packet_execution_pack_summary.v1",
  "evidence_boundary": "software_proof_docker_wave_rover_hil_packet_execution_pack_gate",
  "source": "software_proof",
  "overall_status": "not_proven",
  "execution_pack_status": "ready_for_real_hil_collection_not_proven",
  "delivery_success": false,
  "primary_actions_enabled": false,
  "same_evidence_ref_required": true,
  "required_material_templates": [
    "feedback_T1001.log",
    "odom_once.jsonl",
    "imu_once.jsonl",
    "battery_once.jsonl",
    "operator_hil_report"
  ],
  "collection_sequence": [
    "confirm WAVE ROVER UART access on target host",
    "collect same evidence_ref feedback_T1001.log",
    "capture odom_once.jsonl",
    "capture imu_once.jsonl",
    "capture battery_once.jsonl",
    "write operator_hil_report",
    "rerun packet intake and review decision gates"
  ],
  "owner_handoff": {
    "hardware-engineer": "run real HIL collection on WAVE ROVER host",
    "robot-software-engineer": "consume only accepted review-decision summaries until real packet exists",
    "full-stack-software-engineer": "keep mobile execution pack read-only and actions disabled"
  },
  "rerun_commands": [
    "python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --packet-dir <real_packet_dir>",
    "python3 pc-tools/evidence/wave_rover_hil_packet_review_decision.py --intake-summary <summary.json>",
    "python3 pc-tools/evidence/wave_rover_hil_packet_execution_pack.py --review-summary <summary.json>"
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

### Task A - hardware-engineer - PC HIL packet execution-pack gate

Owner：hardware-engineer。

Files allowed for implementation sprint:

- `pc-tools/evidence/wave_rover_hil_packet_execution_pack.py`
- `pc-tools/evidence/test_wave_rover_hil_packet_execution_pack.py`
- `pc-tools/evidence/fixtures/wave_rover_hil_packet_execution_pack/`
- `docs/hardware/wave_rover_hil_packet_execution_pack.md`

Scope:

- Read `docs/vendor/VENDOR_INDEX.md` and referenced WAVE ROVER files before implementation.
- Consume only review-decision artifact/summary; do not open serial, do not probe `/dev/*`, do not call ROS graph.
- Reuse safe parsing patterns from intake/review decision gates where appropriate, but output new schema names for execution pack.
- Validate review-decision schema, evidence boundary, same `evidence_ref`, material status, safe boundary flags, next evidence, owner handoff and rerun commands.
- Fail closed for missing review summary, malformed JSON, unsupported schema, evidence_ref mismatch, unsafe local path leakage, `delivery_success=true`, `primary_actions_enabled=true`, or `hil_pass` claim.
- Hardware doc must cite `docs/vendor/VENDOR_INDEX.md`, `json_cmd.h`, `uart_ctrl.h`, `base_ctrl.py`, and `config.yaml`.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/wave_rover_hil_packet_execution_pack.py pc-tools/evidence/test_wave_rover_hil_packet_execution_pack.py
python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_execution_pack.py
python3 pc-tools/evidence/wave_rover_hil_packet_execution_pack.py --help
rg -n "wave_rover_hil_packet_execution_pack|software_proof_docker_wave_rover_hil_packet_execution_pack_gate|required_material_templates|collection_sequence|owner_handoff|rerun_commands|not_proven|delivery_success=false|primary_actions_enabled=false|VENDOR_INDEX|json_cmd.h|uart_ctrl.h|base_ctrl.py|config.yaml" pc-tools/evidence docs/hardware
git diff --check -- pc-tools/evidence/wave_rover_hil_packet_execution_pack.py pc-tools/evidence/test_wave_rover_hil_packet_execution_pack.py docs/hardware/wave_rover_hil_packet_execution_pack.md
```

### Task B - robot-software-engineer - diagnostics execution-pack consumer

Owner：robot-software-engineer。

Files allowed for implementation sprint:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Scope:

- Add metadata-only consumer for `wave_rover_hil_packet_execution_pack` summary.
- Support top-level and nested summary envelope if existing diagnostics patterns support that shape.
- Surface execution-pack status, required material templates, collection sequence, owner handoff, rerun commands and boundary flags as diagnostics-safe metadata.
- Fail closed for missing schema, unsupported boundary, evidence_ref mismatch, missing `not_proven`, missing `delivery_success=false`, missing `primary_actions_enabled=false`, or unsafe success copy.
- Never publish command, never enable primary action, never claim HIL.
- Keep existing WAVE ROVER feedback replay, HIL packet intake and review-decision diagnostics behavior intact.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "wave_rover_hil_packet_execution_pack|software_proof_docker_wave_rover_hil_packet_execution_pack_gate|required_material_templates|collection_sequence|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - full-stack-software-engineer - mobile read-only execution-pack panel

Owner：full-stack-software-engineer。

Files allowed for implementation sprint:

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Scope:

- Add read-only "WAVE ROVER HIL packet execution pack" panel.
- Show safe fields only: execution-pack status, safe evidence_ref, required material templates, collection sequence, owner handoff, rerun commands, boundary flags, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`.
- Do not display raw artifact path, local absolute path, serial device, baudrate, raw ROS topic, traceback, checksum, credentials, `/cmd_vel`, or full raw feedback.
- Preserve Start Delivery / Confirm Dropoff / Cancel gating.
- Keep copy Chinese-first and clear that this is not HIL pass.

Acceptance commands:

```bash
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "wave_rover_hil_packet_execution_pack|software_proof_docker_wave_rover_hil_packet_execution_pack_gate|required_material_templates|collection_sequence|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - product-okr-owner - closeout

Owner：product-okr-owner。

Files allowed for implementation sprint:

- `sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/tech-done.md`
- `sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/side2side_check.md`
- `sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Scope:

- Verify A/B/C outputs and logs.
- Update sprint closeout with actual changed files, validation output, failures, residual risks.
- Update OKR only conservatively. If there is no real HIL packet, do not claim Objective 1 `hil_pass`; write this as HIL packet execution-pack software proof.
- Re-state Objective 5 stop rule and PR #4 / PR #5 boundaries.
- Confirm docs under `docs/` changed by implementation owners are synchronized with code behavior.

Acceptance commands:

```bash
test -f sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/tech-done.md && test -f sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/side2side_check.md && test -f sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack/final.md
rg -n "software_proof_docker_wave_rover_hil_packet_execution_pack_gate|Objective 1|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|hil_pass" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_23-24_wave-rover-hil-packet-execution-pack
```

## 6. Parallelization

This sprint is cross-owner and must launch 3 implementation workers in parallel after planning:

- hardware-engineer owns PC execution-pack gate, fixtures, tests, and hardware doc.
- robot-software-engineer owns diagnostics consumer, tests, and ROS contract doc.
- full-stack-software-engineer owns mobile/web read-only panel, fixture/test, and product doc.

Product closeout runs after the three workers finish. The workers are not alone in the codebase; they must not revert edits from other workers and must keep write sets within the listed file scopes.

## 7. Interface Boundaries

- PC execution pack is an offline evidence artifact only.
- Robot diagnostics consumes sanitized summary only.
- Mobile/web shows read-only support state only.
- No task action, ACK, cursor, Start Delivery, Confirm Dropoff, Cancel, `/cmd_vel`, serial, UART, HIL, route/elevator field pass, cloud external proof or delivery success is enabled by this sprint.
