# sprint_type: micro

## 实际执行

- 按 CEO 指定命令尝试跑通 SLAM 建图、路线采集、保存地图、路线转换和 fixed-route dry-run。
- 当前开发主机没有本地 `ros2` 命令，也没有本地 `ros-rbs-humble:dev` 或 `osrf/ros:humble-desktop` 镜像。
- 执行 `bash onboard/scripts/docker_humble_build.sh` 以准备 ROS2/Humble 容器，构建卡在 Docker base image metadata：

```text
#2 [internal] load metadata for docker.io/osrf/ros:humble-desktop
```

- 单独执行 `docker pull osrf/ros:humble-desktop`，60 秒内无任何输出，手动中断。当前阻塞判断为 Docker registry/base image 获取不可用，不是 ROS2 建图链路代码缺失。

## 已验证结果

- `docker image inspect osrf/ros:humble-desktop`：本地不存在。
- `docker image inspect ros-rbs-humble:dev`：本地不存在。
- `command -v ros2`：本机无 ROS2 CLI。
- `python3 -m py_compile` 验证以下入口无语法错误：
  - `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
  - `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/map_recorder.py`
  - `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py`
  - `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_csv_to_yaml.py`
  - `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
- `rg` 确认 `learn.launch.py` 已拉起：
  - `slam_toolbox/async_slam_toolbox_node`
  - `ros2_trashbot_nav/map_recorder`
  - `ros2_trashbot_nav/route_data_recorder`
- 离线路线转换与回放单测通过：

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m unittest \
  onboard/src/ros2_trashbot_nav/test/test_route_csv_to_yaml.py \
  onboard/src/ros2_trashbot_nav/test/test_route_data_recorder_manifest.py \
  onboard/src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py

Ran 23 tests in 0.538s
OK
```

## CEO 指定命令执行状态

- `ros2 topic list | egrep '/scan|/camera/image_raw|/odom|/tf|/map'`：未执行成功，原因是当前主机无 `ros2` CLI，Docker/Humble 容器未能构建。
- `ros2 launch ros2_trashbot_bringup learn.launch.py ...`：未执行成功，同上。
- `ros2 service call /trashbot/save_map std_srvs/srv/Trigger {}`：未执行成功，同上。
- `ros2 run ros2_trashbot_nav route_csv_to_yaml ...`：未执行成功，同上；其离线解析/转换相关单测已通过。
- `ros2 run ros2_trashbot_nav fixed_route_autonomy ...`：未执行成功，同上；其 dry-run 离线单测已通过。

## 剩余风险 / 下一步

- 需要恢复 Docker base image 拉取，或在已有 ROS2/Humble 上位机直接执行 CEO 指定命令。
- 一旦 ROS2 环境可用，下一步不要再做 review/handoff 小切片，直接执行：

```bash
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash
ros2 topic list | egrep '/scan|/camera/image_raw|/odom|/tf|/map'
ros2 launch ros2_trashbot_bringup learn.launch.py route_recorder:=true route_output_dir:=~/.ros/trashbot_runs/field_map_001 route_id:=trash_station_route route_camera_topic:=/camera/image_raw route_odom_topic:=/odom
```

- 本轮没有产生 `map.yaml`、`route.csv`、keyframe 或 replay JSONL；缺口不是代码入口，而是 ROS2 runtime/container 不可用。
