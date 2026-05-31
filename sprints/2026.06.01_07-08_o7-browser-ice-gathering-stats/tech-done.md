# Micro Sprint Tech Done

sprint_type: micro

## 目标

推进 O7 PC Chromium/browser WebRTC camera smoke，收敛上一轮 `first_frame_timeout` 且远端 browser peer `frames_read=0` 的根因。范围限定为 LAN-only camera smoke、PC browser smoke 诊断、PC 只读状态展示与接口文档；未触碰 ROS2/Nav2/UART/WAVE ROVER，也未发送任何机器人控制。

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 页面 `Start WebRTC video` 在无 trickle 信令下等待 `iceGatheringState=complete` 后再 POST `/offer`，避免 offer 缺 host candidates 时 answer 成功但 RTP 不启动。
  - `--self-test-url` 客户端同步等待 ICE gathering complete，并在 JSON 输出 `client_ice_gathering_state` / `client_ice_gathering_timeout`。
  - 服务端 `/health.media_diagnostics` 记录远端 SDP video direction、candidate 数量和 end-of-candidates，用于复盘 browser/self-test offer 是否完整。
- `onboard/scripts/test_local_webrtc_camera_smoke.py`
  - 增加页面必须等待 ICE gathering complete 的回归测试。
- `pc-tools/workstation/scripts/o7-browser-playback-smoke.mjs`
  - browser smoke 增加 `ontrack_count`、receiver/transceiver 摘要、inbound RTP stats、候选对摘要、peer 状态时间线和结束后远端 health 摘要。
  - 失败分类细化为 `track_received_no_rtp` 与 `video_element_decode_timeout`，后续能区分 track、RTP、video 解码/绑定问题。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `O7BrowserPlaybackSmokeSummary` 合同，承接新增 browser stats 字段。
- `pc-tools/workstation/src/server/o7LocalWebrtcCamera.ts`
  - PC API 继续只读 smoke JSON，白名单摘要新增 stats 字段；仍固定 `offer_executed=false`、`webrtc_session_created=false`、`safe_to_control=false`。
- `pc-tools/workstation/src/components/O7LocalCameraSmokePanel.vue`
  - O7 local camera 卡片展示 `ontrack`、inbound packets、decoded frames 和 candidate pair 状态，便于运营调试页直接看阻塞层。
- `docs/interfaces/o7_local_webrtc_camera_smoke.md`
  - 补充 ICE gathering、browser stats 字段、细化失败分类和排障语义。
- `docs/product/pc_tools_workstation.md`
  - 更新 O7 browser playback smoke 的产品边界和诊断能力说明。

## 验证结果

- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`
  - 通过，exit 0。
- `python3 -m unittest onboard/scripts/test_local_webrtc_camera_smoke.py`
  - 通过，`Ran 4 tests in 0.067s`，`OK`。
- 远端同步与 8088 smoke 服务
  - 已用 `scp -P 37878` 同步 `local_webrtc_camera_smoke.py` / `.sh` 到 `root@192.168.1.11:/root/rober/onboard/scripts/`。
  - 已重启远端 `PORT=8088 ROBER_CAMERA_SOURCE=0 nohup bash /root/rober/onboard/scripts/local_webrtc_camera_smoke.sh`。
- 远端 self-test
  - 首次与 browser smoke 并发执行，按单 peer 保护返回 `offer_http_status=409` / `camera_in_use`；已串行重跑。
  - 串行重跑通过：`status=ok`、`answer_received=true`、`client_ice_gathering_state=complete`、`connection_state=connected`、`first_frame_received=true`、`first_frame.width=640`、`first_frame.height=480`、`server_peer_close.status=200`、`server_peer_close.closed=true`、`stopped_tracks=["video"]`、`active_peer_connections=0`。
- PC Chromium browser smoke
  - `cd pc-tools/workstation && ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/ ROBER_O7_BROWSER_SMOKE_REQUIRE_FRAME=1 npm run o7:browser-smoke`
  - 通过，exit 0：`status=ok`、`first_frame_received=true`、`video_width=640`、`video_height=480`、`first_frame_ms=2281`、`connection_state=connected`、`ice_connection_state=connected`、`ice_gathering_state=complete`、`signaling_state=stable`、`ontrack_count=1`、`inbound_video_stats[0].packetsReceived=2`、`framesDecoded=1`、`server_peer_close_status=200:closed`、`post_smoke_remote_health.activePeerConnections=0`。
- `cd pc-tools/workstation && npm run test`
  - 通过，`Test Files 2 passed (2)`，`Tests 45 passed (45)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过，exit 0。
