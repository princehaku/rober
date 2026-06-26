# PC 保存后地图画面失败 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增保存后地图 preview 失败记忆，只在本轮 `map/save` 成功后的自动 preview 失败时触发。
  - 扫图卡片、扫图状态、覆盖提示、地图流程 marker 和下一步按钮同步显示“地图已保存，但最新画面刷新失败”。
  - 下一步焦点回到 `刷新扫图画面`，避免现场拿旧图检查覆盖效果。
- `pc-tools/workstation/src/styles.css`
  - 新增保存后 preview 失败的地图 marker 和覆盖面板失败态样式。
- `pc-tools/workstation/test/App.test.ts`
  - 新增保存成功但保存后 preview 失败的普通首屏用例，锁定 marker、caption、覆盖提示、焦点和禁止误发控制接口。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录保存后地图画面刷新失败的 WYSIWYG 契约。

## 验证结果

- `npm test -- -t "shows saved free-roam map preview refresh failures on the map|keeps free-roam keyboard locked until map recording starts"`：通过，2 passed。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 test files passed，197 tests passed。
- 完整测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免无关 diff。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不触发真实上位机建图保存，不证明真车地图保存质量或 `/api/map/preview` 可用性。
