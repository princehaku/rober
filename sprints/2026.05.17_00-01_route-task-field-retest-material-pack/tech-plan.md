# Sprint 2026.05.17_00-01 Route Task Field Retest Material Pack - Tech Plan

sprint_type: epic

## 1. 技术目标

实现 `route_task_field_retest_material_pack` 的四 owner 计划：

- Autonomy：dependency-free PC CLI 打包/校验 field retest material directory。
- Robot：metadata-only diagnostics summary consumer，fail closed。
- Full-stack：mobile/web 只读“现场材料包” panel。
- Product：三方实现后 closeout、`OKR.md` 和 `docs/process/okr_progress_log.md` 同步。

统一 evidence boundary：

- `software_proof_docker_route_task_field_retest_material_pack_gate`
- `trashbot.route_task_field_retest_material_pack.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. 接口与数据契约

Material pack 必须覆盖八类材料：

- `nav2_or_fixed_route_runtime_log`
- `route_completion_signal`
- `task_record`
- `door_state`
- `target_floor_confirmation`
- `human_assistance_note`
- `dropoff_or_cancel_completion`
- `delivery_result`

Artifact / summary 约束：

- 所有 accepted material 必须使用同一 safe `evidence_ref`。
- 缺失材料、placeholder-only、evidence ref mismatch、raw path、credential、unsafe success phrasing、`delivery_success=true`、`primary_actions_enabled=true` 必须 fail closed 或进入 rejected/missing。
- 输出 summary 必须能被 Robot diagnostics 和 mobile/web 只读消费。
- summary 不得包含 raw filesystem path、credential、完整 artifact、traceback、checksum、raw ROS topic、`/cmd_vel`、串口/UART 细节或硬件参数。

## 3. Task A - Autonomy

Owner：Autonomy Algorithm Engineer。

允许修改：

- `pc-tools/evidence/route_task_field_retest_material_pack.py`
- `pc-tools/evidence/test_route_task_field_retest_material_pack.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 dependency-free CLI，读取 `--material-dir`。
- 校验八类材料、同一 `evidence_ref`、placeholder-only、raw path/credential/unsafe success phrasing、`delivery_success=true`、`primary_actions_enabled=true`。
- 输出 `trashbot.route_task_field_retest_material_pack.v1` artifact 与 summary。
- fixture 只能证明软件 gate；没有真实材料时必须保持 `not_proven`。
- 文档写清它供现有 `result_intake` / `result_reconciliation` 消费，不等于真实 field pass。

验收命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_material_pack.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_material_pack.py
python3 pc-tools/evidence/route_task_field_retest_material_pack.py --help
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|trashbot.route_task_field_retest_material_pack.v1|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_material_pack.py pc-tools/evidence/test_route_task_field_retest_material_pack.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_retest_material_pack.py pc-tools/evidence/test_route_task_field_retest_material_pack.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

## 4. Task B - Robot

Owner：Robot Platform Engineer。

允许修改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- metadata-only 消费 material pack summary。
- 缺 summary、schema mismatch、unsafe fields、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 不改变 collect/dropoff/cancel/ACK/Nav2/HIL/delivery success。
- diagnostics 输出只暴露 safe summary、missing/rejected、same evidence ref、operator next steps 和 boundary。

验收命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|trashbot.route_task_field_retest_material_pack.v1|metadata-only|fail closed|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 5. Task C - Full-stack

Owner：User Touchpoint Full-Stack Engineer。

允许修改：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- 新增只读“现场材料包” panel。
- 展示 material completeness、same evidence ref、八类材料状态、missing/rejected、operator next steps、boundary、`not_proven`。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- copy/export 必须 whitelist-only；无 safe copy 时显示 blocked copy unavailable。
- 不暴露 raw paths、credentials、完整 artifacts、tracebacks、checksums、raw ROS topic、`/cmd_vel`、串口/UART 或成功控制文案。

验收命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|现场材料包|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

