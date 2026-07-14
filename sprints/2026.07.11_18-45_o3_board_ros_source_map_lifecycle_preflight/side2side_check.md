# O3 Board ROS Source Map Lifecycle Preflight Side-to-Side Check

## 验收对象

- Sprint：`sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/`
- 实现 owner：`robot-algorithm-engineer`
- 验收 owner：`product-okr-owner`

## 用户价值和产品北极星

用户价值不是继续累积“ROS source 可能有问题”的泛化诊断，而是把当前 live no-motion blocker 收敛成下一条可执行现场命令：到底是 sourced shell 里的 `ros2` CLI 不可用，还是整套 ROS Python runtime / lifecycle 都坏了。产品北极星仍是 current-run path generation、Nav2 route execution 和 delivery 闭环；本轮只允许为这条主线做 supporting fail-closed 诊断前移。

## 计划口径 vs 实际结果

### 计划口径

- 拆分 `board_source_preflight`，分别记录 `ros2` CLI 与 `rclpy` import；
- 若 preflight 不 clean，则 fail-closed 跳过 lifecycle、`/scan`、`/initialpose` 和 path generation 下游噪音；
- 保持 no-motion，所有安全与控制字段继续为 false。

### 实际结果

- local artifact 与 live artifact 都已写出，且都为 `blocked_with_root_cause`；
- live 关键字段证明：
  - `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_unavailable`
  - `ros2_cli_ok=false`
  - `rclpy_import_ok=true`
  - `python_executable=/usr/bin/python3`
  - `rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`
  - `proof.map_lifecycle_preflight.classification=map_lifecycle_preflight_skipped_without_ros2_cli`
  - `map_server_active=false`
  - `amcl_active=false`
  - `path_generated=false`
- 顶层安全字段继续固定：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `route_execution_success=false`
  - `hil_pass=false`

## Side-to-Side 结论

本轮计划与实际基本一致：实现侧已经把 blocker 从“source 可能坏了”前移到更具体的 sourced shell `ros2` CLI preflight，并且没有把下游 `map_server`、`/scan`、AMCL、path generation 的 fail-closed 噪音误包装成新进展。产品验收通过，但通过的是“supporting blocked diagnostic progress”，不是 mission artifact 消费。

## OKR 映射和方向判断

- Objective 5：保持约 `85%`，因为没有新增真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实手机/browser 证据。
- Objective 1：保持约 `93%`，因为没有新增 current same-run path generation success、Nav2 route execution success、current live HIL pass 或真实 safe-to-control。
- Objective 6：保持约 `93%`，因为没有新增 current-run route/delivery/operator/production material 可消费。
- Objective 7：保持约 `93%`，因为没有新增 PC 侧可消费的 current-run route execution / delivery closure material。
- 方向判断：`继续` O3 no-motion 现场诊断链，但下一轮必须聚焦 sourced shell `ros2` CLI timeout 根因，不能回到 O5 support-only。

## 证据链缺口

- 还没有证明 `ros2_cli_ok=true`；
- `map_lifecycle_preflight` 仍是 `skipped_without_ros2_cli`，尚未进入 `map_server` / `amcl` clean active 读数；
- 仍没有 `/scan`、`/amcl_pose`、`map->odom`、`path_generated=true` 的 current-run 现场材料；
- 本轮不得计入 path generation、route execution、HIL、delivery 或 production cloud success。

## 下一轮建议

下一轮单独复验 sourced shell：

```bash
ssh -p 37878 root@192.168.1.11 \
  'time bash -lc "source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; command -v ros2; python3 -c \"import rclpy,sys; print(rclpy.__file__); print(sys.path[:8])\""'
```

先回答“为什么 `rclpy` import 能返回，但 `command -v ros2` 仍 timeout”，再决定是否进入 lifecycle / `/scan` / AMCL / path generation 复验。
