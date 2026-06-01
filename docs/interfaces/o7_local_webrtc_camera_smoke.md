# O7 LAN-only Local WebRTC Camera Smoke

## 定位

`onboard/scripts/local_webrtc_camera_smoke.py` 是 Orange Pi 上位机本地摄像头 WebRTC smoke。它只用于同 LAN / 同 WiFi 浏览器验证“真实摄像头能出帧，并且 WebRTC receive-only 视频能播放”。

它不是云 relay、不是公网 RTC、不是 TURN 方案，也不发送机器人控制命令。服务固定暴露：

- `GET /`：本地调试页面，浏览器只创建 recvonly video transceiver。
- `GET /health`：Python 版本、依赖状态、端口、安全边界；同时输出 PC 摘要层可直接消费的扁平 `system_metrics` / `stability_metrics`，以及只读详细 `system_diagnostics`（采样时间、进程 uptime、CPU/load、内存、温度）和 aiortc 服务模式下的 `active_peer_connections`、`active_peer_ids`、`media_stability_summary`、`media_diagnostics`、`peer_cleanup`，用于定位 409 残留 peer、短时稳定性和媒体首帧缺失。
- `GET /devices`：`/dev/video*` 和可选 `v4l2-ctl --list-devices` 摘要。
- `POST /offer`：浏览器 SDP offer -> aiortc answer。缺 `aiohttp/aiortc/cv2/av` 或摄像头打不开时返回清晰 JSON 错误。
- `POST /peers/{peer_id}/close`：只释放 `/offer` answer 返回的指定 peer，用于机器自检、浏览器 Stop、页面刷新/关闭后主动清理服务端连接，避免下一轮自检或 browser smoke 被单连接保护误判为 `camera_in_use`。
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
- `/health.system_metrics`、`/health.stability_metrics`、`/health.system_diagnostics` 和 `/health.media_stability_summary` 只作 O7 短时稳定性证据采样；它们不会触发 `/offer`、不会打开摄像头、不会发送 `/cmd_vel`、不会启动 ROS2/Nav2/UART/WAVE ROVER，也不会作为自动控制输入。

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
- `client_ice_gathering_state=complete`：自检客户端在无 trickle 信令下已等待 ICE candidate 收齐再 POST `/offer`；若出现 `client_ice_gathering_timeout=true`，只能证明 answer 尝试，不应外推为稳定浏览器播放。
- `peer_id` + `server_peer_close.closed=true`：自检已经释放本次服务端 peer，后续自检可立刻重复运行。
- `server_peer_close.stopped_tracks=["video"]`：服务端关闭 peer 时已显式停止本地 `CameraTrack`，OpenCV 摄像头句柄应随之 release。
- `status=degraded` + `reason=webrtc_client_dependency_missing`：客户端缺 `aiohttp` 或 `aiortc`，只能确认 HTTP 诊断，不能确认 offer/answer。
- `status=failed` + `reason=health_unreachable`：目标 HTTP 服务不可达。
- `status=failed` + `reason=offer_rejected`：服务端拒绝 `/offer`，`offer_response` 会带服务端 JSON 错误，例如 `camera_in_use`、`offer_failed`。
- `status=failed` + `reason=first_frame_not_received`：answer 已处理但超时未收到首帧，通常指向摄像头读取、编码、ICE 或浏览器/网络链路问题。

默认自检在 degraded/failed 时仍返回 0，方便无依赖现场留下结构化诊断；如果 CI 或上车验收需要强制首帧，可加 `--require-frame` 或设置：

```bash
ROBER_WEBRTC_REQUIRE_FRAME=1 ROBER_WEBRTC_SELF_TEST_URL=http://127.0.0.1:8088 bash onboard/scripts/local_webrtc_camera_smoke.sh
```

## 同 LAN 浏览器播放 smoke

PC workstation 现在新增显式浏览器播放 smoke：

```bash
cd pc-tools/workstation
ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/ npm run o7:browser-smoke
```

`playwright` 是 `pc-tools/workstation` 的 devDependency，但 Chromium 浏览器 runtime 仍按执行环境安装；若 `npm run o7:browser-smoke` 报浏览器 executable 缺失，operator 最多执行一次 `npx playwright install chromium`（或需要系统包时按环境选择 `npx playwright install --with-deps chromium`），并把真实输出写入 sprint 证据。该命令只打开 LAN smoke 页面，点击页面里的 `Start WebRTC video`，等待真实浏览器 `<video>` 收到首帧，并输出机器可读 JSON。默认结果写入：

