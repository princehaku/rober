# 2026-06-10 23:05 PC Camera WebRTC Preview V1 设计

## sprint_type

micro

## owner

`full-stack-software-engineer`

## 用户价值 / 北极星

- 用户当前北极星不是“证明 PC 页面能看到真实图传”，而是“PC 页面能完整控制小车雷达、建图、定位移动、手动移动、实时图传”的最后一个缺口先补齐图传观察面。
- 本轮只交付 `Robot Control` 页面的真实摄像头实时预览闭环，让 operator 在不开放任何运动控制的前提下，用已有上位机 `/api/camera/offer` 建立真实 WebRTC video preview。
- 成功定义不是“云端 RTC 完整产品化”，而是“本机 PC 页面可以显式 Start Preview、看到实时视频、显式 Stop Preview，并且失败时给出可归因原因，离开页面或停止后完成 peer cleanup”。

## 本轮范围结论

- 做：
  - PC 页面通过 existing upper API `POST /api/camera/offer` 建立真实 WebRTC video preview。
  - PC 页面提供 `Start Preview` / `Stop Preview` 两个显式用户动作。
  - PC 页面展示 preview 状态、失败原因、peer id / session 清理状态。
  - 保留真实上位机 smoke evidence，证明 `camera service ready + offer 可用 + peer 可关闭`。
- 不做：
  - 不做云 relay。
  - 不做 TURN/STUN。
  - 不做音频。
  - 不做录制、截图归档、回放。
  - 不做任何运动控制或 safe command 放开。

## 功能点完整清单

1. `Robot Control` 页新增真实图传卡片，位置在 Camera readback 附近，文案明确它是 `real WebRTC preview`，不是 mock preview。
2. 默认状态为 `preview_status=idle_not_started`，页面初始不自动创建会话，避免一打开页面就占用 camera peer。
3. 用户点击 `Start Preview` 后：
   - 前端创建本地 `RTCPeerConnection`。
   - 只申请 video transceiver，不申请 audio。
   - 生成 SDP offer，通过 workstation Node 层转发到 existing upper API `/api/camera/offer`。
   - 使用上位机返回的 SDP answer 完成协商。
   - 页面进入 `preview_status=connecting_offer_posted` -> `preview_status=streaming` 或失败态。
4. 用户点击 `Stop Preview` 后：
   - 前端关闭本地 `RTCPeerConnection`。
   - 若已有 `peer_id`，必须调用 existing upper API `POST/DELETE /api/camera/peers/{peer_id}/close` 对应的 Node 代理关闭远端 peer。
   - 页面进入 `preview_status=stopped_by_user`。
5. 离开页面、切换 baseUrl、重复点击 Start、刷新失败重试时，旧 peer 必须先 cleanup，避免 active peers 泄漏。
6. 状态展示至少包含：
   - `preview_status`
   - `camera_health_status`
   - `selected_camera_device_summary`
   - `peer_id`
   - `ice_connection_state`
   - `video_track_state`
   - `failure_reason`
   - `last_offer_at`
   - `last_stop_at`
7. 失败原因必须可归因，至少覆盖：
   - `camera_not_ready`
   - `offer_request_failed`
   - `offer_http_status_<code>`
   - `invalid_offer_response`
   - `remote_answer_missing`
   - `webrtc_set_remote_description_failed`
   - `video_track_not_received`
   - `peer_cleanup_failed`
   - `upper_api_unreachable`
8. 页面必须明确保持以下入口 disabled，不得因为图传成功而解锁：
   - `/api/base/manual`
   - `/cmd_vel`
   - Nav2 goal
   - radar start
   - map start
   - keyboard control
   - map click goal
9. 页面必须持续展示 fail-closed 总状态：
   - `safe_to_control=false`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
10. 真实 smoke evidence 至少要能回填：
   - 上位机 `/api/camera/health` ready
   - `/api/camera/offer` 返回成功 answer 和 `peer_id`
   - `active peers` 在 Start 后增加、Stop 后回到 `0`
   - 页面能显示真实视频帧而非 placeholder

## Engineer 文件范围

