# PC 雷达启动按钮 Pending WYSIWYG

## sprint_type

micro

## 实际改动

- 普通首屏点击 `启动雷达` 后，在 radar lifecycle POST 未返回前，启动按钮显示 `雷达启动中` 并保持禁用。
- 地图 marker、雷达卡片和按钮三处 pending 口径保持一致，避免 operator 在启动中重复点击。
- 更新 PC 工作站回归测试，锁定 pending 状态下按钮文案、禁用态、地图 marker 和不触发 manual/Nav2/delivery。
- 同步 `docs/product/pc_tools_workstation.md`，明确本轮只改 pending WYSIWYG 文案，不改变 radar start 代理。

## 验证结果

- 首轮定向回归 `npm test -- -t "shows a map radar-starting marker while the plain radar start request is in flight"` 失败：`plain-radar-start` 在 pending 时被 `showPlainRadarStart` 隐藏，测试报 `Cannot call text on an empty DOMWrapper`。
- 修复后重跑定向回归通过：`1 passed | 203 skipped (204)`。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍提示产物 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建。
- `npm test` 通过：`2 passed (2)`、`204 passed (204)`。
- `git diff --check` 通过，无空白错误。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 仍监听 `TCP *:7001 (LISTEN)`，本轮未修改 Clash 或系统代理。

## 剩余风险

- 本轮验证边界是 PC 前端和 mock DOM；未执行真实雷达 lifecycle 启动、真实 scan proof 刷新或 HIL。
