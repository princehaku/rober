# PC camera first-screen plain hint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏相机卡片的 `画面事实` 优先消费 `readback_summary.camera.plain_hint`，把“画面是否显示、共享预览是否非独占、谁打开都接入同一条上游流、下一步动作”合成一条用户口径。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增对齐保护；只有 `plain_hint` 与当前 `camera_wysiwyg_status_plain` 对齐时才优先显示，旧响应或未同步测试 fixture 自动回退原 `camera_wysiwyg_*` 拼接。
- `pc-tools/workstation/test/App.test.ts`：锁定普通首屏不再重复展示 `共享预览事实`，并覆盖 summary 已证明共享预览 streaming 时的简洁显示。
- `docs/product/pc_tools_workstation.md`：同步记录普通首屏消费 `readback_summary.camera.plain_hint` 的只读边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1|shared camera preview state"`，`1 passed`，`2 passed | 213 skipped`。
- 已通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control"`，`1 passed`，`5 passed | 210 skipped`。
- 已通过：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 均成功；仅保留既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test`，`2 passed`，`375 passed`。
- 已通过：重启 PC API 到 `0.0.0.0:7001`，`lsof` 显示 `node` PID `39847` 监听 `TCP *:7001`。
- 已通过：只读请求 `GET /api/robot-control/summary`，live camera `plain_hint` 返回 `画面未显示：不是页面独占：USB Composite Device: DV20 USB  (usb-5310000.usb-1) 当前没人占用，但 UVC 设备没有输出视频帧。共享预览不是页面独占；谁打开页面都接入同一条上游流，当前 0 个页面观看。下一步：检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测`；`viewer_count=0`、`upstream_connected=false`、`has_recent_frame=false`。

## 剩余风险

- 本轮是普通首屏展示收敛，不修复 UVC 设备无首帧输出。
- 未调用 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
