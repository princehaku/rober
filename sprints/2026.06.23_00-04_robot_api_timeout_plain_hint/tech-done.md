# 2026-06-23 00:04 Robot API Timeout Plain Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“小车连接”在 PC summary 显示所有 Robot API readback 都 timeout 时，提示“上位机没回应；检查小车电源、网络和上位机服务后再点连接/刷新”，而不是泛化为“可读到部分信息”。
- `pc-tools/workstation/test/App.test.ts`：新增 timeout summary fixture，验证普通首屏不暴露 `fetch_timeout`/底层 endpoint，并且不触发 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录该提示只消费 summary blocked reasons，不改变控制 gate。

## 验证结果

- `npm test`：通过，2 个 test files，124 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善上位机 HTTP 超时时 PC 普通首屏的解释；真实接口当前 5 秒只读 curl 超时，无法证明 wheel raw L/R 非零、delivery success 或 PC 键盘连续手控。
- 完整 Nav2 路线执行仍只能沿用最近已保存的 latest artifact；当前无法通过 live HTTP readback 复验。
- 需要现场确认小车电源、网络、上位机服务或稍后恢复 HTTP 后，继续复验 `/api/base/status`、`/api/nav2/goal/execution/latest` 与 `/api/delivery/latest`。
