# PC Nav2 执行完成 DOM 合同

- sprint_type: micro
- 时间：2026-06-30 05:14 CST
- owner：User Touchpoint Full-Stack Engineer（主会话直接执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-trip-run` 增加 Nav2 执行完成验收 DOM 字段：
    `data-execution-feedback-sample-count`、`data-execution-control-proven`、
    `data-execution-wheel-lr-nonzero-proven`、`data-execution-complete`、
    `data-execution-post-map-refresh-required`、`data-execution-post-map-refresh-complete`、
    `data-execution-stop-requested`、`data-execution-stop-settled`。
  - 同一卡片增加送达后续状态字段：
    `data-delivery-material-ready`、`data-delivery-confirm-ready`、`data-delivery-success-ready`。
  - 字段全部来自已有 execute/latest、地图刷新、停止兜底和送达 computed，不新增运动入口。
- `pc-tools/workstation/test/App.test.ts`
  - 增加完整 Nav2 执行成功后的 DOM 断言：反馈样本、控制闭环、wheel raw L/R 非零、执行完成、执行后地图刷新完成。
  - 增加执行中 stop requested/settled DOM 断言。
  - 增加执行成功但地图刷新失败时的 DOM 断言：执行完成为 true，执行后地图刷新完成为 false。
  - 增加 IMU/命令迹象但 wheel raw L/R 未证明时的反向断言：不能算完整路线。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏 Nav2 执行完成 DOM 合同和只读边界。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "syncs latest readbacks and pre-fills delivery route material after visible-route trip execution"`，1 passed。
- 通过：`npm test -- test/App.test.ts -t "marks the visible route goal as request-pending while the plain trip request is pending"`，1 passed。
- 通过：`npm test -- test/App.test.ts -t "shows post-trip map refresh failure after a visible route succeeds"`，1 passed。
- 通过：`npm test -- test/App.test.ts -t "keeps Nav2 success with IMU motion signal out of complete route evidence until wheel raw L/R is nonzero"`，1 passed。
- 通过：`npm test -- --run`，`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 通过：`npm run build`，产物包含 `dist/assets/index-DtVNF7P7.js` 和 `dist/assets/index-CZMHo-c5.css`。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，`lsof` 显示 `node` PID 84061 监听 `TCP *:7001`。
- 通过：只读 HTTP smoke，`GET http://127.0.0.1:7001/` 加载 `/assets/index-DtVNF7P7.js`；
  bundle 中确认包含 `data-execution-feedback-sample-count`、`data-execution-post-map-refresh-complete`、
  `data-delivery-material-ready`、`data-execution-stop-settled`。

## 剩余风险

- 本轮是 PC DOM/测试合同增强，没有真实 HIL 发车验证；完整目标仍需要真实小车执行窗口内 wheel raw L/R 非零、地图刷新和送达确认共同证明。
- 执行后地图刷新失败时，PC 会诚实显示“行程完成但画面未刷新”，仍需要现场刷新地图画面后再做送达材料。
- 历史未暂存 artifact 文件保留原状，本轮不回滚不提交。
