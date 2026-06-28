# Map summary plain hint

- sprint_type: micro
- 时间：2026-06-29 07:00 CST
- Owner：User Touchpoint Full-Stack Engineer（主会话执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.map` 新增 `plain_hint`，把地图画面、图上路线和雷达 marker WYSIWYG 结论合成一条只读事实。
  - fail-closed summary 也补齐同名字段，避免读取失败时字段缺失。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 更新 `RobotControlSummaryResponse.readback_summary.map` 类型。
- `pc-tools/workstation/test/App.test.ts`
  - 同步默认 summary fixture 的 map `plain_hint`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖路线未显示、地图/路线/雷达 marker 都已显示、旧雷达来源点不能当当前 marker 三类 WYSIWYG 场景。
- `docs/product/pc_tools_workstation.md`
  - 记录 summary map `plain_hint` 的只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`
  - 结果：1 个测试文件通过，38 个用例通过，122 个同文件用例按过滤跳过。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`
  - 结果：1 个测试文件通过，1 个用例通过，214 个同文件用例按过滤跳过。
- 通过：`npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript 与 Vite build 通过；保留既有 Vite chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`
  - 结果：2 个测试文件通过，375 个用例通过。
- 通过：重启 PC API 到 `0.0.0.0:7001`，实际监听 PID `22231`。
  - 只读 `GET /api/robot-control/summary` 结果：`readback_summary.map.plain_hint` 返回“地图画面、图上路线和小车位置已显示。图上路线已显示在当前地图画面。雷达 marker 未贴到当前地图：当前显示 0 个点；旧来源点 81 个只作诊断...下一步：先启动雷达，再刷新地图画面。”

## 剩余风险

- 本轮只补 summary 只读字段，不刷新地图、不启动雷达、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop。
- live 雷达 marker 仍未贴到当前地图，原因仍是雷达扫描过期且雷达未运行；需要现场显式启动雷达并刷新地图后才能闭环。