## 6. Task D - Product Closeout

Owner：Product Manager / OKR Owner。

允许修改：

- `sprints/2026.05.17_00-01_route-task-field-retest-material-pack/tech-done.md`
- `sprints/2026.05.17_00-01_route-task-field-retest-material-pack/side2side_check.md`
- `sprints/2026.05.17_00-01_route-task-field-retest-material-pack/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 等 Task A/B/C 完成并返回验证结果后再收口。
- 汇总实际改动、验证结果、偏差和剩余风险。
- `OKR.md` 只能按实际证据保守更新；若只有 fixture/software proof，不得写成真实 field pass。
- 收口必须明确 Docker-only、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、不是 Objective 5 external proof。

验收命令摘要：

```bash
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|Objective 2|Objective 3|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_00-01_route-task-field-retest-material-pack OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_00-01_route-task-field-retest-material-pack/tech-done.md sprints/2026.05.17_00-01_route-task-field-retest-material-pack/side2side_check.md sprints/2026.05.17_00-01_route-task-field-retest-material-pack/final.md OKR.md docs/process/okr_progress_log.md
git diff --cached --check
```

## 7. 并行计划

Task A、Task B、Task C 的文件范围互不重叠，实施阶段必须并行派发 3 个 Engineer workers。Task D 在 A/B/C 返回后执行，不与实施任务并行写 closeout。

主会话不得直接实现产品代码、测试代码、硬件配置或业务逻辑；主会话只做派发、结果验收、证据核对和 sprint closeout 判断。

## 8. OKR 最低优先级核对

当前 `OKR.md` 4.1 中完成度最低的是 Objective 5，约 66%。本 sprint 不直接针对 Objective 5。

不针对 Objective 5 的理由：

- `OKR.md` 第 6 节明确：只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等真实外部材料时，才继续推进 Objective 5 completion。
- 当前环境是 Docker-only，没有真实外部云/4G/OSS/CDN/DB/queue/worker 材料；继续堆本地 O5 metadata 不能提升真实 Objective 5。
- 最新 sprint final 建议：若仍无 O5 外部材料，优先补同一 `evidence_ref` 的真实现场材料回填样本，至少拿到一组真实 route/task field retest material set。
- PR #4 elevator-assisted delivery 主线仍缺真实 `door_state`、`target_floor_confirmation`、`human_assistance_note`，这正是 Objective 2 的现场材料缺口。
- PR #5 硬件 baseline / 2D LiDAR / ToF / vendor-source 风险仍缺真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；但最近两轮已消费硬件/source/config blocker，`AGENTS.md` 同一 blocker 最多消费 2 轮，不能第三次围绕同一 blocker 写 wrapper。

因此本轮转向 Objective 2 / Objective 3 的 `route_task_field_retest_material_pack`：这是当前 Docker-only host 上仍能前进、且不会冒充 Objective 5 外部 proof 或第三次消费同一硬件 blocker 的最低可行动作。

## 9. 验收边界

本轮成功标准：

- 三个实施 owner 都完成 scoped implementation 与 fenced validation。
- PC/Robot/mobile/docs 均出现 `software_proof_docker_route_task_field_retest_material_pack_gate`。
- material pack 能 fail closed 解释 missing/rejected/same evidence ref/operator next steps。
- mobile Start/Confirm/Cancel gating 不改变。
- closeout 文档和 `OKR.md` 保持证据边界，不写真实 field pass。

本轮失败标准：

- 使用 fixture 却宣称真实 field pass。
- 任何 surface 输出 `delivery_success=true` 或 `primary_actions_enabled=true`。
- Robot diagnostics 或 mobile/web 暴露 raw path、credential、完整 artifact、traceback、checksum、raw ROS topic、`/cmd_vel`、串口/UART 或硬件参数。
- 第三次围绕 PR #5 同一 hardware/source/config blocker 写 wrapper，而不是推进 route/task material pack。
