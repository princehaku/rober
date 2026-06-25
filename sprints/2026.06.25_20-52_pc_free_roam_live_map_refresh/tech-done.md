# PC 扫图中自动刷新地图画面

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘扫图同一次按住达到连续 pulse 验证阈值后，自动触发一次只读地图预览刷新。
  - 按住期间刷新成功后，扫图状态显示 `地图画面已跟随刷新`，覆盖提示显示松开后还会再刷新一次用于保存。
  - 按住期间的刷新不计入保存 gate；保存仍然要求 stop 后的会话刷新成功。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖第二次连续 pulse 后只新增 1 次 `/api/robot-control/map/preview`，并在松开后再新增 1 次用于保存。
- `docs/product/pc_tools_workstation.md`
  - 同步记录按住扫图中自动刷新地图画面的行为和控制边界。

## 验证结果

- `npm test -- --testNamePattern "free-roam|keyboard locked|keyboard|扫地式建图|map recording"`：通过，1 个测试文件执行，9 个相关测试通过。
- `npm run lint`：通过。
- `npm test`：通过，2 个测试文件，167 个测试通过。
- `npm run build`：通过，完成 TypeScript 和 Vite production build。

## 剩余风险

- 本轮仍是 PC 端只读地图刷新体验改进，不是自动扫图运动控制。
- 真实自由跑动建图还需要上车端 watchdog、雷达避障和 operator stop 兜底后做 HIL 验证。
