# PC Runtime Scan LiDAR WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从 free-roam runtime snapshot 提升结构化 `/scan` 距离字段到 `readback_summary.lidar`：
    `runtime_scan_status`、`runtime_lidar_min_distance_m`、`runtime_lidar_age_s`、`runtime_scan_source`。
  - 当 runtime snapshot 中 `lidar_age_s <= 1.5` 且 `lidar_min_distance_m` 有限时，标记为 `fresh`；否则标记为 `stale/not_loaded`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步扩展 `readback_summary.lidar` 合同，避免 UI 解析 gate 中文文案。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图雷达 marker 优先消费结构化 runtime `/scan` 距离；没有点数组时显示 `雷达距离：最近障碍 Xm（非地图点）`。
  - 旧上车端仍可回退解析 `free_roam_autonomy_gates[]`，但新 summary 不再依赖正则读取中文 evidence。
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展 runtime scan stale-proof 用例，断言 lidar summary 输出结构化 runtime 距离、年龄和来源。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 UI 回归：gate 文案没有距离时，地图仍从结构化 runtime 字段显示雷达距离。
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 runtime `/scan` 距离所见即所得边界。

## 验证结果

- 已通过：`npm test -- --run test/catalog.test.ts -t "uses fresh free-roam runtime scan for mapping lidar readiness|Robot Control summary surfaces running radar lifecycle"`
  - `2 passed | 128 skipped`
- 已通过：`npm test -- --run test/App.test.ts -t "structured runtime scan distance|count-only running radar"`
  - `2 passed | 175 skipped`
- 首轮全量 `npm test -- --run` 曾发现 5 个 App 文案回归和 1 个旧 fixture 防空问题；已修复为“只有结构化 runtime snapshot 才显示新距离读数文案，旧 gate 距离保持原口径”，并补了 `readback_summary?.lidar` 防空。
- 已通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1|derives radar running state|trip controls safety-gated|plain radar refresh failure|auto-refreshes radar proof|structured runtime scan distance"`
  - `6 passed | 171 skipped`
- 已通过：`npm test -- --run`
  - `2 passed (2) / 307 passed (307)`
- 已通过：`npm run build`
  - Vite build 通过；保留既有 chunk size warning。
- 已通过：`npm run lint`
- 已通过：`git diff --check`

## 剩余风险

- 本轮只改只读 summary 和 PC 地图展示，没有触发 radar refresh、manual、keyboard、free-roam start、Nav2、delivery、stop 或 `/cmd_vel`。
- runtime 距离不是地图点云；没有 `scan_preview_points` 时仍不能把距离读数贴成地图雷达点。
- 完整目标仍需要现场安全确认后重跑 ROS/T=13 Nav2，并证明同窗口 wheel raw L/R 非零；摄像头仍需硬件/输入层修复首帧。
