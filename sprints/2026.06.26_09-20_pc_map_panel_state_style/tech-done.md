# PC 地图卡片外层状态

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 09:20

## 实际改动

- 普通首屏 `地图` 整张卡片新增 `plain-map-panel` 与外层 `data-state`。
- 新增地图卡片状态线样式：`地图可见` 为可见态，`地图处理中/地图待刷新` 为等待态，`地图未读取` 为中性态，`地图不可用` 为异常态。
- 补充前端测试，锁定默认地图可见和地图刷新处理中的外层状态，以及对应 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该状态只汇总已有地图视口 WYSIWYG 状态，不自动刷新地图、不开始/保存建图、不执行 Nav2、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 passed / 191 skipped。
- 通过：`npm test -- -t "blocks visible-route execution while the map preview is refreshing"`，1 passed / 191 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实地图刷新/建图保存、真实底盘、真实 Nav2、真实送达和真实键盘长按未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
