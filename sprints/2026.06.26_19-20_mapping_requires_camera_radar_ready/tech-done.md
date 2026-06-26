# 2026-06-26 19:20 Mapping Requires Camera And Radar Ready

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 统一相机首帧失败判断：`source_first_frame_failed`、`source_readiness=first_frame_failed`、`capture_read_returned_false`、`capture_read_call_timeout` 会同时影响普通提示、共享预览 ready 和扫地式建图门禁。
  - `扫地式建图` 的开始记录入口新增传感器门禁：必须先勾现场安全确认、相机源 ready、雷达卡片为 `雷达已运行`，才允许调用固定 `/api/robot-control/map/start`。
  - 相机失败时按钮显示 `检查摄像头后建图`，下一步只聚焦 `检查画面`；雷达 stale/incomplete 时按钮显示 `刷新雷达`，下一步只聚焦 `刷新雷达`。
  - 普通键盘手控门禁未改：仍只按默认小车连接、现场安全确认、按住才动和停止兜底处理，不把雷达作为手控前置。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `markMappingSensorsReady` 测试 helper，让成功建图路径显式证明相机和雷达 ready。
  - 新增用例覆盖相机首帧失败时不会调用 map start，以及雷达 stale 时建图被挡但键盘手控入口仍独立。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏建图记录的相机/雷达 ready 门禁和 PC Node `0.0.0.0:7001` 边界。
- `docs/navigation/free_roam_autonomy.md`
  - 记录基础自助移动 start-ready 与扫地式建图记录门禁的区别。
- `docs/vision/board_camera_publisher.md`
  - 记录 `capture_read_returned_false/capture_read_call_timeout` 对 PC 相机门禁和建图入口的影响。

## 验证结果

- `npm test -- App.test.ts`
  - 通过：132 tests passed。
- `npm test`
  - 通过：2 test files、233 tests passed。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json`、Vite build、`tsc -p tsconfig.server.json` 均完成；仅保留 Vite 现有 chunk size warning。
- Live PC summary：`http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - PC Node 仍监听 `*:7001`。
  - camera：`status=source_first_frame_failed`、`video_source=/dev/video1`、`source_readiness=first_frame_failed`、`source_failure_reason=capture_read_returned_false`。
  - lidar：`lifecycle_running=false`、`continuous_scan_status=latest_proof_present_but_lifecycle_not_running`、`latest_scan_proof_fresh=false`。
  - `free_roam_autonomy_start_ready=true`，但完整 `free_roam_autonomy=locked`；本轮 UI 会继续允许基础自助移动引导，同时阻止扫地式建图记录入口。

## 剩余风险

- 当前 live 上位机相机仍返回 `/dev/video1` 首帧读取失败时，PC 会正确阻止建图并提示检查摄像头；这不是相机硬件/驱动恢复完成。
- 当前 live 雷达 lifecycle 未运行且 latest proof 不 fresh；PC 会正确阻止扫地式建图记录，仍需要现场启动/刷新雷达后再建图。
- 本轮只修改 PC 前端门禁和文档，没有解锁自动扫图 `/cmd_vel` 发布，也没有改变底盘、雷达 lifecycle 或 Clash/系统代理配置。
