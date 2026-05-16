# Sprint 2026.05.16_20-21 Route Task Field Retest Execution Pack - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `route_task_field_retest_execution_pack`，把上一轮 `route_task_terminal_review_decision` 的复核决策推进为下一次真实现场复测可执行的材料包。统一证据边界保持为 `software_proof_docker_route_task_field_retest_execution_pack_gate`，统一状态保持为 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Task A Autonomy Algorithm Engineer：

- 新增 `pc-tools/evidence/route_task_field_retest_execution_pack.py`。
- 新增 `pc-tools/evidence/test_route_task_field_retest_execution_pack.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/navigation/fixed_route_workflow.md`。
- 实现 dependency-free PC gate，支持 `route_task_terminal_review_decision` artifact / summary / wrapper / nested JSON，输出 `trashbot.route_task_field_retest_execution_pack.v1` 与 `trashbot.route_task_field_retest_execution_pack_summary.v1`。
- Pack 包含 safe `evidence_ref`、same ref 要求、required field materials、rerun commands、operator handoff、field retest checklist；elevator source 追加 door state、target floor confirmation、human assistance note。
- 对缺失、坏 JSON、unsupported schema、unsafe copy、missing ref、same-ref false、success/control claim 均 fail closed。

Task B Robot Platform Engineer：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 实现 diagnostics metadata-only consumer，支持 explicit ref、env、top-level、`phone_readiness`、`diagnostics.summary`、`diagnostics.diagnostics_summary`。
- 对缺失、unsupported、unsafe、missing ref、same-ref mismatch、success wording、primary action enabled 均 fail closed。
- 不触发 collect、dropoff、cancel、ACK、cursor、Nav2、HIL、delivery success。

Task C User Touchpoint Full-Stack Engineer：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“现场复测执行包” panel，消费 execution pack / summary / diagnostics safe summary。
- 展示材料、重跑命令、operator handoff、checklist；copy/export whitelist-only。
- Start / Confirm Dropoff / Cancel gating 未改变。

Task D Product Manager / OKR Owner：

- 新增本文件。
- 新增 `side2side_check.md`。
- 新增 `final.md`。
- 更新 `OKR.md`。
- 更新 `docs/process/okr_progress_log.md`。

## 2. 验证结果

Task A 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_execution_pack.py
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_execution_pack.py
Ran 10 tests in 0.022s
OK

python3 pc-tools/evidence/route_task_field_retest_execution_pack.py --help
passed

required rg boundary check
passed

git diff --check -- pc-tools/evidence/route_task_field_retest_execution_pack.py pc-tools/evidence/test_route_task_field_retest_execution_pack.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
passed
```

Task B 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
passed

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 112 tests in 0.125s
OK

required rg boundary check
passed

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
passed
```

Task B 首轮 unittest 发现 summary wrapper 未读取自身 `safe_evidence_ref`，Robot worker 已修复并复验通过。

Task C 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 14 tests in 0.028s
OK

node --check mobile/web/app.js
passed

required rg boundary check
passed

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
passed
```

Task D closeout 需运行的最终验收命令记录在 `final.md`。

## 3. OKR 进度判断

本轮只代表 `software_proof_docker_route_task_field_retest_execution_pack_gate`。

- Objective 1 保持约 75%。本轮不涉及真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或真实传感器材料。
- Objective 2 从约 80% 保守上调到约 81%。理由是 field retest execution pack 把 task terminal review decision 转成下一次现场复测的 same `evidence_ref` 材料、重跑命令、operator handoff 和 checklist。
- Objective 3 从约 80% 保守上调到约 81%。理由是真实 Nav2/fixed-route runtime log、route completion signal、task record 和 rerun commands 被纳入可复跑、可回填的 execution pack。
- Objective 4 从约 89% 保守上调到约 90%。理由是 mobile/web 能只读解释现场复测执行包，普通用户和现场支持能理解下一步材料要求，且 primary actions 未放开。
- Objective 5 保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或外部 O5 材料。

## 4. 偏差与边界

本轮遵守 `AGENTS.md` 同一 blocker 最多消费 2 轮红线。最近两轮 `2026.05.16_17-18_hardware-baseline-source-alignment` 与 `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 已连续消费 PR #5 硬件/source/config blocker；因此本轮未启动第三个硬件 blocker wrapper，而是切换到 Objective 2 / Objective 3 的 route-task field retest execution pack。

PR #4 要求 elevator-assisted delivery 成为主线必须能力。本轮在 execution pack 中保留 elevator source 的 door state、target floor confirmation、human assistance note 材料要求，但不宣称真实电梯通过。

## 5. 剩余风险

仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、真实楼层确认、人工协助记录、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof。

本轮未运行真实硬件、真实电梯、真实手机设备、真实公网云、真实 OSS/CDN、production DB/queue 或 worker/migration 验证；这些缺口不能被本地 Docker software proof 替代。
