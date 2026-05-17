# Sprint 2026.05.17_16-17 Route Task Result Backfill Review Decision - Tech Plan

sprint_type: epic

## 1. 技术目标

实现 `route_task_field_retest_result_backfill_review_decision`，接在 `route_task_field_retest_result_acceptance_backfill` 之后，把 backfill artifact / summary 转成 review decision、accepted / missing / rejected material status、owner handoff、next required evidence 和 rerun commands，并让 Robot diagnostics 与 `mobile/web` 只读展示。

本轮 evidence boundary 固定为 `software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`。输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1（2026-05-17 15:18）显示 Objective 5：云中转 + OSS/CDN 数据通路产品化约 68%，仍是数值最低 Objective。

本 sprint 不针对 Objective 5。原因：

- 本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser 证据。
- Objective 5 当前要提升 completion 必须拿到至少一种真实 external proof；继续做 Docker-only metadata wrapper 会重复消费同一 blocker。
- `OKR.md` 当前最高优先级已明确：若 O5 external materials 不可用，不要把本地 `cloud_worker_*`、route/elevator summaries、browser proof、handoff artifact 或 diagnostics/mobile summary 写成 production proof。

本 sprint 选择 Objective 2 / Objective 3。原因：

- 最新 sprint `2026.05.17_15-16_route-task-result-acceptance-backfill` 已完成 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`，O2/O3 到约 96%，但仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion 和 delivery_result。
- PR #4 将 elevator-assisted delivery 设为主线必须能力；route/elevator 材料链需要从 backfill 入口推进到 review decision，让下一次现场材料补录、退回或分派有明确决策层。
- PR #5 review 暴露 production hardware boundary 与 mandatory sensor baseline 矛盾、OKR lowest narrative drift、mandatory sensor assumptions 缺本地 vendor/source citation；但本轮没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 材料，继续包装 PR #5 blocker 不会推进真实硬件证据。

## 3. 证据边界

本轮证明：

- Docker/local PC gate 可以把上一轮 route-task result backfill summary 转成 review decision。
- Robot diagnostics 可以只读展示 safe review decision summary，并 fail closed。
- `mobile/web` 可以只读展示 phone-safe review decision、material status、owner handoff、next required evidence 和 rerun commands。

本轮不证明：

- 不证明真实 route/elevator field pass。
- 不证明真实 Nav2/fixed-route、真实 route completion signal、真实 task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result 或 delivery success。
- 不证明 HIL、WAVE ROVER、真实串口/UART、真实 2D LiDAR / ToF、真实手机/browser 或 production app。
- 不证明 Objective 5 external proof，包括真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。

## 4. 并行 worker 任务

本轮必须并行启动 4 个 worker。文件范围互不重叠，主节点只做验收和汇总。

### Task A - Autonomy: PC Review Decision Gate

Owner：`autonomy-engineer`

允许改动文件范围：

- `pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py`
- `pc-tools/evidence/test_route_task_field_retest_result_backfill_review_decision.py`
- `docs/interfaces/evidence_contracts.md`

接口影响：

- 新增 artifact schema：`trashbot.route_task_field_retest_result_backfill_review_decision.v1`
- 新增 summary schema：`trashbot.route_task_field_retest_result_backfill_review_decision_summary.v1`
- 输入只允许上一轮 `trashbot.route_task_field_retest_result_acceptance_backfill.v1` artifact 或 compatible summary。
- 输出必须包含 `review_decision`、`material_status`、`accepted_materials`、`missing_materials`、`rejected_materials`、`owner_handoff`、`next_required_evidence`、`rerun_commands`、`safe_copy`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 `evidence_boundary=software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_backfill_review_decision.py
python3 pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py --help
rg -n "route_task_field_retest_result_backfill_review_decision|software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate|accepted_materials|missing_materials|rejected_materials|owner_handoff|next_required_evidence|rerun_commands|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py pc-tools/evidence/test_route_task_field_retest_result_backfill_review_decision.py docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py pc-tools/evidence/test_route_task_field_retest_result_backfill_review_decision.py docs/interfaces/evidence_contracts.md
```

### Task B - Robot: Diagnostics Read-only Consumer

Owner：`robot-software-engineer`

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

接口影响：

- diagnostics 新增只读字段 `route_task_field_retest_result_backfill_review_decision` / `_summary`。
- 支持 file/env/top-level/nested summary 来源。
- unsupported schema/boundary、unsafe copy、success claim、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 不改变 task_orchestrator、action server、Start Delivery、Confirm Dropoff、Cancel 控制语义。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_result_backfill_review_decision|software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate|accepted_materials|missing_materials|rejected_materials|owner_handoff|next_required_evidence|rerun_commands|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - Full-stack: Mobile/web Read-only Panel

Owner：`full-stack-software-engineer`

允许改动文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

接口影响：

- `mobile/web` 新增只读“路线任务回填复核决策” panel。
- 消费 `route_task_field_retest_result_backfill_review_decision` / `_summary` 或 compatible phone-safe summary。
- 展示 review decision、material status、accepted/missing/rejected categories、owner handoff、next required evidence、rerun command summary、safe evidence ref、not proven、boundary flags。
- copy/export 只允许白名单字段；缺 `safe_copy` 时显示 `blocked copy unavailable`。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating，不发送 ACK/cursor/diagnostics fetch/robot command。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "route_task_field_retest_result_backfill_review_decision|software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate|accepted_materials|missing_materials|rejected_materials|owner_handoff|next_required_evidence|rerun_commands|not_proven|delivery_success=false|primary_actions_enabled=false|blocked copy unavailable" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product: Closeout and OKR Boundary

Owner：`product-okr-owner`

允许改动文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/tech-done.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/side2side_check.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/final.md`

