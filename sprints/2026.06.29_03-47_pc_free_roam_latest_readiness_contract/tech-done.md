# PC Free Roam Latest Readiness Contract

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `RobotControlFreeRoamAutonomyLatestResponse` 增加自由移动/建图 readiness 顶层字段。
- `pc-tools/workstation/src/server/index.ts`：让 `/api/robot-control/free-roam/autonomy/latest` 从只读 runtime artifact 派生 `free_move_start_ready`、`motion_ready`、`mapping_readiness_ready`、`mapping_blocked_reasons`、`motion_readiness_plain`、`mapping_readiness_plain`、`motion_next_action_plain` 和 `mapping_next_action_plain`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补充默认 fixture 和 latest proxy 回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录独立 latest endpoint 的只读合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam autonomy latest"`：通过，1 个文件，1 个测试通过，157 个跳过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/latest` 返回 `proxy_status=latest_loaded`、`runtime_status=loaded`、`decision_state=stopping`、`decision_reason=现场请求停止`、`free_move_start_ready=true`、`motion_start_ready=true`、`motion_ready=false`、`mapping_readiness_ready=false`、`mapping_blocked_reasons=[camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview]`、`motion_readiness_plain=可先自由移动；当前有停止请求，开始自由移动会先清除停止请求。`、`mapping_readiness_plain=建图验收未 ready；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 `/api/robot-control/free-roam/autonomy/latest` 的只读响应合同，不启动 free-roam、不启动建图、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- live 建图验收仍依赖真实画面首帧、雷达新鲜、地图记录和地图画面 ready；这些缺口不阻止先低速自由移动。
