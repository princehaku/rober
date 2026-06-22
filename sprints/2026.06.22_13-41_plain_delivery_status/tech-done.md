# Plain Delivery Status

sprint_type: micro

## 实际改动

- PC 普通首屏 `移动/导航` 卡片新增 `任务收口` 状态，显示 `未读取 / 检查中 / 待行程结果 / 待确认 / 已送达`。
- 新增普通按钮 `刷新送达状态` 和 `复查送达条件`，分别调用固定 `delivery/latest` 与 `delivery/check` 代理；`delivery/check` 仍由后端固定 `confirm=false`。
- 首屏只展示普通话术，不泄露 `delivery_success`、`/api/delivery`、blocked field name、route/map ref 或 raw readback。
- 不新增送达确认入口，不调用 `delivery/complete`、`operator/report`、Nav2 goal、`/api/base/manual` 或 `/cmd_vel`。
- 补充 Vue 测试，覆盖普通首屏收口按钮只读/复查行为和 fail-closed 边界。
- 更新 `docs/product/pc_tools_workstation.md` 记录普通首屏收口状态边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`113 passed (113)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 本轮只改善普通用户对最近行程/送达缺口的可见性；没有确认真实送达，也没有发送真实 Nav2 goal 或底盘运动。
- delivery success 仍需要现场最终 checklist、operator report 和 delivery gate 共同通过。
