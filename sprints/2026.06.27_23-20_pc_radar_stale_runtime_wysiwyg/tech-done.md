# PC Radar Stale Runtime WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `runtime_lidar_min_distance_m` / `runtime_lidar_age_s` 只有在 `runtime_scan_status=fresh` 时才参与当前 runtime 距离派生。
  - 新增 stale runtime `/scan` 标签：当结构化距离仍存在但状态为 `stale` 时，雷达卡片、当前事实和地图雷达点口径显示 `旧 /scan 距离 ... 已过期，不贴到地图`。
  - `雷达无新点`、`雷达待刷新`、`刷新中` 三类状态都保留旧距离解释，但不会把旧距离说成当前 `最近障碍`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live-shape 回归：`runtime_scan_status=stale` 且 `runtime_lidar_min_distance_m=0.04` 时，页面不出现 `最近障碍 0.04m`，只显示旧距离过期。
- `docs/product/pc_tools_workstation.md`
  - 记录 stale runtime `/scan` 距离的 PC WYSIWYG 口径。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录旧距离不等于地图点、当前近障碍或建图 ready 证据。

## 验证结果

- `npm test -- test/App.test.ts -t "stale runtime scan distance|structured runtime scan distance|stale running lidar proof|keeps count-only running radar" --maxWorkers=1 --no-fileParallelism`
  - 通过：1 个测试文件，4 个相关用例通过。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：2 个测试文件，317 个用例通过。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示 bundle 超过 500 kB，这是既有体积 warning。

## 剩余风险

- 本轮只修正 PC 端只读呈现，不刷新真实雷达、不恢复定位、不触发自由移动或 Nav2。
- live 当前仍显示摄像头无首帧、雷达 overlay partial、缺 robot map pose；这些真实外部状态仍需后续硬件/上车端修复或现场复验。
