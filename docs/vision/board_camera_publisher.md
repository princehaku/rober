# Board Camera Publisher

`ros2_trashbot_vision/camera_publisher` 提供一个最小真实相机 ROS2 publisher，
用于把板上的 `cv2.VideoCapture` 设备发布到 `/camera/image_raw`，服务真实路线采样、
keyframe 证据和 bringup smoke。

## 设计边界

- 默认 **不启动**。只有 `bringup.launch.py` 显式传 `camera_enabled:=true` 时才拉起。
- 设备打不开时 **fail closed**：节点启动直接失败，不伪造帧，不回退到 mock 图像。
- 读帧失败时 **fail closed**：记录可读错误并跳过该帧，不补空白图。
- 不修改串口、底盘、速度、LiDAR 或 vendor firmware 默认值。

## 参数

- `device`：相机设备路径或数字索引；`bringup.launch.py` 与 `learn.launch.py` 现场默认 `/dev/video1`
- `topic`：发布 topic；默认 `/camera/image_raw`
- `frame_id`：图像 header frame；默认 `camera`
- `width`：请求宽度；默认 `640`
- `height`：请求高度；默认 `480`
- `fps`：请求帧率；默认 `15.0`

如果 `device` 是纯数字字符串（例如 `0`），节点会把它当作 OpenCV index；
否则按路径处理并展开 `~`。

## Launch 用法

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  camera_enabled:=true \
  camera_topic:=/camera/image_raw \
  camera_frame_id:=camera \
  camera_width:=640 \
  camera_height:=480 \
  camera_fps:=15.0
```

本轮 bringup smoke 只允许采样 topic，例如：

```bash
ros2 topic hz /camera/image_raw --window 2
ros2 topic echo --once /camera/image_raw
```

不允许因为验证相机而发布 `/cmd_vel`。

## 2026-06-09 sensor-only smoke 组合

从 `sprints/2026.06.09_23-20_board-bringup-blocker-fix` 开始，`bringup.launch.py`
新增 `base_enabled`，用于现场只验证传感器 topic 时跳过 `esp32_bridge`，避免
`upper_robot_api.py` 常驻占用 `/dev/ttyS5` 影响 smoke。推荐命令：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
```

这个命令的目标仅是证明 `/camera/image_raw`、`/scan`、`/tf_static` 和 `/map`
能够共同进入 ROS graph，不代表：

- WAVE ROVER 底盘 UART 已通过 HIL；
- `base_link -> laser_frame` 已完成机械标定；
- 建图、导航或运动链路已经完成。

## 2026-06-09 实板设备结论

在 `root@192.168.1.11:37878` 实板上执行 `v4l2-ctl --list-devices` 和 OpenCV probe 后，确认：

- `/dev/video0` 是 `cedrus (platform:cedrus)`，属于 Orange Pi H618 的 V4L2 编解码设备，不是 USB 摄像头采集节点。
- `USB Composite Device: DV20 USB` 提供 `/dev/video1` 与 `/dev/video2`。
- 其中 `/dev/video1` 具备 `Video Capture` 能力，OpenCV 实测 `opened=True read=True`。
- `/dev/video2` 是 metadata 节点，OpenCV 不能作为图像输入打开。

因此当前实板的默认相机参数已经固化为：

```bash
camera_enabled:=true
```

`bringup.launch.py` 与 `learn.launch.py` 在 `camera_enabled:=true` 且未显式传
`camera_device` 时会使用 `/dev/video1`。`/dev/video0` 只适合作为失败样例保留在排查记录里，
不应继续作为这块板的现场采样设备假设。不同设备批次如枚举变化，仍可显式传
`camera_device:=...` 覆盖默认值。

## 2026-06-10 ROS2 topic path 结论

在 `root@192.168.1.11:37878` 实板上，root shell 直接执行 `ros2` 仍不在 `PATH`。
本轮确认可用的 ROS2 source 链是：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
```

source 后 `ros2 pkg prefix ros2_trashbot_vision` 和 `ros2 pkg prefix ros2_trashbot_bringup`
均能解析到 `/root/rober/onboard/install/...`。现场最小 camera publisher smoke 使用：

```bash
ros2 run ros2_trashbot_vision camera_publisher --ros-args \
  -p device:=/dev/video1 \
  -p topic:=/camera/image_raw \
  -p width:=640 \
  -p height:=480 \
  -p fps:=2.0
```

实测结果：

- `/camera/image_raw` 出现在 ROS graph，`ros2 topic info` 显示 `sensor_msgs/msg/Image`、`Publisher count: 1`。
- subscriber 收到 `640x480 bgr8` 图像，`step=1920`、`data_len=921600`。
- `ros_camera_topic_proven=true`：已证明 `/dev/video1` 可以经 `camera_publisher` 发布到 `/camera/image_raw`。
- `visible_content_proven=false`：图像仍近黑，`mean_luma=0.21674`、`dynamic_range_luma=0.9266`、`non_black_ratio=0.0`。

因此当前只能宣称 ROS2 camera topic 主链路可发布消息，不能宣称已经有可用视觉路线内容。
下一步必须在现场确认镜头盖、遮挡、朝向、光照和 USB 摄像头本体；在 `visible_content_proven=true`
之前，不应把该画面用于路线关键帧、视觉定位、障碍识别或远程可视验收。

当前实板仍以 `/dev/video1` 作为真实相机。`/dev/video0` 是 Cedrus decoder；
launch 默认值已从 `/dev/video0` 固化为 `/dev/video1`，因此现场运行可省略 `camera_device`：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  camera_enabled:=true \
  camera_width:=640 \
  camera_height:=480 \
  camera_fps:=2.0
```

本轮只修正默认设备选择，`visible_content_proven=false` 仍成立：在可见内容被证明前，
不能把这路画面用于路线关键帧、视觉定位、障碍识别或远程可视验收。

## 本地资料来源

- `docs/vendor/VENDOR_INDEX.md`
  - 明确 Orange Pi Zero 3 是项目主 SBC，不能把 Raspberry Pi 假设直接当项目结论。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - vendor `base_config.use_lidar: false` 说明 LiDAR 在参考 app 中是可选能力，因此本项目也保持 launch 默认关闭。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
  - vendor Raspberry Pi 参考 app 的 USB camera 分支使用 `cv2.VideoCapture(0)`。
- `root@192.168.1.11` 实板命令证据
  - `v4l2-ctl --list-devices`
  - `v4l2-ctl --all -d /dev/video1`
  - OpenCV `VideoCapture('/dev/video1')`
- `docs/interfaces/o7_realtime_hardware_sources.md`
  - 明确 vendor app 只证明 Raspberry Pi 参考能力，不证明 Orange Pi CSI、Picamera2、
    ALSA 编号或 RTC/云端链路已在 rober 项目中打通。

因此当前实现只采纳 vendor 的最小 USB/OpenCV 入口思路，不引入 Raspberry Pi
`Picamera2`、boot overlay 或音视频栈假设。
