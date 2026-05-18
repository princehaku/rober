# Sprint 2026.05.18_08-09 Route Task Field Retest Drill Console - Tech Done

sprint_type: epic

## Autonomy Worker A

### 实际改动

- `tests/__init__.py`：新增顶层验收测试 package 入口，保证 sprint tech-plan 指定的 `python3 -m unittest tests.test_route_task_field_retest_drill_console` 可以直接运行。
- `tests/test_route_task_field_retest_drill_console.py`：复用 `pc-tools/evidence/test_route_task_field_retest_drill_console.py` 的离线围栏测试，避免顶层验收入口和 evidence 目录断言漂移。
- `pc-tools/evidence/README.md`：新增 `route_task_field_retest_drill_console` 证据 gate 说明，明确只消费上一轮 `route_task_field_retest_operator_drill` artifact / summary / compatible wrapper，并产出 `trashbot.route_task_field_retest_drill_console.v1` / `_summary.v1`。

### 验证结果

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_drill_console.py`：通过，无输出。
- `python3 -m unittest tests.test_route_task_field_retest_drill_console`：通过，`Ran 5 tests in 0.021s`，`OK`。
- `rg -n "route_task_field_retest_operator_drill|route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console`：通过，命中 PC evidence、顶层验收测试、产品文档和 sprint 留档中的 operator drill、drill console、software proof 与 fail-closed 关键字。
- `git diff --check -- pc-tools/evidence/route_task_field_retest_drill_console.py pc-tools/evidence/README.md tests/test_route_task_field_retest_drill_console.py docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console`：通过，无 whitespace error。

### 失败定位

- 无新增失败。Autonomy 本轮只补顶层 unittest 入口和 evidence README，核心 PC gate 仍保持 dependency-free、Docker-only software proof 边界。

### 剩余风险

- Autonomy gate 只证明 `route_task_field_retest_operator_drill` 到 `route_task_field_retest_drill_console` 的本地 metadata-only 转换与验收入口可运行；不证明真实 route/elevator field pass、Nav2/fixed-route 实跑、task record/completion signal、dropoff/cancel completion、delivery success、WAVE ROVER/UART/HIL、真实手机/browser/device 或 Objective 5 external proof。

## Robot Worker B

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：让 diagnostics 只读发现 top-level / nested `robot_diagnostics_route_task_field_retest_drill_console_summary`，并把同一 sanitized summary 同步输出到 `route_task_field_retest_drill_console`、`route_task_field_retest_drill_console_summary`、`robot_diagnostics_route_task_field_retest_drill_console_summary` 三个 safe alias。
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：补充 drill console Robot alias 一致性、top-level / nested compatible summary 消费、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和敏感字段不透出断言。
- `docs/product/mobile_user_flow.md`：追加 Robot diagnostics 只读消费说明，明确 alias 只承载 sanitized summary，不读取 raw artifact、local path、checksum、traceback、ROS topic、serial/UART、credentials、ACK、cursor 或 robot command envelope。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过，`Ran 176 tests in 0.345s`，`OK`。
- `rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|not_proven|delivery_success=false|primary_actions_enabled=false|robot_diagnostics_route_task_field_retest_drill_console_summary" onboard/src/ros2_trashbot_behavior docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console`：通过，命中 Robot diagnostics、单测、mobile flow 和 sprint 记录中的 schema/gate/not_proven/alias 证据。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console`：通过，无输出。

### 失败定位与修复

- 首轮 `test_route_task_field_retest_drill_console_robot_alias_sources_are_safe` 失败于 nested Robot alias 输入：完整 summary schema 内部带 `robot_diagnostics_summary` 子对象时，候选顺序误把子对象当完整 summary，导致 `safe_evidence_ref` 丢失并变成 `missing_evidence_ref`。已修复为完整 summary schema 优先，不再被内部子摘要覆盖；重跑全量 diagnostics 单测通过。

### 剩余风险

- Robot diagnostics 仍是 metadata-only / software proof，只证明本地 safe summary 消费与别名输出；不证明真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success、真实手机/browser、WAVE ROVER/UART/HIL 或 Objective 5 external proof。
- 本轮没有改 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor 或 robot command 授权。

## Full-stack Worker C

### 实际改动

- `mobile/web/app.js`：补齐 `route_task_field_retest_drill_console` 首屏只读面板的 operator command groups、required outputs、rerun summary 展示字段，并把 copy/export payload 继续限制在后端 `safe_copy` 授权后的 whitelist-only metadata。
- `mobile/fixtures/mobile_web_status.fixture.json`：新增 `route_task_field_retest_drill_console` / `_summary` fixture，固定 `software_proof_docker_route_task_field_retest_drill_console_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 safe `evidence_ref` 边界。
- `mobile/web/test_mobile_web_entrypoint.py`：补充 drill console 面板、fixture、required outputs 和 rerun summary 的只读断言。
- `docs/product/mobile_user_flow.md`：更新 mobile/web drill console 面板说明，明确 operator command groups、callback checklist、required outputs、rerun summary、safe copy 和 whitelist-only 导出口径。

### 验证结果

- `node --check mobile/web/app.js`：通过，无语法错误。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint`：通过，`Ran 72 tests`，`OK`。
- `rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|not_proven|delivery_success=false|primary_actions_enabled=false|blocked copy unavailable" mobile/web mobile/fixtures mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console`：通过，命中 mobile/web、mobile/fixtures、测试、产品文档和本 sprint 留档中的 drill console / software proof / fail-closed 关键字。
- `git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/index.html mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console`：通过，无 whitespace error。

### 失败定位与修复

- 首轮 `python3 -m unittest mobile.web.test_mobile_web_entrypoint` 失败在 drill console 测试读取旧 `mobile/web/fixtures/status.json`，该旧 fixture 没有本轮 scoped `route_task_field_retest_drill_console` 扩展字段。已把本轮 drill console 两个测试切到 `mobile/fixtures/mobile_web_status.fixture.json`，复跑通过。

### 剩余风险

- 本轮 Full-stack 只证明 mobile/web 对 safe summary 的只读消费和 whitelist-only copy/export，不证明真实手机设备、真实 PWA install prompt、真实 route/elevator field pass、Nav2/fixed-route 实跑、dropoff/cancel completion、delivery success、WAVE ROVER/UART/HIL 或 Objective 5 external proof。
- Start Delivery、Confirm Dropoff、Cancel gating 未改；Robot diagnostics 只输出 phone-safe summary，不透出 raw artifact 或 robot command。

## Product Closeout 记录

### 集成判断

- 三个 worker 小节已合并在同一 `tech-done.md`，并保留各自验证结果与首轮失败修复记录。
- docs/ 同步已覆盖：`docs/product/mobile_user_flow.md` 记录 Robot diagnostics alias 与 mobile/web drill console 面板边界；`pc-tools/evidence/README.md` 记录 Autonomy evidence gate。
- 本轮没有硬件实现、引脚、电压、UART 设备、波特率、JSON 指令、速度映射、反馈协议或机械尺寸改动；因此没有新增 vendor fact 解释，也不把本轮写成 HIL/WAVE ROVER 证据。

### 证据边界

- 本轮是 `software_proof_docker_route_task_field_retest_drill_console_gate`。
- 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不是真实 route/elevator field pass，不是 Nav2/fixed-route proof，不是 task record/completion signal completed，不是 dropoff/cancel completion，不是 delivery success，不是 HIL/WAVE ROVER/UART，不是真实 phone/browser/device proof，也不是 Objective 5 external proof。