- 允许修改：
  - `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `pc-tools/workstation/src/client/workstationApi.ts`
  - `pc-tools/workstation/src/server/index.ts`
  - `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `pc-tools/workstation/src/shared/contracts.ts`
  - `pc-tools/workstation/test/` 下与 Robot Control / camera preview 相关测试
  - `pc-tools/README.md` 中 Robot Control camera preview 说明
- 本轮产品设计文件：
  - `docs/product/pc_tools_workstation.md`
  - `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/tech-done.md`
- 不允许修改：
  - `onboard/` 代码
  - 上位机产品代码
  - ROS2 节点
  - 硬件配置
  - `OKR.md`

## 建议接口落点

- workstation Node 新增本地代理接口，供 Vue 使用，避免浏览器直接跨域访问上位机：
  - `POST /api/robot-control/camera/offer?baseUrl=<robot-api-base-url>`
  - `POST /api/robot-control/camera/peers/:peerId/close?baseUrl=<robot-api-base-url>`
- 这两个本地代理只转发到 existing upper API：
  - `/api/camera/offer`
  - `/api/camera/peers/{peer_id}/close`
- 代理必须继承 Robot Control 既有 baseUrl 白名单：
  - 仅允许回环或 RFC1918 HTTP
  - 拒绝 credentials、query/hash 注入
- 代理只服务 camera preview，不能顺带放开 `/api/base/manual`、`/cmd_vel` 或其他控制 API。

## 验收口径

1. 页面首次加载时，preview 为 `idle_not_started`，不会自动占用 peer。
2. 点击 `Start Preview` 后，页面在可接受时间内进入 `streaming`，且 `<video>` 出现真实远端视频轨。
3. 点击 `Stop Preview` 后，本地 peer 关闭，远端 peer cleanup 成功，页面进入 `stopped_by_user`。
4. 连续执行 `Start Preview -> Stop Preview -> Start Preview` 不会遗留僵尸 peer。
5. 失败时 UI 必须显示具体 `failure_reason`，不能只显示通用 `locked_no_webrtc_session`。
6. 无论 preview 成功还是失败，`/api/base/manual`、`/cmd_vel`、Nav2 goal、radar start、map start、keyboard control、map click goal 都保持 disabled。
7. 真实 smoke 证据必须证明 `active peers=0` 能在 Stop 后回收完成。

## 验收命令

```bash
git status --short --branch
test -f sprints/2026.06.10_23-05_pc_camera_webrtc_preview/tech-done.md
rg -n "sprint_type|实时图传|WebRTC|/api/camera/offer|peer|Start Preview|Stop Preview|验收|文件范围|cmd_vel|safe_to_control|delivery_success" sprints/2026.06.10_23-05_pc_camera_webrtc_preview/tech-done.md
git diff --check
```

## 真实 smoke evidence 要求

- Engineer 交付时必须附带真实上位机 smoke 证据，而不是只给本地 mock：
  - `curl` 或日志证明 `/api/camera/health` 为 ready。
  - `curl` 或日志证明 `/api/camera/offer` 成功返回 answer / `peer_id`。
  - `Start Preview` 后的页面证据，证明真实视频帧已进入。
  - `Stop Preview` 后的页面或 API 证据，证明 peer cleanup 完成且 active peers 回到 `0`。
- 若只能完成本地 mock，必须按 blocked 交付，不能宣称 V1 完成。

## 风险边界

1. 本轮依赖 browser WebRTC 能力和上位机 `aiortc/cv2/av` 环境；若浏览器策略、codec 或 answer schema 漂移，最可能卡在 offer/answer 协商阶段。
2. 不引入 TURN/STUN 的前提下，本轮只面向同局域网 PC -> 上位机直连；这符合当前 V1 范围，不解决跨网段问题。
3. 若上位机 peer cleanup API 实际方法与当前假设不一致，Engineer 必须以真实上位机 contract 为准修正文档和实现，但不能借机扩大到 relay/cloud。
4. 图传成功不等于控制安全放开；`safe_to_control`、`delivery_success`、`primary_actions_enabled` 仍必须保持 false。
5. 本轮不证明音频、录制、云 relay、真实远程运营网络质量，也不证明 ROS2、Nav2、底盘、雷达、建图链路完成。

