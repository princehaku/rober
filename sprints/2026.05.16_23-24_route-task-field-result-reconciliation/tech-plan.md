# Sprint 2026.05.16_23-24 Route Task Field Result Reconciliation - Tech Plan

sprint_type: epic

## 1. 技术目标

本轮实现 `route_task_field_retest_result_reconciliation`：在 Docker-only 条件下新增 fail-closed reconciliation contract，消费上一轮 result intake、session handoff、execution pack 相关 artifact/summary/wrapper，按同一 `evidence_ref` 对八类现场结果材料做一致性复账，并输出：

- PC artifact / summary
- Robot diagnostics metadata-only summary
- mobile/web 只读 panel
- Product closeout / OKR 保守同步

统一证据边界：

- `software_proof_docker_route_task_field_retest_result_reconciliation_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮只做 Docker/local software proof，不宣称真实 field pass、真实 Nav2/fixed-route、真实电梯、真实 WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、delivery_result 或 Objective 5 external proof。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对 Objective 5 的理由是：`OKR.md` 第 6 节明确只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等真实外部材料时才应继续推进 Objective 5 completion；当前开发主机只有 Docker，本轮无法产出这些外部材料。
4. 本轮转向 Objective 2 / Objective 3 的具体证据：
   - 最新 `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/final.md` 建议：若仍没有 O5 外部材料，继续围绕同一 `evidence_ref` 推进真实现场材料回填或 field result reconciliation，不要把 intake readiness 当 field pass。
   - 最近三轮已完成 `route_task_field_retest_execution_pack -> route_task_field_retest_session_handoff -> route_task_field_retest_result_intake`，剩余缺口反复集中在真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
   - PR #4 已把 elevator-assisted delivery 写成主线必须能力，因此本轮 O2/O3 reconciliation 必须覆盖 `door_state`、`target_floor_confirmation` 和 `human_assistance_note`。
   - PR #5 review threads 仍显示硬件基线/2D LiDAR/ToF/vendor source 的 P1/P2 风险；但 `2026.05.16_17-18` 和 `2026.05.16_18-19` 已连续两轮消费该硬件/source/config blocker，上一轮 `22-23` 已按 `AGENTS.md` 同一 blocker 红线转向 O2/O3。本轮继续避免第三次消费同一 PR #5 blocker。

## 2. Owner 拆分

本轮是 4 owner Epic sprint。Autonomy、Robot、Full-stack 三个实施任务文件范围互不重叠，实施阶段必须并行派发；Product closeout 在三方返回后收口。

### Task A Autonomy

责任人：Autonomy Algorithm Engineer。

目标：创建 PC-side result reconciliation gate，把 result intake / session handoff / execution pack 和八类现场结果材料复账为 artifact / summary。

允许修改：

- `pc-tools/evidence/route_task_field_retest_result_reconciliation.py`
- `pc-tools/evidence/test_route_task_field_retest_result_reconciliation.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 输入支持 artifact / summary / wrapper / nested JSON，并能读取上一轮 `route_task_field_retest_result_intake`、`route_task_field_retest_session_handoff`、`route_task_field_retest_execution_pack` 的 sanitized summary。
- 输出 schema 建议为 `trashbot.route_task_field_retest_result_reconciliation.v1` 与 `trashbot.route_task_field_retest_result_reconciliation_summary.v1`。
- 必须检查同一 `evidence_ref`，并覆盖八类现场结果材料：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result。
- 必须输出 reconciliation verdict、same evidence ref status、missing material list、mismatch reasons、placeholder/unsafe material blocks、operator next steps、rerun summary、field callback checklist 和 fail-closed phone-safe summary。
- 必须拒绝 success phrasing、placeholder-only materials、证据号不一致、弱类型 `same_evidence_ref_required`、`delivery_success=true` 或 `primary_actions_enabled=true`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_reconciliation.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_reconciliation.py
python3 pc-tools/evidence/route_task_field_retest_result_reconciliation.py --help
rg -n "route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_reconciliation_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_retest_result_reconciliation.py pc-tools/evidence/test_route_task_field_retest_result_reconciliation.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B Robot

责任人：Robot Platform Engineer。

目标：让 Robot diagnostics metadata-only 消费 Task A summary，并保持 fail-closed。

允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 支持 `route_task_field_retest_result_reconciliation` / `_summary` 字段、环境变量或现有 diagnostics summary wrapper。
- 只输出 phone-safe metadata，不读取完整 raw artifact，不暴露 raw ROS topic、`/cmd_vel`、串口/UART、credentials、local paths、checksums 或 tracebacks。
- 缺失、schema 不匹配、same `evidence_ref` 不成立、成功措辞、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 保留 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_reconciliation_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C Full-stack

责任人：User Touchpoint Full-Stack Engineer。

目标：在 `mobile/web` 增加只读“路线任务现场结果复账” panel、fixture/test 和产品文档。

