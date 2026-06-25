# PC 行程执行后地图同步刷新

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏点击 `执行图上路线` 并返回后，自动调用一次只读地图画面刷新。
  - 目标是让执行后的地图画面、路线 marker、机器人/雷达叠图尽快回到地图卡片，减少现场看旧地图的误判。
  - 该刷新不再次执行 Nav2，不发送 manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展可见路线执行用例，验证执行后会额外读取一次 `/api/robot-control/map/preview`。
  - 同一用例继续验证不会自动送达、不会发送 manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录执行图上路线后的只读地图刷新口径和安全边界。

## 验证结果

- `npm test -- -t "visible-route trip execution|plain trip|Nav2 goal"`：通过，2 files / 11 passed / 165 skipped。
- `npm run lint`：通过。
- `npm run build`：通过，Vite production build 和 server TypeScript build 均完成。
- `npm test`：通过，2 files / 176 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node 90259 ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮不触发真实 Nav2、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 地图刷新是否能显示新的机器人位置取决于上位机 summary/map preview 是否在执行后读到最新定位；PC 侧只保证执行后主动读取一次。
