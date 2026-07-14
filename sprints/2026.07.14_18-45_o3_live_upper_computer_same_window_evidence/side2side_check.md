# Side-to-Side Check - O3 Live Upper-Computer Same-Window Evidence

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Product verdict: `accepted_current_window_live_planner_material_with_dynamic_source_gap_no_okr_lift`
- Proof boundary: `robot_runtime_o3_strict_no_motion_localization_planner_evidence_only`

## 用户价值和北极星对照

北极星是普通用户最终能发起一条可验证、可复盘、可送达的垃圾收集任务。13:38 sprint 只有
same-window readiness checklist；本轮已在真实上位机 `192.168.1.11:37878`、remote
`op-z3-b6.home` 上执行 current-window no-motion capture，证明当前传感器、定位、lifecycle 和
planner 可以形成 28-point path。该结果是真实 robot-runtime material，不是 readiness wrapper。

但本轮没有执行路线、没有送达，也没有 HIL/safe-to-control；且 `/tf` source inventory 未观察到
dynamic `map_to_odom` source，因此只接受 planner material 和 exact gap，不接受 mission closure。

## PRD Side-by-Side

| PRD 验收项 | 实际证据 | Product 判断 |
|---|---|---|
| Fresh target provenance | `target=192.168.1.11:37878`、`remote_hostname=op-z3-b6.home`，helper SHA match | 通过 |
| 有界执行和拉回 | `preflight_exit_code=0`、`capture_exit_code=0`、`scp_exit_code=0` | 通过 |
| 复用现有 LiDAR | Hardware read-only audit 为 `/dev/ttyACM0@150000`；helper `reuse_existing_lidar_lifecycle_no_driver_start`，第二 driver 未启动 | 通过 |
| `/scan` fresh observation | `scan_once_observed=true` | 通过 |
| `/amcl_pose` observation | `amcl_pose_observed=true`、frame `map` | 通过 |
| Map/AMCL lifecycle | `map_server_active=true`、`amcl_active=true` | 通过 |
| `map_to_odom` transform | tf2 chain `map_to_odom=true`、`map_to_odom_dynamic.observed=true` | 部分通过 |
| Dynamic `/tf` source inventory | `dynamic_source_observed=false`、`source_class=missing`、`/tf_topic_missing` | 未通过，exact blocker 已落盘 |
| Planner-only action | `path_generation_attempted=true`、`path_generated=true` | 通过 |
| Structured path | `path_point_count=28`、`path_structured_pose_count=28` | 通过 |
| Strict no-motion | 所有 control/delivery/HIL/safe fields 为 false | 通过 |
| Route/delivery/HIL closure | `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false` | 未证明，不在本轮接受范围 |

## Hardware Read-Only Audit 对照

首次 status 中 lifecycle synthesized `230400` 与 driver diagnostics `150000` 冲突。Hardware
read-only audit 和 retry preflight 证明：

- current holder PID/argv、ROS param 和递增 diagnostics 都指向 `/dev/ttyACM0@150000`；
- top-level current source 为 `driver_diagnostics_latest.serial.serial_baudrate`；
- `230400` 只是 `reference_conflict_not_current` synthetic reference；
- helper 没有 stop/start existing lifecycle，也没有启动第二个 LiDAR driver。

Product 接受实际 current lifecycle 为 `150000`，但保留 lifecycle status synthetic metadata 的
产品/运维语义缺陷，不能把本次 read-only 解歧当作永久修复。

## 与既有 Planner Evidence 对照

- 2026-07-12 21:57 已首次证明 current same-run planner-only path，并让 O1 从约 93% 保守上调到
  约 94%。
- 2026-07-13 03:00 已产生 fresh 28-pose structured planner material；04:02 已由 fixed-route
  consumer 消费，主百分比保持 flat。
- 2026-07-14 13:38 只有 readiness wrapper，未采 live evidence。
- 本轮强于 13:38，因为真实 SSH/current-window `/scan`、`/amcl_pose`、lifecycle、tf2 chain 和
  28-point planner result 都已产生；但它与 7 月 12/13 属同一 planner-only evidence class，且
  dynamic-source contract 仍不 clean。

因此 Product 不重复给 planner-only class 计分：O1 继续约 `94%`，O5 继续约 `85%`，O6/O7
继续约 `93%`，主百分比不调整，KR `不归档`。

## Exact Root Cause 和下一步

Exact root cause：

```text
map_to_odom_dynamic_source_not_observed_in_tf_source_inventory
```

证据边界是 tf2 buffer 已观察 `map->odom` 且 path success，但 `/tf` endpoint/source inventory
missing，`map_to_odom_dynamic.dynamic_source_observed=false`。下一步按顺序：

1. `robot-algorithm-engineer`：执行有界 no-motion `/tf` source inventory，复验 dynamic
   `map_to_odom` publisher endpoint、timestamp 和 freshness；不得再包装整套 planner readiness。
2. `robot-software-engineer`：修正 lifecycle status synthetic `230400` metadata 与 current
   diagnostics `150000` 的语义冲突。
3. `robot-hardware-engineer`：只有 explicit operator approval 后才采 current live stop/HIL。
4. `robot-algorithm-engineer`：只有 dynamic source clean、current HIL 和 operator approval 同时
   满足后，才进入 controlled route execution evidence。

## Rejected Claims

本轮不证明 NavigateToPose、controller/BT、route execution、delivery/operator acceptance、current
live HIL、safe-to-control、O5 production cloud、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART
或任何非零底盘运动。固定：`safe_to_control=false`、`route_execution_success=false`、
`delivery_success=false`、`hil_pass=false`。
