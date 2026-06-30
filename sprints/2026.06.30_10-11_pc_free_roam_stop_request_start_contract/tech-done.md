# PC 自由移动停止请求启动合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plainFreeRoamDomEvidence` 新增 `freeRoamStopRequestPending`、`startWillClearStopRequest`、`motionStartBlockedByStopRequest`，直接消费 action card 结构化 evidence，不解析中文文案。
  - 自由移动主按钮新增 `data-free-roam-stop-request-pending`、`data-start-will-clear-stop-request`、`data-motion-start-blocked-by-stop-request`。
  - 当已勾安全确认且 start 会先清 stop request 时，主按钮文案从普通“开始自由移动（低速）”切换为“解除停止并开始自由移动（低速）”；传感器已满足自动扫图时切换为“解除停止并开始自动扫图（低速）”。
  - 自由移动仪表同步展示“当前有停止请求，点击会先解除”，并继续声明仪表本身不发车。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 stop request pending 场景，固定主按钮和仪表的清 stop request 合同。
  - 扩展默认首屏和相机未首帧场景，证明没有 stop request 时按钮仍保持普通启动文案。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录自由移动 stop request pending 的 PC 端普通文案和 DOM 合同。

## 验证结果

- `npm test -- test/App.test.ts -t "free-roam start as clearing|renders Robot Control V1 by default|allows free-roam recording when camera source is selected|reuses one plain safety confirmation|splits free movement from mapping acceptance|starts map recording before auto sweep"`：通过，1 个测试文件，6 个用例通过。
- `npm test -- --run`：通过，2 个测试文件，391 个用例通过。
- `npm run lint`：通过，0 error；仍有 `RobotControlConsolePanel.vue` 既有 4 条 Vue warning，本轮未新增。
- `npm run build`：通过，产物包含 `dist/assets/index-CDIt7aVw.js`、`dist/assets/index-BQDMiOEq.css`；仍有 Vite chunk > 500 kB 既有提示。
- `git diff --check`：通过。
- 7001 已用新 bundle 重启，监听 `0.0.0.0:7001`，`lsof -iTCP:7001 -sTCP:LISTEN` 显示 Node PID 90148；`curl http://127.0.0.1:7001/` 返回 `index-CDIt7aVw.js`。
- live 只读 summary 验证：`/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，connection 为 degraded；`free_move` action card 为 `start_ready`，summary 为“可先自由移动；当前有停止请求，开始自由移动会先清除停止请求”，evidence 为 `free_roam_stop_request_pending=true`、`start_will_clear_stop_request=true`、`motion_start_blocked_by_stop_request=false`。
- live bundle 字符串验证：`解除停止并开始自由移动`、`data-start-will-clear-stop-request`、`motionStartBlockedByStopRequest`、`freeRoamStopRequestPending` 均存在。

## 剩余风险

- 本轮只改 PC Web 普通文案、DOM 合同、测试和文档；没有发送 free-roam start、manual、keyboard、Nav2、map start、delivery、stop 或 `/cmd_vel`。
- 真实自由移动仍必须由现场 operator 勾安全确认后点击主按钮执行；本轮不做 HIL 运动证明。
