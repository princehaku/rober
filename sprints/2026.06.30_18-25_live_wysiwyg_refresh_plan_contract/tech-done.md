# Live WYSIWYG Refresh Plan Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlLiveClosureSummary` 新增当前所见 no-motion 刷新计划字段：固定顺序、中文步骤标签、radar status endpoint、刷新项布尔值和禁止动作布尔值。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `GET /api/robot-control/summary` 的 `live_closure_summary` 固定输出刷新顺序：radar scan proof refresh -> camera first-frame probe -> map preview -> radar status -> camera MJPEG status。
  - 明确该计划不发送 motion、不启动 Nav2/manual/keyboard/free-roam、也不启动 radar lifecycle 或 map runtime。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-summary` 与 `plain-live-closure-wysiwyg-refresh` 同步暴露刷新顺序、步骤标签、radar status endpoint 和 no-motion/no-start DOM 合同。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 覆盖 summary API、普通首屏 DOM、readback gap 和 wheel rerun 状态下的刷新计划字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明 API/DOM 合同和 ROS2/RViz2/Foxglove 不会被此刷新计划自动启动。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，1 个测试文件、3 个测试通过。
- `npm test -- App.test.ts`：通过，1 个测试文件、225 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，最终生成 `dist/assets/index-Cv6PQ2TZ.js` 与 `dist/assets/index-BCQK7HRw.css`。
- `git diff --check`：通过。
- 7001 重启：旧监听 `node` PID `55717` 已停止，新监听为 `node` PID `70095`，地址 `TCP *:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- live 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `status=needs_wheel_rerun`、`live_wysiwyg_refresh_plan_available=true`、刷新顺序为 radar scan proof refresh -> camera first-frame probe -> map preview -> radar status -> camera MJPEG status，且 `sends_motion=false`、`starts_nav2/manual/keyboard/free_roam/radar_lifecycle/map_runtime=false`。

## 剩余风险

- 本轮只暴露刷新计划合同，不对真实小车发送运动命令，也不 live POST 刷新 endpoint。
- 真实上位机只读 smoke 仅验证 summary 字段可读；相机、雷达和地图的现场画面质量仍需要用户在浏览器和真实硬件环境确认。
