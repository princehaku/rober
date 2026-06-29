# 2026.06.30 06:13 PC 行程送达对齐 DOM 合同

sprint_type: micro

## 实际改动

- 普通首屏行程卡新增送达对齐 DOM 证据：
  - `data-current-nav2-route-map-ref`
  - `data-delivery-route-map-ref`
  - `data-delivery-route-map-matches-current-nav2`
  - `data-delivery-success-matches-current-nav2`
  - `data-delivery-success-evidence-route-mismatch`
  - `data-delivery-success-evidence-stale`
- 扩展现有行程/送达测试，覆盖已送达匹配、本轮草稿匹配、旧草稿不匹配以及更新材料后重新匹配。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，明确这些字段只服务完整 Nav2 路线后的送达验收，不自动发车或确认送达。

## 验证结果

- `npm test -- test/App.test.ts -t "marks the map goal as delivered only when delivery success matches the current Nav2 route|shows final confirmation as next step when latest draft material matches the fresh Nav2 route|blocks final delivery when a restored draft route ref does not match the fresh Nav2 result"`：通过，`3 passed | 216 skipped`。
- `npm test -- --run`：通过，`2 passed` test files，`389 passed` tests。
- `npm run build`：通过，Vite 仅保留既有 chunk size warning。
- `git diff --check`：通过，无 whitespace error。
- dist smoke：`pc-tools/workstation/dist/assets/index-3ZTIfwH2.js` 可检出 `current-nav2-route-map-ref`、`delivery-route-map-matches-current-nav2`、`delivery-success-matches-current-nav2` 和 `delivery-success-evidence-route-mismatch`。

## 剩余风险

- 本轮只补 PC DOM 合同、测试和文档；没有发送真实 Nav2、manual、keyboard、free-roam、delivery 或 `/cmd_vel`。
- 完整目标仍需要真实车 HIL 复验：执行当前图上路线、同窗口轮速 L/R 非零、现场送达确认和传感器 WYSIWYG 需在真实环境闭环。
