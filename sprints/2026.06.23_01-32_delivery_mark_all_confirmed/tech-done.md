# 2026-06-23 01:32 送达最终确认一键勾选

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `最终确认` 区新增 `全部已确认` 本地按钮。
- 该按钮只一次性勾选人在旁边可接管、周围安全、停止手段就绪、已观察到到达/移动、已观察到停止、视频和行程材料已核对、确认已投放/送达七个本地 checkbox。
- 它不保存材料、不提交 operator report、不调用 delivery complete、不执行 Nav2、不发送 manual、stop 或 `/cmd_vel`；后端送达 gate 仍必须由红色 `确认送达（不发车）` 单独触发。
- `pc-tools/workstation/test/App.test.ts`：补充回归，确认点击 `全部已确认` 后本地 checkbox 全部勾选、确认按钮变为可提交，并且 fetch 调用数不增加。
- `docs/product/pc_tools_workstation.md`：同步记录普通首屏最终确认的一键勾选边界。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只减少 PC 端最终确认点击成本；不证明真实 delivery success。
- 当前上位机只读 `GET /api/delivery/latest` 仍显示 `delivery_success=false`，缺现场最终确认与后端 gate 成功。
- 当前上位机只读 `GET /api/base/status` 新鲜 T=1001 仍为 `L/R=0/0`；wheel raw L/R 非零仍未完成。
