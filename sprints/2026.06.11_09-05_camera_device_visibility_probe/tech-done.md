# Camera Device Visibility Probe

## sprint_type

micro

## 本轮目标

定位 PC WebRTC 真实帧近黑根因。上一轮浏览器像素证明已有真实帧进入页面，
但 `nonTransparentPixels=6912`、`nonBlackPixels=0`、`averageRgbSum=4`。
本轮只做 camera/API/v4l2/单帧可见性 probe，不触碰运动、Nav2、串口、雷达或 PC 首屏样式。

## 已读来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/app.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
- `docs/hardware/board_sensor_stack_smoke.md`
- `onboard/scripts/upper_robot_api.py`

vendor 结论边界：vendor 上位机视频默认是 `640x480`，并使用 OpenCV 读取 USB camera；
但 Orange Pi 当前 `/dev/video*` 设备选择和可见内容必须以真实上位机 probe 为准。

## 实际改动

- 新增本轮 artifacts：`sprints/2026.06.11_09-05_camera_device_visibility_probe/artifacts/**`
- 新增本轮留档：`sprints/2026.06.11_09-05_camera_device_visibility_probe/tech-done.md`
- 更新硬件 smoke 文档：`docs/hardware/board_sensor_stack_smoke.md`

未修改产品代码、PC 首屏、launch 默认、运动/Nav2/底盘串口相关代码或配置。

## API readback

真实上位机：`root@192.168.1.11:37878`；Robot API：`http://192.168.1.11:8787`。

- `/api/camera/health`：`status=ready`、`video_source=auto`、`video_source_mode=auto`、
  `port=8088`，`active_peer_count=0`。
- `/api/camera/devices`：存在 `/dev/video0`、`/dev/video1`、`/dev/video2`；
  `v4l2-ctl --list-devices` 显示 `/dev/video0` 是 `cedrus`，
  `/dev/video1` 和 `/dev/video2` 属于 `USB Composite Device: DV20 USB`。
- `/api/status`：camera 聚合状态为 `http_status=200`、`status=ready`、
  `video_source=auto`、`base_url=http://127.0.0.1:8088`。

关键 artifact：

- `artifacts/api/camera_health.json`
- `artifacts/api/camera_devices.json`
- `artifacts/api/status.json`
- `artifacts/api/after_camera_health.json`
- `artifacts/api/after_camera_devices.json`
- `artifacts/api/after_status.json`

## `/dev/video*` 结论

| device | 设备身份 | 抓帧 | 统计 | 是否适合作 PC 图传源 |
| --- | --- | --- | --- | --- |
| `/dev/video0` | `cedrus` platform video decoder，非真实摄像头 | OpenCV `opened=false` | 无有效帧 | 否 |
| `/dev/video1` | DV20 USB `uvcvideo` Video Capture | OpenCV/ffmpeg 均可抓 640x480 帧 | OpenCV：`mean_gray=1.0`、`nonblack_pixels_gt10=0`、`edge_pixels_canny=0`；ffmpeg：同为 `mean_gray=1.0`、`nonblack_pixels_gt10=0` | 当前不适合；它是正确 capture 节点，但画面本身近黑 |
| `/dev/video2` | DV20 USB UVC metadata capture | OpenCV `opened=false` | 只有 metadata format | 否 |

frame artifacts：

- `artifacts/frames/dev_video1.jpg`
- `artifacts/frames/dev_video1_ffmpeg.jpg`

## WebRTC service source

当前 camera service：

- `trashbot-local-webrtc-camera.service` active，监听 `0.0.0.0:8088`。
- 进程参数：`python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 15`。
- systemd 环境：`ROBER_CAMERA_SOURCE=auto`。
- auto selection 日志：候选 `/dev/video0` 打不开，随后 `/dev/video1` 打开并读到 `[480, 640, 3]`，`selected_source=/dev/video1`。

判断：当前近黑不是 auto 误选到 `/dev/video0` 或 `/dev/video2`。auto 已选中唯一真实 capture 节点 `/dev/video1`，
但该节点输出近黑帧。

## 曝光/控制项验证

`/dev/video1 --all` 显示：

- `brightness=0`
- `contrast=256`
- `saturation=250`
- `gain=4`
- `auto_exposure=3`
- `exposure_time_absolute=80` 且 inactive

临时 boost：

- 设置 `brightness=127`、`gain=7`、`gamma=30`、`backlight_compensation=255`
- 抓帧结果仍为 `mean_gray≈0.0012`、`nonblack_pixels_gt10=0`、`edge_pixels_canny=0`
- 恢复：`brightness=0`、`gain=4`、`backlight_compensation=0`；`gamma=17` 被驱动 step 量化为 `20`

结论：软件侧拉高 UVC 亮度/增益不能改善画面，优先怀疑现场镜头遮挡、保护膜、朝向、无光或摄像头本体输出异常。

## 验证结果

- `git diff --check`：通过，输出为空。记录在 `artifacts/git_diff_check.log`。
- 未改 Python API，因此未运行 `python3 -m unittest onboard.tests.test_upper_robot_api` 和
  `python3 -m py_compile onboard/scripts/upper_robot_api.py`。
- `v4l2-ctl --list-devices`：通过，记录在 `artifacts/remote_capture/v4l2_list_devices.log`。
- `v4l2-ctl -d /dev/videoN --all` 与 `--list-formats-ext`：已对 `/dev/video0..2` 保存。
- OpenCV 单帧抓取与亮度统计：记录在 `artifacts/remote_capture/frame_stats.json`。
- ffmpeg `/dev/video1` 单帧交叉验证：记录在 `artifacts/remote_capture/video1_ffmpeg_capture.log`。
- service readback：`trashbot-local-webrtc-camera.service` 与 `trashbot-upper-robot-api.service` 均为 `active`，
  监听 `8088/8787`，记录在 `artifacts/remote_capture/post_probe_service_active.log`。
- 远端临时文件已清理，记录在 `artifacts/remote_capture/remote_temp_cleanup.log`。

## 是否改善到可见场景

No。

没有可切换的更亮 source：`/dev/video0` 不是摄像头，`/dev/video2` 是 metadata，
`/dev/video1` 是唯一 capture 节点但 OpenCV/ffmpeg 都输出近黑帧。未做服务重启或持久配置改动。

## root cause 判断

PC WebRTC 链路和 camera service 能产生真实帧，且服务实际选择 `/dev/video1`；
近黑 root cause 在真实摄像头输入侧，而不是 PC 首屏、WebRTC SDP/ICE、Robot API proxy 或 auto source 误选。

当前最可信 root cause：DV20 USB 摄像头物理光路/环境问题，包含镜头遮挡、保护膜未撕、镜头朝向黑暗区域、现场无光，
或摄像头本体/模组输出异常。仅凭远程 SSH 无法区分上述现场原因。

## 剩余风险和下一步

- 现场需要人工检查 DV20 摄像头镜头、保护膜、朝向、环境光和 USB 接触。
- 建议把摄像头对准明亮场景或手机屏幕，再重跑本 sprint 的 OpenCV/ffmpeg 单帧统计。
- 若仍为 `mean_gray≈1`、`nonblack_pixels_gt10=0`，更换一个已知可见画面的 USB UVC 摄像头后复测。
- 当前 `visible_content_proven=false`，不能把 PC 实时图传用于路线关键帧、远程可视、视觉定位、障碍识别或 O7 可见画面验收。
- 本轮没有运动、Nav2、底盘串口、雷达、送达闭环或 HIL movement 证据。
