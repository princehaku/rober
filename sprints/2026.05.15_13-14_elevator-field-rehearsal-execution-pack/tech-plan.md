# Sprint 2026.05.15_13-14 Elevator Field Rehearsal Execution Pack - Tech Plan

sprint_type: epic

## 1. 技术抓手

复用 `route_task_field_run_execution_pack` 和上一轮 `elevator_field_run_review` 的软件证明模式，新增 gate `software_proof_docker_elevator_field_rehearsal_execution_pack_gate`。本轮只证明 Docker/local execution pack artifact、Robot diagnostics 只读摘要、mobile 只读 panel 和安全文案围栏可工作。

## 2. 分工与文件范围

### Task A - Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/elevator_field_run_execution_pack.py`
- `pc-tools/evidence/test_elevator_field_run_execution_pack.py`
- `pc-tools/README.md`
- `docs/product/elevator_assisted_delivery.md`
- 必要时 `docs/navigation/fixed_route_workflow.md`

实现：

- 新增 CLI，从 `--review-json` 读取 `trashbot.elevator_field_run_review.v1` 或 `trashbot.elevator_field_run_review_summary.v1`。
- 支持 `--output` 和 `--once-json`，输出 `trashbot.elevator_field_run_execution_pack.v1` 和 summary。
- 将 review decision、blocked categories、operator next steps、commands to rerun 和 capture checklist 转成 `controlled_rehearsal_manifest`、`required_material_templates`、`first_run_commands`、`rerun_commands`、`operator_handoff`。
- 输出 not_proven、`delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true`，并过滤 raw artifact、路径、ROS topic、serial/UART、WAVE ROVER、credential 和成功文案。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/elevator_field_run_execution_pack.py pc-tools/evidence/test_elevator_field_run_execution_pack.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_elevator_field_run_execution_pack.py
python3 pc-tools/evidence/elevator_field_run_execution_pack.py --help
rg -n "elevator_field_run_execution_pack|software_proof_docker_elevator_field_rehearsal_execution_pack_gate|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence pc-tools/README.md docs/product/elevator_assisted_delivery.md
git diff --check -- pc-tools/evidence/elevator_field_run_execution_pack.py pc-tools/evidence/test_elevator_field_run_execution_pack.py pc-tools/README.md docs/product/elevator_assisted_delivery.md docs/navigation/fixed_route_workflow.md
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现：

- 只读消费 explicit ref 与环境变量 `TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK` / `_SUMMARY`。
- 暴露 `elevator_field_run_execution_pack` 和 `elevator_field_run_execution_pack_summary`，严格校验 schema/boundary/redaction。
- 固定 `delivery_success=false`、`primary_actions_enabled=false`，不触发 collect/dropoff/cancel、ACK、Nav2、HIL 或真实送达。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "elevator_field_run_execution_pack|software_proof_docker_elevator_field_rehearsal_execution_pack_gate|TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK|delivery_success|primary_actions_enabled" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `docs/product/mobile_user_flow.md`

实现：

- 新增只读“电梯演练执行包” panel，兼容 top-level、`phone_readiness`、diagnostics summary 和 nested diagnostics summary。
- 展示 execution pack verdict、safe evidence ref、controlled rehearsal manifest、required material templates、first-run/rerun commands、operator handoff、not_proven 和 boundary。
- 过滤 raw ROS topic、serial/UART、WAVE ROVER、local path、credential、raw artifact 和 success phrasing。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "elevator_field_run_execution_pack|software_proof_docker_elevator_field_rehearsal_execution_pack_gate|delivery_success|primary_actions_enabled|not_proven" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md
```

### Task D - Product Manager / OKR Owner

允许改动：

- `sprints/2026.05.15_13-14_elevator-field-rehearsal-execution-pack/tech-done.md`
- `sprints/2026.05.15_13-14_elevator-field-rehearsal-execution-pack/side2side_check.md`
- `sprints/2026.05.15_13-14_elevator-field-rehearsal-execution-pack/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现：

- 工程任务返回后汇总实际改动、验证结果、证据边界和 OKR 影响。
- 若只形成软件证明，可保守更新 Objective 2/3，禁止声称真实电梯、HIL、delivery success 或 O5 external proof。

验收命令：

```bash
rg -n "elevator_field_run_execution_pack|software_proof_docker_elevator_field_rehearsal_execution_pack_gate|not real|不证明|delivery_success=false|Objective 5" sprints/2026.05.15_13-14_elevator-field-rehearsal-execution-pack OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.15_13-14_elevator-field-rehearsal-execution-pack OKR.md docs/process/okr_progress_log.md
```

## 3. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 66%。
- 本 sprint 是否针对该 Objective：否。
- 如不针对，理由：`OKR.md` 第 6 节明确写明 O5 只有拿到真实外部材料时才应继续推进 completion；本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 证据。继续做本地 O5 metadata 会重复消耗 blocker。
- final.md 收口时需复核：本轮是否仍无 O5 外部材料；若无，继续保持 O5 不上调。

## 4. 风险与边界

- 本轮所有结果都必须是 `software_proof_docker_elevator_field_rehearsal_execution_pack_gate`。
- 真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion 和 delivery success 仍需现场材料补齐。
- 验证只做围栏，不新增泛化测试堆叠。
