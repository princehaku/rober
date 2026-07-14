# O3 Scan Endpoint Timing Inventory Final

## Sprint Summary

- Sprint: `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/`
- Sprint type: `epic`
- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`
- Outcome: accepted as O3/O1 supporting live no-motion diagnostic progress; no OKR percentage changes and no KR archival.

本轮把上一轮 `/scan_rclpy_child_timeout_after_import` 继续下钻到 `/scan` publisher endpoint、QoS、child runtime 和 sample timing。真实板证明 `/scan` publisher 可见，但 2.2 秒窗口内没有 sample，AMCL、TF 和 path 仍 blocked。

## 用户价值和产品北极星

用户价值：让固定路线送垃圾的现场 blocker 从“读不到 `/scan`”变成可执行的 QoS/window/publisher sample delivery 判断，避免继续重复修旧 ImportError 或回到 O5 support-only lane。

产品北极星：普通手机用户把垃圾交给小车后，小车可沿固定路线安全、可验证地送达。本轮只推进路线生成前置诊断，不等于手机侧送达闭环、真实运动控制、HIL 或生产云完成。

## 实际改动

Algorithm owner 已完成实现与 `tech-done.md` 留档，核心改动为：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：新增 `/scan` child runtime、endpoint inventory、sample timing、requested QoS、publisher inventory、managed runtime scan status 与稳定 classification。
- `onboard/tests/test_nav2_runtime_proof_helper.py`：覆盖 6 个 `/scan` classification、endpoint QoS、sample timing、child runtime shape，以及主进程 rclpy graph 失败时优先消费 child endpoint inventory。
- `docs/navigation/field_route_evidence_preflight.md`：新增 15:44 artifact 读取顺序和证据边界。
- `docs/navigation/fixed_route_workflow.md`：新增 fixed-route/no-motion 现场读取顺序。
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/tech-done.md`
- local/live artifacts

Product closeout 本轮新增或更新：

- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/side2side_check.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Algorithm 已记录的验证结果：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：exit `0`
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`：exit `0`，`Ran 58 tests ... OK`
- local helper：exit `2`，按预期 fail-closed 并写出 artifact
- `scp`：exit `0`
- live helper：exit `2`，按预期 fail-closed 并写出 artifact
- pull artifact：exit `0`
- required `rg`：exit `0`
- scoped `git diff --check`：exit `0`

Product closeout 验收命令：

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory
```

- exit `0`
- output: no whitespace errors

## Live Artifact 关键字段

Artifact: `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/live_o10_scan_endpoint_timing_inventory.raw.json`

`/scan` inventory:

- `/scan.topic_type=sensor_msgs/msg/LaserScan`
- `publisher_inventory.inventory_observed=true`
- `publisher_inventory.publisher_count=1`
- publisher node: `lidar_driver`
- publisher QoS: `RELIABLE` / `VOLATILE`
- requested QoS: `BEST_EFFORT` / `VOLATILE` / `KEEP_LAST` depth 5
- child runtime import/node/subscription/sample-wait all true
- `sample_timing.sample_count=0`
- `probe_window_sec=2.2`
- `probe.classification=/scan_qos_or_window_timeout`

Localization/path:

- `/amcl_pose=false`
- `map_to_odom=false`
- `map_to_base_link=false`
- `path_generated=false`
- `path_point_count=0`

Safety and delivery fields:

- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `route_execution_success=false`
- `hil_pass=false`

## OKR 映射和方向判断

- O5：保持约 `85%`。本轮没有真实 external production evidence，不能补 O5 分数。
- O1：保持约 `93%`。本轮是 O3/O1 supporting live no-motion diagnostic progress，不是 current same-run path generation success、Nav2 route execution success、current live HIL pass、safe-to-control 或 delivery success。
- O6：保持约 `93%`。没有新的 current-run route/delivery/operator/production readback material 可消费。
- O7：保持约 `93%`。没有新的 PC-facing route execution、delivery/operator、真实媒体或生产云材料可展示。

