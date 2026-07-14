# Final - O3 Current Localization Runtime Recovery

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.15_00-53_o3_current_localization_runtime_recovery/`
- Closeout time: `2026-07-15 01:34 Asia/Shanghai`
- Product status: `accepted_live_runtime_recovery_fresh_scan_exact_blocker_cleanup_no_okr_credit`
- Proof boundary: `robot_runtime_o3_strict_no_motion_localization_runtime_active_but_initial_pose_pose_sample_dynamic_map_to_odom_fail_closed_only`

## Product Acceptance 结论

本轮接受真实上位机 strict-no-motion localization runtime recovery、fresh `/scan`、精确 initial-pose blocker
和 helper-owned clean cleanup。最终现场并未得到 `/amcl_pose` sample 或 AMCL dynamic `map->odom`，因此拒绝
clean localization、route execution、delivery、HIL、safe-to-control 和 OKR credit。

## 实际推进

- Local/remote helper SHA 均为 `75e5722f1a050df5174d52fffa7df40302dbbb31bb498bab1550a297d0a1e9b2`。
- Final Attempt natural exit `2`、pull exit `0`、elapsed `97.743s`，不是 outer timeout。
- map_server 与 AMCL active；`/scan` sample fresh，age `22ms`。
- `/amcl_pose` endpoint visible，但 `sample_count=0`、timestamp 未解析、freshness `not_observed`。
- AMCL `/tf` publisher endpoint visible，但 dynamic `map->odom` edge/source/timestamp missing。
- Helper-owned PGID `643654` cleanup residual `0`，既有 LiDAR、ESP32 bridge 与 Upper API 保留。

## Exact Blocker

- Primary：`amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope`。
- Secondary：`/amcl_pose_once_not_observed`、`map_to_odom_dynamic_source_missing`。
- AMCL log 要求 initial pose，而本轮 initialpose forbidden；Product 本轮不自行授权或执行。
- `ros2_node_list_timeout` 仅为 secondary diagnostic，不覆盖上述物理定位根因。

## OKR / KR 决策

- O5=`85%`，仍为最低 Objective；production external evidence 缺失，继续执行 `O5 no-repeat` 跳过。
- O1=`94%`、O6=`93%`、O7=`93%`，全部保持，主百分比不调整。
- `okr_credit=false`，本轮 KR `不归档`。
- 现场 blocker 被缩窄，但没有 mission-success、route/delivery 或 HIL 增量。

## Safety 与拒绝声明

- `safe_to_control=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- 同时 `publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`。
- 不证明 clean localization、path generation、route execution、delivery/operator acceptance、current HIL 或 O5 success。

## 实际改动与验证

- Engineering 实际实现、测试、live artifacts 与 `tech-done.md` 由 Algorithm owner 留档。
- Product 本轮只新增 `side2side_check.md`、`final.md`、Product acceptance JSON，并更新 `OKR.md` 与进度日志。
- 本地证据：`py_compile` exit `0`；`Ran 148 tests in 2.261s`、`OK`；required `rg` 与 scoped diff 通过。
- Product closeout 验证：acceptance JSON `json.tool`、结构断言、required anchor `rg`、scoped `git diff --check`。

## 剩余风险

1. AMCL 未获得 initial pose，无法形成 current `/amcl_pose` 与 dynamic `map->odom`。
2. Endpoint visibility 不等于 current message/timestamp/freshness，不能放宽 clean contract。
3. Helper-managed static TF 与既有 TF authority 仍有重复风险，未获授权不得改 launch/config。
4. Graph CLI timeout 仍可能发生，但已是 secondary diagnostic；cleanup 当前仅证明 helper-owned PGID clean。

## 下一轮唯一建议

由 Product/CEO 明确二选一授权：受控无运动发布一次 `/initialpose`，或使用并验证 persisted initial pose。
授权前不得执行。授权后复用同一 localization-only collector，仅验收 fresh `/amcl_pose` 与唯一 AMCL dynamic
`map->odom` endpoint/timestamp/freshness，仍禁止 planner/controller、NavigateToPose、path opt-in 和 motion。
