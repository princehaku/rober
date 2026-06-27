# PC 雷达 running/missing 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：当 `/api/radar/status` 显示 `lifecycle_running=true` 时，PC summary 的 `readback_summary.lidar.status` 优先采用 `continuous_scan_status`，避免独立 latest proof 404/missing 把已运行雷达显示成未运行。
- `pc-tools/workstation/test/catalog.test.ts`：新增 Node summary 回归用例，覆盖 `latest_proof_missing_while_lifecycle_running`。
- `pc-tools/workstation/test/App.test.ts`：新增普通首屏和地图 marker 回归用例，覆盖雷达驱动运行但无最新点云时显示 `雷达无新点`。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录雷达启动后 proof missing 的产品口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts test/App.test.ts`，结果 `2 passed / 279 passed`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍提示既有单 chunk 大于 500 kB warning，不影响本轮改动。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed / 279 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 已重新运行在 `0.0.0.0:7001`，`lsof` 显示 PID `69539` 监听 `TCP *:7001`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/summary` live 读回
  `readback_summary.lidar.status=latest_proof_incomplete_while_lifecycle_running`、
  `lifecycle_running=true`、`continuous_scan_status=latest_proof_incomplete_while_lifecycle_running`、
  `scan_preview_point_count=72`。

## 剩余风险

- 本轮先修 PC 所见即所得聚合与展示，不执行真实底盘运动、Nav2 发车或 delivery success。
- 如果上车端雷达驱动一直没有 `/scan` 点云或 latest proof 文件，本轮会把它准确显示为 `雷达无新点`，但不等于底层雷达问题已经修复。
- detached 方式启动 7001 在本机没有稳定留存日志；当前 7001 由本轮前台 server session 保持运行，访问口径已恢复为 `0.0.0.0:7001`。
