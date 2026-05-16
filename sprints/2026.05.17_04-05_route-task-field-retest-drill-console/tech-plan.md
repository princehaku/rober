# Sprint 2026.05.17_04-05 Route Task Field Retest Drill Console - Tech Plan

sprint_type: epic

## 1. 总体方案

实现 `route_task_field_retest_drill_console`，作为 `route_task_field_retest_operator_drill` 后的 PC/Robot/mobile software-proof 演练控制台层。该层不读取真实材料目录，不访问真实机器人或外部云，只把 operator drill 的下一步 checklist、safe copy、缺失材料和回调动作汇总成同一份 console artifact / summary。

统一 evidence boundary：

- `software_proof_docker_route_task_field_retest_drill_console_gate`
- `trashbot.route_task_field_retest_drill_console.v1`
- `trashbot.route_task_field_retest_drill_console_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮文件范围由 3 个并行 owner 拆分，互不重叠。Product closeout 后续由主会话处理。

## 2. Task A - Autonomy

Owner：`autonomy-engineer`

允许改动：

- `pc-tools/evidence/route_task_field_retest_drill_console.py`
- `pc-tools/evidence/test_route_task_field_retest_drill_console.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 dependency-free PC CLI，建议参数为 `--operator-drill-json`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`。
- 兼容 `route_task_field_retest_operator_drill` artifact、summary、wrapper / nested JSON。
- 输出 `trashbot.route_task_field_retest_drill_console.v1` 与 `trashbot.route_task_field_retest_drill_console_summary.v1`。
- Summary 必须包含 console status、safe `evidence_ref`、material pack / result intake / result reconciliation command labels、safe checklist、missing material prompts、operator callback checklist、rerun notes、not-proven 列表和 evidence boundary。
- 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
- 对 missing input、坏 JSON、unsupported schema/boundary、证据号不一致、弱类型 `same_evidence_ref_required`、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER、success wording、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 新增代码技术注释使用中文，注释解释为什么 fail closed、为什么只消费 summary、为什么不读取真实材料目录。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_drill_console.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_drill_console.py
python3 pc-tools/evidence/route_task_field_retest_drill_console.py --help
rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|trashbot.route_task_field_retest_drill_console.v1|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_drill_console.py pc-tools/evidence/test_route_task_field_retest_drill_console.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_retest_drill_console.py pc-tools/evidence/test_route_task_field_retest_drill_console.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

## 3. Task B - Robot

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 新增 `route_task_field_retest_drill_console` / `_summary` diagnostics metadata-only consumer。
- 支持 console artifact、summary、Robot-compatible summary 和 nested diagnostics summary。
- 只暴露 safe summary、safe `evidence_ref`、console status、command labels、safe checklist、missing material prompts、operator callback checklist、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 对 missing、unsupported schema/boundary、unsafe copy、success phrasing、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 不改变 collect、dropoff、cancel、ACK、Nav2、HIL、cursor、diagnostics fetch 或 delivery success 语义。
- 新增代码技术注释使用中文，解释 metadata-only 和动作隔离边界。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|metadata-only|fail closed|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 4. Task C - Full-stack

Owner：`full-stack-software-engineer`

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- 新增只读“现场复测演练控制台” panel，消费 `route_task_field_retest_drill_console` artifact / summary / Robot diagnostics compatible summary。
- 展示 console status、safe `evidence_ref`、safe checklist/copy、command labels、missing material prompts、operator callback checklist、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 不变；不得新增 Start / Confirm / Cancel / ACK / cursor / robot command 请求。
- Copy/export 采用 whitelist-only，只允许导出 safe summary fields。
- 不展示 raw artifact、raw JSON、raw path、credential、ROS topic、serial/UART、WAVE ROVER、DB/queue URL、OSS AK/SK、checksums、complete artifact 或 raw robot response。
- 新增代码技术注释使用中文，解释为什么只读、为什么 copy/export 白名单、为什么主操作 gating 不变。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|现场复测演练控制台|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

## 5. Task D - Product Closeout

Owner：`product-okr-owner`

后续允许改动：

- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/tech-done.md`
- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/side2side_check.md`
- `sprints/2026.05.17_04-05_route-task-field-retest-drill-console/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 汇总 A/B/C worker 的实际改动、验证结果、失败定位和剩余风险。
- 保守更新 OKR：Objective 5 不提升；Objective 2 / Objective 3 / Objective 4 是否提升必须基于实际 worker 交付和证据边界。
- 明确本轮由 `route_task_field_retest_operator_drill` 继续推进，不是 Objective 5 external proof，也不是 O1 HIL-entry 或硬件材料真实完成。
- 明确本轮不是真实 route/elevator field pass、HIL、真实手机/browser、production app、真实投放、dropoff/cancel completion 或 delivery success。

验收命令：

```bash
rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #5" sprints/2026.05.17_04-05_route-task-field-retest-drill-console OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_04-05_route-task-field-retest-drill-console/tech-done.md sprints/2026.05.17_04-05_route-task-field-retest-drill-console/side2side_check.md sprints/2026.05.17_04-05_route-task-field-retest-drill-console/final.md OKR.md docs/process/okr_progress_log.md
```

## 6. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 66%。
- 本 sprint 是否针对该 Objective：否。
- 不针对理由：本机是 Docker-only，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。继续本地 O5 metadata depth 不能形成真实 Objective 5 external proof。
- 为什么不转向 Objective 1 硬件材料：最新 `hardware_sensor_hil_entry_execution_pack` 已把硬件链推进到真实材料准备，下一步需要真实 2D LiDAR / ToF / WAVE ROVER / UART / HIL-entry 证据；继续本地包装会重复消费硬件 blocker。
- 本 sprint 目标 Objective：Objective 2 / Objective 3 为主，Objective 4 只读消费为辅。
- final.md 收口时需复核：O5 外部材料是否仍不可用；O1 真实硬件材料是否仍不可用；本轮是否仍保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 7. 本 planning 阶段验收命令

```bash
rg -n "sprint_type: epic|route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|OKR 最低优先级核对|Objective 5|Objective 2|Objective 3|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.17_04-05_route-task-field-retest-drill-console
git diff --check -- sprints/2026.05.17_04-05_route-task-field-retest-drill-console/pre_start.md sprints/2026.05.17_04-05_route-task-field-retest-drill-console/prd.md sprints/2026.05.17_04-05_route-task-field-retest-drill-console/tech-plan.md
```
