# PC Direct Upper API 收口

sprint_type: micro

## 实际改动

- PC workstation 已暴露 `GET /api/o7/direct-upper/status`、`POST /api/o7/direct-upper/base/stop`、`POST /api/o7/direct-upper/base/feedback-request`、`POST /api/o7/direct-upper/base/manual`。
- `status` 只读取 `ROBER_UPPER_API_BASE_URL` 指向的 8787 `/health` 和 `/api/status`，未配置时返回 `not_configured`，不会猜默认 LAN IP。
- `stop/feedback-request/manual` 只通过 PC Express 同源转发到 8787；`feedback-request` 是非运动 `T=130` 请求，`manual` 先做方向白名单、`speed<=0.08m/s`、`duration_ms<=350ms` 限制，再交给 8787 自身 guardrail。
- 默认首屏 `O7LiveOperatorPanel.vue` 已展示 `PC 本机 8787 接口`、direct upper 状态、`ROBER_UPPER_API_BASE_URL` 和本机 API path；现有方向按钮仍保持锁定，不会自动 POST manual 或 feedback-request。
- 文档已同步：
  - `docs/interfaces/o7_direct_upper_pc_api.md`
  - `docs/interfaces/o7_upper_robot_api.md`
  - `docs/product/pc_tools_workstation.md`

## 最小必要修复

- 接手时 `POST /api/o7/direct-upper/base/feedback-request` 已部分写入，但需要补齐 server route、shared contract、client helper、O7LiveOperatorPanel path 展示、tests、docs 和本 tech-done 风险口径。
- 第一轮验收复现到 `App.test.ts` 一个 `vi.fn(async (...) => ({ ... }))` 对象返回体内混入 `void _input;` 语句会触发 esbuild/TypeScript/ESLint 解析失败；当前文件已是 block body 写法并通过最终回归。
- `payloadSummary` 保持显式标注为共享 contract 类型，避免 TypeScript 将 `direction` 扩宽为普通 `string`；这是类型锚定修复，不改变运行时控制、clamp 或 fail-closed 行为。

## 验证结果

- `cd pc-tools/workstation && npm run test`
  - 最终结果：通过，2 个 test files，76 个 tests，duration 13.48s。
- `cd pc-tools/workstation && npm run build`
  - 最终结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `dist/index.html`、CSS、JS bundle。
- `cd pc-tools/workstation && npm run lint`
  - 最终结果：通过，ESLint 无 error 输出。
- `git diff --check -- pc-tools/workstation/src/server/o7DirectUpperApi.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/server/catalog.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7LiveOperatorPanel.vue pc-tools/workstation/src/styles.css pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_direct_upper_pc_api.md docs/interfaces/o7_upper_robot_api.md docs/product/pc_tools_workstation.md sprints/2026.06.03_10-11_pc-direct-upper-api/tech-done.md`
  - 最终结果：通过，无 whitespace error。

## 接口影响

- 新增 PC 本机 API path：
  - `GET /api/o7/direct-upper/status`
  - `POST /api/o7/direct-upper/base/stop`
  - `POST /api/o7/direct-upper/base/feedback-request`
  - `POST /api/o7/direct-upper/base/manual`
- 新增共享 contract：`O7DirectUpperApiStatusResponse`、`O7DirectUpperApiCommandResponse` 和 direct upper safety/request 类型。
- 不修改 `cloud-relay/**`、`onboard/**`、vendor 文件，也不改变生产 4G/cloud relay 路线。

## 用户旅程变化和触点收益

- 现场 PC operator 可在首屏看到 direct upper 是否已配置、8787 状态摘要和可复制的本机 API path。
- cloud relay 不再是 PC 现场调试 direct 8787 的必需路径，但 UI/API 仍明确这是 PC local direct mode，不是普通手机生产路径。
- 失败原因不隐藏：未配置 env、8787 HTTP 失败、坏 JSON、ACK/T=1001 未观察都会进入 fail-closed 字段或 blocked reasons。

## 前后端 / ROS2 联调结果

- 前端到 PC Express 的 direct status 调用已由 Vitest 覆盖。
- PC Express 到 8787 的 `/health`、`/api/status`、`/api/base/stop`、`/api/base/feedback-request`、`/api/base/manual` 行为已由 mocked fetch 覆盖。
- 本轮没有执行真实 ROS2、真实串口、真实 8787 motion、真实 robot ACK、真实 `T=1001` 或 HIL；所有响应继续固定 `safe_to_control=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`。

## Hardware 现场核对风险更新

- Hardware worker 核对到远端 8787 `GET /health` ready、`GET /api/status` ready。
- 真实 `POST /api/base/feedback-request` 当前返回 HTTP `405`，`Allow=OPTIONS`。
- 因此本轮 PC direct upper API 只能证明软件转发路径、shared contract、UI path 展示和 fail-closed 行为；不能宣称远端 feedback endpoint 已部署可用，不能宣称真实 `T=130 -> T=1001` 已闭环，不能宣称 ACK/HIL 通过。

## Product / OKR 收口

- 用户价值：现场 PC operator 现在能在本机看到 8787 direct upper 状态和可复制 API path，并能把 stop、feedback-request、manual 的调用入口固定到 PC workstation 的同源软件合同里，减少现场调试时散落脚本和口头路径带来的误操作风险。
- OKR 映射：本轮主要推进 O7 PC 端运营调试工具链；`feedback-request` 入口为 O1 下一步证据链服务，但没有形成 O1 硬件闭环证据。
- 进度判断：O1 保持约 94%，因为远端真实 `POST /api/base/feedback-request` 返回 HTTP `405`，没有证明 `T=130 -> T=1001`、robot ACK、HIL 或 `safe_to_control=true`。O7 可从约 98.5% 小幅调整到约 98.6%，理由仅是 PC 本机 direct upper API software contract ready、首屏 path visibility 完成、test/build/lint/diff-check 通过；production path、real control、ACK、HIL 仍 `not_proven`。
- 验证引用：Full-Stack 已完成 `npm run test` 2 files / 76 tests passed、`npm run build` passed、`npm run lint` passed、scoped `git diff --check` passed；Hardware 只读/非运动核对确认 8787 `/health` 与 `/api/status` ready，但 feedback-request POST 405。
- 风险边界：本轮不能把 PC direct `manual` 或 `feedback-request` 写成真实底盘控制、真实 `T=1001`、ACK、HIL、delivery success，也不能写成普通手机 production path；首屏按钮仍不自动调用 manual。

## 范围外 dirty 文件核对

本轮过程中曾观察到以下范围外 dirty 路径，它们不属于 direct-upper 收口范围，因此未修改、未回滚：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.06.03_10-11_okr-current-state-refresh/`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `sprints/2026.06.03_11-12_o1-lidar-real-scan-evidence/`

最终 `git status --porcelain=v1 --untracked-files=all` 未再显示上述范围外路径；当前 dirty 集合只包含本轮允许范围内的 direct-upper 文件和本 sprint `tech-done.md`。

## 剩余风险

- direct upper API 只证明 PC 本机软件层和 mocked 8787 contract；远端 `/health` 与 `/api/status` ready 不等于 feedback POST ready，且现场 `POST /api/base/feedback-request` 当前仍为 HTTP 405。
- 真实 8787 feedback endpoint 部署可用、真实底盘停止、真实点动、ACK、`T=1001`、ROS2 `/odom`/`/imu`/`/battery` 与 HIL 均未证明。
- PC `manual` 即使收到 8787 HTTP 200，也不能写成 robot ACK 或 HIL pass；需要后续受控现场材料按 O1 safe pulse acceptance 链路补齐。
