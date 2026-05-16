# Sprint 2026.05.17_06-07 Route Task Field Retest Evidence Dispatch - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

本轮把上一轮 `route_task_field_retest_acceptance_brief` 继续推进成“现场证据包派发”层：现场支持不再只知道需要哪些材料，而是能按 owner、推荐文件名、回填顺序和 callback checklist 去收集 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result、Nav2/fixed-route runtime log、route completion signal 和 task record。

产品北极星保持不变：让普通手机用户交付垃圾后，小车能沿固定路线/电梯 assisted delivery 完成可复盘的低成本送垃圾闭环。本轮仍是 Docker-only software proof，不是真实送达。

## 2. OKR 映射与 KR 拆解

- Objective 2：现场证据从 acceptance brief 推进到 owner/file/backfill/callback dispatch，支撑送垃圾任务和电梯 assisted delivery 的真实材料补齐路径。
- Objective 3：Nav2/fixed-route runtime log、route completion signal、task record 的同一 `evidence_ref` 回填顺序、推荐文件名和 callback checklist 已固化。
- Objective 4：mobile/web 新增 phone-safe 只读 panel，帮助现场支持读取派发状态，但 O4 已接近 99%，且本轮没有真实手机/browser 或 production app proof。
- Objective 5：本轮不是 Objective 5 external proof；没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据。
- Objective 1：本轮没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或 PR #5 所需 2D LiDAR / ToF 真实材料。

## 3. 本轮核心抓手

核心抓手是 `trashbot.route_task_field_retest_evidence_dispatch.v1` / `trashbot.route_task_field_retest_evidence_dispatch_summary.v1` 与统一边界 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`。三端都只消费 safe summary，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. Worker 实际改动

### Task A - Autonomy

实际改动：

- 新增 `pc-tools/evidence/route_task_field_retest_evidence_dispatch.py`
- 新增 `pc-tools/evidence/test_route_task_field_retest_evidence_dispatch.py`
- 更新 `pc-tools/README.md`
- 更新 `docs/navigation/fixed_route_workflow.md`

交付内容：

- 新增 `trashbot.route_task_field_retest_evidence_dispatch.v1` artifact 和 `trashbot.route_task_field_retest_evidence_dispatch_summary.v1` summary。
- Summary 包含 dispatch status、safe `evidence_ref`、material owners、recommended filenames、same-evidence-ref rule、backfill order、callback checklist、fail-closed rerun notes、required evidence packet 和边界。
- Required evidence packet 覆盖 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result、Nav2/fixed-route runtime log、route completion signal 和 task record。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_evidence_dispatch.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_evidence_dispatch.py
Ran 5 tests in 0.067s OK

python3 pc-tools/evidence/route_task_field_retest_evidence_dispatch.py --help
pass

rg coverage
pass

git diff --check scoped to Task A files
pass
```

失败定位：无未关闭失败。

剩余风险：software proof only，不是真实 field pass / Nav2 / elevator / delivery / HIL / phone / Objective 5 proof。

### Task B - Robot

实际改动：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- 更新 `docs/interfaces/ros_contracts.md`

交付内容：

- 新增 `route_task_field_retest_evidence_dispatch` / `_summary` metadata-only diagnostics consumer。
- 支持 artifact、summary、wrapper 和 nested summary。
- fail closed 处理 missing、unsupported schema/boundary、unsafe copy、success phrasing、`delivery_success=true` 和 `primary_actions_enabled=true`。
- 不改变 collect、dropoff、cancel、ACK、Nav2、HIL、cursor 或 delivery success 语义。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 132 tests in 0.186s OK

rg coverage
pass

git diff --check scoped to Task B files
pass
```

失败定位：无未关闭失败。

剩余风险：metadata-only diagnostics，不是真实 Nav2、HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。

### Task C - Full-stack

实际改动：

- 更新 `mobile/web/app.js`
- 更新 `mobile/web/styles.css`
- 更新 `mobile/web/fixtures/status.json`
- 更新 `mobile/web/test_mobile_web_entrypoint.py`
- 更新 `docs/product/mobile_user_flow.md`

交付内容：

- 新增只读“现场证据包派发” panel。
- 兼容 artifact、summary 和 Robot diagnostics compatible summary。
- copy/export whitelist-only；Start Delivery / Confirm Dropoff / Cancel gating 不变。
- 首轮 fixture forbidden `raw path` wording 已修复。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 34 tests in 0.081s OK

node --check mobile/web/app.js
pass

rg coverage
pass

git diff --check scoped to Task C files
pass
```

失败定位：首轮 fixture forbidden `raw path` wording 已由 Task C worker 修复并复验通过。

剩余风险：只读 phone-safe 支援增量，不是真实 iPhone/Android、真实 browser、production app、route/elevator field pass 或 Objective 5 external proof。

## 5. Product Closeout 实际改动

实际改动：

- 新增本文件。
- 新增 `side2side_check.md`。
- 新增 `final.md`。
- 更新 `OKR.md` 当前进度快照。
- 更新 `docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

验收口径：

- A/B/C worker 结果必须被完整收口到 sprint closeout。
- `OKR.md` 只保守上调 Objective 2 / Objective 3，Objective 4 / Objective 1 / Objective 5 不上调。
- 所有 closeout 文档必须保留 Docker-only、software proof、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 边界。
- 必须明确本轮不是 PR #5 硬件材料真实完成、不是 Objective 5 external proof，也不是真实 route/elevator field pass。

责任 Engineer：

- Autonomy Algorithm Engineer：Task A PC evidence dispatch。
- Robot Platform Engineer：Task B Robot diagnostics metadata-only consumer。
- User Touchpoint Full-Stack Engineer：Task C mobile/web phone-safe panel。
- Product Manager / OKR Owner：Task D closeout、OKR 和进度日志。

## 7. Product Closeout 验证结果

```text
rg -n "route_task_field_retest_evidence_dispatch|software_proof_docker_route_task_field_retest_evidence_dispatch_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch OKR.md docs/process/okr_progress_log.md
exit 0; matched closeout docs, OKR.md and docs/process/okr_progress_log.md.

git diff --check -- sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/tech-done.md sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/side2side_check.md sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md OKR.md docs/process/okr_progress_log.md
exit 0; no output.

git status --short
reviewed; only Product Closeout files plus known A/B/C/planning files are present; no staging or commit performed.
```

## 8. 风险、阻塞和证据链缺口

- 本轮仍是 Docker-only software proof，不是 HIL、真实 WAVE ROVER、真实串口/UART、真实 2D LiDAR / ToF、真实 Nav2/fixed-route、真实电梯、真实手机/browser、production app 或 Objective 5 external proof。
- 真实证据链仍需补齐：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result，并保持同一 `evidence_ref`。
- PR #4 / PR #5 相关缺口仍在：电梯 assisted delivery 的真实门状态/楼层确认/人工协助材料，以及单目 + 2D LiDAR + ToF 安全环的真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Objective 5 仍最低，但只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料时才应继续上调。
