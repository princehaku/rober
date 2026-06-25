# PC 实时画面卡片外层状态

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 09:10

## 实际改动

- 普通首屏 `实时画面` 整张卡片新增 `plain-camera-panel`、`data-state` 与 `data-frame-state`。
- 新增卡片外层状态线样式：真实绘帧可见为可见态，连接/关闭/检查/等待为等待态，未打开为中性态，画面偏暗或失败为异常态。
- 补充前端测试，锁定默认未打开、真实视频帧可见、near-black 偏暗三种卡片外层状态，以及对应 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该状态只汇总已有画面框和浏览器绘帧结果，不自动打开相机、不调用 first-frame probe、Nav2、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|starts and stops Camera Preview through workstation camera proxy while keeping control locked|marks near-black preview as 画面偏暗 instead of optimistic 已打开"`，3 passed / 189 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实摄像头 WebRTC、真实底盘、真实 Nav2、真实送达和真实键盘长按未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
