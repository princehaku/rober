# Sprint 2026.05.16_20-21 Route Task Field Retest Execution Pack - Tech Plan

sprint_type: epic

## 1. 目标

实现 `route_task_field_retest_execution_pack`，把上一轮 `route_task_terminal_review_decision` 的 review decision、owner handoff、next required evidence 和 field retest request guidance 转成下一次真实现场复测可使用的 execution pack。该 pack 只证明 Docker/local software proof 的打包与展示链路，不证明真实 field pass、HIL、真实手机/browser、delivery success 或 Objective 5 external proof。

统一边界：

- `software_proof_docker_route_task_field_retest_execution_pack_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. 架构和接口

数据流：

1. Autonomy PC gate 消费上一轮 `route_task_terminal_review_decision` summary 或显式 JSON。
2. PC gate 输出 `trashbot.route_task_field_retest_execution_pack.v1` artifact 和 `trashbot.route_task_field_retest_execution_pack_summary.v1` summary。
3. Robot diagnostics metadata-only 消费 summary，向 `/api/diagnostics` 或 phone-safe status surface 暴露安全摘要。
4. Mobile/web 只读展示 execution pack，copy/export whitelist-only，所有 primary action gating 不变。
5. Product closeout 汇总 evidence boundary、OKR 变更和剩余真实证据缺口。

跨 owner contract：

- `schema` 必须为 `trashbot.route_task_field_retest_execution_pack.v1`。
- Summary schema 建议为 `trashbot.route_task_field_retest_execution_pack_summary.v1`。
- 必须包含 safe `evidence_ref`，并要求同一 `evidence_ref` 贯穿 field materials、rerun commands、task record、route completion signal 和 diagnostics/mobile summary。
- 必须包含 `required_field_materials`、`rerun_commands`、`operator_handoff`、`field_retest_checklist`、`boundary`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺失、unsupported、unsafe、evidence_ref mismatch 必须 fail closed。

## 3. OKR 最低优先级核对

当前 `OKR.md` 4.1 中完成度最低的是 Objective 5，约 66%。本 sprint 不直接针对 Objective 5。

不针对 Objective 5 的具体理由：

- `OKR.md` 第 6 节明确，继续推进 Objective 5 completion 需要真实外部材料：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等。
- 当前开发主机只有 Docker，无法提供这些真实外部材料。
- 继续做本地 O5 metadata wrapper 不能增加 Objective 5 completion，且会重复消费 blocked-by-design 证据。

本 sprint 转向 Objective 2 / Objective 3 的理由：

- Objective 2 与 Objective 3 当前均约 80%，是下一个可行动低完成度方向。
- 上一轮 `route_task_terminal_review_decision` 已产出 review decision、owner handoff、next required evidence 和 field retest request guidance。
- 本轮可以把这些材料转成 field retest execution pack，服务下一次真实 Nav2/fixed-route + task record + route completion signal 的同一 `evidence_ref` 现场回填。
- 最近两轮 `2026.05.16_17-18_hardware-baseline-source-alignment` 与 `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 已连续消费 PR #5 硬件/source/config blocker；根据 `AGENTS.md` 同一 blocker 最多消费 2 轮 sprint 的红线，本轮不能继续第三轮硬件 blocker wrapper。

## 4. Task A - Autonomy Algorithm Engineer

### 文件范围

- Create: `pc-tools/evidence/route_task_field_retest_execution_pack.py`
- Create: `pc-tools/evidence/test_route_task_field_retest_execution_pack.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/navigation/fixed_route_workflow.md`

### 实现要求

- 新增 dependency-free PC gate。
- 输入支持：
  - 上一轮 `route_task_terminal_review_decision` summary。
  - 显式 JSON。
- 输出：
  - `trashbot.route_task_field_retest_execution_pack.v1`。
  - `trashbot.route_task_field_retest_execution_pack_summary.v1`。
- 输出必须包含：
  - same `evidence_ref`。
  - `required_field_materials`：真实 Nav2/fixed-route runtime log、route completion signal、task record、operator field note、mobile/diagnostics safe summary；如 source summary 提到 elevator，则包含 door state、target floor confirmation、human assistance note。
  - `rerun_commands`：现场 first-run / rerun 命令摘要。
  - `operator_handoff`。
  - `field_retest_checklist`。
  - `boundary=software_proof_docker_route_task_field_retest_execution_pack_gate`。
  - `not_proven`。
  - `delivery_success=false`。
  - `primary_actions_enabled=false`。
- 不能写入真实 field pass、HIL、phone device pass、delivery success、Objective 5 external proof。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_execution_pack.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_execution_pack.py
python3 pc-tools/evidence/route_task_field_retest_execution_pack.py --help
rg -n "route_task_field_retest_execution_pack|software_proof_docker_route_task_field_retest_execution_pack_gate|trashbot.route_task_field_retest_execution_pack.v1|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 2|Objective 3|Objective 5" pc-tools/evidence/route_task_field_retest_execution_pack.py pc-tools/evidence/test_route_task_field_retest_execution_pack.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_retest_execution_pack.py pc-tools/evidence/test_route_task_field_retest_execution_pack.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

## 5. Task B - Robot Platform Engineer

