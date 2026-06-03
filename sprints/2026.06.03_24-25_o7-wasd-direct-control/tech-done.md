# O7 WASD Direct Control Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
  - 为 PC direct-upper manual 代理增加独立 `5500ms` 远端 fetch timeout，避免上位机 `/api/base/manual` 的运动 pulse、auto-stop、`T=130` 和 `T=1001` 回读窗口被 status 的 `1200ms` 短超时提前 abort。
  - `GET /api/o7/direct-upper/status`、`POST stop`、`POST feedback-request` 仍保留 `1200ms` 短超时，首屏状态刷新不被 manual 慢窗口拖住。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - 增加键盘遥控：`W/S/A/D` 对应前进/后退/左转/右转，`Space` 和 `X` 对应 stop。
  - 忽略输入框、速度滑条、可编辑区域焦点和 repeat keydown，避免长按或编辑状态误触发连续点动。
  - `forward/back` 继续使用当前滑块速度和 `250ms`；`left/right` 使用更明显 turn pulse：`speed=0.08`、`duration_ms=350`；`stop` 使用 `speed=0`。
- `pc-tools/workstation/test/App.test.ts`
  - 补充按钮 payload 断言、WASD/Space/X 键盘断言、repeat/editable focus 忽略断言，以及 manual 代理可等待超过 `1200ms` 的回归测试。
- `docs/interfaces/o7_direct_upper_pc_api.md`
  - 同步 direct-upper timeout、manual 错误语义、WASD 和 turn pulse 合同。
- `docs/interfaces/o7_live_operator_panel.md`
  - 同步 PC 首屏手控行为、键盘焦点边界、timeout 文案和 fail-closed 展示要求。

## 用户旅程变化和触点收益

operator 在 PC 控制台可以直接用键盘点动：`W` 前进、`S` 后退、`A` 左转、`D` 右转、`Space/X` 停止。左右转从短 `250ms` 改成 `350ms` 且请求 `0.08m/s`，现场感知更明显；后退不需要重复点击等待本地代理超时，manual 代理会等待上位机 auto-stop 和反馈窗口。

所有操作结果仍明确展示 `ACK not observed`、`T=1001 not observed`、`safe_to_control=false`、`blocked_reasons` 和具体 `timeout`/HTTP/bad JSON 失败原因。页面不把 HTTP 200 包装成 HIL、ACK 或安全闭环。

## 接口影响

- `POST /api/o7/direct-upper/base/manual`
  - 请求体仍为 `direction`、`speed`、`duration_ms`。
  - PC 本机代理远端 timeout 调整为 `5500ms`。
  - 方向白名单、速度上限 `<=0.08m/s`、时长上限 `<=350ms` 和 fail-closed 响应不变。
- `GET /api/o7/direct-upper/status`
  - 仍使用 `1200ms` 短超时。
  - `request_timeout_ms` 仍表示 status 只读请求窗口，不代表 manual 远端窗口。
- 前端仍只调用 PC 同源 `/api/o7/direct-upper/base/manual`，浏览器不直连 8787、不 POST `/api/base/manual`、不发送 `/cmd_vel`、不构造 WAVE ROVER JSON。
- 首屏 camera offer 仍保持手动触发，未恢复自动 `/offer`。

## 前后端 / ROS2 联调结果

- 前端到 PC 后端：通过 Vitest mock fetch 覆盖按钮、WASD/Space/X 和 manual payload。
- PC 后端到上位机 8787：通过 fake fetch 覆盖 manual timeout 回归和 payload clamp；本轮未连接真实 8787。
- ROS2 / onboard 串口协议：本轮未修改 onboard、ROS2、WAVE ROVER 串口协议或 8787 上位机脚本。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run`
  - 结果：通过。
  - 日志片段：`Test Files  2 passed (2)`，`Tests  80 passed (80)`。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过。
  - 日志片段：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`，`✓ built in 2.00s`。
- `git diff --check -- pc-tools/workstation/src/server/o7DirectUpperApi.ts pc-tools/workstation/src/server/o7LiveOperatorPanel.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7LiveOperatorPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_direct_upper_pc_api.md docs/interfaces/o7_live_operator_panel.md sprints/2026.06.03_24-25_o7-wasd-direct-control/tech-done.md`
  - 结果：通过，无 whitespace error 输出。

## 失败定位与修复

- 首次 `npm test -- --run` 出现 1 个失败：WASD 测试里一次键盘事件触发了多个 manual 请求。
- 根因不是组件运行时重复注册，而是既有测试没有 unmount 先前 mounted wrapper；本轮新增 window 级 `keydown` listener 后，历史组件实例残留在测试环境里共同响应同一按键。
- 修复：`pc-tools/workstation/test/App.test.ts` 启用 `enableAutoUnmount(afterEach)`，让每个测试结束时卸载组件并触发 `onBeforeUnmount()` 清理 window listener。复跑完整测试通过。

## 剩余风险

- 本轮是 PC workstation 软件闭环，没有做真实 `/dev/ttyS5` 点动、真实 8787 `/api/base/manual`、HIL、robot ACK 或 `T=1001` 现场验收。
- `T=1001 observed/not observed` 仍只按当前 PC/上位机合同展示；未证明真实 ROS feedback topic、真实 `/odom`、`/imu/data`、`/battery` 或 delivery success。
- `safe_to_control=false` 仍是正确锁定状态；若要解锁，需机器人/硬件侧补齐现场净空、人工急停、stop/post-status、ACK/T=1001 和安全复位证据。

## OKR 最低优先级软提醒

当前最低 Objective 仍是 O1；本 micro sprint 属于 O7 触点修复，但直接服务 O1 现场 manual 点动证据采集入口，不提升 O1 HIL 或 `safe_to_control` 完成度。
