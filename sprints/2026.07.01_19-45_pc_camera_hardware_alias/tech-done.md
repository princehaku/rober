# PC 相机硬件恢复 alias

sprint_type: micro

## 实际改动

- PC `live_closure_summary` / `/api/robot-control/live-summary` 增加相机硬件恢复短 alias，用于区分 USB 12M full-speed 硬件链路动作、建图阻塞和自由移动边界。
- 普通首屏 DOM 在当前卡点、WYSIWYG 诊断和建图相机解阻卡同步暴露相同字段。
- 产品文档同步说明 `/map` 是普通用户大地图入口，ROS2 配套 RViz2/Foxglove 只做工程观察，不作为普通用户发车入口。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun|prioritizes full-speed USB camera diagnosis|separates free movement"`：通过，3 passed。
- `npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，1 passed。
- `npm test -- --run test/App.test.ts -t "full-speed USB camera recovery|renders Robot Control V1 by default|opens direct map view"`：通过，3 passed。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仍提示既有 bundle size warning。
- `npm test`：通过，3 files / 418 tests passed。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001` 后只读 curl `/api/robot-control/live-summary`：`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_usb_full_speed_detected=true`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`camera_usb_speed=12M`、`mapping_start_missing_reasons=["camera_first_frame"]`、`free_move_start_ready=true`、`map_display_primary_url=/map`、`map_display_ros2_companion_tools=["rviz2","foxglove"]`、`map_display_ros2_companion_required=false`。

## 剩余风险

- 相机真实画面仍未恢复，当前根因仍是现场 USB 12M full-speed 链路；需要把摄像头换到高速 USB 口/线或带供电 Hub 后再执行 no-motion 首帧复测。
- 本轮未执行任何运动/control POST，也未触发建图 runtime；自由移动和 Nav2 行程仍需现场安全确认后另行验收。
