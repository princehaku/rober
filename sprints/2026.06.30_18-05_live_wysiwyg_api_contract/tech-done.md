# Live WYSIWYG API Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlLiveClosureSummary` 新增当前所见 WYSIWYG API 字段：ready、missing surface ids、needs refresh、readback gap surface ids、primary readback gap 和固定只读刷新 endpoint。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `buildLiveClosureSummary()` 统一计算 camera/map/radar 当前所见缺口和 readback gap，直接透出给 API。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-live-closure-summary` 优先使用 API 的 WYSIWYG 字段，避免 DOM 和外部脚本各算一套。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 补充 API 和 DOM 断言，包括 fixed no-motion refresh endpoint。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 live closure WYSIWYG API 合同。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，1 个测试文件、3 个测试通过。
- `npm test -- App.test.ts`：通过，1 个测试文件、225 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-DAuYzPy_.js` 与 `dist/assets/index-BCQK7HRw.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `6233`，新监听进程为 `node` PID `27713`，地址 `TCP *:7001`。
- live 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_wysiwyg_ready=false`、`live_wysiwyg_missing_surface_ids=camera,radar_map_points`、`live_wysiwyg_needs_refresh=false`、`live_wysiwyg_readback_gap_surface_ids=[]`、`live_wysiwyg_primary_readback_gap_surface_id=none`、固定 radar refresh / camera probe / map preview / camera MJPEG status endpoint。本 smoke 未发送任何运动请求。

## 剩余风险

- 本轮只补只读 API/DOM 合同，不启动雷达 lifecycle、不复测相机、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/stop 或 `/cmd_vel`。
- 真实 camera/map/radar 所见即所得仍需要现场链路恢复后，用只读刷新和实屏观察验证。