### 文件范围

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/ros_contracts.md`

### 实现要求

- Metadata-only 消费 `route_task_field_retest_execution_pack` / `route_task_field_retest_execution_pack_summary`。
- 支持 top-level status、`phone_readiness`、`diagnostics.summary`、`diagnostics.diagnostics_summary` 或既有 nested diagnostics summary pattern。
- 缺失、unsupported schema、unsafe copy、missing `evidence_ref`、same evidence_ref mismatch、success wording、primary action enabled 均 fail closed。
- 不触发 collect、dropoff、cancel、ACK、cursor、Nav2、HIL、delivery success。
- Diagnostics summary 只能暴露 phone-safe fields：schema、execution status、safe evidence_ref、same_evidence_ref_required、required field materials summary、rerun commands summary、operator handoff、field retest checklist、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_execution_pack|software_proof_docker_route_task_field_retest_execution_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false|ACK|Nav2|HIL" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 6. Task C - User Touchpoint Full-Stack Engineer

### 文件范围

- Modify: `mobile/web/app.js`
- Modify: `mobile/web/styles.css`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `mobile/web/fixtures/status.json`
- Modify: `docs/product/mobile_user_flow.md`

### 实现要求

- 新增只读 field retest execution pack panel。
- 消费 `route_task_field_retest_execution_pack`、`route_task_field_retest_execution_pack_summary` 或 compatible safe summaries。
- 展示字段仅限：
  - execution status。
  - safe `evidence_ref`。
  - same evidence ref required。
  - required field materials summary。
  - rerun command summary。
  - operator handoff。
  - field retest checklist。
  - boundary。
  - `not_proven`。
  - `delivery_success=false`。
  - `primary_actions_enabled=false`。
- Copy/export whitelist-only，不导出 raw artifacts、local paths、checksums、tracebacks、raw ROS topics、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER parameters、credentials、DB/queue URLs、OSS AK/SK 或 Objective 5 external material。
- Start / Confirm Dropoff / Cancel gating 不变。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "route_task_field_retest_execution_pack|software_proof_docker_route_task_field_retest_execution_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false|Start|Confirm Dropoff|Cancel|whitelist" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

## 7. Task D - Product Manager / OKR Owner

### 文件范围

- Create/modify: `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/tech-done.md`
- Create/modify: `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/side2side_check.md`
- Create/modify: `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

### 收口要求

- 汇总 Task A/B/C 实际改动和验证结果。
- 明确本轮只代表 `software_proof_docker_route_task_field_retest_execution_pack_gate`。
- 回顾 Objective 5 最低但 blocked 的理由。
- 明确 PR #5 硬件/source/config blocker 已连续两轮消费，本轮遵守红线切换 Objective。
- 如 OKR 有上调，只能保守上调 Objective 2 / Objective 3 / Objective 4 中被真实 software proof 支撑的部分；Objective 5 不得上调。
- 继续列出真实证据缺口：真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、真实楼层确认、人工协助记录、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof。

### 验收命令

```bash
rg -n "route_task_field_retest_execution_pack|software_proof_docker_route_task_field_retest_execution_pack_gate|Objective 5|Objective 2|Objective 3|PR #5|PR #4|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_20-21_route-task-field-retest-execution-pack
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/tech-done.md sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/side2side_check.md sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/final.md
```

## 8. 并行启动计划

本轮为 Epic sprint，且 Task A / Task B / Task C 文件范围互不重叠，必须按 `AGENTS.md` 并行启动 3 个 Engineer worker：

- Autonomy Algorithm Engineer 负责 Task A。
- Robot Platform Engineer 负责 Task B。
- User Touchpoint Full-Stack Engineer 负责 Task C。

Product Manager / OKR Owner 在三位 Engineer 返回后执行 Task D closeout。主节点只做派发、等待、验收和 sprint 文档收口，不直接写产品代码、测试代码或硬件配置。

## 9. 全局验证围栏

后续实现完成后，除各 Task 自己的验收命令外，Product closeout 需要至少运行：

```bash
rg -n "route_task_field_retest_execution_pack|software_proof_docker_route_task_field_retest_execution_pack_gate|Objective 5|Objective 2|Objective 3|PR #5|PR #4|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_20-21_route-task-field-retest-execution-pack OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_20-21_route-task-field-retest-execution-pack OKR.md docs/process/okr_progress_log.md
```

本启动阶段仅创建 `pre_start.md`、`prd.md`、`tech-plan.md`，启动阶段验收命令为：

```bash
test -f sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/pre_start.md && test -f sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/prd.md && test -f sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/tech-plan.md
rg -n "route_task_field_retest_execution_pack|software_proof_docker_route_task_field_retest_execution_pack_gate|Objective 5|Objective 2|Objective 3|PR #5|PR #4|Docker|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.16_20-21_route-task-field-retest-execution-pack
git diff --check -- sprints/2026.05.16_20-21_route-task-field-retest-execution-pack
```

## 10. 剩余风险

- 本轮 execution pack 仍是 software proof only，不能替代真实 field retest。
- 后续 worker 若扩大文件范围，必须在 `tech-done.md` 解释并补齐 docs 同步；否则视为范围漂移。
- 若真实现场材料仍不可用，closeout 不得上调真实送达、HIL、手机真机或 Objective 5 completion。
