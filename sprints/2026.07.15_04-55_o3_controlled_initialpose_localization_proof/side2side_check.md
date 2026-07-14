# Side-to-Side Check - O3 Controlled Initialpose Localization Proof

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_04-55_o3_controlled_initialpose_localization_proof/`
- Product owner: `product-okr-owner`
- Engineering owner: `robot-algorithm-engineer`
- Product status: `blocked_fail_closed_current_live_initialpose_delta_tf_freshness_rejected_no_okr_credit`
- Proof boundary: `robot_runtime_o3_strict_no_motion_controlled_initialpose_localization_proof_only`

## Product Acceptance 结论

本轮接受 actual current live strict-no-motion 定位证据增量：canonical pose 可审计、发布前 gate clean、一次
`/initialpose` 确实发出、fresh `/scan` 与 fresh `/amcl_pose` 可读、dynamic `map->odom` 可观察且唯一归因
AMCL、helper cleanup clean，既有 LiDAR、ESP32 bridge 与 Upper API 保持。

本轮拒绝 clean localization。`map->odom` 的 header stamp 虽已解析，但最终 age=`5090ms`，超过
threshold=`3000ms`；post-write gate 唯一 blocker=`map_to_odom_fresh`，runtime exit=`2`，clean assertion
exit=`1`。该失败必须保留，不能用其他已通过事实覆盖。

## Side-to-Side 验收

| PRD / Tech Plan 口径 | Final Artifact 证据 | Product 决定 |
| --- | --- | --- |
| canonical free-cell/world pose | `row=30,column=125,pixel=254`；`map` pose `(0.8011511639109115, 4.12500006146729, 0.0)` | 接受 canonical pose 可审计；不接受为真实物理位姿 |
| 发布前 persisted/canonical/subscriber/TF gate | `pre_initialpose_gate.clean=true`，blocking reasons 为空 | 接受 pre-gate clean |
| `/initialpose` 最多一次 | Final `initialpose_publish_attempts=1`、attempted/published=`true` | 接受一次发布；本 sprint 永久禁止再发布或 live rerun |
| fresh localization signals | `/scan` age=`22ms`；`/amcl_pose` age=`96ms` 且 stamp parsed | 接受 fresh scan/pose |
| dynamic `map->odom` 来源 | observed、source class=`dynamic`、stamp parsed、`attributed_unique_amcl` | 接受 edge/source/attribution 结构事实 |
| `map->odom` freshness | age=`5090ms` > threshold=`3000ms`，status=`stale` | 拒绝 TF freshness 与 clean localization |
| fail-closed 与 cleanup | post blocker 只有 `map_to_odom_fresh`；runtime exit=`2`；PGID `648519` residual=`0`；graph diff=`0` 行 | 接受 exact blocker 与 helper-owned cleanup |
| 既有 runtime 保持 | stable readback 仍有 `lidar_driver`、`esp32_bridge`、`upper_robot_api` | 接受 no-regression 现场事实 |
| route/delivery/HIL/production | 没有 planner、controller、path、motion、operator、HIL 或 production cloud 证据 | 全部拒绝 |

## 发布次数与失败修复链

- 首轮窗口 `2026-07-14T21:23:11Z` 至 `21:24:48Z` 写前 fail-closed：
  `initialpose_publish_attempts=0`、attempted=`false`、published=`false`，没有消费发布额度。
- 首轮失败定位为两项工程合同问题：map_saver 三行 `origin` 未被初版 parser 接受；rclpy 已看到
  `/initialpose` subscriber `/amcl`，但 endpoint summary 未保留该 topic，导致 ownership audit 误判。
- Engineer 离线修复并回归后，只执行一次最终 live run；该 run
  `initialpose_publish_attempts=1`、attempted=`true`、published=`true`。
- 最终 run 以后没有再次 live rerun。本 sprint 的一次 `/initialpose` 额度已永久用尽，后续不得以复验、
  wrapper 或 collector 修复为理由再次发布。

## Safety、Mission 与证据增量

- 固定 `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、
  `delivery_success=false`、`hil_pass=false`。
- 不证明机器人真实物理位姿、path/route、delivery/operator acceptance、HIL、production cloud 或
  safe-to-control。
- `current_run_artifact_delta=true`：本轮确有新的 current live initialpose、fresh pose 与 dynamic TF 材料。
- `external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`。
- Mission Objective 0 / mission closure 仍未满足；本轮 artifact delta 不自动转换为 OKR credit。

## OKR / KR 决策

- O5 约 `85%`，仍是最低 Objective；production/cloud success-class blocker 未变化，继续跳过其重复消费。
- O1 约 `94%`、O6/O7 各约 `93%`，全部保持；主百分比不调整。
- `okr_credit=false`；KR `不归档`，当前推进区与历史区均不迁移。
- 方向判断：继续 O3/O1 现场定位根因收敛，但暂停本 sprint 的任何 live localization write；不返回
  wrapper、browser、export、readback 或再次 initialpose。

## 验证证据

- Engineering：`python3 -m py_compile` PASS；targeted unittest `Ran 155 tests`、`OK`；required `rg` 与
  scoped diff check PASS。
- Final artifact：`runtime_structural_assertions.log` 输出
  `controlled_initialpose_localization_structural_gate_ok_post_gate_blocked_only_map_to_odom_fresh`。
- Expected fail-closed：`runtime.exit=2`；`runtime_clean_gate.exit=1`；clean assertion 保守失败于 stale TF。
- Runtime safety：forbidden command scan PASS；cleanup identity verified、residual=`0`；graph cleanup diff 为空。

## 剩余风险与下一轮方向

- 当前 artifact 不能区分 AMCL 在静止窗口不持续刷新 TF，还是 collector 在接收 transform 后到统一
  freshness 判定之间消耗约 5 秒。
- 下一轮优先由 `robot-algorithm-engineer` 做严格 read-only、no-topic-write、no-motion 的 TF receipt-time
  与 header-stamp 根因分析。若现有 artifact 已足够证明 collector 判定延迟，先离线修复并测试。
- 任何新的 live localization write 必须由新的明确授权与新 sprint 承载；不得复用本 sprint 的一次额度。
