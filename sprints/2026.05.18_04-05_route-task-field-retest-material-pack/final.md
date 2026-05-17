# Sprint 2026.05.18_04-05 Route Task Field Retest Material Pack - Final

sprint_type: epic

## 1. 最终结论

状态：`CLOSED_READY_FOR_COMMIT_AND_PUSH`。

本 sprint 完成 `route_task_field_retest_material_pack`：承接上一轮 `route_task_field_retest_result_review_handoff`，把 owner handoff 转成 field capture checklist、callback payload skeleton、owner work orders、rerun commands 和 same-`evidence_ref` fail-closed 材料包。A/B/C workers 均完成 scoped validation，Product closeout 已更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md` 和本 `final.md`。

证据边界：`software_proof_docker_route_task_field_retest_material_pack_gate`。本轮仍是 Docker-only / PC-only / metadata-only / mobile read-only software proof，不是真实 route/elevator field pass，不是真实 Nav2/fixed-route，不是真实 task record/completion signal，不是真实 dropoff/cancel completion，不是 delivery success，不是真实手机/browser，不是 HIL，不是 WAVE ROVER/UART，不是 Objective 5 external proof。

## 2. 用户价值和产品北极星

用户价值：现场 owner 不再只拿到 result review handoff，而是拿到下一次真实回填可执行的材料包：要采哪些文件/记录、如何保持同一 safe `evidence_ref`、如何构造 callback、谁负责补齐、如何 rerun。

产品北极星：把低成本 ROS2 垃圾投递机器人推进到“真实送达前的证据链可执行、可复核、可追责”，同时严格区分 software proof 与真实路线、电梯、手机、硬件和云端证据。

## 3. OKR 进度

- Objective 2：保持约 99%。理由是 PR #4 route/elevator field-material chain 已从 review handoff 推进到 material pack，明确 field checklist、callback skeleton、owner work orders 和 rerun；仍不是真实送达、真实电梯、真实 dropoff/cancel completion 或 delivery success。
- Objective 3：保持约 99%。理由是 Nav2/fixed-route runtime log、route completion signal、task record 等 result materials 的采集要求被固化为同一 `evidence_ref` 的材料包；仍不是真实路线实跑、真实 completion signal 或真实 task record。
- Objective 4：保持约 99%。mobile/web 有只读“路线/电梯现场材料包”panel，copy/export whitelist-only，控制按钮不放宽；但无真实 iPhone/Android、production app、真实 browser 或 PWA prompt/user choice。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或真实手机/browser external proof；O5 stop rule 仍成立。
- Objective 1：保持约 81%。本轮没有真实 WAVE ROVER、UART、HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 真实 2D LiDAR / ToF 材料；也未新增 SKU、串口、波特率或硬件假设。

## 4. 实际改动文件

Product closeout 本轮改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.18_04-05_route-task-field-retest-material-pack/tech-done.md`
- `sprints/2026.05.18_04-05_route-task-field-retest-material-pack/side2side_check.md`
- `sprints/2026.05.18_04-05_route-task-field-retest-material-pack/final.md`

A/B/C workers 已完成的 durable work：

- `pc-tools/evidence/route_task_field_retest_material_pack.py`
- `pc-tools/evidence/test_route_task_field_retest_material_pack.py`
- `docs/interfaces/evidence_contracts.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`
- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

## 5. 验证摘要

Task A / Autonomy：

- py_compile exit 0。
- focused unittest `Ran 7 tests OK`。
- 下游 `test_route_task_field_retest_operator_drill.py`、`test_route_task_field_retest_result_acceptance_backfill.py`、`test_route_task_field_retest_result_backfill_review_decision.py` 共 `Ran 15 tests OK`。
- CLI `--help` 显示旧/新入口；required `rg` 等价命令通过；scoped diff check exit 0。

Task B / Robot：

- py_compile exit 0。
- diagnostics unittest `Ran 172 tests in 0.346s OK`。
- 新增 alias：`robot_diagnostics_route_task_field_retest_material_pack_summary`。
- required `rg` exit 0；scoped diff check exit 0。

Task C / Full-stack：

- `node --check mobile/web/app.js` exit 0。
- mobile unittest `Ran 68 tests in 0.305s OK`。
- required `rg` exit 0；scoped diff check exit 0。

Task D / Product closeout：

```text
rg -n "route_task_field_retest_material_pack|software_proof_docker_route_task_field_retest_material_pack_gate|Objective 5|Objective 1|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_04-05_route-task-field-retest-material-pack
matched required boundary / Objective / fail-closed tokens
```

```text
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_04-05_route-task-field-retest-material-pack
exit 0
```

## 6. OKR 最低优先级回顾

当前数值最低 Objective 仍是 Objective 5，约 68%。本 sprint 没有针对 Objective 5，因为继续提升 O5 必须有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover 或真实手机/browser external proof。当前本机只有 Docker，A/B/C durable work 也全部属于 O2/O3/O4 route/elevator material-pack chain，因此没有移动 Objective 5。

下一低项 Objective 1 约 81%。本 sprint 也没有继续 Objective 1，因为最近三轮已经围绕 WAVE ROVER HIL packet 做 intake、review decision 和 execution pack，剩余 blocker 是真实 WAVE ROVER、真实 UART、真实串口日志、真实 topic samples 和 operator HIL report。PR #5 硬件 baseline / vendor source 风险仍存在，但本轮不新增 SKU、串口、波特率或硬件假设，只把 route/elevator 现场材料采集清单做成 software proof。

这两个理由在 final 收口时仍成立。

## 7. 剩余风险和下一步

- 需要真实现场 material pack 后的 callback 回填材料和同一 `evidence_ref` 上车复账。
- 需要真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- 需要真实手机设备 / iPhone / Android / production app / PWA prompt/user choice 现场验收，才能继续证明 Objective 4 的设备侧口径。
- 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或真实手机/browser external proof，才能继续推进 Objective 5。
- 需要真实 WAVE ROVER HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report，才能继续推进 Objective 1。
- 需要 PR #5 的真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定与 HIL-entry 材料，才能推进相关硬件基线。
- Product closeout 已完成要求的 scoped `rg` 和 `git diff --check`；主会话后续只应执行 staged diff 检查、commit 和 push，不再扩大产品代码范围。
