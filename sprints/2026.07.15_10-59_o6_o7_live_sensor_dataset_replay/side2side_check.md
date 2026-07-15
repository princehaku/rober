# O6/O7 真实传感器数据集回放 Epic - Side to Side Check

## 验收结论

- `sprint_type: epic`
- Product decision：`accepted_blocked_fail_closed_no_mission_credit`
- Proof boundary：`live_upper_computer_read_only_sensor_inventory_blocked_scan_publisher_unconfirmed`
- Exact status：`blocked_scan_publisher_unconfirmed`

本轮只接受一次真实上位机只读 inventory 及其 fail-closed 决策，不接受 current-run sensor dataset、rosbag、keyframe、semantic replay、O6 archive、O7 consumer 或 Mission Objective 0 达成。只读 inventory 是 gate 证据，不是本轮 mission artifact，不能把“SSH 可达、工具可用、磁盘充足”包装成真实数据集交付。

## 用户价值与产品北极星对照

用户需要一份本轮新产生、可校验且能被 O6/O7 同 `task_id` 消费的真实传感器数据集。实际只回答了“当前为何不能安全开始录制”：`/scan` 在 topic list 中类型为 `sensor_msgs/msg/LaserScan`，但 verbose info exit `1`、`Unknown topic '/scan'`，publisher count 未确认；ROS CLI 还自动启动 daemon，破坏严格 `runtime_mutation_free` 前提。

产品北极星 `current_live_robot_dataset_consumed=true` 未达成。没有 DB3、metadata、keyframe、semantic replay 或 O6/O7 lineage，inventory 不计 `current_run_artifact_delta`。

## Side-to-side 验收矩阵

| 计划验收项 | 实际事实 | Product 判断 |
| --- | --- | --- |
| 一次 bounded read-only inventory | SSH exit `0`；ROS setup、`ros2 bag`、sqlite3、`--max-bag-size`、磁盘 `994639872` bytes 与无冲突 recorder gate 均通过 | 接受为只读 gate 证据 |
| `/scan` 类型与 publisher count `>=1` | topic list 为 `sensor_msgs/msg/LaserScan`；verbose info exit `1`、`Unknown topic '/scan'`，publisher count 未确认 | `blocked_scan_publisher_unconfirmed` |
| inventory 不改变 runtime | 自动 ROS CLI daemon 在 inventory 窗口内启动；`runtime_mutation_free=false` | strict gate 不通过 |
| 唯一 live rosbag capture | `inventory_invocation_count=1`、`live_capture_invocation_count=0`、`capture_gate=false` | 按计划 fail closed；不得补录 |
| current-run DB3 / metadata / keyframe | 均未生成 | 未验收，不是 current-run mission artifact |
| 离线 LaserScan semantic replay | 无 DB3 输入，未执行 | 未验收 |
| Full-stack Phase C | 未派发；无 O6 write/readback、无 O7 selected-task consumer | 未验收 |
| helper、fixture tests 与产品实现 | 两次 Algorithm helper 实现派单均在产品代码、测试、文档零文件落盘前中断 | 零实现，不把计划当交付 |
| 危险能力保持关闭 | `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false` | 通过安全边界检查 |

## Mission Objective 0 与 OKR 验收

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`

O5 保持约 `85%`，O6/O7 各保持约 `93%`，O1 保持约 `94%`；主百分比全平。O6/O7 KR `不归档`，没有已完成 KR 移入历史区。历史位置仅为本 sprint 的 blocked acceptance：`tech-done.md -> side2side_check.md -> final.md` 及 `artifacts/algorithm/read_only_inventory.json`。

## 抓手、工作项与责任人

- 本 sprint 抓手已退役：一次只读 inventory 已给出 fail-closed 结论，本 sprint **不得重跑** inventory/capture，也不得新增 helper、review、readback、wrapper、fixture 或 Full-stack Phase C 来包装同一结果。
- 下一轮默认切换 Objective，选择不依赖该 `/scan` inventory blocker、能产生 mission-grade artifact/action 的最低可行动 lane。
- 只有 Product/CEO 给出 fresh authorization 且新建 sprint 时，才由 `robot-algorithm-engineer` 使用同一 shell 的 daemon-off、graph-stabilized bounded probe；优先设置 `ROS2CLI_NO_DAEMON=1` 或先执行 daemon-off，再稳定等待 ROS graph，恢复 `/scan publisher_count>=1` gate。
- `full-stack-software-engineer` 只有在新 sprint 已冻结真实 DB3/semantic sections 后才进入 Phase C；不得使用 fixture 替代 live bag。

## 风险证据链

1. 现有 artifact 无法区分 DDS graph 尚未稳定、ROS CLI daemon/cache 影响或 `/scan` publisher 瞬态变化；因此不能宣称 scan publisher 存在。
2. `capture_gate=false` 且 `live_capture_invocation_count=0`，所以不存在 DB3、message/timestamp/hash、LaserScan decode 或跨层 lineage。
3. 两次 helper 派单均零文件落盘，产品代码、测试、构建与 Full-stack 消费均无可验收增量。
4. 本轮没有控制、路线、送达或 HIL 证据；固定 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。
