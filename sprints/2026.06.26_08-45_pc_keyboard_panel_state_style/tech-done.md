# PC 键盘手控面板状态外框

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 08:45

## 实际改动

- 普通首屏 `键盘手控` 面板将 `plainKeyboardControlSummary.state` 暴露为外层 `data-state`。
- 新增 `未满足/可手控/已启用/手控中/待停止/待验证/已验证` 等面板状态外框样式，让 PC 键盘连续手控状态不只藏在长文案里。
- 补充前端测试，锁定键盘 gate 可用、启用、按住连续脉冲、松开 stop 收口后的面板 `data-state` 和 CSS 选择器。
- 更新 `docs/product/pc_tools_workstation.md`，明确该改动只影响 PC 前端 WYSIWYG，不自动启用键盘、不额外发送 manual pulse、不调用 Nav2、delivery complete、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy"`，1 passed / 191 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files passed / 192 tests passed。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node` 正在监听 `*:7001`。
- 已恢复全量测试触发的两个旧 smoke artifact `checked_at` 时间戳副作用。

## 剩余风险

- 真实键盘长按、真实底盘、真实 stop 和真实 Nav2/delivery 未在本 micro sprint 中触发；本轮只做 PC 前端 mock/静态验证。
