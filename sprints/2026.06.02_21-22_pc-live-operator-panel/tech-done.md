# O7 PC Live Operator Panel Tech Done

## Sprint Type

sprint_type: micro

## Actual Changes

- Added `GET /api/o7/live-operator-panel` with schema `trashbot.o7.live_operator_panel.v1`.
- Added O7 first-screen `PC Live Operator` UI for LiDAR/Radar status, camera entry, direction buttons and speed display.
- Kept all control paths fail-closed: `safe_to_control=false`, `sends_commands=false`, `robot_control_executed=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Direction buttons only update local blocked copy and do not call any control API.
- Added interface documentation in `docs/interfaces/o7_live_operator_panel.md` and product boundary update in `docs/product/pc_tools_workstation.md`.

## Upper Computer Facts

- SSH target: `root@192.168.1.11 -p 37878`.
- Camera service fact carried into the contract: `http://192.168.1.11:8088/`, current `health_status=not_listening_observed`, historical `video_source=/dev/video1`.
- Workstation API fact carried into the contract: `8787=not_listening_observed`.
- LiDAR/Radar remains blocked: `/dev/lidar=missing`, STC by-id identity unresolved, scan not proven, no fabricated point cloud.

## Deployment Result

- 8787 deployment is not claimed in this sprint note.
- Final SSH readonly check reached the host, but `ss -ltnp` showed no 8088/8787 listeners and `curl http://127.0.0.1:8088/health` returned connection refused.
- No long-running deployment was attempted in this收口 pass.

## Verification

Final收口 commands:

```bash
cd pc-tools/workstation && npm run test
# Test Files  2 passed (2)
# Tests  65 passed (65)

cd pc-tools/workstation && npm run build
# vite build: 37 modules transformed
# built successfully

cd pc-tools/workstation && npm run lint
# passed, no lint errors

git diff --check -- pc-tools/workstation/src/App.vue pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/server/catalog.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/server/o7LiveOperatorPanel.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7LiveOperatorPanel.vue pc-tools/workstation/src/styles.css pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_live_operator_panel.md docs/product/pc_tools_workstation.md sprints/2026.06.02_21-22_pc-live-operator-panel/tech-done.md
# passed, no whitespace errors
```

Rendered smoke:

- Page contains `PC Live Operator`.
- Page contains `LiDAR / Radar Signal`.
- Page contains `Forward`.
- Page contains `Stop`.
- Forward click only shows blocked copy and does not add a new `fetch` call.

SSH readonly check:

```bash
timeout 12 ssh -o BatchMode=yes -o ConnectTimeout=6 -p 37878 root@192.168.1.11 'uname -a; ss -ltnp | grep -E "8088|8787" || true; curl -fsS http://127.0.0.1:8088/health | head -c 500'
```

- Host reachable: `Linux op-z3-b6.home 6.1.31-sun50iw9 ... aarch64`.
- `8088` and `8787` were not listening in `ss -ltnp`.
- `curl http://127.0.0.1:8088/health` failed with connection refused.

## OKR Impact

- O7 should not be raised; keep it at about 97% because the PC panel is locally verified but the remote 8088/8787 services are offline.

## Remaining Risks

- `base_serial_identity_not_proven`
- `t1001_feedback_not_observed`
- `robot_ack_not_connected`
- Real LiDAR `/scan`, WAVE ROVER UART feedback, robot ACK, Nav2/ROS2 control and delivery success are not proven.

## 2026-06-03 User Console Reskin

本轮按 CEO 反馈把 PC 默认首屏从工程 proof 工作台收敛为普通用户可用的 `Rober 控制台`。`App.vue` 默认只拉 `GET /api/o7/live-operator-panel`，首屏不再渲染 Real Material Acceptance、External Probe Artifact、O7 六区概览、ASR/TTS、cloud 或 proof 大段字段。

实际改动：

- `pc-tools/workstation/src/App.vue`：默认入口改为简洁用户控制台，只保留刷新、错误提示和 O7 live panel。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`：重构为 `预览`、`地图`、`操控`、`状态` 四块；摄像头健康先读取 `GET /api/o7/local-webrtc-camera`，ready 后通过同源 `POST /api/o7/local-webrtc-camera/offer` 创建 recvonly 摄像头媒体预览，并在重连/卸载时 close peer；该 `/offer` 只属于 camera media，不是控制链路。地图明确 `雷达未接入 / 等待建图`；方向按钮只显示 `控制锁定：底盘串口/反馈/ACK 未确认`，工程 blocked reasons 仅放在 `详情`。
- `pc-tools/workstation/src/styles.css`：新增用户控制台视觉样式、状态灯、遥控器布局和移动端单列布局。
- `pc-tools/workstation/test/App.test.ts`：更新为用户化首屏、摄像头 media offer 和锁定交互测试，断言默认只调用 O7 live/operator、local camera status 与 camera offer；方向按钮点击不增加 fetch 调用。
- `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_live_operator_panel.md`：同步默认首屏、API 数据源和 fail-closed 行为边界。

验证结果：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
# vitest: Test Files 2 passed (2), Tests 60 passed (60)
# vite build: 14 modules transformed, built successfully
# eslint: exited 0, no lint errors
```

