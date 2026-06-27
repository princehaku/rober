# 2026-06-28 19:25 PC 键盘首段脉冲发送中事实

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的键盘行新增首段 manual pulse 发送中状态。
  - 按住方向键后、PC 固定 `/api/robot-control/base/manual` 代理尚未返回前，显示“正在发送前进低速脉冲，返回前不把它当作已移动；松开会停”。
  - manual proxy 回包后才显示“正在前进，按住连续低速脉冲”，避免把 pending 请求误说成小车已动。
- `pc-tools/workstation/test/App.test.ts`
  - 新增延迟 manual proxy 回包的键盘回归测试，锁定发送中与回包后两段文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏键盘当前事实对发送中窗口的 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "first keyboard pulse as sending"`
  - 结果：1 个测试文件通过，1 个目标测试通过，197 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，346 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实键盘手控 HIL；验证范围限定在 PC 普通首屏状态展示、固定 manual proxy 调用路径和回归测试。
- 未发送任何真实 manual、keyboard、Nav2、delivery、free-roam、stop 或 `/cmd_vel` 请求。
