# PC 行程执行后地图刷新失败 WYSIWYG

## sprint_type

micro

## 实际改动

- 普通首屏 `执行图上路线` 返回后，自动地图画面刷新如果失败，行程卡片状态改为 `待刷新`。
- 行程卡片、行程状态、行程进度和地图 caption 同步显示 `执行后地图画面刷新失败：<原因>`，同时保留 Nav2 已到达和反馈次数结果。
- 后续任意地图画面刷新成功会清掉这条失败状态；下一次准备或执行行程也会清掉旧失败，避免旧失败污染新行程。
- 新增 PC 工作站回归测试，覆盖可见路线执行成功但执行后 `/api/robot-control/map/preview` 失败的 UI 状态，并验证不触发 manual、delivery complete 或 `/cmd_vel`。
- 同步 `docs/product/pc_tools_workstation.md`，记录执行后地图刷新失败的 WYSIWYG 口径和安全边界。

## 验证结果

- 已通过定向回归：`npm test -- -t "shows post-trip map refresh failure after a visible route succeeds"`。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍提示产物 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建。
- `npm test` 通过：`2 passed (2)`、`205 passed (205)`。
- `git diff --check` 通过，无空白错误。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 仍监听 `TCP *:7001 (LISTEN)`，本轮未修改 Clash 或系统代理。

## 剩余风险

- 本轮验证边界是 PC 前端 mock DOM；未执行真实 Nav2、真实地图 preview 失败、真实雷达刷新或 HIL。
