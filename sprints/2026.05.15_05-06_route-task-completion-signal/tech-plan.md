# Sprint 2026.05.15_05-06 Route Task Completion Signal - Tech Plan

sprint_type: epic

## 1. 技术目标

实现 `software_proof_docker_route_task_completion_signal_gate`：让 Docker/local route/task chain 在同一 `evidence_ref` 下汇总 fixed-route status/replay、task record state transitions、dropoff/cancel completion flags、failure/recovery reason，并输出 completion verdict 给 Robot diagnostics 与 mobile/web 只读消费。

证据边界固定：

- `schema=trashbot.route_task_completion_signal.v1`
- `schema_version=1`
- `evidence_boundary=software_proof_docker_route_task_completion_signal_gate`
- `same_evidence_ref_required=true`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_proven` 必须覆盖真实 delivery、真实 dropoff/cancel completion、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、真实手机设备和 Objective 5 external proof。

## 2. 接口草案

Completion signal artifact 建议字段：

- `schema`
- `schema_version`
- `evidence_boundary`
- `evidence_ref`
- `same_evidence_ref_required`
- `completion_verdict`
- `fixed_route_summary`
- `task_record_summary`
- `state_transition_summary`
- `dropoff_completion`
- `cancel_completion`
- `failure_reason`
- `recovery_reason`
- `materials_status`
- `operator_next_steps`
- `phone_safe_summary`
- `not_proven`
- `primary_actions_enabled=false`
- `delivery_success=false`

建议 verdict：

- `ready_for_route_task_completion_review`
- `blocked_missing_completion_materials`
- `blocked_mismatch_evidence_ref`
- `blocked_unsafe_phone_summary`
- `failed_with_recovery_reason`
- `completed_not_proven`

`completed_not_proven` 只能表示 Docker/local completion signal 材料形状足够进入人工复核；默认仍必须保留 `delivery_success=false`，除非未来 closeout 有真实 field-run/dropoff/cancel 完成材料并更新证据边界。

## 3. 并行任务拆分

### Task A - Autonomy completion-signal CLI

Owner：Autonomy Algorithm Engineer (`autonomy-engineer`)

允许改动：

- `pc-tools/evidence/route_task_completion_signal.py`
- `pc-tools/evidence/test_route_task_completion_signal.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 dependency-free CLI，支持读取 route status/replay、task record、上一轮 reconciliation 或 field-run review/intake summary、可选 dropoff/cancel completion material。
- 缺材料、坏 JSON、unsupported schema、`evidence_ref` mismatch、unsafe phone summary、`delivery_success=true` 输入都必须 fail closed。
- 输出必须包含 `software_proof_docker_route_task_completion_signal_gate`、`same_evidence_ref_required=true`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
- 文档说明该 CLI 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_completion_signal.py pc-tools/evidence/test_route_task_completion_signal.py
python3 pc-tools/evidence/test_route_task_completion_signal.py
python3 pc-tools/evidence/route_task_completion_signal.py --help
rg -n "software_proof_docker_route_task_completion_signal_gate|delivery_success=false|not_proven|same_evidence_ref_required|dropoff_completion|cancel_completion" pc-tools/evidence/route_task_completion_signal.py pc-tools/evidence/test_route_task_completion_signal.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_completion_signal.py pc-tools/evidence/test_route_task_completion_signal.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B - Robot diagnostics metadata-only consumption

Owner：Robot Platform Engineer (`robot-software-engineer`)

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- diagnostics 支持 explicit ref 和环境变量读取 completion signal artifact，导出 `route_task_completion_signal` 与兼容 summary。
- 只读消费 metadata，不触发 `/api/collect`、dropoff、cancel、remote ACK、cursor advance/persistence、terminal ACK、Nav2、WAVE ROVER、HIL 或 delivery success。
- 缺 artifact、坏 JSON、unsupported schema/boundary、unsafe fields、`delivery_success=true` 或 primary actions enabled 时必须 blocked/not_proven。
- 文档补充 metadata-only contract，明确 completion signal 不是 command/status/ACK envelope。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_completion_signal|software_proof_docker_route_task_completion_signal_gate|delivery_success=false|not_proven|collect|dropoff|cancel|ACK|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - Full-stack mobile/web read-only completion panel

