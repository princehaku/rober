# Sprint 2026.05.18_11-12 Route Task Acceptance Execution Pack - Tech Plan

## 1. 执行策略

本轮是 Epic sprint，必须并行启动 3 个 owner 子 agent：Autonomy、Robot、Full-stack。三个 owner 文件范围互不重叠，接口通过 `route_task_field_retest_acceptance_execution_pack` summary schema、safe `evidence_ref`、`software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate` 和 Robot/mobile alias 对齐。

Product Owner 只负责计划、验收口径和后续留档，不直接修改产品代码、测试代码或硬件配置。实现阶段必须按 AGENTS.md 固定 prompt 结构派发给对应 Engineer。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective：Objective 5，约 68%。
2. 本 sprint 是否针对最低 Objective：否。
3. 不针对 Objective 5 的理由：Objective 5 下一步真实进展需要至少一种外部材料：真实 HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof。本机只有 Docker，O5 stop rule 继续成立，不能再堆本地 O5 metadata。
4. 下一个不选 Objective 1 的理由：Objective 1 约 81%，但近期 WAVE ROVER/HIL packet intake、review、execution-pack 已重复消费真实硬件 blocker；当前仍无真实 `/dev/ttyUSB*`、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 operator HIL report。
5. 本轮选择：继续 Objective 2 / Objective 3 / Objective 4 的 PR #4 route/elevator 现场验收链，新增 `route_task_field_retest_acceptance_execution_pack`，消费上一轮 acceptance review decision，产出现场复跑执行包、owner checklist、rerun commands 和 safe evidence bundle。
6. PR #5 处理：PR #5 review 指出的 production hardware boundary、2D LiDAR / ToF mandatory sensor assumptions 和 `docs/vendor/` source 缺口仍是独立硬件材料风险，本轮不包装成已闭环。

## 2. 当前事实和接口缺口

- 已有上一轮 `route_task_field_retest_acceptance_review_decision` PC gate、Robot diagnostics safe alias 和 mobile/web 只读 panel。
- 已有证据边界：`software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`。
- 当前缺口：review decision 之后没有统一 execution pack 来承接现场 owner checklist、rerun commands、安全证据包、材料要求和 fail-closed 交接。
- 本轮目标边界：只新增 `software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`，不声明真实 field pass、delivery success、HIL 或 external cloud proof。

## 3. 并行 owner 分工

### Autonomy Algorithm Engineer

文件范围：

- `pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py`
- `pc-tools/evidence/test_route_task_field_retest_acceptance_execution_pack.py`
- `tests/test_route_task_field_retest_acceptance_execution_pack.py`
- `docs/interfaces/evidence_contracts.md`
- `pc-tools/README.md`

任务：

- 新增 PC gate，消费 `route_task_field_retest_acceptance_review_decision` artifact、summary、nested wrapper 和 file/env style source。
- 输出 schemas：`trashbot.route_task_field_retest_acceptance_execution_pack.v1` 和 `trashbot.route_task_field_retest_acceptance_execution_pack_summary.v1`。
- 输出字段至少包含：`execution_pack_status`、`review_decision_source`、`owner_checklist`、`rerun_commands`、`safe_evidence_bundle`、`required_route_elevator_materials`、`handoff_owner`、`next_required_evidence`、`safe_copy`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须 fail closed：unsupported review decision schema、missing/weak `evidence_ref`、unsafe copy、success/control wording、`delivery_success=true`、`primary_actions_enabled=true`。
- 新增顶层 unittest wrapper，使 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_pack` 可运行。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py tests/test_route_task_field_retest_acceptance_execution_pack.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_pack
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py --help
rg -n "route_task_field_retest_acceptance_execution_pack|software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests docs/interfaces/evidence_contracts.md sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
git diff --check -- pc-tools tests docs/interfaces/evidence_contracts.md sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
```

### Robot Platform Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

任务：

- 新增 diagnostics summarizer/consumer，支持 `route_task_field_retest_acceptance_execution_pack` artifact、summary、nested wrapper 和 file/env style source。
- `status_payload` 输出 `route_task_field_retest_acceptance_execution_pack`、`route_task_field_retest_acceptance_execution_pack_summary`、`robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary` safe alias。
- focused unittest 覆盖 alias、缺输入 blocked、summary-only source、nested wrapper、unsupported schema/boundary、unsafe fields、success/control wording 和 disabled actions。
- 保持 task_orchestrator、Start Delivery、Confirm Dropoff、Cancel、ACK、Nav2、HIL、primary actions 不变。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_acceptance_execution_pack|robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary|software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
```

### User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

任务：

- 新增 mobile/web 只读 `route_task_field_retest_acceptance_execution_pack` panel。
- 读取优先级覆盖 `robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary`、`route_task_field_retest_acceptance_execution_pack_summary`、`route_task_field_retest_acceptance_execution_pack`。
- 展示 safe `evidence_ref`、owner checklist、rerun commands、safe evidence bundle、required route/elevator materials、handoff owner、next required evidence、boundary flags、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 确保 Start Delivery、Confirm Dropoff、Cancel 仍不被该 panel 打开；copy/export 只包含 whitelist metadata。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_execution_pack|robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary|software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
```

## 4. 集成验收

三个 owner 返回后，Product Owner 只做证据核对和 sprint 留档。若任一验证失败，必须把失败定位和重试任务交回对应 owner。

集成验收命令：

```bash
rg -n "route_task_field_retest_acceptance_execution_pack|robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary|software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
git diff --check -- pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
git diff --stat
```

## 5. 风险边界

- 本轮只证明 repo-local / Docker-local software proof，不证明真实 route/elevator field pass。
- 本轮不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
- `delivery_success=false` 和 `primary_actions_enabled=false` 是验收硬门槛，任何 enabled action 或 success phrasing 都必须 fail closed。
- 完成后若仅有 software proof，`OKR.md` 进度不应大幅提升；closeout 只能保守更新证据链与缺口。
