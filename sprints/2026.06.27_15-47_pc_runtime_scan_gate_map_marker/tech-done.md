# 2026-06-27 15:47 PC runtime scan gate map marker

## sprint_type

micro

## 设计

本轮只修 PC 普通首屏的雷达 WYSIWYG：live summary 可能只有 `free_roam_autonomy_gates`，没有
`readback_summary.lidar`，但 `lidar_fresh` 已证明 `free-roam runtime /scan 新鲜`。这种情况下 UI
不能退回“雷达未运行”，也不能伪造地图雷达点；正确口径是“雷达已运行，只显示最近障碍距离，这是非地图点读数”。

安全边界：本轮只消费只读 summary/runtime gate，不启动雷达、不刷新雷达、不启动 free-roam、不发送
manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `gateDerivedLidarReadback()`：当 `lidar_fresh=ready` 且 evidence 明确包含 runtime `/scan` 新鲜时，
    在 `readback_summary.lidar` 缺失的 live 形态下合成最小只读雷达 readback。
  - `summarizeRadarState()` 优先识别“runtime `/scan` 新鲜 + 只有最近障碍距离 + 无点数组”，显示
    `雷达已运行` 和距离读数提示。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live 形态回归：summary 缺 `readback_summary.lidar`，但 runtime scan gate ready 时，普通首屏、
    地图 marker、雷达点口径和坐标口径都显示距离读数，不发任何控制请求。
  - 保留旧形态回归：radar proof stale/incomplete 但 runtime `/scan` 新鲜时不再显示待刷新。
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 runtime scan gate 对地图 marker 的只读兜底与“不伪造地图点”的边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "runtime scan freshness|obstacle-only running radar|runtime scan gates"`
  - 结果：1 个 test file passed，3 tests passed，166 skipped。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - 结果：2 个 test files passed，297 tests passed。
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 结果：Vite build 成功，产物 `dist/assets/index-OqJGEXmD.js`；仍有 500 kB chunk size warning，非本轮新增失败。
- 已通过：`npm --prefix pc-tools/workstation run lint`
- 已通过：`git diff --check`
- 已重启 PC Node：`node` PID `58291` 监听 `*:7001`，HTML 引用新 bundle `index-OqJGEXmD.js`。
- live DOM 只读验证 `http://127.0.0.1:7001`：
  - `plain-radar-panel data-state=雷达已运行`
  - panel 文案包含 `free-roam runtime 已读到实时 /scan；当前没有地图点数组，只显示最近障碍 0.04m，等点位后再贴地图。`
  - 地图 marker：`雷达距离：最近障碍 0.04m（非地图点）`
  - marker aria：`这是距离读数，不是已贴到地图的雷达点`
  - scan point count：`0`
  - 页面请求只包含 summary/health/map preview/camera mjpeg status/latest 等只读 GET；未触发 radar start、manual、Nav2 execute、delivery、stop 或 `/cmd_vel`。

## 剩余风险

- 本轮证明的是 PC UI 对 runtime scan gate 的只读展示，不等于雷达点云已经能贴到地图。
- `obstacle_clear=not_proven` 且距离为 `0.04m` 时，UI 会如实显示最近障碍距离；这不是可继续直行或可验收建图证明。
- 相机首帧、完整 Nav2 路线执行、wheel raw L/R 非零、delivery success 仍需独立现场材料闭环。
