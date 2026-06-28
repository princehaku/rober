# 2026.06.29 09:40 PC camera summary preview guidance WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 Robot Control summary 的 `readback_summary.camera` 增加 `preview_plain_hint`、`preview_next_action`，让只读 summary 的页面不用拼高级诊断字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 summary camera 预览提示汇总逻辑，把共享 MJPEG relay 状态和首帧失败诊断压成普通用户可读的“当前画面事实”和“下一步”。
- `pc-tools/workstation/test/catalog.test.ts`：补充 idle、health 首帧失败、relay 首帧失败、status+summary 一致性的断言，确保该字段不发送任何机器人控制请求。
- `docs/product/pc_tools_workstation.md`：同步记录 summary 新字段、只读边界和不触发运动控制的限制。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "Robot Control summary reflects camera source first-frame failure in shared preview status|Robot Control summary keeps camera status and readiness aligned when relay proves first-frame failure"`，结果 `1 passed`、`2 passed | 152 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`366 passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 和 `vite build` 成功；Vite 仅保留既有大 chunk warning。
- 通过：`git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/robotControlSummary.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md sprints/2026.06.29_09-40_pc_camera_summary_preview_guidance_wysiwyg/tech-done.md`，无 whitespace 问题。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`；返回 `camera.status=source_first_frame_failed`、`preview_status=idle_not_started`、`preview_plain_hint=不是页面独占：USB Composite Device: DV20 USB  (usb-5310000.usb-1) 当前没人占用，但 UVC 设备没有输出视频帧；检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。`、`preview_next_action=check_usb_camera_input_power_or_known_good_uvc`、`robot_control_executed=false`。
- 同一只读 live summary 返回 `free_roam_motion_start_ready=true`、`free_roam_autonomy_start_ready=true`、`free_roam_mapping_ready=false`；说明“小车可以先自由移动/自动扫图启动”不依赖雷达建图验收，但建图验收仍需要相机首帧、fresh radar、mapping active 和 fresh map preview。
- 同一只读 live summary 返回 `nav2_goal_ready=true`、`nav2_goal_wheel_feedback_status=goal_succeeded_but_wheel_lr_zero`；自动驾驶当前不是雷达/相机/controller 阻塞，而是上次路线 action 成功后 wheel raw L/R 仍未证明非零，需要现场安全确认后用 ROS 路线执行重跑采集轮速反馈。

## 剩余风险

- 本轮只修 PC summary 的可读提示，不修真实 DV20/UVC 无帧根因；现场仍需检查 USB、摄像头输入或更换 known-good UVC。
- 未获得本轮现场安全确认，因此不执行 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
