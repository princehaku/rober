# PC Robot API 7001 Port Drift Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当 `baseUrl=http://192.168.1.11:7001` 且 Robot API 只读端点全失败时，新增 `robot_api_port_7001_mismatch_use_8787` 诊断。
  - `current_fact_plain` 明确提示：`7001` 是 PC 页面服务端口，小车上位机 Robot API 是 `192.168.1.11:8787`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 新增 server 单测，锁定 7001 错填时的 blocked reason 和普通文案。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步端口口径：PC Node 固定 `0.0.0.0:7001`，Robot API 固定 `192.168.1.11:8787`；`7001`/`7071` 都不能填成小车 API。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，1 个测试文件、1 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、400 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Q7ojBxrt.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `33712`，新监听进程为 `node` PID `52134`，地址 `TCP *:7001`。
- 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A7001` 返回
  `robot_api_connection.blocked_reasons[0]=robot_api_port_7001_mismatch_use_8787`，`current_fact_plain` 明确提示
  `7001` 是 PC 页面服务端口、Robot API 是 `192.168.1.11:8787`。
- 只读健康检查：`GET http://192.168.1.11:8787/health` 返回 `status=ready`、`safe_to_control=false`、
  `robot_control_executed=false`、`primary_actions_enabled=false`。

## 剩余风险

- 本轮只修正只读诊断，不自动重写用户输入、不重启上位机、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 本轮没有做真实运动 HIL；完整 Nav2 路线执行、键盘连续控制和自由移动仍需要现场安全确认后的真实动作验证。
