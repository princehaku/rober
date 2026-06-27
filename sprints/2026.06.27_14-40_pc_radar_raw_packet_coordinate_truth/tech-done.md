# PC 雷达原始包坐标口径对齐

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中收紧地图坐标口径文案。
- 当 LiDAR lifecycle 正在运行、原始包已收到，但没有解析出地图雷达点时，地图坐标口径从泛化的“雷达点未贴图”改为“原始包已收到但暂无地图雷达点”。
- 更新 `pc-tools/workstation/test/App.test.ts`，锁定有机器人地图坐标但雷达点为 0 的 WYSIWYG 文案。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "keeps the mapped radar marker explicit when running lidar has pose but zero visible points"`，结果 `1 passed | 164 skipped`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `291 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功，仍有既有 `Some chunks are larger than 500 kB` 警告。
- 通过：只读 live summary 显示当前正是本轮形态：`raw_packet_once_observed=true`、`latest_scan_proof_fresh=false`、`scan_preview_point_count=0`、`robot_pose.frame_id=map`。
- 通过：构建产物 `pc-tools/workstation/dist/assets/index-COR6heNR.js` 包含“原始包已收到但暂无地图雷达点”文案。

## 剩余风险

- 本轮只修正 PC 首屏只读文案，不触发雷达刷新、不启动 free-roam、不执行 Nav2、不发送 manual/keyboard/delivery/stop 或 `/cmd_vel`。
- live 上车端当前仍是 raw packet observed 但 scan 点数组为 0；真实地图点仍需要雷达 scan proof fresh 并解析出 `scan_preview_points` 后才能显示。
