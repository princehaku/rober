# Sprint 2026.05.18_04-05 Route Task Field Retest Material Pack - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `route_task_field_retest_material_pack` 三面契约，证据边界固定为 `software_proof_docker_route_task_field_retest_material_pack_gate`。

Task A / Autonomy：

- 实现/修复 `pc-tools/evidence/route_task_field_retest_material_pack.py`。
- 保留旧 `--material-dir` 兼容，同时新增 `--result-review-handoff-json` / `--review-handoff-summary` handoff 模式。
- 恢复 `MATERIAL_ALIASES`、`_source_dir_status`、`_scan_material`、`_has_raw_path_copy`、`_has_success_or_control_claim`，让旧材料目录扫描、handoff summary、unsafe copy 和 success/control claim 防线同时可用。

Task B / Robot：

- 新增 `robot_diagnostics_route_task_field_retest_material_pack_summary` alias。
- 支持 nested diagnostics 消费，保持 diagnostics metadata-only、fail-closed 和 `primary_actions_enabled=false`。

Task C / Full-stack：

- 新增只读“路线/电梯现场材料包”面板。
- 消费 artifact / summary / Robot alias / nested summaries。
- copy/export 仅白名单字段，不放宽 Start Delivery、Confirm Dropoff、Cancel。

Product closeout：

- 更新 `OKR.md`、`docs/process/okr_progress_log.md`、本 `tech-done.md`、`side2side_check.md`、`final.md`。

## 2. PR / 评审依据

- PR #4 要求 elevator assisted delivery 进入主链路；本轮把 route/elevator field materials 转成现场 owner 可执行的材料包，而不是继续停留在 review handoff。
- PR #5 review 指出硬件 baseline / vendor source 风险；本轮不新增 SKU、串口、波特率、2D LiDAR / ToF 参数或硬件假设，只把 route/elevator 现场材料采集清单做成 software proof。
- 最新 `03-04_route-task-result-review-handoff` final 的下一步是同一 `evidence_ref` 真实 callback 回填材料和现场复账；本轮 material pack 正是该回填动作的 checklist、callback skeleton 和 rerun commands。

## 3. 验证结果

Task A / Autonomy：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_material_pack.py
exit 0
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_material_pack.py
Ran 7 tests
OK
```

```text
下游 focused unittest:
test_route_task_field_retest_operator_drill.py
test_route_task_field_retest_result_acceptance_backfill.py
test_route_task_field_retest_result_backfill_review_decision.py
Ran 15 tests
OK
```

```text
CLI --help 显示旧 --material-dir 与新增 --result-review-handoff-json / --review-handoff-summary 入口
required rg 等价命令通过
scoped git diff --check exit 0
```

Task B / Robot：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 172 tests in 0.346s
OK
```

```text
required rg exit 0
scoped git diff --check exit 0
```

Task C / Full-stack：

```text
node --check mobile/web/app.js
exit 0
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 68 tests in 0.305s
OK
```

```text
required rg exit 0
scoped git diff --check exit 0
```

Task D / Product closeout：

```text
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|Objective 5|Objective 1|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_04-05_route-task-field-retest-material-pack
matched required boundary / Objective / fail-closed tokens
```

```text
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_04-05_route-task-field-retest-material-pack
exit 0
```

## 4. 偏差和边界

- 本轮证据是 Docker-only / software proof / metadata-only / mobile read-only，不是真实 route/elevator field pass。
- 本轮没有真实 Nav2/fixed-route runtime、真实 route completion signal、真实 task record、真实 dropoff/cancel completion 或 delivery result。
- 本轮没有真实手机/browser、production app、PWA prompt/user choice、HIL、WAVE ROVER/UART、O5 external proof。
- 本轮没有新增硬件 SKU、串口、波特率、2D LiDAR / ToF 参数或 vendor source 假设；PR #5 的硬件 source 风险保持为真实材料缺口。

## 5. 剩余风险

- 仍需要同一 `evidence_ref` 的真实 callback 回填材料和现场复账。
- 仍需要真实电梯门状态、真实目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- 仍需要真实手机设备 / iPhone / Android / production app / PWA prompt/user choice 现场验收。
- Objective 5 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。
- Objective 1 仍需要真实 WAVE ROVER HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report。
