# Sprint 2026.05.18_16-17 Route Task Acceptance Execution Rerun Queue - Tech Plan

## 1. 目标

实现 `route_task_field_retest_acceptance_execution_rerun_queue`：在上一轮 `route_task_field_retest_acceptance_execution_handoff_intake` 之后新增 metadata-only 受控现场复跑队列包。它只读 handoff intake artifact / summary / wrapper / nested JSON 和可选 queue request JSON，输出 Docker/local software proof summary，不能宣称真实现场复跑、delivery success、HIL 或 Objective 5 proof。

证据边界固定为:

- `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对理由: Objective 5 的下一步真实完成度需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser；当前主机只有 Docker，没有这些外部材料。继续堆本地 O5 metadata 会重复消费外部材料 blocker，不能推动真实产品闭环。
4. 下一低项 Objective 1 约 81%，但真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 和 PR #5 2D LiDAR / ToF 真实材料不可用。本轮也不继续包装同一硬件 blocker。
5. 本轮转向 Objective 2 / 3 / 4 的理由: PR #4 已把 elevator-assisted delivery 写成必须能力，上一轮 final 建议用 handoff intake gate 判定 owner ack、材料补齐或同一 `evidence_ref` 重跑；PR #5 review 继续暴露 2D LiDAR / ToF 与 vendor/source 材料缺口，因此 route/elevator 现场材料链需要一个明确的 metadata-only 复跑队列包来避免误放行。

## 3. PR / Review 证据

- PR #4: `Add elevator-assisted delivery capability to agents, registry and OKR` 已 merged。它把 elevator assisted delivery 写入 Autonomy、Robot、Full-stack 责任和 OKR Phase E，说明 route/elevator 已是必须能力，不是可选 side branch。
- PR #5: `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 已 merged。它把 Objective 2 改为“可送垃圾任务 + 电梯 assisted delivery 必达闭环”，新增 KR7，并把 Objective 4 硬件/感知边界扩展为单目 + 2D LiDAR + ToF。
- PR #5 review 反馈 1: `docs/product/production_hardware_boundary.md` 的 Default Hardware Set 与 mandatory sensor baseline 不一致，可能误导 BOM/procurement 和 bringup。
- PR #5 review 反馈 2: mandatory sensor assumptions 缺 `docs/vendor/` source citation，2D LiDAR / ToF 不能当作已验证硬件事实。
- PR #5 review 反馈 3: OKR lowest-objective narrative 曾出现表格与文字不一致，说明本轮必须在 tech-plan 里显式写清 Objective 5 / Objective 1 为什么不是本轮主线。

## 4. Team 分工

本轮是 Epic sprint，后续实现阶段默认并行启动 3 个 worker。文件范围互不重叠，Product 只做 closeout，不触碰工程文件。

### Task A - Autonomy Engineer

允许改动:

- `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py`
- `tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py`
- `pc-tools/README.md`
- `docs/architecture/evidence_contracts.md` 或现有同类 evidence contract 文档

实现要求:

- 只读消费 `route_task_field_retest_acceptance_execution_handoff_intake` artifact、summary、wrapper 或 nested JSON。
- 可选消费 queue request JSON，queue request 只能包含 owner-safe metadata、safe `evidence_ref`、owner ack、requested rerun reason 和 next-required evidence。
- 输出 artifact schema `trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1`。
- 输出 summary schema `trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1`。
- 状态必须至少覆盖:
  - `queued_for_controlled_field_rerun_not_proven`
  - `needs_owner_ack_before_queue`
  - `needs_acceptance_execution_rerun_queue_backfill`
  - `evidence_ref_mismatch_rerun_queue`
  - `blocked_unsafe_rerun_queue`
  - `blocked_unsupported_handoff_intake`
- 所有输出固定 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺输入、坏 JSON、unsupported schema/boundary、source handoff intake 未 ready、owner ack 缺失、queue request evidence_ref mismatch、unsafe copy、raw path、credential、ROS topic、serial/UART/WAVE ROVER detail、checksum、完整 artifact、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 新增代码技术注释使用中文，且有意义中文注释比例超过 20%。

