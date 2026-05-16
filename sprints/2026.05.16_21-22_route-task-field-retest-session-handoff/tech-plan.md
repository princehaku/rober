# Sprint 2026.05.16_21-22 Route Task Field Retest Session Handoff - Tech Plan

sprint_type: epic

## 1. 技术目标

本轮实现 `route_task_field_retest_session_handoff` 规划：把上一轮 `route_task_field_retest_execution_pack` 转成现场 session handoff artifact/summary、Robot diagnostics metadata-only consumer、mobile/web 只读 panel 和 Product closeout 链路。

统一证据边界：

- `software_proof_docker_route_task_field_retest_session_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮只做 Docker/local software proof，不宣称真实 field pass、真实 fixed-route/Nav2、真实电梯、真实 WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、delivery result 或 Objective 5 external proof。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对 Objective 5 的理由是：`OKR.md` 第 6 节明确只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等真实外部材料才能继续推进 Objective 5 completion；当前开发主机只有 Docker，本轮无法产出这些外部材料。继续新增本地 O5 metadata wrapper 不能提高 Objective 5。
4. 本轮转向 Objective 2 / Objective 3 的具体证据：
   - `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/final.md` 已完成 `software_proof_docker_route_task_field_retest_execution_pack_gate`，但仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、真实手机/browser 和 Objective 5 external proof。
   - `sprints/2026.05.16_19-20_route-task-terminal-review-decision/final.md` 已完成 terminal review decision、owner handoff、next required evidence 和 field retest request guidance，下一步自然是 route-task field retest session handoff。
   - PR #4 已把 elevator-assisted delivery 写成主线必须能力，因此本轮 O2/O3 session handoff 必须覆盖电梯门状态、目标楼层确认和人工协助记录。
   - PR #5 review 指出硬件/source/config blocker；`2026.05.16_17-18_hardware-baseline-source-alignment` 与 `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 已连续两轮消费该 blocker。按 `AGENTS.md` 同一 blocker 最多消费 2 轮红线，本轮不能第三次继续硬件 blocker wrapper，必须切到不依赖真实硬件/source 决策的 O2/O3 field retest handoff。

## 2. Owner 拆分

本轮是 4 owner Epic sprint。文件范围互不重叠，实施阶段应并行派发 Task A / B / C，并由 Task D 在 worker 返回后收口。

### Task A Autonomy

责任人：Autonomy Algorithm Engineer。

目标：创建 PC-side session handoff gate，把上一轮 execution pack 转成现场复测交接 artifact / summary。

允许修改：