Playwright smoke：

- URL：`http://127.0.0.1:5173/`
- 可见：`Rober 控制台`、`预览`、`地图`、`操控`、`状态`、`前进`、`Stop`
- 点击 `前进` 后出现 `已拦截` / `控制锁定` 用户提示
- 首屏未出现：`External Probe Artifact`、`Real Material Acceptance`、`ASR/TTS`
- console errors：0
- 截图：`/tmp/rober-user-console.png`

剩余风险：

- 真实 LiDAR `/scan` 仍未证明，地图只允许占位展示。
- 底盘串口身份、`T=1001` feedback 和 robot ACK 仍未确认，所有操控保持 fail-closed。
- 本轮不处理云中转、O5/O6、真实远端 8088/8787 持久化。

## 2026-06-03 WAVE ROVER 控制口现场修正

本轮 CEO 在上位机现场验证后，修正底盘串口判断：

- 误判候选：`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0`。该口 sysfs 为 `STC USB Serial`，且本地 LiDAR vendor 规则也使用 `34bf/ff0a`，不能作为 WAVE ROVER 底盘口解锁证据。
- 实测控制口：`/dev/ttyS5 @115200`。
- 现场可控命令：

```bash
stty -F /dev/ttyS5 115200 raw -echo -crtscts
printf '{"T":1,"L":0.08,"R":0.08}\n' > /dev/ttyS5
```

CEO 确认上述命令可以让设备响应。Codex 随后执行安全停车：

```bash
stty -F /dev/ttyS5 115200 raw -echo -crtscts
printf '{"T":1,"L":0,"R":0}\n' > /dev/ttyS5
# stop_sent_ttyS5
```

无运动反馈验证：

```bash
ssh -p 37878 root@192.168.1.11 \
  'python3 -s - --once-json --request-base-feedback --port /dev/ttyS5 --baudrate 115200 --read-timeout-s 4' \
  < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

关键结果：

- `serial_opened=true`
- `feedback_request.sent=true`
- `sends_motion_commands=false`
- `read_line_count=0`
- `observed_feedback_types=[]`
- `t1001_feedback_status=not_observed_after_t130`

文档同步：

- `docs/interfaces/o7_live_operator_panel.md`：记录 `/dev/ttyS5` 为当前实测写入口，PC live endpoint 仍只读。
- `docs/interfaces/o7_realtime_hardware_sources.md`：补充底盘串口现场联调分层结论。

当前判断：

- “能跑起来”的根因是：实际底盘写入口在 `/dev/ttyS5`，之前 PC 安全锁盯着 `/dev/ttyACM0`，所以一直显示 `base_serial_identity_not_proven`。
- PC UI 仍不能直接解除全部安全锁，因为 `/dev/ttyS5` 上还没有读到 `T=1001` feedback，robot ACK 也未接入。
- 下一步如果要做 PC 按钮真实控制，需要新增独立控制 API：固定 `/dev/ttyS5 @115200`、低速点动、每次命令自动发送 `{"T":1,"L":0,"R":0}` 停车、并保留反馈/ACK 未闭环状态。

## 2026-06-03 PC 首屏直接摄像头预览

按 CEO 反馈，`http://192.168.1.11:8088/` 已有摄像头服务后，PC 首屏 `预览` 区不再只给“打开摄像头页面”按钮，而是在 `O7LiveOperatorPanel.vue` 内直接创建 recvonly WebRTC 连接：

- 首屏仍先调用 `GET /api/o7/local-webrtc-camera` 读取上位机 `/health` 与 `/devices`。
- 当 camera status 为 `ready` 时，浏览器创建 `RTCPeerConnection({ iceServers: [] })`，添加 `video recvonly` transceiver，等待 ICE gathering complete 后 POST 本机同源 `POST /api/o7/local-webrtc-camera/offer`。
- PC 后端把该 offer 转发到 `http://192.168.1.11:8088/offer`；这么做是因为浏览器从 `http://127.0.0.1:5173` 直接 POST 远端 8088 会被 CORS preflight 拦截。
- 收到 answer 后把 remote track 挂到预览区 `<video autoplay playsinline muted>`。
- 记录远端 `peer_id` 后，在组件卸载、重连或失败时 POST `/peers/{peer_id}/close` 清理远端 active peer。
- 保留“重新连接预览”和“打开摄像头页面”两个操作；前者只重建摄像头 WebRTC，后者打开远端原生页面。
- 该 `/offer` 只属于摄像头媒体预览，不是 PC API 控制能力；操控按钮仍保持 locked，不发送底盘命令。

