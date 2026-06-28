# 2026-06-29 20:10 PC 地图预览小车位置状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlMapPreviewResponse` 新增顶层 `robot_pose_status`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `/api/robot-control/map/preview` 在 forwarded、failed、blocked 完整合同里都返回 `robot_pose_status`。
  - 同轮 overlay 读到 map-frame 小车位置时返回 `map_pose_observed`；没有读到时返回 `not_observed`。
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
  - 同步 map preview fixture 和 loaded/partial overlay 断言。
- `pc-tools/README.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 map preview 顶层小车位置状态字段和安全边界。

## 验证结果

- 已通过：
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview"`
  - `npm --prefix pc-tools/workstation test`
  - `npm --prefix pc-tools/workstation run build`
- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview"` 结果：1 个测试文件通过，2 个测试通过。
- `npm --prefix pc-tools/workstation test` 结果：2 个测试文件通过，373 个测试通过。
- `npm --prefix pc-tools/workstation run build` 结果：TypeScript、Vite client build、server TypeScript 通过；Vite 仍提示 bundle chunk 超过 500 kB，属于既有构建提醒。
- 已重启 PC workstation API，`0.0.0.0:7001` 当前由 `npm run api` / `tsx src/server/index.ts` 监听。
- 只读 live 验证：
  - `curl -sS --max-time 22 http://127.0.0.1:7001/api/robot-control/map/preview`
  - `proxy_status=preview_forwarded`
  - `status=loaded_fail_closed_summary`
  - `width=223`
  - `height=116`
  - `robot_pose_status=map_pose_observed`
  - `radar_overlay_status=not_current`
  - `path_preview_point_count=18`
  - `path_preview_frame_id=map`
  - `robot_control_executed=false`

## 剩余风险

- 本轮只补地图预览只读字段，不刷新定位、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- live 当前 map preview 已读到小车 map-frame 位置和路线点，但完整 Nav2 执行仍需要现场安全确认后重跑并验证执行窗口轮速 L/R 非零。
