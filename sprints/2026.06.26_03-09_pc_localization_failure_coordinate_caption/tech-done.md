# PC 定位失败坐标口径同步

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plainMapCoordinateTruthLabel` 增加 localization reset 失败短原因输入。
  - 普通首屏地图缺少 map-frame pose 且本轮 `重新定位` 失败时，`坐标口径` 从泛化 `机器人位置未读到` 升级为 `机器人定位失败：<failure_reason>`。
  - 有局部雷达点、路线叠图或空地图三种缺 pose 场景都会复用同一定位失败短原因。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 localization reset 失败用例，断言地图 marker 与 `坐标口径` 同步显示 `amcl_timeout`。
- `docs/product/pc_tools_workstation.md`
  - 记录本轮地图 caption WYSIWYG 行为和控制边界。

## 验证结果

- 已通过：
  - `npm test -- -t "shows localization reset failure on the plain map pose marker"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 184 skipped (185)`。
  - `npm run lint`
  - 结果：ESLint 通过。
  - `npm run build`
  - 结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - `npm test`
  - 结果：`Test Files 2 passed (2)`，`Tests 185 passed (185)`。
  - `git diff --check`
  - 结果：通过，无 whitespace error。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：本机已有 `node` 监听 `*:7001`，未改 Clash 或系统代理配置。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有连接真实上位机触发 `/api/localize/reset`，也没有 HIL。
- 该改动只统一首屏地图文案，不改变 AMCL/TF/root cause 定位逻辑。
- 未触发真实 manual、keyboard pulse、Nav2 execute、delivery complete、stop 或 `/cmd_vel`；未修改 Clash 或系统代理配置。