Owner：User Touchpoint Full-Stack Engineer (`full-stack-software-engineer`)

允许改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现要求：

- 新增只读“路线任务完成信号”panel，消费 `route_task_completion_signal` / summary，兼容 `/api/status`、`phone_readiness`、`/api/diagnostics`、`diagnostics.summary` 和 nested diagnostics summary。
- 展示 `completion_verdict`、safe `evidence_ref`、dropoff/cancel completion status、failure/recovery reason、operator next steps、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 evidence boundary。
- 不 fetch raw artifact、本机路径、complete bundles、checksums、tracebacks、raw robot response、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、credentials、DB/queue URL、OSS AK/SK 或 O5 external proof。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating；panel 不调用 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 或 ACK/cursor routes。

验收命令：

```bash
python3 mobile/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_completion_signal|software_proof_docker_route_task_completion_signal_gate|delivery_success=false|not_proven|dropoff_completion|cancel_completion|primary_actions_enabled=false" mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 4. 集成顺序

1. 并行启动 Task A / Task B / Task C。
2. Task A 先稳定 schema 与 fixture 样例；Task B / Task C 可按本 tech-plan 的字段草案先实现兼容读取。
3. 三个 worker 返回后，由 Product Owner 核对字段名、边界语言、验证日志和 docs 同步。
4. 若字段漂移，优先让对应 owner 修复，不由主节点直接改产品代码。
5. 全部验证通过后补 `tech-done.md`、`side2side_check.md`、`final.md`，再按证据边界更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 5. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 2（约 64%）与 Objective 3（约 64%）。
- 本 sprint 是否针对该 Objective：是。
- 具体理由：本轮直接推进 O2/O3 的 route/task completion signal，从上一轮 reconciliation verdict 进入 dropoff/cancel completion、same `evidence_ref`、fixed-route status/replay 和 task record state transitions 的可执行软件证据链。
- 为什么不针对 Objective 5：Objective 5 约 66%，且下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料；当前 Docker-only 主机不适合继续本地 metadata depth。
- `final.md` 收口时需复核：是否仍保留 `delivery_success=false` 与 `not_proven`，是否只在 O2/O3 软件证据上保守调整进度，是否没有把 completion signal 写成真实 delivery、HIL、Nav2 实跑或 O5 external proof。

## 6. 质量与边界要求

- 代码技术注释必须使用中文，新增/修改代码注释比例需超过 20%，并解释为什么要 fail closed、为什么 summary 只读、为什么不能宣称 delivery success。
- 验证只跑围栏：targeted unittest、`py_compile`、`node --check`、required `rg`、scoped `git diff --check`。
- 不运行 broad regression，不做硬件 smoke，不触碰 vendor/hardware/launch 参数。
- 不修改 `OKR.md`，直到实现和 closeout 证据完成。

## 7. 实现阶段子 agent 派发要求

实现阶段必须在同一轮并行启动 3 个 `spawn_agent(agent_type=worker)`：

- `autonomy-engineer`：使用 `.codex/agents/autonomy-engineer.toml` 的完整 prompt，执行 Task A。
- `robot-software-engineer`：使用 `.codex/agents/robot-software-engineer.toml` 的完整 prompt，执行 Task B。
- `full-stack-software-engineer`：使用 `.codex/agents/full-stack-software-engineer.toml` 的完整 prompt，执行 Task C。

每个 worker prompt 必须包含 `[角色 System Prompt]`、`[本轮任务]`、`[文件范围]`、`[验收命令]`、`[输出要求]` 五段，并要求返回实际改动文件、验证命令输出、失败定位和剩余风险。

