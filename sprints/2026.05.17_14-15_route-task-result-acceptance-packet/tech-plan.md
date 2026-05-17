# Sprint 2026.05.17_14-15 Route Task Result Acceptance Packet - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮新增 `route_task_field_retest_result_acceptance_packet`，作为 `route_task_field_retest_result_reconciliation` 后续的 acceptance packet gate。它不新增真实现场材料，不扩大控制能力，只把现有 reconciliation 的 safe lineage、八类 required result materials、缺口、owner handoff、rerun commands 和 pass/fail criteria 汇总为 PC / Robot / mobile 都能只读消费的 packet。

目标 schema / boundary：

- artifact schema：`trashbot.route_task_field_retest_result_acceptance_packet.v1`
- summary schema：`trashbot.route_task_field_retest_result_acceptance_packet_summary.v1`
- evidence boundary：`software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`
- 必须固定输出：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

不新增真实硬件/云/手机 proof，不新增大测试，只用围栏验证。所有实现类 worker 必须更新对应 docs，并在本 sprint `tech-done.md` 写入实际改动、验证结果和剩余风险。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数值最低 Objective：Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。
3. 理由：`OKR.md` 第 6 节明确要求只有拿到真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser 证据时才继续推进 O5 completion。本机没有这些真实外部材料，继续本地 O5 metadata 会重复消费 blocker。
4. 本 sprint 选择 Objective 2 / Objective 3：最新 `13-14` final 已完成 `route_task_field_retest_review_result_handoff -> result_intake -> result_reconciliation` safe lineage bridge；PR #4 要求 route/elevator evidence chain 成为必达主线；当前最可执行的下一步是把 result reconciliation 转成现场/支持/手机可执行的 acceptance packet。
5. 不选择 PR #5 真实硬件 blocker：Codex review 指出的 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry 缺口需要真实硬件材料，本机 Docker-only 无法完成；本轮只保留该风险，不继续消费为本地 metadata。

## 2. Task A - Autonomy 文件范围和验收命令

Owner：Autonomy Algorithm Engineer。

允许改动：

- `pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py`
- `pc-tools/evidence/test_route_task_field_retest_result_acceptance_packet.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md` 中 Task A 段落

要求：

- 新增 PC gate，输入 latest `route_task_field_retest_result_reconciliation` artifact / summary。
- 输出 acceptance packet artifact / summary，包含 safe lineage、八类 required result materials、missing items、mismatch reasons、owner handoff、rerun commands、pass/fail criteria、safe copy。
- 八类 required result materials 必须至少覆盖：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance operator note、dropoff/cancel completion、delivery result。
- 缺 source、unsupported schema、evidence_ref mismatch、unsafe copy、success/control claim 必须 fail closed。
- 不读取 raw handoff artifact，不接触真实 Nav2、serial/UART、WAVE ROVER、云、4G、OSS/CDN、DB/queue 或真实手机/browser。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_acceptance_packet.py
python3 pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py --help
rg -n "route_task_field_retest_result_acceptance_packet|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_acceptance_packet_gate|not_proven|delivery_success=false|primary_actions_enabled=false|pass/fail criteria|rerun commands" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet
git diff --check -- pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py pc-tools/evidence/test_route_task_field_retest_result_acceptance_packet.py pc-tools/README.md docs/navigation/fixed_route_workflow.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md
```

## 3. Task B - Robot 文件范围和验收命令

Owner：Robot Platform Engineer。

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md` 中 Task B 段落

要求：

- 新增或扩展 diagnostics summary function，只读消费 `route_task_field_retest_result_acceptance_packet` artifact / summary。
- 支持 file/env/top-level/nested diagnostics summary 输入，输出 Robot-safe summary。
- 只暴露 packet status、safe `evidence_ref`、missing material summary、owner handoff、rerun command summary、pass/fail criteria summary、safe copy、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺字段、unsupported schema、unsafe copy、success/control claim、raw path/checksum/credential/ROS topic/serial detail 必须 fail closed。
- 不改变 task_orchestrator、action result、Start/Dropoff/Cancel 控制语义。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_result_acceptance_packet|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_acceptance_packet_gate|not_proven|delivery_success=false|primary_actions_enabled=false|pass/fail criteria|rerun commands" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.17_14-15_route-task-result-acceptance-packet
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md
```

## 4. Task C - Full-stack 文件范围和验收命令

Owner：User Touchpoint Full-Stack Engineer。

允许改动：

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md` 中 Task C 段落

要求：

- 新增只读 “路线任务结果验收包” panel，消费 `route_task_field_retest_result_acceptance_packet` / summary / Robot diagnostics compatible summary。
- panel 只展示 packet status、safe lineage、八类 result materials summary、missing items、owner handoff、rerun commands、pass/fail criteria、safe copy、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- copy/export 只包含白名单 safe metadata；缺 safe_copy 时显示 blocked copy unavailable。
- Start Delivery / Confirm Dropoff / Cancel gating 不变，不发送 robot command，不抓取 raw artifact。
- 文案必须避免“现场已通过”“送达成功”“真实手机已验收”等成功暗示。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "route_task_field_retest_result_acceptance_packet|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_acceptance_packet_gate|not_proven|delivery_success=false|primary_actions_enabled=false|pass/fail criteria|rerun commands" mobile/web docs/product sprints/2026.05.17_14-15_route-task-result-acceptance-packet
git diff --check -- mobile/web/app.js mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md
```

## 5. Task D - Product closeout 文件范围和验收命令

Owner：Product Manager / OKR Owner。

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/side2side_check.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/final.md`

要求：

- 等 Task A/B/C 返回后收口，不提前替工程宣称完成。
- 明确本轮是 `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`，不是真实 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof 或 delivery success。
- 若 packet gate、Robot diagnostics 和 mobile/web 都通过围栏验证，Objective 2 / 3 可保守小幅更新；Objective 5 不更新。
- `final.md` 必须回顾 OKR 最低优先级核对，说明 Objective 5 stop rule 和 PR #5 hardware blocker 为什么仍成立。

验收命令：

```bash
rg -n "route_task_field_retest_result_acceptance_packet|route_task_field_retest_result_reconciliation|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|software_proof_docker_route_task_field_retest_result_acceptance_packet_gate" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_14-15_route-task-result-acceptance-packet
```

## 6. 接口和证据边界

- 不新增真实硬件/云/手机 proof。
- 不访问外部公网、OSS/CDN、production DB/queue、4G/SIM、serial/UART、WAVE ROVER 或真实手机/browser。
- 不新增 ROS topic/service/action，不改变 task action result，不改变 remote ACK/cursor，不改变 Start / Confirm Dropoff / Cancel gating。
- 不新增大测试，只用围栏验证。
- 所有输出必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot diagnostics 和 mobile/web 只读消费 summary / safe copy，不读取 raw artifact，不暴露 raw paths、checksums、credentials、ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER 参数或 Objective 5 external proof material。