```text
pc-tools/workstation/.workstation-runtime/o7-browser-playback-smoke.json
```

输出 schema 为 `trashbot.o7.local_webrtc_browser_playback_smoke.v1`。关键字段：

- `status=ok` 且 `first_frame_received=true`：真实浏览器已收到首帧。
- `video_width` / `video_height`：浏览器 `<video>` 解码后的尺寸。
- `first_frame_ms`：从页面启动到首帧可见的耗时。
- `connection_state` / `ice_connection_state` / `ice_gathering_state` / `signaling_state`：浏览器侧 WebRTC 状态。
- `ontrack_count` / `receiver_track_states` / `transceiver_directions`：浏览器是否收到 video track，以及 recvonly/currentDirection 是否符合预期。
- `inbound_video_stats` / `selected_candidate_pair`：浏览器 `getStats()` 的入站 RTP 和候选对摘要；用于区分“有 track 但无 RTP”、“有 RTP 但 video 未解码/未播放”和 ICE 层失败。
- `peer_state_timeline`：浏览器 peer 状态最后若干次变化，便于对齐服务端 `/health.media_diagnostics`。
- `post_smoke_remote_health`：browser smoke 结束后再次只读 `/health`，用于确认服务端 peer 是否已释放。
- `console_errors` / `page_errors`：浏览器控制台和页面异常摘要。
- `blocked_reason`：缺 Playwright、缺 Chromium、页面不可达、按钮不可点、首帧超时或其他失败根因。
- `failure_category`：机器可读失败分类，当前用于区分 `dependency`、`remote_409`、`first_frame_timeout`、`ice_browser`、`page_console_error`、`browser_smoke_failed` 或 `none`。
- `remote_health_status` / `remote_active_peer_connections`：脚本在打开浏览器前只读 `GET /health` 的预检摘要，用于判断远端是否已有 active peer；该预检不发 `/offer`。
- `offer_http_status` / `offer_error_reason` / `offer_error_detail`：浏览器页面显式点击后 `/offer` 的状态和白名单错误摘要；用于区分 409 占用、依赖缺失、摄像头打不开和其他服务端拒绝。
- `observation_window_ms` / `final_ready_state` / `stable_video_width` / `stable_video_height`：失败时保留短稳态窗口和 `<video>` 最终状态，避免只留下超时字符串。
- `server_peer_id` / `server_peer_close_status`：页面 `/offer` 成功返回 peer id 时，脚本会尝试调用 `/peers/{peer_id}/close` 释放本次浏览器 peer；若 `/offer` 被 409 拒绝则 peer id 为空，需先处理服务端已有 active peer。
- `safe_to_control=false` / `sends_commands=false` / `robot_control_executed=false` / `workstation_api_offer_executed=false`：即使 browser smoke 显式点击页面触发 `/offer`，PC API/UI 仍不能自动发 offer、不能创建控制入口、不能发送机器人控制。

浏览器 smoke 是显式命令，不由 PC API 自动触发。缺 Playwright/Chromium 或远端不可达时必须输出 `degraded/failed/fail_closed`，不能把依赖缺失或连接失败冒充成首帧通过。需要强制首帧作为验收门时可设置：

```bash
ROBER_O7_BROWSER_SMOKE_REQUIRE_FRAME=1 ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/ npm run o7:browser-smoke
```

安全边界保持不变：

- 只读视频播放验证。
- 不发送机器人控制。
- 不启动 ROS2/Nav2/UART/WAVE ROVER。
- 不进入公网 RTC、TURN、鉴权或云 relay。

## Peer 释放语义

服务端所有 peer 结束路径必须走同一套清理顺序：先从 active peer 表移除，再枚举 `pc.getSenders()` 并对本地 track 调用 `stop()`，最后关闭 `RTCPeerConnection`。这个顺序覆盖 `/peers/{peer_id}/close` 主动关闭、`connectionState=failed/closed/disconnected` 自动清理、`/offer` 中途失败和服务 shutdown。

