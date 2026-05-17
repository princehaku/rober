# Sprint 2026.05.18_03-04 Route Task Result Review Handoff - Tech Plan

sprint_type: epic

## 1. 技术目标

新增 `route_task_field_retest_result_review_handoff`，承接 `route_task_field_retest_result_review_decision`。本轮要把 decision status、accepted/blocked/rerun reasons、owner handoff、safe `evidence_ref`、missing materials 和 rerun package 转成 owner 可执行 handoff package，供 PC、Robot diagnostics 和 mobile/web 后续只读消费。

证据边界固定为 `software_proof_docker_route_task_field_retest_result_review_handoff_gate`。所有实现、文案、测试和 closeout 必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 最低 Objective 是 Objective 5，约 68%。本 sprint 不针对 Objective 5，因为继续提升 O5 必须有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover 或真实手机/browser external proof；本机 Docker-only，当前没有这些外部材料。

下一低项是 Objective 1，约 81%。本 sprint 也不针对 Objective 1，因为最近三轮已经消费同一真实 WAVE ROVER/HIL packet blocker：`2026.05.17_21-22_wave-rover-hil-packet-intake`、`2026.05.17_22-23_wave-rover-hil-packet-review-decision`、`2026.05.17_23-24_wave-rover-hil-packet-execution-pack`。没有真实 WAVE ROVER、UART、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report 时，不再继续本地包装。

本轮选择 Objective 2 / Objective 3 的原因：PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR` 已合并，且 Testing 明确 no runtime integration tests；最新 sprint 已完成 `route_task_field_retest_result_review_decision`，下一步最可执行的软件工作是 result review handoff，明确真实 route/elevator field pass、Nav2/fixed-route、task record/completion signal、dropoff/cancel completion 和 delivery result 的补齐路径。

PR #5 review 继续作为边界输入：P1 default hardware set 与 mandatory `monocular + 2D LiDAR + ToF` baseline 矛盾；P2 mandatory sensor assumptions 缺 `docs/vendor/` source；P2 lowest-objective narrative 曾误导 routing。说明硬件材料仍需真实 source、receipt、install、calibration 和 HIL-entry，不能用本轮 route/elevator handoff 替代硬件履约。

## 3. 接口和数据契约

### 3.1 上游输入

- artifact schema：`trashbot.route_task_field_retest_result_review_decision.v1`
- summary schema：`trashbot.route_task_field_retest_result_review_decision_summary.v1`
- compatible diagnostics summary：Robot diagnostics 中的 result review decision summary
- 必需字段：safe `evidence_ref`、decision status、accepted reasons、blocked reasons、rerun reasons、owner handoff、next required evidence、rerun commands、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

### 3.2 下游输出

- artifact schema：`trashbot.route_task_field_retest_result_review_handoff.v1`
- summary schema：`trashbot.route_task_field_retest_result_review_handoff_summary.v1`
- evidence boundary：`software_proof_docker_route_task_field_retest_result_review_handoff_gate`
- handoff states：
  - `ready_for_owner_result_callback_not_proven`
  - `needs_result_material_callback_not_proven`
  - `evidence_ref_mismatch_rerun_not_proven`
  - `blocked_missing_result_review_decision_not_proven`
  - `unsupported_result_review_decision_schema_not_proven`

### 3.3 Package 字段

- `handoff_status`
- `owner_work_orders`
- `accepted_reasons`
- `blocked_reasons`
- `rerun_reasons`
- `same_evidence_ref_package`
- `next_material_callback_requirements`
- `rerun_commands`
- `next_required_evidence`
- `evidence_boundary`

### 3.4 Fail-closed 规则

以下情况必须 fail closed：

- 缺 review decision artifact / summary。
- unsupported schema 或 unsupported evidence boundary。
- unsafe / mismatch `evidence_ref`。
- 缺真实 route/elevator result materials：门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff completion、cancel completion、delivery result。
- 出现 success copy、`delivery_success=true`、`primary_actions_enabled=true`、`hil_pass`、field pass、production ready、真实手机通过、raw credential、raw path、raw ROS topic、`/cmd_vel`、serial/UART 参数、OSS/DB/queue/token 或 robot command payload。

## 4. Owner 拆分

### Task A - Autonomy Algorithm Engineer

文件范围：

- `pc-tools/evidence/route_task_field_retest_result_review_handoff.py`
- `pc-tools/evidence/test_route_task_field_retest_result_review_handoff.py`
- `docs/interfaces/evidence_contracts.md`

任务：

- 实现 dependency-free PC gate，读取上一轮 decision artifact / summary。
- 输出 `route_task_field_retest_result_review_handoff` artifact / summary。
- 将 accepted / blocked / rerun 结论转成 handoff status、owner work orders、same-evidence-ref package、next material callback requirements 和 rerun commands。
- 保持 `software_proof_docker_route_task_field_retest_result_review_handoff_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_review_handoff.py
python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_review_handoff.py
rg -n "route_task_field_retest_result_review_handoff|software_proof_docker_route_task_field_retest_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_result_review_handoff.py pc-tools/evidence/test_route_task_field_retest_result_review_handoff.py docs/interfaces/evidence_contracts.md
```

### Task B - Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

任务：

- 接入 result review handoff summary 的 metadata-only diagnostics consumer。
- 支持 env / diagnostics summary / nested summary 的安全读取。
- 不新增控制路径，不触发 ACK、cursor、Start Delivery、Confirm Dropoff、Cancel 或 robot command。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_result_review_handoff|software_proof_docker_route_task_field_retest_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

任务：

- 新增 mobile/web 只读 “路线/电梯结果复核交接” panel。
- 展示 handoff status、safe `evidence_ref`、owner work orders、accepted/blocked/rerun reasons、next material callback requirements、rerun commands、evidence boundary、`not_proven`。
- 保持 Start Delivery、Confirm Dropoff、Cancel gating 不变；不新增 fetch diagnostics、ACK、cursor、result routes 或 robot command。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_result_review_handoff|software_proof_docker_route_task_field_retest_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product Manager / OKR Owner

文件范围：

- `sprints/2026.05.18_03-04_route-task-result-review-handoff/tech-done.md`
- `sprints/2026.05.18_03-04_route-task-result-review-handoff/side2side_check.md`
- `sprints/2026.05.18_03-04_route-task-result-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

