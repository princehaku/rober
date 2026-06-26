# PC 图上路线地图刷新失败 WYSIWYG

## sprint_type

micro

## 实际改动

- 当 summary 已读到路线点、但地图画面 preview 失败导致图上路线不可见时，普通首屏行程卡片状态显示 `待刷新`。
- 行程卡片、行程状态和 `图上路线` WYSIWYG 提示同步显示 `地图画面刷新失败：<原因>`，不再只泛化提示“先刷新地图画面”。
- `执行/刷新图上路线` 按钮仍只重试 no-motion 路线 proof 和地图 preview；不可见路线不会被当成可执行 Nav2 目标。
- 新增 PC 工作站回归测试，覆盖路线已准备但地图 preview 失败的首屏状态，并验证不触发 Nav2 execute、manual 或 `/cmd_vel`。
- 同步 `docs/product/pc_tools_workstation.md`，记录图上路线不可见时的地图刷新失败口径。

## 验证结果

- 已通过定向回归：`npm test -- -t "shows route map preview failure on the trip card when prepared route is not visible"`。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍提示产物 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建。
- `npm test` 通过：`2 passed (2)`、`206 passed (206)`。
- `git diff --check` 通过，无空白错误。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 仍监听 `TCP *:7001 (LISTEN)`，本轮未修改 Clash 或系统代理。

## 剩余风险

- 本轮验证边界是 PC 前端 mock DOM；未执行真实 Nav2、真实地图 preview 失败或 HIL。
