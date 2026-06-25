# PC 定位失败地图 WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图缺少 map-frame 小车位置时，会读取本轮 `重新定位` 固定代理结果。
  - 当 localization reset 失败或被 blocked 时，地图缺位 marker 从 `位置未读到` 改为 `定位失败：<failure_reason>`。
  - 为缺位 marker 增加 aria 说明，明确“小车位置未读到”，避免把失败态误解成已定位。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 localization reset 失败场景测试，覆盖地图 marker、aria、移动卡片短原因，以及未调用 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 2026-06-26 本轮 WYSIWYG 行为、控制边界、Clash 不变和 PC 默认 `0.0.0.0:7001` 入口。

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
- 首次尝试：
  - `npm test -- --runInBand -t "shows localization reset failure on the plain map pose marker"` 失败，原因是当前 Vitest 不支持 Jest 风格 `--runInBand` 参数；已改用 Vitest 支持的过滤命令重跑通过。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有连接真实上位机触发 `/api/localize/reset`，也没有做 HIL。
- 该改动不改变真实定位流程，只把固定代理失败结果映射到普通首屏地图；真实 AMCL timeout、TF 缺失等根因仍需现场按上位机日志继续排查。
- 未触发真实 manual、keyboard pulse、Nav2 execute、delivery complete、stop 或 `/cmd_vel`；未修改 Clash 或系统代理配置。
