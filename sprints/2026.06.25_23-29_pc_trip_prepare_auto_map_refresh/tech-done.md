# PC 行程准备后自动刷新地图

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `准备行程（不发车）` 完成 Nav2 no-motion proof refresh 后自动调用地图预览刷新。
  - 当前 summary 带 `path_preview_points` 时，普通首屏地图会立刻显示路线、起终点和路线点数，执行按钮直接绑定图上终点。
- `pc-tools/workstation/test/App.test.ts`
  - 新增测试覆盖准备行程后 summary 出现路线点、地图自动刷新、路线变为可见、执行按钮放开。
  - 断言该流程不会调用 Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录行程准备后自动刷新地图的 WYSIWYG 口径和安全边界。

## 验证结果

- 通过：`npm test -- -t "refreshes the map automatically after plain trip preparation"`（1 passed，172 skipped）
- 通过：`npm run lint`
- 通过：`npm test`（173 passed）
- 通过：`npm run build`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`（`node` 监听 `*:7001`，未使用 Clash 端口）

## 剩余风险

- 本轮是 PC/mock 层验证，没有执行真实 Nav2 route 或真实底盘运动。
- 真实路线显示仍依赖上位机 summary 在准备行程后正确回读 `path_preview_points` 和地图预览可读。
