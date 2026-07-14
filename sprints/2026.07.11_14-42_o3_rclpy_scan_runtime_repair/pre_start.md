# O3 Rclpy Scan Runtime Repair Pre Start

## sprint_type

`sprint_type: epic`

## 上轮结论

上一轮 `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/` 已把 O3 no-motion live board blocker 从泛化 `/scan_probe_timeout` 下钻为三段式读帧失败：

- `/scan.topic_type=sensor_msgs/msg/LaserScan` 已可见，说明本轮不应再停留在 topic 名称是否存在的层面。
- `best_attempt=rclpy_sensor_data_once`，但板端 `rclpy` 导入失败，错误指向 `librcl_action.so` / `_rclpy_pybind11`。
- 两条 CLI `/scan` echo fallback 均 timeout，`/amcl_pose` timeout，`map_to_odom=false`，`path_generated=false`。
- 安全字段继续固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

该结论说明当前最小可行动作不是 O5 readiness，也不是再写一层 O6/O7 readback surface，而是修复或绕开板端 `rclpy` / `/scan` runtime 读帧问题，产出新的 same-run live no-motion artifact。

## 本轮目标

本轮继续现场 O3 no-motion lane，目标是修复或绕开 `rclpy_sensor_data_once` 的 runtime 读帧失败，使 `/scan` 至少出现一个可复核的 live no-motion frame observation，或把失败进一步收敛到可执行的 ROS environment / LiDAR publisher / DDS QoS / AMCL 输入 blocker。

本轮不执行运动控制，不发 `NavigateToPose`，不触发底盘 UART，不声明 HIL、safe-to-control 或 delivery success。

## OKR 选择理由

O5 仍是当前最低主 Objective，约 `~85%`。但 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/` 已证明 O5 production cutover packet 是 support-only aggregator，固定 `okr_credit_allowed=false`；`sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/` 又证明没有新的 `field_execution_pack` 或真实 production external evidence，结论为 `blocked_missing_new_field_execution_material`。

因此，本轮不直接推进 O5。继续 O5 readiness、probe、checklist 或 support packet 会重复消费同一外部证据 blocker，不能提升主 OKR。本轮转向 O3 是为了打开 O1 current same-run path generation 的前置条件，并为 O6/O7 后续消费 current-run `map.yaml`、`route.csv`、rosbag、replay JSONL、Nav2 result 或 delivery/operator material 提供新的 live source artifact。

最近 O3 no-motion lane 已连续定位到 `/scan`、`/amcl_pose` 和 `map_to_odom`，但上一轮新增事实已经把 root cause 从 generic timeout 收敛到 `rclpy` runtime import failure + CLI timeout。本轮允许继续，但验收必须产出新的 live artifact 或更窄 root cause；不得只复述上一轮失败。

## 用户价值和产品北极星

用户价值是把固定路线送垃圾从历史材料和只读证明推进到当前现场可生成路线：只有 `/scan` 可被 AMCL 持续消费，系统才可能产生 `/amcl_pose`、dynamic `map->odom` 和 same-run path。普通手机用户最终关心的是一键发车后的可靠送达，本轮解决的是该体验背后的最小现场可观测前置条件。

产品北极星仍是普通手机用户可安全、可验证地完成垃圾投递；本轮只做 no-motion proof，不以任何方式扩大为真实送达成功。

## Owner

- 主责 owner：`robot-algorithm-engineer`
- 只读协作：`robot-software-engineer` 可补充 ROS Python runtime / environment packaging 事实，但不并行改 O5、O6、O7 或硬件驱动。
- 不启动 `rober-hardware-engineer`：本轮不改 WAVE ROVER、UART、引脚、电压、波特率、底盘协议或机械事实。
- 不启动 `full-stack-software-engineer`：本轮没有手机、PC 或 O7 UI 改动。

## 验收口径

- 必须产出新的 live no-motion artifact，路径预期为 `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/live_o10_rclpy_scan_runtime_repair.raw.json`。
- Artifact 必须明确 `/scan` 的 `topic_type`、attempt labels、best attempt、runtime source、observed/timed_out/error、root causes 和 false safety fields。
- 若修复成功，至少证明 `/scan` 在 no-motion 窗口内读到一帧，并继续复验 `/amcl_pose` 与 `map_to_odom`。
- 若仍失败，必须比 `ImportError` / CLI timeout 更可执行，例如缺失 shared library 路径、ROS environment 未 source、Python package ABI mismatch、LiDAR publisher 不连续、DDS QoS mismatch 或 managed runtime window 不足。
- 必须继续固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`；除非另有真实安全验收，本轮不得打开这些字段。

## 当前风险

- 板端 `rclpy` / ROS Python shared library 环境可能需要现场 shell、容器或 ROS install 修正；本轮 planning 不直接改硬件配置。
- CLI `/scan` echo 也 timeout，说明即使 `rclpy` 修复，LiDAR 连续发布或 QoS 仍可能继续阻塞。
- `/amcl_pose` 与 `map->odom` 仍未出现，本轮最多解锁 path generation 的前置输入，不等于 same-run path generation success。
- O5 仍缺真实 external production evidence，不能通过本轮 O3 诊断间接涨分。
