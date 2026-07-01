# ROS2 Foxglove 远程观察桥

## sprint_type

micro

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/foxglove_bridge.launch.py`
  - 新增项目包装的 Foxglove 远程观察 launch，默认 `address=0.0.0.0`、`port=8765`。
  - topic 白名单只覆盖地图、雷达、TF、里程计、路线、定位、相机图像、costmap 和 bridge sysinfo。
  - `client_topic_whitelist`、`service_whitelist`、`param_whitelist` 固定为 `(?!)`，避免远程浏览器观察面变成控制入口。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `map_display_foxglove_bridge_launch_command` 改为 `ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图工程观察折叠区同步展示项目包装命令。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 Foxglove launch command literal。
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/robotControlSummary.test.ts`
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 补齐 PC summary/DOM 和 ROS2 launch 静态合同测试。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
  - 同步说明：普通用户仍优先 `/map` PC 大地图；RViz2 本地观察，Foxglove 远程浏览器观察，不替代 PC 简易界面。

## 验证结果

- 已通过：`git diff --check`。
- 已通过：`python3 -m py_compile onboard/src/ros2_trashbot_bringup/launch/foxglove_bridge.launch.py onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`。
- 已通过：`python3 -m unittest onboard.src.ros2_trashbot_bringup.test.test_launch_contract_static`，23 tests OK。
- 本机缺 `pytest`，`python3 -m pytest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 失败于 `No module named pytest`；已用 `unittest` 和 Docker/Humble colcon 覆盖。
- 已通过：`cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts`，2 files / 245 tests passed。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。Vite 仍提示 bundle 超过 500 kB，为既有体积警告。
- 已通过：`bash onboard/scripts/docker_humble_build.sh`，`Summary: 6 packages finished [45.5s]`。
- 已通过：重启 PC workstation 到 `0.0.0.0:7001`，listener PID `70878`。
- 已通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回：
  - `map_display_foxglove_bridge_launch_command=ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py`
  - `map_display_foxglove_websocket_url=ws://192.168.1.11:8765`
  - `map_display_primary_action_label=进入地图大屏`
  - `map_display_default_zoom_percent=1000%`
  - `map_display_sends_motion_when_clicked=false`
  - `map_display_starts_foxglove=false`

## 剩余风险

- 本轮只交付 ROS2/Foxglove 远程观察配套，不执行真实 Nav2、键盘、自由移动或建图。
- `foxglove_bridge` 仍需在上车 ROS2 环境安装 `ros-humble-foxglove-bridge` 后才能实际启动；Docker/Humble 构建只证明项目 launch 文件安装和包构建未破坏。
- 完整目标仍缺真实运动证据：Nav2 同窗口 wheel L/R 非零、送达确认、键盘按住轮速、自由移动运行读回，以及相机 USB 链路恢复后的建图启动。
