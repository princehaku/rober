# ROS2 地图工程观察配套落地

## sprint_type

micro

## 实际改动

- 修改 `onboard/src/ros2_trashbot_bringup/package.xml`：补充 `foxglove_bridge` 运行依赖，避免 PC 页面给出的 Foxglove 观察命令在真实上位机上变成“源码有、运行包缺失”。
- 修改 `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`：在 Foxglove 只读观察测试中同时锁定 `rviz2`、`nav2_rviz_plugins` 和 `foxglove_bridge` 运行依赖声明。
- 更新 `docs/product/pc_tools_workstation.md`：明确普通用户继续用 PC `/map` 大地图，RViz2/Foxglove 只作为 ROS2 工程观察配套；Foxglove bridge 只开放观察 topic，不开放发布、service 或参数能力。
- 上位机同步：把 `foxglove_bridge.launch.py`、`package.xml`、`test_launch_contract_static.py` 和最新 `trashbot_nav.rviz` 同步到 `root@192.168.1.11:/root/rober/onboard/src/ros2_trashbot_bringup/`。
- 上位机部署：先因 ROS APT 索引过期遇到 `404 Not Found`，随后执行 `apt-get update` 并安装 `ros-humble-foxglove-bridge=3.4.2-1jammy.20260625.192337`、`ros-humble-rosx-introspection=2.3.0-1jammy.20260607.144313`、`rapidjson-dev=1.1.0+dfsg2-7`。

## 验证结果

- 本地静态测试：`python3 -m unittest onboard.src.ros2_trashbot_bringup.test.test_launch_contract_static` 通过，`Ran 23 tests` / `OK`。
- 上位机重建：`cd /root/rober/onboard && source /opt/ros/humble/setup.bash && colcon build --symlink-install --packages-select ros2_trashbot_bringup` 通过，`Summary: 1 package finished [12.3s]`。
- 上位机静态测试：`python3 -m pytest src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 通过，`23 passed in 1.04s`。
- 上位机 RViz2 入口：`ros2 launch ros2_trashbot_bringup rviz.launch.py --show-args` 能返回 `rviz_config` 参数，默认配置指向 `trashbot_nav.rviz`。
- 上位机 Foxglove 入口：`ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py --show-args` 能返回 `address=0.0.0.0`、`port=8765`、`use_sim_time=false`、`sysinfo=true`。
- 上位机包状态：`ros2 pkg prefix foxglove_bridge` 返回 `/opt/ros/humble`，`dpkg-query -W` 显示 `ros-humble-foxglove-bridge 3.4.2-1jammy.20260625.192337`。
- 上位机 install 检查：`install/ros2_trashbot_bringup/share/ros2_trashbot_bringup/launch/foxglove_bridge.launch.py` 是指向源码的 symlink；RViz 配置中可见 `Name: Camera Image` 和 `Value: /camera/image_raw`。
- PC 只读状态：`/api/health` 仍返回 `workstation_listen_address=http://0.0.0.0:7001`、`default_robot_api_base_url=http://192.168.1.11:8787`；`/api/robot-control/summary` 返回 `map_tool=pc_big_map`、`map_url=/map`，ROS2 配套文案为 RViz2 本地工程调试、Foxglove bridge + Foxglove Web 远程浏览器观察。

## 剩余风险

- 本轮没有启动长期运行的 Foxglove bridge 服务，只验证 launch 入口和依赖已经具备；需要远程浏览器观察时可在上位机执行 `ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py`，再用 Foxglove Web 连接 `ws://192.168.1.11:8765`。
- Foxglove/RViz2 只是工程观察配套，不替代 PC 普通用户 `/map` 大地图，也不修复当前相机 USB full-speed 无首帧或底盘 wheel L/R 仍为 0/0 的硬件闭环问题。
- 本轮同步了上位机 bringup 相关文件；未做整仓上位机同步，避免扩大现场变更面。
