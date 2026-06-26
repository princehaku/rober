# PC 共享实时画面状态

sprint_type: micro

## 实际改动

- PC Node 新增只读 `GET /api/robot-control/camera/mjpeg/status?baseUrl=...`，读取本机 MJPEG relay 表并返回 `client_count`、`upstream_active`、`content_type_loaded`、`shared_capture=true`、`exclusive_camera_claim=false`。
- `RobotControlConsolePanel` 的普通“实时画面”卡片新增 `共享预览` 状态行；它解释多个 PC 页面是否共享同一个上游 MJPEG 流，但不把共享 relay 当成画面已经出图。
- workstation client、共享 contracts、App 测试桩和 catalog 回归测试同步更新。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts`，132 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts`，102 tests passed。
- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、234 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build OK；仅保留既有 chunk size warning。

## 剩余风险

- 本轮证明的是 PC Node 单上游多客户端共享状态可见；真实相机首帧、UVC 占用、8088 服务稳定性仍以后续真机 smoke 为准。
- 该状态端点不打开摄像头；如果没有页面正在看 MJPEG，`client_count=0/upstream_active=false` 是正常状态，不代表摄像头坏。
