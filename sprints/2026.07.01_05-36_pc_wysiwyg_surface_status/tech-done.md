# PC 当前所见 surface 状态补齐

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlLiveWysiwygSurfaceSummary` 增加 `completed`、`proof_status`、`missing_evidence`、`proof_plain`，让画面、地图、雷达点三项能被脚本和页面直接验收。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：为 camera/map/radar_map_points 生成结构化状态；地图已显示时标记完成，相机缺首帧或雷达点缺当前读数时给出具体缺口；刷新入口仍固定为 no-motion 的 probe/preview/scan-proof。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-wysiwyg-evidence-*` 行同步暴露 `data-completed`、`data-proof-status`、`data-missing-evidence`、`data-proof-plain`，可见文案只说“是否对齐/还差什么”，按钮仍只聚焦处理卡片。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 API 和 DOM 的 surface 状态字段，确认普通页面不显示 `overlay` 等工程词。
- `docs/product/pc_tools_workstation.md`：同步记录当前所见 surface 结构化合同。PC 地图太小时的口径保持：普通用户使用 `/map` 大地图和 100% 到 2400% 缩放；ROS2 配套为 RViz2 和 Foxglove，仅用于工程观察。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/App.test.ts`：通过，2 files / 235 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- --run`：并发全量出现 3 条超时/顺序抖动；三条失败项单独复现全部通过。
- `cd pc-tools/workstation && npm test -- --run --fileParallelism=false`：通过，3 files / 413 tests。
- `git diff --check`：通过。
- 7001 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 200，默认小车地址为 `http://192.168.1.11:8787`，`map_display_primary_url=/map`，默认缩放 `100%`，最高 `2400%`，ROS2 配套工具为 `rviz2,foxglove`；`live_wysiwyg_surface_summaries` 返回 camera/map/radar_map_points 的结构化状态，且 `live_wysiwyg_refresh_sends_motion=false`。
- 7001 地图入口 smoke：`GET /map` 和 `GET /?view=map` 均返回 200 HTML。

## 剩余风险

- 本轮没有触发任何真实运动、Nav2 执行、manual/keyboard/free-roam、建图 start、delivery 或 stop；真实发车闭环仍需要现场安全确认后单独验收。
- 当前 7001 只读 smoke 显示地图和雷达点已对齐，相机仍缺首帧；相机侧需要继续按 USB/供电/known-good UVC 方向排查。
- 并发全量 Vitest 在本机出现过计时抖动，串行全量已通过；后续若 CI 仍并发运行，建议优先用 `--fileParallelism=false` 验证这组带 HTTP/mock 计时的测试。
