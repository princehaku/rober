# 2026-06-11 10:15 Camera Visible Content Recovery

## sprint_type

micro

## owner

`robot-hardware-engineer`

## 任务范围

继续推进真实上车 evidence capture。本轮只排查真实上位机
`root@192.168.1.11:37878` 与 Robot API `http://192.168.1.11:8787`
上的摄像头/实时图传近黑问题，目标是尽可能让 PC 页面出现非黑可见内容。

未触碰底盘、运动、WAVE ROVER UART/serial、firmware、Nav2、雷达参数或
`docs/vendor/**`。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/13 在 Jupyter Lab 中显示实时画面.ipynb`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_en/13 Displaying Real-Time Video Stream in Jupyter Lab.ipynb`

边界：vendor 的 video/OpenCV 材料是 Raspberry Pi 上位机参考，只能说明
`640x480`、OpenCV/Picamera2/USB camera 示例和 camera resource 需要释放等通用参考；
不能外推为 Orange Pi 当前 `/dev/video*` 路径、制式或可见内容事实。

## 实际改动

- 新增 sprint artifacts：
  - `sprints/2026.06.11_10-15_camera_visible_content_recovery/artifacts/remote_capture/`
  - `sprints/2026.06.11_10-15_camera_visible_content_recovery/artifacts/browser/`
- 更新 `docs/hardware/board_sensor_stack_smoke.md`
  - 新增 2026-06-11 10:15 camera visible content recovery 结论、证据和现场动作清单。
- 更新 `docs/product/pc_tools_workstation.md`
  - 补充 PC 页面 WebRTC/canvas 已通但真实画面仍近黑，普通首屏保持简易入口。
- 新增本文件。

未改产品代码、测试代码、PC 普通首屏结构或服务配置。

## 真实上位机 probe 结果

关键 artifact：

- `artifacts/remote_capture/00_remote_camera_baseline.txt`
- `artifacts/remote_capture/01_v4l2_all_formats_controls.txt`
- `artifacts/remote_capture/02_camera_service_journal_tail.txt`
- `artifacts/remote_capture/04_camera_service_unit.txt`
- `artifacts/remote_capture/05_opencv_format_control_attempts.log`
- `artifacts/remote_capture/frame_probe_summary.json`
- `artifacts/remote_capture/07_ffmpeg_frame_probe.log`
- `artifacts/remote_capture/08_usb_media_kernel_probe.txt`
- `artifacts/remote_capture/18_final_upper_camera_health.json`
- `artifacts/remote_capture/19_final_cleanup_process_device_check.txt`

已证实：

- `trashbot-upper-robot-api.service` 与 `trashbot-local-webrtc-camera.service` 均为 `active`。
- WebRTC camera service 参数为 `--video-source auto --width 640 --height 480 --fps 15`。
- `/dev/video1` 是 `uvcvideo` 的 `USB Composite Device: DV20 USB` capture 节点。
- `/dev/video0` 是 `cedrus` platform decoder；`/dev/video2` 是 UVC metadata capture。
- `/dev/video1` 只有 `Input 1`，支持 MJPG `1280x720/640x480/480x320/1920x1080`
  与 YUYV `640x480/320x240`。
- service auto selection 日志显示 `/dev/video0` 打不开，随后选择 `/dev/video1`；
  近黑不是 auto 误选 `/dev/video0` 或 `/dev/video2`。

OpenCV 尝试结果：

| attempt | mean_gray | max_gray | nonblack_pixels_gt10 | edge_pixels |
| --- | ---: | ---: | ---: | ---: |
| default_yuyv_640x480 | 0.0013 | 2 | 0 | 0 |
| mjpg_640x480 | 1.0 | 1 | 0 | 0 |
| mjpg_1280x720 | 1.0 | 1 | 0 | 0 |
| mjpg_1920x1080 | 1.0 | 1 | 0 | 0 |
| yuyv_320x240 | 0.0012 | 1 | 0 | 0 |
| bright_gain_yuyv_640x480 | 0.0011 | 1 | 0 | 0 |
| manual_exposure_bright_yuyv_640x480 | 1.3289 | 79 | 7315 | 597 |
| default_restored_yuyv_640x480 | 0.0019 | 1 | 0 | 0 |

ffmpeg 交叉结果：

- YUYV `640x480`：`mean_gray≈0.019`、`max_gray=1`、`nonblack_pixels_gt10=0`。
- MJPG `640x480`：`mean_gray=1.0`、`max_gray=1`、`nonblack_pixels_gt10=0`。

解释：极端手动曝光能看到很暗轮廓，说明 UVC 管线和解码不是完全坏；
但默认/常规服务参数下没有可用可见内容。

## PC WebRTC smoke 结果

关键 artifact：

- `artifacts/browser/09_browser_camera_preview_open_state.json`
- `artifacts/browser/11_browser_camera_preview_after_close_state.json`
- `artifacts/browser/12_upper_camera_health_after_browser_close.json`
- `artifacts/browser/13_chrome_cdp_camera_open_canvas_state.json`
- `artifacts/browser/13_chrome_cdp_camera_open_viewport.png`
- `artifacts/browser/14_chrome_cdp_camera_after_close_state.json`
- `artifacts/browser/15_upper_camera_health_after_chrome_close.json`
- `artifacts/browser/16_chrome_cdp_camera_video_region.png`
- `artifacts/browser/17_upper_camera_health_after_video_region_close.json`

