# PC Live WYSIWYG Structured Gaps Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlLiveClosureSummary` 新增相机源诊断、共享预览状态、雷达地图当前点/来源点/旧点抑制等只读字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_closure_summary` 从已有 camera/map/radar readback 派生结构化字段：
    - 相机：`live_wysiwyg_camera_source_diagnosis_status`、`live_wysiwyg_camera_source_diagnosis_plain_hint`、`live_wysiwyg_camera_source_diagnosis_next_action_plain`、`live_wysiwyg_camera_source_diagnosis_not_exclusive`、共享预览 client/upstream/exclusive 状态。
    - 雷达地图：`live_wysiwyg_radar_map_current_point_count`、`live_wysiwyg_radar_map_source_point_count`、`live_wysiwyg_radar_map_stale_source_points_suppressed`、`live_wysiwyg_radar_map_primary_blocked_reason`。
  - 字段只解释当前所见缺口，不改变相机、雷达、Nav2、键盘、自由移动、建图或任何运动 gate。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-live-closure-summary` 和 `plain-live-closure-wysiwyg-diagnostics` DOM 同步暴露上述 data 属性，便于现场脚本直接读取。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 覆盖 API 字段和 DOM data 属性，锁定“未知不伪装成 0”“旧来源点被抑制不等于当前地图 marker”的口径。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`
  - 同步记录 PC 当前所见结构化缺口合同。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts --run`，6 tests OK。
- 通过：`npm test -- test/App.test.ts -t "live closure|WYSIWYG|map" --run`，68 tests OK / 161 skipped。
- live 只读检查：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 显示相机 `source_diagnosis_status=uvc_no_frame_not_exclusive`、共享预览 `exclusive_camera_claim=false`，地图/路线当前可见，雷达来源点存在但当前地图贴图点为 0。
- live 只读检查：`GET http://127.0.0.1:7001/api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回地图图像和 18 个路线点，雷达来源点 123、当前贴图点 0，原因是 `runtime_scan_stale_for_map_radar_overlay`。

## 剩余风险

- 本轮没有修复真实 DV20 UVC 无帧，也没有刷新雷达 scan proof；只是让 PC/API/DOM 更直接暴露“不是独占”“旧雷达点不贴当前地图”的证据。
- 本轮未执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`，因此不产生新的真实轮速/路线/建图闭环材料。
