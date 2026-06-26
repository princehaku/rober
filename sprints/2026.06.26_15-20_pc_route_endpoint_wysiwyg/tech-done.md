# PC 图上路线起终点口径 WYSIWYG

## sprint_type

micro

## 实际改动

- 普通首屏行程卡片的图上路线说明补充起点/终点地图坐标，和地图上的路线 marker 使用同一条 route overlay。
- 更新 PC 工作站测试，锁定可执行路线、地图画面刷新中、地图状态刷新中、准备后路线显示四类文案。
- 同步 `docs/product/pc_tools_workstation.md`，明确该呈现只读，不执行 Nav2、不发送手控、delivery、stop 或 `/cmd_vel`，不修改 Clash/系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "draws no-motion route start and end markers when no executed goal is available|blocks visible-route execution while the map preview is refreshing|refreshes the map automatically after plain trip preparation so the route becomes visible|syncs latest readbacks and pre-fills delivery route material after visible-route trip execution"`，结果 `Test Files 1 passed | 1 skipped (2)`，`Tests 4 passed | 198 skipped (202)`。
- 通过：`npm run lint`。
- 通过：`npm run build`。Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`，`Tests 202 passed (202)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端只读展示和 mock/单测验证，未做真实小车 HIL 或真实 Nav2 行程执行验证。
