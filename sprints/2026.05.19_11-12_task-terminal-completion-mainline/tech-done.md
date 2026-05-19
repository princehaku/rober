# Sprint 2026.05.19_11-12 Task Terminal Completion Mainline - Tech Done

## Robot 段落

### 实际改动

- `task_record.py` 新增 `task_terminal_completion_mainline`，作为 Robot 侧
  dropoff/cancel terminal action 的安全事实源。
- `operator_gateway_diagnostics.py` 新增
  `robot_diagnostics_task_terminal_completion_mainline_summary`，只消费
  task_record/latest status/diagnostics 中已经净化的 summary。
- Robot 单测覆盖 task record 写入、diagnostics 摘要、success/cancel/failure
  fail-closed 边界和 task orchestrator dry-run 记录。
- `docs/interfaces/task_record.md` 和
  `docs/interfaces/operator_gateway_diagnostics.md` 同步记录接口契约。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  通过，无输出。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_task_record.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  通过：`Ran 228 tests in 0.684s OK`。
- `rg -n "task_terminal_completion_mainline|robot_diagnostics_task_terminal_completion_mainline_summary|dropoff|cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 2|PR #4" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_11-12_task-terminal-completion-mainline`
  通过，命中 Robot 代码、测试、接口文档和 sprint 边界文本。
- `git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_11-12_task-terminal-completion-mainline`
  通过，无 whitespace error。

### 剩余风险

- 本轮仍是 `software_proof` / `not_proven`，固定
  `delivery_success=false`、`primary_actions_enabled=false`。
- 无真实 task record、真实 dropoff/cancel completion 材料、同一
  `evidence_ref` 的现场复账、真实 Nav2/fixed-route、电梯现场材料、真实手机、
  WAVE ROVER/UART/HIL 或 Objective 5 external proof。

## Full-Stack 段落

### 实际改动

- `mobile/web/app.js` 新增只读 "任务终态主链路" panel，位置跟随 `route_task_terminal_review_decision`，只消费 `robot_diagnostics_task_terminal_completion_mainline_summary`。
- `mobile/web/styles.css` 新增 panel/grid 样式接入，保持现有 phone-first 卡片布局。
- `mobile/web/test_mobile_web_entrypoint.py` 新增 terminal mainline 用例，覆盖 Robot safe alias、fail-closed 边界、无 Start Delivery / Confirm Dropoff / Cancel / diagnostics fetch 扩展，以及 fixture phone-safe 检查。
- `mobile/fixtures/mobile_web_status.fixture.json` 与 `mobile/web/fixtures/status.json` 增加 `robot_diagnostics_task_terminal_completion_mainline_summary` smoke fixture。
- `docs/product/mobile_user_flow.md` 同步说明手机端 terminal mainline 只读展示、字段白名单和证据边界。

### 验证结果

- `python3 mobile/web/test_mobile_web_entrypoint.py`：通过，`Ran 120 tests in 0.851s OK`。
- `python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py`：通过，无输出。
- `node --check mobile/web/app.js`：通过，无输出。
- `rg -n "task_terminal_completion_mainline|robot_diagnostics_task_terminal_completion_mainline_summary|dropoff|cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel|Objective 4|PR #4" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_11-12_task-terminal-completion-mainline`：通过，命中新 panel、fixtures、测试、产品文档和既有安全边界文案。
- `git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_11-12_task-terminal-completion-mainline`：通过，无输出。

### 剩余风险

- 当前只是 `software_proof` / `not_proven` 手机只读展示；没有真实手机设备/browser、真实 Nav2/fixed-route、真实 route/elevator field pass、真实 terminal action material、真实 WAVE ROVER/UART 或 delivery success。
- Start Delivery、Confirm Dropoff、Cancel gating 未扩大；缺少 Robot safe alias 时 panel fail closed，不从 raw artifact、ACK、cursor 或 material status 推导成功。

## Product closeout 段落

### 实际改动

- Product 复核 Robot / Full-Stack worker 写入的 `tech-done.md` 证据，确认本轮只收口 `task_terminal_completion_mainline` 主链路软件证明。
- Product closeout 将继续写入 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，且不提高 Objective 5、Objective 1 或真实 Objective 2/3/4 completion。

### 验收判断

- Robot 证据边界：`task_terminal_completion_mainline` 与 `robot_diagnostics_task_terminal_completion_mainline_summary` 只作为 safe summary，不触发 motion、ACK、cursor、Nav2、HIL 或 terminal completion claim。
- Full-Stack 证据边界：mobile/web “任务终态主链路” panel 只读展示 safe terminal action、safe `evidence_ref`、operator confirmation、missing materials、next required evidence 和 `not_proven`，Start Delivery、Confirm Dropoff、Cancel gating 未扩大。
- Autonomy 只读建议已纳入 Product 收口：必须使用 safe `evidence_ref`，不得把 `fixed_route_status_file`、debug status file、local path、ACK、diagnostics summary、mobile panel、task_record summary 或 material status 写成真实 route evidence / terminal completion。

### 剩余风险

- Objective 5 保持约 68%，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。
- Objective 1 保持约 81%，仍缺 WAVE ROVER/UART/HIL、`feedback_T1001`、真实 `/odom`、`/imu`、`/battery`、PR #5 2D LiDAR / ToF 真实材料。
- Objective 2 / Objective 3 / Objective 4 只记录 `task_terminal_completion_mainline` software-proof 主链路可观察性和 phone-safe visibility；不证明真实 dropoff completion、真实 cancel completion、delivery success、真实 route/elevator field pass、真实 Nav2/fixed-route 或真实手机。
