# O7 PC Direct Manual Control Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/client/workstationApi.ts` 新增 `postO7DirectUpperManual()` client helper，只调用 PC 同源 `/api/o7/direct-upper/base/manual`，并保留 400/502 JSON payload 里的失败原因。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue` 将 `前进`、`后退`、`左转`、`右转`、`Stop` 从本地 `showLocked()` 改为发送 direct-upper manual 请求；UI 展示发送中、已发送、失败、ACK/T=1001 状态、锁定原因和 `safe_to_control=false`。
- `pc-tools/workstation/test/App.test.ts` 更新首屏按钮回归测试，覆盖五个方向按钮都 POST 同源 manual 代理，并确认浏览器不直连 `/api/base/manual`、`/cmd_vel` 或 WAVE ROVER 控制字符串。
- `docs/interfaces/o7_direct_upper_pc_api.md` 和 `docs/interfaces/o7_live_operator_panel.md` 同步按钮行为、错误展示和安全边界。

## 用户旅程变化

用户在 PC 控制台点击方向键后，不再只看到固定“已拦截”。现在会看到该方向是否已通过 PC direct-upper manual 代理发出、上位机请求 HTTP 状态、失败原因、`ACK not observed` / `T=1001 not observed` 和当前锁定原因。这样 operator 可以区分 env 未配置、PC 后端 400/502、8787 不可达、坏 JSON 和“已转发但仍未闭环确认”。

## 接口影响

- 浏览器新增使用既有 PC 后端同源 endpoint：`POST /api/o7/direct-upper/base/manual`。
- 请求体为 `direction`、`speed`、`duration_ms=250`；PC 后端仍负责方向白名单、速度/时长限幅和 8787 转发。
- 未新增浏览器直连上位机 8787 路径，未调用 `/api/base/manual`、`/cmd_vel` 或 WAVE ROVER JSON。
- `GET /api/o7/live-operator-panel` 仍是只读展示合同，`safe_to_control=false` 边界不变。

## 验证结果

已在 `/mnt/e/rober/pc-tools/workstation` 执行：

- `npm test -- --run`
  - 结果：通过。
  - 日志片段：`Test Files  2 passed (2)`，`Tests  76 passed (76)`。
- `npm run build`
  - 结果：通过。
  - 日志片段：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`，`✓ built in 2.05s`。

## 剩余风险

- 本轮只完成 PC workstation 前端到 PC direct-upper manual 代理的软件链路，不证明真实 robot ACK、真实 `T=1001` 闭环、HIL pass、真实运动安全或 delivery success。
- 若 `ROBER_UPPER_API_BASE_URL` 未配置或 8787 `/api/base/manual` 返回失败，UI 会显示失败原因，但不会绕过后端 guardrail。
- 机器人侧仍需在现场看护、物理净空和人工急停条件下由硬件/机器人侧补齐真实点动、stop、post-status、ACK/T=1001 和安全复位证据。

## OKR 最低优先级软提醒

当前最低 Objective 仍是 O1；本 micro sprint 主攻 O7 触点，但直接服务 O1 底盘 manual 受控灰度验收的 operator 入口，不提升 HIL 或 `safe_to_control` 口径。

## 本轮补充：摄像头 offer 409 首屏降噪

### 实际改动

- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue` 将首屏摄像头行为改为只读 `GET /api/o7/local-webrtc-camera` 状态，不再在 camera ready 后自动调用 `POST /api/o7/local-webrtc-camera/offer`。
- `O7LiveOperatorPanel.vue` 保留“重新连接预览”按钮；只有 operator 点击后才创建 recvonly WebRTC offer。offer 返回 HTTP 409 时，UI 显示“摄像头已有预览连接，关闭其他页面或稍后再点重新连接预览”，不把 peer conflict 隐藏成通用失败。
- `pc-tools/workstation/test/App.test.ts` 增加首屏不自动 offer、点击后才 offer、offer 409 可读提示的回归测试，并保留方向按钮走 `/api/o7/direct-upper/base/manual` 的覆盖。
- `docs/interfaces/o7_live_operator_panel.md` 同步首屏只读、手动预览、409 peer conflict 和方向按钮互不影响的接口/验收说明。

