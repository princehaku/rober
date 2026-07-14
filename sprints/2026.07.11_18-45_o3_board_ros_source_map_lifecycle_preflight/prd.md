# O3 Board ROS Source Map Lifecycle Preflight PRD

## 需求背景

固定路线送垃圾要进入 current-run path generation，必须先稳定拿到 `/scan`、`/amcl_pose`、`map->odom` 和 `path_generated`。最近 live artifact 已经证明 helper 不是旧的主进程 rclpy ImportError，而是在 board sourced shell、Python runtime 和 `map_server` lifecycle 层失败。

## 用户价值

用户不会关心 ROS source 细节，但会关心小车为什么不能生成路线并出发。本轮的用户价值是把“现场不能生成路线”拆成可执行的下一步：是环境 source 问题、Python/rclpy 问题、ROS CLI 问题，还是 map 文件/lifecycle 问题。

## 成功口径

接受任一结果：

- true-board artifact 证明 `ros2_cli_ok=true`、`rclpy_import_ok=true`，并把 blocker 收敛到 `map_server_lifecycle_failed` 或更具体 map load/lifecycle 原因；
- true-board artifact 证明 `ros2_cli_ok=false` 或 `rclpy_import_ok=false`，并输出命令路径、Python executable、`sys.path` 前几项、returncode/timeout/error 摘要；
- true-board 不可达时，本地 fail-closed artifact、单测和文档已落地，明确不调整 OKR。

不接受：

- 只重复 `ros2_command_unavailable_after_bash_source`，没有拆分 `command -v ros2` 与 `import rclpy`；
- 只修改文档或 checklist；
- 修改 `/scan` QoS 合同、O5/O6/O7 wrapper 或任何运动控制路径；
- 把 no-motion diagnosis 说成 HIL、route execution 或 delivery success。

## 证据字段要求

artifact 至少应可读回：

- `board_source_preflight.executed`
- `board_source_preflight.ros2_cli_ok`
- `board_source_preflight.rclpy_import_ok`
- `board_source_preflight.python_executable`
- `board_source_preflight.rclpy_file`
- `board_source_preflight.sys_path_head`
- `board_source_preflight.classification`
- `map_lifecycle_preflight` 或等价 lifecycle readback 摘要
- 顶层 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`

## OKR 对齐

- O5 当前约 85%，但缺真实 production external evidence；本轮不消费 O5 blocker。
- O1/O3 live path prerequisite 是本轮主线；成功拆出 source/lifecycle root cause 可推进 current same-run path generation 的前置证据。
- O6/O7 只有在后续形成 current-run route/delivery/operator material 时才消费，本轮不做 readback wrapper。
