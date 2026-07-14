# Final - O3 TF Receipt-Time Freshness Recovery

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/`
- Closeout date：`2026-07-15 Asia/Shanghai`
- Product status：`accepted_offline_contract_repair_rejected_live_mission_credit`
- Proof boundary：`software_proof_o3_tf_receipt_time_freshness_contract_only`

## Product Acceptance 结论

本轮接受离线 TF receipt-time freshness 合同修复，拒绝 live localization、Mission Objective 0 和 OKR
credit。实现解决了上一轮 artifact 无法区分 header age 与 collector receipt/evaluation delay 的合同缺口；
但只读 SSH `date` + `ps` 显示 localization runtime inactive，所以没有部署或 live capture，不能把离线
测试结果扩张为现场证据。

## 实际改动

- Algorithm owner 完成 helper receipt-time 修复：TF transform 记录 `received_at_ms`，artifact 同时保留
  header stamp、receipt/evaluation time、`header_age_at_receipt_ms`、
  `receipt_age_at_evaluation_ms` 与 `header_age_at_evaluation_ms`。
- current observation decision 使用 callback receipt 时的 header age，即 `header_age_at_receipt_ms`，
  不是简单“receipt age”；另外两项继续诊断 collector evaluation delay 与最终 header age。
  missing/invalid receipt fail-closed，threshold 固定 `3000ms`。
- Algorithm owner 补 targeted regression 并同步导航文档与 `tech-done.md`。
- Product owner 完成 `side2side_check.md`、`final.md`、Product acceptance JSON、`OKR.md` 和
  `docs/process/okr_progress_log.md` 收口记录。

## 验证结果

- `python3 -m py_compile ...`：exit `0`。
- `python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py`：
  `Ran 160 tests in 2.244s`，`OK`。
- offline structural assertions：PASS。
- required-field `rg`：PASS。
- scoped `git diff --check`：PASS。
- live preflight：只读 SSH `date` + `ps` 显示 localization runtime inactive。

## 未执行现场验证的事实边界

- 未部署 helper，未执行 live receipt capture。
- 未写任何 ROS topic，未发布 `/initialpose`。
- 未启动或停止 runtime、map_server、AMCL、LiDAR driver 或其他现场进程。
- 未调用 planner/controller/path、NavigateToPose、`/cmd_vel`、`/api/base/manual` 或 UART。
- 没有机器人控制、route execution、delivery、HIL 或 user action。

## Mission / OKR / KR 决策

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- KR：`不归档`
- O5 约 `85%`、O6/O7 各约 `93%`、O1 约 `94%`，全部保持。

方向判断为继续 O3 的下一次真实 receipt evidence，但不再消费离线合同。O5 仍最低，然而其
production/public-cloud success-class 外部证据 blocker 未解，既有 support-only wrapper 已退役，因此
本轮切换 O3 的理由在 final 阶段仍成立。

## Safety Boundaries

- `safe_to_control=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `initialpose_published=false`
- `runtime_started_by_this_run=false`
- `runtime_stopped_by_this_run=false`

## 剩余风险

1. 尚无真实 ROS/DDS callback 的 live receipt artifact，不能证明现场字段和 freshness gate 已按预期落地。
2. `header_age_at_receipt_ms` 只表达 callback receipt 时相对 header 的 age，不证明 header clock 或物理
   定位准确；`receipt_age_at_evaluation_ms` 仅表达 collector 在 receipt 后的收口延迟。
3. runtime inactive 使本轮无法在不越权启停 runtime 的前提下完成一次只读 capture。

## 下一步

只允许两种前置之一成立后，由 `robot-algorithm-engineer` 采一次 live receipt artifact：

1. existing localization runtime 已由独立只读检查确认 active；或
2. CEO/operator 新授权 strict no-motion localization-only runtime。

仍禁止 `/initialpose`、planner/controller/path、NavigateToPose、`/cmd_vel`、`/api/base/manual`、UART、
运动、route、delivery 和 HIL。禁止把本轮离线合同再次包装成新 sprint 交付。
