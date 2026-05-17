# Sprint 2026.05.18_04-05 Route Task Field Retest Material Pack - Tech Plan

sprint_type: epic

## 1. 技术方案

新增 `route_task_field_retest_material_pack` 三面契约：

1. PC evidence gate：读取上一轮 `route_task_field_retest_result_review_handoff` artifact/summary/wrapper，校验 schema、boundary、same safe `evidence_ref`、disabled actions、unsafe copy 和 success claim，输出材料包 artifact 与 summary。
2. Robot diagnostics：读取 PC gate 输出或 nested diagnostics summary，生成只读 diagnostics summary，缺失/unsupported/unsafe 时 fail closed。
3. mobile/web：从 status/readiness/diagnostics 多入口读取 summary，展示只读材料包、field checklist、callback skeleton、owner work orders 和 rerun commands，copy/export 仅白名单字段。

本轮核心 literal：

- `route_task_field_retest_material_pack`
- `trashbot.route_task_field_retest_material_pack.v1`
- `trashbot.route_task_field_retest_material_pack_summary.v1`
- `software_proof_docker_route_task_field_retest_material_pack_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. 文件范围和 owner

Task A / Autonomy Algorithm Engineer 可改：

- `pc-tools/evidence/route_task_field_retest_material_pack.py`
- `pc-tools/evidence/test_route_task_field_retest_material_pack.py`
- `docs/interfaces/evidence_contracts.md`

Task B / Robot Platform Engineer 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task C / User Touchpoint Full-Stack Engineer 可改：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Product closeout 可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.18_04-05_route-task-field-retest-material-pack/tech-done.md`
- `sprints/2026.05.18_04-05_route-task-field-retest-material-pack/side2side_check.md`
- `sprints/2026.05.18_04-05_route-task-field-retest-material-pack/final.md`

范围外文件不得改动。若发现需要共享接口字段，先在输出中说明，不能直接扩大范围。

## 3. 接口契约

PC artifact/summary 至少包含：

- `schema` / `schema_version`
- `evidence_boundary`
- `source_schema`
- `source_boundary`
- `safe_evidence_ref`
- `same_evidence_ref_required=true`
- `material_pack_status`
- `field_capture_checklist`
- `callback_payload_skeleton`
- `owner_work_orders`
- `rerun_commands`
- `safe_copy`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

建议状态：

- `ready_for_field_retest_material_collection_not_proven`
- `needs_result_review_handoff_not_proven`
- `evidence_ref_mismatch_rerun_not_proven`
- `blocked_missing_result_review_handoff_not_proven`
- `unsupported_result_review_handoff_schema_not_proven`

## 4. 验收命令

Task A 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_material_pack.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_material_pack.py
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_material_pack.py pc-tools/evidence/test_route_task_field_retest_material_pack.py docs/interfaces/evidence_contracts.md
```

Task B 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C 必须运行：

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false|路线/电梯现场材料包" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Product closeout 必须运行：

```bash
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|Objective 5|Objective 1|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_04-05_route-task-field-retest-material-pack
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_04-05_route-task-field-retest-material-pack
```

## 5. OKR 最低优先级核对

当前 `OKR.md` 4.1 最低 Objective 是 Objective 5，约 68%。本 sprint 不针对 Objective 5，因为继续推进 O5 必须有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover 或真实手机/browser external proof；当前本机只有 Docker，无法产生这类证据。

下一低项 Objective 1 约 81%。本 sprint 不继续 Objective 1，因为最近三轮已经围绕 WAVE ROVER HIL packet 做 intake / review decision / execution pack，剩余 blocker 是真实 WAVE ROVER、真实 UART、真实串口日志、真实 topic samples 和 operator HIL report。本轮不重复消费同一硬件 blocker。

因此，本轮选择 Objective 2 / 3 的 PR #4 route/elevator field-material 回填准备链：把 `route_task_field_retest_result_review_handoff` 推进到可执行 material pack，仍保持 software proof。

## 6. 风险边界

- 本轮不会提升 Objective 2 / 3 / 4 到 100%，因为没有真实现场材料。
- 本轮不会提升 Objective 5，因为没有外部云/4G/OSS/CDN/DB/queue proof。
- 本轮不会提升 Objective 1，因为没有真实 WAVE ROVER/UART/HIL packet。
- 若任何 worker 发现需要硬件参数、SKU、ToF 通道数、串口、波特率或 WAVE ROVER 指令，必须先读 `docs/vendor/VENDOR_INDEX.md` 并在输出中说明来源；本 sprint 默认不新增此类事实。
