# Sprint 2026.05.18_07-08 Route Task Material Review Operator Drill - Final

sprint_type: epic

## 1. 本轮结论

本轮完成 `software_proof_docker_route_task_field_retest_operator_drill_gate` 的 review-decision input upgrade。`route_task_field_retest_operator_drill` 现在优先消费 `route_task_field_retest_material_callback_review_decision` artifact / summary / wrapper / nested diagnostics，保留 material pack 兼容，并在 mixed wrapper 中优先 review decision。

Robot diagnostics 新增 `robot_diagnostics_route_task_field_retest_operator_drill_summary` output alias，支持 nested/top-level discovery，对 review-decision-derived raw fields 做 fail-closed filtering。mobile/web 首屏“现场操作演练”承接 material callback review decision，展示 source decision、operator drill status、safe `evidence_ref`、commands、checklist、outputs、rerun 和 evidence boundary，copy/export whitelist-only。

本轮没有把 software proof 写成真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 2. OKR 最低优先级核对复核

tech-plan 中的最低优先级核对仍成立：

- 当前数值最低 Objective 仍是 Objective 5，约 68%。
- 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof，因此 Objective 5 不应因本轮上调。
- 下一低项 Objective 1 约 81%。本轮没有真实 WAVE ROVER、UART、串口/topic samples、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 真实 2D LiDAR / ToF source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料，因此 Objective 1 不应因本轮上调。
- 本轮选择 Objective 2 / 3 / 4 仍合理，因为 PR #4 route/elevator field materials 需要一个从 material callback review decision 到 operator drill 的可执行软件层，避免现场执行回退到旧 material pack-only checklist。

## 3. OKR 进度影响

- Objective 1：保持约 81%。本轮不新增硬件事实、不触碰 WAVE ROVER/UART/HIL，不解决 PR #5 hardware baseline / vendor source 的真实材料缺口。
- Objective 2：保守保持约 99%。本轮增强 route/elevator assisted delivery 的现场 operator drill 软件链，但没有真实电梯、真实门状态、真实楼层确认、真实人工协助记录、真实 dropoff/cancel completion 或 delivery result。
- Objective 3：保守保持约 99%。本轮把 Nav2/fixed-route runtime log、route completion signal、task record 等材料的 review decision 转成 operator drill，但没有真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据、route completion signal 或 task record。
- Objective 4：保守保持约 99%。本轮手机首屏只读展示更完整，但没有真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 或现场 phone behavior。
- Objective 5：保持约 68%。本轮没有任何真实 external proof，也没有推进 cloud/4G/OSS/CDN/DB/queue/worker/cutover。

## 4. 验证汇总

A / Autonomy：

```text
py_compile pass
focused unittest: Ran 6 tests in 0.024s OK
required rg pass
scoped diff check pass
```

B / Robot：

```text
py_compile pass
diagnostics unittest: Ran 175 tests OK
required rg pass
scoped diff check pass
```

C / Full-stack：

```text
node --check mobile/web/app.js pass
mobile unittest: Ran 72 tests OK
required rg pass
scoped diff check pass
```

Product closeout：

```text
required rg pass
scoped git diff --check pass
```

## 5. 剩余风险和下一步

剩余风险没有被本轮消除：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 仍是全链路边界。

下一步若仍没有 Objective 5 external proof 或 Objective 1 real hardware proof，最有价值的路线是把本轮 operator drill 带到 PR #4 受控现场材料回填：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result。若拿到 Objective 4 真实手机/browser/device 材料，也可以用它补手机验收缺口。若拿到 PR #5 真实 2D LiDAR / ToF 材料，应走 hardware material intake / review / HIL-entry 链路，而不是继续本地包装硬件 blocker。
