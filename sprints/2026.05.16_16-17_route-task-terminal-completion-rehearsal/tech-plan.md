# Sprint 2026.05.16_16-17 Route Task Terminal Completion Rehearsal - Tech Plan

sprint_type: epic

## 1. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 理由：Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。本机只有 Docker，继续新增 O5 local metadata 不能构成外部 proof。
4. Objective 1 约 73%，但本机没有真实 WAVE ROVER、UART、Orange Pi 串口、`T=1001` feedback 或 HIL，因此本轮不继续消费硬件 blocker。
5. 本 sprint 改攻 Objective 2 / Objective 3 的可行动作：route/task 终态复账。它能在 Docker-only 条件下推进同一 `evidence_ref` 的 task record、completion signal、dropoff/cancel material status、failure/recovery reason 和手机只读摘要，为下一次真实 field session 提供可执行入口。

## 2. 证据依据

- `OKR.md` 4.1：Objective 5 约 66% 最低，但缺真实外部云/4G/OSS/CDN/DB/queue 材料；Objective 2/3 约 78%，仍缺真实 Nav2/fixed-route、真实 route/elevator field pass、同一 `evidence_ref` 的 task record/completion signal、真实 dropoff/cancel completion 和 delivery result。
- PR #5：`Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 把电梯 assisted delivery 写成主链路，推动 O2/O3 继续围绕 route/elevator evidence contract 落地。
- PR #5 review P1：硬件默认集与 mandatory sensor baseline 曾矛盾，说明后续 sprint 必须避免把缺真实硬件材料的本地包装误写成硬件完成。
- PR #5 review P2：OKR lowest narrative 曾误导 sprint routing；本 plan 显式记录 O5 最低但外部阻塞，并说明为什么本轮转向 O2/O3。
- PR #5 review P2：mandatory sensor assumptions 必须引用 `docs/vendor/`；最近硬件链已按 vendor 资料处理到 receipt intake，但真实材料仍缺。
- `sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake/final.md`：真实 2D LiDAR / ToF SKU/source/receipt、采购、安装、接线、电源、标定和 HIL-entry 仍缺；继续堆本地同类包装收益低。
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/final.md`：下一步应补同一 `evidence_ref` 的 Nav2/fixed-route runtime log、task record、route completion signal、门状态、楼层确认、人工协助、dropoff/cancel completion 和 delivery result。
- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/final.md`：route/elevator field retest request 已形成，但真实 dropoff/cancel completion 和 delivery success 仍缺；本轮把终态复账 contract 往前推进。

## 3. 统一接口

- Artifact schema：`trashbot.route_task_terminal_completion_rehearsal.v1`
- Summary schema：`trashbot.route_task_terminal_completion_rehearsal_summary.v1`
- Evidence boundary：`software_proof_docker_route_task_terminal_completion_rehearsal_gate`
- 缺失默认状态：`blocked_missing_route_task_terminal_completion_rehearsal`
- 固定边界：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

## 4. 并行 owner 任务

### Task A：Robot Terminal Completion Summary

责任 Engineer：Robot Platform Engineer。

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_record.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 在 task record 中增加 terminal completion rehearsal summary，覆盖 final_status、final_state、dropoff_result、cancel/failure/recovery reason、same `evidence_ref`、route_progress presence、`delivery_success=false` 和 `primary_actions_enabled=false`。
- `task_orchestrator` 写 record 时填充该 summary；cancel、dropoff timeout、dry-run dropoff 都必须保守表达。
- `operator_gateway_diagnostics` metadata-only 消费 `route_task_terminal_completion_rehearsal` 或 summary，缺失/unsupported/unsafe/evidence_ref mismatch 均 fail closed。
- 不触发 collect/dropoff/cancel、ACK、cursor advance、Nav2、WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。
- 新增代码技术注释必须使用中文，且解释为什么保持 software proof 边界。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_task_record.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_terminal_completion_rehearsal|software_proof_docker_route_task_terminal_completion_rehearsal_gate|blocked_missing_route_task_terminal_completion_rehearsal|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_task_record.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task B：Autonomy PC Evidence Gate

责任 Engineer：Autonomy Algorithm Engineer。

允许改动：

