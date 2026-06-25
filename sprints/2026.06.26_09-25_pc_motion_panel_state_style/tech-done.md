# PC 移动导航卡片外层状态

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 09:25

## 实际改动

- 普通首屏 `移动/导航` 整张卡片新增 `plain-motion-panel` 与外层 `data-state`。
- 新增移动导航卡片状态线样式：完成态、等待/处理中态、中性待处理态、失败态。
- 补充前端测试，锁定默认 `待试动` 外层状态、共享安全确认后不自动触发请求且状态保持可读，以及对应 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该状态只汇总已有移动短状态，不自动勾选安全确认、不记录画面、不试动、不执行 Nav2、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|reuses one plain safety confirmation for trip, keyboard, and free-roam mapping"`，2 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实底盘、真实 first-jog、真实 Nav2、真实送达和真实键盘长按未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
