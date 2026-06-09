# Board Hardware Device Probe

更新时间：2026-06-09 23:41 CST

## 已读 vendor 来源

1. `docs/vendor/VENDOR_INDEX.md`
   - 明确 Orange Pi Zero 3 不能直接套用 Raspberry Pi 设备名假设，UART 设备名必须以上板实际 Linux 节点为准。
2. `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
   - vendor 上位机参考代码会优先抓取 `glob('/dev/ttyACM*')[0]` 作为 LiDAR 串口，并用 `cv2.VideoCapture(0)` 作为最小 USB 相机入口。
3. `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
   - vendor 视频默认分辨率为 `640x480`，LiDAR 在 vendor app 中属于可选能力（`base_config.use_lidar: false`）。
4. `docs/vendor/waveshare_wave_rover/ugv_rpi/99-dai.rules`
   - vendor 仅提供特定 USB 设备权限规则，不能推出 Orange Pi 上当前 `/dev/video*` 或 `/dev/tty*` 的实际映射。

## 实际命令与关键输出

### 1. 板上设备枚举、占用与常驻进程

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "hostname; date; uname -a; ls -l /dev/video* /dev/ttyACM* /dev/ttyS* 2>/dev/null || true; fuser -v /dev/video0 /dev/video1 /dev/video2 /dev/ttyACM0 /dev/ttyS5 2>/dev/null || true; ps -ef | grep -E \"ros2|camera|webrtc|lidar|upper_robot_api\" | grep -v grep || true"'
```

关键输出：

- 主机：`op-z3-b6.home`
- 串口：
  - `/dev/ttyACM0` `root:dialout`
  - `/dev/ttyS5` `root:dialout`
- 视频：
  - `/dev/video0` `root:video`
  - `/dev/video1` `root:video`
  - `/dev/video2` `root:video`
- 常驻进程：
  - `local_webrtc_camera_smoke.py --video-source auto`
  - `upper_robot_api.py --base-port /dev/ttyS5 --base-baudrate 115200`
- 结论：现场确实已有一个服务长期占用 `/dev/ttyS5` 作为底盘串口入口；本次未见显式 LiDAR 常驻进程。

### 2. v4l2 设备识别

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "command -v v4l2-ctl && v4l2-ctl --list-devices && v4l2-ctl --all -d /dev/video0 || true"'
ssh -p 37878 root@192.168.1.11 'bash -lc "v4l2-ctl --all -d /dev/video1 || true; echo ---; v4l2-ctl --all -d /dev/video2 || true"'
```

关键输出：

- `/dev/video0`
  - 设备：`cedrus (platform:cedrus)`
  - 能力：`Video Memory-to-Memory`
  - 结论：这是 Orange Pi H618 的编解码设备，不是摄像头采集节点。
- `/dev/video1`
  - 设备：`USB Composite Device: DV20 USB`
  - 驱动：`uvcvideo`
  - 能力：`Video Capture`
  - 当前格式：`1280x720 MJPG`
- `/dev/video2`
  - 同属 `DV20 USB`
  - 能力：`Metadata Capture`
  - 结论：不是主图像流节点。

### 3. OpenCV 设备探测

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc '"'"'cat <<'"'"'"'"'"'"'"'"'PY'"'"'"'"'"'"'"'"' | python3
import cv2
for dev in ["/dev/video0", "/dev/video1", "/dev/video2"]:
    cap = cv2.VideoCapture(dev)
    ok = cap.isOpened()
    ret, frame = cap.read() if ok else (False, None)
    print(dev, "opened=", ok, "read=", ret, "shape=", None if frame is None else frame.shape)
    cap.release()
PY'"'"''
```

关键输出：

- `/dev/video0 opened= False read= False shape= None`
- `/dev/video1 opened= True read= True shape= (480, 640, 3)`
- `/dev/video2 opened= False read= False shape= None`

### 4. LiDAR 设备身份与别名

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "readlink -f /dev/ttyACM0 || true; udevadm info -q property -n /dev/ttyACM0 2>/dev/null | grep -E \"ID_|DEVPATH|DEVNAME\" || true; ls -l /dev/serial/by-id /dev/serial/by-path 2>/dev/null || true; readlink -f /dev/serial/by-id/* 2>/dev/null || true"'
```

关键输出：

- `/dev/ttyACM0`
- `ID_VENDOR_ID=34bf`
- `ID_MODEL_ID=ff0a`
- `ID_MODEL=STC_USB_Serial`
- `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0`

结论：当前实板 `ttyACM0` 的 USB 身份与项目内 LiDAR 参考测试所记录的 STC/`34bf:ff0a` 线索一致，可作为 LiDAR 候选口。

