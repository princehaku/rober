# Sprint 2026.05.15_02-03 Route Task Field Run Review Console - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮在上一轮 `route_task_field_run_intake` 之后增加 review console/report 层：

1. `pc-tools/evidence/route_task_field_run_review.py` 只读 intake/crosscheck JSON，输出 operator/support review report。
2. diagnostics 读取 review report，输出 metadata-only summary。
3. `mobile/web` 展示 review summary 的只读面板。
4. Product closeout 更新 OKR 和 sprint 证据边界。

所有输出固定为 `software_proof_docker_route_task_field_run_review_console_gate`，并保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 文件范围与 Owner

### Task A - `autonomy-engineer`

允许改动：

- `pc-tools/evidence/route_task_field_run_review.py`
- `pc-tools/evidence/test_route_task_field_run_review.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_run_review.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_task_field_run_review.py
python3 pc-tools/evidence/route_task_field_run_review.py --help
rg -n "route_task_field_run_review|software_proof_docker_route_task_field_run_review_console_gate|delivery_success=false|not_proven" pc-tools docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_run_review.py pc-tools/evidence/test_route_task_field_run_review.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

### Task B - `robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "route_task_field_run_review|software_proof_docker_route_task_field_run_review_console_gate|metadata-only|delivery_success" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
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

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_run_review|software_proof_docker_route_task_field_run_review_console_gate|Start|Confirm|Cancel|delivery_success" mobile docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - `product-okr-owner`

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.15_02-03_route-task-field-run-review-console/tech-done.md`
- `sprints/2026.05.15_02-03_route-task-field-run-review-console/side2side_check.md`
- `sprints/2026.05.15_02-03_route-task-field-run-review-console/final.md`

验收命令：

```bash
rg -n "2026.05.15_02-03_route-task-field-run-review-console|software_proof_docker_route_task_field_run_review_console_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_02-03_route-task-field-run-review-console
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_02-03_route-task-field-run-review-console/tech-done.md sprints/2026.05.15_02-03_route-task-field-run-review-console/side2side_check.md sprints/2026.05.15_02-03_route-task-field-run-review-console/final.md
```

## 3. 接口影响

- 新增 PC/evidence artifact schema：`trashbot.route_task_field_run_review_console.v1`。
- 新增 diagnostics summary：`route_task_field_run_review` / `route_task_field_run_review_summary`。
- 新增 mobile readonly panel：field-run review report。
- 不改变 ROS2 action/service/topic、remote command envelope、Start/Confirm/Cancel gating、ACK/cursor 语义。

## 4. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。
3. 理由：Objective 5 的主要缺口是公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 等真实外部材料；本机只有 Docker/local 软件环境，继续堆本地 O5 metadata 不能提升真实 O5 证据。近期 final.md 也反复确认该 stop rule。Objective 2 / Objective 3 当前可执行缺口是把 field-run intake/crosscheck 变成 operator/support 可用的 review decision 和重跑清单，为下一次真实路线-任务 field run 做准备。

## 5. 风险边界

- 若 Task A 发现 review report 只能复制 intake 字段、没有 operator decision 或重跑价值，应停止实现并返回 blocked。
- 若 diagnostics 或 mobile 展示引入“成功/已送达/可控制”语义，必须回退为只读 `not_proven`。
- 本轮不因本地 software proof 提升 Objective 5，也不声明真实路线、HIL 或 delivery success。