PC 页面流程：

- 填入 `http://192.168.1.11:8787`。
- 点击 `打开画面`，Chrome 隔离浏览器中 `<video>` 达到：
  - `srcObject=true`
  - `readyState=4`
  - `videoWidth=640`
  - `videoHeight=480`
  - `paused=false`
  - `currentTime≈10s`
- canvas `320x240` 采样：
  - `meanGray=1`
  - `minGray=1`
  - `maxGray=1`
  - `nonBlackPixelsGt10=0`
- video 区域截图仍为黑场。
- 点击 `关闭画面` 后，上位机 health 回到：
  - `active_peer_connections=0`
  - `active_peer_ids=[]`

结论：PC WebRTC signaling、video 元素播放、canvas 采样和 peer cleanup 均通；
但 PC 页面未达到非黑可见内容。

## 根因等级

根因等级：**物理输入侧待现场处理**。

软件侧已排除：

- 服务 auto 选源错误。
- `/dev/video0` decoder 或 `/dev/video2` metadata 被误用。
- MJPG/YUYV 格式选择错误。
- `640x480/320x240/1280x720/1920x1080` 分辨率选择错误。
- 常规亮度、对比度、增益、背光、伽马参数不足。
- PC proxy、WebRTC offer/answer、video 元素播放或 peer cleanup 问题。

未翻转：

- `visible_content_proven=false`
- `safe_to_control=false`
- `delivery_success=false`

## 验证命令

已运行：

```bash
ssh root@192.168.1.11 -p 37878 'systemctl is-active trashbot-upper-robot-api.service trashbot-local-webrtc-camera.service'
ssh root@192.168.1.11 -p 37878 'curl http://127.0.0.1:8787/api/camera/health'
ssh root@192.168.1.11 -p 37878 'curl http://127.0.0.1:8787/api/camera/devices'
ssh root@192.168.1.11 -p 37878 'v4l2-ctl -d /dev/video1 --all --list-formats-ext --list-ctrls'
ssh root@192.168.1.11 -p 37878 'python3 OpenCV format/control capture script'
ssh root@192.168.1.11 -p 37878 'ffmpeg YUYV/MJPG one-frame capture'
npm run api
npm run dev -- --port 5173
Chrome headless CDP PC WebRTC smoke
```

清理验证：

- 本地临时 workstation API、Vite 和 Chrome headless 已停止。
- 上位机正式服务仍 active。
- 上位机最终仅剩正式进程：
  - `local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 15`
  - `upper_robot_api.py --host 0.0.0.0 --port 8787 ...`
- 最终 health 保存为 `artifacts/remote_capture/18_final_upper_camera_health.json`。
- 验收补清理修复：历史 `frame_probe_summary.json` 的 `final_controls.auto_exposure`
  误留在 `1 (Manual Mode)`。已在真实上位机按原始记录恢复 `/dev/video1`：
  `auto_exposure=3`、`exposure_time_absolute=80`、`brightness=0`、`contrast=256`、
  `saturation=250`、`gamma=20`、`gain=4`、`power_line_frequency=0`、
  `white_balance_temperature=4500`、`sharpness=100`、`backlight_compensation=0`。
  新 artifact `artifacts/remote_capture/20_final_v4l2_controls_restored.txt`
  显示恢复后 `auto_exposure: 3 (Aperture Priority Mode)`，其余控件均匹配原始记录；
  `artifacts/remote_capture/21_final_camera_health_after_control_restore.json`
  显示 camera health `status=ready`、`active_peer_connections=0`。

本地检查：

- `git diff --check`：通过。
- 文档改动不涉及 Python/PC 产品代码，因此无 `py_compile`、unittest、`npm run build/test/lint`
  强制触发项；本轮 PC smoke 以真实页面运行和 Chrome CDP artifacts 作为验证。

## 剩余风险和现场动作

剩余风险：

- DV20 设备可能是采集卡而非普通摄像头；若物理 HDMI/AV 输入未接入或制式不兼容，
  UVC 会正常出黑帧。
- 若镜头被遮挡、保护膜未移除、朝向暗处或环境光不足，软件侧无法把默认画面变成可用图传。
- 极端手动曝光能看到暗轮廓，但不适合作为常驻服务参数；不能把噪声/暗轮廓当作路线关键帧证据。

现场动作清单：

- 检查镜头盖、保护膜、遮挡、安装朝向和是否对着暗处/车体内部。
- 在镜头前放置强光高对比目标，重跑 OpenCV default YUYV 与 PC 页面 canvas。
- 若 DV20 是采集卡，确认输入源已开机、HDMI/AV 线已接好，输出分辨率/制式兼容。
- 更换一个已知可见画面的 USB UVC 摄像头接到同一 Orange Pi USB 口，重跑
  `/api/camera/devices`、OpenCV/ffmpeg 单帧和 PC WebRTC smoke。
