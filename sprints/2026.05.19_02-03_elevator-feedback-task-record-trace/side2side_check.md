# Sprint 2026.05.19_02-03 Elevator Feedback Task Record Trace - Side2Side Check

## sprint_type: epic

Run time: 2026-05-19 02:11 Asia/Shanghai

## 用户价值和产品北极星

验收对照目标：field owner 能在任务后把手机实时阶段、Robot task_record、operator diagnostics 和 mobile/web post-run panel 放到同一 `evidence_ref` 下复盘，而不是只看实时 UI 或口头描述。北极星仍是普通手机用户可解释、可恢复、可复盘地完成低成本 trash delivery。

## OKR 映射

- Objective 2：通过 `elevator_action_feedback_trace` 增强电梯 assisted delivery 的 task record / diagnostics 可复盘性。
- Objective 4：通过只读 post-run panel 增强手机端解释能力。
- Objective 1 / Objective 3 / Objective 5：不因本轮上调；没有真实硬件、真实 route/Nav2/fixed-route runtime 或 external cloud proof。

## Side-by-side 验收

| 验收项 | 期望 | 实际 | 结论 |
| --- | --- | --- | --- |
| Robot post-run trace | task_record 持久化 elevator phase trace | Robot worker 实现 `elevator_action_feedback_trace`，并通过 focused unittest | 通过 |
| Diagnostics safe summary | 暴露 phone-safe 只读摘要 | diagnostics alias 为 `robot_diagnostics_elevator_action_feedback_trace_summary` | 通过 |
| Mobile post-run panel | 展示 trace，不改变主操作 gating | Full-Stack worker 新增只读 panel，Start Delivery / Confirm Dropoff / Cancel gating 不变 | 通过 |
| 边界 flags | 保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | Worker 验证与 Product rg 均覆盖这些关键字 | 通过 |
| 命名偏差 | planning 草案命名不得阻塞实现 | accepted deviation：`elevator_feedback_task_record_trace` -> `elevator_action_feedback_trace` / `robot_diagnostics_elevator_action_feedback_trace_summary` | 接受 |
| PR #4 / PR #5 边界 | 不把 software proof 写成真实材料 | OKR / final 保留 PR #4 route/elevator field materials 与 PR #5 2D LiDAR / ToF 缺口 | 通过 |

## 需要做什么

本轮已完成 Product closeout。下一步不要继续堆本地 O5 wrapper；若有真实材料，优先回填 PR #4 受控现场材料、O1 WAVE ROVER/UART/HIL packet 或 PR #5 2D LiDAR / ToF 采购/安装/HIL-entry 材料。

## 优先级和验收口径

P0 验收通过：Robot / diagnostics / mobile 三侧均可表达 post-run elevator action feedback trace，且不启用控制、不声明 delivery success。

P1 验收通过：docs/product 和 docs/interfaces 已由 workers 同步更新，Product closeout 同步 `OKR.md` 与 `docs/process/okr_progress_log.md`。

不通过或未覆盖项：真实电梯、真实路线、真实手机、HIL、Objective 5 external proof 均未发生；这些不是本轮验收范围。

## 对应责任 Engineer

- Robot Platform Engineer：trace 持久化、operator gateway、diagnostics summary、Robot tests。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 panel、fixtures、前端验证。
- Product Manager / OKR Owner：本 side2side、final、OKR 和进度日志收口。

## 风险、阻塞和需要补齐的证据链

- 真实 field owner 仍需补 PR #4 材料：门状态、楼层确认、人工协助、Nav2/fixed-route runtime、真实 task_record/completion signal、dropoff/cancel completion、delivery result。
- 硬件 owner 仍需补 PR #5 材料：2D LiDAR / ToF SKU/source、receipt、procurement、installation、wiring、power、calibration、HIL-entry。
- Cloud/O5 owner 仍需补真实 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或 external proof。
