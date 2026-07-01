# Live Mapping Start Gap Consistency

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary/free-roam 聚合优先消费上车 `/api/free-roam/autonomy/latest` 显式 `free_roam_mapping_start_missing_reasons` / `mapping_start_missing`，没有显式缺口时才回退 runtime gate rows。
- `pc-tools/workstation/src/shared/contracts.ts`：`free_roam_autonomy_runtime` 允许携带可选建图启动/验收缺口数组。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：新增回归，覆盖 latest 明确只差 `camera_first_frame`、旧 gate 仍残留 `lidar_fresh` 时，live-summary 不再把“雷达新鲜”写入当前建图启动缺口。
- `docs/product/pc_tools_workstation.md`：记录 live-summary 建图启动缺口优先级和 no-motion 边界。

## 验证结果

- 通过：`npm test -- --run test/robotControlSummary.test.ts -t "uses free-roam latest mapping start gaps before stale runtime gate rows"`，1 passed。
- 通过：`npm test -- --run test/catalog.test.ts -t "surfaces free-roam autonomy runtime state from latest artifact readback"`，1 passed。
- 通过：`npm test`，3 files / 421 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，新 PID `79042`。
- 通过：只读 curl `/api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回 `mapping_start_missing_reasons=["camera_first_frame"]`、`free_roam_mapping_start_missing_reasons=["camera_first_frame"]`、`mapping_lidar_blocks_start=false`、`mapping_lidar_fresh_gate_status=not_loaded`，`objective_audit_summary_plain` 已变为“建图启动还差画面首帧”，同时 `free_move_start_ready=true`、`free_move_without_camera_allowed=true`、`free_roam_motion_without_radar_allowed=true`、`readback_only=true`、`starts_free_roam=false`、`starts_map_runtime=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`submits_delivery=false`、`stops_motion=false`、`publishes_cmd_vel=false`。

## 剩余风险

- 本轮只修 live-summary 只读缺口一致性，不刷新雷达、不启动自由移动、不启动建图 runtime，也不触发 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 完整目标仍未收口：相机首帧、同窗口 wheel L/R 非零、delivery success、键盘连续手控和自由移动运行态仍需现场材料。
