# Sprint 2026.05.14_20-21 Route Task Rehearsal Diagnostics - Final

sprint_type: epic

## 收口结论

本 sprint 完成 `software_proof_docker_route_task_rehearsal_diagnostics_gate`。Task A 已让 route/task rehearsal artifact 产出可诊断的 `diagnostics_summary`；Task B 已让 operator diagnostics 只读消费 artifact 并输出 `route_task_rehearsal` summary；Task C 已按软件证据边界更新 OKR、进度日志和 closeout 文档。

Objective 2 和 Objective 3 各从约 78% 谨慎上调到约 79%。Objective 5 保持约 68%，因为本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 证据。

## 用户价值和北极星

用户价值：现场或支持人员不再只知道“PC 工具有一个 artifact”，而是能在 diagnostics 里看到 route/task rehearsal 的 status、`evidence_ref`、crosscheck status、HIL alignment status、`not_proven` 和 next_step。后续拿到真实路线或硬件材料时，可以沿同一证据锚点补证。

北极星对齐：普通手机用户和支持人员不需要理解 ROS2、串口或命令行，也能区分“可复盘的软件排练证据”和“尚未证明真实送达”的边界。

## OKR 映射和 KR 拆解

- Objective 2 KR5：任务记录可复盘能力增强；diagnostics 能消费 route/task rehearsal artifact，但仍不是 delivery success。
- Objective 3 KR2/KR3/KR5：fixed-route software rehearsal 的输入输出、dry-run 证据和诊断展示链路更清晰。
- Objective 5：本轮不推进，因为没有真实外部云/4G/OSS/CDN/DB/queue 证据。

## 本轮核心抓手、优先级和责任 Engineer

- P0：artifact `diagnostics_summary`，责任 `autonomy-engineer`。
- P0：operator diagnostics `route_task_rehearsal` metadata-only summary，责任 `robot-software-engineer`。
- P0：OKR、progress log、tech-done、side2side、final 收口，责任 `product-okr-owner`。

## 实际改动

Task A `autonomy-engineer`：

- `pc-tools/evidence/evidence_crosscheck.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

Task B `robot-software-engineer`：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task C `product-okr-owner`：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/tech-done.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/side2side_check.md`
- `sprints/2026.05.14_20-21_route-task-rehearsal-diagnostics/final.md`

## 验证结果

- Task A：`python3 -m py_compile pc-tools/evidence/evidence_crosscheck.py` pass；`python3 onboard/src/ros2_trashbot_behavior/test/test_task_record.py` Ran 8 tests OK；required `rg` pass；scoped `git diff --check` pass。
- Task B：operator gateway diagnostics py_compile pass；`test_operator_gateway_diagnostics.py` Ran 45 tests OK；required `rg` pass；scoped `git diff --check` pass。中间 copy/redaction 问题已修复重跑通过。
- Task C：required `rg` 与 scoped `git diff --check` 已执行，输出见最终聊天汇总。

## 阶段验收

通过。P0 验收项均满足：

- artifact 保持旧 `software_proof_docker_route_task_rehearsal_artifact_gate`，并新增 `diagnostics_summary`。
- `diagnostics_summary` schema 为 `trashbot.route_task_rehearsal_diagnostics_summary`，边界为 `software_proof_docker_route_task_rehearsal_diagnostics_gate`。
- summary 只脱敏暴露 status、evidence_boundary、`evidence_ref`、crosscheck_status、hil_alignment_status、`not_proven` 和 next_step。
- operator diagnostics 可通过 explicit ref 或 `TRASHBOT_ROUTE_TASK_REHEARSAL_ARTIFACT` 输出 `route_task_rehearsal` summary。
- valid artifact、missing/sensitive path、crosscheck fail 围栏已覆盖。
- 文档已同步 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## OKR 最低优先级回顾

tech-plan 中的 OKR 最低优先级核对理由仍成立：Objective 5 仍是数字最低（约 68%），但本轮期间没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 或其他真实外部材料出现。继续推进本地 O5 metadata depth 不会移动 O5 completion，因此本轮切到 Objective 2/3 的 route/task rehearsal diagnostics consumption 合理。

下一轮如果真实 O5 外部材料出现，应优先回到 Objective 5；如果仍没有外部材料，O2/O3 的下一步应从本轮 software proof 走向真实 Nav2/fixed-route、真实路线采集和同一 `evidence_ref` 的上车复账，而不是继续扩大 diagnostics 文档。

## 风险/阻塞/证据链

证据链：上一轮 artifact gate -> 本轮 diagnostics summary -> operator diagnostics `route_task_rehearsal` summary -> OKR/progress log 收口。边界保持为 `software_proof_docker_route_task_rehearsal_diagnostics_gate`。

剩余风险：

- 真实 Nav2/fixed-route、真实路线采集、关键帧实景证据未完成。
- WAVE ROVER、真实串口、HIL 与同一 `evidence_ref` 的上车复账未完成。
- dropoff/cancel completion、真实失败恢复和 delivery success 未完成。
- Objective 5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 均未出现。
