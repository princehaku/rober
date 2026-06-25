# PC 本轮进度总状态外框

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 09:05

## 实际改动

- 普通首屏 `本轮进度` 外层新增总状态 `data-state` 与状态 chip。
- 总状态只汇总已有四个收口目标：执行/确认/pending 时显示 `执行中`、`确认中`、`刷新中`，仍有缺口显示 `待处理`，四项全部完成或验证后才显示 `已完成`。
- 新增只作用于主 `plain-goal-progress` 面板的状态左侧线样式，避免影响扫图步骤和自动扫图准备列表。
- 补充前端测试，锁定默认首屏 `待处理`、送达确认 pending 时 `确认中`，以及对应 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该状态只消费页面已有只读状态，不自动刷新、不执行 Nav2、不确认送达、不发送 manual/keyboard pulse/stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|shows delivery confirmation pending on the map while final completion is in flight"`，2 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实底盘、真实 Nav2 行程、真实送达确认和真实键盘长按未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