验收命令:

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_queue
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py --help
rg -n "route_task_field_retest_acceptance_execution_rerun_queue|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate|queued_for_controlled_field_rerun_not_proven|needs_owner_ack_before_queue|needs_acceptance_execution_rerun_queue_backfill|evidence_ref_mismatch_rerun_queue|blocked_unsafe_rerun_queue|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py pc-tools/README.md docs
git diff --check -- pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py pc-tools/README.md docs
```

### Task B - Robot Software Engineer

允许改动:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/architecture/ros_contracts.md` 或现有同类 diagnostics / ROS contract 文档

实现要求:

- 新增 safe alias `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary`。
- 消费 top-level rerun queue summary、artifact nested summary、status diagnostics summary、diagnostics nested summary 和 explicit ref。
- 缺失或 unsafe 时输出 blocked default summary。
- 不触发 collect/dropoff/cancel、ACK、cursor、Nav2 runtime、serial/UART、WAVE ROVER、HIL 或任何 robot command。
- 保持 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
- 新增代码技术注释使用中文，且有意义中文注释比例超过 20%。

验收命令:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary|route_task_field_retest_acceptance_execution_rerun_queue|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs
```

### Task C - Full-stack Software Engineer

允许改动:

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现要求:

- 新增只读“受控复跑队列” panel。
- 优先消费 `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary`，再消费 queue summary / artifact / nested diagnostics。
- 展示字段限定为 queue status、safe `evidence_ref`、source handoff intake status、owner acknowledgement state、owner handoff、next required evidence、safe rerun hint、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不 fetch raw artifact，不展示 raw JSON、local path、checksum、credential、ROS topic、serial/UART、WAVE ROVER detail、完整 artifact 或 success copy。
- Start Delivery / Confirm Dropoff / Cancel gating 不变。
- 新增代码技术注释使用中文，且有意义中文注释比例超过 20%。

验收命令:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "受控复跑队列|route_task_field_retest_acceptance_execution_rerun_queue|robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product Owner Closeout

允许改动:

- `sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/tech-done.md`
- `sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/side2side_check.md`
- `sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求:

- 汇总 worker 实际改动和验证结果。
- 核对 Objective 5 / Objective 1 未被软件证明误上调。
- 如果 OKR 进度调整，只能写软件证明层收益，不能写真实 field pass、HIL、delivery success 或 O5 external proof。
- final 必须回顾本 `OKR 最低优先级核对` 是否仍成立。

验收命令:

```bash
test -f sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/tech-done.md && test -f sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/side2side_check.md && test -f sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/final.md
rg -n "route_task_field_retest_acceptance_execution_rerun_queue|robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue
```

## 5. 接口和数据边界

允许输入:

- `trashbot.route_task_field_retest_acceptance_execution_handoff_intake.v1`
- `trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1`
- wrapper / nested JSON 中的 handoff intake summary
- 可选 queue request JSON

禁止输入或输出:

- raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER low-level details
- credentials、OSS AK/SK、DB/queue URL、bearer token
- complete raw artifact、checksum、absolute local path、traceback
- success/control copy
- `delivery_success=true`
- `primary_actions_enabled=true`

## 6. 集成验收围栏

实现完成后由主节点只做验收判断，不直接修工程代码。集成围栏:

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_queue
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_execution_rerun_queue|robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary|software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue
git diff --check -- OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue
```

## 7. 剩余风险和阻塞

- 本机没有真实硬件，任何 WAVE ROVER/UART/HIL 相关结论只能保持 `not_proven`。
- 本机没有真实外部云/4G/OSS/CDN/DB/queue/worker/手机材料，Objective 5 不能因本轮上调。
- PR #5 2D LiDAR / ToF 仍是 material pending，不得把 rerun queue 写成 sensor procurement 或 HIL-entry proof。
- PR #4 route/elevator field materials 仍需真实现场采集；本轮 queue package 只是把下一步队列化。
- 如果 worker 实现中发现 handoff intake schema 不足，优先 fail closed，并在 `tech-done.md` 写明返工点。