`CameraTrack.stop()` 是幂等的，因为异常路径可能先直接 stop 手里的 track，再通过 sender 表做统一 cleanup。连续 smoke 验收应同时看三类证据：`server_peer_close.stopped_tracks` 包含 `video`、`/health.active_peer_connections=0`、`fuser -v /dev/video0` 在 close 后无占用输出。

## 媒体诊断字段

`/health.media_diagnostics.active_peers.<peer_id>.frames_read` 表示服务端 `CameraTrack` 已从 OpenCV 读取并交给 aiortc 的帧数。浏览器无首帧时若该值持续增长，优先怀疑浏览器 `<video>` 绑定、解码或前端播放路径；若一直为 0，则优先查 server 摄像头读取链路。

`last_frame_ts_ms`、`last_frame_width`、`last_frame_height` 是最近一帧时间与尺寸；`camera_read_failures` 和 `last_error` 是摄像头读取失败计数与最近错误。`media_diagnostics.last_closed_peer.stats` 保留最近关闭 peer 的最终媒体统计，可和 browser smoke 的 `server_peer_close_status=200:closed` 一起判断 close 前 server 是否真的读到过帧。

## 短时稳定性健康采样字段

PC browser smoke 在 3-5 分钟播放期间可以轮询 `GET /health`，把同 LAN 首帧证据扩展为 FPS、延迟、CPU、内存、温度和 camera release 证据。新增字段是只读诊断面，不是控制面：

- `system_metrics.process_uptime_s`：PC 摘要层直接消费的进程 uptime。
- `system_metrics.load_1m`：可用时输出 1 分钟 load；不可用时输出 `load_unavailable_reason`。
- `system_metrics.process_rss_bytes`：可用时输出进程 RSS；不可用时输出 `memory_unavailable_reason`。
- `system_metrics.temperature_celsius`：可用时输出第一路温度样本；不可用时输出 `temperature_unavailable_reason`。
- `stability_metrics.active_peer_count`：当前 active peer 数，和 `active_peer_connections` 保持同义兼容。
- `stability_metrics.active_frames_read` / `active_camera_read_failures`：当前 active peer 读帧与失败总数。
- `stability_metrics.last_closed_frames_read` / `last_closed_fps_estimate` / `last_closed_camera_read_failures` / `last_closed_track_stopped`：最近关闭 peer 的最终帧数、估算 FPS、读帧失败数和 track 是否 stop，便于 browser smoke 结束后判断 camera release。
- `system_diagnostics.sample.wall_time_ms`：墙钟毫秒时间戳，用于和浏览器 JSON、服务端日志对齐。
- `system_diagnostics.sample.monotonic_s`：进程内 monotonic 采样时间，避免系统时间跳变影响短时趋势。
- `system_diagnostics.sample.process_started_wall_time_ms` / `process_uptime_s`：smoke 服务启动时间和进程 uptime。
- `system_diagnostics.cpu.load_average`：`os.getloadavg()` 的 1/5/15 分钟 load；系统不支持时返回 `{ "available": false, "reason": "os_getloadavg_unavailable" }`。
- `system_diagnostics.cpu.process_cpu_percent` / `system_cpu_percent`：安装 `psutil` 时输出非阻塞 CPU 百分比；缺 `psutil` 或运行时异常时返回结构化 `not_available`，`/health` 不失败。
- `system_diagnostics.memory`：优先用 `psutil` 输出进程 RSS/VMS 和系统内存；缺 `psutil` 时尽量退回 `/proc/self/status` 的进程 RSS；两者都不可用时返回 `not_available`。
- `system_diagnostics.temperature.samples[]`：从 `/sys/class/thermal/thermal_zone*/temp` 和 `/sys/class/hwmon/hwmon*/temp*_input` 读取摄氏温度；没有温度文件时返回 `{ "available": false, "reason": "temperature_files_not_found" }`。
- `media_stability_summary.active_peers.<peer_id>`：对当前 peer 的 `frames_read`、`camera_read_failures`、`last_frame_age_ms`、最近帧尺寸、连接状态和估算 `fps_estimate` 做稳定摘要。
- `media_stability_summary.totals.active_frames_read` / `active_camera_read_failures`：当前 active peer 的读帧与失败总数，方便 PC 轮询端快速画趋势。
- `media_stability_summary.last_closed_peer`：最近关闭 peer 的清理结果和最终媒体摘要，用于确认 browser smoke 结束后 camera release 是否发生。

