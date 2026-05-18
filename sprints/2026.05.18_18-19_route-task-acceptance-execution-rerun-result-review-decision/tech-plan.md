# Sprint 2026.05.18_18-19 Route Task Acceptance Execution Rerun Result Review Decision - Tech Plan

## 1. Plan 状态

- sprint_type: epic
- 本轮主题：`route_task_field_retest_acceptance_execution_rerun_result_review_decision`
- 目标证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`
- 实现方式：3 个 Engineer 并行，文件范围互不重叠。
- 验证原则：测试只围栏；只跑 `py_compile`、focused unittest、`node --check`、required `rg`、scoped `git diff --check`，不跑 broad regression。
- 统一边界：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. OKR 最低优先级核对

1. `OKR.md` 4.1 当前数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。原因：Objective 5 仍缺真实外部 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。按 stop rule，没有真实外部材料时不继续堆本地 O5 metadata，也不把本轮 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate` 写成 Objective 5 external proof。
3. 下一低项 Objective 1 约 81%，但本机无真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 2D LiDAR / ToF 仍缺真实 vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。本轮不继续包装同一硬件 blocker。
4. 本 sprint 选择 Objective 2 / Objective 3 / Objective 4 的 route/elevator result review decision 链路。依据是上一轮 final 已完成 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`，下一格必须把 intake 转成 handoff/backfill/mismatch/unsafe/unsupported 判定。
5. final.md 收口时需复核：O5/O1 blocker 是否仍然缺真实材料；若仍缺，则本轮不得上调 O5/O1，也不得把 metadata-only review decision 写成真实现场通过。

## 3. PR #4 / PR #5 证据

- PR #4 要求 elevator-assisted delivery 进入主链；route/elevator 现场材料链必须能从 result intake 进入 review decision，再进入 owner handoff、backfill 或重跑路径。
- PR #5 unresolved review threads 指出 `docs/product/production_hardware_boundary.md` 默认硬件集合与 `monocular + 2D LiDAR + ToF` baseline 矛盾；新增 sensor baseline 缺 `docs/vendor/` source citation；真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料仍缺。
- 本轮不修改硬件事实、不新增传感器型号、不更新 vendor source；只在证据边界里保留 PR #5 风险，避免再消费 Objective 1 hardware blocker。

## 4. 统一接口与状态约束

新增 result review decision gate 必须消费上一轮 result intake artifact/summary，输出 metadata-only artifact/summary。支持状态：

- `ready_for_acceptance_execution_rerun_result_handoff`
- `needs_acceptance_execution_rerun_result_backfill`
- `evidence_ref_mismatch_rerun_result`
- `blocked_unsafe_rerun_result`
- `blocked_unsupported_rerun_result_intake`

所有 owner 必须保持：

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- not real route/elevator field pass
- not delivery success
- not HIL
- not real phone/browser
- not Objective 5 external proof

禁止输出或展示 raw artifact、complete artifact、local path、checksum、credentials、DB/queue URL、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER low-level controls 或真实成功文案。

## 5. 并行 Owner 拆分

### Task A - Autonomy Algorithm Engineer

文件范围：

- `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py`
- `tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

需要做什么：

- 新增 PC gate `route_task_field_retest_acceptance_execution_rerun_result_review_decision.py`。
- 支持从上一轮 result intake artifact/summary 读取 safe intake state、safe `evidence_ref`、owner handoff、next required evidence。
- 材料足够、copy 安全、同一 evidence ref 成立时输出 `ready_for_acceptance_execution_rerun_result_handoff`。
- 缺 route completion signal、task record、Nav2/fixed-route runtime log、dropoff/cancel completion、delivery result、门状态、楼层确认或人工协助记录时输出 `needs_acceptance_execution_rerun_result_backfill`。
- 同一 `evidence_ref` 不一致时输出 `evidence_ref_mismatch_rerun_result`。
- 出现 unsafe copy、raw artifact、success claim、control claim 或 secret-like material 时输出 `blocked_unsafe_rerun_result`。
- 输入不是受支持 result intake schema / summary schema 时输出 `blocked_unsupported_rerun_result_intake`。
- 更新 `pc-tools/README.md` 和 `docs/interfaces/evidence_contracts.md`，写清本 gate 是 metadata-only software proof。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_decision
rg -n "route_task_field_retest_acceptance_execution_rerun_result_review_decision|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate|ready_for_acceptance_execution_rerun_result_handoff|needs_acceptance_execution_rerun_result_backfill|evidence_ref_mismatch_rerun_result|blocked_unsafe_rerun_result|blocked_unsupported_rerun_result_intake|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B - Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

