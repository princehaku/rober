# Summary Motion Compatibility Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增普通脚本兼容 alias：`route_ready`、`wheel_lr_nonzero` 和 `free_roam_start_ready`。
- `route_ready` 直接镜像 `route_ready_on_map`，`wheel_lr_nonzero` 直接镜像 `wheel_lr_nonzero_proven`，`free_roam_start_ready` 直接镜像 `live_closure_summary.free_roam_start_ready`。
- 更新 summary 合同、服务端返回、定向测试、catalog live-summary 合同测试和 PC 工作站产品文档，避免现场 `curl | jq` 读取直觉字段时继续得到 `null`。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认 `route_ready=true`、`route_ready_on_map=true`、`wheel_lr_nonzero=false`、`wheel_lr_nonzero_proven=false`、`free_roam_start_ready=true`、`free_move_start_ready=true`、`free_roam_ready=true`、`free_roam_motion_start_ready=true`。

## 剩余风险

- 本轮只增加只读兼容 alias，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- `wheel_lr_nonzero=false` 是当前现场读回事实，完整 motion 目标仍需安全确认后重跑并在同窗口复验轮速 L/R 非零。
