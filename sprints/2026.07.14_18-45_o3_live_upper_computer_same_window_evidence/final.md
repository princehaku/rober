# Final - O3 Live Upper-Computer Same-Window Evidence

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/`
- Closeout time: 2026-07-14 19:45 Asia/Shanghai
- Product owner: `product-okr-owner`
- Implementation and integration owner: `robot-algorithm-engineer`
- Product status: `accepted_current_window_live_planner_material_with_dynamic_source_gap_no_okr_lift`
- Proof boundary: `robot_runtime_o3_strict_no_motion_localization_planner_evidence_only`

## Product Acceptance 结论

Product 接受本轮为 O3/O1 fresh current-window true-board strict no-motion localization/planner
material。真实上位机 target 为 `192.168.1.11:37878`，remote 为 `op-z3-b6.home`；
`preflight_exit_code=0`、`capture_exit_code=0`、`scp_exit_code=0`。这不是 readiness wrapper。

同一次 remote raw 中：

- `scan_once_observed=true`
- `amcl_pose_observed=true`
- `map_server_active=true`
- `amcl_active=true`
- tf2 chain `map_to_odom=true`
- `path_generation_attempted=true`
- `path_generated=true`
- `path_point_count=28`
- `path_structured_pose_count=28`

Product 同时拒绝把结果写成 clean dynamic-source contract：`map_to_odom_dynamic.observed=true`，
但 `map_to_odom_dynamic.dynamic_source_observed=false`、`source_class=missing`、blocked reason 为
`/tf_topic_missing`。Exact root cause：

```text
map_to_odom_dynamic_source_not_observed_in_tf_source_inventory
```

## 用户价值和产品北极星

本轮把 13:38 的“缺 same-window live evidence”推进为真实板当前窗口可复验的 sensor、AMCL、
lifecycle、TF buffer 和 planner path material，直接减少后续受控路线验证前的不确定性。北极星
仍是可验证送达，不是路径生成本身；本轮没有 route execution、delivery 或 operator acceptance，
因此不宣称任务闭环。

## Hardware 事实接受边界

Hardware read-only audit 证明 current lifecycle 实际为 `/dev/ttyACM0@150000`：holder argv、ROS
param、persisted status 和递增 diagnostics 一致；`230400` 只是 lifecycle status synthetic
`reference_conflict_not_current`。Helper 使用
`managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start`，且
`managed_lidar_driver_started_by_helper=false`，没有启动第二个 LiDAR driver。

Product 接受本轮 read-only disambiguation，但不把 synthetic metadata 冲突视为已经永久修复。

## OKR 映射、方向和 KR 决策

- O5 继续约 `85%`，仍是当前最低 Objective；本轮没有 success-class production/cloud evidence。
- O1 继续约 `94%`。7 月 12 日 current same-run planner-only path 已获得一次保守计分，7 月 13
  日已有 fresh 28-pose material；本轮属于同一 planner-only evidence class，不重复计分。
- O6/O7 继续约 `93%`；本轮没有 production archive/consumer/browser 增量。
- 主百分比不调整。
- KR `不归档`。没有 route execution、delivery/operator acceptance、current live HIL、
  safe-to-control 或 O5 external success，任何当前 KR 都未完成。
- 方向判断：继续 O3 live evidence，但下一步只修 dynamic `/tf` source inventory 和 status
  metadata exact gap；暂停 planner wrapper/readiness 重复包装。

已完成 KR 的历史记录位置不移动，继续保留在 `OKR.md` 历史区和
`docs/process/okr_progress_log.md`。本轮没有新增可归档 KR；证据来源为本 sprint capture envelope、
remote raw、`tech-done.md` 和 Product acceptance JSON。

## O5 Lowest 复核

计划阶段跳过 O5 的理由在收口时仍成立：14:38 CLI export、15:38 live HTTP 和 16:40 headless
Chrome 都仍是 support-only，没有 O5 external success；继续 cloud/relay/browser surface 会重复消费
同一 blocker。CEO 提供的真实上位机入口使 O3 current-window robot-runtime evidence 成为可推进的
更强证据类。本轮确实产出了 fresh live artifact，而不是又一层 wrapper，因此切换有效；但该理由
不允许借机上调 O5 或重复给 O1 planner-only class 计分。

## 实际改动

Algorithm implementation 已写入：

- `artifacts/algorithm/live_upper_computer_same_window_evidence.raw.json`
- `artifacts/algorithm/live_upper_computer_same_window_evidence.remote.raw.json`
- 相关 preflight/capture/SCP logs、exit codes 和 Hardware read-only audit artifacts
- `tech-done.md`

Product closeout 新增或更新：

- `side2side_check.md`
- `final.md`
- `artifacts/product_acceptance_live_upper_computer_same_window_evidence.json`
- `OKR.md`
- `docs/process/okr_progress_log.md`

未修改 Engineer artifacts、helper、tests、产品代码、hardware/launch/map/Nav2 参数或范围外文件。

## 验证结果

Algorithm owner 在 `tech-done.md` 记录：capture envelope、remote raw、retry status JSON 均可解析；
implementation assertion、required-field `rg` 和 scoped diff-check 通过。

Product closeout 验证：

```text
product acceptance JSON json.tool: exit 0
Product structural assertion: product_live_upper_computer_same_window_evidence_acceptance_ok
required anchor rg: exit 0
scoped git diff --check: exit 0
```

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

不证明 `/cmd_vel`、`/api/base/manual`、NavigateToPose、controller/BT、route execution、
delivery/operator acceptance、current live HIL、safe-to-control、WAVE ROVER UART、非零底盘运动
或 O5 production cloud。

## 剩余风险与 Exact Owner/Action

1. `robot-algorithm-engineer`：下一轮只执行有界 no-motion `/tf` source inventory，确认 dynamic
   `map_to_odom` publisher endpoint、timestamp 与 freshness，关闭
   `map_to_odom_dynamic_source_not_observed_in_tf_source_inventory`；不得重复整套 planner wrapper。
2. `robot-software-engineer`：修正 lifecycle status synthetic `230400` metadata 与 current
   diagnostics `150000` 的语义冲突，避免现场 owner 再次误判 current baudrate。
3. `robot-hardware-engineer`：只有 CEO/现场 operator 明确批准后，才采 current live stop/HIL；
   未批准前不得触发底盘 UART 或真实运动。
4. `robot-algorithm-engineer`：只有 dynamic source inventory clean、current HIL 与 explicit
   operator approval 同时存在，才进入 controlled route execution evidence；之后仍需 delivery/
   operator acceptance 才能讨论 mission closure。
