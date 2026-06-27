# 2026-06-28 21:00 PC 自由移动 Start Pending 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `free-roam/autonomy/start` 请求已发送但未返回时，普通首屏按钮从 `启动中` 改为 `请求中`。
  - 当前事实、扫图状态和地图 marker 都改为“启动请求已发送，等待上车端返回；返回前不把它当作已低速运行”。
  - 地图 marker 文案从 `自动扫图启动中` 收口为 `自动扫图请求中（等待返回）`，aria 明确“未确认低速运行”。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 start pending + stop queued 回归测试，锁定 pending 文案、地图 marker、aria 和 stop 可排队行为。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 free-roam start pending 的普通首屏 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "queues free-roam autonomy stop while the start request is still pending"`
  - 结果：1 个测试文件通过，1 个目标测试通过，198 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，347 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮验证范围是 PC 普通首屏 mock/单测链路，未向真实小车发送 free-roam、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel` 请求。
- 真实自由移动/自动扫图 start pending 和 stop queued 仍需要现场安全确认后做 HIL 验收。
