# Sprint 2026.05.15_02-03 Route Task Field Run Review Console - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `software_proof_docker_route_task_field_run_review_console_gate`，把上一轮 field-run intake/crosscheck 推进为 operator/support 可读的 review console、Robot diagnostics metadata-only summary 和 mobile 只读复核 panel。

OKR 口径：Objective 2、Objective 3 从约 84% 保守上调到约 85%。Objective 5 仍是最低约 68%，但无真实外部材料，不上调。Objective 1、Objective 4 不调整。

## 2. 用户价值、北极星和 KR

- 用户价值：现场人员能直接看到复核结论、缺失/不一致材料、重跑命令和下一步，不必手动理解多份 JSON。
- 产品北极星：为普通手机用户的低成本 ROS2 垃圾投递闭环补齐可复盘、可解释、可继续采证的现场材料链。
- Objective 2：推进任务记录和失败/复核闭环。
- Objective 3：推进固定路线/route task 现场材料复核流程。
- Objective 5：仍需真实外部云/4G/OSS/CDN/DB/queue proof，本轮不覆盖。

## 3. 实际交付

Task A `autonomy-engineer` 完成 review console artifact 和 targeted tests，交付 `trashbot.route_task_field_run_review_console.v1`。

Task B `robot-software-engineer` 完成 diagnostics metadata-only summary，支持 explicit ref 与两个环境变量入口，并保持动作/ACK/cursor/HIL/delivery success 隔离。

Task C `full-stack-software-engineer` 完成 mobile 只读 review panel，消费 `trashbot.route_task_field_run_review_summary.v1` 并保留 source artifact `trashbot.route_task_field_run_review_console.v1`，Start/Confirm/Cancel gating 不变。

Task D `product-okr-owner` 完成 sprint closeout、`OKR.md` 4.1 和 `docs/process/okr_progress_log.md` 更新。

## 4. 验证结果

工程 worker 已报告：

- Task A：py_compile pass；`test_route_task_field_run_review.py` `Ran 6 tests OK`；`--help` pass；required rg pass；scoped diff check pass。
- Task B：py_compile pass；diagnostics unittest `Ran 59 tests OK`；required rg pass；scoped diff check pass。
- Task C：mobile unittest `Ran 10 tests OK`；py_compile pass；`node --check` pass；required rg pass；scoped diff check pass。

Task D closeout 验收：

```bash
rg -n "2026.05.15_02-03_route-task-field-run-review-console|software_proof_docker_route_task_field_run_review_console_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_02-03_route-task-field-run-review-console
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_02-03_route-task-field-run-review-console/tech-done.md sprints/2026.05.15_02-03_route-task-field-run-review-console/side2side_check.md sprints/2026.05.15_02-03_route-task-field-run-review-console/final.md
```

Closeout 命令已通过，关键输出：`rg` 找到本 sprint、boundary、Objective 2、Objective 3、Objective 5、`not_proven`、delivery success 和 HIL 边界；`git diff --check` 无输出、退出 0。

## 5. 失败定位和返工

- Task A 首轮 mismatch decision reason 未明确包含 same `evidence_ref`，已修复并复验。
- Task C 首轮 mobile schema drift，从 `trashbot.route_task_field_run_review.v1` 对齐到 Robot diagnostics summary schema `trashbot.route_task_field_run_review_summary.v1`，已复验通过。
- Task D closeout 未发现验证失败。

## 6. 剩余风险

本轮不是真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion、delivery success 或 O5 external proof。

下一轮如果仍没有 O5 真实外部材料，应避免继续堆 O5 local metadata；O2/O3 若继续推进，应该转向真实路线/任务材料采集或同一 `evidence_ref` 的上车复账。