实际改动：

- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`：新增 WebRTC 预览、远端 peer cleanup、重连按钮和播放状态文案。
- `pc-tools/workstation/src/server/o7LocalWebrtcCamera.ts`、`pc-tools/workstation/src/server/index.ts`：新增同源 `/offer` 与 peer close 代理，只转发摄像头 WebRTC 信令，不发送底盘控制。
- `pc-tools/workstation/src/styles.css`：新增内嵌 video、连接状态和 camera action 样式。
- `pc-tools/workstation/test/App.test.ts`：增加 WebRTC mock，验证首屏会 POST `/offer`，且方向按钮仍不新增控制请求。
- `docs/interfaces/o7_live_operator_panel.md`、`docs/product/pc_tools_workstation.md`：同步“前端直接预览、后端合同仍只读”的边界。

验证结果：

```bash
cd pc-tools/workstation && npx vitest run test/App.test.ts
# Test Files 1 passed (1), Tests 2 passed (2)

cd pc-tools/workstation && npm run build
# vite build: 14 modules transformed, built successfully
```

浏览器实际验证：

```bash
ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088 npm run dev -- --host 127.0.0.1 --port 5173
node --input-type=module <playwright_camera_preview_check>
```

- URL：`http://127.0.0.1:5173/`
- console errors：0
- `<video>` 存在：`hasVideo=true`
- 首帧尺寸：`videoWidth=640`、`videoHeight=480`
- 播放状态：`readyState=4`、`srcObject=true`
- 页面文案：`摄像头画面已连接`
- 截图：`/tmp/rober-camera-preview.png`

远端 peer cleanup 验证：

```bash
curl -fsS http://192.168.1.11:8088/health
# active_peer_connections=0
# active_peer_ids=[]
# last_closed_frames_read=617
```

剩余风险：

- 全量 `npm run test` 当前另有 `catalog.test.ts` 的 O7 camera systemd readiness 旧期望失败，和本轮 WebRTC 首屏预览不是同一问题。
- 摄像头预览已接入，但底盘控制仍保持 locked；`T=1001` feedback 和 robot ACK 未闭环前，PC 按钮不能直接下发运动。

## 2026-06-03 上位机统一 API 合并

按 CEO 反馈，PC 端不能长期分别猜摄像头 8088、雷达设备和底盘串口，因此新增上位机统一 API：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/upper_robot_api.sh`
- `onboard/scripts/install_upper_robot_api_service.sh`
- `onboard/systemd/trashbot-upper-robot-api.service`
- `docs/interfaces/o7_upper_robot_api.md`

统一入口：

```text
http://192.168.1.11:8787
```

上位机 endpoints：

- `GET /health`
- `GET /api/status`
- `GET /api/camera/health`
- `GET /api/camera/devices`
- `POST /api/camera/offer`
- `POST /api/camera/peers/{peer_id}/close`
- `GET /api/radar/status`
- `GET /api/base/status`
- `POST /api/base/stop`
- `POST /api/base/manual`

部署结果：

```bash
cd /root/rober
bash onboard/scripts/install_upper_robot_api_service.sh --repo-root /root/rober
# Active: active (running)
# Main PID: 23071
# Exec: upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5
```

远端验证：

```bash
curl -fsS http://192.168.1.11:8787/health
# status=ready

curl -fsS http://192.168.1.11:8787/api/status
# camera.status=ready
# radar.scan_status=not_proven
# base.port=/dev/ttyS5
# base.write_control_available=true
# base.feedback_ack.t1001_observed=false
```

PC 改动：

- `pc-tools/workstation/src/server/o7LocalWebrtcCamera.ts`：优先读取 `ROBER_UPPER_API_BASE_URL`。存在该变量时，PC camera bridge 会访问统一 API 的 `/api/camera/health`、`/api/camera/devices`、`/api/camera/offer` 和 `/api/camera/peers/{peer_id}/close`。
- `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL` 保留为旧 8088 fallback。

PC 验证：

```bash
TMPDIR=/tmp ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npx tsx -e '<buildO7LocalWebrtcCamera smoke>'
# status=ready
# base_url=http://192.168.1.11:8787
# health_http_status=200
# devices_http_status=200

