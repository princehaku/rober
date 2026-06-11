# Local WebRTC Camera Service 可复现化设计记录

## sprint_type

micro

## owner

`robot-software-engineer`

## 本轮目标

继续推进真实上车 evidence capture 的实时图传缺口。当前真实上位机
`trashbot-local-webrtc-camera.service` 正在运行：

```text
python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 15
```

但本地仓库 `onboard/scripts/` 没有 `local_webrtc_camera_smoke.py`，只有历史
sprint artifact 中保存的远端脚本头部。这会导致 camera WebRTC 服务不可复现、
不可测试、不可安全演进，也会让 PC 图传问题继续依赖现场运行态文件。

## 已读资料和事实来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/12/flask_camera.py`
- `docs/vision/board_camera_publisher.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.06.11_10-15_camera_visible_content_recovery/artifacts/remote_capture/03_remote_local_webrtc_camera_smoke_head.py`
- `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/tech-done.md`
- `sprints/2026.06.11_20-05_camera_visible_content_gate_refresh/tech-done.md`

Vendor 边界：

- Waveshare `config.yaml` 的视频默认分辨率为 `640x480`。
- Waveshare Flask demo 使用真实 camera frame 生成 MJPEG，但它是 Raspberry Pi/Picamera2
  示例，不能外推 Orange Pi 当前 `/dev/video*` 路径。
- 当前实板事实仍以本项目历史证据为准：`/dev/video0` 是 Cedrus decoder，
  `/dev/video1` 是 DV20 USB UVC capture，`/dev/video2` 是 metadata 节点。

## 当前缺口

- `upper_robot_api.py` 已代理 `/api/camera/health`、`/api/camera/devices`、
  `/api/camera/offer`、`/api/camera/peers/{peer_id}/close`。
- `pc-tools/workstation` 已通过 Node proxy 和普通首屏 `打开画面/关闭画面`
  使用这些接口。
- 但真正提供 8088 camera service 的脚本没有进入仓库，当前只能从远端运行态和
  sprint artifact 推断行为。
- 2026-06-11 20:05 的真实板端复测显示 `/dev/video1` `open_ok=true` 但
  `read_ok=false` / `first_frame_timeout=true`，这不是 PC proxy 或普通首屏问题。

## 功能设计

下一轮实现必须先补齐仓库内 `onboard/scripts/local_webrtc_camera_smoke.py`，保持
LAN-only、read-only、fail-closed：

1. HTTP endpoint 兼容现有上位机合同：
   - `GET /health`
   - `GET /devices`
   - `POST /offer`
   - `POST /peers/{peer_id}/close`
2. `/health` 返回：
   - `schema=trashbot.local_webrtc_camera_smoke.v1`
   - `app=rober-local-webrtc-camera-smoke`
   - `status`
   - `video_source`
   - `video_source_mode`
   - `active_peer_count`
   - `active_frames_read`
   - `active_camera_read_failures`
   - `safe_to_control=false`
   - `robot_control_executed=false`
   - system/media diagnostics
   - source candidates/current selection 摘要，用于现场判断 auto 到底选中了哪个节点。
3. `/devices` 只做只读设备枚举：
   - `glob /dev/video*`
   - `v4l2-ctl --list-devices`、可选 `--list-formats-ext`
   - 不写 V4L2 controls，不打开底盘、不触碰 `/dev/ttyS5`。
4. `--video-source auto` 规则：
   - 跳过明显的 decoder/metadata 节点，例如当前 `/dev/video0` Cedrus decoder。
   - 优先选择具备 `Video Capture` 能力的 UVC 候选，当前实板应落到 `/dev/video1`。
   - 若用户显式传 `--video-source /dev/video1`，必须按指定源使用，不再自作主张切换。
5. `POST /offer`：
   - 只接受 JSON object，`type=offer` 且 `sdp` 非空。
   - 使用 `aiortc` 创建 sendonly video answer。
   - 使用 `cv2.VideoCapture` 读取真实 frame，并用 `av.VideoFrame` 送出。
   - 缺 `aiortc/cv2/av` 或首帧不可读时返回结构化错误，不伪造黑帧或 placeholder。
6. peer cleanup：
   - `peer_id` 只允许短字母数字。
   - close 后释放 `RTCPeerConnection`、camera capture、track，并在 `/health` 暴露
     `last_closed_*` 摘要，方便 PC stop 后确认 active peers 回到 0。
7. 安全边界：
   - 所有响应固定 `safe_to_control=false`、`robot_control_executed=false`、
     `delivery_success=false`、`primary_actions_enabled=false`。
   - 不发送 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。
   - 技术注释必须使用中文，并说明 fail-closed 和 auto source 选择原因。

## 计划文件范围

下一轮 robot-software 子 agent 可改：

- `onboard/scripts/local_webrtc_camera_smoke.py`
- `onboard/tests/test_local_webrtc_camera_smoke.py` 或同类 camera 单测
- `docs/vision/board_camera_publisher.md`
- `docs/product/pc_tools_workstation.md`（仅同步入口和风险）
- 本 sprint `tech-done.md`

