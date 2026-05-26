# O7 实时音视频硬件来源边界

更新时间：2026-05-27

本文回答 CEO 追问：“视频 RTC 不需要机器上协议打通吗？板子上的代码够了？”结论是：不够。Waveshare 本地 vendor 资料证明 Raspberry Pi 上位机参考 app 包含 WebRTC/视频/音频能力，但它不能直接证明 rober 项目在 Orange Pi Zero 3、ROS2、云中转、公网网络和真实摄像头/音频设备上已经打通。

## 已读本地来源

- `docs/vendor/VENDOR_INDEX.md`
  - 项目硬件栈指定主 SBC 是 Orange Pi Zero 3，H618。
  - WAVE ROVER 的 `ugv_rpi/` 是 Raspberry Pi 上位机参考。
  - vendor Raspberry Pi UART 默认是 `/dev/ttyAMA0` 或 `/dev/serial0`，Orange Pi 真实串口设备必须上车确认。
  - 明确要求不要把 Raspberry Pi 引脚、设备路径或资料当作 Orange Pi 结论。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/README.md`
  - vendor app 是 Waveshare UGV robots 的 Raspberry Pi example。
  - README 声称功能包含 real-time video based on WebRTC、audio interactive、photo taking、video recording、OpenCV/MediaPipe 视觉功能。
  - README 的安装和运行说明面向 Raspberry Pi / Raspberry Pi OS / 热点 Web UI。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/app.py`
  - 引入 `aiortc.RTCPeerConnection` 和 `RTCSessionDescription`。
  - 提供 `/offer`、`/video_feed`、`/playAudio`、`/stop_audio` 等 Flask 路由。
  - `socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)` 证明它是本机 Web app 暴露 5000 端口的实现。
  - 启动时根据 Raspberry Pi 5 判断使用 `/dev/ttyAMA0` 或 `/dev/serial0`，这不能迁移为 Orange Pi 默认路径。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/cv_ctrl.py`
  - 视频帧来源按 USB camera、CSI Picamera2、OAK depthai 三级尝试。
  - USB 分支使用 `cv2.VideoCapture(0)`。
  - CSI 分支使用 `Picamera2` 和 Raspberry Pi libcamera 生态。
  - 输出帧通过 `cv2.imencode('.jpg', ...)` 编码给 `/video_feed`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/audio_ctrl.py`
  - 音频播放使用 `pygame.mixer`，TTS 使用 `pyttsx3`。
  - 如果 `pygame.mixer.init()` 失败，代码只标记 `audio usb not connected` 并返回，不证明 Orange Pi 音频设备可用。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - 记录 `audio_config`、默认分辨率 `640x480`、JPEG quality、`video_fps` 反馈 key 等 vendor app 配置。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/setup.sh`
  - 安装脚本修改 Raspberry Pi `/boot/firmware/config.txt`、启用 `dtparam=uart0`、追加 `dtoverlay=disable-bt`、禁用蓝牙服务，并复制 `asound.conf`。
  - 这些步骤是 Raspberry Pi OS 口径，不是 Orange Pi Zero 3 可直接执行的硬件配置。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/requirements.txt`
  - 固定 `aiortc==1.8.0`、`opencv-python==4.9.0.80`、`picamera2==0.3.17` 等依赖。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/asound.conf`
  - 默认 ALSA `card 3`，这只是 vendor 示例声卡编号，不是 rober Orange Pi 实测编号。

## 已证实边界

| 事项 | 本地 vendor 能证明什么 | rober 当前不能据此宣称什么 |
| --- | --- | --- |
| WebRTC | vendor Raspberry Pi app 有 `aiortc` 依赖和 `/offer` 路由 | 不能证明 rober Orange Pi 已接入云端 RTC、STUN/TURN、鉴权或公网连通 |
| 视频流 | vendor app 有 `/video_feed` MJPEG 路由，帧来自 `cvf.frame_process()` | 不能证明 Orange Pi 摄像头已被 ROS2/RTC 同时安全占用，也不能证明编码延迟和 CPU 负载合格 |
| 摄像头 | vendor app 支持 USB `cv2.VideoCapture(0)`、Raspberry Pi CSI `Picamera2`、OAK depthai | 不能证明 Orange Pi Zero 3 的 CSI、USB 摄像头路径、权限、驱动和帧率已验证 |
| 音频/TTS | vendor app 使用 `pygame.mixer` 播放音频、`pyttsx3` 做 TTS | 不能证明 Orange Pi 上的 USB 声卡、喇叭、ALSA card 编号、TTS 语音包和音量链路可用 |
| 板端协议 | vendor app 通过 Raspberry Pi GPIO UART 控 ESP32，并使用 `/dev/ttyAMA0` 或 `/dev/serial0` | 不能证明 Orange Pi 串口路径、权限、波特率、占用冲突和 ROS2 串口桥已与 RTC 同机共存 |
| 本机 Web UI | vendor app 监听 `0.0.0.0:5000`，手机/PC 可访问同网段 Web UI | 不能证明云中转、4G、公网 HTTPS、浏览器跨 NAT RTC、远程运维链路已完成 |
| 反馈指标 | vendor app 上报 `video_fps`、CPU、RAM、WiFi RSSI、base voltage | 不能证明 rober 的云端 O7 PC 平台已经消费这些指标或形成稳定数据契约 |

## 对 CEO 问题的硬件回答

“板子上的代码够了”只能在一个很窄的范围内成立：如果使用 vendor 推荐的 Raspberry Pi 上位机、vendor app、同网段浏览器、已支持的摄像头和音频设备，vendor 资料提供了可参考实现。

对 rober 当前方案不成立，原因如下：

1. rober 的主 SBC 是 Orange Pi Zero 3，不是 Raspberry Pi。vendor app 的串口路径、boot 配置、Picamera2/libcamera、ALSA card 和安装脚本都带 Raspberry Pi 假设。
2. rober 的 O7 目标是 PC 端运营调试与数据训练平台，链路包含 Orange Pi、ROS2、云中转、实时地图/状态/ASR/TTS/手控，不是 vendor 本机 Web UI。
3. RTC 是否可用不仅取决于板端 app，还取决于摄像头设备占用、编码方式、CPU 负载、网络 NAT、STUN/TURN、HTTPS、安全鉴权和云端信令。
4. vendor app 的 WebRTC 代码只提供了 `/offer` 形态的本机参考，未在本地资料中看到 STUN/TURN 配置、云端信令、ROS2 bridge 或 rober PC 平台数据契约。

因此，vendor app 可以作为“板端参考代码”和“功能存在性线索”，不能作为“rober Orange Pi/ROS2/O7 RTC 已打通”的验收证据。

## Orange Pi / ROS2 仍需证明

后续上车或软件 sprint 必须补齐以下证据，才能把“参考可行”升级为“项目已打通”：

1. 摄像头枚举与采集
   - 在 Orange Pi Zero 3 上确认实际摄像头类型、设备路径、权限和帧率。
   - 如果用 USB 摄像头，需要证明 `cv2.VideoCapture` 或 ROS2 camera driver 可持续读取。
   - 如果用 CSI 摄像头，不能默认沿用 Raspberry Pi `Picamera2`，必须以 Orange Pi 本机驱动和实测为准。
2. 摄像头占用策略
   - 明确 ROS2 感知、RTC 预览、录像/截图是否共享同一采集进程。
   - 避免多个进程同时打开 `/dev/video*` 导致帧流失败。
3. 编码和 CPU 预算
   - 证明 Orange Pi H618 在目标分辨率、帧率、ROS2 负载、云同步负载下仍可运行。
   - 明确使用 MJPEG、软件 H.264、硬件编码或其他方案，并记录实际延迟。
4. 音频和 TTS
   - 在 Orange Pi 上确认 ALSA/PulseAudio/PipeWire 设备、card 编号、喇叭音量和 TTS 依赖。
   - vendor `asound.conf` 的 `card 3` 不能作为项目默认值。
5. 网络和 RTC
   - 明确是否使用 WebRTC、MJPEG over HTTPS、WebSocket 帧流或云端转推。
   - 如果使用 WebRTC，必须补 STUN/TURN、信令、HTTPS、鉴权、断线恢复和弱网策略。
6. ROS2 集成
   - 明确视频/音频节点与现有硬件串口桥、Nav2、任务状态机之间的接口边界。
   - 不能让实时视频链路阻塞底盘 UART 或任务控制。
7. 真实上车证据
   - 需要在真实 Orange Pi + WAVE ROVER + 摄像头 + 音频设备 + 目标网络环境中运行 smoke。
   - 证据至少包含设备枚举、启动日志、浏览器/PC 端画面、音频播放/TTS、CPU/内存/温度、网络状态和失败恢复记录。

## 本 sprint 可采纳的设计边界

- 可以采纳 vendor `ugv_rpi` 作为 Raspberry Pi 上位机参考来源。
- 可以借鉴 `app.py` 的 Flask 路由、`cv_ctrl.py` 的摄像头优先级、`audio_ctrl.py` 的播放/TTS 控制思想。
- 不应直接采纳 Raspberry Pi 串口路径、boot overlay、ALSA `card 3`、Picamera2 假设或同网段 Web UI 作为 rober 默认实现。
- O7 文档和后续实现必须把“vendor 参考能力”和“rober Orange Pi/ROS2/云端已验证能力”分开标注。

## 当前结论

CEO 问题的硬件来源边界是：视频 RTC 需要机器上协议和设备链路打通；板子上的 vendor 代码只证明 Raspberry Pi 参考 app 有相关功能，不证明 rober 当前 Orange Pi 板端、ROS2、云中转和 PC 端已经完成。下一步应由软件/全栈与硬件按上面的证据清单补最小上车 smoke 或可替代的软件 proof，不能用 vendor app 直接替代项目验收。
