# PC 扫图停止后自动刷新地图画面

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘扫图 release stop 成功后，如果地图记录正在运行，自动触发一次只读 `refreshMapPreview({ countForFreeRoamSession: true })`。
  - 扫图状态在 stop 后刷新期间显示 `已停止，正在刷新扫图画面。`；刷新成功后沿用原有 `地图画面已刷新，可以保存当前地图。`
  - 自动刷新只读取地图预览，不发送 manual/keyboard pulse/Nav2/delivery complete/额外 stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖松开方向键后新增 1 次 `/api/robot-control/map/preview`，同时不新增 Nav2 execute 或 delivery complete 调用。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 stop 后自动刷新扫图画面的行为和控制边界。

## 验证结果

- `npm test -- --testNamePattern "free-roam|keyboard locked|keyboard|扫地式建图|map recording"`：通过，1 个测试文件执行，9 个相关测试通过。
- `npm run lint`：通过。
- `npm test`：通过，2 个测试文件，167 个测试通过。
- `npm run build`：通过，完成 TypeScript 和 Vite production build。

## 剩余风险

- 本轮是 PC 端只读地图刷新体验改进，不是自动扫图运动控制。
- 真实自由跑动建图仍需要上车端 watchdog、雷达避障和 operator stop 兜底后做 HIL 验证。
