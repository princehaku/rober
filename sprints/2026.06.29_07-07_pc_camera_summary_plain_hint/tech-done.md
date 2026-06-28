# PC camera summary plain hint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 Robot Control summary 的 `readback_summary.camera` 合同中新增只读 `plain_hint`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 camera WYSIWYG 结论、共享预览非独占事实和下一步动作合成 `plain_hint`；兼容字段仍保留原文，新增字段使用普通用户口径“画面未显示 / 已经看到画面”。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补 summary 断路默认值、UVC 无首帧和共享缓存帧三类断言，锁定非独占与下一步文案。
- `docs/product/pc_tools_workstation.md`：同步记录 summary camera `plain_hint` 的只读边界和使用口径。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`，`1 passed`，`38 passed | 122 skipped`。
- 已通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，`1 passed`，`1 passed | 214 skipped`。
- 已通过：`npm --prefix pc-tools/workstation run build`，`tsc` 和 `vite build` 均成功；仅保留既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test`，`2 passed`，`375 passed`。
- 已通过：重启 PC API 到 `0.0.0.0:7001`，`lsof` 显示 `node` PID `33311` 监听 `TCP *:7001`。
- 已通过：只读请求 `GET /api/robot-control/summary`，live `readback_summary.camera.plain_hint` 返回 `画面未显示：不是页面独占：USB Composite Device: DV20 USB  (usb-5310000.usb-1) 当前没人占用，但 UVC 设备没有输出视频帧。共享预览不是页面独占；谁打开页面都接入同一条上游流，当前 0 个页面观看。下一步：检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测`；同时 `viewer_count=0`、`upstream_connected=false`、`has_recent_frame=false`。

## 剩余风险

- 当前改动只让 summary 对“谁进来都能看同一条共享流 / 当前是否真有画面”更直接可读，不修复 UVC 设备本身无首帧输出。
- 未调用任何 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel` 运动接口。
