# PC 行程执行和键盘手控互锁

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：Nav2 行程执行 pending 时，`canSendManualMotion` 关闭新的 manual/keyboard pulse，键盘启用按钮显示 `行程中`，缺口提示等待行程执行返回；stop 入口不受该 gate 影响。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：手控请求 pending 或键盘方向按住时，普通首屏 `执行图上路线` 显示 `等待手控停止` 并禁用，避免手控和 Nav2 执行同时作为新动作启动。
- `pc-tools/workstation/test/App.test.ts`：扩展行程执行 pending 单测，验证地图仍显示 `行程中`，同时键盘方向按钮禁用、键盘按键/屏幕方向不会产生 `/api/robot-control/base/manual` 请求。
- `docs/product/pc_tools_workstation.md`：同步行程执行和 PC 手控/键盘互锁的用户口径和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "marks the visible route goal as executing while the plain trip request is pending"`，1 passed / 190 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 test files passed，191 tests passed。
- 通过：`git diff --check`。
- 确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示项目 node 监听 `*:7001`。

## 剩余风险

- 本轮验证是 PC mock/单测路径，不触发真实 Nav2 或真实小车运动；真实现场仍需要 operator HIL 观察 stop 接管和 Nav2 执行期间的键盘禁用表现。
