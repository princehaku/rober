# WAVE ROVER HIL Packet Collection Drill Tech Plan

Run time: 2026-05-22 13:06 Asia/Shanghai

## Implementation Plan Header

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven implementation discipline. Main session only performs kickoff, acceptance review, sprint documentation, and closeout; product code, tests, hardware config, and implementation validation belong to the assigned workers.

**Goal:** Build `wave_rover_hil_packet_collection_drill` as a Docker-only, fail-closed WAVE ROVER HIL packet collection drill gate across PC, Robot diagnostics, and `mobile/web`.

**Architecture:** Hardware owns the canonical PC artifact/summary gate. Robot owns the metadata-only safe alias and `/api/status` / `/api/diagnostics` exposure. Full-Stack owns the read-only phone panel that consumes only safe summaries and keeps all primary actions disabled.

**Tech Stack:** Python 3 dependency-free PC evidence tools, Python unittest diagnostics tests, static `mobile/web` JavaScript fixture tests, repo-local Markdown docs, scoped `git diff --check`.

---

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 当前次低 Objective：Objective 1，约 81%。
- 本 sprint 是否针对最低 Objective：否。
- 不针对 Objective 5 的理由：最近 `2026.05.22_12-13_verified-terminal-result-material-review-handoff/final.md` 与 `2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/final.md` 已说明 O5 缺真实 external/cloud/terminal-result material，不能继续包装同一 blocker。当前没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser external proof 或 verified terminal result material。
- 本 sprint 针对 Objective 1 的理由：现有 `wave_rover_hil_packet_intake -> review_decision -> execution_pack` 已形成软件证明链，但下一次真实 WAVE ROVER HIL 采集仍缺一个可执行 collection drill gate。本轮推进 `wave_rover_hil_packet_collection_drill`，保留 `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`，不声明真实 HIL。
- final.md 收口时需复核：如果本轮仍无真实 WAVE ROVER/UART/HIL packet、真实 2D LiDAR/ToF material、PR #5 reviewer resolution 或 O5 external material，则不得提升为真实 proof 或 delivery success。

## Existing Contracts To Reuse

- `pc-tools/evidence/wave_rover_hil_packet_intake.py`
- `pc-tools/evidence/wave_rover_hil_packet_review_decision.py`
- `pc-tools/evidence/wave_rover_hil_packet_execution_pack.py`
- `pc-tools/evidence/fixtures/wave_rover_hil_packet_execution_pack/review_ready.json`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/hardware/wave_rover_hil_packet_execution_pack.md`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/mobile_user_flow.md`

## Source Boundary

Worker implementation must cite local vendor facts from:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

Allowed vendor facts:

- WAVE ROVER upper/lower link is UART newline-delimited JSON.
- `json_cmd.h` defines `FEEDBACK_BASE_INFO 1001`.
- `json_cmd.h` defines `CMD_SPEED_CTRL 1`, `CMD_ROS_CTRL 13`, `CMD_BASE_FEEDBACK 130`, `CMD_BASE_FEEDBACK_FLOW 131`, `CMD_FEEDBACK_FLOW_INTERVAL 142`, and `CMD_UART_ECHO_MODE 143`.
- `base_ctrl.py` sends one JSON object plus newline and reads one JSON line.
- Vendor Raspberry Pi reference uses `/dev/ttyAMA0` at `115200`, but Orange Pi target must not hardcode that device path.

These facts must not be expanded into unverified pinout, voltage, installed sensor, serial device, real HIL, real ToF, real 2D LiDAR, procurement, calibration, motion, or delivery claims.

## Parallel Worker Dispatch

This is a 3-owner Epic sprint. When implementation starts, dispatch the following workers in parallel in one message:

1. `hardware-engineer` owns PC gate, fixtures, hardware docs, and hardware-focused tests.
2. `robot-software-engineer` owns diagnostics safe alias, Robot tests, and interface docs.
3. `full-stack-software-engineer` owns `mobile/web` read-only panel, fixtures, mobile tests, and product mobile docs.

Autonomy is not assigned in this sprint because no Nav2, route, elevator, camera, 2D LiDAR or ToF runtime behavior is changed. Product closeout is separate and must happen only after worker evidence returns.

## Task A: Hardware Collection Drill Gate

**Owner:** `hardware-engineer`

**Allowed files:**

- Create: `pc-tools/evidence/wave_rover_hil_packet_collection_drill.py`
- Create: `pc-tools/evidence/test_wave_rover_hil_packet_collection_drill.py`
- Create/modify: `pc-tools/evidence/fixtures/wave_rover_hil_packet_collection_drill/`
- Create: `docs/hardware/wave_rover_hil_packet_collection_drill.md`

**Implementation requirements:**

- Consume `wave_rover_hil_packet_execution_pack` artifact or summary.
- Emit `schema=trashbot.wave_rover_hil_packet_collection_drill.v1`.
- Emit `summary_schema=trashbot.wave_rover_hil_packet_collection_drill_summary.v1`.
- Emit `evidence_boundary=software_proof_docker_wave_rover_hil_packet_collection_drill_gate`.
- Preserve `source=software_proof`, `overall_status=not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `same_evidence_ref_required=true`.
- Output safe fields only: `collection_drill_status`, safe `evidence_ref`, `required_material_templates`, `preflight_checklist`, `collection_sequence`, `backfill_commands`, `owner_handoff`, `blocked_reasons`, `not_proven`, evidence boundary.
- Required material templates must include `feedback_T1001.log`, `odom_once.jsonl`, `imu_once.jsonl`, `battery_once.jsonl`, `operator_hil_report`.
- Fail closed on missing/unsupported execution pack, unsafe `evidence_ref`, unsafe copy, raw path, serial/UART detail, baudrate, checksum, traceback, credential, `/cmd_vel`, `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, or success-like `hil_pass` claim.
- Do not open serial, do not read `/dev/*`, do not import ROS2, do not send WAVE ROVER commands.
- New code comments must be meaningful Chinese comments and keep comment ratio above 20%.