### 用户旅程变化

operator 打开 PC 控制台时，页面先展示 camera ready/等待服务状态，不再自动抢占上位机 camera peer。已有 active peer 或多个 QA 页面并发时，首屏不会自动产生 `/offer` 409 噪声；需要画面时点击“重新连接预览”即可手动连接。若此时仍有 peer conflict，页面给出可恢复提示，不影响方向按钮继续显示“发送中/已发送（仍锁定）/失败原因”的 direct-upper manual 状态。

### 接口影响

- `GET /api/o7/live-operator-panel` 仍为只读合同，未新增字段，`safe_to_control=false` 边界不变。
- `GET /api/o7/local-webrtc-camera` 仍只读 camera health/devices 摘要。
- `POST /api/o7/local-webrtc-camera/offer` 调用时机从首屏自动改为 operator 点击“重新连接预览”。
- `POST /api/o7/direct-upper/base/manual` 方向按钮路径不变，本轮没有改 onboard、upper API 或其他后端接口。

### 验证结果

已在 `/mnt/e/rober/pc-tools/workstation` 执行：

- `npm test -- --run`
  - 结果：通过。
  - 日志片段：`Test Files  2 passed (2)`，`Tests  78 passed (78)`。
- `npm run build`
  - 结果：通过。
  - 日志片段：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`，`✓ built in 1.99s`。

### 剩余风险

- 本轮没有连接真实 8088 camera 服务或复跑浏览器 rendered QA；验证证据来自组件回归测试和生产构建。
- 用户手动点击“重新连接预览”时，如果远端服务仍返回 409，浏览器 Network/DevTools 仍可能记录该手动请求的 HTTP 409；本轮核心修复是避免首屏自动 409，并把手动 conflict 变成可读恢复提示。
- 方向按钮仍只是 PC direct-upper manual 软件入口，不证明真实 robot ACK、真实 `T=1001`、HIL、真实运动安全或 delivery success。

## 本轮收口复核（2026-06-04）

### 审查结论

- 现有 dirty diff 已把方向按钮从本地 locked 文案推进到 PC 同源 `/api/o7/direct-upper/base/manual`，同时保留 `ACK not observed`、`T=1001 not observed`、`safe_to_control=false` 和锁定原因展示，没有把 HTTP 200 误写成 HIL/ACK/安全可控。
- camera 首屏已改为只读 health/devices 摘要，不再自动 POST `/api/o7/local-webrtc-camera/offer`；HTTP 409 peer conflict 只在 operator 显式点击“重新连接预览”后出现，并显示可恢复提示。
- 浏览器仍只调用 PC 同源 API；没有浏览器直连 8787，没有发送 `/cmd_vel`，没有构造或发送 WAVE ROVER JSON，真实运动/HIL/ACK 仍由机器人侧和硬件侧补证。

### Fresh 验证结果

- `cd pc-tools/workstation && npm test -- --run`
  - 结果：通过。
  - 日志片段：`Test Files  2 passed (2)`，`Tests  78 passed (78)`。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过。
  - 日志片段：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`，`✓ built in 3.26s`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过。
  - 日志片段：`eslint .`，退出码 `0`。
- `git diff --check -- pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7LiveOperatorPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_direct_upper_pc_api.md docs/interfaces/o7_live_operator_panel.md sprints/2026.06.03_23-24_o7-pc-direct-manual-control/tech-done.md`
  - 结果：通过，无 whitespace error 输出。

### 收口风险

- 本轮没有触碰 `onboard/scripts/upper_robot_api.py`、`docs/interfaces/o7_upper_robot_api.md` 或硬件文档；远端 8787 `/api/base/manual` 的真实安全执行、stop/post-status、ACK/T=1001、现场急停和 HIL 仍由 Hardware/Robot 侧补齐。
- 未启动浏览器 rendered QA 或真实 8088 camera；当前 camera 降噪证据来自 Vitest 组件行为、TypeScript build 和 lint。
