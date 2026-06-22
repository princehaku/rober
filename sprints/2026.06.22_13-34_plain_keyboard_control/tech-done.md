# Plain Keyboard Control

sprint_type: micro

## 实际改动

- PC 普通首屏 `移动/导航` 卡片新增键盘连续手控入口，显示 `启用键盘`、`键盘停止` 和 W/A/S/D/方向键说明。
- 键盘手控仍复用原有 focused panel gate：必须先点击启用并让面板获得焦点；输入框和页面其它区域按键不会触发手控。
- 非 stop 键盘 pulse 继续复用 `canSendManualMotion`、operator report preflight、速度/时长 clamp 和固定 workstation proxy；松开、失焦、页面隐藏或切换地址仍走 stop 收口。
- 普通首屏新增 `plainKeyboardControlSummary`，只展示普通话术，不泄露 operator report 缺项、HIL、`/api/base/manual`、raw readback 或工程字段。
- 高级诊断保留完整键盘状态、pulse、interval 和 stop trigger 读数，但不再放置主要操作入口。
- 更新 PC 工作站产品文档和 Vue 测试，锁定普通首屏键盘入口与字段不泄露边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`112 passed (112)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 普通首屏键盘入口位置与可用性；没有发送真实键盘手控脉冲，也不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行或 delivery success。
- 键盘手控仍依赖现场 operator report 材料完整；材料缺失时 UI 会显示普通阻断话术，后端不会转发非 stop manual。
