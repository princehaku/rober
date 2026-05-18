# Sprint 2026.05.18_16-17 Route Task Acceptance Execution Rerun Queue - Final

## 1. 收口结论

本轮完成 `route_task_field_retest_acceptance_execution_rerun_queue`，把上一轮 `route_task_field_retest_acceptance_execution_handoff_intake` 之后的 owner handoff intake 状态推进为受控现场复跑队列 metadata。Autonomy、Robot diagnostics 和 mobile/web 现在能围绕同一 safe `evidence_ref` 表达 queued / ack missing / backfill / mismatch / unsafe / unsupported 状态。

证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`。本轮所有输出保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，不证明真实现场复跑、真实送达、HIL、真实手机/browser 或 Objective 5 external proof。

## 2. OKR 最低优先级核对回顾

- `OKR.md` 4.1 的数字最低 Objective 仍是 Objective 5，约 68%。
- 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser，因此不继续堆 O5 本地 metadata，也不上调 Objective 5。
- 下一低项 Objective 1 仍约 81%，但本机没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 2D LiDAR / ToF 真实材料，因此不继续包装同一硬件 blocker，也不上调 Objective 1。
- 本轮继续推进 Objective 2 / 3 / 4 的 PR #4 route/elevator 现场验收链是合理的，因为上一轮 handoff intake 已指出需要 owner ack、材料补齐或同一 `evidence_ref` 复跑队列。

## 3. 用户价值和产品北极星

北极星仍是普通手机用户可用的低成本 ROS2 自主垃圾投递机器人。本轮的用户价值是让现场 owner、Robot diagnostics 和手机界面都能看到“受控复跑队列”下一步，而不是把 handoff intake 的 ready 状态误读成真实现场通过。普通用户仍只看到安全的只读解释，不接触 raw JSON、ROS topic、串口、路径、凭证或底层硬件材料。

## 4. 实际改动

- Autonomy: `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py`、`tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py`、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- Robot: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_contracts.md`。
- Full-stack: `mobile/web/app.js`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- Product: `sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 5. 集成验证结果

Product closeout 于 2026-05-18 16:19 Asia/Shanghai 复跑集成围栏:

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py`: exit 0。
- `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_queue`: `Ran 6 tests in 0.046s`，`OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: `Ran 185 tests in 0.415s`，`OK`。
- `node --check mobile/web/app.js`: exit 0。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`: `Ran 86 tests in 0.475s`，`OK`。
- required `rg`: exit 0，覆盖 `route_task_field_retest_acceptance_execution_rerun_queue`、`robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary`、`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`、`Objective 5`、`Objective 1`、`PR #4`、`PR #5`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- scoped `git diff --check`: exit 0。
- staged `git diff --cached --check`: exit 0。

## 6. OKR 更新

- Objective 1 保持约 81%。本轮没有真实 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 2D LiDAR / ToF 真实材料。
- Objective 2 保守保持约 99%。本轮把 route/elevator acceptance execution handoff intake 推进到受控复跑队列 metadata，但没有真实 delivery success。
- Objective 3 保守保持约 99%。本轮把 Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 和 delivery result 的材料要求继续队列化，但没有真实路线实跑。
- Objective 4 保守保持约 99%。本轮新增手机只读“受控复跑队列” panel，但没有真实 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice。
- Objective 5 保持约 68%。本轮没有真实外部云/4G/OSS/CDN/DB/queue/worker/cutover/手机 external proof。

## 7. 剩余风险和下一步

- 真实 route/elevator field pass 仍缺：门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion、delivery result。
- 真实 O1 硬件证据仍缺：WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。
- 真实 O5 外部证据仍缺：HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。
- PR #5 2D LiDAR / ToF 仍缺 vendor/source、receipt、procurement、installation、wiring、power、calibration 和 HIL-entry 材料。

下一轮最有用的动作不是继续堆本地 O5 metadata，而是拿真实外部 O5 材料、真实 O1 WAVE ROVER/HIL 材料，或围绕本轮 same `evidence_ref` 补 PR #4 route/elevator 受控现场复跑材料。
