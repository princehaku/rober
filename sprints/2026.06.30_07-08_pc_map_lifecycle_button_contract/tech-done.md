# PC 地图 lifecycle 按钮合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 为普通首屏地图卡的 `plain-map-runtime-start` 补齐固定 `/api/robot-control/map/start`、启动地图记录 runtime、无底盘运动、不执行 Nav2、不启动自由移动的 DOM 合同。
  - 为普通首屏地图卡的 `plain-map-save` 增加 `data-testid`，并补齐固定 `/api/robot-control/map/save`、保存后刷新地图画面、无底盘运动、不执行 Nav2、不启动自由移动的 DOM 合同。
- `pc-tools/workstation/test/App.test.ts`
  - 在默认普通首屏测试中补充地图 lifecycle 两个按钮的固定 endpoint 和非发车边界断言。
- `pc-tools/README.md`
  - 记录地图记录/保存按钮的固定入口和非发车边界。
- `docs/product/pc_tools_workstation.md`
  - 同步普通 PC 工作站产品文档，明确建图普通路径包含启动记录、刷新当前画面和保存地图三段固定入口。

## 验证结果

- 已通过目标用例：
  - `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 结果：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- 已通过全量工作站测试：
  - `npm test -- --run`
  - 结果：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 已通过生产构建：
  - `npm run build`
  - 结果：`vite build` 成功，新 bundle 为 `dist/assets/index-LkGNiSGf.js`。
- 已通过 diff 格式检查：
  - `git diff --check`
  - 结果：无输出，检查通过。
- 已重启 PC Node 工作站：
  - `0.0.0.0:7001` 当前由 `node` 监听，PID `23129`。
  - `curl http://127.0.0.1:7001/` 返回 `index-LkGNiSGf.js` 和 `index-BmaNglvi.css`。

## 剩余风险

- 本轮只补 PC Web DOM 合同和单元测试，没有真实建图 HIL，也没有发送 map start/save、manual、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需在 7001 页面连接上位机后验证：相机和雷达 ready 后启动地图记录、自由移动扫图、刷新当前画面、保存地图。
