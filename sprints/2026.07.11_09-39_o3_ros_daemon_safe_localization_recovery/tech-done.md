# O3 ROS Daemon-safe Localization Recovery Tech Done

## sprint_type

sprint_type: epic

## 自主能力目标和本轮抓手

- 目标：把 no-motion live localization probe 从“把 `!rclpy.ok()` 误判成 topic 缺失”推进到
  daemon-safe、可分层的现场定位诊断。
- 抓手：给 ROS graph 只读查询补 `ros2 daemon stop/start + retry`，并把 root cause 从 generic
  ROS CLI fault 下钻到 `/scan`、`/amcl_pose`、lifecycle、TF 和 refresh readback。

## 实际改动

- `onboard/scripts/field_route_evidence_preflight.py`
  - 新增 ROS daemon fault 识别。
  - 只对 `ros2 topic/list/type/info/echo`、`ros2 lifecycle get`、`tf2_echo` 启用一次 daemon-safe retry。
  - artifact 新增 `daemon_fault_detected`、`daemon_recovered`、`retry_attempts`、
    `recovered_topics`、`unrecovered_blockers`、`ros_daemon_health`、
    `ros_cli_retry_summary`、`scan_topic` 和 `root_cause_layers`。
  - root cause 分类从 generic topic missing 细化到 `map_server_not_active`、
    `amcl_not_active`、`amcl_no_pose`、`tf_missing`、`lidar_missing`。
- `onboard/tests/test_field_route_evidence_preflight.py`
  - 新增 daemon fault recovery 单测。
  - 扩展 root-cause summary 单测，覆盖 scan topic、daemon retry 摘要和层级化 blocker。
- `docs/navigation/field_route_evidence_preflight.md`
  - 补充 daemon-safe retry 约束、artifact 新字段和 blocker 分层规则。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 `!rclpy.ok()` 应归类为 ROS graph/daemon 层，并说明 recovery 后的下一轮动作。
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/local_preflight.raw.json`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/live_daemon_safe_localization.raw.json`

接口影响：

- 仅影响 `field_route_evidence_preflight.py` 的 JSON artifact 摘要字段。
- 不改 `TrashStatus`、motion command、WAVE ROVER 协议、串口参数或任何底盘执行入口。

## 验证结果

```text
python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py
通过
```

```text
python3 -m unittest onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
Ran 126 tests in 0.268s
OK (skipped=1)
```

```text
python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
Ran 23 tests in 0.041s
OK
```

```text
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/local_preflight.raw.json
status=dry_run_template_only_not_proven
```

```text
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/live_daemon_safe_localization.raw.json
status=blocked_refresh_readback_failed
```

```text
git diff --check -- onboard/scripts/field_route_evidence_preflight.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_upper_robot_api.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery
通过
```

## 真实板 artifact 摘要

artifact 路径：

- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/live_daemon_safe_localization.raw.json`

顶层安全字段：

- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

最终 live artifact 结果：

- `daemon_fault_detected=false`
- `daemon_recovered=false`
- `retry_attempts=0`
- `recovered_topics=[]`
- `unrecovered_blockers=[]`
- `/scan observed=true`
- `/amcl_pose observed=false`
- `map->odom observed=false`
- `map->base_link observed=false`
- `nav2_refresh.status=refresh_command_failed`
- `nav2_refresh.returncode=28`
- `nav2_refresh.failure_summary=curl: (28) Operation timed out after 38000 milliseconds with 0 bytes received`

最终 root cause 已经不再停在 generic ROS graph fault，而是收口到：

- `scan_topic.publisher_count=1`
- `map_topic.topic_type=null`
- `amcl_pose_topic.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped`
- `amcl_pose_topic.publisher_count=0`
- `/map_server lifecycle unavailable`
- `/amcl lifecycle unavailable`
- `/planner_server lifecycle unavailable`
- `map->odom` / `map->base_link` 仍报 `Invalid frame ID "map"`
- `root_cause_layers=[map_server_not_active, amcl_not_active, tf_missing]`

## 数据、样本和调试输出变化

- local dry-run artifact 现在会带 daemon-safe retry 合同字段。
- live artifact 现在会显式区分：
  - daemon fault 是否发生；
  - daemon 是否恢复；
  - 哪些 graph 查询被恢复；
  - 当前 blocker 是 ROS graph 还是 map server / AMCL / TF / refresh readback。

## 失败定位

- 本轮最终失败层是 `blocked_refresh_readback_failed`，不是 motion safety 边界破坏。
- 实时 `/scan` 已可读，说明 LiDAR topic 本身不是当前主 blocker。
- `/amcl_pose` 话题类型存在但 `publisher_count=0`，且 `/amcl` lifecycle unavailable。
- `map` frame 仍不存在，`tf2_echo map odom` / `map base_link` 都停在 `Invalid frame ID "map"`。
- `/api/nav2/proof/refresh` 仍以 `curl (28)` 超时结束，说明 refresh readback 依旧没穿过当前 runtime/localization blocker。

## 剩余风险和下一步建议

- 当前还没有 `amcl_pose_observed=true`、`map_to_odom=true`、same-run path generation success，也没有 route/material 新增证据。
- daemon-safe retry 已经把 ROS graph fault 从主 blocker 中剥离，但并不证明 map server、AMCL 或 planner 真正 ready。
- 下一轮应优先排查：
  1. `o11_nav2_lifecycle.sh` / bringup 是否真的拉起 `/map_server`、`/amcl`、`/planner_server`；
  2. `/map` 为什么仍无 topic type；
  3. `/amcl_pose` 为什么 type 存在但 publisher 仍为 0；
  4. 在 lifecycle ready 之后再复跑 refresh，确认 `curl (28)` 是 helper 卡住还是 runtime 未起。
