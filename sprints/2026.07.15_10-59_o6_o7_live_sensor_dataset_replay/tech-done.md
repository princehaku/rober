# O6/O7 真实传感器数据集回放 Epic - Tech Done

## 状态

- `sprint_type: epic`
- `status: engineering_blocked_fail_closed_waiting_product_acceptance`
- 本文只收口 Algorithm 阶段已经发生的事实，不把计划、只读 inventory 或失败门槛包装成 live dataset、semantic replay 或 O6/O7 消费完成。

## 自主能力目标和本轮抓手

本 sprint 原计划在不控制机器人、不启动或停止既有 runtime 的前提下，以 `/scan` 为必需 topic，先完成一次只读上位机 inventory，再由门槛决定是否进行唯一一次短时 rosbag capture，并将同一 DB3 离线回放后交给 Full-stack Phase C 消费。

本轮实际抓手只推进到一次 read-only SSH inventory。前两次 Algorithm 实现派单都在产品代码、测试或文档落盘前被主节点因无产出中断，因此没有实现 capture helper、fixture tests、decoder 适配或 `docs/navigation/` 文档。

## 实际改动

本轮在工程收口前实际新增的 sprint 材料只有：

- Product 规划文件：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Algorithm 只读证据：`artifacts/algorithm/read_only_inventory.json`。
- 本文件 `tech-done.md` 仅记录真实执行结果、验证边界和剩余风险，不属于产品能力实现。

未新增或修改以下计划内产品文件：

- `onboard/scripts/o6_o7_live_sensor_dataset_capture.py`
- `onboard/tests/test_o6_o7_live_sensor_dataset_capture.py`
- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/o6_o7_live_sensor_dataset_replay.md`
- `docs/navigation/field_route_evidence_manifest.md`

## 接口影响与实现内容

- 产品代码、ROS2 message/action、O6 archive API、O7 consumer 和数据库合同均无变化。
- 没有新增 dataset wrapper、dataset endpoint 或 `dataset_id`。
- 唯一 inventory 记录 `inventory_invocation_count=1`、`live_capture_invocation_count=0`、`capture_gate=false`。
- ROS setup 可用；`ros2 bag record --help` 同时证明 sqlite3 storage、`--storage` 和 `--max-bag-size` 可用。
- `/tmp` 可用空间为 `994639872` bytes，高于 `67108864` bytes 门槛；`conflicting_recorder_count=0`。
- `ros2 topic list -t` 中 `/scan` 类型为 `sensor_msgs/msg/LaserScan`，但 bounded `ros2 topic info -v /scan` 返回 exit `1` 和 `Unknown topic '/scan'`，因此 required publisher count 未确认，门槛 fail closed。
- `/odom`、`/tf`、`/tf_static` 的类型匹配且 publisher count 均为 `1`，只保留为新 sprint 中 required gate 恢复后的可选候选；本 sprint `selected_topics=[]`。
- `/camera/image_raw` 与 `/diagnostics` 未确认类型和 publisher，不进入候选；`/map` 与 `/amcl_pose` 明确排除。
- inventory 期间观测到 ROS CLI daemon 的进程启动时间落在调用窗口内。虽然没有显式执行 runtime start/stop 命令，仍按副作用记录 `automatic_ros2_cli_daemon_start_observed=true`、`runtime_mutation_free=false`。

## 失败定位

`capture_gate=false` 的 exact blockers 为：

1. `required_scan_publisher_count_not_confirmed`
2. `scan_topic_info_verbose_exit_1_unknown_topic`
3. `automatic_ros2_cli_daemon_started_during_inventory_window`

核心失败不是磁盘、rosbag/sqlite3 能力或冲突 recorder，而是同一 bounded inventory 内 `/scan` graph 观测不一致：topic list 可见类型，但 verbose info 无法确认 publisher。按 tech plan，必需 `/scan` publisher count 未达到可证明的 `>=1` 时必须停止 live 阶段。

## 未执行项与安全边界

- 未执行第二次 inventory，也未执行任何 `ros2 bag record`；`live_capture_invocation_count=0`。
- 未执行 `ros2 bag play`、topic publish、`/initialpose`、action goal、runtime start/stop、控制或运动。
- 未生成 DB3、metadata、hash、message/timestamp counts、semantic replay sections 或 artifact-bundle input。
- 未派发 Full-stack Phase C；没有 O6 write/readback 或 O7 selected-task consumer 证据。
- 未运行产品代码测试、构建、ROS2 build 或 hardware smoke。
- 固定边界：`safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## 验证结果

只验证了 inventory artifact 和本收口文件的结构/文本，不验证不存在的产品实现：

- `python3 -m json.tool .../read_only_inventory.json`：通过。
- Python 结构断言：通过；确认 inventory invocation 为 `1`、live capture invocation 为 `0`、`capture_gate` 与非空 blockers 一致、无 `dataset_id`、五个危险字段均为 false。
- required `rg`：通过；命中 invocation、gate、LaserScan、publisher、disk、recorder 和固定 false 字段。
- scoped `git diff --check`：通过。
- 产品代码测试/构建：未执行，因为本轮没有产品代码、测试或导航文档实现。

## 数据、样本与调试输出变化

- 新增唯一结构化 read-only inventory JSON，不包含 DB3、raw ROS payload、凭证、token、完整 response body 或 traceback。
- 没有生成 live dataset、route replay、keyframe、rosbag、Nav2 log 或 SLAM log。
- inventory 的候选集合仅用于解释未来门槛：required `/scan` 加可选 `/odom`、`/tf`、`/tf_static`；由于 required gate blocked，本 sprint 实际选中 topic 为空。

## 剩余风险与下一步建议

- 当前无法区分 `/scan` verbose 查询失败是 ROS CLI daemon 缓存、DDS graph 尚未稳定，还是 publisher 在 bounded 窗口内发生瞬态变化；因此不能宣称 `/scan` 可录制。
- ROS CLI daemon 自动副作用说明当前 inventory 形态不满足严格 `runtime_mutation_free=true`，也不能通过再包装 JSON 消除此事实。
- 本 sprint 不得重跑 inventory 或 capture，也不得新增 helper、review、readback、wrapper 或 Full-stack fixture 替代来绕过失败。
- 如 Product/CEO 仍要继续该能力，必须新建 sprint 并重新授权：优先设计 daemon-off 的直接 graph 查询，或在不启停机器人 runtime 的前提下等待 graph 稳定后执行新的 bounded inventory，再恢复 `/scan publisher_count>=1` gate。
- 若没有新的授权或可证明的 graph 稳定条件，应切换 Objective，避免第三次消费同一 inventory blocker。
- Product 后续只可按 blocked/fail-closed 做 `side2side_check.md` 与 `final.md` 验收；本轮不应调整 O6/O7 主进度。
