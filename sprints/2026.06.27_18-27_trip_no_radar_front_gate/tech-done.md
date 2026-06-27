# Trip no radar front gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 删除普通首屏行程/送达链路里的历史 `plainTripRadarBlocked` 死路径。
  - 删除 `plainRadarTrip*` / `plainRadarDelivery*` 文案函数，避免以后把雷达重新接回 Nav2/送达前置。
  - `完整 Nav2 路线执行`、`delivery success`、`本轮进度` 和焦点跳转现在只指向行程本身；雷达状态继续留在雷达卡片、建图验收、LiDAR delta/障碍监看和地图标记。
- `pc-tools/workstation/test/App.test.ts`
  - 在雷达未配置/未运行场景补断言：行程和送达目标不能再提示“先启动雷达再行程”，目标收口的 Nav2/delivery 条目也不能包含雷达前置。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-27 18:27 起替换 2026-06-23 “雷达作为行程/送达前置”的旧口径。

## 验证结果

- 通过：`rg -n "plainTripRadarBlocked|plainTripNeedsFreshRunAfterRadar|plainRadarTrip|plainRadarDelivery" pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 无匹配，旧雷达行程 gate 符号已清空。
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "shows radar start configuration without blocking the minimal trip safety gate"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 171 skipped (172)`
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "keeps plain trip execution blocked until a visible route is confirmed while lidar is stopped"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 171 skipped (172)`
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`
  - `Tests 301 passed (301)`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - 仍有既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`git diff --check`

## 剩余风险

- 本轮没有触发真实 Nav2 execute；没有当前现场操作员安全确认时，仍不执行会动的小车动作。
- live Nav2 下一步仍是勾安全确认后用 ROS 重跑图上路线，并复验 wheel raw L/R 非零。
- 雷达仍用于建图验收和地图监看；本轮只保证它不再作为行程/送达前置。
