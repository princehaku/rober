# PC 扫地图保存后自动刷新

sprint_type: micro

## 目标

把普通首屏“扫地式建图”的保存闭环再收紧一步：operator 点击“保存当前地图”后，不需要再手动点一次刷新，PC 保存成功后自动读取最新地图 preview，并把状态文案说清楚。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增保存后地图画面刷新状态位 `plainFreeRoamSavedMapPreviewFreshForSession`。
  - `/api/robot-control/map/save` 成功后，沿用固定地图 lifecycle 收口，自动触发一次只读 `/api/robot-control/map/preview`。
  - 首屏 `扫图状态`、`地图画面` 和扫图 hint 在保存后自动刷新成功时显示“地图已保存，地图画面已自动刷新”。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展扫地式建图键盘测试，断言保存完成后地图 preview 请求数加一。
  - 同时锁住保存期间和保存后不额外发送 manual、Nav2 execute、delivery complete。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录保存地图后自动刷新地图 preview 的用户流程和安全边界。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏保存后自动刷新行为。

## 验证结果

- `npm test -- -t "keeps free-roam keyboard locked until map recording starts"`：通过，1 个定向用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 生产构建完成。
- `npm test`：通过，2 个测试文件、176 个用例全部通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 正在监听 `TCP *:7001`。

## 剩余风险

- 本轮是 PC 端 mock/单元验证；没有触发真实底盘、Nav2 或 `/cmd_vel`，也不等价于真车建图保存质量 HIL。