接口影响：

- 不改代码接口。
- 根据 Task A/B/C 的实际结果更新 sprint closeout、OKR evidence boundary 和 progress log。
- 若 Task A/B/C 未全部落地或验证失败，不得把 planning 或部分实现写成 OKR 进展。
- 必须明确 Objective 5 仍最低但因缺真实 external proof 不推进；本轮若更新 O2/O3，只能写成 Docker-only software proof。

验收命令：

```bash
rg -n "route_task_field_retest_result_backfill_review_decision|software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_16-17_route-task-result-backfill-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_16-17_route-task-result-backfill-review-decision
```

## 5. 集成顺序

1. 并行启动 Task A / B / C / D。Task D 先准备 closeout skeleton 和验收清单，不提前写完成。
2. Task A 返回后，Robot / Full-stack 按 summary schema 核对字段名；若字段不一致，由 Task A 保持 schema 稳定并给出兼容 summary。
3. Task B / C 返回后，Product 只核对只读边界、copy whitelist、not proven flags、validation logs 和 docs sync。
4. 全部通过后，Product 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 失败处理

- 若 PC gate 无法生成 review decision，退回 Task A，不允许 Robot/mobile 自行拼 fake summary。
- 若 diagnostics 或 mobile 暴露 raw artifact、local path、checksum、traceback、ROS topic、serial/UART、credentials 或成功/控制文案，退回对应 owner。
- 若任何输出出现 `delivery_success=true`、`primary_actions_enabled=true` 或真实 route/elevator/HIL/O5 proof 暗示，必须 fail closed 并修复。
- 若 validation 命令失败，对应 worker 先定位根因、修复并复验；不能把第一轮失败作为最终结果。

## 7. 后续收口文档

实现完成后必须创建或更新：

- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/tech-done.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/side2side_check.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/final.md`

涉及产品用户流程与接口说明的实现必须同步更新 `docs/product/mobile_user_flow.md`、`docs/interfaces/evidence_contracts.md` 或 `docs/interfaces/ros_contracts.md` 中对应内容。
