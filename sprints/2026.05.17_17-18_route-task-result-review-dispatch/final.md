# Sprint 2026.05.17_17-18 Route Task Result Review Dispatch - Final

sprint_type: epic

## 1. Final 状态

状态：`DONE_SOFTWARE_PROOF_DOCKER_ONLY`。

Product closeout 已按完成收口。A/B/C workers 的 PC gate、Robot diagnostics 和 mobile/web panel 均已落地，并通过各自围栏验证。`software_proof_docker_route_task_field_retest_result_review_dispatch_gate` 可用于把上一轮 result backfill review decision 转成现场派发、owner work orders、callback packet requirements 和 rerun commands。

## 2. 用户价值和产品北极星

用户价值：下一次真实 route/elevator result materials 回填前，现场支持可以按同一 `evidence_ref` 明确谁补什么、回调包要带什么、哪些命令要重跑、哪些 accepted materials 不应重复采集、哪些 rejected materials 必须退回重做。

产品北极星仍是低成本 ROS2 自主垃圾投递机器人闭环；本轮把 PR #4 elevator-assisted delivery 的材料链推进到现场派发，不证明真实送达、HIL、真实手机/browser 或 Objective 5 external proof。

## 3. OKR 映射与进度处理

- Objective 2：从约 97% 保守更新到约 98%。原因是 route/elevator result backfill review decision 已进入现场 dispatch，door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 后续可按 owner work orders、callback packet requirements 与 rerun commands 处理。
- Objective 3：从约 97% 保守更新到约 98%。原因是 Nav2/fixed-route runtime log、route completion signal、task record 的材料状态、同一 `evidence_ref` 约束、复跑命令和回调包要求已进入 PC / Robot / mobile 共同只读派发层。
- Objective 5：保持约 68%。它仍是数值最低 Objective，但当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1 保持约 77%，Objective 4 保持约 99%。

## 4. 本轮核心抓手与实际结果

核心抓手：`route_task_field_retest_result_review_dispatch`。

实际结果：

- PC gate 输出 `trashbot.route_task_field_retest_result_review_dispatch.v1` / `_summary.v1`。
- Robot diagnostics 新增 metadata-only consumer `route_task_field_retest_result_review_dispatch` / `_summary`。
- mobile/web 新增只读“路线任务现场派发” panel，copy/export 由 `safe_copy` 白名单授权，缺失显示 `blocked copy unavailable`。
- Sprint closeout、OKR 和 progress log 已按真实完成状态更新。

## 5. PR #4 / PR #5 边界

- PR #4：elevator-assisted delivery 是主线。本轮选择 O2/O3 是为了继续推进上一轮 backfill review decision 后的现场 dispatch；本轮已把 PR #4 route/elevator 材料链从结果回填复核决策推进到现场派发。
- PR #5：hardware materials 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。当前不继续包装该 blocker，也不把本地 software proof 写成硬件进展。

## 6. 验证结果

Task A / Autonomy：

```text
py_compile pass
focused unittest Ran 5 tests in 0.061s OK
CLI --help pass
required rg pass
scoped git diff --check pass
```

Task B / Robot：

```text
py_compile pass
diagnostics unittest Ran 152 tests ... OK
required rg pass
scoped git diff --check pass
initial nested-summary safe_evidence_ref failure fixed and reverified
```

Task C / Full-stack：

```text
mobile unittest Ran 48 tests in 0.171s OK
node --check mobile/web/app.js pass
required rg pass
scoped git diff --check pass
initial raw-path fixture wording fixed to unsafe material reference and reverified
```

Task D / Product：

```text
required closeout rg pass
scoped git diff --check pass
```

## 7. 剩余风险和下一步

本轮仍不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实 dropoff/cancel completion、delivery success、真实手机/browser、production app、WAVE ROVER、真实串口/UART、HIL 或 Objective 5 external proof。

下一步应补真实现场材料：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record / completion signal、dropoff/cancel completion 或 delivery result。PR #5 仍需真实 2D LiDAR / ToF source、procurement、installation、wiring、power、calibration 和 HIL-entry 材料。
