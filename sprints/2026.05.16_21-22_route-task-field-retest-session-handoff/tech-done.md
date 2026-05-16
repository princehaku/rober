# Sprint 2026.05.16_21-22 Route Task Field Retest Session Handoff - Tech Done

sprint_type: epic

## 1. 收口状态

本轮 Task A / B / C / D 已完成。交付物把上一轮 `route_task_field_retest_execution_pack` 推进为可交接的 `route_task_field_retest_session_handoff` artifact / summary、Robot diagnostics metadata-only consumer、mobile/web 只读 panel，以及 Product closeout 留档。

统一证据边界保持：

- `software_proof_docker_route_task_field_retest_session_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮只代表 Docker/local software proof，不是真实 Nav2/fixed-route field pass，不是真实电梯 assisted delivery，不是真实 WAVE ROVER/UART/HIL，不是真实手机/browser，也不是 Objective 5 external proof。

## 2. Task A Autonomy 实际改动

改动文件：

- `pc-tools/evidence/route_task_field_retest_session_handoff.py`
- `pc-tools/evidence/test_route_task_field_retest_session_handoff.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实际结果：

- 新增 PC-side gate，支持 `route_task_field_retest_execution_pack` artifact、summary、wrapper 和 nested JSON 输入。
- 输出 `trashbot.route_task_field_retest_session_handoff.v1` 与 `trashbot.route_task_field_retest_session_handoff_summary.v1`。
- 固定 `software_proof_docker_route_task_field_retest_session_handoff_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 交接内容包含 operator handoff、session owner、八类现场回填材料、相对 material placeholders、rerun commands、field callback checklist、safe copy 和 fail-closed summary。
- 对 missing required materials、placeholder-only materials、证据号不一致、unsafe copy、success/control claim、raw path、credential、ROS topic、UART、WAVE ROVER detail 均 fail closed。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_session_handoff.py
exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_session_handoff.py
Ran 9 tests in 0.029s
OK

python3 pc-tools/evidence/route_task_field_retest_session_handoff.py --help
exit 0

required rg
exit 0

git diff --check -- pc-tools/evidence/route_task_field_retest_session_handoff.py pc-tools/evidence/test_route_task_field_retest_session_handoff.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
exit 0
```

## 3. Task B Robot 实际改动

改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实际结果：

- 新增 `route_task_field_retest_session_handoff` / `_summary` diagnostics metadata-only consumer。
- 支持 explicit ref、`TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF` / `_SUMMARY`、top-level status、nested diagnostics summary。
- schema/boundary、`same_evidence_ref_required` JSON boolean true、false delivery/primary actions、missing/mismatch evidence ref、success/control/raw/credential/path/checksum/traceback 均 fail closed。
- payload 同时输出 alias，保持 diagnostics 与 mobile/web 兼容。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 114 tests in 0.150s
OK

required rg
exit 0

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
exit 0
```

## 4. Task C Full-stack 实际改动

改动文件：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实际结果：

- 新增独立只读“路线任务现场复测交接” panel。
- 兼容 status、phone_readiness、diagnostics、nested diagnostics summary、status.diagnostics.summary。
- 展示 handoff status、session owner、必需现场材料、重跑摘要、下一步、safe copy 状态和边界。
- copy/export 只使用后端显式 `safe_copy`；缺失时显示 `blocked copy unavailable` 并禁用复制/导出。
- Start Delivery / Confirm Dropoff / Cancel 授权逻辑未改。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 16 tests
OK

node --check mobile/web/app.js
exit 0

required rg
exit 0

git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
exit 0
```

## 5. Task D Product closeout 实际改动

改动文件：

- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/tech-done.md`
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/side2side_check.md`
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Product 结论：

- Objective 5 仍是数值最低，约 66%，但当前 Docker-only 主机无法提供公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等真实外部材料，因此 Objective 5 不上调。
- Objective 2 约 81% -> 约 82%，只因 session handoff 让真实 task record、route completion signal、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 的现场回填路径更清楚。
- Objective 3 约 81% -> 约 82%，只因 fixed-route/Nav2 runtime log、route completion signal、task record 和 rerun commands 已进入可交接 session handoff。
- Objective 4 约 90% -> 约 91%，只因 mobile/web phone-safe 只读 panel 能解释现场复测交接和 blocked copy；不代表真实手机/browser。
- Objective 1 保持约 75%，本轮未新增真实 WAVE ROVER/UART/HIL 或传感器材料。

## 6. 失败定位

本轮 closeout 未发现新的 Task D 文档验证失败。A/B/C worker 报告的围栏均为 exit 0；Task D 仅基于这些证据同步 sprint、OKR 和过程日志，没有提交或推送。

## 7. 剩余风险

- 仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、真实路线采集和同一 `evidence_ref` 的上车实机复账。
- 仍缺真实电梯门状态、目标楼层确认、人工协助记录、真实喇叭/TTS、真实 dropoff completion、真实 cancel completion 和 delivery result。
- 仍缺真实 WAVE ROVER/UART/HIL、真实串口日志、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本。
- 仍缺真实手机/browser、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- PR #4 elevator-assisted delivery 主线仍需要现场材料闭环；PR #5 硬件/source/config blocker 不应被第三轮本地 wrapper 重复消费。