TMPDIR=/tmp ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run dev -- --host 127.0.0.1 --port 5173
```

浏览器验证：

- URL：`http://127.0.0.1:5173/`
- console errors：0
- `<video>` 存在：`hasVideo=true`
- 首帧尺寸：`videoWidth=640`、`videoHeight=480`
- 播放状态：`readyState=4`、`srcObject=true`
- 页面文案：`摄像头画面已连接`
- 截图：`/tmp/rober-upper-api-camera-preview.png`

远端 peer cleanup：

```bash
curl -fsS http://192.168.1.11:8088/health
# active_peer_connections=0
# active_peer_ids=[]
# last_closed_frames_read=631
```

安全边界：

- camera `/offer` 只用于媒体预览，不发送底盘控制。
- radar 只返回设备/scan 状态，`scan_status=not_proven` 时不得伪造地图点云。
- base `/api/base/manual` 虽可写 `/dev/ttyS5`，但只允许低速点动并自动停车；`T=1001` feedback 和 robot ACK 仍未闭环，所以 PC 首屏操控按钮继续 locked。

## 2026-06-03 最终渲染 Smoke Cleanup

本轮只做验证 cleanup，不新增功能、不修改代码、不触碰 O1 串口、WAVE ROVER、`T=130/T=1/T=13/T=131`、`/cmd_vel`、ROS2/Nav2 控制路径。

文档口径复查：

按本轮指定 grep 复查旧禁止 offer 文案，三个允许文件均无命中。结论：允许首屏自动创建摄像头 WebRTC 媒体预览的口径已经同步；该 `/offer` 仍只属于 camera media session，控制链路保持 fail-closed。

渲染 smoke：

```bash
cd pc-tools/workstation
ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/ npm run dev -- --host 127.0.0.1 --port 5173
node --input-type=module <playwright_first_screen_smoke>
```

结果：

- URL：`http://127.0.0.1:5173/`
- 首屏文字：可见 `Rober 控制台`、`预览`、`地图`、`操控`、`状态`。
- 媒体信令：首屏确实发起 `POST /api/o7/local-webrtc-camera/offer` 1 次。
- offer 结果：HTTP `409 Conflict`。只读复查远端 `http://192.168.1.11:8088/health` 显示 `status=ready`，但 `active_peer_connections=1`，因此本次新 offer 被远端并发/清理状态拦截。
- `<video>`：元素存在，布局尺寸约 `576x320`；但因 offer 409，`srcObject=false`、`readyState=0`、`videoWidth=0`、`videoHeight=0`，本次没有首帧迹象。
- console errors：1，内容为 offer 409 resource error。
- page errors：0。
- 截图：`/tmp/rober-o7-first-screen-smoke.png`。
- 点击 `前进`：页面出现 `控制锁定` / `已拦截` 类提示，请求数未增加。
- 控制请求：点击后没有新增任何 API 请求；未观察到 `/cmd_vel`、WAVE ROVER JSON、`/robots/*`、控制 API、ROS2/Nav2 或运动命令请求。

收尾：

```bash
lsof -iTCP:5173 -sTCP:LISTEN -n -P || true
# no listener

git diff --check -- docs/interfaces/o7_live_operator_panel.md docs/product/pc_tools_workstation.md sprints/2026.06.02_21-22_pc-live-operator-panel/tech-done.md
# passed
```

剩余风险：

- 本次首屏媒体预览没有拿到首帧，阻塞点是远端 8088 已有 active peer 导致新 offer 返回 409；需要 camera service peer cleanup 或重新跑一次独占浏览器 smoke 后再确认首帧。

## 2026-06-03 Product Closeout

- OKR 映射：Objective 7。
- 方向判断：继续。
- 进度口径：保持约 97.5%。首屏已经是普通用户可读 `Rober 控制台`，并会直接尝试摄像头 WebRTC 媒体预览；但最新 smoke 因远端 `active_peer_connections=1` 返回 `409 Conflict`，video 无首帧，所以不能继续上调。
- 验收边界：`POST /api/o7/local-webrtc-camera/offer` 只用于摄像头媒体预览，不是控制链路；点击前进没有新增请求，方向按钮仍 fail-closed。
- 剩余风险：首屏首帧成功、生产视频链路、真实控制、robot ACK、手控/Nav2、弱网、云 relay/TURN/auth、phone/browser production path 和完整上车闭环仍 `not_proven`。
- 该风险只影响 camera media preview，不改变控制边界；底盘控制仍保持 fail-closed，`T=1001` feedback 和 robot ACK 未闭环前不能解锁 PC 手控。
