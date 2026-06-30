# PC Free Roam Start WYSIWYG Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自由移动主按钮 `plain-free-roam-start` 新增启动后 WYSIWYG 刷新 DOM 合同。
  - 按钮直接暴露固定雷达 scan proof 刷新 endpoint 与 free-roam 地图预览 endpoint。
  - 按钮声明 start 成功后会刷新雷达 proof、地图 preview 和 radar status，方便现场脚本验证启动后的地图/雷达监看不会沿用旧读数。
- `pc-tools/workstation/test/App.test.ts`
  - 在默认 blocked 状态和传感器 ready 可建图状态下，锁定 `plain-free-roam-start` 的固定刷新 endpoint 与 `data-refreshes-*` 合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明该变化只是按钮级可验收合同，不新增自动发车、不绕过安全确认。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|starts map recording before auto sweep when camera and radar are ready"`
  - 通过：`Test Files 1 passed (1)`，`Tests 2 passed | 221 skipped (223)`。
- `npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 397 passed (397)`。
- `npm run lint`
  - 通过：0 error，保留既有 `RobotControlConsolePanel.vue` 4 个 Vue multiline warning。
- `npm run build`
  - 通过：生成 `dist/assets/index-B-rGexaa.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`
  - 通过，无 whitespace 错误。
- 7001 重启与只读 smoke
  - 已重启 Node 到 `0.0.0.0:7001`，新 PID `46115`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle `index-B-rGexaa.js`。
  - bundle 只读 grep 命中 `plain-free-roam-start`、`data-refreshes-radar-scan-proof-after-start`、`data-refreshes-map-preview-after-start`、`data-refreshes-radar-status-after-start`、`radar/scan-proof/refresh`、`rviz2` 和 `foxglove`。
  - `GET /api/robot-control/summary?base_url=http%3A%2F%2F192.168.1.11%3A8787` 为只读请求，未发送运动；返回当前 `live_status=needs_wheel_rerun`。

## 剩余风险

- 本轮只补自由移动 start 后的地图/雷达刷新可验收合同，不执行真实发车、不证明真实轮速 L/R 非零。
- 用户追问地图太小时，现有 PC 合同已经保留 `?view=map` 地图大屏、默认 PC 大地图和 ROS2 配套分工；RViz2/Foxglove 只作为工程/远程观察配套，不替代普通用户简易 PC 页。
