# O7 Browser Playback Real Proof Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/package.json` / `package-lock.json` 增加 `playwright` devDependency，让 `npm run o7:browser-smoke` 不再依赖临时 `npx -p playwright` 注入。
- `pc-tools/workstation/scripts/o7-browser-playback-smoke.mjs` 增强真实浏览器 smoke 证据：只读 `/health` 预检、记录 `failure_category`、`remote_active_peer_connections`、`offer_http_status`、短稳态字段、console/page error count、`server_peer_id` 和 `server_peer_close_status`。脚本仍只在 operator 显式执行时打开 LAN 页面并点击 `Start WebRTC video`，PC API/UI 不自动 POST `/offer`。
- `onboard/scripts/local_webrtc_camera_smoke.py` 修复板端 peer 清理：`/peers/{peer_id}/close`、连接状态清理、offer 异常和 shutdown 都统一显式 stop 本地 video track，再关闭 `RTCPeerConnection`，避免 OpenCV 摄像头 FD 残留导致下一轮 409 或 `camera_open_failed`。
- 同一脚本继续补媒体诊断：`/health.media_diagnostics` 暴露 active/last-closed peer 的连接状态、摄像头 backend、帧读取计数和 track stop 时间；浏览器页面对 streamless `ontrack` fallback 到 `new MediaStream([event.track])` 并主动 `video.play()`。
- 新增 `onboard/scripts/test_local_webrtc_camera_smoke.py`，用 fake peer/track 验证 close path 会调用 `track.stop()`，并静态保护浏览器页面的 Stop / pagehide / beforeunload peer close 逻辑和 streamless track 绑定。
- `pc-tools/workstation/src/shared/contracts.ts`、`src/server/o7LocalWebrtcCamera.ts`、`src/components/O7LocalCameraSmokePanel.vue` 透出 browser smoke 失败分类、offer 状态、peer close 状态和短稳态字段，operator 不用直接打开 JSON 文件也能看到 blocker。
- 更新 `docs/interfaces/o7_local_webrtc_camera_smoke.md` 和 `docs/product/pc_tools_workstation.md`，补充 Playwright/Chromium runtime、peer release、连续 smoke、`first_frame_timeout` 和 fail-closed 边界。

## 验证结果

### 远端 8088 与板端 self-test

- 远端服务：`op-z3-b6.home`，`0.0.0.0:8088`，`imports={"aiohttp":true,"aiortc":true,"cv2":true,"av":true}`，`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`。
- 修复前定位：浏览器 close 后远端 `fuser -v /dev/video0` 显示 smoke 进程仍占用摄像头；后续 self-test 失败为 `offer_failed camera_open_failed:0`。
- 修复后远端 self-test：

```text
status=ok
answer_received=true
connection_state=connected
first_frame_received=true
first_frame.width=640
first_frame.height=480
duration_ms=1955
server_peer_close.closed=true
server_peer_close.stopped_tracks=["video"]
server_peer_close.stats.frames_read=3
server_peer_close.active_peer_connections=0
```

- self-test 后复查：`fuser -v /dev/video0` 无占用输出，`/health.active_peer_connections=0`。

### PC 真实浏览器 smoke

命令：

```bash
cd pc-tools/workstation
ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/ ROBER_O7_BROWSER_SMOKE_REQUIRE_FRAME=1 npm run o7:browser-smoke
```

最终关键输出：

```json
{
  "status": "failed",
  "browser_available": true,
  "playwright_available": true,
  "start_clicked": true,
  "first_frame_received": false,
  "failure_category": "first_frame_timeout",
  "remote_health_status": "ready",
  "remote_active_peer_connections": 0,
  "offer_http_status": 200,
  "connection_state": "connecting",
  "ice_connection_state": "connected",
  "ice_gathering_state": "complete",
  "signaling_state": "stable",
  "final_ready_state": 0,
  "video_width": null,
  "video_height": null,
  "console_error_count": 0,
  "page_error_count": 0,
  "server_peer_close_status": "200:closed",
  "safe_to_control": false,
  "sends_commands": false,
  "robot_control_executed": false,
  "workstation_api_offer_executed": false
}
```

板端 `/health.media_diagnostics.last_closed_peer` 对这轮 browser smoke 的服务端侧摘要为：`camera_opened=true`、`local_sdp_has_video=true`、`remote_sdp_has_video=true`、`actual_width=640`、`actual_height=480`、`actual_fps=22`、`frames_read=0`、`track_stopped=true`。结论：本轮已解决 Playwright 依赖、远端 stale peer、摄像头 FD 残留和连续 self-test 问题；真实 PC Chromium browser 仍未拿到 `<video>` 首帧，剩余 blocker 从“服务端占用/资源释放”推进为“浏览器媒体首帧超时，且服务端该浏览器 peer 未开始读取 video frame”。

### Guardrails

- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`：通过。
- `python3 -m unittest onboard/scripts/test_local_webrtc_camera_smoke.py`：`Ran 3 tests ... OK`。
- `cd pc-tools/workstation && npm run test`：`Test Files 2 passed (2)`，`Tests 45 passed (45)`。
- `cd pc-tools/workstation && npm run build`：Vite `33 modules transformed`，client/server TypeScript 构建通过。
- `cd pc-tools/workstation && npm run lint`：通过，无输出。
- `git diff --check -- pc-tools/workstation onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/test_local_webrtc_camera_smoke.py docs/interfaces/o7_local_webrtc_camera_smoke.md docs/product/pc_tools_workstation.md sprints/2026.06.01_05-06_o7-browser-playback-real-proof/tech-done.md`：通过，无输出。

## 失败定位

- `first_frame_received=false`，因此没有真实 PC browser playback proof。
- 当前失败不再是 Playwright/Chromium 缺失：`browser_available=true`、`playwright_available=true`。
- 当前失败不再是远端 409 或 active peer：预检 `remote_active_peer_connections=0`，`offer_http_status=200`。
- 当前失败不再是板端摄像头完全不可用：远端 self-test 已证明 `first_frame_received=true`、640x480，并且 close 后释放 video track。
- 当前 blocker 是 PC Chromium/headless 真实页面在 ICE connected / signaling stable 后 `<video>` 仍没有到 `readyState>=2`，分类为 `first_frame_timeout`；板端 `media_diagnostics` 同时显示该 browser peer `frames_read=0`，说明 aiortc 没有开始拉取 `CameraTrack.recv()`。下一步需要围绕 transceiver direction / sender negotiation / Chromium headless media pipeline / RTP codec 兼容性继续定位。

## 剩余风险

- 未证明 PC 真实浏览器首帧、首帧耗时、短时稳定性、延迟、CPU/温度、长期帧率。
- 未证明云 relay、公网 RTC、TURN、鉴权、真实 ASR/TTS、真实手控/Nav2、真实 robot ACK、真实手机或真实上车任务闭环。
- 当前远端脚本已由本轮同步到 `root@192.168.1.11:/root/rober/onboard/scripts/local_webrtc_camera_smoke.py` 并验证；如果板端后续回滚到旧脚本，peer close 后摄像头 FD 残留问题会复发。

## O7 上调建议

不建议 O7 从约 92% 上调。依据：板端 LAN self-test 已恢复并能连续释放资源，但 PC 真实浏览器 smoke 仍没有 `first_frame_received=true`、`video_width/video_height` 或 `first_frame_ms`。O7 只有在 PC Chromium 或真实浏览器输出 `status=ok` 且首帧字段完整后，才建议上调。
