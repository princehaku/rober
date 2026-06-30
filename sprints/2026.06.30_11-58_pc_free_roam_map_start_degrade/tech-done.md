# PC 自由移动建图失败降级

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自由移动主按钮在摄像头和雷达 ready 时仍会先尝试 `/api/robot-control/map/start`。
  - 如果地图记录启动失败，主按钮链路不再停在“扫图不会移动”，而是降级调用固定 `/api/robot-control/free-roam/autonomy/start`。
  - 降级 start 请求体固定为 `confirm_operator_safety=true`、`confirm_mapping_active=false`，明确本轮只按低速自由移动记录，不按建图验收。
  - 页面新增“建图记录启动失败，本次已降级为低速自由移动”的普通用户提示，并在 motion/handoff DOM 上暴露 `data-mapping-start-degraded-for-session`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增主按钮建图失败降级测试：确认先调用地图 start，再调用自由移动 start，且不触发 manual、Nav2、delivery 或 `/cmd_vel`。
  - 保留单独“重新建图”按钮失败不发车的旧安全语义。

## 验证结果

- `npm test -- test/App.test.ts -t "degrades to low-speed free roam"`：通过，1 passed。
- `npm test -- test/App.test.ts -t "keeps failed free-roam map lifecycle visible|starts map recording before auto sweep"`：通过，2 passed。
- `npm test -- --run`：通过，2 test files、393 tests passed。
- `npm run lint`：通过，0 errors；保留既有 4 个 Vue multiline warning。
- `npm run build`：通过，产物 `dist/assets/index-BtZKg9Zr.js`。
- `git diff --check`：通过，无 whitespace 问题。
- 7001 重启：`npm run api` 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node PID `97673` 监听 `*:7001`。
- 7001 只读 smoke：`curl 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787'` 返回 `trashbot.pc_tools_workstation.robot_control_summary.v1`；小车 API 读回为 `fetch_timeout_2400ms`，所以仅证明 PC Node 正常，不证明真实上车端 ready。

## 剩余风险

- 当前为 PC 端 mock/DOM 行为验证，未向真实小车发送运动命令。
- 真实上车端如果在 `confirm_mapping_active=false` 时仍额外拒绝 start，需要后续通过 7001 live read-only 证据或现场安全确认后的 HIL 验证继续定位。
