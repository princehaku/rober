# Final - O3 Controlled Initialpose Localization Proof

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_04-55_o3_controlled_initialpose_localization_proof/`
- Closeout time: `2026-07-15 05:38 Asia/Shanghai`
- Product status: `blocked_fail_closed_current_live_initialpose_delta_tf_freshness_rejected_no_okr_credit`
- Proof boundary: `robot_runtime_o3_strict_no_motion_controlled_initialpose_localization_proof_only`

## Product Acceptance 结论

本轮接受 current live strict-no-motion 定位 artifact delta，但拒绝 clean localization 与 OKR credit。
canonical pose、pre-gate、一次 `/initialpose`、fresh `/scan`、fresh `/amcl_pose`、dynamic `map->odom`
观测/parsed stamp/唯一 AMCL 归因和 clean cleanup 均有现场材料；然而 TF age=`5090ms` 超过 `3000ms`
门槛，post gate 唯一 blocker=`map_to_odom_fresh`，因此必须以 blocked/fail-closed 收口。

## 实际改动

- Algorithm owner 实现 persisted pose 审计、canonical free-cell/world-pose 审计、写前 gate、单次
  `/initialpose` 限额、写后 fresh pose/TF gate 与 helper-owned cleanup，并补齐 `155` 项 targeted tests、
  现场 artifacts 和 `tech-done.md`。
- Product owner 本轮新增 `side2side_check.md`、`final.md` 与
  `artifacts/product_acceptance_controlled_initialpose_localization_proof.json`，并保守更新 `OKR.md` 与
  `docs/process/okr_progress_log.md`。
- Product 未修改工程代码、tests、Algorithm artifacts 或 `tech-done.md`。

## 接受的现场事实

- Canonical map pose：`frame_id=map`、`x=0.8011511639109115`、`y=4.12500006146729`、`yaw=0.0`；
  free cell=`row 30 / column 125 / pixel 254`。
- `pre_initialpose_gate.clean=true`；map_server/AMCL active，fresh `/scan`，`/initialpose` subscriber
  count=`1` 且归属 `/amcl`，persisted/canonical/TF authority gate clean。
- Final `initialpose_publish_attempts=1`、attempted=`true`、published=`true`，method 为
  `ros2_topic_pub_once_cli_fallback`。
- Post-write `/scan` age=`22ms`；`/amcl_pose` age=`96ms`、frame=`map`、header stamp parsed。
- Dynamic `map->odom` observed、source class=`dynamic`、header stamp parsed、publisher attribution=
  `attributed_unique_amcl`。
- Helper PGID `648519` identity verified、cleanup residual=`0`、graph diff=`0` 行；既有 LiDAR、ESP32
  bridge 与 Upper API 保持。

## 拒绝项与失败定位

- `map->odom` freshness age=`5090ms`，超过 threshold=`3000ms`，status=`stale`。
- Post-write gate 唯一 blocker 是 `map_to_odom_fresh`；runtime exit=`2`、clean assertion exit=`1`。
- 首轮写前失败时 `initialpose_publish_attempts=0`、attempted/published=`false`。失败定位为三行
  `origin` parser 与 `/initialpose` endpoint summary 保留问题；Engineer 修复后才执行唯一发布 run。
- 修复后唯一 run 已发布 1 次；此后没有重跑。本 sprint 永远不得再发布 `/initialpose`，也不得用
  wrapper 或 read-only collector 改名复用该额度。
- `ros2_node_list_timeout` 是 secondary diagnostic，不覆盖唯一 post-gate blocker。

## Mission / OKR / KR 决策

- `current_run_artifact_delta=true`；`external_artifact_delta=false`、`live_control_delta=false`、
  `user_action_delta=false`。
- Mission Objective 0 与 mission closure 仍未满足；本轮没有 route、delivery/operator、current HIL、
  production cloud 或 user action 增量。
- O5 约 `85%` 且仍最低，production/cloud blocker 继续跳过，不再消费 support wrapper。
- O1 约 `94%`、O6/O7 各约 `93%`，主百分比不调整；`okr_credit=false`，KR `不归档`。
- 固定 `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、
  `delivery_success=false`、`hil_pass=false`。
- 本轮不证明真实物理位姿、clean localization、path/route、delivery/operator acceptance、HIL、
  safe-to-control 或 production cloud。

## 验证结果

- Engineering：`python3 -m py_compile` PASS；targeted unittest `Ran 155 tests`、`OK`；required-field
  `rg` 与 scoped `git diff --check` PASS。
- Live structural gate：PASS，日志为
  `controlled_initialpose_localization_structural_gate_ok_post_gate_blocked_only_map_to_odom_fresh`。
- Expected fail-closed gate：`runtime.exit=2`、`runtime_clean_gate.exit=1`；失败原因只为 stale
  `map_to_odom_fresh`。
- Product closeout：runtime/Product JSON `json.tool`、Product 结构断言、required anchor `rg` 与 scoped
  `git diff --check` 均通过。

## 剩余风险

1. Canonical free cell 不证明机器人真实物理位置就是该坐标，本轮无 ground truth。
2. Artifact 不能区分 AMCL 静止时不持续刷新 TF，还是 collector 在早期采样后延迟约 5 秒才做统一判定。
3. Dynamic TF 已观察且归因明确，但 freshness 不合格，不能放宽 clean localization 准入。
4. 本轮没有 planner/controller/path、motion、route execution、delivery/operator、HIL 或 production cloud。

## 下一轮建议

由 `robot-algorithm-engineer` 优先做 no-topic-write、no-motion 的 TF receipt-time 与 header-stamp 根因
分析；若只靠现有 artifact 即能确认 collector 判定延迟，先离线修复并跑测试。不要再做 wrapper，也不要
再次 initialpose。任何新的 live localization write 都必须进入新 sprint，并获得新的明确授权。
