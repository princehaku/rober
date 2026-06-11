# 2026.06.11 17:00 Current Camera Visible Content Probe

## sprint_type

micro

## owner

`robot-hardware-engineer`

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

## 本轮功能点设计

- 目标只做 `camera-only` 当前状态再判定，不触碰底盘运动、Nav2、雷达、map reset 或 `/api/base/manual` 非 stop 任何动作。
- 只允许读取真实上位机 `http://192.168.1.11:8787` 的 camera health/devices，再通过 `ssh root@192.168.1.11 -p 37878` 做 `/dev/video1` 的 V4L2/OpenCV probe。
- 判定目标只有三类：
  - `visible_content_proven=true`
  - `near_black`
  - `first-frame timeout`
- 若能读到 frame，必须保存至少一张 sample JPG 和一份 metrics JSON。
- 若是 near-black，只做非破坏性、可恢复的 V4L2/OpenCV 组合试探，优先覆盖 `/dev/video1` 当前已知 MJPG/YUYV 与 640x480；可临时读取 controls 并尝试曝光/亮度/对比度等参数，但必须先记录原值，结束时恢复原值，并输出 restore log。
- 若判断修改 controls 风险过高，可不改，但必须在留档中说明原因，不得默默跳过。
- cleanup/readback 必须确认：
  - `active_peer_count=0`
  - `lsof/fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5` 无本轮残留
  - 服务状态可回读

## 本轮验收命令

- `git diff --check`
- 真实上位机 camera health/devices readback
- SSH V4L2/OpenCV probe，保存 raw logs、metrics JSON、sample JPG（若读到 frame）
- cleanup/readback log

## 风险边界

- 本轮不写 `onboard/**`、不改 `docs/vendor/**`、不改 service/launch/firmware/硬件配置。
- 仅在 `docs/vision/board_camera_publisher.md` 和 `docs/hardware/board_sensor_stack_smoke.md` 做必要的状态同步，若事实未变化则不做无意义改动。
- 资料来源以 `docs/vendor/VENDOR_INDEX.md` 为准；Orange Pi / WAVE ROVER / UART / controls 参数不得凭记忆补写。

## 实际改动

- `sprints/2026.06.11_17-00_current_camera_visible_content_probe/tech-done.md`
  - 先写入本轮 camera-only 设计边界，再回填真实 probe 结果、artifact 和 cleanup 读回。
- `docs/vision/board_camera_publisher.md`
  - 同步当前相机状态：本轮 default OpenCV probe 打开成功但 12 次读帧失败，当前仍不能声明可见内容。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 同步本轮 sensor smoke 的 camera-only 收口结果，便于后续现场复核。

## 真实 probe 结果

- 真实上位机 camera health/devices 读回
  - `status=ready`
  - `active_peer_count=0`
  - `active_peer_ids=[]`
  - `/dev/video0`、`/dev/video1`、`/dev/video2` 均可枚举
- 远端 `v4l2-ctl --list-devices` 读回
  - `cedrus (platform:cedrus)` 仍对应 `/dev/video0`
  - `USB Composite Device: DV20 USB` 仍对应 `/dev/video1` / `/dev/video2`
- OpenCV default probe
  - `open_ok=true`
  - `read_ok=false`
  - `attempts=12`
  - `first_frame_timeout=true`
- 后续 `MJPG 640x480` 格式切换尝试只写出 `mjpg_640x480_set_fmt.txt`，但脚本在这一步被收口终止，未形成可用 frame/metrics。
- 没有保存 sample JPG，也没有保存来自有效 frame 的 metrics JSON。
- 当前结论：
  - `visible_content_proven=false`
  - 根因更像 `first-frame timeout`，而不是 `near-black`
  - 依据：default probe 已能打开设备，但 12 次 `read()` 全失败；未进入可比较的 frame 统计阶段

## cleanup/readback

- `trashbot-upper-robot-api.service`：`active`
- `trashbot-local-webrtc-camera.service`：`active`
- `active_peer_count=0`
- `lsof /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5`：无输出
- `fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5`：无输出
- controls 读回仍为原值；`restore` 阶段曾报 `Permission denied`，但最终回读没有变化，不能写成恢复修改成功：
  - `brightness=0`
  - `contrast=256`
  - `saturation=250`
  - `gamma=20`
  - `gain=4`
  - `power_line_frequency=0`
  - `white_balance_temperature=4500`
  - `sharpness=100`
  - `backlight_compensation=0`
  - `auto_exposure=3`
  - `exposure_time_absolute=80`

## artifact 路径

- `sprints/2026.06.11_17-00_current_camera_visible_content_probe/artifacts/remote_capture/`
  - `00_camera_health_before.json`
  - `01_camera_devices_before.json`
  - `02_v4l2_list_devices.txt`
  - `03_v4l2_all_formats_controls_before.txt`
  - `04_lsof_before.txt`
  - `05_fuser_before.txt`
  - `06_controls_before.txt`
  - `10_default.json`
  - `mjpg_640x480_set_fmt.txt`
  - `probe.log`
- `sprints/2026.06.11_17-00_current_camera_visible_content_probe/artifacts/cleanup/cleanup_readback.log`
- 现阶段没有 sample JPG、也没有有效 frame metrics JSON。

## 验证命令结果

- `git diff --check`
  - 通过。
- 真实上位机 camera health/devices readback
  - 通过，见上方 `status=ready` 和 devices 枚举。
- SSH V4L2/OpenCV probe
  - 部分通过：default probe 完成，`open_ok=true` 但 `read_ok=false`，共 12 次读帧失败。
  - 后续 MJPG 格式切换尝试未推进到可用 frame，也没有产生 sample JPG 或有效 frame metrics JSON。
- cleanup/readback log
  - 通过，见 `cleanup_readback.log` 和上方 `lsof/fuser` 结果。

## 剩余风险和下一步现场动作

- 仍需现场确认镜头盖、保护膜、遮挡、朝向和输入源是否存在。
- 如果 DV20 实际是采集卡而非普通 USB 摄像头，需要确认输入源与制式兼容。
- 下一步现场动作是重查物理链路，而不是继续在软件侧扩大控制矩阵。