## 交付给 Engineer 的一句话任务

在不放开任何运动控制的前提下，把 `Robot Control` 页现有 `preview_status=locked_no_webrtc_session` 替换成基于 existing upper API `/api/camera/offer` 的真实 WebRTC video preview，并补齐 `Start Preview`、`Stop Preview`、失败归因、peer cleanup 和真实 smoke evidence。

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 新增 `POST /api/robot-control/camera/offer?baseUrl=<robot-api-base-url>` 与 `POST /api/robot-control/camera/peers/:peerId/close?baseUrl=<robot-api-base-url>`。
  - 代理继续复用 Robot Control 既有 `baseUrl` 安全围栏：仅允许 HTTP、loopback/RFC1918、拒绝 credentials/query/hash，只允许固定 camera offer/close 路径。
  - offer/close 响应只回传 `schema/status/peer_id/answer/error` 安全摘要，并固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
  - 兼容真实上位机当前的顶层 `type/sdp/peer_id` answer contract，不再只接受设计稿里假设的嵌套 `answer`。
  - 对真实 answer SDP 只做最小 normalization：统一 CRLF 并确保末尾 `\r\n`，不改写媒体语义。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 导出 `normalizeRobotApiBaseUrl()`、`endpointUrl()`、`scanDangerousTrueFields()` 给 camera proxy 复用。
  - Robot Control summary 的 camera preview 默认状态改为 `idle_not_started`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlPreviewStatus`、camera offer/close proxy response contract。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `postRobotControlCameraOffer()`、`postRobotControlCameraPeerClose()`。
  - `POST` client 允许前端拿到 fail-closed error body，避免 UI 只看到通用 `returned 502`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 Camera Preview 卡片与 `<video>`。
  - `Start Preview` 仅在用户显式点击后创建 `RTCPeerConnection`，只申请 `recvonly video`，不申请 audio。
  - 展示 `preview_status`、`failure_reason`、`peer_id`、`ice_connection_state`、`video_track_state`、`last_offer_at`、`last_stop_at`、`cleanup_status`。
  - 重复 Start、Stop、切换 `baseUrl`、组件卸载前都先 cleanup 旧 peer，并记住会话自己的 `peer baseUrl`，避免切目标后把 close 打到新地址。
  - `Start Preview` 失败后最终状态保留 `start_failed`，不会被 cleanup 覆盖成 `stopped_by_user`。
  - 所有运动/控制入口保持 disabled。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 Camera Preview UI 测试，验证前端通过 workstation offer/close proxy 建立/停止 preview，且控制入口仍 locked。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 workstation camera offer/close proxy contract 测试，验证安全 URL 围栏、危险 true 字段 fail-closed、peer close 白名单。
  - 新增 answer SDP normalization 测试，验证 proxy 返回的 SDP 保留浏览器可解析的 CRLF 结尾。
- `pc-tools/README.md`
  - 补充 Camera Preview 的前端旅程、Node proxy 边界和 fail-closed 行为。
- `docs/product/pc_tools_workstation.md`
  - 同步产品文档：Camera Preview V1 已实现的接口、状态展示、安全边界、真实 smoke 证据与当前验证缺口。

## 验证结果

已执行：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
git diff --check
ssh root@192.168.1.11 -p 37878 'curl --max-time 8 -sS http://127.0.0.1:8787/api/camera/health; echo; curl --max-time 8 -sS http://127.0.0.1:8787/api/camera/devices; echo'
```

结果：

