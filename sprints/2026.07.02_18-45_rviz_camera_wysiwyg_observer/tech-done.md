# RViz Camera WYSIWYG Observer

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_bringup/rviz/trashbot_nav.rviz`：RViz2 只读工程观察配置新增 `Camera Image` 显示，订阅 `/camera/image_raw`，让地图、雷达、路线、定位和相机画面可以同屏排障。
- `onboard/src/ros2_trashbot_bringup/launch/rviz.launch.py`：启动参数说明同步写入 `/camera/image_raw`，明确该 launch 是观察入口。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`：静态合同测试锁住 RViz2 必须包含 `/camera/image_raw`，并继续禁止 GoalTool、SetInitialPose、SetGoal、Nav Goal。
- `docs/product/pc_tools_workstation.md`：同步产品边界：普通用户仍使用 PC `/map` 大地图和共享相机预览；RViz2/Foxglove 只是工程观察配套，不发车、不控制。

## 验证结果

- `cd onboard && python -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py`：通过，`Ran 23 tests in 0.041s`，`OK`。
- `git diff --check`：通过，无空白错误。
- `bash onboard/scripts/docker_humble_build.sh`：通过，Docker/Humble colcon 输出 `Summary: 6 packages finished [46.1s]`。
- `python -m pytest src/ros2_trashbot_bringup/test/test_launch_contract_static.py`：本机 Python 缺少 pytest，失败为 `No module named pytest`；已用标准库 `unittest` 和 Docker/Humble build 覆盖同一静态合同与安装态构建。

## 剩余风险

- 本轮只补 ROS2 工程观察配置，不验证真实相机是否出帧；相机实物仍需现场换高速 USB/带供电 Hub 后复测。
- 未执行任何会让小车移动的 Nav2、manual、keyboard、free-roam、delivery 或 `/cmd_vel` 操作。
