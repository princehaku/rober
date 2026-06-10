# PC Camera Visible Frame Proof

sprint_type: micro

Owner: `full-stack-software-engineer`

Run time: 2026-06-11 07:50 CST

## 实际改动

- 修复 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的 WebRTC offer 时序：`setLocalDescription` 后等待 `iceGatheringState=complete` 或短超时，再把 SDP 发给 workstation camera offer 代理。原因是上位机当前按非 trickle SDP 处理，过早发送会导致远端 `remote_sdp_candidate_count=0`。
- 同一组件增强 video 绑定与高级诊断：收到远端 video track 后优先绑定 `RTCTrackEvent.streams[0]`，主动 `play()`，并在高级诊断暴露真实 video 元素的 `srcObject`、`readyState`、`videoWidth/videoHeight`、`presentedFrames` 和 `requestVideoFrameCallback` 状态。
- 更新 `pc-tools/workstation/test/App.test.ts`：fake WebRTC 事件携带远端 stream，并断言 `<video data-testid="robot-camera-preview-video">` 绑定到 `srcObject`。
- 更新 `docs/product/pc_tools_workstation.md` 与 `pc-tools/README.md`：说明 camera preview 必须等待 ICE candidates，真实 smoke 必须证明 video 元素绑定/帧，不再只用 `streaming/live` 间接状态。
- 新增本轮 artifacts：
  - `artifacts/browser_dom_first_screen.json`
  - `artifacts/browser_camera_visible_frame_state.json`
  - `artifacts/browser_camera_stop_state.json`
  - `artifacts/remote_camera_health_before_final.json`
  - `artifacts/remote_camera_health_during_visible_frame.json`
  - `artifacts/remote_camera_health_after_stop_final.json`
  - `artifacts/remote_camera_health_after_failed_attempt_cleanup.json`

## 根因判断

根因是产品代码的浏览器 WebRTC offer 时序 bug，不是相机设备坏，也不只是 smoke 采样问题。

上一轮和本轮修复前真实上位机 health 显示失败会话 `remote_sdp_candidate_count=0`、`ice_connection_state=checking`、`frames_read=0`。浏览器页面虽然能进入 `preview_status=streaming`、`video_track_state=live`，但远端没有收到 host candidates，非 trickle 模式下无法完成真实媒体流。

本轮修复后真实上位机 health 显示新会话 `remote_sdp_candidate_count=2`、`ice_connection_state=completed`、`frames_read=815` during active，Stop 后 last closed peer `frames_read=924`。

## 真实可见帧证据

- Browser artifact：`artifacts/browser_camera_visible_frame_state.json`
- 关键字段：
  - `final.detail.preview_status=streaming`
  - `final.detail.ice_connection_state=connected`
  - `final.detail.video_track_state=live`
  - `final.detail.video_element_src_object=true`
  - `final.detail.video_element_ready_state=4`
  - `final.detail.video_element_size=640x480`
  - `final.detail.video_element_frame_status=frame_callback_observed`
  - `final.detail.video_element_presented_frames=2`
  - `final.vueElementFrameProven=true`
- 远端辅助证据：`artifacts/remote_camera_health_during_visible_frame.json`
  - `active_peer_connections=1`
  - `media_diagnostics.active_peers.<peer>.remote_sdp_candidate_count=2`
  - `media_diagnostics.active_peers.<peer>.connection_state=connected`
  - `media_diagnostics.active_peers.<peer>.ice_connection_state=completed`
  - `media_diagnostics.active_peers.<peer>.frames_read=815`
  - `last_frame_width=640`
  - `last_frame_height=480`

说明：Browser 插件的只读隔离脚本直接读 `video.srcObject` 仍返回 `false`，但同一页面 Vue 本体高级诊断读到 `video_element_src_object=true`，且 video 元素直接读数已有 `readyState=4`、`videoWidth=640`、`videoHeight=480`，并触发 `requestVideoFrameCallback`。因此本轮可证明浏览器可见帧，不再停留在 signaling/track live。

## Stop cleanup 证据

- Browser stop artifact：`artifacts/browser_camera_stop_state.json`
  - `detail.preview_status=stopped_by_user`
  - `detail.cleanup_status=peer_closed:closed`
  - `detail.peer_id=not_assigned`
  - `detail.video_element_src_object=false`
  - `video.readyState=0`
- 远端 cleanup artifact：`artifacts/remote_camera_health_after_stop_final.json`
  - `active_peer_connections=0`
  - `active_peer_ids=[]`
  - `stability_metrics.last_closed_frames_read=924`
  - `media_diagnostics.last_closed_peer.stats.remote_sdp_candidate_count=2`
  - `media_diagnostics.last_closed_peer.stats.last_frame_width=640`
  - `media_diagnostics.last_closed_peer.stats.last_frame_height=480`
  - `media_diagnostics.last_closed_peer.cleanup.stopped_tracks=["video"]`

## 首屏与安全边界

- Browser first-screen artifact：`artifacts/browser_dom_first_screen.json`
- 关键字段：
  - `title=Rober 小车控制台`
  - `cardTitles=["小车连接","实时画面","雷达","地图","移动/导航"]`
  - `advancedDetailsOpen=false`
  - `advancedToolsDetailsOpen=false`
  - `forbiddenVisibleHits=[]`
- 本轮 Browser 操作只点击 `连接/刷新`、`打开画面`、`关闭画面`。
- 本轮没有调用 `/api/base/manual`、`/cmd_vel`、Nav2 goal 或任何非零运动 endpoint。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run test`：通过，`2 passed (2)`、`89 passed (89)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- 本地 workstation API：`PORT=8794 npm run api`，通过，监听 `http://127.0.0.1:8794`。
- 真实上位机 Browser smoke：通过，目标 `http://192.168.1.11:8787`，证据见上文 Browser 与 remote health artifacts。
- 真实上位机 cleanup/readback：通过，`/api/camera/health active_peer_connections=0`。

## 剩余风险

- Browser 插件只读隔离脚本直接读取 `video.srcObject` 仍为 `false`，但页面本体诊断、`readyState=4`、`640x480`、frame callback 和远端 frames_read 共同证明可见帧。后续若要让外部黑盒脚本直接读 `srcObject`，需要换 Playwright/CDP 执行上下文或用页面内显式 telemetry 字段。
- 本轮只证明 PC 页面实时图传可见帧和 Stop cleanup；不证明公网 relay、TURN/STUN、录制、截图归档、长期稳定性、任何运动控制或送达成功。

## 完成前反思

- 改动限制在允许文件和本 sprint 目录内，未修改 `onboard/**`、`docs/vendor/**`、硬件配置、launch、底盘/串口/运动协议代码。
- 已同步更新 PC 产品文档和 README。
- 验证失败后已定位根因并修复，未把第一轮失败作为最终结果。
- 已保留修复前失败根因 artifact 和修复后成功/cleanup artifacts。
