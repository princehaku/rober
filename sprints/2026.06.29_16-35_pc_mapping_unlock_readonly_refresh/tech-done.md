# 2026.06.29 16:35 PC 建图条件只读刷新

sprint_type: micro

## 实际改动

- 在 PC 普通用户控制台的“传感器 ready 后建图”解锁包增加 `刷新建图条件（只读）` 按钮。
- 该按钮复用普通首屏只读刷新链路，只读取 summary、地图预览、雷达状态和共享画面状态；不启动雷达、不发车、不启动建图、不执行 Nav2。
- 更新前端测试，覆盖按钮文案、只读接口调用，以及不调用雷达 start、Nav2 execute、手控、free-roam start 等危险端点。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，结果 `1 passed | 216 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed / 382 tests passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，Vite 构建成功；仍有既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 只读 live 摘要：摄像头 `source_first_frame_failed / uvc_no_frame_not_exclusive`，共享预览明确“不是页面独占”；自由移动 `free_roam_motion_start_ready=true`；建图启动缺 `camera_first_frame`、`lidar_fresh`；Nav2 当前 `planner_server_active=true`、`controller_server_active=false`、轮速 L/R 非零未证明。

## 剩余风险

- 本轮是 PC 端只读易用性改动，不直接修复真实 UVC 首帧、雷达 lifecycle 或 Nav2 controller inactive 的上车运行时问题。
- 真实小车移动、建图启动和自动驾驶执行仍需要现场在安全确认后单独验证。
