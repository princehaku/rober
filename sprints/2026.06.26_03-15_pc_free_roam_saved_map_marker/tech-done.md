# PC 扫图保存 Marker 新鲜度同步

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 扫地式建图保存成功后，如果本轮 map preview 已自动刷新，地图上的扫图流程 marker 从 `地图已保存` 升级为 `地图已保存，画面已刷新`。
  - marker aria 同步说明“地图画面已自动刷新，可以检查效果”；未刷新时仍保守显示 `地图已保存`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自由扫图保存流程用例，断言保存后卡片、地图画面、覆盖 guidance、步骤条和地图 marker 都同步显示自动刷新结果。
- `docs/product/pc_tools_workstation.md`
  - 同步记录保存后地图流程 marker 的 WYSIWYG 口径和控制边界。

## 验证结果

- 已通过：
  - `npm test -- -t "keeps free-roam keyboard locked until map recording starts"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 184 skipped (185)`。
  - `npm run lint`
  - 结果：ESLint 通过。
  - `npm run build`
  - 结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - `npm test`
  - 结果：`Test Files 2 passed (2)`，`Tests 185 passed (185)`。
  - `git diff --check`
  - 结果：通过，无 whitespace error。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：本机已有 `node` 监听 `*:7001`，未改 Clash 或系统代理配置。
- 首次尝试：
  - `npm test -- -t "guides free-roam mapping from safety confirmation through keyboard sweep and save"` 未匹配到用例，Vitest 输出 `Tests 185 skipped (185)`；已改用准确用例名重跑通过。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有连接真实上位机执行真实 map save 或读取真实 map preview。
- 该改动只同步地图 marker 文案，不改变 map save、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel` 的后端行为。
- 未触发真实 manual、keyboard pulse、Nav2 execute、delivery complete、stop 或 `/cmd_vel`；未修改 Clash 或系统代理配置。
