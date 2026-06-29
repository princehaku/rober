# PC WYSIWYG 顶层摘要别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：正常可读的 `GET /api/robot-control/summary` 顶层新增 `camera_summary`、`map_summary` 和 `radar_summary`，分别复用 `readback_summary.camera/map/radar`。
- `pc-tools/workstation/src/shared/contracts.ts`：补充三个顶层别名的类型。
- `pc-tools/workstation/test/catalog.test.ts`：增加别名一致性断言，锁住画面可见状态、地图 WYSIWYG 文案和雷达贴图状态。
- `pc-tools/README.md`：记录别名边界，明确只读、不启动相机/雷达/地图刷新、不执行运动命令。

## 验证结果

- `npm test -- --run test/catalog.test.ts`：`1 passed`，`166 passed`。
- `npm run build`：TypeScript、Vite build、server TypeScript 均通过。
- 本机部署：已重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `node` 监听 `*:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- Live summary：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `camera_summary_present=true`、`map_summary_present=true`、`radar_summary_present=true`、`nav2_summary_present=true`；`camera/map/radar` 顶层状态均与 `readback_summary` 嵌套状态一致。当前真实状态仍是 `camera_status=source_first_frame_failed`、`camera_reason=uvc_no_frame_not_exclusive`、`map_path=path_preview_observed`、`map_pose=map_pose_observed`、`radar_status=radar_stopped`、`radar_overlay=not_current`。

## 剩余风险

- 该改动只改善 PC/API 可读性，帮助现场直接判断画面、地图、雷达点的所见即所得状态；不触发摄像头采集、雷达启动、地图刷新、Nav2、键盘、自由移动或 `/cmd_vel`。
- 当前真实目标仍需要后续现场处理摄像头首帧、雷达新鲜贴图，以及带安全确认的真实运动验证。
