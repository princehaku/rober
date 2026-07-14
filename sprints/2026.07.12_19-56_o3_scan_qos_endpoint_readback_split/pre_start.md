# Pre Start - O3 Scan QoS Endpoint Readback Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/`
- Planned start: `2026-07-12 19:56 CST`
- Product owner: `product-okr-owner`
- Implementation owner: `Robot Software`
- Sprint boundary: O3/O1 strict no-motion scan QoS / endpoint / readback split only.
- Single-owner plan: Robot Software owns this sprint because the current blocker sits inside the ROS2/Nav2 readback helper contract, managed runtime artifact interpretation, and strict no-motion validation chain. Algorithm waits until `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof. Hardware waits unless evidence makes LiDAR serial/runtime/wiring the primary blocker after vendor-doc review.

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给小车后，一键发车并得到可验证的送达或失败结果。当前 sprint 不交付用户可见发车能力；它要消除 fixed-route delivery 前的最近技术不确定性：为什么 lifecycle-active 后 `/scan` 在 RELIABLE 和 BEST_EFFORT readback 窗口内都没有可靠样本。

这一步的用户价值是把“定位链路为什么不继续产生 `/amcl_pose` 和 dynamic `map->odom`”从笼统的 Nav2/runtime blocker 下钻成下一条可执行命令。只有拆清 `/scan_reliable_and_best_effort_timeout`，后续才可能恢复 AMCL pose、TF、planner-only path、route execution 和 delivery/operator evidence。

## Read First Evidence

- `AGENTS.md`: 要求每轮 sprint 留档、验证围栏、no-motion 边界、单 owner 闭环和同一 blocker 不重复消费。
- `OKR.md`: O5 仍是最低 Objective，约 `85%`；但 O5 只有真实 external production evidence 才能计增量。
- `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/final.md`: `/map_server` 与 AMCL 已有 lifecycle-active 证据，不能无证据回退到 map_server configure/on_configure/loadmap blocker。
- `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/final.md`: canonical artifact 已把 Product primary blocker 推到 `Nav2 sensor input / /scan_reliable_and_best_effort_timeout`，且 `map_server_active=true`、`amcl_active=true`、`managed_runtime_log_lifecycle_readback.clean=true`、`map_once_observed=true`。
- 自动化记忆：最近 OKR gate 已反复确认，wrapper/readback/support-only 不计 mission 主进度；O3 no-motion lane 可以继续，但必须产出更接近 current-run path/route/delivery 的证据。

## OKR Mapping And Direction

- O5：继续约 `85%`，本轮不做。原因是 O5 缺真实 production/external evidence；继续 local support-only、readiness packet、wrapper 或 cutover checklist 不会产生 `external_artifact_delta`，也不应提高 OKR 百分比。
- O1/O3：继续 strict no-motion lane。本轮目标是把 `/scan_reliable_and_best_effort_timeout` first split 成 publisher endpoint、QoS/window/ROS readback、LiDAR runtime 三类候选，而不是回到 lifecycle、map_server configure/on_configure、loadmap、graph timeout wrapper。
- O6/O7：继续等待 live route execution、delivery/operator acceptance 或 production readback；独立 surface/checklist/handoff 本轮冻结。
- 方向判断：继续 O3/O1；不调整、不归档 KR；只有 same-run path generation、route execution、delivery/operator acceptance、current live HIL 或 real production external evidence 才可触发后续 OKR percentage review。

## 本轮核心抓手

Robot Software 需要围绕 canonical blocker 做第一层分裂：

`/scan_reliable_and_best_effort_timeout`

必须拆成以下互斥或排序明确的候选：

- publisher endpoint：`/scan` publisher 是否存在、topic type 是否稳定、endpoint 是否来自预期 LiDAR/scan path。
- QoS/window/ROS readback：RELIABLE / BEST_EFFORT、CLI/rclpy、readback budget、window timing 或 ROS graph/readback 方式是否造成假 timeout。
- LiDAR runtime：只有在前两类排除或证据指向后，才把 LiDAR driver/runtime/serial/wiring 列为 primary，并要求 Hardware 读 `docs/vendor/VENDOR_INDEX.md` 后介入。

## Strict No-Motion Safety Boundary

本 sprint 是 strict no-motion：

- no /cmd_vel。
- no `/api/base/manual`。
- no NavigateToPose。
- no WAVE ROVER UART。
- 不开底盘、不下发路线、不执行 route、不中继 base manual。
- Artifact 必须保持 `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`，除非 CEO 另开 motion-approved sprint。

## Required Sprint Documents

本 planning pass 创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 Robot Software implementation 需要补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
