# 2026-06-26 04:05 PC 雷达局部点 marker 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 雷达已运行、scan proof 已读到局部点但机器人 map-frame 位姿缺失时，地图雷达 marker 从“雷达已运行，位置未读到”升级为“雷达已运行，局部点 N 个”。
  - marker 的可访问说明同步写明“地图位置未读到，局部轮廓 N 个点等待定位”，避免把局部雷达误读成地图坐标点。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展雷达局部点测试，覆盖 marker 文案和 aria 说明。
- `docs/product/pc_tools_workstation.md`
  - 记录雷达局部点数量同步到地图 marker 的 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- -t "shows local radar scan dots instead of fake map dots when pose is missing"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 177 skipped (178)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-DHdI7bZJ.js 474.05 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 178 passed (178)`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node 90259 ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端状态和 mock 组件测试，不触发真实雷达启动、manual、keyboard pulse、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需在 `0.0.0.0:7001` 上确认雷达局部轮廓点数与真实 scan proof 一致，并继续解决定位后贴图验证。
