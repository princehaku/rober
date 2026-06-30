# PC 当前所见雷达贴图刷新链路

- sprint_type: micro
- 时间：2026-06-30 15:58 CST
- owner：User Touchpoint Full-Stack Engineer（单线闭环；本轮运行时不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `refreshPlainWysiwygEvidence()`。普通首屏“当前所见”按钮现在会先调用 no-motion `refreshRadarProof({ mapPreviewAfter: true })`，再刷新 camera MJPEG 状态；按钮文案改为“刷新当前所见（含雷达贴图）”，并暴露固定雷达 proof endpoint、刷新 radar scan proof、刷新后读 map preview、点击不发运动命令等 DOM 合同。
- `pc-tools/workstation/test/App.test.ts`：默认 Robot Control 首屏测试改为验证该按钮会 POST `/api/robot-control/radar/scan-proof/refresh`，同时仍不会调用 radar start、Nav2 execute、manual、free-roam 等运动入口。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录普通首屏当前所见刷新链路的只读/no-motion 口径。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过：`npm test -- --run`（2 files / 397 tests passed）。
- 已通过：`npm run build`（`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`）。
- 已通过：`git diff --check`。
- 已执行：`npm run lint`，0 errors，保留既有 4 个 `RobotControlConsolePanel.vue` 换行 warning。
- 已通过：7001 刷新验证。旧 PID `64115` 已停止，新 Node PID `77526` 监听 `TCP *:7001`；`GET /` 返回新 bundle `index-CA_eia8V.js` / `index-BBcFFzNr.css`；bundle 包含 `plain-wysiwyg-evidence-refresh`、`scan-proof/refresh` 和“刷新当前所见（含雷达贴图）”。只读 summary 仍显示当前真实缺口：`radar.status=latest_proof_incomplete_while_lifecycle_running`、`radar_scan_observation_missing_reasons=scan_once,scan_hz,raw_packet_once`、`radar_overlay_point_count=0`、`live_closure_summary.status=needs_wheel_rerun`。

## 剩余风险

- 该按钮只刷新 no-motion 雷达 proof、雷达状态、地图预览和画面状态；如果真实 LiDAR 串口/驱动仍没有 fresh scan，地图雷达点仍会保持 0，并继续显示 scan proof 缺口。它不会替代真实硬件修复或真实运动验证。