需要做什么：

- 在 operator gateway diagnostics 中新增 sanitized summary alias，例如 `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary`。
- 只读消费 Autonomy summary，不读取 raw artifact，不开放控制入口。
- 输出 phone/diagnostics safe fields：schema、decision status、safe `evidence_ref`、next required evidence、owner handoff、boundary flags、`not_proven`。
- 保持 `delivery_success=false`、`primary_actions_enabled=false`，并确保 Start / Confirm Dropoff / Cancel gating 不受影响。
- 更新 `docs/interfaces/ros_contracts.md`，说明 Robot 只转发 sanitized metadata，不证明 ROS runtime、Nav2/fixed-route、route completion、dropoff/cancel completion 或 delivery result。

验收命令：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_acceptance_execution_rerun_result_review_decision|robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

需要做什么：

- 在 mobile/web 新增只读“受控复跑结果复核决策”panel。
- 消费 `route_task_field_retest_acceptance_execution_rerun_result_review_decision`、`route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary`、或 Robot sanitized alias。
- 展示 decision status、safe evidence ref、owner handoff、next required evidence、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 保持 Start Delivery、Confirm Dropoff、Cancel 的 fail-closed gating 不变。
- 更新 fixture 和 focused mobile test，覆盖 handoff/backfill/mismatch/unsafe/unsupported 的 phone-safe copy。
- 更新 `docs/product/mobile_user_flow.md`，说明本 panel 是 read-only support metadata，不证明真实手机/browser 或 delivery success。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_execution_rerun_result_review_decision|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate|ready_for_acceptance_execution_rerun_result_handoff|needs_acceptance_execution_rerun_result_backfill|evidence_ref_mismatch_rerun_result|blocked_unsafe_rerun_result|blocked_unsupported_rerun_result_intake|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 6. 集成验收口径

Engineer 并行完成后，Product Manager / OKR Owner 只做集成验收和 sprint 留档，不直接修实现。集成验收必须确认：

- 三个 owner 的 schema / summary / fixture 使用同一 result review decision family。
- 三个 surface 都包含 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`。
- 三个 surface 都保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot/mobile 只消费 sanitized summary，不读取 raw artifact 或完整本地文件。
- mobile/web 没有放宽 Start Delivery、Confirm Dropoff、Cancel。
- docs/interfaces 和 docs/product 明确 not real route/elevator field pass、not delivery success、not HIL、not real phone/browser、not Objective 5 external proof。

集成围栏建议：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_decision
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_execution_rerun_result_review_decision|robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py pc-tools/README.md docs/interfaces/evidence_contracts.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision
git diff --check -- pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py pc-tools/README.md docs/interfaces/evidence_contracts.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision/pre_start.md sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision/prd.md sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision/tech-plan.md
```

## 7. 风险与阻塞

- 真实 route/elevator field evidence 未提供前，本轮不能上调 Objective 2 / 3 / 4 的真实完成度。
- Objective 5 仍被真实外部证据阻塞：HTTPS/TLS、公网、4G/SIM、OSS/CDN、production DB/queue、worker/cutover、真实手机/browser。
- Objective 1 仍被真实硬件证据阻塞：WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。
- PR #5 hardware baseline 风险仍需后续真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料；本轮只在风险中引用，不解决。
- 如果 Engineer 发现现有 result intake fixture 或 diagnostics schema 已有兼容字段，应优先沿用本地模式，不新增并行的重复 schema。

## 8. 后续留档要求

- Engineer 返回后，Product Manager / OKR Owner 更新 `tech-done.md`，记录实际改动、验证结果、偏差和剩余风险。
- 验收完成后更新 `side2side_check.md`，逐条对照 PRD。
- 收口时更新 `final.md`，再次回顾 `OKR 最低优先级核对`、PR #4 / PR #5 证据、Docker-only 边界、是否仍保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
