# 2026-06-23 21:05 Micro Sprint: 普通首屏展示默认小车短地址

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `默认小车` 行新增短地址展示 `192.168.1.11:8787`。
  - 地址仍来自固定默认 `http://192.168.1.11:8787`，首屏不恢复完整 URL 输入框；改地址仍只在高级连接详情中进行。
  - 展示短地址不触发刷新、Nav2、manual、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定普通首屏显示 `192.168.1.11:8787`，但不显示完整 `http://192.168.1.11:8787`。
  - 锁定高级地址清空时首屏显示 `未设置地址`，恢复默认后回到 `192.168.1.11:8787`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏默认小车短地址展示边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，`1 passed | 143 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`、`144 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物生成成功。
- `git diff --check`：通过。

## 剩余风险

- 本轮只推进 PC 端默认小车地址可见性，不证明真实 `wheel raw L/R 非零`、完整 Nav2 路线执行、`delivery success` 或 PC 键盘连续手控。
- 2026-06-23 真实只读状态：上位机 Robot API 在 `0.0.0.0:8787`，雷达 lifecycle 未运行，T1001 L/R 仍为 0/0，delivery success 仍为 false；真实动作仍需现场 operator 明确确认。
