# Plain Connection Degraded

sprint_type: micro

## 实际改动

- PC 普通首屏“小车连接”状态改为表达“是否读到上位机”，不再把单个慢 endpoint 或 proof 缺口直接显示成连接异常。
- 当 `robot_api_connection.loaded_count>0` 且没有 dangerous true fields 时，首屏显示 `已连接`，并提示“部分项目未通过，可展开高级诊断”。
- dangerous true fields 仍显示 `有异常`；所有控制、Nav2、送达和 success gate 不放宽。
- 高级诊断继续展示 `failed_count`、`blocked_count`、`blocked_reasons` 和 endpoint 细节，方便定位 `/api/status` 超时、雷达 proof 缺失等问题。
- 更新 Vue 测试和产品文档，锁定普通首屏连接语义。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`113 passed (113)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 本轮只修正 PC 普通连接状态展示，不证明 wheel raw L/R 非零、完整 Nav2 路线执行或 delivery success。
- 真实上位机当前仍有 `/api/status` 慢、雷达 proof 缺失和 delivery success 未完成等缺口，需继续在高级诊断或后续迭代处理。
