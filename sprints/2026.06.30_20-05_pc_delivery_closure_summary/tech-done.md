# PC 完整行程送达闭环短行

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainDeliveryClosureSummary`，把本轮行程是否完成、送达材料是否对齐当前行程、现场确认是否齐全、最终送达是否成功合成一行。
  - “任务收口”卡新增 `plain-delivery-closure-summary`，暴露 `data-nav2-ready`、`data-material-ready`、`data-route-map-matches-current-nav2`、`data-confirmation-ready`、`data-delivery-success-ready`、`data-confirm-ready` 和 `data-missing-count`。
- `pc-tools/workstation/src/styles.css`
  - 给送达闭环短行增加状态边框，区分待行程、待材料、待确认、可确认和已送达。
- `pc-tools/workstation/test/App.test.ts`
  - 固定默认未完成状态、本轮行程和材料已在但缺现场确认状态，以及全部确认后可提交状态。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录送达闭环短行和非发车边界。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
  - 首轮失败暴露普通首屏出现禁用词“现场确认”；已改为“确认项”后重跑通过。
- `npm test -- test/App.test.ts -t "shows final confirmation as next step when latest draft material matches the fresh Nav2 route"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `npm test -- --run`
  - 结果：通过，`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `npm run build`
  - 结果：通过，Vite 产物 `dist/assets/index-gkpwbcQT.css` 与 `dist/assets/index-gQiLMoFW.js` 已生成。
- `git diff --check`
  - 结果：通过，无空白错误。
- PC Node 重启与 HTTP smoke
  - `npm run api -- --host 0.0.0.0 --port 7001` 已重新监听，`lsof` 显示 `node` PID `77152` 监听 `TCP *:7001`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle：`index-gkpwbcQT.css`、`index-gQiLMoFW.js`。

## 剩余风险

- 本轮只改 PC Web 显示、DOM 合同和文档，不提交送达、不执行 Nav2、不发送 manual/keyboard/free-roam/stop 或 `/cmd_vel`。
- 真实完整行程、wheel raw L/R 非零和 delivery success 仍需要现场 HIL 验证；本轮提供的是 PC 侧更清晰的送达闭环状态与脚本验收入口。