- `npm run build`：通过。
- `npm run test`：通过，`60 passed (60)`。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 真实上位机 smoke：
  - `/api/camera/health` 返回 `status=ready`、`active_peer_connections=0`、`active_peer_ids=[]`。
  - `/api/camera/devices` 返回 `/dev/video0`、`/dev/video1`、`/dev/video2`，`v4l2-ctl --list-devices` 可读。
  - 原始证据保存在 `artifacts/remote_camera_health_devices_2026-06-10.txt`。
  - 板端 `aiortc` self-test 通过上位机 `POST /api/camera/offer` 收到 `answer`，拿到真实 `640x480` 视频帧，并通过 `POST /api/camera/peers/{peer_id}/close` 将 `active_peer_connections` 从 `1` 回收到 `0`。
  - 原始证据保存在 `artifacts/remote_aiortc_offer_frame_close_2026-06-10.json`。
  - 有效 offer 经过 workstation proxy 后返回 `proxy_status=offer_forwarded`、`answer.type=answer`、`answer.sdp` 末尾保留 `\r\n`；原始证据保存在 `artifacts/proxy_offer_response_2026-06-10.json`。
  - 主会话重启本地 workstation API 后，用 Browser 打开真实 PC 页面，填入 `http://192.168.1.11:8787`，执行 `Start Preview -> Stop Preview`：
    - Start 后页面显示 `preview_status=streaming`、`failure_reason=none`、`ice_connection_state=connected`、`video_track_state=live`、`peer_id=7e90454a0dd54307bf40461e72842be6`。
    - Stop 后页面显示 `preview_status=stopped_by_user`、`failure_reason=none`、`peer_id=not_assigned`、`ice_connection_state=closed`、`video_track_state=stopped`、`cleanup_status=peer_closed:closed`。
    - Stop 后远端 `/api/camera/health` 返回 `active_peer_connections=0`、`active_peer_ids=[]`。
    - 页面级结构化证据保存在 `artifacts/browser_page_start_stop_smoke_2026-06-10.json`，截图保存在 `artifacts/browser_camera_preview_after_stop_2026-06-10.jpg`。

## 真实 smoke 证据

- 远端 camera health/devices 证据：
  - `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/remote_camera_health_devices_2026-06-10.txt`
- 远端 aiortc offer/frame/close 证据：
  - `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/remote_aiortc_offer_frame_close_2026-06-10.json`
- 有效 offer 的 workstation proxy 响应证据：
  - `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/proxy_offer_response_2026-06-10.json`
- 本地真实页面 Start/Stop 通过证据：
  - `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/browser_page_start_stop_smoke_2026-06-10.json`
  - `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/browser_camera_preview_after_stop_2026-06-10.jpg`
- 历史失败/阻塞说明，作为修复前证据保留：
  - `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/browser_smoke_blocker_2026-06-10.txt`

## 偏差 / 剩余风险

- 本轮完成了 Node proxy、Vue Preview 生命周期、类型、测试、板端 camera health/devices 真实 smoke、上位机媒体层首帧验证，以及 PC 页面级 `Start Preview -> streaming -> Stop Preview -> peer cleanup` Browser 复验。
- 主会话此前用 Browser 复跑的页面级 smoke 曾失败在 `setRemoteDescription(... Invalid SDP line a=setup:active)`；后续修复为保留 SDP 末尾换行和 CRLF normalization，并已用页面级复验确认不再复现。
- Browser 页面级复验中，页面状态机显示 `streaming`、ICE `connected`、video track `live`；远端媒体层 artifact 证明真实首帧为 `640x480`。Browser DOM 对 `<video>` 的 intrinsic `videoWidth/videoHeight` 读数仍为 `0`，因此截图/DOM 不单独作为帧尺寸证据，帧尺寸以远端 aiortc artifact 为准。
- 本轮仍不能宣称“完整图传 HIL + 运动控制全部完成”；当前只可宣称：
  - workstation Camera Preview V1 的软件实现已完成并通过本地 build/test/lint；
  - 上位机 `camera health/devices` 真实可读；
  - 上位机 `offer -> answer -> 首帧视频 -> peer cleanup` 真实跑通；
  - workstation proxy 对真实 answer 的页面消费兼容已修正并有 artifact；
  - PC 页面 `Start Preview -> streaming -> Stop Preview -> peer cleanup` 已用 Browser 复验；
  - 运动、底盘手控、`/cmd_vel`、Nav2 goal、雷达/建图 start 控制、delivery success 仍未开放也未证明。
