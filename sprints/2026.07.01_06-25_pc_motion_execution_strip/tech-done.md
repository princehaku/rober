# PC 运动执行条

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏动作清单顶部新增 `plain-live-motion-execution-strip` 现场执行条。
  - 执行条聚合完整行程、键盘连续手控、自由移动、传感器就绪后建图四个 runbook 项，显示 ready/blocked/completed 数量和主推荐动作。
  - 主按钮只做页面内聚焦，固定声明不启动 Nav2、manual、keyboard、free-roam、map runtime，也不发送运动命令。
- `pc-tools/workstation/test/App.test.ts`
  - 补充执行条 DOM 合同、普通用户文案、焦点跳转和无 motion/control 请求断言。
- `docs/product/pc_tools_workstation.md`
  - 同步动作清单现场执行条产品合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Robot Control V1 by default"`，1 test passed，229 skipped。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，6 tests passed。
- 通过：`git diff --check`。
- 通过：PC Node 已重启在 `0.0.0.0:7001`，`GET http://127.0.0.1:7001/api/health` 可读。

## 剩余风险

- 本轮只改 PC 端普通用户执行导引，不执行真实 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 完整行程 wheel L/R 非零、delivery success、键盘按住窗口 wheel L/R 非零和自由移动运行证据仍需要现场安全确认后的真实运动复验。
- 相机首帧仍受当前 UVC/USB 传输问题影响，建图启动仍缺 `camera_first_frame`。
