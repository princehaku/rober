# 2026-06-26 03:35 PC 行程到达后地图下一步提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - Nav2 图上路线执行完成且读到本轮反馈样本后，地图 caption 从“已到达，反馈 N 次”扩展为“已到达，反馈 N 次，准备送达材料”。
  - 地图终点 marker 的可访问说明在 `已到达` 状态下补充“下一步准备送达材料”，和行程卡片/本轮进度保持一致。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展图上路线执行成功测试，覆盖 marker aria、地图 caption、行程状态、行程进度、证据摘要和本轮进度下一步。
- `docs/product/pc_tools_workstation.md`
  - 记录 Nav2 到达后地图 WYSIWYG 下一步提示。

## 验证结果

- 通过：`npm test -- -t "marks the visible route goal as executing while the plain trip request is pending"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 177 skipped (178)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-BDMWzkDg.js 473.31 kB`
- 通过：`npm test`
  - 第一次发现 2 个旧断言仍期待旧地图 caption，已更新为新 WYSIWYG 文案。
  - 复跑通过：`Test Files 2 passed (2)`，`Tests 178 passed (178)`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node 90259 ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端状态和 mock 组件测试，不触发真实 Nav2 行程、manual、keyboard pulse、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需 operator 在 `0.0.0.0:7001` 上执行受控路线后复核地图 marker、caption 和送达材料准备流程。
