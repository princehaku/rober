# PC 当前所见主只读动作

sprint_type: micro

## 实际改动

- 后端 `field_acceptance_primary_no_motion_readback_action_id` 在 `all_wysiwyg` 多缺口场景下改为 `refresh_current_wysiwyg`，label 为 `刷新当前所见`，endpoint 使用 WYSIWYG 只读序列第一项 `/api/robot-control/radar/scan-proof/refresh`。
- PC 首屏“刷新当前所见”点击路径改为按 `wysiwyg_refresh_sequence` 串行执行：雷达 scan proof、雷达状态、地图预览、相机首帧、相机 MJPEG 状态、summary；没有序列时才回退旧的雷达/相机刷新。
- 同步更新 PC workstation 产品合同和单元/DOM 断言，保留 radar-only 使用 `refresh_radar_map_overlay`、camera-only 使用 `refresh_camera_first_frame`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 files / 428 tests passed。
- `npm run lint`：通过。
- `git diff --check`：通过。
- `npm run build`：通过，Vite 仅保留既有 bundle size warning。
- 7001 已重启并监听 `*:7001`。
- `curl http://127.0.0.1:7001/api/robot-control/summary` 只读 smoke：`field_acceptance_primary_no_motion_readback_action_id=refresh_current_wysiwyg`，label=`刷新当前所见`，sequence 为 radar scan proof -> radar status -> map preview -> camera first-frame probe -> camera MJPEG status -> summary，`field_acceptance_primary_no_motion_readback_action_sends_motion=false`，Nav2/manual/keyboard/free-roam/map runtime/radar lifecycle/delivery/stop 相关标志均为 false。
- Chrome headless DOM smoke：`plain-field-acceptance-primary-no-motion-readback` 显示 `只读复验：刷新当前所见`，DOM action id/label/endpoint/sequence 与 summary 一致，`data-starts-nav2/manual/keyboard/free-roam/map-runtime/radar-lifecycle=false`。

## 剩余风险

- 本轮没有执行运动命令；没有新安全确认，因此没有复验 wheel L/R 非零、Nav2 完整行程或 delivery success。
- 相机仍返回首帧失败诊断，当前改动只让多缺口刷新路径同时复测相机和雷达，不解决 USB/摄像头物理链路。