方向判断：继续 O3/O1 live localization/path 前置链路；暂停 O5 support-only 追分；不继续消费旧 main-process rclpy ImportError。

## KR 拆解、更新或历史归档

- O1 current same-run path generation：仍 blocked，`path_generated=false`、`path_point_count=0`。
- O6/O7 current-run material：仍 blocked，没有新的 `task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record、operator confirmation 或 production readback。
- O5 production evidence：仍 blocked，没有真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 或真实手机/browser evidence。
- 已完成 KR：无新增。
- 历史归档：无新增，保持在 `docs/process/okr_progress_log.md` 的既有归档记录。

## 本轮核心抓手

核心抓手是 LiDAR publisher/sample timing/endpoint inventory。它已经把 `/scan` blocker 从旧的 child ImportError 收紧为 publisher 可见但 sample timeout：publisher endpoint 可见，QoS 组合需要验证，sample delivery 尚未证明。

## 需要做什么

下一轮由 `robot-algorithm-engineer` 主责：

1. 在真实板复跑 helper，使用更长窗口 `--timeout-s 18`。
2. 如果 `publisher_count=1` 且 `sample_count=0` 仍成立，新增 RELIABLE subscription attempt。
3. 保留当前 BEST_EFFORT attempt，确保能区分 QoS mismatch、窗口过短、DDS endpoint timing 与 LiDAR driver endpoint-only/no-sample 行为。
4. 只有 `/scan_sample_observed` 后，才复验 `/amcl_pose`、dynamic `map->odom` 和 `path_generated=true`。

## 优先级和验收口径

优先级：P0 for O3/O1 live path prerequisite；不是 O5 主 OKR追分项。

下一轮验收口径：

- 接受：`/scan_sample_observed=true`，或把 failure 进一步区分为 QoS mismatch、window timeout、driver endpoint-only/no-sample、DDS timing 或 LiDAR lifecycle。
- 不接受：只复述 `/scan_qos_or_window_timeout`，或只增加 checklist/review/handoff/surface。
- 不调整 OKR：除非出现 `path_generated=true`、live route execution、delivery/operator material 或 production external evidence。
- Safety fields 必须继续 false，除非 CEO 提供真实安全验收材料。

## 对应责任 Engineer

- 主责：`robot-algorithm-engineer`
- 只读咨询：`robot-software-engineer`，仅限 ROS runtime / launch endpoint 事实。
- 不参与：`rober-hardware-engineer`、`full-stack-software-engineer`，除非后续证据转向硬件 LiDAR lifecycle 或 O7 current-run material consumption。

## 失败定位

本轮 root cause:

- `/scan_qos_or_window_timeout`
- `/amcl_pose_probe_timeout`
- `map_to_odom_dynamic_source_missing`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `localization_not_ready_for_path_generation`

Product 判断：`/scan` topic 和 `lidar_driver` publisher 可见，publisher QoS 为 `RELIABLE`，helper child subscriber 已创建并按 `BEST_EFFORT` 等待 2.2 秒，但 `sample_count=0`。下一轮应通过更长窗口和 RELIABLE subscription attempt 区分 QoS/window 与 LiDAR driver endpoint-only/no-sample。

## 剩余风险

- 仍未拿到 `/scan_sample_observed`。
- `/amcl_pose=false`、`map_to_odom=false`、`map_to_base_link=false`、`path_generated=false` 继续阻塞 same-run path generation。
- AMCL rclpy param/source probe 仍有 `librcl_action.so` / `_rclpy_pybind11` import failure；本轮只确认 scan child runtime import 成功。
- 本轮没有 route CSV、keyframe、rosbag、Nav2 result、delivery record、operator confirmation、production readback 或真实运动/HIL。

## 下一轮建议

Rerun true-board helper with longer `--timeout-s 18`; if `publisher_count` remains 1 and `sample_count` remains 0, add a RELIABLE subscription attempt while preserving current BEST_EFFORT attempt, to separate QoS mismatch from LiDAR driver endpoint-only/no-sample behavior.