任务：

- 汇总 A/B/C 验证结果和 evidence boundary。
- 更新 sprint closeout、OKR 进度和 progress log。
- 明确本轮仍不证明 Objective 5 external proof、Objective 1 HIL、真实 route/elevator field pass、真实手机/browser 或 delivery success。

验收命令：

```bash
rg -n "route_task_field_retest_result_review_handoff|software_proof_docker_route_task_field_retest_result_review_handoff_gate|Objective 5|Objective 1|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_03-04_route-task-result-review-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_03-04_route-task-result-review-handoff/tech-done.md sprints/2026.05.18_03-04_route-task-result-review-handoff/side2side_check.md sprints/2026.05.18_03-04_route-task-result-review-handoff/final.md
```

## 5. 并行启动计划

本 sprint 是 epic，且 Task A / B / C 文件范围互不重叠，后续实现阶段必须并行启动 3 个 worker：

- `autonomy-engineer` 负责 PC evidence handoff gate。
- `robot-software-engineer` 负责 Robot diagnostics。
- `full-stack-software-engineer` 负责 mobile/web。

Product closeout 在 A/B/C 返回后执行，不得提前把 planning 文档当业务结果。

## 6. 文档同步

实现完成后必须同步更新：

- `docs/interfaces/evidence_contracts.md`
- `docs/interfaces/ros_contracts.md`
- `docs/product/mobile_user_flow.md`
- `docs/process/okr_progress_log.md`
- 当前 sprint `tech-done.md`、`side2side_check.md`、`final.md`
- `OKR.md`

## 7. 风险和非目标

- 非目标：真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 dropoff/cancel completion、真实 delivery success、真实手机/browser、HIL、Objective 5 external proof。
- 非目标：修复 PR #5 2D LiDAR / ToF source/receipt/install/calibration/HIL-entry 材料缺口；本轮只在边界中保留该 blocker。
- 风险：若 mobile 或 diagnostics copy 出现 success wording，会误导用户把 handoff summary 当真实现场通过，必须通过 rg/test fail closed。
- 风险：若 evidence_ref 不安全或 mismatch 仍进入 ready state，会破坏后续 callback/backfill 链路，必须作为 P0 failure。

## 8. 本轮 planning 验收命令

```bash
test -f sprints/2026.05.18_03-04_route-task-result-review-handoff/pre_start.md && test -f sprints/2026.05.18_03-04_route-task-result-review-handoff/prd.md && test -f sprints/2026.05.18_03-04_route-task-result-review-handoff/tech-plan.md
rg -n "sprint_type: epic|route_task_field_retest_result_review_handoff|OKR 最低优先级核对|Objective 5|Objective 1|PR #4|PR #5|software_proof_docker_route_task_field_retest_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_03-04_route-task-result-review-handoff
git diff --check -- sprints/2026.05.18_03-04_route-task-result-review-handoff/pre_start.md sprints/2026.05.18_03-04_route-task-result-review-handoff/prd.md sprints/2026.05.18_03-04_route-task-result-review-handoff/tech-plan.md
```
