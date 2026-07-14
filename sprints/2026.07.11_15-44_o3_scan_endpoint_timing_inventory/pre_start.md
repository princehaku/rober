# O3 Scan Endpoint Timing Inventory Pre Start

## sprint_type

`sprint_type: epic`

## 上轮结论

上一轮 `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/final.md` 已把 `/scan` runtime blocker 从旧的主进程 `rclpy` ImportError 推进到 ROS-sourced child Python：

- `/scan.topic_type=sensor_msgs/msg/LaserScan` 可见。
- `/scan.probe.best_attempt.runtime=ros_sourced_child_python`。
- `import_check.ok=true`，旧 `librcl_action.so` / `_rclpy_pybind11` ImportError 已从 scan probe 上消除。
- `/scan.probe.observed=false`，新的 root cause 为 `/scan_rclpy_child_timeout_after_import`。
- CLI fallback 仍 timeout。
- `/amcl_pose=false`、`map_to_odom=false`、`path_generated=false`。
- 安全字段继续固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

这说明本轮不应继续消费旧 ImportError，也不应回到 O5 readiness/support-only packet。当前最小可执行问题已经变成：LiDAR publisher 是否启动、`/scan` endpoint 是否真实存在、QoS 是否匹配、sample window 是否足够，以及 child probe import 成功后为什么拿不到样本。

## 本轮目标

本轮继续 O3/O1 supporting live no-motion localization/path lane，目标是让 helper/artifact 新增 `/scan` publisher、sample timing 和 endpoint inventory 字段，在真实板或本地 fail-closed 环境中把 `/scan` 失败清晰归类为以下之一：

- no publisher：`/scan` topic 或 publisher endpoint 不存在。
- LiDAR runtime not started：managed runtime 未启动 LiDAR publisher，或 launch/lifecycle 没有进入可发布状态。
- publisher visible but no sample：endpoint 可见，但采样窗口内没有 LaserScan sample。
- QoS/window timeout：publisher 存在但 subscriber QoS、DDS endpoint 或窗口长度导致 sample timeout。
- child probe timeout after import：ROS-sourced child Python import 成功，但 child probe 等样本超时。
- scan sample observed：至少读到一帧，才能继续复验 `/amcl_pose`、`map_to_odom` 和 `path_generated`。

本轮不执行运动控制，不发 `NavigateToPose`，不触发底盘 UART，不声明 HIL、safe-to-control、route execution success 或 delivery success。

## OKR 选择理由

O5 是当前最低主 Objective，约 `~85%`。但最近 O5 已连续 fail-closed 在真实 external production evidence 缺失：

- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/` 已证明 production cutover readiness packet 固定 `okr_credit_allowed=false`，属于 support-only aggregator。
- 近期 O5 external evidence / field execution pivot 已记录 `blocked_missing_new_field_execution_material`，没有新的真实 production external evidence、field execution pack、Nav2 result、delivery record、operator confirmation 或 production readback。

继续 O5 readiness、probe、checklist 或 support-only packet 会重复消费同一 external production blocker，不能计主 OKR 增量。本轮转向 O3/O1 相邻目标，是因为上一轮已经产生新的 current live no-motion blocker，且该 blocker 可以通过软件 helper/artifact 继续下钻。只有 `/scan` sample 与 localization/path 链路打通后，才可能生成 `map.yaml`、`route.csv`、rosbag、replay JSONL、Nav2 result、delivery record 或 operator material，供 O6/O7 后续消费。

## 用户价值和产品北极星

用户价值：让固定路线送垃圾从历史材料、wrapper/readback 和 support-only 证明，继续靠近当前现场可生成路线的事实链。普通用户最终不关心 `/scan` 名称是否存在，而关心小车能否在当前位置稳定定位并生成可执行路线。

产品北极星：普通手机用户把垃圾交给小车后，小车可以沿固定路线安全、可验证地送达。本轮只处理路线生成前置诊断，不等于手机侧送达闭环、真实运动控制或 HIL 完成。

## Owner

- 主责 owner：`robot-algorithm-engineer`
- Product closeout：`product-okr-owner`
- 不启动 `rober-hardware-engineer`：本轮不改 WAVE ROVER、UART、引脚、电压、波特率、底盘协议或机械事实。
- 不启动 `full-stack-software-engineer`：本轮不改手机、PC、O7 UI 或云端触点。
- `robot-software-engineer` 仅可在后续实现阶段做只读咨询，补充 ROS launch/runtime packaging 事实；本轮 owner 仍是 Algorithm 单线闭环。

## 验收口径

- 必须产出新的 helper/artifact 字段，用于描述 `/scan` publisher count、publisher node、endpoint QoS、subscriber/requested QoS、sample window、first sample latency、sample count、last sample timing 和分类 root cause。
- 真实板可达时，必须在 live no-motion helper artifact 中记录 inventory；真实板不可达时，本地 helper 必须 fail-closed 并写明不可声明 live proof。
- Artifact 必须能区分 no publisher、publisher visible but no sample、QoS/window timeout、LiDAR runtime not started、child probe timeout after import。
- 若 `/scan` observed，后续同窗口复验 `/amcl_pose`、`map_to_odom` 和 `path_generated`；只有 `path_generated=true` 才允许后续讨论主 OKR 百分比调整。
- 必须继续固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`。

## 证据边界

本轮最多是 `software_proof_o3_scan_endpoint_timing_inventory_only` 或 live no-motion supporting evidence。它不证明：

- safe-to-control
- HIL pass
- delivery success
- route execution success
- current live WAVE ROVER motion acceptance
- production cloud success
- O5 external production evidence

没有 `path_generated=true` 时，本轮不得调整 O1/O5/O6/O7 主 OKR 百分比，不归档 KR。

## 当前风险

- `/scan` topic type 可见不等于 publisher endpoint 正在持续发布。
- Endpoint 可见后仍可能因 QoS、DDS discovery、sample window、managed runtime timing 或 LiDAR lifecycle 导致无 sample。
- `/scan` observed 后仍可能继续卡在 AMCL initial pose、map quality、dynamic `map->odom` 或 path planner readiness。
- 真实板不可达时只能得到 local fail-closed，不能声明 live board proof。
