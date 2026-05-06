# ros_rbs - Autonomous Trash Collection Robot

ROS2 自主导航扔垃圾小车项目。

## 架构

5 个包协同工作：
- **ros2_trashbot_interfaces** - 自定义 msg/srv/action
- **ros2_trashbot_nav** - Nav2 导航 + waypoint_manager + map_recorder
- **ros2_trashbot_vision** - 摄像头垃圾检测 (cv_bridge)
- **ros2_trashbot_behavior** - task_orchestrator 状态机 + action server
- **ros2_trashbot_bringup** - 启动文件

## 工作流程
1. **学习阶段**: `learn.launch.py` → SLAM建图 + 人工驾驶记录航点
2. **自主阶段**: `autonomous.launch.py` → 加载地图 → 巡逻 → 检测垃圾 → 导航收集 → 送至垃圾桶

## 构建命令
```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```
