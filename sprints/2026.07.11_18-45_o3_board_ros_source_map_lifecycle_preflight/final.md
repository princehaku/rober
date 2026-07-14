# O3 Board ROS Source Map Lifecycle Preflight Final

## Sprint Summary

- Sprint：`sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/`
- Sprint type：`epic`
- Implementation owner：`robot-algorithm-engineer`
- Product closeout：`product-okr-owner`
- Outcome：accepted as O3/O1 supporting fail-closed diagnostic progress; latest live proof remains blocked before lifecycle、`/scan`、AMCL 和 path generation。

## 用户价值和产品北极星

本轮对用户的价值不是“又一轮 ROS 诊断”，而是把现场下一条命令收敛到可执行问题：当前 true-board sourced shell 中，到底是 `ros2` CLI 不可用，还是 Python/rclpy runtime 本身不可用。产品北极星保持不变，仍是 current-run path generation、Nav2 route execution、delivery 闭环和后续可消费的 mission artifact；本轮没有越过这些门槛。

## 复盘结论

上一轮 `17-43` 已把 blocker 收敛到 managed runtime / lifecycle / ROS2 source 层，但仍把 `ros2_command_unavailable_after_bash_source` 作为较粗分类。本轮在此基础上新增 `board_source_preflight` 与 `map_lifecycle_preflight`，把 sourced shell 中 `ros2` CLI 与 `rclpy` import 拆开读取，并在 preflight 不 clean 时 fail-closed 跳过 lifecycle、`/scan`、`/initialpose` 和 path generation 下游探测。

最终 live artifact 证明：

- `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_unavailable`
- `ros2_cli_ok=false`
- `rclpy_import_ok=true`
- `python_executable=/usr/bin/python3`
- `rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`
- `proof.map_lifecycle_preflight.classification=map_lifecycle_preflight_skipped_without_ros2_cli`
- `map_server_active=false`
- `amcl_active=false`
- `path_generated=false`
- 顶层 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`

因此本轮新的事实不是“ROS 全坏了”，而是“同一个 sourced shell 里 `rclpy` import 已可返回，但 `command -v ros2` 仍无法在 preflight 窗口内自然返回”，所以下游 lifecycle 与 localization/path 读数仍被 fail-closed 跳过。

## 实际改动

Product closeout 新增或更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/side2side_check.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/final.md`

Implementation owner 实际改动与验证留存在：

- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/tech-done.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/local_o10_board_ros_source_map_lifecycle_preflight.raw.json`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/live_o10_board_ros_source_map_lifecycle_preflight.raw.json`

## 验证证据

实现 owner 已提供并通过：

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
exit 0
Ran 63 tests in 2.238s
OK
```

```text
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/local_o10_board_ros_source_map_lifecycle_preflight.raw.json
exit 2
local_status=blocked_with_root_cause
```

```text
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
exit 2
```

```text
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' > sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/live_o10_board_ros_source_map_lifecycle_preflight.raw.json
exit 0
```

## OKR 结论

- Objective 5：保持约 `85%`。原因是没有新增真实公网、4G/SIM、production DB/queue、OSS/CDN、真实手机/browser 或真实 delivery 外部证据。
- Objective 1：保持约 `93%`。原因是没有新增 current same-run path generation success、Nav2 route execution success、current live HIL pass、真实 safe-to-control 或真实 delivery success。
- Objective 6：保持约 `93%`。原因是没有新增 current-run route/delivery/operator/production material 可消费。
- Objective 7：保持约 `93%`。原因是没有新增 PC 消费面需要的 current-run route execution / delivery closure material。
- KR 处理：`不归档 KR`，因为本轮没有任何 KR 达到“已完成并离开当前推进区”的证据门槛。
- 方向判断：`继续` O3 no-motion 现场诊断链，但只允许围绕 sourced shell `ros2` CLI timeout 根因推进，避免再次连续消费 O5 support-only blocker。

## Proof Boundary

本轮证明：

- `board_source_preflight` 已把 sourced shell 中 `ros2` CLI 与 `rclpy` import 拆开；
- 最新 live blocker 已前移到 `board_source_preflight_ros2_cli_unavailable`；
- no-motion safety 边界继续严格保持。

本轮不证明：

- `path_generated=true`
- `route_execution_success=true`
- `safe_to_control=true`
- `hil_pass=true`
- `delivery_success=true`
- production cloud / DB / queue / OSS / CDN / phone/browser external proof

## 剩余风险

- sourced shell 里 `ros2` CLI 与 `rclpy` runtime 继续分裂，可能意味着 PATH、shell init、wrapper 或 CLI 启动链存在独立问题；
- 在 `ros2_cli_ok` 没有恢复前，`map_server` / `amcl` lifecycle 仍只能被标记为 skipped，无法判断下一层真实 blocker；
- 只要 `path_generated=false` 与 `route_execution_success=false` 继续固定，O6/O7 当前 run material 仍不能安全计分。

## 下一轮建议

下一轮先单独复验 sourced shell：

```bash
ssh -p 37878 root@192.168.1.11 \
  'time bash -lc "source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; command -v ros2; python3 -c \"import rclpy,sys; print(rclpy.__file__); print(sys.path[:8])\""'
```

只有当 `command -v ros2` 能自然返回并确认 PATH/source 状态 clean 后，才重新进入 `map_server` / `amcl` lifecycle、`/scan`、`/amcl_pose`、`map->odom` 与 path generation 复验。
