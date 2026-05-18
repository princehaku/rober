# Sprint 2026.05.19_02-03 Elevator Feedback Task Record Trace - Tech Done

## sprint_type: epic

Run time: 2026-05-19 02:11 Asia/Shanghai

## 用户价值和产品北极星

本轮把电梯 assisted delivery 从“手机实时看到阶段”推进到“任务结束后可按同一 `evidence_ref` 复盘阶段”。现场 owner 可以对齐 task_record、operator diagnostics 和 mobile/web post-run panel，判断等待开门、进入电梯、请求按楼层、等待目标楼层、驶出电梯、恢复送达这些阶段是否进入了软件证据链。

产品北极星仍是普通手机用户可解释、可恢复、可复盘地完成低成本 trash delivery。本轮只交付 `software_proof` 可复盘性，不声明真实电梯、真实 Nav2/fixed-route、真实手机、WAVE ROVER/UART/HIL、Objective 5 external proof 或 delivery success。

## OKR 映射

- Objective 2：主要推进 KR5 / KR6 / KR7 的可复盘链路。`elevator_action_feedback_trace` 让 task_record 持久化实时 elevator phase trace，diagnostics 以安全摘要暴露给 operator/mobile。
- Objective 4：次要推进手机端 post-run 复盘体验。mobile/web 增加只读 panel，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Objective 1：不推进。无 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 PR #5 2D LiDAR / ToF 真实材料。
- Objective 3：不推进。无真实路线采集、Nav2/fixed-route runtime、route completion signal 或现场 task record。
- Objective 5：不推进。无真实 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或 external proof。

## KR 拆解或更新

1. Objective 2 KR5：task_record 增加 post-run elevator phase trace，保留阶段、message、percent、event、boundary flags 和 safe evidence reference。
2. Objective 2 KR7：operator gateway / diagnostics 暴露 `robot_diagnostics_elevator_action_feedback_trace_summary`，用于手机和现场 owner 只读复盘。
3. Objective 4 KR6 / KR7：mobile/web 展示 `elevator_action_feedback_trace` / diagnostics summary，文案保持 phone-safe、中文优先、只读。
4. Objective 1 / PR #5：2D LiDAR / ToF SKU/source、receipt、采购、安装、接线、电源、标定、HIL-entry 和 field evidence 继续作为独立缺口。

## 本轮核心抓手

核心抓手是 post-run trace 对齐：Robot 把实时 `current_step=elevator:<phase>` 沉淀进 task_record，diagnostics 输出 `robot_diagnostics_elevator_action_feedback_trace_summary`，mobile/web 只读展示上一轮电梯动作反馈追踪。三者必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 实际改动

Robot worker 完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `docs/interfaces/evidence_contracts.md`
- `docs/product/elevator_assisted_delivery.md`

Robot 实现内容：新增 `elevator_action_feedback_trace`，让 task_record 持久化实时 elevator phase trace；operator gateway 带入 `last_task/status`；diagnostics 暴露 `robot_diagnostics_elevator_action_feedback_trace_summary`。

Full-Stack worker 完成：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

Full-Stack 实现内容：新增只读 post-run `elevator_action_feedback_trace` / `robot_diagnostics_elevator_action_feedback_trace_summary` panel；不改变 Start Delivery、Confirm Dropoff、Cancel gating。

Product closeout 完成：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.19_02-03_elevator-feedback-task-record-trace/tech-done.md`
- `sprints/2026.05.19_02-03_elevator-feedback-task-record-trace/side2side_check.md`
- `sprints/2026.05.19_02-03_elevator-feedback-task-record-trace/final.md`

## Accepted deviation

accepted deviation：planning 文档草案使用 `elevator_feedback_task_record_trace` 命名；实际实现采用与代码更一致的 `elevator_action_feedback_trace`，diagnostics alias 采用 `robot_diagnostics_elevator_action_feedback_trace_summary`。该偏差未放宽产品边界，不作为失败。

## 验证结果

Robot worker 报告：

```text
python3 -m py_compile ... passed
focused unittest: Ran 207 tests in 0.452s OK
required rg passed
scoped git diff --check passed
```

第一轮 unittest 因 `_safe_float` helper 不存在失败；Robot worker 定位后修复为 `_elevator_trace_float`，并重跑通过。

Full-Stack worker 报告：

```text
node --check mobile/web/app.js passed
python3 mobile/web/test_mobile_web_entrypoint.py -> Ran 102 tests ... OK
py_compile passed
required rg passed
scoped git diff --check passed
```

Product closeout 运行的验收命令记录在 `final.md`。

## 优先级和验收口径

P0 已满足：

- task_record / diagnostics / mobile 可按 `elevator_action_feedback_trace` 复盘电梯阶段。
- `robot_diagnostics_elevator_action_feedback_trace_summary` 作为 phone-safe 只读摘要存在。
- `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 边界保留。
- mobile/web 不因 trace summary 启用 Start Delivery、Confirm Dropoff、Cancel。

不验收：

- 真实电梯、真实门状态、真实楼层确认、真实人工协助记录。
- 真实 Nav2/fixed-route runtime、真实 route completion signal、真实 dropoff/cancel completion、delivery result 或 delivery success。
- WAVE ROVER/UART/HIL、PR #5 2D LiDAR / ToF 材料、Objective 5 external proof。

## 风险、阻塞和需要补齐的证据链

- PR #4 真实现场材料仍缺：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、真实 task_record/completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 硬件材料仍缺：2D LiDAR / ToF SKU/vendor/source、receipt/procurement、installation/wiring/power/calibration、HIL-entry 和 field evidence。
- O5 仍缺真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 和 real external proof。
- 本轮 trace 是 repo-local software proof；如果后续文案把 trace 写成 field pass、HIL、真实手机通过或 delivery success，需要立即回滚该表述。
