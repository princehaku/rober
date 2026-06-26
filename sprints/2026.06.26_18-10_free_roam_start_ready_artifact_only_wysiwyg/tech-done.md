# Free-Roam Start Ready 记录模式 WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 调整自动扫图 runtime 文案优先级：`free_roam_autonomy_start_ready=true` 时，即使 runtime 仍是 `artifact_only=true/cmd_vel_publish_enabled=false`，普通首屏也先说明“可以发起 start；当前尚未启动所以仍是记录模式”。
  - 保留安全边界：真正发车仍只通过固定 `/api/robot-control/free-roam/autonomy/start`，浏览器和 Node 不直接发布 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live-shape 回归：`free_roam_autonomy_start_ready=true`、`free_roam_autonomy=locked`、runtime `stopping/artifact_only=true/cmd_vel_publish_enabled=false` 且本地地图记录、地图画面、安全确认、相机和停止兜底都满足时，按钮显示 `开始自动扫图（低速）`，点击只调用固定 start 代理，不调用 manual、Nav2、delivery 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
- `docs/product/pc_tools_workstation.md`
  - 同步 `start_ready` 与 runtime 已解锁的区别，避免把尚未启动的记录模式误读为自动扫图未开放。

## 现场只读证据

- `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - `robot_api_connection.status=readable`
  - `camera.status=ready`
  - `lidar.lifecycle_running=true`
  - `lidar.latest_scan_proof_fresh=true`
  - `safe_command_boundary.free_roam_autonomy_start_ready=true`
  - `safe_command_boundary.free_roam_autonomy=locked`
  - `base.wheel_feedback_latest_left_speed=0`
  - `base.wheel_feedback_latest_right_speed=0`
- `GET /api/robot-control/free-roam/autonomy/latest`
  - `decision_state=stopping`
  - `decision_reason=现场请求停止`
  - `artifact_only=true`
  - `cmd_vel_publish_enabled=false`
- `GET /api/robot-control/map/preview`
  - `proxy_status=preview_forwarded`
  - `map_name=trashbot_map`
  - `width=223`
  - `height=116`
  - `has_free_cells=true`
  - `cell_counts.free=421`

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "free-roam|free roam|自动扫图|扫地式|start-ready|artifact-only"`
  - `Test Files 1 passed`
  - `Tests 16 passed | 111 skipped`
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "start-ready|artifact-only"`
  - `Test Files 1 passed`
  - `Tests 1 passed | 126 skipped`
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed`
  - `Tests 226 passed`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - 仅保留既有 Vite chunk size warning。

## 剩余风险

- 本轮没有在无人现场直接触发自动扫图 start，因为固定 start 可能让车低速移动；真实运动 smoke 需要现场人员在旁确认并随时 stop。
- 轮速 raw L/R 非零仍未证明，当前只读底盘反馈仍为 `0/0`。
- 本轮推进的是“ready 后可以启动建图”的 PC WYSIWYG 与按钮状态，不宣称自动扫图完整 HIL 已完成。
