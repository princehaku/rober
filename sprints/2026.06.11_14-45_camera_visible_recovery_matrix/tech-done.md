# 2026-06-11 14:45 Camera Visible Recovery Matrix

## Sprint 类型

- `sprint_type: micro`
- Owner：Hardware Infra Engineer
- 目标：在不触碰底盘、不改产品代码的前提下，系统性采集 `/dev/video1`
  的 V4L2 格式、分辨率和有限控制矩阵，判断 near-black 是否能恢复为可用可见内容。

## 资料来源与安全边界

本轮硬件事实入口已读取 `AGENTS.md`、`OKR.md` 与 `docs/vendor/VENDOR_INDEX.md`。
WAVE ROVER 底盘边界采用以下本地 vendor 资料：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

采用的来源边界：

- WAVE ROVER 上下位机链路是 UTF-8 newline-delimited JSON over UART。
- vendor Raspberry Pi 默认 `/dev/ttyAMA0 @ 115200` 或参考路径不能外推为
  Orange Pi Zero 3 的项目默认串口。
- 底盘关键命令边界为 `T=1/T=13/T=130/T=131`，本轮全部未执行。
- 本轮未写 WAVE ROVER UART，未调用 `/api/base/manual` 非 stop，未发布
  `/cmd_vel`，未执行 Nav2，未发送任何非零运动。

## 实际改动

- 新增本 sprint 证据目录：
  - `sprints/2026.06.11_14-45_camera_visible_recovery_matrix/artifacts/remote_capture/rober_camera_visible_recovery_matrix_20260611_144351/`
  - `sprints/2026.06.11_14-45_camera_visible_recovery_matrix/artifacts/remote_capture/final_remote_readback.log`
  - `sprints/2026.06.11_14-45_camera_visible_recovery_matrix/artifacts/remote_capture/final_remote_readback_after_restore_rerun.log`
- 新增本记录：`sprints/2026.06.11_14-45_camera_visible_recovery_matrix/tech-done.md`
- 更新硬件与视觉文档：
  - `docs/hardware/board_sensor_stack_smoke.md`
  - `docs/vision/board_camera_publisher.md`

## 采样矩阵结果

远端：`root@192.168.1.11:37878`。
设备：`/dev/video1`，`USB Composite Device: DV20 USB`，driver `uvcvideo`。

原始 V4L2 状态：

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
- `exposure_time_absolute=80 flags=inactive`

格式/分辨率矩阵：

| 样本 | 请求 | 实际 | read_ok | gray_mean | gray_max | non_black_ratio_ge16 | edge_count | visible |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `orig_mjpg_640x480` | MJPG 640x480 | MJPG 640x480 | true | 1.0 | 1 | 0.0 | 0 | false |
| `orig_mjpg_1280x720` | MJPG 1280x720 | MJPG 1280x720 | true | 1.0 | 1 | 0.0 | 0 | false |
| `orig_mjpg_320x240_request` | MJPG 320x240 | MJPG 480x320 | true | 1.0 | 1 | 0.0 | 0 | false |
| `orig_mjpg_480x320_supported` | MJPG 480x320 | MJPG 480x320 | true | 1.0 | 1 | 0.0 | 0 | false |
| `orig_yuyv_640x480` | YUYV 640x480 | YUYV 640x480 | true | 0.000820 | 2 | 0.0 | 0 | false |
| `orig_yuyv_1280x720_request` | YUYV 1280x720 | YUYV 640x480 | true | 0.000840 | 1 | 0.0 | 0 | false |
| `orig_yuyv_320x240` | YUYV 320x240 | YUYV 320x240 | true | 0.000964 | 1 | 0.0 | 0 | false |

控制矩阵在 `MJPG 640x480` 下执行：

