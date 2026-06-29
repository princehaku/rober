# 2026.06.30 10:55 ROS2 RViz 地图观察视图

sprint_type: micro

## 设计先行

本轮补 ROS2 原生地图观察配套，不启动机器人运动、不发送 Nav2 goal、不绕过 PC 安全确认。目标是给工程调试一个比 Web 地图更完整的 RViz2 视图：同屏看 `/map`、`/scan`、TF、Nav2 path 和 AMCL pose，同时明确真实发车仍走 PC 工作站固定执行入口。

## 实际改动

- `onboard/src/ros2_trashbot_bringup/rviz/trashbot_nav.rviz`
  - 新增只读 RViz 配置，显示 Grid、TF、Map、LaserScan、Nav2 Path 和 AMCL Pose。
  - 工具栏只包含 Interact、MoveCamera、Select、Measure，不包含 2D Goal/SetGoal。
- `onboard/src/ros2_trashbot_bringup/launch/rviz.launch.py`
  - 新增 `ros2 launch ros2_trashbot_bringup rviz.launch.py` 入口，默认加载项目 RViz 配置。
- `onboard/src/ros2_trashbot_bringup/CMakeLists.txt`
  - 安装 `rviz/` 目录到 bringup share。
- `onboard/src/ros2_trashbot_bringup/package.xml`
  - 增加 `rviz2` 和 `nav2_rviz_plugins` runtime 依赖声明。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 静态验证 RViz launch 可解析、配置显示关键 topic、且不包含目标下发工具。
- `onboard/README.md`、`pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 RViz2 调试命令、安全边界和 PC 普通首屏的关系。

## 验证结果

- 本机缺少 pytest，`python -m pytest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 未运行：
  - `/opt/homebrew/Caskroom/miniconda/base/bin/python: No module named pytest`。
  - 同一测试文件是 unittest 风格，已用下一条命令覆盖同一断言。
- 通过：`python -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - `Ran 21 tests in 0.035s`，`OK`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`
  - `Summary: 6 packages finished [43.2s]`。
  - 构建日志仅保留 Docker base image platform warning，不影响 colcon 结果。
- 通过：安装产物确认。
  - `onboard/install/ros2_trashbot_bringup/share/ros2_trashbot_bringup/launch/rviz.launch.py`
  - `onboard/install/ros2_trashbot_bringup/share/ros2_trashbot_bringup/rviz/trashbot_nav.rviz`
- 通过：`git diff --check`。

## 剩余风险

- 本轮只新增 RViz2 观察配置和文档，不启动 RViz、不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- RViz2 是工程调试工具；普通用户仍以 PC 工作站大地图和安全确认按钮为主入口。
