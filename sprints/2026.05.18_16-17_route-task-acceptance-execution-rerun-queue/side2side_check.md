# Sprint 2026.05.18_16-17 Route Task Acceptance Execution Rerun Queue - Side2Side Check

## 1. 验收对象

- Autonomy: `route_task_field_retest_acceptance_execution_rerun_queue` PC gate。
- Robot: `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary` safe alias。
- Full-stack: mobile/web 只读“受控复跑队列” panel。
- Product: `OKR.md` 和 `docs/process/okr_progress_log.md` 的边界更新。

## 2. 用户价值对照

- 现场 owner 可以围绕同一 safe `evidence_ref` 判断是否进入受控复跑准备。
- Robot diagnostics 和手机端能展示队列状态、owner handoff、next required evidence、safe rerun hint 和 fail-closed boundary。
- 普通手机用户仍不能通过该 panel 触发 Start Delivery、Confirm Dropoff 或 Cancel。
- Product/OKR 继续区分 `software_proof`、现场材料准备、真实 field pass、HIL 和 Objective 5 external proof。

## 3. OKR 边界对照

- Objective 2: 受益于 route/elevator acceptance execution handoff intake 之后新增受控复跑队列，但没有真实 delivery success。
- Objective 3: 受益于复跑队列继续要求 Nav2/fixed-route runtime log、task record、completion signal 和 same `evidence_ref`，但没有真实路线实跑。
- Objective 4: 受益于手机只读状态展示和 Robot safe alias，但没有真实手机设备/browser 或 production app 验收。
- Objective 5: 数字最低但本轮没有 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue 或 worker/cutover 真实材料，继续保持约 68%。
- Objective 1: 次低但本轮没有 WAVE ROVER/UART/HIL 或 PR #5 2D LiDAR / ToF 真实材料，继续保持约 81%。

## 4. Side-by-side 验收结论

| 验收项 | 结果 | 说明 |
| --- | --- | --- |
| PC gate schema / boundary | 通过 | 使用 `trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1` / `_summary.v1` 和 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`。 |
| Fail-closed 状态 | 通过 | 覆盖 owner ack 缺失、source 未 ready、backfill、evidence_ref mismatch、unsafe copy 和 unsupported handoff intake。 |
| Robot diagnostics safe alias | 通过 | 新增 `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary`，不触发 ACK、cursor、Nav2、serial/UART、WAVE ROVER、HIL 或 robot command。 |
| Mobile read-only panel | 通过 | 新增“受控复跑队列”，优先消费 Robot safe alias，主操作 gating 不变。 |
| 文档同步 | 通过 | 已更新 `pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`、本 sprint 留档、`OKR.md` 和 `docs/process/okr_progress_log.md`。 |
| 证据边界 | 通过 | 始终保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 |

## 5. 未通过或无法覆盖

- 无真实 route/elevator field pass。
- 无真实 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 或 delivery result。
- 无真实 WAVE ROVER/UART/HIL。
- 无真实手机设备/browser、production app 或 Objective 5 external proof。

本轮验收通过的是 metadata-only software proof 链路，不是现场交付验收。
