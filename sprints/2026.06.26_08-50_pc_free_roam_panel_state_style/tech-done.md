# PC 扫地式建图卡片状态外框

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 08:50

## 实际改动

- 普通首屏 `扫地式建图` 卡片将 `plainFreeRoamMappingSummary.state` 暴露为外层 `data-state`。
- 新增 `待确认/可开始/扫图中/保存中/刷新中/已保存/失败` 等扫图卡片状态外框样式，让扫图流程不只显示在地图 marker 和状态行里。
- 补充前端测试，锁定初始待确认、地图记录启动后的扫图中、保存 pending、保存后刷新、已保存状态与 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该改动只影响 PC 前端 WYSIWYG，不自动启动建图、不发送 manual/keyboard pulse、不执行 Nav2、delivery complete、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|keeps free-roam keyboard locked until map recording starts"`，2 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node` 正在监听 `*:7001`。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实扫地式建图、真实键盘长按、真实地图保存、真实底盘和真实 Nav2/delivery 未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
