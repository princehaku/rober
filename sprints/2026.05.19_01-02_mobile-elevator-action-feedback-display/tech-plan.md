# Sprint 2026.05.19_01-02 Mobile Elevator Action Feedback Display - Tech Plan

## 计划状态

本文件完成后进入实现阶段；本轮已按用户“用 team 继续完成 OKR、功能往前走”的要求派发 Full-Stack 与 Robot worker，并由 Product closeout 收口。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 68%。本 sprint 不针对 Objective 5，因为当前 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他 external proof；继续做本地 O5 metadata 不会真实推进 completion。

次低 Objective 1 约 81%。本 sprint 也不针对 Objective 1，因为当前没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，且 PR #5 相关 2D LiDAR / ToF 仍缺真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

本 sprint 选择 Objective 4 / Objective 2：PR #4 要求 elevator-assisted delivery 进入主链，上轮 Robot 已发布 `TrashCollection.Feedback.current_step=elevator:<phase>`；最新可行动缺口是手机端只读消费和展示该实时阶段。

## 架构和接口边界

输入来源：

- 首选：`/api/status` 或状态 payload 中的 action feedback 字段，包含 `current_step=elevator:<phase>`。
- 兼容：`phone_readiness`、`/api/diagnostics`、`diagnostics.summary`、`diagnostics.diagnostics_summary` 或 nested diagnostics summaries 中由 Robot/operator gateway 提供的 phone-safe action feedback summary。

输出行为：

- `mobile/web` 渲染只读“电梯实时阶段”展示。
- 展示只解释 `elevator:<phase>`；非 elevator 前缀、未知 phase 或缺失字段都 fail closed。
- 不向 backend 发送新命令，不调用 Start Delivery、Confirm Dropoff、Cancel，不改变现有 gating。

阶段映射：

| `current_step` | 手机标题 | 用户说明 |
| --- | --- | --- |
| `elevator:waiting_elevator_open` | 等待电梯开门 | 小车已到电梯相关阶段，正在等待可进入条件。 |
| `elevator:entering_elevator` | 进入电梯 | 小车正在执行进入电梯阶段，保持通道安全。 |
| `elevator:requesting_floor_help` | 请求帮忙按楼层 | 小车正在请求旁人协助按目标楼层。 |
| `elevator:waiting_target_floor` | 等待目标楼层 | 小车正在等待目标楼层证据，不代表已到达。 |
| `elevator:exiting_elevator` | 驶出电梯 | 小车正在目标楼层开门后驶出。 |
| `elevator:resume_delivery` | 继续送往垃圾站 | 电梯段结束后继续送达流程；仍不代表投放完成。 |

必须保留的边界字段和文案：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 文件范围和 Owner 分工

### Owner A：Full-Stack 主责

允许修改：

- `mobile/web/app.js`
- `mobile/web/index.html`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `docs/product/mobile_user_flow.md`

任务：

1. 在 existing status rendering 中加入 `current_step=elevator:<phase>` 提取函数。
2. 增加 phase 到中文标题/说明/下一步提示的白名单映射。
3. 渲染只读实时阶段区域，缺失或未知时 fail closed。
4. 增加 fixture，覆盖至少 `elevator:waiting_elevator_open` 和 `elevator:requesting_floor_help`。
5. 增加/更新测试，断言 Start Delivery、Confirm Dropoff、Cancel 在 `primary_actions_enabled=false` 时仍不可用。
6. 更新 `docs/product/mobile_user_flow.md`，说明该展示只属于 `software_proof` / `not_proven`。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "current_step=elevator:<phase>|Start Delivery|Confirm Dropoff|Cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web mobile/fixtures docs/product/mobile_user_flow.md
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md
```

### Owner B：Robot 只读/轻量接口协同

允许修改：

- `docs/interfaces/evidence_contracts.md`
- `docs/product/elevator_assisted_delivery.md`
- 如确有必要且只为暴露现有字段：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- 如确有必要且只为暴露现有字段：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- 如确有必要且只为接口测试：`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`

任务：

1. 只读核对 `TrashCollection.Feedback.current_step=elevator:<phase>` 当前由上轮 Robot action feedback 发布，不新增 robot 状态。
2. 确认 phone-safe message 不包含 raw ROS topic、artifact path、serial/UART、baudrate、WAVE ROVER 参数、credentials、DB/queue URL、raw JSON、完整 artifact 或 checksum。
3. 如发现 mobile 无可消费入口，只补最小兼容 summary 或接口文档；不得重写 task_orchestrator 主链，不得改变 status/result 语义。
4. 保持 `delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "current_step=elevator:<phase>|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" docs/interfaces/evidence_contracts.md docs/product/elevator_assisted_delivery.md onboard/src/ros2_trashbot_behavior
git diff --check -- docs/interfaces/evidence_contracts.md docs/product/elevator_assisted_delivery.md onboard/src/ros2_trashbot_behavior
```

### Owner C：Product Closeout

允许修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/tech-done.md`
- `sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/side2side_check.md`
- `sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/final.md`

任务：

1. 汇总 Full-Stack 和 Robot 的验证证据。
2. 更新 sprint 收口文档，明确本轮是否只计 Objective 4 / Objective 2 的 software proof。
3. 如实现落地且证据充分，更新 `OKR.md` 4.1 和 `docs/process/okr_progress_log.md`；不得把展示写成真实手机、真实电梯、真实 route/elevator field pass、HIL 或 delivery success。
4. 核对 PR #4 / PR #5 证据边界：PR #4 仍缺真实现场材料，PR #5 仍缺真实 2D LiDAR / ToF 材料。

验收命令：

```bash
test -f sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/tech-done.md && test -f sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/side2side_check.md && test -f sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/final.md
rg -n "Objective 5|Objective 1|Objective 2|Objective 4|PR #4|PR #5|current_step=elevator:<phase>|Start Delivery|Confirm Dropoff|Cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display
```

## 并行启动计划

实现阶段应并行启动 2 个 worker：

- `full-stack-software-engineer` 负责手机展示、fixture、测试和 docs/product。
- `robot-software-engineer` 负责只读接口事实核对和必要的最小接口文档或 summary 兼容。

Product closeout 在两个 Engineer 返回后执行，不与实现并行写收口，避免提前宣称完成。

## 风险控制

- 如果 Full-Stack 找不到 `current_step=elevator:<phase>` 输入，展示必须 fail closed，并把阻塞交回 Robot 核对；不得从旧 elevator checklist 推断实时阶段。
- 如果 Robot 需要改接口，必须保持兼容输入，只添加 phone-safe summary，不改变 action result/status 和 delivery result。
- 所有新代码技术注释必须为中文且比例超过 20%；若没有新增复杂代码，也不能为了比例添加空洞注释。
- 本轮实现后的证据仍是 Docker/local `software_proof`，保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 本计划文档验收命令

```bash
test -f sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/pre_start.md && test -f sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/prd.md && test -f sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/tech-plan.md
rg -n "sprint_type: epic|Objective 5|Objective 1|Objective 2|Objective 4|PR #4|PR #5|current_step=elevator:<phase>|Start Delivery|Confirm Dropoff|Cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display
git diff --check -- sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display
```
