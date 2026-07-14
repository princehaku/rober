# O3 Board ROS Source Map Lifecycle Preflight Tech Done

## Sprint Type

sprint_type: epic

## 自主能力目标和本轮抓手

本轮目标是把 true-board helper 在 sourced shell 里的前置失败拆成可复跑、可读回的 `board_source_preflight`，让现场 root cause 不再只停在笼统的 `ros2_command_unavailable_after_bash_source`。

本轮抓手：

1. 在 `o10_amcl_nav2_runtime_proof.py` 中增加短窗口只读 preflight，分别记录 `ros2` CLI、`rclpy` import、Python executable、`rclpy.__file__` 和 `sys.path[:8]`；
2. 在 preflight 失败时 fail-closed 跳过 `/scan` attempt、`/initialpose` 和 path generation，同时保留 no-motion false safety fields；
3. 把 `map_server` / `amcl` lifecycle 单独压成 `map_lifecycle_preflight`，让 artifact 明确区分 source/runtime 与 lifecycle blocker。

## 实际改动文件

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/tech-done.md`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/local_o10_board_ros_source_map_lifecycle_preflight.raw.json`
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/live_o10_board_ros_source_map_lifecycle_preflight.raw.json`

## 接口影响

- helper 新增 `proof.board_source_preflight`：
  - `ros2_cli_ok`
  - `rclpy_import_ok`
  - `python_executable`
  - `rclpy_file`
  - `sys_path_head`
  - `classification`
- helper 新增 `proof.map_lifecycle_preflight`：
  - `map_server_active`
  - `amcl_active`
  - `classification`
- 当 `board_source_preflight.ready=false` 时，helper 会 fail-closed 跳过 `/scan` topic probe、`/initialpose` publish 和 path generation，不发送任何运动控制。

## 实现内容

- 把原本单一 `ros2_check` 扩展为 `board_source_preflight()`，在同一个 sourced shell 中分别执行：
  - `command -v ros2`
  - `python3 -c 'import rclpy ...'`
- 用结构化分类覆盖现场常见 source/runtime blocker：
  - `board_source_preflight_ros2_cli_unavailable`
  - `board_source_preflight_rclpy_import_timeout`
  - `board_source_preflight_rclpy_import_failed_*`
  - `board_source_preflight_ready`
- 增加 `map_lifecycle_preflight` 摘要，把 `map_server` / `amcl` active 状态和 preflight 分类单独写进 artifact。
- 调整 root cause 逻辑：当 preflight 失败时，不再继续堆叠 `/scan_once_not_observed`、`map_to_odom_not_observed` 这类下游噪音，而是优先返回 board source/runtime 或 lifecycle 的更前置 blocker。

## 验证结果

### 1. 语法检查

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：exit `0`。

### 2. 定向单测

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：exit `0`，`Ran 63 tests in 2.238s`，`OK`。

### 3. 本地 fail-closed artifact

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/local_o10_board_ros_source_map_lifecycle_preflight.raw.json
```

结果：exit `2`，artifact 落盘。

关键字段：

- `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_unavailable`
- `proof.board_source_preflight.ros2_cli_ok=false`
- `proof.board_source_preflight.rclpy_import_ok=false`
- `proof.board_source_preflight.python_executable=null`
- `proof.map_lifecycle_preflight.classification=map_lifecycle_preflight_skipped_without_ros2_cli`
- `proof.map_server_active=false`
- `proof.amcl_active=false`
- `proof.path_generated=false`
- 顶层安全字段保持：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`

### 4. true-board helper

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：exit `0`。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

结果：exit `2`，helper 自然返回并写出最新 live artifact。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/live_o10_board_ros_source_map_lifecycle_preflight.raw.json
```

结果：exit `0`。

关键 live 字段：

