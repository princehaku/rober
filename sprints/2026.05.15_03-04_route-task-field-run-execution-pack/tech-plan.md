# Sprint 2026.05.15_03-04 Route Task Field Run Execution Pack - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮从 `software_proof_docker_route_task_field_run_review_console_gate` 往前推进到 `software_proof_docker_route_task_field_run_execution_pack_gate`。

实现阶段新增一个 route/task field-run execution pack：

1. `pc-tools/evidence/route_task_field_run_execution_pack.py` 读取上一轮 review console JSON，输出现场联跑 manifest、材料模板、命令清单、重跑清单、同一 `evidence_ref` 要求、phone-safe summary 和 `not_proven` 边界。
2. Robot diagnostics metadata-only 读取 execution pack summary，不触发 collect/dropoff/cancel、ACK、cursor、HIL 或 delivery success。
3. `mobile/web` 增加只读“路线任务现场执行包”面板，只展示 phone-safe summary，不读取 raw artifact、不改变 Start/Confirm/Cancel gating。
4. Product closeout 根据实现证据更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

所有实现输出必须固定：

- `schema=trashbot.route_task_field_run_execution_pack.v1`
- `evidence_boundary=software_proof_docker_route_task_field_run_execution_pack_gate`
- `same_evidence_ref_required=true`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `not_proven` 包含真实 Nav2/fixed-route、真实路线采集、HIL、dropoff/cancel completion、delivery success、Objective 5 external proof

## 2. 文件范围与 Owner

### Task A - `autonomy-engineer`

允许改动：

- `pc-tools/evidence/route_task_field_run_execution_pack.py`
- `pc-tools/evidence/test_route_task_field_run_execution_pack.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- CLI 支持 `--review-json`、`--output`、`--evidence-ref`。
- ready 路径必须从 review console 读取 safe `evidence_ref`、`operator_next_steps`、`commands_to_rerun` 和 `phone_safe_summary`。
- blocked 路径必须覆盖 missing review、bad JSON、unsupported schema、missing evidence_ref、unsafe summary、missing materials 和 mismatch。
- manifest 必须包含 `field_run_manifest`、`required_material_templates`、`first_run_commands`、`rerun_commands`、`same_evidence_ref_required`、`phone_safe_summary`、`not_proven`。
- 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_run_execution_pack.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_task_field_run_execution_pack.py
python3 pc-tools/evidence/route_task_field_run_execution_pack.py --help
rg -n "route_task_field_run_execution_pack|software_proof_docker_route_task_field_run_execution_pack_gate|same_evidence_ref_required|not_proven|delivery_success=false" pc-tools docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_run_execution_pack.py pc-tools/evidence/test_route_task_field_run_execution_pack.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B - `robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- diagnostics 新增 `route_task_field_run_execution_pack` / `route_task_field_run_execution_pack_summary` metadata-only summary。
- 支持 explicit artifact path 和环境变量输入，命名由实现保持清晰，例如 `TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK`。
- summary 只暴露 schema、status、safe evidence ref、materials status、command summary、same evidence ref requirement、not_proven、evidence boundary。
- metadata-only summary 不触发 collect/dropoff/cancel、remote ACK、cursor advance/persistence、terminal ACK、HIL、production readiness、dropoff/cancel completion 或 delivery success。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "route_task_field_run_execution_pack|software_proof_docker_route_task_field_run_execution_pack_gate|metadata-only|delivery_success|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - `full-stack-software-engineer`

允许改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现要求：

- mobile/web 增加只读“路线任务现场执行包”面板。
- 消费 `route_task_field_run_execution_pack`、`route_task_field_run_execution_pack_summary`，以及 `/api/status`、`phone_readiness`、`/api/diagnostics`、nested diagnostics summary 中的兼容字段。
- 显示 execution status、safe `evidence_ref`、same evidence ref requirement、required materials、first-run/rerun commands summary、operator next steps、`not_proven` 和 evidence boundary。
- 缺 summary 时显示 blocked/not_proven，不 fetch raw artifact，不读取本机路径。
- 不展示 token、Authorization、OSS AK/SK、DB/queue URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本机路径、traceback、checksum、complete artifact 或 raw robot response。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_run_execution_pack|software_proof_docker_route_task_field_run_execution_pack_gate|Start|Confirm|Cancel|delivery success|not_proven" mobile docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - `product-okr-owner`

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/tech-done.md`
- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/side2side_check.md`
- `sprints/2026.05.15_03-04_route-task-field-run-execution-pack/final.md`

