# Sprint 2026.05.18_13-14 Route Task Acceptance Execution Callback Review Decision - Tech Plan

## 1. 技术目标

新增 `route_task_field_retest_acceptance_execution_callback_review_decision` 这一 repo-local software proof rung。它只读上一轮 callback intake 的 artifact / summary，把 received / missing / rejected 状态转成受控现场复跑、材料回填或同一 `evidence_ref` 重跑决策。

固定证据边界：

- `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

不得写成真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 中完成度最低的是 Objective 5，约 68%。本轮不直接推进 Objective 5，原因是本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料；继续堆本地 metadata depth 不会形成 O5 production proof，O5 stop rule 继续成立。

下一低项 Objective 1 约 81%，但仍缺真实 WAVE ROVER/UART/HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report。最近 `wave_rover_hil_packet_*` 已反复消费同一缺真实硬件 blocker，本轮不能继续本地包装同一 blocker。

因此本轮 rerank 到 Objective 2 / Objective 3：基于 PR #4 elevator-assisted delivery 主链和上一轮 acceptance execution callback intake，推进 `route_task_field_retest_acceptance_execution_callback_review_decision`。PR #5 指出的 hardware baseline / vendor source / 2D LiDAR / ToF 风险继续作为真实硬件材料缺口记录，不在本轮用本地软件证明替代。

## 3. 并行 owner 任务拆分

### Task A：Autonomy PC gate

Owner：Autonomy Algorithm Engineer

允许文件范围：

- `pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py`
- `tests/test_route_task_field_retest_acceptance_execution_callback_review_decision.py`
- 如 repo 现有 evidence README 有索引要求，可在实现阶段由 Product closeout 再决定是否补 docs；本轮 planning 不预先扩大范围。

实现要求：

- 读取 callback intake artifact / summary。
- 校验 schema、boundary、status、safe copy、`evidence_ref`、`delivery_success=false`、`primary_actions_enabled=false`。
- 输出 decision：
  - 全部必需材料 received 且同一 `evidence_ref` 对齐：`ready_for_controlled_field_rerun`
  - 存在 missing / rejected：`needs_material_backfill`
  - 同一 `evidence_ref` 不一致：`evidence_ref_mismatch_rerun`
  - 输入缺失、坏 JSON、unsupported schema/boundary、unsafe copy、成功/控制越界声明：fail closed
- 输出 owner handoff、next required evidence、safe rerun command summary、`not_proven`。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py tests/test_route_task_field_retest_acceptance_execution_callback_review_decision.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_review_decision
```

### Task B：Robot diagnostics safe alias

Owner：Robot Platform Engineer

允许文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`

实现要求：

- 增加 `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary` safe alias。
- alias 从主 summary 或兼容 diagnostics summary 中抽取 phone-safe 字段。
- 只保留 review decision、source intake status、safe `evidence_ref`、owner handoff、next required evidence、safe rerun command summary、boundary flags、`not_proven`。
- 不暴露 raw ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER 参数、凭证、local paths、完整 artifacts、checksums 或 tracebacks。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

### Task C：Full-stack mobile/web read-only panel

Owner：User Touchpoint Full-Stack Engineer

允许文件范围：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- 如现有 CSS/HTML 结构必须补 panel 锚点，可只在 `mobile/web/` 内最小修改。

实现要求：

- 新增只读 “现场回执复核决策” panel。
- 消费 `route_task_field_retest_acceptance_execution_callback_review_decision_summary` 或 `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary`。
- 展示 review decision、source intake status、safe `evidence_ref`、owner handoff、next required evidence、safe rerun hint、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating；不发送 ACK、cursor、diagnostics fetch 或 robot command。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
```

### Task D：Product closeout

Owner：Product Manager / OKR Owner

后续允许文件范围：

- `sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/tech-done.md`
- `sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/side2side_check.md`
- `sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- 必要时补 `docs/product/mobile_user_flow.md` 或相关接口文档，前提是工程实际改动触达对应产品说明。

验收要求：

- 复核三位 Engineer 的验证输出。
- 复跑 required rg 和 scoped git diff check。
- 更新 OKR 进展时保守表述：本轮只证明 callback review decision software proof，不提升为真实送达或外部生产证明。

## 4. 接口和数据边界

输入来源：

- `route_task_field_retest_acceptance_execution_callback_intake`
- 兼容 summary / diagnostics safe summary

输出名称：

- `route_task_field_retest_acceptance_execution_callback_review_decision`
- `route_task_field_retest_acceptance_execution_callback_review_decision_summary`
- `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary`

必备字段：

- `schema`
- `schema_version`
- `review_decision`
- `source_callback_intake_schema`
- `source_callback_intake_status`
- `evidence_ref`
- `owner_handoff`
- `next_required_evidence`
- `rerun_commands` 或 safe rerun summary
- `evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 5. 验证计划

只允许围栏验证，不跑 broad test：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py tests/test_route_task_field_retest_acceptance_execution_callback_review_decision.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_review_decision
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_execution_callback_review_decision|robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary|software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs/product/mobile_user_flow.md
```

Planning 文件本身的验收命令：

```bash
test -f sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/pre_start.md && test -f sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/prd.md && test -f sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PR #4|PR #5|route_task_field_retest_acceptance_execution_callback_review_decision|software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision
git diff --check -- sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision
```

## 6. 风险和失败处理

- 如果 callback intake 输入缺失或 schema/boundary 不匹配，PC gate 必须 fail closed，并给出 owner handoff。
- 如果 callback materials 缺失或 rejected，决策必须是 `needs_material_backfill`，不得写成 ready。
- 如果 `evidence_ref` mismatch，决策必须是 `evidence_ref_mismatch_rerun`，不得自动合并材料。
- 如果任何输入或输出含 `delivery_success=true`、`primary_actions_enabled=true`、真实送达成功、真实电梯成功、HIL 通过、真实手机通过或 O5 external proof 文案，必须判为越界。
- 如果 Robot/mobile 只能展示 safe alias 缺失状态，也必须保持 read-only 和 fail-closed。

## 7. 交付顺序

1. 并行启动 Autonomy、Robot、Full-stack 三个 worker。
2. 三个 worker 返回后，由 Product closeout 汇总验证证据。
3. 若任一围栏失败，把失败定位和重试任务交回对应 owner。
4. 全部通过后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和必要 docs。
