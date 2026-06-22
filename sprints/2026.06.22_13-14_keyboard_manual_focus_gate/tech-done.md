# Keyboard Manual Focus Gate

sprint_type: micro

## 实际改动

- PC 高级诊断键盘连续手控改为显式启用：必须点击 `启用键盘`，键盘面板获得焦点后，W/A/S/D 或方向键才会触发连续短脉冲。
- 全局页面按键和输入框内按键不会触发 `/api/robot-control/base/manual`；面板失焦、窗口失焦、页面隐藏或松开当前方向键会退出/停止。
- 键盘点动仍复用现有 `canSendManualMotion` 门禁和固定 workstation proxy，不新增 `/cmd_vel`、浏览器直连或任意 endpoint。
- 补充 Vue 测试，覆盖全局按键不发 manual、启用面板后才发 manual、材料缺失时仍 blocked。
- 更新 `docs/product/pc_tools_workstation.md`，同步键盘手控的显式启用和焦点边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`112 passed (112)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只验证 PC UI 交互和代理请求边界；未在真实现场执行键盘长按运动。
- 真实连续手控仍依赖 operator material gate、现场安全确认、上位机 `/api/base/manual` 和底盘反馈证据。