实现要求：

- 收口时只按实现和验证结果更新 OKR，不得把 execution pack 写成真实 HIL、真实 route、dropoff/cancel completion 或 delivery success。
- 如果只完成 software proof，OKR 文案必须明确 Objective 2 / Objective 3 只是执行材料前移。
- Objective 5 只有在真实外部材料进入证据链时才可上调；本 sprint 默认不覆盖 O5。

验收命令：

```bash
rg -n "2026.05.15_03-04_route-task-field-run-execution-pack|software_proof_docker_route_task_field_run_execution_pack_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_03-04_route-task-field-run-execution-pack
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_03-04_route-task-field-run-execution-pack/tech-done.md sprints/2026.05.15_03-04_route-task-field-run-execution-pack/side2side_check.md sprints/2026.05.15_03-04_route-task-field-run-execution-pack/final.md
```

## 3. 并行启动规则

实现阶段必须并行启动 3 个 Engineer worker：

- `autonomy-engineer` 执行 Task A。
- `robot-software-engineer` 执行 Task B。
- `full-stack-software-engineer` 执行 Task C。

Task A/B/C 文件范围互不重叠。Task B 与 Task C 的接口字段需要对齐，但可以由 Task A 先定义 schema，Task B/C 在同一轮按 schema 消费并在验收失败时返工。Product closeout Task D 等 A/B/C 验证结果返回后执行。

## 4. 接口影响

- 新增 PC/evidence artifact schema：`trashbot.route_task_field_run_execution_pack.v1`。
- 新增 diagnostics summary：`trashbot.route_task_field_run_execution_pack_summary.v1`，字段名 `route_task_field_run_execution_pack` / `route_task_field_run_execution_pack_summary`。
- 新增 mobile read-only panel：field-run execution pack summary。
- 不改变 ROS2 action/service/topic、remote command envelope、Start/Confirm/Cancel gating、ACK/cursor 语义。
- 不新增硬件参数、串口配置、WAVE ROVER 细节或 Objective 5 外部配置。

## 5. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 2 和 Objective 3，均约 62%。Objective 5 约 66%，Objective 1 / Objective 4 约 73%。
2. 本 sprint 针对最低 Objective：是，主线针对 Objective 2 / Objective 3。
3. 具体理由：上一轮 final.md 明确 O2/O3 仍缺真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 上车复账、dropoff/cancel completion 和 delivery success；本轮把 review console 推进为现场执行包，是在 Docker-only 主机上能继续推动 O2/O3 的最接近真实现场材料的一步。Objective 5 虽仍偏低，但需要真实外部云/4G/OSS/CDN/DB/queue 材料才可继续推进，本轮不重复堆 O5 local metadata。

## 6. 风险边界

- `software_proof_docker_route_task_field_run_execution_pack_gate` 只证明 execution pack、diagnostics summary 和 mobile read-only summary 在 Docker/local 环境可生成、可消费、可安全展示。
- execution pack ready 不是真实 Nav2/fixed-route，不是真实路线采集，不是 HIL，不是同一 `evidence_ref` 上车复账，不是 dropoff/cancel completion，不是 delivery success。
- 如果实现中出现“成功送达、已完成投放、真实运行通过、HIL 通过、可开始控制”等文案，必须返工为 `not_proven` / metadata-only。
- 如果 Task A schema 与 Task B/C 消费字段不一致，以 artifact schema 和 `docs/interfaces/ros_contracts.md` 对齐后重跑相关验收。
- 如果本机无法运行 Node 或 Python unittest，worker 必须记录原因、影响和剩余风险；不能用未跑验证替代 pass。

## 7. 本阶段计划验收命令

当前 planning 阶段只验证三份 sprint 计划文档：

```bash
rg -n "sprint_type: epic|Objective 2|Objective 3|Objective 5|software_proof_docker_route_task_field_run_execution_pack_gate|OKR 最低优先级核对|not_proven|delivery success|HIL" sprints/2026.05.15_03-04_route-task-field-run-execution-pack
git diff --check -- sprints/2026.05.15_03-04_route-task-field-run-execution-pack/pre_start.md sprints/2026.05.15_03-04_route-task-field-run-execution-pack/prd.md sprints/2026.05.15_03-04_route-task-field-run-execution-pack/tech-plan.md
```
