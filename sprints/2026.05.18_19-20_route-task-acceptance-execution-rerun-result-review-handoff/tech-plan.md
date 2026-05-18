# Sprint 2026.05.18_19-20 Route Task Acceptance Execution Rerun Result Review Handoff - Tech Plan

## 1. Plan 状态

- sprint_type: epic
- 本轮主题：`route_task_field_retest_acceptance_execution_rerun_result_review_handoff`
- 目标证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`
- 实现方式：3 个 Engineer 并行，Autonomy、Robot、Full-stack 文件范围互不重叠。
- 验证原则：测试只围栏；只跑 `py_compile`、focused unittest、`node --check`、required `rg`、scoped `git diff --check`，不跑 broad regression。
- 统一边界：`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。原因：Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部证据。按 stop rule，没有真实外部材料时不继续堆本地 O5 metadata，也不把本轮 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate` 写成 Objective 5 external proof。
3. 下一低项 Objective 1 约 81%。本机无真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 的 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料仍缺。本轮不第三次消费同一硬件 blocker。
4. 本 sprint 选择 Objective 2 / Objective 3 / Objective 4 的 route/elevator handoff 链路。依据是上一轮 final 已完成 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`，下一步必须把 review decision 交给 PR #4 真实现场回填 owner，而不是创建 O5/O1 包装。
5. final.md 收口时需复核：O5/O1 blocker 是否仍然缺真实材料；若仍缺，则本轮不得上调 O5/O1，也不得把 metadata-only handoff 写成真实现场通过。

## 3. PR #4 / PR #5 证据

- PR #4 已合并：电梯 assisted delivery 进入主链；route/elevator 现场证据链必须继续推进，从 review decision 进入 owner handoff、真实材料回填或同一 `evidence_ref` 重跑。
- PR #5 review 未解决点：`docs/product/production_hardware_boundary.md` 默认硬件集合与 `monocular + 2D LiDAR + ToF` mandatory baseline 矛盾；新增 sensor baseline 缺 `docs/vendor/` source citation；OKR 最低项叙述曾漂移。
- 本轮不修改硬件事实、不新增传感器型号、不更新 vendor source；只在 handoff 风险中保留 PR #5 材料缺口，避免再消费 Objective 1 hardware blocker。

## 4. 统一接口与状态约束

新增 handoff gate 必须消费上一轮 result review decision artifact/summary，输出 metadata-only handoff artifact/summary。建议支持状态：

- `ready_for_acceptance_execution_rerun_result_owner_handoff`
- `needs_acceptance_execution_rerun_result_material_backfill`
- `evidence_ref_mismatch_rerun_result_handoff_blocked`
- `blocked_unsafe_rerun_result_handoff_copy`
- `blocked_unsupported_rerun_result_review_decision`

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

禁止输出或展示 raw artifact、complete artifact、local path、checksum、credentials、DB/queue URL、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER low-level control、success wording 或 control wording。

## 5. 并行 Owner 拆分

### Task A - Autonomy Algorithm Engineer

文件范围：

