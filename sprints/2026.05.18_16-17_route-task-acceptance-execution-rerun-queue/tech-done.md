# Sprint 2026.05.18_16-17 Route Task Acceptance Execution Rerun Queue - Tech Done

## 1. Sprint 声明

- sprint_type: epic
- 收口时间: 2026-05-18 16:19 Asia/Shanghai
- 主题: `route_task_field_retest_acceptance_execution_rerun_queue`
- 证据边界: `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`
- 产品结论: 本轮完成受控现场复跑队列的 metadata-only software proof；没有真实 route/elevator field pass、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 2. 实际改动

### Autonomy Engineer

- 新增 `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py`。
- 新增 `tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/interfaces/evidence_contracts.md`。
- 新增 artifact schema `trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1` 和 summary schema `trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1`。
- 状态覆盖 `queued_for_controlled_field_rerun_not_proven`、`needs_owner_ack_before_queue`、`needs_acceptance_execution_rerun_queue_backfill`、`evidence_ref_mismatch_rerun_queue`、`blocked_unsafe_rerun_queue`、`blocked_unsupported_handoff_intake`。

### Robot Software Engineer

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary` safe alias。
- Robot diagnostics 只读暴露受控复跑队列 metadata，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### Full-stack Software Engineer

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“受控复跑队列” panel，优先消费 Robot safe alias；Start Delivery、Confirm Dropoff、Cancel gating 不变。

### Product Owner

- 新建本文件、`side2side_check.md` 和 `final.md`。
- 更新 `OKR.md` 当前快照，保持 Objective 5 约 68%、Objective 1 约 81%，Objective 2 / 3 / 4 只记录 software proof metadata-only 收益。
- 更新 `docs/process/okr_progress_log.md`，追加本 sprint 证据与边界。

## 3. 验证结果

Worker 已完成的局部围栏:

- Autonomy: `py_compile` exit 0；`python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_queue` 输出 `Ran 6 tests in 0.044s OK`；CLI `--help` exit 0；required `rg` exit 0；scoped diff check exit 0。
- Robot: `py_compile` exit 0；diagnostics unittest 输出 `Ran 185 tests in 0.404s OK`；required `rg` exit 0；scoped diff check exit 0。
- Full-stack: `node --check mobile/web/app.js` passed；`python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 86 tests OK`；required `rg` passed；scoped diff check passed。

Product closeout 需复跑的集成围栏记录在 `final.md`，包括:

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py`
- `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_queue`
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `node --check mobile/web/app.js`
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`
- required `rg`
- scoped `git diff --check`
- staged `git diff --cached --check`

## 4. 偏差和边界

- 本轮没有真实 WAVE ROVER、UART、serial、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report、2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 材料；Objective 1 不上调。
- 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover、真实手机设备/browser、production app 或真实 PWA prompt/user choice；Objective 5 不上调。
- 本轮没有真实 route/elevator field pass、真实 Nav2/fixed-route runtime log、真实 route completion signal、真实 task record、真实门状态、真实目标楼层确认、真实人工协助记录、真实 dropoff/cancel completion、真实 cancel completion 或真实 delivery result；Objective 2 / 3 / 4 保守保持约 99%，不写成 100%。
- `queued_for_controlled_field_rerun_not_proven` 只表示同一 safe `evidence_ref` 的现场复跑队列 metadata 可被 Autonomy、Robot diagnostics 和手机端安全读取；不表示现场复跑已发生。

## 5. 剩余风险

- PR #4 route/elevator 仍需要真实现场材料回填：电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 2D LiDAR / ToF 仍缺真实 vendor/source、receipt、procurement、installation、wiring、power、calibration 和 HIL-entry 证据。
- 后续如果现场 owner 提供真实材料，必须以同一 safe `evidence_ref` 进入 review/intake，不得把本地 rerun queue summary 当成真实通过证据。