除非为兼容字段必须小改代理，否则不改 `upper_robot_api.py`、底盘、雷达、Nav2、
launch 运动参数或 PC 普通首屏。

## 计划验收命令

下一轮实现必须运行：

```bash
python3 -m unittest discover onboard/tests -p '*camera*'
python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py
git diff --check
```

若本地依赖允许，补一个 no-hardware smoke：

```bash
python3 onboard/scripts/local_webrtc_camera_smoke.py --host 127.0.0.1 --port <temp> --video-source auto
curl http://127.0.0.1:<temp>/health
curl http://127.0.0.1:<temp>/devices
```

该 smoke 不得 SSH 上车、不得打开 `/dev/ttyS5`、不得发送运动。

## 本轮实际结果

- 新增 `onboard/scripts/local_webrtc_camera_smoke.py`，把 8088 LAN-only camera
  WebRTC 服务正规化进仓库。服务兼容：
  - `GET /health`
  - `GET /devices`
  - `POST /offer`
  - `POST /peers/{peer_id}/close`
- `/health` 现在输出 `schema`、`app`、`status`、`video_source`、
  `video_source_mode`、`active_peer_count`、`active_frames_read`、
  `active_camera_read_failures`、`system_diagnostics`、`media_diagnostics`、
  `source_candidates_summary`、`current_selection` 和 last offer/last closed peer
  摘要；安全字段固定 `safe_to_control=false`、`robot_control_executed=false`、
  `delivery_success=false`、`primary_actions_enabled=false`。
- `/devices` 只读枚举 `/dev/video*`、`v4l2-ctl --list-devices`、`--all` 和
  `--list-formats-ext`，成功 schema 对齐历史
  `trashbot.local_webrtc_camera_devices.v1`，并显式返回 `writes_controls=false`、
  `opens_serial=false`、`sends_motion_commands=false`。
- `--video-source auto` 用只读能力摘要跳过 Cedrus decoder、metadata 和非
  `Video Capture` 节点，优先 UVC/USB capture；按当前实板事实应选择
  `/dev/video1`。显式指定源时保持 `mode=explicit` 并尊重传入路径。
- `POST /offer` 成功 schema 对齐历史 `trashbot.local_webrtc_camera_offer.v1`。
  在 invalid offer、缺 `aiortc/cv2/av`、auto 无采集源、OpenCV 打不开设备或
  首帧不可读时结构化 fail-closed，不生成黑帧或 placeholder。读到真实首帧后
  才创建 `RTCPeerConnection` 和 video answer。
- `POST /peers/{peer_id}/close` 关闭 peer connection、停止 track、释放
  `VideoCapture`，成功 schema 对齐历史 `trashbot.local_webrtc_camera_close.v1`，
  并在 health 的 `media_diagnostics.last_closed_peer` 中回读。
- 新增 `onboard/tests/test_local_webrtc_camera_smoke.py`，覆盖 auto 选源、
  显式源、invalid offer、缺依赖 fail-closed、只读 devices 命令、health 字段，
  以及 DV20 这类 UVC 复合设备同时暴露 `Video Capture`/`Metadata Capture`
  capability 时仍应把 `/dev/video1` 识别为图像采集节点。
- 同步更新：
  - `docs/vision/board_camera_publisher.md`
  - `docs/product/pc_tools_workstation.md`

## 验证结果

```text
$ python3 -m unittest discover onboard/tests -p '*camera*'
..........
----------------------------------------------------------------------
Ran 10 tests in 0.031s

OK
```

```text
$ python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py
# pass
```

```text
$ git diff --check
# pass
```

no-hardware local smoke：

```text
GET /health  -> HTTP 200, schema=trashbot.local_webrtc_camera_smoke.v1,
                status=no_video_source, video_source=auto,
                video_source_mode=auto, safe_to_control=false
GET /devices -> HTTP 200, schema=trashbot.local_webrtc_camera_devices.v1,
                status=loaded, candidate_count=0, safe_to_control=false
```

本机没有 `/dev/video*` 和 WebRTC 依赖，因此 no-hardware smoke 只证明
health/devices 可复现、只读和安全字段关闭；没有尝试 `/offer` 真实媒体建链。

## 剩余风险

- 当前真实相机 `/dev/video1` `first-frame timeout` 未解决；本轮只让 camera
  service 从运行态文件收敛为仓库内可复现、可测试、可诊断的服务。
- 未恢复 direct frame 前，PC 页面不能证明实时图传可见内容；运动 HIL gate 仍缺
  `visible_content_proven=true`、外部视频、轮速非零和 LiDAR motion delta。
- 本机缺少真实 `/dev/video1`、`aiortc`、`cv2` 和 `av`，未执行真实 `/offer`
  媒体 answer smoke；真实板端仍需部署后用 `/dev/video1` 重跑 offer/close 和
  first-frame 诊断。
