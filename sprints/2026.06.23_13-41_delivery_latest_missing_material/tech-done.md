# Delivery latest missing material

sprint_type: micro

## 设计

本轮针对 `delivery success` 收口的 PC 易用性缺口：真实上位机 `/api/delivery/latest` 已经在 `latest_result.missing_required_material` 中给出缺项，但 PC 普通首屏主要消费 `blocked_reasons`。当 latest 没有顶层 `blocked_reasons` 时，现场人员会看不到“下一步到底差什么”。

设计口径：

- Node 代理继续 fail-closed，不新增任何运动或确认动作。
- `delivery/latest`、`delivery/check`、`delivery/complete` 代理显式返回 `missing_required_material`，让契约能表达上位机 gate 缺项。
- Vue 普通首屏把 `missing_required_material` 和 `blocked_reasons` 合并去重，再翻译成普通用户可读的送达缺项。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 delivery latest/check/complete 三个响应契约新增 `missing_required_material: string[]`。
- `pc-tools/workstation/src/server/index.ts`：delivery latest/check/complete 代理输出 `missing_required_material`，complete 代理也把远端 missing material 合并进 blocked reasons。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：送达 gate 缺项合并读取 latest/check/complete 的 `missing_required_material` 与 `blocked_reasons`，fallback 响应保持空数组。
- `pc-tools/workstation/test/App.test.ts`：覆盖 latest 只有 `missing_required_material`、`blocked_reasons=[]` 时，普通首屏仍显示“现场确认报告、已观察到到达/移动、已观察到停止、确认已投放/送达、最后点击确认送达”，且不调用 delivery check/complete/manual/cmd_vel。
- `pc-tools/workstation/test/catalog.test.ts`：覆盖 Node delivery latest proxy 显式返回 `missing_required_material`。
- `docs/product/pc_tools_workstation.md`：同步记录普通首屏读取送达缺项的新口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "delivery latest missing material"`：通过，1 个目标用例通过，确认 latest 只有 `missing_required_material` 时普通首屏仍显示送达缺项，且未调用 delivery check/complete/manual/cmd_vel。
- `cd pc-tools/workstation && npm test -- -t "delivery latest proxy reads fixed gate gap"`：通过，1 个目标用例通过，确认 Node delivery latest proxy 显式返回 `missing_required_material`。
- `cd pc-tools/workstation && npm test`：通过，2 个 test files / 149 个 tests 全部通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite production build 与 server TypeScript build 完成。
- `git diff --check`：通过，无空白错误。
- 全量测试刷新了两个历史 DOM smoke artifact 的 `checked_at`；本轮已恢复为原始时间，未把旧证据时间戳变更纳入提交。

## 剩余风险

- 本轮不触发真实小车运动，不调用 radar start、first-jog、manual、keyboard pulse、stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `delivery_success` 仍未完成：上位机当前 latest 缺少人工最终确认、observed motion/stop 和 nested delivery success；本轮只让 PC 更清楚地展示这些缺项。