| 样本 | 控制组合 | gray_mean | gray_max | non_black_ratio_ge16 | edge_count | visible |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `ctrl_original_mjpg_640x480` | 原始控制 | 1.0 | 1 | 0.0 | 0 | false |
| `ctrl_auto_balanced_boost_mjpg_640x480` | auto + brightness/gain/gamma/backlight boost | 1.0 | 1 | 0.0 | 0 | false |
| `ctrl_auto_max_boost_mjpg_640x480` | auto + max boost | 1.0 | 1 | 0.0 | 0 | false |
| `ctrl_manual_exp_80_gain4_mjpg_640x480` | manual exposure 80 | 1.0 | 1 | 0.0 | 0 | false |
| `ctrl_manual_exp_1000_gain7_boost_mjpg_640x480` | manual exposure 1000 + boost | 1.000755 | 3 | 0.0 | 0 | false |
| `ctrl_manual_exp_10000_gain7_boost_mjpg_640x480` | manual exposure 10000 + boost | 2.266276 | 19 | 0.000182 | 70 | false |
| `ctrl_manual_exp_50000_gain7_boost_mjpg_640x480` | manual exposure 50000 + boost | 5.280280 | 40 | 0.004417 | 391 | false |

`ctrl_manual_exp_50000_gain7_boost_mjpg_640x480.jpg` 能看到极暗轮廓，但亮度、
非黑比例和边缘强度仍远低于可用画面阈值，因此 `visible_content_proven=false`。

## 控制恢复与清场

第一次脚本内恢复后，`summary.json` 记录到一个恢复缺口：

- `auto_exposure` 已回到 `3`。
- `exposure_time_absolute` 仍为 `50000 flags=inactive`，原因是自动曝光模式下该控制项 inactive。

已立即补恢复：

```bash
v4l2-ctl -d /dev/video1 --set-ctrl=auto_exposure=1
v4l2-ctl -d /dev/video1 --set-ctrl=exposure_time_absolute=80
v4l2-ctl -d /dev/video1 --set-ctrl=auto_exposure=3
```

最终 readback 文件
`sprints/2026.06.11_14-45_camera_visible_recovery_matrix/artifacts/remote_capture/final_remote_readback_after_restore_rerun.log`
显示所有原始控制项已恢复，包括：

- `auto_exposure=3 (Aperture Priority Mode)`
- `exposure_time_absolute=80 flags=inactive`
- `brightness=0`
- `contrast=256`
- `saturation=250`
- `gamma=20`
- `gain=4`
- `backlight_compensation=0`

最终 `lsof/fuser` 对 `/dev/video0`、`/dev/video1`、`/dev/video2`、`/dev/ttyS5`、
`/dev/ttyACM0` 无占用输出。

## 验证结果

运行并记录：

- `v4l2-ctl -d /dev/video1 --all`
- `v4l2-ctl -d /dev/video1 --list-ctrls`
- `v4l2-ctl -d /dev/video1 --list-formats-ext`
- OpenCV 采样矩阵与 JSON 汇总：
  `sprints/2026.06.11_14-45_camera_visible_recovery_matrix/artifacts/remote_capture/rober_camera_visible_recovery_matrix_20260611_144351/summary.json`
- 清场：
  `lsof /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5 /dev/ttyACM0`
  与
  `fuser -v /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5 /dev/ttyACM0`

`git diff --check`：通过，无输出。

## 失败定位

本轮没有把画面恢复到可用可见：

- `visible_content_proven=false`
- 格式/分辨率错误概率低：MJPG/YUYV 主要支持档位都能 read，但默认仍 near-black。
- 设备路径错误概率低：`/dev/video1` 是 UVC Video Capture，且 OpenCV 能稳定读帧。
- 相机完全无输出或采集链路全黑概率降低：高曝光手动档能出现很暗轮廓。
- 最符合证据的是物理暗场、镜头盖/保护膜/遮挡、摄像头朝向纯暗面或现场补光不足。
  如果 DV20 实际是采集卡，还需要现场确认输入源是否接入且源端不是黑屏。

## 剩余风险

- 仍不能放行 motion gate，下一轮只能做人工现场物理修正后的 camera/motion gate 复核。
- 需要现场人工把镜头对准高对比纹理目标并加强补光，或换 known-good USB UVC camera。
- 本轮没有执行 ROS2 camera publisher 复核；原因是目标限定为 V4L2/OpenCV 恢复矩阵，
  且上一轮已证明 ROS/WebRTC 链路活跃。
