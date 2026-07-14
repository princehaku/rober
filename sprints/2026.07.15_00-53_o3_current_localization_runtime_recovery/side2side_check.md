# Side-to-Side Check - O3 Current Localization Runtime Recovery

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_00-53_o3_current_localization_runtime_recovery/`
- Product owner: `product-okr-owner`
- Engineering owner: `robot-algorithm-engineer`
- Product status: `accepted_live_runtime_recovery_fresh_scan_exact_blocker_cleanup_no_okr_credit`
- Proof boundary: `robot_runtime_o3_strict_no_motion_localization_runtime_active_but_initial_pose_pose_sample_dynamic_map_to_odom_fail_closed_only`

## Side-to-Side 验收

| PRD 口径 | Final Attempt 证据 | Product 决定 |
| --- | --- | --- |
| localization-only runtime | map_server/AMCL active，local/remote SHA 均为 `75e5722f...` | 接受 live runtime recovery |
| current `/scan` | sample observed，age `22ms`，状态 `fresh` | 接受 fresh scan |
| current `/amcl_pose` | endpoint visible，但 `sample_count=0`、freshness `not_observed` | 拒绝 clean localization |
| dynamic `map->odom` | AMCL `/tf` endpoint visible，但 edge/source/timestamp 均 missing | 拒绝 clean localization TF |
| fail-closed 与 cleanup | natural exit `2`、pull `0`、elapsed `97.743s`、PGID residual `0` | 接受 blocker 与 cleanup |
| route/delivery/HIL | 未请求 path、未控制机器人、无 delivery/operator evidence | 全部拒绝 |

## Exact Blocker 与安全边界

- Primary exact blocker：`amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope`。
- 继发 blocker：`/amcl_pose_once_not_observed`、`map_to_odom_dynamic_source_missing`。
- AMCL log 明确要求 initial pose；本轮 initialpose forbidden，Product 不追认也不补授权。
- 本轮没有 initialpose、planner/controller、NavigateToPose、`cmd_vel`、base/manual 或 UART 控制。

## Product 接受与拒绝

- 接受：真实上位机 localization runtime recovery、map_server/AMCL active、fresh `/scan`、exact blocker、helper-owned cleanup。
- 拒绝：clean `/amcl_pose`、dynamic `map->odom`、clean localization、path generation、route execution、delivery、HIL、safe-to-control。
- 固定 `safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。
- `okr_credit=false`；KR `不归档`。

## OKR/KR 决策

- O5=`85%`，仍最低；因缺 production external evidence，执行 `O5 no-repeat` 跳过。
- O1=`94%`、O6=`93%`、O7=`93%`，全部保持。
- 本轮缩窄真实现场 blocker，但没有形成新的 mission-success class，主百分比不调整。

## 验证证据

- 本地：`py_compile` 通过；`Ran 148 tests in 2.261s`，`OK`；required `rg` 与 scoped diff 通过。
- 现场：最终 helper local/remote SHA 一致；runtime natural exit `2`，pull exit `0`。
- Window：`2026-07-14T17:24:46Z` 至 `17:26:25Z`；summary elapsed `97743ms`。
- Cleanup：helper PGID `643654` residual `0`，未使用 `pkill`/`killall`，既有进程保留。

## 剩余风险与下一步

- AMCL 在未初始化时不会输出 pose 或 dynamic `map->odom`；endpoint visible 不能替代 current sample。
- graph CLI timeout 仍是 secondary diagnostic，但不覆盖 initial-pose primary blocker。
- 下一轮只能由 Product/CEO 明确授权受控无运动一次 `/initialpose`，或授权并验证 persisted initial pose。
- 获授权后复用 localization-only collector，先验收 fresh `/amcl_pose` 与唯一 dynamic `map->odom`；仍不得进入 planner/controller。
