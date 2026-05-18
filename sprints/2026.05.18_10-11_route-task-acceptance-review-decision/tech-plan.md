# Sprint 2026.05.18_10-11 Route Task Acceptance Review Decision - Tech Plan

## 1. 执行策略

本轮是 Epic sprint，必须并行启动 3 个 owner 子 agent：Autonomy、Robot、Full-stack。三个 owner 文件范围互不重叠，接口通过 `route_task_field_retest_acceptance_review_decision` summary schema、safe `evidence_ref`、`software_proof_docker_route_task_field_retest_acceptance_review_decision_gate` 和 Robot/mobile alias 对齐。

Product Owner 只负责计划、验收口径和后续留档，不直接修改产品代码、测试代码或硬件配置。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective：Objective 5，约 68%。
2. 本 sprint 是否针对最低 Objective：否。
3. 不针对理由：Objective 5 下一步真实进展需要至少一种外部材料：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof。本机只有 Docker，O5 stop rule 继续成立。
4. 下一个不选 Objective 1 的理由：Objective 1 约 81%，但 2026.05.17_20-21 到 23-24 已连续消费 WAVE ROVER/HIL 本地包装；当前仍无真实 `/dev/ttyUSB*`、`feedback_T1001`、`/odom`、`/imu`、`/battery` 或 operator HIL report。
5. 本轮选择：继续 PR #4 merged 后的 route/elevator field materials 回填路线，针对 Objective 2 / Objective 3 / Objective 4 的 actionable gap：`route_task_field_retest_acceptance_brief` 下游 review decision。
6. PR #5 处理：PR #5 review 指出的 hardware baseline / 2D LiDAR / ToF / vendor-source 问题真实材料仍缺，本轮不做硬件材料包装。

## 2. 当前事实和接口缺口

- PC evidence 已有 `pc-tools/evidence/route_task_field_retest_acceptance_brief.py` 和顶层 `tests/test_route_task_field_retest_acceptance_brief.py`。
- Robot diagnostics 已输出 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary`。
- mobile/web 已能读取 acceptance brief safe alias。
- 缺口：brief 之后没有统一 decision contract 来表达“受控现场复跑 / 材料回填 / owner handoff / evidence_ref mismatch rerun / unsafe rejection”。

## 3. 并行 owner 分工

### Autonomy Algorithm Engineer

文件范围：

- `pc-tools/evidence/route_task_field_retest_acceptance_review_decision.py`
- `pc-tools/evidence/test_route_task_field_retest_acceptance_review_decision.py`
- `tests/test_route_task_field_retest_acceptance_review_decision.py`
- `docs/interfaces/evidence_contracts.md`
- `pc-tools/README.md`

任务：

- 新增 PC gate，消费 `route_task_field_retest_acceptance_brief` artifact/summary/wrapper。
- 输出 schemas：`trashbot.route_task_field_retest_acceptance_review_decision.v1` 和 `trashbot.route_task_field_retest_acceptance_review_decision_summary.v1`。
- 必须覆盖 statuses：`ready_for_controlled_field_retest_not_proven`、`needs_route_elevator_material_backfill_not_proven`、`needs_owner_handoff_not_proven`、`evidence_ref_mismatch_rerun_not_proven`、`blocked_acceptance_brief_not_ready`、`unsupported_acceptance_brief_schema_not_proven`、`rejected_unsafe_acceptance_brief_claim_not_proven`。
- 输出字段至少包含：`review_decision`、`material_status`、`owner_handoff`、`next_required_evidence`、`rerun_commands`、`safe_copy`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 新增顶层 unittest wrapper，使 `python3 -m unittest tests.test_route_task_field_retest_acceptance_review_decision` 可运行。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_review_decision.py tests/test_route_task_field_retest_acceptance_review_decision.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_review_decision
python3 pc-tools/evidence/route_task_field_retest_acceptance_review_decision.py --help
rg -n "route_task_field_retest_acceptance_review_decision|software_proof_docker_route_task_field_retest_acceptance_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests docs/interfaces/evidence_contracts.md sprints/2026.05.18_10-11_route-task-acceptance-review-decision
git diff --check -- pc-tools tests docs/interfaces/evidence_contracts.md sprints/2026.05.18_10-11_route-task-acceptance-review-decision
```

### Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

任务：

- 新增 diagnostics summarizer/consumer，支持 `route_task_field_retest_acceptance_review_decision` artifact、summary、nested wrapper 和 file/env style source。
- `status_payload` 输出 `route_task_field_retest_acceptance_review_decision`、`route_task_field_retest_acceptance_review_decision_summary`、`robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary` safe alias。
- focused unittest 覆盖 alias、缺输入 blocked、summary-only source、nested wrapper、unsupported schema/boundary、unsafe fields、success/control wording 和 disabled actions。
- 保持 task_orchestrator、Start Delivery、Confirm Dropoff、Cancel、ACK、Nav2、HIL、primary actions 不变。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_acceptance_review_decision|robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary|software_proof_docker_route_task_field_retest_acceptance_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md sprints/2026.05.18_10-11_route-task-acceptance-review-decision
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md sprints/2026.05.18_10-11_route-task-acceptance-review-decision
```

### User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

任务：

- 新增 mobile/web 只读 `route_task_field_retest_acceptance_review_decision` panel。
- 读取优先级覆盖 `robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary`、`route_task_field_retest_acceptance_review_decision_summary`、`route_task_field_retest_acceptance_review_decision`。
- 展示 review decision、safe evidence ref、material status、owner handoff、next required evidence、rerun commands、boundary flags、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 确保 Start Delivery、Confirm Dropoff、Cancel 仍不被该 panel 打开；copy/export 只包含 whitelist metadata。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_review_decision|robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary|software_proof_docker_route_task_field_retest_acceptance_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.18_10-11_route-task-acceptance-review-decision
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.18_10-11_route-task-acceptance-review-decision
```

## 4. 集成验收

三个 owner 返回后，Product Owner 只做证据核对和 sprint 留档。若任一验证失败，必须把失败定位和重试任务交回对应 owner。

集成验收命令：

```bash
rg -n "route_task_field_retest_acceptance_review_decision|robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary|software_proof_docker_route_task_field_retest_acceptance_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_10-11_route-task-acceptance-review-decision
git diff --check -- pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_10-11_route-task-acceptance-review-decision
git diff --stat
```

## 5. 风险边界

- 本轮只证明 repo-local / Docker-local software proof，不证明真实 route/elevator field pass。
- 本轮不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
- `delivery_success=false` 和 `primary_actions_enabled=false` 是验收硬门槛，任何 enabled action 或 success phrasing 都必须 fail closed。
- 完成后若仅有 software proof，`OKR.md` 进度不应大幅提升；closeout 只能保守更新证据链与缺口。
