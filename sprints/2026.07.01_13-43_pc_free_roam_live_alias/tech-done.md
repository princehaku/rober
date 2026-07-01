# PC Free Roam Live Alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：给 `RobotControlLiveClosureSummary` 补自由移动/建图短 alias，覆盖 `free_roam_ready`、`free_roam_start_ready`、`free_roam_motion_start_ready`、`free_roam_motion_ready`、`free_move_without_camera_allowed`、`free_roam_motion_without_radar_allowed`、`free_roam_mapping_start_ready`、`free_roam_mapping_start_missing_reasons`、`free_roam_mapping_ready` 和 `free_roam_mapping_missing_reasons`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：这些 alias 全部从现有 `free_move_start_ready`、`mapping_start_ready`、`mapping_*` 与 free-roam readback 派生，不新增请求、不改变发车 gate。
- `pc-tools/workstation/test/catalog.test.ts`：锁定 `/api/robot-control/live-summary` 的扁平 alias，确认自由移动可启动、相机/雷达不阻塞先自由移动、建图仍按传感器 gate 判断。
- `docs/product/pc_tools_workstation.md`：同步自由移动/建图 alias 合同和 no-motion 边界。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts -t "live-summary route exposes"`，结果 `1 passed`、`1 passed | 180 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 仍提示主 chunk 超过 500 kB，这是既有体积警告，不影响本轮 live-summary alias。
- 通过：`npm test`，结果 `3 passed`、`419 passed`。
- 通过：`git diff --check`。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 Node `*:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：真实只读 `GET /api/robot-control/live-summary` 返回 `free_roam_ready=true`、`free_roam_start_ready=true`、`free_roam_motion_start_ready=true`、`free_roam_motion_ready=false`、`free_move_without_camera_allowed=true`、`free_roam_motion_without_radar_allowed=true`、`free_roam_mapping_start_ready=false`、`free_roam_mapping_start_missing_reasons=["camera_first_frame"]`、`camera_blocks_free_move=false`、`camera_blocks_mapping_start=true`、`starts_free_roam=false`、`starts_map_runtime=false`、`publishes_cmd_vel=false`。

## 剩余风险

- 本轮只补 PC 端只读状态字段，不执行 free-roam start、Nav2、manual、keyboard、map start、delivery、stop 或 `/cmd_vel`；真实自由移动运动闭环仍需现场勾安全确认后执行验证。
- 真实摄像头首帧仍未 ready，因此建图启动仍应被 `camera_first_frame` gate 阻塞；该阻塞不影响先自由移动。