所有缺失指标都必须 fail-open 为结构化诊断字段，不能把缺温度文件、缺 `psutil`、裁剪系统 `/proc` 权限差异升级为 HTTP 500。短时稳定性验收仍需结合 browser 侧 `getStats()`、`first_frame_ms`、console/page errors 和 close 后 `/health.active_peer_connections=0` 一起判断。

## 常见失败定位

- `/devices` 为空：摄像头未枚举、驱动未加载、USB/CSI 连接或权限问题。
- `/offer` 返回 `webrtc_dependency_missing`：缺 `aiohttp`、`aiortc`、`opencv-python` 或 `av`。
- `/offer` 返回 `camera_open_failed`：设备路径错误、摄像头被其他进程占用、权限不足或 OpenCV backend 不支持。
- 自检返回 `offer_rejected` 且服务端 detail 为 `camera_open_failed:<source>`：同上，优先确认 `ROBER_CAMERA_SOURCE` 和摄像头占用。
- 自检返回 `first_frame_not_received`：answer/ICE 和首帧之间失败，需要结合 `/tmp/rober-local-webrtc-camera.log`、CPU/温度、摄像头帧率和同 LAN 网络继续定位。
- 浏览器 smoke `failure_category=remote_409`、`offer_http_status=409` 或控制台出现 `409 (Conflict)`，且 `/health.active_peer_connections=1`：服务端单 peer 保护已被现有浏览器或未关闭自检占用，本轮不能证明真实浏览器首帧；先调用 `/peers/{peer_id}/close`、刷新服务端或确认人工观看会话，再重新执行一次显式 browser smoke。
- `/peers/{peer_id}/close` 返回 200 但 `fuser -v /dev/video0` 仍显示 smoke 进程：说明本地 track 没有释放或仍有读取线程占用，不能继续跑 browser smoke，应先看 close JSON 里的 `stopped_tracks` / `track_stop_errors` 和服务端日志。
- 浏览器标签页刷新/关闭后仍出现 `active_peer_connections=1`：新版页面会在 Stop、`pagehide`、`beforeunload` 时对 answer 返回的 `peer_id` 调用 `/peers/{peer_id}/close`；若远端仍运行旧脚本或浏览器被强杀导致 close 请求未到达，可用 `/health.active_peer_ids` 定位残留 peer，必要时重启 8088 smoke 服务后重跑。
- 浏览器 smoke `failure_category=first_frame_timeout`：页面已显式点击并等待 `<video>`，但超时未到 `readyState>=2` 且尺寸仍为空；优先结合 ICE 状态、页面错误、服务端日志、CPU/温度和摄像头帧率继续定位。
- 浏览器 smoke `failure_category=track_received_no_rtp`：页面收到 video track，但 `inbound_video_stats` 没有 packets/decoded frame，优先查 RTP 是否从 aiortc sender 启动、codec/RTCP/候选路径是否正常。
- 浏览器 smoke `failure_category=video_element_decode_timeout`：浏览器已有入站 RTP 或 decoded frame，但 `<video>` 没有进入 `readyState>=2`，优先查 headless Chromium 解码、autoplay/play promise、video 绑定和页面脚本。
- 浏览器 smoke ICE connected 但 `<video>` `readyState=0`：新版页面会在 `event.streams[0]` 为空时用 `new MediaStream([event.track])` 兜底绑定 streamless track，并主动调用 `video.play()`。若 server `frames_read` 增长但浏览器仍无首帧，下一步重点查 Chrome 编解码/自动播放/页面脚本错误；若 `frames_read=0`，重点查 server 摄像头读取链路。
- 浏览器页面有 answer 但无画面：需要查看 `/tmp/rober-local-webrtc-camera.log`，并补真实浏览器控制台、ICE 状态、CPU/温度和摄像头帧率证据。
- `npm run o7:browser-smoke` 返回 `playwright_dependency_missing_use_npx_p_playwright_or_install_browser_runtime`：当前 PC workstation Node 环境缺浏览器自动化依赖，本轮只能保留 fail-closed JSON，不能证明真实浏览器播放。
