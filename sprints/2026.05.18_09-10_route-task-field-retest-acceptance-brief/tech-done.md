# Sprint 2026.05.18_09-10 Route Task Field Retest Acceptance Brief - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `software_proof_docker_route_task_field_retest_acceptance_brief_gate` 的三端一致性闭环。目标是让 PR #4 route/elevator field retest 在进入真实现场材料回填前，拥有同一 `route_task_field_retest_acceptance_brief` contract、同一 Robot safe alias 和同一 mobile phone-safe 展示入口。

Autonomy worker：

- 更新 `tests/test_route_task_field_retest_acceptance_brief.py`，新增顶层 unittest wrapper，复用既有 `pc-tools/evidence/test_route_task_field_retest_acceptance_brief.py`。
- 更新 `pc-tools/README.md`，补充 acceptance brief gate 的命令和边界说明。
- 未改变 schema、CLI 或 runtime 行为；PC gate 仍保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Robot worker：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- `status_payload` 新增 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary` safe alias，值等于 sanitized `route_task_field_retest_acceptance_brief_summary`；清理 latest_status 时移除同名输入 alias，避免上游 raw alias 覆盖 sanitized output。
- focused tests 断言 `route_task_field_retest_acceptance_brief`、`route_task_field_retest_acceptance_brief_summary`、`robot_diagnostics_route_task_field_retest_acceptance_brief_summary` 三个 alias 一致。

Full-stack worker：

- 更新 `mobile/web/fixtures/status.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 未改 `mobile/web/app.js`，因为现有读取路径已覆盖 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary`。
- fixture 和 tests 证明 Robot alias 与主 acceptance brief 保持同一 boundary/status/phone-safe whitelist；产品文档记录 Robot alias metadata-only。

Product closeout：

- 创建本文件、`side2side_check.md`、`final.md`。
- 保守更新 `OKR.md` 4.1 当前快照和 `docs/process/okr_progress_log.md`。
- 本轮不修改产品代码、测试代码、硬件配置或 mobile implementation docs 以外的实现文件。

## 2. 验证结果

Autonomy worker 验证：

```text
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_brief.py tests/test_route_task_field_retest_acceptance_brief.py
pass

python3 -m unittest tests.test_route_task_field_retest_acceptance_brief
Ran 5 tests in 0.029s
OK

required rg
pass

scoped git diff --check
pass
```

Robot worker 验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
pass

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 176 tests in 0.356s
OK

required rg
pass

scoped git diff --check
pass
```

Full-stack worker 验证：

```text
node --check mobile/web/app.js
pass

python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 72 tests in 0.368s
OK

required rg
pass

scoped git diff --check
pass
```

Product closeout 需要执行的最终围栏见 `final.md`。

## 3. 偏差

- Full-stack worker 没有修改 `mobile/web/app.js`，偏差可接受：既有 alias 读取路径已经覆盖本轮 Robot alias，worker 用 fixture/test 证明读取与 gating 边界。
- 本轮没有跑 broad build、broad test、Docker/Humble build、ROS graph、Nav2 runtime、hardware smoke、真实手机/browser 或外部云验证；这是计划内围栏，避免把 metadata-only closeout 扩大成不具备材料的实机证明。

## 4. 剩余风险

- 真实 route/elevator field pass 仍缺：真实电梯门状态、真实目标楼层确认、真实人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result 均未出现。
- Objective 1 不推进：没有 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 2D LiDAR / ToF 真实 SKU/source/receipt/install/wiring/calibration/HIL-entry 材料。
- Objective 5 不推进：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover、真实手机/browser external proof。
- 本轮仅证明 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`；必须继续保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
