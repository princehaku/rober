# 2026-06-28 20:40 PC 地图记录启动 Pending 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自动扫图入口先补地图记录时，地图 marker 从泛化的“扫图记录启动中”改为 `地图记录启动中（不发车）`。
  - marker aria 同步写明“不发车”，避免把 map/start pending 窗口误看成小车已经低速运行。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 ready 传感器自动扫图回归测试，延迟 `map/start` 回包并断言 pending 期间没有调用 `free-roam/autonomy/start`。
  - 测试锁定 pending 期间的地图 marker、aria、自由移动提示和扫图状态文案，回包后再继续验证 `map/start -> free-roam/autonomy/start` 顺序。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 map/start pending 的普通首屏 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "starts map recording before auto sweep"`
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

- 本轮验证范围是 PC 普通首屏 mock/单测链路，未向真实小车发送 map/start、free-roam、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel` 请求。
- 真实建图启动和自动扫图 HIL 仍需要现场安全确认后单独验收。
