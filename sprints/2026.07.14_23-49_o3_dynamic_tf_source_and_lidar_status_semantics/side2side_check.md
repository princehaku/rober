# Side-to-Side Check - Dynamic TF Source and LiDAR Status Semantics

## Sprint Metadata

- `sprint_type: epic`
- Sprint: `sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/`
- Product owner: `product-okr-owner`
- Acceptance time: 2026-07-15 00:27 Asia/Shanghai
- Product status: `accepted_robot_software_live_clean_algorithm_live_fail_closed_no_okr_credit`
- Proof boundary: `product_acceptance_o3_o1_dynamic_tf_source_and_lidar_status_semantics_fail_closed_no_mission_credit`

## Product 对照结论

本轮有两个可独立接受的结果，但不能合并写成 clean：Robot Software 的 LiDAR status
current/reference semantics 已完成现场 clean readback；Algorithm 的 dynamic TF source inventory 在最终现场窗
fail-closed。两个 lane 没有同窗同时 clean，因此整轮 `overall_clean=false`，不进入路线执行、送达或 OKR
计分口径。

| PRD / 验收面 | 计划口径 | 实际证据 | Product 判定 |
| --- | --- | --- | --- |
| LiDAR current 状态 | current runtime 与 vendor reference 必须分开 | PID `550851`，holder、PID-matched status、diagnostics 与 API 均为 `/dev/ttyACM0@150000`；`230400` 为 `reference_only_not_current` | 通过，Robot Software lane clean |
| LiDAR 现场可复验 | SSH/API 退出码为 0，部署脚本一致 | lifecycle/API exit 均为 `0`；local/remote SHA 均为 `5e65abc3...` | 通过 |
| Dynamic TF source | current graph 中找到并归因 AMCL dynamic `map->odom` publisher | `/tf` 唯一 publisher 为 `/esp32_bridge`，仅观察 `odom->base_link`；无 `/amcl`、无 `/map_server` | fail-closed，不通过 clean contract |
| Algorithm collector | deploy/install/capture/pull 完整且结论可机读 | deploy/install/pull exit `0`，capture natural exit `2`，`68.562s`，capture-time SHA match | 通过 fail-closed 证据，不是通过目标 |
| Compact child repair | 修复后需现场重新部署和验证 | 本地 145 tests 通过，但修复发生在最终 capture 后且未 redeploy | `local_fix_not_live_verified` |
| Mission / safety | 只有 live route/HIL/operator/delivery 才能计闭环 | 所有 safety 和 mission success 字段均为 false | 不计分、不归档 |

## Robot Software Lane

现场窗口为 `2026-07-14T16:09:22Z` 至 `2026-07-14T16:09:26Z`。lifecycle 与 Upper API
验证分别为 `8/8`、`2/2`；真实持有进程 PID `550851`。current baudrate 的三条证据源均为
`150000`：`running_holder.argv.--serial-baudrate`、`persisted_status.pid_matched.baudrate`、
`driver_diagnostics.serial.serial_baudrate`。API 使用
`lifecycle_status_readback.latest_result.baudrate`。vendor `230400` 仅作资料参考，不得覆盖 current
readback。

Product 接受此 lane 为 `live_lidar_lifecycle_current_reference_semantics_readback_only`，不是 HIL、路线
执行或安全准入。

## Algorithm Lane

本地 `py_compile`、145 tests、JSON、结构断言和 diff check 均通过。最终现场窗口为
`2026-07-14T16:14:28Z` 至 `2026-07-14T16:15:41Z`；deploy SCP、install SSH、pull SCP
均 exit `0`，capture natural exit `2`，耗时 `68.562s`，capture-time local/remote SHA 均为
`638abe14...`。

当前 graph 的可接受事实是：`/tf` 只有 `/esp32_bridge` publisher，dynamic TF 仅
`odom->base_link`，没有 `/amcl`，没有 `/map_server`。因此不能把 AMCL `map->odom` source
归因成功；`publisher_attribution_status=unavailable_amcl_tf_publisher_not_observed_in_node_graph`。
最终 raw 中 child JSON 还存在 8KB 截断，但 Product 采用 derived fail-closed summary 的 current graph
事实，不把受截断影响的 raw top-level `/tf_topic_missing` 误写成唯一现场结论。

最终 capture 后的 compact child repair 仅在本地通过测试，SHA 为 `f4f0b668...`，没有重新部署或现场
复验，状态固定为 `local_fix_not_live_verified`。

## OKR 与 No-repeat 对照

- O5 约 `85%`，仍是最低 Objective；success-class production/cloud evidence 仍不存在。
- O1 约 `94%`，O6/O7 各约 `93%`；本轮不调整主百分比。
- Robot Software status semantics clean 是可靠现场维护证据；Algorithm lane 则暴露 current runtime
  prerequisite 缺失，未形成更强 mission artifact。
- 本轮 KR `不归档`，OKR credit 为 false。
- 跳过 O5 的 no-repeat 理由仍成立：不得再做 status/readiness/export/browser/voice wrapper。

## Safety 与拒绝声明

本轮固定 `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、
`delivery_success=false`、`hil_pass=false`。

不证明 clean dynamic TF source、AMCL `map->odom` publisher attribution、route execution、delivery、
operator acceptance、current live HIL、safe-to-control 或 O5 external success。

## 下一轮 Exact Action

`robot-algorithm-engineer` 只先在一个 current strict no-motion 窗口启动或确认 `/map_server` 与
`/amcl` runtime，然后重试 compact dynamic TF source collector，不再运行 planner wrapper。只有
explicit operator approval 与 current HIL 同时具备后，才允许转入 controlled route evidence。
