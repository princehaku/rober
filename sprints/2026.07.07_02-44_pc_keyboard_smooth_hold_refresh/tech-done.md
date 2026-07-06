# PC 键盘连续手控顺滑刷新

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘按住、manual pulse in-flight 或 stop/manual pending 时，实时地图和相机状态轮询暂停，避免连续手控时重面板读回抢占前端渲染。
  - 键盘松开后的 stop 改为 `sendStop({ refreshAfter: false })`，不再先走通用 summary 刷新；stop 成功后只保留一次 feedback-samples + summary 的 post-hold 验收读回。
  - 键盘 DOM 新增 `data-keyboard-smooth-hold-refresh-paused`，让组件测试和现场脚本能直接验证按住期间刷新让路。
- `pc-tools/workstation/test/App.test.ts`
  - 新增组件测试模拟长按键盘 6 秒，确认 manual pulse 连续发送、地图预览和相机状态轮询不增加、松开后 stop/feedback/summary 只按一次验收链路执行。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定键盘顺滑刷新合同源码字段，避免回退到按住期间重刷新。
- `pc-tools/README.md`
  - 记录 PC 键盘顺滑模式的运行边界和现场 DOM 验收字段。
- `docs/product/pc_tools_workstation.md`
  - 同步产品边界：PC 键盘按住期间暂停重刷新，不改变 ROS2、相机或底盘硬件协议。

## 验证结果

- `npm test -- test/catalog.test.ts --run`
  - 通过：`Test Files 1 passed (1)`，`Tests 195 passed (195)`。
- `npm test -- test/App.test.ts --run`
  - 通过：`Test Files 1 passed (1)`，`Tests 243 passed (243)`。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
  - Vite 仍提示单个 chunk 超过 500 kB；这是既有打包体积提示，本轮未扩大为阻塞项。
- 本机服务复验
  - 已重启 PC API/UI：`HOST=0.0.0.0 PORT=7001 npm run api`。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
  - `curl -sS http://127.0.0.1:7001/api/health` 返回 `workstation_host="0.0.0.0"`、`workstation_port=7001`、`default_robot_api_base_url="http://192.168.1.11:8787"`。
  - `curl -sS -I http://127.0.0.1:7001/` 返回 `HTTP/1.1 200 OK`。

## 剩余风险

- 本轮变更只覆盖 PC 前端刷新调度和键盘 release 读回节奏，不宣称真实硬件 HIL 重新验收。
- 真实现场仍需用户在浏览器按住 W/A/S/D 体感复验；代码级测试已覆盖按住 6 秒不触发地图/相机重轮询，以及松开后只做一次 summary 读回。
