# Final - O3 Dynamic TF Source and LiDAR Status Semantics

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/`
- Closeout time: 2026-07-15 00:27 Asia/Shanghai
- Product owner: `product-okr-owner`
- Engineering owners: `robot-software-engineer`, `robot-algorithm-engineer`
- Product status: `accepted_robot_software_live_clean_algorithm_live_fail_closed_no_okr_credit`
- Proof boundary: `product_acceptance_o3_o1_dynamic_tf_source_and_lidar_status_semantics_fail_closed_no_mission_credit`

## Product Acceptance 结论

Product 接受 Robot Software 的 LiDAR status current/reference semantics 为现场 clean readback，同时接受
Algorithm 的 dynamic TF source inventory 为有根因的现场 fail-closed 证据。由于两个 lane 未在现场同时
clean，整轮 `overall_clean=false`，不接受 clean dynamic TF source、路线执行、送达、HIL、
safe-to-control 或 O5 success 声明。

## 实际推进

Robot Software lane 已关闭上一轮 `150000` current 与 `230400` synthetic/reference 的语义歧义：

- lifecycle `8/8`、Upper API `2/2` 通过；现场 PID 为 `550851`。
- holder、PID-matched persisted status、diagnostics 与 API 都读回 `/dev/ttyACM0@150000`。
- vendor `230400` 明确为 `reference_only_not_current`。
- SSH/API exit 均为 `0`；local/remote script SHA 一致。

Algorithm lane 本地 `py_compile`、145 tests、JSON/assert/diff 均通过，但最终现场 capture natural exit
`2`。现场 deploy/install/pull 均 exit `0`，capture 用时 `68.562s` 且 capture-time SHA match；当前
graph 中 `/tf` 唯一 publisher 是 `/esp32_bridge`，dynamic transform 只有 `odom->base_link`，没有
`/amcl`、没有 `/map_server`，因此不能归因 AMCL dynamic `map->odom` source。

最终 capture 后才完成的 compact child repair 没有重新部署或现场复验，必须保持
`local_fix_not_live_verified`，不能用本地 145 tests 替代 live acceptance。

## 用户价值与北极星

本轮消除了现场 LiDAR baudrate “current 值还是资料参考值”的歧义，并把 dynamic TF source 的阻塞从
泛化 `/tf` 缺失收紧到 current graph 缺少 map/AMCL runtime 与 AMCL endpoint。这降低了下一次现场
复验的定位成本，但北极星仍是可验证送达；本轮没有路线执行、送达或 operator acceptance，故不计
mission closure。

## OKR / KR 决策

- O5 继续约 `85%`，仍是最低 Objective；没有 success-class production/cloud evidence。
- O1 继续约 `94%`；LiDAR status semantics clean 不等于 current HIL 或 route execution。
- O6/O7 继续各约 `93%`。
- 主百分比不调整，OKR credit 为 false，本轮 KR `不归档`。
- O5 no-repeat 跳过理由仍成立；不得再消费 status/readiness/export/browser/voice wrapper。

## 实际改动

Engineering owner 的实际实现、测试、现场 artifacts 与 `tech-done.md` 由各 owner 留档。Product closeout
只新增/更新：

- `side2side_check.md`
- `final.md`
- `artifacts/product_acceptance_dynamic_tf_source_and_lidar_status_semantics.json`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Product 未修改 Engineer code、tests、hardware configuration、engineering artifacts 或 `tech-done.md`。

## 验证结果

Engineering 证据：Robot Software lifecycle `8/8`、Upper API `2/2`；Algorithm `Ran 145 tests ... OK`，
并完成 `py_compile`、JSON、结构断言与 diff check。现场 Robot Software lifecycle/API exit `0/0`；
Algorithm deploy/install/pull exit `0/0/0`，capture natural exit `2`。

Product closeout 执行并要求通过：acceptance JSON `json.tool`、Product structural assertion、required
anchor `rg` 和 scoped `git diff --check`。

## 失败定位

Algorithm clean contract 的 exact blocker 是 current existing ROS graph 未运行 `/map_server` 与
`/amcl`，因此没有 AMCL TF publisher endpoint；现有 `/tf` 只由 `/esp32_bridge` 发布
`odom->base_link`。同时 sourced rclpy child JSON 在 parent parse 前被 8KB 截断。后者已有本地修复，
但 `local_fix_not_live_verified`，所以不能覆盖最终 live capture exit `2`。

## Safety 和拒绝声明

本轮固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

不证明 clean dynamic TF source、route execution、delivery/operator acceptance、current live HIL、
safe-to-control、WAVE ROVER movement 或 O5 external success。

## 剩余风险与下一轮建议

1. `robot-algorithm-engineer`：只启动或确认 current `/map_server` 与 `/amcl` runtime，然后在同一
   strict no-motion window 重试 compact dynamic TF source collector；不要带 planner。
2. 若 runtime 启动后仍无 AMCL endpoint，保留 endpoint/QoS/timestamp/freshness 的 exact blocker，
   不再包装 status/readiness/export/browser/voice artifact。
3. 只有 explicit operator approval 与 current HIL 到位后，才进入 controlled route evidence；之后仍需
   delivery/operator acceptance 才可讨论 mission closure。
