# 2026-06-28 12:35 upper map preview radar overlay WYSIWYG

sprint_type: micro

## 实际改动

- 修改 `onboard/scripts/upper_robot_api.py`：上车端 `GET /api/map/preview` 新增只读 `radar_overlay` 字段，直接合并 radar status 与 nav2 proof latest 的 AMCL map 位姿。
- 当雷达 scan proof 已 stale 或雷达 lifecycle stopped 时，`radar_overlay.overlay_status=not_current`，保留 `scan_preview_source_point_count`、`scan_preview_frame_id` 和 `robot_pose` 诊断事实，但 `scan_preview_points=[]`、`scan_preview_point_count=0`，避免旧雷达点继续画在地图上。
- 修改 `onboard/scripts/upper_robot_api.py`：上车端 `GET /api/nav2/status` 现在提升只读 path proof、AMCL 位姿、planner/controller active 和 lifecycle blocker，直连 8787 也能解释自动驾驶为什么不能动。
- 修改 `pc-tools/workstation/src/server/robotControlSummary.ts`：PC summary 现在消费上车 `nav2_status.blocked_reasons/root_causes`，将 `nav2_lifecycle_not_running` 合并进普通首屏自动驾驶 blocker，避免 8787 已报 blocker 但 7001 仍显示空 blockers。
- 修改 `onboard/tests/test_upper_robot_api.py`：新增最小 YAML/PGM 地图单元测试，覆盖 8787 直连地图预览在 stale/stopped 雷达下不绘制旧点；新增 Nav2 status 单元测试，覆盖 path 已生成但 lifecycle stopped 时返回 `path_ready_with_service_blockers` 且不发布运动命令。
- 修改 `pc-tools/workstation/test/catalog.test.ts`：新增 PC summary lifecycle blocker 回归测试。
- 更新 `docs/product/pc_tools_workstation.md`：记录 8787 上车直连和 7001 PC 代理的地图雷达叠图口径一致。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_map_preview_returns_not_current_radar_overlay_without_drawing_stale_points`，结果 `1 test OK`。
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_status_lifts_path_proof_and_service_blockers_without_motion`，结果 `1 test OK`。
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api`，结果 `80 tests OK`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "lifecycle not running|controller is inactive"`，结果 `2 tests passed`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "Nav2 route|nav2 goal|automatic"`，结果 `4 tests passed`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts`，结果 `153 tests passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 TypeScript 与 Vite build 成功；仅有既有 chunk size warning。
- 通过：`git diff --check onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py docs/product/pc_tools_workstation.md sprints/2026.06.28_12-35_upper_map_preview_radar_overlay_wysiwyg/tech-done.md`
- 通过：上车部署后只读复核 `GET http://192.168.1.11:8787/api/map/preview`，结果 `status=loaded`、`map_name=trashbot_map`、`223x116`、`radar_overlay.overlay_status=not_current`、`scan_preview_point_count=0`、`scan_preview_source_point_count=81`、`scan_preview_frame_id=laser_frame`、`robot_pose.frame_id=map`、`blocked_reasons=[runtime_scan_stale_for_map_radar_overlay, radar_lifecycle_not_running_for_map_radar_overlay]`、`command_result.executed=false`、`sends_motion_commands=false`、`publishes_cmd_vel=false`。
- 通过：上车部署后只读复核 `GET http://192.168.1.11:8787/api/nav2/status`，结果 `status=path_ready_with_service_blockers`、`path_generated=true`、`path_point_count=18`、`path_generation_service_name=/compute_path_to_pose`、`amcl_pose.frame_id=map`、`lifecycle_running=false`、`lifecycle_state=stopped`、`planner_server_active=true`、`controller_server_active=false`、`blocked_reasons=[nav2_lifecycle_not_running]`、`next_action=启动或恢复 Nav2 lifecycle 后再执行图上路线`、`sends_motion_commands=false`、`publishes_cmd_vel=false`、`safe_to_control=false`。
- 通过：PC 代理只读复核 `GET http://127.0.0.1:7001/api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787`，结果 `proxy_status=preview_forwarded`、`radar_overlay.overlay_status=not_current`、`scan_preview_point_count=0`、`robot_control_executed=false`。
- 通过：PC 7001 重启到当前源码后只读复核 `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`，结果 `nav2_goal_ready=false`、`nav2_goal_label=自动驾驶服务未启动`、`nav2_goal_blockers=[nav2_lifecycle_not_running]`、`current_blockers=nav2_lifecycle_not_running`、`keyboard_control_start_ready=true`、`free_roam_start_ready=true`、`camera_status=source_first_frame_failed`、`camera_not_exclusive=true`。
- 通过：相机 health 只读复核仍为 `source_first_frame_failed`、`source_usage_status=not_in_use`、`source_usage_owner_count=0`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`shared_preview_contract=single_shared_capture_for_multiple_clients`。

## 剩余风险

- 本轮只修地图预览事实合同，不证明真实雷达已恢复 fresh scan，也不执行 Nav2 goal 或底盘运动。
- 相机仍需要真实首帧恢复；当前已知问题是 UVC 无帧且非页面独占。