### 5. bringup topic smoke

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; timeout 25s ros2 launch ros2_trashbot_bringup bringup.launch.py camera_enabled:=false > /tmp/rober_bringup_smoke.log 2>&1 & pid=$!; sleep 12; ros2 topic list | grep -E \"^(/scan|/tf_static|/odom|/battery|/imu/data|/map)$\" || true; timeout 5s ros2 topic echo --once /tf_static 2>&1 || true; tail -n 80 /tmp/rober_bringup_smoke.log"' 
```

关键输出：

- 仅看到：`/map`
- `/tf_static`：`topic does not appear to be published yet`
- bringup 日志：
  - `Cannot open serial port /dev/ttyUSB0`
  - `serial.serialutil.SerialException: ... '/dev/ttyUSB0'`

### 6. 单独 LiDAR smoke

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; timeout -s INT 10s ros2 run ros2_trashbot_hardware lidar_driver --ros-args -p serial_port:=/dev/ttyACM0 -p frame_id:=laser_frame > /tmp/rober_lidar_smoke2.log 2>&1 & pid=$!; sleep 3; ros2 topic list | grep -E \"^(/scan|/lidar/raw_packet)$\" || true; timeout 4s ros2 topic echo --once /scan 2>&1 || true; wait $pid 2>/dev/null || true; tail -n 60 /tmp/rober_lidar_smoke2.log"'
```

关键输出：

- topic 列表出现：`/scan`
- `/scan` 单次回显：
  - `frame_id: laser_frame`
  - `range_max: 8.0`
  - 有效 `ranges` / `intensities`
- 日志：
  - `LiDAR serial started: /dev/ttyACM0 @ 150000`

## Camera `/dev/video*` 结论

1. 当前 `bringup.launch.py` 默认 `camera_device:=/dev/video0` 与实板不匹配。
2. `/dev/video0` 是 Orange Pi `cedrus` M2M 编解码节点，不是 UVC 摄像头。
3. 真正可被 OpenCV 打开的图像节点是 `/dev/video1`。
4. `/dev/video2` 仅是该 UVC 设备的 metadata 节点，不能作为 `camera_publisher` 图像输入。

建议的现场 launch 参数：

```bash
camera_enabled:=true camera_device:=/dev/video1
```

这是基于 `v4l2-ctl --list-devices` 与 OpenCV 实读帧结果得出的实板证据，不是猜测。

## LiDAR `/scan` / `/tf_static` 结论

### `/scan`

1. 当前短时 `bringup.launch.py` 没有启动 `lidar_driver`，因此仅靠这个 bringup 不会稳定产生 `/scan`。
2. 同一次 smoke 里 `esp32_bridge` 还因默认 `serial_port=/dev/ttyUSB0` 直接启动失败，进一步缩短了现场 topic 观察窗口。
3. 但单独运行 `lidar_driver --ros-args -p serial_port:=/dev/ttyACM0` 时，`/scan` 可以成功出现并回显真实数据。

因此本轮 `/scan` 缺失的根因不是“LiDAR 硬件坏了”，而是：

- 当前 bringup 组合未纳入 LiDAR node；
- 同时硬件桥默认串口仍指向一个在实板不存在的设备名。

### `/tf_static`

1. 当前 `bringup.launch.py` 只启动：
   - `esp32_bridge`
   - `waypoint_manager`
   - `map_recorder`
   - `camera_publisher`（可选）
   - `task_orchestrator`
   - `operator_gateway`（可选）
   - `remote_bridge`（可选）
2. 其中没有 `robot_state_publisher` 或 `static_transform_publisher`。
3. 本次 smoke 中 `ros2 topic echo --once /tf_static` 也明确返回未发布。

因此本轮 `/tf_static` 缺失是 launch 组成边界问题，不是短时采样偶然漏看。

## 剩余风险

1. 本次没有改 launch 默认值；因此后续若仍直接运行当前 `bringup.launch.py`，`esp32_bridge` 仍会默认尝试 `/dev/ttyUSB0`。
2. `upper_robot_api.py` 常驻使用 `/dev/ttyS5`，后续若要同时验证 ROS2 硬件桥与既有上位机服务，需要先约束串口独占关系。
3. LiDAR 单独 smoke 已证明 `/scan` 可出，但还没有把该 node 纳入现场主 bringup 验收链。
4. `timeout -s INT` 结束 `lidar_driver` 时暴露了一个退出期 `rclpy.shutdown()` 双重关闭异常；这不影响 `/scan` 可用性判断，但影响 smoke 日志整洁度。

## 下一步履约动作

1. 现场 camera smoke 统一改用 `camera_device:=/dev/video1` 采样 `/camera/image_raw`。
2. 现场 `/scan` gate 不要再用当前 `bringup.launch.py` 单独判定；应改为：
   - 单独 `lidar_driver` smoke，或
   - 一个包含 `lidar_driver` 的 field stack / full bringup。
3. 后续若进入修复轮，优先处理两个入口参数对齐：
   - `camera_device` 默认值与实板枚举不符；
   - `esp32_bridge` 默认串口与实板入口不符。
