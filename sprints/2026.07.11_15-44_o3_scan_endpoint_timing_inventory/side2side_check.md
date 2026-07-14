# O3 Scan Endpoint Timing Inventory Side2Side Check

## 验收结论

- Sprint: `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/`
- Sprint type: `epic`
- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`
- Product verdict: 接受本轮作为 O3/O1 supporting live no-motion 诊断进展；不接受作为 path generation、route execution、HIL、delivery 或 O5 production evidence。

本轮符合 PRD 目标：把上一轮 `/scan_rclpy_child_timeout_after_import` 继续下钻为 publisher endpoint、QoS、child runtime 与 sample timing 的可执行事实清单。真实板 artifact 证明 `/scan` endpoint 可见，但仍没有 sample、AMCL pose、dynamic `map->odom` 或 path，因此 OKR 百分比保持不变。

## 用户价值和产品北极星

用户价值：让固定路线送垃圾从“topic 名称可见但读不到样本”的模糊 blocker，推进到“LiDAR publisher 可见、QoS/window 需要验证”的下一条现场命令。

产品北极星：普通手机用户把垃圾交给小车后，小车可沿固定路线安全、可验证地送达。本轮只推进路线生成前置诊断，不等于手机侧送达闭环、真实运动控制或 HIL 完成。

## Side2Side 对照

| PRD / Tech Plan 验收项 | 本轮证据 | Product 判断 |
| --- | --- | --- |
| 新增 `/scan` publisher inventory | live artifact: `/scan.topic_type=sensor_msgs/msg/LaserScan`，`publisher_inventory.inventory_observed=true`，`publisher_inventory.publisher_count=1`，publisher node 为 `lidar_driver` | 通过 |
| 新增 endpoint QoS 与 requested QoS | publisher QoS 为 `RELIABLE` / `VOLATILE`；requested QoS 为 `BEST_EFFORT` / `VOLATILE` / `KEEP_LAST` depth 5 | 通过 |
| 新增 child runtime 与 sample timing | child runtime import、node、subscription、sample-wait 均为 true；`sample_timing.sample_count=0`，`probe_window_sec=2.2` | 通过，且明确仍 blocked |
| 稳定 root cause 分类 | `probe.classification=/scan_qos_or_window_timeout` | 通过 |
| 若未观测到 `/scan` sample，不推进 AMCL/path 成功 | `/amcl_pose=false`，`map_to_odom=false`，`map_to_base_link=false`，`path_generated=false`，`path_point_count=0` | 通过 |
| 所有安全字段必须 false | `safe_to_control=false`，`robot_control_executed=false`，`delivery_success=false`，`route_execution_success=false`，`hil_pass=false` | 通过 |
| 不触发运动控制、底盘 UART 或 NavigateToPose | tech-done 记录本轮 no-motion helper，不执行 `/cmd_vel`、底盘 UART、NavigateToPose 或路线执行 | 通过 |
| OKR 不因 supporting 诊断加分 | O5 约 85%，O1/O6/O7 约 93%，无百分比变化，无 KR 归档 | 通过 |

## 实际改动核对

Algorithm 已完成并记录以下改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/tech-done.md`
- local/live artifacts

Product closeout 本轮只新增或更新允许范围内的收口文档与 OKR 记录。

## 验证证据核对

Algorithm 记录的验证已通过：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：exit `0`
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`：exit `0`，`Ran 58 tests ... OK`
- local helper：exit `2`，按预期 fail-closed 并写出 artifact
- `scp`：exit `0`
- live helper：exit `2`，按预期 fail-closed 并写出 artifact
- pull artifact：exit `0`
- required `rg`：exit `0`
- scoped `git diff --check`：exit `0`

Product closeout 还需运行本轮指定的 scoped diff check，并在 `final.md` 记录结果。

## OKR 映射和方向判断

- O5：继续保持约 `85%`。本轮没有真实 external production evidence、真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 或真实手机/browser evidence。
- O1：继续保持约 `93%`。本轮是 current live no-motion diagnostic progress，但没有 current same-run path generation success、Nav2 route execution success、current live HIL pass、safe-to-control 或 delivery success。
- O6/O7：继续保持约 `93%`。本轮没有新的 `task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record、operator confirmation 或 production readback 可消费。

方向判断：继续 O3/O1 live localization/path 前置链路，不回到 O5 support-only，也不继续修旧 main-process rclpy ImportError。

## KR 拆解、更新或历史归档

- O1 current same-run path generation：仍 blocked，`path_generated=false`、`path_point_count=0`。
- O6/O7 current-run material：仍 blocked，没有新路线/回放/送达/operator material。
- O5 production evidence：仍 blocked，没有真实 external production evidence。
- 已完成 KR：无。
- 历史归档：无新增。

## 失败定位

本轮最新 live root cause 为：

- `/scan_qos_or_window_timeout`
- `/amcl_pose_probe_timeout`
- `map_to_odom_dynamic_source_missing`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `localization_not_ready_for_path_generation`

Product 解释：`/scan` topic 和 `lidar_driver` publisher 可见，publisher QoS 为 `RELIABLE`，helper child subscriber 已创建并按 `BEST_EFFORT` 等待 2.2 秒，但 `sample_count=0`。这说明下一轮应该区分 QoS mismatch、窗口过短、DDS endpoint timing 与 LiDAR driver endpoint-only/no-sample 行为。

## 剩余风险和下一步

剩余风险：

- 仍未拿到 `/scan_sample_observed`。
- `/amcl_pose=false`、`map_to_odom=false`、`map_to_base_link=false`、`path_generated=false` 继续阻塞 same-run path generation。
- AMCL rclpy param/source probe 仍有 `librcl_action.so` / `_rclpy_pybind11` import failure，但本轮 scan probe 已在 sourced child runtime 中成功 import。
- 本轮没有 route CSV、keyframe、rosbag、Nav2 result、delivery record 或 operator confirmation。

下一条建议：rerun true-board helper with longer `--timeout-s 18`; if `publisher_count` remains 1 and `sample_count` remains 0, add a RELIABLE subscription attempt while preserving current BEST_EFFORT attempt, to separate QoS mismatch from LiDAR driver endpoint-only/no-sample behavior.