- `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_unavailable`
- `proof.board_source_preflight.ros2_cli_ok=false`
- `proof.board_source_preflight.rclpy_import_ok=true`
- `proof.board_source_preflight.python_executable=/usr/bin/python3`
- `proof.board_source_preflight.rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`
- `proof.board_source_preflight.sys_path_head[:4]=["", "/root/rober/onboard/build/ros2_trashbot_behavior", "/root/rober/onboard/install/ros2_trashbot_behavior/lib/python3.10/site-packages", "/root/rober/onboard/build/ros2_trashbot_vision"]`
- `proof.map_lifecycle_preflight.classification=map_lifecycle_preflight_skipped_without_ros2_cli`
- `proof.map_server_active=false`
- `proof.amcl_active=false`
- `proof.path_generated=false`
- 顶层安全字段保持：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`

### 5. 锚点检索与 diff 检查

```bash
rg -n "board_source_preflight|ros2_cli_ok|rclpy_import_ok|map_server|lifecycle|safe_to_control|robot_control_executed|delivery_success|hil_pass" \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight
```

结果：exit `0`。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight
```

结果：exit `0`。

## 数据、样本或调试输出变化

- 新增 local artifact：
  - `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/local_o10_board_ros_source_map_lifecycle_preflight.raw.json`
- 新增 live artifact：
  - `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/artifacts/live_o10_board_ros_source_map_lifecycle_preflight.raw.json`
- 新增结构化字段：
  - `proof.board_source_preflight`
  - `proof.map_lifecycle_preflight`
- live 现场从旧的笼统 `ros2_command_unavailable_after_bash_source` 前移为更具体事实：
  - `ros2_cli_ok=false`
  - `rclpy_import_ok=true`
  - `python_executable=/usr/bin/python3`
  - `rclpy.__file__` 已定位到 `/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`

## 失败定位

当前最前置 true-board blocker 已拆成两层：

1. `board_source_preflight_ros2_cli_unavailable`
   - sourced shell 中 `command -v ros2` 在 6 秒窗口内 timeout
   - 这让 helper fail-closed 跳过 `/scan`、`/initialpose` 和 path generation
2. `rclpy` runtime 其实是通的
   - `rclpy_import_ok=true`
   - `python_executable=/usr/bin/python3`
   - `rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`

也就是说，本轮真实板不再只是“ROS source 可能有问题”的泛化猜测，而是更具体地收敛到：

- Python/rclpy runtime 已可用；
- 但同一 sourced shell 里的 `ros2` CLI 解析/返回仍异常慢或卡住；
- 因为 preflight 不 clean，`map_lifecycle_preflight` 当前被 fail-closed 标成 `skipped_without_ros2_cli`；
- 下游 `/scan`、`/amcl_pose`、`map->odom`、`path_generated` 不再作为本轮主 blocker 继续噪音化堆叠。

现场日志还暴露了 managed runtime 期间的 LiDAR 进程异常：

- `serial.serialutil.SerialException: device reports readiness to read but returned no data`

但这不是本轮第一根因；在 `ros2` CLI preflight 没 clean 前，它仍排在 board source blocker 之后。

## 剩余风险

- true-board 若仍存在 ROS source 漂移，`ros2` CLI 与 `rclpy` import 可能继续分裂为两个根因；
- 即使 preflight ready，`map_server` / `amcl` lifecycle 仍可能单独阻断 `/scan`、`/amcl_pose` 和 path generation；
- 本轮仍是 no-motion supporting evidence，不证明 `path_generated=true`、`route_execution_success=true`、`safe_to_control=true`、`hil_pass=true` 或 `delivery_success=true`。

## 下一条现场执行命令

```bash
ssh -p 37878 root@192.168.1.11 \
  'time bash -lc "source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; command -v ros2; python3 -c \"import rclpy,sys; print(rclpy.__file__); print(sys.path[:8])\""'
```

先单独确认 sourced shell 里为什么 `rclpy` import 能在 6 秒内返回，但 `command -v ros2` 仍 timeout；只有这层 clean 后，才值得再次进入 lifecycle `/scan` / AMCL 读数。
