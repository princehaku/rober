# Sprint 2026.05.15_06-07 Route Task Field Run Console - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星：让普通手机用户最终能把垃圾交给小车，并清楚知道任务是否真实完成、哪里需要人工介入、哪些证据能支撑下一次现场复测。

本轮用户价值：把上一轮 completion signal、route status、execution pack 和 task record 进一步收敛成现场运行准备台。现场同学现在可以从统一入口看到要跑哪条路线、必须采哪些材料、same `evidence_ref` 是否一致、dropoff/cancel 材料是否缺失，以及哪些结果仍是 `not_proven`。

## 2. OKR 映射与 KR 拆解

- Objective 2：推进 KR4/KR5。Task A/B/C 已把 task record、dropoff/cancel material status、failure/recovery reason 和 operator next steps 作为 field-run console 与只读 summary 输出，但保持 `delivery_success=false`。
- Objective 3：推进 KR2/KR3/KR5。Task A 已把 execution pack、route status、task record 和 completion signal 纳入 same `evidence_ref` 校验；Task B/C 只读消费 summary，形成 PC/operator -> Robot diagnostics -> mobile panel 的一致边界。
- Objective 4：只做支援，不上调。`mobile/web` 新增只读“路线现场运行准备”panel，但 Browser 渲染补验未运行，不能计真实手机/browser 或 production app 证据。
- Objective 5：本轮不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料；本轮 not real O5 external proof。

## 3. 实际改动

Task A - Autonomy Algorithm Engineer：

- `pc-tools/evidence/route_task_field_run_console.py`
- `pc-tools/evidence/test_route_task_field_run_console.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

新增 dependency-free CLI，读取 execution pack、route status、task record 和 completion signal，输出 `schema=trashbot.route_task_field_run_console.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_console_gate`、`same_evidence_ref_required=true`、`console_verdict`、`field_run_plan`、`capture_checklist`、execution/route/task/completion summaries、dropoff/cancel material status、operator next steps、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false`、`delivery_success=false`。

Task B - Robot Platform Engineer：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Diagnostics 新增 `route_task_field_run_console` / `_summary` metadata-only consumption，支持 explicit ref 和 `TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE` / `_SUMMARY` 环境变量，严格检查 schema、boundary 和 unsafe fields，并固定 `delivery_success=false`、`primary_actions_enabled=false`。

Task C - User Touchpoint Full-Stack Engineer：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

新增只读“路线现场运行准备”panel，消费 `route_task_field_run_console` / summary，展示 console verdict、safe `evidence_ref`、field-run plan、capture checklist、dropoff/cancel status、operator next steps、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 boundary。

Task D - Product Manager / OKR Owner：

- `sprints/2026.05.15_06-07_route-task-field-run-console/tech-done.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/side2side_check.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Product closeout 汇总三条工程 worker 结果，更新 OKR evidence boundary 和 progress log；不提交、不推送。

## 4. 验证结果

Task A 验证：

- `python3 -m py_compile pc-tools/evidence/route_task_field_run_console.py pc-tools/evidence/test_route_task_field_run_console.py`：pass。
- `python3 pc-tools/evidence/test_route_task_field_run_console.py`：`Ran 6 tests in 0.019s OK`。
- `python3 pc-tools/evidence/route_task_field_run_console.py --help`：pass。
- Required `rg`：pass。
- Scoped `git diff --check`：pass。

Task B 验证：

- `python3 -m py_compile ...operator_gateway_diagnostics.py ...test_operator_gateway_diagnostics.py`：pass。
- `python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 67 tests in 0.053s OK`。
- Required `rg`：pass。
- Scoped `git diff --check`：pass。

Task C 验证：

- `python3 mobile/test_mobile_web_entrypoint.py`：`Ran 37 tests in 0.073s OK`。
- `python3 -m py_compile mobile/test_mobile_web_entrypoint.py`：pass。
- `node --check mobile/web/app.js`：pass。
- Required `rg`：pass。
- Scoped `git diff --check`：pass。
- Browser 渲染补验未运行：`Browser is not available: iab`，因此不能计真实手机/browser 证据。

Task D closeout 验收见本轮最终验证命令输出。

## 5. 失败定位与偏差

- Task A 首轮 safe-copy 扫描把内部 `serial_or_uart` 边界标签误判为 unsafe；Autonomy 已修复并复验通过。
- Browser 渲染补验未运行，根因为运行时 `iab` 不可用；影响范围仅限真实 browser/手机证据，工程 unit/syntax/rg/diff 围栏不受影响。
- 本轮没有硬件、串口、WAVE ROVER、Nav2 runtime、真实 fixed-route、真实 dropoff/cancel completion 或外部 O5 材料。

## 6. 剩余风险和证据边界

本轮证据边界固定为 `software_proof_docker_route_task_field_run_console_gate`。它只是 Docker/local field-run 准备台、diagnostics summary 和 mobile 只读 panel 的软件证明；不是 `not real` 交付证明，也不是：

- 真实 Nav2/fixed-route 运行。
- 真实路线采集或关键帧实景证据。
- WAVE ROVER、真实串口/UART、HIL 或 `T=1001` feedback。
- 同一 `evidence_ref` 上车实机复账。
- 真实 dropoff/cancel completion。
- `delivery_success=true` 或真实送达。
- 真实手机/browser、production app、真实 PWA prompt/user choice。
- Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 7. 文档同步与工程质量监管

三条工程任务均更新了对应 `docs/`：

- Autonomy：`docs/navigation/fixed_route_workflow.md`。
- Robot：`docs/interfaces/ros_contracts.md`。
- Full-stack：`docs/product/mobile_user_flow.md`。

Product closeout 已同步 `OKR.md` 与 `docs/process/okr_progress_log.md`。代码中文注释比例由对应 worker 在各自文件范围内负责；本 closeout 未直接修改产品代码、测试代码或硬件配置。
