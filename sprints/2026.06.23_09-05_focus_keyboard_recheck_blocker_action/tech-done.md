# 复查手控条件聚焦真实缺口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `复查手控条件` 刷新后不再只停留在复查按钮；若键盘 gate 已满足则聚焦启用键盘，若仍缺恢复确认、轮速记录或雷达移动记录，则聚焦对应的恢复确认、试动或保存区域。该逻辑只移动焦点，不触发运动、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：扩展“先补轮速”场景，验证点击 `复查手控条件` 只触发只读反馈刷新，不发送 manual，并把焦点带到 `plain-wheel-trial`。
- `docs/product/pc_tools_workstation.md`：同步普通首屏键盘复查聚焦规则，明确仍保持不发车边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、136 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。
- 已恢复 `npm test` 改写的历史 smoke JSON `checked_at` 副作用，提交范围不包含旧 artifacts 噪声。

## 剩余风险

- 本轮是 PC 端易用性和安全聚焦改进，不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、真实 delivery success 或真实 PC 键盘连续手控。
- `0.0.0.0:7071` 仍被本机 Clash Verge 占用；未得到明确授权前不杀进程，因此本轮不启动占用 7071 的 public API 服务。
