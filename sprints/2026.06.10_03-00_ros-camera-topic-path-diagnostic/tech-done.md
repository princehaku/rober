# ROS Camera Topic Path Diagnostic Micro Sprint

- sprint_type: micro
- owner: robot-software-engineer
- time: 2026-06-10 03:00 Asia/Shanghai
- motion_commands_sent=false
- safe_to_control=false
- delivery_success=false
- ros_camera_topic_proven=true
- visible_content_proven=false

## 目标和资料来源

本轮目标是在不发任何底盘运动命令、不修改远端产品代码或持久化配置的前提下，通过真实上位机 SSH 验证 `/dev/video1` 到 ROS2 `/camera/image_raw` 的主链路。验收口径只要求证明 ROS topic 能发布真实相机消息，不要求可见环境内容通过。

资料来源：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/camera_publisher.py`
- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
- 上车命令输出：`artifacts/ssh_host_info.log`、`artifacts/ros2_environment_discovery.log`、`artifacts/remote_ros_camera_session.log`
- 上轮相机可见性证据：`sprints/2026.06.10_02-50_board-camera-visibility-diagnostic/artifacts/camera_visibility_summary.json`

硬件事实边界采用 `docs/vendor/VENDOR_INDEX.md`：主控为 Orange Pi Zero 3，底盘为 Waveshare WAVE ROVER，下位机为 ESP32。本轮只验证摄像头 ROS topic，不新增引脚、电压、UART、底盘协议或速度映射假设。

## 实际改动

新增本 sprint 内证据文件：

- `docs/vision/board_camera_publisher.md`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/ssh_host_info.log`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/ros2_environment_discovery.log`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/remote_ros_camera_session.log`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/remote_publisher_cleanup_check.log`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/remote_tgz_path.txt`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/scp_pull.log`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/remote_ros_camera_topic.tgz`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/remote_ros_camera_topic/*`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/camera_image_raw_sample.jpg`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/artifacts/ros_camera_topic_summary.json`
- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/tech-done.md`

文档同步内容：

- 将本轮 ROS2 source 链 `/opt/ros/humble/setup.bash` + `/root/rober/onboard/install/setup.bash` 写入 `docs/vision/board_camera_publisher.md`。
- 明确当前实板真实相机仍是 `/dev/video1`，`/dev/video0` 是 Cedrus decoder；launch 默认 `/dev/video0` 仅作可覆盖默认，现场必须显式传 `camera_device:=/dev/video1`。
- 同步 ROS topic 证据：`ros_camera_topic_proven=true`，subscriber 收到 `640x480 bgr8`、`data_len=921600`。
- 同步视觉内容边界：`mean_luma=0.21674`、`dynamic_range_luma=0.9266`、`non_black_ratio=0.0`、`visible_content_proven=false`。
- 明确不能宣称可用视觉路线内容，下一步需要现场确认镜头盖、遮挡、朝向、光照和 USB 摄像头本体。

未修改产品代码、launch、驱动、测试、其它 sprint 目录或远端长期配置。

## 本地代码事实

- `camera_publisher.py` 默认 `device=/dev/video0`，显式参数可覆盖为 `/dev/video1`。
- `learn.launch.py` 的 `camera_device` 默认仍是 `/dev/video0`，但相机节点只在 `camera_enabled:=true` 时启动。
- `bringup.launch.py` 的 `camera_device` 默认仍是 `/dev/video0`。
- 上轮真实上车 V4L2 诊断确认 `/dev/video1` 是 UVC 相机，`/dev/video0` 是 Cedrus decoder，`/dev/video2` 是 UVC metadata。因此真实运行必须显式传 `camera_device:=/dev/video1`，否则存在误绑 decoder 的风险。

## 验证结果

SSH 连通和主机信息：

```text
== host ==
op-z3-b6.home
2026-06-10T02:52:26+08:00
Linux op-z3-b6.home 6.1.31-sun50iw9 #1.0.4 SMP Thu Jul 11 16:37:41 CST 2024 aarch64 ...
== user ==
uid=0(root) gid=0(root) groups=0(root)
== video ==
/dev/video0
/dev/video1
/dev/video2
== command presence ==
python3=/usr/bin/python3
timeout=/usr/bin/timeout
v4l2-ctl=/usr/bin/v4l2-ctl
ffmpeg=/usr/local/bin/ffmpeg
```

ROS2 环境发现：

```text
FOUND /opt/ros/humble/setup.bash
FOUND /root/rober/onboard/install/setup.bash
WHICH_ROS2=/opt/ros/humble/bin/ros2
/root/rober/onboard/install/ros2_trashbot_vision
/root/rober/onboard/install/ros2_trashbot_bringup
```

第一次环境发现脚本失败定位：

```text
/opt/ros/humble/setup.bash: line 8: AMENT_TRACE_SETUP_FILES: unbound variable
```

根因是 smoke 脚本开启了 `set -u`，ROS2 `setup.bash` 读取未定义环境变量时退出。已去掉 `set -u` 后重跑通过，不属于 ROS 包或相机失败。

最小 camera publisher smoke 命令：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
ros2 run ros2_trashbot_vision camera_publisher --ros-args -p device:=/dev/video1 -p topic:=/camera/image_raw -p width:=640 -p height:=480 -p fps:=2.0
```

publisher 日志：

```text
publisher_alive=true
[INFO] [1781031272.400514148] [camera_publisher]: camera_publisher streaming /dev/video1 to /camera/image_raw with frame_id=camera, requested 640x480@2.00fps
publisher_cleanup=ok
```

补充清理复核：原 smoke 脚本杀掉了 `ros2 run` 父进程，但复查发现实际 Python `camera_publisher` 子进程 PID 85410 仍在运行。已执行定向 `kill 85410` 并复查，最终 `ps -eo pid=,args= | grep "[r]os2_trashbot_vision/lib/ros2_trashbot_vision/camera_publisher"` 无输出，远端没有残留相机 publisher。

`/camera/image_raw` topic 验证：

```text
== ros2 topic list ==
/camera/image_raw
/parameter_events
/rosout

== ros2 topic info /camera/image_raw ==
Type: sensor_msgs/msg/Image
Publisher count: 1
Subscription count: 0

== ros2 topic echo header ==
stamp:
  sec: 1781031278
  nanosec: 382722532
frame_id: camera
---

== ros2 topic echo shape fields ==
height: 480
width: 640
encoding: bgr8
step: 1920
```

`ros2 topic hz /camera/image_raw` 输出：

```text
average rate: 1.120
	min: 0.893s max: 0.894s std dev: 0.00053s window: 3
average rate: 1.120
	min: 0.893s max: 0.894s std dev: 0.00043s window: 5
average rate: 1.119
	min: 0.893s max: 0.895s std dev: 0.00054s window: 9
```

Python subscriber 一帧采样：

```text
image_message_observed=true
height=480
width=640
encoding=bgr8
step=1920
data_len=921600
expected_data_len_from_height_step=921600
mean_luma=0.21674
min_luma=0.0
max_luma=0.9266
dynamic_range_luma=0.9266
stddev_luma=0.07359
non_black_ratio=0.0
visible_content_candidate=false
```

本轮结论：

- `ros_camera_topic_proven=true`：已证明 `/dev/video1` 可以经 `camera_publisher` 发布到 ROS2 `/camera/image_raw`，且 subscriber 收到完整 `sensor_msgs/msg/Image`。
- `visible_content_proven=false`：图像亮度仍接近黑场，动态范围不足，不能证明可用环境纹理或视觉内容。
- `motion_commands_sent=false`：未发送 `/cmd_vel`、未写底盘串口、未启动任何运动控制。

文档同步验证：

```text
docs/vision/board_camera_publisher.md 已补充 2026-06-10 ROS2 topic path 结论：
- ROS2 source 链为 /opt/ros/humble/setup.bash + /root/rober/onboard/install/setup.bash
- 现场 smoke 必须显式 camera_device:=/dev/video1
- ros_camera_topic_proven=true
- visible_content_proven=false
- mean_luma=0.21674, dynamic_range_luma=0.9266, non_black_ratio=0.0
```

## 剩余风险

- `safe_to_control=false`：本轮只验证 ROS camera topic，不构成移动或自主运行准入。
- `delivery_success=false`：本轮没有验证送垃圾、到站、返回、投放或用户任务闭环。
- `visible_content_proven=false`：摄像头 topic 虽然通，但画面仍为黑/近黑，不能用于路线关键帧、视觉定位、障碍识别或远程可视确认。
- launch 默认 `/dev/video0` 仍是现场风险：真实运行必须显式传 `camera_device:=/dev/video1`，否则可能绑定 Cedrus decoder。按本轮文件范围只留证据，不修改产品代码。
- `ros2 topic hz` 实测约 1.12 Hz，低于请求的 2 Hz。可能受 OpenCV/V4L2 输出、曝光、CPU、ROS topic 工具采样窗口或设备帧率影响；本轮只要求 topic 主链路证明，未进一步调参。

## 协同需求

- Product：不需要重新裁剪范围；本轮是 O3 现场验证 lane 的相机 ROS topic 证据补齐。
- Hardware：需要现场确认镜头盖、遮挡、相机朝向、光照和 USB 摄像头本体是否异常。
- Autonomy：后续路线关键帧采集前，需要先拿到 `visible_content_proven=true` 的相机画面。
- Full-Stack：本轮不涉及手机/Web/API。