允许修改：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- panel 消费 `route_task_field_retest_result_reconciliation` / `_summary` 以及 Robot diagnostics 的 compatible summary。
- 只展示 safe `evidence_ref`、reconciliation verdict、same evidence ref status、八类结果材料状态、missing material list、mismatch reasons、operator next steps、safe copy、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、evidence boundary。
- copy/export whitelist-only；若无 `safe_copy`，显示 blocked copy unavailable。
- 不改变 Start Delivery、Confirm Dropoff、Cancel authorization。
- 不暴露 raw artifacts、raw JSON、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、credentials、DB/queue URLs、OSS AK/SK、local paths、tracebacks、checksums 或完整 artifacts。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_reconciliation_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

### Task D Product closeout

责任人：Product Manager / OKR Owner。

目标：在 Task A/B/C 返回后完成 sprint 留档、OKR 保守同步和过程日志。

允许修改：

- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/tech-done.md`
- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/side2side_check.md`
- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 Task A/B/C 实际改动、验证日志片段、失败定位和剩余风险。
- `OKR.md` 只能基于真实 evidence 保守更新；没有真实 field materials 时不得写成 field pass。
- Objective 5 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 时保持不提升。
- 明确本轮仍是 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `docs/process/okr_progress_log.md` 记录 PR #4、PR #5、Docker-only、O5 blocked 和 O2/O3 rerank 依据。

验收命令：

```bash
rg -n "route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_reconciliation_gate|Objective 5|Objective 2|Objective 3|PR #5|PR #4|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_23-24_route-task-field-result-reconciliation
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_23-24_route-task-field-result-reconciliation/tech-done.md sprints/2026.05.16_23-24_route-task-field-result-reconciliation/side2side_check.md sprints/2026.05.16_23-24_route-task-field-result-reconciliation/final.md
```

## 3. 接口影响

- 新增 PC evidence gate contract：`trashbot.route_task_field_retest_result_reconciliation.v1` / `trashbot.route_task_field_retest_result_reconciliation_summary.v1`。
- Robot diagnostics 只新增 metadata-only compatible summary 消费，不改变 task_orchestrator 状态机、不新增 motion/control route。
- mobile/web 只新增 read-only panel，不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 语义和 gating。
- Product closeout 只同步 sprint / OKR / process docs，不改变 runtime contract。

## 4. 并行派发要求

实施阶段必须在同一轮并行启动 Task A / Task B / Task C 三个 Engineer worker；Task D 等三方输出后收口。若运行时缺少子 agent 能力，`final.md` 必须解释降级原因；主节点不得直接写产品代码、测试代码、硬件配置或运行实现验证。

## 5. Docs 同步范围

实现阶段必须同步更新以下 docs，且每个 owner 的 docs 范围互不重叠：

- Autonomy：`docs/navigation/fixed_route_workflow.md`
- Robot：`docs/interfaces/ros_contracts.md`
- Full-stack：`docs/product/mobile_user_flow.md`
- Product：`docs/process/okr_progress_log.md`

若实现未触及对应行为，worker 必须在输出里说明无需更新的原因；但本轮计划默认这些文档都需要同步。

## 6. 全局验收命令

Planning 文档创建后先运行：

```bash
test -f sprints/2026.05.16_23-24_route-task-field-result-reconciliation/pre_start.md && test -f sprints/2026.05.16_23-24_route-task-field-result-reconciliation/prd.md && test -f sprints/2026.05.16_23-24_route-task-field-result-reconciliation/tech-plan.md
rg -n "sprint_type: epic|route_task_field_retest_result_reconciliation|software_proof_docker_route_task_field_retest_result_reconciliation_gate|Objective 5|Objective 2|Objective 3|PR #4|PR #5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.16_23-24_route-task-field-result-reconciliation
git diff --check -- sprints/2026.05.16_23-24_route-task-field-result-reconciliation/pre_start.md sprints/2026.05.16_23-24_route-task-field-result-reconciliation/prd.md sprints/2026.05.16_23-24_route-task-field-result-reconciliation/tech-plan.md
```

实现后 Task D 追加运行各 owner 的 fenced commands。不得用 broad regression 替代围栏，也不得把 local Docker proof 写成真实 field proof。

## 7. 剩余风险

- 本轮没有真实现场材料，因此即使 implementation 全部通过，也只是现场结果复账能力，不是 field pass。
- Objective 5 仍 blocked 在真实外部云/4G/OSS/CDN/DB/queue/worker evidence。
- Objective 1 / PR #5 硬件 baseline 仍缺真实 vendor/source/procurement/installation/wiring/calibration/HIL entry 材料。
- PR #4 的电梯 assisted delivery 主线要求仍需真实 door_state、target_floor_confirmation、human_assistance_note 和 field run 才能从 `not_proven` 转向真实验收。
