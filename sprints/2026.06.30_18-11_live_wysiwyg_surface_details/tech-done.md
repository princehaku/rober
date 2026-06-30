# Live WYSIWYG Surface Details Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlLiveWysiwygSurfaceSummary`，并在 `RobotControlLiveClosureSummary` 暴露 `live_wysiwyg_surface_summaries`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `buildLiveClosureSummary()` 为 `camera`、`map`、`radar_map_points` 输出 visible/readback_gap/status/next_action/fixed_refresh_endpoint 明细。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 同步 fixture 和 API 断言，确保三类 surface 的固定只读 endpoint 和不发车合同存在。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录 live WYSIWYG surface 明细 API 合同。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，1 个测试文件、3 个测试通过。
- `npm test -- App.test.ts`：通过，1 个测试文件、225 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-DAuYzPy_.js` 与 `dist/assets/index-BCQK7HRw.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `27713`，新监听进程为 `node` PID `44418`，地址 `TCP *:7001`。
- live 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 3 个 `live_wysiwyg_surface_summaries`：`camera visible=false readback_gap=false fixed_refresh_endpoint=/api/robot-control/camera/first-frame/probe`、`map visible=true readback_gap=false fixed_refresh_endpoint=/api/robot-control/map/preview`、`radar_map_points visible=false readback_gap=false fixed_refresh_endpoint=/api/robot-control/radar/scan-proof/refresh`。本 smoke 未发送任何运动请求。

## 剩余风险

- 本轮只补只读 API 明细，不自动刷新 camera/map/radar，不启动雷达 lifecycle，不执行 Nav2，不发送 manual/keyboard/free-roam/stop 或 `/cmd_vel`。
- 真实所见即所得仍需要现场恢复相机首帧和雷达扫描后做实屏/只读刷新验证。
