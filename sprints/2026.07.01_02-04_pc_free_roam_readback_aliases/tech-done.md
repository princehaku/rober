# PC 自由移动 readback 别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`readback_summary.free_roam` 新增 `free_move_without_camera_allowed`、`motion_without_radar_allowed`、`free_move_minimal_precheck_safety_only`、`free_move_safety_confirm_required`、`free_move_camera_preflight_required`、`free_move_radar_preflight_required`、`mapping_start_requires_camera_first_frame`、`mapping_start_requires_lidar_fresh`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从已有自由移动 readiness 派生上述只读字段，明确“可先自由移动”和“建图启动要求相机/雷达”是两层能力。
- `pc-tools/workstation/test/catalog.test.ts`：补充自由移动、建图启动和建图就绪场景断言，防止字段再次退回为空或语义混淆。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts -t "free roam|自由移动|mapping" --run`，7 tests OK / 170 skipped。
- 通过：`npm test -- test/robotControlSummary.test.ts --run`，6 tests OK。
- 通过：`npm test -- test/catalog.test.ts --run`，177 tests OK。
- 通过：`npm test -- --run`，3 个测试文件、412 tests OK。
- 通过：`npm run build`，生成 `dist/assets/index-BoR-EUKp.js` 与 `dist/assets/index-BMxcT92A.css`；保留既有 Vite chunk size warning。
- 通过：`npm run lint`，0 error；保留既有 4 条 `vue/multiline-html-element-content-newline` warning。
- 通过：PC Node 重启到 `0.0.0.0:7001` 后，live 只读 summary 返回 `motion_start_ready=true`、`free_move_without_camera_allowed=true`、`motion_without_radar_allowed=true`、`free_move_minimal_precheck_safety_only=true`、`free_move_safety_confirm_required=true`、`free_move_camera_preflight_required=false`、`free_move_radar_preflight_required=false`、`mapping_start_requires_camera_first_frame=true`、`mapping_start_requires_lidar_fresh=true`、`mapping_start_ready=false`、`mapping_start_missing=camera_first_frame`、`safe_to_control=false`。

## 剩余风险

- 本轮只改 PC 只读 summary 字段，不启动自由移动、不启动建图、不发送 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 当前 live 建图启动仍缺 `camera_first_frame`；需修复摄像头首帧后才能让建图启动 ready。
