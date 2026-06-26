# PC 自动扫图停止后刷新门禁

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自动扫图 stop 请求转发成功后，清空本轮扫图地图 preview fresh 标记。
  - 地图流程 marker 区分 `自动扫图已停止，待刷新` 与 `自动扫图已停止，可保存`，避免把旧图当成停止后的新图。
  - 下一步流程在停止后优先回到 `刷新扫图画面`，刷新成功后才允许保存地图。
- `pc-tools/workstation/src/styles.css`
  - 新增自动扫图停止待刷新 / 已刷新可保存的 marker 状态样式映射。
- `pc-tools/workstation/test/App.test.ts`
  - 更新自动扫图 start/stop 和 start-pending stop 排队用例，锁定停止后必须刷新地图画面再保存。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 2026-06-26 12:00 起自动扫图 stop 后刷新门禁的 WYSIWYG 契约。

## 验证结果

- `npm test -- -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation|queues free-roam autonomy stop while the start request is still pending"`：通过，2 passed。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 test files passed，197 tests passed。
- 完整测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免无关 diff。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不触发真实自动扫图、不验证真实 stop 后地图覆盖变化。
