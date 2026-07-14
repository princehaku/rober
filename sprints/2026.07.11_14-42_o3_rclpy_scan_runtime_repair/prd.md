# O3 Rclpy Scan Runtime Repair PRD

## 背景

最近三轮 O3 no-motion live board 证据已经把问题从泛化 localization failure 收敛到 `/scan` runtime 读帧链路：

- `/scan.topic_type=sensor_msgs/msg/LaserScan` 可见。
- `rclpy_sensor_data_once` 是最佳尝试，但板端发生 `ImportError`，涉及 `librcl_action.so` / `_rclpy_pybind11`。
- `cli_sensor_data_echo_once` 与 `cli_default_echo_once` 都 timeout。
- `/amcl_pose` timeout，AMCL dynamic `map->odom` 未出现，`path_generated=false`。

这说明系统已经越过了“topic 是否存在”的阶段，下一步必须修复或绕开板端 ROS Python runtime，使 helper 能在 same-run no-motion 窗口内真实消费 `/scan` frame。没有 `/scan` frame，AMCL 不可能稳定输出 `/amcl_pose`，O1 的 current same-run path generation 与 O6/O7 的 current-run material 消费都会继续冻结。

## 用户价值

固定路线垃圾投递的用户价值不是更多诊断文案，而是当前现场能生成并验证路线。`/scan` 读帧是路线生成前置链路的第一个可执行门槛：

1. `/scan` frame observed。
2. AMCL 消费 scan 后输出 `/amcl_pose`。
3. `map->odom` dynamic TF 出现。
4. same-run no-motion path generation 成功。
5. 后续才有 route execution、delivery record、operator confirmation 和 O6/O7 current-run material。

本轮目标是推进第 1 步，避免继续用 support-only、historical comparator 或 wrapper surface 代替现场执行材料。

## 产品北极星

北极星：普通手机用户把垃圾交给小车后，小车可沿固定路线安全送达，并且每次执行都有可复盘证据。

本轮对北极星的贡献是建立当前现场路线生成的传感器输入证据。它不是送达闭环本身，也不证明 safe-to-control、HIL pass 或 delivery success。

## OKR 映射和方向判断

- O5：方向判断为暂停 support-only 追分。O5 仍约 `~85%` 且最低，但缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser evidence；继续 readiness/probe 不计分。
- O1：方向判断为继续。修复 `/scan` runtime 读帧可直接解锁 O1 当前缺口 `current same-run path generation success` 的前置条件。
- O6/O7：方向判断为等待 current-run material。只有 O1/O3 产出 current-run scan/localization/path 或 route artifact，O6/O7 才有新的 `task_id`、route/material、Nav2 result 或 delivery/operator material 可消费。

本轮不更新 `OKR.md`，不归档 KR，不调整百分比。

## KR 拆解、更新或历史归档

- O1 current same-run path generation：本轮只推进 `/scan` frame observation 的前置门槛；验收成功后下一步是 `/amcl_pose`、`map->odom` 和 path generation。
- O6/O7 current-run material：本轮只产出上游 live no-motion artifact；不直接改 archive/readback/UI schema。
- O5 production evidence：本轮不推进；等待真实 external evidence。
- 已完成 KR：无。
- 历史归档：无。本轮规划文档不得把任何 KR 移入历史区。

## 本轮核心抓手

核心抓手是 `rclpy` / `/scan` runtime repair：

- 修复板端 `rclpy` shared library import failure，或增加等价的非 `rclpy` sensor-data frame reader fallback。
- 保留三段式 attempt 结构，但把失败原因从上一轮的 generic `ImportError` 下钻到 environment/library/QoS/publisher/window 层。
- 复跑 live no-motion helper，并写出新的 artifact。

## 范围

本轮允许后续 implementation owner 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/tech-done.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/*`

本 planning 阶段只创建：

- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/pre_start.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/prd.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/tech-plan.md`

## 非目标

- 不执行机器人运动，不发底盘控制，不触发 WAVE ROVER UART。
- 不把 `topic_type` 可见当成 `/scan` frame observed。
- 不把 local Mac fail-closed artifact 当成 live board proof。
- 不新增 O5 readiness、O6 archive、O7 UI、cloud relay 或 checklist surface。
- 不消费旧 historical material 作为新 OKR 增量。
- 不更新 `OKR.md`，不写 `tech-done.md`、`side2side_check.md` 或 `final.md`。

## 需要做什么

1. 检查 live board 上 `rclpy` import failure 的最小复现，确认是 shared library path、ROS setup、Python package ABI、install overlay 还是运行方式问题。
2. 修复或绕开 `rclpy_sensor_data_once`，优先保持 sensor-data QoS 语义。
3. 若 `rclpy` 无法快速修复，提供同等保守的 frame reader fallback，并把 fallback boundary 写入 artifact。
4. 复跑 no-motion helper，产出新的 live artifact。
5. 若 `/scan` observed，继续同窗口复验 `/amcl_pose`、`map_to_odom` 和 path generation；若未 observed，输出更窄 root cause 和下一条现场命令。

## 优先级和验收口径

- 优先级：P0，因为它是 O1 current same-run path generation 和 O6/O7 current-run material 的前置 live blocker。
- 验收口径：新的 live no-motion artifact 必须证明 `/scan` frame observed，或给出比上一轮更窄、更可执行的 failure boundary。
- 安全验收：`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false` 必须保留。
- Product 验收：不接受只新增文档、wrapper、readback、状态面板或重复上一轮 artifact 的结果。

## 对应责任 Engineer

- 主责：`robot-algorithm-engineer`
- 只读咨询：`robot-software-engineer`，仅在需要定位 ROS Python runtime / shell environment 时补事实。
- 不参与：`rober-hardware-engineer`、`full-stack-software-engineer`。

## 风险、阻塞和需要补齐的证据链

- 风险：`rclpy` 修复后仍可能因 LiDAR publisher 频率、QoS 或 managed runtime 窗口导致 `/scan` timeout。
- 风险：`/scan` observed 后仍可能卡在 AMCL 参数、initial pose、map quality 或 dynamic TF source。
- 阻塞：真实板 SSH / ROS runtime 不可达时只能产出 local fail-closed，不能算 live proof。
- 待补证据链：`scan_observed=true` -> `/amcl_pose_observed=true` -> `map_to_odom=true` -> `path_generated=true` -> current-run route material -> O6/O7 archive/readback -> delivery/operator material。

## 需要创建或更新的 sprint 文档

本轮 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation / acceptance 阶段才允许创建：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
