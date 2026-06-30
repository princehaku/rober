# PC 建图启动传感器读数动作卡合同

sprint_type: micro

## 实际改动

- `mapping_start` / `free_move` action card evidence 新增建图启动传感器原始判定：相机首帧、相机 source readiness、雷达 fresh、雷达 lifecycle、runtime scan 是否 fresh、runtime scan 是否只作诊断、雷达 fresh 是否被 lifecycle stopped 阻断，以及下一步雷达动作。
- 普通首屏 action card DOM 同步新增 `data-mapping-camera-first-frame-ready`、`data-mapping-camera-source-readiness`、`data-mapping-lidar-fresh-ready`、`data-mapping-lidar-lifecycle-running/state`、`data-mapping-runtime-scan-fresh`、`data-mapping-runtime-scan-diagnostic-only`、`data-mapping-lidar-fresh-blocked-by-lifecycle` 和 `data-mapping-lidar-next-action-plain`。
- 更新测试、README 和 PC 工作站产品文档，明确 runtime snapshot fresh 但雷达 lifecycle stopped 时只能作诊断，不能当作建图启动的 `lidar_fresh`。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`：通过。
- `npm test -- test/catalog.test.ts -t "does not treat stale runtime scan as mapping-start lidar readiness when radar lifecycle is stopped"`：通过。
- `npm test -- --run`：2 个测试文件、397 个测试全部通过。
- `npm run lint`：0 error，4 个既有 Vue 换行 warning。
- `npm run build`：通过，生成 `dist/assets/index-RfCF6W89.js`。
- `git diff --check`：通过。
- 本机 7001 live 验证：Node 监听 `0.0.0.0:7001`，PID `42985`；`mapping_start.evidence` 返回 `mapping_camera_first_frame_ready=false`、`mapping_camera_source_readiness=first_frame_failed`、`mapping_lidar_lifecycle_running=false`、`mapping_lidar_lifecycle_state=stopped`、`mapping_runtime_scan_fresh=true`、`mapping_runtime_scan_diagnostic_only=true`、`mapping_lidar_fresh_blocked_by_lifecycle=true`，页面 bundle 包含新增 mapping DOM 字段。

## 剩余风险

- 本轮不启动雷达、不启动建图、不启动自由移动，也不发送 `/cmd_vel`；它只把建图启动缺口在 PC 首屏显式化。
- live 当前仍缺相机首帧和雷达 lifecycle running，因此建图启动仍未就绪；但自由移动 start_ready 不受这两个建图缺口阻塞。
