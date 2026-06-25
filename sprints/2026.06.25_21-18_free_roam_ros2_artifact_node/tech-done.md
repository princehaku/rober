# Free Roam ROS2 Artifact Node

- sprint_type: micro
- time: 2026-06-25 21:18 Asia/Shanghai
- owner: robot-algorithm-engineer
- safe_to_control: false
- real_motion_triggered: false

## 实际改动

- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy_node.py`：新增 ROS2 接线节点，订阅 `/scan` 和 `/map`，生成策略 snapshot，写 `trashbot.free_roam_autonomy.runtime.v1` artifact，并在 `stop_required=true` 时调用 `/trashbot/stop`。
- `onboard/src/ros2_trashbot_nav/setup.py`：注册 `free_roam_autonomy_node` console script。
- `onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`：用 ROS stub 验证雷达距离过滤、地图覆盖统计、默认 artifact-only 不发布 Twist、双参数解锁后才发布受限 Twist。
- `docs/navigation/free_roam_autonomy.md`、`docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`：同步策略节点边界和 PC 仍锁定原因。

## 验证结果

- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy_node.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py`，`Ran 7 tests ... OK`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`，`Ran 4 tests ... OK`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_nav/test -p 'test*.py'`，`Ran 66 tests ... OK`。
- 通过：`npm run lint`。
- 通过：`npm test`，`167 passed`。
- 通过：`npm run build`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，`Summary: 6 packages finished [43.1s]`。

## 剩余风险

- 本轮没有运行真实 ROS2 节点或真车 HIL；代码默认不发布 `/cmd_vel`。
- 仍需上位机 summary 读取 runtime artifact 并回传给 PC，随后做 stop fallback、雷达避障和地图覆盖的低速 HIL。
