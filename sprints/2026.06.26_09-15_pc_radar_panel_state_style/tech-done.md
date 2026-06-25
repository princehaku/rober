# PC 雷达卡片外层状态

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 09:15

## 实际改动

- 普通首屏 `雷达` 整张卡片新增 `plain-radar-panel` 与外层 `data-state`。
- 新增雷达卡片状态线样式：运行态、等待/启动中/待刷新态、未运行中性态、刷新/启动失败异常态。
- 补充前端测试，锁定默认 `雷达已运行`、`雷达未运行`、`雷达待刷新`、`雷达启动中`、`雷达启动失败` 等外层状态和 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该状态只汇总已有雷达短状态和地图雷达 marker 口径，不自动启动雷达、不刷新 proof、不执行 Nav2、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|keeps trip controls safety-gated while running lidar proof only asks for refresh|shows plain radar refresh failure reason on the map|shows a map radar-starting marker while the plain radar start request is in flight|shows plain radar start only when the readback says lidar is stopped"`，5 passed / 187 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实 LiDAR lifecycle、真实 scan proof、真实底盘、真实 Nav2、真实送达和真实键盘长按未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
