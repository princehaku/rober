# Sprint 2026.05.16_02-03 Elevator Route Evidence Reconciliation - Pre Start

sprint_type: epic

## 1. 启动背景

本轮从 `OKR.md` 4.1 live 快照重新排序：Objective 5 约 66%，仍是数值最低；Objective 3 约 73%，Objective 2 / Objective 4 约 74%。但 `OKR.md` 第 6 节和最近两轮 final 都明确：O5 只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 证据时才应继续推进 completion。本机只有 Docker，没有真实外部材料，继续做本地 O5 metadata 会重复消费同一 blocker。

因此本轮转向最低可行动作：Objective 3 为主，Objective 2 / Objective 4 支撑。目标是把上一轮 `elevator_assist_rehearsal_evidence` 主链路和既有 `route_task_completion_signal` / field-run 材料链做同一 `evidence_ref` 复账，让现场/上车复测前能清楚判断“电梯阶段证据”和“路线任务完成信号”是否能归到同一次 run。

## 2. 近期 PR / 评审证据

- `sprints/2026.05.16_01-02_elevator-evidence-driven-mainline/final.md` 第 1 节：上一轮只把电梯 rehearsal evidence 压进 Robot task record 主链路；下一步仍缺真实电梯门状态、目标楼层、人工协助、Nav2/fixed-route runtime、task record、completion signal 同一 `evidence_ref` 的复账。
- `sprints/2026.05.15_13-14_elevator-field-rehearsal-execution-pack/final.md` 第 6 节：电梯 execution pack 已经能告诉现场同学采什么，但下一步必须把真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal 等材料用同一 `evidence_ref` 回填。
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/final.md` 第 1 节 / 第 3 节：route/task 现场复账已经能按同一 `evidence_ref` 检查 execution pack、intake/review 材料，但电梯阶段证据尚未进入 route completion 复账。
- 反复出现的问题：多轮 final 都把 O5 external proof 作为缺真实材料 blocker；O2/O3/O4 的可行动作集中在 same `evidence_ref`、not_proven、delivery_success=false、mobile 只读解释和现场重跑清单。

## 3. 本轮目标

交付 `software_proof_docker_elevator_route_evidence_reconciliation_gate`：

- PC/evidence CLI 读取 `trashbot.elevator_assist_rehearsal_evidence.v1` 或 summary，以及 `trashbot.route_task_completion_signal.v1` 或 summary，输出 `trashbot.elevator_route_evidence_reconciliation.v1`。
- 复账逻辑必须检查 same `evidence_ref`、电梯 phase evidence present、route completion signal present、dropoff/cancel/delivery success 不可误宣称、not_proven 边界完整。
- Robot diagnostics 只读消费 reconciliation artifact / summary，固定 `delivery_success=false`、`primary_actions_enabled=false`，不触发 ROS action、ACK、HIL、Nav2 或真实运动。
- `mobile/web` 新增只读 panel，给普通用户/现场同学展示 evidence ref、phase/route 对齐状态、missing/mismatch、operator next steps 和 boundary，不改变 Start / Confirm / Cancel gating。

## 4. Owner 与文件边界

- Autonomy Algorithm Engineer：`pc-tools/evidence/elevator_route_evidence_reconciliation.py`、对应 test、`pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/product/elevator_assisted_delivery.md` 的相关小节。
- Robot Platform Engineer：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：`mobile/web/app.js`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：本 sprint 六文档、`OKR.md`、`docs/process/okr_progress_log.md`。

## 5. 验收口径

- 本轮所有输出都是 Docker/local software proof，不证明真实电梯、真实楼层确认、真实人工协助、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。
- 验证只跑围栏命令：对应单元测试、py_compile、`node --check`、required `rg`、scoped `git diff --check`。
- 不新增硬件参数、不改 WAVE ROVER/UART/Orange Pi 事实，不需要 vendor 文档介入。

## 6. Blocker 重复消费核对

最近两轮 final 的共同 blocker 是 O5 外部材料缺失。本轮不把该 blocker 包装成 O5 进展，也不继续增加 O5 本地 metadata。它转向 O3/O2 可执行复账链，帮助下一次真实现场 run 把电梯阶段证据和路线任务完成信号放到同一 `evidence_ref`。
