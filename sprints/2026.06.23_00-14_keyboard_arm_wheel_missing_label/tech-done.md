# 2026-06-23 00:14 键盘启用轮速缺项提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `启用键盘` 按钮在连接、键盘合同、移动前检查和现场画面都已满足，但键盘 gate 仍缺 `轮速记录` 时显示 `启用键盘（先补轮速）`。
- `pc-tools/workstation/test/App.test.ts`：新增回归，覆盖前置 gate 已满足但 wheel/LiDAR 材料未齐时按钮禁用、文案指向轮速补证、点击与键盘按键都不调用 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`：同步记录该文案只做普通用户引导，不 arm 键盘、不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`125 passed (125)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 普通首屏键盘 gate 的轮速缺项提示，不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控已经完成。
- 真实小车仍需要 operator 在安全确认后采集非零轮速、LiDAR motion delta 和送达确认材料；本轮没有发送任何真实运动控制命令。
