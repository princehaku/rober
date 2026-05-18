# Sprint 2026.05.19_01-02 Mobile Elevator Action Feedback Display - Tech Done

## Owner B - Robot 只读/轻量接口协同

Run time: 2026-05-19 01:08:51 CST

### 实际改动

- `docs/interfaces/evidence_contracts.md`: 新增 `mobile_elevator_action_feedback` contract，明确 `current_step=elevator:<phase>` 是 phone-safe、只读、metadata-only 的实时展示字段。
- `docs/product/elevator_assisted_delivery.md`: 补齐六个允许的 elevator phase、fail-closed 规则、phone-safe 禁止项和 `software_proof` / `not_proven` 边界。
- 未修改 `operator_gateway.py`、`operator_gateway_diagnostics.py` 或测试代码；现有 `operator_gateway.py` 已从 `TrashCollection.Feedback.current_step` 原样透传 `current_step` 到 status payload。

### 核对证据

- `task_orchestrator.py` 已定义并发布 `elevator:waiting_elevator_open`、`elevator:entering_elevator`、`elevator:requesting_floor_help`、`elevator:waiting_target_floor`、`elevator:exiting_elevator`、`elevator:resume_delivery`。
- `operator_gateway.py` 的 `_on_collect_feedback` 已把 `feedback.current_step` 写入 status payload，不需要新增 summary 或改主链。
- phone-safe 边界保持为：不暴露 raw ROS topic、artifact path、serial/UART、baudrate、WAVE ROVER 参数、credentials、DB/queue URL、raw JSON、完整 artifact 或 checksum。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`: exit 0.
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: `Ran 190 tests in 0.435s` / `OK`.
- `rg -n "current_step=elevator:<phase>|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" docs/interfaces/evidence_contracts.md docs/product/elevator_assisted_delivery.md onboard/src/ros2_trashbot_behavior sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/tech-done.md`: exit 0; key hits include evidence contract lines for `current_step=elevator:<phase>`, product doc lines for `source=software_proof` / `not_proven` / `delivery_success=false` / `primary_actions_enabled=false`, and this Owner B section.
- `git diff --check -- docs/interfaces/evidence_contracts.md docs/product/elevator_assisted_delivery.md onboard/src/ros2_trashbot_behavior sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/tech-done.md`: exit 0.

### 剩余风险

- 本轮只证明现有 Robot action feedback 字段和文档 contract 可被手机端只读消费；不证明真实电梯、真实手机设备/浏览器、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、dropoff/cancel 完成或 delivery success。
- `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 必须由 Full-Stack 展示层继续保留；Start Delivery、Confirm Dropoff、Cancel 不得由该展示解锁。

## Owner A - Full-Stack 手机实时阶段展示

Run time: 2026-05-19 01:14:33 CST

### 实际改动

- `mobile/web/app.js`: 新增 `current_step=elevator:<phase>` 白名单解析、phone-safe action message 过滤、只读“电梯实时阶段”panel，并接入 status / offline / diagnostics refresh 渲染链路；缺失、非 `elevator:` 前缀或未知 phase 均 fail closed。
- `mobile/web/styles.css`: 将 `elevator-realtime-stage-panel` / `elevator-realtime-stage-grid` 纳入现有 card/grid 样式。
- `mobile/web/test_mobile_web_entrypoint.py`: 增加实时阶段白名单、phone-safe 过滤、fixture phase、主按钮 gating 不变的断言。
- `mobile/web/fixtures/status.json`: 增加 `phone_action_feedback.current_step=elevator:waiting_elevator_open`，并保留 `delivery_success=false`、`primary_actions_enabled=false`。
- `mobile/fixtures/mobile_web_status.fixture.json`: 在现有 `phone_action_feedback` 中补充 `current_step=elevator:requesting_floor_help` 和 boundary flags，避免重复 JSON key。
- `docs/product/mobile_user_flow.md`: 记录“电梯实时阶段”只读展示、输入来源、phase 白名单、fail-closed 规则和 `software_proof` / `not_proven` 边界。

### 验证结果

- `python3 mobile/web/test_mobile_web_entrypoint.py`: `Ran 100 tests in 0.612s` / `OK`。
- `python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py`: exit 0。
- `node --check mobile/web/app.js`: exit 0。
- `rg -n "current_step=elevator:<phase>|Start Delivery|Confirm Dropoff|Cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/tech-done.md`: exit 0；命中 app/doc/fixture/sprint 里的实时阶段、button gating 和边界字段。
- `git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/tech-done.md`: exit 0。

### 失败定位

- 首轮 `python3 mobile/web/test_mobile_web_entrypoint.py` 失败：`mobile/fixtures/mobile_web_status.fixture.json` 已存在后置 `phone_action_feedback`，导致新增在顶部的同名 key 被 JSON parser 覆盖。已改为合并到现有 `phone_action_feedback`，并移除重复 key 后重跑通过。

### 剩余风险

- 本轮只证明 `mobile/web` 可消费 fixture/status 中的 phone-safe `current_step=elevator:<phase>` 并只读展示；不证明真实手机、真实电梯、真实 Nav2/fixed-route、dropoff/cancel completion、HIL 或 delivery success。
- Start Delivery、Confirm Dropoff、Cancel 仍由既有 `command_safety`、legacy permission、terminal confirmation 和 ACK gates 控制；新 panel 不提供控制入口，也不提升 `primary_actions_enabled=false`。

## Product Closeout - OKR Owner

Run time: 2026-05-19 01:17:04 CST

### 用户价值和产品北极星

本轮把 `current_step=elevator:<phase>` 从 Robot action feedback 字段推进为手机用户可读的只读“电梯实时阶段”展示。用户价值是降低普通用户对电梯阶段的误判和等待焦虑；产品北极星仍是手机可解释的低成本 trash delivery，而不是本地 fixture 或文档 closeout。

### OKR 映射和 KR 拆解

- Objective 2：PR #4 支撑电梯主链路，本轮让电梯阶段 feedback 可以被手机端只读消费，保守计为 software-proof 可观测性提升；不证明真实 route/elevator field pass。
- Objective 4：手机端展示等待电梯开门、进入电梯、请求帮忙按楼层、等待目标楼层、驶出电梯、继续送往垃圾站等阶段；Start Delivery、Confirm Dropoff、Cancel gating 不变。
- Objective 1：保持约 81%，没有 WAVE ROVER/UART/HIL 或 `feedback_T1001.log` 等真实硬件证据。
- Objective 5：保持约 68%，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover external proof。

### 验收和风险边界

Product closeout 已创建 `side2side_check.md` 和 `final.md`，更新 `OKR.md` 4.1、最高优先级、风险边界，并在 `docs/process/okr_progress_log.md` 追加本轮条目。PR #5 的 2D LiDAR / ToF、vendor source/materials、采购/安装/接线/电源/标定/HIL-entry 仍未解决。

本轮保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。不证明真实手机、真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、O5 external proof、dropoff/cancel completion 或 delivery success。
