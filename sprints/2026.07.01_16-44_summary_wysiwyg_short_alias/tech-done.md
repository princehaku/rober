# Summary WYSIWYG Short Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增 WYSIWYG 普通短 alias：`camera_visible`、`map_visible`、`path_visible`、`radar_visible` 和 `radar_points_visible`。
- `camera_visible` 镜像 `camera_current_visible`，`map_visible` 镜像 `map_current_visible`，`path_visible` 镜像 `path_current_visible`，`radar_visible` / `radar_points_visible` 镜像 `radar_map_points_visible`。
- 更新 summary 合同、服务端返回、定向测试、catalog live-summary 合同测试和 PC 工作站产品文档，避免现场 `curl | jq` 查询直觉字段时得到 `null`。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认 WYSIWYG 短 alias 不再为 `null`：`camera_visible=false`、`map_visible=true`、`path_visible=true`、`radar_visible=false`、`radar_points_visible=false`。

## 剩余风险

- 本轮只增加只读 alias，不打开相机，不刷新地图，不启动雷达 lifecycle，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 当前真实 WYSIWYG 仍未全部完成：相机当前不可见，雷达地图点仍为 `not_current`，需要现场按固定 no-motion 复测/刷新链路继续收口。