- `cd pc-tools/workstation && npm run build`
  - 通过，Vite 输出 `33 modules transformed`，`built in 2.41s`。

## 失败定位

上一轮 browser smoke 的核心失败收敛为：页面在没有 trickle ICE 信令的 HTTP `/offer` 模式下，未显式等待 ICE gathering complete 就提交 offer，导致服务端能 answer、ICE 状态可进入 connected/stable，但浏览器会话没有稳定触发 aiortc `CameraTrack.recv()`，最终 `<video>` 无首帧且服务端 browser peer `frames_read=0`。

本轮修复后，browser smoke 已证明真实 Chromium 收到 track、收到 RTP、解码 1 帧并显示 640x480 首帧；远端 health 也证明 peer close 后摄像头 track 已释放。

## 剩余风险

- 当前证据仍是同 LAN / 同 WiFi / HTTP smoke，不证明云 relay、公网 RTC、TURN、鉴权、长期稳定性、CPU/温度、弱网恢复或真实用户浏览器体验。
- PC API/UI 仍按设计只读 `/health`、`/devices` 和显式 smoke JSON，不自动 POST `/offer`；真实产品播放入口仍需后续单独设计安全确认、鉴权和会话生命周期。
- `selected_candidate_pair` 在当前 Chromium stats 中为 `null`，但 inbound RTP stats 已能证明媒体入站；后续若需要候选对细节，可继续从 `transport.selectedCandidatePairId` 反查。
- 本轮未修改 `OKR.md` 和 `docs/process/okr_progress_log.md`，留给 Product/OKR owner 根据证据收口。

## OKR 最低优先级核对

本轮直接针对当前最低可推进项 O7：PC Chromium/browser WebRTC camera smoke 首帧缺口。测试作为护栏，核心产出是从 `first_frame_timeout` 推进到同 LAN Chromium 首帧通过。

## Product/OKR 收口

Product 判断本轮把 O7 状态从“browser first frame not proven / first_frame_timeout”推进到“same-LAN Chromium browser playback first-frame proven”。可引用证据为 `pc-tools/workstation/.workstation-runtime/o7-browser-playback-smoke.json`：`status=ok`、`first_frame_received=true`、`video_width=640`、`video_height=480`、`first_frame_ms=2281`、`connection_state=connected`、`ice_connection_state=connected`、`ice_gathering_state=complete`、`signaling_state=stable`、`ontrack_count=1`、`inbound_video_stats[0].packetsReceived=2`、`framesDecoded=1`、`server_peer_close_status=200:closed`、`post_smoke_remote_health.activePeerConnections=0`。

OKR 方向判断：继续，不暂停、不替换。`OKR.md` 已把 O7 从约 92% 调整为约 94%，因为本轮关闭的是同 LAN Chromium 浏览器首帧和 browser stats 证据缺口，但仍没有证明公网 RTC、TURN、云 relay、鉴权、长期帧率/延迟/CPU/温度、真实用户浏览器/手机体验、ASR/TTS、手控/Nav2、真实 robot ACK 或上车任务闭环。

本轮没有已完成 KR 移入历史归档区；O7 KR 仍保留在当前推进区。历史证据记录位置为 `docs/process/okr_progress_log.md` 的 `2026-06-01 07-08｜o7-browser-ice-gathering-stats` 小节和本段。下一优先级建议：不再重复消费 `first_frame_timeout`，改为补 3-5 分钟短时稳定性、帧率/延迟/CPU/温度、断开重连、camera release、产品播放入口安全确认、鉴权和会话生命周期。
