# PC 扫地式建图刷新中键盘 gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `keyboardMapWysiwygBlocked`，地图记录已启动、扫图画面刷新 pending 且当前没有按住方向时，禁用新的键盘/屏幕方向移动；状态行显示等待地图刷新。已经按住方向时不硬切，仍允许松开并发送 stop。
- `pc-tools/workstation/test/App.test.ts`：扩展 `keeps free-roam keyboard locked until map recording starts`，用延迟 map preview Promise 验证刷新 pending 时方向键禁用、pointerdown 不产生 `/api/robot-control/base/manual` 请求，刷新完成后恢复。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`：同步扫地式建图地图刷新中的键盘 gate 行为和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "keeps free-roam keyboard locked until map recording starts"`，1 passed / 190 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 test files passed，191 tests passed。
- 通过：`git diff --check`。
- 确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示项目 node 监听 `*:7001`。

## 剩余风险

- 本轮验证仍是 PC 端 mock/单测验证，不触发真实小车运动；真实键盘操作、map preview 慢请求和松手 stop 收口仍需要现场 HIL 观察。