- `pc-tools/evidence/route_task_terminal_completion_rehearsal.py`
- `pc-tools/evidence/test_route_task_terminal_completion_rehearsal.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 dependency-free CLI，读取 route status、task record、existing `route_task_completion_signal` artifact/summary，可选 dropoff/cancel material summary。
- 输出 artifact / summary，schema 与 boundary 使用本 plan 第 3 节。
- Fail closed：缺 required source、bad JSON、unsupported schema/boundary、same `evidence_ref` mismatch、unsafe copy、`delivery_success=true`、`primary_actions_enabled=true`、raw path/credential/ROS topic/serial/WAVE ROVER/HIL/success wording。
- 摘要必须给 Robot/mobile 足够字段：terminal verdict、safe `evidence_ref`、dropoff/cancel material status、failure/recovery reason、operator next steps、not_proven。
- 新增代码技术注释必须使用中文，解释字段白名单和 fail-closed 原因。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_terminal_completion_rehearsal.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_terminal_completion_rehearsal.py
python3 pc-tools/evidence/route_task_terminal_completion_rehearsal.py --help
rg -n "route_task_terminal_completion_rehearsal|software_proof_docker_route_task_terminal_completion_rehearsal_gate|not_proven|delivery_success=false|primary_actions_enabled=false|dropoff|cancel" pc-tools docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_terminal_completion_rehearsal.py pc-tools/evidence/test_route_task_terminal_completion_rehearsal.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task C：Full-Stack Mobile Read-Only Panel

责任 Engineer：User Touchpoint Full-Stack Engineer。

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- 在 route/elevator 和 completion signal panels 附近新增只读“任务终态复账” panel。
- 消费 `route_task_terminal_completion_rehearsal`、`route_task_terminal_completion_rehearsal_summary`、`phone_readiness`、`/api/diagnostics`、nested diagnostics summary 中兼容字段。
- 展示 terminal verdict、safe `evidence_ref`、dropoff/cancel material status、failure/recovery reason、operator next steps、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- copy/export whitelist-only，不展示 raw JSON、ROS topic、串口、凭证、完整本机路径、checksum、完整 artifact、HIL 或成功送达文案。
- Start / Confirm Dropoff / Cancel gating 不变。
- 新增代码技术注释必须使用中文，解释为何该 panel 只读且不授权控制。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "route_task_terminal_completion_rehearsal|任务终态复账|software_proof_docker_route_task_terminal_completion_rehearsal_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

### Task D：Product Closeout

责任 Engineer：Product Manager / OKR Owner。

允许改动：

- `sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal/tech-done.md`
- `sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal/side2side_check.md`
- `sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 Robot / Autonomy / Full-stack worker 的实际改动、验证命令、失败定位和剩余风险。
- 回顾本轮是否仍符合 OKR 最低优先级核对：O5 仍最低但外部阻塞；O1 无硬件；本轮只提升 O2/O3/O4 的软件准备度。
- `OKR.md` 只允许按 software proof 保守更新；没有真实材料时，不提升 O1/O5，不声明真实 completion、HIL 或 delivery success。
- closeout 必须明确本轮不证明真实 Nav2/fixed-route、真实 route/elevator field pass、真实 dropoff/cancel completion、delivery success、真实手机/browser、WAVE ROVER/UART/HIL 或 O5 external proof。

验收命令：

```bash
rg -n "route_task_terminal_completion_rehearsal|software_proof_docker_route_task_terminal_completion_rehearsal_gate|Objective 5|Objective 2|Objective 3|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal OKR.md docs/process/okr_progress_log.md
```

## 5. 接口影响

- 新增 Robot/task record 终态复账摘要字段；不改变 ROS action/topic/service 运行时契约。
- 新增 PC evidence artifact / summary schema；只读、dependency-free、Docker/local。
- Robot diagnostics 新增 metadata-only consumer；不触发控制链路。
- Mobile/web 新增只读 panel；主操作按钮授权条件不变。

## 6. 风险边界

- 本轮不是真实 dropoff/cancel completion 或 delivery success。
- 本轮不是真实 route/elevator field pass、Nav2/fixed-route runtime proof、真实路线采集、真实电梯、真实手机/browser、production app、WAVE ROVER/UART/HIL 或 Objective 5 external proof。
- 若 worker 发现已有 `route_task_completion_signal` 已覆盖部分字段，仍应把本轮增量控制在 terminal rehearsal summary / UI / diagnostics contract，不做无关重构。

## 7. Sprint 文档要求

- Planning 阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后补齐：`tech-done.md`、`side2side_check.md`、`final.md`。
- 不允许一次性预生成 closeout 文档；closeout 必须基于 worker 实际验证结果。
