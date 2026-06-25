# 2026.06.26 04:16 PC 自动扫图保存 gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `freeRoamAutonomySaveBlocked`：自动扫图 start/stop 请求未返回，或 start 已转发但 stop 尚未转发成功时，普通首屏禁止保存地图。
  - `保存当前地图` 按钮在自动扫图运行/启停 pending 期间显示 `先停止自动扫图` 并保持 disabled。
  - 扫地式建图步骤条的保存步骤在该状态下提示 `先停止自动扫图，再保存地图`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自动扫图 ready 流程测试：start 后保存按钮锁定，stop 返回后保存按钮恢复可用；同时继续断言不调用 manual、Nav2 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录自动扫图运行中保存地图的普通首屏 gate 和控制边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- -t "starts free-roam autonomy"`
  - 结果：1 passed，190 skipped。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
- 已通过：`cd pc-tools/workstation && npm test`
  - 结果：2 files passed，191 tests passed。
- 已通过：`git diff --check`
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node` 正在监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有做真实自动扫图 HIL。
- 没有触发真实上位机自动扫图、manual、Nav2、delivery 或 `/cmd_vel`；真实场地仍需 HIL 验证 stop 后保存流程。
