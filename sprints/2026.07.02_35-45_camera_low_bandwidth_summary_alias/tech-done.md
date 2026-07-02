# 相机低带宽 probe 证据持久化

sprint_type: micro

## 实际改动

- 将最近一次 camera first-frame probe 的 `low_bandwidth_fallback_attempted` 和 `low_bandwidth_fallback_min_size` 写入 PC 内存 overlay，并并入 `readback_summary.camera`。
- 在 `current_camera_wysiwyg_pack_*` 顶层短字段同步暴露低带宽 fallback 状态和 fallback 摘要。
- 在普通 PC `plain-current-camera-wysiwyg-pack` DOM 暴露 `data-low-bandwidth-fallback-attempted`、`data-low-bandwidth-fallback-min-size` 和 `data-first-frame-probe-fallback-attempts-summary`。
- 更新 TypeScript contract、App DOM 测试、catalog 代理/summary 测试和 PC 产品文档。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts -t "workstation camera first-frame probe uses quick source check without backend smoke"`，1 passed / 182 skipped。
- 通过：`npm test -- test/App.test.ts -t "marks radar map WYSIWYG as not blocking mapping when only camera first frame is missing"`，1 passed / 236 skipped。
- 通过：`npm run build`。Vite 仍提示已有 bundle size warning，但 TypeScript 和构建均通过。
- 通过：`npm test -- test/catalog.test.ts`，183 passed。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，PID `97025` 监听 `*:7001`。
- 通过：只读执行 `POST /api/robot-control/camera/first-frame/probe` 后，summary 显示：
  - `readback_summary.camera.first_frame_probe_low_bandwidth_fallback_attempted=true`
  - `readback_summary.camera.first_frame_probe_low_bandwidth_fallback_min_size=160x120`
  - `current_camera_wysiwyg_pack_low_bandwidth_fallback_attempted=true`
  - `current_camera_wysiwyg_pack_low_bandwidth_fallback_min_size=160x120`
  - `current_camera_wysiwyg_pack_first_frame_probe_fallback_attempts_summary` 包含 `MJPG@160x120` 和 `YUYV@160x120`
- 通过：只读执行 `POST /api/robot-control/radar/scan-proof/refresh` 后，summary 显示 `current_radar_map_wysiwyg_pack_status=loaded`、`current_radar_map_wysiwyg_pack_missing_evidence=[]`、当前雷达地图点 `4` 个、`live_wysiwyg_missing_surface_ids=[camera]`，目标进度为 `current_goal_done_count=2`、`current_goal_remaining_count=5`。

## 剩余风险

- 本轮只让低带宽 probe 证据在 summary 和 DOM 中持久可读，不改变相机硬件事实；现场仍是 USB `12M` full-speed 且首帧 timeout，需要换高速 USB 口/线或带供电 USB Hub 后复测。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`；真实运动三项仍需要现场安全确认后 HIL 验收。
