# Sprint 2026.05.17_01-02 Route Task Field Retest Operator Drill - Tech Plan

sprint_type: epic

## 1. 总体方案

实现 `route_task_field_retest_operator_drill`，作为 `route_task_field_retest_material_pack` 后的 PC/Robot/mobile software-proof 演练层。该层不替代真实现场材料，只把现场人员接下来如何运行 material pack、result intake、result reconciliation 固化成 safe artifact / summary。

统一 evidence boundary：

- `software_proof_docker_route_task_field_retest_operator_drill_gate`
- `trashbot.route_task_field_retest_operator_drill.v1`
- `trashbot.route_task_field_retest_operator_drill_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. Task A - Autonomy

Owner：`autonomy-engineer`

允许改动：

- `pc-tools/evidence/route_task_field_retest_operator_drill.py`
- `pc-tools/evidence/test_route_task_field_retest_operator_drill.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 dependency-free PC CLI，支持 `--material-pack-json`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`。
- 兼容 material pack artifact、summary、wrapper / nested JSON。
- 输出 operator drill artifact / summary，包含 material pack command、result intake command、result reconciliation command、required outputs、missing material prompts、operator callback checklist、rerun notes 和 safe copy。
- 对 unsupported schema/boundary、证据号不一致、弱类型 `same_evidence_ref_required`、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER、success wording、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 代码新增技术注释使用中文，避免硬件细节猜测。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_operator_drill.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_operator_drill.py
python3 pc-tools/evidence/route_task_field_retest_operator_drill.py --help
rg -n "route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|trashbot.route_task_field_retest_operator_drill.v1|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_operator_drill.py pc-tools/evidence/test_route_task_field_retest_operator_drill.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_retest_operator_drill.py pc-tools/evidence/test_route_task_field_retest_operator_drill.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

## 3. Task B - Robot

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 新增 `route_task_field_retest_operator_drill` / `_summary` diagnostics metadata-only consumer。
- 只暴露 safe summary、safe `evidence_ref`、drill status、next command labels、missing material prompts、operator callback checklist、boundary。
- 对 missing、unsupported、unsafe、success phrasing、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 不改变 collect、dropoff、cancel、ACK、Nav2、HIL 或 delivery success 语义。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|metadata-only|fail closed|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
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

- 新增只读“现场操作演练” panel，消费 operator drill / summary / Robot diagnostics compatible summary。
- 展示 drill status、safe `evidence_ref`、next command labels、missing material prompts、operator callback checklist、boundary、`not_proven`。
- Start Delivery、Confirm Dropoff、Cancel gating 不变。
- copy/export 不允许 raw artifact、raw path、credential、ROS topic、serial/UART/WAVE ROVER、success wording。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|现场操作演练|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

## 5. Task D - Product Closeout

Owner：`product-okr-owner`

允许改动：

- `sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/tech-done.md`
- `sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/side2side_check.md`
- `sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 汇总 A/B/C worker 的实际改动、验证结果、失败定位和剩余风险。
- 保守更新 OKR：Objective 5 不提升；O2/O3/O4 是否提升必须基于实际 worker 交付和证据边界。
- 明确 PR #4 / PR #5 证据如何支撑本轮方向。
- 明确本轮不是真实 field pass、HIL、真实手机/browser 或 O5 external proof。

验收命令：

```bash
rg -n "route_task_field_retest_operator_drill|software_proof_docker_route_task_field_retest_operator_drill_gate|Objective 2|Objective 3|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_01-02_route-task-field-retest-operator-drill OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/tech-done.md sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/side2side_check.md sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/final.md OKR.md docs/process/okr_progress_log.md
```

## 6. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 66%。
- 本 sprint 是否针对该 Objective：否。
- 不针对理由：本机只有 Docker，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。继续本地 O5 metadata depth 不能形成真实 O5 external proof。
- 本 sprint 目标 Objective：Objective 2 / Objective 3 为主，Objective 4 只读消费为辅。
- final.md 收口时需复核：O5 外部材料是否仍不可用；如不可用，是否继续保留 O5 不提升。
