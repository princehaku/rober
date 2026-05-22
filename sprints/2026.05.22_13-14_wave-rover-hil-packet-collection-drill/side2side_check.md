# WAVE ROVER HIL Packet Collection Drill Side2Side Check

Run time: 2026-05-22 13:44 Asia/Shanghai

## Sprint Type

- `sprint_type: epic`
- Capability: `wave_rover_hil_packet_collection_drill`
- Evidence boundary: `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`

## User Value And Product North Star

用户价值：field owner 现在有一条可演练的 WAVE ROVER HIL packet 采集链路，能在真实上车前预先检查 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 和 `operator_hil_report` 是否按同一 safe `evidence_ref` 准备齐套。

产品北极星：普通手机用户和 support 只能看到安全、可解释、不可误操作的采集准备状态。没有真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 和 operator HIL report 前，产品不能显示 HIL 通过、送达完成或启用主操作。

## OKR Mapping

- Primary Objective: Objective 1，因为本 sprint 针对硬件协议可信底盘的 HIL packet collection readiness。
- Objective 5 仍是最低完成度 Objective，约 68%；本轮不针对它，因为没有真实 external/cloud/terminal-result material。
- Objective 4 只获得 read-only mobile visibility，不获得 true phone/browser proof。
- Objective 2/3 不受本轮提升；本轮没有 route/elevator field pass、Nav2/fixed-route runtime log、dropoff/cancel completion 或 delivery success。

## KR Breakdown

| KR | Owner | Side2Side Result |
| --- | --- | --- |
| Hardware collection drill gate | Hardware Infra Engineer | Completed. PC gate emits collection-drill artifact and summary, validates required HIL packet material templates, and fails closed on unsafe/success claims. |
| Robot diagnostics safe alias | Robot Platform Engineer | Completed. Robot diagnostics exposes `robot_diagnostics_wave_rover_hil_packet_collection_drill_summary` without serial, ACK, cursor, Nav2, route, command, or HIL side effects. |
| Mobile read-only panel | User Touchpoint Full-Stack Engineer | Completed. `mobile/web` renders the safe collection-drill panel and keeps Start Delivery / Confirm Dropoff / Cancel disabled. |
| Product closeout | Product Manager / OKR Owner | Completed. Sprint closeout docs, `OKR.md`, and progress log were updated with conservative software-proof language. |

## Priority And Acceptance Check

Acceptance criteria from PRD / tech-plan:

- PC gate consumes execution-pack artifact or summary and emits `trashbot.wave_rover_hil_packet_collection_drill.v1`: accepted by Task A evidence.
- Required materials include `feedback_T1001.log`, `odom_once.jsonl`, `imu_once.jsonl`, `battery_once.jsonl`, and `operator_hil_report`: accepted by Task A evidence and docs.
- Robot diagnostics consumes only sanitized summary forms and fails closed: accepted by Task B evidence.
- Mobile/web shows only safe status, material templates, checklist, sequence, backfill commands, owner handoff, and no-overclaim flags: accepted by Task C evidence.
- All surfaces keep `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`: accepted across A/B/C/D evidence.
- Product closeout updates sprint docs, `OKR.md`, and progress log without percentage lift: accepted by this closeout.

## Evidence Chain

- Task A worker evidence: `py_compile` pass; `python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_collection_drill.py` -> `Ran 9 tests ... OK`; CLI `--help` pass; required `rg` pass; scoped `git diff --check` pass.
- Task B worker evidence: `py_compile` pass; `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` -> `Ran 286 tests ... OK`; required `rg` pass; scoped `git diff --check` pass.
- Task C worker evidence: `node --check` pass; `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` -> `Ran 257 tests ... OK`; fixture `json.tool` pass; required `rg` pass; scoped `git diff --check` pass.
- Product integration acceptance: `py_compile` pass; integrated unittest run -> `Ran 552 tests in 3.836s OK`; CLI `--help` pass; `node --check` pass; fixture `json.tool` pass; required `rg` pass; scoped `git diff --check` pass.

## No-Overclaim Check

This sprint remains `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`.

It does not prove:

- real WAVE ROVER or real UART/serial
- real `/odom`, `/imu/data`, or `/battery`
- real HIL or `hil_pass`
- real 2D LiDAR / ToF SKU, source, receipt, procurement, installation, wiring, power, calibration, or HIL-entry
- PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution
- true phone/browser proof or real iPhone/Android behavior
- Objective 5 external proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, or worker/cutover
- route/elevator field pass, Nav2/fixed-route proof, dropoff/cancel completion, verified terminal result, or delivery success

## Risks And Evidence Gaps

- Objective 1 remains blocked on real WAVE ROVER powered bench/UART/HIL packet captures, real operator HIL report, and PR #5 hardware material / reviewer resolution.
- Objective 5 remains blocked on real external cloud material or verified terminal delivery/dropoff/cancel result material.
- Objective 4 remains blocked on true phone/browser evidence, real iPhone/Android behavior, production app, and real PWA prompt/userChoice.
- Objective 2/3 remain blocked on real task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor evidence, dropoff/cancel completion, and delivery result under the same safe `evidence_ref`.
