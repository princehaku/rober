# Sprint 2026.05.14_22-03 Route Task Rehearsal Operator Review - Tech Done

sprint_type: epic

## 用户价值和产品北极星

本轮把上一轮 route/task rehearsal execution bundle 继续推进成操作员可读的复盘/下一轮重跑决策链路。北极星仍是普通手机用户能完成送垃圾任务；本轮交付的实际价值是让现场操作员和支持人员不翻 raw artifact，也能看懂当前软件排练是否可用、还缺什么证据、下一轮该补路线/task material、重跑 rehearsal，还是等待真实 HIL/上车材料。

## OKR 映射

- Objective 2：推进 KR5“每次任务产出可复盘记录”，把 execution bundle 变成 `next_rehearsal_decision`、mismatch、`not_proven` 和 phone-safe copy。
- Objective 3：推进固定路线 dry-run/replay 的可解释能力，把 crosscheck/HIL boundary 和下一轮动作展示到 diagnostics 与 `mobile/web`。
- Objective 5：本轮不新增真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料，不提升 O5。
- Objective 1：本轮不读取硬件、不触发 Nav2、不访问串口，不声明 WAVE ROVER、真实 UART 或 HIL。

## KR 拆解或更新

- KR-O2-review：已生成 `trashbot.route_task_rehearsal_operator_review.v1` operator review package，包含 `next_rehearsal_decision`、`not_proven`、mismatch 与 `safe_copy`。
- KR-O3-decision：已让 diagnostics 与 mobile 首屏可读消费 operator review，帮助下一轮从 software proof 走向真实路线/任务证据。
- KR-mobile-safe：已保持 whitelist-only copy、`primary_actions_enabled=false`、`delivery_success=false`，并证明 metadata-only 不触发控制路径。
- KR-boundary：三端统一 `software_proof_docker_route_task_rehearsal_operator_review_gate`，不写成 HIL、真实路线运行或 delivery success。

## 实际改动

Task A `autonomy-engineer`：

- 新增 `pc-tools/evidence/route_task_rehearsal_operator_review.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/navigation/fixed_route_workflow.md`。
- 产物消费 `route_task_rehearsal_execution_bundle.json`，输出 `schema=trashbot.route_task_rehearsal_operator_review.v1`、`evidence_boundary=software_proof_docker_route_task_rehearsal_operator_review_gate`、`next_rehearsal_decision`、`not_proven`、whitelist-only `safe_copy`、`primary_actions_enabled=false`、`delivery_success=false`。

Task B `robot-software-engineer`：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 `route_task_rehearsal_operator_review` diagnostics summary，支持 explicit `route_task_rehearsal_operator_review_ref` 与 `TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW`。

Task C `full-stack-software-engineer`：

- 更新 `mobile/web/index.html`。
- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 新增 `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 首屏新增“路线/任务排练复盘”只读摘要，消费 status、phone_readiness 与 diagnostics 的 `route_task_rehearsal_operator_review*`。

Product closeout：

- 更新 `OKR.md`。
- 更新 `docs/process/okr_progress_log.md`。
- 创建本文件、`side2side_check.md`、`final.md`。

## 验证结果

Task A 验证：

- `python3 -m py_compile pc-tools/evidence/route_task_rehearsal_operator_review.py`：pass。
- `python3 pc-tools/evidence/route_task_rehearsal_operator_review.py --help`：pass。
- `/tmp` valid bundle drill：pass。
- schema/boundary/decision/not_proven/safe_copy blacklist assertions：pass。
- missing/read_error/unsupported schema smoke：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Task B 验证：

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：pass。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics`：`Ran 51 tests ... OK`。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Task C 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint`：`Ran 3 tests ... OK`。
- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`：pass。
- `node --check mobile/web/app.js`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Product closeout 验收：

- `rg -n "2026.05.14_22-03_route-task-rehearsal-operator-review|software_proof_docker_route_task_rehearsal_operator_review_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review`：pass，命中本 sprint、O2/O3/O5、HIL/not_proven/delivery success 边界。
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/tech-done.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/side2side_check.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/final.md`：pass。

## 偏差与失败定位

- 无最终遗留验证失败。
- 本轮 closeout 没有重跑工程 worker 的全部实现命令，只核对了工程 worker 汇总结果、相关 docs 已更新，并执行 Product 指定围栏。
- 本轮没有真实硬件、真实 Nav2/fixed-route、真实手机设备或真实云外部材料，因此所有结论保持 Docker/local software proof。

## 剩余风险

- `software_proof_docker_route_task_rehearsal_operator_review_gate` 只证明 Docker/local operator review 链路，不证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion 或 delivery success。
- O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 与 production worker/migration。
- O1 仍缺真实 WAVE ROVER `hil_pass`、真实串口日志与 `T=1001` feedback。
- 后续 O2/O3 若继续推进，必须从 operator review 走向真实路线/任务材料，不能继续叠加本地包装层。