- `pc-tools/evidence/route_task_field_retest_session_handoff.py`
- `pc-tools/evidence/test_route_task_field_retest_session_handoff.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 输入支持上一轮 `route_task_field_retest_execution_pack` artifact / summary / nested JSON。
- 输出 schema 建议为 `trashbot.route_task_field_retest_session_handoff.v1` 与 `trashbot.route_task_field_retest_session_handoff_summary.v1`。
- 必须保留同一 `evidence_ref`，并列出下一次现场回填的真实材料：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result。
- 必须输出 operator handoff、session owner、material paths/placeholders、rerun commands、field callback/checklist 和 fail-closed summary。
- 必须拒绝 success phrasing、placeholder-only materials、证据号不一致或缺少 required materials 的 handoff。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_session_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_session_handoff.py
python3 pc-tools/evidence/route_task_field_retest_session_handoff.py --help
rg -n "route_task_field_retest_session_handoff|software_proof_docker_route_task_field_retest_session_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_retest_session_handoff.py pc-tools/evidence/test_route_task_field_retest_session_handoff.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B Robot

责任人：Robot Platform Engineer。

目标：让 Robot diagnostics metadata-only 消费 Task A summary，并保持 fail-closed。

允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 支持 `route_task_field_retest_session_handoff` / `_summary` 字段、环境变量或现有 diagnostics summary wrapper。
- 只输出 phone-safe metadata，不读取完整 raw artifact，不暴露 raw ROS topic、`/cmd_vel`、串口/UART、credentials、local paths、checksums 或 tracebacks。
- 缺失、schema 不匹配、弱类型 `same_evidence_ref_required`、成功措辞、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 保留 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 `software_proof_docker_route_task_field_retest_session_handoff_gate`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_session_handoff|software_proof_docker_route_task_field_retest_session_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C Full-stack

责任人：User Touchpoint Full-Stack Engineer。

目标：在 `mobile/web` 增加只读“路线任务现场复测交接” panel、fixture/test 和产品文档。

允许修改：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- panel 消费 `route_task_field_retest_session_handoff` / `_summary` 以及 Robot diagnostics 的 compatible summary。
- 只展示 safe `evidence_ref`、handoff status、session owner、required field materials、rerun commands summary、operator next steps、safe copy、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、evidence boundary。
- copy/export whitelist-only；若无 `safe_copy`，显示 blocked copy unavailable。
- 不改变 Start Delivery、Confirm Dropoff、Cancel authorization。
- 不暴露 raw artifacts、raw JSON、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、credentials、DB/queue URLs、OSS AK/SK、local paths、tracebacks、checksums 或完整 artifacts。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_session_handoff|software_proof_docker_route_task_field_retest_session_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

### Task D Product closeout

责任人：Product Manager / OKR Owner。

目标：在 Task A/B/C 返回后完成 sprint 留档、OKR 保守同步和过程日志。

允许修改：

- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/tech-done.md`
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/side2side_check.md`
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 Task A/B/C 实际改动、验证日志片段、失败定位和剩余风险。
- `OKR.md` 只能基于真实 evidence 保守更新；没有真实 field materials 时不得写成 field pass。
- Objective 5 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 时保持不提升。
- 明确本轮仍是 `software_proof_docker_route_task_field_retest_session_handoff_gate`，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `docs/process/okr_progress_log.md` 记录 PR #4、PR #5、Docker-only、O5 blocked 和 O2/O3 rerank 依据。

验收命令：

```bash
rg -n "route_task_field_retest_session_handoff|software_proof_docker_route_task_field_retest_session_handoff_gate|Objective 5|Objective 2|Objective 3|PR #5|PR #4|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_21-22_route-task-field-retest-session-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/tech-done.md sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/side2side_check.md sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/final.md
```

## 3. 接口影响

- 新增 PC evidence gate contract：`trashbot.route_task_field_retest_session_handoff.v1` / `trashbot.route_task_field_retest_session_handoff_summary.v1`。
- Robot diagnostics 只新增 metadata-only compatible summary 消费，不改变 task_orchestrator 状态机、不新增 motion/control route。
- mobile/web 只新增 read-only panel，不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 语义和 gating。
- Product closeout 只同步 sprint / OKR / process docs，不改变 runtime contract。

## 4. 并行派发要求

实施阶段必须在同一轮并行启动 Task A / Task B / Task C 三个 Engineer worker；Task D 等三方输出后收口。若运行时缺少子 agent 能力，`final.md` 必须解释降级原因；主节点不得直接写产品代码、测试代码、硬件配置或运行实现验证。

## 5. 全局验收命令

Planning 文档创建后先运行：

```bash
test -f sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/pre_start.md && test -f sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/prd.md && test -f sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/tech-plan.md
rg -n "route_task_field_retest_session_handoff|software_proof_docker_route_task_field_retest_session_handoff_gate|Objective 5|Objective 2|Objective 3|PR #5|PR #4|Docker|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.16_21-22_route-task-field-retest-session-handoff
git diff --check -- sprints/2026.05.16_21-22_route-task-field-retest-session-handoff
```

实现后 Task D 追加运行各 owner 的 fenced commands。不得用 broad regression 替代围栏，也不得把 local Docker proof 写成真实 field proof。

## 6. 剩余风险

- 本轮没有真实现场材料，因此即使 implementation 全部通过，也只是现场复测交接 readiness。
- Objective 5 仍 blocked 在真实外部云/4G/OSS/CDN/DB/queue/worker evidence。
- Objective 1 / PR #5 硬件 baseline 仍缺真实 vendor/source/procurement/installation/wiring/calibration/HIL entry 材料。
- PR #4 的电梯 assisted delivery 主线要求仍需真实门状态、目标楼层确认、人工协助记录和 field run 才能从 `not_proven` 转向真实验收。
