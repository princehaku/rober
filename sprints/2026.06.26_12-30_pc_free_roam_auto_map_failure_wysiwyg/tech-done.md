# PC 自动扫图地图刷新失败 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增自动扫图会话地图 preview 刷新失败状态。
  - 自动扫图 start 已转发后，如果自动地图 preview refresh 失败，扫图状态行显示 `自动扫图状态机已启动，但地图画面刷新失败`。
  - 地图扫图流程 marker 同步显示 `自动扫图已启动，地图刷新失败：<原因>`，不再继续显示普通 `自动扫图已启动`。
- `pc-tools/workstation/src/styles.css`
  - 新增 `auto_map_failed` 地图扫图 marker 失败视觉态。
- `pc-tools/workstation/test/App.test.ts`
  - 新增自动扫图 start 后地图 preview refresh 失败用例，锁定 marker、扫图状态、readiness hint、地图画面失败文案和不误发控制接口。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 2026-06-26 12:30 起自动扫图地图刷新失败的 WYSIWYG 契约。

## 验证结果

- `npm test -- -t "shows free-roam autonomy map preview refresh failures on the map|shows free-roam autonomy radar refresh failures on the map|starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`：通过，3 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 输出 chunk size warning，但构建成功。
- `npm test`：通过，2 test files passed，199 tests passed。
- 完整测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免无关 diff。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不触发真实自动扫图，也不证明真实地图 preview 或覆盖变化 HIL。
