# PC 自由移动启动 Pending 未证明口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自由移动/自动扫图 start 请求 pending 时，当前事实、自由移动/扫图状态和地图 marker aria 统一显示“启动请求已发送，等待上车端返回；返回前未证明已启动或已低速运行”。
  - 保留红色停止可点击和 start 返回后自动 stop 排队逻辑，不改变自由移动、建图、键盘、Nav2 或底盘命令路径。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 `queues free-roam autonomy stop while the start request is still pending`，锁定当前事实、扫图状态、地图 marker 和 stop 排队行为。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自由移动/自动扫图 start pending 的未证明口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "queues free-roam autonomy stop while the start request is still pending"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 199 skipped (200)`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 348 passed (348)`
- 通过：`npm run lint`
  - `eslint .`
- 通过：`npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建通过。
- 通过：`git diff --check`

## 剩余风险

- 本轮没有连接真实小车，也没有发送真实 free-roam、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`；仅验证 PC 前端 pending 状态呈现和 mock API 行为。
- 工作区已有两个旧 artifact JSON 文件处于 modified，本轮不修改、不提交。
