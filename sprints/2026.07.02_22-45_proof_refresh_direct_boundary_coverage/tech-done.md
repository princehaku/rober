# 2026.07.02 22:45 Proof refresh 直接回包边界覆盖

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/test/catalog.test.ts`：在 `workstation proof refresh proxies only allow fixed radar, map, and Nav2 POST bodies` 用例里，补齐 `map/proof/refresh` 和 `nav2/proof/refresh` 直接回包的完整只读安全边界断言。
- `docs/product/pc_tools_workstation.md`：同步要求 catalog 验证对三个 proof refresh 代理逐项覆盖 no-motion 边界，避免现场直接 curl map/nav2 proof 回包时边界退化。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run catalog.test.ts`：通过，`1 passed / 182 passed`。
- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed / 247 passed`。
- `git diff --check`：通过，无 whitespace error。
- `cd pc-tools/workstation && npm run build`：通过，Vite 保留既有 chunk size warning。
- `cd pc-tools/workstation && npm run lint`：通过。

## 剩余风险

- 本轮强化的是 PC 代理直接回包的自动化覆盖；真实车上仍需现场 curl proof refresh 回包确认上车链路可达。
