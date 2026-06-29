# PC 地图 WYSIWYG 目标总览口径修正

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `mapWysiwygVisibleFromPlain()`，让目标总览按“地图画面本身是否可见”判断 `map_wysiwyg`，并兼容 live 文案“地图画面、图上路线、小车位置和雷达标记都已按当前读数显示”。
- `pc-tools/workstation/test/catalog.test.ts`：补回归断言，确保上述 live 文案会让 `action_status_cards[].id=map_preview` 显示 visible，并让 `goal_checklist[].id=map_wysiwyg` 标为 done。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`：同步说明地图画面、路线执行、雷达贴图三类目标的责任边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/catalog.test.ts`：通过，168 tests OK。
- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm test -- test/App.test.ts`：通过，218 tests OK。

## 剩余风险

- 本轮只修正只读 summary 目标总览口径，不刷新地图、不启动雷达、不执行 Nav2、不发送 keyboard/manual/free-roam/delivery/stop 或 `/cmd_vel`。
- live 目标仍未完成：相机首帧未显示、完整路线执行还需要现场安全确认后重跑并证明 wheel raw L/R 非零、建图启动仍缺相机首帧。
- 当前工作区已有两份历史 DOM smoke artifact 是改动状态，本轮未触碰、未提交。
