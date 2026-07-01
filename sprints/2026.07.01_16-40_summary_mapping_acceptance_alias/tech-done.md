# Summary Mapping Acceptance Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增建图验收 alias：`mapping_acceptance_ready`、`free_roam_mapping_ready` 和 `free_roam_mapping_missing_reasons`。
- `mapping_acceptance_ready` 与 `free_roam_mapping_ready` 同源，表示建图验收是否已经就绪；`free_roam_mapping_missing_reasons` 与 `mapping_acceptance_missing_reasons` 同源，表示还差画面首帧、雷达新鲜、建图运行态或最新地图画面等验收条件。
- 更新 summary 合同、服务端返回、定向测试、catalog live-summary 合同测试和 PC 工作站产品文档，避免现场 `curl | jq` 读建图验收 ready/missing 时得到 `null`。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认 `mapping_acceptance_ready=false`、`free_roam_mapping_ready=false`，且 `free_roam_mapping_missing_reasons=["camera_first_frame","lidar_fresh","mapping_active","fresh_map_preview"]` 与 `mapping_acceptance_missing_reasons` 一致。

## 剩余风险

- 本轮只增加只读 summary alias，不启动 free-roam，不启动建图，不执行 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 当前现场建图验收仍未 ready；剩余缺口需要相机首帧、雷达新鲜、建图运行态和最新地图画面读回共同满足。
