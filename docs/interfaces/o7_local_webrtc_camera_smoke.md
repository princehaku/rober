# O7 LAN-only Local WebRTC Camera Smoke

## 定位

`onboard/scripts/local_webrtc_camera_smoke.py` 是 Orange Pi 上位机本地摄像头 WebRTC smoke。它只用于同 LAN / 同 WiFi 浏览器验证“真实摄像头能出帧，并且 WebRTC receive-only 视频能播放”。

它不是云 relay、不是公网 RTC、不是 TURN 方案，也不发送机器人控制命令。服务固定暴露：

- `GET /`：本地调试页面，浏览器只创建 recvonly video transceiver。
- `GET /health`：Python 版本、依赖状态、端口、安全边界。
- `GET /devices`：`/dev/video*` 和可选 `v4l2-ctl --list-devices` 摘要。
- `POST /offer`：浏览器 SDP offer -> aiortc answer。缺 `aiohttp/aiortc/cv2/av` 或摄像头打不开时返回清晰 JSON 错误。
- `POST /peers/{peer_id}/close`：只释放 `/offer` answer 返回的指定 peer，用于机器自检后主动清理服务端连接，避免下一轮自检被单连接保护误判为 `camera_in_use`。
- `--self-test-url http://host:port`：机器可读 recvonly offer-level 客户端。它会读取 `/health`、`/devices`，依赖齐全时向 `/offer` 发 SDP offer，验证 answer，并等待至少一帧视频；依赖或摄像头失败时输出结构化 `degraded/failed` 原因。

## Vendor 来源边界

已按项目纪律读取：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/interfaces/o7_realtime_hardware_sources.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/app.py`

Waveshare vendor Raspberry Pi app 只能证明 vendor 参考实现里存在 `aiortc`、`/offer`、`/video_feed` 和摄像头来源示例；它不证明 rober 的 Orange Pi Zero 3、当前摄像头、当前网络和当前 Python 依赖已经验证。本 smoke 的验收必须以 Orange Pi 远端实测为准。

## 安全边界

- `safe_to_control=false`
- `sends_commands=false`
- `robot_control_executed=false`
- 不启动底盘、UART、WAVE ROVER、Nav2、ROS2 launch 或任何运动控制。
- 默认不使用公网 STUN/TURN；`RTCPeerConnection` 页面侧设置 `iceServers: []`。
- 第一版限制单个 peer，降低摄像头独占和 CPU 压力。

## 启动

```bash
PORT=8088 ROBER_CAMERA_SOURCE=0 bash onboard/scripts/local_webrtc_camera_smoke.sh
```

同网段浏览器访问：

```text
http://<orange-pi-lan-ip>:8088/
```

若依赖缺失但 `python3` 可用，脚本仍会启动诊断服务；此时 `/health` 和 `/devices` 可访问，`/offer` 会返回 `webrtc_dependency_missing`，不能把它当作 WebRTC 播放成功。

## 机器可读 offer-level 自检

服务已启动后，可以在本机、同 LAN PC 或远端 SSH 中运行：

```bash
python3 onboard/scripts/local_webrtc_camera_smoke.py --self-test-url http://127.0.0.1:8088 --self-test-timeout 8
```

也可以通过 shell 封装运行：

```bash
ROBER_WEBRTC_SELF_TEST_URL=http://127.0.0.1:8088 ROBER_WEBRTC_SELF_TEST_TIMEOUT=8 bash onboard/scripts/local_webrtc_camera_smoke.sh
```

自检输出单行 JSON，schema 为 `trashbot.local_webrtc_camera_offer_self_test.v1`。关键字段：

- `status=ok`：`/health` 可达、`/offer` 返回 answer，且 `first_frame_received=true`。
- `peer_id` + `server_peer_close.closed=true`：自检已经释放本次服务端 peer，后续自检可立刻重复运行。
- `status=degraded` + `reason=webrtc_client_dependency_missing`：客户端缺 `aiohttp` 或 `aiortc`，只能确认 HTTP 诊断，不能确认 offer/answer。
- `status=failed` + `reason=health_unreachable`：目标 HTTP 服务不可达。
- `status=failed` + `reason=offer_rejected`：服务端拒绝 `/offer`，`offer_response` 会带服务端 JSON 错误，例如 `camera_in_use`、`offer_failed`。
- `status=failed` + `reason=first_frame_not_received`：answer 已处理但超时未收到首帧，通常指向摄像头读取、编码、ICE 或浏览器/网络链路问题。

默认自检在 degraded/failed 时仍返回 0，方便无依赖现场留下结构化诊断；如果 CI 或上车验收需要强制首帧，可加 `--require-frame` 或设置：

```bash
ROBER_WEBRTC_REQUIRE_FRAME=1 ROBER_WEBRTC_SELF_TEST_URL=http://127.0.0.1:8088 bash onboard/scripts/local_webrtc_camera_smoke.sh
```

## 常见失败定位

- `/devices` 为空：摄像头未枚举、驱动未加载、USB/CSI 连接或权限问题。
- `/offer` 返回 `webrtc_dependency_missing`：缺 `aiohttp`、`aiortc`、`opencv-python` 或 `av`。
- `/offer` 返回 `camera_open_failed`：设备路径错误、摄像头被其他进程占用、权限不足或 OpenCV backend 不支持。
- 自检返回 `offer_rejected` 且服务端 detail 为 `camera_open_failed:<source>`：同上，优先确认 `ROBER_CAMERA_SOURCE` 和摄像头占用。
- 自检返回 `first_frame_not_received`：answer/ICE 和首帧之间失败，需要结合 `/tmp/rober-local-webrtc-camera.log`、CPU/温度、摄像头帧率和同 LAN 网络继续定位。
- 浏览器页面有 answer 但无画面：需要查看 `/tmp/rober-local-webrtc-camera.log`，并补真实浏览器控制台、ICE 状态、CPU/温度和摄像头帧率证据。
