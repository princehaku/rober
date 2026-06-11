# Camera First-frame Probe Tool

## sprint_type

micro

## 背景

用户要求去掉 subagent 调用，本轮直接在主会话推进。当前真实上车 goal 的 PC 实时图传仍卡在
`/dev/video1` 首帧 timeout：camera service 能正确选择 DV20 UVC capture，但 `/offer`
返回 `first_frame_unreadable/first_frame_timeout`。为了避免继续用临时 SSH 命令反复排查，
本轮把“打开设备、短超时读首帧、计算亮度指标、可选保存样张”的探针入仓。

本轮采用的硬件资料入口：

- `docs/vendor/VENDOR_INDEX.md`

本轮不调用 `/api/base/manual`，不发布 `/cmd_vel`，不执行 Nav2 goal，不打开
WAVE ROVER UART，不触碰 `/dev/ttyS5`。

## 设计

- 新脚本只做 camera first-frame probe：
  - 默认设备 `/dev/video1`；
  - 可指定 `--fourcc MJPG|YUYV`、宽高、FPS、短超时和 sample 输出路径；
  - 额外提供 `--read-call-timeout-s`，降低 UVC 故障时单次 `cap.read()` 长阻塞风险；
  - 所有结果输出结构化 JSON；
  - 失败时 fail closed，不伪造黑帧或 placeholder；
  - 成功读帧时只输出 `visible_content_candidate`，不把它升级成运动 gate 的
    `visible_content_proven=true`。
- 安全边界：
  - 不导入 ROS2；
  - 不打开串口；
  - 不发送底盘控制；
  - 固定 `safe_to_control=false`、`robot_control_executed=false`、
    `delivery_success=false`、`primary_actions_enabled=false`。

## 实际改动

- 新增 `onboard/scripts/camera_first_frame_probe.py`
  - 输出 schema `trashbot.camera_first_frame_probe.v1`；
  - 支持 OpenCV 缺失、设备打不开、首帧 timeout、探针异常、读帧成功五类结果；
  - 首帧失败时记录 `failure_reason`，区分整体 deadline 与单次 read 调用 timeout；
  - 读帧成功时输出 shape、pixel_count、mean/min/max luma、dynamic range、
    non_black ratio 和 `visible_content_candidate`；
  - 可选 `--sample-path` 保存真实首帧。
- 新增 `onboard/tests/test_camera_first_frame_probe.py`
  - 使用 fake cv2/fake capture，不打开真实摄像头；
  - 覆盖缺依赖 fail-closed、open_failed release、first_frame_timeout、安全字段、
    metrics 和 CLI JSON 输出。
- 更新 `docs/vision/board_camera_publisher.md`
  - 记录该探针作为 DV20/known-good UVC 的可复现实板验证入口。
- 新增实板 artifacts：
  - `artifacts/01_remote_probe_compile_sha.txt`
  - `artifacts/02_remote_pre_probe_health.txt`
  - `artifacts/03a_pre_sequential_fuser.txt`
  - `artifacts/03_probe_default.json`
  - `artifacts/04_probe_mjpg.json`
  - `artifacts/05_probe_yuyv.json`
  - `artifacts/06_remote_post_probe_cleanup.txt`

## 验证结果

本地验证：

```bash
python3 -m unittest discover onboard/tests -p '*camera*'
python3 -m unittest discover onboard/tests
python3 -m py_compile onboard/scripts/camera_first_frame_probe.py onboard/scripts/local_webrtc_camera_smoke.py
git diff --check
```

结果：

- `Ran 15 tests ... OK`
- `Ran 103 tests ... OK`
- `py_compile` 通过
- `git diff --check` 通过

上板验证：

```bash
scp -P 37878 onboard/scripts/camera_first_frame_probe.py \
  root@192.168.1.11:/root/rober/onboard/scripts/camera_first_frame_probe.py
ssh -p 37878 root@192.168.1.11 \
  'python3 -m py_compile /root/rober/onboard/scripts/camera_first_frame_probe.py'
ssh -p 37878 root@192.168.1.11 \
  'timeout 18s python3 /root/rober/onboard/scripts/camera_first_frame_probe.py --device /dev/video1 --width 640 --height 480 --fps 15 --timeout-s 3 --read-call-timeout-s 4'
ssh -p 37878 root@192.168.1.11 \
  'timeout 18s python3 /root/rober/onboard/scripts/camera_first_frame_probe.py --device /dev/video1 --width 640 --height 480 --fps 15 --fourcc MJPG --timeout-s 3 --read-call-timeout-s 4'
ssh -p 37878 root@192.168.1.11 \
  'timeout 18s python3 /root/rober/onboard/scripts/camera_first_frame_probe.py --device /dev/video1 --width 640 --height 480 --fps 15 --fourcc YUYV --timeout-s 3 --read-call-timeout-s 4'
```

远端脚本 hash：

- `f9fd64e4c6571f0b5f2ed68f64ce3fbe3dc41d20a77b4dcd77d7528a5bc2f1b7`

串行 probe 结果：

| 模式 | open_ok | read_ok | status | failure_reason | elapsed_ms | visible_content_proven |
| --- | --- | --- | --- | --- | ---: | --- |
| default | true | false | `first_frame_timeout` | `capture_read_call_timeout` | 4633 | false |
| MJPG 640x480 | true | false | `first_frame_timeout` | `capture_read_call_timeout` | 4654 | false |
| YUYV 640x480 | true | false | `first_frame_timeout` | `capture_read_call_timeout` | 4635 | false |

说明：曾经误把 default/MJPG/YUYV 三档并行启动，default 得到过一次
`open_failed`，该结果可能来自同一 `/dev/video1` 并发抢占，已废弃不用；
本轮结论以 `03a_pre_sequential_fuser.txt` 之后的串行 artifacts 为准。

收尾状态：

- `trashbot-local-webrtc-camera.service=active`
- `trashbot-upper-robot-api.service=active`
- `/api/camera/health status=ready`
- `/api/camera/health video_source=/dev/video1`
- `/api/camera/health active_peer_count=0`
- `fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5` 无残留 holder 输出

## 剩余风险

- 真实 `/dev/video1` 仍是 `open_ok=true/read_ok=false`，首帧不可读没有恢复。
- 新探针证明了问题可以在不经过 PC/WebRTC 的底层 camera first-frame 层稳定复现。
- 下一步仍需要现场动作：确认 DV20 输入源、线缆、供电、采集卡状态，或插入 known-good UVC
  后用同一脚本复测。
- 运动 HIL gate 仍缺 `visible_content_proven=true`、外部视频、轮速反馈非零和 LiDAR
  motion delta，不能放行非 stop 运动。
