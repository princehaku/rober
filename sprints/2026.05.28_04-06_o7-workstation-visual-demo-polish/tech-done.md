# O7 workstation visual demo polish

sprint_type: micro

## 实际改动

- 将 `pc-tools/workstation` 默认首屏切到 `O7 Console`，并在 O7 面板顶部增加运营调试台式布局：状态栏、O7 六区概览、demo 轨迹地图、标注样本、ASR/TTS stub、手控/寻路 stub。
- 新增固定 demo archive fixture：`pc-tools/workstation/fixtures/o7/demo_archive.json`。
- 新增 `GET /api/o7/demo/archive`，只读取仓库内固定 fixture，并复用 `trashbot.o7.cloud_archive_tasks.v1` adapter 保持 fail-closed。
- 更新 `workstationApi`、App/O7 测试和 catalog 测试，覆盖 demo 数据被 UI/API 消费，以及 `safe_to_control=false`、`robot_control_executed=false`、`command_dispatch_enabled=false` 不被打开。
- 更新 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`，说明 demo mode、视觉改造和真实能力边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。输出包含 `✓ 31 modules transformed.`、`dist/index.html`、`dist/assets/index-DSs4AtiP.css`、`dist/assets/index-ChAbHAa8.js`、`✓ built in 2.14s`。
- `cd pc-tools/workstation && npm run test`：通过。输出 `Test Files  2 passed (2)`、`Tests  42 passed (42)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 lint error 输出。
- `rg -n "demo|O7|not_proven|safe_to_control=false|robot_control_executed=false|实时地图|电梯状态|历史路线回放|数据标注|ASR|TTS|手控|寻路" pc-tools docs sprints/2026.05.28_04-06_o7-workstation-visual-demo-polish`：通过，命中 O7/demo/fail-closed 文案。
- `git diff --check -- pc-tools docs sprints/2026.05.28_04-06_o7-workstation-visual-demo-polish`：通过，无 whitespace error。
- 本地 API smoke：`PORT=8799 npm run api` 后请求 `GET /api/o7/demo/archive`，返回 `{"schema":"trashbot.o7.cloud_archive_tasks.v1","status":"fixture_archive_ready","tasks":2,"selected":"demo-o7-task-002","safe_to_control":false,"robot_control_executed":false,"command_dispatch_enabled":false}`。

## 失败定位与修复

- 第一轮 `npm run build` / `npm run test` 失败于当前 WSL/Linux 环境缺少 npm optional native 包：`@rollup/rollup-linux-x64-gnu`，后续又暴露 `@esbuild/linux-x64` 缺失而只存在 Windows binary。原因是 `node_modules` 来自 Windows/macOS 平台依赖树，不是业务代码错误。
- `npm install` 在 `/mnt/e` WSL 挂载目录上长时间无输出卡住；已停止卡住进程。随后按 `package-lock.json` 中已声明版本，用 `npm pack` 补齐本机验证所需的 ignored `node_modules` native optional 包：`@rollup/rollup-linux-x64-gnu@4.60.4`、`@esbuild/linux-x64@0.28.0`、`@esbuild/linux-x64@0.27.7`，未改 `package.json` 或 `package-lock.json`。

## 剩余风险

- 当前仍是 PC-only 本地 demo/software proof；真实 O6 bearer API、真实 RTC/视频、真实 ASR/TTS、真实手控/Nav2、真实 robot ACK、真实 browser/手机和上车数据仍为 `not_proven`。
- demo 轨迹地图是本地 fixture 的视觉 smoke，不证明真实 ROS2 `/tf`、真实地图定位或 <2s 刷新延迟。
## 2026-05-28 500 修复追加

### 实际改动

- 修复 `GET http://127.0.0.1:5173/api/o7/demo/archive` 在只启动 Vite dev server 时依赖 8787 代理而返回 500/代理失败的问题。
- `pc-tools/workstation/vite.config.ts` 新增 `rober-workstation-api-dev` middleware，开发态直接复用 Express `createWorkstationApp()` 的 `/api/*` handler，非 API 请求继续交给 Vite。
- 同步更新 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`，说明 5173 dev API 与 fail-closed 边界。

### 验证结果

- `cd pc-tools/workstation && npm run build`：通过，`31 modules transformed`，`built in 963ms`。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`，`Tests 42 passed (42)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 lint error 输出。
- Vite dev smoke：启动 `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort` 后请求 `GET /api/o7/demo/archive` 返回 `status_code=200`、`schema=trashbot.o7.cloud_archive_tasks.v1`、`archive_status=fixture_archive_ready`、`selected_task_id=demo-o7-task-002`、`task_count=2`、`safe_to_control=False`、`robot_control_executed=False`、`command_dispatch_enabled=False`；验证后已清理 5173 后台进程。

### 剩余风险

- 当前修复仅覆盖 workstation Vite dev 与本地 Express API 合流，不证明真实 O6 bearer API、真实 RTC/视频、真实 ASR/TTS、真实手控/Nav2、真实 robot ACK、真实 browser/手机或上车数据。
- 5173 dev middleware 复用 Express handler；后续新增 `/api/*` 时仍需保持 fail-closed 字段和文档同步。
