# 自动扫图锁定时的人工扫图向导文案

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 10:36 CST

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `plainFreeRoamManualGuideButtonLabel`，当上车端自动扫图 readiness 未 ready 时，自动扫图准备按钮不再固定显示 `按步骤人工扫图`，而是按当前下一步显示 `先勾安全确认`、`开始记录并继续`、`启用键盘扫图`、`刷新扫图画面`、`保存当前地图` 或 `按步骤：按住方向键扫图`。
- `pc-tools/workstation/test/App.test.ts`：更新普通首屏和人工扫图向导回归，锁定未勾安全时只聚焦安全 checkbox；勾安全后按钮显示 `开始记录并继续`，点击只调用固定 map start 并启用键盘窗口，不调用自动扫图 start、manual、Nav2、delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步说明该按钮是人工扫图导引文案，不修改 Clash 或系统代理配置，不新增控制通道。

## 验证结果

- 首次定向测试筛选 `npm test -- -t "renders the plain robot control home|uses the locked free-roam autonomy button as a manual mapping guide"` 未匹配测试名，Vitest 输出 `204 skipped`，不作为通过证据。
- 通过：`npm test -- -t "renders Robot Control V1|uses the locked auto-sweep"`，2 passed。
- 通过：`npm run lint`。
- 通过：`npm run build`。仅保留既有 Vite chunk size warning。
- 通过：`npm test`，204 passed。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，`node` 监听 `*:7001`。
- 已恢复全量测试自动刷新的两个旧 smoke artifact `checked_at` 字段，本轮未提交这些历史 artifact。

## 剩余风险

- 本轮只改善自动扫图锁定状态下的 PC 人工扫图向导文案和回归覆盖；真实自动扫图仍依赖上车端 readiness、雷达/地图/stop gate 和 HIL 证据。
