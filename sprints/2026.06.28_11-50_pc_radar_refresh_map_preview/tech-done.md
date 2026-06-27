# 2026.06.28 11:50 PC 雷达刷新后同步地图预览

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `refreshRadarProof()` 完成固定雷达 proof refresh 和只读 radar/status 后，默认刷新一次地图预览。
  - 新增 `mapPreviewAfter` 选项；free-roam start 传 `false`，继续使用自己的建图会话地图刷新，避免重复计数。
  - 该改动只串联只读地图预览，不发送底盘 manual、Nav2 goal、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通“刷新雷达”回归，断言雷达刷新后会读取 `/api/robot-control/map/preview`，同时仍不触发 first-jog、manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录雷达刷新后地图 marker 同轮更新规则。

## 验证结果

- `npm test -- test/App.test.ts --testNamePattern "refreshes radar and map proof" --maxWorkers=1 --no-fileParallelism`：1 passed，186 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：2 files passed，331 tests passed。
- `npm run lint`：passed。
- `npm run build`：passed（Vite chunk-size warning 保持既有状态，不影响构建通过）。
- `git diff --check`：passed。
- 7001 已按 `HOST=0.0.0.0 PORT=7001 npm run api:public` 重启，`lsof` 显示 node 监听 `*:7001`。
- live summary `http://127.0.0.1:7001/api/robot-control/summary`：
  - 当前未点击雷达启动/刷新，live 仍是 `radar_lifecycle=stopped`、`runtime_scan_status=stale`、`map.radar_overlay_status=not_current`、overlay 点数 `0`。
  - 相机仍是 `uvc_no_frame_not_exclusive`；自由移动仍是 `free_roam_motion_start_ready=true`。
  - Nav2 下一步仍保持“先恢复 Nav2 planner 和 Nav2 controller，再生成图上路线并读到小车地图位置”。

## 剩余风险

- 本轮不触发真实雷达 start/refresh；只修改 PC 端点击后的只读刷新串联。
- 当前 live 雷达仍是 stopped/stale，地图 overlay 仍为 `not_current`；真实地图 marker 更新需要现场显式点击雷达启动或刷新。
