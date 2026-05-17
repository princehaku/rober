# Sprint 2026.05.17_09-10 Route Task Field Retest Callback Intake - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `route_task_field_retest_callback_intake`，把上一轮 `route_task_field_retest_evidence_dispatch` 的 owner/file/backfill/callback checklist 推进为 PC / Robot / mobile 三端可消费的现场回执入口。统一证据边界保持：

- `software_proof_docker_route_task_field_retest_callback_intake_gate`
- `trashbot.route_task_field_retest_callback_intake.v1`
- `trashbot.route_task_field_retest_callback_intake_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

### Task A - Autonomy

实际改动文件：

- `pc-tools/evidence/route_task_field_retest_callback_intake.py`
- `pc-tools/evidence/test_route_task_field_retest_callback_intake.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

交付内容：

- 新增 dependency-free PC callback intake CLI。
- 支持消费 `route_task_field_retest_evidence_dispatch` artifact / summary / wrapper / nested JSON。
- 接收 sanitized callback JSON，输出 callback intake artifact / summary。
- 固化推荐文件名收到状态、same-`evidence_ref` 检查、缺项列表、下一次回填动作、owner handoff、callback checklist result 和 not-proven boundary。
- 修复首轮问题：缺材料时不能采信 callback 的 "send to result intake"，已强制转为 `collect_missing_materials_then_rerun_result_intake`。

### Task B - Robot

实际改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

交付内容：

- 新增 `route_task_field_retest_callback_intake` / `_summary` diagnostics metadata-only consumer。
- 支持 callback intake artifact、summary、Robot-compatible summary 和 nested diagnostics summary。
- 只暴露 safe summary、safe `evidence_ref`、intake status、received/missing summary、same-evidence-ref match result、next backfill action、callback checklist result、boundary、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。
- 保持 collect、dropoff、cancel、ACK、Nav2、HIL、cursor、diagnostics fetch 和 delivery success 语义不变。
- 修复首轮问题：env summary wrapper 误读 `robot_compatible_summary` 导致 `safe_evidence_ref` 丢失，已改为正确读取安全摘要。

### Task C - Full-stack

实际改动文件：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

交付内容：

- 新增 mobile/web 只读“现场回执入口” panel。
- 兼容 callback intake artifact / summary / Robot diagnostics compatible summary。
- 展示 intake status、safe `evidence_ref`、received filenames、missing materials、same-evidence-ref match result、next backfill action、callback checklist result、boundary、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 保持不变。
- Copy/export 继续 whitelist-only，不展示 raw artifact、raw JSON、raw path、credential、ROS topic、serial/UART、WAVE ROVER、DB/queue URL、OSS AK/SK、checksums、complete artifact 或 raw robot response。

### Task D - Product Closeout

实际改动文件：

- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/tech-done.md`
- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/side2side_check.md`
- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 2. 验证结果

Task A Autonomy 已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_callback_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_callback_intake.py
Ran 5 tests in 0.066s
OK
python3 pc-tools/evidence/route_task_field_retest_callback_intake.py --help
required rg: 243 matches
scoped git diff --check: passed
```

Task B Robot 已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 140 tests in 0.208s
OK
required rg: passed
scoped git diff --check: passed
```

Task C Full-stack 已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 36 tests in 0.092s
OK
node --check mobile/web/app.js
required rg: passed
scoped git diff --check: passed
```

Task D Product closeout 已通过：

```text
rg -n "route_task_field_retest_callback_intake|software_proof_docker_route_task_field_retest_callback_intake_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_09-10_route-task-field-retest-callback-intake OKR.md docs/process/okr_progress_log.md
exit 0; matched sprint closeout, OKR.md, and docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/tech-done.md sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/side2side_check.md sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/final.md OKR.md docs/process/okr_progress_log.md
exit 0; no whitespace errors
git diff --name-only
OKR.md
docs/interfaces/ros_contracts.md
docs/navigation/fixed_route_workflow.md
docs/process/okr_progress_log.md
docs/product/mobile_user_flow.md
mobile/web/app.js
mobile/web/fixtures/status.json
mobile/web/styles.css
mobile/web/test_mobile_web_entrypoint.py
onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
pc-tools/README.md
```

`git diff --name-only` 只列出 tracked 改动，未包含未跟踪的新文件；`git status --short` 显示新增的 `pc-tools/evidence/route_task_field_retest_callback_intake.py`、`pc-tools/evidence/test_route_task_field_retest_callback_intake.py` 和本 sprint 目录仍未跟踪。Product-owned tracked 改动仅为 `OKR.md` 与 `docs/process/okr_progress_log.md`，未发现额外 Product-owned tracked 文件。

## 3. 偏差和失败定位

- Task A 首轮偏差：缺材料时 callback 不应进入 result intake。处理：强制下一步动作改为 `collect_missing_materials_then_rerun_result_intake`，避免把不完整材料误写成结果回填。
- Task B 首轮偏差：env summary wrapper 误读 `robot_compatible_summary`，导致 `safe_evidence_ref` 丢失。处理：修复 summary 读取路径并用 diagnostics unittest 复验。
- Task C 无需产品侧追加失败定位；现有验证证明只读 panel 与主操作 gating 隔离。

## 4. 剩余风险

- 本轮仍是 Docker-only software proof，不是真实 route/elevator field pass。
- 仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 和同一 `evidence_ref` 的上车实机复账。
- 仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实浏览器/设备验收。
- 仍缺 Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover。
- PR #5 2D LiDAR / ToF material proof 仍缺真实 SKU/source、receipt、采购、安装、接线、电源、标定、HIL-entry 和 field evidence。