- `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py`
- `tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

接口约束：

- 只消费上一轮 `route_task_field_retest_acceptance_execution_rerun_result_review_decision` artifact/summary 的 safe 字段。
- 不读取真实材料目录，不解析 raw artifact，不访问本地 path、checksum、credentials、DB/queue URL、ROS topic 或 serial/UART。
- 输出 artifact/summary 必须含 schema、handoff status、safe `evidence_ref`、owner role、next required evidence、rerun summary、boundary flags、`not_proven`。
- 输出必须固定 `source=software_proof`、`delivery_success=false`、`primary_actions_enabled=false`。

需要做什么：

- 新增 PC gate `route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py`。
- 将上一轮 ready handoff decision 转成 `ready_for_acceptance_execution_rerun_result_owner_handoff`。
- 将缺真实门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 或 delivery result 转成 `needs_acceptance_execution_rerun_result_material_backfill`。
- 将 `evidence_ref` 不一致转成 `evidence_ref_mismatch_rerun_result_handoff_blocked`。
- 将 unsafe copy、raw artifact、success claim、control claim 或 secret-like material 转成 `blocked_unsafe_rerun_result_handoff_copy`。
- 将不支持的 review decision 输入转成 `blocked_unsupported_rerun_result_review_decision`。
- 更新 `pc-tools/README.md` 和 `docs/interfaces/evidence_contracts.md`，写清本 gate 是 PR #4 真实现场回填准备层。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff
rg -n "route_task_field_retest_acceptance_execution_rerun_result_review_handoff|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate|ready_for_acceptance_execution_rerun_result_owner_handoff|needs_acceptance_execution_rerun_result_material_backfill|evidence_ref_mismatch_rerun_result_handoff_blocked|blocked_unsafe_rerun_result_handoff_copy|blocked_unsupported_rerun_result_review_decision|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B - Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

接口约束：

- 只读消费 Autonomy sanitized summary，不读取 raw artifact，不打开材料目录，不新增控制入口。
- 输出 safe alias，例如 `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary`。
- alias 只包含 schema、handoff status、safe `evidence_ref`、owner role、next required evidence、boundary flags、`not_proven`。
- 必须保持 `delivery_success=false`、`primary_actions_enabled=false`；不得影响 Start / Confirm Dropoff / Cancel gating。

需要做什么：

- 在 operator gateway diagnostics 中新增 handoff safe alias。
- 增加 focused diagnostics test，覆盖 ready owner handoff、material backfill、mismatch、unsafe、unsupported。
- 更新 `docs/interfaces/ros_contracts.md`，说明 Robot 只转发 sanitized metadata，不证明 ROS runtime、Nav2/fixed-route、route completion、dropoff/cancel completion 或 delivery result。

验收命令：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_acceptance_execution_rerun_result_review_handoff|robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

接口约束：

- 只消费 `route_task_field_retest_acceptance_execution_rerun_result_review_handoff`、`route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary` 或 Robot sanitized alias。
- 只展示 safe fields：handoff status、owner role、safe evidence ref、next required evidence、rerun summary、boundary flags、`not_proven`。
- 不展示 raw artifact、complete artifact、local path、checksum、credentials、DB/queue URL、ROS topic、serial/UART、WAVE ROVER low-level control、success wording 或 control wording。
- 不发送 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor 或 diagnostics fetch；现有 primary action gating 不变。

需要做什么：

- 在 mobile/web 新增只读“受控复跑交接”panel。
- 更新 fixture，覆盖 handoff summary 的 phone-safe example。
- 更新 focused mobile test，覆盖 ready owner handoff、material backfill、mismatch、unsafe、unsupported copy。
- 更新 `docs/product/mobile_user_flow.md`，说明本 panel 是 read-only support metadata，不证明真实手机/browser 或 delivery success。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_execution_rerun_result_review_handoff|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate|ready_for_acceptance_execution_rerun_result_owner_handoff|needs_acceptance_execution_rerun_result_material_backfill|evidence_ref_mismatch_rerun_result_handoff_blocked|blocked_unsafe_rerun_result_handoff_copy|blocked_unsupported_rerun_result_review_decision|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 6. 集成验收口径

Engineer 并行完成后，Product Manager / OKR Owner 只做集成验收和 sprint 留档，不直接修实现。集成验收必须确认：

- 三个 owner 的 schema / summary / fixture 使用同一 handoff family。
- 三个 surface 都包含 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`。
- 三个 surface 都保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot/mobile 只消费 sanitized summary，不读取 raw artifact 或完整本地文件。
- mobile/web 没有放宽 Start Delivery、Confirm Dropoff、Cancel。
- docs/interfaces 和 docs/product 明确 not real route/elevator field pass、not delivery success、not HIL、not real phone/browser、not Objective 5 external proof。

集成围栏建议：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_execution_rerun_result_review_handoff|robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate|Objective 5|Objective 1|PR #4|PR #5|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py pc-tools/README.md docs/interfaces/evidence_contracts.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.18_19-20_route-task-acceptance-execution-rerun-result-review-handoff
git diff --check -- pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.18_19-20_route-task-acceptance-execution-rerun-result-review-handoff/pre_start.md sprints/2026.05.18_19-20_route-task-acceptance-execution-rerun-result-review-handoff/prd.md sprints/2026.05.18_19-20_route-task-acceptance-execution-rerun-result-review-handoff/tech-plan.md
```

## 7. 风险与阻塞

- 真实 route/elevator field evidence 未提供前，本轮不能上调 Objective 2 / 3 / 4 到真实完成，也不能声称 route/elevator field pass。
- Objective 5 仍被真实外部证据阻塞：HTTPS/TLS、公网、4G/SIM、OSS/CDN、production DB/queue、worker/cutover、真实手机/browser。
- Objective 1 仍被真实硬件证据阻塞：WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。
- PR #5 hardware baseline 风险仍需后续真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料；本轮只在风险中引用，不解决。
- 如果 Engineer 发现现有 review decision fixture 或 diagnostics schema 已有兼容字段，应优先沿用本地模式，不新增并行的重复 schema。

## 8. 后续留档要求

- Engineer 返回后，Product Manager / OKR Owner 更新 `tech-done.md`，记录实际改动、验证结果、偏差和剩余风险。
- 验收完成后更新 `side2side_check.md`，逐条对照 PRD。
- 收口时更新 `final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，再次回顾 `OKR 最低优先级核对`、PR #4 / PR #5 证据、Docker-only 边界、是否仍保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
