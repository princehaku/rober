# PC 图上行程执行绑定短行

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainTripRouteBindingSummary`，把地图上当前/最近/未绑定路线、路线点数、终点坐标和主按钮目标源合成短行。
  - 行程卡新增 `plain-trip-route-binding`，暴露 `data-route-wysiwyg-ready`、`data-executes-current-route-goal`、`data-goal-frame-id/x/y` 和 `data-target-source`。
  - 没有当前地图路线时，短行明确主按钮只会准备或刷新路线，不发车；当前地图路线可执行时，短行明确会执行这条地图路线。
- `pc-tools/workstation/src/styles.css`
  - 给行程绑定短行增加轻量边框和状态色，方便现场从行程卡里快速扫到当前绑定状态。
- `pc-tools/workstation/test/App.test.ts`
  - 固定默认未绑定状态、当前地图路线可执行状态和样式合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 PC 行程卡新增图上路线绑定短行及非发车边界。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
  - 首轮失败暴露普通首屏重新出现“路线”工程词；已改为“图上行程/地图行程”后重跑通过。
- `npm test -- test/App.test.ts -t "executes the visible route endpoint with nonzero Y instead of the default Nav2 form goal"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `npm test -- --run`
  - 结果：通过，`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `npm run build`
  - 结果：通过，Vite 产物 `dist/assets/index-CZyfJbv9.css` 与 `dist/assets/index-Bkwk6LJC.js` 已生成。
- `git diff --check`
  - 结果：通过，无空白错误。
- PC Node 重启与 HTTP smoke
  - `npm run api -- --host 0.0.0.0 --port 7001` 已重新监听，`lsof` 显示 `node` PID `47752` 监听 `TCP *:7001`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle：`index-CZyfJbv9.css`、`index-Bkwk6LJC.js`。

## 剩余风险

- 本轮只改 PC Web 展示、DOM 合同和文档，不启动 ROS2 runtime、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实路线执行、wheel raw L/R 非零和 delivery success 仍需要现场 HIL 验证；本轮只提升“地图上看到的路线”和“主按钮将执行的路线”之间的可见绑定。
