# PC map preview path next action

## sprint_type

micro

## 实际改动

- 在 `RobotControlMapPreviewResponse` 合同中新增 `path_preview_next_action_plain`，让只读地图预览直接返回普通用户可理解的下一步。
- 上位机代理根据同轮路线点和 map-frame 小车位置生成三种文案：
  - 路线不可见：提示先准备图上路线并刷新地图。
  - 路线可见但小车位置不可见：提示刷新定位或地图。
  - 路线和小车位置都可见：提示确认路线后再勾选安全确认执行。
- PC fallback、单元测试 fixture、合同测试、`pc-tools/README.md` 和 `docs/product/pc_free_roam_mapping_design.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview"`
  - `Test Files 1 passed (1)`
  - `Tests 2 passed | 156 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍有既有 chunk size warning，但 build 成功。
- 通过：本机 7001 只读 live map preview 验证。
  - 7001 监听为 workstation 的 `tsx src/server/index.ts` / `node` 进程，未触碰 Clash。
  - `curl http://127.0.0.1:7001/api/robot-control/map/preview` 返回：
    `proxy_status=preview_forwarded`、`status=loaded_fail_closed_summary`、
    `path_preview_status=path_preview_observed`、`path_preview_point_count=18`、
    `path_preview_frame_id=map`、`robot_pose_status=map_pose_observed`、
    `path_preview_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`、
    `robot_control_executed=false`。

## 剩余风险

- 本轮只补只读 map preview 文案，不准备路线、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实运动或自动驾驶执行验证。
