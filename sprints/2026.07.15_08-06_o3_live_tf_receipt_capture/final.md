# Final - O3 Live TF Receipt Capture

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/`
- Closeout date：`2026-07-15 Asia/Shanghai`
- Product status：`accepted_current_run_receipt_artifact_blocked_missing_map_to_odom_no_okr_credit`
- Proof boundary：`live_strict_no_motion_localization_receipt_artifact_blocked_missing_map_to_odom`

## Product Acceptance 结论

本轮接受一份新的 true-board current-run TF receipt artifact，拒绝 clean localization、Mission Objective 0
与 OKR credit。唯一 live run natural exit=`2`；map_server/AMCL active，`/scan` fresh `21ms`，TF inventory
`3/3` transforms 均有 `received_at_ms`。Observed dynamic `odom->base_link` 的三类 age 为
`6/39677/39683ms`，并以 `header_age_at_receipt_ms` 做 freshness decision，证明 collector 后续约 39.7 秒
evaluation delay 没有污染 receipt-time gate。

目标 dynamic `map->odom` 仍缺失。Exact blocker 是
`amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope`、`/amcl_pose_probe_timeout` 与
`map_to_odom_dynamic_source_missing`。本轮没有发布 `/initialpose`，不能把相邻 edge 的 receipt 数据复制成
目标 edge 成功证据。

## 实际改动与证据

- Algorithm 未改 helper、测试、ROS interface、launch/config 或硬件配置。
- 更新 `docs/navigation/field_route_evidence_preflight.md`，记录 current live receipt、三类 age、exact blocker
  与 cleanup 边界。
- 当前 sprint 新增完整 planning/engineering/artifact/acceptance/final 留档；primary artifact 为
  `artifacts/algorithm/runtime-proof.json`，capture envelope 和 structure assertion 提供摘要与复算证据。
- Product 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`；主百分比保持 flat，KR `不归档`。

## 验证结果

- `python3 -m py_compile ...`：exit `0`。
- `python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py`：
  `Ran 160 tests in 2.267s`，`OK`。
- `python3 -m json.tool .../artifacts/algorithm/runtime-proof.json >/dev/null`：exit `0`。
- structure assertion：`live_tf_receipt_capture_structure_assertions_ok`。
- required anchor `rg`：PASS。
- scoped `git diff --check`：PASS。

## Safety 与 Cleanup

- `initialpose_publish_attempts=0`、`initialpose_published=false`。
- `path_generation_requested=false`、`path_generation_attempted=false`、`path_generated=false`。
- planner/controller 未启动；`uses_base_uart=false`、`publishes_cmd_vel=false`、
  `calls_base_manual=false`、`robot_control_executed=false`。
- `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。
- helper-owned process-group cleanup residual=`0`，post inventory localization/helper residual=`0`。

## Mission / OKR / KR 决策

- `current_run_artifact_delta=true`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- O5 约 `85%`、O6/O7 各约 `93%`、O1 约 `94%`，全部保持。
- KR：`不归档`；无已完成 KR 移入历史区。历史证据写入
  `docs/process/okr_progress_log.md`，当前证据保留在本 sprint。

O5 live tunnel 只读审计的 exact blocker 仍是当前上位机缺 tunnel/provider runtime、public endpoint、
TLS/DNS 与 credential；这不是 external production evidence。O5 的 preflight/readback/export/browser/voice/
packet/mock wrapper 继续退役，不得以相邻包装重开。

## 方向判断

方向为 `继续 O3，但替换重复抓手`。本轮已经再次证明无 initial pose 时 AMCL 不产生 current pose 与
dynamic `map->odom`，因此下一 sprint 不得重复启动同样的无初始位姿 runtime。只有以下材料之一出现才继续：

1. verified persisted pose，可直接进入只读目标 edge capture；
2. CEO/operator 对新 sprint 的 explicit controlled localization input 授权；
3. O5 success-class public-cloud endpoint/TLS/runtime external evidence，可切回最低 Objective。

planner/controller/path、NavigateToPose、`/cmd_vel`、`/api/base/manual`、UART、运动、route、delivery 与 HIL
仍需独立授权和对应 Engineer 验收，不能从本 sprint 推导。

## 剩余风险

1. 尚无 current dynamic `map->odom` receipt age，不能证明目标 localization TF freshness clean。
2. `odom->base_link` receipt-time clean 不等于 physical localization ground truth 或 map-to-base chain clean。
3. O5 仍被真实 public-cloud/tunnel 外部条件阻塞；只读审计没有形成 production endpoint 证据。
4. 本轮虽有 `current_run_artifact_delta=true`，但没有 external/control/user-action delta，仍低于 Mission
   Objective 0。
