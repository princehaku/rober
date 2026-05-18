# Sprint 2026.05.18_08-09 Route Task Field Retest Drill Console - Final

sprint_type: epic

## 1. 最终结论

本轮完成 `software_proof_docker_route_task_field_retest_drill_console_gate` closeout。三位 worker 已把上一轮 `route_task_field_retest_operator_drill` 推进成可被 PC evidence、Robot diagnostics 和 mobile/web 只读消费的 drill console summary，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Product closeout 已完成 `tech-done.md` 合并、`side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md` 更新。`tech-done.md` 已修复并行写入导致的 Autonomy 小节缺失问题。

## 2. 用户价值和产品北极星

本轮让现场 operator / support user 可以在同一 safe `evidence_ref` 下查看 drill console 的 operator command groups、callback checklist、required outputs、rerun summary 和 safe copy 边界。它减少现场材料演练时回退到旧 material pack-only 清单的风险，也减少把 operator drill / drill console 误读成真实现场通过的风险。

北极星仍是普通手机用户最终能完成一次低成本送垃圾任务；本轮只是 route/elevator 现场材料准备和 support surface 的软件证明，不是普通用户端真实送达闭环。

## 3. OKR 进度更新

- Objective 1 保持约 81%。本轮没有新增 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report、2D LiDAR / ToF SKU/source、串口、波特率或硬件假设。
- Objective 2 保持约 99%。本轮补强 field retest drill console，但没有真实 route/elevator field pass、真实门状态、真实楼层确认、人工协助现场记录、dropoff/cancel completion 或 delivery result。
- Objective 3 保持约 99%。本轮把 Nav2/fixed-route required outputs 与 rerun summary 放进 drill console，但没有真实路线采集、Nav2 waypoint/fixed-route 实跑、route completion signal 或 task record。
- Objective 4 保持约 99%。本轮让 mobile/web 只读展示 drill console safe summary，但没有真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 或真实现场 phone behavior。
- Objective 5 保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他真实 external proof。

## 4. 实际改动摘要

- Autonomy：新增顶层 unittest 入口和 `pc-tools/evidence/README.md` gate 说明，保留 PC evidence gate 的 Docker-only software proof 边界。
- Robot：新增 drill console Robot diagnostics alias，修复 nested child summary 覆盖完整 summary 造成 `safe_evidence_ref` 丢失的问题。
- Full-stack：mobile/web drill console 面板新增 operator command groups、required outputs、rerun summary，修复测试读取旧 fixture 的问题。
- Product：合并 `tech-done.md` 三方证据，创建验收对照和 final，保守更新 OKR 与进度日志。

## 5. 验证结果

Worker fenced 验证均已在 `tech-done.md` 留档：

- Autonomy：`py_compile` 通过；`python3 -m unittest tests.test_route_task_field_retest_drill_console` 通过，`Ran 5 tests in 0.021s OK`；required `rg` 和 scoped `git diff --check` 通过。
- Robot：`py_compile` 通过；diagnostics unittest 通过，`Ran 176 tests in 0.345s OK`；required `rg` 和 scoped `git diff --check` 通过。
- Full-stack：`node --check mobile/web/app.js` 通过；mobile unittest 通过，`Ran 72 tests OK`；required `rg` 和 scoped `git diff --check` 通过。

Product closeout 额外运行本轮要求的 `rg`、scoped `git diff --check`、`git diff --stat`、`git status --short`，并在提交前核对 staged diff。

## 6. 风险和阻塞

- 仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、task record/completion signal、dropoff/cancel completion 和 delivery success。
- 仍缺 HIL、WAVE ROVER/UART、真实串口、真实 feedback、PR #5 2D LiDAR / ToF 真实材料。
- 仍缺真实 phone/browser/device proof、production app、真实 PWA prompt/user choice。
- Objective 5 external proof 仍缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 production worker/cutover 证据。

## 7. 下一步

若 O5 external proof 和 O1 real hardware proof 仍不可用，下一轮应继续沿 PR #4 route/elevator 真实材料回填路线推进：带本轮 drill console 到受控现场，采集同一 safe `evidence_ref` 下的门状态、楼层确认、人工协助、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 或 delivery result；拿到真实材料后再进入 intake / review / reconciliation，而不是继续堆本地 metadata depth。