**Validation commands:**

```bash
python3 -m py_compile pc-tools/evidence/wave_rover_hil_packet_collection_drill.py pc-tools/evidence/test_wave_rover_hil_packet_collection_drill.py
python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_collection_drill.py
python3 pc-tools/evidence/wave_rover_hil_packet_collection_drill.py --help
rg -n "wave_rover_hil_packet_collection_drill|software_proof_docker_wave_rover_hil_packet_collection_drill_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|FEEDBACK_BASE_INFO 1001" pc-tools/evidence docs/hardware/wave_rover_hil_packet_collection_drill.md
git diff --check -- pc-tools/evidence/wave_rover_hil_packet_collection_drill.py pc-tools/evidence/test_wave_rover_hil_packet_collection_drill.py pc-tools/evidence/fixtures/wave_rover_hil_packet_collection_drill docs/hardware/wave_rover_hil_packet_collection_drill.md
```

## Task B: Robot Diagnostics Safe Alias

**Owner:** `robot-software-engineer`

**Allowed files:**

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/operator_gateway_diagnostics.md`

**Implementation requirements:**

- Add constants and summary helpers for `trashbot.wave_rover_hil_packet_collection_drill.v1` and `trashbot.wave_rover_hil_packet_collection_drill_summary.v1`.
- Expose `wave_rover_hil_packet_collection_drill`, `wave_rover_hil_packet_collection_drill_summary`, and `robot_diagnostics_wave_rover_hil_packet_collection_drill_summary` where existing WAVE ROVER HIL packet summaries are exposed.
- Consume status, diagnostics, compatible summary, and nested summary sources following existing WAVE ROVER HIL packet patterns.
- Preserve metadata-only behavior: no serial open, no ACK mutation, no cursor mutation, no Nav2 route, no `/cmd_vel`, no WAVE ROVER command.
- Fail closed with `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` on missing summary or unsafe fields.
- New code comments must be meaningful Chinese comments and keep comment ratio above 20%.

**Validation commands:**

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "wave_rover_hil_packet_collection_drill|robot_diagnostics_wave_rover_hil_packet_collection_drill_summary|software_proof_docker_wave_rover_hil_packet_collection_drill_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
```

## Task C: Mobile Read-Only Panel

**Owner:** `full-stack-software-engineer`

**Allowed files:**

- Modify: `mobile/web/app.js`
- Modify: `mobile/fixtures/mobile_web_status.fixture.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

**Implementation requirements:**

- Add `WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_BOUNDARY`.
- Add summary extraction for `wave_rover_hil_packet_collection_drill`, `wave_rover_hil_packet_collection_drill_summary`, and `robot_diagnostics_wave_rover_hil_packet_collection_drill_summary`.
- Render a read-only panel after the existing WAVE ROVER execution-pack panel.
- Show only safe status, safe `evidence_ref`, required material templates, preflight checklist, collection sequence, backfill/rerun commands, owner handoff, evidence boundary, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Do not add copy/export controls unless copied content is sanitized and explicitly covered by tests.
- Do not expose raw artifact, raw JSON, complete feedback, checksum, local path, serial/UART path, baudrate, credentials, traceback, ROS topic, `/cmd_vel`, true phone/browser proof, real HIL, or success wording.
- Start Delivery / Confirm Dropoff / Cancel must remain disabled.
- New code comments must be meaningful Chinese comments and keep comment ratio above 20%.

**Validation commands:**

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null
rg -n "wave_rover_hil_packet_collection_drill|software_proof_docker_wave_rover_hil_packet_collection_drill_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Integration Acceptance

After Tasks A/B/C return, Product closeout should require:

```bash
python3 -m py_compile pc-tools/evidence/wave_rover_hil_packet_collection_drill.py pc-tools/evidence/test_wave_rover_hil_packet_collection_drill.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_collection_drill.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py
python3 pc-tools/evidence/wave_rover_hil_packet_collection_drill.py --help
node --check mobile/web/app.js
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null
rg -n "wave_rover_hil_packet_collection_drill|software_proof_docker_wave_rover_hil_packet_collection_drill_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" pc-tools/evidence onboard/src/ros2_trashbot_behavior mobile docs sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill
git diff --check -- pc-tools/evidence onboard/src/ros2_trashbot_behavior mobile docs sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill
```

## Evidence Boundary And No-Overclaim Rules

- Required boundary: `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`.
- Required false flags: `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Must not claim: real HIL, `hil_pass`, real WAVE ROVER, real UART, real serial device, real `/odom`, real `/imu/data`, real `/battery`, real 2D LiDAR/ToF, PR #5 reviewer resolved, true phone/browser proof, O5 external proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, route/elevator field pass, dropoff/cancel completion, verified terminal result, or delivery success.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved until reviewer resolves it; comment `3269642220` remains only a software-proof reply.

## Product Kickoff Validation Commands

The Product kickoff owner must run:

```bash
test -f sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill/pre_start.md && test -f sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill/prd.md && test -f sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|wave_rover_hil_packet_collection_drill|software_proof_docker_wave_rover_hil_packet_collection_drill_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill
git diff --check -- sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill
```

## Remaining Risks For Closeout

- This plan does not create real WAVE ROVER/UART/HIL material.
- This plan does not resolve PR #5 thread `PRRT_kwDOSWB9286CJ3tX`.
- This plan does not provide Objective 5 external/cloud/terminal-result material.
- This plan does not update `OKR.md`; Product closeout must decide conservative wording only after worker evidence returns.

