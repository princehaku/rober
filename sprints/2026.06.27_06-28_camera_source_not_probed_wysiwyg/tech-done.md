# 2026.06.27 06:28 Camera Source Not Probed WYSIWYG

## sprint_type

micro

## 实际改动

- 真实上位机 `root@192.168.1.11 -p 37878` 复测 camera：停止 8088 后对 USB 设备 `3-1` 执行 unbind/bind，`/dev/video1` 重新枚举，8088/8787 恢复监听；但 direct `v4l2-ctl` 仍 8 秒 0 字节，`/api/camera/first-frame/probe` 仍 `first_frame_timeout/capture_read_call_timeout`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：当 camera health 只是 `source_readiness=source_selected_not_probed` 时，Robot Control summary 输出 `camera.status=source_not_probed`，不再把 service-selected 状态当作 `ready`；如果 probe overlay 或 health 已证明首帧失败，则输出 `source_first_frame_failed`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏把 `source_not_probed` 显示成“相机在线但还没确认首帧，先点检查画面或打开画面”，WYSIWYG 状态行同步显示同一句，不再泛化为 ready。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：更新 summary 和普通首屏断言，覆盖 `source_not_probed/source_first_frame_failed` 的新口径。
- `docs/product/pc_tools_workstation.md`、`docs/vision/board_camera_publisher.md`：记录真实上位机 USB reset 复测和 PC WYSIWYG 口径收紧。

## 验证结果

- `npm test -- --run test/catalog.test.ts`：通过，`113 passed`。
- `npm test -- --run test/App.test.ts`：通过，`150 passed`。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。
- 重启 `0.0.0.0:7001` 后确认 live summary 显示
  `camera.status=source_not_probed`、`source_readiness=source_selected_not_probed`、
  `source_usage=not_in_use`，没有再把 selected camera 冒充成 `ready`。
- 通过 7001 触发 `POST /api/robot-control/camera/first-frame/probe` 后确认 summary overlay
  切为 `camera.status=source_first_frame_failed`、`source_readiness=first_frame_failed`。

## 剩余风险

- USB reset 没有恢复 DV20 首帧；当前真实问题仍在摄像头输入、UVC 设备、USB 线/供电或采集卡工作模式。
- 本轮只修正 PC 所见即所得状态，不伪造画面、不把相机 selected 当作建图 ready。
- Nav2 仍是 action succeeded 但同窗口 wheel raw L/R 未非零，完整路线与 delivery success 仍未完成。
