# PC 扫图启动后自动启用键盘

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `开始扫地式建图` 成功启动地图记录后，如果键盘 gate 已满足，自动进入 `键盘已启用`。
  - 该动作只打开全局键盘窗口，不发送 manual pulse；移动仍要 operator 按住方向键/WASD/屏幕方向键。
  - 扫图按钮文案在已启用后显示 `键盘已启用`，下一步直接提示按住方向键扫图。
- `pc-tools/workstation/test/App.test.ts`
  - 更新扫图流程测试，断言启动记录后自动启用键盘但 `base/manual` 调用数不增加。
  - 保留按住屏幕方向键后才发送 manual pulse、松开后 stop 和地图刷新收口的断言。
- `docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录扫图启动后自动启用键盘的安全边界。

## 验证结果

- 通过：`npm test -- -t "free-roam keyboard locked"`（1 passed，171 skipped）
- 通过：`npm run lint`
- 通过：`npm test`（172 passed）
- 通过：`npm run build`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`（`node` 监听 `*:7001`，未使用 Clash 端口）

## 剩余风险

- 本轮仍是 PC/mock 层，没有触发真实小车运动或真实建图 HIL。
- 真正“无人值守自动扫图”仍未开放；当前只是减少人工扫图向导里的启用键盘步骤。
